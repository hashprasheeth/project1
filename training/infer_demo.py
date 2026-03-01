"""
infer_demo.py  —  Inference Demo with Visualized Results
=========================================================
Runs EfficientDet-D5 on test images and draws bounding boxes.
Perfect for demonstrating the model to professors / stakeholders.

Usage
-----
    # Run on test set images
    python infer_demo.py

    # Run on a custom folder
    python infer_demo.py --source path/to/images/

    # Run on a single image
    python infer_demo.py --source path/to/image.jpg

    # Use ONNX model instead of .pth
    python infer_demo.py --onnx ewaste_model/ewaste_d5_best.onnx
"""

import argparse
import glob
import json
import random
import sys
import time
from pathlib import Path

SCRIPT_DIR   = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
REPO_DIR     = SCRIPT_DIR / "Yet-Another-EfficientDet-Pytorch"
DATASET_DIR  = PROJECT_ROOT / "ewaste_model" / "dataset"
CKPT_DIR     = PROJECT_ROOT / "ewaste_model" / "checkpoints"
RESULTS_DIR  = PROJECT_ROOT / "ewaste_model" / "demo_results"

# Colour palette for bounding boxes (one per class, auto-generated)
random.seed(42)


def get_latest_checkpoint() -> Path | None:
    checkpoints = sorted(glob.glob(str(CKPT_DIR / "efficientdet-d5_*.pth")))
    return Path(checkpoints[-1]) if checkpoints else None


def get_class_names() -> list[str]:
    ann_file = DATASET_DIR / "train" / "_annotations.coco.json"
    if not ann_file.exists():
        hits = list(DATASET_DIR.rglob("_annotations.coco.json"))
        ann_file = hits[0] if hits else None

    if ann_file and ann_file.exists():
        with open(ann_file) as f:
            data = json.load(f)
        cats = sorted(data["categories"], key=lambda c: c["id"])
        return [c["name"] for c in cats]
    return [f"ewaste_{i:02d}" for i in range(77)]


def generate_colors(n: int) -> list[tuple]:
    colors = []
    for i in range(n):
        hue = int(360 * i / n)
        # Convert HSV→BGR for OpenCV
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(hue / 360, 0.85, 0.95)
        colors.append((int(b * 255), int(g * 255), int(r * 255)))
    return colors


def run_pth_inference(img_path: Path, model, transform, device, threshold: float):
    """Run inference with PyTorch model, returns (boxes, scores, class_ids)."""
    import torch
    import cv2
    import numpy as np

    img = cv2.imread(str(img_path))
    if img is None:
        return [], [], []

    orig_h, orig_w = img.shape[:2]
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Preprocess
    input_tensor = transform(rgb).unsqueeze(0).to(device)

    with torch.no_grad():
        features, regression, classification, anchors = model(input_tensor)

        # Use EfficientDet's built-in postprocessing
        sys.path.insert(0, str(REPO_DIR))
        from utils.utils import postprocess, invert_affine, preprocess

        out = postprocess(
            input_tensor, anchors, regression, classification,
            regressBoxes=None, clipBoxes=None,
            threshold=threshold, iou_threshold=0.5,
        )

    boxes  = out[0]["rois"].cpu().numpy() if len(out) > 0 and "rois" in out[0] else []
    scores = out[0]["scores"].cpu().numpy() if len(out) > 0 and "scores" in out[0] else []
    ids    = out[0]["class_ids"].cpu().numpy() if len(out) > 0 and "class_ids" in out[0] else []
    return boxes, scores, ids


