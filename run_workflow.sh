#!/bin/bash
# ============================================
# Campaign Creative Automation Workflow
# Linux/Mac Launcher Script
# ============================================

echo ""
echo "======================================================================"
echo "Campaign Creative Automation Workflow"
echo "======================================================================"
echo ""

# ============================================
# Check if Python is installed
# ============================================
echo "[1/4] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not in PATH"
    echo ""
    echo "Please install Python 3.8 or higher:"
    echo "  - Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  - macOS: brew install python3"
    echo "  - Or download from: https://www.python.org/downloads/"
    echo ""
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "[OK] Python $PYTHON_VERSION found"
echo ""

# ============================================
# Check if credentials.json exists
# ============================================
echo "[2/4] Checking credentials.json..."
if [ ! -f "credentials.json" ]; then
    echo "[ERROR] credentials.json not found!"
    echo ""
    echo "Please create credentials.json from the template:"
    echo "  1. Copy credentials.json.example to credentials.json"
    echo "  2. Add your API keys:"
    echo "     - OpenAI API key (for GPT-5)"
    echo "     - Google Gemini API key (for Gemini 2.5 Flash)"
    echo ""
    if [ -f "credentials.json.example" ]; then
        echo "Template file found: credentials.json.example"
        echo "Run: cp credentials.json.example credentials.json"
    fi
    echo ""
    exit 1
fi
echo "[OK] credentials.json found"
echo ""

# ============================================
# Check if package is installed
# ============================================
echo "[3/4] Checking package installation..."
if ! python3 -c "import campaign_automation" 2>/dev/null; then
    echo "[WARNING] Package not installed. Installing now..."
    echo ""
    if ! pip3 install -e . > /dev/null 2>&1; then
        echo "[ERROR] Failed to install package"
        echo ""
        echo "Please run manually:"
        echo "  pip3 install -e ."
        echo ""
        exit 1
    fi
    echo "[OK] Package installed successfully"
else
    echo "[OK] Package already installed"
fi
echo ""

# ============================================
# Check if requirements are installed
# ============================================
echo "[4/4] Checking dependencies..."
if ! python3 -c "import yaml, requests, openai, PIL" 2>/dev/null; then
    echo "[WARNING] Some dependencies missing. Installing from requirements.txt..."
    echo ""
    if ! pip3 install -r requirements.txt > /dev/null 2>&1; then
        echo "[ERROR] Failed to install dependencies"
        echo ""
        echo "Please run manually:"
        echo "  pip3 install -r requirements.txt"
        echo ""
        exit 1
    fi
    echo "[OK] Dependencies installed successfully"
else
    echo "[OK] All dependencies installed"
fi
echo ""

# ============================================
# Run the workflow
# ============================================
echo "======================================================================"
echo "Starting Campaign Workflow"
echo "======================================================================"
echo ""

# Pass all arguments to the workflow (supports campaign file and --dropbox flag)
python3 -m campaign_automation.workflow "$@"

# ============================================
# Check workflow result
# ============================================
if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================================"
    echo "Workflow completed successfully!"
    echo "======================================================================"
    echo ""
    echo "Check the output folder for generated images."
else
    echo ""
    echo "======================================================================"
    echo "Workflow failed with errors"
    echo "======================================================================"
    echo ""
    echo "Please check the error messages above."
fi

echo ""
