@echo off
chcp 65001 >nul
title YuxTrans 安装程序

echo.
echo ╔════════════════════════════════════╗
echo ║     YuxTrans v0.1.0 安装程序      ║
echo ║     AI 翻译工具 - 轻量版          ║
echo ╚════════════════════════════════════╝
echo.

:: 检测 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [×] 未检测到 Python
    echo.
    echo 请先安装 Python 3.10 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^1') do set PYVER=%%i
echo [✓] 检测到 Python %PYVER%
echo.

:: 检测 pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo [×] pip 不可用
    pause
    exit /b 1
)

:: 安装核心依赖
echo [1/4] 安装核心依赖 (httpx, pyyaml)...
pip install httpx pyyaml -q
if errorlevel 1 (
    echo [×] 核心依赖安装失败
    pause
    exit /b 1
)
echo     完成!
echo.

:: 询问桌面端
echo 是否安装桌面端?
echo   - 需要下载约 100MB
echo   - 提供系统托盘、快捷键、划词翻译等功能
echo.
set /p install_desktop="输入 y 安装桌面端，其他键跳过: "

if /i "%install_desktop%"=="y" (
    echo.
    echo [2/4] 安装桌面端 (PyQt6)...
    pip install PyQt6 -q
    if errorlevel 1 (
        echo [×] 桌面端安装失败，跳过
    ) else (
        echo     完成!
    )
) else (
    echo [2/4] 跳过桌面端安装
)
echo.

:: 安装 yuxtrans
echo [3/4] 安装 YuxTrans...
pip install -e . -q
if errorlevel 1 (
    echo [×] YuxTrans 安装失败
    pause
    exit /b 1
)
echo     完成!
echo.

:: 安装浏览器插件
echo [4/4] 浏览器插件安装指引:
echo.
echo   1. 打开 Chrome 浏览器
echo   2. 地址栏输入: chrome://extensions/
echo   3. 开启"开发者模式"
echo   4. 点击"加载已解压的扩展程序"
echo   5. 选择 extension 目录
echo.

:: 完成
echo ╔════════════════════════════════════╗
echo ║          安装完成!                ║
echo ╠════════════════════════════════════╣
echo ║  使用方法:                        ║
echo ║    命令行: yuxtrans --help        ║
echo ║    桌面端: 运行 yuxtrans          ║
echo ║    插件:   加载 extension 目录    ║
echo ╚════════════════════════════════════╝
echo.

pause