# 🔧 TASK_20250928_02 안전한 Git 워크플로우 가이드

> **목적**: Infrastructure 계층 위반 해결 작업의 안전하고 체계적인 진행을 위한 Git 워크플로우 및 체크리스트
> **대상 태스크**: TASK_20250928_02 - Settings Screen Infrastructure 계층 직접 접근 위반 해결
> **작성일**: 2025-09-29
> **적용 범위**: Critical 아키텍처 변경 작업 전반

---

## 📋 Git 브랜치 전략 및 커밋 타이밍

### 1️⃣ 초기 브랜치 설정

```powershell
# 현재 상태 백업
git add -A
git commit -m "🔒 TASK_20250928_02 시작 전 백업 - Infrastructure 계층 위반 해결 작업 전"

# 작업 브랜치 생성 및 이동
git checkout -b fix/settings-infrastructure-violations-phase1-6
git push -u origin fix/settings-infrastructure-violations-phase1-6
```

### 2️⃣ Phase별 커밋 & 푸시 전략

#### Phase 1: 로깅 서비스 DI 구조 구축 (2시간)

```powershell
# Phase 1 시작
Write-Host "🚀 Phase 1 시작: ApplicationLoggingService 구조 구축" -ForegroundColor Green

# 체크포인트 1-1: 인터페이스 정의 후
git add application/services/logging_application_service.py
git commit -m "✨ Phase 1.1: ApplicationLoggingService 인터페이스 정의

- IPresentationLogger 인터페이스 생성
- Application Layer 로깅 서비스 구조 설계
- Infrastructure 의존성 격리 패턴 적용"

# 체크포인트 1-2: DI 컨테이너 등록 후
git add infrastructure/dependency_injection/
git commit -m "🔧 Phase 1.2: DI 컨테이너에 로깅 서비스 등록

- ApplicationContainer에 logging_service 바인딩 추가
- Component별 로깅 컨텍스트 관리 구현
- Singleton 생명주기 적용"

# Phase 1 완료 후 푸시
git push origin fix/settings-infrastructure-violations-phase1-6
Write-Host "✅ Phase 1 완료 - DI 로깅 구조 구축 성공" -ForegroundColor Green
```

**🔄 코파일럿 채팅 Clear 타이밍**: Phase 1 완료 후 (컨텍스트 정리)

#### Phase 2: Settings Screen View 계층 수정 (3시간)

```powershell
# Phase 2 시작 (새 채팅 세션)
Write-Host "🚀 Phase 2 시작: Settings Views Infrastructure 직접 접근 제거" -ForegroundColor Green

# 체크포인트 2-1: 메인 설정 화면 수정 후 (핵심)
git add ui/desktop/screens/settings/settings_screen.py
git commit -m "🔥 Phase 2.1: SettingsScreen Infrastructure 직접 접근 제거

- create_component_logger import 제거
- @inject 데코레이터 적용
- 생성자 의존성 주입 패턴 적용
- 47건 위반 중 메인 파일 해결"

# 즉시 기능 테스트
python run_desktop_ui.py
# 정상 동작 확인 후 푸시
git push origin fix/settings-infrastructure-violations-phase1-6

# 체크포인트 2-2: API Settings Views 수정 후
git add ui/desktop/screens/settings/api_settings/
git commit -m "🔧 Phase 2.2: API Settings Views Infrastructure 접근 제거

- api_settings_view.py 등 8개 파일 수정
- Infrastructure 직접 import 완전 제거
- 의존성 주입 패턴 일관성 있게 적용"

# 체크포인트 2-3: Database Settings Views 수정 후
git add ui/desktop/screens/settings/database_settings/
git commit -m "🔧 Phase 2.3: Database Settings Views Infrastructure 접근 제거

- database_settings_view.py 등 5개 파일 수정
- Widget 클래스들 DI 패턴 적용
- 로깅 서비스 생성자 주입으로 변경"

# Phase 2 완료 후 푸시 & 중간 검증
python docs\architecture_review\tools\mvp_quick_analyzer.py --component settings --violations-only
git push origin fix/settings-infrastructure-violations-phase1-6
Write-Host "✅ Phase 2 완료 - Settings Views 계층 정리 성공" -ForegroundColor Green
```

**🔄 코파일럿 채팅 Clear 타이밍**: Phase 2 완료 후 (대량 파일 수정 후 컨텍스트 정리)

#### Phase 3: Settings Presenter 계층 수정 (2시간)

```powershell
# Phase 3 시작 (새 채팅 세션)
Write-Host "🚀 Phase 3 시작: Settings Presenters Infrastructure 접근 제거" -ForegroundColor Green

# 체크포인트 3-1: Presenter 파일들 수정 후
git add ui/desktop/screens/settings/*/presenters/
git commit -m "🔧 Phase 3.1: Settings Presenters Infrastructure 접근 제거

- database_settings_presenter.py 등 Presenter 파일들 수정
- get_path_service 등 Infrastructure 직접 호출 제거
- Application Service를 통한 간접 접근 패턴 적용"

# Phase 3 완료 후 푸시
git push origin fix/settings-infrastructure-violations-phase1-6
Write-Host "✅ Phase 3 완료 - Presenters 계층 정리 성공" -ForegroundColor Green
```

