"""
WebSocket v6.0 간소화된 매니저
============================

핵심 기능만 포함한 단순한 WebSocket 관리자
- 싱글톤 패턴
- 기본적인 연결 관리
- 컴포넌트 등록/해제
- 구독 관리 위임
"""

import asyncio
import weakref
import time
import json
from typing import Dict, List, Optional, Any

try:
    import websockets
    import websockets.exceptions
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    websockets = None
    WEBSOCKETS_AVAILABLE = False

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .websocket_types import (
    WebSocketType, GlobalManagerState, ConnectionState, DataType,
    BaseWebSocketEvent, SubscriptionSpec, HealthStatus
)
from .data_processor import DataProcessor
from ..support.subscription_manager import SubscriptionManager
from ..support.jwt_manager import JWTManager
from ..support.websocket_config import get_config

# Rate Limiter 통합
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import (
    gate_websocket
)
from upbit_auto_trading.infrastructure.external_apis.upbit.dynamic_rate_limiter_wrapper import (
    get_dynamic_rate_limiter, DynamicConfig, AdaptiveStrategy
)


class WebSocketManager:
    """간소화된 WebSocket 매니저"""

    _instance: Optional['WebSocketManager'] = None
    _lock = asyncio.Lock()

    def __init__(self):
        if WebSocketManager._instance is not None:
            raise RuntimeError("WebSocketManager는 싱글톤입니다. get_instance()를 사용하세요.")

        # 로깅
        self.logger = create_component_logger("WebSocketManager")

        # 상태
        self._state = GlobalManagerState.IDLE
        self._connections: Dict[WebSocketType, Optional[Any]] = {
            WebSocketType.PUBLIC: None,
            WebSocketType.PRIVATE: None
        }
        self._connection_states: Dict[WebSocketType, ConnectionState] = {
            WebSocketType.PUBLIC: ConnectionState.DISCONNECTED,
            WebSocketType.PRIVATE: ConnectionState.DISCONNECTED
        }

        # 메시지 수신 태스크
        self._message_tasks: Dict[WebSocketType, Optional[asyncio.Task]] = {
            WebSocketType.PUBLIC: None,
            WebSocketType.PRIVATE: None
        }

        # 연결 모니터링 태스크
        self._monitoring_task: Optional[asyncio.Task] = None

        # 연결 헬스체크를 위한 마지막 메시지 수신 시간 추적
        self._last_message_times: Dict[WebSocketType, Optional[float]] = {
            WebSocketType.PUBLIC: None,
            WebSocketType.PRIVATE: None
        }

        # 연결 메트릭스 추가
        self._connection_metrics: Dict[WebSocketType, Dict[str, Any]] = {
            WebSocketType.PUBLIC: {
                'connected_at': None,
                'last_ping_sent': None,
                'last_pong_received': None,
                'consecutive_errors': 0,
                'total_reconnects': 0
            },
            WebSocketType.PRIVATE: {
                'connected_at': None,
                'last_ping_sent': None,
                'last_pong_received': None,
                'consecutive_errors': 0,
                'total_reconnects': 0
            }
        }

        # 컴포넌트 관리
        self._components: Dict[str, weakref.ReferenceType] = {}

        # 하위 시스템
        self._data_processor: Optional[DataProcessor] = None
        self._subscription_manager: Optional[SubscriptionManager] = None  # v6.2 구독 관리자 (리얼타임 중심)
        self._jwt_manager: Optional[JWTManager] = None

        # Rate Limiter 시스템
        self._dynamic_limiter = None
        self._rate_limiter_enabled = True
        self._rate_limit_stats = {
            'total_connections': 0,
            'total_messages': 0,
            'rate_limit_waits': 0,
            'rate_limit_errors': 0
        }

        # ===== v6.1 Pending State 기반 배치 처리 =====
        self._pending_subscription_task: Optional[asyncio.Task] = None
        self._debounce_delay: float = 0.1  # 100ms 디바운스 (추가 요청 수집용)

        self.logger.info("WebSocketManager 초기화 완료 (v6.1 Pending State 지원)")

    @classmethod
    async def get_instance(cls) -> 'WebSocketManager':
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance._initialize()
        return cls._instance

    async def _initialize(self) -> None:
        """내부 초기화"""
        try:
            # 하위 시스템 초기화
            self._data_processor = DataProcessor()
            self._subscription_manager = SubscriptionManager()  # v6.2 구독 관리자 (리얼타임 중심)
            self._jwt_manager = JWTManager()

            # 스트림 변경 감지
            self._subscription_manager.add_change_callback(self._on_subscription_change)

            # Rate Limiter 시스템 초기화
            await self._initialize_rate_limiter()

            self.logger.info("WebSocketManager v6.2 하위 시스템 초기화 완료")

        except Exception as e:
            self.logger.error(f"초기화 실패: {e}")
            raise

    async def _initialize_rate_limiter(self) -> None:
        """Rate Limiter 시스템 초기화"""
        try:
            # 설정 로드
            config = get_config()
            rate_config = config.rate_limiter

            # Rate Limiter 비활성화 시 스킵
            if not rate_config.enable_rate_limiter:
                self.logger.info("Rate Limiter 비활성화됨")
                self._rate_limiter_enabled = False
                return

            # 동적 Rate Limiter 설정
            strategy_map = {
                "conservative": AdaptiveStrategy.CONSERVATIVE,
                "balanced": AdaptiveStrategy.BALANCED,
                "aggressive": AdaptiveStrategy.AGGRESSIVE
            }

            dynamic_config = DynamicConfig(
                strategy=strategy_map.get(rate_config.strategy, AdaptiveStrategy.BALANCED),
                error_429_threshold=rate_config.error_threshold,
                reduction_ratio=rate_config.reduction_ratio,
                recovery_delay=rate_config.recovery_delay,
                recovery_step=rate_config.recovery_step,
                recovery_interval=rate_config.recovery_interval
            )

            if rate_config.enable_dynamic_adjustment:
                self._dynamic_limiter = await get_dynamic_rate_limiter(dynamic_config)

                # 429 에러 콜백 설정
                self._dynamic_limiter.on_429_detected = self._on_rate_limit_error
                self._dynamic_limiter.on_rate_reduced = self._on_rate_reduced
                self._dynamic_limiter.on_rate_recovered = self._on_rate_recovered

                self.logger.info(f"동적 Rate Limiter 초기화 완료 (전략: {rate_config.strategy})")
            else:
                # 기본 Rate Limiter만 사용
                self.logger.info("기본 Rate Limiter 사용")

        except Exception as e:
            self.logger.warning(f"Rate Limiter 초기화 실패 (계속 진행): {e}")
            self._rate_limiter_enabled = False

    def _on_rate_limit_error(self, group, endpoint, error):
        """Rate Limit 에러 감지 콜백"""
        self._rate_limit_stats['rate_limit_errors'] += 1
        self.logger.warning(f"WebSocket Rate Limit 감지: {group.value} - {endpoint}")

    def _on_rate_reduced(self, group, old_ratio, new_ratio):
        """Rate Limit 감소 콜백"""
        self.logger.warning(f"WebSocket Rate 감소: {group.value} {old_ratio:.1%} → {new_ratio:.1%}")

    def _on_rate_recovered(self, group, old_ratio, new_ratio):
        """Rate Limit 복구 콜백"""
        self.logger.info(f"WebSocket Rate 복구: {group.value} {old_ratio:.1%} → {new_ratio:.1%}")

    async def _apply_rate_limit(self, action: str = 'websocket_message') -> None:
        """Rate Limiter 적용"""
        if not self._rate_limiter_enabled:
            return

        try:
            start_time = time.monotonic()

            if self._dynamic_limiter:
                # 동적 Rate Limiter 사용
                await self._dynamic_limiter.acquire(action, 'WS', max_wait=15.0)
            else:
                # 기본 Rate Limiter 사용 (폴백)
                await gate_websocket(action, max_wait=15.0)

            # 대기 시간 통계
            wait_time = time.monotonic() - start_time
            if wait_time > 0.1:  # 100ms 이상 대기한 경우만 기록
                self._rate_limit_stats['rate_limit_waits'] += 1

        except Exception as e:
            self._rate_limit_stats['rate_limit_errors'] += 1
            self.logger.warning(f"Rate Limiter 오류 (계속 진행): {e}")
            # Rate Limiter 실패 시에도 계속 진행 (안전성 확보)

    def _on_subscription_change(self, changes: Dict) -> None:
        """구독 변경 콜백 (v6.1 Pending State 기반 배치 처리)"""
        try:
            # 🎯 Pending State 확인: 이미 처리 중인 Task가 있으면 새로 생성하지 않음
            if not self._pending_subscription_task or self._pending_subscription_task.done():
                self.logger.debug("📝 새로운 구독 변경 처리 Task 생성")
                self._pending_subscription_task = asyncio.create_task(
                    self._debounced_subscription_handler()
                )
            else:
                self.logger.debug("⏳ 이미 처리 중인 구독 Task 있음 - 자동 통합됨")

            # ✅ 새 요청이 와도 SubscriptionManager가 즉시 상태 통합
            # ✅ 기존 Task가 깨어날 때 최신 통합 상태를 한 번에 전송

        except Exception as e:
            self.logger.error(f"구독 변경 콜백 실패: {e}")

    async def _debounced_subscription_handler(self) -> None:
        """디바운스된 구독 처리 (Pending State 핵심 로직)"""
        try:
            # 🔄 짧은 디바운스 대기 (추가 요청들을 모으기 위해)
            await asyncio.sleep(self._debounce_delay)

            self.logger.debug("🚀 통합된 구독 상태 전송 시작")

            # 📡 최신 통합 상태 기반으로 전송 (Rate Limiter 적용)
            await self._send_latest_subscriptions()

            self.logger.debug("✅ 구독 상태 전송 완료")

        except Exception as e:
            self.logger.error(f"디바운스된 구독 처리 실패: {e}")
        finally:
            # 🔄 Pending 상태 해제
            self._pending_subscription_task = None

    async def _send_latest_subscriptions(self) -> None:
        """
        최신 구독 상태 전송 (v6.1 통합 메시지 + Rate Limiter 적용)

        Rate Limiter 펜딩 시나리오:
        1. 요청 A: ticker 구독 → Rate Limiter 대기 (펜딩 Task 생성)
        2. 요청 B: orderbook 구독 → 기존 Task 있음, SubscriptionManager만 업데이트
        3. 요청 C: trade 구독 → 기존 Task 있음, SubscriptionManager만 업데이트
        4. Rate Limiter 해제 → 최신 통합 상태(A+B+C)를 하나의 통합 메시지로 전송
        """
        try:
            if not self._subscription_manager:
                self.logger.warning("SubscriptionManager가 없음")
                return

            # v6.2: 리얼타임 스트림 상태 조회
            public_streams = self._subscription_manager.get_realtime_streams(WebSocketType.PUBLIC)
            private_streams = self._subscription_manager.get_realtime_streams(WebSocketType.PRIVATE)

            # Public 통합 메시지 전송
            if public_streams and self._connection_states[WebSocketType.PUBLIC] == ConnectionState.CONNECTED:
                self.logger.info(f"📤 Public 통합 스트림 전송: {len(public_streams)}개 타입")
                await self._apply_rate_limit('websocket_subscription')
                await self._send_current_subscriptions(WebSocketType.PUBLIC)

            # Private 통합 메시지 전송
            if private_streams:
                self.logger.info(f"📤 Private 통합 스트림 전송: {len(private_streams)}개 타입")
                await self._ensure_connection(WebSocketType.PRIVATE)
                await self._apply_rate_limit('websocket_subscription')
                await self._send_current_subscriptions(WebSocketType.PRIVATE)

            if not public_streams and not private_streams:
                self.logger.debug("📭 전송할 리얼타임 스트림 없음")

        except Exception as e:
            self.logger.error(f"최신 구독 상태 전송 실패: {e}")
            raise

    # ================================================================
    # 상태 관리
    # ================================================================

    async def start(self) -> None:
        """WebSocket 매니저 시작"""
        if self._state == GlobalManagerState.ACTIVE:
            self.logger.warning("이미 실행 중입니다")
            return

        try:
            self._state = GlobalManagerState.INITIALIZING
            self.logger.info("WebSocket 매니저 시작")

            # 전역 WebSocket 관리를 위해 시작 시 즉시 기본 연결 생성
            self.logger.info("기본 WebSocket 연결 생성 중...")
            await self._ensure_connection(WebSocketType.PUBLIC)

            # Private 연결은 필요 시에만 생성 (API 키가 있는 경우)
            try:
                if self._jwt_manager:
                    token = await self._jwt_manager.get_valid_token()
                    if token:
                        self.logger.info("API 키 감지됨, Private 연결 생성 중...")
                        await self._ensure_connection(WebSocketType.PRIVATE)
                    else:
                        self.logger.info("API 키 없음, Private 연결 스킵")
                else:
                    self.logger.info("JWT Manager 없음, Private 연결 스킵")
            except Exception as e:
                self.logger.warning(f"Private 연결 생성 실패 (계속 진행): {e}")

            # 연결 상태 모니터링 시작
            await self._start_connection_monitoring()

            self._state = GlobalManagerState.ACTIVE
            self.logger.info("✅ WebSocket 매니저 시작 완료 (기본 연결 준비됨, 지속성 보장)")

        except Exception as e:
            self._state = GlobalManagerState.ERROR
            self.logger.error(f"시작 실패: {e}")
            raise

    async def stop(self) -> None:
        """WebSocket 매니저 정지"""
        if self._state == GlobalManagerState.IDLE:
            return

        try:
            self._state = GlobalManagerState.SHUTTING_DOWN
            self.logger.info("WebSocket 매니저 정지")

            # 모든 연결 종료
            await self._disconnect_all()

            # Rate Limiter 모니터링 정지
            if self._dynamic_limiter:
                await self._dynamic_limiter.stop_monitoring()

            # 연결 모니터링 중지
            if self._monitoring_task:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass

            self._state = GlobalManagerState.IDLE
            self.logger.info("WebSocket 매니저 정지 완료")

        except Exception as e:
            self._state = GlobalManagerState.ERROR
            self.logger.error(f"정지 실패: {e}")

    # ================================================================
    # 연결 지속성 관리
    # ================================================================

    async def _start_connection_monitoring(self) -> None:
        """연결 상태 모니터링 시작 (지속성 보장)"""
        async def monitor_connections():
            while self._state == GlobalManagerState.ACTIVE:
                try:
                    # 주기적으로 연결 상태 확인 (30초마다)
                    await asyncio.sleep(30.0)

                    # Public 연결 헬스체크
                    if not await self._is_connection_healthy(WebSocketType.PUBLIC):
                        self.logger.warning("Public 연결 헬스체크 실패, 복구 시작")
                        asyncio.create_task(self._recover_connection_with_backoff(WebSocketType.PUBLIC))

                    # Private 연결 헬스체크 (API 키 유효성 포함)
                    if await self._should_maintain_private_connection():
                        if not await self._is_connection_healthy(WebSocketType.PRIVATE):
                            self.logger.warning("Private 연결 헬스체크 실패, 복구 시작")
                            asyncio.create_task(self._recover_connection_with_backoff(WebSocketType.PRIVATE))
                        else:
                            # API 키가 없거나 유효하지 않으면 Private 연결 해제
                            if self._connection_states[WebSocketType.PRIVATE] == ConnectionState.CONNECTED:
                                self.logger.info("API 키 없음/무효, Private 연결 해제")
                                await self._disconnect_websocket(WebSocketType.PRIVATE)

                    # Ping 전송 (연결 유지)
                    await self._send_ping_if_needed()

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"연결 모니터링 중 오류: {e}")
                    await asyncio.sleep(10.0)  # 오류 시 10초 대기 후 재시도

        self._monitoring_task = asyncio.create_task(monitor_connections())
        self.logger.info("✅ 연결 지속성 모니터링 시작")

    async def _send_ping_if_needed(self) -> None:
        """필요 시 Ping 전송 (연결 유지)"""
        current_time = time.time()
        config = get_config()
        ping_interval = config.connection.heartbeat_interval

        for connection_type in [WebSocketType.PUBLIC, WebSocketType.PRIVATE]:
            if self._connection_states[connection_type] != ConnectionState.CONNECTED:
                continue

            connection = self._connections.get(connection_type)
            if not connection:
                continue

            metrics = self._connection_metrics[connection_type]
            last_ping = metrics.get('last_ping_sent', 0)

            # Ping 간격 확인
            if current_time - last_ping >= ping_interval:
                try:
                    # WebSocket ping 전송
                    await connection.ping()
                    metrics['last_ping_sent'] = current_time
                    self.logger.debug(f"📡 Ping 전송: {connection_type}")

                except Exception as e:
                    self.logger.warning(f"Ping 전송 실패 ({connection_type}): {e}")
                    # Ping 실패 시 연결 상태를 의심스럽게 여김
                    metrics['consecutive_errors'] += 1

    async def _reconnect_websocket(self, connection_type: WebSocketType) -> None:
        """WebSocket 재연결"""
        try:
            self.logger.info(f"WebSocket 재연결 시작: {connection_type}")

            # 기존 연결 정리
            await self._disconnect_websocket(connection_type)

            # 잠시 대기 (재연결 안정성)
            await asyncio.sleep(1.0)

            # 새 연결 생성
            await self._connect_websocket(connection_type)

            self.logger.info(f"✅ WebSocket 재연결 완료: {connection_type}")

        except Exception as e:
            self.logger.error(f"WebSocket 재연결 실패 ({connection_type}): {e}")

    async def _is_connection_healthy(self, connection_type: WebSocketType) -> bool:
        """연결 건강도 확인"""
        try:
            connection = self._connections.get(connection_type)

            # 1️⃣ 연결 객체 존재 확인
            if not connection:
                return False

            # 2️⃣ WebSocket 상태 확인 (state == 1 = OPEN)
            if hasattr(connection, 'state') and connection.state != 1:
                self.logger.warning(f"{connection_type} 연결 상태 비정상: state={connection.state}")
                return False

            # 3️⃣ 최근 응답성 확인 (60초 이내 메시지 수신)
            last_activity = self._last_message_times.get(connection_type)
            if last_activity and time.time() - last_activity > 60:
                self.logger.warning(f"{connection_type} 연결: 60초간 메시지 없음")
                return False

            # 4️⃣ 연결 상태가 CONNECTED인지 확인
            if self._connection_states[connection_type] != ConnectionState.CONNECTED:
                return False

            return True

        except Exception as e:
            self.logger.error(f"연결 헬스체크 실패 ({connection_type}): {e}")
            return False

    async def _should_maintain_private_connection(self) -> bool:
        """Private 연결 유지 필요 여부 확인"""
        try:
            if not self._jwt_manager:
                return False

            # API 키 유효성 확인
            token = await self._jwt_manager.get_valid_token()
            return token is not None

        except Exception as e:
            self.logger.warning(f"Private 연결 필요성 확인 실패: {e}")
            return False

    async def _recover_connection_with_backoff(self, connection_type: WebSocketType) -> None:
        """지수백오프를 사용한 연결 복구"""
        config = get_config()
        max_attempts = config.reconnection.max_attempts
        base_delay = config.reconnection.base_delay
        max_delay = config.reconnection.max_delay
        exponential_base = config.reconnection.exponential_base

        for attempt in range(max_attempts):
            try:
                self.logger.info(f"{connection_type} 연결 복구 시도 {attempt + 1}/{max_attempts}")

                # 재연결 시도
                await self._reconnect_websocket(connection_type)

                # 성공 시 메트릭스 업데이트
                metrics = self._connection_metrics[connection_type]
                metrics['total_reconnects'] += 1
                metrics['consecutive_errors'] = 0

                self.logger.info(f"✅ {connection_type} 연결 복구 성공 (시도: {attempt + 1})")
                return

            except Exception as e:
                # 실패 시 메트릭스 업데이트
                metrics = self._connection_metrics[connection_type]
                metrics['consecutive_errors'] += 1

                self.logger.warning(f"❌ {connection_type} 연결 복구 실패 (시도: {attempt + 1}): {e}")

                # 마지막 시도가 아니면 대기
                if attempt < max_attempts - 1:
                    # 지수백오프 계산
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)

                    # Jitter 추가 (설정된 경우)
                    if config.reconnection.jitter:
                        import random
                        delay = delay * (0.5 + random.random() * 0.5)

                    self.logger.info(f"⏱️ {delay:.1f}초 후 재시도...")
                    await asyncio.sleep(delay)

        # 모든 재시도 실패
        self.logger.error(f"🚨 {connection_type} 연결 완전 실패 (최대 재시도 횟수 초과)")
        self._connection_states[connection_type] = ConnectionState.ERROR

    # ================================================================
    # 컴포넌트 관리
    # ================================================================

    async def register_component(
        self,
        component_id: str,
        component_ref: Any,
        subscriptions: Optional[List[SubscriptionSpec]] = None
    ) -> None:
        """컴포넌트 등록"""
        try:
            # WeakRef로 컴포넌트 저장 (안전한 콜백으로 수정)
            def safe_cleanup_callback(ref):
                try:
                    # 이벤트 루프가 실행 중인지 확인
                    loop = asyncio.get_running_loop()
                    if loop and not loop.is_closed():
                        asyncio.create_task(self._cleanup_component(component_id))
                except RuntimeError:
                    # 이벤트 루프가 없거나 종료됨, 무시
                    self.logger.debug(f"컴포넌트 자동 정리 스킵 (이벤트 루프 없음): {component_id}")
                except Exception as e:
                    self.logger.error(f"컴포넌트 자동 정리 오류: {e}")

            self._components[component_id] = weakref.ref(component_ref, safe_cleanup_callback)

            # v6.2: 리얼타임 스트림 등록
            if subscriptions and self._subscription_manager:
                # 🔧 타입 변환: List[SubscriptionSpec] → ComponentSubscription
                from .websocket_types import ComponentSubscription
                component_subscription = ComponentSubscription(
                    component_id=component_id,
                    subscriptions=subscriptions,
                    callback=None,  # 필요시 콜백 설정
                    stream_filter=None  # 필요시 필터 설정
                )

                await self._subscription_manager.register_component(
                    component_id,
                    component_subscription,  # ✅ 올바른 타입
                    component_ref
                )

            self.logger.debug(f"컴포넌트 등록: {component_id}")

        except Exception as e:
            self.logger.error(f"컴포넌트 등록 실패 ({component_id}): {e}")
            raise

    async def unregister_component(self, component_id: str) -> None:
        """컴포넌트 해제"""
        try:
            # v6.2: 리얼타임 스트림 해제
            if self._subscription_manager:
                await self._subscription_manager.unregister_component(component_id)

            # 컴포넌트 제거
            self._components.pop(component_id, None)

        except Exception as e:
            self.logger.error(f"컴포넌트 해제 실패 ({component_id}): {e}")

    async def _cleanup_component(self, component_id: str) -> None:
        """컴포넌트 자동 정리 (WeakRef 콜백)"""
        try:
            self.logger.debug(f"컴포넌트 자동 정리: {component_id}")
            await self.unregister_component(component_id)
        except Exception as e:
            self.logger.error(f"컴포넌트 정리 오류 ({component_id}): {e}")

    # ================================================================
    # 연결 관리
    # ================================================================

    async def _ensure_connection(self, connection_type: WebSocketType) -> None:
        """연결 보장"""
        if self._connection_states[connection_type] != ConnectionState.CONNECTED:
            await self._connect_websocket(connection_type)

    async def _disconnect_if_connected(self, connection_type: WebSocketType) -> None:
        """연결되어 있다면 해제"""
        if self._connection_states[connection_type] == ConnectionState.CONNECTED:
            await self._disconnect_websocket(connection_type)

    async def _connect_websocket(self, connection_type: WebSocketType) -> None:
        """WebSocket 연결"""
        try:
            if not WEBSOCKETS_AVAILABLE:
                raise RuntimeError("websockets 라이브러리가 설치되지 않았습니다")

            self._connection_states[connection_type] = ConnectionState.CONNECTING

            # Rate Limiter 적용 (WebSocket 연결)
            await self._apply_rate_limit('websocket_connect')

            # 설정 로드
            config = get_config()

            # 연결 타입에 따른 URL 선택 (업비트 공식 엔드포인트)
            if connection_type == WebSocketType.PUBLIC:
                url = config.connection.public_url  # wss://api.upbit.com/websocket/v1
            else:
                url = config.connection.private_url  # wss://api.upbit.com/websocket/v1/private

            # Private 연결 시 JWT를 Authorization 헤더로 추가 (업비트 공식 방식)
            headers = {}
            if connection_type == WebSocketType.PRIVATE and self._jwt_manager:
                token = await self._jwt_manager.get_valid_token()
                if token:
                    # 업비트 공식 문서에 따라 JWT는 Authorization 헤더로 전달
                    headers['Authorization'] = f'Bearer {token}'
                    self.logger.debug("Private 연결: JWT 토큰을 Authorization 헤더로 추가")
                else:
                    self.logger.error("Private 연결: 유효한 JWT 토큰을 얻을 수 없습니다")
                    raise RuntimeError("JWT 토큰 없음")

            # 압축 설정 (업비트 공식 압축 지원)
            compression = "deflate" if config.connection.enable_compression else None

            # 연결 생성
            if not WEBSOCKETS_AVAILABLE or websockets is None:
                raise RuntimeError("websockets 라이브러리가 설치되지 않았습니다")

            # 업비트 WebSocket 연결 시도 (Authorization 헤더 포함)
            try:
                self.logger.debug(f"연결 시도: {connection_type} -> {url}")

                # websockets 라이브러리 버전에 따른 헤더 전송 방식
                if headers:
                    # Authorization 헤더가 있는 경우 (Private 연결)
                    connection = await websockets.connect(
                        url,
                        additional_headers=headers  # websockets 15.x에서는 additional_headers 사용
                    )
                else:
                    # Public 연결 (헤더 없음)
                    connection = await websockets.connect(url)

                self.logger.info(f"업비트 WebSocket 연결 성공: {connection_type} -> {url}")

                # 연결 상태 확인 (state 속성 사용)
                connection_state = getattr(connection, 'state', None)
                connection_open = getattr(connection, 'open', None)
                self.logger.debug(f"연결 직후 상태: state={connection_state}, open={connection_open}")

                # state가 1(OPEN)이 아니면 문제
                if hasattr(connection, 'state') and connection.state != 1:
                    self.logger.error(f"WebSocket 상태 비정상: state={connection.state} (1=OPEN, 2=CLOSING, 3=CLOSED)")
                    raise RuntimeError(f"WebSocket 연결 실패: 상태={connection.state}")

            except Exception as e:
                self.logger.error(f"WebSocket 연결 실패 ({connection_type}): {e}")
                raise

            self._connections[connection_type] = connection
            self._connection_states[connection_type] = ConnectionState.CONNECTED
            self._rate_limit_stats['total_connections'] += 1

            # 연결 메트릭스 업데이트
            current_time = time.time()
            self._connection_metrics[connection_type]['connected_at'] = current_time
            self._last_message_times[connection_type] = current_time

            # 메시지 수신 태스크 시작
            task = asyncio.create_task(self._handle_messages(connection_type, connection))
            self._message_tasks[connection_type] = task

            # 현재 구독 전송
            await self._send_current_subscriptions(connection_type)

            self.logger.info(f"WebSocket 연결 성공: {connection_type} -> {url} (압축: {compression is not None})")

        except Exception as e:
            self._connection_states[connection_type] = ConnectionState.DISCONNECTED
            self.logger.error(f"WebSocket 연결 실패 ({connection_type}): {e}")
            raise

    async def _disconnect_websocket(self, connection_type: WebSocketType) -> None:
        """WebSocket 연결 해제"""
        try:
            # 메시지 태스크 취소
            task = self._message_tasks.get(connection_type)
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # 연결 종료
            connection = self._connections.get(connection_type)
            if connection:
                await connection.close()

            # 상태 초기화
            self._connections[connection_type] = None
            self._connection_states[connection_type] = ConnectionState.DISCONNECTED
            self._message_tasks[connection_type] = None

            self.logger.info(f"WebSocket 연결 해제: {connection_type}")

        except Exception as e:
            self.logger.error(f"연결 해제 실패 ({connection_type}): {e}")

    async def _disconnect_all(self) -> None:
        """모든 연결 해제"""
        for connection_type in WebSocketType:
            await self._disconnect_websocket(connection_type)

    async def _send_current_subscriptions(self, connection_type: WebSocketType) -> None:
        """
        현재 구독 정보 전송 (v6.1 통합 메시지 방식)

        기존 방식: 각 데이터 타입별로 개별 메시지 전송
        새로운 방식: 모든 데이터 타입을 하나의 통합 메시지로 전송
        """
        try:
            # v6.2: 리얼타임 스트림 조회
            if self._subscription_manager:
                streams = self._subscription_manager.get_realtime_streams(connection_type)
            else:
                streams = {}

            if not streams:
                self.logger.debug(f"전송할 리얼타임 스트림 없음: {connection_type}")
                return

            # v6.2 통합 메시지 생성 및 전송
            # v6.2: 통합 메시지 생성 (리얼타임 + 스냅샷)
            unified_message = await self._create_unified_message_v6_2(connection_type, streams)

            total_symbols = sum(len(symbols) for symbols in streams.values())
            self.logger.info(f"📤 통합 스트림 메시지 전송 ({connection_type}): {len(streams)}개 타입, {total_symbols}개 심볼")

            await self._send_message(connection_type, unified_message)
            self.logger.info(f"✅ 통합 스트림 메시지 전송 성공 ({connection_type})")

        except Exception as e:
            self.logger.error(f"통합 구독 전송 실패 ({connection_type}): {e}")
            raise

    async def _create_unified_message_v6_2(self, connection_type: WebSocketType, streams: Dict[DataType, set]) -> str:
        """
        v6.2 통합 메시지 생성 (리얼타임 스트림 + 스냅샷 요청)

        Args:
            connection_type: WebSocket 연결 타입
            streams: {DataType: {symbols}} 형태의 리얼타임 스트림 목록

        Returns:
            JSON 문자열 형태의 통합 메시지
        """
        try:
            if not self._subscription_manager:
                return self._create_empty_subscription_message()

            # format_utils의 create_unified_message 활용
            from ..support.format_utils import UpbitMessageFormatter
            formatter = UpbitMessageFormatter()

            # streams를 UpbitMessageFormatter가 기대하는 형식으로 변환
            subscriptions_dict = {
                data_type: list(symbols) for data_type, symbols in streams.items()
            }

            return formatter.create_unified_message(
                ws_type=connection_type.value,
                subscriptions=subscriptions_dict
            )

        except Exception as e:
            self.logger.error(f"v6.2 통합 메시지 생성 실패: {e}")
            # 폴백: 기존 방식
            if streams:
                first_type, first_symbols = next(iter(streams.items()))
                return self._create_subscription_message(first_type, list(first_symbols))
            else:
                return self._create_empty_subscription_message()

    def _create_empty_subscription_message(self) -> str:
        """빈 구독 메시지 생성 (오류 상황 대응)"""
        message = [
            {"ticket": f"upbit_empty_{int(time.time())}"},
            {"format": "DEFAULT"}
        ]
        return json.dumps(message)

    def _create_subscription_message(self, data_type: DataType, symbols: List[str]) -> str:
        """구독 메시지 생성 - v5 호환 (올바른 업비트 형식)"""
        message = [
            {"ticket": f"upbit_websocket_v6_{int(time.time())}"},
            {
                "type": data_type.value,
                "codes": symbols
                # isOnlySnapshot, isOnlyRealtime 제거 = 실시간 구독
            },
            {"format": "DEFAULT"}
        ]
        return json.dumps(message)

    async def _send_message(self, connection_type: WebSocketType, message: str) -> None:
        """메시지 전송"""
        connection = self._connections[connection_type]
        connection_state = self._connection_states[connection_type]

        self.logger.debug(f"메시지 전송 시도: {connection_type}, 상태: {connection_state}, 연결: {connection is not None}")

        if not connection:
            self.logger.error(f"연결이 없음 ({connection_type})")
            raise RuntimeError(f"WebSocket 연결이 없습니다: {connection_type}")

        if connection_state != ConnectionState.CONNECTED:
            self.logger.error(f"연결 상태 불량 ({connection_type}): {connection_state}")
            raise RuntimeError(f"WebSocket 연결 상태가 잘못됨: {connection_type} - {connection_state}")

        try:
            self.logger.debug(f"WebSocket 메시지 전송 시도 ({connection_type}): {message[:100]}...")

            # Rate Limiter 적용 (메시지 전송)
            self.logger.debug("Rate Limiter 적용 중...")
            await self._apply_rate_limit('websocket_message')
            self.logger.debug("Rate Limiter 통과!")

            # 연결 상태 재확인 (websockets 라이브러리의 실제 상태 확인)
            try:
                connection_state = getattr(connection, 'state', None)
                connection_open = getattr(connection, 'open', None)
                self.logger.debug(f"연결 상태 상세: state={connection_state}, open={connection_open}")

                # websockets 라이브러리의 State 확인 (1=OPEN, 2=CLOSING, 3=CLOSED)
                if hasattr(connection, 'state') and connection.state != 1:  # 1 = OPEN
                    self.logger.warning(f"WebSocket 상태 확인 필요: state={connection.state}")
                    # 상태가 OPEN이 아니어도 메시지 전송 시도 (예외로 확인)

            except Exception as e:
                self.logger.warning(f"연결 상태 확인 실패: {e}")

            # 실제 메시지 전송
            self.logger.debug("실제 메시지 전송 중...")
            await connection.send(message)
            self.logger.debug("메시지 전송 완료, 통계 업데이트 중...")

            self._rate_limit_stats['total_messages'] += 1
            self.logger.info(f"✅ 메시지 전송 성공 ({connection_type}): {len(message)} bytes")

        except asyncio.TimeoutError as e:
            self.logger.error(f"❌ 메시지 전송 타임아웃 ({connection_type}): {e}")
            raise
        except Exception as e:
            self.logger.error(f"❌ 메시지 전송 실패 ({connection_type}): {type(e).__name__}: {e}")
            self.logger.error(f"연결 상태: open={getattr(connection, 'open', 'unknown')}")
            raise  # 메시지 전송 실패 시 예외 재발생

    async def _handle_messages(self, connection_type: WebSocketType, connection) -> None:
        """메시지 수신 처리"""
        try:
            async for message in connection:
                try:
                    # 마지막 메시지 수신 시간 업데이트 (헬스체크용)
                    self._last_message_times[connection_type] = time.time()

                    self.logger.debug(f"📨 WebSocket 메시지 수신 ({connection_type}): {message}")

                    # JSON 파싱
                    data = json.loads(message)

                    # stream_type 확인을 위한 디버깅
                    if 'stream_type' in data:
                        self.logger.info(f"🎯 stream_type 발견: {data.get('stream_type')} (타입: {data.get('type')})")
                    else:
                        self.logger.warning(f"⚠️ stream_type 누락: {data.get('type')} - {list(data.keys())}")

                    # 업비트 에러 메시지 확인
                    if 'error' in data:
                        self.logger.error(f"🚨 업비트 WebSocket 에러 ({connection_type}): {data}")
                        continue

                    if 'status' in data and data.get('status') != 'OK':
                        self.logger.warning(f"⚠️ 업비트 WebSocket 상태 메시지 ({connection_type}): {data}")
                        continue

                    # 이벤트 생성
                    event = self._create_event(connection_type, data)
                    if event:
                        # 데이터 프로세서로 전달
                        if self._data_processor:
                            await self._data_processor.route_event(event)

                        # 등록된 컴포넌트들에게 직접 이벤트 전달
                        await self._broadcast_event_to_components(event)

                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON 파싱 실패 ({connection_type}): {e}")
                    self.logger.warning(f"원본 메시지: {message}")
                except Exception as e:
                    self.logger.error(f"메시지 처리 실패 ({connection_type}): {e}")
                    self.logger.error(f"원본 메시지: {message}")

        except Exception as e:
            if WEBSOCKETS_AVAILABLE and websockets and hasattr(websockets, 'exceptions'):
                if isinstance(e, websockets.exceptions.ConnectionClosed):
                    self.logger.info(f"WebSocket 연결 종료: {connection_type}")
                else:
                    self.logger.error(f"메시지 수신 오류 ({connection_type}): {e}")
            else:
                self.logger.error(f"메시지 수신 오류 ({connection_type}): {e}")
        finally:
            self._connection_states[connection_type] = ConnectionState.DISCONNECTED
            # 연결 종료 시 마지막 메시지 시간 초기화
            self._last_message_times[connection_type] = None

    async def _broadcast_event_to_components(self, event: BaseWebSocketEvent) -> None:
        """등록된 모든 컴포넌트에게 이벤트 브로드캐스트"""
        self.logger.debug(f"🔄 컴포넌트 브로드캐스트 시작: 등록된 컴포넌트 수 {len(self._components)}")

        for component_id, component_ref in list(self._components.items()):
            try:
                component = component_ref()  # WeakRef에서 실제 객체 가져오기
                if component and hasattr(component, 'handle_event'):
                    self.logger.debug(f"📤 이벤트 전달 중: {component_id} <- {type(event).__name__}")
                    await component.handle_event(event)
                else:
                    self.logger.warning(f"⚠️ 컴포넌트 {component_id}: handle_event 메서드 없음 또는 객체 무효")
            except Exception as e:
                self.logger.error(f"컴포넌트 {component_id} 이벤트 전달 실패: {e}")
                # WeakRef가 무효화되었을 수 있으므로 정리
                if component_ref() is None:
                    await self._cleanup_component(component_id)

    def _create_event(self, connection_type: WebSocketType, data: Dict) -> Optional[BaseWebSocketEvent]:
        """이벤트 생성"""
        try:
            # 메시지 타입 확인
            data_type = data.get('type') or data.get('ty')

            if not data_type:
                self.logger.warning(f"데이터 타입을 찾을 수 없음: {data}")
                return None

            # 타입별 이벤트 생성 (websocket_types.py의 변환 함수 사용)
            from .websocket_types import (
                create_ticker_event, create_orderbook_event, create_trade_event,
                create_candle_event, create_myorder_event, create_myasset_event
            )

            if data_type == 'ticker':
                event = create_ticker_event(data)
                self.logger.debug(f"📊 Ticker 이벤트 생성: {event.symbol}, stream_type: {event.stream_type}")
                return event
            elif data_type == 'orderbook':
                return create_orderbook_event(data)
            elif data_type == 'trade':
                return create_trade_event(data)
            elif data_type.startswith('candle'):
                return create_candle_event(data)
            elif data_type == 'myorder':
                return create_myorder_event(data)
            elif data_type == 'myasset':
                return create_myasset_event(data)
            else:
                self.logger.warning(f"알 수 없는 데이터 타입: {data_type}")
                return None

        except Exception as e:
            self.logger.error(f"이벤트 생성 실패: {e}")
            self.logger.error(f"원본 데이터: {data}")
            return None

    def _detect_data_type(self, data: Dict) -> Optional[DataType]:
        """데이터 타입 감지"""
        if 'ty' in data:
            type_value = data['ty']

            # 정확한 매칭
            for data_type in DataType:
                if data_type.value == type_value:
                    return data_type

        return None

    # ================================================================
    # 상태 조회
    # ================================================================

    def get_state(self) -> GlobalManagerState:
        """매니저 상태 반환"""
        return self._state

    def get_connection_state(self, connection_type: WebSocketType) -> ConnectionState:
        """연결 상태 반환"""
        return self._connection_states[connection_type]

    def get_connection_metrics(self, connection_type: WebSocketType) -> Dict[str, Any]:
        """특정 연결의 메트릭스 반환"""
        try:
            base_metrics = self._connection_metrics[connection_type].copy()

            # 현재 상태 추가
            base_metrics['current_state'] = self._connection_states[connection_type].value
            base_metrics['is_connected'] = self._connection_states[connection_type] == ConnectionState.CONNECTED

            # 활동 정보 추가
            last_message = self._last_message_times.get(connection_type)
            base_metrics['last_message_time'] = last_message

            # 연결 지속 시간 계산
            connected_at = base_metrics.get('connected_at')
            if connected_at and self._connection_states[connection_type] == ConnectionState.CONNECTED:
                base_metrics['uptime_seconds'] = time.time() - connected_at
            else:
                base_metrics['uptime_seconds'] = 0.0

            # 헬스 점수 계산 (0.0 ~ 1.0)
            health_score = 1.0
            if not base_metrics['is_connected']:
                health_score = 0.0
            else:
                # 연속 에러 수에 따른 감점
                consecutive_errors = base_metrics.get('consecutive_errors', 0)
                health_score -= min(consecutive_errors * 0.1, 0.5)

                # 최근 활동에 따른 감점
                if last_message:
                    inactive_seconds = time.time() - last_message
                    if inactive_seconds > 60:  # 1분 이상 비활성
                        health_score -= min(inactive_seconds / 300, 0.3)  # 최대 5분에서 0.3 감점

                health_score = max(0.0, health_score)

            base_metrics['health_score'] = health_score

            return base_metrics

        except Exception as e:
            self.logger.error(f"연결 메트릭스 조회 실패 ({connection_type}): {e}")
            return {
                'error': str(e),
                'current_state': 'error',
                'is_connected': False,
                'health_score': 0.0
            }

    def get_all_connection_metrics(self) -> Dict[str, Dict[str, Any]]:
        """모든 연결의 메트릭스 반환"""
        return {
            connection_type.value: self.get_connection_metrics(connection_type)
            for connection_type in WebSocketType
        }

    def get_health_status(self) -> HealthStatus:
        """헬스 상태 반환"""
        try:
            is_healthy = (
                self._state == GlobalManagerState.ACTIVE
                and self._data_processor is not None
                and self._subscription_manager is not None
            )

            return HealthStatus(
                status="healthy" if is_healthy else "unhealthy",
                uptime_seconds=0.0,  # 단순화
                total_messages_processed=self._rate_limit_stats['total_messages'],
                connection_errors=self._rate_limit_stats['rate_limit_errors'],
                last_error=None if is_healthy else "시스템 오류"
            )
        except Exception as e:
            return HealthStatus(
                status="error",
                uptime_seconds=0.0,
                total_messages_processed=0,
                connection_errors=1,
                last_error=str(e),
                last_error_time=time.time()
            )

    def get_rate_limiter_status(self) -> Dict[str, Any]:
        """Rate Limiter 상태 반환"""
        status = {
            'enabled': self._rate_limiter_enabled,
            'stats': self._rate_limit_stats.copy(),
            'dynamic_limiter': None
        }

        if self._dynamic_limiter and self._rate_limiter_enabled:
            try:
                status['dynamic_limiter'] = self._dynamic_limiter.get_dynamic_status()
            except Exception as e:
                self.logger.warning(f"Rate Limiter 상태 조회 실패: {e}")

        return status


# ================================================================
# 전역 접근
# ================================================================

_global_manager: Optional[WebSocketManager] = None


async def get_global_websocket_manager() -> WebSocketManager:
    """글로벌 WebSocket 매니저 반환 (Application Service 호환)"""
    global _global_manager
    if _global_manager is None:
        _global_manager = await WebSocketManager.get_instance()
    return _global_manager


async def get_websocket_manager() -> WebSocketManager:
    """WebSocketClient가 사용하는 매니저 반환"""
    return await get_global_websocket_manager()
