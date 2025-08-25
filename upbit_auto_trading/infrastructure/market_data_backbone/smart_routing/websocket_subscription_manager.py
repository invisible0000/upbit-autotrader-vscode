"""
WebSocket 구독 매니저 v3.0 - 올바른 업비트 구독 모델

🎯 핵심 개념 수정:
- 업비트 WebSocket 구독 = 타입별 하나의 구독으로 모든 심볼 처리 가능
- 예: ticker 타입 하나로 189개 KRW 심볼 모두 구독 가능
- 최대 제한: 4개 구독 타입 (ticker, trade, orderbook, candle)
- 성능 목표: 직접 WebSocket 수준 (6,392+ 심볼/초)
"""

import asyncio
import time
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
class TypeSubscription:
    """타입별 구독 정보 - 하나의 타입에 여러 심볼"""
    subscription_type: SubscriptionType
    symbols: Set[str]                    # 구독 중인 심볼들
    last_updated: datetime              # 마지막 업데이트 시간
    created_at: datetime                # 구독 생성 시간
    message_count: int = 0              # 수신된 메시지 수
    priority: int = 5                   # 우선순위 (1=최고, 10=최저)

    def add_symbols(self, new_symbols: List[str]) -> List[str]:
        """새 심볼 추가 - 실제 추가된 심볼만 반환"""
        before_count = len(self.symbols)
        self.symbols.update(new_symbols)
        self.last_updated = datetime.now()

        # 실제 추가된 심볼 계산
        added_symbols = []
        if len(self.symbols) > before_count:
            added_symbols = [s for s in new_symbols if s in self.symbols]

        return added_symbols

    def remove_symbols(self, remove_symbols: List[str]) -> List[str]:
        """심볼 제거 - 실제 제거된 심볼만 반환"""
        removed_symbols = []
        for symbol in remove_symbols:
            if symbol in self.symbols:
                self.symbols.remove(symbol)
                removed_symbols.append(symbol)

        if removed_symbols:
            self.last_updated = datetime.now()

        return removed_symbols

    def has_symbol(self, symbol: str) -> bool:
        """심볼 구독 여부 확인"""
        return symbol in self.symbols

    def is_empty(self) -> bool:
        """빈 구독인지 확인"""
        return len(self.symbols) == 0


