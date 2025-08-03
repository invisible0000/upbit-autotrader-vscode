# 🧪 테스팅 전략

> **목적**: Clean Architecture에서 계층별 테스트 방법과 전략  
> **대상**: 개발자, QA 엔지니어  
> **예상 읽기 시간**: 22분

## 🎯 Clean Architecture 테스트 피라미드

### 📊 테스트 구조
```
      🔺 E2E Tests (느림, 적음)
     ┌─────────────────────────┐
    ┌─────────────────────────────┐
   ┌───────────────────────────────┐  Integration Tests (보통, 중간)
  ┌─────────────────────────────────┐
 ┌───────────────────────────────────┐ Unit Tests (빠름, 많음)
└───────────────────────────────────┘
```

### 🎯 계층별 테스트 비율
```python
TEST_DISTRIBUTION = {
    "Unit Tests": "70%",        # Domain + Application 로직 중심
    "Integration Tests": "20%", # Infrastructure 연동
    "E2E Tests": "10%"         # 전체 시나리오
}

# 계층별 테스트 우선순위
LAYER_TEST_PRIORITY = {
    "Domain": "최고 (비즈니스 로직)",
    "Application": "높음 (유스케이스)",
    "Infrastructure": "중간 (기술 구현)",
    "Presentation": "낮음 (UI 상호작용)"
}
```

## 💎 Domain Layer 테스팅

### 1. 엔티티 테스트
```python
# tests/domain/entities/test_trading_condition.py
import pytest
from domain.entities.trading_condition import TradingCondition
from domain.entities.trading_variable import TradingVariable
from domain.exceptions import InvalidOperatorError, IncompatibleValueError

class TestTradingCondition:
    """TradingCondition 엔티티 테스트"""
    
    def setup_method(self):
        """테스트 전 설정"""
        self.rsi_variable = TradingVariable(
            variable_id="RSI",
            name="RSI 지표",
            purpose_category="momentum",
            comparison_group="percentage_comparable"
        )
    
    def test_create_valid_condition_success(self):
        """✅ 유효한 조건 생성 성공"""
        # Given
        operator = ">"
        target_value = "70"
        
        # When
        condition = TradingCondition.create(
            variable=self.rsi_variable,
            operator=operator,
            target_value=target_value
        )
        
        # Then
        assert condition.id is not None
        assert condition.variable == self.rsi_variable
        assert condition.operator == operator
        assert condition.target_value == target_value
        assert len(condition.get_uncommitted_events()) == 1
        assert condition.get_uncommitted_events()[0].__class__.__name__ == "ConditionCreatedEvent"
    
    def test_create_invalid_operator_fails(self):
        """❌ 잘못된 연산자로 조건 생성 실패"""
        # Given
        invalid_operator = "@@"
        
        # When & Then
        with pytest.raises(InvalidOperatorError) as exc_info:
            TradingCondition.create(
                variable=self.rsi_variable,
                operator=invalid_operator,
                target_value="70"
            )
        
        assert "지원하지 않는 연산자" in str(exc_info.value)
    
    def test_create_incompatible_value_fails(self):
        """❌ 호환되지 않는 값으로 조건 생성 실패"""
        # Given
        incompatible_value = "invalid_percentage"
        
        # When & Then
        with pytest.raises(IncompatibleValueError):
            TradingCondition.create(
                variable=self.rsi_variable,
                operator=">",
                target_value=incompatible_value
            )
    
    def test_business_rule_validation(self):
        """🔍 비즈니스 규칙 검증"""
        # RSI는 0-100 범위 값만 허용
        valid_values = ["0", "50", "100"]
        invalid_values = ["-10", "150", "abc"]
        
        for value in valid_values:
            condition = TradingCondition.create(
                variable=self.rsi_variable,
                operator=">",
                target_value=value
            )
            assert condition is not None
        
        for value in invalid_values:
            with pytest.raises(IncompatibleValueError):
                TradingCondition.create(
                    variable=self.rsi_variable,
                    operator=">",
                    target_value=value
                )
    
    def test_domain_events_generation(self):
        """📤 도메인 이벤트 생성 테스트"""
        # Given
        condition = TradingCondition.create(
            variable=self.rsi_variable,
            operator=">",
            target_value="70"
        )
        
        # When
        events = condition.get_uncommitted_events()
        
        # Then
        assert len(events) == 1
        
        event = events[0]
        assert event.condition_id == condition.id
        assert event.variable_id == self.rsi_variable.variable_id
        assert event.occurred_at is not None
        
        # 이벤트 커밋 후 확인
        condition.mark_events_as_committed()
        assert len(condition.get_uncommitted_events()) == 0
```

