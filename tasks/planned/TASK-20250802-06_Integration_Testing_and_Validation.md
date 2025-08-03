# TASK-20250802-06: 통합 테스트 및 검증

## 📋 작업 개요
**목표**: Phase 1 리팩토링 완료 후 전체 시스템 통합 테스트 및 성능 검증
**우선순위**: HIGH
**예상 소요시간**: 3-4시간
**전제조건**: TASK-20250802-05 완료

## 🎯 작업 목표
- [ ] 전체 백테스팅 시스템 End-to-End 테스트
- [ ] 기존 기능과 새 구조의 완전한 동등성 검증
- [ ] 성능 벤치마크 및 최적화
- [ ] 사용자 시나리오 기반 통합 테스트

## 🧪 통합 테스트 구조

```
tests/
├── integration/
│   ├── __init__.py
│   ├── test_end_to_end_backtesting.py     # E2E 테스트
│   ├── test_ui_service_integration.py     # UI-서비스 통합
│   ├── test_legacy_compatibility.py       # 레거시 호환성
│   └── test_performance_benchmarks.py     # 성능 벤치마크
│
├── acceptance/
│   ├── test_user_scenarios.py             # 사용자 시나리오
│   └── test_real_world_usage.py           # 실제 사용 패턴
│
└── benchmarks/
    ├── performance_comparison.py          # 성능 비교
    └── memory_usage_analysis.py           # 메모리 사용량 분석
```

## 🛠️ 세부 테스트 구현

### Step 1: End-to-End 테스트

#### 1.1 전체 백테스팅 플로우 테스트
```python
# test_end_to_end_backtesting.py
class TestEndToEndBacktesting:
    """전체 백테스팅 시스템 E2E 테스트"""
    
    @pytest.mark.integration
    def test_complete_backtesting_flow(self):
        """완전한 백테스팅 플로우 테스트"""
        # 1. UI 컴포넌트 초기화
        from upbit_auto_trading.ui.desktop.screens.strategy_management.shared_simulation.charts.simulation_control_widget import SimulationControlWidget
        from upbit_auto_trading.ui.desktop.screens.strategy_management.shared_simulation.charts.simulation_result_widget import SimulationResultWidget
        
        control_widget = SimulationControlWidget()
        result_widget = SimulationResultWidget()
        
        # 2. 시뮬레이션 설정
        scenarios = ["상승 추세", "하락 추세", "횡보", "급등", "급락"]
        
        for scenario in scenarios:
            # 3. 시뮬레이션 실행
            control_widget.scenario_combo.setCurrentText(scenario)
            control_widget.length_spinbox.setValue(100)
            control_widget.run_button.click()
            
            # 4. 결과 검증
            self._wait_for_simulation_completion(result_widget)
            assert result_widget.price_data is not None
            assert len(result_widget.price_data) == 100
            
            # 5. UI 상태 검증
            assert control_widget.run_button.isEnabled()
            assert not control_widget.progress_bar.isVisible()
    
    @pytest.mark.integration
    def test_multiple_indicators_integration(self):
        """다중 지표 통합 테스트"""
        from business_logic.backtester.services.backtesting_service import BacktestingService
        from business_logic.backtester.models.backtest_config import BacktestConfig
        
        service = BacktestingService()
        config = BacktestConfig(
            data_source="embedded",
            scenario="상승 추세",
            data_length=200,
            indicators=["SMA", "EMA", "RSI", "MACD"],
            parameters={
                "sma_period": 20,
                "ema_period": 12,
                "rsi_period": 14
            }
        )
        
        result = service.run_backtest(config)
        
        # 모든 지표 계산 검증
        assert "SMA" in result.indicators
        assert "EMA" in result.indicators
        assert "RSI" in result.indicators
        assert "MACD" in result.indicators
        
        # 데이터 길이 일관성 검증
        assert len(result.market_data.close_prices) == 200
        assert len(result.indicators["SMA"]) == 200
        assert len(result.indicators["RSI"]) == 200
```

### Step 2: 레거시 호환성 검증

