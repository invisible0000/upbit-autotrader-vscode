#!/usr/bin/env python3
"""
Configuration System Manual Verification
Python REPL 방식 설정 로드 검증
"""

import os
import sys

def main():
    """설정 시스템 수동 검증"""
    print("🔍 Configuration System 수동 검증 시작")
    print("=" * 60)

    # UTF-8 환경변수 설정 (UnicodeError 방지)
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    os.environ['UPBIT_LOG_CONTEXT'] = 'testing'
    os.environ['UPBIT_LOG_SCOPE'] = 'silent'
    os.environ['UPBIT_CONSOLE_OUTPUT'] = 'false'

    try:
        # Step 1: ConfigLoader 임포트 및 생성
        print("📦 Step 1: ConfigLoader 임포트")
        from upbit_auto_trading.infrastructure.config.loaders.config_loader import ConfigLoader
        loader = ConfigLoader()
        print("✅ ConfigLoader 생성 성공")

        # Step 2: 모든 환경 설정 로드 테스트
        print("\n📋 Step 2: 환경별 설정 로드 테스트")
        environments = ['development', 'testing', 'production']

        for env in environments:
            print(f"\n🔧 {env} 환경 설정 로드 중...")
            try:
                config = loader.load_config(env)
                print(f"✅ {env} 설정 로드 성공")
                print(f"   - 환경: {config.environment.value}")
                print(f"   - 로그 레벨: {config.logging.level}")
                print(f"   - 모의 거래: {config.trading.paper_trading}")
                print(f"   - DB 백업: {getattr(config.database, 'backup_enabled', 'N/A')}")
                print(f"   - API 타임아웃: {config.upbit_api.timeout_seconds}초")

            except Exception as e:
                print(f"❌ {env} 설정 로드 실패: {e}")
                return False

        # Step 3: DIContainer 기본 동작 테스트
        print(f"\n🔧 Step 3: DIContainer 기본 동작 테스트")
        from upbit_auto_trading.infrastructure.dependency_injection.container import DIContainer

        container = DIContainer()

        # 간단한 서비스 등록 및 해결 테스트
        class TestService:
            def __init__(self):
                self.name = "TestService"

        container.register_singleton(TestService)
        service = container.resolve(TestService)

        print(f"✅ DIContainer 기본 동작 성공")
        print(f"   - 서비스 타입: {type(service).__name__}")
        print(f"   - 서비스 이름: {service.name}")

        # Step 4: ApplicationContext 통합 테스트
        print(f"\n🔧 Step 4: ApplicationContext 통합 테스트")
        from upbit_auto_trading.infrastructure.dependency_injection.app_context import ApplicationContext

        with ApplicationContext('testing') as context:
            print(f"✅ ApplicationContext 생성 성공")
            print(f"   - 환경: {context.config.environment.value}")
            print(f"   - 앱 이름: {context.config.app_name}")
            print(f"   - 컨테이너 준비: {'O' if context.container else 'X'}")

        print(f"\n🎉 모든 수동 검증 완료!")
        return True

    except Exception as e:
        print(f"\n❌ 검증 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Configuration System 검증 성공")
        sys.exit(0)
    else:
        print("\n💥 Configuration System 검증 실패")
        sys.exit(1)
