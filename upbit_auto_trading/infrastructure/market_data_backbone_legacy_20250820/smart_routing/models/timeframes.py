"""
표준화된 타임프레임 정의

이 모듈은 거래소 독립적인 타임프레임 표준을 제공합니다.
업비트 API의 분/일/주/월 단위를 기준으로 하되, 다른 거래소와의
호환성도 고려하여 설계되었습니다.
"""

from enum import Enum
from typing import Optional, Tuple
from datetime import timedelta

from upbit_auto_trading.infrastructure.logging import create_component_logger


class Timeframe(Enum):
    """표준화된 타임프레임 열거형"""

    # 분봉 (Minutes)
    MINUTES_1 = "1m"
    MINUTES_3 = "3m"
    MINUTES_5 = "5m"
    MINUTES_10 = "10m"
    MINUTES_15 = "15m"
    MINUTES_30 = "30m"
    MINUTES_60 = "60m"    # 1시간봉을 60분으로 표기

    # 시간봉 (Hours) - 별칭
    HOURS_1 = "1h"
    HOURS_4 = "4h"
    HOURS_6 = "6h"
    HOURS_8 = "8h"
    HOURS_12 = "12h"

    # 일봉/주봉/월봉 (Days/Weeks/Months)
    DAYS_1 = "1d"
    WEEKS_1 = "1w"
    MONTHS_1 = "1M"

    def __str__(self) -> str:
        """문자열 표현"""
        return self.value

    @property
    def minutes(self) -> int:
        """타임프레임을 분 단위로 변환"""
        conversion_map = {
            self.MINUTES_1: 1,
            self.MINUTES_3: 3,
            self.MINUTES_5: 5,
            self.MINUTES_10: 10,
            self.MINUTES_15: 15,
            self.MINUTES_30: 30,
            self.MINUTES_60: 60,
            self.HOURS_1: 60,
            self.HOURS_4: 240,
            self.HOURS_6: 360,
            self.HOURS_8: 480,
            self.HOURS_12: 720,
            self.DAYS_1: 1440,         # 24 * 60
            self.WEEKS_1: 10080,       # 7 * 24 * 60
            self.MONTHS_1: 43200,      # 30 * 24 * 60 (근사값)
        }
        return conversion_map[self]

    @property
    def timedelta(self) -> timedelta:
        """timedelta 객체로 변환"""
        return timedelta(minutes=self.minutes)

    def to_upbit_format(self) -> Tuple[str, str]:
        """업비트 API 형식으로 변환 (타입, 단위)"""
        upbit_mapping = {
            # 분봉 → candles/minutes/{unit}
            self.MINUTES_1: ("minutes", "1"),
            self.MINUTES_3: ("minutes", "3"),
            self.MINUTES_5: ("minutes", "5"),
            self.MINUTES_10: ("minutes", "10"),
            self.MINUTES_15: ("minutes", "15"),
            self.MINUTES_30: ("minutes", "30"),
            self.MINUTES_60: ("minutes", "60"),
            self.HOURS_1: ("minutes", "60"),      # 업비트는 60분으로 표기
            self.HOURS_4: ("minutes", "240"),     # 업비트는 240분으로 표기
            # 일/주/월봉
            self.DAYS_1: ("days", ""),
            self.WEEKS_1: ("weeks", ""),
            self.MONTHS_1: ("months", ""),
        }

        if self not in upbit_mapping:
            raise ValueError(f"업비트에서 지원되지 않는 타임프레임: {self}")

        return upbit_mapping[self]

    def to_binance_format(self) -> str:
        """바이낸스 API 형식으로 변환"""
        binance_mapping = {
            self.MINUTES_1: "1m",
            self.MINUTES_3: "3m",
            self.MINUTES_5: "5m",
            self.MINUTES_15: "15m",
            self.MINUTES_30: "30m",
            self.HOURS_1: "1h",
            self.HOURS_4: "4h",
            self.HOURS_6: "6h",
            self.HOURS_8: "8h",
            self.HOURS_12: "12h",
            self.DAYS_1: "1d",
            self.WEEKS_1: "1w",
            self.MONTHS_1: "1M",
        }

        if self not in binance_mapping:
            raise ValueError(f"바이낸스에서 지원되지 않는 타임프레임: {self}")

        return binance_mapping[self]

    @classmethod
    def from_upbit_path(cls, path: str) -> 'Timeframe':
        """업비트 API 경로에서 타임프레임 추출"""
        # 예: "/v1/candles/minutes/15" → MINUTES_15
        if "/minutes/" in path:
            unit = path.split("/minutes/")[1].split("?")[0]
            mapping = {
                "1": cls.MINUTES_1,
                "3": cls.MINUTES_3,
                "5": cls.MINUTES_5,
                "10": cls.MINUTES_10,
                "15": cls.MINUTES_15,
                "30": cls.MINUTES_30,
                "60": cls.MINUTES_60,
                "240": cls.HOURS_4,
            }
            if unit in mapping:
                return mapping[unit]
        elif "/days" in path:
            return cls.DAYS_1
        elif "/weeks" in path:
            return cls.WEEKS_1
        elif "/months" in path:
            return cls.MONTHS_1

        raise ValueError(f"업비트 경로에서 타임프레임을 찾을 수 없습니다: {path}")

    @classmethod
    def from_string(cls, timeframe_str: str) -> 'Timeframe':
        """문자열에서 타임프레임 생성"""
        # 대소문자 구분 없이 매칭
        for tf in cls:
            if tf.value.lower() == timeframe_str.lower():
                return tf

        # 숫자+단위 형식 파싱 (예: "15m", "4h", "1d")
        import re
        match = re.match(r"(\d+)([mhd]|M)", timeframe_str.lower())
        if match:
            number, unit = match.groups()
            number = int(number)

            if unit == "m":  # 분
                for tf in cls:
                    if "MINUTES_" in tf.name and tf.minutes == number:
                        return tf
            elif unit == "h":  # 시간
                for tf in cls:
                    if "HOURS_" in tf.name and tf.minutes == number * 60:
                        return tf
            elif unit == "d":  # 일
                if number == 1:
                    return cls.DAYS_1
            elif unit == "M":  # 월
                if number == 1:
                    return cls.MONTHS_1

        raise ValueError(f"알 수 없는 타임프레임 형식: {timeframe_str}")

    @property
    def is_minute_based(self) -> bool:
        """분봉 기반인지 확인"""
        return self.minutes < 60 or self in [self.MINUTES_60, self.HOURS_1]

    @property
    def is_hour_based(self) -> bool:
        """시간봉 기반인지 확인"""
        return 60 <= self.minutes < 1440

    @property
    def is_day_based(self) -> bool:
        """일봉 이상인지 확인"""
        return self.minutes >= 1440

    @property
    def supports_websocket(self) -> bool:
        """WebSocket에서 지원하는지 확인 (업비트 기준)"""
        # 업비트 WebSocket은 실시간 데이터만 지원 (캔들 데이터는 REST만)
        return False  # 현재 업비트는 실시간 캔들 구독을 지원하지 않음

    @property
    def supports_realtime(self) -> bool:
        """실시간 데이터 지원 여부"""
        # 분봉은 실시간성이 높음
        return self.is_minute_based and self.minutes <= 60


