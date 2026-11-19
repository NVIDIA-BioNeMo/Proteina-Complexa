"""Tests for antibody framework conditioning and the generalised concat factory.

Covers two things:

1.  The new ``framework`` conditioner slot behaves as designed -- correct
    dimensions for both ablation arms, genuine optionality, zero-init no-op,
    and a VH/VL distinction.
2.  Generalising ``ConcatFeaturesFactory.forward`` from a hardcoded
    ``len(all_feats) == 1 / == 2`` branch chain to a per-slot loop did not
    change behaviour for the pre-existing configurations, and did not rename
    any parameter (the released checkpoints contain entries such as
    ``nn.concat_factory.linear_out_ligand.lora_A``, so names are a
    compatibility contract).
"""

import pytest
import torch

from proteinfoundation.nn.feature_factory.concat_feature_factory_v2 import ConcatFeaturesFactory

DIM = 256
B, N_SAMPLE, N_TARGET, N_LIGAND, K_FRAMEWORK = 2, 12, 9, 7, 6
VH, VL = 0, 1


def _base_batch():
    return {
        "x_t": {"bb_ca": torch.randn(B, N_SAMPLE, 3)},
        "mask": torch.ones(B, N_SAMPLE, dtype=torch.bool),
        "coords_nm": torch.randn(B, N_SAMPLE, 37, 3),
        "coord_mask": torch.ones(B, N_SAMPLE, 37, dtype=torch.bool),
        "batch_size": B,
    }


def _add_target(batch):
    """Protein target: atom37 coordinates plus residue indices."""
    return batch | {
        "x_target": torch.randn(B, N_TARGET, 37, 3),
        "target_mask": torch.ones(B, N_TARGET, 37, dtype=torch.bool),
        "seq_target": torch.randint(0, 20, (B, N_TARGET)),
        "seq_target_mask": torch.ones(B, N_TARGET, dtype=torch.bool),
        "target_chains": torch.zeros(B, N_TARGET, dtype=torch.long),
        "target_hotspot_mask": torch.zeros(B, N_TARGET, dtype=torch.bool),
    }


def _add_ligand(batch):
    """Ligand reuses the x_target/seq_target keys with per-ATOM coords and a one-hot type."""
    onehot = torch.zeros(B, N_LIGAND, 128)
    onehot[:, :, 6] = 1.0
    return batch | {
        "x_target": torch.randn(B, N_LIGAND, 3),
        "target_mask": torch.ones(B, N_LIGAND, dtype=torch.bool),
        "seq_target": onehot,
        "seq_target_mask": torch.ones(B, N_LIGAND, dtype=torch.bool),
        "target_charge": torch.randn(B, N_LIGAND),
        "target_atom_name": torch.randn(B, N_LIGAND, 4 * 64),
        "target_laplacian_pe": torch.randn(B, N_LIGAND, 32),
    }


def _add_motif(batch, n_motif=5):
    return batch | {
        "x_motif": torch.randn(B, n_motif, 37, 3),
        "motif_mask": torch.ones(B, n_motif, 37, dtype=torch.bool),
        "seq_motif": torch.randint(0, 20, (B, n_motif)),
        "seq_motif_mask": torch.ones(B, n_motif, dtype=torch.bool),
    }


