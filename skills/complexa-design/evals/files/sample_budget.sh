#!/usr/bin/env bash
# Synthetic command proposal for review; not a completed campaign.
complexa design configs/search_binder_local_pipeline.yaml \
  ++run_name=pdl1_budget ++generation.task_name=02_PDL1 \
  ++gen_njobs=2 ++eval_njobs=1 \
  ++generation.dataloader.batch_size=4 \
  ++generation.dataloader.dataset.nres.nsamples=60 \
  ++generation.dataloader.dataset.nrepeat_per_sample=3 \
  ++generation.search.beam_search.beam_width=8 \
  ++generation.filter.filter_samples_limit=60 \
  ++metric.binder_folding_method=colabdesign
