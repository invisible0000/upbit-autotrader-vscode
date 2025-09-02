"""
WebSocket v6.0 통합 데이터 프로세서
================================

data_routing_engine + data_pool_manager 통합
- 콜백 기반 라우팅 (v6.0)
- 데이터 풀 기반 관리 (v6.1)
- 백프레셔 처리
- 성능 최적화

간소화된 통합 접근법으로 복잡성 대폭 감소
"""

import asyncio
import time
from typing import Dict, Set, Optional, Callable, List
from dataclasses import dataclass, field
from collections import defaultdict, deque

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .websocket_types import (
    BaseWebSocketEvent, DataType, BackpressureStrategy, BackpressureConfig,
    TickerEvent, OrderbookEvent, TradeEvent, CandleEvent, MyOrderEvent, MyAssetEvent
)


@dataclass
class CallbackInfo:
    """콜백 정보"""
    callback: Callable[[BaseWebSocketEvent], None]
    component_id: str
    data_type: DataType
    queue: asyncio.Queue
    error_count: int = 0
    last_success: float = field(default_factory=time.monotonic)
    is_active: bool = True


@dataclass
class DataPoolEntry:
    """데이터 풀 엔트리"""
    symbol: str
    data_type: DataType
    data: BaseWebSocketEvent
    timestamp: float = field(default_factory=time.time)
    update_count: int = 0


@dataclass
class ClientInterest:
    """클라이언트 관심사"""
    client_id: str
    data_types: Set[DataType]
    symbols: Set[str]
    last_access: float = field(default_factory=time.time)


@dataclass
class ProcessingStats:
    """처리 통계"""
    total_events_received: int = 0
    total_events_distributed: int = 0
    events_dropped: int = 0
    active_callbacks: int = 0
    pool_size: int = 0
    client_requests: int = 0
    backpressure_activations: int = 0

    @property
    def distribution_rate(self) -> float:
        """분배 성공률"""
        if self.total_events_received == 0:
            return 1.0
        return self.total_events_distributed / self.total_events_received


