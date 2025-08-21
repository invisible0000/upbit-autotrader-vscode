"""
WebSocket 구독 관리 시스템

WebSocket 연결의 생명주기를 자율적으로 관리하고
효율적인 구독 정책을 제공합니다.
"""

import asyncio
import json
import uuid
from typing import Dict, List, Set, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

from ..models import TradingSymbol
from .rate_limit_mapper import IntegratedRateLimiter, RateLimitType
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
    UpbitWebSocketQuotationClient,
    WebSocketDataType,
    WebSocketMessage
)


class SubscriptionState(Enum):
    """구독 상태"""
    PENDING = "pending"        # 구독 요청됨
    ACTIVE = "active"          # 활성 구독 중
    PAUSED = "paused"          # 일시 정지
    CANCELLED = "cancelled"    # 취소됨
    ERROR = "error"           # 오류 상태


class ConnectionState(Enum):
    """연결 상태"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class SubscriptionInfo:
    """구독 정보"""

    subscription_id: str
    symbol: TradingSymbol
    data_types: List[str]
    callback: Callable[[Dict[str, Any]], None]
    created_at: datetime
    state: SubscriptionState = SubscriptionState.PENDING
    last_data_time: Optional[datetime] = None
    error_count: int = 0
    total_messages: int = 0

    @property
    def is_active(self) -> bool:
        """활성 상태 여부"""
        return self.state == SubscriptionState.ACTIVE

    @property
    def idle_duration(self) -> timedelta:
        """마지막 데이터 이후 경과 시간"""
        if self.last_data_time:
            return datetime.now() - self.last_data_time
        return datetime.now() - self.created_at


@dataclass
class ConnectionMetrics:
    """연결 메트릭"""

    connection_attempts: int = 0
    successful_connections: int = 0
    disconnection_count: int = 0
    last_connection_time: Optional[datetime] = None
    last_disconnection_time: Optional[datetime] = None
    total_messages_received: int = 0
    total_errors: int = 0
    uptime_seconds: float = 0.0

    @property
    def connection_success_rate(self) -> float:
        """연결 성공률"""
        if self.connection_attempts == 0:
            return 0.0
        return self.successful_connections / self.connection_attempts

    @property
    def avg_session_duration(self) -> float:
        """평균 세션 지속 시간 (초)"""
        if self.successful_connections == 0:
            return 0.0
        return self.uptime_seconds / self.successful_connections


class WebSocketSubscriptionManager:
    """WebSocket 구독 관리자

    주요 기능:
    1. 자동 연결 관리 및 재연결
    2. 구독 생명주기 관리
    3. 유휴 구독 자동 정리
    4. 오류 복구 및 백오프
    5. 성능 모니터링
    """

    def __init__(
        self,
        websocket_url: str = "wss://api.upbit.com/websocket/v1",
        max_connections: int = 5,
        max_subscriptions_per_connection: int = 10,
        idle_timeout_minutes: int = 30,
        reconnect_max_attempts: int = 5,
        reconnect_base_delay: float = 1.0
    ):
        self.websocket_url = websocket_url
        self.max_connections = max_connections
        self.max_subscriptions_per_connection = max_subscriptions_per_connection
        self.idle_timeout_minutes = idle_timeout_minutes
        self.reconnect_max_attempts = reconnect_max_attempts
        self.reconnect_base_delay = reconnect_base_delay

        # Rate Limiting 통합
        self.rate_limiter = IntegratedRateLimiter()

        # 구독 관리
        self.subscriptions: Dict[str, SubscriptionInfo] = {}
        self.symbol_to_subscriptions: Dict[str, Set[str]] = {}

        # 연결 관리
        self.connections: Dict[str, UpbitWebSocketQuotationClient] = {}  # connection_id -> websocket_client
        self.connection_states: Dict[str, ConnectionState] = {}
        self.connection_metrics: Dict[str, ConnectionMetrics] = {}
        self.connection_subscriptions: Dict[str, Set[str]] = {}  # connection_id -> subscription_ids

        # 자동 관리 태스크
        self.management_tasks: Set[asyncio.Task] = set()
        self.is_running = False

        self.logger = logging.getLogger(self.__class__.__name__)

    async def start(self) -> None:
        """구독 관리자 시작"""
        if self.is_running:
            return

        self.is_running = True

        # 자동 관리 태스크 시작
        self.management_tasks.add(
            asyncio.create_task(self._cleanup_task())
        )
        self.management_tasks.add(
            asyncio.create_task(self._health_monitor_task())
        )

        self.logger.info("WebSocket 구독 관리자 시작됨")

    async def stop(self) -> None:
        """구독 관리자 종료"""
        if not self.is_running:
            return

        self.is_running = False

        # 모든 구독 취소
        for subscription_id in list(self.subscriptions.keys()):
            await self.unsubscribe(subscription_id)

        # 모든 연결 종료
        for connection_id in list(self.connections.keys()):
            await self._close_connection(connection_id)

        # 관리 태스크 종료
        for task in self.management_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self.management_tasks.clear()

        self.logger.info("WebSocket 구독 관리자 종료됨")

    async def subscribe(
        self,
        symbol: TradingSymbol,
        data_types: List[str],
        callback: Callable[[Dict[str, Any]], None]
    ) -> str:
        """데이터 구독 (Rate Limiting 적용)"""

        if not self.is_running:
            await self.start()

        # WebSocket 연결/메시지 전송에 대한 Rate Limiting 확인
        if not await self.rate_limiter.wait_for_availability(RateLimitType.WEBSOCKET, timeout_seconds=5.0):
            self.logger.warning(f"WebSocket rate limit으로 구독 실패: {symbol}")
            raise Exception(f"WebSocket rate limit exceeded for subscription: {symbol}")

        subscription_id = str(uuid.uuid4())

        # 구독 정보 생성
        subscription = SubscriptionInfo(
            subscription_id=subscription_id,
            symbol=symbol,
            data_types=data_types,
            callback=callback,
            created_at=datetime.now()
        )

        self.subscriptions[subscription_id] = subscription

        # 심볼별 인덱스 업데이트 - 업비트 형식으로 통일
        symbol_key = symbol.to_upbit_symbol()  # KRW-BTC 형식
        if symbol_key not in self.symbol_to_subscriptions:
            self.symbol_to_subscriptions[symbol_key] = set()
        self.symbol_to_subscriptions[symbol_key].add(subscription_id)

        self.logger.debug(f"🔗 심볼 매핑 생성: {symbol_key} -> {subscription_id}")

        # 적절한 연결에 할당
        connection_id = await self._assign_to_connection(subscription_id)

        if connection_id:
            # WebSocket 구독 메시지 전송
            await self._send_subscribe_message(connection_id, subscription)
            subscription.state = SubscriptionState.ACTIVE

            self.logger.info(f"구독 생성됨: {subscription_id} -> {symbol} {data_types}")
        else:
            subscription.state = SubscriptionState.ERROR
            self.logger.error(f"구독 실패: 사용 가능한 연결 없음 - {subscription_id}")

        return subscription_id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """구독 해제"""

        if subscription_id not in self.subscriptions:
            return False

        subscription = self.subscriptions[subscription_id]

        # 연결에서 구독 제거
        connection_id = self._find_connection_for_subscription(subscription_id)
        if connection_id:
            await self._send_unsubscribe_message(connection_id, subscription)
            self.connection_subscriptions[connection_id].discard(subscription_id)

        # 구독 정보 제거
        subscription.state = SubscriptionState.CANCELLED
        del self.subscriptions[subscription_id]

        # 심볼별 인덱스 업데이트 - 업비트 형식으로 통일
        symbol_key = subscription.symbol.to_upbit_symbol()  # KRW-BTC 형식
        if symbol_key in self.symbol_to_subscriptions:
            self.symbol_to_subscriptions[symbol_key].discard(subscription_id)
            if not self.symbol_to_subscriptions[symbol_key]:
                del self.symbol_to_subscriptions[symbol_key]

        self.logger.info(f"구독 해제됨: {subscription_id}")
        return True

    async def pause_subscription(self, subscription_id: str) -> bool:
        """구독 일시 정지"""

        if subscription_id not in self.subscriptions:
            return False

        subscription = self.subscriptions[subscription_id]
        if subscription.state == SubscriptionState.ACTIVE:
            subscription.state = SubscriptionState.PAUSED

            # 연결에서 일시적으로 구독 해제
            connection_id = self._find_connection_for_subscription(subscription_id)
            if connection_id:
                await self._send_unsubscribe_message(connection_id, subscription)

            self.logger.info(f"구독 일시정지: {subscription_id}")
            return True

        return False

    async def resume_subscription(self, subscription_id: str) -> bool:
        """구독 재개"""

        if subscription_id not in self.subscriptions:
            return False

        subscription = self.subscriptions[subscription_id]
        if subscription.state == SubscriptionState.PAUSED:
            # 연결에 다시 구독
            connection_id = await self._assign_to_connection(subscription_id)
            if connection_id:
                await self._send_subscribe_message(connection_id, subscription)
                subscription.state = SubscriptionState.ACTIVE

                self.logger.info(f"구독 재개: {subscription_id}")
                return True

        return False

    def get_subscription_stats(self) -> Dict[str, Any]:
        """구독 통계 정보"""

        active_count = sum(1 for s in self.subscriptions.values() if s.is_active)

        # 상태별 개수
        state_counts = {}
        for state in SubscriptionState:
            count = sum(1 for s in self.subscriptions.values() if s.state == state)
            state_counts[state.value] = count

        # 연결 통계
        connection_stats = {}
        for conn_id, metrics in self.connection_metrics.items():
            connection_stats[conn_id] = {
                "state": self.connection_states.get(conn_id, ConnectionState.DISCONNECTED).value,
                "subscriptions": len(self.connection_subscriptions.get(conn_id, set())),
                "success_rate": metrics.connection_success_rate,
                "total_messages": metrics.total_messages_received,
                "uptime_seconds": metrics.uptime_seconds
            }

        return {
            "total_subscriptions": len(self.subscriptions),
            "active_subscriptions": active_count,
            "subscription_states": state_counts,
            "total_connections": len(self.connections),
            "connection_stats": connection_stats,
            "symbols_monitored": len(self.symbol_to_subscriptions)
        }

    async def _assign_to_connection(self, subscription_id: str) -> Optional[str]:
        """구독을 적절한 연결에 할당"""

        # 기존 연결 중 여유가 있는 것 찾기
        for conn_id, sub_ids in self.connection_subscriptions.items():
            if (len(sub_ids) < self.max_subscriptions_per_connection and
                self.connection_states.get(conn_id) == ConnectionState.CONNECTED):

                sub_ids.add(subscription_id)
                return conn_id

        # 새 연결 생성 필요
        if len(self.connections) < self.max_connections:
            return await self._create_new_connection()

        # 연결 제한 도달
        self.logger.warning("최대 연결 수에 도달함")
        return None

    async def _create_new_connection(self) -> Optional[str]:
        """새 WebSocket 연결 생성 (Rate Limiting 적용)"""

        # WebSocket 연결 요청에 대한 Rate Limiting 확인
        if not await self.rate_limiter.wait_for_availability(RateLimitType.WEBSOCKET, timeout_seconds=3.0):
            self.logger.warning("WebSocket rate limit으로 연결 생성 실패")
            return None

        connection_id = str(uuid.uuid4())

        try:
            # 실제 WebSocket 클라이언트 생성
            client = UpbitWebSocketQuotationClient()

            # 메시지 핸들러 등록
            client.add_message_handler(WebSocketDataType.TICKER, self._handle_websocket_message)
            client.add_message_handler(WebSocketDataType.ORDERBOOK, self._handle_websocket_message)
            client.add_message_handler(WebSocketDataType.TRADE, self._handle_websocket_message)

            self.connection_states[connection_id] = ConnectionState.CONNECTING
            self.connection_metrics[connection_id] = ConnectionMetrics()
            self.connection_subscriptions[connection_id] = set()

            # 실제 연결 수행
            await client.connect()

            # 연결 성공
            self.connections[connection_id] = client
            self.connection_states[connection_id] = ConnectionState.CONNECTED
            self.connection_metrics[connection_id].successful_connections += 1
            self.connection_metrics[connection_id].last_connection_time = datetime.now()

            # 메시지 리스너 시작 (백그라운드)
            asyncio.create_task(self._message_listener(connection_id, client))

            self.logger.info(f"✅ 실제 WebSocket 연결 생성: {connection_id}")
            return connection_id

        except Exception as e:
            self.logger.error(f"❌ WebSocket 연결 실패: {e}")
            if connection_id in self.connection_states:
                self.connection_states[connection_id] = ConnectionState.FAILED
            return None

    async def _message_listener(self, connection_id: str, client: UpbitWebSocketQuotationClient):
        """WebSocket 메시지 리스너"""
        try:
            async for message in client.listen():
                # 메시지는 핸들러에서 이미 처리됨
                if connection_id in self.connection_metrics:
                    self.connection_metrics[connection_id].total_messages_received += 1
        except Exception as e:
            self.logger.error(f"❌ 메시지 리스너 오류 ({connection_id}): {e}")
            if connection_id in self.connection_states:
                self.connection_states[connection_id] = ConnectionState.FAILED

    def _handle_websocket_message(self, message: WebSocketMessage):
        """WebSocket 메시지 처리"""
        try:
            # 해당 심볼의 구독들을 찾아서 콜백 호출
            symbol_key = message.market  # KRW-BTC 형식

            if symbol_key in self.symbol_to_subscriptions:
                # 활성 구독이 있는 경우에만 처리
                active_subscriptions = []
                for sub_id in list(self.symbol_to_subscriptions[symbol_key]):
                    if sub_id in self.subscriptions:
                        subscription = self.subscriptions[sub_id]
                        if subscription.state == SubscriptionState.ACTIVE:
                            active_subscriptions.append(subscription)
                        else:
                            # 비활성 구독은 심볼 매핑에서 제거
                            self.symbol_to_subscriptions[symbol_key].discard(sub_id)

                # 활성 구독이 없으면 심볼 매핑 정리
                if not active_subscriptions:
                    if symbol_key in self.symbol_to_subscriptions:
                        del self.symbol_to_subscriptions[symbol_key]
                    self.logger.debug(f"🔍 비활성 심볼 매핑 정리: {symbol_key}")
                    return

                # 활성 구독들에게 데이터 전달
                for subscription in active_subscriptions:
                    subscription.last_data_time = datetime.now()
                    subscription.total_messages += 1

                    try:
                        subscription.callback(message.data)
                        self.logger.debug(f"📊 데이터 전달: {symbol_key} -> {subscription.subscription_id}")
                    except Exception as e:
                        self.logger.error(f"❌ 콜백 오류: {e}")
                        subscription.error_count += 1
            else:
                # 구독이 없는 경우 디버그 레벨로만 로그 (경고 수준 낮춤)
                self.logger.debug(f"🔍 미구독 심볼 메시지: {symbol_key}")

        except Exception as e:
            self.logger.error(f"❌ 메시지 처리 오류: {e}")

    async def _send_subscribe_message(
        self,
        connection_id: str,
        subscription: SubscriptionInfo
    ) -> None:
        """구독 메시지 전송"""

        if connection_id not in self.connections:
            self.logger.error(f"❌ 연결을 찾을 수 없음: {connection_id}")
            return

        client = self.connections[connection_id]
        symbol_code = subscription.symbol.to_upbit_symbol()

        try:
            # 데이터 타입에 따라 구독
            success = False
            for data_type in subscription.data_types:
                if data_type == "ticker":
                    success = await client.subscribe_ticker([symbol_code])
                elif data_type == "orderbook":
                    success = await client.subscribe_orderbook([symbol_code])
                elif data_type == "trade":
                    success = await client.subscribe_trade([symbol_code])

                if success:
                    self.logger.info(f"✅ 실제 구독 성공: {symbol_code} ({data_type})")
                else:
                    self.logger.error(f"❌ 구독 실패: {symbol_code} ({data_type})")

        except Exception as e:
            self.logger.error(f"❌ 구독 메시지 전송 실패: {e}")

    async def _send_unsubscribe_message(
        self,
        connection_id: str,
        subscription: SubscriptionInfo
    ) -> None:
        """구독 해제 메시지 전송"""

        # 업비트는 명시적 구독 해제 메시지가 없으므로
        # 연결 레벨에서 관리
        self.logger.debug(f"구독 해제 처리: {connection_id} -> {subscription.subscription_id}")

    def _find_connection_for_subscription(self, subscription_id: str) -> Optional[str]:
        """구독이 속한 연결 찾기"""

        for conn_id, sub_ids in self.connection_subscriptions.items():
            if subscription_id in sub_ids:
                return conn_id
        return None

    async def _close_connection(self, connection_id: str) -> None:
        """연결 종료 (자동 재연결 비활성화)"""

        if connection_id in self.connections:
            try:
                # 실제 WebSocket 연결 해제 (자동 재연결 비활성화)
                client = self.connections[connection_id]
                client.auto_reconnect = False  # 자동 재연결 비활성화
                await client.disconnect()
                self.logger.info(f"✅ WebSocket 연결 해제: {connection_id}")
            except Exception as e:
                self.logger.error(f"❌ 연결 해제 오류: {e}")
            finally:
                del self.connections[connection_id]

        if connection_id in self.connection_states:
            self.connection_states[connection_id] = ConnectionState.DISCONNECTED

        # 해당 연결의 모든 구독을 오류 상태로
        if connection_id in self.connection_subscriptions:
            for sub_id in self.connection_subscriptions[connection_id]:
                if sub_id in self.subscriptions:
                    self.subscriptions[sub_id].state = SubscriptionState.ERROR
            del self.connection_subscriptions[connection_id]

        self.logger.info(f"연결 종료 완료: {connection_id}")

    async def _cleanup_task(self) -> None:
        """유휴 구독 정리 태스크"""

        while self.is_running:
            try:
                await asyncio.sleep(60)  # 1분마다 체크

                current_time = datetime.now()
                idle_threshold = timedelta(minutes=self.idle_timeout_minutes)

                # 유휴 구독 찾기
                idle_subscriptions = []
                for sub_id, subscription in self.subscriptions.items():
                    if subscription.idle_duration > idle_threshold:
                        idle_subscriptions.append(sub_id)

                # 유휴 구독 제거
                for sub_id in idle_subscriptions:
                    await self.unsubscribe(sub_id)
                    self.logger.info(f"유휴 구독 정리: {sub_id}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"정리 태스크 오류: {e}")

    async def _health_monitor_task(self) -> None:
        """연결 상태 모니터링 태스크"""

        while self.is_running:
            try:
                await asyncio.sleep(30)  # 30초마다 체크

                # 연결 상태 확인
                for conn_id in list(self.connection_states.keys()):
                    state = self.connection_states[conn_id]

                    if state == ConnectionState.FAILED:
                        # 실패한 연결의 구독들을 다른 연결로 이전
                        await self._migrate_subscriptions_from_failed_connection(conn_id)
                        await self._close_connection(conn_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"상태 모니터링 오류: {e}")

    async def _migrate_subscriptions_from_failed_connection(
        self,
        failed_connection_id: str
    ) -> None:
        """실패한 연결의 구독들을 다른 연결로 이전"""

        if failed_connection_id not in self.connection_subscriptions:
            return

        sub_ids = list(self.connection_subscriptions[failed_connection_id])

        for sub_id in sub_ids:
            if sub_id in self.subscriptions:
                subscription = self.subscriptions[sub_id]

                # 새 연결에 할당 시도
                new_connection_id = await self._assign_to_connection(sub_id)

                if new_connection_id:
                    await self._send_subscribe_message(new_connection_id, subscription)
                    subscription.state = SubscriptionState.ACTIVE
                    self.logger.info(f"구독 이전 완료: {sub_id} -> {new_connection_id}")
                else:
                    subscription.state = SubscriptionState.ERROR
                    self.logger.error(f"구독 이전 실패: {sub_id}")