#### 2.1 기존 시스템과 결과 비교
```python
# test_legacy_compatibility.py
class TestLegacyCompatibility:
    """기존 시스템과의 완전한 호환성 검증"""
    
    @pytest.mark.compatibility
    def test_all_scenarios_compatibility(self):
        """모든 시나리오에서 기존 결과와 동일성 검증"""
        scenarios = ["상승 추세", "하락 추세", "횡보", "급등", "급락", "이동평균 교차"]
        
        for scenario in scenarios:
            # 기존 엔진 결과
            legacy_result = self._get_legacy_result(scenario)
            
            # 새로운 엔진 결과
            new_result = self._get_new_result(scenario)
            
            # 통계적 유사성 검증
            similarity = self._calculate_similarity(
                legacy_result['price_data'], 
                new_result.market_data.close_prices
            )
            
            assert similarity > 0.95, f"시나리오 '{scenario}' 호환성 부족: {similarity:.3f}"
    
    def _get_legacy_result(self, scenario: str) -> Dict[str, Any]:
        """기존 엔진에서 결과 가져오기"""
        from upbit_auto_trading.ui.desktop.screens.strategy_management.shared_simulation.engines.robust_simulation_engine import RobustSimulationEngine
        
        engine = RobustSimulationEngine()
        return engine.get_scenario_data(scenario, 100)
    
    def _get_new_result(self, scenario: str) -> SimulationResult:
        """새로운 엔진에서 결과 가져오기"""
        from business_logic.backtester.services.backtesting_service import BacktestingService
        from business_logic.backtester.models.backtest_config import BacktestConfig
        
        service = BacktestingService()
        config = BacktestConfig(
            data_source="embedded",
            scenario=scenario,
            data_length=100,
            indicators=[],
            parameters={}
        )
        return service.run_backtest(config)
    
    def _calculate_similarity(self, data1: List[float], data2: List[float]) -> float:
        """두 데이터 세트의 유사성 계산"""
        import numpy as np
        
        # 길이 맞춤
        min_len = min(len(data1), len(data2))
        data1 = data1[:min_len]
        data2 = data2[:min_len]
        
        # 피어슨 상관계수
        correlation = np.corrcoef(data1, data2)[0, 1]
        
        # 평균 절대 오차 (정규화)
        mae = np.mean(np.abs(np.array(data1) - np.array(data2)))
        mae_normalized = mae / np.mean(np.abs(data1))
        
        # 전체 유사성 점수 (상관계수 80%, MAE 20%)
        similarity = correlation * 0.8 + (1 - mae_normalized) * 0.2
        return max(0, similarity)
```

### Step 3: 성능 벤치마크

#### 3.1 성능 비교 테스트
```python
# test_performance_benchmarks.py
class TestPerformanceBenchmarks:
    """성능 벤치마크 테스트"""
    
    @pytest.mark.benchmark
    def test_simulation_performance_comparison(self, benchmark):
        """시뮬레이션 성능 비교"""
        
        def run_new_engine():
            """새로운 엔진 실행"""
            from business_logic.backtester.services.backtesting_service import BacktestingService
            service = BacktestingService()
            config = BacktestConfig(
                data_source="embedded",
                scenario="상승 추세",
                data_length=1000,
                indicators=["SMA", "RSI", "MACD"],
                parameters={}
            )
            return service.run_backtest(config)
        
        def run_legacy_engine():
            """기존 엔진 실행"""
            from upbit_auto_trading.ui.desktop.screens.strategy_management.shared_simulation.engines.robust_simulation_engine import RobustSimulationEngine
            engine = RobustSimulationEngine()
            return engine.get_scenario_data("상승 추세", 1000)
        
        # 새로운 엔진 성능 측정
        new_result = benchmark(run_new_engine)
        
        # 기존 엔진 성능 측정 (참고용)
        import time
        start_time = time.time()
        legacy_result = run_legacy_engine()
        legacy_time = time.time() - start_time
        
        print(f"Legacy engine time: {legacy_time:.3f}s")
        print(f"New engine time: {benchmark.stats.min:.3f}s")
        
        # 성능 요구사항: 기존 대비 2배 이상 느려지지 않음
        assert benchmark.stats.min < legacy_time * 2.0
    
    @pytest.mark.benchmark  
    def test_memory_usage_comparison(self):
        """메모리 사용량 비교"""
        import tracemalloc
        
        # 새로운 엔진 메모리 사용량
        tracemalloc.start()
        new_result = self._run_new_engine_heavy_load()
        new_memory = tracemalloc.get_traced_memory()[1]  # peak
        tracemalloc.stop()
        
        # 기존 엔진 메모리 사용량
        tracemalloc.start()
        legacy_result = self._run_legacy_engine_heavy_load()
        legacy_memory = tracemalloc.get_traced_memory()[1]  # peak
        tracemalloc.stop()
        
        print(f"Legacy memory: {legacy_memory / 1024 / 1024:.2f} MB")
        print(f"New memory: {new_memory / 1024 / 1024:.2f} MB")
        
        # 메모리 요구사항: 기존 대비 50% 이상 증가하지 않음
        assert new_memory < legacy_memory * 1.5
```

