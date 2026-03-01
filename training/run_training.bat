@echo off
REM ============================================================
REM  Untrashify — EfficientDet-D5 E-Waste Training Launcher
REM  Double-click to run the full training pipeline
REM ============================================================
title Untrashify Training Pipeline

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║   Untrashify E-Waste Detection — Training Setup  ║
echo  ╚══════════════════════════════════════════════════╝
echo.

REM Change to training directory
cd /d "%~dp0"

REM Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found in PATH.
    echo  Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Check Git is available (needed to clone EfficientDet repo)
git --version >nul 2>&1
if errorlevel 1 (
    echo  [WARN] Git not found - may fail to clone EfficientDet repo.
    echo  Install Git from https://git-scm.com if errors occur.
    echo.
)

echo  [1/3] Installing Python dependencies...
pip install -q -r requirements_training.txt
if errorlevel 1 (
    echo  [ERROR] pip install failed. Check your internet connection.
    pause
    exit /b 1
)
echo  Done.
echo.

echo  [2/3] Starting training pipeline (5 epochs for demo)...
echo  This will:
echo    - Download the e-waste dataset from Roboflow
echo    - Download pretrained EfficientDet-D5 weights   (~230 MB)
echo    - Fine-tune for 5 epochs
echo    - Export to ONNX for deployment
echo.
echo  Press Ctrl+C at any time to stop.
echo.

python train_local.py --epochs 5 --batch-size 2
if errorlevel 1 (
    echo.
    echo  [ERROR] Training failed. See error messages above.
    pause
    exit /b 1
)

echo.
echo  [3/3] Training complete! Opening results folder...

set RESULTS_DIR=..\ewaste_model\demo_results
if exist "%RESULTS_DIR%" (
    explorer "%RESULTS_DIR%"
)

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║   Training Finished Successfully!                ║
echo  ║                                                  ║
echo  ║   Run inference demo:                            ║
echo  ║     python infer_demo.py                         ║
echo  ║                                                  ║
echo  ║   Deploy (requires Docker):                      ║
echo  ║     cd .. ^& docker-compose up                   ║
echo  ╚══════════════════════════════════════════════════╝
echo.
pause
