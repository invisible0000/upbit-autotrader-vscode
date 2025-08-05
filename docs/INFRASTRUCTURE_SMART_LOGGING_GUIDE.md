# 🔍 Infrastructure Layer 스마트 로깅 시스템 v3.0

> **목적**: LLM 에이전트와 개발자를 위한 실시간 에러 감지 및 효율적 디버깅 지원
> **대상**: 모든 개발자, LLM 에이전트
> **우선순위**: 개발의 첫 단계 - 문제 즉시 인식 및 보고

## 🎯 핵심 목표

### 1. 실시간 문제 감지
- **즉시 인식**: 에러 발생과 동시에 LLM 에이전트가 인식
- **구조화된 보고**: 문제 해결에 필요한 모든 컨텍스트 제공
- **스마트 필터링**: 중요한 로그만 선별하여 노이즈 제거

### 2. 효율적 디버깅 지원
- **Context-aware**: 개발 상황에 맞는 로그 레벨 자동 조정
- **Feature Development**: 특정 기능 개발 시 집중 로깅
- **환경별 제어**: development, testing, production 환경 자동 감지

## 🏗️ 시스템 아키텍처

### Core Components
```
upbit_auto_trading/infrastructure/logging/
├── __init__.py                    # 통합 진입점
├── interfaces/
│   └── logging_interface.py       # ILoggingService 인터페이스
├── services/
│   └── smart_logging_service.py   # SmartLoggingService 구현
├── configuration/
│   └── logging_config.py          # 환경 기반 설정
└── README.md                      # 상세 사용법
```

### Integration Points
- **ApplicationContext**: DI Container 자동 등록
- **run_desktop_ui.py**: UI 애플리케이션 통합
- **Environment Variables**: 실시간 제어
- **LLM Agent**: 구조화된 에러 보고

## 🚀 기본 사용법

### 1. 기본 컴포넌트 로거
```python
# 권장 방식 - 컴포넌트별 로거
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("ComponentName")
logger.info("정보 메시지")
logger.debug("디버그 정보")  # 스마트 필터링으로 자동 제어
logger.error("에러 발생")    # LLM 에이전트 즉시 인식
```

### 2. Feature Development Context
```python
# 특정 기능 개발 시 집중 로깅
from upbit_auto_trading.infrastructure.logging import get_logging_service

service = get_logging_service()
with service.feature_development_context("StrategyBuilder"):
    logger = service.get_logger("StrategyComponent")
    logger.debug("상세 개발 로그만 출력")  # 해당 기능만 집중
```

### 3. LLM 에이전트 보고
```python
# 구조화된 에러 보고
logger = create_component_logger("ErrorHandler")

try:
    critical_operation()
except Exception as e:
    # LLM 에이전트 즉시 인식용 구조화된 로그
    logger.error(f"🤖 LLM_REPORT: Operation=critical_op, Error={type(e).__name__}, Message={str(e)}")
    logger.debug(f"📊 Context: {get_context_data()}")
    raise
```

## ⚙️ 환경변수 제어

### 실시간 로그 제어
```powershell
# 개발 시 상세 로깅
$env:UPBIT_LOG_CONTEXT='debugging'
$env:UPBIT_LOG_SCOPE='debug_all'
$env:UPBIT_CONSOLE_OUTPUT='true'

# 특정 컴포넌트만 집중
$env:UPBIT_COMPONENT_FOCUS='StrategyBuilder'

# 프로덕션에서는 최소 로깅
$env:UPBIT_LOG_CONTEXT='production'
$env:UPBIT_LOG_SCOPE='minimal'
```

### 환경변수 옵션

#### UPBIT_LOG_CONTEXT (로그 컨텍스트)
- `development`: 개발 환경 (기본값)
- `testing`: 테스트 환경
- `production`: 프로덕션 환경
- `debugging`: 디버깅 모드
- `silent`: 로깅 비활성화

#### UPBIT_LOG_SCOPE (로그 범위)
- `silent`: 로그 없음
- `minimal`: 에러만
- `normal`: 기본 로그 (기본값)
- `verbose`: 상세 로그
- `debug_all`: 모든 디버그 로그

#### UPBIT_COMPONENT_FOCUS (컴포넌트 집중)
- 특정 컴포넌트명 설정 시 해당 컴포넌트만 로깅
- 예: `StrategyBuilder`, `TriggerSystem`, `BacktestEngine`

#### UPBIT_CONSOLE_OUTPUT (콘솔 출력)
- `true`: 터미널에 실시간 로그 출력 (LLM 에이전트 즉시 인식)
- `false`: 파일에만 로그 저장 (기본값)

## 📁 로그 파일 구조

### Dual File System
- **메인 로그**: `upbit_auto_trading.log` (통합 로그)
- **세션 로그**: `upbit_auto_trading_YYYYMMDD_HHMMSS_PID{숫자}.log` (세션별)

