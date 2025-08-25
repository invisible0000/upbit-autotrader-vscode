"""
시간 유틸리티 함수
캔들 시간 생성 및 관리 도구
"""

from datetime import datetime, timedelta
from typing import List, Optional


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
    timeframe_minutes = _parse_timeframe_to_minutes(timeframe)

    if timeframe_minutes is None:
        raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

    # 시작 시간을 캔들 시간 경계로 정렬
    aligned_start = _align_to_candle_boundary(start_time, timeframe_minutes)

    times = []
    current_time = aligned_start

    while current_time <= end_time:
        times.append(current_time)
        current_time += timedelta(minutes=timeframe_minutes)

    return times


def _parse_timeframe_to_minutes(timeframe: str) -> Optional[int]:
    """타임프레임 문자열을 분 단위로 변환"""
    timeframe = timeframe.lower().strip()

    if timeframe.endswith('m'):
        return int(timeframe[:-1])
    elif timeframe.endswith('h'):
        return int(timeframe[:-1]) * 60
    elif timeframe.endswith('d'):
        return int(timeframe[:-1]) * 60 * 24
    elif timeframe.endswith('w'):
        return int(timeframe[:-1]) * 60 * 24 * 7
    elif timeframe.endswith('M'):  # 월 단위는 30일로 근사
        return int(timeframe[:-1]) * 60 * 24 * 30
    else:
        # 숫자만 있는 경우 분으로 간주
        try:
            return int(timeframe)
        except ValueError:
            return None


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


def get_previous_candle_time(dt: datetime, timeframe: str) -> datetime:
    """이전 캔들 시간 계산"""
    timeframe_minutes = _parse_timeframe_to_minutes(timeframe)
    if timeframe_minutes is None:
        raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

    aligned = _align_to_candle_boundary(dt, timeframe_minutes)
    return aligned - timedelta(minutes=timeframe_minutes)


def get_next_candle_time(dt: datetime, timeframe: str) -> datetime:
    """다음 캔들 시간 계산"""
    timeframe_minutes = _parse_timeframe_to_minutes(timeframe)
    if timeframe_minutes is None:
        raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

    aligned = _align_to_candle_boundary(dt, timeframe_minutes)
    return aligned + timedelta(minutes=timeframe_minutes)


def is_candle_time_boundary(dt: datetime, timeframe: str) -> bool:
    """주어진 시간이 캔들 시간 경계인지 확인"""
    timeframe_minutes = _parse_timeframe_to_minutes(timeframe)
    if timeframe_minutes is None:
        return False

    aligned = _align_to_candle_boundary(dt, timeframe_minutes)
    return dt == aligned
