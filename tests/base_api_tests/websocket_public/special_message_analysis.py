"""
업비트 WebSocket 특별 메시지 분석

🎯 목적: mixed_subscription_processing_demo.py에서 나타나는 "unknown" 메시지 원인 분석
- 데이터 메시지가 아닌 시스템 메시지 확인
- 업비트 서버에서 보내는 상태 메시지 분석
- stream_type이 없는 메시지 유형 파악
"""

import asyncio
import json
import websockets
from typing import Dict, Any, List

class SpecialMessageAnalyzer:
    """업비트 WebSocket 특별 메시지 분석기"""

    def __init__(self):
        self.url = "wss://api.upbit.com/websocket/v1"
        self.all_messages = []

    async def analyze_all_messages(self) -> None:
        """모든 메시지 타입 분석"""
        print("🔍 업비트 WebSocket 모든 메시지 타입 분석")
        print("=" * 80)

        async with websockets.connect(self.url) as websocket:
            # 혼합 구독 요청 (mixed_subscription_processing_demo.py와 동일)
            request = [
                {"ticket": "special_message_analysis"},
                {"type": "ticker", "codes": ["KRW-BTC", "KRW-ETH"]},
                {"type": "trade", "codes": ["KRW-BTC", "KRW-ETH"]},
                {"type": "orderbook", "codes": ["KRW-BTC"]},
                {"type": "candle.5m", "codes": ["KRW-BTC"]}
            ]

            print(f"📤 혼합 구독 요청: {json.dumps(request, ensure_ascii=False)}")
            await websocket.send(json.dumps(request))

            print("\n📨 수신 메시지 분석 (20초간):")
            message_types = {}
            special_messages = []

            for i in range(50):  # 최대 50개 메시지 분석
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=20.0)

                    # JSON 파싱 시도
                    try:
                        data = json.loads(response)
                    except json.JSONDecodeError:
                        # JSON이 아닌 메시지 (상태 메시지 등)
                        print(f"⚠️ 메시지 {i+1}: JSON이 아닌 메시지 - '{response}'")
                        special_messages.append({
                            "order": i + 1,
                            "type": "non_json",
                            "content": response,
                            "analysis": "시스템 상태 메시지"
                        })
                        continue

                    # 메시지 분류
                    msg_type = data.get("type", "unknown")
                    stream_type = data.get("stream_type")
                    has_stream_type = "stream_type" in data
                    has_price_data = data.get("trade_price") is not None

                    # 메시지 타입별 카운팅
                    if msg_type not in message_types:
                        message_types[msg_type] = {
                            "count": 0,
                            "with_stream_type": 0,
                            "without_stream_type": 0,
                            "with_price_data": 0,
                            "examples": []
                        }

                    message_types[msg_type]["count"] += 1

                    if has_stream_type:
                        message_types[msg_type]["with_stream_type"] += 1
                    else:
                        message_types[msg_type]["without_stream_type"] += 1

                    if has_price_data:
                        message_types[msg_type]["with_price_data"] += 1

                    # 특별한 메시지 (stream_type 없거나 type이 unknown)
                    if not has_stream_type or msg_type == "unknown":
                        if len(message_types[msg_type]["examples"]) < 3:  # 최대 3개 예시
                            message_types[msg_type]["examples"].append({
                                "order": i + 1,
                                "data": data,
                                "has_stream_type": has_stream_type,
                                "has_price_data": has_price_data
                            })

                    # 실시간 출력 (처음 10개만)
                    if i < 10:
                        stream_status = f"stream_type={stream_type}" if has_stream_type else "stream_type 없음"
                        price_status = f"현재가={data.get('trade_price', 'N/A')}" if has_price_data else "가격정보 없음"
                        print(f"   메시지 {i+1}: type={msg_type}, {stream_status}, {price_status}")

                except asyncio.TimeoutError:
                    print("⏱️ 메시지 수신 대기 시간 초과")
                    break
                except Exception as e:
                    print(f"❌ 메시지 {i+1} 처리 오류: {e}")

            # 분석 결과 출력
            print(f"\n📊 메시지 타입별 분석 결과:")
            print("=" * 80)

            for msg_type, stats in message_types.items():
                print(f"\n🔸 타입: {msg_type}")
                print(f"   총 메시지: {stats['count']}개")
                print(f"   stream_type 있음: {stats['with_stream_type']}개")
                print(f"   stream_type 없음: {stats['without_stream_type']}개")
                print(f"   가격 데이터 있음: {stats['with_price_data']}개")

                # 특별한 메시지 예시
                if stats["examples"]:
                    print(f"   📋 stream_type 없는 메시지 예시:")
                    for example in stats["examples"]:
                        print(f"      메시지 {example['order']}:")

                        # 메시지 내용 요약
                        data = example["data"]
                        summary_fields = []

                        if "status" in data:
                            summary_fields.append(f"status={data['status']}")
                        if "market" in data or "code" in data:
                            market = data.get("market", data.get("code"))
                            summary_fields.append(f"market={market}")
                        if "trade_price" in data:
                            summary_fields.append(f"trade_price={data['trade_price']}")
                        if "error" in data:
                            summary_fields.append(f"error={data['error']}")

                        summary = ", ".join(summary_fields) if summary_fields else "특별한 필드 없음"
                        print(f"         {summary}")

                        # 전체 데이터 (작은 메시지만)
                        if len(str(data)) < 200:
                            print(f"         전체: {data}")

            # 특별 메시지 분석
            if special_messages:
                print(f"\n🚨 JSON이 아닌 특별 메시지:")
                for msg in special_messages:
                    print(f"   메시지 {msg['order']}: '{msg['content']}' ({msg['analysis']})")

            print(f"\n💡 'unknown' 메시지 원인 분석:")
            if "unknown" in message_types:
                unknown_stats = message_types["unknown"]
                print(f"   - 총 {unknown_stats['count']}개의 unknown 메시지 발견")
                print(f"   - stream_type 없음: {unknown_stats['without_stream_type']}개")
                print(f"   - 가격 데이터 없음: {unknown_stats['count'] - unknown_stats['with_price_data']}개")
                print(f"   → 업비트 서버의 시스템 메시지 또는 상태 알림일 가능성")
            else:
                print(f"   - unknown 타입 메시지 없음 (정상)")

async def main():
    """메인 분석 실행"""
    analyzer = SpecialMessageAnalyzer()
    await analyzer.analyze_all_messages()

if __name__ == "__main__":
    asyncio.run(main())
