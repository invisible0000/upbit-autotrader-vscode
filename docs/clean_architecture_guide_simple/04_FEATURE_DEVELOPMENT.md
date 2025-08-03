# 🚀 기능 추가 개발 가이드

> **목적**: Clean Architecture 기반 새 기능 개발 워크플로  
> **대상**: LLM 에이전트, 개발자  
> **갱신**: 2025-08-03

## 🎯 개발 4단계 프로세스

```
1. 📋 요구사항 → 2. 💎 Domain → 3. ⚙️ Application → 4. 🎨 Presentation
   분석 (30분)     설계 (45분)    구현 (60분)       구현 (90분)
```

**핵심**: Domain부터 시작해서 바깥쪽 계층으로 확장

## 📋 1단계: 요구사항 분석

### ✅ 체크리스트
- [ ] **비즈니스 규칙** 명확히 정의
- [ ] **입출력** 데이터 형식 결정
- [ ] **성능 요구사항** 수치화
- [ ] **제약사항** 구체적으로 나열

### 💡 예시: "트레일링 스탑" 기능
```markdown
📝 비즈니스 규칙
- 수익률 5% 도달 시 트레일링 스탑 활성화
- 최고가 대비 3% 하락 시 자동 매도
- 포지션별 독립적 관리

📊 입출력
- 입력: 활성화_수익률, 추적_거리, 현재_가격
- 출력: 매도_신호 or 대기_상태

⚡ 성능 요구사항
- 가격 업데이트 1초 내 반응
- 메모리 사용량 포지션당 1KB 이하

🚨 제약사항
- 추적 거리: 1% ~ 20%
- 활성화 수익률: 최소 2%
```

## 💎 2단계: Domain Layer 설계

### 📊 도메인 엔티티 정의
```python
# domain/entities/trailing_stop.py
class TrailingStop:
    """트레일링 스탑 도메인 엔티티"""
    
    def __init__(self, activation_rate: Decimal, trail_distance: Decimal):
        # ✅ 비즈니스 규칙 검증
        if activation_rate < Decimal('0.02'):
            raise InvalidActivationRateError("활성화 수익률은 2% 이상이어야 합니다")
            
        if not Decimal('0.01') <= trail_distance <= Decimal('0.20'):
            raise InvalidTrailDistanceError("추적 거리는 1%~20% 범위여야 합니다")
        
        self.activation_rate = activation_rate
        self.trail_distance = trail_distance
        self.highest_price = None
        self.stop_price = None
        self.is_active = False
        
    def update_price(self, current_price: Decimal, entry_price: Decimal) -> TradingSignal:
        """가격 업데이트 및 신호 생성"""
        # ✅ 순수 비즈니스 로직
        profit_rate = (current_price - entry_price) / entry_price
        
        # 활성화 조건 확인
        if not self.is_active and profit_rate >= self.activation_rate:
            self._activate(current_price)
        
        if self.is_active:
            return self._update_trailing_stop(current_price)
            
        return TradingSignal.HOLD
        
    def _activate(self, price: Decimal):
        """트레일링 스탑 활성화"""
        self.is_active = True
        self.highest_price = price
        self.stop_price = price * (1 - self.trail_distance)
        
    def _update_trailing_stop(self, current_price: Decimal) -> TradingSignal:
        """트레일링 스탑 업데이트"""
        # 최고가 갱신
        if current_price > self.highest_price:
            self.highest_price = current_price
            self.stop_price = current_price * (1 - self.trail_distance)
        
        # 손절 조건 확인
        if current_price <= self.stop_price:
            return TradingSignal.SELL
            
        return TradingSignal.HOLD
```

### 📋 값 객체 정의
```python
# domain/value_objects/trading_signal.py
@dataclass(frozen=True)
class TradingSignal:
    action: str  # 'BUY', 'SELL', 'HOLD'
    reason: str
    timestamp: datetime
    
    HOLD = None  # 싱글톤 패턴
    
    @classmethod
    def sell(cls, reason: str):
        return cls('SELL', reason, datetime.utcnow())
```

## ⚙️ 3단계: Application Layer 구현

