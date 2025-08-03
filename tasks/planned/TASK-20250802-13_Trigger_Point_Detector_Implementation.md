# 📋 TASK-20250802-13: 트리거 포인트 검출 엔진 구현

## 🎯 **작업 개요**
trigger_builder_screen.py의 트리거 포인트 감지 로직을 순수 비즈니스 로직으로 분리하여 trigger_point_detector.py로 구현합니다.

## 📊 **현재 상황**

### **분리 대상 메서드**
```python
# trigger_builder_screen.py에서 분리할 메서드들
├── calculate_trigger_points() (라인 1146) → 메인 트리거 포인트 감지
└── _calculate_cross_trigger_points() (라인 959) → 크로스 신호 감지

# components/shared/trigger_calculator.py에서 통합할 메서드들  
└── calculate_trigger_points() → 기존 구현 개선
```

### **트리거 포인트 감지 로직 분석**
```python
# 현재 지원하는 연산자들
SUPPORTED_OPERATORS = ['>', '>=', '<', '<=', '~=', '!=', 'cross_above', 'cross_below']

# 감지 시나리오
├── 고정값 비교: RSI > 70, SMA < 현재가
├── 변수간 비교: SMA_5 cross_above SMA_20  
├── 근사값 비교: 현재가 ~= 이전고점 (±1%)
└── 추세 감지: 연속 상승/하락 패턴
```

## 🏗️ **구현 목표**

### **새로운 파일 구조**
```
business_logic/triggers/engines/
├── technical_indicator_calculator.py          # 이전 TASK 완료
├── trigger_point_detector.py                  # 이번 TASK 구현 대상
└── cross_signal_analyzer.py                   # 다음 TASK
```

### **TriggerPointDetector 클래스 설계**
```python
class TriggerPointDetector:
    """트리거 포인트 검출 엔진 - UI 독립적 순수 비즈니스 로직"""
    
    def __init__(self):
        """초기화"""
        self._supported_operators = {
            '>', '>=', '<', '<=', '~=', '!=', 'trend_up', 'trend_down'
        }
    
    def detect_trigger_points(self, variable_data: List[float], operator: str, 
                            target_value: Union[float, List[float]], 
                            options: Dict[str, Any] = None) -> TriggerDetectionResult:
        """메인 트리거 포인트 검출 엔트리포인트"""
        
    def detect_fixed_value_triggers(self, data: List[float], operator: str, 
                                  target: float) -> List[int]:
        """고정값 대비 트리거 포인트 검출"""
        
    def detect_trend_triggers(self, data: List[float], direction: str, 
                            min_duration: int = 3) -> List[int]:
        """추세 기반 트리거 포인트 검출"""
        
    def detect_approximate_triggers(self, data: List[float], target: float, 
                                  tolerance_percent: float = 1.0) -> List[int]:
        """근사값 트리거 포인트 검출"""
```

## 📋 **상세 작업 내용**

### **1. 기존 로직 분석 및 추출 (2시간)**
```powershell
# 기존 트리거 감지 로직 분석
python -c @"
import sys
sys.path.append('.')

# 기존 TriggerCalculator 분석
from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.shared.trigger_calculator import TriggerCalculator

calc = TriggerCalculator()
test_data = [45, 50, 55, 48, 52, 58, 62, 59, 65, 70, 68, 72]

# 다양한 연산자 테스트
operators = ['>', '>=', '<', '<=']
for op in operators:
    result = calc.calculate_trigger_points(test_data, op, 60)
    print(f'{op} 60: {result}')
"@
```

### **2. 모델 클래스 구현 (1시간)**
```python
# business_logic/triggers/models/trigger_detection_models.py
"""
트리거 검출 관련 모델 클래스들
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

class TriggerOperator(Enum):
    """트리거 연산자 열거형"""
    GREATER_THAN = ">"
    GREATER_EQUAL = ">="
    LESS_THAN = "<"
    LESS_EQUAL = "<="
    APPROXIMATELY_EQUAL = "~="
    NOT_EQUAL = "!="
    TREND_UP = "trend_up"
    TREND_DOWN = "trend_down"

@dataclass
class TriggerPoint:
    """개별 트리거 포인트 정보"""
    index: int                      # 데이터 인덱스
    value: float                    # 해당 시점의 값
    target_value: float             # 비교 대상 값
    operator: str                   # 사용된 연산자
    confidence: float = 1.0         # 신뢰도 (0-1)
    metadata: Dict[str, Any] = None # 추가 정보

@dataclass  
class TriggerDetectionResult:
    """트리거 검출 결과"""
    success: bool
    trigger_points: List[TriggerPoint]
    total_triggers: int
    data_length: int
    operator: str
    target_value: Union[float, List[float]]
    detection_summary: str
    performance_metrics: Dict[str, float] = None
    error_message: Optional[str] = None
```

