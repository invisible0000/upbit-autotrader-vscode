"""
타이밍 정밀 분석기 - Rate Limiter vs 실제 HTTP 요청 간격 추적
"""

import time
import asyncio
import sys
from typing import List, Dict
from dataclasses import dataclass, field
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import (
    get_global_rate_limiter
)
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import (
    UpbitPublicClient
)


@dataclass
class TimingEvent:
    """타이밍 이벤트 기록"""
    event_type: str  # 'rate_limiter_start', 'rate_limiter_end', 'http_start', 'http_end', 'server_429'
    timestamp: float  # time.monotonic() 기준
    endpoint: str
    sequence: int
    details: Dict = field(default_factory=dict)


class TimingAnalyzer:
    """정밀 타이밍 분석기"""

    def __init__(self):
        self.events: List[TimingEvent] = []
        self.sequence_counter = 0

    def log_event(self, event_type: str, endpoint: str, **details):
        """이벤트 기록"""
        self.sequence_counter += 1
        event = TimingEvent(
            event_type=event_type,
            timestamp=time.monotonic(),
            endpoint=endpoint,
            sequence=self.sequence_counter,
            details=details
        )
        self.events.append(event)

        # 즉시 출력 (디버깅용)
        relative_time = event.timestamp - self.events[0].timestamp if self.events else 0
        print(f"[{relative_time:8.3f}s] SEQ-{event.sequence:02d} {event_type:20s} {endpoint} {details}")

    def analyze_intervals(self):
        """실제 HTTP 요청 간격 분석"""
        http_requests = [e for e in self.events if e.event_type == 'http_start']

        if len(http_requests) < 2:
            print("❌ HTTP 요청이 2개 미만으로 간격 분석 불가")
            return

        print("\n🔍 === HTTP 요청 간격 분석 ===")

        intervals = []
        for i in range(1, len(http_requests)):
            prev_req = http_requests[i - 1]
            curr_req = http_requests[i]
            interval = curr_req.timestamp - prev_req.timestamp
            intervals.append(interval)

            print(f"  요청 {i:2d}: {interval * 1000:7.1f}ms 간격 (SEQ-{prev_req.sequence} → SEQ-{curr_req.sequence})")

        avg_interval = sum(intervals) / len(intervals)
        min_interval = min(intervals)
        max_interval = max(intervals)

        print("\n📊 간격 통계:")
        print(f"  평균: {avg_interval * 1000:.1f}ms")
        print(f"  최소: {min_interval * 1000:.1f}ms")
        print(f"  최대: {max_interval * 1000:.1f}ms")
        print(f"  실제 RPS: {1 / avg_interval:.2f}")

        # Rate Limiter 설정과 비교
        expected_interval = 1 / 8.0  # 8 RPS 설정
        print("\n🎯 설정 vs 실제:")
        print(f"  설정: 8 RPS ({expected_interval * 1000:.1f}ms 간격)")
        print(f"  실제: {1 / avg_interval:.2f} RPS ({avg_interval * 1000:.1f}ms 간격)")

        if avg_interval < expected_interval * 0.9:
            print("⚠️  실제 간격이 설정보다 빠름 - Rate Limiter 누락 의심")
        elif avg_interval > expected_interval * 1.5:
            print("✅ 실제 간격이 설정보다 여유있음 - Rate Limiter 정상")

    def analyze_rate_limiter_effectiveness(self):
        """Rate Limiter 대기 시간 vs 실제 효과 분석"""
        print("\n🔍 === Rate Limiter 효과성 분석 ===")

        # Rate Limiter 대기 시간 추출
        wait_events = [e for e in self.events if e.event_type == 'rate_limiter_wait']

        for event in wait_events:
            wait_time = event.details.get('wait_time_ms', 0)
            print(f"  SEQ-{event.sequence}: {wait_time:.1f}ms 대기")

        if wait_events:
            avg_wait = sum(e.details.get('wait_time_ms', 0) for e in wait_events) / len(wait_events)
            print(f"\n📊 평균 Rate Limiter 대기: {avg_wait:.1f}ms")
        else:
            print("📊 Rate Limiter 대기 없음 (모든 요청 즉시 통과)")

    def find_429_patterns(self):
        """429 에러 발생 패턴 분석"""
        print("\n🔍 === 429 에러 패턴 분석 ===")

        error_events = [e for e in self.events if e.event_type == 'server_429']

        if not error_events:
            print("✅ 429 에러 발생하지 않음")
            return

        for error_event in error_events:
            print(f"🚨 SEQ-{error_event.sequence}: 429 에러 발생")

            # 바로 이전 HTTP 요청들과의 간격 계산
            prev_requests = [e for e in self.events
                           if e.event_type == 'http_start' and e.sequence < error_event.sequence]

            if len(prev_requests) >= 2:
                last_req = prev_requests[-1]
                second_last_req = prev_requests[-2]

                interval_to_error = error_event.timestamp - last_req.timestamp
                prev_interval = last_req.timestamp - second_last_req.timestamp

                print(f"  이전 요청 간격: {prev_interval * 1000:.1f}ms")
                print(f"  에러까지 간격: {interval_to_error * 1000:.1f}ms")


