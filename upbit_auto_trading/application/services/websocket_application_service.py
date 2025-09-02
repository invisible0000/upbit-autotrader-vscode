"""
WebSocket Application Service (DDD 아키텍처 통합)
==================================================

WebSocket v6.0 전역 관리자를 Application Layer에서 관리하는 서비스
프로그램 시작 시 자동 초기화 및 생명주기 관리
"""

import asyncio
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass

from upbit_auto_trading.application.services.base_application_service import BaseApplicationService
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v6 import (
    GlobalWebSocketManager,
    get_global_websocket_manager,
    BaseWebSocketEvent
)
from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass
class WebSocketServiceConfig:
    """WebSocket 서비스 설정"""
    auto_start_on_init: bool = True
    enable_public_connection: bool = True
    enable_private_connection: bool = True
    reconnect_on_failure: bool = True
    max_reconnect_attempts: int = 10
    health_check_interval: float = 30.0


class WebSocketApplicationService(BaseApplicationService):
    """
    WebSocket Application Service

    역할:
    - 전역 WebSocket Manager 생명주기 관리
    - Application Layer에서 WebSocket 기능 제공
    - 다른 Application Service들이 실시간 데이터를 쉽게 구독할 수 있도록 지원
    - DDD 계층 간 경계 준수
    """

    def __init__(self, config: Optional[WebSocketServiceConfig] = None):
        super().__init__()
        self.logger = create_component_logger("WebSocketApplicationService")

        # 설정
        self.config = config or WebSocketServiceConfig()

        # 전역 관리자
        self._global_manager: Optional[GlobalWebSocketManager] = None

        # 서비스 상태
        self._is_initialized = False
        self._is_running = False

        # 헬스 체크 태스크
        self._health_check_task: Optional[asyncio.Task] = None

        # 구독 상태 추적 (Application Layer 레벨)
        self._active_subscriptions: Dict[str, Dict] = {}

        self.logger.info("WebSocket Application Service 초기화 완료")

    async def initialize(self) -> bool:
        """
        서비스 초기화
        프로그램 시작 시 호출되어야 함
        """
        if self._is_initialized:
            self.logger.warning("이미 초기화된 서비스")
            return True

        try:
            self.logger.info("WebSocket Application Service 초기화 시작")

            # 전역 WebSocket Manager 획득
            self._global_manager = await get_global_websocket_manager()

            # 자동 시작 설정
            if self.config.auto_start_on_init:
                await self.start()

            self._is_initialized = True
            self.logger.info("✅ WebSocket Application Service 초기화 완료")
            return True

        except Exception as e:
            self.logger.error(f"WebSocket Application Service 초기화 실패: {e}")
            return False

    async def start(self) -> bool:
        """서비스 시작"""
        if not self._is_initialized:
            self.logger.error("서비스가 초기화되지 않음")
            return False

        if self._is_running:
            self.logger.warning("이미 실행 중인 서비스")
            return True

        try:
            self.logger.info("WebSocket Application Service 시작")

            # 연결 초기화
            if self.config.enable_public_connection:
                await self._ensure_public_connection()

            if self.config.enable_private_connection:
                await self._ensure_private_connection()

            # 헬스 체크 시작
            if self.config.health_check_interval > 0:
                self._start_health_check()

            self._is_running = True
            self.logger.info("✅ WebSocket Application Service 시작 완료")
            return True

        except Exception as e:
            self.logger.error(f"WebSocket Application Service 시작 실패: {e}")
            return False

    async def stop(self) -> None:
        """서비스 중지"""
        if not self._is_running:
            return

        try:
            self.logger.info("WebSocket Application Service 중지 시작")

            # 헬스 체크 중지
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            # 모든 구독 해제
            await self._cleanup_all_subscriptions()

            # 전역 관리자 정리
            if self._global_manager:
                await self._global_manager.shutdown(timeout=10.0)

            self._is_running = False
            self.logger.info("✅ WebSocket Application Service 중지 완료")

        except Exception as e:
            self.logger.error(f"서비스 중지 중 오류: {e}")

    # ================================================================
    # Public API - 다른 Application Service에서 사용
    # ================================================================

    async def subscribe_ticker(
        self,
        symbols: List[str],
        callback: Callable[[BaseWebSocketEvent], None],
        component_id: str = "default"
    ) -> Optional[str]:
        """
        현재가 데이터 구독

        Args:
            symbols: 구독할 심볼 리스트
            callback: 데이터 수신 콜백
            component_id: 구독 컴포넌트 식별자

        Returns:
            구독 ID (해제 시 사용)
        """
        if not self._is_running:
            self.logger.error("서비스가 실행되지 않음")
            return None

        try:
            # 전역 관리자를 통한 구독
            subscription_id = await self._global_manager.subscribe_ticker(symbols)

            if subscription_id:
                # Application Layer에서 구독 추적
                self._active_subscriptions[subscription_id] = {
                    'type': 'ticker',
                    'symbols': symbols,
                    'callback': callback,
                    'component_id': component_id
                }

                self.logger.info(f"✅ 현재가 구독 완료 - ID: {subscription_id}, 심볼: {symbols}")

            return subscription_id

        except Exception as e:
            self.logger.error(f"현재가 구독 실패: {e}")
            return None

    async def subscribe_orderbook(
        self,
        symbols: List[str],
        callback: Callable[[BaseWebSocketEvent], None],
        component_id: str = "default"
    ) -> Optional[str]:
        """호가창 데이터 구독"""
        if not self._is_running:
            self.logger.error("서비스가 실행되지 않음")
            return None

        try:
            subscription_id = await self._global_manager.subscribe_orderbook(symbols)

            if subscription_id:
                self._active_subscriptions[subscription_id] = {
                    'type': 'orderbook',
                    'symbols': symbols,
                    'callback': callback,
                    'component_id': component_id
                }

                self.logger.info(f"✅ 호가창 구독 완료 - ID: {subscription_id}, 심볼: {symbols}")

            return subscription_id

        except Exception as e:
            self.logger.error(f"호가창 구독 실패: {e}")
            return None

    async def unsubscribe(self, subscription_id: str) -> bool:
        """구독 해제"""
        try:
            # 전역 관리자에서 구독 해제
            success = await self._global_manager.unsubscribe(subscription_id)

            # Application Layer 추적 제거
            if subscription_id in self._active_subscriptions:
                del self._active_subscriptions[subscription_id]
                self.logger.info(f"✅ 구독 해제 완료 - ID: {subscription_id}")

            return success

        except Exception as e:
            self.logger.error(f"구독 해제 실패: {e}")
            return False

    async def get_service_status(self) -> Dict[str, Any]:
        """서비스 상태 조회"""
        try:
            status = {
                'is_initialized': self._is_initialized,
                'is_running': self._is_running,
                'active_subscriptions_count': len(self._active_subscriptions),
                'config': {
                    'auto_start': self.config.auto_start_on_init,
                    'public_enabled': self.config.enable_public_connection,
                    'private_enabled': self.config.enable_private_connection
                }
            }

            # 전역 관리자 상태 추가
            if self._global_manager:
                health_status = self._global_manager.get_health_status()
                # performance_metrics는 현재 WebSocketManager에 없으므로 제거

                status.update({
                    'global_manager_health': health_status.status,
                    'manager_state': self._global_manager.get_state().value if self._global_manager.get_state() else "unknown"
                })

            return status

        except Exception as e:
            self.logger.error(f"상태 조회 실패: {e}")
            return {'error': str(e)}

    # ================================================================
    # Private Methods
    # ================================================================

    async def _ensure_public_connection(self) -> bool:
        """Public 연결 보장"""
        try:
            if self._global_manager:
                # 연결 초기화 시도
                success = await self._global_manager.initialize_public_connection()
                if success:
                    self.logger.info("✅ Public 연결 초기화 완료")
                    return True
                else:
                    self.logger.warning("Public 연결 실패")
                    return False

            self.logger.warning("GlobalWebSocketManager가 없음")
            return False

        except Exception as e:
            self.logger.error(f"Public 연결 보장 실패: {e}")
            return False

    async def _ensure_private_connection(self) -> bool:
        """Private 연결 보장"""
        try:
            if self._global_manager:
                # Private API 지원 확인
                is_private_available = await self._global_manager.is_private_available()
                if not is_private_available:
                    self.logger.info("API 키 없음 - Private 연결 스킵")
                    return True

                # 연결 초기화 시도
                success = await self._global_manager.initialize_private_connection()
                if success:
                    self.logger.info("✅ Private 연결 초기화 완료")
                    return True
                else:
                    self.logger.warning("Private 연결 실패")
                    return False

            self.logger.warning("GlobalWebSocketManager가 없음")
            return False

        except Exception as e:
            self.logger.error(f"Private 연결 보장 실패: {e}")
            return False

    def _start_health_check(self) -> None:
        """헬스 체크 태스크 시작"""
        async def health_check_loop():
            while self._is_running:
                try:
                    await asyncio.sleep(self.config.health_check_interval)

                    if self._global_manager:
                        health_status = self._global_manager.get_health_status()
                        if health_status.status != "healthy":
                            self.logger.warning(f"WebSocket 상태 이상: {health_status.status}")

                            # 재연결 시도
                            if self.config.reconnect_on_failure:
                                await self._attempt_reconnection()

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"헬스 체크 중 오류: {e}")

        self._health_check_task = asyncio.create_task(health_check_loop())

    async def _attempt_reconnection(self) -> None:
        """재연결 시도"""
        try:
            self.logger.info("WebSocket 재연결 시도")

            # Public 연결 재시도
            if self.config.enable_public_connection:
                await self._ensure_public_connection()

            # Private 연결 재시도
            if self.config.enable_private_connection:
                await self._ensure_private_connection()

        except Exception as e:
            self.logger.error(f"재연결 시도 실패: {e}")

    async def _cleanup_all_subscriptions(self) -> None:
        """모든 구독 정리"""
        try:
            subscription_ids = list(self._active_subscriptions.keys())

            for subscription_id in subscription_ids:
                await self.unsubscribe(subscription_id)

            self.logger.info(f"✅ 모든 구독 정리 완료 - {len(subscription_ids)}개")

        except Exception as e:
            self.logger.error(f"구독 정리 실패: {e}")


# ================================================================
# 전역 서비스 인스턴스 (싱글톤 패턴)
# ================================================================

_global_websocket_service: Optional[WebSocketApplicationService] = None


async def get_websocket_service(
    config: Optional[WebSocketServiceConfig] = None
) -> WebSocketApplicationService:
    """전역 WebSocket Application Service 획득"""
    global _global_websocket_service

    if _global_websocket_service is None:
        _global_websocket_service = WebSocketApplicationService(config)
        await _global_websocket_service.initialize()

    return _global_websocket_service


async def shutdown_websocket_service() -> None:
    """전역 WebSocket Application Service 종료"""
    global _global_websocket_service

    if _global_websocket_service:
        await _global_websocket_service.stop()
        _global_websocket_service = None
