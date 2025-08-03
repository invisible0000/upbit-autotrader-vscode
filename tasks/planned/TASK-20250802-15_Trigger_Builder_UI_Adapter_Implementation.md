# 📋 TASK-20250802-15: 트리거 빌더 UI 어댑터 구현

## 🎯 **작업 개요**
새로 구현된 business_logic 서비스들과 기존 trigger_builder_screen.py UI를 연결하는 어댑터를 구현하여 완벽한 호환성을 보장합니다.

## 📊 **현재 상황**

### **완료된 business_logic 서비스들**
```
business_logic/triggers/engines/
├── technical_indicator_calculator.py          # TASK-12 완료
├── trigger_point_detector.py                  # TASK-13 완료
└── cross_signal_analyzer.py                   # TASK-14 완료
```

### **연결해야 할 UI 메서드들**
```python
# trigger_builder_screen.py에서 어댑터로 대체할 메서드들
├── _calculate_variable_data() → TechnicalIndicatorCalculator
├── calculate_trigger_points() → TriggerPointDetector  
├── _calculate_cross_trigger_points() → CrossSignalAnalyzer
├── _calculate_sma() → TechnicalIndicatorCalculator
├── _calculate_ema() → TechnicalIndicatorCalculator
├── _calculate_rsi() → TechnicalIndicatorCalculator
└── _calculate_macd() → TechnicalIndicatorCalculator
```

## 🏗️ **구현 목표**

### **새로운 어댑터 구조**
```
upbit_auto_trading/ui/desktop/adapters/
├── __init__.py
├── trigger_builder_adapter.py                 # 이번 TASK 구현 대상
├── technical_indicator_adapter.py             # 기술 지표 전용 어댑터
└── cross_signal_adapter.py                    # 크로스 신호 전용 어댑터
```

### **TriggerBuilderAdapter 클래스 설계**
```python
class TriggerBuilderAdapter:
    """트리거 빌더 UI와 business_logic 서비스 연결 어댑터"""
    
    def __init__(self):
        """비즈니스 로직 서비스들 초기화"""
        self._indicator_calculator = TechnicalIndicatorCalculator()
        self._trigger_detector = TriggerPointDetector()
        self._cross_analyzer = CrossSignalAnalyzer()
        self._result_formatter = TriggerBuilderResultFormatter()
    
    def calculate_variable_data(self, variable_name: str, price_data: List[float], 
                              custom_parameters: Dict = None) -> List[float]:
        """기존 _calculate_variable_data() 메서드 호환 인터페이스"""
        
    def calculate_trigger_points(self, data: List[float], operator: str, 
                               target_value: float) -> List[int]:
        """기존 calculate_trigger_points() 메서드 호환 인터페이스"""
        
    def calculate_cross_trigger_points(self, base_data: List[float], 
                                     external_data: List[float], 
                                     operator: str) -> List[int]:
        """기존 _calculate_cross_trigger_points() 메서드 호환 인터페이스"""
```

## 📋 **상세 작업 내용**

### **1. 기존 UI 인터페이스 분석 (2시간)**
```powershell
# 기존 trigger_builder_screen.py의 메서드 시그니처 분석
python -c @"
import sys
sys.path.append('.')
import inspect

# trigger_builder_screen.py 분석이 필요하지만 import 에러 방지를 위해
# 예상 시그니처들을 정리
expected_signatures = {
    '_calculate_variable_data': '(variable_name: str, price_data: List[float], custom_parameters: Dict = None) -> List[float]',
    'calculate_trigger_points': '(data: List[float], operator: str, target_value: float) -> List[int]',
    '_calculate_cross_trigger_points': '(base_data: List[float], external_data: List[float], operator: str) -> List[int]',
    '_calculate_sma': '(prices: List[float], period: int) -> List[float]',
    '_calculate_ema': '(prices: List[float], period: int) -> List[float]',
    '_calculate_rsi': '(prices: List[float], period: int = 14) -> List[float]',
    '_calculate_macd': '(prices: List[float]) -> List[float]'
}

for method, signature in expected_signatures.items():
    print(f'{method}: {signature}')
"@
```

