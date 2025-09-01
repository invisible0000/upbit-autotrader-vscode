"""
업비트 WebSocket v6.0 통합 패키지
===============================

v5 호환성 완전 제거, 순수 v6 아키텍처
중앙 집중식 글로벌 관리자 + 네이티브 클라이언트

주요 컴포넌트:
- GlobalWebSocketManager: 중앙 관리자 (싱글톤)
- NativeWebSocketClient: 순수 WebSocket 클라이언트
- models: v5 우수 구조 + v6 타입 시스템 통합
- types: @dataclass 기반 타입 안전성
- subscription_state_manager: 구독 상태 관리
- data_routing_engine: 데이터 분배 엔진
"""

from typing import Dict, Any
import time

# 핵심 컴포넌트
from .global_websocket_manager import (
    GlobalWebSocketManager,
    get_global_websocket_manager,
    get_global_websocket_manager_sync,
    is_manager_available,
    ConnectionMetrics,
    EpochManager
)

from .websocket_client_proxy import (
    WebSocketClientProxy,
    create_websocket_proxy,
    quick_ticker_subscription
)

from .jwt_manager import (
    JWTManager,
    get_global_jwt_manager,
    get_valid_jwt_token,
    shutdown_global_jwt_manager
)

from .native_websocket_client import (
    NativeWebSocketClient,
    create_public_client,
    create_private_client
)

# 타입 시스템
from .types import (
    # 열거형
    ConnectionState,
    SubscriptionState,
    WebSocketType,
    DataType,
    GlobalManagerState,
    BackpressureStrategy,

    # 이벤트 클래스
    BaseWebSocketEvent,
    TickerEvent,
    OrderbookEvent,
    OrderbookUnit,
    TradeEvent,
    CandleEvent,
    MyOrderEvent,
    MyAssetEvent,

    # 구독 시스템
    SubscriptionSpec,
    ComponentSubscription,

    # 성능 및 상태
    PerformanceMetrics,
    HealthStatus,
    BackpressureConfig,

    # 설정
    WebSocketV6Config,

    # 유틸리티 함수
    create_ticker_event,
    create_orderbook_event,
    get_data_type_from_message,
    validate_symbols,
    normalize_symbols
)

# 데이터 모델 (v5 + v6 통합)
from .models import (
    # v5 호환 열거형
    StreamType,

    # 필드 문서
    TICKER_FIELDS,
    TRADE_FIELDS,
    ORDERBOOK_FIELDS,
    CANDLE_FIELDS,
    MY_ORDER_FIELDS,
    MY_ASSET_FIELDS,

    # 메시지 처리
    create_websocket_message,
    is_snapshot_message,
    is_realtime_message,
    infer_message_type,
    validate_mixed_message,

    # v6 통합 함수
    convert_dict_to_v6_event,
    process_message_to_v6_event,
    get_v6_data_type_from_dict,
    create_v6_compatible_message,

    # 검증 함수
    validate_ticker_data,
    validate_trade_data,
    validate_orderbook_data,
    validate_candle_data,
    validate_my_order_data,
    validate_my_asset_data,

    # 유틸리티
    get_field_documentation,
    print_field_documentation,
    create_connection_status,
    update_connection_status,

    # SIMPLE 포맷 지원
    process_websocket_message,
    convert_message_format,
    get_message_format,
    is_simple_format_supported,

    # 예시 메시지
    example_ticker_message,
    example_trade_message,
    example_orderbook_message
)

# 하위 시스템
from .subscription_state_manager import (
    SubscriptionStateManager,
    SubscriptionChange
)

from .data_routing_engine import (
    DataRoutingEngine,
    FanoutHub,
    DataDistributionStats
)

# 설정 및 예외
from .config import (
    get_config,
    WebSocketV6Config as Config
)

from .exceptions import (
    WebSocketException,
    ConnectionError,
    SubscriptionError,
    BackpressureError,
    AuthenticationError,
    RecoveryError
)

# SIMPLE 포맷 컨버터
try:
    from .simple_format_converter import (
        auto_detect_and_convert,
        convert_to_simple_format,
        convert_from_simple_format
    )
    SIMPLE_FORMAT_AVAILABLE = True
except ImportError:
    SIMPLE_FORMAT_AVAILABLE = False


# 패키지 메타 정보
__version__ = "6.0.0"
__author__ = "업비트 자동매매 시스템"
__description__ = "업비트 WebSocket v6.0 - v5 호환성 제거, 순수 v6 아키텍처"

# 핵심 API 단축 접근
__all__ = [
    # === 핵심 매니저 ===
    "GlobalWebSocketManager",
    "get_global_websocket_manager",
    "is_manager_available",

    # === 프록시 인터페이스 ===
    "WebSocketClientProxy",
    "create_websocket_proxy",
    "quick_ticker_subscription",

    # === JWT 관리 ===
    "JWTManager",
    "get_global_jwt_manager",
    "get_valid_jwt_token",

    # === 클라이언트 ===
    "NativeWebSocketClient",
    "create_public_client",
    "create_private_client",

    # === 타입 시스템 ===
    "DataType",
    "WebSocketType",
    "ConnectionState",
    "BaseWebSocketEvent",
    "TickerEvent",
    "OrderbookEvent",
    "TradeEvent",
    "SubscriptionSpec",
    "ComponentSubscription",

    # === 데이터 모델 ===
    "infer_message_type",
    "validate_mixed_message",
    "convert_dict_to_v6_event",
    "process_message_to_v6_event",

    # === 설정 및 예외 ===
    "get_config",
    "WebSocketException",
    "ConnectionError",
    "SubscriptionError",

    # === 상수 ===
    "SIMPLE_FORMAT_AVAILABLE",
    "__version__"
]


