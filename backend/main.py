import time
import json
import uuid
import re
from typing import Dict, List
from collections import defaultdict
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from backend.core.config import settings
from backend.core.debug_log import debug_log, debug_log_path
from backend.core.logger import logger
from backend.services.onnx_inference import inference_svc
from backend.services.safety_engine import SafetyEngine
from backend.middleware.observability import ObservabilityMiddleware

# ── api-security-best-practices: Rate limiter ──────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    description="E-Waste Detection and Tracking System with Hazardous Material Monitoring"
)

# ── api-security-best-practices: Attach rate limiter ──────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── api-security-best-practices: Security headers middleware ───────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(self), microphone=(), geolocation=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# ── api-security-best-practices: Proper CORS (fix wildcard + credentials) ─
# Never use allow_origins=["*"] together with allow_credentials=True.
# Restrict to known, configured origins only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,   # e.g. ["http://localhost:5173"]
    allow_credentials=False,                   # No credentials = wildcard safe, but we use explicit origins
    allow_methods=["GET", "POST"],             # Only methods we actually use
    allow_headers=["Content-Type"],
)
app.add_middleware(ObservabilityMiddleware)

# ── api-security-best-practices: File type validation ──────────────────────
_ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
_ALLOWED_MAGIC = {
    b"\xff\xd8\xff",          # JPEG
    b"\x89PNG",               # PNG
    b"RIFF",                  # WebP (RIFF....WEBP)
}

def _validate_image(contents: bytes, content_type: str | None):
    """Reject files that are not real images (MIME + magic bytes check)."""
    if content_type and content_type not in _ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported file type. Upload JPEG, PNG, or WebP.")
    magic = contents[:4]
    if not any(magic.startswith(sig) for sig in _ALLOWED_MAGIC):
        raise HTTPException(status_code=415, detail="File content does not match an accepted image format.")


