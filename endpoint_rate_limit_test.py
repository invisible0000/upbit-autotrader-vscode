"""
업비트 Rate Limiter 엔드포인트별 제한 검증 테스트
복잡한 0.5 RPS, 8 RPS, 30 RPS 혼합 시나리오 테스트
"""

import asyncio
import time
from typing import Dict, List
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import (
    UpbitRateLimiter, RateLimitStrategy, UpbitRateLimitGroup
)


@dataclass
class EndpointTestResult:
    """엔드포인트 테스트 결과"""
    endpoint: str
    method: str
    expected_group: str
    expected_rps: float
    actual_rps: float
    total_requests: int
    test_duration: float
    wait_times: List[float]
    success: bool
    error_message: str = ""


class EndpointRateLimitTester:
    """엔드포인트별 Rate Limit 검증 테스터"""

    def __init__(self):
        self.limiter = UpbitRateLimiter(
            client_id="endpoint_tester",
            strategy=RateLimitStrategy.HYBRID_FAST
        )

    async def test_single_endpoint(
        self,
        endpoint: str,
        method: str,
        expected_rps: float,
        test_duration: float = 10.0,
        request_count: int = None
    ) -> EndpointTestResult:
        """단일 엔드포인트 Rate Limit 테스트"""

        print(f"\n🧪 테스트: {endpoint} [{method}] (목표: {expected_rps} RPS)")

        # 예상 그룹 확인
        expected_group = self.limiter._get_endpoint_group(endpoint, method)

        start_time = time.perf_counter()
        wait_times = []
        total_requests = 0

        # 요청 수 결정
        if request_count is None:
            request_count = max(int(expected_rps * test_duration * 1.2), 20)

        try:
            for i in range(request_count):
                loop_start = time.perf_counter()

                # Rate Limiter acquire
                await self.limiter.acquire(endpoint, method)

                loop_end = time.perf_counter()
                wait_time = (loop_end - loop_start) * 1000  # ms
                wait_times.append(wait_time)
                total_requests += 1

                # 진행 상황 출력
                if total_requests % max(1, request_count // 5) == 0:
                    elapsed = time.perf_counter() - start_time
                    current_rps = total_requests / elapsed
                    avg_wait = sum(wait_times[-10:]) / min(10, len(wait_times))
                    print(f"   진행: {total_requests}/{request_count}, "
                          f"현재 RPS: {current_rps:.2f}, 평균대기: {avg_wait:.1f}ms")

                # 시간 제한 확인
                if time.perf_counter() - start_time >= test_duration:
                    break

        except Exception as e:
            return EndpointTestResult(
                endpoint=endpoint,
                method=method,
                expected_group=expected_group.value,
                expected_rps=expected_rps,
                actual_rps=0.0,
                total_requests=total_requests,
                test_duration=0.0,
                wait_times=wait_times,
                success=False,
                error_message=str(e)
            )

        final_time = time.perf_counter()
        actual_duration = final_time - start_time
        actual_rps = total_requests / actual_duration

        # 성공 기준: 실제 RPS가 예상 RPS의 80% 이상이고 110% 이하
        success = (expected_rps * 0.8) <= actual_rps <= (expected_rps * 1.1)

        result = EndpointTestResult(
            endpoint=endpoint,
            method=method,
            expected_group=expected_group.value,
            expected_rps=expected_rps,
            actual_rps=actual_rps,
            total_requests=total_requests,
            test_duration=actual_duration,
            wait_times=wait_times,
            success=success
        )

        print(f"   결과: {actual_rps:.2f} RPS (목표: {expected_rps:.2f}) - {'✅' if success else '❌'}")

        return result


async def test_mixed_endpoint_scenario():
    """복합 엔드포인트 시나리오 테스트"""

    print("=" * 90)
    print("🎯 업비트 Rate Limiter 엔드포인트별 제한 검증")
    print("=" * 90)

    tester = EndpointRateLimitTester()

    # 테스트 시나리오 정의
    test_scenarios = [
        # Public API (높은 제한)
        ("/market/all", "GET", 30.0, "QUOTATION"),
        ("/ticker", "GET", 30.0, "QUOTATION"),
        ("/candles/minutes/1", "GET", 30.0, "QUOTATION"),

        # Private API - Exchange Default (30 RPS)
        ("/accounts", "GET", 30.0, "EXCHANGE_DEFAULT"),
        ("/orders/chance", "GET", 30.0, "EXCHANGE_DEFAULT"),
        ("/orders", "GET", 30.0, "EXCHANGE_DEFAULT"),  # GET은 30 RPS

        # Private API - Order (8 RPS)
        ("/orders", "POST", 8.0, "ORDER"),              # POST는 8 RPS
        ("/orders", "DELETE", 8.0, "ORDER"),            # DELETE는 8 RPS

        # Private API - Order Cancel All (0.5 RPS)
        ("/orders/cancel_all", "DELETE", 0.5, "ORDER_CANCEL_ALL"),
    ]

    results = []

    print(f"\n📋 테스트 대상: {len(test_scenarios)}개 엔드포인트")
    print("엔드포인트                | 메서드 | 예상그룹        | 목표RPS | 실제RPS | 성공")
    print("-" * 80)

    for endpoint, method, expected_rps, expected_group_name in test_scenarios:
        try:
            # 개별 테스트 실행 (짧은 시간으로)
            result = await tester.test_single_endpoint(
                endpoint=endpoint,
                method=method,
                expected_rps=expected_rps,
                test_duration=8.0,  # 8초 테스트
                request_count=min(int(expected_rps * 10), 50)  # 최대 50회
            )

            results.append(result)

            # 결과 출력
            endpoint_short = endpoint[:24].ljust(24)
            method_short = method.ljust(6)
            group_short = result.expected_group[:14].ljust(14)
            expected_str = f"{expected_rps:.1f}".rjust(7)
            actual_str = f"{result.actual_rps:.2f}".rjust(7)
            status = "✅" if result.success else "❌"

            print(f"{endpoint_short} | {method_short} | {group_short} | {expected_str} | {actual_str} | {status}")

            # 엔드포인트 간 휴식 (서로 영향 최소화)
            await asyncio.sleep(1.0)

        except Exception as e:
            print(f"❌ {endpoint} [{method}] 테스트 실패: {e}")
            results.append(EndpointTestResult(
                endpoint=endpoint, method=method, expected_group=expected_group_name,
                expected_rps=expected_rps, actual_rps=0.0, total_requests=0,
                test_duration=0.0, wait_times=[], success=False, error_message=str(e)
            ))

    # 📊 종합 분석
    print("\n" + "=" * 90)
    print("📊 엔드포인트별 Rate Limiting 검증 결과")
    print("=" * 90)

    success_count = sum(1 for r in results if r.success)
    total_count = len(results)

    print(f"\n✅ 성공: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

    if success_count < total_count:
        print(f"\n❌ 실패한 테스트:")
        for result in results:
            if not result.success:
                print(f"   - {result.endpoint} [{result.method}]: "
                      f"예상 {result.expected_rps:.1f} RPS vs 실제 {result.actual_rps:.2f} RPS")
                if result.error_message:
                    print(f"     오류: {result.error_message}")

    # 🔍 그룹별 분석
    group_analysis = {}
    for result in results:
        group = result.expected_group
        if group not in group_analysis:
            group_analysis[group] = []
        group_analysis[group].append(result)

    print(f"\n🔍 그룹별 분석:")
    for group, group_results in group_analysis.items():
        group_success = sum(1 for r in group_results if r.success)
        group_total = len(group_results)
        avg_accuracy = sum(r.actual_rps / r.expected_rps for r in group_results if r.expected_rps > 0) / group_total

        print(f"   {group}: {group_success}/{group_total} 성공, 평균 정확도 {avg_accuracy*100:.1f}%")

    # 💡 권장사항
    if success_count == total_count:
        print(f"\n🎉 모든 엔드포인트가 올바른 Rate Limiting을 적용하고 있습니다!")
        print(f"   - 0.5 RPS (ORDER_CANCEL_ALL) ✅")
        print(f"   - 8 RPS (ORDER) ✅")
        print(f"   - 30 RPS (QUOTATION, EXCHANGE_DEFAULT) ✅")
    else:
        print(f"\n⚠️  일부 엔드포인트에서 Rate Limiting 문제가 발견되었습니다.")
        print(f"   코드 검토 및 수정이 필요합니다.")


async def test_concurrent_mixed_endpoints():
    """동시 다발적 혼합 엔드포인트 테스트"""

    print("\n" + "=" * 90)
    print("🔀 동시 다발적 혼합 엔드포인트 테스트")
    print("=" * 90)
    print("목적: 서로 다른 RPS 제한의 엔드포인트들이 동시에 호출될 때 올바르게 분리되는지 확인")

    async def client_task(client_id: int, endpoint: str, method: str, requests: int) -> Dict[str, float]:
        """개별 클라이언트 작업"""
        limiter = UpbitRateLimiter(client_id=f"mixed_client_{client_id}")

        start_time = time.perf_counter()

        for i in range(requests):
            await limiter.acquire(endpoint, method)

            if (i + 1) % max(1, requests // 3) == 0:
                elapsed = time.perf_counter() - start_time
                current_rps = (i + 1) / elapsed
                print(f"   클라이언트-{client_id} ({endpoint}): {i+1}/{requests}, {current_rps:.2f} RPS")

        end_time = time.perf_counter()
        duration = end_time - start_time

        return {
            'client_id': client_id,
            'endpoint': endpoint,
            'method': method,
            'requests': requests,
            'duration': duration,
            'rps': requests / duration
        }

    # 🚀 동시 실행: 다양한 RPS 제한 혼합
    tasks = [
        client_task(1, "/orders/cancel_all", "DELETE", 5),    # 0.5 RPS
        client_task(2, "/orders", "POST", 30),                # 8 RPS
        client_task(3, "/accounts", "GET", 60),               # 30 RPS
        client_task(4, "/ticker", "GET", 60),                 # 30 RPS
        client_task(5, "/orders", "DELETE", 30),              # 8 RPS
    ]

    print(f"🚀 5개 클라이언트 동시 실행...")

    start_time = time.perf_counter()
    results = await asyncio.gather(*tasks)
    end_time = time.perf_counter()

    print(f"\n📊 동시 실행 결과 (총 {end_time - start_time:.1f}초):")
    print("클라이언트 | 엔드포인트           | 메서드 | 요청수 | 실제RPS | 예상RPS | 성공")
    print("-" * 80)

    expected_rps_map = {
        "/orders/cancel_all": 0.5,
        "/orders": 8.0,  # POST/DELETE
        "/accounts": 30.0,
        "/ticker": 30.0
    }

    for result in results:
        endpoint = result['endpoint']
        method = result['method']

        # 예상 RPS 결정
        if endpoint == "/orders" and method in ["POST", "DELETE"]:
            expected_rps = 8.0
        else:
            expected_rps = expected_rps_map.get(endpoint, 10.0)

        actual_rps = result['rps']
        success = (expected_rps * 0.7) <= actual_rps <= (expected_rps * 1.2)

        client_str = f"클라이언트-{result['client_id']}".ljust(10)
        endpoint_str = endpoint[:19].ljust(19)
        method_str = method.ljust(6)
        requests_str = str(result['requests']).rjust(6)
        actual_str = f"{actual_rps:.2f}".rjust(7)
        expected_str = f"{expected_rps:.1f}".rjust(7)
        status = "✅" if success else "❌"

        print(f"{client_str} | {endpoint_str} | {method_str} | {requests_str} | {actual_str} | {expected_str} | {status}")

    # 성공률 계산
    successes = sum(1 for result in results
                   if (expected_rps_map.get(result['endpoint'], 8.0 if result['endpoint'] == "/orders" else 10.0) * 0.7)
                   <= result['rps'] <=
                   (expected_rps_map.get(result['endpoint'], 8.0 if result['endpoint'] == "/orders" else 10.0) * 1.2))

    print(f"\n🎯 동시 실행 성공률: {successes}/{len(results)} ({successes/len(results)*100:.1f}%)")

    if successes == len(results):
        print("✅ 모든 엔드포인트가 동시 실행에서도 올바른 Rate Limiting을 유지합니다!")
    else:
        print("⚠️  동시 실행에서 일부 엔드포인트의 Rate Limiting이 간섭받았습니다.")


if __name__ == "__main__":
    print("💻 업비트 Rate Limiter 엔드포인트별 제한 완전 검증")
    print("=" * 90)

    asyncio.run(test_mixed_endpoint_scenario())
    asyncio.run(test_concurrent_mixed_endpoints())
