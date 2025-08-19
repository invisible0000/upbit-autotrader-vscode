"""
PyQtGraph 캔들스틱 렌더러 - Infrastructure Layer

DDD Infrastructure 계층:
- PyQtGraph 의존성 격리
- 캔들스틱 렌더링 구현
- 성능 최적화 (QPicture 캐싱)
- 그래픽 스타일 관리

Domain 계층과 독립적인 렌더링 구현
"""

from typing import List, Optional, Dict, Any
import numpy as np

try:
    import pyqtgraph as pg
    from pyqtgraph.Qt import QtGui, QtCore
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    pg = None
    QtGui = QtCore = None

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.chart_viewer.db_integration_layer import CandleData


class CandlestickRenderer:
    """
    PyQtGraph 기반 캔들스틱 렌더러

    핵심 책임:
    - PyQtGraph GraphicsObject 구현
    - 고성능 캔들스틱 렌더링
    - QPicture 캐싱 최적화
    - 스타일 및 색상 관리
    """

    def __init__(self):
        self._logger = create_component_logger("CandlestickRenderer")

        if not PYQTGRAPH_AVAILABLE:
            self._logger.warning("PyQtGraph 불가용 - 렌더링 비활성화")
            return

        # 렌더링 데이터
        self._candle_data: List[CandleData] = []
        self._numpy_data: Optional[Dict[str, np.ndarray]] = None

        # 캐싱
        self._bounding_rect: Optional[QRectF] = None
        self._picture_cache: Optional['pg.QtGui.QPicture'] = None
        self._needs_redraw = True

        # 스타일 설정
        self._setup_styles()

        # 성능 메트릭스
        self._render_count = 0
        self._last_render_time = 0.0

        self._logger.debug("캔들스틱 렌더러 초기화 완료")

    def _setup_styles(self) -> None:
        """스타일 설정"""
        if not PYQTGRAPH_AVAILABLE:
            return

        # 상승 캔들 (초록색)
        self._bull_pen = QPen(QColor(0, 150, 0), 1)
        self._bull_brush = QBrush(QColor(0, 150, 0, 100))

        # 하락 캔들 (빨간색)
        self._bear_pen = QPen(QColor(200, 0, 0), 1)
        self._bear_brush = QBrush(QColor(200, 0, 0, 100))

        # 도지 캔들 (회색)
        self._doji_pen = QPen(QColor(100, 100, 100), 1)

        # 캔들 스타일 설정
        self._candle_width = 0.8
        self._wick_width = 1

    def set_data(self, candles: List[CandleData]) -> bool:
        """
        캔들 데이터 설정

        Args:
            candles: 캔들 데이터 리스트

        Returns:
            데이터 변경 여부
        """
        if not PYQTGRAPH_AVAILABLE:
            return False

        import time
        start_time = time.perf_counter()

        try:
            # 데이터 변경 감지
            data_changed = self._detect_data_changes(candles)
            if not data_changed:
                return False

            # 데이터 저장
            self._candle_data = candles.copy()

            # NumPy 배열 변환 (성능 최적화)
            self._prepare_numpy_data()

            # 캐시 무효화
            self._invalidate_cache()

            # 성능 기록
            render_time = time.perf_counter() - start_time
            self._last_render_time = render_time * 1000  # ms 단위
            self._render_count += 1

            if self._render_count % 50 == 0:  # 50회마다 로깅
                self._logger.debug(
                    f"데이터 설정: {len(candles)}개, "
                    f"{self._last_render_time:.2f}ms, "
                    f"누적: {self._render_count}회"
                )

            return True

        except Exception as e:
            self._logger.error(f"데이터 설정 실패: {e}")
            return False

    def _detect_data_changes(self, new_candles: List[CandleData]) -> bool:
        """데이터 변경 감지"""
        if len(new_candles) != len(self._candle_data):
            return True

        if not new_candles or not self._candle_data:
            return len(new_candles) != len(self._candle_data)

        # 마지막 캔들 비교 (실시간 업데이트 최적화)
        last_new = new_candles[-1]
        last_old = self._candle_data[-1]

        return (
            last_new.close_price != last_old.close_price
            or last_new.high_price != last_old.high_price
            or last_new.low_price != last_old.low_price
            or last_new.volume != last_old.volume
        )

    def _prepare_numpy_data(self) -> None:
        """NumPy 배열 준비 (벡터화 연산)"""
        if not self._candle_data:
            self._numpy_data = None
            return

        n = len(self._candle_data)
        self._numpy_data = {
            'x': np.arange(n, dtype=np.float64),
            'open': np.array([c.open_price for c in self._candle_data], dtype=np.float64),
            'high': np.array([c.high_price for c in self._candle_data], dtype=np.float64),
            'low': np.array([c.low_price for c in self._candle_data], dtype=np.float64),
            'close': np.array([c.close_price for c in self._candle_data], dtype=np.float64),
        }

    def _invalidate_cache(self) -> None:
        """캐시 무효화"""
        self._bounding_rect = None
        self._picture_cache = None
        self._needs_redraw = True

    def get_bounding_rect(self) -> Optional['QRectF']:
        """바운딩 박스 계산 (캐시됨)"""
        if not PYQTGRAPH_AVAILABLE or not self._numpy_data:
            return None

        if self._bounding_rect is not None:
            return self._bounding_rect

        # 데이터 범위 계산
        x_data = self._numpy_data['x']
        high_data = self._numpy_data['high']
        low_data = self._numpy_data['low']

        if len(x_data) == 0:
            self._bounding_rect = QRectF()
            return self._bounding_rect

        x_min, x_max = float(x_data.min()), float(x_data.max())
        y_min, y_max = float(low_data.min()), float(high_data.max())

        # 여유 공간 추가
        y_range = y_max - y_min
        y_margin = y_range * 0.1 if y_range > 0 else y_max * 0.1
        x_margin = self._candle_width / 2

        self._bounding_rect = QRectF(
            x_min - x_margin,
            y_min - y_margin,
            (x_max - x_min) + 2 * x_margin,
            (y_range) + 2 * y_margin
        )

        return self._bounding_rect

    def render(self, painter: 'QPainter') -> None:
        """
        캔들스틱 렌더링

        Args:
            painter: QPainter 객체
        """
        if not PYQTGRAPH_AVAILABLE or not self._candle_data:
            return

        # 캐시된 그림이 있고 재그리기가 필요 없으면 캐시 사용
        if self._picture_cache is not None and not self._needs_redraw:
            self._picture_cache.play(painter)
            return

        # 새로운 그림 생성
        self._picture_cache = pg.QtGui.QPicture()
        cache_painter = pg.QtGui.QPainter(self._picture_cache)

        try:
            self._draw_candles(cache_painter)
            self._needs_redraw = False
        finally:
            cache_painter.end()

        # 캐시된 그림 그리기
        if self._picture_cache:
            self._picture_cache.play(painter)

    def _draw_candles(self, painter: 'QPainter') -> None:
        """실제 캔들 그리기"""
        if not self._candle_data or not self._numpy_data:
            return

        # 안티앨리어싱 활성화
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 캔들 크기 계산
        half_width = self._candle_width / 2

        # 각 캔들 그리기
        for i, candle in enumerate(self._candle_data):
            x = float(i)
            self._draw_single_candle(painter, x, candle, half_width)

    def _draw_single_candle(
        self,
        painter: 'QPainter',
        x: float,
        candle: CandleData,
        half_width: float
    ) -> None:
        """단일 캔들 그리기"""
        open_price = candle.open_price
        high_price = candle.high_price
        low_price = candle.low_price
        close_price = candle.close_price

        # 상승/하락 판단
        is_bull = close_price >= open_price
        is_doji = abs(close_price - open_price) < (high_price - low_price) * 0.01

        # 스타일 설정
        if is_doji:
            painter.setPen(self._doji_pen)
            painter.setBrush(QBrush())  # 투명
        elif is_bull:
            painter.setPen(self._bull_pen)
            painter.setBrush(self._bull_brush)
        else:
            painter.setPen(self._bear_pen)
            painter.setBrush(self._bear_brush)

        # 심지(고가-저가) 그리기
        painter.drawLine(
            QPointF(x, low_price),
            QPointF(x, high_price)
        )

        # 몸체(시가-종가) 그리기
        body_top = max(open_price, close_price)
        body_bottom = min(open_price, close_price)
        body_height = body_top - body_bottom

        if body_height > 0 and not is_doji:
            body_rect = QRectF(
                x - half_width, body_bottom,
                self._candle_width, body_height
            )
            painter.drawRect(body_rect)
        else:
            # 도지 캔들 (시가 == 종가)
            painter.drawLine(
                QPointF(x - half_width, close_price),
                QPointF(x + half_width, close_price)
            )

    def add_candle(self, candle: CandleData) -> bool:
        """캔들 추가"""
        if not PYQTGRAPH_AVAILABLE:
            return False

        self._candle_data.append(candle)
        return self.set_data(self._candle_data)

    def update_last_candle(self, candle: CandleData) -> bool:
        """마지막 캔들 업데이트"""
        if not PYQTGRAPH_AVAILABLE or not self._candle_data:
            return False

        self._candle_data[-1] = candle
        return self.set_data(self._candle_data)

    def get_candle_count(self) -> int:
        """캔들 개수 반환"""
        return len(self._candle_data)

    def get_performance_info(self) -> Dict[str, Any]:
        """성능 정보 반환"""
        return {
            'renderer_active': PYQTGRAPH_AVAILABLE,
            'candle_count': len(self._candle_data),
            'render_count': self._render_count,
            'last_render_time_ms': self._last_render_time,
            'cache_active': (
                self._picture_cache is not None and not self._needs_redraw
            ),
            'needs_redraw': self._needs_redraw
        }

    def set_style(
        self,
        bull_color: str = "#009600",
        bear_color: str = "#c80000",
        doji_color: str = "#646464",
        candle_width: float = 0.8
    ) -> None:
        """스타일 설정"""
        if not PYQTGRAPH_AVAILABLE:
            return

        # 색상 파싱 및 설정
        bull_qcolor = QColor(bull_color)
        bear_qcolor = QColor(bear_color)
        doji_qcolor = QColor(doji_color)

        self._bull_pen = QPen(bull_qcolor, 1)
        self._bull_brush = QBrush(QColor(bull_qcolor.red(), bull_qcolor.green(), bull_qcolor.blue(), 100))

        self._bear_pen = QPen(bear_qcolor, 1)
        self._bear_brush = QBrush(QColor(bear_qcolor.red(), bear_qcolor.green(), bear_qcolor.blue(), 100))

        self._doji_pen = QPen(doji_qcolor, 1)

        self._candle_width = candle_width

        # 스타일 변경 시 재그리기 필요
        self._invalidate_cache()

        self._logger.debug(f"스타일 업데이트: bull={bull_color}, bear={bear_color}, width={candle_width}")

    def clear(self) -> None:
        """렌더러 정리"""
        self._candle_data.clear()
        self._numpy_data = None
        self._invalidate_cache()
        self._logger.debug("렌더러 정리 완료")
