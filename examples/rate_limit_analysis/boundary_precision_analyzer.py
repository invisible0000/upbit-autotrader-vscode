#!/usr/bin/env python3
"""
업비트 서버 Rate Limit 경계 영역 정밀 분석

목적:
1. 80ms~110ms 구간에서 정확한 임계점 찾기
2. 9~12 RPS 범위의 세밀한 테스트
3. Burst + Sustained 조합 패턴 분석
4. GCRA 최적 파라미터 도출

발견사항 기반:
- 100ms(10RPS): 100% 성공
- 80ms(12.5RPS): 8.9% 실패
- Burst: 10개 요청까지 연속 가능
"""

import asyncio
import aiohttp
import time
import statistics
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
import json


@dataclass
class PrecisionTestResult:
    """정밀 테스트 결과"""
    interval_ms: int
    target_rps: float
    total_requests: int
    success_count: int
    rate_limit_count: int
    first_429_at: Optional[float]
    success_rate: float
    avg_response_time: float
    test_duration: float


class BoundaryPrecisionAnalyzer:
    """경계 영역 정밀 분석기"""

    def __init__(self):
        self.base_url = "https://api.upbit.com"
        self.test_endpoint = "/v1/candles/minutes/1"
        self.test_params = {"market": "KRW-BTC", "count": "1"}
        self.results: List[PrecisionTestResult] = []

    async def make_request(self, session: aiohttp.ClientSession) -> tuple[int, float]:
        """단일 요청 실행 - 간소화"""
        start_time = time.time()

        try:
            async with session.get(
                f"{self.base_url}{self.test_endpoint}",
                params=self.test_params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response_time = time.time() - start_time
                return response.status, response_time

        except Exception:
            return 0, time.time() - start_time

    async def precision_interval_test(
        self,
        session: aiohttp.ClientSession,
        interval_ms: int,
        test_duration: int = 60  # 더 긴 테스트로 안정성 확인
    ) -> PrecisionTestResult:
        """특정 간격으로 정밀 테스트"""
        print(f"\n🔬 정밀 테스트: {interval_ms}ms 간격 ({1000/interval_ms:.2f} RPS), {test_duration}초 동안")

        interval_sec = interval_ms / 1000.0
        target_rps = 1.0 / interval_sec

        results = []
        start_time = time.time()
        request_count = 0
        success_count = 0
        rate_limit_count = 0
        first_429_at = None
        response_times = []

        while time.time() - start_time < test_duration:
            request_start = time.time()

            status_code, response_time = await self.make_request(session)
            results.append((status_code, response_time, request_start - start_time))
            request_count += 1

            if status_code == 200:
                success_count += 1
                response_times.append(response_time)
            elif status_code == 429:
                rate_limit_count += 1
                if first_429_at is None:
                    first_429_at = request_start - start_time
                    print(f"  ⚠️  첫 429 발생: {first_429_at:.2f}초 후 (요청 #{request_count})")

            # 10초마다 진행 상황 출력
            if request_count % max(1, int(10 / interval_sec)) == 0:
                elapsed = time.time() - start_time
                current_success_rate = success_count / request_count * 100
                current_429_rate = rate_limit_count / request_count * 100
                print(f"  📊 {elapsed:.0f}초: {request_count}req, 성공률: {current_success_rate:.1f}%, 429률: {current_429_rate:.1f}%")

            # 간격 조절
            elapsed = time.time() - request_start
            sleep_time = max(0, interval_sec - elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        # 결과 정리
        success_rate = success_count / request_count * 100 if request_count > 0 else 0
        avg_response_time = statistics.mean(response_times) if response_times else 0
        actual_duration = time.time() - start_time

        result = PrecisionTestResult(
            interval_ms=interval_ms,
            target_rps=target_rps,
            total_requests=request_count,
            success_count=success_count,
            rate_limit_count=rate_limit_count,
            first_429_at=first_429_at,
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            test_duration=actual_duration
        )

        self.results.append(result)

        print(f"  ✅ 완료: {success_rate:.1f}% 성공률 ({success_count}/{request_count})")

        return result

    async def burst_plus_sustained_test(
        self,
        session: aiohttp.ClientSession,
        burst_count: int = 10,
        sustained_interval_ms: int = 100
    ):
        """Burst + Sustained 조합 테스트"""
        print(f"\n💥 Burst + Sustained 테스트: {burst_count}개 연속 + {sustained_interval_ms}ms 간격")

        # 1단계: Burst
        print(f"  🚀 Burst 단계: {burst_count}개 연속 요청")
        burst_results = []
        burst_start = time.time()

        for i in range(burst_count):
            status_code, response_time = await self.make_request(session)
            burst_results.append((status_code, response_time))
            print(f"    요청 #{i+1}: {status_code}, {response_time*1000:.1f}ms")

        burst_duration = time.time() - burst_start
        burst_success = sum(1 for status, _ in burst_results if status == 200)

        print(f"  📊 Burst 결과: {burst_success}/{burst_count} 성공, {burst_duration:.2f}초 소요")

        # 2단계: Sustained
        print(f"  ⚡ Sustained 단계: {sustained_interval_ms}ms 간격으로 30초 동안")
        sustained_start = time.time()
        sustained_results = []
        interval_sec = sustained_interval_ms / 1000.0

        while time.time() - sustained_start < 30:
            request_start = time.time()

            status_code, response_time = await self.make_request(session)
            sustained_results.append((status_code, response_time))

            if len(sustained_results) % 10 == 0:
                success_rate = sum(1 for s, _ in sustained_results if s == 200) / len(sustained_results) * 100
                print(f"    📈 {len(sustained_results)}req: {success_rate:.1f}% 성공률")

            # 간격 조절
            elapsed = time.time() - request_start
            sleep_time = max(0, interval_sec - elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        sustained_success = sum(1 for status, _ in sustained_results if status == 200)
        sustained_total = len(sustained_results)

        print(f"  📊 Sustained 결과: {sustained_success}/{sustained_total} 성공")
        print(f"  🎯 전체 결과: Burst {burst_success}/{burst_count}, Sustained {sustained_success}/{sustained_total}")

    async def find_exact_threshold(self, session: aiohttp.ClientSession):
        """정확한 임계점 찾기 - 85~105ms 세밀 테스트"""
        print(f"\n🎯 정확한 임계점 찾기: 85~105ms 구간 세밀 분석")

        # 세밀한 간격으로 테스트
        test_intervals = [105, 100, 95, 90, 85]  # ms, 안전한 것부터 시작

        for interval in test_intervals:
            await asyncio.sleep(2)  # 테스트 간 휴식
            result = await self.precision_interval_test(session, interval, test_duration=45)

            # 결과에 따른 분석
            if result.success_rate >= 99.0:
                print(f"  ✅ {interval}ms: 매우 안전 ({result.success_rate:.1f}%)")
            elif result.success_rate >= 95.0:
                print(f"  ⚠️  {interval}ms: 약간 위험 ({result.success_rate:.1f}%)")
            else:
                print(f"  ❌ {interval}ms: 위험 ({result.success_rate:.1f}%)")
                break  # 더 공격적인 테스트는 중단

    def analyze_and_recommend(self):
        """분석 및 권장사항 도출"""
        print(f"\n" + "="*60)
        print(f"📈 경계 영역 정밀 분석 결과")
        print(f"="*60)

        if not self.results:
            print("❌ 테스트 결과가 없습니다.")
            return

        # 결과 정렬 (RPS 순)
        sorted_results = sorted(self.results, key=lambda x: x.target_rps)

        print(f"\n🔍 테스트 결과 요약:")
        for result in sorted_results:
            status = "✅ 안전" if result.success_rate >= 99 else "⚠️  주의" if result.success_rate >= 95 else "❌ 위험"
            print(f"  {result.interval_ms:3d}ms ({result.target_rps:5.2f} RPS): {result.success_rate:5.1f}% {status}")

        # 안전한 최대 RPS 찾기
        safe_results = [r for r in sorted_results if r.success_rate >= 99.0]
        if safe_results:
            max_safe_rps = max(r.target_rps for r in safe_results)
            max_safe_interval = min(r.interval_ms for r in safe_results if r.target_rps == max_safe_rps)
            print(f"\n🎯 권장 설정:")
            print(f"  • 안전한 최대 RPS: {max_safe_rps:.2f}")
            print(f"  • 권장 간격: {max_safe_interval}ms")
            print(f"  • GCRA 설정: requests_per_second = {max_safe_rps:.0f}")

        # Burst 권장사항
        print(f"\n💥 Burst 설정 권장사항:")
        print(f"  • burst_size: 10 (측정된 서버 허용량)")
        print(f"  • 초기 토큰: 10개")

        # 보수적 마진 권장
        if safe_results:
            conservative_rps = max_safe_rps * 0.9  # 10% 마진
            print(f"\n🛡️  보수적 설정 (10% 마진):")
            print(f"  • RPS: {conservative_rps:.2f}")
            print(f"  • 간격: {1000/conservative_rps:.0f}ms")

        # 파일 저장
        self.save_precision_results()

    def save_precision_results(self):
        """정밀 결과 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"boundary_precision_results_{timestamp}.json"

        data = {
            "timestamp": timestamp,
            "test_type": "boundary_precision_analysis",
            "results": []
        }

        for result in self.results:
            data["results"].append({
                "interval_ms": result.interval_ms,
                "target_rps": result.target_rps,
                "total_requests": result.total_requests,
                "success_count": result.success_count,
                "rate_limit_count": result.rate_limit_count,
                "success_rate": result.success_rate,
                "first_429_at_seconds": result.first_429_at,
                "avg_response_time_ms": result.avg_response_time * 1000,
                "test_duration_seconds": result.test_duration
            })

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n💾 정밀 결과 저장: {filename}")

    async def run_precision_analysis(self):
        """전체 정밀 분석 실행"""
        print(f"🎯 업비트 서버 Rate Limit 경계 영역 정밀 분석")
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"목표: 80ms~110ms 구간에서 정확한 임계점 찾기")

        connector = aiohttp.TCPConnector(limit=10, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": "Upbit-Boundary-Precision-Analyzer/1.0"}
        ) as session:

            # 1단계: 정확한 임계점 찾기
            await self.find_exact_threshold(session)

            # 2단계: Burst + Sustained 조합 테스트
            await asyncio.sleep(3)
            await self.burst_plus_sustained_test(session)

        # 결과 분석
        self.analyze_and_recommend()


async def main():
    """메인 실행 함수"""
    analyzer = BoundaryPrecisionAnalyzer()

    try:
        await analyzer.run_precision_analysis()
    except KeyboardInterrupt:
        print(f"\n⏹️  사용자 중단. 지금까지의 결과를 분석합니다.")
        analyzer.analyze_and_recommend()
    except Exception as e:
        print(f"\n❌ 분석 중 오류 발생: {e}")
        if analyzer.results:
            analyzer.analyze_and_recommend()


if __name__ == "__main__":
    print(f"🎯 업비트 API 서버 Rate Limit 경계 영역 정밀 분석기")
    print(f"목적: 정확한 임계점 찾기 및 GCRA 최적화")
    print(f"-" * 50)

    asyncio.run(main())
