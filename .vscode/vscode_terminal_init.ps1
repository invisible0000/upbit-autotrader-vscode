# VS Code 터미널 자동 가상환경 활성화 스크립트 v2.0
# 안전하고 견고한 가상환경 활성화

param(
    [switch]$Quiet = $false
)

# 오류 처리 설정
$ErrorActionPreference = "SilentlyContinue"

function Write-SafeHost {
    param($Message, $Color = "White")
    if (-not $Quiet) {
        Write-Host $Message -ForegroundColor $Color
    }
}

# 가상환경 경로 설정
$venvPath = "D:/projects/upbit-autotrader-vscode/.venv/Scripts/Activate.ps1"
$workspaceRoot = "D:/projects/upbit-autotrader-vscode"

try {
    # 작업 디렉토리 설정
    if (Test-Path $workspaceRoot) {
        Set-Location $workspaceRoot
        Write-SafeHost "📁 작업 디렉토리: $workspaceRoot" -Color Cyan
    }

    # 가상환경 활성화
    if (Test-Path $venvPath) {
        Write-SafeHost "🐍 가상환경을 활성화합니다..." -Color Yellow
        & $venvPath

        # 활성화 확인
        if ($env:VIRTUAL_ENV) {
            $venvName = Split-Path $env:VIRTUAL_ENV -Leaf
            Write-SafeHost "✅ 가상환경 활성화 성공: ($venvName)" -Color Green
        } else {
            Write-SafeHost "⚠️  가상환경 활성화 실패" -Color Red
        }
    } else {
        Write-SafeHost "❌ 가상환경을 찾을 수 없습니다: $venvPath" -Color Red
    }

    # Python 환경 정보
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $pythonVersion = python --version 2>$null
        Write-SafeHost "� Python: $pythonVersion" -Color Green
    }

    Write-SafeHost "---" -Color Gray

} catch {
    Write-SafeHost "❌ 오류 발생: $($_.Exception.Message)" -Color Red
}

# 환경 설정 완료 메시지
Write-SafeHost "🎯 터미널 준비 완료!" -Color Cyan
