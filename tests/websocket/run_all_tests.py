"""
WebSocket 티커 테스트 전체 실행기
모든 테스트를 순차적으로 실행하고 통합 리포트 생성
"""
import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any

from tests.websocket.test_base import create_component_logger
from tests.websocket.ticker.test_01_single_request import TestSingleTickerRequest
from tests.websocket.ticker.test_02_multiple_requests import TestMultipleTickerRequests
from tests.websocket.ticker.test_03_multi_symbol import TestMultiSymbolSubscription
from tests.websocket.ticker.test_04_multi_5_ticker import TestMulti5TickerSubscription
from tests.websocket.ticker.test_05_multiple_multi import TestMultipleMultiSubscription
from tests.websocket.ticker.test_06_sequential_ordered import TestSequentialOrderedRequests
from tests.websocket.ticker.test_07_multiple_simultaneous import TestMultipleSimultaneousRequests
from tests.websocket.ticker.test_08_large_scale_50_ticker import TestLargeScaleTickerRequests
from tests.websocket.ticker.test_09_krw_market_comprehensive import TestKRWMarketComprehensive
from tests.websocket.ticker.test_10_consecutive_5_rounds import TestConsecutiveFiveRounds
from tests.websocket.ticker.test_11_load_scalability import TestLoadScalability