class WebSocketSubscriptionManager:
    """
    WebSocket 구독 매니저 v3.0 - 올바른 업비트 구독 모델

    핵심 원칙:
    - 타입별 하나의 구독으로 모든 심볼 처리
    - 최대 4개 구독 타입으로 모든 데이터 커버
    - 직접 WebSocket 수준 성능 달성
    """

    def __init__(self, websocket_client, max_subscription_types: int = 4):
        """
        Args:
            websocket_client: WebSocket 클라이언트
            max_subscription_types: 최대 구독 타입 수 (업비트: 4개면 충분)
        """
        self.websocket_client = websocket_client
        self.logger = create_component_logger("WebSocketSubscriptionManager")

        # 타입별 구독 관리 (최대 4개 타입)
        self.max_subscription_types = min(max_subscription_types, 4)
        self.type_subscriptions: Dict[SubscriptionType, TypeSubscription] = {}

        # 성능 모니터링
        self.total_symbols_subscribed = 0
        self.total_messages_received = 0
        self.last_performance_check = datetime.now()

        # 구독 변경 성능 추적
        self.subscription_changes = []
        self.last_subscription_change = None

        self.logger.info(
            f"✅ WebSocket 구독 매니저 v3.0 초기화 "
            f"(최대 {self.max_subscription_types}개 타입, 무제한 심볼)"
        )

    async def subscribe_symbols(
        self,
        symbols: List[str],
        subscription_type: SubscriptionType,
        priority: int = 5
    ) -> bool:
        """
        심볼 구독 - 타입별 일괄 처리

        Args:
            symbols: 구독할 심볼 리스트
            subscription_type: 구독 타입
            priority: 우선순위

        Returns:
            구독 성공 여부
        """
        if not symbols:
            return True

        start_time = time.perf_counter()

        try:
            # 기존 구독이 있으면 심볼 추가
            if subscription_type in self.type_subscriptions:
                existing_sub = self.type_subscriptions[subscription_type]
                new_symbols = [s for s in symbols if not existing_sub.has_symbol(s)]

                if not new_symbols:
                    self.logger.debug(f"모든 심볼이 이미 구독됨: {subscription_type.value}")
                    return True

                # 기존 구독에 심볼 추가
                added_symbols = existing_sub.add_symbols(new_symbols)
                if added_symbols:
                    # WebSocket에 추가 구독 요청
                    success = await self._execute_subscription_update(
                        subscription_type, list(existing_sub.symbols)
                    )
                    if success:
                        self.logger.info(
                            f"✅ 심볼 추가 완료: {subscription_type.value} "
                            f"(+{len(added_symbols)}개, 총 {len(existing_sub.symbols)}개)"
                        )
                        return True
                    else:
                        # 실패시 롤백
                        existing_sub.remove_symbols(added_symbols)
                        return False

                return True

            else:
                # 새 타입 구독 생성
                if len(self.type_subscriptions) >= self.max_subscription_types:
                    # 공간 확보 필요
                    if not await self._make_space_for_new_type(priority):
                        self.logger.warning(
                            f"⚠️ 구독 타입 한계 초과: {len(self.type_subscriptions)}/{self.max_subscription_types}"
                        )
                        return False

                # 새 구독 생성
                new_subscription = TypeSubscription(
                    subscription_type=subscription_type,
                    symbols=set(symbols),
                    last_updated=datetime.now(),
                    created_at=datetime.now(),
                    priority=priority
                )

                # WebSocket 구독 실행
                success = await self._execute_subscription_update(subscription_type, symbols)
                if success:
                    self.type_subscriptions[subscription_type] = new_subscription
                    self.total_symbols_subscribed += len(symbols)

                    self.logger.info(
                        f"✅ 새 타입 구독 생성: {subscription_type.value} "
                        f"({len(symbols)}개 심볼)"
                    )
                    return True
                else:
                    return False

        except Exception as e:
            self.logger.error(f"❌ 구독 실행 예외: {e}")
            return False

        finally:
            # 성능 기록
            elapsed_time = (time.perf_counter() - start_time) * 1000
            self._record_subscription_performance(
                subscription_type, len(symbols), elapsed_time, True
            )

    async def unsubscribe_symbols(
        self,
        symbols: List[str],
        subscription_type: SubscriptionType
    ) -> bool:
        """
        심볼 구독 해제

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
                # 타입 전체 구독 해제
                success = await self._execute_unsubscription(subscription_type)
                if success:
                    del self.type_subscriptions[subscription_type]
                    self.logger.info(f"✅ 타입 구독 해제: {subscription_type.value}")
                    return True
                else:
                    # 실패시 심볼 롤백
                    subscription.add_symbols(removed_symbols)
                    return False
            else:
                # 일부 심볼만 해제 - 전체 구독 업데이트
                success = await self._execute_subscription_update(
                    subscription_type, list(subscription.symbols)
                )
                if success:
                    self.logger.info(
                        f"✅ 심볼 제거 완료: {subscription_type.value} "
                        f"(-{len(removed_symbols)}개, 남은 {len(subscription.symbols)}개)"
                    )
                    return True
                else:
                    # 실패시 심볼 롤백
                    subscription.add_symbols(removed_symbols)
                    return False

        except Exception as e:
            self.logger.error(f"❌ 구독 해제 예외: {e}")
            # 예외 시 심볼 롤백
            subscription.add_symbols(removed_symbols)
            return False

    async def _execute_subscription_update(
        self,
        subscription_type: SubscriptionType,
        symbols: List[str]
    ) -> bool:
        """WebSocket 구독 업데이트 실행"""
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
            self.logger.error(f"❌ WebSocket 구독 실행 실패: {e}")
            return False

    async def _execute_unsubscription(self, subscription_type: SubscriptionType) -> bool:
        """WebSocket 구독 해제 실행"""
        try:
            # 업비트는 개별 구독 해제를 지원하지 않으므로
            # 연결 재설정 또는 전체 재구독 필요
            if hasattr(self.websocket_client, 'unsubscribe_all'):
                return await self.websocket_client.unsubscribe_all()
            else:
                # 재연결로 구독 정리
                if hasattr(self.websocket_client, 'reconnect'):
                    success = await self.websocket_client.reconnect()
                    if success:
                        # 나머지 구독 복원
                        return await self._restore_subscriptions(exclude_type=subscription_type)
                    return False
                return True  # 연결 재설정 기능이 없으면 성공으로 처리

        except Exception as e:
            self.logger.error(f"❌ WebSocket 구독 해제 실패: {e}")
            return False

    async def _restore_subscriptions(self, exclude_type: Optional[SubscriptionType] = None) -> bool:
        """모든 구독 복원 (특정 타입 제외)"""
        try:
            for sub_type, subscription in self.type_subscriptions.items():
                if sub_type == exclude_type:
                    continue

                success = await self._execute_subscription_update(
                    sub_type, list(subscription.symbols)
                )
                if not success:
                    self.logger.error(f"❌ 구독 복원 실패: {sub_type.value}")
                    return False

                await asyncio.sleep(0.1)  # 구독 간 간격

            return True

        except Exception as e:
            self.logger.error(f"❌ 구독 복원 예외: {e}")
            return False

    async def _make_space_for_new_type(self, priority: int) -> bool:
        """새 타입을 위한 공간 확보"""
        if len(self.type_subscriptions) < self.max_subscription_types:
            return True

        # 가장 낮은 우선순위 찾기
        lowest_priority_type = None
        lowest_priority = 0

        for sub_type, subscription in self.type_subscriptions.items():
            if subscription.priority > lowest_priority:
                lowest_priority = subscription.priority
                lowest_priority_type = sub_type

        # 새 요청이 기존 최저 우선순위보다 높으면 교체
        if lowest_priority_type and priority < lowest_priority:
            # 기존 구독 제거
            success = await self._execute_unsubscription(lowest_priority_type)
            if success:
                del self.type_subscriptions[lowest_priority_type]
                self.logger.info(
                    f"🔄 낮은 우선순위 타입 제거: {lowest_priority_type.value} "
                    f"(우선순위: {lowest_priority} → {priority})"
                )
                return True

        return False

    def get_subscription_status(self) -> Dict[str, Any]:
        """구독 상태 조회"""
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
                "last_updated": subscription.last_updated.isoformat(),
                "priority": subscription.priority
            }

        return status

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

    def _record_subscription_performance(
        self,
        subscription_type: SubscriptionType,
        symbol_count: int,
        elapsed_time_ms: float,
        success: bool
    ) -> None:
        """구독 성능 기록"""
        self.subscription_changes.append({
            "timestamp": datetime.now(),
            "subscription_type": subscription_type.value,
            "symbol_count": symbol_count,
            "elapsed_time_ms": elapsed_time_ms,
            "success": success,
            "symbols_per_second": symbol_count / (elapsed_time_ms / 1000) if elapsed_time_ms > 0 else 0
        })

        # 최근 10개 기록만 유지
        if len(self.subscription_changes) > 10:
            self.subscription_changes = self.subscription_changes[-10:]

    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 조회"""
        if not self.subscription_changes:
            return {"message": "성능 데이터 없음"}

        recent_changes = self.subscription_changes[-5:]  # 최근 5개

        avg_time = sum(c["elapsed_time_ms"] for c in recent_changes) / len(recent_changes)
        avg_symbols_per_second = sum(c["symbols_per_second"] for c in recent_changes) / len(recent_changes)
        success_rate = sum(1 for c in recent_changes if c["success"]) / len(recent_changes)

        return {
            "recent_average_time_ms": round(avg_time, 2),
            "recent_average_symbols_per_second": round(avg_symbols_per_second, 1),
            "recent_success_rate": round(success_rate * 100, 1),
            "total_subscription_changes": len(self.subscription_changes),
            "recent_changes": recent_changes
        }

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
        """구독 처리 가능 여부 확인 (v3.0 호환성 메서드)

        v3.0 모델: 심볼 수는 무제한, 구독 타입 수만 제한
        - 기존 타입이면 무제한 심볼 추가 가능
        - 새 타입이면 버퍼 전략 고려하여 판단
        """
        # 기존 타입이면 심볼 수와 무관하게 항상 처리 가능
        if subscription_type in self.type_subscriptions:
            return True

        # 새 타입이고 여유 공간이 있으면 처리 가능
        if len(self.type_subscriptions) < self.max_subscription_types:
            return True

        # 새 타입이고 공간이 없으면 버퍼 전략으로 처리 가능
        # (기존 낮은 우선순위 타입을 대체할 수 있음)
        return True  # v3.0에서는 항상 처리 가능 (우선순위 관리로 해결)

    def get_current_subscription_count(self) -> int:
        """현재 구독 타입 수 반환 (v3.0 호환성 메서드)

        주의: v3.0에서는 구독 수가 아닌 구독 타입 수를 반환
        """
        return len(self.type_subscriptions)

    def get_max_subscription_count(self) -> int:
        """최대 구독 타입 수 반환 (v3.0 호환성 메서드)

        주의: v3.0에서는 구독 수가 아닌 구독 타입 수 제한
        """
        return self.max_subscription_types

    async def cleanup(self) -> None:
        """정리 작업"""
        try:
            # 모든 구독 해제
            for subscription_type in list(self.type_subscriptions.keys()):
                await self._execute_unsubscription(subscription_type)

            self.type_subscriptions.clear()
            self.logger.info("🧹 WebSocket 구독 매니저 v3.0 정리 완료")

        except Exception as e:
            self.logger.error(f"❌ 정리 작업 실패: {e}")
