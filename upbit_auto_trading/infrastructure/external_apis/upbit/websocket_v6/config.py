"""
WebSocket v6.0 설정 관리 (YAML 지원 확장)
=========================================

WebSocket v6 시스템의 통합 설정 관리
- 기존 Python 기반 설정 유지 (하위 호환성)
- YAML 파일 로딩 기능 추가 (v6.1 신규)
- 환경별 설정, 기본값, 검증 로직 포함

설정 영역:
- 연결 설정 (URL, 타임아웃)
- 재연결 설정 (백오프, 최대 시도)
- 백프레셔 설정 (큐 크기, 전략)
- Private 인증 설정 (JWT)
- 성능 모니터링 설정
- 포맷 변환 설정 (SIMPLE ↔ DEFAULT) - NEW
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum

from .types import BackpressureConfig, BackpressureStrategy
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("WebSocketConfig")


class Environment(Enum):
    """실행 환경"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class FormatConfig:
    """포맷 변환 설정 (v6.1 신규)"""
    internal_format: str = "default"  # 내부 시스템 포맷
    transmission_format: str = "simple"  # 네트워크 전송 포맷
    user_interface_format: str = "default"  # 사용자 API 포맷
    enable_transparent_conversion: bool = True  # 투명 변환 활성화
    log_format_conversion: bool = False  # 변환 로깅


@dataclass
class ConnectionConfig:
    """연결 설정"""
    # 현재: Public/Private 동일 URL (업비트 정책)
    url: str = "wss://api.upbit.com/websocket/v1"

    # 향후 분리 대비 (현재 미사용)
    public_url: str = "wss://api.upbit.com/websocket/v1"
    private_url: str = "wss://api.upbit.com/websocket/v1"

    connect_timeout: float = 10.0
    heartbeat_interval: float = 30.0
    enable_compression: bool = True
    enable_simple_format: bool = False
    max_message_size: int = 1024 * 1024  # 1MB

    def validate(self) -> None:
        """설정 검증"""
        if not self.url.startswith("wss://"):
            raise ValueError("url은 wss:// 형식이어야 합니다")
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
class WebSocketConfig:
    """WebSocket 통합 설정"""
    environment: Environment = Environment.DEVELOPMENT
    connection: ConnectionConfig = field(default_factory=ConnectionConfig)
    reconnection: ReconnectionConfig = field(default_factory=ReconnectionConfig)
    backpressure: BackpressureConfig = field(default_factory=BackpressureConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    subscription: SubscriptionConfig = field(default_factory=SubscriptionConfig)
    format: FormatConfig = field(default_factory=FormatConfig)  # NEW

    # 디버깅 옵션
    debug_mode: bool = False
    log_level: str = "INFO"
    log_websocket_messages: bool = False

    @property
    def is_transparent_conversion_enabled(self) -> bool:
        """투명 포맷 변환 활성화 여부"""
        return (self.format.enable_transparent_conversion
                and self.connection.enable_simple_format)

    @property
    def should_use_simple_format_for_transmission(self) -> bool:
        """전송 시 SIMPLE 포맷 사용 여부"""
        return (self.format.transmission_format == "simple"
                and self.connection.enable_simple_format)

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
            'format': {
                'internal_format': self.format.internal_format,
                'transmission_format': self.format.transmission_format,
                'user_interface_format': self.format.user_interface_format,
                'enable_transparent_conversion': self.format.enable_transparent_conversion,
                'log_format_conversion': self.format.log_format_conversion,
            },
            'debug': {
                'debug_mode': self.debug_mode,
                'log_level': self.log_level,
                'log_websocket_messages': self.log_websocket_messages,
            }
        }


# =============================================================================
# YAML 설정 로딩 기능 (v6.1 신규)
# =============================================================================

