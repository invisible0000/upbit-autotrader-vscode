#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
테마 관리자 - 전역 테마 상태 관리 및 감지
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Optional
import os


class ThemeManager(QObject):
    """테마 관리자 - 싱글톤 패턴으로 전역 테마 상태 관리"""
    
    # 테마 변경 시그널
    theme_changed = pyqtSignal(bool)  # True: 다크 테마, False: 라이트 테마
    
    def __init__(self):
        super().__init__()
        self._current_style_file = None
        self._is_dark_theme = False
        
    def is_dark_theme(self) -> bool:
        """현재 다크 테마인지 확인"""
        try:
            # 1. QApplication 팔레트로 감지 (가장 정확)
            if QApplication.instance():
                palette = QApplication.instance().palette()
                bg_color_obj = palette.color(palette.ColorRole.Window)
                self._is_dark_theme = bg_color_obj.lightness() < 128
                return self._is_dark_theme
            
            # 2. 현재 로드된 스타일 파일로 감지
            if self._current_style_file:
                self._is_dark_theme = 'dark' in self._current_style_file.lower()
                return self._is_dark_theme
                
        except Exception as e:
            print(f"⚠️ 테마 감지 실패: {e}")
            
        return self._is_dark_theme
    
    def get_theme_name(self) -> str:
        """현재 테마 이름 반환"""
        return "dark" if self.is_dark_theme() else "light"
    
    def set_current_style_file(self, style_file_path: str):
        """현재 사용 중인 스타일 파일 설정"""
        self._current_style_file = style_file_path
        old_theme = self._is_dark_theme
        new_theme = self.is_dark_theme()
        
        # 테마가 변경되었으면 시그널 발생
        if old_theme != new_theme:
            self.theme_changed.emit(new_theme)
    
    def get_matplotlib_style(self) -> str:
        """matplotlib 스타일 반환"""
        return 'dark_background' if self.is_dark_theme() else 'default'
    
    def get_plotly_template(self) -> str:
        """plotly 템플릿 반환"""
        return 'plotly_dark' if self.is_dark_theme() else 'plotly_white'
    
    def get_chart_colors(self) -> dict:
        """차트용 색상 팔레트 반환"""
        if self.is_dark_theme():
            return {
                'text': '#e0e0e0',
                'grid': 'rgba(255,255,255,0.2)',
                'background': 'rgba(0,0,0,0)',
                'line_colors': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
            }
        else:
            return {
                'text': '#333333',
                'grid': 'lightgray',
                'background': 'rgba(255,255,255,0)',
                'line_colors': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
            }


# 전역 테마 매니저 인스턴스
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """전역 테마 매니저 인스턴스 반환"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def is_dark_theme() -> bool:
    """현재 다크 테마인지 확인 (편의 함수)"""
    return get_theme_manager().is_dark_theme()


def get_matplotlib_style() -> str:
    """matplotlib 스타일 반환 (편의 함수)"""
    return get_theme_manager().get_matplotlib_style()


def get_plotly_template() -> str:
    """plotly 템플릿 반환 (편의 함수)"""
    return get_theme_manager().get_plotly_template()


def get_chart_colors() -> dict:
    """차트용 색상 팔레트 반환 (편의 함수)"""
    return get_theme_manager().get_chart_colors()


def apply_matplotlib_theme():
    """matplotlib에 현재 테마 적용 (편의 함수)"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib as mpl
        
        if is_dark_theme():
            plt.style.use('dark_background')
            # 추가 다크 테마 설정
            mpl.rcParams.update({
                'text.color': '#e0e0e0',
                'axes.labelcolor': '#e0e0e0',
                'xtick.color': '#e0e0e0',
                'ytick.color': '#e0e0e0',
                'grid.color': 'rgba(255,255,255,0.2)',
                'figure.facecolor': 'none',
                'axes.facecolor': 'none'
            })
        else:
            plt.style.use('default')
            # 라이트 테마 설정
            mpl.rcParams.update({
                'text.color': '#333333',
                'axes.labelcolor': '#333333',
                'xtick.color': '#333333',
                'ytick.color': '#333333',
                'grid.color': 'lightgray',
                'figure.facecolor': 'none',
                'axes.facecolor': 'none'
            })
            
    except ImportError:
        print("⚠️ matplotlib이 설치되지 않았습니다.")
    except Exception as e:
        print(f"⚠️ matplotlib 테마 적용 실패: {e}")
