"""
3단계 고급 기능 테스트: SmartRouter WebSocket 강제 선택
연속 요청으로 빈도 분석기가 WebSocket을 선택하도록 유도
"""
import asyncio
import logging
from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.smart_data_router import SmartDataRouter
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.upbit_rest_provider import UpbitRestProvider
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.upbit_websocket_provider import UpbitWebSocketProvider

async def main():
    """3단계: 강제 WebSocket 선택 테스트"""
    logger = create_component_logger("WebSocketForceTest")

    print("🧪 3단계: 강제 WebSocket 선택 테스트 시작")
    print("=" * 50)

    # Provider 초기화
    rest_provider = UpbitRestProvider()
    websocket_provider = UpbitWebSocketProvider()

    # SmartDataRouter 초기화
    router = SmartDataRouter(
        rest_provider=rest_provider,
        websocket_provider=websocket_provider
    )

    try:
        # 빈도 시뮬레이션: 짧은 간격으로 5번 연속 요청
        print("📊 연속 요청으로 빈도 분석 패턴 구축...")
        for i in range(5):
            print(f"   {i+1}/5 캔들 요청 실행 중...")
            start_time = asyncio.get_event_loop().time()

            result = await router.get_candle_data('KRW-BTC', '1m')

            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            print(f"   → 소스: {result.source:>9}, 종가: {result.close:>12,.0f}, 소요시간: {elapsed:>6.1f}ms")

            # 0.05초 간격으로 빠른 요청
            await asyncio.sleep(0.05)

        print("\n🔍 최종 라우팅 정책 확인...")

        # 마지막 테스트: WebSocket이 선택되는지 확인
        final_start = asyncio.get_event_loop().time()
        final_result = await router.get_candle_data('KRW-BTC', '1m')
        final_elapsed = (asyncio.get_event_loop().time() - final_start) * 1000

        print(f"🎯 최종 결과:")
        print(f"   소스: {final_result.source}")
        print(f"   종가: {final_result.close:,.0f}")
        print(f"   소요시간: {final_elapsed:.1f}ms")

        if final_result.source == 'websocket':
            print("✅ SUCCESS: SmartRouter가 WebSocket을 선택했습니다!")
        else:
            print("⚠️ INFO: SmartRouter가 여전히 REST를 선택하고 있습니다")
            print("   (빈도 분석 임계값을 더 조정해야 할 수 있습니다)")

    except Exception as e:
        logger.error(f"❌ 테스트 오류: {e}")
        raise
    finally:
        # 리소스 정리
        print("\n🧹 리소스 정리 중...")
        if hasattr(websocket_provider, 'disconnect'):
            await websocket_provider.disconnect()
        print("✅ 모든 리소스 정리 완료")

    print("\n" + "=" * 50)
    print("🎉 3단계 고급 기능 테스트 완료")

if __name__ == "__main__":
    asyncio.run(main())
