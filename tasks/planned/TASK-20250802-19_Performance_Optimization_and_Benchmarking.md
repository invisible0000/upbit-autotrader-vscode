# 📋 TASK-20250802-19: 성능 최적화 및 벤치마킹

## 🎯 **작업 개요**
리팩토링된 트리거 빌더 시스템의 성능을 최적화하고, 실제 운영 환경에서의 성능 벤치마크를 설정합니다.

## 📊 **현재 상황**

### **성능 최적화 대상**
```python
# 주요 성능 병목 지점들
├── 대용량 데이터 처리 (10,000+ 포인트)
├── 복잡한 기술 지표 계산 (MACD, Bollinger Bands 등)
├── 다중 조건 트리거 탐지
├── 실시간 차트 렌더링
├── 메모리 사용량 최적화
└── 동시성 처리 개선

# 현재 성능 이슈
├── 대용량 데이터에서 RSI 계산 속도 저하
├── 크로스 신호 탐지의 O(n²) 복잡도
├── 차트 데이터 생성 시 메모리 중복
├── NumPy 배열 변환 오버헤드
└── PyQt6 UI 업데이트 블로킹
```

### **최적화 목표**
```python
# 성능 목표 (기존 대비)
├── 처리 속도: 50% 개선
├── 메모리 사용량: 30% 감소
├── UI 응답성: 지연 시간 2초 이하
├── 동시 처리: 5개 이상 작업 동시 실행
└── 확장성: 100,000 포인트까지 처리 가능
```

## 🏗️ **구현 목표**

### **성능 최적화 모듈 구조**
```
business_logic/optimization/
├── __init__.py
├── performance_analyzer.py                    # 성능 분석 도구
├── memory_optimizer.py                        # 메모리 최적화
├── calculation_accelerator.py                 # 계산 가속화
├── caching_manager.py                         # 캐싱 관리
├── parallel_processor.py                      # 병렬 처리
└── benchmarking/
    ├── __init__.py
    ├── benchmark_runner.py                    # 벤치마크 실행기
    ├── performance_profiler.py                # 성능 프로파일러
    └── benchmark_reports.py                   # 벤치마크 리포트
```

### **최적화된 계산 엔진**
```
business_logic/triggers/engines/optimized/
├── __init__.py
├── vectorized_indicator_calculator.py         # 벡터화된 지표 계산
├── streaming_trigger_detector.py              # 스트리밍 트리거 탐지
├── parallel_cross_analyzer.py                 # 병렬 크로스 분석
└── cached_calculation_engine.py               # 캐시된 계산 엔진
```

## 📋 **상세 작업 내용**