### 2. 도메인 서비스 테스트
```python
# tests/domain/services/test_compatibility_checker.py
class TestCompatibilityChecker:
    """호환성 검증 도메인 서비스 테스트"""
    
    def setup_method(self):
        self.checker = CompatibilityChecker()
        
        # 테스트용 변수들
        self.rsi_variable = TradingVariable(
            variable_id="RSI",
            comparison_group="percentage_comparable"
        )
        
        self.sma_variable = TradingVariable(
            variable_id="SMA",
            comparison_group="price_comparable"
        )
        
        self.close_variable = TradingVariable(
            variable_id="Close",
            comparison_group="price_comparable"
        )
    
    def test_same_group_variables_compatible(self):
        """✅ 같은 그룹 변수들은 호환됨"""
        # When
        result = self.checker.check_compatibility(
            self.sma_variable, 
            self.close_variable
        )
        
        # Then
        assert result.is_compatible
        assert result.warning_message is None
    
    def test_different_group_variables_incompatible(self):
        """❌ 다른 그룹 변수들은 비호환"""
        # When
        result = self.checker.check_compatibility(
            self.rsi_variable,
            self.sma_variable
        )
        
        # Then
        assert not result.is_compatible
        assert "비교할 수 없습니다" in result.error_message
    
    def test_price_vs_percentage_with_normalization(self):
        """⚠️ 가격-백분율 비교는 정규화와 함께 경고"""
        # 특별 케이스: 가격과 백분율 지표 비교
        result = self.checker.check_compatibility_with_normalization(
            self.close_variable,
            self.rsi_variable
        )
        
        assert result.is_compatible  # 정규화로 가능
        assert result.requires_normalization
        assert "정규화" in result.warning_message

# 도메인 서비스 Mock 테스트
class TestCompatibilityCheckerWithMocks:
    """Mock을 사용한 도메인 서비스 테스트"""
    
    def test_external_dependency_isolation(self):
        """외부 의존성 격리 테스트"""
        # Given
        mock_variable_repo = Mock(spec=VariableRepository)
        mock_variable_repo.find_by_id.return_value = self.rsi_variable
        
        checker = CompatibilityChecker(variable_repo=mock_variable_repo)
        
        # When
        result = checker.check_compatibility_by_id("RSI", "SMA")
        
        # Then
        mock_variable_repo.find_by_id.assert_called_with("RSI")
        assert result is not None
```

## ⚙️ Application Layer 테스팅

