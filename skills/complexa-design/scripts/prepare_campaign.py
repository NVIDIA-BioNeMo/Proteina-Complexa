#!/usr/bin/env python3
"""Prepare a Complexa campaign without importing ML code or probing hardware.

Requires PyYAML. Reads the released pipeline's direct stage files; this is a
static review, not Hydra composition or runtime/target validation. Exit 2 means
an unsupported or inconsistent plan. Writes only to a new output directory.

Usage:
    python3 prepare_campaign.py --project-root REPO --pipeline binder \\
        --target TARGET --run-name RUN --out-dir NEW_DIRECTORY
Arguments:
    Required paths, pipeline, target, and run name are shown above. Optional
    sample/search/refolder settings and YAML overrides are listed by --help.
Output:
    campaign_plan.json, campaign_overrides.yaml, and launch.sh in NEW_DIRECTORY
    (a fresh sibling with --revision if it exists); stdout reports output_dir.
    The launch script is never executed.
Exit codes:
    0 on success; 2 for invalid arguments, inconsistent plans, or handled
    read/write/syntax-check failures; 1 for unexpected Python errors.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

import yaml

PIPELINES = {
    "binder": ("complexa", "targets/targets_dict.yaml", "target_dict_cfg"),
    "ligand_binder": ("complexa_ligand", "targets/ligand_targets_dict.yaml", "target_dict_cfg"),
    "ame": ("complexa_ame", "design_tasks/ame_dict_v2.yaml", "motif_target_dict_cfg"),
}
LORA = {"r": 32, "lora_alpha": 64.0, "lora_dropout": 0.0, "train_bias": "none"}
BACKENDS = {"colabdesign": ["AF2_DIR"], "rf3_latest": ["RF3_CKPT_PATH", "RF3_EXEC_PATH"], "esmfold": ["ESM_DIR"]}
SEARCHES = ("single-pass", "best-of-n", "beam-search", "fk-steering", "mcts")
BASH_SYNTAX_TIMEOUT_SECONDS = 5


def merge(base: dict, patch: dict) -> dict:
    result = deepcopy(base)
    for key, value in patch.items():
        result[key] = (
            merge(result[key], value)
            if isinstance(result.get(key), dict) and isinstance(value, dict)
            else deepcopy(value)
        )
    return result


def get(data: dict, path: str, default=None):
    for key in path.split("."):
        if not isinstance(data, dict) or key not in data:
            return default
        data = data[key]
    return data


def put(data: dict, path: str, value) -> None:
    keys = path.split(".")
    for key in keys[:-1]:
        data = data.setdefault(key, {})
        if not isinstance(data, dict):
            raise ValueError(f"Cannot set {path}: {key} is not a mapping")
    data[keys[-1]] = value


def read_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"Expected a YAML mapping: {path}")
    return value


def positive(value, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def job_counts(nsamples: int, repeats: int, jobs: int) -> list[int]:
    """Match generate.split_by_job: split lengths if repeat=1, else repeats."""
    for name, value in (("nsamples", nsamples), ("repeats", repeats), ("jobs", jobs)):
        positive(value, name)
    units, multiplier = (nsamples, 1) if repeats == 1 else (repeats, nsamples)
    chunk = (units + jobs - 1) // jobs
    return [max(0, min(chunk, units - i * chunk)) * multiplier for i in range(jobs)]


def source_config(root: Path, pipeline: str) -> tuple[dict, list[dict], list[str]]:
    """Read only direct stages; leave nested Hydra defaults/interpolations intact."""
    base, sources, missing = {}, [], []
    top = root / f"configs/search_{pipeline}_local_pipeline.yaml"
    cfg = read_yaml(top)
    expected = [
        f"pipeline/{pipeline}/{pipeline}_generate@generation",
        f"pipeline/{pipeline}/{pipeline}_evaluate@_global_",
        f"pipeline/{pipeline}/{pipeline}_analyze@_global_",
        "_self_",
    ]
    if cfg.get("defaults") != expected:
        raise ValueError(
            "Custom pipeline defaults are not supported by this static planner; inspect with Hydra on a prepared installation"
        )
    for stage in ("generate", "evaluate", "analyze"):
        path = root / f"configs/pipeline/{pipeline}/{pipeline}_{stage}.yaml"
        if not path.is_file():
            if stage == "generate":
                raise ValueError(f"Missing generation config: {path}")
            missing.append(str(path.relative_to(root)))
            continue
        leaf = read_yaml(path)
        sources.append({"path": str(path.relative_to(root)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        leaf.pop("defaults", None)
        base = merge(base, {"generation": leaf} if stage == "generate" else leaf)
    sources.append({"path": str(top.relative_to(root)), "sha256": hashlib.sha256(top.read_bytes()).hexdigest()})
    cfg.pop("defaults")
    return merge(base, cfg), sources, missing


def env_references(value) -> list[str]:
    return sorted(set(re.findall(r"\$\{oc\.env:([A-Za-z_][A-Za-z0-9_]*)", json.dumps(value))))


def hydra_value(value) -> str:
    # Hydra dictionary keys are unquoted; string values must retain their types.
    if isinstance(value, dict):
        if any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(k)) for k in value):
            raise ValueError("Unsupported Hydra dictionary key")
        return "{" + ",".join(f"{k}:{hydra_value(v)}" for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ",".join(hydra_value(v) for v in value) + "]"
    if (
        isinstance(value, str)
        and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_./-]*", value)
        and value.lower() not in {"true", "false", "null"}
    ):
        return value
    return json.dumps(value, allow_nan=False)


def override_args(patch: dict, prefix: str = "") -> list[str]:
    args = []
    for key, value in patch.items():
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(key)):
            raise ValueError(f"Unsupported override key: {key!r}")
        path = prefix + key
        if isinstance(value, dict) and path not in {"generation.reward_model", "lora"}:
            args.extend(override_args(value, path + "."))
        else:
            args.append(f"++{path}={hydra_value(value)}")
    return args


def build_plan(root: Path, pipeline: str, patch: dict, *, samples: int | None = None) -> tuple[dict, dict, str]:
    base, sources, missing = source_config(root, pipeline)
    patch = deepcopy(patch)
    if "defaults" in patch:
        raise ValueError("Changing Hydra defaults requires full composition, outside this planner's scope")
    cfg = merge(base, patch)
    stem, registry_rel, registry_key = PIPELINES[pipeline]
    if cfg.get("ckpt_name") != stem + ".ckpt" or Path(str(cfg.get("autoencoder_ckpt_path"))).name != stem + "_ae.ckpt":
        raise ValueError(f"Released {pipeline} pipeline requires {stem}.ckpt and {stem}_ae.ckpt")
    if pipeline != "binder" and cfg.get("lora") != LORA:
        raise ValueError(f"Released {pipeline} checkpoint requires LoRA {LORA}")
    if pipeline == "ame" and get(cfg, "env_vars.USE_V2_COMPLEXA_ARCH") != "True":
        raise ValueError('AME requires env_vars.USE_V2_COMPLEXA_ARCH as the string "True"')
    if pipeline != "binder":
        # Carry the released checkpoint contract into a portable corrective patch.
        for key in ("ckpt_name", "autoencoder_ckpt_path", "lora"):
            patch.setdefault(key, deepcopy(cfg[key]))
        if pipeline == "ame":
            patch.setdefault("env_vars", deepcopy(cfg["env_vars"]))
    for name in ("run_name", "generation.task_name"):
        if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", str(get(cfg, name, ""))):
            raise ValueError(f"{name} must be a single explicit name, not an interpolation or shell expression")
    if get(patch, "generation.task_name") is None or "run_name" not in patch:
        raise ValueError("Supply an explicit target key and unique run name; do not inherit an example target")

    dataset = get(cfg, "generation.dataloader.dataset")
    if (
        not isinstance(dataset, dict)
        or get(dataset, "nres._target_") != "proteinfoundation.datasets.gen_dataset.UniformInt"
    ):
        raise ValueError("Budget calculation supports the released UniformInt dataset only")
    dataset_target = dataset.get("task_name")
    if dataset_target not in {"${...task_name}", get(cfg, "generation.task_name")}:
        raise ValueError("Dataset target must agree with generation.task_name; conflicting target overrides are unsafe")
    repeats = positive(dataset.get("nrepeat_per_sample"), "nrepeat_per_sample")
    if samples is not None:
        positive(samples, "samples")
        if samples % repeats:
            raise ValueError(
                "Exact base samples must be divisible by nrepeat_per_sample; choose another budget or repeat count"
            )
        put(patch, "generation.dataloader.dataset.nres.nsamples", samples // repeats)
        cfg = merge(base, patch)
    nsamples = positive(get(cfg, "generation.dataloader.dataset.nres.nsamples"), "nsamples")
    jobs = positive(cfg.get("gen_njobs"), "gen_njobs")
    positive(cfg.get("eval_njobs"), "eval_njobs")
    positive(get(cfg, "generation.dataloader.batch_size"), "batch_size")
    algorithm = get(cfg, "generation.search.algorithm")
    if algorithm not in SEARCHES:
        raise ValueError(f"Unsupported search: {algorithm}")
    reward = get(cfg, "generation.reward_model")
    if algorithm != "single-pass" and (not isinstance(reward, dict) or not reward.get("reward_models")):
        raise ValueError("Reward-guided search requires an active reward model; AME defaults to null")
    if get(patch, "generation.search.beam_search.beam_width") is not None and algorithm != "beam-search":
        raise ValueError("Beam width does not activate beam search; select algorithm=beam-search explicitly")
    if algorithm == "beam-search":
        positive(get(cfg, "generation.search.beam_search.beam_width"), "beam_width")
    refolder = get(cfg, "metric.binder_folding_method")
    if refolder not in BACKENDS:
        raise ValueError(
            "Select --refolder colabdesign, rf3_latest or esmfold; the snapshot may omit evaluation defaults"
        )
    limit = get(cfg, "generation.filter.filter_samples_limit")
    if limit is not None:
        positive(limit, "filter_samples_limit")
    registry = root / "configs" / registry_rel
    target = get(cfg, "generation.task_name")
    registered = registry.is_file() and target in read_yaml(registry).get(registry_key, {})
    evaluation = set(BACKENDS[refolder])
    if get(cfg, "metric.compute_esm_metrics") or (
        get(cfg, "metric.compute_monomer_metrics") and "esmfold" in get(cfg, "metric.monomer_folding_models", [])
    ):
        evaluation.add("ESM_DIR")
    analysis = []
    if get(cfg, "aggregation.compute_diversity"):
        analysis.append("FOLDSEEK_EXEC")
    if get(cfg, "aggregation.compute_mmseqs_diversity"):
        analysis.append("MMSEQS_EXEC")
    plan = {
        "schema_version": 1,
        "scope": "static_plan",
        "pipeline": f"configs/search_{pipeline}_local_pipeline.yaml",
        "runtime_validated": False,
        "gpu_execution": "not_run",
        "sources": sources,
        "composition": "Direct stage YAMLs only; nested defaults, target inputs and interpolations require validation on the prepared installation.",
        "missing_stage_files": missing,
        "target": {
            "key": target,
            "registry": str(registry.relative_to(root)),
            "registered": registered,
            "status": "registered_inputs_unverified" if registered else "unresolved",
            "required_inputs": ["target structure", "binder length", "ligand selection/chemistry", "contig_atoms"]
            if pipeline == "ame"
            else [
                "target structure",
                "binder length",
                "ligand selection/chemistry" if pipeline == "ligand_binder" else "epitope/hotspots",
            ],
        },
        "checkpoints": {
            "model": str(Path(cfg["ckpt_path"]) / cfg["ckpt_name"]),
            "autoencoder": cfg["autoencoder_ckpt_path"],
            "lora": cfg.get("lora"),
            "env_vars": cfg.get("env_vars", {}),
        },
        "sample_budget": {
            "nsamples": nsamples,
            "nrepeat_per_sample": repeats,
            "requested_base_samples": nsamples * repeats,
            "gen_njobs": jobs,
            "per_job_base_samples": job_counts(nsamples, repeats, jobs),
            "filter_samples_limit": limit,
            "observed_generated": None,
            "observed_passing": None,
        },
        "search": {
            "algorithm": algorithm,
            "beam_width": get(cfg, "generation.search.beam_search.beam_width") if algorithm == "beam-search" else None,
        },
        "dependencies": {
            "generation_reward": env_references(reward),
            "refinement": env_references(get(cfg, "generation.refinement")),
            "evaluation": sorted(evaluation),
            "analysis": analysis,
            "evaluation_refolder": refolder,
            "complete": False,
        },
        "unvalidated": [
            "nested Hydra defaults and overrides",
            "target structures and selections",
            "runtime, checkpoint contents and tool/backend access",
            "GPU allocation and capacity",
        ],
    }
    argv = ["complexa", "design", plan["pipeline"], *override_args(patch)]
    plan["command_argv"] = argv
    # No shell eval, no environment sourcing, no ML command is executed here.
    script = '#!/usr/bin/env bash\nset -euo pipefail\n: "${COMPLEXA_PROJECT_ROOT:?Set the prepared Complexa project root}"\ncd -- "$COMPLEXA_PROJECT_ROOT"\n'
    if not registered:
        script += "# Target registration/inputs were not validated in this snapshot. Resolve before launch.\n"
    if target.startswith("UNREGISTERED_"):
        script += ': "${COMPLEXA_TARGET:?Set the registered target key after supplying its scientific inputs}"\n'
    rendered = [shlex.quote(arg) for arg in argv]
    if target.startswith("UNREGISTERED_"):
        rendered[3:] = [
            '"++generation.task_name=$COMPLEXA_TARGET"'
            if arg == shlex.quote(f"++generation.task_name={target}")
            else arg
            for arg in rendered[3:]
        ]
    script += " \\\n  ".join([" ".join(rendered[:3]), *rendered[3:]]) + "\n"
    return plan, patch, script


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--pipeline", choices=PIPELINES, required=True)
    parser.add_argument("--target", required=True, help="Registry key, or explicit UNREGISTERED_* placeholder")
    parser.add_argument("--run-name", required=True)
    parser.add_argument(
        "--out-dir", type=Path, required=True, help="New directory; existing artifacts are never overwritten"
    )
    parser.add_argument(
        "--revision", action="store_true",
        help="If --out-dir already exists, write to a new sibling directory and report its path",
    )
    parser.add_argument("--overrides", type=Path, help="YAML mapping applied over source defaults before CLI choices")
    parser.add_argument("--samples", type=int, help="Exact global base sample budget, not retained or passing designs")
    parser.add_argument("--repeats", type=int)
    parser.add_argument("--gen-jobs", type=int)
    parser.add_argument("--eval-jobs", type=int)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--filter-limit", type=int)
    parser.add_argument("--search", choices=SEARCHES)
    parser.add_argument("--beam-width", type=int)
    parser.add_argument("--refolder", choices=BACKENDS)
    parser.add_argument("--ame-rf3-reward", action="store_true", help="Explicitly enable the documented AME RF3 reward")
    args = parser.parse_args()
    try:
        patch = read_yaml(args.overrides) if args.overrides else {}
        options = {
            "run_name": args.run_name,
            "generation.task_name": args.target,
            "generation.dataloader.dataset.nrepeat_per_sample": args.repeats,
            "gen_njobs": args.gen_jobs,
            "eval_njobs": args.eval_jobs,
            "generation.dataloader.batch_size": args.batch_size,
            "generation.filter.filter_samples_limit": args.filter_limit,
            "generation.search.algorithm": args.search,
            "generation.search.beam_search.beam_width": args.beam_width,
            "metric.binder_folding_method": args.refolder,
        }
        for key, value in options.items():
            if value is not None:
                put(patch, key, value)
        if args.ame_rf3_reward:
            if args.pipeline != "ame":
                raise ValueError("--ame-rf3-reward is only for AME")
            patch = merge(patch, read_yaml(Path(__file__).resolve().parent.parent / "config/ame_rf3_reward.yaml"))
        plan, patch, script = build_plan(args.project_root.resolve(), args.pipeline, patch, samples=args.samples)
        # Syntax-check via stdin before writing any artifacts, without a temporary file.
        subprocess.run(
            ["bash", "-n"], shell=False, input=script, text=True, check=True, timeout=BASH_SYNTAX_TIMEOUT_SECONDS
        )
        output_dir = args.out_dir
        try:
            output_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            if not args.revision:
                raise ValueError(
                    f"Output already exists: {output_dir}. Preserve it; use --revision "
                    "or choose a new --out-dir. Do not delete an earlier plan to retry."
                ) from None
            output_dir = Path(tempfile.mkdtemp(prefix=f"{output_dir.name}-", dir=output_dir.parent))
        for name, contents in (
            ("campaign_plan.json", json.dumps(plan, indent=2) + "\n"),
            ("campaign_overrides.yaml", yaml.safe_dump(patch, sort_keys=False)),
            ("launch.sh", script),
        ):
            with (output_dir / name).open("x") as handle:
                handle.write(contents)
        print(
            json.dumps(
                {
                    "output_dir": str(output_dir.resolve()),
                    "sample_budget": plan["sample_budget"],
                    "dependencies": plan["dependencies"],
                    "target": plan["target"],
                    "missing_stage_files": plan["missing_stage_files"],
                },
                indent=2,
            )
        )
        return 0
    except (ValueError, TypeError, OSError, yaml.YAMLError, subprocess.SubprocessError) as exc:
        print(f"Plan not written: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