### **2. 결과 포매터 구현 (1시간)**
```python
# ui/desktop/adapters/result_formatters.py
"""
비즈니스 로직 결과를 UI 형식으로 변환하는 포매터들
"""

from typing import List, Dict, Any, Optional, Union
import logging
from upbit_auto_trading.business_logic.triggers.models.trigger_detection_models import TriggerDetectionResult
from upbit_auto_trading.business_logic.triggers.models.cross_analysis_models import CrossAnalysisResult

class TriggerBuilderResultFormatter:
    """트리거 빌더 결과 포매터"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def format_indicator_result(self, result, fallback_value: float = 0.0) -> List[float]:
        """
        IndicatorResult를 기존 UI 형식으로 변환
        
        Args:
            result: IndicatorResult 객체
            fallback_value: 실패 시 반환할 기본값
            
        Returns:
            List[float]: UI에서 기대하는 값 리스트
        """
        if hasattr(result, 'success') and result.success:
            return result.values
        else:
            # 실패 시 빈 리스트 또는 기본값으로 채워진 리스트 반환
            self.logger.warning(f"지표 계산 실패: {getattr(result, 'error_message', 'Unknown error')}")
            return []
    
    def format_trigger_detection_result(self, result: TriggerDetectionResult) -> List[int]:
        """
        TriggerDetectionResult를 기존 UI 형식으로 변환
        
        Args:
            result: TriggerDetectionResult 객체
            
        Returns:
            List[int]: 트리거 포인트 인덱스 리스트
        """
        if result.success:
            return [tp.index for tp in result.trigger_points]
        else:
            self.logger.warning(f"트리거 검출 실패: {result.error_message}")
            return []
    
    def format_cross_analysis_result(self, result: CrossAnalysisResult) -> List[int]:
        """
        CrossAnalysisResult를 기존 UI 형식으로 변환
        
        Args:
            result: CrossAnalysisResult 객체
            
        Returns:
            List[int]: 크로스 포인트 인덱스 리스트
        """
        if result.success:
            return [cp.index for cp in result.cross_points]
        else:
            self.logger.warning(f"크로스 분석 실패: {result.error_message}")
            return []
    
    def convert_ui_parameters(self, ui_params: Optional[Dict]) -> Dict[str, Any]:
        """
        UI 파라미터를 business_logic 형식으로 변환
        
        Args:
            ui_params: UI에서 전달받은 파라미터
            
        Returns:
            Dict[str, Any]: business_logic 서비스에서 사용할 파라미터
        """
        if not ui_params:
            return {}
        
        # UI 파라미터 키 매핑
        param_mapping = {
            'period': 'period',
            'fast_period': 'fast',
            'slow_period': 'slow', 
            'signal_period': 'signal',
            'tolerance': 'tolerance_percent',
            'min_strength': 'min_strength'
        }
        
        converted = {}
        for ui_key, value in ui_params.items():
            business_key = param_mapping.get(ui_key, ui_key)
            converted[business_key] = value
        
        return converted
    
    def handle_calculation_error(self, error: Exception, context: str) -> List[float]:
        """
        계산 오류를 UI 친화적으로 처리
        
        Args:
            error: 발생한 예외
            context: 오류 발생 컨텍스트
            
        Returns:
            List[float]: 안전한 기본값
        """
        error_msg = f"{context} 계산 중 오류: {str(error)}"
        self.logger.error(error_msg)
        
        # UI가 크래시되지 않도록 빈 리스트 반환
        return []
```

