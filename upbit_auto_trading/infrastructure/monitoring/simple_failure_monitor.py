"""
SimpleFailureMonitor 클래스

API 호출 실패 감지 및 연속 실패 모니터링을 담당하는 경량 모니터링 시스템
"""

import threading
from typing import Optional, Callable
from upbit_auto_trading.infrastructure.logging import create_component_logger


class SimpleFailureMonitor:
    """
    간단한 실패 모니터링 클래스

    API 호출 결과를 추적하여 연속 실패 시 상태를 업데이트합니다.
    성능 최적화를 위해 최소한의 오버헤드로 설계되었습니다.
    """

    def __init__(self,
                 failure_threshold: int = 3,
                 status_callback: Optional[Callable[[bool], None]] = None,
                 enable_logging: bool = True):
        """
        초기화

        Args:
            failure_threshold (int): 연속 실패 임계값 (기본: 3회)
            status_callback (Callable[[bool], None], optional): 상태 변경 콜백 함수
            enable_logging (bool): 로깅 활성화 여부 (성능 최적화용)
        """
        self.failure_threshold = failure_threshold
        self.status_callback = status_callback
        self.consecutive_failures = 0
        self._is_failed_state = False
        self._lock = threading.RLock()  # 스레드 안전성을 위한 락

        # 성능 최적화를 위한 조건부 로깅
        self.enable_logging = enable_logging
        if enable_logging:
            self.logger = create_component_logger("SimpleFailureMonitor")
        else:
            self.logger = None

        # 성능 측정용 카운터
        self._total_calls = 0
        self._success_calls = 0

    def _log_debug(self, message: str) -> None:
        """조건부 디버그 로깅"""
        if self.logger:
            self.logger.debug(message)

    def _log_info(self, message: str) -> None:
        """조건부 정보 로깅"""
        if self.logger:
            self.logger.info(message)

    def _log_warning(self, message: str) -> None:
        """조건부 경고 로깅"""
        if self.logger:
            self.logger.warning(message)

    def mark_api_result(self, success: bool) -> None:
        """
        API 호출 결과를 기록합니다.

        Args:
            success (bool): API 호출 성공 여부
        """
        with self._lock:
            self._total_calls += 1

            if success:
                self._success_calls += 1
                # 성공 시 연속 실패 카운터 리셋
                if self.consecutive_failures > 0:
                    self.consecutive_failures = 0
                    self._log_debug("API 성공, 실패 카운터 리셋")

                # 실패 상태에서 복구됨
                if self._is_failed_state:
                    self._is_failed_state = False
                    self._log_info(f"API 연결 복구 감지 (총 호출: {self._total_calls})")
                    if self.status_callback:
                        self.status_callback(True)  # 연결 복구
            else:
                # 실패 카운터 증가
                self.consecutive_failures += 1
                self._log_debug(f"API 실패 #{self.consecutive_failures}")

                # 임계값 도달 시 실패 상태로 전환
                if (self.consecutive_failures >= self.failure_threshold and
                        not self._is_failed_state):
                    self._is_failed_state = True
                    self._log_warning(
                        f"API 연속 {self.consecutive_failures}회 실패 감지 "
                        f"(성공률: {self.get_success_rate():.1f}%)"
                    )
                    if self.status_callback:
                        self.status_callback(False)  # 연결 실패

    def get_success_rate(self) -> float:
        """
        현재까지의 API 성공률을 반환합니다.

        Returns:
            float: 성공률 (0.0 ~ 100.0)
        """
        if self._total_calls == 0:
            return 100.0
        return (self._success_calls / self._total_calls) * 100.0

    def get_statistics(self) -> dict:
        """
        모니터링 통계를 반환합니다.

        Returns:
            dict: 통계 정보
        """
        return {
            'total_calls': self._total_calls,
            'success_calls': self._success_calls,
            'consecutive_failures': self.consecutive_failures,
            'success_rate': self.get_success_rate(),
            'is_failed_state': self._is_failed_state,
            'failure_threshold': self.failure_threshold
        }

    def reset_statistics(self) -> None:
        """
        통계를 초기화합니다.
        """
        with self._lock:
            self.consecutive_failures = 0
            self._is_failed_state = False
            self._total_calls = 0
            self._success_calls = 0
            self._log_info("모니터링 통계 초기화")

    def is_healthy(self) -> bool:
        """
        현재 API 상태가 건강한지 확인합니다.

        Returns:
            bool: 건강한 상태 여부
        """
        return not self._is_failed_state

    def __repr__(self) -> str:
        """문자열 표현"""
        stats = self.get_statistics()
        return (
            f"SimpleFailureMonitor("
            f"failures={stats['consecutive_failures']}, "
            f"success_rate={stats['success_rate']:.1f}%, "
            f"healthy={self.is_healthy()})"
        )


class GlobalAPIMonitor:
    """
    전역 API 모니터링 싱글톤 클래스

    애플리케이션 전체에서 하나의 모니터링 인스턴스를 공유합니다.
    """

    _instance: Optional[SimpleFailureMonitor] = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls,
                    failure_threshold: int = 3,
                    status_callback: Optional[Callable[[bool], None]] = None) -> SimpleFailureMonitor:
        """
        싱글톤 인스턴스를 반환합니다.

        Args:
            failure_threshold (int): 연속 실패 임계값
            status_callback (Callable[[bool], None], optional): 상태 변경 콜백

        Returns:
            SimpleFailureMonitor: 모니터링 인스턴스
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = SimpleFailureMonitor(
                        failure_threshold=failure_threshold,
                        status_callback=status_callback
                    )
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """싱글톤 인스턴스를 초기화합니다 (테스트용)"""
        with cls._lock:
            cls._instance = None


# 편의 함수들
def mark_api_success() -> None:
    """API 성공을 전역 모니터에 기록"""
    GlobalAPIMonitor.get_instance().mark_api_result(True)


def mark_api_failure() -> None:
    """API 실패를 전역 모니터에 기록"""
    GlobalAPIMonitor.get_instance().mark_api_result(False)


def get_api_statistics() -> dict:
    """전역 API 통계를 반환"""
    return GlobalAPIMonitor.get_instance().get_statistics()


def is_api_healthy() -> bool:
    """전역 API 상태가 건강한지 확인"""
    return GlobalAPIMonitor.get_instance().is_healthy()
