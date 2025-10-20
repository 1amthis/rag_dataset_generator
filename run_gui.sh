#!/bin/bash
# Launch script for RAG Dataset Generator GUI (Mac/Linux)

echo "🚀 Starting RAG Dataset Generator..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup..."
    ./setup.sh
    if [ $? -ne 0 ]; then
        echo "Setup failed. Please run ./setup.sh manually."
        exit 1
    fi
fi

# Activate virtual environment
source venv/bin/activate

# Check if gradio is installed
if ! python3 -c "import gradio" 2>/dev/null; then
    echo "Installing Gradio..."
    pip install gradio>=4.0.0
fi

# Launch GUI
echo "Opening GUI in your browser..."
echo "Press Ctrl+C to stop the server"
echo ""

cd src
python3 gui_gradio.py
