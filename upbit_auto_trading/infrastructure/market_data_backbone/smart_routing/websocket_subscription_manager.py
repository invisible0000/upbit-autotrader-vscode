"""
WebSocket 구독 매니저 v5.0 - 간소화된 구독 관리

🎯 핵심 개념:
- 티켓 관리는 기본 WebSocket 클라이언트가 담당 (중앙집중식)
- 상위 매니저는 단순한 구독 상태 추적만 담당
- 타입별 구독으로 모든 심볼 처리
- 복잡한 티켓 로직 제거로 성능 및 안정성 향상
"""

from datetime import datetime
from typing import Dict, List, Any, Set, Optional
from dataclasses import dataclass
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger


class SubscriptionType(Enum):
    """구독 타입 - 업비트 WebSocket 지원 타입"""
    TICKER = "ticker"      # 현재가
    TRADE = "trade"        # 체결
    ORDERBOOK = "orderbook"  # 호가
    CANDLE = "candle"      # 캔들


@dataclass
class SimpleSubscription:
    """간소화된 구독 정보"""
    subscription_type: SubscriptionType
    symbols: Set[str]
    created_at: datetime
    last_updated: datetime
    message_count: int = 0

    def add_symbols(self, new_symbols: List[str]) -> List[str]:
        """새 심볼 추가 - 실제 추가된 심볼만 반환"""
        before_count = len(self.symbols)
        self.symbols.update(new_symbols)
        self.last_updated = datetime.now()

        # 실제 추가된 심볼 반환
        if len(self.symbols) > before_count:
            return [s for s in new_symbols if s in self.symbols]
        return []

    def remove_symbols(self, remove_symbols: List[str]) -> List[str]:
        """심볼 제거 - 실제 제거된 심볼만 반환"""
        removed = []
        for symbol in remove_symbols:
            if symbol in self.symbols:
                self.symbols.remove(symbol)
                removed.append(symbol)

        if removed:
            self.last_updated = datetime.now()
        return removed

    def has_symbol(self, symbol: str) -> bool:
        """심볼 구독 여부 확인"""
        return symbol in self.symbols

    def is_empty(self) -> bool:
        """빈 구독인지 확인"""
        return len(self.symbols) == 0


