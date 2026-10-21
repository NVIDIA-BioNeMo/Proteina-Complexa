# `complexa download` Reference

Full flag matrix, destination layout, and NGC source for every checkpoint
Complexa can pull.

`complexa download` is a thin Python wrapper around `env/download_startup.sh`.
The CLI (`src/proteinfoundation/cli/cli_runner.py:download_main`) accepts the
documented flags below and forwards them to the bash script. It is a first-party,
developer-run CLI invoked with a fixed, documented set of flags — it takes no
untrusted or network-supplied input, so the forwarded arguments are not an
injection surface.

---

## Flag matrix

The Python argparse explicitly defines these flags:

| Flag | What it downloads | Destination | Approx size | Source |
|------|-------------------|-------------|-------------|--------|
| `--complexa` | `complexa.ckpt` + `complexa_ae.ckpt` (protein binder) | `./ckpts/` | ~3 GB | NGC `proteina_complexa` |
| `--complexa-ligand` | `complexa_ligand.ckpt` + `complexa_ligand_ae.ckpt` (ligand binder) | `./ckpts/` | ~3 GB | NGC `proteina_complexa_ligand` |
| `--complexa-ame` | `complexa_ame.ckpt` + `complexa_ame_ae.ckpt` (motif scaffolding) | `./ckpts/` | ~3 GB | NGC `proteina_complexa_ame` |
| `--complexa-all` | All three Complexa pairs | `./ckpts/` | ~9 GB | NGC (3 models) |
| `--all` | ProteinMPNN + LigandMPNN + AF2 + ESM2 + RF3 | `./community_models/...` | ~50 GB | Mixed (GitHub + AWS + HF + NGC) |
| `--everything` | All Complexa pairs plus the `--all` community set | both | Allow additional disk headroom | Mixed |
| `--status` | Show install state; downloads nothing | (none) | n/a | n/a |

The underlying bash script also accepts per-model flags (`--pmpnn`,
`--ligmpnn`, `--af2`, `--esm2`, `--rf3`). They are not defined in the Python
CLI parser, which rejects unknown flags before reaching the download wrapper.
Invoke the trusted script directly for these selections, for example:

```bash
bash env/download_startup.sh --af2 --pmpnn
```

| Script flag | Destination | Approx size |
|------------------|-------------|-------------|
| `--pmpnn` | `./community_models/ProteinMPNN/{ca,vanilla}_model_weights/` | ~50 MB |
| `--ligmpnn` | `./community_models/LigandMPNN/model_params/` | ~500 MB |
| `--af2` | `./community_models/ckpts/AF2/` | ~3 GB |
| `--esm2` | `./community_models/ckpts/ESM2/` | ~2.5 GB |
| `--rf3` | `./community_models/ckpts/RF3/` | ~10 GB |

---

## Default destinations

All downloads land relative to the *current working directory* (the script
`cd`s to project root, derived from `PROJECT_ROOT` inside `download_startup.sh`).

```
$PROJECT_ROOT/
├── ckpts/                                   ← all 6 Complexa ckpts here, flat
│   ├── complexa.ckpt                        ← protein binder model
│   ├── complexa_ae.ckpt                     ← protein binder autoencoder
│   ├── complexa_ligand.ckpt                 ← ligand binder model
│   ├── complexa_ligand_ae.ckpt              ← ligand binder autoencoder
│   ├── complexa_ame.ckpt                    ← AME motif scaffolding model
│   └── complexa_ame_ae.ckpt                 ← AME autoencoder
└── community_models/
    ├── ProteinMPNN/
    │   ├── ca_model_weights/                ← Cα-only weights
    │   └── vanilla_model_weights/           ← full-backbone weights
    ├── LigandMPNN/model_params/             ← LigandMPNN weights
    └── ckpts/
        ├── AF2/                             ← AlphaFold2 .npz params
        ├── ESM2/                            ← ESM2-650M weights
        └── RF3/                             ← RoseTTAFold3 ckpt
```

