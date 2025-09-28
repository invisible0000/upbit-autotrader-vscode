"""
데스크톱 UI 실행 스크립트 - QAsync AppKernel 기반 통합 버전
목적: 단일 진입점으로 모든 런타임 리소스를 AppKernel을 통해 중앙 관리
"""
import sys
import os
import asyncio
import traceback
from datetime import datetime
from typing import Optional

try:
    import qasync
    from PyQt6.QtWidgets import QApplication, QMessageBox
    QASYNC_AVAILABLE = True
except ImportError as e:
    print(f"❌ QAsync 또는 PyQt6가 설치되지 않았습니다: {e}")
    print("다음 명령어로 설치하세요: pip install qasync PyQt6")
    sys.exit(1)

# AppKernel 및 인프라스트럭처 임포트
from upbit_auto_trading.infrastructure.runtime import (
    AppKernel,
    KernelConfig,
    get_loop_guard,
    ensure_main_loop
)
from upbit_auto_trading.infrastructure.logging import create_component_logger

# UI 컴포넌트 임포트
try:
    from upbit_auto_trading.ui.desktop.main_window import MainWindow
    MAIN_WINDOW_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ MainWindow를 임포트할 수 없습니다: {e}")
    MAIN_WINDOW_AVAILABLE = False

# 기존 ApplicationContext 임포트 (호환성 유지)
try:
    from upbit_auto_trading.infrastructure.dependency_injection.app_context import (
        ApplicationContext,
        ApplicationContextError
    )
    APP_CONTEXT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ ApplicationContext를 임포트할 수 없습니다: {e}")
    APP_CONTEXT_AVAILABLE = False

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 메인 애플리케이션 로거
logger = create_component_logger("MainApp")


def setup_exception_handler():
    """전역 예외 핸들러 설정"""
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
        error_content.append("")

        new_error_text = "\\n".join(error_content)

        try:
            # 기존 내용 읽기
            existing_content = ""
            if os.path.exists(log_file_path):
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()

            # 새 에러를 맨 위에 추가
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write(new_error_text + existing_content)

            logger.error(f"치명적 오류 발생, 로그 파일에 저장됨: {log_file_path}")

        except Exception as log_error:
            print(f"로그 파일 작성 실패: {log_error}")

        # 콘솔에도 출력
        traceback.print_exception(exc_type, exc_value, exc_traceback)

    sys.excepthook = exception_handler


