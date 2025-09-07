"""
TimeUtils v4.0 - 통일된 시간 처리 유틸리티
캔들 시간 생성, 정렬 및 초 단위 변환 도구
업비트 특화 CandleDataProvider 시스템의 핵심 시간 처리 모듈
"""

from datetime import datetime, timedelta
from typing import List, Optional


class TimeUtils:
    """통일된 시간 처리 유틸리티 (v4.0 확장)"""

    @staticmethod
    def generate_candle_times(start_time: datetime, end_time: datetime, timeframe: str) -> List[datetime]:
        """
        시작 시간부터 종료 시간까지 예상되는 캔들 시간 목록 생성

        Args:
            start_time: 시작 시간
            end_time: 종료 시간
            timeframe: 타임프레임 (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)

        Returns:
            예상 캔들 시간 목록
        """
        # 타임프레임을 분 단위로 변환
        timeframe_minutes = TimeUtils._parse_timeframe_to_minutes(timeframe)

        if timeframe_minutes is None:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

        # 시작 시간을 캔들 시간 경계로 정렬
        aligned_start = TimeUtils._align_to_candle_boundary(start_time, timeframe_minutes)

        times = []
        current_time = aligned_start

        while current_time <= end_time:
            times.append(current_time)
            current_time += timedelta(minutes=timeframe_minutes)

        return times

    @staticmethod
    def get_timeframe_seconds(timeframe: str) -> int:
        """
        타임프레임을 초 단위로 변환 (v4.0 신규 메서드)

        Args:
            timeframe: 타임프레임 (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)

        Returns:
            초 단위 시간 간격

        Raises:
            ValueError: 지원하지 않는 타임프레임
        """
        timeframe_minutes = TimeUtils._parse_timeframe_to_minutes(timeframe)

        if timeframe_minutes is None:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

        return timeframe_minutes * 60

    @staticmethod
    def get_timeframe_minutes(timeframe: str) -> int:
        """
        타임프레임을 분 단위로 변환 (호환성 메서드)

        Args:
            timeframe: 타임프레임 (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)

        Returns:
            분 단위 시간 간격

        Raises:
            ValueError: 지원하지 않는 타임프레임
        """
        timeframe_minutes = TimeUtils._parse_timeframe_to_minutes(timeframe)

        if timeframe_minutes is None:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

        return timeframe_minutes

    @staticmethod
    def _parse_timeframe_to_minutes(timeframe: str) -> Optional[float]:
        """업비트 공식 타임프레임을 분 단위로 변환"""
        timeframe = timeframe.lower().strip()

        # 초 단위 (업비트는 1초만 지원)
        if timeframe == '1s':
            return 1 / 60  # 분 단위로 변환하면 0.0167분

        # 분 단위 (업비트 지원: 1, 3, 5, 10, 15, 30, 60, 240)
        elif timeframe.endswith('m'):
            minutes = int(timeframe[:-1])
            # 업비트 공식 지원 분 단위 검증
            if minutes in [1, 3, 5, 10, 15, 30, 60, 240]:
                return minutes
            else:
                # 기존 호환성을 위해 허용하되 경고 로그 필요
                return minutes

        # 시간 단위 (하위 호환성)
        elif timeframe.endswith('h'):
            hours = int(timeframe[:-1])
            return hours * 60

        # 일 단위
        elif timeframe.endswith('d'):
            days = int(timeframe[:-1])
            return days * 60 * 24

        # 주 단위
        elif timeframe.endswith('w'):
            weeks = int(timeframe[:-1])
            return weeks * 60 * 24 * 7

        # 월 단위 (30일로 근사)
        elif timeframe.endswith('M'):
            months = int(timeframe[:-1])
            return months * 60 * 24 * 30

        # 연 단위 (365일로 근사)
        elif timeframe.endswith('y'):
            years = int(timeframe[:-1])
            return years * 60 * 24 * 365

        else:
            # 숫자만 있는 경우 분으로 간주 (하위 호환성)
            try:
                return int(timeframe)
            except ValueError:
                return None

    @staticmethod
    def _align_to_candle_boundary(dt: datetime, timeframe_minutes: int) -> datetime:
        """
        주어진 시간을 캔들 경계에 맞춰 정렬

        Args:
            dt: 정렬할 시간
            timeframe_minutes: 타임프레임 (분 단위)

        Returns:
            정렬된 시간
        """
        if timeframe_minutes < 60:
            # 1시간 미만: 분 단위로 정렬
            aligned_minute = (dt.minute // timeframe_minutes) * timeframe_minutes
            return dt.replace(minute=aligned_minute, second=0, microsecond=0)

        elif timeframe_minutes < 1440:  # 24시간 미만
            # 시간 단위로 정렬
            hours = timeframe_minutes // 60
            aligned_hour = (dt.hour // hours) * hours
            return dt.replace(hour=aligned_hour, minute=0, second=0, microsecond=0)

        else:
            # 일 단위 이상: 자정으로 정렬
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def get_previous_candle_time(dt: datetime, timeframe: str) -> datetime:
        """이전 캔들 시간 계산"""
        timeframe_minutes = TimeUtils._parse_timeframe_to_minutes(timeframe)
        if timeframe_minutes is None:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

        aligned = TimeUtils._align_to_candle_boundary(dt, timeframe_minutes)
        return aligned - timedelta(minutes=timeframe_minutes)

    @staticmethod
    def get_next_candle_time(dt: datetime, timeframe: str) -> datetime:
        """다음 캔들 시간 계산"""
        timeframe_minutes = TimeUtils._parse_timeframe_to_minutes(timeframe)
        if timeframe_minutes is None:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

        aligned = TimeUtils._align_to_candle_boundary(dt, timeframe_minutes)
        return aligned + timedelta(minutes=timeframe_minutes)

    @staticmethod
    def is_candle_time_boundary(dt: datetime, timeframe: str) -> bool:
        """주어진 시간이 캔들 시간 경계인지 확인"""
        timeframe_minutes = TimeUtils._parse_timeframe_to_minutes(timeframe)
        if timeframe_minutes is None:
            return False

        aligned = TimeUtils._align_to_candle_boundary(dt, timeframe_minutes)
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
            timeframe_minutes = TimeUtils._parse_timeframe_to_minutes(timeframe)
            if timeframe_minutes is None:
                return False

            aligned1 = TimeUtils._align_to_candle_boundary(time1, timeframe_minutes)
            aligned2 = TimeUtils._align_to_candle_boundary(time2, timeframe_minutes)

            # 동일한 정렬 방식이 적용되었는지 확인
            return aligned1 == time1 and aligned2 == time2

        except Exception:
            return False

    @staticmethod
    def calculate_candle_count(start_time: datetime, end_time: datetime, timeframe: str) -> int:
        """
        시작 시간부터 종료 시간까지의 캔들 개수 계산 (v4.0 신규)

        Args:
            start_time: 시작 시간
            end_time: 종료 시간
            timeframe: 타임프레임

        Returns:
            예상 캔들 개수
        """
        timeframe_seconds = TimeUtils.get_timeframe_seconds(timeframe)
        time_diff = (end_time - start_time).total_seconds()
        return max(0, int(time_diff // timeframe_seconds) + 1)


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
