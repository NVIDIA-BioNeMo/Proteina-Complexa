# Runtime resources and dependencies

Use this reference for execution readiness or an explicitly requested resource
review. Configuration-only reviews need neither GPU probes nor model downloads.

## Assess the selected workload

The local pipelines default to one generation worker, one evaluation worker,
24 CPU threads, and a generation batch size of 16. These are defaults, not tested
minimum resources. Model length, target size, reward/refolder, search expansion,
batching, and concurrent workers determine memory and time. Do not promise that
a particular batch size fits a GPU or that doubling workers halves runtime.

Each generation/evaluation worker uses a GPU; workers do not shard one design
across devices. Verify allocation and device access before increasing worker
counts. On memory failure, inspect the failing stage and concurrent processes,
then reduce its batching if compatible with the request. Reducing branch count,
steps, or redesign attempts changes the scientific/compute budget; do not make
those changes silently. Disk retention settings do not reliably fix GPU OOM.

`preflight.sh` records available devices, paths, and checkpoint fingerprints. Its
`gpu.available=false` can also mean `nvidia-smi` failed or was absent. Distinguish
confirmed absence, inaccessible allocated hardware, and an undetermined probe.
In containers, host driver/module information alone does not prove this task has
a GPU allocation. Reuse readiness evidence unless the environment changed.

## Check both search and evaluation dependencies

| Selected component | Check before execution |
|---|---|
| Generator | Matching model and autoencoder checkpoints; pipeline LoRA/architecture settings |
| AF2 reward or ColabDesign refolding/refinement | AF2/JAX dependencies and `AF2_DIR` contents |
| RF3 reward or refolding | RF3 executable/environment at `RF3_EXEC_PATH` and weights at `RF3_CKPT_PATH` |
| TMOL reward/interface metrics | TMOL dependencies and supported structure/interaction type |
| MPNN or monomer metrics | Selected inverse-folding and folding models, their dependencies and weights |
| ESM metrics | Selected ESM packages/weights/cache |
| Structural/sequence clustering | Configured Foldseek/MMseqs executables and needed structures/sequences |
| Optional interface geometry tools | The tools selected by the actual metric configuration |

Changing final refolding does not remove a search reward's dependencies. Verify
executable usability and weight contents where required; existence flags alone
are insufficient. Record unresolved requirements in a launch plan. Install or
download only when runtime provisioning is part of the authorized task.
