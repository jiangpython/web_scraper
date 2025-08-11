@echo off
chcp 65001 >nul
echo 🚀 高并发网页爬虫启动器
echo ================================

cd /d "%~dp0"

if not exist venv\ (
    echo ❌ 未找到虚拟环境，请先运行项目安装脚本
    pause
    exit /b 1
)

call venv\Scripts\activate

echo 📋 可用选项:
echo   1. 自动配置 (推荐)
echo   2. 保守模式 (稳定性优先)
echo   3. 平衡模式 (推荐日常使用)
echo   4. 激进模式 (高性能)
echo   5. 极限模式 (仅测试用)
echo   6. 查看所有配置
echo   7. 自定义配置
echo.

set /p choice=请选择配置模式 (1-7): 

if "%choice%"=="1" (
    echo 使用自动推荐配置...
    python run_parallel_scraper_fixed.py --preset auto
) else if "%choice%"=="2" (
    echo 使用保守模式...
    python run_parallel_scraper_fixed.py --preset conservative
) else if "%choice%"=="3" (
    echo 使用平衡模式...
    python run_parallel_scraper_fixed.py --preset balanced
) else if "%choice%"=="4" (
    echo 使用激进模式...
    python run_parallel_scraper_fixed.py --preset aggressive
) else if "%choice%"=="5" (
    echo 使用极限模式...
    python run_parallel_scraper_fixed.py --preset extreme
) else if "%choice%"=="6" (
    echo 显示所有配置预设...
    python parallel_config.py
    echo.
    echo 按任意键返回主菜单...
    pause >nul
    goto :start
) else if "%choice%"=="7" (
    echo 🎛️ 自定义配置...
    set /p workers=输入线程数 (1-10, 默认4): 
    set /p batch=输入批次大小 (10-100, 默认50): 
    set /p pool=输入驱动池大小 (2-15, 默认6): 
    
    set cmd=python run_parallel_scraper_fixed.py --preset balanced
    if not "%workers%"=="" set cmd=%cmd% --max-workers %workers%
    
    echo 执行命令: %cmd%
    %cmd%
) else (
    echo ❌ 无效选择，使用默认自动配置
    python run_parallel_scraper_fixed.py --preset auto
)

echo.
echo 程序执行完毕
pause