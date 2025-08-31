"""
모든 Rate Limiting 전략 순차 테스트 - 실제 업비트 API 통신
"""

import asyncio
import time
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import UpbitRateLimiter, RateLimitStrategy
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient


async def test_strategy_with_real_api(strategy: RateLimitStrategy, test_count: int = 100):
    """실제 업비트 API를 사용한 전략 테스트"""
    print(f"\n🚀 전략: {strategy.name} ({test_count}회 실제 API 테스트)")
    print("=" * 60)

    # Rate Limiter와 실제 API 클라이언트 생성
    rate_limiter = UpbitRateLimiter(strategy=strategy)
    client = UpbitPublicClient(rate_limiter=rate_limiter)
    start_time = time.perf_counter()

    # 📊 추가 메트릭 추적을 위한 변수들
    api_response_times = []     # 순수 서버 응답 시간들 (RT)
    actual_intervals = []       # 실제 요청간 간격들 (AIR)
    request_start_times = []    # 요청 시작 시점들
    success_count = 0
    error_count = 0
    rate_limit_errors = 0

    for i in range(test_count):
        interval_start = time.perf_counter()
        request_start_times.append(interval_start)

        try:
            # 실제 업비트 API 호출 (마켓 정보 조회)
            markets = await client.get_market_all()
            interval_end = time.perf_counter()

            # 📊 메트릭 계산
            pure_api_time = client.get_last_http_response_time()    # 순수 서버 응답 시간 (RT)

            api_response_times.append(pure_api_time)
            success_count += 1

            # 실제 간격 계산 (이전 요청 완료부터 현재 요청 시작까지)
            if i > 0:
                actual_interval = (interval_start - request_start_times[i - 1]) * 1000
                actual_intervals.append(actual_interval)

            elapsed = interval_end - start_time
            current_rps = (i + 1) / elapsed if elapsed > 0 else 0

            # Rate limiter 상태 확인
            rate_status = client.get_rate_limit_status()
            global_count = rate_status.get('global', {}).get('current', 0)

            # 매 10회마다 상태 출력 + 추가 메트릭
            if (i + 1) % 10 == 0:
                avg_api_time = sum(api_response_times[-10:]) / min(10, len(api_response_times))
                market_count = len(markets) if markets else 0

                # 📊 추가 메트릭 계산
                recent_rt = api_response_times[-10:] if len(api_response_times) >= 10 else api_response_times
                recent_air = actual_intervals[-9:] if len(actual_intervals) >= 9 else actual_intervals  # 최근 9개 간격

                min_rt = min(recent_rt) if recent_rt else 0
                max_rt = max(recent_rt) if recent_rt else 0
                min_air = min(recent_air) if recent_air else 0
                max_air = max(recent_air) if recent_air else 0
                avg_air = sum(recent_air) / len(recent_air) if recent_air else 0

                print(f"요청 {i + 1:3d}/{test_count} | RT: {pure_api_time:6.1f}ms | "
                      f"평균RT: {avg_api_time:6.1f}ms | AIR: {avg_air:6.1f}ms | "
                      f"큐: {global_count:2d}/10 | RPS: {current_rps:5.1f} | 마켓: {market_count}")
                print(f"        📊 MinRT: {min_rt:5.1f}ms | MaxRT: {max_rt:5.1f}ms | "
                      f"MinAIR: {min_air:5.1f}ms | MaxAIR: {max_air:5.1f}ms")

        except Exception as e:
            interval_end = time.perf_counter()
            error_time = (interval_end - interval_start) * 1000
            api_response_times.append(error_time)  # 에러도 응답 시간으로 기록
            error_count += 1

            if "429" in str(e) or "Rate Limit" in str(e):
                rate_limit_errors += 1
                print(f"요청 {i + 1:3d}/{test_count} | ⚠️ 429 ERROR | {error_time:6.1f}ms | 에러: {str(e)[:50]}...")
            else:
                print(f"요청 {i + 1:3d}/{test_count} | ❌ API ERROR | {error_time:6.1f}ms | 에러: {str(e)[:50]}...")

    # 📊 최종 통계 계산 (새로운 메트릭 기반)
    total_time = time.perf_counter() - start_time
    final_rps = test_count / total_time

    # RT 메트릭 (순수 서버 응답 시간)
    avg_rt = sum(api_response_times) / len(api_response_times) if api_response_times else 0
    max_rt = max(api_response_times) if api_response_times else 0
    min_rt = min(api_response_times) if api_response_times else 0

    # AIR 메트릭 (실제 요청간 간격)
    avg_air = sum(actual_intervals) / len(actual_intervals) if actual_intervals else 0
    max_air = max(actual_intervals) if actual_intervals else 0
    min_air = min(actual_intervals) if actual_intervals else 0

    # 정리
    await client.close()

    print("-" * 60)
    print(f"📊 최종 결과: RPS {final_rps:.2f} | 평균RT {avg_rt:.1f}ms | "
          f"최대RT {max_rt:.1f}ms | 최소RT {min_rt:.1f}ms")
    print(f"📊 간격 메트릭: 평균AIR {avg_air:.1f}ms | "
          f"MinAIR {min_air:.1f}ms | MaxAIR {max_air:.1f}ms")
    print(f"🎯 성공률: {success_count}/{test_count} ({success_count / test_count * 100:.1f}%) | "
          f"429 에러: {rate_limit_errors}회 | 기타 에러: {error_count - rate_limit_errors}회")

    return {
        'strategy': strategy.name,
        'rps': final_rps,
        'avg_rt_ms': avg_rt,      # RT = Response Time (순수 서버 응답 시간)
        'max_rt_ms': max_rt,
        'min_rt_ms': min_rt,
        'avg_air_ms': avg_air,    # AIR = Actual Interval Rate (실제 요청간 간격)
        'min_air_ms': min_air,
        'max_air_ms': max_air,
        'total_time_s': total_time,
        'success_count': success_count,
        'rate_limit_errors': rate_limit_errors,
        'total_errors': error_count
    }


