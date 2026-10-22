# Pipeline defaults

These defaults were checked against Proteina-Complexa revision
`8fc6f5c85b38a2585ffaac555e708576dc4e8533`. Inspect the supplied revision when it
differs. Pipeline paths below are relative to the inference project, not this skill.

## Select the matching configuration

| Setting | Protein binder | Ligand binder | AME motif + ligand |
|---|---|---|---|
| Pipeline under `configs/` | `search_binder_local_pipeline.yaml` | `search_ligand_binder_local_pipeline.yaml` | `search_ame_local_pipeline.yaml` |
| Composed stage prefix under `configs/pipeline/` | `binder/binder_` | `ligand_binder/ligand_binder_` | `ame/ame_` |
| Model checkpoint | `complexa.ckpt` | `complexa_ligand.ckpt` | `complexa_ame.ckpt` |
| Autoencoder checkpoint | `complexa_ae.ckpt` | `complexa_ligand_ae.ckpt` | `complexa_ame_ae.ckpt` |
| Target dictionary | `configs/targets/targets_dict.yaml` | `configs/targets/ligand_targets_dict.yaml` | `configs/design_tasks/ame_dict_v2.yaml` |
| Example task key | `02_PDL1` | `39_7V11_LIGAND` | `M0096_1chm` |
| Default search | `best-of-n` | `best-of-n` | `single-pass` |
| Search reward | AF2 alias `af2folding` | RF3 alias `rf3folding` | `null` |
| Inverse folding | `soluble_mpnn` | `ligand_mpnn` | `ligand_mpnn` |
| Final `metric.binder_folding_method` | `colabdesign` | `rf3_latest` | `rf3_latest` |
| `metric.sequence_types` | `[self]` | `[self, mpnn]` | `[self, mpnn_fixed]` |
| Evaluation `protein_type` | `binder` | `binder` | `motif_binder` |
| Analysis `result_type` | `protein_binder` | `ligand_binder` | `motif_ligand_binder` |
| `aggregation.analysis_modes` | `[binder, monomer]` | `[binder, monomer]` | `[motif_binder, monomer]` |
| `metric.compute_monomer_metrics` | `true` | `true` | `false` |

Each stage prefix has `generate.yaml`, `evaluate.yaml`, and `analyze.yaml` files.
The generation config is composed under `generation`; the evaluation and analysis
configs are composed at the root. All three local pipelines default to
`gen_njobs=1`, `eval_njobs=1`, `ncpus_=24`, and generation `batch_size=16`.
These are configuration defaults, not minimum hardware or output-count guarantees.

## Preserve checkpoint and target compatibility

Ligand and AME checkpoints require their pipeline's LoRA settings:
`r=32`, `lora_alpha=64.0`, `lora_dropout=0.0`, `train_bias=none`. AME also sets
`env_vars.USE_V2_COMPLEXA_ARCH: "True"`; the CLI injects this into stage subprocesses.
The released protein and ligand pipelines use the default v1 architecture.
Do not substitute checkpoints or remove adapters to fix a model-load failure.

AME starts without a reward model. Configure the appropriate reward and its
runtime before enabling reward-guided search; changing the algorithm alone is
insufficient. AME pre/refolded interface metrics are disabled by the released
evaluation config; comments in older manuals claiming they are enabled are stale.

With AME's null reward model, generation writes missing `total_reward` values.
The filter drops those rows and can write empty reward/selection tables, while
retaining the generated directories. Evaluation discovers `job_*` directories
independently, so an empty top-samples table does not establish zero evaluated
designs. Check generation records and actual evaluation counts before reporting
attrition; do not invent reward values or change the requested defaults to mask
this inconsistency. Trace `generate.py`, `filter.py`, and `evaluation/utils.py`
when the supplied revision differs.

Target entries must match the selected registry and available structures. A motif
request also needs the motif atom/residue specification. Do not invent a registry
key or infer that an example target supplies a newly requested epitope. Keep
`protein_type` and `result_type` aligned: they determine computed metrics and
analysis criteria, respectively. The standalone `motif_protein_binder` evaluation
is not another top-level design pipeline.

Sources: the three top-level pipeline YAMLs and their composed configs;
[CLI stage runner](https://github.com/NVIDIA-BioNeMo/Proteina-Complexa/blob/8fc6f5c85b38a2585ffaac555e708576dc4e8533/src/proteinfoundation/cli/cli_runner.py).
