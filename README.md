# Untrashify — E-Waste Detection System

Untrashify detects e-waste items from images using a React frontend and FastAPI backend.

## Quick Install (Simple)

### Requirements

- Python 3.10+
- Node.js 18+
- npm

### 1) Clone

```bash
git clone <repository-url>
cd untrashify-main
```

### 2) Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

### 3) Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 4) Run backend (Terminal 1)

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8002
```

### 5) Run frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`.

## Why backend is port 8002

Frontend dev proxy is configured to call backend at `http://localhost:8002`.

## Quick Test

Backend health:

```bash
curl http://localhost:8002/health
```

Detection test:

```bash
curl -X POST http://localhost:8002/detect -F "file=@ewaste_image.jpg"
```

## What is in GitHub vs what is not

### Included in repository

- Backend source code (`backend/`)
- Frontend source code (`frontend/`)
- Class metadata (`class_labels.json`)
- Training scripts (`training/`)
- Docker config (`docker-compose.yml`)

### Not included in repository (must be added/downloaded separately)

- Python virtual environments (`venv/`, `.venv/`, etc.)
- Node modules (`node_modules/`)
- `.env` local secrets file
- Large model files/checkpoints (`ewaste_model/checkpoints/`, `*.pth`, `*.onnx`)
- Large training datasets (`ewaste_model/dataset/`, training dataset folders)

These are intentionally excluded by `.gitignore`.

## Model setup note

For meaningful detection accuracy, place a trained checkpoint under:

- `ewaste_model/checkpoints/ewaste/efficientdet-d0_*.pth`

Fallback path used by config:

- `ewaste_model/checkpoints/efficientdet-d0.pth`

If no checkpoint exists, backend may start but detections will be weak or empty.

## Optional: Docker

```bash
docker-compose up --build
```

- Frontend: `http://localhost`
- Backend: `http://localhost:8000`
