@echo off
setlocal

rem Determine script directory (api\scripts)
set SCRIPT_DIR=%~dp0
set ROOT_DIR=%SCRIPT_DIR%..

rem Change to api root
cd /d "%ROOT_DIR%"

rem Default environment for local run if not already set
if "%ENVIRONMENT%"=="" set ENVIRONMENT=local

rem If a virtual environment exists at .venv, activate it
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

rem Change into src so top-level modules like config.py can be imported
cd /d "%ROOT_DIR%\src"

rem Run the FastAPI app via uvicorn (local entrypoint)
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

endlocal
