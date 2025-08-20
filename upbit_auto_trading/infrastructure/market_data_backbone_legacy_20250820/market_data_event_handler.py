"""
마켓 데이터 이벤트 핸들러

기존 InMemoryEventBus 시스템을 활용하여 차트뷰어 전용 이벤트를 처리합니다.
기존 DomainEvent를 상속받은 차트뷰어 이벤트만 처리하며, 기존 시스템과 완전 격리됩니다.

주요 기능:
- 기존 이벤트 시스템 활용한 차트뷰어 이벤트 처리
- 우선순위 기반 이벤트 구독 (5, 8, 10)
- 기존 매매 우선순위(1-3)와 격리
- 1개월 타임프레임 포함 모든 이벤트 처리
"""

from typing import Dict, Any
from datetime import datetime

from upbit_auto_trading.domain.events.base_domain_event import DomainEvent
from upbit_auto_trading.domain.events.chart_viewer_events import (
    ChartViewerEvent, CandleDataEvent, OrderbookDataEvent,
    TechnicalIndicatorEvent, ChartLifecycleEvent, ChartSubscriptionEvent,
    ChartViewerPriority
)
from upbit_auto_trading.application.services.chart_market_data_service import ChartMarketDataService
from upbit_auto_trading.infrastructure.market_data_backbone.data_collector import MultiSourceDataCollector
from upbit_auto_trading.infrastructure.logging import create_component_logger


