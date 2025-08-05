# TASK-20250803-12

## Title
Presentation Layer - 메인 윈도우 Infrastructure Layer 통합

## Objective (목표)
TASK-11에서 구축한 Infrastructure Layer (Configuration Management & DI Container)를 메인 윈도우와 설정 시스템에 통합하여 전체 애플리케이션의 견고한 기반을 확립합니다. 기존 run_desktop_ui.py를 Infrastructure Layer와 연결하고, 메인 윈도우가 DI Container를 통해 서비스를 주입받도록 리팩토링합니다.

## Source of Truth (준거 문서)
- `tasks/completed/TASK-20250803-11_configuration_management_system.md` - 완료된 Infrastructure Layer
- `docs/LLM_AGENT_TASK_GUIDELINES.md` - LLM 에이전트 TASK 작업 가이드
- `docs/COMPONENT_ARCHITECTURE.md` - DDD 기반 시스템 아키텍처

## Pre-requisites (선행 조건)
- `TASK-20250803-11`: Configuration Management System 완료 (19개 테스트 통과)
- Infrastructure Layer 구현 완료 (DI Container, Service Registry)
- 프로젝트 루트 정리 완료 (legacy 폴더로 이동)

## Detailed Steps (상세 실행 절차)

### 1. **[정리]** 프로젝트 루트 환경 정리
- [X] 루트에 분산된 테스트/디버그 스크립트 정리

#### 📌 작업 로그 (Work Log)
> - **정리 완료된 파일들:** 40개 이상의 test_*, debug_*, fix_*, proposed_*, verify_* 스크립트를 `legacy/test_scripts_archive_20250805`로 이동
> - **핵심 기능:** 프로젝트 루트 환경을 깔끔하게 정리하여 TASK 작업에 방해되지 않는 환경 구축
> - **상세 설명:** 중복된 UI 화면 파일들(`backtesting_screen.py`, `portfolio_screen.py`, `realtime_trade_screen.py`, `settings_login_screen.py`)을 `legacy/ui_legacy_screens_20250805`로 이동하고, 루트에 생성된 다양한 테스트/디버그 스크립트들을 체계적으로 아카이브하여 메인 개발 환경을 정리함. 정식 단위 테스트(`tests/` 폴더)와 필수 실행 스크립트(`run_desktop_ui.py`, `setup.py`, `run_config_tests.py`)는 유지하여 기능 손실 없이 환경 최적화 완료

- [X] 중복 UI 화면 파일들 legacy 이동 완료

### 2. **[분석]** 현재 메인 윈도우 구조 분석
- [ ] `upbit_auto_trading/ui/desktop/main_window.py` 구조 분석
- [ ] 기존 로깅 시스템과 새로운 Infrastructure Layer 호환성 검토
- [ ] 메인 윈도우에서 직접 접근하는 컴포넌트들 식별
- [ ] DI Container를 통해 주입받아야 할 서비스들 목록 작성

### 3. **[백업]** 기존 파일들 안전 백업
- [ ] `run_desktop_ui.py`를 `run_desktop_ui_old.py`로 백업
- [ ] `main_window.py`를 `main_window_old.py`로 백업
- [ ] 기존 로깅 시스템 파일들 백업

### 4. **[통합]** run_desktop_ui.py Infrastructure Layer 연결
- [ ] ServiceContainer 초기화 및 서비스 등록 구현
- [ ] MainWindow 생성자 수정 (DI Container 주입받도록)
- [ ] 애플리케이션 엔트리 포인트 리팩토링

### 5. **[리팩토링]** 메인 윈도우 DI 지원
- [ ] MainWindow 클래스 생성자 수정 (ServiceContainer 의존성 주입)
- [ ] 기존 하드코딩된 컴포넌트 생성을 DI로 전환
- [ ] 설정 서비스 연결 및 초기화 로직 구현

### 6. **[확장]** 설정 시스템 통합
- [ ] UIConfiguration, TradingConfiguration 모델 정의
- [ ] SettingsService 구현 (Configuration Management 활용)
- [ ] 기존 설정 UI와 새로운 설정 서비스 연결

### 7. **[연결]** 테마 시스템 Infrastructure 통합
- [ ] ThemeService 구현 (Configuration 기반)
- [ ] 기존 theme_notifier와 새로운 ThemeService 연결
- [ ] 설정 기반 테마 초기화 및 이벤트 전파

### 8. **[테스트]** 통합 테스트 및 검증
- [ ] 애플리케이션 시작 테스트 (3초 이내)
- [ ] DI Container 서비스 주입 테스트
- [ ] 설정 변경 즉시 반영 테스트
- [ ] 메모리 누수 검증 (1시간 운영):
## 📊 성공 기준

### 기능적 요구사항
- [ ] 메인 윈도우가 Infrastructure Layer를 통해 초기화됨
- [ ] 설정이 Configuration Management를 통해 관리됨
- [ ] UI 컴포넌트들이 DI Container를 통해 서비스를 받음
- [ ] 테마 시스템이 설정 서비스와 연동됨
- [ ] 기존 UI 기능 손실 없이 Infrastructure Layer 혜택 적용

### 비기능적 요구사항
- [ ] 애플리케이션 시작 시간 3초 이내
- [ ] 설정 변경이 즉시 UI에 반영됨
- [ ] 메모리 누수 없음 (1시간 운영 후 메모리 증가 10% 이내)
- [ ] DI Container 오버헤드 최소화

### 아키텍처 요구사항
- [ ] UI Layer와 Infrastructure Layer 간 명확한 분리
- [ ] 의존성 방향이 올바름 (UI → Application → Infrastructure)
- [ ] 모든 외부 의존성이 DI Container를 통해 주입됨
- [ ] 기존 코드와의 호환성 유지 (단계적 마이그레이션)

## 🔗 다음 작업과의 연결

### TASK-13 (Presentation Layer MVP Refactor)
- 이 작업에서 구축한 기반 위에 MVP 패턴 적용
- 서비스 계층을 활용한 Presenter 구현

### TASK-14 (View Refactoring Passive View)
- Passive View 패턴으로 UI 컴포넌트 리팩토링
- 이벤트 시스템을 활용한 뷰 업데이트

## 🚨 주의사항

### 호환성 유지
- 기존 UI 컴포넌트들의 기능 유지
- 사용자 설정 데이터 손실 방지
- 점진적 마이그레이션으로 위험 최소화
- `_old.py` 백업 파일로 롤백 가능성 확보

### 성능 고려
- DI Container 오버헤드 최소화
- 필요한 서비스만 지연 로딩
- UI 응답성 유지
- 로깅 시스템 성능 영향 최소화

## 📚 참고 문서

- [Configuration Management Implementation](../completed/TASK-20250803-11_configuration_management_system.md)
- [DDD 아키텍처 가이드](../../docs/COMPONENT_ARCHITECTURE.md)
- [UI 디자인 시스템](../../docs/UI_DESIGN_SYSTEM.md)
- [LLM 에이전트 작업 가이드](../../docs/LLM_AGENT_TASK_GUIDELINES.md)

---

**💡 핵심**: "Infrastructure Layer를 메인 윈도우에 연결하여 전체 애플리케이션의 견고한 기반을 구축한다!"

**🎯 목표**: "기존 기능 손실 없이 Infrastructure Layer의 혜택을 받는 안정적이고 확장 가능한 메인 윈도우 구현!"
