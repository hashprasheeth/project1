import itertools
import numpy as np
from backend.core.config import settings
from backend.core.debug_log import debug_log
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

def _batched_nms(
    boxes: np.ndarray, scores: np.ndarray, class_ids: np.ndarray, iou_threshold: float = 0.5
) -> np.ndarray:
    """Run NMS per class, then merge by score descending."""
    keep_all = []
    for cid in np.unique(class_ids):
        cls_idx = np.where(class_ids == cid)[0]
        if cls_idx.size == 0:
            continue
        cls_keep_local = _nms(boxes[cls_idx], scores[cls_idx], iou_threshold)
        keep_all.extend(cls_idx[cls_keep_local].tolist())
    if not keep_all:
        return np.array([], dtype=np.int64)
    keep_arr = np.array(keep_all, dtype=np.int64)
    order = np.argsort(scores[keep_arr])[::-1]
    return keep_arr[order]


def _dedupe_final_detections(detections: list[dict], iou_threshold: float) -> list[dict]:
    """Run one more NMS pass after final labels are decided."""
    if len(detections) <= 1:
        return detections

    label_ids: dict[str, int] = {}
    boxes = []
    scores = []
    class_ids = []
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        label = str(det["label"])
        if label not in label_ids:
            label_ids[label] = len(label_ids)
        boxes.append([x1, y1, x2, y2])
        scores.append(float(det["confidence"]))
        class_ids.append(label_ids[label])

    keep = _batched_nms(
        np.asarray(boxes, dtype=np.float32),
        np.asarray(scores, dtype=np.float32),
        np.asarray(class_ids, dtype=np.int64),
        iou_threshold=iou_threshold,
    )
    return [detections[int(idx)] for idx in keep]


def _apply_demo_label_corrections(
    label: str,
    width: float,
    height: float,
    frame_area: float,
) -> str:
    """
    Presentation-specific correction layer for the currently allowed demo objects.
    This is intentionally conservative and only rewrites a few known confusion cases.
    """
    area_ratio = (width * height) / max(frame_area, 1.0)
    aspect_ratio = width / max(height, 1e-6)

    # Batteries are often confused with compact rectangular electronics.
    # Only remap to battery for very small objects, never to PCB.
    if label in {"SSD", "Power-Adapter"}:
        if area_ratio <= 0.03 and 0.35 <= aspect_ratio <= 4.5:
            return "Battery"
        return "Electronic-Waste"

    # For the presentation, all CRT/display-family hits should resolve to CRT-TV.
    if label in {"CRT-Monitor", "Flat-Panel-TV", "Flat-Panel-Monitor"}:
        return "CRT-TV"

    return label


