# TASK-20250803-15

## Title
System Integration - Clean Architecture 통합 테스트 및 검증

## Objective (목표)
모든 계층이 통합된 Clean Architecture 시스템의 종단간(E2E) 테스트를 수행하고, 의존성 방향과 계층 분리가 올바르게 구현되었는지 검증합니다. 기본 7규칙 전략을 통한 완전한 워크플로 검증을 포함합니다.

## Source of Truth (준거 문서)
'리팩토링 계획 브리핑 문서' - Section "Phase 5: 통합 테스트 및 최적화 (2주)" > "5.1 시스템 통합 테스트 (1주)"

## Pre-requisites (선행 조건)
- Phase 1-4 모든 태스크 완료
- Clean Architecture 5계층 구현 완료
- 기본 7규칙 전략 컴포넌트 준비

## Detailed Steps (상세 실행 절차)

### 1. **[환경 구성]** 통합 테스트 환경 설정
- [ ] `tests/integration/` 디렉토리 구조 생성:
```
tests/integration/
├── conftest.py              # 통합 테스트 설정
├── test_architecture_compliance.py  # 아키텍처 준수 테스트
├── test_e2e_basic_7_rules.py       # 7규칙 E2E 테스트
├── test_dependency_direction.py     # 의존성 방향 검증
├── test_layer_isolation.py         # 계층 격리 테스트
└── fixtures/                       # 테스트 데이터
    ├── sample_strategies.json
    └── test_market_data.csv
```

- [ ] `tests/integration/conftest.py` 설정:
```python
import pytest
from upbit_auto_trading.shared.dependency_injection import DIContainer
from upbit_auto_trading.infrastructure.database import DatabaseManager
from upbit_auto_trading.application.services import *

@pytest.fixture
def integration_container():
    """통합 테스트용 DI 컨테이너"""
    container = DIContainer()
    
    # 테스트용 데이터베이스 설정
    db_manager = DatabaseManager(":memory:")
    container.register_singleton(DatabaseManager, db_manager)
    
    # 모든 서비스 등록
    container.register(StrategyApplicationService)
    container.register(TriggerApplicationService)
    container.register(BacktestApplicationService)
    
    return container

@pytest.fixture
def sample_market_data():
    """샘플 시장 데이터"""
    return load_test_market_data()
```

### 2. **[아키텍처 검증]** Clean Architecture 준수 테스트
- [ ] `test_architecture_compliance.py` 작성:
```python
import ast
import os
from pathlib import Path

class ArchitectureComplianceTest:
    """Clean Architecture 준수 검증"""
    
    def test_dependency_direction_compliance(self):
        """의존성 방향 검증"""
        violations = []
        
        # Domain 계층은 다른 계층을 참조하면 안됨
        domain_violations = self._check_domain_dependencies()
        violations.extend(domain_violations)
        
        # Application은 Infrastructure를 직접 참조하면 안됨
        app_violations = self._check_application_dependencies()
        violations.extend(app_violations)
        
        assert len(violations) == 0, f"의존성 위반: {violations}"
    
    def test_layer_isolation(self):
        """계층 격리 검증"""
        # Presentation이 Domain을 직접 참조하지 않는지 확인
        presentation_files = self._get_python_files("presentation/")
        for file_path in presentation_files:
            imports = self._extract_imports(file_path)
            domain_imports = [imp for imp in imports if "domain" in imp]
            assert len(domain_imports) == 0, f"{file_path}에서 Domain 직접 참조"
    
    def _check_domain_dependencies(self) -> List[str]:
        """Domain 계층 의존성 검사"""
        domain_files = self._get_python_files("domain/")
        violations = []
        
        forbidden_imports = ["application", "infrastructure", "presentation"]
        
        for file_path in domain_files:
            imports = self._extract_imports(file_path)
            for imp in imports:
                if any(forbidden in imp for forbidden in forbidden_imports):
                    violations.append(f"{file_path}: {imp}")
        
        return violations
```

