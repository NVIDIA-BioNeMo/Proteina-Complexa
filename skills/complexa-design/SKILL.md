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
compatibility: "complexa CLI installed; environment file populated; one CUDA GPU with at least 40 GB VRAM (A100, H100, or L40S); 24 CPUs; about 50 GB disk"
allowed-tools: Bash, Read, Write, Env, AskUserQuestion
---

<!-- CI revalidation requested. -->

# Complexa Design Skill

Drive the full four-stage `complexa design` pipeline: generate (flow matching +
search), filter (top-N by reward), evaluate (refold with AF2 or RF3), then
analyze (success rate and sequence-structure diversity). Pick the right pipeline
config for the design intent, validate the run upfront so the user does not
discover a missing ckpt mid-folding, run it, and emit a replayable manifest +
per-design success CSV.

## Choose the requested outcome

For a configuration review or future launch script, use the supplied project
files and [Pipeline Reference](references/pipelines.md). Read the selected
pipeline YAML and its generation config; follow other references only for a
specific unresolved key or output. A partial snapshot supports a review, but
does not establish that the CLI, targets, weights, or refolder are installed.
Finish the requested artifacts and record missing launch prerequisites. Check
shell syntax with `bash -n`; runtime validation waits for a prepared installation.

For an actual campaign, follow the runtime steps below. Use parameters already
supplied by the user; ask only for missing inputs that change the design. When
readiness was already probed for this request, reuse that evidence unless the
environment changes. Keep configuration preparation, generation, and measured
evaluation results distinct in the final answer.

## Step 1: Pre-flight

Always run the shared preflight before launching a design — generation needs the
GPU and the right checkpoint, evaluation needs AF2 or RF3 weights and tool
binaries. Bail early if the host cannot run the chosen pipeline.

When a request permits a CPU fallback only if no GPU is available, verify the
allocated hardware first. An allocated GPU with missing dependencies or weights, or a
failed GPU run, remains blocked on the requested execution; it does not qualify
for that fallback. Report probe failures separately from confirmed GPU absence.
The shared preflight's `gpu.available=false` also covers failed or missing
`nvidia-smi`; check device/allocation evidence before treating it as GPU absence.
In containers, `/proc/driver/nvidia/gpus` and loaded kernel modules may describe
the host, not this task's allocation. Check container device exposure and any
available scheduler allocation information together. A CPU allocation can share
a GPU host; an allocated GPU with inaccessible devices is blocked. If allocation
remains unclear, report it as undetermined.

Set `SKILL_DIR` to the directory containing this manifest in a separate shell
assignment, then run; an inline environment assignment cannot set its expansion
in the same command:

```bash
bash "$SKILL_DIR"/scripts/preflight.sh
```

Read the JSON report emitted by preflight and bail if any of these are missing
for the chosen pipeline:

- `gpu.available: false` -> GPU execution is not ready; distinguish absent hardware from a failed probe as above.
- `gpu.vram_gb < 40` -> generation OOMs at default `batch_size: 16`; lower to 8.
- `checkpoints["complexa.ckpt"].exists` and `checkpoints["complexa_ae.ckpt"].exists` -> required for protein binder.
- `checkpoints["complexa_ligand.ckpt"].exists` and `checkpoints["complexa_ligand_ae.ckpt"].exists` -> required for ligand binder.
- `checkpoints["complexa_ame.ckpt"].exists` and `checkpoints["complexa_ame_ae.ckpt"].exists` -> required for AME.
- `community_models.AF2_DIR.exists: false` -> protein binder default eval (`colabdesign`) fails.
- `community_models.RF3_CKPT_PATH.exists: false` or `tools.rf3.exists: false` -> ligand binder / AME default eval (`rf3_latest`) fails.

If a ckpt is missing, point at `complexa-setup` and have the user run
`complexa download --complexa-<variant>` first.

## Step 2: Pick the pipeline

Select the pipeline YAML that matches the requested target. Each YAML pins the
corresponding checkpoint, target dictionary, reward, and refold backend.

