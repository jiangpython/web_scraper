@echo off
chcp 65001 >nul
title 数英网数据统计与智能对话系统

echo.
echo ============================================================
echo                    数英网数据统计与智能对话系统
echo ============================================================
echo.

:: 检查虚拟环境
if not exist "venv\Scripts\python.exe" (
    echo 错误: 未找到虚拟环境，请先创建虚拟环境
    echo 创建方法: python -m venv venv
    pause
    exit /b 1
)

:: 检查配置文件
if not exist "config.env" (
    echo 警告: 未找到配置文件 config.env
    echo 正在创建默认配置文件...
    copy nul config.env >nul
    echo # 数英网数据统计与智能对话系统配置文件 > config.env
    echo GEMINI_API_KEY=your_gemini_api_key_here >> config.env
    echo SERVER_PORT=5000 >> config.env
    echo.
    echo 请编辑 config.env 文件，设置您的 Gemini API 密钥
    echo.
)

:: 检查依赖包
echo 正在检查依赖包...
venv\Scripts\python.exe -c "import flask, flask_cors, pandas, openpyxl" 2>nul
if errorlevel 1 (
    echo 正在安装依赖包...
    venv\Scripts\python.exe -m pip install flask flask-cors pandas openpyxl google-generativeai jieba
    if errorlevel 1 (
        echo 错误: 依赖包安装失败
        pause
        exit /b 1
    )
)

:: 检查数据文件夹
if not exist "data" (
    echo 错误: 未找到 data 文件夹
    echo 请确保 data 文件夹存在并包含Excel文件
    pause
    exit /b 1
)

:: 启动系统
echo.
echo 正在启动系统...
echo.

:: 使用虚拟环境中的Python启动
venv\Scripts\python.exe start_dashboard.py

:: 如果程序异常退出，暂停显示错误信息
if errorlevel 1 (
    echo.
    echo 程序异常退出，错误代码: %errorlevel%
    echo 请检查错误信息并修复问题
    pause
) 