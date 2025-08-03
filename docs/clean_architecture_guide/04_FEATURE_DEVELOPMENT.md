# 🚀 기능 추가 개발 가이드

> **목적**: 새로운 기능을 Clean Architecture 방식으로 개발하는 워크플로  
> **대상**: 개발자, 기능 기획자  
> **예상 읽기 시간**: 18분

## 🎯 개발 워크플로 개요

```
1. 요구사항 분석 → 2. Domain 설계 → 3. Application 설계
         ↓                    ↓              ↓
4. Infrastructure 구현 ← 5. Presentation 구현 ← 6. 통합 테스트
```

## 📋 실제 사례: "트레일링 스탑" 기능 추가

### Phase 1: 요구사항 분석 (30분)

#### 📝 기능 명세서 작성
```markdown
# 트레일링 스탑 기능 명세

## 비즈니스 요구사항
- 수익이 발생하면 손절선을 자동으로 상향 조정
- 최대 수익에서 일정 비율 하락 시 자동 매도
- 활성화 조건과 추적 거리를 사용자가 설정 가능

## 기술적 요구사항
- 실시간 가격 모니터링 (1초 이내 반응)
- 포지션별 독립적인 트레일링 상태 관리
- 백테스팅에서도 동일하게 동작

## 제약사항
- 최대 추적 거리: 20%
- 최소 추적 거리: 1%
- 활성화 수익률: 최소 2%
```

#### 🎯 영향도 분석
```python
# 영향받는 계층 분석
affected_layers = {
    "Domain": ["Position", "TradingRule", "TrailingStopStrategy"],
    "Application": ["PositionManagementService", "TradingSignalService"],
    "Infrastructure": ["PositionRepository", "PriceMonitoringService"],
    "Presentation": ["StrategyBuilderView", "PositionMonitorWidget"]
}
```

### Phase 2: Domain Layer 설계 (45분)

#### 📊 도메인 모델 설계
```python
# domain/entities/trailing_stop_strategy.py
class TrailingStopStrategy(ManagementStrategy):
    """트레일링 스탑 관리 전략 - Domain Entity"""
    
    def __init__(
        self, 
        strategy_id: StrategyId,
        activation_profit_rate: Decimal,
        trail_distance_rate: Decimal,
        max_loss_rate: Decimal
    ):
        super().__init__(strategy_id)
        
        # 비즈니스 규칙 검증
        self._validate_parameters(
            activation_profit_rate, 
            trail_distance_rate, 
            max_loss_rate
        )
        
        self.activation_profit_rate = activation_profit_rate
        self.trail_distance_rate = trail_distance_rate
        self.max_loss_rate = max_loss_rate
        self.highest_price = None
        self.stop_price = None
        self.is_activated = False
        
    def _validate_parameters(self, activation_rate, trail_rate, max_loss):
        """비즈니스 규칙 검증"""
        if not (0.02 <= activation_rate <= 1.0):
            raise InvalidParameterError("활성화 수익률은 2%-100% 범위여야 합니다")
            
        if not (0.01 <= trail_rate <= 0.20):
            raise InvalidParameterError("추적 거리는 1%-20% 범위여야 합니다")
            
        if max_loss and max_loss >= activation_rate:
            raise InvalidParameterError("최대 손실률은 활성화 수익률보다 작아야 합니다")
    
    def update_with_price(self, current_price: Price, position: Position) -> TradingSignal:
        """가격 업데이트에 따른 신호 생성 - 핵심 비즈니스 로직"""
        
        profit_rate = position.calculate_profit_rate(current_price)
        
        # 1. 트레일링 스탑 활성화 검사
        if not self.is_activated and profit_rate >= self.activation_profit_rate:
            self._activate_trailing_stop(current_price)
            self._add_event(TrailingStopActivatedEvent(
                self.id, position.id, current_price, profit_rate
            ))
        
        # 2. 활성화된 경우 스탑 가격 업데이트
        if self.is_activated:
            return self._update_stop_price(current_price, position)
        
        return TradingSignal.hold()
    
    def _activate_trailing_stop(self, current_price: Price):
        """트레일링 스탑 활성화"""
        self.is_activated = True
        self.highest_price = current_price
        self.stop_price = current_price * (1 - self.trail_distance_rate)
    
    def _update_stop_price(self, current_price: Price, position: Position) -> TradingSignal:
        """스탑 가격 업데이트 및 신호 생성"""
        
        # 최고가 갱신 시 스탑 가격 상향 조정
        if current_price > self.highest_price:
            self.highest_price = current_price
            new_stop_price = current_price * (1 - self.trail_distance_rate)
            self.stop_price = max(self.stop_price, new_stop_price)
            
            self._add_event(TrailingStopUpdatedEvent(
                self.id, position.id, current_price, self.stop_price
            ))
        
        # 스탑 가격 터치 시 청산 신호
        if current_price <= self.stop_price:
            self._add_event(TrailingStopTriggeredEvent(
                self.id, position.id, current_price, self.stop_price
            ))
            return TradingSignal.close_position(
                reason="트레일링 스탑 실행",
                price=current_price
            )
        
        return TradingSignal.hold()
```

