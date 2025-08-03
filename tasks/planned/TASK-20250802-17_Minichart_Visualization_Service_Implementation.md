# 📋 TASK-20250802-17: 미니차트 시각화 서비스 구현

## 🎯 **작업 개요**
shared_simulation/charts/ 폴더의 미니차트 시스템을 UI 독립적인 business_logic 서비스로 분리하여 재사용성을 극대화합니다.

## 📊 **현재 상황**

### **분리 대상 파일들**
```python
# shared_simulation/charts/ 폴더 (UI 계층에 위치)
├── simulation_control_widget.py → 차트 제어 UI + 비즈니스 로직 혼재
├── simulation_result_widget.py → 결과 표시 UI + 데이터 처리 로직 혼재
├── chart_visualizer.py → 차트 렌더링 + 데이터 변환 로직 혼재
└── 기타 차트 관련 유틸리티들

# 현재 미니차트 재사용 현황
├── trigger_builder에서 사용 → 트리거 시뮬레이션 차트
└── strategy_maker에서 사용 → 전략 백테스팅 차트
```

### **미니차트 핵심 기능**
```python
# 현재 미니차트 시스템이 제공하는 기능들
├── 실시간 가격 데이터 차트 렌더링
├── 기술 지표 오버레이 (SMA, EMA, RSI, MACD)
├── 트리거 포인트 마킹 및 시각화
├── 크로스 신호 표시
├── 확대/축소, 팬 기능
├── 차트 테마 변경 (다크/라이트 모드)
├── 데이터 구간 선택 및 필터링
└── 시뮬레이션 결과 시각화
```

## 🏗️ **구현 목표**

### **새로운 서비스 구조**
```
business_logic/visualization/
├── engines/
│   ├── __init__.py
│   ├── chart_data_engine.py                # 차트 데이터 생성 및 변환
│   ├── indicator_overlay_engine.py         # 지표 오버레이 계산
│   ├── signal_visualization_engine.py      # 신호 마킹 및 시각화
│   └── chart_rendering_engine.py           # 차트 렌더링 로직 (UI 독립적)
├── models/
│   ├── __init__.py
│   ├── chart_configuration_model.py        # 차트 설정 모델
│   ├── chart_data_model.py                 # 차트 데이터 모델
│   ├── visualization_theme_model.py        # 테마 모델
│   └── chart_interaction_model.py          # 상호작용 모델
└── services/
    ├── __init__.py
    ├── minichart_orchestration_service.py  # 메인 미니차트 서비스
    ├── chart_theme_service.py              # 테마 관리 서비스
    └── chart_export_service.py             # 차트 내보내기 서비스
```

### **UI 어댑터 구조**
```
ui/desktop/adapters/visualization/
├── __init__.py
├── minichart_widget_adapter.py             # 미니차트 위젯 어댑터
├── chart_control_adapter.py                # 차트 제어 어댑터
└── chart_theme_adapter.py                  # 테마 UI 어댑터
```

### **MinichartOrchestrationService 클래스 설계**
```python
class MinichartOrchestrationService:
    """미니차트 오케스트레이션 서비스 - UI 독립적 차트 시스템"""
    
    def __init__(self):
        """차트 엔진들 초기화"""
        self._data_engine = ChartDataEngine()
        self._overlay_engine = IndicatorOverlayEngine()
        self._signal_engine = SignalVisualizationEngine()
        self._rendering_engine = ChartRenderingEngine()
        self._theme_service = ChartThemeService()
    
    def create_chart_data(self, price_data: List[float], indicators: Dict[str, Any], 
                         signals: List[Dict], config: ChartConfiguration) -> ChartDataModel:
        """차트 데이터 생성"""
        
    def render_chart(self, chart_data: ChartDataModel, 
                    render_config: RenderConfiguration) -> ChartRenderResult:
        """차트 렌더링 (UI 독립적)"""
        
    def add_indicator_overlay(self, chart_data: ChartDataModel, 
                            indicator: IndicatorConfig) -> ChartDataModel:
        """지표 오버레이 추가"""
        
    def mark_signals(self, chart_data: ChartDataModel, 
                    signals: List[SignalPoint]) -> ChartDataModel:
        """신호 마킹"""
```

