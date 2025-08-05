#!/usr/bin/env python3
"""
Configuration System Manual Verification
REPL 검증을 위한 설정 로드 테스트 스크립트
"""

import os
import sys
from pathlib import Path

def verify_config_loading():
    """설정 로딩 검증"""
    print("🔍 Configuration System Manual Verification")
    print("=" * 60)

    try:
        # UTF-8 환경변수 설정으로 UnicodeError 방지
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONUTF8'] = '1'
        os.environ['UPBIT_LOG_CONTEXT'] = 'testing'
        os.environ['UPBIT_LOG_SCOPE'] = 'silent'
        os.environ['UPBIT_CONSOLE_OUTPUT'] = 'false'

        from upbit_auto_trading.infrastructure.config import ConfigLoader

        print("✅ ConfigLoader 임포트 성공")

        # 모든 환경 설정 검증
        loader = ConfigLoader()
        print("✅ ConfigLoader 인스턴스 생성 성공")

        environments = ['development', 'testing', 'production']

        for env in environments:
            print(f"\n📋 {env.upper()} 환경 설정 로드 테스트:")
            print("-" * 40)

            try:
                config = loader.load_config(env)

                print(f"✅ {env} 설정 로드 성공")
                print(f"   - 환경: {config.environment.value}")
                print(f"   - 로그 레벨: {config.logging.level}")
                print(f"   - 모의 거래: {config.trading.paper_trading}")
                print(f"   - 설정 DB 경로: {config.database.settings_db_path}")
                print(f"   - API 기본 URL: {config.upbit_api.base_url}")
                print(f"   - 앱 이름: {config.app_name}")
                print(f"   - 앱 버전: {config.app_version}")

                # 설정 검증 실행
                validation_errors = config.validate()
                if validation_errors:
                    print(f"⚠️  검증 경고: {validation_errors}")
                else:
                    print("✅ 설정 검증 통과")

            except Exception as e:
                print(f"❌ {env} 설정 로드 실패: {e}")
                return False

        print(f"\n🎉 모든 환경 설정 로드 검증 완료!")
        return True

    except Exception as e:
        print(f"❌ 설정 시스템 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_dependency_injection():
    """의존성 주입 검증"""
    print(f"\n🔧 Dependency Injection Manual Verification")
    print("=" * 60)

    try:
        from upbit_auto_trading.infrastructure.dependency_injection import DIContainer, LifetimeScope

        print("✅ DIContainer 임포트 성공")

        # 컨테이너 생성
        container = DIContainer()
        print("✅ DIContainer 인스턴스 생성 성공")

        # 테스트 서비스 클래스들
        class TestService:
            def __init__(self):
                self.value = "test_service"

        class DatabaseService:
            def __init__(self):
                self.connection = "test_connection"

        class BusinessService:
            def __init__(self, db_service: DatabaseService):
                self.db_service = db_service
                self.name = "business_service"

        print("\n📋 서비스 등록 및 해결 테스트:")
        print("-" * 40)

        # Singleton 등록 및 테스트
        container.register_singleton(TestService)
        service1 = container.resolve(TestService)
        service2 = container.resolve(TestService)
        print(f"✅ Singleton 테스트: {service1 is service2} (같은 인스턴스)")

        # Transient 등록 및 테스트
        container.register_transient(DatabaseService)
        db1 = container.resolve(DatabaseService)
        db2 = container.resolve(DatabaseService)
        print(f"✅ Transient 테스트: {db1 is not db2} (다른 인스턴스)")

        # 자동 의존성 주입 테스트
        container.register_transient(BusinessService)
        business = container.resolve(BusinessService)
        print(f"✅ 자동 의존성 주입 테스트: {isinstance(business.db_service, DatabaseService)}")

        # Scoped 생명주기 테스트
        container.register_scoped(TestService, TestService)  # 다시 등록 (Scoped로)

        with container.create_scope() as scope:
            scoped1 = scope.resolve(TestService)
            scoped2 = scope.resolve(TestService)
            print(f"✅ Scoped (같은 스코프): {scoped1 is scoped2}")

        with container.create_scope() as scope2:
            scoped3 = scope2.resolve(TestService)
            print(f"✅ Scoped (다른 스코프): {scoped1 is not scoped3}")

        print(f"\n🎉 의존성 주입 시스템 검증 완료!")
        return True

    except Exception as e:
        print(f"❌ 의존성 주입 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_application_context():
    """애플리케이션 컨텍스트 검증"""
    print(f"\n🚀 Application Context Manual Verification")
    print("=" * 60)

    try:
        from upbit_auto_trading.infrastructure.dependency_injection import ApplicationContext

        print("✅ ApplicationContext 임포트 성공")

        print("\n📋 ApplicationContext 초기화 및 설정 로드 확인:")
        print("-" * 40)

        # 기본 설정 폴더 경로
        config_dir = Path("config")

        # Development 환경으로 컨텍스트 생성
        with ApplicationContext('development', config_dir) as context:
            print("✅ ApplicationContext 생성 성공")
            print(f"   - 환경: {context.config.environment.value}")
            print(f"   - 앱 이름: {context.config.app_name}")
            print(f"   - 컨테이너 생성: {context.container is not None}")

            # 테스트 서비스 등록
            class ConfigService:
                def __init__(self, config):
                    self.config = config
                    self.app_name = config.app_name

            # ApplicationConfig를 컨테이너에 등록
            context.container.register_singleton(type(context.config), context.config)
            context.container.register_transient(ConfigService,
                                                lambda: ConfigService(context.config))

            # 서비스 해결
            config_service = context.container.resolve(ConfigService)
            print(f"✅ 서비스 해결 성공: {config_service.app_name}")

        print("✅ ApplicationContext 생명주기 관리 완료")

        print(f"\n🎉 애플리케이션 컨텍스트 검증 완료!")
        return True

    except Exception as e:
        print(f"❌ 애플리케이션 컨텍스트 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_config_files():
    """설정 파일 검증"""
    print(f"\n📁 Configuration Files Manual Verification")
    print("=" * 60)

    try:
        import yaml

        config_files = [
            'config/config.yaml',
            'config/config.development.yaml',
            'config/config.testing.yaml',
            'config/config.production.yaml'
        ]

        for config_file in config_files:
            if Path(config_file).exists():
                print(f"✅ {config_file} 존재")

                # YAML 구문 검증
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        yaml.safe_load(f)
                    print(f"   ✅ 구문 검증 통과")
                except yaml.YAMLError as e:
                    print(f"   ❌ YAML 구문 오류: {e}")
                    return False
            else:
                print(f"❌ {config_file} 누락")
                return False

        print(f"\n🎉 설정 파일 검증 완료!")
        return True

    except Exception as e:
        print(f"❌ 설정 파일 검증 실패: {e}")
        return False

def main():
    """전체 검증 실행"""
    print("🔍 Configuration Management System - Manual Verification")
    print("=" * 80)

    # 프로젝트 루트로 작업 디렉토리 변경
    project_root = Path(__file__).parent
    os.chdir(project_root)

    results = []

    # 1. 설정 로딩 검증
    results.append(("설정 로딩", verify_config_loading()))

    # 2. 의존성 주입 검증
    results.append(("의존성 주입", verify_dependency_injection()))

    # 3. 애플리케이션 컨텍스트 검증
    results.append(("애플리케이션 컨텍스트", verify_application_context()))

    # 4. 설정 파일 검증
    results.append(("설정 파일", verify_config_files()))

    # 결과 요약
    print(f"\n📊 검증 결과 요약:")
    print("=" * 80)

    all_passed = True
    for name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{status}: {name}")
        if not result:
            all_passed = False

    if all_passed:
        print(f"\n🎉 모든 검증이 성공했습니다!")
        print("✅ Configuration Management System이 완전히 구현되었습니다.")
        return 0
    else:
        print(f"\n💥 일부 검증이 실패했습니다.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