class QAsyncApplication:
    """
    AppKernel 기반 QAsync 애플리케이션 관리자
    """

    def __init__(self):
        self.qapp: Optional[QApplication] = None
        self.kernel: Optional[AppKernel] = None
        self.main_window: Optional[MainWindow] = None
        self.app_context: Optional[ApplicationContext] = None
        self._shutdown_requested = False
        self._shutdown_event = None

    async def initialize(self) -> bool:
        """
        애플리케이션 초기화

        Returns:
            초기화 성공 여부
        """
        try:
            logger.info("🚀 QAsync 애플리케이션 초기화 시작...")

            # 1. QApplication 생성
            if not self.qapp:
                self.qapp = qasync.QApplication(sys.argv)
                logger.info("✅ QAsync QApplication 생성 완료")

            # 2. AppKernel 부트스트랩
            kernel_config = KernelConfig(
                strict_loop_guard=True,
                enable_task_manager=True,
                enable_event_bus=False,  # Step 2에서 구현
                enable_http_clients=True,
                log_level="INFO"
            )

            self.kernel = AppKernel.bootstrap(self.qapp, kernel_config)
            logger.info("✅ AppKernel 부트스트랩 완료")

            # 3. 기존 ApplicationContext 초기화 (호환성)
            if APP_CONTEXT_AVAILABLE:
                try:
                    self.app_context = ApplicationContext()
                    self.app_context.initialize()
                    logger.info("✅ ApplicationContext 초기화 완료 (호환성 레이어)")
                except Exception as e:
                    logger.warning(f"⚠️ ApplicationContext 초기화 실패: {e}")
                    # AppKernel만으로도 동작 가능하므로 계속 진행

            # 4. 메인 윈도우 생성
            if MAIN_WINDOW_AVAILABLE:
                try:
                    # AppKernel 컨텍스트에서 MainWindow 생성
                    ensure_main_loop(where="MainWindow 생성", component="MainApp")

                    if self.app_context:
                        # 기존 방식 (ApplicationContext 사용)
                        self.main_window = MainWindow(self.app_context)
                    else:
                        # AppKernel만 사용하는 새로운 방식 (추후 구현)
                        logger.warning("ApplicationContext 없이 MainWindow 생성은 추후 구현됩니다.")
                        return False

                    # MainWindow 종료 신호를 AppKernel 종료와 연결
                    self.main_window.closeEvent = self._create_close_event_handler()

                    self.main_window.show()
                    logger.info("✅ MainWindow 생성 및 표시 완료")

                    # QApplication 종료 신호도 연결
                    self.qapp.aboutToQuit.connect(self._on_application_quit)

                except Exception as e:
                    logger.error(f"❌ MainWindow 생성 실패: {e}")
                    return False
            else:
                logger.warning("MainWindow를 사용할 수 없어 기본 메시지만 표시합니다.")
                QMessageBox.information(
                    None,
                    "업비트 자동매매 시스템",
                    "AppKernel 기반 QAsync 애플리케이션이 시작되었습니다.\\n"
                    "MainWindow 컴포넌트가 누락되어 기본 UI로 실행됩니다."
                )

            logger.info("🎉 QAsync 애플리케이션 초기화 완료")
            return True

        except Exception as e:
            logger.error(f"❌ 애플리케이션 초기화 실패: {e}")
            traceback.print_exc()
            return False

    def _create_close_event_handler(self):
        """MainWindow closeEvent 핸들러 생성"""
        original_close_event = self.main_window.closeEvent if hasattr(self.main_window, 'closeEvent') else None

        def close_event_handler(event):
            """MainWindow가 닫힐 때 AppKernel 종료 요청"""
            logger.info("🔲 MainWindow 종료 요청 감지")

            # 기존 closeEvent가 있다면 먼저 실행
            if original_close_event and callable(original_close_event):
                try:
                    original_close_event(event)
                except Exception as e:
                    logger.warning(f"⚠️ 기존 closeEvent 실행 중 오류: {e}")

            # AppKernel 종료 요청
            if not self._shutdown_requested:
                self._shutdown_requested = True
                if self._shutdown_event:
                    self._shutdown_event.set()
                logger.info("✅ AppKernel 종료 요청 완료")

            # 이벤트 수락
            event.accept()

        return close_event_handler

    def _on_application_quit(self):
        """QApplication aboutToQuit 신호 핸들러"""
        logger.info("🚪 QApplication 종료 신호 수신")
        if not self._shutdown_requested:
            self._shutdown_requested = True
            if self._shutdown_event:
                self._shutdown_event.set()
            logger.info("✅ QApplication 종료로 인한 AppKernel 종료 요청")

    async def run(self) -> int:
        """
        메인 애플리케이션 실행

        Returns:
            종료 코드
        """
        try:
            if not self.kernel:
                raise RuntimeError("AppKernel이 초기화되지 않았습니다.")

            logger.info("🎬 애플리케이션 메인 루프 시작")

            # 종료 이벤트 생성
            self._shutdown_event = asyncio.Event()

            # 종료 신호 대기 (UI 종료 또는 Ctrl+C)
            import signal

            def signal_handler(signum, frame):
                logger.info(f"🛑 종료 신호 수신: {signum}")
                if not self._shutdown_requested:
                    self._shutdown_requested = True
                    self._shutdown_event.set()

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # 종료 이벤트 대기
            logger.info("⏳ 애플리케이션 실행 중... (UI 종료 또는 Ctrl+C로 종료)")
            await self._shutdown_event.wait()

            logger.info("🏁 애플리케이션 정상 종료")
            return 0

        except KeyboardInterrupt:
            logger.info("🛑 사용자 중단 요청 (Ctrl+C)")
            return 0
        except Exception as e:
            logger.error(f"❌ 애플리케이션 실행 중 오류: {e}")
            traceback.print_exc()
            return 1

    async def shutdown(self) -> None:
        """애플리케이션 종료 및 정리"""
        logger.info("🧹 애플리케이션 종료 시퀀스 시작...")

        try:
            # 1. 메인 윈도우 정리
            if self.main_window:
                try:
                    self.main_window.close()
                    self.main_window = None
                    logger.info("✅ MainWindow 정리 완료")
                except Exception as e:
                    logger.error(f"❌ MainWindow 정리 실패: {e}")

            # 2. ApplicationContext 정리 (호환성)
            if self.app_context:
                try:
                    if hasattr(self.app_context, 'shutdown'):
                        self.app_context.shutdown()
                    if hasattr(self.app_context, 'dispose'):
                        self.app_context.dispose()
                    self.app_context = None
                    logger.info("✅ ApplicationContext 정리 완료")
                except Exception as e:
                    logger.error(f"❌ ApplicationContext 정리 실패: {e}")

            # 3. AppKernel 종료 (자동으로 모든 리소스 정리됨)
            if self.kernel:
                await self.kernel.shutdown()
                self.kernel = None
                logger.info("✅ AppKernel 정리 완료")

            # 4. QApplication 정리
            if self.qapp:
                self.qapp.quit()
                logger.info("✅ QApplication 종료 요청 완료")

            logger.info("🏆 애플리케이션 완전 종료")

        except Exception as e:
            logger.error(f"❌ 종료 시퀀스 오류: {e}")


async def main_async() -> int:
    """메인 비동기 실행 함수"""
    app = QAsyncApplication()

    try:
        # 초기화
        if not await app.initialize():
            logger.error("❌ 애플리케이션 초기화 실패")
            return 1

        # 실행
        return await app.run()

    finally:
        # 정리
        await app.shutdown()


def main() -> int:
    """메인 진입점"""
    if not QASYNC_AVAILABLE:
        print("❌ QAsync가 설치되지 않았습니다.")
        return 1

    try:
        # ✨ 핵심: QApplication을 가장 먼저 생성하여 DPI 설정 선점
        # 다른 모든 초기화보다 앞서서 Qt가 DPI 제어하도록 함
        app = qasync.QApplication(sys.argv)

        # QApplication 생성 후에 나머지 초기화 진행
        setup_exception_handler()
        logger.info("🎯 업비트 자동매매 시스템 시작 (QAsync AppKernel 기반)")

        # QAsync 이벤트 루프 생성
        loop = qasync.QEventLoop(app)

        with loop:
            # AppKernel 기반 메인 애플리케이션 실행
            return loop.run_until_complete(main_async())

    except Exception as e:
        logger.error(f"❌ 메인 실행 실패: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
