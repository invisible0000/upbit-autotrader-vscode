import asyncio
import logging
import time
from typing import List, Callable, Dict, Any, Optional, Type
from collections import defaultdict, deque
from datetime import datetime

from upbit_auto_trading.domain.events.base_domain_event import DomainEvent
from upbit_auto_trading.infrastructure.events.bus.event_bus_interface import (
    IEventBus, EventSubscription, EventProcessingResult, IEventStorage
)


class InMemoryEventBus(IEventBus):
    """메모리 기반 이벤트 버스 구현"""

    def __init__(self, event_storage: Optional[IEventStorage] = None,
                 max_queue_size: int = 10000, worker_count: int = 4,
                 batch_size: int = 10, batch_timeout_seconds: float = 1.0):
        self._subscriptions: Dict[Type[DomainEvent], List[EventSubscription]] = defaultdict(list)
        self._event_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._event_storage = event_storage
        self._worker_count = worker_count
        self._batch_size = batch_size
        self._batch_timeout = batch_timeout_seconds

        # 실행 상태
        self._is_running = False
        self._workers: List[asyncio.Task] = []
        self._lock = asyncio.Lock()

        # 통계
        self._stats = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'processing_time_total': 0.0,
            'last_reset': datetime.now()
        }

        # 실패한 이벤트 관리
        self._failed_events: deque = deque(maxlen=1000)
        self._retry_queue: asyncio.Queue = asyncio.Queue()

        self._logger = logging.getLogger(__name__)

    async def publish(self, event: DomainEvent) -> None:
        """단일 이벤트 발행"""
        if not self._is_running:
            raise RuntimeError("이벤트 버스가 시작되지 않았습니다")

        try:
            # 이벤트 저장 (선택적)
            if self._event_storage:
                stored_event_id = await self._event_storage.store_event(event)
                # DomainEvent의 event_id를 직접 수정할 수 없으므로 내부적으로 관리

            # 큐에 추가
            await self._event_queue.put(event)

            async with self._lock:
                self._stats['events_published'] += 1

            self._logger.debug(f"이벤트 발행됨: {event.__class__.__name__} (ID: {event.event_id})")

        except asyncio.QueueFull:
            self._logger.error(f"이벤트 큐가 가득참. 이벤트 삭제: {event.__class__.__name__}")
            raise RuntimeError("이벤트 큐 용량 초과")

        except Exception as e:
            self._logger.error(f"이벤트 발행 실패: {event.__class__.__name__} - {e}")
            raise

    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """배치 이벤트 발행"""
        if not events:
            return

        # 이벤트 저장 (배치)
        if self._event_storage:
            for event in events:
                await self._event_storage.store_event(event)

        # 큐에 배치 추가
        for event in events:
            try:
                await self._event_queue.put(event)
                async with self._lock:
                    self._stats['events_published'] += 1
            except asyncio.QueueFull:
                self._logger.error(f"배치 이벤트 발행 중 큐 가득참: {event.__class__.__name__}")
                break

        self._logger.info(f"배치 이벤트 {len(events)}개 발행 완료")

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable,
                  is_async: bool = True, priority: int = 1,
                  retry_count: int = 3) -> str:
        """이벤트 구독"""
        subscription = EventSubscription(
            event_type=event_type,
            handler=handler,
            is_async=is_async,
            priority=priority,
            retry_count=retry_count
        )

        # 우선순위순으로 삽입 정렬
        subscriptions = self._subscriptions[event_type]
        insert_index = 0
        for i, existing in enumerate(subscriptions):
            if subscription.priority < existing.priority:
                insert_index = i
                break
            insert_index = i + 1

        subscriptions.insert(insert_index, subscription)

        self._logger.info(f"이벤트 구독 등록: {event_type.__name__} -> {handler.__name__}")
        return subscription.subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """구독 취소"""
        for event_type, subscriptions in self._subscriptions.items():
            for i, subscription in enumerate(subscriptions):
                if subscription.subscription_id == subscription_id:
                    del subscriptions[i]
                    self._logger.info(f"구독 취소됨: {subscription_id}")
                    return True

        return False

    async def start(self) -> None:
        """이벤트 버스 시작"""
        if self._is_running:
            return

        self._is_running = True

        # 워커 태스크 시작
        for i in range(self._worker_count):
            worker_task = asyncio.create_task(
                self._worker_loop(f"worker-{i}")
            )
            self._workers.append(worker_task)

        # 재시도 워커 시작
        retry_worker = asyncio.create_task(self._retry_worker_loop())
        self._workers.append(retry_worker)

        self._logger.info(f"이벤트 버스 시작됨 (워커 {self._worker_count}개)")

    async def stop(self) -> None:
        """이벤트 버스 중지"""
        if not self._is_running:
            return

        self._is_running = False

        # 워커 태스크 종료
        for worker in self._workers:
            worker.cancel()

        # 완료 대기
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

        self._logger.info("이벤트 버스 중지됨")

    def get_statistics(self) -> Dict[str, Any]:
        """처리 통계 조회"""
        current_time = datetime.now()
        uptime = current_time - self._stats['last_reset']

        avg_processing_time = 0.0
        if self._stats['events_processed'] > 0:
            avg_processing_time = (
                self._stats['processing_time_total'] / self._stats['events_processed']
            )

        return {
            'uptime_seconds': uptime.total_seconds(),
            'events_published': self._stats['events_published'],
            'events_processed': self._stats['events_processed'],
            'events_failed': self._stats['events_failed'],
            'avg_processing_time_ms': round(avg_processing_time, 2),
            'queue_size': self._event_queue.qsize(),
            'retry_queue_size': self._retry_queue.qsize(),
            'failed_events_count': len(self._failed_events),
            'subscription_count': sum(len(subs) for subs in self._subscriptions.values()),
            'is_running': self._is_running,
            'worker_count': len(self._workers)
        }

    def get_failed_events(self) -> List[Dict[str, Any]]:
        """실패한 이벤트 목록 조회"""
        return list(self._failed_events)

    def clear_failed_events(self) -> None:
        """실패한 이벤트 목록 초기화"""
        self._failed_events.clear()
        self._logger.info("실패한 이벤트 목록이 초기화되었습니다")

    async def _worker_loop(self, worker_name: str) -> None:
        """워커 루프"""
        self._logger.debug(f"워커 시작됨: {worker_name}")

        while self._is_running:
            try:
                # 배치로 이벤트 수집
                events = []
                deadline = time.time() + self._batch_timeout

                while len(events) < self._batch_size and time.time() < deadline:
                    try:
                        timeout = max(0.1, deadline - time.time())
                        event = await asyncio.wait_for(
                            self._event_queue.get(),
                            timeout=timeout
                        )
                        events.append(event)
                    except asyncio.TimeoutError:
                        break

                # 수집된 이벤트 처리
                if events:
                    await self._process_events_batch(events, worker_name)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"워커 루프 오류 {worker_name}: {e}")
                await asyncio.sleep(1)

        self._logger.debug(f"워커 종료됨: {worker_name}")

    async def _process_events_batch(self, events: List[DomainEvent],
                                    worker_name: str) -> None:
        """이벤트 배치 처리"""
        for event in events:
            await self._process_single_event(event, worker_name)

    async def _process_single_event(self, event: DomainEvent,
                                    worker_name: str) -> None:
        """단일 이벤트 처리"""
        event_type = type(event)
        subscriptions = self._subscriptions.get(event_type, [])

        if not subscriptions:
            self._logger.debug(f"구독자 없음: {event_type.__name__}")
            return

        start_time = time.time()
        success_count = 0
        failure_count = 0

        # 모든 구독자에게 이벤트 전달
        for subscription in subscriptions:
            try:
                result = await self._invoke_handler(event, subscription, worker_name)

                if result.success:
                    success_count += 1
                else:
                    failure_count += 1
                    await self._handle_processing_failure(event, subscription, result)

                # 결과 저장
                if self._event_storage and event.event_id:
                    await self._event_storage.mark_event_processed(event.event_id, result)

            except Exception as e:
                failure_count += 1
                error_msg = f"핸들러 호출 실패: {subscription.handler.__name__} - {e}"
                self._logger.error(error_msg)

                result = EventProcessingResult(
                    event_id=event.event_id or 'unknown',
                    success=False,
                    error_message=error_msg
                )
                await self._handle_processing_failure(event, subscription, result)

        # 통계 업데이트
        processing_time = (time.time() - start_time) * 1000
        async with self._lock:
            self._stats['events_processed'] += 1
            self._stats['events_failed'] += failure_count
            self._stats['processing_time_total'] += processing_time

        self._logger.debug(
            f"이벤트 처리 완료: {event_type.__name__} "
            f"(성공: {success_count}, 실패: {failure_count}, "
            f"처리시간: {processing_time:.1f}ms, 워커: {worker_name})"
        )

    async def _invoke_handler(self, event: DomainEvent,
                              subscription: EventSubscription,
                              worker_name: str) -> EventProcessingResult:
        """핸들러 호출"""
        start_time = time.time()

        try:
            if subscription.is_async:
                if asyncio.iscoroutinefunction(subscription.handler):
                    await subscription.handler(event)
                else:
                    # 동기 함수를 스레드풀에서 실행
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, subscription.handler, event)
            else:
                subscription.handler(event)

            processing_time = (time.time() - start_time) * 1000

            return EventProcessingResult(
                event_id=event.event_id or 'unknown',
                success=True,
                processing_time_ms=processing_time
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            error_msg = f"핸들러 실행 오류: {subscription.handler.__name__} - {str(e)}"

            return EventProcessingResult(
                event_id=event.event_id or 'unknown',
                success=False,
                error_message=error_msg,
                processing_time_ms=processing_time
            )

    async def _handle_processing_failure(self, event: DomainEvent,
                                         subscription: EventSubscription,
                                         result: EventProcessingResult) -> None:
        """처리 실패 이벤트 처리"""
        # 재시도 큐에 추가 (재시도 횟수 체크)
        if result.retry_attempt < subscription.retry_count:
            retry_event = {
                'event': event,
                'subscription': subscription,
                'retry_attempt': result.retry_attempt + 1,
                'scheduled_time': time.time() + (2 ** result.retry_attempt)  # 지수 백오프
            }

            try:
                await self._retry_queue.put(retry_event)
                self._logger.info(
                    f"재시도 스케줄됨: {event.__class__.__name__} "
                    f"(시도 {result.retry_attempt + 1}/{subscription.retry_count})"
                )
            except asyncio.QueueFull:
                self._logger.error("재시도 큐가 가득참")
        else:
            # 최대 재시도 횟수 초과 - 실패 이벤트로 기록
            self._failed_events.append({
                'event': event,
                'subscription': subscription,
                'final_result': result,
                'failed_at': datetime.now()
            })

            self._logger.error(
                f"이벤트 처리 최종 실패: {event.__class__.__name__} "
                f"- {result.error_message}"
            )

    async def _retry_worker_loop(self) -> None:
        """재시도 워커 루프"""
        self._logger.debug("재시도 워커 시작됨")

        while self._is_running:
            try:
                retry_item = await asyncio.wait_for(
                    self._retry_queue.get(),
                    timeout=1.0
                )

                # 스케줄된 시간까지 대기
                wait_time = retry_item['scheduled_time'] - time.time()
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

                # 재시도 실행
                result = await self._invoke_handler(
                    retry_item['event'],
                    retry_item['subscription'],
                    'retry-worker'
                )

                result.retry_attempt = retry_item['retry_attempt']

                if not result.success:
                    await self._handle_processing_failure(
                        retry_item['event'],
                        retry_item['subscription'],
                        result
                    )
                else:
                    self._logger.info(
                        f"재시도 성공: {retry_item['event'].__class__.__name__} "
                        f"(시도 {result.retry_attempt})"
                    )

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"재시도 워커 오류: {e}")
                await asyncio.sleep(1)

        self._logger.debug("재시도 워커 종료됨")
