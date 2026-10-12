"""Behavioral contracts for CPU-only skill tooling; no model imports or weights."""

import ast
import importlib.util
import json
import logging
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from hydra.core.override_parser.overrides_parser import OverridesParser
from omegaconf import OmegaConf

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills/complexa-design"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


planner = load("campaign_planner", SKILL / "scripts/prepare_campaign.py")
gpu = load("gpu_probe", ROOT / "skills/_shared/scripts/gpu_probe.py")
grader = load("artifact_grader", SKILL / "evals/grader.py")
experiment = load("experiment", SKILL / "evals/prepare_experiment.py")


class PlannerTests(unittest.TestCase):
    def options(self, pipeline="binder"):
        return {
            "run_name": "pdl1_budget",
            "generation": {
                "task_name": "02_PDL1" if pipeline == "binder" else "UNREGISTERED_MOTIF_TASK",
                "dataloader": {"batch_size": 4, "dataset": {"nrepeat_per_sample": 3}},
                "search": {"algorithm": "beam-search", "beam_search": {"beam_width": 8}},
                "filter": {"filter_samples_limit": 12},
            },
            "gen_njobs": 2,
            "eval_njobs": 1,
            "metric": {"binder_folding_method": "colabdesign" if pipeline == "binder" else "rf3_latest"},
        }

    def test_budget_matches_real_split_by_job(self):
        tree = ast.parse((ROOT / "src/proteinfoundation/generate.py").read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "split_by_job")
        namespace = {"sys": sys, "logger": logging.getLogger(__name__)}
        exec(compile(ast.Module(body=[node], type_ignores=[]), "generate.py", "exec"), namespace)
        for n, repeats, jobs in [(20, 3, 2), (50, 1, 2), (1, 1, 3), (7, 5, 3), (2, 2, 1)]:
            actual = []
            for job in range(jobs):
                cfg = OmegaConf.create(
                    {
                        "dataloader": {
                            "dataset": {
                                "nres": {"nsamples": n},
                                "nrepeat_per_sample": repeats,
                                "conditional_features": None,
                            }
                        }
                    }
                )
                try:
                    split = namespace["split_by_job"](cfg, job, jobs).dataloader.dataset
                    actual.append(split.nres.nsamples * split.nrepeat_per_sample)
                except SystemExit as exc:
                    self.assertEqual(exc.code, 0)
                    actual.append(0)
            self.assertEqual(planner.job_counts(n, repeats, jobs), actual)
            self.assertEqual(sum(actual), n * repeats)

    def test_snapshot_budget_and_no_fabricated_outcomes(self):
        plan, _, script = planner.build_plan(SKILL / "evals/files/project", "binder", self.options(), samples=60)
        self.assertEqual(plan["sample_budget"]["per_job_base_samples"], [40, 20])
        self.assertEqual(plan["sample_budget"]["nsamples"], 20)
        self.assertIsNone(plan["sample_budget"]["observed_generated"])
        self.assertFalse(plan["runtime_validated"])
        self.assertEqual(len(plan["missing_stage_files"]), 2)
        subprocess.run(["bash", "-n"], input=script, text=True, check=True)

    def test_nondivisible_budget_rejected(self):
        with self.assertRaisesRegex(ValueError, "divisible"):
            planner.build_plan(ROOT, "binder", self.options(), samples=61)

    def test_conflicting_dataset_target_rejected(self):
        options = self.options()
        options["generation"]["dataloader"]["dataset"]["task_name"] = "UNRELATED_TARGET"
        with self.assertRaisesRegex(ValueError, "Dataset target"):
            planner.build_plan(ROOT, "binder", options)

    def test_refolder_does_not_remove_reward(self):
        options = self.options()
        options["metric"]["binder_folding_method"] = "esmfold"
        plan, _, _ = planner.build_plan(ROOT, "binder", options, samples=60)
        self.assertEqual(plan["dependencies"]["generation_reward"], ["AF2_DIR"])
        self.assertIn("ESM_DIR", plan["dependencies"]["evaluation"])

    def test_inactive_beam_width_rejected(self):
        options = self.options()
        del options["generation"]["search"]["algorithm"]
        with self.assertRaisesRegex(ValueError, "does not activate"):
            planner.build_plan(ROOT, "binder", options)

    def test_ame_rejects_wrong_model_and_null_reward(self):
        options = self.options("ame")
        with self.assertRaisesRegex(ValueError, "active reward"):
            planner.build_plan(ROOT, "ame", options)
        recipe = planner.read_yaml(SKILL / "config/ame_rf3_reward.yaml")
        options = planner.merge(options, recipe)
        for key, value in (
            ("ckpt_name", "complexa.ckpt"),
            ("lora", None),
            ("env_vars", {"USE_V2_COMPLEXA_ARCH": True}),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                planner.build_plan(ROOT, "ame", dict(options, **{key: value}))

    def test_ame_recipe_matches_source_example_and_hydra(self):
        text = (ROOT / "configs/pipeline/ame/ame_generate.yaml").read_text()
        example = text.split("# reward_model:\n", 1)[1].split("#     # TMOL", 1)[0]
        source = yaml.safe_load(
            "reward_model:\n" + "\n".join(line[2:] for line in example.splitlines() if line.startswith("# "))
        )
        recipe = planner.read_yaml(SKILL / "config/ame_rf3_reward.yaml")
        self.assertEqual(recipe["generation"]["reward_model"], source["reward_model"])
        plan, overrides, script = planner.build_plan(ROOT, "ame", planner.merge(self.options("ame"), recipe))
        composed = OmegaConf.create({"generation": {"reward_model": None}})
        for arg in plan["command_argv"][3:]:
            parsed = OverridesParser.create().parse_override(arg)
            OmegaConf.update(composed, parsed.key_or_group, parsed.value(), merge=True, force_add=True)
        self.assertEqual(composed.env_vars.USE_V2_COMPLEXA_ARCH, "True")
        self.assertEqual(composed.generation.reward_model.reward_models.rf3folding.reward_weights.min_ipAE, -1)
        self.assertEqual(overrides["lora"], planner.LORA)
        self.assertIn("COMPLEXA_TARGET:?", script)
        self.assertFalse(plan["target"]["registered"])

    def test_cli_does_not_overwrite_or_execute(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "plan"
            command = [
                sys.executable,
                str(SKILL / "scripts/prepare_campaign.py"),
                "--project-root",
                str(ROOT),
                "--pipeline",
                "binder",
                "--target",
                "02_PDL1",
                "--run-name",
                "smoke",
                "--samples",
                "50",
                "--out-dir",
                str(out),
            ]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            content = (out / "launch.sh").read_bytes()
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2)
            self.assertEqual((out / "launch.sh").read_bytes(), content)


class ProbeTests(unittest.TestCase):
    def evidence(self, *, devices=(), env=None, status="missing", stdout="", error=None):
        return {
            "device_nodes": list(devices),
            "allocation_env": env or {},
            "device_scan_error": error,
            "nvidia_smi": {"status": status, "stdout": stdout, "stderr": "", "returncode": None},
        }

    def test_cpu_absence_uses_multiple_signals(self):
        self.assertEqual(gpu.classify(self.evidence())["status"], "absent")
        self.assertEqual(gpu.classify(self.evidence(status="error"))["status"], "unknown")
        self.assertEqual(gpu.classify(self.evidence(env={"NVIDIA_VISIBLE_DEVICES": "all"}))["status"], "unknown")
        self.assertEqual(gpu.classify(self.evidence(env={"CUDA_VISIBLE_DEVICES": "0"}))["status"], "unknown")

    def test_allocated_failures_stay_gpu_blockers(self):
        for evidence in [
            self.evidence(devices=["/dev/nvidia0"], status="error"),
            self.evidence(env={"SLURM_JOB_GPUS": "0"}),
            self.evidence(env={"SLURM_STEP_GPUS": "0"}, error="PermissionError"),
            self.evidence(
                devices=["/dev/nvidia0"], env={"CUDA_VISIBLE_DEVICES": "-1"}, status="ok", stdout="H100, 81920, 580\n"
            ),
        ]:
            with self.subTest(evidence=evidence):
                result = gpu.classify(evidence)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["allocation"], "allocated")
                self.assertFalse(result["available"])

    def test_accessible_management_and_malformed_probe(self):
        result = gpu.classify(self.evidence(devices=["/dev/nvidia0"], status="ok", stdout="H100, 81920, 580\n"))
        self.assertEqual((result["status"], result["vram_gb"]), ("accessible", 80))
        bad = gpu.classify(self.evidence(status="ok", stdout="Error\n"))
        self.assertEqual(bad["status"], "unknown")

    def test_bounded_probe_and_environment_allowlist(self):
        with (
            patch.object(gpu.shutil, "which", return_value="/fake/nvidia-smi"),
            patch.object(gpu.subprocess, "run", side_effect=subprocess.TimeoutExpired("nvidia-smi", 8)) as run,
            patch.dict(os.environ, {"SECRET_TOKEN": "never-log-me", "SLURM_JOB_GPUS": "0"}, clear=True),
        ):
            result = gpu.collect()
        self.assertEqual(run.call_args.kwargs["timeout"], 8)
        self.assertEqual(result["evidence"]["nvidia_smi"]["status"], "timeout")
        self.assertNotIn("never-log-me", json.dumps(result))

    def test_preflight_does_not_source_dotenv_or_hash_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ckpts").mkdir()
            (root / "ckpts/complexa.ckpt").write_bytes(b"test checkpoint")
            (root / ".env").write_text(
                f"CKPT_PATH={root}/ckpts\nSECRET_TOKEN=hidden\nLOCAL_DATA_PATH=$(touch {root}/executed)\n"
            )
            script = ROOT / "skills/_shared/scripts/preflight.sh"
            for hash_args, expected_hash in (([], False), (["--hash-checkpoints"], True)):
                run = subprocess.run(
                    ["bash", str(script), "--quiet", "--out", str(root / "preflight.json"), *hash_args],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    timeout=25,
                )
                self.assertEqual(run.returncode, 0, run.stderr)
                doc = json.loads((root / "preflight.json").read_text())
                self.assertEqual(bool(doc["checkpoints"]["complexa.ckpt"]["sha256"]), expected_hash)
                self.assertNotIn("hidden", json.dumps(doc))
                self.assertFalse((root / "executed").exists())


