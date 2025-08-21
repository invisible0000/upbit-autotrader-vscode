"""
3단계 고급 기능 테스트: WebSocket Provider 성능 및 안정성 테스트 - 최종
"""
import asyncio
import time
from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.upbit_websocket_provider import UpbitWebSocketProvider
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.models.requests import CandleDataRequest
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.models.symbols import TradingSymbol
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.models.timeframes import Timeframe


async def main():
    """3단계: WebSocket Provider 고급 성능 테스트"""
    logger = create_component_logger("WebSocketFinalTest")

    print("🧪 3단계: WebSocket Provider 고급 성능 테스트")
    print("=" * 60)

    provider = UpbitWebSocketProvider()

    try:
        # 테스트 1: 다중 심볼 성능 테스트
        print("1️⃣ 다중 심볼 성능 테스트")
        symbols = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']

        total_success = 0
        total_requests = len(symbols)
        response_times = []

        for symbol_str in symbols:
            print(f"   🚀 {symbol_str} 테스트 중...")
            try:
                symbol = TradingSymbol.from_upbit_symbol(symbol_str)
                request = CandleDataRequest(
                    symbol=symbol,
                    timeframe=Timeframe.MINUTE_1,
                    count=1
                )

                start_time = time.time()
                result = await provider.get_candle_data(request)
                elapsed = (time.time() - start_time) * 1000

                if result and result.data:
                    candle = result.data[0]
                    total_success += 1
                    response_times.append(elapsed)
                    print(f"   ✅ {symbol_str}: 종가 {candle.close_price:>12,.0f} ({elapsed:>6.1f}ms)")
                else:
                    print(f"   ❌ {symbol_str}: 데이터 없음")

            except Exception as e:
                print(f"   ❌ {symbol_str}: 오류 - {e}")

        print(f"\n📊 다중 심볼 결과: {total_success}/{total_requests} 성공")
        if response_times:
            print(f"   평균 응답시간: {sum(response_times)/len(response_times):.1f}ms")

        # 테스트 2: 연속 요청 안정성 테스트
        print("\n2️⃣ 연속 요청 안정성 테스트 (5회)")

        symbol = TradingSymbol.from_upbit_symbol('KRW-BTC')
        consecutive_success = 0
        consecutive_times = []

        for i in range(5):
            try:
                request = CandleDataRequest(
                    symbol=symbol,
                    timeframe=Timeframe.MINUTE_1,
                    count=1
                )

                start_time = time.time()
                result = await provider.get_candle_data(request)
                elapsed = (time.time() - start_time) * 1000

                if result and result.data:
                    candle = result.data[0]
                    consecutive_success += 1
                    consecutive_times.append(elapsed)
                    print(f"   요청 {i + 1}: 종가 {candle.close_price:>12,.0f} ({elapsed:>6.1f}ms)")
                else:
                    print(f"   요청 {i + 1}: 데이터 없음")

                # 0.2초 간격
                await asyncio.sleep(0.2)

            except Exception as e:
                print(f"   요청 {i + 1}: 오류 - {e}")

        print(f"\n📈 연속 요청 결과: {consecutive_success}/5 성공")
        if consecutive_times:
            print(f"   평균 응답시간: {sum(consecutive_times)/len(consecutive_times):.1f}ms")
            print(f"   최고 응답시간: {max(consecutive_times):.1f}ms")
            print(f"   최저 응답시간: {min(consecutive_times):.1f}ms")

        # 테스트 3: 타임프레임 호환성 테스트
        print("\n3️⃣ 타임프레임 호환성 테스트")
        timeframes = [
            (Timeframe.MINUTE_1, '1m'),
            (Timeframe.MINUTE_5, '5m'),
            (Timeframe.MINUTE_15, '15m')
        ]
        symbol = TradingSymbol.from_upbit_symbol('KRW-BTC')

        tf_success = 0
        tf_total = len(timeframes)

        for timeframe, tf_name in timeframes:
            try:
                request = CandleDataRequest(
                    symbol=symbol,
                    timeframe=timeframe,
                    count=1
                )

                start_time = time.time()
                result = await provider.get_candle_data(request)
                elapsed = (time.time() - start_time) * 1000

                if result and result.data:
                    candle = result.data[0]
                    tf_success += 1
                    print(f"   ✅ {tf_name:>3}: 종가 {candle.close_price:>12,.0f} ({elapsed:>6.1f}ms)")
                else:
                    print(f"   ❌ {tf_name:>3}: 데이터 없음")

            except Exception as e:
                print(f"   ❌ {tf_name:>3}: 오류 - {e}")

        print(f"\n🎯 타임프레임 결과: {tf_success}/{tf_total} 성공")

        # 최종 성과 평가
        overall_success = total_success + consecutive_success + tf_success
        overall_total = total_requests + 5 + tf_total
        success_rate = (overall_success / overall_total) * 100

        print(f"\n🏆 최종 성과:")
        print(f"   전체 성공률: {success_rate:.1f}% ({overall_success}/{overall_total})")

        if success_rate >= 90:
            print("   ✅ 우수: WebSocket Provider 고급 기능 완벽 작동!")
        elif success_rate >= 75:
            print("   ⚠️ 양호: 일부 개선 여지가 있음")
        else:
            print("   ❌ 부족: 추가 최적화 필요")

        # 성능 벤치마크
        all_times = response_times + consecutive_times
        if all_times:
            print(f"\n⚡ 성능 벤치마크:")
            print(f"   전체 평균: {sum(all_times)/len(all_times):.1f}ms")
            print(f"   최고 성능: {min(all_times):.1f}ms")
            print(f"   최저 성능: {max(all_times):.1f}ms")

            if sum(all_times)/len(all_times) < 300:
                print("   🚀 성능: 우수 (300ms 미만)")
            elif sum(all_times)/len(all_times) < 500:
                print("   ⚡ 성능: 양호 (500ms 미만)")
            else:
                print("   🐌 성능: 개선 필요 (500ms 이상)")

    except Exception as e:
        logger.error(f"❌ 테스트 오류: {e}")
        raise
    finally:
        # 리소스 정리
        print("\n🧹 리소스 정리 중...")
        if hasattr(provider, 'disconnect'):
            await provider.disconnect()
        print("✅ 모든 리소스 정리 완료")

    print("\n" + "=" * 60)
    print("🎉 3단계 고급 기능 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(main())
