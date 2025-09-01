# 🏗️ 업비트 자동매매 시스템 아키텍처 가이드

## 🎯 시스템 개요

**설계 철학**: DDD(Domain-Driven Design) 기반의 확장 가능한 매매 시스템
**핵심 목표**: 기본 7규칙 전략의 완벽한 구현과 확장성

### 🚀 핵심 원칙
- **도메인 중심**: 매매 로직이 시스템의 핵심
- **계층 분리**: Presentation → Application → Domain ← Infrastructure
- **의존성 역전**: 상위 계층이 하위 계층에 의존하지 않음
- **테스트 가능**: 모든 컴포넌트가 독립적으로 테스트 가능

## 📊 4계층 DDD 아키텍처

### 1. Presentation Layer (PyQt6 UI)
```
upbit_auto_trading/ui/desktop/
├── main_window.py              # 메인 애플리케이션
├── presenters/                 # MVP 패턴 프레젠터
│   ├── strategy_presenter.py   # 전략 관리
│   ├── trigger_presenter.py    # 트리거 빌더
│   └── backtest_presenter.py   # 백테스팅
├── views/                      # Passive View 구현
│   ├── strategy_view.py        # 전략 관리 뷰
│   ├── trigger_view.py         # 트리거 빌더 뷰
│   └── backtest_view.py        # 백테스팅 뷰
└── common/                     # 공통 UI 컴포넌트
    ├── styles/                 # 통합 스타일 시스템
    ├── widgets/                # 재사용 위젯
    └── theme_notifier.py       # 테마 관리
```

### 2. Application Layer (Use Cases)
```
upbit_auto_trading/application/
├── services/                   # 비즈니스 서비스
│   ├── strategy_service.py     # 전략 관리 서비스
│   ├── trigger_service.py      # 트리거 관리 서비스
│   └── backtest_service.py     # 백테스팅 서비스
├── dto/                        # 데이터 전송 객체
│   ├── strategy_dto.py         # 전략 DTO
│   └── trigger_dto.py          # 트리거 DTO
└── use_cases/                  # 사용 사례
    ├── create_strategy.py      # 전략 생성
    └── run_backtest.py         # 백테스팅 실행
```

### 3. Domain Layer (핵심 비즈니스)
```
upbit_auto_trading/domain/
├── entities/                   # 도메인 엔티티
│   ├── strategy.py             # 전략 엔티티
│   ├── trigger.py              # 트리거 엔티티
│   └── position.py             # 포지션 엔티티
├── value_objects/              # 값 객체
│   ├── strategy_id.py          # 전략 식별자
│   └── trading_signal.py       # 거래 신호
├── services/                   # 도메인 서비스
│   ├── compatibility_checker.py # 호환성 검증
│   └── signal_evaluator.py     # 신호 평가
└── repositories/               # 저장소 인터페이스
    ├── strategy_repository.py  # 전략 저장소
    └── market_data_repository.py # 시장 데이터 저장소
```

### 4. Infrastructure Layer (외부 연동)
```
upbit_auto_trading/infrastructure/
├── logging/                    # 통합 로깅 시스템 ⭐
│   ├── services/
│   │   └── logging_service.py  # LoggingService 구현
│   └── config/
│       └── logging_config.py   # 로깅 설정 관리
├── repositories/               # 저장소 구현체
│   ├── sqlite_strategy_repository.py
│   └── sqlite_market_data_repository.py
├── external_apis/              # 외부 API
│   └── upbit_api_client.py     # 업비트 API
└── database/                   # 데이터베이스
    └── connection_manager.py   # DB 연결 관리
```

## 🎯 핵심 컴포넌트 설계

