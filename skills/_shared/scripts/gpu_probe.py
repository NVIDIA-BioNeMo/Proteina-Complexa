#!/usr/bin/env python3
"""Bounded Linux task-GPU probe. No ML imports, host /proc probes or provisioning.

`accessible` means NVIDIA management access, not validated CUDA inference.
The pure classifier is separate so allocation/failure cases can be tested on CPU.

Usage:
    python3 gpu_probe.py
Arguments:
    None. Reads only the allocation variables named in ENV_KEYS.
Output:
    JSON on stdout with status, allocation, reason, and bounded probe evidence.
Exit codes:
    0 when evidence is collected (including absent/blocked/unknown GPU status).
    Unexpected Python errors exit with 1; GPU readiness is reported in JSON.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ENV_KEYS = (
    "SLURM_JOB_GPUS",
    "SLURM_STEP_GPUS",
    "SLURM_GPUS_ON_NODE",
    "CUDA_VISIBLE_DEVICES",
    "NVIDIA_VISIBLE_DEVICES",
)
DISABLED = {"", "-1", "none", "void", "nodevfiles"}
PROBE_TIMEOUT_SECONDS = 8
MAX_STDOUT_CHARS = 8192
MAX_STDERR_CHARS = 2048
NVIDIA_QUERY_COLUMNS = 3
MIB_PER_GIB = 1024


def classify(evidence: dict) -> dict:
    """Combine device exposure, allocation hints and the bounded NVIDIA query."""
    env = evidence["allocation_env"]
    devices = evidence["device_nodes"]
    probe = evidence["nvidia_smi"]
    explicit = any(
        v.lower() not in DISABLED | {"all"} for k, v in env.items() if k in {"SLURM_JOB_GPUS", "SLURM_STEP_GPUS"}
    ) or (env.get("SLURM_GPUS_ON_NODE", "0").isdigit() and int(env.get("SLURM_GPUS_ON_NODE", "0")) > 0)
    visibility_hint = any(
        env[k].lower() not in DISABLED for k in ("CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES") if k in env
    )
    hidden = any(env[k].lower() in DISABLED for k in ("CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES") if k in env)
    gpus = []
    if probe["status"] == "ok":
        try:
            for row in csv.reader(io.StringIO(probe["stdout"])):
                if len(row) != NVIDIA_QUERY_COLUMNS:
                    raise ValueError("unexpected NVIDIA query columns")
                gpus.append(
                    {
                        "name": row[0].strip(),
                        "vram_gb": int(float(row[1].strip()) // MIB_PER_GIB),
                        "driver": row[2].strip(),
                    }
                )
        except (ValueError, OverflowError):
            gpus = []
            probe = dict(probe, status="invalid_output")
            evidence = dict(evidence, nvidia_smi=probe)

    allocated = bool(devices or explicit)
    if evidence["device_scan_error"]:
        status, allocation, reason = (
            ("blocked", "allocated", "An allocated GPU could not be inspected.")
            if explicit
            else ("unknown", "unknown", "Device exposure could not be inspected.")
        )
    elif allocated and hidden:
        status, allocation, reason = (
            "blocked",
            "allocated",
            "GPU exposure/allocation exists, but a visibility setting disables access.",
        )
    elif allocated and gpus:
        status, allocation, reason = (
            "accessible",
            "allocated",
            "Task GPU exposure/allocation and the NVIDIA query agree; CUDA execution is untested.",
        )
    elif allocated:
        status, allocation, reason = (
            "blocked",
            "allocated",
            "Task GPU exposure/allocation exists, but the NVIDIA query did not establish access.",
        )
    elif gpus or visibility_hint:
        status, allocation, reason = (
            "unknown",
            "unknown",
            "NVIDIA visibility suggests GPUs, but task device/allocation evidence is missing.",
        )
    elif probe["status"] == "missing" or (probe["status"] == "ok" and not probe["stdout"].strip()):
        status, allocation, reason = (
            "absent",
            "absent",
            "No exposed GPU devices, no positive allocation hints, and no GPUs reported by the local NVIDIA probe.",
        )
    else:
        status, allocation, reason = (
            "unknown",
            "unknown",
            "NVIDIA probe failed without sufficient task allocation evidence; failure alone is not GPU absence.",
        )
    result = {
        "available": status == "accessible",
        "status": status,
        "allocation": allocation,
        "reason": reason,
        "evidence": evidence,
    }
    if gpus:
        result.update(gpus[0], count=len(gpus), cuda="unknown", devices=gpus)
    return result


def collect(timeout: float = PROBE_TIMEOUT_SECONDS) -> dict:
    try:
        devices = sorted(str(p) for p in Path("/dev").iterdir() if re.fullmatch(r"nvidia\d+|dxg", p.name))
        scan_error = None
    except OSError as exc:
        devices, scan_error = [], type(exc).__name__
    binary = shutil.which("nvidia-smi")
    command = [binary or "nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"]
    probe = {
        "command": command,
        "status": "missing",
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "timeout_seconds": timeout,
    }
    if binary:
        try:
            # Fixed query arguments to the installed NVIDIA utility; no shell input.
            proc = subprocess.run(command, shell=False, capture_output=True, text=True, timeout=timeout, check=False)
            probe.update(
                status="ok" if proc.returncode == 0 else "error",
                returncode=proc.returncode,
                stdout=proc.stdout[:MAX_STDOUT_CHARS],
                stderr=proc.stderr[:MAX_STDERR_CHARS],
            )
        except subprocess.TimeoutExpired:
            probe.update(status="timeout", stderr="NVIDIA query exceeded the time limit.")
        except OSError as exc:
            probe.update(status="error", stderr=type(exc).__name__)
    return classify(
        {
            "device_nodes": devices,
            "device_scan_error": scan_error,
            "allocation_env": {k: os.environ[k] for k in ENV_KEYS if k in os.environ},
            "nvidia_smi": probe,
        }
    )


if __name__ == "__main__":
    print(json.dumps(collect(), indent=2))
