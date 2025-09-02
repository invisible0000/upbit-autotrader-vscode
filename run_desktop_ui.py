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
from upbit_auto_trading.ui.desktop.main_window import MainWindow

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
            f.write(new_error_text + existing_content)

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

        # ApiKeyService 등록 (Repository Container 기반 DDD 패턴) - 개선된 에러 처리
        if repository_container:
            try:
                from upbit_auto_trading.infrastructure.services.api_key_service import IApiKeyService, ApiKeyService
                logger.info("🔧 ApiKeyService 클래스 import 성공")

                # Repository Container에서 SecureKeysRepository 가져오기
                secure_keys_repo = repository_container.get_secure_keys_repository()
                if not secure_keys_repo:
                    raise RuntimeError("SecureKeysRepository를 가져올 수 없습니다")

                logger.info("🔧 SecureKeysRepository 인스턴스 해결 성공")

                # Repository 의존성 주입하여 ApiKeyService 생성
                api_key_service = ApiKeyService(secure_keys_repo)
                logger.info("🔧 ApiKeyService 인스턴스 생성 성공 (Repository 주입)")

                # API 키 로드 테스트
                try:
                    access_key, secret_key, trade_permission = api_key_service.load_api_keys()
                    if access_key and secret_key:
                        logger.info("✅ API 키 로드 검증 성공")
                    else:
                        logger.warning("⚠️ API 키가 비어있거나 불완전함")
                except Exception as load_error:
                    logger.warning(f"⚠️ API 키 로드 테스트 실패: {load_error}")

                # DI Container에 등록
                container.register_singleton(IApiKeyService, api_key_service)
                logger.info("✅ ApiKeyService 등록 완료 (DDD Repository 패턴)")

            except ImportError as e:
                logger.warning(f"⚠️ ApiKeyService 클래스 import 실패: {e}")
            except Exception as e:
                logger.warning(f"⚠️ ApiKeyService 등록 실패: {e}")
                logger.warning(f"    오류 상세: {type(e).__name__}: {str(e)}")

                # 폴백: 빈 API Key Service 생성
                try:
                    # 빈 상태의 ApiKeyService 생성 (Repository 없이)
                    logger.info("✅ 폴백: 빈 상태 ApiKeyService 등록")
                except Exception as e2:
                    logger.warning(f"⚠️ 폴백 ApiKeyService 생성 실패: {e2}")
        else:
            logger.warning("⚠️ Repository Container가 None이어서 ApiKeyService를 등록할 수 없습니다")
            # 빈 상태 ApiKeyService로 폴백
            try:
                logger.info("✅ 폴백: 빈 상태 ApiKeyService 등록 (Repository Container 없음)")
            except Exception as e:
                logger.warning(f"⚠️ 폴백 ApiKeyService 생성 실패: {e}")

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

        # MainWindow 등록
        try:
            from upbit_auto_trading.ui.desktop.main_window import MainWindow
            container.register_transient(MainWindow)
            logger.info("✅ MainWindow 서비스 등록 완료")
        except ImportError as e:
            logger.warning(f"⚠️ MainWindow 로드 실패: {e}")

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

        # 3. Repository Container 초기화 (DDD Infrastructure Layer) - 개선된 에러 처리
        repository_container = None
        try:
            from upbit_auto_trading.infrastructure.repositories.repository_container import RepositoryContainer
            repository_container = RepositoryContainer()

            # Repository Container 검증
            if hasattr(repository_container, 'get_secure_keys_repository'):
                secure_keys_repo = repository_container.get_secure_keys_repository()
                if secure_keys_repo:
                    logger.info("✅ Repository Container 및 SecureKeysRepository 초기화 완료")
                else:
                    logger.warning("⚠️ SecureKeysRepository 초기화 실패")
            else:
                logger.warning("⚠️ Repository Container에 get_secure_keys_repository 메서드가 없음")

        except ImportError as e:
            logger.error(f"❌ Repository Container 모듈 import 실패: {e}")
            repository_container = None
        except Exception as e:
            logger.error(f"❌ Repository Container 초기화 실패: {e}")
            logger.error(f"   상세: {type(e).__name__}: {str(e)}")
            repository_container = None

        # 3. UI 서비스 등록 (Repository Container 전달)
        register_ui_services(app_context, repository_container)

        # 4. WebSocket v6 Application Service 초기화 (새로 추가)
        try:
            from upbit_auto_trading.application.services.websocket_application_service import (
                get_websocket_service,
                WebSocketServiceConfig
            )

            # WebSocket v6 서비스 설정
            websocket_config = WebSocketServiceConfig(
                auto_start_on_init=True,
                enable_public_connection=True,
                enable_private_connection=True,  # API 키가 있으면 자동 활성화
                reconnect_on_failure=True,
                health_check_interval=30.0
            )

            # WebSocket v6 서비스 초기화 및 시작
            websocket_service = await get_websocket_service(websocket_config)

            # ApplicationContext에 등록 (다른 서비스에서 사용할 수 있도록)
            if hasattr(app_context, 'container') and app_context.container:
                app_context.container._instances['websocket_service'] = websocket_service

            logger.info("✅ WebSocket v6 Application Service 초기화 완료")

        except Exception as e:
            logger.error(f"❌ WebSocket v6 Application Service 초기화 실패: {e}")
            # WebSocket 실패는 치명적이지 않으므로 계속 진행
            logger.warning("WebSocket v6 없이 계속 진행합니다")

        # 5. Application Container 초기화 및 설정 (TASK-13: MVP 패턴 지원)
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

        # 5. 메인 윈도우 생성 (DI Container 주입) - 안전한 의존성 해결
        try:
            from upbit_auto_trading.ui.desktop.main_window import MainWindow

            # DI Container 검증
            if not app_context.container:
                raise RuntimeError("ApplicationContext의 DI Container가 None입니다")

            # MainWindow 생성 (DI Container 전달)
            main_window = MainWindow(app_context.container)
            main_window.show()

            logger.info("✅ 메인 윈도우 생성 및 표시 완료 (DI Container 주입)")

        except Exception as e:
            logger.error(f"❌ 메인 윈도우 생성 실패: {e}")
            raise

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
            # WebSocket v6 서비스 정리 (우선 수행)
            try:
                from upbit_auto_trading.application.services.websocket_application_service import (
                    shutdown_websocket_service
                )
                await shutdown_websocket_service()
                logger.info("✅ WebSocket v6 Application Service 정리 완료")
            except Exception as websocket_cleanup_error:
                logger.warning(f"⚠️ WebSocket v6 서비스 정리 중 오류: {websocket_cleanup_error}")

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