class TimeframeValidator:
    """타임프레임 유효성 검증 및 변환 도구"""

    def __init__(self):
        self._logger = create_component_logger("TimeframeValidator")

    def validate_for_exchange(self, timeframe: Timeframe, exchange: str) -> bool:
        """특정 거래소에서 지원하는 타임프레임인지 확인"""
        try:
            if exchange == "upbit":
                timeframe.to_upbit_format()
                return True
            elif exchange == "binance":
                timeframe.to_binance_format()
                return True
            else:
                self._logger.warning(f"알 수 없는 거래소: {exchange}")
                return False
        except ValueError:
            return False

    def get_supported_timeframes(self, exchange: str) -> list[Timeframe]:
        """거래소별 지원 타임프레임 목록"""
        supported = []
        for tf in Timeframe:
            if self.validate_for_exchange(tf, exchange):
                supported.append(tf)
        return supported

    def find_nearest_supported(self, target_minutes: int, exchange: str) -> Optional[Timeframe]:
        """가장 가까운 지원 타임프레임 찾기"""
        supported = self.get_supported_timeframes(exchange)
        if not supported:
            return None

        # 분 차이를 기준으로 가장 가까운 것 선택
        return min(supported, key=lambda tf: abs(tf.minutes - target_minutes))


# 편의 상수
MINUTE_TIMEFRAMES = [
    Timeframe.MINUTES_1, Timeframe.MINUTES_3, Timeframe.MINUTES_5,
    Timeframe.MINUTES_10, Timeframe.MINUTES_15, Timeframe.MINUTES_30,
    Timeframe.MINUTES_60
]

HOUR_TIMEFRAMES = [
    Timeframe.HOURS_1, Timeframe.HOURS_4, Timeframe.HOURS_6,
    Timeframe.HOURS_8, Timeframe.HOURS_12
]

DAY_TIMEFRAMES = [
    Timeframe.DAYS_1, Timeframe.WEEKS_1, Timeframe.MONTHS_1
]

UPBIT_SUPPORTED_TIMEFRAMES = [
    Timeframe.MINUTES_1, Timeframe.MINUTES_3, Timeframe.MINUTES_5,
    Timeframe.MINUTES_10, Timeframe.MINUTES_15, Timeframe.MINUTES_30,
    Timeframe.MINUTES_60, Timeframe.HOURS_4,
    Timeframe.DAYS_1, Timeframe.WEEKS_1, Timeframe.MONTHS_1
]


# 편의 함수
def parse_timeframe(timeframe_str: str) -> Timeframe:
    """문자열에서 타임프레임 파싱 (별칭)"""
    return Timeframe.from_string(timeframe_str)
