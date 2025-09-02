"""
WebSocket v6.0 설정 및 예외 관리
==============================

config.py + exceptions.py 통합 모듈
- 환경별 설정 관리
- 예외 체계 정의
- 설정 검증 및 로딩
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("WebSocketConfig")


# ================================================================
# 예외 클래스들
# ================================================================

class WebSocketException(Exception):
    """WebSocket v6 기본 예외"""
    pass


class ConnectionError(WebSocketException):
    """연결 관련 예외"""
    pass


class SubscriptionError(WebSocketException):
    """구독 관련 예외"""
    pass


class AuthenticationError(WebSocketException):
    """인증 관련 예외"""
    pass


class BackpressureError(WebSocketException):
    """백프레셔 관련 예외"""
    pass


class RecoveryError(WebSocketException):
    """복구 관련 예외"""
    pass


# ================================================================
# 설정 열거형
# ================================================================

class Environment(Enum):
    """실행 환경"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


# ================================================================
# 설정 데이터 클래스들
# ================================================================

@dataclass
class ConnectionConfig:
    """연결 설정"""
    public_url: str = "wss://api.upbit.com/websocket/v1"
    private_url: str = "wss://api.upbit.com/websocket/v1"
    connect_timeout: float = 10.0
    heartbeat_interval: float = 30.0
    enable_compression: bool = True
    max_message_size: int = 1024 * 1024  # 1MB

    def validate(self) -> None:
        """설정 검증"""
        if not self.public_url.startswith("wss://"):
            raise ValueError("public_url은 wss:// 형식이어야 합니다")
        if not self.private_url.startswith("wss://"):
            raise ValueError("private_url은 wss:// 형식이어야 합니다")
        if self.connect_timeout <= 0:
            raise ValueError("connect_timeout은 양수여야 합니다")
        if self.heartbeat_interval <= 0:
            raise ValueError("heartbeat_interval은 양수여야 합니다")


@dataclass
class ReconnectionConfig:
    """재연결 설정"""
    max_attempts: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

    def validate(self) -> None:
        """설정 검증"""
        if self.max_attempts < 0:
            raise ValueError("max_attempts는 0 이상이어야 합니다")
        if self.base_delay <= 0:
            raise ValueError("base_delay는 양수여야 합니다")
        if self.max_delay <= 0:
            raise ValueError("max_delay는 양수여야 합니다")
        if self.exponential_base <= 1:
            raise ValueError("exponential_base는 1보다 커야 합니다")


@dataclass
class AuthConfig:
    """인증 설정"""
    jwt_refresh_threshold: float = 300.0  # 5분 전 갱신
    max_auth_retries: int = 3
    auth_timeout: float = 5.0

    def validate(self) -> None:
        """설정 검증"""
        if self.jwt_refresh_threshold <= 0:
            raise ValueError("jwt_refresh_threshold는 양수여야 합니다")
        if self.max_auth_retries < 0:
            raise ValueError("max_auth_retries는 0 이상이어야 합니다")
        if self.auth_timeout <= 0:
            raise ValueError("auth_timeout은 양수여야 합니다")


@dataclass
class MonitoringConfig:
    """모니터링 설정"""
    enable_health_check: bool = True
    health_check_interval: float = 30.0
    enable_performance_metrics: bool = True
    metrics_update_interval: float = 10.0
    enable_connection_metrics: bool = True
    cleanup_interval: float = 60.0

    def validate(self) -> None:
        """설정 검증"""
        if self.health_check_interval <= 0:
            raise ValueError("health_check_interval은 양수여야 합니다")
        if self.metrics_update_interval <= 0:
            raise ValueError("metrics_update_interval은 양수여야 합니다")
        if self.cleanup_interval <= 0:
            raise ValueError("cleanup_interval은 양수여야 합니다")


