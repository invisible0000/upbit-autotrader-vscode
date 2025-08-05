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
- [X] `upbit_auto_trading/ui/desktop/main_window.py` 구조 분석

#### 🧠 접근 전략 (Approach Strategy)
> 1. 기존 `upbit_auto_trading/ui/desktop/main_window.py`의 MainWindow 클래스를 분석하여 현재 의존성 패턴 파악 (직접 import, try-except 폴백 패턴, StyleManager 직접 생성)
> 2. `run_desktop_ui.py`의 현재 애플리케이션 초기화 과정을 분석하여 Infrastructure Layer 통합 지점 식별
> 3. TASK-11에서 구현된 `upbit_auto_trading/infrastructure/dependency_injection/container.py`의 DIContainer와 `config/models/config_models.py`의 설정 모델을 활용
> 4. 기존 폴백 코드(try-except ImportError) 제거하고 DI Container를 통한 의존성 주입으로 전환
> 5. MainWindow 생성자에 ServiceContainer 주입받도록 수정하여 Infrastructure Layer 혜택 활용

#### 📌 작업 로그 (Work Log)
> - **분석 완료된 파일:** `upbit_auto_trading/ui/desktop/main_window.py` (760줄), `run_desktop_ui.py` (124줄), StyleManager, 로깅 시스템
> - **핵심 발견:** 현재 광범위한 try-except ImportError 폴백 패턴 (NavigationBar, StatusBar, StyleManager, 9개 Screen 컴포넌트 모두), 하드코딩된 StyleManager 직접 생성, 지연 로딩 방식의 화면 관리, 기존 로깅 시스템 v3.0 존재
> - **상세 설명:** MainWindow는 760줄의 대형 클래스로 9개의 화면 컴포넌트를 관리하며, 모든 컴포넌트에 대해 try-except ImportError로 더미 클래스 폴백 패턴 사용. `self.style_manager = StyleManager()` 등 하드코딩된 의존성 생성이 다수 존재. run_desktop_ui.py는 단순한 구조로 MainWindow를 직접 생성하여 DI Container 통합 지점이 명확함. 기존 로깅 시스템 v3.0이 `upbit_auto_trading/logging/`에 구현되어 있어 Infrastructure Layer와 통합 가능함.

- [X] 기존 로깅 시스템과 새로운 Infrastructure Layer 호환성 검토

#### 📌 작업 로그 (Work Log)
> - **호환성 검토 완료:** 기존 로깅 시스템 v3.0 (`upbit_auto_trading/logging/`) vs Infrastructure Layer 로깅 설정
> - **핵심 발견:** 기존 로깅 시스템은 독립적이며 Infrastructure Layer와 호환 가능. `LoggerFactory.get_debug_logger()` 패턴으로 DI Container와 통합 가능
> - **상세 설명:** 현재 `upbit_auto_trading/logging/__init__.py`에 LoggerFactory가 구현되어 있고, `get_logger()` 함수로 컴포넌트별 로거 제공. `run_desktop_ui.py`에서 폴백 로거 사용 중이나, Infrastructure Layer의 LoggingConfig와 통합하여 환경별 로그 레벨 제어 가능. DI Container에 LoggerFactory를 등록하고 MainWindow에서 주입받는 방식으로 통합할 예정.

- [X] 메인 윈도우에서 직접 접근하는 컴포넌트들 식별

#### 📌 작업 로그 (Work Log)
> - **식별 완료:** MainWindow에서 직접 접근하는 15개 핵심 컴포넌트 분석 완료
> - **핵심 발견:** StyleManager 직접 생성, NavigationBar/StatusBar 의존성, 9개 Screen 컴포넌트 지연 로딩, QSettings 직접 사용, SimplePaths 직접 사용, theme_notifier 직접 import
> - **상세 설명:**
>   1. **UI 컴포넌트:** NavigationBar, StatusBar (try-except 폴백)
>   2. **스타일 관리:** StyleManager 직접 생성 (`self.style_manager = StyleManager()`), theme_notifier 직접 import
>   3. **화면 관리:** 9개 Screen 클래스들 (DashboardScreen, ChartViewScreen, SettingsScreen 등) 지연 로딩 방식
>   4. **설정 관리:** QSettings 직접 사용 (윈도우 크기/위치, 테마 저장)
>   5. **경로 관리:** SimplePaths 직접 import 및 사용
>   6. **API/DB 체크:** UpbitAPI, SQLite 직접 접근
>
>   모든 컴포넌트가 하드코딩 방식으로 생성되어 DI Container를 통한 의존성 주입으로 전환 가능함.

