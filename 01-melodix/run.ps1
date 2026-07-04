$ErrorActionPreference = "Stop"

# Always run from project root so `app.main` imports resolve.
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$VenvDir = Join-Path $ProjectRoot ".venv"
$RequirementsFile = Join-Path $ProjectRoot "streaming\requirements.txt"
$RequiredPythonMinor = "3.12"

try {
    $pyRuntimes = & py -0p 2>$null
}
catch {
    $pyRuntimes = ""
}

if ($LASTEXITCODE -ne 0 -or -not ($pyRuntimes -match "-V:3\.12")) {
    throw "Python 3.12 is required for MSSQL/pyodbc setup. Install Python 3.12 and run this script again."
}

if (Test-Path $VenvDir) {
    $venvVersion = & "$VenvDir\Scripts\python.exe" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ($venvVersion -ne $RequiredPythonMinor) {
        Write-Warning ".venv uses Python $venvVersion. Recreating with Python $RequiredPythonMinor..."
        Remove-Item -Recurse -Force $VenvDir
    }
}

if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating virtual environment with Python 3.12..."
    py -3.12 -m venv $VenvDir
}

$ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
if (-not (Test-Path $ActivateScript)) {
    throw "Virtual environment activation script not found: $ActivateScript"
}

. $ActivateScript

$pythonVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($pythonVersion -ne $RequiredPythonMinor) {
    throw "Activated python is $pythonVersion but $RequiredPythonMinor is required."
}

if (-not (Test-Path $RequirementsFile)) {
    throw "Requirements file not found: $RequirementsFile"
}

Write-Host "Installing dependencies..."
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r $RequirementsFile

Write-Host ""
Write-Host "  +------------------------------+"
Write-Host "  |   melodix  ·  01             |"
Write-Host "  |   http://localhost:8000      |"
Write-Host "  +------------------------------+"
Write-Host ""

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
