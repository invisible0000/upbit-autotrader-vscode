# Time Operations Utilities
"""
시간 계산 및 변환 유틸리티

기능:
- Timeframe 파싱 (문자열 → 초/분 변환)
- 시간 경계 정렬
- 시간 간격 생성
- 누락 시간 계산
- 지속 시간 포맷팅
- KST/UTC 변환
"""

from .time_utils import (
    parse_timeframe_to_seconds,
    parse_timeframe_to_minutes,
    align_to_timeframe_boundary,
    generate_timeframe_intervals,
    calculate_missing_intervals,
    is_timestamp_aligned,
    get_next_timeframe_boundary,
    format_duration,
    timestamp_to_kst_string,
    kst_string_to_utc_timestamp
)

__all__ = [
    'parse_timeframe_to_seconds',
    'parse_timeframe_to_minutes',
    'align_to_timeframe_boundary',
    'generate_timeframe_intervals',
    'calculate_missing_intervals',
    'is_timestamp_aligned',
    'get_next_timeframe_boundary',
    'format_duration',
    'timestamp_to_kst_string',
    'kst_string_to_utc_timestamp'
]
