# MindCare Mental Health App Launcher
# PowerShell Script

Write-Host "================================================" -ForegroundColor Blue
Write-Host "MindCare Mental Health App Manager" -ForegroundColor Cyan
Write-Host "Complete Project Management Solution" -ForegroundColor Magenta
Write-Host "================================================" -ForegroundColor Blue

Write-Host "[*] Starting development server..." -ForegroundColor Yellow

# Check if Python is available
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
    Write-Host "[+] Python found: $pythonCmd" -ForegroundColor Green
} else {
    Write-Host "[-] ERROR: Python not found!" -ForegroundColor Red
    exit 1
}

# Check project files
$appFile = "app.py"
$mainFile = "main.py"

if (!(Test-Path $appFile) -and !(Test-Path $mainFile)) {
    Write-Host "[-] ERROR: No main application file found" -ForegroundColor Red
    exit 1
}

Write-Host "[+] Project files check passed" -ForegroundColor Green

# Determine main file to run
$mainToRun = $mainFile
if (!(Test-Path $mainFile) -and (Test-Path $appFile)) {
    $mainToRun = $appFile
}

Write-Host "[i] Starting Flask server from $mainToRun..." -ForegroundColor Blue
Write-Host "[i] Server will be available at: http://localhost:8005" -ForegroundColor Blue
Write-Host "[i] Press Ctrl+C to stop the server" -ForegroundColor Blue
Write-Host "============================================" -ForegroundColor Yellow

# Set environment variables
$env:FLASK_ENV = "development"
$env:FLASK_DEBUG = "1"

# Start the server
Write-Host "[+] Starting Flask server..." -ForegroundColor Green
& $pythonCmd $mainToRun