### 3. **[E2E 테스트]** 기본 7규칙 전략 완전 워크플로
- [ ] `test_e2e_basic_7_rules.py` 작성:
```python
class Basic7RulesE2ETest:
    """기본 7규칙 전략 종단간 테스트"""
    
    def test_complete_strategy_workflow(self, integration_container):
        """전체 전략 워크플로 테스트"""
        # Given: 서비스 준비
        strategy_service = integration_container.resolve(StrategyApplicationService)
        trigger_service = integration_container.resolve(TriggerApplicationService)
        backtest_service = integration_container.resolve(BacktestApplicationService)
        
        # When: 7규칙 전략 생성
        strategy_id = self._create_basic_7_rules_strategy(strategy_service, trigger_service)
        
        # Then: 전략이 올바르게 생성됨
        assert strategy_id is not None
        strategy = strategy_service.get_strategy(strategy_id)
        assert len(strategy.entry_rules) == 1  # RSI 진입
        assert len(strategy.management_rules) == 6  # 6개 관리 규칙
        
        # When: 백테스팅 실행
        backtest_result = backtest_service.run_backtest(
            BacktestCommand(
                strategy_id=strategy_id,
                symbol="KRW-BTC",
                start_date="2024-01-01",
                end_date="2024-12-31"
            )
        )
        
        # Then: 백테스팅 결과 검증
        assert backtest_result.total_trades > 0
        assert backtest_result.total_return is not None
        assert backtest_result.max_drawdown is not None
    
    def _create_basic_7_rules_strategy(self, strategy_service, trigger_service):
        """기본 7규칙 전략 생성"""
        # 1. RSI 과매도 진입 조건 생성
        rsi_condition = trigger_service.create_condition(
            CreateConditionCommand(
                name="RSI 과매도 진입",
                variable_id="RSI",
                variable_params={"period": 14},
                operator="<",
                target_value="30"
            )
        )
        
        # 2. 진입 전략 생성
        entry_strategy = strategy_service.create_entry_strategy(
            CreateEntryStrategyCommand(
                name="RSI 진입",
                conditions=[rsi_condition.id],
                action_type="BUY"
            )
        )
        
        # 3-7. 관리 전략들 생성 (불타기, 물타기, 익절, 손절, 급등감지, 급락감지)
        management_strategies = self._create_management_strategies(strategy_service, trigger_service)
        
        # 8. 전체 전략 조합
        strategy = strategy_service.create_combined_strategy(
            CreateCombinedStrategyCommand(
                name="기본 7규칙 전략",
                entry_strategy_id=entry_strategy.id,
                management_strategy_ids=[ms.id for ms in management_strategies]
            )
        )
        
        return strategy.id
```

### 4. **[성능 테스트]** 시스템 성능 검증
- [ ] `test_performance.py` 작성:
```python
import time
import psutil
import pytest

class PerformanceTest:
    """시스템 성능 테스트"""
    
    def test_strategy_creation_performance(self, integration_container):
        """전략 생성 성능 테스트"""
        strategy_service = integration_container.resolve(StrategyApplicationService)
        
        start_time = time.time()
        
        # 100개 전략 생성
        for i in range(100):
            strategy_service.create_strategy(self._get_sample_strategy_data(i))
        
        elapsed_time = time.time() - start_time
        
        # 100개 전략 생성이 5초 이내
        assert elapsed_time < 5.0, f"전략 생성 시간 초과: {elapsed_time}초"
    
    def test_backtest_memory_usage(self, integration_container):
        """백테스팅 메모리 사용량 테스트"""
        backtest_service = integration_container.resolve(BacktestApplicationService)
        
        # 메모리 사용량 측정 시작
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 1년 백테스팅 실행
        backtest_service.run_backtest(self._get_long_term_backtest_command())
        
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = end_memory - start_memory
        
        # 메모리 증가량이 500MB 이하
        assert memory_increase < 500, f"메모리 사용량 초과: {memory_increase}MB"
```

