---
name: complexa-design
description: Run or review Proteina-Complexa binder and motif design campaigns; analyze their results. Do not use for sequence annotation.
compatibility: "Reviews need supplied files; execution needs a configured Proteina-Complexa CLI, CUDA allocation, checkpoints, and selected model dependencies."
allowed-tools: Bash, Read, Write, Env, AskUserQuestion
metadata:
  author: Ohad Mosafi <omosafi@nvidia.com>
  tags: [protein-design, complexa, binder-design, scientific-workflows]
---

# Complexa Design

## Purpose

Prepare, execute, or analyze protein-binder, ligand-binder, and AME motif-scaffolding
campaigns with Proteina-Complexa. The project CLI implements generation, filtering,
refolding, and analysis. This skill supplies decision guidance and two local
bookkeeping helpers; it does not implement inference.

## Prerequisites

For an offline review, use the supplied configuration, source snapshot, or result
tables. A partial checkout is enough to review the represented behavior; record
unresolved inputs without installing dependencies or downloading weights.

For execution, use an initialized project installation with its environment file,
target structures, matching model/autoencoder checkpoints, and allocated CUDA GPU.
Search rewards and final evaluation have separate dependencies: AF2 needs
`AF2_DIR`; RF3 needs `RF3_CKPT_PATH` and `RF3_EXEC_PATH`. Check additional models
and tools selected by the resolved configuration, including auxiliary monomer
metrics. Python 3 and Bash suffice for the bundled helpers. See
[hardware and dependency checks](references/hardware.md) when assessing readiness.

## Inputs

| Input | Required or optional | Source |
|---|---|---|
| Requested outcome | Required | User request: review, preparation, execution, or result analysis |
| Source/configuration | Required for implementation-specific work | Supplied snapshot or installed project revision |
| Target and structures | Required for execution | Registered task key and matching structures; reviews may record missing inputs |
| Campaign overrides | Optional | User's run name, sample/search/refinement settings, backend, sequence types, and criteria; otherwise preserve defaults |
| Result tables and metadata | Required for outcome analysis | Supplied export with units and denominators |
| Output destination | Optional | User's requested paths; otherwise choose a new run directory |

Explicit user choices take precedence over saved state and configuration defaults.
Reuse prior evidence for this request when it still applies. Resolve implementation
questions against the supplied source revision, not contradictory comments or an
unrelated installation. Ask only for missing inputs that affect the requested work.

## Instructions

1. **Choose the task mode.** For reviews and launch preparation, inspect the supplied
   inputs and the relevant reference below, then write the requested artifacts.
   Skip runtime probes and inference. For result analysis, compute from the actual
   tables and metadata; do not launch a new campaign. For execution, follow steps
   2–5. Do not read evaluation definitions or benchmark reports as task guidance.
2. **Resolve the campaign.** Select the matching pipeline using
   [pipeline defaults](references/pipelines.md). Inspect that pipeline and the
   relevant composed stage config. Target keys are registry entries, not arbitrary
   protein names. If a requested target is absent, identify the missing structure,
   chain/hotspot or motif definition needed to prepare it. Preserve LoRA and
   architecture settings required by the selected checkpoint.
3. **Check the actual runtime.** Keep the installed skill location separate from
   the project working directory. Run `preflight.sh` from the project directory,
   using an explicit report destination, and read its JSON. Reuse an existing probe
   unless the environment changed. A failed probe, inaccessible allocated GPU,
   missing weights, or failed GPU run does not establish GPU absence; consult
   allocation/device evidence before using an absence-conditioned CPU fallback.
4. **Validate and execute.** Review overrides against the composed configuration.
   Run `complexa validate design PIPELINE` on the prepared installation. At the
   documented revision this validator does not accept Hydra overrides or fully
   validate their semantics; use the checks in [CLI execution](references/INFERENCE.md).
   Correct an identified configuration error before retrying; report unresolved
   runtime/input blockers. Launch `complexa design` with the exact reviewed
   configuration and overrides. Follow an authorized foreground campaign through
   completion, checking process exit status and stage logs. A submitted/background
   job is running, not a completed result; retain its job/session and log paths.
5. **Inspect and deliver.** Read the actual generated/evaluated artifacts, apply the
   recorded criteria, and report attrition and missing metrics. Use
   [evaluation outputs](references/EVALUATION_METRICS.md) for output discovery.
   Write a manifest beside executed-run results and verify its command, config,
   revision, and CSV pointers. Record missing provenance rather than inventing it.

For any requested file deliverable, write it to the requested destination, reopen
it, and check the relevant configuration or computed values. Validate shell
syntax with `bash -n`; parse YAML/JSON and check table-derived results when
applicable. Stop once the requested artifacts and relevant checks are complete.
Configuration preparation alone is not evidence of model execution.

## Available Scripts

