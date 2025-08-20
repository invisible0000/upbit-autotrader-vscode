"""
타임프레임 도메인 모델

거래소 독립적인 시간 간격 표현을 제공합니다.
업비트의 분봉/일봉 구조를 완전히 추상화합니다.
"""

from enum import Enum
from typing import Optional
from datetime import timedelta


class Timeframe(Enum):
    """거래소 독립적 타임프레임 정의

    업비트 API의 URL 구조를 몰라도 되도록
    표준화된 타임프레임을 제공합니다.
    """

    # 분봉
    MINUTE_1 = "1m"
    MINUTE_3 = "3m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"

    # 시간봉
    HOUR_1 = "1h"
    HOUR_4 = "4h"

    # 일봉
    DAY_1 = "1d"

    # 주봉
    WEEK_1 = "1w"

    # 월봉
    MONTH_1 = "1M"

    def to_upbit_url_path(self) -> str:
        """업비트 API URL 경로로 변환

        Returns:
            업비트 API 경로 (예: "/v1/candles/minutes/15")
        """
        mapping = {
            # 분봉
            self.MINUTE_1: "/v1/candles/minutes/1",
            self.MINUTE_3: "/v1/candles/minutes/3",
            self.MINUTE_5: "/v1/candles/minutes/5",
            self.MINUTE_15: "/v1/candles/minutes/15",
            self.MINUTE_30: "/v1/candles/minutes/30",

            # 시간봉
            self.HOUR_1: "/v1/candles/minutes/60",
            self.HOUR_4: "/v1/candles/minutes/240",

            # 일봉
            self.DAY_1: "/v1/candles/days",

            # 주봉
            self.WEEK_1: "/v1/candles/weeks",

            # 월봉
            self.MONTH_1: "/v1/candles/months"
        }

        return mapping[self]

    def to_minutes(self) -> int:
        """분 단위로 변환

        Returns:
            분 단위 시간 간격
        """
        mapping = {
            # 분봉
            self.MINUTE_1: 1,
            self.MINUTE_3: 3,
            self.MINUTE_5: 5,
            self.MINUTE_15: 15,
            self.MINUTE_30: 30,

            # 시간봉
            self.HOUR_1: 60,
            self.HOUR_4: 240,

            # 일봉
            self.DAY_1: 1440,  # 24 * 60

            # 주봉
            self.WEEK_1: 10080,  # 7 * 24 * 60

            # 월봉 (30일 기준)
            self.MONTH_1: 43200  # 30 * 24 * 60
        }

        return mapping[self]

    def to_timedelta(self) -> timedelta:
        """timedelta 객체로 변환

        Returns:
            시간 간격을 나타내는 timedelta
        """
        return timedelta(minutes=self.to_minutes())

    @classmethod
    def from_upbit_url_path(cls, url_path: str) -> Optional['Timeframe']:
        """업비트 URL 경로에서 타임프레임 추출

        Args:
            url_path: 업비트 API URL 경로

        Returns:
            해당하는 Timeframe 또는 None
        """
        reverse_mapping = {
            "/v1/candles/minutes/1": cls.MINUTE_1,
            "/v1/candles/minutes/3": cls.MINUTE_3,
            "/v1/candles/minutes/5": cls.MINUTE_5,
            "/v1/candles/minutes/15": cls.MINUTE_15,
            "/v1/candles/minutes/30": cls.MINUTE_30,
            "/v1/candles/minutes/60": cls.HOUR_1,
            "/v1/candles/minutes/240": cls.HOUR_4,
            "/v1/candles/days": cls.DAY_1,
            "/v1/candles/weeks": cls.WEEK_1,
            "/v1/candles/months": cls.MONTH_1
        }

        return reverse_mapping.get(url_path)

    def __str__(self) -> str:
        """문자열 표현"""
        return self.value

    def __repr__(self) -> str:
        """디버그 표현"""
        return f"Timeframe.{self.name}"


# 자주 사용되는 타임프레임들을 상수로 정의
class CommonTimeframes:
    """자주 사용되는 타임프레임들"""

    # 단기 분석용
    M1 = Timeframe.MINUTE_1
    M5 = Timeframe.MINUTE_5
    M15 = Timeframe.MINUTE_15

    # 중기 분석용
    H1 = Timeframe.HOUR_1
    H4 = Timeframe.HOUR_4

    # 장기 분석용
    D1 = Timeframe.DAY_1
    W1 = Timeframe.WEEK_1

    # 모든 타임프레임 리스트
    ALL = [
        Timeframe.MINUTE_1,
        Timeframe.MINUTE_3,
        Timeframe.MINUTE_5,
        Timeframe.MINUTE_15,
        Timeframe.MINUTE_30,
        Timeframe.HOUR_1,
        Timeframe.HOUR_4,
        Timeframe.DAY_1,
        Timeframe.WEEK_1,
        Timeframe.MONTH_1
    ]
