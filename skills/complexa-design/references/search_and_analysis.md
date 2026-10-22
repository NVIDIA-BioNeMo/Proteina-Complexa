# Search and campaign analysis

Use this reference for search-budget reviews, reward configuration, refinement
comparisons, and campaign summaries. The implementation notes below were checked
against Proteina-Complexa revision `8fc6f5c85b38a2585ffaac555e708576dc4e8533`.
Read the corresponding files in the user's checkout when its version differs.
Configuration review does not require installing the inference stack.

## Beam search: schedule, compute, and saved candidates

Select `generation.search.algorithm=beam-search` explicitly. A beam-width override
alone leaves the default `best-of-n` algorithm selected. Set an increasing
`generation.search.step_checkpoints` schedule from zero to
`generation.args.nsteps`; `BeamSearch.search` rejects a different final checkpoint.
Changing the denoising budget without changing the schedule can prevent launch.

For one complete dataset traversal, let:

- `N = generation.dataloader.dataset.nres.nsamples * nrepeat_per_sample`;
- `W = generation.search.beam_search.beam_width`;
- `B = generation.search.beam_search.n_branch`;
- `S = len(generation.search.step_checkpoints) - 1`.

With `keep_lookahead_samples=true`, no search reward cutoff, no refinement copies,
and all generation batches completed, there are `N * W * B * S` saved lookahead
candidates and `N * W` finals, totaling `N * W * (B * S + 1)`. These are candidate
records before deduplication and filtering, not independent successful designs.
With lookahead saving disabled, only the finals are retained. Search cutoffs,
failures, and additional pre-refinement copies change the saved count.

`dataloader.batch_size` and `search.max_batch_size` govern batching and memory;
they do not set the campaign's requested sample count. The post-generation top-N
limit is a retention cap, not a promise of that many successes. Equal input counts
also do not establish equal compute between different search algorithms or
refinement settings. Record the search budget and actual completed outputs.

