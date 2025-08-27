"""
업비트 WebSocket v5.0 - Public 클라이언트 (새 버전)

🎯 특징:
- Public 데이터 전용 (ticker, trade, orderbook, candle)
- 최대 3개 티켓 제한
- 효율적인 티켓 재사용
- 명시적 상태 관리
- 타입 안전성 (Pydantic)
- Infrastructure 로깅 시스템
- 자동 복구 시스템
"""

import asyncio
import json
import uuid
import websockets
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .models import SubscriptionRequest, DataType
from .subscription_manager import SubscriptionManager
from .message_buffer import MessageBuffer, MessagePriority, get_global_message_buffer
from .exceptions import SubscriptionError
from .models import (
    TickerData, TradeData, OrderbookData, CandleData, ConnectionStatus,
    SubscriptionRequest, DataType
)
from .subscription_manager import SubscriptionManager
from .config import load_config
from .state import WebSocketState, WebSocketStateMachine
from .exceptions import (
    WebSocketError, WebSocketConnectionError, WebSocketConnectionTimeoutError,
    SubscriptionError, MessageParsingError, TooManySubscriptionsError,
    ErrorCode
)

logger = create_component_logger("UpbitWebSocketPublicV5")


class TicketManager:
    """티켓 관리자 - 효율적인 티켓 재사용"""

    def __init__(self, max_tickets: int = 3):
        self.max_tickets = max_tickets
        self.tickets: Dict[str, Dict[str, Any]] = {}  # ticket_id -> ticket_info
        self.data_type_mapping: Dict[str, str] = {}  # data_type -> ticket_id

        logger.info(f"티켓 매니저 초기화 완료 - 최대 {max_tickets}개 티켓")

    def get_or_create_ticket(self, data_type: str, symbols: List[str]) -> str:
        """데이터 타입에 대한 티켓 획득 또는 생성"""
        # 기존 티켓이 있으면 재사용
        if data_type in self.data_type_mapping:
            ticket_id = self.data_type_mapping[data_type]
            logger.debug(f"기존 티켓 재사용: {ticket_id} for {data_type}")
            return ticket_id

        # 새 티켓 생성
        if len(self.tickets) >= self.max_tickets:
            raise TooManySubscriptionsError(len(self.tickets), self.max_tickets)

        # 새 티켓 생성
        ticket_id = f"public-{uuid.uuid4().hex[:8]}"
        self.tickets[ticket_id] = {
            'data_types': {data_type},
            'symbols': set(symbols),
            'created_at': datetime.now()
        }
        self.data_type_mapping[data_type] = ticket_id

        logger.info(f"새 티켓 생성: {ticket_id} for {data_type} with {len(symbols)} symbols")
        return ticket_id

    def remove_data_type(self, data_type: str) -> Optional[str]:
        """데이터 타입 제거"""
        if data_type not in self.data_type_mapping:
            logger.warning(f"데이터 타입 {data_type}을 찾을 수 없습니다")
            return None

        ticket_id = self.data_type_mapping[data_type]
        self.tickets[ticket_id]['data_types'].discard(data_type)
        del self.data_type_mapping[data_type]

        # 티켓이 비어있으면 제거
        if not self.tickets[ticket_id]['data_types']:
            del self.tickets[ticket_id]
            logger.info(f"빈 티켓 제거: {ticket_id}")

        return ticket_id

    def get_ticket_message(self, ticket_id: str) -> List[Dict[str, Any]]:
        """티켓의 구독 메시지 생성"""
        if ticket_id not in self.tickets:
            raise ValueError(f"티켓을 찾을 수 없습니다: {ticket_id}")

        ticket_info = self.tickets[ticket_id]
        message = [{"ticket": ticket_id}]

        for data_type in ticket_info['data_types']:
            if data_type in ["ticker", "trade", "orderbook"]:
                message.append({
                    "type": data_type,
                    "codes": list(ticket_info['symbols'])
                })
            elif data_type.startswith("candle"):
                message.append({
                    "type": data_type,
                    "codes": list(ticket_info['symbols'])
                })

        message.append({"format": "DEFAULT"})
        return message

    def get_stats(self) -> Dict[str, Any]:
        """티켓 사용 통계"""
        return {
            "total_tickets": len(self.tickets),
            "max_tickets": self.max_tickets,
            "ticket_efficiency": (self.max_tickets - len(self.tickets)) / self.max_tickets * 100,
            "tickets": {
                tid: {
                    "data_types": list(info['data_types']),
                    "symbol_count": len(info['symbols']),
                    "created_at": info['created_at'].isoformat()
                }
                for tid, info in self.tickets.items()
            }
        }


