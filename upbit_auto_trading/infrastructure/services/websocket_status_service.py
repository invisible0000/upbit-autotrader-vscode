"""
WebSocket 상태 관리 서비스

웹소켓 클라이언트들의 연결 상태를 모니터링하고 UI에 상태를 제공하는
경량 서비스입니다. 리소스 효율성을 위해 최소한의 모니터링만 수행합니다.

Design Principles:
- 리소스 최소화: 주기적 폴링 대신 이벤트 기반 상태 업데이트
- 상태 캐싱: 빈번한 상태 조회 시 캐시된 값 반환
- 느슨한 결합: WebSocket 클라이언트와 독립적으로 동작
"""

from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
from upbit_auto_trading.infrastructure.logging import create_component_logger


class WebSocketStatus:
    """개별 웹소켓 연결 상태"""

    def __init__(self, client_name: str):
        self.client_name = client_name
        self.is_connected = False
        self.last_check_time = datetime.now()
        self.error_message = ""
        self.reconnect_count = 0

    def update(self, connected: bool, error_message: str = ""):
        """상태 업데이트"""
        self.is_connected = connected
        self.last_check_time = datetime.now()
        self.error_message = error_message
        if not connected:
            self.reconnect_count += 1

    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            'client_name': self.client_name,
            'is_connected': self.is_connected,
            'last_check_time': self.last_check_time.isoformat(),
            'error_message': self.error_message,
            'reconnect_count': self.reconnect_count
        }


class WebSocketStatusService:
    """
    웹소켓 상태 관리 서비스

    여러 웹소켓 클라이언트의 상태를 통합 관리하고
    UI 상태바에 표시할 요약 정보를 제공합니다.
    """

    def __init__(self):
        self.logger = create_component_logger("WebSocketStatusService")
        self._statuses: Dict[str, WebSocketStatus] = {}
        self._status_callbacks: Dict[str, Callable] = {}

        # 상태 캐시 (리소스 절약)
        self._cached_overall_status = False
        self._cache_timestamp = datetime.now()
        self._cache_ttl = timedelta(seconds=5)  # 5초 캐시

        self.logger.info("WebSocket 상태 서비스 초기화 완료")

    def register_client(self, client_name: str, status_callback: Optional[Callable] = None):
        """
        웹소켓 클라이언트 등록

        Args:
            client_name: 클라이언트 식별자 ('quotation', 'private' 등)
            status_callback: 상태 변경 시 호출할 콜백 함수
        """
        self._statuses[client_name] = WebSocketStatus(client_name)
        if status_callback:
            self._status_callbacks[client_name] = status_callback

        self.logger.debug(f"웹소켓 클라이언트 등록: {client_name}")

    def update_client_status(self, client_name: str, connected: bool, error_message: str = ""):
        """
        클라이언트 상태 업데이트

        Args:
            client_name: 클라이언트 식별자
            connected: 연결 상태
            error_message: 오류 메시지 (선택적)
        """
        if client_name not in self._statuses:
            self.logger.warning(f"등록되지 않은 클라이언트: {client_name}")
            return

        old_status = self._statuses[client_name].is_connected
        self._statuses[client_name].update(connected, error_message)

        # 상태 변경 시에만 로깅 및 콜백 호출
        if old_status != connected:
            status_text = "연결됨" if connected else "연결 끊김"
            self.logger.info(f"웹소켓 상태 변경: {client_name} -> {status_text}")

            # 상태 변경 콜백 호출
            if client_name in self._status_callbacks:
                try:
                    self._status_callbacks[client_name](connected)
                except Exception as e:
                    self.logger.error(f"상태 콜백 호출 실패: {e}")

        # 캐시 무효화
        self._invalidate_cache()

    def get_overall_status(self) -> bool:
        """
        전체 웹소켓 연결 상태 반환 (UI 상태바용)

        Returns:
            bool: 하나 이상의 웹소켓이 연결되어 있으면 True
        """
        # 캐시 확인
        if self._is_cache_valid():
            return self._cached_overall_status

        # 새로운 상태 계산
        if not self._statuses:
            overall_status = False  # 등록된 클라이언트가 없으면 미연결
        else:
            # 하나라도 연결되어 있으면 연결됨으로 표시
            overall_status = any(status.is_connected for status in self._statuses.values())

        # 캐시 업데이트
        self._cached_overall_status = overall_status
        self._cache_timestamp = datetime.now()

        return overall_status

    def get_detailed_status(self) -> Dict[str, dict]:
        """
        모든 클라이언트의 상세 상태 반환

        Returns:
            각 클라이언트의 상세 상태 정보
        """
        return {
            name: status.to_dict()
            for name, status in self._statuses.items()
        }

    def get_status_summary(self) -> str:
        """
        상태 요약 텍스트 반환 (툴팁용)

        Returns:
            str: 상태 요약 텍스트
        """
        if not self._statuses:
            return "웹소켓 기능이 현재 사용되지 않고 있습니다."

        connected_count = sum(1 for status in self._statuses.values() if status.is_connected)
        total_count = len(self._statuses)

        if connected_count == 0:
            return f"웹소켓 대기 중 (0/{total_count})"
        elif connected_count == total_count:
            return f"웹소켓 모두 활성 ({connected_count}/{total_count})"
        else:
            return f"웹소켓 부분 활성 ({connected_count}/{total_count})"

    def is_client_connected(self, client_name: str) -> bool:
        """특정 클라이언트 연결 상태 확인"""
        return self._statuses.get(client_name, WebSocketStatus(client_name)).is_connected

    def _is_cache_valid(self) -> bool:
        """캐시 유효성 확인"""
        return datetime.now() - self._cache_timestamp < self._cache_ttl

    def _invalidate_cache(self):
        """캐시 무효화"""
        self._cache_timestamp = datetime.now() - self._cache_ttl

    def clear_all_status(self):
        """모든 상태 초기화"""
        self._statuses.clear()
        self._status_callbacks.clear()
        self._invalidate_cache()
        self.logger.info("웹소켓 상태 서비스 초기화됨")


# 전역 인스턴스 (Singleton 패턴)
websocket_status_service = WebSocketStatusService()
