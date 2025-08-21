"""
실시간 구독 기능 개선

Queue 기반의 진정한 실시간 구독 시스템을 구현합니다.
기존의 "한 번의 데이터 스냅샷" 방식을 "지속적인 실시간 스트림"으로 개선합니다.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, AsyncGenerator, Callable
from dataclasses import dataclass
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("RealtimeSubscriptionManager")


@dataclass
class SubscriptionConfig:
    """구독 설정"""
    symbols: List[str]
    data_types: List[str]  # ['ticker', 'orderbook', 'trade']
    buffer_size: int = 1000
    timeout_seconds: float = 30.0
    auto_reconnect: bool = True


@dataclass
class RealtimeDataMessage:
    """실시간 데이터 메시지"""
    symbol: str
    data_type: str
    data: Dict[str, Any]
    timestamp: datetime
    sequence: int = 0


class RealtimeDataQueue:
    """실시간 데이터 큐"""

    def __init__(self, subscription_id: str, config: SubscriptionConfig):
        self.subscription_id = subscription_id
        self.config = config
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=config.buffer_size)
        self.is_active = True
        self.created_at = datetime.now()
        self.last_data_time = datetime.now()
        self.total_messages = 0
        self.dropped_messages = 0

    async def put(self, message: RealtimeDataMessage) -> bool:
        """메시지 추가 (논블로킹)"""
        if not self.is_active:
            return False

        try:
            self.queue.put_nowait(message)
            self.last_data_time = datetime.now()
            self.total_messages += 1
            return True
        except asyncio.QueueFull:
            self.dropped_messages += 1
            logger.warning(f"큐 버퍼 초과로 메시지 드롭: {self.subscription_id}")
            return False

    async def get(self, timeout: Optional[float] = None) -> Optional[RealtimeDataMessage]:
        """메시지 조회"""
        if not self.is_active:
            return None

        try:
            return await asyncio.wait_for(self.queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def get_batch(self, max_count: int = 10, timeout: float = 0.1) -> List[RealtimeDataMessage]:
        """배치 메시지 조회"""
        messages = []
        deadline = time.time() + timeout

        while len(messages) < max_count and time.time() < deadline and self.is_active:
            try:
                remaining_time = max(0.001, deadline - time.time())
                message = await self.get(timeout=remaining_time)
                if message:
                    messages.append(message)
                else:
                    break
            except Exception:
                break

        return messages

    def close(self):
        """큐 종료"""
        self.is_active = False

    def get_stats(self) -> Dict[str, Any]:
        """통계 정보"""
        return {
            'subscription_id': self.subscription_id,
            'queue_size': self.queue.qsize(),
            'total_messages': self.total_messages,
            'dropped_messages': self.dropped_messages,
            'uptime_seconds': (datetime.now() - self.created_at).total_seconds(),
            'last_data_seconds_ago': (datetime.now() - self.last_data_time).total_seconds(),
            'is_active': self.is_active
        }


class RealtimeSubscriptionManager:
    """실시간 구독 관리자

    기존의 제한적인 실시간 구독을 Queue 기반의 진정한 실시간 스트림으로 개선합니다.
    """

    def __init__(self):
        logger.info("RealtimeSubscriptionManager 초기화")

        # 구독 관리
        self.active_subscriptions: Dict[str, RealtimeDataQueue] = {}
        self.subscription_callbacks: Dict[str, List[Callable]] = {}
        self.global_callbacks: List[Callable] = []

        # 백그라운드 작업
        self.data_distributor_task: Optional[asyncio.Task] = None
        self.health_monitor_task: Optional[asyncio.Task] = None
        self.is_running = False

        # 메트릭
        self.total_subscriptions = 0
        self.total_messages_processed = 0
        self.start_time = datetime.now()

        # WebSocket 연결 (실제 구현에서는 UpbitWebSocketQuotationClient 사용)
        self.websocket_client = None  # Placeholder

        logger.info("RealtimeSubscriptionManager 초기화 완료")

    async def start(self):
        """실시간 구독 시스템 시작"""
        if self.is_running:
            return

        self.is_running = True

        # WebSocket 연결 시작
        # self.websocket_client = UpbitWebSocketQuotationClient()
        # await self.websocket_client.connect()

        # 백그라운드 작업 시작
        self.data_distributor_task = asyncio.create_task(self._data_distribution_loop())
        self.health_monitor_task = asyncio.create_task(self._health_monitor_loop())

        logger.info("✅ 실시간 구독 시스템 시작")

    async def stop(self):
        """실시간 구독 시스템 정지"""
        self.is_running = False

        # 모든 구독 종료
        for queue in self.active_subscriptions.values():
            queue.close()

        # 백그라운드 작업 종료
        if self.data_distributor_task:
            self.data_distributor_task.cancel()
            try:
                await self.data_distributor_task
            except asyncio.CancelledError:
                pass

        if self.health_monitor_task:
            self.health_monitor_task.cancel()
            try:
                await self.health_monitor_task
            except asyncio.CancelledError:
                pass

        # WebSocket 연결 종료
        # if self.websocket_client:
        #     await self.websocket_client.disconnect()

        logger.info("✅ 실시간 구독 시스템 정지")

    async def create_subscription(self, config: SubscriptionConfig) -> str:
        """실시간 구독 생성

        Returns:
            subscription_id: 구독 ID (Queue 접근용)
        """
        subscription_id = f"sub_{int(time.time() * 1000)}_{len(self.active_subscriptions)}"

        # 구독 큐 생성
        queue = RealtimeDataQueue(subscription_id, config)
        self.active_subscriptions[subscription_id] = queue
        self.total_subscriptions += 1

        # WebSocket 구독 추가 (실제 구현)
        # for symbol in config.symbols:
        #     for data_type in config.data_types:
        #         await self.websocket_client.subscribe(symbol, data_type)

        logger.info(f"✅ 실시간 구독 생성: {subscription_id}, 심볼: {config.symbols}, 타입: {config.data_types}")
        return subscription_id

    def get_subscription_queue(self, subscription_id: str) -> Optional[RealtimeDataQueue]:
        """구독 큐 조회"""
        return self.active_subscriptions.get(subscription_id)

    async def close_subscription(self, subscription_id: str) -> bool:
        """구독 종료"""
        queue = self.active_subscriptions.pop(subscription_id, None)
        if queue:
            queue.close()
            logger.info(f"✅ 구독 종료: {subscription_id}")
            return True
        return False

    async def subscribe_with_callback(
        self,
        config: SubscriptionConfig,
        callback: Callable[[RealtimeDataMessage], None]
    ) -> str:
        """콜백 기반 구독"""
        subscription_id = await self.create_subscription(config)

        if subscription_id not in self.subscription_callbacks:
            self.subscription_callbacks[subscription_id] = []
        self.subscription_callbacks[subscription_id].append(callback)

        logger.info(f"✅ 콜백 구독 등록: {subscription_id}")
        return subscription_id

    async def subscribe_with_async_generator(
        self,
        config: SubscriptionConfig
    ) -> AsyncGenerator[RealtimeDataMessage, None]:
        """AsyncGenerator 기반 구독 (Python async for 지원)"""
        subscription_id = await self.create_subscription(config)
        queue = self.get_subscription_queue(subscription_id)

        if not queue:
            return

        try:
            logger.info(f"✅ AsyncGenerator 구독 시작: {subscription_id}")
            while queue.is_active and self.is_running:
                message = await queue.get(timeout=1.0)
                if message:
                    yield message
        finally:
            await self.close_subscription(subscription_id)
            logger.info(f"✅ AsyncGenerator 구독 종료: {subscription_id}")

    async def _data_distribution_loop(self):
        """데이터 분배 루프 (백그라운드)"""
        logger.info("데이터 분배 루프 시작")

        while self.is_running:
            try:
                # 실제 구현에서는 WebSocket에서 데이터 수신
                # message_data = await self.websocket_client.receive_message()
                # 현재는 모의 데이터로 테스트
                await self._simulate_realtime_data()

                await asyncio.sleep(0.1)  # 100ms 간격

            except Exception as e:
                logger.error(f"데이터 분배 오류: {e}")
                await asyncio.sleep(1.0)

        logger.info("데이터 분배 루프 종료")

    async def _simulate_realtime_data(self):
        """실시간 데이터 시뮬레이션 (테스트용)"""
        if not self.active_subscriptions:
            return

        import random

        # 모의 데이터 생성
        symbols = ["KRW-BTC", "KRW-ETH", "KRW-ADA"]
        data_types = ["ticker", "orderbook"]

        for _ in range(random.randint(1, 3)):  # 1-3개 메시지 생성
            symbol = random.choice(symbols)
            data_type = random.choice(data_types)

            if data_type == "ticker":
                mock_data = {
                    "trade_price": random.randint(90000000, 100000000),
                    "change": "RISE" if random.random() > 0.5 else "FALL",
                    "change_rate": round(random.uniform(-0.05, 0.05), 4),
                    "trade_volume": round(random.uniform(0.1, 10.0), 4)
                }
            else:  # orderbook
                mock_data = {
                    "total_ask_size": round(random.uniform(10.0, 100.0), 4),
                    "total_bid_size": round(random.uniform(10.0, 100.0), 4),
                    "orderbook_units": []
                }

            message = RealtimeDataMessage(
                symbol=symbol,
                data_type=data_type,
                data=mock_data,
                timestamp=datetime.now(),
                sequence=self.total_messages_processed
            )

            # 모든 관련 구독 큐에 메시지 전송
            await self._distribute_message(message)
            self.total_messages_processed += 1

    async def _distribute_message(self, message: RealtimeDataMessage):
        """메시지 분배"""
        distributed_count = 0

        for subscription_id, queue in list(self.active_subscriptions.items()):
            # 구독 필터링 확인
            if (message.symbol in queue.config.symbols and
                    message.data_type in queue.config.data_types):

                success = await queue.put(message)
                if success:
                    distributed_count += 1

                # 콜백 처리
                callbacks = self.subscription_callbacks.get(subscription_id, [])
                for callback in callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(message)
                        else:
                            callback(message)
                    except Exception as e:
                        logger.error(f"콜백 처리 오류: {e}")

        # 전역 콜백 처리
        for callback in self.global_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except Exception as e:
                logger.error(f"전역 콜백 처리 오류: {e}")

        if distributed_count > 0:
            logger.debug(f"메시지 분배 완료: {message.symbol}:{message.data_type} → {distributed_count}개 구독")

    async def _health_monitor_loop(self):
        """건강 상태 모니터링"""
        logger.info("건강 상태 모니터링 시작")

        while self.is_running:
            try:
                await self._check_subscription_health()
                await asyncio.sleep(30.0)  # 30초마다 점검
            except Exception as e:
                logger.error(f"건강 상태 점검 오류: {e}")
                await asyncio.sleep(5.0)

        logger.info("건강 상태 모니터링 종료")

    async def _check_subscription_health(self):
        """구독 건강 상태 점검"""
        current_time = datetime.now()
        stale_subscriptions = []

        for subscription_id, queue in self.active_subscriptions.items():
            # 장시간 데이터 없는 구독 찾기
            seconds_since_last_data = (current_time - queue.last_data_time).total_seconds()

            if seconds_since_last_data > queue.config.timeout_seconds:
                stale_subscriptions.append(subscription_id)
                logger.warning(f"구독 타임아웃: {subscription_id} ({seconds_since_last_data:.1f}초)")

        # 타임아웃된 구독 처리
        for subscription_id in stale_subscriptions:
            queue = self.active_subscriptions.get(subscription_id)
            if queue and queue.config.auto_reconnect:
                logger.info(f"구독 자동 재연결 시도: {subscription_id}")
                # 실제로는 WebSocket 재구독 로직 필요
            else:
                await self.close_subscription(subscription_id)

    def get_system_stats(self) -> Dict[str, Any]:
        """시스템 통계"""
        uptime = (datetime.now() - self.start_time).total_seconds()

        subscription_stats = []
        total_queue_size = 0
        total_dropped = 0

        for queue in self.active_subscriptions.values():
            stats = queue.get_stats()
            subscription_stats.append(stats)
            total_queue_size += stats['queue_size']
            total_dropped += stats['dropped_messages']

        return {
            'system': {
                'is_running': self.is_running,
                'uptime_seconds': uptime,
                'total_subscriptions_created': self.total_subscriptions,
                'active_subscriptions': len(self.active_subscriptions),
                'total_messages_processed': self.total_messages_processed,
                'messages_per_second': self.total_messages_processed / max(uptime, 1.0)
            },
            'performance': {
                'total_queue_size': total_queue_size,
                'total_dropped_messages': total_dropped,
                'drop_rate': total_dropped / max(self.total_messages_processed, 1) * 100
            },
            'subscriptions': subscription_stats
        }


# 편의성 래퍼 함수들
async def create_ticker_stream(symbols: List[str]) -> AsyncGenerator[RealtimeDataMessage, None]:
    """티커 데이터 스트림 생성"""
    manager = RealtimeSubscriptionManager()
    await manager.start()

    try:
        config = SubscriptionConfig(
            symbols=symbols,
            data_types=["ticker"],
            buffer_size=500
        )

        async for message in manager.subscribe_with_async_generator(config):
            yield message
    finally:
        await manager.stop()


async def create_orderbook_stream(symbols: List[str]) -> AsyncGenerator[RealtimeDataMessage, None]:
    """호가 데이터 스트림 생성"""
    manager = RealtimeSubscriptionManager()
    await manager.start()

    try:
        config = SubscriptionConfig(
            symbols=symbols,
            data_types=["orderbook"],
            buffer_size=1000
        )

        async for message in manager.subscribe_with_async_generator(config):
            yield message
    finally:
        await manager.stop()
