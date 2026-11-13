# Explicit parameter sweeps

Use this reference only when the user requests multiple parameter combinations.
A single-campaign review does not require cluster setup or sweep generation.
The project provides `script_utils/generate_inference_configs.py` and SLURM
launchers; inspect their arguments in the supplied revision before using them.

## Prepare a bounded comparison

A sweeper YAML maps dotted configuration keys to lists of values. Multiple axes
form a Cartesian product. Scalar `--override KEY=VALUE` arguments pin values and
override the corresponding sweep axis. For example, a sweep of widths needs the
beam-search algorithm explicitly selected:

```yaml
generation.search.beam_search.beam_width: [2, 6]
```

On a prepared project installation, preview configuration generation with:

```bash
python script_utils/generate_inference_configs.py \
    --config_name search_binder_pipeline \
    --sweeper configs/sweeps/beam_width.yaml \
    --override generation.search.algorithm=beam-search generation.task_name=02_PDL1 \
    --dryrun
```

Use the actual reviewed sweeper path. A preview is not a submitted or completed
campaign. For an offline plan, write the sweep/configuration artifacts and derive
the combination count without importing the inference stack. Do not assume the
local `complexa design` command accepts the SLURM launcher's `--sweeper` flag.

Count total combinations and budget candidate expansion for each arm. Couple any
`nsteps` change with an ending checkpoint schedule; a Cartesian product of steps
and schedules can create invalid combinations. Keep scientific criteria, target
inputs, evaluation protocol, and seed policy comparable. Record each run's exact
settings and completed counts; equal input counts do not imply equal compute.

Cluster launchers can synchronize code and submit remote jobs. Use them only as
part of an authorized cluster run, with actual destination/allocation settings
and distinct output names. A sweep plan alone does not authorize submission.