Note: `.env_example` defaults `LOCAL_CHECKPOINT_PATH` to
`${LOCAL_CODE_PATH}/checkpoints`. Set it to `${LOCAL_CODE_PATH}/ckpts` when
using the downloader's layout, or move the weights to your configured path.
`complexa download` always writes to `$PROJECT_ROOT/ckpts/` regardless of
the `.env` setting. Preserve `CKPT_PATH=${LOCAL_CHECKPOINT_PATH}`; Docker
activation selects `DOCKER_CHECKPOINT_PATH` separately.

---

## The three Complexa model variants

| Variant | Pipeline config | Required ckpt pair | Use case |
|---------|----------------|---------------------|----------|
| Protein binder | `configs/search_binder_local_pipeline.yaml` | `complexa.ckpt` + `complexa_ae.ckpt` | De novo binders for protein targets (PDL1, EGFR, etc.) |
| Ligand binder | `configs/search_ligand_binder_local_pipeline.yaml` | `complexa_ligand.ckpt` + `complexa_ligand_ae.ckpt` | Binders to small-molecule pockets (FAD, OQO, etc.) |
| AME | `configs/search_ame_local_pipeline.yaml` | `complexa_ame.ckpt` + `complexa_ame_ae.ckpt` | Scaffolding catalytic / functional motifs with ligand context |

Each pipeline YAML has three checkpoint fields at the top level that you
**must** point at your local ckpts. After `complexa download --complexa-all`
they will be at `./ckpts/complexa{,_ae,_ligand,_ligand_ae,_ame,_ame_ae}.ckpt`:

```yaml
ckpt_path: ./ckpts
ckpt_name: complexa.ckpt
autoencoder_ckpt_path: ./ckpts/complexa_ae.ckpt
```

Or override on the CLI without editing the YAML:

```bash
complexa design configs/search_binder_local_pipeline.yaml \
    ++ckpt_path=./ckpts \
    ++ckpt_name=complexa.ckpt \
    ++autoencoder_ckpt_path=./ckpts/complexa_ae.ckpt
```

> Note: `complexa download` always uses a *flat* `./ckpts/` layout. If you
> downloaded ckpts manually into per-variant subdirectories
> (`ckpts/complexa_protein/`, etc.), update the pipeline YAML `ckpt_path` to
> match — or move/symlink into the flat layout.

---

## `complexa download --status` output

Abbreviated example after installing all Complexa pairs and AF2 through the
corresponding aggregate and script flags:

```
═══════════════════════════════════════════
  Installation Status
═══════════════════════════════════════════
    Complexa (Protein): ✓ Installed (./ckpts/)
    Complexa (Ligand):  ✓ Installed (./ckpts/)
    Complexa (AME):     ✓ Installed (./ckpts/)
    ProteinMPNN:     ○ Missing (community_models/ProteinMPNN/)
    LigandMPNN:      ○ Missing (community_models/LigandMPNN/model_params/)
    AF2:             ✓ Installed (community_models/ckpts/AF2/)
    ESM2:            ○ Not installed (community_models/ckpts/ESM2/)
    RF3:             ○ Missing (community_models/ckpts/RF3/)
═══════════════════════════════════════════
```

Read each row as: `<Model name>: <✓ Installed | ○ Missing> (<destination>)`.
Use the CLI's aggregate flags or the script's per-model flags for missing
families. The status checks are presence checks, not integrity checks; verify
nonzero sizes and download completion before treating weights as usable.

---

## Tips

- Run `complexa download --status` **before** any download — it shows what is already on disk and saves re-downloading.
- Re-running `complexa download --<flag>` is idempotent: existing non-empty ckpts are skipped (`download_complexa_weights` checks `[ -f "$fm_ckpt" ] && [ -s "$fm_ckpt" ]`).
- Failed downloads leave a zero-byte file then `rm -f` it — safe to retry without manual cleanup.
- For Hugging Face downloads, configure authentication as required by the selected source without printing tokens.
- `complexa download --everything` fetches all bundled variants and community families. Prefer targeted script flags unless you need that complete set; optional backends require their own installation procedure.
