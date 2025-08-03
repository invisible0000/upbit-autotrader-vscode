# 📋 TASK-20250802-12: 기술 지표 계산 엔진 구현

## 🎯 **작업 개요**
trigger_builder_screen.py의 SMA, EMA, RSI, MACD 계산 로직을 순수 비즈니스 로직으로 분리하여 technical_indicator_calculator.py로 구현합니다.

## 📊 **현재 상황**

### **분리 대상 메서드**
```python
# trigger_builder_screen.py에서 분리할 메서드들 (라인 번호 참조)
├── _calculate_variable_data() (라인 867) → 메인 계산 디스패처
├── _calculate_sma() (라인 937) → SMA 계산
├── _calculate_ema() (라인 941) → EMA 계산  
├── _calculate_rsi() (라인 945) → RSI 계산
└── _calculate_macd() (라인 949) → MACD 계산
```

### **기존 trigger_calculator.py 통합**
```python
# components/shared/trigger_calculator.py (312줄)
# 이미 구현된 순수 로직들을 새 엔진으로 통합
├── calculate_sma() → 기존 로직 활용
├── calculate_ema() → 기존 로직 활용
├── calculate_rsi() → 기존 로직 활용
└── calculate_trigger_points() → trigger_point_detector.py로 이전
```

## 🏗️ **구현 목표**

### **새로운 파일 구조**
```
business_logic/triggers/engines/
├── __init__.py
├── technical_indicator_calculator.py          # 이번 TASK 구현 대상
├── trigger_point_detector.py                  # 다음 TASK
└── cross_signal_analyzer.py                   # 다음 TASK
```

### **TechnicalIndicatorCalculator 클래스 설계**
```python
class TechnicalIndicatorCalculator:
    """기술 지표 계산 엔진 - UI 독립적 순수 비즈니스 로직"""
    
    def __init__(self):
        """초기화"""
        self._supported_indicators = {
            'SMA', 'EMA', 'RSI', 'MACD', 'BOLLINGER', 'STOCHASTIC'
        }
    
    def calculate_indicator(self, indicator_name: str, price_data: List[float], 
                          parameters: Dict[str, Any] = None) -> List[float]:
        """메인 계산 엔트리포인트 - _calculate_variable_data() 대체"""
        
    def calculate_sma(self, prices: List[float], period: int) -> List[float]:
        """단순 이동평균 계산"""
        
    def calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """지수 이동평균 계산"""
        
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """상대강도지수 계산"""
        
    def calculate_macd(self, prices: List[float], fast: int = 12, 
                      slow: int = 26, signal: int = 9) -> Dict[str, List[float]]:
        """MACD 계산"""
```

## 📋 **상세 작업 내용**

### **1. 기존 로직 분석 및 추출 (2시간)**
```powershell
# 기존 계산 로직 분석
python -c @"
import sys
sys.path.append('.')
from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.trigger_builder_screen import TriggerBuilderScreen
from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.shared.trigger_calculator import TriggerCalculator

# 기존 로직 분석 및 테스트 데이터 생성
test_data = [100, 105, 102, 108, 110, 107, 112, 109, 115, 118]
calc = TriggerCalculator()
print('SMA(5):', calc.calculate_sma(test_data, 5))
print('EMA(5):', calc.calculate_ema(test_data, 5))
print('RSI(5):', calc.calculate_rsi(test_data, 5))
"@
```

