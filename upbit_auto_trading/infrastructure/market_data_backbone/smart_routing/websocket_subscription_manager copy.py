"""
WebSocket 구독 매니저 v5.0 - 간소화된 구독 관리

🎯 핵심 개념:
- 티켓 관리는 기본 WebSocket 클라이언트가 담당 (중앙집중식)
- 상위 매니저는 단순한 구독 상태 추적만 담당
- 타입별 구독으로 모든 심볼 처리
- 복잡한 티켓 로직 제거로 성능 및 안정성 향상
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Set, Optional
from dataclasses import dataclass
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger


"""
WebSocket 구독 매니저 v5.0 - 간소화된 구독 관리

🎯 핵심 개념:
- 티켓 관리는 기본 WebSocket 클라이언트가 담당 (중앙집중식)
- 상위 매니저는 단순한 구독 상태 추적만 담당
- 타입별 구독으로 모든 심볼 처리
- 복잡한 티켓 로직 제거로 성능 및 안정성 향상
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Set, Optional
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger


class SubscriptionType(Enum):
    """구독 타입 - 업비트 WebSocket 지원 타입"""
    TICKER = "ticker"      # 현재가
    TRADE = "trade"        # 체결
    ORDERBOOK = "orderbook"  # 호가
    CANDLE = "candle"      # 캔들


