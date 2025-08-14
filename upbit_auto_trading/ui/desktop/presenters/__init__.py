"""
UI Desktop Presenters Package

MVP 패턴의 Presenter 계층을 담당하는 모듈들입니다.
View와 Model 사이의 중재자 역할을 수행합니다.
"""

from .main_window_presenter import IMainWindowPresenter, MainWindowPresenter

__all__ = [
    'IMainWindowPresenter',
    'MainWindowPresenter',
]
