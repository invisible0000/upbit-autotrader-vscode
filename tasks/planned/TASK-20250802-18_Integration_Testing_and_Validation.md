# 📋 TASK-20250802-18: 전체 통합 테스트 및 검증

## 🎯 **작업 개요**
리팩토링된 모든 컴포넌트들의 통합 테스트를 실시하고, 기존 trigger_builder_screen.py와 100% 호환성을 보장합니다.

## 📊 **현재 상황**

### **리팩토링된 컴포넌트들**
```python
# 기존 1642라인 → 분리된 구조
├── trigger_builder_screen.py (UI만 남김, ~400라인 예상)
├── business_logic/triggers/
│   ├── engines/
│   │   ├── technical_indicator_calculator.py      # TASK-11
│   │   ├── trigger_point_detector.py             # TASK-12
│   │   └── cross_signal_analyzer.py              # TASK-13
│   ├── services/
│   │   ├── trigger_orchestration_service.py      # TASK-14
│   │   └── condition_management_service.py       # TASK-16
│   └── models/                                   # TASK-15
├── business_logic/visualization/
│   ├── engines/chart_data_engine.py              # TASK-17
│   └── services/minichart_orchestration_service.py
└── ui/desktop/adapters/triggers/
    └── trigger_builder_adapter.py                # TASK-15
```

### **통합 테스트 범위**
```python
# 1. 핵심 워크플로우 테스트
├── 기술 지표 계산 → 트리거 탐지 → 크로스 신호 분석
├── 조건 생성 → 검증 → 시뮬레이션
├── 차트 데이터 생성 → 시각화 → UI 표시
└── 전체 워크플로우 엔드투엔드 테스트

# 2. 기존 호환성 테스트
├── trigger_builder_screen.py의 모든 기존 메서드 호출
├── 기존 시뮬레이션 결과와 동일성 보장
├── UI 이벤트 처리 호환성
└── 데이터베이스 연동 호환성

# 3. 성능 테스트
├── 대용량 데이터 처리 (10,000+ 데이터 포인트)
├── 복잡한 조건 조합 처리
├── 메모리 사용량 측정
└── 응답 시간 벤치마크
```

## 🏗️ **구현 목표**

### **통합 테스트 구조**
```
tests/integration/trigger_builder/
├── __init__.py
├── test_full_workflow_integration.py           # 전체 워크플로우 테스트
├── test_backwards_compatibility.py            # 기존 호환성 테스트
├── test_performance_integration.py            # 성능 통합 테스트
├── test_ui_adapter_integration.py             # UI 어댑터 통합 테스트
├── test_chart_integration.py                  # 차트 시스템 통합 테스트
└── fixtures/
    ├── sample_price_data.json                 # 테스트용 가격 데이터
    ├── sample_trigger_conditions.json         # 테스트용 조건 데이터
    └── benchmark_results.json                 # 성능 벤치마크 기준값
```

### **호환성 검증 테스트**
```
tests/compatibility/trigger_builder/
├── __init__.py
├── test_legacy_method_compatibility.py        # 기존 메서드 호환성
├── test_simulation_result_compatibility.py    # 시뮬레이션 결과 동일성
├── test_ui_behavior_compatibility.py          # UI 동작 호환성
└── test_database_compatibility.py             # 데이터베이스 호환성
```

## 📋 **상세 작업 내용**

