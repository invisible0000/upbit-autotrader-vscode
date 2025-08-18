"""
업비트 WebSocket 문제 해결 테스트
- Market 정보 파싱 개선 확인
- 에러 메시지 처리 확인
- 연결 해제 오류 수정 확인
"""

import asyncio
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
    UpbitWebSocketQuotationClient
)


async def test_improved_websocket():
    """개선된 WebSocket 클라이언트 테스트"""
    print("🔧 WebSocket 클라이언트 개선사항 테스트")
    print("=" * 60)

    try:
        async with UpbitWebSocketQuotationClient() as client:
            print("✅ 클라이언트 연결 성공")

            # 구독 설정 (단순화)
            await client.subscribe_ticker(["KRW-BTC"])
            print("📡 BTC Ticker 구독 완료")

            # 메시지 수신 및 분석
            message_count = 0
            market_info_count = 0

            async for message in client.listen():
                message_count += 1

                # Market 정보 확인
                if message.market != 'UNKNOWN':
                    market_info_count += 1

                print(f"📨 메시지 {message_count}: 타입={message.type.value}, "
                      f"마켓={message.market}, 가격={message.data.get('trade_price', 'N/A')}")

                # 원본 데이터 일부 확인 (디버깅용)
                if message_count <= 3:
                    print(f"   📊 원본 필드: {list(message.data.keys())[:8]}")

                if message_count >= 10:  # 10개 메시지만 테스트
                    break

            print("\n📊 테스트 결과:")
            print(f"   총 메시지: {message_count}개")
            print(f"   Market 정보 파싱 성공: {market_info_count}개")
            print(f"   파싱 성공률: {market_info_count / message_count * 100:.1f}%")

            return message_count > 0 and market_info_count > 0

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


async def test_error_handling():
    """에러 처리 테스트"""
    print("\n🚨 에러 처리 테스트")
    print("=" * 60)

    try:
        async with UpbitWebSocketQuotationClient() as client:
            # 잘못된 구독 시도 (에러 발생 유도)
            await client.subscribe_candle(["KRW-INVALID"], unit=999)  # 잘못된 단위

            print("📡 의도적 에러 구독 시도 완료")

            # 에러 메시지 수신 확인
            error_count = 0
            message_count = 0

            async for message in client.listen():
                message_count += 1

                if 'error' in message.data:
                    error_count += 1
                    print(f"🚨 에러 메시지 수신: {message.data.get('error')}")

                if message_count >= 5:  # 5개 메시지만 확인
                    break

            print("\n📊 에러 처리 결과:")
            print(f"   에러 메시지: {error_count}개")
            return True

    except Exception as e:
        print(f"❌ 에러 처리 테스트 실패: {e}")
        return False


async def test_connection_cleanup():
    """연결 정리 테스트"""
    print("\n🔗 연결 정리 테스트")
    print("=" * 60)

    try:
        client = UpbitWebSocketQuotationClient()

        # 연결
        await client.connect()
        print("✅ 연결 성공")

        # 구독
        await client.subscribe_ticker(["KRW-BTC"])
        print("📡 구독 성공")

        # 짧은 메시지 수신
        count = 0
        async for message in client.listen():
            count += 1
            if count >= 3:
                break

        print(f"📨 {count}개 메시지 수신")

        # 연결 해제 (개선된 로직 테스트)
        await client.disconnect()
        print("✅ 연결 해제 완료 (오류 없음)")

        return True

    except Exception as e:
        print(f"❌ 연결 정리 테스트 실패: {e}")
        return False


async def main():
    """메인 테스트 실행"""
    print("🎯 WebSocket 클라이언트 개선사항 검증")
    print("🔧 Market 정보 파싱, 에러 처리, 연결 정리 개선")
    print("=" * 80)

    results = {}

    # 1. 개선된 WebSocket 테스트
    results['improved'] = await test_improved_websocket()

    # 2. 에러 처리 테스트
    results['error_handling'] = await test_error_handling()

    # 3. 연결 정리 테스트
    results['connection_cleanup'] = await test_connection_cleanup()

    # 결과 요약
    print("\n" + "=" * 80)
    print("📋 개선사항 검증 결과:")
    print(f"   ✅ Market 정보 파싱: {'성공' if results['improved'] else '실패'}")
    print(f"   ✅ 에러 처리: {'성공' if results['error_handling'] else '실패'}")
    print(f"   ✅ 연결 정리: {'성공' if results['connection_cleanup'] else '실패'}")

    if all(results.values()):
        print("\n🎉 모든 개선사항 검증 완료!")
        print("💡 WebSocket 클라이언트가 안정적으로 동작")
    else:
        print("\n⚠️ 일부 개선사항 추가 작업 필요")


if __name__ == "__main__":
    asyncio.run(main())
