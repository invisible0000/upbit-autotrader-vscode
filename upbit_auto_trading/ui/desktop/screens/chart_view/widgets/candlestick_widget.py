"""
DDD 기반 캔들스틱 차트 위젯 - Presentation Layer

DDD 아키텍처 적용:
- Domain: 차트 상태 관리 (ChartStateService)
- Application: 데이터 조작 (ChartDataApplicationService)
- Infrastructure: 렌더링 (CandlestickRenderer)
- Presentation: UI 컨트롤 및 이벤트 처리

각 계층의 책임 분리를 통한 유지보수성 향상
"""

from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter

try:
    import pyqtgraph as pg
    from PyQt6.QtCore import QRectF
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    pg = None
    QRectF = None

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.chart_viewer.db_integration_layer import CandleData
from upbit_auto_trading.domain.services.chart_state_service import ChartStateService, ChartViewState
from upbit_auto_trading.application.services.chart_data_service import ChartDataApplicationService
from upbit_auto_trading.infrastructure.chart.pyqtgraph_renderer import SimpleCandlestickRenderer


class PyQtGraphCandlestickItem(pg.GraphicsObject if PYQTGRAPH_AVAILABLE else object):
    """
    PyQtGraph GraphicsObject 어댑터

    Infrastructure 계층의 렌더러를 PyQtGraph 인터페이스에 연결
    """

    def __init__(self, renderer: SimpleCandlestickRenderer):
        if not PYQTGRAPH_AVAILABLE:
            super().__init__()
            return

        super().__init__()
        self._renderer = renderer
        self._logger = create_component_logger("PyQtGraphCandlestickItem")

    def setData(self, candles: List[CandleData]) -> None:
        """데이터 설정 - 렌더러에 위임"""
        if not PYQTGRAPH_AVAILABLE:
            return

        data_changed = self._renderer.set_data(candles)
        if data_changed:
            self.update()

    def boundingRect(self):
        """바운딩 박스 - 렌더러에서 계산"""
        if not PYQTGRAPH_AVAILABLE or pg is None:
            return None

        rect = self._renderer.get_bounding_rect()
        return rect if rect is not None else pg.QtCore.QRectF()

    def paint(self, painter: QPainter, option, widget) -> None:
        """렌더링 - 렌더러에 위임"""
        if not PYQTGRAPH_AVAILABLE:
            return

        self._renderer.render(painter)

    def addCandle(self, candle: CandleData) -> None:
        """캔들 추가"""
        if not PYQTGRAPH_AVAILABLE:
            return

        if self._renderer.add_candle(candle):
            self.update()

    def updateLastCandle(self, candle: CandleData) -> None:
        """마지막 캔들 업데이트"""
        if not PYQTGRAPH_AVAILABLE:
            return

        if self._renderer.update_last_candle(candle):
            self.update()


