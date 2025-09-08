# TimeFrame Application Service - DDD 시스템 전체 timeframe 관리
from typing import Dict, List
from upbit_auto_trading.domain.value_objects.timeframe import TimeFrame, TimeFrameType


class TimeFrameService:
    """TimeFrame 관련 Application Service - DDD 계층 간 timeframe 처리 중재"""

    @staticmethod
    def create_timeframe(value: str) -> TimeFrame:
        """안전한 TimeFrame 생성"""
        return TimeFrame(value)

    @staticmethod
    def get_supported_timeframes() -> List[TimeFrame]:
        """지원되는 모든 timeframe 목록"""
        supported = ['1s', '1m', '3m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M']
        return [TimeFrame(tf) for tf in supported]

    @staticmethod
    def get_timeframes_by_type(timeframe_type: TimeFrameType) -> List[TimeFrame]:
        """타입별 timeframe 목록"""
        all_timeframes = TimeFrameService.get_supported_timeframes()
        return [tf for tf in all_timeframes if tf.type == timeframe_type]

    @staticmethod
    def find_higher_timeframes(base_timeframe: TimeFrame) -> List[TimeFrame]:
        """주어진 timeframe보다 높은 timeframe들"""
        all_timeframes = TimeFrameService.get_supported_timeframes()
        return [tf for tf in all_timeframes if tf.is_higher_than(base_timeframe)]

    @staticmethod
    def find_lower_timeframes(base_timeframe: TimeFrame) -> List[TimeFrame]:
        """주어진 timeframe보다 낮은 timeframe들"""
        all_timeframes = TimeFrameService.get_supported_timeframes()
        return [tf for tf in all_timeframes if base_timeframe.is_higher_than(tf)]

    @staticmethod
    def get_timeframe_seconds_mapping() -> Dict[str, int]:
        """전체 timeframe -> seconds 매핑 (Repository/Infrastructure 계층용)"""
        timeframes = TimeFrameService.get_supported_timeframes()
        return {tf.value: tf.seconds for tf in timeframes}

    @staticmethod
    def calculate_interval_count(timeframe: TimeFrame, duration_seconds: int) -> int:
        """지정된 기간에 포함되는 timeframe 개수 계산"""
        return duration_seconds // timeframe.seconds

    @staticmethod
    def validate_timeframe_string(value: str) -> bool:
        """timeframe 문자열 유효성 검증 (Domain 생성 전 체크)"""
        try:
            TimeFrame(value)
            return True
        except ValueError:
            return False
