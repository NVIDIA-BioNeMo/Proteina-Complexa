# Candidate lineage

Search metadata identifies candidates and their branching history. At revision
`8fc6f5c85b38a2585ffaac555e708576dc4e8533`, tags occur in PDB filenames such as
`job_{id}_n_{len}_id_{idx}_{tag}.pdb` and in `metadata_tag` when exported to CSV.
Inspect actual generated records; a tag alone is not a globally unique design ID.

## Decode tags and retain pairing evidence

| Algorithm | Tag pattern |
|---|---|
| Single-pass | `single_orig{S}` |
| Best-of-n | `bon_orig{S}_r{R}` |
| Beam search | `beam_orig{S}_bm{B}[-s{START}to{END}br{BR}]*` |
| FK steering | `fk_orig{S}_bm{B}[-s{START}to{END}br{BR}]*` |
| MCTS | `mcts_orig{S}[-s{START}to{END}br{BR}]*`; simulations additionally append `-s{START}to{END}sim{SIM}br{BR}` |

`S` is the original sample index, `R` a replica, `B` an initial beam, and each
step segment records a denoising interval and branch. Match a candidate's ancestry
by lineage prefixes within the same run/job/batch; similar prefixes from another
batch do not establish ancestry. Lookahead tags may have fewer segments than a
final, but use explicit sample-type metadata when available.

For refinement comparisons, retain run/job/batch/sample identity, metadata tag,
sample type, sequence, structure path, and error evidence. Pair `final_unrefined`
with `final` by stable lineage, not sequence identity. Changed sequences are
expected after refinement, while unchanged sequences can reflect an optimization
outcome or an error returning the original. Preserve both arms before selection.
Deduplication and top-N filtering can remove one arm even when files are retained.

Do not infer requested dataset size from filenames or batch size. Use dataset
sample/repeat settings and actual completed batches; candidate counts include
replicas, branching, lookaheads, and optional refinement copies. Count surviving
pairs and report missing members explicitly.