### Step 4: 사용자 시나리오 테스트

#### 4.1 실제 사용 패턴 테스트
```python
# test_user_scenarios.py
class TestUserScenarios:
    """실제 사용자 시나리오 기반 테스트"""
    
    @pytest.mark.acceptance
    def test_typical_user_workflow(self):
        """일반적인 사용자 워크플로우 테스트"""
        # 시나리오: 사용자가 여러 시나리오로 백테스팅을 순차 실행
        
        from upbit_auto_trading.ui.desktop.screens.strategy_management.shared_simulation.adapters.backtesting_adapter import BacktestingAdapter
        adapter = BacktestingAdapter()
        
        # 1. 상승 추세 시뮬레이션
        result1 = adapter.run_simulation("상승 추세", 100, ["SMA"])
        assert result1['success'] is True
        assert result1['change_percent'] > 0
        
        # 2. 하락 추세 시뮬레이션  
        result2 = adapter.run_simulation("하락 추세", 100, ["RSI"])
        assert result2['success'] is True
        assert result2['change_percent'] < 0
        
        # 3. 복합 지표 시뮬레이션
        result3 = adapter.run_simulation("횡보", 200, ["SMA", "RSI", "MACD"])
        assert result3['success'] is True
        assert 'SMA' in result3['indicators']
        assert 'RSI' in result3['indicators']
        assert 'MACD' in result3['indicators']
    
    @pytest.mark.acceptance
    def test_error_recovery_scenario(self):
        """에러 상황에서 복구 시나리오 테스트"""
        from upbit_auto_trading.ui.desktop.screens.strategy_management.shared_simulation.adapters.backtesting_adapter import BacktestingAdapter
        adapter = BacktestingAdapter()
        
        # 1. 잘못된 시나리오 입력
        result = adapter.run_simulation("잘못된_시나리오", 100, ["SMA"])
        assert result['success'] is False
        assert 'error' in result
        assert 'fallback_data' in result
        
        # 2. 에러 후 정상 시나리오 실행 (복구 확인)
        result = adapter.run_simulation("상승 추세", 100, ["SMA"])
        assert result['success'] is True
```

## 📊 검증 체크리스트

### 기능 검증
- [ ] 모든 시나리오에서 시뮬레이션 정상 실행
- [ ] 모든 기술적 지표 정확한 계산
- [ ] UI 인터페이스 기존과 100% 동일
- [ ] 에러 상황 적절한 처리

### 성능 검증
- [ ] 시뮬레이션 실행 시간 기존 대비 2배 이내
- [ ] 메모리 사용량 기존 대비 1.5배 이내
- [ ] UI 응답성 저하 없음

### 호환성 검증
- [ ] 기존 시뮬레이션 결과와 95% 이상 일치
- [ ] 모든 시나리오 호환성 확인
- [ ] UI 사용법 변화 없음

## ✅ 완료 기준
- [ ] 모든 통합 테스트 통과 (100%)
- [ ] 성능 벤치마크 요구사항 충족
- [ ] 레거시 호환성 95% 이상 달성
- [ ] 사용자 시나리오 테스트 통과

## 📈 성공 지표
- **테스트 통과율**: 100%
- **성능 저하**: 2배 이내
- **메모리 증가**: 1.5배 이내
- **호환성**: 95% 이상

## 🚨 최종 확인 사항
1. **기능 회귀 없음**: 기존 기능 100% 보존
2. **UI 변경 없음**: 사용자 경험 동일
3. **성능 요구사항**: 허용 범위 내 성능
4. **안정성**: 에러 상황 적절한 처리

## 🔗 연관 TASK
- **이전**: TASK-20250802-05 (UI 연결 및 서비스 통합)
- **다음**: TASK-20250802-07 (Phase 1 완료 및 정리)

## 📝 산출물
1. **통합 테스트 리포트**: 모든 테스트 결과 및 통계
2. **성능 벤치마크 보고서**: 성능 비교 및 분석
3. **호환성 검증 보고서**: 레거시 시스템과의 비교 분석
4. **품질 보증 문서**: 최종 품질 검증 및 승인

---
**작업자**: GitHub Copilot
**생성일**: 2025년 8월 2일
**상태**: 계획됨