## 📋 **상세 작업 내용**

### **1. 기존 차트 시스템 분석 (2시간)**
```powershell
# 기존 shared_simulation/charts/ 분석
python -c @"
import sys
import os
sys.path.append('.')

# 기존 차트 컴포넌트들의 의존성 분석
chart_files = [
    'upbit_auto_trading/ui/desktop/screens/strategy_management/shared_simulation/charts/simulation_control_widget.py',
    'upbit_auto_trading/ui/desktop/screens/strategy_management/shared_simulation/charts/simulation_result_widget.py', 
    'upbit_auto_trading/ui/desktop/screens/strategy_management/shared_simulation/charts/chart_visualizer.py'
]

for file_path in chart_files:
    if os.path.exists(file_path):
        print(f'분석 대상: {file_path}')
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f'  - 라인 수: {len(lines)}')
            
            # PyQt6 의존성 확인
            pyqt_imports = [line.strip() for line in lines if 'PyQt6' in line and 'import' in line]
            print(f'  - PyQt6 의존성: {len(pyqt_imports)}개')
            
            # matplotlib 의존성 확인
            mpl_imports = [line.strip() for line in lines if 'matplotlib' in line and 'import' in line]
            print(f'  - matplotlib 의존성: {len(mpl_imports)}개')
            
            print()
    else:
        print(f'파일 없음: {file_path}')
"@
```

### **2. 차트 데이터 모델 구현 (2시간)**
```python
# business_logic/visualization/models/chart_data_model.py
"""
차트 데이터 관련 모델 클래스들
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np

class ChartType(Enum):
    """차트 타입"""
    CANDLESTICK = "candlestick"
    LINE = "line"
    AREA = "area"
    SCATTER = "scatter"

class TimeFrame(Enum):
    """시간 프레임"""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"

@dataclass
class PricePoint:
    """가격 포인트"""
    timestamp: float
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float = 0.0

@dataclass
class IndicatorPoint:
    """지표 포인트"""
    timestamp: float
    value: float
    indicator_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SignalPoint:
    """신호 포인트"""
    timestamp: float
    price: float
    signal_type: str  # buy, sell, trigger, cross
    strength: float = 1.0
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ChartConfiguration:
    """차트 설정"""
    chart_type: ChartType = ChartType.CANDLESTICK
    time_frame: TimeFrame = TimeFrame.HOUR_1
    show_volume: bool = True
    show_grid: bool = True
    width: int = 800
    height: int = 600
    title: str = ""
    theme: str = "default"

@dataclass
class IndicatorConfig:
    """지표 설정"""
    indicator_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    color: str = "blue"
    line_style: str = "solid"
    line_width: int = 2
    overlay: bool = True  # True: 메인 차트, False: 서브 차트

@dataclass
class ChartDataModel:
    """차트 데이터 모델 - 전체 차트 데이터 컨테이너"""
    # 기본 가격 데이터
    price_data: List[PricePoint] = field(default_factory=list)
    
    # 지표 데이터
    indicators: Dict[str, List[IndicatorPoint]] = field(default_factory=dict)
    
    # 신호 데이터
    signals: List[SignalPoint] = field(default_factory=list)
    
    # 차트 설정
    configuration: ChartConfiguration = field(default_factory=ChartConfiguration)
    
    # 메타데이터
    data_source: str = "unknown"
    created_at: float = 0.0
    data_range: Tuple[float, float] = (0.0, 0.0)
    
    def get_price_series(self) -> pd.DataFrame:
        """가격 데이터를 pandas DataFrame으로 변환"""
        if not self.price_data:
            return pd.DataFrame()
        
        data = {
            'timestamp': [p.timestamp for p in self.price_data],
            'open': [p.open_price for p in self.price_data],
            'high': [p.high_price for p in self.price_data],
            'low': [p.low_price for p in self.price_data],
            'close': [p.close_price for p in self.price_data],
            'volume': [p.volume for p in self.price_data]
        }
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        return df.set_index('timestamp')
    
    def get_indicator_series(self, indicator_name: str) -> pd.Series:
        """특정 지표 데이터를 pandas Series로 변환"""
        if indicator_name not in self.indicators:
            return pd.Series()
        
        indicator_data = self.indicators[indicator_name]
        timestamps = [p.timestamp for p in indicator_data]
        values = [p.value for p in indicator_data]
        
        index = pd.to_datetime(timestamps, unit='s')
        return pd.Series(values, index=index, name=indicator_name)
    
    def add_indicator_data(self, indicator_name: str, 
                          timestamps: List[float], values: List[float],
                          parameters: Dict[str, Any] = None):
        """지표 데이터 추가"""
        if len(timestamps) != len(values):
            raise ValueError("timestamps와 values의 길이가 일치하지 않습니다")
        
        params = parameters or {}
        indicator_points = [
            IndicatorPoint(ts, val, indicator_name, params)
            for ts, val in zip(timestamps, values)
        ]
        
        self.indicators[indicator_name] = indicator_points
    
    def add_signal(self, timestamp: float, price: float, signal_type: str,
                  strength: float = 1.0, description: str = "", 
                  metadata: Dict[str, Any] = None):
        """신호 포인트 추가"""
        signal = SignalPoint(
            timestamp=timestamp,
            price=price,
            signal_type=signal_type,
            strength=strength,
            description=description,
            metadata=metadata or {}
        )
        self.signals.append(signal)
    
    def get_data_summary(self) -> Dict[str, Any]:
        """데이터 요약 정보"""
        return {
            "price_points": len(self.price_data),
            "indicators": list(self.indicators.keys()),
            "signal_count": len(self.signals),
            "time_range": self.data_range,
            "chart_type": self.configuration.chart_type.value,
            "data_source": self.data_source
        }

@dataclass
class ChartRenderResult:
    """차트 렌더링 결과"""
    success: bool
    chart_data: Any = None  # matplotlib figure 또는 기타 차트 객체
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    render_time: float = 0.0
```

