"""Encode/decode structures through the frozen Proteina-Complexa autoencoder.

Measures all-atom reconstruction RMSD and sequence recovery for antibody Fv
structures vs non-antibody controls, to test whether the frozen AE's latent
space represents Ig folds as faithfully as the folds it was trained on.
"""

import os
import sys

import numpy as np
import torch

import biotite.structure as struc
from biotite.structure.io.pdb import PDBFile

from proteinfoundation.datasets.structure_data import atomarray_to_atom37
from proteinfoundation.partial_autoencoder.autoencoder import AutoEncoder
from proteinfoundation.utils.pdb_utils import write_prot_to_pdb

CKPT = "./ckpts/complexa_ae.ckpt"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
DEV = "cuda" if torch.cuda.is_available() else "cpu"


def load_chains(path, specs):
    """specs: list of (chain_id, max_residues or None). Returns an AtomArray."""
    arr = PDBFile.read(path).get_structure(model=1)
    arr = arr[struc.filter_amino_acids(arr)]
    arr = arr[~arr.hetero]
    pieces = []
    for ch, nres in specs:
        sub = arr[arr.chain_id == ch]
        if len(sub) == 0:
            raise ValueError(f"chain {ch} empty in {path}")
        ids = []
        for r in sub.res_id:
            if len(ids) == 0 or ids[-1] != r:
                ids.append(r)
        if nres is not None:
            ids = ids[:nres]
        sub = sub[np.isin(sub.res_id, np.array(ids))]
        pieces.append(sub)
    out = pieces[0]
    for p in pieces[1:]:
        out = out + p
    return out


def make_batch(data):
    rt_all = data.residue_type.long()
    keep = (rt_all >= 0) & (rt_all < 20) & data.coord_mask[:, 1].bool()
    data.coords = data.coords[keep]
    data.coord_mask = data.coord_mask[keep]
    data.residue_type = rt_all[keep]
    data.residue_pdb_idx = data.residue_pdb_idx[keep]
    data.chains = data.chains[keep]

    coords = data.coords.float()
    coord_mask = data.coord_mask.bool()
    coords_nm = coords / 10.0
    mask = coord_mask[:, 1].clone()

    ca = coords[:, 1, :]
    d = torch.norm(ca[1:] - ca[:-1], dim=1)
    cb = torch.cat([d > 4.0, torch.tensor([False])])

    b = lambda t: t.unsqueeze(0).to(DEV)
    batch = {
        "coords": b(coords),
        "coords_nm": b(coords_nm),
        "coord_mask": b(coord_mask),
        "residue_type": b(data.residue_type.long()),
        "residue_pdb_idx": b(data.residue_pdb_idx.float()),
        "chains": b(data.chains.long()),
        "chain_breaks_per_residue": b(cb),
        "mask": b(mask),
        "ca_coors_nm": b(coords_nm[:, 1, :]),
    }
    return batch, coords_nm.to(DEV), coord_mask.to(DEV), mask.to(DEV), data.residue_type.long().to(DEV)


def run(model, name, path, specs, write_pdb=True):
    arr = load_chains(path, specs)
    data = atomarray_to_atom37(arr, sample_id=name)
    batch, coords_nm, coord_mask, mask, restype = make_batch(data)
    n = int(mask.sum())

    with torch.no_grad():
        enc = model.encode(batch)
        z = enc["z_latent"] if isinstance(enc, dict) else (enc[0] if isinstance(enc, tuple) else enc)
        dec = model.decode(z, batch["ca_coors_nm"], batch["mask"])

    rec = dec["coors_nm"][0]
    valid = coord_mask & dec["atom_mask"][0].bool() & mask[:, None]
    diff = (rec - coords_nm) * valid[..., None]
    rmsd_nm = torch.sqrt((diff**2).sum() / (valid.sum() * 3.0))
    rmsd_a = float(rmsd_nm) * 10.0

    per_atom = torch.sqrt(((rec - coords_nm) ** 2).sum(-1))[valid]
    med_a = float(per_atom.median()) * 10.0

    pred_rt = dec["residue_type"][0].long()
    rec_rate = float(((pred_rt == restype) & mask).sum()) / max(n, 1)

    if write_pdb:
        os.makedirs(OUT, exist_ok=True)
        sq = ((rec - coords_nm) ** 2).sum(-1) * valid
        cnt = valid.sum(-1).clamp(min=1)
        per_res = (torch.sqrt(sq.sum(-1) / cnt) * 10.0).cpu().numpy()
        bf = np.repeat(per_res[:, None], 37, axis=1)
        tag = name.split()[0]
        nch = len(torch.unique(data.chains))
        if nch > 2:
            tag = f"{tag}_{nch}chain"
        ch = data.chains.cpu().numpy()
        aa = restype.cpu().numpy()
        write_prot_to_pdb((coords_nm * valid[..., None]).cpu().numpy() * 10.0,
                          os.path.join(OUT, f"{tag}_input.pdb"), aatype=aa,
                          chain_index=ch, no_indexing=True, overwrite=True)
        write_prot_to_pdb((rec * valid[..., None]).cpu().numpy() * 10.0,
                          os.path.join(OUT, f"{tag}_recon.pdb"), aatype=aa,
                          chain_index=ch, b_factors=bf, no_indexing=True, overwrite=True)

    print(f"  {name:22s} n={n:4d}  all-atom RMSD {rmsd_a:6.3f} A   median {med_a:6.3f} A   seq recovery {rec_rate*100:5.1f}%")
    return rmsd_a, rec_rate


