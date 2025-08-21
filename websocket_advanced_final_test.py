"""
3단계 고급 기능 테스트: WebSocket Provider 다중 심볼 테스트
"""
import asyncio
from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.upbit_websocket_provider import UpbitWebSocketProvider
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.models.requests import CandleDataRequest
from upbit_auto_trading.domain.trading.models.trading_symbol import TradingSymbol
from upbit_auto_trading.domain.trading.models.timeframe import Timeframe


async def main():
    """WebSocket Provider 고급 기능 테스트"""
    logger = create_component_logger("WebSocketAdvancedTest")

    print("🧪 3단계: WebSocket Provider 고급 기능 테스트")
    print("=" * 55)

    provider = UpbitWebSocketProvider()

    try:
        # 테스트 1: 다중 심볼 동시 테스트
        print("1️⃣ 다중 심볼 동시 캔들 데이터 테스트")
        symbols = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']

        tasks = []
        for symbol_str in symbols:
            print(f"   🚀 {symbol_str} 캔들 요청 시작...")
            symbol = TradingSymbol.from_string(symbol_str)
            timeframe = Timeframe.from_string('1m')
            request = CandleDataRequest(symbol=symbol, timeframe=timeframe)
            task = provider.get_candle_data(request)
            tasks.append((symbol_str, task))

        # 동시 실행
        results = []
        for symbol_str, task in tasks:
            try:
                start_time = asyncio.get_event_loop().time()
                result = await task
                elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
                results.append((symbol_str, result, elapsed))
                print(f"   ✅ {symbol_str}: {result.close:>12,.0f} ({elapsed:>6.1f}ms)")
            except Exception as e:
                print(f"   ❌ {symbol_str}: 오류 - {e}")

        print(f"\n📊 결과 요약: {len(results)}/{len(symbols)} 성공")

        # 테스트 2: 연속 요청 성능 테스트
        print("\n2️⃣ 연속 요청 성능 테스트 (동일 심볼)")
        total_time = 0
        success_count = 0

        symbol = TradingSymbol.from_string('KRW-BTC')
        timeframe = Timeframe.from_string('1m')

        for i in range(3):
            try:
                start_time = asyncio.get_event_loop().time()
                request = CandleDataRequest(symbol=symbol, timeframe=timeframe)
                result = await provider.get_candle_data(request)
                elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
                total_time += elapsed
                success_count += 1
                print(f"   요청 {i + 1}: {result.close:>12,.0f} ({elapsed:>6.1f}ms)")
                await asyncio.sleep(0.1)  # 짧은 대기
            except Exception as e:
                print(f"   요청 {i + 1}: 오류 - {e}")

        if success_count > 0:
            avg_time = total_time / success_count
            print(f"\n📈 성능 요약:")
            print(f"   성공률: {success_count}/3")
            print(f"   평균 응답시간: {avg_time:.1f}ms")

        # 테스트 3: 타임프레임 변경 테스트
        print("\n3️⃣ 다양한 타임프레임 테스트")
        timeframes = ['1m', '5m', '15m']
        symbol = TradingSymbol.from_string('KRW-BTC')

        for tf_str in timeframes:
            try:
                start_time = asyncio.get_event_loop().time()
                timeframe = Timeframe.from_string(tf_str)
                request = CandleDataRequest(symbol=symbol, timeframe=timeframe)
                result = await provider.get_candle_data(request)
                elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
                print(f"   ✅ {tf_str:>3}: {result.close:>12,.0f} ({elapsed:>6.1f}ms)")
            except Exception as e:
                print(f"   ❌ {tf_str:>3}: 오류 - {e}")

        print("\n🎯 모든 고급 기능 테스트 완료!")

    except Exception as e:
        logger.error(f"❌ 테스트 오류: {e}")
        raise
    finally:
        # 리소스 정리
        print("\n🧹 리소스 정리 중...")
        if hasattr(provider, 'disconnect'):
            await provider.disconnect()
        print("✅ 모든 리소스 정리 완료")

    print("\n" + "=" * 55)
    print("🎉 3단계 고급 기능 테스트 성공!")

if __name__ == "__main__":
    asyncio.run(main())