### **3. 차트 데이터 엔진 구현 (3시간)**
```python
# business_logic/visualization/engines/chart_data_engine.py
"""
차트 데이터 생성 및 변환 엔진
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ..models.chart_data_model import (
    ChartDataModel, PricePoint, ChartConfiguration, TimeFrame
)

class ChartDataEngine:
    """차트 데이터 생성 및 변환 엔진"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_chart_data_from_prices(self, price_list: List[float], 
                                    timestamps: Optional[List[float]] = None,
                                    config: Optional[ChartConfiguration] = None) -> ChartDataModel:
        """
        가격 리스트로부터 차트 데이터 생성
        기존 시뮬레이션에서 사용하던 방식과 호환
        
        Args:
            price_list: 가격 데이터 리스트
            timestamps: 타임스탬프 리스트 (없으면 자동 생성)
            config: 차트 설정
            
        Returns:
            ChartDataModel: 생성된 차트 데이터
        """
        try:
            self.logger.debug(f"차트 데이터 생성: 가격 {len(price_list)}개")
            
            # 기본 설정
            chart_config = config or ChartConfiguration()
            
            # 타임스탬프 생성 (없는 경우)
            if timestamps is None:
                base_time = datetime.now().timestamp()
                interval = self._get_interval_seconds(chart_config.time_frame)
                timestamps = [base_time - (len(price_list) - i) * interval 
                            for i in range(len(price_list))]
            
            if len(timestamps) != len(price_list):
                raise ValueError("timestamps와 price_list 길이가 일치하지 않습니다")
            
            # 가격 포인트 생성 (라인 차트용으로 OHLC 동일하게 설정)
            price_points = []
            for i, (ts, price) in enumerate(zip(timestamps, price_list)):
                # 이전 가격 대비 변동 시뮬레이션 (임시)
                if i > 0:
                    prev_price = price_list[i-1]
                    volatility = abs(price - prev_price) * 0.1
                    high = price + volatility
                    low = price - volatility
                    open_price = prev_price
                else:
                    high = low = open_price = price
                
                price_points.append(PricePoint(
                    timestamp=ts,
                    open_price=open_price,
                    high_price=high,
                    low_price=low,
                    close_price=price,
                    volume=1000.0  # 기본 볼륨
                ))
            
            # 데이터 범위 계산
            data_range = (timestamps[0], timestamps[-1]) if timestamps else (0.0, 0.0)
            
            chart_data = ChartDataModel(
                price_data=price_points,
                configuration=chart_config,
                data_source="price_list",
                created_at=datetime.now().timestamp(),
                data_range=data_range
            )
            
            self.logger.debug(f"차트 데이터 생성 완료: {len(price_points)}개 포인트")
            return chart_data
            
        except Exception as e:
            self.logger.error(f"차트 데이터 생성 오류: {str(e)}")
            raise
    
    def create_chart_data_from_ohlcv(self, ohlcv_data: List[Dict[str, float]],
                                   config: Optional[ChartConfiguration] = None) -> ChartDataModel:
        """
        OHLCV 데이터로부터 차트 데이터 생성
        
        Args:
            ohlcv_data: OHLCV 데이터 리스트 [{"timestamp": ..., "open": ..., "high": ..., "low": ..., "close": ..., "volume": ...}]
            config: 차트 설정
            
        Returns:
            ChartDataModel: 생성된 차트 데이터
        """
        try:
            chart_config = config or ChartConfiguration()
            
            price_points = []
            for data_point in ohlcv_data:
                price_points.append(PricePoint(
                    timestamp=data_point["timestamp"],
                    open_price=data_point["open"],
                    high_price=data_point["high"],
                    low_price=data_point["low"],
                    close_price=data_point["close"],
                    volume=data_point.get("volume", 0.0)
                ))
            
            timestamps = [p.timestamp for p in price_points]
            data_range = (min(timestamps), max(timestamps)) if timestamps else (0.0, 0.0)
            
            return ChartDataModel(
                price_data=price_points,
                configuration=chart_config,
                data_source="ohlcv",
                created_at=datetime.now().timestamp(),
                data_range=data_range
            )
            
        except Exception as e:
            self.logger.error(f"OHLCV 차트 데이터 생성 오류: {str(e)}")
            raise
    
    def add_technical_indicators(self, chart_data: ChartDataModel, 
                               indicators: Dict[str, Dict[str, Any]]) -> ChartDataModel:
        """
        기술 지표를 차트 데이터에 추가
        
        Args:
            chart_data: 기존 차트 데이터
            indicators: 지표 설정 {"SMA": {"period": 20}, "RSI": {"period": 14}}
            
        Returns:
            ChartDataModel: 지표가 추가된 차트 데이터
        """
        try:
            # 기술 지표 계산 (TechnicalIndicatorCalculator 사용)
            from ...triggers.engines.technical_indicator_calculator import TechnicalIndicatorCalculator
            calculator = TechnicalIndicatorCalculator()
            
            # 가격 데이터 추출
            close_prices = [p.close_price for p in chart_data.price_data]
            timestamps = [p.timestamp for p in chart_data.price_data]
            
            for indicator_name, params in indicators.items():
                self.logger.debug(f"지표 계산: {indicator_name} with {params}")
                
                # 지표 계산
                result = calculator.calculate_indicator(indicator_name, close_prices, params)
                
                if result.success:
                    # 차트 데이터에 지표 추가
                    chart_data.add_indicator_data(
                        indicator_name, timestamps, result.values, params
                    )
                    self.logger.debug(f"지표 추가 완료: {indicator_name}")
                else:
                    self.logger.warning(f"지표 계산 실패: {indicator_name} - {result.error_message}")
            
            return chart_data
            
        except Exception as e:
            self.logger.error(f"기술 지표 추가 오류: {str(e)}")
            raise
    
    def add_trigger_signals(self, chart_data: ChartDataModel, 
                          trigger_points: List[int], signal_type: str = "trigger",
                          signal_strength: float = 1.0) -> ChartDataModel:
        """
        트리거 신호를 차트 데이터에 추가
        
        Args:
            chart_data: 기존 차트 데이터
            trigger_points: 트리거 포인트 인덱스 리스트
            signal_type: 신호 타입
            signal_strength: 신호 강도
            
        Returns:
            ChartDataModel: 신호가 추가된 차트 데이터
        """
        try:
            for index in trigger_points:
                if 0 <= index < len(chart_data.price_data):
                    price_point = chart_data.price_data[index]
                    
                    chart_data.add_signal(
                        timestamp=price_point.timestamp,
                        price=price_point.close_price,
                        signal_type=signal_type,
                        strength=signal_strength,
                        description=f"{signal_type} 신호 (인덱스: {index})",
                        metadata={"index": index}
                    )
            
            self.logger.debug(f"트리거 신호 추가 완료: {len(trigger_points)}개")
            return chart_data
            
        except Exception as e:
            self.logger.error(f"트리거 신호 추가 오류: {str(e)}")
            raise
    
    def filter_data_by_range(self, chart_data: ChartDataModel, 
                           start_time: float, end_time: float) -> ChartDataModel:
        """
        시간 범위로 데이터 필터링
        
        Args:
            chart_data: 원본 차트 데이터
            start_time: 시작 시간 (timestamp)
            end_time: 종료 시간 (timestamp)
            
        Returns:
            ChartDataModel: 필터링된 차트 데이터
        """
        try:
            # 가격 데이터 필터링
            filtered_prices = [
                p for p in chart_data.price_data 
                if start_time <= p.timestamp <= end_time
            ]
            
            # 지표 데이터 필터링
            filtered_indicators = {}
            for name, points in chart_data.indicators.items():
                filtered_indicators[name] = [
                    p for p in points 
                    if start_time <= p.timestamp <= end_time
                ]
            
            # 신호 데이터 필터링
            filtered_signals = [
                s for s in chart_data.signals 
                if start_time <= s.timestamp <= end_time
            ]
            
            # 새로운 차트 데이터 생성
            filtered_chart_data = ChartDataModel(
                price_data=filtered_prices,
                indicators=filtered_indicators,
                signals=filtered_signals,
                configuration=chart_data.configuration,
                data_source=chart_data.data_source + "_filtered",
                created_at=datetime.now().timestamp(),
                data_range=(start_time, end_time)
            )
            
            self.logger.debug(f"데이터 필터링 완료: {len(filtered_prices)}개 포인트")
            return filtered_chart_data
            
        except Exception as e:
            self.logger.error(f"데이터 필터링 오류: {str(e)}")
            raise
    
    def _get_interval_seconds(self, time_frame: TimeFrame) -> int:
        """시간 프레임을 초 단위로 변환"""
        intervals = {
            TimeFrame.MINUTE_1: 60,
            TimeFrame.MINUTE_5: 300,
            TimeFrame.MINUTE_15: 900,
            TimeFrame.HOUR_1: 3600,
            TimeFrame.HOUR_4: 14400,
            TimeFrame.DAY_1: 86400
        }
        return intervals.get(time_frame, 3600)  # 기본 1시간
    
    def resample_data(self, chart_data: ChartDataModel, 
                     new_timeframe: TimeFrame) -> ChartDataModel:
        """
        데이터를 새로운 시간 프레임으로 리샘플링
        
        Args:
            chart_data: 원본 차트 데이터
            new_timeframe: 새로운 시간 프레임
            
        Returns:
            ChartDataModel: 리샘플링된 차트 데이터
        """
        try:
            # pandas를 사용한 리샘플링
            df = chart_data.get_price_series()
            
            # 리샘플링 규칙 매핑
            rule_mapping = {
                TimeFrame.MINUTE_1: '1T',
                TimeFrame.MINUTE_5: '5T', 
                TimeFrame.MINUTE_15: '15T',
                TimeFrame.HOUR_1: '1H',
                TimeFrame.HOUR_4: '4H',
                TimeFrame.DAY_1: '1D'
            }
            
            rule = rule_mapping.get(new_timeframe, '1H')
            
            # OHLCV 리샘플링
            resampled = df.resample(rule).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            # 새로운 차트 데이터 생성
            ohlcv_data = []
            for timestamp, row in resampled.iterrows():
                ohlcv_data.append({
                    "timestamp": timestamp.timestamp(),
                    "open": row['open'],
                    "high": row['high'],
                    "low": row['low'],
                    "close": row['close'],
                    "volume": row['volume']
                })
            
            new_config = chart_data.configuration
            new_config.time_frame = new_timeframe
            
            resampled_chart_data = self.create_chart_data_from_ohlcv(ohlcv_data, new_config)
            
            self.logger.debug(f"리샘플링 완료: {len(resampled)}개 포인트")
            return resampled_chart_data
            
        except Exception as e:
            self.logger.error(f"리샘플링 오류: {str(e)}")
            raise
```

