from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path
import os
from enum import Enum


class Environment(Enum):
    """실행 환경"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """데이터베이스 설정"""
    settings_db_path: str = "data/settings.sqlite3"
    strategies_db_path: str = "data/strategies.sqlite3"
    market_data_db_path: str = "data/market_data.sqlite3"
    connection_timeout: int = 30
    max_connections: int = 10
    wal_mode: bool = True
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    use_dynamic_paths: bool = True  # DDD 기반 동적 경로 사용 여부
    config_source: str = "config/database_config.yaml"  # DDD 설정 파일 경로
    fallback_settings_db: str = "data/settings.sqlite3"  # 폴백 경로들
    fallback_strategies_db: str = "data/strategies.sqlite3"
    fallback_market_data_db: str = "data/market_data.sqlite3"

    def __post_init__(self):
        """경로 검증 및 절대경로 변환 (인메모리 DB 제외)"""
        # 인메모리 DB는 절대경로 변환하지 않음
        if self.settings_db_path != ':memory:':
            self.settings_db_path = str(Path(self.settings_db_path).resolve())
        if self.strategies_db_path != ':memory:':
            self.strategies_db_path = str(Path(self.strategies_db_path).resolve())
        if self.market_data_db_path != ':memory:':
            self.market_data_db_path = str(Path(self.market_data_db_path).resolve())


@dataclass
class UpbitApiConfig:
    """Upbit API 설정"""
    base_url: str = "https://api.upbit.com/v1"
    websocket_url: str = "wss://api.upbit.com/websocket/v1"
    requests_per_second: int = 10
    requests_per_minute: int = 600
    timeout_seconds: int = 30
    max_retries: int = 3
    access_key: Optional[str] = None
    secret_key: Optional[str] = None

    def __post_init__(self):
        """환경변수에서 API 키 로드"""
        if not self.access_key:
            self.access_key = os.getenv('UPBIT_ACCESS_KEY')
        if not self.secret_key:
            self.secret_key = os.getenv('UPBIT_SECRET_KEY')


@dataclass
@dataclass
class LoggingConfig:
    """로깅 설정"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    file_path: str = "logs/upbit_auto_trading.log"
    file_max_size_mb: int = 100
    file_backup_count: int = 5
    console_enabled: bool = True
    context: str = "development"  # development, testing, production, debugging
    scope: str = "normal"         # silent, minimal, normal, verbose, debug_all
    component_focus: Optional[str] = None

    # 새로 추가된 필드들 (프로파일 스위칭을 위해)
    llm_briefing_enabled: bool = True
    performance_monitoring: bool = False
    briefing_update_interval: int = 5
    feature_development: Optional[str] = None

    def __post_init__(self):
        """환경변수에서 로깅 설정 오버라이드"""
        self.context = os.getenv('UPBIT_LOG_CONTEXT', self.context)
        self.scope = os.getenv('UPBIT_LOG_SCOPE', self.scope)
        self.component_focus = os.getenv('UPBIT_COMPONENT_FOCUS', self.component_focus)
        if os.getenv('UPBIT_CONSOLE_OUTPUT', '').lower() == 'true':
            self.console_enabled = True

        # 새 필드들 환경변수 처리
        if os.getenv('UPBIT_LLM_BRIEFING_ENABLED'):
            self.llm_briefing_enabled = os.getenv('UPBIT_LLM_BRIEFING_ENABLED', '').lower() == 'true'
        if os.getenv('UPBIT_PERFORMANCE_MONITORING'):
            self.performance_monitoring = os.getenv('UPBIT_PERFORMANCE_MONITORING', '').lower() == 'true'
        if os.getenv('UPBIT_BRIEFING_UPDATE_INTERVAL'):
            try:
                self.briefing_update_interval = int(os.getenv('UPBIT_BRIEFING_UPDATE_INTERVAL', '5'))
            except ValueError:
                pass
        self.feature_development = os.getenv('UPBIT_FEATURE_DEVELOPMENT', self.feature_development)


@dataclass
class EventBusConfig:
    """Event Bus 설정"""
    implementation: str = "in_memory"  # in_memory, sqlite, redis
    worker_count: int = 4
    batch_size: int = 10
    batch_timeout_seconds: float = 1.0
    max_queue_size: int = 10000
    retry_max_attempts: int = 3
    retry_delay_seconds: float = 1.0
    retry_exponential_base: float = 2.0
    storage_enabled: bool = True
    storage_cleanup_days: int = 7


@dataclass
class TradingConfig:
    """매매 설정"""
    max_position_size_krw: int = 1000000  # 최대 포지션 크기 (원)
    min_order_amount_krw: int = 5000      # 최소 주문 금액 (원)
    max_orders_per_minute: int = 10       # 분당 최대 주문 수
    stop_loss_enabled: bool = True
    take_profit_enabled: bool = True
    paper_trading: bool = True            # 모의 거래 모드
    allowed_markets: List[str] = field(default_factory=lambda: ["KRW-BTC", "KRW-ETH"])
    default_fee: float = 0.0005           # 기본 거래 수수료
    default_slippage: float = 0.001       # 기본 슬리피지
    default_risk_percent: float = 0.02    # 기본 위험 비율

    # 추가 매매 설정
    auto_trading_enabled: bool = False    # 자동매매 활성화
    strategy_validation: bool = True      # 전략 유효성 검증
    max_concurrent_strategies: int = 5    # 최대 동시 전략 수
    order_confirmation: bool = True       # 주문 확인 팝업

    # 위험 관리
    max_daily_loss_krw: int = 100000     # 일일 최대 손실
    max_drawdown_percent: float = 0.10   # 최대 드로우다운
    emergency_stop_enabled: bool = True   # 비상 정지 기능

    # 백테스팅 설정
    backtest_commission: float = 0.0005   # 백테스트 수수료
    backtest_slippage: float = 0.001     # 백테스트 슬리피지
    backtest_start_balance: int = 1000000  # 백테스트 시작 잔고

    # API 제한
    api_call_delay_ms: int = 100          # API 호출 간격 (밀리초)
    order_retry_count: int = 3            # 주문 재시도 횟수
    order_timeout_seconds: int = 30       # 주문 타임아웃


