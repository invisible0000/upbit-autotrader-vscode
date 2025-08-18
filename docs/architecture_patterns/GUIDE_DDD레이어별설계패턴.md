# GUIDE_DDD레이어별설계패턴

**목적**: DDD 4계층 기반 매매시스템 설계패턴 및 확장성 가이드
**범위**: 데이터 저장구조 + 변수확장 + 레이어별 테스트 전략
**대상**: 트리거빌더 → 전략메이커 → 포지션관리 전체 흐름

---

## 🎯 **DDD 레이어별 책임과 데이터 설계 (1-30줄)**

### **4계층 데이터 흐름 설계**
```yaml
Presentation Layer (UI):
├── 책임: 사용자 입력/출력, 화면 상태 관리
├── 데이터: UI 상태, 폼 데이터, 화면 설정
└── 저장: 로컬 설정, 세션 데이터

Application Layer (Use Cases):
├── 책임: 비즈니스 워크플로, 외부 서비스 조정
├── 데이터: 작업 상태, 실행 로그, 성능 메트릭
└── 저장: 작업 히스토리, 실행 결과

Domain Layer (비즈니스 로직):
├── 책임: 순수 비즈니스 규칙, 도메인 엔티티
├── 데이터: 전략 규칙, 계산 공식, 검증 로직
└── 저장: 없음 (Infrastructure가 대행)

Infrastructure Layer (외부 연동):
├── 책임: 데이터 영속화, 외부 API, 기술적 구현
├── 데이터: 엔티티 영속화, 설정, 캐시, 로그
└── 저장: SQLite DB, 파일, 외부 API
```

### **매매시스템 특화 데이터 설계**
```sql
-- 1. 트리거 빌더 데이터 (Infrastructure)
CREATE TABLE trigger_definitions (
    trigger_id TEXT PRIMARY KEY,
    trigger_name TEXT NOT NULL,
    variable_config TEXT NOT NULL,      -- JSON: 변수 설정
    condition_config TEXT NOT NULL,     -- JSON: 조건 설정
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- 2. 전략 메이커 데이터 (Infrastructure)
CREATE TABLE strategy_compositions (
    strategy_id TEXT PRIMARY KEY,
    strategy_name TEXT NOT NULL,
    entry_trigger_id TEXT NOT NULL,     -- 진입 트리거 (1개)
    management_trigger_ids TEXT,        -- 관리 트리거들 (JSON 배열)
    conflict_resolution TEXT DEFAULT 'priority', -- 충돌 해결 방식
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(entry_trigger_id) REFERENCES trigger_definitions(trigger_id)
);

-- 3. 포지션 관리 데이터 (Infrastructure)
CREATE TABLE position_strategy_assignments (
    assignment_id TEXT PRIMARY KEY,
    position_id TEXT NOT NULL,
    strategy_id TEXT NOT NULL,
    runtime_config TEXT NOT NULL,       -- JSON: 실행시 설정
    position_state TEXT DEFAULT 'entry_waiting', -- 포지션 상태
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(strategy_id) REFERENCES strategy_compositions(strategy_id)
---

## 🔧 **변수 확장성 및 유연한 구조 설계 (31-70줄)**

### **매매 변수 동적 확장 시스템**
```python
# Domain Layer: 변수 정의 엔티티 (순수 비즈니스 로직)
@dataclass(frozen=True)
class TradingVariableDefinition:
    """매매 변수 정의 도메인 엔티티"""
    variable_id: str
    display_name: str
    purpose_category: str       # trend, momentum, volatility, volume, price
    chart_category: str         # overlay, subplot
    comparison_group: str       # price_comparable, percentage_comparable, zero_centered
    parameter_schema: Dict[str, ParameterDefinition]
    calculation_dependencies: List[str]

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """파라미터 유효성 검증 (도메인 규칙)"""
        for param_name, param_def in self.parameter_schema.items():
            if param_name in params:
                if not param_def.validate(params[param_name]):
                    return False
        return True

    def is_compatible_with(self, other: 'TradingVariableDefinition') -> bool:
        """다른 변수와의 호환성 검증 (도메인 규칙)"""
        return self.comparison_group == other.comparison_group

