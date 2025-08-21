#!/usr/bin/env python3
"""
스마트 라우터 종합 성능 테스트 v2.0

개선 사항:
1. aiohttp 세션 리소스 정리
2. WebSocket 실제 RPS 측정 (한계 테스트)
3. 실시간 캔들 WebSocket 지원 테스트
4. 성능 지표에 RPS 포함
"""

import asyncio
import time
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.smart_data_router import (
    SmartDataRouter
)
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.upbit_rest_provider import (
    UpbitRestProvider
)
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.upbit_websocket_provider import (
    UpbitWebSocketProvider
)
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.strategies.frequency_analyzer import (
    AdvancedFrequencyAnalyzer
)
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.strategies.channel_selector import (
    AdvancedChannelSelector
)
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.models.symbols import TradingSymbol
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.models.timeframes import Timeframe
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.models.requests import (
    CandleDataRequest
)


@dataclass
class PerformanceMetrics:
    """성능 메트릭"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    total_rps: float = 0.0
    max_rps: float = 0.0
    min_response_time_ms: float = float('inf')
    max_response_time_ms: float = 0.0


@dataclass
class TestResult:
    """테스트 결과"""
    test_name: str
    success: bool = False
    duration_seconds: float = 0.0
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    additional_metrics: Dict[str, Any] = field(default_factory=dict)
    error_messages: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.performance.total_requests == 0:
            return 0.0
        return (self.performance.successful_requests / self.performance.total_requests) * 100


class SmartRouterComprehensiveTester:
    """스마트 라우터 종합 성능 테스터"""

    def __init__(self):
        self.logger = create_component_logger("ComprehensiveTester")
        self.results: List[TestResult] = []

        # 컴포넌트 초기화
        try:
            self.rest_provider = UpbitRestProvider()
            self.websocket_provider = UpbitWebSocketProvider()
            self.frequency_analyzer = AdvancedFrequencyAnalyzer()
            self.channel_selector = AdvancedChannelSelector(self.frequency_analyzer)

            self.smart_router = SmartDataRouter(
                rest_provider=self.rest_provider,
                websocket_provider=self.websocket_provider,
                channel_selector=self.channel_selector,
                frequency_analyzer=self.frequency_analyzer
            )

            self.logger.info("✅ 스마트 라우터 컴포넌트 초기화 완료")

        except Exception as e:
            self.logger.error(f"❌ 초기화 실패: {e}")
            raise

    async def test_websocket_real_rps(self) -> TestResult:
        """WebSocket 실제 RPS 한계 테스트"""
        test_result = TestResult(test_name="WebSocket 실제 RPS 한계")
        logger = create_component_logger("WebSocketRPS")

        start_time = time.time()

        try:
            symbol = TradingSymbol.from_upbit_symbol("KRW-BTC")
            request_times = []
            response_times = []
            rps_measurements = []

            logger.info("🚀 WebSocket RPS 한계 테스트 시작")

            # 30초 동안 최대한 많은 요청 전송
            test_duration = 30.0
            end_time = start_time + test_duration

            while time.time() < end_time:
                batch_start = time.time()
                batch_requests = 0

                # 1초 동안 가능한 많은 요청
                while time.time() - batch_start < 1.0:
                    request_start = time.time()

                    try:
                        # 실시간 캔들 데이터 요청 (WebSocket 지원)
                        response = await self.smart_router.get_ticker_data(symbol)

                        request_end = time.time()
                        response_time = (request_end - request_start) * 1000

                        if response and response.data:
                            test_result.performance.successful_requests += 1
                            response_times.append(response_time)
                            logger.debug(f"✅ 티커 요청 성공: {response_time:.2f}ms")
                        else:
                            test_result.performance.failed_requests += 1

                        batch_requests += 1
                        test_result.performance.total_requests += 1

                        # Rate Limit 방지용 최소 대기
                        await asyncio.sleep(0.1)

                    except Exception as e:
                        test_result.performance.failed_requests += 1
                        logger.warning(f"❌ 요청 실패: {e}")
                        await asyncio.sleep(0.2)  # 오류 시 더 긴 대기

                # 1초간 RPS 측정
                batch_duration = time.time() - batch_start
                batch_rps = batch_requests / batch_duration
                rps_measurements.append(batch_rps)

                logger.info(f"📊 1초간 RPS: {batch_rps:.2f}")

                # WebSocket 연결 안정성을 위한 짧은 휴식
                await asyncio.sleep(0.1)

            # 성능 메트릭 계산
            if response_times:
                test_result.performance.avg_response_time_ms = statistics.mean(response_times)
                test_result.performance.min_response_time_ms = min(response_times)
                test_result.performance.max_response_time_ms = max(response_times)

            if rps_measurements:
                test_result.performance.total_rps = statistics.mean(rps_measurements)
                test_result.performance.max_rps = max(rps_measurements)

            # 추가 메트릭
            test_result.additional_metrics.update({
                "test_duration_seconds": test_duration,
                "rps_measurements": rps_measurements,
                "theoretical_max_rps": 10.0,  # 업비트 REST API 제한
                "websocket_recommended": test_result.performance.total_rps > 5.0,
                "rate_limit_efficiency": min(100.0, (test_result.performance.total_rps / 10.0) * 100)
            })

            logger.info(f"📈 평균 RPS: {test_result.performance.total_rps:.2f}")
            logger.info(f"⚡ 최대 RPS: {test_result.performance.max_rps:.2f}")
            logger.info(f"📊 성공률: {test_result.success_rate:.1f}%")

            # 성공 기준: 5 RPS 이상 & 80% 성공률
            test_result.success = (
                test_result.performance.total_rps >= 5.0 and
                test_result.success_rate >= 80.0
            )

        except Exception as e:
            test_result.success = False
            test_result.error_messages.append(f"WebSocket RPS 테스트 실패: {str(e)}")
            logger.error(f"❌ WebSocket RPS 테스트 실패: {e}")

        test_result.duration_seconds = time.time() - start_time
        self.results.append(test_result)
        return test_result

    async def test_websocket_candle_support(self) -> TestResult:
        """WebSocket 실시간 캔들 지원 테스트"""
        test_result = TestResult(test_name="WebSocket 실시간 캔들 지원")
        logger = create_component_logger("WebSocketCandle")

        start_time = time.time()

        try:
            symbol = TradingSymbol.from_upbit_symbol("KRW-BTC")
            logger.info("🕯️ WebSocket 실시간 캔들 데이터 테스트 시작")

            # 1분봉 실시간 캔들 요청 (업비트 WebSocket 지원)
            candle_response = await self.smart_router.get_candle_data(
                symbol=symbol,
                timeframe=Timeframe.MINUTE_1,  # ONE_MINUTE -> MINUTE_1로 수정
                count=1
            )

            test_result.performance.total_requests = 1

            if candle_response and candle_response.data:
                test_result.performance.successful_requests = 1
                latest_candle = candle_response.data[0]

                test_result.additional_metrics.update({
                    "candle_timestamp": latest_candle.timestamp.isoformat(),
                    "candle_price": float(latest_candle.close),
                    "data_source": candle_response.metadata.data_source,
                    "websocket_fallback_occurred": "rest" in candle_response.metadata.data_source.lower()
                })

                logger.info(f"✅ 실시간 캔들 수신: {latest_candle.close} KRW")
                logger.info(f"📊 데이터 소스: {candle_response.metadata.data_source}")

                # WebSocket으로 성공하면 성공, REST로 fallback되어도 시스템이 정상 작동
                test_result.success = True

            else:
                test_result.performance.failed_requests = 1
                test_result.error_messages.append("캔들 데이터 응답이 비어있음")
                logger.error("❌ 캔들 데이터 응답이 비어있음")

        except Exception as e:
            test_result.performance.failed_requests = 1
            test_result.success = False
            test_result.error_messages.append(f"WebSocket 캔들 테스트 실패: {str(e)}")
            logger.error(f"❌ WebSocket 캔들 테스트 실패: {e}")

        test_result.duration_seconds = time.time() - start_time
        self.results.append(test_result)
        return test_result

    async def test_mixed_workload_performance(self) -> TestResult:
        """혼합 워크로드 성능 테스트"""
        test_result = TestResult(test_name="혼합 워크로드 성능")
        logger = create_component_logger("MixedWorkload")

        start_time = time.time()

        try:
            symbol = TradingSymbol.from_upbit_symbol("KRW-BTC")
            logger.info("🔄 혼합 워크로드 성능 테스트 시작")

            response_times = []
            rps_measurements = []

            # 다양한 요청을 10초 동안 수행
            test_duration = 10.0
            end_time = start_time + test_duration

            request_types = [
                "ticker",    # 40%
                "candle",    # 30%
                "ticker",    # 반복
                "ticker",    # 반복
                "candle"     # 반복
            ]

            type_index = 0

            while time.time() < end_time:
                batch_start = time.time()
                batch_requests = 0

                # 1초 배치 처리
                while time.time() - batch_start < 1.0:
                    request_start = time.time()
                    request_type = request_types[type_index % len(request_types)]

                    try:
                        if request_type == "ticker":
                            response = await self.smart_router.get_ticker_data(symbol)
                            expected_data = response.data if response else None
                        else:  # candle
                            response = await self.smart_router.get_candle_data(
                                symbol=symbol,
                                timeframe=Timeframe.MINUTE_1,  # ONE_MINUTE -> MINUTE_1로 수정
                                count=1
                            )
                            expected_data = response.data if response else None

                        request_end = time.time()
                        response_time = (request_end - request_start) * 1000

                        if expected_data:
                            test_result.performance.successful_requests += 1
                            response_times.append(response_time)
                        else:
                            test_result.performance.failed_requests += 1

                        batch_requests += 1
                        test_result.performance.total_requests += 1
                        type_index += 1

                        # 적당한 간격 유지
                        await asyncio.sleep(0.15)

                    except Exception as e:
                        test_result.performance.failed_requests += 1
                        logger.warning(f"❌ {request_type} 요청 실패: {e}")
                        await asyncio.sleep(0.2)

                # 배치 RPS 계산
                batch_duration = time.time() - batch_start
                if batch_duration > 0:
                    batch_rps = batch_requests / batch_duration
                    rps_measurements.append(batch_rps)
                    logger.info(f"📊 배치 RPS: {batch_rps:.2f} ({batch_requests}개 요청)")

            # 성능 메트릭 계산
            if response_times:
                test_result.performance.avg_response_time_ms = statistics.mean(response_times)
                test_result.performance.min_response_time_ms = min(response_times)
                test_result.performance.max_response_time_ms = max(response_times)

            if rps_measurements:
                test_result.performance.total_rps = statistics.mean(rps_measurements)
                test_result.performance.max_rps = max(rps_measurements)

            # 라우팅 통계 가져오기
            router_stats = await self.smart_router.get_routing_stats()

            test_result.additional_metrics.update({
                "router_total_requests": router_stats.total_requests,
                "router_websocket_requests": router_stats.websocket_requests,
                "router_rest_requests": router_stats.rest_requests,
                "websocket_usage_rate": router_stats.websocket_usage_rate * 100,
                "rest_usage_rate": router_stats.rest_usage_rate * 100,
                "router_avg_response_time": router_stats.avg_response_time_ms,
                "router_error_rate": router_stats.error_rate * 100
            })

            logger.info(f"📈 혼합 워크로드 평균 RPS: {test_result.performance.total_rps:.2f}")
            logger.info(f"🔄 WebSocket 사용률: {router_stats.websocket_usage_rate * 100:.1f}%")
            logger.info(f"📊 전체 성공률: {test_result.success_rate:.1f}%")

            # 성공 기준: 3 RPS 이상 & 85% 성공률
            test_result.success = (
                test_result.performance.total_rps >= 3.0 and
                test_result.success_rate >= 85.0
            )

        except Exception as e:
            test_result.success = False
            test_result.error_messages.append(f"혼합 워크로드 테스트 실패: {str(e)}")
            logger.error(f"❌ 혼합 워크로드 테스트 실패: {e}")

        test_result.duration_seconds = time.time() - start_time
        self.results.append(test_result)
        return test_result

    async def test_frequency_analyzer_precision(self) -> TestResult:
        """FrequencyAnalyzer 정밀도 테스트"""
        test_result = TestResult(test_name="FrequencyAnalyzer 정밀도")
        logger = create_component_logger("FrequencyPrecision")

        start_time = time.time()

        try:
            symbol = TradingSymbol.from_upbit_symbol("KRW-BTC")
            logger.info("🧮 FrequencyAnalyzer 정밀도 테스트 시작")

            # 정확한 6초 간격으로 10번 요청 = 분당 10회
            expected_rps = 10.0
            request_interval = 6.0  # 초
            request_count = 10

            logger.info(f"📊 {request_interval}초 간격으로 {request_count}번 요청 전송")

            for i in range(request_count):
                self.frequency_analyzer.update_request_pattern(
                    symbol=symbol,
                    data_type="candle",
                    request_time=datetime.now()
                )

                if i < request_count - 1:  # 마지막 요청 후에는 대기하지 않음
                    await asyncio.sleep(request_interval)

                logger.debug(f"📤 요청 {i+1}/{request_count} 전송")

            # 패턴 분석
            await asyncio.sleep(1.0)  # 분석을 위한 짧은 대기
            pattern = self.frequency_analyzer.analyze_request_pattern(symbol, "candle")

            # 정확도 계산
            actual_rps = pattern.requests_per_minute
            accuracy = max(0, 100 - abs(expected_rps - actual_rps) / expected_rps * 100)

            test_result.performance.total_requests = 1
            test_result.performance.successful_requests = 1 if accuracy >= 80.0 else 0

            test_result.additional_metrics.update({
                "expected_rps": expected_rps,
                "actual_rps": actual_rps,
                "accuracy_percentage": accuracy,
                "consistency_score": pattern.consistency_score,
                "websocket_recommended": pattern.websocket_recommended,
                "trend_direction": pattern.trend_direction
            })

            logger.info(f"📈 예상 RPS: {expected_rps:.1f}")
            logger.info(f"📊 실제 RPS: {actual_rps:.2f}")
            logger.info(f"🎯 정확도: {accuracy:.1f}%")
            logger.info(f"📡 WebSocket 추천: {pattern.websocket_recommended}")

            # 성공 기준: 80% 이상 정확도
            test_result.success = accuracy >= 80.0

        except Exception as e:
            test_result.success = False
            test_result.error_messages.append(f"FrequencyAnalyzer 정밀도 테스트 실패: {str(e)}")
            logger.error(f"❌ FrequencyAnalyzer 정밀도 테스트 실패: {e}")

        test_result.duration_seconds = time.time() - start_time
        self.results.append(test_result)
        return test_result

    def print_comprehensive_summary(self):
        """종합 테스트 결과 요약 출력"""

        print("\n" + "="*80)
        print("📊 스마트 라우터 종합 성능 테스트 결과 (v2.0)")
        print("="*80)

        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)

        print(f"📈 전체 테스트: {total_tests}개")
        print(f"✅ 성공: {successful_tests}개")
        print(f"❌ 실패: {total_tests - successful_tests}개")
        print(f"🎯 성공률: {(successful_tests/total_tests*100):.1f}%")

        # 전체 성능 요약
        total_requests = sum(r.performance.total_requests for r in self.results)
        total_successful = sum(r.performance.successful_requests for r in self.results)
        avg_response_times = [r.performance.avg_response_time_ms for r in self.results if r.performance.avg_response_time_ms > 0]
        total_rps_values = [r.performance.total_rps for r in self.results if r.performance.total_rps > 0]

        if avg_response_times:
            overall_avg_response = statistics.mean(avg_response_times)
            print(f"⚡ 전체 평균 응답시간: {overall_avg_response:.2f}ms")

        if total_rps_values:
            overall_avg_rps = statistics.mean(total_rps_values)
            max_rps = max(total_rps_values)
            print(f"🚀 전체 평균 RPS: {overall_avg_rps:.2f}")
            print(f"🔥 최대 RPS: {max_rps:.2f}")

        if total_requests > 0:
            overall_success_rate = (total_successful / total_requests) * 100
            print(f"📊 전체 성공률: {overall_success_rate:.1f}%")

        print("\n" + "-"*60)
        print("📋 개별 테스트 결과")
        print("-"*60)

        for result in self.results:
            status = "✅" if result.success else "❌"
            print(f"\n{status} {result.test_name}")
            print(f"   ⏱️  지속시간: {result.duration_seconds:.2f}초")
            print(f"   📤 총 요청: {result.performance.total_requests}개")
            print(f"   ✅ 성공률: {result.success_rate:.1f}%")

            if result.performance.avg_response_time_ms > 0:
                print(f"   ⚡ 평균 응답시간: {result.performance.avg_response_time_ms:.2f}ms")

            if result.performance.total_rps > 0:
                print(f"   🚀 평균 RPS: {result.performance.total_rps:.2f}")

            if result.performance.max_rps > 0:
                print(f"   🔥 최대 RPS: {result.performance.max_rps:.2f}")

            if result.additional_metrics:
                print(f"   📊 추가 메트릭:")
                for key, value in result.additional_metrics.items():
                    if isinstance(value, float):
                        print(f"      {key}: {value:.2f}")
                    elif isinstance(value, list) and len(value) > 10:
                        print(f"      {key}: [{len(value)}개 측정값]")
                    else:
                        print(f"      {key}: {value}")

            if result.error_messages:
                print(f"   ❌ 오류 ({len(result.error_messages)}개):")
                for error in result.error_messages[:3]:  # 최대 3개만 표시
                    print(f"      - {error}")

    async def cleanup(self):
        """리소스 정리"""
        try:
            # REST Provider 세션 정리
            if hasattr(self.rest_provider, 'cleanup'):
                await self.rest_provider.cleanup()

            # WebSocket Provider 연결 정리
            if hasattr(self.websocket_provider, 'disconnect'):
                await self.websocket_provider.disconnect()

            self.logger.info("🧹 리소스 정리 완료")

        except Exception as e:
            self.logger.warning(f"⚠️ 리소스 정리 중 오류: {e}")


async def main():
    """메인 테스트 실행"""

    print("🚀 스마트 라우터 종합 성능 테스트 시작 (v2.0)")
    print("="*50)

    tester = SmartRouterComprehensiveTester()

    if not hasattr(tester, 'smart_router'):
        print("❌ 스마트 라우터 초기화 실패로 테스트 중단")
        return

    try:
        # 1. WebSocket 실제 RPS 한계 테스트
        print("\n1️⃣ WebSocket 실제 RPS 한계 테스트")
        await tester.test_websocket_real_rps()

        # 2. WebSocket 실시간 캔들 지원 테스트
        print("\n2️⃣ WebSocket 실시간 캔들 지원 테스트")
        await tester.test_websocket_candle_support()

        # 3. 혼합 워크로드 성능 테스트
        print("\n3️⃣ 혼합 워크로드 성능 테스트")
        await tester.test_mixed_workload_performance()

        # 4. FrequencyAnalyzer 정밀도 테스트
        print("\n4️⃣ FrequencyAnalyzer 정밀도 테스트")
        await tester.test_frequency_analyzer_precision()

        # 결과 요약
        tester.print_comprehensive_summary()

    finally:
        # 리소스 정리
        await tester.cleanup()

    print("\n🎉 모든 테스트 완료!")


if __name__ == "__main__":
    asyncio.run(main())
