# QAsync 아키텍처 컴플라이언스 도구 설치 스크립트
# 목적: pre-commit hook과 CI/CD 정적 검사 활성화

param(
    [switch]$Install,
    [switch]$Check,
    [switch]$Help
)

function Show-Help {
    Write-Host "QAsync 아키텍처 컴플라이언스 도구" -ForegroundColor Green
    Write-Host ""
    Write-Host "사용법:" -ForegroundColor Yellow
    Write-Host "  .\setup-qasync-compliance.ps1 -Install  # pre-commit hook 설치"
    Write-Host "  .\setup-qasync-compliance.ps1 -Check    # 현재 상태 검사"
    Write-Host "  .\setup-qasync-compliance.ps1 -Help     # 도움말 표시"
    Write-Host ""
    Write-Host "설치 후 매 커밋마다 자동으로 금지 패턴 검사가 수행됩니다." -ForegroundColor Cyan
}

function Install-PreCommitHook {
    Write-Host "🔧 Pre-commit hook 설치 중..." -ForegroundColor Yellow

    try {
        # pre-commit 설치 확인
        $preCommitExists = Get-Command pre-commit -ErrorAction SilentlyContinue

        if (-not $preCommitExists) {
            Write-Host "📦 pre-commit 설치 중..." -ForegroundColor Cyan
            pip install pre-commit
        }

        # pre-commit hook 설치
        pre-commit install

        Write-Host "✅ Pre-commit hook이 성공적으로 설치되었습니다!" -ForegroundColor Green
        Write-Host "이제 매 커밋마다 QAsync 컴플라이언스 검사가 자동으로 수행됩니다." -ForegroundColor Cyan

    } catch {
        Write-Host "❌ Pre-commit hook 설치 실패: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "수동으로 다음 명령어를 실행해보세요:" -ForegroundColor Yellow
        Write-Host "  pip install pre-commit" -ForegroundColor Gray
        Write-Host "  pre-commit install" -ForegroundColor Gray
    }
}

function Test-QAsyncCompliance {
    Write-Host "🔍 QAsync 아키텍처 컴플라이언스 검사 시작..." -ForegroundColor Yellow
    Write-Host ""

    # 1. 금지 패턴 검사
    Write-Host "1️⃣ 금지 패턴 검사:" -ForegroundColor Cyan

    $pythonFiles = Get-ChildItem upbit_auto_trading -Recurse -Include *.py -ErrorAction SilentlyContinue

    if (-not $pythonFiles) {
        Write-Host "⚠️ Python 파일을 찾을 수 없습니다." -ForegroundColor Yellow
        return
    }

    $prohibitedPatterns = @(
        "new_event_loop\(",
        "run_until_complete\(",
        "asyncio\.run\(",
        "set_event_loop\(None\)",
        "QApplication\.exec\(\)"
    )

    $totalViolations = 0
    $violationsByPattern = @{}

    foreach ($pattern in $prohibitedPatterns) {
        $violations = $pythonFiles | Select-String -Pattern $pattern
        $violationsByPattern[$pattern] = $violations
        $totalViolations += $violations.Count

        if ($violations.Count -gt 0) {
            Write-Host "  ❌ $pattern : $($violations.Count)개 발견" -ForegroundColor Red
        } else {
            Write-Host "  ✅ $pattern : 위반 없음" -ForegroundColor Green
        }
    }

    # 2. 권장 패턴 확인
    Write-Host "`n2️⃣ 권장 패턴 사용 현황:" -ForegroundColor Cyan

    $recommendedPatterns = @(
        "@asyncSlot",
        "qasync\.",
        "TaskManager",
        "LoopGuard"
    )

    foreach ($pattern in $recommendedPatterns) {
        $matches = $pythonFiles | Select-String -Pattern $pattern

        if ($matches.Count -gt 0) {
            Write-Host "  ✅ $pattern : $($matches.Count)개 파일에서 사용" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️ $pattern : 미사용 (도입 권장)" -ForegroundColor Yellow
        }
    }

    # 3. 결과 요약
    Write-Host "`n📊 검사 결과 요약:" -ForegroundColor Green
    Write-Host "  - 검사된 파일: $($pythonFiles.Count)개"
    Write-Host "  - 금지 패턴 위반: $totalViolations개"

    if ($totalViolations -gt 0) {
        Write-Host "`n🚨 QAsync 아키텍처 위반 사항 발견!" -ForegroundColor Red
        Write-Host "상세 위반 사항:" -ForegroundColor Yellow

        foreach ($pattern in $prohibitedPatterns) {
            $violations = $violationsByPattern[$pattern]
            if ($violations.Count -gt 0) {
                Write-Host "`n  패턴: $pattern" -ForegroundColor Red
                foreach ($violation in $violations) {
                    Write-Host "    📁 $($violation.Filename):$($violation.LineNumber)" -ForegroundColor Gray
                }
            }
        }

        Write-Host "`n💡 해결 방법:" -ForegroundColor Green
        Write-Host "  1. docs/big_issues/issue_01_20250926/QAsync_REFACTORING_WORK_GUIDE.md 참조"
        Write-Host "  2. tasks/active/TASK_20250926_01-qasync_architecture_migration.md 태스크 수행"
        Write-Host "  3. @asyncSlot 데코레이터와 TaskManager 사용으로 전환"
    } else {
        Write-Host "✅ QAsync 아키텍처 컴플라이언스 완벽 통과!" -ForegroundColor Green
    }

    # 4. CI/CD 상태 확인
    Write-Host "`n3️⃣ CI/CD 설정 확인:" -ForegroundColor Cyan

    if (Test-Path ".github\workflows\qasync-check.yml") {
        Write-Host "  ✅ GitHub Actions 워크플로우 존재" -ForegroundColor Green
    } else {
        Write-Host "  ❌ GitHub Actions 워크플로우 없음" -ForegroundColor Red
    }

    if (Test-Path ".pre-commit-config.yaml") {
        Write-Host "  ✅ Pre-commit 설정 존재" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Pre-commit 설정 없음" -ForegroundColor Red
    }
}

# 메인 실행 로직
if ($Help -or (-not $Install -and -not $Check)) {
    Show-Help
} elseif ($Install) {
    Install-PreCommitHook
} elseif ($Check) {
    Test-QAsyncCompliance
}
