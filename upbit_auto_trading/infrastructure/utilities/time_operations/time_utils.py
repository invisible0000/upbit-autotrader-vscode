# 시간 연산 유틸리티 - Infrastructure Layer
from datetime import datetime, timedelta
from typing import List, Optional

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("TimeOperationsUtils")


def parse_timeframe_to_seconds(timeframe: str) -> Optional[int]:
    """타임프레임 문자열을 초 단위로 변환"""
    timeframe = timeframe.lower().strip()

    try:
        if timeframe.endswith('s'):
            return int(timeframe[:-1])
        elif timeframe.endswith('m'):
            return int(timeframe[:-1]) * 60
        elif timeframe.endswith('h'):
            return int(timeframe[:-1]) * 3600
        elif timeframe.endswith('d'):
            return int(timeframe[:-1]) * 86400
        elif timeframe.endswith('w'):
            return int(timeframe[:-1]) * 604800
        elif timeframe.upper().endswith('M'):  # 월 단위
            return int(timeframe[:-1]) * 2592000  # 30일 기준
        else:
            return None
    except ValueError:
        return None


def parse_timeframe_to_minutes(timeframe: str) -> Optional[int]:
    """타임프레임 문자열을 분 단위로 변환"""
    seconds = parse_timeframe_to_seconds(timeframe)
    return seconds // 60 if seconds else None


def align_to_timeframe_boundary(timestamp: datetime, timeframe: str) -> datetime:
    """타임스탬프를 timeframe 경계로 정렬"""
    minutes = parse_timeframe_to_minutes(timeframe)
    if not minutes:
        return timestamp

    # 분 단위로 정렬
    aligned_minute = (timestamp.minute // minutes) * minutes
    return timestamp.replace(minute=aligned_minute, second=0, microsecond=0)


def generate_timeframe_intervals(start_time: datetime, end_time: datetime, timeframe: str) -> List[datetime]:
    """시작 시간부터 종료 시간까지 timeframe 간격의 시간 목록 생성"""
    intervals = []

    minutes = parse_timeframe_to_minutes(timeframe)
    if not minutes:
        logger.error(f"지원하지 않는 timeframe: {timeframe}")
        return intervals

    # 시작 시간을 timeframe 경계로 정렬
    current_time = align_to_timeframe_boundary(start_time, timeframe)

    while current_time <= end_time:
        intervals.append(current_time)
        current_time += timedelta(minutes=minutes)

    return intervals


def calculate_missing_intervals(existing_times: List[datetime], start_time: datetime,
                                end_time: datetime, timeframe: str) -> List[datetime]:
    """누락된 시간 간격 계산"""
    expected_times = generate_timeframe_intervals(start_time, end_time, timeframe)
    existing_set = set(existing_times)

    missing_times = [t for t in expected_times if t not in existing_set]
    return sorted(missing_times)


def is_timestamp_aligned(timestamp: datetime, timeframe: str) -> bool:
    """타임스탬프가 timeframe 경계에 정렬되어 있는지 확인"""
    aligned = align_to_timeframe_boundary(timestamp, timeframe)
    return timestamp == aligned


def get_next_timeframe_boundary(timestamp: datetime, timeframe: str) -> datetime:
    """다음 timeframe 경계 시간 반환"""
    minutes = parse_timeframe_to_minutes(timeframe)
    if not minutes:
        return timestamp

    aligned = align_to_timeframe_boundary(timestamp, timeframe)
    if aligned == timestamp:
        # 이미 경계에 있으면 다음 경계로
        return aligned + timedelta(minutes=minutes)
    else:
        # 경계에 없으면 다음 경계가 정렬된 시간
        return aligned + timedelta(minutes=minutes)


def format_duration(seconds: int) -> str:
    """초 단위 시간을 사람이 읽기 쉬운 형태로 포맷팅"""
    if seconds < 60:
        return f"{seconds}초"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}분"
    elif seconds < 86400:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        if remaining_minutes > 0:
            return f"{hours}시간 {remaining_minutes}분"
        else:
            return f"{hours}시간"
    else:
        days = seconds // 86400
        remaining_hours = (seconds % 86400) // 3600
        if remaining_hours > 0:
            return f"{days}일 {remaining_hours}시간"
        else:
            return f"{days}일"


def timestamp_to_kst_string(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """UTC 타임스탬프를 KST 문자열로 변환"""
    # KST는 UTC+9
    kst_time = timestamp + timedelta(hours=9)
    return kst_time.strftime(format_str)


def kst_string_to_utc_timestamp(kst_string: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """KST 문자열을 UTC 타임스탬프로 변환"""
    kst_time = datetime.strptime(kst_string, format_str)
    # KST에서 UTC로 변환 (9시간 빼기)
    utc_time = kst_time - timedelta(hours=9)
    return utc_time
