# Phase 2 실행 스크립트 - 폴더 구조 정리

## 1. 백업 생성
Write-Host "=== Phase 2: 폴더 구조 정리 시작 ===" -ForegroundColor Green
Write-Host "1. 백업 생성 중..." -ForegroundColor Yellow

$triggerBuilderPath = "upbit_auto_trading\ui\desktop\screens\strategy_management\trigger_builder"
$enginesPath = "$triggerBuilderPath\engines"
$backupPath = "$triggerBuilderPath\engines_backup"

if (Test-Path $enginesPath) {
    if (Test-Path $backupPath) {
        Remove-Item $backupPath -Recurse -Force
    }
    Copy-Item $enginesPath $backupPath -Recurse
    Write-Host "✅ 백업 생성 완료: $backupPath" -ForegroundColor Green
} else {
    Write-Host "❌ engines 폴더를 찾을 수 없습니다: $enginesPath" -ForegroundColor Red
    exit 1
}

## 2. 폴더명 변경
Write-Host "2. 폴더명 변경 중..." -ForegroundColor Yellow
$newEnginesPath = "$triggerBuilderPath\mini_simulation_engines"

if (Test-Path $newEnginesPath) {
    Write-Host "⚠️ mini_simulation_engines 폴더가 이미 존재합니다. 제거 중..." -ForegroundColor Yellow
    Remove-Item $newEnginesPath -Recurse -Force
}

Move-Item $enginesPath $newEnginesPath
Write-Host "✅ 폴더명 변경 완료: engines → mini_simulation_engines" -ForegroundColor Green

## 3. 심볼릭 링크 생성 (임시 호환성)
Write-Host "3. 호환성 심볼릭 링크 생성 중..." -ForegroundColor Yellow

# Windows에서 Junction 생성 (관리자 권한 불필요)
cmd /c "mklink /J `"$enginesPath`" `"$newEnginesPath`""

if (Test-Path "$enginesPath\data") {
    Write-Host "✅ 심볼릭 링크 생성 완료" -ForegroundColor Green
} else {
    Write-Host "❌ 심볼릭 링크 생성 실패" -ForegroundColor Red
    # 롤백
    Move-Item $newEnginesPath $enginesPath
    Write-Host "🔄 롤백 완료" -ForegroundColor Yellow
    exit 1
}

## 4. 테스트
Write-Host "4. 기능 테스트 중..." -ForegroundColor Yellow
Write-Host "🔍 테스트를 위해 python run_desktop_ui.py를 실행해주세요" -ForegroundColor Cyan
Write-Host "📝 트리거 빌더에서 미니차트 시뮬레이션이 정상 동작하는지 확인하세요" -ForegroundColor Cyan

Write-Host "`n=== Phase 2 완료 ===" -ForegroundColor Green
Write-Host "다음 단계: 중복 코드 분석 및 제거" -ForegroundColor Blue
