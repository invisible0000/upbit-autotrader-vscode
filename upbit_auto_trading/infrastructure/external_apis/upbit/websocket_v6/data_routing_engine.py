"""
데이터 라우팅 엔진 & 백프레셔 핸들러
====================================

WebSocket v6의 데이터 분배 및 백프레셔 관리
수신된 데이터를 모든 구독자에게 안전하고 효율적으로 분배

핵심 기능:
- FanoutHub를 통한 멀티캐스팅
- 백프레셔 처리 (큐 오버플로우 대응)
- 콜백 에러 격리
- 성능 모니터링
"""

import asyncio
import time
from typing import Dict, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from collections import defaultdict

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .types import (
    BaseWebSocketEvent, DataType, BackpressureStrategy, BackpressureConfig
)


@dataclass
class QueuedEvent:
    """큐에 저장되는 이벤트"""
    event: BaseWebSocketEvent
    queued_at: float = field(default_factory=time.monotonic)
    attempts: int = 0

    @property
    def age_seconds(self) -> float:
        """이벤트 나이(초)"""
        return time.monotonic() - self.queued_at


@dataclass
class CallbackInfo:
    """콜백 정보"""
    callback: Callable[[BaseWebSocketEvent], None]
    component_id: str
    data_type: DataType
    queue: asyncio.Queue
    error_count: int = 0
    last_error: Optional[Exception] = None
    last_success: float = field(default_factory=time.monotonic)
    is_active: bool = True


class BackpressureHandler:
    """백프레셔 처리 전략"""

    def __init__(self, config: BackpressureConfig):
        self.config = config
        self.logger = create_component_logger("BackpressureHandler")

        # 통계
        self.dropped_count = 0
        self.coalesced_count = 0
        self.throttled_count = 0

    async def handle_queue_overflow(
        self,
        queue: asyncio.Queue,
        new_event: BaseWebSocketEvent,
        callback_info: CallbackInfo
    ) -> bool:
        """
        큐 오버플로우 처리

        Returns:
            bool: True if event was handled, False if dropped
        """
        strategy = self.config.strategy

        if strategy == BackpressureStrategy.DROP_OLDEST:
            return await self._drop_oldest_strategy(queue, new_event, callback_info)
        elif strategy == BackpressureStrategy.COALESCE_BY_SYMBOL:
            return await self._coalesce_by_symbol_strategy(queue, new_event, callback_info)
        elif strategy == BackpressureStrategy.THROTTLE:
            return await self._throttle_strategy(queue, new_event, callback_info)
        elif strategy == BackpressureStrategy.BLOCK:
            return await self._block_strategy(queue, new_event, callback_info)
        else:
            self.logger.warning(f"알 수 없는 백프레셔 전략: {strategy}")
            return False

    async def _drop_oldest_strategy(
        self,
        queue: asyncio.Queue,
        new_event: BaseWebSocketEvent,
        callback_info: CallbackInfo
    ) -> bool:
        """오래된 이벤트 제거 전략"""
        try:
            # 가장 오래된 이벤트 제거
            while queue.qsize() >= self.config.max_queue_size:
                try:
                    dropped_event = queue.get_nowait()
                    self.dropped_count += 1
                    self.logger.debug(f"오래된 이벤트 제거: {type(dropped_event.event).__name__}")
                except asyncio.QueueEmpty:
                    break

            # 새 이벤트 추가
            queued_event = QueuedEvent(event=new_event)
            queue.put_nowait(queued_event)
            return True

        except asyncio.QueueFull:
            self.dropped_count += 1
            self.logger.warning(f"큐 가득참으로 이벤트 폐기: {callback_info.component_id}")
            return False

    async def _coalesce_by_symbol_strategy(
        self,
        queue: asyncio.Queue,
        new_event: BaseWebSocketEvent,
        callback_info: CallbackInfo
    ) -> bool:
        """심볼별 통합 전략 (동일 심볼의 최신 데이터만 유지)"""
        if not new_event.symbol:
            return await self._drop_oldest_strategy(queue, new_event, callback_info)

        try:
            # 큐에서 동일 심볼 이벤트 검색 및 제거
            temp_events = []
            symbol_found = False

            while not queue.empty():
                try:
                    queued_event = queue.get_nowait()
                    if (queued_event.event.symbol == new_event.symbol
                            and type(queued_event.event).__name__ == type(new_event).__name__):
                        # 동일 심볼+타입 이벤트 발견 → 폐기
                        self.coalesced_count += 1
                        symbol_found = True
                    else:
                        temp_events.append(queued_event)
                except asyncio.QueueEmpty:
                    break

            # 큐 재구성
            for event in temp_events:
                queue.put_nowait(event)

            # 새 이벤트 추가
            queued_event = QueuedEvent(event=new_event)
            queue.put_nowait(queued_event)

            if symbol_found:
                self.logger.debug(f"심볼 통합: {new_event.symbol}")

            return True

        except Exception as e:
            self.logger.error(f"심볼별 통합 오류: {e}")
            return await self._drop_oldest_strategy(queue, new_event, callback_info)

    async def _throttle_strategy(
        self,
        queue: asyncio.Queue,
        new_event: BaseWebSocketEvent,
        callback_info: CallbackInfo
    ) -> bool:
        """스로틀 전략 (일정 간격으로만 이벤트 처리)"""
        now = time.monotonic()
        throttle_interval = self.config.throttle_interval_ms / 1000.0

        if now - callback_info.last_success < throttle_interval:
            self.throttled_count += 1
            return False  # 스로틀됨

        return await self._drop_oldest_strategy(queue, new_event, callback_info)

    async def _block_strategy(
        self,
        queue: asyncio.Queue,
        new_event: BaseWebSocketEvent,
        callback_info: CallbackInfo
    ) -> bool:
        """블로킹 전략 (대기)"""
        try:
            queued_event = QueuedEvent(event=new_event)
            await asyncio.wait_for(
                queue.put(queued_event),
                timeout=1.0  # 1초 최대 대기
            )
            return True
        except asyncio.TimeoutError:
            self.dropped_count += 1
            return False

    def get_stats(self) -> Dict[str, int]:
        """백프레셔 통계 반환"""
        return {
            'dropped_count': self.dropped_count,
            'coalesced_count': self.coalesced_count,
            'throttled_count': self.throttled_count
        }


