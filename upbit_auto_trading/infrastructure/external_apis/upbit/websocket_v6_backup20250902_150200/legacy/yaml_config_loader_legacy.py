"""
WebSocket v6.0 YAML 설정 로더
============================

DDD + MVP + Infrastructure v4.0 호환
YAML 기반 중앙화된 설정 관리 시스템
"""

import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("WebSocketConfigLoader")


@dataclass
class FormatConfig:
    """포맷 변환 설정"""
    internal_format: str = "default"
    transmission_format: str = "simple"
    user_interface_format: str = "default"
    enable_transparent_conversion: bool = True
    log_format_conversion: bool = False


@dataclass
class PerformanceConfig:
    """성능 최적화 설정"""
    message_buffer_size: int = 1000
    max_memory_mb: float = 100.0
    enable_compression: bool = True
    compression_level: int = 6
    enable_simple_format: bool = True


@dataclass
class ConnectionConfig:
    """연결 설정"""
    url: str = "wss://api.upbit.com/websocket/v1"
    connection_timeout: float = 10.0
    ping_interval: float = 20.0
    ping_timeout: float = 10.0
    close_timeout: float = 10.0
    heartbeat_interval: float = 30.0
    heartbeat_timeout: float = 60.0


@dataclass
class ReconnectionConfig:
    """재연결 설정"""
    enabled: bool = True
    max_attempts: int = 5
    base_delay: float = 2.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0


@dataclass
class SubscriptionConfig:
    """구독 설정"""
    max_subscriptions: int = 10
    batch_size: int = 5
    timeout: float = 30.0
    format_preference: str = "auto"
    public_pool_size: int = 3
    private_pool_size: int = 2


@dataclass
class LoggingConfig:
    """로깅 설정"""
    level: str = "INFO"
    enable_debug: bool = False
    log_messages: bool = False
    log_performance_metrics: bool = True
    log_format_conversion: bool = False


@dataclass
class DevelopmentConfig:
    """개발 환경 설정"""
    enable_dry_run: bool = True
    enable_detailed_logging: bool = False
    enable_message_dump: bool = False
    enable_performance_tracking: bool = True