### 트리거 시스템 (핵심)
```python
class TriggerCondition:
    """개별 조건 (예: RSI > 30)"""
    def __init__(self, variable, operator, value):
        self.variable = variable      # 매매 변수
        self.operator = operator      # 비교 연산자
        self.value = value           # 대상값

class TriggerRule:
    """규칙 (조건들의 논리 조합)"""
    def __init__(self, conditions, logic='AND'):
        self.conditions = conditions
        self.logic = logic

class TriggerBuilder:
    """트리거 빌더 메인 컴포넌트"""
    def __init__(self):
        self.rules = []
        self.validator = CompatibilityValidator()

    def add_rule(self, rule: TriggerRule):
        if self.validator.validate(rule):
            self.rules.append(rule)
```

### 전략 시스템
```python
class BaseStrategy(ABC):
    """전략 기본 클래스"""
    @abstractmethod
    def generate_signal(self, data) -> TradingSignal:
        pass

class Basic7RuleStrategy(BaseStrategy):
    """기본 7규칙 전략 (검증 기준)"""
    def __init__(self):
        self.entry_rules = []      # 진입 규칙
        self.management_rules = [] # 관리 규칙
        self.exit_rules = []       # 탈출 규칙

    def add_rsi_oversold_entry(self):
        """RSI 과매도 진입"""
        pass

    def add_profit_averaging_up(self):
        """수익시 불타기"""
        pass
```

### UI 컴포넌트 설계
```python
class BaseWidget(QWidget):
    """모든 UI 위젯 기본 클래스"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.apply_theme()  # 통합 테마 시스템

class ConditionCard(BaseWidget):
    """조건 카드 위젯"""
    def __init__(self, condition):
        self.condition = condition
        super().__init__()

class RuleBuilder(BaseWidget):
    """규칙 빌더 위젯"""
    def add_condition(self):
        """호환성 검증 포함 조건 추가"""
        pass
```

## 🗄️ 3-DB 아키텍처

