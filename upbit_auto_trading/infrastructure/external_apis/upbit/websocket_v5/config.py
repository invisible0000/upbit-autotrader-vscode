"""
업비트 WebSocket v5.0 - YAML 기반 설정 시스템

🎯 특징:
- 외부 설정 파일 지원
- 환경별 설정 분리
- 타입 안전성 보장
- 설정 유효성 검증
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import yaml
from enum import Enum


class LogLevel(str, Enum):
    """로그 레벨"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Environment(str, Enum):
    """환경 구분"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


@dataclass
class ConnectionConfig:
    """연결 설정"""
    url: str = "wss://api.upbit.com/websocket/v1"
    private_url: str = "wss://api.upbit.com/websocket/v1/private"
    connect_timeout: float = 10.0
    close_timeout: float = 5.0
    ping_interval: float = 30.0
    ping_timeout: float = 10.0
    message_timeout: float = 60.0

    def __post_init__(self):
        """설정 유효성 검증"""
        if self.connect_timeout <= 0:
            raise ValueError("connect_timeout은 0보다 커야 합니다")
        if self.ping_interval <= 0:
            raise ValueError("ping_interval은 0보다 커야 합니다")


@dataclass
class ReconnectionConfig:
    """재연결 설정"""
    auto_reconnect: bool = True
    max_attempts: int = 10
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    min_interval: float = 5.0

    def __post_init__(self):
        """설정 유효성 검증"""
        if self.max_attempts < 0:
            raise ValueError("max_attempts는 0 이상이어야 합니다")
        if self.initial_delay <= 0:
            raise ValueError("initial_delay는 0보다 커야 합니다")
        if self.backoff_multiplier < 1.0:
            raise ValueError("backoff_multiplier는 1.0 이상이어야 합니다")


@dataclass
class SubscriptionConfig:
    """구독 설정"""
    max_tickets: int = 5
    enable_ticket_reuse: bool = True
    default_format: str = "DEFAULT"
    format_preference: str = "auto"  # "auto", "simple", "default"
    auto_subscribe_on_connect: bool = False
    subscription_timeout: float = 10.0
    # 티켓 풀 크기 설정
    public_pool_size: int = 3
    private_pool_size: int = 2

    def __post_init__(self):
        """설정 유효성 검증"""
        if self.max_tickets <= 0 or self.max_tickets > 10:
            raise ValueError("max_tickets는 1-10 사이여야 합니다")
        if self.format_preference not in ["auto", "simple", "default"]:
            raise ValueError("format_preference는 'auto', 'simple', 'default' 중 하나여야 합니다")
        if self.public_pool_size <= 0 or self.public_pool_size > 10:
            raise ValueError("public_pool_size는 1-10 사이여야 합니다")
        if self.private_pool_size <= 0 or self.private_pool_size > 5:
            raise ValueError("private_pool_size는 1-5 사이여야 합니다")


@dataclass
class RateLimitConfig:
    """Rate Limit 설정"""
    requests_per_second: int = 10
    requests_per_minute: int = 600
    burst_limit: int = 10
    enable_rate_limiting: bool = True

    def __post_init__(self):
        """설정 유효성 검증"""
        if self.requests_per_second <= 0:
            raise ValueError("requests_per_second는 0보다 커야 합니다")
        if self.requests_per_minute <= 0:
            raise ValueError("requests_per_minute는 0보다 커야 합니다")


@dataclass
class LoggingConfig:
    """로깅 설정"""
    level: LogLevel = LogLevel.INFO
    enable_console: bool = True
    enable_file: bool = False
    file_path: Optional[str] = None
    max_file_size: str = "10MB"
    backup_count: int = 5
    log_message_details: bool = False

    def __post_init__(self):
        """설정 유효성 검증"""
        if self.enable_file and not self.file_path:
            raise ValueError("파일 로깅이 활성화되었지만 file_path가 없습니다")


@dataclass
class EventConfig:
    """이벤트 설정"""
    enable_event_broker: bool = False
    broker_type: str = "memory"  # memory, redis, rabbitmq
    broker_url: Optional[str] = None
    event_queue_size: int = 1000
    enable_message_persistence: bool = False

    def __post_init__(self):
        """설정 유효성 검증"""
        if self.enable_event_broker and self.broker_type not in ["memory", "redis", "rabbitmq"]:
            raise ValueError("지원하지 않는 broker_type입니다")


@dataclass
class SecurityConfig:
    """보안 설정"""
    enable_ssl_verification: bool = True
    api_key_env_var: str = "UPBIT_ACCESS_KEY"
    secret_key_env_var: str = "UPBIT_SECRET_KEY"
    jwt_expiration_minutes: int = 10


@dataclass
class PerformanceConfig:
    """성능 설정"""
    message_buffer_size: int = 1000
    worker_thread_count: int = 2
    enable_message_compression: bool = False  # WebSocket 압축 (성능 우선으로 비활성화)
    memory_limit_mb: int = 100


@dataclass
class WebSocketConfig:
    """통합 WebSocket 설정"""
    environment: Environment = Environment.DEVELOPMENT
    connection: ConnectionConfig = field(default_factory=ConnectionConfig)
    reconnection: ReconnectionConfig = field(default_factory=ReconnectionConfig)
    subscription: SubscriptionConfig = field(default_factory=SubscriptionConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    event: EventConfig = field(default_factory=EventConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)

    @classmethod
    def from_yaml(cls, config_path: str) -> 'WebSocketConfig':
        """YAML 파일에서 설정 로드"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)

        return cls.from_dict(yaml_data)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'WebSocketConfig':
        """딕셔너리에서 설정 객체 생성"""
        # 환경 설정
        environment = Environment(config_dict.get('environment', 'development'))

        # 각 섹션별 설정 생성
        connection = ConnectionConfig(**config_dict.get('connection', {}))
        reconnection = ReconnectionConfig(**config_dict.get('reconnection', {}))
        subscription = SubscriptionConfig(**config_dict.get('subscription', {}))
        rate_limit = RateLimitConfig(**config_dict.get('rate_limit', {}))

        # 로깅 설정 (LogLevel 변환)
        logging_dict = config_dict.get('logging', {})
        if 'level' in logging_dict:
            logging_dict['level'] = LogLevel(logging_dict['level'])
        logging = LoggingConfig(**logging_dict)

        event = EventConfig(**config_dict.get('event', {}))
        security = SecurityConfig(**config_dict.get('security', {}))
        performance = PerformanceConfig(**config_dict.get('performance', {}))

        return cls(
            environment=environment,
            connection=connection,
            reconnection=reconnection,
            subscription=subscription,
            rate_limit=rate_limit,
            logging=logging,
            event=event,
            security=security,
            performance=performance
        )

    def to_yaml(self, output_path: str) -> None:
        """설정을 YAML 파일로 저장"""
        config_dict = self.to_dict()

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)

    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 변환"""
        return {
            'environment': self.environment.value,
            'connection': {
                'url': self.connection.url,
                'private_url': self.connection.private_url,
                'connect_timeout': self.connection.connect_timeout,
                'close_timeout': self.connection.close_timeout,
                'ping_interval': self.connection.ping_interval,
                'ping_timeout': self.connection.ping_timeout,
                'message_timeout': self.connection.message_timeout
            },
            'reconnection': {
                'auto_reconnect': self.reconnection.auto_reconnect,
                'max_attempts': self.reconnection.max_attempts,
                'initial_delay': self.reconnection.initial_delay,
                'max_delay': self.reconnection.max_delay,
                'backoff_multiplier': self.reconnection.backoff_multiplier,
                'min_interval': self.reconnection.min_interval
            },
            'subscription': {
                'max_tickets': self.subscription.max_tickets,
                'enable_ticket_reuse': self.subscription.enable_ticket_reuse,
                'default_format': self.subscription.default_format,
                'auto_subscribe_on_connect': self.subscription.auto_subscribe_on_connect,
                'subscription_timeout': self.subscription.subscription_timeout
            },
            'rate_limit': {
                'requests_per_second': self.rate_limit.requests_per_second,
                'requests_per_minute': self.rate_limit.requests_per_minute,
                'burst_limit': self.rate_limit.burst_limit,
                'enable_rate_limiting': self.rate_limit.enable_rate_limiting
            },
            'logging': {
                'level': self.logging.level.value,
                'enable_console': self.logging.enable_console,
                'enable_file': self.logging.enable_file,
                'file_path': self.logging.file_path,
                'max_file_size': self.logging.max_file_size,
                'backup_count': self.logging.backup_count,
                'log_message_details': self.logging.log_message_details
            },
            'event': {
                'enable_event_broker': self.event.enable_event_broker,
                'broker_type': self.event.broker_type,
                'broker_url': self.event.broker_url,
                'event_queue_size': self.event.event_queue_size,
                'enable_message_persistence': self.event.enable_message_persistence
            },
            'security': {
                'enable_ssl_verification': self.security.enable_ssl_verification,
                'api_key_env_var': self.security.api_key_env_var,
                'secret_key_env_var': self.security.secret_key_env_var,
                'jwt_expiration_minutes': self.security.jwt_expiration_minutes
            },
            'performance': {
                'message_buffer_size': self.performance.message_buffer_size,
                'worker_thread_count': self.performance.worker_thread_count,
                'enable_message_compression': self.performance.enable_message_compression,
                'memory_limit_mb': self.performance.memory_limit_mb
            }
        }

    def get_connection_params(self) -> Dict[str, Any]:
        """WebSocket 연결용 파라미터 추출"""
        return {
            'ping_interval': self.connection.ping_interval,
            'ping_timeout': self.connection.ping_timeout,
            'close_timeout': self.connection.close_timeout
        }

    def is_development(self) -> bool:
        """개발 환경 여부"""
        return self.environment == Environment.DEVELOPMENT

    def is_production(self) -> bool:
        """운영 환경 여부"""
        return self.environment == Environment.PRODUCTION


# 기본 설정 템플릿
DEFAULT_CONFIG_TEMPLATE = """
# 업비트 WebSocket v5.0 설정 파일
environment: development

