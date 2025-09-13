#!/usr/bin/env python3
"""
업비트 서버의 실제 Rate Limit을 정밀 측정하는 스크립트

목적:
1. 순수 aiohttp 클라이언트로 업비트 서버의 실제 429 threshold 찾기
2. 다양한 요청 간격으로 테스트하여 진짜 한계 측정
3. Retry-After 헤더 분석으로 서버 정책 파악
4. 현재 GCRA 설정의 보수성 정도 확인

방법론:
- Binary Search로 최적 RPS 찾기
- 연속 요청 테스트로 burst capacity 측정
- 장기간 테스트로 steady-state limit 확인
"""

import asyncio
import aiohttp
import time
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json


@dataclass
class RequestResult:
    """개별 요청 결과"""
    timestamp: float
    status_code: int
    response_time: float
    retry_after: Optional[int] = None
    error: Optional[str] = None


@dataclass
class TestPhase:
    """테스트 단계 결과"""
    phase_name: str
    target_rps: float
    actual_interval: float
    total_requests: int
    success_count: int
    rate_limit_count: int  # 429 responses
    error_count: int
    avg_response_time: float
    retry_after_values: List[int]
    first_429_at: Optional[float] = None


class EmpiricalServerLimitMeasurement:
    """업비트 서버 한계 정밀 측정기"""

    def __init__(self):
        self.base_url = "https://api.upbit.com"
        self.test_endpoint = "/v1/candles/minutes/1"
        self.test_params = {"market": "KRW-BTC", "count": "1"}
        self.results: List[RequestResult] = []
        self.phases: List[TestPhase] = []

    async def make_request(self, session: aiohttp.ClientSession) -> RequestResult:
        """단일 요청 실행"""
        start_time = time.time()

        try:
            async with session.get(
                f"{self.base_url}{self.test_endpoint}",
                params=self.test_params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response_time = time.time() - start_time

                retry_after = None
                if response.status == 429:
                    retry_after_header = response.headers.get('Retry-After')
                    if retry_after_header:
                        retry_after = int(retry_after_header)

                return RequestResult(
                    timestamp=start_time,
                    status_code=response.status,
                    response_time=response_time,
                    retry_after=retry_after
                )

        except Exception as e:
            return RequestResult(
                timestamp=start_time,
                status_code=0,
                response_time=time.time() - start_time,
                error=str(e)
            )

    async def test_fixed_interval(
        self,
        session: aiohttp.ClientSession,
        interval_ms: int,
        duration_seconds: int = 30,
        phase_name: str = ""
    ) -> TestPhase:
        """고정 간격으로 요청 테스트"""
        print(f"\n🔬 [{phase_name}] 고정 간격 테스트: {interval_ms}ms 간격, {duration_seconds}초 동안")

        interval_sec = interval_ms / 1000.0
        target_rps = 1.0 / interval_sec

        results: List[RequestResult] = []
        start_time = time.time()
        request_count = 0
        first_429_at = None

        while time.time() - start_time < duration_seconds:
            request_start = time.time()

            result = await self.make_request(session)
            results.append(result)
            request_count += 1

            # 첫 번째 429 기록
            if result.status_code == 429 and first_429_at is None:
                first_429_at = result.timestamp - start_time
                print(f"  ⚠️  첫 429 발생: {first_429_at:.2f}초 후 (요청 #{request_count})")

            # 실시간 상태 출력
            if request_count % 10 == 0:
                success_rate = sum(1 for r in results if r.status_code == 200) / len(results) * 100
                rate_limit_rate = sum(1 for r in results if r.status_code == 429) / len(results) * 100
                print(f"  📊 진행: {request_count}req, 성공률: {success_rate:.1f}%, 429률: {rate_limit_rate:.1f}%")

            # 간격 조절
            elapsed = time.time() - request_start
            sleep_time = max(0, interval_sec - elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        # 결과 분석
        success_count = sum(1 for r in results if r.status_code == 200)
        rate_limit_count = sum(1 for r in results if r.status_code == 429)
        error_count = sum(1 for r in results if r.status_code not in [200, 429])

        response_times = [r.response_time for r in results if r.response_time > 0]
        avg_response_time = statistics.mean(response_times) if response_times else 0

        retry_after_values = [r.retry_after for r in results if r.retry_after is not None]

        # 실제 간격 계산
        timestamps = [r.timestamp for r in results]
        actual_intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
        actual_interval = statistics.mean(actual_intervals) if actual_intervals else interval_sec

        phase = TestPhase(
            phase_name=phase_name,
            target_rps=target_rps,
            actual_interval=actual_interval,
            total_requests=len(results),
            success_count=success_count,
            rate_limit_count=rate_limit_count,
            error_count=error_count,
            avg_response_time=avg_response_time,
            retry_after_values=retry_after_values,
            first_429_at=first_429_at
        )

        self.phases.append(phase)
        self.results.extend(results)

        return phase

    async def burst_test(self, session: aiohttp.ClientSession, burst_size: int = 20) -> TestPhase:
        """연속 Burst 요청 테스트"""
        print(f"\n💥 Burst 테스트: {burst_size}개 연속 요청")

        results: List[RequestResult] = []
        start_time = time.time()
        first_429_at = None

        for i in range(burst_size):
            result = await self.make_request(session)
            results.append(result)

            if result.status_code == 429 and first_429_at is None:
                first_429_at = result.timestamp - start_time
                print(f"  ⚠️  Burst에서 첫 429: {i+1}번째 요청에서 발생")

            print(f"  📋 요청 #{i+1}: {result.status_code}, {result.response_time*1000:.1f}ms")

        # 분석
        success_count = sum(1 for r in results if r.status_code == 200)
        rate_limit_count = sum(1 for r in results if r.status_code == 429)

        timestamps = [r.timestamp for r in results]
        total_duration = timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 0
        actual_rps = len(results) / max(total_duration, 0.001)

        response_times = [r.response_time for r in results if r.response_time > 0]
        avg_response_time = statistics.mean(response_times) if response_times else 0

        retry_after_values = [r.retry_after for r in results if r.retry_after is not None]

        phase = TestPhase(
            phase_name="Burst Test",
            target_rps=actual_rps,
            actual_interval=total_duration / max(len(results)-1, 1),
            total_requests=len(results),
            success_count=success_count,
            rate_limit_count=rate_limit_count,
            error_count=len(results) - success_count - rate_limit_count,
            avg_response_time=avg_response_time,
            retry_after_values=retry_after_values,
            first_429_at=first_429_at
        )

        self.phases.append(phase)
        self.results.extend(results)

        return phase

    async def binary_search_optimal_rps(self, session: aiohttp.ClientSession) -> float:
        """Binary Search로 최적 RPS 찾기"""
        print(f"\n🎯 Binary Search로 최적 RPS 찾기")

        # 초기 범위: 매우 보수적 ~ 매우 공격적
        min_interval_ms = 50   # 20 RPS
        max_interval_ms = 2000  # 0.5 RPS

        optimal_interval = None
        iterations = 0
        max_iterations = 6  # 충분한 정밀도

        while iterations < max_iterations and (max_interval_ms - min_interval_ms) > 50:
            iterations += 1
            mid_interval = (min_interval_ms + max_interval_ms) // 2

            print(f"  🔍 반복 #{iterations}: {mid_interval}ms 간격 테스트 (RPS: {1000/mid_interval:.2f})")

            phase = await self.test_fixed_interval(
                session,
                mid_interval,
                duration_seconds=20,  # 짧게 해서 빠르게 판단
                phase_name=f"Binary Search #{iterations}"
            )

            # 429 발생률로 판단
            rate_limit_rate = phase.rate_limit_count / phase.total_requests

            print(f"    📊 결과: 429률 {rate_limit_rate*100:.1f}%")

            if rate_limit_rate > 0.1:  # 10% 이상 429 → 너무 빠름
                min_interval_ms = mid_interval
                print(f"    ⬆️  너무 빠름. 간격 증가 ({min_interval_ms}ms~{max_interval_ms}ms)")
            else:  # 429가 거의 없음 → 더 빨리 가능
                max_interval_ms = mid_interval
                optimal_interval = mid_interval
                print(f"    ⬇️  여유 있음. 간격 감소 ({min_interval_ms}ms~{max_interval_ms}ms)")

        if optimal_interval:
            optimal_rps = 1000 / optimal_interval
            print(f"  🎉 최적 구간 발견: {optimal_interval}ms 간격 (≈ {optimal_rps:.2f} RPS)")
            return optimal_rps
        else:
            print(f"  ⚠️  최적값 찾기 실패. 보수적으로 설정 필요")
            return 1.0  # 매우 보수적

    def analyze_results(self):
        """전체 결과 분석 및 리포트 생성"""
        print(f"\n" + "="*60)
        print(f"📊 업비트 서버 Rate Limit 측정 결과 분석")
        print(f"="*60)

        if not self.phases:
            print("❌ 측정 데이터가 없습니다.")
            return

        print(f"\n🔍 단계별 결과:")
        for phase in self.phases:
            success_rate = phase.success_count / phase.total_requests * 100
            rate_limit_rate = phase.rate_limit_count / phase.total_requests * 100

            print(f"\n  📋 {phase.phase_name}")
            print(f"    • 목표 RPS: {phase.target_rps:.2f}")
            print(f"    • 실제 간격: {phase.actual_interval*1000:.1f}ms")
            print(f"    • 총 요청: {phase.total_requests}")
            print(f"    • 성공률: {success_rate:.1f}% ({phase.success_count}/{phase.total_requests})")
            print(f"    • 429 비율: {rate_limit_rate:.1f}% ({phase.rate_limit_count}/{phase.total_requests})")

            if phase.first_429_at:
                print(f"    • 첫 429 발생: {phase.first_429_at:.2f}초 후")

            if phase.retry_after_values:
                avg_retry_after = statistics.mean(phase.retry_after_values)
                print(f"    • Retry-After 평균: {avg_retry_after:.1f}초")

        # 현재 GCRA 설정과 비교
        print(f"\n📈 GCRA 설정 vs 측정 결과 비교:")

        # 성공적인 단계들에서 최고 RPS 찾기
        successful_phases = [p for p in self.phases if p.rate_limit_count / p.total_requests < 0.05]
        if successful_phases:
            max_successful_rps = max(p.target_rps for p in successful_phases)
            print(f"    • 측정된 최대 안전 RPS: {max_successful_rps:.2f}")
            print(f"    • 현재 GCRA 설정 (10 req/sec): 비교 분석 필요")

            improvement_ratio = max_successful_rps / 10.0
            print(f"    • 개선 가능 배수: {improvement_ratio:.2f}x")

            if improvement_ratio > 1.5:
                print(f"    • 🚀 현재 설정이 과도하게 보수적! {improvement_ratio:.1f}배 빨라질 수 있음")
            elif improvement_ratio < 0.8:
                print(f"    • ⚠️  현재 설정도 공격적. 조금 보수적으로 조정 필요")
            else:
                print(f"    • ✅ 현재 설정이 적절한 수준")

        print(f"\n💡 권장사항:")
        self._generate_recommendations()

    def _generate_recommendations(self):
        """측정 결과 기반 권장사항 생성"""
        if not self.phases:
            return

        # Burst 테스트 결과 분석
        burst_phases = [p for p in self.phases if "Burst" in p.phase_name]
        if burst_phases:
            burst_phase = burst_phases[0]
            if burst_phase.first_429_at and burst_phase.first_429_at < 1.0:
                burst_capacity = burst_phase.success_count
                print(f"    • Burst capacity: 약 {burst_capacity}개 요청까지 연속 가능")
            else:
                print(f"    • Burst capacity: 20개 이상 (측정 범위 초과)")

        # 안정적인 RPS 범위
        stable_phases = [p for p in self.phases if p.rate_limit_count == 0 and p.total_requests > 10]
        if stable_phases:
            max_stable_rps = max(p.target_rps for p in stable_phases)
            print(f"    • 안정적 RPS 범위: ~{max_stable_rps:.2f} RPS")

        # 권장 GCRA 설정
        print(f"    • 권장 GCRA 설정 업데이트:")
        print(f"      - requests_per_second: [측정 결과 기반]")
        print(f"      - burst_size: [burst capacity 기반]")
        print(f"      - 보수적 마진: 10-20% 여유 유지")

    async def run_full_measurement(self):
        """전체 측정 프로세스 실행"""
        print(f"🚀 업비트 서버 Rate Limit 정밀 측정 시작")
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        connector = aiohttp.TCPConnector(limit=10, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": "Upbit-Rate-Limit-Measurement/1.0"}
        ) as session:

            # 1단계: Burst 테스트
            await self.burst_test(session, burst_size=20)

            # 2초 휴식
            await asyncio.sleep(2)

            # 2단계: Binary Search로 최적 RPS 찾기
            optimal_rps = await self.binary_search_optimal_rps(session)

            # 3단계: 몇 가지 고정 간격 테스트
            test_intervals = [100, 150, 200, 300, 500]  # ms
            for interval in test_intervals:
                await asyncio.sleep(1)  # 단계 간 휴식
                await self.test_fixed_interval(
                    session,
                    interval,
                    duration_seconds=15,
                    phase_name=f"고정간격 {interval}ms"
                )

        # 결과 분석
        self.analyze_results()

        # JSON으로 상세 결과 저장
        self.save_detailed_results()

    def save_detailed_results(self):
        """상세 측정 결과를 JSON으로 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"empirical_server_limit_results_{timestamp}.json"

        # 결과 데이터 직렬화
        results_data = {
            "measurement_timestamp": timestamp,
            "total_requests": len(self.results),
            "phases": [],
            "raw_results": []
        }

        # 단계별 결과
        for phase in self.phases:
            phase_data = {
                "phase_name": phase.phase_name,
                "target_rps": phase.target_rps,
                "actual_interval_ms": phase.actual_interval * 1000,
                "total_requests": phase.total_requests,
                "success_count": phase.success_count,
                "rate_limit_count": phase.rate_limit_count,
                "success_rate": phase.success_count / phase.total_requests * 100,
                "rate_limit_rate": phase.rate_limit_count / phase.total_requests * 100,
                "avg_response_time_ms": phase.avg_response_time * 1000,
                "first_429_at_seconds": phase.first_429_at,
                "retry_after_values": phase.retry_after_values
            }
            results_data["phases"].append(phase_data)

        # 원시 결과 (처음 100개만)
        for result in self.results[:100]:
            result_data = {
                "timestamp": result.timestamp,
                "status_code": result.status_code,
                "response_time_ms": result.response_time * 1000,
                "retry_after": result.retry_after,
                "error": result.error
            }
            results_data["raw_results"].append(result_data)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        print(f"\n💾 상세 결과 저장됨: {filename}")


async def main():
    """메인 실행 함수"""
    measurement = EmpiricalServerLimitMeasurement()

    try:
        await measurement.run_full_measurement()
    except KeyboardInterrupt:
        print(f"\n⏹️  사용자 중단. 지금까지의 결과를 분석합니다.")
        measurement.analyze_results()
    except Exception as e:
        print(f"\n❌ 측정 중 오류 발생: {e}")
        if measurement.results:
            print(f"🔍 부분 결과라도 분석해보겠습니다.")
            measurement.analyze_results()


if __name__ == "__main__":
    print(f"📡 업비트 API 서버 Rate Limit 정밀 측정기")
    print(f"목적: 실제 서버 한계를 찾아 GCRA 설정 최적화")
    print(f"-" * 50)

    asyncio.run(main())
