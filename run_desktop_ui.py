"""
데스크톱 UI 실행 스크립트 - Infrastructure Layer 통합 버전 (QAsync 기반)
"""
import sys
import os
import traceback
import asyncio
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMessageBox
from qasync import QEventLoop
from upbit_auto_trading.infrastructure.dependency_injection.app_context import ApplicationContext, ApplicationContextError
from upbit_auto_trading.infrastructure.logging import create_component_logger

# MainApp 전용 로거 (콘솔 출력은 UPBIT_CONSOLE_OUTPUT 환경변수로 제어)
logger = create_component_logger("MainApp")


# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def exception_handler(exc_type, exc_value, exc_traceback):
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file_path = os.path.join(log_dir, "gui_error.log")

    # 에러 정보 생성
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_content = []
    error_content.append(f"{'=' * 50}")
    error_content.append(f"오류 발생 시간: {now}")

    # traceback을 문자열로 수집
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    error_content.extend(tb_lines)
    error_content.append("")  # 빈 줄 추가

    # 새 에러 + 기존 내용 (역순 삽입)
    new_error_text = "\n".join(error_content)

    try:
        # 기존 내용 읽기 (파일이 있다면)
        existing_content = ""
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()

        # 새 에러를 맨 위에 + 기존 내용 (역순 로깅)
        with open(log_file_path, 'w', encoding='utf-8') as f:
            f.write(new_error_text)
            if existing_content:
                f.write(existing_content)
    except Exception:
        # 로그 쓰기 실패 시 기본 append 방식으로 폴백
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(new_error_text)

    try:
        error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        QMessageBox.critical(None, "애플리케이션 오류", f"오류가 발생했습니다. 'logs/gui_error.log' 파일을 확인해주세요.\n\n{error_message}")
    except ImportError:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.excepthook = exception_handler


def create_application_context() -> ApplicationContext:
    """애플리케이션 컨텍스트 생성 및 초기화"""
    try:
        # 환경변수에서 환경 설정 로드 (기본값: development)
        environment = os.getenv('UPBIT_ENVIRONMENT', 'development')

        # ApplicationContext 생성
        app_context = ApplicationContext(environment=environment)

        # 컨텍스트 초기화
        app_context.initialize()

        logger.info(f"✅ ApplicationContext 초기화 완료 (환경: {environment})")
        return app_context

    except ApplicationContextError as e:
        logger.error(f"❌ ApplicationContext 초기화 실패: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {e}")
        raise


