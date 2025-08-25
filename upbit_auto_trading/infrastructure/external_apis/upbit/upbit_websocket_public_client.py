"""
업비트 WebSocket Public 클라이언트 - Private API 수준 품질 개선
- 인증이 필요없는 공개 시세 데이터 실시간 수신
- Dict 통일 정책 적용
- 타입 안전성 보장
- Infrastructure 로깅 체계
"""

import asyncio
import websockets
import json
import uuid
from typing import Dict, Any, List, Optional, Callable, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger


class WebSocketDataType(Enum):
    """WebSocket 데이터 타입 (공개 API 전용)"""
    TICKER = "ticker"
    TRADE = "trade"
    ORDERBOOK = "orderbook"
    CANDLE = "candle"  # 모든 캔들 타입 통합


class StreamType(Enum):
    """업비트 WebSocket 스트림 타입"""
    SNAPSHOT = "SNAPSHOT"  # 스냅샷 (타임프레임 완료/초기 데이터)
    REALTIME = "REALTIME"  # 실시간 업데이트


@dataclass(frozen=True)
class WebSocketMessage:
    """WebSocket 메시지 구조 - 불변 DTO (스트림 타입 포함)"""
    type: WebSocketDataType
    market: str
    data: Dict[str, Any]
    timestamp: datetime
    raw_data: str
    stream_type: Optional[StreamType] = None  # 업비트 스트림 타입

    def __post_init__(self):
        """데이터 검증"""
        if not self.market:
            raise ValueError("Market은 필수 필드입니다")
        if not isinstance(self.data, dict):
            raise ValueError("Data는 Dict 타입이어야 합니다")

    def is_snapshot(self) -> bool:
        """스냅샷 메시지인지 확인 (타임프레임 완료)"""
        return self.stream_type == StreamType.SNAPSHOT

    def is_realtime(self) -> bool:
        """실시간 메시지인지 확인 (진행 중 업데이트)"""
        return self.stream_type == StreamType.REALTIME


class SubscriptionResult:
    """구독 결과 - Dict 통일 정책 적용"""

    def __init__(self):
        self._subscriptions: Dict[str, Dict[str, Any]] = {}

    def add_subscription(self, data_type: WebSocketDataType, symbols: List[str], **kwargs) -> None:
        """구독 추가"""
        type_key = data_type.value
        self.add_subscription_with_key(type_key, symbols, **kwargs)

    def add_subscription_with_key(self, type_key: str, symbols: List[str], **kwargs) -> None:
        """키로 직접 구독 추가 (캔들 타입 전용)"""
        if type_key not in self._subscriptions:
            self._subscriptions[type_key] = {
                'symbols': set(),
                'created_at': datetime.now(),
                'metadata': {}
            }

        # 심볼 추가 (중복 제거)
        self._subscriptions[type_key]['symbols'].update(symbols)

        # 메타데이터 업데이트
        if kwargs:
            self._subscriptions[type_key]['metadata'].update(kwargs)

    def get_subscriptions(self) -> Dict[str, Dict[str, Any]]:
        """모든 구독 정보 반환 - Dict 형태"""
        result = {}
        for type_key, sub_data in self._subscriptions.items():
            result[type_key] = {
                'symbols': list(sub_data['symbols']),  # set을 list로 변환
                'created_at': sub_data['created_at'],
                'metadata': sub_data['metadata']
            }
        return result

    def get_symbols_by_type(self, data_type: WebSocketDataType) -> List[str]:
        """특정 타입의 구독 심볼 목록 반환"""
        type_key = data_type.value
        if type_key in self._subscriptions:
            return list(self._subscriptions[type_key]['symbols'])
        return []

    def clear(self) -> None:
        """모든 구독 정보 삭제"""
        self._subscriptions.clear()

    def get_candle_subscriptions(self) -> List[str]:
        """모든 캔들 구독 심볼 통합 반환"""
        candle_symbols = set()
        for key in self._subscriptions:
            if key.startswith('candle.'):
                candle_symbols.update(self._subscriptions[key]['symbols'])
        return list(candle_symbols)

    def has_candle_subscriptions(self) -> bool:
        """캔들 구독이 있는지 확인"""
        return any(key.startswith('candle.') for key in self._subscriptions)