### **3. trigger_point_detector.py 구현 (4시간)**
```python
# business_logic/triggers/engines/trigger_point_detector.py
"""
트리거 포인트 검출 엔진
UI와 완전히 분리된 순수 비즈니스 로직
"""

from typing import List, Dict, Any, Optional, Union
import logging
import math
from ..models.trigger_detection_models import (
    TriggerDetectionResult, TriggerPoint, TriggerOperator
)

class TriggerPointDetector:
    """트리거 포인트 검출 엔진"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._operator_handlers = {
            '>': self._detect_greater_than,
            '>=': self._detect_greater_equal,
            '<': self._detect_less_than,
            '<=': self._detect_less_equal,
            '~=': self._detect_approximately_equal,
            '!=': self._detect_not_equal,
            'trend_up': self._detect_trend_up,
            'trend_down': self._detect_trend_down
        }
    
    def detect_trigger_points(self, variable_data: List[float], operator: str, 
                            target_value: Union[float, List[float]], 
                            options: Dict[str, Any] = None) -> TriggerDetectionResult:
        """
        메인 트리거 포인트 검출 엔트리포인트
        기존 calculate_trigger_points() 메서드를 대체
        
        Args:
            variable_data: 분석할 변수 데이터 (가격, RSI, SMA 등)
            operator: 비교 연산자
            target_value: 비교 대상 값(들)
            options: 추가 옵션 (tolerance, min_duration 등)
            
        Returns:
            TriggerDetectionResult: 검출 결과 및 메타데이터
        """
        # 입력 검증
        if not variable_data or len(variable_data) == 0:
            return TriggerDetectionResult(
                success=False, trigger_points=[], total_triggers=0,
                data_length=0, operator=operator, target_value=target_value,
                detection_summary="입력 데이터가 없습니다",
                error_message="변수 데이터가 비어있습니다"
            )
        
        if operator not in self._operator_handlers:
            return TriggerDetectionResult(
                success=False, trigger_points=[], total_triggers=0,
                data_length=len(variable_data), operator=operator, 
                target_value=target_value,
                detection_summary=f"지원하지 않는 연산자: {operator}",
                error_message=f"연산자 '{operator}'는 지원되지 않습니다"
            )
        
        # 옵션 기본값 설정
        opts = options or {}
        
        try:
            # 연산자별 검출 수행
            handler = self._operator_handlers[operator]
            trigger_points = handler(variable_data, target_value, opts)
            
            # 성능 메트릭 계산
            performance_metrics = self._calculate_performance_metrics(
                variable_data, trigger_points, operator, target_value
            )
            
            # 요약 메시지 생성
            summary = self._generate_detection_summary(
                trigger_points, len(variable_data), operator, target_value
            )
            
            return TriggerDetectionResult(
                success=True,
                trigger_points=trigger_points,
                total_triggers=len(trigger_points),
                data_length=len(variable_data),
                operator=operator,
                target_value=target_value,
                detection_summary=summary,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            self.logger.error(f"트리거 검출 오류: {str(e)}")
            return TriggerDetectionResult(
                success=False, trigger_points=[], total_triggers=0,
                data_length=len(variable_data), operator=operator,
                target_value=target_value,
                detection_summary="검출 중 오류 발생",
                error_message=str(e)
            )
    
    def _detect_greater_than(self, data: List[float], target: float, 
                           options: Dict[str, Any]) -> List[TriggerPoint]:
        """큰 값 트리거 검출 (>)"""
        triggers = []
        for i, value in enumerate(data):
            if value > target:
                triggers.append(TriggerPoint(
                    index=i, value=value, target_value=target,
                    operator=">", confidence=1.0
                ))
        return triggers
    
    def _detect_greater_equal(self, data: List[float], target: float, 
                            options: Dict[str, Any]) -> List[TriggerPoint]:
        """크거나 같은 값 트리거 검출 (>=)"""
        triggers = []
        for i, value in enumerate(data):
            if value >= target:
                triggers.append(TriggerPoint(
                    index=i, value=value, target_value=target,
                    operator=">=", confidence=1.0
                ))
        return triggers
    
    def _detect_less_than(self, data: List[float], target: float, 
                        options: Dict[str, Any]) -> List[TriggerPoint]:
        """작은 값 트리거 검출 (<)"""
        triggers = []
        for i, value in enumerate(data):
            if value < target:
                triggers.append(TriggerPoint(
                    index=i, value=value, target_value=target,
                    operator="<", confidence=1.0
                ))
        return triggers
    
    def _detect_less_equal(self, data: List[float], target: float, 
                         options: Dict[str, Any]) -> List[TriggerPoint]:
        """작거나 같은 값 트리거 검출 (<=)"""
        triggers = []
        for i, value in enumerate(data):
            if value <= target:
                triggers.append(TriggerPoint(
                    index=i, value=value, target_value=target,
                    operator="<=", confidence=1.0
                ))
        return triggers
    
    def _detect_approximately_equal(self, data: List[float], target: float, 
                                  options: Dict[str, Any]) -> List[TriggerPoint]:
        """근사값 트리거 검출 (~=)"""
        tolerance_percent = options.get('tolerance_percent', 1.0)
        triggers = []
        
        for i, value in enumerate(data):
            if target != 0:
                diff_percent = abs(value - target) / abs(target) * 100
                if diff_percent <= tolerance_percent:
                    confidence = 1.0 - (diff_percent / tolerance_percent) * 0.5
                    triggers.append(TriggerPoint(
                        index=i, value=value, target_value=target,
                        operator="~=", confidence=confidence,
                        metadata={"diff_percent": diff_percent}
                    ))
        return triggers
    
    def _detect_not_equal(self, data: List[float], target: float, 
                        options: Dict[str, Any]) -> List[TriggerPoint]:
        """같지 않은 값 트리거 검출 (!=)"""
        epsilon = options.get('epsilon', 1e-6)
        triggers = []
        
        for i, value in enumerate(data):
            if abs(value - target) > epsilon:
                triggers.append(TriggerPoint(
                    index=i, value=value, target_value=target,
                    operator="!=", confidence=1.0
                ))
        return triggers
    
    def _detect_trend_up(self, data: List[float], target: float, 
                       options: Dict[str, Any]) -> List[TriggerPoint]:
        """상승 추세 트리거 검출"""
        min_duration = options.get('min_duration', 3)
        min_change_percent = options.get('min_change_percent', 0.5)
        triggers = []
        
        for i in range(min_duration, len(data)):
            # 연속 상승 확인
            is_uptrend = True
            start_value = data[i - min_duration]
            
            for j in range(i - min_duration + 1, i + 1):
                if data[j] <= data[j - 1]:
                    is_uptrend = False
                    break
            
            if is_uptrend:
                change_percent = ((data[i] - start_value) / start_value) * 100
                if change_percent >= min_change_percent:
                    confidence = min(change_percent / (min_change_percent * 2), 1.0)
                    triggers.append(TriggerPoint(
                        index=i, value=data[i], target_value=target,
                        operator="trend_up", confidence=confidence,
                        metadata={"change_percent": change_percent, "duration": min_duration}
                    ))
        
        return triggers
    
    def _detect_trend_down(self, data: List[float], target: float, 
                         options: Dict[str, Any]) -> List[TriggerPoint]:
        """하락 추세 트리거 검출"""
        min_duration = options.get('min_duration', 3)
        min_change_percent = options.get('min_change_percent', 0.5)
        triggers = []
        
        for i in range(min_duration, len(data)):
            # 연속 하락 확인
            is_downtrend = True
            start_value = data[i - min_duration]
            
            for j in range(i - min_duration + 1, i + 1):
                if data[j] >= data[j - 1]:
                    is_downtrend = False
                    break
            
            if is_downtrend:
                change_percent = ((start_value - data[i]) / start_value) * 100
                if change_percent >= min_change_percent:
                    confidence = min(change_percent / (min_change_percent * 2), 1.0)
                    triggers.append(TriggerPoint(
                        index=i, value=data[i], target_value=target,
                        operator="trend_down", confidence=confidence,
                        metadata={"change_percent": change_percent, "duration": min_duration}
                    ))
        
        return triggers
    
    def _calculate_performance_metrics(self, data: List[float], 
                                     triggers: List[TriggerPoint],
                                     operator: str, target: float) -> Dict[str, float]:
        """성능 메트릭 계산"""
        if not triggers:
            return {"trigger_rate": 0.0, "avg_confidence": 0.0}
        
        trigger_rate = len(triggers) / len(data) * 100
        avg_confidence = sum(t.confidence for t in triggers) / len(triggers)
        
        return {
            "trigger_rate": trigger_rate,
            "avg_confidence": avg_confidence,
            "total_triggers": len(triggers),
            "data_coverage": len(data)
        }
    
    def _generate_detection_summary(self, triggers: List[TriggerPoint], 
                                  data_length: int, operator: str, 
                                  target: Union[float, List[float]]) -> str:
        """검출 요약 메시지 생성"""
        if not triggers:
            return f"조건 '{operator} {target}'을 만족하는 트리거 포인트가 없습니다"
        
        trigger_rate = len(triggers) / data_length * 100
        avg_confidence = sum(t.confidence for t in triggers) / len(triggers)
        
        return (f"총 {len(triggers)}개 트리거 포인트 검출 "
                f"(발생률: {trigger_rate:.1f}%, 평균 신뢰도: {avg_confidence:.2f})")
```