def load_yaml_config(config_file: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    YAML 설정 파일 로드

    Args:
        config_file: YAML 설정 파일 경로

    Returns:
        Dict[str, Any]: YAML 설정 데이터 또는 None
    """
    if config_file is None:
        # 현재 디렉토리의 websocket_config.yaml 찾기
        current_dir = Path(__file__).parent
        config_path = current_dir / "websocket_config.yaml"
    else:
        config_path = Path(config_file)

    if not config_path.exists():
        logger.info(f"YAML 설정 파일 없음: {config_path}, Python 설정 사용")
        return None

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)

        logger.info(f"✅ YAML 설정 로드 완료: {config_path}")
        return yaml_data

    except Exception as e:
        logger.error(f"YAML 설정 로드 실패: {e}, Python 설정으로 폴백")
        return None


def apply_yaml_overrides(config: WebSocketConfig, yaml_data: Dict[str, Any]) -> WebSocketConfig:
    """
    YAML 설정으로 기존 설정 오버라이드

    Args:
        config: 기존 WebSocketConfig
        yaml_data: YAML 설정 데이터

    Returns:
        WebSocketConfig: 오버라이드된 설정
    """
    # Connection 설정 오버라이드
    if 'connection' in yaml_data:
        conn_yaml = yaml_data['connection']
        if 'url' in conn_yaml:
            config.connection.url = conn_yaml['url']
            # 향후 분리 대비
            config.connection.public_url = conn_yaml['url']
            config.connection.private_url = conn_yaml['url']
        if 'connection_timeout' in conn_yaml:
            config.connection.connect_timeout = conn_yaml['connection_timeout']
        if 'heartbeat_interval' in conn_yaml:
            config.connection.heartbeat_interval = conn_yaml['heartbeat_interval']
        if 'max_message_size' in conn_yaml:
            config.connection.max_message_size = conn_yaml['max_message_size']

    # Performance 설정 오버라이드
    if 'performance' in yaml_data:
        perf_yaml = yaml_data['performance']
        if 'enable_compression' in perf_yaml:
            config.connection.enable_compression = perf_yaml['enable_compression']
        if 'enable_simple_format' in perf_yaml:
            config.connection.enable_simple_format = perf_yaml['enable_simple_format']

    # Backpressure 설정 오버라이드 (NEW)
    if 'backpressure' in yaml_data:
        bp_yaml = yaml_data['backpressure']
        if 'max_queue_size' in bp_yaml:
            config.backpressure.max_queue_size = bp_yaml['max_queue_size']
        if 'warning_threshold' in bp_yaml:
            config.backpressure.warning_threshold = bp_yaml['warning_threshold']
        if 'strategy' in bp_yaml:
            try:
                config.backpressure.strategy = BackpressureStrategy(bp_yaml['strategy'])
            except ValueError:
                pass  # 잘못된 전략은 무시

    # Monitoring 설정 오버라이드 (NEW)
    if 'monitoring' in yaml_data:
        mon_yaml = yaml_data['monitoring']
        if 'metrics_collection_interval' in mon_yaml:
            config.monitoring.metrics_collection_interval = mon_yaml['metrics_collection_interval']
        if 'health_check_interval' in mon_yaml:
            config.monitoring.health_check_interval = mon_yaml['health_check_interval']
        if 'performance_window_size' in mon_yaml:
            config.monitoring.performance_window_size = mon_yaml['performance_window_size']
        if 'alert_error_rate_threshold' in mon_yaml:
            config.monitoring.alert_error_rate_threshold = mon_yaml['alert_error_rate_threshold']
        if 'alert_latency_threshold_ms' in mon_yaml:
            config.monitoring.alert_latency_threshold_ms = mon_yaml['alert_latency_threshold_ms']
        if 'alert_queue_threshold' in mon_yaml:
            config.monitoring.alert_queue_threshold = mon_yaml['alert_queue_threshold']
        if 'alert_reconnect_threshold' in mon_yaml:
            config.monitoring.alert_reconnect_threshold = mon_yaml['alert_reconnect_threshold']

    # Subscription 설정 오버라이드 (NEW)
    if 'subscription' in yaml_data:
        sub_yaml = yaml_data['subscription']
        if 'max_symbols_per_request' in sub_yaml:
            config.subscription.max_symbols_per_request = sub_yaml['max_symbols_per_request']
        if 'timeout' in sub_yaml:
            config.subscription.subscription_timeout = sub_yaml['timeout']
        if 'auto_cleanup_interval' in sub_yaml:
            config.subscription.auto_cleanup_interval = sub_yaml['auto_cleanup_interval']
        if 'grace_period' in sub_yaml:
            config.subscription.grace_period = sub_yaml['grace_period']

    # Auth 설정 오버라이드 (NEW)
    if 'auth' in yaml_data:
        auth_yaml = yaml_data['auth']
        if 'jwt_refresh_threshold' in auth_yaml:
            config.auth.jwt_refresh_threshold = auth_yaml['jwt_refresh_threshold']
        if 'jwt_refresh_retry_count' in auth_yaml:
            config.auth.jwt_refresh_retry_count = auth_yaml['jwt_refresh_retry_count']
        if 'jwt_refresh_timeout' in auth_yaml:
            config.auth.jwt_refresh_timeout = auth_yaml['jwt_refresh_timeout']
        if 'fallback_to_rest' in auth_yaml:
            config.auth.fallback_to_rest = auth_yaml['fallback_to_rest']

    # Format 설정 오버라이드 (v6.1 신규)
    if 'format' in yaml_data:
        format_yaml = yaml_data['format']
        if 'internal_format' in format_yaml:
            config.format.internal_format = format_yaml['internal_format']
        if 'transmission_format' in format_yaml:
            config.format.transmission_format = format_yaml['transmission_format']
        if 'user_interface_format' in format_yaml:
            config.format.user_interface_format = format_yaml['user_interface_format']
        if 'enable_transparent_conversion' in format_yaml:
            config.format.enable_transparent_conversion = format_yaml['enable_transparent_conversion']
        if 'log_format_conversion' in format_yaml:
            config.format.log_format_conversion = format_yaml['log_format_conversion']

    # Reconnection 설정 오버라이드
    if 'reconnection' in yaml_data:
        recon_yaml = yaml_data['reconnection']
        if 'max_attempts' in recon_yaml:
            config.reconnection.max_attempts = recon_yaml['max_attempts']
        if 'base_delay' in recon_yaml:
            config.reconnection.base_delay = recon_yaml['base_delay']
        if 'max_delay' in recon_yaml:
            config.reconnection.max_delay = recon_yaml['max_delay']

    logger.info("✅ YAML 설정 오버라이드 완료")
    return config


# =============================================================================
# 설정 팩토리 함수
# =============================================================================

def create_default_config(environment: Environment = Environment.DEVELOPMENT) -> WebSocketConfig:
    """기본 설정 생성"""
    config = WebSocketConfig(environment=environment)
    config.apply_environment_overrides()
    config.validate()
    return config


def create_development_config() -> WebSocketConfig:
    """개발 환경 설정"""
    config = WebSocketConfig(environment=Environment.DEVELOPMENT)

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


def create_testing_config() -> WebSocketConfig:
    """테스트 환경 설정"""
    config = WebSocketConfig(environment=Environment.TESTING)

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


def create_production_config() -> WebSocketConfig:
    """프로덕션 환경 설정"""
    config = WebSocketConfig(environment=Environment.PRODUCTION)

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

# =============================================================================
# 환경변수 기반 설정 로딩 (YAML 지원 확장)
# =============================================================================

def load_config_from_env() -> WebSocketConfig:
    """환경변수에서 설정 로딩 (YAML 오버라이드 지원)"""
    # 환경 결정
    env_name = os.getenv("UPBIT_ENVIRONMENT", "development").lower()
    try:
        environment = Environment(env_name)
    except ValueError:
        environment = Environment.DEVELOPMENT

    # 기본 설정 생성
    config = create_default_config(environment)

    # YAML 설정 오버라이드 시도
    yaml_data = load_yaml_config()
    if yaml_data:
        config = apply_yaml_overrides(config, yaml_data)

    # 환경변수 오버라이드 (최우선)
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


# 전역 설정 인스턴스 (싱글톤)
_global_config_instance: Optional[WebSocketConfig] = None


def get_config() -> WebSocketConfig:
    """설정 인스턴스 획득 (싱글톤 패턴)"""
    global _global_config_instance
    if _global_config_instance is None:
        _global_config_instance = load_config_from_env()
    return _global_config_instance


def reset_config() -> None:
    """설정 인스턴스 리셋 (테스트용)"""
    global _global_config_instance
    _global_config_instance = None


# =============================================================================
# 편의 함수들 (v6.1 신규)
# =============================================================================

def get_transmission_format() -> str:
    """전송용 포맷 반환"""
    config = get_config()
    return config.format.transmission_format


def is_compression_enabled() -> bool:
    """압축 활성화 여부"""
    config = get_config()
    return config.connection.enable_compression


def is_simple_format_enabled() -> bool:
    """SIMPLE 포맷 활성화 여부"""
    config = get_config()
    return config.connection.enable_simple_format


def is_transparent_conversion_enabled() -> bool:
    """투명 변환 활성화 여부"""
    config = get_config()
    return config.is_transparent_conversion_enabled


def get_user_interface_format() -> str:
    """사용자 인터페이스 포맷 반환"""
    config = get_config()
    return config.format.user_interface_format


def get_internal_format() -> str:
    """내부 시스템 포맷 반환"""
    config = get_config()
    return config.format.internal_format
