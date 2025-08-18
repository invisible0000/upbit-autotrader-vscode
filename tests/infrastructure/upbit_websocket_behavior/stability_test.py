"""
업비트 WebSocket 안정성 테스트
- 타임아웃과 예외 처리 강화
- 단계별 검증으로 안정성 확보
"""

import asyncio
import time
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
    UpbitWebSocketQuotationClient
)


async def test_basic_stability():
    """기본 안정성 테스트 - 타임아웃 포함"""
    print("🛡️ 기본 안정성 테스트")
    print("=" * 60)

    try:
        client = UpbitWebSocketQuotationClient()

        # 1. 연결 테스트
        print("🔗 1단계: 연결 테스트")
        if not await client.connect():
            print("❌ 연결 실패")
            return False
        print("✅ 연결 성공")

        # 2. 구독 테스트
        print("📡 2단계: 구독 테스트")
        if not await client.subscribe_ticker(["KRW-BTC"]):
            print("❌ 구독 실패")
            return False
        print("✅ 구독 성공")

        # 3. 메시지 수신 테스트 (타임아웃 설정)
        print("📨 3단계: 메시지 수신 테스트 (10초 타임아웃)")
        message_count = 0
        start_time = time.time()

        try:
            async for message in client.listen():
                message_count += 1
                print(f"   📊 메시지 {message_count}: {message.market} - {message.data.get('trade_price', 'N/A'):,}원")

                # 타임아웃 체크
                if time.time() - start_time > 10:  # 10초 타임아웃
                    print("⏱️ 타임아웃 - 정상 종료")
                    break

                if message_count >= 5:  # 5개 메시지면 충분
                    print("✅ 충분한 메시지 수신")
                    break

        except asyncio.TimeoutError:
            print("⚠️ 메시지 수신 타임아웃")

        # 4. 연결 해제 테스트
        print("🔌 4단계: 연결 해제 테스트")
        await client.disconnect()
        print("✅ 연결 해제 완료")

        print(f"\n📊 안정성 테스트 결과: {message_count}개 메시지 수신")
        return message_count > 0

    except Exception as e:
        print(f"❌ 안정성 테스트 실패: {e}")
        return False


async def test_error_resilience():
    """에러 복원력 테스트 - 잘못된 요청에 대한 처리"""
    print("\n🚨 에러 복원력 테스트")
    print("=" * 60)

    try:
        client = UpbitWebSocketQuotationClient()

        # 연결
        await client.connect()
        print("✅ 연결 성공")

        # 1. 정상 구독
        print("📡 정상 구독 테스트")
        await client.subscribe_ticker(["KRW-BTC"])
        print("✅ 정상 구독 완료")

        # 2. 잘못된 구독 시도 (클라이언트 레벨에서 차단)
        print("🚫 잘못된 구독 시도")
        try:
            result = await client.subscribe_candle(["KRW-INVALID"], unit=999)
            if not result:
                print("✅ 클라이언트에서 잘못된 요청 차단")
        except Exception as e:
            print(f"✅ 예외 처리됨: {e}")

        # 3. 정상 메시지 수신 확인 (타임아웃 설정)
        print("📨 정상 메시지 수신 확인")
        message_count = 0
        start_time = time.time()

        async for message in client.listen():
            message_count += 1
            print(f"   📊 정상 메시지: {message.market}")

            if time.time() - start_time > 5 or message_count >= 3:
                break

        await client.disconnect()
        print(f"✅ 에러 복원력 테스트 완료: {message_count}개 정상 메시지")
        return message_count > 0

    except Exception as e:
        print(f"❌ 에러 복원력 테스트 실패: {e}")
        return False