### 1. 서비스 테스트
```python
# tests/application/services/test_condition_creation_service.py
class TestConditionCreationService:
    """조건 생성 서비스 테스트"""
    
    def setup_method(self):
        # Mock dependencies
        self.mock_condition_repo = Mock(spec=ConditionRepository)
        self.mock_variable_repo = Mock(spec=VariableRepository)
        self.mock_unit_of_work = Mock(spec=UnitOfWork)
        self.mock_event_publisher = Mock(spec=EventPublisher)
        
        # Service under test
        self.service = ConditionCreationService(
            condition_repo=self.mock_condition_repo,
            variable_repo=self.mock_variable_repo,
            unit_of_work=self.mock_unit_of_work,
            event_publisher=self.mock_event_publisher
        )
        
        # Test data
        self.rsi_variable = TradingVariable(
            variable_id="RSI",
            name="RSI 지표"
        )
    
    def test_create_condition_success(self):
        """✅ 조건 생성 성공 시나리오"""
        # Given
        command = CreateConditionCommand(
            variable_id="RSI",
            operator=">",
            target_value="70",
            name="RSI 과매수"
        )
        
        # Mock setup
        self.mock_variable_repo.find_by_id.return_value = self.rsi_variable
        self.mock_condition_repo.save.return_value = Mock(id="condition-123")
        self.mock_unit_of_work.transaction.return_value.__enter__ = Mock()
        self.mock_unit_of_work.transaction.return_value.__exit__ = Mock(return_value=None)
        
        # When
        result = self.service.create_condition(command)
        
        # Then
        assert result.success
        assert result.data.condition_id == "condition-123"
        
        # Verify interactions
        self.mock_variable_repo.find_by_id.assert_called_once_with("RSI")
        self.mock_condition_repo.save.assert_called_once()
        self.mock_event_publisher.publish.assert_called()
    
    def test_create_condition_variable_not_found(self):
        """❌ 변수 없음으로 인한 실패"""
        # Given
        command = CreateConditionCommand(
            variable_id="UNKNOWN",
            operator=">",
            target_value="70"
        )
        
        self.mock_variable_repo.find_by_id.return_value = None
        
        # When
        result = self.service.create_condition(command)
        
        # Then
        assert not result.success
        assert "존재하지 않는 변수" in result.error
        self.mock_condition_repo.save.assert_not_called()
    
    def test_create_condition_domain_exception(self):
        """❌ 도메인 규칙 위반으로 인한 실패"""
        # Given
        command = CreateConditionCommand(
            variable_id="RSI",
            operator="INVALID",
            target_value="70"
        )
        
        self.mock_variable_repo.find_by_id.return_value = self.rsi_variable
        
        # When
        result = self.service.create_condition(command)
        
        # Then
        assert not result.success
        assert "비즈니스 규칙 위반" in result.error
    
    def test_create_condition_transaction_rollback(self):
        """💥 트랜잭션 롤백 시나리오"""
        # Given
        command = CreateConditionCommand(
            variable_id="RSI",
            operator=">",
            target_value="70"
        )
        
        self.mock_variable_repo.find_by_id.return_value = self.rsi_variable
        self.mock_condition_repo.save.side_effect = Exception("DB Error")
        
        # When
        result = self.service.create_condition(command)
        
        # Then
        assert not result.success
        assert "시스템 오류" in result.error
        
        # 이벤트는 발행되지 않아야 함
        self.mock_event_publisher.publish.assert_not_called()
```

### 2. 쿼리 핸들러 테스트
```python
# tests/application/queries/test_condition_list_query_handler.py
class TestConditionListQueryHandler:
    """조건 목록 쿼리 핸들러 테스트"""
    
    def setup_method(self):
        self.mock_condition_repo = Mock(spec=ConditionRepository)
        self.handler = ConditionListQueryHandler(self.mock_condition_repo)
    
    def test_handle_empty_list(self):
        """📋 빈 목록 조회"""
        # Given
        query = GetConditionListQuery()
        self.mock_condition_repo.find_all.return_value = []
        
        # When
        result = self.handler.handle(query)
        
        # Then
        assert result.success
        assert len(result.data.conditions) == 0
    
    def test_handle_filtered_list(self):
        """🔍 필터링된 목록 조회"""
        # Given
        query = GetConditionListQuery(variable_id="RSI")
        mock_conditions = [
            Mock(variable=Mock(variable_id="RSI")),
            Mock(variable=Mock(variable_id="RSI"))
        ]
        self.mock_condition_repo.find_by_variable.return_value = mock_conditions
        
        # When
        result = self.handler.handle(query)
        
        # Then
        assert result.success
        assert len(result.data.conditions) == 2
        self.mock_condition_repo.find_by_variable.assert_called_once_with("RSI")
```

## 🔌 Infrastructure Layer 테스팅

