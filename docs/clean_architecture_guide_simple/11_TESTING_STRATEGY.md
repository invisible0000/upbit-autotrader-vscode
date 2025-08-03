# 🧪 테스팅 전략 가이드

> **목적**: Clean Architecture에서 계층별 테스트 방법과 전략  
> **대상**: LLM 에이전트, 개발자  
> **갱신**: 2025-08-03

## 🎯 테스트 피라미드

### 테스트 계층 구조
```
    🔺 E2E Tests        ← 사용자 시나리오 (5%)
   ┌─────────────────┐
  ┌───────────────────┐
 ┌─────────────────────┐ Integration Tests ← 계층 간 통합 (25%)
┌───────────────────────┐
└─────────────────────────┘ Unit Tests ← 개별 클래스/함수 (70%)
```

### 계층별 테스트 목표
- **💎 Domain**: 비즈니스 로직 정확성 (외부 의존성 없음)
- **⚙️ Application**: 유스케이스 처리 흐름
- **🔌 Infrastructure**: 외부 시스템 연동 (Mock 활용)
- **🎨 Presentation**: UI 동작과 사용자 시나리오

## 💎 Domain Layer 테스트

### Entity 테스트
```python
import pytest
from datetime import datetime
from domain.entities import Strategy, TradingRule
from domain.exceptions import BusinessRuleViolationException

class TestStrategy:
    """전략 Entity 단위 테스트"""
    
    def test_create_strategy_success(self):
        """전략 생성 성공 테스트"""
        # Given
        strategy_name = "RSI 전략"
        
        # When
        strategy = Strategy(strategy_name)
        
        # Then
        assert strategy.name == strategy_name
        assert len(strategy.rules) == 0
        assert strategy.id is not None
        
    def test_add_rule_success(self):
        """규칙 추가 성공 테스트"""
        # Given
        strategy = Strategy("테스트 전략")
        rule = TradingRule("RSI", {"period": 14})
        
        # When
        strategy.add_rule(rule)
        
        # Then
        assert len(strategy.rules) == 1
        assert strategy.rules[0] == rule
        
    def test_add_rule_exceed_limit_fails(self):
        """규칙 개수 제한 초과 실패 테스트"""
        # Given
        strategy = Strategy("테스트 전략")
        
        # 10개 규칙 추가
        for i in range(10):
            rule = TradingRule(f"Rule_{i}", {})
            strategy.add_rule(rule)
            
        # When & Then
        with pytest.raises(BusinessRuleViolationException) as exc_info:
            extra_rule = TradingRule("Extra_Rule", {})
            strategy.add_rule(extra_rule)
            
        assert "최대_규칙_제한" in str(exc_info.value)
        
    def test_strategy_events_generated(self):
        """도메인 이벤트 발생 테스트"""
        # Given
        strategy = Strategy("테스트 전략")
        rule = TradingRule("RSI", {"period": 14})
        
        # When
        strategy.add_rule(rule)
        events = strategy.get_events()
        
        # Then
        assert len(events) == 1
        assert events[0].event_name == "RuleAddedEvent"
        assert events[0].strategy_id == strategy.id
```

### Value Object 테스트
```python
class TestTradingRule:
    """트레이딩 규칙 값 객체 테스트"""
    
    def test_create_rule_with_parameters(self):
        """파라미터가 있는 규칙 생성"""
        # Given
        rule_type = "RSI"
        parameters = {"period": 14, "overbought": 70}
        
        # When
        rule = TradingRule(rule_type, parameters)
        
        # Then
        assert rule.type == rule_type
        assert rule.parameters == parameters
        
    def test_rule_equality(self):
        """규칙 동등성 테스트"""
        # Given
        rule1 = TradingRule("RSI", {"period": 14})
        rule2 = TradingRule("RSI", {"period": 14})
        rule3 = TradingRule("MACD", {"period": 14})
        
        # Then
        assert rule1 == rule2
        assert rule1 != rule3
        
    def test_rule_immutability(self):
        """규칙 불변성 테스트"""
        # Given
        parameters = {"period": 14}
        rule = TradingRule("RSI", parameters)
        
        # When
        parameters["period"] = 20
        
        # Then
        assert rule.parameters["period"] == 14  # 원본 불변
```

