@echo off
REM ============================================
REM Campaign Creative Automation Workflow
REM Windows Launcher Script
REM ============================================

echo.
echo ======================================================================
echo Campaign Creative Automation Workflow
echo ======================================================================
echo.

REM ============================================
REM Check if Python is installed
REM ============================================
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found
echo.

REM ============================================
REM Check if credentials.json exists
REM ============================================
echo [2/4] Checking credentials.json...
if not exist "credentials.json" (
    echo [ERROR] credentials.json not found!
    echo.
    echo Please create credentials.json from the template:
    echo   1. Copy credentials.json.example to credentials.json
    echo   2. Add your API keys:
    echo      - OpenAI API key ^(for GPT-5^)
    echo      - Google Gemini API key ^(for Gemini 2.5 Flash^)
    echo.
    if exist "credentials.json.example" (
        echo Template file found: credentials.json.example
        echo Run: copy credentials.json.example credentials.json
    )
    echo.
    pause
    exit /b 1
)
echo [OK] credentials.json found
echo.

REM ============================================
REM Check if package is installed
REM ============================================
echo [3/4] Checking package installation...
python -c "import campaign_automation" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Package not installed. Installing now...
    echo.
    pip install -e . >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install package
        echo.
        echo Please run manually:
        echo   pip install -e .
        echo.
        pause
        exit /b 1
    )
    echo [OK] Package installed successfully
) else (
    echo [OK] Package already installed
)
echo.

REM ============================================
REM Check if requirements are installed
REM ============================================
echo [4/4] Checking dependencies...
python -c "import yaml, requests, openai, PIL" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Some dependencies missing. Installing from requirements.txt...
    echo.
    pip install -r requirements.txt >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install dependencies
        echo.
        echo Please run manually:
        echo   pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed successfully
) else (
    echo [OK] All dependencies installed
)
echo.

REM ============================================
REM Run the workflow
REM ============================================
echo ======================================================================
echo Starting Campaign Workflow
echo ======================================================================
echo.

REM Pass all arguments to the workflow (supports campaign file and --dropbox flag)
python -m campaign_automation.workflow %*

REM ============================================
REM Check workflow result
REM ============================================
if %ERRORLEVEL% equ 0 (
    echo.
    echo ======================================================================
    echo Workflow completed successfully!
    echo ======================================================================
    echo.
    echo Check the output folder for generated images.
) else (
    echo.
    echo ======================================================================
    echo Workflow failed with errors
    echo ======================================================================
    echo.
    echo Please check the error messages above.
)

echo.
pause