class MarketDataEventHandler:
    """
    마켓 데이터 이벤트 핸들러

    기존 InMemoryEventBus와 호환되는 차트뷰어 전용 이벤트 핸들러입니다.
    기존 시스템에 영향을 주지 않으면서 차트뷰어 이벤트만 처리합니다.
    """

    def __init__(self, event_bus=None, upbit_api_client=None, websocket_client=None):
        self.logger = create_component_logger("MarketDataEventHandler")

        # 기존 시스템과 호환 (의존성 주입)
        self._event_bus = event_bus

        # 차트뷰어 전용 서비스들
        self._market_data_service = ChartMarketDataService(
            event_bus=event_bus,
            upbit_api_client=upbit_api_client,
            websocket_client=websocket_client
        )
        self._data_collector = MultiSourceDataCollector()

        # 이벤트 구독 상태 (기존 시스템과 격리)
        self._subscription_ids: Dict[str, str] = {}
        self._is_registered = False

        # 처리 통계 (기존 시스템과 격리)
        self._event_stats = {
            'total_processed': 0,
            'candle_events': 0,
            'orderbook_events': 0,
            'lifecycle_events': 0,
            'subscription_events': 0,
            'indicator_events': 0,
            'errors': 0,
            'last_processed': None
        }

    async def register_with_event_bus(self) -> None:
        """기존 이벤트 버스에 차트뷰어 이벤트 핸들러 등록"""
        if self._is_registered or not self._event_bus:
            return

        try:
            # 차트뷰어 이벤트들을 기존 우선순위와 격리하여 구독

            # 캔들 데이터 이벤트 (우선순위 5: 활성화 차트)
            candle_subscription_id = self._event_bus.subscribe(
                event_type=CandleDataEvent,
                handler=self._handle_candle_data_event,
                is_async=True,
                priority=ChartViewerPriority.CHART_HIGH,  # 5 (기존 1-3과 격리)
                retry_count=2
            )
            self._subscription_ids['candle'] = candle_subscription_id

            # 호가창 데이터 이벤트 (우선순위 8: 백그라운드)
            orderbook_subscription_id = self._event_bus.subscribe(
                event_type=OrderbookDataEvent,
                handler=self._handle_orderbook_data_event,
                is_async=True,
                priority=ChartViewerPriority.CHART_BACKGROUND,  # 8
                retry_count=2
            )
            self._subscription_ids['orderbook'] = orderbook_subscription_id

            # 차트 생명주기 이벤트 (우선순위 5: 중요)
            lifecycle_subscription_id = self._event_bus.subscribe(
                event_type=ChartLifecycleEvent,
                handler=self._handle_lifecycle_event,
                is_async=True,
                priority=ChartViewerPriority.CHART_HIGH,  # 5
                retry_count=3
            )
            self._subscription_ids['lifecycle'] = lifecycle_subscription_id

            # 구독 관리 이벤트 (우선순위 5: 중요)
            subscription_subscription_id = self._event_bus.subscribe(
                event_type=ChartSubscriptionEvent,
                handler=self._handle_subscription_event,
                is_async=True,
                priority=ChartViewerPriority.CHART_HIGH,  # 5
                retry_count=3
            )
            self._subscription_ids['subscription'] = subscription_subscription_id

            # 기술적 지표 이벤트 (우선순위 10: 낮음)
            indicator_subscription_id = self._event_bus.subscribe(
                event_type=TechnicalIndicatorEvent,
                handler=self._handle_indicator_event,
                is_async=True,
                priority=ChartViewerPriority.CHART_LOW,  # 10
                retry_count=1
            )
            self._subscription_ids['indicator'] = indicator_subscription_id

            self._is_registered = True

            self.logger.info(
                f"차트뷰어 이벤트 핸들러 등록 완료 "
                f"(구독 {len(self._subscription_ids)}개, 우선순위 5/8/10 - 기존 1-3과 격리)"
            )

        except Exception as e:
            self.logger.error(f"이벤트 핸들러 등록 실패: {e}")
            raise

    async def _handle_candle_data_event(self, event: CandleDataEvent) -> None:
        """캔들 데이터 이벤트 처리 (기존 시스템과 격리)"""
        try:
            self.logger.debug(
                f"캔들 데이터 이벤트 처리: {event.symbol} {event.timeframe} "
                f"(우선순위: {event.priority_level}, 실시간: {event.is_realtime})"
            )

            # 이벤트 유효성 확인
            if not self._is_chart_viewer_event(event):
                self.logger.warning(f"차트뷰어 이벤트가 아님: {event.event_type}")
                return

            # 1개월 타임프레임 포함 처리
            if event.timeframe not in ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"]:
                self.logger.warning(f"지원하지 않는 타임프레임: {event.timeframe}")
                return

            # 캔들 데이터 검증
            candle_data = event.candle_data
            if not candle_data or not self._validate_candle_data(candle_data):
                self.logger.warning("유효하지 않은 캔들 데이터")
                return

            # 차트뷰어 전용 처리 로직
            await self._process_candle_data(event)

            # 통계 업데이트
            self._event_stats['candle_events'] += 1
            self._event_stats['total_processed'] += 1
            self._event_stats['last_processed'] = datetime.now()

        except Exception as e:
            self.logger.error(f"캔들 데이터 이벤트 처리 실패: {e}")
            self._event_stats['errors'] += 1

    async def _handle_orderbook_data_event(self, event: OrderbookDataEvent) -> None:
        """호가창 데이터 이벤트 처리 (기존 시스템과 격리)"""
        try:
            self.logger.debug(
                f"호가창 데이터 이벤트 처리: {event.symbol} "
                f"(우선순위: {event.priority_level})"
            )

            # 이벤트 유효성 확인
            if not self._is_chart_viewer_event(event):
                self.logger.warning(f"차트뷰어 이벤트가 아님: {event.event_type}")
                return

            # 호가창 데이터 검증
            if not event.bid_levels and not event.ask_levels:
                self.logger.warning("호가창 데이터가 비어있음")
                return

            # 차트뷰어 전용 처리 로직
            await self._process_orderbook_data(event)

            # 통계 업데이트
            self._event_stats['orderbook_events'] += 1
            self._event_stats['total_processed'] += 1
            self._event_stats['last_processed'] = datetime.now()

        except Exception as e:
            self.logger.error(f"호가창 데이터 이벤트 처리 실패: {e}")
            self._event_stats['errors'] += 1

    async def _handle_lifecycle_event(self, event: ChartLifecycleEvent) -> None:
        """차트 생명주기 이벤트 처리 (기존 시스템과 격리)"""
        try:
            self.logger.info(
                f"차트 생명주기 이벤트: {event.chart_id} {event.lifecycle_type} "
                f"(우선순위: {event.resource_priority})"
            )

            # 이벤트 유효성 확인
            if not self._is_chart_viewer_event(event):
                self.logger.warning(f"차트뷰어 이벤트가 아님: {event.event_type}")
                return

            # 생명주기별 처리
            if event.lifecycle_type in ["activated", "restored"]:
                await self._handle_chart_activation(event)
            elif event.lifecycle_type in ["deactivated", "minimized"]:
                await self._handle_chart_deactivation(event)
            elif event.lifecycle_type == "closed":
                await self._handle_chart_closure(event)

            # 통계 업데이트
            self._event_stats['lifecycle_events'] += 1
            self._event_stats['total_processed'] += 1
            self._event_stats['last_processed'] = datetime.now()

        except Exception as e:
            self.logger.error(f"생명주기 이벤트 처리 실패: {e}")
            self._event_stats['errors'] += 1

    async def _handle_subscription_event(self, event: ChartSubscriptionEvent) -> None:
        """구독 관리 이벤트 처리 (기존 시스템과 격리)"""
        try:
            self.logger.info(
                f"구독 이벤트: {event.subscription_type} "
                f"{event.symbol} {event.timeframe} (ID: {event.subscription_id})"
            )

            # 이벤트 유효성 확인
            if not self._is_chart_viewer_event(event):
                self.logger.warning(f"차트뷰어 이벤트가 아님: {event.event_type}")
                return

            # 구독 타입별 처리
            if event.subscription_type == "subscribe":
                await self._handle_data_subscription(event)
            elif event.subscription_type == "unsubscribe":
                await self._handle_data_unsubscription(event)
            elif event.subscription_type == "update":
                await self._handle_subscription_update(event)

            # 통계 업데이트
            self._event_stats['subscription_events'] += 1
            self._event_stats['total_processed'] += 1
            self._event_stats['last_processed'] = datetime.now()

        except Exception as e:
            self.logger.error(f"구독 이벤트 처리 실패: {e}")
            self._event_stats['errors'] += 1

    async def _handle_indicator_event(self, event: TechnicalIndicatorEvent) -> None:
        """기술적 지표 이벤트 처리 (기존 시스템과 격리)"""
        try:
            self.logger.debug(
                f"지표 이벤트: {event.symbol} {event.indicator_type} "
                f"(우선순위: {event.priority_level})"
            )

            # 이벤트 유효성 확인
            if not self._is_chart_viewer_event(event):
                self.logger.warning(f"차트뷰어 이벤트가 아님: {event.event_type}")
                return

            # 지표 데이터 처리
            await self._process_indicator_data(event)

            # 통계 업데이트
            self._event_stats['indicator_events'] += 1
            self._event_stats['total_processed'] += 1
            self._event_stats['last_processed'] = datetime.now()

        except Exception as e:
            self.logger.error(f"지표 이벤트 처리 실패: {e}")
            self._event_stats['errors'] += 1

    def _is_chart_viewer_event(self, event: DomainEvent) -> bool:
        """차트뷰어 이벤트인지 확인 (기존 시스템과 격리)"""
        if not isinstance(event, ChartViewerEvent):
            return False

        # 우선순위 범위 확인 (차트뷰어 전용 5, 8, 10)
        if hasattr(event, 'priority_level'):
            return ChartViewerPriority.is_chart_viewer_priority(event.priority_level)

        return True

    def _validate_candle_data(self, candle_data: Dict[str, Any]) -> bool:
        """캔들 데이터 유효성 검사"""
        required_fields = ['open', 'high', 'low', 'close', 'volume']

        for field in required_fields:
            if field not in candle_data:
                return False

            try:
                value = float(candle_data[field])
                if value < 0:
                    return False
            except (ValueError, TypeError):
                return False

        # OHLC 논리 확인
        try:
            o, h, l, c = (float(candle_data[f]) for f in ['open', 'high', 'low', 'close'])
            return l <= o <= h and l <= c <= h
        except (ValueError, TypeError):
            return False

    async def _process_candle_data(self, event: CandleDataEvent) -> None:
        """캔들 데이터 처리 (차트뷰어 전용)"""
        # 실제 차트 업데이트 로직은 Presentation 계층에서 처리
        # 여기서는 데이터 검증 및 전처리만 수행
        pass

    async def _process_orderbook_data(self, event: OrderbookDataEvent) -> None:
        """호가창 데이터 처리 (차트뷰어 전용)"""
        # 실제 호가창 업데이트 로직은 Presentation 계층에서 처리
        # 여기서는 데이터 검증 및 전처리만 수행
        pass

    async def _process_indicator_data(self, event: TechnicalIndicatorEvent) -> None:
        """기술적 지표 데이터 처리 (차트뷰어 전용)"""
        # 실제 지표 차트 업데이트 로직은 Presentation 계층에서 처리
        # 여기서는 데이터 검증 및 전처리만 수행
        pass

    async def _handle_chart_activation(self, event: ChartLifecycleEvent) -> None:
        """차트 활성화 처리 (리소스 우선순위 상승)"""
        self.logger.info(f"차트 활성화: {event.chart_id} (우선순위: {event.resource_priority})")
        # 실시간 데이터 수집 빈도 증가 등

    async def _handle_chart_deactivation(self, event: ChartLifecycleEvent) -> None:
        """차트 비활성화 처리 (리소스 절약 모드)"""
        self.logger.info(f"차트 비활성화: {event.chart_id} (우선순위: {event.resource_priority})")
        # 실시간 데이터 수집 빈도 감소 등

    async def _handle_chart_closure(self, event: ChartLifecycleEvent) -> None:
        """차트 종료 처리 (리소스 해제)"""
        self.logger.info(f"차트 종료: {event.chart_id}")
        # 관련 구독 해제, 메모리 정리 등

    async def _handle_data_subscription(self, event: ChartSubscriptionEvent) -> None:
        """데이터 구독 처리"""
        # MarketDataService를 통한 데이터 수집 시작
        pass

    async def _handle_data_unsubscription(self, event: ChartSubscriptionEvent) -> None:
        """데이터 구독 해제 처리"""
        # MarketDataService를 통한 데이터 수집 중지
        pass

    async def _handle_subscription_update(self, event: ChartSubscriptionEvent) -> None:
        """구독 업데이트 처리"""
        # 구독 설정 변경 처리
        pass

    def get_event_stats(self) -> Dict[str, Any]:
        """이벤트 처리 통계 조회 (기존 시스템과 격리)"""
        return {
            **self._event_stats,
            'subscription_count': len(self._subscription_ids),
            'is_registered': self._is_registered,
            'subscriptions': list(self._subscription_ids.keys())
        }

    async def unregister_from_event_bus(self) -> None:
        """이벤트 버스에서 등록 해제 (기존 시스템과 격리)"""
        if not self._is_registered or not self._event_bus:
            return

        try:
            # 모든 구독 해제
            for event_type, subscription_id in self._subscription_ids.items():
                success = self._event_bus.unsubscribe(subscription_id)
                if success:
                    self.logger.debug(f"구독 해제 완료: {event_type}")
                else:
                    self.logger.warning(f"구독 해제 실패: {event_type}")

            self._subscription_ids.clear()
            self._is_registered = False

            self.logger.info("차트뷰어 이벤트 핸들러 등록 해제 완료")

        except Exception as e:
            self.logger.error(f"이벤트 핸들러 등록 해제 실패: {e}")

    async def cleanup(self) -> None:
        """리소스 정리 (기존 시스템과 격리)"""
        self.logger.info("마켓 데이터 이벤트 핸들러 정리 중...")

        # 이벤트 버스 등록 해제
        await self.unregister_from_event_bus()

        # 서비스 정리
        if self._market_data_service:
            await self._market_data_service.cleanup()

        if self._data_collector:
            await self._data_collector.cleanup()

        # 통계 초기화
        self._event_stats = {
            'total_processed': 0,
            'candle_events': 0,
            'orderbook_events': 0,
            'lifecycle_events': 0,
            'subscription_events': 0,
            'indicator_events': 0,
            'errors': 0,
            'last_processed': None
        }

        self.logger.info("마켓 데이터 이벤트 핸들러 정리 완료")