def main():
    print(f"device: {DEV}")
    model = AutoEncoder.load_from_checkpoint(CKPT, map_location=DEV)
    model.eval().to(DEV)
    for p in model.parameters():
        p.requires_grad = False
    print(f"loaded {CKPT}, latent_dim={model.latent_dim}\n")

    ab = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdbs")
    ctl = "./assets/target_data/alpha_proteo_targets"

    print("ANTIBODY Fv (VH + VL):")
    ab_r = []
    for name, path, specs in [
        ("1a2y Fv", f"{ab}/1a2y.pdb", [("B", None), ("A", None)]),
        ("1bj1 Fv (bevacizumab)", f"{ab}/1bj1.pdb", [("H", 120), ("L", 107)]),
        ("12e8 Fv", f"{ab}/12e8.pdb", [("H", 120), ("L", 107)]),
        ("1n8z Fv (trastuzumab)", f"{ab}/1n8z.pdb", [("B", 120), ("A", 107)]),
    ]:
        try:
            ab_r.append(run(model, name, path, specs))
        except Exception as e:
            import traceback; traceback.print_exc()

    print("\n3-CHAIN COMPLEX (VH + VL + antigen):")
    for name, path, specs in [
        ("1a2y Fv+lysozyme", f"{ab}/1a2y.pdb", [("B", None), ("A", None), ("C", None)]),
        ("1bj1 Fv+VEGF", f"{ab}/1bj1.pdb", [("H", 120), ("L", 107), ("V", None)]),
        ("1n8z Fv+HER2", f"{ab}/1n8z.pdb", [("B", 120), ("A", 107), ("C", 200)]),
    ]:
        try:
            run(model, name, path, specs)
        except Exception as e:
            print(f"  {name:22s} FAILED: {type(e).__name__}: {e}")

    print("\n4-CHAIN COMPLEX (two Fabs + two antigen copies):")
    try:
        run(model, "1bj1 HLVW", f"{ab}/1bj1.pdb", [("H", 120), ("L", 107), ("V", None), ("W", None)])
    except Exception as e:
        print(f"  1bj1 HLVW              FAILED: {type(e).__name__}: {e}")

    print("\nNON-ANTIBODY controls:")
    ct_r = []
    import glob

    for f in sorted(glob.glob(f"{ctl}/*.pdb"))[:4]:
        nm = os.path.basename(f).replace(".pdb", "")
        try:
            arr = PDBFile.read(f).get_structure(model=1)
            arr = arr[struc.filter_amino_acids(arr)]
            chains = list(dict.fromkeys(arr.chain_id.tolist()))
            ct_r.append(run(model, nm[:22], f, [(chains[0], 230)]))
        except Exception as e:
            print(f"  {nm:22s} FAILED: {type(e).__name__}: {e}")

    if ab_r and ct_r:
        a = np.array([x[0] for x in ab_r]); c = np.array([x[0] for x in ct_r])
        sa = np.array([x[1] for x in ab_r]); sc = np.array([x[1] for x in ct_r])
        print("\n" + "=" * 70)
        print(f"antibody Fv : RMSD mean {a.mean():.3f} A (n={len(a)})   seq recovery {sa.mean()*100:.1f}%")
        print(f"control     : RMSD mean {c.mean():.3f} A (n={len(c)})   seq recovery {sc.mean()*100:.1f}%")
        print(f"ratio       : {a.mean()/max(c.mean(),1e-9):.2f}x")


if __name__ == "__main__":
    sys.exit(main())