class GraderTests(unittest.TestCase):
    def test_budget_grades_real_script_not_only_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            options = PlannerTests().options()
            plan, _, script = planner.build_plan(ROOT, "binder", options, samples=60)
            (root / "launch.sh").write_text(script)
            (root / "budget.json").write_text(json.dumps(plan["sample_budget"]))
            (root / "budget_review.md").write_text("60 base samples; filter keeps at most 12, no measured outcomes.")
            entry = {"id": "complexa-design-005"}
            self.assertEqual(grader.grade(entry, root)["custom_metrics"]["artifact_contract"], 1)
            (root / "launch.sh").write_text(script.replace("nsamples=20", "nsamples=60"))
            self.assertEqual(grader.grade(entry, root)["custom_metrics"]["artifact_contract"], 0)

    def test_dependency_contract_rejects_false_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review = {
                "ready_to_run": False,
                "generation_reward_environment": ["AF2_DIR"],
                "evaluation_refolder": "esmfold",
                "evaluation_environment": ["ESM_DIR"],
                "missing_prerequisites": ["AF2_DIR"],
                "change_generation_objective": False,
            }
            (root / "dependency_review.md").write_text("AF2 weights still required for generation.")
            for ready, score in ((False, 1), (True, 0)):
                review["ready_to_run"] = ready
                (root / "dependency_review.json").write_text(json.dumps(review))
                self.assertEqual(
                    grader.grade({"id": "complexa-design-006"}, root)["custom_metrics"]["artifact_contract"], score
                )

    def test_ame_grader_rejects_null_reward_or_changed_criteria(self):
        proposal = planner.read_yaml(SKILL / "evals/files/ame_proposal.yaml")
        fixed = planner.merge(
            proposal,
            {
                "ckpt_name": "complexa_ame.ckpt",
                "autoencoder_ckpt_path": "./ckpts/complexa_ame_ae.ckpt",
                "lora": planner.LORA,
                "env_vars": {"USE_V2_COMPLEXA_ARCH": "True"},
            },
        )
        fixed = planner.merge(fixed, planner.read_yaml(SKILL / "config/ame_rf3_reward.yaml"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ame_review.md").write_text("Motif contig_atoms and ligand selections remain missing.")
            for doc, score in (
                (fixed, 1),
                (planner.merge(fixed, {"generation": {"reward_model": None}}), 0),
                (dict(fixed, aggregation={"success_thresholds": None}), 0),
            ):
                (root / "ame_patch.yaml").write_text(yaml.safe_dump(doc))
                self.assertEqual(
                    grader.grade({"id": "complexa-design-007"}, root)["custom_metrics"]["artifact_contract"], score
                )

    def test_missing_malformed_and_outside_artifacts_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for case in ("001", "002", "003", "005", "006", "007"):
                self.assertEqual(
                    grader.grade({"id": "complexa-design-" + case}, root)["custom_metrics"]["artifact_contract"], 0
                )
            (root / "execution_mode.json").write_text("[]")
            self.assertEqual(
                grader.grade({"id": "complexa-design-001"}, root)["custom_metrics"]["artifact_contract"], 0
            )
            with self.assertRaises(ValueError):
                grader.read_artifact(root, str(ROOT / "pyproject.toml"))


class ExperimentTests(unittest.TestCase):
    def test_paired_inputs_identical_and_modified_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "comparison"
            manifest = experiment.prepare(
                SKILL,
                SKILL,
                out,
                version="1.5.8",
                image="example/runner@sha256:" + "a" * 64,
                models={"codex": "pinned-model"},
                attempts=3,
            )
            self.assertEqual(manifest["planned_agent_executions"], 84)
            self.assertEqual(len(manifest["runs"]), 4)
            for cohort in ("original", "capability"):
                left = out / cohort / "instructions/complexa-design/evals"
                right = out / cohort / "helpers/complexa-design/evals"
                self.assertEqual(experiment.fingerprints(left), experiment.fingerprints(right))
            changed = out / "capability/helpers/complexa-design/SKILL.md"
            changed.write_text(changed.read_text() + "\nmodified\n")
            with patch.object(experiment.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "changed"):
                    experiment.execute(out / "experiment.json")
                run.assert_not_called()

    def test_reject_mutable_image_or_single_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            for image, attempts in (("runner:latest", 3), ("runner@sha256:" + "a" * 64, 1)):
                with self.subTest(image=image, attempts=attempts), self.assertRaises(ValueError):
                    experiment.prepare(
                        SKILL,
                        SKILL,
                        Path(tmp) / "plan",
                        version="1.5.8",
                        image=image,
                        models={"codex": "fixed"},
                        attempts=attempts,
                    )


if __name__ == "__main__":
    unittest.main()
