"""
고급 Smart Router 사용법 데모

이 예제는 다음을 다룹니다:
1. 호가 데이터 요청
2. 대용량 캔    async def get_large_candle_dataset(self, symbol: str, interval: str = "5m",
                                       total_count: int = 2000) -> List[Dict[str, Any]]:차트 데이터 (2000개)
3. KRW 티커 다중 심볼 동시 조회
4. 실시간 통합 모니터링 시스템
"""

import asyncio
import time
from typing import List, Dict, Any
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.simple_smart_router import SimpleSmartRouter
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.upbit_data_provider import (
    UpbitDataProvider
)

logger = create_component_logger("AdvancedRouterDemo")


class AdvancedTradingSystem:
    """고급 트레이딩 시스템 데모"""

    def __init__(self):
        self.router = SimpleSmartRouter()
        self.data_provider = UpbitDataProvider()

        # KRW 마켓 주요 심볼들
        self.krw_symbols = [
            "KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", "KRW-DOT",
            "KRW-MATIC", "KRW-SOL", "KRW-AVAX", "KRW-LINK", "KRW-ATOM"
        ]

    async def start(self):
        """시스템 시작"""
        logger.info("🚀 고급 트레이딩 시스템 시작")
        await self.router.start()
        await self.data_provider.start()
        logger.info("✅ 시스템 초기화 완료")

    async def stop(self):
        """시스템 정지"""
        logger.info("⏹️ 시스템 정지 중...")
        await self.router.stop()
        await self.data_provider.stop()
        logger.info("✅ 시스템 정지 완료")

    async def get_orderbook_data(self, symbols: List[str]) -> Dict[str, Any]:
        """호가 데이터 조회 (Smart Router 통합)"""
        logger.info(f"📈 호가 데이터 조회: {len(symbols)}개 심볼")

        try:
            # UpbitDataProvider를 통한 호가 데이터 조회
            result = await self.data_provider.get_orderbook_data(symbols)

            if result.get('success'):
                logger.info(f"✅ 호가 조회 성공: {len(result['data'])}개 심볼")
                return result['data']
            else:
                logger.warning(f"⚠️ 호가 조회 실패: {result.get('error', '알 수 없는 오류')}")
                return {}

        except Exception as e:
            logger.error(f"❌ 호가 조회 예외: {e}")
            return {}

    async def get_large_candle_dataset(self, symbol: str, interval: str = "5m",
                                     total_count: int = 2000) -> List[Dict[str, Any]]:
        """대용량 캔들 데이터 조회 (차트용 2000개)"""
        logger.info(f"📊 대용량 캔들 데이터 조회: {symbol} {interval} {total_count}개")

        all_candles = []
        batch_size = 200  # 업비트 API 제한
        batches_needed = (total_count + batch_size - 1) // batch_size

        try:
            for batch_num in range(batches_needed):
                remaining = total_count - len(all_candles)
                current_batch_size = min(batch_size, remaining)

                logger.info(f"📦 배치 {batch_num + 1}/{batches_needed}: {current_batch_size}개 조회")

                # Smart Router로 캔들 조회
                batch_candles = await self.router.get_candles(
                    symbol=symbol,
                    interval=interval,
                    count=current_batch_size
                )

                if batch_candles:
                    all_candles.extend(batch_candles)
                    logger.debug(f"📈 누적 캔들: {len(all_candles)}개")
                else:
                    logger.warning(f"⚠️ 배치 {batch_num + 1} 조회 실패")
                    break

                # API 제한 고려 (0.1초 간격)
                if batch_num < batches_needed - 1:
                    await asyncio.sleep(0.1)

            logger.info(f"✅ 대용량 캔들 조회 완료: {len(all_candles)}개")
            return all_candles

        except Exception as e:
            logger.error(f"❌ 대용량 캔들 조회 예외: {e}")
            return all_candles  # 부분 데이터라도 반환

    async def get_multiple_tickers_parallel(self, symbols: List[str]) -> Dict[str, Any]:
        """다중 심볼 티커 병렬 조회"""
        logger.info(f"🔄 다중 티커 병렬 조회: {len(symbols)}개 심볼")

        start_time = time.time()

        try:
            # 병렬 비동기 처리
            tasks = [
                self.router.get_ticker(symbol)
                for symbol in symbols
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 결과 정리
            ticker_data = {}
            success_count = 0

            for symbol, result in zip(symbols, results):
                if isinstance(result, Exception):
                    logger.warning(f"⚠️ {symbol} 조회 실패: {result}")
                    ticker_data[symbol] = None
                elif result:
                    ticker_data[symbol] = result
                    success_count += 1
                else:
                    ticker_data[symbol] = None

            elapsed = time.time() - start_time
            logger.info(f"✅ 병렬 조회 완료: {success_count}/{len(symbols)} 성공, {elapsed:.2f}초")

            return ticker_data

        except Exception as e:
            logger.error(f"❌ 병렬 조회 예외: {e}")
            return {}

    async def get_comprehensive_market_data(self, symbols: List[str]) -> Dict[str, Any]:
        """종합 마켓 데이터 조회 (티커 + 호가 + 최신 캔들)"""
        logger.info(f"🌐 종합 마켓 데이터 조회: {len(symbols)}개 심볼")

        start_time = time.time()

        try:
            # 병렬로 다양한 데이터 수집
            tasks = {
                'tickers': self.get_multiple_tickers_parallel(symbols),
                'orderbooks': self.get_orderbook_data(symbols[:5]),  # 호가는 5개만 (API 제한)
                'latest_candles': asyncio.gather(*[
                    self.router.get_candles(symbol, "1m", 1)
                    for symbol in symbols[:5]
                ])
            }

            results = await asyncio.gather(*tasks.values(), return_exceptions=True)

            # 결과 조합
            comprehensive_data = {
                'timestamp': datetime.now().isoformat(),
                'symbols_count': len(symbols),
                'data': {}
            }

            # 티커 데이터
            if not isinstance(results[0], Exception):
                comprehensive_data['tickers'] = results[0]

            # 호가 데이터
            if not isinstance(results[1], Exception):
                comprehensive_data['orderbooks'] = results[1]

            # 최신 캔들
            if not isinstance(results[2], Exception) and results[2]:
                latest_candles = {}
                candle_results = results[2]
                if isinstance(candle_results, list):
                    for i, candles in enumerate(candle_results):
                        if i < len(symbols[:5]) and candles and len(candles) > 0:
                            symbol = symbols[i]
                            latest_candles[symbol] = candles[0]  # 최신 캔들만
                    comprehensive_data['latest_candles'] = latest_candles

            elapsed = time.time() - start_time
            logger.info(f"✅ 종합 데이터 조회 완료: {elapsed:.2f}초")

            return comprehensive_data

        except Exception as e:
            logger.error(f"❌ 종합 데이터 조회 예외: {e}")
            return {'error': str(e)}

    async def real_time_monitoring_system(self, symbols: List[str], duration: int = 30):
        """실시간 모니터링 시스템 (지정된 시간 동안)"""
        logger.info(f"👁️ 실시간 모니터링 시작: {len(symbols)}개 심볼, {duration}초간")

        start_time = time.time()
        cycle_count = 0

        try:
            while time.time() - start_time < duration:
                cycle_start = time.time()
                cycle_count += 1

                logger.info(f"🔄 모니터링 사이클 #{cycle_count}")

                # 핵심 심볼 실시간 조회
                core_symbols = symbols[:3]  # 상위 3개만

                # 병렬 실시간 데이터 수집
                ticker_data = await self.get_multiple_tickers_parallel(core_symbols)

                # 간단한 분석
                analysis = {}
                for symbol, data in ticker_data.items():
                    if data:
                        analysis[symbol] = {
                            'price': data.get('trade_price', 0),
                            'change_rate': data.get('signed_change_rate', 0),
                            'volume': data.get('acc_trade_volume_24h', 0)
                        }

                # 로그 출력
                for symbol, info in analysis.items():
                    logger.info(f"📊 {symbol}: ₩{info['price']:,} ({info['change_rate']:+.2%})")

                # 다음 사이클까지 대기 (5초 간격)
                cycle_time = time.time() - cycle_start
                wait_time = max(5.0 - cycle_time, 0.5)
                await asyncio.sleep(wait_time)

            logger.info(f"✅ 실시간 모니터링 완료: {cycle_count}사이클")

        except Exception as e:
            logger.error(f"❌ 실시간 모니터링 예외: {e}")


async def demo_advanced_usage():
    """고급 사용법 데모 실행"""
    system = AdvancedTradingSystem()

    try:
        # 시스템 시작
        await system.start()

        print("\n" + "=" * 60)
        print("🚀 고급 Smart Router 사용법 데모")
        print("=" * 60)

        # 1. 호가 데이터 조회
        print("\n🔸 1. 호가 데이터 조회")
        orderbooks = await system.get_orderbook_data(["KRW-BTC", "KRW-ETH"])
        if orderbooks:
            for symbol, orderbook in orderbooks.items():
                if orderbook and 'orderbook_units' in orderbook:
                    best_ask = orderbook['orderbook_units'][0]
                    print(f"📈 {symbol} 호가: 매도 ₩{best_ask.get('ask_price', 0):,} (수량: {best_ask.get('ask_size', 0)})")

        # 2. 대용량 캔들 데이터
        print("\n🔸 2. 대용량 캔들 차트 데이터 (500개)")
        large_candles = await system.get_large_candle_dataset("KRW-BTC", "5m", 500)
        print(f"📊 BTC 5분봉 차트 데이터: {len(large_candles)}개 캔들")
        if large_candles:
            latest = large_candles[0]  # 최신 캔들
            print(f"📈 최신 캔들: 시가 ₩{latest.get('opening_price', 0):,}, "
                  f"종가 ₩{latest.get('trade_price', 0):,}")

        # 3. 다중 심볼 병렬 조회
        print("\n🔸 3. KRW 마켓 다중 심볼 병렬 조회")
        multi_tickers = await system.get_multiple_tickers_parallel(system.krw_symbols)
        success_symbols = [s for s, d in multi_tickers.items() if d is not None]
        print(f"🔄 병렬 조회 결과: {len(success_symbols)}/{len(system.krw_symbols)} 성공")

        # 상위 3개 출력
        for symbol in success_symbols[:3]:
            data = multi_tickers[symbol]
            if data:
                price = data.get('trade_price', 0)
                change_rate = data.get('signed_change_rate', 0)
                print(f"💰 {symbol}: ₩{price:,} ({change_rate:+.2%})")

        # 4. 종합 마켓 데이터
        print("\n🔸 4. 종합 마켓 데이터 조회")
        comprehensive = await system.get_comprehensive_market_data(system.krw_symbols[:5])

        if 'tickers' in comprehensive:
            print(f"📊 티커 데이터: {len([k for k, v in comprehensive['tickers'].items() if v])}개")
        if 'orderbooks' in comprehensive:
            print(f"📈 호가 데이터: {len(comprehensive['orderbooks'])}개")
        if 'latest_candles' in comprehensive:
            print(f"🕯️ 최신 캔들: {len(comprehensive['latest_candles'])}개")

        # 5. 실시간 모니터링 (10초간)
        print("\n🔸 5. 실시간 모니터링 시스템 (10초간)")
        await system.real_time_monitoring_system(["KRW-BTC", "KRW-ETH", "KRW-XRP"], 10)

        # 최종 통계
        print("\n🔸 최종 사용 통계")
        stats = system.router.get_usage_stats()
        print(f"📊 추적된 심볼: {stats['total_symbols']}개")
        print(f"🔥 고빈도 심볼: {len([s for s, d in stats['symbols'].items() if d['is_high_frequency']])}개")

        total_requests = sum(data['total_requests'] for data in stats['symbols'].values())
        print(f"📈 총 요청 수: {total_requests}회")

    except Exception as e:
        logger.error(f"❌ 데모 실행 오류: {e}")
        print(f"❌ 오류 발생: {e}")

    finally:
        # 시스템 정지
        await system.stop()


if __name__ == "__main__":
    print("🚀 고급 Smart Router 사용법 데모를 시작합니다...")
    asyncio.run(demo_advanced_usage())
