"""
업비트 WebSocket 첫 번째 메시지 상세 분석

🎯 목적: 첫 번째 메시지가 실제 데이터인지 구독 확인인지 검증
- 첫 번째 메시지의 모든 필드 분석
- 데이터 유효성 검증 (가격, 시간 등)
- 실제 시세 데이터인지 확인
"""

import asyncio
import json
import websockets
from datetime import datetime
from typing import Dict, Any

class FirstMessageAnalyzer:
    """업비트 WebSocket 첫 번째 메시지 분석기"""

    def __init__(self):
        self.url = "wss://api.upbit.com/websocket/v1"

    async def analyze_first_message_detailed(self) -> None:
        """첫 번째 메시지 상세 분석"""
        print("🔍 업비트 WebSocket 첫 번째 메시지 상세 분석")
        print("=" * 80)

        async with websockets.connect(self.url) as websocket:
            request = [
                {"ticket": "first_message_analysis"},
                {"type": "ticker", "codes": ["KRW-BTC"]}
            ]

            print(f"📤 구독 요청: {json.dumps(request, ensure_ascii=False)}")
            await websocket.send(json.dumps(request))

            # 첫 번째 메시지 분석
            print("\n📨 첫 번째 메시지 수신 중...")
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            data = json.loads(response)

            print("\n📋 첫 번째 메시지 전체 내용:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

            print("\n🔍 주요 필드 분석:")

            # 기본 정보
            message_type = data.get("type", "알 수 없음")
            market = data.get("market", data.get("code", "알 수 없음"))
            stream_type = data.get("stream_type", "없음")

            print(f"   📊 타입: {message_type}")
            print(f"   🏪 마켓: {market}")
            print(f"   🔄 스트림 타입: {stream_type}")

            # 가격 정보 검증
            trade_price = data.get("trade_price")
            opening_price = data.get("opening_price")
            high_price = data.get("high_price")
            low_price = data.get("low_price")

            print(f"\n💰 가격 정보:")
            print(f"   현재가: {trade_price:,}원" if trade_price else "   현재가: 없음")
            print(f"   시가: {opening_price:,}원" if opening_price else "   시가: 없음")
            print(f"   고가: {high_price:,}원" if high_price else "   고가: 없음")
            print(f"   저가: {low_price:,}원" if low_price else "   저가: 없음")

            # 시간 정보 검증
            timestamp = data.get("timestamp")
            trade_timestamp = data.get("trade_timestamp")
            trade_date = data.get("trade_date")
            trade_time = data.get("trade_time")

            print(f"\n⏰ 시간 정보:")
            if timestamp:
                dt = datetime.fromtimestamp(timestamp / 1000)
                print(f"   타임스탬프: {timestamp} ({dt.strftime('%Y-%m-%d %H:%M:%S')})")
            if trade_timestamp:
                dt = datetime.fromtimestamp(trade_timestamp / 1000)
                print(f"   체결시간: {trade_timestamp} ({dt.strftime('%Y-%m-%d %H:%M:%S')})")
            if trade_date:
                print(f"   체결일자: {trade_date}")
            if trade_time:
                print(f"   체결시각: {trade_time}")

            # 거래량 정보
            trade_volume = data.get("trade_volume")
            acc_trade_volume = data.get("acc_trade_volume")
            acc_trade_price = data.get("acc_trade_price")

            print(f"\n📈 거래량 정보:")
            print(f"   체결량: {trade_volume}" if trade_volume else "   체결량: 없음")
            print(f"   누적거래량: {acc_trade_volume}" if acc_trade_volume else "   누적거래량: 없음")
            print(f"   누적거래금액: {acc_trade_price:,.0f}원" if acc_trade_price else "   누적거래금액: 없음")

            # 변화 정보
            change = data.get("change")
            change_price = data.get("change_price")
            change_rate = data.get("change_rate")

            print(f"\n📊 변화 정보:")
            print(f"   변화방향: {change}" if change else "   변화방향: 없음")
            print(f"   변화금액: {change_price:,}원" if change_price else "   변화금액: 없음")
            print(f"   변화율: {change_rate:.4f}%" if change_rate else "   변화율: 없음")

            # 데이터 유효성 검증
            print(f"\n✅ 데이터 유효성 검증:")

            is_valid_data = True
            validation_results = []

            if not trade_price or trade_price <= 0:
                is_valid_data = False
                validation_results.append("❌ 유효하지 않은 현재가")
            else:
                validation_results.append("✅ 유효한 현재가")

            if not timestamp:
                is_valid_data = False
                validation_results.append("❌ 타임스탬프 없음")
            else:
                validation_results.append("✅ 유효한 타임스탬프")

            if stream_type not in ["SNAPSHOT", "REALTIME"]:
                validation_results.append(f"⚠️ 예상치 못한 stream_type: {stream_type}")
            else:
                validation_results.append(f"✅ 유효한 stream_type: {stream_type}")

            for result in validation_results:
                print(f"   {result}")

            print(f"\n🎯 결론:")
            if is_valid_data:
                print("   ✅ 첫 번째 메시지는 실제 시세 데이터입니다")
                print("   ✅ 구독 후 즉시 사용 가능한 유효한 데이터")
                if stream_type == "SNAPSHOT":
                    print("   📸 스냅샷 데이터: 현재 시점의 완전한 시세 정보")
                elif stream_type == "REALTIME":
                    print("   🔴 실시간 데이터: 실시간 업데이트 정보")
            else:
                print("   ❌ 첫 번째 메시지는 유효하지 않은 데이터입니다")
                print("   ⚠️ 구독 확인 메시지일 가능성")

            # 두 번째 메시지와 비교
            print(f"\n🔄 두 번째 메시지와 비교...")
            try:
                response2 = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data2 = json.loads(response2)

                trade_price2 = data2.get("trade_price")
                stream_type2 = data2.get("stream_type")
                timestamp2 = data2.get("timestamp")

                print(f"   📨 두 번째 메시지:")
                print(f"      현재가: {trade_price2:,}원" if trade_price2 else "      현재가: 없음")
                print(f"      stream_type: {stream_type2}")

                if trade_price and trade_price2:
                    price_diff = abs(trade_price - trade_price2)
                    print(f"      가격 차이: {price_diff:,}원")

                if timestamp and timestamp2:
                    time_diff = abs(timestamp - timestamp2)
                    print(f"      시간 차이: {time_diff}ms")

            except asyncio.TimeoutError:
                print("   ⏱️ 두 번째 메시지 대기 시간 초과")

async def main():
    """메인 분석 실행"""
    analyzer = FirstMessageAnalyzer()
    await analyzer.analyze_first_message_detailed()

if __name__ == "__main__":
    asyncio.run(main())