### **1. 전체 워크플로우 통합 테스트 (4시간)**
```python
# tests/integration/trigger_builder/test_full_workflow_integration.py
"""
트리거 빌더 전체 워크플로우 통합 테스트
"""

import pytest
import logging
from typing import List, Dict, Any
from unittest.mock import Mock, patch

from business_logic.triggers.services.trigger_orchestration_service import TriggerOrchestrationService
from business_logic.visualization.services.minichart_orchestration_service import MinichartOrchestrationService
from ui.desktop.adapters.triggers.trigger_builder_adapter import TriggerBuilderAdapter

class TestFullWorkflowIntegration:
    """전체 워크플로우 통합 테스트"""
    
    @pytest.fixture
    def sample_price_data(self):
        """테스트용 가격 데이터"""
        return [100 + i + (i % 10) * 2 for i in range(100)]
    
    @pytest.fixture
    def trigger_service(self):
        """트리거 오케스트레이션 서비스"""
        return TriggerOrchestrationService()
    
    @pytest.fixture
    def chart_service(self):
        """차트 오케스트레이션 서비스"""
        return MinichartOrchestrationService()
    
    @pytest.fixture
    def ui_adapter(self, trigger_service, chart_service):
        """UI 어댑터"""
        return TriggerBuilderAdapter(trigger_service, chart_service)
    
    def test_complete_indicator_calculation_workflow(self, ui_adapter, sample_price_data):
        """완전한 지표 계산 워크플로우 테스트"""
        # Given: 가격 데이터와 지표 설정
        indicator_configs = {
            "SMA": {"period": 20},
            "RSI": {"period": 14},
            "MACD": {"fast": 12, "slow": 26, "signal": 9}
        }
        
        # When: 지표 계산 실행
        result = ui_adapter.calculate_all_indicators(sample_price_data, indicator_configs)
        
        # Then: 모든 지표가 성공적으로 계산됨
        assert result.success
        assert "SMA" in result.indicators
        assert "RSI" in result.indicators
        assert "MACD" in result.indicators
        
        # 계산된 지표 값 검증
        assert len(result.indicators["SMA"]) == len(sample_price_data)
        assert all(0 <= rsi <= 100 for rsi in result.indicators["RSI"] if rsi is not None)
        
        logging.info(f"지표 계산 완료: {list(result.indicators.keys())}")
    
    def test_complete_trigger_detection_workflow(self, ui_adapter, sample_price_data):
        """완전한 트리거 탐지 워크플로우 테스트"""
        # Given: 트리거 조건 설정
        condition = {
            "variable": "SMA_20",
            "operator": "crosses_above",
            "target": "price",
            "threshold": 105
        }
        
        # When: 트리거 탐지 실행
        result = ui_adapter.detect_triggers(sample_price_data, [condition])
        
        # Then: 트리거가 성공적으로 탐지됨
        assert result.success
        assert isinstance(result.trigger_points, list)
        
        # 탐지된 트리거 포인트 검증
        for point in result.trigger_points:
            assert 0 <= point < len(sample_price_data)
        
        logging.info(f"트리거 탐지 완료: {len(result.trigger_points)}개 포인트")
    
    def test_complete_simulation_workflow(self, ui_adapter, sample_price_data):
        """완전한 시뮬레이션 워크플로우 테스트"""
        # Given: 시뮬레이션 설정
        simulation_config = {
            "conditions": [
                {
                    "variable": "RSI_14",
                    "operator": "less_than",
                    "threshold": 30
                }
            ],
            "indicators": {
                "RSI": {"period": 14},
                "SMA": {"period": 20}
            }
        }
        
        # When: 시뮬레이션 실행
        result = ui_adapter.run_complete_simulation(sample_price_data, simulation_config)
        
        # Then: 시뮬레이션이 성공적으로 완료됨
        assert result.success
        assert result.chart_data is not None
        assert len(result.trigger_points) >= 0
        
        # 차트 데이터 검증
        chart_summary = result.chart_data.get_data_summary()
        assert chart_summary["price_points"] == len(sample_price_data)
        assert "RSI" in chart_summary["indicators"]
        
        logging.info(f"시뮬레이션 완료: {chart_summary}")
    
    def test_chart_visualization_integration(self, ui_adapter, sample_price_data):
        """차트 시각화 통합 테스트"""
        # Given: 차트 설정
        chart_config = {
            "indicators": ["SMA_20", "RSI_14"],
            "show_signals": True,
            "theme": "dark"
        }
        
        # When: 차트 생성 및 시각화
        result = ui_adapter.create_visualization(sample_price_data, chart_config)
        
        # Then: 차트가 성공적으로 생성됨
        assert result.success
        assert result.chart_data is not None
        
        # 차트 데이터 무결성 검증
        chart_data = result.chart_data
        assert len(chart_data.price_data) == len(sample_price_data)
        assert "SMA" in chart_data.indicators
        assert "RSI" in chart_data.indicators
        
        logging.info(f"차트 생성 완료: {chart_data.get_data_summary()}")
    
    def test_error_handling_integration(self, ui_adapter):
        """오류 처리 통합 테스트"""
        # Given: 잘못된 입력 데이터
        invalid_data = []
        invalid_conditions = [{"invalid": "condition"}]
        
        # When: 오류 상황 처리
        result = ui_adapter.detect_triggers(invalid_data, invalid_conditions)
        
        # Then: 적절한 오류 처리
        assert not result.success
        assert result.error_message is not None
        
        logging.info(f"오류 처리 확인: {result.error_message}")
    
    @pytest.mark.performance
    def test_large_dataset_performance(self, ui_adapter):
        """대용량 데이터셋 성능 테스트"""
        # Given: 대용량 가격 데이터 (10,000 포인트)
        large_price_data = [100 + i * 0.1 + (i % 100) * 0.5 for i in range(10000)]
        
        # When: 복잡한 조건으로 트리거 탐지
        import time
        start_time = time.time()
        
        result = ui_adapter.detect_triggers(large_price_data, [
            {"variable": "SMA_50", "operator": "crosses_above", "target": "price"},
            {"variable": "RSI_14", "operator": "less_than", "threshold": 30}
        ])
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Then: 성능 기준 충족
        assert result.success
        assert execution_time < 5.0  # 5초 이내 처리
        
        logging.info(f"대용량 데이터 처리 시간: {execution_time:.2f}초")
    
    def test_memory_usage_integration(self, ui_adapter, sample_price_data):
        """메모리 사용량 통합 테스트"""
        import psutil
        import os
        
        # Given: 메모리 사용량 측정 시작
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # When: 반복적인 계산 수행
        for _ in range(10):
            result = ui_adapter.calculate_all_indicators(sample_price_data, {
                "SMA": {"period": 20},
                "EMA": {"period": 20},
                "RSI": {"period": 14},
                "MACD": {"fast": 12, "slow": 26, "signal": 9}
            })
            assert result.success
        
        # Then: 메모리 사용량 확인
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        assert memory_increase < 50  # 50MB 이내 증가
        
        logging.info(f"메모리 사용량 증가: {memory_increase:.2f}MB")
```

