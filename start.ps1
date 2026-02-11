<#
随手记账单转换工具 - PowerShell快速启动脚本
自动处理虚拟环境创建、激活和依赖安装
#>

$ErrorActionPreference = "Stop"

Write-Host "随手记账单转换工具 - PowerShell快速启动脚本" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

# 检查Python是否安装
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python已安装: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误：未找到Python，请先安装Python" -ForegroundColor Red
    Write-Host "下载地址：https://www.python.org/downloads/" -ForegroundColor Blue
    Read-Host "按任意键退出"
    exit 1
}

# 检查虚拟环境是否存在
if (-not (Test-Path ".venv")) {
    Write-Host "📦 创建虚拟环境..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 错误：虚拟环境创建失败" -ForegroundColor Red
        Read-Host "按任意键退出"
        exit 1
    }
    Write-Host "✅ 虚拟环境创建成功" -ForegroundColor Green
}

# 激活虚拟环境
Write-Host "🚀 激活虚拟环境..." -ForegroundColor Yellow
. .venv\Scripts\Activate.ps1
if (-not $env:VIRTUAL_ENV) {
    Write-Host "❌ 错误：虚拟环境激活失败" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}
Write-Host "✅ 虚拟环境已激活: $env:VIRTUAL_ENV" -ForegroundColor Green

# 检查依赖是否安装
Write-Host "🛠️  检查依赖..." -ForegroundColor Yellow
try {
    $requiredPackages = @("openpyxl", "pandas", "xlrd", "pdfplumber")
    $installedPackages = pip list --format=freeze | ForEach-Object { $_.Split('==')[0].ToLower() }
    $missingPackages = @()

    foreach ($pkg in $requiredPackages) {
        if ($pkg.ToLower() -notin $installedPackages) {
            $missingPackages += $pkg
        }
    }

    if ($missingPackages.Count -gt 0) {
        Write-Host "📥 安装缺失的依赖包: $($missingPackages -join ', ')" -ForegroundColor Yellow
        pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ 错误：依赖安装失败" -ForegroundColor Red
            Read-Host "按任意键退出"
            exit 1
        }
        Write-Host "✅ 依赖安装成功" -ForegroundColor Green
    } else {
        Write-Host "✅ 所有依赖已安装" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ 错误：依赖检查失败: $_" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "✅ 环境准备完成！" -ForegroundColor Green
Write-Host "📖 使用说明：" -ForegroundColor Cyan
Write-Host "  - 处理单个文件：python src/main.py input/xxx.csv output/" -ForegroundColor Gray
Write-Host "  - 批量处理：python src/main.py input/ output/" -ForegroundColor Gray
Write-Host "  - 查看帮助：python src/main.py --help" -ForegroundColor Gray
Write-Host "=======================================" -ForegroundColor Cyan

# 保持窗口打开
Read-Host "`n按任意键退出"