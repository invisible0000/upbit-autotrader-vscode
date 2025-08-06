# API키 탭 Infrastructure Layer 통합 프롬프트

## 🎯 작업 목표
API키 탭을 Infrastructure Layer v4.0와 통합하여 UI 설정 탭과 동일한 품질의 배치 저장 시스템 구현

## 📋 현재 상태 분석

### ✅ 기존 구현 상태
1. **API 키 관리자 위젯**: `api_key_manager_secure.py` - 완전 구현됨
   - Infrastructure Layer 로깅 v4.0 통합 완료
   - 보안 강화 버전 (암호화, 분리 저장)
   - UI 구성 완료 (Access Key, Secret Key, 권한 설정)
   - 시그널 시스템 구현

2. **Settings Screen 연동**: API 키 탭이 이미 Settings Screen에 통합됨
   - 탭 위젯으로 정상 표시
   - Import 및 인스턴스 생성 완료

### ❌ 미구현 사항
1. **SettingsService 통합 없음**: API 키 관리자가 SettingsService와 연동되지 않음
2. **Infrastructure Layer 서비스 없음**: ApiKeyService 등 서비스 계층 부재
3. **배치 저장 시스템 부재**: UI 설정 탭과 같은 pending changes 시스템 없음
4. **MVP 패턴 미적용**: 의존성 주입 시스템과 연동되지 않음

## 🔧 구현해야 할 작업

### 1. ApiKeyService 생성 (최우선)
**파일**: `upbit_auto_trading/infrastructure/services/api_key_service.py`

**기능**:
- API 키 암호화/복호화 관리
- 설정 데이터베이스와 연동
- API 키 검증 및 테스트
- 권한 설정 관리

**참조**: UI 설정의 SettingsService 패턴 적용

### 2. API 키 관리자 배치 저장 시스템 구현
**파일**: `api_key_manager_secure.py` 수정

**구현 사항**:
- `_pending_changes` 딕셔너리 추가
- `_update_unsaved_changes_state()` 메서드 구현
- 배치 저장 버튼 활성화/비활성화 로직
- UI 설정 탭과 동일한 UX 패턴 적용

### 3. SettingsService 의존성 주입
**파일**:
- `settings_screen.py` - ApiKeyManagerSecure 생성 시 service 주입
- `api_key_manager_secure.py` - constructor에 service 매개변수 추가

### 4. Application Service Container 등록
**파일**: `upbit_auto_trading/infrastructure/dependency_injection/app_service_container.py`

**추가 사항**:
- ApiKeyService 등록
- 의존성 해결 체인 구성

## 📐 구체적 구현 패턴

### UI 설정 탭 성공 패턴 적용
현재 세션에서 완벽하게 구현된 UI 설정 탭의 다음 패턴들을 그대로 적용:

1. **배치 저장 시스템**:
   ```python
   self._pending_changes = {}
   self._has_unsaved_changes = False
   ```

2. **변경 감지 및 버튼 활성화**:
   ```python
   def _on_api_key_changed_batch(self):
       # 변경사항을 pending_changes에 저장
       # 저장 버튼 활성화
   ```

3. **서비스 의존성 주입**:
   ```python
   def __init__(self, parent=None, api_key_service=None):
       self.api_key_service = api_key_service
   ```

4. **Infrastructure Layer 로깅**:
   ```python
   self.logger = create_component_logger("ApiKeyManager")
   ```

## 🎯 성공 기준

### 완료 조건
1. **배치 저장**: API 키 변경 시 즉시 저장되지 않고 "저장" 버튼 활성화
2. **서비스 통합**: ApiKeyService를 통한 데이터베이스 연동
3. **보안 유지**: 기존 암호화 및 보안 기능 완전 보존
4. **UX 일관성**: UI 설정 탭과 동일한 사용자 경험

### 테스트 시나리오
1. API 키 입력 → 저장 버튼 활성화 확인
2. 저장 버튼 클릭 → 데이터베이스 저장 확인
3. 프로그램 재시작 → API 키 복원 확인
4. 테스트 버튼 → API 연결 검증 확인

## � 참조 파일