# In-memory tracking state for simulated video streams
class EWasteTracker:
    """Tracks e-waste detections across frames/images for statistics"""
    def __init__(self):
        self.detections_history: List[Dict] = []
        self.class_counts = defaultdict(int)
        self.hazard_counts = defaultdict(int)
        self.total_frames = 0

    @staticmethod
    def _bbox_iou(box_a: List[float], box_b: List[float]) -> float:
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b
        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)
        inter_w = max(0.0, inter_x2 - inter_x1)
        inter_h = max(0.0, inter_y2 - inter_y1)
        inter_area = inter_w * inter_h
        if inter_area <= 0:
            return 0.0
        area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
        area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
        union = area_a + area_b - inter_area
        return inter_area / max(union, 1e-6)

    def stabilize_labels(self, detections: List[Dict], lookback_frames: int = 6, min_iou: float = 0.35) -> List[Dict]:
        """
        Stabilize class labels across nearby frames by majority voting in overlapping boxes.
        This reduces random label flips while keeping detections model-driven.
        """
        if not detections or not self.detections_history:
            return detections

        recent = self.detections_history[-lookback_frames:]
        stabilized: List[Dict] = []
        for det in detections:
            bbox = det.get("bbox")
            label_votes = defaultdict(int)
            label_votes[det.get("label", "unknown")] += 2  # bias to current frame
            if isinstance(bbox, list) and len(bbox) == 4:
                for frame in recent:
                    for prev in frame.get("detections", []):
                        prev_bbox = prev.get("bbox")
                        if not (isinstance(prev_bbox, list) and len(prev_bbox) == 4):
                            continue
                        if self._bbox_iou(bbox, prev_bbox) >= min_iou:
                            label_votes[prev.get("label", "unknown")] += 1
            top_label = max(label_votes.items(), key=lambda kv: kv[1])[0]
            if top_label != det.get("label"):
                det = {**det, "label": top_label}
            stabilized.append(det)
        return stabilized
        
    def add_detection(self, detections: List[Dict], is_hazardous: bool):
        """Add detection results from a frame"""
        self.total_frames += 1
        
        for det in detections:
            class_name = det.get("label", "unknown")
            self.class_counts[class_name] += 1
            
            if det.get("hazardous", False):
                self.hazard_counts[class_name] += 1
        
        self.detections_history.append({
            "frame": self.total_frames,
            "timestamp": time.time(),
            "detections": detections,
            "is_hazardous": is_hazardous
        })
        
        # Keep only last 100 frames in memory
        if len(self.detections_history) > 100:
            self.detections_history.pop(0)
    
    def get_stats(self) -> Dict:
        """Get aggregated statistics"""
        total_detections = sum(self.class_counts.values())
        total_hazardous = sum(self.hazard_counts.values())
        
        return {
            "total_frames_processed": self.total_frames,
            "total_detections": total_detections,
            "total_hazardous_items": total_hazardous,
            "hazard_rate": round(total_hazardous / max(total_detections, 1), 3),
            "class_distribution": dict(self.class_counts),
            "hazardous_distribution": dict(self.hazard_counts),
            "top_detected_classes": sorted(
                self.class_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10],
            "recycling_recommendations": self._get_recycling_recommendations()
        }
    
    def _get_recycling_recommendations(self) -> Dict:
        """Generate recycling recommendations based on detected items"""
        recommendations = {
            "hazardous_facility": [],
            "ewaste_facility": [],
            "standard_recycling": [],
            "data_destruction_required": []
        }
        
        # Load class labels for recycling info
        try:
            project_root = Path(__file__).parent.parent
            labels_path = project_root / "class_labels.json"
            
            if labels_path.exists():
                with open(labels_path, 'r') as f:
                    labels_data = json.load(f)
                    
                for class_name in self.class_counts.keys():
                    # Find class in labels
                    for class_info in labels_data.get("classes", {}).values():
                        if class_info["name"] == class_name:
                            bin_type = class_info.get("recycling_bin", "electronics")
                            
                            if bin_type == "hazardous":
                                recommendations["hazardous_facility"].append(class_name)
                            elif bin_type == "electronics":
                                recommendations["ewaste_facility"].append(class_name)
                            else:
                                recommendations["standard_recycling"].append(class_name)
                            
                            # Check for data-bearing devices
                            if class_name in ["HDD", "SSD", "Smartphone", "Tablet", "Laptop", "Desktop-PC", "Server"]:
                                recommendations["data_destruction_required"].append(class_name)
        except Exception as e:
            logger.warning(f"Could not load recycling recommendations: {e}")
        
        return recommendations
    
    def reset(self):
        """Reset tracking statistics"""
        self.detections_history = []
        self.class_counts = defaultdict(int)
        self.hazard_counts = defaultdict(int)
        self.total_frames = 0

# Global tracker instance
tracker = EWasteTracker()
HARD_NEG_DIR = Path(__file__).parent.parent / "ewaste_model" / "hard_negative_buffer"
TRAINING_COMMAND_HINT = "python training/retrain_with_hard_negatives.py"


def _discover_training_terminal_file() -> Path | None:
    """
    Discover the terminal log file for the active retraining process.
    """
    projects_root = Path.home() / ".cursor" / "projects"
    if not projects_root.exists():
        return None
    candidates = []
    for terminal_file in projects_root.glob("*/terminals/*.txt"):
        try:
            stat = terminal_file.stat()
            candidates.append((stat.st_mtime, terminal_file))
        except Exception:
            continue
    for _, terminal_file in sorted(candidates, reverse=True):
        try:
            text = terminal_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if TRAINING_COMMAND_HINT in text:
            return terminal_file
    return None


