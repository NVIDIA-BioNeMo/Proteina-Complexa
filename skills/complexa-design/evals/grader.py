#!/usr/bin/env python3
"""Add deterministic artifact checks alongside ACES; never execute agent code.

Reads the same /workspace/output artifacts for either arm. Case 004 has no
artifact obligations (vacuous pass, excluded from artifact-only summaries).
These checks do not establish
biological quality, hardware allocation, or completed GPU inference; ACES and
the GPU integration suite remain responsible for those outcomes.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
from pathlib import Path

import yaml


def read_artifact(root: Path, name: str) -> str:
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise ValueError(f"Missing, out-of-scope or oversized artifact: {name}")
    return path.read_text()


def get(data, path: str):
    for key in path.split("."):
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


def shell_lines(script: str):
    """Join shell continuations without swallowing commands after comments."""
    # Bash starts a comment only at a word boundary; shlex also treats a hash
    # inside an unquoted word as a comment. Strip only actual comments first.
    pending = ""
    for physical_line in script.split("\n"):
        line = pending + physical_line
        quote, escaped, boundary = None, False, True
        for i, char in enumerate(line):
            if escaped:
                escaped = False
                boundary = False
                continue
            if char == "\\" and quote != "'":
                escaped = True
            elif quote:
                if char == quote:
                    quote = None
            elif char in "\"'":
                quote = char
            elif char == "#" and boundary:
                line = line[:i]
                break
            boundary = not quote and not escaped and char in " \t;&|()<>"
        if escaped:
            pending = line[:-1]
            continue
        yield line
        pending = ""
    if pending:
        raise ValueError("Incomplete shell line continuation")


def shell_words(line: str) -> list[str]:
    """Tokenize a logical line, keeping shell operators and literal hashes."""
    lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|()<>")
    lexer.commenters = ""
    lexer.whitespace_split = True
    return list(lexer)


def shell_setup(words: list[str]) -> bool:
    """Allow strict shell options, a working directory, and readiness guards."""
    command, *args = words
    if command == "set":
        if len(args) >= 2 and args[-1] in {"pipefail", "errexit", "nounset"}:
            if not re.fullmatch(r"-[eEu]*o", args[-2]):
                return False
            args = args[:-2]
            return all(re.fullmatch(r"-[eEu]+", arg) for arg in args)
        return bool(args) and all(re.fullmatch(r"-[eEu]+", arg) for arg in args)
    if command == "cd":
        if args[:1] == ["--"]:
            args = args[1:]
        return len(args) == 1 and bool(re.fullmatch(
            r"[\w./ -]+|\$[A-Za-z_][A-Za-z0-9_]*|\$\{[A-Za-z_][A-Za-z0-9_]*\}", args[0]
        )) and not args[0].startswith("-")
    if command == ":":
        return len(args) == 1 and bool(re.fullmatch(r"\$\{[A-Za-z_][A-Za-z0-9_]*:?\?[^$`{}]*\}", args[0]))
    return False


def launch_overrides(script: str) -> tuple[str, dict]:
    """Read one direct literal invocation; reject other executable statements.

    This deliberately supports only comments, simple shell setup, and the CLI.
    Shell syntax validation never runs the script, including its substitutions.
    """
    subprocess.run(
        ["bash", "-n"], input=script, text=True, capture_output=True, check=True, timeout=5, shell=False
    )
    invocation = None
    for line in shell_lines(script):
        words = shell_words(line)
        if words[-1:] == [";"]:
            words = words[:-1]
        if not words:
            continue
        if invocation is not None:
            raise ValueError("Unexpected command after complexa design")
        if words[:2] == ["complexa", "design"] and len(words) >= 3:
            invocation = words
        elif not shell_setup(words):
            raise ValueError("Expected simple shell setup followed by a direct complexa design invocation")
    if invocation is None:
        raise ValueError("Expected one literal complexa design invocation")
    values = {}
    for token in invocation[3:]:
        if not re.match(r"\+{0,2}[A-Za-z_][A-Za-z0-9_.]*=", token):
            raise ValueError("Nonliteral launch argument")
        key, value = token.lstrip("+").split("=", 1)
        if "$" in value or "`" in value or key in values:
            raise ValueError("Dynamic or duplicate launch override")
        if not re.fullmatch(r"[A-Za-z0-9_./:+-]+|'[^']*'|\"[^\"]*\"", value):
            raise ValueError("Expected a literal scalar override")
        # Parse only primitive fields used below; complex YAML values are not executed.
        values[key] = yaml.safe_load(value)
    return invocation[2], values


def string_array_contains(value, required: str) -> bool:
    """Require a JSON array of strings before checking a dependency's presence."""
    return isinstance(value, list) and all(isinstance(item, str) for item in value) and required in value


