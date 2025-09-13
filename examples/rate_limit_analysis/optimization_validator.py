#!/usr/bin/env python3
"""
GCRA 최적화 설정 검증 테스트

목적:
1. 새로운 10 RPS + 10 burst 설정 검증
2. 기존 8 RPS + 3 burst와 성능 비교
3. 실제 캔들 데이터 수집 시나리오 테스트
"""

import asyncio
import time
import statistics
from typing import List, Tuple
import sys
import os

# 프로젝트 루트 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import (
    UpbitGCRARateLimiter,
    UpbitRateLimitGroup,
    get_global_rate_limiter
)
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient


class OptimizationValidator:
    """최적화된 GCRA 설정 검증기"""

    def __init__(self):
        self.results = []

    async def test_burst_performance(self, limiter: UpbitGCRARateLimiter, burst_count: int = 10):
        """버스트 성능 테스트"""
        print(f"\n🚀 버스트 성능 테스트: {burst_count}개 연속 요청")

        burst_times = []
        start_time = time.monotonic()

        for i in range(burst_count):
            acquire_start = time.monotonic()
            await limiter.acquire('/candles/minutes/1', 'GET')
            acquire_time = time.monotonic() - acquire_start
            burst_times.append(acquire_time)

            print(f"  요청 #{i+1}: {acquire_time*1000:.1f}ms")

        total_time = time.monotonic() - start_time
        avg_acquire_time = statistics.mean(burst_times)
        immediate_count = sum(1 for t in burst_times if t < 0.01)  # 10ms 미만

        print(f"\n📊 버스트 결과:")
        print(f"  • 총 시간: {total_time:.2f}초")
        print(f"  • 평균 획득 시간: {avg_acquire_time*1000:.1f}ms")
        print(f"  • 즉시 처리: {immediate_count}/{burst_count}")
        print(f"  • 실제 RPS: {burst_count/total_time:.2f}")

        return {
            'total_time': total_time,
            'avg_acquire_time': avg_acquire_time,
            'immediate_count': immediate_count,
            'actual_rps': burst_count / total_time
        }

    async def test_sustained_performance(self, limiter: UpbitGCRARateLimiter, duration: int = 30):
        """지속적 성능 테스트"""
        print(f"\n⚡ 지속적 성능 테스트: {duration}초 동안")

        request_times = []
        start_time = time.monotonic()
        request_count = 0

        while time.monotonic() - start_time < duration:
            acquire_start = time.monotonic()
            await limiter.acquire('/candles/minutes/1', 'GET')
            acquire_time = time.monotonic() - acquire_start

            request_times.append(acquire_time)
            request_count += 1

            if request_count % 20 == 0:
                elapsed = time.monotonic() - start_time
                current_rps = request_count / elapsed
                print(f"  📊 {elapsed:.0f}초: {request_count}req, RPS: {current_rps:.2f}")

        total_time = time.monotonic() - start_time
        actual_rps = request_count / total_time
        avg_acquire_time = statistics.mean(request_times)
        immediate_count = sum(1 for t in request_times if t < 0.01)

        print(f"\n📊 지속 결과:")
        print(f"  • 총 요청: {request_count}")
        print(f"  • 실제 RPS: {actual_rps:.2f}")
        print(f"  • 평균 획득 시간: {avg_acquire_time*1000:.1f}ms")
        print(f"  • 즉시 처리 비율: {immediate_count/request_count*100:.1f}%")

        return {
            'total_requests': request_count,
            'actual_rps': actual_rps,
            'avg_acquire_time': avg_acquire_time,
            'immediate_ratio': immediate_count / request_count
        }

    async def test_real_candle_collection(self):
        """실제 캔들 수집 시나리오 테스트"""
        print(f"\n📊 실제 캔들 수집 시나리오 테스트")

        client = UpbitPublicClient()

        # 여러 심볼의 최근 캔들 수집 (실제 시나리오)
        symbols = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", "KRW-DOGE"]

        start_time = time.monotonic()
        success_count = 0

        for symbol in symbols:
            try:
                print(f"  📈 {symbol} 1분봉 수집 중...")
                candles = await client.get_candles_minute(
                    market=symbol,
                    unit=1,
                    count=10
                )
                success_count += 1
                print(f"    ✅ {len(candles)}개 캔들 수집 완료")

            except Exception as e:
                print(f"    ❌ 오류: {e}")

        total_time = time.monotonic() - start_time

        print(f"\n📊 실제 수집 결과:")
        print(f"  • 성공: {success_count}/{len(symbols)}")
        print(f"  • 총 시간: {total_time:.2f}초")
        print(f"  • 평균 심볼당: {total_time/len(symbols):.2f}초")

        return {
            'success_rate': success_count / len(symbols),
            'total_time': total_time,
            'time_per_symbol': total_time / len(symbols)
        }

    async def run_validation(self):
        """전체 검증 실행"""
        print(f"🎯 GCRA 최적화 설정 검증")
        print(f"새 설정: 10 RPS + 10 burst (vs 기존 8 RPS + 3 burst)")
        print(f"=" * 60)

        # 전역 Rate Limiter 사용
        limiter = await get_global_rate_limiter()

        # 현재 설정 확인
        status = limiter.get_status()
        public_status = status['groups']['rest_public'][0]
        current_rps = 1.0 / public_status['T']
        current_burst = public_status['burst_capacity']

        print(f"🔧 현재 적용된 설정:")
        print(f"  • RPS: {current_rps}")
        print(f"  • Burst: {current_burst}")

        # 1단계: 버스트 성능 테스트
        burst_result = await self.test_burst_performance(limiter, 10)

        # 잠시 휴식
        await asyncio.sleep(2)

        # 2단계: 지속적 성능 테스트
        sustained_result = await self.test_sustained_performance(limiter, 20)

        # 잠시 휴식
        await asyncio.sleep(2)

        # 3단계: 실제 캔들 수집 테스트
        collection_result = await self.test_real_candle_collection()

        # 결과 요약
        print(f"\n" + "=" * 60)
        print(f"✅ GCRA 최적화 검증 완료")
        print(f"=" * 60)

        print(f"\n🚀 버스트 성능:")
        print(f"  • 10개 요청 처리 시간: {burst_result['total_time']:.2f}초")
        print(f"  • 즉시 처리 비율: {burst_result['immediate_count']}/10")
        print(f"  • 실제 버스트 RPS: {burst_result['actual_rps']:.1f}")

        print(f"\n⚡ 지속 성능:")
        print(f"  • 실제 RPS: {sustained_result['actual_rps']:.2f}")
        print(f"  • 즉시 처리 비율: {sustained_result['immediate_ratio']*100:.1f}%")

        print(f"\n📊 실제 수집 성능:")
        print(f"  • 성공률: {collection_result['success_rate']*100:.1f}%")
        print(f"  • 심볼당 평균 시간: {collection_result['time_per_symbol']:.2f}초")

        # 성능 개선 평가
        print(f"\n🎯 성능 개선 평가:")
        if burst_result['immediate_count'] >= 8:
            print(f"  ✅ 버스트 성능 우수 (10개 중 {burst_result['immediate_count']}개 즉시)")
        else:
            print(f"  ⚠️  버스트 성능 개선 필요")

        if sustained_result['actual_rps'] >= 9.5:
            print(f"  ✅ 지속 성능 우수 ({sustained_result['actual_rps']:.2f} RPS)")
        else:
            print(f"  ⚠️  지속 성능 개선 필요")

        if collection_result['success_rate'] == 1.0:
            print(f"  ✅ 실제 수집 안정성 확보")
        else:
            print(f"  ❌ 실제 수집 오류 발생")


async def main():
    """메인 실행"""
    validator = OptimizationValidator()
    await validator.run_validation()


if __name__ == "__main__":
    asyncio.run(main())
