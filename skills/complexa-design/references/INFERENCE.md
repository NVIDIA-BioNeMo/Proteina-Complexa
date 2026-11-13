# CLI execution and validation

Commands below refer to the prepared inference project. Set the working directory
to that project so `.env`, `ckpts`, relative configs, and output roots resolve
consistently. Keep installed skill helpers in their own location.

## Prepare and validate

Select the reviewed pipeline and inspect target existence, checkpoint pair,
architecture/adapters, and both search and evaluation dependencies. The built-in
readiness check accepts a config path:

```bash
complexa validate design configs/search_binder_local_pipeline.yaml
```

At revision `8fc6f5c85b38a2585ffaac555e708576dc4e8533`, `validate` has no positional
Hydra-overrides argument. Appending `++generation.task_name=...` is rejected by
its argument parser. It also uses lightweight YAML/path checks, not complete Hydra
composition and semantic validation. Review launch overrides separately against
their consuming code and target dictionary. A prepared concrete config improves
path checking but still cannot establish full readiness: folding detection checks
`compute_binder_metrics`, whereas AME enables `compute_motif_binder_metrics`, so
its RF3 requirements can be missed. Verify selected backend dependencies directly.
Do not claim that validation of an unchanged baseline checked later CLI overrides.
Warnings may be nonblocking; inspect their relevance to the requested stages.

For review-only work, parse saved YAML and check `bash -n` on a launch script
without importing the inference stack. Label those as static checks. A missing
runtime is not a reason to provision one during an offline review.

## Launch, follow, and recover

The full CLI runs `generate → filter → evaluate → analyze`, with stage logs and
parallel-job routing. For example, after successful readiness review:

```bash
complexa design configs/search_ligand_binder_local_pipeline.yaml \
    ++run_name=ligand_pilot ++generation.task_name=39_7V11_LIGAND
```

Use the matching AME or protein pipeline for those tasks. `--verbose` sends stage
output to the terminal. Track the launched process, inspect exit codes/logs, and
report complete, partial, running, or blocked status from evidence. Stop retries
when no configuration/environment change addresses the observed failure.

For an explicitly requested stage rerun, the CLI also exposes `complexa generate`,
`complexa filter`, `complexa evaluate`, and `complexa analyze`, each with the
pipeline path and reviewed overrides. Recover only the failed/incomplete stage
when its inputs are intact; inspect existing outputs and log paths before any
rerun that could replace them. Preserve the run name, target, source revision,
sequence lineage, and criteria needed to associate results with generation.

If debugging bypasses the CLI and invokes a `proteinfoundation` module directly,
reproduce the CLI's config composition, environment injection, job IDs, and output
routing. In particular, AME's architecture toggle must reach the subprocess.
A future launch script should record these requirements, not claim they were run.

Sources: [argument parser and stage runner](https://github.com/NVIDIA-BioNeMo/Proteina-Complexa/blob/8fc6f5c85b38a2585ffaac555e708576dc4e8533/src/proteinfoundation/cli/cli_runner.py),
[readiness validator](https://github.com/NVIDIA-BioNeMo/Proteina-Complexa/blob/8fc6f5c85b38a2585ffaac555e708576dc4e8533/src/proteinfoundation/cli/validate.py).
