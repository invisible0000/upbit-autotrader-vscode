"""
WebSocket v6.0 설정 및 예외 관리
==============================

config.py + exceptions.py 통합 모듈
- 환경별 설정 관리
- 예외 체계 정의
- 설정 검증 및 로딩
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum
from pathlib import Path

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
    private_url: str = "wss://api.upbit.com/websocket/v1/private"  # Private 엔드포인트 분리
    connect_timeout: float = 10.0
    heartbeat_interval: float = 30.0
    enable_compression: bool = True  # 업비트 압축 기능 활성화
    max_message_size: int = 1024 * 1024  # 1MB
    compression_threshold: int = 1024  # 압축 임계값 (바이트)

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
        if self.compression_threshold < 0:
            raise ValueError("compression_threshold는 0 이상이어야 합니다")


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
class RateLimiterConfig:
    """Rate Limiter 설정"""
    enable_rate_limiter: bool = True
    enable_dynamic_adjustment: bool = True
    strategy: str = "balanced"  # conservative, balanced, aggressive
    error_threshold: int = 2
    reduction_ratio: float = 0.7
    recovery_delay: float = 120.0
    recovery_step: float = 0.15
    recovery_interval: float = 20.0

    def validate(self) -> None:
        """설정 검증"""
        if self.strategy not in ["conservative", "balanced", "aggressive"]:
            raise ValueError("strategy는 conservative, balanced, aggressive 중 하나여야 합니다")
        if self.error_threshold < 1:
            raise ValueError("error_threshold는 1 이상이어야 합니다")
        if not 0.1 <= self.reduction_ratio <= 1.0:
            raise ValueError("reduction_ratio는 0.1~1.0 사이여야 합니다")
        if self.recovery_delay <= 0:
            raise ValueError("recovery_delay는 양수여야 합니다")
        if not 0.01 <= self.recovery_step <= 1.0:
            raise ValueError("recovery_step은 0.01~1.0 사이여야 합니다")
        if self.recovery_interval <= 0:
            raise ValueError("recovery_interval은 양수여야 합니다")


@dataclass
class SimpleFormatConfig:
    """Simple Format 설정 (네트워크 사용량 최적화)"""
    enable_simple_mode: bool = False  # 기본값: 비활성화
    auto_convert_incoming: bool = True  # 수신 데이터 자동 변환
    force_simple_format: bool = False  # 모든 요청에 format=SIMPLE 강제 적용
    enable_compression_with_simple: bool = True  # SIMPLE 모드에서도 압축 사용
    debug_format_conversion: bool = False  # 포맷 변환 디버깅

    def validate(self) -> None:
        """설정 검증"""
        # Simple Mode가 활성화된 경우 auto_convert_incoming은 필수
        if self.enable_simple_mode and not self.auto_convert_incoming:
            logger.warning("Simple Mode 활성화 시 auto_convert_incoming 권장")

        # force_simple_format은 enable_simple_mode가 활성화된 경우에만 의미
        if self.force_simple_format and not self.enable_simple_mode:
            raise ValueError("force_simple_format은 enable_simple_mode가 활성화된 경우에만 사용 가능")


@dataclass
class WebSocketConfig:
    """WebSocket v6 통합 설정"""
    environment: Environment = Environment.DEVELOPMENT
    connection: ConnectionConfig = field(default_factory=ConnectionConfig)
    reconnection: ReconnectionConfig = field(default_factory=ReconnectionConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    rate_limiter: RateLimiterConfig = field(default_factory=RateLimiterConfig)
    simple_format: SimpleFormatConfig = field(default_factory=SimpleFormatConfig)

    def validate(self) -> None:
        """전체 설정 검증"""
        self.connection.validate()
        self.reconnection.validate()
        self.auth.validate()
        self.monitoring.validate()
        self.rate_limiter.validate()
        self.simple_format.validate()

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

        # 압축 임계값 설정
        if threshold := os.getenv('UPBIT_WEBSOCKET_COMPRESSION_THRESHOLD'):
            try:
                self.connection.compression_threshold = int(threshold)
            except ValueError:
                logger.warning(f"잘못된 UPBIT_WEBSOCKET_COMPRESSION_THRESHOLD 값: {threshold}")

        # Rate Limiter 설정
        if enable_limiter := os.getenv('UPBIT_WEBSOCKET_RATE_LIMITER'):
            self.rate_limiter.enable_rate_limiter = enable_limiter.lower() in ('true', '1', 'yes')

        if enable_dynamic := os.getenv('UPBIT_WEBSOCKET_DYNAMIC_RATE_LIMITER'):
            self.rate_limiter.enable_dynamic_adjustment = enable_dynamic.lower() in ('true', '1', 'yes')

        if strategy := os.getenv('UPBIT_WEBSOCKET_RATE_STRATEGY'):
            if strategy in ["conservative", "balanced", "aggressive"]:
                self.rate_limiter.strategy = strategy
            else:
                logger.warning(f"잘못된 UPBIT_WEBSOCKET_RATE_STRATEGY 값: {strategy}")

        if error_threshold := os.getenv('UPBIT_WEBSOCKET_ERROR_THRESHOLD'):
            try:
                self.rate_limiter.error_threshold = int(error_threshold)
            except ValueError:
                logger.warning(f"잘못된 UPBIT_WEBSOCKET_ERROR_THRESHOLD 값: {error_threshold}")

        # Simple Format 설정
        if enable_simple := os.getenv('UPBIT_WEBSOCKET_SIMPLE_MODE'):
            self.simple_format.enable_simple_mode = enable_simple.lower() in ('true', '1', 'yes')

        if auto_convert := os.getenv('UPBIT_WEBSOCKET_AUTO_CONVERT_INCOMING'):
            self.simple_format.auto_convert_incoming = auto_convert.lower() in ('true', '1', 'yes')

        if force_simple := os.getenv('UPBIT_WEBSOCKET_FORCE_SIMPLE_FORMAT'):
            self.simple_format.force_simple_format = force_simple.lower() in ('true', '1', 'yes')

        if compression_with_simple := os.getenv('UPBIT_WEBSOCKET_COMPRESSION_WITH_SIMPLE'):
            self.simple_format.enable_compression_with_simple = compression_with_simple.lower() in ('true', '1', 'yes')

        if debug_format := os.getenv('UPBIT_WEBSOCKET_DEBUG_FORMAT_CONVERSION'):
            self.simple_format.debug_format_conversion = debug_format.lower() in ('true', '1', 'yes')

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
                'max_message_size': self.connection.max_message_size,
                'compression_threshold': self.connection.compression_threshold
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
            },
            'rate_limiter': {
                'enable_rate_limiter': self.rate_limiter.enable_rate_limiter,
                'enable_dynamic_adjustment': self.rate_limiter.enable_dynamic_adjustment,
                'strategy': self.rate_limiter.strategy,
                'error_threshold': self.rate_limiter.error_threshold,
                'reduction_ratio': self.rate_limiter.reduction_ratio,
                'recovery_delay': self.rate_limiter.recovery_delay,
                'recovery_step': self.rate_limiter.recovery_step,
                'recovery_interval': self.rate_limiter.recovery_interval
            },
            'simple_format': {
                'enable_simple_mode': self.simple_format.enable_simple_mode,
                'auto_convert_incoming': self.simple_format.auto_convert_incoming,
                'force_simple_format': self.simple_format.force_simple_format,
                'enable_compression_with_simple': self.simple_format.enable_compression_with_simple,
                'debug_format_conversion': self.simple_format.debug_format_conversion
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

    # Simple Mode: 개발 시 디버깅 용이성 우선
    config.simple_format.enable_simple_mode = False
    config.simple_format.debug_format_conversion = True

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

    # Simple Mode: 테스트에서 SIMPLE 모드 검증
    config.simple_format.enable_simple_mode = True
    config.simple_format.debug_format_conversion = True

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

    # Simple Mode: 프로덕션에서 네트워크 최적화 최대화
    config.simple_format.enable_simple_mode = True
    config.simple_format.force_simple_format = True
    config.simple_format.debug_format_conversion = False

    return config


# ================================================================
# 설정 로딩 및 관리
# ================================================================

def load_yaml_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """YAML 설정 파일 로딩"""
    if config_path is None:
        # 프로젝트 루트에서 config 폴더 찾기
        current_path = Path(__file__)
        # upbit-autotrader-vscode 프로젝트 루트 찾기
        while current_path.parent != current_path and current_path.name != "upbit-autotrader-vscode":
            current_path = current_path.parent
        config_path = str(current_path / "config" / "websocket_config.yaml")

    config_file = Path(config_path)

    if not config_file.exists():
        logger.warning(f"YAML 설정 파일 없음: {config_file}")
        return {}

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            yaml_config = yaml.safe_load(f) or {}
        logger.info(f"YAML 설정 로딩 완료: {config_file}")
        return yaml_config
    except Exception as e:
        logger.error(f"YAML 설정 로딩 실패: {e}")
        return {}


def apply_yaml_config_to_instance(config: WebSocketConfig, yaml_config: Dict[str, Any]) -> None:
    """YAML 설정을 WebSocketConfig 인스턴스에 적용"""
    # 환경별 설정 우선 적용
    env_name = config.environment.value
    env_config = yaml_config.get(env_name, {})

    # 기본 설정과 환경별 설정 병합
    merged_config = {**yaml_config}
    for key, value in env_config.items():
        if isinstance(value, dict) and key in merged_config:
            merged_config[key] = {**merged_config.get(key, {}), **value}
        else:
            merged_config[key] = value

    # 각 설정 섹션 적용
    if 'connection' in merged_config:
        conn = merged_config['connection']
        config.connection.public_url = conn.get('public_url', config.connection.public_url)
        config.connection.private_url = conn.get('private_url', config.connection.private_url)
        config.connection.connect_timeout = conn.get('connect_timeout', config.connection.connect_timeout)
        config.connection.heartbeat_interval = conn.get('heartbeat_interval', config.connection.heartbeat_interval)
        config.connection.enable_compression = conn.get('enable_compression', config.connection.enable_compression)
        config.connection.max_message_size = conn.get('max_message_size', config.connection.max_message_size)
        config.connection.compression_threshold = conn.get('compression_threshold', config.connection.compression_threshold)

    if 'reconnection' in merged_config:
        reconn = merged_config['reconnection']
        config.reconnection.max_attempts = reconn.get('max_attempts', config.reconnection.max_attempts)
        config.reconnection.base_delay = reconn.get('base_delay', config.reconnection.base_delay)
        config.reconnection.max_delay = reconn.get('max_delay', config.reconnection.max_delay)
        config.reconnection.exponential_base = reconn.get('exponential_base', config.reconnection.exponential_base)
        config.reconnection.jitter = reconn.get('jitter', config.reconnection.jitter)

    if 'auth' in merged_config:
        auth = merged_config['auth']
        config.auth.jwt_refresh_threshold = auth.get('jwt_refresh_threshold', config.auth.jwt_refresh_threshold)
        config.auth.max_auth_retries = auth.get('max_auth_retries', config.auth.max_auth_retries)
        config.auth.auth_timeout = auth.get('auth_timeout', config.auth.auth_timeout)

    if 'monitoring' in merged_config:
        monitor = merged_config['monitoring']
        config.monitoring.enable_health_check = monitor.get(
            'enable_health_check', config.monitoring.enable_health_check)
        config.monitoring.health_check_interval = monitor.get(
            'health_check_interval', config.monitoring.health_check_interval)
        config.monitoring.enable_performance_metrics = monitor.get(
            'enable_performance_metrics', config.monitoring.enable_performance_metrics)
        config.monitoring.metrics_update_interval = monitor.get(
            'metrics_update_interval', config.monitoring.metrics_update_interval)
        config.monitoring.enable_connection_metrics = monitor.get(
            'enable_connection_metrics', config.monitoring.enable_connection_metrics)
        config.monitoring.cleanup_interval = monitor.get(
            'cleanup_interval', config.monitoring.cleanup_interval)

    if 'rate_limiter' in merged_config:
        rate = merged_config['rate_limiter']
        config.rate_limiter.enable_rate_limiter = rate.get(
            'enable_rate_limiter', config.rate_limiter.enable_rate_limiter)
        config.rate_limiter.enable_dynamic_adjustment = rate.get(
            'enable_dynamic_adjustment', config.rate_limiter.enable_dynamic_adjustment)
        config.rate_limiter.strategy = rate.get('strategy', config.rate_limiter.strategy)
        config.rate_limiter.error_threshold = rate.get(
            'error_threshold', config.rate_limiter.error_threshold)
        config.rate_limiter.reduction_ratio = rate.get(
            'reduction_ratio', config.rate_limiter.reduction_ratio)
        config.rate_limiter.recovery_delay = rate.get(
            'recovery_delay', config.rate_limiter.recovery_delay)
        config.rate_limiter.recovery_step = rate.get(
            'recovery_step', config.rate_limiter.recovery_step)
        config.rate_limiter.recovery_interval = rate.get(
            'recovery_interval', config.rate_limiter.recovery_interval)

    if 'simple_format' in merged_config:
        simple = merged_config['simple_format']
        config.simple_format.enable_simple_mode = simple.get(
            'enable_simple_mode', config.simple_format.enable_simple_mode)
        config.simple_format.auto_convert_incoming = simple.get(
            'auto_convert_incoming', config.simple_format.auto_convert_incoming)
        config.simple_format.force_simple_format = simple.get(
            'force_simple_format', config.simple_format.force_simple_format)
        config.simple_format.enable_compression_with_simple = simple.get(
            'enable_compression_with_simple', config.simple_format.enable_compression_with_simple)
        config.simple_format.debug_format_conversion = simple.get(
            'debug_format_conversion', config.simple_format.debug_format_conversion)


def load_config_from_env() -> WebSocketConfig:
    """환경변수와 YAML에서 설정 로딩 (통합)"""
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

    # YAML 설정 로딩 및 적용
    yaml_config = load_yaml_config()
    if yaml_config:
        apply_yaml_config_to_instance(config, yaml_config)

    # 환경변수 오버라이드 적용 (최종 우선순위)
    config.apply_environment_overrides()

    # 설정 검증
    try:
        config.validate()
    except Exception as e:
        logger.error(f"설정 검증 실패: {e}")
        raise

    logger.info(f"WebSocket 설정 로딩 완료: {environment.value}")
    logger.info(f"Simple Mode: {config.simple_format.enable_simple_mode}")
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


def get_simple_format_config() -> SimpleFormatConfig:
    """Simple Format 설정 반환"""
    return get_config().simple_format


def is_simple_mode_enabled() -> bool:
    """Simple Mode 활성화 여부 확인"""
    return get_config().simple_format.enable_simple_mode


def should_force_simple_format() -> bool:
    """SIMPLE 포맷 강제 적용 여부 확인"""
    config = get_config().simple_format
    return config.enable_simple_mode and config.force_simple_format


def should_auto_convert_incoming() -> bool:
    """수신 데이터 자동 변환 여부 확인"""
    return get_config().simple_format.auto_convert_incoming


def is_format_debug_enabled() -> bool:
    """포맷 변환 디버깅 활성화 여부"""
    return get_config().simple_format.debug_format_conversion
