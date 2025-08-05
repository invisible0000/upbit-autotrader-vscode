#!/usr/bin/env python3
"""
전체 단위 테스트 검증 스크립트
"""

import subprocess
import sys
import os

def main():
    """전체 테스트 실행"""
    print("🔍 전체 Configuration Management System 단위 테스트 검증")
    print("=" * 60)

    # UTF-8 환경변수 설정 (UnicodeError 방지)
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'
    env['UPBIT_LOG_CONTEXT'] = 'testing'
    env['UPBIT_LOG_SCOPE'] = 'silent'
    env['UPBIT_CONSOLE_OUTPUT'] = 'false'

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/infrastructure/config/test_config_loader.py",
        "-v",  # verbose
        "--tb=short"  # 짧은 traceback
    ]

    try:
        print("📋 실행 명령:")
        print(" ".join(cmd))
        print()

        result = subprocess.run(cmd, env=env, cwd=os.getcwd())

        print(f"\n{'=' * 60}")
        print(f"🎯 테스트 결과: {'✅ 성공' if result.returncode == 0 else '❌ 실패'}")
        print(f"Return Code: {result.returncode}")
        print(f"{'=' * 60}")

        return result.returncode == 0

    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