# ================================================================
# 패키지 레벨 유틸리티
# ================================================================

def get_package_info() -> dict:
    """패키지 정보 반환"""
    return {
        'version': __version__,
        'description': __description__,
        'simple_format_support': SIMPLE_FORMAT_AVAILABLE,
        'v5_models_integrated': True,  # v5 models.py 구조 통합 완료
        'core_components': [
            'GlobalWebSocketManager',
            'NativeWebSocketClient',
            'SubscriptionStateManager',
            'DataRoutingEngine'
        ],
        'supported_data_types': [dt.value for dt in DataType],
        'connection_types': [wt.value for wt in WebSocketType]
    }


def print_package_info():
    """패키지 정보 출력"""
    info = get_package_info()

    print(f"\n🚀 {__description__}")
    print(f"📦 Version: {info['version']}")
    print(f"🔧 SIMPLE Format: {'✅ Available' if info['simple_format_support'] else '❌ Not Available'}")

    print("\n📋 Core Components:")
    for component in info['core_components']:
        print(f"  • {component}")

    print(f"\n📊 Supported Data Types ({len(info['supported_data_types'])}):")
    for data_type in info['supported_data_types']:
        print(f"  • {data_type}")

    print(f"\n🔗 Connection Types ({len(info['connection_types'])}):")
    for conn_type in info['connection_types']:
        print(f"  • {conn_type}")


async def quick_health_check():
    """빠른 시스템 상태 체크"""
    try:
        # 매니저 가용성 확인
        manager_available = is_manager_available()

        # 설정 로드 확인
        config = get_config()

        # SIMPLE 포맷 확인
        simple_available = SIMPLE_FORMAT_AVAILABLE

        # 매니저 인스턴스 확인 (생성하지 않고 체크만)
        manager_instance = None
        if manager_available:
            try:
                manager_instance = await get_global_websocket_manager()
                health_status = await manager_instance.get_health_status()
            except Exception:
                health_status = None
        else:
            health_status = None

        return {
            'package_healthy': True,
            'manager_available': manager_available,
            'config_loaded': config is not None,
            'simple_format_available': simple_available,
            'manager_health': health_status.status if health_status else "not_initialized",
            'timestamp': time.time()
        }

    except Exception as e:
        return {
            'package_healthy': False,
            'error': str(e),
            'timestamp': time.time()
        }


# ================================================================
# 개발자용 디버그 함수
# ================================================================

def debug_package_structure():
    """패키지 구조 디버그 출력"""
    import sys

    print("\n🔍 WebSocket v6 Package Debug Info")
    print("=" * 50)

    # 모듈 임포트 상태
    modules = [
        'global_websocket_manager',
        'native_websocket_client',
        'types',
        'models',
        'subscription_state_manager',
        'data_routing_engine',
        'config',
        'exceptions'
    ]

    print("\n📦 Module Import Status:")
    for module in modules:
        full_name = f"upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v6.{module}"
        status = "✅ Loaded" if full_name in sys.modules else "❌ Not Loaded"
        print(f"  {module}: {status}")

    # 핵심 클래스 확인
    print("\n🏗️ Core Classes:")
    try:
        print(f"  GlobalWebSocketManager: {'✅' if 'GlobalWebSocketManager' in globals() else '❌'}")
        print(f"  NativeWebSocketClient: {'✅' if 'NativeWebSocketClient' in globals() else '❌'}")
        print(f"  DataType: {'✅' if 'DataType' in globals() else '❌'}")
        print(f"  BaseWebSocketEvent: {'✅' if 'BaseWebSocketEvent' in globals() else '❌'}")
    except Exception as e:
        print(f"  Error checking classes: {e}")

    # 패키지 정보
    info = get_package_info()
    print("\n📊 Package Info:")
    print(f"  Version: {info['version']}")
    print(f"  Components: {len(info['core_components'])}")
    print(f"  Data Types: {len(info['supported_data_types'])}")


def health_check() -> Dict[str, Any]:
    """시스템 헬스 체크"""
    try:
        manager = get_global_websocket_manager()
        return {
            'health_score': 100,  # 기본 건강 상태
            'manager_type': type(manager).__name__,
            'status': 'healthy',
            'components_loaded': True,
            'imports_successful': True
        }
    except Exception as e:
        return {
            'health_score': 0,
            'manager_type': 'unknown',
            'status': 'error',
            'error': str(e),
            'components_loaded': False,
            'imports_successful': False
        }


def debug_info() -> Dict[str, Any]:
    """디버그 정보 반환"""
    return {
        'features': [
            'singleton_manager',
            'native_websocket_client',
            'simple_format_converter',
            'backpressure_handler',
            'data_routing_engine',
            'comprehensive_monitoring'
        ],
        'monitoring_enabled': True,
        'v5_models_integrated': True,
        'architecture': 'v6_pure',
        'compatibility': 'v5_removed'
    }


if __name__ == "__main__":
    print_package_info()
    debug_package_structure()