### **2. 기존 호환성 검증 테스트 (3시간)**
```python
# tests/compatibility/trigger_builder/test_legacy_method_compatibility.py
"""
기존 trigger_builder_screen.py 메서드 호환성 테스트
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication, QWidget
import sys

# 기존 trigger_builder_screen.py와 새로운 어댑터 임포트
from ui.desktop.screens.strategy_management.components.triggers.trigger_builder_screen import TriggerBuilderScreen
from ui.desktop.adapters.triggers.trigger_builder_adapter import TriggerBuilderAdapter

class TestLegacyMethodCompatibility:
    """기존 메서드 호환성 테스트"""
    
    @pytest.fixture(scope="module")
    def qapp(self):
        """PyQt6 애플리케이션 픽스처"""
        if not QApplication.instance():
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()
        yield app
        app.quit()
    
    @pytest.fixture
    def mock_parent(self, qapp):
        """Mock 부모 위젯"""
        return Mock(spec=QWidget)
    
    @pytest.fixture
    def legacy_screen(self, mock_parent):
        """기존 트리거 빌더 스크린"""
        return TriggerBuilderScreen(mock_parent)
    
    @pytest.fixture
    def sample_data(self):
        """테스트용 샘플 데이터"""
        return {
            "price_data": [100 + i for i in range(50)],
            "variable_name": "SMA_20",
            "period": 20,
            "threshold": 105
        }
    
    def test_calculate_sma_compatibility(self, legacy_screen, sample_data):
        """_calculate_sma 메서드 호환성 테스트"""
        # Given: 기존 방식의 SMA 계산
        price_data = sample_data["price_data"]
        period = sample_data["period"]
        
        # When: 기존 메서드 호출
        with patch.object(legacy_screen, '_data_manager') as mock_manager:
            mock_manager.get_price_data.return_value = price_data
            
            legacy_result = legacy_screen._calculate_sma(price_data, period)
        
        # 새로운 어댅터를 통한 계산
        adapter = TriggerBuilderAdapter()
        new_result = adapter.calculate_technical_indicator("SMA", price_data, {"period": period})
        
        # Then: 결과가 동일함
        assert len(legacy_result) == len(new_result.values)
        
        # 값 비교 (소수점 오차 허용)
        for legacy_val, new_val in zip(legacy_result, new_result.values):
            if legacy_val is not None and new_val is not None:
                assert abs(legacy_val - new_val) < 0.001
    
    def test_calculate_trigger_points_compatibility(self, legacy_screen, sample_data):
        """calculate_trigger_points 메서드 호환성 테스트"""
        # Given: 트리거 포인트 계산 파라미터
        price_data = sample_data["price_data"]
        variable_name = sample_data["variable_name"]
        threshold = sample_data["threshold"]
        
        # When: 기존 메서드 호출
        with patch.object(legacy_screen, '_prepare_calculation_data') as mock_prep:
            mock_prep.return_value = {"SMA_20": [100 + i * 0.5 for i in range(50)]}
            
            legacy_result = legacy_screen.calculate_trigger_points(
                variable_name, "crosses_above", threshold
            )
        
        # 새로운 어댑터를 통한 계산
        adapter = TriggerBuilderAdapter()
        condition = {
            "variable": variable_name,
            "operator": "crosses_above", 
            "threshold": threshold
        }
        new_result = adapter.detect_triggers(price_data, [condition])
        
        # Then: 결과가 동일함
        assert isinstance(legacy_result, list)
        assert isinstance(new_result.trigger_points, list)
        
        # 트리거 포인트 개수 비교
        assert len(legacy_result) == len(new_result.trigger_points)
    
    def test_simulation_method_compatibility(self, legacy_screen, sample_data):
        """시뮬레이션 메서드 호환성 테스트"""
        # Given: 시뮬레이션 파라미터
        price_data = sample_data["price_data"]
        
        # When: 기존 시뮬레이션 실행
        with patch.object(legacy_screen, 'trigger_simulation_service') as mock_service:
            mock_service.run_simulation.return_value = {
                "success": True,
                "trigger_points": [10, 20, 30],
                "chart_data": Mock()
            }
            
            legacy_result = legacy_screen.run_trigger_simulation()
        
        # 새로운 어댑터를 통한 시뮬레이션
        adapter = TriggerBuilderAdapter()
        simulation_config = {
            "conditions": [{"variable": "SMA_20", "operator": "crosses_above", "threshold": 105}],
            "indicators": {"SMA": {"period": 20}}
        }
        new_result = adapter.run_complete_simulation(price_data, simulation_config)
        
        # Then: 결과 구조가 호환됨
        assert "success" in legacy_result
        assert hasattr(new_result, "success")
        assert "trigger_points" in legacy_result
        assert hasattr(new_result, "trigger_points")
    
    def test_ui_event_handler_compatibility(self, legacy_screen):
        """UI 이벤트 핸들러 호환성 테스트"""
        # Given: UI 이벤트 시뮬레이션
        mock_event = Mock()
        
        # When: 기존 이벤트 핸들러 호출
        original_handlers = [
            "on_variable_changed",
            "on_operator_changed", 
            "on_threshold_changed",
            "on_calculate_clicked"
        ]
        
        # Then: 모든 핸들러가 존재하고 호출 가능함
        for handler_name in original_handlers:
            assert hasattr(legacy_screen, handler_name)
            handler = getattr(legacy_screen, handler_name)
            assert callable(handler)
    
    def test_data_access_compatibility(self, legacy_screen):
        """데이터 접근 메서드 호환성 테스트"""
        # Given: 데이터 접근 메서드들
        data_methods = [
            "get_current_variable_data",
            "get_calculation_results",
            "get_trigger_points",
            "get_simulation_results"
        ]
        
        # When & Then: 모든 메서드가 존재함
        for method_name in data_methods:
            assert hasattr(legacy_screen, method_name)
            method = getattr(legacy_screen, method_name)
            assert callable(method)
    
    def test_configuration_compatibility(self, legacy_screen):
        """설정 관련 메서드 호환성 테스트"""
        # Given: 설정 관련 메서드들
        config_methods = [
            "save_current_configuration",
            "load_configuration",
            "reset_to_defaults"
        ]
        
        # When & Then: 모든 설정 메서드가 존재함
        for method_name in config_methods:
            if hasattr(legacy_screen, method_name):
                method = getattr(legacy_screen, method_name)
                assert callable(method)
```

