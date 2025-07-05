# SEC-copilot Auto-Activation Script
# This script automatically activates the virtual environment and sets up the environment

Write-Host "🤖 SEC-copilot Environment Setup" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Check if virtual environment exists
$VenvPath = Join-Path $ScriptDir "venv"
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"

if (Test-Path $ActivateScript) {
    Write-Host "✅ Virtual environment found. Activating..." -ForegroundColor Yellow
    & $ActivateScript
    
    # Set PYTHONPATH
    $env:PYTHONPATH = $ScriptDir
    
    Write-Host "✅ Virtual environment activated!" -ForegroundColor Green
    Write-Host "📍 Project directory: $ScriptDir" -ForegroundColor Cyan
    Write-Host "🐍 Python path: $((Get-Command python).Source)" -ForegroundColor Cyan
    
    # Check if .env file exists and remind user about API keys
    $EnvFile = Join-Path $ScriptDir ".env"
    if (Test-Path $EnvFile) {
        Write-Host "📝 .env file found - make sure your API keys are configured" -ForegroundColor Yellow
    } else {
        Write-Host "⚠️  No .env file found. You may need to create one with your API keys:" -ForegroundColor Yellow
        Write-Host "   OPENAI_API_KEY=your_openai_key" -ForegroundColor Gray
        Write-Host "   KAY_API_KEY=your_kay_key" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "🚀 Ready to go! You can now run:" -ForegroundColor Green
    Write-Host "   streamlit run app.py" -ForegroundColor White
    Write-Host ""
    
} else {
    Write-Host "❌ Virtual environment not found at: $VenvPath" -ForegroundColor Red
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    
    # Create virtual environment
    python -m venv $VenvPath
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Virtual environment created successfully!" -ForegroundColor Green
        Write-Host "Activating virtual environment..." -ForegroundColor Yellow
        & $ActivateScript
        
        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        pip install -r requirements.txt
        
        Write-Host "✅ Setup complete! Virtual environment is ready." -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create virtual environment. Please check your Python installation." -ForegroundColor Red
    }
}
