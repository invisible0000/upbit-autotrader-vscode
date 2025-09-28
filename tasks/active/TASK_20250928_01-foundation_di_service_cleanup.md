# 📋 TASK_20250928_01: Foundation DI 서비스 정돈

## 🎯 태스크 목표

- **주요 목표**: 의존성 주입 연결 문제 해결 및 기초 서비스 안정화
- **완료 기준**: ApiKeyService None 문제 해결, DI Container 완전 활성화, Legacy 패턴 제거

## 📊 현재 상황 분석

### 🔍 발견된 문제점

1. **DI 연결 불완전**:
   - `ApiKeyService가 None으로 전달됨` 로그 에러 발생
   - `api_settings_presenter.py`에서 ApiKeyService 의존성 주입 실패
   - Container wiring이 불완전하게 적용됨

2. **Legacy 패턴 혼재**:
   - `@inject` 패턴과 Legacy `resolve()` 패턴 혼재 사용
   - `MainWindow`에서 `di_container=None` 같은 Legacy 파라미터 존재
   - Container에서 "Legacy resolve() 호출 감지" 경고 메시지

3. **Silent Failure 패턴**:
   - try-catch로 에러를 숨기는 패턴 다수 존재
   - 실패시 조용히 넘어가서 디버깅 어려움
   - Infrastructure Layer 통합이라고 하지만 실제로는 단순 예외 처리

### 📁 사용 가능한 리소스

- `upbit_auto_trading/infrastructure/dependency_injection/container.py`: DI Container 정의
- `docs/DEPENDENCY_INJECTION_QUICK_GUIDE.md`: DI 적용 가이드
- 로그 파일: `logs/session_20250928_182519_PID35296.log`: 에러 분석 자료

## 🔄 체계적 작업 절차 (필수 준수)

### 8단계 작업 절차

1. **📋 작업 항목 확인**: 태스크 문서에서 구체적 작업 내용 파악
2. **🔍 검토 후 세부 작업 항목 생성**: 작업을 더 작은 단위로 분해
3. **🔄 작업중 마킹**: 해당 작업 항목을 `[-]` 상태로 변경
4. **⚙️ 작업 항목 진행**: 실제 작업 수행
5. **✅ 작업 내용 확인**: 결과물 검증 및 품질 확인
6. **📝 상세 작업 내용 업데이트**: 태스크 문서에 진행사항 기록
7. **[x] 작업 완료 마킹**: 해당 작업 항목을 완료 상태로 변경
8. **⏳ 작업 승인 대기**: 다음 단계 진행 전 검토 및 승인

### 작업 상태 마커

- **[ ]**: 미완료 (미시작)
- **[-]**: 진행 중 (현재 작업)
- **[x]**: 완료

## 🛠️ 작업 계획

### Phase 1: DI Container 연결 진단 및 수정

- [ ] **DI Container Wiring 상태 분석**: 현재 등록된 Provider 및 Wiring 모듈 확인
- [ ] **ApiKeyService Provider 연결 검증**: Container에서 ApiKeyService가 올바르게 등록되었는지 확인
- [ ] **Wiring 모듈 등록 확인**: `api_settings_presenter.py`가 wiring_modules에 포함되었는지 확인
- [ ] **@inject 데코레이터 적용 검증**: ApiSettingsPresenter 생성자에 @inject 패턴 적용 확인

### Phase 2: Legacy 패턴 제거

- [ ] **Legacy resolve() 호출 탐지**: 코드베이스에서 Legacy resolve() 패턴 사용 위치 파악
- [ ] **MainWindow Legacy 파라미터 제거**: `di_container=None` 같은 불필요한 파라미터 제거
- [ ] **@inject 패턴으로 마이그레이션**: Legacy 패턴을 @inject 패턴으로 전환
- [ ] **Container 경고 메시지 제거**: Legacy 호출로 인한 경고 메시지 해결

### Phase 3: 에러 처리 패턴 개선