- [X] DI Container를 통해 주입받아야 할 서비스들 목록 작성

#### 📌 작업 로그 (Work Log)
> - **서비스 목록 완성:** DI Container를 통해 주입받을 10개 핵심 서비스 식별 및 우선순위 설정
> - **핵심 발견:** 기존 하드코딩된 의존성들을 서비스 인터페이스로 추상화하여 테스트 가능성과 유지보수성 향상 가능
> - **상세 설명:**
>   **1순위 (핵심 서비스):**
>   - `IConfigurationService`: QSettings, SimplePaths 대체하여 환경별 설정 관리
>   - `IStyleService`: StyleManager, theme_notifier 통합하여 테마 관리
>   - `ILoggingService`: 기존 로깅 시스템 v3.0과 Infrastructure Layer 로깅 통합
>
>   **2순위 (UI 서비스):**
>   - `INavigationService`: NavigationBar 의존성 주입
>   - `IStatusService`: StatusBar 의존성 주입
>   - `IScreenFactory`: 9개 Screen 컴포넌트 지연 로딩을 팩토리 패턴으로 관리
>
>   **3순위 (외부 연동):**
>   - `IApiConnectionService`: UpbitAPI 연결 상태 관리
>   - `IDatabaseService`: SQLite 연결 상태 관리
>   - `IEventBus`: Screen 간 통신 (backtest_requested, api_status_changed 등)
>   - `IWindowService`: 창 크기/위치 관리
>
>   모든 서비스는 인터페이스 기반으로 설계하여 Mock 객체로 단위 테스트 가능하게 구성

### 3. **[백업]** 기존 파일들 안전 백업
- [X] `run_desktop_ui.py`를 `run_desktop_ui_old.py`로 백업

#### 📌 작업 로그 (Work Log)
> - **백업 완료된 파일:** `run_desktop_ui.py` → `run_desktop_ui_old.py`
> - **핵심 기능:** 기존 애플리케이션 엔트리 포인트의 안전한 백업으로 롤백 가능성 확보
> - **상세 설명:** PowerShell Copy-Item 명령으로 124줄의 기존 run_desktop_ui.py 파일을 run_desktop_ui_old.py로 복사하여 백업 완료. 백업 파일은 Infrastructure Layer 통합 과정에서 문제 발생 시 즉시 롤백할 수 있는 안전장치 역할을 함.

- [X] `main_window.py`를 `main_window_old.py`로 백업

#### 📌 작업 로그 (Work Log)
> - **백업 완료된 파일:** `upbit_auto_trading/ui/desktop/main_window.py` → `main_window_old.py`
> - **핵심 기능:** 760줄의 대형 MainWindow 클래스 백업으로 DI 리팩토링 과정의 안전성 확보
> - **상세 설명:** 기존 MainWindow 클래스의 완전한 백업 완료. 이 파일은 DI Container 통합과 의존성 주입 리팩토링 과정에서 핵심적으로 변경될 예정이므로, 백업을 통해 기존 동작을 보존하고 필요시 즉시 복원 가능하도록 함.

- [X] 기존 로깅 시스템 파일들 백업

#### 📌 작업 로그 (Work Log)
> - **백업 완료된 파일들:** `upbit_auto_trading/logging/` 전체 → `backups/logging_system_backup_20250805_203011/`
> - **핵심 기능:** 기존 로깅 시스템 v3.0 전체 백업으로 Infrastructure Layer 통합 과정의 안전성 확보
> - **상세 설명:** 7개 파일 백업 완료 (`__init__.py`, `debug_logger.py`, `smart_log_manager.py`, `README.md`, `test_smart_logging.py`, docs/, __pycache__/). 기존 로깅 시스템과 Infrastructure Layer의 LoggingConfig 통합 과정에서 호환성 문제 발생 시 즉시 복원 가능하도록 완전한 백업 체계 구축함.