### 성공 사례 (UI 설정 탭)
- `upbit_auto_trading/ui/desktop/screens/settings/ui_settings.py`
- `upbit_auto_trading/infrastructure/services/settings_service.py`
- `upbit_auto_trading/presentation/mvp_container.py`

### 수정 대상 파일
- `upbit_auto_trading/ui/desktop/screens/settings/api_key_manager_secure.py`
- `upbit_auto_trading/ui/desktop/screens/settings/settings_screen.py`

### 신규 생성 파일
- `upbit_auto_trading/infrastructure/services/api_key_service.py`

## 🚨 주의사항

1. **보안 유지**: 기존 암호화 시스템 절대 손상 금지
2. **원칙 준수**: DDD 아키텍처 및 Infrastructure Layer 원칙 엄격 준수
3. **호환성**: 기존 API 키 파일과 완전 호환성 유지
4. **로깅**: Infrastructure Layer v4.0 로깅 시스템 활용

## � 개발 순서

1. **ApiKeyService 생성** → 2. **API 키 관리자 수정** → 3. **의존성 주입** → 4. **테스트 및 검증**

이 순서로 진행하면 UI 설정 탭의 성공적인 패턴을 그대로 재현할 수 있습니다.
- `docs/edu_docs/trigger_builder_refactoring_logs/12_infrastructure_layer_integration/` - 실무 경험과 문제 해결 가이드
- `docs/COMPONENT_ARCHITECTURE.md` - DDD 기반 시스템 아키텍처
- `docs/LLM_AGENT_TASK_GUIDELINES.md` - LLM 에이전트 TASK 작업 가이드

### 활용 가능한 Infrastructure Layer
- `upbit_auto_trading/infrastructure/application_context.py` - 애플리케이션 컨텍스트
- `upbit_auto_trading/infrastructure/dependency_injection/container.py` - DI Container
- `upbit_auto_trading/infrastructure/services/settings_service.py` - 설정 서비스
- `upbit_auto_trading/infrastructure/services/theme_service.py` - 테마 서비스
- `upbit_auto_trading/logging/` - Smart Logging v3.1 시스템

## 🎯 권장 시작 명령어

### 1. 현재 상태 확인
```bash
# 애플리케이션 정상 동작 확인
python run_desktop_ui.py

# Infrastructure Layer 테스트
python -m pytest tests/infrastructure/ --tb=short

# 프로젝트 구조 파악
ls -la tasks/active/
ls -la docs/
```

### 2. TASK-13 활성화
```bash
# TASK-13을 active 폴더로 이동 (아직 존재하지 않는다면 생성)
# TASK-13 문서 확인 후 작업 시작
```

## 💭 LLM 에이전트에게 전달할 컨텍스트

### 성공한 패턴들 (재사용 권장)
1. **백업 우선 전략**: 모든 핵심 파일 백업 후 작업 진행
2. **점진적 통합**: 한 번에 모든 것을 바꾸지 않고 단계별 진행
3. **폴백 시스템**: 새로운 기능 실패 시 기존 방식으로 자동 전환
4. **구조화된 로깅**: 모든 중요한 상태 변화를 LLM 로그에 기록
5. **단계별 검증**: 각 단계마다 애플리케이션 실행으로 문제 조기 발견

### 주의해야 할 함정들
1. **Qt 컴포넌트 테스트**: Mock 객체 사용으로 메타클래스 충돌 회피
2. **의존성 순환 참조**: 의존성 그래프 사전 설계로 예방
3. **VSCode 터미널 자동화**: 이미 최적화되었으니 건드리지 말 것
4. **설정 마이그레이션**: 기존 QSettings → Infrastructure Layer 점진적 전환

## 🚀 세션 시작 제안

다음과 같이 시작하시면 됩니다:

**"TASK-12 Infrastructure Layer 통합이 성공적으로 완료되었습니다. 이제 이 견고한 기반 위에 TASK-13 Presentation Layer MVP Refactor를 시작하고 싶습니다.

현재 상태를 확인하고 TASK-13 작업을 시작해주세요. MVP 패턴 도입을 통해 UI 로직과 비즈니스 로직을 분리하여 테스트 가능성과 유지보수성을 향상시키는 것이 목표입니다."**

---

이 프롬프트로 다음 세션에서 원활하게 TASK-13을 시작할 수 있을 것입니다! 🎯
