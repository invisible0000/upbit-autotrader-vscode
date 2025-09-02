"""
WebSocket v6.0 간소화된 패키지
============================

사용자 친화적인 단일 인터페이스 제공
- 내부 복잡성 완전 숨김
- 네이티브 연결 로직 통합
- 4개 핵심 파일로 구성

핵심 컴포넌트:
- WebSocketClient: 유일한 사용자 인터페이스
- WebSocketManager: 내부 중앙 관리자 (네이티브 로직 포함)
- websocket_types: 통합 타입 시스템
- websocket_config: 설정 및 예외 관리
"""

import time
from typing import Dict, Any

# 핵심 사용자 인터페이스
from .core.websocket_client import (
    WebSocketClient,
    create_websocket_client,
    quick_ticker_subscription
)

# 내부 관리자 (고급 사용자용)
from .core.websocket_manager import (
    WebSocketManager,
    get_websocket_manager
)

# 타입 시스템
from .core.websocket_types import (
    # 열거형
    ConnectionState,
    SubscriptionState,
    WebSocketType,
    DataType,
    GlobalManagerState,
    BackpressureStrategy,
    StreamType,

    # 이벤트 클래스
    BaseWebSocketEvent,
    TickerEvent,
    OrderbookEvent,
    OrderbookUnit,
    TradeEvent,
    CandleEvent,
    MyOrderEvent,
    MyAssetEvent,

    # 구독 및 성능
    SubscriptionSpec,
    ComponentSubscription,
    PerformanceMetrics,
    HealthStatus,
    BackpressureConfig,
    ConnectionMetrics,

    # 필드 문서 (v5 호환성)
    TICKER_FIELDS,
    TRADE_FIELDS,
    ORDERBOOK_FIELDS,
    CANDLE_FIELDS,
    MY_ORDER_FIELDS,
    MY_ASSET_FIELDS,

    # 유틸리티 함수
    create_ticker_event,
    create_orderbook_event,
    get_data_type_from_message,
    infer_message_type,
    convert_dict_to_event,
    validate_symbols,
    normalize_symbols
)

# 설정 및 예외
from .support.websocket_config import (
    # 예외 클래스
    WebSocketException,
    ConnectionError,
    SubscriptionError,
    AuthenticationError,
    BackpressureError,
    RecoveryError,

    # 설정 클래스
    WebSocketConfig,
    ConnectionConfig,
    ReconnectionConfig,
    AuthConfig,
    MonitoringConfig,
    Environment,

    # 설정 함수
    get_config,
    reset_config,
    set_config,
    is_development,
    is_production,
    get_connection_config,
    get_reconnection_config
)

# JWT 관리 (Private 기능용)
from .support.jwt_manager import (
    JWTManager,
    get_global_jwt_manager,
    get_valid_jwt_token,
    shutdown_global_jwt_manager
)

# 포맷 변환 (SIMPLE 형식 지원)
from .support.format_utils import (
    UpbitMessageFormatter
)


# ================================================================
# 패키지 메타 정보
# ================================================================

__version__ = "6.1.0"
__author__ = "업비트 자동매매 시스템"
__description__ = "WebSocket v6.0 간소화 - 사용자 친화적 단일 인터페이스"

# 핵심 API (사용자가 알아야 할 것들만)
__all__ = [
    # === 메인 인터페이스 (95% 사용자가 이것만 사용) ===
    "WebSocketClient",
    "create_websocket_client",
    "quick_ticker_subscription",

    # === 이벤트 타입 (콜백에서 사용) ===
    "TickerEvent",
    "OrderbookEvent",
    "TradeEvent",
    "CandleEvent",
    "MyOrderEvent",
    "MyAssetEvent",

    # === 기본 열거형 ===
    "DataType",
    "WebSocketType",
    "ConnectionState",

    # === 상태 조회 ===
    "HealthStatus",
    "PerformanceMetrics",

    # === 예외 처리 ===
    "WebSocketException",
    "ConnectionError",
    "SubscriptionError",
    "AuthenticationError",

    # === 설정 (필요시) ===
    "get_config",
    "is_development",
    "is_production",

    # === 고급 기능 (전문가용) ===
    "WebSocketManager",
    "get_websocket_manager",
    "get_system_status",

    # === 포맷 변환 ===
    "UpbitMessageFormatter",

    # === 메타 정보 ===
    "__version__"
]


# ================================================================
# 패키지 레벨 유틸리티
# ================================================================

def get_package_info() -> Dict[str, Any]:
    """패키지 정보 반환"""
    return {
        'version': __version__,
        'description': __description__,
        'architecture': 'simplified_v6',
        'core_files': [
            'websocket_client.py',
            'websocket_manager.py',
            'websocket_types.py',
            'websocket_config.py'
        ],
        'supported_data_types': [dt.value for dt in DataType],
        'connection_types': [wt.value for wt in WebSocketType],
        'native_integration': True,
        'user_friendly': True
    }