def draw_boxes(img_bgr, boxes, scores, class_ids, class_names, colors):
    """Draw bounding boxes on image and return annotated copy."""
    import cv2
    import numpy as np

    annotated = img_bgr.copy()
    h, w = annotated.shape[:2]

    for box, score, cls_id in zip(boxes, scores, class_ids):
        cls_id = int(cls_id)
        color = colors[cls_id % len(colors)]
        label = f"{class_names[cls_id] if cls_id < len(class_names) else cls_id}: {score:.2f}"

        x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        # Box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

        # Label background
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(annotated, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
        cv2.putText(annotated, label, (x1 + 2, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    return annotated


def run_demo(source: Path, checkpoint: Path | None, onnx_model: Path | None,
             threshold: float, max_images: int):
    import cv2

    print("\n" + "═" * 60)
    print("  🔍 Untrashify — E-Waste Inference Demo")
    print("═" * 60)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    class_names = get_class_names()
    colors = generate_colors(len(class_names))
    print(f"  Classes    : {len(class_names)}")
    print(f"  Threshold  : {threshold}")
    print(f"  Results dir: {RESULTS_DIR}")

    # Collect image paths
    if source.is_file():
        img_paths = [source]
    else:
        extensions = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp"]
        img_paths = []
        for ext in extensions:
            img_paths += list(source.rglob(ext))
        img_paths = img_paths[:max_images]

    if not img_paths:
        # Fall back to test set
        test_dir = DATASET_DIR / "test" / "images"
        if test_dir.exists():
            for ext in ["*.jpg", "*.jpeg", "*.png"]:
                img_paths += list(test_dir.glob(ext))
            img_paths = img_paths[:max_images]

    if not img_paths:
        print("\n  ✗ No images found. Specify --source or download the dataset first.")
        return

    print(f"  Images     : {len(img_paths)}")

    # ── ONNX inference path ──────────────────────────────────────────────────
    if onnx_model and onnx_model.exists():
        import onnxruntime as ort
        import numpy as np

        print(f"\n  Loading ONNX model: {onnx_model}")
        sess = ort.InferenceSession(str(onnx_model),
                                    providers=["CUDAExecutionProvider",
                                               "CPUExecutionProvider"])
        input_name = sess.get_inputs()[0].name
        print("  ✓ ONNX session ready\n")

        for idx, img_path in enumerate(img_paths):
            img = cv2.imread(str(img_path))
            if img is None:
                continue
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            input_arr = rgb.transpose(2, 0, 1).astype("float32")[None] / 255.0

            t0 = time.perf_counter()
            outputs = sess.run(None, {input_name: input_arr})
            elapsed = (time.perf_counter() - t0) * 1000

            # Minimal post-processing (outputs depend on model export config)
            print(f"  [{idx+1}/{len(img_paths)}] {img_path.name}  ({elapsed:.1f} ms)")

            # Save raw result for now (ONNX post-processing is model-specific)
            out_path = RESULTS_DIR / f"result_{img_path.stem}.jpg"
            cv2.imwrite(str(out_path), img)

        print(f"\n  Results saved to: {RESULTS_DIR}")
        return

    # ── PyTorch inference path ───────────────────────────────────────────────
    sys.path.insert(0, str(REPO_DIR))

    try:
        import torch
        from backbone import EfficientDetBackbone
        from torchvision import transforms
    except ImportError as e:
        print(f"  ✗ {e} — run train_local.py first to clone the repo")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  Device     : {device}")

    if checkpoint is None:
        checkpoint = get_latest_checkpoint()
    if checkpoint is None or not checkpoint.exists():
        print("  ✗ No checkpoint found. Run training first.")
        return

    print(f"  Checkpoint : {checkpoint}\n")

    model = EfficientDetBackbone(
        num_classes=len(class_names),
        compound_coef=5,
        ratios=[(1.0, 1.0), (1.4, 0.7), (0.7, 1.4)],
        scales=[2 ** 0, 2 ** (1.0 / 3.0), 2 ** (2.0 / 3.0)],
    )
    state = torch.load(str(checkpoint), map_location=device)
    if "model" in state:
        state = state["model"]
    model.load_state_dict(state, strict=False)
    model.to(device).eval()

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    total_detections = 0
    for idx, img_path in enumerate(img_paths):
        img = cv2.imread(str(img_path))
        if img is None:
            continue

        t0 = time.perf_counter()
        try:
            boxes, scores, class_ids = run_pth_inference(
                img_path, model, transform, device, threshold)
        except Exception as e:
            print(f"  [{idx+1}] ✗ {img_path.name}: {e}")
            boxes, scores, class_ids = [], [], []

        elapsed = (time.perf_counter() - t0) * 1000
        n_det = len(boxes)
        total_detections += n_det
        print(f"  [{idx+1:3d}/{len(img_paths)}] {img_path.name:<40} "
              f"{n_det:2d} detections  ({elapsed:.0f} ms)")

        annotated = draw_boxes(img, boxes, scores, class_ids, class_names, colors)
        out_path = RESULTS_DIR / f"result_{img_path.stem}.jpg"
        cv2.imwrite(str(out_path), annotated)

    print(f"\n  ══════════════════════════════════════════")
    print(f"  ✅ Demo Complete!")
    print(f"     Images processed : {len(img_paths)}")
    print(f"     Total detections : {total_detections}")
    print(f"     Results saved to : {RESULTS_DIR}")
    print(f"  ══════════════════════════════════════════\n")


def parse_args():
    parser = argparse.ArgumentParser(description="Inference demo for EfficientDet-D5 e-waste model")
    parser.add_argument("--source", type=str, default=None,
                        help="Path to image file or folder (default: test split)")
    parser.add_argument("--checkpoint", type=str, default=None,
                        help="Path to .pth checkpoint (auto-detected if omitted)")
    parser.add_argument("--onnx", type=str, default=None,
                        help="Path to .onnx model (uses ONNX runtime instead of PyTorch)")
    parser.add_argument("--threshold", type=float, default=0.3,
                        help="Detection confidence threshold (default: 0.3)")
    parser.add_argument("--max-images", type=int, default=20,
                        help="Max images to process (default: 20)")
    return parser.parse_args()


def main():
    args = parse_args()

    source = Path(args.source) if args.source else DATASET_DIR / "test" / "images"
    checkpoint = Path(args.checkpoint) if args.checkpoint else None
    onnx_model = Path(args.onnx) if args.onnx else None

    run_demo(source, checkpoint, onnx_model, args.threshold, args.max_images)


if __name__ == "__main__":
    main()
