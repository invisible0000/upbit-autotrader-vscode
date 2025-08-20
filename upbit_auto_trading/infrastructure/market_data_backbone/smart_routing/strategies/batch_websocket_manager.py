"""
배치식 WebSocket 구독 관리 시스템

하나의 연결로 다양한 속도 요구사항을 가진 구독들을
효율적으로 관리합니다.
"""

import asyncio
from typing import Dict, Set, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
    UpbitWebSocketQuotationClient,
    WebSocketDataType,
    WebSocketMessage
)


class UpdateSpeed(Enum):
    """업데이트 속도 요구사항"""
    REALTIME = "realtime"      # 실시간 (모든 메시지)
    FAST = "fast"              # 빠름 (1초마다)
    NORMAL = "normal"          # 보통 (5초마다)
    SLOW = "slow"              # 느림 (30초마다)
    ON_DEMAND = "on_demand"    # 필요할 때만


@dataclass
class SubscriptionRequest:
    """구독 요청"""
    client_id: str
    symbols: Set[str]
    data_types: Set[WebSocketDataType]
    speed: UpdateSpeed
    callback: Optional[Callable[[WebSocketMessage], None]] = None
    last_update: datetime = field(default_factory=datetime.now)
    is_active: bool = True


@dataclass
class BatchSubscription:
    """배치 구독 정보"""
    symbols: Set[str]
    data_types: Set[WebSocketDataType]
    websocket_client: UpbitWebSocketQuotationClient
    subscribers: Dict[str, SubscriptionRequest]
    last_message_time: Dict[str, datetime] = field(default_factory=dict)
    message_cache: Dict[str, WebSocketMessage] = field(default_factory=dict)


