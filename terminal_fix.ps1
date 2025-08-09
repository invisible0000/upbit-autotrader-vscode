# 터미널 문제 해결을 위한 진단 스크립트

Write-Host "=== 터미널 환경 진단 ==="

# 1. PowerShell 버전 확인
Write-Host "`n1. PowerShell 버전:"
$PSVersionTable.PSVersion

# 2. 실행 정책 확인
Write-Host "`n2. 실행 정책:"
Get-ExecutionPolicy -List

# 3. 경로 확인
Write-Host "`n3. 경로 확인:"
Write-Host "Current Directory: $PWD"
Write-Host "PowerShell Path: $PSHOME"

# 4. 가상환경 확인
Write-Host "`n4. 가상환경 확인:"
if (Test-Path "D:\projects\upbit-autotrader-vscode\venv") {
    Write-Host "✅ 가상환경 폴더 존재"
    if (Test-Path "D:\projects\upbit-autotrader-vscode\venv\Scripts\Activate.ps1") {
        Write-Host "✅ 활성화 스크립트 존재"
    } else {
        Write-Host "❌ 활성화 스크립트 없음"
    }
} else {
    Write-Host "❌ 가상환경 폴더 없음"
}

# 5. Python 확인
Write-Host "`n5. Python 확인:"
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python: $pythonVersion"
} catch {
    Write-Host "❌ Python 명령어 없음"
}

Write-Host "`n=== 진단 완료 ==="
