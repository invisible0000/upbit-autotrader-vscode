# 📈 Finplot 금융 차트 개발 가이드

> **Phase 3.1 권장 솔루션**: PyQtGraph → Finplot 마이그레이션
> **성능 목표**: 60fps 실시간 업데이트, 200+ 캔들 처리, 명시적 렌더링 제어

## 🎯 왜 Finplot인가?

### **✅ 핵심 장점**
- **금융 차트 전문**: 캔들스틱, 볼린저밴드, RSI 등 네이티브 지원
- **명시적 업데이트 제어**: `update_data(gfx=False)` → `update_gfx()` 분리
- **PyQtGraph 기반**: 고성능 렌더링, PyQt6 완벽 통합
- **실시간 최적화**: 웹소켓 + 효율적 데이터 업데이트 패턴
- **OrderFlow 지원**: 프로급 거래량 프로파일, 히트맵 기능

### **📊 성능 비교**
```
PyQtGraph (직접구현): 커스텀 렌더러 필요, 복잡한 캔들스틱 로직
mplfinance:          전체 재그리기, 60fps 어려움
Finplot:             ⭐ 금융특화 + 실시간 최적화 + 명시적 제어
```

## 🛠 기본 사용법

### **1. 설치**
```bash
pip install finplot
```

### **2. 기본 캔들스틱**
```python
import finplot as fplt
import pandas as pd

# 데이터 준비 (필수 컬럼 순서: time, open, close, high, low)
df = pd.DataFrame({
    'time': timestamps,
    'open': open_prices,
    'close': close_prices,
    'high': high_prices,
    'low': low_prices
})

# 차트 생성
fplt.create_plot('BTC/KRW 1분봉', init_zoom_periods=100)
fplt.candlestick_ochl(df[['open', 'close', 'high', 'low']])
fplt.show()
```

### **3. 실시간 업데이트 패턴**
```python
# 효율적인 업데이트 (핵심!)
plot_candles, plot_volume = fplt.live(2)

def update_chart():
    # 1단계: 데이터만 업데이트 (렌더링 없음)
    plot_candles.candlestick_ochl(new_candles, gfx=False)
    plot_volume.volume_ocv(new_volumes, gfx=False)

    # 2단계: 일괄 렌더링
    plot_candles.update_gfx()
    plot_volume.update_gfx()

# 타이머 기반 실시간 업데이트
fplt.timer_callback(update_chart, 0.5)  # 2Hz
```

## 🏗 DDD 아키텍처 통합

### **Infrastructure Layer**
```python
# upbit_auto_trading/infrastructure/chart/finplot_renderer.py
class FinplotCandlestickRenderer:
    def __init__(self):
        self._plot_items = {}
        self._needs_update = False

    def set_data(self, candles: List[CandleData]) -> bool:
        """데이터 설정 (렌더링 지연)"""
        df = self._convert_to_finplot_format(candles)
        self._plot_items['candles'].candlestick_ochl(df, gfx=False)
        self._needs_update = True
        return True

    def render_updates(self) -> None:
        """명시적 렌더링 실행"""
        if self._needs_update:
            for item in self._plot_items.values():
                item.update_gfx()
            self._needs_update = False
```

### **Presentation Layer**
```python
# upbit_auto_trading/presentation/chart/finplot_widget.py
class FinplotCandlestickWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._renderer = FinplotCandlestickRenderer()
        self._setup_finplot_integration()

    def _setup_finplot_integration(self):
        """Finplot을 PyQt6 레이아웃에 임베딩"""
        layout = QVBoxLayout(self)

        # Finplot 차트 생성
        ax = fplt.create_plot(init_zoom_periods=200)
        self._candles, self._volume = fplt.live(2)

        # PyQt6 위젯으로 임베딩
        layout.addWidget(ax.vb.win)
```

## 🚀 고급 기능

### **1. 다중 패널 레이아웃**
```python
# 5개 패널: 메인차트 + 볼륨 + MACD + RSI + OrderFlow
ax, ax_vol, ax_macd, ax_rsi, ax_flow = fplt.create_plot(
    'Advanced Trading View',
    rows=5,
    row_stretch_factors=[3, 1, 1, 1, 1]  # 메인차트 3배 크기
)

fplt.candlestick_ochl(ohlc_data, ax=ax)
fplt.volume_ocv(volume_data, ax=ax_vol)
fplt.plot(macd_data, ax=ax_macd, legend='MACD')
fplt.plot(rsi_data, ax=ax_rsi, legend='RSI')
```

### **2. OrderFlow 히트맵 (고급)**
```python
# 거래량 프로파일 히트맵
fplt.delta_heatmap(delta_data, filter_limit=0.7, ax=ax)

# POC (Point of Control) 라인
fplt.plot(poc_prices, ax=ax, legend='POC', color='#008FFF')
```

### **3. 실시간 성능 최적화**
```python
class PerformanceOptimizer:
    def __init__(self):
        self._update_queue = []
        self._last_render = time.time()
        self._render_interval = 1/60  # 60fps

    def queue_update(self, data):
        """업데이트 큐잉"""
        self._update_queue.append(data)

    def process_updates(self):
        """배치 처리로 성능 최적화"""
        if time.time() - self._last_render < self._render_interval:
            return

        # 큐에 쌓인 모든 업데이트 처리
        for data in self._update_queue:
            self._apply_data_update(data, gfx=False)

        # 일괄 렌더링
        self._render_all()
        self._update_queue.clear()
        self._last_render = time.time()
```

## 📝 모범 사례

### **✅ DO**
- `update_data(gfx=False)` + `update_gfx()` 분리 사용
- `fplt.live()` 객체로 실시간 플롯 관리
- 타이머 기반 업데이트 (`fplt.timer_callback`)
- 성능을 위한 `init_zoom_periods` 설정
- OrderFlow 분석시 `max_zoom_points` 조정

### **❌ DON'T**
- 매번 전체 차트 재생성하지 말 것
- 동기적 API 호출로 UI 블로킹하지 말 것
- 필요 이상의 높은 업데이트 주기 설정 금지

## 🔗 참고 자료

- **공식 리포지토리**: https://github.com/highfestiva/finplot
- **OrderFlow 확장**: https://github.com/tysonwu/stack-orderflow
- **실시간 예제**: `finplot/examples/bitmex-ws.py`
- **복합 지표**: `finplot/examples/complicated.py`

## 🎯 Phase 3.1 구현 계획

1. **PyQtGraph 코드 교체**: 기존 렌더러를 Finplot 기반으로 마이그레이션
2. **실시간 업데이트**: 웹소켓 + `gfx=False` 패턴 적용
3. **성능 검증**: 200 캔들 + 60fps 목표 달성
4. **DDD 유지**: Infrastructure/Presentation 계층 분리 보존

**결론**: Finplot은 우리의 모든 요구사항(금융 차트, 실시간 성능, PyQt6 통합, 명시적 제어)을 만족하는 최적의 솔루션입니다.
