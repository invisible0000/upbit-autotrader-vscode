"""
업비트 클라이언트 함수명 충돌 분석 보고서

동일한 코드에서 여러 클라이언트를 import할 때 발생할 수 있는
함수명 충돌 상황을 조사하고 해결방안을 제시합니다.
"""

# ================================================================
# 분석 대상 클라이언트
# ================================================================

CLIENTS = {
    "UpbitPublicClient": "REST API 공개 데이터",
    "UpbitPrivateClient": "REST API 인증 데이터",
    "UpbitWebSocketPublicV5": "WebSocket 공개 데이터",
    "UpbitWebSocketPrivateV5": "WebSocket 인증 데이터",
    "rest_to_websocket_converter": "데이터 변환 함수들"
}

# ================================================================
# 🔴 심각한 충돌 (동일한 함수명 + 다른 기능)
# ================================================================

CRITICAL_CONFLICTS = {
    "get_status": {
        "클라이언트": ["UpbitWebSocketPublicV5", "UpbitWebSocketPrivateV5"],
        "리스크": "높음",
        "설명": "WebSocket 연결 상태 조회",
        "충돌상황": "같은 이름이지만 Public/Private 별도 상태",
        "해결방안": "클래스 기반 import 사용 권장"
    },

    "health_check": {
        "클라이언트": ["UpbitWebSocketPublicV5", "UpbitWebSocketPrivateV5"],
        "리스크": "높음",
        "설명": "WebSocket 건강 상태 체크",
        "충돌상황": "같은 이름이지만 Public/Private 별도 체크",
        "해결방안": "클래스 기반 import 사용 권장"
    },

    "connect": {
        "클라이언트": ["UpbitWebSocketPublicV5", "UpbitWebSocketPrivateV5"],
        "리스크": "높음",
        "설명": "WebSocket 연결 생성",
        "충돌상황": "같은 이름이지만 Public/Private 연결 방식 다름",
        "해결방안": "클래스 기반 import 사용 권장"
    },

    "disconnect": {
        "클라이언트": ["UpbitWebSocketPublicV5", "UpbitWebSocketPrivateV5"],
        "리스크": "높음",
        "설명": "WebSocket 연결 해제",
        "충돌상황": "같은 이름이지만 Public/Private 연결 해제 다름",
        "해결방안": "클래스 기반 import 사용 권장"
    }
}

# ================================================================
# 🟡 중간 충돌 (동일한 함수명 + 비슷한 기능)
# ================================================================

MODERATE_CONFLICTS = {
    "subscribe": {
        "클라이언트": ["UpbitWebSocketPublicV5", "UpbitWebSocketPrivateV5"],
        "리스크": "중간",
        "설명": "데이터 구독",
        "충돌상황": "비슷한 기능이지만 Public/Private 데이터 구독 방식 다름",
        "해결방안": "클래스 기반 import 또는 alias 사용"
    },

    "unsubscribe": {
        "클라이언트": ["UpbitWebSocketPublicV5", "UpbitWebSocketPrivateV5"],
        "리스크": "중간",
        "설명": "구독 해제",
        "충돌상황": "비슷한 기능이지만 Public/Private 구독 해제 방식 다름",
        "해결방안": "클래스 기반 import 또는 alias 사용"
    },

    "unsubscribe_all": {
        "클라이언트": ["UpbitWebSocketPublicV5", "UpbitWebSocketPrivateV5"],
        "리스크": "중간",
        "설명": "모든 구독 해제",
        "충돌상황": "비슷한 기능이지만 Public/Private 전체 해제 방식 다름",
        "해결방안": "클래스 기반 import 또는 alias 사용"
    },

    "get_accounts": {
        "클라이언트": ["UpbitPrivateClient"],
        "리스크": "낮음",
        "설명": "계좌/자산 정보 조회",
        "충돌상황": "Private Client에만 존재하므로 현재 충돌 없음",
        "해결방안": "현재 문제없음, 향후 확장 시 주의"
    }
}

# ================================================================
# 🟢 안전 영역 (고유한 함수명들)
# ================================================================

UNIQUE_FUNCTIONS = {
    "UpbitPublicClient": [
        "get_market_all", "get_candle_seconds", "get_candle_minutes",
        "get_candle_days", "get_candle_weeks", "get_candle_months",
        "get_candle_years", "get_trades_ticks", "get_ticker", "get_orderbook",
        "get_single_ticker", "get_single_orderbook", "get_krw_markets",
        "get_btc_markets", "get_usdt_markets", "get_rate_limit_status"
    ],

    "UpbitPrivateClient": [
        "get_orders_chance", "place_order", "get_order", "get_orders",
        "get_open_orders", "get_closed_orders", "cancel_order",
        "cancel_orders_by_ids", "batch_cancel_orders", "get_trades_history"
    ],

    "UpbitWebSocketPublicV5": [
        "subscribe_ticker", "subscribe_trade", "subscribe_orderbook",
        "subscribe_candle", "is_connected"
    ],

    "UpbitWebSocketPrivateV5": [
        "subscribe_my_orders", "subscribe_my_assets", "rotate_jwt_token",
        "get_auth_status", "get_supported_data_types"
    ],

    "rest_to_websocket_converter": [
        "convert_rest_ticker_to_websocket", "convert_rest_orderbook_to_websocket",
        "convert_rest_candle_to_websocket", "convert_rest_trades_to_websocket",
        "convert_rest_order_to_websocket", "convert_rest_asset_to_websocket",
        "convert_websocket_asset_to_rest", "convert_websocket_order_to_rest",
        "create_unified_response", "batch_convert_rest_to_websocket"
    ]
}