### **4. 미니차트 오케스트레이션 서비스 구현 (3시간)**
```python
# business_logic/visualization/services/minichart_orchestration_service.py
"""
미니차트 오케스트레이션 서비스
전체 미니차트 워크플로우 관리
"""

from typing import List, Dict, Any, Optional
import logging
from ..engines.chart_data_engine import ChartDataEngine
from ..models.chart_data_model import ChartDataModel, ChartConfiguration, ChartRenderResult

class MinichartOrchestrationService:
    """미니차트 오케스트레이션 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 엔진들 초기화
        self._data_engine = ChartDataEngine()
        
        self.logger.info("MinichartOrchestrationService 초기화 완료")
    
    def create_simulation_chart(self, price_data: List[float], 
                             trigger_points: List[int] = None,
                             indicators: Dict[str, Dict[str, Any]] = None,
                             config: Optional[ChartConfiguration] = None) -> ChartDataModel:
        """
        시뮬레이션 차트 생성
        기존 shared_simulation에서 사용하던 방식과 호환
        
        Args:
            price_data: 가격 데이터
            trigger_points: 트리거 포인트 인덱스들
            indicators: 추가할 지표들
            config: 차트 설정
            
        Returns:
            ChartDataModel: 생성된 차트 데이터
        """
        try:
            self.logger.debug(f"시뮬레이션 차트 생성: 가격 {len(price_data)}개")
            
            # 1. 기본 차트 데이터 생성
            chart_data = self._data_engine.create_chart_data_from_prices(
                price_data, config=config
            )
            
            # 2. 기술 지표 추가
            if indicators:
                chart_data = self._data_engine.add_technical_indicators(
                    chart_data, indicators
                )
            
            # 3. 트리거 신호 추가
            if trigger_points:
                chart_data = self._data_engine.add_trigger_signals(
                    chart_data, trigger_points, "trigger"
                )
            
            self.logger.debug("시뮬레이션 차트 생성 완료")
            return chart_data
            
        except Exception as e:
            self.logger.error(f"시뮬레이션 차트 생성 오류: {str(e)}")
            raise
    
    def create_strategy_backtesting_chart(self, price_data: List[float],
                                        buy_signals: List[int] = None,
                                        sell_signals: List[int] = None,
                                        indicators: Dict[str, Dict[str, Any]] = None,
                                        config: Optional[ChartConfiguration] = None) -> ChartDataModel:
        """
        전략 백테스팅 차트 생성
        strategy_maker에서 사용할 차트
        
        Args:
            price_data: 가격 데이터
            buy_signals: 매수 신호 인덱스들
            sell_signals: 매도 신호 인덱스들
            indicators: 추가할 지표들
            config: 차트 설정
            
        Returns:
            ChartDataModel: 생성된 차트 데이터
        """
        try:
            self.logger.debug(f"백테스팅 차트 생성: 가격 {len(price_data)}개")
            
            # 1. 기본 차트 데이터 생성
            chart_data = self._data_engine.create_chart_data_from_prices(
                price_data, config=config
            )
            
            # 2. 기술 지표 추가
            if indicators:
                chart_data = self._data_engine.add_technical_indicators(
                    chart_data, indicators
                )
            
            # 3. 매수 신호 추가
            if buy_signals:
                chart_data = self._data_engine.add_trigger_signals(
                    chart_data, buy_signals, "buy", 1.0
                )
            
            # 4. 매도 신호 추가
            if sell_signals:
                chart_data = self._data_engine.add_trigger_signals(
                    chart_data, sell_signals, "sell", 1.0
                )
            
            self.logger.debug("백테스팅 차트 생성 완료")
            return chart_data
            
        except Exception as e:
            self.logger.error(f"백테스팅 차트 생성 오류: {str(e)}")
            raise
    
    def get_chart_summary(self, chart_data: ChartDataModel) -> Dict[str, Any]:
        """차트 데이터 요약 정보"""
        try:
            summary = chart_data.get_data_summary()
            
            # 추가 분석 정보
            if chart_data.price_data:
                prices = [p.close_price for p in chart_data.price_data]
                summary.update({
                    "price_range": (min(prices), max(prices)),
                    "price_change": prices[-1] - prices[0] if len(prices) > 1 else 0,
                    "price_change_percent": ((prices[-1] - prices[0]) / prices[0] * 100) if len(prices) > 1 and prices[0] != 0 else 0
                })
            
            # 신호 분석
            signal_types = {}
            for signal in chart_data.signals:
                signal_types[signal.signal_type] = signal_types.get(signal.signal_type, 0) + 1
            summary["signal_breakdown"] = signal_types
            
            return summary
            
        except Exception as e:
            self.logger.error(f"차트 요약 생성 오류: {str(e)}")
            return {}
    
    def export_chart_data(self, chart_data: ChartDataModel, 
                         format_type: str = "json") -> Dict[str, Any]:
        """
        차트 데이터 내보내기
        
        Args:
            chart_data: 차트 데이터
            format_type: 내보내기 형식 (json, csv 등)
            
        Returns:
            Dict: 내보내기 데이터
        """
        try:
            if format_type == "json":
                return {
                    "price_data": [
                        {
                            "timestamp": p.timestamp,
                            "open": p.open_price,
                            "high": p.high_price,
                            "low": p.low_price,
                            "close": p.close_price,
                            "volume": p.volume
                        }
                        for p in chart_data.price_data
                    ],
                    "indicators": {
                        name: [
                            {
                                "timestamp": point.timestamp,
                                "value": point.value,
                                "parameters": point.parameters
                            }
                            for point in points
                        ]
                        for name, points in chart_data.indicators.items()
                    },
                    "signals": [
                        {
                            "timestamp": s.timestamp,
                            "price": s.price,
                            "type": s.signal_type,
                            "strength": s.strength,
                            "description": s.description,
                            "metadata": s.metadata
                        }
                        for s in chart_data.signals
                    ],
                    "configuration": {
                        "chart_type": chart_data.configuration.chart_type.value,
                        "time_frame": chart_data.configuration.time_frame.value,
                        "title": chart_data.configuration.title,
                        "theme": chart_data.configuration.theme
                    },
                    "metadata": {
                        "data_source": chart_data.data_source,
                        "created_at": chart_data.created_at,
                        "data_range": chart_data.data_range
                    }
                }
            else:
                raise ValueError(f"지원하지 않는 형식: {format_type}")
                
        except Exception as e:
            self.logger.error(f"차트 데이터 내보내기 오류: {str(e)}")
            raise
```

