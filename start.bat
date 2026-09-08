@echo off
cd /d "D:\伟澳新能源\AIO获客系统"
set "PY=C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
echo Starting Wilsolar AIO System...
echo Browser will open: http://localhost:8501
echo (Close this window to stop the system)
"%PY%" -m streamlit run app.py
pause