def _parse_training_status_from_terminal(terminal_file: Path) -> Dict:
    text = terminal_file.read_text(encoding="utf-8", errors="ignore")
    header_pid = re.search(r"^pid:\s*(\d+)", text, flags=re.MULTILINE)
    header_started = re.search(r"^started_at:\s*(.+)$", text, flags=re.MULTILINE)
    header_running_for = re.search(r"^running_for_ms:\s*(\d+)", text, flags=re.MULTILINE)
    footer_exit = re.search(r"^exit_code:\s*([^\r\n]+)", text, flags=re.MULTILINE)

    step_matches = list(
        re.finditer(
            r"Step:\s*(\d+)\.\s*Epoch:\s*(\d+)/(\d+)\.\s*Iteration:\s*(\d+)/(\d+)",
            text,
            flags=re.MULTILINE,
        )
    )
    val_epoch_matches = list(
        re.finditer(
            r"Val\.\s*Epoch:\s*(\d+)/(\d+)\.",
            text,
            flags=re.MULTILINE,
        )
    )
    status = {
        "running": footer_exit is None,
        "terminal_file": str(terminal_file),
        "pid": int(header_pid.group(1)) if header_pid else None,
        "started_at": header_started.group(1).strip() if header_started else None,
        "running_for_ms": int(header_running_for.group(1)) if header_running_for else None,
        "exit_code": None if footer_exit is None else footer_exit.group(1).strip(),
        "step": None,
        "epoch_current": None,
        "epoch_total": None,
        "iter_current": None,
        "iter_total": None,
        "epoch_progress_pct": 0.0,
        "overall_progress_pct": 0.0,
        "eta_seconds": 0,
        "progress_source": "none",
    }
    step_overall = 0.0
    if step_matches:
        last = step_matches[-1]
        step, e_cur, e_total, i_cur, i_total = map(int, last.groups())
        status["step"] = step
        status["epoch_current"] = e_cur
        status["epoch_total"] = e_total
        status["iter_current"] = i_cur
        status["iter_total"] = i_total
        epoch_progress = (i_cur / i_total) if i_total else 0.0
        overall_progress = (((e_cur - 1) + epoch_progress) / e_total) if e_total else 0.0
        status["epoch_progress_pct"] = round(epoch_progress * 100, 2)
        status["overall_progress_pct"] = round(overall_progress * 100, 2)
        status["progress_source"] = "step"
        step_overall = overall_progress
        if status["running_for_ms"] and e_total and i_total:
            total_iters = e_total * i_total
            completed_iters = ((e_cur - 1) * i_total) + i_cur
            if completed_iters > 0 and total_iters > completed_iters:
                elapsed_s = status["running_for_ms"] / 1000.0
                iter_per_s = completed_iters / max(elapsed_s, 1e-6)
                if iter_per_s > 0:
                    remaining_iters = total_iters - completed_iters
                    status["eta_seconds"] = max(0, int(remaining_iters / iter_per_s))
    if val_epoch_matches:
        val_cur, val_total = map(int, val_epoch_matches[-1].groups())
        val_overall = (val_cur / val_total) if val_total else 0.0
        if val_overall > step_overall:
            status["epoch_current"] = min(val_cur + 1, val_total)
            status["epoch_total"] = val_total
            status["iter_current"] = None
            status["iter_total"] = None
            status["epoch_progress_pct"] = 0.0 if val_cur < val_total else 100.0
            status["overall_progress_pct"] = round(val_overall * 100, 2)
            status["progress_source"] = "val_epoch"
            if status["running_for_ms"] and val_overall > 0 and val_overall < 1:
                elapsed_s = status["running_for_ms"] / 1000.0
                status["eta_seconds"] = max(0, int((elapsed_s * (1 - val_overall)) / val_overall))
    return status


