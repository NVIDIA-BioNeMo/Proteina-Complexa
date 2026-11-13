# Evaluation outputs and interpretation

Use the run's resolved criteria and source revision. The implementation defaults
below were checked at `8fc6f5c85b38a2585ffaac555e708576dc4e8533`; they are in-silico
selection criteria, not measured affinity or experimental binding evidence.

## Identify the records and criteria

Start with paths reported by the CLI and analysis logs, rather than guessing an
output directory. `analyze.py` combines per-job evaluation CSVs into
`RAW_{result_type}_results_{config_name}_combined.csv`. Relevant outputs include
`overall_results_*.csv`, `res_filter_*_pass_*.csv`, `res_div_foldseek_*.csv`, and
`res_div_mmseqs_*.csv`. The analysis organizer can move these into subdirectories
such as `filter_results/`, `diversity/`, and `motif_binder_metrics/`; search within
the actual result directory. Inspect saved success-criteria JSON when present.
Missing files or metrics mean that component has not been established.

Identify whether a table has one row per evaluated sequence or per base design
with list-valued redesign metrics. Align list values by the same redesign index.
Distinguish complex `i_pAE`/`min_ipAE`, complex `pLDDT`, binder self-consistency RMSD,
and ligand RMSD. Confirm normalization from the export/backend: a normalized PAE
is multiplied by 31 for Angstrom thresholds; normalized pLDDT uses a 0–1 scale.
Do not apply the scale again to a table already in Angstroms or assume pLDDT is
always exported on the same scale.

| Result type | Default criteria, all for the same sequence |
|---|---|
| `protein_binder` | `complex_i_pAE * 31 <= 7`; `complex_pLDDT >= 0.9`; `binder_scRMSD_ca < 1.5` |
| `ligand_binder` | `complex_min_ipAE * 31 < 2`; `binder_scRMSD_ca < 2`; `ligand_scRMSD_aligned_allatom < 5` |
| `motif_protein_binder` | `complex_i_pAE * 31 <= 7`; `complex_pLDDT >= 0.8`; `binder_scRMSD_ca < 2`; motif RMSD `< 2`; correct motif sequence `>= 1` |
| `motif_ligand_binder` (AME) | `binder_scRMSD_bb3 <= 2`; motif RMSD `<= 1.5`; correct motif sequence `>= 1`; ligand-clash indicator `< 0.5` |

RMSDs are in Angstroms. Motif criteria resolve the sequence-specific columns
`{seq_type}_motif_rmsd_pred_all`, `{seq_type}_correct_motif_sequence_all`, and,
for AME, `{seq_type}_has_ligand_clashes_all`. Missing or non-finite values do not
pass. Preserve inclusive versus strict operators at boundaries. The protein
paper's strict ipAE/pLDDT wording differs from implementation boundaries; state
which criteria were applied.

AME's analysis YAML comments describe older ipAE/pLDDT/sequence-recovery criteria.
The actual `run_motif_binder_analysis` default comes from
`get_default_motif_binder_success`, whose AME criteria are shown above. Custom
`aggregation.motif_binder_success_thresholds` uses nested `binder` and `motif`
sections, rather than the older flat example in those comments. Explicit custom
criteria in a completed run take precedence; report their provenance.

## Count successes, coverage, and diversity

Report `self`, `mpnn`, and `mpnn_fixed` separately. `self` scores the generated
sequence; post-generation MPNN sequences are distinct attempts. Auxiliary monomer
designability can also run inverse folding independently of binder sequence types.
For a request excluding all additional redesign, inspect
`metric.compute_designability` as well as `metric.sequence_types`.

Compute and retain passing IDs for these distinct quantities:

- Generated-sequence successes / eligible base designs.
- Passing redesign sequence attempts / evaluated redesign attempts.
- Base designs with any passing redesign / eligible base designs.
- Added coverage: designs with a passing redesign but no passing self result.
- Overall coverage: the union of self-passing and redesign-passing base designs.

A passing redesign must satisfy every criterion itself. Never combine the best
metric from several failing redesigns into a fictitious passing sequence. Missing
self metrics can yield added passing coverage, but do not prove the original
sequence failed. Report missing data and generation/filter/evaluation attrition
separately, and state whether the denominator covers generated or evaluated designs.
Do not add sequence counts to base-design counts or double-count their union.

For structural diversity, count distinct Foldseek clusters within the successful
subset. Use the supplied frozen assignments/settings if present; do not imply a
new clustering run. Sequence diversity (MMseqs2), PDB counts, and successful
structural clusters are different quantities. Failed structures do not inflate
the successful cluster count. If assignments or required structures are absent,
report diversity as unmeasured. Label synthetic records as synthetic calculations.

Sources: [binder criteria](https://github.com/NVIDIA-BioNeMo/Proteina-Complexa/blob/8fc6f5c85b38a2585ffaac555e708576dc4e8533/src/proteinfoundation/result_analysis/binder_analysis_utils.py),
[motif criteria](https://github.com/NVIDIA-BioNeMo/Proteina-Complexa/blob/8fc6f5c85b38a2585ffaac555e708576dc4e8533/src/proteinfoundation/result_analysis/motif_binder_analysis_utils.py),
[analysis routing and output assembly](https://github.com/NVIDIA-BioNeMo/Proteina-Complexa/blob/8fc6f5c85b38a2585ffaac555e708576dc4e8533/src/proteinfoundation/analyze.py).
