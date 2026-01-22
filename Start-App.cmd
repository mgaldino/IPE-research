@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\\Scripts\\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 goto :error
)

echo Installing dependencies...
".venv\\Scripts\\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo Starting app...
".venv\\Scripts\\python.exe" -m app
goto :eof

:error
echo Failed to start the app.
pause