def _save_hard_negative_sample(
    contents: bytes,
    content_type: str | None,
    enhanced_detections: List[Dict],
    classes: List[str],
    is_hazardous: bool,
    frame_number: int,
    processing_ms: float,
):
    """
    Save hard-negative candidates for later labeling/retraining.
    Criteria:
      - zero detections (misses),
      - many generic Electronic-Waste labels (low specificity),
      - low-confidence detections.
    """
    if not contents:
        return

    total_items = len(enhanced_detections)
    ewaste_generic = sum(1 for d in enhanced_detections if d.get("label") == "Electronic-Waste")
    low_conf = sum(1 for d in enhanced_detections if float(d.get("confidence", 0.0)) < 0.45)
    should_capture = (
        total_items == 0
        or ewaste_generic >= 3
        or low_conf >= 3
    )
    if not should_capture:
        return

    HARD_NEG_DIR.mkdir(parents=True, exist_ok=True)
    ext = ".jpg"
    if content_type == "image/png":
        ext = ".png"
    elif content_type == "image/webp":
        ext = ".webp"
    sample_id = f"{int(time.time()*1000)}-{uuid.uuid4().hex[:8]}"
    image_path = HARD_NEG_DIR / f"{sample_id}{ext}"
    meta_path = HARD_NEG_DIR / f"{sample_id}.json"

    try:
        image_path.write_bytes(contents)
        meta_payload = {
            "sample_id": sample_id,
            "captured_at": int(time.time() * 1000),
            "frame_number": frame_number,
            "processing_time_ms": round(processing_ms, 2),
            "content_type": content_type or "unknown",
            "total_items": total_items,
            "detected_classes": classes,
            "is_hazardous": is_hazardous,
            "detections": enhanced_detections,
            "capture_reason": {
                "zero_detections": total_items == 0,
                "generic_ewaste_count": ewaste_generic,
                "low_confidence_count": low_conf,
            },
            "image_file": image_path.name,
        }
        meta_path.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")
    except Exception as exc:
        debug_log(
            "main.py:/detect",
            "hard_negative_capture_failed",
            {"error": str(exc), "sample_id": sample_id},
        )

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", extra={"error": str(exc), "path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "request_id": getattr(request.state, "request_id", "unknown")},
    )

@app.on_event("startup")
async def startup_event():
    logger.info("application_startup")
    debug_log(
        "main.py:startup",
        "backend_startup",
        {"debug_log_path": debug_log_path(), "rate_limit_detect": settings.RATE_LIMIT_DETECT},
    )
    try:
        inference_svc.load_model()
        logger.info("onnx_model_loaded")
    except Exception:
        logger.warning("onnx_model_load_pending")

