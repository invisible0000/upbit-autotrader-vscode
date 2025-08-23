"""
Smart Router 전용 WebSocket 구독 관리자 - 극도 보수적 전략
- 단일 구독 우선 (최대 2개)
- 성능 최적화 중심
- 최소한의 구독으로 최대 효과
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger


class SubscriptionType(Enum):
    """구독 타입"""
    TICKER = "ticker"
    ORDERBOOK = "orderbook"
    TRADE = "trade"
    CANDLE = "candle"


@dataclass
class SubscriptionInfo:
    """구독 정보"""
    symbol: str
    subscription_type: SubscriptionType
    last_requested: datetime
    request_count: int = 1
    priority: int = 5  # 1=최고 우선순위, 10=최저


class WebSocketSubscriptionManager:
    """
    Smart Router 전용 WebSocket 구독 관리자 - 성능 최적화 버전

    🚨 극도 보수적 전략:
    1. 기본: 단일 구독만 유지
    2. 최대: 2개 구독까지만 허용
    3. 즉시 우선순위 기반 교체
    4. 성능 모니터링 및 자동 다운그레이드
    """

    def __init__(self, websocket_client):
        self.websocket_client = websocket_client
        self.logger = create_component_logger("ConservativeWSManager")

        # 🚨 극도 보수적 설정
        self.max_subscriptions = 1  # 기본: 단일 구독
        self.emergency_limit = 2    # 긴급 시에만 2개
        self.performance_threshold = 50  # 초당 메시지 50개 이하 시 경고

        # 구독 상태 추적
        self.active_subscriptions: Dict[str, SubscriptionInfo] = {}
        self.subscription_history: List[SubscriptionInfo] = []

        # 🆕 데이터 저장소 (Smart Router용)
        self._latest_data: Dict[str, Dict[str, Any]] = {}  # {market: {data_type: data}}
        self._data_timestamps: Dict[str, Dict[str, datetime]] = {}  # {market: {data_type: timestamp}}

        # 🚨 성능 모니터링
        self.message_count = 0
        self.last_performance_check = datetime.now()
        self.performance_warnings = 0

        # 백그라운드 설정
        self.cleanup_interval = 30.0  # 30초마다 정리
        self.inactive_timeout = timedelta(minutes=1)  # 1분간 미사용 시 해제 (보수적)

        # 구독 관리 메트릭
        self.subscription_count = 0
        self.unsubscription_count = 0
        self.forced_downgrades = 0  # 성능 이슈로 인한 강제 다운그레이드

        # 백그라운드 태스크
        self._cleanup_task: Optional[asyncio.Task] = None
        self._performance_task: Optional[asyncio.Task] = None
        self._start_background_tasks()

        # 🆕 데이터 핸들러 등록
        self._setup_data_handlers()

    async def _performance_monitor(self) -> None:
        """성능 모니터링 태스크"""
        while True:
            try:
                await asyncio.sleep(10.0)  # 10초마다 체크
                await self._check_performance()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"성능 모니터링 오류: {e}")

    async def _check_performance(self) -> None:
        """성능 상태 확인 및 자동 최적화"""
        current_time = datetime.now()
        time_diff = (current_time - self.last_performance_check).total_seconds()

        if time_diff > 0:
            messages_per_second = self.message_count / time_diff

            # 성능 임계값 확인
            if messages_per_second < self.performance_threshold and len(self.active_subscriptions) > 1:
                self.performance_warnings += 1
                self.logger.warning(f"⚠️ 성능 저하 감지: {messages_per_second:.1f} msg/s (임계값: {self.performance_threshold})")

                # 3회 연속 경고 시 강제 다운그레이드
                if self.performance_warnings >= 3:
                    await self._emergency_downgrade()
                    self.performance_warnings = 0
            else:
                self.performance_warnings = 0  # 성능 정상 시 경고 카운트 리셋

            # 카운터 리셋
            self.message_count = 0
            self.last_performance_check = current_time

    async def _emergency_downgrade(self) -> None:
        """긴급 성능 최적화 - 단일 구독으로 강제 다운그레이드"""
        if len(self.active_subscriptions) <= 1:
            return

        self.logger.warning("🚨 긴급 성능 최적화: 단일 구독으로 다운그레이드")

        # 가장 최근 요청된 구독 1개만 유지
        latest_subscription = max(
            self.active_subscriptions.values(),
            key=lambda x: x.last_requested
        )

        # 기존 구독 정리
        self.active_subscriptions.clear()

        # 최우선 구독만 재등록
        key = f"{latest_subscription.symbol}:{latest_subscription.subscription_type.value}"
        self.active_subscriptions[key] = latest_subscription

        # 전체 재구독
        await self._resubscribe_all()
        self.forced_downgrades += 1
        self.max_subscriptions = 1  # 최대 구독을 1개로 제한

        self.logger.info(f"✅ 긴급 최적화 완료: {latest_subscription.symbol} {latest_subscription.subscription_type.value} 단일 구독 유지")

    def _start_background_tasks(self) -> None:
        """백그라운드 태스크 시작"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

        if self._performance_task is None or self._performance_task.done():
            self._performance_task = asyncio.create_task(self._performance_monitor())

        self.logger.debug("백그라운드 태스크 시작: 정리 + 성능 모니터링")

    def _setup_data_handlers(self) -> None:
        """데이터 수신 핸들러 설정"""
        # WebSocket 클라이언트에서 직접 DataType 가져오기
        from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import WebSocketDataType

        # 모든 데이터 타입에 대해 저장 핸들러 등록
        for data_type in WebSocketDataType:
            self.websocket_client.add_message_handler(data_type, self._store_data_handler)

        self.logger.debug("데이터 핸들러 등록 완료")

    def _store_data_handler(self, message) -> None:
        """WebSocket 메시지 저장 핸들러"""
        try:
            market = message.market
            data_type = message.type.value

            # 마켓별 데이터 초기화
            if market not in self._latest_data:
                self._latest_data[market] = {}
            if market not in self._data_timestamps:
                self._data_timestamps[market] = {}

            # 데이터 저장
            self._latest_data[market][data_type] = message.data
            self._data_timestamps[market][data_type] = message.timestamp

            self.logger.debug(f"📊 데이터 저장: {market} {data_type}")

        except Exception as e:
            self.logger.error(f"데이터 저장 핸들러 오류: {e}")

    def _start_cleanup_task(self) -> None:
        """백그라운드 정리 태스크 시작"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            self.logger.debug("구독 정리 태스크 시작")

    async def _periodic_cleanup(self) -> None:
        """주기적 구독 정리"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_inactive_subscriptions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"구독 정리 중 오류: {e}")

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
            "subscription_history_count": len(self.subscription_history)
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

        # 이미 구독 중인 경우 갱신만
        if subscription_key in self.active_subscriptions:
            self.active_subscriptions[subscription_key].last_requested = current_time
            self.active_subscriptions[subscription_key].request_count += 1
            self.logger.debug(f"🔄 기존 구독 갱신: {subscription_key}")
            return True

        # 구독 제한 확인
        if len(self.active_subscriptions) >= self.max_subscriptions:
            # 가장 오래된 구독 해제 후 재구독
            await self._optimize_subscriptions(subscription_key)

        # 새 구독 추가
        self.active_subscriptions[subscription_key] = SubscriptionInfo(
            symbol=symbol,
            subscription_type=subscription_type,
            last_requested=current_time
        )

        # 실제 WebSocket 구독 요청
        success = await self._execute_subscription(symbol, subscription_type)

        if success:
            self.subscription_count += 1
            self.logger.debug(f"✅ 새 구독 성공: {subscription_key}")
        else:
            # 실패 시 정리
            if subscription_key in self.active_subscriptions:
                del self.active_subscriptions[subscription_key]
            self.logger.warning(f"❌ 구독 실패: {subscription_key}")

        return success

    # =================================================================
    # 📊 데이터 접근 메서드 (Smart Router용)
    # =================================================================

    async def get_latest_data(self, market: str, data_type: str) -> Optional[Dict[str, Any]]:
        """최신 데이터 조회 (Smart Router용)

        Args:
            market: 마켓 코드 (예: "KRW-BTC")
            data_type: 데이터 타입 ("ticker", "orderbook", "trade")

        Returns:
            최신 데이터 또는 None
        """
        if not self._latest_data:
            return None

        market_data = self._latest_data.get(market, {})
        return market_data.get(data_type)

    async def has_recent_data(self, market: str, data_type: str, max_age_seconds: float = 10.0) -> bool:
        """최신 데이터 존재 여부 확인

        Args:
            market: 마켓 코드
            data_type: 데이터 타입
            max_age_seconds: 최대 허용 나이 (초)

        Returns:
            최신 데이터 존재 여부
        """
        if not self._data_timestamps:
            return False

        market_timestamps = self._data_timestamps.get(market, {})
        timestamp = market_timestamps.get(data_type)

        if not timestamp:
            return False

        age = (datetime.now() - timestamp).total_seconds()
        return age <= max_age_seconds

    async def _optimize_subscriptions(self, new_subscription_key: str) -> None:
        """구독 최적화 (5개 제한 대응)"""
        # 가장 오래된 구독 찾기
        oldest_key = min(
            self.active_subscriptions.keys(),
            key=lambda k: self.active_subscriptions[k].last_requested
        )

        self.logger.info(f"🔄 구독 최적화: {oldest_key} 해제 → {new_subscription_key} 추가")

        # 가장 오래된 구독 제거
        del self.active_subscriptions[oldest_key]

        # 전체 재구독 필요 (업비트는 개별 해제 불가)
        await self._resubscribe_all()
        self.optimization_count += 1

    async def _resubscribe_all(self) -> None:
        """전체 재구독 (업비트 개별 해제 불가 대응)"""
        if not self.active_subscriptions:
            return

        # 현재 구독 정보 백업
        current_subscriptions = list(self.active_subscriptions.values())

        # WebSocket 재연결 (모든 구독 해제됨)
        if hasattr(self.websocket_client, 'reconnect'):
            await self.websocket_client.reconnect()

        # 현재 활성 구독들 재구독
        success_count = 0
        for info in current_subscriptions:
            success = await self._execute_subscription(info.symbol, info.subscription_type)
            if success:
                success_count += 1

        self.logger.info(f"🔄 전체 재구독 완료: {success_count}/{len(current_subscriptions)}개 성공")

    async def _execute_subscription(self, symbol: str, subscription_type: SubscriptionType) -> bool:
        """실제 WebSocket 구독 실행"""
        try:
            if subscription_type == SubscriptionType.TICKER:
                return await self.websocket_client.subscribe_ticker([symbol])
            elif subscription_type == SubscriptionType.ORDERBOOK:
                return await self.websocket_client.subscribe_orderbook([symbol])
            elif subscription_type == SubscriptionType.TRADE:
                return await self.websocket_client.subscribe_trade([symbol])
            elif subscription_type == SubscriptionType.CANDLE:
                return await self.websocket_client.subscribe_candle([symbol])
            else:
                self.logger.error(f"지원하지 않는 구독 타입: {subscription_type}")
                return False
        except Exception as e:
            self.logger.error(f"구독 실행 오류: {symbol} {subscription_type} - {e}")
            return False

    def is_subscribed(self, symbol: str, subscription_type: SubscriptionType) -> bool:
        """구독 상태 확인"""
        subscription_key = f"{symbol}:{subscription_type.value}"
        return subscription_key in self.active_subscriptions

    def get_subscription_count(self) -> int:
        """현재 구독 개수 반환"""
        return len(self.active_subscriptions)

    def get_subscription_info(self) -> Dict[str, Any]:
        """구독 정보 반환"""
        return {
            "active_count": len(self.active_subscriptions),
            "max_limit": self.max_subscriptions,
            "subscriptions": {
                key: {
                    "symbol": info.symbol,
                    "type": info.subscription_type.value,
                    "last_requested": info.last_requested.isoformat(),
                    "request_count": info.request_count
                }
                for key, info in self.active_subscriptions.items()
            },
            "metrics": {
                "total_subscriptions": self.subscription_count,
                "total_unsubscriptions": self.unsubscription_count,
                "optimizations": self.optimization_count
            }
        }

    async def cleanup(self) -> None:
        """정리 작업"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        self.active_subscriptions.clear()
        self.logger.debug("구독 관리자 정리 완료")
