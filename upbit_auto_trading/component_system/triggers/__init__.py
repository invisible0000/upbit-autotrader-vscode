"""
트리거 컴포넌트 패키지 초기화
Trigger Components Package Initialization

모든 트리거 컴포넌트들을 쉽게 가져올 수 있도록 하는 초기화 모듈
"""

# 가격 기반 트리거들
from .price_triggers import (
    PriceChangeTrigger, PriceChangeConfig,
    PriceBreakoutTrigger, PriceBreakoutConfig,
    PriceCrossoverTrigger, PriceCrossoverConfig
)

# 지표 기반 트리거들
from .indicator_triggers import (
    RSITrigger, RSITriggerConfig,
    MACDTrigger, MACDTriggerConfig,
    BollingerBandTrigger, BollingerBandTriggerConfig,
    MovingAverageCrossTrigger, MovingAverageCrossConfig
)

# 시간 기반 트리거들
from .time_triggers import (
    PeriodicTrigger, PeriodicTriggerConfig,
    ScheduledTrigger, ScheduledTriggerConfig,
    DelayTrigger, DelayTriggerConfig
)

# 거래량 기반 트리거들
from .volume_triggers import (
    VolumeSurgeTrigger, VolumeSurgeConfig,
    VolumeDropTrigger, VolumeDropConfig,
    RelativeVolumeTrigger, RelativeVolumeConfig,
    VolumeBreakoutTrigger, VolumeBreakoutConfig
)

# 전체 트리거 클래스 목록
TRIGGER_CLASSES = {
    # 가격 기반
    'price_change': PriceChangeTrigger,
    'price_breakout': PriceBreakoutTrigger,
    'price_crossover': PriceCrossoverTrigger,
    
    # 지표 기반
    'rsi': RSITrigger,
    'macd': MACDTrigger,
    'bollinger_bands': BollingerBandTrigger,
    'moving_average_cross': MovingAverageCrossTrigger,
    
    # 시간 기반
    'periodic': PeriodicTrigger,
    'scheduled': ScheduledTrigger,
    'delay': DelayTrigger,
    
    # 거래량 기반
    'volume_surge': VolumeSurgeTrigger,
    'volume_drop': VolumeDropTrigger,
    'relative_volume': RelativeVolumeTrigger,
    'volume_breakout': VolumeBreakoutTrigger,
}

# 설정 클래스 목록
CONFIG_CLASSES = {
    # 가격 기반
    'price_change': PriceChangeConfig,
    'price_breakout': PriceBreakoutConfig,
    'price_crossover': PriceCrossoverConfig,
    
    # 지표 기반
    'rsi': RSITriggerConfig,
    'macd': MACDTriggerConfig,
    'bollinger_bands': BollingerBandTriggerConfig,
    'moving_average_cross': MovingAverageCrossConfig,
    
    # 시간 기간
    'periodic': PeriodicTriggerConfig,
    'scheduled': ScheduledTriggerConfig,
    'delay': DelayTriggerConfig,
    
    # 거래량 기반
    'volume_surge': VolumeSurgeConfig,
    'volume_drop': VolumeDropConfig,
    'relative_volume': RelativeVolumeConfig,
    'volume_breakout': VolumeBreakoutConfig,
}

# 카테고리별 트리거 그룹
TRIGGER_CATEGORIES = {
    'price': ['price_change', 'price_breakout', 'price_crossover'],
    'indicator': ['rsi', 'macd', 'bollinger_bands', 'moving_average_cross'],
    'time': ['periodic', 'scheduled', 'delay'],
    'volume': ['volume_surge', 'volume_drop', 'relative_volume', 'volume_breakout'],
}