### 데이터베이스 분리 설계
- **settings.sqlite3**: 변수 정의, 파라미터 (data_info/*.yaml 기반)
- **strategies.sqlite3**: 사용자 전략, 백테스팅 결과
- **market_data.sqlite3**: 시장 데이터, 지표 캐시

### 주요 테이블 구조
```sql
-- settings.sqlite3
tv_trading_variables     -- 매매 변수 정의
tv_indicator_categories  -- 지표 카테고리
tv_comparison_groups     -- 호환성 그룹

-- strategies.sqlite3
user_strategies          -- 사용자 전략
strategy_rules          -- 전략 규칙
backtest_results        -- 백테스팅 결과

-- market_data.sqlite3
candle_data             -- 캔들 데이터 (1초~240분봉 지원)
calculated_indicators   -- 계산된 지표
```

## 📡 WebSocket v6 시스템

### 지원 데이터 타입
- **Public 데이터**: ticker, trade, orderbook
- **캔들 데이터**: candle.1s(1초봉), candle.1m(1분봉), candle.3m(3분봉), candle.5m(5분봉), candle.10m(10분봉), candle.15m(15분봉), candle.30m(30분봉), candle.60m(60분봉), candle.240m(240분봉)
- **Private 데이터**: myorder, myasset

### 주요 구성 요소
- **NativeWebSocketClient**: 저수준 WebSocket 연결 관리
- **SubscriptionStateManager**: 구독 상태 및 콜백 관리
- **JWTManager**: Private WebSocket 인증 토큰 관리
- **Models**: v5 호환성 레이어 및 메시지 변환

### 캔들 데이터 구독 예시
```python
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v6 import *

# 1초봉 구독
await client.subscribe(
    data_type=DataType.CANDLE_1S,
    symbols=["KRW-BTC", "KRW-ETH"],
    callback=candle_handler
)

# 5분봉 구독
await client.subscribe(
    data_type=DataType.CANDLE_5M,
    symbols=["KRW-BTC"],
    callback=candle_handler
)
```

## 🔄 데이터 흐름

### 1. 트리거 생성 흐름
```
사용자 입력 → UI 검증 → 호환성 체크 → 도메인 검증 → DB 저장
```

### 2. 매매 신호 생성 흐름
```
시장 데이터 → 지표 계산 → 조건 평가 → 전략 실행 → 매매 신호
```

### 3. 기본 7규칙 전략 흐름
```
RSI 과매도 감지 → 진입 → 수익시 불타기 → 트레일링 스탑 → 익절/손절
```

## 🛡️ 에러 처리 정책

### 계층별 에러 처리
```python
# Domain Layer: 비즈니스 규칙 위반
class DomainRuleViolationError(Exception):
    pass

# Application Layer: 사용 사례 실패
class UseCaseExecutionError(Exception):
    pass

# Infrastructure Layer: 외부 연동 실패
class ExternalServiceError(Exception):
    pass

# UI Layer: 사용자 입력 오류
class UserInputValidationError(Exception):
    pass
```

### 에러 전파 원칙
- **Domain 에러**: 절대 숨기지 않고 즉시 전파
- **Infrastructure 에러**: 재시도 후 적절한 도메인 에러로 변환
- **UI 에러**: 사용자 친화적 메시지로 표시

## 🔧 Infrastructure 로깅 시스템

### 스마트 로깅 기능
```python
from upbit_auto_trading.infrastructure.logging import create_component_logger

# 기본 사용법
logger = create_component_logger("TriggerBuilder")
logger.info("트리거 생성 시작")
logger.debug("상세 진행상황")  # 환경변수로 제어

# 환경변수 제어
$env:UPBIT_CONSOLE_OUTPUT='true'     # 콘솔 출력 활성화
$env:UPBIT_LOG_SCOPE='verbose'       # 상세 로그 레벨
$env:UPBIT_COMPONENT_FOCUS='TriggerBuilder'  # 특정 컴포넌트 집중
```

### 실시간 설정 변경
- **config/logging_config.yaml** 파일 수정 시 즉시 반영
- 재시작 없이 로그 레벨, 컴포넌트 포커스 변경 가능
- 개발 환경별 자동 설정 적용

## 🎨 UI 테마 시스템

### 전역 스타일 관리
```python
# 올바른 사용법
widget.setObjectName("primary_button")  # QSS에서 스타일 정의

# 금지사항
widget.setStyleSheet("color: blue;")     # 하드코딩 금지
```

### 테마 파일 구조
```
ui/desktop/common/styles/
├── style_manager.py      # 중앙 스타일 관리
├── default_style.qss     # 라이트 테마
├── dark_style.qss        # 다크 테마
└── component_styles.qss  # 컴포넌트별 확장
```

## ✅ 개발 검증 체크리스트

### 아키텍처 준수 확인
- [ ] DDD 계층 분리 준수
- [ ] 의존성 방향 올바름 (상위→하위)
- [ ] Domain Layer가 외부에 의존하지 않음
- [ ] Infrastructure 로깅 시스템 사용
- [ ] 통합 스타일 시스템 적용

### 기능 검증
- [ ] `python run_desktop_ui.py` 정상 실행
- [ ] 트리거 빌더에서 7규칙 구성 가능
- [ ] 호환성 검증 시스템 동작
- [ ] 실시간 로그 설정 변경 적용

## 📚 관련 문서

- **[기본 7규칙 전략 가이드](BASIC_7_RULE_STRATEGY_GUIDE.md)**: 시스템의 검증 기준
- **[트리거 빌더 가이드](TRIGGER_BUILDER_GUIDE.md)**: 트리거 시스템 상세
- **[DB 스키마](DB_SCHEMA.md)**: 데이터베이스 설계
- **[통합 설정 관리 가이드](UNIFIED_CONFIGURATION_MANAGEMENT_GUIDE.md)**: 설정 시스템

---

**🎯 성공 기준**: 기본 7규칙 전략이 트리거 빌더에서 완벽하게 구성되고 실행되는 시스템!

**💡 핵심 철학**: "각 컴포넌트가 독립적으로 테스트 가능하고 교체 가능한 구조"