Source: [beam search](https://github.com/NVIDIA-BioNeMo/Proteina-Complexa/blob/8fc6f5c85b38a2585ffaac555e708576dc4e8533/src/proteinfoundation/search/beam_search.py).

## Composite rewards: sign, scale, and structure provenance

`generation.reward_model` controls search scoring;
`metric.binder_folding_method` controls subsequent evaluation. Changing the latter
does not replace the search reward model or remove its dependencies.

For protein-interface H-bond optimization alongside AF2 confidence:

- Keep the AF2 model under its configured alias, normally `af2folding`, and give
  `i_pae` a negative coefficient because lower error is better.
- Add `proteinfoundation.rewards.tmol_reward.TmolRewardModel` under a distinct
  alias. For H-bond counts use `enable_hbond=true`, `enable_elec=false`,
  `hbond_weight=1.0`, `reward_type=interaction_count`, and the requested
  `energy_threshold`. `energy_sum` instead optimizes the negative energy sum.
- Set TMOL's `structure_source` to the **reward model alias**, such as
  `af2folding`, when the requested geometry is refolded. A backend name such as
  `colabdesign` is not interchangeable with that alias.
- Set the outer `CompositeRewardModel.weights` by alias. They default to 1.0;
  positive coefficients add model rewards. Equal coefficients do not normalize
  the numerical ranges of confidence and interaction counts.

The composite scores folding models first and requests a saved PDB when a
downstream model needs it. If the expected refolded PDB is absent, the current
implementation can fall back to the generated PDB. Therefore verify the saved
structure and the downstream scoring path in actual runtime evidence before
claiming an H-bond score was measured on refolded geometry. A configuration alone
does not prove that provenance. TMOL's bundled ligand reward example is explicitly
unsupported; do not transfer this protein-interface setup to a ligand campaign.

An RF3 final evaluation can provide a separate folding check after AF2-guided
search, but the campaign still needs AF2 and TMOL for the reward and RF3 for final
evaluation. Neither reward improvement nor refolding confidence proves binding
affinity or experimental success.

Sources: [composite reward](https://github.com/NVIDIA-BioNeMo/Proteina-Complexa/blob/8fc6f5c85b38a2585ffaac555e708576dc4e8533/src/proteinfoundation/rewards/base_reward.py),
[TMOL reward](https://github.com/NVIDIA-BioNeMo/Proteina-Complexa/blob/8fc6f5c85b38a2585ffaac555e708576dc4e8533/src/proteinfoundation/rewards/tmol_reward.py).

## Generate then refine: preserve a valid paired comparison

The implemented AF2 sequence-refinement algorithm is
`generation.refinement.algorithm=sequence_hallucination`. For greedy-only
refinement, disable `enable_soft_optimization`, enable `enable_greedy_optimization`,
and set `n_greedy_iters` and `n_recycles` explicitly. This is distinct from
post-generation MPNN redesign. The method paper's main Generate & Hallucinate
setting uses 15 greedy iterations and three recycles.

`refine_targets=final` leaves lookaheads unchanged. `save_pre_refinement=final`
saves the original finals as `sample_type=final_unrefined` alongside the refined
finals. Use run, batch/sample lineage, and metadata tags to pair them; sequence
identity is not a reliable pairing key after refinement. Refinement errors can
return the original sample, so retain logs and label unchanged/failed refinements.

Archive generated originals, refined outputs, rewards, and metadata **before**
deduplication or top-N filtering. Those steps can discard one member of a pair;
`delete_non_top_n_samples=false` preserves displaced directories but does not make
the selected result table a complete paired dataset. Report pairing attrition
and use matched pairs for a before/after comparison.

Evaluate `metric.sequence_types=[self]` to score the resulting sequences without
another binder redesign. If the request excludes all additional MPNN work, also
disable the separate monomer `metric.compute_designability` calculation. Keep
the same evaluation backend and success criteria across comparison arms.

Source: [refinement and output assembly](https://github.com/NVIDIA-BioNeMo/Proteina-Complexa/blob/8fc6f5c85b38a2585ffaac555e708576dc4e8533/src/proteinfoundation/proteina.py).

## Ligand rewards and post-generation filtering

The released ligand configuration explicitly weights RF3 `min_ipAE` by -1.0,
sets other reward coefficients to zero, and enables `normalize_pae`. With outer
weight 1.0, `total_reward = -raw_min_ipAE / 31`; larger is better. Translate a
requested raw error ceiling into this reward's units before choosing a cutoff.
Do not compare normalized, negative rewards directly with positive Angstroms.
Other weights or normalization settings require deriving the formula again.

At the pinned revision, the post-generation filter:

1. Drops rows with missing `total_reward`.
2. When `dedup_sequence=true`, keeps the first row per `aatype` **before** sorting;
   this need not be the highest-scoring duplicate.
3. Sorts rewards descending. It applies the inclusive `>= reward_threshold`
   cutoff and top-N truncation **only when the post-dedup row count exceeds the
   cap**. At or below the cap, the cutoff is skipped.

For a small pilot, audit the resulting selection explicitly. If the requested
policy is an unconditional cutoff with best-scoring sequence deduplication,
compute and save that reviewed selection separately; a threshold-only override
does not implement it in this revision. Avoid deleting source candidates during
review. The search-time cutoff is a different setting: it applies to lookaheads
with a strict `>` comparison, not to every final output.

Passing a search/filter reward cutoff is not passing ligand evaluation: the
default ligand success criteria additionally constrain binder and ligand RMSDs.

Sources: [RF3 scoring](https://github.com/NVIDIA-BioNeMo/Proteina-Complexa/blob/8fc6f5c85b38a2585ffaac555e708576dc4e8533/src/proteinfoundation/rewards/rf3_reward.py),
[post-generation filter](https://github.com/NVIDIA-BioNeMo/Proteina-Complexa/blob/8fc6f5c85b38a2585ffaac555e708576dc4e8533/src/proteinfoundation/filter.py).

## Success and diversity: preserve units and denominators

Use the resolved run criteria, not an assumed threshold from prose. At the pinned
revision, protein defaults require all three criteria for the **same sequence**:
normalized complex `i_pAE * 31 <= 7`, complex `pLDDT >= 0.9`, and binder
`scRMSD_ca < 1.5`. Missing or non-finite values do not pass. The method paper uses
strict ipAE/pLDDT wording; state whether the report follows the paper or the
implementation, especially for boundary values.

Ligand defaults require normalized complex `min_ipAE * 31 < 2`, binder
`scRMSD_ca < 2`, and ligand `scRMSD_aligned_allatom < 5`. Do not replace these with
the protein thresholds or a reward-only gate.

Report `self`, `mpnn`, and `mpnn_fixed` separately. A design gains passing coverage
through redesign when its self sequence does not pass the recorded criteria and
at least one individual redesign passes **all** criteria. Report missing self
metrics separately: added coverage is not evidence that an unmeasured original
sequence actually failed. Never combine the best metric from different redesigns
into a fictitious passing sequence. Distinguish passing sequence attempts from
base designs with any passing sequence; state denominators and evaluation/filter
attrition.

Count distinct Foldseek clusters among the successful structures for structural
diversity, using the recorded clustering settings. Do not count failed clusters,
PDB files, or unique sequences as successful structural clusters. If assignments
or structures are absent, report that diversity is unmeasured. Label synthetic
tables as examples rather than measured campaigns.

Sources: [success criteria and redesign checks](https://github.com/NVIDIA-BioNeMo/Proteina-Complexa/blob/8fc6f5c85b38a2585ffaac555e708576dc4e8533/src/proteinfoundation/result_analysis/binder_analysis_utils.py),
[method paper](https://arxiv.org/html/2603.27950v1), sections 3.3, H.2, H.5, I.5, and I.8.
