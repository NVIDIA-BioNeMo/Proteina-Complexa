# Proteina-Complexa Skills

Five project-local Claude Code skills covering setup, target configuration, design, evaluation, and sweeps. Each skill picks the cheapest tool for its job — the `complexa` CLI where it adds real value (pipeline orchestration, weight downloads, Hydra-defaults validation), and direct file edits / Python module calls where the CLI would just be a thin wrapper.

## The three design pipelines

Complexa runs one of three pipelines. **Protein binder is the default**; the other two are extensions for ligand pockets and enzyme scaffolding. Pick the pipeline by picking the `configs/search_*_pipeline.yaml` file — each one pins its own model checkpoint, autoencoder, targets dict, reward, and refold backend, so switching pipelines is "swap the config + change the target name".

| Pipeline (intent) | Config YAML | Model ckpt | Targets dict | Task-name pattern | Download flag |
|---|---|---|---|---|---|
| **Protein binder (default)** | `configs/search_binder_local_pipeline.yaml` | `complexa.ckpt` + `complexa_ae.ckpt` | `configs/targets/targets_dict.yaml` | `02_PDL1`, `22_DerF21`, … | `--complexa --all` |
| Ligand binder (small-molecule pocket) | `configs/search_ligand_binder_local_pipeline.yaml` | `complexa_ligand.ckpt` + `complexa_ligand_ae.ckpt` | `configs/targets/ligand_targets_dict.yaml` | `39_7V11_LIGAND`, `41_7BKC_LIGAND`, … | `--complexa-ligand --all` |
| AME (motif + ligand, enzyme scaffolding) | `configs/search_ame_local_pipeline.yaml` | `complexa_ame.ckpt` + `complexa_ame_ae.ckpt` | `configs/design_tasks/ame_dict_v2.yaml` | `M0024_1nzy`, `M0096_1chm`, … | `--complexa-ame --all` |

**If the user doesn't specify a pipeline, default to protein binder.** Switch to one of the others only when the request explicitly names a ligand pocket / SMILES / enzyme / `M####_<pdb>` task. See [`complexa-design/SKILL.md`](./complexa-design/SKILL.md) Step 2 for the full "what changes when you switch pipeline" cheat sheet and [`complexa-design/references/pipelines.md`](./complexa-design/references/pipelines.md) for the deep dive (reward weights, success thresholds, LoRA, `USE_V2_COMPLEXA_ARCH`).

## Skills

Each skill picks the cheapest tool for the job — sometimes the `complexa` CLI,
sometimes a direct file edit or Python module call. The "primary tool" column
is the default the skill recommends; the alternatives are still documented
inside each `SKILL.md` for cases where they fit better.

| Skill | Primary tool | CLI / alternative paths | When to use it |
|---|---|---|---|
| [`complexa-setup`](./complexa-setup/) | **File-edit** for `.env` + **CLI** (`complexa download`) for weights | `complexa init` is a `cp+sed` wrapper, fine either way; `complexa validate env` and `validate design` are the recommended CLI checks | Fresh checkout, verifying an existing install, configuring `.env` |
| [`complexa-target`](./complexa-target/) | **File-edit** of `configs/targets/{,ligand_}targets_dict.yaml` | `complexa target add/list/show` (CLI is a thin YAML-append wrapper); `complexa validate target` still has unique value (Hydra defaults traversal) | Registering a new protein or ligand design target |
| [`complexa-design`](./complexa-design/) | **CLI** (`complexa design <pipeline>` orchestrates 4 stages with logging) | Direct `python -m proteinfoundation.{generate,filter,evaluate,analyze}` for single-stage debug | Protein binder, ligand binder, AME motif scaffolding |
| [`complexa-evaluate-pdbs`](./complexa-evaluate-pdbs/) | **CLI** (`complexa analysis <eval_cfg>` chains evaluate→analyze) | Direct `python -m proteinfoundation.{evaluate,analyze}` for debugging | Re-folding / scoring an existing PDB directory with AF2 / RF3 / ESMFold |
| [`complexa-sweep`](./complexa-sweep/) | **Python script** (`script_utils/generate_inference_configs.py`) + a `complexa design` loop | No CLI — `complexa design` does not accept `--sweeper`; generate configs first, then loop | Finding optimal beam_width, nsteps, reward weights, etc. |

## Shared infrastructure and references

| File | Purpose |
|---|---|
| [`_shared/scripts/preflight.sh`](./_shared/scripts/preflight.sh) | One-shot system probe (GPU, VRAM, disk, checkpoints, tools, `.env`). Outputs `preflight.json`. |
| [`_shared/scripts/write_manifest.py`](./_shared/scripts/write_manifest.py) | Emits a pinned, replayable `run_manifest.json` per pipeline run. |
| [`_shared/references/hardware.md`](./_shared/references/hardware.md) | Per-pipeline hardware requirements. |
| [`_shared/references/INFERENCE.md`](./_shared/references/INFERENCE.md) | Canonical inference and search guide. |
| [`_shared/references/CONFIGURATION_GUIDE.md`](./_shared/references/CONFIGURATION_GUIDE.md) | Canonical pipeline configuration guide. |
| [`_shared/references/EVALUATION_METRICS.md`](./_shared/references/EVALUATION_METRICS.md) | Canonical evaluation and analysis guide. |
| [`_shared/references/SEARCH_METADATA.md`](./_shared/references/SEARCH_METADATA.md) | Canonical search-metadata guide. |
| [`_shared/references/SWEEP.md`](./_shared/references/SWEEP.md) | Canonical parameter-sweep guide. |

The explicit ownership map in [`_shared/sync_shared.py`](./_shared/sync_shared.py)
copies each asset as a real file only into the independently distributed skills
that need it. Because the five canonical guides cross-link one another, the map
copies the complete guide set into `complexa-design`,
`complexa-evaluate-pdbs`, and `complexa-sweep`; `complexa-setup` and
`complexa-target` receive none of those guides. The traditional top-level
`docs/*.md` guide paths are symlinks to the canonical files.

The skills require `complexa` (this repo's CLI), `bash`, and optionally `nvidia-smi`.

## Adding a new skill

These skills were authored with Anthropic's [`skill-creator`](https://github.com/anthropics/skills/tree/main/skill-creator) workflow:

1. **Draft** — `SKILL.md` (≤300 lines) + progressive-disclosure `references/*.md`. Anchor authoring to specific source files (`cli_runner.py`, `target_cli.py`, `configs/**`).
2. **Test prompts** — a handful of realistic agent prompts per skill.
3. **Parallel eval** — for each prompt, run a with-skill agent vs a baseline; grade against objective assertions (uses correct flag? cites real override key? runs preflight?).
4. **Iterate** on regressions.

The flagship reference is [`complexa-design`](./complexa-design/) — its SKILL.md anchors on a real scientific task (full pipeline → success rate + diversity) and shows the progressive-disclosure pattern at its widest (3 reference files).
