# 📋 TASK-20250802-14: 크로스 신호 분석 엔진 구현

## 🎯 **작업 개요**
trigger_builder_screen.py의 크로스 신호 감지 로직(_calculate_cross_trigger_points)을 순수 비즈니스 로직으로 분리하여 cross_signal_analyzer.py로 구현합니다.

## 📊 **현재 상황**

### **분리 대상 메서드**
```python
# trigger_builder_screen.py에서 분리할 메서드 (라인 959)
└── _calculate_cross_trigger_points(base_data, external_data, operator)
    ├── cross_above: 기준선이 비교선을 위로 돌파
    ├── cross_below: 기준선이 비교선을 아래로 돌파  
    ├── golden_cross: 단기 이평선이 장기 이평선을 상향 돌파
    └── dead_cross: 단기 이평선이 장기 이평선을 하향 돌파
```

### **크로스 신호 분석 시나리오**
```python
# 현재 지원하는 크로스 패턴들
CROSS_PATTERNS = {
    'cross_above': '기준선이 비교선을 위로 돌파',
    'cross_below': '기준선이 비교선을 아래로 돌파',
    'golden_cross': '골든 크로스 (상향 돌파)',
    'dead_cross': '데드 크로스 (하향 돌파)',
    'divergence_bullish': '강세 다이버전스',
    'divergence_bearish': '약세 다이버전스'
}

# 사용 예시
├── SMA_5 cross_above SMA_20 → 단기 상승 신호
├── RSI cross_below 30 → 과매도 진입 신호
├── MACD cross_above Signal → 매수 신호
└── Price cross_below Bollinger_Lower → 반등 기대 신호
```

## 🏗️ **구현 목표**

### **새로운 파일 구조**
```
business_logic/triggers/engines/
├── technical_indicator_calculator.py          # TASK-12 완료
├── trigger_point_detector.py                  # TASK-13 완료  
└── cross_signal_analyzer.py                   # 이번 TASK 구현 대상
```

### **CrossSignalAnalyzer 클래스 설계**
```python
class CrossSignalAnalyzer:
    """크로스 신호 분석 엔진 - UI 독립적 순수 비즈니스 로직"""
    
    def __init__(self):
        """초기화"""
        self._supported_patterns = {
            'cross_above', 'cross_below', 'golden_cross', 'dead_cross',
            'divergence_bullish', 'divergence_bearish'
        }
    
    def analyze_cross_signals(self, base_data: List[float], reference_data: List[float], 
                            pattern: str, options: Dict[str, Any] = None) -> CrossAnalysisResult:
        """메인 크로스 신호 분석 엔트리포인트"""
        
    def detect_simple_cross(self, base_data: List[float], reference_data: List[float], 
                          direction: str) -> List[CrossPoint]:
        """단순 크로스 패턴 검출"""
        
    def detect_golden_dead_cross(self, short_ma: List[float], long_ma: List[float], 
                               cross_type: str) -> List[CrossPoint]:
        """골든/데드 크로스 검출"""
        
    def detect_divergence(self, price_data: List[float], indicator_data: List[float], 
                        divergence_type: str) -> List[CrossPoint]:
        """다이버전스 패턴 검출"""
```

## 📋 **상세 작업 내용**

### **1. 기존 로직 분석 및 추출 (2시간)**
```powershell
# 기존 크로스 신호 로직 분석
python -c @"
import sys
sys.path.append('.')

# 테스트 데이터 생성 - 명확한 크로스 패턴
base_data = [20, 22, 25, 23, 26, 28, 30, 29, 31, 33]      # 상승 추세
reference_data = [25, 25, 25, 25, 25, 25, 25, 25, 25, 25] # 고정선

print('Base Data:', base_data)
print('Reference Data:', reference_data)

# 크로스 포인트 수동 계산
cross_points = []
for i in range(1, len(base_data)):
    prev_base, curr_base = base_data[i-1], base_data[i]
    prev_ref, curr_ref = reference_data[i-1], reference_data[i]
    
    # cross_above 검출
    if prev_base <= prev_ref and curr_base > curr_ref:
        cross_points.append(('cross_above', i, curr_base, curr_ref))
    # cross_below 검출  
    elif prev_base >= prev_ref and curr_base < curr_ref:
        cross_points.append(('cross_below', i, curr_base, curr_ref))

print('Expected Cross Points:', cross_points)
"@
```