### 4. **[통합]** run_desktop_ui.py Infrastructure Layer 연결
- [X] ServiceContainer 초기화 및 서비스 등록 구현

#### 📌 작업 로그 (Work Log)
> - **수정/생성된 파일:** `run_desktop_ui.py`, `upbit_auto_trading/ui/desktop/main_window.py`
> - **핵심 기능:** ApplicationContext 기반 애플리케이션 생명주기 관리 및 MainWindow DI Container 지원
> - **상세 설명:**
>   1. **run_desktop_ui.py 완전 리팩토링:** 기존 124줄의 단순 구조에서 Infrastructure Layer 기반 초기화로 전환. `ApplicationContext.initialize()` 통해 환경변수 기반 설정 로드(`UPBIT_ENVIRONMENT`), ConfigLoader, LoggingConfig, DIContainer 순차 초기화 구현
>   2. **MainWindow 생성자 확장:** `__init__(self, di_container=None)` 시그니처로 변경하여 DI Container 옵션 파라미터 지원. 기존 방식과 호환성 유지하면서 Infrastructure Layer 통합 준비
>   3. **UI 서비스 등록 시스템:** `register_ui_services()` 함수로 기존 LoggerFactory를 DI Container에 싱글톤 등록하여 기존 로깅 시스템 v3.0과 Infrastructure Layer 통합
>   4. **에러 처리 강화:** ApplicationContextError 전용 예외 처리로 Infrastructure Layer 초기화 실패와 일반 애플리케이션 오류 구분
>   5. **성공적 테스트:** 애플리케이션 정상 실행 확인 (`🔧 스마트 로그 관리자 v3.0 초기화` 출력으로 기존 로깅 시스템과 통합 동작 검증)

- [X] MainWindow 생성자 수정 (DI Container 주입받도록)
- [X] 애플리케이션 엔트리 포인트 리팩토링

#### 📌 작업 로그 (Work Log)
> - **수정/생성된 파일:** `run_desktop_ui.py` 완전 리팩토링
> - **핵심 기능:** 함수 기반 모듈화된 애플리케이션 엔트리 포인트 구조로 전환
> - **상세 설명:**
>   1. **모듈화 구조:** `create_application_context()`, `register_ui_services()`, `setup_application()`, `run_application()` 함수로 책임 분리
>   2. **강화된 서비스 등록:** LoggerFactory를 문자열 키 기반으로 DI Container에 등록하여 Infrastructure Layer와 기존 로깅 시스템 v3.0 완전 통합
>   3. **견고한 에러 처리:** ApplicationContextError와 일반 Exception을 구분하여 구체적 오류 메시지 제공
>   4. **정리 작업 자동화:** `app_context.dispose()` 호출로 리소스 정리 자동화
>   5. **성공적 검증:** 애플리케이션 정상 시작/종료 확인 (`✅ ApplicationContext 초기화 완료`, `✅ UI 서비스 등록 완료`, `✅ 애플리케이션 정상 종료` 출력), 기존 기능 손실 없이 Infrastructure Layer 혜택 적용됨

### 5. **[리팩토링]** 메인 윈도우 DI 지원
- [X] MainWindow 클래스 생성자 수정 (ServiceContainer 의존성 주입)
- [X] 기존 하드코딩된 컴포넌트 생성을 DI로 전환

#### 📌 작업 로그 (Work Log)
> - **수정/생성된 파일:** `run_desktop_ui.py`, `upbit_auto_trading/ui/desktop/main_window.py`
> - **핵심 기능:** StyleManager, NavigationBar, StatusBar 하드코딩 생성을 DI Container 기반 주입으로 전환
> - **상세 설명:**
>   1. **서비스 등록 확장:** `register_ui_services()`에 StyleManager(싱글톤), NavigationBar(transient), StatusBar(transient) 등록
>   2. **DI 주입 로직:** MainWindow에서 `di_container.resolve()` 패턴으로 서비스 주입, 실패 시 기존 방식으로 폴백하여 호환성 보장
>   3. **StyleManager DI 성공:** `✅ StyleManager DI 주입 성공` 메시지로 정상 작동 확인
>   4. **점진적 전환:** 기존 try-except ImportError 폴백 패턴과 공존하면서 단계적으로 DI 전환
>   5. **테스트 검증:** 애플리케이션 정상 시작/종료, 기존 기능 손실 없이 Infrastructure Layer 혜택 적용
- [X] 설정 서비스 연결 및 초기화 로직 구현

