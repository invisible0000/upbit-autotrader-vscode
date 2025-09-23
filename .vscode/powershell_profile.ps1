# PowerShell Profile for VS Code Virtual Environment Auto-Activation
# 위치: $PROFILE.CurrentUserAllHosts (모든 PowerShell 호스트에 적용)

# VS Code 워크스페이스에서 자동으로 가상환경 활성화
function Invoke-VenvAutoActivation {
    param(
        [string]$WorkspacePath = $PWD.Path
    )

    # .venv 폴더 찾기
    $venvPaths = @(
        "$WorkspacePath\.venv\Scripts\Activate.ps1",
        "$WorkspacePath\venv\Scripts\Activate.ps1",
        "$WorkspacePath\.virtualenv\Scripts\Activate.ps1"
    )

    foreach ($venvPath in $venvPaths) {
        if (Test-Path $venvPath) {
            # 이미 가상환경이 활성화된 경우 중복 활성화 방지
            if (-not $env:VIRTUAL_ENV) {
                try {
                    & $venvPath
                    $venvName = Split-Path $env:VIRTUAL_ENV -Leaf
                    Write-Host "🐍 Virtual environment activated: ($venvName)" -ForegroundColor Green
                    break
                } catch {
                    Write-Host "⚠️ Failed to activate virtual environment: $venvPath" -ForegroundColor Yellow
                }
            }
        }
    }
}

# VS Code 터미널에서만 자동 활성화
if ($env:TERM_PROGRAM -eq "vscode" -or $env:VSCODE_PID) {
    # upbit-autotrader-vscode 프로젝트 감지
    if ($PWD.Path -like "*upbit-autotrader-vscode*") {
        Invoke-VenvAutoActivation
    }
}

# Python 관련 유용한 함수들
function Get-PythonInfo {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $pythonPath = (Get-Command python).Source
        $pythonVersion = python --version
        Write-Host "Python Path: $pythonPath" -ForegroundColor Cyan
        Write-Host "Python Version: $pythonVersion" -ForegroundColor Cyan
        if ($env:VIRTUAL_ENV) {
            Write-Host "Virtual Environment: $env:VIRTUAL_ENV" -ForegroundColor Green
        } else {
            Write-Host "Virtual Environment: Not Active" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Python not found in PATH" -ForegroundColor Red
    }
}

# 별칭 설정
Set-Alias pyinfo Get-PythonInfo
