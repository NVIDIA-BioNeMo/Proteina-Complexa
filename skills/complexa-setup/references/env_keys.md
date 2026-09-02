# `.env` Key Reference

Complete reference for every variable in `.env_example`. Sections mirror the
ones in `.env_example` itself. Each entry says: required vs optional, default,
what reads it, and the failure mode if it is missing or wrong.

`.env` is loaded by `python-dotenv` via `proteinfoundation/cli/validate.py:load_env_config`
and resolved into Hydra configs via `${oc.env:VARIABLE_NAME}` interpolation.
Missing required variables surface as Hydra `InterpolationKeyError` at config
resolution time — intentional, so you see exactly which key is missing.

---

## Section 1 — Required

You must set these before running any pipeline command. `complexa init` does
not fill these in; its first phase only copies `.env_example`.

### `LOCAL_CODE_PATH`

- **Required.** No default — `.env_example` ships with a placeholder.
- Absolute path to this repo checkout on the host.
- Read by: `COMMUNITY_MODELS_PATH`, `AF2_DIR`, `ESM_DIR`, `RF3_DIR`, `RF3_CKPT_PATH`, and `UV_VENV` (all derived via `${LOCAL_CODE_PATH}/...`).
- **Failure mode**: every community-model and tool path resolves below the placeholder checkout and does not exist → `complexa validate evaluate` / Hydra `FileNotFoundError`.
- Fix: edit to an absolute path, e.g. `LOCAL_CODE_PATH=/home/me/code/Proteina-Complexa`.

### `LOCAL_DATA_PATH`

- **Required.** Default placeholder `/path/to/PFM_data`.
- Absolute path to the PFM data directory (target PDBs under `target_data/`, datasets, etc.).
- Read by: the default `DATA_PATH` alias in `.env`; Docker's generated `env.sh` overrides `DATA_PATH` with `DOCKER_DATA_PATH`. `complexa validate env` requires the active value to point at an existing directory.
- **Failure mode**: `complexa validate env` reports `DATA_PATH: Directory not found`; `complexa validate target` fails to locate `target_data/`.
- Fix: edit, then `mkdir -p $LOCAL_DATA_PATH` and populate it with the target PDBs you plan to design against (the bundled examples ship under `assets/target_data/`, or build your own with the `complexa-target` skill).

---

## Section 2 — Credentials (all optional)

### `GITLAB_TOKEN`

- **Optional.** Default placeholder `TOKEN_HERE`.
- Used by `env/docker-ops.sh` to authenticate against a private Docker registry (only relevant if you build the image yourself and push it somewhere that needs a token).
- **Failure mode if missing**: `docker login` is skipped → cannot pull private images. The default Dockerfile build (`docker build -f env/docker/Dockerfile .`) and all NGC downloads still work without it.
- Fix: set if you have your own private registry configured via `REGISTRY` / `DOCKER_IMAGE`.

### `WANDB_API_KEY` / `WANDB_ENTITY`

- **Optional.** Default placeholders `YOUR_WANDB_KEY` / `YOUR_WANDB_ENTITY`.
- Used by training code (`proteinfoundation.train`) for run logging.
- Placeholder values are explicitly *not* injected — W&B logging is silently disabled when either is a placeholder.
- **Failure mode if missing**: no W&B logging; training still runs.
- Fix: set both if you want training runs tracked.

### `HF_TOKEN`

- **Optional.** Default placeholder `HF_TOKEN_HERE`.
- Read by `env/download_startup.sh` (the script behind `complexa download`) when pulling ESM2 / ESMFold from Hugging Face Hub.
- **Failure mode if missing**: ESM2 / ESMFold downloads may hit anonymous rate limits or fail for gated repos. Other downloads (NGC, GitHub) work without it.
- Fix: set if `--esm2` or `--esmfold` downloads fail with 401/429.

---

## Section 3 — Local options (all optional)

### `LOCAL_CACHE_DIR`

- **Optional.** Default `${LOCAL_CODE_PATH}/.cache`.
- Active alias `CACHE_DIR` resolves to this for UV runtime.
- Used for Hydra cache, foldseek temp, HuggingFace hub cache.
- **Failure mode if missing**: defaults work for almost everyone; set only if `.cache` should live on a faster / larger disk.

### `LOCAL_CHECKPOINT_PATH`

- **Optional.** Default in `.env_example`: `${LOCAL_CODE_PATH}/checkpoints`.
- Active alias `CKPT_PATH` resolves to this for UV runtime.
- Note: `complexa download` always writes Complexa model + AE checkpoints to `$PROJECT_ROOT/ckpts/` (a sibling of `checkpoints/`) regardless of this setting. If you want `CKPT_PATH` to point at the download location, set `LOCAL_CHECKPOINT_PATH=${LOCAL_CODE_PATH}/ckpts` after running `complexa download`.
- **Failure mode if missing**: pipeline configs resolve `${oc.env:CKPT_PATH}` to the default — if the directory doesn't exist or is empty, loading the model fails.
- Fix: either run `complexa download --complexa-all` and set `LOCAL_CHECKPOINT_PATH=${LOCAL_CODE_PATH}/ckpts`, or move/symlink the downloaded ckpts into the `checkpoints/` default.

### `DOCKER_MOUNTS`

- **Optional.** Default empty.
- Comma-separated `host:container` pairs added to `env/docker-ops.sh run`.
- **Failure mode if missing**: only standard mounts (`LOCAL_CODE_PATH`, `LOCAL_DATA_PATH`) are exposed to the container.
- Fix: set if you need extra paths visible inside the container — e.g. `DOCKER_MOUNTS=/scratch:/scratch,/lustre:/lustre`.

### `LOGURU_LEVEL`

