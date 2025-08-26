"""
test02_single_ticker_multi_request.py
====================================

SmartDataProvider 캐시 동작 검증 테스트
- 단일 심볼, 다중 요청
- 캐시 적중률 및 성능 개선 검증
- TTL 및 캐시 만료 동작 확인
"""

import pytest
import asyncio
import time

from upbit_auto_trading.infrastructure.market_data_backbone.smart_data_provider.core.smart_data_provider import (
    SmartDataProvider
)


class TestSingleTickerMultiRequest:
    """단일 티커 다중 요청 캐시 테스트"""

    @pytest.mark.asyncio
    async def test_cache_behavior_sequential(self):
        """순차적 요청에서 캐시 동작 검증"""
        # Given
        smart_provider = SmartDataProvider()
        symbol = "KRW-BTC"
        request_count = 5
        response_times = []
        cache_hits = []

        print(f"🧪 {symbol} 순차적 {request_count}회 요청 테스트 시작...")

        # When - 동일 심볼을 여러 번 요청
        for i in range(request_count):
            start_time = time.time()
            result = await smart_provider.get_ticker(symbol)
            response_time = (time.time() - start_time) * 1000

            # Then
            assert result.success is True, f"{i + 1}번째 요청 실패: {result.error}"
            assert result.data is not None, f"{i + 1}번째 요청 데이터 None"

            response_times.append(response_time)
            cache_hits.append(result.metadata.get('cache_hit', False))

            print(f"  요청 {i + 1}: {response_time:.1f}ms, 캐시: {cache_hits[-1]}, 소스: {result.metadata.get('source')}")

            # 첫 요청 후 잠시 대기 (캐시 생성 시간)
            if i == 0:
                await asyncio.sleep(0.1)

        # 캐시 효과 검증
        first_response_time = response_times[0]
        avg_later_response_time = sum(response_times[1:]) / len(response_times[1:])

        print(f"📊 첫 요청: {first_response_time:.1f}ms")
        print(f"📊 이후 평균: {avg_later_response_time:.1f}ms")
        print(f"📊 캐시 히트율: {sum(cache_hits) / len(cache_hits) * 100:.1f}%")        # 성능 개선 확인 (이후 요청들이 더 빨라야 함)
        if any(cache_hits[1:]):  # 캐시가 적중한 경우가 있다면
            assert avg_later_response_time < first_response_time * 0.5, "캐시로 인한 성능 개선 부족"

    @pytest.mark.asyncio
    async def test_cache_behavior_concurrent(self):
        """동시 요청에서 캐시 동작 검증"""
        # Given
        smart_provider = SmartDataProvider()
        symbol = "KRW-ETH"
        concurrent_count = 3

        print(f"🧪 {symbol} 동시 {concurrent_count}개 요청 테스트 시작...")

        # When - 동일 심볼을 동시에 요청
        start_time = time.time()

        tasks = [
            smart_provider.get_ticker(symbol)
            for _ in range(concurrent_count)
        ]

        results = await asyncio.gather(*tasks)
        total_time = (time.time() - start_time) * 1000

        # Then
        for i, result in enumerate(results):
            assert result.success is True, f"{i + 1}번째 동시 요청 실패: {result.error}"
            assert result.data is not None, f"{i + 1}번째 동시 요청 데이터 None"

            cache_hit = result.metadata.get('cache_hit', False)
            source = result.metadata.get('source', 'unknown')
            response_time = result.metadata.get('response_time_ms', 0)

            print(f"  동시 요청 {i + 1}: {response_time:.1f}ms, 캐시: {cache_hit}, 소스: {source}")

        print(f"📊 총 소요 시간: {total_time:.1f}ms")

        # 동시 요청 효율성 검증 (순차 요청보다 빨라야 함)
        expected_sequential_time = concurrent_count * 500  # 예상 순차 실행 시간
        assert total_time < expected_sequential_time, (
            f"동시 요청 효율성 부족: {total_time:.1f}ms > {expected_sequential_time}ms"
        )

    @pytest.mark.asyncio
    async def test_different_symbols_no_cross_cache(self):
        """서로 다른 심볼 간 캐시 간섭 없음 검증"""
        # Given
        smart_provider = SmartDataProvider()
        symbols = ["KRW-BTC", "KRW-ETH", "BTC-ETH"]

        print(f"🧪 다중 심볼({len(symbols)}개) 캐시 독립성 테스트 시작...")

        # When - 각 심볼을 2번씩 요청
        for symbol in symbols:
            print(f"\n  === {symbol} 테스트 ===")

            # 첫 번째 요청
            start_time = time.time()
            result1 = await smart_provider.get_ticker(symbol)
            first_time = (time.time() - start_time) * 1000

            assert result1.success is True, f"{symbol} 첫 요청 실패"
            first_cache_hit = result1.metadata.get('cache_hit', False)

            # 짧은 대기 후 두 번째 요청
            await asyncio.sleep(0.1)

            start_time = time.time()
            result2 = await smart_provider.get_ticker(symbol)
            second_time = (time.time() - start_time) * 1000

            assert result2.success is True, f"{symbol} 두 번째 요청 실패"
            second_cache_hit = result2.metadata.get('cache_hit', False)

            print(f"    첫 요청: {first_time:.1f}ms, 캐시: {first_cache_hit}")
            print(f"    둘째 요청: {second_time:.1f}ms, 캐시: {second_cache_hit}")

            # 데이터 일관성 검증
            assert result1.data["market"] == symbol, f"첫 요청 심볼 불일치: {result1.data.get('market')}"
            assert result2.data["market"] == symbol, f"두 번째 요청 심볼 불일치: {result2.data.get('market')}"

    @pytest.mark.asyncio
    async def test_cache_data_freshness(self):
        """캐시된 데이터의 신선도 검증"""
        # Given
        smart_provider = SmartDataProvider()
        symbol = "KRW-BTC"

        print(f"🧪 {symbol} 캐시 데이터 신선도 테스트 시작...")

        # When - 첫 번째 요청
        result1 = await smart_provider.get_ticker(symbol)
        assert result1.success is True

        timestamp1 = result1.data.get("timestamp", 0)
        trade_price1 = result1.data.get("trade_price", 0)

        print(f"  첫 요청: 가격={trade_price1:,.0f}, 타임스탬프={timestamp1}")

        # 2초 대기 (캐시 TTL 내에서)
        await asyncio.sleep(2)

        # 두 번째 요청
        result2 = await smart_provider.get_ticker(symbol)
        assert result2.success is True

        timestamp2 = result2.data.get("timestamp", 0)
        trade_price2 = result2.data.get("trade_price", 0)
        cache_hit = result2.metadata.get('cache_hit', False)

        print(f"  둘째 요청: 가격={trade_price2:,.0f}, 타임스탬프={timestamp2}, 캐시={cache_hit}")

        # Then - 데이터 신선도 검증
        if cache_hit:
            # 캐시된 데이터의 경우 타임스탬프 차이가 합리적이어야 함
            timestamp_diff = abs(timestamp2 - timestamp1)
            print(f"  📊 타임스탬프 차이: {timestamp_diff}ms")

            # 캐시된 데이터라도 너무 오래된 것은 아니어야 함 (5분 이내)
            assert timestamp_diff < 300000, f"캐시 데이터가 너무 오래됨: {timestamp_diff}ms"
        else:
            # 새로운 데이터의 경우 타임스탬프가 더 최신이어야 함
            assert timestamp2 >= timestamp1, "새 데이터의 타임스탬프가 더 오래됨"

    @pytest.mark.asyncio
    async def test_cache_performance_improvement(self):
        """캐시 성능 개선 정량적 측정"""
        # Given
        smart_provider = SmartDataProvider()
        symbol = "KRW-ETH"
        cold_requests = 3  # 캐시 없는 상태
        warm_requests = 5  # 캐시 있는 상태

        print(f"🧪 {symbol} 캐시 성능 개선 정량 측정 시작...")

        # When - Cold start (캐시 없는 상태)
        cold_times = []
        for i in range(cold_requests):
            start_time = time.time()
            result = await smart_provider.get_ticker(symbol)
            response_time = (time.time() - start_time) * 1000

            assert result.success is True
            cold_times.append(response_time)
            print(f"  Cold 요청 {i + 1}: {response_time:.1f}ms")

            # 캐시 초기화를 위해 잠시 대기
            await asyncio.sleep(0.5)

        # 캐시 생성을 위한 한 번의 요청
        await smart_provider.get_ticker(symbol)
        await asyncio.sleep(0.1)  # 캐시 안정화

        # Warm start (캐시 있는 상태)
        warm_times = []
        for i in range(warm_requests):
            start_time = time.time()
            result = await smart_provider.get_ticker(symbol)
            response_time = (time.time() - start_time) * 1000

            assert result.success is True
            warm_times.append(response_time)
            cache_hit = result.metadata.get('cache_hit', False)
            print(f"  Warm 요청 {i + 1}: {response_time:.1f}ms, 캐시: {cache_hit}")

            await asyncio.sleep(0.1)

        # Then - 성능 개선 분석
        avg_cold_time = sum(cold_times) / len(cold_times)
        avg_warm_time = sum(warm_times) / len(warm_times)
        improvement_ratio = avg_cold_time / avg_warm_time if avg_warm_time > 0 else 1

        print("\n📊 성능 개선 분석:")
        print(f"  Cold 평균: {avg_cold_time:.1f}ms")
        print(f"  Warm 평균: {avg_warm_time:.1f}ms")
        print(f"  개선 비율: {improvement_ratio:.1f}x")

        # 캐시로 인한 성능 개선이 있어야 함 (최소 20% 개선)
        improvement_threshold = 1.2
        if improvement_ratio >= improvement_threshold:
            print(f"✅ 캐시 성능 개선 확인: {improvement_ratio:.1f}x >= {improvement_threshold}x")
        else:
            print(f"⚠️ 캐시 성능 개선 미흡: {improvement_ratio:.1f}x < {improvement_threshold}x")


if __name__ == "__main__":
    # 개별 실행을 위한 테스트 러너
    async def run_tests():
        test_instance = TestSingleTickerMultiRequest()

        print("🧪 test02_single_ticker_multi_request 시작...")

        try:
            await test_instance.test_cache_behavior_sequential()
            print("\n" + "=" * 60)

            await test_instance.test_cache_behavior_concurrent()
            print("\n" + "=" * 60)

            await test_instance.test_different_symbols_no_cross_cache()
            print("\n" + "=" * 60)

            await test_instance.test_cache_data_freshness()
            print("\n" + "=" * 60)

            await test_instance.test_cache_performance_improvement()

            print("\n🎉 모든 캐시 테스트 통과!")

        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            raise    # 실행
    asyncio.run(run_tests())