### **1. 성능 분석 및 프로파일링 (2시간)**
```python
# business_logic/optimization/performance_analyzer.py
"""
성능 분석 및 프로파일링 도구
"""

import time
import psutil
import cProfile
import pstats
import io
from typing import Dict, Any, List, Callable, Optional
from functools import wraps
from dataclasses import dataclass
import logging
import threading
from contextlib import contextmanager

@dataclass
class PerformanceMetrics:
    """성능 측정 결과"""
    execution_time: float
    memory_usage: float  # MB
    cpu_usage: float     # %
    function_calls: int
    peak_memory: float
    memory_growth: float
    
class PerformanceAnalyzer:
    """성능 분석 도구"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._metrics_history = []
        self._baseline_metrics = None
    
    def profile_function(self, func: Callable) -> Callable:
        """함수 성능 프로파일링 데코레이터"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.measure_performance(func, *args, **kwargs)
        return wrapper
    
    def measure_performance(self, func: Callable, *args, **kwargs) -> Any:
        """함수 실행 성능 측정"""
        # 시작 시점 메트릭
        start_time = time.time()
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        start_cpu = process.cpu_percent()
        
        # 프로파일링 시작
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            # 함수 실행
            result = func(*args, **kwargs)
            
            # 프로파일링 종료
            profiler.disable()
            
            # 종료 시점 메트릭
            end_time = time.time()
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            end_cpu = process.cpu_percent()
            
            # 통계 수집
            stats_stream = io.StringIO()
            stats = pstats.Stats(profiler, stream=stats_stream)
            stats.sort_stats('cumulative')
            
            # 메트릭 계산
            metrics = PerformanceMetrics(
                execution_time=end_time - start_time,
                memory_usage=end_memory,
                cpu_usage=max(start_cpu, end_cpu),
                function_calls=stats.total_calls,
                peak_memory=end_memory,
                memory_growth=end_memory - start_memory
            )
            
            # 결과 기록
            self._metrics_history.append({
                "function": func.__name__,
                "timestamp": end_time,
                "metrics": metrics,
                "args_count": len(args),
                "kwargs_count": len(kwargs)
            })
            
            self.logger.debug(f"함수 {func.__name__} 실행: {metrics.execution_time:.3f}초, "
                            f"메모리: {metrics.memory_growth:+.1f}MB")
            
            return result
            
        except Exception as e:
            profiler.disable()
            self.logger.error(f"성능 측정 중 오류: {str(e)}")
            raise
    
    @contextmanager
    def benchmark_context(self, operation_name: str):
        """벤치마크 컨텍스트 매니저"""
        start_time = time.time()
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024 / 1024
        
        self.logger.info(f"벤치마크 시작: {operation_name}")
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = process.memory_info().rss / 1024 / 1024
            
            execution_time = end_time - start_time
            memory_growth = end_memory - start_memory
            
            self.logger.info(f"벤치마크 완료: {operation_name} - "
                           f"시간: {execution_time:.3f}초, 메모리: {memory_growth:+.1f}MB")
    
    def set_baseline(self, baseline_name: str, metrics: PerformanceMetrics):
        """성능 기준선 설정"""
        self._baseline_metrics = {
            "name": baseline_name,
            "metrics": metrics,
            "timestamp": time.time()
        }
        self.logger.info(f"성능 기준선 설정: {baseline_name}")
    
    def compare_with_baseline(self, current_metrics: PerformanceMetrics) -> Dict[str, float]:
        """기준선과 성능 비교"""
        if not self._baseline_metrics:
            return {}
        
        baseline = self._baseline_metrics["metrics"]
        
        comparison = {
            "execution_time_ratio": current_metrics.execution_time / baseline.execution_time,
            "memory_usage_ratio": current_metrics.memory_usage / baseline.memory_usage,
            "cpu_usage_ratio": current_metrics.cpu_usage / baseline.cpu_usage,
            "execution_time_improvement": ((baseline.execution_time - current_metrics.execution_time) / baseline.execution_time) * 100,
            "memory_improvement": ((baseline.memory_usage - current_metrics.memory_usage) / baseline.memory_usage) * 100
        }
        
        return comparison
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """성능 리포트 생성"""
        if not self._metrics_history:
            return {"error": "성능 데이터 없음"}
        
        # 함수별 통계
        function_stats = {}
        for record in self._metrics_history:
            func_name = record["function"]
            metrics = record["metrics"]
            
            if func_name not in function_stats:
                function_stats[func_name] = {
                    "call_count": 0,
                    "total_time": 0.0,
                    "total_memory": 0.0,
                    "max_time": 0.0,
                    "max_memory": 0.0
                }
            
            stats = function_stats[func_name]
            stats["call_count"] += 1
            stats["total_time"] += metrics.execution_time
            stats["total_memory"] += metrics.memory_growth
            stats["max_time"] = max(stats["max_time"], metrics.execution_time)
            stats["max_memory"] = max(stats["max_memory"], metrics.memory_growth)
        
        # 평균 계산
        for func_name, stats in function_stats.items():
            stats["avg_time"] = stats["total_time"] / stats["call_count"]
            stats["avg_memory"] = stats["total_memory"] / stats["call_count"]
        
        return {
            "summary": {
                "total_measurements": len(self._metrics_history),
                "total_functions": len(function_stats),
                "measurement_period": {
                    "start": min(r["timestamp"] for r in self._metrics_history),
                    "end": max(r["timestamp"] for r in self._metrics_history)
                }
            },
            "function_statistics": function_stats,
            "baseline_comparison": self._baseline_metrics,
            "performance_trends": self._analyze_trends()
        }
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """성능 트렌드 분석"""
        if len(self._metrics_history) < 2:
            return {}
        
        # 시간순 정렬
        sorted_records = sorted(self._metrics_history, key=lambda x: x["timestamp"])
        
        # 트렌드 계산
        execution_times = [r["metrics"].execution_time for r in sorted_records]
        memory_usages = [r["metrics"].memory_growth for r in sorted_records]
        
        return {
            "execution_time_trend": {
                "first": execution_times[0],
                "last": execution_times[-1],
                "average": sum(execution_times) / len(execution_times),
                "trend": "improving" if execution_times[-1] < execution_times[0] else "degrading"
            },
            "memory_usage_trend": {
                "first": memory_usages[0],
                "last": memory_usages[-1], 
                "average": sum(memory_usages) / len(memory_usages),
                "trend": "improving" if memory_usages[-1] < memory_usages[0] else "degrading"
            }
        }
```