connection:
  url: "wss://api.upbit.com/websocket/v1"
  private_url: "wss://api.upbit.com/websocket/v1/private"
  connect_timeout: 10.0
  close_timeout: 5.0
  ping_interval: 30.0
  ping_timeout: 10.0
  message_timeout: 60.0

reconnection:
  auto_reconnect: true
  max_attempts: 10
  initial_delay: 1.0
  max_delay: 60.0
  backoff_multiplier: 2.0
  min_interval: 5.0

subscription:
  max_tickets: 5
  enable_ticket_reuse: true
  default_format: "DEFAULT"
  auto_subscribe_on_connect: false
  subscription_timeout: 10.0

rate_limit:
  requests_per_second: 10
  requests_per_minute: 600
  burst_limit: 10
  enable_rate_limiting: true

logging:
  level: "INFO"
  enable_console: true
  enable_file: false
  file_path: null
  max_file_size: "10MB"
  backup_count: 5
  log_message_details: false

event:
  enable_event_broker: false
  broker_type: "memory"
  broker_url: null
  event_queue_size: 1000
  enable_message_persistence: false

security:
  enable_ssl_verification: true
  api_key_env_var: "UPBIT_ACCESS_KEY"
  secret_key_env_var: "UPBIT_SECRET_KEY"
  jwt_expiration_minutes: 10

performance:
  message_buffer_size: 1000
  worker_thread_count: 2
  enable_message_compression: false
  memory_limit_mb: 100
"""


def create_default_config(output_path: str) -> None:
    """기본 설정 파일 생성"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(DEFAULT_CONFIG_TEMPLATE.strip())


def load_config(config_path: Optional[str] = None) -> WebSocketConfig:
    """설정 로드 (파일 없으면 기본값 사용)"""
    if config_path and Path(config_path).exists():
        return WebSocketConfig.from_yaml(config_path)
    else:
        return WebSocketConfig()  # 기본값 사용