### **4. 단위 테스트 구현 (2시간)**
```python
# tests/unit/triggers/test_trigger_point_detector.py
"""
TriggerPointDetector 단위 테스트
"""

import pytest
from upbit_auto_trading.business_logic.triggers.engines.trigger_point_detector import TriggerPointDetector
from upbit_auto_trading.business_logic.triggers.models.trigger_detection_models import TriggerDetectionResult

class TestTriggerPointDetector:
    
    def setup_method(self):
        """테스트 설정"""
        self.detector = TriggerPointDetector()
        self.test_data = [45, 50, 55, 48, 52, 58, 62, 59, 65, 70, 68, 72, 75, 73]
    
    def test_greater_than_detection(self):
        """> 연산자 트리거 검출 테스트"""
        result = self.detector.detect_trigger_points(self.test_data, ">", 60)
        
        assert result.success is True
        assert result.total_triggers > 0
        assert all(tp.value > 60 for tp in result.trigger_points)
        
        # 예상 트리거 포인트 확인
        expected_indices = [6, 8, 9, 11, 12]  # 62, 65, 70, 72, 75
        actual_indices = [tp.index for tp in result.trigger_points]
        assert actual_indices == expected_indices
    
    def test_less_than_detection(self):
        """< 연산자 트리거 검출 테스트"""
        result = self.detector.detect_trigger_points(self.test_data, "<", 55)
        
        assert result.success is True
        assert all(tp.value < 55 for tp in result.trigger_points)
    
    def test_approximately_equal_detection(self):
        """~= 연산자 트리거 검출 테스트"""
        result = self.detector.detect_trigger_points(
            self.test_data, "~=", 50, {"tolerance_percent": 2.0}
        )
        
        assert result.success is True
        # 50 ± 2% = 49-51 범위의 값들 검출
        for tp in result.trigger_points:
            assert 49 <= tp.value <= 51
    
    def test_trend_up_detection(self):
        """상승 추세 트리거 검출 테스트"""
        # 명확한 상승 추세 데이터
        uptrend_data = [100, 102, 105, 108, 110, 95, 97, 100, 103, 107]
        result = self.detector.detect_trigger_points(
            uptrend_data, "trend_up", 0, {"min_duration": 3, "min_change_percent": 1.0}
        )
        
        assert result.success is True
        # 상승 추세 구간에서 트리거 검출되어야 함
    
    def test_invalid_operator(self):
        """지원하지 않는 연산자 테스트"""
        result = self.detector.detect_trigger_points(self.test_data, "invalid", 50)
        
        assert result.success is False
        assert "지원하지 않는 연산자" in result.error_message
    
    def test_empty_data(self):
        """빈 데이터 처리 테스트"""
        result = self.detector.detect_trigger_points([], ">", 50)
        
        assert result.success is False
        assert "비어있습니다" in result.error_message
    
    def test_performance_metrics(self):
        """성능 메트릭 계산 테스트"""
        result = self.detector.detect_trigger_points(self.test_data, ">", 60)
        
        assert result.performance_metrics is not None
        assert "trigger_rate" in result.performance_metrics
        assert "avg_confidence" in result.performance_metrics
        assert 0 <= result.performance_metrics["trigger_rate"] <= 100
        assert 0 <= result.performance_metrics["avg_confidence"] <= 1
```

