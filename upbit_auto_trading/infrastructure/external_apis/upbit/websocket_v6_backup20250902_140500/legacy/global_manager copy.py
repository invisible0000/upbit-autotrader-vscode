"""
글로벌 웹소켓 매니저
==================

WebSocket v6의 중앙 관리자 - 모든 컴포넌트를 조율하는 싱글톤

핵심 역할:
- v5 물리 연결 재사용 및 관리
- 구독 상태 통합 관리
- 데이터 라우팅 제어
- 전역 Rate Limiter 연동
- 복구 정책 관리

설계 원칙:
- 싱글톤 패턴으로 전역 상태 관리
- v5와 v6 간 호환성 유지
- 컴포넌트 격리를 통한 안전성
- 비동기 안전 보장
"""

import asyncio
import weakref
from typing import Dict, Optional, Set, Any, Callable
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger
# TODO: Rate Limiter 연동 추가 예정
# from upbit_auto_trading.infrastructure.rate_limiter import get_global_rate_limiter, gate_websocket

from .types import (
    BaseWebSocketEvent,
    ComponentSubscription,
    ConnectionMetrics,
    DataType,
    GlobalManagerState,
    DataStreamEvent
)
from .exceptions import (
    SubscriptionError,
    RecoveryError,
    ConfigurationError
)
from .config import create_development_config
from .subscription_state_manager import SubscriptionStateManager
from .data_routing_engine import DataRoutingEngine


@dataclass
class ConnectionState:
    """개별 연결 상태 추적"""
    is_connected: bool = False
    last_ping: Optional[float] = None
    reconnect_count: int = 0
    error_count: int = 0
    subscription_count: int = 0


