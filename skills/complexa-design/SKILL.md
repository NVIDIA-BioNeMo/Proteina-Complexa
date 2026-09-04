---
name: complexa-design
description: >
  Agent runbook for orchestrating an end-to-end protein, ligand-binder, or AME
  design through the separately installed first-party Proteina-Complexa CLI.
  Use for requests such as "design a binder", "run complexa design", "de novo
  binder", ligand binding, motif scaffolding, beam search, FK steering, MCTS,
  refolding, or reporting design success and diversity. SKILL.md selects and
  invokes the project CLI; bundled executables only inspect local readiness and
  write a run manifest, and do not implement model inference themselves.
compatibility: "complexa CLI installed (pip install -e .); environment file populated; 1x CUDA GPU >=40GB VRAM (A100/H100/L40S); 24 CPUs; ~50GB disk"
allowed-tools: Bash, Read, Write, Env, AskUserQuestion
---

# Complexa Design Skill

Drive the full four-stage `complexa design` pipeline: generate (flow matching +
search) -> filter (top-N by reward) -> evaluate (refold with AF2/RF3) ->
analyze (success rate, FoldSeek/MMseqs diversity). Pick the right pipeline
config for the design intent, validate the run upfront so the user does not
discover a missing ckpt mid-folding, run it, and emit a replayable manifest +
per-design success CSV.

## What this skill enables

- Protein binder design for protein targets (AF2 reward + ColabDesign refold).
- Ligand binder design for small-molecule targets (RF3 reward + RF3 refold).
- AME motif scaffolding with ligand context (motif + ligand features, RF3).
- Search-based optimization: single-pass, best-of-n, beam-search, fk-steering, mcts.
- Refold backends: ColabDesign (AF2), RF3, Boltz2, ESMFold (fast iteration).
- Pass-rate + diversity analysis with per-`result_type` thresholds.

## Step 1: Pre-flight

Always run the shared preflight before launching a design — generation needs the
GPU and the right checkpoint, evaluation needs AF2/RF3 weights and tool
binaries. Bail early if the host cannot run the chosen pipeline.

```bash
bash scripts/preflight.sh
```

Read `./complexa_setup/preflight.json` and bail if any of these are missing for
the chosen pipeline:

- `gpu.available: false` -> all pipelines fail.
- `gpu.vram_gb < 40` -> generation OOMs at default `batch_size: 16`; lower to 8.
- `ckpts.complexa[.ckpt]` -> required for protein binder.
- `ckpts.complexa_ligand[.ckpt]` -> required for ligand binder.
- `ckpts.complexa_ame[.ckpt]` -> required for AME.
- `env.AF2_DIR` missing -> protein binder default eval (`colabdesign`) fails.
- `env.RF3_CKPT_PATH` or `env.RF3_EXEC_PATH` missing -> ligand binder / AME default eval (`rf3_latest`) fails.

If a ckpt is missing, point at `complexa-setup` and have the user run
`complexa download --complexa-<variant>` first.

## Step 2: Pick the pipeline

Select the pipeline YAML that matches the requested target. Each YAML pins the
corresponding checkpoint, target dictionary, reward, and refold backend.

| Request | Pipeline YAML | Target pattern | Default refold |
|---|---|---|---|
| Protein-surface binder (default) | `search_binder_local_pipeline.yaml` | `02_PDL1` | `colabdesign` |
| Small-molecule pocket / ligand binder | `search_ligand_binder_local_pipeline.yaml` | `39_7V11_LIGAND` | `rf3_latest` |
| AME enzyme or motif-plus-ligand scaffold | `search_ame_local_pipeline.yaml` | `M0096_1chm` | `rf3_latest` |

Protein binder is the default when the user does not identify a ligand or
motif. Do not remove the `lora:` block in ligand or AME pipeline YAMLs; those
released checkpoints require it. AME defaults to `single-pass`; enable a
reward model before selecting a reward-guided search algorithm. See
[references/pipelines.md](references/pipelines.md) for checkpoints, target
dictionaries, thresholds, and the full pipeline matrix.

## Step 3: Gather parameters

Use AskUserQuestion to fill in the four parameters that vary every run. Default
to sensible production settings if the user has no preference.

