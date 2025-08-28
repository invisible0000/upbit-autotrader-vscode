"""
간단한 재연결 속도 테스트 - 1회만 실행
"""

import asyncio
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5.upbit_websocket_public_client import (  # noqa: E402
    UpbitWebSocketPublicV5
)

async def quick_test():
    print("🚀 극한 최적화 재연결 속도 테스트")

    # 클라이언트 생성 및 연결
    client = UpbitWebSocketPublicV5(max_tickets=1)
    await client.connect()
    await asyncio.sleep(1.0)  # 연결 안정화

    print("연결 완료, 재연결 테스트 시작...")

    # 재연결 시간 측정
    start_time = time.perf_counter()
    success = await client.force_reconnect()
    end_time = time.perf_counter()

    if success:
        elapsed = end_time - start_time
        print(f"✅ 재연결 성공: {elapsed:.3f}초")

        # 기존 버전 대비 개선도 계산
        old_time = 0.5  # 기존 고정 대기시간
        improvement = ((old_time - elapsed) / old_time) * 100
        print(f"📊 기존 0.5초 대비: {improvement:+.1f}% 개선")

        if elapsed < 0.1:
            print("🏆 100ms 미만 달성!")
        if elapsed < 0.05:
            print("🥇 50ms 미만 달성!")
    else:
        print("❌ 재연결 실패")

    # 정리
    await client.disconnect()

if __name__ == "__main__":
    os.environ["UPBIT_CONSOLE_OUTPUT"] = "false"  # 로깅 최소화
    asyncio.run(quick_test())
