"""
📋 Smart Router 고급 사용법 가이드

질문하신 모든 기능에 대한 완전한 사용법입니다:
1. 호가 데이터 요청
2. 대용량 캔들 차트 (2000개)
3. KRW 티커 다중 심볼 동시 조회
4. 모든 기능 통합 사용법
"""

import asyncio
from typing import List, Dict, Any

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.simple_smart_router import SimpleSmartRouter

logger = create_component_logger("SmartRouterGuide")


class SmartRouterUsageGuide:
    """Smart Router 완전 사용법 가이드"""

    def __init__(self):
        self.router = SimpleSmartRouter()

    async def start(self):
        """시스템 시작"""
        await self.router.start()

    async def stop(self):
        """시스템 정지"""
        await self.router.stop()

    # ====================================================================
    # 1. 호가 데이터 요청 방법
    # ====================================================================

    async def get_orderbook_simple(self, symbol: str) -> Dict[str, Any]:
        """간단한 호가 조회"""
        # SimpleSmartRouter는 기본적으로 티커/캔들만 지원
        # 호가는 UpbitDataProvider 직접 사용이 필요

        from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.upbit_data_provider import UpbitDataProvider

        provider = UpbitDataProvider()
        await provider.start()

        try:
            # 호가 데이터 조회
            result = await provider.get_orderbook_data([symbol])

            if result.get('success'):
                return result['data'].get(symbol, {})
            else:
                return {}

        finally:
            await provider.stop()

    async def get_multiple_orderbooks(self, symbols: List[str]) -> Dict[str, Any]:
        """다중 심볼 호가 조회"""
        from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.upbit_data_provider import UpbitDataProvider

        provider = UpbitDataProvider()
        await provider.start()

        try:
            # 배치로 호가 조회 (업비트는 최대 10개까지)
            batch_size = 10
            all_orderbooks = {}

            for i in range(0, len(symbols), batch_size):
                batch = symbols[i:i + batch_size]
                result = await provider.get_orderbook_data(batch)

                if result.get('success'):
                    all_orderbooks.update(result['data'])

                # API 제한 고려
                if i + batch_size < len(symbols):
                    await asyncio.sleep(0.1)

            return all_orderbooks

        finally:
            await provider.stop()

    # ====================================================================
    # 2. 대용량 캔들 차트 데이터 (2000개)
    # ====================================================================

    async def get_large_chart_data(self, symbol: str, interval: str = "5m",
                                   total_count: int = 2000) -> List[Dict[str, Any]]:
        """대용량 캔들 데이터 조회 (차트용)"""
        logger.info(f"📊 대용량 차트 데이터: {symbol} {interval} {total_count}개")

        all_candles = []
        batch_size = 200  # 업비트 API 제한

        try:
            for batch_num in range((total_count + batch_size - 1) // batch_size):
                remaining = total_count - len(all_candles)
                current_batch = min(batch_size, remaining)

                logger.info(f"📦 배치 {batch_num + 1}: {current_batch}개 조회")

                # Smart Router로 최적화된 조회
                batch_candles = await self.router.get_candles(
                    symbol=symbol,
                    interval=interval,
                    count=current_batch
                )

                if batch_candles:
                    all_candles.extend(batch_candles)
                    logger.debug(f"✅ 누적: {len(all_candles)}개")
                else:
                    logger.warning(f"⚠️ 배치 {batch_num + 1} 실패")
                    break

                # Rate limit 준수
                await asyncio.sleep(0.1)

            logger.info(f"✅ 차트 데이터 완료: {len(all_candles)}개")
            return all_candles

        except Exception as e:
            logger.error(f"❌ 차트 데이터 오류: {e}")
            return all_candles

    # ====================================================================
    # 3. KRW 티커 다중 심볼 동시 조회
    # ====================================================================

    async def get_all_krw_tickers(self) -> Dict[str, Any]:
        """KRW 마켓 전체 티커 조회"""
        # KRW 마켓 주요 심볼들
        krw_symbols = [
            "KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", "KRW-DOT",
            "KRW-LINK", "KRW-SOL", "KRW-AVAX", "KRW-MATIC", "KRW-ATOM",
            "KRW-NEAR", "KRW-ALGO", "KRW-HBAR", "KRW-ICP", "KRW-SAND"
        ]

        return await self.get_multiple_tickers_optimized(krw_symbols)

    async def get_multiple_tickers_optimized(self, symbols: List[str]) -> Dict[str, Any]:
        """최적화된 다중 티커 조회"""
        logger.info(f"🔄 다중 티커 조회: {len(symbols)}개")

        # 병렬 비동기 처리로 성능 최적화
        start_time = asyncio.get_event_loop().time()

        try:
            # 병렬 태스크 생성
            tasks = [
                self.router.get_ticker(symbol)
                for symbol in symbols
            ]

            # 동시 실행
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 결과 정리
            ticker_data = {}
            success_count = 0

            for symbol, result in zip(symbols, results):
                if isinstance(result, Exception):
                    logger.warning(f"⚠️ {symbol} 실패: {result}")
                    ticker_data[symbol] = None
                elif result:
                    ticker_data[symbol] = result
                    success_count += 1
                else:
                    ticker_data[symbol] = None

            elapsed = asyncio.get_event_loop().time() - start_time
            logger.info(f"✅ 다중 조회 완료: {success_count}/{len(symbols)} ({elapsed:.2f}초)")

            return {
                'success_count': success_count,
                'total_count': len(symbols),
                'elapsed_time': elapsed,
                'data': ticker_data
            }

        except Exception as e:
            logger.error(f"❌ 다중 조회 오류: {e}")
            return {'error': str(e)}

    # ====================================================================
    # 4. 모든 기능 통합 사용 - 실시간 트레이딩 대시보드
    # ====================================================================

    async def create_trading_dashboard(self, symbols: List[str]) -> Dict[str, Any]:
        """실시간 트레이딩 대시보드 (모든 데이터 통합)"""
        logger.info(f"📊 트레이딩 대시보드 생성: {len(symbols)}개 심볼")

        dashboard_data = {
            'timestamp': asyncio.get_event_loop().time(),
            'symbols': symbols,
            'data': {}
        }

        try:
            # 병렬로 모든 데이터 수집
            tasks = {
                'tickers': self.get_multiple_tickers_optimized(symbols),
                'orderbooks': self.get_multiple_orderbooks(symbols[:5]),  # 호가는 5개만
                'charts': asyncio.gather(*[
                    self.router.get_candles(symbol, "1m", 100)  # 최근 100개 캔들
                    for symbol in symbols[:3]  # 차트는 주요 3개만
                ])
            }

            # 동시 실행
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)

            # 티커 데이터
            if not isinstance(results[0], Exception):
                dashboard_data['tickers'] = results[0]

            # 호가 데이터
            if not isinstance(results[1], Exception):
                dashboard_data['orderbooks'] = results[1]

            # 차트 데이터
            if not isinstance(results[2], Exception):
                chart_data = {}
                for i, candles in enumerate(results[2]):
                    if i < len(symbols[:3]) and candles:
                        chart_data[symbols[i]] = candles
                dashboard_data['charts'] = chart_data

            logger.info("✅ 대시보드 생성 완료")
            return dashboard_data

        except Exception as e:
            logger.error(f"❌ 대시보드 생성 오류: {e}")
            return {'error': str(e)}

    # ====================================================================
    # 5. 고성능 실시간 모니터링
    # ====================================================================

    async def start_realtime_monitoring(self, symbols: List[str],
                                        update_interval: float = 1.0,
                                        duration: int = 60):
        """고성능 실시간 모니터링"""
        logger.info(f"🔴 실시간 모니터링 시작: {len(symbols)}개, {duration}초간")

        start_time = asyncio.get_event_loop().time()
        cycle = 0

        try:
            while asyncio.get_event_loop().time() - start_time < duration:
                cycle += 1
                cycle_start = asyncio.get_event_loop().time()

                logger.info(f"🔄 사이클 #{cycle}")

                # 핵심 데이터만 빠르게 조회
                core_symbols = symbols[:5]
                ticker_result = await self.get_multiple_tickers_optimized(core_symbols)

                # 실시간 분석
                if 'data' in ticker_result:
                    analysis = self.analyze_market_data(ticker_result['data'])
                    self.display_realtime_analysis(analysis, cycle)

                # 다음 사이클까지 대기
                cycle_time = asyncio.get_event_loop().time() - cycle_start
                wait_time = max(update_interval - cycle_time, 0.1)
                await asyncio.sleep(wait_time)

            logger.info(f"✅ 실시간 모니터링 완료: {cycle}사이클")

        except Exception as e:
            logger.error(f"❌ 실시간 모니터링 오류: {e}")

    def analyze_market_data(self, ticker_data: Dict[str, Any]) -> Dict[str, Any]:
        """마켓 데이터 분석"""
        analysis = {
            'top_gainers': [],
            'top_losers': [],
            'high_volume': [],
            'summary': {}
        }

        try:
            valid_data = []
            for symbol, data in ticker_data.items():
                if data and isinstance(data, dict):
                    change_rate = data.get('signed_change_rate', 0)
                    volume = data.get('acc_trade_volume_24h', 0)
                    price = data.get('trade_price', 0)

                    valid_data.append({
                        'symbol': symbol,
                        'price': price,
                        'change_rate': change_rate,
                        'volume': volume
                    })

            if valid_data:
                # 상승률 Top 3
                analysis['top_gainers'] = sorted(
                    valid_data, key=lambda x: x['change_rate'], reverse=True
                )[:3]

                # 하락률 Top 3
                analysis['top_losers'] = sorted(
                    valid_data, key=lambda x: x['change_rate']
                )[:3]

                # 거래량 Top 3
                analysis['high_volume'] = sorted(
                    valid_data, key=lambda x: x['volume'], reverse=True
                )[:3]

                # 요약 통계
                total_symbols = len(valid_data)
                rising = len([d for d in valid_data if d['change_rate'] > 0])
                falling = len([d for d in valid_data if d['change_rate'] < 0])

                analysis['summary'] = {
                    'total': total_symbols,
                    'rising': rising,
                    'falling': falling,
                    'neutral': total_symbols - rising - falling
                }

        except Exception as e:
            logger.error(f"분석 오류: {e}")

        return analysis

    def display_realtime_analysis(self, analysis: Dict[str, Any], cycle: int):
        """실시간 분석 결과 표시"""
        print(f"\n🔍 사이클 #{cycle} 분석 결과:")

        if 'summary' in analysis and analysis['summary']:
            s = analysis['summary']
            print(f"📊 마켓 현황: 상승 {s['rising']}, 하락 {s['falling']}, 보합 {s['neutral']}")

        if analysis['top_gainers']:
            print("📈 상승률 TOP:")
            for i, item in enumerate(analysis['top_gainers'], 1):
                print(f"  {i}. {item['symbol']}: {item['change_rate']:+.2%}")

        if analysis['high_volume']:
            print("📊 거래량 TOP:")
            for i, item in enumerate(analysis['high_volume'], 1):
                volume_text = f"{item['volume']:.0f}" if item['volume'] < 1000 else f"{item['volume']/1000:.1f}K"
                print(f"  {i}. {item['symbol']}: {volume_text}")