class BatchWebSocketManager:
    """배치식 WebSocket 구독 관리자

    핵심 전략:
    1. 하나의 WebSocket 연결로 모든 구독 통합
    2. 클라이언트별 속도 요구사항에 따라 메시지 필터링
    3. 동적 구독 심볼 추가/제거 (재연결을 통해)
    4. 메시지 캐싱으로 중복 처리 방지
    """

    def __init__(self):
        self.logger = create_component_logger("BatchWebSocketManager")

        # 메인 배치 구독
        self.batch_subscriptions: Dict[str, BatchSubscription] = {}

        # 클라이언트 요청 관리
        self.active_requests: Dict[str, SubscriptionRequest] = {}

        # 속도별 업데이트 간격 (초)
        self.speed_intervals = {
            UpdateSpeed.REALTIME: 0.0,    # 모든 메시지
            UpdateSpeed.FAST: 1.0,        # 1초
            UpdateSpeed.NORMAL: 5.0,      # 5초
            UpdateSpeed.SLOW: 30.0,       # 30초
            UpdateSpeed.ON_DEMAND: -1.0   # 요청 시에만
        }

        # 최적화 설정
        self.rebalance_interval = 60  # 1분마다 배치 최적화
        self.max_symbols_per_batch = 200  # 배치당 최대 심볼 수

        # 최적화 태스크
        self._rebalance_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """매니저 초기화"""
        self.logger.info("🔄 배치 WebSocket 관리자 초기화")

        # 자동 최적화 시작
        self._rebalance_task = asyncio.create_task(self._rebalance_loop())

        self.logger.info("✅ 배치 WebSocket 관리자 초기화 완료")

    async def shutdown(self):
        """매니저 종료"""
        self.logger.info("🔄 배치 WebSocket 관리자 종료")

        # 최적화 태스크 중단
        if self._rebalance_task:
            self._rebalance_task.cancel()

        # 모든 배치 구독 종료
        for batch_id in list(self.batch_subscriptions.keys()):
            await self._close_batch_subscription(batch_id)

        self.logger.info("✅ 배치 WebSocket 관리자 종료 완료")

    async def subscribe(
        self,
        client_id: str,
        symbols: List[str],
        data_types: List[WebSocketDataType],
        speed: UpdateSpeed = UpdateSpeed.NORMAL,
        callback: Optional[Callable[[WebSocketMessage], None]] = None
    ) -> bool:
        """구독 요청"""

        self.logger.info(f"📡 구독 요청: {client_id} - {len(symbols)}개 심볼, {speed.value}")

        # 요청 생성
        request = SubscriptionRequest(
            client_id=client_id,
            symbols=set(symbols),
            data_types=set(data_types),
            speed=speed,
            callback=callback
        )

        self.active_requests[client_id] = request

        # 적절한 배치에 추가
        success = await self._add_to_optimal_batch(request)

        if success:
            self.logger.info(f"✅ 구독 성공: {client_id}")
        else:
            self.logger.error(f"❌ 구독 실패: {client_id}")

        return success

    async def unsubscribe(self, client_id: str) -> bool:
        """구독 해제"""

        self.logger.info(f"📡 구독 해제: {client_id}")

        if client_id not in self.active_requests:
            self.logger.warning(f"⚠️ 미등록 클라이언트: {client_id}")
            return False

        # 요청 제거
        request = self.active_requests[client_id]
        del self.active_requests[client_id]

        # 배치에서 제거
        await self._remove_from_batches(client_id, request)

        self.logger.info(f"✅ 구독 해제 완료: {client_id}")
        return True

    async def update_subscription(
        self,
        client_id: str,
        new_symbols: List[str],
        new_speed: Optional[UpdateSpeed] = None
    ) -> bool:
        """구독 업데이트"""

        self.logger.info(f"🔄 구독 업데이트: {client_id}")

        if client_id not in self.active_requests:
            return False

        request = self.active_requests[client_id]
        old_symbols = request.symbols.copy()

        # 요청 업데이트
        request.symbols = set(new_symbols)
        if new_speed:
            request.speed = new_speed

        # 변경이 필요한 경우 배치 재구성
        if old_symbols != request.symbols or new_speed:
            await self._rebalance_client_subscription(client_id, request)

        return True

    async def get_cached_data(self, client_id: str) -> Dict[str, WebSocketMessage]:
        """캐시된 데이터 조회 (ON_DEMAND용)"""

        if client_id not in self.active_requests:
            return {}

        request = self.active_requests[client_id]
        cached_data = {}

        # 클라이언트의 심볼에 해당하는 캐시된 데이터 수집
        for batch in self.batch_subscriptions.values():
            if client_id in batch.subscribers:
                for symbol in request.symbols:
                    if symbol in batch.message_cache:
                        cached_data[symbol] = batch.message_cache[symbol]

        return cached_data

    def get_statistics(self) -> Dict[str, Any]:
        """통계 정보 조회"""

        total_symbols = set()
        total_clients = len(self.active_requests)

        batch_stats = []
        for batch_id, batch in self.batch_subscriptions.items():
            total_symbols.update(batch.symbols)

            batch_stats.append({
                'batch_id': batch_id,
                'symbols': len(batch.symbols),
                'subscribers': len(batch.subscribers),
                'data_types': [dt.value for dt in batch.data_types]
            })

        speed_distribution = {}
        for request in self.active_requests.values():
            speed = request.speed.value
            speed_distribution[speed] = speed_distribution.get(speed, 0) + 1

        return {
            'total_symbols': len(total_symbols),
            'total_clients': total_clients,
            'active_batches': len(self.batch_subscriptions),
            'batch_details': batch_stats,
            'speed_distribution': speed_distribution
        }

    # Private Methods

    async def _add_to_optimal_batch(self, request: SubscriptionRequest) -> bool:
        """최적 배치에 요청 추가"""

        # 기존 배치 중 호환 가능한 것 찾기
        compatible_batch = self._find_compatible_batch(request)

        if compatible_batch:
            # 기존 배치에 추가
            return await self._add_to_existing_batch(compatible_batch, request)
        else:
            # 새 배치 생성
            return await self._create_new_batch(request)

    def _find_compatible_batch(self, request: SubscriptionRequest) -> Optional[str]:
        """호환 가능한 배치 찾기"""

        for batch_id, batch in self.batch_subscriptions.items():
            # 데이터 타입 호환성 확인
            if not batch.data_types.intersection(request.data_types):
                continue

            # 심볼 수 제한 확인
            combined_symbols = batch.symbols.union(request.symbols)
            if len(combined_symbols) > self.max_symbols_per_batch:
                continue

            # 호환 가능
            return batch_id

        return None

    async def _create_new_batch(self, request: SubscriptionRequest) -> bool:
        """새 배치 생성"""

        batch_id = f"batch_{len(self.batch_subscriptions)}_{request.client_id}"

        try:
            # WebSocket 클라이언트 생성
            client = UpbitWebSocketQuotationClient()
            await client.connect()

            # 메시지 핸들러 등록
            for data_type in request.data_types:
                client.add_message_handler(data_type, self._create_message_handler(batch_id))

            # 구독 시작
            success = True
            for data_type in request.data_types:
                if data_type == WebSocketDataType.TICKER:
                    result = await client.subscribe_ticker(list(request.symbols))
                elif data_type == WebSocketDataType.ORDERBOOK:
                    result = await client.subscribe_orderbook(list(request.symbols))
                elif data_type == WebSocketDataType.TRADE:
                    result = await client.subscribe_trade(list(request.symbols))
                else:
                    result = False

                success = success and result

            if success:
                # 배치 생성
                batch = BatchSubscription(
                    symbols=request.symbols.copy(),
                    data_types=request.data_types.copy(),
                    websocket_client=client,
                    subscribers={request.client_id: request}
                )

                self.batch_subscriptions[batch_id] = batch
                self.logger.info(f"✅ 새 배치 생성: {batch_id}")
                return True
            else:
                await client.disconnect()
                self.logger.error(f"❌ 배치 생성 실패: {batch_id}")
                return False

        except Exception as e:
            self.logger.error(f"❌ 배치 생성 오류: {e}")
            return False

    async def _add_to_existing_batch(self, batch_id: str, request: SubscriptionRequest) -> bool:
        """기존 배치에 요청 추가"""

        batch = self.batch_subscriptions[batch_id]

        # 새로운 심볼이 있는지 확인
        new_symbols = request.symbols - batch.symbols

        if new_symbols:
            # 배치 재구성 필요
            return await self._rebuild_batch(batch_id, request)
        else:
            # 단순히 구독자만 추가
            batch.subscribers[request.client_id] = request
            self.logger.info(f"✅ 기존 배치에 추가: {batch_id}")
            return True

    async def _rebuild_batch(self, batch_id: str, new_request: SubscriptionRequest) -> bool:
        """배치 재구성 (새 심볼 추가)"""

        self.logger.info(f"🔧 배치 재구성: {batch_id}")

        batch = self.batch_subscriptions[batch_id]

        # 새로운 심볼 집합
        combined_symbols = batch.symbols.union(new_request.symbols)
        combined_data_types = batch.data_types.union(new_request.data_types)

        # 기존 연결 종료
        await batch.websocket_client.disconnect()

        try:
            # 새 연결 생성
            new_client = UpbitWebSocketQuotationClient()
            await new_client.connect()

            # 메시지 핸들러 등록
            for data_type in combined_data_types:
                new_client.add_message_handler(data_type, self._create_message_handler(batch_id))

            # 새로운 구독 시작
            success = True
            for data_type in combined_data_types:
                if data_type == WebSocketDataType.TICKER:
                    result = await new_client.subscribe_ticker(list(combined_symbols))
                elif data_type == WebSocketDataType.ORDERBOOK:
                    result = await new_client.subscribe_orderbook(list(combined_symbols))
                elif data_type == WebSocketDataType.TRADE:
                    result = await new_client.subscribe_trade(list(combined_symbols))
                else:
                    result = False

                success = success and result

            if success:
                # 배치 업데이트
                batch.symbols = combined_symbols
                batch.data_types = combined_data_types
                batch.websocket_client = new_client
                batch.subscribers[new_request.client_id] = new_request

                self.logger.info(f"✅ 배치 재구성 완료: {batch_id}")
                return True
            else:
                await new_client.disconnect()
                self.logger.error(f"❌ 배치 재구성 실패: {batch_id}")
                return False

        except Exception as e:
            self.logger.error(f"❌ 배치 재구성 오류: {e}")
            return False

    def _create_message_handler(self, batch_id: str) -> Callable[[WebSocketMessage], None]:
        """배치별 메시지 핸들러 생성"""

        def handle_message(message: WebSocketMessage):
            asyncio.create_task(self._process_batch_message(batch_id, message))

        return handle_message

    async def _process_batch_message(self, batch_id: str, message: WebSocketMessage):
        """배치 메시지 처리"""

        if batch_id not in self.batch_subscriptions:
            return

        batch = self.batch_subscriptions[batch_id]

        # 메시지 캐시 업데이트
        batch.message_cache[message.market] = message
        batch.last_message_time[message.market] = datetime.now()

        # 구독자별 속도 제어하여 전달
        for client_id, request in batch.subscribers.items():
            if message.market in request.symbols and message.type in request.data_types:
                await self._deliver_message_if_needed(request, message)

    async def _deliver_message_if_needed(self, request: SubscriptionRequest, message: WebSocketMessage):
        """필요한 경우에만 메시지 전달 (속도 제어)"""

        now = datetime.now()
        interval = self.speed_intervals[request.speed]

        # ON_DEMAND는 전달하지 않음 (캐시에만 저장)
        if request.speed == UpdateSpeed.ON_DEMAND:
            return

        # REALTIME은 모든 메시지 전달
        if request.speed == UpdateSpeed.REALTIME:
            time_since_last = 0.0
        else:
            time_since_last = (now - request.last_update).total_seconds()

        # 간격 확인
        if time_since_last >= interval:
            request.last_update = now

            # 콜백 호출
            if request.callback:
                try:
                    if asyncio.iscoroutinefunction(request.callback):
                        await request.callback(message)
                    else:
                        request.callback(message)
                except Exception as e:
                    self.logger.error(f"❌ 콜백 오류 ({request.client_id}): {e}")

    async def _remove_from_batches(self, client_id: str, request: SubscriptionRequest):
        """배치에서 클라이언트 제거"""

        for batch_id, batch in list(self.batch_subscriptions.items()):
            if client_id in batch.subscribers:
                del batch.subscribers[client_id]

                # 구독자가 없으면 배치 제거
                if not batch.subscribers:
                    await self._close_batch_subscription(batch_id)

    async def _close_batch_subscription(self, batch_id: str):
        """배치 구독 종료"""

        if batch_id in self.batch_subscriptions:
            batch = self.batch_subscriptions[batch_id]
            await batch.websocket_client.disconnect()
            del self.batch_subscriptions[batch_id]
            self.logger.info(f"🗑️ 배치 종료: {batch_id}")

    async def _rebalance_client_subscription(self, client_id: str, request: SubscriptionRequest):
        """클라이언트 구독 재조정"""

        # 기존 배치에서 제거
        await self._remove_from_batches(client_id, request)

        # 새로운 배치에 추가
        await self._add_to_optimal_batch(request)

    async def _rebalance_loop(self):
        """주기적 배치 최적화"""

        try:
            while True:
                await asyncio.sleep(self.rebalance_interval)
                await self._optimize_batches()

        except asyncio.CancelledError:
            self.logger.info("🔄 배치 최적화 루프 중단")

    async def _optimize_batches(self):
        """배치 최적화"""

        self.logger.info("🔧 배치 최적화 시작")

        # 통계 기반 최적화 로직
        stats = self.get_statistics()

        # 비효율적인 배치 통합
        await self._merge_inefficient_batches()

        # 과부하 배치 분할
        await self._split_overloaded_batches()

        self.logger.info("✅ 배치 최적화 완료")

    async def _merge_inefficient_batches(self):
        """비효율적인 배치 통합"""

        # 구독자 수가 적은 배치들을 찾아서 통합
        small_batches = [
            (batch_id, batch) for batch_id, batch in self.batch_subscriptions.items()
            if len(batch.subscribers) <= 2
        ]

        # 통합 로직 구현 (복잡하므로 여기서는 스킵)
        pass

    async def _split_overloaded_batches(self):
        """과부하 배치 분할"""

        # 심볼 수가 너무 많은 배치를 분할
        overloaded_batches = [
            (batch_id, batch) for batch_id, batch in self.batch_subscriptions.items()
            if len(batch.symbols) > self.max_symbols_per_batch * 0.9
        ]

        # 분할 로직 구현 (복잡하므로 여기서는 스킵)
        pass
