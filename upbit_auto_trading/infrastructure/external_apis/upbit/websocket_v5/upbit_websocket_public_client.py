"""
업비트 WebSocket v5.0 - Public 클라이언트 (v4.0 통합 버전)

🎯 특징:
- SubscriptionManager v4.0 완전 통합
- 레거시 호환성 제거, 순수 v4.0 API
- 지능적 구독 최적화 및 자동 생명주기 관리
- 스냅샷/리얼타임 단순화된 인터페이스
- 압축 지원 (deflate) 및 SIMPLE 포맷 지원
- 업비트 공식 API 100% 호환
"""
import asyncio
import json
import time
import uuid
import websockets
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .models import (
    infer_message_type, validate_mixed_message, create_websocket_message,
    create_connection_status
)
from .config import load_config
from .state import WebSocketState, WebSocketStateMachine
from .subscription_manager import SubscriptionManager
from .simple_format_converter import (
    auto_detect_and_convert,
    convert_to_simple_format,
    convert_from_simple_format,
)
from .exceptions import (
    WebSocketError, WebSocketConnectionError, WebSocketConnectionTimeoutError,
    SubscriptionError, MessageParsingError,
    ErrorCode
)

logger = create_component_logger("UpbitWebSocketPublicV5")


class UpbitWebSocketPublicV5:
    """업비트 WebSocket v5.0 Public 클라이언트 - v4.0 구독 매니저 통합"""

    def __init__(self, config_path: Optional[str] = None,
                 event_broker: Optional[Any] = None,
                 cleanup_interval: Optional[int] = None):
        """
        Args:
            config_path: 설정 파일 경로
            event_broker: 외부 이벤트 브로커
            cleanup_interval: 구독 자동 정리 간격 (초, None이면 30초)
        """
        # 설정 로드
        self.config = load_config(config_path)

        # 상태 관리
        self.state_machine = WebSocketStateMachine()

        # 연결 관리
        self.websocket: Optional[Any] = None
        self.connection_id = str(uuid.uuid4())

        # 🚀 v4.0 구독 관리자 통합 (순수 v4.0 API)
        self.subscription_manager = SubscriptionManager(
            cleanup_interval=cleanup_interval or 30
        )

        # 이벤트 시스템
        self.event_broker = event_broker

        # 통계
        self.stats = {
            'messages_received': 0,
            'messages_processed': 0,
            'errors': 0,
            'reconnect_count': 0,
            'start_time': datetime.now(),
            'last_message_time': None
        }

        # 백그라운드 태스크
        self._tasks: Set[asyncio.Task] = set()

        logger.info(f"Public WebSocket 클라이언트 v4.0 초기화 완료 - ID: {self.connection_id}")

    def _default_callback(self, symbol: str, data_type: str, data: dict):
        """기본 콜백 함수"""
        logger.debug(f"Public 기본 콜백: {symbol} {data_type} 데이터 수신")

    async def connect(self, enable_compression: Optional[bool] = None,
                      enable_simple_format: bool = False) -> None:
        """
        WebSocket 연결

        Args:
            enable_compression: WebSocket 압축 활성화 (None이면 config에서 로드)
            enable_simple_format: SIMPLE 포맷 사용 여부
        """
        if self.state_machine.current_state != WebSocketState.DISCONNECTED:
            logger.warning(f"이미 연결된 상태입니다: {self.state_machine.current_state}")
            return

        try:
            self.state_machine.transition_to(WebSocketState.CONNECTING)
            logger.info(f"WebSocket 연결 시도: {self.config.connection.url}")

            # 압축 설정
            compression_enabled = (enable_compression
                                   if enable_compression is not None
                                   else self.config.performance.enable_message_compression)

            # SIMPLE 포맷 설정 저장
            self.enable_simple_format = enable_simple_format

            # WebSocket 연결 옵션 구성
            connection_kwargs = {
                "ping_interval": self.config.connection.ping_interval,
                "ping_timeout": self.config.connection.ping_timeout,
                "close_timeout": self.config.connection.close_timeout,
            }

            if compression_enabled:
                logger.debug("Public WebSocket 압축 기능 활성화 (deflate)")
                connection_kwargs["compression"] = "deflate"

            if enable_simple_format:
                logger.debug("Public WebSocket SIMPLE 포맷 활성화")

            # WebSocket 연결
            self.websocket = await asyncio.wait_for(
                websockets.connect(
                    self.config.connection.url,
                    **connection_kwargs
                ),
                timeout=self.config.connection.connect_timeout
            )

            self.state_machine.transition_to(WebSocketState.CONNECTED)
            logger.info("WebSocket 연결 완료")

            # 🚀 v4.0 구독 매니저에 WebSocket 연결 설정
            self.subscription_manager.set_websocket_connections(public_ws=self.websocket)

            # 백그라운드 태스크 시작
            self._start_background_tasks()

            # 백그라운드 서비스 시작
            await self.subscription_manager.start_background_services()

            # 이벤트 발송
            await self._emit_event("websocket.connected", {
                "connection_id": self.connection_id,
                "timestamp": datetime.now().isoformat(),
                "compression_enabled": compression_enabled,
                "simple_format_enabled": enable_simple_format
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

            # 백그라운드 서비스 중단
            self.subscription_manager.stop_background_services()

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
                        callback: Optional[Callable] = None,
                        is_only_snapshot: bool = False) -> str:
        """데이터 구독 - v4.0 SubscriptionManager 완전 통합

        Args:
            data_type: 데이터 타입 (ticker, trade, orderbook, minute1 등)
            symbols: 구독할 심볼 리스트
            callback: 데이터 수신 콜백
            is_only_snapshot: True이면 스냅샷만 수신 후 종료

        Returns:
            subscription_id: 구독 식별자
        """
        if not self.is_connected():
            raise SubscriptionError("WebSocket이 연결되지 않았습니다", data_type, symbols)

        try:
            self.state_machine.transition_to(WebSocketState.SUBSCRIBING)

            if is_only_snapshot:
                # v4.0 스냅샷 요청
                await self.subscription_manager.request_snapshot_data(
                    symbols=symbols,
                    data_type=data_type,
                    connection_type="public",
                    timeout=5.0
                )
                subscription_id = f"snapshot_{data_type}_{int(time.time())}"
                logger.info(f"스냅샷 구독 완료: {data_type} - {symbols}")
            else:
                # v4.0 실시간 구독
                success = await self.subscription_manager.request_realtime_data(
                    symbols=symbols,
                    data_type=data_type,
                    callback=callback or self._default_callback,
                    client_id=f"public_{data_type}",
                    connection_type="public"
                )

                if success:
                    subscription_id = f"realtime_{data_type}_{int(time.time())}"
                    logger.info(f"실시간 구독 완료: {data_type} - {symbols}")
                else:
                    raise SubscriptionError(f"실시간 구독 실패: {data_type}", data_type, symbols)

            self.state_machine.transition_to(WebSocketState.ACTIVE)
            return subscription_id

        except Exception as e:
            error = SubscriptionError(f"구독 실패: {str(e)}", data_type, symbols)
            await self._handle_error(error)
            raise error

    async def unsubscribe(self, subscription_id: str) -> None:
        """구독 해제 - v4.0 단순화"""
        try:
            # v4.0에서는 SubscriptionManager가 직접 처리
            await self.subscription_manager.unsubscribe(subscription_id)
            logger.info(f"구독 해제 완료: {subscription_id}")

        except Exception as e:
            logger.error(f"구독 해제 중 오류: {e}")

    async def unsubscribe_all(self) -> bool:
        """모든 구독 해제 - v4.0"""
        try:
            return await self.subscription_manager.unsubscribe_all("public")
        except Exception as e:
            logger.error(f"전체 구독 해제 실패: {e}")
            return False

    # 편의 메서드들 - v4.0 간소화
    async def subscribe_ticker(self, symbols: List[str], callback: Optional[Callable] = None,
                               is_only_snapshot: bool = False) -> str:
        """현재가 구독 - v4.0 단순화"""
        return await self.subscribe("ticker", symbols, callback, is_only_snapshot)

    async def subscribe_trade(self, symbols: List[str], callback: Optional[Callable] = None,
                              is_only_snapshot: bool = False) -> str:
        """체결 구독 - v4.0 단순화"""
        return await self.subscribe("trade", symbols, callback, is_only_snapshot)

    async def subscribe_orderbook(self, symbols: List[str], callback: Optional[Callable] = None,
                                  is_only_snapshot: bool = False) -> str:
        """호가 구독 - v4.0 단순화"""
        return await self.subscribe("orderbook", symbols, callback, is_only_snapshot)

    async def subscribe_candle(self, symbols: List[str], interval: str = "1m",
                               callback: Optional[Callable] = None,
                               is_only_snapshot: bool = False) -> str:
        """캔들 구독 - v4.0 단순화"""
        # 업비트 표준 데이터 타입으로 변환
        if interval.endswith('m'):
            data_type = f"minute{interval[:-1]}"
        elif interval.endswith('h'):
            data_type = f"minute{int(interval[:-1]) * 60}"
        elif interval == "1d":
            data_type = "day"
        elif interval == "1w":
            data_type = "week"
        elif interval == "1M":
            data_type = "month"
        else:
            data_type = f"minute{interval}"

        return await self.subscribe(data_type, symbols, callback, is_only_snapshot)

    # 상태 조회 메서드들 - v4.0 단순화
    async def get_status(self) -> Dict[str, Any]:
        """연결 상태 조회 - v4.0 구독 매니저 통합"""
        current_time = datetime.now()
        uptime = (current_time - self.stats['start_time']).total_seconds()

        # v4.0 구독 정보
        subscription_state = self.subscription_manager.get_state()

        return {
            **create_connection_status(
                state=self.state_machine.current_state.name,
                connection_id=self.connection_id
            ),
            "uptime_seconds": round(uptime, 2),
            "messages_received": self.stats['messages_received'],
            "messages_processed": self.stats['messages_processed'],
            "error_count": self.stats['errors'],
            "subscription_state": subscription_state
        }

    async def health_check(self) -> Dict[str, Any]:
        """건강 상태 체크 - v4.0"""
        current_time = datetime.now()
        uptime = (current_time - self.stats['start_time']).total_seconds()

        # 연결 상태 체크
        is_connected = self.is_connected()

        # 최근 메시지 수신 확인 (30초 이내)
        last_message_ago = None
        if self.stats['last_message_time']:
            last_message_ago = (current_time - self.stats['last_message_time']).total_seconds()

        # 건강도 점수 계산
        health_score = 100

        if not is_connected:
            health_score -= 50

        if last_message_ago and last_message_ago > 30:
            health_score -= 20

        if self.stats['errors'] / max(self.stats['messages_received'], 1) > 0.01:
            health_score -= 15

        # 상태 등급
        if health_score >= 90:
            status = "🟢 EXCELLENT"
        elif health_score >= 75:
            status = "🟡 GOOD"
        elif health_score >= 50:
            status = "🟠 WARNING"
        else:
            status = "🔴 CRITICAL"

        # v4.0 구독 정보
        subscription_state = self.subscription_manager.get_state()
        active_intents = len(subscription_state.get('realtime_intents', {}))

        return {
            'overall_status': status,
            'health_score': max(0, health_score),
            'connection_status': '🟢 Connected' if is_connected else '🔴 Disconnected',
            'uptime_minutes': round(uptime / 60, 1),
            'last_message_seconds_ago': round(last_message_ago, 1) if last_message_ago else None,
            'error_count': self.stats['errors'],
            'active_subscriptions': active_intents
        }

    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self.state_machine.is_connected()

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
        """메시지 수신 루프 - v4.0 단순화"""
        logger.info("메시지 수신 루프 시작")

        try:
            if self.websocket:
                async for message in self.websocket:
                    self.stats['messages_received'] += 1
                    self.stats['last_message_time'] = datetime.now()
                    await self._process_message(message)

        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket 연결이 종료되었습니다")
            await self._handle_disconnection()

        except Exception as e:
            logger.error(f"메시지 루프 오류: {e}")
            self.stats['errors'] += 1
            await self._handle_error(WebSocketError(
                f"메시지 루프 오류: {str(e)}",
                error_code=ErrorCode.CONNECTION_FAILED
            ))

    async def _process_message(self, raw_message) -> None:
        """메시지 처리 - v4.0 단순화 + SIMPLE 포맷 변환"""
        message_str = ""
        try:
            # 🔧 bytes 객체를 문자열로 변환
            if isinstance(raw_message, bytes):
                message_str = raw_message.decode('utf-8')
            else:
                message_str = raw_message

            # 🔍 디버그: 수신된 원본 메시지 로깅
            logger.debug(f"수신된 메시지: {message_str[:200]}{'...' if len(message_str) > 200 else ''}")

            data = json.loads(message_str)

            # SIMPLE 포맷 변환 처리
            if hasattr(self, 'enable_simple_format') and self.enable_simple_format:
                try:
                    # SIMPLE 포맷을 DEFAULT 포맷으로 변환
                    data = auto_detect_and_convert(data)
                    logger.debug("SIMPLE 포맷을 DEFAULT 포맷으로 변환 완료")
                except Exception as e:
                    logger.warning(f"SIMPLE 포맷 변환 실패, 원본 데이터 사용: {e}")

            # 메시지 타입 식별
            message_type = self._identify_message_type(data)
            if not message_type:
                logger.debug(f"알 수 없는 메시지: {data}")
                return

            # 메시지별 처리
            if message_type == "ticker":
                await self._handle_ticker(data)
            elif message_type == "trade":
                await self._handle_trade(data)
            elif message_type == "orderbook":
                await self._handle_orderbook(data)
            elif message_type.startswith("minute") or message_type in ["day", "week", "month"]:
                await self._handle_candle(data)

            self.stats['messages_processed'] += 1

        except json.JSONDecodeError as e:
            self.stats['errors'] += 1
            error = MessageParsingError(message_str or str(raw_message), str(e))
            await self._handle_error(error)
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"메시지 처리 중 오류: {e}")

    def _identify_message_type(self, data: Dict[str, Any]) -> Optional[str]:
        """메시지 타입 식별"""
        return infer_message_type(data)

    async def _handle_ticker(self, data: Dict[str, Any]) -> None:
        """현재가 데이터 처리"""
        try:
            logger.debug(f"Ticker 데이터 처리 시작: {data.get('code', 'UNKNOWN')}")
            validated_data = validate_mixed_message(data)
            message = create_websocket_message("ticker", data.get('code', 'UNKNOWN'), validated_data)
            await self._emit_data("ticker", message)
            logger.debug(f"Ticker 데이터 처리 완료: {data.get('code', 'UNKNOWN')}")
        except Exception as e:
            logger.error(f"Ticker 데이터 처리 오류: {e}")
            logger.error(f"문제 데이터: {data}")

    async def _handle_trade(self, data: Dict[str, Any]) -> None:
        """체결 데이터 처리"""
        try:
            validated_data = validate_mixed_message(data)
            message = create_websocket_message("trade", data.get('code', 'UNKNOWN'), validated_data)
            await self._emit_data("trade", message)
        except Exception as e:
            logger.error(f"Trade 데이터 처리 오류: {e}")

    async def _handle_orderbook(self, data: Dict[str, Any]) -> None:
        """호가 데이터 처리"""
        try:
            validated_data = validate_mixed_message(data)
            message = create_websocket_message("orderbook", data.get('code', 'UNKNOWN'), validated_data)
            await self._emit_data("orderbook", message)
        except Exception as e:
            logger.error(f"Orderbook 데이터 처리 오류: {e}")

    async def _handle_candle(self, data: Dict[str, Any]) -> None:
        """캔들 데이터 처리"""
        try:
            validated_data = validate_mixed_message(data)
            message = create_websocket_message("candle", data.get('code', 'UNKNOWN'), validated_data)
            await self._emit_data("candle", message)
        except Exception as e:
            logger.error(f"Candle 데이터 처리 오류: {e}")

    async def _emit_data(self, data_type: str, data: Any) -> None:
        """데이터 발송 - v4.0 직접 처리"""
        try:
            # 심볼 추출 방법 개선
            if isinstance(data, dict):
                # message 객체에서 market 필드를 우선적으로 사용
                symbol = data.get('market', data.get('code', data.get('symbol', 'UNKNOWN')))
            else:
                symbol = getattr(data, 'market', getattr(data, 'symbol', getattr(data, 'code', 'UNKNOWN')))

            logger.debug(f"데이터 발송: {data_type}, 심볼: {symbol}")
            self.subscription_manager.on_data_received(symbol, data_type, data)
            logger.debug(f"on_data_received 호출 완료: {symbol}")

            # 이벤트 브로커로 발송
            if self.event_broker:
                await self._emit_event(f"websocket.{data_type}", data)

        except Exception as e:
            logger.error(f"데이터 발송 오류: {e}")
            logger.error(f"문제 데이터: {data}")

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

                logger.info("재연결 성공")
                return

            except Exception as e:
                logger.error(f"재연결 실패 (시도 {attempt + 1}): {e}")

        logger.error("최대 재연결 시도 횟수 초과")
        self.state_machine.transition_to(WebSocketState.ERROR)


# 편의 함수들
async def create_public_client(config_path: Optional[str] = None,
                               event_broker: Optional[Any] = None,
                               cleanup_interval: int = 30) -> UpbitWebSocketPublicV5:
    """Public 클라이언트 생성"""
    client = UpbitWebSocketPublicV5(config_path, event_broker, cleanup_interval)
    await client.connect()
    return client


async def quick_subscribe_ticker(symbols: List[str], callback: Callable) -> UpbitWebSocketPublicV5:
    """빠른 현재가 구독 (개발/테스트용)"""
    client = await create_public_client()
    await client.subscribe_ticker(symbols, callback)
    return client