### 1. Repository 테스트
```python
# tests/infrastructure/repositories/test_sqlite_condition_repository.py
import pytest
import sqlite3
from infrastructure.repositories.sqlite_condition_repository import SQLiteConditionRepository

class TestSQLiteConditionRepository:
    """SQLite 조건 Repository 테스트"""
    
    def setup_method(self):
        # In-memory 테스트 DB
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        
        # 테스트 스키마 생성
        self._create_test_schema()
        
        # Repository 인스턴스
        self.repo = SQLiteConditionRepository(self.connection)
        
        # 테스트 데이터
        self.test_condition = TradingCondition.create(
            variable=TradingVariable("RSI", "RSI 지표"),
            operator=">",
            target_value="70"
        )
    
    def _create_test_schema(self):
        """테스트용 스키마 생성"""
        self.connection.execute("""
            CREATE TABLE trading_conditions (
                id TEXT PRIMARY KEY,
                variable_id TEXT NOT NULL,
                variable_params TEXT,
                operator TEXT NOT NULL,
                target_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.connection.execute("""
            CREATE TABLE trading_variables (
                variable_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                purpose_category TEXT NOT NULL,
                comparison_group TEXT NOT NULL
            )
        """)
        
        # 테스트용 변수 삽입
        self.connection.execute("""
            INSERT INTO trading_variables 
            (variable_id, name, purpose_category, comparison_group)
            VALUES ('RSI', 'RSI 지표', 'momentum', 'percentage_comparable')
        """)
    
    def test_save_new_condition_success(self):
        """✅ 새 조건 저장 성공"""
        # When
        saved_condition = self.repo.save(self.test_condition)
        
        # Then
        assert saved_condition.id == self.test_condition.id
        
        # DB에서 확인
        cursor = self.connection.execute(
            "SELECT * FROM trading_conditions WHERE id = ?",
            (self.test_condition.id.value,)
        )
        row = cursor.fetchone()
        
        assert row is not None
        assert row['variable_id'] == "RSI"
        assert row['operator'] == ">"
        assert row['target_value'] == "70"
    
    def test_find_by_id_existing_condition(self):
        """🔍 존재하는 조건 조회"""
        # Given - 조건을 미리 저장
        self.repo.save(self.test_condition)
        
        # When
        found_condition = self.repo.find_by_id(self.test_condition.id)
        
        # Then
        assert found_condition is not None
        assert found_condition.id == self.test_condition.id
        assert found_condition.variable.variable_id == "RSI"
        assert found_condition.operator == ">"
        assert found_condition.target_value == "70"
    
    def test_find_by_id_non_existing_condition(self):
        """❌ 존재하지 않는 조건 조회"""
        # Given
        non_existing_id = ConditionId("non-existing")
        
        # When
        result = self.repo.find_by_id(non_existing_id)
        
        # Then
        assert result is None
    
    def test_find_all_conditions(self):
        """📋 모든 조건 조회"""
        # Given - 여러 조건 저장
        condition1 = self.test_condition
        condition2 = TradingCondition.create(
            variable=TradingVariable("RSI", "RSI 지표"),
            operator="<",
            target_value="30"
        )
        
        self.repo.save(condition1)
        self.repo.save(condition2)
        
        # When
        all_conditions = self.repo.find_all()
        
        # Then
        assert len(all_conditions) == 2
        condition_ids = [c.id for c in all_conditions]
        assert condition1.id in condition_ids
        assert condition2.id in condition_ids
    
    def test_delete_condition(self):
        """🗑️ 조건 삭제"""
        # Given
        self.repo.save(self.test_condition)
        
        # When
        self.repo.delete(self.test_condition.id)
        
        # Then
        found_condition = self.repo.find_by_id(self.test_condition.id)
        assert found_condition is None
        
        # DB에서도 확인
        cursor = self.connection.execute(
            "SELECT COUNT(*) as count FROM trading_conditions WHERE id = ?",
            (self.test_condition.id.value,)
        )
        assert cursor.fetchone()['count'] == 0
```

### 2. API 클라이언트 테스트
```python
# tests/infrastructure/api_clients/test_upbit_api_client.py
import responses
from infrastructure.api_clients.upbit_api_client import UpbitApiClient

class TestUpbitApiClient:
    """업비트 API 클라이언트 테스트"""
    
    def setup_method(self):
        self.client = UpbitApiClient(
            access_key="test_access_key",
            secret_key="test_secret_key"
        )
    
    @responses.activate
    def test_get_candle_data_success(self):
        """✅ 캔들 데이터 조회 성공"""
        # Given
        mock_response = [
            {
                "market": "KRW-BTC",
                "candle_date_time_utc": "2024-01-01T00:00:00",
                "candle_date_time_kst": "2024-01-01T09:00:00",
                "opening_price": 50000000.0,
                "high_price": 51000000.0,
                "low_price": 49000000.0,
                "trade_price": 50500000.0,
                "candle_acc_trade_volume": 100.5
            }
        ]
        
        responses.add(
            responses.GET,
            "https://api.upbit.com/v1/candles/minutes/1",
            json=mock_response,
            status=200
        )
        
        # When
        result = self.client.get_candle_data("KRW-BTC", "1m", 1)
        
        # Then
        assert len(result) == 1
        assert result[0]['market'] == "KRW-BTC"
        assert result[0]['trade_price'] == 50500000.0
    
    @responses.activate
    def test_get_candle_data_api_error(self):
        """❌ API 오류 처리"""
        # Given
        responses.add(
            responses.GET,
            "https://api.upbit.com/v1/candles/minutes/1",
            json={"error": {"name": "RATE_LIMIT_EXCEEDED"}},
            status=429
        )
        
        # When & Then
        with pytest.raises(UpbitApiError) as exc_info:
            self.client.get_candle_data("KRW-BTC", "1m", 1)
        
        assert "429" in str(exc_info.value)
    
    def test_authentication_header_generation(self):
        """🔐 인증 헤더 생성 테스트"""
        # When
        headers = self.client._generate_auth_headers("GET", "/v1/test", {})
        
        # Then
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")
```

