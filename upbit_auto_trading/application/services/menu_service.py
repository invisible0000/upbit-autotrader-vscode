"""
Menu Service - MainWindow의 메뉴 관리 로직 분리
"""
from typing import Any
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtGui import QAction

from upbit_auto_trading.infrastructure.logging import create_component_logger


class IMenuService:
    """메뉴 관리 서비스 인터페이스"""

    def setup_menu_bar(self, window: QMainWindow, dependencies: dict) -> None:
        """메뉴 바 설정"""
        pass

    def toggle_theme(self, theme_service: Any, style_manager: Any, nav_bar: Any) -> None:
        """테마 전환"""
        pass

    def show_about_dialog(self, parent: QMainWindow) -> None:
        """정보 대화상자 표시"""
        pass


class MenuService(IMenuService):
    """메뉴 관리 서비스 구현"""

    def __init__(self):
        self._logger = create_component_logger("MenuService")

    def setup_menu_bar(self, window: QMainWindow, dependencies: dict) -> None:
        """메뉴 바 설정"""
        try:
            self._setup_file_menu(window, dependencies)
            self._setup_view_menu(window, dependencies)
            self._setup_help_menu(window, dependencies)
            self._logger.info("메뉴 바 설정 완료")

        except Exception as e:
            self._logger.error(f"메뉴 바 설정 실패: {e}")
            raise

    def toggle_theme(self, theme_service: Any, style_manager: Any, nav_bar: Any) -> None:
        """테마 전환 (ThemeService 우선, 실패 시 StyleManager 폴백)"""
        try:
            if theme_service:
                try:
                    # ThemeService를 통한 테마 전환
                    new_theme = theme_service.toggle_theme()
                    self._logger.info(f"ThemeService를 통한 테마 전환 완료: {new_theme}")

                    # 네비게이션 바 스타일 강제 업데이트
                    if nav_bar:
                        nav_bar.update()
                        nav_bar.repaint()
                    return

                except Exception as e:
                    self._logger.warning(f"ThemeService 테마 전환 실패, StyleManager 사용: {e}")

            # 폴백: StyleManager 사용
            if style_manager:
                style_manager.toggle_theme()
                self._logger.info("StyleManager를 통한 테마 전환 완료")

                # 네비게이션 바 스타일 강제 업데이트
                if nav_bar:
                    nav_bar.update()
                    nav_bar.repaint()
            else:
                self._logger.error("테마 전환 실패: ThemeService 및 StyleManager 모두 사용 불가")

        except Exception as e:
            self._logger.error(f"테마 전환 중 오류: {e}")

    def show_about_dialog(self, parent: QMainWindow) -> None:
        """정보 대화상자 표시"""
        try:
            QMessageBox.about(
                parent,
                "업비트 자동매매 시스템",
                "업비트 자동매매 시스템 v1.0.0\n\n"
                "업비트 API를 활용한 암호화폐 자동 거래 시스템입니다.\n"
                "© 2025 업비트 자동매매 시스템"
            )
            self._logger.info("정보 대화상자 표시 완료")

        except Exception as e:
            self._logger.error(f"정보 대화상자 표시 실패: {e}")

    def _setup_file_menu(self, window: QMainWindow, dependencies: dict) -> None:
        """파일 메뉴 설정"""
        try:
            file_menu = window.menuBar().addMenu("파일")

            # 설정 액션
            settings_action = QAction("설정", window)
            change_screen_callback = dependencies.get('change_screen_callback')
            if change_screen_callback:
                settings_action.triggered.connect(lambda: change_screen_callback("settings"))
            file_menu.addAction(settings_action)

            # 종료 액션
            exit_action = QAction("종료", window)
            exit_action.triggered.connect(window.close)
            file_menu.addAction(exit_action)

            self._logger.debug("파일 메뉴 설정 완료")

        except Exception as e:
            self._logger.error(f"파일 메뉴 설정 실패: {e}")
            raise

    def _setup_view_menu(self, window: QMainWindow, dependencies: dict) -> None:
        """보기 메뉴 설정"""
        try:
            view_menu = window.menuBar().addMenu("보기")

            # 테마 전환 액션
            theme_action = QAction("테마 전환", window)
            toggle_theme_callback = dependencies.get('toggle_theme_callback')
            if toggle_theme_callback:
                theme_action.triggered.connect(toggle_theme_callback)
            view_menu.addAction(theme_action)

            # 구분선 추가
            view_menu.addSeparator()

            # 창 크기 초기화 액션
            reset_size_action = QAction("창 크기 초기화", window)
            window_state_service = dependencies.get('window_state_service')
            if window_state_service:
                reset_size_action.triggered.connect(
                    lambda: window_state_service.reset_window_size(window)
                )
            view_menu.addAction(reset_size_action)

            # 창 크기 초기화 (중간) 액션
            reset_size_medium_action = QAction("창 크기 초기화(중간)", window)
            if window_state_service:
                reset_size_medium_action.triggered.connect(
                    lambda: window_state_service.reset_window_size_medium(window)
                )
            view_menu.addAction(reset_size_medium_action)

            self._logger.debug("보기 메뉴 설정 완료")

        except Exception as e:
            self._logger.error(f"보기 메뉴 설정 실패: {e}")
            raise

    def _setup_help_menu(self, window: QMainWindow, dependencies: dict) -> None:
        """도움말 메뉴 설정"""
        try:
            help_menu = window.menuBar().addMenu("도움말")

            # 정보 액션
            about_action = QAction("정보", window)
            about_action.triggered.connect(lambda: self.show_about_dialog(window))
            help_menu.addAction(about_action)

            self._logger.debug("도움말 메뉴 설정 완료")

        except Exception as e:
            self._logger.error(f"도움말 메뉴 설정 실패: {e}")
            raise