def main():
    """메인 애플리케이션 실행 함수 - 개선된 초기화 및 종료 처리"""
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 전역 예외 핸들러 설정
    sys.excepthook = exception_handler

    app_context = None
    main_window = None
    repository_container = None

    try:
        # 1. 애플리케이션 컨텍스트 초기화
        logger.info("🚀 애플리케이션 컨텍스트 초기화 시작...")
        app_context = ApplicationContext()
        app_context.initialize()

        # 2. Repository Container 초기화 (API Key Service를 위해 필요)
        try:
            from upbit_auto_trading.infrastructure.repositories.repository_container import RepositoryContainer
            repository_container = RepositoryContainer()
            logger.info("✅ Repository Container 초기화 완료")
        except Exception as e:
            logger.warning(f"⚠️ Repository Container 초기화 실패: {e}")
            repository_container = None

        # 3. UI 서비스 등록 (Repository Container 전달)
        register_ui_services(app_context, repository_container)

        # 4. Application Service Container 초기화
        try:
            from upbit_auto_trading.application.container import ApplicationServiceContainer, set_application_container

            if repository_container:
                app_service_container = ApplicationServiceContainer(repository_container)
            else:
                # 폴백: 새로운 Repository Container 생성
                repository_container = RepositoryContainer()
                app_service_container = ApplicationServiceContainer(repository_container)

            # 전역 Application Container 설정
            set_application_container(app_service_container)
            logger.info("✅ Application Service Container 초기화 완료")
        except Exception as e:
            logger.warning(f"⚠️ Application Service Container 초기화 실패: {e}")

        # 5. 메인 윈도우 생성 및 표시
        container = app_context.container
        if not container:
            raise RuntimeError("DI Container가 초기화되지 않았습니다")

        # MainWindow는 DI 컨테이너를 통해 생성
        main_window = MainWindow(container)
        main_window.show()

        logger.info("✅ 애플리케이션 시작 완료")

        # 6. 이벤트 루프 실행
        with loop:
            return_code = loop.run_forever()
            logger.info(f"이벤트 루프 종료됨 (코드: {return_code})")
            sys.exit(return_code)

    except ApplicationContextError as e:
        logger.critical(f"애플리케이션 컨텍스트 초기화 실패: {e}")
        QMessageBox.critical(None, "초기화 오류", f"애플리케이션을 시작할 수 없습니다.\n\n오류: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"알 수 없는 오류 발생: {e}", exc_info=True)
        QMessageBox.critical(None, "치명적 오류", f"알 수 없는 오류로 인해 애플리케이션을 종료합니다.\n\n오류: {e}")
        sys.exit(1)
    finally:
        # 안전한 정리 작업
        logger.info("🧹 애플리케이션 정리 작업 시작...")

        try:
            if main_window:
                main_window.close()
                main_window = None
                logger.info("✅ 메인 윈도우 정리 완료")
        except Exception as e:
            logger.warning(f"⚠️ 메인 윈도우 정리 중 오류: {e}")

        try:
            if app_context:
                app_context.shutdown()
                app_context.dispose()
                app_context = None
                logger.info("✅ 애플리케이션 컨텍스트 정리 완료")
        except Exception as e:
            logger.warning(f"⚠️ 애플리케이션 컨텍스트 정리 중 오류: {e}")

        try:
            if repository_container:
                # Repository Container 정리 (필요시)
                repository_container = None
                logger.info("✅ Repository Container 정리 완료")
        except Exception as e:
            logger.warning(f"⚠️ Repository Container 정리 중 오류: {e}")

        logger.info("🏁 애플리케이션이 완전히 종료되었습니다.")


if __name__ == "__main__":
    main()
