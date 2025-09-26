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
from typing import Dict, List, Optional, Any, Set

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

# Rate Limiter 통합 - 새로운 통합 Rate Limiter 사용
from upbit_auto_trading.infrastructure.external_apis.upbit.rate_limiter import (
    UnifiedUpbitRateLimiter,
    get_unified_rate_limiter,
    UpbitRateLimitGroup
)

# WebSocket Rate Limiter 전역 인스턴스
_websocket_rate_limiter: Optional[UnifiedUpbitRateLimiter] = None


async def get_websocket_rate_limiter() -> UnifiedUpbitRateLimiter:
    """WebSocket 전용 Rate Limiter 인스턴스 가져오기"""
    global _websocket_rate_limiter
    if _websocket_rate_limiter is None:
        _websocket_rate_limiter = await get_unified_rate_limiter()
    return _websocket_rate_limiter


async def gate_websocket(action: str, max_wait: float = 15.0):
    """WebSocket 전용 Rate Limiting Gate"""
    try:
        rate_limiter = await get_websocket_rate_limiter()
        # WebSocket 연결은 WEBSOCKET 그룹 사용 - acquire 메서드 사용
        # action을 websocket_ prefix로 변환하여 Rate Limiter 엔드포인트 매핑 활용
        websocket_endpoint = f"websocket_{action}" if not action.startswith("websocket_") else action
        await rate_limiter.acquire(websocket_endpoint, method='WS')
    except Exception as e:
        # WebSocket gate 실패 시 로그만 남기고 계속 진행 (웹소켓 안정성 우선)
        import logging
        logger = logging.getLogger("websocket.rate_limiter")
        logger.warning(f"WebSocket rate limit gate 실패 ({action}): {e}")
        # 짧은 대기 후 진행
        await asyncio.sleep(0.1)


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

        # 🔧 Background Tasks Set (Weak Reference 방지 - 공식 Python 패턴)
        self._background_tasks: Set[asyncio.Task] = set()

        # 🔧 Graceful Shutdown을 위한 Event 기반 중단 메커니즘
        self._shutdown_event: asyncio.Event = asyncio.Event()

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

        # Rate Limiter 시스템 (통합 Rate Limiter 사용)
        self._unified_limiter = None
        self._rate_limiter_enabled = True
        self._rate_limit_stats = {
            'total_connections': 0,
            'total_messages': 0,
            'rate_limit_waits': 0,
            'rate_limit_errors': 0
        }

        # ===== v6.2 안전한 Pending State 기반 처리 =====
        self._pending_subscription_task: Optional[asyncio.Task] = None

        self.logger.info("WebSocketManager 초기화 완료 (v6.2 안전한 Pending State)")

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

    def _create_background_task(self, coro, name: str = "background_task") -> asyncio.Task:
        """
        Background Task 생성 및 관리 (Weak Reference 방지)
        Python 공식 권장 패턴 적용
        """
        task = asyncio.create_task(coro, name=name)

        # Strong Reference 유지
        self._background_tasks.add(task)

        # 완료 시 자동 정리
        task.add_done_callback(self._background_tasks.discard)

        self.logger.debug(f"🎯 Background Task 생성: {name} (총 {len(self._background_tasks)}개)")
        return task

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

            # 통합 Rate Limiter 사용
            self._unified_limiter = await get_unified_rate_limiter()
            self._rate_limiter_enabled = True
            self.logger.info("📊 통합 Rate Limiter 초기화 완료")

            # 기존 동적 조정 기능은 UnifiedUpbitRateLimiter 내부에서 처리됨

        except Exception as e:
            self.logger.warning(f"통합 Rate Limiter 초기화 실패 (계속 진행): {e}")
            self._rate_limiter_enabled = False
            self._unified_limiter = None

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
        """Rate Limiter 적용 (레거시 호환용 - 새로운 코드는 지연된 커밋 패턴 사용 권장)"""
        if not self._rate_limiter_enabled:
            return

        try:
            start_time = time.monotonic()

            # 새로운 통합 Rate Limiter 사용
            await gate_websocket(action, max_wait=15.0)

            # 대기 시간 통계
            wait_time = time.monotonic() - start_time
            if wait_time > 0.1:  # 100ms 이상 대기한 경우만 기록
                self._rate_limit_stats['rate_limit_waits'] += 1

        except Exception as e:
            self._rate_limit_stats['rate_limit_errors'] += 1
            self.logger.warning(f"Rate Limiter 오류 (계속 진행): {e}")
            # Rate Limiter 실패 시에도 계속 진행 (안전성 확보)

    async def _apply_delayed_commit_rate_limit(self, action: str) -> tuple[Any, str]:
        """지연된 커밋을 위한 Rate Limiter 적용 (토큰 예약만)

        Returns:
            tuple: (rate_limiter_instance, websocket_endpoint)
        """
        if not self._rate_limiter_enabled:
            return None, action

        try:
            websocket_endpoint = f"websocket_{action}" if not action.startswith("websocket_") else action
            rate_limiter = await get_websocket_rate_limiter()

            # 토큰만 예약 (타임스탬프 윈도우 업데이트 안함)
            await rate_limiter.acquire(websocket_endpoint, method='WS')
            self.logger.debug(f"📝 Rate Limiter 토큰 예약: {websocket_endpoint}")

            return rate_limiter, websocket_endpoint

        except Exception as e:
            self._rate_limit_stats['rate_limit_errors'] += 1
            self.logger.warning(f"Rate Limiter 토큰 예약 실패 (계속 진행): {e}")
            return None, action

    async def _commit_rate_limit_timestamp(self, rate_limiter: Any, websocket_endpoint: str) -> None:
        """Rate Limiter 타임스탬프 윈도우 커밋"""
        if rate_limiter and websocket_endpoint:
            try:
                await rate_limiter.commit_timestamp(websocket_endpoint, method='WS')
                self.logger.debug(f"✅ Rate Limiter 타임스탬프 커밋: {websocket_endpoint}")
            except Exception as e:
                self.logger.warning(f"Rate Limiter 타임스탬프 커밋 실패: {e}")

    async def _apply_websocket_connection_rate_limit(self, action: str = 'websocket_connect') -> tuple[Any, str]:
        """WebSocket 연결 전용 빠른 Rate Limiter (타임아웃 3초)

        WebSocket 연결은 빠른 응답이 중요하므로 짧은 타임아웃 적용
        """
        if not self._rate_limiter_enabled:
            return None, action

        try:
            websocket_endpoint = f"websocket_{action}" if not action.startswith("websocket_") else action
            rate_limiter = await get_websocket_rate_limiter()

            # WebSocket 연결 전용 빠른 토큰 획득 (타임아웃 3초)
            start_time = time.monotonic()

            try:
                # 짧은 타임아웃으로 빠른 획득 시도
                await asyncio.wait_for(
                    rate_limiter.acquire(websocket_endpoint, method='WS'),
                    timeout=3.0  # WebSocket 연결 전용 짧은 타임아웃
                )

                elapsed = time.monotonic() - start_time
                self.logger.debug(f"🚀 WebSocket 연결 Rate Limiter 빠른 획득: {websocket_endpoint} ({elapsed:.3f}s)")
                return rate_limiter, websocket_endpoint

            except asyncio.TimeoutError:
                elapsed = time.monotonic() - start_time
                self.logger.warning(f"⚡ WebSocket 연결 Rate Limiter 타임아웃 ({elapsed:.1f}s) - 연결 진행")
                # 타임아웃 시에도 연결 진행 (WebSocket 연결 우선)
                return None, websocket_endpoint

        except Exception as e:
            self._rate_limit_stats['rate_limit_errors'] += 1
            self.logger.warning(f"WebSocket 연결 Rate Limiter 오류 (계속 진행): {e}")
            return None, action

    async def _get_rate_limiter_delay(self) -> float:
        """Rate Limiter 실제 지연 시간 측정 (안전한 병합 제어)"""
        if not self._rate_limiter_enabled:
            return 0.0  # Rate Limiter 비활성화 시 지연 없음

        try:
            # 실제 Rate Limiter 지연 시간 측정
            start_time = time.monotonic()

            # 통합 Rate Limiter로 지연 시간 측정
            await gate_websocket('websocket_delay_check', max_wait=15.0)

            actual_delay = time.monotonic() - start_time

            # 지연이 발생했으면 실제 지연 시간 반환
            if actual_delay > 0.01:  # 10ms 이상이면 실제 지연으로 간주
                self.logger.debug(f"🕐 Rate Limiter 실제 지연: {actual_delay:.3f}s")
                return actual_delay
            else:
                return 0.0  # 즉시 사용 가능

        except Exception as e:
            self.logger.warning(f"Rate Limiter 지연 측정 실패: {e}")
            return 0.1  # 오류 시 안전한 기본값

    def _on_subscription_change(self, changes: Dict) -> None:
        """구독 변경 콜백 (안전한 즉시 처리 방식)"""
        try:
            self.logger.info(f"🔔 구독 변경 콜백 수신: {len(changes)}개 변경사항")

            # 🚀 안전한 방식: Pending 없이 즉시 처리 (무한 병합 방지)
            if not self._pending_subscription_task or self._pending_subscription_task.done():
                self.logger.info("📝 새로운 구독 변경 처리 Task 생성")
                self._pending_subscription_task = asyncio.create_task(
                    self._immediate_subscription_handler()
                )
            else:
                self.logger.info("⏳ 기존 구독 Task 완료 대기 중 - 새 요청은 다음 처리 주기에서 반영")
                # 중요: 기존 Task가 끝나면 최신 상태가 자동으로 반영됨
                # 무한 병합 없이 안전하게 처리됨

        except Exception as e:
            self.logger.error(f"구독 변경 콜백 실패: {e}")

    async def _immediate_subscription_handler(self) -> None:
        """즉시 구독 처리 (Rate Limiter 실제 지연 동기화)"""
        try:
            self.logger.info("🚀 즉시 구독 상태 전송 시작")

            # 📡 Rate Limiter와 동기화된 안전한 전송
            await self._send_latest_subscriptions()

            self.logger.info("✅ 구독 상태 전송 완료")

        except Exception as e:
            self.logger.error(f"즉시 구독 처리 실패: {e}")
        finally:
            # 🔄 Pending 상태 해제
            self._pending_subscription_task = None

    async def _debounced_subscription_handler(self) -> None:
        """안전한 구독 처리 (Rate Limiter 실제 지연 기반 병합)"""
        try:
            # 🔍 Rate Limiter 실제 지연 시간 측정
            rate_limiter_delay = await self._get_rate_limiter_delay()

            if rate_limiter_delay == 0.0:
                self.logger.info("⚡ Rate Limiter 즉시 사용 가능 - 바로 전송")
            else:
                # 🎯 실제 지연 시간 기반 추가 수집 시간 (최대 0.1초)
                additional_collect_time = min(rate_limiter_delay * 0.5, 0.1)
                self.logger.info(
                    f"⏳ Rate Limiter 지연 감지 ({rate_limiter_delay:.3f}s) - "
                    f"추가 수집: {additional_collect_time:.3f}s"
                )

                # 실제 지연에 맞춘 최소한의 추가 수집
                if additional_collect_time > 0.01:  # 10ms 이상만 대기
                    await asyncio.sleep(additional_collect_time)

            self.logger.info("🚀 통합된 구독 상태 전송 시작")

            # 📡 최신 통합 상태 기반으로 전송 (Rate Limiter 적용)
            await self._send_latest_subscriptions()

            self.logger.info("✅ 구독 상태 전송 완료")

        except Exception as e:
            self.logger.error(f"구독 처리 실패: {e}")
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

            # Public 통합 메시지 전송 (지연된 커밋 패턴은 _send_message 내부에서 처리)
            if public_streams and self._connection_states[WebSocketType.PUBLIC] == ConnectionState.CONNECTED:
                self.logger.info(f"📤 Public 통합 스트림 전송: {len(public_streams)}개 타입")
                await self._send_current_subscriptions(WebSocketType.PUBLIC)

            # Private 통합 메시지 전송 (지연된 커밋 패턴은 _send_message 내부에서 처리)
            if private_streams:
                self.logger.info(f"📤 Private 통합 스트림 전송: {len(private_streams)}개 타입")
                await self._ensure_connection(WebSocketType.PRIVATE)
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
        """WebSocket 매니저 정지 (개선된 태스크 관리)"""
        self.logger.info("🚀 WebSocketManager.stop() 메서드 시작")
        self.logger.info(f"📊 현재 상태: {self._state}")

        if self._state == GlobalManagerState.IDLE:
            self.logger.info("⚠️ 매니저가 이미 IDLE 상태")
            return

        try:
            self._state = GlobalManagerState.SHUTTING_DOWN
            self.logger.info("WebSocket 매니저 정지")
            self.logger.info(f"📊 shutdown_event 설정 전 상태: {self._shutdown_event.is_set()}")

            # 🔧 Event 기반 중단 신호 전송 (즉시 반응)
            self.logger.info("🛑 Graceful Shutdown 이벤트 설정")
            self._shutdown_event.set()
            self.logger.info(f"📊 shutdown_event 설정 후 상태: {self._shutdown_event.is_set()}")
            self._shutdown_event.set()

            # 1️⃣ 연결 모니터링 중지 (Event 기반으로 즉시 반응)
            if self._monitoring_task and not self._monitoring_task.done():
                try:
                    self.logger.info("🛑 모니터링 태스크 Event 기반 중지 시작")

                    # Event가 설정되었으므로 태스크가 자연스럽게 종료될 때까지 대기
                    try:
                        await asyncio.wait_for(self._monitoring_task, timeout=2.0)
                        self.logger.info("✅ 모니터링 태스크 Event 기반 정상 종료")
                    except asyncio.TimeoutError:
                        self.logger.warning("⚠️ 모니터링 태스크 Event 응답 타임아웃 - 강제 취소")
                        self._monitoring_task.cancel()
                        try:
                            await asyncio.wait_for(self._monitoring_task, timeout=1.0)
                        except (asyncio.TimeoutError, asyncio.CancelledError):
                            pass

                    self._monitoring_task = None

                except (asyncio.CancelledError, asyncio.TimeoutError):
                    self.logger.info("✅ 모니터링 태스크 정리 완료")
                    self._monitoring_task = None
                except Exception as e:
                    self.logger.warning(f"⚠️ 모니터링 태스크 정리 중 오류: {e}")
                    self._monitoring_task = None            # 2️⃣ Rate Limiter 모니터링 정지 (두 번째)

            # 3️⃣ Background Tasks 정리 (Weak Reference 방지용)
            if self._background_tasks:
                self.logger.info(f"🧹 Background Tasks 정리 시작 ({len(self._background_tasks)}개)")

                # 모든 Background Task 취소
                for task in list(self._background_tasks):
                    if not task.done():
                        task.cancel()

                # 취소 완료 대기 (최대 2초)
                if self._background_tasks:
                    try:
                        await asyncio.wait_for(
                            asyncio.gather(*self._background_tasks, return_exceptions=True),
                            timeout=2.0
                        )
                        self.logger.info("✅ Background Tasks 정리 완료")
                    except asyncio.TimeoutError:
                        self.logger.warning("⚠️ Background Tasks 정리 타임아웃")

                self._background_tasks.clear()
            # 통합 Rate Limiter는 글로벌 인스턴스이므로 별도 정리 불필요

            # 3️⃣ 모든 연결 종료 (마지막)
            await self._disconnect_all()

            self._state = GlobalManagerState.IDLE
            self.logger.info("WebSocket 매니저 정지 완료")

        except Exception as e:
            self.logger.error(f"정지 실패: {e}")
            # 에러가 있어도 IDLE 상태로 변경 (다음 시작을 위해)
            self._state = GlobalManagerState.IDLE

    @classmethod
    async def reset_instance(cls) -> None:
        """싱글톤 인스턴스 리셋 (테스트용)"""
        async with cls._lock:
            if cls._instance is not None:
                try:
                    await cls._instance.stop()
                except Exception as e:
                    # 로깅용 임시 logger
                    import logging
                    logger = logging.getLogger("WebSocketManager")
                    logger.warning(f"인스턴스 정지 중 오류 (무시): {e}")
                finally:
                    cls._instance = None

    # ================================================================
    # 연결 지속성 관리
    # ================================================================

    async def _start_connection_monitoring(self) -> None:
        """연결 상태 모니터링 시작 (Event 기반 Graceful Shutdown)"""
        self.logger.info("🚀 _start_connection_monitoring() 메서드 시작")

        async def monitor_connections():
            self.logger.info("🔍 Event 기반 연결 모니터링 시작")
            self.logger.info(f"📊 shutdown_event 상태: {self._shutdown_event.is_set()}")

            while self._state == GlobalManagerState.ACTIVE:
                try:
                    # 🔧 Event 기반 대기: 30초 또는 shutdown_event 중 먼저 발생하는 것
                    try:
                        # 🛡️ Event Loop 바인딩 안전성 체크
                        current_loop = asyncio.get_running_loop()
                        if hasattr(self._shutdown_event, '_loop') and self._shutdown_event._loop != current_loop:
                            self.logger.warning("⚠️ shutdown_event가 다른 이벤트 루프에 바인딩됨, 새로 생성")
                            self._shutdown_event = asyncio.Event()

                        await asyncio.wait_for(self._shutdown_event.wait(), timeout=30.0)
                        # shutdown_event가 설정되면 즉시 종료
                        self.logger.info("🛑 Shutdown Event 감지 - 모니터링 루프 즉시 종료")
                        break
                    except RuntimeError as e:
                        if "bound to a different event loop" in str(e):
                            self.logger.warning("🔧 Event Loop 바인딩 문제 해결: shutdown_event 재생성")
                            self._shutdown_event = asyncio.Event()
                            # 재생성 후 다시 시도하지 않고 타임아웃으로 처리
                            await asyncio.sleep(30.0)
                        else:
                            raise e
                    except asyncio.TimeoutError:
                        # 30초 타임아웃 - 정상적인 헬스체크 수행
                        self.logger.debug("⏰ 30초 헬스체크 타이머 - 연결 상태 확인")

                    # 상태가 변경되었으면 루프 종료
                    if self._state != GlobalManagerState.ACTIVE:
                        self.logger.info("🏁 GlobalManagerState 변경 감지 - 모니터링 루프 종료")
                        break

                    # Public 연결 헬스체크
                    if not await self._is_connection_healthy(WebSocketType.PUBLIC):
                        self.logger.warning("Public 연결 헬스체크 실패, 복구 시작")
                        self._create_background_task(
                            self._recover_connection_with_backoff(WebSocketType.PUBLIC),
                            "public_recovery"
                        )

                    # Private 연결 헬스체크 (API 키 유효성 포함)
                    if await self._should_maintain_private_connection():
                        # API 키가 유효하면 헬스체크 수행
                        if not await self._is_connection_healthy(WebSocketType.PRIVATE):
                            self.logger.warning("Private 연결 헬스체크 실패, 복구 시작")
                            self._create_background_task(
                                self._recover_connection_with_backoff(WebSocketType.PRIVATE),
                                "private_recovery"
                            )
                    else:
                        # API 키가 없거나 유효하지 않으면 Private 연결 해제
                        if self._connection_states[WebSocketType.PRIVATE] == ConnectionState.CONNECTED:
                            self.logger.info("API 키 없음/무효, Private 연결 해제")
                            await self._disconnect_websocket(WebSocketType.PRIVATE)

                    # Ping 전송 (연결 유지) - 상태 재확인
                    if self._state != GlobalManagerState.ACTIVE:
                        break
                    await self._send_ping_if_needed()

                except asyncio.CancelledError:
                    self.logger.info("🛑 모니터링 태스크 취소 신호 수신 - 정상 종료")
                    break
                except Exception as e:
                    import traceback
                    self.logger.error(f"연결 모니터링 중 오류: {e}")
                    self.logger.error(f"스택 트레이스: {traceback.format_exc()}")
                    # 오류 시에도 상태 확인 후 대기
                    if self._state != GlobalManagerState.ACTIVE:
                        break
                    # 오류 시 Event 기반 대기 (10초 또는 shutdown_event)
                    try:
                        # 🛡️ Event Loop 바인딩 안전성 체크
                        current_loop = asyncio.get_running_loop()
                        if hasattr(self._shutdown_event, '_loop') and self._shutdown_event._loop != current_loop:
                            self._shutdown_event = asyncio.Event()

                        await asyncio.wait_for(self._shutdown_event.wait(), timeout=10.0)
                        self.logger.info("🛑 오류 처리 중 Shutdown Event 감지")
                        break
                    except RuntimeError as e:
                        if "bound to a different event loop" in str(e):
                            self.logger.warning("🔧 Event Loop 바인딩 문제 해결: shutdown_event 재생성")
                            self._shutdown_event = asyncio.Event()
                            await asyncio.sleep(10.0)
                        else:
                            raise e
                    except asyncio.TimeoutError:
                        pass  # 10초 후 재시도

            self.logger.info("🏁 Event 기반 모니터링 루프 완전 종료")


        self._monitoring_task = asyncio.create_task(monitor_connections())
        self.logger.info("✅ Event 기반 연결 지속성 모니터링 태스크 생성 완료")
        self.logger.info(f"📊 모니터링 태스크 상태: {self._monitoring_task}")
        self.logger.info("✅ Event 기반 연결 지속성 모니터링 시작")

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

            # None 값 처리
            if last_ping is None:
                last_ping = 0
                metrics['last_ping_sent'] = 0

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
        """연결 건강도 확인 (구독 상태 고려)"""
        try:
            connection = self._connections.get(connection_type)

            # 1️⃣ 연결 객체 존재 확인
            if not connection:
                return False

            # 2️⃣ WebSocket 상태 확인 (state == 1 = OPEN)
            if hasattr(connection, 'state') and connection.state != 1:
                self.logger.warning(f"{connection_type} 연결 상태 비정상: state={connection.state}")
                return False

            # 3️⃣ 연결 상태가 CONNECTED인지 확인
            if self._connection_states[connection_type] != ConnectionState.CONNECTED:
                return False

            # 4️⃣ 구독 상태 고려한 응답성 확인
            return await self._check_connection_responsiveness(connection_type)

        except Exception as e:
            self.logger.error(f"연결 헬스체크 실패 ({connection_type}): {e}")
            return False

    async def _check_connection_responsiveness(self, connection_type: WebSocketType) -> bool:
        """연결 응답성 확인 (구독 여부 고려)"""
        try:
            # 활성 구독 상태 확인
            has_active_subscriptions = self._has_active_subscriptions(connection_type)
            last_activity = self._last_message_times.get(connection_type)
            current_time = time.time()

            # 구독이 없는 경우: 연결 자체는 건강한 것으로 간주
            if not has_active_subscriptions:
                self.logger.debug(f"{connection_type} 연결: 구독 없음, 건강한 상태로 간주")
                # Ping으로 연결 상태만 간단히 확인
                return await self._verify_connection_with_ping(connection_type)

            # 구독이 있는 경우: 메시지 수신 시간 확인 (더 엄격)
            # None 체크로 Float-NoneType 에러 방지
            if last_activity is not None and current_time - last_activity > 60:
                self.logger.warning(f"{connection_type} 연결: 구독 있지만 60초간 메시지 없음")
                return False

            # last_activity가 None인 경우 (연결 후 아직 메시지 없음)
            if last_activity is None:
                self.logger.debug(f"{connection_type} 연결: 구독 있음, 첫 메시지 대기 중")
                return True  # 연결 직후로 간주

            # 구독이 있고 최근에 메시지를 받았으면 건강
            return True

        except Exception as e:
            self.logger.error(f"연결 응답성 확인 실패 ({connection_type}): {e}")
            return False

    def _has_active_subscriptions(self, connection_type: WebSocketType) -> bool:
        """활성 구독 존재 여부 확인"""
        try:
            if not self._subscription_manager:
                return False

            # 리얼타임 스트림 확인
            streams = self._subscription_manager.get_realtime_streams(connection_type)
            for data_type, symbols in streams.items():
                if symbols:  # 심볼이 있으면 활성 구독
                    return True

            # 펜딩 스냅샷 확인
            pending = self._subscription_manager.get_pending_snapshots(connection_type)
            for data_type, symbols in pending.items():
                if symbols:  # 펜딩 스냅샷이 있으면 활성
                    return True

            return False

        except Exception as e:
            self.logger.debug(f"구독 상태 확인 실패 ({connection_type}): {e}")
            return False

    async def _verify_connection_with_ping(self, connection_type: WebSocketType) -> bool:
        """Ping으로 연결 상태 실제 확인 (개선된 방법)"""
        try:
            connection = self._connections.get(connection_type)
            if not connection:
                return False

            # 사용자 제시 방법: ping()의 pong_waiter를 wait_for로 감싸기
            self.logger.debug(f"🏓 {connection_type} Ping 전송 중...")
            pong_waiter = await connection.ping()
            await asyncio.wait_for(pong_waiter, timeout=3.0)

            # Pong 응답 받음
            self.logger.debug(f"✅ {connection_type} Pong 응답 받음 - 연결 살아있음")
            return True

        except asyncio.TimeoutError:
            self.logger.warning(f"❌ {connection_type} Ping 응답 없음 - 연결 문제?")
            return False
        except Exception as e:
            self.logger.warning(f"🚨 {connection_type} Ping 오류: {e}")
            return False

    async def _should_maintain_private_connection(self) -> bool:
        """Private 연결 유지 필요 여부 확인"""
        try:
            if not self._jwt_manager:
                self.logger.debug("JWT Manager 없음")
                return False

            # API 키 유효성 확인
            token = await self._jwt_manager.get_valid_token()
            has_token = token is not None
            self.logger.debug(f"JWT 토큰 확인 결과: {has_token} (토큰 길이: {len(token) if token else 0})")
            return has_token

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
            self.logger.info(f"🔄 컴포넌트 등록 시작: {component_id} (구독 {len(subscriptions or [])}개)")

            # WeakRef로 컴포넌트 저장 (안전한 콜백으로 수정)
            def safe_cleanup_callback(ref):
                try:
                    # 이벤트 루프가 실행 중인지 확인
                    loop = asyncio.get_running_loop()
                    if loop and not loop.is_closed():
                        self._create_background_task(
                            self._cleanup_component(component_id),
                            f"cleanup_{component_id}"
                        )
                except RuntimeError:
                    # 이벤트 루프가 없거나 종료됨, 무시
                    self.logger.debug(f"컴포넌트 자동 정리 스킵 (이벤트 루프 없음): {component_id}")
                except Exception as e:
                    self.logger.error(f"컴포넌트 자동 정리 오류: {e}")

            self._components[component_id] = weakref.ref(component_ref, safe_cleanup_callback)
            self.logger.debug(f"📝 WeakRef 컴포넌트 저장 완료: {component_id}")

            # v6.2: 리얼타임 스트림 등록
            if subscriptions and self._subscription_manager:
                self.logger.debug(f"📊 구독 정보 변환 시작: {len(subscriptions)}개")

                # 🔧 타입 변환: List[SubscriptionSpec] → ComponentSubscription
                from .websocket_types import ComponentSubscription
                component_subscription = ComponentSubscription(
                    component_id=component_id,
                    subscriptions=subscriptions,
                    callback=None,  # 필요시 콜백 설정
                    stream_filter=None  # 필요시 필터 설정
                )
                self.logger.debug("✅ ComponentSubscription 생성 완료")

                self.logger.debug("🎯 SubscriptionManager.register_component() 호출")
                await self._subscription_manager.register_component(
                    component_id,
                    component_subscription,  # ✅ 올바른 타입
                    component_ref
                )
                self.logger.info("✅ SubscriptionManager.register_component() 완료")

                # ✅ Pending State 메커니즘에 의한 자동 전송 활용
                # _on_subscription_change() 콜백이 자동으로 호출되어 통합 전송됨
                self.logger.info(f"🚀 구독 등록 완료: {component_id} - Pending State 메커니즘 활용")
            else:
                if not subscriptions:
                    self.logger.warning(f"⚠️ 구독 정보 없음: {component_id}")
                if not self._subscription_manager:
                    self.logger.error(f"❌ SubscriptionManager 없음: {component_id}")

            self.logger.info(f"✅ 전체 컴포넌트 등록 완료: {component_id}")

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

            # 🚀 WebSocket 연결 전용 빠른 Rate Limiter 적용 (타임아웃 3초)
            try:
                rate_limiter, websocket_endpoint = await self._apply_websocket_connection_rate_limit('websocket_connect')
            except Exception as e:
                self.logger.warning(f"WebSocket 연결 Rate Limiter 실패 (계속 진행): {e}")
                rate_limiter, websocket_endpoint = None, 'websocket_connect'

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
                # 🔧 WebSocket 연결마다 새로운 JWT 토큰 강제 생성 (업비트 보안 정책)
                self.logger.debug("Private 연결: 새로운 JWT 토큰 강제 생성 시작")
                token_refresh_success = await self._jwt_manager.force_refresh()

                if token_refresh_success:
                    token = await self._jwt_manager.get_valid_token()
                    if token:
                        # 업비트 공식 문서에 따라 JWT는 Authorization 헤더로 전달
                        headers['Authorization'] = f'Bearer {token}'
                        self.logger.debug("Private 연결: 새로운 JWT 토큰을 Authorization 헤더로 추가")
                    else:
                        self.logger.error("Private 연결: JWT 강제 갱신 후에도 토큰 없음")
                        raise RuntimeError("JWT 토큰 강제 갱신 실패")
                else:
                    self.logger.error("Private 연결: JWT 토큰 강제 갱신 실패")
                    raise RuntimeError("JWT 토큰 강제 갱신 실패")

            # 압축 설정 (업비트 공식 압축 지원)
            compression = "deflate" if config.connection.enable_compression else None

            # 연결 생성
            if not WEBSOCKETS_AVAILABLE or websockets is None:
                raise RuntimeError("websockets 라이브러리가 설치되지 않았습니다")

            # 업비트 WebSocket 연결 시도 (Authorization 헤더 포함)
            max_retry_attempts = 2 if connection_type == WebSocketType.PRIVATE else 1

            for attempt in range(max_retry_attempts):
                try:
                    self.logger.debug(f"연결 시도: {connection_type} -> {url} (시도: {attempt + 1}/{max_retry_attempts})")

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

                    # 성공적으로 연결됨
                    break

                except Exception as e:
                    self.logger.error(f"WebSocket 연결 실패 ({connection_type}), 시도 {attempt + 1}: {e}")

                    # Private 연결에서 HTTP 401 오류이고 재시도가 가능한 경우
                    if (connection_type == WebSocketType.PRIVATE and
                        attempt < max_retry_attempts - 1 and
                        ("401" in str(e) or "unauthorized" in str(e).lower())):

                        self.logger.warning("HTTP 401 오류 감지 - JWT 토큰 재갱신 후 재시도")

                        # JWT 토큰 재갱신
                        if self._jwt_manager:
                            try:
                                await self._jwt_manager.force_refresh()
                                new_token = await self._jwt_manager.get_valid_token()
                                if new_token:
                                    headers['Authorization'] = f'Bearer {new_token}'
                                    self.logger.debug("JWT 토큰 재갱신 완료 - 재시도 준비")
                                    continue  # 다음 시도로
                            except Exception as jwt_error:
                                self.logger.error(f"JWT 토큰 재갱신 실패: {jwt_error}")

                    # 마지막 시도이거나 재시도 불가능한 오류
                    if attempt == max_retry_attempts - 1:
                        raise  # 최종 예외 발생

                    # 재시도 전 짧은 대기
                    await asyncio.sleep(0.5)

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

            # 🚀 WebSocket 연결 성공 시 타임스탬프 커밋 (빠른 처리)
            if rate_limiter:  # Rate Limiter가 성공적으로 획득된 경우만
                try:
                    await self._commit_rate_limit_timestamp(rate_limiter, websocket_endpoint)
                except Exception as e:
                    self.logger.warning(f"WebSocket 연결 Rate Limiter 커밋 실패 (무시): {e}")
            else:
                self.logger.debug(f"Rate Limiter 타임아웃으로 커밋 스킵: {websocket_endpoint}")

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

            # 메트릭스 리셋
            if connection_type in self._connection_metrics:
                self._connection_metrics[connection_type]['connected_at'] = None
                self._connection_metrics[connection_type]['uptime_seconds'] = 0.0

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

            # 🎯 메시지 전송 완료 후 구독 상태 업데이트 (지연 업데이트)
            if self._subscription_manager:
                self._subscription_manager.commit_subscription_state_update(connection_type)
                self.logger.debug(f"🔄 구독 상태 업데이트 완료 ({connection_type})")

        except Exception as e:
            self.logger.error(f"통합 구독 전송 실패 ({connection_type}): {e}")
            raise

    async def _create_unified_message_v6_2(self, connection_type: WebSocketType, streams: Dict[DataType, set]) -> str:
        """
        v6.2 통합 메시지 생성 (리얼타임 스트림 + 스냅샷 요청, 기존/신규 구독 분리 지원)

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

            # 구독 분류 정보 가져오기 (Phase 1에서 구현한 API 활용)
            subscription_classification = self._subscription_manager.get_subscription_classification(connection_type)

            # 🔍 디버그: 분류 정보 상세 로깅
            self.logger.debug("🔍 구독 분류 정보 조회 결과:")
            self.logger.debug(f"  - 분류 정보 존재: {subscription_classification is not None}")
            if subscription_classification:
                self.logger.debug(f"  - 분류된 타입 수: {len(subscription_classification)}")
                for data_type, classification in subscription_classification.items():
                    existing = classification.get('existing', [])
                    new = classification.get('new', [])
                    self.logger.debug(f"  - {data_type.value}: 기존={existing}, 신규={new}")
            else:
                self.logger.debug(f"  - 분류 정보 없음, subscriptions_dict={subscriptions_dict}")

            # 분류 정보가 있으면 새로운 방식으로, 없으면 기존 방식으로 처리
            if subscription_classification:
                self.logger.debug(f"🎯 분류된 구독 정보 활용: {len(subscription_classification)}개 타입")
                unified_message = formatter.create_unified_message(
                    ws_type=connection_type.value,
                    subscriptions=subscriptions_dict,
                    subscription_classification=subscription_classification
                )
                self.logger.debug(f"🎯 분류 방식 결과 메시지: {unified_message}")
                return unified_message
            else:
                # � 분류 정보 없음 - 이는 시스템 버그이거나 지원하지 않는 타입
                if subscriptions_dict:
                    unsupported_types = list(subscriptions_dict.keys())
                    self.logger.error(f"🚨 지원하지 않는 데이터 타입 감지: {unsupported_types}")
                    self.logger.error("🚨 이는 시스템 버그이거나 업비트 API 변경으로 인한 문제일 수 있습니다")

                    # 안전을 위해 빈 메시지 반환 (잘못된 구독 방지)
                    self.logger.warning("⚠️  안전을 위해 구독 요청을 차단합니다")
                    return self._create_empty_subscription_message()
                else:
                    # 빈 구독은 정상 (모든 컴포넌트가 구독 해제된 상태)
                    self.logger.debug("📝 빈 구독 상태 - 정상")
                    return self._create_empty_subscription_message()

        except Exception as e:
            self.logger.error(f"v6.2 통합 메시지 생성 실패: {e}")
            self.logger.error("예외 발생 위치: _create_unified_message_v6_2")
            self.logger.error(f"예외 타입: {type(e).__name__}")

            # 🚨 안전을 위해 빈 메시지 반환 - 잘못된 구독 전송 방지
            self.logger.error("🚨 안전을 위해 구독 요청을 차단합니다 (예외 발생)")
            return self._create_empty_subscription_message()

    def _create_empty_subscription_message(self) -> str:
        """빈 구독 메시지 생성 (오류 상황 대응)"""
        message = [
            {"ticket": "public"},
            {"format": "DEFAULT"}
        ]
        return json.dumps(message)

    def _create_subscription_message(self, data_type: DataType, symbols: List[str]) -> str:
        """구독 메시지 생성 - v5 호환 (올바른 업비트 형식)"""
        message = [
            {"ticket": "public"},
            {
                "type": data_type.value,
                "codes": symbols
                # isOnlySnapshot, isOnlyRealtime 제거 = 실시간 구독
            },
            {"format": "DEFAULT"}
        ]
        return json.dumps(message)

    async def send_raw_message(self, connection_type: WebSocketType, message_data: list) -> None:
        """
        원시 메시지 직접 전송 (구독 목록 조회 등 특수 용도)

        Args:
            connection_type: WebSocket 연결 타입 (PUBLIC/PRIVATE)
            message_data: 전송할 메시지 데이터 (list 형태)
        """
        try:
            message_json = json.dumps(message_data)
            self.logger.debug(f"📤 원시 메시지 전송: {connection_type.value}, 내용: {message_json}")
            await self._send_message(connection_type, message_json)
            self.logger.info(f"✅ 원시 메시지 전송 완료: {connection_type.value}")
        except Exception as e:
            self.logger.error(f"💥 원시 메시지 전송 실패 ({connection_type.value}): {e}")
            raise

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

        # 🚀 지연된 커밋 패턴 적용: acquire → 전송 → commit_timestamp
        websocket_endpoint = 'websocket_message'
        rate_limiter = None

        try:
            self.logger.debug(f"WebSocket 메시지 전송 시도 ({connection_type}): {message}")

            # 1️⃣ Rate Limiter 토큰 예약 (타임스탬프 업데이트 안함)
            self.logger.debug("Rate Limiter 토큰 예약 중...")
            if self._rate_limiter_enabled:
                try:
                    rate_limiter = await get_websocket_rate_limiter()
                    await rate_limiter.acquire(websocket_endpoint, method='WS')
                    self.logger.debug("Rate Limiter 토큰 예약 완료!")
                except Exception as e:
                    self.logger.warning(f"Rate Limiter 토큰 예약 실패 (계속 진행): {e}")
                    rate_limiter = None            # 연결 상태 재확인 (websockets 라이브러리의 실제 상태 확인)
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

            # 2️⃣ 실제 메시지 전송
            self.logger.debug("실제 메시지 전송 중...")
            await connection.send(message)
            self.logger.debug("메시지 전송 완료, 통계 업데이트 중...")

            # 3️⃣ 성공 시 타임스탬프 윈도우 커밋
            if self._rate_limiter_enabled and rate_limiter:
                try:
                    await rate_limiter.commit_timestamp(websocket_endpoint, method='WS')
                    self.logger.debug(f"📊 타임스탬프 커밋 완료: {websocket_endpoint}")
                except Exception as e:
                    self.logger.warning(f"Rate Limiter 타임스탬프 커밋 실패: {e}")
                    # 커밋 실패해도 메시지는 성공적으로 전송되었으므로 계속 진행

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

                    # 메시지 로깅 (처음 50자만 표시, 바이트/문자열 호환)
                    if isinstance(message, bytes):
                        message_str = message.decode('utf-8')
                    else:
                        message_str = message
                    message_preview = message_str[:50] + "..." if len(message_str) > 50 else message_str
                    self.logger.debug(f"📨 WebSocket 메시지 수신 ({connection_type}): {message_preview}")

                    # JSON 파싱 (바이트/문자열 호환)
                    if isinstance(message, bytes):
                        message_str = message.decode('utf-8')
                    else:
                        message_str = message
                    data = json.loads(message_str)

                    # SIMPLE 포맷 자동 변환 (Simple Mode 수신 데이터 처리)
                    from upbit_auto_trading.infrastructure.external_apis.upbit.websocket.support.websocket_config import (
                        should_auto_convert_incoming
                    )

                    if should_auto_convert_incoming():
                        try:
                            from upbit_auto_trading.infrastructure.external_apis.upbit.websocket.support.format_utils import (
                                UpbitMessageFormatter
                            )

                            # UpbitMessageFormatter 인스턴스가 없으면 생성
                            if not hasattr(self, '_format_converter'):
                                self._format_converter = UpbitMessageFormatter()

                            # SIMPLE 포맷인지 감지하고 변환
                            simple_type = self._format_converter._detect_simple_type(data)
                            if simple_type:
                                self.logger.debug(f"🗜️ SIMPLE 포맷 감지 ({simple_type}): 자동 변환 시작")
                                data = self._format_converter.convert_simple_to_default(data)
                                self.logger.debug("✅ DEFAULT 포맷으로 변환 완료")
                        except Exception as e:
                            self.logger.warning(f"⚠️ SIMPLE 포맷 변환 실패 (원본 데이터 사용): {e}")

                    # stream_type 확인을 위한 디버깅
                    if 'stream_type' in data:
                        self.logger.info(f"🎯 stream_type 발견: {data.get('stream_type')} (타입: {data.get('type')})")
                    else:
                        # 관리 응답 메시지는 stream_type이 없어도 정상
                        if 'method' in data:
                            self.logger.debug(f"🔧 관리 응답 메시지: {data.get('method')} (stream_type 불필요)")
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
                    # 메시지를 안전하게 문자열로 변환
                    if isinstance(message, bytes):
                        message_safe = message.decode('utf-8', errors='replace')
                    else:
                        message_safe = message
                    message_preview = message_safe[:50] + "..." if len(message_safe) > 50 else message_safe
                    self.logger.warning(f"JSON 파싱 실패 ({connection_type}): {e}")
                    self.logger.warning(f"원본 메시지: {message_preview}")
                except Exception as e:
                    # 메시지를 안전하게 문자열로 변환
                    if isinstance(message, bytes):
                        message_safe = message.decode('utf-8', errors='replace')
                    else:
                        message_safe = message
                    message_preview = message_safe[:50] + "..." if len(message_safe) > 50 else message_safe
                    self.logger.error(f"메시지 처리 실패 ({connection_type}): {e}")
                    self.logger.error(f"원본 메시지: {message_preview}")

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

        # 무효 컴포넌트 ID 수집
        invalid_component_ids = []

        for component_id, component_ref in list(self._components.items()):
            try:
                component = component_ref()  # WeakRef에서 실제 객체 가져오기
                if component and hasattr(component, 'handle_event'):
                    self.logger.debug(f"📤 이벤트 전달 중: {component_id} <- {type(event).__name__}")
                    await component.handle_event(event)
                else:
                    self.logger.warning(f"⚠️ 컴포넌트 {component_id}: handle_event 메서드 없음 또는 객체 무효")
                    invalid_component_ids.append(component_id)
            except Exception as e:
                self.logger.error(f"컴포넌트 {component_id} 이벤트 전달 실패: {e}")
                # WeakRef가 무효화되었을 수 있으므로 정리 대상에 추가
                if component_ref() is None:
                    invalid_component_ids.append(component_id)

        # 무효 컴포넌트 즉시 정리 (강화된 정리)
        if invalid_component_ids:
            self.logger.info(f"🧹 무효 컴포넌트 {len(invalid_component_ids)}개 즉시 정리: {invalid_component_ids}")
            for component_id in invalid_component_ids:
                try:
                    # WeakRef 제거
                    if component_id in self._components:
                        del self._components[component_id]
                        self.logger.debug(f"🗑️ WeakRef 제거 완료: {component_id}")

                    # SubscriptionManager에서도 제거
                    if self._subscription_manager:
                        await self._subscription_manager.unregister_component(component_id)
                        self.logger.debug(f"📤 SubscriptionManager에서 제거 완료: {component_id}")

                except Exception as e:
                    self.logger.error(f"컴포넌트 정리 실패 ({component_id}): {e}")

    def _create_event(self, connection_type: WebSocketType, data: Dict) -> Optional[BaseWebSocketEvent]:
        """이벤트 생성"""
        try:
            # 관리 응답 메시지 처리 (LIST_SUBSCRIPTIONS 등)
            if 'method' in data:
                from .websocket_types import create_admin_response_event
                event = create_admin_response_event(data)
                self.logger.debug(f"🔧 관리 응답 이벤트 생성: {data.get('method')}")
                return event

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
            elif data_type == 'myOrder':  # 정확한 케이스 매칭
                return create_myorder_event(data)
            elif data_type == 'myAsset':  # 정확한 케이스 매칭
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
        # 'ty' 필드 우선 확인 (기존 방식)
        if 'ty' in data:
            type_value = data['ty']
        # 'type' 필드 확인 (Private WebSocket의 경우)
        elif 'type' in data:
            type_value = data['type']
        else:
            return None

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
            if connected_at is not None and self._connection_states[connection_type] == ConnectionState.CONNECTED:
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
                if last_message is not None:
                    inactive_seconds = time.time() - last_message
                    if inactive_seconds > 60:  # 1분 이상 비활성
                        health_score -= min(inactive_seconds / 300, 0.3)  # 최대 5분에서 0.3 감점
                else:
                    # last_message가 None인 경우: 새 연결로 간주하여 감점 없음
                    pass

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
        """Rate Limiter 상태 반환 (통합 Rate Limiter 사용)"""
        status = {
            'enabled': self._rate_limiter_enabled,
            'stats': self._rate_limit_stats.copy(),
            'unified_limiter': None
        }

        if self._unified_limiter and self._rate_limiter_enabled:
            try:
                # 통합 Rate Limiter의 상태 정보 조회
                status['unified_limiter'] = {
                    'type': 'UnifiedUpbitRateLimiter',
                    'websocket_enabled': True
                }
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


def get_websocket_manager_sync() -> Optional[WebSocketManager]:
    """동기식 매니저 반환 (데드락 방지용 - stop() 전용)"""
    global _global_manager
    return _global_manager  # Lock 없이 기존 인스턴스만 반환


async def get_websocket_manager() -> WebSocketManager:
    """WebSocketClient가 사용하는 매니저 반환"""
    return await get_global_websocket_manager()