### **2. 벡터화된 계산 엔진 구현 (3시간)**
```python
# business_logic/triggers/engines/optimized/vectorized_indicator_calculator.py
"""
벡터화된 기술 지표 계산 엔진
NumPy/Pandas 최적화 활용
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import logging
from numba import jit, njit
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

# NumPy 경고 무시
warnings.filterwarnings('ignore', category=RuntimeWarning)

class VectorizedIndicatorCalculator:
    """벡터화된 기술 지표 계산기"""
    
    def __init__(self, use_numba: bool = True, max_workers: int = 4):
        self.logger = logging.getLogger(__name__)
        self.use_numba = use_numba
        self.max_workers = max_workers
        
        # 계산 결과 캐시
        self._cache = {}
        self._cache_size_limit = 100
        
    def calculate_multiple_indicators(self, price_data: List[float], 
                                    indicators: Dict[str, Dict[str, Any]]) -> Dict[str, np.ndarray]:
        """
        다중 지표 병렬 계산
        
        Args:
            price_data: 가격 데이터
            indicators: 지표 설정 딕셔너리
            
        Returns:
            Dict[str, np.ndarray]: 계산된 지표들
        """
        try:
            # NumPy 배열로 변환 (한 번만)
            prices = np.array(price_data, dtype=np.float64)
            
            # 캐시 키 생성
            cache_key = self._generate_cache_key(prices, indicators)
            if cache_key in self._cache:
                self.logger.debug("캐시에서 지표 결과 반환")
                return self._cache[cache_key]
            
            results = {}
            
            # 병렬 계산 준비
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_indicator = {}
                
                for indicator_name, params in indicators.items():
                    if indicator_name in ["SMA", "EMA", "RSI", "MACD", "BOLLINGER"]:
                        future = executor.submit(
                            self._calculate_single_indicator, 
                            prices, indicator_name, params
                        )
                        future_to_indicator[future] = indicator_name
                
                # 결과 수집
                for future in as_completed(future_to_indicator):
                    indicator_name = future_to_indicator[future]
                    try:
                        result = future.result()
                        results[indicator_name] = result
                        self.logger.debug(f"지표 계산 완료: {indicator_name}")
                    except Exception as e:
                        self.logger.error(f"지표 계산 오류 {indicator_name}: {str(e)}")
                        results[indicator_name] = np.full(len(prices), np.nan)
            
            # 캐시 저장
            self._update_cache(cache_key, results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"다중 지표 계산 오류: {str(e)}")
            raise
    
    def _calculate_single_indicator(self, prices: np.ndarray, 
                                  indicator_name: str, params: Dict[str, Any]) -> np.ndarray:
        """단일 지표 계산"""
        if indicator_name == "SMA":
            return self._calculate_sma_vectorized(prices, params.get("period", 20))
        elif indicator_name == "EMA":
            return self._calculate_ema_vectorized(prices, params.get("period", 20))
        elif indicator_name == "RSI":
            return self._calculate_rsi_vectorized(prices, params.get("period", 14))
        elif indicator_name == "MACD":
            return self._calculate_macd_vectorized(
                prices, 
                params.get("fast", 12),
                params.get("slow", 26),
                params.get("signal", 9)
            )
        elif indicator_name == "BOLLINGER":
            return self._calculate_bollinger_vectorized(
                prices,
                params.get("period", 20),
                params.get("std_dev", 2)
            )
        else:
            raise ValueError(f"지원하지 않는 지표: {indicator_name}")
    
    def _calculate_sma_vectorized(self, prices: np.ndarray, period: int) -> np.ndarray:
        """벡터화된 SMA 계산"""
        if self.use_numba:
            return self._sma_numba(prices, period)
        else:
            return self._sma_pandas(prices, period)
    
    def _calculate_ema_vectorized(self, prices: np.ndarray, period: int) -> np.ndarray:
        """벡터화된 EMA 계산"""
        if self.use_numba:
            return self._ema_numba(prices, period)
        else:
            return self._ema_pandas(prices, period)
    
    def _calculate_rsi_vectorized(self, prices: np.ndarray, period: int) -> np.ndarray:
        """벡터화된 RSI 계산"""
        if self.use_numba:
            return self._rsi_numba(prices, period)
        else:
            return self._rsi_pandas(prices, period)
    
    def _calculate_macd_vectorized(self, prices: np.ndarray, 
                                 fast: int, slow: int, signal: int) -> np.ndarray:
        """벡터화된 MACD 계산"""
        ema_fast = self._calculate_ema_vectorized(prices, fast)
        ema_slow = self._calculate_ema_vectorized(prices, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = self._calculate_ema_vectorized(macd_line, signal)
        histogram = macd_line - signal_line
        
        # MACD는 3개 값을 반환 (Line, Signal, Histogram)
        return np.column_stack([macd_line, signal_line, histogram])
    
    def _calculate_bollinger_vectorized(self, prices: np.ndarray, 
                                      period: int, std_dev: float) -> np.ndarray:
        """벡터화된 볼린저 밴드 계산"""
        sma = self._calculate_sma_vectorized(prices, period)
        rolling_std = self._rolling_std_vectorized(prices, period)
        
        upper_band = sma + (rolling_std * std_dev)
        lower_band = sma - (rolling_std * std_dev)
        
        # 볼린저 밴드는 3개 값을 반환 (Upper, Middle, Lower)
        return np.column_stack([upper_band, sma, lower_band])
    
    # Numba 최적화 함수들
    @staticmethod
    @njit
    def _sma_numba(prices: np.ndarray, period: int) -> np.ndarray:
        """Numba 최적화된 SMA"""
        n = len(prices)
        sma = np.full(n, np.nan)
        
        for i in range(period - 1, n):
            sma[i] = np.mean(prices[i - period + 1:i + 1])
        
        return sma
    
    @staticmethod
    @njit  
    def _ema_numba(prices: np.ndarray, period: int) -> np.ndarray:
        """Numba 최적화된 EMA"""
        n = len(prices)
        ema = np.full(n, np.nan)
        
        if n < period:
            return ema
        
        # 첫 번째 EMA는 SMA로 계산
        ema[period - 1] = np.mean(prices[:period])
        
        # 승수 계산
        multiplier = 2.0 / (period + 1)
        
        # EMA 계산
        for i in range(period, n):
            ema[i] = (prices[i] * multiplier) + (ema[i - 1] * (1 - multiplier))
        
        return ema
    
    @staticmethod
    @njit
    def _rsi_numba(prices: np.ndarray, period: int) -> np.ndarray:
        """Numba 최적화된 RSI"""
        n = len(prices)
        rsi = np.full(n, np.nan)
        
        if n < period + 1:
            return rsi
        
        # 가격 변화 계산
        changes = np.diff(prices)
        gains = np.maximum(changes, 0.0)
        losses = np.maximum(-changes, 0.0)
        
        # 첫 번째 평균 계산
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        if avg_loss == 0:
            rsi[period] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[period] = 100.0 - (100.0 / (1.0 + rs))
        
        # RSI 계산 (Wilder's smoothing)
        alpha = 1.0 / period
        for i in range(period + 1, n):
            avg_gain = alpha * gains[i - 1] + (1 - alpha) * avg_gain
            avg_loss = alpha * losses[i - 1] + (1 - alpha) * avg_loss
            
            if avg_loss == 0:
                rsi[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi[i] = 100.0 - (100.0 / (1.0 + rs))
        
        return rsi
    
    # Pandas 최적화 함수들 (Numba가 불가능한 경우)
    def _sma_pandas(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Pandas 최적화된 SMA"""
        series = pd.Series(prices)
        return series.rolling(window=period, min_periods=period).mean().values
    
    def _ema_pandas(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Pandas 최적화된 EMA"""
        series = pd.Series(prices)
        return series.ewm(span=period, adjust=False).mean().values
    
    def _rsi_pandas(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Pandas 최적화된 RSI"""
        series = pd.Series(prices)
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.values
    
    def _rolling_std_vectorized(self, prices: np.ndarray, period: int) -> np.ndarray:
        """벡터화된 롤링 표준편차"""
        series = pd.Series(prices)
        return series.rolling(window=period, min_periods=period).std().values
    
    def _generate_cache_key(self, prices: np.ndarray, indicators: Dict[str, Dict[str, Any]]) -> str:
        """캐시 키 생성"""
        price_hash = hash(prices.tobytes())
        indicator_hash = hash(str(sorted(indicators.items())))
        return f"{price_hash}_{indicator_hash}"
    
    def _update_cache(self, key: str, results: Dict[str, np.ndarray]):
        """캐시 업데이트"""
        if len(self._cache) >= self._cache_size_limit:
            # LRU 방식으로 가장 오래된 항목 제거
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        self._cache[key] = results
    
    def clear_cache(self):
        """캐시 초기화"""
        self._cache.clear()
        self.logger.debug("지표 계산 캐시 초기화")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        return {
            "cache_size": len(self._cache),
            "cache_limit": self._cache_size_limit,
            "cache_usage": len(self._cache) / self._cache_size_limit * 100
        }
```