class FanoutHub:
    """데이터 분배 허브"""

    def __init__(self, backpressure_config: BackpressureConfig):
        self.logger = create_component_logger("FanoutHub")
        self.backpressure_handler = BackpressureHandler(backpressure_config)

        # 콜백 관리
        self._callbacks: Dict[str, CallbackInfo] = {}  # callback_id -> CallbackInfo
        self._data_type_callbacks: Dict[DataType, Set[str]] = defaultdict(set)

        # 큐 모니터링
        self._queue_warning_threshold = int(backpressure_config.max_queue_size * backpressure_config.warning_threshold)

        # 백그라운드 태스크
        self._processor_tasks: Set[asyncio.Task] = set()
        self._running = False

        # 성능 메트릭
        self._metrics = {
            'events_distributed': 0,
            'callbacks_called': 0,
            'callback_errors': 0,
            'queue_overflows': 0,
            'avg_distribution_latency_ms': 0.0
        }

        self.logger.info("FanoutHub 초기화 완료")

    async def start(self) -> None:
        """FanoutHub 시작"""
        if self._running:
            return

        self._running = True
        self.logger.info("FanoutHub 시작")

    async def stop(self) -> None:
        """FanoutHub 중지"""
        if not self._running:
            return

        self._running = False

        # 모든 프로세서 태스크 중지
        for task in self._processor_tasks:
            task.cancel()

        if self._processor_tasks:
            await asyncio.gather(*self._processor_tasks, return_exceptions=True)

        self._processor_tasks.clear()
        self.logger.info("FanoutHub 중지 완료")

    def register_callback(
        self,
        callback_id: str,
        callback: Callable[[BaseWebSocketEvent], None],
        component_id: str,
        data_type: DataType,
        max_queue_size: Optional[int] = None
    ) -> None:
        """콜백 등록"""
        if callback_id in self._callbacks:
            self.logger.warning(f"콜백 ID 중복: {callback_id}")
            return

        queue_size = max_queue_size or self.backpressure_handler.config.max_queue_size
        queue = asyncio.Queue(maxsize=queue_size)

        callback_info = CallbackInfo(
            callback=callback,
            component_id=component_id,
            data_type=data_type,
            queue=queue
        )

        self._callbacks[callback_id] = callback_info
        self._data_type_callbacks[data_type].add(callback_id)

        # 콜백 프로세서 태스크 시작
        task = asyncio.create_task(self._process_callback_queue(callback_id))
        self._processor_tasks.add(task)
        task.add_done_callback(self._processor_tasks.discard)

        self.logger.debug(f"콜백 등록: {callback_id} ({component_id}, {data_type.value})")

    def unregister_callback(self, callback_id: str) -> None:
        """콜백 해제"""
        if callback_id not in self._callbacks:
            return

        callback_info = self._callbacks[callback_id]
        callback_info.is_active = False

        # 데이터 타입 매핑에서 제거
        self._data_type_callbacks[callback_info.data_type].discard(callback_id)

        # 콜백 정보 제거
        del self._callbacks[callback_id]

        self.logger.debug(f"콜백 해제: {callback_id}")

    async def distribute_event(self, event: BaseWebSocketEvent, data_type: DataType) -> None:
        """이벤트를 해당 콜백들에게 분배"""
        if not self._running:
            return

        start_time = time.monotonic()

        # 해당 데이터 타입의 콜백들 찾기
        callback_ids = self._data_type_callbacks.get(data_type, set())
        if not callback_ids:
            return

        distribution_count = 0

        for callback_id in callback_ids.copy():  # 복사본으로 순회 (동시 수정 방지)
            callback_info = self._callbacks.get(callback_id)
            if not callback_info or not callback_info.is_active:
                continue

            try:
                await self._enqueue_event(event, callback_info)
                distribution_count += 1

            except Exception as e:
                self.logger.error(f"이벤트 큐잉 오류: {callback_id}, {e}")

        # 성능 메트릭 업데이트
        self._metrics['events_distributed'] += 1

        if distribution_count > 0:
            latency_ms = (time.monotonic() - start_time) * 1000
            self._update_avg_latency(latency_ms)

    async def _enqueue_event(self, event: BaseWebSocketEvent, callback_info: CallbackInfo) -> None:
        """이벤트를 콜백 큐에 추가"""
        queue = callback_info.queue

        # 큐 사용률 확인
        queue_size = queue.qsize()
        if queue_size >= self._queue_warning_threshold:
            self.logger.warning(
                f"큐 사용률 높음: {callback_info.component_id} "
                f"({queue_size}/{queue.maxsize})"
            )

        # 큐가 가득 찬 경우 백프레셔 처리
        if queue.full():
            self._metrics['queue_overflows'] += 1
            success = await self.backpressure_handler.handle_queue_overflow(
                queue, event, callback_info
            )
            if not success:
                self.logger.warning(f"이벤트 폐기: {callback_info.component_id}")
                return
        else:
            # 정상적으로 큐에 추가
            queued_event = QueuedEvent(event=event)
            queue.put_nowait(queued_event)

    async def _process_callback_queue(self, callback_id: str) -> None:
        """콜백 큐 처리 (백그라운드 태스크)"""
        callback_info = self._callbacks.get(callback_id)
        if not callback_info:
            return

        self.logger.debug(f"콜백 프로세서 시작: {callback_id}")

        try:
            while self._running and callback_info.is_active:
                try:
                    # 큐에서 이벤트 대기 (타임아웃 포함)
                    queued_event = await asyncio.wait_for(
                        callback_info.queue.get(),
                        timeout=1.0
                    )

                    # 콜백 호출
                    await self._invoke_callback(callback_info, queued_event.event)

                except asyncio.TimeoutError:
                    continue  # 타임아웃은 정상
                except Exception as e:
                    self.logger.error(f"콜백 프로세서 오류: {callback_id}, {e}")
                    callback_info.error_count += 1
                    await asyncio.sleep(0.1)  # 연속 오류 방지

        finally:
            self.logger.debug(f"콜백 프로세서 종료: {callback_id}")

    async def _invoke_callback(self, callback_info: CallbackInfo, event: BaseWebSocketEvent) -> None:
        """콜백 호출 (에러 격리)"""
        try:
            if asyncio.iscoroutinefunction(callback_info.callback):
                await callback_info.callback(event)
            else:
                callback_info.callback(event)

            # 성공 기록
            callback_info.last_success = time.monotonic()
            self._metrics['callbacks_called'] += 1

        except Exception as e:
            # 에러 기록 (전파하지 않음)
            callback_info.error_count += 1
            callback_info.last_error = e
            self._metrics['callback_errors'] += 1

            self.logger.error(
                f"콜백 오류: {callback_info.component_id} "
                f"({callback_info.data_type.value}), {e}"
            )

    def _update_avg_latency(self, latency_ms: float) -> None:
        """평균 지연 시간 업데이트 (이동 평균)"""
        current_avg = self._metrics['avg_distribution_latency_ms']
        alpha = 0.1  # 이동 평균 가중치
        self._metrics['avg_distribution_latency_ms'] = (
            alpha * latency_ms + (1 - alpha) * current_avg
        )

    # =============================================================================
    # 모니터링 및 상태 조회
    # =============================================================================

    def get_callback_stats(self) -> Dict[str, Dict[str, Any]]:
        """콜백별 통계"""
        stats = {}

        for callback_id, callback_info in self._callbacks.items():
            stats[callback_id] = {
                'component_id': callback_info.component_id,
                'data_type': callback_info.data_type.value,
                'queue_size': callback_info.queue.qsize(),
                'queue_maxsize': callback_info.queue.maxsize,
                'error_count': callback_info.error_count,
                'last_error': str(callback_info.last_error) if callback_info.last_error else None,
                'last_success': callback_info.last_success,
                'is_active': callback_info.is_active
            }

        return stats

    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 조회"""
        backpressure_stats = self.backpressure_handler.get_stats()

        return {
            **self._metrics,
            **backpressure_stats,
            'active_callbacks': len([c for c in self._callbacks.values() if c.is_active]),
            'total_callbacks': len(self._callbacks),
            'processor_tasks': len(self._processor_tasks),
            'data_type_distribution': {
                data_type.value: len(callback_ids)
                for data_type, callback_ids in self._data_type_callbacks.items()
            }
        }

    def get_queue_status(self) -> Dict[str, Dict[str, Any]]:
        """큐 상태 조회"""
        status = {}

        for callback_id, callback_info in self._callbacks.items():
            queue = callback_info.queue
            usage_ratio = queue.qsize() / queue.maxsize if queue.maxsize > 0 else 0

            status[callback_id] = {
                'component_id': callback_info.component_id,
                'size': queue.qsize(),
                'maxsize': queue.maxsize,
                'usage_ratio': usage_ratio,
                'is_warning': usage_ratio >= self.backpressure_handler.config.warning_threshold,
                'is_full': queue.full()
            }

        return status


class DataRoutingEngine:
    """데이터 라우팅 엔진 - 메인 인터페이스"""

    def __init__(self, backpressure_config: BackpressureConfig):
        self.logger = create_component_logger("DataRoutingEngine")
        self.fanout_hub = FanoutHub(backpressure_config)

        # 라우팅 통계
        self._routing_stats = {
            'total_events': 0,
            'routed_events': 0,
            'unrouted_events': 0,
            'error_events': 0
        }

        self.logger.info("데이터 라우팅 엔진 초기화 완료")

    async def start(self) -> None:
        """라우팅 엔진 시작"""
        await self.fanout_hub.start()
        self.logger.info("데이터 라우팅 엔진 시작")

    async def stop(self) -> None:
        """라우팅 엔진 중지"""
        await self.fanout_hub.stop()
        self.logger.info("데이터 라우팅 엔진 중지")

    def register_data_consumer(
        self,
        consumer_id: str,
        callback: Callable[[BaseWebSocketEvent], None],
        component_id: str,
        data_type: DataType
    ) -> None:
        """데이터 소비자 등록"""
        self.fanout_hub.register_callback(consumer_id, callback, component_id, data_type)
        self.logger.debug(f"데이터 소비자 등록: {consumer_id}")

    def unregister_data_consumer(self, consumer_id: str) -> None:
        """데이터 소비자 해제"""
        self.fanout_hub.unregister_callback(consumer_id)
        self.logger.debug(f"데이터 소비자 해제: {consumer_id}")

    async def route_event(self, event: BaseWebSocketEvent, data_type: DataType) -> None:
        """이벤트 라우팅"""
        self._routing_stats['total_events'] += 1

        try:
            await self.fanout_hub.distribute_event(event, data_type)
            self._routing_stats['routed_events'] += 1

        except Exception as e:
            self._routing_stats['error_events'] += 1
            self.logger.error(f"이벤트 라우팅 오류: {type(event).__name__}, {e}")

    # =============================================================================
    # 상태 조회
    # =============================================================================

    def get_routing_stats(self) -> Dict[str, Any]:
        """라우팅 통계"""
        fanout_metrics = self.fanout_hub.get_performance_metrics()

        return {
            **self._routing_stats,
            'fanout_metrics': fanout_metrics,
            'success_ratio': (
                self._routing_stats['routed_events'] / max(1, self._routing_stats['total_events'])
            )
        }

    def get_consumer_stats(self) -> Dict[str, Dict[str, Any]]:
        """소비자별 통계"""
        return self.fanout_hub.get_callback_stats()

    def get_queue_status(self) -> Dict[str, Dict[str, Any]]:
        """큐 상태"""
        return self.fanout_hub.get_queue_status()