### **2. technical_indicator_calculator.py 구현 (4시간)**
```python
# business_logic/triggers/engines/technical_indicator_calculator.py
"""
기술 지표 계산 엔진
UI와 완전히 분리된 순수 비즈니스 로직
"""

from typing import List, Dict, Any, Optional, Union
import logging
from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass
class IndicatorResult:
    """지표 계산 결과"""
    values: List[float]
    indicator_name: str
    parameters: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None

class TechnicalIndicatorCalculator:
    """기술 지표 계산 엔진"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._indicator_registry = {
            'SMA': self.calculate_sma,
            'EMA': self.calculate_ema,
            'RSI': self.calculate_rsi,
            'MACD': self.calculate_macd,
            'BOLLINGER': self.calculate_bollinger_bands,
            'STOCHASTIC': self.calculate_stochastic
        }
    
    def calculate_indicator(self, indicator_name: str, price_data: List[float], 
                          parameters: Dict[str, Any] = None) -> IndicatorResult:
        """
        메인 지표 계산 엔트리포인트
        기존 _calculate_variable_data() 메서드를 대체
        
        Args:
            indicator_name: 지표 이름 (SMA, EMA, RSI, MACD 등)
            price_data: 가격 데이터 리스트
            parameters: 지표별 파라미터 (period, fast, slow 등)
            
        Returns:
            IndicatorResult: 계산 결과 및 메타데이터
        """
        # 입력 검증
        if not price_data or len(price_data) < 2:
            return IndicatorResult(
                values=[], indicator_name=indicator_name, 
                parameters=parameters or {}, success=False,
                error_message="가격 데이터가 부족합니다"
            )
        
        # 파라미터 기본값 설정
        params = parameters or {}
        
        try:
            # 지표별 계산 수행
            if indicator_name in self._indicator_registry:
                calculator_func = self._indicator_registry[indicator_name]
                result_values = calculator_func(price_data, **params)
                
                return IndicatorResult(
                    values=result_values,
                    indicator_name=indicator_name,
                    parameters=params,
                    success=True
                )
            else:
                return IndicatorResult(
                    values=[], indicator_name=indicator_name,
                    parameters=params, success=False,
                    error_message=f"지원하지 않는 지표: {indicator_name}"
                )
                
        except Exception as e:
            self.logger.error(f"지표 계산 오류 [{indicator_name}]: {str(e)}")
            return IndicatorResult(
                values=[], indicator_name=indicator_name,
                parameters=params, success=False,
                error_message=str(e)
            )
    
    def calculate_sma(self, prices: List[float], period: int = 20) -> List[float]:
        """단순 이동평균 계산 - 기존 로직 개선"""
        if len(prices) < period:
            return [0.0] * len(prices)
        
        sma_values = []
        for i in range(len(prices)):
            if i < period - 1:
                sma_values.append(0.0)
            else:
                window_sum = sum(prices[i-period+1:i+1])
                sma_values.append(window_sum / period)
        
        return sma_values
    
    def calculate_ema(self, prices: List[float], period: int = 20) -> List[float]:
        """지수 이동평균 계산 - 기존 로직 개선"""
        if len(prices) < period:
            return [0.0] * len(prices)
        
        multiplier = 2.0 / (period + 1)
        ema_values = [0.0] * len(prices)
        
        # 첫 번째 EMA는 SMA로 시작
        ema_values[period-1] = sum(prices[:period]) / period
        
        # 나머지는 EMA 공식 적용
        for i in range(period, len(prices)):
            ema_values[i] = (prices[i] * multiplier) + (ema_values[i-1] * (1 - multiplier))
        
        return ema_values
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """RSI 계산 - 기존 로직 개선"""
        if len(prices) < period + 1:
            return [50.0] * len(prices)  # 중립값 반환
        
        # 가격 변화 계산
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        gains = [max(delta, 0) for delta in deltas]
        losses = [abs(min(delta, 0)) for delta in deltas]
        
        rsi_values = [50.0]  # 첫 번째 값은 중립
        
        # 초기 평균 gain/loss 계산
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        for i in range(period, len(deltas)):
            # Wilder's smoothing 적용
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100.0 - (100.0 / (1.0 + rs))
            
            rsi_values.append(rsi)
        
        # 길이 맞추기
        while len(rsi_values) < len(prices):
            rsi_values.insert(0, 50.0)
        
        return rsi_values
    
    def calculate_macd(self, prices: List[float], fast: int = 12, 
                      slow: int = 26, signal: int = 9) -> List[float]:
        """MACD 계산 - 기존 로직 개선"""
        if len(prices) < max(fast, slow, signal):
            return [0.0] * len(prices)
        
        # EMA 계산
        ema_fast = self.calculate_ema(prices, fast)
        ema_slow = self.calculate_ema(prices, slow)
        
        # MACD 라인 계산
        macd_line = [fast_val - slow_val for fast_val, slow_val in zip(ema_fast, ema_slow)]
        
        # Signal 라인은 MACD의 EMA
        signal_line = self.calculate_ema(macd_line, signal)
        
        # 히스토그램
        histogram = [macd - sig for macd, sig in zip(macd_line, signal_line)]
        
        # 기본적으로 MACD 라인 반환 (UI에서 필요시 추가 데이터 요청 가능)
        return macd_line
```

