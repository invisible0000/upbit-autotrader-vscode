"""
DDD/MVP 기반 전략 관리 화면 (신규)
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from upbit_auto_trading.application.di_container import DIContainer
    from upbit_auto_trading.ui.desktop.common.styles.style_manager import StyleManager

from upbit_auto_trading.infrastructure.logging import create_component_logger


class StrategyManagementScreen(QWidget):
    """DDD/MVP 패턴 기반 전략 관리 화면"""

    def __init__(self):
        super().__init__()
        self.logger = create_component_logger("StrategyManagementScreen")
        self.mvp_container = None
        self.style_manager = None
        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 탭 위젯 생성
        self.tab_widget = QTabWidget()

        # 각 탭은 DDD/MVP 기반 컴포넌트로 구현 예정
        from upbit_auto_trading.ui.desktop.common.placeholder_screen import create_placeholder_screen

        # 트리거 빌더 탭 (DDD/MVP 기반)
        trigger_tab = create_placeholder_screen("트리거 빌더 (DDD/MVP)")
        self.tab_widget.addTab(trigger_tab, "트리거 빌더")

        # 전략 메이커 탭 (DDD/MVP 기반)
        strategy_tab = create_placeholder_screen("전략 메이커 (DDD/MVP)")
        self.tab_widget.addTab(strategy_tab, "전략 메이커")

        # 전략 목록 탭 (DDD/MVP 기반)
        list_tab = create_placeholder_screen("전략 목록 (DDD/MVP)")
        self.tab_widget.addTab(list_tab, "전략 목록")

        # 시뮬레이션 탭 (DDD/MVP 기반)
        simulation_tab = create_placeholder_screen("시뮬레이션 (DDD/MVP)")
        self.tab_widget.addTab(simulation_tab, "시뮬레이션")

        layout.addWidget(self.tab_widget)

        self.logger.info("✅ DDD/MVP 기반 전략 관리 화면 초기화 완료")

    def set_mvp_container(self, mvp_container: 'DIContainer'):
        """MVP Container 주입"""
        self.mvp_container = mvp_container
        self.logger.info("✅ MVP Container 주입 완료 (DDD/MVP 기반)")

    def set_style_manager(self, style_manager: 'StyleManager'):
        """StyleManager 주입"""
        self.style_manager = style_manager
        self.logger.info("✅ StyleManager 주입 완료")
