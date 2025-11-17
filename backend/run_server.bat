@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
uvicorn app.main_standalone:app --reload --host 0.0.0.0 --port 8000
