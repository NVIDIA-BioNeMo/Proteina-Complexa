import torch
from loguru import logger

from proteinfoundation.nn.feature_factory.framework_feats import FrameworkConcatSeqFeat
from proteinfoundation.nn.feature_factory.ligand_feats import LigandConcatSeqFeat
from proteinfoundation.nn.feature_factory.motif_feats import MotifConcatSeqFeat
from proteinfoundation.nn.feature_factory.target_feats import TargetConcatSeqFeat

# Slot name -> (linear attribute, layernorm attribute).
#
# These attribute names are load-bearing: they appear in released checkpoints
# (e.g. ``nn.concat_factory.linear_out_ligand.lora_A``), so renaming them breaks
# weight loading.  "motif" keeps the unsuffixed names for that reason.
_PROJ_ATTRS = {
    "ligand": ("linear_out_ligand", "ln_out_ligand"),
    "target": ("linear_out_target", "ln_out_target"),
    "motif": ("linear_out", "ln_out"),
    "framework": ("linear_out_framework", "ln_out_framework"),
}


class ConcatFeaturesFactory(torch.nn.Module):
    """Factory for creating concat features from motif, target, ligand and/or framework.

    Each enabled conditioner contributes its own tokens along the sequence axis,
    projected by its own bias-free linear layer.  Token order is fixed as
    ligand/target, then motif, then framework; this order is part of the
    checkpoint contract and must not change.

    Args:
        enable_motif: Whether to enable motif concat features
        enable_target: Whether to enable target concat features
        enable_ligand: Whether to enable ligand concat features
        enable_framework: Whether to enable antibody framework concat features
        framework_use_coords: If True the framework conditioner carries absolute
            coordinates in addition to sequence; if False it is sequence-only.
        zero_init_framework: Zero-initialise the framework projection so that an
            untrained framework path is an exact no-op on a pretrained model
            (ControlNet-style).  Gradients still flow, so it trains normally.
        dim_feats_out: The dimension of the output features
        use_ln_out: Whether to use layer normalization
        **kwargs: Additional keyword arguments
    """

    def __init__(
        self,
        enable_motif: bool = False,
        enable_target: bool = False,
        enable_ligand: bool = False,
        enable_framework: bool = False,
        framework_use_coords: bool = False,
        zero_init_framework: bool = True,
        dim_feats_out: int = 256,
        use_ln_out: bool = False,
        **kwargs,
    ):
        super().__init__()
        self.enable_motif = enable_motif
        self.enable_target = enable_target
        self.enable_ligand = enable_ligand
        self.enable_framework = enable_framework

        if not (enable_motif or enable_target or enable_ligand or enable_framework):
            raise ValueError(
                "At least one of enable_motif, enable_target, enable_ligand or enable_framework must be True"
            )
        if enable_ligand and enable_target:
            raise ValueError("Cannot enable both ligand and target concat features for now")

        # Ordered slot list.  Order defines token order in the extended
        # representation and must match the original implementation.
        self.feature_creators = torch.nn.ModuleList()
        self.slot_names: list[str] = []

        def _add(name, creator):
            self.feature_creators.append(creator)
            self.slot_names.append(name)
            logger.info(f"Enabled {name} concat features")
            return creator.get_dim()

        slot_dims = {}
        if enable_ligand:
            slot_dims["ligand"] = _add("ligand", LigandConcatSeqFeat(**kwargs))
        elif enable_target:
            slot_dims["target"] = _add("target", TargetConcatSeqFeat(**kwargs))

        if enable_motif:
            slot_dims["motif"] = _add("motif", MotifConcatSeqFeat(**kwargs))

        if enable_framework:
            slot_dims["framework"] = _add(
                "framework",
                FrameworkConcatSeqFeat(use_coords=framework_use_coords, **kwargs),
            )

        # Create projection layers under their checkpoint-compatible names.
        for name, in_dim in slot_dims.items():
            lin_attr, ln_attr = _PROJ_ATTRS[name]
            lin = torch.nn.Linear(in_dim, dim_feats_out, bias=False)
            if name == "framework" and zero_init_framework:
                torch.nn.init.zeros_(lin.weight)
            setattr(self, lin_attr, lin)
            setattr(self, ln_attr, torch.nn.LayerNorm(dim_feats_out) if use_ln_out else torch.nn.Identity())

    def _project(self, name, feats):
        lin_attr, ln_attr = _PROJ_ATTRS[name]
        return getattr(self, ln_attr)(getattr(self, lin_attr)(feats))

    def forward(self, batch, seq_repr, seq_mask):
        """
        Args:
            batch: Input batch dictionary
            seq_repr: Original sequence representation [b, n, dim]
            seq_mask: Original sequence mask [b, n]

        Returns:
            extended_seq_repr: Extended sequence representation [b, n + n_concat, dim]
            extended_mask: Extended mask [b, n + n_concat]
        """
        if "batch_size" not in batch:
            batch["batch_size"] = seq_repr.shape[0]

        projected_parts, mask_parts = [], []
        # Projections whose slot produced no tokens this step.  Their parameters
        # would otherwise be absent from the autograd graph, which DDP reports as
        # unused parameters; a zero-weighted term keeps them attached.
        idle_slots = []

        for name, creator in zip(self.slot_names, self.feature_creators):
            feats, mask = creator(batch)  # [b, n_i, d_i], [b, n_i]
            if feats.shape[1] == 0:
                idle_slots.append(name)
                continue
            proj = self._project(name, feats) * mask[..., None]
            projected_parts.append(proj)
            mask_parts.append(mask)

        if not projected_parts:
            return seq_repr, seq_mask

        projected_feats = torch.cat(projected_parts, dim=1)
        combined_masks = torch.cat(mask_parts, dim=1)

        for name in idle_slots:
            lin_attr, _ = _PROJ_ATTRS[name]
            lin = getattr(self, lin_attr)
            zeros = torch.zeros(1, 1, lin.in_features, device=projected_feats.device, dtype=projected_feats.dtype)
            projected_feats = projected_feats + 0 * self._project(name, zeros)[0, 0, :]

        extended_seq_repr = torch.cat([seq_repr, projected_feats], dim=1)
        extended_mask = torch.cat([seq_mask, combined_masks], dim=1)
        return extended_seq_repr, extended_mask