def _apply_phone_priority(detections: list[dict]) -> list[dict]:
    """
    If a confident phone is present, keep phone detections and only very confident
    non-phone boxes. This reduces random live-camera boxes.
    """
    if not settings.PHONE_PRIORITY_ENABLED or not detections:
        return detections

    phone_label = settings.PHONE_PRIORITY_CLASS
    has_confident_phone = any(
        str(d.get("label")) == phone_label
        and float(d.get("confidence", 0.0)) >= settings.PHONE_PRIORITY_MIN_CONFIDENCE
        for d in detections
    )
    if not has_confident_phone:
        return detections

    kept: list[dict] = []
    for det in detections:
        label = str(det.get("label"))
        score = float(det.get("confidence", 0.0))
        if label == phone_label or score >= settings.PHONE_PRIORITY_OTHER_MIN_CONFIDENCE:
            kept.append(det)
    return kept


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
        threshold = settings.DETECTION_CONFIDENCE_THRESHOLD
        iou_threshold = 0.5
        max_detections = 50
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

        # Some EfficientDet exports already return probabilities in [0, 1].
        # Apply sigmoid only when outputs look like logits.
        cls_min = float(np.min(cls))
        cls_max = float(np.max(cls))
        if cls_min >= 0.0 and cls_max <= 1.0:
            cls_scores = cls
        else:
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

        new_w, new_h, orig_w, orig_h = meta
        # Clip in resized-image space (not padded canvas space) to avoid off-frame boxes.
        decoded[:, 0] = np.clip(decoded[:, 0], 0, new_w - 1)
        decoded[:, 1] = np.clip(decoded[:, 1], 0, new_h - 1)
        decoded[:, 2] = np.clip(decoded[:, 2], 0, new_w - 1)
        decoded[:, 3] = np.clip(decoded[:, 3], 0, new_h - 1)

        max_scores = cls_scores.max(axis=1)
        mask = max_scores > threshold
        used_fallback = False
        if settings.DETECTION_ENABLE_FALLBACK and not mask.any():
            # Fallback path: keep top-K predictions above a low floor
            # to avoid hard-zero output when the scene is ambiguous.
            fallback_floor = settings.DETECTION_FALLBACK_MIN_CONFIDENCE
            candidate_idx = np.where(max_scores >= fallback_floor)[0]
            if candidate_idx.size > 0:
                order = candidate_idx[np.argsort(max_scores[candidate_idx])[::-1]]
                keep_idx = order[: max(1, settings.DETECTION_FALLBACK_TOP_K)]
                mask = np.zeros_like(max_scores, dtype=bool)
                mask[keep_idx] = True
                used_fallback = True
        if not mask.any():
            debug_log(
                "safety_engine.py:analyze",
                "detection_filter_summary",
                {
                    "threshold": threshold,
                    "min_detection_area_ratio": settings.MIN_DETECTION_AREA_RATIO,
                    "max_score_observed": round(float(max_scores.max(initial=0.0)), 4),
                    "used_fallback": used_fallback,
                    "skipped_small_boxes": 0,
                    "final_detections": 0,
                },
            )
            return [], [], False

        filtered_boxes = decoded[mask]
        filtered_cls = cls_scores[mask]
        filtered_max_scores = max_scores[mask]
        class_ids = filtered_cls.argmax(axis=1)

        keep = _batched_nms(filtered_boxes, filtered_max_scores, class_ids, iou_threshold)
        if len(keep) > max_detections:
            keep = keep[:max_detections]

        final_boxes = filtered_boxes[keep]
        final_scores = filtered_max_scores[keep]
        final_class_ids = class_ids[keep]
        final_class_probs = filtered_cls[keep]

        scale_x = orig_w / new_w
        scale_y = orig_h / new_h

        class_map = settings.CLASSES
        detections = []
        detected_class_names = set()
        is_hazardous = False
        min_area = settings.MIN_DETECTION_AREA_RATIO * float(orig_w * orig_h)
        skipped_small_boxes = 0
        skipped_generic_ewaste_boxes = 0
        skipped_disallowed_classes = 0
        skipped_low_class_confidence = 0
        skipped_low_margin = 0
        allowed_classes = set(settings.ALLOWED_DETECTION_CLASSES)

        for i in range(len(final_boxes)):
            cid = int(final_class_ids[i])
            label = class_map.get(cid, f"class_{cid}")
            score = float(final_scores[i])

            top2 = np.partition(final_class_probs[i], -2)[-2:]
            margin = float(top2[-1] - top2[-2])
            if margin < settings.DETECTION_MIN_CLASS_MARGIN:
                if settings.COLLAPSE_AMBIGUOUS_TO_EWASTE:
                    label = "Electronic-Waste"
                else:
                    skipped_low_margin += 1
                    continue

            x1 = float(final_boxes[i, 0]) * scale_x
            y1 = float(final_boxes[i, 1]) * scale_y
            x2 = float(final_boxes[i, 2]) * scale_x
            y2 = float(final_boxes[i, 3]) * scale_y
            width = max(0.0, x2 - x1)
            height = max(0.0, y2 - y1)
            area = width * height
            if area < min_area:
                skipped_small_boxes += 1
                continue

            label = _apply_demo_label_corrections(
                label=label,
                width=width,
                height=height,
                frame_area=float(orig_w * orig_h),
            )

            if settings.ENABLE_ALLOWED_CLASS_FILTER and label not in allowed_classes:
                skipped_disallowed_classes += 1
                continue

            if settings.ENABLE_CLASS_CONFIDENCE_FLOOR:
                class_floor = settings.CLASS_CONFIDENCE_FLOOR.get(
                    label, settings.DEFAULT_CLASS_CONFIDENCE_FLOOR
                )
                if score < class_floor:
                    skipped_low_class_confidence += 1
                    continue

            if label == "Electronic-Waste":
                max_generic_area = settings.GENERIC_EWASTE_MAX_AREA_RATIO * float(orig_w * orig_h)
                aspect_ratio = (height / max(width, 1e-6)) if width > 0 else 999.0
                if area > max_generic_area or aspect_ratio > settings.GENERIC_EWASTE_MAX_ASPECT_RATIO:
                    skipped_generic_ewaste_boxes += 1
                    continue

            detections.append({
                "label": label,
                "confidence": round(score, 4),
                "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                "_orig_w": int(orig_w),
                "_orig_h": int(orig_h),
            })

        detections = _dedupe_final_detections(detections, settings.FINAL_LABEL_NMS_IOU)
        detections = _apply_phone_priority(detections)
        detected_class_names = {str(d["label"]) for d in detections}
        is_hazardous = any(str(d["label"]) in SafetyEngine.HAZARDOUS_ITEMS for d in detections)

        debug_log(
            "safety_engine.py:analyze",
            "detection_filter_summary",
            {
                "threshold": threshold,
                "min_detection_area_ratio": settings.MIN_DETECTION_AREA_RATIO,
                "used_fallback": used_fallback,
                "skipped_small_boxes": skipped_small_boxes,
                "skipped_generic_ewaste_boxes": skipped_generic_ewaste_boxes,
                "skipped_disallowed_classes": skipped_disallowed_classes,
                "skipped_low_class_confidence": skipped_low_class_confidence,
                "skipped_low_margin": skipped_low_margin,
                "final_detections": len(detections),
            },
        )
        return detections, list(detected_class_names), is_hazardous

