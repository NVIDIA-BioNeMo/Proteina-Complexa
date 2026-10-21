"""Check source fidelity and real CLI behavior without installing the ML stack."""

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

EVALS = Path(__file__).resolve().parents[1]
ROOT = EVALS.parents[2]
PROJECT = EVALS / "files/project"
CLI = ROOT / "src/proteinfoundation/cli/cli_runner.py"


class SetupFixtureTests(unittest.TestCase):
    def test_source_snapshots_and_original_dataset_are_unchanged(self):
        manifest = json.loads((PROJECT / "source_manifest.json").read_text())
        original = (EVALS / "full-installation.json").read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(), manifest["full_installation_sha256"])
        for filename, record in manifest["files"].items():
            with self.subTest(filename=filename):
                source = (ROOT / record["source"]).read_bytes()
                self.assertEqual(hashlib.sha256(source).hexdigest(), record["source_sha256"])
                lines = source.splitlines(keepends=True)
                excerpt = b"".join(lines[record["start_line"] - 1 : record["end_line"]])
                self.assertEqual((PROJECT / filename).read_bytes(), excerpt)
                self.assertEqual(hashlib.sha256(excerpt).hexdigest(), record["sha256"])

    def test_template_supports_both_real_initialization_paths(self):
        for runtime in ("uv", "docker"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as directory:
                work = Path(directory)
                (work / ".env_example").write_bytes((PROJECT / ".env_example").read_bytes())
                subprocess.run(
                    [sys.executable, str(CLI), "init"],
                    cwd=work,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                self.assertTrue((work / ".env").is_file())
                self.assertFalse((work / "env.sh").exists())
                values = {
                    "LOCAL_CODE_PATH": str(work),
                    "LOCAL_DATA_PATH": str(work / "data"),
                    "LOCAL_CHECKPOINT_PATH": "${LOCAL_CODE_PATH}/ckpts",
                    "DOCKER_CHECKPOINT_PATH": "/workspace/Proteina-Complexa/ckpts",
                }
                dotenv = (work / ".env").read_text()
                for key, value in values.items():
                    dotenv = re.sub(rf"^{key}=.*$", f"{key}={value}", dotenv, flags=re.MULTILINE)
                (work / ".env").write_text(dotenv)
                subprocess.run(
                    [sys.executable, str(CLI), "init", runtime],
                    cwd=work,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                self.assertEqual((work / ".env").read_text(), dotenv)
                result = subprocess.run(
                    [
                        "bash",
                        "-c",
                        'source "$1" >/dev/null; printf "%s\\n" "$COMPLEXA_INIT" "$CKPT_PATH" "$DATA_PATH"',
                        "setup-test",
                        str(work / "env.sh"),
                    ],
                    cwd=work,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                expected = [runtime, str(work / "ckpts"), str(work / "data")]
                if runtime == "docker":
                    expected = [runtime, "/workspace/Proteina-Complexa/ckpts", "/workspace/data/PFM_data"]
                self.assertEqual(result.stdout.splitlines(), expected)

    def test_cli_rejects_script_only_download_flags_before_execution(self):
        for flag in ("--af2", "--pmpnn"):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as directory:
                result = subprocess.run(
                    [sys.executable, str(CLI), "download", flag],
                    cwd=directory,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn("unrecognized arguments", result.stderr)
                self.assertEqual(list(Path(directory).iterdir()), [])

    def test_inventory_matches_first_party_model_file_requirements(self):
        inventory = json.loads((EVALS / "files/inventory/checkpoint_inventory.json").read_text())
        self.assertTrue(inventory["synthetic"])
        sizes = {item["path"]: item["size_bytes"] for item in inventory["files"]}
        self.assertEqual(len(sizes), len(inventory["files"]))
        required = re.findall(
            r'^        "([^"\n]+\.npz)"', (PROJECT / "af2_status_source.sh.txt").read_text(), re.MULTILINE
        )
        prefix = "community_models/ckpts/AF2/"
        missing = {name for name in required if prefix + name not in sizes}
        empty = {name for name in required if sizes.get(prefix + name) == 0}
        self.assertEqual(missing, {"params_model_3_multimer_v3.npz"})
        self.assertEqual(empty, {"params_model_5_ptm.npz"})
        for family, names in (
            ("ca_model_weights", ("v_48_002", "v_48_010", "v_48_020")),
            ("vanilla_model_weights", ("v_48_002", "v_48_010", "v_48_020", "v_48_030")),
        ):
            for name in names:
                self.assertGreater(sizes[f"community_models/ProteinMPNN/{family}/{name}.pt"], 0)


if __name__ == "__main__":
    unittest.main()