- **Optional.** Default `INFO`.
- Read by `loguru` for Python log verbosity.
- Set to `DEBUG` for verbose pipeline logs, `WARNING` for quieter runs.

### `USE_V2_COMPLEXA_ARCH`

- **Optional.** Default `False`.
- Set to `True` only when using V2 Complexa model weights. The default-shipped checkpoints are V1.
- **Failure mode if wrong**: loading a V2 ckpt with this `False` (or a V1 ckpt with this `True`) throws a state-dict mismatch at model load time.

---

## Section 4 — Docker image (rarely edited)

These are read by `env/docker-ops.sh build/pull/run`.

### `REGISTRY` / `REGISTRY_USER`

- **Required only for `docker-ops.sh push/pull` against a private registry.** Defaults in `.env_example`: `registry.example.com` / `'$oauthuser'` (placeholders — you must edit if pushing/pulling).
- Used in `docker login` and tagging. Local `docker build` does not need these.

### `DOCKER_IMAGE`

- **Required for `docker-ops.sh run` (Docker runtime).** Default placeholder `registry.example.com/org/repo:tag`.
- Tag of the image `docker-ops.sh run` will start. If you built the image yourself with `docker build -t proteina-complexa -f env/docker/Dockerfile .`, set this to `proteina-complexa:latest`.

### `CONTAINER_NAME`

- **Required for Docker runtime.** Default `proteina-dev`.
- Name assigned to the running container; reused for later `exec` / `stop` operations.

### `DOCKERFILE_PATH`

- **Required for `docker-ops.sh build`.** Default `env/docker/Dockerfile`.
- Path (relative to `LOCAL_CODE_PATH`) of the Dockerfile used by `docker-ops.sh build`.

---

## Runtime activation and derived values

The `.env` template defaults its active aliases to UV values. Running
`complexa init uv` or `complexa init docker` generates `env.sh`; it does not
rewrite `.env`. Source `env.sh` before running Complexa so Docker-specific
overrides and the selected-runtime marker are exported.

### `COMPLEXA_INIT`

- Exported as `uv` or `docker` by the generated `env.sh`; it is not an `.env` key.

### `DATA_PATH` / `CACHE_DIR` / `CKPT_PATH`

- `DATA_PATH` and `CKPT_PATH` default to `${LOCAL_*}` in `.env`; Docker's
  generated `env.sh` overrides them with `${DOCKER_*}`. `CACHE_DIR` may be
  supplied separately by Docker tooling. Edit the local or Docker source
  values rather than the active aliases.

### `FOLDSEEK_EXEC` / `RF3_EXEC_PATH` / `SC_EXEC` / `HBPLUS_EXEC` / `MMSEQS_EXEC` / `DSSP_EXEC` / `TMOL_PATH`

- Active tool binaries default to `${UV_*}` in `.env`; generated `env.sh`
  overrides the supported tool variables with `${DOCKER_*}` for Docker. Edit
  the family variables for a non-standard install.
- Used by: `complexa evaluate` (foldseek for diversity; mmseqs for sequence clustering; hbplus/sc for interface metrics; dssp for secondary structure; tmol for force-field metrics).
- **Failure mode if path is wrong**: the tool is silently skipped (treated as a warning in `complexa validate evaluate`), and the corresponding metric column is missing from the result CSV.

### `AF2_DIR` / `ESM_DIR` / `RF3_DIR` / `RF3_CKPT_PATH`

- **Derived by `.env`, but they must point at real weight directories for evaluation/reward to work.**
- Derived from `${LOCAL_CODE_PATH}/community_models/ckpts/...`. After `complexa download --all` or `complexa download --af2`, the directories under `community_models/ckpts/` are populated.
- Read by: reward models (`AF2RewardModel`, `RF3RewardRunner`) and evaluation folding (colabdesign / rf3 backends).
- **Failure mode if wrong**: `complexa validate evaluate` reports `AF2 weights: Directory not found` or `RF3 checkpoint: File not found`. Generation can still run without these; only reward and refolding break.

### `RF3_CKPT_PATH`

- Default `${RF3_DIR}/rf3_foundry_01_24_latest_remapped.ckpt` — exact filename produced by `complexa download --rf3`. If you have a different RF3 checkpoint, edit to its full path.

### `COMMUNITY_MODELS_PATH`

- Default `${LOCAL_CODE_PATH}/community_models`. Edit only if you mirror community models on a separate disk.

### `UV_VENV` / `UV_*_EXEC` / `DOCKER_*_EXEC`

- Per-runtime tool-path families. Generated `env.sh` selects which family the active `FOLDSEEK_EXEC` etc. use. Edit the *family member* (e.g. `UV_FOLDSEEK_EXEC`) only if your local install lives somewhere unusual.

### `DOCKER_REPO_PATH` / `DOCKER_DATA_PATH` / `DOCKER_PYTHONPATH` / `DOCKER_CHECKPOINT_PATH` / `DOCKER_CACHE_DIR` / `DOCKER_HF_HOME` / `DOCKER_HF_HUB_CACHE`

- Container-internal paths inside the Complexa Docker image. Hard-coded to `/workspace/...`; only edit if you ship a custom image with different layout.

---

## What `complexa validate env` actually checks

From `src/proteinfoundation/cli/validate.py:validate_env`:

1. `.env` file exists in CWD (or any parent up to the repo root).
2. `DATA_PATH` env var is set and resolves to an existing directory.

That is the full check. It does not validate ckpts, tool binaries, or HF
tokens. Those are checked by `complexa validate {generate,evaluate,design}
<config>` which loads a pipeline YAML and verifies the paths each stage will
actually read. Run `complexa validate design configs/search_binder_local_pipeline.yaml`
once after editing `.env` to catch missing AF2/RF3/foldseek before the first
real pipeline run.