class UpbitWebSocketPublicClient:
    """
    업비트 WebSocket Public 클라이언트 - Private API 수준 품질

    특징:
    - Dict 통일 정책 적용
    - 타입 안전성 보장
    - Infrastructure 로깅 체계
    - 견고한 에러 처리
    - 포괄적인 재연결 메커니즘
    """

    def __init__(self, auto_reconnect: bool = True, max_reconnect_attempts: int = 10,
                 reconnect_delay: float = 5.0, ping_interval: float = 30.0,
                 message_timeout: float = 10.0):
        """
        클라이언트 초기화

        Args:
            auto_reconnect: 자동 재연결 활성화
            max_reconnect_attempts: 최대 재연결 시도 횟수
            reconnect_delay: 재연결 지연 시간 (초)
            ping_interval: PING 간격 (초)
            message_timeout: 메시지 타임아웃 (초)
        """
        # 연결 설정
        self.url = "wss://api.upbit.com/websocket/v1"
        self.websocket: Optional[Any] = None
        self.is_connected = False

        # 구독 관리 - Dict 통일 정책 적용
        self._subscription_manager = SubscriptionResult()

        # 메시지 핸들러 관리
        self.message_handlers: Dict[WebSocketDataType, List[Callable]] = {}

        # 로깅
        self.logger = create_component_logger("UpbitWebSocketPublic")

        # 재연결 설정
        self.auto_reconnect = auto_reconnect
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_attempts = 0

        # 메시지 처리 설정
        self.ping_interval = ping_interval
        self.message_timeout = message_timeout

        # 메시지 수신 루프 제어
        self.message_loop_task: Optional[asyncio.Task] = None
        self.auto_start_message_loop = True
        self._message_loop_running = False

        # 외부 제너레이터 요청 지원
        self._external_listeners: List[asyncio.Queue] = []
        self._enable_external_listen = False

        # 백그라운드 태스크 추적
        self._background_tasks: set = set()

        # 통계 정보
        self._stats = {
            'messages_received': 0,
            'messages_processed': 0,
            'errors_count': 0,
            'last_message_time': None,
            'connection_start_time': None
        }

    async def connect(self) -> bool:
        """WebSocket 연결 (인증 불필요)"""
        try:
            self.logger.info(f"WebSocket 연결 시도: {self.url}")

            # 연결 설정 (인증 불필요)
            self.websocket = await websockets.connect(
                self.url,
                ping_interval=self.ping_interval,
                ping_timeout=self.message_timeout,
                compression=None  # 압축 비활성화로 성능 최적화
            )

            self.is_connected = True
            self.reconnect_attempts = 0
            self._stats['connection_start_time'] = datetime.now()
            self.logger.info("✅ WebSocket 연결 성공 (API 키 불필요)")

            # PING 메시지로 연결 유지
            try:
                loop = asyncio.get_running_loop()
                keep_alive_task = loop.create_task(self._keep_alive())
            except RuntimeError:
                # 이벤트 루프가 없는 경우 백그라운드 태스크 없이 진행
                self.logger.warning("Event Loop가 없어 keep_alive 태스크를 시작할 수 없음")
                keep_alive_task = None

            if keep_alive_task:
                self._background_tasks.add(keep_alive_task)
                keep_alive_task.add_done_callback(self._background_tasks.discard)

            return True

        except Exception as e:
            self.logger.error(f"❌ WebSocket 연결 실패: {e}")
            self.is_connected = False
            self._stats['errors_count'] += 1
            return False

    async def disconnect(self) -> None:
        """WebSocket 연결 해제 (모든 태스크 정리)"""
        try:
            self.auto_reconnect = False

            # 🔧 메시지 수신 루프 중지
            if self.message_loop_task and not self.message_loop_task.done():
                self.message_loop_task.cancel()
                try:
                    await self.message_loop_task
                except asyncio.CancelledError:
                    pass
                self.message_loop_task = None

            # 🔧 모든 백그라운드 태스크 정리
            if self._background_tasks:
                self.logger.debug(f"백그라운드 태스크 {len(self._background_tasks)}개 정리 중...")
                for task in list(self._background_tasks):
                    if not task.done():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                self._background_tasks.clear()
                self.logger.debug("백그라운드 태스크 정리 완료")

            if self.websocket:
                try:
                    # WebSocket 상태 확인 후 닫기
                    if hasattr(self.websocket, 'close') and not getattr(self.websocket, 'closed', True):
                        await self.websocket.close()
                    self.logger.info("WebSocket 연결 해제 완료")
                except Exception as close_error:
                    self.logger.debug(f"WebSocket 닫기 중 오류 (무시됨): {close_error}")
        except Exception as e:
            self.logger.warning(f"WebSocket 연결 해제 중 오류: {e}")
        finally:
            self.is_connected = False
            self.websocket = None
            self._message_loop_running = False

    async def subscribe_ticker(self, symbols: List[str],
                               is_only_snapshot: bool = False,
                               is_only_realtime: bool = False) -> bool:
        """
        현재가 정보 구독 (단수형 컨벤션)

        Args:
            symbols: 심볼 리스트 (모든 심볼 동시 구독 가능)
            is_only_snapshot: 스냅샷 시세만 제공
            is_only_realtime: 실시간 시세만 제공

        Returns:
            bool - 구독 성공 여부
        """
        return await self._subscribe(
            WebSocketDataType.TICKER,
            symbols,
            is_only_snapshot=is_only_snapshot,
            is_only_realtime=is_only_realtime
        )

    async def subscribe_trade(self, symbols: List[str],
                              is_only_snapshot: bool = False,
                              is_only_realtime: bool = False) -> bool:
        """
        체결 정보 구독 (단수형 컨벤션)

        Args:
            symbols: 심볼 리스트 (모든 심볼 동시 구독 가능)
            is_only_snapshot: 스냅샷 시세만 제공
            is_only_realtime: 실시간 시세만 제공

        Returns:
            bool - 구독 성공 여부
        """
        return await self._subscribe(
            WebSocketDataType.TRADE,
            symbols,
            is_only_snapshot=is_only_snapshot,
            is_only_realtime=is_only_realtime
        )

    async def subscribe_orderbook(self, symbols: List[str],
                                  is_only_snapshot: bool = False,
                                  is_only_realtime: bool = False) -> bool:
        """
        호가 정보 구독 (단수형 컨벤션)

        Args:
            symbols: 심볼 리스트 (모든 심볼 동시 구독 가능)
            is_only_snapshot: 스냅샷 시세만 제공
            is_only_realtime: 실시간 시세만 제공

        Returns:
            bool - 구독 성공 여부
        """
        return await self._subscribe(
            WebSocketDataType.ORDERBOOK,
            symbols,
            is_only_snapshot=is_only_snapshot,
            is_only_realtime=is_only_realtime
        )

    async def subscribe_candle(self, symbols: List[str], unit: int = 1,
                               is_only_snapshot: bool = False,
                               is_only_realtime: bool = False) -> bool:
        """
        캔들 정보 구독 (단수형 컨벤션)

        Args:
            symbols: 심볼 리스트 (모든 심볼 동시 구독 가능)
            unit: 캔들 단위 (업비트 지원: 1s, 1m, 3m, 5m, 10m, 15m, 30m, 60m, 240m)
            is_only_snapshot: 스냅샷 시세만 제공
            is_only_realtime: 실시간 시세만 제공

        Returns:
            bool - 구독 성공 여부
        """
        return await self._subscribe(
            WebSocketDataType.CANDLE,
            symbols,
            unit,
            is_only_snapshot=is_only_snapshot,
            is_only_realtime=is_only_realtime
        )

    async def _subscribe(self, data_type: WebSocketDataType, symbols: List[str],
                         candle_unit: Optional[int] = None,
                         is_only_snapshot: bool = False,
                         is_only_realtime: bool = False) -> bool:
        """내부 구독 메서드 - Dict 통일 정책 적용"""
        if not self.is_connected or not self.websocket:
            self.logger.error("WebSocket이 연결되지 않음")
            return False

        try:
            # 고유 티켓 생성
            ticket = f"upbit-auto-trader-{uuid.uuid4().hex[:8]}"

            # 구독 메시지 구성
            data_type_obj = {"type": data_type.value, "codes": symbols}

            # 스트림 타입 옵션 추가 (업비트 공식 지원)
            if is_only_snapshot:
                data_type_obj["is_only_snapshot"] = True
            if is_only_realtime:
                data_type_obj["is_only_realtime"] = True

            subscribe_msg = [
                {"ticket": ticket},
                data_type_obj,
                {"format": "DEFAULT"}  # 압축하지 않은 기본 형식
            ]

            # 캔들 타입인 경우 단위 지정
            if data_type == WebSocketDataType.CANDLE and candle_unit is not None:
                # 문자열을 정수로 변환
                try:
                    unit_int = int(candle_unit)
                except (ValueError, TypeError):
                    unit_int = 5  # 기본값 5분

                # 캔들 단위별 타입 지정 (업비트 공식 WebSocket API 형식)
                # 참고: https://docs.upbit.com/kr/reference/websocket-candle
                candle_type_map = {
                    # 초봉
                    0: "candle.1s",        # 1초봉 (특별값 0으로 구분)
                    # 분봉 (분 단위 그대로 사용)
                    1: "candle.1m",        # 1분봉
                    3: "candle.3m",        # 3분봉
                    5: "candle.5m",        # 5분봉
                    10: "candle.10m",      # 10분봉
                    15: "candle.15m",      # 15분봉
                    30: "candle.30m",      # 30분봉
                    60: "candle.60m",      # 60분봉 (1시간)
                    240: "candle.240m",    # 240분봉 (4시간)
                    # 주의: 1440m(일봉)은 업비트 WebSocket에서 지원하지 않음
                }
                actual_type = candle_type_map.get(unit_int, "candle.5m")
                subscribe_msg[1]["type"] = actual_type

            await self.websocket.send(json.dumps(subscribe_msg))

            # 구독 정보 저장 - 캔들의 경우 실제 타입으로 저장
            if data_type == WebSocketDataType.CANDLE and candle_unit is not None:
                # 실제 전송된 캔들 타입으로 저장
                try:
                    unit_int = int(candle_unit)
                except (ValueError, TypeError):
                    unit_int = 5

                candle_type_map = {
                    0: "candle.1s", 1: "candle.1m", 3: "candle.3m", 5: "candle.5m",
                    10: "candle.10m", 15: "candle.15m", 30: "candle.30m",
                    60: "candle.60m", 240: "candle.240m"
                    # 주의: 1440m(일봉)은 업비트 WebSocket에서 지원하지 않음
                }
                actual_type_str = candle_type_map.get(unit_int, "candle.5m")

                # 실제 캔들 타입으로 저장
                self._subscription_manager.add_subscription_with_key(actual_type_str, symbols)
            else:
                # 일반 타입은 기존 방식
                kwargs = {}
                if candle_unit is not None:
                    kwargs['candle_unit'] = candle_unit
                self._subscription_manager.add_subscription(data_type, symbols, **kwargs)

            # 첫 구독 시 자동으로 메시지 수신 루프 시작
            if self.auto_start_message_loop and not self.message_loop_task and not self._message_loop_running:
                # 현재 이벤트 루프 확인 (안전한 방식)
                try:
                    loop = asyncio.get_running_loop()
                    self.message_loop_task = loop.create_task(self._message_receiver_loop())
                    self.logger.debug("🚀 메시지 수신 루프 자동 시작")
                except RuntimeError:
                    # 이벤트 루프가 없는 경우 수신 루프 없이 진행
                    self.logger.warning("Event Loop가 없어 메시지 수신 루프를 시작할 수 없음")
                    self._enable_external_listen = False
                except Exception as e:
                    self.logger.error(f"메시지 수신 루프 시작 실패: {e}")
                    # Event Loop 문제 시 폴백 모드로 동작
                    self._enable_external_listen = False

            # 심볼 로그 최적화 (대량 심볼일 때 간결하게 표시)
            symbols_display = self._format_symbols_for_log(symbols)
            self.logger.info(f"✅ {data_type.value} 구독 완료: {symbols_display}")
            return True

        except Exception as e:
            self.logger.error(f"❌ {data_type.value} 구독 실패: {e}")
            self._stats['errors_count'] += 1
            return False

    def add_message_handler(self, data_type: WebSocketDataType, handler: Callable[[WebSocketMessage], None]) -> None:
        """메시지 핸들러 등록"""
        if data_type not in self.message_handlers:
            self.message_handlers[data_type] = []
        self.message_handlers[data_type].append(handler)
        self.logger.debug(f"메시지 핸들러 등록: {data_type.value}")

    async def listen(self) -> AsyncGenerator[WebSocketMessage, None]:
        """실시간 메시지 수신 제너레이터 (큐 기반으로 단일 수신 루프와 연동)"""
        if not self.is_connected or not self.websocket:
            raise RuntimeError("WebSocket이 연결되지 않음")

        # 외부 listen 모드 활성화
        self._enable_external_listen = True

        # 이 제너레이터 전용 큐 생성
        message_queue = asyncio.Queue()
        self._external_listeners.append(message_queue)

        # 메시지 루프가 없으면 시작
        if not self.message_loop_task and not self._message_loop_running:
            try:
                loop = asyncio.get_running_loop()
                self.message_loop_task = loop.create_task(self._message_receiver_loop())
                self.logger.debug("🚀 메시지 수신 루프 시작 (listen() 요청)")
            except RuntimeError as e:
                self.logger.error(f"Event Loop 오류로 메시지 수신 루프 시작 실패: {e}")
                # Event Loop 문제 시에는 직접 대기하지 않고 즉시 종료
                return

        try:
            while self.is_connected:
                try:
                    # 큐에서 메시지 대기 (타임아웃 적용)
                    message = await asyncio.wait_for(message_queue.get(), timeout=self.message_timeout)
                    yield message
                except asyncio.TimeoutError:
                    # 타임아웃은 정상적인 상황 (메시지가 없을 때)
                    continue
                except Exception as e:
                    self.logger.error(f"메시지 큐 처리 오류: {e}")
                    break
        finally:
            # 정리: 큐 제거
            if message_queue in self._external_listeners:
                self._external_listeners.remove(message_queue)

            if self.auto_reconnect:
                await self._attempt_reconnect()

    def _infer_message_type(self, data: Dict[str, Any]) -> Optional[WebSocketDataType]:
        """메시지 타입 추론 (단순화된 로직)"""
        # 에러 메시지 체크
        if 'error' in data:
            self.logger.warning(f"WebSocket 에러 수신: {data.get('error')}")
            return None

        # 상태 메시지 체크 (UP 메시지 등)
        if 'status' in data:
            self.logger.debug(f"상태 메시지: {data.get('status')}")
            return None

        # 업비트 공식 type 필드 직접 사용
        if 'type' in data:
            msg_type = data['type']

            # 캔들 타입들을 통합 처리
            if msg_type.startswith('candle.'):
                return WebSocketDataType.CANDLE

            # 기본 타입 매핑
            type_mapping = {
                'ticker': WebSocketDataType.TICKER,
                'trade': WebSocketDataType.TRADE,
                'orderbook': WebSocketDataType.ORDERBOOK
            }

            return type_mapping.get(msg_type)

        # 필드 기반 추론 (fallback)
        if 'trade_price' in data and 'change_rate' in data and 'signed_change_rate' in data:
            return WebSocketDataType.TICKER
        elif 'trade_price' in data and 'trade_volume' in data and 'ask_bid' in data:
            return WebSocketDataType.TRADE
        elif 'orderbook_units' in data:
            return WebSocketDataType.ORDERBOOK
        elif 'opening_price' in data and 'trade_price' in data and 'candle_date_time_utc' in data:
            return WebSocketDataType.CANDLE
        else:
            # 디버그를 위해 알 수 없는 타입의 필드들 로깅
            field_list = list(data.keys())[:10]  # 처음 10개 필드만
            self.logger.debug(f"알 수 없는 메시지 타입: {field_list}")
            return None

    async def _handle_message(self, message: WebSocketMessage) -> None:
        """메시지 핸들러 실행"""
        handlers = self.message_handlers.get(message.type, [])
        for handler in handlers:
            try:
                await handler(message) if asyncio.iscoroutinefunction(handler) else handler(message)
            except Exception as e:
                self.logger.error(f"메시지 핸들러 실행 오류: {e}")

    async def _message_receiver_loop(self) -> None:
        """단일 메시지 수신 루프 - 모든 WebSocket recv를 여기서 처리"""
        if self._message_loop_running:
            self.logger.debug("메시지 수신 루프 이미 실행 중")
            return

        if not self.is_connected or not self.websocket:
            self.logger.error("WebSocket이 연결되지 않음")
            return

        self._message_loop_running = True
        self.logger.debug("메시지 수신 루프 시작")

        try:
            # 단일 recv 루프로 모든 메시지 처리
            async for raw_message in self.websocket:
                try:
                    self._stats['messages_received'] += 1

                    # JSON 파싱
                    data = json.loads(raw_message)

                    # 메시지 타입 추론
                    message_type = self._infer_message_type(data)
                    if not message_type:
                        continue

                    # Market 정보 추출 (여러 필드에서 확인)
                    market = data.get('market') or data.get('code') or data.get('symbol', 'UNKNOWN')

                    # 스트림 타입 추출 (업비트 API 스펙)
                    stream_type = None
                    if 'stream_type' in data:
                        stream_type_str = data['stream_type']
                        if stream_type_str == 'SNAPSHOT':
                            stream_type = StreamType.SNAPSHOT
                        elif stream_type_str == 'REALTIME':
                            stream_type = StreamType.REALTIME

                    # WebSocketMessage 객체 생성 (타입 안전성 검증 포함)
                    try:
                        message = WebSocketMessage(
                            type=message_type,
                            market=market,
                            data=data,
                            timestamp=datetime.now(),
                            raw_data=raw_message,
                            stream_type=stream_type
                        )
                    except ValueError as ve:
                        self.logger.warning(f"메시지 생성 실패: {ve}")
                        continue

                    self._stats['messages_processed'] += 1
                    self._stats['last_message_time'] = datetime.now()

                    # 1. 등록된 핸들러 실행
                    await self._handle_message(message)

                    # 2. 외부 listen() 제너레이터들에게 메시지 전달
                    if self._enable_external_listen and self._external_listeners:
                        for queue in self._external_listeners.copy():  # copy()로 안전한 순회
                            try:
                                queue.put_nowait(message)
                            except asyncio.QueueFull:
                                self.logger.warning("외부 listen 큐가 가득참")
                            except Exception as e:
                                self.logger.error(f"외부 listen 큐 오류: {e}")

                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON 파싱 실패: {e}")
                    self._stats['errors_count'] += 1
                except Exception as e:
                    self.logger.error(f"메시지 처리 오류: {e}")
                    self._stats['errors_count'] += 1

        except websockets.ConnectionClosed:
            self.logger.warning("WebSocket 연결이 닫혔습니다")
            self.is_connected = False
        except Exception as e:
            self.logger.error(f"메시지 수신 루프 오류: {e}")
            self._stats['errors_count'] += 1
        finally:
            self._message_loop_running = False
            self.message_loop_task = None
            self.logger.debug("메시지 수신 루프 종료")

    async def _keep_alive(self) -> None:
        """연결 유지 (PING 메시지)"""
        while self.is_connected and self.websocket:
            try:
                await asyncio.sleep(self.ping_interval)
                if self.is_connected and self.websocket:
                    await self.websocket.ping()
            except Exception as e:
                self.logger.warning(f"PING 전송 실패: {e}")
                break

    async def _attempt_reconnect(self) -> bool:
        """자동 재연결 시도 - 빠른 재연결"""
        if not self.auto_reconnect or self.reconnect_attempts >= self.max_reconnect_attempts:
            self.logger.warning(f"재연결 중단: attempts={self.reconnect_attempts}, max={self.max_reconnect_attempts}")
            return False

        self.reconnect_attempts += 1
        self.logger.info(f"재연결 시도 {self.reconnect_attempts}/{self.max_reconnect_attempts}")

        # 빠른 재연결을 위해 대기시간 단축 (최대 2초)
        wait_time = min(self.reconnect_attempts * 0.5, 2.0)
        await asyncio.sleep(wait_time)

        if await self.connect():
            # 기존 구독 복원 - Dict 통일 방식
            subscriptions = self._subscription_manager.get_subscriptions()
            for data_type_str, sub_data in subscriptions.items():
                try:
                    data_type = WebSocketDataType(data_type_str)
                    symbols = sub_data['symbols']
                    metadata = sub_data['metadata']

                    # 캔들 단위가 있는 경우 전달
                    candle_unit = metadata.get('candle_unit')
                    await self._subscribe(data_type, symbols, candle_unit)
                except Exception as e:
                    self.logger.warning(f"구독 복원 실패: {data_type_str} - {e}")

            self.logger.info("✅ 재연결 및 구독 복원 완료")
            return True

        return False

    async def unsubscribe(self) -> None:
        """모든 구독 해제 (기본 메서드)"""
        self._subscription_manager.clear()
        self.logger.info("모든 구독 해제됨")

    def get_subscriptions(self) -> Dict[str, Dict[str, Any]]:
        """모든 구독 정보 반환 - Dict 통일 정책"""
        return self._subscription_manager.get_subscriptions()

    def get_subscription_stats(self) -> Dict[str, Any]:
        """구독 및 연결 통계 정보 반환"""
        subscriptions = self._subscription_manager.get_subscriptions()
        return {
            'is_connected': self.is_connected,
            'subscription_types': list(subscriptions.keys()),
            'total_symbols': sum(len(sub['symbols']) for sub in subscriptions.values()),
            'connection_start_time': self._stats['connection_start_time'],
            'messages_received': self._stats['messages_received'],
            'messages_processed': self._stats['messages_processed'],
            'errors_count': self._stats['errors_count'],
            'last_message_time': self._stats['last_message_time']
        }

    # 🆕 스트림 타입 활용 메서드들
    def add_snapshot_handler(self, data_type: WebSocketDataType, handler: Callable[[WebSocketMessage], None]) -> None:
        """스냅샷 전용 핸들러 등록 (타임프레임 완료 시에만 호출)"""
        def snapshot_filter(message: WebSocketMessage):
            if message.is_snapshot():
                handler(message)

        self.add_message_handler(data_type, snapshot_filter)
        self.logger.debug(f"스냅샷 핸들러 등록: {data_type.value}")

    def add_realtime_handler(self, data_type: WebSocketDataType, handler: Callable[[WebSocketMessage], None]) -> None:
        """실시간 전용 핸들러 등록 (진행 중 업데이트만 호출)"""
        def realtime_filter(message: WebSocketMessage):
            if message.is_realtime():
                handler(message)

        self.add_message_handler(data_type, realtime_filter)
        self.logger.debug(f"실시간 핸들러 등록: {data_type.value}")

    def add_candle_completion_handler(self, handler: Callable[[WebSocketMessage], None]) -> None:
        """캔들 완성 전용 핸들러 (타임프레임 완료 시에만 호출)"""
        def candle_completion_filter(message: WebSocketMessage):
            if message.type == WebSocketDataType.CANDLE and message.is_snapshot():
                self.logger.info(f"🕐 캔들 완성: {message.market} - {message.data.get('candle_date_time_utc', 'N/A')}")
                handler(message)

        self.add_message_handler(WebSocketDataType.CANDLE, candle_completion_filter)
        self.logger.debug("캔들 완성 핸들러 등록 (SNAPSHOT 전용)")

    async def close(self) -> None:
        """연결 종료 (disconnect 별칭)"""
        await self.disconnect()

    async def __aenter__(self):
        """async with 컨텍스트 매니저 진입"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async with 컨텍스트 매니저 종료"""
        await self.disconnect()

    def _format_symbols_for_log(self, symbols: List[str], max_display: int = 3) -> str:
        """심볼 목록을 로그에 적합하게 포맷팅

        Args:
            symbols: 심볼 목록
            max_display: 최대 표시할 심볼 수 (앞/뒤)

        Returns:
            포맷팅된 문자열 (예: "[KRW-BTC, KRW-ETH, ..., KRW-DOT] (총 189개)")
        """
        if not symbols:
            return "[]"

        total_count = len(symbols)

        # 심볼이 적으면 모두 표시
        if total_count <= max_display * 2:
            return f"[{', '.join(symbols)}]"

        # 심볼이 많으면 처음 3개 + ... + 마지막 1개 + 총 개수
        first_part = symbols[:max_display]
        last_part = symbols[-1:]  # 마지막 1개만

        formatted = f"[{', '.join(first_part)}, ..., {', '.join(last_part)}] (총 {total_count}개)"
        return formatted
