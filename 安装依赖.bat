@echo off
chcp 65001 >nul
title 安装依赖
cd /d "D:\伟澳新能源\AIO获客系统"

set "PY=C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo.
echo  正在安装依赖包（streamlit / pandas）...
echo  首次安装可能需要 1-3 分钟，请耐心等待。
echo.
"%PY%" -m pip install -r requirements.txt

echo.
echo  依赖安装完成！请双击 start.bat 启动系统。
echo.
pause
