#!/usr/bin/env bash
# Synthetic command proposal for review; not a completed campaign.
# Proposed future host: Complexa and ESMFold weights present, AF2 weights absent.
complexa design configs/search_binder_local_pipeline.yaml \
  ++run_name=pdl1_esm_review ++generation.task_name=02_PDL1 \
  ++generation.search.algorithm=beam-search \
  ++generation.search.beam_search.beam_width=8 \
  ++generation.dataloader.dataset.nres.nsamples=24 \
  ++generation.dataloader.dataset.nrepeat_per_sample=1 \
  ++metric.binder_folding_method=esmfold