# ====================================================================
# 📋 사용법 예제들
# ====================================================================

async def example_1_orderbook():
    """예제 1: 호가 데이터 조회"""
    print("\n🔸 예제 1: 호가 데이터 조회")

    guide = SmartRouterUsageGuide()
    await guide.start()

    try:
        # 단일 호가 조회
        orderbook = await guide.get_orderbook_simple("KRW-BTC")
        if orderbook:
            print(f"📈 BTC 호가: {len(orderbook.get('orderbook_units', []))}단계")

        # 다중 호가 조회
        symbols = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
        orderbooks = await guide.get_multiple_orderbooks(symbols)
        print(f"📊 다중 호가: {len(orderbooks)}개 심볼")

    finally:
        await guide.stop()


async def example_2_large_chart():
    """예제 2: 대용량 차트 데이터"""
    print("\n🔸 예제 2: 대용량 차트 데이터 (2000개)")

    guide = SmartRouterUsageGuide()
    await guide.start()

    try:
        # 2000개 캔들 조회
        candles = await guide.get_large_chart_data("KRW-BTC", "5m", 2000)
        print(f"📊 BTC 5분봉: {len(candles)}개 캔들")

        if candles:
            latest = candles[0]
            print(f"📈 최신 캔들: ₩{latest.get('trade_price', 0):,}")

    finally:
        await guide.stop()


