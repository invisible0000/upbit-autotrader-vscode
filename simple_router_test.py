#!/usr/bin/env python3
"""
스마트 라우터 단일 기능 테스트

로그를 최소화하고 핵심 기능만 테스트합니다.
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


class SimpleRouterTester:
    """간단한 스마트 라우터 테스트"""

    def __init__(self):
        self.logger = create_component_logger("SimpleTest")

        # Provider들 생성
        self.rest_provider = UpbitRestProvider()
        self.websocket_provider = UpbitWebSocketProvider()

        # SmartDataRouter 초기화
        self.smart_router = SmartDataRouter(
            rest_provider=self.rest_provider,
            websocket_provider=self.websocket_provider
        )

    async def test_ticker_data(self) -> bool:
        """티커 데이터 테스트"""
        try:
            symbol = TradingSymbol.from_upbit_symbol("KRW-BTC")
            response = await self.smart_router.get_ticker_data(symbol)

            if response and response.data:
                price = response.data.current_price
                self.logger.info(f"✅ 티커 테스트 성공: BTC = {price:,} KRW")
                return True
            else:
                self.logger.error("❌ 티커 데이터 없음")
                return False

        except Exception as e:
            self.logger.error(f"❌ 티커 테스트 실패: {e}")
            return False

    async def test_candle_data(self) -> bool:
        """캔들 데이터 테스트"""
        try:
            symbol = TradingSymbol.from_upbit_symbol("KRW-BTC")
            response = await self.smart_router.get_candle_data(
                symbol=symbol,
                timeframe=Timeframe.MINUTE_1,
                count=1
            )

            if response and response.data:
                candle = response.data[0]
                close_price = candle.close_price  # close가 아니라 close_price
                self.logger.info(f"✅ 캔들 테스트 성공: 1분봉 종가 = {close_price:,} KRW")
                self.logger.info(f"📊 데이터 소스: {response.metadata.data_source}")
                return True
            else:
                self.logger.error("❌ 캔들 데이터 없음")
                return False

        except Exception as e:
            self.logger.error(f"❌ 캔들 테스트 실패: {e}")
            return False

    async def test_routing_logic(self) -> bool:
        """라우팅 로직 테스트"""
        try:
            # 라우팅 통계 확인
            stats = await self.smart_router.get_routing_stats()
            self.logger.info("📊 라우팅 통계:")
            self.logger.info(f"   총 요청: {stats.total_requests}")
            self.logger.info(f"   REST 요청: {stats.rest_requests}")
            self.logger.info(f"   WebSocket 요청: {stats.websocket_requests}")
            self.logger.info(f"   에러율: {stats.error_rate:.1f}%")
            return True

        except Exception as e:
            self.logger.error(f"❌ 라우팅 통계 실패: {e}")
            return False

    async def cleanup(self):
        """리소스 정리"""
        try:
            # 🔧 aiohttp 세션 정리
            if hasattr(self.rest_provider, 'close'):
                await self.rest_provider.close()
                self.logger.info("🧹 REST Provider 세션 정리 완료")

            # 🔧 WebSocket 연결 정리
            if hasattr(self.websocket_provider, 'disconnect'):
                await self.websocket_provider.disconnect()
                self.logger.info("🧹 WebSocket Provider 연결 정리 완료")

            self.logger.info("🧹 모든 리소스 정리 완료")
        except Exception as e:
            self.logger.error(f"❌ 정리 실패: {e}")


async def main():
    """메인 테스트 실행"""
    tester = SimpleRouterTester()

    print("🚀 스마트 라우터 단순 기능 테스트 시작")
    print("=" * 50)

    tests = [
        ("1️⃣ 티커 데이터", tester.test_ticker_data),
        ("2️⃣ 캔들 데이터", tester.test_candle_data),
        ("3️⃣ 라우팅 로직", tester.test_routing_logic),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name} 테스트 중...")
        start_time = time.time()

        success = await test_func()
        duration = (time.time() - start_time) * 1000

        status = "✅ 성공" if success else "❌ 실패"
        print(f"{status} ({duration:.1f}ms)")
        results.append(success)

    # 정리
    await tester.cleanup()

    # 결과 요약
    success_count = sum(results)
    total_count = len(results)

    print("\n" + "=" * 50)
    print(f"📊 테스트 결과: {success_count}/{total_count} 성공")

    if success_count == total_count:
        print("🎉 모든 테스트 통과!")
    else:
        print("⚠️  일부 테스트 실패 - 문제점 확인 필요")

    return success_count == total_count


if __name__ == "__main__":
    asyncio.run(main())
