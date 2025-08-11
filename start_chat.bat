@echo off
chcp 65001
cls
echo.
echo ==========================================
echo    数英网项目爬虫 - AI智能助手
echo ==========================================
echo.

cd /d "%~dp0"

echo 激活虚拟环境...
if not exist "venv\Scripts\activate.bat" (
    echo [错误] 虚拟环境不存在，请先创建虚拟环境
    echo 运行: python -m venv venv
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo 启动AI智能助手...
echo 请稍等，正在初始化...
echo.

python smart_ai_assistant.py

echo.
echo AI助手已退出
pause