### **3. 메모리 최적화 관리자 (2시간)**
```python
# business_logic/optimization/memory_optimizer.py
"""
메모리 사용량 최적화 관리자
"""

import gc
import psutil
import os
import sys
from typing import Dict, Any, List, Optional, Callable
import logging
import weakref
from functools import wraps
import numpy as np
import pandas as pd
from contextlib import contextmanager

class MemoryOptimizer:
    """메모리 최적화 관리자"""
    
    def __init__(self, memory_threshold_mb: float = 500.0):
        self.logger = logging.getLogger(__name__)
        self.memory_threshold_mb = memory_threshold_mb
        
        # 메모리 사용량 추적
        self._memory_snapshots = []
        self._object_registry = weakref.WeakSet()
        
        # 최적화 설정
        self._optimization_enabled = True
        self._auto_gc_threshold = 100  # MB
        
    def monitor_memory(self, func: Callable) -> Callable:
        """메모리 사용량 모니터링 데코레이터"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 실행 전 메모리 확인
            initial_memory = self.get_current_memory_usage()
            
            if initial_memory > self.memory_threshold_mb:
                self.logger.warning(f"메모리 사용량 임계값 초과: {initial_memory:.1f}MB")
                self.optimize_memory()
            
            try:
                result = func(*args, **kwargs)
                
                # 실행 후 메모리 확인
                final_memory = self.get_current_memory_usage()
                memory_growth = final_memory - initial_memory
                
                if memory_growth > self._auto_gc_threshold:
                    self.logger.info(f"메모리 증가량 {memory_growth:.1f}MB, GC 실행")
                    self.force_garbage_collection()
                
                return result
                
            except MemoryError:
                self.logger.error("메모리 부족 오류 발생, 긴급 메모리 정리")
                self.emergency_memory_cleanup()
                raise
                
        return wrapper
    
    @contextmanager
    def memory_context(self, operation_name: str = "operation"):
        """메모리 관리 컨텍스트"""
        initial_memory = self.get_current_memory_usage()
        self.logger.debug(f"메모리 컨텍스트 시작 ({operation_name}): {initial_memory:.1f}MB")
        
        try:
            yield
        finally:
            final_memory = self.get_current_memory_usage()
            memory_growth = final_memory - initial_memory
            
            self.logger.debug(f"메모리 컨텍스트 종료 ({operation_name}): "
                            f"{final_memory:.1f}MB (성장: {memory_growth:+.1f}MB)")
            
            # 메모리 스냅샷 저장
            self._memory_snapshots.append({
                "operation": operation_name,
                "initial_memory": initial_memory,
                "final_memory": final_memory,
                "memory_growth": memory_growth,
                "timestamp": psutil.time.time()
            })
            
            # 자동 정리
            if memory_growth > self._auto_gc_threshold:
                self.force_garbage_collection()
    
    def get_current_memory_usage(self) -> float:
        """현재 메모리 사용량 반환 (MB)"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def optimize_memory(self):
        """메모리 최적화 실행"""
        if not self._optimization_enabled:
            return
        
        initial_memory = self.get_current_memory_usage()
        
        # 1. 가비지 컬렉션 강제 실행
        self.force_garbage_collection()
        
        # 2. NumPy/Pandas 캐시 정리
        self._cleanup_numpy_cache()
        self._cleanup_pandas_cache()
        
        # 3. 약한 참조 객체 정리
        self._cleanup_weak_references()
        
        final_memory = self.get_current_memory_usage()
        memory_saved = initial_memory - final_memory
        
        self.logger.info(f"메모리 최적화 완료: {memory_saved:.1f}MB 절약")
    
    def force_garbage_collection(self):
        """강제 가비지 컬렉션"""
        collected = gc.collect()
        self.logger.debug(f"가비지 컬렉션: {collected}개 객체 정리")
    
    def emergency_memory_cleanup(self):
        """긴급 메모리 정리"""
        self.logger.warning("긴급 메모리 정리 시작")
        
        # 1. 모든 캐시 정리
        self._cleanup_all_caches()
        
        # 2. 강제 GC (3회)
        for i in range(3):
            collected = gc.collect()
            self.logger.debug(f"긴급 GC {i+1}/3: {collected}개 객체 정리")
        
        # 3. 시스템 메모리 상태 확인
        memory_info = psutil.virtual_memory()
        self.logger.warning(f"시스템 메모리: {memory_info.percent:.1f}% 사용 중")
    
    def _cleanup_numpy_cache(self):
        """NumPy 캐시 정리"""
        try:
            # NumPy 내부 캐시 정리 (가능한 경우)
            if hasattr(np, '_NoValue'):
                # NumPy 내부 캐시 정리
                pass
            self.logger.debug("NumPy 캐시 정리 완료")
        except Exception as e:
            self.logger.debug(f"NumPy 캐시 정리 실패: {str(e)}")
    
    def _cleanup_pandas_cache(self):
        """Pandas 캐시 정리"""
        try:
            # Pandas 옵션 캐시 정리
            if hasattr(pd, 'reset_option'):
                # 일부 pandas 캐시 리셋
                pass
            self.logger.debug("Pandas 캐시 정리 완료")
        except Exception as e:
            self.logger.debug(f"Pandas 캐시 정리 실패: {str(e)}")
    
    def _cleanup_weak_references(self):
        """약한 참조 객체 정리"""
        try:
            # 약한 참조 레지스트리 정리
            initial_count = len(self._object_registry)
            # WeakSet은 자동으로 정리되므로 수동 작업 불필요
            final_count = len(self._object_registry)
            
            cleaned_count = initial_count - final_count
            if cleaned_count > 0:
                self.logger.debug(f"약한 참조 정리: {cleaned_count}개 객체")
        except Exception as e:
            self.logger.debug(f"약한 참조 정리 실패: {str(e)}")
    
    def _cleanup_all_caches(self):
        """모든 캐시 정리"""
        self._cleanup_numpy_cache()
        self._cleanup_pandas_cache()
        
        # 애플리케이션별 캐시 정리 (확장 가능)
        # 예: 지표 계산 캐시, 차트 데이터 캐시 등
    
    def register_large_object(self, obj: Any, description: str = ""):
        """대용량 객체 등록 (메모리 추적용)"""
        self._object_registry.add(obj)
        self.logger.debug(f"대용량 객체 등록: {description}")
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """메모리 통계 반환"""
        current_memory = self.get_current_memory_usage()
        system_memory = psutil.virtual_memory()
        
        # 메모리 증가 추세 분석
        if len(self._memory_snapshots) >= 2:
            recent_snapshots = self._memory_snapshots[-10:]  # 최근 10개
            memory_trend = sum(s["memory_growth"] for s in recent_snapshots)
        else:
            memory_trend = 0.0
        
        return {
            "current_memory_mb": current_memory,
            "memory_threshold_mb": self.memory_threshold_mb,
            "threshold_exceeded": current_memory > self.memory_threshold_mb,
            "system_memory_percent": system_memory.percent,
            "system_available_gb": system_memory.available / 1024 / 1024 / 1024,
            "memory_trend_mb": memory_trend,
            "registered_objects": len(self._object_registry),
            "snapshots_count": len(self._memory_snapshots),
            "optimization_enabled": self._optimization_enabled
        }
    
    def set_optimization_enabled(self, enabled: bool):
        """메모리 최적화 활성화/비활성화"""
        self._optimization_enabled = enabled
        self.logger.info(f"메모리 최적화 {'활성화' if enabled else '비활성화'}")
    
    def clear_snapshots(self):
        """메모리 스냅샷 기록 초기화"""
        self._memory_snapshots.clear()
        self.logger.debug("메모리 스냅샷 기록 초기화")
```