## 🧪 통합 테스트

### 1. 전체 유스케이스 테스트
```python
# tests/integration/test_condition_creation_integration.py
class TestConditionCreationIntegration:
    """조건 생성 통합 테스트"""
    
    def setup_method(self):
        # 실제 DB 사용 (테스트용)
        self.db_path = ":memory:"
        self.db_manager = DatabaseManager(self.db_path)
        self._setup_test_database()
        
        # 실제 구현체들 사용
        self.condition_repo = SQLiteConditionRepository(self.db_manager.connection)
        self.variable_repo = SQLiteVariableRepository(self.db_manager.connection)
        self.unit_of_work = SQLiteUnitOfWork(self.db_manager.connection)
        self.event_publisher = InMemoryEventPublisher()
        
        # Service
        self.service = ConditionCreationService(
            condition_repo=self.condition_repo,
            variable_repo=self.variable_repo,
            unit_of_work=self.unit_of_work,
            event_publisher=self.event_publisher
        )
    
    def _setup_test_database(self):
        """테스트 DB 스키마 및 데이터 설정"""
        # 스키마 생성
        with open("data_info/upbit_autotrading_schema_strategies.sql") as f:
            schema_sql = f.read()
            self.db_manager.connection.executescript(schema_sql)
        
        # 테스트 변수 삽입
        self.db_manager.connection.execute("""
            INSERT INTO trading_variables 
            (variable_id, name, purpose_category, comparison_group)
            VALUES ('RSI', 'RSI 지표', 'momentum', 'percentage_comparable')
        """)
        self.db_manager.connection.commit()
    
    def test_end_to_end_condition_creation(self):
        """🔄 End-to-End 조건 생성 테스트"""
        # Given
        command = CreateConditionCommand(
            variable_id="RSI",
            operator=">",
            target_value="70",
            name="RSI 과매수 감지"
        )
        
        # When
        result = self.service.create_condition(command)
        
        # Then
        assert result.success
        
        # DB에서 실제로 저장되었는지 확인
        saved_condition = self.condition_repo.find_by_id(
            ConditionId(result.data.condition_id)
        )
        assert saved_condition is not None
        assert saved_condition.variable.variable_id == "RSI"
        
        # 이벤트가 발행되었는지 확인
        published_events = self.event_publisher.get_published_events()
        assert len(published_events) == 1
        assert published_events[0].__class__.__name__ == "ConditionCreatedEvent"
    
    def test_transaction_rollback_on_error(self):
        """💥 오류 시 트랜잭션 롤백 확인"""
        # Given - 잘못된 변수 ID
        command = CreateConditionCommand(
            variable_id="UNKNOWN",
            operator=">",
            target_value="70"
        )
        
        # When
        result = self.service.create_condition(command)
        
        # Then
        assert not result.success
        
        # DB에 저장되지 않았는지 확인
        all_conditions = self.condition_repo.find_all()
        assert len(all_conditions) == 0
        
        # 이벤트도 발행되지 않았는지 확인
        published_events = self.event_publisher.get_published_events()
        assert len(published_events) == 0
```

