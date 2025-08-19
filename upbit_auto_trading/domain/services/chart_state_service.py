"""
차트 상태 관리 서비스 - Domain Layer

DDD 순수 도메인 로직:
- 차트 표시 상태 관리
- 줌/스크롤 상태 계산
- 캔들 데이터 변경 감지
- 성능 메트릭스 계산

외부 의존성 없는 순수 비즈니스 로직
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from upbit_auto_trading.infrastructure.chart_viewer.db_integration_layer import CandleData


@dataclass(frozen=True)
class ChartViewState:
    """차트 뷰 상태 값 객체"""
    symbol: str
    timeframe: str
    candle_count: int
    visible_range: Tuple[int, int]  # (start_index, end_index)
    zoom_level: float
    auto_scroll_enabled: bool
    is_realtime: bool
    last_update_time: datetime


@dataclass(frozen=True)
class ChartPerformanceMetrics:
    """차트 성능 메트릭스 값 객체"""
    fps: float
    last_update_time_ms: float
    total_updates: int
    candle_count: int
    cache_hit_rate: float
    render_time_ms: float


@dataclass
class ChartDisplayRange:
    """차트 표시 범위 계산"""
    start_index: int = 0
    end_index: int = 0
    visible_candles: int = 50
    total_candles: int = 0

    def calculate_auto_scroll_range(self) -> Tuple[int, int]:
        """자동 스크롤을 위한 범위 계산"""
        if self.total_candles <= self.visible_candles:
            return 0, max(0, self.total_candles - 1)

        end_idx = self.total_candles - 1
        start_idx = max(0, end_idx - self.visible_candles + 1)
        return start_idx, end_idx

    def calculate_zoom_range(self, center_index: int, zoom_factor: float) -> Tuple[int, int]:
        """줌을 위한 범위 계산"""
        new_visible = max(10, int(self.visible_candles / zoom_factor))

        start_idx = max(0, center_index - new_visible // 2)
        end_idx = min(self.total_candles - 1, start_idx + new_visible - 1)

        # 경계 조정
        if end_idx == self.total_candles - 1:
            start_idx = max(0, end_idx - new_visible + 1)

        return start_idx, end_idx


class ChartStateService:
    """
    차트 상태 관리 도메인 서비스

    핵심 책임:
    - 차트 표시 상태 관리
    - 데이터 변경 감지 로직
    - 줌/스크롤 계산
    - 성능 메트릭스 계산
    """

    def __init__(self):
        self._current_state: Optional[ChartViewState] = None
        self._candle_data: List[CandleData] = []
        self._display_range = ChartDisplayRange()

        # 성능 추적
        self._update_count = 0
        self._last_update_time = 0.0
        self._performance_history: List[float] = []

    def initialize_state(
        self,
        symbol: str,
        timeframe: str,
        visible_candles: int = 50
    ) -> ChartViewState:
        """차트 상태 초기화"""
        self._display_range.visible_candles = visible_candles

        self._current_state = ChartViewState(
            symbol=symbol,
            timeframe=timeframe,
            candle_count=0,
            visible_range=(0, 0),
            zoom_level=1.0,
            auto_scroll_enabled=True,
            is_realtime=False,
            last_update_time=datetime.now()
        )

        return self._current_state

    def detect_data_changes(self, new_candles: List[CandleData]) -> bool:
        """데이터 변경 감지"""
        if len(new_candles) != len(self._candle_data):
            return True

        if not new_candles or not self._candle_data:
            return len(new_candles) != len(self._candle_data)

        # 마지막 캔들 비교 (실시간 업데이트 감지)
        last_new = new_candles[-1]
        last_old = self._candle_data[-1]

        return (
            last_new.close_price != last_old.close_price
            or last_new.high_price != last_old.high_price
            or last_new.low_price != last_old.low_price
            or last_new.volume != last_old.volume
        )

    def update_candle_data(self, candles: List[CandleData]) -> ChartViewState:
        """캔들 데이터 업데이트"""
        if not self._current_state:
            raise ValueError("차트 상태가 초기화되지 않음")

        data_changed = self.detect_data_changes(candles)
        if not data_changed:
            return self._current_state

        # 데이터 업데이트
        self._candle_data = candles.copy()
        self._display_range.total_candles = len(candles)
        self._update_count += 1

        # 표시 범위 계산
        if self._current_state.auto_scroll_enabled:
            start_idx, end_idx = self._display_range.calculate_auto_scroll_range()
        else:
            start_idx, end_idx = self._current_state.visible_range
            # 데이터 범위 검증
            end_idx = min(end_idx, len(candles) - 1)
            start_idx = min(start_idx, end_idx)

        # 새 상태 생성
        self._current_state = ChartViewState(
            symbol=self._current_state.symbol,
            timeframe=self._current_state.timeframe,
            candle_count=len(candles),
            visible_range=(start_idx, end_idx),
            zoom_level=self._current_state.zoom_level,
            auto_scroll_enabled=self._current_state.auto_scroll_enabled,
            is_realtime=True,  # 데이터 업데이트 시 실시간 모드
            last_update_time=datetime.now()
        )

        return self._current_state

    def add_realtime_candle(self, candle: CandleData) -> ChartViewState:
        """실시간 캔들 추가"""
        if not self._current_state:
            raise ValueError("차트 상태가 초기화되지 않음")

        self._candle_data.append(candle)
        return self.update_candle_data(self._candle_data)

    def update_last_candle(self, candle: CandleData) -> ChartViewState:
        """마지막 캔들 업데이트"""
        if not self._current_state or not self._candle_data:
            raise ValueError("차트 상태가 초기화되지 않음 또는 데이터 없음")

        self._candle_data[-1] = candle
        return self.update_candle_data(self._candle_data)

    def change_zoom(self, zoom_factor: float, center_index: Optional[int] = None) -> ChartViewState:
        """줌 변경"""
        if not self._current_state:
            raise ValueError("차트 상태가 초기화되지 않음")

        if center_index is None:
            # 현재 표시 범위의 중앙을 기준으로
            start, end = self._current_state.visible_range
            center_index = (start + end) // 2

        # 새 줌 레벨 계산
        new_zoom = max(0.1, min(10.0, self._current_state.zoom_level * zoom_factor))

        # 새 표시 범위 계산
        start_idx, end_idx = self._display_range.calculate_zoom_range(center_index, new_zoom)

        self._current_state = ChartViewState(
            symbol=self._current_state.symbol,
            timeframe=self._current_state.timeframe,
            candle_count=self._current_state.candle_count,
            visible_range=(start_idx, end_idx),
            zoom_level=new_zoom,
            auto_scroll_enabled=False,  # 줌 시 자동 스크롤 비활성화
            is_realtime=self._current_state.is_realtime,
            last_update_time=datetime.now()
        )

        return self._current_state

    def toggle_auto_scroll(self, enabled: bool) -> ChartViewState:
        """자동 스크롤 토글"""
        if not self._current_state:
            raise ValueError("차트 상태가 초기화되지 않음")

        # 자동 스크롤 활성화 시 최신 데이터로 이동
        if enabled and not self._current_state.auto_scroll_enabled:
            start_idx, end_idx = self._display_range.calculate_auto_scroll_range()
            visible_range = (start_idx, end_idx)
        else:
            visible_range = self._current_state.visible_range

        self._current_state = ChartViewState(
            symbol=self._current_state.symbol,
            timeframe=self._current_state.timeframe,
            candle_count=self._current_state.candle_count,
            visible_range=visible_range,
            zoom_level=self._current_state.zoom_level,
            auto_scroll_enabled=enabled,
            is_realtime=self._current_state.is_realtime,
            last_update_time=datetime.now()
        )

        return self._current_state

    def change_symbol(self, symbol: str) -> ChartViewState:
        """심볼 변경"""
        if not self._current_state:
            raise ValueError("차트 상태가 초기화되지 않음")

        # 데이터 리셋
        self._candle_data.clear()
        self._display_range.total_candles = 0

        self._current_state = ChartViewState(
            symbol=symbol,
            timeframe=self._current_state.timeframe,
            candle_count=0,
            visible_range=(0, 0),
            zoom_level=1.0,
            auto_scroll_enabled=True,
            is_realtime=False,
            last_update_time=datetime.now()
        )

        return self._current_state

    def change_timeframe(self, timeframe: str) -> ChartViewState:
        """타임프레임 변경"""
        if not self._current_state:
            raise ValueError("차트 상태가 초기화되지 않음")

        # 데이터 리셋
        self._candle_data.clear()
        self._display_range.total_candles = 0

        self._current_state = ChartViewState(
            symbol=self._current_state.symbol,
            timeframe=timeframe,
            candle_count=0,
            visible_range=(0, 0),
            zoom_level=1.0,
            auto_scroll_enabled=True,
            is_realtime=False,
            last_update_time=datetime.now()
        )

        return self._current_state

    def record_performance_sample(self, update_time_ms: float) -> None:
        """성능 샘플 기록"""
        self._last_update_time = update_time_ms
        self._performance_history.append(update_time_ms)

        # 최근 100개 샘플만 유지
        if len(self._performance_history) > 100:
            self._performance_history = self._performance_history[-100:]

    def calculate_performance_metrics(self, render_time_ms: float = 0.0) -> ChartPerformanceMetrics:
        """성능 메트릭스 계산"""
        if not self._performance_history:
            avg_time = self._last_update_time
            fps = 0.0
        else:
            avg_time = sum(self._performance_history) / len(self._performance_history)
            # FPS 계산 (1000ms / 평균 업데이트 시간)
            fps = 1000.0 / avg_time if avg_time > 0 else 0.0

        # 캐시 히트율 계산 (임시 구현)
        cache_hit_rate = 0.85 if len(self._candle_data) > 0 else 0.0

        return ChartPerformanceMetrics(
            fps=fps,
            last_update_time_ms=self._last_update_time,
            total_updates=self._update_count,
            candle_count=len(self._candle_data),
            cache_hit_rate=cache_hit_rate,
            render_time_ms=render_time_ms
        )

    def get_visible_candles(self) -> List[CandleData]:
        """현재 표시 범위의 캔들 데이터 반환"""
        if not self._current_state or not self._candle_data:
            return []

        start, end = self._current_state.visible_range
        end = min(end, len(self._candle_data) - 1)
        start = max(0, min(start, end))

        return self._candle_data[start:end + 1]

    def get_current_state(self) -> Optional[ChartViewState]:
        """현재 차트 상태 반환"""
        return self._current_state

    def get_candle_data(self) -> List[CandleData]:
        """전체 캔들 데이터 반환"""
        return self._candle_data.copy()
