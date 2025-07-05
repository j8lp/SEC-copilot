@echo off
echo 🤖 SEC-copilot Environment Setup
echo =================================

REM Get the script directory
set SCRIPT_DIR=%~dp0
set VENV_PATH=%SCRIPT_DIR%venv
set ACTIVATE_SCRIPT=%VENV_PATH%\Scripts\activate.bat

REM Check if virtual environment exists
if exist "%ACTIVATE_SCRIPT%" (
    echo ✅ Virtual environment found. Activating...
    call "%ACTIVATE_SCRIPT%"
    
    REM Set PYTHONPATH
    set PYTHONPATH=%SCRIPT_DIR%
    
    echo ✅ Virtual environment activated!
    echo 📍 Project directory: %SCRIPT_DIR%
    
    REM Check if .env file exists
    if exist "%SCRIPT_DIR%.env" (
        echo 📝 .env file found - make sure your API keys are configured
    ) else (
        echo ⚠️  No .env file found. You may need to create one with your API keys:
        echo    OPENAI_API_KEY=your_openai_key
        echo    KAY_API_KEY=your_kay_key
    )
    
    echo.
    echo 🚀 Ready to go! You can now run:
    echo    streamlit run app.py
    echo.
    
) else (
    echo ❌ Virtual environment not found at: %VENV_PATH%
    echo Creating virtual environment...
    
    REM Create virtual environment
    python -m venv "%VENV_PATH%"
    
    if %ERRORLEVEL% == 0 (
        echo ✅ Virtual environment created successfully!
        echo Activating virtual environment...
        call "%ACTIVATE_SCRIPT%"
        
        echo Installing dependencies...
        pip install -r requirements.txt
        
        echo ✅ Setup complete! Virtual environment is ready.
    ) else (
        echo ❌ Failed to create virtual environment. Please check your Python installation.
    )
)

REM Keep the command prompt open
cmd /k
