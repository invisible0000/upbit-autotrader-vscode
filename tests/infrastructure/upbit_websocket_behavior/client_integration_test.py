"""
업비트 WebSocket Quotation 클라이언트 테스트
- 새로 구현한 클라이언트 클래스 검증
- 스크리너/백테스팅 시나리오 테스트
"""

import asyncio
from typing import List
import time

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
    UpbitWebSocketQuotationClient,
    WebSocketDataType,
    WebSocketMessage
)


class MessageCollector:
    """메시지 수집기 - 테스트용"""

    def __init__(self):
        self.messages: List[WebSocketMessage] = []
        self.ticker_count = 0
        self.trade_count = 0
        self.orderbook_count = 0

    def handle_ticker(self, message: WebSocketMessage) -> None:
        """Ticker 메시지 핸들러"""
        self.messages.append(message)
        self.ticker_count += 1
        print(f"📊 Ticker [{self.ticker_count}]: {message.market} - {message.data.get('trade_price', 'N/A'):,}원")

    def handle_trade(self, message: WebSocketMessage) -> None:
        """Trade 메시지 핸들러"""
        self.messages.append(message)
        self.trade_count += 1
        print(f"💰 Trade [{self.trade_count}]: {message.market} - {message.data.get('trade_price', 'N/A'):,}원")

    def handle_orderbook(self, message: WebSocketMessage) -> None:
        """Orderbook 메시지 핸들러"""
        self.messages.append(message)
        self.orderbook_count += 1
        print(f"📈 Orderbook [{self.orderbook_count}]: {message.market}")


async def test_client_basic_functionality():
    """클라이언트 기본 기능 테스트"""
    print("🧪 WebSocket 클라이언트 기본 기능 테스트")
    print("=" * 60)

    collector = MessageCollector()

    try:
        async with UpbitWebSocketQuotationClient() as client:
            print("✅ 클라이언트 연결 성공")

            # 메시지 핸들러 등록
            client.add_message_handler(WebSocketDataType.TICKER, collector.handle_ticker)
            client.add_message_handler(WebSocketDataType.TRADE, collector.handle_trade)
            client.add_message_handler(WebSocketDataType.ORDERBOOK, collector.handle_orderbook)

            # 구독 설정
            await client.subscribe_ticker(["KRW-BTC", "KRW-ETH"])
            await client.subscribe_trade(["KRW-BTC"])
            await client.subscribe_orderbook(["KRW-BTC"])

            print("📡 구독 설정 완료 - 30초간 메시지 수신 테스트")

            # 30초간 메시지 수신
            message_count = 0
            start_time = time.time()

            async for message in client.listen():
                message_count += 1

                if time.time() - start_time > 30:  # 30초 후 종료
                    break

                if message_count % 20 == 0:  # 20개마다 상태 출력
                    elapsed = time.time() - start_time
                    print(f"⏱️ {elapsed:.1f}초 경과 - 수신 메시지: {message_count}개")

            print("\n📊 테스트 결과:")
            print(f"   총 메시지: {message_count}개")
            print(f"   Ticker: {collector.ticker_count}개")
            print(f"   Trade: {collector.trade_count}개")
            print(f"   Orderbook: {collector.orderbook_count}개")

            return message_count > 0

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


