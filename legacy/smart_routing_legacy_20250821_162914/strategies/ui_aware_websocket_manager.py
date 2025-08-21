"""
UI 상태 기반 WebSocket 자원 관리 시스템

화면별 생명주기에 따라 WebSocket 연결을 최적화하여
자원 효율성과 성능을 동시에 달성합니다.
"""

import asyncio
from typing import Dict, List, Set, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import weakref

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
    UpbitWebSocketQuotationClient,
    WebSocketDataType
)


class ScreenType(Enum):
    """화면 타입별 WebSocket 사용 우선순위"""
    CRITICAL = "critical"      # 항상 활성 (실시간 거래, 알림)
    ON_DEMAND = "on_demand"    # 화면 열릴 때만 (차트뷰, 대시보드)
    BACKGROUND = "background"  # REST API 우선 (설정, 히스토리)


class SubscriptionPriority(Enum):
    """구독 우선순위"""
    CRITICAL = "critical"      # 해제 금지 (포트폴리오, 거래 알림)
    SHARED = "shared"          # 공유 구독 (코인 리스트)
    EXCLUSIVE = "exclusive"    # 독점 구독 (선택된 심볼 호가)
    TEMPORARY = "temporary"    # 임시 구독 (분석 도구)


@dataclass
class ScreenSubscription:
    """화면별 구독 정보"""
    screen_name: str
    screen_type: ScreenType
    symbols: Set[str]
    data_types: Set[WebSocketDataType]
    priority: SubscriptionPriority
    created_at: datetime
    last_activity: datetime
    is_active: bool = True


@dataclass
class SharedSubscription:
    """공유 구독 정보"""
    subscription_id: str
    symbols: Set[str]
    data_types: Set[WebSocketDataType]
    reference_count: int
    screens: Set[str]
    websocket_client: Optional[UpbitWebSocketQuotationClient] = None
    created_at: datetime = None