### **2. 모델 클래스 구현 (1시간)**
```python
# business_logic/triggers/models/cross_analysis_models.py
"""
크로스 신호 분석 관련 모델 클래스들
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class CrossPattern(Enum):
    """크로스 패턴 열거형"""
    CROSS_ABOVE = "cross_above"
    CROSS_BELOW = "cross_below"  
    GOLDEN_CROSS = "golden_cross"
    DEAD_CROSS = "dead_cross"
    DIVERGENCE_BULLISH = "divergence_bullish"
    DIVERGENCE_BEARISH = "divergence_bearish"

@dataclass
class CrossPoint:
    """개별 크로스 포인트 정보"""
    index: int                      # 크로스 발생 인덱스
    pattern: str                    # 크로스 패턴명
    base_value: float               # 기준선 값
    reference_value: float          # 비교선 값
    strength: float = 1.0           # 크로스 강도 (0-1)
    duration: int = 1               # 지속 기간
    metadata: Dict[str, Any] = None # 추가 정보

@dataclass
class CrossAnalysisResult:
    """크로스 신호 분석 결과"""
    success: bool
    cross_points: List[CrossPoint]
    total_crosses: int
    pattern: str
    base_data_length: int
    reference_data_length: int
    analysis_summary: str
    signal_strength: float = 0.0    # 전체 신호 강도
    reliability_score: float = 0.0  # 신뢰도 점수
    performance_metrics: Dict[str, float] = None
    error_message: Optional[str] = None

@dataclass  
class DivergencePoint:
    """다이버전스 포인트 정보"""
    start_index: int                # 다이버전스 시작점
    end_index: int                  # 다이버전스 종료점
    price_direction: str            # 가격 방향 (up/down)
    indicator_direction: str        # 지표 방향 (up/down)
    divergence_type: str            # 다이버전스 타입 (bullish/bearish)
    strength: float                 # 다이버전스 강도
```

