"""
train_local.py  -  EfficientDet-D5 Fine-Tuning on E-Waste Dataset
==================================================================
One-stop training script for local Windows execution. No git required.

Usage
-----
    # Full demo run (5 epochs, auto-downloads dataset & weights)
    python train_local.py

    # Download dataset only (no training yet)
    python train_local.py --download-only

    # Custom epochs / batch size
    python train_local.py --epochs 10 --batch-size 1

    # Skip dataset download if already present
    python train_local.py --skip-download --epochs 5
"""

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

# -----------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------
SCRIPT_DIR   = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
REPO_DIR     = SCRIPT_DIR / "Yet-Another-EfficientDet-Pytorch"
DATASET_DIR  = PROJECT_ROOT / "ewaste_model" / "dataset"
CKPT_DIR     = PROJECT_ROOT / "ewaste_model" / "checkpoints"
PROJECTS_DIR = SCRIPT_DIR / "projects"

ROBOFLOW_API_KEY   = "J5X5BymTiaxtbKzjd80N"
ROBOFLOW_WORKSPACE = "electronic-waste-detection"
ROBOFLOW_PROJECT   = "e-waste-dataset-r0ojc"
ROBOFLOW_VERSION   = 44

# Official EfficientDet-D0 COCO pretrained weights (~15 MB)
D0_WEIGHTS_URL  = (
    "https://github.com/zylo117/Yet-Another-EfficientDet-Pytorch"
    "/releases/download/1.0/efficientdet-d0.pth"
)
D0_WEIGHTS_PATH = CKPT_DIR / "efficientdet-d0.pth"

# GitHub ZIP (no git required)
REPO_ZIP_URL = (
    "https://github.com/zylo117/Yet-Another-EfficientDet-Pytorch"
    "/archive/refs/heads/master.zip"
)


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def banner(msg: str):
    sep = "=" * 62
    print(f"\n{sep}\n  {msg}\n{sep}")


def run_cmd(cmd: list, cwd=None):
    """Run a subprocess and stream output; exit on failure."""
    print(f"\n>>> {' '.join(str(c) for c in cmd)}\n")
    result = subprocess.run(cmd, cwd=str(cwd or REPO_DIR))
    if result.returncode != 0:
        print(f"\n[FAIL] Command failed (exit {result.returncode})")
        sys.exit(result.returncode)


