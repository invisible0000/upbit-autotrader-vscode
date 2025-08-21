"""
Smart Routing 간단 테스트 러너

기본 기능만 빠르게 검증하는 단순화된 테스트 러너입니다.
"""

import asyncio
import sys
import os

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))

from upbit_auto_trading.infrastructure.logging import create_component_logger
from basic.test_01_basic_functionality import Test01BasicFunctionality


async def run_basic_test():
    """기본 기능 테스트만 실행"""
    logger = create_component_logger("SimpleTestRunner")

    logger.info("🚀 Smart Routing 기본 기능 간단 테스트 시작")
    logger.info("=" * 60)

    try:
        # Test 01만 실행
        test = Test01BasicFunctionality()
        result = await test.execute_full_test()

        if result:
            logger.info("✅ 기본 기능 테스트 성공!")
            return True
        else:
            logger.error("❌ 기본 기능 테스트 실패")
            return False

    except Exception as e:
        logger.error(f"❌ 테스트 실행 중 오류: {e}")
        return False


async def main():
    """메인 실행 함수"""
    success = await run_basic_test()
    return success


if __name__ == "__main__":
    # 환경변수 설정
    os.environ['UPBIT_CONSOLE_OUTPUT'] = 'true'
    os.environ['UPBIT_LOG_SCOPE'] = 'normal'

    success = asyncio.run(main())
    sys.exit(0 if success else 1)
