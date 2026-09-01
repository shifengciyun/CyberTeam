@echo off
chcp 65001 >nul
echo ================================================
echo   CyberStrikeAI Python 打包脚本
echo ================================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM 安装依赖
echo [1/4] 安装项目依赖...
pip install -r requirements.txt -q

REM 安装 PyInstaller
echo [2/4] 安装 PyInstaller...
pip install pyinstaller -q

REM 清理旧构建
echo [3/4] 清理旧构建...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

REM 打包
echo [4/4] 开始打包...
pyinstaller run.spec --noconfirm

echo.
echo ================================================
echo   打包完成！
echo   输出目录: dist\CyberStrikeAI\
echo   可执行文件: dist\CyberStrikeAI\CyberStrikeAI.exe
echo ================================================
echo.
echo 使用方法:
echo   1. 复制 dist\CyberStrikeAI 整个目录到目标机器
echo   2. 复制 .env.example 为 .env 并填写 API Key
echo   3. 双击 CyberStrikeAI.exe 启动
echo.
pause
