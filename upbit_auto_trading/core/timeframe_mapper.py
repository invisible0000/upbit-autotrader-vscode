"""
Timeframe 매핑 유틸리티
API 친화적 값과 사용자 친화적 한글 값 간의 변환을 담당
"""

from typing import Dict, Optional


class TimeframeMapper:
    """Timeframe 값 변환을 위한 매핑 클래스"""

    # API 친화적 값 → 사용자 표시용 한글 값
    API_TO_DISPLAY: Dict[str, str] = {
        "position_follow": "포지션 설정 따름",
        "1m": "1분",
        "3m": "3분",
        "5m": "5분",
        "10m": "10분",
        "15m": "15분",
        "30m": "30분",
        "1h": "1시간",
        "4h": "4시간",
        "1d": "1일",
        "1w": "1주",
        "1M": "1월"
    }

    # 사용자 표시용 한글 값 → API 친화적 값
    DISPLAY_TO_API: Dict[str, str] = {v: k for k, v in API_TO_DISPLAY.items()}

    @classmethod
    def to_display(cls, api_value: str) -> str:
        """API 친화적 값을 사용자 표시용 한글로 변환

        Args:
            api_value: API에서 사용하는 timeframe 값 (예: "1m", "position_follow")

        Returns:
            사용자에게 표시할 한글 값 (예: "1분", "포지션 설정 따름")
        """
        return cls.API_TO_DISPLAY.get(api_value, api_value)

    @classmethod
    def to_api(cls, display_value: str) -> str:
        """사용자 표시용 한글을 API 친화적 값으로 변환

        Args:
            display_value: 사용자에게 표시되는 한글 값 (예: "1분", "포지션 설정 따름")

        Returns:
            API에서 사용할 값 (예: "1m", "position_follow")
        """
        return cls.DISPLAY_TO_API.get(display_value, display_value)

    @classmethod
    def get_all_display_values(cls) -> list[str]:
        """모든 사용자 표시용 값 목록 반환"""
        return list(cls.API_TO_DISPLAY.values())

    @classmethod
    def get_all_api_values(cls) -> list[str]:
        """모든 API 친화적 값 목록 반환"""
        return list(cls.API_TO_DISPLAY.keys())

    @classmethod
    def is_valid_api_value(cls, value: str) -> bool:
        """유효한 API 값인지 확인"""
        return value in cls.API_TO_DISPLAY

    @classmethod
    def is_valid_display_value(cls, value: str) -> bool:
        """유효한 표시용 값인지 확인"""
        return value in cls.DISPLAY_TO_API


# 편의를 위한 함수들
def timeframe_to_display(api_value: str) -> str:
    """API 값을 표시용으로 변환"""
    return TimeframeMapper.to_display(api_value)


def timeframe_to_api(display_value: str) -> str:
    """표시용 값을 API용으로 변환"""
    return TimeframeMapper.to_api(display_value)


def get_timeframe_display_list() -> list[str]:
    """UI 콤보박스용 표시 값 목록"""
    return TimeframeMapper.get_all_display_values()


def get_timeframe_api_list() -> list[str]:
    """API 호출용 값 목록"""
    return TimeframeMapper.get_all_api_values()