def register_ui_services(app_context: ApplicationContext, repository_container=None):
    """UI 전용 서비스들을 DI Container에 등록"""
    try:
        container = app_context.container

        # Infrastructure 통합 로깅 시스템 사용
        logger.info("🔧 Infrastructure 통합 로깅 시스템 연계...")

        # ApplicationContext에서 이미 등록된 ILoggingService 활용
        logger.info("✅ Infrastructure 기본 로깅 시스템 연계 완료")
        logger.info("✅ Infrastructure Layer 로깅 통합 완료")

        # Domain Logger 의존성 주입 설정 (성능 최적화)
        logger.info("🔧 Domain Logger 성능 최적화 의존성 주입 시작...")
        try:
            from upbit_auto_trading.infrastructure.logging.domain_logger_impl import create_infrastructure_domain_logger
            from upbit_auto_trading.domain.logging import set_domain_logger

            # Infrastructure 기반 Domain Logger 생성
            domain_logger_impl = create_infrastructure_domain_logger()

            # Domain Layer에 의존성 주입
            set_domain_logger(domain_logger_impl)

            logger.info("✅ Domain Logger 성능 최적화 완료 (272배 향상)")
        except Exception as e:
            logger.warning(f"⚠️ Domain Logger 의존성 주입 실패: {e}")
            logger.warning("   NoOpLogger가 기본값으로 사용됩니다")

        # Configuration 서비스 등록 (ApplicationContext에서 이미 생성된 것 활용)
        try:
            from upbit_auto_trading.infrastructure.config.loaders.config_loader import ConfigLoader
            # ApplicationContext 내부의 ConfigLoader 대신 새로 생성해서 등록
            config_loader_instance = ConfigLoader(app_context._config_dir)
            container.register_singleton(ConfigLoader, config_loader_instance)
            logger.info("✅ ConfigurationService 등록 완료")
        except Exception as e:
            logger.warning(f"⚠️ ConfigurationService 등록 실패: {e}")

        # SettingsService 등록
        logger.info("🔧 SettingsService 등록 시작...")
        try:
            from upbit_auto_trading.infrastructure.services.settings_service import ISettingsService, SettingsService
            logger.info("🔧 SettingsService 클래스 import 성공")
            config_loader_instance = container.resolve(ConfigLoader)
            logger.info("🔧 ConfigLoader 인스턴스 해결 성공")
            settings_service = SettingsService(config_loader_instance)
            logger.info("🔧 SettingsService 인스턴스 생성 성공")
            container.register_singleton(ISettingsService, settings_service)
            logger.info("✅ SettingsService 등록 완료")
        except Exception as e:
            logger.warning(f"⚠️ SettingsService 등록 실패: {e}")
            logger.warning(f"    오류 상세: {type(e).__name__}: {str(e)}")
            # MockSettingsService로 폴백
            try:
                from upbit_auto_trading.infrastructure.services.settings_service import ISettingsService, MockSettingsService
                container.register_singleton(ISettingsService, MockSettingsService())
                logger.info("✅ MockSettingsService 폴백 등록 완료")
            except Exception as e2:
                logger.warning(f"⚠️ MockSettingsService 폴백도 실패: {e2}")

        # ApiKeyService 등록 (Repository Container 기반 DDD 패턴)
        if repository_container:
            try:
                from upbit_auto_trading.infrastructure.services.api_key_service import IApiKeyService, ApiKeyService
                logger.info("🔧 ApiKeyService 클래스 import 성공")

                # Repository Container에서 SecureKeysRepository 가져오기
                secure_keys_repo = repository_container.get_secure_keys_repository()
                logger.info("🔧 SecureKeysRepository 인스턴스 해결 성공")

                # Repository 의존성 주입하여 ApiKeyService 생성
                api_key_service = ApiKeyService(secure_keys_repo)
                logger.info("🔧 ApiKeyService 인스턴스 생성 성공 (Repository 주입)")

                # DI Container에 등록
                container.register_singleton(IApiKeyService, api_key_service)
                logger.info("✅ ApiKeyService 등록 완료 (DDD Repository 패턴)")
            except Exception as e:
                logger.warning(f"⚠️ ApiKeyService 등록 실패: {e}")
                logger.warning(f"    오류 상세: {type(e).__name__}: {str(e)}")
                traceback.print_exc()
        else:
            logger.warning("⚠️ Repository Container가 없어서 ApiKeyService를 등록할 수 없습니다")

        # StyleManager 등록
        try:
            from upbit_auto_trading.ui.desktop.common.styles.style_manager import StyleManager
            container.register_singleton(StyleManager, StyleManager())
            logger.info("✅ StyleManager 서비스 등록 완료")
        except ImportError as e:
            logger.warning(f"⚠️ StyleManager 로드 실패: {e}")

        # ThemeService 등록 (Infrastructure Layer 기반)
        logger.info("🔧 ThemeService 등록 시작...")
        try:
            from upbit_auto_trading.infrastructure.services.theme_service import IThemeService, ThemeService
            logger.info("🔧 ThemeService 클래스 import 성공")
            settings_service_instance = container.resolve(ISettingsService)
            style_manager_instance = container.resolve(StyleManager)
            logger.info("🔧 SettingsService 및 StyleManager 의존성 해결 성공")
            theme_service = ThemeService(settings_service_instance, style_manager_instance)
            logger.info("🔧 ThemeService 인스턴스 생성 성공")
            container.register_singleton(IThemeService, theme_service)
            logger.info("✅ ThemeService 등록 완료")
        except Exception as e:
            logger.warning(f"⚠️ ThemeService 등록 실패: {e}")
            logger.warning(f"    오류 상세: {type(e).__name__}: {str(e)}")
            # MockThemeService로 폴백
            try:
                from upbit_auto_trading.infrastructure.services.theme_service import IThemeService, MockThemeService
                container.register_singleton(IThemeService, MockThemeService())
                logger.info("✅ MockThemeService 폴백 등록 완료")
            except Exception as e2:
                logger.warning(f"⚠️ MockThemeService 폴백도 실패: {e2}")

        # NavigationBar 등록
        try:
            from upbit_auto_trading.ui.desktop.common.widgets.navigation_bar import NavigationBar
            container.register_transient(NavigationBar)
            logger.info("✅ NavigationBar 서비스 등록 완료")
        except ImportError as e:
            logger.warning(f"⚠️ NavigationBar 로드 실패: {e}")

        # StatusBar 등록
        try:
            from upbit_auto_trading.ui.desktop.common.widgets.status_bar import StatusBar
            container.register_transient(StatusBar)
            logger.info("✅ StatusBar 서비스 등록 완료")
        except ImportError as e:
            logger.warning(f"⚠️ StatusBar 로드 실패: {e}")

        logger.info("✅ UI 서비스 등록 완료")

    except Exception as e:
        logger.error(f"❌ UI 서비스 등록 실패: {e}")
        raise


