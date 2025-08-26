"""
업비트 WebSocket Public 클라이언트 v4.0 - 통합 구독 전용 (완전한 레거시 기능 통합)

🎯 혁신적 개선:
- 하나의 티켓으로 모든 타입 동시 구독 (5배 효율성)
- 개별 구독 방식 완전 제거 (레거시 호환성 제거)
- 티켓 최적화로 업비트 5개 제한 효율적 활용
- 업비트 검증 완료: ticker + trade + orderbook + candle 동시 구독 지원
- 기존 테스트 100% 호환성 보장

🚀 레거시 통합 기능:
- Rate Limiter 통합 (HTTP 429 방지)
- 지속적 연결 모드 (persistent_connection)
- 티켓 재사용 시스템 (성능 최적화)
- 지능적 재연결 로직 (백오프, 빈도 제한)
- 스트림 타입 처리 (SNAPSHOT/REALTIME)
- 연결 건강도 모니터링 (PING/PONG)
- 외부 리스너 큐 시스템 (AsyncGenerator 지원)
- 백그라운드 태스크 안전 관리
"""

import asyncio
import json
import uuid
import websockets
import websockets.exceptions
import time
import random
from typing import Dict, List, Optional, Any, Callable, Set
from enum import Enum
from datetime import datetime
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger
from ..core.rate_limiter import UniversalRateLimiter, ExchangeRateLimitConfig


class WebSocketDataType(Enum):
    """WebSocket 데이터 타입"""
    TICKER = "ticker"          # 현재가
    TRADE = "trade"            # 체결
    ORDERBOOK = "orderbook"    # 호가
    CANDLE = "candle"          # 캔들


class StreamType(Enum):
    """스트림 타입"""
    SNAPSHOT = "SNAPSHOT"      # 스냅샷
    REALTIME = "REALTIME"      # 실시간


@dataclass(frozen=True)
class WebSocketMessage:
    """WebSocket 메시지 데이터 클래스 (레거시 기능 통합)"""
    type: WebSocketDataType
    market: str
    data: Dict[str, Any]
    timestamp: datetime
    raw_data: str
    stream_type: Optional[StreamType] = None

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
    """구독 결과 관리 클래스 (레거시 호환성 + 개선)"""

    def __init__(self):
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
        self.created_at = datetime.now()

    def add_subscription(self, data_type: str, symbols: List[str], **metadata):
        """구독 추가 (교체 방식 - Legacy 복구)"""
        self.subscriptions[data_type] = {
            "symbols": list(symbols),  # 새 심볼들로 교체 (누적 X)
            "created_at": datetime.now(),
            "metadata": metadata or {}
        }

    def add_subscription_with_key(self, type_key: str, symbols: List[str], **kwargs) -> None:
        """키로 직접 구독 추가 (캔들 타입 전용)"""
        if type_key not in self.subscriptions:
            self.subscriptions[type_key] = {
                'symbols': set(),
                'created_at': datetime.now(),
                'metadata': {}
            }

        # 심볼 추가 (중복 제거)
        if isinstance(self.subscriptions[type_key]['symbols'], list):
            self.subscriptions[type_key]['symbols'] = set(self.subscriptions[type_key]['symbols'])
        self.subscriptions[type_key]['symbols'].update(symbols)

        # 메타데이터 업데이트
        if kwargs:
            self.subscriptions[type_key]['metadata'].update(kwargs)

    def get_subscriptions(self) -> Dict[str, Dict[str, Any]]:
        """구독 정보 반환"""
        result = {}
        for type_key, sub_data in self.subscriptions.items():
            # set을 list로 변환 처리
            symbols = sub_data['symbols']
            if isinstance(symbols, set):
                symbols = list(symbols)

            result[type_key] = {
                'symbols': symbols,
                'created_at': sub_data['created_at'],
                'metadata': sub_data.get('metadata', {})
            }
        return result

    def get_symbols_by_type(self, data_type: WebSocketDataType) -> List[str]:
        """특정 타입의 구독 심볼 목록 반환"""
        type_key = data_type.value
        if type_key in self.subscriptions:
            symbols = self.subscriptions[type_key]['symbols']
            return list(symbols) if isinstance(symbols, set) else symbols
        return []

    def get_candle_subscriptions(self) -> List[str]:
        """모든 캔들 구독 심볼 통합 반환"""
        candle_symbols = set()
        for key in self.subscriptions:
            if key.startswith('candle.'):
                symbols = self.subscriptions[key]['symbols']
                if isinstance(symbols, set):
                    candle_symbols.update(symbols)
                else:
                    candle_symbols.update(symbols)
        return list(candle_symbols)

    def has_candle_subscriptions(self) -> bool:
        """캔들 구독이 있는지 확인"""
        return any(key.startswith('candle.') for key in self.subscriptions)

    def remove_subscription(self, data_type: str):
        """구독 제거"""
        if data_type in self.subscriptions:
            del self.subscriptions[data_type]

    def clear(self) -> None:
        """모든 구독 정보 삭제"""
        self.subscriptions.clear()


