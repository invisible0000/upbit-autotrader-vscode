"""
ChannelRouter - 채널 선택 로직 (Phase 1.1 단순 구현)

Phase 1.1에서는 기본적인 전략만 지원
Phase 1.2에서 성능 기반 지능적 라우팅 추가 예정
"""

from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime, timedelta

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .market_data_backbone import ChannelStrategy


class ChannelDecision:
    """채널 선택 결과"""

    def __init__(self, channel: str, reason: str, confidence: float = 1.0):
        self.channel = channel  # "rest" or "websocket"
        self.reason = reason    # 선택 이유
        self.confidence = confidence  # 신뢰도 (0.0-1.0)


class ChannelRouter:
    """
    채널 선택 로직 관리

    Phase 1.1: 단순한 전략 기반 선택
    Phase 1.2: 성능 메트릭 기반 지능적 선택
    """

    def __init__(self):
        """ChannelRouter 초기화"""
        self._logger = create_component_logger("ChannelRouter")

        # Phase 1.2에서 구현 예정
        self._performance_history: Dict[str, list] = {
            "rest_latency": [],
            "websocket_latency": [],
            "rest_success_rate": [],
            "websocket_success_rate": []
        }

    def choose_channel(self, symbol: str, strategy: ChannelStrategy,
                      request_type: str = "ticker") -> ChannelDecision:
        """
        채널 선택 결정

        Args:
            symbol: 마켓 심볼
            strategy: 채널 선택 전략
            request_type: 요청 타입 ("ticker", "candle", "orderbook")

        Returns:
            ChannelDecision: 채널 선택 결과
        """
        # Phase 1.1 단순 구현
        if strategy == ChannelStrategy.REST_ONLY:
            return ChannelDecision(
                channel="rest",
                reason="사용자가 REST API 전용 선택",
                confidence=1.0
            )

        elif strategy == ChannelStrategy.WEBSOCKET_ONLY:
            # Phase 1.1에서는 WebSocket 미지원
            self._logger.warning("WebSocket 전용 요청이지만 Phase 1.1에서는 미지원")
            return ChannelDecision(
                channel="rest",
                reason="WebSocket은 Phase 1.2에서 지원 예정, REST로 대체",
                confidence=0.5
            )

        else:  # ChannelStrategy.AUTO
            # Phase 1.1에서는 항상 REST API 사용
            return ChannelDecision(
                channel="rest",
                reason="Phase 1.1에서는 REST API만 지원",
                confidence=0.8
            )

    def update_performance_metric(self, channel: str, metric_type: str,
                                 value: float, success: bool = True) -> None:
        """
        성능 메트릭 업데이트 - Phase 1.2에서 구현 예정

        Args:
            channel: 채널 ("rest" or "websocket")
            metric_type: 메트릭 타입 ("latency", "success_rate")
            value: 측정값
            success: 성공 여부
        """
        # Phase 1.1에서는 로깅만 수행
        self._logger.debug(f"성능 메트릭 기록: {channel}.{metric_type} = {value} (성공: {success})")

        # Phase 1.2에서 실제 구현 예정
        # 현재는 최근 10개만 유지하는 간단한 구현
        history_key = f"{channel}_{metric_type}"
        if history_key in self._performance_history:
            history = self._performance_history[history_key]
            history.append({
                "value": value,
                "success": success,
                "timestamp": datetime.now()
            })
            # 최근 10개만 유지
            if len(history) > 10:
                history.pop(0)

    def get_channel_performance(self, channel: str) -> Dict[str, Any]:
        """
        채널 성능 정보 조회 - Phase 1.2에서 구현 예정

        Args:
            channel: 채널 ("rest" or "websocket")

        Returns:
            dict: 성능 정보
        """
        # Phase 1.1 단순 구현
        if channel == "rest":
            return {
                "availability": True,
                "avg_latency": 150.0,  # 추정값
                "success_rate": 0.95,  # 추정값
                "last_check": datetime.now(),
                "status": "available"
            }
        elif channel == "websocket":
            return {
                "availability": False,  # Phase 1.1에서는 미지원
                "avg_latency": None,
                "success_rate": None,
                "last_check": None,
                "status": "not_implemented"
            }
        else:
            return {
                "availability": False,
                "status": "unknown_channel"
            }

    def get_optimal_strategy(self, request_type: str,
                           data_volume: Optional[int] = None) -> ChannelStrategy:
        """
        요청 특성에 따른 최적 전략 추천 - Phase 1.2에서 구현 예정

        Args:
            request_type: 요청 타입
            data_volume: 데이터 볼륨 (예: 캔들 개수)

        Returns:
            ChannelStrategy: 추천 전략
        """
        # Phase 1.1에서는 항상 REST 우선
        self._logger.debug(f"최적 전략 요청: {request_type}, 볼륨: {data_volume}")
        return ChannelStrategy.REST_ONLY

    def is_websocket_available(self) -> bool:
        """WebSocket 사용 가능 여부"""
        # Phase 1.1에서는 false
        return False

    def is_rest_available(self) -> bool:
        """REST API 사용 가능 여부"""
        # Phase 1.1에서는 항상 true
        return True
