"""
Screen Manager Service - MainWindow의 화면 관리 로직 분리
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from PyQt6.QtWidgets import QWidget, QStackedWidget

from upbit_auto_trading.infrastructure.logging import create_component_logger


class IScreenManagerService(ABC):
    """화면 관리 서비스 인터페이스"""

    @abstractmethod
    def initialize_screens(self, stack_widget: QStackedWidget, screen_widgets: Dict[str, Optional[QWidget]]) -> None:
        """화면 초기화 (대시보드만 즉시 로드, 나머지는 지연 로딩)"""
        pass

    @abstractmethod
    def change_screen(self, screen_name: str, stack_widget: QStackedWidget,
                      screen_widgets: Dict[str, Optional[QWidget]],
                      dependencies: Dict[str, Any]) -> bool:
        """화면 전환"""
        pass

    @abstractmethod
    def load_screen_lazy(self, screen_name: str, screen_widgets: Dict[str, Optional[QWidget]],
                         stack_widget: QStackedWidget, dependencies: Dict[str, Any]) -> Optional[QWidget]:
        """지연 로딩으로 화면 생성"""
        pass


class ScreenManagerService(IScreenManagerService):
    """화면 관리 서비스 구현"""

    def __init__(self):
        self._logger = create_component_logger("ScreenManagerService")
        self._screen_mapping = {
            "dashboard": "대시보드",
            "chart_view": "차트 뷰",
            "screener": "종목 스크리닝",
            "strategy": "매매전략 관리",
            "backtest": "백테스팅",
            "trading": "실시간 거래",
            "portfolio": "포트폴리오 구성",
            "monitoring": "모니터링/알림",
            "settings": "설정"
        }

    def initialize_screens(self, stack_widget: QStackedWidget, screen_widgets: Dict[str, Optional[QWidget]]) -> None:
        """화면 초기화 (대시보드만 즉시 로드, 나머지는 지연 로딩)"""
        try:
            from upbit_auto_trading.ui.desktop.screens.dashboard.dashboard_screen import DashboardScreen

            # 대시보드 화면만 먼저 로드 (기본 화면)
            dashboard_screen = DashboardScreen()
            stack_widget.addWidget(dashboard_screen)
            screen_widgets['대시보드'] = dashboard_screen

            # 나머지 화면들은 지연 로딩을 위해 None으로 초기화
            screen_widgets['차트 뷰'] = None
            screen_widgets['종목 스크리닝'] = None
            screen_widgets['매매전략 관리 (신규)'] = None
            screen_widgets['매매전략 관리 (백업)'] = None
            screen_widgets['백테스팅'] = None
            screen_widgets['실시간 거래'] = None
            screen_widgets['포트폴리오 구성'] = None
            screen_widgets['모니터링/알림'] = None
            screen_widgets['설정'] = None

            self._logger.info("대시보드 화면만 초기화 완료, 나머지는 지연 로딩됩니다")

        except Exception as e:
            self._logger.error(f"화면 초기화 실패: {e}")
            raise

    def change_screen(self, screen_name: str, stack_widget: QStackedWidget,
                      screen_widgets: Dict[str, Optional[QWidget]],
                      dependencies: Dict[str, Any]) -> bool:
        """화면 전환 (지연 로딩 방식)"""
        self._logger.info(f"화면 전환 요청: {screen_name}")

        try:
            # 현재 활성 화면에서 차트뷰인 경우 업데이트 일시정지
            current_widget = stack_widget.currentWidget()
            if current_widget:
                # 차트뷰 화면인지 확인하고 일시정지
                try:
                    if hasattr(current_widget, 'pause_chart_updates'):
                        current_widget.pause_chart_updates()
                except Exception as e:
                    self._logger.warning(f"이전 화면 일시정지 중 오류: {e}")

            # 화면 이름 매핑
            mapped_name = self._screen_mapping.get(screen_name, screen_name)

            # 해당 화면이 이미 로드되었는지 확인
            if screen_widgets.get(mapped_name) is None:
                self._logger.info(f"{mapped_name} 화면 지연 로딩 중...")
                widget = self.load_screen_lazy(mapped_name, screen_widgets, stack_widget, dependencies)
                if widget is None:
                    self._logger.error(f"{mapped_name} 화면 로딩 실패")
                    return False

            # 화면 전환
            widget = screen_widgets.get(mapped_name)
            if widget:
                index = stack_widget.indexOf(widget)
                if index >= 0:
                    stack_widget.setCurrentIndex(index)
                    self._logger.info(f"{mapped_name} 화면으로 전환 완료")

                    # 차트뷰 화면으로 전환한 경우 업데이트 재개
                    try:
                        if hasattr(widget, 'resume_chart_updates'):
                            widget.resume_chart_updates()
                    except Exception as e:
                        self._logger.warning(f"차트뷰 업데이트 재개 중 오류: {e}")

                    return True
                else:
                    self._logger.error(f"{mapped_name} 화면을 스택에서 찾을 수 없습니다")
                    return False
            else:
                self._logger.error(f"{mapped_name} 화면 로딩 실패")
                return False

        except Exception as e:
            self._logger.error(f"화면 전환 중 오류: {e}")
            return False

    def load_screen_lazy(self, screen_name: str, screen_widgets: Dict[str, Optional[QWidget]],
                         stack_widget: QStackedWidget, dependencies: Dict[str, Any]) -> Optional[QWidget]:
        """지연 로딩으로 화면 생성"""
        try:
            screen = None

            if screen_name == "차트 뷰":
                self._logger.info("차트뷰 화면 로딩 중...")
                from upbit_auto_trading.ui.desktop.screens.chart_view.chart_view_screen import ChartViewScreen
                screen = ChartViewScreen()

            elif screen_name == "종목 스크리닝":
                from upbit_auto_trading.ui.desktop.screens.asset_screener.asset_screener_screen import AssetScreenerScreen
                screen = AssetScreenerScreen()

            elif screen_name == "매매전략 관리":
                # DDD/MVP 기반 전략 관리 화면
                from upbit_auto_trading.ui.desktop.screens.strategy_management.strategy_management_screen import (
                    StrategyManagementScreen
                )
                screen = StrategyManagementScreen()

            elif screen_name == "백테스팅":
                from upbit_auto_trading.ui.desktop.screens.backtesting.backtesting_screen import BacktestingScreen
                screen = BacktestingScreen()

            elif screen_name == "실시간 거래":
                from upbit_auto_trading.ui.desktop.screens.live_trading.live_trading_screen import LiveTradingScreen
                screen = LiveTradingScreen()

            elif screen_name == "포트폴리오 구성":
                from upbit_auto_trading.ui.desktop.screens.portfolio_configuration.portfolio_configuration_screen import PortfolioConfigurationScreen
                screen = PortfolioConfigurationScreen()

            elif screen_name == "모니터링/알림":
                from upbit_auto_trading.ui.desktop.screens.monitoring_alerts.monitoring_alerts_screen import MonitoringAlertsScreen
                screen = MonitoringAlertsScreen()

            elif screen_name == "설정":
                screen = self._load_settings_screen(dependencies)

            if screen:
                stack_widget.addWidget(screen)
                screen_widgets[screen_name] = screen
                self._logger.info(f"{screen_name} 화면 생성 및 추가 완료")
                return screen
            else:
                self._logger.error(f"알 수 없는 화면 이름: {screen_name}")
                return None

        except Exception as e:
            self._logger.error(f"{screen_name} 화면 로딩 중 오류: {e}")
            return None

    def _load_settings_screen(self, dependencies: Dict[str, Any]) -> Optional[QWidget]:
        """설정 화면 로딩 (MVP 패턴 적용)"""
        try:
            mvp_container = dependencies.get('mvp_container')
            settings_service = dependencies.get('settings_service')
            parent = dependencies.get('parent')

            # MVP 패턴 적용 (TASK-13: Settings MVP 구현)
            if mvp_container:
                try:
                    # MVP Container를 통해 Settings Presenter와 View 생성
                    settings_view, settings_presenter = mvp_container.create_settings_mvp(
                        settings_service=settings_service,
                        parent=parent
                    )
                    screen = settings_view  # View가 실제 QWidget

                    # Presenter 초기 설정 로드
                    settings_presenter.load_initial_settings()

                    self._logger.info("✅ Settings MVP 패턴 생성 완료")

                except Exception as e:
                    self._logger.error(f"❌ Settings MVP 생성 실패: {e}")
                    # 폴백: 기존 방식
                    from upbit_auto_trading.ui.desktop.screens.settings.settings_screen import SettingsScreen
                    screen = SettingsScreen(settings_service=settings_service, parent=parent)
                    self._logger.warning("⚠️ Settings 기존 방식으로 폴백")
            else:
                # MVP Container가 없으면 기존 방식
                from upbit_auto_trading.ui.desktop.screens.settings.settings_screen import SettingsScreen
                screen = SettingsScreen(settings_service=settings_service, parent=parent)
                self._logger.info("SettingsScreen에 SettingsService 주입 완료 (기존 방식)")

            # 시그널 연결
            self._connect_settings_signals(screen, dependencies)

            return screen

        except Exception as e:
            self._logger.error(f"설정 화면 로딩 실패: {e}")
            return None

    def _connect_settings_signals(self, screen: QWidget, dependencies: Dict[str, Any]) -> None:
        """설정 화면 시그널 연결"""
        try:
            # 설정 변경 시그널 연결
            settings_changed_callback = dependencies.get('settings_changed_callback')
            if hasattr(screen, 'settings_changed') and settings_changed_callback:
                screen.settings_changed.connect(settings_changed_callback)
                self._logger.info("SettingsScreen settings_changed 시그널 연결 완료")

            # 테마 변경 시그널 연결
            theme_changed_callback = dependencies.get('theme_changed_callback')
            if hasattr(screen, 'theme_changed') and theme_changed_callback:
                screen.theme_changed.connect(theme_changed_callback)
                self._logger.info("SettingsScreen theme_changed 시그널 연결 완료")

            # API 상태 변경 시그널 연결
            api_status_changed_callback = dependencies.get('api_status_changed_callback')
            if hasattr(screen, 'api_status_changed') and api_status_changed_callback:
                screen.api_status_changed.connect(api_status_changed_callback)
                self._logger.info("SettingsScreen api_status_changed 시그널 연결 완료")

        except Exception as e:
            self._logger.warning(f"설정 화면 시그널 연결 중 오류: {e}")
