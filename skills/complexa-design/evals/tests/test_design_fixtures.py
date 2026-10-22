"""Validate research fixtures and their oracles against the first-party source.

Run from a Proteina-Complexa checkout. Requires numpy, pandas, and PyYAML, but
does not import model implementations, install dependencies, or perform inference.
Only unused runtime imports and scalar tensor arithmetic are stubbed below;
filter selection, reward routing, and success comparisons use production code.
"""

import ast
import csv
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pandas as pd
import yaml

EVALS = Path(__file__).resolve().parents[1]
ROOT = EVALS.parents[2]
SOURCE = EVALS / "files/design_source"
sys.path.insert(0, str(ROOT / "src"))


class Config(dict):
    """Minimal attribute access for the filter's already-resolved config."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


def load_source_module(relative_path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def runtime_stubs():
    hydra_config = SimpleNamespace(get=lambda: SimpleNamespace(job=SimpleNamespace(config_name="pilot")))
    return {
        "hydra": SimpleNamespace(
            main=lambda **kwargs: lambda function: function,
            core=SimpleNamespace(hydra_config=SimpleNamespace(HydraConfig=hydra_config)),
        ),
        "lightning": SimpleNamespace(),
        "torch": SimpleNamespace(
            Tensor=float,
            dtype=type,
            float32="float32",
            tensor=lambda value, dtype=None: float(value),
        ),
        "dotenv": SimpleNamespace(load_dotenv=lambda: None),
        "loguru": SimpleNamespace(logger=Mock()),
    }


class DesignFixtureTests(unittest.TestCase):
    def test_source_fidelity_and_syntax(self):
        manifest = json.loads((SOURCE / "source_manifest.json").read_text())
        self.assertEqual(manifest["revision"], "8fc6f5c85b38a2585ffaac555e708576dc4e8533")
        for filename, record in manifest["files"].items():
            with self.subTest(filename=filename):
                original = (ROOT / record["source"]).read_bytes()
                self.assertEqual(hashlib.sha256(original).hexdigest(), record["source_sha256"])
                excerpt = b"".join(original.splitlines(keepends=True)[record["start_line"] - 1 : record["end_line"]])
                self.assertEqual((SOURCE / filename).read_bytes(), excerpt)
                self.assertEqual(hashlib.sha256(excerpt).hexdigest(), record["sha256"])
                if filename.endswith(".py.txt"):
                    ast.parse(textwrap.dedent(excerpt.decode()))
                elif filename.endswith(".yaml"):
                    self.assertIsInstance(yaml.safe_load(excerpt), dict)

    def test_existing_cases_and_gpu_archive_are_preserved(self):
        cases = json.loads((EVALS / "evals.json").read_text())["evals"]
        digest = hashlib.sha256(json.dumps(cases[:4], sort_keys=True).encode()).hexdigest()
        self.assertEqual(digest, "2cb0836f75c1edca0bf9d58b39e022326ca0dea3b57382ac418ffe76447e61bc")
        gpu_digest = hashlib.sha256((EVALS / "gpu-integration.json").read_bytes()).hexdigest()
        self.assertEqual(gpu_digest, "c2af01e47d40a3e205881338e5240b93661474635c8546ab4c86d070749fe03c")

    def test_case_inputs_are_present_and_contained(self):
        cases = json.loads((EVALS / "evals.json").read_text())["evals"]
        self.assertEqual(len(cases), 9)
        self.assertEqual(len({case["id"] for case in cases}), len(cases))
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertTrue(case["prompt"] and case["expected_output"] and case["assertions"])
                for filename in case["files"]:
                    target = (EVALS / filename).resolve()
                    self.assertTrue(target.is_relative_to(EVALS / "files"))
                    self.assertTrue(target.exists())
        for path in (EVALS / "files").glob("*_review/*.yaml"):
            self.assertIsInstance(yaml.safe_load(path.read_text()), dict)

    def run_filter(self, limit, threshold):
        with patch.dict(sys.modules, runtime_stubs()):
            filtering = load_source_module("src/proteinfoundation/filter.py", "design_test_filter")
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            shutil.copy2(EVALS / "files/filter_review/rewards_pilot_0.csv", work)
            cfg = Config(
                root_path=str(work),
                base_config_name="pilot",
                generation=Config(
                    dataloader=Config(dataset=Config(nres=Config(nsamples=6))),
                    filter=Config(
                        filter_samples_limit=limit,
                        reward_threshold=threshold,
                        dedup_sequence=True,
                        delete_non_top_n_samples=False,
                    ),
                ),
            )
            filtering.main(cfg)
            return pd.read_csv(work / "top_samples_pilot.csv")["candidate_id"].tolist()

    def test_actual_filter_skips_threshold_at_or_below_cap(self):
        # These expectations exercise the actual implementation, including the
        # first-occurrence duplicate and the boundary where len == cap.
        for limit, threshold in ((100, 7.0), (100, -7 / 31), (4, -7 / 31)):
            with self.subTest(limit=limit, threshold=threshold):
                self.assertEqual(self.run_filter(limit, threshold), ["L04", "L03", "L01", "L06"])

    def test_actual_filter_applies_normalized_threshold_above_cap(self):
        self.assertEqual(self.run_filter(3, -7 / 31), ["L04", "L03"])
        self.assertEqual(self.run_filter(3, 7.0), [])
        rows = pd.read_csv(EVALS / "files/filter_review/rewards_pilot_0.csv")
        eligible = rows.dropna(subset=["total_reward"])
        self.assertTrue(((eligible.raw_min_ipAE / 31 + eligible.total_reward).abs() < 1e-12).all())
        # A separately reviewed implementation of the user's explicit policy.
        intended = eligible.sort_values("total_reward", ascending=False).drop_duplicates("aatype")
        intended = intended[intended.raw_min_ipAE <= 7].head(100)
        self.assertEqual(intended.candidate_id.tolist(), ["L02", "L04", "L03"])

    def test_composite_routes_saved_structure_and_falls_back_if_missing(self):
        with patch.dict(sys.modules, runtime_stubs()):
            rewards = load_source_module("src/proteinfoundation/rewards/base_reward.py", "design_test_reward")
        for alias, emit_structure in (("af2folding", True), ("af2folding", False), ("colabdesign", True)):
            with self.subTest(alias=alias, emit_structure=emit_structure), tempfile.TemporaryDirectory() as directory:
                generated = str(Path(directory) / "sample.pdb")
                Path(generated).write_text("REMARK synthetic routing fixture\n")
                calls = []

                def fold_score(pdb_path, **kwargs):
                    calls.append(("fold", pdb_path))
                    if emit_structure and kwargs.get("save_pdb"):
                        Path(kwargs["output_pdb_path"]).write_text("REMARK synthetic refolded fixture\n")
                    return {"total_reward": -0.2}

                def interaction_score(pdb_path, **kwargs):
                    calls.append(("interaction", pdb_path))
                    return {"total_reward": 3.0}

                folding = SimpleNamespace(
                    IS_FOLDING_MODEL=True, SUPPORTS_SAVE_PDB=True, score=fold_score, cleanup=lambda: None
                )
                interaction = SimpleNamespace(
                    IS_FOLDING_MODEL=False, structure_source=alias, score=interaction_score, cleanup=lambda: None
                )
                composite = rewards.CompositeRewardModel({"af2folding": folding, "tmol": interaction})
                result = composite.score(generated)
                expected_path = (
                    generated.replace(".pdb", "_refolded_af2folding.pdb")
                    if alias == "af2folding" and emit_structure
                    else generated
                )
                self.assertEqual(calls, [("fold", generated), ("interaction", expected_path)])
                self.assertAlmostEqual(result["total_reward"], 2.8)

    def test_outcome_oracle_uses_production_thresholds(self):
        with patch.dict(sys.modules, {"loguru": SimpleNamespace(logger=Mock())}):
            from proteinfoundation.result_analysis.binder_analysis_utils import (
                DEFAULT_PROTEIN_BINDER_THRESHOLDS,
                check_redesign_passes_all_thresholds,
                check_sample_has_passing_redesign,
            )

        with (EVALS / "files/outcome_review/evaluation_rows.csv").open() as handle:
            rows = list(csv.DictReader(handle))
        with (EVALS / "files/outcome_review/foldseek_clusters.csv").open() as handle:
            clusters = {row["sequence_id"]: row["cluster_id"] for row in csv.DictReader(handle)}
        self.assertEqual(set(clusters), {row["sequence_id"] for row in rows})
        thresholds = DEFAULT_PROTEIN_BINDER_THRESHOLDS
        for row in rows:
            row["metrics"] = {
                key: float(row[column]) if row[column] else float("nan")
                for key, column in (
                    ("i_pAE", "complex_i_pAE"),
                    ("pLDDT", "complex_pLDDT"),
                    ("scRMSD_ca", "binder_scRMSD_ca"),
                )
            }
            row["passes"] = check_redesign_passes_all_thresholds(row["metrics"], thresholds)

        passed_self = [row for row in rows if row["sequence_type"] == "self" and row["passes"]]
        passed_mpnn = [row for row in rows if row["sequence_type"] == "mpnn" and row["passes"]]
        self_designs = {row["design_id"] for row in passed_self}
        mpnn_designs = {row["design_id"] for row in passed_mpnn}
        self.assertEqual(self_designs, {"D01", "D02"})
        self.assertEqual(
            {row["sequence_id"] for row in passed_mpnn}, {"D01_mpnn_1", "D01_mpnn_2", "D03_mpnn_1", "D05_mpnn_1"}
        )
        self.assertEqual(mpnn_designs, {"D01", "D03", "D05"})
        self.assertEqual(mpnn_designs - self_designs, {"D03", "D05"})
        self.assertEqual(len(self_designs | mpnn_designs), 4)
        self.assertEqual(sum(row["sequence_type"] == "self" for row in rows), 6)
        self.assertEqual(sum(row["sequence_type"] == "mpnn" for row in rows), 12)
        self.assertEqual({clusters[row["sequence_id"]] for row in passed_self}, {"F01"})
        self.assertEqual({clusters[row["sequence_id"]] for row in passed_mpnn}, {"F01", "F02"})

        # D04's redesigns each pass different criteria, but none passes all.
        d04 = [row for row in rows if row["design_id"] == "D04" and row["sequence_type"] == "mpnn"]
        metrics = {key: [row["metrics"][key] for row in d04] for key in thresholds}
        self.assertFalse(check_sample_has_passing_redesign(metrics, thresholds))
        self.assertFalse(next(row["passes"] for row in rows if row["sequence_id"] == "D05_self_0"))
        self.assertFalse(next(row["passes"] for row in rows if row["sequence_id"] == "D03_self_0"))


if __name__ == "__main__":
    unittest.main()
