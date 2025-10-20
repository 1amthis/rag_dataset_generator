@echo off
REM Launch script for RAG Dataset Generator GUI (Windows)

echo 🚀 Starting RAG Dataset Generator...
echo.

REM Check if venv exists
if not exist "venv\" (
    echo Virtual environment not found. Please run setup.bat first.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if gradio is installed
python -c "import gradio" 2>nul
if errorlevel 1 (
    echo Installing Gradio...
    pip install gradio>=4.0.0
)

REM Launch GUI
echo Opening GUI in your browser...
echo Press Ctrl+C to stop the server
echo.

cd src
python gui_gradio.py