def print_package_info():
    """패키지 정보 출력"""
    info = get_package_info()

    print(f"\n🚀 {__description__}")
    print(f"📦 Version: {info['version']}")
    print(f"🏗️ Architecture: {info['architecture']}")

    print(f"\n📁 Core Files ({len(info['core_files'])}):")
    for file in info['core_files']:
        print(f"  • {file}")

    print(f"\n📊 Supported Data Types ({len(info['supported_data_types'])}):")
    for data_type in info['supported_data_types']:
        print(f"  • {data_type}")

    print(f"\n🔗 Connection Types ({len(info['connection_types'])}):")
    for conn_type in info['connection_types']:
        print(f"  • {conn_type}")

    print("\n✨ Features:")
    print(f"  • Native Integration: {info['native_integration']}")
    print(f"  • User Friendly: {info['user_friendly']}")


async def quick_health_check():
    """빠른 시스템 상태 체크"""
    try:
        # 설정 로드 확인
        config = get_config()

        # 매니저 인스턴스 확인
        health_status = None
        try:
            manager = await get_websocket_manager()
            health_status = manager.get_health_status()
        except Exception:
            health_status = None

        return {
            'package_healthy': True,
            'manager_available': health_status is not None,
            'config_loaded': config is not None,
            'manager_health': health_status.status if health_status else "not_initialized",
            'architecture': 'simplified_v6',
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

    print("\n🔍 WebSocket v6 Simplified Package Debug")
    print("=" * 55)

    # 모듈 임포트 상태
    modules = [
        'core.websocket_client',
        'core.websocket_manager',
        'core.websocket_types',
        'support.websocket_config',
        'support.jwt_manager'
    ]

    print("\n📦 Module Import Status:")
    for module in modules:
        full_name = f"upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v6.{module}"
        status = "✅ Loaded" if full_name in sys.modules else "❌ Not Loaded"
        print(f"  {module}: {status}")

    # 핵심 클래스 확인
    print("\n🏗️ Core Classes:")
    try:
        print(f"  WebSocketClient: {'✅' if 'WebSocketClient' in globals() else '❌'}")
        print(f"  WebSocketManager: {'✅' if 'WebSocketManager' in globals() else '❌'}")
        print(f"  DataType: {'✅' if 'DataType' in globals() else '❌'}")
        print(f"  BaseWebSocketEvent: {'✅' if 'BaseWebSocketEvent' in globals() else '❌'}")
    except Exception as e:
        print(f"  Error checking classes: {e}")

    # 패키지 정보
    info = get_package_info()
    print("\n📊 Package Info:")
    print(f"  Version: {info['version']}")
    print(f"  Architecture: {info['architecture']}")
    print(f"  Core Files: {len(info['core_files'])}")
    print(f"  Data Types: {len(info['supported_data_types'])}")


# ================================================================
# 사용 예제 (문서화용)
# ================================================================

def print_usage_examples():
    """사용 예제 출력"""
    print("\n📖 WebSocket v6.0 Usage Examples")
    print("=" * 40)

    print("\n🎯 Basic Usage (현재가 구독):")
    print("""
from websocket_v6 import WebSocketClient

async def my_callback(event):
    print(f"가격: {event.symbol} = {event.trade_price}")

async with WebSocketClient("my_app") as client:
    await client.subscribe_ticker(["KRW-BTC"], my_callback)
    # 자동으로 정리됨
""")

    print("\n📊 Multiple Data Types:")
    print("""
async with WebSocketClient("trading_bot") as client:
    await client.subscribe_ticker(["KRW-BTC"], ticker_callback)
    await client.subscribe_orderbook(["KRW-BTC"], orderbook_callback)
    await client.subscribe_candle(["KRW-BTC"], candle_callback, unit="5m")
""")

    print("\n🔒 Private Data (API 키 필요):")
    print("""
async with WebSocketClient("my_orders") as client:
    await client.subscribe_my_order(order_callback)
    await client.subscribe_my_asset(asset_callback)
""")

    print("\n⚡ Quick Setup:")
    print("""
from websocket_v6 import quick_ticker_subscription

client = await quick_ticker_subscription(
    "quick_price",
    ["KRW-BTC", "KRW-ETH"],
    lambda event: print(f"{event.symbol}: {event.trade_price}")
)
""")


if __name__ == "__main__":
    print_package_info()
    print_usage_examples()
    debug_package_structure()


# ================================================================
# 시스템 상태 조회 함수
# ================================================================

async def get_system_status() -> Dict[str, Any]:
    """
    WebSocket v6 시스템 전체 상태 조회

    Returns:
        Dict[str, Any]: 시스템 상태 정보
            - package_healthy: 패키지 건강 상태
            - manager_available: 매니저 가용성
            - config_loaded: 설정 로드 상태
            - manager_health: 매니저 건강 상태
            - architecture: 아키텍처 버전
            - timestamp: 조회 시각
    """
    try:
        # 설정 로드 확인
        config = get_config()

        # 매니저 인스턴스 확인
        health_status = None
        try:
            manager = await get_websocket_manager()
            health_status = manager.get_health_status()
        except Exception:
            health_status = None

        return {
            'package_healthy': True,
            'manager_available': health_status is not None,
            'config_loaded': config is not None,
            'manager_health': health_status.status if health_status else "not_initialized",
            'architecture': 'simplified_v6',
            'timestamp': time.time()
        }

    except Exception as e:
        return {
            'package_healthy': False,
            'manager_available': False,
            'config_loaded': False,
            'manager_health': "error",
            'architecture': 'simplified_v6',
            'error': str(e),
            'timestamp': time.time()
        }