| Script | Purpose | Arguments |
|---|---|---|
| [preflight.sh](scripts/preflight.sh) | Inspect local GPU, checkpoint, and tool readiness; write JSON | `--out PATH`, optional `--quiet`; `--help` |
| [write_manifest.py](scripts/write_manifest.py) | Record an executed command, available config, checkpoint fingerprints, and CSV pointers | Required `--output-dir DIR --command TEXT --skill complexa-design`; `--out PATH`; optional `--include-system-metadata`; `--help` |

Invoke these with Bash/Python. Use the installed skill location provided by the
host for `COMPLEXA_SKILL_DIR`; use the actual inference project for
`COMPLEXA_PROJECT_DIR`. Assign variables before expanding them in commands.
Preflight reads `.env` as data from the current directory. Both helpers write
files, and an existing destination can be overwritten, so choose run-specific
paths. Neither helper provisions an environment or validates scientific success.

## Examples

For an offline request such as “review these ligand filter settings and write an
audit,” read the supplied table and filtering source, use the relevant section of
`search_and_analysis.md`, compute the selections, and save/reopen the audit. Do not
probe GPUs or treat synthetic PDB paths as files to refold.

For a prepared protein-binder runtime, these are separate readiness and launch
commands; replace the example target/run with the reviewed values:

```bash
cd "$COMPLEXA_PROJECT_DIR"
bash "$COMPLEXA_SKILL_DIR/scripts/preflight.sh" --out "$RUN_ARTIFACT_DIR/preflight.json"
complexa validate design configs/search_binder_local_pipeline.yaml
complexa design configs/search_binder_local_pipeline.yaml \
    ++run_name=binder_pilot ++generation.task_name=02_PDL1 \
    ++generation.dataloader.dataset.nres.nsamples=12
```

Inspect readiness before launching. The sample count is a base dataset setting;
search replicas and repeats can produce more candidate records. After execution,
set `RESULTS_DIR` to the actual results directory and `EXECUTED_COMMAND` to the
command that was run, then record provenance:

```bash
python3 "$COMPLEXA_SKILL_DIR/scripts/write_manifest.py" \
    --output-dir "$RESULTS_DIR" --command "$EXECUTED_COMMAND" \
    --skill complexa-design --out "$RUN_ARTIFACT_DIR/run_manifest.json"
```

## Output Format

Honor requested filenames and schemas. The final handoff must identify `status`,
`artifacts`, `checks`, and `limitations`, in the requested format. Include the
following fields for the applicable outcome:

- **Review/preparation:** corrected configuration or launch script, source revision,
  reasons for changes, checks performed, and unresolved launch requirements.
- **Executed campaign:** completion/partial/failure status, exact command and resolved
  settings, manifest, generation/evaluation directories, result tables, and logs.
- **Outcome analysis:** criteria with units/operators, passing IDs and denominators
  for each sequence type, base-design coverage, missing data/attrition, and
  successful structural-cluster counts when assignments exist.

Separate generated-sequence success from post-generation redesign and distinguish
synthetic calculations, predicted behavior, and measured in-silico results.

## Limitations

Refolding confidence and search rewards do not establish experimental affinity.
Search and filtering can discard candidates or one member of a refinement pair;
retain source artifacts for comparisons. Configuration and path checks cannot
prove that a refolder used the intended geometry or that a model will fit GPU
memory. The manifest hashes only the first 4 KiB of checkpoints and lists at most
50 CSVs; check it for unresolved config paths or missing provenance.

## Troubleshooting

Use [failure diagnosis](references/troubleshooting.md) for a reported error.
Preserve the requested backend, search budget, and scientific criteria while
correcting the cause. Do not turn missing dependencies into an automatic backend
switch, or zero successes into relaxed thresholds. Check units and missing metrics
before interpreting a low pass rate.

## References

Load only the reference needed for the current decision, then inspect the relevant
source/config section if the version differs or a question remains unresolved.
All paths mentioned inside these guides are relative to the inference project.

| Decision | Reference |
|---|---|
| Protein, ligand, or AME pipeline and checkpoint | [Pipeline defaults](references/pipelines.md) |
| Compose a configuration or trace a nested key | [Configuration guide](references/CONFIGURATION_GUIDE.md) |
| Choose common command-line overrides | [Overrides](references/overrides.md) |
| Execute, validate, or resume stages | [CLI execution](references/INFERENCE.md) |
| Budget search, combine rewards, compare refinement, or audit filtering | [Search and campaign analysis](references/search_and_analysis.md) |
| Interpret metrics and discover result files | [Evaluation outputs](references/EVALUATION_METRICS.md) |
| Match candidate lineage | [Search metadata](references/SEARCH_METADATA.md) |
| Plan an explicitly requested parameter sweep | [Sweeps](references/SWEEP.md) |
| Diagnose resource or dependency problems | [Hardware](references/hardware.md), [Troubleshooting](references/troubleshooting.md) |