# ================================================================
# 🔧 권장 Import 패턴
# ================================================================

RECOMMENDED_IMPORT_PATTERNS = {

    "🟢 안전한 패턴 - 클래스 기반 Import": """
# 권장: 클래스별로 import하여 네임스페이스 분리
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_private_client import UpbitPrivateClient
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5.upbit_websocket_public_client import UpbitWebSocketPublicV5
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5.upbit_websocket_private_client import UpbitWebSocketPrivateV5

# 사용 예시
public_rest = UpbitPublicClient()
private_rest = UpbitPrivateClient(access_key="...", secret_key="...")
public_ws = UpbitWebSocketPublicV5()
private_ws = UpbitWebSocketPrivateV5(access_key="...", secret_key="...")

# 충돌 없이 각각의 메서드 사용 가능
await public_ws.get_status()   # Public WebSocket 상태
await private_ws.get_status()  # Private WebSocket 상태
""",

    "🟡 주의 패턴 - Alias 사용": """
# 주의깊게 사용: alias로 구분
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5.upbit_websocket_public_client import UpbitWebSocketPublicV5 as PublicWS
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5.upbit_websocket_private_client import UpbitWebSocketPrivateV5 as PrivateWS

# 사용 예시
public_ws = PublicWS()
private_ws = PrivateWS()

await public_ws.connect()   # Public 연결
await private_ws.connect()  # Private 연결
""",

    "🔴 위험한 패턴 - 직접 함수 Import": """
# 🚨 권장하지 않음: 함수명 충돌 발생 가능
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5.upbit_websocket_public_client import connect, get_status
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5.upbit_websocket_private_client import connect, get_status  # ❌ 충돌!

# 마지막 import가 이전 것을 덮어씀
await connect()     # ❓ Public? Private? 예측 불가능
await get_status()  # ❓ Public? Private? 예측 불가능
""",

    "🟢 변환기 함수는 안전": """
# 변환기 함수들은 고유한 이름으로 안전
from upbit_auto_trading.infrastructure.external_apis.upbit.rest_to_websocket_converter import (
    convert_rest_ticker_to_websocket,
    convert_rest_asset_to_websocket,
    create_unified_response
)
""",

    "🟢 컨텍스트 매니저 패턴": """
# 가장 안전한 사용 패턴
async with UpbitPublicClient() as public_client:
    ticker = await public_client.get_ticker("KRW-BTC")

async with UpbitPrivateClient(access_key="...", secret_key="...") as private_client:
    accounts = await private_client.get_accounts()

async with UpbitWebSocketPublicV5() as public_ws:
    await public_ws.subscribe_ticker(["KRW-BTC"], callback)

async with UpbitWebSocketPrivateV5() as private_ws:
    await private_ws.subscribe_my_orders(callback=callback)
"""
}

# ================================================================
# 🚨 실제 충돌 시나리오
# ================================================================

REAL_WORLD_CONFLICTS = {
    "시나리오 1 - 혼합 WebSocket 사용": {
        "상황": "Public과 Private WebSocket을 동시에 사용",
        "충돌함수": ["connect", "disconnect", "get_status", "health_check"],
        "문제": "어떤 연결의 상태인지 구분 불가능",
        "해결": "클래스 기반 import로 네임스페이스 분리"
    },

    "시나리오 2 - 통합 모니터링": {
        "상황": "모든 클라이언트 상태를 통합 모니터링",
        "충돌함수": ["get_status", "health_check"],
        "문제": "각각의 상태를 개별적으로 확인해야 함",
        "해결": "각 클라이언트별 상태 체크 함수 분리"
    },

    "시나리오 3 - 자동 재연결": {
        "상황": "연결 장애 시 자동 재연결 로직",
        "충돌함수": ["connect", "disconnect", "is_connected"],
        "문제": "어떤 연결을 재시작할지 모호함",
        "해결": "클라이언트별 재연결 관리자 분리"
    }
}

# ================================================================
# 📋 최종 권장사항
# ================================================================

FINAL_RECOMMENDATIONS = [
    "✅ 항상 클래스 기반 import 사용: from module import ClassName",
    "✅ 컨텍스트 매니저 패턴 활용: async with ClassName() as client",
    "✅ 변환기 함수는 안전하므로 직접 import 가능",
    "⚠️ 동일한 함수명이 있는 모듈에서는 직접 함수 import 금지",
    "⚠️ alias 사용 시 명확한 이름으로 구분",
    "❌ from module import * 절대 사용 금지"
]

def analyze_conflicts():
    """충돌 분석 결과 출력"""
    print("🔍 업비트 클라이언트 함수명 충돌 분석")
    print("=" * 60)

    print(f"\n🔴 심각한 충돌: {len(CRITICAL_CONFLICTS)}개")
    for func, info in CRITICAL_CONFLICTS.items():
        print(f"  • {func}: {info['설명']} (리스크: {info['리스크']})")

    print(f"\n🟡 중간 충돌: {len(MODERATE_CONFLICTS)}개")
    for func, info in MODERATE_CONFLICTS.items():
        print(f"  • {func}: {info['설명']} (리스크: {info['리스크']})")

    print(f"\n🟢 고유 함수:")
    for client, functions in UNIQUE_FUNCTIONS.items():
        print(f"  • {client}: {len(functions)}개 고유 함수")

    print(f"\n📋 권장사항:")
    for rec in FINAL_RECOMMENDATIONS:
        print(f"  {rec}")

if __name__ == "__main__":
    analyze_conflicts()
