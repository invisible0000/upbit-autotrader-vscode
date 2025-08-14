"""
MainWindow Presenter - MainWindow의 프레젠테이션 로직 분리
DDD Application Layer - MVP 패턴의 Presenter 역할
"""
from typing import Any
from abc import ABC, abstractmethod

from upbit_auto_trading.infrastructure.logging import create_component_logger


class IMainWindowPresenter(ABC):
    """MainWindow 프레젠테이션 로직 인터페이스"""

    @abstractmethod
    def handle_theme_changed_from_service(self, theme_name: str, nav_bar: Any) -> None:
        """ThemeService에서 테마 변경 시그널 처리"""
        pass

    @abstractmethod
    def handle_settings_changed_from_screen(self, window: Any) -> None:
        """설정 화면에서 설정 변경 시그널 처리"""
        pass

    @abstractmethod
    def handle_theme_changed_from_ui_settings(self, theme_name: str, theme_service: Any, nav_bar: Any) -> None:
        """UI 설정에서 테마 변경 처리"""
        pass

    @abstractmethod
    def perform_startup_checks(self, window: Any, api_key_service: Any, database_health_service: Any) -> None:
        """애플리케이션 시작 시 검증 작업 수행"""
        pass


class MainWindowPresenter(IMainWindowPresenter):
    """MainWindow 프레젠테이션 로직 구현"""

    def __init__(self):
        self._logger = create_component_logger("MainWindowPresenter")

    def handle_theme_changed_from_service(self, theme_name: str, nav_bar: Any) -> None:
        """ThemeService에서 테마 변경 시그널을 받았을 때 처리"""
        try:
            self._logger.info(f"ThemeService에서 테마 변경 시그널 수신: {theme_name}")

            # 네비게이션 바 스타일 강제 업데이트
            if nav_bar:
                nav_bar.update()
                nav_bar.repaint()

            # 전역 테마 변경 알림 발송 (기존 컴포넌트와의 호환성)
            self._notify_theme_changed()

        except Exception as e:
            self._logger.error(f"테마 변경 시그널 처리 실패: {e}")

    def handle_settings_changed_from_screen(self, window: Any) -> None:
        """설정 화면에서 설정 변경 시그널을 받았을 때 처리"""
        try:
            self._logger.info("설정 화면에서 설정 변경 시그널 수신")

            # 테마가 변경되었을 수 있으므로 테마 재로드 요청
            if hasattr(window, '_load_theme'):
                window._load_theme()

            # 네비게이션 바 스타일 강제 업데이트
            if hasattr(window, 'nav_bar') and window.nav_bar:
                window.nav_bar.update()
                window.nav_bar.repaint()

        except Exception as e:
            self._logger.error(f"설정 변경 시그널 처리 실패: {e}")

    def handle_theme_changed_from_ui_settings(self, theme_name: str, theme_service: Any, nav_bar: Any) -> None:
        """UI 설정에서 테마 변경 처리"""
        try:
            self._logger.info(f"UI 설정에서 테마 변경 요청: {theme_name}")

            # ThemeService를 통한 테마 설정
            if theme_service:
                # 테마명을 Theme enum으로 변환
                try:
                    from upbit_auto_trading.ui.desktop.common.styles.style_manager import Theme
                    if theme_name.lower() == 'dark':
                        theme_service.set_theme(Theme.DARK)
                    else:
                        theme_service.set_theme(Theme.LIGHT)

                    self._logger.info(f"ThemeService를 통한 테마 설정 완료: {theme_name}")
                except Exception as e:
                    self._logger.warning(f"ThemeService 테마 설정 실패: {e}")

            # 네비게이션 바 스타일 강제 업데이트
            if nav_bar:
                nav_bar.update()
                nav_bar.repaint()

        except Exception as e:
            self._logger.error(f"UI 설정 테마 변경 처리 실패: {e}")

    def perform_startup_checks(self, window: Any, api_key_service: Any, database_health_service: Any) -> None:
        """애플리케이션 시작 시 검증 작업 수행"""
        try:
            self._logger.info("애플리케이션 시작 시 검증 작업 시작")

            # API 키 연결 테스트
            self._perform_api_connection_test(window, api_key_service)

            # DB 건강 검사
            self._perform_database_health_check(window, database_health_service)

            self._logger.info("애플리케이션 시작 시 검증 작업 완료")

        except Exception as e:
            self._logger.error(f"시작 시 검증 작업 실패: {e}")

    def _notify_theme_changed(self) -> None:
        """전역 테마 변경 알림 발송"""
        try:
            from upbit_auto_trading.ui.desktop.common.theme_notifier import get_theme_notifier
            theme_notifier = get_theme_notifier()
            theme_notifier.notify_theme_changed()
            self._logger.info("기존 theme_notifier를 통한 알림 발송 완료")
        except Exception as e:
            self._logger.warning(f"기존 테마 변경 알림 실패: {e}")

    def _perform_api_connection_test(self, window: Any, api_key_service: Any) -> None:
        """API 연결 테스트 수행"""
        try:
            if not api_key_service:
                self._logger.warning("ApiKeyService가 없어 API 연결 테스트 생략")
                return

            # API 키 존재 여부 확인
            has_api_keys = api_key_service.has_api_keys()

            if has_api_keys:
                self._logger.info("API 키 파일 발견 - 연결 테스트 중...")

                # 실제 API 연결 테스트
                is_connected = api_key_service.test_connection()

                if is_connected:
                    self._logger.info("API 연결 테스트 성공 - 정상 연결됨")
                    # StatusBar 업데이트 (있는 경우)
                    if hasattr(window, 'status_bar') and window.status_bar:
                        window.status_bar.update_api_status(True)
                else:
                    self._logger.warning("API 연결 테스트 실패 - 연결 확인 필요")
                    if hasattr(window, 'status_bar') and window.status_bar:
                        window.status_bar.update_api_status(False)
            else:
                self._logger.info("API 키가 설정되지 않음 - 설정 필요")
                if hasattr(window, 'status_bar') and window.status_bar:
                    window.status_bar.update_api_status(None)

        except Exception as e:
            self._logger.error(f"API 연결 테스트 실패: {e}")

    def _perform_database_health_check(self, window: Any, database_health_service: Any) -> None:
        """데이터베이스 건강 검사 수행"""
        try:
            if not database_health_service:
                self._logger.warning("DatabaseHealthService가 없어 DB 건강 검사 생략")
                return

            self._logger.info("🔍 DatabaseHealthService를 통한 DB 건강 검사 시작")

            # DB 건강 검사 수행
            is_healthy = database_health_service.check_database_health_on_startup()

            if is_healthy:
                self._logger.info("📊 DB 상태 업데이트: 연결됨")
                # StatusBar 업데이트 (있는 경우)
                if hasattr(window, 'status_bar') and window.status_bar:
                    window.status_bar.update_db_status("연결됨")
            else:
                self._logger.warning("📊 DB 상태 업데이트: 연결 실패")
                if hasattr(window, 'status_bar') and window.status_bar:
                    window.status_bar.update_db_status("연결 실패")

        except Exception as e:
            self._logger.error(f"데이터베이스 건강 검사 실패: {e}")