- **Target name** — must be a key in the relevant dict (`targets_dict.yaml` for
  protein binder, `ligand_targets_dict.yaml` for ligand, `ame_dict_v2.yaml` for
  AME). If the user names a target that is not in the dict, hand off to
  `complexa-target` to add it first.
- **Run name** — a short identifier appended to the output dir (e.g. `pdl1_v1`).
- **Search algorithm** — default to `beam-search` with `beam_width=8` and
  `n_branch=4` for production. Use `single-pass` for a quick smoke test.
- **Evaluation refold backend** — protein binder defaults to `colabdesign`
  (AF2); ligand/AME default to `rf3_latest`. Use `esmfold` for fast iteration
  (worse but seconds per sample).

## Step 4: Validate

Validate before running. This is cheap (seconds) and catches missing ckpts,
missing env vars, unknown override keys, and missing target entries — all of
which would otherwise abort the pipeline mid-evaluation after hours of
generation.

```bash
complexa validate design configs/search_binder_local_pipeline.yaml \
    ++generation.task_name=02_PDL1 \
    ++metric.binder_folding_method=colabdesign
```

The validator returns non-zero on failure and prints a pass/fail report.
Re-run the command with the suggested overrides until it returns clean.

## Step 5: Run the pipeline

`complexa design` is the right tool for the full 4-stage run — it orchestrates
`generate → filter → evaluate → analyze` as sequential subprocesses with a
shared run name, log dir, and multi-GPU split (see `run_design_pipeline` in
`src/proteinfoundation/cli/cli_runner.py`). Re-implementing that manually
loses the per-stage log routing and progress prints.

Use `++` (forced) Hydra overrides; they apply to all stages. The minimal
production protein-binder invocation:

```bash
complexa design configs/search_binder_local_pipeline.yaml \
    ++run_name=pdl1_v1 \
    ++generation.task_name=02_PDL1 \
    ++generation.search.algorithm=beam-search \
    ++generation.search.beam_search.beam_width=8 \
    ++metric.binder_folding_method=colabdesign
```

For ligand binder / AME, use the matching pipeline YAML and target name from
the Step 2 table; every other override above is pipeline-agnostic and can be
reused as-is.

Add `--verbose` to stream logs to the terminal instead of `./logs/`. The skill
does not poll progress — the user re-invokes if they want a status; point them
at `complexa status` and `./logs/design_pipeline_*/`.

### Debugging a single stage

