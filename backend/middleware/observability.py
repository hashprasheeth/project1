import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from backend.core.logger import logger

class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Attach Request ID
        request.state.request_id = request_id
        
        # Log Request (Debug)
        # logger.debug("request_started", extra={"path": request.url.path, "request_id": request_id})
        
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            
            # Log Metric
            logger.info(
                "request_completed",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "duration_ms": round(process_time, 2),
                    "request_id": request_id
                }
            )
            
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                "request_failed",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error": str(e),
                    "duration_ms": round(process_time, 2),
                    "request_id": request_id
                }
            )
            raise e
