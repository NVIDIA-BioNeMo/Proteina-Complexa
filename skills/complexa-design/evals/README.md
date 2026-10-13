# Complexa design evaluations

The default `evals.json` contains seven cases. Both arms receive the same input
files, prompts, and assertions. Synthetic proposals are review inputs, never
measured campaign results.

| Cases | Task | Evidence required |
|---|---|---|
| 001–003 | Original protein, ligand, and AME requests, with hardware-dependent fallbacks | Allocation evidence, execution mode, and the artifacts for the selected branch |
| 004 | Unrelated PostgreSQL guidance | Correct routing; no Complexa commands |
| 005 | Repair a sample budget and beam-search launch command | Saved syntax-checked command, budget JSON, separate generation and retention limits |
| 006 | Review an ESMFold substitution while preserving AF2-guided generation | Configuration-specific dependency diagnosis, review JSON and remaining blocker |
| 007 | Repair an AME checkpoint/search proposal with missing scientific inputs | Parsed YAML patch, compatible model settings, active reward, unresolved target selections |

Cases 001–004 are unchanged from revision `e6d75d7`. The three new cases are
offline reviews on any host; probing hardware or provisioning a runtime is
outside their scope. They exercise configuration decisions, not successful
inference or biological quality. The separate `gpu-integration.json` still
contains the original full-campaign requests and requires a prepared GPU runner.

`files/project/SNAPSHOT.md` records the source revision of the six unmodified
configuration snapshots. `sample_budget.sh`, `refold_plan.sh`, and
`ame_proposal.yaml` are deliberately flawed synthetic proposals. They exercise
sample-count/job semantics, stage-specific dependencies, and the released AME
model/search contract. Do not execute them as launch scripts.

## Comparing revisions

1. For comparison with the October 7, 2026 four-case report, evaluate both skill
   revisions on cases 001–004 in an isolated copy. Keep the supplied fixtures
   identical and select the same hardware branch. Do not change these cases or
   weaken their assertions to increase lift.
2. For the expanded seven-case suite, establish a new paired baseline. Keep the
   model, evaluator version, runner, tool access, budgets, and prompts fixed
   across arms. Compare per-case and per-agent results, and repeat trials before
   treating small lift changes as reproducible. Report the dataset digest.
3. Inspect the actual failed assertions and traces. Track productive tool calls,
   uncached prompt plus completion tokens, and runtime alongside correctness.
   Do not infer lift by subtracting composite scores with different coverage.
4. Review security findings against the exact command and its scope. Report or
   repair a grader defect separately; a correction is not a skill improvement.
   Use the same corrected evaluator for both arms when rerunning.
5. Report offline reviews, CPU fallbacks, and completed GPU campaigns separately.
   Expanding the dataset changes the headline score's meaning. Preserve the old
   comparison and reserve additional unseen requests for checking generalization.

After live validation, regenerate benchmark reports, skill cards, and signatures
through the normal validation/signing pipeline. Local schema, YAML, and shell
checks do not establish improved agent scores.

## Deterministic artifact checks

`config.yml` selects `default_plus_custom` and declares `artifact_contract`.
`grader.py` reads saved files in `/workspace/output` after either agent arm.
It never executes a generated launch command. The contract is conjunctive:
missing/malformed artifacts or an incorrect checked setting produce zero.
Original cases retain their prompts; their custom checks cover manifest shape,
mode consistency, CPU artifact presence and shell syntax only. GPU completion,
allocation decisions and prose/scientific correctness still require ACES and
the GPU integration suite. Case 004 has no artifact obligations: it emits a
vacuous pass to satisfy the numeric reward contract and is excluded from
artifact-only summaries.

For the new cases, public prompts specify the JSON fields and literal command
format that the grader checks. The two arms use the same grader and inputs;
they need not use the planning helper. Custom results supplement ACES and do
not replace `overall`, security or the other standard metrics. Require a runner
with Python, PyYAML and Bash for both arms. Verifier files and `evals/` must be
excluded from the installed skill; current SkillEvaluator runtime staging does
this. Do not stage grading oracles as agent input.

