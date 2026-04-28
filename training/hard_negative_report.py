import json
from pathlib import Path
from collections import Counter


ROOT = Path(__file__).resolve().parents[1]
BUFFER_DIR = ROOT / "ewaste_model" / "hard_negative_buffer"
OUT_REPORT = ROOT / "ewaste_model" / "hard_negative_report.json"


def main():
    BUFFER_DIR.mkdir(parents=True, exist_ok=True)
    meta_files = sorted(BUFFER_DIR.glob("*.json"))
    total = len(meta_files)
    reason_counter = Counter()
    class_counter = Counter()

    for meta_file in meta_files:
        try:
            payload = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        reason = payload.get("capture_reason", {})
        if reason.get("zero_detections"):
            reason_counter["zero_detections"] += 1
        if int(reason.get("generic_ewaste_count", 0)) > 0:
            reason_counter["generic_ewaste"] += 1
        if int(reason.get("low_confidence_count", 0)) > 0:
            reason_counter["low_confidence"] += 1
        for cls in payload.get("detected_classes", []):
            class_counter[cls] += 1

    report = {
        "buffer_dir": str(BUFFER_DIR),
        "total_samples": total,
        "reason_counts": dict(reason_counter),
        "top_detected_classes": class_counter.most_common(20),
        "next_steps": [
            "Manually review captured frames and relabel true objects.",
            "Export labeled data to COCO format.",
            "Place labeled COCO split under ewaste_model/hard_negative_labeled/train and valid.",
            "Run training/retrain_with_hard_negatives.py",
        ],
    }
    OUT_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Hard-negative samples: {total}")
    print(f"Report written to: {OUT_REPORT}")


if __name__ == "__main__":
    main()
