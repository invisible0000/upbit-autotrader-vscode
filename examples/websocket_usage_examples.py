"""
업비트 WebSocket Quotation 클라이언트 사용 예제
API 키 없이 스크리너/백테스팅에서 실시간 데이터 활용
"""

import asyncio
import time
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
    UpbitWebSocketQuotationClient,
    WebSocketDataType
)


# 예제 1: 스크리너용 실시간 가격 모니터링 (30초 자동 정지)
async def example_screener():
    """스크리너: 여러 코인의 실시간 가격 변화 모니터링"""
    print("📊 스크리너 예제: 실시간 가격 모니터링 (30초 자동 정지)")
    print("=" * 60)

    # 모니터링할 코인들
    symbols = ["KRW-BTC", "KRW-ETH", "KRW-ADA", "KRW-DOT"]

    async with UpbitWebSocketQuotationClient() as client:
        # Ticker 구독 (실시간 가격)
        await client.subscribe_ticker(symbols)

        price_tracker = {}
        message_count = 0
        start_time = time.time()

        async for message in client.listen():
            if message.type == WebSocketDataType.TICKER:
                symbol = message.market
                current_price = message.data.get('trade_price', 0)
                message_count += 1
                change_rate = message.data.get('signed_change_rate', 0) * 100

                # 가격 변화 추적
                if symbol not in price_tracker:
                    price_tracker[symbol] = current_price
                    print(f"🟢 {symbol}: {current_price:,}원 ({change_rate:+.2f}%)")
                else:
                    prev_price = price_tracker[symbol]
                    if current_price != prev_price:
                        direction = "🔵" if current_price > prev_price else "🔴"
                        print(f"{direction} {symbol}: {prev_price:,} → {current_price:,}원 ({change_rate:+.2f}%)")
                        price_tracker[symbol] = current_price

                # 30초 또는 30개 메시지 후 자동 정지
                elapsed_time = time.time() - start_time
                if elapsed_time >= 30 or message_count >= 30:
                    print(f"\n✅ 스크리너 완료: {message_count}개 메시지, {elapsed_time:.1f}초 경과")
                    break


# 예제 2: 백테스팅용 실시간 데이터 수집 (시간 제한)
async def example_backtesting():
    """백테스팅: 실시간 ticker + trade 데이터 수집 (20초 제한)"""
    print("\n📈 백테스팅 예제: 실시간 데이터 수집 (20초 제한)")
    print("=" * 60)

    async with UpbitWebSocketQuotationClient() as client:
        # Ticker와 Trade 동시 구독
        await client.subscribe_ticker(["KRW-BTC"])
        await client.subscribe_trade(["KRW-BTC"])

        data_buffer = {
            'ticker': [],
            'trade': []
        }
        start_time = time.time()

        async for message in client.listen():
            if message.type == WebSocketDataType.TICKER:
                ticker_data = {
                    'timestamp': message.timestamp,
                    'price': message.data.get('trade_price'),
                    'volume': message.data.get('acc_trade_volume_24h'),
                    'change_rate': message.data.get('signed_change_rate')
                }
                data_buffer['ticker'].append(ticker_data)
                print(f"📊 Ticker: {ticker_data['price']:,}원")

            elif message.type == WebSocketDataType.TRADE:
                trade_data = {
                    'timestamp': message.timestamp,
                    'price': message.data.get('trade_price'),
                    'volume': message.data.get('trade_volume'),
                    'ask_bid': message.data.get('ask_bid')
                }
                data_buffer['trade'].append(trade_data)
                print(f"💰 Trade: {trade_data['price']:,}원 ({trade_data['ask_bid']})")

            # 20초 또는 20개 데이터 후 종료
            elapsed_time = time.time() - start_time
            total_data = len(data_buffer['ticker']) + len(data_buffer['trade'])
            if elapsed_time >= 20 or total_data >= 20:
                print(f"\n✅ 데이터 수집 완료: {elapsed_time:.1f}초 경과")
                break

        print("\n📊 수집된 데이터:")
        print(f"   Ticker: {len(data_buffer['ticker'])}개")
        print(f"   Trade: {len(data_buffer['trade'])}개")


# 예제 3: multiplier 기능 연동용 실시간 HIGH/LOW 추적 (15초)
async def example_multiplier_integration():
    """multiplier 기능: 실시간 HIGH/LOW 추적 (15초 제한)"""
    print("\n🎯 Multiplier 연동 예제: HIGH/LOW 실시간 추적 (15초 제한)")
    print("=" * 60)

    async with UpbitWebSocketQuotationClient() as client:
        await client.subscribe_ticker(["KRW-BTC"])

        high_low_tracker = {
            'daily_high': 0,
            'daily_low': float('inf'),
            'current_high': 0,
            'current_low': float('inf')
        }
        start_time = time.time()
        update_count = 0

        async for message in client.listen():
            if message.type == WebSocketDataType.TICKER:
                data = message.data
                current_price = data.get('trade_price', 0)
                daily_high = data.get('high_price', 0)
                daily_low = data.get('low_price', 0)
                update_count += 1

                # HIGH/LOW 업데이트
                high_low_tracker['daily_high'] = daily_high
                high_low_tracker['daily_low'] = daily_low

                # 현재 세션 HIGH/LOW 추적
                if current_price > high_low_tracker['current_high']:
                    high_low_tracker['current_high'] = current_price
                    print(f"🔥 신규 HIGH: {current_price:,}원")

                if current_price < high_low_tracker['current_low']:
                    high_low_tracker['current_low'] = current_price
                    print(f"❄️ 신규 LOW: {current_price:,}원")

                # multiplier 계산 예시
                high_multiplier = current_price / daily_high if daily_high > 0 else 0
                low_multiplier = current_price / daily_low if daily_low > 0 else 0

                print(f"📊 현재가: {current_price:,}원")
                print(f"   HIGH Multiplier: {high_multiplier:.4f}")
                print(f"   LOW Multiplier: {low_multiplier:.4f}")
                print("-" * 40)

                # 15초 또는 10번 업데이트 후 종료
                elapsed_time = time.time() - start_time
                if elapsed_time >= 15 or update_count >= 10:
                    print(f"\n✅ Multiplier 추적 완료: {update_count}번 업데이트, {elapsed_time:.1f}초 경과")
                    break