### **3. 단위 테스트 구현 (2시간)**
```python
# tests/unit/triggers/test_technical_indicator_calculator.py
"""
TechnicalIndicatorCalculator 단위 테스트
기존 계산 결과와의 호환성 보장
"""

import pytest
import numpy as np
from upbit_auto_trading.business_logic.triggers.engines.technical_indicator_calculator import (
    TechnicalIndicatorCalculator, IndicatorResult
)

class TestTechnicalIndicatorCalculator:
    
    def setup_method(self):
        """테스트 설정"""
        self.calculator = TechnicalIndicatorCalculator()
        self.test_data = [100, 105, 102, 108, 110, 107, 112, 109, 115, 118, 120, 117, 125, 122]
    
    def test_sma_calculation(self):
        """SMA 계산 정확성 테스트"""
        result = self.calculator.calculate_indicator("SMA", self.test_data, {"period": 5})
        
        assert result.success is True
        assert len(result.values) == len(self.test_data)
        assert result.indicator_name == "SMA"
        
        # 수동 계산 검증 (5번째 값)
        expected_5th = sum(self.test_data[:5]) / 5  # 105.0
        assert abs(result.values[4] - expected_5th) < 0.01
    
    def test_ema_calculation(self):
        """EMA 계산 정확성 테스트"""
        result = self.calculator.calculate_indicator("EMA", self.test_data, {"period": 5})
        
        assert result.success is True
        assert len(result.values) == len(self.test_data)
        
        # EMA는 점진적으로 변화하는지 확인
        non_zero_values = [v for v in result.values if v > 0]
        assert len(non_zero_values) >= len(self.test_data) - 4
    
    def test_rsi_calculation(self):
        """RSI 계산 정확성 테스트"""
        result = self.calculator.calculate_indicator("RSI", self.test_data, {"period": 5})
        
        assert result.success is True
        assert len(result.values) == len(self.test_data)
        
        # RSI는 0-100 범위 내에 있어야 함
        for value in result.values:
            assert 0 <= value <= 100
    
    def test_macd_calculation(self):
        """MACD 계산 정확성 테스트"""
        result = self.calculator.calculate_indicator("MACD", self.test_data, 
                                                   {"fast": 5, "slow": 10, "signal": 3})
        
        assert result.success is True
        assert len(result.values) == len(self.test_data)
    
    def test_invalid_indicator(self):
        """지원하지 않는 지표 테스트"""
        result = self.calculator.calculate_indicator("INVALID", self.test_data)
        
        assert result.success is False
        assert "지원하지 않는 지표" in result.error_message
    
    def test_insufficient_data(self):
        """데이터 부족 시 처리 테스트"""
        short_data = [100]
        result = self.calculator.calculate_indicator("SMA", short_data, {"period": 5})
        
        assert result.success is False
        assert "가격 데이터가 부족" in result.error_message

    @pytest.mark.performance
    def test_large_dataset_performance(self):
        """대용량 데이터 성능 테스트"""
        large_data = np.random.randn(10000).tolist()
        
        import time
        start_time = time.time()
        result = self.calculator.calculate_indicator("SMA", large_data, {"period": 20})
        end_time = time.time()
        
        assert result.success is True
        assert end_time - start_time < 1.0  # 1초 이내 완료
```

### **4. 기존 코드와 호환성 테스트 (1시간)**
```python
# tests/integration/test_indicator_compatibility.py
"""
기존 trigger_builder_screen.py와 새로운 calculator 호환성 테스트
"""

import pytest
from upbit_auto_trading.business_logic.triggers.engines.technical_indicator_calculator import TechnicalIndicatorCalculator

class TestIndicatorCompatibility:
    
    def setup_method(self):
        self.new_calculator = TechnicalIndicatorCalculator()
        self.test_data = [100, 105, 102, 108, 110, 107, 112, 109, 115, 118]
    
    def test_sma_compatibility(self):
        """SMA 계산 호환성 검증"""
        # 기존 방식 (trigger_calculator.py)
        from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.shared.trigger_calculator import TriggerCalculator
        legacy_calc = TriggerCalculator()
        legacy_result = legacy_calc.calculate_sma(self.test_data, 5)
        
        # 새로운 방식
        new_result = self.new_calculator.calculate_indicator("SMA", self.test_data, {"period": 5})
        
        # 결과 비교 (소수점 6자리까지)
        for i, (legacy_val, new_val) in enumerate(zip(legacy_result, new_result.values)):
            assert abs(legacy_val - new_val) < 1e-6, f"Index {i}: {legacy_val} != {new_val}"
```

## ✅ **완료 기준**

### **구현 완료 체크리스트**
- [ ] `technical_indicator_calculator.py` 구현 완료
- [ ] 모든 지표 계산 메서드 구현 (SMA, EMA, RSI, MACD)
- [ ] 단위 테스트 90% 이상 커버리지
- [ ] 기존 계산 결과와 100% 호환성 보장
- [ ] 성능 테스트 통과 (10,000개 데이터 1초 이내)

### **품질 기준**
- [ ] PyQt6 의존성 완전 제거
- [ ] 타입 힌트 100% 적용
- [ ] docstring 모든 public 메서드 작성
- [ ] 에러 처리 및 로깅 구현

### **검증 명령어**
```powershell
# 단위 테스트 실행
pytest tests/unit/triggers/test_technical_indicator_calculator.py -v

# 호환성 테스트 실행  
pytest tests/integration/test_indicator_compatibility.py -v

# 커버리지 확인
pytest --cov=upbit_auto_trading.business_logic.triggers.engines tests/unit/triggers/ --cov-report=html
```

## 🔗 **연관 작업**
- **이전**: TASK-20250802-11 (아키텍처 분석 및 설계)
- **다음**: TASK-20250802-13 (트리거 포인트 검출 엔진 구현)
- **관련**: TASK-20250802-15 (UI 어댑터 구현)

## 📊 **예상 소요 시간**
- **총 소요 시간**: 9시간
- **우선순위**: CRITICAL  
- **복잡도**: MEDIUM
- **리스크**: LOW

---
**작성일**: 2025년 8월 2일  
**담당자**: GitHub Copilot  
**문서 타입**: 구현 작업
