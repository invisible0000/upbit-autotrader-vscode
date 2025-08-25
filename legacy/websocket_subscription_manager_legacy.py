"""
WebSocket 구독 매니저 v2.0

🚨 핵심 원칙:
- 최대5개
- 6개 이상 시 심각한 성능 저하 (10초+ 대기)
- 초당 50개 미만 메시지 = 성능 경고

성능 기준:
- 정상: 초당 100+ 메시지
- 경고: 초당 50-100 메시지
- 위험: 초당 50 미만 메시지
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger


class SubscriptionType(Enum):
    """구독 타입"""
    TICKER = "ticker"
    ORDERBOOK = "orderbook"
    TRADE = "trade"


@dataclass
class SubscriptionInfo:
    """구독 정보"""
    symbol: str
    subscription_type: SubscriptionType
    last_requested: datetime
    request_count: int = 1
    priority: int = 5  # 1=최고, 10=최저


class WebSocketSubscriptionManager:
    """
    WebSocket 구독 매니저 v2.0
    업비트의 구독은 5개를 넘어가면 극심한 성능 저하가 발생합니다.
    따라서 구독은 5개 이하를 유지해야 합니다.
    비상시에는 3개로 축소하여 안정성을 확보해야 합니다.
    """

    def __init__(self, websocket_client, max_subscriptions: int = 5):
        """
        Args:
            websocket_client: WebSocket 클라이언트
            max_subscriptions: 최대 구독 수 (업비트 안전 한계: 5개)
        """
        self.websocket_client = websocket_client
        self.logger = create_component_logger("WebSocketSubscriptionManager")

        # 업비트 안전 한계: 5개 (5개 이상 시 급격한 성능 저하)
        self.max_subscriptions = min(max_subscriptions, 5)  # 강제로 5개 제한
        self.emergency_limit = 3    # 비상시 3개로 축소

        # 구독 관리
        self.active_subscriptions: Dict[str, SubscriptionInfo] = {}
        self.subscription_history: List[SubscriptionInfo] = []
        self.subscription_count = 0

        # 성능 모니터링 비활성화 (메시지 수 제한 제거)
        self.message_count = 0
        self.performance_monitoring_disabled = True  # 성능 모니터링 완전 비활성화
        self.last_performance_check: Optional[datetime] = None
        self.performance_degraded = False

        # Phase 2.2: 구독 변경 성능 모니터링
        self.subscription_change_times: List[float] = []  # 구독 변경 소요 시간 기록
        self.smart_change_success_count = 0  # 스마트 변경 성공 횟수
        self.smart_change_total_count = 0    # 스마트 변경 시도 횟수
        self.average_change_time = 0.0       # 평균 구독 변경 시간

        # 비활성 구독 정리
        self.inactive_timeout = timedelta(minutes=5)  # 5분으로 단축 (빠른 정리)
        self.optimization_count = 0

        # 백그라운드 태스크 비활성화 (성능 모니터링 제거)
        self.is_monitoring = False  # 모니터링 비활성화
        self.performance_monitor_task: Optional[asyncio.Task] = None

        self.logger.info(
            f"✅ WebSocket 구독 매니저 초기화 (업비트 안전 한계: 최대 {self.max_subscriptions}개, "
            f"비상시 {self.emergency_limit}개, 실시간 구독 정리 활성화)"
        )

    # 성능 모니터링 비활성화 (제거됨)
    # def _start_performance_monitoring(self) -> None
    # async def _performance_monitor(self) -> None
    # async def _check_performance(self) -> None
    # async def _emergency_downgrade(self) -> None

    async def _cleanup_inactive_subscriptions(self) -> None:
        """미사용 구독 정리 (업비트 안전성 확보)"""
        current_time = datetime.now()
        inactive_subscriptions = []

        for key, info in self.active_subscriptions.items():
            if current_time - info.last_requested > self.inactive_timeout:
                inactive_subscriptions.append(key)

        if inactive_subscriptions:
            self.logger.info(f"🧹 미사용 구독 {len(inactive_subscriptions)}개 정리 중...")
            for key in inactive_subscriptions:
                del self.active_subscriptions[key]

            # 정리 후 전체 재구독 (업비트는 개별 해제 불가)
            await self._resubscribe_all()
            self.optimization_count += 1
            self.logger.info(f"✅ 구독 정리 완료: {len(self.active_subscriptions)}개 유지")

    async def request_subscription(
        self,
        symbol: str,
        subscription_type: SubscriptionType,
        priority: int = 5
    ) -> bool:
        """
        WebSocket 구독 요청 (업비트 안전 한계 5개 준수)

        전략:
        1. 기존 구독이 있으면 갱신
        2. 5개 이하면 즉시 추가
        3. 5개 초과시 미사용 구독 자동 정리 후 추가
        4. 우선순위 기반 스마트 교체

        Args:
            symbol: 심볼 (예: KRW-BTC)
            subscription_type: 구독 타입
            priority: 우선순위 (1=최고, 10=최저)

        Returns:
            구독 성공 여부
        """
        return await self.request_batch_subscription([symbol], subscription_type, priority)

    async def request_batch_subscription(
        self,
        symbols: List[str],
        subscription_type: SubscriptionType,
        priority: int = 5
    ) -> bool:
        """
        WebSocket 배치 구독 요청 (성능 최적화)

        업비트의 다중 심볼 일괄 구독을 활용하여 성능을 극대화합니다.
        재연결 없이 추가 구독만 수행하여 지연을 최소화합니다.

        Args:
            symbols: 심볼 리스트 (예: ["KRW-BTC", "KRW-ETH"])
            subscription_type: 구독 타입
            priority: 우선순위 (1=최고, 10=최저)

        Returns:
            구독 성공 여부
        """
        current_time = datetime.now()
        new_symbols = []

        # 1. 기존 구독 확인 및 갱신
        for symbol in symbols:
            subscription_key = f"{symbol}:{subscription_type.value}"
            if subscription_key in self.active_subscriptions:
                self.active_subscriptions[subscription_key].last_requested = current_time
                self.active_subscriptions[subscription_key].request_count += 1
                self.logger.debug(f"✅ 기존 구독 갱신: {subscription_key}")
            else:
                new_symbols.append(symbol)

        # 2. 신규 구독이 없으면 완료
        if not new_symbols:
            self.logger.debug(f"모든 심볼이 이미 구독됨: {symbols}")
            return True

        # 3. 미사용 구독 자동 정리
        await self._cleanup_inactive_subscriptions()

        # 4. 구독 수 확인 및 공간 확보
        current_count = len(self.active_subscriptions)
        required_space = len(new_symbols)

        if current_count + required_space > self.max_subscriptions:
            # 공간 부족 시 우선순위 기반 정리
            needed_space = current_count + required_space - self.max_subscriptions
            removed_count = await self._remove_low_priority_subscriptions(needed_space, priority)

            if removed_count < needed_space:
                self.logger.warning(
                    f"⚠️ 구독 공간 부족: 필요 {needed_space}, 확보 {removed_count} "
                    f"(현재: {len(self.active_subscriptions)}/{self.max_subscriptions})"
                )
                # 가능한 만큼만 구독
                available_space = self.max_subscriptions - len(self.active_subscriptions)
                new_symbols = new_symbols[:available_space]

        # 5. 신규 구독 추가 (재연결 없이)
        try:
            # 배치 구독 실행
            subscription_success = await self._execute_batch_subscription(new_symbols, subscription_type)

            if subscription_success:
                # 메모리에 구독 정보 저장
                for symbol in new_symbols:
                    subscription_key = f"{symbol}:{subscription_type.value}"
                    new_subscription = SubscriptionInfo(
                        symbol=symbol,
                        subscription_type=subscription_type,
                        last_requested=current_time,
                        request_count=1,
                        priority=priority
                    )
                    self.active_subscriptions[subscription_key] = new_subscription

                self.subscription_count = len(self.active_subscriptions)
                self.logger.info(
                    f"✅ 배치 구독 성공: {new_symbols} ({subscription_type.value}) "
                    f"- 총 {self.subscription_count}/{self.max_subscriptions}개"
                )
                return True
            else:
                self.logger.error(f"❌ 배치 구독 실패: {new_symbols}")
                return False

        except Exception as e:
            self.logger.error(f"❌ 배치 구독 예외: {e}")
            return False
        success = await self._execute_subscription(symbol, subscription_type)

        if success:
            self.subscription_count += 1
            self.logger.info(f"✅ 새 구독 추가: {subscription_key} (총 {len(self.active_subscriptions)}개)")
        else:
            del self.active_subscriptions[subscription_key]
            self.logger.error(f"❌ 구독 실행 실패: {subscription_key}")

        return success

    async def _replace_single_subscription(
        self,
        symbol: str,
        subscription_type: SubscriptionType,
        priority: int,
        current_time: datetime
    ) -> None:
        """
        ⚠️ DEPRECATED: 단일 구독 강제 교체는 연결 불안정을 야기함
        현재는 사용하지 않음 - 다중 구독 지원으로 변경
        """
        self.logger.warning(f"🚫 DEPRECATED: 단일 구독 강제 교체 호출됨 - 무시: {symbol}:{subscription_type.value}")
        return  # 아무것도 하지 않음
        # 기존 구독 정보 저장 (히스토리용)
        if self.active_subscriptions:
            old_key = list(self.active_subscriptions.keys())[0]
            old_subscription = self.active_subscriptions[old_key]
            self.subscription_history.append(old_subscription)

            self.logger.info(f"🔄 구독 교체 시도: {old_key} → {symbol}:{subscription_type.value}")

            # Phase 2.1: 스마트 구독 변경 시도
            smart_change_success = await self._smart_subscription_change(
                symbol, subscription_type, priority, current_time
            )

            if smart_change_success:
                self.logger.info(f"🚀 스마트 구독 교체 성공: {old_key} → {symbol}:{subscription_type.value}")
                return

        # 스마트 변경 실패 또는 기존 구독이 없으면 기존 로직 사용
        self.logger.info(f"🔄 전체 재구독으로 교체: {symbol}:{subscription_type.value}")

        # 새 구독으로 완전 교체
        self.active_subscriptions.clear()

        new_subscription = SubscriptionInfo(
            symbol=symbol,
            subscription_type=subscription_type,
            last_requested=current_time,
            request_count=1,
            priority=priority
        )

        subscription_key = f"{symbol}:{subscription_type.value}"
        self.active_subscriptions[subscription_key] = new_subscription

        # 전체 재구독
        await self._resubscribe_all()

    async def _smart_replace_subscription(
        self,
        symbol: str,
        subscription_type: SubscriptionType,
        priority: int,
        current_time: datetime
    ) -> bool:
        """지능형 구독 교체 (업비트 5개 한계 준수)"""
        subscription_key = f"{symbol}:{subscription_type.value}"

        # 가장 낮은 우선순위 또는 오래된 구독 찾기
        worst_subscription_key = min(
            self.active_subscriptions.keys(),
            key=lambda k: (
                self.active_subscriptions[k].priority,  # 낮은 우선순위
                -self.active_subscriptions[k].request_count,  # 적은 요청 횟수
                self.active_subscriptions[k].last_requested   # 오래된 것
            )
        )

        worst_subscription = self.active_subscriptions[worst_subscription_key]

        # 새 구독이 더 중요하거나 기존 구독이 너무 오래됐으면 교체
        is_higher_priority = priority < worst_subscription.priority
        is_old_subscription = (current_time - worst_subscription.last_requested) > timedelta(minutes=2)

        if is_higher_priority or is_old_subscription:
            reason = "높은 우선순위" if is_higher_priority else "오래된 구독"
            self.logger.info(
                f"🔄 구독 교체({reason}): {worst_subscription_key} "
                f"→ {subscription_key} (총 {self.max_subscriptions}개 유지)"
            )

            # 교체 실행
            del self.active_subscriptions[worst_subscription_key]

            new_subscription = SubscriptionInfo(
                symbol=symbol,
                subscription_type=subscription_type,
                last_requested=current_time,
                request_count=1,
                priority=priority
            )

            self.active_subscriptions[subscription_key] = new_subscription
            await self._resubscribe_all()  # 전체 재구독
            return True

        self.logger.info(
            f"⚠️ 구독 거부: {subscription_key} (우선순위 {priority}) "
            f"vs 기존 최저 {worst_subscription.priority}, 5개 한계 유지"
        )
        return False

    async def _smart_subscription_change(
        self,
        new_symbol: str,
        new_subscription_type: SubscriptionType,
        priority: int,
        current_time: datetime
    ) -> bool:
        """
        🚀 스마트 구독 변경 - Phase 2.1 핵심 기능

        동일 데이터 타입에서는 재연결 없이 심볼만 변경하여 성능 최적화
        """
        # Phase 2.2: 성능 측정 시작
        start_time = time.time()

        new_subscription_key = f"{new_symbol}:{new_subscription_type.value}"

        # 기존 구독 중 동일 타입 찾기
        same_type_subscriptions = [
            (key, sub) for key, sub in self.active_subscriptions.items()
            if sub.subscription_type == new_subscription_type
        ]

        if same_type_subscriptions:
            # 동일 타입이 있으면 심볼만 변경 (재연결 없음)
            old_key, old_subscription = same_type_subscriptions[0]
            old_symbol = old_subscription.symbol

            self.logger.info(f"🚀 스마트 구독 변경: {old_symbol} → {new_symbol} ({new_subscription_type.value})")

            # 기존 구독 제거
            del self.active_subscriptions[old_key]

            # 새 구독 추가
            new_subscription = SubscriptionInfo(
                symbol=new_symbol,
                subscription_type=new_subscription_type,
                last_requested=current_time,
                request_count=1,
                priority=priority
            )
            self.active_subscriptions[new_subscription_key] = new_subscription

            # 심볼만 변경하는 효율적인 구독 실행
            success = await self._execute_symbol_change(old_symbol, new_symbol, new_subscription_type)

            # Phase 2.2: 성능 측정 완료
            elapsed_time = time.time() - start_time
            self._record_subscription_change_performance(elapsed_time, success, is_smart_change=True)

            if success:
                self.logger.info(f"✅ 스마트 구독 변경 완료: {old_symbol} → {new_symbol} (재연결 없음, {elapsed_time:.3f}s)")
                return True
            else:
                # 실패 시 폴백: 전체 재구독
                self.logger.warning("⚠️ 스마트 변경 실패, 전체 재구독으로 폴백")
                await self._resubscribe_all()
                return False
        else:
            # 동일 타입이 없으면 기존 로직 사용
            elapsed_time = time.time() - start_time
            self._record_subscription_change_performance(elapsed_time, False, is_smart_change=False)
            return False

    async def _execute_symbol_change(
        self,
        old_symbol: str,
        new_symbol: str,
        subscription_type: SubscriptionType
    ) -> bool:
        """
        심볼만 변경하는 효율적인 구독 실행

        재연결 없이 구독 내용만 변경하여 성능 최적화
        """
        try:
            # 기존 구독 해제 (연결은 유지)
            if hasattr(self.websocket_client, 'unsubscribe_symbol'):
                await self.websocket_client.unsubscribe_symbol(old_symbol, subscription_type.value)
                await asyncio.sleep(0.1)  # 짧은 대기

            # 새 심볼로 구독
            if subscription_type == SubscriptionType.TICKER:
                await self.websocket_client.subscribe_ticker([new_symbol])
            elif subscription_type == SubscriptionType.ORDERBOOK:
                await self.websocket_client.subscribe_orderbook([new_symbol])
            elif subscription_type == SubscriptionType.TRADE:
                await self.websocket_client.subscribe_trade([new_symbol])

            self.logger.debug(f"✅ 심볼 변경 구독 실행: {old_symbol} → {new_symbol}:{subscription_type.value}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 심볼 변경 구독 실패: {old_symbol} → {new_symbol}:{subscription_type.value} - {e}")
            return False

    async def _execute_subscription(self, symbol: str, subscription_type: SubscriptionType) -> bool:
        """
        실제 WebSocket 구독 실행

        Args:
            symbol: 심볼
            subscription_type: 구독 타입

        Returns:
            구독 성공 여부
        """
        try:
            if subscription_type == SubscriptionType.TICKER:
                await self.websocket_client.subscribe_ticker([symbol])
            elif subscription_type == SubscriptionType.ORDERBOOK:
                await self.websocket_client.subscribe_orderbook([symbol])
            elif subscription_type == SubscriptionType.TRADE:
                await self.websocket_client.subscribe_trade([symbol])
            else:
                self.logger.error(f"❌ 지원하지 않는 구독 타입: {subscription_type}")
                return False

            self.logger.debug(f"✅ WebSocket 구독 실행: {symbol}:{subscription_type.value}")
            return True

        except Exception as e:
            self.logger.error(f"❌ WebSocket 구독 실행 실패: {symbol}:{subscription_type.value} - {e}")
            return False

    async def _execute_batch_subscription(self, symbols: List[str], subscription_type: SubscriptionType) -> bool:
        """
        배치 WebSocket 구독 실행 (성능 최적화)

        Args:
            symbols: 심볼 리스트
            subscription_type: 구독 타입

        Returns:
            구독 성공 여부
        """
        try:
            if not symbols:
                return True

            if subscription_type == SubscriptionType.TICKER:
                await self.websocket_client.subscribe_ticker(symbols)
            elif subscription_type == SubscriptionType.ORDERBOOK:
                await self.websocket_client.subscribe_orderbook(symbols)
            elif subscription_type == SubscriptionType.TRADE:
                await self.websocket_client.subscribe_trade(symbols)
            else:
                self.logger.error(f"❌ 지원하지 않는 구독 타입: {subscription_type}")
                return False

            self.logger.debug(f"✅ WebSocket 배치 구독 실행: {symbols} ({subscription_type.value})")
            return True

        except Exception as e:
            self.logger.error(f"❌ WebSocket 배치 구독 실행 실패: {symbols} ({subscription_type.value}) - {e}")
            return False

    async def _remove_low_priority_subscriptions(self, needed_space: int, min_priority: int) -> int:
        """
        낮은 우선순위 구독 제거

        Args:
            needed_space: 필요한 공간 수
            min_priority: 최소 우선순위 (이보다 낮은 우선순위만 제거)

        Returns:
            실제 제거된 구독 수
        """
        try:
            # 우선순위가 낮고 오래된 구독 찾기
            removable_subscriptions = []
            for key, info in self.active_subscriptions.items():
                if info.priority > min_priority:  # 우선순위가 낮음 (숫자가 클수록 낮음)
                    removable_subscriptions.append((key, info))

            # 우선순위와 마지막 요청 시간 기준으로 정렬
            removable_subscriptions.sort(
                key=lambda x: (x[1].priority, x[1].last_requested)
            )

            # 필요한 만큼 제거
            removed_count = 0
            for i in range(min(needed_space, len(removable_subscriptions))):
                key, info = removable_subscriptions[i]
                del self.active_subscriptions[key]
                removed_count += 1
                self.logger.debug(f"🗑️ 낮은 우선순위 구독 제거: {key} (우선순위: {info.priority})")

            if removed_count > 0:
                # 제거 후 전체 재구독 필요 (업비트 특성상)
                await self._resubscribe_all()
                self.logger.info(f"✅ 낮은 우선순위 구독 {removed_count}개 제거 완료")

            return removed_count

        except Exception as e:
            self.logger.error(f"❌ 낮은 우선순위 구독 제거 실패: {e}")
            return 0

    async def _resubscribe_all(self) -> None:
        """
        전체 재구독 (WebSocket 연결 재설정)

        🚨 중요: 업비트 WebSocket은 개별 구독 취소를 지원하지 않음
        모든 구독 변경 시 전체 재연결 필요
        """
        try:
            self.logger.info(f"🔄 전체 재구독 시작 (총 {len(self.active_subscriptions)}개)")

            # 기존 연결 종료
            if hasattr(self.websocket_client, 'disconnect'):
                await self.websocket_client.disconnect()
                await asyncio.sleep(0.5)  # 연결 종료 대기

            # 새 연결 및 구독
            if hasattr(self.websocket_client, 'connect'):
                await self.websocket_client.connect()
                await asyncio.sleep(0.5)  # 연결 설정 대기

            # 모든 활성 구독 재실행
            for subscription_key, subscription_info in self.active_subscriptions.items():
                await self._execute_subscription(
                    subscription_info.symbol,
                    subscription_info.subscription_type
                )
                await asyncio.sleep(0.1)  # 구독 간 간격

            self.logger.info(f"✅ 전체 재구독 완료: {len(self.active_subscriptions)}개")

        except Exception as e:
            self.logger.error(f"❌ 전체 재구독 실패: {e}")
            # 비상 조치: 모든 구독 정리
            self.active_subscriptions.clear()
            self.subscription_count = 0

    def get_subscription_status(self) -> Dict[str, Any]:
        """
        현재 구독 상태 조회

        Returns:
            구독 상태 정보
        """
        return {
            "active_count": len(self.active_subscriptions),
            "max_subscriptions": self.max_subscriptions,
            "emergency_limit": self.emergency_limit,
            "performance_monitoring_disabled": self.performance_monitoring_disabled,
            "message_count": self.message_count,
            "last_performance_check": self.last_performance_check.isoformat() if self.last_performance_check else None,
            "performance_degraded": self.performance_degraded,
            "active_subscriptions": {
                key: {
                    "symbol": sub.symbol,
                    "type": sub.subscription_type.value,
                    "priority": sub.priority,
                    "request_count": sub.request_count,
                    "last_requested": sub.last_requested.isoformat()
                }
                for key, sub in self.active_subscriptions.items()
            },
            "subscription_history_count": len(self.subscription_history),
            "optimization_count": self.optimization_count
        }

    async def cleanup(self) -> None:
        """
        정리 작업 (성능 모니터링 태스크 종료)
        """
        self.is_monitoring = False
        if self.performance_monitor_task and not self.performance_monitor_task.done():
            self.performance_monitor_task.cancel()
            try:
                await self.performance_monitor_task
            except asyncio.CancelledError:
                pass

        self.logger.info("🧹 WebSocket 구독 매니저 정리 완료")

    # 강제 단일 구독 모드 제거됨 (WebSocket 우선 정책으로 변경)
    # async def force_single_subscription_mode(self) -> None

    def increment_message_count(self) -> None:
        """
        메시지 수신 카운트 증가

        WebSocket 클라이언트에서 메시지 수신 시 호출
        """
        self.message_count += 1

    async def set_max_subscriptions(self, max_subscriptions: int) -> None:
        """
        최대 구독 수 변경

        Args:
            max_subscriptions: 새로운 최대 구독 수
        """
        old_max = self.max_subscriptions
        self.max_subscriptions = min(max_subscriptions, self.emergency_limit)

        self.logger.info(f"📊 최대 구독 수 변경: {old_max} → {self.max_subscriptions}")

        # 현재 구독이 새로운 한계를 초과하면 조정
        if len(self.active_subscriptions) > self.max_subscriptions:
            await self._optimize_subscriptions_to_limit()

    async def _optimize_subscriptions_to_limit(self) -> None:
        """구독 수를 설정된 한계에 맞게 최적화"""
        current_count = len(self.active_subscriptions)
        target_count = self.max_subscriptions

        if current_count <= target_count:
            return

        self.logger.info(f"🔧 구독 최적화: {current_count}개 → {target_count}개")

        # 우선순위별 정렬
        sorted_subs = sorted(
            self.active_subscriptions.items(),
            key=lambda x: (
                x[1].priority,
                -x[1].request_count,
                x[1].last_requested
            )
        )

        # 상위 N개만 유지
        keep_subs = dict(sorted_subs[:target_count])
        removed_keys = [key for key in self.active_subscriptions.keys() if key not in keep_subs]

        self.active_subscriptions = keep_subs

        # 전체 재구독
        await self._resubscribe_all()

        self.logger.info(f"✅ 구독 최적화 완료: {len(removed_keys)}개 제거, {len(self.active_subscriptions)}개 유지")

    def _record_subscription_change_performance(
        self,
        elapsed_time: float,
        success: bool,
        is_smart_change: bool
    ) -> None:
        """
        Phase 2.2: 구독 변경 성능 기록

        Args:
            elapsed_time: 소요 시간 (초)
            success: 성공 여부
            is_smart_change: 스마트 변경 사용 여부
        """
        # 성능 기록 업데이트
        self.subscription_change_times.append(elapsed_time)

        # 최근 10개 기록만 유지
        if len(self.subscription_change_times) > 10:
            self.subscription_change_times = self.subscription_change_times[-10:]

        # 평균 계산
        self.average_change_time = sum(self.subscription_change_times) / len(self.subscription_change_times)

        # 스마트 변경 통계 업데이트
        if is_smart_change:
            self.smart_change_total_count += 1
            if success:
                self.smart_change_success_count += 1

        # 성능 로깅
        success_rate = (self.smart_change_success_count / max(1, self.smart_change_total_count)) * 100
        self.logger.debug(
            f"📊 구독 변경 성능: {elapsed_time:.3f}s, "
            f"평균: {self.average_change_time:.3f}s, "
            f"스마트 변경 성공률: {success_rate:.1f}%"
        )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Phase 2.2: 성능 메트릭 조회

        Returns:
            성능 메트릭 딕셔너리
        """
        smart_success_rate = 0.0
        if self.smart_change_total_count > 0:
            smart_success_rate = (self.smart_change_success_count / self.smart_change_total_count) * 100

        return {
            "average_change_time": self.average_change_time,
            "recent_change_times": self.subscription_change_times.copy(),
            "smart_change_success_rate": smart_success_rate,
            "smart_change_success_count": self.smart_change_success_count,
            "smart_change_total_count": self.smart_change_total_count,
            "active_subscriptions_count": len(self.active_subscriptions),
            "performance_degraded": self.performance_degraded
        }