### **3. trigger_builder_adapter.py 구현 (4시간)**
```python
# ui/desktop/adapters/trigger_builder_adapter.py
"""
트리거 빌더 UI 어댑터
기존 UI와 새로운 business_logic 서비스들을 연결
"""

from typing import List, Dict, Any, Optional, Union
import logging
from .result_formatters import TriggerBuilderResultFormatter

# Business Logic 서비스들 import
from upbit_auto_trading.business_logic.triggers.engines.technical_indicator_calculator import TechnicalIndicatorCalculator
from upbit_auto_trading.business_logic.triggers.engines.trigger_point_detector import TriggerPointDetector
from upbit_auto_trading.business_logic.triggers.engines.cross_signal_analyzer import CrossSignalAnalyzer

class TriggerBuilderAdapter:
    """
    트리거 빌더 UI 어댑터
    기존 trigger_builder_screen.py의 메서드 시그니처를 완벽히 유지하면서
    내부적으로는 새로운 business_logic 서비스를 호출
    """
    
    def __init__(self):
        """서비스 및 포매터 초기화"""
        self.logger = logging.getLogger(__name__)
        
        # Business Logic 서비스들
        self._indicator_calculator = TechnicalIndicatorCalculator()
        self._trigger_detector = TriggerPointDetector()
        self._cross_analyzer = CrossSignalAnalyzer()
        
        # 결과 포매터
        self._formatter = TriggerBuilderResultFormatter()
        
        self.logger.info("TriggerBuilderAdapter 초기화 완료")
    
    def calculate_variable_data(self, variable_name: str, price_data: List[float], 
                              custom_parameters: Optional[Dict] = None) -> List[float]:
        """
        기존 _calculate_variable_data() 메서드 호환 인터페이스
        
        Args:
            variable_name: 변수명 (SMA, EMA, RSI, MACD 등)
            price_data: 가격 데이터
            custom_parameters: 사용자 정의 파라미터
            
        Returns:
            List[float]: 계산된 지표 값들 (기존 형식 유지)
        """
        try:
            self.logger.debug(f"지표 계산 요청: {variable_name}, 데이터 길이: {len(price_data)}")
            
            # UI 파라미터를 business_logic 형식으로 변환
            parameters = self._formatter.convert_ui_parameters(custom_parameters)
            
            # Business Logic 서비스 호출
            result = self._indicator_calculator.calculate_indicator(
                variable_name, price_data, parameters
            )
            
            # UI 형식으로 결과 변환
            formatted_result = self._formatter.format_indicator_result(result)
            
            self.logger.debug(f"지표 계산 완료: {variable_name}, 결과 길이: {len(formatted_result)}")
            return formatted_result
            
        except Exception as e:
            return self._formatter.handle_calculation_error(e, f"지표 계산 ({variable_name})")
    
    def calculate_trigger_points(self, data: List[float], operator: str, 
                               target_value: float) -> List[int]:
        """
        기존 calculate_trigger_points() 메서드 호환 인터페이스
        
        Args:
            data: 분석 대상 데이터
            operator: 비교 연산자 (>, >=, <, <=, ~=, != 등)
            target_value: 비교 대상 값
            
        Returns:
            List[int]: 트리거 포인트 인덱스들 (기존 형식 유지)
        """
        try:
            self.logger.debug(f"트리거 포인트 검출: {operator} {target_value}, 데이터 길이: {len(data)}")
            
            # Business Logic 서비스 호출
            result = self._trigger_detector.detect_trigger_points(
                data, operator, target_value
            )
            
            # UI 형식으로 결과 변환
            formatted_result = self._formatter.format_trigger_detection_result(result)
            
            self.logger.debug(f"트리거 포인트 검출 완료: {len(formatted_result)}개 검출")
            return formatted_result
            
        except Exception as e:
            return self._formatter.handle_calculation_error(e, "트리거 포인트 검출")
    
    def calculate_cross_trigger_points(self, base_data: List[float], 
                                     external_data: List[float], 
                                     operator: str) -> List[int]:
        """
        기존 _calculate_cross_trigger_points() 메서드 호환 인터페이스
        
        Args:
            base_data: 기준선 데이터
            external_data: 비교선 데이터  
            operator: 크로스 연산자 (cross_above, cross_below 등)
            
        Returns:
            List[int]: 크로스 포인트 인덱스들 (기존 형식 유지)
        """
        try:
            self.logger.debug(f"크로스 신호 분석: {operator}, 데이터 길이: {len(base_data)}")
            
            # Business Logic 서비스 호출
            result = self._cross_analyzer.analyze_cross_signals(
                base_data, external_data, operator
            )
            
            # UI 형식으로 결과 변환
            formatted_result = self._formatter.format_cross_analysis_result(result)
            
            self.logger.debug(f"크로스 신호 분석 완료: {len(formatted_result)}개 검출")
            return formatted_result
            
        except Exception as e:
            return self._formatter.handle_calculation_error(e, "크로스 신호 분석")
    
    # 개별 지표 계산 메서드들 (기존 호환성 유지)
    def calculate_sma(self, prices: List[float], period: int) -> List[float]:
        """SMA 계산 (기존 _calculate_sma 호환)"""
        return self.calculate_variable_data("SMA", prices, {"period": period})
    
    def calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """EMA 계산 (기존 _calculate_ema 호환)"""
        return self.calculate_variable_data("EMA", prices, {"period": period})
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """RSI 계산 (기존 _calculate_rsi 호환)"""
        return self.calculate_variable_data("RSI", prices, {"period": period})
    
    def calculate_macd(self, prices: List[float], fast: int = 12, 
                      slow: int = 26, signal: int = 9) -> List[float]:
        """MACD 계산 (기존 _calculate_macd 호환)"""
        return self.calculate_variable_data("MACD", prices, {
            "fast": fast, "slow": slow, "signal": signal
        })
    
    # 고급 기능들 (새로운 business_logic의 추가 기능 활용)
    def get_calculation_metadata(self, variable_name: str, price_data: List[float], 
                               custom_parameters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        계산 메타데이터 제공 (선택적 기능)
        UI에서 필요시 추가 정보를 얻을 수 있음
        """
        try:
            parameters = self._formatter.convert_ui_parameters(custom_parameters)
            result = self._indicator_calculator.calculate_indicator(
                variable_name, price_data, parameters
            )
            
            if hasattr(result, 'success') and result.success:
                return {
                    "indicator_name": result.indicator_name,
                    "parameters": result.parameters,
                    "data_length": len(result.values),
                    "success": True
                }
            else:
                return {
                    "success": False,
                    "error": getattr(result, 'error_message', 'Unknown error')
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_trigger_analysis_summary(self, data: List[float], operator: str, 
                                   target_value: float) -> Dict[str, Any]:
        """
        트리거 분석 요약 정보 제공 (선택적 기능)
        """
        try:
            result = self._trigger_detector.detect_trigger_points(
                data, operator, target_value
            )
            
            if result.success:
                return {
                    "total_triggers": result.total_triggers,
                    "trigger_rate": (result.total_triggers / result.data_length) * 100,
                    "summary": result.detection_summary,
                    "performance_metrics": result.performance_metrics,
                    "success": True
                }
            else:
                return {
                    "success": False,
                    "error": result.error_message
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_cross_analysis_summary(self, base_data: List[float], 
                                 external_data: List[float], 
                                 operator: str) -> Dict[str, Any]:
        """
        크로스 분석 요약 정보 제공 (선택적 기능)
        """
        try:
            result = self._cross_analyzer.analyze_cross_signals(
                base_data, external_data, operator
            )
            
            if result.success:
                return {
                    "total_crosses": result.total_crosses,
                    "signal_strength": result.signal_strength,
                    "reliability_score": result.reliability_score,
                    "summary": result.analysis_summary,
                    "performance_metrics": result.performance_metrics,
                    "success": True
                }
            else:
                return {
                    "success": False,
                    "error": result.error_message
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
```

