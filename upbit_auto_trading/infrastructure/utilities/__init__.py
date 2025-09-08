# Infrastructure Utilities Package
"""
Infrastructure Layer 기술적 유틸리티 모음

DDD 원칙에 따라 순수한 기술적 기능만 포함:
- 파일 시스템 조작
- 시간 계산 및 변환
- 수학적 계산
- 암호화 헬퍼
- 네트워크 유틸리티

주의사항:
- Domain 로직 포함 금지
- UI/Presentation 관련 기능 금지
- 비즈니스 규칙 포함 금지
"""

from .file_operations.file_utils import (
    calculate_file_checksum,
    verify_file_integrity,
    check_disk_space,
    get_file_metadata,
    safe_atomic_copy,
    ensure_directory_exists,
    cleanup_temp_files
)

from .time_operations.time_utils import (
    parse_timeframe_to_seconds,
    parse_timeframe_to_minutes,
    align_to_timeframe_boundary,
    generate_timeframe_intervals,
    calculate_missing_intervals,
    format_duration,
    timestamp_to_kst_string,
    kst_string_to_utc_timestamp
)

from .math_calculations.financial_math import (
    safe_decimal,
    percentage_change,
    round_to_tick_size,
    calculate_order_amount,
    calculate_rsi,
    calculate_moving_average,
    calculate_volatility,
    is_within_tolerance,
    calculate_position_size,
    normalize_to_range
)

__all__ = [
    # File Operations
    'calculate_file_checksum',
    'verify_file_integrity',
    'check_disk_space',
    'get_file_metadata',
    'safe_atomic_copy',
    'ensure_directory_exists',
    'cleanup_temp_files',

    # Time Operations
    'parse_timeframe_to_seconds',
    'parse_timeframe_to_minutes',
    'align_to_timeframe_boundary',
    'generate_timeframe_intervals',
    'calculate_missing_intervals',
    'format_duration',
    'timestamp_to_kst_string',
    'kst_string_to_utc_timestamp',

    # Math Calculations
    'safe_decimal',
    'percentage_change',
    'round_to_tick_size',
    'calculate_order_amount',
    'calculate_rsi',
    'calculate_moving_average',
    'calculate_volatility',
    'is_within_tolerance',
    'calculate_position_size',
    'normalize_to_range'
]
