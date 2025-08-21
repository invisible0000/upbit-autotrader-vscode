"""
Simple Smart Router 사용 예제

기존 복잡한 스마트 라우팅 시스템을 단순한 API로 래핑한 예제입니다.
실제 시스템 통합을 위한 데모를 제공합니다.
"""

import asyncio
from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.simple_smart_router import (
    get_simple_router, initialize_simple_router
)

logger = create_component_logger("SimpleRouterDemo")


async def demo_basic_usage():
    """기본 사용법 데모"""
    logger.info("=== Simple Smart Router 기본 사용법 데모 ===")

    # 1. 라우터 초기화
    router = await initialize_simple_router()
    logger.info("✅ Simple Router 초기화 완료")

    # 2. 티커 데이터 조회 (단순)
    logger.info("🔍 티커 데이터 조회 중...")
    ticker_data = await router.get_ticker("KRW-BTC")
    logger.info(f"📊 티커 데이터 조회 결과: {len(ticker_data)} 필드")

    # 3. 캔들 데이터 조회 (단순)
    logger.info("🔍 캔들 데이터 조회 중...")
    candle_data = await router.get_candles("KRW-BTC", "1m", 10)
    logger.info(f"📊 캔들 데이터 조회 결과: {len(candle_data)} 개 캔들")

    # 4. 패턴 학습 확인
    pattern = router.get_symbol_pattern("KRW-BTC")
    logger.info(f"🧠 학습된 패턴: {pattern.get_frequency_category()}")

    # 5. 정리
    await router.stop()
    logger.info("✅ Simple Router 정지 완료")


async def demo_pattern_learning():
    """패턴 학습 데모"""
    logger.info("=== 패턴 학습 데모 ===")

    router = await initialize_simple_router()

    # 고빈도 요청 패턴 시뮬레이션
    logger.info("🔥 고빈도 요청 패턴 시뮬레이션...")
    for i in range(10):
        await router.get_ticker("KRW-ETH")
        await asyncio.sleep(0.5)  # 0.5초 간격으로 빠른 요청

    # 패턴 확인
    pattern = router.get_symbol_pattern("KRW-ETH")
    logger.info(f"🧠 ETH 패턴 분석 결과: {pattern.get_frequency_category()}")
    logger.info(f"📈 총 요청 수: {len(pattern.request_history)}")
    logger.info(f"⚡ 고빈도 여부: {pattern.is_high_frequency()}")

    await router.stop()


async def demo_multiple_symbols():
    """다중 심볼 처리 데모"""
    logger.info("=== 다중 심볼 처리 데모 ===")

    router = await initialize_simple_router()

    symbols = ["KRW-BTC", "KRW-ETH", "KRW-ADA", "KRW-XRP", "KRW-DOT"]

    # 병렬 요청 처리
    logger.info(f"🔄 {len(symbols)}개 심볼 병렬 처리...")
    tasks = [router.get_ticker(symbol) for symbol in symbols]
    results = await asyncio.gather(*tasks)

    successful_results = [r for r in results if r]
    logger.info(f"✅ 성공적 조회: {len(successful_results)}/{len(symbols)} 심볼")

    # 각 심볼별 패턴 확인
    for symbol in symbols:
        pattern = router.get_symbol_pattern(symbol)
        logger.info(f"📊 {symbol}: {pattern.get_frequency_category()} ({len(pattern.request_history)} 요청)")

    await router.stop()


async def demo_error_handling():
    """에러 처리 데모"""
    logger.info("=== 에러 처리 데모 ===")

    router = await initialize_simple_router()

    # 잘못된 심볼 처리는 skip (API 호출 방지)
    logger.info("❌ 잘못된 심볼 테스트 (스킵됨 - API 호출 방지)")
    logger.info("🔍 실제 서비스에서는 심볼 검증 로직이 필요합니다")

    # 정상 요청으로 테스트
    logger.info("✅ 정상 요청 테스트...")
    valid_data = await router.get_ticker("KRW-BTC")
    logger.info(f"🔍 정상 요청 결과: {len(valid_data)} 필드")

    await router.stop()


async def demo_integration_example():
    """실제 시스템 통합 예제"""
    logger.info("=== 실제 시스템 통합 예제 ===")

    # 전역 라우터 사용 (싱글톤 패턴)
    router = get_simple_router()
    await router.start()

    # 차트 뷰어 시뮬레이션
    logger.info("📈 차트 뷰어 시뮬레이션...")
    chart_data = await router.get_candles("KRW-BTC", "5m", 50)
    logger.info(f"📊 차트용 캔들 데이터: {len(chart_data)} 개")

    # 백테스팅 시뮬레이션
    logger.info("🔙 백테스팅 시뮬레이션...")
    backtest_data = await router.get_candles("KRW-ETH", "1h", 100)
    logger.info(f"📊 백테스트용 캔들 데이터: {len(backtest_data)} 개")

    # 실시간 모니터링 시뮬레이션
    logger.info("👁️ 실시간 모니터링 시뮬레이션...")
    monitoring_symbols = ["KRW-BTC", "KRW-ETH", "KRW-ADA"]
    for symbol in monitoring_symbols:
        ticker = await router.get_ticker(symbol)
        logger.info(f"📡 {symbol} 모니터링: {len(ticker)} 필드")

    # 통계 확인
    stats = router.get_usage_stats()
    total_requests = sum(symbol_stats['total_requests'] for symbol_stats in stats['symbols'].values())
    frequency_distribution = {}
    for symbol_stats in stats['symbols'].values():
        freq_category = symbol_stats['frequency_category']
        frequency_distribution[freq_category] = frequency_distribution.get(freq_category, 0) + 1

    logger.info(f"📈 전체 사용 통계:")
    logger.info(f"  - 총 심볼 수: {stats['total_symbols']}")
    logger.info(f"  - 총 요청 수: {total_requests}")
    logger.info(f"  - 빈도 분포: {frequency_distribution}")

    await router.stop()


async def main():
    """메인 데모 실행"""
    logger.info("🚀 Simple Smart Router 데모 시작")

    try:
        await demo_basic_usage()
        await asyncio.sleep(1)

        await demo_pattern_learning()
        await asyncio.sleep(1)

        await demo_multiple_symbols()
        await asyncio.sleep(1)

        await demo_error_handling()
        await asyncio.sleep(1)

        await demo_integration_example()

        logger.info("✅ 모든 데모 완료")

    except Exception as e:
        logger.error(f"❌ 데모 실행 중 오류: {e}")
        raise


if __name__ == "__main__":
    # 환경 변수 설정 (로깅)
    import os
    os.environ["UPBIT_CONSOLE_OUTPUT"] = "true"
    os.environ["UPBIT_LOG_SCOPE"] = "verbose"

    # 데모 실행
    asyncio.run(main())