async def test_timing_with_rate_limiter():
    """Rate Limiter 포함 타이밍 테스트"""
    analyzer = TimingAnalyzer()

    print("🚀 Rate Limiter 포함 타이밍 테스트 시작")
    analyzer.log_event('test_start', 'test', test_type='rate_limiter')

    # Rate Limiter 준비
    rate_limiter = await get_global_rate_limiter()

    # 10회 요청으로 패턴 확인
    for i in range(10):
        endpoint = '/candles/minutes/1'

        # Rate Limiter 호출 시작
        analyzer.log_event('rate_limiter_start', endpoint, request_num=i+1)

        start_wait = time.monotonic()
        await rate_limiter.acquire(endpoint, 'GET')
        end_wait = time.monotonic()

        wait_time_ms = (end_wait - start_wait) * 1000
        analyzer.log_event('rate_limiter_end', endpoint,
                          request_num=i+1, wait_time_ms=wait_time_ms)

        # 실제 HTTP 요청 시뮬레이션 (짧은 지연)
        analyzer.log_event('http_start', endpoint, request_num=i+1)
        await asyncio.sleep(0.015)  # 15ms HTTP 요청 시뮬레이션
        analyzer.log_event('http_end', endpoint, request_num=i+1)

    analyzer.log_event('test_end', 'test', test_type='rate_limiter')

    # 분석 실행
    analyzer.analyze_intervals()
    analyzer.analyze_rate_limiter_effectiveness()
    analyzer.find_429_patterns()

    return analyzer


async def test_timing_with_full_client():
    """실제 UpbitPublicClient 사용 타이밍 테스트"""
    analyzer = TimingAnalyzer()

    print("\n" + "="*60)
    print("🚀 실제 UpbitPublicClient 타이밍 테스트 시작")
    analyzer.log_event('test_start', 'test', test_type='full_client')

    # 실제 클라이언트 생성
    client = UpbitPublicClient()

    try:
        # 5회 실제 API 호출
        for i in range(5):
            analyzer.log_event('api_call_start', '/candles/minutes/1', request_num=i+1)

            try:
                # 실제 API 호출
                response = await client.get_candles_minutes(
                    market="KRW-BTC",
                    unit=1,
                    count=10
                )
                analyzer.log_event('api_call_success', '/candles/minutes/1',
                                 request_num=i+1, candles_count=len(response))

            except Exception as e:
                if "429" in str(e):
                    analyzer.log_event('server_429', '/candles/minutes/1',
                                     request_num=i+1, error=str(e))
                else:
                    analyzer.log_event('api_call_error', '/candles/minutes/1',
                                     request_num=i+1, error=str(e))

    finally:
        await client.close()

    analyzer.log_event('test_end', 'test', test_type='full_client')

    # 분석 실행
    analyzer.analyze_intervals()
    analyzer.find_429_patterns()

    return analyzer


async def run_comprehensive_timing_analysis():
    """종합 타이밍 분석"""
    print("🎯 === 종합 타이밍 분석 시작 ===\n")

    # 1단계: Rate Limiter만 테스트
    print("📊 1단계: Rate Limiter 순수 테스트")
    analyzer1 = await test_timing_with_rate_limiter()

    # 2초 대기
    print("\n⏸️  2초 쿨다운...")
    await asyncio.sleep(2)

    # 2단계: 실제 클라이언트 테스트
    print("\n📊 2단계: 실제 UpbitPublicClient 테스트")
    analyzer2 = await test_timing_with_full_client()

    # 최종 비교
    print("\n🏆 === 최종 비교 분석 ===")
    print("Rate Limiter만:", len([e for e in analyzer1.events if e.event_type == 'rate_limiter_end']))
    print("실제 API 호출:", len([e for e in analyzer2.events if e.event_type == 'api_call_success']))
    print("429 에러 발생:", len([e for e in analyzer2.events if e.event_type == 'server_429']))


if __name__ == "__main__":
    asyncio.run(run_comprehensive_timing_analysis())
