---
name: complexa-setup
description: >
  Agent runbook for first-time Proteina-Complexa setup, dotenv configuration,
  runtime activation, model-weight installation, GPU preflight, and environment
  validation. Use for "set up complexa", "install complexa", "complexa init",
  "complexa download", checkpoint installation or status, UV versus Docker
  selection, and fresh checkouts. SKILL.md invokes the first-party CLI; bundled
  executables safely inspect local readiness and write a private setup manifest.
compatibility: "bash 4+ and Python 3 for local checks; complexa CLI for runtime initialization/downloads; nvidia-smi optional"
allowed-tools: Bash, Read, Write, Env, AskUserQuestion
---


# Complexa Setup Skill

Drive the three steps a fresh Proteina-Complexa checkout needs before any
design run: create `.env`, fetch model weights, and sanity-check the env.
Probe the host for GPU / disk / tool binaries first so the user does not
discover a missing dependency mid-pipeline. End with a JSON setup artifact the
user (or a future agent) can re-read instead of re-deriving state.

## Instructions

Match the requested setup scope. For offline configuration, a checkpoint audit,
or a future-host plan, inspect the supplied files and prepare only the requested
artifacts. Do not build the ML environment or download weights just to edit a
dotenv. For those limited tasks, record unavailable prerequisites and future
commands without attempting full installation. For an installation request,
follow the runtime build and download steps below, and report concrete failures
instead of repeatedly restarting provisioning. Configuration-only completion
does not establish runtime or GPU readiness. Keep commands actually executed
separate from commands planned for later; do not record an unexecuted download
as completed in the manifest.

Set `SETUP_SKILL_DIR` to this skill's absolute installation directory, using
the location supplied by the skill loader. The bundled helpers are
[preflight.sh](scripts/preflight.sh) and
[write_manifest.py](scripts/write_manifest.py). Run them with the
Proteina-Complexa project root as the working directory so they inspect the
intended `.env`.

## CLI vs direct file-edit — pick the cheapest path per step

| Step | Preferred path | Why |
|---|---|---|
| `.env` creation (Step 2) | **CLI** (`complexa init`) | Phase 1 copies `.env_example` to `.env`; it does not select a runtime. |
| `.env` value edits (Step 3) | **File edit** (StrReplace `LOCAL_CODE_PATH=…` etc.) | No CLI for this — the values are user-specific paths. |
| Runtime activation (end of Step 3) | **CLI** (`complexa init uv` or `complexa init docker`), then `source env.sh` | Phase 2 generates `env.sh`, which loads `.env` and selects runtime-specific paths. |
| Download model weights (Step 4) | **CLI** (`complexa download --…`) | Dispatches to `env/download_startup.sh` (~1000 lines of bash with NGC URLs, retries, checksum-style skip-if-present). Don't try to replicate. |
| Validate env (Step 5) | **CLI** (`complexa validate env`) or `test -f .env && test -d $DATA_PATH` | CLI prints a nicer report; the manual check is one-liner-safe. |
| Validate full design config (after picking a pipeline) | **CLI** (`complexa validate design CONFIG`) | Non-trivial Hydra defaults traversal + ckpt + env-var checks; not worth replicating. |

## What this skill enables

- A correctly-shaped `.env` for either UV or Docker runtime.
- Model checkpoints (Complexa protein/ligand/AME plus community models) downloaded to known paths.
- A `preflight.json` snapshot of the host (GPU, disk, .env, ckpts, tool binaries).
- A `run_manifest.json` capturing exactly which `complexa init` + `complexa download` invocations were used (replay-friendly).
- A pass/fail report from `complexa validate env` with clear next-step hints.

## Step 1: Pre-flight check

Run the shared preflight before configuring or installing on the current host.
It does not require `.env` to exist and records local readiness observations.
For an exported inventory audit or future-host configuration, use the supplied
evidence and distinguish it from checks actually performed on the current host.

```bash
bash "$SETUP_SKILL_DIR/scripts/preflight.sh"
```

The script writes `./complexa_setup/preflight.json`. Read it and surface:

- `gpu.available` — if `false`, design / evaluate steps will fail; warn the user.
- `gpu.vram_gb` — Complexa needs ≥40 GB (A100/H100/L40S).
- `disk.free_gb` at `CKPT_PATH` — minimum ~50 GB for the full Complexa + community model set.
- `env.missing_required` — anything listed here must be edited in `.env` before validation passes.
- `tools.{foldseek,mmseqs,dssp,hbplus,sc}.exists` — missing tools degrade evaluation but do not block generation.

## Step 1b: Build the Python environment (when installation is requested)

The `complexa` CLI is installed inside the project's Python environment, not on
the system path by default. On a **fresh clone**, the `.venv/` directory does
not yet exist and `complexa init` will fail with `command not found`. Build the
UV venv when an actual UV installation is requested and its prerequisites are
available. Offline configuration and audit tasks skip this step:

```bash
test -d .venv || ./env/build_uv_env.sh   # first-time UV build
source .venv/bin/activate
which complexa                            # sanity check: should point inside .venv
```