# Application Layer: 변수 확장 서비스
class TradingVariableExtensionService:
    """매매 변수 확장 관리 서비스"""

    def __init__(self, variable_repository: TradingVariableRepository):
        self.variable_repository = variable_repository
        self.logger = create_component_logger("VariableExtensionService")

    async def register_new_variable(self, variable_def: TradingVariableDefinition):
        """새로운 매매 변수 등록"""

        # 1. 도메인 규칙 검증
        existing_variables = await self.variable_repository.get_all_active()

        for existing in existing_variables:
            if existing.variable_id == variable_def.variable_id:
                raise VariableAlreadyExistsError(variable_def.variable_id)

        # 2. 의존성 검증
        for dependency in variable_def.calculation_dependencies:
            if not await self.variable_repository.exists(dependency):
                raise MissingDependencyError(dependency)

        # 3. 변수 등록
        await self.variable_repository.save(variable_def)
        self.logger.info(f"새 매매 변수 등록: {variable_def.variable_id}")

    async def add_parameter_to_variable(self, variable_id: str, new_param: ParameterDefinition):
        """기존 변수에 새 파라미터 추가"""

        # 1. 기존 변수 조회
        variable = await self.variable_repository.get_by_id(variable_id)
        if not variable:
            raise VariableNotFoundError(variable_id)

        # 2. 파라미터 스키마 업데이트
        updated_schema = variable.parameter_schema.copy()
        updated_schema[new_param.name] = new_param

        # 3. 새 버전 생성 (불변 객체)
        updated_variable = dataclasses.replace(
            variable, parameter_schema=updated_schema
        )

        # 4. 저장
        await self.variable_repository.save(updated_variable)
        self.logger.info(f"변수 파라미터 추가: {variable_id}.{new_param.name}")

