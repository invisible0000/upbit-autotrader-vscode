"""
WebSocket 마켓 데이터 수집 서비스 (Infrastructure Layer)

실시간 호가창과 차트뷰를 위한 WebSocket 데이터 수집 및 이벤트 발행.
API 대역폭 절약을 위해 WebSocket 우선 활용.
"""

import asyncio
from typing import Optional, Set, List

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
    UpbitWebSocketQuotationClient,
    WebSocketDataType,
    WebSocketMessage
)
from upbit_auto_trading.infrastructure.events.bus.in_memory_event_bus import InMemoryEventBus
from upbit_auto_trading.domain.events.chart_viewer_events import (
    WebSocketOrderbookUpdateEvent,
    WebSocketTickerUpdateEvent
)


class WebSocketMarketDataService:
    """
    WebSocket 마켓 데이터 수집 서비스 (Infrastructure Layer)

    - 실시간 호가창 데이터 수집 및 이벤트 발행
    - 현재가(ticker) 데이터 수집 및 이벤트 발행
    - API 대역폭 절약을 위한 WebSocket 우선 정책
    - DDD 아키텍처 준수 (Infrastructure -> Domain Event -> Presentation)
    """

    def __init__(self, event_bus: InMemoryEventBus):
        """서비스 초기화"""
        self._logger = create_component_logger("WebSocketMarketDataService")
        self._event_bus = event_bus

        # WebSocket 클라이언트
        self._websocket_client: Optional[UpbitWebSocketQuotationClient] = None
        self._connection_task: Optional[asyncio.Task] = None

        # 구독 관리
        self._subscribed_symbols: Set[str] = set()
        self._orderbook_subscribers: Set[str] = set()
        self._ticker_subscribers: Set[str] = set()

        # 상태 관리
        self._is_running = False
        self._reconnect_count = 0
        self._max_reconnect_attempts = 10

    async def start_service(self) -> bool:
        """서비스 시작 (WebSocket 연결 및 메시지 리스닝 시작)"""
        if self._is_running:
            self._logger.warning("WebSocket 서비스가 이미 실행 중입니다")
            return True

        try:
            self._logger.info("WebSocket 마켓 데이터 서비스 시작...")

            # WebSocket 클라이언트 초기화
            self._websocket_client = UpbitWebSocketQuotationClient()

            # 연결 시도
            connected = await self._websocket_client.connect()
            if not connected:
                self._logger.error("WebSocket 연결 실패")
                return False

            # 메시지 리스닝 태스크 시작
            self._connection_task = asyncio.create_task(self._listen_messages())
            self._is_running = True

            self._logger.info("WebSocket 마켓 데이터 서비스 시작 완료")
            return True

        except Exception as e:
            self._logger.error(f"WebSocket 서비스 시작 실패: {e}")
            return False

    async def stop_service(self) -> None:
        """서비스 중지"""
        if not self._is_running:
            return

        self._logger.info("WebSocket 마켓 데이터 서비스 중지...")

        self._is_running = False

        # 연결 태스크 중지
        if self._connection_task and not self._connection_task.done():
            self._connection_task.cancel()
            try:
                await self._connection_task
            except asyncio.CancelledError:
                pass

        # WebSocket 연결 해제
        if self._websocket_client:
            await self._websocket_client.disconnect()
            self._websocket_client = None

        # 구독 상태 초기화
        self._subscribed_symbols.clear()
        self._orderbook_subscribers.clear()
        self._ticker_subscribers.clear()

        self._logger.info("WebSocket 마켓 데이터 서비스 중지 완료")

    async def subscribe_orderbook(self, symbol: str) -> bool:
        """호가창 데이터 구독"""
        if not self._websocket_client or not self._is_running:
            self._logger.warning(f"WebSocket 서비스가 실행되지 않음 - 호가창 구독 실패: {symbol}")
            return False

        try:
            # 이미 구독 중인지 확인
            if symbol in self._orderbook_subscribers:
                self._logger.debug(f"이미 호가창 구독 중: {symbol}")
                return True

            # WebSocket 구독
            success = await self._websocket_client.subscribe_orderbook([symbol])
            if success:
                self._orderbook_subscribers.add(symbol)
                self._subscribed_symbols.add(symbol)
                self._logger.info(f"호가창 구독 성공: {symbol}")
                return True
            else:
                self._logger.error(f"호가창 구독 실패: {symbol}")
                return False

        except Exception as e:
            self._logger.error(f"호가창 구독 오류 - {symbol}: {e}")
            return False

    async def subscribe_ticker(self, symbol: str) -> bool:
        """현재가 데이터 구독"""
        if not self._websocket_client or not self._is_running:
            self._logger.warning(f"WebSocket 서비스가 실행되지 않음 - 현재가 구독 실패: {symbol}")
            return False

        try:
            # 이미 구독 중인지 확인
            if symbol in self._ticker_subscribers:
                self._logger.debug(f"이미 현재가 구독 중: {symbol}")
                return True

            # WebSocket 구독
            success = await self._websocket_client.subscribe_ticker([symbol])
            if success:
                self._ticker_subscribers.add(symbol)
                self._subscribed_symbols.add(symbol)
                self._logger.info(f"현재가 구독 성공: {symbol}")
                return True
            else:
                self._logger.error(f"현재가 구독 실패: {symbol}")
                return False

        except Exception as e:
            self._logger.error(f"현재가 구독 오류 - {symbol}: {e}")
            return False

    async def unsubscribe_symbol(self, symbol: str) -> None:
        """심볼 구독 해제"""
        # TODO: WebSocket 클라이언트에 unsubscribe 메소드 추가 필요
        self._orderbook_subscribers.discard(symbol)
        self._ticker_subscribers.discard(symbol)

        # 다른 타입의 구독이 없으면 전체 구독에서 제거
        if symbol not in self._orderbook_subscribers and symbol not in self._ticker_subscribers:
            self._subscribed_symbols.discard(symbol)

        self._logger.info(f"심볼 구독 해제: {symbol}")

    def get_subscribed_symbols(self) -> List[str]:
        """현재 구독 중인 심볼 목록"""
        return list(self._subscribed_symbols)

    def is_running(self) -> bool:
        """서비스 실행 상태"""
        return self._is_running

    async def _listen_messages(self) -> None:
        """WebSocket 메시지 리스닝 (백그라운드 태스크)"""
        if not self._websocket_client:
            return

        try:
            self._logger.info("WebSocket 메시지 리스닝 시작...")

            async for message in self._websocket_client.listen():
                await self._process_message(message)

        except asyncio.CancelledError:
            self._logger.info("WebSocket 메시지 리스닝 중지됨")
        except Exception as e:
            self._logger.error(f"WebSocket 메시지 리스닝 오류: {e}")

            # 재연결 시도
            if self._is_running and self._reconnect_count < self._max_reconnect_attempts:
                self._reconnect_count += 1
                self._logger.info(f"WebSocket 재연결 시도 {self._reconnect_count}/{self._max_reconnect_attempts}")
                await asyncio.sleep(5.0)  # 5초 대기 후 재연결

                if self._websocket_client:
                    await self._websocket_client.disconnect()
                    connected = await self._websocket_client.connect()
                    if connected:
                        self._logger.info("WebSocket 재연결 성공")
                        self._reconnect_count = 0
                        # 기존 구독 재등록
                        await self._resubscribe_all()
                        # 메시지 리스닝 재시작
                        self._connection_task = asyncio.create_task(self._listen_messages())

    async def _process_message(self, message: WebSocketMessage) -> None:
        """WebSocket 메시지 처리 및 도메인 이벤트 발행"""
        try:
            if message.type == WebSocketDataType.ORDERBOOK:
                await self._process_orderbook_message(message)
            elif message.type == WebSocketDataType.TICKER:
                await self._process_ticker_message(message)
            else:
                self._logger.debug(f"처리하지 않는 메시지 타입: {message.type}")

        except Exception as e:
            self._logger.error(f"메시지 처리 오류 - {message.market}: {e}")

    async def _process_orderbook_message(self, message: WebSocketMessage) -> None:
        """호가창 메시지 처리"""
        data = message.data
        symbol = message.market

        # 스프레드 계산
        spread_percent = 0.0
        total_ask_size = 0.0
        total_bid_size = 0.0

        if 'orderbook_units' in data:
            units = data['orderbook_units']
            if units:
                # 최우선 호가로 스프레드 계산
                best_ask = float(units[0].get('ask_price', 0))
                best_bid = float(units[0].get('bid_price', 0))
                if best_ask > 0 and best_bid > 0:
                    spread_percent = ((best_ask - best_bid) / best_bid) * 100

                # 총 매도/매수 물량 계산
                total_ask_size = sum(float(unit.get('ask_size', 0)) for unit in units)
                total_bid_size = sum(float(unit.get('bid_size', 0)) for unit in units)

        # 시장 임팩트 분석 (간단한 버전)
        market_impact_analysis = {
            'liquidity_score': min(total_ask_size + total_bid_size, 100.0) / 100.0,
            'spread_impact': min(spread_percent, 1.0) / 1.0,
            'imbalance_ratio': total_bid_size / (total_ask_size + 1e-8) if total_ask_size > 0 else 1.0
        }

        # 도메인 이벤트 발행
        event = WebSocketOrderbookUpdateEvent(
            symbol=symbol,
            orderbook_data=data,
            spread_percent=spread_percent,
            total_ask_size=total_ask_size,
            total_bid_size=total_bid_size,
            market_impact_analysis=market_impact_analysis
        )

        await self._event_bus.publish(event)
        self._logger.debug(f"호가창 이벤트 발행: {symbol} (스프레드: {spread_percent:.3f}%)")

    async def _process_ticker_message(self, message: WebSocketMessage) -> None:
        """현재가 메시지 처리"""
        data = message.data
        symbol = message.market

        # 도메인 이벤트 발행
        event = WebSocketTickerUpdateEvent(
            symbol=symbol,
            current_price=float(data.get('trade_price', 0)),
            change_rate=float(data.get('signed_change_rate', 0)) * 100,  # 퍼센트로 변환
            volume_24h=float(data.get('acc_trade_volume_24h', 0)),
            high_price=float(data.get('high_price', 0)),
            low_price=float(data.get('low_price', 0)),
            prev_closing_price=float(data.get('prev_closing_price', 0))
        )

        await self._event_bus.publish(event)
        self._logger.debug(f"현재가 이벤트 발행: {symbol} ({event.current_price:,.0f}원)")

    async def _resubscribe_all(self) -> None:
        """재연결 시 모든 구독 재등록"""
        if not self._websocket_client:
            return

        # 호가창 구독 재등록
        if self._orderbook_subscribers:
            await self._websocket_client.subscribe_orderbook(list(self._orderbook_subscribers))
            self._logger.info(f"호가창 구독 재등록: {list(self._orderbook_subscribers)}")

        # 현재가 구독 재등록
        if self._ticker_subscribers:
            await self._websocket_client.subscribe_ticker(list(self._ticker_subscribers))
            self._logger.info(f"현재가 구독 재등록: {list(self._ticker_subscribers)}")