## ✅ **완료 기준**

### **구현 완료 체크리스트**
- [ ] 차트 데이터 모델 구현 완료
- [ ] 차트 데이터 엔진 구현 완료 
- [ ] 미니차트 오케스트레이션 서비스 구현 완료
- [ ] UI 어댑터 구현 완료
- [ ] 기존 shared_simulation과 100% 호환성 보장
- [ ] 단위 테스트 90% 이상 커버리지

### **품질 기준**
- [ ] PyQt6 의존성 완전 분리
- [ ] matplotlib 차트 렌더링 지원
- [ ] trigger_builder와 strategy_maker에서 재사용 가능
- [ ] 성능 최적화 (대용량 데이터 처리)

### **검증 명령어**
```powershell
# 단위 테스트 실행
pytest tests/unit/visualization/ -v

# 통합 테스트 실행
pytest tests/integration/test_minichart_integration.py -v

# 기존 shared_simulation 호환성 테스트
pytest tests/compatibility/test_shared_simulation_compatibility.py -v
```

## 🔗 **연관 작업**
- **이전**: TASK-20250802-16 (조건 관리 서비스 구현)
- **다음**: TASK-20250802-18 (전체 통합 테스트 및 검증)
- **관련**: TASK-20250802-15 (트리거 빌더 UI 어댑터 구현)

## 📊 **예상 소요 시간**
- **총 소요 시간**: 10시간
- **우선순위**: HIGH
- **복잡도**: HIGH (차트 시스템 복잡성)
- **리스크**: MEDIUM (matplotlib 렌더링 이슈)

---
**작성일**: 2025년 8월 2일  
**담당자**: GitHub Copilot  
**문서 타입**: 시각화 서비스 구현
