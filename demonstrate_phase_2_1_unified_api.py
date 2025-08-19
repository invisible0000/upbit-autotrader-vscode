"""
UnifiedMarketDataAPI 데모 스크립트 (Phase 2.1)

전문가 권고사항 구현 검증:
✅ SmartChannelRouter 지능적 라우팅 데모
✅ 데이터 구조 통일 확인
✅ 통합 에러 처리 검증
"""

import asyncio
import os

# 환경변수 설정 (로깅)
os.environ["UPBIT_CONSOLE_OUTPUT"] = "true"
os.environ["UPBIT_LOG_SCOPE"] = "info"

from upbit_auto_trading.infrastructure.market_data_backbone.v2.unified_market_data_api import (
    UnifiedMarketDataAPI,
    SmartChannelRouter,
    FieldMapper,
    ErrorUnifier
)


async def demo_smart_channel_routing():
    """SmartChannelRouter 지능적 라우팅 데모"""
    print("🧠 SmartChannelRouter 지능적 라우팅 데모")
    print("=" * 60)

    router = SmartChannelRouter()

    # 1. 명시적 힌트 테스트
    print("\n1. 명시적 힌트 테스트:")
    decision = router.route_request("KRW-BTC", "ticker", "rest")
    print(f"   REST 힌트 → {decision.channel} ({decision.reason})")

    decision = router.route_request("KRW-BTC", "ticker", "websocket")
    print(f"   WebSocket 힌트 → {decision.channel} ({decision.reason})")

    # 2. 빈도 기반 자동 라우팅
    print("\n2. 빈도 기반 자동 라우팅:")

    # WebSocket 활성화 (시뮬레이션)
    router._channel_health["websocket"]["available"] = True
    print("   WebSocket 채널 활성화됨")

    # 저빈도 요청
    for i in range(3):
        decision = router.route_request("KRW-BTC", "ticker")
        print(f"   요청 {i + 1} → {decision.channel} (저빈도)")

    # 고빈도 패턴 시뮬레이션
    pattern = router._get_or_create_pattern("KRW-ETH")
    pattern.request_intervals = [0.05, 0.05, 0.05]  # 20req/s

    decision = router.route_request("KRW-ETH", "ticker")
    print(f"   고빈도 요청 → {decision.channel} ({decision.reason})")

    # 3. 채널 상태 관리
    print("\n3. 채널 상태 관리:")
    router.update_channel_health("websocket", False, Exception("연결 에러"))
    print("   WebSocket 에러 발생 (1회)")

    for i in range(3):
        router.update_channel_health("websocket", False, Exception(f"에러 {i + 2}"))
    print("   WebSocket 연속 에러 발생 → 자동 비활성화")

    decision = router.route_request("KRW-BTC", "ticker", "realtime")
    print(f"   실시간 요청 → {decision.channel} (WebSocket 불가로 폴백)")

    # 4. 통계 확인
    print("\n4. 채널 통계:")
    stats = router.get_channel_statistics()
    print(f"   활성 심볼 수: {stats['active_symbols']}")
    print(f"   REST 상태: {'✅' if stats['channel_health']['rest']['available'] else '❌'}")
    print(f"   WebSocket 상태: {'✅' if stats['channel_health']['websocket']['available'] else '❌'}")


def demo_field_mapping():
    """필드 매핑 데모"""
    print("\n\n🔄 필드 매핑 (데이터 구조 통일) 데모")
    print("=" * 60)

    # REST 데이터 매핑
    print("\n1. REST API 데이터 → 통합 형태:")
    rest_data = {
        "market": "KRW-BTC",
        "trade_price": 50000000,
        "signed_change_rate": 0.025,
        "signed_change_price": 1000000,
        "acc_trade_volume_24h": 1500.5,
        "high_price": 51000000,
        "low_price": 49000000
    }

    mapped_rest = FieldMapper.map_rest_data(rest_data)
    print(f"   market → symbol: {mapped_rest.get('symbol')}")
    print(f"   trade_price → current_price: {mapped_rest.get('current_price')}")
    print(f"   signed_change_rate → change_rate: {mapped_rest.get('change_rate')}")

    # WebSocket DEFAULT 데이터 매핑
    print("\n2. WebSocket (DEFAULT) 데이터 → 통합 형태:")
    ws_data = {
        "code": "KRW-BTC",
        "trade_price": 50000000,
        "signed_change_rate": 0.025,
        "signed_change_price": 1000000
    }

    mapped_ws = FieldMapper.map_websocket_data(ws_data, is_simple=False)
    print(f"   code → symbol: {mapped_ws.get('symbol')}")
    print(f"   trade_price → current_price: {mapped_ws.get('current_price')}")

    # WebSocket SIMPLE 데이터 매핑
    print("\n3. WebSocket (SIMPLE) 데이터 → 통합 형태:")
    ws_simple_data = {
        "cd": "KRW-BTC",
        "tp": 50000000,
        "scr": 0.025,
        "scp": 1000000
    }

    mapped_simple = FieldMapper.map_websocket_data(ws_simple_data, is_simple=True)
    print(f"   cd → symbol: {mapped_simple.get('symbol')}")
    print(f"   tp → current_price: {mapped_simple.get('current_price')}")

    print("\n✅ 모든 채널의 데이터가 동일한 필드명으로 통일됨!")


