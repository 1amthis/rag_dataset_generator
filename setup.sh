#!/bin/bash
# Setup script for RAG Dataset Generator

echo "Setting up RAG Dataset Generator..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
REQUIRED_VERSION="3.8"

if (( $(echo "$PYTHON_VERSION < $REQUIRED_VERSION" | bc -l) )); then
    echo "Error: Python $REQUIRED_VERSION or higher is required (found $PYTHON_VERSION)"
    exit 1
fi

echo "Python version: OK ($PYTHON_VERSION)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Edit .env and add your OpenAI API key before running the tool!"
    echo "  nano .env"
else
    echo ".env file already exists"
fi

# Create output directory
mkdir -p output

echo ""
echo "Setup complete! Next steps:"
echo "1. Edit .env and add your OpenAI API key:"
echo "   nano .env"
echo ""
echo "2. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "3. Run the tool:"
echo "   python3 src/main.py your_document.pdf"
echo ""
echo "For help:"
echo "   python3 src/main.py --help"
