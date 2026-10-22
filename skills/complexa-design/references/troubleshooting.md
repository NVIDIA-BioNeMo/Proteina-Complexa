# Failure diagnosis

Start with the failing stage, exact command/configuration, exit status, and a
bounded relevant log excerpt. Correct a demonstrated cause and retry that step;
repeating the same failure without a change adds no evidence. Preserve existing
results and scientific criteria while diagnosing the problem.

## Match the failure to its cause

| Symptom | Evidence to inspect | Action |
|---|---|---|
| `validate` rejects a `++...` argument | `cli_runner.py` validation parser | Remove unsupported override arguments from the readiness command; review the intended launch overrides separately |
| Missing key or interpolation | Selected pipeline, composed config namespace, environment variable name | Correct the key/path or report the missing runtime value; `++` accepting a key does not prove it is consumed |
| Missing target | Selected target/task registry, structure path, chains and selectors | Supply the actual registered input or report what is missing; do not substitute a different target |
| Checkpoint shape/key mismatch | Checkpoint pair, LoRA settings, architecture toggle | Restore the selected pipeline's matching settings; do not bypass incompatible weights |
| AF2 or RF3 unavailable | Both search reward and final backend dependencies | Correct the requested backend's installation/path when authorized; otherwise report a launch blocker |
| CUDA OOM | Failing worker/stage, sequence/target length, batching, concurrent GPU use | Adjust batching where possible; preserve requested branch/step/redesign budgets |
| Zero selected candidates or surprising ranks | Reward sign/normalization, missing values, dedup order, conditional cutoff in `filter.py` | Calculate the actual selection; keep any intended-policy selection separate and preserve originals |
| Refinement pairs missing or unchanged | Generation records before filtering, sample types, lineage, refinement logs | Report attrition and failures; a `final` label alone does not prove refinement succeeded |
| No passing designs | Recorded thresholds, units, same-sequence metrics, missing data | Report the result under the requested criteria; do not relax thresholds to create successes |
| Missing diversity result | Successful structures, cluster assignments, tool paths and logs | Report unmeasured diversity or rerun the requested analysis when inputs/runtime are available |

## Keep evidence proportional to the task

During an offline review, a missing package or GPU does not block writing a valid
configuration, calculation, or launch plan. Mark unavailable runtime checks as
unperformed. During execution, preserve partial outputs and explain which stage
blocked completion; a launch command or manifest is not a success record.

For AME/RF3 geometry problems, inspect ligand atom selection, chain/residue mapping,
and the actual refolder input/output before interpreting ligand or motif RMSD.
Do not rewrite the user's structure merely to match an assumed identifier.
For all metrics, use the schema and units of the actual export rather than an
unrelated example CSV.