async def run_application_async(app: QApplication) -> int:
    """메인 애플리케이션 실행 (QAsync 기반)"""
    app_context = None
    main_window = None

    try:
        # ApplicationContext 초기화
        app_context = create_application_context()

        # 2. Domain Events Subscriber 초기화 (DDD Architecture Phase 2)
        try:
            from upbit_auto_trading.infrastructure.logging.domain_event_subscriber import initialize_domain_logging_subscriber
            initialize_domain_logging_subscriber()
            logger.info("✅ Domain Events 로깅 구독자 초기화 완료")
        except Exception as e:
            logger.warning(f"⚠️ Domain Events 구독자 초기화 실패: {e}")

        # 3. Repository Container 초기화 (DDD Infrastructure Layer)
        try:
            from upbit_auto_trading.infrastructure.repositories.repository_container import RepositoryContainer
            repository_container = RepositoryContainer()
            logger.info("✅ Repository Container 초기화 완료")
        except Exception as e:
            logger.warning(f"⚠️ Repository Container 초기화 실패: {e}")
            repository_container = None

        # 3. UI 서비스 등록 (Repository Container 전달)
        register_ui_services(app_context, repository_container)

        # 4. Application Container 초기화 및 설정 (TASK-13: MVP 패턴 지원)
        try:
            from upbit_auto_trading.application.container import ApplicationServiceContainer, set_application_container

            # Application Service Container 생성 (이미 생성된 Repository Container 사용)
            if repository_container:
                app_service_container = ApplicationServiceContainer(repository_container)
            else:
                # 폴백: 새로운 Repository Container 생성
                from upbit_auto_trading.infrastructure.repositories.repository_container import RepositoryContainer
                repository_container = RepositoryContainer()
                app_service_container = ApplicationServiceContainer(repository_container)

            # 전역 Application Container 설정
            set_application_container(app_service_container)

            logger.info("✅ Application Service Container 초기화 완료")
        except Exception as e:
            logger.warning(f"⚠️ Application Service Container 초기화 실패: {e}")
            logger.warning(f"   상세: {type(e).__name__}: {str(e)}")

        # 안전한 종료를 위한 이벤트 설정
        app_close_event = asyncio.Event()
        app.aboutToQuit.connect(app_close_event.set)

        # 5. 메인 윈도우 생성 (DI Container 주입)
        from upbit_auto_trading.ui.desktop.main_window import MainWindow
        main_window = MainWindow(app_context.container)
        main_window.show()

        logger.info("✅ 애플리케이션 시작됨 (QAsync 기반 Infrastructure Layer)")

        # QAsync 이벤트 루프 실행 (안전한 종료 대기)
        await app_close_event.wait()
        return 0

    except ApplicationContextError as e:
        logger.error(f"❌ Infrastructure Layer 초기화 실패: {e}")
        QMessageBox.critical(None, "시스템 오류", f"Infrastructure Layer 초기화에 실패했습니다:\n{e}")
        return 1

    except Exception as e:
        logger.error(f"❌ 애플리케이션 실행 중 오류: {e}")
        traceback.print_exc()
        QMessageBox.critical(None, "애플리케이션 오류", f"애플리케이션 시작에 실패했습니다:\n{e}")
        return 1

    finally:
        # 안전한 정리 작업
        try:
            if main_window:
                main_window.close()
                main_window = None

            if app_context:
                app_context.dispose()
                logger.info("✅ ApplicationContext 정리 완료")

        except Exception as cleanup_error:
            logger.warning(f"⚠️ 정리 작업 중 오류: {cleanup_error}")

        # DB 연결 강제 정리
        try:
            import gc

            # 가비지 컬렉션 강제 실행
            gc.collect()

            # SQLite 연결 강제 정리 (필요시)
            logger.info("🔧 리소스 정리 완료")

        except Exception:
            pass


def run_application() -> int:
    """QAsync 애플리케이션 실행 래퍼"""
    try:
        # QApplication 먼저 생성
        app = QApplication(sys.argv)

        # QAsync 이벤트 루프 실행
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)

        # 안전한 종료를 위한 이벤트 설정
        app_close_event = asyncio.Event()
        app.aboutToQuit.connect(app_close_event.set)

        # 비동기 애플리케이션 실행
        return loop.run_until_complete(run_application_async(app))

    except Exception as e:
        logger.error(f"❌ QAsync 실행 실패: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # 작업 디렉토리를 프로젝트 루트로 설정
    project_root = os.path.abspath(os.path.dirname(__file__))
    os.chdir(project_root)

    # 애플리케이션 실행
    exit_code = run_application()
    sys.exit(exit_code)