For debugger or profiler use, call the matching `proteinfoundation` module
directly with the same resolved pipeline configuration. Prefer the CLI for
ordinary runs because it preserves logs and parallel-job routing; the
individual-stage command patterns are in
[references/INFERENCE.md](references/INFERENCE.md#individual-stages).

For AME inputs evaluated with RF3, ensure the ligand is represented as `L:0`
before refolding; otherwise RF3 can complete CCD atoms and corrupt RMSD
calculation. This does not apply to AF2/ColabDesign or non-AME runs.

Wall-clock at default (`nsteps=400`, `beam_width=8`, `batch_size=16`, 100
designs, colabdesign eval) is ~30–120 minutes on a single A100/H100.

## Step 6: Collect results

Outputs land in two directories. Surface both:

> **Caution:** These paths are relative to the current directory. Runs can
> consume tens of GB, and the manifest path below is overwritten on repeated
> use. Choose an empty run directory or back up existing results first.

```bash
ls ./inference/${CONFIG_STEM}_${TASK}_*${RUN_NAME}/   # generated PDBs + filter
ls ./evaluation_results/${RUN_NAME}/                  # per-design CSV + analysis
```

Read the combined results CSV and summarize:

```bash
ls ./evaluation_results/*/binder_results_*_combined.csv
ls ./evaluation_results/*/motif_binder_results_*_combined.csv  # AME
ls ./evaluation_results/*/res_filter_*_pass_*.csv              # success rate
ls ./evaluation_results/*/res_div_foldseek_*.csv               # FoldSeek diversity
```

Pull the success rate from `res_filter_binder_pass_*.csv`, the per-design
metrics (interface pAE, pLDDT, scRMSD) from the combined CSV, and FoldSeek
TM-score diversity from `res_div_foldseek_*.csv`. Report top-N designs by
i_pAE (protein binder) or min_ipAE (ligand binder).

## Step 7: Emit manifest

Drop a JSON manifest beside the results so the run is replayable. The shared
helper captures the command, config, git SHA, and pointers to the result CSVs.

```bash
python3 scripts/write_manifest.py \
    --output-dir ./evaluation_results/${RUN_NAME} \
    --command "complexa design configs/search_binder_local_pipeline.yaml ++run_name=${RUN_NAME} ++generation.task_name=${TASK}" \
    --skill complexa-design \
    --out ./run_manifest.json
```

Surface the manifest path and the result CSV to the user.

## Most-common overrides

The 10 overrides that cover ~90% of runs. Full reference (every key, type,
default) is in [references/overrides.md](references/overrides.md).

| Override | Default | What it controls |
|----------|---------|------------------|
| `++generation.task_name=<name>` | (per config) | Which target / AME task to design for |
| `++run_name=<str>` | (config stem) | Output dir suffix and CSV tag |
| `++generation.search.algorithm=beam-search` | `best-of-n` (binder/ligand), `single-pass` (AME) | Search strategy |
| `++generation.search.beam_search.beam_width=8` | `4` | Beam-search width (more = better designs, slower) |
| `++generation.args.nsteps=200` | `400` | Diffusion steps (fewer = faster, lower quality) |
| `++generation.dataloader.batch_size=8` | `16` (binder/ligand/AME) | Drop to 8 on a 40GB GPU |
| `++generation.filter.filter_samples_limit=500` | `1000` | Top-N samples to keep after filtering |
| `++metric.binder_folding_method=esmfold` | `colabdesign` (binder), `rf3_latest` (ligand/AME) | Evaluation refold backend |
| `++metric.num_redesign_seqs=8` | `2` | ProteinMPNN/LigandMPNN/SolubleMPNN sequences per design |
| `++aggregation.success_thresholds.i_pAE.threshold=10.0` | `7.0` (protein binder) | Loosen / tighten success criteria |

## Hardware requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| GPU | 1x CUDA GPU, 40 GB VRAM | A100 / H100 / L40S, 80 GB VRAM |
| CPUs | 16 | 24 (the `ncpus_` default in every pipeline config) |
| Disk | 50 GB at `./inference/` + `./evaluation_results/` | 200 GB for sweep runs |
| RAM | 32 GB | 64 GB+ |

Typical wall-clock for 100 designs, `beam_width=8`, default `nsteps=400`:

- Protein binder + colabdesign refold: ~60–120 min on 1x A100/H100.
- Ligand binder + RF3 refold: ~90–180 min (RF3 dominates).
- AME + RF3 refold: ~120–240 min.
- Any pipeline + ESMFold refold: ~30–60 min (fast iteration).

Bumping `gen_njobs=2` and `eval_njobs=2` halves wall-clock on a 2-GPU host. See
`references/hardware.md` for per-pipeline VRAM tables.

## Troubleshooting (common cases)

| Symptom | Cause | Fix |
|---------|-------|-----|
| `CUDA out of memory` in generate | `batch_size: 16` too big on 40GB GPU | `++generation.dataloader.batch_size=8` |
| `CUDA out of memory` in evaluate | AF2 / RF3 batched too aggressively | `++eval_njobs=1` and `++metric.num_redesign_seqs=2` |
| `InterpolationKeyError: AF2_DIR` | colabdesign eval but `.env` does not set `AF2_DIR` | Set `AF2_DIR` in `.env` or `++metric.binder_folding_method=esmfold` |
| `InterpolationKeyError: RF3_CKPT_PATH` | RF3 eval but RF3 not installed | `complexa download --all` or switch eval backend |
| `KeyError: 'task_name' not in target_dict_cfg` | Target not in `targets_dict.yaml` / `ligand_targets_dict.yaml` / `ame_dict_v2.yaml` | Use `complexa-target` skill to add it |
| 0 designs pass success thresholds | Defaults too strict for this target | Loosen via `++aggregation.success_thresholds.*` |

For detailed troubleshooting, see
[references/troubleshooting.md](references/troubleshooting.md).