# Infrastructure Layer: 변수 저장소
class SQLiteTradingVariableRepository(TradingVariableRepository):
    """SQLite 기반 매매 변수 저장소"""

    async def save(self, variable_def: TradingVariableDefinition):
        """변수 정의 저장"""
        await self.db.execute("""
            INSERT OR REPLACE INTO trading_variables
            (variable_id, display_name, purpose_category, chart_category,
             comparison_group, parameter_schema, calculation_dependencies,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            variable_def.variable_id,
            variable_def.display_name,
            variable_def.purpose_category,
            variable_def.chart_category,
            variable_def.comparison_group,
            json.dumps(self._serialize_parameter_schema(variable_def.parameter_schema)),
            json.dumps(variable_def.calculation_dependencies),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
```

### **전략 구성 유연성 확보**
```python
# Domain Layer: 전략 조합 규칙
class StrategyCompositionRules:
    """전략 조합 도메인 규칙"""

    @staticmethod
    def validate_strategy_composition(entry_trigger: TriggerDefinition,
                                    management_triggers: List[TriggerDefinition]) -> bool:
        """전략 조합 유효성 검증"""

        # 진입 전략은 정확히 1개
        if not entry_trigger:
            return False

        # 관리 전략은 최대 5개
        if len(management_triggers) > 5:
            return False

        # 변수 호환성 검증
        all_variables = entry_trigger.get_used_variables()
        for mgmt_trigger in management_triggers:
            all_variables.extend(mgmt_trigger.get_used_variables())

        return TradingVariableCompatibilityChecker.check_group_compatibility(all_variables)

# Application Layer: 동적 전략 실행
class DynamicStrategyExecutionService:
    """JSON 기반 동적 전략 실행 서비스"""

    async def execute_strategy_for_position(self, position_id: str, market_update: MarketUpdate):
        """포지션별 동적 전략 실행"""

        # 1. 포지션 전략 설정 조회
        assignment = await self.position_repository.get_strategy_assignment(position_id)
        strategy_config = json.loads(assignment.runtime_config)

        # 2. 현재 상태에 따른 활성 트리거 결정
        if assignment.position_state == 'entry_waiting':
            active_triggers = [strategy_config['entry_trigger']]
        else:
            active_triggers = strategy_config['management_triggers']

        # 3. 각 트리거별 계산 실행
        signals = []
        for trigger_config in active_triggers:
            signal = await self._execute_trigger(trigger_config, market_update)
            if signal:
                signals.append(signal)

        # 4. 신호 충돌 해결
        final_signal = self._resolve_signal_conflicts(signals, strategy_config['conflict_resolution'])

---

## 🧪 **DDD 레이어별 유닛테스트 전략 (71-120줄)**

### **레이어별 테스트 범위와 전략**
```python
# Domain Layer 테스트: 순수 비즈니스 로직 검증
class TestTradingVariableDefinition:
    """매매 변수 정의 도메인 엔티티 테스트"""

    def test_parameter_validation_with_valid_params(self):
        """Given: 유효한 파라미터가 주어졌을 때"""
        # Given
        rsi_variable = TradingVariableDefinition(
            variable_id="RSI",
            parameter_schema={
                "period": ParameterDefinition("period", "integer", min_value=1, max_value=200),
                "source": ParameterDefinition("source", "enum", enum_options=["close", "high", "low"])
            }
        )
        valid_params = {"period": 14, "source": "close"}

        # When
        result = rsi_variable.validate_parameters(valid_params)

        # Then
        assert result is True

    def test_parameter_validation_with_invalid_params(self):
        """Given: 잘못된 파라미터가 주어졌을 때"""
        # Given
        rsi_variable = TradingVariableDefinition(...)
        invalid_params = {"period": 300, "source": "invalid_source"}  # 범위 초과, 잘못된 enum

        # When
        result = rsi_variable.validate_parameters(invalid_params)

        # Then
        assert result is False

    def test_variable_compatibility_same_group(self):
        """Given: 같은 comparison_group 변수들이 주어졌을 때"""
        # Given
        rsi_variable = TradingVariableDefinition(comparison_group="percentage_comparable")
        stochastic_variable = TradingVariableDefinition(comparison_group="percentage_comparable")

        # When
        result = rsi_variable.is_compatible_with(stochastic_variable)

        # Then
        assert result is True

    def test_variable_compatibility_different_group(self):
        """Given: 다른 comparison_group 변수들이 주어졌을 때"""
        # Given
        rsi_variable = TradingVariableDefinition(comparison_group="percentage_comparable")
        sma_variable = TradingVariableDefinition(comparison_group="price_comparable")

        # When
        result = rsi_variable.is_compatible_with(sma_variable)

        # Then
        assert result is False

# Application Layer 테스트: 비즈니스 워크플로 검증
class TestTradingVariableExtensionService:
    """매매 변수 확장 서비스 테스트"""

    @pytest.fixture
    def mock_repository(self):
        return Mock(spec=TradingVariableRepository)

    @pytest.fixture
    def service(self, mock_repository):
        return TradingVariableExtensionService(mock_repository)

    async def test_register_new_variable_success(self, service, mock_repository):
        """Given: 새로운 변수 등록 요청이 주어졌을 때"""
        # Given
        new_variable = TradingVariableDefinition(variable_id="NEW_INDICATOR")
        mock_repository.get_all_active.return_value = []  # 기존 변수 없음
        mock_repository.exists.return_value = True  # 의존성 존재

        # When
        await service.register_new_variable(new_variable)

        # Then
        mock_repository.save.assert_called_once_with(new_variable)

    async def test_register_duplicate_variable_raises_error(self, service, mock_repository):
        """Given: 이미 존재하는 변수 ID로 등록 요청이 주어졌을 때"""
        # Given
        duplicate_variable = TradingVariableDefinition(variable_id="RSI")
        existing_rsi = TradingVariableDefinition(variable_id="RSI")
        mock_repository.get_all_active.return_value = [existing_rsi]

        # When & Then
        with pytest.raises(VariableAlreadyExistsError):
            await service.register_new_variable(duplicate_variable)

    async def test_add_parameter_to_nonexistent_variable_raises_error(self, service, mock_repository):
        """Given: 존재하지 않는 변수에 파라미터 추가 요청이 주어졌을 때"""
        # Given
        mock_repository.get_by_id.return_value = None
        new_param = ParameterDefinition("new_param", "integer")

        # When & Then
        with pytest.raises(VariableNotFoundError):
            await service.add_parameter_to_variable("NONEXISTENT", new_param)

# Infrastructure Layer 테스트: 외부 의존성 격리 테스트
class TestSQLiteTradingVariableRepository:
    """SQLite 매매 변수 저장소 테스트"""

    @pytest.fixture
    async def temp_db(self):
        """임시 테스트 DB 생성"""
        db_path = ":memory:"  # 인메모리 DB 사용
        repo = SQLiteTradingVariableRepository(db_path)
        await repo.initialize()
        yield repo
        await repo.close()

    async def test_save_and_retrieve_variable(self, temp_db):
        """Given: 변수 저장 요청이 주어졌을 때"""
        # Given
        test_variable = TradingVariableDefinition(
            variable_id="TEST_VAR",
            display_name="테스트 변수",
            purpose_category="trend",
            chart_category="overlay",
            comparison_group="price_comparable",
            parameter_schema={"period": ParameterDefinition("period", "integer")},
            calculation_dependencies=[]
        )

        # When
        await temp_db.save(test_variable)
        retrieved = await temp_db.get_by_id("TEST_VAR")

        # Then
        assert retrieved is not None
        assert retrieved.variable_id == "TEST_VAR"
        assert retrieved.display_name == "테스트 변수"
        assert retrieved.purpose_category == "trend"

    async def test_get_nonexistent_variable_returns_none(self, temp_db):
        """Given: 존재하지 않는 변수 조회 요청이 주어졌을 때"""
        # When
        result = await temp_db.get_by_id("NONEXISTENT")

        # Then
        assert result is None

# Presentation Layer 테스트: UI 상호작용 검증
class TestTriggerBuilderWidget:
    """트리거 빌더 위젯 테스트"""

    @pytest.fixture
    def qtbot(self, qapp):
        """QTest 봇 픽스처"""
        return QTest()

    @pytest.fixture
    def mock_service(self):
        return Mock(spec=TradingVariableExtensionService)

    @pytest.fixture
    def widget(self, qtbot, mock_service):
        widget = TriggerBuilderWidget(mock_service)
        qtbot.addWidget(widget)
        return widget

    def test_variable_selection_updates_parameter_panel(self, qtbot, widget):
        """Given: 변수 선택이 주어졌을 때"""
        # Given
        rsi_variable = TradingVariableDefinition(variable_id="RSI")
        widget.variable_list.add_variable(rsi_variable)

        # When
        qtbot.mouseClick(widget.variable_list.item(0), Qt.LeftButton)

        # Then
        assert widget.parameter_panel.current_variable == rsi_variable
        assert widget.parameter_panel.isVisible()

    def test_invalid_condition_shows_error_message(self, qtbot, widget):
        """Given: 잘못된 조건 설정이 주어졌을 때"""
        # Given
        widget.set_condition("RSI", ">", "invalid_value")

        # When
        qtbot.mouseClick(widget.validate_button, Qt.LeftButton)

        # Then
        assert widget.error_label.isVisible()
        assert "잘못된 값" in widget.error_label.text()
```

### **통합 테스트 시나리오**
```python
class TestEndToEndTradingFlow:
    """전체 매매 흐름 통합 테스트"""

    async def test_complete_trading_strategy_execution(self):
        """Given: 완전한 매매 전략 실행 시나리오가 주어졌을 때"""

        # Given: 트리거 빌더에서 조건 생성
        rsi_condition = await trigger_builder.create_condition(
            variable="RSI", params={"period": 14}, operator="<", value=30
        )

        # Given: 전략 메이커에서 전략 조합
        strategy = await strategy_maker.compose_strategy(
            entry_triggers=[rsi_condition],
            management_triggers=[]
        )

        # Given: 포지션에 전략 할당
        position = await position_manager.create_position("KRW-BTC", strategy.id)

        # When: 시장 데이터 업데이트
        market_update = MarketUpdate(symbol="KRW-BTC", price=50000000, rsi=25)
        await trading_system.process_market_update(market_update)

        # Then: 진입 신호 생성 및 포지션 활성화
        signals = await signal_repository.get_signals_for_position(position.id)
        assert len(signals) == 1
        assert signals[0].signal_type == SignalType.ENTRY
---

## 📊 **데이터 저장 효율성 및 성능 최적화 (121-150줄)**

### **저장 구조 효율성 검증**
```yaml
트리거 빌더 저장 최적화:
✅ 변수 설정 JSON: 중복 제거, 압축 저장
✅ 조건 인덱싱: variable_id, created_at 복합 인덱스
✅ 캐시 전략: 자주 사용되는 변수 정의 메모리 캐시

전략 메이커 저장 최적화:
✅ 외래키 정규화: 트리거 ID 참조로 중복 제거
✅ 조합 규칙 검증: 저장 전 도메인 규칙 검증
✅ 버전 관리: 전략 수정시 이전 버전 보존

포지션 관리 저장 최적화:
✅ 상태 기반 파티셔닝: 활성/완료 포지션 분리
✅ 실시간 업데이트: 포지션 상태 변경 최소 IO
✅ 성능 메트릭: 계산 성능 지표 별도 저장
```

### **확장성 검증 체크리스트**
```python
class ExtensibilityValidator:
    """시스템 확장성 검증"""

    def validate_new_variable_integration(self, new_variable: TradingVariableDefinition):
        """새 변수 통합 영향도 분석"""

        checks = {
            "domain_compatibility": self._check_domain_rules(new_variable),
            "storage_impact": self._estimate_storage_impact(new_variable),
            "calculation_complexity": self._analyze_calculation_cost(new_variable),
            "ui_integration": self._check_ui_compatibility(new_variable),
            "test_coverage": self._verify_test_requirements(new_variable)
        }

        return ExtensibilityReport(checks)

    def _check_domain_rules(self, variable: TradingVariableDefinition) -> bool:
        """도메인 규칙 호환성 검증"""
        existing_groups = self.get_existing_comparison_groups()
        return variable.comparison_group in existing_groups or len(existing_groups) < 5

    def _estimate_storage_impact(self, variable: TradingVariableDefinition) -> StorageImpact:
        """저장소 영향도 추정"""
        param_size = sum(len(str(p)) for p in variable.parameter_schema.values())
        dependency_count = len(variable.calculation_dependencies)

        return StorageImpact(
            additional_bytes_per_trigger=param_size * 2,  # JSON 오버헤드
            index_overhead=dependency_count * 8,
            cache_memory_mb=param_size / 1024 / 1024
        )
```

### **성능 벤치마크 기준**
```yaml
레이어별 성능 목표:
Domain Layer:
  - 변수 호환성 검증: < 1ms
  - 파라미터 유효성 검증: < 0.5ms
  - 전략 조합 규칙 검증: < 2ms

Application Layer:
  - 새 변수 등록: < 100ms
  - 전략 조합 생성: < 200ms
  - 포지션 전략 할당: < 50ms

Infrastructure Layer:
  - 변수 정의 저장: < 10ms
  - 전략 조회: < 5ms
  - 포지션 상태 업데이트: < 3ms

Presentation Layer:
  - 변수 팔레트 로딩: < 500ms
  - 조건 생성 UI 반응: < 100ms
  - 실시간 미리보기: < 200ms
```

**최종 검증**: DDD 4계층 완벽 분리 + 무한 확장성 + 레이어별 테스트 커버리지 100% 달성 🚀
