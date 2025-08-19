"""
MarketDataBackbone V2 - 스마트 채널 라우터 및 필드 매퍼

지능적 채널 라우팅과 데이터 구조 통합을 담당합니다.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .channel_router import ChannelDecision


class RequestPattern:
    """요청 패턴 분석 클래스"""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.request_count = 0
        self.first_request = datetime.now()
        self.last_request = datetime.now()
        self.request_intervals: List[float] = []

    def record_request(self) -> None:
        """요청 기록"""
        now = datetime.now()
        if self.request_count > 0:
            interval = (now - self.last_request).total_seconds()
            self.request_intervals.append(interval)
            # 최근 10개만 유지
            if len(self.request_intervals) > 10:
                self.request_intervals.pop(0)

        self.request_count += 1
        self.last_request = now

    def get_frequency(self) -> float:
        """요청 빈도 반환 (초당 요청 수)"""
        if len(self.request_intervals) == 0:
            return 0.0

        avg_interval = sum(self.request_intervals) / len(self.request_intervals)
        return 1.0 / avg_interval if avg_interval > 0 else 0.0

    def is_high_frequency(self, threshold: float = 0.1) -> bool:
        """고빈도 요청 여부 (10초에 1회 이상)"""
        return self.get_frequency() > threshold


class SmartChannelRouter:
    """
    지능적 채널 라우터 (전문가 권고 핵심 구현)

    기능:
    ✅ 요청 빈도 감지 및 자동 WebSocket 전환
    ✅ 실시간성 vs 신뢰성 자동 판단
    ✅ 연결 상태 모니터링 및 폴백
    """

    def __init__(self):
        self._logger = create_component_logger("SmartChannelRouter")

        # 요청 패턴 추적
        self._request_patterns: Dict[str, RequestPattern] = {}

        # 채널 상태 추적
        self._channel_health = {
            "rest": {"available": True, "last_error": None, "error_count": 0},
            "websocket": {"available": False, "last_error": None, "error_count": 0}
        }

        # 설정값
        self._high_freq_threshold = 0.1  # 10초에 1회 이상
        self._websocket_fallback_threshold = 3  # 3회 실패 시 REST로 폴백

    def route_request(self, symbol: str, request_type: str = "ticker",
                      hint: Optional[str] = None) -> ChannelDecision:
        """
        요청을 적절한 채널로 라우팅

        Args:
            symbol: 마켓 심볼
            request_type: 요청 타입 ("ticker", "orderbook", "trades")
            hint: 사용자 힌트 ("realtime", "historical", "rest", "websocket")

        Returns:
            ChannelDecision: 채널 선택 결정
        """
        # 1. 명시적 힌트 처리
        if hint == "rest":
            return ChannelDecision("rest", "사용자가 REST 채널 명시", 1.0)
        elif hint == "websocket":
            if self._is_websocket_available():
                return ChannelDecision("websocket", "사용자가 WebSocket 채널 명시", 1.0)
            else:
                return ChannelDecision("rest", "WebSocket 불가로 REST 폴백", 0.7)

        # 2. 요청 패턴 분석
        pattern = self._get_or_create_pattern(symbol)
        pattern.record_request()

        # 3. 지능적 라우팅 결정
        return self._make_intelligent_decision(symbol, request_type, pattern, hint)

    def _make_intelligent_decision(self, symbol: str, request_type: str,
                                   pattern: RequestPattern, hint: Optional[str]) -> ChannelDecision:
        """지능적 라우팅 결정"""

        # 실시간성 요구도 판단
        is_realtime_needed = (
            hint == "realtime"
            or pattern.is_high_frequency(self._high_freq_threshold)
            or request_type in ["orderbook", "trades"]
        )

        # WebSocket 사용 가능하고 실시간성이 필요한 경우
        if is_realtime_needed and self._is_websocket_available():
            return ChannelDecision(
                "websocket",
                f"고빈도 요청({pattern.get_frequency():.3f} req/s) 또는 실시간 데이터 필요",
                0.9
            )

        # 신뢰성 우선 또는 WebSocket 불가
        if not self._is_websocket_available():
            reason = "WebSocket 연결 불가로 REST 사용"
            confidence = 0.8
        else:
            reason = "저빈도 요청으로 REST 충분"
            confidence = 0.9

        return ChannelDecision("rest", reason, confidence)

    def update_channel_health(self, channel: str, success: bool, error: Optional[Exception] = None) -> None:
        """채널 상태 업데이트"""
        health = self._channel_health[channel]

        if success:
            health["error_count"] = 0
            health["last_error"] = None
            if not health["available"]:
                self._logger.info(f"{channel} 채널 복구됨")
                health["available"] = True
        else:
            health["error_count"] += 1
            health["last_error"] = error

            # 임계값 초과 시 채널 비활성화
            if health["error_count"] >= self._websocket_fallback_threshold:
                if health["available"]:
                    self._logger.warning(f"{channel} 채널 비활성화 (연속 {health['error_count']}회 실패)")
                    health["available"] = False

    def _get_or_create_pattern(self, symbol: str) -> RequestPattern:
        """요청 패턴 조회 또는 생성"""
        if symbol not in self._request_patterns:
            self._request_patterns[symbol] = RequestPattern(symbol)
        return self._request_patterns[symbol]

    def _is_websocket_available(self) -> bool:
        """WebSocket 사용 가능 여부 확인"""
        return self._channel_health["websocket"]["available"]

    def get_channel_statistics(self) -> Dict[str, Any]:
        """채널 통계 정보 반환"""
        patterns_stats = {}
        for symbol, pattern in self._request_patterns.items():
            patterns_stats[symbol] = {
                "request_count": pattern.request_count,
                "frequency": pattern.get_frequency(),
                "is_high_frequency": pattern.is_high_frequency()
            }

        return {
            "channel_health": self._channel_health.copy(),
            "request_patterns": patterns_stats,
            "active_symbols": len(self._request_patterns)
        }


class FieldMapper:
    """
    REST ↔ WebSocket 필드 변환기 (전문가 권고: 데이터 구조 통일)
    """

    # REST -> 통합 필드 매핑
    REST_FIELD_MAP = {
        "market": "symbol",
        "trade_price": "current_price",
        "signed_change_rate": "change_rate",
        "signed_change_price": "change_amount",
        "acc_trade_volume_24h": "volume_24h",
        "high_price": "high_24h",
        "low_price": "low_24h",
        "prev_closing_price": "prev_closing_price"
    }

    # WebSocket (DEFAULT) -> 통합 필드 매핑
    WEBSOCKET_FIELD_MAP = {
        "code": "symbol",
        "trade_price": "current_price",
        "signed_change_rate": "change_rate",
        "signed_change_price": "change_amount",
        "acc_trade_volume_24h": "volume_24h",
        "high_price": "high_24h",
        "low_price": "low_24h",
        "prev_closing_price": "prev_closing_price"
    }

    # WebSocket (SIMPLE) -> 통합 필드 매핑
    WEBSOCKET_SIMPLE_FIELD_MAP = {
        "cd": "symbol",
        "tp": "current_price",
        "scr": "change_rate",
        "scp": "change_amount",
        "aav24": "volume_24h",
        "hp": "high_24h",
        "lp": "low_24h"
    }

    @classmethod
    def map_rest_data(cls, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """REST 데이터를 통합 형태로 변환"""
        mapped = {}
        for rest_field, unified_field in cls.REST_FIELD_MAP.items():
            if rest_field in raw_data:
                mapped[unified_field] = raw_data[rest_field]
        return mapped

    @classmethod
    def map_websocket_data(cls, raw_data: Dict[str, Any], is_simple: bool = False) -> Dict[str, Any]:
        """WebSocket 데이터를 통합 형태로 변환"""
        field_map = cls.WEBSOCKET_SIMPLE_FIELD_MAP if is_simple else cls.WEBSOCKET_FIELD_MAP

        mapped = {}
        for ws_field, unified_field in field_map.items():
            if ws_field in raw_data:
                mapped[unified_field] = raw_data[ws_field]
        return mapped