@dataclass
class WebSocketYamlConfig:
    """WebSocket v6.0 통합 YAML 설정"""
    connection: ConnectionConfig = field(default_factory=ConnectionConfig)
    reconnection: ReconnectionConfig = field(default_factory=ReconnectionConfig)
    subscription: SubscriptionConfig = field(default_factory=SubscriptionConfig)
    format: FormatConfig = field(default_factory=FormatConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    development: DevelopmentConfig = field(default_factory=DevelopmentConfig)

    @property
    def is_transparent_conversion_enabled(self) -> bool:
        """투명 포맷 변환 활성화 여부"""
        return (self.format.enable_transparent_conversion
                and self.performance.enable_simple_format)

    @property
    def should_use_simple_format_for_transmission(self) -> bool:
        """전송 시 SIMPLE 포맷 사용 여부"""
        return (self.format.transmission_format == "simple"
                and self.performance.enable_simple_format)

    @property
    def compression_settings(self) -> Dict[str, Any]:
        """압축 설정 딕셔너리"""
        return {
            'enable_compression': self.performance.enable_compression,
            'compression_level': self.performance.compression_level
        }

    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 변환"""
        return {
            'connection': {
                'url': self.connection.url,
                'connection_timeout': self.connection.connection_timeout,
                'ping_interval': self.connection.ping_interval,
                'ping_timeout': self.connection.ping_timeout,
                'close_timeout': self.connection.close_timeout,
                'heartbeat_interval': self.connection.heartbeat_interval,
                'heartbeat_timeout': self.connection.heartbeat_timeout,
            },
            'reconnection': {
                'enabled': self.reconnection.enabled,
                'max_attempts': self.reconnection.max_attempts,
                'base_delay': self.reconnection.base_delay,
                'max_delay': self.reconnection.max_delay,
                'backoff_multiplier': self.reconnection.backoff_multiplier,
            },
            'subscription': {
                'max_subscriptions': self.subscription.max_subscriptions,
                'batch_size': self.subscription.batch_size,
                'timeout': self.subscription.timeout,
                'format_preference': self.subscription.format_preference,
                'public_pool_size': self.subscription.public_pool_size,
                'private_pool_size': self.subscription.private_pool_size,
            },
            'format': {
                'internal_format': self.format.internal_format,
                'transmission_format': self.format.transmission_format,
                'user_interface_format': self.format.user_interface_format,
                'enable_transparent_conversion': self.format.enable_transparent_conversion,
                'log_format_conversion': self.format.log_format_conversion,
            },
            'performance': {
                'message_buffer_size': self.performance.message_buffer_size,
                'max_memory_mb': self.performance.max_memory_mb,
                'enable_compression': self.performance.enable_compression,
                'compression_level': self.performance.compression_level,
                'enable_simple_format': self.performance.enable_simple_format,
            },
            'logging': {
                'level': self.logging.level,
                'enable_debug': self.logging.enable_debug,
                'log_messages': self.logging.log_messages,
                'log_performance_metrics': self.logging.log_performance_metrics,
                'log_format_conversion': self.logging.log_format_conversion,
            },
            'development': {
                'enable_dry_run': self.development.enable_dry_run,
                'enable_detailed_logging': self.development.enable_detailed_logging,
                'enable_message_dump': self.development.enable_message_dump,
                'enable_performance_tracking': self.development.enable_performance_tracking,
            }
        }


def load_yaml_config(config_file: Optional[str] = None) -> WebSocketYamlConfig:
    """
    YAML 설정 파일 로드

    Args:
        config_file: 설정 파일 경로 (기본값: websocket_config.yaml)

    Returns:
        WebSocketYamlConfig: 로드된 설정
    """
    if config_file is None:
        # 현재 파일과 같은 디렉토리의 websocket_config.yaml 사용
        current_dir = Path(__file__).parent
        config_file = current_dir / "websocket_config.yaml"

    config_path = Path(config_file)

    if not config_path.exists():
        logger.warning(f"설정 파일이 없습니다: {config_path}")
        logger.info("기본 설정으로 WebSocket 시작")
        return WebSocketYamlConfig()

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)

        if not yaml_data:
            logger.warning("빈 설정 파일, 기본값 사용")
            return WebSocketYamlConfig()

        # YAML 데이터를 dataclass 인스턴스로 변환
        config = WebSocketYamlConfig()

        # Connection 설정
        if 'connection' in yaml_data:
            conn_data = yaml_data['connection']
            config.connection = ConnectionConfig(**conn_data)

        # Reconnection 설정
        if 'reconnection' in yaml_data:
            recon_data = yaml_data['reconnection']
            config.reconnection = ReconnectionConfig(**recon_data)

        # Subscription 설정
        if 'subscription' in yaml_data:
            sub_data = yaml_data['subscription']
            config.subscription = SubscriptionConfig(**sub_data)

        # Format 설정
        if 'format' in yaml_data:
            format_data = yaml_data['format']
            config.format = FormatConfig(**format_data)

        # Performance 설정
        if 'performance' in yaml_data:
            perf_data = yaml_data['performance']
            config.performance = PerformanceConfig(**perf_data)

        # Logging 설정
        if 'logging' in yaml_data:
            log_data = yaml_data['logging']
            config.logging = LoggingConfig(**log_data)

        # Development 설정
        if 'development' in yaml_data:
            dev_data = yaml_data['development']
            config.development = DevelopmentConfig(**dev_data)

        logger.info(f"✅ YAML 설정 로드 완료: {config_path}")

        # 투명 변환 설정 확인
        if config.is_transparent_conversion_enabled:
            logger.info("🔄 투명 포맷 변환 활성화됨 (사용자 불편함 최소화)")

        return config

    except Exception as e:
        logger.error(f"설정 파일 로드 실패: {e}")
        logger.info("기본 설정으로 WebSocket 시작")
        return WebSocketYamlConfig()


def save_yaml_config(config: WebSocketYamlConfig, config_file: Optional[str] = None) -> bool:
    """
    설정을 YAML 파일로 저장

    Args:
        config: 저장할 설정
        config_file: 저장할 파일 경로

    Returns:
        bool: 저장 성공 여부
    """
    if config_file is None:
        current_dir = Path(__file__).parent
        config_file = current_dir / "websocket_config.yaml"

    config_path = Path(config_file)

    try:
        config_dict = config.to_dict()

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        logger.info(f"✅ 설정 저장 완료: {config_path}")
        return True

    except Exception as e:
        logger.error(f"설정 저장 실패: {e}")
        return False


# 전역 설정 인스턴스 (싱글톤 패턴)
_global_yaml_config: Optional[WebSocketYamlConfig] = None


def get_yaml_config(reload: bool = False) -> WebSocketYamlConfig:
    """
    전역 YAML 설정 인스턴스 반환

    Args:
        reload: 설정 재로드 여부

    Returns:
        WebSocketYamlConfig: 전역 설정 인스턴스
    """
    global _global_yaml_config

    if _global_yaml_config is None or reload:
        _global_yaml_config = load_yaml_config()

    return _global_yaml_config


# 편의 함수들
def get_transmission_format() -> str:
    """전송용 포맷 반환"""
    config = get_yaml_config()
    return config.format.transmission_format


def is_compression_enabled() -> bool:
    """압축 활성화 여부"""
    config = get_yaml_config()
    return config.performance.enable_compression


def is_simple_format_enabled() -> bool:
    """SIMPLE 포맷 활성화 여부"""
    config = get_yaml_config()
    return config.performance.enable_simple_format


def is_transparent_conversion_enabled() -> bool:
    """투명 변환 활성화 여부"""
    config = get_yaml_config()
    return config.is_transparent_conversion_enabled


if __name__ == "__main__":
    # 테스트 코드
    print("🧪 WebSocket v6.0 YAML 설정 테스트")
    print("=" * 50)

    config = load_yaml_config()

    print(f"📡 연결 URL: {config.connection.url}")
    print(f"🔄 투명 변환: {'✅ 활성화' if config.is_transparent_conversion_enabled else '❌ 비활성화'}")
    print(f"📦 압축: {'✅ 활성화' if config.performance.enable_compression else '❌ 비활성화'}")
    print(f"📋 SIMPLE 포맷: {'✅ 활성화' if config.performance.enable_simple_format else '❌ 비활성화'}")
    print(f"🏠 내부 포맷: {config.format.internal_format}")
    print(f"📤 전송 포맷: {config.format.transmission_format}")
    print(f"👤 사용자 포맷: {config.format.user_interface_format}")