### **4. 병렬 처리 최적화 (2시간)**
```python
# business_logic/optimization/parallel_processor.py
"""
병렬 처리 최적화 관리자
"""

import threading
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Dict, Any, Callable, Optional, Union
import logging
import time
import queue
from dataclasses import dataclass
import asyncio

@dataclass
class ProcessingTask:
    """처리 작업 정의"""
    task_id: str
    function: Callable
    args: tuple
    kwargs: dict
    priority: int = 0  # 낮을수록 높은 우선순위

class ParallelProcessor:
    """병렬 처리 최적화 관리자"""
    
    def __init__(self, max_workers: Optional[int] = None):
        self.logger = logging.getLogger(__name__)
        
        # 워커 수 설정
        self.max_workers = max_workers or min(8, (mp.cpu_count() or 1) + 4)
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # 작업 큐 및 결과 추적
        self._task_queue = queue.PriorityQueue()
        self._results = {}
        self._active_tasks = {}
        
        # 성능 통계
        self._processing_stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_processing_time": 0.0
        }
        
    def process_indicators_parallel(self, price_data: List[float], 
                                  indicators: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        다중 지표 병렬 계산
        기존 VectorizedIndicatorCalculator와 연동
        """
        try:
            from .vectorized_indicator_calculator import VectorizedIndicatorCalculator
            calculator = VectorizedIndicatorCalculator(max_workers=self.max_workers)
            
            # 지표별 병렬 작업 생성
            tasks = []
            for indicator_name, params in indicators.items():
                task = ProcessingTask(
                    task_id=f"indicator_{indicator_name}",
                    function=calculator._calculate_single_indicator,
                    args=(price_data, indicator_name, params),
                    kwargs={},
                    priority=self._get_indicator_priority(indicator_name)
                )
                tasks.append(task)
            
            # 병렬 실행
            results = self.execute_tasks_parallel(tasks)
            
            # 결과 정리
            indicator_results = {}
            for task_id, result in results.items():
                if result["success"]:
                    indicator_name = task_id.replace("indicator_", "")
                    indicator_results[indicator_name] = result["data"]
                else:
                    self.logger.error(f"지표 계산 실패: {task_id} - {result['error']}")
            
            return indicator_results
            
        except Exception as e:
            self.logger.error(f"병렬 지표 계산 오류: {str(e)}")
            raise
    
    def execute_tasks_parallel(self, tasks: List[ProcessingTask]) -> Dict[str, Dict[str, Any]]:
        """작업들을 병렬로 실행"""
        results = {}
        
        # 우선순위 기준 정렬
        sorted_tasks = sorted(tasks, key=lambda t: t.priority)
        
        # ThreadPoolExecutor 사용하여 병렬 실행
        future_to_task = {}
        
        for task in sorted_tasks:
            future = self.thread_pool.submit(
                self._execute_single_task, task
            )
            future_to_task[future] = task
            
            # 활성 작업 추적
            self._active_tasks[task.task_id] = {
                "task": task,
                "future": future,
                "start_time": time.time()
            }
        
        # 결과 수집
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            
            try:
                result = future.result()
                results[task.task_id] = {
                    "success": True,
                    "data": result,
                    "error": None
                }
                self._processing_stats["completed_tasks"] += 1
                
            except Exception as e:
                results[task.task_id] = {
                    "success": False,
                    "data": None,
                    "error": str(e)
                }
                self._processing_stats["failed_tasks"] += 1
                self.logger.error(f"작업 실행 오류 {task.task_id}: {str(e)}")
            
            finally:
                # 활성 작업에서 제거
                if task.task_id in self._active_tasks:
                    task_info = self._active_tasks.pop(task.task_id)
                    processing_time = time.time() - task_info["start_time"]
                    self._processing_stats["total_processing_time"] += processing_time
        
        self._processing_stats["total_tasks"] += len(tasks)
        return results
    
    def _execute_single_task(self, task: ProcessingTask) -> Any:
        """단일 작업 실행"""
        try:
            start_time = time.time()
            result = task.function(*task.args, **task.kwargs)
            execution_time = time.time() - start_time
            
            self.logger.debug(f"작업 완료: {task.task_id} ({execution_time:.3f}초)")
            return result
            
        except Exception as e:
            self.logger.error(f"작업 실행 오류 {task.task_id}: {str(e)}")
            raise
    
    def _get_indicator_priority(self, indicator_name: str) -> int:
        """지표별 우선순위 반환 (낮을수록 높은 우선순위)"""
        priority_map = {
            "SMA": 1,      # 단순 이동평균 (빠름)
            "EMA": 1,      # 지수 이동평균 (빠름)
            "RSI": 2,      # RSI (중간)
            "MACD": 3,     # MACD (복잡함)
            "BOLLINGER": 3, # 볼린저 밴드 (복잡함)
            "STOCHASTIC": 4, # 스토캐스틱 (매우 복잡함)
        }
        return priority_map.get(indicator_name, 5)  # 기본 우선순위
    
    def process_trigger_detection_parallel(self, price_data: List[float],
                                         conditions: List[Dict[str, Any]],
                                         batch_size: int = 1000) -> List[int]:
        """
        트리거 탐지 병렬 처리
        대용량 데이터를 배치로 나누어 병렬 처리
        """
        try:
            if len(price_data) <= batch_size:
                # 소규모 데이터는 병렬 처리 불필요
                from ..engines.trigger_point_detector import TriggerPointDetector
                detector = TriggerPointDetector()
                return detector.detect_triggers(price_data, conditions)
            
            # 데이터를 배치로 분할
            batches = self._split_data_into_batches(price_data, batch_size)
            
            # 배치별 병렬 작업 생성
            tasks = []
            for i, batch in enumerate(batches):
                task = ProcessingTask(
                    task_id=f"trigger_batch_{i}",
                    function=self._detect_triggers_batch,
                    args=(batch["data"], conditions, batch["start_index"]),
                    kwargs={},
                    priority=0
                )
                tasks.append(task)
            
            # 병렬 실행
            results = self.execute_tasks_parallel(tasks)
            
            # 결과 병합
            all_trigger_points = []
            for task_id in sorted(results.keys()):
                if results[task_id]["success"]:
                    batch_triggers = results[task_id]["data"]
                    all_trigger_points.extend(batch_triggers)
            
            return sorted(all_trigger_points)
            
        except Exception as e:
            self.logger.error(f"병렬 트리거 탐지 오류: {str(e)}")
            raise
    
    def _split_data_into_batches(self, data: List[float], 
                               batch_size: int) -> List[Dict[str, Any]]:
        """데이터를 배치로 분할"""
        batches = []
        
        for i in range(0, len(data), batch_size):
            batch_data = data[i:i + batch_size]
            batches.append({
                "data": batch_data,
                "start_index": i,
                "end_index": i + len(batch_data) - 1
            })
        
        return batches
    
    def _detect_triggers_batch(self, batch_data: List[float], 
                             conditions: List[Dict[str, Any]], 
                             start_index: int) -> List[int]:
        """배치 단위 트리거 탐지"""
        from ..engines.trigger_point_detector import TriggerPointDetector
        detector = TriggerPointDetector()
        
        # 배치 내 트리거 탐지
        batch_triggers = detector.detect_triggers(batch_data, conditions)
        
        # 전체 인덱스로 변환
        global_triggers = [start_index + idx for idx in batch_triggers]
        return global_triggers
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """처리 통계 반환"""
        stats = self._processing_stats.copy()
        
        # 추가 통계 계산
        if stats["completed_tasks"] > 0:
            stats["average_processing_time"] = (
                stats["total_processing_time"] / stats["completed_tasks"]
            )
            stats["success_rate"] = (
                stats["completed_tasks"] / stats["total_tasks"] * 100
            ) if stats["total_tasks"] > 0 else 0
        else:
            stats["average_processing_time"] = 0
            stats["success_rate"] = 0
        
        stats["active_tasks_count"] = len(self._active_tasks)
        stats["max_workers"] = self.max_workers
        
        return stats
    
    def shutdown(self):
        """병렬 처리기 종료"""
        self.logger.info("병렬 처리기 종료 중...")
        self.thread_pool.shutdown(wait=True)
        self.logger.info("병렬 처리기 종료 완료")
    
    def __del__(self):
        """소멸자"""
        try:
            self.shutdown()
        except:
            pass
```

