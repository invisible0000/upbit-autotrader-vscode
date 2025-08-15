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

        # 트리거 빌더 탭 (DDD/MVP 기반) - 실제 구현
        try:
            from upbit_auto_trading.ui.desktop.screens.strategy_management.tabs.trigger_builder.trigger_builder_tab import (
                TriggerBuilderTab
            )
            trigger_tab = TriggerBuilderTab()
            self.tab_widget.addTab(trigger_tab, "트리거 빌더")
            self.logger.info("✅ 트리거 빌더 탭 실제 구현 로드 완료")
        except Exception as e:
            self.logger.error(f"❌ 트리거 빌더 탭 로드 실패: {e}")
            from upbit_auto_trading.ui.desktop.common.placeholder_screen import create_placeholder_screen
            trigger_tab = create_placeholder_screen(f"트리거 빌더 로드 실패: {str(e)}")
            self.tab_widget.addTab(trigger_tab, "트리거 빌더")

        # 전략 메이커 탭 (DDD/MVP 기반) - placeholder
        from upbit_auto_trading.ui.desktop.common.placeholder_screen import create_placeholder_screen
        strategy_tab = create_placeholder_screen("전략 메이커 (DDD/MVP)")
        self.tab_widget.addTab(strategy_tab, "전략 메이커")

        # 전략 목록 탭 (DDD/MVP 기반) - placeholder
        list_tab = create_placeholder_screen("전략 목록 (DDD/MVP)")
        self.tab_widget.addTab(list_tab, "전략 목록")

        # 시뮬레이션 탭 (DDD/MVP 기반) - placeholder
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
