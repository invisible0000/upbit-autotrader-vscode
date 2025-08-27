"""
업비트 WebSocket v5.0 - 구독 관리 시스템

🎯 핵심 기능:
- 스냅샷/리얼타임 티켓 풀 분리
- 스마트 해제 전략
- 자동 재구독 시스템
- 티켓 효율성 최적화
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("SubscriptionManager")


class TicketPool:
    """티켓 풀 관리"""

    def __init__(self, pool_name: str, max_size: int):
        self.pool_name = pool_name
        self.max_size = max_size
        self.active_tickets: Dict[str, Dict[str, Any]] = {}
        self.created_at = datetime.now()

    def acquire_ticket(self, purpose: str = "general") -> Optional[str]:
        """티켓 획득"""
        if len(self.active_tickets) >= self.max_size:
            logger.warning(f"티켓 풀 '{self.pool_name}' 한계 도달 ({self.max_size}개)")
            return None

        ticket_id = f"{self.pool_name}_{uuid.uuid4().hex[:8]}"
        self.active_tickets[ticket_id] = {
            "purpose": purpose,
            "created_at": datetime.now(),
            "subscriptions": []
        }

        logger.debug(f"티켓 획득: {ticket_id} (목적: {purpose})")
        return ticket_id

    def release_ticket(self, ticket_id: str) -> bool:
        """티켓 해제"""
        if ticket_id in self.active_tickets:
            del self.active_tickets[ticket_id]
            logger.debug(f"티켓 해제: {ticket_id}")
            return True
        return False

    def get_available_count(self) -> int:
        """사용 가능한 티켓 수"""
        return self.max_size - len(self.active_tickets)

    def get_stats(self) -> Dict[str, Any]:
        """티켓 풀 통계"""
        return {
            "pool_name": self.pool_name,
            "max_size": self.max_size,
            "active_count": len(self.active_tickets),
            "available_count": self.get_available_count(),
            "active_tickets": list(self.active_tickets.keys())
        }


class UnsubscribeStrategy:
    """구독 해제 전략"""

    # 마켓별 해제 전용 심볼
    UNSUBSCRIBE_SYMBOLS = {
        "KRW": "BTC-USDT",
        "BTC": "ETH-USDT",
        "USDT": "BTC-KRW",
        "ETH": "BTC-USDT"
    }

    @classmethod
    def get_unsubscribe_symbol(cls, current_symbols: List[str]) -> str:
        """현재 구독 마켓에 맞는 해제 전용 심볼 반환"""
        if not current_symbols:
            return "BTC-USDT"  # 기본값

        # 가장 많이 사용된 마켓 타입 감지
        market_counts = {}
        for symbol in current_symbols:
            if "-" in symbol:
                market = symbol.split("-")[0]
                market_counts[market] = market_counts.get(market, 0) + 1

        if market_counts:
            primary_market = max(market_counts, key=market_counts.get)
            return cls.UNSUBSCRIBE_SYMBOLS.get(primary_market, "BTC-USDT")

        return "BTC-USDT"

    @classmethod
    def create_soft_unsubscribe_request(cls, ticket_id: str, current_symbols: List[str]) -> SubscriptionRequest:
        """소프트 해제용 스냅샷 요청 생성"""
        unsubscribe_symbol = cls.get_unsubscribe_symbol(current_symbols)

        return SubscriptionRequest(
            ticket=ticket_id,
            data_type=DataType.TICKER,
            symbols=[unsubscribe_symbol],
            is_only_snapshot=True
        )


class SubscriptionManager:
    """업비트 WebSocket 구독 관리자"""

    def __init__(self):
        self.logger = create_component_logger("SubscriptionManager")

        # 티켓 풀 분리
        self.snapshot_pool = TicketPool("snapshot", max_size=1)
        self.realtime_pool = TicketPool("realtime", max_size=2)

        # 구독 상태 추적
        self.subscription_registry: Dict[str, Dict[str, Any]] = {}

        # 재구독용 백업
        self.backup_subscriptions: List[SubscriptionRequest] = []

        self.logger.info("✅ 구독 관리자 초기화 완료")

    async def request_snapshot(self, data_type: DataType, symbols: List[str], **options) -> Optional[str]:
        """일회성 스냅샷 요청"""
        ticket_id = self.snapshot_pool.acquire_ticket("snapshot")
        if not ticket_id:
            self.logger.error("스냅샷 티켓 풀 포화")
            return None

        subscription = SubscriptionRequest(
            ticket=ticket_id,
            data_type=data_type,
            symbols=symbols,
            is_only_snapshot=True,
            options=options
        )

        # 레지스트리에 등록 (임시)
        self.subscription_registry[ticket_id] = {
            "mode": "snapshot",
            "data_type": data_type.value,
            "symbols": symbols,
            "created_at": datetime.now(),
            "status": "active",
            "subscription": subscription
        }

        self.logger.info(f"스냅샷 요청: {data_type.value} - {symbols}")
        return ticket_id

    async def subscribe_realtime(self, data_type: DataType, symbols: List[str], **options) -> Optional[str]:
        """지속적 리얼타임 구독"""
        ticket_id = self.realtime_pool.acquire_ticket("realtime")
        if not ticket_id:
            self.logger.error("리얼타임 티켓 풀 포화")
            return None

        subscription = SubscriptionRequest(
            ticket=ticket_id,
            data_type=data_type,
            symbols=symbols,
            is_only_snapshot=False,
            options=options
        )

        # 레지스트리에 등록
        self.subscription_registry[ticket_id] = {
            "mode": "realtime",
            "data_type": data_type.value,
            "symbols": symbols,
            "created_at": datetime.now(),
            "status": "active",
            "last_message": None,
            "subscription": subscription
        }

        # 재구독용 백업
        self.backup_subscriptions.append(subscription)

        self.logger.info(f"리얼타임 구독: {data_type.value} - {symbols}")
        return ticket_id

    async def soft_unsubscribe(self, subscription_id: str) -> bool:
        """소프트 해제 (스냅샷으로 교체)"""
        if subscription_id not in self.subscription_registry:
            return False

        subscription_info = self.subscription_registry[subscription_id]
        current_symbols = subscription_info["symbols"]

        # 소프트 해제 요청 생성
        unsubscribe_request = UnsubscribeStrategy.create_soft_unsubscribe_request(
            subscription_id, current_symbols
        )

        # 상태 업데이트
        subscription_info["status"] = "unsubscribing"
        subscription_info["unsubscribe_request"] = unsubscribe_request

        self.logger.info(f"소프트 해제 시작: {subscription_id}")
        return True

    async def hard_unsubscribe(self, subscription_id: str) -> bool:
        """하드 해제 (완전 제거)"""
        if subscription_id not in self.subscription_registry:
            return False

        subscription_info = self.subscription_registry[subscription_id]
        mode = subscription_info["mode"]

        # 티켓 해제
        if mode == "snapshot":
            self.snapshot_pool.release_ticket(subscription_id)
        elif mode == "realtime":
            self.realtime_pool.release_ticket(subscription_id)

        # 레지스트리에서 제거
        del self.subscription_registry[subscription_id]

        # 백업에서도 제거
        self.backup_subscriptions = [
            sub for sub in self.backup_subscriptions
            if sub.ticket != subscription_id
        ]

        self.logger.info(f"하드 해제 완료: {subscription_id}")
        return True

    async def cleanup_inactive(self) -> int:
        """비활성 구독 정리"""
        cleaned_count = 0
        inactive_keys = []

        for ticket_id, info in self.subscription_registry.items():
            if info["mode"] == "snapshot":
                # 스냅샷은 10분 후 자동 정리
                age = (datetime.now() - info["created_at"]).total_seconds()
                if age > 600:  # 10분
                    inactive_keys.append(ticket_id)

        for ticket_id in inactive_keys:
            await self.hard_unsubscribe(ticket_id)
            cleaned_count += 1

        if cleaned_count > 0:
            self.logger.info(f"비활성 구독 {cleaned_count}개 정리 완료")

        return cleaned_count

    def get_resubscribe_requests(self) -> List[SubscriptionRequest]:
        """재구독용 요청 목록 반환"""
        return self.backup_subscriptions.copy()

    def get_subscription_stats(self) -> Dict[str, Any]:
        """구독 통계"""
        snapshot_count = sum(1 for info in self.subscription_registry.values()
                           if info["mode"] == "snapshot")
        realtime_count = sum(1 for info in self.subscription_registry.values()
                           if info["mode"] == "realtime")

        return {
            "total_subscriptions": len(self.subscription_registry),
            "snapshot_subscriptions": snapshot_count,
            "realtime_subscriptions": realtime_count,
            "snapshot_pool": self.snapshot_pool.get_stats(),
            "realtime_pool": self.realtime_pool.get_stats(),
            "backup_count": len(self.backup_subscriptions)
        }

    def validate_subscription(self, data_type: DataType, symbols: List[str]) -> bool:
        """중복 구독 방지 검증"""
        for info in self.subscription_registry.values():
            if (info["data_type"] == data_type.value and
                set(info["symbols"]) == set(symbols)):
                self.logger.warning(f"중복 구독 감지: {data_type.value} - {symbols}")
                return False
        return True

    def detect_conflicts(self) -> List[str]:
        """구독 충돌 감지"""
        conflicts = []

        # 동일 심볼의 스냅샷/리얼타임 동시 구독 감지
        snapshot_symbols = set()
        realtime_symbols = set()

        for info in self.subscription_registry.values():
            symbols = set(info["symbols"])
            if info["mode"] == "snapshot":
                snapshot_symbols.update(symbols)
            elif info["mode"] == "realtime":
                realtime_symbols.update(symbols)

        conflict_symbols = snapshot_symbols & realtime_symbols
        if conflict_symbols:
            conflicts.append(f"스냅샷/리얼타임 충돌: {conflict_symbols}")

        return conflicts