@dataclass
class UIConfig:
    """UI 설정"""
    theme: str = "light"  # light, dark
    window_width: int = 1600
    window_height: int = 1000
    window_x: Optional[int] = None        # 창 X 위치
    window_y: Optional[int] = None        # 창 Y 위치
    window_maximized: bool = False        # 창 최대화 상태
    auto_refresh_interval_seconds: int = 5
    chart_update_interval_seconds: int = 1
    max_chart_candles: int = 200
    save_window_state: bool = True        # 창 상태 저장

    # 화면별 설정
    default_screen: str = "dashboard"     # 시작 화면
    last_screen: Optional[str] = None     # 마지막 사용 화면

    # 차트 설정
    chart_style: str = "candlestick"      # candlestick, line, bar
    chart_timeframe: str = "1h"           # 기본 차트 시간프레임
    chart_indicators: List[str] = field(default_factory=lambda: ["SMA", "RSI"])  # 기본 지표

    # 알림 설정
    notifications_enabled: bool = True
    sound_alerts: bool = True
    popup_alerts: bool = True

    # 데이터 표시 설정
    currency_format: str = "KRW"          # KRW, USD
    decimal_places: int = 2               # 소수점 자리수

    # 성능 설정
    animation_enabled: bool = True        # UI 애니메이션
    smooth_scrolling: bool = True         # 부드러운 스크롤링


@dataclass
class ApplicationConfig:
    """전체 애플리케이션 설정"""
    environment: Environment
    database: DatabaseConfig
    upbit_api: UpbitApiConfig
    logging: LoggingConfig
    event_bus: EventBusConfig
    trading: TradingConfig
    ui: UIConfig

    # 메타 정보
    app_name: str = "Upbit Auto Trading"
    app_version: str = "1.0.0"
    config_version: str = "1.0"

    def is_development(self) -> bool:
        """개발 환경인지 확인"""
        return self.environment == Environment.DEVELOPMENT

    def is_testing(self) -> bool:
        """테스트 환경인지 확인"""
        return self.environment == Environment.TESTING

    def is_production(self) -> bool:
        """프로덕션 환경인지 확인"""
        return self.environment == Environment.PRODUCTION

    def validate(self) -> List[str]:
        """설정 유효성 검사"""
        errors = []

        # 데이터베이스 경로 검증 (인메모리 DB 제외)
        for db_path in [self.database.settings_db_path,
                        self.database.strategies_db_path,
                        self.database.market_data_db_path]:
            if db_path != ':memory:':
                db_dir = Path(db_path).parent
                if not db_dir.exists():
                    errors.append(f"데이터베이스 디렉토리가 존재하지 않습니다: {db_dir}")

        # 로그 디렉토리 검증 (파일 로깅 사용 시에만)
        if self.logging.file_enabled:
            log_dir = Path(self.logging.file_path).parent
            if not log_dir.exists():
                errors.append(f"로그 디렉토리가 존재하지 않습니다: {log_dir}")

        # API 키 검증 (프로덕션에서 실거래 시에만)
        is_prod = self.is_production()
        is_real_trading = not self.trading.paper_trading
        is_not_testing = not os.getenv('UPBIT_TESTING_MODE')

        if is_prod and is_real_trading and is_not_testing:
            if not self.upbit_api.access_key or not self.upbit_api.secret_key:
                errors.append("프로덕션 환경에서는 Upbit API 키가 필요합니다")

        # 매매 설정 검증
        if self.trading.max_position_size_krw < self.trading.min_order_amount_krw:
            errors.append("최대 포지션 크기가 최소 주문 금액보다 작습니다")

        return errors


# 환경별 기본 설정
DEFAULT_CONFIGS = {
    Environment.DEVELOPMENT: {
        "database": {
            "backup_enabled": False,
            "connection_timeout": 10
        },
        "logging": {
            "level": "DEBUG",
            "console_enabled": True
        },
        "trading": {
            "paper_trading": True,
            "max_position_size_krw": 100000
        },
        "event_bus": {
            "worker_count": 2,
            "storage_cleanup_days": 1
        }
    },
    Environment.TESTING: {
        "database": {
            "settings_db_path": ":memory:",
            "strategies_db_path": ":memory:",
            "market_data_db_path": ":memory:",
            "backup_enabled": False
        },
        "logging": {
            "level": "WARNING",
            "file_enabled": False,
            "console_enabled": False
        },
        "trading": {
            "paper_trading": True,
            "max_position_size_krw": 10000
        },
        "upbit_api": {
            "timeout_seconds": 5,
            "max_retries": 1
        }
    },
    Environment.PRODUCTION: {
        "database": {
            "backup_enabled": True,
            "backup_interval_hours": 6
        },
        "logging": {
            "level": "INFO",
            "console_enabled": False
        },
        "trading": {
            "paper_trading": False,  # 주의: 실제 거래
            "max_orders_per_minute": 5
        },
        "event_bus": {
            "worker_count": 8,
            "storage_cleanup_days": 30
        }
    }
}
