#!/usr/bin/env pwsh
<#
.SYNOPSIS
    数英网数据统计与智能对话系统启动脚本

.DESCRIPTION
    一键启动数英网数据统计与智能对话系统
    自动检查环境、依赖和配置，然后启动Web服务器

.PARAMETER ConfigFile
    配置文件路径，默认为 config.env

.EXAMPLE
    .\启动系统.ps1
    .\启动系统.ps1 -ConfigFile "my_config.env"
#>

param(
    [string]$ConfigFile = "config.env"
)

# 设置控制台编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 设置窗口标题
$Host.UI.RawUI.WindowTitle = "数英网数据统计与智能对话系统"

function Write-Header {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "                数英网数据统计与智能对话系统" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Test-Environment {
    Write-Host "🔧 检查系统环境..." -ForegroundColor Green
    
    # 检查虚拟环境
    if (-not (Test-Path "venv\Scripts\python.exe")) {
        Write-Host "❌ 错误: 未找到虚拟环境" -ForegroundColor Red
        Write-Host "💡 请先创建虚拟环境: python -m venv venv" -ForegroundColor Yellow
        return $false
    }
    
    Write-Host "✅ 虚拟环境检查通过" -ForegroundColor Green
    return $true
}

function Test-Config {
    Write-Host "📋 检查配置文件..." -ForegroundColor Green
    
    if (-not (Test-Path $ConfigFile)) {
        Write-Host "⚠️ 未找到配置文件 $ConfigFile" -ForegroundColor Yellow
        Write-Host "📝 正在创建默认配置文件..." -ForegroundColor Cyan
        
        $configContent = @"
# 数英网数据统计与智能对话系统配置文件
# 请根据实际情况修改以下配置

# Gemini API配置
GEMINI_API_KEY=your_gemini_api_key_here

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
DEBUG_MODE=false

# 数据配置
DATA_FOLDER=data
OUTPUT_FOLDER=output
WEB_DATA_FILE=web_data.json

# 分析配置
BATCH_SIZE=50
MAX_WORKERS=2
POOL_SIZE=3

# 延时配置
MIN_DELAY=2
MAX_DELAY=4
BATCH_DELAY=8

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=output/logs/scraper.log

# 浏览器配置
AUTO_OPEN_BROWSER=true
BROWSER_URL=http://localhost:5000
"@
        
        $configContent | Out-File -FilePath $ConfigFile -Encoding UTF8
        Write-Host "✅ 配置文件已创建: $ConfigFile" -ForegroundColor Green
        Write-Host "💡 请编辑配置文件，设置您的 Gemini API 密钥" -ForegroundColor Yellow
    } else {
        Write-Host "✅ 配置文件检查通过" -ForegroundColor Green
    }
    
    return $true
}

function Test-Dependencies {
    Write-Host "📦 检查依赖包..." -ForegroundColor Green
    
    $requiredPackages = @("flask", "flask_cors", "pandas", "openpyxl")
    $missingPackages = @()
    
    foreach ($package in $requiredPackages) {
        try {
            & "venv\Scripts\python.exe" -c "import $package" 2>$null
            Write-Host "✅ $package" -ForegroundColor Green
        } catch {
            $missingPackages += $package
            Write-Host "❌ $package" -ForegroundColor Red
        }
    }
    
    if ($missingPackages.Count -gt 0) {
        Write-Host "📥 正在安装缺少的依赖包..." -ForegroundColor Cyan
        $packages = $missingPackages -join " "
        & "venv\Scripts\python.exe" -m pip install $packages google-generativeai jieba
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ 依赖包安装失败" -ForegroundColor Red
            return $false
        }
        
        Write-Host "✅ 依赖包安装完成" -ForegroundColor Green
    }
    
    return $true
}

function Test-DataFolder {
    Write-Host "📁 检查数据文件夹..." -ForegroundColor Green
    
    if (-not (Test-Path "data")) {
        Write-Host "❌ 错误: 未找到 data 文件夹" -ForegroundColor Red
        Write-Host "💡 请确保 data 文件夹存在并包含Excel文件" -ForegroundColor Yellow
        return $false
    }
    
    $excelFiles = Get-ChildItem "data\*.xlsx" -ErrorAction SilentlyContinue
    if ($excelFiles.Count -eq 0) {
        Write-Host "⚠️ 警告: data 文件夹中没有Excel文件" -ForegroundColor Yellow
    } else {
        Write-Host "✅ 找到 $($excelFiles.Count) 个Excel文件" -ForegroundColor Green
    }
    
    return $true
}

function Start-System {
    Write-Host "🚀 启动系统..." -ForegroundColor Green
    Write-Host ""
    
    try {
        & "venv\Scripts\python.exe" "start_dashboard.py"
    } catch {
        Write-Host "❌ 系统启动失败: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    return $true
}

# 主函数
function Main {
    Write-Header
    
    # 检查环境
    if (-not (Test-Environment)) {
        Read-Host "按回车键退出"
        exit 1
    }
    
    # 检查配置
    if (-not (Test-Config)) {
        Read-Host "按回车键退出"
        exit 1
    }
    
    # 检查依赖
    if (-not (Test-Dependencies)) {
        Read-Host "按回车键退出"
        exit 1
    }
    
    # 检查数据文件夹
    if (-not (Test-DataFolder)) {
        Read-Host "按回车键退出"
        exit 1
    }
    
    # 启动系统
    Start-System
}

# 执行主函数
Main 