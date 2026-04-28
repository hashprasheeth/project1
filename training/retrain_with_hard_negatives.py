import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EFFDET_REPO = ROOT / "training" / "Yet-Another-EfficientDet-Pytorch"
REPO_DATASET = EFFDET_REPO / "datasets" / "ewaste"
BASE_DATASET = ROOT / "ewaste_model" / "dataset"
HARD_NEG_LABELED = ROOT / "ewaste_model" / "hard_negative_labeled"
MERGED_DATASET = ROOT / "ewaste_model" / "dataset_plus_hn"
CHECKPOINTS = ROOT / "ewaste_model" / "checkpoints" / "ewaste"


def copy_tree_contents(src: Path, dst: Path):
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


def merge_datasets():
    # If we have no extra labeled hard negatives yet, reuse existing dataset directly.
    if not HARD_NEG_LABELED.exists():
        print(f"No hard-negative labels found at {HARD_NEG_LABELED}.")
        print("Proceeding with existing dataset only.")
        return BASE_DATASET

    if MERGED_DATASET.exists():
        shutil.rmtree(MERGED_DATASET)
    shutil.copytree(BASE_DATASET, MERGED_DATASET)

    for split in ("train", "valid"):
        hn_split = HARD_NEG_LABELED / split
        if not hn_split.exists():
            continue
        dst_split = MERGED_DATASET / split
        copy_tree_contents(hn_split, dst_split)

    print(f"Merged dataset ready: {MERGED_DATASET}")
    return MERGED_DATASET


def run_training(dataset_path: Path):
    # Use junction to avoid long-path copy failures on Windows.
    if REPO_DATASET.exists():
        subprocess.run(["cmd", "/c", "rmdir", str(REPO_DATASET)], capture_output=True, check=False)
        if REPO_DATASET.exists():
            shutil.rmtree(REPO_DATASET, ignore_errors=True)
    REPO_DATASET.parent.mkdir(parents=True, exist_ok=True)
    cmd_mklink = [
        "cmd",
        "/c",
        "mklink",
        "/J",
        str(REPO_DATASET),
        str(dataset_path),
    ]
    link_result = subprocess.run(cmd_mklink, capture_output=True, text=True)
    if link_result.returncode != 0:
        raise RuntimeError(
            f"Failed to create dataset junction.\nSTDOUT: {link_result.stdout}\nSTDERR: {link_result.stderr}"
        )
    print(f"Linked dataset into repo: {REPO_DATASET} -> {dataset_path}")

    # Ensure EfficientDet expected annotation layout exists:
    # datasets/ewaste/annotations/instances_train.json and instances_valid.json
    ann_dir = REPO_DATASET / "annotations"
    ann_dir.mkdir(parents=True, exist_ok=True)
    train_ann_src = dataset_path / "train" / "_annotations.coco.json"
    valid_ann_src = dataset_path / "valid" / "_annotations.coco.json"
    if train_ann_src.exists():
        shutil.copy2(train_ann_src, ann_dir / "instances_train.json")
    if valid_ann_src.exists():
        shutil.copy2(valid_ann_src, ann_dir / "instances_valid.json")
    print(f"Prepared annotation files in: {ann_dir}")

    # Continue from the strongest known checkpoint so far.
    weights = CHECKPOINTS / "efficientdet-d0_0_6860.pth"
    if not weights.exists():
        raise FileNotFoundError(f"Expected checkpoint not found: {weights}")

    cmd = [
        sys.executable,
        "train.py",
        "-c",
        "0",
        "-p",
        "ewaste",
        "--batch_size",
        "2",
        "--lr",
        "5e-4",
        "--num_epochs",
        "8",
        "--load_weights",
        str(weights),
        "--saved_path",
        str(CHECKPOINTS),
        "--num_workers",
        "2",
    ]
    print("Starting retraining with hard negatives...")
    print(" ".join(cmd))
    subprocess.run(cmd, cwd=str(EFFDET_REPO), check=True)


def main():
    dataset_path = merge_datasets()
    run_training(dataset_path)


if __name__ == "__main__":
    main()