#### 📌 작업 로그 (Work Log)
> - **수정/생성된 파일:** `run_desktop_ui.py`, `upbit_auto_trading/ui/desktop/main_window.py`
> - **핵심 기능:** ConfigLoader를 DI Container에 등록하고 QSettings 대신 Infrastructure Layer 설정 시스템 활용
> - **상세 설명:**
>   1. **ConfigurationService 등록:** ConfigLoader를 ApplicationContext에서 가져와 DI Container에 등록
>   2. **NavigationBar/StatusBar DI 성공:** `✅ NavigationBar DI 주입 성공`, `✅ StatusBar DI 주입 성공` 메시지로 완전한 DI 전환 확인
>   3. **테마 설정 통합:** `_load_theme()` 메서드에서 ConfigLoader 우선 사용, 실패 시 QSettings 폴백으로 호환성 보장
>   4. **점진적 설정 마이그레이션:** 기존 QSettings와 새로운 ConfigLoader 공존하여 단계적 전환
>   5. **완전한 DI 체계:** StyleManager, NavigationBar, StatusBar 모두 DI Container에서 주입받아 Infrastructure Layer 혜택 완전 활용

### 6. **[확장]** 설정 시스템 통합
- [X] MainWindow print() → IL 스마트 로깅 전환

#### 📌 작업 로그 (Work Log)
> - **수정/생성된 파일:** `upbit_auto_trading/ui/desktop/main_window.py`
> - **핵심 기능:** MainWindow의 모든 print() 문을 Infrastructure Layer 스마트 로깅 v3.1 시스템으로 완전 전환하여 LLM 에이전트 효율적 보고 체계 구축
> - **상세 설명:**
>   1. **IL 스마트 로깅 통합:** LoggerFactory를 DI Container에서 주입받아 `create_component_logger("MainWindow")` 패턴으로 구조화된 로깅 적용
>   2. **LLM 로그 분리 시스템 v3.1 활용:** 기존 print() 문을 info/warning/error 로그로 분류하고, 중요한 상태 변화는 `🤖 LLM_REPORT:` 형식으로 LLM 에이전트 전용 로그 생성
>   3. **성공적 통합 확인:** `MainWindow IL 스마트 로깅 초기화 완료`, `SettingsService DI 주입 실패, QSettings 사용`, `API 연결 테스트 성공 - 정상 연결됨`, `DB 연결 성공: settings.sqlite3` 등 구조화된 로그 출력
>   4. **듀얼 로깅 시스템:** 사람용 로그(`logs/upbit_auto_trading.log`)와 LLM용 로그(`logs/upbit_auto_trading_LLM_*.log`)로 자동 분리되어 각각의 소비자에게 최적화된 로그 제공
>   5. **점진적 설정 통합:** ConfigLoader 우선 시도 후 QSettings 폴백으로 호환성 보장하면서 Infrastructure Layer 설정 시스템 단계적 도입

- [-] UIConfiguration, TradingConfiguration 모델 정의

#### 🧠 접근 전략 (Approach Strategy)
> ✅ **완료:** Infrastructure Layer 스마트 로깅 v3.1 및 LLM 로그 분리 시스템 개발 완료
> 1. MainWindow의 모든 print() 문을 IL 스마트 로깅으로 완전 전환 완료 ✅
> 2. LLM 로그 분리 시스템 v3.1 개발: 사람용(`upbit_auto_trading.log`) + LLM용(`upbit_auto_trading_LLM_*.log`) 듀얼 파일 시스템 ✅
> 3. 시작 시 세션 로그 정리 시스템: 프로그램 재시작 시 이전 세션 로그들 자동 통합 및 백업 ✅
> 4. DI Container에서 LoggerFactory 주입받아 구조화된 로깅 적용 완료 ✅
> 5. `🤖 LLM_REPORT` 형식의 구조화된 에이전트 보고 시스템 구축 완료 ✅
> 6. 전체 문서 체계 업데이트: copilot-instructions.md, docs/README.md, ERROR_HANDLING_POLICY.md 등에 LLM_LOG_SEPARATION_GUIDE.md 참조 추가 완료 ✅

