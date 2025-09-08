# TimeFrame Infrastructure Provider - 시스템 전체 편의성 제공
from typing import Dict, Optional
from upbit_auto_trading.domain.value_objects.timeframe import TimeFrame
from upbit_auto_trading.application.services.timeframe_service import TimeFrameService


class TimeFrameProvider:
    """TimeFrame Infrastructure Provider - 시스템 전체 접근성 제공"""

    _instance: Optional['TimeFrameProvider'] = None

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._timeframe_cache: Dict[str, TimeFrame] = {}
            self._seconds_mapping: Dict[str, int] = {}
            self._initialize()
            self._initialized = True

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _initialize(self):
        """초기화 - 캐시 및 매핑 테이블 구축"""
        supported_timeframes = TimeFrameService.get_supported_timeframes()
        for tf in supported_timeframes:
            self._timeframe_cache[tf.value] = tf
            self._seconds_mapping[tf.value] = tf.seconds

    def get_timeframe(self, value: str) -> TimeFrame:
        """캐시된 TimeFrame 객체 반환"""
        if value not in self._timeframe_cache:
            timeframe = TimeFrame(value)
            self._timeframe_cache[value] = timeframe
            self._seconds_mapping[value] = timeframe.seconds
        return self._timeframe_cache[value]

    def get_seconds(self, timeframe_value: str) -> int:
        """timeframe 값에 대한 초 단위 변환"""
        if timeframe_value not in self._seconds_mapping:
            self.get_timeframe(timeframe_value)
        return self._seconds_mapping[timeframe_value]

    def get_all_seconds_mapping(self) -> Dict[str, int]:
        """전체 timeframe -> seconds 매핑 반환"""
        return self._seconds_mapping.copy()

    @classmethod
    def reset_cache(cls):
        """캐시 초기화 (테스트용)"""
        cls._instance = None


# 편의 함수들 (Infrastructure 계층에서 간편 사용)
def get_timeframe(value: str) -> TimeFrame:
    """전역 TimeFrame 인스턴스 반환"""
    provider = TimeFrameProvider()
    return provider.get_timeframe(value)


def get_timeframe_seconds(value: str) -> int:
    """timeframe 값에 대한 초 단위 변환"""
    provider = TimeFrameProvider()
    return provider.get_seconds(value)


def get_timeframe_seconds_mapping() -> Dict[str, int]:
    """전체 timeframe -> seconds 매핑"""
    provider = TimeFrameProvider()
    return provider.get_all_seconds_mapping()
