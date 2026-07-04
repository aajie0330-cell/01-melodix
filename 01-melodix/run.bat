@echo off
setlocal

cd /d "%~dp0"

where powershell >nul 2>nul
if errorlevel 1 (
  echo PowerShell not found. Please install PowerShell and try again.
  exit /b 1
)

powershell -ExecutionPolicy Bypass -File "%~dp0run.ps1"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
  echo.
  echo Startup failed with exit code %EXIT_CODE%.
)

exit /b %EXIT_CODE%
