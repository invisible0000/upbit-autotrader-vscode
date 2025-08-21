#!/usr/bin/env python3
"""
스마트 라우터 안정성 테스트
- 연속 실행으로 리소스 누수 및 WebSocket 안정성 검증
- 단계별 검증으로 문제점 조기 발견
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


class StabilityTester:
    """안정성 테스트"""

    def __init__(self, test_id: int):
        self.test_id = test_id
        self.logger = create_component_logger(f"StabilityTest-{test_id}")

    async def run_single_test(self) -> bool:
        """단일 테스트 실행"""
        rest_provider = None
        websocket_provider = None

        try:
            # Provider들 생성
            rest_provider = UpbitRestProvider()
            websocket_provider = UpbitWebSocketProvider()

            # SmartDataRouter 초기화
            smart_router = SmartDataRouter(
                rest_provider=rest_provider,
                websocket_provider=websocket_provider
            )

            # 티커 테스트
            symbol = TradingSymbol.from_upbit_symbol("KRW-BTC")
            ticker_response = await smart_router.get_ticker_data(symbol)

            if not ticker_response or not ticker_response.data:
                self.logger.error("티커 데이터 실패")
                return False

            # 캔들 테스트
            candle_response = await smart_router.get_candle_data(
                symbol=symbol,
                timeframe=Timeframe.MINUTE_1,
                count=1
            )

            if not candle_response or not candle_response.data:
                self.logger.error("캔들 데이터 실패")
                return False

            price = ticker_response.data.current_price
            candle_price = candle_response.data[0].close_price

            self.logger.info(f"✅ 테스트 {self.test_id}: BTC = {price:,} / 캔들 = {candle_price:,}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 테스트 {self.test_id} 실패: {e}")
            return False
        finally:
            # 리소스 정리
            try:
                if rest_provider and hasattr(rest_provider, 'close'):
                    await rest_provider.close()
                if websocket_provider and hasattr(websocket_provider, 'disconnect'):
                    await websocket_provider.disconnect()
            except Exception as e:
                self.logger.error(f"정리 오류: {e}")


async def main():
    """메인 안정성 테스트"""
    print("🔧 스마트 라우터 안정성 테스트 시작")
    print("=" * 50)

    test_count = 5
    success_count = 0

    for i in range(1, test_count + 1):
        print(f"\n🧪 테스트 {i}/{test_count} 실행 중...")

        tester = StabilityTester(i)
        start_time = time.time()

        success = await tester.run_single_test()
        duration = (time.time() - start_time) * 1000

        if success:
            success_count += 1
            print(f"✅ 성공 ({duration:.1f}ms)")
        else:
            print(f"❌ 실패 ({duration:.1f}ms)")

        # 테스트 간 잠시 대기 (리소스 완전 해제 대기)
        if i < test_count:
            await asyncio.sleep(1.0)

    print("\n" + "=" * 50)
    print(f"📊 안정성 테스트 결과: {success_count}/{test_count} 성공")

    if success_count == test_count:
        print("🎉 모든 테스트 성공 - 시스템 안정성 확인!")
    else:
        print("⚠️  일부 실패 - 안정성 문제 가능성")

    return success_count == test_count


if __name__ == "__main__":
    asyncio.run(main())
