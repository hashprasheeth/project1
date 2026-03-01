import sys
import numpy as np
import cv2
from pathlib import Path
from fastapi import HTTPException
from backend.core.config import settings
from backend.core.logger import logger

REPO_DIR = Path(__file__).parent.parent.parent / "training" / "Yet-Another-EfficientDet-Pytorch"


class PyTorchInferenceService:
    def __init__(self):
        self.model = None
        self.device = None

    def load_model(self):
        if self.model is not None:
            return

        if str(REPO_DIR) not in sys.path:
            sys.path.insert(0, str(REPO_DIR))

        try:
            import torch
            from backbone import EfficientDetBackbone

            self.device = "cuda" if torch.cuda.is_available() else "cpu"

            model = EfficientDetBackbone(
                num_classes=len(settings.CLASSES),
                compound_coef=0,
                ratios=[(1.0, 1.0), (1.4, 0.7), (0.7, 1.4)],
                scales=[2 ** 0, 2 ** (1.0 / 3.0), 2 ** (2.0 / 3.0)],
            )

            ckpt_path = settings.CHECKPOINT_PATH
            if not ckpt_path.exists():
                raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")

            state = torch.load(str(ckpt_path), map_location=self.device, weights_only=False)
            if "model" in state:
                state = state["model"]
            model.load_state_dict(state, strict=False)
            model.to(self.device).eval()
            model.requires_grad_(False)
            self.model = model

            logger.info("pytorch_model_loaded", extra={
                "checkpoint": str(ckpt_path),
                "device": self.device,
                "num_classes": len(settings.CLASSES),
            })

        except Exception as e:
            logger.error("model_load_failed", extra={"error": str(e)})
            raise HTTPException(status_code=503, detail=f"Model load failed: {e}")

    def preprocess(self, image_bytes: bytes) -> tuple:
        """Decode, resize with aspect-aware padding, normalize for EfficientDet."""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Could not decode image")

            orig_h, orig_w = img.shape[:2]
            input_size = settings.MODEL_INPUT_SIZE

            img_rgb = img[:, :, ::-1].astype(np.float32) / 255.0
            mean = np.array(settings.IMAGE_MEAN, dtype=np.float32)
            std = np.array(settings.IMAGE_STD, dtype=np.float32)
            img_normalized = (img_rgb - mean) / std

            if orig_w > orig_h:
                new_w = input_size
                new_h = int(input_size / orig_w * orig_h)
            else:
                new_w = int(input_size / orig_h * orig_w)
                new_h = input_size

            resized = cv2.resize(img_normalized, (new_w, new_h))
            canvas = np.zeros((input_size, input_size, 3), dtype=np.float32)
            canvas[:new_h, :new_w] = resized

            meta = (new_w, new_h, orig_w, orig_h)
            return canvas, meta

        except ValueError:
            raise
        except Exception as e:
            logger.error("preprocess_failed", extra={"error": str(e)})
            raise HTTPException(status_code=400, detail="Invalid image format")

    def infer(self, image_bytes: bytes) -> dict:
        """Run inference and return raw model outputs."""
        import torch

        self.load_model()
        canvas, meta = self.preprocess(image_bytes)

        # NHWC -> NCHW tensor
        img_tensor = torch.from_numpy(canvas).permute(2, 0, 1).unsqueeze(0).to(self.device)

        try:
            with torch.no_grad():
                features, regression, classification, anchors = self.model(img_tensor)

            return {
                "regression": regression.cpu().numpy(),
                "classification": classification.cpu().numpy(),
                "anchors": anchors.cpu().numpy(),
                "_meta": meta,
                "_input_shape": (1, 3, settings.MODEL_INPUT_SIZE, settings.MODEL_INPUT_SIZE),
            }
        except Exception as e:
            logger.error("inference_failed", extra={"error": str(e)})
            raise HTTPException(status_code=500, detail="Model Inference Failed")

    def is_healthy(self) -> bool:
        try:
            self.load_model()
            return self.model is not None
        except Exception:
            return False


inference_svc = PyTorchInferenceService()
