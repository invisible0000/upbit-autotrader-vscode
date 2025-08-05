# 🚀 스마트 로깅 시스템 v3.0

**UPBIT 자동매매 통합 로깅 시스템** - 컨텍스트 인식 + 스마트 필터링 + 듀얼 파일 로깅

## 📋 개요

스마트 로깅 시스템 v3.0은 **로그 범람 방지**와 **개발 상황별 최적화**를 위한 통합 로깅 솔루션입니다.

### 🎯 핵심 기능

- **🧠 스마트 필터링**: 개발 상황에 맞는 자동 로그 제어
- **📁 듀얼 파일 로깅**: 메인 로그 + 세션별 로그 관리
- **🎮 컨텍스트 인식**: 개발/테스트/프로덕션 자동 전환
- **⚡ 성능 최적화**: 조건부 컴파일 + 캐시 시스템
- **🔧 환경변수 제어**: 원클릭 로그 설정 변경

## 🏗️ 시스템 구조

```
upbit_auto_trading/logging/
├── __init__.py              # 통합 진입점
├── debug_logger.py          # 스마트 디버그 로거 (v3.0)
├── smart_log_manager.py     # 스마트 로그 매니저
├── test_smart_logging.py    # 테스트 스위트
└── README.md               # 이 문서
```

### 📊 로그 파일 구조

```
logs/
├── upbit_auto_trading.log                          # 메인 로그 (모든 세션 통합, 50MB 제한)
├── upbit_auto_trading_20250803_103650_PID72884.log # 현재 세션만 (프로그램 실행 중)
└── upbit_auto_trading_backup_20250806_120000.log   # 백업 로그 (50MB 초과 시 자동 생성)
```

💡 **중요**:
- 이전 세션 로그들은 프로그램 시작 시 메인 로그로 자동 통합되므로 PID 파일은 현재 실행 중인 세션만 존재합니다.
- 메인 로그가 50MB를 초과하면 자동으로 백업되고 새 로그가 시작됩니다.
- 30일 이상 된 백업 파일은 자동으로 삭제됩니다.

## 🚀 빠른 시작

### 1. 기본 사용법

```python
# 통합 로거 사용 (권장)
from upbit_auto_trading.logging import get_integrated_logger

logger = get_integrated_logger("MyComponent")
logger.info("일반 정보")
logger.success("작업 성공")
logger.error("에러 발생")
logger.debug("디버그 정보")  # 환경에 따라 자동 필터링
logger.performance("성능 정보")
```

### 2. 스마트 필터링 사용

```python
from upbit_auto_trading.logging import get_smart_log_manager

manager = get_smart_log_manager()

# 특정 기능 개발 중
with manager.feature_development("RSI_Strategy"):
    logger = get_integrated_logger("RSI_Strategy")
    logger.debug("RSI 계산 로직")  # ✅ 출력됨

    other_logger = get_integrated_logger("UI_Component")
    other_logger.debug("UI 업데이트")  # ❌ 필터링됨

# 특정 컴포넌트만 디버깅
with manager.debug_session(["TradingEngine", "OrderManager"]):
    trade_logger = get_integrated_logger("TradingEngine")
    trade_logger.debug("주문 처리")  # ✅ 출력됨
```

### 3. 환경변수 제어

```bash
# PowerShell에서 설정
$env:UPBIT_LOG_CONTEXT='development'  # development, testing, production, debugging
$env:UPBIT_LOG_SCOPE='verbose'        # silent, minimal, normal, verbose, debug_all
$env:UPBIT_COMPONENT_FOCUS='RSI_Strategy,TradingEngine'  # 특정 컴포넌트만

# 실행
python your_script.py
```

## �️ 로그 파일 관리 정책

### 📏 크기 제한 및 로테이션
- **메인 로그 제한**: 50MB
- **로테이션 동작**: 50MB 초과 시 `upbit_auto_trading_backup_YYYYMMDD_HHMMSS.log`로 백업 후 새 메인 로그 시작
- **백업 정리**: 30일 이상 된 백업 파일 자동 삭제

### 🔄 세션 파일 정리
- **파일 명명**: `upbit_auto_trading_YYYYMMDD_HHMMSS_PID숫자.log`
- **자동 병합**: 프로그램 시작 시 이전 세션들을 메인 로그로 통합
- **자동 삭제**: 병합 완료 후 이전 세션 파일들 자동 삭제
- **현재 세션만**: 실행 중인 PID 파일만 logs 폴더에 유지

