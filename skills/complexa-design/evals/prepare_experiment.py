#!/usr/bin/env python3
"""Freeze two paired comparisons: instruction-only vs baseline, helpers vs baseline.

Prepare only by default. Each comparison retains its own no-skill control so
SkillEvaluator can compute trusted paired coverage/lift. Original and capability
cohorts are separate; the seven-case aggregate is their union, not a new dataset.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
import subprocess
from pathlib import Path

import yaml


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprints(root: Path) -> dict[str, str]:
    return {
        str(p.relative_to(root)): digest(p)
        for p in sorted(root.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts
    }


def prepare(
    skill: Path,
    reference: Path,
    out: Path,
    *,
    version: str,
    image: str,
    models: dict[str, str],
    attempts: int = 5,
    seed: int = 20261012,
) -> dict:
    if not re.fullmatch(r"[\w./:-]+@sha256:[0-9a-f]{64}", image):
        raise ValueError("Use an immutable runner image reference ending @sha256:<64 hex digits>")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[a-z0-9.+-]*)", version):
        raise ValueError("Supply an exact evaluator version")
    if attempts < 2 or not models or any(not v.strip() or v.lower() == "default" for v in models.values()):
        raise ValueError("At least two attempts and explicit model IDs are required")
    if set(models) - {"codex", "claude-code"}:
        raise ValueError("This comparison supports codex and claude-code")
    for source in (skill, reference):
        if not (source / "SKILL.md").is_file() or out.resolve().is_relative_to(source.resolve()):
            raise ValueError("Use existing skill directories and an experiment directory outside them")
    dataset = json.loads((skill / "evals/evals.json").read_text())
    cohorts = {"original": dataset["evals"][:4], "capability": dataset["evals"][4:]}
    if [e["id"] for e in cohorts["original"]] != [f"complexa-design-{i:03}" for i in range(1, 5)]:
        raise ValueError("The original four-case cohort changed identity/order")
    out.mkdir(parents=True, exist_ok=False)
    runs = []
    for cohort, entries in cohorts.items():
        for variant, source in (("instructions", reference), ("helpers", skill)):
            dest = out / cohort / variant / "complexa-design"
            shutil.copytree(
                source,
                dest,
                ignore=shutil.ignore_patterns("evals", "__pycache__", "BENCHMARK.md", "skill-card.md", "skill.oms.sig"),
            )
            evaluation = dest / "evals"
            evaluation.mkdir()
            shutil.copytree(skill / "evals/files", evaluation / "files")
            shutil.copy2(skill / "evals/grader.py", evaluation / "grader.py")
            (evaluation / "evals.json").write_text(
                json.dumps({"skill_name": "complexa-design", "evals": entries}, indent=2) + "\n"
            )
            # Identical execution policy/fixtures/grader in both variants and arms.
            config = {
                "schema_version": 1,
                "skill_workspace": {"mode": "isolated", "include": []},
                "grading": {"mode": "default_plus_custom", "custom_metrics": ["artifact_contract"]},
                "harbor": {
                    "n_attempts": attempts,
                    "stop_on_pass": False,
                    "n_concurrent": 1,
                    "timeout_multiplier": 1.0,
                    "auto_scale_timeout": False,
                    "resources": {"cpus": 4, "memory_mb": 8192, "storage_mb": 20480},
                    "agents": {k: {"model": v} for k, v in models.items()},
                    "custom_dockerfile_mode": "preserve",
                    "base_image_mode": "disabled",
                },
            }
            (evaluation / "config.yml").write_text(yaml.safe_dump(config, sort_keys=False))
            environment = evaluation / "environment"
            environment.mkdir()
            # Prerequisites are part of the common pinned image, not installed by a skill arm.
            (environment / "Dockerfile").write_text(f"FROM {image}\nRUN python3 -c 'import yaml' && command -v bash\n")
            command = [
                "skillevaluator",
                "tier3",
                "evaluate",
                str(dest.resolve()),
                "--env-mode",
                "docker",
                "--agents",
                ",".join(models),
                "--no-stop-on-pass",
                "--harbor-keep-jobs",
                "--results-dir",
                str((out / "results" / cohort / variant).resolve()),
            ]
            runs.append(
                {
                    "cohort": cohort,
                    "variant": variant,
                    "skill": str(dest.resolve()),
                    "dataset_sha256": digest(evaluation / "evals.json"),
                    "command": command,
                }
            )
    random.Random(seed).shuffle(runs)
    manifest = {
        "schema_version": 1,
        "evaluator_version": version,
        "runner_image": image,
        "models": models,
        "attempts_per_case_arm": attempts,
        "order_seed": seed,
        "runs": runs,
        "planned_agent_executions": len(dataset["evals"]) * 2 * 2 * attempts * len(models),
        "comparison": "Two native paired comparisons with independent no-skill controls. Inspect baseline drift before comparing variants.",
        "reporting": "Report original and capability cohorts separately; union them with per-case weighting for the expanded suite. Exclude case 004 from artifact-only summaries. Preserve per-agent/per-case attempt scores, tokens and wall time.",
        "files": fingerprints(out),
    }
    (out / "experiment.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def execute(path: Path) -> None:
    manifest = json.loads(path.read_text())
    root = path.parent
    for name, expected in manifest["files"].items():
        file = (root / name).resolve()
        if not file.is_relative_to(root.resolve()) or digest(file) != expected:
            raise ValueError(f"Frozen experiment file changed: {name}")
    for cohort in ("original", "capability"):
        actual = {f"{cohort}/{name}": sha for name, sha in fingerprints(root / cohort).items()}
        expected = {name: sha for name, sha in manifest["files"].items() if name.startswith(cohort + "/")}
        if actual != expected:
            raise ValueError(f"Frozen experiment gained or lost files: {cohort}")
    result = subprocess.run(["skillevaluator", "--version"], capture_output=True, text=True, check=True, timeout=15)
    if manifest["evaluator_version"] not in re.findall(r"\d+\.\d+\.\d+[a-z0-9.+-]*", result.stdout):
        raise ValueError("Installed evaluator version does not match the experiment")
    for run in manifest["runs"]:
        # Contract validation must pass before spending any agent executions.
        subprocess.run(
            ["skillevaluator", "tier3", "validate", run["skill"], "--harbor-contract", "--strict", "--json"], check=True
        )
    for run in manifest["runs"]:
        subprocess.run(run["command"], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--reference-skill", type=Path)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--evaluator-version")
    parser.add_argument("--runner-image")
    parser.add_argument("--agent-model", action="append", default=[], metavar="AGENT=MODEL")
    parser.add_argument("--attempts", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20261012)
    parser.add_argument(
        "--execute-manifest", type=Path, help="Explicitly run a previously frozen experiment; invokes paid agents"
    )
    args = parser.parse_args()
    if args.execute_manifest:
        execute(args.execute_manifest.resolve())
        return
    if not all((args.reference_skill, args.out_dir, args.evaluator_version, args.runner_image, args.agent_model)):
        parser.error(
            "Preparation needs --reference-skill, --out-dir, --evaluator-version, --runner-image and --agent-model"
        )
    models = {}
    for item in args.agent_model:
        if "=" not in item:
            parser.error("--agent-model requires AGENT=MODEL")
        agent, model = item.split("=", 1)
        if agent in models:
            parser.error(f"Duplicate agent model: {agent}")
        models[agent] = model
    manifest = prepare(
        args.skill.resolve(),
        args.reference_skill.resolve(),
        args.out_dir.resolve(),
        version=args.evaluator_version,
        image=args.runner_image,
        models=models,
        attempts=args.attempts,
        seed=args.seed,
    )
    print(
        json.dumps(
            {
                "manifest": str(args.out_dir.resolve() / "experiment.json"),
                "planned_agent_executions": manifest["planned_agent_executions"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