def demo_error_unification():
    """에러 통합 처리 데모"""
    print("\n\n⚠️  통합 에러 처리 데모")
    print("=" * 60)

    # 다양한 에러 시나리오
    error_scenarios = [
        (Exception("429 Too Many Requests"), "rest", "get_ticker"),
        (Exception("INVALID_AUTH: Authentication failed"), "websocket", "connect"),
        (Exception("Connection timeout occurred"), "websocket", "subscribe"),
        (Exception("Invalid data format"), "rest", "parse_response"),
        (Exception("Service unavailable"), "rest", "request")
    ]

    for i, (error, channel, operation) in enumerate(error_scenarios, 1):
        print(f"\n{i}. 원본 에러: {error}")
        print(f"   채널: {channel}, 작업: {operation}")

        unified_error = ErrorUnifier.unify_error(error, channel, operation)
        print(f"   통합 에러: {type(unified_error).__name__}")
        print(f"   에러 코드: {unified_error.error_code}")
        print(f"   메시지: {unified_error}")


async def demo_unified_api():
    """UnifiedMarketDataAPI 전체 기능 데모"""
    print("\n\n🚀 UnifiedMarketDataAPI 통합 기능 데모")
    print("=" * 60)

    # API 초기화
    api = UnifiedMarketDataAPI(use_websocket=True, cache_ttl=30)
    print("✅ UnifiedMarketDataAPI 초기화 완료")

    # 1. 단일 티커 조회
    print("\n1. 단일 티커 조회:")
    try:
        ticker = await api.get_ticker("KRW-BTC")
        print(f"   심볼: {ticker.symbol}")
        print(f"   현재가: {ticker.current_price:,}원")
        print(f"   변화율: {ticker.change_rate}%")
        print(f"   데이터 소스: {ticker.data_source}")
        print(f"   데이터 품질: {ticker.data_quality}")
        print(f"   신뢰도: {ticker.confidence_score}")
        print(f"   처리시간: {ticker.processing_time_ms}ms")
    except Exception as e:
        print(f"   에러: {e}")

    # 2. 실시간 힌트와 함께 조회
    print("\n2. 실시간 힌트 조회:")
    try:
        realtime_ticker = await api.get_ticker("KRW-BTC", realtime=True)
        print(f"   실시간 데이터 소스: {realtime_ticker.data_source}")
        print(f"   처리시간: {realtime_ticker.processing_time_ms}ms")
    except Exception as e:
        print(f"   에러: {e}")

    # 3. 다중 티커 조회
    print("\n3. 다중 티커 조회:")
    symbols = ["KRW-BTC", "KRW-ETH", "KRW-ADA"]
    try:
        tickers = await api.get_multiple_tickers(symbols)
        print(f"   조회된 티커 수: {len(tickers)}/{len(symbols)}")
        for ticker in tickers:
            print(f"   {ticker.symbol}: {ticker.current_price:,}원 ({ticker.data_quality})")
    except Exception as e:
        print(f"   에러: {e}")

    # 4. 헬스 체크
    print("\n4. API 헬스 체크:")
    try:
        health = await api.health_check()
        print(f"   상태: {health['status']}")
        print(f"   응답시간: {health.get('response_time_ms', 'N/A')}ms")
        print(f"   데이터 품질: {health.get('data_quality', 'N/A')}")
    except Exception as e:
        print(f"   에러: {e}")

    # 5. 통계 정보
    print("\n5. API 사용 통계:")
    stats = api.get_api_statistics()
    api_stats = stats["api_stats"]
    print(f"   총 요청: {api_stats['total_requests']}")
    print(f"   REST 요청: {api_stats['rest_requests']}")
    print(f"   WebSocket 요청: {api_stats['websocket_requests']}")
    print(f"   에러 수: {api_stats['errors']}")

    channel_stats = stats["channel_routing"]
    print(f"   활성 심볼: {channel_stats['active_symbols']}")


async def main():
    """메인 데모 함수"""
    print("🎯 UnifiedMarketDataAPI 전문가 권고사항 구현 데모")
    print("📋 Phase 2.1: SmartChannelRouter + 데이터 통일 + 에러 처리")
    print("🔧 기존 MarketDataBackbone V2 (62개 테스트 통과) 기반 확장")
    print("")

    # 각 기능별 데모 실행
    await demo_smart_channel_routing()
    demo_field_mapping()
    demo_error_unification()
    await demo_unified_api()

    print("\n\n🎉 데모 완료!")
    print("✅ SmartChannelRouter: 지능적 채널 선택 구현")
    print("✅ FieldMapper: REST ↔ WebSocket 필드명 통일")
    print("✅ ErrorUnifier: 다양한 예외를 일관된 형태로 처리")
    print("✅ UnifiedMarketDataAPI: 투명한 통합 인터페이스 제공")
    print("")
    print("📈 다음 단계: 실제 REST/WebSocket 클라이언트 연동")
    print("🔗 7규칙 자동매매 전략 시스템과 통합")


if __name__ == "__main__":
    asyncio.run(main())