### 💾 백업 전략
```
logs/
├── upbit_auto_trading.log                     # 현재 메인 로그 (최대 50MB)
├── upbit_auto_trading_20250806_120000_PID123.log  # 현재 세션 로그
├── upbit_auto_trading_backup_20250801_080000.log  # 백업 로그 (30일 보관)
└── upbit_auto_trading_backup_20250805_140000.log  # 백업 로그 (30일 보관)
```

## �📖 상세 가이드

### 🎯 로그 컨텍스트 (상황별 분류)

| 컨텍스트 | 설명 | 로그 범위 |
|---------|------|----------|
| `DEVELOPMENT` | 개발 중 | 상세한 로그 |
| `TESTING` | 테스트 중 | 핵심 로그만 |
| `DEBUGGING` | 디버깅 중 | 모든 디버그 로그 |
| `PRODUCTION` | 프로덕션 | ERROR, CRITICAL만 |
| `PERFORMANCE` | 성능 측정 | 최소한의 로그 |
| `EMERGENCY` | 긴급 상황 | 모든 로그 활성화 |

### 🔍 로그 스코프 (출력 범위)

| 스코프 | 포함 레벨 | 필터링 조건 |
|--------|----------|------------|
| `SILENT` | ERROR, CRITICAL | 최소한만 |
| `MINIMAL` | INFO, WARNING, ERROR, CRITICAL | 핵심 키워드만 |
| `NORMAL` | INFO, WARNING, ERROR, CRITICAL | 일반적 |
| `VERBOSE` | DEBUG, INFO, WARNING, ERROR, CRITICAL | 상세함 |
| `DEBUG_ALL` | 모든 레벨 | 제한 없음 |

### 🎮 컨텍스트 매니저 활용

```python
# 기능 개발 모드
with manager.feature_development("NewFeature", LogScope.VERBOSE):
    # NewFeature 관련 로그만 상세히 출력
    pass

# 테스트 모드
with manager.testing_mode("API_Test"):
    # 핵심 로그만 출력
    pass

# 성능 측정 모드
with manager.performance_mode():
    # 로그 최소화로 성능 영향 방지
    pass

# 긴급 모드
with manager.emergency_mode():
    # 모든 로그 활성화
    pass
```

### 🔧 데코레이터 활용

```python
from upbit_auto_trading.logging import log_scope, debug_components, LogScope

@log_scope(LogScope.VERBOSE)
def develop_new_strategy():
    logger = get_integrated_logger("StrategyDeveloper")
    logger.debug("상세 개발 로그")  # ✅ 출력됨

@debug_components("TradingEngine", "OrderManager")
def debug_trading_issue():
    logger = get_integrated_logger("TradingEngine")
    logger.debug("거래 문제 디버깅")  # ✅ 출력됨
```

## 🔧 환경변수 레퍼런스

### 주요 환경변수

```bash
# 로그 컨텍스트 설정
UPBIT_LOG_CONTEXT=development|testing|debugging|production|performance|emergency

# 로그 스코프 설정
UPBIT_LOG_SCOPE=silent|minimal|normal|verbose|debug_all

# 컴포넌트 포커스 (쉼표로 구분)
UPBIT_COMPONENT_FOCUS=Component1,Component2,Component3

# 기능 포커스
UPBIT_FEATURE_FOCUS=MyFeature

# 기존 환경별 설정 (v2.x 호환)
UPBIT_ENV=development|production
UPBIT_BUILD_TYPE=debug|production
UPBIT_DEBUG_MODE=true|false

# 콘솔 출력 제어 (실시간 터미널 출력)
UPBIT_CONSOLE_OUTPUT=true|false  # true: 터미널에 실시간 출력, false: 파일만
```

### 환경별 추천 설정

```bash
# 개발 환경
$env:UPBIT_LOG_CONTEXT='development'
$env:UPBIT_LOG_SCOPE='verbose'

# 테스트 환경
$env:UPBIT_LOG_CONTEXT='testing'
$env:UPBIT_LOG_SCOPE='minimal'

# 프로덕션 환경
$env:UPBIT_LOG_CONTEXT='production'
$env:UPBIT_LOG_SCOPE='silent'

# 디버깅 환경
$env:UPBIT_LOG_CONTEXT='debugging'
$env:UPBIT_LOG_SCOPE='debug_all'
$env:UPBIT_COMPONENT_FOCUS='ProblemComponent1,ProblemComponent2'

# 실시간 터미널 출력 활성화
$env:UPBIT_CONSOLE_OUTPUT='true'  # 에러 로그를 즉시 터미널에서 확인
```

## 🧪 테스트 및 검증

### 기본 테스트 실행

```bash
# 테스트 스위트 실행
python upbit_auto_trading/logging/test_smart_logging.py
```