### **4. trigger_builder_screen.py 수정 (2시간)**
```python
# trigger_builder_screen.py 수정 사항
"""
기존 파일의 계산 메서드들을 어댑터 호출로 대체
"""

# 클래스 초기화 부분에 어댑터 추가
def __init__(self):
    super().__init__()
    
    # 🚀 NEW: 어댑터 초기화
    from upbit_auto_trading.ui.desktop.adapters.trigger_builder_adapter import TriggerBuilderAdapter
    self._adapter = TriggerBuilderAdapter()
    
    # 기존 초기화 코드 유지...

# 계산 메서드들을 어댑터 호출로 대체
def _calculate_variable_data(self, variable_name, price_data, custom_parameters=None):
    """어댑터로 위임 - 기존 시그니처 유지"""
    return self._adapter.calculate_variable_data(variable_name, price_data, custom_parameters)

def calculate_trigger_points(self, data, operator, target_value):
    """어댑터로 위임 - 기존 시그니처 유지"""
    return self._adapter.calculate_trigger_points(data, operator, target_value)

def _calculate_cross_trigger_points(self, base_data, external_data, operator):
    """어댑터로 위임 - 기존 시그니처 유지"""
    return self._adapter.calculate_cross_trigger_points(base_data, external_data, operator)

# 개별 지표 계산 메서드들도 어댑터로 위임
def _calculate_sma(self, prices, period):
    """어댑터로 위임"""
    return self._adapter.calculate_sma(prices, period)

def _calculate_ema(self, prices, period):
    """어댑터로 위임"""
    return self._adapter.calculate_ema(prices, period)

def _calculate_rsi(self, prices, period=14):
    """어댑터로 위임"""
    return self._adapter.calculate_rsi(prices, period)

def _calculate_macd(self, prices):
    """어댑터로 위임"""
    return self._adapter.calculate_macd(prices)
```

