from pydantic_settings import BaseSettings
from typing import Dict, List
import json
from pathlib import Path


class Settings(BaseSettings):
    APP_NAME: str = "E-Waste Detection API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    MODEL_NAME: str = "efficientdet_d0"
    MODEL_INPUT_SIZE: int = 512
    PREFERRED_CHECKPOINT_NAME: str = "efficientdet-d0_0_6860.pth"
    IMAGE_MEAN: list = [0.485, 0.456, 0.406]
    IMAGE_STD: list = [0.229, 0.224, 0.225]

    # Precision-first demo thresholds.
    # Goal: avoid embarrassing false positives in live/uncontrolled scenes.
    DETECTION_CONFIDENCE_THRESHOLD: float = 0.5
    # Keep a narrow fallback so true demo objects are not silently dropped.
    DETECTION_ENABLE_FALLBACK: bool = False
    DETECTION_FALLBACK_MIN_CONFIDENCE: float = 0.35
    DETECTION_FALLBACK_TOP_K: int = 2
    # Hazard classification is class-based, but keep this for compatibility.
    HAZARDOUS_THRESHOLD: float = 0.78
    MIN_DETECTION_AREA_RATIO: float = 0.00008
    # Demo mode: allowlist to prevent weird off-class hallucinations.
    ENABLE_ALLOWED_CLASS_FILTER: bool = True
    ALLOWED_DETECTION_CLASSES: List[str] = [
        "Smartphone",
        "Battery",
        "PCB",
        "Laptop",
        "CRT-TV",
        "CRT-Monitor",
        "Flat-Panel-TV",
        "Flat-Panel-Monitor",
        "Electronic-Waste",
    ]
    # Class-specific confidence floors to suppress common false positives.
    CLASS_CONFIDENCE_FLOOR: Dict[str, float] = {
        "Smartphone": 0.76,
        "Battery": 0.7,
        "PCB": 0.64,
        "Laptop": 0.62,
        "CRT-Monitor": 0.7,
        "Flat-Panel-TV": 0.7,
        "Flat-Panel-Monitor": 0.68,
        "CRT-TV": 0.72,
        "Electronic-Waste": 0.88,
    }
    ENABLE_CLASS_CONFIDENCE_FLOOR: bool = True
    DEFAULT_CLASS_CONFIDENCE_FLOOR: float = 0.64
    # Reject ambiguous classifications (top1 too close to top2).
    DETECTION_MIN_CLASS_MARGIN: float = 0.1
    COLLAPSE_AMBIGUOUS_TO_EWASTE: bool = False
    # Phone-first live behavior: keep confident phone detections, suppress noisy others.
    PHONE_PRIORITY_ENABLED: bool = True
    PHONE_PRIORITY_CLASS: str = "Smartphone"
    PHONE_PRIORITY_MIN_CONFIDENCE: float = 0.78
    PHONE_PRIORITY_OTHER_MIN_CONFIDENCE: float = 0.72
    # Prevent the generic class from swallowing a person-sized region in live camera mode.
    GENERIC_EWASTE_MAX_AREA_RATIO: float = 0.18
    GENERIC_EWASTE_MAX_ASPECT_RATIO: float = 1.6
    FINAL_LABEL_NMS_IOU: float = 0.35
    HAZARDOUS_CLASSES: List[str] = [
        "Battery", "CRT-Monitor", "CRT-TV", "PCB",
        "Smoke-Detector", "Compact-Fluorescent-Lamps", "Neon-Sign",
        "Straight-Tube-Fluorescent-Lamp", "Air-Conditioner", "Boiler",
        "Cooled-Dispenser", "Cooling-Display", "Dehumidifier", "Desktop-PC",
        "Drone", "Electric-Bicycle", "Flashlight", "Flat-Panel-Monitor",
        "Flat-Panel-TV", "Freezer", "HDD", "Laptop", "Microwave",
        "Photovoltaic-Panel", "Printer", "Projector", "Refrigerator",
        "Rotary-Mower", "SSD", "Server", "Smart-Watch", "Smartphone",
        "Soldering-Iron", "Street-Lamp", "Tablet", "Electronic-Waste",
    ]

    CLASSES: Dict[int, str] = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_class_labels()
        self._resolve_checkpoint_path()

    def _resolve_checkpoint_path(self):
        project_root = Path(__file__).parent.parent.parent
        ckpt_dir = project_root / "ewaste_model" / "checkpoints" / "ewaste"
        if ckpt_dir.exists():
            preferred = ckpt_dir / self.PREFERRED_CHECKPOINT_NAME
            if preferred.exists() and preferred.stat().st_size > 1_000_000:
                self._checkpoint_path = preferred
                print(f"[config] Preferred checkpoint: {preferred.name}")
                return
            pth_files = sorted(ckpt_dir.glob("efficientdet-d0_*.pth"), key=lambda p: p.stat().st_mtime)
            # Filter out tiny files (corrupted checkpoints)
            pth_files = [p for p in pth_files if p.stat().st_size > 1_000_000]
            if pth_files:
                self._checkpoint_path = pth_files[-1]
                print(f"[config] Checkpoint: {self._checkpoint_path.name}")
                return

        fallback = project_root / "ewaste_model" / "checkpoints" / "efficientdet-d0.pth"
        self._checkpoint_path = fallback
        if fallback.exists():
            print(f"[config] Using pretrained checkpoint: {fallback}")
        else:
            print(f"[config] No checkpoint found, expected in: {ckpt_dir}")

    @property
    def CHECKPOINT_PATH(self) -> Path:
        return self._checkpoint_path

    def _load_class_labels(self):
        project_root = Path(__file__).parent.parent.parent
        paths = [
            project_root / "class_labels.json",
            project_root / "triton_model_repo" / "efficientdet_d5" / "class_labels.json",
        ]

        for p in paths:
            if p.exists():
                try:
                    with open(p, "r") as f:
                        data = json.load(f)
                    self.CLASSES = {int(k): v["name"] for k, v in data["classes"].items()}
                    print(f"[config] Loaded {len(self.CLASSES)} classes from {p}")
                    return
                except Exception as e:
                    print(f"[config] Warning: could not load {p}: {e}")

        self._use_default_classes()

    def _use_default_classes(self):
        default_classes = [
            "Electronic-Waste", "Air-Conditioner", "Bar-Phone", "Battery",
            "Blood-Pressure-Monitor", "Boiler", "CRT-Monitor", "CRT-TV",
            "Calculator", "Camera", "Ceiling-Fan", "Christmas-Lights",
            "Clothes-Iron", "Coffee-Machine", "Compact-Fluorescent-Lamps",
            "Computer-Keyboard", "Computer-Mouse", "Cooled-Dispenser",
            "Cooling-Display", "Dehumidifier", "Desktop-PC", "Digital-Oscilloscope",
            "Dishwasher", "Drone", "Electric-Bicycle", "Electric-Guitar",
            "Electrocardiograph-Machine", "Electronic-Keyboard", "Exhaust-Fan",
            "Flashlight", "Flat-Panel-Monitor", "Flat-Panel-TV", "Floor-Fan",
            "Freezer", "Glucose-Meter", "HDD", "Hair-Dryer", "Headphone",
            "LED-Bulb", "Laptop", "Microwave", "Music-Player", "Neon-Sign",
            "Network-Switch", "Non-Cooled-Dispenser", "Oven", "PCB",
            "Patient-Monitoring-System", "Photovoltaic-Panel", "PlayStation-5",
            "Power-Adapter", "Printer", "Projector", "Pulse-Oximeter",
            "Range-Hood", "Refrigerator", "Rotary-Mower", "Router", "SSD",
            "Server", "Smart-Watch", "Smartphone", "Smoke-Detector",
            "Soldering-Iron", "Speaker", "Stove", "Straight-Tube-Fluorescent-Lamp",
            "Street-Lamp", "TV-Remote-Control", "Table-Lamp", "Tablet",
            "Telephone-Set", "Toaster", "Tumble-Dryer", "USB-Flash-Drive",
            "Vacuum-Cleaner", "Washing-Machine", "Xbox-Series-X",
        ]
        self.CLASSES = {i: name for i, name in enumerate(default_classes)}
        print(f"[config] Using {len(self.CLASSES)} default classes")

    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://localhost:4173",
    ]
    # Live camera/video mode needs a materially higher budget than manual uploads.
    RATE_LIMIT_DETECT: str = "240/minute"

    class Config:
        env_file = ".env"


settings = Settings()
