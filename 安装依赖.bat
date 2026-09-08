@echo off
cd /d "D:\伟澳新能源\AIO获客系统"
set "PY=C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
echo Installing dependencies (streamlit / pandas)...
"%PY%" -m pip install -r requirements.txt
echo Done. Now double-click start.bat
pause
