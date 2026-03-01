"""
export_onnx.py  —  Export Trained EfficientDet-D5 Checkpoint to ONNX
=====================================================================
Run after training to produce a deployment-ready ONNX model.

Usage
-----
    python export_onnx.py --checkpoint ewaste_model/checkpoints/efficientdet-d5_5.pth
    python export_onnx.py --checkpoint <path>.pth --num-classes 77 --input-size 1280
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

SCRIPT_DIR   = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
REPO_DIR     = SCRIPT_DIR / "Yet-Another-EfficientDet-Pytorch"
DATASET_DIR  = PROJECT_ROOT / "ewaste_model" / "dataset"
OUTPUT_DIR   = PROJECT_ROOT / "ewaste_model"
TRITON_DEST  = PROJECT_ROOT / "triton_model_repo" / "efficientdet_d5" / "1"


def get_num_classes_from_dataset() -> int:
    """Auto-detect class count from dataset annotation file."""
    ann_file = DATASET_DIR / "train" / "_annotations.coco.json"
    if not ann_file.exists():
        hits = list(DATASET_DIR.rglob("_annotations.coco.json"))
        if not hits:
            return 77  # fallback
        ann_file = hits[0]
    with open(ann_file) as f:
        data = json.load(f)
    return len(data.get("categories", []))


def export_to_onnx(checkpoint_path: Path, num_classes: int, input_size: int):
    # Add repo to path so we can import EfficientDet modules
    sys.path.insert(0, str(REPO_DIR))

    try:
        import torch
        import onnx
    except ImportError as e:
        print(f"  [ERR] Missing dependency: {e}")
        print("  Run: pip install torch onnx")
        sys.exit(1)

    try:
        from backbone import EfficientDetBackbone
    except ImportError:
        print(f"  [ERR] Could not import EfficientDetBackbone from repo: {REPO_DIR}")
        print("  Make sure the repo is cloned (run train_local.py first)")
        sys.exit(1)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  Device      : {device}")
    print(f"  Checkpoint  : {checkpoint_path}")
    print(f"  Num classes : {num_classes}")
    print(f"  Input size  : {input_size}x{input_size}")

    # Build model
    model = EfficientDetBackbone(
        num_classes=num_classes,
        compound_coef=0,
        ratios=[(1.0, 1.0), (1.4, 0.7), (0.7, 1.4)],
        scales=[2 ** 0, 2 ** (1.0 / 3.0), 2 ** (2.0 / 3.0)],
    )

    print("\n  Loading checkpoint ...")
    state = torch.load(str(checkpoint_path), map_location=device, weights_only=False)
    if "model" in state:
        state = state["model"]
    model.load_state_dict(state, strict=False)
    model.to(device).eval()
    print("  [OK] Checkpoint loaded")

    # Dummy input for tracing
    dummy_input = torch.randn(1, 3, input_size, input_size, device=device)

    onnx_path = OUTPUT_DIR / "ewaste_d0_best.onnx"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n  Exporting to ONNX -> {onnx_path} ...")
    torch.onnx.export(
        model,
        dummy_input,
        str(onnx_path),
        export_params=True,
        opset_version=12,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["classification", "regression", "anchors"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "classification": {0: "batch_size"},
            "regression": {0: "batch_size"},
        },
    )

    print("  Validating ONNX graph ...")
    onnx_model = onnx.load(str(onnx_path))
    onnx.checker.check_model(onnx_model)
    size_mb = onnx_path.stat().st_size / 1_048_576
    print(f"  [OK] ONNX model valid  ({size_mb:.1f} MB)")

    TRITON_DEST.mkdir(parents=True, exist_ok=True)
    triton_path = TRITON_DEST / "model.onnx"
    shutil.copy2(onnx_path, triton_path)
    print(f"  [OK] Copied to Triton  : {triton_path}")

    print("\n  ==========================================")
    print("  ONNX Export Complete!")
    print("  ==========================================")
    print(f"  ONNX file   : {onnx_path}")
    print(f"  Triton dest : {triton_path}")
    print(f"  Input shape : [batch, 3, {input_size}, {input_size}]")
    print(f"  Classes     : {num_classes}")
    print("\n  Next: start the backend to load the model automatically")


def parse_args():
    parser = argparse.ArgumentParser(description="Export EfficientDet-D5 checkpoint to ONNX")
    parser.add_argument("--checkpoint", type=str, required=True,
                        help="Path to .pth checkpoint file")
    parser.add_argument("--num-classes", type=int, default=None,
                        help="Number of classes (auto-detected if not specified)")
    parser.add_argument("--input-size", type=int, default=512,
                        help="Model input resolution (default 512 for D0)")
    return parser.parse_args()


def main():
    args = parse_args()

    checkpoint_path = Path(args.checkpoint)
    if not checkpoint_path.exists():
        print(f"  [ERR] Checkpoint not found: {checkpoint_path}")
        sys.exit(1)

    num_classes = args.num_classes or get_num_classes_from_dataset()
    export_to_onnx(checkpoint_path, num_classes, args.input_size)


if __name__ == "__main__":
    main()
