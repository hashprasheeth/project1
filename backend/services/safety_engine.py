import itertools
import numpy as np
from backend.core.config import settings
from backend.core.logger import logger


def _generate_anchors(input_size: int, anchor_scale: float = 4.0):
    """Generate EfficientDet anchor boxes matching the training config."""
    pyramid_levels = [3, 4, 5, 6, 7]
    strides = [2 ** x for x in pyramid_levels]
    scales = np.array([2 ** 0, 2 ** (1.0 / 3.0), 2 ** (2.0 / 3.0)])
    ratios = [(1.0, 1.0), (1.4, 0.7), (0.7, 1.4)]

    boxes_all = []
    for stride in strides:
        for scale, ratio in itertools.product(scales, ratios):
            base = anchor_scale * stride * scale
            ax2 = base * ratio[0] / 2.0
            ay2 = base * ratio[1] / 2.0

            x = np.arange(stride / 2, input_size, stride)
            y = np.arange(stride / 2, input_size, stride)
            xv, yv = np.meshgrid(x, y)
            xv, yv = xv.ravel(), yv.ravel()

            boxes = np.stack([yv - ay2, xv - ax2, yv + ay2, xv + ax2], axis=1)
            boxes_all.append(boxes)

    return np.concatenate(boxes_all, axis=0).astype(np.float32)


def _decode_boxes(anchors: np.ndarray, regression: np.ndarray) -> np.ndarray:
    """Apply regression deltas to anchor boxes (BBoxTransform in NumPy)."""
    ya = (anchors[:, 0] + anchors[:, 2]) / 2
    xa = (anchors[:, 1] + anchors[:, 3]) / 2
    ha = anchors[:, 2] - anchors[:, 0]
    wa = anchors[:, 3] - anchors[:, 1]

    dy, dx, dh, dw = regression[:, 0], regression[:, 1], regression[:, 2], regression[:, 3]

    w = np.exp(dw) * wa
    h = np.exp(dh) * ha
    yc = dy * ha + ya
    xc = dx * wa + xa

    x1 = xc - w / 2
    y1 = yc - h / 2
    x2 = xc + w / 2
    y2 = yc + h / 2

    return np.stack([x1, y1, x2, y2], axis=1)


def _nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float = 0.5) -> np.ndarray:
    """Simple NMS in NumPy."""
    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        if order.size == 1:
            break

        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)

        inds = np.where(iou <= iou_threshold)[0]
        order = order[inds + 1]

    return np.array(keep, dtype=np.int64)


