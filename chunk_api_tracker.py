"""
청크 수집 중 API 호출 추적기 - 숨겨진 동시 호출 탐지
"""

import asyncio
import time
import sys
from pathlib import Path
from typing import List
import json

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 테스트용 임포트
from tests.candle_data_logic.candle_collection_tester import test_count_collection


class ChunkAPICallTracker:
    """청크 수집 중 모든 API 호출 추적"""

    def __init__(self):
        self.api_calls = []
        self.start_time = None

    def log_api_call(self, endpoint: str, details: dict = None):
        """API 호출 기록"""
        if self.start_time is None:
            self.start_time = time.monotonic()

        timestamp = time.monotonic()
        relative_time = timestamp - self.start_time

        call_info = {
            'timestamp': timestamp,
            'relative_time': relative_time,
            'endpoint': endpoint,
            'details': details or {}
        }

        self.api_calls.append(call_info)
        print(f"[{relative_time:8.3f}s] API 호출: {endpoint} {details}")

    def analyze_call_patterns(self):
        """API 호출 패턴 분석"""
        print(f"\n🔍 === API 호출 패턴 분석 ===")
        print(f"총 API 호출: {len(self.api_calls)}회")

        if len(self.api_calls) < 2:
            print("API 호출이 2개 미만으로 분석 불가")
            return

        # 호출 간격 분석
        intervals = []
        for i in range(1, len(self.api_calls)):
            prev_call = self.api_calls[i - 1]
            curr_call = self.api_calls[i]
            interval = curr_call['relative_time'] - prev_call['relative_time']
            intervals.append(interval)

            print(f"  호출 {i:2d}: {interval * 1000:7.1f}ms 간격")

        avg_interval = sum(intervals) / len(intervals)
        min_interval = min(intervals)
        max_interval = max(intervals)

        print(f"\n📊 간격 통계:")
        print(f"  평균: {avg_interval * 1000:.1f}ms")
        print(f"  최소: {min_interval * 1000:.1f}ms")
        print(f"  최대: {max_interval * 1000:.1f}ms")
        print(f"  실제 RPS: {1 / avg_interval:.2f}")

        # 위험한 간격 탐지 (8 RPS = 125ms 기준)
        danger_calls = [i for i, interval in enumerate(intervals) if interval < 0.11]  # 110ms 미만
        if danger_calls:
            print(f"\n⚠️  위험한 간격 감지: {len(danger_calls)}회")
            for call_idx in danger_calls:
                print(f"    호출 {call_idx + 1}: {intervals[call_idx] * 1000:.1f}ms")

        # 동시 호출 탐지 (10ms 이내)
        concurrent_calls = [i for i, interval in enumerate(intervals) if interval < 0.01]
        if concurrent_calls:
            print(f"\n🚨 동시 호출 의심: {len(concurrent_calls)}회")
            for call_idx in concurrent_calls:
                print(f"    호출 {call_idx + 1}: {intervals[call_idx] * 1000:.1f}ms")


# Rate Limiter 호출 추적을 위한 패치
original_acquire = None
tracker = ChunkAPICallTracker()


async def patched_acquire(self, endpoint: str, method: str = 'GET', **kwargs):
    """Rate Limiter acquire 호출 추적"""
    tracker.log_api_call(f"RATE_LIMITER:{endpoint}", {
        'method': method,
        'limiter_id': getattr(self, 'client_id', 'unknown')
    })

    # 원본 호출
    return await original_acquire(self, endpoint, method, **kwargs)


async def test_chunk_collection_with_tracking():
    """청크 수집 중 API 호출 추적 테스트"""
    global original_acquire, tracker

    print("🎯 청크 수집 API 호출 추적 테스트 시작")

    # Rate Limiter 패치
    from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import UpbitGCRARateLimiter
    original_acquire = UpbitGCRARateLimiter.acquire
    UpbitGCRARateLimiter.acquire = patched_acquire

    try:
        print("\n📊 소규모 청크 테스트 (5개 청크, 50개 캔들)")
        tracker = ChunkAPICallTracker()  # 리셋

        # 기존 테스트 함수 직접 호출
        await test_count_collection(
            symbol="KRW-BTC",
            timeframe="1m",
            count=50
        )

        # 결과 분석
        tracker.analyze_call_patterns()

        print("\n" + "="*60)
        print("📊 중간 규모 청크 테스트 (10개 청크, 100개 캔들)")

        # 2초 대기
        await asyncio.sleep(2)

        tracker = ChunkAPICallTracker()  # 리셋

        # 중간 규모 테스트
        await test_count_collection(
            symbol="KRW-BTC",
            timeframe="1m",
            count=100
        )

        # 결과 분석
        tracker.analyze_call_patterns()

    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 패치 복원
        if original_acquire:
            UpbitGCRARateLimiter.acquire = original_acquire

        print("\n✅ 추적 테스트 완료")


if __name__ == "__main__":
    asyncio.run(test_chunk_collection_with_tracking())