async def example_3_multiple_tickers():
    """예제 3: KRW 다중 티커 조회"""
    print("\n🔸 예제 3: KRW 다중 티커 동시 조회")

    guide = SmartRouterUsageGuide()
    await guide.start()

    try:
        # 전체 KRW 티커 조회
        result = await guide.get_all_krw_tickers()

        print(f"🔄 조회 결과: {result.get('success_count', 0)}/{result.get('total_count', 0)}")
        print(f"⏱️ 소요 시간: {result.get('elapsed_time', 0):.2f}초")

        # 상위 3개 출력
        if 'data' in result:
            count = 0
            for symbol, data in result['data'].items():
                if data and count < 3:
                    price = data.get('trade_price', 0)
                    change = data.get('signed_change_rate', 0)
                    print(f"💰 {symbol}: ₩{price:,} ({change:+.2%})")
                    count += 1

    finally:
        await guide.stop()


async def example_4_integrated_dashboard():
    """예제 4: 통합 대시보드"""
    print("\n🔸 예제 4: 모든 기능 통합 대시보드")

    guide = SmartRouterUsageGuide()
    await guide.start()

    try:
        symbols = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", "KRW-DOT"]
        dashboard = await guide.create_trading_dashboard(symbols)

        print(f"📊 대시보드 생성 완료:")

        if 'tickers' in dashboard:
            ticker_count = dashboard['tickers'].get('success_count', 0)
            print(f"  📈 티커: {ticker_count}개")

        if 'orderbooks' in dashboard:
            print(f"  📊 호가: {len(dashboard['orderbooks'])}개")

        if 'charts' in dashboard:
            print(f"  📈 차트: {len(dashboard['charts'])}개")

    finally:
        await guide.stop()


async def example_5_realtime_monitoring():
    """예제 5: 실시간 모니터링"""
    print("\n🔸 예제 5: 실시간 모니터링 (10초간)")

    guide = SmartRouterUsageGuide()
    await guide.start()

    try:
        symbols = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
        await guide.start_realtime_monitoring(symbols, 2.0, 10)  # 2초 간격, 10초간

    finally:
        await guide.stop()


async def run_all_examples():
    """모든 예제 실행"""
    print("=" * 60)
    print("🚀 Smart Router 고급 사용법 완전 가이드")
    print("=" * 60)

    try:
        await example_1_orderbook()
        await example_2_large_chart()
        await example_3_multiple_tickers()
        await example_4_integrated_dashboard()
        await example_5_realtime_monitoring()

        print("\n✅ 모든 예제 완료!")

    except Exception as e:
        print(f"❌ 예제 실행 오류: {e}")


if __name__ == "__main__":
    print("🚀 Smart Router 고급 사용법 가이드를 시작합니다...")
    asyncio.run(run_all_examples())