## ⚙️ Application Layer 테스트

### Service 테스트 (Mock 활용)
```python
import pytest
from unittest.mock import Mock, patch
from application.services import StrategyService
from application.commands import CreateStrategyCommand
from domain.entities import Strategy

class TestStrategyService:
    """전략 서비스 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.mock_repo = Mock()
        self.mock_event_publisher = Mock()
        self.service = StrategyService(self.mock_repo, self.mock_event_publisher)
        
    def test_create_strategy_success(self):
        """전략 생성 성공 테스트"""
        # Given
        command = CreateStrategyCommand(
            name="RSI 전략",
            rules=[{"type": "RSI", "parameters": {"period": 14}}]
        )
        self.mock_repo.save.return_value = "strategy-123"
        
        # When
        result = self.service.create_strategy(command)
        
        # Then
        assert result.is_success
        assert result.value == "strategy-123"
        self.mock_repo.save.assert_called_once()
        self.mock_event_publisher.publish_all.assert_called_once()
        
    def test_create_strategy_validation_fails(self):
        """전략 생성 검증 실패 테스트"""
        # Given
        command = CreateStrategyCommand(name="", rules=[])  # 잘못된 입력
        
        # When
        result = self.service.create_strategy(command)
        
        # Then
        assert not result.is_success
        assert "전략 이름은 필수" in str(result.error)
        self.mock_repo.save.assert_not_called()
        
    def test_create_strategy_domain_exception_handled(self):
        """도메인 예외 처리 테스트"""
        # Given
        command = CreateStrategyCommand(
            name="테스트 전략",
            rules=[{"type": "RSI", "parameters": {"period": 14}}]
        )
        
        # Domain에서 예외 발생 시뮬레이션
        with patch('domain.entities.Strategy') as mock_strategy_class:
            mock_strategy = Mock()
            mock_strategy.add_rule.side_effect = BusinessRuleViolationException(
                "최대_규칙_제한", "규칙 개수 초과"
            )
            mock_strategy_class.return_value = mock_strategy
            
            # When
            result = self.service.create_strategy(command)
            
            # Then
            assert not result.is_success
            assert "비즈니스 규칙 위반" in str(result.error)
```

### Use Case 통합 테스트
```python
class TestCreateStrategyUseCase:
    """전략 생성 유스케이스 통합 테스트"""
    
    def setup_method(self):
        """실제 구현체로 테스트 설정"""
        self.db_connection = sqlite3.connect(":memory:")
        self.setup_test_database()
        
        self.strategy_repo = SqliteStrategyRepository(self.db_connection)
        self.event_publisher = InMemoryEventPublisher()
        self.service = StrategyService(self.strategy_repo, self.event_publisher)
        
    def setup_test_database(self):
        """테스트용 DB 스키마 생성"""
        cursor = self.db_connection.cursor()
        cursor.execute("""
            CREATE TABLE strategies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE strategy_rules (
                id INTEGER PRIMARY KEY,
                strategy_id TEXT,
                rule_data TEXT,
                FOREIGN KEY (strategy_id) REFERENCES strategies(id)
            )
        """)
        
    def test_end_to_end_strategy_creation(self):
        """전략 생성 전체 흐름 테스트"""
        # Given
        command = CreateStrategyCommand(
            name="RSI 과매도 전략",
            rules=[
                {"type": "RSI", "parameters": {"period": 14, "threshold": 30}},
                {"type": "SMA", "parameters": {"period": 20}}
            ]
        )
        
        # When
        result = self.service.create_strategy(command)
        
        # Then
        assert result.is_success
        strategy_id = result.value
        
        # DB에서 조회 검증
        saved_strategy = self.strategy_repo.get_by_id(strategy_id)
        assert saved_strategy.name == "RSI 과매도 전략"
        assert len(saved_strategy.rules) == 2
        
        # 이벤트 발행 검증
        # (실제로는 이벤트 핸들러 Mock으로 검증)
```

