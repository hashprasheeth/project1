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
    IMAGE_MEAN: list = [0.485, 0.456, 0.406]
    IMAGE_STD: list = [0.229, 0.224, 0.225]

    HAZARDOUS_THRESHOLD: float = 0.85
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
    RATE_LIMIT_DETECT: str = "60/minute"

    class Config:
        env_file = ".env"


settings = Settings()
