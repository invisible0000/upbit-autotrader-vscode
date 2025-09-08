# TimeFrame Domain Value Object
from dataclasses import dataclass
from enum import Enum


class TimeFrameType(Enum):
    SECOND = "s"
    MINUTE = "m"
    HOUR = "h"
    DAY = "d"
    WEEK = "w"
    MONTH = "M"


@dataclass(frozen=True)
class TimeFrame:
    """TimeFrame Domain Value Object - DDD 핵심 개념"""
    value: str

    def __post_init__(self):
        if not self._is_valid():
            raise ValueError(f"Invalid timeframe: {self.value}")

    def _is_valid(self) -> bool:
        valid_timeframes = {
            '1s', '1m', '3m', '5m', '15m', '30m',
            '1h', '4h', '1d', '1w', '1M'
        }
        return self.value in valid_timeframes

    @property
    def seconds(self) -> int:
        """timeframe을 초로 변환 (Domain 로직)"""
        mapping = {
            '1s': 1, '1m': 60, '3m': 180, '5m': 300, '15m': 900,
            '30m': 1800, '1h': 3600, '4h': 14400, '1d': 86400,
            '1w': 604800, '1M': 2592000
        }
        return mapping[self.value]

    @property
    def type(self) -> TimeFrameType:
        """timeframe 타입 반환"""
        suffix = self.value[-1]
        return TimeFrameType(suffix)

    @property
    def magnitude(self) -> int:
        """timeframe 크기 반환 (1m -> 1, 15m -> 15)"""
        return int(self.value[:-1]) if self.value[:-1].isdigit() else 1

    def is_higher_than(self, other: 'TimeFrame') -> bool:
        """다른 timeframe보다 큰지 비교"""
        return self.seconds > other.seconds

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other) -> bool:
        if isinstance(other, TimeFrame):
            return self.value == other.value
        elif isinstance(other, str):
            return self.value == other
        return False

    def __hash__(self) -> int:
        return hash(self.value)