## 🔌 Infrastructure Layer 테스트

### Repository 테스트
```python
import tempfile
import os

class TestSqliteStrategyRepository:
    """SQLite 전략 리포지토리 테스트"""
    
    def setup_method(self):
        """테스트용 임시 DB 생성"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        self.repo = SqliteStrategyRepository(self.temp_db.name)
        self.repo._create_tables()  # 테이블 생성
        
    def teardown_method(self):
        """테스트 후 정리"""
        os.unlink(self.temp_db.name)
        
    def test_save_and_retrieve_strategy(self):
        """전략 저장 및 조회 테스트"""
        # Given
        strategy = Strategy("테스트 전략")
        rule = TradingRule("RSI", {"period": 14})
        strategy.add_rule(rule)
        
        # When
        saved_id = self.repo.save(strategy)
        retrieved_strategy = self.repo.get_by_id(saved_id)
        
        # Then
        assert retrieved_strategy.name == "테스트 전략"
        assert len(retrieved_strategy.rules) == 1
        assert retrieved_strategy.rules[0].type == "RSI"
        
    def test_get_nonexistent_strategy_raises_exception(self):
        """존재하지 않는 전략 조회 시 예외 발생"""
        # When & Then
        with pytest.raises(DatabaseException):
            self.repo.get_by_id("nonexistent-id")
```

### API 클라이언트 테스트
```python
import responses
import json

class TestUpbitApiClient:
    """업비트 API 클라이언트 테스트"""
    
    def setup_method(self):
        self.client = UpbitApiClient()
        
    @responses.activate
    def test_get_market_data_success(self):
        """시장 데이터 조회 성공 테스트"""
        # Given
        symbol = "KRW-BTC"
        mock_response = [{
            "market": "KRW-BTC",
            "trade_price": 50000000,
            "change": "RISE",
            "change_rate": 0.05
        }]
        
        responses.add(
            responses.GET,
            f"https://api.upbit.com/v1/ticker?markets={symbol}",
            json=mock_response,
            status=200
        )
        
        # When
        market_data = self.client.get_market_data(symbol)
        
        # Then
        assert market_data.symbol == "KRW-BTC"
        assert market_data.price == 50000000
        assert market_data.change_rate == 0.05
        
    @responses.activate
    def test_get_market_data_not_found(self):
        """존재하지 않는 심볼 조회 테스트"""
        # Given
        symbol = "INVALID-SYMBOL"
        responses.add(
            responses.GET,
            f"https://api.upbit.com/v1/ticker?markets={symbol}",
            status=404
        )
        
        # When & Then
        with pytest.raises(NetworkException) as exc_info:
            self.client.get_market_data(symbol)
            
        assert "존재하지 않는 심볼" in str(exc_info.value)
```

## 🎨 Presentation Layer 테스트

### Presenter 테스트
```python
class TestStrategyBuilderPresenter:
    """전략 빌더 Presenter 테스트"""
    
    def setup_method(self):
        self.mock_view = Mock()
        self.mock_service = Mock()
        self.presenter = StrategyBuilderPresenter(self.mock_view, self.mock_service)
        
    def test_create_strategy_success_updates_view(self):
        """전략 생성 성공 시 View 업데이트"""
        # Given
        strategy_data = {"name": "테스트 전략", "rules": []}
        self.mock_service.create_strategy.return_value = Result.success("strategy-123")
        
        # When
        self.presenter.create_strategy(strategy_data)
        
        # Then
        self.mock_view.show_success_message.assert_called_once()
        self.mock_view.refresh_strategy_list.assert_called_once()
        
    def test_create_strategy_validation_error_shows_warning(self):
        """검증 오류 시 경고 메시지 표시"""
        # Given
        strategy_data = {"name": "", "rules": []}
        validation_error = ValidationException("name", "전략 이름은 필수입니다")
        self.mock_service.create_strategy.return_value = Result.failure(validation_error)
        
        # When
        self.presenter.create_strategy(strategy_data)
        
        # Then
        self.mock_view.show_validation_error.assert_called_once_with(
            "name", "전략 이름은 필수입니다"
        )
```

