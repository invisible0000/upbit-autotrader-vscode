
# VS Code 터미널에서 자동 가상환경 활성화
if ($env:TERM_PROGRAM -eq "vscode" -and (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "🐍 가상환경 자동 활성화 중..." -ForegroundColor Green
    .\venv\Scripts\Activate.ps1
    Write-Host "✅ 가상환경 활성화 완료: $(Split-Path $env:VIRTUAL_ENV -Leaf)" -ForegroundColor Green
}