### **3. cross_signal_analyzer.py 구현 (4시간)**
```python
# business_logic/triggers/engines/cross_signal_analyzer.py
"""
크로스 신호 분석 엔진
UI와 완전히 분리된 순수 비즈니스 로직
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import math
import numpy as np
from ..models.cross_analysis_models import (
    CrossAnalysisResult, CrossPoint, DivergencePoint, CrossPattern
)

class CrossSignalAnalyzer:
    """크로스 신호 분석 엔진"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._pattern_handlers = {
            'cross_above': self._analyze_cross_above,
            'cross_below': self._analyze_cross_below,
            'golden_cross': self._analyze_golden_cross,
            'dead_cross': self._analyze_dead_cross,
            'divergence_bullish': self._analyze_bullish_divergence,
            'divergence_bearish': self._analyze_bearish_divergence
        }
    
    def analyze_cross_signals(self, base_data: List[float], reference_data: List[float], 
                            pattern: str, options: Dict[str, Any] = None) -> CrossAnalysisResult:
        """
        메인 크로스 신호 분석 엔트리포인트
        기존 _calculate_cross_trigger_points() 메서드를 대체
        
        Args:
            base_data: 기준선 데이터 (예: SMA_5)
            reference_data: 비교선 데이터 (예: SMA_20) 
            pattern: 크로스 패턴 ('cross_above', 'cross_below' 등)
            options: 추가 옵션 (min_strength, filter_noise 등)
            
        Returns:
            CrossAnalysisResult: 크로스 분석 결과 및 메타데이터
        """
        # 입력 검증
        if not base_data or not reference_data:
            return CrossAnalysisResult(
                success=False, cross_points=[], total_crosses=0,
                pattern=pattern, base_data_length=len(base_data or []),
                reference_data_length=len(reference_data or []),
                analysis_summary="입력 데이터가 없습니다",
                error_message="base_data 또는 reference_data가 비어있습니다"
            )
        
        if len(base_data) != len(reference_data):
            return CrossAnalysisResult(
                success=False, cross_points=[], total_crosses=0,
                pattern=pattern, base_data_length=len(base_data),
                reference_data_length=len(reference_data),
                analysis_summary="데이터 길이가 다릅니다",
                error_message=f"base_data({len(base_data)})와 reference_data({len(reference_data)}) 길이가 일치하지 않습니다"
            )
        
        if pattern not in self._pattern_handlers:
            return CrossAnalysisResult(
                success=False, cross_points=[], total_crosses=0,
                pattern=pattern, base_data_length=len(base_data),
                reference_data_length=len(reference_data),
                analysis_summary=f"지원하지 않는 패턴: {pattern}",
                error_message=f"패턴 '{pattern}'은 지원되지 않습니다"
            )
        
        # 옵션 기본값 설정
        opts = options or {}
        min_strength = opts.get('min_strength', 0.1)
        filter_noise = opts.get('filter_noise', True)
        
        try:
            # 패턴별 분석 수행
            handler = self._pattern_handlers[pattern]
            cross_points = handler(base_data, reference_data, opts)
            
            # 노이즈 필터링
            if filter_noise:
                cross_points = self._filter_noise_signals(cross_points, min_strength)
            
            # 성능 메트릭 계산
            performance_metrics = self._calculate_cross_metrics(
                cross_points, len(base_data), pattern
            )
            
            # 신호 강도 및 신뢰도 계산
            signal_strength = self._calculate_signal_strength(cross_points)
            reliability_score = self._calculate_reliability_score(
                cross_points, base_data, reference_data, pattern
            )
            
            # 요약 메시지 생성
            summary = self._generate_analysis_summary(
                cross_points, len(base_data), pattern, signal_strength
            )
            
            return CrossAnalysisResult(
                success=True,
                cross_points=cross_points,
                total_crosses=len(cross_points),
                pattern=pattern,
                base_data_length=len(base_data),
                reference_data_length=len(reference_data),
                analysis_summary=summary,
                signal_strength=signal_strength,
                reliability_score=reliability_score,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            self.logger.error(f"크로스 신호 분석 오류: {str(e)}")
            return CrossAnalysisResult(
                success=False, cross_points=[], total_crosses=0,
                pattern=pattern, base_data_length=len(base_data),
                reference_data_length=len(reference_data),
                analysis_summary="분석 중 오류 발생",
                error_message=str(e)
            )
    
    def _analyze_cross_above(self, base_data: List[float], reference_data: List[float], 
                           options: Dict[str, Any]) -> List[CrossPoint]:
        """상향 크로스 분석 (cross_above)"""
        cross_points = []
        
        for i in range(1, len(base_data)):
            prev_base, curr_base = base_data[i-1], base_data[i]
            prev_ref, curr_ref = reference_data[i-1], reference_data[i]
            
            # 상향 크로스 조건: 이전에는 아래, 현재는 위
            if prev_base <= prev_ref and curr_base > curr_ref:
                # 크로스 강도 계산 (돌파 폭에 비례)
                breakthrough_ratio = (curr_base - curr_ref) / max(abs(curr_ref), 1.0)
                strength = min(breakthrough_ratio * 10, 1.0)  # 0-1 정규화
                
                cross_points.append(CrossPoint(
                    index=i,
                    pattern="cross_above",
                    base_value=curr_base,
                    reference_value=curr_ref,
                    strength=strength,
                    metadata={
                        "breakthrough_ratio": breakthrough_ratio,
                        "previous_gap": prev_ref - prev_base
                    }
                ))
        
        return cross_points
    
    def _analyze_cross_below(self, base_data: List[float], reference_data: List[float], 
                           options: Dict[str, Any]) -> List[CrossPoint]:
        """하향 크로스 분석 (cross_below)"""
        cross_points = []
        
        for i in range(1, len(base_data)):
            prev_base, curr_base = base_data[i-1], base_data[i]
            prev_ref, curr_ref = reference_data[i-1], reference_data[i]
            
            # 하향 크로스 조건: 이전에는 위, 현재는 아래
            if prev_base >= prev_ref and curr_base < curr_ref:
                # 크로스 강도 계산
                breakthrough_ratio = (curr_ref - curr_base) / max(abs(curr_ref), 1.0)
                strength = min(breakthrough_ratio * 10, 1.0)
                
                cross_points.append(CrossPoint(
                    index=i,
                    pattern="cross_below",
                    base_value=curr_base,
                    reference_value=curr_ref,
                    strength=strength,
                    metadata={
                        "breakthrough_ratio": breakthrough_ratio,
                        "previous_gap": prev_base - prev_ref
                    }
                ))
        
        return cross_points
    
    def _analyze_golden_cross(self, base_data: List[float], reference_data: List[float], 
                            options: Dict[str, Any]) -> List[CrossPoint]:
        """골든 크로스 분석 (단기선이 장기선을 상향 돌파)"""
        # 기본적으로 cross_above와 동일하지만 추가 검증
        cross_points = self._analyze_cross_above(base_data, reference_data, options)
        
        # 골든 크로스 추가 조건 검증
        min_ma_gap = options.get('min_ma_gap', 0.5)  # 최소 이평선 간격 (%)
        validated_crosses = []
        
        for cp in cross_points:
            # 장기 이평선과 단기 이평선의 간격이 충분한지 확인
            gap_percent = abs(cp.reference_value - cp.base_value) / cp.reference_value * 100
            
            if gap_percent >= min_ma_gap:
                cp.pattern = "golden_cross"
                cp.metadata["ma_gap_percent"] = gap_percent
                validated_crosses.append(cp)
        
        return validated_crosses
    
    def _analyze_dead_cross(self, base_data: List[float], reference_data: List[float], 
                          options: Dict[str, Any]) -> List[CrossPoint]:
        """데드 크로스 분석 (단기선이 장기선을 하향 돌파)"""
        # 기본적으로 cross_below와 동일하지만 추가 검증
        cross_points = self._analyze_cross_below(base_data, reference_data, options)
        
        # 데드 크로스 추가 조건 검증
        min_ma_gap = options.get('min_ma_gap', 0.5)
        validated_crosses = []
        
        for cp in cross_points:
            gap_percent = abs(cp.base_value - cp.reference_value) / cp.reference_value * 100
            
            if gap_percent >= min_ma_gap:
                cp.pattern = "dead_cross"
                cp.metadata["ma_gap_percent"] = gap_percent
                validated_crosses.append(cp)
        
        return validated_crosses
    
    def _analyze_bullish_divergence(self, base_data: List[float], reference_data: List[float], 
                                  options: Dict[str, Any]) -> List[CrossPoint]:
        """강세 다이버전스 분석"""
        # 가격은 하락, 지표는 상승하는 패턴 검출
        window_size = options.get('window_size', 5)
        min_divergence_strength = options.get('min_divergence_strength', 0.3)
        
        divergence_points = []
        
        for i in range(window_size, len(base_data) - window_size):
            # 가격 추세 분석 (하락)
            price_start = base_data[i - window_size]
            price_end = base_data[i + window_size]
            price_trend = (price_end - price_start) / price_start
            
            # 지표 추세 분석 (상승)
            indicator_start = reference_data[i - window_size]
            indicator_end = reference_data[i + window_size]
            indicator_trend = (indicator_end - indicator_start) / indicator_start
            
            # 강세 다이버전스: 가격 하락, 지표 상승
            if price_trend < -0.01 and indicator_trend > 0.01:
                strength = abs(price_trend) + indicator_trend
                
                if strength >= min_divergence_strength:
                    divergence_points.append(CrossPoint(
                        index=i,
                        pattern="divergence_bullish",
                        base_value=base_data[i],
                        reference_value=reference_data[i],
                        strength=min(strength, 1.0),
                        metadata={
                            "price_trend": price_trend,
                            "indicator_trend": indicator_trend,
                            "window_size": window_size
                        }
                    ))
        
        return divergence_points
    
    def _analyze_bearish_divergence(self, base_data: List[float], reference_data: List[float], 
                                  options: Dict[str, Any]) -> List[CrossPoint]:
        """약세 다이버전스 분석"""
        # 가격은 상승, 지표는 하락하는 패턴 검출
        window_size = options.get('window_size', 5)
        min_divergence_strength = options.get('min_divergence_strength', 0.3)
        
        divergence_points = []
        
        for i in range(window_size, len(base_data) - window_size):
            price_start = base_data[i - window_size]
            price_end = base_data[i + window_size]
            price_trend = (price_end - price_start) / price_start
            
            indicator_start = reference_data[i - window_size]
            indicator_end = reference_data[i + window_size]
            indicator_trend = (indicator_end - indicator_start) / indicator_start
            
            # 약세 다이버전스: 가격 상승, 지표 하락
            if price_trend > 0.01 and indicator_trend < -0.01:
                strength = price_trend + abs(indicator_trend)
                
                if strength >= min_divergence_strength:
                    divergence_points.append(CrossPoint(
                        index=i,
                        pattern="divergence_bearish",
                        base_value=base_data[i],
                        reference_value=reference_data[i],
                        strength=min(strength, 1.0),
                        metadata={
                            "price_trend": price_trend,
                            "indicator_trend": indicator_trend,
                            "window_size": window_size
                        }
                    ))
        
        return divergence_points
    
    def _filter_noise_signals(self, cross_points: List[CrossPoint], 
                            min_strength: float) -> List[CrossPoint]:
        """노이즈 신호 필터링"""
        return [cp for cp in cross_points if cp.strength >= min_strength]
    
    def _calculate_signal_strength(self, cross_points: List[CrossPoint]) -> float:
        """전체 신호 강도 계산"""
        if not cross_points:
            return 0.0
        
        return sum(cp.strength for cp in cross_points) / len(cross_points)
    
    def _calculate_reliability_score(self, cross_points: List[CrossPoint], 
                                   base_data: List[float], reference_data: List[float],
                                   pattern: str) -> float:
        """신뢰도 점수 계산"""
        if not cross_points:
            return 0.0
        
        # 기본 신뢰도는 신호 강도 기반
        base_reliability = self._calculate_signal_strength(cross_points)
        
        # 패턴별 추가 신뢰도 요소
        if pattern in ['golden_cross', 'dead_cross']:
            # 이평선 크로스는 데이터 변동성이 낮을수록 신뢰도 높음
            volatility = np.std(base_data) / np.mean(base_data)
            volatility_factor = max(0, 1 - volatility)
            return (base_reliability + volatility_factor) / 2
        
        return base_reliability
    
    def _calculate_cross_metrics(self, cross_points: List[CrossPoint], 
                               data_length: int, pattern: str) -> Dict[str, float]:
        """크로스 분석 성능 메트릭 계산"""
        if not cross_points:
            return {"cross_frequency": 0.0, "avg_strength": 0.0}
        
        cross_frequency = len(cross_points) / data_length * 100
        avg_strength = sum(cp.strength for cp in cross_points) / len(cross_points)
        
        # 패턴별 추가 메트릭
        metrics = {
            "cross_frequency": cross_frequency,
            "avg_strength": avg_strength,
            "total_crosses": len(cross_points),
            "data_coverage": data_length
        }
        
        if pattern in ['divergence_bullish', 'divergence_bearish']:
            # 다이버전스는 지속성 메트릭 추가
            durations = [cp.metadata.get('window_size', 1) for cp in cross_points]
            metrics["avg_duration"] = sum(durations) / len(durations)
        
        return metrics
    
    def _generate_analysis_summary(self, cross_points: List[CrossPoint], 
                                 data_length: int, pattern: str, 
                                 signal_strength: float) -> str:
        """분석 요약 메시지 생성"""
        if not cross_points:
            return f"'{pattern}' 패턴의 크로스 신호가 검출되지 않았습니다"
        
        frequency = len(cross_points) / data_length * 100
        
        return (f"'{pattern}' 패턴 {len(cross_points)}개 검출 "
                f"(빈도: {frequency:.1f}%, 평균 강도: {signal_strength:.2f})")
```

