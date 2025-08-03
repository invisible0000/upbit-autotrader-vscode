# TASK-20250802-04: 백테스팅 엔진 단위 테스트 작성

## 📋 작업 개요
**목표**: 새로운 백테스팅 엔진의 포괄적인 단위 테스트 구현
**우선순위**: HIGH
**예상 소요시간**: 3-4시간
**전제조건**: TASK-20250802-03 완료
**목표 커버리지**: 90% 이상

## 🎯 작업 목표
- [ ] 모든 백테스팅 엔진 클래스 단위 테스트 작성
- [ ] 90% 이상 코드 커버리지 달성
- [ ] 기존 시뮬레이션 결과와 동일성 검증
- [ ] 에러 케이스 및 예외 상황 테스트

## 🧪 테스트 파일 구조

```
tests/
├── unit/
│   ├── __init__.py
│   ├── backtester/
│   │   ├── __init__.py
│   │   ├── engines/
│   │   │   ├── test_base_engine.py
│   │   │   ├── test_market_data_engine.py
│   │   │   ├── test_indicator_engine.py
│   │   │   ├── test_simulation_engine.py
│   │   │   └── test_scenario_engine.py
│   │   ├── models/
│   │   │   ├── test_market_data.py
│   │   │   ├── test_backtest_config.py
│   │   │   └── test_simulation_result.py
│   │   └── services/
│   │       ├── test_backtesting_service.py
│   │       └── test_data_validation_service.py
│   └── conftest.py                     # pytest 설정 및 fixtures
└── integration/
    └── test_backtesting_integration.py # 통합 테스트
```

## 🛠️ 세부 테스트 구현

### Step 1: 테스트 데이터 및 Fixtures 설정

#### 1.1 conftest.py 구현
```python
import pytest
import pandas as pd
from datetime import datetime, timedelta
from business_logic.backtester.models.market_data import MarketData
from business_logic.backtester.models.backtest_config import BacktestConfig

@pytest.fixture
def sample_market_data():
    """테스트용 시장 데이터"""
    dates = [datetime.now() - timedelta(days=i) for i in range(100, 0, -1)]
    prices = [50000 + i * 100 for i in range(100)]
    
    return MarketData(
        timestamps=dates,
        open_prices=prices,
        high_prices=[p * 1.02 for p in prices],
        low_prices=[p * 0.98 for p in prices], 
        close_prices=prices,
        volumes=[1000 + i * 10 for i in range(100)]
    )

@pytest.fixture  
def sample_backtest_config():
    """테스트용 백테스트 설정"""
    return BacktestConfig(
        data_source="embedded",
        scenario="상승 추세",
        data_length=100,
        indicators=["SMA", "RSI"],
        parameters={"sma_period": 20, "rsi_period": 14}
    )
```

### Step 2: 엔진별 단위 테스트

#### 2.1 MarketDataEngine 테스트 (test_market_data_engine.py)
```python
class TestMarketDataEngine:
    """MarketDataEngine 단위 테스트"""
    
    def test_load_embedded_data(self, sample_backtest_config):
        """내장 데이터 로딩 테스트"""
        engine = MarketDataEngine()
        data = engine.load_data(sample_backtest_config)
        
        assert isinstance(data, MarketData)
        assert len(data.close_prices) == 100
        assert all(price > 0 for price in data.close_prices)
    
    def test_load_real_data_with_fallback(self, sample_backtest_config):
        """실제 DB 데이터 로딩 (폴백 포함) 테스트"""
        config = sample_backtest_config
        config.data_source = "real_db"
        
        engine = MarketDataEngine()
        data = engine.load_data(config)
        
        # 실제 DB 없어도 폴백 데이터로 동작해야 함
        assert isinstance(data, MarketData)
        assert len(data.close_prices) > 0
    
    def test_scenario_data_generation(self, sample_backtest_config):
        """시나리오별 데이터 생성 테스트"""
        scenarios = ["상승 추세", "하락 추세", "횡보", "급등", "급락"]
        engine = MarketDataEngine()
        
        for scenario in scenarios:
            config = sample_backtest_config
            config.scenario = scenario
            data = engine.load_data(config)
            
            assert isinstance(data, MarketData)
            assert len(data.close_prices) == config.data_length
    
    def test_invalid_config_handling(self):
        """잘못된 설정 처리 테스트"""
        engine = MarketDataEngine()
        
        # 잘못된 시나리오
        config = BacktestConfig(
            data_source="embedded",
            scenario="invalid_scenario", 
            data_length=10,
            indicators=[],
            parameters={}
        )
        
        with pytest.raises(BacktestDataError):
            engine.load_data(config)
```

#### 2.2 IndicatorEngine 테스트 (test_indicator_engine.py)
```python
class TestIndicatorEngine:
    """IndicatorEngine 단위 테스트"""
    
    def test_sma_calculation(self, sample_market_data):
        """SMA 계산 정확성 테스트"""
        engine = IndicatorEngine()
        sma_data = engine.calculate_sma(sample_market_data.close_prices, period=20)
        
        # 수동 계산과 비교
        expected_sma = sum(sample_market_data.close_prices[19:39]) / 20
        assert abs(sma_data[19] - expected_sma) < 0.01
    
    def test_rsi_calculation(self, sample_market_data):
        """RSI 계산 정확성 테스트"""
        engine = IndicatorEngine()
        rsi_data = engine.calculate_rsi(sample_market_data.close_prices, period=14)
        
        # RSI 범위 검증 (0-100)
        assert all(0 <= rsi <= 100 for rsi in rsi_data if rsi is not None)
        assert len(rsi_data) == len(sample_market_data.close_prices)
    
    def test_macd_calculation(self, sample_market_data):
        """MACD 계산 정확성 테스트"""
        engine = IndicatorEngine()
        macd_data = engine.calculate_macd(sample_market_data.close_prices)
        
        assert 'macd' in macd_data
        assert 'signal' in macd_data
        assert 'histogram' in macd_data
        assert len(macd_data['macd']) == len(sample_market_data.close_prices)
    
    def test_custom_parameters(self, sample_market_data):
        """커스텀 파라미터 지원 테스트"""
        engine = IndicatorEngine()
        
        # 다른 기간으로 SMA 계산
        sma_10 = engine.calculate_sma(sample_market_data.close_prices, period=10)
        sma_30 = engine.calculate_sma(sample_market_data.close_prices, period=30)
        
        # 다른 기간은 다른 결과 생성
        assert sma_10 != sma_30
```