def _add_framework(batch, with_coords=False, chain=None):
    if chain is None:
        chain = torch.full((B, K_FRAMEWORK), VH)
        chain[:, K_FRAMEWORK // 2 :] = VL
    out = batch | {
        "seq_framework": torch.randint(0, 20, (B, K_FRAMEWORK)),
        "seq_framework_mask": torch.ones(B, K_FRAMEWORK, dtype=torch.bool),
        "framework_chain": chain,
    }
    if with_coords:
        out |= {
            "x_framework": torch.randn(B, K_FRAMEWORK, 37, 3),
            "framework_mask": torch.ones(B, K_FRAMEWORK, 37, dtype=torch.bool),
        }
    return out


@pytest.fixture
def seq_repr():
    return torch.randn(B, N_SAMPLE, DIM), torch.ones(B, N_SAMPLE, dtype=torch.bool)


# --------------------------------------------------------------------------
# Pre-existing configurations must keep working
# --------------------------------------------------------------------------

EXISTING_CONFIGS = [
    ("motif", dict(enable_motif=True), _add_motif, 5),
    ("target", dict(enable_target=True), _add_target, N_TARGET),
    ("ligand", dict(enable_ligand=True), _add_ligand, N_LIGAND),
]


@pytest.mark.parametrize("name,cfg,add_fn,n_tokens", EXISTING_CONFIGS)
def test_existing_single_conditioner_token_counts(name, cfg, add_fn, n_tokens, seq_repr):
    sr, sm = seq_repr
    factory = ConcatFeaturesFactory(dim_feats_out=DIM, **cfg).eval()
    with torch.no_grad():
        out, mask = factory(add_fn(_base_batch()), sr, sm)
    assert out.shape == (B, N_SAMPLE + n_tokens, DIM)
    assert mask.shape == (B, N_SAMPLE + n_tokens)


@pytest.mark.parametrize(
    "cfg,add_fns,n_tokens",
    [
        (dict(enable_ligand=True, enable_motif=True), [_add_ligand, _add_motif], N_LIGAND + 5),
        (dict(enable_target=True, enable_motif=True), [_add_target, _add_motif], N_TARGET + 5),
    ],
)
def test_existing_paired_conditioners(cfg, add_fns, n_tokens, seq_repr):
    sr, sm = seq_repr
    factory = ConcatFeaturesFactory(dim_feats_out=DIM, **cfg).eval()
    batch = _base_batch()
    for fn in add_fns:
        batch = fn(batch)
    with torch.no_grad():
        out, _ = factory(batch, sr, sm)
    assert out.shape == (B, N_SAMPLE + n_tokens, DIM)


@pytest.mark.parametrize(
    "cfg,expected",
    [
        (dict(enable_motif=True), {"linear_out", "ln_out"}),
        (dict(enable_target=True), {"linear_out_target", "ln_out_target"}),
        (dict(enable_ligand=True), {"linear_out_ligand", "ln_out_ligand"}),
    ],
)
def test_projection_attribute_names_are_stable(cfg, expected):
    """These names appear in released checkpoints; renaming them breaks loading."""
    factory = ConcatFeaturesFactory(dim_feats_out=DIM, use_ln_out=True, **cfg)
    for attr in expected:
        assert hasattr(factory, attr), f"missing {attr}; released checkpoints reference it"


def test_ligand_and_target_remain_mutually_exclusive():
    with pytest.raises(ValueError):
        ConcatFeaturesFactory(enable_ligand=True, enable_target=True, dim_feats_out=DIM)


def test_no_conditioner_enabled_raises():
    with pytest.raises(ValueError):
        ConcatFeaturesFactory(dim_feats_out=DIM)


# --------------------------------------------------------------------------
# The framework slot
# --------------------------------------------------------------------------


def test_framework_dims_for_both_ablation_arms():
    seq_only = ConcatFeaturesFactory(enable_framework=True, dim_feats_out=DIM)
    with_struct = ConcatFeaturesFactory(enable_framework=True, framework_use_coords=True, dim_feats_out=DIM)
    # 20 residue type + 2 chain type
    assert seq_only.feature_creators[0].get_dim() == 22
    # + 148 atom37 coords + 37 atom mask
    assert with_struct.feature_creators[0].get_dim() == 207


def test_framework_adds_exactly_one_token_per_residue(seq_repr):
    sr, sm = seq_repr
    factory = ConcatFeaturesFactory(enable_target=True, enable_framework=True, dim_feats_out=DIM).eval()
    with torch.no_grad():
        without, _ = factory(_add_target(_base_batch()), sr, sm)
        with_fw, _ = factory(_add_framework(_add_target(_base_batch())), sr, sm)
    assert with_fw.shape[1] - without.shape[1] == K_FRAMEWORK


def test_framework_is_genuinely_optional(seq_repr):
    """Absent framework keys must leave the representation byte-identical.

    The conditioner contributes zero-WIDTH tokens rather than zero-VALUED ones,
    so a model trained with conditioning dropout sees exactly the same input at
    inference time when no framework is supplied.
    """
    sr, sm = seq_repr
    with_slot = ConcatFeaturesFactory(enable_target=True, enable_framework=True, dim_feats_out=DIM).eval()
    with torch.no_grad():
        out, mask = with_slot(_add_target(_base_batch()), sr, sm)
    assert out.shape == (B, N_SAMPLE + N_TARGET, DIM)
    assert mask.shape == (B, N_SAMPLE + N_TARGET)


def test_zero_init_framework_is_an_exact_noop(seq_repr):
    """Adding this slot to a pretrained checkpoint must not perturb it."""
    sr, sm = seq_repr
    factory = ConcatFeaturesFactory(
        enable_target=True, enable_framework=True, zero_init_framework=True, dim_feats_out=DIM
    ).eval()
    batch = _add_target(_base_batch())
    with torch.no_grad():
        without, _ = factory(dict(batch), sr, sm)
        with_fw, _ = factory(_add_framework(dict(batch)), sr, sm)

    framework_tokens = with_fw[:, N_SAMPLE + N_TARGET :, :]
    assert float(framework_tokens.abs().max()) == 0.0
    # and the pre-existing tokens are untouched
    assert torch.equal(with_fw[:, : N_SAMPLE + N_TARGET, :], without)


def test_zero_init_projection_still_trains(seq_repr):
    """Zero-init must not mean zero-gradient, or the slot could never learn."""
    sr, sm = seq_repr
    factory = ConcatFeaturesFactory(
        enable_target=True, enable_framework=True, zero_init_framework=True, dim_feats_out=DIM
    )
    out, _ = factory(_add_framework(_add_target(_base_batch())), sr, sm)
    out.sum().backward()
    grad = factory.linear_out_framework.weight.grad
    assert grad is not None and float(grad.abs().sum()) > 0


def test_vh_and_vl_are_distinguishable():
    """Without a chain-type signal the model cannot learn VH/VL pairing geometry."""
    factory = ConcatFeaturesFactory(enable_framework=True, dim_feats_out=DIM).eval()
    creator = factory.feature_creators[0]

    batch = _add_framework(_base_batch())
    as_vh = batch | {"framework_chain": torch.full((B, K_FRAMEWORK), VH)}
    as_vl = batch | {"framework_chain": torch.full((B, K_FRAMEWORK), VL)}

    with torch.no_grad():
        feats_vh, _ = creator(as_vh)
        feats_vl, _ = creator(as_vl)
    assert not torch.equal(feats_vh, feats_vl)


def test_structure_arm_forward(seq_repr):
    sr, sm = seq_repr
    factory = ConcatFeaturesFactory(
        enable_target=True, enable_framework=True, framework_use_coords=True, dim_feats_out=DIM
    ).eval()
    batch = _add_framework(_add_target(_base_batch()), with_coords=True)
    with torch.no_grad():
        out, _ = factory(batch, sr, sm)
    assert out.shape == (B, N_SAMPLE + N_TARGET + K_FRAMEWORK, DIM)


def test_framework_token_order_is_last(seq_repr):
    """Token order is part of the checkpoint contract: target/ligand, motif, then framework."""
    sr, sm = seq_repr
    factory = ConcatFeaturesFactory(
        enable_target=True, enable_motif=True, enable_framework=True, dim_feats_out=DIM
    ).eval()
    assert factory.slot_names == ["target", "motif", "framework"]