### **4. 단위 테스트 구현 (2시간)**
```python
# tests/unit/triggers/test_cross_signal_analyzer.py
"""
CrossSignalAnalyzer 단위 테스트
"""

import pytest
from upbit_auto_trading.business_logic.triggers.engines.cross_signal_analyzer import CrossSignalAnalyzer

class TestCrossSignalAnalyzer:
    
    def setup_method(self):
        """테스트 설정"""
        self.analyzer = CrossSignalAnalyzer()
        
        # 명확한 크로스 패턴 테스트 데이터
        self.base_data = [20, 22, 25, 23, 26, 28, 30, 29, 31, 33]      # 상승 추세
        self.reference_data = [25, 25, 25, 25, 25, 25, 25, 25, 25, 25] # 고정선 (25)
    
    def test_cross_above_detection(self):
        """상향 크로스 검출 테스트"""
        result = self.analyzer.analyze_cross_signals(
            self.base_data, self.reference_data, "cross_above"
        )
        
        assert result.success is True
        assert result.total_crosses > 0
        
        # 첫 번째 크로스는 인덱스 2에서 발생 (25 돌파)
        first_cross = result.cross_points[0]
        assert first_cross.index == 2
        assert first_cross.pattern == "cross_above"
        assert first_cross.base_value > first_cross.reference_value
    
    def test_cross_below_detection(self):
        """하향 크로스 검출 테스트"""
        # 하향 크로스 테스트 데이터 (하락 후 상승)
        down_data = [30, 28, 26, 24, 22, 20, 23, 26, 29, 31]
        fixed_line = [25] * 10
        
        result = self.analyzer.analyze_cross_signals(
            down_data, fixed_line, "cross_below"
        )
        
        assert result.success is True
        assert result.total_crosses > 0
        
        # 하향 크로스 검증
        for cross in result.cross_points:
            assert cross.pattern == "cross_below"
            assert cross.base_value < cross.reference_value
    
    def test_golden_cross_detection(self):
        """골든 크로스 검출 테스트"""
        # 단기선(5일)이 장기선(20일) 상향 돌파
        short_ma = [95, 98, 102, 105, 108, 110, 112, 115, 118, 120]  # 상승
        long_ma = [100, 100, 100, 105, 105, 105, 110, 110, 110, 115] # 완만한 상승
        
        result = self.analyzer.analyze_cross_signals(
            short_ma, long_ma, "golden_cross"
        )
        
        assert result.success is True
        # 골든 크로스는 추가 검증을 거치므로 모든 상향 크로스가 골든 크로스는 아님
    
    def test_data_length_mismatch(self):
        """데이터 길이 불일치 처리 테스트"""
        short_data = [1, 2, 3]
        long_data = [1, 2, 3, 4, 5]
        
        result = self.analyzer.analyze_cross_signals(
            short_data, long_data, "cross_above"
        )
        
        assert result.success is False
        assert "길이가 일치하지 않습니다" in result.error_message
    
    def test_invalid_pattern(self):
        """지원하지 않는 패턴 테스트"""
        result = self.analyzer.analyze_cross_signals(
            self.base_data, self.reference_data, "invalid_pattern"
        )
        
        assert result.success is False
        assert "지원되지 않습니다" in result.error_message
    
    def test_signal_strength_calculation(self):
        """신호 강도 계산 테스트"""
        result = self.analyzer.analyze_cross_signals(
            self.base_data, self.reference_data, "cross_above"
        )
        
        assert result.success is True
        assert 0 <= result.signal_strength <= 1
        assert 0 <= result.reliability_score <= 1
    
    def test_divergence_detection(self):
        """다이버전스 검출 테스트"""
        # 가격 하락, RSI 상승 패턴 (강세 다이버전스)
        price_data = [100, 95, 90, 85, 80, 75, 70, 68, 66, 65]    # 하락
        rsi_data = [30, 32, 35, 38, 42, 45, 48, 50, 52, 55]       # 상승
        
        result = self.analyzer.analyze_cross_signals(
            price_data, rsi_data, "divergence_bullish", 
            {"window_size": 3, "min_divergence_strength": 0.1}
        )
        
        assert result.success is True
        # 다이버전스는 복잡한 패턴이므로 검출 여부만 확인
```

