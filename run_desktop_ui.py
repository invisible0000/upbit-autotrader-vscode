"""
데스크톱 UI 실행 스크립트 - Infrastructure Layer 통합 버전
"""
import sys
import os
import traceback
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMessageBox

# Infrastructure Layer import
from upbit_auto_trading.infrastructure.dependency_injection.app_context import ApplicationContext, ApplicationContextError


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

        print(f"✅ ApplicationContext 초기화 완료 (환경: {environment})")
        return app_context

    except ApplicationContextError as e:
        print(f"❌ ApplicationContext 초기화 실패: {e}")
        raise
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        raise


def register_ui_services(app_context: ApplicationContext):
    """UI 전용 서비스들을 DI Container에 등록"""
    try:
        container = app_context.container

        # Infrastructure 통합 로깅 시스템 사용 (새로운 방식)
        print("🔧 Infrastructure 통합 로깅 시스템 연계...")
        try:
            # ApplicationContext에서 이미 등록된 ILoggingService 활용
            from upbit_auto_trading.infrastructure.logging.interfaces.logging_interface import ILoggingService
            logging_service = container.resolve(ILoggingService)
            print("✅ Infrastructure 통합 로깅 시스템 연계 완료")

            # 기존 LoggerFactory 호환성을 위한 추가 등록
            from upbit_auto_trading.logging import LoggerFactory
            container.register_singleton(LoggerFactory, LoggerFactory())
            print("✅ 기존 LoggerFactory 호환성 등록 완료")

        except Exception as e:
            print(f"⚠️ Infrastructure 로깅 연계 실패, 기존 방식 사용: {e}")
            # 폴백: 기존 로깅 시스템
            from upbit_auto_trading.logging import LoggerFactory
            container.register_singleton(LoggerFactory, LoggerFactory())

        # Configuration 서비스 등록 (ApplicationContext에서 이미 생성된 것 활용)
        try:
            from upbit_auto_trading.infrastructure.config.loaders.config_loader import ConfigLoader
            # ApplicationContext 내부의 ConfigLoader 대신 새로 생성해서 등록
            config_loader_instance = ConfigLoader(app_context._config_dir)
            container.register_singleton(ConfigLoader, config_loader_instance)
            print("✅ ConfigurationService 등록 완료")
        except Exception as e:
            print(f"⚠️ ConfigurationService 등록 실패: {e}")

        # SettingsService 등록
        print("🔧 SettingsService 등록 시작...")
        try:
            from upbit_auto_trading.infrastructure.services.settings_service import ISettingsService, SettingsService
            print("🔧 SettingsService 클래스 import 성공")
            config_loader_instance = container.resolve(ConfigLoader)
            print("🔧 ConfigLoader 인스턴스 해결 성공")
            settings_service = SettingsService(config_loader_instance)
            print("🔧 SettingsService 인스턴스 생성 성공")
            container.register_singleton(ISettingsService, settings_service)
            print("✅ SettingsService 등록 완료")
        except Exception as e:
            print(f"⚠️ SettingsService 등록 실패: {e}")
            print(f"    오류 상세: {type(e).__name__}: {str(e)}")
            # MockSettingsService로 폴백
            try:
                from upbit_auto_trading.infrastructure.services.settings_service import ISettingsService, MockSettingsService
                container.register_singleton(ISettingsService, MockSettingsService())
                print("✅ MockSettingsService 폴백 등록 완료")
            except Exception as e2:
                print(f"⚠️ MockSettingsService 폴백도 실패: {e2}")

        # StyleManager 등록
        try:
            from upbit_auto_trading.ui.desktop.common.styles.style_manager import StyleManager
            container.register_singleton(StyleManager, StyleManager())
            print("✅ StyleManager 서비스 등록 완료")
        except ImportError as e:
            print(f"⚠️ StyleManager 로드 실패: {e}")

        # NavigationBar 등록
        try:
            from upbit_auto_trading.ui.desktop.common.widgets.navigation_bar import NavigationBar
            container.register_transient(NavigationBar)
            print("✅ NavigationBar 서비스 등록 완료")
        except ImportError as e:
            print(f"⚠️ NavigationBar 로드 실패: {e}")

        # StatusBar 등록
        try:
            from upbit_auto_trading.ui.desktop.common.widgets.status_bar import StatusBar
            container.register_transient(StatusBar)
            print("✅ StatusBar 서비스 등록 완료")
        except ImportError as e:
            print(f"⚠️ StatusBar 로드 실패: {e}")

        print("✅ UI 서비스 등록 완료")

    except Exception as e:
        print(f"❌ UI 서비스 등록 실패: {e}")
        raise


def setup_application() -> tuple[QApplication, ApplicationContext]:
    """애플리케이션 및 ApplicationContext 설정"""
    # QApplication 생성
    app = QApplication(sys.argv)

    # 1. ApplicationContext 초기화
    app_context = create_application_context()

    # 2. UI 서비스 등록
    register_ui_services(app_context)

    return app, app_context


def run_application() -> int:
    """메인 애플리케이션 실행"""
    app = None
    app_context = None
    main_window = None

    try:
        # 애플리케이션 설정
        app, app_context = setup_application()

        # 3. 메인 윈도우 생성 (DI Container 주입)
        from upbit_auto_trading.ui.desktop.main_window import MainWindow
        main_window = MainWindow(app_context.container)
        main_window.show()

        print("✅ 애플리케이션 시작됨 (Infrastructure Layer 기반)")

        # 애플리케이션 이벤트 루프 시작
        exit_code = app.exec()

        return exit_code

    except ApplicationContextError as e:
        print(f"❌ Infrastructure Layer 초기화 실패: {e}")
        QMessageBox.critical(None, "시스템 오류", f"Infrastructure Layer 초기화에 실패했습니다:\n{e}")
        return 1

    except Exception as e:
        print(f"❌ 애플리케이션 실행 중 오류: {e}")
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
                print("✅ ApplicationContext 정리 완료")

            if app:
                app.quit()
                print("✅ 애플리케이션 정상 종료")

        except Exception as cleanup_error:
            print(f"⚠️ 정리 작업 중 오류: {cleanup_error}")

        # DB 연결 강제 정리
        try:
            import gc
            import sqlite3

            # 가비지 컬렉션 강제 실행
            gc.collect()

            # SQLite 연결 강제 정리 (필요시)
            print("🔧 리소스 정리 완료")

        except Exception:
            pass


if __name__ == "__main__":
    # 작업 디렉토리를 프로젝트 루트로 설정
    project_root = os.path.abspath(os.path.dirname(__file__))
    os.chdir(project_root)

    # 애플리케이션 실행
    exit_code = run_application()
    sys.exit(exit_code)
