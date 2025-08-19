"""
통합 마켓 데이터 API 사용 예제

사용자가 제안한 "백본 통신 채널" 시스템의 실제 사용 방법을 보여주는 예제입니다.
실제 업비트 API/WebSocket 클라이언트와 연동하여 완전한 시스템을 구성합니다.
"""

import asyncio
from typing import List, Dict, Any

from upbit_auto_trading.infrastructure.market_data_backbone.unified_market_data_api import (
    UnifiedMarketDataAPI,
    DataRequest,
    DataRequestType,
    ChannelStrategy,
    create_unified_api,
    create_candle_request,
    create_realtime_request
)
from upbit_auto_trading.infrastructure.logging import create_component_logger


async def demo_simple_candle_request():
    """
    단순 캔들 데이터 요청 데모

    시스템이 자동으로 최적의 채널(API vs WebSocket)을 선택하여
    데이터를 가져오는 과정을 보여줍니다.
    """
    logger = create_component_logger("CandleRequestDemo")

    logger.info("=== 단순 캔들 데이터 요청 데모 ===")

    # 통합 API 생성 (실제 클라이언트는 None으로 시뮬레이션)
    api = await create_unified_api()

    try:
        # 캔들 데이터 요청 생성
        request = create_candle_request(
            symbol="KRW-BTC",
            timeframe="1m",
            count=200,
            strategy=ChannelStrategy.AUTO  # 자동 최적화
        )

        logger.info(f"요청 생성: {request.symbol} {request.timeframe} {request.count}개")

        # 동기 방식으로 데이터 요청
        candles = await api.request_data_sync(request)

        logger.info(f"✅ 데이터 수신 완료: {len(candles)}개")
        logger.info(f"첫 번째 캔들: {candles[0] if candles else 'None'}")

        # 성능 메트릭 확인
        metrics = api.get_performance_metrics()
        logger.info(f"활성 요청 수: {metrics['active_requests']}")

    except Exception as e:
        logger.error(f"요청 실패: {e}")


async def demo_realtime_data_streaming():
    """
    실시간 데이터 스트리밍 데모

    WebSocket을 통한 실시간 데이터 수신과
    자동 장애 복구를 보여줍니다.
    """
    logger = create_component_logger("RealtimeStreamingDemo")

    logger.info("=== 실시간 데이터 스트리밍 데모 ===")

    # 수신된 데이터 처리 콜백
    def on_realtime_data(data: List[Dict[str, Any]]):
        logger.info(f"📊 실시간 데이터 수신: {len(data)}개")
        for item in data[:2]:  # 처음 2개만 출력
            logger.info(f"  └─ {item.get('symbol', 'Unknown')}: {item.get('price', 0):,.0f}원")

    api = await create_unified_api()

    try:
        # 실시간 요청 생성
        request = create_realtime_request(
            symbol="KRW-BTC",
            timeframe="1m",
            data_callback=on_realtime_data
        )

        logger.info(f"실시간 구독 시작: {request.symbol}")

        # 비동기 방식으로 실시간 구독
        request_id = await api.request_data(request)
        logger.info(f"구독 ID: {request_id}")

        # 5초간 실시간 데이터 수신
        await asyncio.sleep(5)

        logger.info("✅ 실시간 스트리밍 완료")

    except Exception as e:
        logger.error(f"스트리밍 실패: {e}")


