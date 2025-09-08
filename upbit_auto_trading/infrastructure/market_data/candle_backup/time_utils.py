"""
TimeUtils v4.0 - 업비트 특화 시간 처리 유틸리티
캔들 시간 생성, 정렬 및 초 단위 변환 도구
업비트 공식 API 타임프레임 완전 지원: 초(1s), 분(1,3,5,10,15,30,60,240m), 일/주/월/연
"""

from datetime import datetime, timedelta
from typing import List


class TimeUtils:
    """업비트 특화 시간 처리 유틸리티 (v4.0 확장)"""

    # 업비트 공식 지원 분 단위 목록
    SUPPORTED_MINUTE_UNITS = [1, 3, 5, 10, 15, 30, 60, 240]

    @staticmethod
    def get_timeframe_seconds(timeframe: str) -> int:
        """
        타임프레임을 초 단위로 변환 (v4.0 신규 메서드)

        Args:
            timeframe: 타임프레임 (1s, 1m, 3m, 5m, 10m, 15m, 30m, 60m, 240m, 1d, 1w, 1M, 1y)

        Returns:
            초 단위 시간 간격

        Raises:
            ValueError: 지원하지 않는 타임프레임
        """
        normalized = timeframe.lower().strip()

        # 초 단위 (업비트는 1s만 지원)
        if normalized == '1s':
            return 1

        # 분 단위
        elif normalized.endswith('m'):
            minutes = int(normalized[:-1])
            return minutes * 60

        # 시간 단위 (하위 호환성)
        elif normalized.endswith('h'):
            hours = int(normalized[:-1])
            return hours * 3600

        # 일 단위
        elif normalized.endswith('d'):
            days = int(normalized[:-1])
            return days * 86400

        # 주 단위
        elif normalized.endswith('w'):
            weeks = int(normalized[:-1])
            return weeks * 604800

        # 월 단위 (30일로 근사)
        elif normalized.endswith('M'):
            months = int(normalized[:-1])
            return months * 2592000  # 30 * 24 * 60 * 60

        # 연 단위 (365일로 근사)
        elif normalized.endswith('y'):
            years = int(normalized[:-1])
            return years * 31536000  # 365 * 24 * 60 * 60

        else:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

    @staticmethod
    def get_timeframe_minutes(timeframe: str) -> int:
        """
        타임프레임을 분 단위로 변환 (호환성 메서드)

        Args:
            timeframe: 타임프레임

        Returns:
            분 단위 시간 간격 (초 단위는 1분으로 올림)

        Raises:
            ValueError: 지원하지 않는 타임프레임
        """
        seconds = TimeUtils.get_timeframe_seconds(timeframe)
        minutes = seconds // 60

        # 초 단위인 경우 최소 1분으로 처리
        return max(1, minutes)

    @staticmethod
    def get_timeframe_timedelta(timeframe: str) -> timedelta:
        """
        타임프레임을 timedelta로 변환

        Args:
            timeframe: 타임프레임

        Returns:
            timedelta 객체
        """
        seconds = TimeUtils.get_timeframe_seconds(timeframe)
        return timedelta(seconds=seconds)

    @staticmethod
    def is_upbit_supported_timeframe(timeframe: str) -> bool:
        """
        업비트에서 공식 지원하는 타임프레임인지 확인

        Args:
            timeframe: 검증할 타임프레임

        Returns:
            지원 여부
        """
        normalized = timeframe.lower().strip()

        # 초 캔들 (1s만 지원)
        if normalized == '1s':
            return True

        # 분 캔들 (공식 지원 단위)
        elif normalized.endswith('m'):
            try:
                minutes = int(normalized[:-1])
                return minutes in TimeUtils.SUPPORTED_MINUTE_UNITS
            except ValueError:
                return False

        # 일/주/월/연 캔들 (1단위만 지원)
        elif normalized in ['1d', '1w', '1M', '1y']:
            return True

        return False

    @staticmethod
    def generate_candle_times(start_time: datetime, end_time: datetime, timeframe: str) -> List[datetime]:
        """
        시작 시간부터 종료 시간까지 예상되는 캔들 시간 목록 생성

        Args:
            start_time: 시작 시간
            end_time: 종료 시간
            timeframe: 타임프레임

        Returns:
            예상 캔들 시간 목록
        """
        # 타임프레임을 timedelta로 변환
        delta = TimeUtils.get_timeframe_timedelta(timeframe)

        # 시작 시간을 캔들 시간 경계로 정렬
        aligned_start = TimeUtils._align_to_candle_boundary(start_time, timeframe)

        times = []
        current_time = aligned_start

        while current_time <= end_time:
            times.append(current_time)
            current_time += delta

        return times

    @staticmethod
    def _align_to_candle_boundary(dt: datetime, timeframe: str) -> datetime:
        """
        주어진 시간을 캔들 경계에 맞춰 정렬

        Args:
            dt: 정렬할 시간
            timeframe: 타임프레임

        Returns:
            정렬된 시간
        """
        normalized = timeframe.lower().strip()

        # 초 단위 (1초 경계)
        if normalized == '1s':
            return dt.replace(microsecond=0)

        # 분 단위
        elif normalized.endswith('m'):
            minutes = int(normalized[:-1])
            if minutes < 60:
                # 1시간 미만: 분 단위로 정렬
                aligned_minute = (dt.minute // minutes) * minutes
                return dt.replace(minute=aligned_minute, second=0, microsecond=0)
            else:
                # 60분 이상 (60m=1h, 240m=4h): 시간 단위로 정렬
                hours = minutes // 60
                aligned_hour = (dt.hour // hours) * hours
                return dt.replace(hour=aligned_hour, minute=0, second=0, microsecond=0)

        # 일 단위 이상: 자정으로 정렬
        else:
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def get_previous_candle_time(dt: datetime, timeframe: str) -> datetime:
        """이전 캔들 시간 계산"""
        delta = TimeUtils.get_timeframe_timedelta(timeframe)
        aligned = TimeUtils._align_to_candle_boundary(dt, timeframe)
        return aligned - delta

    @staticmethod
    def get_next_candle_time(dt: datetime, timeframe: str) -> datetime:
        """다음 캔들 시간 계산"""
        delta = TimeUtils.get_timeframe_timedelta(timeframe)
        aligned = TimeUtils._align_to_candle_boundary(dt, timeframe)
        return aligned + delta

    @staticmethod
    def is_candle_time_boundary(dt: datetime, timeframe: str) -> bool:
        """주어진 시간이 캔들 시간 경계인지 확인"""
        aligned = TimeUtils._align_to_candle_boundary(dt, timeframe)
        return dt == aligned

    @staticmethod
    def validate_time_consistency(time1: datetime, time2: datetime, timeframe: str) -> bool:
        """
        두 시간이 동일한 캔들 경계 정렬을 가지는지 검증 (v4.0 신규)

        Args:
            time1: 첫 번째 시간
            time2: 두 번째 시간
            timeframe: 타임프레임

        Returns:
            시간 일관성 여부
        """
        try:
            aligned1 = TimeUtils._align_to_candle_boundary(time1, timeframe)
            aligned2 = TimeUtils._align_to_candle_boundary(time2, timeframe)

            # 동일한 정렬 방식이 적용되었는지 확인
            return aligned1 == time1 and aligned2 == time2

        except Exception:
            return False

    @staticmethod
    def calculate_candle_count(start_time: datetime, end_time: datetime, timeframe: str) -> int:
        """
        시작 시간부터 종료 시간까지의 캔들 개수 계산 (v4.0 신규, v4.1 경계 정렬 개선)

        Args:
            start_time: 시작 시간
            end_time: 종료 시간
            timeframe: 타임프레임

        Returns:
            예상 캔들 개수
        """
        # v4.1 개선: 경계 정렬 후 정확한 계산
        aligned_start = TimeUtils._align_to_candle_boundary(start_time, timeframe)
        aligned_end = TimeUtils._align_to_candle_boundary(end_time, timeframe)

        timeframe_seconds = TimeUtils.get_timeframe_seconds(timeframe)
        time_diff = (aligned_end - aligned_start).total_seconds()
        return max(0, int(time_diff // timeframe_seconds) + 1)

    @staticmethod
    def normalize_timeframe(timeframe: str) -> str:
        """
        타임프레임을 표준 형식으로 정규화 (업비트 호환성)

        Args:
            timeframe: 원본 타임프레임

        Returns:
            정규화된 타임프레임

        Examples:
            "1h" -> "60m"
            "4h" -> "240m"
            "1M" -> "1M"
        """
        normalized = timeframe.lower().strip()

        # 시간 단위를 분 단위로 변환
        if normalized.endswith('h'):
            hours = int(normalized[:-1])
            return f"{hours * 60}m"

        # 대문자 M 보존 (월 단위)
        elif normalized.endswith('m') and timeframe.endswith('M'):
            return timeframe  # 원본 대문자 M 유지

        return normalized


# 하위 호환성을 위한 함수들
def generate_candle_times(start_time: datetime, end_time: datetime, timeframe: str) -> List[datetime]:
    """하위 호환성을 위한 래퍼 함수"""
    return TimeUtils.generate_candle_times(start_time, end_time, timeframe)


def get_previous_candle_time(dt: datetime, timeframe: str) -> datetime:
    """하위 호환성을 위한 래퍼 함수"""
    return TimeUtils.get_previous_candle_time(dt, timeframe)


def get_next_candle_time(dt: datetime, timeframe: str) -> datetime:
    """하위 호환성을 위한 래퍼 함수"""
    return TimeUtils.get_next_candle_time(dt, timeframe)


def is_candle_time_boundary(dt: datetime, timeframe: str) -> bool:
    """하위 호환성을 위한 래퍼 함수"""
    return TimeUtils.is_candle_time_boundary(dt, timeframe)