#### 🔗 Value Objects 정의
```python
# domain/value_objects/trading_signal.py
class TradingSignal:
    """거래 신호 Value Object"""
    
    def __init__(self, signal_type: str, reason: str, price: Price = None):
        self.signal_type = signal_type  # HOLD, CLOSE_POSITION, ADD_BUY
        self.reason = reason
        self.price = price
        self.timestamp = datetime.utcnow()
    
    @classmethod
    def close_position(cls, reason: str, price: Price):
        return cls("CLOSE_POSITION", reason, price)
    
    @classmethod
    def hold(cls, reason: str = "조건 미충족"):
        return cls("HOLD", reason)
```

### Phase 3: Application Layer 구현 (60분)

#### 🔧 Application Service 구현
```python
# application/services/trading_signal_service.py
class TradingSignalService:
    """트레일링 스탑 신호 생성 서비스"""
    
    def __init__(
        self, 
        position_repo: PositionRepository,
        strategy_repo: StrategyRepository,
        event_publisher: EventPublisher
    ):
        self.position_repo = position_repo
        self.strategy_repo = strategy_repo
        self.event_publisher = event_publisher
    
    def process_price_update(self, symbol: str, current_price: Price):
        """가격 업데이트 처리 - 메인 유스케이스"""
        
        # 1. 활성 포지션 조회
        active_positions = self.position_repo.find_active_by_symbol(symbol)
        
        signals = []
        for position in active_positions:
            # 2. 포지션별 관리 전략 조회
            strategies = self.strategy_repo.find_management_strategies_by_position(
                position.id
            )
            
            # 3. 각 전략에서 신호 생성
            for strategy in strategies:
                if isinstance(strategy, TrailingStopStrategy):
                    signal = strategy.update_with_price(current_price, position)
                    
                    if signal.signal_type != "HOLD":
                        signals.append(PositionSignal(position.id, signal))
                        
                        # 4. 도메인 이벤트 발행
                        for event in strategy.get_uncommitted_events():
                            self.event_publisher.publish(event)
                        strategy.mark_events_as_committed()
        
        return ProcessPriceUpdateResult(signals)
```

#### 📝 Command/Query 정의
```python
# application/commands/create_trailing_stop_command.py
@dataclass
class CreateTrailingStopCommand:
    """트레일링 스탑 생성 명령"""
    position_id: PositionId
    activation_profit_rate: Decimal
    trail_distance_rate: Decimal
    max_loss_rate: Optional[Decimal] = None
    
    def validate(self):
        """명령 유효성 검증"""
        if self.activation_profit_rate <= 0:
            raise InvalidCommandError("활성화 수익률은 양수여야 합니다")
        
        if self.trail_distance_rate <= 0:
            raise InvalidCommandError("추적 거리는 양수여야 합니다")

# application/queries/get_trailing_stop_status_query.py
@dataclass
class GetTrailingStopStatusQuery:
    """트레일링 스탑 상태 조회"""
    position_id: PositionId

class TrailingStopQueryHandler:
    def handle(self, query: GetTrailingStopStatusQuery):
        strategy = self.strategy_repo.find_trailing_stop_by_position(
            query.position_id
        )
        
        if not strategy:
            return TrailingStopStatusResult(None)
        
        return TrailingStopStatusResult(
            TrailingStopStatusDto(
                is_activated=strategy.is_activated,
                highest_price=strategy.highest_price,
                stop_price=strategy.stop_price,
                activation_rate=strategy.activation_profit_rate
            )
        )
```

### Phase 4: Infrastructure Layer 구현 (45분)

