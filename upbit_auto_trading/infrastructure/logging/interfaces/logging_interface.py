"""
Infrastructure Layer - Logging Interface
=======================================

로깅 서비스 추상화 인터페이스
Clean Architecture의 Dependency Inversion Principle 적용
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, ContextManager
import logging
from enum import Enum

class LogContext(Enum):
    """로그 컨텍스트 - 사용 상황별 분류"""
    DEVELOPMENT = "development"    # 개발 중
    TESTING = "testing"           # 테스트 실행
    PRODUCTION = "production"     # 프로덕션 운영
    DEBUGGING = "debugging"       # 디버깅 중
    PERFORMANCE = "performance"   # 성능 측정
    EMERGENCY = "emergency"       # 응급 상황

class LogScope(Enum):
    """로그 스코프 - 출력 범위 제어"""
    SILENT = "silent"         # 오류만
    MINIMAL = "minimal"       # 경고 이상
    NORMAL = "normal"         # 정보 이상
    VERBOSE = "verbose"       # 디버그 포함
    DEBUG_ALL = "debug_all"   # 모든 로그

class ILoggingService(ABC):
    """
    로깅 서비스 인터페이스

    Infrastructure Layer의 핵심 횡단 관심사(Cross-cutting Concern)
    모든 계층에서 일관된 로깅 기능 제공
    """

    @abstractmethod
    def get_logger(self, component_name: str) -> logging.Logger:
        """
        컴포넌트별 로거 조회

        Args:
            component_name: 컴포넌트 이름 (예: "StrategyService", "UIManager")

        Returns:
            logging.Logger: 컴포넌트 전용 로거
        """
        pass

    @abstractmethod
    def set_context(self, context: LogContext) -> None:
        """
        로그 컨텍스트 설정

        Args:
            context: 로그 컨텍스트 (development, testing, production 등)
        """
        pass

    @abstractmethod
    def set_scope(self, scope: LogScope) -> None:
        """
        로그 스코프 설정

        Args:
            scope: 로그 스코프 (silent, minimal, normal, verbose, debug_all)
        """
        pass

    @abstractmethod
    def enable_feature_development(self, feature_name: str) -> ContextManager:
        """
        특정 기능 개발 모드 활성화

        with 문과 함께 사용하여 특정 기능 개발 시에만 상세 로그 출력

        Args:
            feature_name: 기능 이름

        Returns:
            ContextManager: 컨텍스트 매니저

        Example:
            >>> with logging_service.enable_feature_development("StrategyCreation"):
            ...     logger.debug("상세 개발 로그...")
        """
        pass

    @abstractmethod
    def get_current_context(self) -> LogContext:
        """
        현재 로그 컨텍스트 조회

        Returns:
            LogContext: 현재 설정된 로그 컨텍스트
        """
        pass

    @abstractmethod
    def get_current_scope(self) -> LogScope:
        """
        현재 로그 스코프 조회

        Returns:
            LogScope: 현재 설정된 로그 스코프
        """
        pass

    @abstractmethod
    def is_debug_enabled(self, component_name: str) -> bool:
        """
        특정 컴포넌트의 디버그 로깅 활성화 여부 확인

        Args:
            component_name: 컴포넌트 이름

        Returns:
            bool: 디버그 로깅 활성화 여부
        """
        pass

    @abstractmethod
    def configure_file_logging(self,
                              main_log_path: str,
                              session_log_path: Optional[str] = None,
                              enable_dual_logging: bool = True) -> None:
        """
        파일 로깅 설정

        Args:
            main_log_path: 메인 로그 파일 경로
            session_log_path: 세션별 로그 파일 경로 (선택적)
            enable_dual_logging: 듀얼 로깅 활성화 여부
        """
        pass

    @abstractmethod
    def get_log_statistics(self) -> dict:
        """
        로깅 통계 정보 조회

        Returns:
            dict: 로그 레벨별 통계, 파일 크기 등
        """
        pass

class IContextManager(ABC):
    """기능별 개발 모드 컨텍스트 매니저 인터페이스"""

    @abstractmethod
    def __enter__(self):
        """컨텍스트 진입"""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 종료"""
        pass
