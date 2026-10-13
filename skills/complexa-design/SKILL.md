---
name: complexa-design
description: >
  Prepare, review, or run Proteina-Complexa design campaigns for protein binders,
  small-molecule binders, and AME motif-plus-ligand scaffolds.
allowed-tools: Bash, Read, Write, Env, AskUserQuestion
metadata:
  author: Ohad Mosafi <omosafi@nvidia.com>
  tags: [proteina-complexa, protein-design, campaign-planning]
---

# Complexa Design

## Purpose

Use the separately installed first-party `complexa design` CLI for
**generate → filter → evaluate → analyze**. Bundled scripts prepare plans, inspect
readiness, and record provenance; they do not implement inference. GPU execution requires
a prepared CUDA runtime, model and refolder weights, tools, and target inputs.

Activate for requests such as "prepare a Complexa binder launch" or "run an AME
design campaign." Standalone evaluation of existing PDBs, target registration,
installation, and parameter sweeps are separate workflows.

## Inputs

Required for launch planning: source checkout/snapshot, pipeline, target/task,
run name, and output location. Sample budget, search, and refolder are optional
overrides of the selected config. Explicit user choices take precedence over
config defaults; ask only for missing scientific inputs needed for the scope.

## Prerequisites

Offline planning needs a source checkout/snapshot, Python 3, PyYAML, and Bash
for syntax checking. Execution additionally needs the installed Complexa CLI,
CUDA access, registered inputs, and weights for every active backend.

## Instructions

### 1. Select the pipeline and scope

For launch preparation, use `scripts/prepare_campaign.py` to read the selected
source stages, compute job budgets, check the released checkpoint/search
contract, and write `launch.sh`, `campaign_overrides.yaml`, and
`campaign_plan.json`. It needs Python with PyYAML, runs offline, and never starts
inference. Inspect its compact output and any missing stage files; it does not
compose nested Hydra defaults or validate runtime readiness. Use supplied
snapshots for reviews. Read source/reference details only where the plan leaves
an unresolved decision. For unsupported custom pipelines, inspect the selected
YAML and its generation config directly. Options: [planning.md](references/planning.md).

Use `--revision` for planning retries. Read the returned `output_dir`; an existing
plan stays intact and the revision receives a new sibling directory. Do not
delete output directories to satisfy the helper's new-directory requirement.

| Intent | Pipeline under `configs/` | Model / autoencoder | Search / evaluation defaults |
|---|---|---|---|
| Protein-surface binder | `search_binder_local_pipeline.yaml` | `complexa.ckpt` / `complexa_ae.ckpt` | `best-of-n` / `colabdesign` (AF2) |
| Small-molecule binder | `search_ligand_binder_local_pipeline.yaml` | `complexa_ligand.ckpt` / `complexa_ligand_ae.ckpt` | `best-of-n` / `rf3_latest` |
| AME motif + ligand scaffold | `search_ame_local_pipeline.yaml` | `complexa_ame.ckpt` / `complexa_ame_ae.ckpt` | `single-pass` / `rf3_latest` |

Generation configs are `configs/pipeline/{binder,ligand_binder,ame}/*_generate.yaml`.
Protein, ligand, and AME target registries are respectively
`configs/targets/targets_dict.yaml`, `configs/targets/ligand_targets_dict.yaml`,
and `configs/design_tasks/ame_dict_v2.yaml`. Check the requested key there when
available. If missing, request the structure and selections needed to register
it; a plan can retain an explicitly unresolved key. Never substitute a bundled
target for an unregistered one. AME needs curated `contig_atoms` and ligand
selection under `motif_target_dict_cfg`; do not invent them.

For **review or launch preparation**, finish the requested files without
inference. Probe readiness only when requested or when selecting a permitted
hardware-dependent fallback. Missing runtime files do not prevent static review.
For **execution**, resolve missing scientific inputs and check readiness before
launch. Preserve the user's chosen scope, search, refolder, and success criteria.

### 2. Check readiness once when needed

Set `SKILL_DIR` to this skill's directory and `OUTPUT_DIR` to the requested
artifact directory in separate assignments before using them. From the prepared
project root (or supplied snapshot for a readiness review):