class UIAwareWebSocketManager:
    """UI 상태 기반 WebSocket 자원 관리자

    주요 기능:
    1. 화면별 WebSocket 생명주기 관리
    2. 공유 구독을 통한 자원 효율성
    3. 자동 최적화 및 정리
    4. 실시간 모니터링
    """

    def __init__(self):
        self.logger = create_component_logger("UIAwareWebSocketManager")

        # 화면 상태 추적
        self.active_screens: Set[str] = set()
        self.screen_subscriptions: Dict[str, ScreenSubscription] = {}

        # 공유 구독 관리
        self.shared_subscriptions: Dict[str, SharedSubscription] = {}

        # Critical 구독 (항상 유지)
        self.critical_subscriptions: Dict[str, ScreenSubscription] = {}

        # WebSocket 연결 풀
        self.websocket_pools: Dict[str, UpbitWebSocketQuotationClient] = {}

        # 최적화 설정
        self.optimization_interval = 300  # 5분
        self.idle_threshold = 600        # 10분
        self.max_connections = 15        # 최대 동시 연결 수

        # 성능 메트릭
        self.performance_metrics = {
            "total_messages": 0,
            "messages_per_second": 0.0,
            "last_optimization": datetime.now(),
            "memory_usage_mb": 0.0
        }

        # 최적화 루프 태스크
        self._optimization_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """매니저 초기화"""
        self.logger.info("🎮 UI 상태 기반 WebSocket 매니저 초기화 시작")

        # 자동 최적화 루프 시작
        self._optimization_task = asyncio.create_task(self._optimization_loop())

        self.logger.info("✅ UI 상태 기반 WebSocket 매니저 초기화 완료")

    async def shutdown(self):
        """매니저 종료"""
        self.logger.info("🔄 UI 상태 기반 WebSocket 매니저 종료 시작")

        # 최적화 루프 중단
        if self._optimization_task:
            self._optimization_task.cancel()

        # 모든 구독 해제
        await self._cleanup_all_subscriptions()

        self.logger.info("✅ UI 상태 기반 WebSocket 매니저 종료 완료")

    async def on_screen_opened(
        self,
        screen_name: str,
        screen_type: ScreenType,
        symbols: List[str],
        data_types: List[WebSocketDataType],
        priority: SubscriptionPriority = SubscriptionPriority.EXCLUSIVE
    ):
        """화면이 열릴 때 WebSocket 구독 시작"""

        self.logger.info(f"📱 화면 열림: {screen_name} ({screen_type.value})")

        self.active_screens.add(screen_name)

        # 화면 타입별 처리
        if screen_type == ScreenType.CRITICAL:
            await self._handle_critical_screen(screen_name, symbols, data_types)

        elif screen_type == ScreenType.ON_DEMAND:
            await self._handle_on_demand_screen(screen_name, symbols, data_types, priority)

        else:  # BACKGROUND
            self.logger.info(f"📋 {screen_name}: REST API 우선 사용")

    async def on_screen_closed(self, screen_name: str):
        """화면이 닫힐 때 WebSocket 구독 정리"""

        self.logger.info(f"📱 화면 닫힘: {screen_name}")

        self.active_screens.discard(screen_name)

        # 화면별 구독 정리
        if screen_name in self.screen_subscriptions:
            subscription = self.screen_subscriptions[screen_name]

            if subscription.priority == SubscriptionPriority.CRITICAL:
                # Critical 구독은 유지
                self.logger.info(f"🔒 {screen_name}: Critical 구독 유지")

            elif subscription.priority == SubscriptionPriority.SHARED:
                # 공유 구독 참조 카운트 감소
                await self._release_shared_subscriptions(screen_name)

            else:  # EXCLUSIVE, TEMPORARY
                # 독점/임시 구독 해제
                await self._cleanup_exclusive_subscription(screen_name)

            del self.screen_subscriptions[screen_name]

    async def on_symbol_changed(
        self,
        screen_name: str,
        old_symbols: List[str],
        new_symbols: List[str],
        data_types: List[WebSocketDataType]
    ):
        """선택된 심볼이 변경될 때 구독 업데이트"""

        self.logger.info(f"🔄 {screen_name}: 심볼 변경 {old_symbols} → {new_symbols}")

        if screen_name not in self.screen_subscriptions:
            return

        subscription = self.screen_subscriptions[screen_name]

        # 기존 구독 해제
        if subscription.priority == SubscriptionPriority.EXCLUSIVE:
            await self._unsubscribe_symbols(screen_name, old_symbols, data_types)

        # 새 구독 시작
        await self._subscribe_symbols(screen_name, new_symbols, data_types)

        # 구독 정보 업데이트
        subscription.symbols = set(new_symbols)
        subscription.last_activity = datetime.now()

    async def get_or_create_shared_subscription(
        self,
        subscription_id: str,
        screen_name: str,
        symbols: List[str],
        data_types: List[WebSocketDataType]
    ) -> bool:
        """공유 구독 획득 또는 생성"""

        if subscription_id not in self.shared_subscriptions:
            # 새로운 공유 구독 생성
            shared_sub = SharedSubscription(
                subscription_id=subscription_id,
                symbols=set(symbols),
                data_types=set(data_types),
                reference_count=0,
                screens=set(),
                created_at=datetime.now()
            )

            # WebSocket 클라이언트 생성 및 구독
            client = UpbitWebSocketQuotationClient()
            await client.connect()

            success = True
            for data_type in data_types:
                if data_type == WebSocketDataType.TICKER:
                    result = await client.subscribe_ticker(symbols)
                elif data_type == WebSocketDataType.ORDERBOOK:
                    result = await client.subscribe_orderbook(symbols)
                elif data_type == WebSocketDataType.TRADE:
                    result = await client.subscribe_trade(symbols)
                else:
                    result = False

                success = success and result

            if success:
                shared_sub.websocket_client = client
                self.shared_subscriptions[subscription_id] = shared_sub
                self.logger.info(f"✅ 공유 구독 생성: {subscription_id}")
            else:
                await client.disconnect()
                self.logger.error(f"❌ 공유 구독 생성 실패: {subscription_id}")
                return False

        # 참조 카운트 증가
        shared_sub = self.shared_subscriptions[subscription_id]
        shared_sub.reference_count += 1
        shared_sub.screens.add(screen_name)

        self.logger.info(f"📈 공유 구독 참조 증가: {subscription_id} ({shared_sub.reference_count})")
        return True

    async def release_shared_subscription(self, subscription_id: str, screen_name: str):
        """공유 구독 해제"""

        if subscription_id not in self.shared_subscriptions:
            return

        shared_sub = self.shared_subscriptions[subscription_id]
        shared_sub.reference_count = max(0, shared_sub.reference_count - 1)
        shared_sub.screens.discard(screen_name)

        self.logger.info(f"📉 공유 구독 참조 감소: {subscription_id} ({shared_sub.reference_count})")

        # 더 이상 사용하지 않으면 구독 해제
        if shared_sub.reference_count <= 0:
            if shared_sub.websocket_client:
                await shared_sub.websocket_client.disconnect()

            del self.shared_subscriptions[subscription_id]
            self.logger.info(f"🗑️ 공유 구독 완전 해제: {subscription_id}")

    def get_resource_usage(self) -> Dict[str, Any]:
        """현재 자원 사용량 조회"""

        return {
            "active_screens": len(self.active_screens),
            "screen_subscriptions": len(self.screen_subscriptions),
            "shared_subscriptions": len(self.shared_subscriptions),
            "critical_subscriptions": len(self.critical_subscriptions),
            "websocket_connections": len(self.websocket_pools),
            "total_symbols": sum(len(sub.symbols) for sub in self.screen_subscriptions.values()),
            "performance_metrics": self.performance_metrics.copy()
        }

    def get_optimization_recommendations(self) -> List[str]:
        """자원 최적화 권장사항"""

        recommendations = []
        usage = self.get_resource_usage()

        if usage["websocket_connections"] > self.max_connections:
            recommendations.append(f"연결 수 과다 ({usage['websocket_connections']}/{self.max_connections}) - 공유 구독 활용 권장")

        if usage["total_symbols"] > 200:
            recommendations.append("구독 심볼 과다 - 필요한 심볼만 구독 권장")

        if len(self.active_screens) == 0 and usage["screen_subscriptions"] > 0:
            recommendations.append("비활성 화면의 구독 감지 - 정리 필요")

        return recommendations

    # Private Methods

    async def _handle_critical_screen(
        self,
        screen_name: str,
        symbols: List[str],
        data_types: List[WebSocketDataType]
    ):
        """Critical 화면 처리 (항상 유지)"""

        subscription = ScreenSubscription(
            screen_name=screen_name,
            screen_type=ScreenType.CRITICAL,
            symbols=set(symbols),
            data_types=set(data_types),
            priority=SubscriptionPriority.CRITICAL,
            created_at=datetime.now(),
            last_activity=datetime.now()
        )

        # Critical 구독은 별도 관리
        self.critical_subscriptions[screen_name] = subscription

        # 전용 WebSocket 연결 생성
        await self._create_exclusive_websocket(screen_name, symbols, data_types)

        self.logger.info(f"🔒 Critical 구독 등록: {screen_name}")

    async def _handle_on_demand_screen(
        self,
        screen_name: str,
        symbols: List[str],
        data_types: List[WebSocketDataType],
        priority: SubscriptionPriority
    ):
        """On-Demand 화면 처리 (화면 열릴 때만)"""

        subscription = ScreenSubscription(
            screen_name=screen_name,
            screen_type=ScreenType.ON_DEMAND,
            symbols=set(symbols),
            data_types=set(data_types),
            priority=priority,
            created_at=datetime.now(),
            last_activity=datetime.now()
        )

        self.screen_subscriptions[screen_name] = subscription

        if priority == SubscriptionPriority.SHARED:
            # 공유 구독 활용
            subscription_id = f"shared_{'-'.join(sorted(symbols))}_{'-'.join(dt.value for dt in data_types)}"
            await self.get_or_create_shared_subscription(subscription_id, screen_name, symbols, data_types)

        else:  # EXCLUSIVE, TEMPORARY
            # 독점 구독 생성
            await self._create_exclusive_websocket(screen_name, symbols, data_types)

        self.logger.info(f"📱 On-Demand 구독 시작: {screen_name} ({priority.value})")

    async def _create_exclusive_websocket(
        self,
        screen_name: str,
        symbols: List[str],
        data_types: List[WebSocketDataType]
    ):
        """독점 WebSocket 연결 생성"""

        client = UpbitWebSocketQuotationClient()
        await client.connect()

        success = True
        for data_type in data_types:
            if data_type == WebSocketDataType.TICKER:
                result = await client.subscribe_ticker(symbols)
            elif data_type == WebSocketDataType.ORDERBOOK:
                result = await client.subscribe_orderbook(symbols)
            elif data_type == WebSocketDataType.TRADE:
                result = await client.subscribe_trade(symbols)
            else:
                result = False

            success = success and result

        if success:
            self.websocket_pools[screen_name] = client
            self.logger.info(f"✅ 독점 WebSocket 생성: {screen_name}")
        else:
            await client.disconnect()
            self.logger.error(f"❌ 독점 WebSocket 생성 실패: {screen_name}")

    async def _cleanup_exclusive_subscription(self, screen_name: str):
        """독점 구독 정리"""

        if screen_name in self.websocket_pools:
            client = self.websocket_pools[screen_name]
            await client.disconnect()
            del self.websocket_pools[screen_name]
            self.logger.info(f"🗑️ 독점 구독 해제: {screen_name}")

    async def _release_shared_subscriptions(self, screen_name: str):
        """화면의 모든 공유 구독 해제"""

        # 해당 화면이 참여한 공유 구독들 찾기
        for subscription_id, shared_sub in list(self.shared_subscriptions.items()):
            if screen_name in shared_sub.screens:
                await self.release_shared_subscription(subscription_id, screen_name)

    async def _subscribe_symbols(
        self,
        screen_name: str,
        symbols: List[str],
        data_types: List[WebSocketDataType]
    ):
        """심볼 구독"""

        if screen_name in self.websocket_pools:
            client = self.websocket_pools[screen_name]

            for data_type in data_types:
                if data_type == WebSocketDataType.TICKER:
                    await client.subscribe_ticker(symbols)
                elif data_type == WebSocketDataType.ORDERBOOK:
                    await client.subscribe_orderbook(symbols)
                elif data_type == WebSocketDataType.TRADE:
                    await client.subscribe_trade(symbols)

    async def _unsubscribe_symbols(
        self,
        screen_name: str,
        symbols: List[str],
        data_types: List[WebSocketDataType]
    ):
        """심볼 구독 해제 (업비트는 개별 해제 불가 - 재연결 방식)"""

        if screen_name in self.websocket_pools:
            self.logger.info(f"🔄 {screen_name}: 구독 변경을 위한 재연결 방식 사용")

            # 기존 연결 종료
            client = self.websocket_pools[screen_name]
            await client.disconnect()

            # 구독 정보에서 해당 심볼 제거
            if screen_name in self.screen_subscriptions:
                subscription = self.screen_subscriptions[screen_name]
                subscription.symbols.difference_update(symbols)

                # 남은 심볼이 있으면 재구독
                if subscription.symbols:
                    await self._create_exclusive_websocket(
                        screen_name,
                        list(subscription.symbols),
                        list(subscription.data_types)
                    )
                else:
                    # 모든 심볼이 제거되면 연결 해제
                    if screen_name in self.websocket_pools:
                        del self.websocket_pools[screen_name]

    async def _optimization_loop(self):
        """자동 최적화 루프"""

        try:
            while True:
                await asyncio.sleep(self.optimization_interval)
                await self._optimize_resources()

        except asyncio.CancelledError:
            self.logger.info("🔄 최적화 루프 중단")

        except Exception as e:
            self.logger.error(f"❌ 최적화 루프 오류: {e}")

    async def _optimize_resources(self):
        """WebSocket 자원 최적화"""

        self.logger.info("🔧 WebSocket 자원 최적화 시작")

        # 1. 유휴 연결 정리
        await self._cleanup_idle_connections()

        # 2. 중복 구독 감지
        await self._detect_duplicate_subscriptions()

        # 3. 성능 메트릭 업데이트
        self._update_performance_metrics()

        self.performance_metrics["last_optimization"] = datetime.now()
        self.logger.info("✅ WebSocket 자원 최적화 완료")

    async def _cleanup_idle_connections(self):
        """유휴 연결 정리"""

        now = datetime.now()
        idle_screens = []

        for screen_name, subscription in self.screen_subscriptions.items():
            idle_time = now - subscription.last_activity

            if (idle_time.total_seconds() > self.idle_threshold and
                subscription.priority != SubscriptionPriority.CRITICAL):
                idle_screens.append(screen_name)

        for screen_name in idle_screens:
            self.logger.info(f"🧹 유휴 연결 정리: {screen_name}")
            await self.on_screen_closed(screen_name)

    async def _detect_duplicate_subscriptions(self):
        """중복 구독 감지 및 권장사항"""

        symbol_groups = {}

        for screen_name, subscription in self.screen_subscriptions.items():
            key = (frozenset(subscription.symbols), frozenset(subscription.data_types))

            if key not in symbol_groups:
                symbol_groups[key] = []
            symbol_groups[key].append(screen_name)

        # 중복 구독 감지
        for (symbols, data_types), screens in symbol_groups.items():
            if len(screens) > 1:
                self.logger.warning(f"⚠️ 중복 구독 감지: {screens} - 공유 구독 권장")

    def _update_performance_metrics(self):
        """성능 메트릭 업데이트"""

        # 연결 수, 구독 수 등 기본 메트릭 업데이트
        usage = self.get_resource_usage()

        self.performance_metrics.update({
            "active_connections": usage["websocket_connections"],
            "total_subscriptions": usage["screen_subscriptions"] + usage["shared_subscriptions"],
            "memory_usage_mb": self._estimate_memory_usage()
        })

    def _estimate_memory_usage(self) -> float:
        """메모리 사용량 추정"""

        # 간단한 추정 (실제로는 더 정교한 계산 필요)
        base_memory = 10.0  # MB
        connection_memory = len(self.websocket_pools) * 2.0  # 연결당 2MB
        subscription_memory = len(self.screen_subscriptions) * 0.1  # 구독당 0.1MB

        return base_memory + connection_memory + subscription_memory

    async def _cleanup_all_subscriptions(self):
        """모든 구독 정리 (종료 시)"""

        # 독점 구독 정리
        for screen_name in list(self.websocket_pools.keys()):
            await self._cleanup_exclusive_subscription(screen_name)

        # 공유 구독 정리
        for subscription_id in list(self.shared_subscriptions.keys()):
            shared_sub = self.shared_subscriptions[subscription_id]
            if shared_sub.websocket_client:
                await shared_sub.websocket_client.disconnect()

        # Critical 구독 정리
        for screen_name in list(self.critical_subscriptions.keys()):
            await self._cleanup_exclusive_subscription(screen_name)

        self.websocket_pools.clear()
        self.shared_subscriptions.clear()
        self.critical_subscriptions.clear()
        self.screen_subscriptions.clear()