## ✅ **완료 기준**

### **구현 완료 체크리스트**
- [ ] `trigger_point_detector.py` 구현 완료
- [ ] `trigger_detection_models.py` 모델 클래스 구현
- [ ] 모든 연산자 검출 로직 구현 (>, >=, <, <=, ~=, !=, trend_up, trend_down)
- [ ] 단위 테스트 90% 이상 커버리지
- [ ] 성능 메트릭 및 신뢰도 계산 구현

### **품질 기준**
- [ ] 기존 calculate_trigger_points() 결과와 100% 호환성
- [ ] PyQt6 의존성 완전 제거  
- [ ] 타입 힌트 100% 적용
- [ ] 에러 처리 및 로깅 구현

### **검증 명령어**
```powershell
# 단위 테스트 실행
pytest tests/unit/triggers/test_trigger_point_detector.py -v

# 호환성 테스트 (기존 로직과 비교)
pytest tests/integration/test_trigger_detection_compatibility.py -v
```

## 🔗 **연관 작업**
- **이전**: TASK-20250802-12 (기술 지표 계산 엔진 구현)
- **다음**: TASK-20250802-14 (크로스 신호 분석 엔진 구현)
- **관련**: TASK-20250802-15 (UI 어댑터 구현)

## 📊 **예상 소요 시간**
- **총 소요 시간**: 9시간
- **우선순위**: CRITICAL
- **복잡도**: MEDIUM-HIGH
- **리스크**: LOW

---
**작성일**: 2025년 8월 2일  
**담당자**: GitHub Copilot  
**문서 타입**: 구현 작업
