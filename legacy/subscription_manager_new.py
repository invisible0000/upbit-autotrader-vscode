"""
업비트 WebSocket v5.0 - 새로운 구독 관리 시스템

🎯 설계 원칙:
1. 스냅샷 = 1회용 티켓, 매번 새로 생성
2. 리얼타임 = 재사용 가능한 티켓
3. 콜백 = 구독 ID별 독립 관리
4. 단순성 = 책임 분리와 명확한 인터페이스

🔧 핵심 개념:
- Ticket: 업비트 WebSocket의 물리적 연결 단위
- Subscription: 논리적 데이터 요청 단위 (사용자 관점)
- Callback: 구독별 데이터 처리 함수
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import uuid
import json
import asyncio

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .config import load_config

logger = create_component_logger("SubscriptionManager")


# =====================================================================
# 1. 티켓 관리 시스템 (물리적 WebSocket 연결 단위)
# =====================================================================

class TicketManager:
    """업비트 WebSocket 티켓 관리 - 물리적 연결 단위"""

    def __init__(self, max_tickets: int = 3):
        self.max_tickets = max_tickets
        self.active_tickets: Dict[str, Dict[str, Any]] = {}
        self.next_ticket_number = 1

    def create_ticket(self, purpose: str = "general") -> Optional[str]:
        """새로운 티켓 생성"""
        if len(self.active_tickets) >= self.max_tickets:
            logger.warning(f"티켓 한계 도달: {len(self.active_tickets)}/{self.max_tickets}")
            return None

        ticket_id = f"ticket_{self.next_ticket_number:03d}_{uuid.uuid4().hex[:6]}"
        self.next_ticket_number += 1

        self.active_tickets[ticket_id] = {
            "purpose": purpose,
            "created_at": datetime.now(),
            "subscription_count": 0,
            "is_realtime": purpose == "realtime"
        }

        logger.debug(f"티켓 생성: {ticket_id} (목적: {purpose})")
        return ticket_id

    def release_ticket(self, ticket_id: str) -> bool:
        """티켓 해제"""
        if ticket_id in self.active_tickets:
            del self.active_tickets[ticket_id]
            logger.debug(f"티켓 해제: {ticket_id}")
            return True
        return False

    def get_reusable_ticket(self, data_type: str) -> Optional[str]:
        """리얼타임용 재사용 가능한 티켓 찾기"""
        for ticket_id, info in self.active_tickets.items():
            if info["is_realtime"] and info["subscription_count"] < 5:  # 티켓당 최대 5개 구독
                return ticket_id
        return None

    def increment_subscription_count(self, ticket_id: str) -> None:
        """구독 카운트 증가"""
        if ticket_id in self.active_tickets:
            self.active_tickets[ticket_id]["subscription_count"] += 1

    def decrement_subscription_count(self, ticket_id: str) -> None:
        """구독 카운트 감소"""
        if ticket_id in self.active_tickets:
            self.active_tickets[ticket_id]["subscription_count"] -= 1
            if self.active_tickets[ticket_id]["subscription_count"] <= 0:
                self.release_ticket(ticket_id)

    def get_stats(self) -> Dict[str, Any]:
        """티켓 통계"""
        return {
            "total_tickets": len(self.active_tickets),
            "max_tickets": self.max_tickets,
            "utilization": len(self.active_tickets) / self.max_tickets * 100,
            "tickets": {tid: info["subscription_count"] for tid, info in self.active_tickets.items()}
        }


# =====================================================================
# 2. 구독 관리 시스템 (논리적 요청 단위)
# =====================================================================

class SubscriptionRegistry:
    """구독 등록 및 관리 - 논리적 요청 단위"""

    def __init__(self):
        self.subscriptions: Dict[str, Dict[str, Any]] = {}

    def register_subscription(self, data_type: str, symbols: List[str],
                            ticket_id: str, mode: str) -> str:
        """구독 등록"""
        subscription_id = f"{mode}_{uuid.uuid4().hex[:8]}"

        self.subscriptions[subscription_id] = {
            "data_type": data_type,
            "symbols": symbols,
            "ticket_id": ticket_id,
            "mode": mode,  # "snapshot" or "realtime"
            "created_at": datetime.now(),
            "message_count": 0,
            "status": "active"
        }

        logger.debug(f"구독 등록: {subscription_id} ({mode}) - {data_type}:{symbols}")
        return subscription_id

    def unregister_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """구독 해제"""
        if subscription_id in self.subscriptions:
            subscription = self.subscriptions.pop(subscription_id)
            logger.debug(f"구독 해제: {subscription_id}")
            return subscription
        return None

    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """구독 정보 조회"""
        return self.subscriptions.get(subscription_id)

    def get_subscriptions_by_ticket(self, ticket_id: str) -> List[str]:
        """티켓별 구독 목록"""
        return [sid for sid, info in self.subscriptions.items()
                if info["ticket_id"] == ticket_id]

    def increment_message_count(self, subscription_id: str) -> None:
        """메시지 카운트 증가"""
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id]["message_count"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """구독 통계"""
        snapshot_count = sum(1 for sub in self.subscriptions.values() if sub["mode"] == "snapshot")
        realtime_count = sum(1 for sub in self.subscriptions.values() if sub["mode"] == "realtime")

        return {
            "total_subscriptions": len(self.subscriptions),
            "snapshot_subscriptions": snapshot_count,
            "realtime_subscriptions": realtime_count,
            "active_subscriptions": len([s for s in self.subscriptions.values() if s["status"] == "active"])
        }


# =====================================================================
# 3. 콜백 관리 시스템 (구독별 데이터 처리)
# =====================================================================

class CallbackManager:
    """콜백 관리 - 구독별 독립적 처리"""

    def __init__(self):
        self.callbacks: Dict[str, Callable] = {}

    def register_callback(self, subscription_id: str, callback: Optional[Callable]) -> None:
        """콜백 등록"""
        if callback:
            self.callbacks[subscription_id] = callback
            logger.debug(f"콜백 등록: {subscription_id}")

    def unregister_callback(self, subscription_id: str) -> None:
        """콜백 해제"""
        if subscription_id in self.callbacks:
            del self.callbacks[subscription_id]
            logger.debug(f"콜백 해제: {subscription_id}")

    async def execute_callback(self, subscription_id: str, data: Any) -> bool:
        """콜백 실행"""
        if subscription_id not in self.callbacks:
            return False

        callback = self.callbacks[subscription_id]
        try:
            if hasattr(callback, '__call__'):
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            return True
        except Exception as e:
            logger.error(f"콜백 실행 오류 [{subscription_id}]: {e}")
            return False

    def get_registered_subscriptions(self) -> List[str]:
        """등록된 콜백이 있는 구독 목록"""
        return list(self.callbacks.keys())


# =====================================================================
# 4. 메시지 생성 시스템 (업비트 WebSocket 프로토콜)
# =====================================================================

class MessageBuilder:
    """업비트 WebSocket 메시지 생성"""

    @staticmethod
    def create_snapshot_message(ticket_id: str, data_type: str, symbols: List[str]) -> List[Dict[str, Any]]:
        """스냅샷 메시지 생성"""
        return [
            {"ticket": ticket_id},
            {
                "type": data_type,
                "codes": symbols,
                "is_only_snapshot": True
            },
            {"format": "DEFAULT"}
        ]

    @staticmethod
    def create_realtime_message(ticket_id: str, data_type: str, symbols: List[str]) -> List[Dict[str, Any]]:
        """리얼타임 메시지 생성"""
        return [
            {"ticket": ticket_id},
            {
                "type": data_type,
                "codes": symbols
            },
            {"format": "DEFAULT"}
        ]

    @staticmethod
    def create_unsubscribe_message(ticket_id: str) -> List[Dict[str, Any]]:
        """구독 해제 메시지 생성 (스냅샷으로 교체)"""
        return [
            {"ticket": ticket_id},
            {
                "type": "ticker",
                "codes": ["KRW-BTC"],
                "is_only_snapshot": True
            },
            {"format": "DEFAULT"}
        ]


# =====================================================================
# 5. 통합 구독 매니저 (메인 인터페이스)
# =====================================================================

class SubscriptionManager:
    """통합 구독 관리자 - 새로운 설계"""

    def __init__(self, max_tickets: int = 3, config_path: Optional[str] = None):
        # 설정 로드
        self.config = load_config(config_path)

        # 핵심 컴포넌트들
        self.ticket_manager = TicketManager(max_tickets)
        self.subscription_registry = SubscriptionRegistry()
        self.callback_manager = CallbackManager()
        self.message_builder = MessageBuilder()

        # WebSocket 연결 참조
        self.websocket_connection: Optional[Any] = None

        logger.info(f"새로운 구독 매니저 초기화 - 최대 티켓: {max_tickets}")

    def set_websocket_connection(self, websocket) -> None:
        """WebSocket 연결 설정"""
        self.websocket_connection = websocket
        logger.debug("WebSocket 연결 설정 완료")

    # =================================================================
    # 스냅샷 구독 (1회용, 매번 새로운 티켓)
    # =================================================================

    async def request_snapshot(self, data_type: str, symbols: List[str],
                             callback: Optional[Callable] = None) -> Optional[str]:
        """스냅샷 요청 - 매번 새로운 티켓 생성"""
        if not self.websocket_connection:
            logger.error("WebSocket 연결이 설정되지 않았습니다")
            return None

        # 1. 새로운 스냅샷 전용 티켓 생성
        ticket_id = self.ticket_manager.create_ticket("snapshot")
        if not ticket_id:
            logger.error("스냅샷 티켓 생성 실패")
            return None

        try:
            # 2. 구독 등록
            subscription_id = self.subscription_registry.register_subscription(
                data_type, symbols, ticket_id, "snapshot"
            )

            # 3. 콜백 등록
            self.callback_manager.register_callback(subscription_id, callback)

            # 4. 메시지 생성 및 전송
            message = self.message_builder.create_snapshot_message(ticket_id, data_type, symbols)
            await self.websocket_connection.send(json.dumps(message))

            logger.info(f"스냅샷 요청 완료: {subscription_id} - {data_type}:{symbols}")
            logger.debug(f"전송 메시지: {message}")

            return subscription_id

        except Exception as e:
            logger.error(f"스냅샷 요청 실패: {e}")
            # 실패시 정리
            self.ticket_manager.release_ticket(ticket_id)
            if 'subscription_id' in locals():
                self.subscription_registry.unregister_subscription(subscription_id)
                self.callback_manager.unregister_callback(subscription_id)
            return None

    # =================================================================
    # 리얼타임 구독 (지속적, 티켓 재사용 가능)
    # =================================================================

    async def subscribe_realtime(self, data_type: str, symbols: List[str],
                               callback: Optional[Callable] = None) -> Optional[str]:
        """리얼타임 구독 - 티켓 재사용 가능"""
        if not self.websocket_connection:
            logger.error("WebSocket 연결이 설정되지 않았습니다")
            return None

        # 1. 재사용 가능한 티켓 찾기 또는 새로 생성
        ticket_id = self.ticket_manager.get_reusable_ticket(data_type)
        if not ticket_id:
            ticket_id = self.ticket_manager.create_ticket("realtime")
            if not ticket_id:
                logger.error("리얼타임 티켓 생성 실패")
                return None

        try:
            # 2. 구독 등록
            subscription_id = self.subscription_registry.register_subscription(
                data_type, symbols, ticket_id, "realtime"
            )

            # 3. 콜백 등록
            self.callback_manager.register_callback(subscription_id, callback)

            # 4. 티켓 구독 카운트 증가
            self.ticket_manager.increment_subscription_count(ticket_id)

            # 5. 메시지 생성 및 전송
            message = self.message_builder.create_realtime_message(ticket_id, data_type, symbols)
            await self.websocket_connection.send(json.dumps(message))

            logger.info(f"리얼타임 구독 완료: {subscription_id} - {data_type}:{symbols}")
            logger.debug(f"전송 메시지: {message}")

            return subscription_id

        except Exception as e:
            logger.error(f"리얼타임 구독 실패: {e}")
            # 실패시 정리
            if 'subscription_id' in locals():
                self.subscription_registry.unregister_subscription(subscription_id)
                self.callback_manager.unregister_callback(subscription_id)
                self.ticket_manager.decrement_subscription_count(ticket_id)
            return None

    # =================================================================
    # 구독 해제
    # =================================================================

    async def unsubscribe(self, subscription_id: str) -> bool:
        """구독 해제"""
        subscription = self.subscription_registry.get_subscription(subscription_id)
        if not subscription:
            logger.warning(f"구독을 찾을 수 없음: {subscription_id}")
            return False

        try:
            ticket_id = subscription["ticket_id"]
            mode = subscription["mode"]

            # 1. 콜백 해제
            self.callback_manager.unregister_callback(subscription_id)

            # 2. 구독 해제
            self.subscription_registry.unregister_subscription(subscription_id)

            # 3. 모드별 정리
            if mode == "snapshot":
                # 스냅샷: 티켓 즉시 해제 (1회용이므로)
                self.ticket_manager.release_ticket(ticket_id)
                logger.info(f"스냅샷 구독 해제 완료: {subscription_id}")

            elif mode == "realtime":
                # 리얼타임: 구독 카운트 감소, 필요시 해제 메시지 전송
                self.ticket_manager.decrement_subscription_count(ticket_id)

                # 해당 티켓의 다른 구독이 없으면 해제 메시지 전송
                remaining_subscriptions = self.subscription_registry.get_subscriptions_by_ticket(ticket_id)
                if not remaining_subscriptions and self.websocket_connection:
                    try:
                        unsubscribe_message = self.message_builder.create_unsubscribe_message(ticket_id)
                        await self.websocket_connection.send(json.dumps(unsubscribe_message))
                        logger.debug(f"해제 메시지 전송: {unsubscribe_message}")
                    except Exception as e:
                        logger.error(f"해제 메시지 전송 실패: {e}")

                logger.info(f"리얼타임 구독 해제 완료: {subscription_id}")

            return True

        except Exception as e:
            logger.error(f"구독 해제 실패: {e}")
            return False

    # =================================================================
    # 메시지 처리 (WebSocket 클라이언트에서 호출)
    # =================================================================

    async def process_message(self, raw_message: str) -> None:
        """수신된 메시지 처리"""
        try:
            data = json.loads(raw_message)
            if not isinstance(data, dict):
                return

            # 메시지에서 티켓 ID 추출 (업비트는 메시지에 티켓 정보 없으므로 다른 방법 필요)
            # 현재는 모든 구독에 대해 콜백 실행 (개선 필요)
            message_type = data.get('type', '')

            # 해당 타입의 구독들에 대해 콜백 실행
            for subscription_id, subscription in self.subscription_registry.subscriptions.items():
                if subscription['data_type'] == message_type and subscription['status'] == 'active':
                    # 메시지 카운트 증가
                    self.subscription_registry.increment_message_count(subscription_id)

                    # 콜백 실행
                    await self.callback_manager.execute_callback(subscription_id, data)

                    # 스냅샷의 경우 1회 처리 후 자동 해제
                    if subscription['mode'] == 'snapshot':
                        await self.unsubscribe(subscription_id)
                        logger.debug(f"스냅샷 자동 해제: {subscription_id}")

        except Exception as e:
            logger.error(f"메시지 처리 오류: {e}")

    # =================================================================
    # 통계 및 상태 조회
    # =================================================================

    def get_stats(self) -> Dict[str, Any]:
        """전체 통계"""
        return {
            "ticket_stats": self.ticket_manager.get_stats(),
            "subscription_stats": self.subscription_registry.get_stats(),
            "callback_stats": {
                "registered_callbacks": len(self.callback_manager.get_registered_subscriptions())
            }
        }

    def get_active_subscriptions(self) -> Dict[str, Dict[str, Any]]:
        """활성 구독 목록"""
        return self.subscription_registry.subscriptions.copy()

    # =================================================================
    # 편의 메서드들
    # =================================================================

    async def quick_price_check(self, symbol: str, callback: Optional[Callable] = None) -> Optional[str]:
        """빠른 가격 조회 (스냅샷)"""
        return await self.request_snapshot("ticker", [symbol], callback)

    async def start_price_monitoring(self, symbol: str, callback: Optional[Callable] = None) -> Optional[str]:
        """가격 모니터링 시작 (리얼타임)"""
        return await self.subscribe_realtime("ticker", [symbol], callback)

    async def unsubscribe_all(self) -> int:
        """모든 구독 해제"""
        subscription_ids = list(self.subscription_registry.subscriptions.keys())
        unsubscribed_count = 0

        for subscription_id in subscription_ids:
            if await self.unsubscribe(subscription_id):
                unsubscribed_count += 1

        logger.info(f"전체 구독 해제 완료: {unsubscribed_count}개")
        return unsubscribed_count


# =====================================================================
# 6. 편의 함수들
# =====================================================================

def create_subscription_manager(max_tickets: int = 3, config_path: Optional[str] = None) -> SubscriptionManager:
    """구독 매니저 생성"""
    return SubscriptionManager(max_tickets, config_path)


async def quick_snapshot(manager: SubscriptionManager, symbol: str) -> Optional[str]:
    """단일 심볼 스냅샷 조회"""
    return await manager.request_snapshot("ticker", [symbol])


async def batch_snapshots(manager: SubscriptionManager, symbols: List[str]) -> List[Optional[str]]:
    """여러 심볼 스냅샷 일괄 조회"""
    results = []
    for symbol in symbols:
        result = await manager.request_snapshot("ticker", [symbol])
        results.append(result)
        # API 제한을 위한 짧은 대기
        await asyncio.sleep(0.05)
    return results