@app.post("/detect")
@limiter.limit(settings.RATE_LIMIT_DETECT)   # api-security-best-practices: 10/min on inference
async def detect_ewaste(file: UploadFile = File(...), request: Request = None):
    """
    Detect e-waste items in uploaded image
    Returns: Detection results with hazard flags and recycling info
    """
    # Security: Size Check
    content_length = request.headers.get('content-length')
    if content_length and int(content_length) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")
        
    start_time = time.time()
    
    try:
        contents = await file.read()
        
        if len(contents) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
             raise HTTPException(status_code=413, detail="File too large")

        # api-security-best-practices: Validate file type (MIME + magic bytes)
        _validate_image(contents, file.content_type)
        raw_output = await run_in_threadpool(inference_svc.infer, contents)
        
        # Analyze with safety engine
        boxes, classes, is_hazardous = SafetyEngine.analyze(raw_output)
        
        # Enhance detections with recycling info
        enhanced_detections = []
        for box in boxes:
            class_name = box.get("label", "unknown")
            recycling_info = await get_recycling_info_for_class(class_name)
            
            enhanced_detections.append({
                **box,
                "hazardous": class_name in settings.HAZARDOUS_CLASSES,
                "recycling_bin": recycling_info.get("recycling_bin", "electronics"),
                "recycling_tip": recycling_info.get("tip", "Dispose at e-waste facility")
            })
        
        # Temporal label stabilization improves consistency across video frames.
        enhanced_detections = tracker.stabilize_labels(enhanced_detections)
        # After stabilization, recompute hazard + recycling metadata from the final label
        # so the UI never shows mismatched hazard banners or recycling tips.
        if enhanced_detections:
            refreshed: List[Dict] = []
            for det in enhanced_detections:
                final_label = det.get("label", "unknown")
                recycling_info = await get_recycling_info_for_class(final_label)
                refreshed.append({
                    **det,
                    "hazardous": final_label in settings.HAZARDOUS_CLASSES,
                    "recycling_bin": recycling_info.get("recycling_bin", "electronics"),
                    "recycling_tip": recycling_info.get("tip", "Dispose at e-waste facility"),
                })
            enhanced_detections = refreshed
        is_hazardous = any(d.get("hazardous", False) for d in enhanced_detections)

        # Update tracker
        tracker.add_detection(enhanced_detections, is_hazardous)
        
        latency = (time.time() - start_time) * 1000
        
        hazard_count = sum(1 for d in enhanced_detections if d.get("hazardous", False))
        _save_hard_negative_sample(
            contents=contents,
            content_type=file.content_type,
            enhanced_detections=enhanced_detections,
            classes=classes,
            is_hazardous=is_hazardous,
            frame_number=tracker.total_frames,
            processing_ms=latency,
        )
        debug_log(
            "main.py:/detect",
            "detect_result",
            {
                "content_type": file.content_type or "unknown",
                "bytes": len(contents),
                "total_items": len(enhanced_detections),
                "hazard_count": hazard_count,
                "frame_number": tracker.total_frames,
            },
        )
        
        return {
            "detections": enhanced_detections,
            "detected_classes": classes,
            "is_hazardous": is_hazardous,
            "hazard_count": hazard_count,
            "total_items": len(enhanced_detections),
            "processing_time_ms": round(latency, 2),
            "frame_number": tracker.total_frames
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error("detection_failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recycling-info/{class_name}")
async def get_recycling_info(class_name: str):
    """
    Get recycling information for a specific e-waste class
    """
    info = await get_recycling_info_for_class(class_name)
    
    if not info:
        raise HTTPException(status_code=404, detail=f"Class '{class_name}' not found")
    
    return info

async def get_recycling_info_for_class(class_name: str) -> Dict:
    """Helper to get recycling info from class labels JSON"""
    try:
        project_root = Path(__file__).parent.parent
        labels_path = project_root / "class_labels.json"
        
        if not labels_path.exists():
            return {"recycling_bin": "electronics", "tip": "Dispose at e-waste facility"}
        
        with open(labels_path, 'r') as f:
            labels_data = json.load(f)
        
        for class_info in labels_data.get("classes", {}).values():
            if class_info["name"] == class_name:
                is_hazardous = class_info.get("hazardous", False)
                recycling_bin = class_info.get("recycling_bin", "electronics")
                
                tips = {
                    "hazardous": "⚠️ HAZARDOUS: Dispose at specialized hazardous waste facility only",
                    "electronics": "♻️ Dispose at certified e-waste recycling facility",
                    "metals": "🔧 Recyclable at metal recycling centers",
                    "displays": "🖥️ Special handling required for displays - contact e-waste facility"
                }
                
                return {
                    "class": class_name,
                    "description": class_info.get("description", ""),
                    "hazardous": is_hazardous,
                    "recycling_bin": recycling_bin,
                    "tip": tips.get(recycling_bin, tips["electronics"])
                }
        
        return {"recycling_bin": "electronics", "tip": "Dispose at e-waste facility"}
    
    except Exception as e:
        logger.error(f"Error loading recycling info: {e}")
        return {"recycling_bin": "electronics", "tip": "Dispose at e-waste facility"}

@app.get("/stats")
async def get_statistics():
    """
    Get aggregated e-waste detection statistics and recycling recommendations
    """
    stats = tracker.get_stats()
    debug_log(
        "main.py:/stats",
        "stats_snapshot",
        {
            "total_frames_processed": stats.get("total_frames_processed", 0),
            "total_detections": stats.get("total_detections", 0),
            "total_hazardous_items": stats.get("total_hazardous_items", 0),
        },
    )

    return {
        **stats,
        "system_info": {
            "model": settings.MODEL_NAME,
            "total_classes": 77,
            "hazardous_classes": len(settings.HAZARDOUS_CLASSES)
        }
    }

@app.post("/track/reset")
async def reset_tracking():
    """Reset tracking statistics"""
    tracker.reset()
    debug_log("main.py:/track/reset", "tracking_reset", {"total_frames": tracker.total_frames})
    return {"message": "Tracking statistics reset successfully"}


@app.post("/debug/client-log")
async def debug_client_log(payload: Dict):
    """
    Collects frontend debug events and appends them to the shared debug session log.
    """
    debug_log(
        "frontend",
        str(payload.get("message", "client_event")),
        {
            "location": payload.get("location", "unknown"),
            "data": payload.get("data", {}),
        },
    )
    return {"ok": True}

@app.get("/health")
async def health():
    """Health check including model status"""
    model_ok = inference_svc.is_healthy()
    status_code = 200 if model_ok else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if model_ok else "degraded",
            "dependencies": {
                "model": "loaded" if model_ok else "not_loaded"
            },
            "tracking_stats": {
                "total_frames": tracker.total_frames,
                "total_detections": sum(tracker.class_counts.values())
            }
        }
    )