#### 💾 Repository 구현
```python
# infrastructure/repositories/sqlite_strategy_repository.py
class SQLiteStrategyRepository(StrategyRepository):
    
    def save_trailing_stop_strategy(self, strategy: TrailingStopStrategy):
        """트레일링 스탑 전략 저장"""
        
        # Domain 객체 → DB 스키마 변환
        strategy_data = {
            'id': strategy.id.value,
            'type': 'trailing_stop',
            'position_id': strategy.position_id.value,
            'activation_profit_rate': float(strategy.activation_profit_rate),
            'trail_distance_rate': float(strategy.trail_distance_rate),
            'max_loss_rate': float(strategy.max_loss_rate) if strategy.max_loss_rate else None,
            'is_activated': strategy.is_activated,
            'highest_price': float(strategy.highest_price) if strategy.highest_price else None,
            'stop_price': float(strategy.stop_price) if strategy.stop_price else None,
            'created_at': strategy.created_at.isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        query = """
        INSERT INTO trading_strategies 
        (id, type, position_id, parameters, state, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        self.db.execute(query, (
            strategy_data['id'],
            strategy_data['type'],
            strategy_data['position_id'],
            json.dumps({
                'activation_profit_rate': strategy_data['activation_profit_rate'],
                'trail_distance_rate': strategy_data['trail_distance_rate'],
                'max_loss_rate': strategy_data['max_loss_rate']
            }),
            json.dumps({
                'is_activated': strategy_data['is_activated'],
                'highest_price': strategy_data['highest_price'],
                'stop_price': strategy_data['stop_price']
            }),
            strategy_data['created_at'],
            strategy_data['updated_at']
        ))
    
    def find_trailing_stop_by_position(self, position_id: PositionId):
        """포지션별 트레일링 스탑 조회"""
        query = """
        SELECT * FROM trading_strategies 
        WHERE position_id = ? AND type = 'trailing_stop' AND is_active = 1
        """
        
        row = self.db.fetch_one(query, (position_id.value,))
        if not row:
            return None
        
        # DB → Domain 객체 변환
        parameters = json.loads(row['parameters'])
        state = json.loads(row['state'])
        
        strategy = TrailingStopStrategy(
            StrategyId(row['id']),
            Decimal(parameters['activation_profit_rate']),
            Decimal(parameters['trail_distance_rate']),
            Decimal(parameters['max_loss_rate']) if parameters['max_loss_rate'] else None
        )
        
        # 상태 복원
        strategy.is_activated = state['is_activated']
        strategy.highest_price = Price(state['highest_price']) if state['highest_price'] else None
        strategy.stop_price = Price(state['stop_price']) if state['stop_price'] else None
        
        return strategy
```

### Phase 5: Presentation Layer 구현 (90분)

#### 🎨 UI 구현 (MVP 패턴)
```python
# presentation/views/trailing_stop_config_view.py
class TrailingStopConfigView(QWidget):
    """트레일링 스탑 설정 UI"""
    
    def __init__(self):
        super().__init__()
        self.presenter = None
        self.setup_ui()
    
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        
        # 활성화 수익률 설정
        self.activation_rate_label = QLabel("활성화 수익률 (%)")
        self.activation_rate_spinbox = QDoubleSpinBox()
        self.activation_rate_spinbox.setRange(2.0, 100.0)
        self.activation_rate_spinbox.setValue(5.0)
        self.activation_rate_spinbox.setSuffix("%")
        
        # 추적 거리 설정
        self.trail_distance_label = QLabel("추적 거리 (%)")
        self.trail_distance_spinbox = QDoubleSpinBox()
        self.trail_distance_spinbox.setRange(1.0, 20.0)
        self.trail_distance_spinbox.setValue(3.0)
        self.trail_distance_spinbox.setSuffix("%")
        
        # 버튼
        button_layout = QHBoxLayout()
        self.create_button = QPushButton("트레일링 스탑 생성")
        self.cancel_button = QPushButton("취소")
        
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        
        # 레이아웃 구성
        layout.addWidget(self.activation_rate_label)
        layout.addWidget(self.activation_rate_spinbox)
        layout.addWidget(self.trail_distance_label)
        layout.addWidget(self.trail_distance_spinbox)
        layout.addLayout(button_layout)
        
        # 이벤트 연결
        self.create_button.clicked.connect(self.on_create_clicked)
        self.cancel_button.clicked.connect(self.close)
    
    def on_create_clicked(self):
        """생성 버튼 클릭 처리"""
        config_data = {
            'activation_profit_rate': self.activation_rate_spinbox.value() / 100,
            'trail_distance_rate': self.trail_distance_spinbox.value() / 100
        }
        
        # Presenter에게 위임
        self.presenter.create_trailing_stop(config_data)
    
    def show_success_message(self, message: str):
        """성공 메시지 표시"""
        QMessageBox.information(self, "성공", message)
        self.close()
    
    def show_error_message(self, message: str):
        """에러 메시지 표시"""
        QMessageBox.warning(self, "오류", message)

# presentation/presenters/trailing_stop_presenter.py
class TrailingStopPresenter:
    """트레일링 스탑 Presenter"""
    
    def __init__(self, view, trailing_stop_service, position_id):
        self.view = view
        self.service = trailing_stop_service
        self.position_id = position_id
        self.view.presenter = self
    
    def create_trailing_stop(self, config_data):
        """트레일링 스탑 생성 처리"""
        try:
            # DTO 생성
            command = CreateTrailingStopCommand(
                position_id=self.position_id,
                activation_profit_rate=Decimal(str(config_data['activation_profit_rate'])),
                trail_distance_rate=Decimal(str(config_data['trail_distance_rate']))
            )
            
            # Service 호출
            result = self.service.create_trailing_stop(command)
            
            if result.success:
                self.view.show_success_message("트레일링 스탑이 생성되었습니다")
            else:
                self.view.show_error_message(result.error)
                
        except Exception as e:
            self.view.show_error_message(f"예상치 못한 오류: {str(e)}")
```

