# Configuration composition

Use this guide to trace the effective settings for a particular project revision.
Read the selected top-level pipeline and only the stage configs involved in the
requested change. Full training configuration and unrelated pipelines are outside
a design review.

## Namespaces and precedence

A local pipeline composes a `*_generate.yaml` file at `@generation`, and
`*_evaluate.yaml` / `*_analyze.yaml` files at `@_global_`, followed by `_self_`.
Thus `search.algorithm` inside the generation file becomes
`generation.search.algorithm`; evaluation's `metric` stays `metric`, not
`evaluation.metric`. Top-level pipeline values override earlier composed defaults;
command-line Hydra overrides take precedence over those values.

Use `++key=value` for pipeline command-line overrides, quoting the entire argument
when it contains brackets, spaces, or shell comparison characters. The CLI forwards
overrides to all stages. Forced additions can admit unused or misspelled keys;
acceptance by Hydra is not proof that the implementation reads the key.

For a requested nested YAML patch, retain that structure instead of writing dotted
keys as literal YAML keys. For example:

```yaml
generation:
  search:
    algorithm: beam-search
    beam_search:
      beam_width: 6
metric:
  sequence_types: [self]
```

This is an override fragment, not a standalone fully composed pipeline. Preserve
the baseline's other settings. The `complexa design` CLI takes a pipeline config
and Hydra arguments; it does not automatically merge an arbitrary second YAML
file. For an executable artifact, provide a proper composed config or translate
reviewed leaf values to supported CLI arguments.

## Follow the key to its consumer

| Decision | Configuration and implementation to inspect |
|---|---|
| Algorithm and branch schedule | Selected `*_generate.yaml`; `src/proteinfoundation/search/search_factory.py` and selected search implementation |
| Reward coefficients and folding geometry | `generation.reward_model`; `src/proteinfoundation/rewards/base_reward.py` plus the selected reward module |
| Final-only refinement and preservation | `generation.refinement`; refinement/output assembly in `src/proteinfoundation/proteina.py` |
| Deduplication, cutoff, retention/deletion | `generation.filter`; `src/proteinfoundation/filter.py` |
| Evaluation sequence types and auxiliary redesign | Selected `*_evaluate.yaml`; `src/proteinfoundation/evaluate.py` |
| Actual success defaults and operators | `src/proteinfoundation/result_analysis/binder_analysis_utils.py` or `motif_binder_analysis_utils.py`; routing in `analyze.py` |

Use implementation behavior when YAML comments disagree, and explain the
mismatch. In particular, the AME analysis comments describe older thresholds;
`run_motif_binder_analysis` obtains its defaults from the motif analysis module
when no explicit custom criteria are supplied. Do not silently copy the comments.

Environment interpolations such as `${oc.env:RF3_CKPT_PATH}` remain unresolved in
an offline review without that environment. Record required variables rather than
replacing them with invented machine paths. A supplied partial source snapshot
can establish represented key semantics without establishing runtime readiness.