def grade(entry: dict, root: Path) -> dict:
    case = entry["id"]
    checks, errors = {}, []
    if case == "complexa-design-004":
        return {
            "custom_metrics": {"artifact_contract": 1.0},
            "details": {
                "artifact_contract": {
                    "applicable": False,
                    "reason": "No artifact obligations. Exclude from artifact-only summaries; ACES grades routing and behavior.",
                }
            },
        }
    try:
        if case in {"complexa-design-001", "complexa-design-002", "complexa-design-003"}:
            mode = json.loads(read_artifact(root, "execution_mode.json"))
            checks["mode_schema"] = (
                mode.get("selected_mode") in {"cpu", "gpu", "undetermined"}
                and mode.get("task_status") in {"completed", "blocked", "failed", "awaiting_confirmation"}
                and mode.get("gpu_execution") in {"completed", "not_run", "failed"}
                and isinstance(mode.get("reason"), str)
                and bool(mode["reason"].strip())
                and bool(mode.get("evidence"))
            )
            checks["mode_consistency"] = not (
                (mode.get("selected_mode") != "gpu" and mode.get("gpu_execution") != "not_run")
                or (mode.get("selected_mode") == "undetermined" and mode.get("task_status") == "completed")
                or (
                    mode.get("selected_mode") == "gpu"
                    and mode.get("task_status") == "completed"
                    and mode.get("gpu_execution") != "completed"
                )
            )
            if mode.get("selected_mode") == "cpu" and mode.get("task_status") == "completed":
                files = {
                    "complexa-design-001": ["launch.sh", "readiness.md"],
                    "complexa-design-002": ["ligand_run_plan.md"],
                    "complexa-design-003": ["ame_review.md"],
                }[case]
                for file in files:
                    content = read_artifact(root, file)
                    checks[file + "_nonempty"] = bool(content.strip())
                    if file.endswith(".sh"):
                        subprocess.run(
                            ["bash", "-n"], input=content, text=True, capture_output=True, check=True, timeout=5
                        )
                        checks["shell_syntax"] = True
            # No hidden requirement on format of legacy evidence paths or prose.
        elif case == "complexa-design-005":
            pipeline, args = launch_overrides(read_artifact(root, "launch.sh"))
            expected = {
                "run_name": "pdl1_budget",
                "generation.task_name": "02_PDL1",
                "gen_njobs": 2,
                "eval_njobs": 1,
                "generation.dataloader.batch_size": 4,
                "generation.dataloader.dataset.nres.nsamples": 20,
                "generation.dataloader.dataset.nrepeat_per_sample": 3,
                "generation.search.algorithm": "beam-search",
                "generation.search.beam_search.beam_width": 8,
                "generation.filter.filter_samples_limit": 12,
                "metric.binder_folding_method": "colabdesign",
            }
            checks["pipeline"] = pipeline == "configs/search_binder_local_pipeline.yaml"
            for key, value in expected.items():
                checks[key] = args.get(key) == value and type(args.get(key)) is type(value)
            checks["no_extra_changes"] = set(args) == set(expected)
            budget = json.loads(read_artifact(root, "budget.json"))
            counts = budget.get("per_job_base_samples")
            checks["global_budget"] = (
                type(budget.get("requested_base_samples")) is int
                and budget["requested_base_samples"] == 60
                and counts == [40, 20]
                and all(type(n) is int for n in counts)
            )
            checks["no_observed_results"] = (
                budget.get("observed_generated", "missing") is None
                and budget.get("observed_passing", "missing") is None
            )
            checks["review"] = bool(read_artifact(root, "budget_review.md").strip())
        elif case == "complexa-design-006":
            review = json.loads(read_artifact(root, "dependency_review.json"))
            checks["not_ready"] = review.get("ready_to_run") is False
            checks["reward_dependency"] = string_array_contains(review.get("generation_reward_environment"), "AF2_DIR")
            checks["evaluation_dependency"] = review.get(
                "evaluation_refolder"
            ) == "esmfold" and string_array_contains(review.get("evaluation_environment"), "ESM_DIR")
            checks["missing_af2"] = string_array_contains(review.get("missing_prerequisites"), "AF2_DIR")
            checks["preserve_objective"] = review.get("change_generation_objective") is False
            checks["review"] = bool(read_artifact(root, "dependency_review.md").strip())
        elif case == "complexa-design-007":
            patch = yaml.safe_load(read_artifact(root, "ame_patch.yaml"))
            expected = {
                "run_name": "ame_review",
                "ckpt_name": "complexa_ame.ckpt",
                "autoencoder_ckpt_path": "./ckpts/complexa_ame_ae.ckpt",
                "lora.r": 32,
                "lora.lora_alpha": 64.0,
                "lora.lora_dropout": 0.0,
                "lora.train_bias": "none",
                "env_vars.USE_V2_COMPLEXA_ARCH": "True",
                "generation.task_name": "UNREGISTERED_MOTIF_TASK",
                "generation.search.algorithm": "beam-search",
                "generation.search.beam_search.beam_width": 8,
                "generation.reward_model._target_": "proteinfoundation.rewards.base_reward.CompositeRewardModel",
                "generation.reward_model.reward_models.rf3folding._target_": "proteinfoundation.rewards.rf3_reward.RF3RewardRunner",
                "generation.reward_model.reward_models.rf3folding.ckpt_path": "${oc.env:RF3_CKPT_PATH}",
                "generation.reward_model.reward_models.rf3folding.rf3_path": "${oc.env:RF3_EXEC_PATH}",
                "generation.reward_model.reward_models.rf3folding.normalize_pae": True,
            }
            for key, value in expected.items():
                checks[key] = (
                    get(patch, key) == value and type(get(patch, key)) is type(value)
                    if isinstance(value, (str, bool))
                    else get(patch, key) == value
                )
            weight = get(patch, "generation.reward_model.reward_models.rf3folding.reward_weights.min_ipAE")
            checks["reward_direction"] = (
                isinstance(weight, (int, float)) and not isinstance(weight, bool) and weight < 0
            )
            checks["preserve_evaluation_and_criteria"] = (
                isinstance(patch, dict)
                and not {"aggregation", "defaults"}.intersection(patch)
                and patch.get("metric", {}) in ({}, {"binder_folding_method": "rf3_latest"})
                and "refinement" not in patch.get("generation", {})
            )
            checks["review"] = bool(read_artifact(root, "ame_review.md").strip())
        else:
            raise ValueError(f"No artifact contract defined for {case}")
    except (OSError, ValueError, TypeError, AttributeError, yaml.YAMLError, subprocess.SubprocessError) as exc:
        checks["artifact_read_or_parse"] = False
        errors.append(str(exc))
    # Contract success is conjunctive: partial checks must not hide a critical failure.
    score = float(bool(checks) and all(checks.values()))
    return {
        "custom_metrics": {"artifact_contract": score},
        "details": {
            "artifact_contract": {
                "applicable": True,
                "checks": checks,
                "errors": errors,
                "scope": "Artifact structure and declared configuration; not scientific validation.",
            }
        },
    }


def main() -> None:
    tests = Path(os.environ.get("HARBOR_TESTS_DIR", "/tests"))
    logs = Path(os.environ.get("HARBOR_LOGS_DIR", "/logs"))
    verifier = Path(os.environ.get("HARBOR_VERIFIER_DIR", str(logs / "verifier")))
    entry = json.loads(Path(os.environ.get("HARBOR_ENTRY_JSON", str(tests / "entry.json"))).read_text())
    root = Path(os.environ.get("COMPLEXA_EVAL_OUTPUT", "/workspace/output"))
    result = grade(entry, root)
    dest = Path(os.environ.get("HARBOR_REWARD_JSON", str(verifier / "reward.json")))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2) + "\n")
    # ACES's existing reward.txt is authoritative in default_plus_custom mode.


if __name__ == "__main__":
    main()