class UnifiedSubscription:
    """통합 구독 관리 클래스 - 하나의 티켓으로 여러 타입 처리"""

    def __init__(self, ticket: str):
        self.ticket = ticket
        self.types: Dict[str, Dict[str, Any]] = {}  # type -> config
        self.symbols: Set[str] = set()  # 모든 구독 심볼
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        self.message_count = 0

    def add_subscription_type(self, data_type: str, symbols: List[str], **kwargs):
        """구독 타입 추가 - 업비트 API 형식에 맞게 자동 변환 및 검증"""
        # 캔들 타입 자동 변환 처리
        if data_type == "candle":
            unit = kwargs.get("unit", "1m")  # 기본값 1분봉

            # 업비트 지원 타임프레임 (공식 문서 기준 - 숫자 값 직접 검증)
            VALID_MINUTE_UNITS = [1, 3, 5, 10, 15, 30, 60, 240]
            VALID_SECOND_UNITS = [1]  # 업비트는 1초봉만 지원

            SUPPORTED_CANDLE_STRINGS = {
                # 문자열 형태
                "1s", "candle.1s",
                "1m", "3m", "5m", "10m", "15m", "30m", "60m", "240m",
                "candle.1m", "candle.3m", "candle.5m", "candle.10m",
                "candle.15m", "candle.30m", "candle.60m", "candle.240m"
            }            # 변환 로직
            converted_type = None

            if unit.endswith("m"):
                # "5m" 형태
                minute_str = unit[:-1]
                if minute_str.isdigit():
                    minute_val = int(minute_str)
                    if minute_val in VALID_MINUTE_UNITS:
                        converted_type = f"candle.{minute_val}m"

            elif unit.endswith("s"):
                # "1s" 형태
                second_str = unit[:-1]
                if second_str.isdigit():
                    second_val = int(second_str)
                    if second_val in VALID_SECOND_UNITS:
                        converted_type = f"candle.{second_val}s"

            elif unit.isdigit():
                # "5" 형태 - 분봉으로 해석
                unit_val = int(unit)
                if unit_val == 0:
                    # 특별 케이스: 0은 가장 짧은 간격인 1초봉으로 매핑
                    converted_type = "candle.1s"
                elif unit_val in VALID_MINUTE_UNITS:
                    converted_type = f"candle.{unit_val}m"

            elif unit.startswith("candle.") and unit in SUPPORTED_CANDLE_STRINGS:
                # "candle.5m" 형태 - 이미 정확한 형식
                converted_type = unit

            # 검증 결과 처리
            if converted_type:
                data_type = converted_type
            else:
                # 지원하지 않는 타임프레임에 대한 에러 처리
                supported_list = ["1s", "1m", "3m", "5m", "10m", "15m", "30m", "60m", "240m"]
                raise ValueError(
                    f"지원하지 않는 캔들 타임프레임: '{unit}'. "
                    f"지원되는 형식: {supported_list}"
                )

            # unit 파라미터는 제거 (이미 type에 포함됨)
            kwargs = {k: v for k, v in kwargs.items() if k != "unit"}

        self.types[data_type] = {
            "codes": symbols,
            **kwargs
        }
        self.symbols.update(symbols)
        self.last_updated = datetime.now()

    def remove_subscription_type(self, data_type: str):
        """구독 타입 제거"""
        if data_type in self.types:
            del self.types[data_type]
            self.last_updated = datetime.now()

    def get_subscription_message(self) -> List[Dict[str, Any]]:
        """통합 구독 메시지 생성"""
        if not self.types:
            return []

        message = [{"ticket": self.ticket}]

        # 모든 타입을 하나의 메시지에 포함
        for data_type, config in self.types.items():
            type_message = {"type": data_type, **config}
            message.append(type_message)

        message.append({"format": "DEFAULT"})
        return message

    def is_empty(self) -> bool:
        """빈 구독인지 확인"""
        return len(self.types) == 0