# 트리거 메타데이터
TRIGGER_METADATA = {
    'price_change': {
        'display_name': '가격 변동 트리거',
        'category': 'price',
        'description': '가격이 지정된 비율만큼 변동했을 때 실행',
        'difficulty': 'beginner'
    },
    'price_breakout': {
        'display_name': '가격 돌파 트리거',
        'category': 'price',
        'description': '지정된 가격 범위를 돌파했을 때 실행',
        'difficulty': 'intermediate'
    },
    'price_crossover': {
        'display_name': '가격 교차 트리거',
        'category': 'price',
        'description': '가격이 특정 기준선을 교차했을 때 실행',
        'difficulty': 'intermediate'
    },
    'rsi': {
        'display_name': 'RSI 트리거',
        'category': 'indicator',
        'description': 'RSI 지표가 과매수/과매도 구간에 진입했을 때 실행',
        'difficulty': 'intermediate'
    },
    'macd': {
        'display_name': 'MACD 트리거',
        'category': 'indicator',
        'description': 'MACD 시그널이 발생했을 때 실행',
        'difficulty': 'advanced'
    },
    'bollinger_bands': {
        'display_name': '볼린저 밴드 트리거',
        'category': 'indicator',
        'description': '볼린저 밴드 경계를 터치했을 때 실행',
        'difficulty': 'intermediate'
    },
    'moving_average_cross': {
        'display_name': '이동평균 교차 트리거',
        'category': 'indicator',
        'description': '이동평균선이 교차했을 때 실행',
        'difficulty': 'beginner'
    },
    'periodic': {
        'display_name': '주기적 트리거',
        'category': 'time',
        'description': '지정된 시간 간격으로 실행',
        'difficulty': 'beginner'
    },
    'scheduled': {
        'display_name': '예약 트리거',
        'category': 'time',
        'description': '특정 시간에 실행',
        'difficulty': 'beginner'
    },
    'delay': {
        'display_name': '지연 트리거',
        'category': 'time',
        'description': '지정된 시간 후 실행',
        'difficulty': 'beginner'
    },
    'volume_surge': {
        'display_name': '거래량 급증 트리거',
        'category': 'volume',
        'description': '거래량이 평균 대비 급증했을 때 실행',
        'difficulty': 'intermediate'
    },
    'volume_drop': {
        'display_name': '거래량 감소 트리거',
        'category': 'volume',
        'description': '거래량이 급격히 감소했을 때 실행',
        'difficulty': 'intermediate'
    },
    'relative_volume': {
        'display_name': '상대적 거래량 트리거',
        'category': 'volume',
        'description': '과거 대비 상대적으로 높은 거래량일 때 실행',
        'difficulty': 'advanced'
    },
    'volume_breakout': {
        'display_name': '거래량 돌파 트리거',
        'category': 'volume',
        'description': '특정 거래량 임계값을 돌파했을 때 실행',
        'difficulty': 'intermediate'
    },
}

def get_trigger_class(trigger_type: str):
    """트리거 타입으로 클래스 가져오기"""
    return TRIGGER_CLASSES.get(trigger_type)


def get_config_class(trigger_type: str):
    """트리거 타입으로 설정 클래스 가져오기"""
    return CONFIG_CLASSES.get(trigger_type)


def get_triggers_by_category(category: str):
    """카테고리별 트리거 목록 가져오기"""
    return TRIGGER_CATEGORIES.get(category, [])


def get_trigger_metadata(trigger_type: str):
    """트리거 메타데이터 가져오기"""
    return TRIGGER_METADATA.get(trigger_type, {})

__all__ = [
    # 클래스들
    'PriceChangeTrigger', 'PriceChangeConfig',
    'PriceBreakoutTrigger', 'PriceBreakoutConfig',
    'PriceCrossoverTrigger', 'PriceCrossoverConfig',
    'RSITrigger', 'RSITriggerConfig',
    'MACDTrigger', 'MACDTriggerConfig',
    'BollingerBandTrigger', 'BollingerBandTriggerConfig',
    'MovingAverageCrossTrigger', 'MovingAverageCrossConfig',
    'PeriodicTrigger', 'PeriodicTriggerConfig',
    'ScheduledTrigger', 'ScheduledTriggerConfig',
    'DelayTrigger', 'DelayTriggerConfig',
    'VolumeSurgeTrigger', 'VolumeSurgeConfig',
    'VolumeDropTrigger', 'VolumeDropConfig',
    'RelativeVolumeTrigger', 'RelativeVolumeConfig',
    'VolumeBreakoutTrigger', 'VolumeBreakoutConfig',
    
    # 딕셔너리들과 함수들
    'TRIGGER_CLASSES', 'CONFIG_CLASSES', 'TRIGGER_CATEGORIES', 'TRIGGER_METADATA',
    'get_trigger_class', 'get_config_class', 'get_triggers_by_category', 'get_trigger_metadata'
]