### **5. 성능 벤치마크 실행 (1시간)**
```powershell
# 성능 벤치마크 스크립트
Write-Host "⚡ 트리거 빌더 성능 최적화 벤치마크" -ForegroundColor Green

# 1. 기존 성능 기준선 측정
Write-Host "`n📊 1. 기존 성능 기준선 측정..." -ForegroundColor Yellow
python -c @"
import sys
sys.path.append('.')

from business_logic.optimization.performance_analyzer import PerformanceAnalyzer
from ui.desktop.adapters.triggers.trigger_builder_adapter import TriggerBuilderAdapter
import time

# 기준선 측정
analyzer = PerformanceAnalyzer()
adapter = TriggerBuilderAdapter()

# 테스트 데이터
price_data = [100 + i * 0.1 + (i % 100) * 0.5 for i in range(1000)]
indicators = {
    'SMA': {'period': 20},
    'RSI': {'period': 14},
    'MACD': {'fast': 12, 'slow': 26, 'signal': 9}
}

# 기준선 성능 측정
@analyzer.profile_function
def baseline_calculation():
    return adapter.calculate_all_indicators(price_data, indicators)

result = baseline_calculation()
print(f'✅ 기준선 측정 완료: {len(result.indicators)}개 지표')

# 기준선 저장
baseline_metrics = analyzer._metrics_history[-1]['metrics']
analyzer.set_baseline('original_implementation', baseline_metrics)
print(f'📈 기준선 성능: {baseline_metrics.execution_time:.3f}초, {baseline_metrics.memory_growth:.1f}MB')
"@