## ✅ **완료 기준**

### **구현 완료 체크리스트**
- [ ] `cross_signal_analyzer.py` 구현 완료
- [ ] `cross_analysis_models.py` 모델 클래스 구현
- [ ] 모든 크로스 패턴 분석 로직 구현 (cross_above, cross_below, golden_cross, dead_cross, divergence)
- [ ] 신호 강도 및 신뢰도 계산 구현
- [ ] 노이즈 필터링 로직 구현
- [ ] 단위 테스트 90% 이상 커버리지

### **품질 기준**
- [ ] 기존 _calculate_cross_trigger_points() 결과와 100% 호환성
- [ ] PyQt6 의존성 완전 제거
- [ ] 타입 힌트 100% 적용
- [ ] 성능 최적화 (대용량 데이터 처리)

### **검증 명령어**
```powershell
# 단위 테스트 실행
pytest tests/unit/triggers/test_cross_signal_analyzer.py -v

# 호환성 테스트
pytest tests/integration/test_cross_signal_compatibility.py -v
```

## 🔗 **연관 작업**
- **이전**: TASK-20250802-13 (트리거 포인트 검출 엔진 구현)
- **다음**: TASK-20250802-15 (트리거 빌더 UI 어댑터 구현)
- **관련**: TASK-20250802-16 (조건 관리 서비스 구현)

## 📊 **예상 소요 시간**
- **총 소요 시간**: 9시간
- **우선순위**: HIGH
- **복잡도**: MEDIUM-HIGH
- **리스크**: MEDIUM (복잡한 패턴 분석)

---
**작성일**: 2025년 8월 2일  
**담당자**: GitHub Copilot  
**문서 타입**: 구현 작업
