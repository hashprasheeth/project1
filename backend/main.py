import time
import json
from typing import Dict, List
from collections import defaultdict
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from backend.core.config import settings
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
        
        # Update tracker
        tracker.add_detection(enhanced_detections, is_hazardous)
        
        latency = (time.time() - start_time) * 1000
        
        hazard_count = sum(1 for d in enhanced_detections if d.get("hazardous", False))
        
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
    return {"message": "Tracking statistics reset successfully"}

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


# Legacy endpoint for backward compatibility
@app.post("/predict")
async def predict(file: UploadFile = File(...), request: Request = None):
    """Legacy endpoint - redirects to /detect"""
    return await detect_ewaste(file, request)