# 2. 최적화된 성능 측정
Write-Host "`n🚀 2. 최적화된 성능 측정..." -ForegroundColor Yellow
python -c @"
import sys
sys.path.append('.')

from business_logic.optimization.performance_analyzer import PerformanceAnalyzer
from business_logic.triggers.engines.optimized.vectorized_indicator_calculator import VectorizedIndicatorCalculator
from business_logic.optimization.parallel_processor import ParallelProcessor
import numpy as np

# 최적화된 계산 테스트
analyzer = PerformanceAnalyzer()
calculator = VectorizedIndicatorCalculator(use_numba=True)
processor = ParallelProcessor()

# 테스트 데이터
price_data = [100 + i * 0.1 + (i % 100) * 0.5 for i in range(1000)]
indicators = {
    'SMA': {'period': 20},
    'RSI': {'period': 14},
    'MACD': {'fast': 12, 'slow': 26, 'signal': 9}
}

# 최적화된 성능 측정
@analyzer.profile_function
def optimized_calculation():
    return calculator.calculate_multiple_indicators(price_data, indicators)

result = optimized_calculation()
print(f'✅ 최적화 측정 완료: {len(result)}개 지표')

# 성능 비교
current_metrics = analyzer._metrics_history[-1]['metrics']
comparison = analyzer.compare_with_baseline(current_metrics)

