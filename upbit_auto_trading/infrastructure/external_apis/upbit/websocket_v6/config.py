"""
WebSocket v6.0 설정 관리
======================

WebSocket v6 시스템의 설정 관리
환경별 설정, 기본값, 검증 로직 포함

설정 영역:
- 연결 설정 (URL, 타임아웃)
- 재연결 설정 (백오프, 최대 시도)
- 백프레셔 설정 (큐 크기, 전략)
- Private 인증 설정 (JWT)
- 성능 모니터링 설정
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any
from enum import Enum

from .types import BackpressureConfig, BackpressureStrategy


class Environment(Enum):
    """실행 환경"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class ConnectionConfig:
    """연결 설정"""
    public_url: str = "wss://api.upbit.com/websocket/v1"
    private_url: str = "wss://api.upbit.com/websocket/v1"
    connect_timeout: float = 10.0
    heartbeat_interval: float = 30.0
    enable_compression: bool = True
    enable_simple_format: bool = False

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
    jitter_range: tuple = (0.1, 0.5)  # 10%~50% 지터

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
        if len(self.jitter_range) != 2:
            raise ValueError("jitter_range는 (min, max) 튜플이어야 합니다")


@dataclass
class AuthConfig:
    """인증 설정 (Private WebSocket)"""
    jwt_refresh_threshold: float = 0.8  # 80% 만료 시점에 갱신
    jwt_refresh_retry_count: int = 3
    jwt_refresh_timeout: float = 10.0
    fallback_to_rest: bool = True  # JWT 실패 시 REST API 폴백

    def validate(self) -> None:
        """설정 검증"""
        if not (0.0 < self.jwt_refresh_threshold < 1.0):
            raise ValueError("jwt_refresh_threshold는 0과 1 사이여야 합니다")
        if self.jwt_refresh_retry_count < 0:
            raise ValueError("jwt_refresh_retry_count는 0 이상이어야 합니다")
        if self.jwt_refresh_timeout <= 0:
            raise ValueError("jwt_refresh_timeout은 양수여야 합니다")


@dataclass
class MonitoringConfig:
    """모니터링 설정"""
    metrics_collection_interval: float = 10.0
    health_check_interval: float = 30.0
    performance_window_size: int = 100  # 성능 메트릭 윈도우 크기

    # 알림 임계값
    alert_error_rate_threshold: float = 0.05  # 5% 에러율
    alert_latency_threshold_ms: float = 1000.0  # 1초 지연
    alert_queue_threshold: float = 0.8  # 큐 80% 사용률
    alert_reconnect_threshold: int = 3  # 3회 이상 재연결

    def validate(self) -> None:
        """설정 검증"""
        if self.metrics_collection_interval <= 0:
            raise ValueError("metrics_collection_interval은 양수여야 합니다")
        if self.health_check_interval <= 0:
            raise ValueError("health_check_interval은 양수여야 합니다")
        if self.performance_window_size <= 0:
            raise ValueError("performance_window_size는 양수여야 합니다")


@dataclass
class SubscriptionConfig:
    """구독 설정"""
    max_symbols_per_request: int = 100  # 업비트 제한
    subscription_timeout: float = 30.0
    auto_cleanup_interval: float = 300.0  # 5분마다 자동 정리
    grace_period: float = 30.0  # 구독 해제 후 대기 시간

    def validate(self) -> None:
        """설정 검증"""
        if self.max_symbols_per_request <= 0:
            raise ValueError("max_symbols_per_request는 양수여야 합니다")
        if self.subscription_timeout <= 0:
            raise ValueError("subscription_timeout은 양수여야 합니다")
        if self.auto_cleanup_interval <= 0:
            raise ValueError("auto_cleanup_interval은 양수여야 합니다")
        if self.grace_period < 0:
            raise ValueError("grace_period는 0 이상이어야 합니다")