Skip this step if `which complexa` already resolves — that means a previous
build is still good. The Docker runtime skips it entirely; the venv lives
inside the container image instead. If the user said "I just cloned" or you
see no `.venv/` next to `pyproject.toml` during an installation task, run the build script — `complexa init`
without a venv produces a confusing `command not found` rather than an obvious
"build the venv first" error.

## Step 2: Create `.env`

Pick the runtime. UV is the default and faster to start; Docker is required on
Ubuntu 20.04 or systems with GLIBC mismatches.

Use AskUserQuestion if it is not obvious from context:

> "Which runtime do you want to configure? `uv` (recommended, faster) or `docker` (use if you do not have a UV venv built locally)?"

### Preferred: CLI

```bash
test -f .env || complexa init    # Phase 1: copy .env_example to .env
```

If the CLI is not yet available but the checkout is trusted, `cp .env_example
.env` is equivalent to phase 1 only. Runtime selection happens later through
`env.sh`; do not rewrite the active path expressions in `.env`.

`complexa init --force` replaces the entire existing dotenv, including custom
paths and credentials. Use it only when the user has explicitly requested a
reset; otherwise preserve the existing file and edit the required values.
Before an authorized reset, save a private backup with a unique filename and
report its path without printing its contents:

```bash
complexa init --force            # Recreate .env from .env_example (drops any edits)
```

### Verify either way

```bash
test -f .env && echo "OK: .env present" || echo "MISSING"
```

## Step 3: Edit .env

No CLI for this — Step 2 only created `.env`; you still need to write your
machine-specific paths into `.env` by hand (StrReplace or your editor). The two
absolutely-required edits are:

```bash
LOCAL_CODE_PATH=/absolute/path/to/Proteina-Complexa
LOCAL_DATA_PATH=/absolute/path/to/PFM_data
```

The template defaults `LOCAL_CHECKPOINT_PATH` to `${LOCAL_CODE_PATH}/checkpoints`,
but the downloader writes Complexa weights to `ckpts/`. For that layout, set
`LOCAL_CHECKPOINT_PATH=${LOCAL_CODE_PATH}/ckpts` and retain the derived
`CKPT_PATH=${LOCAL_CHECKPOINT_PATH}` alias. For a future Docker run, also align
`DOCKER_CHECKPOINT_PATH` with the checkpoint directory inside that container.

Everything else (cache, ckpts, community-model dirs, tool binaries) is derived
from `LOCAL_CODE_PATH` by default and only needs editing if you have a
non-standard layout. For the full table — every key, what it controls, what
fails if it is missing — see [references/env_keys.md](references/env_keys.md).

Quick decision table for the four edits most users make:

| Key | Default | Set this if |
|-----|---------|-------------|
| `LOCAL_CODE_PATH` | placeholder | Always — required |
| `LOCAL_DATA_PATH` | `/path/to/PFM_data` | Always — required, points at target PDBs |
| `HF_TOKEN` | placeholder | You need ESMFold or gated HF models |
| `WANDB_API_KEY` | placeholder | You want training runs logged to W&B |

After editing the paths, generate and activate the runtime environment. The
runtime is a positional argument:

```bash
complexa init uv                 # or: complexa init docker
source env.sh
```

`env.sh` sources the edited `.env`, maps the active tool/data/checkpoint paths
for the selected runtime, and exports `COMPLEXA_INIT=uv` or `docker`.

## Step 4: Download checkpoints

Use the first-party downloader. `complexa download` dispatches to
`env/download_startup.sh` (~1000 lines of bash with NGC URLs, retries, and
skip-if-present logic across ~6 community-model families). Rolling your own
wget loop is a recipe for partial downloads and wrong destination paths.

The CLI parser accepts the aggregate flags below. For just AF2 or ProteinMPNN,
use `bash env/download_startup.sh --af2` or `--pmpnn` from the trusted checkout;
these per-model flags are supported by the script, not the CLI parser. Inspect
the existing inventory before choosing a download. `--status` checks presence,
so an empty or unverified file is not evidence of usable weights.

Ask which models the user actually needs — downloading everything is ~100+ GB.
Pick from the three Complexa variants and the community-model set. Each
Complexa variant unlocks exactly one `complexa design` pipeline; AF2 / RF3
inside the community-model set are what `evaluate` (and reward-guided search)
need at run time.

| Flag | What it downloads | Unlocks pipeline | Destination | Approx size |
|------|-------------------|------------------|-------------|-------------|
| `--complexa` | Complexa protein-binder model + AE (`complexa.ckpt`, `complexa_ae.ckpt`) | **Protein binder** (default) — `configs/search_binder_local_pipeline.yaml` | `./ckpts/` | ~3 GB |
| `--complexa-ligand` | Ligand-binder model + AE (`complexa_ligand.ckpt`, `complexa_ligand_ae.ckpt`) | Ligand binder — `configs/search_ligand_binder_local_pipeline.yaml` | `./ckpts/` | ~3 GB |
| `--complexa-ame` | AME motif-scaffolding model + AE (`complexa_ame.ckpt`, `complexa_ame_ae.ckpt`) | AME (enzyme) — `configs/search_ame_local_pipeline.yaml` | `./ckpts/` | ~3 GB |
| `--complexa-all` | All three Complexa variants | All three pipelines | `./ckpts/` | ~9 GB |
| `--all` | ProteinMPNN + LigandMPNN + AF2 + ESM2 + RF3 | Needed by **evaluate / reward**: AF2 (protein binder), RF3 (ligand binder + AME), MPNNs (inverse folding). | `./community_models/` | ~50 GB |
| `--everything` | All three Complexa variants plus the `--all` community set | All bundled pipelines; does not provision additional refold backends | both | Allow additional disk headroom |
| `--status` | Show install state — does not download | (none) | (none) | n/a |