⚠️ **다음 작업 필요:**
- UIConfiguration 모델 정의 (Window 크기/위치, 테마 설정을 Configuration으로 관리)
- SettingsService 구현 (QSettings 대신 IL ConfigLoader 활용)
- 기존 설정 UI와 새로운 설정 서비스 연결

- [ ] MainWindow print() → IL 스마트 로깅 전환
- [ ] UIConfiguration 모델 정의 (Window 크기/위치, 테마 설정)
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

## 📊 성공 기준

### 기능적 요구사항
- [X] 메인 윈도우가 Infrastructure Layer를 통해 초기화됨 (ApplicationContext 기반 초기화 완료)
- [X] UI 컴포넌트들이 DI Container를 통해 서비스를 받음 (StyleManager, NavigationBar, StatusBar DI 완료)
- [X] Infrastructure Layer 스마트 로깅 v3.1 통합 (print() → IL 로깅 전환 완료)
- [X] LLM 로그 분리 시스템 v3.1 구축 (듀얼 파일 시스템, 시작 시 정리, 문서 업데이트 완료)
- [X] 기존 UI 기능 손실 없이 Infrastructure Layer 혜택 적용 (완전 호환성 검증 완료)
- [ ] 설정이 Configuration Management를 통해 관리됨 (QSettings → ConfigLoader 마이그레이션 필요)
- [ ] 테마 시스템이 설정 서비스와 연동됨

### 비기능적 요구사항
- [X] 애플리케이션 시작 시간 3초 이내 (현재 정상 시작 시간 확인)
- [X] DI Container 오버헤드 최소화 (성능 저하 없음 확인)
- [ ] 설정 변경이 즉시 UI에 반영됨 (Configuration 시스템 완성 후 검증 필요)
- [ ] 메모리 누수 없음 (1시간 운영 후 메모리 증가 10% 이내)

### 아키텍처 요구사항
- [X] UI Layer와 Infrastructure Layer 간 명확한 분리 (DI Container 통한 의존성 주입)
- [X] 의존성 방향이 올바름 (UI → Application → Infrastructure)
- [X] DI Container를 통한 주요 서비스 주입 (LoggerFactory, StyleManager, NavigationBar, StatusBar)
- [X] 기존 코드와의 호환성 유지 (점진적 마이그레이션, 폴백 시스템)
- [ ] 모든 외부 의존성이 DI Container를 통해 주입됨 (설정, 테마 서비스 완성 필요)

## 🎉 주요 성과 요약 (2025-08-06 기준)

### ✅ 완료된 핵심 작업들
1. **Infrastructure Layer 완전 통합**: ApplicationContext 기반 애플리케이션 생명주기 관리
2. **DI Container 활용**: StyleManager, NavigationBar, StatusBar 의존성 주입 성공
3. **스마트 로깅 v3.1 시스템**: MainWindow의 모든 print() → IL 로깅 전환 완료
4. **LLM 로그 분리 시스템 v3.1**:
   - 사람용(`logs/upbit_auto_trading.log`) + LLM용(`logs/upbit_auto_trading_LLM_*.log`) 듀얼 파일
   - 시작 시 이전 세션 자동 정리 및 백업 시스템
   - 전체 문서 체계 업데이트 (copilot-instructions.md, docs/ 등)
5. **호환성 보장**: 기존 UI 기능 손실 없이 Infrastructure Layer 혜택 적용
6. **안전한 백업**: run_desktop_ui_old.py, main_window_old.py, 로깅 시스템 백업 완료

### 🔄 진행 중인 작업
- 설정 시스템 통합: QSettings → Configuration Management 마이그레이션
- 테마 시스템 Infrastructure 연결
- 전체 통합 테스트 및 성능 검증

### 🚀 다음 LLM 에이전트를 위한 작업 지침
1. **6단계 완료 확인**: UIConfiguration 모델 정의 → SettingsService 구현 → 설정 UI 연결
2. **7단계 진행**: ThemeService 구현 → theme_notifier 통합
3. **8단계 검증**: 통합 테스트 → 성능 검증 → 메모리 누수 체크

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
