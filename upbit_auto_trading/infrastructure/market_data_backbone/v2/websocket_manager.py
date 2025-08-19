"""
MarketDataBackbone V2 - WebSocket Manager
실시간 데이터 스트림 관리 및 구독 시스템
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from decimal import Decimal

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
    UpbitWebSocketQuotationClient,
    WebSocketDataType,
    WebSocketMessage
)


@dataclass
class TickerData:
    """WebSocket용 간단한 티커 데이터"""
    symbol: str
    current_price: Decimal
    change_rate: Decimal
    change_price: Decimal
    volume_24h: Decimal
    timestamp: int
    source: str


class ChannelType(Enum):
    """WebSocket 채널 타입"""
    TICKER = "ticker"
    ORDERBOOK = "orderbook"
    TRADE = "trade"


@dataclass
class SubscriptionRequest:
    """구독 요청 정보"""
    symbols: List[str]
    channel_type: ChannelType
    callback_queue: asyncio.Queue
    subscription_id: str


class WebSocketManager:
    """
    WebSocket 연결 및 구독 관리 클래스
    - 기존 UpbitWebSocketQuotationClient 활용
    - 큐 기반 메시지 분배
    - 자동 재연결 및 구독 복원
    """

    def __init__(self):
        self.logger = create_component_logger("WebSocketManager")

        # WebSocket 클라이언트
        self._client: Optional[UpbitWebSocketQuotationClient] = None

        # 구독 관리
        self._subscriptions: Dict[str, SubscriptionRequest] = {}
        self._active_symbols: Set[str] = set()

        # 연결 상태
        self._is_connected = False
        self._is_listening = False
        self._listen_task: Optional[asyncio.Task] = None

        # 재연결 설정
        self._auto_reconnect = True
        self._reconnect_delay = 5.0
        self._max_reconnect_attempts = 10
        self._reconnect_attempts = 0

    async def connect(self) -> bool:
        """WebSocket 연결 설정"""
        try:
            self.logger.info("WebSocket 연결 시작...")

            # 기존 클라이언트 정리
            if self._client:
                await self._client.disconnect()

            # 새 클라이언트 생성 및 연결
            self._client = UpbitWebSocketQuotationClient()

            # 메시지 핸들러 등록 (동기 함수로 수정)
            self._client.add_message_handler(WebSocketDataType.TICKER, self._handle_ticker_message)
            self._client.add_message_handler(WebSocketDataType.ORDERBOOK, self._handle_orderbook_message)
            self._client.add_message_handler(WebSocketDataType.TRADE, self._handle_trade_message)

            # 연결 수행
            if await self._client.connect():
                self._is_connected = True
                self._reconnect_attempts = 0

                # 메시지 리스닝 시작
                self._listen_task = asyncio.create_task(self._listen_messages())

                self.logger.info("✅ WebSocket 연결 및 리스닝 시작 완료")
                return True
            else:
                self.logger.error("❌ WebSocket 클라이언트 연결 실패")
                return False

        except Exception as e:
            self.logger.error(f"❌ WebSocket 연결 중 오류: {e}")
            self._is_connected = False
            return False

    async def disconnect(self) -> None:
        """WebSocket 연결 해제"""
        try:
            self.logger.info("WebSocket 연결 해제 시작...")

            # 자동 재연결 비활성화
            self._auto_reconnect = False

            # 리스닝 중단
            self._is_listening = False
            if self._listen_task:
                self._listen_task.cancel()
                try:
                    await self._listen_task
                except asyncio.CancelledError:
                    pass
                self._listen_task = None

            # 클라이언트 연결 해제
            if self._client:
                await self._client.disconnect()
                self._client = None

            # 상태 초기화
            self._is_connected = False
            self._subscriptions.clear()
            self._active_symbols.clear()

            self.logger.info("✅ WebSocket 연결 해제 완료")

        except Exception as e:
            self.logger.error(f"❌ WebSocket 연결 해제 중 오류: {e}")

    async def subscribe_ticker(self, symbols: List[str]) -> asyncio.Queue:
        """티커 데이터 구독"""
        return await self._subscribe(symbols, ChannelType.TICKER)

    async def subscribe_orderbook(self, symbols: List[str]) -> asyncio.Queue:
        """호가 데이터 구독"""
        return await self._subscribe(symbols, ChannelType.ORDERBOOK)

    async def subscribe_trade(self, symbols: List[str]) -> asyncio.Queue:
        """체결 데이터 구독"""
        return await self._subscribe(symbols, ChannelType.TRADE)

    async def _subscribe(self, symbols: List[str], channel_type: ChannelType) -> asyncio.Queue:
        """내부 구독 메서드"""
        try:
            # 연결 확인 및 재연결
            if not self._is_connected:
                if not await self.connect():
                    raise RuntimeError("WebSocket 연결 실패")

            # 구독 ID 생성
            subscription_id = f"{channel_type.value}_{uuid.uuid4().hex[:8]}"

            # 메시지 큐 생성
            message_queue = asyncio.Queue(maxsize=1000)  # 큐 크기 제한

            # 구독 요청 객체 생성
            request = SubscriptionRequest(
                symbols=symbols,
                channel_type=channel_type,
                callback_queue=message_queue,
                subscription_id=subscription_id
            )

            # 구독 정보 저장
            self._subscriptions[subscription_id] = request

            # 새로운 심볼만 구독 (기존 구독 중복 방지)
            new_symbols = [s for s in symbols if s not in self._active_symbols]
            if new_symbols:
                # 실제 WebSocket 구독 수행
                success = False
                if channel_type == ChannelType.TICKER:
                    success = await self._client.subscribe_ticker(new_symbols)
                elif channel_type == ChannelType.ORDERBOOK:
                    success = await self._client.subscribe_orderbook(new_symbols)
                elif channel_type == ChannelType.TRADE:
                    success = await self._client.subscribe_trade(new_symbols)

                if success:
                    self._active_symbols.update(new_symbols)
                    self.logger.info(f"✅ {channel_type.value} 구독 완료: {new_symbols}")
                else:
                    # 구독 실패 시 정리
                    del self._subscriptions[subscription_id]
                    raise RuntimeError(f"{channel_type.value} 구독 실패")
            else:
                self.logger.debug(f"모든 심볼이 이미 구독됨: {symbols}")

            return message_queue

        except Exception as e:
            self.logger.error(f"❌ 구독 실패 ({channel_type.value}): {e}")
            raise

    async def unsubscribe(self, subscription_id: str) -> None:
        """구독 해제"""
        try:
            if subscription_id in self._subscriptions:
                request = self._subscriptions[subscription_id]
                del self._subscriptions[subscription_id]

                # 더 이상 사용되지 않는 심볼 찾기
                still_used_symbols = set()
                for sub in self._subscriptions.values():
                    still_used_symbols.update(sub.symbols)

                # 사용되지 않는 심볼 제거
                unused_symbols = set(request.symbols) - still_used_symbols
                for symbol in unused_symbols:
                    self._active_symbols.discard(symbol)

                # 큐 정리 (남은 메시지 처리)
                try:
                    while not request.callback_queue.empty():
                        request.callback_queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass

                self.logger.info(f"✅ 구독 해제 완료: {subscription_id}")
            else:
                self.logger.warning(f"존재하지 않는 구독 ID: {subscription_id}")

        except Exception as e:
            self.logger.error(f"❌ 구독 해제 오류: {e}")

    async def _listen_messages(self) -> None:
        """메시지 리스닝 루프"""
        try:
            self._is_listening = True
            self.logger.info("WebSocket 메시지 리스닝 시작")

            if not self._client:
                raise RuntimeError("WebSocket 클라이언트가 없음")

            async for message in self._client.listen():
                if not self._is_listening:
                    break

                # 메시지 처리는 핸들러에서 자동으로 수행됨
                # (클라이언트가 핸들러를 호출함)

        except Exception as e:
            self.logger.error(f"❌ 메시지 리스닝 오류: {e}")

            # 재연결 시도
            if self._auto_reconnect and self._reconnect_attempts < self._max_reconnect_attempts:
                await self._attempt_reconnect()
        finally:
            self._is_listening = False

    def _handle_ticker_message(self, message: WebSocketMessage) -> None:
        """티커 메시지 처리 (동기 함수)"""
        try:
            # WebSocket 메시지를 TickerData로 변환
            ticker_data = self._convert_websocket_ticker(message.data)

            # 해당 심볼을 구독하는 모든 티커 큐에 전송
            asyncio.create_task(self._distribute_message(ticker_data.symbol, ChannelType.TICKER, ticker_data))

        except Exception as e:
            self.logger.error(f"❌ 티커 메시지 처리 오류: {e}")

    def _handle_orderbook_message(self, message: WebSocketMessage) -> None:
        """호가 메시지 처리 (동기 함수)"""
        try:
            # WebSocket 메시지를 Dict로 처리
            orderbook_data = self._convert_websocket_orderbook(message.data)

            # 해당 심볼을 구독하는 모든 호가 큐에 전송
            asyncio.create_task(self._distribute_message(orderbook_data['symbol'], ChannelType.ORDERBOOK, orderbook_data))

        except Exception as e:
            self.logger.error(f"❌ 호가 메시지 처리 오류: {e}")

    def _handle_trade_message(self, message: WebSocketMessage) -> None:
        """체결 메시지 처리 (동기 함수)"""
        try:
            # WebSocket 메시지 처리 (향후 구현)
            symbol = message.data.get('code', message.data.get('market', 'UNKNOWN'))
            asyncio.create_task(self._distribute_message(symbol, ChannelType.TRADE, message.data))

        except Exception as e:
            self.logger.error(f"❌ 체결 메시지 처리 오류: {e}")

    async def _distribute_message(self, symbol: str, channel_type: ChannelType, data: Any) -> None:
        """메시지를 해당하는 모든 구독자에게 분배"""
        distributed_count = 0

        for subscription in self._subscriptions.values():
            if (subscription.channel_type == channel_type and
                    symbol in subscription.symbols):
                try:
                    # 큐가 가득 찬 경우 가장 오래된 메시지 제거
                    if subscription.callback_queue.full():
                        try:
                            subscription.callback_queue.get_nowait()
                        except asyncio.QueueEmpty:
                            pass

                    # 새 메시지 추가
                    subscription.callback_queue.put_nowait(data)
                    distributed_count += 1

                except asyncio.QueueFull:
                    self.logger.warning(f"큐 오버플로우: {subscription.subscription_id}")
                except Exception as e:
                    self.logger.error(f"메시지 분배 오류: {e}")

        if distributed_count > 0:
            self.logger.debug(f"메시지 분배 완료: {symbol} ({channel_type.value}) -> {distributed_count}개 구독자")

    def _convert_websocket_ticker(self, raw_data: Dict[str, Any]) -> TickerData:
        """WebSocket 티커 데이터를 TickerData로 변환"""
        try:
            return TickerData(
                symbol=raw_data.get('code', raw_data.get('market', '')),
                current_price=Decimal(str(raw_data.get('trade_price', 0))),
                change_rate=Decimal(str(raw_data.get('signed_change_rate', 0))),
                change_price=Decimal(str(raw_data.get('signed_change_price', 0))),
                volume_24h=Decimal(str(raw_data.get('acc_trade_volume_24h', 0))),
                timestamp=raw_data.get('timestamp', int(datetime.now().timestamp() * 1000)),
                source="websocket"
            )
        except Exception as e:
            self.logger.error(f"❌ 티커 데이터 변환 오류: {e}")
            raise

    def _convert_websocket_orderbook(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """WebSocket 호가 데이터를 Dict로 변환"""
        try:
            return {
                'symbol': raw_data.get('code', raw_data.get('market', '')),
                'orderbook_units': raw_data.get('orderbook_units', []),
                'timestamp': raw_data.get('timestamp', int(datetime.now().timestamp() * 1000)),
                'source': 'websocket'
            }
        except Exception as e:
            self.logger.error(f"❌ 호가 데이터 변환 오류: {e}")
            raise

    async def _attempt_reconnect(self) -> bool:
        """자동 재연결 시도"""
        if not self._auto_reconnect or self._reconnect_attempts >= self._max_reconnect_attempts:
            self.logger.warning("재연결 한계 도달 또는 비활성화됨")
            return False

        self._reconnect_attempts += 1
        self.logger.info(f"재연결 시도 {self._reconnect_attempts}/{self._max_reconnect_attempts}")

        await asyncio.sleep(self._reconnect_delay)

        # 기존 구독 정보 백업
        old_subscriptions = dict(self._subscriptions)

        try:
            # 재연결 시도
            if await self.connect():
                # 기존 구독 복원
                for subscription in old_subscriptions.values():
                    try:
                        if subscription.channel_type == ChannelType.TICKER:
                            await self._client.subscribe_ticker(subscription.symbols)
                        elif subscription.channel_type == ChannelType.ORDERBOOK:
                            await self._client.subscribe_orderbook(subscription.symbols)
                        elif subscription.channel_type == ChannelType.TRADE:
                            await self._client.subscribe_trade(subscription.symbols)

                        # 구독 정보 복원
                        self._subscriptions[subscription.subscription_id] = subscription
                        self._active_symbols.update(subscription.symbols)

                    except Exception as e:
                        self.logger.error(f"구독 복원 실패: {subscription.subscription_id} - {e}")

                self.logger.info("✅ 재연결 및 구독 복원 완료")
                return True
            else:
                self.logger.error("재연결 실패")
                return False

        except Exception as e:
            self.logger.error(f"재연결 중 오류: {e}")
            return False

    async def get_connection_status(self) -> Dict[str, Any]:
        """연결 상태 및 통계 반환"""
        return {
            'is_connected': self._is_connected,
            'is_listening': self._is_listening,
            'active_subscriptions': len(self._subscriptions),
            'active_symbols': len(self._active_symbols),
            'reconnect_attempts': self._reconnect_attempts,
            'max_reconnect_attempts': self._max_reconnect_attempts,
            'subscriptions': {
                sub_id: {
                    'symbols': sub.symbols,
                    'channel_type': sub.channel_type.value,
                    'queue_size': sub.callback_queue.qsize()
                }
                for sub_id, sub in self._subscriptions.items()
            }
        }

    async def __aenter__(self):
        """async with 컨텍스트 매니저 진입"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async with 컨텍스트 매니저 종료"""
        await self.disconnect()