async def test_all_strategies():
    """모든 전략 순차 테스트"""
    print("🎯 모든 Rate Limiting 전략 순차 테스트")
    print("각 전략당 100회씩 테스트하여 성능 비교")
    print("=" * 80)

    strategies = [
        RateLimitStrategy.CLOUDFLARE_SLIDING_WINDOW,
        RateLimitStrategy.AIOLIMITER_OPTIMIZED,
        RateLimitStrategy.HYBRID_FAST,
        RateLimitStrategy.LEGACY_CONSERVATIVE,
        RateLimitStrategy.RESPONSE_INTERVAL_SIMPLE,
        RateLimitStrategy.SMART_RESPONSE_ADAPTIVE
    ]

    results = []

    for strategy in strategies:
        try:
            result = await test_strategy_with_real_api(strategy, 100)
            results.append(result)

            # 전략 간 간격
            print("\n⏳ 다음 전략 준비 중...\n")
            await asyncio.sleep(2)

        except Exception as e:
            print(f"❌ {strategy.name} 테스트 실패: {e}")

    # 전체 결과 요약
    print("\n" + "=" * 90)
    print("📈 전체 전략 성능 요약")
    print("=" * 90)
    print("전략명                    | RPS   | 평균RT  | MinRT   | MaxRT   | 평균AIR  | MinAIR  | MaxAIR  | 성공률")
    print("-" * 98)

    for result in results:
        name = result['strategy'][:22].ljust(22)
        rps = f"{result['rps']:.2f}".rjust(5)
        avg_rt = f"{result['avg_rt_ms']:.1f}ms".rjust(7)  # RT = Response Time
        min_rt = f"{result['min_rt_ms']:.1f}ms".rjust(7)
        max_rt = f"{result['max_rt_ms']:.1f}ms".rjust(7)
        avg_air = f"{result.get('avg_air_ms', 0):.1f}ms".rjust(8)  # AIR = Actual Interval Rate
        min_air = f"{result.get('min_air_ms', 0):.1f}ms".rjust(7)
        max_air = f"{result.get('max_air_ms', 0):.1f}ms".rjust(7)
        success_rate = f"{result['success_count'] / 100 * 100:.0f}%".rjust(6)

        print(f"{name} | {rps} | {avg_rt} | {min_rt} | {max_rt} | {avg_air} | {min_air} | {max_air} | {success_rate}")

    # 429 에러 요약
    print("\n📊 Rate Limiting 에러 현황:")
    total_429_errors = sum(r['rate_limit_errors'] for r in results)
    total_other_errors = sum(r['total_errors'] - r['rate_limit_errors'] for r in results)
    print(f"   전체 429 에러: {total_429_errors}회")
    print(f"   기타 에러: {total_other_errors}회")
    print(f"   전체 실패한 요청: {total_429_errors + total_other_errors}회")

    # 최고 성능 전략 표시
    if results:
        best_rps = max(results, key=lambda x: x['rps'])
        best_stability = min(results, key=lambda x: x['avg_rt_ms'])
        best_success = max(results, key=lambda x: x['success_count'])
        most_consistent_air = min(results, key=lambda x: abs(x.get('max_air_ms', 1000) - x.get('min_air_ms', 0)))

        print("\n🏆 성능 우수 전략:")
        print(f"   최고 RPS: {best_rps['strategy']} ({best_rps['rps']:.2f})")
        print(f"   최고 안정성: {best_stability['strategy']} ({best_stability['avg_rt_ms']:.1f}ms)")
        print(f"   최고 성공률: {best_success['strategy']} ({best_success['success_count']}/100)")
        print(f"   가장 일정한 간격: {most_consistent_air['strategy']} "
              f"(차이: {abs(most_consistent_air.get('max_air_ms', 0) - most_consistent_air.get('min_air_ms', 0)):.1f}ms)")

        # 업비트 기준 안전 전략 (10 RPS 이하, 429 에러 없음)
        safe_strategies = [r for r in results if r['rps'] <= 10.0 and r['rate_limit_errors'] == 0]
        if safe_strategies:
            best_safe = max(safe_strategies, key=lambda x: x['rps'])
            print(f"   업비트 안전 최고: {best_safe['strategy']} ({best_safe['rps']:.2f} RPS, 429에러 0회)")


if __name__ == "__main__":
    asyncio.run(test_all_strategies())