@dataclass
class WebSocketV6Config:
    """WebSocket v6 통합 설정"""
    environment: Environment = Environment.DEVELOPMENT
    connection: ConnectionConfig = field(default_factory=ConnectionConfig)
    reconnection: ReconnectionConfig = field(default_factory=ReconnectionConfig)
    backpressure: BackpressureConfig = field(default_factory=BackpressureConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    subscription: SubscriptionConfig = field(default_factory=SubscriptionConfig)

    # 디버깅 옵션
    debug_mode: bool = False
    log_level: str = "INFO"
    log_websocket_messages: bool = False

    def validate(self) -> None:
        """전체 설정 검증"""
        self.connection.validate()
        self.reconnection.validate()
        self.auth.validate()
        self.monitoring.validate()
        self.subscription.validate()

        # 크로스 검증
        if self.reconnection.max_delay < self.reconnection.base_delay:
            raise ValueError("max_delay는 base_delay보다 커야 합니다")

    def apply_environment_overrides(self) -> None:
        """환경별 설정 오버라이드 적용"""
        if self.environment == Environment.DEVELOPMENT:
            self.debug_mode = True
            self.log_level = "DEBUG"
            self.log_websocket_messages = True
            self.reconnection.max_attempts = 3  # 개발 환경에서는 빠른 실패

        elif self.environment == Environment.TESTING:
            self.debug_mode = True
            self.log_level = "DEBUG"
            self.connection.connect_timeout = 5.0  # 테스트 환경에서는 빠른 타임아웃
            self.reconnection.max_attempts = 2

        elif self.environment == Environment.STAGING:
            self.debug_mode = False
            self.log_level = "INFO"
            self.log_websocket_messages = False

        elif self.environment == Environment.PRODUCTION:
            self.debug_mode = False
            self.log_level = "WARNING"
            self.log_websocket_messages = False
            self.reconnection.max_attempts = 10  # 프로덕션에서는 더 많은 재시도
            self.monitoring.alert_error_rate_threshold = 0.01  # 더 엄격한 알림

    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 변환"""
        return {
            'environment': self.environment.value,
            'connection': {
                'public_url': self.connection.public_url,
                'private_url': self.connection.private_url,
                'connect_timeout': self.connection.connect_timeout,
                'heartbeat_interval': self.connection.heartbeat_interval,
                'enable_compression': self.connection.enable_compression,
                'enable_simple_format': self.connection.enable_simple_format,
            },
            'reconnection': {
                'max_attempts': self.reconnection.max_attempts,
                'base_delay': self.reconnection.base_delay,
                'max_delay': self.reconnection.max_delay,
                'exponential_base': self.reconnection.exponential_base,
                'jitter': self.reconnection.jitter,
            },
            'backpressure': {
                'strategy': self.backpressure.strategy.value,
                'max_queue_size': self.backpressure.max_queue_size,
                'warning_threshold': self.backpressure.warning_threshold,
            },
            'auth': {
                'jwt_refresh_threshold': self.auth.jwt_refresh_threshold,
                'jwt_refresh_retry_count': self.auth.jwt_refresh_retry_count,
                'fallback_to_rest': self.auth.fallback_to_rest,
            },
            'monitoring': {
                'metrics_collection_interval': self.monitoring.metrics_collection_interval,
                'health_check_interval': self.monitoring.health_check_interval,
                'alert_error_rate_threshold': self.monitoring.alert_error_rate_threshold,
            },
            'subscription': {
                'max_symbols_per_request': self.subscription.max_symbols_per_request,
                'subscription_timeout': self.subscription.subscription_timeout,
                'auto_cleanup_interval': self.subscription.auto_cleanup_interval,
            },
            'debug': {
                'debug_mode': self.debug_mode,
                'log_level': self.log_level,
                'log_websocket_messages': self.log_websocket_messages,
            }
        }


# =============================================================================
# 설정 팩토리 함수
# =============================================================================

def create_default_config(environment: Environment = Environment.DEVELOPMENT) -> WebSocketV6Config:
    """기본 설정 생성"""
    config = WebSocketV6Config(environment=environment)
    config.apply_environment_overrides()
    config.validate()
    return config


def create_development_config() -> WebSocketV6Config:
    """개발 환경 설정"""
    config = WebSocketV6Config(environment=Environment.DEVELOPMENT)

    # 개발 환경 특화 설정
    config.debug_mode = True
    config.log_level = "DEBUG"
    config.log_websocket_messages = True

    # 빠른 피드백을 위한 설정
    config.connection.connect_timeout = 5.0
    config.reconnection.max_attempts = 3
    config.reconnection.base_delay = 0.5

    # 작은 큐 크기로 백프레셔 테스트
    config.backpressure.max_queue_size = 100
    config.backpressure.warning_threshold = 0.7

    config.validate()
    return config


def create_testing_config() -> WebSocketV6Config:
    """테스트 환경 설정"""
    config = WebSocketV6Config(environment=Environment.TESTING)

    # 테스트 환경 특화 설정
    config.debug_mode = True
    config.log_level = "DEBUG"

    # 빠른 실행을 위한 설정
    config.connection.connect_timeout = 3.0
    config.connection.heartbeat_interval = 10.0
    config.reconnection.max_attempts = 2
    config.reconnection.base_delay = 0.1
    config.reconnection.max_delay = 2.0

    # 테스트용 작은 값들
    config.backpressure.max_queue_size = 50
    config.monitoring.metrics_collection_interval = 1.0
    config.monitoring.health_check_interval = 5.0

    config.validate()
    return config


def create_production_config() -> WebSocketV6Config:
    """프로덕션 환경 설정"""
    config = WebSocketV6Config(environment=Environment.PRODUCTION)

    # 프로덕션 환경 특화 설정
    config.debug_mode = False
    config.log_level = "WARNING"
    config.log_websocket_messages = False

    # 안정성 우선 설정
    config.connection.connect_timeout = 15.0
    config.reconnection.max_attempts = 10
    config.reconnection.base_delay = 2.0
    config.reconnection.max_delay = 120.0

    # 큰 큐 크기로 안정성 확보
    config.backpressure.max_queue_size = 5000
    config.backpressure.warning_threshold = 0.9

    # 엄격한 모니터링
    config.monitoring.alert_error_rate_threshold = 0.01
    config.monitoring.alert_latency_threshold_ms = 500.0

    config.validate()
    return config


# =============================================================================
# 환경변수 기반 설정 로딩
# =============================================================================

def load_config_from_env() -> WebSocketV6Config:
    """환경변수에서 설정 로딩"""
    # 환경 결정
    env_name = os.getenv("UPBIT_ENVIRONMENT", "development").lower()
    try:
        environment = Environment(env_name)
    except ValueError:
        environment = Environment.DEVELOPMENT

    # 기본 설정 생성
    config = create_default_config(environment)

    # 환경변수 오버라이드
    if url := os.getenv("UPBIT_WEBSOCKET_PUBLIC_URL"):
        config.connection.public_url = url

    if url := os.getenv("UPBIT_WEBSOCKET_PRIVATE_URL"):
        config.connection.private_url = url

    if timeout := os.getenv("UPBIT_WEBSOCKET_CONNECT_TIMEOUT"):
        try:
            config.connection.connect_timeout = float(timeout)
        except ValueError:
            pass

    if attempts := os.getenv("UPBIT_WEBSOCKET_MAX_RECONNECT_ATTEMPTS"):
        try:
            config.reconnection.max_attempts = int(attempts)
        except ValueError:
            pass

    if queue_size := os.getenv("UPBIT_WEBSOCKET_MAX_QUEUE_SIZE"):
        try:
            config.backpressure.max_queue_size = int(queue_size)
        except ValueError:
            pass

    if strategy := os.getenv("UPBIT_WEBSOCKET_BACKPRESSURE_STRATEGY"):
        try:
            config.backpressure.strategy = BackpressureStrategy(strategy.lower())
        except ValueError:
            pass

    if debug := os.getenv("UPBIT_WEBSOCKET_DEBUG"):
        config.debug_mode = debug.lower() in ("true", "1", "yes", "on")

    if log_level := os.getenv("UPBIT_WEBSOCKET_LOG_LEVEL"):
        config.log_level = log_level.upper()

    config.validate()
    return config


def get_config() -> WebSocketV6Config:
    """설정 인스턴스 획득 (싱글톤 패턴)"""
    if not hasattr(get_config, '_instance'):
        get_config._instance = load_config_from_env()
    return get_config._instance


def reset_config() -> None:
    """설정 인스턴스 리셋 (테스트용)"""
    if hasattr(get_config, '_instance'):
        delattr(get_config, '_instance')