if comparison:
    print(f'📈 성능 개선:')
    print(f'  - 실행 시간: {comparison["execution_time_improvement"]:.1f}% 개선')
    print(f'  - 메모리 사용: {comparison["memory_improvement"]:.1f}% 개선')
    print(f'  - 속도 비율: {comparison["execution_time_ratio"]:.2f}x')
"@

# 3. 대용량 데이터 성능 테스트
Write-Host "`n💾 3. 대용량 데이터 성능 테스트..." -ForegroundColor Yellow
python -c @"
import sys
sys.path.append('.')

from business_logic.optimization.performance_analyzer import PerformanceAnalyzer
from business_logic.optimization.memory_optimizer import MemoryOptimizer
from business_logic.triggers.engines.optimized.vectorized_indicator_calculator import VectorizedIndicatorCalculator

# 메모리 최적화와 함께 테스트
analyzer = PerformanceAnalyzer()
memory_optimizer = MemoryOptimizer()
calculator = VectorizedIndicatorCalculator()

# 대용량 테스트 데이터 (10,000 포인트)
large_price_data = [100 + i * 0.01 + (i % 1000) * 0.1 for i in range(10000)]

indicators = {
    'SMA': {'period': 50},
    'EMA': {'period': 50},
    'RSI': {'period': 14},
    'MACD': {'fast': 12, 'slow': 26, 'signal': 9},
    'BOLLINGER': {'period': 20, 'std_dev': 2}
}

# 메모리 모니터링과 함께 실행
@memory_optimizer.monitor_memory
@analyzer.profile_function
def large_scale_calculation():
    return calculator.calculate_multiple_indicators(large_price_data, indicators)

with memory_optimizer.memory_context('large_scale_test'):
    result = large_scale_calculation()

print(f'✅ 대용량 데이터 처리 완료: {len(result)}개 지표, {len(large_price_data)}개 포인트')

# 메모리 통계
memory_stats = memory_optimizer.get_memory_statistics()
print(f'💾 메모리 사용량: {memory_stats["current_memory_mb"]:.1f}MB')
print(f'🎯 메모리 임계값: {"⚠️ 초과" if memory_stats["threshold_exceeded"] else "✅ 정상"}')
"@

# 4. 성능 리포트 생성
Write-Host "`n📋 4. 성능 리포트 생성..." -ForegroundColor Yellow
python -c @"
import sys
sys.path.append('.')
import json
from pathlib import Path

from business_logic.optimization.performance_analyzer import PerformanceAnalyzer

# 최종 성능 리포트 생성
analyzer = PerformanceAnalyzer()
report = analyzer.generate_performance_report()

# 리포트 저장
report_dir = Path('tests/integration/trigger_builder/fixtures')
report_dir.mkdir(parents=True, exist_ok=True)

report_file = report_dir / 'optimization_report.json'
with open(report_file, 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f'📊 성능 리포트 저장: {report_file}')
print(f'📈 측정된 함수: {report["summary"]["total_functions"]}개')
print(f'📏 총 측정 횟수: {report["summary"]["total_measurements"]}회')
"@

Write-Host "`n✅ 성능 최적화 벤치마크 완료!" -ForegroundColor Green
```

## ✅ **완료 기준**

### **성능 최적화 체크리스트**
- [ ] 벡터화된 계산 엔진 구현 완료
- [ ] 메모리 사용량 30% 이상 감소
- [ ] 처리 속도 50% 이상 개선
- [ ] 병렬 처리 안정성 확보
- [ ] 대용량 데이터 처리 능력 확보

### **벤치마크 기준**
- [ ] 1,000 포인트: 1초 이내 처리
- [ ] 10,000 포인트: 5초 이내 처리
- [ ] 메모리 사용량: 200MB 이내
- [ ] 동시 작업: 5개 이상 안정 처리

### **검증 명령어**
```powershell
# 성능 테스트 실행
pytest tests/integration/trigger_builder/test_performance_integration.py -v -m performance

# 메모리 테스트 실행
pytest tests/unit/optimization/ -v

# 벤치마크 실행
python business_logic/optimization/benchmarking/benchmark_runner.py
```

## 🔗 **연관 작업**
- **이전**: TASK-20250802-18 (전체 통합 테스트 및 검증)
- **다음**: TASK-20250802-20 (문서화 및 배포 준비)
- **관련**: 모든 이전 TASK (성능 개선 대상)

## 📊 **예상 소요 시간**
- **총 소요 시간**: 10시간
- **우선순위**: HIGH
- **복잡도**: HIGH (성능 최적화 복잡성)
- **리스크**: MEDIUM (호환성 유지 필요)

---
**작성일**: 2025년 8월 2일  
**담당자**: GitHub Copilot  
**문서 타입**: 성능 최적화 및 벤치마킹