### Phase 6: 통합 및 테스트 (120분)

#### 🧪 도메인 테스트
```python
# tests/domain/test_trailing_stop_strategy.py
class TestTrailingStopStrategy:
    
    def test_strategy_creation_with_valid_parameters(self):
        """유효한 파라미터로 전략 생성 테스트"""
        strategy = TrailingStopStrategy(
            StrategyId.generate(),
            activation_profit_rate=Decimal('0.05'),  # 5%
            trail_distance_rate=Decimal('0.03'),     # 3%
            max_loss_rate=Decimal('0.02')            # 2%
        )
        
        assert strategy.activation_profit_rate == Decimal('0.05')
        assert strategy.trail_distance_rate == Decimal('0.03')
        assert not strategy.is_activated
    
    def test_activation_when_profit_threshold_reached(self):
        """수익 임계값 도달 시 활성화 테스트"""
        strategy = TrailingStopStrategy(
            StrategyId.generate(),
            activation_profit_rate=Decimal('0.05'),
            trail_distance_rate=Decimal('0.03')
        )
        
        position = create_test_position(entry_price=Price(100))
        current_price = Price(105)  # 5% 수익
        
        signal = strategy.update_with_price(current_price, position)
        
        assert strategy.is_activated
        assert strategy.highest_price == current_price
        assert strategy.stop_price == Price(101.85)  # 105 * 0.97
        assert signal.signal_type == "HOLD"
    
    def test_stop_trigger_when_price_falls_below_stop(self):
        """스탑 가격 이하로 하락 시 청산 신호 테스트"""
        strategy = TrailingStopStrategy(
            StrategyId.generate(),
            activation_profit_rate=Decimal('0.05'),
            trail_distance_rate=Decimal('0.03')
        )
        
        position = create_test_position(entry_price=Price(100))
        
        # 활성화
        strategy.update_with_price(Price(105), position)
        
        # 스탑 가격 이하로 하락
        signal = strategy.update_with_price(Price(101), position)
        
        assert signal.signal_type == "CLOSE_POSITION"
        assert signal.reason == "트레일링 스탑 실행"
```

#### 🔗 통합 테스트
```python
# tests/integration/test_trailing_stop_integration.py
class TestTrailingStopIntegration:
    
    def test_end_to_end_trailing_stop_creation(self):
        """트레일링 스탑 생성 전체 흐름 테스트"""
        # Given
        position_id = PositionId.generate()
        command = CreateTrailingStopCommand(
            position_id=position_id,
            activation_profit_rate=Decimal('0.05'),
            trail_distance_rate=Decimal('0.03')
        )
        
        # When
        result = self.trailing_stop_service.create_trailing_stop(command)
        
        # Then
        assert result.success
        
        # 저장된 전략 확인
        saved_strategy = self.strategy_repo.find_trailing_stop_by_position(
            position_id
        )
        assert saved_strategy is not None
        assert saved_strategy.activation_profit_rate == Decimal('0.05')
```

## ✅ 완료 체크리스트

### Domain Layer
- [ ] 핵심 엔티티 구현 (TrailingStopStrategy)
- [ ] 비즈니스 규칙 검증 로직
- [ ] 도메인 이벤트 정의
- [ ] Value Object 정의

### Application Layer  
- [ ] Application Service 구현
- [ ] Command/Query 정의
- [ ] Event Handler 구현
- [ ] DTO 정의

### Infrastructure Layer
- [ ] Repository 구현
- [ ] 데이터베이스 스키마 업데이트
- [ ] 외부 API 연동 (필요 시)

### Presentation Layer
- [ ] UI 구현 (MVP 패턴)
- [ ] Presenter 구현
- [ ] 사용자 입력 검증

### Testing
- [ ] 도메인 로직 단위 테스트
- [ ] Application Service 테스트
- [ ] Repository 통합 테스트
- [ ] UI 테스트

## 🔍 다음 단계

- **[UI 개발 가이드](05_UI_DEVELOPMENT.md)**: MVP 패턴 상세 구현
- **[데이터베이스 수정](06_DATABASE_MODIFICATION.md)**: 스키마 변경 방법
- **[테스팅 전략](16_TESTING_STRATEGY.md)**: 계층별 테스트 방법

---
**💡 핵심**: "Domain부터 시작해서 바깥쪽으로 확장하는 것이 Clean Architecture 개발의 핵심입니다!"