class DataProcessor:
    """
    통합 데이터 프로세서

    콜백 기반 라우팅 + 데이터 풀 관리를 하나의 클래스에서 처리
    """

    def __init__(self, backpressure_config: Optional[BackpressureConfig] = None):
        self.logger = create_component_logger("DataProcessor")

        # 백프레셔 설정
        self.backpressure_config = backpressure_config or BackpressureConfig()

        # 콜백 기반 라우팅 (v6.0)
        self._callbacks: Dict[str, CallbackInfo] = {}  # callback_id -> CallbackInfo
        self._data_type_callbacks: Dict[DataType, Set[str]] = defaultdict(set)

        # 데이터 풀 (v6.1)
        self._data_pool: Dict[str, Dict[DataType, DataPoolEntry]] = defaultdict(dict)
        self._client_interests: Dict[str, ClientInterest] = {}
        self._data_history: Dict[str, Dict[DataType, deque]] = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=100))
        )

        # 백그라운드 태스크
        self._processor_task: Optional[asyncio.Task] = None
        self._event_queue: asyncio.Queue = asyncio.Queue(maxsize=self.backpressure_config.max_queue_size)
        self._running = False

        # 통계
        self.stats = ProcessingStats()

        self.logger.info("데이터 프로세서 초기화 완료")

    # ================================================================
    # 생명주기 관리
    # ================================================================

    async def start(self) -> None:
        """데이터 프로세서 시작"""
        if self._running:
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        self.logger.info("데이터 프로세서 시작됨")

    async def stop(self) -> None:
        """데이터 프로세서 중지"""
        if not self._running:
            return

        self._running = False

        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

        # 큐 정리
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        self.logger.info("데이터 프로세서 중지됨")

    # ================================================================
    # 콜백 기반 라우팅 (v6.0)
    # ================================================================

    def register_callback(
        self,
        callback_id: str,
        component_id: str,
        data_type: DataType,
        callback: Callable[[BaseWebSocketEvent], None]
    ) -> None:
        """콜백 등록"""
        if callback_id in self._callbacks:
            self.logger.warning(f"콜백 ID 중복: {callback_id}")
            return

        queue = asyncio.Queue(maxsize=self.backpressure_config.max_queue_size)

        callback_info = CallbackInfo(
            callback=callback,
            component_id=component_id,
            data_type=data_type,
            queue=queue
        )

        self._callbacks[callback_id] = callback_info
        self._data_type_callbacks[data_type].add(callback_id)
        self.stats.active_callbacks = len(self._callbacks)

        # 백그라운드에서 콜백 처리
        asyncio.create_task(self._process_callback_queue(callback_id))

        self.logger.debug(f"콜백 등록: {callback_id} ({data_type})")

    def unregister_callback(self, callback_id: str) -> None:
        """콜백 해제"""
        if callback_id not in self._callbacks:
            return

        callback_info = self._callbacks.pop(callback_id)
        self._data_type_callbacks[callback_info.data_type].discard(callback_id)
        self.stats.active_callbacks = len(self._callbacks)

        self.logger.debug(f"콜백 해제: {callback_id}")

    async def _process_callback_queue(self, callback_id: str) -> None:
        """개별 콜백 큐 처리"""
        while callback_id in self._callbacks:
            callback_info = self._callbacks[callback_id]

            try:
                # 타임아웃으로 주기적 체크
                event = await asyncio.wait_for(callback_info.queue.get(), timeout=1.0)

                if not callback_info.is_active:
                    continue

                # 콜백 실행
                try:
                    callback_info.callback(event)
                    callback_info.last_success = time.monotonic()
                    callback_info.error_count = 0
                except Exception as e:
                    callback_info.error_count += 1
                    self.logger.error(f"콜백 오류 ({callback_id}): {e}")

                    # 오류가 너무 많으면 비활성화
                    if callback_info.error_count >= 5:
                        callback_info.is_active = False
                        self.logger.warning(f"콜백 비활성화: {callback_id}")

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"콜백 큐 처리 오류: {e}")
                break

    # ================================================================
    # 데이터 풀 관리 (v6.1)
    # ================================================================

    def register_client_interest(
        self,
        client_id: str,
        data_types: Set[DataType],
        symbols: Set[str]
    ) -> None:
        """클라이언트 관심사 등록"""
        self._client_interests[client_id] = ClientInterest(
            client_id=client_id,
            data_types=data_types,
            symbols=symbols
        )

        self.logger.debug(f"클라이언트 관심사 등록: {client_id}, {len(symbols)}개 심볼")

    def unregister_client(self, client_id: str) -> None:
        """클라이언트 해제"""
        self._client_interests.pop(client_id, None)
        self.logger.debug(f"클라이언트 해제: {client_id}")

    def get_latest_data(self, symbol: str, data_type: DataType) -> Optional[BaseWebSocketEvent]:
        """최신 데이터 조회"""
        self.stats.client_requests += 1

        symbol_data = self._data_pool.get(symbol, {})
        entry = symbol_data.get(data_type)

        if entry:
            # 접근 시간 업데이트
            entry.timestamp = time.time()
            return entry.data

        return None

    def get_multiple_latest_data(
        self,
        symbols: List[str],
        data_type: DataType
    ) -> Dict[str, Optional[BaseWebSocketEvent]]:
        """여러 심볼의 최신 데이터 일괄 조회"""
        result = {}
        for symbol in symbols:
            result[symbol] = self.get_latest_data(symbol, data_type)
        return result

    def get_data_history(
        self,
        symbol: str,
        data_type: DataType,
        limit: int = 10
    ) -> List[BaseWebSocketEvent]:
        """데이터 히스토리 조회"""
        history = self._data_history.get(symbol, {}).get(data_type, deque())
        return list(history)[-limit:] if history else []

    # ================================================================
    # 이벤트 처리
    # ================================================================

    async def route_event(self, event: BaseWebSocketEvent) -> None:
        """이벤트 라우팅 (메인 진입점)"""
        if not self._running:
            return

        try:
            self._event_queue.put_nowait(event)
            self.stats.total_events_received += 1
        except asyncio.QueueFull:
            # 백프레셔 처리
            await self._handle_backpressure(event)

    async def _process_events(self) -> None:
        """메인 이벤트 처리 루프"""
        while self._running:
            try:
                # 이벤트 대기
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)

                # 데이터 풀 업데이트 (v6.1)
                await self._update_data_pool(event)

                # 콜백 라우팅 (v6.0)
                await self._route_to_callbacks(event)

                self.stats.total_events_distributed += 1

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"이벤트 처리 오류: {e}")

    async def _update_data_pool(self, event: BaseWebSocketEvent) -> None:
        """데이터 풀 업데이트"""
        symbol = getattr(event, 'symbol', None)
        if not symbol:
            return

        # 데이터 타입 추론
        data_type = self._infer_data_type(event)
        if not data_type:
            return

        # 풀 업데이트
        if symbol not in self._data_pool:
            self._data_pool[symbol] = {}

        self._data_pool[symbol][data_type] = DataPoolEntry(
            symbol=symbol,
            data_type=data_type,
            data=event,
            update_count=self._data_pool[symbol].get(data_type, DataPoolEntry(symbol, data_type, event)).update_count + 1
        )

        # 히스토리 추가
        self._data_history[symbol][data_type].append(event)

        self.stats.pool_size = sum(len(types) for types in self._data_pool.values())

    async def _route_to_callbacks(self, event: BaseWebSocketEvent) -> None:
        """콜백으로 이벤트 라우팅"""
        data_type = self._infer_data_type(event)
        if not data_type:
            return

        callback_ids = self._data_type_callbacks.get(data_type, set())

        for callback_id in callback_ids.copy():
            if callback_id not in self._callbacks:
                self._data_type_callbacks[data_type].discard(callback_id)
                continue

            callback_info = self._callbacks[callback_id]

            if not callback_info.is_active:
                continue

            try:
                callback_info.queue.put_nowait(event)
            except asyncio.QueueFull:
                # 개별 콜백 백프레셔 처리
                await self._handle_callback_backpressure(callback_info, event)

    def _infer_data_type(self, event: BaseWebSocketEvent) -> Optional[DataType]:
        """이벤트에서 데이터 타입 추론"""
        if isinstance(event, TickerEvent):
            return DataType.TICKER
        elif isinstance(event, OrderbookEvent):
            return DataType.ORDERBOOK
        elif isinstance(event, TradeEvent):
            return DataType.TRADE
        elif isinstance(event, CandleEvent):
            # 캔들 단위별 구분 필요시 구현
            return DataType.CANDLE_1M  # 기본값
        elif isinstance(event, MyOrderEvent):
            return DataType.MYORDER
        elif isinstance(event, MyAssetEvent):
            return DataType.MYASSET

        return None

    # ================================================================
    # 백프레셔 처리
    # ================================================================

    async def _handle_backpressure(self, event: BaseWebSocketEvent) -> None:
        """전역 백프레셔 처리"""
        self.stats.backpressure_activations += 1

        if self.backpressure_config.strategy == BackpressureStrategy.DROP_OLDEST:
            # 가장 오래된 이벤트 드롭
            try:
                self._event_queue.get_nowait()
                self._event_queue.put_nowait(event)
            except (asyncio.QueueEmpty, asyncio.QueueFull):
                self.stats.events_dropped += 1

        elif self.backpressure_config.strategy == BackpressureStrategy.THROTTLE:
            # 스로틀링
            await asyncio.sleep(self.backpressure_config.throttle_interval_ms / 1000)
            try:
                self._event_queue.put_nowait(event)
            except asyncio.QueueFull:
                self.stats.events_dropped += 1

        else:
            # 기본: 드롭
            self.stats.events_dropped += 1

        self.logger.warning(f"백프레셔 활성화: {self.backpressure_config.strategy}")

    async def _handle_callback_backpressure(
        self,
        callback_info: CallbackInfo,
        event: BaseWebSocketEvent
    ) -> None:
        """개별 콜백 백프레셔 처리"""
        if self.backpressure_config.strategy == BackpressureStrategy.DROP_OLDEST:
            try:
                callback_info.queue.get_nowait()
                callback_info.queue.put_nowait(event)
            except (asyncio.QueueEmpty, asyncio.QueueFull):
                pass

    # ================================================================
    # 상태 조회
    # ================================================================

    def get_stats(self) -> ProcessingStats:
        """처리 통계 조회"""
        return self.stats

    def get_active_symbols(self) -> Set[str]:
        """활성 심볼 목록"""
        return set(self._data_pool.keys())

    def get_required_subscriptions(self) -> Dict[DataType, Set[str]]:
        """필요한 구독 목록 계산 (모든 클라이언트 관심사 통합)"""
        required = defaultdict(set)

        for interest in self._client_interests.values():
            for data_type in interest.data_types:
                required[data_type].update(interest.symbols)

        return dict(required)

    def cleanup_inactive_data(self, max_age_seconds: float = 3600) -> int:
        """비활성 데이터 정리"""
        current_time = time.time()
        cleaned_count = 0

        for symbol in list(self._data_pool.keys()):
            symbol_data = self._data_pool[symbol]

            for data_type in list(symbol_data.keys()):
                entry = symbol_data[data_type]

                if current_time - entry.timestamp > max_age_seconds:
                    del symbol_data[data_type]
                    cleaned_count += 1

            # 빈 심볼 제거
            if not symbol_data:
                del self._data_pool[symbol]

        if cleaned_count > 0:
            self.logger.info(f"비활성 데이터 정리: {cleaned_count}개")

        return cleaned_count


# ================================================================
# 팩토리 함수
# ================================================================

def create_data_processor(
    backpressure_strategy: BackpressureStrategy = BackpressureStrategy.DROP_OLDEST,
    max_queue_size: int = 1000
) -> DataProcessor:
    """데이터 프로세서 생성"""
    config = BackpressureConfig(
        strategy=backpressure_strategy,
        max_queue_size=max_queue_size
    )

    return DataProcessor(config)


__all__ = [
    'DataProcessor',
    'CallbackInfo',
    'DataPoolEntry',
    'ClientInterest',
    'ProcessingStats',
    'create_data_processor'
]
