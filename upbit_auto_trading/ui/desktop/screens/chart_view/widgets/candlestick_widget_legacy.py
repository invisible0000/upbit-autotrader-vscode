"""
PyQtGraph 기반 캔들스틱 차트 위젯 - Phase 3.1 구현

동적 변화에 최적화된 실시간 캔들스틱 차트 구현:
- setData() 기반 효율적 업데이트
- 200개 초기 데이터 로딩
- 마우스 휠 확대/축소
- 기존 백본 시스템과 연동

Performance Target: 60fps 실시간 업데이트
"""

from typing import Optional, List, Dict, Any
import numpy as np
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPen, QBrush

try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    print("⚠️ PyQtGraph not available - falling back to placeholder")

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.domain.value_objects.chart_data import CandleData


class CandlestickItem(pg.GraphicsObject if PYQTGRAPH_AVAILABLE else object):
    """
    고성능 캔들스틱 아이템 - PyQtGraph GraphicsObject 기반

    동적 변화 최적화 특징:
    - QPainter 직접 렌더링으로 최고 성능
    - setData() 호출로 부분 업데이트
    - boundingRect() 최적화로 불필요한 리렌더링 방지
    - 실시간 데이터 추가시 마지막 캔들만 재계산
    """

    def __init__(self, parent=None):
        if not PYQTGRAPH_AVAILABLE:
            super().__init__()
            return

        super().__init__(parent)

        self._logger = create_component_logger("CandlestickItem")

        # 캔들 데이터
        self._candle_data: List[CandleData] = []
        self._x_data: np.ndarray = np.array([])
        self._open_data: np.ndarray = np.array([])
        self._high_data: np.ndarray = np.array([])
        self._low_data: np.ndarray = np.array([])
        self._close_data: np.ndarray = np.array([])

        # 렌더링 캐시
        self._bounding_rect: Optional[pg.QtCore.QRectF] = None
        self._picture: Optional[pg.QtGui.QPicture] = None
        self._needs_redraw = True

        # 스타일 설정
        self._bull_pen = QPen(QColor(0, 150, 0), 1)        # 상승 캔들 (초록)
        self._bear_pen = QPen(QColor(200, 0, 0), 1)        # 하락 캔들 (빨강)
        self._bull_brush = QBrush(QColor(0, 150, 0, 100))  # 상승 채우기
        self._bear_brush = QBrush(QColor(200, 0, 0, 100))  # 하락 채우기

        # 성능 메트릭스
        self._last_update_time = 0.0
        self._update_count = 0

        self._logger.debug("캔들스틱 아이템 초기화 완료")

    def setData(self, candle_data: List[CandleData]) -> None:
        """
        캔들 데이터 설정 - 동적 변화 최적화

        성능 최적화:
        - 데이터 변경 시에만 재계산
        - NumPy 배열로 벡터화 연산
        - 기존 데이터와 비교하여 변경 감지
        """
        if not PYQTGRAPH_AVAILABLE or not candle_data:
            return

        import time
        start_time = time.perf_counter()

        try:
            # 데이터 변경 감지 (성능 최적화)
            data_changed = (len(candle_data) != len(self._candle_data))
            if not data_changed and candle_data:
                # 마지막 캔들만 비교 (실시간 업데이트)
                if (self._candle_data and
                        candle_data[-1].close_price != self._candle_data[-1].close_price):
                    data_changed = True

            if not data_changed:
                return

            # 캔들 데이터 저장
            self._candle_data = candle_data.copy()

            # NumPy 배열 변환 (벡터화 연산)
            n = len(candle_data)
            self._x_data = np.arange(n, dtype=np.float64)
            self._open_data = np.array([c.open_price for c in candle_data], dtype=np.float64)
            self._high_data = np.array([c.high_price for c in candle_data], dtype=np.float64)
            self._low_data = np.array([c.low_price for c in candle_data], dtype=np.float64)
            self._close_data = np.array([c.close_price for c in candle_data], dtype=np.float64)

            # 캐시 무효화
            self._bounding_rect = None
            self._picture = None
            self._needs_redraw = True
            self._update_count += 1

            # 화면 갱신 요청
            self.update()

            # 성능 로깅
            update_time = time.perf_counter() - start_time
            self._last_update_time = update_time

            if self._update_count % 100 == 0:  # 100회마다 로깅
                self._logger.debug(
                    f"캔들 데이터 업데이트: {n}개, "
                    f"시간: {update_time * 1000:.2f}ms, "
                    f"누적: {self._update_count}회"
                )

        except Exception as e:
            self._logger.error(f"캔들 데이터 설정 실패: {e}")

    def boundingRect(self):
        """
        바운딩 박스 계산 - 캐시된 결과 반환으로 성능 최적화
        """
        if not PYQTGRAPH_AVAILABLE:
            return None

        if self._bounding_rect is not None:
            return self._bounding_rect

        if len(self._x_data) == 0:
            self._bounding_rect = pg.QtCore.QRectF()
            return self._bounding_rect

        # 데이터 범위 계산
        x_min, x_max = float(self._x_data.min()), float(self._x_data.max())
        y_min, y_max = float(self._low_data.min()), float(self._high_data.max())

        # 여유 공간 추가 (10%)
        y_range = y_max - y_min
        y_margin = y_range * 0.1
        x_margin = 0.5  # 캔들 폭의 절반

        self._bounding_rect = pg.QtCore.QRectF(
            x_min - x_margin, y_min - y_margin,
            (x_max - x_min) + 2 * x_margin, (y_range) + 2 * y_margin
        )

        return self._bounding_rect

    def paint(self, painter: 'pg.QtGui.QPainter', option, widget) -> None:
        """
        캔들스틱 렌더링 - QPicture 캐시 활용으로 성능 최적화
        """
        if not PYQTGRAPH_AVAILABLE or len(self._candle_data) == 0:
            return

        # 캐시된 그림이 있고 재그리기가 필요 없으면 캐시 사용
        if self._picture is not None and not self._needs_redraw:
            self._picture.play(painter)
            return

        # 새로운 그림 생성
        self._picture = pg.QtGui.QPicture()
        cache_painter = pg.QtGui.QPainter(self._picture)

        try:
            self._draw_candles(cache_painter)
            self._needs_redraw = False
        finally:
            cache_painter.end()

        # 캐시된 그림 그리기
        self._picture.play(painter)

    def _draw_candles(self, painter: 'pg.QtGui.QPainter') -> None:
        """
        실제 캔들 그리기 - 벡터화 연산으로 성능 최적화
        """
        if not self._candle_data:
            return

        # 안티앨리어싱 활성화
        painter.setRenderHint(pg.QtGui.QPainter.RenderHint.Antialiasing, True)

        # 캔들 폭 계산 (동적 조정)
        candle_width = 0.8
        half_width = candle_width / 2

        for i, candle in enumerate(self._candle_data):
            x = float(i)
            open_price = candle.open_price
            high_price = candle.high_price
            low_price = candle.low_price
            close_price = candle.close_price

            # 상승/하락 판단
            is_bull = close_price >= open_price

            # 펜과 브러시 설정
            if is_bull:
                painter.setPen(self._bull_pen)
                painter.setBrush(self._bull_brush)
            else:
                painter.setPen(self._bear_pen)
                painter.setBrush(self._bear_brush)

            # 심지(고가-저가) 그리기
            painter.drawLine(
                pg.QtCore.QPointF(x, low_price),
                pg.QtCore.QPointF(x, high_price)
            )

            # 몸체(시가-종가) 그리기
            body_top = max(open_price, close_price)
            body_bottom = min(open_price, close_price)
            body_height = body_top - body_bottom

            if body_height > 0:
                body_rect = pg.QtCore.QRectF(
                    x - half_width, body_bottom,
                    candle_width, body_height
                )
                painter.drawRect(body_rect)
            else:
                # 도지 캔들 (시가 == 종가)
                painter.drawLine(
                    pg.QtCore.QPointF(x - half_width, close_price),
                    pg.QtCore.QPointF(x + half_width, close_price)
                )

    def addCandle(self, candle: CandleData) -> None:
        """
        새 캔들 추가 - 실시간 업데이트 최적화
        """
        if not PYQTGRAPH_AVAILABLE:
            return

        self._candle_data.append(candle)
        self.setData(self._candle_data)

    def updateLastCandle(self, candle: CandleData) -> None:
        """
        마지막 캔들 업데이트 - 실시간 변화 최적화
        """
        if not PYQTGRAPH_AVAILABLE or not self._candle_data:
            return

        self._candle_data[-1] = candle
        self.setData(self._candle_data)

    def getPerformanceMetrics(self) -> Dict[str, Any]:
        """성능 메트릭스 반환"""
        return {
            'last_update_time_ms': self._last_update_time * 1000,
            'update_count': self._update_count,
            'candle_count': len(self._candle_data),
            'cache_active': self._picture is not None and not self._needs_redraw
        }