def download_file(url: str, dest: Path, desc: str):
    """Download a file with a simple ASCII progress indicator."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        size_mb = dest.stat().st_size / 1_048_576
        print(f"  [OK] Already exists: {dest.name} ({size_mb:.1f} MB) - skipping")
        return

    print(f"  Downloading {desc} ...")
    print(f"    URL : {url}")
    print(f"    Dest: {dest}")

    last_pct = [-1]

    def _progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            pct = min(100, downloaded * 100 // total_size)
            if pct != last_pct[0]:
                bar = "#" * (pct // 5) + "." * (20 - pct // 5)
                print(f"\r    [{bar}] {pct}%", end="", flush=True)
                last_pct[0] = pct

    urllib.request.urlretrieve(url, dest, reporthook=_progress)
    print()  # newline after progress bar
    size_mb = dest.stat().st_size / 1_048_576
    print(f"  [OK] Downloaded: {dest.name} ({size_mb:.1f} MB)")


# -----------------------------------------------------------------------
# Step 1 - Download EfficientDet repo as ZIP (no git required)
# -----------------------------------------------------------------------

def clone_efficientdet():
    banner("Step 1/6 - Download EfficientDet Repository (ZIP)")
    if REPO_DIR.exists() and (REPO_DIR / "train.py").exists():
        print(f"  [OK] Repo already present: {REPO_DIR}")
        return

    zip_path    = SCRIPT_DIR / "efficientdet_repo.zip"
    extract_dir = SCRIPT_DIR / "_efficientdet_extract"

    print("  Downloading Yet-Another-EfficientDet-Pytorch ...")
    print("  (no git required - pure Python download)")
    download_file(REPO_ZIP_URL, zip_path, "EfficientDet source code (~5-10 MB)")

    print("\n  Extracting ZIP ...")
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)

    # GitHub ZIPs contain a top-level folder like "Yet-Another-EfficientDet-Pytorch-master"
    extracted_folders = [d for d in extract_dir.iterdir() if d.is_dir()]
    if not extracted_folders:
        print("  [FAIL] ZIP extraction produced no folders - aborting")
        sys.exit(1)
    inner_dir = extracted_folders[0]

    if REPO_DIR.exists():
        shutil.rmtree(REPO_DIR)
    shutil.move(str(inner_dir), str(REPO_DIR))
    shutil.rmtree(extract_dir, ignore_errors=True)
    zip_path.unlink(missing_ok=True)
    print(f"  [OK] Repo ready at: {REPO_DIR}")

    # Install the repo's own requirements
    print("\n  Installing repo dependencies ...")
    req_file = REPO_DIR / "requirements.txt"
    if req_file.exists():
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-r", str(req_file)],
            check=False
        )
    else:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q",
             "pycocotools", "webcolors", "tensorboard", "tensorboardX"],
            check=False
        )
    print("  [OK] EfficientDet repo ready")


# -----------------------------------------------------------------------
# Step 2 - Download Roboflow dataset
# -----------------------------------------------------------------------

def download_dataset():
    banner("Step 2/6 - Download E-Waste Dataset from Roboflow")

    ann_file = DATASET_DIR / "train" / "_annotations.coco.json"
    if ann_file.exists():
        print(f"  [OK] Dataset already present: {DATASET_DIR}")
        return

    try:
        from roboflow import Roboflow
    except ImportError:
        print("  Installing roboflow ...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "roboflow"], check=True)
        from roboflow import Roboflow

    # Windows has a 260-character MAX_PATH limit.
    # Roboflow image filenames are very long, so we download to a short root path
    # to avoid hitting the limit, then move the dataset into the project.
    SHORT_DL_PATH = Path("C:/rf_ewaste")
    SHORT_DL_PATH.mkdir(parents=True, exist_ok=True)

    print(f"  Workspace : {ROBOFLOW_WORKSPACE}")
    print(f"  Project   : {ROBOFLOW_PROJECT}")
    print(f"  Version   : {ROBOFLOW_VERSION}")
    print(f"  Format    : COCO")
    print(f"  Short DL  : {SHORT_DL_PATH}  (avoids Windows 260-char path limit)")
    print(f"  Final dest: {DATASET_DIR}")

    rf      = Roboflow(api_key=ROBOFLOW_API_KEY)
    project = rf.workspace(ROBOFLOW_WORKSPACE).project(ROBOFLOW_PROJECT)
    version = project.version(ROBOFLOW_VERSION)

    # Download to short path
    original_cwd = os.getcwd()
    os.chdir(SHORT_DL_PATH)
    ds = version.download("coco")
    os.chdir(original_cwd)

    # Find where Roboflow actually put it
    candidates = [d for d in SHORT_DL_PATH.iterdir() if d.is_dir()]
    if not candidates:
        print("  [FAIL] Roboflow download produced no folder - check internet connection")
        sys.exit(1)
    dl_dir = candidates[0]
    print(f"  Downloaded to: {dl_dir}")

    # Move to project dataset directory
    DATASET_DIR.parent.mkdir(parents=True, exist_ok=True)
    if DATASET_DIR.exists():
        shutil.rmtree(DATASET_DIR)
    shutil.move(str(dl_dir), str(DATASET_DIR))

    # Clean up short path
    shutil.rmtree(SHORT_DL_PATH, ignore_errors=True)

    print(f"  [OK] Dataset moved to: {DATASET_DIR}")


# -----------------------------------------------------------------------
# Step 3 - Read class names from COCO JSON
# -----------------------------------------------------------------------

def read_class_names() -> list:
    banner("Step 3/6 - Reading Class Names from Dataset")

    ann_file = DATASET_DIR / "train" / "_annotations.coco.json"
    if not ann_file.exists():
        hits = list(DATASET_DIR.rglob("_annotations.coco.json"))
        if not hits:
            print("  [WARN] Annotation not found - using 77 generic class names")
            return [f"ewaste_{i:02d}" for i in range(77)]
        ann_file = hits[0]

    with open(ann_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    categories  = sorted(data["categories"], key=lambda c: c["id"])
    class_names = [c["name"] for c in categories]
    print(f"  [OK] {len(class_names)} classes found:")
    for i, name in enumerate(class_names):
        print(f"    [{i:3d}] {name}")
    return class_names


# -----------------------------------------------------------------------
# Step 4 - Write EfficientDet project config (ewaste.yml)
# -----------------------------------------------------------------------

def write_config(class_names: list):
    banner("Step 4/6 - Writing EfficientDet Project Config")

    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    config_path = PROJECTS_DIR / "ewaste.yml"

    # EfficientDet train.py builds annotation path as:
    #   {data_path}/{project}/annotations/instances_{train_set}.json
    # So train_set / val_set must be SHORT split names, NOT full paths.
    valid_split = "valid" if (DATASET_DIR / "valid").exists() else "val"

    lines = [
        "project_name: ewaste",
        "train_set: train",
        f"val_set: {valid_split}",
        "num_gpus: 1",
        f"num_classes: {len(class_names)}",
        "compound_coef: 0",
        "",
        "mean: [0.485, 0.456, 0.406]",
        "std: [0.229, 0.224, 0.225]",
        "",
        "anchors_scales: '[2 ** 0, 2 ** (1.0 / 3.0), 2 ** (2.0 / 3.0)]'",
        "anchors_ratios: '[(1.0, 1.0), (1.4, 0.7), (0.7, 1.4)]'",
        "",
        "obj_list:",
    ] + [f"  - '{n}'" for n in class_names]

    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  [OK] Config: {config_path}")
    print(f"       Classes   : {len(class_names)}")
    print(f"       train_set : train")
    print(f"       val_set   : {valid_split}")
    return config_path


# -----------------------------------------------------------------------
# Step 5 - Download pretrained EfficientDet-D0 COCO weights
# -----------------------------------------------------------------------

def download_pretrained_weights():
    banner("Step 5/6 - Download Pretrained EfficientDet-D0 Weights")
    CKPT_DIR.mkdir(parents=True, exist_ok=True)
    download_file(D0_WEIGHTS_URL, D0_WEIGHTS_PATH, "EfficientDet-D0 COCO pretrained (~15 MB)")

    # Copy into repo weights/ so train.py finds them
    repo_weights = REPO_DIR / "weights"
    repo_weights.mkdir(exist_ok=True)
    dest = repo_weights / "efficientdet-d0.pth"
    if not dest.exists():
        shutil.copy2(D0_WEIGHTS_PATH, dest)
        print(f"  [OK] Copied weights to repo weights/")


# -----------------------------------------------------------------------
# Step 6a - Prepare dataset directory layout expected by EfficientDet
# -----------------------------------------------------------------------

def prepare_dataset_for_repo():
    """
    YAEDPytorch train.py expects:
        datasets/ewaste/train/             <- images
        datasets/ewaste/valid/             <- images
        datasets/ewaste/annotations/
            instances_train.json
            instances_valid.json
    """
    banner("Step 6a/6 - Preparing Dataset Layout for EfficientDet")

    repo_ds    = REPO_DIR / "datasets" / "ewaste"
    repo_ann   = repo_ds / "annotations"
    repo_ds.mkdir(parents=True, exist_ok=True)
    repo_ann.mkdir(exist_ok=True)

    for split, rf_split in [("train", "train"), ("valid", "valid"), ("val", "valid")]:
        # Roboflow COCO may place images in split/images/ OR directly in split/
        src_img_sub  = DATASET_DIR / rf_split / "images"
        src_img_root = DATASET_DIR / rf_split
        if src_img_sub.exists():
            src_img = src_img_sub
        elif src_img_root.exists() and any(
            f.suffix in (".jpg", ".jpeg", ".png")
            for f in src_img_root.iterdir()
        ):
            src_img = src_img_root
        else:
            continue

        dst_img = repo_ds / split

        # Remove any stale junction/symlink first (broken junctions need rmdir on Windows)
        subprocess.run(["cmd", "/c", "rmdir", str(dst_img)], capture_output=True, check=False)
        if dst_img.is_symlink():
            dst_img.unlink(missing_ok=True)

        # Skip if destination already has image files (real directory from prior copy)
        if dst_img.is_dir() and any(
            f.suffix.lower() in (".jpg", ".jpeg", ".png")
            for f in dst_img.iterdir() if f.is_file()
        ):
            print(f"  [OK] {split}/ already has images - skipping")
        elif not dst_img.exists():
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(dst_img), str(src_img.resolve())],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"  [OK] Junction {split}/ -> {src_img}")
            else:
                try:
                    dst_img.symlink_to(src_img.resolve(), target_is_directory=True)
                    print(f"  [OK] Linked {split}/ -> {src_img}")
                except OSError:
                    print(f"  Copying {split}/ images ...")
                    shutil.copytree(src_img, dst_img)
                    print(f"  [OK] Copied {split}/")

        src_ann = DATASET_DIR / rf_split / "_annotations.coco.json"
        dst_ann = repo_ann / f"instances_{split}.json"
        if src_ann.exists() and not dst_ann.exists():
            shutil.copy2(src_ann, dst_ann)
            print(f"  [OK] Annotations: instances_{split}.json")

    print("  [OK] Dataset layout ready")


# -----------------------------------------------------------------------
# Step 6b - Run training
# -----------------------------------------------------------------------

def run_training(num_epochs: int, class_names: list, batch_size: int = 4, head_only: bool = True):
    banner(f"Step 6b/6 - Training EfficientDet-D0 for {num_epochs} Epoch(s)")

    CKPT_DIR.mkdir(parents=True, exist_ok=True)
    log_dir = PROJECT_ROOT / "ewaste_model" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "train.py",
        "-c", "0",
        "-p", "ewaste",
        "--batch_size", str(batch_size),
        "--lr", "1e-3",
        "--num_epochs", str(num_epochs),
        "--load_weights", "weights/efficientdet-d0.pth",
        "--saved_path", str(CKPT_DIR),
        "--log_path",   str(log_dir),
        "--head_only",  str(head_only),
        "--num_workers", "2",
    ]

    print(f"  Batch size  : {batch_size}")
    print(f"  Head only   : {head_only}")
    print(f"  Epochs      : {num_epochs}")
    print(f"  Checkpoints : {CKPT_DIR}")
    run_cmd(cmd, cwd=REPO_DIR)

    checkpoints = sorted(glob.glob(str(CKPT_DIR / "efficientdet-d0_*.pth")))
    if checkpoints:
        best = checkpoints[-1]
        print(f"\n  [OK] Latest checkpoint: {best}")
        return Path(best)
    else:
        print("  [WARN] No checkpoint files found - check training logs")
        return None


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description="EfficientDet-D5 E-Waste Fine-Tuning - Local Training Script"
    )
    p.add_argument("--epochs",         type=int, default=5,
                   help="Training epochs (default: 5 for demo)")
    p.add_argument("--batch-size",     type=int, default=2,
                   help="Batch size (default: 2 for 4GB VRAM; use 4+ with 6GB+)")
    p.add_argument("--head-only",      action="store_true", default=True,
                   help="Freeze backbone, train only BiFPN+head (saves ~60%% VRAM)")
    p.add_argument("--full-finetune",  action="store_true",
                   help="Unfreeze backbone for full fine-tuning (needs 6GB+ VRAM)")
    p.add_argument("--download-only",  action="store_true",
                   help="Only download dataset, skip training")
    p.add_argument("--skip-download",  action="store_true",
                   help="Skip dataset download (use existing data)")
    p.add_argument("--skip-export",    action="store_true",
                   help="Skip ONNX export after training")
    return p.parse_args()


def main():
    args = parse_args()

    print("\n" + "=" * 62)
    print("  Untrashify - EfficientDet-D0 E-Waste Training Pipeline")
    print("=" * 62)
    print(f"  Project root : {PROJECT_ROOT}")
    print(f"  Dataset dir  : {DATASET_DIR}")
    print(f"  Checkpoints  : {CKPT_DIR}")
    print(f"  Epochs       : {args.epochs}")
    print(f"  Batch size   : {args.batch_size}")

    clone_efficientdet()

    if not args.skip_download:
        download_dataset()
    else:
        print("\n  [skip-download] Using existing dataset")

    if args.download_only:
        print("\n[OK] Dataset download complete. Run without --download-only to train.")
        return

    class_names = read_class_names()
    write_config(class_names)
    download_pretrained_weights()
    prepare_dataset_for_repo()

    # Copy project config into the repo so train.py picks it up
    dst_proj = REPO_DIR / "projects" / "ewaste.yml"
    dst_proj.parent.mkdir(exist_ok=True)
    shutil.copy2(PROJECTS_DIR / "ewaste.yml", dst_proj)
    print(f"  [OK] Project config copied to repo: {dst_proj}")

    head_only = not args.full_finetune
    checkpoint_path = run_training(args.epochs, class_names, args.batch_size, head_only)

    # Auto-export to ONNX
    if checkpoint_path and not args.skip_export:
        banner("Post-Training - Auto ONNX Export")
        export_script = SCRIPT_DIR / "export_onnx.py"
        if export_script.exists():
            run_cmd([
                sys.executable, str(export_script),
                "--checkpoint",  str(checkpoint_path),
                "--num-classes", str(len(class_names)),
            ])
        else:
            print("  export_onnx.py not found - run manually after training")

    print("\n" + "=" * 62)
    print("  Training pipeline complete!")
    print("=" * 62)
    if checkpoint_path:
        print(f"  Checkpoint : {checkpoint_path}")
    onnx_path = PROJECT_ROOT / "ewaste_model" / "ewaste_d0_best.onnx"
    if onnx_path.exists():
        print(f"  ONNX model : {onnx_path}")
    print("\n  Next steps:")
    print("    1. Run inference demo:  python infer_demo.py")
    print("    2. Deploy via Docker:   docker-compose up")
    print("=" * 62 + "\n")


if __name__ == "__main__":
    main()
