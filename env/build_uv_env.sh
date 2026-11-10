#!/bin/bash
set -e

# ==============================================================================
# Protein Foundation Models - Public UV Environment Installation Script
# ==============================================================================
# Public release variant: installs all Python dependencies by default.
# Does NOT install Foldseek, MMseqs2, Foldcomp, or any NVIDIA-internal binaries.
#
# Usage: ./build_uv_env.sh [OPTIONS] [INSTALL_ROOT]
#
# Options:
#   --clean         Remove existing .venv and UV cache before building (fresh start)
#   --minimal       Skip optional backends (JAX, ColabFold, tmol, Foundry, Modin/Ray)
#   --python VER    Python version: 3.12 (default: 3.12)
#   --name NAME     Custom prompt name shown when venv is activated (default: complexa)
#   --root PATH     Specify installation root directory (where .venv will be created)
#   -h, --help      Show this help message
#
# Examples:
#   ./build_uv_env.sh                      # Full install (Python 3.12)
#   ./build_uv_env.sh --minimal            # Base dependencies only
#   ./build_uv_env.sh --python 3.12        # Full install with Python 3.12
#   ./build_uv_env.sh --name myenv         # Custom prompt: (myenv)
#   ./build_uv_env.sh --root /path/to/dir  # Create .venv in custom directory
# ==============================================================================

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

INSTALL_ROOT=""
FULL_INSTALL=true
CLEAN=false
PYTHON_VERSION="3.12"
VENV_NAME="complexa"

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN=true
            shift
            ;;
        --minimal)
            FULL_INSTALL=false
            shift
            ;;
        --python)
            PYTHON_VERSION="${2:?Missing value for $1}"
            if [[ "$PYTHON_VERSION" != "3.12" ]]; then
                echo "Error: Python version must be 3.12 (required by pyproject.toml)"
                exit 1
            fi
            shift 2
            ;;
        --name)
            VENV_NAME="${2:?Missing value for $1}"
            shift 2
            ;;
        --root)
            INSTALL_ROOT="${2:?Missing value for $1}"
            shift 2
            ;;
        -h|--help)
            echo "Usage: ./build_uv_env.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --clean         Remove existing .venv and UV cache before building"
            echo "  --minimal       Skip optional backends (JAX, ColabFold, tmol, Foundry, Modin/Ray)"
            echo "  --python VER    Python version: 3.12 (default: 3.12)"
            echo "  --name NAME     Custom prompt name (default: complexa)"
            echo "  --root PATH     Specify where to create .venv (default: project dir)"
            echo "  -h, --help      Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./build_uv_env.sh                # Full install (Python 3.12)"
            echo "  ./build_uv_env.sh --minimal      # Base dependencies only"
            echo "  ./build_uv_env.sh --python 3.12  # Full install with Python 3.12"
            exit 0
            ;;
        -*)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
        *)
            if [[ -z "$INSTALL_ROOT" ]]; then
                INSTALL_ROOT="$1"
            else
                echo "Error: Multiple paths specified"
                exit 1
            fi
            shift
            ;;
    esac
done

if [[ -n "$INSTALL_ROOT" ]]; then
    VENV_DIR="$INSTALL_ROOT"
    mkdir -p "$VENV_DIR"
else
    VENV_DIR="$PROJECT_DIR"
fi

cd "$VENV_DIR"

export UV_CACHE_DIR="$VENV_DIR/.uv-cache"
export UV_HTTP_TIMEOUT="${UV_HTTP_TIMEOUT:-120}"

if [[ "$CLEAN" == "true" ]]; then
    echo "Cleaning existing environment and cache..."
    rm -rf "$VENV_DIR/.venv"
    rm -rf "$UV_CACHE_DIR"
    uv cache clean 2>/dev/null || true
    echo "Clean complete."
fi

echo "=============================================="
echo "  Proteina-Complexa - Public Environment Builder"
echo "=============================================="
echo "Project directory: $PROJECT_DIR"
echo "Install directory: $VENV_DIR"
echo "Python version: $PYTHON_VERSION"
echo "Prompt name: $VENV_NAME"
echo "Full install: $FULL_INSTALL"
echo ""