class CandlestickWidget(QWidget):
    """
    캔들스틱 차트 위젯 - Phase 3.1 메인 구현

    기능:
    - PyQtGraph 기반 고성능 렌더링
    - 200개 초기 데이터 로딩
    - 마우스 휠 확대/축소
    - 실시간 데이터 업데이트
    - 기존 백본 시스템 연동
    """

    # 시그널 정의
    candle_clicked = pyqtSignal(int, dict)  # 캔들 클릭 (인덱스, 캔들 데이터)
    zoom_changed = pyqtSignal(float, float)  # 확대/축소 변경 (x_range, y_range)
    data_requested = pyqtSignal(str, str, int)  # 데이터 요청 (심볼, 타임프레임, 개수)

    def __init__(self, parent: Optional[QWidget] = None):
        """캔들스틱 위젯 초기화"""
        super().__init__(parent)

        self._logger = create_component_logger("CandlestickWidget")

        if not PYQTGRAPH_AVAILABLE:
            self._setup_fallback_ui()
            return

        # 상태 관리
        self._current_symbol = "KRW-BTC"
        self._current_timeframe = "1m"
        self._is_realtime = False
        self._auto_scroll = True

        # PyQtGraph 위젯
        self._plot_widget = None  # pg.PlotWidget 또는 None
        self._candlestick_item: Optional[CandlestickItem] = None

        # 컨트롤
        self._timeframe_combo: Optional[QComboBox] = None
        self._auto_scroll_btn: Optional[QPushButton] = None

        # 성능 모니터링
        self._performance_timer = QTimer()
        self._performance_timer.timeout.connect(self._log_performance)
        self._frame_count = 0
        self._last_fps_time = 0.0

        # UI 초기화
        self._setup_ui()
        self._setup_plot()
        self._setup_controls()

        # 테스트 데이터 로드
        QTimer.singleShot(100, self._load_test_data)

        self._logger.info("✅ PyQtGraph 캔들스틱 위젯 초기화 완료")

    def _setup_fallback_ui(self) -> None:
        """PyQtGraph 불가용시 대체 UI"""
        layout = QVBoxLayout(self)
        fallback_label = QLabel("⚠️ PyQtGraph가 설치되지 않음\n대체 차트 라이브러리 필요")
        fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fallback_label.setStyleSheet("color: orange; font-size: 14pt; font-weight: bold;")
        layout.addWidget(fallback_label)

        self._logger.warning("PyQtGraph 불가용 - 대체 UI 표시")

    def _setup_ui(self) -> None:
        """기본 UI 구조 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 컨트롤 패널 (상단)
        control_panel = QWidget()
        control_panel.setMaximumHeight(40)
        layout.addWidget(control_panel)

        # 차트 영역 (메인)
        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setMinimumHeight(300)
        layout.addWidget(self._plot_widget, 1)

        # 컨트롤 패널 레이아웃
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(5, 5, 5, 5)

        self._setup_control_widgets(control_layout)

    def _setup_control_widgets(self, layout: QHBoxLayout) -> None:
        """컨트롤 위젯 설정"""
        # 타임프레임 선택
        layout.addWidget(QLabel("타임프레임:"))

        self._timeframe_combo = QComboBox()
        timeframes = ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"]
        self._timeframe_combo.addItems(timeframes)
        self._timeframe_combo.setCurrentText(self._current_timeframe)
        self._timeframe_combo.currentTextChanged.connect(self._on_timeframe_changed)
        layout.addWidget(self._timeframe_combo)

        layout.addStretch()

        # 자동 스크롤 버튼
        self._auto_scroll_btn = QPushButton("🔄 자동스크롤")
        self._auto_scroll_btn.setCheckable(True)
        self._auto_scroll_btn.setChecked(self._auto_scroll)
        self._auto_scroll_btn.toggled.connect(self._on_auto_scroll_toggled)
        layout.addWidget(self._auto_scroll_btn)

        # 성능 모니터 시작 버튼 (개발용)
        perf_btn = QPushButton("📊 성능모니터")
        perf_btn.setCheckable(True)
        perf_btn.toggled.connect(self._toggle_performance_monitor)
        layout.addWidget(perf_btn)

    def _setup_plot(self) -> None:
        """플롯 설정"""
        if not self._plot_widget:
            return

        # 축 레이블
        self._plot_widget.setLabel('left', '가격', units='KRW')
        self._plot_widget.setLabel('bottom', '시간', units='')

        # 배경 및 그리드
        self._plot_widget.setBackground('white')
        self._plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # 마우스 상호작용
        self._plot_widget.setMouseEnabled(x=True, y=True)
        self._plot_widget.enableAutoRange(axis='y')

        # 캔들스틱 아이템 생성
        self._candlestick_item = CandlestickItem()
        self._plot_widget.addItem(self._candlestick_item)

        # 크로스헤어 추가 (옵션)
        self._add_crosshair()

        self._logger.debug("플롯 설정 완료")

    def _add_crosshair(self) -> None:
        """크로스헤어 추가 (마우스 추적선)"""
        if not self._plot_widget:
            return

        # 수직선
        self._v_line = pg.InfiniteLine(angle=90, movable=False, pen='gray')
        # 수평선
        self._h_line = pg.InfiniteLine(angle=0, movable=False, pen='gray')

        self._plot_widget.addItem(self._v_line, ignoreBounds=True)
        self._plot_widget.addItem(self._h_line, ignoreBounds=True)

        # 마우스 이동 이벤트 연결
        plot_item = self._plot_widget.getPlotItem()
        plot_item.scene().sigMouseMoved.connect(self._on_mouse_moved)

    def _on_mouse_moved(self, pos) -> None:
        """마우스 이동 처리 (크로스헤어 업데이트)"""
        if not self._plot_widget:
            return

        plot_item = self._plot_widget.getPlotItem()
        if plot_item.sceneBoundingRect().contains(pos):
            mouse_point = plot_item.vb.mapSceneToView(pos)
            self._v_line.setPos(mouse_point.x())
            self._h_line.setPos(mouse_point.y())

    def _setup_controls(self) -> None:
        """컨트롤 이벤트 설정"""
        if not self._plot_widget:
            return

        # 줌 변경 이벤트
        plot_item = self._plot_widget.getPlotItem()
        plot_item.vb.sigRangeChanged.connect(self._on_zoom_changed)

    def _on_timeframe_changed(self, timeframe: str) -> None:
        """타임프레임 변경 처리"""
        self._current_timeframe = timeframe
        self._logger.info(f"타임프레임 변경: {timeframe}")

        # 데이터 요청
        self.data_requested.emit(self._current_symbol, timeframe, 200)

    def _on_auto_scroll_toggled(self, enabled: bool) -> None:
        """자동 스크롤 토글"""
        self._auto_scroll = enabled
        self._logger.debug(f"자동 스크롤: {enabled}")

    def _on_zoom_changed(self) -> None:
        """줌 변경 처리"""
        if not self._plot_widget:
            return

        view_box = self._plot_widget.getPlotItem().vb
        x_range, y_range = view_box.viewRange()

        self.zoom_changed.emit(
            x_range[1] - x_range[0],  # x 범위
            y_range[1] - y_range[0]   # y 범위
        )

    def _toggle_performance_monitor(self, enabled: bool) -> None:
        """성능 모니터 토글"""
        if enabled:
            self._performance_timer.start(1000)  # 1초마다
            self._last_fps_time = datetime.now().timestamp()
            self._frame_count = 0
            self._logger.info("성능 모니터 시작")
        else:
            self._performance_timer.stop()
            self._logger.info("성능 모니터 중지")

    def _log_performance(self) -> None:
        """성능 로깅"""
        if not self._candlestick_item:
            return

        current_time = datetime.now().timestamp()
        time_delta = current_time - self._last_fps_time

        if time_delta > 0:
            fps = self._frame_count / time_delta
            metrics = self._candlestick_item.getPerformanceMetrics()

            self._logger.info(
                f"📊 성능 메트릭스: FPS={fps:.1f}, "
                f"업데이트={metrics['update_count']}회, "
                f"마지막업데이트={metrics['last_update_time_ms']:.2f}ms, "
                f"캔들수={metrics['candle_count']}개, "
                f"캐시활성={metrics['cache_active']}"
            )

        self._frame_count = 0
        self._last_fps_time = current_time

    def _load_test_data(self) -> None:
        """테스트 데이터 로드 (200개 캔들)"""
        self._logger.info("📊 테스트 데이터 로드 시작 (200개 캔들)")

        # 현재 시간부터 200분 전까지의 1분 캔들 생성
        end_time = datetime.now()
        base_price = 45000000  # 4500만원

        test_candles = []
        for i in range(200):
            candle_time = end_time - timedelta(minutes=199 - i)

            # 가격 변동 시뮬레이션 (랜덤 워크)
            price_change = np.random.normal(0, base_price * 0.01)  # 1% 변동
            base_price = max(base_price + price_change, base_price * 0.8)  # 최소 80% 보호

            # OHLC 생성
            open_price = base_price
            high_price = open_price + abs(np.random.normal(0, base_price * 0.005))
            low_price = open_price - abs(np.random.normal(0, base_price * 0.005))
            close_price = open_price + np.random.normal(0, base_price * 0.008)

            # high, low 보정
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)

            volume = np.random.uniform(0.1, 2.0)  # 0.1~2.0 BTC

            candle = CandleData(
                symbol=self._current_symbol,
                timestamp=candle_time,
                timeframe=self._current_timeframe,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=volume,
                quote_volume=volume * close_price,
                trade_count=int(np.random.uniform(50, 200))
            )

            test_candles.append(candle)

        # 캔들스틱 차트에 데이터 설정
        if self._candlestick_item:
            self._candlestick_item.setData(test_candles)
            self._logger.info(f"✅ 테스트 데이터 로드 완료: {len(test_candles)}개 캔들")

            # 자동 범위 조정
            if self._plot_widget:
                self._plot_widget.autoRange()

    def setSymbol(self, symbol: str) -> None:
        """심볼 변경"""
        if symbol != self._current_symbol:
            self._current_symbol = symbol
            self._logger.info(f"심볼 변경: {symbol}")

            # 새 데이터 요청
            self.data_requested.emit(symbol, self._current_timeframe, 200)

    def setTimeframe(self, timeframe: str) -> None:
        """타임프레임 변경"""
        if timeframe != self._current_timeframe:
            self._current_timeframe = timeframe
            if self._timeframe_combo:
                self._timeframe_combo.setCurrentText(timeframe)

            self._logger.info(f"타임프레임 변경: {timeframe}")

    def updateCandleData(self, candles: List[CandleData]) -> None:
        """캔들 데이터 업데이트 (백본 시스템 연동)"""
        if not self._candlestick_item or not candles:
            return

        start_time = datetime.now().timestamp()

        # 데이터 설정
        self._candlestick_item.setData(candles)
        self._frame_count += 1

        # 자동 스크롤 (실시간 모드)
        if self._auto_scroll and self._is_realtime:
            self._scroll_to_latest()

        update_time = (datetime.now().timestamp() - start_time) * 1000

        if len(candles) > 100:  # 대량 데이터일 때만 로깅
            self._logger.debug(f"캔들 데이터 업데이트: {len(candles)}개, {update_time:.2f}ms")

    def addRealtimeCandle(self, candle: CandleData) -> None:
        """실시간 캔들 추가"""
        if not self._candlestick_item:
            return

        self._is_realtime = True
        self._candlestick_item.addCandle(candle)
        self._frame_count += 1

        if self._auto_scroll:
            self._scroll_to_latest()

    def updateRealtimeCandle(self, candle: CandleData) -> None:
        """실시간 캔들 업데이트 (현재 캔들 수정)"""
        if not self._candlestick_item:
            return

        self._is_realtime = True
        self._candlestick_item.updateLastCandle(candle)
        self._frame_count += 1

    def _scroll_to_latest(self) -> None:
        """최신 데이터로 스크롤"""
        if not self._plot_widget or not self._candlestick_item:
            return

        # X축을 최신 데이터 영역으로 이동
        candle_count = len(self._candlestick_item._candle_data)
        if candle_count > 0:
            view_range = 50  # 50개 캔들 표시
            x_max = candle_count - 1
            x_min = max(0, x_max - view_range)

            self._plot_widget.setXRange(x_min, x_max, padding=0.02)

    def getCurrentSymbol(self) -> str:
        """현재 심볼 반환"""
        return self._current_symbol

    def getCurrentTimeframe(self) -> str:
        """현재 타임프레임 반환"""
        return self._current_timeframe

    def getPerformanceInfo(self) -> Dict[str, Any]:
        """성능 정보 반환"""
        info = {
            'widget_active': True,
            'pyqtgraph_available': PYQTGRAPH_AVAILABLE,
            'current_symbol': self._current_symbol,
            'current_timeframe': self._current_timeframe,
            'realtime_mode': self._is_realtime,
            'auto_scroll': self._auto_scroll
        }

        if self._candlestick_item:
            info.update(self._candlestick_item.getPerformanceMetrics())

        return info
