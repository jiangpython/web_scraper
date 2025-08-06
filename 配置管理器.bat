@echo off
chcp 65001 >nul
title 数英网系统配置管理器

echo.
echo ============================================================
echo                数英网系统配置管理器
echo ============================================================
echo.

:: 检查虚拟环境
if not exist "venv\Scripts\python.exe" (
    echo 错误: 未找到虚拟环境，请先创建虚拟环境
    echo 创建方法: python -m venv venv
    pause
    exit /b 1
)

:: 启动配置管理器
echo 正在启动配置管理器...
venv\Scripts\python.exe config_manager.py

if errorlevel 1 (
    echo.
    echo 配置管理器启动失败，错误代码: %errorlevel%
    pause
) 