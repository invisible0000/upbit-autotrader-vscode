# 🎯 업비트 자동매매 시스템 테스트 실무 예제

> **대상**: 주니어 개발자 (업비트 프로젝트 신규 참여자)  
> **목적**: 프로젝트별 구체적인 테스트 작성 방법 학습  
> **전제**: UNIT_TEST_LIFECYCLE_GUIDE.md 선행 학습 완료

## 📋 목차
- [1. 프로젝트 테스트 구조](#1-프로젝트-테스트-구조)
- [2. 전략 시스템 테스트](#2-전략-시스템-테스트)
- [3. 트리거 빌더 테스트](#3-트리거-빌더-테스트)
- [4. 백테스팅 엔진 테스트](#4-백테스팅-엔진-테스트)
- [5. Mock 활용 실전 사례](#5-mock-활용-실전-사례)

---

## 1. 프로젝트 테스트 구조

### 📁 현재 테스트 폴더 구조
```
tests/
├── unit/                           # 유닛 테스트
│   ├── business_logic/            # 비즈니스 로직 테스트
│   │   ├── test_strategy.py       # 전략 관련 테스트
│   │   ├── test_backtester.py     # 백테스팅 테스트
│   │   └── test_screener.py       # 종목 스크리닝 테스트
│   ├── data_layer/               # 데이터 계층 테스트
│   │   ├── test_database_manager.py
│   │   └── test_market_data.py
│   └── ui/                       # UI 컴포넌트 테스트
│       ├── test_trigger_builder.py
│       └── test_strategy_maker.py
├── integration/                   # 통합 테스트
│   ├── test_strategy_execution.py
│   └── test_data_flow.py
├── fixtures/                     # 테스트 데이터
│   ├── market_data.json
│   ├── sample_strategies.json
│   └── test_database.sql
└── conftest.py                   # pytest 공통 설정
```

### 🔧 conftest.py 기본 설정
```python
import pytest
import pandas as pd
from datetime import datetime, timedelta
from upbit_auto_trading.data_layer.storage.database_manager import DatabaseManager

@pytest.fixture
def sample_market_data():
    """테스트용 시장 데이터 생성"""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    data = pd.DataFrame({
        'timestamp': dates,
        'open': 50000 + np.random.randn(100) * 1000,
        'high': 51000 + np.random.randn(100) * 1000,
        'low': 49000 + np.random.randn(100) * 1000,
        'close': 50000 + np.random.randn(100) * 1000,
        'volume': 1000 + np.random.randn(100) * 100
    })
    return data

@pytest.fixture
def test_database():
    """테스트용 인메모리 데이터베이스"""
    db_manager = DatabaseManager(":memory:")
    # 테스트 스키마 초기화
    db_manager.initialize_test_schema()
    yield db_manager
    db_manager.close()

@pytest.fixture
def sample_strategy_config():
    """기본 7규칙 전략 설정"""
    return {
        "name": "기본 7규칙 RSI 전략",
        "entry_rules": [
            {
                "type": "RSI_ENTRY",
                "variable": "RSI",
                "operator": "<",
                "value": 30,
                "parameters": {"period": 14}
            }
        ],
        "exit_rules": [
            {
                "type": "PROFIT_TARGET",
                "variable": "PROFIT_RATE",
                "operator": ">=",
                "value": 10.0
            }
        ]
    }
```

---

## 2. 전략 시스템 테스트

### 🎯 Strategy Entity 테스트
```python
# tests/unit/business_logic/test_strategy.py

import pytest
from upbit_auto_trading.business_logic.strategy.strategy_entity import Strategy
from upbit_auto_trading.business_logic.strategy.triggers import RSITrigger

class TestStrategyEntity:
    """전략 엔티티 테스트 슈트"""
    
    def test_create_basic_strategy(self, sample_strategy_config):
        """기본 전략 생성 테스트"""
        # Arrange
        config = sample_strategy_config
        
        # Act
        strategy = Strategy.create_from_config(config)
        
        # Assert
        assert strategy.name == "기본 7규칙 RSI 전략"
        assert len(strategy.entry_rules) == 1
        assert len(strategy.exit_rules) == 1
        assert strategy.is_valid()
    
    def test_strategy_entry_signal_generation(self, sample_market_data):
        """진입 신호 생성 테스트"""
        # Arrange
        rsi_trigger = RSITrigger(period=14, oversold=30, overbought=70)
        strategy = Strategy("Test Strategy", entry_triggers=[rsi_trigger])
        
        # Act
        signal = strategy.evaluate_entry_signal(sample_market_data)
        
        # Assert
        assert signal in ['BUY', 'SELL', 'HOLD']
    
    def test_strategy_validation_rules(self):
        """전략 검증 규칙 테스트"""
        # Arrange & Act & Assert
        
        # 진입 규칙이 없는 경우
        with pytest.raises(ValidationError, match="진입 규칙이 없습니다"):
            Strategy("Invalid Strategy", entry_triggers=[], exit_triggers=[])
        
        # 호환되지 않는 트리거 조합
        incompatible_triggers = [
            RSITrigger(period=14),
            VolumeTrigger(threshold=1000)  # RSI와 Volume은 호환 불가
        ]
        with pytest.raises(CompatibilityError):
            Strategy("Incompatible Strategy", entry_triggers=incompatible_triggers)
    
    def test_strategy_serialization(self, sample_strategy_config):
        """전략 직렬화/역직렬화 테스트"""
        # Arrange
        original_strategy = Strategy.create_from_config(sample_strategy_config)
        
        # Act
        serialized = original_strategy.to_dict()
        restored_strategy = Strategy.from_dict(serialized)
        
        # Assert
        assert restored_strategy.name == original_strategy.name
        assert len(restored_strategy.entry_rules) == len(original_strategy.entry_rules)
        assert restored_strategy.is_equivalent_to(original_strategy)
```

### 📈 지표 계산 테스트
```python
# tests/unit/business_logic/test_indicators.py

import pytest
import numpy as np
from upbit_auto_trading.business_logic.indicators.rsi import calculate_rsi
from upbit_auto_trading.business_logic.indicators.moving_average import calculate_sma

class TestTechnicalIndicators:
    """기술적 지표 계산 테스트"""
    
    def test_rsi_calculation_accuracy(self):
        """RSI 계산 정확도 테스트"""
        # Arrange - 알려진 결과를 가진 데이터
        prices = [44, 44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.85, 
                 46.08, 45.89, 46.03, 46.83, 46.69, 46.45, 46.59]
        expected_rsi = 70.53  # 수동 계산된 값
        
        # Act
        result = calculate_rsi(prices, period=14)
        
        # Assert
        assert abs(result - expected_rsi) < 0.1, f"RSI 계산 오차: {result} vs {expected_rsi}"
    
    def test_rsi_boundary_conditions(self):
        """RSI 경계값 테스트"""
        # 모든 상승: RSI = 100
        uptrend_prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
        rsi_up = calculate_rsi(uptrend_prices, period=9)
        assert rsi_up == 100
        
        # 모든 하락: RSI = 0
        downtrend_prices = [109, 108, 107, 106, 105, 104, 103, 102, 101, 100]
        rsi_down = calculate_rsi(downtrend_prices, period=9)
        assert rsi_down == 0
        
        # 동일한 가격: RSI = 50 (중립)
        flat_prices = [100] * 15
        rsi_flat = calculate_rsi(flat_prices, period=14)
        assert rsi_flat == 50
    
    def test_rsi_error_handling(self):
        """RSI 에러 처리 테스트"""
        # 데이터 부족
        with pytest.raises(ValueError, match="데이터가 부족합니다"):
            calculate_rsi([100, 101], period=14)
        
        # 음수 기간
        with pytest.raises(ValueError, match="기간은 양수여야 합니다"):
            calculate_rsi([100, 101, 102], period=-1)
        
        # 빈 데이터
        with pytest.raises(ValueError, match="빈 데이터입니다"):
            calculate_rsi([], period=14)
    
    @pytest.mark.performance
    def test_rsi_performance(self):
        """RSI 계산 성능 테스트"""
        # Arrange
        large_dataset = np.random.random(10000) * 100
        
        # Act
        import time
        start_time = time.time()
        result = calculate_rsi(large_dataset, period=14)
        execution_time = time.time() - start_time
        
        # Assert
        assert execution_time < 0.1, f"RSI 계산이 너무 느림: {execution_time}초"
        assert isinstance(result, float)
```

---

## 3. 트리거 빌더 테스트

### 🎯 조건 생성 테스트
```python
# tests/unit/ui/test_trigger_builder.py

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication
from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.trigger_builder_screen import TriggerBuilderScreen

class TestTriggerBuilder:
    """트리거 빌더 UI 테스트"""
    
    @pytest.fixture
    def app(self):
        """PyQt6 애플리케이션 픽스처"""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app
    
    @pytest.fixture
    def trigger_builder(self, app, test_database):
        """트리거 빌더 위젯 픽스처"""
        builder = TriggerBuilderScreen()
        builder.database_manager = test_database
        return builder
    
    def test_variable_selection(self, trigger_builder):
        """변수 선택 기능 테스트"""
        # Arrange
        trigger_builder.load_available_variables()
        
        # Act
        trigger_builder.select_variable("RSI")
        
        # Assert
        assert trigger_builder.current_variable == "RSI"
        assert trigger_builder.parameter_panel.is_visible()
    
    def test_parameter_configuration(self, trigger_builder):
        """파라미터 설정 테스트"""
        # Arrange
        trigger_builder.select_variable("RSI")
        
        # Act
        trigger_builder.set_parameter("period", 14)
        trigger_builder.set_parameter("overbought", 70)
        trigger_builder.set_parameter("oversold", 30)
        
        # Assert
        params = trigger_builder.get_current_parameters()
        assert params["period"] == 14
        assert params["overbought"] == 70
        assert params["oversold"] == 30
    
    def test_condition_creation(self, trigger_builder):
        """조건 생성 테스트"""
        # Arrange
        trigger_builder.select_variable("RSI")
        trigger_builder.set_parameter("period", 14)
        
        # Act
        condition = trigger_builder.create_condition(
            operator="<",
            target_value=30,
            condition_name="RSI 과매도"
        )
        
        # Assert
        assert condition.variable_id == "RSI"
        assert condition.operator == "<"
        assert condition.target_value == 30
        assert condition.name == "RSI 과매도"
    
    @patch('upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.core.compatibility_validator.CompatibilityValidator')
    def test_compatibility_validation(self, mock_validator, trigger_builder):
        """호환성 검증 테스트"""
        # Arrange
        mock_validator.return_value.check_compatibility.return_value = "incompatible"
        trigger_builder.select_variable("RSI")
        
        # Act
        is_compatible = trigger_builder.check_variable_compatibility("Volume")
        
        # Assert
        assert not is_compatible
        mock_validator.return_value.check_compatibility.assert_called_once_with("RSI", "Volume")
    
    def test_condition_drag_and_drop(self, trigger_builder):
        """조건 드래그앤드롭 테스트"""
        # Arrange
        condition1 = trigger_builder.create_condition_card("RSI < 30")
        condition2 = trigger_builder.create_condition_card("SMA(20) > Close")
        
        # Act
        trigger_builder.canvas.add_condition(condition1)
        trigger_builder.canvas.add_condition(condition2)
        trigger_builder.canvas.set_logic_operator("AND")
        
        # Assert
        assert len(trigger_builder.canvas.conditions) == 2
        assert trigger_builder.canvas.logic_operator == "AND"
```

### 🔗 호환성 검증 시스템 테스트
```python
# tests/unit/ui/test_compatibility_validator.py

import pytest
from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.shared.compatibility_validator import CompatibilityValidator

class TestCompatibilityValidator:
    """변수 호환성 검증 테스트"""
    
    @pytest.fixture
    def validator(self, test_database):
        return CompatibilityValidator(test_database)
    
    def test_same_comparison_group_compatibility(self, validator):
        """동일 비교 그룹 호환성 테스트"""
        # price_comparable 그룹
        assert validator.check_compatibility("SMA", "EMA") == "compatible"
        assert validator.check_compatibility("Close", "High") == "compatible"
        
        # percentage_comparable 그룹
        assert validator.check_compatibility("RSI", "Stochastic") == "compatible"
    
    def test_different_comparison_group_incompatibility(self, validator):
        """다른 비교 그룹 비호환성 테스트"""
        # price vs percentage
        assert validator.check_compatibility("Close", "RSI") == "warning"
        
        # volume vs percentage
        assert validator.check_compatibility("Volume", "RSI") == "incompatible"
    
    def test_filter_compatible_variables(self, validator):
        """호환 가능 변수 필터링 테스트"""
        # Arrange
        base_variable = "RSI"
        
        # Act
        compatible_vars = validator.get_compatible_variables(base_variable)
        
        # Assert
        assert "Stochastic" in compatible_vars
        assert "Williams_R" in compatible_vars
        assert "SMA" not in compatible_vars  # price_comparable이므로 제외
        assert "Volume" not in compatible_vars  # volume_based이므로 제외
    
    def test_normalization_warning_generation(self, validator):
        """정규화 경고 생성 테스트"""
        # Act
        result = validator.check_compatibility("Close", "RSI")
        warning_msg = validator.get_warning_message("Close", "RSI")
        
        # Assert
        assert result == "warning"
        assert "정규화" in warning_msg
        assert "주의" in warning_msg
```

---

## 4. 백테스팅 엔진 테스트

### 📊 백테스팅 로직 테스트
```python
# tests/unit/business_logic/test_backtester.py

import pytest
import pandas as pd
from datetime import datetime, timedelta
from upbit_auto_trading.business_logic.backtester.backtesting_engine import BacktestingEngine
from upbit_auto_trading.business_logic.strategy.strategy_entity import Strategy

class TestBacktestingEngine:
    """백테스팅 엔진 테스트"""
    
    @pytest.fixture
    def backtest_engine(self, test_database):
        return BacktestingEngine(database_manager=test_database)
    
    @pytest.fixture
    def sample_ohlcv_data(self):
        """백테스팅용 OHLCV 데이터"""
        dates = pd.date_range(start='2023-01-01', periods=365, freq='D')
        np.random.seed(42)  # 재현 가능한 랜덤 데이터
        
        # 상승 추세 데이터 생성
        base_price = 50000
        prices = []
        for i in range(365):
            # 일반적인 변동성 + 상승 추세
            change = np.random.normal(0.001, 0.02)  # 평균 0.1% 상승, 2% 변동성
            base_price *= (1 + change)
            prices.append(base_price)
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': np.random.randint(1000, 10000, 365)
        })
        return data
    
    def test_simple_strategy_backtest(self, backtest_engine, sample_ohlcv_data, sample_strategy_config):
        """단순 전략 백테스팅 테스트"""
        # Arrange
        strategy = Strategy.create_from_config(sample_strategy_config)
        initial_capital = 1000000  # 100만원
        
        # Act
        result = backtest_engine.run_backtest(
            strategy=strategy,
            data=sample_ohlcv_data,
            initial_capital=initial_capital,
            symbol="KRW-BTC"
        )
        
        # Assert
        assert result.initial_capital == initial_capital
        assert result.final_capital > 0
        assert result.total_trades >= 0
        assert -100 <= result.total_return <= 1000  # 합리적인 수익률 범위
        assert 0 <= result.win_rate <= 100
    
    def test_position_management(self, backtest_engine, sample_ohlcv_data):
        """포지션 관리 테스트"""
        # Arrange
        strategy = Strategy.create_basic_buy_hold_strategy()
        
        # Act
        backtest_engine.start_backtest(strategy, sample_ohlcv_data, 1000000)
        
        # 첫 번째 매수 신호 시뮬레이션
        buy_signal = backtest_engine.process_signal('BUY', sample_ohlcv_data.iloc[10])
        
        # Assert
        assert backtest_engine.current_position is not None
        assert backtest_engine.current_position.entry_price > 0
        assert backtest_engine.current_position.quantity > 0
        
        # 매도 신호 시뮬레이션
        sell_signal = backtest_engine.process_signal('SELL', sample_ohlcv_data.iloc[20])
        
        # Assert
        assert backtest_engine.current_position is None  # 포지션 청산됨
        assert len(backtest_engine.trade_history) == 1  # 거래 기록 저장됨
    
    def test_performance_metrics_calculation(self, backtest_engine):
        """성과 지표 계산 테스트"""
        # Arrange
        trade_history = [
            {'entry_price': 50000, 'exit_price': 55000, 'quantity': 0.1, 'profit': 500},
            {'entry_price': 55000, 'exit_price': 52000, 'quantity': 0.1, 'profit': -300},
            {'entry_price': 52000, 'exit_price': 58000, 'quantity': 0.1, 'profit': 600},
        ]
        backtest_engine.trade_history = trade_history
        
        # Act
        metrics = backtest_engine.calculate_performance_metrics()
        
        # Assert
        assert metrics['total_trades'] == 3
        assert metrics['winning_trades'] == 2
        assert metrics['losing_trades'] == 1
        assert metrics['win_rate'] == 66.67  # 2/3 * 100
        assert metrics['total_profit'] == 800  # 500 - 300 + 600
        assert metrics['avg_profit_per_trade'] == 266.67  # 800 / 3
    
    @pytest.mark.performance
    def test_backtest_performance(self, backtest_engine, sample_strategy_config):
        """백테스팅 성능 테스트"""
        # Arrange
        strategy = Strategy.create_from_config(sample_strategy_config)
        large_dataset = self.create_large_ohlcv_dataset(days=1000)  # 3년치 데이터
        
        # Act
        import time
        start_time = time.time()
        result = backtest_engine.run_backtest(strategy, large_dataset, 1000000)
        execution_time = time.time() - start_time
        
        # Assert
        assert execution_time < 5.0, f"백테스팅이 너무 느림: {execution_time}초"
        assert result is not None
    
    def test_edge_cases(self, backtest_engine, sample_strategy_config):
        """극단적 케이스 테스트"""
        strategy = Strategy.create_from_config(sample_strategy_config)
        
        # 매우 작은 데이터셋
        tiny_data = pd.DataFrame({
            'timestamp': [datetime.now()],
            'open': [50000],
            'high': [51000],
            'low': [49000],
            'close': [50500],
            'volume': [1000]
        })
        
        with pytest.raises(ValueError, match="데이터가 부족합니다"):
            backtest_engine.run_backtest(strategy, tiny_data, 1000000)
        
        # 매우 작은 자본금
        with pytest.raises(ValueError, match="자본금이 너무 작습니다"):
            backtest_engine.run_backtest(strategy, self.create_large_ohlcv_dataset(), 1000)
    
    def create_large_ohlcv_dataset(self, days=1000):
        """대용량 OHLCV 데이터 생성"""
        dates = pd.date_range(start='2021-01-01', periods=days, freq='D')
        base_price = 50000
        prices = []
        
        for i in range(days):
            change = np.random.normal(0, 0.02)
            base_price *= (1 + change)
            prices.append(base_price)
        
        return pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * 1.02 for p in prices],
            'low': [p * 0.98 for p in prices],
            'close': prices,
            'volume': np.random.randint(1000, 10000, days)
        })
```

---

## 5. Mock 활용 실전 사례

### 🔌 외부 API Mock 처리
```python
# tests/unit/data_layer/test_upbit_api.py

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from upbit_auto_trading.data_layer.external_apis.upbit_client import UpbitClient

class TestUpbitApiClient:
    """업비트 API 클라이언트 테스트"""
    
    @pytest.fixture
    def upbit_client(self):
        return UpbitClient(access_key="test_key", secret_key="test_secret")
    
    @patch('requests.get')
    def test_get_current_price_success(self, mock_get, upbit_client):
        """현재 가격 조회 성공 테스트"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            'market': 'KRW-BTC',
            'trade_price': 50000000,
            'change': 'RISE',
            'change_rate': 0.02
        }]
        mock_get.return_value = mock_response
        
        # Act
        price_data = upbit_client.get_current_price('KRW-BTC')
        
        # Assert
        assert price_data['trade_price'] == 50000000
        assert price_data['change'] == 'RISE'
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_get_current_price_api_error(self, mock_get, upbit_client):
        """API 오류 처리 테스트"""
        # Arrange
        mock_get.side_effect = requests.exceptions.ConnectionError("네트워크 오류")
        
        # Act & Assert
        with pytest.raises(APIConnectionError, match="업비트 API 연결 실패"):
            upbit_client.get_current_price('KRW-BTC')
    
    @patch('requests.get')
    def test_get_current_price_rate_limit(self, mock_get, upbit_client):
        """요청 제한 처리 테스트"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 429  # Too Many Requests
        mock_response.json.return_value = {'error': '요청 제한 초과'}
        mock_get.return_value = mock_response
        
        # Act & Assert
        with pytest.raises(RateLimitError, match="요청 제한 초과"):
            upbit_client.get_current_price('KRW-BTC')
    
    @patch('upbit_auto_trading.data_layer.external_apis.upbit_client.time.sleep')
    @patch('requests.get')
    def test_retry_mechanism(self, mock_get, mock_sleep, upbit_client):
        """재시도 메커니즘 테스트"""
        # Arrange
        # 첫 번째, 두 번째 호출은 실패, 세 번째는 성공
        mock_get.side_effect = [
            requests.exceptions.ConnectionError("일시적 오류"),
            requests.exceptions.ConnectionError("일시적 오류"),
            Mock(status_code=200, json=lambda: [{'trade_price': 50000000}])
        ]
        
        # Act
        result = upbit_client.get_current_price('KRW-BTC')
        
        # Assert
        assert result['trade_price'] == 50000000
        assert mock_get.call_count == 3  # 3번 호출됨
        assert mock_sleep.call_count == 2  # 2번 대기함
```

### 🗄️ 데이터베이스 Mock 처리
```python
# tests/unit/data_layer/test_strategy_repository.py

import pytest
from unittest.mock import Mock, patch
from upbit_auto_trading.data_layer.repositories.strategy_repository import StrategyRepository

class TestStrategyRepository:
    """전략 저장소 테스트"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock 데이터베이스 매니저"""
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.get_connection.return_value.cursor.return_value = mock_cursor
        return mock_db, mock_cursor
    
    def test_save_strategy_success(self, mock_db_manager):
        """전략 저장 성공 테스트"""
        # Arrange
        mock_db, mock_cursor = mock_db_manager
        repository = StrategyRepository(mock_db)
        
        strategy_data = {
            'id': 'strategy_001',
            'name': '테스트 전략',
            'config': {'entry_rules': [], 'exit_rules': []}
        }
        
        # Act
        result = repository.save_strategy(strategy_data)
        
        # Assert
        assert result == 'strategy_001'
        mock_cursor.execute.assert_called_once()
        mock_db.get_connection.return_value.commit.assert_called_once()
    
    def test_save_strategy_database_error(self, mock_db_manager):
        """데이터베이스 오류 처리 테스트"""
        # Arrange
        mock_db, mock_cursor = mock_db_manager
        mock_cursor.execute.side_effect = Exception("DB 연결 오류")
        repository = StrategyRepository(mock_db)
        
        strategy_data = {'id': 'strategy_001', 'name': '테스트 전략'}
        
        # Act & Assert
        with pytest.raises(DatabaseError, match="전략 저장 실패"):
            repository.save_strategy(strategy_data)
        
        # 롤백이 호출되었는지 확인
        mock_db.get_connection.return_value.rollback.assert_called_once()
```

### 🎮 UI 컴포넌트 Mock 처리
```python
# tests/unit/ui/test_strategy_maker_presenter.py

import pytest
from unittest.mock import Mock, MagicMock
from upbit_auto_trading.ui.desktop.screens.strategy_management.strategy_maker.strategy_maker_presenter import StrategyMakerPresenter

class TestStrategyMakerPresenter:
    """전략 메이커 프레젠터 테스트"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock 의존성들"""
        mock_view = Mock()
        mock_strategy_service = Mock()
        mock_validation_service = Mock()
        
        return mock_view, mock_strategy_service, mock_validation_service
    
    def test_save_strategy_success(self, mock_dependencies):
        """전략 저장 성공 시나리오"""
        # Arrange
        mock_view, mock_strategy_service, mock_validation_service = mock_dependencies
        presenter = StrategyMakerPresenter(mock_view, mock_strategy_service, mock_validation_service)
        
        strategy_data = {
            'name': '테스트 전략',
            'entry_rules': [{'type': 'RSI', 'value': 30}],
            'exit_rules': [{'type': 'PROFIT_TARGET', 'value': 10}]
        }
        
        mock_validation_service.validate_strategy.return_value = True
        mock_strategy_service.create_strategy.return_value = 'strategy_001'
        
        # Act
        presenter.save_strategy(strategy_data)
        
        # Assert
        mock_validation_service.validate_strategy.assert_called_once_with(strategy_data)
        mock_strategy_service.create_strategy.assert_called_once_with(strategy_data)
        mock_view.show_success_message.assert_called_once()
        mock_view.clear_form.assert_called_once()
    
    def test_save_strategy_validation_error(self, mock_dependencies):
        """전략 검증 실패 시나리오"""
        # Arrange
        mock_view, mock_strategy_service, mock_validation_service = mock_dependencies
        presenter = StrategyMakerPresenter(mock_view, mock_strategy_service, mock_validation_service)
        
        strategy_data = {'name': '잘못된 전략'}
        validation_errors = ['진입 규칙이 없습니다', '청산 규칙이 없습니다']
        mock_validation_service.validate_strategy.side_effect = ValidationError(validation_errors)
        
        # Act
        presenter.save_strategy(strategy_data)
        
        # Assert
        mock_view.show_validation_errors.assert_called_once_with(validation_errors)
        mock_strategy_service.create_strategy.assert_not_called()
```

---

## 🎯 실무 적용 가이드

### ✅ 테스트 작성 순서 (실무 권장)
1. **핵심 비즈니스 로직**: Strategy, Indicator 계산
2. **데이터 계층**: Repository, Database 연동
3. **UI 로직**: Presenter, View Model
4. **통합 테스트**: 전체 워크플로

### 🔧 Mock 사용 가이드라인
- **외부 API**: 항상 Mock 처리
- **데이터베이스**: 단위 테스트에서는 Mock, 통합 테스트에서는 실제 DB
- **파일 시스템**: Mock 처리 권장
- **시간 관련**: `freezegun` 라이브러리 활용

### 📊 테스트 커버리지 목표
- **비즈니스 로직**: 90% 이상
- **데이터 계층**: 80% 이상
- **UI 계층**: 70% 이상 (Mock 중심)

---

**💡 다음 단계**: `tests/` 폴더에서 실제 테스트를 작성해보며 이 가이드를 참고하세요!
