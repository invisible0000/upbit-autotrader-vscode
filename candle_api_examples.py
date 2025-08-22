"""
업비트 스마트 라우팅 캔들 API 사용 예시

업비트 REST API 형식과 일치하는 캔들 요청 방법을 보여줍니다.
"""

import asyncio
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing import SmartRouter
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("CandleExamples")


async def main():
    """캔들 API 사용 예시"""
    smart_router = SmartRouter()

    try:
        await smart_router.initialize()
        logger.info("=== 업비트 스마트 라우팅 캔들 API 사용 예시 ===\n")

        # 🔥 실거래 용도별 구분 안내
        logger.info("🔥 실거래 용도별 데이터 선택 가이드:")
        logger.info("   ✅ 실시간 매매 변수 (주문가격, 손익계산) → get_ticker() 사용")
        logger.info("   ✅ 기술적 분석 (RSI, 이동평균, 차트패턴) → get_candles() 사용")
        logger.info("")
        logger.info("📊 타임프레임 차이 (업비트 공식 확인):")
        logger.info("   🎯 티커 OHLC = 일봉 타임프레임 (UTC 0시~현재)")
        logger.info("     - opening_price: 당일 첫 거래가")
        logger.info("     - high_price: 당일 최고가")
        logger.info("     - low_price: 당일 최저가")
        logger.info("     - trade_price: 현재 최신 체결가")
        logger.info("")
        logger.info("   📈 캔들 OHLC = 지정 타임프레임 (1m/5m/1h/1d 등)")
        logger.info("     - opening_price: 해당 봉 시작가")
        logger.info("     - high_price: 해당 봉 최고가")
        logger.info("     - low_price: 해당 봉 최저가")
        logger.info("     - trade_price: 해당 봉 종가")
        print()

        # 예시 1: 명시적 1분봉 단일 캔들
        logger.info("1️⃣ 최신 1분봉 캔들 조회 (기술적 분석용)")
        logger.info("   사용법: get_candles(['KRW-BTC'], interval='1m', count=1)")
        result1 = await smart_router.get_candles(["KRW-BTC"], interval="1m", count=1)
        logger.info(f"   결과: success={result1.get('success', False)}")
        logger.info("   용도: RSI, 이동평균 등 기술적 분석")
        print()

        # 예시 2: 실시간 현재가 (매매 변수용)
        logger.info("2️⃣ 실시간 현재가 조회 (매매 변수용)")
        logger.info("   사용법: get_ticker(['KRW-BTC'])")
        try:
            result2 = await smart_router.get_ticker(["KRW-BTC"])
            logger.info(f"   결과: success={result2.get('success', False)}")
            logger.info("   용도: 주문 가격 결정, 실시간 손익 계산")
        except AttributeError:
            logger.info("   (get_ticker 메서드 사용 - 별도 구현 필요)")
        print()

        # 예시 3: 5분봉 기술적 분석용
        logger.info("3️⃣ 5분봉 20개 조회 (기술적 분석용)")
        logger.info("   사용법: get_candles(['KRW-BTC'], interval='5m', count=20)")
        result3 = await smart_router.get_candles(["KRW-BTC"], interval="5m", count=20)
        logger.info(f"   결과: success={result3.get('success', False)}")
        logger.info("   용도: 5분봉 RSI, 단기 이동평균")
        print()        # 예시 4: 특정 시점부터 조회 (ISO 8601 형식)
        logger.info("4️⃣ 특정 시점부터 캔들 조회")
        to_time = "2025-08-22T03:00:00Z"  # UTC 기준
        logger.info(f"   사용법: get_candles(['KRW-BTC'], count=5, to='{to_time}')")
        result4 = await smart_router.get_candles(["KRW-BTC"], count=5, to=to_time)
        logger.info(f"   결과: success={result4.get('success', False)}")
        logger.info(f"   데이터 개수: {len(result4.get('data', []))}")
        print()

        # 예시 5: 다중 심볼 (다중 타임프레임 전략 시뮬레이션)
        logger.info("5️⃣ 다중 심볼 캔들 조회 (다중 타임프레임 전략)")
        symbols = ["KRW-BTC", "KRW-ETH", "KRW-DOGE"]
        logger.info(f"   사용법: get_candles({symbols}, interval='15m', count=5)")
        result5 = await smart_router.get_candles(symbols, interval="15m", count=5)
        logger.info(f"   결과: success={result5.get('success', False)}")
        logger.info(f"   데이터 개수: {len(result5.get('data', []))}")
        print()

        # 예시 6: 일봉 데이터 (과거 데이터 조회)
        logger.info("6️⃣ 일봉 200개 조회 (과거 데이터)")
        logger.info("   사용법: get_candles(['KRW-BTC'], interval='1d', count=200)")
        result6 = await smart_router.get_candles(["KRW-BTC"], interval="1d", count=200)
        logger.info(f"   결과: success={result6.get('success', False)}")
        logger.info(f"   데이터 개수: {len(result6.get('data', []))}")
        print()

        # 예시 7: 실거래 현재가 모니터링 (하이브리드 방식)
        logger.info("7️⃣ 실거래 현재가 모니터링 - 하이브리드 방식")
        logger.info("   용도: 포지션별 타임프레임 통일 + 체결 없음 안전성")
        logger.info("")

        # 티커로 최신 체결가 확보
        logger.info("   단계 1: 티커로 최신 체결가 확보")
        try:
            # ticker_result = await smart_router.get_ticker(["KRW-BTC"])
            logger.info("   ticker_result = await smart_router.get_ticker(['KRW-BTC'])")
            logger.info("   latest_price = ticker_result['trade_price']")
            logger.info("   latest_timestamp = ticker_result['trade_timestamp']")
        except AttributeError:
            logger.info("   (get_ticker 메서드 구현 필요)")

        # 포지션 타임프레임 캔들 확인
        logger.info("")
        logger.info("   단계 2: 포지션 타임프레임(5분) 캔들 확인")
        result7 = await smart_router.get_candles(["KRW-BTC"], interval="5m", count=1)
        if result7.get('success') and result7.get('data') and len(result7['data']) > 0:
            candle = result7['data'][0]
            logger.info(f"   캔들 종가: {candle.get('trade_price', 'N/A')}")
            logger.info(f"   캔들 시간: {candle.get('candle_date_time', 'N/A')}")
        else:
            logger.info("   캔들 데이터 없음 또는 접근 오류")

        logger.info("")
        logger.info("   단계 3: 시간 차이 검증 및 현재가 선택")
        logger.info("   if (티커시간 - 캔들시간) < 타임프레임:")
        logger.info("       return 캔들_종가  # 타임프레임 일치")
        logger.info("   else:")
        logger.info("       return 티커_현재가  # 체결 없음 대응")
        print()

        logger.info("=== 실거래 데이터 선택 가이드 ===")
        logger.info("🔥 매매 변수 계산 (실시간):")
        logger.info("   → get_ticker() - 주문가격, 손익계산, 진입/청산 판단")
        logger.info("   → 티커 OHLC = 일봉 기준 (UTC 0시~현재)")
        logger.info("")
        logger.info("📊 기술적 분석 (과거 데이터):")
        logger.info("   → get_candles() - RSI, 이동평균, 차트패턴, 백테스팅")
        logger.info("   → 캔들 OHLC = 지정 타임프레임 (1m/5m/1h/1d 등)")
        logger.info("")
        logger.info("⚡ 핵심 구분점:")
        logger.info("   - 티커: 동명 필드여도 '일봉 타임프레임' 고정")
        logger.info("   - 캔들: 명시적 타임프레임 지정 (1분~월봉)")
        logger.info("   - 실시간 거래 = 티커, 기술 분석 = 캔들")
        logger.info("")
        logger.info("🔥 실거래 현재가 모니터링 전략 (하이브리드):")
        logger.info("   1️⃣ 기본: 포지션 타임프레임 캔들의 trade_price")
        logger.info("   2️⃣ 백업: 체결 없음/지연 시 티커 trade_price")
        logger.info("   3️⃣ 검증: 캔들vs티커 시간차로 유효성 판단")
        logger.info("")
        logger.info("📍 체결 없음 상황 대응:")
        logger.info("   - 캔들: 해당 구간 체결 없으면 데이터 미생성")
        logger.info("   - 티커: 체결 없어도 이전 유효 데이터 유지")
        logger.info("   - 권장: 캔들 우선 + 티커 백업 (안전성)")
        logger.info("")
        logger.info("⭐ 포지션별 타임프레임 통일성:")
        logger.info("   - 5분 포지션 → 5분봉 현재가 모니터링")
        logger.info("   - 15분 포지션 → 15분봉 현재가 모니터링")
        logger.info("   - 타임프레임 일치로 전략 일관성 확보")
        logger.info("")
        logger.info("📋 캔들 API 형식:")
        logger.info("   get_candles(symbols, interval='1m', count=1, to=None)")
        logger.info("")
        logger.info("📋 매개변수:")
        logger.info("   - symbols: List[str] - 조회할 심볼 리스트 (예: ['KRW-BTC'])")
        logger.info("   - interval: str - 캔들 간격 (1m, 3m, 5m, 15m, 30m, 1h, 1d, 1w, 1M)")
        logger.info("   - count: int - 조회할 캔들 개수 (최대 200개, 기본값: 1)")
        logger.info("   - to: str - 종료 시각 (ISO 8601, 예: '2025-08-22T03:00:00Z')")
        logger.info("")
        logger.info("📋 스마트 라우팅 (캔들용):")
        logger.info("   🚨 1단계: 필수 검증 (데이터 무결성)")
        logger.info("     - 타임프레임(interval) 필수")
        logger.info("     - 심볼(symbols) 필수")
        logger.info("     - count > 1 → REST API 강제")
        logger.info("     - to 매개변수 → REST API 강제")
        logger.info("")
        logger.info("   ⚡ 2단계: WebSocket vs REST 경합 (단일 캔들만)")
        logger.info("     - count = 1: WebSocket 우선 (실시간성)")
        logger.info("     - count 없음: WebSocket 우선 (최신 1개)")
        logger.info("     - 다중 심볼: WebSocket 효율성 우대")
        logger.info("")
        logger.info("🎯 타임프레임별 채널 선택 패턴:")
        logger.info("   ✅ 단일 최신 캔들: WebSocket vs REST 경합")
        logger.info("   🔒 과거/다중 캔들: REST API 강제 (데이터 무결성)")
        logger.info("   🔒 대용량 히스토리: REST API 강제 (성능)")
        logger.info("")
        logger.info("⚠️  주의사항:")
        logger.info("   🚨 타임프레임(interval)과 심볼(symbols) 필수 (검증됨)")
        logger.info("   🚨 WebSocket 캔들 = 최신 1개만 (count > 1은 REST 강제)")
        logger.info("   🚨 과거 데이터(to) = REST API 강제 (WebSocket 불가)")
        logger.info("   ✅ 실시간 매매 = 티커, 기술분석 = 캔들")
        logger.info("   ✅ WebSocket vs REST 경합 = 단일 최신 캔들만")

    except Exception as e:
        logger.error(f"예시 실행 중 오류: {e}")
    finally:
        await smart_router.cleanup_resources()


if __name__ == "__main__":
    asyncio.run(main())