- [ ] **Silent Failure 패턴 탐지**: try-catch로 에러를 숨기는 코드 위치 파악
- [ ] **Fail-Fast 패턴 적용**: 중요한 의존성 실패시 명확한 에러 발생하도록 변경
- [ ] **Infrastructure 로깅 강화**: 실패 원인을 명확히 로그로 남기도록 개선
- [ ] **DI 실패시 명확한 에러**: 의존성 주입 실패시 구체적인 원인 표시

### Phase 4: 검증 및 테스트

- [ ] **DI Container 통합 테스트**: 모든 Provider가 올바르게 주입되는지 테스트
- [ ] **ApiKeyService 연결 테스트**: 설정 화면에서 ApiKeyService가 정상 작동하는지 확인
- [ ] **Legacy 패턴 완전 제거 검증**: 코드베이스에서 Legacy 패턴 완전 제거 확인
- [ ] **전체 애플리케이션 실행 테스트**: `python run_desktop_ui.py`로 전체 기능 정상 동작 확인

## 🔧 개발할 도구

- `di_connection_verifier.py`: DI Container 연결 상태를 진단하는 도구
- `legacy_pattern_detector.py`: Legacy 패턴 사용을 탐지하는 스크립트
- `silent_failure_finder.py`: Silent Failure 패턴을 찾는 분석 도구

## 🎯 성공 기준

- ✅ ApiKeyService None 에러 완전 해결
- ✅ 모든 DI Provider 정상 연결 및 주입
- ✅ Legacy resolve() 패턴 완전 제거
- ✅ Silent Failure 패턴 90% 이상 개선
- ✅ DI Container 경고 메시지 제로
- ✅ 설정 화면 API 키 관리 기능 정상 동작
- ✅ `python run_desktop_ui.py` 에러 없이 실행

## 💡 작업 시 주의사항

### 안전성 원칙

- **백업 필수**: 수정 전 모든 파일 백업 (`*_legacy.py` 형태)
- **단계별 검증**: 각 Phase 완료후 반드시 실행 테스트
- **롤백 준비**: 문제 발생시 즉시 이전 상태로 복구 가능하도록 준비

### DDD 아키텍처 준수

- **계층 위반 금지**: Domain 레이어에 외부 의존성 추가 금지
- **Infrastructure 로깅**: 모든 수정에서 `create_component_logger` 사용
- **@inject 패턴 우선**: 새로운 코드는 반드시 @inject 패턴 사용

### 기술적 제약

- **PowerShell 전용**: Unix 명령어 사용 금지
- **3-DB 분리 유지**: settings.sqlite3, strategies.sqlite3, market_data.sqlite3 구조 유지
- **Dry-Run 기본**: 모든 테스트는 dry_run=True로 시작

## 🚀 즉시 시작할 작업

```powershell
# 1. 현재 DI Container 상태 분석
python -c "
from upbit_auto_trading.infrastructure.dependency_injection.container import ApplicationContainer
container = ApplicationContainer()
print('📊 DI Container 등록 상태:')
for name in dir(container):
    if not name.startswith('_'):
        provider = getattr(container, name)
        if hasattr(provider, 'provided'):
            print(f'  ✅ {name}: {provider.provided}')
"

# 2. ApiKeyService Provider 확인
python -c "
try:
    from upbit_auto_trading.infrastructure.dependency_injection.container import ApplicationContainer
    container = ApplicationContainer()
    api_service = container.api_key_service()
    print(f'✅ ApiKeyService 생성 성공: {type(api_service).__name__}')
except Exception as e:
    print(f'❌ ApiKeyService 생성 실패: {e}')
"

# 3. Legacy 패턴 탐지
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String -Pattern "\.resolve\(|di_container.*resolve"
```

---
**다음 에이전트 시작점**: Phase 1의 "DI Container Wiring 상태 분석"부터 시작하여 체계적으로 문제를 해결하세요.
