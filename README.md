# Untrashify — E-Waste Detection System

AI-powered platform for detecting and classifying electronic waste in images. Uses **EfficientDet-D0** trained on the **E-Waste Dataset (78 classes)** from Roboflow, with **PyTorch inference** and a FastAPI backend.

## Overview

- **78 E-Waste Classes**: Electronic-Waste, Battery, CRT-Monitor, Laptop, Smartphone, PCB, and 72 other categories
- **PyTorch Inference**: Direct model loading from `.pth` checkpoint (no Triton required)
- **Hazardous Material Detection**: Flags dangerous items (batteries, CRTs, PCBs, etc.) above configurable confidence threshold
- **Safety Interlock**: Real-time hazardous detection triggers alerts in the dashboard
- **Production Ready**: FastAPI backend with rate limiting, file validation, security headers, and structured logging

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Browser  →  http://localhost:5173 (dev) or :80 (Docker)     │
└──────────────────────────┬──────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │   React Frontend        │
              │   Vite + TailwindCSS    │
              │   /api/* → proxy        │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │   FastAPI Backend       │
              │   PyTorch EfficientDet  │
              │   SafetyEngine (NMS)    │
              └─────────────────────────┘
```

- **Frontend**: React SPA with live webcam/video detection, analytics, and class explorer
- **Backend**: FastAPI loads EfficientDet-D0 checkpoint, runs inference, post-processes with SafetyEngine (anchor decode, NMS, hazardous flagging)

## Dataset & Training

- **Dataset**: E-Waste Dataset (COCO format) from Roboflow  
  - Workspace: `electronic-waste-detection`  
  - Project: `e-waste-dataset-r0ojc`  
  - Version: 44
- **Model**: EfficientDet-D0 (compound coefficient 0, input size 512×512)
- **Training**: Local via `train_local.py` (no git required; downloads repo as ZIP)
- **Output**: `.pth` checkpoint in `ewaste_model/checkpoints/ewaste/`

See [`training/How_To_Train.md`](training/How_To_Train.md) for Colab training. For local training:

```bash
python training/train_local.py --epochs 5 --batch-size 2
```

## Run The App (Current State)

### Prerequisites

- **Hardware**: GPU recommended (CPU works for inference, but slower)
- **Software**: Python 3.10+, Node.js 18+, npm, Docker (optional)
- **Model files**: Keep weights under `ewaste_model/checkpoints/` (latest local checkpoint is auto-selected)

### 1. Clone Repository

```bash
git clone <repository-url>
cd untrashify-main
```

### 2. Backend Setup (FastAPI + Inference)

Install Python dependencies from repo root:

```bash
pip install -r backend/requirements.txt
```

Start backend from repo root (frontend dev proxy expects `8002`):

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8002
```

Quick health check:

```bash
curl http://localhost:8002/health
```

### 3. Frontend Setup (Vite + React)

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

In dev mode, frontend requests `/api/*` are proxied to `http://localhost:8002`.

### 4. Verify End-to-End Detection

Call the detect endpoint directly:

```bash
curl -X POST http://localhost:8002/detect -F "file=@ewaste_image.jpg"
```

### 5. Model Notes (If Detection Is Empty)

**Option A: Train Locally**

```bash
python training/train_local.py --epochs 5 --batch-size 2
```

Checkpoints are saved to `ewaste_model/checkpoints/ewaste/efficientdet-d0_*.pth`.

**Option B: Use Pretrained Weights (Demo)**

The config falls back to `ewaste_model/checkpoints/efficientdet-d0.pth` (COCO pretrained) if no trained checkpoint exists. The app still runs, but class accuracy will be lower until you train/fine-tune.

### 6. Docker (Optional)

```bash
docker-compose up --build
```

- Frontend: **http://localhost** (port 80)
- Backend: **http://localhost:8000**

See [`DOCKER_GUIDE.md`](DOCKER_GUIDE.md) for details.

## E-Waste Classes (78 Total)

Classes are defined in `class_labels.json`. Examples:

**Hazardous (35 classes):** Battery, CRT-Monitor, CRT-TV, PCB, Smoke-Detector, Compact-Fluorescent-Lamps, Air-Conditioner, Boiler, Laptop, Smartphone, Tablet, HDD, SSD, Refrigerator, Photovoltaic-Panel, etc.

**Non-Hazardous (43 classes):** Bar-Phone, Calculator, Camera, Computer-Keyboard, Computer-Mouse, Router, Speaker, USB-Flash-Drive, Ceiling-Fan, Coffee-Machine, etc.

Each class has `name`, `hazardous`, `recycling_bin` (electronics, hazardous, metals, displays), and `description`.

## API Usage

### Detect E-Waste

```bash
curl -X POST http://localhost:8000/detect -F "file=@ewaste_image.jpg"
```

**Response:**

```json
{
  "detections": [
    {
      "label": "Battery",
      "confidence": 0.92,
      "bbox": [120.5, 80.3, 250.1, 200.7],
      "hazardous": true,
      "recycling_bin": "hazardous",
      "recycling_tip": "⚠️ HAZARDOUS: Dispose at specialized hazardous waste facility only"
    }
  ],
  "is_hazardous": true,
  "hazard_count": 1,
  "total_items": 1,
  "processing_time_ms": 145.23,
  "frame_number": 1
}
```

### Other Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (model loaded status) |
| `GET` | `/stats` | Aggregated detection statistics |
| `GET` | `/logs` | Recent detection log entries |
| `GET` | `/dispatch` | Simulated dispatch queue |
| `POST` | `/track/reset` | Reset tracking statistics |
| `GET` | `/recycling-info/{class_name}` | Recycling info for a class |

## Configuration

Environment variables (or `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_NAME` | `efficientdet_d0` | Model identifier |
| `HAZARDOUS_THRESHOLD` | `0.85` | Confidence threshold for detections |
| `MAX_FILE_SIZE_MB` | `10` | Max upload size |
| `ALLOWED_ORIGINS` | `["http://localhost:5173", ...]` | CORS origins |
| `RATE_LIMIT_DETECT` | `60/minute` | Max detect requests per minute |
| `MIN_DETECTION_AREA_RATIO` | `0.002` | Drops tiny noisy bounding boxes |

Checkpoint path is auto-resolved: `ewaste_model/checkpoints/ewaste/efficientdet-d0_*.pth` (latest) or `ewaste_model/checkpoints/efficientdet-d0.pth` (fallback).

## Quick Backend Test

Smoke-test inference endpoint directly:

```bash
curl -X POST http://localhost:8000/detect -F "file=@ewaste_image.jpg"
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI, Python 3.10+ |
| Inference | PyTorch (EfficientDetBackbone), OpenCV |
| Frontend | React, Vite, TypeScript, TailwindCSS |
| Model | EfficientDet-D0 (78 classes) |
| Training | PyTorch, Yet-Another-EfficientDet-Pytorch, Roboflow |
| Deployment | Docker, Docker Compose |

## Project Structure

```
untrashify-main/
├── backend/           # FastAPI app
│   ├── main.py        # Routes, EWasteTracker
│   ├── core/          # config, logger
│   ├── services/      # onnx_inference (PyTorch), safety_engine
│   └── middleware/    # observability
├── frontend/          # React SPA
├── training/          # train_local.py, export_onnx.py
├── class_labels.json  # 78 class definitions
├── ewaste_model/      # checkpoints, dataset (git-ignored)
└── docker-compose.yml
```

## License

Confidential — Untrashify E-Waste Detection System
