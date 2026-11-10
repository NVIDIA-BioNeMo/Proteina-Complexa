"""Run after installation: python env/smoke_test.py [--minimal | --af2] [--cuda].

Exercises imports and compiled operators without downloading model weights.
"""

import argparse
import importlib
import importlib.metadata
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--minimal", action="store_true", help="Check optional packages are absent")
    mode.add_argument("--af2", action="store_true", help="Also check AF2 imports and JAX computation")
    parser.add_argument("--cuda", action="store_true", help="Require and exercise a CUDA GPU")
    args = parser.parse_args()

    if args.minimal:
        for package in (
            "torchaudio",
            "torchvision",
            "torch-geometric",
            "torch-sparse",
            "torch-cluster",
            "jax",
            "jaxlib",
            "rc-foundry",
            "tmol",
            "modin",
            "ray",
        ):
            try:
                importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                continue
            raise AssertionError(f"Unexpected package in minimal environment: {package}")

    import torch
    from torch_scatter import scatter_mean

    assert torch.__version__ == "2.7.0+cu126", torch.__version__
    if args.cuda:
        assert torch.cuda.is_available(), "CUDA is unavailable"
    device = "cuda" if args.cuda else "cpu"
    values = torch.tensor([1.0, 3.0, 6.0], device=device, requires_grad=True)
    indices = torch.tensor([0, 0, 1], device=device)
    result = scatter_mean(values, indices)
    torch.testing.assert_close(result, torch.tensor([2.0, 6.0], device=device))
    result.sum().backward()
    torch.testing.assert_close(values.grad, torch.tensor([0.5, 0.5, 1.0], device=device))
    matrix = torch.randn(32, 32, device=device)
    assert torch.isfinite(matrix @ matrix.T).all()

    for module in (
        "lightning",
        "proteinfoundation.generate",
        "proteinfoundation.train",
        "proteinfoundation.datasets.pipelines.complexa_ligand",
        "proteinfoundation.search.search_factory",
    ):
        importlib.import_module(module)
        print(f"Imported {module}")

    import numpy as np
    from biotite.structure import AtomArray

    from proteinfoundation.utils.cluster_utils import fasta_to_df
    from proteinfoundation.utils.pdb_utils import AtomSelectionStack

    # The Atomworks 3 query module must retain the target contig syntax we use.
    atoms = AtomArray(4)
    atoms.chain_id = np.array(["A", "A", "A", "B"])
    atoms.res_id = np.array([1, 2, 3, 1])
    atoms.res_name = np.array(["ALA"] * 4)
    atoms.atom_name = np.array(["CA"] * 4)
    selection = AtomSelectionStack.from_contig("A1-2, B1-1")
    np.testing.assert_array_equal(selection.get_mask(atoms), [True, True, False, True])

    with tempfile.TemporaryDirectory() as directory:
        fasta = Path(directory) / "example.fasta"
        fasta.write_text(">example\nACD\nEF\n")
        frame = fasta_to_df(str(fasta))
        assert frame.to_dict("records") == [{"id": "example", "sequence": "ACDEF"}]
    if args.af2:
        import jax
        import jax.numpy as jnp

        importlib.import_module("proteinfoundation.search.sequence_hallucination")
        importlib.import_module("proteinfoundation.rewards.alphafold2_reward")
        assert jax.__version__ == "0.4.29", jax.__version__
        if args.cuda:
            assert any(device.platform == "gpu" for device in jax.devices()), "JAX GPU unavailable"
        result = jax.jit(lambda x: x @ x)(jnp.ones((4, 4))).block_until_ready()
        np.testing.assert_allclose(np.asarray(result), np.full((4, 4), 4.0))
        print(f"AF2 imports and JAX computation passed: {jax.devices()}")

    print(f"Environment smoke test passed: torch={torch.__version__}, device={device}")


if __name__ == "__main__":
    main()