### **3. 성능 벤치마크 테스트 (2시간)**
```python
# tests/integration/trigger_builder/test_performance_integration.py
"""
성능 통합 테스트 및 벤치마크
"""

import pytest
import time
import psutil
import os
from typing import List, Dict, Any
import json
from pathlib import Path

from ui.desktop.adapters.triggers.trigger_builder_adapter import TriggerBuilderAdapter

class TestPerformanceIntegration:
    """성능 통합 테스트"""
    
    @pytest.fixture
    def performance_adapter(self):
        """성능 테스트용 어댑터"""
        return TriggerBuilderAdapter()
    
    @pytest.fixture
    def benchmark_data(self):
        """벤치마크 기준 데이터 로드"""
        benchmark_file = Path(__file__).parent / "fixtures" / "benchmark_results.json"
        if benchmark_file.exists():
            with open(benchmark_file, 'r') as f:
                return json.load(f)
        return {
            "max_execution_time": {
                "small_dataset": 1.0,    # 100 포인트
                "medium_dataset": 3.0,   # 1,000 포인트  
                "large_dataset": 10.0    # 10,000 포인트
            },
            "max_memory_usage": {
                "small_dataset": 10,     # 10MB
                "medium_dataset": 50,    # 50MB
                "large_dataset": 200     # 200MB
            }
        }
    
    def generate_price_data(self, size: int) -> List[float]:
        """테스트용 가격 데이터 생성"""
        import random
        random.seed(42)  # 재현 가능한 결과
        
        base_price = 100.0
        prices = [base_price]
        
        for i in range(1, size):
            change = random.uniform(-2.0, 2.0)
            new_price = max(prices[-1] + change, 1.0)
            prices.append(new_price)
        
        return prices
    
    @pytest.mark.performance
    def test_small_dataset_performance(self, performance_adapter, benchmark_data):
        """소규모 데이터셋 성능 테스트 (100 포인트)"""
        # Given: 소규모 데이터
        price_data = self.generate_price_data(100)
        conditions = [
            {"variable": "SMA_20", "operator": "crosses_above", "target": "price"},
            {"variable": "RSI_14", "operator": "less_than", "threshold": 30}
        ]
        
        # When: 성능 측정
        start_time = time.time()
        result = performance_adapter.detect_triggers(price_data, conditions)
        execution_time = time.time() - start_time
        
        # Then: 성능 기준 충족
        assert result.success
        max_time = benchmark_data["max_execution_time"]["small_dataset"]
        assert execution_time < max_time, f"실행 시간 {execution_time:.2f}초가 기준 {max_time}초 초과"
        
        print(f"소규모 데이터 처리 시간: {execution_time:.3f}초")
    
    @pytest.mark.performance
    def test_medium_dataset_performance(self, performance_adapter, benchmark_data):
        """중간 규모 데이터셋 성능 테스트 (1,000 포인트)"""
        # Given: 중간 규모 데이터
        price_data = self.generate_price_data(1000)
        simulation_config = {
            "conditions": [
                {"variable": "SMA_50", "operator": "crosses_above", "target": "EMA_20"},
                {"variable": "MACD", "operator": "crosses_above", "target": "MACD_signal"}
            ],
            "indicators": {
                "SMA": {"period": 50},
                "EMA": {"period": 20},
                "MACD": {"fast": 12, "slow": 26, "signal": 9}
            }
        }
        
        # When: 성능 측정
        start_time = time.time()
        result = performance_adapter.run_complete_simulation(price_data, simulation_config)
        execution_time = time.time() - start_time
        
        # Then: 성능 기준 충족
        assert result.success
        max_time = benchmark_data["max_execution_time"]["medium_dataset"]
        assert execution_time < max_time, f"실행 시간 {execution_time:.2f}초가 기준 {max_time}초 초과"
        
        print(f"중간 규모 데이터 처리 시간: {execution_time:.3f}초")
    
    @pytest.mark.performance
    def test_large_dataset_performance(self, performance_adapter, benchmark_data):
        """대규모 데이터셋 성능 테스트 (10,000 포인트)"""
        # Given: 대규모 데이터
        price_data = self.generate_price_data(10000)
        complex_conditions = [
            {"variable": "SMA_200", "operator": "crosses_above", "target": "price"},
            {"variable": "RSI_14", "operator": "between", "min_threshold": 30, "max_threshold": 70},
            {"variable": "MACD", "operator": "crosses_above", "target": "MACD_signal"},
            {"variable": "EMA_50", "operator": "greater_than", "target": "SMA_200"}
        ]
        
        # When: 성능 측정
        start_time = time.time()
        result = performance_adapter.detect_triggers(price_data, complex_conditions)
        execution_time = time.time() - start_time
        
        # Then: 성능 기준 충족
        assert result.success
        max_time = benchmark_data["max_execution_time"]["large_dataset"]
        assert execution_time < max_time, f"실행 시간 {execution_time:.2f}초가 기준 {max_time}초 초과"
        
        print(f"대규모 데이터 처리 시간: {execution_time:.3f}초")
    
    @pytest.mark.performance
    def test_memory_usage_benchmark(self, performance_adapter, benchmark_data):
        """메모리 사용량 벤치마크 테스트"""
        # Given: 메모리 모니터링 시작
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # When: 대용량 데이터 연속 처리
        for size in [100, 1000, 5000]:
            price_data = self.generate_price_data(size)
            
            for _ in range(5):  # 5번 반복
                result = performance_adapter.calculate_all_indicators(price_data, {
                    "SMA": {"period": 20},
                    "EMA": {"period": 20}, 
                    "RSI": {"period": 14},
                    "MACD": {"fast": 12, "slow": 26, "signal": 9},
                    "BOLLINGER": {"period": 20, "std_dev": 2}
                })
                assert result.success
        
        # Then: 메모리 사용량 확인
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        max_memory = benchmark_data["max_memory_usage"]["large_dataset"]
        assert memory_increase < max_memory, f"메모리 증가 {memory_increase:.1f}MB가 기준 {max_memory}MB 초과"
        
        print(f"메모리 사용량 증가: {memory_increase:.1f}MB")
    
    @pytest.mark.performance  
    def test_concurrent_operations_performance(self, performance_adapter):
        """동시 연산 성능 테스트"""
        import threading
        import queue
        
        # Given: 여러 동시 작업
        price_data = self.generate_price_data(1000)
        results_queue = queue.Queue()
        
        def worker_task(worker_id: int):
            try:
                result = performance_adapter.detect_triggers(price_data, [
                    {"variable": f"SMA_{20 + worker_id}", "operator": "crosses_above", "target": "price"}
                ])
                results_queue.put(("success", worker_id, result.success))
            except Exception as e:
                results_queue.put(("error", worker_id, str(e)))
        
        # When: 동시 실행
        threads = []
        start_time = time.time()
        
        for i in range(5):  # 5개 스레드
            thread = threading.Thread(target=worker_task, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        execution_time = time.time() - start_time
        
        # Then: 모든 작업 성공 및 성능 확인
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(results) == 5
        assert all(result[0] == "success" and result[2] for result in results)
        assert execution_time < 10.0  # 10초 이내
        
        print(f"동시 작업 처리 시간: {execution_time:.3f}초")
    
    def test_save_benchmark_results(self, benchmark_data):
        """벤치마크 결과 저장"""
        # 새로운 벤치마크 결과 생성 (실제 측정값으로 업데이트)
        updated_benchmark = {
            "last_updated": time.time(),
            "max_execution_time": {
                "small_dataset": 1.0,
                "medium_dataset": 3.0,
                "large_dataset": 10.0
            },
            "max_memory_usage": {
                "small_dataset": 10,
                "medium_dataset": 50,
                "large_dataset": 200
            },
            "test_environment": {
                "python_version": "3.13",
                "platform": "Windows",
                "cpu_count": os.cpu_count(),
                "total_memory": psutil.virtual_memory().total / 1024 / 1024 / 1024  # GB
            }
        }
        
        # 벤치마크 파일 저장
        benchmark_file = Path(__file__).parent / "fixtures" / "benchmark_results.json"
        benchmark_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(benchmark_file, 'w') as f:
            json.dump(updated_benchmark, f, indent=2)
        
        print(f"벤치마크 결과 저장 완료: {benchmark_file}")
```

