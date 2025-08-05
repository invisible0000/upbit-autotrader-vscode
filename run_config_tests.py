#!/usr/bin/env python3
"""
Configuration Tests Runner
단위 테스트 실행을 위한 스크립트
"""

import subprocess
import sys
import os


def run_test(test_path):
    """개별 테스트 실행"""
    print(f"\n{'=' * 60}")
    print(f"🧪 실행 중: {test_path}")
    print(f"{'=' * 60}")

    # UTF-8 환경변수 설정
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'
    env['UPBIT_LOG_CONTEXT'] = 'testing'  # 로깅 시스템을 테스트 모드로
    env['UPBIT_LOG_SCOPE'] = 'silent'     # 로깅 출력 최소화
    env['UPBIT_CONSOLE_OUTPUT'] = 'false'  # 콘솔 출력 비활성화

    cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        "-xvs"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                cwd=os.getcwd(), env=env, encoding='utf-8')

        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        print(f"Return Code: {result.returncode}")
        return result.returncode == 0

    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")
        return False


def run_all_config_tests():
    """모든 Configuration 테스트 실행"""
    print("🚀 Configuration Management System 테스트 시작")

    # 전체 테스트 실행
    test_file = "tests/infrastructure/config/test_config_loader.py"
    return run_test(test_file)


def run_specific_tests():
    """특정 실패 테스트들만 실행"""
    failing_tests = [
        "tests/infrastructure/config/test_config_loader.py::TestIntegration::test_full_system_integration",
        "tests/infrastructure/config/test_config_loader.py::TestIntegration::test_environment_specific_service_behavior"
    ]

    results = []
    for test in failing_tests:
        success = run_test(test)
        results.append((test, success))

    print(f"\n{'=' * 60}")
    print("📊 테스트 결과 요약:")
    print(f"{'=' * 60}")

    for test, success in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{status}: {test}")

    return all(success for _, success in results)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--specific":
        print("🎯 특정 실패 테스트만 실행")
        success = run_specific_tests()
    else:
        print("🎯 전체 Configuration 테스트 실행")
        success = run_all_config_tests()

    if success:
        print("\n🎉 모든 테스트가 성공했습니다!")
        sys.exit(0)
    else:
        print("\n💥 일부 테스트가 실패했습니다.")
        sys.exit(1)
