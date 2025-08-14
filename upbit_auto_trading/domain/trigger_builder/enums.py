"""
트리거 빌더 도메인 Enums
- VariableCategory: 변수의 목적/용도 분류
- ChartCategory: 차트 표시 방식
- ComparisonGroup: 변수 간 비교 가능성 그룹
- ConditionOperator: 조건 연산자
- ConditionStatus: 조건 상태
"""
from enum import Enum


class VariableCategory(Enum):
    """변수의 목적/용도별 분류"""
    TREND = "trend"              # 추세 지표 (SMA, EMA 등)
    MOMENTUM = "momentum"        # 모멘텀 지표 (RSI, STOCHASTIC 등)
    VOLATILITY = "volatility"    # 변동성 지표 (ATR, BOLLINGER_BAND 등)
    VOLUME = "volume"           # 거래량 지표 (VOLUME, VOLUME_SMA 등)
    PRICE = "price"             # 가격 정보 (CURRENT_PRICE, OPEN_PRICE 등)
    CAPITAL = "capital"         # 자본/잔고 정보 (CASH_BALANCE, COIN_BALANCE 등)
    STATE = "state"             # 거래 상태 (PROFIT_PERCENT, POSITION_SIZE 등)
    DYNAMIC_MANAGEMENT = "dynamic_management"  # 동적 관리 (불타기, 물타기, 트레일링 스탑)


class ChartCategory(Enum):
    """차트 표시 방식"""
    OVERLAY = "overlay"         # 주 차트에 오버레이 (SMA, EMA, 볼린저밴드 등)
    SUBPLOT = "subplot"         # 별도 서브플롯 (RSI, MACD, 거래량 등)


class ComparisonGroup(Enum):
    """변수 간 비교 가능성 그룹 - 동일 그룹끼리만 직접 비교 가능"""
    PRICE_COMPARABLE = "price_comparable"           # 가격 기반 비교 (원화 단위)
    PERCENTAGE_COMPARABLE = "percentage_comparable"  # 백분율 비교 (0-100)
    ZERO_CENTERED = "zero_centered"                 # 0 중심 비교 (-100 ~ +100)
    VOLUME_COMPARABLE = "volume_comparable"         # 거래량 비교
    VOLATILITY_COMPARABLE = "volatility_comparable"  # 변동성 비교
    CAPITAL_COMPARABLE = "capital_comparable"       # 자본/잔고 비교
    QUANTITY_COMPARABLE = "quantity_comparable"     # 수량 비교
    SIGNAL_CONDITIONAL = "signal_conditional"       # 조건부 신호 (MACD 등)
    DYNAMIC_TARGET = "dynamic_target"               # 동적 목표값 (불타기/물타기 목표가)


class ConditionOperator(Enum):
    """조건 연산자"""
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="
    CROSSOVER = "crossover"      # 상향 돌파
    CROSSUNDER = "crossunder"    # 하향 돌파


class ConditionStatus(Enum):
    """조건 상태"""
    VALID = "valid"        # 유효
    INVALID = "invalid"    # 무효
    PENDING = "pending"    # 대기
    ERROR = "error"        # 오류


class CalculationMethod(Enum):
    """통합 파라미터 계산 방식 (UI 확장형)"""
    STATIC_VALUE = "static_value"                       # 정적 값 (고정값)
    PERCENTAGE_OF_EXTREME = "percentage_of_extreme"     # 극값% (최고/최저 기준)
    ENTRY_PRICE_PERCENT = "entry_price_percent"         # 진입가%p
    AVERAGE_PRICE_PERCENT = "average_price_percent"     # 평단가%p
    PERCENTAGE_OF_TRACKED = "percentage_of_tracked"     # 추적값% (기존 호환)
    STATIC_VALUE_OFFSET = "static_value_offset"         # 정적 오프셋 (기존 호환)


class BaseVariable(Enum):
    """기준값 타입"""
    ENTRY_PRICE = "entry_price"         # 최초 진입가
    AVERAGE_PRICE = "average_price"     # 현재 평단가
    CURRENT_PRICE = "current_price"     # 현재가
    HIGH_PRICE = "high_price"           # 고가
    LOW_PRICE = "low_price"             # 저가


class TrailDirection(Enum):
    """트레일링 방향 (확장형)"""
    UP = "up"                   # 상향 추적 (고점 추적)
    DOWN = "down"               # 하향 추적 (저점 추적)
    BIDIRECTIONAL = "bidirectional"  # 양방향 추적


class ResetTrigger(Enum):
    """초기화 트리거 조건"""
    NEVER = "never"                     # 초기화 안함
    POSITION_ENTRY = "position_entry"   # 포지션 진입시
    POSITION_EXIT = "position_exit"     # 포지션 청산시
    MANUAL_RESET = "manual_reset"       # 수동 초기화
    CONDITION_MET = "condition_met"     # 특정 조건 달성시
    DAILY_RESET = "daily_reset"         # 일일 초기화
    STRATEGY_RESTART = "strategy_restart"  # 전략 재시작시


class DetectionType(Enum):
    """변화 감지 방식"""
    ABSOLUTE_CHANGE = "절대값_변화"        # 절대값 변화
    PERCENT_CHANGE = "퍼센트_변화"         # 퍼센트 변화
    DIRECTION_CHANGE = "방향_변화"         # 방향 변화
    THRESHOLD_BREAK = "임계값_돌파"        # 임계값 돌파
    NEW_HIGH = "신고점_갱신"              # 신고점 갱신
    NEW_LOW = "신저점_갱신"               # 신저점 갱신


class BreakoutType(Enum):
    """돌파 유형"""
    UPWARD_BREAK = "상승_돌파"            # 상승 돌파
    DOWNWARD_BREAK = "하락_돌파"          # 하락 돌파
    BIDIRECTIONAL_BREAK = "양방향_돌파"    # 양방향 돌파
    RESISTANCE_BREAK = "저항선_돌파"       # 저항선 돌파
    SUPPORT_BREAK = "지지선_돌파"          # 지지선 돌파


class DetectionSensitivity(Enum):
    """감지 민감도"""
    LOW = "낮음"                         # 낮음
    MEDIUM = "중간"                      # 중간
    HIGH = "높음"                        # 높음
    VERY_HIGH = "매우_높음"              # 매우 높음
