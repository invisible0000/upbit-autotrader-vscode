"""
업비트 WebSocket 성능 테스트 (간소화 버전)
RPS(Requests Per Second) 측정 및 실제 제한 확인
"""
import asyncio
import json
import time
import uuid
from datetime import datetime
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleUpbitWebSocketTester:
    """간소화된 업비트 WebSocket 테스터"""

    def __init__(self, url: str = "wss://api.upbit.com/websocket/v1"):
        self.url = url

    async def test_basic_connection(self):
        """기본 연결 테스트"""
        logger.info("🔗 기본 WebSocket 연결 테스트")

        try:
            async with websockets.connect(self.url) as websocket:
                # 단일 구독 요청
                subscription = [
                    {"ticket": str(uuid.uuid4())},
                    {"type": "ticker", "codes": ["KRW-BTC"]},
                    {"format": "DEFAULT"}
                ]

                await websocket.send(json.dumps(subscription))
                logger.info("✅ 구독 요청 전송 완료")

                # 5초간 메시지 수신
                message_count = 0
                start_time = time.time()

                try:
                    while time.time() - start_time < 5:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        message_count += 1

                        if message_count <= 3:  # 처음 3개 메시지만 출력
                            data = json.loads(message)
                            logger.info(f"📥 메시지 {message_count}: {data.get('market', 'Unknown')} - {data.get('trade_price', 'N/A')}")

                except asyncio.TimeoutError:
                    pass

                duration = time.time() - start_time
                rps = message_count / duration

                logger.info(f"📊 결과: {message_count}개 메시지, {duration:.2f}초, {rps:.2f} msg/sec")
                return {"messages": message_count, "duration": duration, "rps": rps}

        except Exception as e:
            logger.error(f"❌ 연결 실패: {e}")
            return {"error": str(e)}

    async def test_multiple_subscriptions(self):
        """다중 구독 테스트"""
        logger.info("📊 다중 구독 성능 테스트")

        try:
            async with websockets.connect(self.url) as websocket:
                # 여러 심볼 구독
                symbols = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", "KRW-DOT"]

                subscription = [
                    {"ticket": str(uuid.uuid4())},
                    {"type": "ticker", "codes": symbols},
                    {"format": "SIMPLE"}  # 간소화 포맷
                ]

                request_time = time.time()
                await websocket.send(json.dumps(subscription))
                logger.info(f"✅ {len(symbols)}개 심볼 구독 요청 완료")

                # 10초간 메시지 수신
                message_count = 0
                start_time = time.time()
                symbol_counts = {}

                try:
                    while time.time() - start_time < 10:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        message_count += 1

                        try:
                            data = json.loads(message)
                            market = data.get('mk', data.get('market', 'Unknown'))
                            symbol_counts[market] = symbol_counts.get(market, 0) + 1
                        except:
                            pass

                except asyncio.TimeoutError:
                    pass

                duration = time.time() - start_time
                rps = message_count / duration

                logger.info(f"📊 다중 구독 결과:")
                logger.info(f"   총 메시지: {message_count}개")
                logger.info(f"   지속 시간: {duration:.2f}초")
                logger.info(f"   평균 RPS: {rps:.2f}")

                for symbol, count in symbol_counts.items():
                    logger.info(f"   {symbol}: {count}개 ({count/duration:.2f} msg/sec)")

                return {
                    "total_messages": message_count,
                    "duration": duration,
                    "rps": rps,
                    "symbol_breakdown": symbol_counts
                }

        except Exception as e:
            logger.error(f"❌ 다중 구독 실패: {e}")
            return {"error": str(e)}

    async def test_rate_limits(self):
        """Rate Limit 실제 테스트"""
        logger.info("🚦 실제 Rate Limit 테스트")

        # WebSocket 연결 제한 테스트
        logger.info("📊 WebSocket 연결 빈도 테스트...")

        connect_results = []
        for i in range(3):  # 3번 연속 연결
            start = time.time()
            try:
                async with websockets.connect(self.url, timeout=5) as ws:
                    # 짧은 테스트 메시지
                    test_msg = [
                        {"ticket": str(uuid.uuid4())},
                        {"type": "ticker", "codes": ["KRW-BTC"]},
                        {"format": "DEFAULT"}
                    ]
                    await ws.send(json.dumps(test_msg))

                    # 1초간 대기
                    await asyncio.sleep(1)
                    duration = time.time() - start
                    connect_results.append({"success": True, "duration": duration})
                    logger.info(f"   연결 {i+1}: 성공 ({duration:.2f}초)")

            except Exception as e:
                duration = time.time() - start
                connect_results.append({"success": False, "error": str(e), "duration": duration})
                logger.info(f"   연결 {i+1}: 실패 - {e}")

        # 메시지 전송 빈도 테스트
        logger.info("📊 메시지 전송 빈도 테스트...")

        try:
            async with websockets.connect(self.url) as ws:
                message_results = []

                for i in range(10):  # 10개 메시지 전송
                    start = time.time()
                    try:
                        msg = [
                            {"ticket": str(uuid.uuid4())},
                            {"type": "ticker", "codes": ["KRW-BTC"]},
                            {"format": "DEFAULT"}
                        ]
                        await ws.send(json.dumps(msg))
                        duration = time.time() - start
                        message_results.append({"success": True, "duration": duration})

                        # 짧은 간격으로 전송
                        await asyncio.sleep(0.2)

                    except Exception as e:
                        duration = time.time() - start
                        message_results.append({"success": False, "error": str(e)})
                        logger.info(f"   메시지 {i+1}: 실패 - {e}")
                        break

                successful_messages = sum(1 for r in message_results if r["success"])
                logger.info(f"   성공한 메시지: {successful_messages}/10")

        except Exception as e:
            logger.info(f"   메시지 테스트 실패: {e}")

        return {
            "connection_tests": connect_results,
            "message_tests": message_results if 'message_results' in locals() else []
        }


async def main():
    """메인 테스트"""

    tester = SimpleUpbitWebSocketTester()

    print("🚀 업비트 WebSocket 간소화 성능 테스트")
    print("=" * 50)

    # 1. 기본 연결 테스트
    print("\n1️⃣ 기본 연결 테스트")
    basic_result = await tester.test_basic_connection()

    # 2. 다중 구독 테스트
    print("\n2️⃣ 다중 구독 테스트")
    multi_result = await tester.test_multiple_subscriptions()

    # 3. Rate Limit 테스트
    print("\n3️⃣ Rate Limit 테스트")
    rate_result = await tester.test_rate_limits()

    # 결과 요약
    print("\n📋 테스트 결과 요약")
    print("=" * 30)

    if "rps" in basic_result:
        print(f"기본 연결 RPS: {basic_result['rps']:.2f}")

    if "rps" in multi_result:
        print(f"다중 구독 RPS: {multi_result['rps']:.2f}")
        print(f"동시 구독 심볼: {len(multi_result.get('symbol_breakdown', {}))}")

    successful_connections = sum(1 for r in rate_result["connection_tests"] if r["success"])
    print(f"성공한 연결: {successful_connections}/3")

    print("\n✅ 테스트 완료!")


if __name__ == "__main__":
    asyncio.run(main())