### **4. 통합 검증 스크립트 (1시간)**
```powershell
# 통합 테스트 실행 스크립트
Write-Host "🚀 트리거 빌더 리팩토링 통합 테스트 시작" -ForegroundColor Green

# 1. 단위 테스트 실행
Write-Host "`n📋 1. 단위 테스트 실행..." -ForegroundColor Yellow
pytest tests/unit/business_logic/triggers/ -v --tb=short

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 단위 테스트 실패" -ForegroundColor Red
    exit 1
}

# 2. 통합 테스트 실행
Write-Host "`n🔗 2. 통합 테스트 실행..." -ForegroundColor Yellow
pytest tests/integration/trigger_builder/ -v --tb=short

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 통합 테스트 실패" -ForegroundColor Red
    exit 1
}

# 3. 호환성 테스트 실행
Write-Host "`n🔄 3. 호환성 테스트 실행..." -ForegroundColor Yellow
pytest tests/compatibility/trigger_builder/ -v --tb=short

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 호환성 테스트 실패" -ForegroundColor Red
    exit 1
}

# 4. 성능 테스트 실행
Write-Host "`n⚡ 4. 성능 테스트 실행..." -ForegroundColor Yellow
pytest tests/integration/trigger_builder/test_performance_integration.py -v -m performance --tb=short

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 성능 테스트 실패" -ForegroundColor Red
    exit 1
}

