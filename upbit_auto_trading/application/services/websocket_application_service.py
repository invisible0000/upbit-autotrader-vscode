"""
WebSocket Application Service (DDD 아키텍처 통합)
==================================================

WebSocket v6.0 Infrastructure Layer를 Application Layer에서 관리하는 서비스
프로그램 시작 시 자동 초기화 및 생명주기 관리
DDD 계층 경계를 준수하며 Infrastructure의 WebSocketManager를 추상화
"""

import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass

from upbit_auto_trading.application.services.base_application_service import BaseApplicationService
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket.core.websocket_manager import (
    WebSocketManager, get_websocket_manager
)
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket.core.websocket_types import (
    HealthStatus
)
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket.core.websocket_client import (
    WebSocketClient
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
    - WebSocket Manager 생명주기 관리 (Infrastructure Layer 추상화)
    - Application Layer에서 WebSocket 기능 제공
    - 다른 Application Service들이 실시간 데이터를 쉽게 구독할 수 있도록 지원
    - DDD 계층 간 경계 준수 (Infrastructure -> Application)
    """

    def __init__(self, config: Optional[WebSocketServiceConfig] = None):
        super().__init__()
        self.logger = create_component_logger("WebSocketApplicationService")

        # 설정
        self.config = config or WebSocketServiceConfig()

        # Infrastructure Layer WebSocket Manager (싱글톤 패턴)
        self._manager: Optional[WebSocketManager] = None

        # Application Layer 클라이언트들 (컴포넌트별 관리)
        self._clients: Dict[str, WebSocketClient] = {}

        # 서비스 상태
        self._is_initialized = False
        self._is_running = False

        # 헬스 체크 태스크
        self._health_check_task: Optional[asyncio.Task] = None

        # 구독 상태 추적 (Application Layer 레벨)
        self._active_subscriptions: Dict[str, Dict] = {}

        self.logger.info("WebSocket Application Service 생성 완료")

    async def initialize(self) -> bool:
        """
        서비스 초기화
        프로그램 시작 시 호출되어야 함
        """
        if self._is_initialized:
            self.logger.warning("이미 초기화된 서비스")
            return True

        try:
            self.logger.info("🚀 WebSocket Application Service 초기화 시작")

            # Infrastructure Layer WebSocket Manager 획득 (싱글톤)
            self._manager = await get_websocket_manager()

            if not self._manager:
                self.logger.error("WebSocket Manager 획득 실패")
                return False

            self.logger.debug("✅ WebSocket Manager 연결 완료")

            # 자동 시작 설정
            if self.config.auto_start_on_init:
                await self.start()

            self._is_initialized = True
            self.logger.info("✅ WebSocket Application Service 초기화 완료")
            return True

        except Exception as e:
            self.logger.error(f"❌ WebSocket Application Service 초기화 실패: {e}")
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
            self.logger.info("🔄 WebSocket Application Service 시작")

            # Infrastructure Manager 시작
            if self._manager:
                await self._manager.start()
                self.logger.debug("✅ Infrastructure WebSocket Manager 시작 완료")

            # 헬스 체크 시작
            if self.config.health_check_interval > 0:
                self._start_health_check()

            self._is_running = True
            self.logger.info("✅ WebSocket Application Service 시작 완료")
            return True

        except Exception as e:
            self.logger.error(f"❌ WebSocket Application Service 시작 실패: {e}")
            return False

    async def stop(self) -> None:
        """서비스 중지"""
        if not self._is_running:
            return

        try:
            self.logger.info("🔄 WebSocket Application Service 중지 시작")

            # 헬스 체크 중지
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            # 모든 구독 및 클라이언트 정리
            await self._cleanup_all_clients()

            # Infrastructure Manager 중지
            if self._manager:
                await self._manager.stop()

            self._is_running = False
            self.logger.info("✅ WebSocket Application Service 중지 완료")

        except Exception as e:
            self.logger.error(f"❌ 서비스 중지 중 오류: {e}")

    # ================================================================
    # Public API - 다른 Application Service에서 사용
    # ================================================================

    async def create_client(self, component_id: str) -> Optional[WebSocketClient]:
        """
        새로운 WebSocket 클라이언트 생성

        Args:
            component_id: 컴포넌트 고유 식별자 (예: "chart_btc", "dashboard_main")

        Returns:
            WebSocketClient 인스턴스 또는 None (실패 시)
        """
        if not self._is_running:
            self.logger.error("서비스가 실행되지 않음")
            return None

        try:
            if component_id in self._clients:
                self.logger.warning(f"이미 존재하는 클라이언트: {component_id}")
                return self._clients[component_id]

            # 새 클라이언트 생성
            client = WebSocketClient(component_id)
            self._clients[component_id] = client

            self.logger.info(f"✅ WebSocket 클라이언트 생성 완료: {component_id}")
            return client

        except Exception as e:
            self.logger.error(f"❌ 클라이언트 생성 실패 ({component_id}): {e}")
            return None

    async def remove_client(self, component_id: str) -> bool:
        """
        WebSocket 클라이언트 제거

        Args:
            component_id: 제거할 컴포넌트 식별자

        Returns:
            성공 여부
        """
        try:
            if component_id not in self._clients:
                self.logger.warning(f"존재하지 않는 클라이언트: {component_id}")
                return True

            # 클라이언트 정리
            client = self._clients[component_id]
            await client.cleanup()

            # 추적에서 제거
            del self._clients[component_id]

            self.logger.info(f"✅ WebSocket 클라이언트 제거 완료: {component_id}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 클라이언트 제거 실패 ({component_id}): {e}")
            return False

    async def get_client(self, component_id: str) -> Optional[WebSocketClient]:
        """기존 WebSocket 클라이언트 조회"""
        return self._clients.get(component_id)

    async def get_service_status(self) -> Dict[str, Any]:
        """서비스 상태 조회"""
        try:
            status = {
                'is_initialized': self._is_initialized,
                'is_running': self._is_running,
                'active_clients_count': len(self._clients),
                'active_clients': list(self._clients.keys()),
                'config': {
                    'auto_start': self.config.auto_start_on_init,
                    'public_enabled': self.config.enable_public_connection,
                    'private_enabled': self.config.enable_private_connection,
                    'health_check_interval': self.config.health_check_interval
                }
            }

            # Infrastructure Manager 상태 추가
            if self._manager:
                health_status = self._manager.get_health_status()
                status.update({
                    'infrastructure_health': health_status.status if health_status else 'unknown',
                    'infrastructure_details': {
                        'total_messages': health_status.total_messages_processed if health_status else 0,
                        'connection_errors': health_status.connection_errors if health_status else 0,
                        'last_error': health_status.last_error if health_status else None
                    }
                })

            return status

        except Exception as e:
            self.logger.error(f"❌ 상태 조회 실패: {e}")
            return {'error': str(e)}

    async def get_health_status(self) -> Dict[str, Any]:
        """헬스 상태 조회"""
        try:
            if not self._manager:
                return {'status': 'unhealthy', 'reason': 'manager_not_available'}

            health = self._manager.get_health_status()

            return {
                'status': 'healthy' if self._is_running else 'stopped',
                'infrastructure_health': health.status if health else 'unknown',
                'clients_count': len(self._clients),
                'is_running': self._is_running
            }

        except Exception as e:
            self.logger.error(f"❌ 헬스 상태 조회 실패: {e}")
            return {'status': 'error', 'error': str(e)}

    # ================================================================
    # Private Methods
    # ================================================================

    def _start_health_check(self) -> None:
        """헬스 체크 태스크 시작"""
        async def health_check_loop():
            while self._is_running:
                try:
                    await asyncio.sleep(self.config.health_check_interval)

                    if self._manager:
                        health = self._manager.get_health_status()
                        if health and health.status != "healthy":
                            self.logger.warning(f"WebSocket Infrastructure 상태 이상: {health.status}")

                            # 재연결 시도
                            if self.config.reconnect_on_failure:
                                await self._attempt_reconnection()

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"❌ 헬스 체크 중 오류: {e}")

        self._health_check_task = asyncio.create_task(health_check_loop())
        self.logger.debug("✅ 헬스 체크 태스크 시작")

    async def _attempt_reconnection(self) -> None:
        """재연결 시도"""
        try:
            self.logger.info("🔄 WebSocket 재연결 시도")

            if self._manager:
                # Infrastructure Manager를 통한 재시작 (stop -> start)
                await self._manager.stop()
                await self._manager.start()
                self.logger.info("✅ WebSocket 재연결 완료")

        except Exception as e:
            self.logger.error(f"❌ 재연결 시도 실패: {e}")

    async def _cleanup_all_clients(self) -> None:
        """모든 클라이언트 정리"""
        try:
            client_ids = list(self._clients.keys())

            for client_id in client_ids:
                await self.remove_client(client_id)

            self.logger.info(f"✅ 모든 클라이언트 정리 완료 - {len(client_ids)}개")

        except Exception as e:
            self.logger.error(f"❌ 클라이언트 정리 실패: {e}")


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
