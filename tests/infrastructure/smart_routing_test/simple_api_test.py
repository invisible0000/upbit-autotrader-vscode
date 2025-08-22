"""
스마트 라우터 V2.0 간단한 실제 API 테스트

설정 파일 없이 간단하게 실제 API 연동을 테스트합니다.
"""

import asyncio
import os

# 로깅 환경 설정
os.environ["UPBIT_CONSOLE_OUTPUT"] = "true"
os.environ["UPBIT_LOG_SCOPE"] = "normal"
os.environ["UPBIT_COMPONENT_FOCUS"] = "SmartRouter"

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.smart_router import (
    SmartRouter, get_smart_router, initialize_smart_router
)
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.models import (
    DataRequest, DataType, RealtimePriority
)

logger = create_component_logger("SmartRouterSimpleTest")


async def test_simple_ticker():
    """간단한 현재가 테스트"""
    logger.info("=== 간단한 현재가 테스트 시작 ===")

    try:
        # 스마트 라우터 초기화
        router = get_smart_router()
        await router.initialize()

        # 현재가 요청
        result = await router.get_ticker(["KRW-BTC"])

        logger.info(f"테스트 결과: {result}")
        logger.info(f"성공 여부: {result.get('success', False)}")

        if result.get("success"):
            logger.info(f"메타데이터: {result.get('metadata', {})}")
            logger.info(f"데이터 타입: {type(result.get('data', {}))}")
            logger.info(f"데이터 샘플: {str(result.get('data', {}))[:300]}...")
        else:
            logger.error(f"에러 메시지: {result.get('error', 'Unknown error')}")

        # 성능 요약
        summary = router.get_performance_summary()
        logger.info(f"성능 요약: {summary}")

        return result

    except Exception as e:
        logger.error(f"테스트 실행 실패: {e}")
        return {"success": False, "error": str(e)}
    finally:
        # 정리
        if router.websocket_client and router.websocket_client.is_connected:
            await router.websocket_client.disconnect()


async def test_simple_candles():
    """간단한 캔들 테스트"""
    logger.info("=== 간단한 캔들 테스트 시작 ===")

    try:
        # 스마트 라우터 초기화
        router = get_smart_router()
        await router.initialize()

        # 캔들 요청
        result = await router.get_candles(["KRW-BTC"], "1m", 5)

        logger.info(f"캔들 테스트 결과: {result.get('success', False)}")

        if result.get("success"):
            logger.info(f"메타데이터: {result.get('metadata', {})}")
            logger.info(f"데이터 타입: {type(result.get('data', {}))}")

            data = result.get('data', {})
            if isinstance(data, list):
                logger.info(f"캔들 개수: {len(data)}")
                if len(data) > 0:
                    logger.info(f"첫 번째 캔들: {data[0]}")
            elif isinstance(data, dict):
                logger.info(f"데이터 구조: {list(data.keys()) if data else 'Empty dict'}")
        else:
            logger.error(f"캔들 테스트 에러: {result.get('error', 'Unknown error')}")

        return result

    except Exception as e:
        logger.error(f"캔들 테스트 실행 실패: {e}")
        return {"success": False, "error": str(e)}
    finally:
        # 정리
        if router.websocket_client and router.websocket_client.is_connected:
            await router.websocket_client.disconnect()


async def main():
    """메인 테스트 함수"""
    logger.info("🚀 스마트 라우터 간단한 실제 API 테스트 시작")

    # 현재가 테스트
    ticker_result = await test_simple_ticker()

    # 잠시 대기
    await asyncio.sleep(1)

    # 캔들 테스트
    candles_result = await test_simple_candles()

    logger.info("✅ 스마트 라우터 간단한 실제 API 테스트 완료")

    return {
        "ticker_success": ticker_result.get("success", False),
        "candles_success": candles_result.get("success", False)
    }


if __name__ == "__main__":
    results = asyncio.run(main())
    print(f"\n최종 결과: {results}")