class SafetyEngine:
    HAZARDOUS_ITEMS = {
        "Battery", "CRT-Monitor", "CRT-TV", "PCB",
        "Smoke-Detector", "Compact-Fluorescent-Lamps", "Neon-Sign",
        "Straight-Tube-Fluorescent-Lamp", "Air-Conditioner", "Boiler",
        "Cooled-Dispenser", "Cooling-Display", "Dehumidifier", "Desktop-PC",
        "Drone", "Electric-Bicycle", "Flashlight", "Flat-Panel-Monitor",
        "Flat-Panel-TV", "Freezer", "HDD", "Laptop", "Microwave",
        "Photovoltaic-Panel", "Printer", "Projector", "Refrigerator",
        "Rotary-Mower", "SSD", "Server", "Smart-Watch", "Smartphone",
        "Soldering-Iron", "Street-Lamp", "Tablet", "Electronic-Waste",
    }

    _anchors_cache: dict[int, np.ndarray] = {}

    @staticmethod
    def _get_anchors(input_size: int) -> np.ndarray:
        if input_size not in SafetyEngine._anchors_cache:
            SafetyEngine._anchors_cache[input_size] = _generate_anchors(input_size)
        return SafetyEngine._anchors_cache[input_size]

    @staticmethod
    def analyze(raw_output: dict) -> tuple[list[dict], list[str], bool]:
        """
        Post-process EfficientDet ONNX output into detection results.

        Returns:
            (boxes, detected_classes, is_hazardous)
        """
        threshold = settings.HAZARDOUS_THRESHOLD
        iou_threshold = 0.5
        max_detections = 20
        input_shape = raw_output.get("_input_shape", (1, 3, 512, 512))
        meta = raw_output.get("_meta", (512, 512, 512, 512))
        input_size = input_shape[2]

        regression = None
        classification = None
        model_anchors = None

        for key, val in raw_output.items():
            if key.startswith("_"):
                continue
            if not isinstance(val, np.ndarray):
                continue
            if "regression" in key.lower() or "regress" in key.lower():
                regression = val
            elif "class" in key.lower():
                classification = val
            elif "anchor" in key.lower():
                model_anchors = val

        if regression is None or classification is None:
            output_keys = [k for k in raw_output if not k.startswith("_")]
            for key in output_keys:
                val = raw_output[key]
                if not isinstance(val, np.ndarray) or val.ndim < 2:
                    continue
                if val.shape[-1] == 4 and regression is None:
                    regression = val
                elif val.shape[-1] > 4 and classification is None:
                    classification = val

        if regression is None or classification is None:
            logger.warning("could_not_identify_outputs", extra={
                "keys": [k for k in raw_output if not k.startswith("_")]
            })
            return [], [], False

        reg = regression[0]  # [N, 4]
        cls = classification[0]  # [N, num_classes]

        cls_scores = 1.0 / (1.0 + np.exp(-np.clip(cls, -50, 50)))

        if model_anchors is not None:
            anc = model_anchors[0] if model_anchors.ndim == 3 else model_anchors
            anchors = anc
        else:
            anchors = SafetyEngine._get_anchors(input_size)

        if anchors.shape[0] != reg.shape[0]:
            logger.warning("anchor_mismatch", extra={
                "anchors": anchors.shape[0], "regression": reg.shape[0]
            })
            min_n = min(anchors.shape[0], reg.shape[0])
            anchors = anchors[:min_n]
            reg = reg[:min_n]
            cls_scores = cls_scores[:min_n]

        decoded = _decode_boxes(anchors, reg)

        decoded[:, 0] = np.clip(decoded[:, 0], 0, input_size - 1)
        decoded[:, 1] = np.clip(decoded[:, 1], 0, input_size - 1)
        decoded[:, 2] = np.clip(decoded[:, 2], 0, input_size - 1)
        decoded[:, 3] = np.clip(decoded[:, 3], 0, input_size - 1)

        max_scores = cls_scores.max(axis=1)
        mask = max_scores > threshold
        if not mask.any():
            return [], [], False

        filtered_boxes = decoded[mask]
        filtered_cls = cls_scores[mask]
        filtered_max_scores = max_scores[mask]
        class_ids = filtered_cls.argmax(axis=1)

        keep = _nms(filtered_boxes, filtered_max_scores, iou_threshold)
        if len(keep) > max_detections:
            keep = keep[:max_detections]

        final_boxes = filtered_boxes[keep]
        final_scores = filtered_max_scores[keep]
        final_class_ids = class_ids[keep]

        new_w, new_h, orig_w, orig_h = meta
        scale_x = orig_w / new_w
        scale_y = orig_h / new_h

        class_map = settings.CLASSES
        detections = []
        detected_class_names = set()
        is_hazardous = False

        for i in range(len(final_boxes)):
            cid = int(final_class_ids[i])
            label = class_map.get(cid, f"class_{cid}")
            score = float(final_scores[i])

            x1 = float(final_boxes[i, 0]) * scale_x
            y1 = float(final_boxes[i, 1]) * scale_y
            x2 = float(final_boxes[i, 2]) * scale_x
            y2 = float(final_boxes[i, 3]) * scale_y

            hazardous = label in SafetyEngine.HAZARDOUS_ITEMS
            if hazardous:
                is_hazardous = True

            detected_class_names.add(label)
            detections.append({
                "label": label,
                "confidence": round(score, 4),
                "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
            })

        return detections, list(detected_class_names), is_hazardous

    @staticmethod
    def check_safety(detected_label: str, confidence: float) -> dict:
        is_hazardous = detected_label in SafetyEngine.HAZARDOUS_ITEMS
        return {
            "is_hazardous": is_hazardous,
            "recycling_tip": "HAZARD: Handle with care" if is_hazardous else "General E-Waste Recycling",
            "confidence": confidence,
        }