class WebSocketSubscriptionManager:
    """
    WebSocket 구독 매니저 v5.0 - 간소화된 구독 관리

    핵심 원칙:
    - 티켓 관리는 기본 WebSocket 클라이언트에 완전 위임
    - 상위 매니저는 구독 상태 추적만 담당
    - 복잡한 로직 제거로 안정성 및 성능 향상
    """

    def __init__(self, websocket_client):
        """
        Args:
            websocket_client: 티켓 관리 기능이 있는 WebSocket 클라이언트
        """
        self.websocket_client = websocket_client
        self.logger = create_component_logger("WebSocketSubscriptionManager")

        # 간소화된 구독 상태 추적 (타입별)
        self.active_subscriptions: Dict[SubscriptionType, Set[str]] = {}

        self.logger.info("✅ WebSocket 구독 매니저 v5.0 초기화 (간소화된 관리, 티켓은 기본 API 담당)")

    async def subscribe_symbols(
        self,
        symbols: List[str],
        subscription_type: SubscriptionType
    ) -> bool:
        """
        심볼 구독 - 간소화된 버전

        티켓 관리는 기본 WebSocket 클라이언트가 자동 처리
        상위 매니저는 단순히 구독 요청만 전달

        Args:
            symbols: 구독할 심볼 리스트
            subscription_type: 구독 타입

        Returns:
            구독 성공 여부
        """
        if not symbols:
            return True

        try:
            # 🎯 간소화: 기본 WebSocket 클라이언트에 단순 위임
            # 티켓 관리, 중복 처리 등은 모두 기본 API가 담당
            success = await self._call_websocket_subscribe(subscription_type, symbols)

            if success:
                # 구독 상태만 간단히 추적
                if subscription_type not in self.active_subscriptions:
                    self.active_subscriptions[subscription_type] = set()

                self.active_subscriptions[subscription_type].update(symbols)

                self.logger.info(
                    f"✅ 구독 성공: {subscription_type.value} "
                    f"({len(symbols)}개 심볼) - 티켓 관리는 기본 API 담당"
                )
                return True
            else:
                self.logger.warning(f"❌ 구독 실패: {subscription_type.value}")
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
        if subscription_type not in self.active_subscriptions:
            return True

        try:
            # 해제할 심볼 필터링
            symbols_to_remove = [s for s in symbols if s in self.active_subscriptions[subscription_type]]

            if not symbols_to_remove:
                return True

            # 상태에서 제거
            self.active_subscriptions[subscription_type] -= set(symbols_to_remove)

            # 해당 타입에 남은 심볼이 있으면 전체 구독 유지, 없으면 해제
            if self.active_subscriptions[subscription_type]:
                # 남은 심볼들로 구독 재설정
                remaining_symbols = list(self.active_subscriptions[subscription_type])
                success = await self._call_websocket_subscribe(subscription_type, remaining_symbols)
            else:
                # 빈 구독 해제
                success = await self._call_websocket_subscribe(subscription_type, [])
                if success:
                    del self.active_subscriptions[subscription_type]

            if success:
                self.logger.info(
                    f"✅ 구독 해제 성공: {subscription_type.value} "
                    f"(-{len(symbols_to_remove)}개 심볼)"
                )

            return success

        except Exception as e:
            self.logger.error(f"❌ 구독 해제 예외: {e}")
            return False

    async def _call_websocket_subscribe(
        self,
        subscription_type: SubscriptionType,
        symbols: List[str]
    ) -> bool:
        """WebSocket 구독 호출 - 간소화된 위임"""
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

    def get_subscription_status(self) -> Dict[str, Any]:
        """구독 상태 조회 - 간소화된 버전"""
        total_symbols = sum(len(symbols) for symbols in self.active_subscriptions.values())

        status = {
            "total_subscription_types": len(self.active_subscriptions),
            "total_symbols": total_symbols,
            "subscriptions": {}
        }

        for sub_type, symbols in self.active_subscriptions.items():
            status["subscriptions"][sub_type.value] = {
                "symbol_count": len(symbols),
                "symbols": list(symbols)
            }

        return status

    def is_symbol_subscribed(self, symbol: str, subscription_type: SubscriptionType) -> bool:
        """심볼이 구독 중인지 확인"""
        if subscription_type not in self.active_subscriptions:
            return False
        return symbol in self.active_subscriptions[subscription_type]

    def get_symbols_by_type(self, subscription_type: SubscriptionType) -> List[str]:
        """특정 타입의 구독 심볼 목록"""
        if subscription_type not in self.active_subscriptions:
            return []
        return list(self.active_subscriptions[subscription_type])

    async def cleanup(self) -> None:
        """정리 작업 - 간소화된 버전"""
        try:
            # 모든 구독 해제 (기본 WebSocket 클라이언트가 티켓 정리)
            for subscription_type in list(self.active_subscriptions.keys()):
                await self._call_websocket_subscribe(subscription_type, [])

            self.active_subscriptions.clear()
            self.logger.info("🧹 WebSocket 구독 매니저 v5.0 정리 완료")

        except Exception as e:
            self.logger.error(f"❌ 정리 작업 실패: {e}")

    # ===== 레거시 호환성 메서드들 (기존 SmartRouter와의 호환성 보장) =====

    async def request_batch_subscription(
        self,
        symbols: List[str],
        subscription_type: SubscriptionType,
        priority: int = 5  # 더 이상 사용되지 않음
    ) -> bool:
        """기존 SmartRouter 호환성을 위한 배치 구독 메서드"""
        return await self.subscribe_symbols(symbols, subscription_type)

    def can_handle_subscription(
        self,
        symbols: List[str],
        subscription_type: SubscriptionType
    ) -> bool:
        """구독 처리 가능 여부 확인 - 간소화된 버전

        v5.0에서는 기본 WebSocket 클라이언트가 티켓 관리를 담당하므로
        항상 처리 가능 (티켓 한계는 기본 API가 자동 관리)
        """
        return True

    def get_current_subscription_count(self) -> int:
        """현재 구독 타입 수 반환"""
        return len(self.active_subscriptions)

    def get_max_subscription_count(self) -> int:
        """최대 구독 가능 수 반환 - 티켓 관리는 기본 API 담당"""
        return 4  # 업비트 지원 타입 수

    # ===== 기존 복잡한 메서드들 제거됨 =====
    # - _execute_subscription_update (기본 API 위임)
    # - _execute_unsubscription (기본 API 위임)
    # - _make_space_for_new_type (우선순위 관리 불필요)
    # - _restore_subscriptions (기본 API가 처리)
    # - _record_subscription_performance (단순화)
    # - 복잡한 티켓 관리 로직들 (기본 API로 이동)

    # ===== 호환성을 위한 더미 메서드들 =====

    def get_connection_health(self) -> float:
        """WebSocket 연결 건강도 반환 (0.0-1.0)"""
        return 1.0 if self.active_subscriptions else 0.5

    def get_subscription_info(self, subscription_id: Optional[str]) -> Dict[str, Any]:
        """구독 정보 반환 - 간소화된 버전"""
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
            if subscription_type in self.active_subscriptions:
                return {
                    "is_new_subscription": False,
                    "age_ms": 1000,  # 임의 값
                    "subscription_id": subscription_id,
                    "sequence": 0,  # 간소화
                    "type": subscription_type.value,
                    "symbol_count": len(self.active_subscriptions[subscription_type])
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

    def increment_message_count(self, subscription_type: SubscriptionType) -> None:
        """메시지 수신 카운트 - 더 이상 필요 없음 (간소화)"""
        pass

    def update_message_count(self, subscription_type: SubscriptionType) -> None:
        """메시지 수신 시 카운터 업데이트 - 더 이상 필요 없음 (간소화)"""
        pass

    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 조회 - 간소화된 버전"""
        return {
            "message": "성능 추적 간소화됨 - 기본 WebSocket API가 티켓 최적화 담당",
            "total_subscription_types": len(self.active_subscriptions),
            "total_symbols": sum(len(symbols) for symbols in self.active_subscriptions.values())
        }

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
                # 부분 구독 해제 - 선언형 방식으로 남은 심볼만 구독
                success = await self._execute_subscription_update(
                    subscription_type, list(subscription.symbols)
                )
                if success:
                    self.logger.info(
                        f"✅ 선언형 심볼 제거: {subscription_type.value} "
                        f"(-{len(removed_symbols)}개 → 남은 {len(subscription.symbols)}개)"
                    )
                    return True
                else:
                    # 실패시 심볼 롤백
                    subscription.add_symbols(removed_symbols)
                    self.logger.warning(f"❌ 선언형 제거 실패, 롤백: {subscription_type.value}")
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
        """WebSocket 구독 해제 실행 - 선언형 방식 (99.3% 성능 향상)"""
        try:
            # ✅ 선언형 구독 관리: 빈 심볼 목록으로 덮어쓰기
            # 테스트로 입증된 0.7ms vs 100.9ms (재연결) 성능
            success = await self._execute_subscription_update(subscription_type, [])

            if success:
                self.logger.info(
                    f"✅ 선언형 구독 해제 완료: {subscription_type.value} "
                    f"(덮어쓰기 방식, 재연결 없음)"
                )
                return True
            else:
                # 폴백: 전체 구독 상태 재설정 (필요시에만)
                self.logger.warning(f"⚠️ 선언형 해제 실패, 폴백 실행: {subscription_type.value}")
                if hasattr(self.websocket_client, 'unsubscribe_all'):
                    return await self.websocket_client.unsubscribe_all()
                return False

        except Exception as e:
            self.logger.error(f"❌ 선언형 구독 해제 실패: {e}")
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

    # =====================================
    # 🚀 3단계: WebSocket 소스 정보 추가 메서드들
    # =====================================

    def get_connection_health(self) -> float:
        """WebSocket 연결 건강도 반환 (0.0-1.0)"""
        if not self.type_subscriptions:
            return 0.5  # 구독 없음

        # 구독별 메시지 수신율 기반 건강도 계산
        total_health = 0.0
        active_subscriptions = 0

        for subscription in self.type_subscriptions.values():
            age_seconds = (datetime.now() - subscription.created_at).total_seconds()

            if age_seconds > 0:
                message_rate = subscription.message_count / age_seconds
                # 1초당 1메시지 이상이면 건강한 상태로 간주
                health_score = min(1.0, message_rate / 1.0)
                total_health += health_score
                active_subscriptions += 1

        if active_subscriptions == 0:
            return 0.5

        return total_health / active_subscriptions

    def get_subscription_info(self, subscription_id: Optional[str]) -> Dict[str, Any]:
        """구독 정보 반환"""
        # subscription_id를 타입으로 매핑하여 정보 반환
        if not subscription_id:
            return {
                "is_new_subscription": True,
                "age_ms": 0,
                "subscription_id": None,
                "sequence": 0,
                "type": "unknown"
            }

        # subscription_id에서 타입 추출 (예: "ticker_KRW-BTC" -> "ticker")
        subscription_type_str = subscription_id.split('_')[0] if '_' in subscription_id else subscription_id

        try:
            subscription_type = SubscriptionType(subscription_type_str)
            if subscription_type in self.type_subscriptions:
                subscription = self.type_subscriptions[subscription_type]
                age_ms = (datetime.now() - subscription.created_at).total_seconds() * 1000

                return {
                    "is_new_subscription": age_ms < 1000,  # 1초 미만이면 새 구독
                    "age_ms": age_ms,
                    "subscription_id": subscription_id,
                    "sequence": subscription.message_count,
                    "type": subscription_type.value,
                    "symbol_count": len(subscription.symbols),
                    "message_count": subscription.message_count
                }
        except ValueError:
            pass  # 잘못된 구독 타입

        # 구독 정보를 찾을 수 없음
        return {
            "is_new_subscription": True,
            "age_ms": 0,
            "subscription_id": subscription_id,
            "sequence": 0,
            "type": "unknown"
        }

    def update_message_count(self, subscription_type: SubscriptionType) -> None:
        """메시지 수신 시 카운터 업데이트"""
        if subscription_type in self.type_subscriptions:
            self.type_subscriptions[subscription_type].message_count += 1
            self.type_subscriptions[subscription_type].last_updated = datetime.now()