### 2. 성능 테스트
```python
# tests/performance/test_condition_performance.py
import time
import pytest

class TestConditionPerformance:
    """조건 처리 성능 테스트"""
    
    def test_bulk_condition_creation_performance(self):
        """📊 대량 조건 생성 성능"""
        # Given
        num_conditions = 1000
        commands = [
            CreateConditionCommand(
                variable_id="RSI",
                operator=">",
                target_value=str(50 + i % 50),
                name=f"조건_{i}"
            )
            for i in range(num_conditions)
        ]
        
        # When
        start_time = time.time()
        
        results = []
        for command in commands:
            result = self.service.create_condition(command)
            results.append(result)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Then
        successful_results = [r for r in results if r.success]
        assert len(successful_results) == num_conditions
        
        # 성능 기준: 1000개 조건을 10초 내에 생성
        assert execution_time < 10.0, f"성능 기준 미달: {execution_time:.2f}초"
        
        # 평균 처리 시간
        avg_time_per_condition = execution_time / num_conditions
        assert avg_time_per_condition < 0.01, f"평균 처리시간 초과: {avg_time_per_condition:.4f}초"
    
    def test_query_performance_with_large_dataset(self):
        """🔍 대용량 데이터 조회 성능"""
        # Given - 대량 데이터 생성
        self._create_large_dataset(5000)
        
        # When
        start_time = time.time()
        all_conditions = self.condition_repo.find_all()
        end_time = time.time()
        
        # Then
        assert len(all_conditions) == 5000
        
        query_time = end_time - start_time
        assert query_time < 1.0, f"조회 성능 기준 미달: {query_time:.2f}초"
```

## 🎨 Presentation Layer 테스팅

### 1. Presenter 테스트
```python
# tests/presentation/presenters/test_condition_builder_presenter.py
class TestConditionBuilderPresenter:
    """조건 빌더 Presenter 테스트"""
    
    def setup_method(self):
        # Mock dependencies
        self.mock_view = Mock(spec=ConditionBuilderView)
        self.mock_service = Mock(spec=ConditionCreationService)
        
        # Presenter under test
        self.presenter = ConditionBuilderPresenter(
            view=self.mock_view,
            condition_service=self.mock_service
        )
    
    def test_handle_create_condition_success(self):
        """✅ 조건 생성 성공 처리"""
        # Given
        form_data = {
            'variable_id': 'RSI',
            'operator': '>',
            'target_value': '70',
            'name': 'RSI 과매수'
        }
        
        mock_result = Result.ok(CreateConditionResult("condition-123"))
        self.mock_service.create_condition.return_value = mock_result
        
        # When
        self.presenter.handle_create_condition(form_data)
        
        # Then
        self.mock_service.create_condition.assert_called_once()
        self.mock_view.show_success_message.assert_called_once()
        self.mock_view.clear_form.assert_called_once()
        self.mock_view.refresh_condition_list.assert_called_once()
    
    def test_handle_create_condition_failure(self):
        """❌ 조건 생성 실패 처리"""
        # Given
        form_data = {'variable_id': 'INVALID'}
        
        mock_result = Result.fail("존재하지 않는 변수입니다")
        self.mock_service.create_condition.return_value = mock_result
        
        # When
        self.presenter.handle_create_condition(form_data)
        
        # Then
        self.mock_view.show_error_message.assert_called_once_with(
            "존재하지 않는 변수입니다"
        )
        self.mock_view.clear_form.assert_not_called()
```

### 2. UI 통합 테스트 (pytest-qt 사용)
```python
# tests/ui/test_condition_builder_ui.py
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from presentation.views.condition_builder_view import ConditionBuilderView

@pytest.fixture
def condition_builder_view(qtbot):
    """조건 빌더 View 픽스처"""
    view = ConditionBuilderView()
    qtbot.addWidget(view)
    return view

class TestConditionBuilderUI:
    """조건 빌더 UI 테스트"""
    
    def test_form_validation_invalid_input(self, qtbot, condition_builder_view):
        """❌ 잘못된 입력에 대한 폼 검증"""
        # Given
        view = condition_builder_view
        
        # When - 필수 필드 비워두고 생성 버튼 클릭
        QTest.mouseClick(view.create_button, Qt.MouseButton.LeftButton)
        
        # Then - 오류 메시지 표시 확인
        qtbot.wait(100)  # UI 업데이트 대기
        assert view.error_label.isVisible()
        assert "필수 필드" in view.error_label.text()
    
    def test_form_submission_valid_input(self, qtbot, condition_builder_view):
        """✅ 유효한 입력으로 폼 제출"""
        # Given
        view = condition_builder_view
        
        # 폼 데이터 입력
        view.variable_combo.setCurrentText("RSI")
        view.operator_combo.setCurrentText(">")
        view.target_value_input.setText("70")
        view.condition_name_input.setText("RSI 과매수")
        
        # When
        QTest.mouseClick(view.create_button, Qt.MouseButton.LeftButton)
        
        # Then - 신호 발행 확인
        assert view.condition_created.was_emitted()
        
        # 폼 데이터 확인
        emitted_data = view.condition_created.last_emission
        assert emitted_data['variable_id'] == 'RSI'
        assert emitted_data['operator'] == '>'
        assert emitted_data['target_value'] == '70'
```

