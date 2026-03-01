"""
E-Waste COCO Dataset Loader
PyTorch Dataset class compatible with Yet-Another-EfficientDet-Pytorch training loop.
"""

import os
import cv2
import json
import torch
import numpy as np
from pathlib import Path
from torch.utils.data import Dataset


class EWasteCocoDataset(Dataset):
    """
    COCO-format dataset for e-waste detection.
    Returns images and annotations in the format expected by EfficientDet.
    """

    def __init__(self, root_dir: str, split: str = "train", transform=None):
        """
        Args:
            root_dir: Path to the downloaded dataset root (contains train/valid/test folders)
            split:    'train', 'valid', or 'test'
            transform: Optional albumentations/torchvision transforms
        """
        self.root_dir = Path(root_dir)
        self.split = split
        self.transform = transform

        # Resolve split folder name (Roboflow uses 'valid' not 'val')
        split_dir = self.root_dir / split
        if not split_dir.exists():
            # Try alternate names
            for alt in ("val", "validation", "test"):
                if (self.root_dir / alt).exists():
                    split_dir = self.root_dir / alt
                    break

        self.img_dir = split_dir / "images"
        ann_file = split_dir / "_annotations.coco.json"

        if not ann_file.exists():
            raise FileNotFoundError(
                f"Annotation file not found: {ann_file}\n"
                f"Make sure the dataset was downloaded correctly."
            )

        with open(ann_file, "r") as f:
            coco_data = json.load(f)

        # Build category id → index mapping (0-indexed for model)
        categories = sorted(coco_data["categories"], key=lambda x: x["id"])
        self.class_names = [cat["name"] for cat in categories]
        self.cat_id_to_idx = {cat["id"]: idx for idx, cat in enumerate(categories)}
        self.num_classes = len(categories)

        # Index images
        self.images = {img["id"]: img for img in coco_data["images"]}
        self.img_ids = [img["id"] for img in coco_data["images"]]

        # Index annotations by image id
        self.anns = {}
        for ann in coco_data.get("annotations", []):
            img_id = ann["image_id"]
            if img_id not in self.anns:
                self.anns[img_id] = []
            self.anns[img_id].append(ann)

        print(
            f"[EWasteCocoDataset] Loaded {split} set: "
            f"{len(self.img_ids)} images, {self.num_classes} classes"
        )

    def __len__(self):
        return len(self.img_ids)

    def __getitem__(self, idx):
        img_id = self.img_ids[idx]
        img_info = self.images[img_id]
        img_path = self.img_dir / img_info["file_name"]

        # Load image as RGB
        img = cv2.imread(str(img_path))
        if img is None:
            raise RuntimeError(f"Could not load image: {img_path}")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        orig_h, orig_w = img.shape[:2]

        # Build annotation arrays  [x1, y1, x2, y2, class_idx]
        annotations = np.zeros((0, 5), dtype=np.float32)
        if img_id in self.anns:
            rows = []
            for ann in self.anns[img_id]:
                if ann.get("iscrowd", 0):
                    continue
                x, y, w, h = ann["bbox"]
                x2 = x + w
                y2 = y + h
                cls_idx = self.cat_id_to_idx.get(ann["category_id"], 0)
                rows.append([x, y, x2, y2, cls_idx])
            if rows:
                annotations = np.array(rows, dtype=np.float32)

        if self.transform:
            sample = self.transform(image=img, bboxes=annotations[:, :4], labels=annotations[:, 4])
            img = sample["image"]
            bboxes = np.array(sample["bboxes"], dtype=np.float32)
            labels = np.array(sample["labels"], dtype=np.float32)
            if len(bboxes) > 0:
                annotations = np.concatenate([bboxes, labels[:, None]], axis=1)
            else:
                annotations = np.zeros((0, 5), dtype=np.float32)

        # Convert to tensors
        img_tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
        ann_tensor = torch.from_numpy(annotations)

        return img_tensor, ann_tensor, img_id

    def get_class_names(self):
        return self.class_names


def collate_fn(batch):
    """Custom collate for variable-size annotation tensors."""
    images, annotations, img_ids = zip(*batch)
    images = torch.stack(images, dim=0)
    return images, list(annotations), list(img_ids)