#### Phase 4: DI 설정 업데이트 (1시간)

```powershell
# Phase 4 시작
Write-Host "🚀 Phase 4 시작: DI 컨테이너 설정 최종 업데이트" -ForegroundColor Green

# 체크포인트 4-1: 컨테이너 설정 완료 후
git add infrastructure/dependency_injection/
git commit -m "⚙️ Phase 4.1: DI 컨테이너 Settings 관련 서비스 완전 설정

- MVPContainer Settings MVP 바인딩 완성
- ApplicationContainer 로깅 서비스 생명주기 최적화
- 순환 참조 방지 패턴 적용"

git push origin fix/settings-infrastructure-violations-phase1-6
```

#### Phase 5: View→Presenter 직접 생성 위반 해결 (2시간)

```powershell
# Phase 5 시작
Write-Host "🚀 Phase 5 시작: View→Presenter 직접 생성 위반 해결" -ForegroundColor Green

# 체크포인트 5-1: 핵심 위반 제거 후
git add ui/desktop/screens/settings/settings_screen.py
git commit -m "🔥 Phase 5.1: SettingsScreen Presenter 직접 생성 위반 해결

- line 98, 185, 210, 248 Presenter 직접 생성 제거
- MVPContainer를 통한 완전한 의존성 주입 적용
- V20250928_051 위반 완전 해결"

# 즉시 기능 테스트 (가장 중요한 변경사항)
python run_desktop_ui.py
# 정상 동작 확인 후 푸시
git push origin fix/settings-infrastructure-violations-phase1-6
```

**🔄 코파일럿 채팅 Clear 타이밍**: Phase 5 완료 후 (핵심 아키텍처 변경 완료)

#### Phase 6: 최종 테스트 및 검증 (1.5시간)

```powershell
# Phase 6 시작 (새 채팅 세션 - 최종 검증)
Write-Host "🚀 Phase 6 시작: 최종 테스트 및 검증" -ForegroundColor Green

# 자동 분석 도구 재실행
python docs\architecture_review\tools\mvp_quick_analyzer.py --component settings --violations-only

# Infrastructure 직접 import 검증
Get-ChildItem upbit_auto_trading\ui\desktop\screens\settings -Recurse -Include *.py | Select-String -Pattern "from upbit_auto_trading\.infrastructure"

# 최종 커밋
git add .
git commit -m "✅ Phase 6: TASK_20250928_02 최종 완료 검증

- Infrastructure 직접 접근 47건 완전 해결
- View→Presenter 직접 생성 4건 완전 해결
- 자동 분석 도구 Critical 위반 0건 달성
- 모든 Settings 기능 정상 동작 확인

해결된 위반사항:
- V20250928_001: Infrastructure 계층 직접 접근 (47건)
- V20250928_051: View→Presenter 직접 생성 (4건)"

# 최종 푸시
git push origin fix/settings-infrastructure-violations-phase1-6
Write-Host "🎉 TASK_20250928_02 완전 성공!" -ForegroundColor Green
```

---

## 📋 안전 체크리스트 및 롤백 전략

### 🚨 각 Phase별 필수 검증 사항

```powershell
# Phase별 안전 검증 스크립트
function Test-PhaseCompletion {
    param($Phase)

    Write-Host "🔍 Phase $Phase 검증 시작..." -ForegroundColor Yellow

    # 1. 애플리케이션 시작 테스트
    Write-Host "1️⃣ 애플리케이션 시작 테스트"
    python -c "
import sys
sys.path.append('.')
try:
    from run_desktop_ui import main
    print('✅ import 성공')
except Exception as e:
    print(f'❌ import 실패: {e}')
    exit(1)
"

    # 2. DI 컨테이너 초기화 테스트
    Write-Host "2️⃣ DI 컨테이너 초기화 테스트"
    python -c "
from upbit_auto_trading.infrastructure.dependency_injection.container import ApplicationContainer
try:
    container = ApplicationContainer()
    container.wire()
    print('✅ DI 컨테이너 정상')
except Exception as e:
    print(f'❌ DI 컨테이너 오류: {e}')
    exit(1)
"

    # 3. 구문 오류 검사
    Write-Host "3️⃣ Python 구문 검사"
    python -m py_compile (Get-ChildItem upbit_auto_trading\ui\desktop\screens\settings -Recurse -Include *.py)

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Phase $Phase 검증 통과" -ForegroundColor Green
        return $true
    } else {
        Write-Host "❌ Phase $Phase 검증 실패" -ForegroundColor Red
        return $false
    }
}

# 사용법
if (-not (Test-PhaseCompletion "1")) {
    Write-Host "⚠️ 롤백 권장: git reset --hard HEAD~1" -ForegroundColor Yellow
}
```

