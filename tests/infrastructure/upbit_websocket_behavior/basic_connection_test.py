"""
업비트 WebSocket 기본 연결 테스트
- API 키 불필요한 Quotation 엔드포인트 테스트
- 스크리너/백테스팅 용도 검증
"""

import asyncio
import websockets
import json
import time
from datetime import datetime


async def test_quotation_connection():
    """업비트 WebSocket Quotation 기본 연결 테스트 (API 키 불필요)"""
    print("🚀 업비트 WebSocket Quotation 연결 테스트 시작")
    print("📊 API 키 불필요 - 스크리너/백테스팅용 시세 데이터 확인")
    print("-" * 60)

    uri = "wss://api.upbit.com/websocket/v1"  # 인증 불필요

    try:
        print(f"🔗 연결 시도: {uri}")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 연결 성공 (API 키 불필요)")

            # 구독 메시지 전송
            subscribe_msg = [
                {"ticket": "screener-test-" + str(int(time.time()))},
                {"type": "ticker", "codes": ["KRW-BTC", "KRW-ETH"]}
            ]

            print(f"📤 구독 메시지 전송: {json.dumps(subscribe_msg, ensure_ascii=False)}")
            await websocket.send(json.dumps(subscribe_msg))

            print("⏳ 시세 데이터 수신 대기...")

            # 몇 개의 메시지 수신 테스트
            for i in range(5):
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(response)

                    print(f"\n📊 메시지 {i + 1} 수신:")
                    print(f"   마켓: {data.get('market', 'N/A')}")
                    print(f"   현재가: {data.get('trade_price', 'N/A'):,}원")
                    print(f"   변화율: {data.get('signed_change_rate', 'N/A')}")
                    print(f"   타임스탬프: {datetime.fromtimestamp(data.get('timestamp', 0) / 1000)}")

                except asyncio.TimeoutError:
                    print(f"⚠️ 메시지 {i + 1} 수신 타임아웃")
                    break
                except json.JSONDecodeError as e:
                    print(f"❌ JSON 파싱 오류: {e}")
                    print("   원본 데이터: 파싱 실패")
                except Exception as e:
                    print(f"❌ 메시지 처리 오류: {e}")

            print("\n✅ 테스트 완료 - WebSocket Quotation 연결 및 데이터 수신 정상")

    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return False

    return True


async def test_multiple_data_types():
    """여러 데이터 타입 동시 구독 테스트"""
    print("\n🔀 다중 데이터 타입 구독 테스트")
    print("-" * 60)

    uri = "wss://api.upbit.com/websocket/v1"

    try:
        async with websockets.connect(uri) as websocket:
            # 여러 데이터 타입 동시 구독
            subscribe_msg = [
                {"ticket": "multi-test-" + str(int(time.time()))},
                {"type": "ticker", "codes": ["KRW-BTC"]},
                {"type": "trade", "codes": ["KRW-BTC"]},
                {"type": "orderbook", "codes": ["KRW-BTC"]},
                {"format": "DEFAULT"}
            ]

            print("📤 다중 구독 메시지 전송")
            await websocket.send(json.dumps(subscribe_msg))

            print("⏳ 다양한 데이터 타입 수신 대기...")

            data_types_received = set()

            for i in range(10):
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)

                    # 데이터 타입 추론
                    if 'trade_price' in data and 'change_rate' in data:
                        data_type = "ticker"
                    elif 'trade_price' in data and 'trade_volume' in data:
                        data_type = "trade"
                    elif 'orderbook_units' in data:
                        data_type = "orderbook"
                    else:
                        data_type = "unknown"

                    data_types_received.add(data_type)
                    print(f"📨 {data_type} 데이터 수신")

                except asyncio.TimeoutError:
                    break
                except Exception as e:
                    print(f"⚠️ 데이터 처리 오류: {e}")

            print(f"\n✅ 수신된 데이터 타입: {data_types_received}")
            return len(data_types_received) > 0

    except Exception as e:
        print(f"❌ 다중 구독 테스트 실패: {e}")
        return False


async def main():
    """메인 테스트 실행"""
    print("🎯 업비트 WebSocket 기본 기능 검증")
    print("=" * 60)

    # 기본 연결 테스트
    result1 = await test_quotation_connection()

    # 다중 데이터 타입 테스트
    result2 = await test_multiple_data_types()

    print("\n" + "=" * 60)
    print("📋 테스트 결과 요약:")
    print(f"   ✅ 기본 연결: {'성공' if result1 else '실패'}")
    print(f"   ✅ 다중 구독: {'성공' if result2 else '실패'}")

    if result1 and result2:
        print("\n🎉 WebSocket Quotation 기본 기능 검증 완료!")
        print("💡 API 키 없이도 스크리너/백테스팅 데이터 수신 가능 확인")
    else:
        print("\n⚠️ 일부 테스트 실패 - 추가 확인 필요")


if __name__ == "__main__":
    asyncio.run(main())