### **5. 통합 테스트 구현 (2시간)**
```python
# tests/integration/test_trigger_builder_adapter_integration.py
"""
TriggerBuilderAdapter 통합 테스트
기존 UI와의 완벽한 호환성 검증
"""

import pytest
from upbit_auto_trading.ui.desktop.adapters.trigger_builder_adapter import TriggerBuilderAdapter

class TestTriggerBuilderAdapterIntegration:
    
    def setup_method(self):
        """테스트 설정"""
        self.adapter = TriggerBuilderAdapter()
        self.test_data = [100, 105, 102, 108, 110, 107, 112, 109, 115, 118, 120, 117, 125, 122]
    
    def test_sma_calculation_compatibility(self):
        """SMA 계산 호환성 테스트"""
        # 어댑터를 통한 계산
        result = self.adapter.calculate_variable_data("SMA", self.test_data, {"period": 5})
        
        # 기본 검증
        assert isinstance(result, list)
        assert len(result) == len(self.test_data)
        assert all(isinstance(x, (int, float)) for x in result)
        
        # 직접 SMA 메서드 호출
        direct_result = self.adapter.calculate_sma(self.test_data, 5)
        
        # 결과 동일성 확인
        assert result == direct_result
    
    def test_trigger_point_detection_compatibility(self):
        """트리거 포인트 검출 호환성 테스트"""
        result = self.adapter.calculate_trigger_points(self.test_data, ">", 110)
        
        # 기본 검증
        assert isinstance(result, list)
        assert all(isinstance(x, int) for x in result)
        assert all(0 <= x < len(self.test_data) for x in result)
        
        # 로직 검증: 110 초과 값들의 인덱스가 포함되어야 함
        for idx in result:
            assert self.test_data[idx] > 110
    
    def test_cross_signal_detection_compatibility(self):
        """크로스 신호 검출 호환성 테스트"""
        base_data = [20, 22, 25, 23, 26, 28, 30, 29, 31, 33]
        reference_data = [25] * 10
        
        result = self.adapter.calculate_cross_trigger_points(
            base_data, reference_data, "cross_above"
        )
        
        # 기본 검증
        assert isinstance(result, list)
        assert all(isinstance(x, int) for x in result)
        
        # 로직 검증: 상향 크로스 포인트들 확인
        for idx in result:
            if idx > 0:
                prev_base = base_data[idx-1]
                curr_base = base_data[idx]
                prev_ref = reference_data[idx-1]  
                curr_ref = reference_data[idx]
                
                # 상향 크로스 조건 확인
                assert prev_base <= prev_ref and curr_base > curr_ref
    
    def test_error_handling(self):
        """오류 처리 테스트"""
        # 빈 데이터
        result = self.adapter.calculate_variable_data("SMA", [], {"period": 5})
        assert result == []
        
        # 잘못된 지표명
        result = self.adapter.calculate_variable_data("INVALID", self.test_data)
        assert result == []
        
        # 잘못된 연산자
        result = self.adapter.calculate_trigger_points(self.test_data, "invalid", 100)
        assert result == []
    
    def test_metadata_features(self):
        """메타데이터 기능 테스트"""
        metadata = self.adapter.get_calculation_metadata("SMA", self.test_data, {"period": 5})
        
        assert metadata["success"] is True
        assert metadata["indicator_name"] == "SMA"
        assert metadata["data_length"] == len(self.test_data)
        
        # 트리거 분석 요약
        summary = self.adapter.get_trigger_analysis_summary(self.test_data, ">", 110)
        
        assert summary["success"] is True
        assert "total_triggers" in summary
        assert "trigger_rate" in summary
    
    @pytest.mark.performance
    def test_performance_compatibility(self):
        """성능 호환성 테스트"""
        import time
        large_data = list(range(1000))
        
        # SMA 계산 성능
        start_time = time.time()
        result = self.adapter.calculate_variable_data("SMA", large_data, {"period": 20})
        end_time = time.time()
        
        assert len(result) == len(large_data)
        assert end_time - start_time < 0.5  # 500ms 이내
```

## ✅ **완료 기준**

### **구현 완료 체크리스트**
- [ ] `trigger_builder_adapter.py` 구현 완료
- [ ] `result_formatters.py` 구현 완료  
- [ ] `trigger_builder_screen.py` 수정 완료
- [ ] 모든 기존 메서드 시그니처 100% 호환성 보장
- [ ] 통합 테스트 90% 이상 커버리지

### **호환성 기준**
- [ ] 기존 UI 동작 100% 일치
- [ ] 계산 결과 정확성 보장
- [ ] 에러 처리 안정성 유지
- [ ] 성능 저하 없음 (기존 대비 ±10% 이내)

### **검증 명령어**
```powershell
# 통합 테스트 실행
pytest tests/integration/test_trigger_builder_adapter_integration.py -v

# 전체 UI 동작 검증
python run_desktop_ui.py

# 어댑터 성능 테스트
pytest tests/performance/test_adapter_performance.py --benchmark-only
```

## 🔗 **연관 작업**
- **이전**: TASK-20250802-14 (크로스 신호 분석 엔진 구현)
- **다음**: TASK-20250802-16 (조건 관리 서비스 구현)
- **관련**: TASK-20250802-17 (미니차트 시각화 서비스 구현)

## 📊 **예상 소요 시간**
- **총 소요 시간**: 11시간
- **우선순위**: CRITICAL
- **복잡도**: HIGH (UI 호환성 보장)
- **리스크**: MEDIUM

---
**작성일**: 2025년 8월 2일  
**담당자**: GitHub Copilot  
**문서 타입**: UI 통합 작업
