"""
WebSocket 구독 매니저 v2.0 - 극도 보수적 전략

🚨 핵심 원칙:
- 기본 1개 구독, 최대 2개 (비상시)
- 6개 이상 시 심각한 성능 저하 (10초+ 대기)
- 초당 50개 미만 메시지 = 성능 경고
- 전체 재연결 방식 (개별 구독 해제 불가)

성능 기준:
- 정상: 초당 100+ 메시지
- 경고: 초당 50-100 메시지
- 위험: 초당 50 미만 메시지 → 즉시 단일 구독 모드
"""

import asyncio
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
    극도 보수적 WebSocket 구독 매니저

    🚨 사용자 요구사항:
    "제발 부탁이니 1~2개의 구독을 유지하고 통상 1개만 유지하기를 바랍니다"
    "6개 부터 사실상 통신이 안됩니다. 10초 이상 대기가 걸리기도 합니다"
    "초당 22개 메세지는 매우 적은 양입니다. 엄청 않좋은 상태입니다"
    """

    def __init__(self, websocket_client, max_subscriptions: int = 1):
        """
        Args:
            websocket_client: WebSocket 클라이언트
            max_subscriptions: 최대 구독 수 (기본 1개, 비상시 2개)
        """
        self.websocket_client = websocket_client
        self.logger = create_component_logger("WebSocketSubscriptionManager")

        # 🚨 극도 보수적 설정
        self.max_subscriptions = max_subscriptions  # 기본 1개
        self.emergency_limit = 2  # 비상시 최대 2개

        # 구독 관리
        self.active_subscriptions: Dict[str, SubscriptionInfo] = {}
        self.subscription_history: List[SubscriptionInfo] = []
        self.subscription_count = 0

        # 성능 모니터링
        self.message_count = 0
        self.performance_threshold = 50  # 초당 최소 메시지 수
        self.last_performance_check: Optional[datetime] = None
        self.performance_degraded = False

        # 비활성 구독 정리
        self.inactive_timeout = timedelta(minutes=5)
        self.optimization_count = 0

        # 백그라운드 태스크
        self.is_monitoring = True
        self.performance_monitor_task: Optional[asyncio.Task] = None

        # 즉시 성능 모니터링 시작
        self._start_performance_monitoring()

        self.logger.info(f"🚨 극도 보수적 구독 매니저 초기화 (최대 {max_subscriptions}개)")

    def _start_performance_monitoring(self) -> None:
        """성능 모니터링 시작"""
        if not self.performance_monitor_task or self.performance_monitor_task.done():
            self.performance_monitor_task = asyncio.create_task(self._performance_monitor())
            self.logger.debug("📊 성능 모니터링 시작")

    async def _performance_monitor(self) -> None:
        """
        백그라운드 성능 모니터링

        - 10초마다 메시지 수신 속도 체크
        - 50개/초 미만 시 비상 최적화 실행
        """
        while self.is_monitoring:
            try:
                await asyncio.sleep(10)  # 10초마다 체크
                await self._check_performance()
                await self._cleanup_inactive_subscriptions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"성능 모니터링 오류: {e}")

    async def _check_performance(self) -> None:
        """성능 체크 및 자동 최적화"""
        current_time = datetime.now()

        if self.last_performance_check:
            time_diff = (current_time - self.last_performance_check).total_seconds()
            if time_diff > 0:
                messages_per_second = self.message_count / time_diff

                self.logger.debug(f"📊 성능 체크: {messages_per_second:.1f} 메시지/초")

                # 성능 임계값 체크
                if messages_per_second < self.performance_threshold:
                    if not self.performance_degraded:
                        self.logger.warning(f"⚠️ 성능 저하 감지: {messages_per_second:.1f}/초 < {self.performance_threshold}")
                        self.performance_degraded = True
                        await self._emergency_downgrade()
                else:
                    if self.performance_degraded:
                        self.logger.info(f"✅ 성능 회복: {messages_per_second:.1f}/초")
                        self.performance_degraded = False

        # 카운터 리셋
        self.message_count = 0
        self.last_performance_check = current_time

    async def _emergency_downgrade(self) -> None:
        """
        비상 성능 최적화

        성능 저하 시 강제로 단일 구독 모드 전환
        """
        self.logger.warning("🚨 비상 성능 최적화 실행")

        if len(self.active_subscriptions) > 1:
            await self.force_single_subscription_mode()
        elif len(self.active_subscriptions) == 0:
            self.logger.warning("🚨 활성 구독 없음 - WebSocket 연결 상태 확인 필요")
        else:
            # 이미 단일 구독인데도 성능이 나쁘면 재연결
            self.logger.warning("🚨 단일 구독에서도 성능 저하 - 재연결 시도")
            await self._resubscribe_all()

    async def _cleanup_inactive_subscriptions(self) -> None:
        """비활성 구독 정리"""
        current_time = datetime.now()
        inactive_subscriptions = []

        for key, info in self.active_subscriptions.items():
            if current_time - info.last_requested > self.inactive_timeout:
                inactive_subscriptions.append(key)

        if inactive_subscriptions:
            self.logger.info(f"🧹 비활성 구독 {len(inactive_subscriptions)}개 해제 중...")
            for key in inactive_subscriptions:
                del self.active_subscriptions[key]

            # 전체 재구독 (업비트는 개별 해제 불가)
            await self._resubscribe_all()
            self.optimization_count += 1

    async def request_subscription(
        self,
        symbol: str,
        subscription_type: SubscriptionType,
        priority: int = 5
    ) -> bool:
        """
        🚨 극도 보수적 구독 요청

        전략:
        1. 기본적으로 단일 구독만 허용
        2. 새 요청 시 기존 구독 즉시 교체
        3. 우선순위 기반 선택
        4. 성능 모니터링 연동

        Args:
            symbol: 심볼 (예: KRW-BTC)
            subscription_type: 구독 타입
            priority: 우선순위 (1=최고, 10=최저)

        Returns:
            구독 성공 여부
        """
        subscription_key = f"{symbol}:{subscription_type.value}"
        current_time = datetime.now()

        # 기존 구독이 있으면 갱신
        if subscription_key in self.active_subscriptions:
            self.active_subscriptions[subscription_key].last_requested = current_time
            self.active_subscriptions[subscription_key].request_count += 1
            self.logger.debug(f"✅ 기존 구독 갱신: {subscription_key}")
            return True

        # 🚨 극도 보수적 전략: 기본적으로 1개만 허용
        current_count = len(self.active_subscriptions)

        if current_count >= self.max_subscriptions:
            # 단일 구독 모드: 즉시 교체
            if self.max_subscriptions == 1:
                self.logger.info(f"🔄 단일 구독 교체: {subscription_key}")
                await self._replace_single_subscription(symbol, subscription_type, priority, current_time)
                return True

            # 2개 허용 모드: 우선순위 기반 교체
            elif self.max_subscriptions == 2:
                return await self._smart_replace_subscription(symbol, subscription_type, priority, current_time)

            # 그 외에는 거부
            else:
                self.logger.warning(f"⚠️ 구독 거부: 최대 {self.max_subscriptions}개 초과 - {subscription_key}")
                return False

        # 빈 슬롯이 있으면 추가
        new_subscription = SubscriptionInfo(
            symbol=symbol,
            subscription_type=subscription_type,
            last_requested=current_time,
            request_count=1,
            priority=priority
        )

        self.active_subscriptions[subscription_key] = new_subscription
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
        """단일 구독 즉시 교체"""
        # 기존 구독 정보 저장 (히스토리용)
        if self.active_subscriptions:
            old_key = list(self.active_subscriptions.keys())[0]
            old_subscription = self.active_subscriptions[old_key]
            self.subscription_history.append(old_subscription)

            self.logger.info(f"🔄 구독 교체: {old_key} → {symbol}:{subscription_type.value}")

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
        """지능형 구독 교체 (2개 모드)"""
        subscription_key = f"{symbol}:{subscription_type.value}"

        # 가장 낮은 우선순위 구독 찾기
        lowest_priority_key = min(
            self.active_subscriptions.keys(),
            key=lambda k: (
                self.active_subscriptions[k].priority,
                -self.active_subscriptions[k].request_count,  # 요청 횟수가 적은 것
                self.active_subscriptions[k].last_requested   # 오래된 것
            )
        )

        lowest_priority_sub = self.active_subscriptions[lowest_priority_key]

        # 새 구독이 더 우선순위가 높으면 교체
        if priority < lowest_priority_sub.priority:
            self.logger.info(f"🔄 우선순위 교체: {lowest_priority_key} (우선순위 {lowest_priority_sub.priority}) → {subscription_key} (우선순위 {priority})")

            # 교체 실행
            del self.active_subscriptions[lowest_priority_key]

            new_subscription = SubscriptionInfo(
                symbol=symbol,
                subscription_type=subscription_type,
                last_requested=current_time,
                request_count=1,
                priority=priority
            )

            self.active_subscriptions[subscription_key] = new_subscription
            await self._resubscribe_all()
            return True

        self.logger.info(f"⚠️ 구독 거부: 우선순위 부족 - {subscription_key} (우선순위 {priority}) vs 기존 최저 {lowest_priority_sub.priority}")
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
            "performance_threshold": self.performance_threshold,
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

    async def force_single_subscription_mode(self) -> None:
        """
        강제 단일 구독 모드 전환 (비상 최적화)
        """
        self.logger.warning("🚨 강제 단일 구독 모드 전환")

        old_max = self.max_subscriptions
        self.max_subscriptions = 1

        # 현재 구독이 1개 초과면 가장 우선순위 높은 것만 남기기
        if len(self.active_subscriptions) > 1:
            # 우선순위별 정렬
            sorted_subs = sorted(
                self.active_subscriptions.items(),
                key=lambda x: (
                    x[1].priority,
                    -x[1].request_count,
                    x[1].last_requested
                )
            )

            # 최고 우선순위 구독만 유지
            keep_key, keep_sub = sorted_subs[0]
            self.active_subscriptions = {keep_key: keep_sub}

            # 전체 재구독
            await self._resubscribe_all()

            self.logger.warning(f"🚨 단일 구독 모드: {keep_key} 유지 (이전 {old_max}개 → 1개)")

        # 성능 모니터링 강화
        self.performance_threshold = 30  # 더 엄격한 임계값

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
