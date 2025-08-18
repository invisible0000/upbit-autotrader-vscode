"""
업비트 WebSocket 실용 예제 - API 키 없이 스크리너/백테스팅 완벽 지원
"""

import asyncio
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
    UpbitWebSocketQuotationClient,
    WebSocketDataType
)


async def simple_screener_example():
    """간단한 스크리너: 실시간 가격 변화 모니터링"""
    print("📊 간단한 스크리너 예제 (API 키 불필요)")
    print("=" * 50)

    async with UpbitWebSocketQuotationClient() as client:
        # 원하는 코인들 구독
        await client.subscribe_ticker(["KRW-BTC", "KRW-ETH", "KRW-ADA"])

        message_count = 0
        async for message in client.listen():
            if message.type == WebSocketDataType.TICKER:
                symbol = message.market
                price = message.data.get('trade_price', 0)
                change_rate = message.data.get('signed_change_rate', 0) * 100

                print(f"{symbol}: {price:,}원 ({change_rate:+.2f}%)")

                message_count += 1
                if message_count >= 10:  # 10개 메시지만 확인
                    break

    print("✅ 스크리너 예제 완료\n")


async def backtesting_data_collection():
    """백테스팅용 데이터 수집"""
    print("📈 백테스팅 데이터 수집 예제")
    print("=" * 50)

    async with UpbitWebSocketQuotationClient() as client:
        # Ticker와 Trade 데이터 동시 수집
        await client.subscribe_ticker(["KRW-BTC"])
        await client.subscribe_trade(["KRW-BTC"])

        collected_data = []

        async for message in client.listen():
            data_point = {
                'type': message.type.value,
                'timestamp': message.timestamp,
                'market': message.market,
                'price': message.data.get('trade_price', 0)
            }

            # Trade 데이터의 경우 추가 정보 포함
            if message.type == WebSocketDataType.TRADE:
                data_point['volume'] = message.data.get('trade_volume', 0)
                data_point['ask_bid'] = message.data.get('ask_bid', '')

            collected_data.append(data_point)
            print(f"{data_point['type']}: {data_point['price']:,}원")

            if len(collected_data) >= 8:
                break

        print(f"\n✅ 수집 완료: {len(collected_data)}개 데이터")
        print("   - 백테스팅/분석에 활용 가능")
        print()


async def multiplier_ready_example():
    """multiplier 기능 연동 준비 예제"""
    print("🎯 Multiplier 기능 연동 준비")
    print("=" * 50)

    async with UpbitWebSocketQuotationClient() as client:
        await client.subscribe_ticker(["KRW-BTC"])

        async for message in client.listen():
            if message.type == WebSocketDataType.TICKER:
                current_price = message.data.get('trade_price', 0)
                daily_high = message.data.get('high_price', 0)
                daily_low = message.data.get('low_price', 0)

                # multiplier 계산 (실제 구현에서 사용할 로직)
                high_multiplier = current_price / daily_high if daily_high > 0 else 0
                low_multiplier = current_price / daily_low if daily_low > 0 else 0

                print(f"현재가: {current_price:,}원")
                print(f"HIGH 배수: {high_multiplier:.4f}")
                print(f"LOW 배수: {low_multiplier:.4f}")
                print("-" * 30)

                # 3번만 확인
                break

    print("✅ Multiplier 준비 완료\n")


async def main():
    """핵심 사용 예제들"""
    print("🚀 업비트 WebSocket - 핵심 사용법")
    print("🔑 API 키 없이도 완벽 동작!")
    print("=" * 80)

    # 실용적인 예제들
    await simple_screener_example()
    await backtesting_data_collection()
    await multiplier_ready_example()

    print("=" * 80)
    print("🎉 모든 예제 완료!")
    print("💡 이제 multiplier 기능에서 이 WebSocket 클라이언트를 활용하세요!")


if __name__ == "__main__":
    asyncio.run(main())
