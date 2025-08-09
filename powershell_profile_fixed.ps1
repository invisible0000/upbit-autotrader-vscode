# PowerShell Profile for VS Code Shell Integration and Enhanced Development Experience

# VS Code Shell Integration
if ($env:TERM_PROGRAM -eq "vscode") {
    try {
        . "$(code --locate-shell-integration-path pwsh)"
    } catch {
        # Shell integration 실패 시 무시하고 계속 진행
    }
}

# Enhanced Terminal Settings for Development
try {
    Set-PSReadlineOption -PredictionSource History
    Set-PSReadlineOption -PredictionViewStyle ListView
    Set-PSReadlineOption -EditMode Windows
} catch {
    # PSReadLine 설정 실패 시 무시하고 계속 진행
}

# Custom Aliases for Upbit Autotrader Development
Set-Alias -Name ut -Value "python run_desktop_ui.py"
Set-Alias -Name test-db -Value "python test_database_path_change.py"

# Project-Specific Functions
function Show-UpbitStatus {
    Write-Host "📊 Upbit Autotrader 프로젝트 상태 확인" -ForegroundColor Cyan
    Write-Host ("=" * 50) -ForegroundColor Gray

    # 데이터베이스 파일 확인
    Write-Host "💾 데이터베이스 파일:" -ForegroundColor Yellow
    if (Test-Path "data") {
        Get-ChildItem "data/*.sqlite3" -ErrorAction SilentlyContinue | ForEach-Object {
            $size = [math]::Round($_.Length / 1KB, 2)
            Write-Host "   $($_.Name): ${size} KB" -ForegroundColor Green
        }
    } else {
        Write-Host "   ❌ data 폴더를 찾을 수 없습니다" -ForegroundColor Red
    }

    # 가상환경 확인
    if ($env:VIRTUAL_ENV) {
        Write-Host "🐍 가상환경: $env:VIRTUAL_ENV" -ForegroundColor Green
    } else {
        Write-Host "⚠️  가상환경이 활성화되지 않음" -ForegroundColor Yellow
    }

    Write-Host ("=" * 50) -ForegroundColor Gray
}

Write-Host "✅ VS Code Shell Integration 프로파일 설정 완료!" -ForegroundColor Green