async def demo_multi_symbol_monitoring():
    """
    다중 심볼 모니터링 데모

    여러 코인을 동시에 모니터링하면서
    각각에 최적화된 채널을 자동 선택하는 과정을 보여줍니다.
    """
    logger = create_component_logger("MultiSymbolDemo")

    logger.info("=== 다중 심볼 모니터링 데모 ===")

    # 모니터링할 심볼들
    symbols = ["KRW-BTC", "KRW-ETH", "KRW-ADA", "KRW-DOT", "KRW-LINK"]

    # 데이터 수신 카운터
    data_counters = {symbol: 0 for symbol in symbols}

    def create_callback(symbol: str):
        def callback(data: List[Dict[str, Any]]):
            data_counters[symbol] += len(data)
            logger.info(f"📈 {symbol}: {len(data)}개 수신 (총 {data_counters[symbol]}개)")
        return callback

    api = await create_unified_api()

    try:
        # 모든 심볼에 대해 동시 요청
        tasks = []
        for symbol in symbols:
            # 심볼별로 다른 전략 사용 (데모용)
            strategies = [
                ChannelStrategy.AUTO,
                ChannelStrategy.WEBSOCKET_PREFERRED,
                ChannelStrategy.HYBRID_BALANCED,
                ChannelStrategy.API_PREFERRED,
                ChannelStrategy.AUTO
            ]

            strategy = strategies[symbols.index(symbol)]

            request = create_realtime_request(
                symbol=symbol,
                timeframe="1m",
                data_callback=create_callback(symbol)
            )
            request.channel_strategy = strategy

            tasks.append(api.request_data(request))
            logger.info(f"요청 생성: {symbol} (전략: {strategy.value})")

        # 모든 요청 동시 실행
        request_ids = await asyncio.gather(*tasks)
        logger.info(f"✅ {len(request_ids)}개 심볼 모니터링 시작")

        # 10초간 모니터링
        for i in range(10):
            await asyncio.sleep(1)
            total_data = sum(data_counters.values())
            logger.info(f"[{i+1}/10초] 총 수신 데이터: {total_data}개")

        # 최종 결과 출력
        logger.info("=== 최종 결과 ===")
        for symbol, count in data_counters.items():
            logger.info(f"  {symbol}: {count}개")

        # 성능 메트릭 확인
        metrics = api.get_performance_metrics()
        logger.info(f"최종 활성 요청: {metrics['active_requests']}개")

    except Exception as e:
        logger.error(f"다중 모니터링 실패: {e}")


async def demo_fallback_resilience():
    """
    장애 복구 및 복원력 데모

    한 채널이 실패했을 때 자동으로 다른 채널로
    전환되는 과정을 시뮬레이션합니다.
    """
    logger = create_component_logger("FallbackDemo")

    logger.info("=== 장애 복구 및 복원력 데모 ===")

    api = await create_unified_api()

    try:
        # 1. 정상 상태에서 데이터 요청
        logger.info("1단계: 정상 상태 데이터 요청")
        normal_request = create_candle_request("KRW-BTC", "1m", 100)

        start_time = asyncio.get_event_loop().time()
        data = await api.request_data_sync(normal_request)
        response_time = (asyncio.get_event_loop().time() - start_time) * 1000

        logger.info(f"  ✅ 정상 응답: {len(data)}개 ({response_time:.1f}ms)")

        # 2. WebSocket 장애 시뮬레이션
        logger.info("2단계: WebSocket 장애 시뮬레이션")

        # 채널 라우터에 WebSocket 장애 보고
        api._channel_router.update_channel_performance("websocket", 5000.0, False)
        api._channel_router.update_channel_performance("api", 300.0, True)

        # WebSocket 우선 요청이지만 API로 자동 전환되어야 함
        fallback_request = create_realtime_request("KRW-ETH", "1m")
        fallback_request.channel_strategy = ChannelStrategy.WEBSOCKET_PREFERRED

        start_time = asyncio.get_event_loop().time()
        request_id = await api.request_data(fallback_request)
        response_time = (asyncio.get_event_loop().time() - start_time) * 1000

        logger.info(f"  ✅ 자동 전환 완료: {request_id} ({response_time:.1f}ms)")

        # 3. 채널 상태 확인
        logger.info("3단계: 채널 상태 확인")
        channel_status = api.get_channel_status()

        for channel, status in channel_status.items():
            logger.info(f"  📊 {channel}: 가용성={status.is_available}, "
                       f"지연시간={status.latency_ms:.1f}ms, "
                       f"성공률={status.success_rate:.1%}")

        # 4. 복구 후 성능 개선 확인
        logger.info("4단계: 복구 시뮬레이션")

        # WebSocket 복구 시뮬레이션
        api._channel_router.update_channel_performance("websocket", 150.0, True)

        recovery_request = create_candle_request("KRW-BTC", "5m", 50)
        recovery_request.channel_strategy = ChannelStrategy.AUTO

        start_time = asyncio.get_event_loop().time()
        data = await api.request_data_sync(recovery_request)
        response_time = (asyncio.get_event_loop().time() - start_time) * 1000

        logger.info(f"  ✅ 복구 후 성능: {len(data)}개 ({response_time:.1f}ms)")

        logger.info("✅ 장애 복구 데모 완료")

    except Exception as e:
        logger.error(f"장애 복구 데모 실패: {e}")


