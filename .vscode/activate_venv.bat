@echo off
REM VS Code Terminal Virtual Environment Activator
REM GitHub Copilot이 여는 터미널에서 자동으로 가상환경 활성화

echo 🐍 Activating Python virtual environment...

REM 가상환경 경로 설정
set VENV_PATH=D:\projects\upbit-autotrader-vscode\.venv
set WORKSPACE_PATH=D:\projects\upbit-autotrader-vscode

REM 작업 디렉토리로 이동
cd /d "%WORKSPACE_PATH%"

REM 가상환경 활성화
if exist "%VENV_PATH%\Scripts\activate.bat" (
    call "%VENV_PATH%\Scripts\activate.bat"
    echo ✅ Virtual environment activated: .venv
) else (
    echo ❌ Virtual environment not found: %VENV_PATH%
)

REM Python 정보 출력
python --version 2>nul
if %errorlevel% equ 0 (
    echo 🐍 Python is ready
) else (
    echo ⚠️ Python not found
)

echo ---
echo 🎯 Terminal ready for development!
echo.