class GlobalWebSocketManager:
    """
    WebSocket v6 중앙 관리자 (싱글톤)

    모든 v6 컴포넌트의 생명주기와 상태를 관리하며,
    v5 물리 연결을 재사용하여 효율적인 데이터 스트리밍 제공
    """

    _instance: Optional['GlobalWebSocketManager'] = None
    _lock = asyncio.Lock()

    def __new__(cls) -> 'GlobalWebSocketManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 싱글톤 중복 초기화 방지
        if hasattr(self, '_initialized'):
            return

        self._logger = create_component_logger("GlobalWebSocketManager")
        self._config = create_development_config()

        # 핵심 컴포넌트
        self._subscription_manager = SubscriptionStateManager()
        self._routing_engine = DataRoutingEngine()

        # v5 연결 관리
        self._public_client = None  # UpbitWebSocketPublicV5 인스턴스
        self._private_client = None  # UpbitWebSocketPrivateV5 인스턴스

        # 연결 상태 추적
        self._connection_states: Dict[str, ConnectionState] = {
            'public': ConnectionState(),
            'private': ConnectionState()
        }

        # 전역 상태
        self._state = GlobalManagerState.INITIALIZING
        self._startup_time: Optional[float] = None
        self._shutdown_requested = False

        # 컴포넌트 참조 (WeakRef로 메모리 누수 방지)
        self._registered_components: Set[weakref.ReferenceType] = set()

        # 이벤트 루프 및 작업 관리
        self._background_tasks: Set[asyncio.Task] = set()
        self._event_handlers: Dict[type, Set[Callable]] = {}

        self._initialized = True
        self._logger.info("GlobalWebSocketManager 초기화 완료")

    @classmethod
    async def get_instance(cls) -> 'GlobalWebSocketManager':
        """스레드 안전한 싱글톤 인스턴스 획득"""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
                await cls._instance._initialize_async()
            return cls._instance

    async def _initialize_async(self):
        """비동기 초기화 작업"""
        try:
            self._logger.info("비동기 초기화 시작")

            # 백그라운드 작업 시작
            self._background_tasks.add(
                asyncio.create_task(self._health_monitor_loop())
            )
            self._background_tasks.add(
                asyncio.create_task(self._metrics_collection_loop())
            )

            self._state = GlobalManagerState.IDLE
            self._startup_time = asyncio.get_event_loop().time()

            self._logger.info("GlobalWebSocketManager 비동기 초기화 완료")

        except Exception as e:
            self._logger.error(f"비동기 초기화 실패: {e}")
            self._state = GlobalManagerState.ERROR
            raise RecoveryError(f"매니저 초기화 실패: {e}")

    async def register_component(self, component_id: str, weak_ref: weakref.ReferenceType):
        """컴포넌트 등록 및 생명주기 관리"""
        async with self._lock:
            try:
                if weak_ref in self._registered_components:
                    self._logger.warning(f"컴포넌트 {component_id} 이미 등록됨")
                    return

                self._registered_components.add(weak_ref)
                self._logger.info(f"컴포넌트 등록: {component_id}")

                # 컴포넌트 정리 콜백 등록
                def cleanup_callback(ref):
                    asyncio.create_task(self._cleanup_component(component_id, ref))

                weak_ref.__callback__ = cleanup_callback

            except Exception as e:
                self._logger.error(f"컴포넌트 등록 실패: {e}")
                raise ConfigurationError(f"컴포넌트 등록 오류: {e}")

    async def _cleanup_component(self, component_id: str, ref: weakref.ReferenceType):
        """컴포넌트 정리"""
        try:
            if ref in self._registered_components:
                self._registered_components.remove(ref)
                self._logger.info(f"컴포넌트 정리 완료: {component_id}")
        except Exception as e:
            self._logger.error(f"컴포넌트 정리 실패: {e}")

    async def initialize_v5_connections(self, public_client=None, private_client=None):
        """v5 클라이언트 연결 초기화"""
        try:
            self._logger.info("v5 연결 초기화 시작")

            if public_client:
                self._public_client = public_client
                self._connection_states['public'].is_connected = True
                self._logger.info("Public v5 클라이언트 연결됨")

            if private_client:
                self._private_client = private_client
                self._connection_states['private'].is_connected = True
                self._logger.info("Private v5 클라이언트 연결됨")

            # 데이터 핸들러 설정
            if self._public_client:
                await self._setup_v5_data_handler(self._public_client, 'public')
            if self._private_client:
                await self._setup_v5_data_handler(self._private_client, 'private')

            self._state = GlobalManagerState.ACTIVE
            self._logger.info("v5 연결 초기화 완료")

        except Exception as e:
            self._logger.error(f"v5 연결 초기화 실패: {e}")
            self._state = GlobalManagerState.ERROR
            raise ConnectionError(f"v5 연결 실패: {e}")

    async def _setup_v5_data_handler(self, client, connection_type: str):
        """v5 클라이언트 데이터 핸들러 설정"""
        try:
            # v5 클라이언트의 콜백을 v6 라우팅으로 연결
            original_callback = getattr(client, '_on_message', None)

            async def v6_wrapper(message):
                try:
                    # v5 메시지를 v6 이벤트로 변환
                    v6_event = await self._convert_v5_to_v6_event(message, connection_type)
                    if v6_event:
                        await self._routing_engine.distribute_event(v6_event)

                    # 원본 콜백도 호출 (v5 호환성 유지)
                    if original_callback:
                        await original_callback(message)

                except Exception as e:
                    self._logger.error(f"v5→v6 변환 오류: {e}")

            # v5 클라이언트에 래퍼 콜백 설정
            if hasattr(client, 'set_message_callback'):
                client.set_message_callback(v6_wrapper)
            else:
                client._on_message = v6_wrapper

        except Exception as e:
            self._logger.error(f"v5 핸들러 설정 실패: {e}")
            raise ConfigurationError(f"핸들러 설정 오류: {e}")

    async def _convert_v5_to_v6_event(self, v5_message: Dict[str, Any], source: str) -> Optional[BaseWebSocketEvent]:
        """v5 메시지를 v6 이벤트로 변환"""
        try:
            # v5 메시지 파싱 로직 (상세 구현은 향후 Phase 2에서)
            # 현재는 기본적인 변환만 수행

            if not isinstance(v5_message, dict):
                return None

            # 메시지 타입 감지
            msg_type = v5_message.get('type', 'unknown')
            symbol = v5_message.get('code', 'UNKNOWN')

            # 기본 이벤트 생성 (임시)
            from .types import DataStreamEvent

            event = DataStreamEvent(
                data_type=DataType.TICKER,
                symbol=symbol,
                data=v5_message,
                source_connection=source,
                sequence_id=int(asyncio.get_event_loop().time() * 1000000)
            )

            return event

        except Exception as e:
            self._logger.error(f"v5→v6 변환 실패: {e}")
            return None

    async def add_subscription(self, component_id: str, subscription: ComponentSubscription):
        """구독 추가 (Rate Limiter 연동)"""
        try:
            # 전역 Rate Limiter 체크
            rate_limiter = get_global_rate_limiter()
            gate_result = await gate_websocket(
                rate_limiter,
                endpoint="subscribe",
                weight=len(subscription.subscriptions)
            )

            if not gate_result.allowed:
                raise SubscriptionError(
                    f"Rate limit 초과: {gate_result.retry_after}초 후 재시도"
                )

            # 구독 상태 관리자에 등록
            await self._subscription_manager.register_component(component_id, subscription)

            # 데이터 라우팅 엔진에 콜백 등록
            await self._routing_engine.register_callback(
                component_id,
                subscription.callback,
                subscription.subscriptions
            )

            # v5 클라이언트에 실제 구독 요청
            await self._apply_v5_subscriptions()

            self._logger.info(f"구독 추가 완료: {component_id}, {len(subscription.subscriptions)}개 항목")

        except Exception as e:
            self._logger.error(f"구독 추가 실패: {e}")
            raise SubscriptionError(f"구독 실패: {e}")

    async def remove_subscription(self, component_id: str):
        """구독 제거"""
        try:
            # 상태 관리자에서 제거
            await self._subscription_manager.unregister_component(component_id)

            # 라우팅 엔진에서 제거
            await self._routing_engine.unregister_callback(component_id)

            # v5 구독 업데이트
            await self._apply_v5_subscriptions()

            self._logger.info(f"구독 제거 완료: {component_id}")

        except Exception as e:
            self._logger.error(f"구독 제거 실패: {e}")
            raise SubscriptionError(f"구독 제거 오류: {e}")

    async def _apply_v5_subscriptions(self):
        """통합된 구독을 v5 클라이언트에 적용"""
        try:
            # 통합 구독 목록 가져오기
            consolidated = self._subscription_manager.get_consolidated_subscriptions()

            public_subs = []
            private_subs = []

            for spec in consolidated:
                if spec.requires_auth:
                    private_subs.append(spec)
                else:
                    public_subs.append(spec)

            # Public 구독 적용
            if self._public_client and public_subs:
                await self._apply_subscriptions_to_client(
                    self._public_client, public_subs, 'public'
                )

            # Private 구독 적용
            if self._private_client and private_subs:
                await self._apply_subscriptions_to_client(
                    self._private_client, private_subs, 'private'
                )

        except Exception as e:
            self._logger.error(f"v5 구독 적용 실패: {e}")
            raise SubscriptionError(f"구독 적용 오류: {e}")

    async def _apply_subscriptions_to_client(self, client, subscriptions, connection_type: str):
        """개별 v5 클라이언트에 구독 적용"""
        try:
            # v5 클라이언트별 구독 형식으로 변환
            v5_format = []
            for spec in subscriptions:
                v5_item = {
                    'ticket': f"v6_{spec.data_type.value}_{spec.symbol}",
                    'type': spec.data_type.value,
                    'codes': [spec.symbol] if spec.symbol != "*" else None,
                    'isOnlySnapshot': False,
                    'isOnlyRealtime': True
                }
                v5_format.append(v5_item)

            # v5 클라이언트 구독 메서드 호출
            if hasattr(client, 'subscribe_multiple'):
                await client.subscribe_multiple(v5_format)
            elif hasattr(client, 'subscribe'):
                for item in v5_format:
                    await client.subscribe(item)
            else:
                self._logger.warning(f"{connection_type} 클라이언트에 구독 메서드 없음")

            self._connection_states[connection_type].subscription_count = len(subscriptions)
            self._logger.info(f"{connection_type} 구독 적용 완료: {len(subscriptions)}개")

        except Exception as e:
            self._logger.error(f"{connection_type} 구독 적용 실패: {e}")
            raise

    async def get_metrics(self) -> ConnectionMetrics:
        """전체 연결 메트릭스 수집"""
        try:
            # 개별 연결 상태 수집
            public_state = self._connection_states.get('public', ConnectionState())
            private_state = self._connection_states.get('private', ConnectionState())

            # 라우팅 엔진 메트릭스
            routing_metrics = await self._routing_engine.get_performance_metrics()

            metrics = ConnectionMetrics(
                connected_clients=sum(1 for state in self._connection_states.values() if state.is_connected),
                total_subscriptions=sum(state.subscription_count for state in self._connection_states.values()),
                messages_per_second=routing_metrics.get('messages_per_second', 0.0),
                average_latency_ms=routing_metrics.get('average_latency_ms', 0.0),
                error_rate=routing_metrics.get('error_rate', 0.0),
                uptime_seconds=asyncio.get_event_loop().time() - (self._startup_time or 0)
            )

            return metrics

        except Exception as e:
            self._logger.error(f"메트릭스 수집 실패: {e}")
            # 기본값 반환
            return ConnectionMetrics(
                connected_clients=0,
                total_subscriptions=0,
                messages_per_second=0.0,
                average_latency_ms=0.0,
                error_rate=0.0,
                uptime_seconds=0.0
            )

    async def _health_monitor_loop(self):
        """백그라운드 헬스 모니터링"""
        try:
            while not self._shutdown_requested:
                await asyncio.sleep(self._config.health_check_interval)

                # 연결 상태 체크
                for conn_type, state in self._connection_states.items():
                    if state.is_connected:
                        # 핑 체크 (실제 구현은 v5 클라이언트 API에 따라)
                        current_time = asyncio.get_event_loop().time()
                        if state.last_ping and (current_time - state.last_ping) > 30:
                            self._logger.warning(f"{conn_type} 연결 응답 지연")

                # 컴포넌트 정리 (약한 참조 정리)
                dead_refs = [ref for ref in self._registered_components if ref() is None]
                for ref in dead_refs:
                    self._registered_components.remove(ref)

        except asyncio.CancelledError:
            self._logger.info("헬스 모니터 종료")
        except Exception as e:
            self._logger.error(f"헬스 모니터 오류: {e}")

    async def _metrics_collection_loop(self):
        """백그라운드 메트릭스 수집"""
        try:
            while not self._shutdown_requested:
                await asyncio.sleep(60)  # 1분마다 수집

                metrics = await self.get_metrics()
                self._logger.info(
                    f"메트릭스: 연결={metrics.connected_clients}, "
                    f"구독={metrics.total_subscriptions}, "
                    f"MPS={metrics.messages_per_second:.1f}, "
                    f"지연={metrics.average_latency_ms:.1f}ms"
                )

        except asyncio.CancelledError:
            self._logger.info("메트릭스 수집 종료")
        except Exception as e:
            self._logger.error(f"메트릭스 수집 오류: {e}")

    async def shutdown(self):
        """우아한 종료"""
        try:
            self._logger.info("GlobalWebSocketManager 종료 시작")
            self._shutdown_requested = True
            self._state = GlobalManagerState.SHUTTING_DOWN

            # 백그라운드 작업 취소
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()

            # 모든 작업 완료 대기
            if self._background_tasks:
                await asyncio.gather(*self._background_tasks, return_exceptions=True)

            # 컴포넌트 정리
            await self._subscription_manager.cleanup()
            await self._routing_engine.cleanup()

            # v5 연결 정리 (필요시)
            self._public_client = None
            self._private_client = None

            self._state = GlobalManagerState.STOPPED
            self._logger.info("GlobalWebSocketManager 종료 완료")

        except Exception as e:
            self._logger.error(f"종료 중 오류: {e}")
            self._state = GlobalManagerState.ERROR

    @property
    def state(self) -> GlobalManagerState:
        """현재 매니저 상태"""
        return self._state

    @property
    def is_healthy(self) -> bool:
        """헬스 체크"""
        return (
            self._state in [GlobalManagerState.IDLE, GlobalManagerState.ACTIVE] and
            not self._shutdown_requested
        )


# 전역 접근을 위한 헬퍼 함수
async def get_global_websocket_manager() -> GlobalWebSocketManager:
    """전역 웹소켓 매니저 인스턴스 획득"""
    return await GlobalWebSocketManager.get_instance()