class WebSocketSubscriptionManager:
    """
    WebSocket 구독 매니저 v5.0 - 간소화된 구독 관리

    핵심 원칙:
    - 티켓 관리는 기본 WebSocket 클라이언트에 완전 위임
    - 상위 매니저는 구독 상태 추적만 담당
    - 복잡한 로직 제거로 안정성 및 성능 향상
    """

    def __init__(self, websocket_client, max_subscription_types: int = 4):
        """
        Args:
            websocket_client: 티켓 관리 기능이 있는 WebSocket 클라이언트
            max_subscription_types: 최대 구독 타입 수 (업비트: 4개)
        """
        self.websocket_client = websocket_client
        self.logger = create_component_logger("WebSocketSubscriptionManager")
        self.max_subscription_types = max_subscription_types

        # 간소화된 구독 상태 추적 (타입별)
        self.type_subscriptions: Dict[SubscriptionType, SimpleSubscription] = {}

        # 성능 모니터링 (간소화)
        self.total_messages_received = 0

        self.logger.info("✅ WebSocket 구독 매니저 v5.0 초기화 (간소화된 관리, 티켓은 기본 API 담당)")

    async def subscribe_symbols(
        self,
        symbols: List[str],
        subscription_type: SubscriptionType,
        priority: int = 5
    ) -> bool:
        """
        심볼 구독 - 간소화된 버전

        티켓 관리는 기본 WebSocket 클라이언트가 자동 처리
        상위 매니저는 단순히 구독 요청만 전달

        Args:
            symbols: 구독할 심볼 리스트
            subscription_type: 구독 타입
            priority: 우선순위 (무시됨 - 기본 API가 관리)

        Returns:
            구독 성공 여부
        """
        if not symbols:
            return True

        try:
            # 기존 구독이 있으면 심볼 추가
            if subscription_type in self.type_subscriptions:
                existing_sub = self.type_subscriptions[subscription_type]
                new_symbols = [s for s in symbols if not existing_sub.has_symbol(s)]

                if not new_symbols:
                    self.logger.debug(f"모든 심볼이 이미 구독됨: {subscription_type.value}")
                    return True

                # 🎯 간소화: 기본 WebSocket 클라이언트에 단순 위임
                success = await self._call_websocket_subscribe(subscription_type, list(existing_sub.symbols) + new_symbols)

                if success:
                    existing_sub.add_symbols(new_symbols)
                    self.logger.info(f"✅ 심볼 추가: {subscription_type.value} (+{len(new_symbols)}개)")
                    return True
                else:
                    return False

            else:
                # 새 타입 구독 생성
                if len(self.type_subscriptions) >= self.max_subscription_types:
                    self.logger.warning(f"⚠️ 구독 타입 한계 초과: {len(self.type_subscriptions)}/{self.max_subscription_types}")
                    return False

                # 🎯 간소화: 기본 WebSocket 클라이언트에 단순 위임
                success = await self._call_websocket_subscribe(subscription_type, symbols)

                if success:
                    # 새 구독 생성
                    new_subscription = SimpleSubscription(
                        subscription_type=subscription_type,
                        symbols=set(symbols),
                        created_at=datetime.now(),
                        last_updated=datetime.now()
                    )
                    self.type_subscriptions[subscription_type] = new_subscription

                    self.logger.info(f"✅ 새 타입 구독: {subscription_type.value} ({len(symbols)}개 심볼)")
                    return True
                else:
                    return False

        except Exception as e:
            self.logger.error(f"❌ 구독 예외: {e}")
            return False

    async def unsubscribe_symbols(
        self,
        symbols: List[str],
        subscription_type: SubscriptionType
    ) -> bool:
        """
        심볼 구독 해제 - 간소화된 버전

        Args:
            symbols: 해제할 심볼 리스트
            subscription_type: 구독 타입

        Returns:
            해제 성공 여부
        """
        if subscription_type not in self.type_subscriptions:
            return True

        subscription = self.type_subscriptions[subscription_type]
        removed_symbols = subscription.remove_symbols(symbols)

        if not removed_symbols:
            return True

        try:
            if subscription.is_empty():
                # 타입 전체 구독 해제 - 빈 리스트로 구독
                success = await self._call_websocket_subscribe(subscription_type, [])
                if success:
                    del self.type_subscriptions[subscription_type]
                    self.logger.info(f"✅ 타입 구독 해제: {subscription_type.value}")
                    return True
                else:
                    # 실패시 롤백
                    subscription.add_symbols(removed_symbols)
                    return False
            else:
                # 부분 구독 해제 - 남은 심볼만 구독
                success = await self._call_websocket_subscribe(subscription_type, list(subscription.symbols))
                if success:
                    self.logger.info(f"✅ 심볼 제거: {subscription_type.value} (-{len(removed_symbols)}개)")
                    return True
                else:
                    # 실패시 롤백
                    subscription.add_symbols(removed_symbols)
                    return False

        except Exception as e:
            self.logger.error(f"❌ 구독 해제 예외: {e}")
            # 예외 시 롤백
            subscription.add_symbols(removed_symbols)
            return False

    async def _call_websocket_subscribe(self, subscription_type: SubscriptionType, symbols: List[str]) -> bool:
        """
        WebSocket 구독 호출 - 간소화된 버전

        티켓 관리는 기본 WebSocket 클라이언트가 완전 담당
        """
        try:
            if subscription_type == SubscriptionType.TICKER:
                return await self.websocket_client.subscribe_ticker(symbols)
            elif subscription_type == SubscriptionType.TRADE:
                return await self.websocket_client.subscribe_trade(symbols)
            elif subscription_type == SubscriptionType.ORDERBOOK:
                return await self.websocket_client.subscribe_orderbook(symbols)
            elif subscription_type == SubscriptionType.CANDLE:
                return await self.websocket_client.subscribe_candle(symbols)
            else:
                self.logger.error(f"❌ 지원하지 않는 구독 타입: {subscription_type}")
                return False

        except Exception as e:
            self.logger.error(f"❌ WebSocket 구독 호출 실패: {e}")
            return False

    # ===== 호환성 메서드들 (기존 SmartRouter와의 호환성 보장) =====

    async def request_batch_subscription(
        self,
        symbols: List[str],
        subscription_type: SubscriptionType,
        priority: int = 5
    ) -> bool:
        """기존 SmartRouter 호환성을 위한 배치 구독 메서드"""
        return await self.subscribe_symbols(symbols, subscription_type, priority)

    def can_handle_subscription(
        self,
        symbols: List[str],
        subscription_type: SubscriptionType
    ) -> bool:
        """구독 처리 가능 여부 확인"""
        # 기존 타입이면 항상 처리 가능
        if subscription_type in self.type_subscriptions:
            return True

        # 새 타입이고 여유 공간이 있으면 처리 가능
        return len(self.type_subscriptions) < self.max_subscription_types

    def get_current_subscription_count(self) -> int:
        """현재 구독 타입 수 반환"""
        return len(self.type_subscriptions)

    def get_max_subscription_count(self) -> int:
        """최대 구독 타입 수 반환"""
        return self.max_subscription_types

    def is_symbol_subscribed(self, symbol: str, subscription_type: SubscriptionType) -> bool:
        """심볼이 구독 중인지 확인"""
        if subscription_type not in self.type_subscriptions:
            return False
        return self.type_subscriptions[subscription_type].has_symbol(symbol)

    def get_symbols_by_type(self, subscription_type: SubscriptionType) -> List[str]:
        """특정 타입의 구독 심볼 목록"""
        if subscription_type not in self.type_subscriptions:
            return []
        return list(self.type_subscriptions[subscription_type].symbols)

    def increment_message_count(self, subscription_type: SubscriptionType) -> None:
        """메시지 수신 카운트 증가"""
        if subscription_type in self.type_subscriptions:
            self.type_subscriptions[subscription_type].message_count += 1
        self.total_messages_received += 1

    def get_subscription_status(self) -> Dict[str, Any]:
        """구독 상태 조회 - 간소화된 버전"""
        total_symbols = sum(len(sub.symbols) for sub in self.type_subscriptions.values())

        status = {
            "total_subscription_types": len(self.type_subscriptions),
            "max_subscription_types": self.max_subscription_types,
            "total_symbols": total_symbols,
            "total_messages_received": self.total_messages_received,
            "subscriptions": {}
        }

        for sub_type, subscription in self.type_subscriptions.items():
            status["subscriptions"][sub_type.value] = {
                "symbol_count": len(subscription.symbols),
                "symbols": list(subscription.symbols),
                "message_count": subscription.message_count,
                "created_at": subscription.created_at.isoformat(),
                "last_updated": subscription.last_updated.isoformat()
            }

        return status

    async def cleanup(self) -> None:
        """정리 작업 - 간소화된 버전"""
        try:
            # 모든 구독 해제 (빈 리스트로 구독)
            for subscription_type in list(self.type_subscriptions.keys()):
                await self._call_websocket_subscribe(subscription_type, [])

            self.type_subscriptions.clear()
            self.logger.info("🧹 WebSocket 구독 매니저 v5.0 정리 완료")

        except Exception as e:
            self.logger.error(f"❌ 정리 작업 실패: {e}")

    # ===== SmartRouter 호환성 메서드들 =====

    def get_connection_health(self) -> float:
        """WebSocket 연결 건강도 반환 (0.0-1.0)"""
        if not self.type_subscriptions:
            return 0.5

        # 구독별 메시지 수신율 기반 건강도 계산
        total_health = 0.0
        active_subscriptions = 0

        for subscription in self.type_subscriptions.values():
            age_seconds = (datetime.now() - subscription.created_at).total_seconds()
            if age_seconds > 0:
                message_rate = subscription.message_count / age_seconds
                health_score = min(1.0, message_rate / 1.0)
                total_health += health_score
                active_subscriptions += 1

        return total_health / active_subscriptions if active_subscriptions > 0 else 0.5

    def get_subscription_info(self, subscription_id: Optional[str]) -> Dict[str, Any]:
        """구독 정보 반환"""
        if not subscription_id:
            return {
                "is_new_subscription": True,
                "age_ms": 0,
                "subscription_id": None,
                "sequence": 0,
                "type": "unknown"
            }

        # subscription_id에서 타입 추출
        subscription_type_str = subscription_id.split('_')[0] if '_' in subscription_id else subscription_id

        try:
            subscription_type = SubscriptionType(subscription_type_str)
            if subscription_type in self.type_subscriptions:
                subscription = self.type_subscriptions[subscription_type]
                age_ms = (datetime.now() - subscription.created_at).total_seconds() * 1000

                return {
                    "is_new_subscription": age_ms < 1000,
                    "age_ms": age_ms,
                    "subscription_id": subscription_id,
                    "sequence": subscription.message_count,
                    "type": subscription_type.value,
                    "symbol_count": len(subscription.symbols),
                    "message_count": subscription.message_count
                }
        except ValueError:
            pass

        return {
            "is_new_subscription": True,
            "age_ms": 0,
            "subscription_id": subscription_id,
            "sequence": 0,
            "type": "unknown"
        }

    def update_message_count(self, subscription_type: SubscriptionType) -> None:
        """메시지 수신 시 카운터 업데이트"""
        self.increment_message_count(subscription_type)