### 📚 Application Service
```python
# application/services/trailing_stop_service.py
class TrailingStopService:
    """트레일링 스탑 Application Service"""
    
    def __init__(self, position_repo, price_monitor, event_publisher):
        self.position_repo = position_repo
        self.price_monitor = price_monitor
        self.event_publisher = event_publisher
        
    def activate_trailing_stop(self, command: ActivateTrailingStopCommand):
        """트레일링 스탑 활성화 Use Case"""
        # ✅ 검증
        position = self.position_repo.find_by_id(command.position_id)
        if not position:
            return Result.fail("포지션을 찾을 수 없습니다")
            
        if position.has_trailing_stop():
            return Result.fail("이미 트레일링 스탑이 활성화되어 있습니다")
        
        # ✅ Domain 객체 생성
        trailing_stop = TrailingStop(
            command.activation_rate,
            command.trail_distance
        )
        
        # ✅ 포지션에 추가
        position.set_trailing_stop(trailing_stop)
        
        # ✅ 저장
        self.position_repo.save(position)
        
        # ✅ 이벤트 발행
        self.event_publisher.publish(
            TrailingStopActivated(position.id, trailing_stop.id)
        )
        
        return Result.success("트레일링 스탑이 활성화되었습니다")
    
    def process_price_update(self, price_update: PriceUpdateEvent):
        """가격 업데이트 처리 Use Case"""
        # ✅ 활성 포지션 조회
        active_positions = self.position_repo.find_active_with_trailing_stop()
        
        for position in active_positions:
            signal = position.trailing_stop.update_price(
                price_update.current_price,
                position.entry_price
            )
            
            if signal and signal.action == 'SELL':
                # ✅ 매도 신호 발행
                self.event_publisher.publish(
                    SellSignalGenerated(position.id, signal.reason)
                )
```

### 📝 Command/Query 객체
```python
# application/commands/activate_trailing_stop_command.py
@dataclass
class ActivateTrailingStopCommand:
    position_id: PositionId
    activation_rate: Decimal
    trail_distance: Decimal
    user_id: UserId
    
    def validate(self):
        if self.activation_rate < Decimal('0.02'):
            raise ValidationError("활성화 수익률은 2% 이상이어야 합니다")
```

## 🔌 4단계: Infrastructure 구현

### 🗄️ Repository 구현
```python
# infrastructure/repositories/position_repository.py
class SqlitePositionRepository(PositionRepository):
    def find_active_with_trailing_stop(self) -> List[Position]:
        """트레일링 스탑이 있는 활성 포지션 조회"""
        query = """
        SELECT p.*, ts.* 
        FROM positions p
        JOIN trailing_stops ts ON p.id = ts.position_id
        WHERE p.status = 'ACTIVE' AND ts.is_active = 1
        """
        
        rows = self.db.execute(query).fetchall()
        positions = []
        
        for row in rows:
            # ✅ DB 데이터 → Domain 객체 변환
            trailing_stop = TrailingStop(
                activation_rate=Decimal(row['activation_rate']),
                trail_distance=Decimal(row['trail_distance'])
            )
            # trailing_stop 상태 복원
            trailing_stop.highest_price = Decimal(row['highest_price']) if row['highest_price'] else None
            trailing_stop.stop_price = Decimal(row['stop_price']) if row['stop_price'] else None
            trailing_stop.is_active = bool(row['ts_is_active'])
            
            position = Position.from_dict(row)
            position.set_trailing_stop(trailing_stop)
            positions.append(position)
            
        return positions
```

### ⚡ 이벤트 처리
```python
# infrastructure/events/trailing_stop_event_handler.py
class TrailingStopEventHandler:
    def handle_sell_signal(self, event: SellSignalGenerated):
        """매도 신호 처리"""
        # ✅ 주문 서비스 호출
        order_command = CreateMarketSellOrderCommand(
            position_id=event.position_id,
            reason=event.reason
        )
        
        self.order_service.create_market_sell_order(order_command)
```

## 🎨 5단계: Presentation 구현

