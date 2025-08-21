"""
🎯 Smart Router 핵심 사용법 - 질문 답변

사용자 질문에 대한 완전한 답변:
1. 호가는 어떻게 요청하나요?
2. 차트를 그릴때 최신 캔들을 요청하면서 2000개 그래프는 어떻게 그려야 하나요?
3. KRW 티커에 여러값들을 동시에 불러오려면 어떻게 하나요?
4. 이 모든게 동시에 이루어지면 어떻게 사용해야 하나요?
"""

import asyncio
from typing import List, Dict, Any

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.simple_smart_router import (
    SimpleSmartRouter
)
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.upbit_data_provider import (
    UpbitDataProvider
)

logger = create_component_logger("SmartRouterAnswers")


class SmartRouterAnswers:
    """사용자 질문에 대한 완전한 답변"""

    def __init__(self):
        self.router = SimpleSmartRouter()
        self.data_provider = UpbitDataProvider()

    async def start(self):
        """시스템 시작"""
        await self.router.start()
        await self.data_provider.start()

    async def stop(self):
        """시스템 정지"""
        await self.router.stop()
        await self.data_provider.stop()

    # ====================================================================
    # 답변 1: 호가는 어떻게 요청하나요?
    # ====================================================================

    async def answer_1_orderbook_request(self):
        """답변 1: 호가 요청 방법"""
        print("\n" + "="*50)
        print("🔸 답변 1: 호가는 어떻게 요청하나요?")
        print("="*50)

        # 방법 1: 단일 심볼 호가 조회
        print("\n📋 방법 1: 단일 심볼 호가 조회")
        print("```python")
        print("# UpbitDataProvider 사용 (추천)")
        print("provider = UpbitDataProvider()")
        print("await provider.start()")
        print("result = await provider.get_orderbook_data(['KRW-BTC'])")
        print("orderbook = result['data']['KRW-BTC']")
        print("```")

        try:
            # 실제 실행
            result = await self.data_provider.get_orderbook_data(['KRW-BTC'])
            if result.get('success') and 'KRW-BTC' in result.get('data', {}):
                orderbook = result['data']['KRW-BTC']
                if 'orderbook_units' in orderbook:
                    best_ask = orderbook['orderbook_units'][0]
                    print(f"✅ 실행 결과: BTC 매도호가 ₩{best_ask.get('ask_price', 0):,}")
                else:
                    print("⚠️ 호가 구조가 예상과 다름")
            else:
                print("⚠️ 호가 조회 실패")
        except Exception as e:
            print(f"❌ 호가 조회 오류: {e}")

        # 방법 2: 다중 심볼 호가 조회
        print("\n📋 방법 2: 다중 심볼 호가 조회")
        print("```python")
        print("symbols = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']")
        print("result = await provider.get_orderbook_data(symbols)")
        print("for symbol, orderbook in result['data'].items():")
        print("    print(f'{symbol} 호가: {len(orderbook[\"orderbook_units\"])}단계')")
        print("```")

    # ====================================================================
    # 답변 2: 차트를 그릴때 최신 캔들 요청하면서 2000개 그래프
    # ====================================================================

    async def answer_2_large_chart_data(self):
        """답변 2: 대용량 차트 데이터 (2000개) 요청 방법"""
        print("\n" + "="*50)
        print("🔸 답변 2: 차트용 2000개 캔들 데이터는 어떻게?")
        print("="*50)

        print("\n📋 방법: 배치 처리로 대용량 데이터 수집")
        print("```python")
        print("async def get_chart_data_2000(symbol, interval='5m'):")
        print("    all_candles = []")
        print("    batch_size = 200  # 업비트 API 제한")
        print("    total_batches = 2000 // batch_size  # 10배치")
        print("    ")
        print("    for batch in range(total_batches):")
        print("        candles = await router.get_candles(symbol, interval, batch_size)")
        print("        all_candles.extend(candles)")
        print("        await asyncio.sleep(0.1)  # Rate limit 준수")
        print("    ")
        print("    return all_candles")
        print("```")

        # 실제 실행 (500개로 테스트)
        print("\n⚡ 실제 실행 (500개 테스트):")
        try:
            test_candles = await self.get_large_candles("KRW-BTC", "5m", 500)
            print(f"✅ 테스트 결과: {len(test_candles)}개 캔들 수집 성공")

            if test_candles:
                latest = test_candles[0]
                print(f"📈 최신 캔들: ₩{latest.get('trade_price', 0):,}")
        except Exception as e:
            print(f"❌ 차트 데이터 오류: {e}")

    async def get_large_candles(self, symbol: str, interval: str, count: int) -> List[Dict[str, Any]]:
        """대용량 캔들 데이터 수집"""
        all_candles = []
        batch_size = 200

        for batch_num in range((count + batch_size - 1) // batch_size):
            remaining = count - len(all_candles)
            current_batch = min(batch_size, remaining)

            candles = await self.router.get_candles(symbol, interval, current_batch)
            if candles:
                all_candles.extend(candles)
            else:
                break

            await asyncio.sleep(0.1)

        return all_candles

    # ====================================================================
    # 답변 3: KRW 티커에 여러값들을 동시에 불러오기
    # ====================================================================

    async def answer_3_multiple_krw_tickers(self):
        """답변 3: KRW 티커 다중 심볼 동시 조회"""
        print("\n" + "="*50)
        print("🔸 답변 3: KRW 티커 여러값들을 동시에 불러오기")
        print("="*50)

        print("\n📋 방법: 병렬 비동기 처리")
        print("```python")
        print("# KRW 마켓 주요 심볼들")
        print("krw_symbols = [")
        print("    'KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-ADA',")
        print("    'KRW-DOT', 'KRW-SOL', 'KRW-AVAX', 'KRW-MATIC'")
        print("]")
        print("")
        print("# 병렬 비동기 처리")
        print("tasks = [router.get_ticker(symbol) for symbol in krw_symbols]")
        print("results = await asyncio.gather(*tasks)")
        print("")
        print("# 결과 정리")
        print("tickers = {}")
        print("for symbol, data in zip(krw_symbols, results):")
        print("    if data:")
        print("        tickers[symbol] = data")
        print("```")

        # 실제 실행
        print("\n⚡ 실제 실행:")
        try:
            krw_symbols = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", "KRW-DOT"]

            start_time = asyncio.get_event_loop().time()

            # 병렬 처리
            tasks = [self.router.get_ticker(symbol) for symbol in krw_symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            elapsed = asyncio.get_event_loop().time() - start_time

            # 결과 정리
            success_count = 0
            for symbol, result in zip(krw_symbols, results):
                if not isinstance(result, Exception) and result:
                    success_count += 1
                    price = result.get('trade_price', 0)
                    change = result.get('signed_change_rate', 0)
                    print(f"💰 {symbol}: ₩{price:,} ({change:+.2%})")

            print(f"✅ 병렬 조회 완료: {success_count}/{len(krw_symbols)} 성공, {elapsed:.2f}초")

        except Exception as e:
            print(f"❌ 다중 티커 오류: {e}")

    # ====================================================================
    # 답변 4: 모든게 동시에 이루어지면 어떻게 사용?
    # ====================================================================

    async def answer_4_integrated_usage(self):
        """답변 4: 모든 기능 동시 사용법"""
        print("\n" + "="*50)
        print("🔸 답변 4: 모든게 동시에 이루어지면 어떻게 사용?")
        print("="*50)

        print("\n📋 해답: 통합 트레이딩 시스템 구축")
        print("```python")
        print("async def integrated_trading_system():")
        print("    # 1단계: 병렬로 모든 데이터 수집")
        print("    tasks = {")
        print("        'tickers': get_multiple_tickers(krw_symbols),")
        print("        'orderbooks': get_multiple_orderbooks(symbols[:5]),")
        print("        'charts': get_chart_data_2000('KRW-BTC', '5m')")
        print("    }")
        print("    ")
        print("    results = await asyncio.gather(*tasks.values())")
        print("    ")
        print("    # 2단계: 실시간 모니터링 루프")
        print("    while True:")
        print("        # 빠른 업데이트 (티커)")
        print("        quick_update = await get_multiple_tickers(core_symbols)")
        print("        # 분석 및 표시")
        print("        analyze_and_display(quick_update)")
        print("        await asyncio.sleep(1.0)")
        print("```")

        # 실제 통합 실행
        print("\n⚡ 실제 통합 실행:")
        try:
            symbols = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]

            # 1단계: 초기 데이터 수집
            print("📊 1단계: 초기 데이터 수집...")
            initial_data = await self.collect_initial_data(symbols)

            print(f"  ✅ 티커: {initial_data.get('ticker_count', 0)}개")
            print(f"  ✅ 호가: {initial_data.get('orderbook_count', 0)}개")
            print(f"  ✅ 차트: {initial_data.get('chart_count', 0)}개 캔들")

            # 2단계: 실시간 모니터링 (5초간)
            print("\n📡 2단계: 실시간 모니터링 (5초간)...")
            await self.realtime_monitoring_demo(symbols, 5)

        except Exception as e:
            print(f"❌ 통합 실행 오류: {e}")

    async def collect_initial_data(self, symbols: List[str]) -> Dict[str, Any]:
        """초기 데이터 수집"""
        try:
            # 병렬 데이터 수집
            tasks = [
                self.get_multiple_tickers_parallel(symbols),
                self.get_multiple_orderbooks_safe(symbols[:3]),
                self.get_large_candles("KRW-BTC", "5m", 100)  # 100개만 테스트
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            return {
                'ticker_count': len(results[0]) if not isinstance(results[0], Exception) else 0,
                'orderbook_count': len(results[1]) if not isinstance(results[1], Exception) else 0,
                'chart_count': len(results[2]) if not isinstance(results[2], Exception) else 0
            }

        except Exception as e:
            logger.error(f"초기 데이터 수집 오류: {e}")
            return {}

    async def get_multiple_tickers_parallel(self, symbols: List[str]) -> Dict[str, Any]:
        """병렬 티커 조회"""
        tasks = [self.router.get_ticker(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        tickers = {}
        for symbol, result in zip(symbols, results):
            if not isinstance(result, Exception) and result:
                tickers[symbol] = result

        return tickers

    async def get_multiple_orderbooks_safe(self, symbols: List[str]) -> Dict[str, Any]:
        """안전한 다중 호가 조회"""
        try:
            result = await self.data_provider.get_orderbook_data(symbols)
            return result.get('data', {}) if result.get('success') else {}
        except Exception as e:
            logger.warning(f"호가 조회 실패: {e}")
            return {}

    async def realtime_monitoring_demo(self, symbols: List[str], duration: int):
        """실시간 모니터링 데모"""
        start_time = asyncio.get_event_loop().time()
        cycle = 0

        while asyncio.get_event_loop().time() - start_time < duration:
            cycle += 1

            # 빠른 티커 업데이트
            tickers = await self.get_multiple_tickers_parallel(symbols)

            # 간단한 분석 표시
            if tickers:
                print(f"  🔄 사이클 {cycle}: {len(tickers)}개 심볼 업데이트")
                for symbol, data in list(tickers.items())[:2]:  # 상위 2개만
                    price = data.get('trade_price', 0)
                    change = data.get('signed_change_rate', 0)
                    print(f"    💰 {symbol}: ₩{price:,} ({change:+.2%})")

            await asyncio.sleep(1.0)


async def main():
    """메인 실행 함수"""
    print("🚀 Smart Router 질문 답변을 시작합니다...")

    answers = SmartRouterAnswers()

    try:
        await answers.start()

        # 모든 질문에 대한 답변 실행
        await answers.answer_1_orderbook_request()
        await answers.answer_2_large_chart_data()
        await answers.answer_3_multiple_krw_tickers()
        await answers.answer_4_integrated_usage()

        print("\n" + "="*50)
        print("✅ 모든 질문 답변 완료!")
        print("="*50)
        print("\n📋 요약:")
        print("1. 호가: UpbitDataProvider.get_orderbook_data() 사용")
        print("2. 2000개 차트: 배치 처리로 200개씩 수집")
        print("3. 다중 KRW 티커: asyncio.gather()로 병렬 처리")
        print("4. 통합 사용: 초기 수집 + 실시간 모니터링 구조")

    except Exception as e:
        print(f"❌ 실행 오류: {e}")

    finally:
        await answers.stop()


if __name__ == "__main__":
    asyncio.run(main())