# 예제 4: 에러 처리 및 재연결 데모 (10초)
async def example_error_handling():
    """에러 처리: 안정적인 연결 관리 (10초 제한)"""
    print("\n🛡️ 에러 처리 예제: 안정적인 연결 관리 (10초 제한)")
    print("=" * 60)

    client = UpbitWebSocketQuotationClient()
    start_time = time.time()

    try:
        # 연결 시도
        if await client.connect():
            print("✅ 연결 성공")

            # 구독 시도
            if await client.subscribe_ticker(["KRW-BTC"]):
                print("✅ 구독 성공")

                # 메시지 수신 (타임아웃 적용)
                message_count = 0
                async for message in client.listen():
                    message_count += 1
                    print(f"📨 메시지 {message_count}: {message.market}")

                    # 10초 또는 5개 메시지 후 종료
                    elapsed_time = time.time() - start_time
                    if elapsed_time >= 10 or message_count >= 5:
                        print(f"✅ {message_count}개 메시지 수신 완료 ({elapsed_time:.1f}초)")
                        break
            else:
                print("❌ 구독 실패")
        else:
            print("❌ 연결 실패")

    except Exception as e:
        print(f"❌ 예외 발생: {e}")
    finally:
        # 안전한 연결 해제
        await client.disconnect()
        print("✅ 연결 정리 완료")


# 예제 5: 차트 뷰용 실시간 데이터 수집 (사용자 아키텍처 시나리오)
async def example_chart_view_scenario():
    """차트 뷰 시나리오: 200개 캔들 + 실시간 업데이트 (15초)"""
    print("\n📊 차트 뷰 시나리오: 실시간 차트 업데이트 (15초 제한)")
    print("=" * 60)

    async with UpbitWebSocketQuotationClient() as client:
        await client.subscribe_ticker(["KRW-BTC"])

        chart_data = {
            'last_price': 0,
            'price_updates': [],
            'volume_updates': []
        }
        start_time = time.time()
        update_count = 0

        async for message in client.listen():
            if message.type == WebSocketDataType.TICKER:
                data = message.data
                current_price = data.get('trade_price', 0)
                volume_24h = data.get('acc_trade_volume_24h', 0)
                update_count += 1

                # 차트 업데이트 시뮬레이션
                if chart_data['last_price'] != current_price:
                    chart_data['last_price'] = current_price
                    chart_data['price_updates'].append({
                        'timestamp': message.timestamp,
                        'price': current_price
                    })
                    print(f"📈 차트 업데이트: {current_price:,}원")

                chart_data['volume_updates'].append({
                    'timestamp': message.timestamp,
                    'volume': volume_24h
                })

                # 15초 또는 10번 업데이트 후 종료
                elapsed_time = time.time() - start_time
                if elapsed_time >= 15 or update_count >= 10:
                    print(f"\n✅ 차트 뷰 완료: {len(chart_data['price_updates'])}개 가격 업데이트")
                    print(f"   총 {update_count}번 업데이트, {elapsed_time:.1f}초 경과")
                    break


async def main():
    """모든 사용 예제 실행 (총 90초 이내 완료)"""
    print("🎯 업비트 WebSocket Quotation 클라이언트 사용 예제")
    print("🔑 API 키 불필요 - 스크리너/백테스팅/Multiplier 완벽 지원")
    print("⏰ 각 예제는 자동으로 시간 제한됩니다")
    print("=" * 80)

    main_start = time.time()

    # 각 예제를 순차적으로 실행 (시간 제한)
    await example_screener()  # 30초
    await example_backtesting()  # 20초
    await example_multiplier_integration()  # 15초
    await example_error_handling()  # 10초
    await example_chart_view_scenario()  # 15초

    total_elapsed = time.time() - main_start

    print("\n" + "=" * 80)
    print("🎉 모든 사용 예제 완료!")
    print(f"⏰ 총 실행 시간: {total_elapsed:.1f}초")
    print("💡 이제 multiplier 기능에서 실시간 WebSocket 데이터를 활용할 수 있습니다.")
    print("\n🏗️ 다음 단계: UI 통합 테스트")
    print("   python run_desktop_ui.py → 전략 관리 → 트리거 빌더")


if __name__ == "__main__":
    asyncio.run(main())
