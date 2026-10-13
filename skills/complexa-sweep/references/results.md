# Interpreting measured Complexa results

Use this reference after evaluation or when reviewing supplied CSVs. Preserve
the requested result type, sequence types, and saved success criteria. A static
config review cannot establish pass rate, diversity, or experimental binding.

## Locate and reconcile artifacts

Read the output paths from the CLI log; the usual root is
`evaluation_results/{run_name}`. Combined raw CSVs contain per-design metrics.
Analysis writes `res_nsamples.csv`, `res_filter_binder_pass_*.csv`,
`res_filter_ligand_pass_*.csv`, or `res_filter_motif_binder_pass_*.csv` and
`success_criteria_*.json`. Analysis subdirectories may hold these files, so use
the actual printed paths rather than assuming everything is at the root.

Identify records by `id_gen`, task, and sequence type. A design may have several
redesigns and metric rows; row count is not necessarily unique design count.
Distinguish requested, generated, retained, evaluated, and passing counts. Report
failed/missing evaluations and the denominator used for each pass rate.

## Apply the correct metric convention

Binder columns usually use a sequence prefix (`self`, `mpnn`, `mpnn_fixed`) and
a component (`complex`, `binder`, `ligand`). Read actual headers before choosing
columns. Values can be lists over redesigns; parse serialized lists with a data
parser such as `ast.literal_eval`, never executable `eval`.

The released binder analysis thresholds are:

| Result type | Joint criteria for a single redesign |
|---|---|
| Protein binder | `complex_i_pAE * 31 <= 7`, `complex_pLDDT >= 0.9`, `binder_scRMSD_ca < 1.5` |
| Ligand binder | `complex_min_ipAE * 31 < 2`, `binder_scRMSD_ca < 2`, `ligand_scRMSD_aligned_allatom < 5` |
| Motif protein binder | `complex_i_pAE * 31 <= 7`, `complex_pLDDT >= 0.8`, `binder_scRMSD_ca < 2`, motif RMSD `< 2`, motif sequence recovery `>= 1` |
| Motif ligand binder (AME) | `binder_scRMSD_bb3 <= 2`, motif RMSD `<= 1.5`, motif sequence recovery `>= 1`, ligand clashes `< 0.5` |

RMSD uses angstroms. These PAE thresholds assume the normalized Complexa CSV
representation; externally supplied PAE in angstroms must not be scaled again.
Likewise, distinguish pLDDT on a 0-1 scale from a 0-100 scale. Inspect backend,
column naming, and saved settings before comparing across experiments.

A design passes when at least one evaluated redesign satisfies every criterion
jointly. Combining one redesign's good interface with another's good motif is
incorrect. Motif column names depend on atom selection (`_ca`, `_all`, etc.);
use the effective `aggregation.motif_binder_success_thresholds`. With
`atom_selection_mode: tip_atoms`, CA motif metrics may be filled with zero, so
they are not independent evidence of accurate tip-atom geometry.

For monomer components, designability measures inverse-folded sequence refolds;
codesignability measures the original sequence refold. Their usual scRMSD
threshold is 2 angstroms. Motif-only evaluation also requires motif-specific
sequence recovery and RMSD criteria; do not apply binder thresholds to it.
User-specified/saved thresholds take precedence over these released defaults.

## Report diversity and compare campaigns

`res_div_foldseek_{mode}_*.csv` reports structural clustering;
`res_div_mmseqs_*.csv` reports sequence clustering. State the mode (binder,
complex, interface, or monomer), sequence type, thresholds, and subset (all or
successful samples). FoldSeek and MMseqs2 must actually run to claim their
diversity results. A count of unique sequences is a different statistic.

Rank only comparable measured rows under the requested objective. Keep the
original success definition fixed across configurations and report missing
values separately. Retain ties on a Pareto frontier: one point dominates
another only if it is no worse on every objective and strictly better on at
least one. Record objective directions and runtime provenance.

Include the source CSV paths, unique-design denominator, passing count,
criteria path, and unavailable metrics in the final summary. For an unfamiliar
schema, inspect the selected analysis config and its result-type implementation
in the supplied source checkout before interpreting columns.