### UI 위젯 테스트 (QTest 활용)
```python
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

class TestStrategyBuilderView:
    """전략 빌더 View 테스트"""
    
    @classmethod
    def setup_class(cls):
        """QApplication 생성"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
            
    def setup_method(self):
        self.view = StrategyBuilderView()
        self.mock_presenter = Mock()
        self.view.set_presenter(self.mock_presenter)
        
    def test_strategy_name_input_triggers_validation(self):
        """전략 이름 입력 시 검증 트리거"""
        # Given
        strategy_name = "RSI 전략"
        
        # When
        QTest.keyClicks(self.view.strategy_name_input, strategy_name)
        
        # Then
        assert self.view.strategy_name_input.text() == strategy_name
        
    def test_create_button_calls_presenter(self):
        """생성 버튼 클릭 시 Presenter 호출"""
        # Given
        self.view.strategy_name_input.setText("테스트 전략")
        
        # When
        QTest.mouseClick(self.view.create_button, Qt.MouseButton.LeftButton)
        
        # Then
        self.mock_presenter.create_strategy.assert_called_once()
        
    def test_show_validation_error_updates_ui(self):
        """검증 에러 표시 테스트"""
        # When
        self.view.show_validation_error("name", "이름이 너무 깁니다")
        
        # Then
        assert "border: 2px solid red" in self.view.strategy_name_input.styleSheet()
        assert "이름이 너무 깁니다" in self.view.strategy_name_input.toolTip()
```

## 🚀 테스트 자동화

### pytest 설정
```python
# conftest.py
import pytest
import sqlite3
import tempfile
from unittest.mock import Mock

@pytest.fixture
def temp_database():
    """임시 데이터베이스 픽스처"""
    temp_db = tempfile.NamedTemporaryFile(delete=False)
    temp_db.close()
    
    conn = sqlite3.connect(temp_db.name)
    # 테스트용 스키마 생성
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE strategies (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)
    conn.commit()
    
    yield temp_db.name
    
    conn.close()
    os.unlink(temp_db.name)

@pytest.fixture
def mock_event_publisher():
    """이벤트 발행자 Mock 픽스처"""
    return Mock()

@pytest.fixture
def sample_strategy():
    """샘플 전략 픽스처"""
    strategy = Strategy("샘플 전략")
    rule = TradingRule("RSI", {"period": 14})
    strategy.add_rule(rule)
    return strategy
```

### 테스트 커버리지
```bash
# 커버리지 측정 실행
pytest --cov=application --cov=domain --cov=infrastructure --cov-report=html

# 브랜치 커버리지 포함
pytest --cov=application --cov-branch --cov-report=term-missing
```

### CI/CD 파이프라인
```yaml
# .github/workflows/test.yml
name: Test Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
        
    - name: Run unit tests
      run: pytest tests/unit --cov=domain --cov=application
      
    - name: Run integration tests
      run: pytest tests/integration
      
    - name: Run E2E tests
      run: pytest tests/e2e
```

## 📊 테스트 품질 지표

### 커버리지 목표
- **Domain Layer**: 95% 이상 (핵심 비즈니스 로직)
- **Application Layer**: 90% 이상 (유스케이스)
- **Infrastructure Layer**: 80% 이상 (외부 연동)
- **Presentation Layer**: 70% 이상 (UI 로직)

### 테스트 실행 시간 목표
- **Unit Tests**: 전체 실행 10초 이내
- **Integration Tests**: 전체 실행 2분 이내
- **E2E Tests**: 전체 실행 10분 이내

## 📚 관련 문서

- [시스템 개요](01_SYSTEM_OVERVIEW.md): 테스트 대상 아키텍처 이해
- [계층별 책임](02_LAYER_RESPONSIBILITIES.md): 계층별 테스트 전략
- [에러 처리](10_ERROR_HANDLING.md): 예외 상황 테스트
- [문제 해결](06_TROUBLESHOOTING.md): 테스트 관련 문제 해결

---
**💡 핵심**: "테스트는 문서화의 한 형태입니다. 테스트 코드로 시스템의 의도를 명확히 표현하세요!"