async def test_multi_symbol_performance():
    """다중 심볼 성능 테스트"""
    print("\n⚡ 다중 심볼 성능 테스트")
    print("=" * 60)

    symbols = ["KRW-BTC", "KRW-ETH", "KRW-ADA"]

    try:
        async with UpbitWebSocketQuotationClient() as client:
            print(f"📡 {len(symbols)}개 심볼 구독")
            await client.subscribe_ticker(symbols)

            # 심볼별 메시지 카운트
            symbol_counts = {}
            total_messages = 0
            start_time = time.time()

            async for message in client.listen():
                total_messages += 1
                symbol = message.market

                if symbol not in symbol_counts:
                    symbol_counts[symbol] = 0
                symbol_counts[symbol] += 1

                # 진행 상황 출력
                if total_messages % 10 == 0:
                    elapsed = time.time() - start_time
                    print(f"   📊 {elapsed:.1f}초: {total_messages}개 메시지")

                # 테스트 종료 조건
                if time.time() - start_time > 15 or total_messages >= 30:
                    break

            print(f"\n📊 다중 심볼 성능 결과:")
            print(f"   총 메시지: {total_messages}개")
            for symbol, count in symbol_counts.items():
                print(f"   {symbol}: {count}개")

            return len(symbol_counts) >= 2  # 최소 2개 심볼에서 메시지 수신

    except Exception as e:
        print(f"❌ 다중 심볼 테스트 실패: {e}")
        return False


async def test_reconnection_stability():
    """재연결 안정성 테스트"""
    print("\n🔄 재연결 안정성 테스트")
    print("=" * 60)

    try:
        client = UpbitWebSocketQuotationClient()

        # 첫 번째 연결
        print("🔗 첫 번째 연결")
        await client.connect()
        await client.subscribe_ticker(["KRW-BTC"])

        # 짧은 메시지 수신
        count1 = 0
        async for message in client.listen():
            count1 += 1
            if count1 >= 3:
                break
        print(f"✅ 첫 번째 세션: {count1}개 메시지")

        # 연결 해제
        await client.disconnect()
        print("🔌 연결 해제")

        # 짧은 대기
        await asyncio.sleep(1)

        # 재연결
        print("🔗 재연결 시도")
        await client.connect()
        await client.subscribe_ticker(["KRW-BTC"])

        # 두 번째 메시지 수신
        count2 = 0
        start_time = time.time()
        async for message in client.listen():
            count2 += 1
            if count2 >= 3 or time.time() - start_time > 10:
                break
        print(f"✅ 두 번째 세션: {count2}개 메시지")

        await client.disconnect()

        print(f"📊 재연결 테스트 완료: {count1 + count2}개 총 메시지")
        return count1 > 0 and count2 > 0

    except Exception as e:
        print(f"❌ 재연결 테스트 실패: {e}")
        return False


async def main():
    """안정성 중심 메인 테스트"""
    print("🎯 WebSocket 클라이언트 안정성 검증")
    print("🛡️ 타임아웃, 에러 처리, 복원력 중심 테스트")
    print("=" * 80)

    results = {}

    # 1. 기본 안정성
    results['stability'] = await test_basic_stability()

    # 2. 에러 복원력
    results['error_resilience'] = await test_error_resilience()

    # 3. 다중 심볼 성능
    results['multi_symbol'] = await test_multi_symbol_performance()

    # 4. 재연결 안정성
    results['reconnection'] = await test_reconnection_stability()

    # 결과 요약
    print("\n" + "=" * 80)
    print("📋 안정성 검증 결과:")
    print(f"   🛡️ 기본 안정성: {'성공' if results['stability'] else '실패'}")
    print(f"   🚨 에러 복원력: {'성공' if results['error_resilience'] else '실패'}")
    print(f"   ⚡ 다중 심볼: {'성공' if results['multi_symbol'] else '실패'}")
    print(f"   🔄 재연결: {'성공' if results['reconnection'] else '실패'}")

    success_count = sum(results.values())
    total_count = len(results)

    if success_count == total_count:
        print(f"\n🎉 모든 안정성 테스트 성공! ({success_count}/{total_count})")
        print("💡 WebSocket 클라이언트가 프로덕션 환경에서 안정적으로 동작 가능")
    else:
        print(f"\n⚠️ 일부 테스트 실패 ({success_count}/{total_count})")
        failed_tests = [name for name, result in results.items() if not result]
        print(f"   실패한 테스트: {failed_tests}")


if __name__ == "__main__":
    asyncio.run(main())