@dataclass
class WebSocketConfig:
    """WebSocket v6 통합 설정"""
    environment: Environment = Environment.DEVELOPMENT
    connection: ConnectionConfig = field(default_factory=ConnectionConfig)
    reconnection: ReconnectionConfig = field(default_factory=ReconnectionConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    def validate(self) -> None:
        """전체 설정 검증"""
        self.connection.validate()
        self.reconnection.validate()
        self.auth.validate()
        self.monitoring.validate()

    def apply_environment_overrides(self) -> None:
        """환경변수 오버라이드 적용"""
        # 연결 설정
        if public_url := os.getenv('UPBIT_WEBSOCKET_PUBLIC_URL'):
            self.connection.public_url = public_url
        if private_url := os.getenv('UPBIT_WEBSOCKET_PRIVATE_URL'):
            self.connection.private_url = private_url
        if timeout := os.getenv('UPBIT_WEBSOCKET_TIMEOUT'):
            try:
                self.connection.connect_timeout = float(timeout)
            except ValueError:
                logger.warning(f"잘못된 UPBIT_WEBSOCKET_TIMEOUT 값: {timeout}")

        # 재연결 설정
        if max_attempts := os.getenv('UPBIT_WEBSOCKET_MAX_ATTEMPTS'):
            try:
                self.reconnection.max_attempts = int(max_attempts)
            except ValueError:
                logger.warning(f"잘못된 UPBIT_WEBSOCKET_MAX_ATTEMPTS 값: {max_attempts}")

        # 압축 설정
        if compression := os.getenv('UPBIT_WEBSOCKET_COMPRESSION'):
            self.connection.enable_compression = compression.lower() in ('true', '1', 'yes')

    def to_dict(self) -> Dict[str, Any]:
        """Dict 형식으로 변환"""
        return {
            'environment': self.environment.value,
            'connection': {
                'public_url': self.connection.public_url,
                'private_url': self.connection.private_url,
                'connect_timeout': self.connection.connect_timeout,
                'heartbeat_interval': self.connection.heartbeat_interval,
                'enable_compression': self.connection.enable_compression,
                'max_message_size': self.connection.max_message_size
            },
            'reconnection': {
                'max_attempts': self.reconnection.max_attempts,
                'base_delay': self.reconnection.base_delay,
                'max_delay': self.reconnection.max_delay,
                'exponential_base': self.reconnection.exponential_base,
                'jitter': self.reconnection.jitter
            },
            'auth': {
                'jwt_refresh_threshold': self.auth.jwt_refresh_threshold,
                'max_auth_retries': self.auth.max_auth_retries,
                'auth_timeout': self.auth.auth_timeout
            },
            'monitoring': {
                'enable_health_check': self.monitoring.enable_health_check,
                'health_check_interval': self.monitoring.health_check_interval,
                'enable_performance_metrics': self.monitoring.enable_performance_metrics,
                'metrics_update_interval': self.monitoring.metrics_update_interval,
                'enable_connection_metrics': self.monitoring.enable_connection_metrics,
                'cleanup_interval': self.monitoring.cleanup_interval
            }
        }


# ================================================================
# 환경별 설정 팩토리
# ================================================================

def create_development_config() -> WebSocketConfig:
    """개발 환경 설정"""
    config = WebSocketConfig(environment=Environment.DEVELOPMENT)

    # 개발 환경 최적화
    config.connection.connect_timeout = 5.0
    config.connection.heartbeat_interval = 20.0
    config.reconnection.max_attempts = 3
    config.reconnection.base_delay = 0.5
    config.monitoring.health_check_interval = 15.0
    config.monitoring.metrics_update_interval = 5.0

    return config


def create_testing_config() -> WebSocketConfig:
    """테스트 환경 설정"""
    config = WebSocketConfig(environment=Environment.TESTING)

    # 테스트 환경 최적화
    config.connection.connect_timeout = 3.0
    config.connection.heartbeat_interval = 10.0
    config.reconnection.max_attempts = 1
    config.reconnection.base_delay = 0.1
    config.monitoring.health_check_interval = 5.0
    config.monitoring.metrics_update_interval = 1.0

    return config


def create_production_config() -> WebSocketConfig:
    """프로덕션 환경 설정"""
    config = WebSocketConfig(environment=Environment.PRODUCTION)

    # 프로덕션 환경 최적화
    config.connection.connect_timeout = 15.0
    config.connection.heartbeat_interval = 60.0
    config.reconnection.max_attempts = 10
    config.reconnection.base_delay = 2.0
    config.reconnection.max_delay = 300.0
    config.monitoring.health_check_interval = 60.0
    config.monitoring.metrics_update_interval = 30.0

    return config


# ================================================================
# 설정 로딩 및 관리
# ================================================================

def load_config_from_env() -> WebSocketConfig:
    """환경변수에서 설정 로딩"""
    env_name = os.getenv('UPBIT_ENVIRONMENT', 'development').lower()

    try:
        environment = Environment(env_name)
    except ValueError:
        logger.warning(f"알 수 없는 환경: {env_name}, development로 설정")
        environment = Environment.DEVELOPMENT

    # 환경별 기본 설정 생성
    if environment == Environment.DEVELOPMENT:
        config = create_development_config()
    elif environment == Environment.TESTING:
        config = create_testing_config()
    elif environment == Environment.PRODUCTION:
        config = create_production_config()
    else:
        config = WebSocketConfig(environment=environment)

    # 환경변수 오버라이드 적용
    config.apply_environment_overrides()

    # 설정 검증
    try:
        config.validate()
    except Exception as e:
        logger.error(f"설정 검증 실패: {e}")
        raise

    logger.info(f"WebSocket 설정 로딩 완료: {environment.value}")
    return config


# ================================================================
# 전역 설정 인스턴스
# ================================================================

_global_config: Optional[WebSocketConfig] = None


def get_config() -> WebSocketConfig:
    """전역 설정 인스턴스 반환"""
    global _global_config

    if _global_config is None:
        _global_config = load_config_from_env()

    return _global_config


def reset_config() -> None:
    """설정 초기화 (테스트용)"""
    global _global_config
    _global_config = None


def set_config(config: WebSocketConfig) -> None:
    """설정 직접 설정 (테스트용)"""
    global _global_config
    _global_config = config


# ================================================================
# 편의 함수들
# ================================================================

def is_development() -> bool:
    """개발 환경 여부"""
    return get_config().environment == Environment.DEVELOPMENT


def is_production() -> bool:
    """프로덕션 환경 여부"""
    return get_config().environment == Environment.PRODUCTION


def get_connection_config() -> ConnectionConfig:
    """연결 설정 반환"""
    return get_config().connection


def get_reconnection_config() -> ReconnectionConfig:
    """재연결 설정 반환"""
    return get_config().reconnection