```bash
bash "$SKILL_DIR/scripts/preflight.sh" --out "$OUTPUT_DIR/preflight.json"
```

Reuse this evidence unless the environment changes. `gpu.status` is
`accessible`, `absent`, `blocked`, or `unknown`; `gpu.evidence` saves exposed
devices, allowlisted allocation hints, and one NVIDIA query's output, exit
status, and timeout. Management access does not prove CUDA inference works.
Use these observations directly; only probe missing signals for `unknown` or
diagnose a specific blocker. An already installed CUDA runtime may help; do not
install one to probe. Never dump the full environment or `.env`. Checkpoint
hashing is optional (`--hash-checkpoints`), not needed for routine readiness.

- Allocated GPU: keep GPU mode even if access, runtime, weights, or memory block
  launch. A failed execution remains a GPU failure.
- Confirmed absence of a task GPU allocation: use the CPU fallback if requested.
- Conflicting or incomplete evidence: report allocation as undetermined/blocked.

A failed probe alone does not establish GPU absence. Visibility variables are
hints, not a substitute for allocation evidence. Host `/proc/driver/nvidia` data
and kernel modules do not establish a task allocation. Do not repeat broad host
searches once the evidence is sufficient, or provision software during a review.

Check the checkpoint paths in the effective configuration (which can differ
from preflight's environment defaults), actual CLI availability, and dependencies
of **both generation reward and evaluation**. Protein search uses AF2_DIR;
ligand reward and ligand/AME evaluation need RF3_CKPT_PATH and RF3_EXEC_PATH.
Changing `metric.binder_folding_method` changes evaluation only: ESMFold does
not remove an active AF2/RF3 reward dependency. Existence checks alone do not
prove a backend can execute. For capacity decisions use [hardware.md](references/hardware.md).

### 3. Set the effective configuration

Use Hydra `++key=value` overrides with `complexa design`; preserve other defaults.

| Decision | Controls and constraints |
|---|---|
| Target and outputs | `generation.task_name`, unique `run_name`; preserve existing results |
| Generated sample budget | With the supplied `UniformInt` dataset, `generation.dataloader.dataset.nres.nsamples × generation.dataloader.dataset.nrepeat_per_sample` is the base count; the length range is not another multiplier |
| Memory and retention | `generation.dataloader.batch_size` changes batch memory; `generation.filter.filter_samples_limit` caps retained candidates, not generation |
| Beam search | Set `generation.search.algorithm=beam-search` and `generation.search.beam_search.beam_width`; width alone does not activate it |
| Search reward | `generation.reward_model.*`; separate from `generation.refinement.*`, evaluation `metric.*`, and analysis `aggregation.success_thresholds.*` |
| Ligand/AME checkpoints | Preserve the released `lora` block (`r=32`, `lora_alpha=64.0`, `lora_dropout=0.0`, `train_bias=none`) |
| AME architecture/search | Preserve `env_vars.USE_V2_COMPLEXA_ARCH="True"`; default reward is null, so configure a reward model before enabling reward-guided search |

Search lookaheads, duplicates, filtering, and failures affect observed output
counts. State the requested base count separately from generated, retained,
evaluated, and successful designs. GPU job counts split work; they are not a
sample-count multiplier. See [pipelines.md](references/pipelines.md) for variant
details and [overrides.md](references/overrides.md) for additional keys.

### 4. Validate, execute, and verify the requested outcome

For a saved launch script, run `bash -n` on that file directly and read it back.
This checks syntax only; it does not validate runtime readiness. A partial
snapshot cannot support live validation, and unresolved targets remain explicit
in the plan. Keep requested artifacts and existing output directories intact.

On a prepared installation, run `complexa validate design CONFIG.yaml`. For
protein/ligand targets, also use `complexa validate target CONFIG.yaml --target TARGET`.
The target validator reads `target_dict_cfg`; check AME's `motif_target_dict_cfg`
and atom selections separately. Validation does not accept design's Hydra
overrides; check the effective overrides separately and do not claim the
base-config check validated them. Retry after a concrete fix, not repeatedly
against missing dependencies. Use [troubleshooting.md](references/troubleshooting.md)
for a specific failure. For an explicitly requested cluster launch, use
[cluster_execution.md](references/cluster_execution.md).

Launch the authorized `complexa design` command and follow its logs through all
four stages. Report an unfinished/background run as running, not completed.
Preserve logs on failure. For AME with RF3, check the documented `L:0` ligand
representation before refolding; do not silently rewrite scientific inputs.

Read the actual output paths printed by the CLI. Use generation logs/results
for generated counts, combined per-design CSVs for evaluation, `res_filter_*_pass_*.csv`
for success, and `res_div_foldseek_*.csv` / `res_div_mmseqs_*.csv` for diversity.
Report the sample subset and saved success criteria. Do not loosen thresholds
to improve a pass rate or infer diversity from configuration files. Details:
[results.md](references/results.md).

After execution, record the real invocation and output directory:

```bash
python3 "$SKILL_DIR/scripts/write_manifest.py" \
  --output-dir "$RESULTS_DIR" --command "$EXECUTED_COMMAND" \
  --skill complexa-design --out "$OUTPUT_DIR/run_manifest.json"
```

## Output Format

Before finishing, reopen the saved artifacts. Show compact, separately bounded
tool output for the mode/reason, allocation evidence, exact launch command and
sample controls, or actual result counts and CSV paths. Avoid a single large
dump that truncates the command or evidence. If the request requires
`execution_mode.json`, include `selected_mode`, `task_status`, `gpu_execution`,
`reason`, and paths to actual evidence; keep CPU preparation distinct from a
completed GPU campaign. Report unresolved prerequisites and unmeasured results.

## Available Scripts

Set `SKILL_DIR` to this skill's installed directory. Invoke helpers through Bash
or Python as shown in the examples.

| Script | Purpose | Arguments |
|---|---|---|
| `scripts/prepare_campaign.py` | Prepare a static plan and syntax-checked launch script | `--project-root`, `--pipeline`, `--target`, `--run-name`, `--out-dir`; optional controls via `--help` |
| `scripts/preflight.sh` | Inspect readiness without installing dependencies | `--out`; optional `--hash-checkpoints` |
| `scripts/gpu_probe.py` | Collect bounded GPU allocation/access evidence; used by preflight | None |
| `scripts/write_manifest.py` | Record invocation, config, and result paths | `--output-dir`, `--command`, `--skill`, `--out` |

## Limitations

A static plan does not compose nested Hydra defaults or prove runtime readiness.
GPU access does not establish scientific success; only completed evaluations
provide measured success and diversity results.

## Troubleshooting

For missing weights, refolder errors, chain mismatches, or OOMs, match the
symptom in [troubleshooting.md](references/troubleshooting.md) before retrying.
For an offline review, record the remedy without provisioning a runtime.

## Examples

**PD-L1, beam search, AF2, 50 base samples.** Set `PROJECT_ROOT` to the source
tree and `PLAN_DIR` to a new artifact directory. Prepare and inspect the plan:

```bash
python3 "$SKILL_DIR/scripts/prepare_campaign.py" \
  --project-root "$PROJECT_ROOT" --out-dir "$PLAN_DIR" --revision \
  --pipeline binder --target 02_PDL1 --run-name pdl1_beam \
  --samples 50 --repeats 1 --search beam-search --beam-width 8 \
  --refolder colabdesign
```

Before an authorized run, resolve the plan's missing prerequisites and set
`COMPLEXA_PROJECT_ROOT` to the prepared installation for `launch.sh`. When the
user specifies artifact filenames, place the requested files there and read
them back; the helper's plan does not replace a requested review or mode manifest.

**Unregistered ATP ligand.** Prepare a ligand pipeline plan with the ligand
checkpoint pair, LoRA, and RF3 dependencies. Request the structure, ligand
selection/chemistry, and binder length needed for registration. Keep the future
task key unresolved and report that no binding results have been measured.

**AME scaffold review.** Check the AME checkpoint pair, LoRA, v2 architecture,
motif/ligand inputs, default single-pass search, and RF3 evaluation. Explain which
real success and diversity files a later campaign must produce. If asked to
change search, address its reward configuration as part of the same change.
