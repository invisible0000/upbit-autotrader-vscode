"""
PyQtGraph 캔들스틱 렌더러 - 간소화 버전
"""

from typing import List, Optional, Dict, Any
import numpy as np

try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    pg = None

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.chart_viewer.db_integration_layer import CandleData


class SimpleCandlestickRenderer:
    """간소화된 PyQtGraph 기반 캔들스틱 렌더러"""

    def __init__(self):
        self._logger = create_component_logger("SimpleCandlestickRenderer")
        self._candle_data: List[CandleData] = []
        self._bounding_rect = None
        self._needs_redraw = True

        # 성능 카운터
        self._render_count = 0

        if PYQTGRAPH_AVAILABLE:
            self._init_styles()

        self._logger.debug("✅ 간소화 캔들스틱 렌더러 초기화 완료")

    def _init_styles(self) -> None:
        """스타일 초기화"""
        # PyQtGraph Qt 클래스 사용
        from pyqtgraph.Qt import QtGui

        QColor = QtGui.QColor
        QPen = QtGui.QPen
        QBrush = QtGui.QBrush

        # 상승 캔들 스타일 (녹색)
        self._bull_pen = QPen(QColor(0, 150, 0), 1)
        self._bull_brush = QBrush(QColor(0, 150, 0, 100))

        # 하락 캔들 스타일 (빨간색)
        self._bear_pen = QPen(QColor(200, 0, 0), 1)
        self._bear_brush = QBrush(QColor(200, 0, 0, 100))

        # 도지 캔들 스타일 (회색)
        self._doji_pen = QPen(QColor(100, 100, 100), 1)

        # 캔들 설정
        self._candle_width = 0.8

    def set_data(self, candles: List[CandleData]) -> bool:
        """데이터 설정"""
        if not PYQTGRAPH_AVAILABLE:
            return False

        # 간단한 변경 감지
        if len(candles) != len(self._candle_data):
            self._candle_data = candles.copy()
            self._needs_redraw = True
            self._bounding_rect = None
            return True

        return False

    def get_bounding_rect(self):
        """바운딩 박스 계산"""
        if not PYQTGRAPH_AVAILABLE or not self._candle_data:
            return pg.QtCore.QRectF() if PYQTGRAPH_AVAILABLE else None

        if self._bounding_rect is not None:
            return self._bounding_rect

        from pyqtgraph.Qt import QtCore
        QRectF = QtCore.QRectF

        # 데이터 범위 계산
        high_prices = [c.high_price for c in self._candle_data]
        low_prices = [c.low_price for c in self._candle_data]

        if not high_prices:
            self._bounding_rect = QRectF()
            return self._bounding_rect

        x_min, x_max = 0, len(self._candle_data) - 1
        y_min, y_max = min(low_prices), max(high_prices)

        # 여유 공간 추가
        y_range = y_max - y_min
        y_margin = y_range * 0.1 if y_range > 0 else y_max * 0.1
        x_margin = 0.5

        self._bounding_rect = QRectF(
            x_min - x_margin,
            y_min - y_margin,
            (x_max - x_min) + 2 * x_margin,
            y_range + 2 * y_margin
        )

        return self._bounding_rect

    def render(self, painter) -> None:
        """렌더링"""
        if not PYQTGRAPH_AVAILABLE or not self._candle_data:
            return

        from pyqtgraph.Qt import QtGui, QtCore
        QPointF = QtCore.QPointF
        QRectF = QtCore.QRectF
        QBrush = QtGui.QBrush

        try:
            # 안티앨리어싱 활성화
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

            # 캔들 크기 계산
            half_width = self._candle_width / 2

            # 각 캔들 그리기
            for i, candle in enumerate(self._candle_data):
                x = float(i)

                open_price = candle.open_price
                high_price = candle.high_price
                low_price = candle.low_price
                close_price = candle.close_price

                # 상승/하락 판단
                is_bull = close_price >= open_price

                # 스타일 설정
                if is_bull:
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

                # 최소 몸체 높이 보장
                if body_height < (high_price - low_price) * 0.01:
                    body_height = (high_price - low_price) * 0.01
                    body_top = (open_price + close_price) / 2 + body_height / 2
                    body_bottom = body_top - body_height

                # 몸체 사각형 그리기
                body_rect = QRectF(
                    x - half_width,
                    body_bottom,
                    self._candle_width,
                    body_height
                )
                painter.drawRect(body_rect)

            self._render_count += 1
            self._needs_redraw = False

            if self._render_count % 10 == 0:  # 10회마다 로깅
                self._logger.debug(f"렌더링 완료: {len(self._candle_data)}개 캔들, 횟수: {self._render_count}")

        except Exception as e:
            self._logger.error(f"렌더링 실패: {e}")

    def add_candle(self, candle: CandleData) -> bool:
        """캔들 추가"""
        self._candle_data.append(candle)
        self._needs_redraw = True
        self._bounding_rect = None
        return True

    def update_last_candle(self, candle: CandleData) -> bool:
        """마지막 캔들 업데이트"""
        if self._candle_data:
            self._candle_data[-1] = candle
            self._needs_redraw = True
            self._bounding_rect = None
            return True
        return False

    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계"""
        return {
            'render_count': self._render_count,
            'candle_count': len(self._candle_data),
            'needs_redraw': self._needs_redraw
        }

    def get_performance_info(self) -> Dict[str, Any]:
        """성능 정보 (호환성을 위한 별칭)"""
        return self.get_performance_stats()

    def clear(self) -> None:
        """데이터 및 캐시 초기화"""
        self._candle_data.clear()
        self._bounding_rect = None
        self._needs_redraw = True
        self._render_count = 0
        self._logger.debug("렌더러 초기화 완료")
