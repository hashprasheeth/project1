# How to Train the E-Waste Detection Model

This guide explains how to train the EfficientDet-D5 model on the **UNU-KEYS E-Waste Dataset (77 classes)** using Google Colab and Roboflow.

## Overview

- **Dataset**: UNU-KEYS E-Waste Dataset (COCO format)
- **Source**: Roboflow
- **Classes**: 77 e-waste categories
- **Model**: EfficientDet-D5
- **Platform**: Google Colab (cloud training)
- **Output**: ONNX model for local Triton deployment

---

## Prerequisites

1. **Roboflow Account**: Sign up at [roboflow.com](https://roboflow.com)
2. **Roboflow API Key**: Get from [roboflow.com/settings/api](https://app.roboflow.com/settings/api)
3. **Google Account**: For Google Colab access
4. **Google Drive**: For saving trained models

---

## Step 1: Get Roboflow API Key

1. Go to [https://app.roboflow.com/settings/api](https://app.roboflow.com/settings/api)
2. Copy your **Private API Key**
3. Keep it handy for the next step

---

## Step 2: Open Google Colab Notebook

### Option A: Upload Notebook to Colab

1. Download `train_ewaste_d5.ipynb` from this repository
2. Go to [Google Colab](https://colab.research.google.com)
3. Click **File → Upload Notebook**
4. Upload the notebook file

### Option B: Open from GitHub (if hosted)

1. Go to [Google Colab](https://colab.research.google.com)
2. Click **File → Open Notebook → GitHub**
3. Enter the repository URL

---

## Step 3: Configure Runtime

1. In Colab, go to **Runtime → Change runtime type**
2. Select **GPU** as hardware accelerator
3. Choose **T4 GPU** (free tier) or **A100** (Colab Pro)
4. Click **Save**

---

## Step 4: Run Training Cells

### Cell 1: Install Dependencies

Run the first cell to install PyTorch, EfficientDet, and Roboflow:

```python
!git clone https://github.com/zylo117/Yet-Another-EfficientDet-Pytorch.git
%cd Yet-Another-EfficientDet-Pytorch
!pip install -q -r requirements.txt
!pip install -q roboflow onnx onnxruntime-gpu
```

**Expected time**: 2-3 minutes

### Cell 2: Download E-Waste Dataset

Replace `YOUR_API_KEY_HERE` with your actual Roboflow API key:

```python
from roboflow import Roboflow

ROBOFLOW_API_KEY = "paste_your_key_here"

rf = Roboflow(api_key=ROBOFLOW_API_KEY)
project = rf.workspace("unu-keys").project("ewaste")
dataset = project.version(1).download("coco")
```

**Expected time**: 5-10 minutes (depends on dataset size)

### Cell 3: Configure Model

This cell sets up EfficientDet-D5 for 77 classes. No changes needed.

**Expected time**: < 1 minute

### Cell 4: Train Model

Start training! This will take several hours:

```python
!python train.py -c 5 -p ewaste --batch_size 4 --lr 1e-4 --num_epochs 100
```

**Expected time**: 4-8 hours on T4 GPU, 2-4 hours on A100 GPU

> **Tip**: If you get Out Of Memory (OOM) errors, reduce `batch_size` to 2

### Cell 5: Export to ONNX

After training completes, export the model:

```python
!python export_onnx.py --compound_coef 5 --weights logs/ewaste/best.pth
```

**Expected time**: 1-2 minutes

### Cell 6: Save to Google Drive

Mount Google Drive and save the model:

```python
from google.colab import drive
drive.mount('/content/drive')
# Model automatically saved to /content/drive/MyDrive/ewaste_model/
```

---

## Step 5: Download Model

1. Open [Google Drive](https://drive.google.com)
2. Navigate to **MyDrive/ewaste_model/**
3. Download `model.onnx`

---

## Step 6: Deploy to Local Triton

### Transfer Model

Use the provided transfer script:

```bash
# Navigate to project root
cd d:\untrashify-main

# Transfer model (adjust path to your download location)
python training/transfer_model.py C:\Users\YourName\Downloads\model.onnx
```

The script will:
- Validate the ONNX model
- Copy it to `triton_model_repo/efficientdet_d5/1/model.onnx`
- Verify the transfer

### Start Triton Server

```bash
docker-compose up triton
```

Check logs for successful model loading:
```
Successfully loaded 'efficientdet_d5'
```

---

## Step 7: Test Inference

Upload a sample e-waste image via the API to test the deployment!
