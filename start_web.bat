@echo off
chcp 65001 >nul
cls

echo ======================================================
echo  数英网项目数据面板 - Web 服务器
echo ======================================================
echo.

echo [INFO] 当前目录: %CD%
echo [INFO] 切换到项目目录...
cd /d "%~dp0"
echo [INFO] 项目目录: %CD%
echo.

echo [INFO] 检查虚拟环境...
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] 虚拟环境不存在！请先创建虚拟环境
    echo.
    pause
    exit /b 1
)

echo [INFO] 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] 虚拟环境激活失败！
    echo.
    pause
    exit /b 1
)
echo [INFO] 虚拟环境激活成功
echo.

echo [INFO] 检查必要文件...
if not exist "web_server.py" (
    echo [ERROR] web_server.py 不存在！
    pause
    exit /b 1
)

echo [INFO] 启动Web服务器...
echo [INFO] 访问地址: http://localhost:5000
echo [INFO] AI助手已集成，支持智能对话
echo [INFO] 按 Ctrl+C 停止服务器
echo ======================================================
echo.

python web_server.py

echo.
echo ======================================================
echo [INFO] Web服务器已停止
echo ======================================================
pause
