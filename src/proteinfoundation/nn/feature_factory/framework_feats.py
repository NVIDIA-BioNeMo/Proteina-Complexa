"""Antibody framework conditioning features.

Conditions generation on the framework (non-CDR) portions of an antibody Fv,
supplied as *sequence* and, optionally, as structure.

Why a separate conditioner rather than reusing the motif path:

  * The motif path (``MotifConcatSeqFeat``) is 205-dim, of which 185 dims are
    absolute coordinates plus an atom-presence mask and only 20 are residue
    identity.  It therefore *requires* the motif to be placed in space.  The
    antibody case we care about supplies framework sequence with no committed
    pose, so the coordinate half must be optional rather than zero-filled.
  * The framework spans two chains (VH and VL) whose identity matters.  Motif
    features carry no chain-type signal.

The ``use_coords`` flag is the ablation axis: ``False`` is sequence-only
conditioning (22 dims), ``True`` adds absolute coordinates (207 dims).  Both
arms are the same module so switching is a config change, not a code change.

Expected batch keys:
    seq_framework           [b, k]          residue types, 0-19
    seq_framework_mask      [b, k]          bool, valid framework positions
    framework_chain         [b, k]          0 = VH, 1 = VL
    x_framework             [b, k, 37, 3]   atom37 coords in nm (use_coords only)
    framework_mask          [b, k, 37]      bool atom mask    (use_coords only)
"""

import torch
from loguru import logger

from proteinfoundation.nn.feature_factory.base_feature import Feature
from proteinfoundation.nn.feature_factory.seq_feats import (
    Atom37NanometersCoorsSeqFeat,
    ResidueTypeSeqFeat,
)

# VH and VL.  Kept as a named constant because the chain-type one-hot width is
# baked into the projection shape and therefore into checkpoint compatibility.
N_FRAMEWORK_CHAIN_TYPES = 2


class FrameworkChainTypeSeqFeat(Feature):
    """One-hot over framework chain type (VH / VL).

    Carries which variable domain each conditioning token belongs to.  Without
    this the model sees one undifferentiated bag of framework residues and has
    no way to learn the VH/VL pairing geometry that defines an Fv.
    """

    def __init__(self, **kwargs):
        super().__init__(dim=N_FRAMEWORK_CHAIN_TYPES)
        self._has_logged = False

    def forward(self, batch):
        if "framework_chain" in batch:
            chain = batch["framework_chain"].long().clamp(0, N_FRAMEWORK_CHAIN_TYPES - 1)
            oh = torch.nn.functional.one_hot(chain, num_classes=N_FRAMEWORK_CHAIN_TYPES)
            return oh.to(torch.float32)

        b, n = self.extract_bs_and_n(batch)
        device = self.extract_device(batch)
        if not self._has_logged:
            logger.warning("No framework_chain in batch, returning zeros for FrameworkChainTypeSeqFeat")
            self._has_logged = True
        return torch.zeros(b, n, self.dim, device=device)


class FrameworkSequenceSeqFeat(Feature):
    """One-hot residue identity over framework positions."""

    def __init__(self, **kwargs):
        super().__init__(dim=20)
        self.seq_feat = ResidueTypeSeqFeat()
        self._has_logged = False

    def forward(self, batch):
        if "seq_framework" in batch and "seq_framework_mask" in batch:
            return self.seq_feat(
                {
                    "residue_type": batch["seq_framework"],
                    "mask_dict": {"residue_type": batch["seq_framework_mask"]},
                }
            )

        b, n = self.extract_bs_and_n(batch)
        device = self.extract_device(batch)
        if not self._has_logged:
            logger.warning(
                "No seq_framework/seq_framework_mask in batch, returning zeros for FrameworkSequenceSeqFeat"
            )
            self._has_logged = True
        return torch.zeros(b, n, self.dim, device=device)


class FrameworkConcatSeqFeat(Feature):
    """Framework conditioning tokens, appended along the token axis.

    Returns ``(feats, mask)`` with shapes ``[b, k, dim]`` and ``[b, k]``, matching
    the contract of ``MotifConcatSeqFeat`` / ``TargetConcatSeqFeat`` so that
    ``ConcatFeaturesFactory`` can treat this as one more conditioner slot.

    Args:
        use_coords: If True, append absolute atom37 coordinates and the atom
            mask, giving structure-aware framework conditioning.  If False
            (default) the conditioning is sequence-only and carries no pose.
    """

    def __init__(self, use_coords: bool = False, **kwargs):
        super().__init__(dim=None)
        self.use_coords = use_coords

        self.seq_feat = FrameworkSequenceSeqFeat()
        self.chain_feat = FrameworkChainTypeSeqFeat()
        self.dim = self.seq_feat.dim + self.chain_feat.dim  # 20 + 2 = 22

        if use_coords:
            self.coords_feat = Atom37NanometersCoorsSeqFeat(rel=False)
            self.dim += self.coords_feat.dim + 37  # + 148 + 37 = 207
        else:
            self.coords_feat = None

        self._has_logged = False

    def _empty(self, batch):
        """No framework supplied: contribute zero tokens.

        Returning width-0 tensors (rather than zero-valued tokens) keeps the
        conditioning genuinely optional -- the extended representation is then
        byte-identical to the unconditioned one, so a model trained with
        conditioning dropout sees exactly the inference-time unconditioned case.
        """
        if not self._has_logged:
            logger.warning("Missing required framework data for FrameworkConcatSeqFeat")
            self._has_logged = True
        b = batch.get("batch_size", 1)
        device = self.extract_device(batch)
        return (
            torch.zeros(b, 0, self.dim, device=device),
            torch.zeros(b, 0, dtype=torch.bool, device=device),
        )

    def forward(self, batch):
        required = ("seq_framework", "seq_framework_mask")
        if any(k not in batch for k in required):
            return self._empty(batch)
        if self.use_coords and ("x_framework" not in batch or "framework_mask" not in batch):
            return self._empty(batch)

        mask = batch["seq_framework_mask"]  # [b, k]

        parts = [
            self.seq_feat(batch),  # [b, k, 20]
            self.chain_feat(batch),  # [b, k, 2]
        ]

        if self.use_coords:
            parts.append(
                self.coords_feat(
                    {
                        "coords_nm": batch["x_framework"],  # [b, k, 37, 3]
                        "coord_mask": batch["framework_mask"],  # [b, k, 37]
                    }
                )
            )  # [b, k, 148]
            parts.append(batch["framework_mask"] * 1.0)  # [b, k, 37]

        feats = torch.cat(parts, dim=-1)  # [b, k, self.dim]
        feats = feats * mask[..., None]
        return feats, mask