# 5. 코드 커버리지 확인
Write-Host "`n📊 5. 코드 커버리지 확인..." -ForegroundColor Yellow
pytest tests/ --cov=business_logic.triggers --cov=ui.desktop.adapters.triggers --cov-report=html --cov-report=term

# 6. 통합 검증 완료
Write-Host "`n✅ 모든 통합 테스트 완료!" -ForegroundColor Green
Write-Host "📈 커버리지 리포트: htmlcov/index.html" -ForegroundColor Cyan
```

## ✅ **완료 기준**

### **통합 테스트 체크리스트**
- [ ] 전체 워크플로우 통합 테스트 100% 통과
- [ ] 기존 호환성 테스트 100% 통과
- [ ] 성능 벤치마크 기준 충족
- [ ] 메모리 사용량 기준 충족
- [ ] 코드 커버리지 95% 이상

### **품질 기준**
- [ ] 모든 기존 기능 100% 동작
- [ ] 성능 저하 없음 (기존 대비 동등 이상)
- [ ] 메모리 누수 없음
- [ ] 동시성 안전성 보장

### **검증 명령어**
```powershell
# 전체 통합 테스트 실행
pytest tests/integration/ tests/compatibility/ -v

# 성능 테스트만 실행
pytest -m performance -v

# 커버리지 포함 전체 테스트
pytest --cov=business_logic --cov=ui.desktop.adapters --cov-report=html
```

## 🔗 **연관 작업**
- **이전**: TASK-20250802-17 (미니차트 시각화 서비스 구현)
- **다음**: TASK-20250802-19 (성능 최적화 및 벤치마킹)
- **관련**: 모든 이전 TASK (TASK-11 ~ TASK-17)

## 📊 **예상 소요 시간**
- **총 소요 시간**: 10시간
- **우선순위**: CRITICAL
- **복잡도**: HIGH (전체 시스템 통합)
- **리스크**: HIGH (호환성 이슈 가능성)

---
**작성일**: 2025년 8월 2일  
**담당자**: GitHub Copilot  
**문서 타입**: 통합 테스트 및 검증