Case 005 accepts one literal `complexa design` command, optionally preceded by
comments, strict `set` options, a `cd` to the project, and `:` readiness guards.
Line continuations and quoted literals are supported. Additional commands,
redirections, pipelines, control flow, and dynamic overrides fail the contract.
Case 006 requires JSON arrays of strings for all three dependency lists;
strings and objects with matching keys are not arrays.

## Freeze a comparison before running it

`prepare_experiment.py` creates a new directory containing immutable input copies,
source hashes, common execution configuration, commands and `experiment.json`.
Supply an instruction-only skill snapshot captured before adding the helpers:

```bash
python3 evals/prepare_experiment.py \
  --reference-skill "$INSTRUCTION_ONLY_SKILL" --out-dir "$EXPERIMENT_DIR" \
  --evaluator-version "$PINNED_EVALUATOR_VERSION" \
  --runner-image "$RUNNER_IMAGE_WITH_SHA256_DIGEST" \
  --agent-model "codex=$PINNED_CODEX_MODEL" \
  --agent-model "claude-code=$PINNED_CLAUDE_MODEL" --attempts 5
```

This prepares four native paired runs: original/capability cohorts for each
variant. The logical conditions are no skill, instructions, and helpers; each
variant retains its own independent no-skill control for valid evaluator
coverage and a baseline-drift check. Seven cases, two agents, two variants,
two arms and five attempts require **280 agent executions**. Preparation does
not run them. Order is shuffled with a recorded seed, early stopping is off,
and agent models, CPU/memory/storage, runtime image, grading and fixtures match.

The manifest calculates the total from these four runs and records each run's
case count, conditions, and execution count:

| Cohort | Variant | Cases | Arms | Attempts | Agents | Executions |
|---|---|---:|---:|---:|---:|---:|
| Original | Instructions | 4 | 2 | 5 | 2 | 80 |
| Original | Helpers | 4 | 2 | 5 | 2 | 80 |
| Capability | Instructions | 3 | 2 | 5 | 2 | 60 |
| Capability | Helpers | 3 | 2 | 5 | 2 | 60 |

Each `tier3 evaluate` command runs with-skill and without-skill conditions by
default; neither `--skip-baseline` nor `--skip-with-skill` is supplied. Counting
only the with-skill condition would give 140 and omit the independent controls.

Install the pinned evaluator in a dedicated environment, verify its provider
access and resolved models, and preserve its dependency lock and agent CLI
versions with the results. The image must already support the chosen agents
and shared verifier dependencies; pinning an image alone does not freeze
packages that a harness subsequently installs. Use CPU runners for this
comparison and run GPU integration separately on prepared GPU runners.

```bash
python3 evals/prepare_experiment.py --execute-manifest "$EXPERIMENT_DIR/experiment.json"
```

Execution verifies hashes/version and runs strict Harbor contract validation
before any agent run. Missing runtime/provider access remains a blocker.
Keep every attempt and report per-case, per-agent means and uncertainty, not
only the best trial or pass@k. Track uncached prompt + completion tokens,
wall time, and tool productivity separately from the evaluator's lift basket.
Compare the original cohort to its new paired control, not directly to the
October report if the evaluator/model changed. Report the capability cohort
separately and the seven-case union with equal per-case weights. Validate any
claimed gain on additional independently authored cases kept out of tuning;
changing sample numbers in these development cases is not an unseen holdout.

Local behavioral checks (no GPU or paid agents):

```bash
uv run --no-project --with PyYAML==6.0.3 --with hydra-core==1.3.2 \
  python -m unittest discover -s skills/tests -v
```

Run that last command from the repository root. It checks real source job
splitting, Hydra argument parsing, GPU failure classification, malicious dotenv
non-execution, grader rejection cases, and experiment isolation. These checks
also run in the shared-sync CI workflow.