### 🖼️ View 구현
```python
# presentation/views/trailing_stop_dialog.py
class TrailingStopDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.presenter = None
        self.setup_ui()
        
    def setup_ui(self):
        # ✅ UI 구성
        layout = QVBoxLayout()
        
        # 활성화 수익률 입력
        self.activation_rate_input = QDoubleSpinBox()
        self.activation_rate_input.setRange(2.0, 50.0)
        self.activation_rate_input.setValue(5.0)
        self.activation_rate_input.setSuffix('%')
        
        # 추적 거리 입력
        self.trail_distance_input = QDoubleSpinBox()
        self.trail_distance_input.setRange(1.0, 20.0)
        self.trail_distance_input.setValue(3.0)
        self.trail_distance_input.setSuffix('%')
        
        # 버튼
        self.activate_button = QPushButton("트레일링 스탑 활성화")
        self.activate_button.clicked.connect(self.on_activate_clicked)
        
        layout.addWidget(QLabel("활성화 수익률:"))
        layout.addWidget(self.activation_rate_input)
        layout.addWidget(QLabel("추적 거리:"))
        layout.addWidget(self.trail_distance_input)
        layout.addWidget(self.activate_button)
        
        self.setLayout(layout)
        
    def on_activate_clicked(self):
        # ✅ 입력 수집
        data = {
            'activation_rate': self.activation_rate_input.value() / 100,
            'trail_distance': self.trail_distance_input.value() / 100
        }
        
        # ✅ Presenter 호출
        self.presenter.activate_trailing_stop(data)
```

### 🎭 Presenter 구현
```python
# presentation/presenters/trailing_stop_presenter.py
class TrailingStopPresenter:
    def __init__(self, view, service):
        self.view = view
        self.service = service
        
    def activate_trailing_stop(self, form_data):
        # ✅ Command 생성
        command = ActivateTrailingStopCommand(
            position_id=self.current_position_id,
            activation_rate=Decimal(str(form_data['activation_rate'])),
            trail_distance=Decimal(str(form_data['trail_distance'])),
            user_id=self.current_user_id
        )
        
        # ✅ Service 호출
        try:
            result = self.service.activate_trailing_stop(command)
            
            if result.success:
                self.view.show_success("트레일링 스탑이 활성화되었습니다")
                self.view.close()
            else:
                self.view.show_error(result.error)
                
        except ValidationError as e:
            self.view.show_error(f"입력 오류: {e.message}")
```

## 🧪 6단계: 테스트 작성

### 🎯 Domain 테스트
```python
# tests/domain/test_trailing_stop.py
class TestTrailingStop:
    def test_activation_with_valid_profit(self):
        # Given
        trailing_stop = TrailingStop(
            activation_rate=Decimal('0.05'),
            trail_distance=Decimal('0.03')
        )
        entry_price = Decimal('100')
        current_price = Decimal('106')  # 6% 수익
        
        # When
        signal = trailing_stop.update_price(current_price, entry_price)
        
        # Then
        assert trailing_stop.is_active
        assert signal == TradingSignal.HOLD
        assert trailing_stop.stop_price == Decimal('102.82')  # 106 * 0.97
```

### ⚙️ Application 테스트
```python
# tests/application/test_trailing_stop_service.py
class TestTrailingStopService:
    def test_activate_trailing_stop_success(self):
        # Given
        service = TrailingStopService(mock_repo, mock_monitor, mock_publisher)
        command = ActivateTrailingStopCommand(
            position_id=PositionId('pos-123'),
            activation_rate=Decimal('0.05'),
            trail_distance=Decimal('0.03'),
            user_id=UserId('user-456')
        )
        
        # When
        result = service.activate_trailing_stop(command)
        
        # Then
        assert result.success
        mock_repo.save.assert_called_once()
        mock_publisher.publish.assert_called_once()
```

## 📋 개발 완료 체크리스트

- [ ] **Domain**: 비즈니스 규칙 완전 구현
- [ ] **Application**: Use Case 시나리오 커버
- [ ] **Infrastructure**: Repository 및 외부 연동
- [ ] **Presentation**: UI 완성 및 사용성 검증
- [ ] **Test**: 90% 이상 커버리지
- [ ] **Documentation**: API 문서 및 사용 가이드

## 📚 관련 문서

- [시스템 개요](01_SYSTEM_OVERVIEW.md): 전체 아키텍처
- [계층별 책임](02_LAYER_RESPONSIBILITIES.md): 각 계층 역할
- [데이터 흐름](03_DATA_FLOW.md): 요청 처리 과정

---
**💡 핵심**: "Domain부터 시작해서 바깥쪽으로 확장하면 견고한 기능을 만들 수 있습니다!"