## 🔄 테스트 자동화

### 1. pytest 설정
```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=upbit_auto_trading
    --cov-report=html
    --cov-report=term-missing

markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    performance: Performance tests
```

### 2. 테스트 환경 구성
```python
# conftest.py
import pytest
import tempfile
import os
from unittest.mock import Mock

@pytest.fixture(scope="session")
def test_database():
    """테스트용 임시 데이터베이스"""
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as f:
        db_path = f.name
    
    # 스키마 생성
    # ... 스키마 설정 코드 ...
    
    yield db_path
    
    # 정리
    os.unlink(db_path)

@pytest.fixture
def mock_upbit_client():
    """Mock 업비트 클라이언트"""
    mock_client = Mock(spec=UpbitApiClient)
    mock_client.get_candle_data.return_value = [
        {
            "market": "KRW-BTC",
            "trade_price": 50000000.0,
            "candle_date_time_kst": "2024-01-01T09:00:00"
        }
    ]
    return mock_client

@pytest.fixture(autouse=True)
def clean_domain_events():
    """각 테스트 후 도메인 이벤트 정리"""
    yield
    # 전역 이벤트 저장소 정리
    DomainEventDispatcher.clear_all_events()
```

### 3. CI/CD 파이프라인 테스트
```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-qt
    
    - name: Run unit tests
      run: pytest tests/unit -m "not slow"
    
    - name: Run integration tests  
      run: pytest tests/integration
    
    - name: Run performance tests
      run: pytest tests/performance -m performance
    
    - name: Generate coverage report
      run: pytest --cov=./ --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
```

## 🎯 테스트 베스트 프랙티스

### 1. 테스트 작성 가이드
```python
# ✅ 좋은 테스트
def test_create_condition_with_invalid_operator_should_raise_domain_exception():
    """명확한 테스트명: 무엇을_언제_어떤결과"""
    # Given (준비)
    invalid_operator = "@@"
    
    # When (실행) & Then (검증)
    with pytest.raises(InvalidOperatorError) as exc_info:
        TradingCondition.create(
            variable=rsi_variable,
            operator=invalid_operator,
            target_value="70"
        )
    
    assert "지원하지 않는 연산자" in str(exc_info.value)

# ❌ 나쁜 테스트
def test_condition():
    condition = TradingCondition.create(...)
    assert condition is not None  # 모호한 검증
```

### 2. Mock 사용 가이드
```python
# ✅ 적절한 Mock 사용
class TestConditionService:
    def test_create_condition_calls_repository_correctly(self):
        # Mock은 외부 의존성(Repository)에만 사용
        mock_repo = Mock(spec=ConditionRepository)
        service = ConditionService(condition_repo=mock_repo)
        
        # 실제 Domain 객체 사용 (Mock 하지 않음)
        result = service.create_condition(valid_command)
        
        # 상호작용 검증
        mock_repo.save.assert_called_once()

# ❌ 과도한 Mock 사용
def test_with_too_many_mocks():
    # Domain 객체까지 Mock하면 테스트 의미 없음
    mock_condition = Mock(spec=TradingCondition)
    mock_variable = Mock(spec=TradingVariable)
    # ...
```

## 🔍 다음 단계

- **[성능 최적화](10_PERFORMANCE_OPTIMIZATION.md)**: 테스트에서 발견된 성능 이슈 해결
- **[배포 및 마이그레이션](17_DEPLOYMENT_MIGRATION.md)**: 프로덕션 환경 테스트
- **[디버깅 가이드](15_DEBUGGING_GUIDE.md)**: 테스트 실패 시 디버깅 방법

---
**💡 핵심**: "Clean Architecture에서는 Domain 로직을 중심으로 테스트하고, 외부 의존성만 Mock을 사용합니다!"
