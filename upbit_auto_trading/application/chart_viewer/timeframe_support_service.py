"""
1개월 타임프레임 지원 서비스

기존 InMemoryEventBus와 호환되는 타임프레임 관리 시스템입니다.
WebSocket/API 하이브리드 모드를 구현하여 1M 타임프레임까지 안전하게 지원합니다.

태스크 0.3: 1개월 타임프레임 지원 시스템
- TimeframeSupport 클래스 구현 ✅
- 1w, 1M 타임프레임 API 전용 처리 ✅
- WebSocket/API 하이브리드 모드 구현 ✅
- 기존 타임프레임과 호환성 보장 ✅
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.domain.events.chart_viewer_events import (
    ChartSubscriptionEvent,
    ChartViewerPriority,
    TimeframeSupport
)
logger = create_component_logger("TimeframeSupportService")


@dataclass(frozen=True)
class TimeframeConfiguration:
    """타임프레임별 설정"""
    timeframe: str
    data_source: str  # "websocket", "api", "hybrid"
    polling_interval_ms: int
    max_candles: int
    api_endpoint: str
    conversion_required: bool
    base_timeframe: Optional[str] = None  # 변환 시 기준 타임프레임


class TimeframeSupportService:
    """
    1개월 타임프레임 지원 서비스

    기존 InMemoryEventBus와 완전히 호환되며, 차트뷰어 전용 우선순위(5,8,10)를 사용합니다.
    1M 타임프레임까지 안전하게 지원하며, 기존 매매 시스템에 영향을 주지 않습니다.
    """

    def __init__(self, event_bus):
        """
        Args:
            event_bus: 기존 InMemoryEventBus 인스턴스 (완전 호환)
        """
        self.event_bus = event_bus
        self._configurations: Dict[str, TimeframeConfiguration] = {}
        self._active_subscriptions: Dict[str, Dict[str, Any]] = {}
        self._setup_timeframe_configurations()

        logger.info("TimeframeSupportService 초기화 완료 (기존 시스템 호환)")

    def _setup_timeframe_configurations(self):
        """타임프레임별 설정 초기화"""

        # WebSocket 지원 타임프레임 (실시간)
        websocket_timeframes = {
            "1m": TimeframeConfiguration(
                timeframe="1m",
                data_source="websocket",
                polling_interval_ms=10000,  # 10초 백업 폴링
                max_candles=500,
                api_endpoint="/v1/candles/minutes/1",
                conversion_required=False
            ),
            "3m": TimeframeConfiguration(
                timeframe="3m",
                data_source="hybrid",  # WebSocket + 변환
                polling_interval_ms=30000,
                max_candles=400,
                api_endpoint="/v1/candles/minutes/3",
                conversion_required=True,
                base_timeframe="1m"
            ),
            "5m": TimeframeConfiguration(
                timeframe="5m",
                data_source="hybrid",
                polling_interval_ms=60000,
                max_candles=300,
                api_endpoint="/v1/candles/minutes/5",
                conversion_required=True,
                base_timeframe="1m"
            ),
            "15m": TimeframeConfiguration(
                timeframe="15m",
                data_source="hybrid",
                polling_interval_ms=180000,
                max_candles=200,
                api_endpoint="/v1/candles/minutes/15",
                conversion_required=True,
                base_timeframe="1m"
            ),
            "30m": TimeframeConfiguration(
                timeframe="30m",
                data_source="hybrid",
                polling_interval_ms=300000,
                max_candles=150,
                api_endpoint="/v1/candles/minutes/30",
                conversion_required=True,
                base_timeframe="1m"
            ),
            "1h": TimeframeConfiguration(
                timeframe="1h",
                data_source="hybrid",
                polling_interval_ms=600000,
                max_candles=100,
                api_endpoint="/v1/candles/minutes/60",
                conversion_required=True,
                base_timeframe="1m"
            ),
            "4h": TimeframeConfiguration(
                timeframe="4h",
                data_source="hybrid",
                polling_interval_ms=1800000,
                max_candles=100,
                api_endpoint="/v1/candles/minutes/240",
                conversion_required=True,
                base_timeframe="1m"
            ),
            "1d": TimeframeConfiguration(
                timeframe="1d",
                data_source="api",  # WebSocket 미지원, API 전용
                polling_interval_ms=3600000,  # 1시간
                max_candles=100,
                api_endpoint="/v1/candles/days",
                conversion_required=True,
                base_timeframe="1h"  # 1시간봉에서 변환
            )
        }

        # API 전용 타임프레임 (1w, 1M)
        api_only_timeframes = {
            "1w": TimeframeConfiguration(
                timeframe="1w",
                data_source="api",
                polling_interval_ms=7200000,  # 2시간
                max_candles=52,  # 1년치
                api_endpoint="/v1/candles/weeks",
                conversion_required=True,
                base_timeframe="1d"  # 일봉에서 변환
            ),
            "1M": TimeframeConfiguration(
                timeframe="1M",
                data_source="api",
                polling_interval_ms=21600000,  # 6시간
                max_candles=24,  # 2년치
                api_endpoint="/v1/candles/months",
                conversion_required=True,
                base_timeframe="1d"  # 일봉에서 변환
            )
        }

        # 전체 설정 통합
        self._configurations.update(websocket_timeframes)
        self._configurations.update(api_only_timeframes)

        logger.info(f"타임프레임 설정 완료: {list(self._configurations.keys())}")

    def get_timeframe_configuration(self, timeframe: str) -> Optional[TimeframeConfiguration]:
        """타임프레임 설정 조회"""
        return self._configurations.get(timeframe)

    def is_timeframe_supported(self, timeframe: str) -> bool:
        """타임프레임 지원 여부 확인"""
        is_supported = TimeframeSupport.is_timeframe_supported(timeframe)

        if not is_supported:
            logger.warning(f"지원하지 않는 타임프레임: {timeframe}")

        return is_supported

    def get_data_source_strategy(self, timeframe: str) -> str:
        """타임프레임별 데이터 소스 전략 반환"""
        config = self.get_timeframe_configuration(timeframe)
        if not config:
            logger.error(f"타임프레임 설정을 찾을 수 없음: {timeframe}")
            return "api"  # 기본값

        strategy = config.data_source
        logger.debug(f"타임프레임 {timeframe} 데이터 소스 전략: {strategy}")

        return strategy

    def get_polling_interval(self, timeframe: str, window_state: str = "active") -> int:
        """
        타임프레임별 폴링 주기 반환 (창 상태 고려)

        Args:
            timeframe: 타임프레임
            window_state: "active", "background", "minimized"
        """
        config = self.get_timeframe_configuration(timeframe)
        if not config:
            return 60000  # 기본값: 1분

        base_interval = config.polling_interval_ms

        # 창 상태별 폴링 주기 조정 (리소스 절약)
        multiplier = {
            "active": 1.0,      # 정상 주기
            "background": 2.0,  # 2배 느리게
            "minimized": 4.0    # 4배 느리게
        }.get(window_state, 1.0)

        adjusted_interval = int(base_interval * multiplier)

        logger.debug(f"폴링 주기 조정: {timeframe} {window_state} -> {adjusted_interval}ms")

        return adjusted_interval

    async def subscribe_timeframe(
        self,
        chart_id: str,
        symbol: str,
        timeframe: str,
        window_state: str = "active"
    ) -> bool:
        """
        타임프레임 구독 (기존 이벤트 버스 활용)

        기존 InMemoryEventBus의 subscribe 메서드를 활용하여 안전하게 구독합니다.
        차트뷰어 전용 우선순위(5,8,10)를 사용합니다.
        """
        try:
            if not self.is_timeframe_supported(timeframe):
                logger.error(f"지원하지 않는 타임프레임: {timeframe}")
                return False

            config = self.get_timeframe_configuration(timeframe)
            if not config:
                logger.error(f"타임프레임 설정 없음: {timeframe}")
                return False

            # 구독 정보 생성
            subscription_key = f"{chart_id}:{symbol}:{timeframe}"

            # 차트뷰어 우선순위 결정 (기존 시스템과 격리)
            priority = ChartViewerPriority.get_window_priority(window_state)

            # 구독 이벤트 생성 (기존 DomainEvent 상속)
            subscription_event = ChartSubscriptionEvent(
                chart_id=chart_id,
                symbol=symbol,
                timeframe=timeframe,
                subscription_type="subscribe",
                subscription_id=subscription_key,
                window_active=(window_state == "active"),
                priority_level=priority,
                requested_count=config.max_candles
            )

            # 기존 InMemoryEventBus에 이벤트 발행 (완전 호환)
            await self.event_bus.publish(subscription_event)

            # 구독 정보 저장
            self._active_subscriptions[subscription_key] = {
                "chart_id": chart_id,
                "symbol": symbol,
                "timeframe": timeframe,
                "config": config,
                "window_state": window_state,
                "priority": priority,
                "subscribed_at": datetime.now()
            }

            logger.info(f"타임프레임 구독 완료: {subscription_key} (우선순위: {priority})")

            return True

        except Exception as e:
            logger.error(f"타임프레임 구독 실패: {chart_id}:{symbol}:{timeframe} - {e}")
            return False

    async def unsubscribe_timeframe(
        self,
        chart_id: str,
        symbol: str,
        timeframe: str
    ) -> bool:
        """
        타임프레임 구독 해제 (기존 이벤트 버스 활용)
        """
        try:
            subscription_key = f"{chart_id}:{symbol}:{timeframe}"

            if subscription_key not in self._active_subscriptions:
                logger.warning(f"구독되지 않은 타임프레임: {subscription_key}")
                return True  # 이미 해제됨

            subscription_info = self._active_subscriptions[subscription_key]

            # 구독 해제 이벤트 생성
            unsubscribe_event = ChartSubscriptionEvent(
                chart_id=chart_id,
                symbol=symbol,
                timeframe=timeframe,
                subscription_type="unsubscribe",
                subscription_id=subscription_key,
                priority_level=subscription_info["priority"]
            )

            # 기존 InMemoryEventBus에 이벤트 발행
            await self.event_bus.publish(unsubscribe_event)

            # 구독 정보 제거
            del self._active_subscriptions[subscription_key]

            logger.info(f"타임프레임 구독 해제 완료: {subscription_key}")

            return True

        except Exception as e:
            logger.error(f"타임프레임 구독 해제 실패: {chart_id}:{symbol}:{timeframe} - {e}")
            return False

    async def update_window_state(
        self,
        chart_id: str,
        new_state: str
    ) -> bool:
        """
        창 상태 변경 시 구독 우선순위 업데이트 (기존 시스템 안전)

        기존 매매 우선순위(1-3)에 영향을 주지 않고 차트뷰어 우선순위(5,8,10)만 조정합니다.
        """
        try:
            updated_count = 0
            new_priority = ChartViewerPriority.get_window_priority(new_state)

            # 해당 차트의 모든 구독 업데이트
            for subscription_key, subscription_info in self._active_subscriptions.items():
                if subscription_info["chart_id"] == chart_id:

                    # 우선순위 및 상태 업데이트
                    subscription_info["window_state"] = new_state
                    subscription_info["priority"] = new_priority

                    # 구독 업데이트 이벤트 생성
                    update_event = ChartSubscriptionEvent(
                        chart_id=chart_id,
                        symbol=subscription_info["symbol"],
                        timeframe=subscription_info["timeframe"],
                        subscription_type="update",
                        subscription_id=subscription_key,
                        window_active=(new_state == "active"),
                        priority_level=new_priority
                    )

                    # 기존 InMemoryEventBus에 우선순위 변경 이벤트 발행
                    await self.event_bus.publish(update_event)

                    updated_count += 1

            logger.info(f"창 상태 업데이트 완료: {chart_id} -> {new_state} (우선순위: {new_priority}, {updated_count}개 구독)")

            return True

        except Exception as e:
            logger.error(f"창 상태 업데이트 실패: {chart_id} -> {new_state} - {e}")
            return False

    def get_subscription_info(self, chart_id: str) -> Dict[str, Dict[str, Any]]:
        """차트별 구독 정보 조회"""
        chart_subscriptions = {}

        for subscription_key, subscription_info in self._active_subscriptions.items():
            if subscription_info["chart_id"] == chart_id:
                chart_subscriptions[subscription_key] = subscription_info.copy()

        return chart_subscriptions

    def get_all_supported_timeframes(self) -> List[Tuple[str, str, bool]]:
        """
        지원하는 모든 타임프레임 정보 반환

        Returns:
            List[Tuple[display_name, value, websocket_supported]]
        """
        timeframes = [
            ("1분", "1m", True),
            ("3분", "3m", True),
            ("5분", "5m", True),
            ("15분", "15m", True),
            ("30분", "30m", True),
            ("1시간", "1h", True),
            ("4시간", "4h", True),
            ("1일", "1d", False),
            ("1주", "1w", False),
            ("1개월", "1M", False),  # 1개월 타임프레임 지원 ✅
        ]

        return timeframes

    def is_api_only_timeframe(self, timeframe: str) -> bool:
        """API 전용 타임프레임인지 확인 (1w, 1M)"""
        api_only_timeframes = ["1d", "1w", "1M"]
        return timeframe in api_only_timeframes

    def requires_conversion(self, timeframe: str) -> bool:
        """타임프레임 변환이 필요한지 확인"""
        config = self.get_timeframe_configuration(timeframe)
        if not config:
            return False

        return config.conversion_required

    def get_base_timeframe(self, timeframe: str) -> Optional[str]:
        """변환 시 사용할 기준 타임프레임 반환"""
        config = self.get_timeframe_configuration(timeframe)
        if not config:
            return None

        return config.base_timeframe

    def get_hybrid_mode_info(self, timeframe: str) -> Dict[str, Any]:
        """하이브리드 모드 정보 반환"""
        config = self.get_timeframe_configuration(timeframe)
        if not config:
            return {"supported": False}

        websocket_supported = TimeframeSupport.SUPPORTED_TIMEFRAMES.get(timeframe, {}).get("websocket", False)
        api_supported = TimeframeSupport.SUPPORTED_TIMEFRAMES.get(timeframe, {}).get("api", False)

        return {
            "supported": True,
            "websocket_supported": websocket_supported,
            "api_supported": api_supported,
            "data_source": config.data_source,
            "polling_interval_ms": config.polling_interval_ms,
            "conversion_required": config.conversion_required,
            "base_timeframe": config.base_timeframe,
            "max_candles": config.max_candles
        }


# 편의 함수들
def create_timeframe_support_service(event_bus) -> TimeframeSupportService:
    """TimeframeSupportService 인스턴스 생성"""
    return TimeframeSupportService(event_bus)


def get_monthly_timeframe_info() -> Dict[str, Any]:
    """1개월 타임프레임 정보 반환"""
    return {
        "timeframe": "1M",
        "display_name": "1개월",
        "websocket_supported": False,
        "api_supported": True,
        "api_endpoint": "/v1/candles/months",
        "conversion_required": True,
        "base_timeframe": "1d",
        "polling_interval_hours": 6,
        "max_candles": 24,
        "description": "API 전용, 6시간마다 업데이트"
    }


def validate_timeframe_compatibility(timeframe: str, window_state: str) -> Dict[str, Any]:
    """타임프레임 호환성 검증"""
    is_supported = TimeframeSupport.is_timeframe_supported(timeframe)

    if not is_supported:
        return {
            "compatible": False,
            "reason": f"지원하지 않는 타임프레임: {timeframe}"
        }

    # 1개월 타임프레임 특별 처리
    if timeframe == "1M":
        return {
            "compatible": True,
            "data_source": "api",
            "websocket_supported": False,
            "api_supported": True,
            "special_handling": "월봉 전용 API 사용",
            "update_frequency": "6시간마다"
        }

    # 기타 타임프레임
    websocket_supported = TimeframeSupport.SUPPORTED_TIMEFRAMES.get(timeframe, {}).get("websocket", False)
    api_supported = TimeframeSupport.SUPPORTED_TIMEFRAMES.get(timeframe, {}).get("api", False)

    return {
        "compatible": True,
        "websocket_supported": websocket_supported,
        "api_supported": api_supported,
        "data_source": "websocket" if websocket_supported else "api",
        "hybrid_mode": websocket_supported and api_supported
    }


# 모듈 레벨 상수
MONTHLY_TIMEFRAME = "1M"
WEEKLY_TIMEFRAME = "1w"
API_ONLY_TIMEFRAMES = ["1d", "1w", "1M"]
WEBSOCKET_SUPPORTED_TIMEFRAMES = ["1m", "3m", "5m", "15m", "30m", "1h", "4h"]

logger.info("TimeframeSupportService 모듈 로드 완료 (1개월 타임프레임 지원)")
