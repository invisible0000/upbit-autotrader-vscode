"""
Finplot 기반 캔들스틱 차트 - DDD 아키텍처
Infrastructure Layer: Finplot 렌더러

핵심 특징:
- 금융 차트 전문 라이브러리
- 실시간 업데이트 최적화
- PyQt6 완벽 통합
"""

from typing import List, Optional, Dict, Any
import pandas as pd

try:
    import finplot as fplt
    FINPLOT_AVAILABLE = True
except ImportError:
    FINPLOT_AVAILABLE = False
    fplt = None

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.chart_viewer.db_integration_layer import CandleData


class FinplotCandlestickRenderer:
    """Finplot 기반 전문 캔들스틱 렌더러"""

    def __init__(self):
        self._logger = create_component_logger("FinplotCandlestickRenderer")
        self._candle_data: List[CandleData] = []
        self._df: Optional[pd.DataFrame] = None

        # Finplot 플롯 객체들
        self._ax = None
        self._candle_plot = None

        # 성능 카운터
        self._update_count = 0
        self._last_data_size = 0

        if FINPLOT_AVAILABLE:
            self._init_colors()

        self._logger.debug("✅ Finplot 캔들스틱 렌더러 초기화 완료")

    def _init_colors(self) -> None:
        """Finplot 색상 설정"""
        # 업비트 스타일 색상 (한국 거래소 스타일)
        self._colors = {
            'bull_shadow': '#d60000',    # 빨간색 (한국: 상승=빨강)
            'bull_frame': '#d60000',
            'bull_body': '#d60000',
            'bear_shadow': '#005fcc',    # 파란색 (한국: 하락=파랑)
            'bear_frame': '#005fcc',
            'bear_body': '#005fcc'
        }

    def create_plot(self, title: str = "캔들스틱 차트", init_zoom_periods: int = 200) -> Any:
        """Finplot 차트 생성"""
        if not FINPLOT_AVAILABLE:
            self._logger.error("Finplot 라이브러리가 설치되지 않음")
            return None

        try:
            # Finplot 차트 생성
            self._ax = fplt.create_plot(
                title=title,
                init_zoom_periods=init_zoom_periods,
                maximize=False
            )

            self._logger.info(f"✅ Finplot 차트 생성 완료: {title}")
            return self._ax

        except Exception as e:
            self._logger.error(f"Finplot 차트 생성 실패: {e}")
            return None

    def set_data(self, candles: List[CandleData]) -> bool:
        """캔들 데이터 설정"""
        if not FINPLOT_AVAILABLE or not candles:
            return False

        try:
            # CandleData를 pandas DataFrame으로 변환
            data_rows = []
            for candle in candles:
                data_rows.append({
                    'time': candle.timestamp,
                    'open': float(candle.open_price),
                    'close': float(candle.close_price),
                    'high': float(candle.high_price),
                    'low': float(candle.low_price),
                    'volume': float(candle.volume or 0)
                })

            self._df = pd.DataFrame(data_rows)

            # 시간 인덱스 설정
            self._df['time'] = pd.to_datetime(self._df['time'])
            self._df.set_index('time', inplace=True)

            # 데이터 변경 감지
            data_changed = len(candles) != self._last_data_size
            self._last_data_size = len(candles)
            self._candle_data = candles.copy()

            self._logger.debug(f"📊 데이터 설정 완료: {len(candles)}개 캔들")
            return data_changed

        except Exception as e:
            self._logger.error(f"데이터 설정 실패: {e}")
            return False

    def render_candlesticks(self, gfx_update: bool = True) -> bool:
        """캔들스틱 렌더링"""
        if not FINPLOT_AVAILABLE or self._df is None or self._ax is None:
            return False

        try:
            # 기존 플롯이 있으면 업데이트, 없으면 새로 생성
            if self._candle_plot is None:
                # 새 캔들스틱 플롯 생성
                self._candle_plot = fplt.candlestick_ochl(
                    self._df[['open', 'close', 'high', 'low']],
                    ax=self._ax
                )

                # 한국 스타일 색상 적용
                self._candle_plot.colors.update(self._colors)

                self._logger.info("🕯️ 새 캔들스틱 플롯 생성")
            else:
                # 기존 플롯 데이터 업데이트
                self._candle_plot.update_data(
                    self._df[['open', 'close', 'high', 'low']],
                    gfx=gfx_update
                )

            if gfx_update:
                self._candle_plot.update_gfx()

            self._update_count += 1

            if self._update_count % 10 == 0:  # 10회마다 로깅
                self._logger.debug(f"🎨 렌더링 완료: {len(self._candle_data)}개 캔들, 횟수: {self._update_count}")

            return True

        except Exception as e:
            self._logger.error(f"캔들스틱 렌더링 실패: {e}")
            return False

    def add_candle(self, candle: CandleData) -> bool:
        """새 캔들 추가"""
        if not FINPLOT_AVAILABLE:
            return False

        try:
            self._candle_data.append(candle)

            # DataFrame에 새 행 추가
            new_row = pd.DataFrame([{
                'time': candle.timestamp,
                'open': float(candle.open_price),
                'close': float(candle.close_price),
                'high': float(candle.high_price),
                'low': float(candle.low_price),
                'volume': float(candle.volume or 0)
            }])
            new_row['time'] = pd.to_datetime(new_row['time'])
            new_row.set_index('time', inplace=True)

            if self._df is not None:
                self._df = pd.concat([self._df, new_row])
            else:
                self._df = new_row

            return True

        except Exception as e:
            self._logger.error(f"캔들 추가 실패: {e}")
            return False

    def update_last_candle(self, candle: CandleData) -> bool:
        """마지막 캔들 업데이트"""
        if not FINPLOT_AVAILABLE or not self._candle_data:
            return False

        try:
            # 메모리 데이터 업데이트
            self._candle_data[-1] = candle

            # DataFrame 마지막 행 업데이트
            if self._df is not None and len(self._df) > 0:
                last_time = pd.to_datetime(candle.timestamp)
                self._df.loc[self._df.index[-1]] = {
                    'open': float(candle.open_price),
                    'close': float(candle.close_price),
                    'high': float(candle.high_price),
                    'low': float(candle.low_price),
                    'volume': float(candle.volume or 0)
                }

            return True

        except Exception as e:
            self._logger.error(f"마지막 캔들 업데이트 실패: {e}")
            return False

    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계"""
        return {
            'update_count': self._update_count,
            'candle_count': len(self._candle_data),
            'dataframe_size': len(self._df) if self._df is not None else 0,
            'finplot_available': FINPLOT_AVAILABLE
        }

    def clear(self) -> None:
        """데이터 및 상태 초기화"""
        self._candle_data.clear()
        self._df = None
        self._candle_plot = None
        self._update_count = 0
        self._last_data_size = 0

        if self._ax is not None:
            try:
                self._ax.reset()  # Finplot 축 리셋
            except:
                pass

        self._logger.debug("렌더러 초기화 완료")

    def get_plot_widget(self):
        """PyQt6 위젯 반환 (임베딩용)"""
        if not FINPLOT_AVAILABLE or self._ax is None:
            return None

        try:
            # Finplot의 내부 PyQt 위젯 반환
            return self._ax.vb.win
        except Exception as e:
            self._logger.error(f"위젯 반환 실패: {e}")
            return None

    def show(self, qt_exec: bool = True) -> None:
        """차트 표시"""
        if FINPLOT_AVAILABLE:
            fplt.show(qt_exec=qt_exec)