class WebSocketTestRunner:
    """WebSocket 테스트 실행기"""

    def __init__(self):
        self.logger = create_component_logger("WebSocketTestRunner")
        self.test_results: List[Dict[str, Any]] = []
        self.start_time = None
        self.end_time = None

    def create_test_results_dir(self):
        """테스트 결과 디렉토리 생성"""
        os.makedirs("tests/websocket/test_results", exist_ok=True)

    async def run_basic_tests(self):
        """기본 통신 테스트 실행"""
        self.logger.info("🔧 기본 통신 테스트 시작")

        basic_tests = [
            ("Test 1: 단일 티커 요청", TestSingleTickerRequest),
            ("Test 2: 5회 연속 요청", TestMultipleTickerRequests),
            ("Test 3: 멀티 심볼 구독", TestMultiSymbolSubscription),
            ("Test 4: 5개 티커 멀티 구독", TestMulti5TickerSubscription),
            ("Test 5: 다회 멀티 구독", TestMultipleMultiSubscription),
            ("Test 6: 순서대로 요청", TestSequentialOrderedRequests),
            ("Test 7: 다중 동시 요청", TestMultipleSimultaneousRequests),
            ("Test 10: 연속 5회 일관성", TestConsecutiveFiveRounds),
        ]

        for test_name, test_class in basic_tests:
            self.logger.info(f"🚀 {test_name} 실행 중...")

            try:
                test_instance = test_class()
                await test_instance.run_full_test()

                # 결과 저장
                test_result = {
                    "test_name": test_name,
                    "status": "SUCCESS",
                    "metrics": test_instance.metrics.to_dict(),
                    "timestamp": datetime.now().isoformat()
                }
                self.test_results.append(test_result)

                self.logger.info(f"✅ {test_name} 완료")

                # 테스트 간 쿨다운
                await asyncio.sleep(3)

            except Exception as e:
                self.logger.error(f"❌ {test_name} 실패: {e}")
                test_result = {
                    "test_name": test_name,
                    "status": "FAILED",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                self.test_results.append(test_result)

    async def run_heavy_tests(self):
        """대용량 및 특수 테스트 실행"""
        self.logger.info("🔥 대용량 및 특수 테스트 시작")

        heavy_tests = [
            ("Test 8: 50개 티커 대용량 처리", TestLargeScaleTickerRequests),
            ("Test 9: KRW 마켓 전체 포괄", TestKRWMarketComprehensive),
        ]

        for test_name, test_class in heavy_tests:
            self.logger.info(f"🚀 {test_name} 실행 중...")

            try:
                test_instance = test_class()
                await test_instance.run_full_test()

                # 결과 저장
                test_result = {
                    "test_name": test_name,
                    "status": "SUCCESS",
                    "metrics": test_instance.metrics.to_dict(),
                    "timestamp": datetime.now().isoformat()
                }
                self.test_results.append(test_result)

                self.logger.info(f"✅ {test_name} 완료")

                # 대용량 테스트 간 쿨다운 (더 길게)
                await asyncio.sleep(10)

            except Exception as e:
                self.logger.error(f"❌ {test_name} 실패: {e}")
                test_result = {
                    "test_name": test_name,
                    "status": "FAILED",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                self.test_results.append(test_result)

    async def run_load_tests(self):
        """부하 테스트 실행"""
        self.logger.info("🔥 부하 테스트 시작")

        try:
            load_test = TestLoadScalability()
            await load_test.run_full_test()

            # 부하 테스트 결과
            test_result = {
                "test_name": "Test 11: 부하 및 확장성 테스트",
                "status": "SUCCESS",
                "metrics": load_test.metrics.to_dict(),
                "scalability_analysis": load_test.analyzer.analyze_scalability(),
                "timestamp": datetime.now().isoformat()
            }
            self.test_results.append(test_result)

            self.logger.info("✅ 부하 테스트 완료")

        except Exception as e:
            self.logger.error(f"❌ 부하 테스트 실패: {e}")
            test_result = {
                "test_name": "Test 11: 부하 및 확장성 테스트",
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.test_results.append(test_result)

    def generate_summary_report(self):
        """통합 요약 리포트 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 통계 계산
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["status"] == "SUCCESS")
        failed_tests = total_tests - successful_tests

        # 성능 통계 (성공한 테스트만)
        successful_metrics = [
            r["metrics"] for r in self.test_results
            if r["status"] == "SUCCESS" and "metrics" in r
        ]

        total_requests = sum(m["total_requests"] for m in successful_metrics)
        avg_response_time = sum(
            float(m["avg_response_time"].replace("ms", ""))
            for m in successful_metrics
        ) / len(successful_metrics) if successful_metrics else 0

        total_duration = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0

        # 요약 리포트
        summary = {
            "test_suite_summary": {
                "execution_time": {
                    "start": self.start_time.isoformat() if self.start_time else None,
                    "end": self.end_time.isoformat() if self.end_time else None,
                    "duration_seconds": total_duration
                },
                "test_statistics": {
                    "total_tests": total_tests,
                    "successful_tests": successful_tests,
                    "failed_tests": failed_tests,
                    "success_rate": f"{(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
                },
                "performance_overview": {
                    "total_requests": total_requests,
                    "average_response_time": f"{avg_response_time:.2f}ms",
                    "overall_rps": f"{total_requests/total_duration:.2f}" if total_duration > 0 else "0"
                }
            },
            "detailed_results": self.test_results
        }

        # 파일 저장
        filename = f"tests/websocket/test_results/test_suite_summary_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        self.logger.info(f"📁 통합 리포트 저장됨: {filename}")

        return summary

    def print_final_summary(self, summary: Dict[str, Any]):
        """최종 요약 출력"""
        print(f"\n{'='*80}")
        print("📊 WebSocket 티커 테스트 최종 요약")
        print(f"{'='*80}")

        stats = summary["test_suite_summary"]

        print(f"⏱️  실행 시간: {stats['execution_time']['duration_seconds']:.1f}초")
        print(f"📈 테스트 결과: {stats['test_statistics']['successful_tests']}/{stats['test_statistics']['total_tests']} 성공 ({stats['test_statistics']['success_rate']})")
        print(f"🔢 총 요청 수: {stats['performance_overview']['total_requests']:,}")
        print(f"⚡ 평균 응답시간: {stats['performance_overview']['average_response_time']}")
        print(f"🚀 전체 RPS: {stats['performance_overview']['overall_rps']}")

        print(f"\n🔍 개별 테스트 결과:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "SUCCESS" else "❌"
            print(f"   {status_icon} {result['test_name']}")

            if result["status"] == "SUCCESS" and "metrics" in result:
                metrics = result["metrics"]
                print(f"      - 요청: {metrics['successful_requests']}/{metrics['total_requests']}")
                print(f"      - 응답시간: {metrics['avg_response_time']}")
                print(f"      - RPS: {metrics['requests_per_second']}")

        # 권장사항
        print(f"\n💡 권장사항:")
        if stats['test_statistics']['success_rate'].replace('%', '') != '100.0':
            print("   - 실패한 테스트 원인 분석 필요")

        avg_rt = float(stats['performance_overview']['average_response_time'].replace('ms', ''))
        if avg_rt > 500:
            print("   - 응답시간 최적화 검토 필요 (500ms 초과)")
        elif avg_rt < 300:
            print("   - 우수한 응답시간 성능 (300ms 미만)")

        print(f"\n🎯 결론: {'양호' if stats['test_statistics']['success_rate'] == '100.0%' else '개선 필요'}")

    async def run_all_tests(self):
        """모든 테스트 실행"""
        self.start_time = datetime.now()
        self.create_test_results_dir()

        print("🚀 WebSocket 티커 테스트 스위트 시작")
        print(f"시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        try:
            # 기본 테스트 실행
            await self.run_basic_tests()

            print(f"\n{'='*60}")
            print("기본 테스트 완료, 대용량 테스트 시작")

            # 대용량 테스트 실행
            await self.run_heavy_tests()

            print(f"\n{'='*60}")
            print("대용량 테스트 완료, 부하 테스트 시작")

            # 부하 테스트 실행
            await self.run_load_tests()

        except Exception as e:
            self.logger.error(f"❌ 테스트 스위트 실행 중 오류: {e}")
        finally:
            self.end_time = datetime.now()

        # 요약 리포트 생성 및 출력
        summary = self.generate_summary_report()
        self.print_final_summary(summary)


async def main():
    """메인 실행 함수"""
    runner = WebSocketTestRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
