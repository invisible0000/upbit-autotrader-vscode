"""
Window State Service - MainWindow의 창 상태 관리 로직 분리
"""
from typing import Any, Tuple
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import QSettings

from upbit_auto_trading.infrastructure.logging import create_component_logger


class IWindowStateService:
    """창 상태 관리 서비스 인터페이스"""

    def load_window_state(self, window: QMainWindow, settings_service: Any) -> bool:
        """창 상태 로드"""
        pass

    def save_window_state(self, window: QMainWindow, settings_service: Any) -> bool:
        """창 상태 저장"""
        pass

    def reset_window_size(self, window: QMainWindow, size: Tuple[int, int] = (1280, 720)) -> None:
        """창 크기 초기화"""
        pass

    def reset_window_size_medium(self, window: QMainWindow, size: Tuple[int, int] = (1600, 1000)) -> None:
        """창 크기 초기화 (중간 크기)"""
        pass


class WindowStateService(IWindowStateService):
    """창 상태 관리 서비스 구현"""

    def __init__(self):
        self._logger = create_component_logger("WindowStateService")

    def load_window_state(self, window: QMainWindow, settings_service: Any) -> bool:
        """창 상태 로드 (SettingsService 우선, 실패 시 QSettings 폴백)"""
        try:
            # SettingsService를 통한 창 상태 로드 시도
            if settings_service:
                success = self._load_from_settings_service(window, settings_service)
                if success:
                    return True

            # 폴백: QSettings 사용
            return self._load_from_qsettings(window)

        except Exception as e:
            self._logger.error(f"창 상태 로드 실패: {e}")
            self._set_default_window_state(window)
            return False

    def save_window_state(self, window: QMainWindow, settings_service: Any) -> bool:
        """창 상태 저장 (SettingsService 우선, 실패 시 QSettings 폴백)"""
        try:
            # SettingsService를 통한 창 상태 저장 시도
            if settings_service:
                success = self._save_to_settings_service(window, settings_service)
                if success:
                    return True

            # 폴백: QSettings 사용
            return self._save_to_qsettings(window)

        except Exception as e:
            self._logger.error(f"창 상태 저장 실패: {e}")
            return False

    def reset_window_size(self, window: QMainWindow, size: Tuple[int, int] = (1280, 720)) -> None:
        """창 크기 초기화"""
        try:
            # 기본 크기로 초기화
            window.resize(size[0], size[1])

            self._logger.info(f"창 크기를 {size[0]}x{size[1]}로 초기화했습니다")

            # 모든 위젯 업데이트 (MainWindow의 메서드 호출)
            if hasattr(window, '_update_all_widgets'):
                window._update_all_widgets()

        except Exception as e:
            self._logger.error(f"창 크기 초기화 실패: {e}")

    def reset_window_size_medium(self, window: QMainWindow, size: Tuple[int, int] = (1600, 1000)) -> None:
        """창 크기 초기화 (중간 크기)"""
        try:
            # 중간 크기로 초기화
            window.resize(size[0], size[1])

            self._logger.info(f"창 크기를 중간 크기({size[0]}x{size[1]})로 초기화했습니다")

            # 모든 위젯 업데이트 (MainWindow의 메서드 호출)
            if hasattr(window, '_update_all_widgets'):
                window._update_all_widgets()

        except Exception as e:
            self._logger.error(f"창 크기 초기화 실패: {e}")

    def _load_from_settings_service(self, window: QMainWindow, settings_service: Any) -> bool:
        """SettingsService에서 창 상태 로드"""
        try:
            window_state = settings_service.load_window_state()
            if window_state:
                # 창 크기 설정
                if 'width' in window_state and 'height' in window_state:
                    window.resize(window_state['width'], window_state['height'])
                    self._logger.info(f"SettingsService에서 창 크기 로드: {window_state['width']}x{window_state['height']}")

                # 창 위치 설정
                if 'x' in window_state and 'y' in window_state:
                    window.move(window_state['x'], window_state['y'])
                    self._logger.info(f"SettingsService에서 창 위치 로드: ({window_state['x']}, {window_state['y']})")

                # 최대화 상태 설정
                if window_state.get('maximized', False):
                    window.showMaximized()
                    self._logger.info("SettingsService에서 창 최대화 상태 로드")

                return True
            else:
                self._logger.info("SettingsService에 저장된 창 상태 없음, 기본값 사용")
                return False

        except Exception as e:
            self._logger.warning(f"SettingsService 창 상태 로드 실패, QSettings 사용: {e}")
            return False

    def _load_from_qsettings(self, window: QMainWindow) -> bool:
        """QSettings에서 창 상태 로드"""
        try:
            settings = QSettings("UpbitAutoTrading", "MainWindow")

            # 창 크기 복원
            size = settings.value("size")
            if size:
                window.resize(size)
                self._logger.info(f"QSettings에서 창 크기 로드: {size.width()}x{size.height()}")

            # 창 위치 복원
            position = settings.value("position")
            if position:
                window.move(position)
                self._logger.info(f"QSettings에서 창 위치 로드: ({position.x()}, {position.y()})")

            return True

        except Exception as e:
            self._logger.warning(f"QSettings 창 상태 로드 실패, 기본값 사용: {e}")
            return False

    def _save_to_settings_service(self, window: QMainWindow, settings_service: Any) -> bool:
        """SettingsService에 창 상태 저장"""
        try:
            settings_service.save_window_state(
                x=window.pos().x(),
                y=window.pos().y(),
                width=window.size().width(),
                height=window.size().height(),
                maximized=window.isMaximized()
            )
            self._logger.info("SettingsService를 통한 창 상태 저장 완료")
            return True

        except Exception as e:
            self._logger.warning(f"SettingsService 창 상태 저장 실패, QSettings 사용: {e}")
            return False

    def _save_to_qsettings(self, window: QMainWindow) -> bool:
        """QSettings에 창 상태 저장"""
        try:
            settings = QSettings("UpbitAutoTrading", "MainWindow")
            settings.setValue("size", window.size())
            settings.setValue("position", window.pos())
            self._logger.info("QSettings를 통한 창 상태 저장 완료")
            return True

        except Exception as e:
            self._logger.error(f"QSettings 창 상태 저장 실패: {e}")
            return False

    def _set_default_window_state(self, window: QMainWindow) -> None:
        """기본 창 상태 설정"""
        try:
            window.resize(1600, 1000)
            self._logger.info("기본 창 크기(1600x1000) 설정 완료")
        except Exception as e:
            self._logger.error(f"기본 창 상태 설정 실패: {e}")