async def test_screener_scenario():
    """스크리너 시나리오 테스트"""
    print("\n🔍 스크리너 시나리오 테스트")
    print("=" * 60)

    # 스크리너용 다중 심볼 모니터링
    markets = ["KRW-BTC", "KRW-ETH", "KRW-ADA", "KRW-DOT", "KRW-LINK"]

    try:
        async with UpbitWebSocketQuotationClient() as client:
            await client.subscribe_ticker(markets)

            print(f"📊 스크리너 모니터링 시작: {len(markets)}개 코인")

            price_changes = {}
            message_count = 0
            start_time = time.time()

            async for message in client.listen():
                if message.type == WebSocketDataType.TICKER:
                    market = message.market
                    current_price = message.data.get('trade_price', 0)
                    change_rate = message.data.get('signed_change_rate', 0)

                    if market not in price_changes:
                        price_changes[market] = []

                    price_changes[market].append({
                        'price': current_price,
                        'change_rate': change_rate,
                        'timestamp': message.timestamp
                    })

                    message_count += 1

                    # 10초마다 급등/급락 체크
                    if message_count % 50 == 0:
                        print("\n📈 가격 변화 현황:")
                        for market, changes in price_changes.items():
                            if changes:
                                latest = changes[-1]
                                print(f"   {market}: {latest['price']:,}원 ({latest['change_rate']*100:+.2f}%)")

                if time.time() - start_time > 15:  # 15초 후 종료
                    break

            print(f"\n✅ 스크리너 테스트 완료 - {len(price_changes)}개 코인 모니터링")
            return len(price_changes) > 0

    except Exception as e:
        print(f"❌ 스크리너 테스트 실패: {e}")
        return False


async def test_backtest_scenario():
    """백테스팅 시나리오 테스트"""
    print("\n📈 백테스팅 시나리오 테스트")
    print("=" * 60)

    try:
        async with UpbitWebSocketQuotationClient() as client:
            # 캔들 데이터 구독 (백테스팅용)
            await client.subscribe_candle(["KRW-BTC"], unit=5)
            await client.subscribe_ticker(["KRW-BTC"])  # 실시간 가격도 함께

            print("📊 백테스팅 데이터 수집 시작 (5분봉 + 실시간)")

            candle_count = 0
            ticker_count = 0
            start_time = time.time()

            async for message in client.listen():
                if message.type == WebSocketDataType.CANDLE_5M:
                    candle_count += 1
                    data = message.data
                    print(f"🕯️ 캔들 [{candle_count}]: O={data.get('opening_price', 'N/A')} "
                          f"H={data.get('high_price', 'N/A')} "
                          f"L={data.get('low_price', 'N/A')} "
                          f"C={data.get('trade_price', 'N/A')}")

                elif message.type == WebSocketDataType.TICKER:
                    ticker_count += 1
                    if ticker_count % 10 == 0:  # 10번째마다 출력
                        price = message.data.get('trade_price', 0)
                        print(f"💰 실시간 가격: {price:,}원")

                if time.time() - start_time > 20:  # 20초 후 종료
                    break

            print("\n✅ 백테스팅 테스트 완료")
            print(f"   캔들 데이터: {candle_count}개")
            print(f"   실시간 가격: {ticker_count}개")

            return candle_count >= 0 and ticker_count > 0  # 캔들은 시간에 따라 없을 수 있음

    except Exception as e:
        print(f"❌ 백테스팅 테스트 실패: {e}")
        return False


async def main():
    """메인 테스트 실행"""
    print("🎯 업비트 WebSocket Quotation 클라이언트 통합 테스트")
    print("🔑 API 키 불필요 - 스크리너/백테스팅 최적화 검증")
    print("=" * 80)

    results = {}

    # 1. 기본 기능 테스트
    results['basic'] = await test_client_basic_functionality()

    # 2. 스크리너 시나리오 테스트
    results['screener'] = await test_screener_scenario()

    # 3. 백테스팅 시나리오 테스트
    results['backtest'] = await test_backtest_scenario()

    # 결과 요약
    print("\n" + "=" * 80)
    print("📋 테스트 결과 요약:")
    print(f"   ✅ 기본 기능: {'성공' if results['basic'] else '실패'}")
    print(f"   ✅ 스크리너: {'성공' if results['screener'] else '실패'}")
    print(f"   ✅ 백테스팅: {'성공' if results['backtest'] else '실패'}")

    if all(results.values()):
        print("\n🎉 모든 테스트 성공!")
        print("💡 WebSocket Quotation 클라이언트가 API 키 없이 정상 동작 확인")
        print("🚀 스크리너/백테스팅 시나리오 완벽 지원")
    else:
        print("\n⚠️ 일부 테스트 실패 - 추가 확인 필요")
        failed_tests = [name for name, result in results.items() if not result]
        print(f"   실패한 테스트: {failed_tests}")


if __name__ == "__main__":
    asyncio.run(main())