# ------------------------------------------------------------------------------
# 1. Check/Install UV
# ------------------------------------------------------------------------------
if ! command -v uv &> /dev/null; then
    echo "[1/7] Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "[1/7] uv already installed: $(uv --version)"
fi

# ------------------------------------------------------------------------------
# 2. Create virtual environment
# ------------------------------------------------------------------------------
echo "[2/7] Creating virtual environment with Python $PYTHON_VERSION..."
uv venv --python "$PYTHON_VERSION" --prompt "$VENV_NAME" "$VENV_DIR/.venv"

source "$VENV_DIR/.venv/bin/activate"
echo "      Python: $(which python)"

# ------------------------------------------------------------------------------
# 3. Install PyTorch with CUDA 12.6
# ------------------------------------------------------------------------------
echo "[3/7] Installing PyTorch 2.7.0 with CUDA 12.6..."
uv pip install --constraint "$PROJECT_DIR/env/constraints.txt" torch==2.7.0+cu126 \
    --index-url https://download.pytorch.org/whl/cu126

# ------------------------------------------------------------------------------
# 4. Resolve base dependencies together (including Graphein and Atomworks)
# ------------------------------------------------------------------------------
echo "[4/7] Installing base dependencies from pyproject.toml..."
uv pip install --constraint "$PROJECT_DIR/env/constraints.txt" --index-strategy unsafe-best-match -e "$PROJECT_DIR"

# ------------------------------------------------------------------------------
# 5. Install the only required PyTorch Geometric extension
# ------------------------------------------------------------------------------
echo "[5/7] Installing torch-scatter from a matching CUDA wheel..."
uv pip install --constraint "$PROJECT_DIR/env/constraints.txt" torch_scatter --only-binary=:all: \
    -f https://data.pyg.org/whl/torch-2.7.0+cu126.html

# ------------------------------------------------------------------------------
# 6. Install optional/full dependencies
# ------------------------------------------------------------------------------
if [ "$FULL_INSTALL" = true ]; then
    echo "[6/7] Installing full dependencies (ColabFold, JAX, tmol, Foundry, Modin/Ray)..."

    # Resolve JAX and its ecosystem together: sequential downgrades leave newer
    # chex/optax/ml-dtypes installed against an incompatible JAX or NumPy.
    uv pip install --constraint "$PROJECT_DIR/env/constraints.txt" \
        -e "$PROJECT_DIR[data-prep]" \
        colabdesign==1.1.1 alphafold-colabfold==2.3.7 \
        "jax[cuda12]==0.4.29" jaxlib==0.4.29+cuda12.cudnn91 flax==0.9.0 \
        "rc-foundry[all]" \
        -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html

    echo "      -> Installing local colabdesign (community_models/colabdesign)..."
    uv pip install --constraint "$PROJECT_DIR/env/constraints.txt" -e "$PROJECT_DIR/community_models/colabdesign"

    echo "      -> Tmol..."
    uv pip install --constraint "$PROJECT_DIR/env/constraints.txt" "git+https://github.com/uw-ipd/tmol.git@d8a6f7f9649d36e74440bca25246ee7c467ce490" || echo "Warning: tmol install failed"
else
    echo "[6/7] Skipping optional dependencies (omit --minimal to install)"
fi

# ------------------------------------------------------------------------------
# 7. Verify dependency consistency
# ------------------------------------------------------------------------------
echo "[7/7] Checking installed dependencies..."
uv pip check

# ------------------------------------------------------------------------------
# Done!
# ------------------------------------------------------------------------------
echo ""
echo "=============================================="
echo "  Installation Complete!"
echo "=============================================="
echo ""
echo "To activate the environment:"
echo "  source $VENV_DIR/.venv/bin/activate"
echo ""
echo "To verify installation:"
echo "  python -c \"import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')\""
echo ""
echo "Note: Foldseek and MMseqs2 are not included in the public build."
echo "Install them separately if needed:"
echo "  wget https://mmseqs.com/foldseek/foldseek-linux-gpu.tar.gz"
echo "  wget https://mmseqs.com/latest/mmseqs-linux-gpu.tar.gz"
