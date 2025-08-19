"""
차트 뷰 화면 - Phase 2 구현

기존 InMemoryEventBus와 호환되는 3열 동적 레이아웃 차트뷰어입니다.
마켓 데이터 백본과 연동하여 실시간 차트 및 호가 데이터를 제공합니다.
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.ui.desktop.screens.chart_view.widgets.dynamic_splitter import DynamicSplitter
from upbit_auto_trading.ui.desktop.screens.chart_view.presenters.window_lifecycle_presenter import WindowLifecyclePresenter
from upbit_auto_trading.ui.desktop.screens.chart_view.widgets.coin_list_widget import CoinListWidget
from upbit_auto_trading.ui.desktop.screens.chart_view.widgets.orderbook_widget import OrderbookWidget
from upbit_auto_trading.domain.events.chart_viewer_events import ChartSubscriptionEvent, ChartViewerPriority


class ChartViewScreen(QWidget):
    """
    차트 뷰 화면 - Phase 2 구현

    3열 동적 레이아웃(1:4:2 비율):
    - 좌측: 코인 리스트 패널
    - 중앙: 차트 영역 패널
    - 우측: 호가창 패널
    """

    # 시그널 정의
    coin_selected = pyqtSignal(str)  # 코인 선택 시그널
    timeframe_changed = pyqtSignal(str)  # 타임프레임 변경 시그널
    layout_changed = pyqtSignal()  # 레이아웃 변경 시그널

    def __init__(self, parent: Optional[QWidget] = None):
        """차트 뷰 화면 초기화"""
        super().__init__(parent)

        self._logger = create_component_logger("ChartViewScreen")
        self._logger.info("� Phase 2 차트 뷰 화면 초기화 시작")

        # 상태 관리
        self._layout_state: Dict[str, Any] = {}
        self._is_active = True

        # UI 컴포넌트
        self._splitter: Optional[DynamicSplitter] = None
        self._coin_list_panel: Optional[CoinListWidget] = None
        self._chart_area_panel: Optional[QWidget] = None
        self._orderbook_panel: Optional[OrderbookWidget] = None

        # 프레젠터
        self._window_lifecycle_presenter: Optional[WindowLifecyclePresenter] = None

        # UI 초기화
        self._setup_ui()
        self._setup_layout()
        self._setup_presenters()

        # 지연 초기화 (창이 완전히 로드된 후)
        QTimer.singleShot(100, self._post_init_setup)

        self._logger.info("✅ Phase 2 차트 뷰 화면 초기화 완료")

    def _setup_ui(self) -> None:
        """기본 UI 구조 설정"""
        self.setWindowTitle("차트 뷰어 - Phase 2")
        self.setMinimumSize(800, 600)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 동적 스플리터 생성
        self._splitter = DynamicSplitter(self)
        self._splitter.layout_changed.connect(self._on_layout_changed)

        main_layout.addWidget(self._splitter)

        self._logger.debug("기본 UI 구조 설정 완료")

    def _setup_layout(self) -> None:
        """3열 레이아웃 설정"""
        # 패널들 생성
        self._coin_list_panel = self._create_coin_list_panel()
        self._chart_area_panel = self._create_chart_area_panel()
        self._orderbook_panel = self._create_orderbook_panel()

        # 스플리터에 패널 추가
        panels = [
            self._coin_list_panel,
            self._chart_area_panel,
            self._orderbook_panel
        ]

        self._splitter.setup_layout(panels)

        self._logger.info("🎯 3열 레이아웃(1:4:2) 설정 완료")

    def _setup_presenters(self) -> None:
        """프레젠터 초기화"""
        # 창 생명주기 프레젠터 초기화
        self._window_lifecycle_presenter = WindowLifecyclePresenter(self)

        # 시그널 연결
        self._window_lifecycle_presenter.state_changed.connect(self._on_window_state_changed)
        self._window_lifecycle_presenter.resource_optimized.connect(self._on_resource_optimized)

        self._logger.info("✅ 프레젠터 초기화 완료")

    def _on_window_state_changed(self, state: str) -> None:
        """창 상태 변경 처리"""
        self._logger.info(f"🔄 창 상태 변경: {state}")

        # 상태에 따른 리소스 조정
        if state == "active":
            self._is_active = True
        elif state in ["inactive", "minimized", "hidden"]:
            self._is_active = False

    def _on_resource_optimized(self, saving_rate: float) -> None:
        """리소스 최적화 처리"""
        self._logger.debug(f"💡 리소스 절약: {saving_rate:.1%}")

    def _on_coin_selected(self, symbol: str) -> None:
        """코인 선택 처리 - 호가창 연동 강화"""
        self._logger.info(f"💰 코인 선택: {symbol}")
        self.coin_selected.emit(symbol)

        # 호가창 심벌 업데이트 (고급 기능 포함)
        if hasattr(self._orderbook_panel, 'set_symbol'):
            self._orderbook_panel.set_symbol(symbol)

            # 호가창 정보 로깅 (실제 매매 지원 확인)
            if hasattr(self._orderbook_panel, 'get_widget_info'):
                widget_info = self._orderbook_panel.get_widget_info()
                self._logger.debug(
                    f"호가창 정보: 마켓={widget_info.get('current_market')}, "
                    f"틱사이즈={widget_info.get('tick_size')}, "
                    f"모아보기지원={widget_info.get('grouping_support')}"
                )

        # DDD Infrastructure 레이어로 실제 데이터 요청 이벤트 발행
        self._request_orderbook_data(symbol)

    def _request_orderbook_data(self, symbol: str) -> None:
        """DDD 아키텍처 기반 실제 호가 데이터 요청 (Infrastructure 레이어 연동)"""
        try:
            # Phase 2에서는 샘플 데이터가 이미 로드되었으므로 로깅만 수행
            # Phase 3에서 실제 Infrastructure 이벤트 버스 연동 예정
            self._logger.info(f"🔄 호가 데이터 요청 준비: {symbol} (Phase 3에서 실제 API 연동 예정)")

            # 향후 Infrastructure 레이어 이벤트 발행 예정:
            # subscription_event = ChartSubscriptionEvent(
            #     chart_id=f"orderbook_{symbol}",
            #     symbol=symbol,
            #     data_type="orderbook",
            #     timeframe="realtime",
            #     action="subscribe",
            #     priority_level=ChartViewerPriority.ORDERBOOK_HIGH
            # )
            # await self._event_bus.publish(subscription_event)

        except Exception as e:
            self._logger.error(f"호가 데이터 요청 실패: {symbol} - {e}")

    def _on_market_changed(self, market: str) -> None:
        """마켓 변경 처리"""
        self._logger.info(f"📊 마켓 변경: {market}")

    def _on_favorite_toggled(self, symbol: str, is_favorite: bool) -> None:
        """즐겨찾기 토글 처리"""
        action = "추가" if is_favorite else "제거"
        self._logger.debug(f"⭐ 즐겨찾기 {action}: {symbol}")

    def _create_coin_list_panel(self) -> CoinListWidget:
        """코인 리스트 패널 생성 (좌측 - 1 비율)"""
        # 실제 코인 리스트 위젯 사용
        coin_list_widget = CoinListWidget()
        coin_list_widget.setMinimumWidth(200)

        # 시그널 연결
        coin_list_widget.coin_selected.connect(self._on_coin_selected)
        coin_list_widget.market_changed.connect(self._on_market_changed)
        coin_list_widget.favorite_toggled.connect(self._on_favorite_toggled)

        self._logger.debug("실제 코인 리스트 위젯 생성 완료")
        return coin_list_widget

    def _create_chart_area_panel(self) -> QWidget:
        """차트 영역 패널 생성 (중앙 - 4 비율)"""
        panel = QWidget()
        panel.setMinimumWidth(400)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # 컨트롤 패널 (상단)
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)

        # 차트 영역 (메인)
        chart_area = QWidget()
        chart_area.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")

        chart_layout = QVBoxLayout(chart_area)
        chart_layout.setContentsMargins(10, 10, 10, 10)

        # 메인 플롯 영역 (3/4)
        main_plot = QWidget()
        main_plot.setStyleSheet("background-color: white; border: 1px solid #ddd;")
        main_plot.setMinimumHeight(300)

        main_plot_layout = QVBoxLayout(main_plot)
        main_plot_title = QLabel("캔들스틱 차트 (메인 플롯)")
        main_plot_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_plot_content = QLabel("Phase 3에서 PyQtGraph 구현 예정")
        main_plot_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_plot_layout.addWidget(main_plot_title)
        main_plot_layout.addWidget(main_plot_content)
        main_plot_layout.addStretch()

        # 서브 플롯 영역 (1/4)
        sub_plot = QWidget()
        sub_plot.setStyleSheet("background-color: white; border: 1px solid #ddd;")
        sub_plot.setMinimumHeight(100)
        sub_plot.setMaximumHeight(150)

        sub_plot_layout = QVBoxLayout(sub_plot)
        sub_plot_title = QLabel("📊 거래량 (서브 플롯)")
        sub_plot_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_plot_content = QLabel("MACD, RSI, ATR, STOCH 선택 가능")
        sub_plot_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_plot_layout.addWidget(sub_plot_title)
        sub_plot_layout.addWidget(sub_plot_content)

        chart_layout.addWidget(main_plot, 3)  # 3/4 비율
        chart_layout.addWidget(sub_plot, 1)   # 1/4 비율

        layout.addWidget(chart_area, 1)

        self._logger.debug("차트 영역 패널 생성 완료")
        return panel

    def _create_control_panel(self) -> QWidget:
        """차트 컨트롤 패널 생성"""
        panel = QWidget()
        panel.setMaximumHeight(50)
        panel.setStyleSheet("background-color: #e8e8e8; border: 1px solid #ccc;")

        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 5, 10, 5)

        # 타임프레임 선택
        timeframe_label = QLabel("타임프레임:")
        timeframe_info = QLabel("1m, 3m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M")

        # 데이터 소스 선택
        source_label = QLabel("데이터 소스:")
        source_info = QLabel("☑️ WebSocket ☐ API")

        layout.addWidget(timeframe_label)
        layout.addWidget(timeframe_info)
        layout.addStretch()
        layout.addWidget(source_label)
        layout.addWidget(source_info)

        return panel

    def _create_orderbook_panel(self) -> OrderbookWidget:
        """호가창 패널 생성 (우측 - 2 비율) - 실제 매매 지원"""
        # 실제 호가창 위젯 사용
        orderbook_widget = OrderbookWidget()
        orderbook_widget.setMinimumWidth(200)

        # 호가창 고급 기능 시그널 연결
        orderbook_widget.price_clicked.connect(self._on_orderbook_price_clicked)
        orderbook_widget.orderbook_updated.connect(self._on_orderbook_updated)
        orderbook_widget.market_impact_analyzed.connect(self._on_market_impact_analyzed)
        orderbook_widget.optimal_price_suggested.connect(self._on_optimal_price_suggested)

        # 기본 심벌 설정 (KRW-BTC)
        orderbook_widget.set_symbol("KRW-BTC")

        self._logger.info("호가창 위젯 생성 완료 (실제 매매 지원)")
        return orderbook_widget

    def _on_orderbook_price_clicked(self, order_type: str, price: float) -> None:
        """호가창 가격 클릭 처리 (실제 매매 지원)"""
        self._logger.info(f"💰 호가창 가격 클릭: {order_type} {price:,.0f}원")
        # TODO: Phase 4에서 실제 주문 인터페이스 연동

    def _on_orderbook_updated(self, orderbook_data: dict) -> None:
        """호가창 업데이트 처리"""
        symbol = orderbook_data.get('symbol', 'Unknown')
        ask_count = len(orderbook_data.get('asks', []))
        bid_count = len(orderbook_data.get('bids', []))
        self._logger.debug(f"호가창 업데이트: {symbol} (매도 {ask_count}, 매수 {bid_count})")

    def _on_market_impact_analyzed(self, impact_data: dict) -> None:
        """시장 임팩트 분석 결과 처리"""
        self._logger.debug(f"시장 임팩트 분석 완료: {len(impact_data)}개 볼륨")
        # TODO: Phase 4에서 리스크 관리 시스템 연동

    def _on_optimal_price_suggested(self, order_type: str, optimal_price: float) -> None:
        """최적 주문가 제안 처리"""
        self._logger.info(f"💡 최적가 제안: {order_type} {optimal_price:,.0f}원")
        # TODO: Phase 4에서 스마트 주문 시스템 연동

    def _post_init_setup(self) -> None:
        """지연 초기화 설정"""
        # 기본 비율 적용
        if self._splitter:
            self._splitter.reset_to_default_ratios()

        self._logger.debug("지연 초기화 설정 완료")

    def _on_layout_changed(self) -> None:
        """레이아웃 변경 시 처리"""
        if self._splitter:
            ratios = self._splitter.get_current_ratios()
            self._logger.debug(f"레이아웃 비율 변경: {ratios}")
            self.layout_changed.emit()

    def save_layout_state(self) -> Dict[str, Any]:
        """레이아웃 상태 저장"""
        if self._splitter:
            self._layout_state = self._splitter.save_layout_state()
            self._logger.debug("레이아웃 상태 저장됨")
            return self._layout_state
        return {}

    def restore_layout_state(self, state: Dict[str, Any]) -> None:
        """레이아웃 상태 복원"""
        if self._splitter and state:
            self._splitter.restore_layout_state(state)
            self._layout_state = state
            self._logger.debug("레이아웃 상태 복원됨")

    def reset_layout(self) -> None:
        """레이아웃을 기본값으로 재설정"""
        if self._splitter:
            self._splitter.reset_to_default_ratios()
            self._logger.info("레이아웃이 기본값(1:4:2)으로 재설정됨")

    def set_active_state(self, active: bool) -> None:
        """활성화 상태 설정 (리소스 관리용)"""
        self._is_active = active
        self._logger.debug(f"활성화 상태 변경: {active}")

    def is_active(self) -> bool:
        """현재 활성화 상태 반환"""
        return self._is_active

    def get_layout_info(self) -> Dict[str, Any]:
        """현재 레이아웃 정보 반환"""
        info = {
            'active': self._is_active,
            'panel_count': 3,
            'layout_type': '3-column-horizontal',
            'ratios': [1, 4, 2],
            'min_widths': [200, 400, 200]
        }

        if self._splitter:
            info['current_ratios'] = self._splitter.get_current_ratios()
            info['current_sizes'] = self._splitter.sizes()

        return info
