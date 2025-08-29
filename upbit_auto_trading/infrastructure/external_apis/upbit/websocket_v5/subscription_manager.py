"""
SubscriptionManager v4.0
========================

혁신적 단순화 설계:
- 웹소켓 덮어쓰기 원리 기반
- 연결별 단일 활성 구독
- 지능적 구독 최적화
- 자동 생명주기 관리

핵심 원칙:
1. Public/Private 연결 분리 관리
2. 클라이언트 인터페이스 극단적 단순화
3. 백그라운드 자동 정리
4. 실시간+스냅샷 지능적 조화

지원 데이터 타입:
- Public: ticker, orderbook, trade, minute1~minute240, day, week, month
- Private: myorder, myasset
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Dict, Set, List, Optional, Callable, Any
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .models import DataType  # 동일 디렉토리의 models.py에서 DataType import
from .exceptions import SubscriptionError  # 예외 클래스 import

logger = create_component_logger("SubscriptionManager")


class ConnectionType(Enum):
    """웹소켓 연결 타입"""
    PUBLIC = "public"
    PRIVATE = "private"


@dataclass
class SubscriptionIntent:
    """구독 의도 - 클라이언트가 원하는 것"""
    symbols: Set[str]
    data_type: DataType
    callback: Optional[Callable] = None
    client_id: str = ""
    last_used: float = field(default_factory=time.time)
    is_realtime: bool = True


@dataclass
class ActiveSubscription:
    """현재 활성 구독 상태"""
    ticket_id: str
    symbols: Set[str]
    data_types: Set[DataType]
    timestamp: float = field(default_factory=time.time)


class ConnectionState:
    """연결별 상태 관리"""

    def __init__(self, connection_type: ConnectionType):
        self.connection_type = connection_type
        self.active_subscription: Optional[ActiveSubscription] = None
        self.websocket: Optional[Any] = None  # WebSocket 연결 객체
        self.is_connected = False

    def update_subscription(self, ticket_id: str, symbols: Set[str], data_types: Set[DataType]):
        """활성 구독 업데이트"""
        self.active_subscription = ActiveSubscription(
            ticket_id=ticket_id,
            symbols=symbols,
            data_types=data_types
        )
        logger.info(f"{self.connection_type.value} 구독 업데이트: {len(symbols)}개 심볼, {len(data_types)}개 타입")

    def clear_subscription(self):
        """구독 클리어"""
        self.active_subscription = None
        logger.info(f"{self.connection_type.value} 구독 클리어")


class SubscriptionOptimizer:
    """구독 요청 지능적 최적화 엔진"""

    def __init__(self):
        self.logger = create_component_logger("SubscriptionOptimizer")

    def optimize_realtime_request(self,
                                  current_intents: Dict[str, SubscriptionIntent],
                                  connection_state: ConnectionState) -> Optional[List[Dict[str, Any]]]:
        """
        실시간 구독 요청 최적화

        Returns:
            최적화된 웹소켓 메시지 (없으면 None)
        """
        if not current_intents:
            return None

        # 모든 활성 의도 통합
        all_symbols = set()
        all_data_types = set()

        for intent in current_intents.values():
            if intent.is_realtime:
                all_symbols.update(intent.symbols)
                all_data_types.add(intent.data_type)

        if not all_symbols:
            return None

        # 하나의 통합 메시지 생성
        ticket_id = f"unified_{connection_state.connection_type.value}_{int(time.time())}"

        message: List[Dict[str, Any]] = [
            {"ticket": ticket_id}
        ]

        # 데이터 타입별로 구독 추가
        for data_type in all_data_types:
            type_symbols = []
            for intent in current_intents.values():
                if intent.is_realtime and intent.data_type == data_type:
                    type_symbols.extend(intent.symbols)

            if type_symbols:
                message.append({
                    "type": data_type.value,
                    "codes": list(set(type_symbols))  # 중복 제거
                    # is_only_snapshot 없음 → 실시간
                })

        message.append({"format": "DEFAULT"})

        # 상태 업데이트
        connection_state.update_subscription(ticket_id, all_symbols, all_data_types)

        self.logger.info(f"실시간 구독 최적화 완료: {len(all_symbols)}개 심볼, {len(all_data_types)}개 타입")
        return message

    def optimize_snapshot_request(self,
                                  snapshot_symbols: Set[str],
                                  data_type: DataType,
                                  current_realtime: Set[str],
                                  connection_state: ConnectionState) -> tuple:
        """
        스냅샷 요청 최적화

        Returns:
            (snapshot_message, restore_message)
        """
        overlap_symbols = snapshot_symbols & current_realtime
        snapshot_only_symbols = snapshot_symbols - current_realtime

        # 스냅샷 메시지 생성
        ticket_id = f"snapshot_{connection_state.connection_type.value}_{int(time.time())}"

        snapshot_message: List[Dict[str, Any]] = [
            {"ticket": ticket_id}
        ]

        # 겹치는 부분: 기본값으로 (실시간 유지)
        if overlap_symbols:
            snapshot_message.append({
                "type": data_type.value,
                "codes": list(overlap_symbols)
                # is_only_snapshot 없음 → 실시간 유지
            })

        # 겹치지 않는 부분: 스냅샷만
        if snapshot_only_symbols:
            snapshot_message.append({
                "type": data_type.value,
                "codes": list(snapshot_only_symbols),
                "isOnlySnapshot": True  # 1회성
            })

        snapshot_message.append({"format": "DEFAULT"})

        # 복원 메시지는 나중에 필요할 때 생성
        restore_message = None

        self.logger.info(f"스냅샷 최적화: 겹침 {len(overlap_symbols)}개, 독립 {len(snapshot_only_symbols)}개")
        return snapshot_message, restore_message


class AutoLifecycleManager:
    """구독 자동 생명주기 관리"""

    def __init__(self, cleanup_interval: int = 30):
        self.cleanup_interval = cleanup_interval  # 초
        self.usage_tracker: Dict[str, float] = {}
        self.performance_tracker: Dict[str, Dict[str, Any]] = {
            "public": {"last_message_time": 0, "message_count": 0, "reconnect_count": 0},
            "private": {"last_message_time": 0, "message_count": 0, "reconnect_count": 0}
        }
        self.is_running = False
        self.logger = create_component_logger("AutoLifecycleManager")

    async def start_background_cleanup(self, subscription_manager):
        """백그라운드 정리 작업 시작 (비동기 태스크로 실행)"""
        self.is_running = True
        self.logger.info(f"자동 정리 시작: {self.cleanup_interval}초 간격")

        # 🚨 백그라운드 태스크로 실행 (메인 스레드 블록킹 방지)
        async def cleanup_loop():
            while self.is_running:
                await asyncio.sleep(5)  # 5초마다 체크
                await self._cleanup_unused_subscriptions(subscription_manager)
                await self._monitor_performance(subscription_manager)

        # 백그라운드 태스크로 시작하고 즉시 반환
        asyncio.create_task(cleanup_loop())
        self.logger.debug("백그라운드 정리 태스크 시작됨")

    def stop_background_cleanup(self):
        """백그라운드 정리 작업 중단"""
        self.is_running = False
        self.logger.info("자동 정리 중단")

    def mark_data_received(self, symbol: str, data_type: DataType):
        """데이터 수신시 자동 호출 - 사용중임을 표시"""
        key = f"{symbol}:{data_type.value}"
        self.usage_tracker[key] = time.time()

        # 성능 추적 업데이트
        connection_type = "private" if data_type.is_private() else "public"
        self.performance_tracker[connection_type]["last_message_time"] = time.time()
        self.performance_tracker[connection_type]["message_count"] += 1

    async def _cleanup_unused_subscriptions(self, subscription_manager):
        """미사용 구독 정리"""
        now = time.time()
        unused_keys = [
            key for key, last_time in self.usage_tracker.items()
            if now - last_time > self.cleanup_interval
        ]

        if unused_keys:
            self.logger.info(f"{len(unused_keys)}개 미사용 구독 정리 중...")

            for key in unused_keys:
                symbol, data_type_str = key.split(':')
                data_type = DataType(data_type_str)

                # subscription_manager에서 제거
                await subscription_manager._remove_from_subscription(symbol, data_type)
                del self.usage_tracker[key]

    async def _monitor_performance(self, subscription_manager):
        """성능 모니터링 및 자동 재연결"""
        now = time.time()

        for conn_type_str, stats in self.performance_tracker.items():
            last_msg_time = stats["last_message_time"]

            # 3초 이상 메시지가 없으면 성능 문제로 간주
            if last_msg_time > 0 and (now - last_msg_time) > 3:
                self.logger.warning(f"{conn_type_str} 연결에서 {now - last_msg_time:.1f}초간 메시지 없음")

                # 재연결 시도 (하루에 최대 10회)
                if stats["reconnect_count"] < 10:
                    await subscription_manager.force_reconnect(conn_type_str)
                    stats["reconnect_count"] += 1
                    stats["last_message_time"] = now  # 재설정

            # 하루마다 재연결 카운터 리셋
            if now % (24 * 3600) < 60:  # 자정 근처
                stats["reconnect_count"] = 0


class SubscriptionDebugger:
    """구독 상태 실시간 모니터링"""

    def __init__(self, subscription_manager):
        self.subscription_manager = subscription_manager
        self.logger = create_component_logger("SubscriptionDebugger")

    def get_current_state(self) -> dict:
        """현재 구독 상태 전체 조회"""
        public_state = self.subscription_manager.public_state
        private_state = self.subscription_manager.private_state

        state = {
            "timestamp": time.time(),
            "public_connection": {
                "connected": public_state.is_connected,
                "active_subscription": None,
                "websocket_status": "connected" if public_state.websocket else "disconnected"
            },
            "private_connection": {
                "connected": private_state.is_connected,
                "active_subscription": None,
                "websocket_status": "connected" if private_state.websocket else "disconnected"
            },
            "realtime_intents": len(self.subscription_manager.realtime_intents),
            "pending_snapshots": len(self.subscription_manager.snapshot_requests),
            "lifecycle_usage_count": len(self.subscription_manager.lifecycle_manager.usage_tracker)
        }

        # 활성 구독 정보 추가
        if public_state.active_subscription:
            sub = public_state.active_subscription
            state["public_connection"]["active_subscription"] = {
                "ticket_id": sub.ticket_id,
                "symbols": list(sub.symbols),
                "data_types": [dt.value for dt in sub.data_types],
                "timestamp": sub.timestamp
            }

        if private_state.active_subscription:
            sub = private_state.active_subscription
            state["private_connection"]["active_subscription"] = {
                "ticket_id": sub.ticket_id,
                "symbols": list(sub.symbols),
                "data_types": [dt.value for dt in sub.data_types],
                "timestamp": sub.timestamp
            }

        return state

    def print_state_summary(self):
        """상태 요약 출력"""
        state = self.get_current_state()

        print("\n" + "=" * 50)
        print("📊 SubscriptionManager v4.0 상태")
        print("=" * 50)

        # Public 연결
        pub = state["public_connection"]
        print(f"🌐 Public: {'✅' if pub['connected'] else '❌'} "
              f"({'구독중' if pub['active_subscription'] else '대기중'})")
        if pub['active_subscription']:
            sub = pub['active_subscription']
            print(f"   📡 {len(sub['symbols'])}개 심볼, {len(sub['data_types'])}개 타입")

        # Private 연결
        priv = state["private_connection"]
        print(f"🔒 Private: {'✅' if priv['connected'] else '❌'} "
              f"({'구독중' if priv['active_subscription'] else '대기중'})")
        if priv['active_subscription']:
            sub = priv['active_subscription']
            print(f"   📡 {len(sub['symbols'])}개 심볼, {len(sub['data_types'])}개 타입")

        # 전체 통계
        print(f"📈 실시간 의도: {state['realtime_intents']}개")
        print(f"📷 대기중 스냅샷: {state['pending_snapshots']}개")
        print(f"🔄 사용량 추적: {state['lifecycle_usage_count']}개")
        print("=" * 50)


class SubscriptionManager:
    """
    SubscriptionManager v4.0

    혁신적 단순화:
    - 연결별 단일 활성 구독
    - 지능적 최적화 엔진
    - 자동 생명주기 관리
    - 극단적 클라이언트 단순성
    """

    def __init__(self, cleanup_interval: int = 30):
        self.logger = create_component_logger("SubscriptionManager")

        # 연결 상태 관리
        self.public_state = ConnectionState(ConnectionType.PUBLIC)
        self.private_state = ConnectionState(ConnectionType.PRIVATE)

        # 구독 의도 추적
        self.realtime_intents: Dict[str, SubscriptionIntent] = {}
        self.snapshot_requests: Dict[str, asyncio.Future] = {}

        # 핵심 엔진들
        self.optimizer = SubscriptionOptimizer()
        self.lifecycle_manager = AutoLifecycleManager(cleanup_interval)
        self.debugger = SubscriptionDebugger(self)

        self.logger.info("SubscriptionManager v4.0 초기화 완료")

    # ==========================================
    # 클라이언트 인터페이스 (극단적 단순화)
    # ==========================================

    async def request_realtime_data(self,
                                    symbols: List[str],
                                    data_type: str,
                                    callback: Callable,
                                    client_id: str = "",
                                    connection_type: str = "auto") -> bool:
        """
        실시간 데이터 요청

        Args:
            symbols: 구독할 심볼 목록
            data_type: 데이터 타입 (ticker, orderbook, trade, minute1~month, myorder, myasset)
            callback: 데이터 수신 콜백
            client_id: 클라이언트 식별자
            connection_type: "public", "private", "auto" (자동 판단)

        Returns:
            성공 여부
        """
        try:
            dt = DataType(data_type)

            # 연결 타입 자동 판단
            if connection_type == "auto":
                conn_type = ConnectionType.PRIVATE if dt.is_private() else ConnectionType.PUBLIC
            else:
                conn_type = ConnectionType(connection_type)

            # 데이터 타입과 연결 타입 호환성 검증
            if dt.is_private() and conn_type == ConnectionType.PUBLIC:
                raise ValueError(f"Private 데이터 타입 {data_type}은 Private 연결에서만 사용 가능")
            elif dt.is_public() and conn_type == ConnectionType.PRIVATE:
                self.logger.warning(f"Public 데이터 타입 {data_type}을 Private 연결에서 요청 (권장하지 않음)")

            # 구독 의도 등록
            intent_key = f"{client_id}:{data_type}"
            self.realtime_intents[intent_key] = SubscriptionIntent(
                symbols=set(symbols),
                data_type=dt,
                callback=callback,
                client_id=client_id,
                is_realtime=True
            )

            # 구독 최적화 및 전송
            await self._rebuild_realtime_subscription(conn_type)

            self.logger.info(f"실시간 구독 요청 완료: {symbols} ({data_type}) -> {conn_type.value}")
            return True

        except Exception as e:
            self.logger.error(f"실시간 구독 요청 실패: {e}")
            return False

    async def request_snapshot_data(self,
                                    symbols: List[str],
                                    data_type: str,
                                    connection_type: str = "auto",
                                    timeout: float = 5.0) -> dict:
        """
        스냅샷 데이터 요청 (즉시 반환)

        Args:
            symbols: 요청할 심볼 목록
            data_type: 데이터 타입
            connection_type: "public", "private", "auto" (자동 판단)
            timeout: 응답 대기 시간 (초)

        Returns:
            수신된 데이터 딕셔너리
        """
        try:
            dt = DataType(data_type)

            # 연결 타입 자동 판단
            if connection_type == "auto":
                conn_type = ConnectionType.PRIVATE if dt.is_private() else ConnectionType.PUBLIC
            else:
                conn_type = ConnectionType(connection_type)

            # 현재 실시간 구독 중인 심볼들 파악
            current_realtime = self._get_current_realtime_symbols(conn_type, dt)

            # 스냅샷 최적화
            snapshot_msg, restore_msg = self.optimizer.optimize_snapshot_request(
                set(symbols), dt, current_realtime, self._get_connection_state(conn_type)
            )

            # 응답 대기 Future 생성
            request_id = f"snapshot_{int(time.time())}"
            future = asyncio.Future()
            self.snapshot_requests[request_id] = future

            # 스냅샷 요청 전송
            await self._send_message(conn_type, snapshot_msg)

            # 응답 대기
            try:
                result = await asyncio.wait_for(future, timeout=timeout)
                self.logger.info(f"스냅샷 요청 완료: {len(symbols)}개 심볼")
                return result
            except asyncio.TimeoutError:
                self.logger.warning(f"스냅샷 요청 타임아웃: {symbols}")
                return {}
            finally:
                # 정리
                self.snapshot_requests.pop(request_id, None)

                # 실시간 구독 복원 (필요한 경우)
                if current_realtime:
                    await self._rebuild_realtime_subscription(conn_type)

        except Exception as e:
            self.logger.error(f"스냅샷 요청 실패: {e}")
            return {}

    async def stop_realtime_data(self,
                                 symbols: List[str],
                                 data_type: str,
                                 client_id: str = "",
                                 connection_type: str = "public") -> bool:
        """
        실시간 데이터 중단

        Args:
            symbols: 중단할 심볼 목록
            data_type: 데이터 타입
            client_id: 클라이언트 식별자
            connection_type: "public" 또는 "private"

        Returns:
            성공 여부
        """
        try:
            conn_type = ConnectionType(connection_type)

            # 구독 의도 제거
            intent_key = f"{client_id}:{data_type}"
            if intent_key in self.realtime_intents:
                del self.realtime_intents[intent_key]

                # 구독 재구성 (빈 구독 시 더미 메시지 전송)
                await self._rebuild_realtime_subscription(conn_type)

                self.logger.info(f"실시간 구독 중단: {symbols} ({data_type})")
                return True
            else:
                self.logger.warning(f"중단할 구독을 찾을 수 없음: {intent_key}")
                return False

        except Exception as e:
            self.logger.error(f"실시간 구독 중단 실패: {e}")
            return False

    async def unsubscribe_all(self, connection_type: str = "public") -> bool:
        """
        모든 구독 해제 (명시적 unsubscribe)

        Args:
            connection_type: "public" 또는 "private"

        Returns:
            성공 여부
        """
        try:
            conn_type = ConnectionType(connection_type)

            # 해당 연결의 모든 의도 제거
            keys_to_remove = []
            for key, intent in self.realtime_intents.items():
                if self._is_relevant_connection(intent, conn_type):
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.realtime_intents[key]

            # 더미 스냅샷으로 안전한 해제
            await self._send_safe_unsubscribe(conn_type)

            # 연결 상태 정리
            connection_state = self._get_connection_state(conn_type)
            connection_state.clear_subscription()

            self.logger.info(f"{conn_type.value} 모든 구독 해제 완료")
            return True

        except Exception as e:
            self.logger.error(f"전체 구독 해제 실패: {e}")
            return False

    async def force_reconnect(self, connection_type: str = "public") -> bool:
        """
        웹소켓 강제 재연결 (성능 저하 시)

        Args:
            connection_type: "public" 또는 "private"

        Returns:
            재연결 성공 여부
        """
        try:
            conn_type = ConnectionType(connection_type)
            connection_state = self._get_connection_state(conn_type)

            self.logger.warning(f"{conn_type.value} 웹소켓 강제 재연결 시작")

            # 현재 구독 상태 백업
            backup_intents = {
                key: intent for key, intent in self.realtime_intents.items()
                if self._is_relevant_connection(intent, conn_type)
            }

            # 웹소켓 연결 해제
            if connection_state.websocket:
                await connection_state.websocket.close()
                connection_state.websocket = None
                connection_state.is_connected = False

            # 잠시 대기
            await asyncio.sleep(1.0)

            # 재연결 시뮬레이션 (실제로는 클라이언트에서 처리)
            # connection_state.is_connected = True  # 실제 재연결 후 설정

            # 구독 복원
            if backup_intents:
                await self._rebuild_realtime_subscription(conn_type)
                self.logger.info(f"{len(backup_intents)}개 구독 복원 완료")

            return True

        except Exception as e:
            self.logger.error(f"강제 재연결 실패: {e}")
            return False

    # ==========================================
    # 내부 최적화 메서드들
    # ==========================================

    async def _rebuild_realtime_subscription(self, connection_type: ConnectionType):
        """실시간 구독 전체 재구성"""
        # 해당 연결의 활성 의도들만 필터링
        relevant_intents = {
            key: intent for key, intent in self.realtime_intents.items()
            if self._is_relevant_connection(intent, connection_type)
        }

        connection_state = self._get_connection_state(connection_type)

        # 최적화된 메시지 생성
        message = self.optimizer.optimize_realtime_request(relevant_intents, connection_state)

        if message:
            await self._send_message(connection_type, message)
        else:
            # ⚠️ 구독할 것이 없으면 더미 스냅샷으로 안전하게 처리
            await self._send_safe_unsubscribe(connection_type)
            connection_state.clear_subscription()

    async def _send_safe_unsubscribe(self, connection_type: ConnectionType):
        """
        안전한 구독 해제 - 빈 메시지 대신 더미 스냅샷 전송

        업비트 웹소켓은 빈 구독 리스트 []를 보내면 에러가 발생하므로,
        더미 스냅샷을 보내서 안전하게 기존 구독을 대체합니다.
        """
        try:
            connection_state = self._get_connection_state(connection_type)

            if not (connection_state.websocket and connection_state.is_connected):
                return

            # 더미 스냅샷 메시지 (기존 구독을 대체)
            dummy_message = [
                {"ticket": f"dummy_{connection_type.value}_{int(time.time())}"},
                {
                    "type": "ticker",
                    "codes": ["KRW-BTC"],  # 안전한 기본 심볼
                    "isOnlySnapshot": True  # 1회성 요청
                },
                {"format": "DEFAULT"}
            ]

            await connection_state.websocket.send(json.dumps(dummy_message))

            self.logger.info(f"{connection_type.value} 안전한 구독 해제 (더미 스냅샷)")

        except Exception as e:
            self.logger.error(f"안전한 구독 해제 실패: {e}")

    async def _monitor_websocket_performance(self, connection_type: ConnectionType) -> bool:
        """
        웹소켓 성능 모니터링

        Returns:
            재연결이 필요한지 여부
        """
        connection_state = self._get_connection_state(connection_type)

        # 성능 지표 체크 (예시)
        performance_issues = [
            not connection_state.is_connected,
            # 추가 성능 지표들...
            # - 응답 지연 시간
            # - 메시지 손실률
            # - 메모리 사용량 등
        ]

        if any(performance_issues):
            self.logger.warning(f"{connection_type.value} 성능 문제 감지")
            return True

        return False

    def _get_current_realtime_symbols(self, connection_type: ConnectionType, data_type: DataType) -> Set[str]:
        """현재 실시간 구독 중인 심볼들 반환"""
        symbols = set()

        for intent in self.realtime_intents.values():
            if (intent.is_realtime
                    and intent.data_type == data_type
                    and self._is_relevant_connection(intent, connection_type)):
                symbols.update(intent.symbols)

        return symbols

    def _is_relevant_connection(self, intent: SubscriptionIntent, connection_type: ConnectionType) -> bool:
        """의도가 해당 연결 타입과 관련있는지 확인"""
        # 데이터 타입에 따라 자동 판단
        if intent.data_type.is_public() and connection_type == ConnectionType.PUBLIC:
            return True
        elif intent.data_type.is_private() and connection_type == ConnectionType.PRIVATE:
            return True
        else:
            return False

    def _get_connection_state(self, connection_type: ConnectionType) -> ConnectionState:
        """연결 타입에 따른 상태 반환"""
        return (self.public_state if connection_type == ConnectionType.PUBLIC
                else self.private_state)

    async def _send_message(self, connection_type: ConnectionType, message: List[Dict[str, Any]]):
        """웹소켓 메시지 전송"""
        connection_state = self._get_connection_state(connection_type)

        if connection_state.websocket is not None and connection_state.is_connected:
            message_json = json.dumps(message)
            await connection_state.websocket.send(message_json)
            self.logger.debug(f"{connection_type.value} 메시지 전송: {len(message)} 항목")
            # 🔍 디버그: 실제 전송 메시지 내용 로깅
            self.logger.debug(f"실제 전송 메시지: {message_json}")
        else:
            self.logger.error(f"{connection_type.value} 연결이 없어 메시지 전송 실패")

    async def _remove_from_subscription(self, symbol: str, data_type: DataType):
        """구독에서 특정 심볼 제거 (생명주기 관리용)"""
        # 해당 심볼을 포함한 의도들 찾아서 제거
        keys_to_remove = []

        for key, intent in self.realtime_intents.items():
            if symbol in intent.symbols and intent.data_type == data_type:
                intent.symbols.discard(symbol)
                if not intent.symbols:  # 빈 집합이 되면 의도 자체 제거
                    keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.realtime_intents[key]

        # 구독 재구성
        await self._rebuild_realtime_subscription(ConnectionType.PUBLIC)
        await self._rebuild_realtime_subscription(ConnectionType.PRIVATE)

        self.logger.info(f"자동 정리: {symbol}:{data_type.value} 제거")

    # ==========================================
    # 생명주기 관리
    # ==========================================

    async def start_background_services(self):
        """백그라운드 서비스 시작"""
        await self.lifecycle_manager.start_background_cleanup(self)
        self.logger.info("백그라운드 서비스 시작 완료")

    def stop_background_services(self):
        """백그라운드 서비스 중단"""
        self.lifecycle_manager.stop_background_cleanup()
        self.logger.info("백그라운드 서비스 중단 완료")

    def on_data_received(self, symbol: str, data_type: str, data: dict):
        """데이터 수신시 호출 - 사용량 추적 + 스냅샷 Future 완료"""
        try:
            dt = DataType(data_type)
            self.lifecycle_manager.mark_data_received(symbol, dt)

            # 🎯 스냅샷 Future 완료 처리
            self._complete_snapshot_futures(symbol, data_type, data)

            # 해당 구독 의도의 콜백 호출
            for intent in self.realtime_intents.values():
                if (symbol in intent.symbols
                        and intent.data_type == dt
                        and intent.callback):
                    intent.callback(symbol, data_type, data)
                    intent.last_used = time.time()

        except Exception as e:
            self.logger.error(f"데이터 수신 처리 실패: {e}")
            # 추가 디버깅 정보
            self.logger.error(f"  심볼: {symbol}, 데이터타입: {data_type}")
            self.logger.error(f"  데이터 샘플: {str(data)[:100]}...")
            import traceback
            self.logger.error(f"  스택 트레이스: {traceback.format_exc()}")

    def _complete_snapshot_futures(self, symbol: str, data_type: str, data: dict):
        """스냅샷 요청 Future들을 완료 처리"""
        # 완료할 Future들을 찾기
        completed_requests = []

        for request_id, future in self.snapshot_requests.items():
            if not future.done():
                # 스냅샷 데이터를 Future에 설정
                try:
                    result = {symbol: {data_type: data}}
                    future.set_result(result)
                    completed_requests.append(request_id)
                    self.logger.debug(f"스냅샷 Future 완료: {request_id} - {symbol}:{data_type}")
                except Exception as e:
                    self.logger.error(f"스냅샷 Future 완료 실패: {e}")

        # 완료된 요청들 정리
        for request_id in completed_requests:
            self.snapshot_requests.pop(request_id, None)

    # ==========================================
    # 디버깅 및 모니터링
    # ==========================================

    def get_state(self) -> dict:
        """현재 상태 조회"""
        return self.debugger.get_current_state()

    def print_state(self):
        """상태 출력"""
        self.debugger.print_state_summary()

    def set_websocket_connections(self, public_ws=None, private_ws=None):
        """웹소켓 연결 설정 (테스트/초기화용)"""
        if public_ws:
            self.public_state.websocket = public_ws
            self.public_state.is_connected = True

        if private_ws:
            self.private_state.websocket = private_ws
            self.private_state.is_connected = True

        self.logger.info("웹소켓 연결 설정 완료")

    # ==========================================
    # 기존 클라이언트 호환성 메서드들
    # ==========================================

    async def subscribe(self, data_type: str, symbols: List[str],
                        callback: Optional[Callable] = None,
                        client_id: str = "default") -> str:
        """기존 클라이언트 호환용 subscribe"""
        success = await self.request_realtime_data(
            symbols=symbols,
            data_type=data_type,
            callback=callback or self._default_callback,
            client_id=client_id
        )

        if success:
            return f"{client_id}:{data_type}"  # subscription_id로 사용
        else:
            raise SubscriptionError(f"구독 실패: {data_type}", data_type)

    async def unsubscribe(self, subscription_id: str) -> None:
        """기존 클라이언트 호환용 unsubscribe"""
        try:
            # subscription_id에서 client_id와 data_type 추출
            if ":" in subscription_id:
                client_id, data_type = subscription_id.split(":", 1)

                # 해당 구독 중단
                await self.stop_realtime_data(
                    symbols=[],  # 모든 심볼
                    data_type=data_type,
                    client_id=client_id
                )
            else:
                self.logger.debug(f"스냅샷 구독 ID는 실시간 해제 대상이 아님: {subscription_id}")

        except Exception as e:
            self.logger.error(f"구독 해제 실패: {e}")

    def _default_callback(self, symbol: str, data_type: str, data: dict):
        """기본 콜백 (로깅용)"""
        self.logger.debug(f"데이터 수신: {symbol} {data_type}")

    async def get_subscription_count(self) -> Dict[str, int]:
        """현재 구독 수 반환"""
        public_count = len([
            intent for intent in self.realtime_intents.values()
            if intent.data_type.is_public()
        ])

        private_count = len([
            intent for intent in self.realtime_intents.values()
            if intent.data_type.is_private()
        ])

        return {
            "public": public_count,
            "private": private_count,
            "total": public_count + private_count
        }

    async def health_check(self) -> Dict[str, Any]:
        """시스템 건강성 체크"""
        state = self.get_state()

        health = {
            "overall_status": "healthy",
            "connections": {
                "public": "connected" if state["public_connection"]["connected"] else "disconnected",
                "private": "connected" if state["private_connection"]["connected"] else "disconnected"
            },
            "subscriptions": await self.get_subscription_count(),
            "performance": {
                "public": self.lifecycle_manager.performance_tracker["public"],
                "private": self.lifecycle_manager.performance_tracker["private"]
            },
            "timestamp": time.time()
        }

        # 전체 상태 판정
        if not any(state[conn]["connected"] for conn in ["public_connection", "private_connection"]):
            health["overall_status"] = "critical"
        elif health["subscriptions"]["total"] == 0:
            health["overall_status"] = "idle"

        return health


# ==========================================
# 사용 예시 및 테스트 도우미
# ==========================================

async def example_usage():
    """SubscriptionManager v4.0 사용 예시"""

    # 초기화
    manager = SubscriptionManager(cleanup_interval=30)

    # 백그라운드 서비스 시작
    await manager.start_background_services()

    def my_callback(symbol: str, data_type: str, data: dict):
        print(f"📈 {symbol} {data_type}: {data.get('trade_price', 'N/A')}")

    try:
        # 실시간 데이터 요청
        await manager.request_realtime_data(
            symbols=["KRW-BTC", "KRW-ETH"],
            data_type="ticker",
            callback=my_callback,
            client_id="my_client"
        )

        # 스냅샷 데이터 요청
        snapshot_data = await manager.request_snapshot_data(
            symbols=["KRW-ADA", "KRW-DOT"],
            data_type="ticker"
        )
        print(f"스냅샷 수신: {len(snapshot_data)}개")

        # 상태 확인
        manager.print_state()

        # 잠시 대기
        await asyncio.sleep(60)

        # 실시간 중단
        await manager.stop_realtime_data(
            symbols=["KRW-BTC", "KRW-ETH"],
            data_type="ticker",
            client_id="my_client"
        )

    finally:
        # 정리
        manager.stop_background_services()


if __name__ == "__main__":
    print("🚀 SubscriptionManager v4.0")
    print("=" * 40)
    print("혁신적 단순화 설계")
    print("- 연결별 단일 활성 구독")
    print("- 지능적 최적화 엔진")
    print("- 자동 생명주기 관리")
    print("=" * 40)

    # 예시 실행
    # asyncio.run(example_usage())
