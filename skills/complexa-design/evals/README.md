# Complexa design evaluation coverage

The existing four cases remain unchanged: three hardware-dependent campaign or
configuration tasks and one unrelated-request control. The original GPU campaign
suite remains in `gpu-integration.json`. Five additional cases exercise design
decisions and result interpretation without requiring model installation or GPU
inference. They are ordinary offline review requests, independent of hardware
availability, not successful substitutes for the GPU cases.

## Research basis

The method paper, [Scaling Atomistic Protein Binder Design with Generative
Pretraining and Test-Time Compute](https://arxiv.org/html/2603.27950v1), motivates
search-budget accounting, composite interface rewards, Generate & Hallucinate,
and distinguishing co-generated from redesigned successes. Concrete keys,
operators, and implementation behavior come from
[the pinned source revision](https://github.com/NVIDIA-BioNeMo/Proteina-Complexa/tree/8fc6f5c85b38a2585ffaac555e708576dc4e8533),
not assumptions that every paper experiment is available through every released
checkpoint.

| Case | User decision | Paper motivation | Implementation evidence |
| --- | --- | --- | --- |
| 005 | Repair a shortened beam schedule and budget saved candidates | H.2: beam search and retained lookaheads | `BeamSearch.search`, dataset length, generation config |
| 006 | Combine interface confidence and H-bond counts on the requested geometry | 3.3 and I.8: interface H-bond optimization; I.1.1: separate folding checks | Composite reward routing, TMOL constructor/scoring, protein evaluation config |
| 007 | Plan a paired Generate & Hallucinate comparison | H.5 and I.3: refinement stages | Refinement factory, pre-refinement copies, failure handling, evaluation sequence types |
| 008 | Audit ligand reward units and pilot selection | 3.3 and I.7: ligand metrics and search | RF3 normalization, explicit reward coefficients, filter ordering and cutoff guard |
| 009 | Separate self success, redesign rescue, and successful structural diversity | 3.3 and I.5: co-design versus sequence redesign | Default threshold operators, per-sequence conjunction, per-design aggregation |

Case 008 tests behavior found in the implementation, not a claim made in the
paper. Case 009 deliberately follows implementation defaults: its inclusive
protein ipAE/pLDDT boundaries differ from the strict wording in the paper.
The reference documents that distinction. The suite does not assert that a
configuration or synthetic calculation reproduces the paper's scientific results.

Fold-class conditioning is a possible future case once released-checkpoint
compatibility and a concrete user workflow can be supplied. Do not invent a
supported conditioning switch from a paper figure alone.

## Fixture and grading contract

`files/design_source/source_manifest.json` records exact source paths, line ranges,
hashes, and commit-pinned links for the shared reading snapshot. The YAML files are
unchanged upstream copies. Python excerpts retain their original indentation and
are saved as text; the snapshot is intentionally not an importable installation.
Case-specific drafts and tables are explicitly synthetic. The table schemas and
units are supplied with the inputs, including frozen cluster assignments for the
reporting task.

Both evaluation arms receive the same prompts and raw inputs. The new prompts
exclude evaluation definitions and prior benchmark reports from the task. Expected
outputs and assertions stay in `evals.json`, not in the raw input directories or
runtime guidance. The runtime reference contains reusable implementation facts,
not case IDs or case-specific answer tables.

Grade the saved artifact contents and the stated interpretation. Merely mentioning
a feature, selecting the skill, or reporting a plausible scientific result does
not satisfy a case. The prompts request artifact readback so the evaluator can
observe the actual configuration and calculated outputs. Accept equivalent YAML
overlays and truthful limitations; do not require exact prose or an unrequested
GPU launch. These cases do not weaken the original execution or coverage gates.

The skill's runtime guidance now routes advanced requests to
`references/search_and_analysis.md`, clarifies default protein sequence evaluation,
and replaces automatic threshold-loosening advice with an audit of units and
recorded criteria. Existing signed benchmark files describe an older revision;
only a new live NV-CARPS evaluation can establish the revised skill's quality.

## Local verification

From the repository root, with numpy, pandas, and PyYAML available:

```bash
python -m unittest discover -s skills/complexa-design/evals/tests -v
skillevaluator validate skills/complexa-design --profile external \
  --catalog-path . --checks schema --no-dedup
```

The tests verify source fidelity, preservation of the original cases, fixture
paths, actual production filter behavior, composite structure routing, and the
success-count oracle using production threshold functions. Model execution is
stubbed only for the reward routing test; no folding accuracy is tested.

Independent local agent trials use isolated copies containing only the prompts,
raw inputs, and (for the skill arm) runtime instructions, references, and helpers.
They exclude eval definitions, tests, and benchmark reports. These are behavioral
checks, not the two-agent NV-CARPS score or evidence of positive skill lift.
On 2026-10-22, both local arms produced correct artifacts for all five new cases
under semantic review. This validates task feasibility and the answer expectations;
it does **not** demonstrate that these cases lower the baseline ceiling. The cases
add domain-specific regression coverage, while the reference fixes substantive
guidance gaps.

Re-run the full live evaluation to compare with-skill and baseline outcomes; a
strong baseline is an informative result, not a reason to withhold source evidence
or change the expected scientific answer.