| Request | Pipeline | Target pattern | Default refold |
|---|---|---|---|
| Protein-surface binder (default) | Protein local pipeline | `02_PDL1` | `colabdesign` |
| Small-molecule pocket or ligand binder | Ligand local pipeline | `39_7V11_LIGAND` | `rf3_latest` |
| AME enzyme or motif-plus-ligand scaffold | AME local pipeline | `M0096_1chm` | `rf3_latest` |

Protein binder is the default when the user does not identify a ligand or
motif. Do not remove the `lora:` block in ligand or AME pipeline YAMLs; those
released checkpoints require it. AME defaults to `single-pass`; enable a
reward model before selecting a reward-guided search algorithm. Use the exact
pipeline command in the bundled Pipeline Reference at
`"$SKILL_DIR"/references/pipelines.md`; it also lists checkpoints, target
dictionaries, and thresholds.

## Step 3: Gather parameters

Fill in parameters not already specified. Preserve the selected pipeline's
defaults unless the user requests a change.

- **Target name** — must be a key in the matching protein, ligand, or AME target
  dictionary documented in the bundled Pipeline Reference. If the user names a
  target that is not present, hand off to `complexa-target` to add it first.
- **Run name** — a short identifier appended to the output dir (e.g. `pdl1_v1`).
- **Search algorithm** — binder and ligand default to `best-of-n`; AME defaults
  to `single-pass` with no reward model. A requested beam-width change also
  needs `++generation.search.algorithm=beam-search`; changing the width alone
  does not select that algorithm.
- **Sample count** — set `++generation.dataloader.dataset.nres.nsamples=N`
  for the requested base sample count. `batch_size` controls memory use and
  `filter_samples_limit` caps retained outputs; neither requests N generated
  designs. Search intermediates, filtering, and failures can change final counts.
- **Evaluation refold backend** — protein binder defaults to `colabdesign`
  (AF2); ligand and AME default to `rf3_latest`. Use `esmfold` for fast iteration
  (worse but seconds per sample).

## Step 4: Validate

Validate before running. This is cheap (seconds) and catches missing ckpts,
missing env vars, configuration errors, and missing target entries — all of
which would otherwise abort the pipeline mid-evaluation after hours of
generation.

Run `complexa validate design` with the selected pipeline command and the
chosen target override. The bundled Inference Guide at
`"$SKILL_DIR"/references/INFERENCE.md` has exact validation examples. The
validator returns non-zero on failure and prints a status report. Correct the
reported configuration issue and retry after that change. Missing runtime or
scientific inputs are blockers to report, not reasons to keep retrying validation.

## Step 5: Run the pipeline

`complexa design` is the right tool for the full 4-stage run — it orchestrates
`generate → filter → evaluate → analyze` as sequential subprocesses with a
shared run name, log directory, and multi-GPU split. Re-implementing that
manually loses the per-stage log routing and progress prints.

Use `++` (forced) Hydra overrides; they apply to all stages. Start from the
matching production command in the bundled Pipeline Reference and add the run
name, target, search algorithm, beam width, and refold backend selected above.
For ligand binder and AME, select the matching pipeline and target; the common
overrides can otherwise be reused.

Add `--verbose` to stream logs to the terminal. The skill does not poll
progress — the user re-invokes if they want a status; point them at
`complexa status` and the run's log directory.

### Debugging a single stage

For debugger or profiler use, call the matching `proteinfoundation` module
directly with the same resolved pipeline configuration. Prefer the CLI for
ordinary runs because it preserves logs and parallel-job routing; the
individual-stage command patterns are in the bundled Inference Guide.

For AME inputs evaluated with RF3, ensure the ligand is represented as `L:0`
before refolding; otherwise RF3 can complete CCD atoms and corrupt RMSD
calculation. This does not apply to AF2 with ColabDesign or non-AME runs.

Wall-clock at default (`nsteps=400`, `beam_width=8`, `batch_size=16`, 100
designs, colabdesign eval) is about 30–120 minutes on a single A100 or H100.

## Step 6: Collect results

Outputs land in generation and evaluation directories. Surface both, using the
paths printed by the CLI:

