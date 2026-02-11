@echo off
chcp 65001 >nul
echo 随手记账单转换工具 - 快速启动脚本
echo ========================================

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误：未找到Python，请先安装Python
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查虚拟环境是否存在
if not exist ".venv" (
    echo 📦 创建虚拟环境...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo ❌ 错误：虚拟环境创建失败
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
)

REM 激活虚拟环境
echo 🚀 激活虚拟环境...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ 错误：虚拟环境激活失败
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 🛠️  检查依赖...
pip list --format=freeze | findstr /i "openpyxl pandas xlrd pdfplumber" >nul
if %errorlevel% neq 0 (
    echo 📥 安装依赖包...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ 错误：依赖安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖安装成功
)

echo ========================================
echo ✅ 环境准备完成！
echo 📖 使用说明：
echo   - 处理单个文件：python src/main.py input/xxx.csv output/
echo   - 批量处理：python src/main.py input/ output/
echo   - 查看帮助：python src/main.py --help
echo ========================================

REM 保持窗口打开
powershell.exe -NoExit -Command "Write-Host '按任意键退出...'; $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown'); exit"