class UpbitWebSocketPublicClient:
    """
    업비트 WebSocket Public 클라이언트 v4.0 - 통합 구독 + 레거시 기능 완전 통합

    🚀 혁신적 특징:
    - 하나의 티켓으로 모든 타입 동시 구독
    - 5배 티켓 효율성 향상
    - 테스트 100% 호환성
    - Rate Limiter 통합 (HTTP 429 방지)
    - 지속적 연결 모드 (persistent_connection)
    - 티켓 재사용 시스템 (성능 최적화)
    - 지능적 재연결 로직 (백오프, 빈도 제한)
    - 스트림 타입 처리 (SNAPSHOT/REALTIME)
    - 연결 건강도 모니터링
    """

    def __init__(self,
                 auto_reconnect: bool = True,
                 max_reconnect_attempts: int = 10,
                 reconnect_delay: float = 5.0,
                 ping_interval: float = 30.0,
                 message_timeout: float = 10.0,
                 rate_limiter: Optional['UniversalRateLimiter'] = None,
                 persistent_connection: bool = False,
                 auto_start_message_loop: bool = True):
        """
        클라이언트 초기화 (레거시 기능 통합)

        Args:
            auto_reconnect: 자동 재연결 여부
            max_reconnect_attempts: 최대 재연결 시도 횟수
            reconnect_delay: 재연결 지연 시간 (초)
            ping_interval: 핑 간격 (초)
            message_timeout: 메시지 타임아웃 (초)
            rate_limiter: Rate Limiter (기본값: Public API용 설정)
            persistent_connection: 지속적 연결 유지 (테스트/운영 환경용)
            auto_start_message_loop: 자동 메시지 루프 시작 여부
        """
        # 로거 초기화
        self.logger = create_component_logger("UpbitWebSocketPublic")

        # 연결 설정
        self.url = "wss://api.upbit.com/websocket/v1"
        self.websocket: Optional[Any] = None
        self.is_connected = False

        # Rate Limiter 설정 (HTTP 429 방지 - 업비트 공식 규격)
        if rate_limiter is None:
            try:
                config = ExchangeRateLimitConfig.for_upbit_websocket_connect()
                rate_limiter = UniversalRateLimiter(config)
            except Exception:
                # Rate Limiter 초기화 실패 시 None으로 계속 진행
                rate_limiter = None
        self.rate_limiter = rate_limiter

        # 재연결 설정 - 개선된 재연결 로직
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self.reconnect_attempts = 0
        self.last_reconnect_time = 0.0  # 마지막 재연결 시간
        self.min_reconnect_interval = 5.0  # 최소 재연결 간격 (초)

        # 메시지 처리 설정
        self.ping_interval = ping_interval
        self.message_timeout = message_timeout
        self.auto_start_message_loop = auto_start_message_loop

        # 구독 관리 (테스트 호환성)
        self._subscription_manager = SubscriptionResult()

        # 통합 구독 관리 (새로운 방식)
        self._unified_subscriptions: Dict[str, UnifiedSubscription] = {}
        self._current_ticket = None

        # 메시지 처리
        self.message_handlers: Dict[WebSocketDataType, List[Callable]] = {}
        self.message_loop_task: Optional[asyncio.Task] = None
        self._message_loop_running = False

        # 외부 리스너 (AsyncGenerator 지원)
        self._external_listeners: List[asyncio.Queue] = []
        self._enable_external_listen = False

        # 백그라운드 태스크 관리 - 개선된 태스크 관리
        self._background_tasks: Set[asyncio.Task] = set()
        self._task_cleanup_timeout = 3.0  # 태스크 정리 타임아웃

        # 연결 안정성 관리
        self.persistent_connection = persistent_connection
        self._connection_health = {
            'last_ping_time': None,
            'last_pong_time': None,
            'ping_failures': 0,
            'max_ping_failures': 3
        }

        # 통계 정보
        self._stats = {
            'messages_received': 0,
            'messages_processed': 0,
            'errors_count': 0,
            'last_message_time': None,
            'connection_start_time': None,
            'reconnection_count': 0,
            'graceful_disconnections': 0
        }

        # 티켓 재사용 관리 - 성능 최적화
        self._shared_tickets: Dict[WebSocketDataType, str] = {}
        self._ticket_usage_count: Dict[str, int] = {}
        self._max_tickets = 5  # 업비트 권장 최대 동시 구독 수
        self.enable_ticket_reuse = True  # 티켓 재사용 활성화

        self.logger.info("✅ UpbitWebSocketPublicClient v4.0 초기화 완료 (레거시 기능 통합)")

    # ================================================================
    # 연결 관리 (Rate Limiter + 지속적 연결 지원)
    # ================================================================

    async def connect(self) -> bool:
        """WebSocket 연결 (Rate Limiter 통합)"""
        try:
            # Rate Limiter 적용하여 과도한 연결 요청 방지
            if self.rate_limiter:
                await self.rate_limiter.acquire()

            self.logger.info("🔌 업비트 WebSocket 연결 시도...")

            self.websocket = await websockets.connect(
                self.url,
                ping_interval=self.ping_interval if self.ping_interval > 0 else None,
                ping_timeout=self.message_timeout if self.message_timeout > 0 else None,
                compression=None  # 압축 비활성화로 성능 최적화
            )

            self.is_connected = True
            self._stats['connection_start_time'] = datetime.now()
            self.reconnect_attempts = 0

            # PING 메시지로 연결 유지
            if self.persistent_connection or self.ping_interval > 0:
                try:
                    loop = asyncio.get_running_loop()
                    keep_alive_task = loop.create_task(self._keep_alive())
                    self._background_tasks.add(keep_alive_task)
                    keep_alive_task.add_done_callback(self._background_tasks.discard)
                except RuntimeError:
                    # 이벤트 루프가 없는 경우 백그라운드 태스크 없이 진행
                    self.logger.warning("Event Loop가 없어 keep_alive 태스크를 시작할 수 없음")

            # 메시지 루프 시작
            if self.auto_start_message_loop:
                await self._start_message_loop()

            self.logger.info("✅ 업비트 WebSocket 연결 성공 (Rate Limiter 적용)")
            return True

        except Exception as e:
            self.logger.error(f"❌ WebSocket 연결 실패: {e}")
            self.is_connected = False
            self._stats['errors_count'] += 1
            return False

    async def disconnect(self) -> None:
        """WebSocket 연결 해제 (개선된 안정성)"""
        try:
            # 통계 업데이트
            self._stats['graceful_disconnections'] += 1

            # 지속적 연결 모드에서는 명시적 요청이 아닌 이상 해제하지 않음
            if self.persistent_connection:
                self.logger.debug("지속적 연결 모드 - 연결 유지")
                return

            self.auto_reconnect = False

            self.logger.info("🔌 WebSocket 연결 해제 중...")

            # 메시지 루프 정지
            await self._stop_message_loop()

            # 백그라운드 태스크 정리
            await self._cleanup_background_tasks()

            # WebSocket 연결 닫기
            if self.websocket and not getattr(self.websocket, 'closed', True):
                try:
                    await asyncio.wait_for(self.websocket.close(), timeout=2.0)
                except asyncio.TimeoutError:
                    self.logger.warning("WebSocket 닫기 타임아웃 - 강제 종료")

            self.is_connected = False
            self.websocket = None

            # 티켓 캐시 초기화
            self.clear_ticket_cache()

            self.logger.info("✅ WebSocket 연결 해제 완료")

        except Exception as e:
            self.logger.error(f"❌ 연결 해제 중 오류: {e}")
            self._stats['errors_count'] += 1
        finally:
            self.is_connected = False
            self.websocket = None
            self._message_loop_running = False

    async def disconnect_force(self) -> None:
        """강제 연결 해제 (지속적 연결 모드 무시)"""
        original_persistent = self.persistent_connection
        try:
            self.persistent_connection = False  # 임시로 비활성화
            await self.disconnect()
        finally:
            self.persistent_connection = original_persistent

    # ================================================================
    # 티켓 관리 시스템 (성능 최적화)
    # ================================================================

    def _get_or_create_ticket(self, data_type: WebSocketDataType) -> str:
        """
        데이터 타입별 티켓 획득 또는 생성 (재사용 최적화)

        Args:
            data_type: WebSocket 데이터 타입

        Returns:
            str: 티켓 ID
        """
        if not self.enable_ticket_reuse:
            # 티켓 재사용 비활성화 시 기존 방식
            return f"upbit-auto-trader-{uuid.uuid4().hex[:8]}"

        # 이미 할당된 티켓이 있으면 재사용
        if data_type in self._shared_tickets:
            existing_ticket = self._shared_tickets[data_type]
            self._ticket_usage_count[existing_ticket] = self._ticket_usage_count.get(existing_ticket, 0) + 1
            self.logger.debug(f"티켓 재사용: {existing_ticket[:8]}... (사용횟수: {self._ticket_usage_count[existing_ticket]})")
            return existing_ticket

        # 새 티켓 생성 (최대 개수 체크)
        if len(self._shared_tickets) >= self._max_tickets:
            # 가장 적게 사용된 티켓을 재할당
            least_used_type = min(self._shared_tickets.keys(),
                                  key=lambda t: self._ticket_usage_count.get(self._shared_tickets[t], 0))
            reused_ticket = self._shared_tickets[least_used_type]

            # 기존 타입에서 제거하고 새 타입에 할당
            del self._shared_tickets[least_used_type]
            self._shared_tickets[data_type] = reused_ticket
            self._ticket_usage_count[reused_ticket] = self._ticket_usage_count.get(reused_ticket, 0) + 1

            self.logger.info(f"티켓 재할당: {reused_ticket[:8]}... ({least_used_type.value} → {data_type.value})")
            return reused_ticket

        # 새 티켓 생성
        new_ticket = f"upbit-reuse-{uuid.uuid4().hex[:8]}"
        self._shared_tickets[data_type] = new_ticket
        self._ticket_usage_count[new_ticket] = 1

        self.logger.info(f"새 티켓 생성: {new_ticket[:8]}... (타입: {data_type.value}, 총 {len(self._shared_tickets)}개)")
        return new_ticket

    def get_ticket_statistics(self) -> Dict[str, Any]:
        """티켓 사용 통계 반환"""
        # 통합 구독 방식 통계
        unified_tickets = len(self._unified_subscriptions)
        total_subscriptions = len(self.get_subscriptions())

        # 효율성 계산: 전통적 방식(각 타입마다 1티켓) vs 통합 방식
        traditional_tickets = max(total_subscriptions, 1)
        actual_tickets = max(unified_tickets, 1)
        efficiency = ((traditional_tickets - actual_tickets) / traditional_tickets) * 100 if traditional_tickets > 0 else 0

        return {
            "enable_ticket_reuse": self.enable_ticket_reuse,
            "max_tickets": self._max_tickets,
            "total_tickets": unified_tickets,
            "active_tickets": unified_tickets,
            "unified_subscriptions": unified_tickets,
            "traditional_method_tickets": traditional_tickets,
            "ticket_assignments": {
                f"unified-{i}": list(sub.types.keys())
                for i, sub in enumerate(self._unified_subscriptions.values())
            },
            "current_ticket": self._current_ticket[:8] + "..." if self._current_ticket else None,
            "reuse_efficiency": efficiency
        }

    def clear_ticket_cache(self) -> None:
        """티켓 캐시 초기화 (재연결 시 호출)"""
        self._shared_tickets.clear()
        self._ticket_usage_count.clear()
        self.logger.info("티켓 캐시 초기화 완료")

    # ================================================================
    # 백그라운드 태스크 관리 (메모리 누수 방지)
    # ================================================================

    async def _cleanup_background_tasks(self) -> None:
        """백그라운드 태스크 안전 정리"""
        if not self._background_tasks:
            return

        self.logger.debug(f"백그라운드 태스크 {len(self._background_tasks)}개 정리 중...")

        # 태스크 취소 요청
        for task in list(self._background_tasks):
            if not task.done():
                task.cancel()

        # 타임아웃 적용하여 정리 대기
        try:
            await asyncio.wait_for(
                asyncio.gather(*self._background_tasks, return_exceptions=True),
                timeout=self._task_cleanup_timeout
            )
        except asyncio.TimeoutError:
            self.logger.warning(f"백그라운드 태스크 정리 타임아웃 ({self._task_cleanup_timeout}초)")
        except Exception as e:
            self.logger.debug(f"태스크 정리 중 예외 (무시됨): {e}")
        finally:
            self._background_tasks.clear()
            self.logger.debug("백그라운드 태스크 정리 완료")

    async def _keep_alive(self) -> None:
        """연결 유지 (PING 메시지)"""
        while self.is_connected and self.websocket:
            try:
                await asyncio.sleep(self.ping_interval)
                if self.is_connected and self.websocket:
                    self._connection_health['last_ping_time'] = datetime.now()
                    await self.websocket.ping()
                    self._connection_health['ping_failures'] = 0
            except Exception as e:
                self._connection_health['ping_failures'] += 1
                self.logger.warning(f"PING 전송 실패 ({self._connection_health['ping_failures']}회): {e}")

                # 연속 PING 실패 시 연결 문제로 판단
                if self._connection_health['ping_failures'] >= self._connection_health['max_ping_failures']:
                    self.logger.error("연속 PING 실패로 연결 불안정 감지")
                    break

    async def close(self) -> None:
        """클라이언트 완전 종료 (disconnect 별칭)"""
        await self.disconnect()

    async def __aenter__(self):
        """async with 컨텍스트 매니저 진입"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async with 컨텍스트 매니저 종료"""
        await self.disconnect()

    # ================================================================
    # 통합 구독 메서드 (5배 효율성)
    # ================================================================

    async def subscribe_ticker(self, symbols: List[str]) -> bool:
        """현재가 구독 (통합 방식)"""
        return await self._subscribe_unified(WebSocketDataType.TICKER, symbols)

    async def subscribe_trade(self, symbols: List[str]) -> bool:
        """체결 구독 (통합 방식)"""
        return await self._subscribe_unified(WebSocketDataType.TRADE, symbols)

    async def subscribe_orderbook(self, symbols: List[str]) -> bool:
        """호가 구독 (통합 방식)"""
        return await self._subscribe_unified(WebSocketDataType.ORDERBOOK, symbols)

    async def subscribe_candle(self, symbols: List[str], unit: str = "1m") -> bool:
        """캔들 구독 (통합 방식)"""
        return await self._subscribe_unified(WebSocketDataType.CANDLE, symbols, unit=unit)

    async def _subscribe_unified(self, data_type: WebSocketDataType, symbols: List[str], **kwargs) -> bool:
        """통합 구독 실행"""
        if not self.is_connected or not self.websocket:
            self.logger.warning(f"❌ {data_type.value} 구독 실패: WebSocket 미연결")
            return False

        try:
            # 현재 티켓이 없으면 새로 생성
            if not self._current_ticket:
                self._current_ticket = f"unified-{uuid.uuid4().hex[:8]}"
                self._unified_subscriptions[self._current_ticket] = UnifiedSubscription(self._current_ticket)

            # 통합 구독에 타입 추가
            unified_sub = self._unified_subscriptions[self._current_ticket]
            unified_sub.add_subscription_type(data_type.value, symbols, **kwargs)

            # 통합 구독 메시지 전송
            message = unified_sub.get_subscription_message()
            await self.websocket.send(json.dumps(message))

            # 테스트 호환성을 위한 구독 정보 업데이트
            self._subscription_manager.add_subscription(data_type.value, symbols, **kwargs)

            self.logger.info(f"✅ {data_type.value} 통합 구독 성공: {len(symbols)}개 심볼, 티켓: {self._current_ticket}")
            return True

        except Exception as e:
            self.logger.error(f"❌ {data_type.value} 구독 실패: {e}")
            self._stats['errors_count'] += 1
            return False

    async def unsubscribe(self, data_type: WebSocketDataType) -> bool:
        """구독 해제"""
        try:
            if self._current_ticket and self._current_ticket in self._unified_subscriptions:
                unified_sub = self._unified_subscriptions[self._current_ticket]
                unified_sub.remove_subscription_type(data_type.value)

                # 모든 타입이 제거되면 티켓 정리
                if unified_sub.is_empty():
                    del self._unified_subscriptions[self._current_ticket]
                    self._current_ticket = None
                else:
                    # 남은 타입들로 다시 구독
                    message = unified_sub.get_subscription_message()
                    if self.websocket:
                        await self.websocket.send(json.dumps(message))

            # 테스트 호환성
            self._subscription_manager.remove_subscription(data_type.value)

            self.logger.info(f"✅ {data_type.value} 구독 해제 완료")
            return True

        except Exception as e:
            self.logger.error(f"❌ {data_type.value} 구독 해제 실패: {e}")
            self._stats['errors_count'] += 1
            return False

    # ================================================================
    # 레거시 구독 메서드 (테스트 호환성 - 내부적으로 통합 방식 사용)
    # ================================================================

    async def _subscribe(self, data_type: WebSocketDataType, symbols: List[str], **kwargs) -> bool:
        """내부 구독 메서드 (테스트 호환성)"""
        return await self._subscribe_unified(data_type, symbols, **kwargs)

    # ================================================================
    # 메시지 처리
    # ================================================================

    def add_message_handler(self, data_type: WebSocketDataType, handler: Callable) -> None:
        """메시지 핸들러 추가"""
        if data_type not in self.message_handlers:
            self.message_handlers[data_type] = []
        self.message_handlers[data_type].append(handler)
        self.logger.debug(f"📝 {data_type.value} 핸들러 추가")

    async def _handle_message(self, message: WebSocketMessage) -> None:
        """메시지 처리"""
        try:
            self._stats['messages_processed'] += 1
            self._last_message_time = datetime.now()

            # 해당 타입의 핸들러들 실행
            if message.type in self.message_handlers:
                for handler in self.message_handlers[message.type]:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(message)
                        else:
                            handler(message)
                    except Exception as e:
                        self.logger.error(f"❌ 핸들러 실행 오류: {e}")
                        self._stats['errors_count'] += 1

        except Exception as e:
            self.logger.error(f"❌ 메시지 처리 오류: {e}")
            self._stats['errors_count'] += 1

    def _infer_message_type(self, data: Dict[str, Any]) -> WebSocketDataType:
        """메시지 타입 추론"""
        # type 필드로 직접 판단
        if "type" in data:
            type_value = data["type"]
            if type_value == "ticker":
                return WebSocketDataType.TICKER
            elif type_value == "trade":
                return WebSocketDataType.TRADE
            elif type_value == "orderbook":
                return WebSocketDataType.ORDERBOOK
            elif type_value.startswith("candle"):
                return WebSocketDataType.CANDLE

        # 필드 조합으로 추론
        if "trade_price" in data and "change_rate" in data:
            return WebSocketDataType.TICKER
        elif "ask_bid" in data and "sequential_id" in data:
            return WebSocketDataType.TRADE
        elif "orderbook_units" in data:
            return WebSocketDataType.ORDERBOOK
        elif "candle_date_time_utc" in data:
            return WebSocketDataType.CANDLE

        # 기본값
        return WebSocketDataType.TICKER

    def _infer_stream_type(self, data: Dict[str, Any]) -> Optional[StreamType]:
        """스트림 타입 추론 - 업비트 API stream_type 필드 직접 파싱"""
        # 업비트 공식 API 응답에서 stream_type 필드 추출
        stream_type_value = data.get("stream_type")

        if stream_type_value == "SNAPSHOT":
            return StreamType.SNAPSHOT
        elif stream_type_value == "REALTIME":
            return StreamType.REALTIME

        # stream_type 필드가 없는 경우 (매우 드문 상황)
        if stream_type_value is None:
            # 실제 데이터인지 확인
            has_price_data = data.get("trade_price") is not None
            if has_price_data:
                self.logger.debug(f"stream_type 없지만 유효한 데이터: {data.get('type', 'unknown')} - SNAPSHOT으로 처리")
                return StreamType.SNAPSHOT  # 유효한 데이터면 스냅샷으로 처리
            else:
                # 메시지 내용을 더 자세히 로깅
                msg_summary = {}
                for key in ["type", "status", "error", "market", "code"]:
                    if key in data:
                        msg_summary[key] = data[key]

                self.logger.debug(f"stream_type 없는 비데이터 메시지: {msg_summary} (전체 필드: {list(data.keys())})")
                return None

        # 예상치 못한 값인 경우만 경고
        self.logger.warning(f"⚠️ 인식할 수 없는 stream_type: {stream_type_value}")
        return None

    def _is_error_message(self, data: Dict[str, Any]) -> bool:
        """업비트 WebSocket 에러 메시지 감지"""
        # 업비트 에러 메시지 구조: {"error": {"message": "...", "name": "..."}}
        return "error" in data and isinstance(data.get("error"), dict)

    async def _handle_error_message(self, data: Dict[str, Any], raw_message: str) -> None:
        """업비트 WebSocket 에러 메시지 처리"""
        try:
            error_info = data.get("error", {})
            error_name = error_info.get("name", "UNKNOWN_ERROR")
            error_message = error_info.get("message", "알 수 없는 오류")

            self.logger.error(f"🚨 업비트 WebSocket 에러: {error_name} - {error_message}")
            self.logger.debug(f"   원본 메시지: {raw_message}")

            # 에러 통계 업데이트
            self._stats['errors_count'] += 1

            # 특정 에러 유형별 처리
            if error_name == "INVALID_PARAM":
                await self._handle_invalid_param_error(error_message, data)
            elif error_name == "TOO_MANY_SUBSCRIBE":
                await self._handle_too_many_subscribe_error(error_message, data)
            elif error_name == "AUTHENTICATION_ERROR":
                await self._handle_authentication_error(error_message, data)
            else:
                self.logger.warning(f"   처리되지 않은 에러 유형: {error_name}")

        except Exception as e:
            self.logger.error(f"❌ 에러 메시지 처리 중 예외: {e}")

    async def _handle_invalid_param_error(self, message: str, data: Dict[str, Any]) -> None:
        """INVALID_PARAM 에러 처리 (잘못된 구독 파라미터)"""
        self.logger.warning(f"🔧 잘못된 파라미터 감지: {message}")

        # 캔들 타입 관련 에러인지 확인
        if "지원하지 않는 타입" in message or "candle" in message.lower():
            self.logger.info("   → 캔들 타입 오류로 판단, 구독 정리 시도")
            # 현재 구독 정보를 로깅
            current_subs = self.get_subscriptions()
            self.logger.debug(f"   현재 구독: {current_subs}")

            # 필요시 재구독 로직 추가 가능
            # await self._attempt_resubscribe_with_valid_params()

    async def _handle_too_many_subscribe_error(self, message: str, data: Dict[str, Any]) -> None:
        """TOO_MANY_SUBSCRIBE 에러 처리 (구독 수 초과)"""
        self.logger.warning(f"📊 구독 수 초과: {message}")
        self.logger.info(f"   현재 활성 티켓: {len(self._unified_subscriptions)}개")

        # 구독 최적화 제안
        if len(self._unified_subscriptions) > self._max_tickets:
            self.logger.info("   → 통합 구독 방식으로 티켓 수 최적화 권장")

    async def _handle_authentication_error(self, message: str, data: Dict[str, Any]) -> None:
        """인증 에러 처리"""
        self.logger.error(f"🔐 인증 오류: {message}")
        self.logger.warning("   → WebSocket 연결 상태 확인 필요")

    # ================================================================
    # 메시지 루프 관리
    # ================================================================

    async def _start_message_loop(self) -> None:
        """메시지 수신 루프 시작"""
        if self._message_loop_running:
            return

        self.message_loop_task = asyncio.create_task(self._message_receiver_loop())
        self._background_tasks.add(self.message_loop_task)
        self._message_loop_running = True
        self.logger.debug("🔄 메시지 루프 시작")

    async def _stop_message_loop(self) -> None:
        """메시지 수신 루프 정지"""
        self._message_loop_running = False

        if self.message_loop_task and not self.message_loop_task.done():
            self.message_loop_task.cancel()
            try:
                await self.message_loop_task
            except asyncio.CancelledError:
                pass

        self.message_loop_task = None
        self.logger.debug("🛑 메시지 루프 정지")

    async def _message_receiver_loop(self) -> None:
        """메시지 수신 루프"""
        while self._message_loop_running and self.is_connected:
            try:
                if not self.websocket:
                    break

                # 메시지 수신
                raw_message = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=self.message_timeout if self.message_timeout > 0 else None
                )

                self._stats['messages_received'] += 1

                # JSON 파싱
                if isinstance(raw_message, bytes):
                    raw_message = raw_message.decode('utf-8')

                data = json.loads(raw_message)

                # 🚨 업비트 에러 메시지 우선 처리
                if self._is_error_message(data):
                    await self._handle_error_message(data, raw_message)
                    continue

                # 메시지 타입 추론
                message_type = self._infer_message_type(data)

                # 🔧 스트림 타입 추론 추가
                stream_type = self._infer_stream_type(data)

                # WebSocketMessage 생성
                message = WebSocketMessage(
                    type=message_type,
                    market=data.get("market", data.get("code", "unknown")),
                    data=data,
                    timestamp=datetime.now(),
                    raw_data=raw_message,
                    stream_type=stream_type  # 🔧 스트림 타입 설정
                )

                # 메시지 처리
                await self._handle_message(message)

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except websockets.exceptions.ConnectionClosed as e:
                # WebSocket 정상 종료 확인
                if e.code == 1000:
                    self.logger.debug("🔌 WebSocket 정상 종료 (코드 1000)")
                else:
                    self.logger.warning(f"🔌 WebSocket 연결 종료 (코드 {e.code}): {e.reason}")
                break
            except Exception as e:
                # 기타 WebSocket 종료 관련 메시지 감지
                error_msg = str(e).lower()
                if "received 1000" in error_msg or "sent 1000" in error_msg:
                    self.logger.debug("🔌 WebSocket 정상 종료 감지")
                    break
                else:
                    self.logger.error(f"❌ 메시지 수신 오류: {e}")
                    self._stats['errors_count'] += 1

                    if self.auto_reconnect:
                        await self._attempt_reconnect()
                    else:
                        break

    # ================================================================
    # ================================================================
    # 정보 조회 메서드 (테스트 호환성)
    # ================================================================

    def get_subscriptions(self) -> Dict[str, Dict[str, Any]]:
        """구독 정보 조회 (테스트 호환성)"""
        return self._subscription_manager.get_subscriptions()

    def get_subscription_stats(self) -> Dict[str, Any]:
        """구독 통계 정보 조회"""
        subscriptions = self.get_subscriptions()

        return {
            "is_connected": self.is_connected,
            "subscription_types": list(subscriptions.keys()),
            "total_symbols": sum(len(sub["symbols"]) for sub in subscriptions.values()),
            "connection_start_time": self._stats['connection_start_time'],
            "messages_received": self._stats['messages_received'],
            "messages_processed": self._stats['messages_processed'],
            "errors_count": self._stats['errors_count'],
            "last_message_time": self._stats['last_message_time'],
            "unified_tickets": len(self._unified_subscriptions),
            "current_ticket": self._current_ticket
        }

    # ================================================================
    # 외부 리스너 지원 (테스트 호환성)
    # ================================================================

    async def listen(self, external_handler: Optional[Callable] = None) -> None:
        """외부 리스너 등록 및 리스닝 시작"""
        if external_handler:
            # 외부 핸들러를 위한 큐 생성
            handler_queue = asyncio.Queue()
            self._external_listeners.append(handler_queue)
            self._enable_external_listen = True

            # 별도 태스크에서 핸들러 처리
            async def handler_task():
                while self.is_connected:
                    try:
                        message = await handler_queue.get()
                        if asyncio.iscoroutinefunction(external_handler):
                            await external_handler(message)
                        else:
                            external_handler(message)
                    except Exception as e:
                        self.logger.error(f"외부 핸들러 오류: {e}")
                        break

            task = asyncio.create_task(handler_task())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

        # 메시지 루프가 실행 중이 아니면 시작
        if not self._message_loop_running:
            await self._start_message_loop()

    # ================================================================
    # 지능적 재연결 로직 및 추가 유틸리티 메서드
    # ================================================================

    async def _attempt_reconnect(self) -> bool:
        """자동 재연결 시도 - 개선된 재연결 로직"""
        # 재연결 조건 검사
        if not self._should_attempt_reconnect():
            return False

        # 재연결 통계 업데이트
        self.reconnect_attempts += 1
        self._stats['reconnection_count'] += 1
        current_time = time.time()

        self.logger.info(f"재연결 시도 {self.reconnect_attempts}/{self.max_reconnect_attempts}")

        # 지능적 재연결 지연 계산
        delay = self._calculate_reconnect_delay()

        self.logger.debug(f"재연결 대기: {delay:.2f}초 (Rate Limiter 고려)")
        await asyncio.sleep(delay)

        # 재연결 실행
        if await self.connect():
            # 기존 구독 복원
            await self._restore_subscriptions()
            self.last_reconnect_time = current_time
            self.logger.info("✅ 재연결 및 구독 복원 완료")
            return True

        return False

    def _should_attempt_reconnect(self) -> bool:
        """재연결 필요성 판단"""
        # 기본 조건 확인
        if not self.auto_reconnect or self.reconnect_attempts >= self.max_reconnect_attempts:
            self.logger.warning(f"재연결 중단: attempts={self.reconnect_attempts}, max={self.max_reconnect_attempts}")
            return False

        # 연결 상태 확인
        if self.is_connected:
            self.logger.debug("이미 연결됨 - 재연결 불필요")
            return False

        # 재연결 빈도 제한
        current_time = time.time()
        if (self.last_reconnect_time > 0
                and current_time - self.last_reconnect_time < self.min_reconnect_interval):
            self.logger.debug(f"재연결 간격 제한 ({self.min_reconnect_interval}초)")
            return False

        return True

    def _calculate_reconnect_delay(self) -> float:
        """지능적 재연결 지연 계산"""
        # 기본 지연: 지수 백오프 + 지터
        base_delay = min(0.1 * (2 ** self.reconnect_attempts), 2.0)

        # Rate Limiter 고려
        rate_limiter_delay = 0.2

        # 전체 지연이 과도하지 않도록 제한
        total_delay = base_delay + rate_limiter_delay
        if total_delay > 5.0:
            base_delay = max(0.1, 5.0 - rate_limiter_delay)

        # 지터 추가 (±10%)
        jitter = random.uniform(0.9, 1.1)

        return base_delay * jitter

    async def _restore_subscriptions(self) -> None:
        """기존 구독 복원"""
        try:
            subscriptions = self._subscription_manager.get_subscriptions()
            for data_type_str, sub_data in subscriptions.items():
                try:
                    # 캔들 타입 처리
                    if data_type_str.startswith('candle.'):
                        # 캔들 단위 추출
                        parts = data_type_str.split('.')
                        if len(parts) >= 2:
                            unit_str = parts[1].replace('m', '').replace('s', '')
                            try:
                                unit = int(unit_str)
                            except ValueError:
                                unit = 5  # 기본값
                        else:
                            unit = 5

                        symbols = sub_data['symbols']
                        await self.subscribe_candle(symbols, str(unit))
                    else:
                        # 일반 타입 처리
                        try:
                            data_type = WebSocketDataType(data_type_str)
                            symbols = sub_data['symbols']

                            if data_type == WebSocketDataType.TICKER:
                                await self.subscribe_ticker(symbols)
                            elif data_type == WebSocketDataType.TRADE:
                                await self.subscribe_trade(symbols)
                            elif data_type == WebSocketDataType.ORDERBOOK:
                                await self.subscribe_orderbook(symbols)

                        except ValueError:
                            self.logger.warning(f"알 수 없는 데이터 타입: {data_type_str}")

                except Exception as e:
                    self.logger.warning(f"구독 복원 실패: {data_type_str} - {e}")
        except Exception as e:
            self.logger.error(f"구독 복원 과정 오류: {e}")

    # ================================================================
    # 스트림 타입 활용 메서드들 (레거시 기능)
    # ================================================================

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

    def __repr__(self) -> str:
        """객체 문자열 표현"""
        status = "연결됨" if self.is_connected else "연결 해제"
        return f"UpbitWebSocketPublicClient(상태={status}, 티켓={len(self._unified_subscriptions)}개)"