**Convenient complete bundles per pipeline** (use targeted script flags for
already-partially-installed community models):

- Protein binder (default): `complexa download --complexa --all`
- Ligand binder: `complexa download --complexa-ligand --all`
- AME / enzyme: `complexa download --complexa-ame --all`
- All three: `complexa download --everything`

For the full per-model destination breakdown and per-flag NGC sources, see
[references/downloads.md](references/downloads.md).

Pick the smallest invocation that covers the user's goal, then run:

```bash
complexa download --complexa            # protein binder only
complexa download --complexa-all        # all three Complexa variants
complexa download --all                 # community models only
complexa download --everything          # everything
```

Without arguments, `complexa download` launches an interactive wizard — prefer
explicit flags in agent mode.

Verify what landed:

```bash
complexa download --status
```

The status output groups by family (Complexa / community / optional) and prints
"Installed" or "Missing" per ckpt. Re-run the specific flag if a ckpt is
flagged missing.

## Step 5: Validate

Final check that `.env` is loadable and the required paths resolve:

```bash
complexa validate env
```

`validate env` checks: (1) `.env` exists, (2) `DATA_PATH` is set and points at
an existing directory. It does not check ckpt files — those are checked by
`complexa validate design <config>` once you have a pipeline config picked.

Common failures and fixes:

| Symptom | Cause | Fix |
|---------|-------|-----|
| `.env file: No .env file found` | `complexa init` not run | Run `complexa init` first |
| `DATA_PATH: Not set in .env` | Placeholder not edited | Edit `LOCAL_DATA_PATH` in `.env` |
| `DATA_PATH: Directory not found` | Path edited but does not exist on disk | `mkdir -p $LOCAL_DATA_PATH` or copy target data there |
| Hydra error `InterpolationKeyError: AF2_DIR` | Reward/eval config wants AF2 but `.env` does not define it | Download AF2 weights or remove AF2 from the config |

## Step 6: Emit setup artifact

Drop a JSON manifest in `./complexa_setup/` so the user has a single file
describing the resulting state. The shared helper writes it for you:

```bash
mkdir -p ./complexa_setup
python3 "$SETUP_SKILL_DIR/scripts/write_manifest.py" \
    --output-dir ./complexa_setup \
    --command "complexa init ${COMPLEXA_INIT}; complexa download <selected flags>; complexa validate env" \
    --skill complexa-setup \
    --out ./complexa_setup/run_manifest.json
```

Surface the resulting files to the user:

```bash
ls -la ./complexa_setup/
```

Expected contents:

```
complexa_setup/
├── preflight.json      # GPU / disk / .env / ckpt / tool snapshot
└── run_manifest.json   # init + download invocations + git SHA + runtime
```

## Hardware requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| GPU | 1× CUDA GPU, ≥24 GB VRAM | A100 / H100 / L40S, 40–80 GB VRAM |
| CUDA | 12.0 | 12.4+ |
| Disk (CKPT_PATH) | 50 GB | 150 GB (covers `--everything`) |
| RAM | 16 GB | 64 GB+ |
| OS | Ubuntu 22.04+ (UV) | Ubuntu 22.04+ or Docker on any host |

Ubuntu 20.04 throws GLIBC errors with the UV runtime — use `complexa init
docker` on those hosts. See `references/hardware.md`
for per-pipeline (binder vs ligand vs AME) requirements.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `complexa: command not found` | Package not installed in active env | `source .venv/bin/activate` then `pip install -e .` |
| `complexa init` says `.env_example not found` | Running outside repo root | `cd` to the project root (where `.env_example` lives) |
| `.env_example not found. Cannot initialize .env.` | Not in project root | `cd` into `Proteina-Complexa/` and retry |
| `complexa download` fails on NGC URL | Behind firewall / no internet | Configure a proxy for the download script, or download the model `.ckpt`s manually from the NGC pages linked in the main `README.md` and drop them into `./ckpts/` |
| `complexa download --status` shows ckpts present but `validate` fails | `.env` `CKPT_PATH` points elsewhere | Either move ckpts or edit `LOCAL_CHECKPOINT_PATH` in `.env` |
| GLIBC error on import | Ubuntu 20.04 with UV runtime | Run `complexa init docker`, source `env.sh`, and use `./env/docker-ops.sh run` |

---

For the full `.env` reference (every key, defaults, failure modes), see
[references/env_keys.md](references/env_keys.md).

For the full download flag matrix, NGC URLs, and destination layout, see
[references/downloads.md](references/downloads.md).
