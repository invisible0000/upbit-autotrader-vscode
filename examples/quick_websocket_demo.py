"""
빠른 WebSocket 데모 - 10초 내 완료
"""

import asyncio
import time
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
    UpbitWebSocketQuotationClient,
    WebSocketDataType
)


async def quick_demo():
    """10초 제한 빠른 WebSocket 데모"""
    print("🚀 빠른 WebSocket 데모 시작 (10초 제한)")
    print("=" * 50)

    start_time = time.time()
    message_count = 0

    async with UpbitWebSocketQuotationClient() as client:
        await client.subscribe_ticker(["KRW-BTC"])

        async for message in client.listen():
            if message.type == WebSocketDataType.TICKER:
                message_count += 1
                price = message.data.get('trade_price', 0)
                change_rate = message.data.get('signed_change_rate', 0) * 100

                print(f"📊 {message_count}. BTC: {price:,}원 ({change_rate:+.2f}%)")

                # 10초 또는 10개 메시지 후 자동 종료
                elapsed = time.time() - start_time
                if elapsed >= 10 or message_count >= 10:
                    print(f"\n✅ 데모 완료: {message_count}개 메시지, {elapsed:.1f}초")
                    break


if __name__ == "__main__":
    asyncio.run(quick_demo())