### Step 3: 서비스 계층 테스트

#### 3.1 BacktestingService 통합 테스트
```python
class TestBacktestingService:
    """BacktestingService 통합 테스트"""
    
    def test_complete_backtest_flow(self, sample_backtest_config):
        """전체 백테스트 플로우 테스트"""
        service = BacktestingService()
        result = service.run_backtest(sample_backtest_config)
        
        assert isinstance(result, SimulationResult)
        assert result.market_data is not None
        assert result.indicators is not None
        assert result.simulation_metadata is not None
    
    def test_backtest_with_multiple_indicators(self, sample_backtest_config):
        """다중 지표 백테스트 테스트"""
        config = sample_backtest_config
        config.indicators = ["SMA", "EMA", "RSI", "MACD"]
        
        service = BacktestingService()
        result = service.run_backtest(config)
        
        # 모든 지표가 계산되었는지 확인
        assert "SMA" in result.indicators
        assert "EMA" in result.indicators  
        assert "RSI" in result.indicators
        assert "MACD" in result.indicators
```

### Step 4: 기존 시뮬레이션과 동일성 검증

#### 4.1 레거시 호환성 테스트
```python
class TestLegacyCompatibility:
    """기존 시뮬레이션 결과와 동일성 검증"""
    
    def test_embedded_engine_compatibility(self):
        """내장 엔진 결과 동일성 테스트"""
        # 기존 EmbeddedSimulationDataEngine 결과
        from upbit_auto_trading.ui.desktop.screens.strategy_management.shared_simulation.engines.embedded_simulation_engine import EmbeddedSimulationDataEngine
        legacy_engine = EmbeddedSimulationDataEngine()
        legacy_result = legacy_engine.get_scenario_data("상승 추세", 50)
        
        # 새로운 엔진 결과
        from business_logic.backtester.services.backtesting_service import BacktestingService
        new_service = BacktestingService()
        config = BacktestConfig(
            data_source="embedded",
            scenario="상승 추세", 
            data_length=50,
            indicators=[],
            parameters={}
        )
        new_result = new_service.run_backtest(config)
        
        # 결과 비교 (허용 오차 범위 내)
        assert len(new_result.market_data.close_prices) == len(legacy_result['price_data'])
        
        # 통계적 유사성 검증
        import numpy as np
        correlation = np.corrcoef(
            new_result.market_data.close_prices,
            legacy_result['price_data']
        )[0, 1]
        assert correlation > 0.95  # 95% 이상 상관관계
```

## 📊 테스트 커버리지 목표

### 목표 커버리지
- **전체 프로젝트**: 85% 이상
- **business_logic/backtester/**: 90% 이상
- **핵심 엔진 클래스**: 95% 이상

### 커버리지 측정 명령어
```bash
# 커버리지 측정
pytest --cov=business_logic/backtester --cov-report=html tests/unit/backtester/

# 상세 리포트 생성
pytest --cov=business_logic/backtester --cov-report=term-missing

# CI/CD용 XML 리포트
pytest --cov=business_logic/backtester --cov-report=xml --cov-fail-under=90
```

## ✅ 완료 기준
- [ ] 모든 엔진 클래스 단위 테스트 작성 (5개 엔진)
- [ ] 90% 이상 코드 커버리지 달성
- [ ] 기존 시뮬레이션 결과와 95% 이상 일치
- [ ] 에러 케이스 및 예외 상황 테스트 완료
- [ ] 성능 벤치마크 테스트 작성

## 📈 성공 지표
- **테스트 통과율**: 100%
- **코드 커버리지**: 90% 이상
- **레거시 호환성**: 95% 이상 결과 일치
- **성능**: 기존 대비 성능 저하 5% 이내

## 🚨 주의사항
1. **테스트 독립성**: 각 테스트는 서로 독립적으로 실행되어야 함
2. **데이터 격리**: 테스트 데이터가 실제 DB에 영향 주면 안됨
3. **성능 고려**: 테스트 실행 시간 최소화
4. **재현 가능성**: 동일한 입력에 대해 동일한 결과

## 🔗 연관 TASK  
- **이전**: TASK-20250802-03 (순수 엔진 구현)
- **다음**: TASK-20250802-05 (UI 연결 및 서비스 통합)

## 📝 산출물
1. **단위 테스트 파일**: 10개 테스트 파일 완전 구현
2. **커버리지 리포트**: HTML 형태의 상세 커버리지 보고서
3. **성능 벤치마크**: 기존 vs 새로운 엔진 성능 비교
4. **호환성 검증 보고서**: 레거시 시스템과의 결과 비교 분석

---
**작업자**: GitHub Copilot
**생성일**: 2025년 8월 2일
**상태**: 계획됨