> **Caution:** These paths are relative to the current directory. Runs can
> consume tens of GB, and the manifest path below is overwritten on repeated
> use. Choose an empty run directory or back up existing results first.

Read the combined results CSV and summarize the success-rate, per-design, and
diversity CSVs described in the bundled Evaluation Metrics Guide. Report top-N
designs by i_pAE for protein binders or min_ipAE for ligand binders.

## Step 7: Emit manifest

Drop a JSON manifest beside the results so the run is replayable. The shared
helper captures the command, config, git SHA, and pointers to the result CSVs.

```bash
python3 "$SKILL_DIR"/scripts/write_manifest.py \
    --output-dir <results-directory> \
    --command "<exact-complexa-command-that-was-run>" \
    --skill complexa-design \
    --out <manifest-file>
```

Surface the manifest path and the result CSV to the user.

## Most-common overrides

The 10 overrides that cover ~90% of runs. Full reference (every key, type,
default) is in the bundled Overrides Reference.

| Override | Default | What it controls |
|----------|---------|------------------|
| `++generation.task_name=<name>` | (per config) | Which target / AME task to design for |
| `++run_name=<str>` | (config stem) | Output dir suffix and CSV tag |
| `++generation.search.algorithm=beam-search` | `best-of-n` (binder and ligand), `single-pass` (AME) | Search strategy |
| `++generation.search.beam_search.beam_width=8` | `4` | Beam-search width (more = better designs, slower) |
| `++generation.args.nsteps=200` | `400` | Diffusion steps (fewer = faster, lower quality) |
| `++generation.dataloader.batch_size=8` | `16` (all pipelines) | Drop to 8 on a 40GB GPU |
| `++generation.filter.filter_samples_limit=500` | `1000` | Top-N samples to keep after filtering |
| `++metric.binder_folding_method=esmfold` | `colabdesign` (binder), `rf3_latest` (ligand and AME) | Evaluation refold backend |
| `++metric.num_redesign_seqs=8` | `2` | Inverse-folded sequences per design |
| `++aggregation.success_thresholds.i_pAE.threshold=10` | seven (protein binder) | Loosen or tighten success criteria |

## Hardware requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| GPU | 1x CUDA GPU, 40 GB VRAM | A100, H100, or L40S, 80 GB VRAM |
| CPUs | 16 | 24 (the `ncpus_` default in every pipeline config) |
| Disk | 50 GB for generated and evaluation outputs | 200 GB for sweep runs |
| RAM | 32 GB | 64 GB+ |

Typical wall-clock for 100 designs, `beam_width=8`, default `nsteps=400`:

- Protein binder + colabdesign refold: ~60–120 min on one A100 or H100.
- Ligand binder + RF3 refold: ~90–180 min (RF3 dominates).
- AME + RF3 refold: ~120–240 min.
- Any pipeline + ESMFold refold: ~30–60 min (fast iteration).

Bumping `gen_njobs=2` and `eval_njobs=2` halves wall-clock on a 2-GPU host. See
the bundled Hardware Reference for per-pipeline VRAM tables.

## Troubleshooting (common cases)

| Symptom | Cause | Fix |
|---------|-------|-----|
| `CUDA out of memory` in generate | `batch_size: 16` too big on 40GB GPU | `++generation.dataloader.batch_size=8` |
| `CUDA out of memory` in evaluate | AF2 / RF3 batched too aggressively | `++eval_njobs=1` and `++metric.num_redesign_seqs=2` |
| `InterpolationKeyError: AF2_DIR` | colabdesign eval but `.env` does not set `AF2_DIR` | Set `AF2_DIR` in `.env` or `++metric.binder_folding_method=esmfold` |
| `InterpolationKeyError: RF3_CKPT_PATH` | RF3 eval but RF3 not installed | `complexa download --all` or switch eval backend |
| `KeyError: 'task_name' not in target_dict_cfg` | Target absent from the selected target dictionary | Use `complexa-target` skill to add it |
| 0 designs pass success thresholds | Defaults too strict for this target | Loosen via `++aggregation.success_thresholds.*` |

For detailed troubleshooting, see the bundled Troubleshooting Reference.
