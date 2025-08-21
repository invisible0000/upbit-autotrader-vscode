"""
개선된 스마트 라우팅 시스템 데모

사용자 피드백을 반영한 안정적이고 직관적인 라우팅 전략 시연:
1. 요청 패턴 기반 자동 최적화
2. 안정적인 데이터 반환 보장
3. 실패 복구 메커니즘
4. 실시간 vs 히스토리컬 데이터 최적화
"""

import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing import (
    initialize_simple_router
)

# 로깅 설정
logger = create_component_logger("ImprovedRouterDemo")


async def demo_improved_basic_usage():
    """기본 사용법 데모 - 개선된 버전"""
    logger.info("=== 개선된 Smart Router 기본 사용법 데모 ===")

    # 라우터 초기화
    router = await initialize_simple_router()

    try:
        # 1. 기본 티커 조회
        logger.info("🔍 기본 티커 데이터 조회 중...")
        ticker_data = await router.get_ticker("KRW-BTC")

        if ticker_data:
            logger.info(f"✅ 티커 조회 성공: {len(ticker_data)} 필드")
            logger.info(f"📊 주요 정보 - 현재가: {ticker_data.get('trade_price', 'N/A')}")
        else:
            logger.warning("⚠️ 티커 데이터를 가져오지 못했습니다")

        # 2. 실시간 최신 캔들 조회 (웹소켓 우선)
        logger.info("🔍 실시간 최신 캔들 조회 중... (웹소켓 우선)")
        latest_candle = await router.get_candles("KRW-BTC", "1m", count=1)

        if latest_candle:
            logger.info(f"✅ 최신 캔들 조회 성공: {len(latest_candle)} 개")
        else:
            logger.warning("⚠️ 최신 캔들 데이터를 가져오지 못했습니다")

        # 3. 히스토리컬 캔들 조회 (REST API 우선)
        logger.info("🔍 히스토리컬 캔들 조회 중... (REST API 우선)")
        historical_candles = await router.get_candles("KRW-BTC", "1m", count=200)

        if historical_candles:
            logger.info(f"✅ 히스토리컬 캔들 조회 성공: {len(historical_candles)} 개")
        else:
            logger.warning("⚠️ 히스토리컬 캔들 데이터를 가져오지 못했습니다")

        # 4. 사용 패턴 확인
        pattern = router.get_symbol_pattern("KRW-BTC")
        logger.info(f"📈 사용 패턴 - 요청 수: {len(pattern.request_history)}, 카테고리: {pattern.get_frequency_category()}")

        # 5. 전체 사용 통계
        stats = router.get_usage_stats()
        logger.info(f"📊 사용 통계: {stats}")

    except Exception as e:
        logger.error(f"❌ 데모 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await router.stop()


async def demo_pattern_optimization():
    """요청 패턴 최적화 데모"""
    logger.info("=== 요청 패턴 기반 최적화 데모 ===")

    router = await initialize_simple_router()

    try:
        symbol = "KRW-ETH"

        # 1. 고빈도 실시간 패턴 시뮬레이션
        logger.info("🚀 고빈도 실시간 패턴 시뮬레이션...")
        for i in range(6):  # 빠른 연속 요청
            ticker = await router.get_ticker(symbol)
            if ticker:
                logger.info(f"  [{i+1}/6] 실시간 데이터: {ticker.get('trade_price', 'N/A')}")
            await asyncio.sleep(0.5)  # 0.5초 간격

        # 패턴 확인
        pattern = router.get_symbol_pattern(symbol)
        logger.info(f"📊 패턴 분석: {pattern.get_frequency_category()} (고빈도: {pattern.is_high_frequency()})")

        # 2. 이제 최신 캔들 요청 (실시간 최적화된 라우팅 적용)
        logger.info("🔍 실시간 최적화된 캔들 조회...")
        optimized_candle = await router.get_candles(symbol, "1m", count=1)
        if optimized_candle:
            logger.info(f"✅ 최적화된 캔들: {len(optimized_candle)} 개")

    except Exception as e:
        logger.error(f"❌ 패턴 최적화 데모 오류: {e}")

    finally:
        await router.stop()


async def demo_failure_recovery():
    """실패 복구 메커니즘 데모"""
    logger.info("=== 실패 복구 메커니즘 데모 ===")

    router = await initialize_simple_router()

    try:
        # 1. 정상적인 요청으로 캐시 구축
        logger.info("🔧 캐시 구축을 위한 정상 요청...")
        normal_data = await router.get_ticker("KRW-ADA")
        if normal_data:
            logger.info("✅ 정상 데이터로 캐시 구축 완료")

        # 2. 존재하지 않는 심볼 처리는 skip (API 호출 방지)
        logger.info("🔍 존재하지 않는 심볼 테스트 (스킵됨 - API 호출 방지)")
        logger.info("📊 실제 서비스에서는 심볼 검증 로직이 필요합니다")

        # 3. 정상 심볼로 복구 확인
        logger.info("🔍 정상 심볼로 복구 확인...")
        recovery_data = await router.get_ticker("KRW-ADA")
        if recovery_data:
            logger.info("✅ 복구 성공: 시스템이 정상적으로 작동합니다")

    except Exception as e:
        logger.error(f"❌ 실패 복구 데모 오류: {e}")

    finally:
        await router.stop()


async def demo_candle_request_patterns():
    """캔들 요청 패턴별 최적화 데모"""
    logger.info("=== 캔들 요청 패턴별 최적화 데모 ===")

    router = await initialize_simple_router()

    try:
        symbol = "KRW-DOGE"

        # 1. 최신 1개 캔들 (웹소켓 우선)
        logger.info("📊 최신 1개 캔들 요청 (웹소켓 우선 전략)...")
        latest = await router.get_candles(symbol, "1m", count=1)
        logger.info(f"  결과: {len(latest)} 개 캔들")

        # 2. 중간 크기 요청 (균형 전략)
        logger.info("📊 중간 크기 캔들 요청 (균형 전략)...")
        medium = await router.get_candles(symbol, "1m", count=50)
        logger.info(f"  결과: {len(medium)} 개 캔들")

        # 3. 대량 히스토리컬 요청 (REST API 우선)
        logger.info("📊 대량 히스토리컬 요청 (REST API 우선 전략)...")
        historical = await router.get_candles(symbol, "1m", count=500)
        logger.info(f"  결과: {len(historical)} 개 캔들")

        # 패턴 분석
        pattern = router.get_symbol_pattern(symbol)
        logger.info(f"📈 최종 패턴: {pattern.get_frequency_category()}")

    except Exception as e:
        logger.error(f"❌ 캔들 패턴 데모 오류: {e}")

    finally:
        await router.stop()


async def main():
    """메인 데모 실행"""
    try:
        logger.info("🚀 개선된 Smart Router 시스템 데모 시작")

        # 1. 기본 사용법
        await demo_improved_basic_usage()
        await asyncio.sleep(2)

        # 2. 패턴 최적화
        await demo_pattern_optimization()
        await asyncio.sleep(2)

        # 3. 실패 복구
        await demo_failure_recovery()
        await asyncio.sleep(2)

        # 4. 캔들 요청 패턴
        await demo_candle_request_patterns()

        logger.info("✅ 모든 데모 완료!")

    except Exception as e:
        logger.error(f"❌ 메인 데모 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
