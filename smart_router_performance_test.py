"""
스마트 라우터 성능 테스트
실제 구현된 스마트 라우터 기반 종합 성능 평가
"""
import asyncio
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import statistics
import logging
import traceback

# 스마트 라우터 관련 임포트
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.smart_data_router import SmartDataRouter
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.upbit_rest_provider import UpbitRestProvider
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.implementations.upbit_websocket_provider import UpbitWebSocketProvider
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.strategies.frequency_analyzer import AdvancedFrequencyAnalyzer
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.strategies.channel_selector import AdvancedChannelSelector
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.models.symbols import TradingSymbol
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.models.timeframes import Timeframe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TestResults:
    """테스트 결과 데이터 클래스"""

    test_name: str
    success: bool = False
    duration_seconds: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    websocket_usage_rate: float = 0.0
    rest_usage_rate: float = 0.0
    error_messages: List[str] = field(default_factory=list)
    additional_metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """성공률 (%)"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def requests_per_second(self) -> float:
        """초당 요청수"""
        if self.duration_seconds == 0:
            return 0.0
        return self.total_requests / self.duration_seconds


class SmartRouterPerformanceTester:
    """스마트 라우터 성능 테스터"""

    def __init__(self):
        self.results: List[TestResults] = []

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

            logger.info("✅ 스마트 라우터 컴포넌트 초기화 완료")

        except Exception as e:
            logger.error(f"❌ 컴포넌트 초기화 실패: {e}")
            logger.error(f"상세 오류: {traceback.format_exc()}")

    async def test_basic_performance(self) -> TestResults:
        """기본 성능 벤치마크 테스트"""

        test_result = TestResults("기본 성능 벤치마크")
        logger.info("🔧 기본 성능 벤치마크 테스트 시작")

        start_time = time.time()

        try:
            symbol = TradingSymbol.from_upbit_symbol("KRW-BTC")
            timeframe = Timeframe.MINUTE_1

            # 10번의 캔들 데이터 요청
            for i in range(10):
                try:
                    request_start = time.time()

                    # 스마트 라우터를 통한 데이터 요청
                    candle_data = await self.smart_router.get_candle_data(
                        symbol=symbol,
                        timeframe=timeframe,
                        count=100
                    )

                    request_duration = time.time() - request_start

                    test_result.total_requests += 1
                    if candle_data and hasattr(candle_data, 'data') and len(candle_data.data) > 0:
                        test_result.successful_requests += 1
                        test_result.avg_response_time += request_duration * 1000  # ms
                        logger.info(f"✅ 요청 {i+1}: {len(candle_data.data)}개 캔들, {request_duration*1000:.2f}ms")
                    else:
                        test_result.failed_requests += 1
                        test_result.error_messages.append(f"요청 {i+1}: 빈 응답")

                    # 짧은 대기 (Rate Limit 고려)
                    await asyncio.sleep(0.5)

                except Exception as e:
                    test_result.total_requests += 1
                    test_result.failed_requests += 1
                    test_result.error_messages.append(f"요청 {i+1} 실패: {str(e)}")
                    logger.error(f"❌ 요청 {i+1} 실패: {e}")

            # 평균 응답 시간 계산
            if test_result.successful_requests > 0:
                test_result.avg_response_time /= test_result.successful_requests

            test_result.duration_seconds = time.time() - start_time
            test_result.success = test_result.successful_requests > 0

            # 스마트 라우터 통계 수집
            stats = await self.smart_router.get_routing_stats()
            if stats:
                total_requests = stats.rest_requests + stats.websocket_requests
                if total_requests > 0:
                    test_result.rest_usage_rate = (stats.rest_requests / total_requests) * 100
                    test_result.websocket_usage_rate = (stats.websocket_requests / total_requests) * 100

                test_result.additional_metrics = {
                    "rest_requests": stats.rest_requests,
                    "websocket_requests": stats.websocket_requests,
                    "avg_response_time_ms": stats.avg_response_time_ms,
                    "error_rate": stats.error_rate
                }

        except Exception as e:
            test_result.success = False
            test_result.error_messages.append(f"테스트 전체 실패: {str(e)}")
            logger.error(f"❌ 기본 성능 테스트 실패: {e}")

        self.results.append(test_result)
        return test_result

    async def test_frequency_analyzer_accuracy(self) -> TestResults:
        """FrequencyAnalyzer 정확성 테스트"""

        test_result = TestResults("FrequencyAnalyzer 정확성")
        logger.info("🧮 FrequencyAnalyzer 정확성 테스트 시작")

        start_time = time.time()

        try:
            symbol = TradingSymbol.from_upbit_symbol("KRW-BTC")

            # 테스트 시나리오 1: 고빈도 요청 (분당 10회 시뮬레이션)
            logger.info("📊 고빈도 요청 패턴 시뮬레이션...")

            for i in range(10):  # 1분 동안 10번 요청
                self.frequency_analyzer.update_request_pattern(
                    symbol=symbol,
                    data_type="candle",
                    request_time=datetime.now()
                )
                await asyncio.sleep(6.0)  # 6초 간격 = 분당 10회

            # 패턴 분석
            pattern = self.frequency_analyzer.analyze_request_pattern(symbol, "candle")

            test_result.additional_metrics["high_frequency_rps"] = pattern.requests_per_minute
            test_result.additional_metrics["websocket_recommended"] = pattern.websocket_recommended
            test_result.additional_metrics["consistency_score"] = pattern.consistency_score

            # 예상값과 비교 (약 10 RPS 예상)
            expected_rps = 10.0
            actual_rps = pattern.requests_per_minute
            accuracy = 100 - abs(expected_rps - actual_rps) / expected_rps * 100

            test_result.additional_metrics["rps_accuracy"] = accuracy
            test_result.success = accuracy > 80  # 80% 이상 정확도면 성공

            logger.info(f"📈 고빈도 패턴 결과: {actual_rps:.2f} RPS (예상: {expected_rps})")
            logger.info(f"🎯 정확도: {accuracy:.1f}%")
            logger.info(f"📡 WebSocket 추천: {pattern.websocket_recommended}")

            test_result.total_requests = 1
            test_result.successful_requests = 1 if test_result.success else 0

        except Exception as e:
            test_result.success = False
            test_result.error_messages.append(f"FrequencyAnalyzer 테스트 실패: {str(e)}")
            logger.error(f"❌ FrequencyAnalyzer 테스트 실패: {e}")

        test_result.duration_seconds = time.time() - start_time
        self.results.append(test_result)
        return test_result

    async def test_channel_switching(self) -> TestResults:
        """채널 자동 전환 테스트"""

        test_result = TestResults("채널 자동 전환")
        logger.info("🔄 채널 자동 전환 테스트 시작")

        start_time = time.time()

        try:
            symbol = TradingSymbol.from_upbit_symbol("KRW-ETH")

            # 초기 저빈도 요청 (REST 예상)
            logger.info("📉 저빈도 요청 단계...")
            initial_channel = None

            for i in range(3):
                # 채널 선택 확인
                selected_channel = self.channel_selector.select_optimal_channel(
                    symbol=symbol,
                    data_type="ticker",
                    recent_request_count=i,  # 누락된 매개변수 추가
                    priority="normal"
                )

                if i == 0:
                    initial_channel = selected_channel

                logger.info(f"   요청 {i+1}: {selected_channel} 채널 선택")

                # 요청 시뮬레이션
                self.frequency_analyzer.update_request_pattern(
                    symbol=symbol,
                    data_type="ticker",
                    request_time=datetime.now(),
                    response_time_ms=150.0,
                    success=True
                )

                await asyncio.sleep(2)  # 저빈도 간격

            # 고빈도 요청으로 전환 (WebSocket 예상)
            logger.info("📈 고빈도 요청 단계...")

            for i in range(15):  # 빠른 간격으로 많은 요청
                # 채널 선택 재확인
                selected_channel = self.channel_selector.select_optimal_channel(
                    symbol=symbol,
                    data_type="ticker",
                    recent_request_count=10 + i,  # 고빈도 시뮬레이션
                    priority="high"
                )

                if i % 5 == 0:  # 5번마다 로그
                    logger.info(f"   요청 {i+1}: {selected_channel} 채널 선택")

                # 고빈도 요청 시뮬레이션
                self.frequency_analyzer.update_request_pattern(
                    symbol=symbol,
                    data_type="ticker",
                    request_time=datetime.now(),
                    response_time_ms=50.0,
                    success=True
                )

                await asyncio.sleep(0.2)  # 고빈도 간격

            # 최종 채널 확인
            final_channel = self.channel_selector.select_optimal_channel(
                symbol=symbol,
                data_type="ticker",
                recent_request_count=20,  # 최종 고빈도 상태
                priority="high"
            )

            # 채널 전환 검증
            channel_switched = initial_channel != final_channel

            test_result.additional_metrics = {
                "initial_channel": str(initial_channel),
                "final_channel": str(final_channel),
                "channel_switched": channel_switched
            }

            test_result.success = channel_switched  # 채널이 전환되었으면 성공
            test_result.total_requests = 18
            test_result.successful_requests = 18 if test_result.success else 0

            logger.info(f"🔄 채널 전환 결과: {initial_channel} → {final_channel}")
            logger.info(f"✅ 전환 성공: {channel_switched}")

        except Exception as e:
            test_result.success = False
            test_result.error_messages.append(f"채널 전환 테스트 실패: {str(e)}")
            logger.error(f"❌ 채널 전환 테스트 실패: {e}")

        test_result.duration_seconds = time.time() - start_time
        self.results.append(test_result)
        return test_result

    async def test_rate_limit_compliance(self) -> TestResults:
        """Rate Limit 준수 테스트"""

        test_result = TestResults("Rate Limit 준수")
        logger.info("🚦 Rate Limit 준수 테스트 시작")

        start_time = time.time()

        try:
            symbol = TradingSymbol.from_upbit_symbol("KRW-XRP")

            # 15개 요청을 빠르게 전송 (초당 10회 제한 테스트)
            logger.info("⚡ 빠른 연속 요청 테스트 (Rate Limit 검증)...")

            request_times = []

            for i in range(15):
                request_start = time.time()

                try:
                    # REST Provider를 통한 직접 요청 (Rate Limit 적용됨)
                    from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.models.requests import RequestFactory
                    ticker_request = RequestFactory.current_ticker(symbol)
                    ticker_data = await self.rest_provider.get_ticker_data(ticker_request)

                    request_end = time.time()
                    request_duration = request_end - request_start
                    request_times.append(request_duration)

                    test_result.total_requests += 1

                    if ticker_data and ticker_data.data:
                        test_result.successful_requests += 1
                        logger.info(f"✅ 요청 {i+1}: {ticker_data.data.current_price} KRW ({request_duration:.3f}s)")
                    else:
                        test_result.failed_requests += 1
                        logger.info(f"❌ 요청 {i+1}: 빈 응답")

                except Exception as e:
                    test_result.total_requests += 1
                    test_result.failed_requests += 1
                    test_result.error_messages.append(f"요청 {i+1}: {str(e)}")
                    logger.info(f"❌ 요청 {i+1}: 실패 - {str(e)}")

                # Rate Limit을 의도적으로 테스트하기 위해 짧은 간격
                await asyncio.sleep(0.05)  # 50ms 간격 (초당 20회 시도)

            # Rate Limit 동작 분석
            if request_times:
                avg_request_time = statistics.mean(request_times)
                max_request_time = max(request_times)

                test_result.avg_response_time = avg_request_time * 1000  # ms
                test_result.additional_metrics = {
                    "avg_request_time": avg_request_time,
                    "max_request_time": max_request_time,
                    "rate_limit_triggered": max_request_time > 1.0,  # 1초 이상이면 Rate Limit 의심
                    "request_time_variance": statistics.stdev(request_times) if len(request_times) > 1 else 0
                }

            # 성공률이 50% 이상이고 Rate Limit이 적절히 동작하면 성공
            test_result.success = (test_result.success_rate >= 50 and
                                 test_result.additional_metrics.get("rate_limit_triggered", False))

            logger.info(f"📊 Rate Limit 테스트 결과:")
            logger.info(f"   성공률: {test_result.success_rate:.1f}%")
            logger.info(f"   평균 응답시간: {test_result.avg_response_time:.1f}ms")
            logger.info(f"   Rate Limit 감지: {test_result.additional_metrics.get('rate_limit_triggered', False)}")

        except Exception as e:
            test_result.success = False
            test_result.error_messages.append(f"Rate Limit 테스트 실패: {str(e)}")
            logger.error(f"❌ Rate Limit 테스트 실패: {e}")

        test_result.duration_seconds = time.time() - start_time
        self.results.append(test_result)
        return test_result

    def print_test_summary(self):
        """테스트 결과 요약 출력"""

        print("\n" + "="*80)
        print("📊 스마트 라우터 성능 테스트 결과 요약")
        print("="*80)

        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)

        print(f"📈 전체 테스트: {total_tests}개")
        print(f"✅ 성공: {successful_tests}개")
        print(f"❌ 실패: {total_tests - successful_tests}개")
        print(f"🎯 성공률: {(successful_tests/total_tests*100):.1f}%")

        print("\n" + "-"*60)
        print("📋 개별 테스트 결과")
        print("-"*60)

        for result in self.results:
            status = "✅" if result.success else "❌"
            print(f"{status} {result.test_name}")
            print(f"   ⏱️  지속시간: {result.duration_seconds:.2f}초")
            print(f"   📤 총 요청: {result.total_requests}개")
            print(f"   ✅ 성공률: {result.success_rate:.1f}%")

            if result.avg_response_time > 0:
                print(f"   ⚡ 평균 응답시간: {result.avg_response_time:.1f}ms")

            if result.additional_metrics:
                print(f"   📊 추가 메트릭:")
                for key, value in result.additional_metrics.items():
                    print(f"      {key}: {value}")

            if result.error_messages:
                print(f"   ❌ 오류 ({len(result.error_messages)}개):")
                for error in result.error_messages[:3]:  # 최대 3개만 표시
                    print(f"      - {error}")

            print()

    async def cleanup(self):
        """리소스 정리"""
        try:
            # REST Provider 세션 정리
            if hasattr(self.rest_provider, '_session') and self.rest_provider._session:
                await self.rest_provider._session.close()

            # WebSocket Provider 연결 정리
            if hasattr(self.websocket_provider, 'disconnect'):
                await self.websocket_provider.disconnect()

            print("🧹 리소스 정리 완료")

        except Exception as e:
            print(f"⚠️ 리소스 정리 중 오류: {e}")


async def main():
    """메인 테스트 실행"""

    print("🚀 스마트 라우터 성능 테스트 시작")
    print("="*50)

    tester = SmartRouterPerformanceTester()

    if not hasattr(tester, 'smart_router'):
        print("❌ 스마트 라우터 초기화 실패로 테스트 중단")
        return

    # 1. 기본 성능 벤치마크
    print("\n1️⃣ 기본 성능 벤치마크 테스트")
    await tester.test_basic_performance()

    # 2. FrequencyAnalyzer 정확성 테스트
    print("\n2️⃣ FrequencyAnalyzer 정확성 테스트")
    await tester.test_frequency_analyzer_accuracy()

    # 3. 채널 자동 전환 테스트
    print("\n3️⃣ 채널 자동 전환 테스트")
    await tester.test_channel_switching()

    # 4. Rate Limit 준수 테스트
    print("\n4️⃣ Rate Limit 준수 테스트")
    await tester.test_rate_limit_compliance()

    # 결과 요약
    tester.print_test_summary()

    # 리소스 정리
    await tester.cleanup()

    print("\n🎉 모든 테스트 완료!")


if __name__ == "__main__":
    asyncio.run(main())
