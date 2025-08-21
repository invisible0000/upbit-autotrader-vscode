"""
Smart Routing System 통합 테스트 러너

Test 04 표준에 따른 포괄적 검증 실행
- Basic Functionality (Test 01)
- Performance Validation (Test 02)
- Stress Testing (Test 03)
- Scenario Validation (Test 04)
"""

import asyncio
import sys
import traceback
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from upbit_auto_trading.infrastructure.logging import create_component_logger

# 테스트 모듈 import (절대 경로 추가 후)
from basic.test_01_basic_functionality import Test01BasicFunctionality
from performance.test_02_performance_validation import Test02PerformanceValidation
from stress.test_03_stress_validation import Test03StressValidation
from scenarios.test_04_scenario_validation import Test04ScenarioValidation


class SmartRoutingTestSuite:
    """Smart Routing System 통합 테스트 스위트"""

    def __init__(self):
        self.logger = create_component_logger("SmartRoutingTestSuite")
        self.test_results = {}

    async def run_all_tests(self) -> bool:
        """전체 테스트 스위트 실행"""
        self.logger.info("🚀 Smart Routing System 통합 테스트 시작")
        self.logger.info("=" * 100)

        # 테스트 목록 정의
        tests = [
            ("Test 01 - Basic Functionality", Test01BasicFunctionality),
            ("Test 02 - Performance Validation", Test02PerformanceValidation),
            ("Test 03 - Stress Testing", Test03StressValidation),
            ("Test 04 - Scenario Validation", Test04ScenarioValidation)
        ]

        overall_success = True
        successful_tests = 0
        total_tests = len(tests)

        # 각 테스트 순차 실행
        for test_name, test_class in tests:
            self.logger.info(f"\n🎯 {test_name} 실행 중...")
            self.logger.info("-" * 80)

            try:
                # 테스트 인스턴스 생성 및 실행
                test_instance = test_class()
                test_result = await test_instance.execute_full_test()

                # 결과 기록
                self.test_results[test_name] = {
                    'success': test_result,
                    'error': None
                }

                if test_result:
                    successful_tests += 1
                    self.logger.info(f"✅ {test_name} 성공")
                else:
                    overall_success = False
                    self.logger.warning(f"❌ {test_name} 실패")

            except Exception as e:
                overall_success = False
                error_msg = f"{e.__class__.__name__}: {str(e)}"
                self.test_results[test_name] = {
                    'success': False,
                    'error': error_msg
                }

                self.logger.error(f"❌ {test_name} 예외 발생: {error_msg}")
                self.logger.debug(f"상세 스택 트레이스:\\n{traceback.format_exc()}")

            # 테스트 간 안정화 시간
            await asyncio.sleep(2)

        # 최종 결과 보고
        self._report_final_results(successful_tests, total_tests, overall_success)

        return overall_success

    def _report_final_results(self, successful_tests: int, total_tests: int, overall_success: bool):
        """최종 결과 보고"""
        self.logger.info("\n" + "=" * 100)
        self.logger.info("🏆 Smart Routing System 통합 테스트 완료")
        self.logger.info("=" * 100)

        success_rate = (successful_tests / total_tests) * 100
        self.logger.info(f"📊 전체 성공률: {successful_tests}/{total_tests} ({success_rate:.1f}%)")

        # 개별 테스트 결과 상세
        self.logger.info("\n📋 개별 테스트 결과:")
        for test_name, result in self.test_results.items():
            status = "✅" if result['success'] else "❌"
            self.logger.info(f"   {status} {test_name}")
            if result['error']:
                self.logger.info(f"      오류: {result['error']}")

        # 전체 판정
        if overall_success:
            self.logger.info("\n🎉 전체 테스트 성공! Smart Routing System이 모든 검증을 통과했습니다.")
        else:
            self.logger.warning(f"\n⚠️  일부 테스트 실패. {total_tests - successful_tests}개 테스트에서 문제가 발견되었습니다.")

        # 권장사항
        self._provide_recommendations(successful_tests, total_tests)

    def _provide_recommendations(self, successful_tests: int, total_tests: int):
        """테스트 결과 기반 권장사항 제공"""
        success_rate = (successful_tests / total_tests) * 100

        self.logger.info("\n💡 권장사항:")

        if success_rate >= 100:
            self.logger.info("   • Smart Routing System이 프로덕션 배포 준비 완료되었습니다.")
            self.logger.info("   • 모든 성능 기준과 안정성 요구사항을 충족합니다.")

        elif success_rate >= 75:
            self.logger.info("   • 시스템이 대부분 정상 동작하지만 일부 개선이 필요합니다.")
            self.logger.info("   • 실패한 테스트를 검토하고 문제를 해결하세요.")

        elif success_rate >= 50:
            self.logger.info("   • 시스템에 중요한 문제가 있습니다.")
            self.logger.info("   • 프로덕션 배포 전 반드시 문제를 해결하세요.")

        else:
            self.logger.info("   • 시스템이 기본적인 요구사항을 충족하지 못합니다.")
            self.logger.info("   • 근본적인 아키텍처 검토가 필요할 수 있습니다.")

        # 성능 개선 제안
        failed_tests = [name for name, result in self.test_results.items() if not result['success']]

        if "Performance Validation" in " ".join(failed_tests):
            self.logger.info("   • 성능 최적화: 캐시 설정, 네트워크 정책, 또는 Tier 로직 조정 검토")

        if "Stress Testing" in " ".join(failed_tests):
            self.logger.info("   • 안정성 강화: 오류 처리, 리소스 관리, 또는 동시성 제어 개선")

        if "Scenario Validation" in " ".join(failed_tests):
            self.logger.info("   • 실무 적합성: 사용 패턴 분석 및 Context 기반 최적화 필요")

    async def run_individual_test(self, test_number: int) -> bool:
        """개별 테스트 실행"""
        test_mapping = {
            1: ("Test 01 - Basic Functionality", Test01BasicFunctionality),
            2: ("Test 02 - Performance Validation", Test02PerformanceValidation),
            3: ("Test 03 - Stress Testing", Test03StressValidation),
            4: ("Test 04 - Scenario Validation", Test04ScenarioValidation)
        }

        if test_number not in test_mapping:
            self.logger.error(f"❌ 잘못된 테스트 번호: {test_number}")
            return False

        test_name, test_class = test_mapping[test_number]

        self.logger.info(f"🎯 {test_name} 개별 실행")
        self.logger.info("-" * 60)

        try:
            test_instance = test_class()
            result = await test_instance.execute_full_test()

            if result:
                self.logger.info(f"✅ {test_name} 성공")
            else:
                self.logger.warning(f"❌ {test_name} 실패")

            return result

        except Exception as e:
            self.logger.error(f"❌ {test_name} 예외: {e}")
            return False


async def main():
    """메인 실행 함수"""
    suite = SmartRoutingTestSuite()

    # 명령행 인수 처리
    if len(sys.argv) > 1:
        try:
            test_number = int(sys.argv[1])
            return await suite.run_individual_test(test_number)
        except ValueError:
            print("사용법: python run_smart_routing_tests.py [1|2|3|4]")
            print("  1: Basic Functionality")
            print("  2: Performance Validation")
            print("  3: Stress Testing")
            print("  4: Scenario Validation")
            print("  인수 없음: 전체 테스트")
            return False
    else:
        # 전체 테스트 실행
        return await suite.run_all_tests()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
