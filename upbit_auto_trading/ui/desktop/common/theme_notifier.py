"""
전역 테마 변경 알림 시스템
"""

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from typing import Optional

class ThemeNotifier(QObject):
    """전역 테마 변경 알림을 담당하는 클래스"""

    # 테마 변경 신호
    theme_changed = pyqtSignal(bool)  # True: 다크 테마, False: 라이트 테마

    def __init__(self):
        super().__init__()

    def is_dark_theme(self) -> bool:
        """현재 다크 테마인지 확인"""
        try:
            # 1. StyleManager에서 직접 테마 정보 가져오기
            try:
                from upbit_auto_trading.ui.desktop.common.styles.style_manager import StyleManager
                style_manager = StyleManager()
                current_theme = style_manager.current_theme
                is_dark = current_theme.value == 'dark'
                print(f"🔍 StyleManager 테마: {current_theme.value} -> {'다크' if is_dark else '라이트'}")
                return is_dark
            except Exception as e:
                print(f"⚠️ StyleManager 접근 실패: {e}")

            # 2. QApplication palette 방식 (백업) - 주석 처리
            # app = QApplication.instance()
            # if app:
            #     bg_color_obj = app.palette().color(app.palette().ColorRole.Window)
            #     is_dark = bg_color_obj.lightness() < 128
            #     print(f"🔍 QApplication 팔레트: lightness={bg_color_obj.lightness()} -> {'다크' if is_dark else '라이트'}")
            #     return is_dark
        except Exception as e:
            print(f"⚠️ 테마 감지 실패: {e}")
        return False

    def notify_theme_changed(self):
        """테마 변경 알림 발송"""
        # StyleManager에서 직접 현재 테마 상태 가져오기
        try:
            from upbit_auto_trading.ui.desktop.common.styles.style_manager import StyleManager
            style_manager = StyleManager()
            current_theme = style_manager.current_theme
            is_dark = current_theme.value == 'dark'
            print(f"🎨 테마 전환: {current_theme.value} -> {'다크' if is_dark else '라이트'} 모드 알림 발송")
            self.theme_changed.emit(is_dark)
        except Exception as e:
            print(f"⚠️ 테마 변경 알림 실패: {e}")
            # 백업으로 기존 방식 사용
            is_dark = self.is_dark_theme()
            print(f"🎨 테마 전환 (백업): {'다크' if is_dark else '라이트'}")
            self.theme_changed.emit(is_dark)

# 전역 인스턴스
_theme_notifier = None

def get_theme_notifier() -> ThemeNotifier:
    """전역 테마 알림 인스턴스 반환"""
    global _theme_notifier
    if _theme_notifier is None:
        _theme_notifier = ThemeNotifier()
    return _theme_notifier

def apply_matplotlib_theme_simple():
    """matplotlib에 간단한 테마 적용"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib as mpl
        import logging

        # matplotlib 로깅 레벨을 WARNING으로 설정하여 디버그 출력 억제
        logging.getLogger('matplotlib').setLevel(logging.WARNING)
        logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)

        notifier = get_theme_notifier()
        is_dark = notifier.is_dark_theme()

        # 한글 폰트 설정 (경고 메시지 방지)
        try:
            import matplotlib.font_manager as fm
            # 시스템에서 사용 가능한 한글 폰트 찾기
            font_list = [font.name for font in fm.fontManager.ttflist
                         if 'Gothic' in font.name or 'Malgun' in font.name or '맑은' in font.name]
            if font_list:
                mpl.rcParams['font.family'] = font_list[0]
            else:
                # 기본 폰트 사용 (한글 경고 무시)
                mpl.rcParams['font.family'] = 'sans-serif'
        except Exception:
            pass

        if is_dark:
            print("🎨 다크 테마 적용: matplotlib 'dark_background' 스타일")
            plt.style.use('dark_background')
            # 다크 테마 추가 설정
            mpl.rcParams['axes.edgecolor'] = 'white'  # 차트 테두리
            mpl.rcParams['axes.linewidth'] = 0.8
            mpl.rcParams['xtick.color'] = 'white'
            mpl.rcParams['ytick.color'] = 'white'
            mpl.rcParams['axes.labelcolor'] = 'white'
            mpl.rcParams['text.color'] = 'white'
            mpl.rcParams['figure.facecolor'] = '#2E2E2E'  # 그림 배경
            mpl.rcParams['axes.facecolor'] = '#2E2E2E'    # 축 배경
        else:
            print("🎨 라이트 테마 적용: matplotlib 기본 스타일")
            plt.style.use('default')
            # 라이트 테마 명시적 설정
            mpl.rcParams['axes.edgecolor'] = 'black'  # 차트 테두리
            mpl.rcParams['axes.linewidth'] = 0.8
            mpl.rcParams['xtick.color'] = 'black'
            mpl.rcParams['ytick.color'] = 'black'
            mpl.rcParams['axes.labelcolor'] = 'black'
            mpl.rcParams['text.color'] = 'black'
            mpl.rcParams['figure.facecolor'] = 'white'  # 그림 배경
            mpl.rcParams['axes.facecolor'] = 'white'    # 축 배경

    except Exception as e:
        print(f"⚠️ matplotlib 테마 적용 실패: {e}")