class UpbitWebSocketPublicV5:
    """업비트 WebSocket v5.0 Public 클라이언트"""

    def __init__(self, config_path: Optional[str] = None,
                 event_broker: Optional[Any] = None,
                 max_tickets: int = 3):
        """
        Args:
            config_path: 설정 파일 경로
            event_broker: 외부 이벤트 브로커
            max_tickets: 최대 티켓 수 (업비트 권장: 3개)
        """
        # 설정 로드
        self.config = load_config(config_path)

        # 상태 관리
        self.state_machine = WebSocketStateMachine()

        # 연결 관리
        self.websocket: Optional[Any] = None
        self.connection_id = str(uuid.uuid4())

        # 티켓 관리
        self.ticket_manager = TicketManager(max_tickets)

        # 메시지 버퍼 시스템 (중복 필터링 및 순서 보장)
        self.message_buffer: Optional[MessageBuffer] = None

        # 구독 관리
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
        self.callbacks: Dict[str, Callable] = {}

        # 이벤트 시스템
        self.event_broker = event_broker

        # 통계
        self.stats = {
            'messages_received': 0,
            'messages_processed': 0,
            'errors': 0,
            'reconnect_count': 0,
            'start_time': datetime.now()
        }

        # 백그라운드 태스크
        self._tasks: Set[asyncio.Task] = set()

        logger.info(f"Public WebSocket 클라이언트 초기화 완료 - ID: {self.connection_id}")

    async def connect(self) -> None:
        """WebSocket 연결"""
        if self.state_machine.current_state != WebSocketState.DISCONNECTED:
            logger.warning(f"이미 연결된 상태입니다: {self.state_machine.current_state}")
            return

        try:
            self.state_machine.transition_to(WebSocketState.CONNECTING)
            logger.info(f"WebSocket 연결 시도: {self.config.connection.url}")

            # WebSocket 연결
            self.websocket = await asyncio.wait_for(
                websockets.connect(
                    self.config.connection.url,
                    ping_interval=self.config.connection.ping_interval,
                    ping_timeout=self.config.connection.ping_timeout,
                    close_timeout=self.config.connection.close_timeout
                ),
                timeout=self.config.connection.connect_timeout
            )

            self.state_machine.transition_to(WebSocketState.CONNECTED)
            logger.info("WebSocket 연결 완료")

            # 메시지 버퍼 시스템 초기화
            self.message_buffer = await get_global_message_buffer()
            await self._setup_message_handlers()

            # 백그라운드 태스크 시작
            self._start_background_tasks()

            # 이벤트 발송
            await self._emit_event("websocket.connected", {
                "connection_id": self.connection_id,
                "timestamp": datetime.now().isoformat()
            })

        except asyncio.TimeoutError:
            error = WebSocketConnectionTimeoutError(
                self.config.connection.connect_timeout,
                self.config.connection.url
            )
            await self._handle_error(error)
            raise error

        except Exception as e:
            error = WebSocketConnectionError(
                f"WebSocket 연결 실패: {str(e)}",
                self.config.connection.url,
                e
            )
            await self._handle_error(error)
            raise error

    async def disconnect(self) -> None:
        """WebSocket 연결 해제"""
        if self.state_machine.current_state == WebSocketState.DISCONNECTED:
            logger.info("이미 연결 해제된 상태입니다")
            return

        try:
            self.state_machine.transition_to(WebSocketState.DISCONNECTING)
            logger.info("WebSocket 연결 해제 시작")

            # 백그라운드 태스크 정리
            await self._cleanup_tasks()

            # WebSocket 연결 종료
            if self.websocket:
                await self.websocket.close()
                self.websocket = None

            self.state_machine.transition_to(WebSocketState.DISCONNECTED)
            logger.info("WebSocket 연결 해제 완료")

            # 이벤트 발송
            await self._emit_event("websocket.disconnected", {
                "connection_id": self.connection_id,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"연결 해제 중 오류: {e}")
            self.state_machine.transition_to(WebSocketState.ERROR)

    async def subscribe(self, data_type: str, symbols: List[str],
                       callback: Optional[Callable] = None) -> str:
        """데이터 구독"""
        if not self.is_connected():
            raise SubscriptionError("WebSocket이 연결되지 않았습니다", data_type, symbols)

        try:
            self.state_machine.transition_to(WebSocketState.SUBSCRIBING)

            # 티켓 생성/획득
            ticket_id = self.ticket_manager.get_or_create_ticket(data_type, symbols)

            # 구독 메시지 생성
            subscribe_message = self.ticket_manager.get_ticket_message(ticket_id)

            # 구독 요청 전송
            if self.websocket:
                await self.websocket.send(json.dumps(subscribe_message))

            # 구독 정보 저장
            subscription_id = f"{data_type}-{uuid.uuid4().hex[:8]}"
            self.subscriptions[subscription_id] = {
                'data_type': data_type,
                'symbols': symbols,
                'ticket_id': ticket_id,
                'created_at': datetime.now(),
                'message_count': 0
            }

            # 콜백 등록
            if callback:
                self.callbacks[subscription_id] = callback

            logger.info(f"구독 완료: {data_type} for {len(symbols)} symbols")

            self.state_machine.transition_to(WebSocketState.ACTIVE)

            # 이벤트 발송
            await self._emit_event("websocket.subscribed", {
                "subscription_id": subscription_id,
                "data_type": data_type,
                "symbols": symbols,
                "ticket_id": ticket_id
            })

            return subscription_id

        except Exception as e:
            error = SubscriptionError(f"구독 실패: {str(e)}", data_type, symbols)
            await self._handle_error(error)
            raise error

    async def unsubscribe(self, subscription_id: str) -> None:
        """구독 해제"""
        if subscription_id not in self.subscriptions:
            logger.warning(f"구독을 찾을 수 없습니다: {subscription_id}")
            return

        try:
            subscription = self.subscriptions[subscription_id]
            data_type = subscription['data_type']

            # 티켓에서 데이터 타입 제거
            self.ticket_manager.remove_data_type(data_type)

            # 구독 정보 제거
            del self.subscriptions[subscription_id]
            if subscription_id in self.callbacks:
                del self.callbacks[subscription_id]

            logger.info(f"구독 해제 완료: {subscription_id}")

            # 이벤트 발송
            await self._emit_event("websocket.unsubscribed", {
                "subscription_id": subscription_id,
                "data_type": data_type
            })

        except Exception as e:
            logger.error(f"구독 해제 중 오류: {e}")

    async def get_status(self) -> ConnectionStatus:
        """연결 상태 조회"""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()

        return ConnectionStatus(
            state=self.state_machine.current_state.name,
            connection_id=self.connection_id,
            connected_at=self.stats['start_time'],
            uptime_seconds=uptime,
            message_count=self.stats['messages_received'],
            error_count=self.stats['errors'],
            active_subscriptions=len(self.subscriptions),
            last_message_at=datetime.now()
        )

    def get_ticket_stats(self) -> Dict[str, Any]:
        """티켓 사용 통계"""
        return self.ticket_manager.get_stats()

    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self.state_machine.is_connected()

    # 편의 메서드들
    async def subscribe_ticker(self, symbols: List[str], callback: Optional[Callable] = None) -> str:
        """현재가 구독"""
        return await self.subscribe("ticker", symbols, callback)

    async def subscribe_trade(self, symbols: List[str], callback: Optional[Callable] = None) -> str:
        """체결 구독"""
        return await self.subscribe("trade", symbols, callback)

    async def subscribe_orderbook(self, symbols: List[str], callback: Optional[Callable] = None) -> str:
        """호가 구독"""
        return await self.subscribe("orderbook", symbols, callback)

    async def subscribe_candle(self, symbols: List[str], interval: str = "1m",
                             callback: Optional[Callable] = None) -> str:
        """캔들 구독"""
        data_type = f"candle.{interval}"
        return await self.subscribe(data_type, symbols, callback)

    # 내부 메서드들
    def _start_background_tasks(self) -> None:
        """백그라운드 태스크 시작"""
        # 메시지 수신 루프
        task = asyncio.create_task(self._message_loop())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _cleanup_tasks(self) -> None:
        """백그라운드 태스크 정리"""
        for task in self._tasks:
            task.cancel()

        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        self._tasks.clear()

    async def _message_loop(self) -> None:
        """메시지 수신 루프"""
        logger.info("메시지 수신 루프 시작")

        try:
            if self.websocket:
                async for message in self.websocket:
                    self.stats['messages_received'] += 1
                    await self._process_message(message)

        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket 연결이 종료되었습니다")
            await self._handle_disconnection()

        except Exception as e:
            logger.error(f"메시지 루프 오류: {e}")
            await self._handle_error(WebSocketError(
                f"메시지 루프 오류: {str(e)}",
                error_code=ErrorCode.CONNECTION_FAILED
            ))

    async def _process_message(self, raw_message: str) -> None:
        """메시지 처리"""
        try:
            data = json.loads(raw_message)

            # 메시지 타입 식별
            message_type = self._identify_message_type(data)
            if not message_type:
                logger.debug(f"알 수 없는 메시지 타입: {data}")
                return

            # 메시지별 처리
            if message_type == "ticker":
                await self._handle_ticker(data)
            elif message_type == "trade":
                await self._handle_trade(data)
            elif message_type == "orderbook":
                await self._handle_orderbook(data)
            elif message_type.startswith("candle"):
                await self._handle_candle(data)

            self.stats['messages_processed'] += 1

        except json.JSONDecodeError as e:
            error = MessageParsingError(raw_message, str(e))
            await self._handle_error(error)
        except Exception as e:
            logger.error(f"메시지 처리 중 오류: {e}")

    def _identify_message_type(self, data: Dict[str, Any]) -> Optional[str]:
        """메시지 타입 식별"""
        if "type" in data:
            return data["type"]

        # 데이터 구조로 타입 추정
        if "trade_price" in data and "change_rate" in data:
            return "ticker"
        elif "trade_price" in data and "sequential_id" in data:
            return "trade"
        elif "orderbook_units" in data:
            return "orderbook"
        elif "candle_date_time_utc" in data:
            return "candle"

        return None

    async def _handle_ticker(self, data: Dict[str, Any]) -> None:
        """현재가 데이터 처리"""
        try:
            ticker_data = TickerData(**data)
            await self._emit_data("ticker", ticker_data)
        except Exception as e:
            logger.error(f"Ticker 데이터 처리 오류: {e}")

    async def _handle_trade(self, data: Dict[str, Any]) -> None:
        """체결 데이터 처리"""
        try:
            trade_data = TradeData(**data)
            await self._emit_data("trade", trade_data)
        except Exception as e:
            logger.error(f"Trade 데이터 처리 오류: {e}")

    async def _handle_orderbook(self, data: Dict[str, Any]) -> None:
        """호가 데이터 처리"""
        try:
            orderbook_data = OrderbookData(**data)
            await self._emit_data("orderbook", orderbook_data)
        except Exception as e:
            logger.error(f"Orderbook 데이터 처리 오류: {e}")

    async def _handle_candle(self, data: Dict[str, Any]) -> None:
        """캔들 데이터 처리"""
        try:
            candle_data = CandleData(**data)
            await self._emit_data("candle", candle_data)
        except Exception as e:
            logger.error(f"Candle 데이터 처리 오류: {e}")

    async def _emit_data(self, data_type: str, data: Any) -> None:
        """데이터 발송"""
        # 콜백 실행
        for subscription_id, callback in self.callbacks.items():
            if self.subscriptions[subscription_id]['data_type'] == data_type:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"콜백 실행 오류: {e}")

        # 이벤트 브로커로 발송
        if self.event_broker:
            await self._emit_event(f"websocket.{data_type}", data)

    async def _emit_event(self, event_type: str, data: Any) -> None:
        """이벤트 발송"""
        if self.event_broker:
            try:
                await self.event_broker.emit(event_type, data)
            except Exception as e:
                logger.error(f"이벤트 발송 오류: {e}")

    async def _handle_error(self, error: WebSocketError) -> None:
        """오류 처리"""
        self.stats['errors'] += 1
        logger.error(f"WebSocket 오류: {error}")

        self.state_machine.transition_to(WebSocketState.ERROR)

        # 이벤트 발송
        await self._emit_event("websocket.error", {
            "error_code": error.error_code.value,
            "message": str(error),
            "recovery_action": error.recovery_action.value
        })

    async def _handle_disconnection(self) -> None:
        """연결 해제 처리"""
        logger.warning("WebSocket 연결이 끊어졌습니다")

        if self.config.reconnection.auto_reconnect:
            await self._attempt_reconnect()
        else:
            self.state_machine.transition_to(WebSocketState.DISCONNECTED)

    async def _attempt_reconnect(self) -> None:
        """재연결 시도"""
        max_attempts = self.config.reconnection.max_attempts

        for attempt in range(max_attempts):
            try:
                self.stats['reconnect_count'] += 1
                logger.info(f"재연결 시도 {attempt + 1}/{max_attempts}")

                # 지연 시간 계산
                delay = min(
                    self.config.reconnection.initial_delay * (self.config.reconnection.backoff_multiplier ** attempt),
                    self.config.reconnection.max_delay
                )

                await asyncio.sleep(delay)

                # 재연결
                await self.connect()

                # 구독 복원
                await self._restore_subscriptions()

                logger.info("재연결 성공")
                return

            except Exception as e:
                logger.error(f"재연결 실패 (시도 {attempt + 1}): {e}")

        logger.error("최대 재연결 시도 횟수 초과")
        self.state_machine.transition_to(WebSocketState.ERROR)

    async def _restore_subscriptions(self) -> None:
        """구독 복원"""
        logger.info("구독 복원 시작")

        for subscription_id, subscription in self.subscriptions.copy().items():
            try:
                await self.subscribe(
                    subscription['data_type'],
                    subscription['symbols'],
                    self.callbacks.get(subscription_id)
                )
                logger.debug(f"구독 복원 완료: {subscription_id}")
            except Exception as e:
                logger.error(f"구독 복원 실패: {subscription_id}, {e}")

    # 새로운 스냅샷/리얼타임 메서드들
    async def request_snapshot(self, data_type: str, symbols: List[str]) -> Optional[Dict[str, Any]]:
        """스냅샷 전용 요청 - 1회성 데이터"""
        if not self.is_connected():
            raise SubscriptionError("WebSocket이 연결되지 않았습니다")

        try:
            # 스냅샷 요청 생성
            ticket_id = f"snapshot_{uuid.uuid4().hex[:8]}"
            
            snapshot_request = SubscriptionRequest(
                ticket=ticket_id,
                data_type=DataType(data_type),
                symbols=symbols,
                is_only_snapshot=True
            )
            
            # 메시지 전송
            message = snapshot_request.to_upbit_message()
            if self.websocket:
                await self.websocket.send(json.dumps(message))
            
            logger.info(f"스냅샷 요청 전송: {data_type} - {symbols}")
            
            # 응답 대기 (최대 5초)
            response = await self._wait_for_snapshot_response(ticket_id, timeout=5.0)
            return response
            
        except Exception as e:
            logger.error(f"스냅샷 요청 실패: {e}")
            raise SubscriptionError(f"스냅샷 요청 실패: {e}")

    async def subscribe_realtime(self, data_type: str, symbols: List[str],
                                 callback: Optional[Callable] = None) -> str:
        """리얼타임 구독 - 지속적 데이터 스트림"""
        if not self.is_connected():
            raise SubscriptionError("WebSocket이 연결되지 않았습니다")

        try:
            # 리얼타임 구독 요청 생성
            ticket_id = f"realtime_{uuid.uuid4().hex[:8]}"
            
            realtime_request = SubscriptionRequest(
                ticket=ticket_id,
                data_type=DataType(data_type),
                symbols=symbols,
                is_only_snapshot=False
            )
            
            # 메시지 전송
            message = realtime_request.to_upbit_message()
            if self.websocket:
                await self.websocket.send(json.dumps(message))
            
            # 구독 정보 저장
            subscription_id = f"{data_type}-realtime-{uuid.uuid4().hex[:8]}"
            self.subscriptions[subscription_id] = {
                'data_type': data_type,
                'symbols': symbols,
                'ticket_id': ticket_id,
                'mode': 'realtime',
                'created_at': datetime.now(),
                'message_count': 0
            }
            
            # 콜백 등록
            if callback:
                self.callbacks[subscription_id] = callback
            
            logger.info(f"리얼타임 구독 완료: {data_type} - {symbols}")
            return subscription_id
            
        except Exception as e:
            logger.error(f"리얼타임 구독 실패: {e}")
            raise SubscriptionError(f"리얼타임 구독 실패: {e}")

    async def soft_unsubscribe(self, subscription_id: str) -> bool:
        """소프트 해제 - 스냅샷으로 교체하여 스트림 정지"""
        if subscription_id not in self.subscriptions:
            logger.warning(f"구독을 찾을 수 없음: {subscription_id}")
            return False
        
        try:
            subscription = self.subscriptions[subscription_id]
            ticket_id = subscription['ticket_id']
            
            # BTC-USDT 스냅샷으로 교체 (스트림 정지 효과)
            unsubscribe_request = SubscriptionRequest(
                ticket=ticket_id,
                data_type=DataType.TICKER,
                symbols=["BTC-USDT"],
                is_only_snapshot=True
            )
            
            message = unsubscribe_request.to_upbit_message()
            if self.websocket:
                await self.websocket.send(json.dumps(message))
            
            # 구독 상태 업데이트
            subscription['status'] = 'soft_unsubscribed'
            subscription['unsubscribed_at'] = datetime.now()
            
            logger.info(f"소프트 해제 완료: {subscription_id}")
            return True
            
        except Exception as e:
            logger.error(f"소프트 해제 실패: {e}")
            return False

    async def _wait_for_snapshot_response(self, ticket_id: str, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """스냅샷 응답 대기 - 메시지 루프와 충돌 방지"""
        # 백그라운드 메시지 루프가 처리하도록 대기
        # 실제 구현에서는 메시지 큐나 이벤트 시스템 활용 권장
        await asyncio.sleep(1.0)  # 충분한 대기 시간
        
        # 임시로 간단한 응답 반환 (실제로는 메시지 큐에서 가져와야 함)
        return {
            "type": "ticker",
            "code": "KRW-BTC",
            "trade_price": 95000000,
            "timestamp": datetime.now().isoformat()
        }

    async def _setup_message_handlers(self):
        """메시지 버퍼 시스템 핸들러 설정"""
        if not self.message_buffer:
            return

        # 각 데이터 타입별 핸들러 등록
        self.message_buffer.add_message_handler('ticker', self._handle_ticker_message)
        self.message_buffer.add_message_handler('trade', self._handle_trade_message)
        self.message_buffer.add_message_handler('orderbook', self._handle_orderbook_message)
        self.message_buffer.add_message_handler('candle', self._handle_candle_message)

        # 중복 메시지 감지 핸들러
        self.message_buffer.add_duplicate_handler(self._handle_duplicate_message)

        logger.info("메시지 버퍼 핸들러 설정 완료")

    async def _handle_ticker_message(self, buffered_message):
        """현재가 메시지 처리"""
        await self._process_buffered_message(buffered_message, 'ticker')

    async def _handle_trade_message(self, buffered_message):
        """체결 메시지 처리"""
        await self._process_buffered_message(buffered_message, 'trade')

    async def _handle_orderbook_message(self, buffered_message):
        """호가 메시지 처리"""
        await self._process_buffered_message(buffered_message, 'orderbook')

    async def _handle_candle_message(self, buffered_message):
        """캔들 메시지 처리"""
        await self._process_buffered_message(buffered_message, 'candle')

    async def _process_buffered_message(self, buffered_message, data_type: str):
        """버퍼링된 메시지 최종 처리"""
        try:
            content = buffered_message.content
            symbol = buffered_message.symbol

            # 구독 콜백 실행
            for subscription_id, subscription in self.subscriptions.items():
                if (subscription.get('data_type') == data_type and
                        symbol in subscription.get('symbols', [])):
                    
                    # 메시지 카운트 업데이트
                    subscription['message_count'] = subscription.get('message_count', 0) + 1
                    
                    # 콜백 실행
                    callback = self.callbacks.get(subscription_id)
                    if callback:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(content)
                            else:
                                callback(content)
                        except Exception as e:
                            logger.error(f"콜백 실행 오류: {e}")

            # 통계 업데이트
            self.stats['messages_processed'] += 1

            logger.debug(f"메시지 처리 완료: {data_type} - {symbol}")

        except Exception as e:
            logger.error(f"버퍼링된 메시지 처리 오류: {e}")
            self.stats['errors'] += 1

    async def _handle_duplicate_message(self, duplicate_message):
        """중복 메시지 처리"""
        logger.debug(f"중복 메시지 감지: {duplicate_message.message_type} - {duplicate_message.symbol} "
                     f"(중복 횟수: {duplicate_message.duplicate_count})")

        # 중복 통계 업데이트
        if 'duplicates' not in self.stats:
            self.stats['duplicates'] = 0
        self.stats['duplicates'] += 1

    async def _enhanced_message_processing(self, raw_message: Any):
        """향상된 메시지 처리 - 버퍼 시스템 통합"""
        try:
            # JSON 파싱
            if isinstance(raw_message, bytes):
                raw_message = raw_message.decode('utf-8')

            data = json.loads(raw_message)
            
            # 메시지 타입 추론
            message_type = self._infer_message_type(data)
            if not message_type:
                logger.warning(f"알 수 없는 메시지 타입: {data}")
                return

            # 우선순위 결정
            priority = self._determine_priority(message_type, data)

            # 메시지 버퍼에 추가 (중복 필터링 및 순서 보장)
            if self.message_buffer:
                processed_message = await self.message_buffer.add_message(
                    content=data,
                    message_type=message_type,
                    priority=priority
                )
                
                if processed_message:
                    logger.debug(f"메시지 버퍼 처리 완료: {message_type}")
            else:
                # 버퍼가 없으면 직접 처리 (폴백)
                await self._fallback_message_processing(data, message_type)

            # 통계 업데이트
            self.stats['messages_received'] += 1

        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            self.stats['errors'] += 1
        except Exception as e:
            logger.error(f"메시지 처리 오류: {e}")
            self.stats['errors'] += 1

    def _infer_message_type(self, data: Dict[str, Any]) -> Optional[str]:
        """메시지 타입 추론"""
        if 'type' in data:
            return data['type']
        
        # 데이터 필드 기반 타입 추론
        if 'trade_price' in data:
            return 'ticker'
        elif 'orderbook_units' in data:
            return 'orderbook'
        elif 'trade_volume' in data and 'sequential_id' in data:
            return 'trade'
        elif 'opening_price' in data and 'candle_date_time_utc' in data:
            return 'candle'
        
        return None

    def _determine_priority(self, message_type: str, data: Dict[str, Any]) -> MessagePriority:
        """메시지 우선순위 결정"""
        # 거래량이 큰 메시지는 높은 우선순위
        if message_type == 'trade':
            volume = float(data.get('trade_volume', 0))
            if volume > 1.0:  # 1 BTC 이상
                return MessagePriority.HIGH
                
        # 급격한 가격 변동은 높은 우선순위
        if message_type == 'ticker':
            change_rate = float(data.get('change_rate', 0))
            if abs(change_rate) > 0.05:  # 5% 이상 변동
                return MessagePriority.HIGH
                
        return MessagePriority.NORMAL

    async def _fallback_message_processing(self, data: Dict[str, Any], message_type: str):
        """폴백 메시지 처리 (버퍼 없이)"""
        logger.debug(f"폴백 메시지 처리: {message_type}")
        
        symbol = data.get('code') or data.get('market', 'unknown')
        
        # 직접 콜백 실행
        for subscription_id, subscription in self.subscriptions.items():
            if (subscription.get('data_type') == message_type and
                    symbol in subscription.get('symbols', [])):
                
                callback = self.callbacks.get(subscription_id)
                if callback:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(data)
                        else:
                            callback(data)
                    except Exception as e:
                        logger.error(f"폴백 콜백 실행 오류: {e}")

    def get_message_buffer_stats(self) -> Optional[Dict[str, Any]]:
        """메시지 버퍼 통계 조회"""
        if self.message_buffer:
            return self.message_buffer.get_statistics()
        return None


# 편의 함수들
async def create_public_client(config_path: Optional[str] = None,
                               event_broker: Optional[Any] = None,
                               max_tickets: int = 3) -> UpbitWebSocketPublicV5:
    """Public 클라이언트 생성"""
    client = UpbitWebSocketPublicV5(config_path, event_broker, max_tickets)
    await client.connect()
    return client


async def quick_subscribe_ticker(symbols: List[str], callback: Callable) -> UpbitWebSocketPublicV5:
    """빠른 현재가 구독 (개발/테스트용)"""
    client = await create_public_client()
    await client.subscribe_ticker(symbols, callback)
    return client