async def demo_channel_optimization():
    """
    채널 최적화 데모

    다양한 요청 유형에 대해 시스템이 어떻게
    최적의 채널을 선택하는지 보여줍니다.
    """
    logger = create_component_logger("OptimizationDemo")

    logger.info("=== 채널 최적화 데모 ===")

    api = await create_unified_api()

    test_cases = [
        ("대량 과거 데이터", DataRequestType.HISTORICAL_CANDLES, {"count": 1000}),
        ("소량 과거 데이터", DataRequestType.HISTORICAL_CANDLES, {"count": 50}),
        ("실시간 캔들", DataRequestType.REALTIME_CANDLES, {}),
        ("호가창", DataRequestType.ORDERBOOK, {}),
        ("현재가", DataRequestType.TICKER, {}),
        ("체결내역", DataRequestType.TRADES, {})
    ]

    for description, request_type, params in test_cases:
        try:
            logger.info(f"📋 테스트 케이스: {description}")

            # 요청 생성
            request = DataRequest(
                request_type=request_type,
                symbol="KRW-BTC",
                timeframe="1m" if request_type in [DataRequestType.HISTORICAL_CANDLES, DataRequestType.REALTIME_CANDLES] else None,
                **params
            )

            # 최적 채널 분석
            optimal_strategy = api._channel_router.analyze_optimal_channel(request)

            logger.info(f"  🎯 선택된 전략: {optimal_strategy.value}")
            logger.info(f"  📊 요청 타입: {request_type.value}")

            # 데이터 소스 설정 확인
            config = api._create_data_source_config(request, optimal_strategy)
            logger.info(f"  ⚙️ 소스 타입: {config.source_type}")
            logger.info(f"  📈 하이브리드 비율: {config.hybrid_ratio:.1%} (WebSocket)")
            logger.info("")

        except Exception as e:
            logger.error(f"최적화 테스트 실패 - {description}: {e}")

    logger.info("✅ 채널 최적화 데모 완료")


async def main():
    """메인 데모 실행"""
    logger = create_component_logger("MainDemo")

    logger.info("🚀 통합 마켓 데이터 API 종합 데모 시작")

    demos = [
        ("단순 캔들 요청", demo_simple_candle_request),
        ("실시간 스트리밍", demo_realtime_data_streaming),
        ("다중 심볼 모니터링", demo_multi_symbol_monitoring),
        ("장애 복구 및 복원력", demo_fallback_resilience),
        ("채널 최적화", demo_channel_optimization)
    ]

    for name, demo_func in demos:
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"🎬 {name} 데모 시작")
            logger.info(f"{'='*60}")

            await demo_func()

            logger.info(f"✅ {name} 데모 완료")
            await asyncio.sleep(1)  # 데모 간 간격

        except Exception as e:
            logger.error(f"❌ {name} 데모 실패: {e}")

    logger.info("\n🎉 모든 데모 완료!")


if __name__ == "__main__":
    # 로깅 환경 설정
    import os
    os.environ["UPBIT_CONSOLE_OUTPUT"] = "true"
    os.environ["UPBIT_LOG_SCOPE"] = "verbose"

    # 데모 실행
    asyncio.run(main())