@app.get("/logs")
async def get_logs():
    """Get recent detection log entries for the live terminal"""
    entries = []
    for frame in reversed(tracker.detections_history[-20:]):
        ts = time.strftime("%H:%M:%S", time.localtime(frame["timestamp"]))
        for det in frame["detections"]:
            label = det.get("label", "unknown")
            conf = det.get("confidence", 0)
            is_haz = det.get("hazardous", False)

            if is_haz:
                entries.append({"timestamp": ts, "level": "danger",
                    "message": f"ALERT: Hazardous item detected ({label})"})
            else:
                entries.append({"timestamp": ts, "level": "info",
                    "message": f"Item cleared ({label}) - conf {round(conf * 100)}%"})

    if not entries:
        now = time.strftime("%H:%M:%S")
        entries = [
            {"timestamp": now, "level": "system", "message": "System check complete. All sensors active."},
            {"timestamp": now, "level": "system", "message": "Awaiting detections..."},
        ]
    return entries[:20]


@app.get("/dispatch")
async def get_dispatch_queue():
    """Get simulated dispatch queue based on detected items"""
    batches = []
    batch_num = 9921
    hazardous_items = []
    safe_items = []

    for frame in tracker.detections_history[-30:]:
        for det in frame["detections"]:
            if det.get("hazardous"):
                hazardous_items.append(det["label"])
            else:
                safe_items.append(det["label"])

    if hazardous_items:
        batches.append({
            "id": f"batch-{batch_num}",
            "batchName": f"BATCH #{batch_num}",
            "status": "ready",
            "progress": 100,
            "icon": "warning",
        })
        batch_num += 1

    if safe_items:
        batches.append({
            "id": f"batch-{batch_num}",
            "batchName": f"BATCH #{batch_num}",
            "status": "sorting",
            "progress": 70,
            "icon": "inventory_2",
        })
        batch_num += 1

    batches.append({
        "id": f"batch-{batch_num}",
        "batchName": f"BATCH #{batch_num}",
        "status": "queued",
        "progress": 0,
        "icon": "schedule",
    })

    return batches


@app.get("/training/status")
async def get_training_status():
    """
    Return current retraining progress by parsing the live terminal output.
    """
    terminal_file = _discover_training_terminal_file()
    if terminal_file is None:
        return {
            "running": False,
            "message": "No retraining terminal found.",
            "step": None,
            "epoch_current": None,
            "epoch_total": None,
            "iter_current": None,
            "iter_total": None,
            "epoch_progress_pct": 0.0,
            "overall_progress_pct": 0.0,
            "eta_seconds": 0,
        }
    try:
        return _parse_training_status_from_terminal(terminal_file)
    except Exception as exc:
        return {
            "running": False,
            "message": f"Failed to parse training status: {exc}",
            "step": None,
            "epoch_current": None,
            "epoch_total": None,
            "iter_current": None,
            "iter_total": None,
            "epoch_progress_pct": 0.0,
            "overall_progress_pct": 0.0,
            "eta_seconds": 0,
        }


# Legacy endpoint for backward compatibility
@app.post("/predict")
async def predict(file: UploadFile = File(...), request: Request = None):
    """Legacy endpoint - redirects to /detect"""
    return await detect_ewaste(file, request)

