# Common pipeline overrides

These keys apply to `complexa design PIPELINE` and the individual stage commands.
They are not arguments to `complexa validate`. Check the selected revision's
composed configuration and key consumer before adding an override. An accepted
forced Hydra key can still be unused by the implementation.

## Generation and search

| Key | Purpose and constraint |
|---|---|
| `run_name` | Run/output identifier; preserve it across stages |
| `generation.task_name` | Existing entry in the selected target/task dictionary |
| `generation.dataloader.dataset.nres.nsamples` | Base sample count; account for `generation.dataloader.nrepeat_per_sample` |
| `generation.dataloader.batch_size` | Dataset batching and memory; not the number of designs |
| `generation.search.max_batch_size` | Search batching; not a scientific selection threshold |
| `generation.search.algorithm` | `single-pass`, `best-of-n`, `beam-search`, `fk-steering`, or `mcts` |
| `generation.search.best_of_n.replicas` | Replicas for best-of-n |
| `generation.search.beam_search.beam_width`, `.n_branch` | Retained beams and branches; require beam-search to be selected |
| `generation.search.fk_steering.beam_width`, `.n_branch`, `.temperature` | FK population, branching, and selection temperature |
| `generation.search.mcts.n_simulations` | MCTS simulations |
| `generation.args.nsteps` | Denoising endpoint; keep `generation.search.step_checkpoints` consistent |
| `generation.filter.filter_samples_limit` | Post-generation retention cap, not a generation request |
| `generation.filter.reward_threshold` | Cutoff in total-reward units; inspect its conditional application in `filter.py` |
| `generation.filter.delete_non_top_n_samples` | Whether displaced outputs are deleted; preserve originals for comparisons |
| `generation.refinement.algorithm` | `null` or implemented `sequence_hallucination` |

Supply full paths on the command line; abbreviated `.n_branch` above shares the
preceding table cell's prefix. For example:

```bash
complexa design configs/search_binder_local_pipeline.yaml \
    ++run_name=beam_pilot ++generation.task_name=02_PDL1 \
    ++generation.search.algorithm=beam-search \
    ++generation.search.beam_search.beam_width=6 \
    ++generation.args.nsteps=300 \
    '++generation.search.step_checkpoints=[0,100,200,300]'
```

## Evaluation and analysis

| Key | Purpose and constraint |
|---|---|
| `metric.binder_folding_method` | Final evaluation backend; does not change `generation.reward_model` |
| `metric.sequence_types` | Evaluated sequence types; `[self]` excludes binder MPNN redesign |
| `metric.num_redesign_seqs` | Number of redesigns when that sequence type is enabled |
| `metric.compute_monomer_metrics` | Enable/disable the separate monomer metric suite |
| `metric.compute_designability` | Auxiliary inverse-folding/designability work within that suite |
| `metric.keep_folding_outputs` | Retain refolded structure files for inspection; not a GPU-memory guarantee |
| `aggregation.success_thresholds` | Binder criteria with `threshold`, `op`, `scale`, and `column_prefix` |
| `aggregation.motif_binder_success_thresholds` | Motif criteria with joint `binder` and `motif` sections |
| `gen_njobs`, `eval_njobs` | Independent stage workers; check available GPU allocation and job partitioning |

Preserve the user's backend, budget, and scientific criteria. Any exploratory
threshold change should produce a separate, labeled analysis. Search rewards,
post-generation reward selection, and final scientific success gates are separate
settings and may use different units and comparison operators.
