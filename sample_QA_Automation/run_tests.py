"""
테스트 실행 스크립트

이 스크립트는 업비트 자동매매 시스템의 GUI 자동화 테스트를 실행합니다.
"""

import unittest
import sys
import os
import argparse
import time
from datetime import datetime
from PyQt6.QtWidgets import QApplication

# 테스트 모듈 임포트
from tests.test_main_window import TestMainWindow
from tests.test_dashboard import TestDashboard
from tests.test_chart_view import TestChartView
from tests.test_settings import TestSettings


def run_all_tests():
    """모든 테스트 실행"""
    # 시작 시간 기록
    start_time = time.time()
    
    # QApplication 인스턴스 생성
    app = QApplication(sys.argv)
    
    # 테스트 스위트 생성
    test_suite = unittest.TestSuite()
    
    # 테스트 추가
    test_suite.addTest(unittest.makeSuite(TestMainWindow))
    test_suite.addTest(unittest.makeSuite(TestDashboard))
    test_suite.addTest(unittest.makeSuite(TestChartView))
    test_suite.addTest(unittest.makeSuite(TestSettings))
    
    # 테스트 실행
    result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # 종료 시간 기록
    end_time = time.time()
    execution_time = end_time - start_time
    
    # 결과 요약 출력
    print("\n" + "=" * 80)
    print(f"테스트 실행 시간: {execution_time:.2f}초")
    print(f"실행된 테스트: {result.testsRun}")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패: {len(result.failures)}")
    print(f"오류: {len(result.errors)}")
    print("=" * 80)
    
    # 테스트 결과 보고서 생성
    generate_report(result, execution_time)
    
    # 종료 코드 반환
    return 0 if result.wasSuccessful() else 1


def run_specific_test(test_name):
    """특정 테스트 실행"""
    # QApplication 인스턴스 생성
    app = QApplication(sys.argv)
    
    # 테스트 실행
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromName(f"tests.{test_name}")
    )
    
    # 종료 코드 반환
    return 0 if result.wasSuccessful() else 1


def generate_report(result, execution_time):
    """테스트 결과 보고서 생성"""
    # 보고서 디렉토리 생성
    report_dir = "test_reports"
    os.makedirs(report_dir, exist_ok=True)
    
    # 보고서 파일 이름 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(report_dir, f"test_report_{timestamp}.md")
    
    # 보고서 작성
    with open(report_file, "w") as f:
        f.write("# GUI 자동화 테스트 보고서\n\n")
        f.write(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 테스트 요약\n")
        f.write(f"- 총 테스트 케이스: {result.testsRun}\n")
        f.write(f"- 성공: {result.testsRun - len(result.failures) - len(result.errors)}\n")
        f.write(f"- 실패: {len(result.failures)}\n")
        f.write(f"- 오류: {len(result.errors)}\n")
        f.write(f"- 테스트 실행 시간: {execution_time:.2f}초\n\n")
        
        if result.failures:
            f.write("## 실패한 테스트 케이스\n")
            for i, (test, error) in enumerate(result.failures, 1):
                f.write(f"### {i}. {test}\n")
                f.write("```\n")
                f.write(error)
                f.write("\n```\n\n")
        
        if result.errors:
            f.write("## 오류가 발생한 테스트 케이스\n")
            for i, (test, error) in enumerate(result.errors, 1):
                f.write(f"### {i}. {test}\n")
                f.write("```\n")
                f.write(error)
                f.write("\n```\n\n")
    
    print(f"테스트 보고서가 생성되었습니다: {report_file}")


if __name__ == "__main__":
    # 명령행 인자 파싱
    parser = argparse.ArgumentParser(description="업비트 자동매매 시스템 GUI 자동화 테스트")
    parser.add_argument("--test", help="실행할 특정 테스트 (예: test_main_window.TestMainWindow)")
    args = parser.parse_args()
    
    # 테스트 실행
    if args.test:
        sys.exit(run_specific_test(args.test))
    else:
        sys.exit(run_all_tests())