### 자동 관리
- 세션 종료 시 세션 로그가 메인 로그로 자동 병합
- 오래된 세션 파일 자동 정리
- 로그 파일 크기 제한 및 로테이션

## 🤖 LLM 에이전트 통합

### 구조화된 에러 보고
```python
def report_error_to_llm(error_context):
    """LLM 에이전트에게 구조화된 에러 보고"""
    logger = create_component_logger("LLMReporter")

    # 구조화된 보고 형식
    logger.error("🤖 === LLM 에이전트 에러 보고 시작 ===")
    logger.error(f"📍 Component: {error_context.component}")
    logger.error(f"⚠️ Error Type: {error_context.error_type}")
    logger.error(f"📄 Error Message: {error_context.message}")
    logger.error(f"📊 Context Data: {error_context.context}")
    logger.error(f"🔍 Stack Trace: {error_context.stack_trace}")
    logger.error("🤖 === LLM 에이전트 에러 보고 완료 ===")
```

### 실시간 인식 패턴
- **에러 태그**: `🤖 LLM_REPORT:` 접두사로 즉시 인식
- **구조화된 데이터**: key=value 형식으로 파싱 가능
- **컨텍스트 정보**: 문제 해결에 필요한 모든 정보 포함

## 🔧 DI Container 통합

### ApplicationContext 자동 등록
```python
# ApplicationContext에서 자동으로 등록됨
from upbit_auto_trading.infrastructure.dependency_injection.app_context import ApplicationContext

app_context = ApplicationContext()
container = app_context.container

# ILoggingService 자동 해결
from upbit_auto_trading.infrastructure.logging.interfaces.logging_interface import ILoggingService
logging_service = container.resolve(ILoggingService)
```

### Clean Architecture 준수
- **Interface**: ILoggingService 추상화
- **Implementation**: SmartLoggingService 구현
- **Dependency Injection**: ApplicationContext 자동 등록
- **Environment Configuration**: 환경별 자동 설정

## 🧪 테스트 및 검증

### 기본 기능 테스트
```python
# 테스트 스크립트 실행
python test_infrastructure_logging.py
```

### UI 통합 테스트
```python
# UI 통합 테스트
python test_infrastructure_ui_integration.py
```

### 환경변수 테스트
```powershell
# 환경별 로깅 테스트
$env:UPBIT_LOG_CONTEXT='debugging'
python test_infrastructure_logging.py
```

## 📚 마이그레이션 가이드

### 기존 로깅 시스템에서 마이그레이션

#### Before (기존 방식)
```python
from upbit_auto_trading.logging import get_integrated_logger
logger = get_integrated_logger("Component")
```

#### After (Infrastructure Layer)
```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
logger = create_component_logger("Component")
```

### 호환성 지원
- ApplicationContext에서 기존 LoggerFactory도 등록됨
- 기존 코드는 점진적으로 마이그레이션 가능
- 두 시스템 모두 정상 동작

## ⚡ 성능 최적화

### 스마트 필터링
- Context와 Scope에 따른 자동 로그 레벨 조정
- 불필요한 로그는 실행 시점에서 제거
- Feature Development 모드로 필요한 로그만 선별

### 메모리 효율성
- 세션별 로그 파일로 메모리 사용량 최소화
- 자동 로그 로테이션으로 디스크 공간 관리
- 비동기 로그 처리로 성능 영향 최소화

## 🚨 주의사항

### 환경변수 설정
- 개발 시에만 `UPBIT_CONSOLE_OUTPUT=true` 사용
- 프로덕션에서는 반드시 `UPBIT_LOG_CONTEXT=production` 설정
- 민감한 정보는 로그에 포함하지 않음

### LLM 에이전트 보고
- 구조화된 형식을 반드시 준수
- 에러 컨텍스트에 문제 해결 정보 포함
- 스택 트레이스와 실행 환경 정보 제공

## 📖 관련 문서

- [ERROR_HANDLING_POLICY.md](../docs/ERROR_HANDLING_POLICY.md): 에러 처리 정책
- [DEV_CHECKLIST.md](../docs/DEV_CHECKLIST.md): 개발 검증 체크리스트
- [ApplicationContext](../upbit_auto_trading/infrastructure/dependency_injection/app_context.py): DI 통합
- [copilot-instructions.md](../.vscode/copilot-instructions.md): LLM 에이전트 지침

---

**🎯 핵심**: Infrastructure Layer 스마트 로깅 시스템은 개발의 첫 단계입니다. 문제를 즉시 인식하고 LLM 에이전트에게 효율적으로 보고하여 빠른 문제 해결을 지원합니다.

**🤖 LLM 에이전트**: 이 시스템을 통해 실시간으로 문제를 감지하고 구조화된 정보를 바탕으로 효율적인 디버깅을 지원할 수 있습니다.