### 🔄 긴급 롤백 절차

```powershell
# 긴급 롤백 스크립트
function Invoke-EmergencyRollback {
    param($CommitCount = 1)

    Write-Host "🚨 긴급 롤백 시작 - $CommitCount 커밋 되돌리기" -ForegroundColor Red

    # 현재 상태 임시 백업
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    git stash push -m "emergency_backup_$timestamp"

    # 롤백 실행
    git reset --hard HEAD~$CommitCount

    # 검증
    python run_desktop_ui.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 롤백 성공 - 정상 상태 복구" -ForegroundColor Green
    } else {
        Write-Host "❌ 롤백 후에도 문제 지속" -ForegroundColor Red
    }
}
```

### 🛡️ 각 Phase별 위험 요소 및 대응책

#### Phase 1 위험 요소

- **위험**: DI 컨테이너 설정 오류로 인한 순환 참조
- **대응**: 각 서비스별 의존성 그래프 사전 검토
- **롤백**: ApplicationContainer 설정 이전 상태로 복원

#### Phase 2 위험 요소

- **위험**: 대량 파일 수정으로 인한 기존 기능 중단
- **대응**: 메인 파일 우선 수정 후 즉시 기능 테스트
- **롤백**: 파일별 개별 롤백 가능

#### Phase 5 위험 요소

- **위험**: View→Presenter 연결 구조 변경으로 인한 UI 오작동
- **대응**: 각 Presenter 연결 후 즉시 해당 설정 탭 테스트
- **롤백**: settings_screen.py 핵심 파일만 롤백

---

## 🎯 성공 완료 후 메인 브랜치 통합

```powershell
# 모든 Phase 성공 후 메인 브랜치 통합
Write-Host "🎉 TASK_20250928_02 완전 성공 - 메인 브랜치 통합" -ForegroundColor Green

# 메인 브랜치로 이동
git checkout master
git pull origin master

# 작업 브랜치 머지
git merge fix/settings-infrastructure-violations-phase1-6

# 최종 통합 테스트
python run_desktop_ui.py
python docs\architecture_review\tools\mvp_quick_analyzer.py --component settings --violations-only

# 메인 브랜치 푸시
git push origin master

# 작업 브랜치 정리 (선택사항)
git branch -d fix/settings-infrastructure-violations-phase1-6
git push origin --delete fix/settings-infrastructure-violations-phase1-6

Write-Host "✅ TASK_20250928_02 완전 완료 및 메인 브랜치 통합 성공!" -ForegroundColor Green
```

---

## 📊 권장 코파일럿 채팅 Clear 타이밍 요약

| Phase | Clear 타이밍 | 이유 |
|-------|-------------|------|
| Phase 1 완료 후 | DI 구조 구축 완료 | 컨텍스트 정리, 새로운 아키텍처 관점 준비 |
| Phase 2 완료 후 | 대량 View 파일 수정 완료 | 메모리 정리, 과도한 파일 수정 컨텍스트 정리 |
| Phase 5 완료 후 | 핵심 아키텍처 변경 완료 | 새로운 시각으로 검증 준비, 핵심 변경 완료 |
| Phase 6 시작 시 | 최종 검증 단계 | 깨끗한 컨텍스트로 문제 발견 능력 극대화 |

---

## 🎯 성공 기준 및 완료 지표

### ✅ 필수 완료 사항

- [ ] Infrastructure 직접 접근 47건 완전 제거
- [ ] View→Presenter 직접 생성 4건 완전 해결
- [ ] 자동 분석 도구에서 Critical 위반 0건 달성
- [ ] 모든 Settings 화면 기능 정상 동작

### 📈 성공 지표

- [ ] `Get-ChildItem upbit_auto_trading\ui\desktop\screens\settings -Recurse -Include *.py | Select-String -Pattern "from upbit_auto_trading\.infrastructure"` 결과 0건
- [ ] `python docs\architecture_review\tools\mvp_quick_analyzer.py --component settings --violations-only` 결과 Critical 0건
- [ ] `python run_desktop_ui.py` 실행하여 모든 설정 탭 정상 동작 확인
- [ ] 로깅 출력이 DI를 통해 정상 작동

---

## 🔗 관련 문서 및 참조

- **원본 태스크**: `tasks/active/TASK_20250928_02_infrastructure_layer_fix.md`
- **아키텍처 가이드**: `docs/DDD_아키텍처_패턴_가이드.md`
- **의존성 주입 가이드**: `docs/DEPENDENCY_INJECTION_ARCHITECTURE.md`
- **MVP 패턴 가이드**: `docs/MVP_ARCHITECTURE.md`
- **자동 분석 도구**: `docs/architecture_review/tools/mvp_quick_analyzer.py`

---

**작성일**: 2025-09-29
**적용 대상**: TASK_20250928_02 Infrastructure 계층 위반 해결
**예상 소요시간**: 11.5시간 (Phase별 분할 진행)
**우선순위**: Critical (P0)
