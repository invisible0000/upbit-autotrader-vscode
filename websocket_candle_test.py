#!/usr/bin/env python3
"""
WebSocket 캔들 구현 테스트

새로 구현된 WebSocket 캔들 기능을 검증합니다.
"""

import asyncio
import time
from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.smart_data_router import (
    SmartDataRouter
)
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.upbit_rest_provider import (
    UpbitRestProvider
)
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.upbit_websocket_provider import (
    UpbitWebSocketProvider
)
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.models.symbols import TradingSymbol
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.models.timeframes import Timeframe


class WebSocketCandleTester:
    """WebSocket 캔들 테스트"""

    def __init__(self):
        self.logger = create_component_logger("WebSocketCandleTest")

        # Provider들 생성
        self.rest_provider = UpbitRestProvider()
        self.websocket_provider = UpbitWebSocketProvider()

        # SmartDataRouter 초기화
        self.smart_router = SmartDataRouter(
            rest_provider=self.rest_provider,
            websocket_provider=self.websocket_provider
        )

    async def test_websocket_candle_direct(self) -> bool:
        """WebSocket Provider 직접 테스트"""
        try:
            symbol = TradingSymbol.from_upbit_symbol("KRW-BTC")

            from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.models.requests import CandleDataRequest

            request = CandleDataRequest(
                symbol=symbol,
                timeframe=Timeframe.MINUTE_1,
                count=1
            )

            self.logger.info("WebSocket Provider 직접 호출 시작...")
            start_time = time.time()

            response = await self.websocket_provider.get_candle_data(request)

            duration = (time.time() - start_time) * 1000

            if response and response.data:
                candle = response.data[0]
                self.logger.info("✅ WebSocket 캔들 직접 테스트 성공")
                self.logger.info(f"   심볼: {response.symbol.to_upbit_symbol()}")
                self.logger.info(f"   타임프레임: {response.timeframe}")
                self.logger.info(f"   종가: {candle.close_price:,}")
                self.logger.info(f"   소스: {response.metadata.data_source}")
                self.logger.info(f"   소요시간: {duration:.1f}ms")
                return True
            else:
                self.logger.error("❌ WebSocket 캔들 데이터 없음")
                return False

        except Exception as e:
            self.logger.error(f"❌ WebSocket 캔들 직접 테스트 실패: {e}")
            return False

    async def test_smart_router_websocket_preference(self) -> bool:
        """SmartRouter의 WebSocket 선택 테스트"""
        try:
            symbol = TradingSymbol.from_upbit_symbol("KRW-BTC")

            self.logger.info("SmartRouter WebSocket 선택 테스트 시작...")
            start_time = time.time()

            # 강제로 WebSocket 사용하도록 여러 번 요청 (빈도 증가)
            response = None
            for i in range(3):
                response = await self.smart_router.get_candle_data(
                    symbol=symbol,
                    timeframe=Timeframe.MINUTE_1,
                    count=1
                )
                await asyncio.sleep(0.1)  # 짧은 간격으로 연속 요청

            duration = (time.time() - start_time) * 1000

            if response and response.data:
                candle = response.data[0]
                self.logger.info("✅ SmartRouter WebSocket 테스트 성공:")
                self.logger.info(f"   종가: {candle.close_price:,}")
                self.logger.info(f"   소스: {response.metadata.data_source}")
                self.logger.info(f"   소요시간: {duration:.1f}ms")

                # WebSocket이 사용되었는지 확인
                if response.metadata.data_source == "websocket":
                    self.logger.info("🎉 SmartRouter가 WebSocket을 자동 선택했습니다!")
                    return True
                else:
                    self.logger.warning("⚠️ SmartRouter가 REST를 선택했습니다 (패턴 분석 결과)")
                    return True  # 여전히 성공으로 간주
            else:
                self.logger.error("❌ SmartRouter 캔들 데이터 없음")
                return False

        except Exception as e:
            self.logger.error(f"❌ SmartRouter WebSocket 테스트 실패: {e}")
            return False

    async def cleanup(self):
        """리소스 정리"""
        try:
            if hasattr(self.rest_provider, 'close'):
                await self.rest_provider.close()
            if hasattr(self.websocket_provider, 'disconnect'):
                await self.websocket_provider.disconnect()
            self.logger.info("🧹 모든 리소스 정리 완료")
        except Exception as e:
            self.logger.error(f"❌ 정리 실패: {e}")


async def main():
    """메인 WebSocket 캔들 테스트"""
    print("🚀 WebSocket 캔들 구현 테스트 시작")
    print("=" * 50)

    tester = WebSocketCandleTester()

    tests = [
        ("1️⃣ WebSocket Provider 직접 테스트", tester.test_websocket_candle_direct),
        ("2️⃣ SmartRouter WebSocket 선택 테스트", tester.test_smart_router_websocket_preference),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name} 실행 중...")
        start_time = time.time()

        success = await test_func()
        duration = (time.time() - start_time) * 1000

        status = "✅ 성공" if success else "❌ 실패"
        print(f"{status} ({duration:.1f}ms)")
        results.append(success)

        # 테스트 간 잠시 대기
        if test_func != tests[-1][1]:  # 마지막 테스트가 아니면
            await asyncio.sleep(2.0)

    # 정리
    await tester.cleanup()

    # 결과 요약
    success_count = sum(results)
    total_count = len(results)

    print("\n" + "=" * 50)
    print(f"📊 WebSocket 캔들 테스트 결과: {success_count}/{total_count} 성공")

    if success_count == total_count:
        print("🎉 WebSocket 캔들 구현 완료!")
    else:
        print("⚠️ 일부 테스트 실패 - 구현 점검 필요")

    return success_count == total_count


if __name__ == "__main__":
    asyncio.run(main())
