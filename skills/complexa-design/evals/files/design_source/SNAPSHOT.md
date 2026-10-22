# Offline source snapshot

These are unchanged configuration files and exact Python excerpts from
NVIDIA-BioNeMo/Proteina-Complexa revision
`8fc6f5c85b38a2585ffaac555e708576dc4e8533`.
`source_manifest.json` records original paths, line ranges, source hashes, excerpt
hashes, and commit-pinned URLs. Python excerpts retain their original indentation
and use `.py.txt` because this is a reading snapshot, not an importable package.

Available material:

| Files | Source area |
| --- | --- |
| `configs/` | Protein/ligand pipeline, generation, sampling, and protein evaluation configuration |
| `beam_search.py.txt`, `dataset_length.py.txt` | Beam-search implementation and dataset length |
| `composite_reward.py.txt`, `tmol_init.py.txt`, `tmol_score.py.txt` | Composite reward routing and TMOL configuration/scoring |
| `rf3_score.py.txt` | RF3 reward calculation |
| `search_factory.py.txt`, `apply_refinement.py.txt`, `append_unrefined.py.txt`, `sequence_hallucination.py.txt` | Refinement construction, execution, and output assembly |
| `filter.py.txt` | Post-generation selection |
| `binder_analysis_utils.py.txt`, `evaluate_threshold.py.txt` | Success criteria and per-sequence/design checks |

This partial snapshot does not include a runnable CLI, target structures, model
weights, or a GPU runtime. Draft overrides in sibling task directories are
synthetic user inputs for review; they are not upstream configuration defaults.
Synthetic CSVs are not experimental or inference results, and their PDB paths
are labels rather than existing structures.