class CandlestickWidget(QWidget):
    """
    DDD 기반 캔들스틱 차트 위젯 - Phase 3.1 구현

    핵심 원칙:
    - Presentation Layer: UI 컨트롤과 이벤트만 처리
    - Domain/Application 서비스에 비즈니스 로직 위임
    - Infrastructure 격리: PyQtGraph 의존성 숨김

    Performance Target: 60fps 실시간 업데이트
    """

    # 시그널 정의
    candle_clicked = pyqtSignal(int, dict)
    zoom_changed = pyqtSignal(float, float)
    data_requested = pyqtSignal(str, str, int)

    def __init__(self, parent: Optional[QWidget] = None):
        """위젯 초기화"""
        super().__init__(parent)

        self._logger = create_component_logger("CandlestickChartWidget")

        # DDD 서비스 계층
        self._chart_state_service = ChartStateService()
        self._chart_data_service = ChartDataApplicationService(self._chart_state_service)

        # Infrastructure 계층
        self._renderer = SimpleCandlestickRenderer()

        # PyQtGraph 구성요소 (조건부)
        self._plot_widget: Optional[pg.PlotWidget] = None
        self._candlestick_item: Optional[PyQtGraphCandlestickItem] = None

        # UI 컨트롤
        self._timeframe_combo: Optional[QComboBox] = None
        self._auto_scroll_btn: Optional[QPushButton] = None

        # 성능 모니터링
        self._performance_timer = QTimer()
        self._performance_timer.timeout.connect(self._update_performance_display)

        # UI 초기화
        if PYQTGRAPH_AVAILABLE:
            self._setup_chart_ui()
        else:
            self._setup_fallback_ui()

        # 초기화 및 테스트 데이터
        self._initialize_chart()

        self._logger.info("✅ DDD 캔들스틱 차트 위젯 초기화 완료")

    def _setup_fallback_ui(self) -> None:
        """PyQtGraph 불가용시 대체 UI"""
        layout = QVBoxLayout(self)
        fallback_label = QLabel("⚠️ PyQtGraph 필요\npip install pyqtgraph")
        fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fallback_label.setStyleSheet("color: orange; font-size: 14pt; font-weight: bold;")
        layout.addWidget(fallback_label)

        self._logger.warning("PyQtGraph 불가용 - 대체 UI 표시")

    def _setup_chart_ui(self) -> None:
        """차트 UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 컨트롤 패널
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)

        # 차트 영역
        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setMinimumHeight(300)
        self._setup_plot_widget()
        layout.addWidget(self._plot_widget, 1)

    def _create_control_panel(self) -> QWidget:
        """컨트롤 패널 생성"""
        panel = QWidget()
        panel.setMaximumHeight(40)

        layout = QHBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # 타임프레임 선택
        layout.addWidget(QLabel("타임프레임:"))

        self._timeframe_combo = QComboBox()
        timeframes = ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"]
        self._timeframe_combo.addItems(timeframes)
        self._timeframe_combo.setCurrentText("1m")
        self._timeframe_combo.currentTextChanged.connect(self._on_timeframe_changed)
        layout.addWidget(self._timeframe_combo)

        layout.addStretch()

        # 자동 스크롤 버튼
        self._auto_scroll_btn = QPushButton("🔄 자동스크롤")
        self._auto_scroll_btn.setCheckable(True)
        self._auto_scroll_btn.setChecked(True)
        self._auto_scroll_btn.toggled.connect(self._on_auto_scroll_toggled)
        layout.addWidget(self._auto_scroll_btn)

        # 데이터 새로고침 버튼
        refresh_btn = QPushButton("↻ 새로고침")
        refresh_btn.clicked.connect(self._on_refresh_clicked)
        layout.addWidget(refresh_btn)

        # 성능 모니터 버튼
        perf_btn = QPushButton("📊 성능")
        perf_btn.setCheckable(True)
        perf_btn.toggled.connect(self._toggle_performance_monitor)
        layout.addWidget(perf_btn)

        return panel

    def _setup_plot_widget(self) -> None:
        """플롯 위젯 설정"""
        if self._plot_widget is None:
            return

        # 기본 설정
        self._plot_widget.setLabel('left', '가격', units='KRW')
        self._plot_widget.setLabel('bottom', '시간')
        self._plot_widget.setBackground('white')
        self._plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # 마우스 상호작용
        self._plot_widget.setMouseEnabled(x=True, y=True)
        self._plot_widget.enableAutoRange(axis='y')

        # 캔들스틱 아이템 생성
        self._candlestick_item = PyQtGraphCandlestickItem(self._renderer)
        self._plot_widget.addItem(self._candlestick_item)

        # 줌 변경 이벤트
        plot_item = self._plot_widget.getPlotItem()
        plot_item.vb.sigRangeChanged.connect(self._on_zoom_changed)

        self._logger.debug("플롯 위젯 설정 완료")

    def _initialize_chart(self) -> None:
        """차트 초기화"""
        # 비동기 초기화를 동기로 시뮬레이션 (테스트 데이터)
        QTimer.singleShot(100, self._load_initial_data)

    def _load_initial_data(self) -> None:
        """초기 데이터 로드"""
        try:
            # Application 서비스를 통한 초기화 (동기 버전)
            self._chart_state_service.initialize_state("KRW-BTC", "1m")

            # 테스트 데이터 생성 및 설정
            test_candles = self._chart_data_service._generate_test_data("KRW-BTC", "1m", 200)
            updated_state = self._chart_state_service.update_candle_data(test_candles)

            # UI 업데이트
            self._update_chart_display(updated_state)

            self._logger.info(f"✅ 초기 데이터 로드 완료: {len(test_candles)}개 캔들")

        except Exception as e:
            self._logger.error(f"초기 데이터 로드 실패: {e}")

    def _update_chart_display(self, state: ChartViewState) -> None:
        """차트 표시 업데이트"""
        if self._candlestick_item is None:
            return

        # 표시할 캔들 데이터 가져오기
        visible_candles = self._chart_state_service.get_visible_candles()

        # 렌더러에 데이터 설정
        self._candlestick_item.setData(visible_candles)

        # 자동 스크롤 처리
        if state.auto_scroll_enabled and self._plot_widget:
            self._auto_scroll_to_latest(state)

    def _auto_scroll_to_latest(self, state: ChartViewState) -> None:
        """최신 데이터로 자동 스크롤"""
        if self._plot_widget is None or state.candle_count == 0:
            return

        start_idx, end_idx = state.visible_range
        self._plot_widget.setXRange(start_idx, end_idx)

    def _on_timeframe_changed(self, timeframe: str) -> None:
        """타임프레임 변경 이벤트"""
        try:
            # Domain 서비스를 통한 상태 변경
            state = self._chart_state_service.change_timeframe(timeframe)

            # 새 데이터 생성 (실제로는 API 호출)
            test_candles = self._chart_data_service._generate_test_data(
                state.symbol, timeframe, 200
            )
            updated_state = self._chart_state_service.update_candle_data(test_candles)

            # UI 업데이트
            self._update_chart_display(updated_state)

            self._logger.info(f"타임프레임 변경: {timeframe}")

        except Exception as e:
            self._logger.error(f"타임프레임 변경 실패: {e}")

    def _on_auto_scroll_toggled(self, enabled: bool) -> None:
        """자동 스크롤 토글"""
        try:
            state = self._chart_state_service.toggle_auto_scroll(enabled)
            self._update_chart_display(state)

            self._logger.debug(f"자동 스크롤: {enabled}")

        except Exception as e:
            self._logger.error(f"자동 스크롤 토글 실패: {e}")

    def _on_zoom_changed(self) -> None:
        """줌 변경 이벤트"""
        if self._plot_widget is None:
            return

        try:
            plot_item = self._plot_widget.getPlotItem()
            if plot_item and hasattr(plot_item, 'vb'):
                view_box = plot_item.vb
                x_range, y_range = view_box.viewRange()

                # 시그널 발생
                self.zoom_changed.emit(
                    x_range[1] - x_range[0],
                    y_range[1] - y_range[0]
                )

        except Exception as e:
            self._logger.error(f"줌 변경 처리 실패: {e}")

    def _on_refresh_clicked(self) -> None:
        """데이터 새로고침"""
        try:
            current_state = self._chart_state_service.get_current_state()
            if not current_state:
                return

            # 새 테스트 데이터 생성
            test_candles = self._chart_data_service._generate_test_data(
                current_state.symbol,
                current_state.timeframe,
                200
            )
            updated_state = self._chart_state_service.update_candle_data(test_candles)

            # UI 업데이트
            self._update_chart_display(updated_state)

            self._logger.info("데이터 새로고침 완료")

        except Exception as e:
            self._logger.error(f"데이터 새로고침 실패: {e}")

    def _toggle_performance_monitor(self, enabled: bool) -> None:
        """성능 모니터 토글"""
        if enabled:
            self._performance_timer.start(2000)  # 2초마다
            self._logger.info("성능 모니터 시작")
        else:
            self._performance_timer.stop()
            self._logger.info("성능 모니터 중지")

    def _update_performance_display(self) -> None:
        """성능 정보 표시"""
        try:
            # Domain에서 성능 메트릭스 가져오기
            domain_metrics = self._chart_state_service.calculate_performance_metrics()

            # Infrastructure에서 렌더링 정보 가져오기
            render_info = self._renderer.get_performance_info()

            self._logger.info(
                f"📊 성능: 캔들={domain_metrics.candle_count}개, "
                f"업데이트={domain_metrics.total_updates}회, "
                f"렌더링={render_info['last_render_time_ms']:.2f}ms, "
                f"캐시={render_info['cache_active']}"
            )

        except Exception as e:
            self._logger.error(f"성능 모니터링 실패: {e}")

    # 공개 API
    def set_symbol(self, symbol: str) -> None:
        """심볼 변경"""
        try:
            state = self._chart_state_service.change_symbol(symbol)

            # 새 데이터 로드
            test_candles = self._chart_data_service._generate_test_data(
                symbol, state.timeframe, 200
            )
            updated_state = self._chart_state_service.update_candle_data(test_candles)

            self._update_chart_display(updated_state)

            self._logger.info(f"심볼 변경: {symbol}")

        except Exception as e:
            self._logger.error(f"심볼 변경 실패: {e}")

    def update_candle_data(self, candles: List[CandleData]) -> None:
        """캔들 데이터 업데이트 (외부 연동)"""
        try:
            # 상태가 초기화되지 않았다면 자동 초기화
            current_state = self._chart_state_service.get_current_state()
            if not current_state and candles:
                # 첫 번째 캔들의 정보로 초기화
                first_candle = candles[0]
                self._chart_state_service.initialize_state(
                    first_candle.symbol,
                    first_candle.timeframe
                )
                self._logger.info(f"자동 초기화: {first_candle.symbol} {first_candle.timeframe}")

            state = self._chart_state_service.update_candle_data(candles)
            self._update_chart_display(state)

        except Exception as e:
            self._logger.error(f"캔들 데이터 업데이트 실패: {e}")

    def add_realtime_candle(self, candle: CandleData) -> None:
        """실시간 캔들 추가"""
        try:
            state = self._chart_state_service.add_realtime_candle(candle)
            self._update_chart_display(state)

        except Exception as e:
            self._logger.error(f"실시간 캔들 추가 실패: {e}")

    def get_performance_info(self) -> Dict[str, Any]:
        """성능 정보 반환"""
        try:
            domain_metrics = self._chart_state_service.calculate_performance_metrics()
            render_info = self._renderer.get_performance_info()

            return {
                'domain_metrics': {
                    'candle_count': domain_metrics.candle_count,
                    'total_updates': domain_metrics.total_updates,
                    'cache_hit_rate': domain_metrics.cache_hit_rate
                },
                'render_info': render_info,
                'pyqtgraph_available': PYQTGRAPH_AVAILABLE
            }

        except Exception as e:
            self._logger.error(f"성능 정보 조회 실패: {e}")
            return {}

    def cleanup(self) -> None:
        """리소스 정리"""
        try:
            self._performance_timer.stop()
            self._renderer.clear()
            self._logger.info("차트 위젯 정리 완료")

        except Exception as e:
            self._logger.error(f"차트 위젯 정리 실패: {e}")
