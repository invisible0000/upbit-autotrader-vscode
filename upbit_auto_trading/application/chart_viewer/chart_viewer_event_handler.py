"""
차트뷰어 전용 이벤트 핸들러

기존 InMemoryEventBus를 활용하여 차트뷰어 이벤트를 안전하게 처리합니다.
기존 매매 시스템과 완전히 격리되어 영향을 주지 않습니다.
"""

from typing import Dict, Any
from upbit_auto_trading.domain.events.chart_viewer_events import (
    ChartViewerEvent, CandleDataEvent, OrderbookDataEvent,
    TechnicalIndicatorEvent, ChartLifecycleEvent, ChartSubscriptionEvent,
    ChartViewerPriority
)
from upbit_auto_trading.infrastructure.events.bus.event_bus_interface import IEventBus
from upbit_auto_trading.infrastructure.logging import create_component_logger


class ChartViewerEventHandler:
    """
    차트뷰어 전용 이벤트 핸들러

    기존 InMemoryEventBus를 활용하여 차트뷰어 이벤트를 처리합니다.
    기존 시스템과 완전 격리되어 영향을 주지 않습니다.
    """

    def __init__(self, event_bus: IEventBus):
        self._event_bus = event_bus
        self._logger = create_component_logger("ChartViewerEventHandler")
        self._subscription_ids: Dict[str, str] = {}
        self._active_charts: Dict[str, bool] = {}

        # 기존 시스템과 격리된 초기화
        self._setup_chart_viewer_subscriptions()
        self._logger.info("차트뷰어 이벤트 핸들러 초기화됨 (기존 시스템과 격리)")

    def _setup_chart_viewer_subscriptions(self) -> None:
        """차트뷰어 전용 이벤트 구독 설정 (기존 시스템과 격리)"""
        try:
            # 캔들 데이터 이벤트 구독 (우선순위 5)
            candle_subscription_id = self._event_bus.subscribe(
                event_type=CandleDataEvent,
                handler=self._handle_candle_data_event,
                is_async=True,
                priority=ChartViewerPriority.CHART_HIGH,  # 5
                retry_count=3
            )
            self._subscription_ids['candle_data'] = candle_subscription_id

            # 호가창 데이터 이벤트 구독 (우선순위 5)
            orderbook_subscription_id = self._event_bus.subscribe(
                event_type=OrderbookDataEvent,
                handler=self._handle_orderbook_data_event,
                is_async=True,
                priority=ChartViewerPriority.CHART_HIGH,  # 5
                retry_count=3
            )
            self._subscription_ids['orderbook_data'] = orderbook_subscription_id

            # 기술적 지표 이벤트 구독 (우선순위 8)
            indicator_subscription_id = self._event_bus.subscribe(
                event_type=TechnicalIndicatorEvent,
                handler=self._handle_technical_indicator_event,
                is_async=True,
                priority=ChartViewerPriority.CHART_BACKGROUND,  # 8
                retry_count=2
            )
            self._subscription_ids['technical_indicator'] = indicator_subscription_id

            # 생명주기 이벤트 구독 (우선순위 5)
            lifecycle_subscription_id = self._event_bus.subscribe(
                event_type=ChartLifecycleEvent,
                handler=self._handle_lifecycle_event,
                is_async=True,
                priority=ChartViewerPriority.CHART_HIGH,  # 5
                retry_count=2
            )
            self._subscription_ids['lifecycle'] = lifecycle_subscription_id

            # 구독 관리 이벤트 구독 (우선순위 8)
            subscription_subscription_id = self._event_bus.subscribe(
                event_type=ChartSubscriptionEvent,
                handler=self._handle_subscription_event,
                is_async=True,
                priority=ChartViewerPriority.CHART_BACKGROUND,  # 8
                retry_count=2
            )
            self._subscription_ids['subscription'] = subscription_subscription_id

            self._logger.info(
                f"차트뷰어 이벤트 구독 설정 완료: {len(self._subscription_ids)}개 "
                f"(우선순위 {ChartViewerPriority.CHART_HIGH}, {ChartViewerPriority.CHART_BACKGROUND})"
            )

        except Exception as e:
            self._logger.error(f"차트뷰어 이벤트 구독 설정 실패: {e}")
            raise

    async def _handle_candle_data_event(self, event: CandleDataEvent) -> None:
        """캔들 데이터 이벤트 처리 (기존 시스템과 격리)"""
        try:
            chart_id = event.chart_id
            symbol = event.symbol
            timeframe = event.timeframe

            # 차트가 활성 상태인지 확인
            if not self._is_chart_active(chart_id):
                self._logger.debug(f"비활성 차트 캔들 데이터 무시: {chart_id}")
                return

            # 캔들 데이터 처리 로직 (차트뷰어 전용)
            self._logger.debug(
                f"캔들 데이터 처리: {symbol} {timeframe} "
                f"(실시간: {event.is_realtime}, 소스: {event.data_source})"
            )

            # 여기서 실제 차트 업데이트 로직 호출
            # (후속 Phase에서 구현)

        except Exception as e:
            self._logger.error(f"캔들 데이터 이벤트 처리 실패: {e}")
            # 기존 시스템에 영향을 주지 않도록 예외를 삼키지 않고 로깅만

    async def _handle_orderbook_data_event(self, event: OrderbookDataEvent) -> None:
        """호가창 데이터 이벤트 처리 (기존 시스템과 격리)"""
        try:
            chart_id = event.chart_id
            symbol = event.symbol

            # 차트가 활성 상태인지 확인
            if not self._is_chart_active(chart_id):
                self._logger.debug(f"비활성 차트 호가 데이터 무시: {chart_id}")
                return

            # 호가창 데이터 처리 로직 (차트뷰어 전용)
            bid_count = len(event.bid_levels)
            ask_count = len(event.ask_levels)
            self._logger.debug(
                f"호가창 데이터 처리: {symbol} "
                f"(매수 {bid_count}개, 매도 {ask_count}개)"
            )

            # 여기서 실제 호가창 업데이트 로직 호출
            # (후속 Phase에서 구현)

        except Exception as e:
            self._logger.error(f"호가창 데이터 이벤트 처리 실패: {e}")

    async def _handle_technical_indicator_event(self, event: TechnicalIndicatorEvent) -> None:
        """기술적 지표 이벤트 처리 (기존 시스템과 격리)"""
        try:
            chart_id = event.chart_id
            symbol = event.symbol
            indicator_type = event.indicator_type

            # 차트가 활성 상태인지 확인
            if not self._is_chart_active(chart_id):
                self._logger.debug(f"비활성 차트 지표 데이터 무시: {chart_id}")
                return

            # 기술적 지표 처리 로직 (차트뷰어 전용)
            self._logger.debug(
                f"기술적 지표 처리: {symbol} {indicator_type} "
                f"(파라미터: {event.parameters})"
            )

            # 여기서 실제 지표 차트 업데이트 로직 호출
            # (후속 Phase에서 구현)

        except Exception as e:
            self._logger.error(f"기술적 지표 이벤트 처리 실패: {e}")

    async def _handle_lifecycle_event(self, event: ChartLifecycleEvent) -> None:
        """생명주기 이벤트 처리 (기존 시스템과 격리)"""
        try:
            chart_id = event.chart_id
            lifecycle_type = event.lifecycle_type
            resource_priority = event.resource_priority

            # 차트 상태 업데이트
            if lifecycle_type == "activated":
                self._active_charts[chart_id] = True
                self._logger.info(f"차트 활성화: {chart_id} (우선순위: {resource_priority})")
            elif lifecycle_type in ["deactivated", "minimized"]:
                self._active_charts[chart_id] = False
                self._logger.info(f"차트 비활성화: {chart_id} (우선순위: {resource_priority})")
            elif lifecycle_type == "restored":
                self._active_charts[chart_id] = True
                self._logger.info(f"차트 복원: {chart_id} (우선순위: {resource_priority})")
            elif lifecycle_type == "closed":
                self._active_charts.pop(chart_id, None)
                self._logger.info(f"차트 종료: {chart_id}")

            # 기존 시스템과 격리된 리소스 관리
            self._adjust_chart_resources(chart_id, lifecycle_type, resource_priority)

        except Exception as e:
            self._logger.error(f"생명주기 이벤트 처리 실패: {e}")

    async def _handle_subscription_event(self, event: ChartSubscriptionEvent) -> None:
        """구독 관리 이벤트 처리 (기존 시스템과 격리)"""
        try:
            chart_id = event.chart_id
            subscription_type = event.subscription_type
            subscription_id = event.subscription_id

            if subscription_type == "subscribe":
                self._logger.info(f"차트 구독 시작: {chart_id} ({subscription_id})")
            elif subscription_type == "unsubscribe":
                self._logger.info(f"차트 구독 해제: {chart_id} ({subscription_id})")
            elif subscription_type == "update":
                self._logger.debug(f"차트 구독 업데이트: {chart_id} ({subscription_id})")

            # 여기서 실제 구독 관리 로직 호출
            # (후속 Phase에서 구현)

        except Exception as e:
            self._logger.error(f"구독 관리 이벤트 처리 실패: {e}")

    def _is_chart_active(self, chart_id: str) -> bool:
        """차트 활성 상태 확인 (기존 시스템과 무관)"""
        return self._active_charts.get(chart_id, False)

    def _adjust_chart_resources(self, chart_id: str, lifecycle_type: str,
                               resource_priority: int) -> None:
        """차트 리소스 조정 (기존 시스템과 격리)"""
        try:
            # 기존 시스템에 영향을 주지 않는 리소스 관리
            if lifecycle_type == "activated":
                self._logger.debug(f"차트 리소스 증가: {chart_id} (우선순위: {resource_priority})")
            elif lifecycle_type in ["deactivated", "minimized"]:
                self._logger.debug(f"차트 리소스 감소: {chart_id} (우선순위: {resource_priority})")

            # 실제 리소스 조정 로직은 후속 Phase에서 구현

        except Exception as e:
            self._logger.error(f"차트 리소스 조정 실패: {e}")

    async def publish_chart_event(self, event: ChartViewerEvent) -> None:
        """차트뷰어 이벤트 발행 (기존 시스템 활용)"""
        try:
            await self._event_bus.publish(event)
            self._logger.debug(f"차트뷰어 이벤트 발행: {event.event_type}")
        except Exception as e:
            self._logger.error(f"차트뷰어 이벤트 발행 실패: {e}")
            raise

    def cleanup(self) -> None:
        """리소스 정리 (기존 시스템과 격리)"""
        try:
            # 구독 해제
            for subscription_type, subscription_id in self._subscription_ids.items():
                self._event_bus.unsubscribe(subscription_id)
                self._logger.debug(f"차트뷰어 구독 해제: {subscription_type}")

            # 상태 초기화
            self._subscription_ids.clear()
            self._active_charts.clear()

            self._logger.info("차트뷰어 이벤트 핸들러 정리 완료")

        except Exception as e:
            self._logger.error(f"차트뷰어 이벤트 핸들러 정리 실패: {e}")

    def get_handler_statistics(self) -> Dict[str, Any]:
        """핸들러 통계 조회 (기존 시스템과 무관)"""
        return {
            'subscription_count': len(self._subscription_ids),
            'active_charts_count': len([chart_id for chart_id, active in self._active_charts.items() if active]),
            'total_charts_count': len(self._active_charts),
            'subscriptions': list(self._subscription_ids.keys()),
            'active_charts': [chart_id for chart_id, active in self._active_charts.items() if active]
        }
