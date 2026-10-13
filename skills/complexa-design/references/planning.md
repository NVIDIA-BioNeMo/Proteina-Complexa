# Offline campaign preparation

Run `python3 scripts/prepare_campaign.py --help` from this skill directory.
The helper requires PyYAML and a supplied Complexa config tree or partial source
snapshot. It does not install packages, probe GPUs, resolve interpolations, or
execute the CLI. If Python/PyYAML is unavailable and installation is outside the
request, review the YAML directly.

Required options are `--project-root`, `--pipeline` (`binder`, `ligand_binder`,
or `ame`), `--target`, `--run-name`, and `--out-dir`. The output directory must
be new so a previous plan or campaign is never overwritten. Add `--revision`
when iterating: if that path already exists, the helper creates a new sibling
directory and returns its actual path in `output_dir`. Read artifacts from that
returned path. Never remove a previous plan or campaign to make a retry succeed.

| Option | Meaning |
|---|---|
| `--revision` | Preserve an existing output path and create a fresh sibling for this plan. |
| `--samples N --repeats R` | Exact global base budget; N must be divisible by R. Defaults preserve source counts when omitted. |
| `--gen-jobs N --eval-jobs N` | Split generation/evaluation work; never multiply the global budget. Idle generation jobs are reported as zero. |
| `--batch-size N --filter-limit N` | Independent memory and retention controls. |
| `--search ALGORITHM --beam-width N` | Width requires explicit active beam search. |
| `--refolder colabdesign\|rf3_latest\|esmfold` | Evaluation backend; does not remove generation reward dependencies. Required when the snapshot omits evaluation defaults. |
| `--overrides FILE.yaml` | Explicit mapping merged over source defaults before command-line choices. Inconsistent checkpoint/LoRA/architecture choices fail validation. |
| `--ame-rf3-reward` | Opt in to the RF3 reward example shipped with AME when reward-guided search is requested. Preserves evaluation and success criteria. |

Output:

- `campaign_plan.json`: source digests, model contract, requested budget and
  per-job split, stage-specific dependency hints, unresolved targets, and exact
  CLI arguments. Observed counts remain null. Dependency hints are incomplete
  when nested defaults or stage files have not been inspected.
- `campaign_overrides.yaml`: explicit settings to review. This is an override
  mapping, not a standalone runnable pipeline config.
- `launch.sh`: syntax-checked command for a future prepared project root. Set
  `COMPLEXA_PROJECT_ROOT` before launching. An `UNREGISTERED_*` target requires
  `COMPLEXA_TARGET` after its structure and selections have been registered.

Exit 0 means a static plan was written, not that the target or runtime is ready.
Exit 2 reports an inconsistent/unsupported plan or a write/syntax error. Fix the
reported issue; do not retry unchanged or silently change the scientific goal.
Registered keys still require checking the actual structure and selections.
For AME the corrective patch carries the released checkpoint pair, LoRA, and
string `USE_V2_COMPLEXA_ARCH="True"`; guided search also needs an active reward.

The helper supports the released direct stage layout and UniformInt dataset.
For custom Hydra defaults, other checkpoint architectures or reward backends,
use a prepared installation to compose and validate the effective config.
Keep source analysis thresholds and refinement settings unless explicitly asked
to change them. Additional RF3, ESM, inverse-folding and analysis dependencies
must be checked from the complete installed configuration before execution.
