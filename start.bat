@echo off
chcp 65001 >nul
title 户外路灯外贸 AIO 获客系统
cd /d "D:\伟澳新能源\AIO获客系统"

set "PY=C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo.
echo  ============================================
echo   户外路灯外贸 AIO 获客系统 正在启动...
echo   浏览器会自动打开 http://localhost:8501
echo   关闭本窗口即可退出系统
echo  ============================================
echo.

"%PY%" -m streamlit run app.py

echo.
echo  系统已退出。按任意键关闭窗口...
pause >nul
