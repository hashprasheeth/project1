import json
import time
from pathlib import Path
from typing import Any, Dict


_DEBUG_LOG_PATH = Path(__file__).resolve().parents[2] / "debug-72ca7d.log"


def debug_log(location: str, message: str, data: Dict[str, Any] | None = None):
    payload = {
        "sessionId": "72ca7d",
        "location": location,
        "message": message,
        "data": data or {},
        "timestamp": int(time.time() * 1000),
    }
    try:
        with _DEBUG_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
    except Exception:
        # Debug logging should never affect request handling.
        pass


def debug_log_path() -> str:
    return str(_DEBUG_LOG_PATH)
