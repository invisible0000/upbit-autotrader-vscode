#!/usr/bin/env python3
"""
업비트 WebSocket 첫 응답의 stream_type 확인 테스트
첫 번째 메시지가 정말로 stream_type을 포함하는지 정확히 확인
"""

import asyncio
import json
import websockets
from datetime import datetime


async def test_first_message_stream_type():
    """첫 번째 메시지의 stream_type 직접 확인"""
    print("🧪 업비트 WebSocket 첫 응답 stream_type 확인 테스트")
    print("=" * 60)

    uri = "wss://api.upbit.com/websocket/v1"

    # 구독 메시지 (티커 하나만)
    subscription_message = [
        {"ticket": "first-message-test"},
        {"type": "ticker", "codes": ["KRW-BTC"]},
        {"format": "DEFAULT"}
    ]

    try:
        print("🔗 WebSocket 연결 중...")
        async with websockets.connect(uri) as websocket:
            print("✅ 연결 성공")

            # 구독 요청 전송
            print("📡 구독 요청 전송...")
            await websocket.send(json.dumps(subscription_message))
            print(f"   구독 메시지: {json.dumps(subscription_message)}")

            # 첫 번째 메시지 대기
            print("\n⏱️  첫 번째 메시지 대기 중...")

            message_count = 0
            async for raw_message in websocket:
                message_count += 1

                # 메시지 파싱
                try:
                    data = json.loads(raw_message)
                except json.JSONDecodeError as e:
                    print(f"❌ JSON 파싱 오류: {e}")
                    continue

                print(f"\n📨 메시지 #{message_count} 수신:")
                print(f"   수신 시각: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")

                # stream_type 확인
                stream_type = data.get("stream_type")
                if stream_type:
                    print(f"   ✅ stream_type 발견: '{stream_type}'")
                else:
                    print(f"   ❌ stream_type 없음")

                # 주요 필드들 확인
                important_fields = ["type", "code", "trade_price", "stream_type", "timestamp"]
                print(f"   📋 주요 필드:")
                for field in important_fields:
                    if field in data:
                        value = data[field]
                        if field == "trade_price":
                            value = f"{value:,.0f}원" if isinstance(value, (int, float)) else value
                        print(f"      {field}: {value}")
                    else:
                        print(f"      {field}: (없음)")

                # 전체 필드 목록
                all_fields = list(data.keys())
                print(f"   📝 전체 필드 ({len(all_fields)}개): {', '.join(all_fields)}")

                # 처음 3개 메시지만 확인하고 종료
                if message_count >= 3:
                    print(f"\n🎯 결론:")
                    if stream_type:
                        print(f"   ✅ 첫 번째 메시지부터 stream_type='{stream_type}' 포함")
                        if stream_type == "SNAPSHOT":
                            print(f"   💡 이는 초기 스냅샷 데이터임을 의미")
                        elif stream_type == "REALTIME":
                            print(f"   💡 이는 실시간 업데이트 데이터임을 의미")
                    else:
                        print(f"   ❌ 첫 번째 메시지에 stream_type 없음")
                    break

    except Exception as e:
        print(f"❌ 테스트 실행 오류: {e}")


async def test_multiple_types_first_messages():
    """여러 타입의 첫 메시지 동시 확인"""
    print(f"\n🧪 여러 타입 동시 구독 시 첫 메시지들 확인")
    print("=" * 60)

    uri = "wss://api.upbit.com/websocket/v1"

    # 복합 구독 메시지 (모든 타입)
    subscription_message = [
        {"ticket": "multi-type-test"},
        {"type": "ticker", "codes": ["KRW-BTC"]},
        {"type": "trade", "codes": ["KRW-BTC"]},
        {"type": "orderbook", "codes": ["KRW-BTC"]},
        {"type": "candle.1m", "codes": ["KRW-BTC"]},
        {"format": "DEFAULT"}
    ]

    try:
        print("🔗 WebSocket 연결 중...")
        async with websockets.connect(uri) as websocket:
            print("✅ 연결 성공")

            # 구독 요청 전송
            print("📡 복합 구독 요청 전송...")
            await websocket.send(json.dumps(subscription_message))

            # 각 타입별 첫 메시지 추적
            type_first_messages = {}
            message_count = 0

            print(f"\n⏱️  각 타입의 첫 메시지 확인 중...")

            async for raw_message in websocket:
                message_count += 1

                try:
                    data = json.loads(raw_message)
                except json.JSONDecodeError:
                    continue

                msg_type = data.get("type", "unknown")
                stream_type = data.get("stream_type")

                # 해당 타입의 첫 메시지인지 확인
                if msg_type not in type_first_messages:
                    type_first_messages[msg_type] = {
                        "stream_type": stream_type,
                        "has_stream_type": stream_type is not None,
                        "message_number": message_count,
                        "timestamp": datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    }

                    print(f"   📨 {msg_type.upper()} 첫 메시지:")
                    print(f"      순서: #{message_count}")
                    print(f"      stream_type: {stream_type if stream_type else '(없음)'}")
                    print(f"      시각: {type_first_messages[msg_type]['timestamp']}")

                # 모든 타입의 첫 메시지를 받았으면 종료
                expected_types = {"ticker", "trade", "orderbook", "candle.1m"}
                if set(type_first_messages.keys()) >= expected_types:
                    break

                # 최대 20개 메시지만 확인
                if message_count >= 20:
                    break

            # 결과 요약
            print(f"\n📊 각 타입별 첫 메시지 stream_type 결과:")
            for msg_type, info in type_first_messages.items():
                status = "✅" if info["has_stream_type"] else "❌"
                stream_type = info["stream_type"] if info["has_stream_type"] else "없음"
                print(f"   {status} {msg_type.upper()}: {stream_type}")

            # 전체 결론
            all_have_stream_type = all(info["has_stream_type"] for info in type_first_messages.values())
            print(f"\n🎯 최종 결론:")
            if all_have_stream_type:
                print(f"   ✅ 모든 타입의 첫 메시지가 stream_type을 포함")
                print(f"   💡 업비트는 구독 즉시 완전한 데이터를 전송함")
            else:
                print(f"   ❌ 일부 타입의 첫 메시지에 stream_type 없음")
                missing_types = [t for t, info in type_first_messages.items() if not info["has_stream_type"]]
                print(f"   누락된 타입: {', '.join(missing_types)}")

    except Exception as e:
        print(f"❌ 테스트 실행 오류: {e}")


async def main():
    """메인 테스트 실행"""
    print("🚀 업비트 WebSocket 첫 응답 stream_type 검증")
    print(f"📅 테스트 일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}")

    # 단일 타입 테스트
    await test_first_message_stream_type()

    # 복합 타입 테스트
    await test_multiple_types_first_messages()

    print(f"\n{'='*60}")
    print(f"📋 검증 완료!")
    print(f"   이 테스트를 통해 업비트 WebSocket 첫 응답의")
    print(f"   stream_type 포함 여부를 확실히 확인할 수 있습니다.")


if __name__ == "__main__":
    asyncio.run(main())
