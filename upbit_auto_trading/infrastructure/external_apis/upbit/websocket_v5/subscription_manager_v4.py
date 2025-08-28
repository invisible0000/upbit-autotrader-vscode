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

logger = create_component_logger("SubscriptionManagerV4")


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
        self.is_running = False
        self.logger = create_component_logger("AutoLifecycleManager")

    async def start_background_cleanup(self, subscription_manager):
        """백그라운드 정리 작업 시작"""
        self.is_running = True
        self.logger.info(f"자동 정리 시작: {self.cleanup_interval}초 간격")

        while self.is_running:
            await asyncio.sleep(5)  # 5초마다 체크
            await self._cleanup_unused_subscriptions(subscription_manager)

    def stop_background_cleanup(self):
        """백그라운드 정리 작업 중단"""
        self.is_running = False
        self.logger.info("자동 정리 중단")

    def mark_data_received(self, symbol: str, data_type: DataType):
        """데이터 수신시 자동 호출 - 사용중임을 표시"""
        key = f"{symbol}:{data_type.value}"
        self.usage_tracker[key] = time.time()

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


class SubscriptionManagerV4:
    """
    SubscriptionManager v4.0

    혁신적 단순화:
    - 연결별 단일 활성 구독
    - 지능적 최적화 엔진
    - 자동 생명주기 관리
    - 극단적 클라이언트 단순성
    """

    def __init__(self, cleanup_interval: int = 30):
        self.logger = create_component_logger("SubscriptionManagerV4")

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

                # 구독 재구성
                await self._rebuild_realtime_subscription(conn_type)

                self.logger.info(f"실시간 구독 중단: {symbols} ({data_type})")
                return True
            else:
                self.logger.warning(f"중단할 구독을 찾을 수 없음: {intent_key}")
                return False

        except Exception as e:
            self.logger.error(f"실시간 구독 중단 실패: {e}")
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
            # 구독할 것이 없으면 연결 정리
            connection_state.clear_subscription()

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
            await connection_state.websocket.send(json.dumps(message))
            self.logger.debug(f"{connection_type.value} 메시지 전송: {len(message)} 항목")
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
        """데이터 수신시 호출 - 사용량 추적"""
        try:
            dt = DataType(data_type)
            self.lifecycle_manager.mark_data_received(symbol, dt)

            # 해당 구독 의도의 콜백 호출
            for intent in self.realtime_intents.values():
                if (symbol in intent.symbols
                        and intent.data_type == dt
                        and intent.callback):
                    intent.callback(symbol, data_type, data)
                    intent.last_used = time.time()

        except Exception as e:
            self.logger.error(f"데이터 수신 처리 실패: {e}")

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
# 사용 예시 및 테스트 도우미
# ==========================================

async def example_usage():
    """SubscriptionManager v4.0 사용 예시"""

    # 초기화
    manager = SubscriptionManagerV4(cleanup_interval=30)

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