### 5. **[데이터 무결성]** 3-DB 아키텍처 검증
- [ ] `test_database_integrity.py` 작성:
```python
class DatabaseIntegrityTest:
    """데이터베이스 무결성 테스트"""
    
    def test_3db_isolation(self, integration_container):
        """3-DB 격리 검증"""
        db_manager = integration_container.resolve(DatabaseManager)
        
        # settings.sqlite3 - 구조 정의만
        settings_data = db_manager.get_settings_data()
        assert "trading_variables" in settings_data
        assert "variable_parameters" in settings_data
        
        # strategies.sqlite3 - 전략 인스턴스만
        strategies_data = db_manager.get_strategies_data()
        assert "strategies" in strategies_data
        assert "strategy_conditions" in strategies_data
        
        # market_data.sqlite3 - 시장 데이터만
        market_data = db_manager.get_market_data()
        assert "price_data" in market_data
        assert "indicator_cache" in market_data
    
    def test_referential_integrity(self, integration_container):
        """참조 무결성 검증"""
        strategy_service = integration_container.resolve(StrategyApplicationService)
        
        # 전략 생성
        strategy = strategy_service.create_strategy(self._get_sample_strategy())
        
        # 전략 삭제 시 관련 조건들도 삭제되는지 확인
        strategy_service.delete_strategy(strategy.id)
        
        # 고아 레코드가 없어야 함
        orphaned_conditions = strategy_service.get_orphaned_conditions()
        assert len(orphaned_conditions) == 0
```

### 6. **[UI 통합]** Presentation Layer 통합 테스트
- [ ] `test_ui_integration.py` 작성:
```python
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

class UIIntegrationTest:
    """UI 통합 테스트"""
    
    def test_mvp_pattern_integration(self, qtbot, integration_container):
        """MVP 패턴 통합 테스트"""
        # Given: View와 Presenter 생성
        view_factory = integration_container.resolve(ViewFactory)
        strategy_view = view_factory.create_strategy_maker_view()
        
        qtbot.addWidget(strategy_view)
        
        # When: 사용자 입력 시뮬레이션
        strategy_view.name_input.setText("테스트 전략")
        strategy_view.description_input.setText("통합 테스트용 전략")
        
        QTest.mouseClick(strategy_view.save_button, Qt.MouseButton.LeftButton)
        
        # Then: 전략이 저장되고 목록에 표시됨
        qtbot.waitUntil(lambda: "테스트 전략" in strategy_view.get_strategy_list())
    
    def test_event_driven_ui_updates(self, qtbot, integration_container):
        """이벤트 기반 UI 갱신 테스트"""
        ui_event_handler = integration_container.resolve(UIEventHandler)
        progress_widget = ProgressChartWidget()
        
        # 백테스팅 진행 이벤트 발행
        progress_event = BacktestProgressEvent(
            strategy_id="test-strategy",
            progress_percent=50.0,
            current_date="2024-06-15",
            interim_results={"return": 5.2}
        )
        
        ui_event_handler.publish(progress_event)
        
        # UI가 업데이트되었는지 확인
        assert progress_widget.progress_bar.value() == 50
        assert "2024-06-15" in progress_widget.status_label.text()
```

## Verification Criteria (완료 검증 조건)

### **[아키텍처 준수]**
- [ ] 모든 의존성이 안쪽 방향으로만 흐름
- [ ] Domain 계층이 다른 계층을 참조하지 않음
- [ ] Presentation이 Domain을 직접 참조하지 않음

### **[기능 검증]**
- [ ] 기본 7규칙 전략 완전 워크플로 성공
- [ ] 모든 계층 간 통신이 올바르게 동작
- [ ] UI와 백엔드 로직이 완전 분리됨

### **[성능 기준]**
- [ ] 전략 생성 시간 100ms 이하
- [ ] 백테스팅 메모리 사용량 500MB 이하
- [ ] UI 응답 시간 100ms 이하

## Notes (주의사항)
- 통합 테스트는 실제 데이터베이스가 아닌 메모리 DB 사용
- UI 테스트 시 QApplication 초기화 필요
- 성능 테스트는 CI 환경 고려하여 기준 조정