### 수동 테스트

```python
# 시스템 상태 확인
from upbit_auto_trading.logging import get_logging_status
status = get_logging_status()
print(status)

# 빠른 설정 테스트
from upbit_auto_trading.logging import quick_setup
quick_setup(context="debugging", scope="debug_all", components=["TestComponent"])
```

## 📊 성능 및 최적화

### 성능 특징

- **캐시 시스템**: 동일한 필터링 조건 재사용
- **조건부 로깅**: 불필요한 로그 처리 완전 스킵
- **스마트 필터링**: 메시지 내용 기반 지능형 필터링

### 메모리 사용량

- **기본 모드**: ~1MB (기존 v2.x와 동일)
- **스마트 모드**: ~1.5MB (캐시 포함)
- **캐시 크기**: 평균 100-500개 항목

## 🔄 마이그레이션 가이드

### v2.x에서 v3.0으로

```python
# 기존 코드 (v2.x) - 계속 작동
from upbit_auto_trading.utils.debug_logger import get_logger
logger = get_logger("Component")

# 새 코드 (v3.0) - 권장
from upbit_auto_trading.logging import get_integrated_logger
logger = get_integrated_logger("Component")

# 기존 API 완전 호환
from upbit_auto_trading.logging import debug_logger, get_logger  # v2.x와 동일
```

### import 경로 변경

```python
# 기존
from upbit_auto_trading.utils.debug_logger import *

# 새로운 방식
from upbit_auto_trading.logging import *
```

## ⚠️ 문제 해결

### 자주 발생하는 문제

1. **스마트 매니저 로드 실패**
   ```python
   # 확인 방법
   from upbit_auto_trading.logging import get_logging_status
   print(get_logging_status())
   ```

2. **로그가 너무 많이 출력됨**
   ```bash
   # 스코프 변경
   $env:UPBIT_LOG_SCOPE='minimal'
   ```

3. **특정 컴포넌트 로그만 보고 싶음**
   ```bash
   # 컴포넌트 포커스 설정
   $env:UPBIT_COMPONENT_FOCUS='MyComponent'
   ```

4. **로그가 전혀 출력되지 않음**
   ```bash
   # 긴급 모드로 전환
   $env:UPBIT_LOG_CONTEXT='emergency'
   ```

5. **터미널에 실시간 로그가 안 보임 (에러 발견이 어려움)**
   ```bash
   # 콘솔 출력 활성화
   $env:UPBIT_CONSOLE_OUTPUT='true'
   ```

### 디버깅 명령어

```bash
# 메인 로그 확인 (모든 세션 통합) (PowerShell)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Get-Content logs/upbit_auto_trading.log -Encoding UTF8 | Select-Object -Last 20

# 현재 세션 로그 확인 (실시간 로그) (PowerShell)
Get-ChildItem logs\upbit_auto_trading_*PID*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Encoding UTF8 | Select-Object -Last 20

# 환경변수 확인
Get-ChildItem Env:UPBIT_*
```

## 🎯 LLM 에이전트를 위한 핵심 정보

### 즉시 사용 가능한 패턴

```python
# 1. 기본 로거 생성
logger = get_integrated_logger("ComponentName")

# 2. 컨텍스트별 로깅
with manager.feature_development("FeatureName"):
    logger.debug("개발 중 상세 로그")

# 3. 환경변수 기반 제어
os.environ['UPBIT_LOG_SCOPE'] = 'minimal'  # 로그 줄이기
os.environ['UPBIT_COMPONENT_FOCUS'] = 'MyComponent'  # 포커스 설정
```

### 권장 컴포넌트명

- `MainApp`: 메인 애플리케이션
- `TradingEngine`: 거래 엔진
- `StrategyManager`: 전략 관리
- `DatabaseManager`: 데이터베이스
- `APIManager`: API 통신
- `UIComponent`: UI 관련

### 성능 고려사항

- 프로덕션에서는 `UPBIT_LOG_CONTEXT=production` 설정 필수
- 대량 로깅 시 `performance_mode()` 사용
- 디버깅 완료 후 환경변수 초기화

## 📚 추가 자료

- **상위 문서**: `upbit_auto_trading/utils/DEBUG_LOGGER_USAGE_GUIDE_v2.2.md`
- **아키텍처 가이드**: `docs/LOGGING_ARCHITECTURE.md` (예정)
- **성능 분석**: `docs/LOGGING_PERFORMANCE.md` (예정)

---

**스마트 로깅 시스템 v3.0** - 개발 효율성과 시스템 안정성을 모두 잡는 차세대 로깅 솔루션! 🚀
