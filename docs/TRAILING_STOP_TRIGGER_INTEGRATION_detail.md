# 🔗 트레일링 스탑 트리거 통합 가이드

> **목적**: 트레일링 스탑을 기존 트리거 빌더 시스템에 통합하는 완전한 구현 가이드  
> **대상**: 개발자, 시스템 아키텍트  
> **예상 읽기 시간**: 25분

## 🎯 통합 전략 개요

### 📋 핵심 아이디어
트레일링 스탑을 **특별한 형태의 트리거**로 취급하여 기존 트리거 빌더 시스템에 자연스럽게 통합합니다.

### 🔄 통합 원칙
1. **인터페이스 일관성**: 모든 트리거는 동일한 `evaluate()` 메서드 사용
2. **상태 관리**: 트레일링 스탑의 동적 상태를 트리거 내부에서 관리
3. **호환성 유지**: 기존 시스템과 완전 호환
4. **확장성**: 다른 고급 주문 타입 추가 용이

## 💎 Domain Layer 구현

### 1. 트리거 타입 확장
```python
# domain/entities/trigger_types.py
from enum import Enum
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

class TriggerType(Enum):
    """트리거 타입 정의"""
    SIMPLE = "simple"               # 단순 조건 트리거
    COMPOUND = "compound"           # 복합 조건 트리거
    TRAILING_STOP = "trailing_stop" # 트레일링 스탑 트리거
    BREAKOUT = "breakout"           # 돌파 트리거
    CUSTOM = "custom"               # 사용자 정의 트리거

class TriggerExecutionMode(Enum):
    """트리거 실행 모드"""
    IMMEDIATE = "immediate"         # 즉시 실행
    DELAYED = "delayed"            # 지연 실행
    CONDITIONAL = "conditional"     # 조건부 실행

class TriggerResult:
    """트리거 평가 결과"""
    
    def __init__(
        self,
        is_triggered: bool,
        action: Optional[str] = None,
        reason: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0
    ):
        self.is_triggered = is_triggered
        self.action = action or "NO_ACTION"
        self.reason = reason or "NOT_TRIGGERED"
        self.data = data or {}
        self.confidence = confidence
        self.timestamp = datetime.utcnow()
    
    @classmethod
    def triggered(cls, action: str, reason: str, data: Dict[str, Any] = None):
        """트리거 발동 결과 생성"""
        return cls(True, action, reason, data)
    
    @classmethod
    def not_triggered(cls, reason: str = "조건 미충족"):
        """트리거 미발동 결과 생성"""
        return cls(False, reason=reason)
```

### 2. 트레일링 스탑 트리거 구현
```python
# domain/entities/trailing_stop_trigger.py
from .base_trigger import BaseTrigger
from .trigger_types import TriggerType, TriggerResult
from ..value_objects.market_data import MarketData

class TrailingStopTrigger(BaseTrigger):
    """트레일링 스탑 트리거"""
    
    def __init__(
        self,
        trigger_id: str,
        activation_profit_rate: Decimal,
        trail_distance_rate: Decimal,
        max_loss_rate: Optional[Decimal] = None
    ):
        super().__init__(trigger_id, TriggerType.TRAILING_STOP)
        
        # 설정 값
        self.activation_profit_rate = activation_profit_rate  # 활성화 수익률
        self.trail_distance_rate = trail_distance_rate        # 추적 거리
        self.max_loss_rate = max_loss_rate                    # 최대 손실률 (선택)
        
        # 동적 상태
        self._is_active = False
        self._highest_price: Optional[Decimal] = None
        self._current_stop_price: Optional[Decimal] = None
        self._activated_at: Optional[datetime] = None
        self._last_update: Optional[datetime] = None
        
        # 통계
        self._price_updates_count = 0
        self._stop_price_adjustments = 0
    
    @property
    def is_active(self) -> bool:
        """트레일링 스탑 활성화 상태"""
        return self._is_active
    
    @property
    def current_stop_price(self) -> Optional[Decimal]:
        """현재 손절가"""
        return self._current_stop_price
    
    @property
    def highest_price(self) -> Optional[Decimal]:
        """기록된 최고가"""
        return self._highest_price
    
    def evaluate(self, market_data: MarketData) -> TriggerResult:
        """트리거 평가 - BaseTrigger 인터페이스 구현"""
        try:
            current_price = market_data.current_price
            entry_price = market_data.entry_price
            
            if not current_price or not entry_price:
                return TriggerResult.not_triggered("가격 정보 부족")
            
            self._price_updates_count += 1
            self._last_update = datetime.utcnow()
            
            # 1. 활성화 검사
            if not self._is_active:
                activation_result = self._check_activation(current_price, entry_price)
                if activation_result:
                    return activation_result
            
            # 2. 트레일링 로직 평가
            if self._is_active:
                return self._evaluate_trailing_logic(current_price)
            
            return TriggerResult.not_triggered("트레일링 스탑 비활성화 상태")
            
        except Exception as e:
            return TriggerResult.not_triggered(f"평가 중 오류: {str(e)}")
    
    def _check_activation(self, current_price: Decimal, entry_price: Decimal) -> Optional[TriggerResult]:
        """트레일링 스탑 활성화 검사"""
        profit_rate = (current_price - entry_price) / entry_price
        
        if profit_rate >= self.activation_profit_rate:
            self._activate(current_price)
            
            return TriggerResult(
                is_triggered=False,  # 활성화되었지만 아직 청산 신호는 아님
                action="TRAILING_STOP_ACTIVATED",
                reason=f"수익률 {profit_rate:.2%} 달성으로 활성화",
                data={
                    "activation_price": float(current_price),
                    "profit_rate": float(profit_rate),
                    "initial_stop_price": float(self._current_stop_price)
                }
            )
        
        return None
    
    def _activate(self, current_price: Decimal):
        """트레일링 스탑 활성화"""
        self._is_active = True
        self._highest_price = current_price
        self._current_stop_price = current_price * (1 - self.trail_distance_rate)
        self._activated_at = datetime.utcnow()
        
        # 도메인 이벤트 추가
        self._add_domain_event(TrailingStopActivatedEvent(
            trigger_id=self.id,
            activation_price=current_price,
            initial_stop_price=self._current_stop_price
        ))
    
    def _evaluate_trailing_logic(self, current_price: Decimal) -> TriggerResult:
        """트레일링 로직 평가"""
        
        # 최고가 갱신 검사
        if current_price > self._highest_price:
            old_stop_price = self._current_stop_price
            self._update_highest_price(current_price)
            
            # 손절가 업데이트 이벤트
            if self._current_stop_price != old_stop_price:
                self._add_domain_event(TrailingStopUpdatedEvent(
                    trigger_id=self.id,
                    old_stop_price=old_stop_price,
                    new_stop_price=self._current_stop_price,
                    new_highest_price=current_price
                ))
        
        # 손절가 터치 검사
        if current_price <= self._current_stop_price:
            return self._create_exit_signal(current_price)
        
        # 최대 손실률 검사 (선택사항)
        if self.max_loss_rate:
            max_loss_result = self._check_max_loss(current_price)
            if max_loss_result:
                return max_loss_result
        
        return TriggerResult.not_triggered("트레일링 조건 미충족")
    
    def _update_highest_price(self, current_price: Decimal):
        """최고가 업데이트 및 손절가 조정"""
        self._highest_price = current_price
        new_stop_price = current_price * (1 - self.trail_distance_rate)
        
        # 손절가는 상승만 가능 (하락하지 않음)
        if new_stop_price > self._current_stop_price:
            self._current_stop_price = new_stop_price
            self._stop_price_adjustments += 1
    
    def _create_exit_signal(self, current_price: Decimal) -> TriggerResult:
        """청산 신호 생성"""
        profit_loss = current_price - self._current_stop_price
        
        return TriggerResult.triggered(
            action="CLOSE_POSITION",
            reason="트레일링 스탑 발동",
            data={
                "trigger_price": float(current_price),
                "stop_price": float(self._current_stop_price),
                "highest_price": float(self._highest_price),
                "profit_loss": float(profit_loss),
                "active_duration": (datetime.utcnow() - self._activated_at).total_seconds()
            }
        )
    
    def _check_max_loss(self, current_price: Decimal) -> Optional[TriggerResult]:
        """최대 손실률 검사"""
        if not self.max_loss_rate or not self._highest_price:
            return None
        
        loss_from_peak = (self._highest_price - current_price) / self._highest_price
        
        if loss_from_peak >= self.max_loss_rate:
            return TriggerResult.triggered(
                action="CLOSE_POSITION",
                reason="최대 손실률 초과",
                data={
                    "trigger_price": float(current_price),
                    "highest_price": float(self._highest_price),
                    "loss_from_peak": float(loss_from_peak),
                    "max_loss_rate": float(self.max_loss_rate)
                }
            )
        
        return None
    
    def get_status_summary(self) -> Dict[str, Any]:
        """상태 요약 정보"""
        return {
            "trigger_id": self.id,
            "type": self.trigger_type.value,
            "is_active": self._is_active,
            "activation_profit_rate": float(self.activation_profit_rate),
            "trail_distance_rate": float(self.trail_distance_rate),
            "current_stop_price": float(self._current_stop_price) if self._current_stop_price else None,
            "highest_price": float(self._highest_price) if self._highest_price else None,
            "activated_at": self._activated_at.isoformat() if self._activated_at else None,
            "price_updates_count": self._price_updates_count,
            "stop_price_adjustments": self._stop_price_adjustments
        }
```

### 3. 기본 트리거 인터페이스
```python
# domain/entities/base_trigger.py
from abc import ABC, abstractmethod
from typing import List
from ..events.domain_event import DomainEvent

class BaseTrigger(ABC):
    """모든 트리거의 기본 클래스"""
    
    def __init__(self, trigger_id: str, trigger_type: TriggerType):
        self.id = trigger_id
        self.trigger_type = trigger_type
        self.created_at = datetime.utcnow()
        self.is_enabled = True
        self._domain_events: List[DomainEvent] = []
    
    @abstractmethod
    def evaluate(self, market_data: MarketData) -> TriggerResult:
        """트리거 조건 평가"""
        pass
    
    def _add_domain_event(self, event: DomainEvent):
        """도메인 이벤트 추가"""
        self._domain_events.append(event)
    
    def get_uncommitted_events(self) -> List[DomainEvent]:
        """미처리 도메인 이벤트 조회"""
        return self._domain_events.copy()
    
    def mark_events_as_committed(self):
        """도메인 이벤트 처리 완료 표시"""
        self._domain_events.clear()
    
    def enable(self):
        """트리거 활성화"""
        self.is_enabled = True
    
    def disable(self):
        """트리거 비활성화"""
        self.is_enabled = False
```

## ⚙️ Application Layer 구현

### 1. 트리거 빌더 서비스 확장
```python
# application/services/enhanced_trigger_builder.py
class EnhancedTriggerBuilder:
    """확장된 트리거 빌더"""
    
    def __init__(self, trigger_factory, validation_service):
        self.trigger_factory = trigger_factory
        self.validation_service = validation_service
    
    def create_trailing_stop_trigger(
        self,
        activation_profit_rate: Decimal,
        trail_distance_rate: Decimal,
        max_loss_rate: Optional[Decimal] = None
    ) -> TrailingStopTrigger:
        """트레일링 스탑 트리거 생성"""
        
        # 입력 검증
        self._validate_trailing_stop_params(
            activation_profit_rate, 
            trail_distance_rate, 
            max_loss_rate
        )
        
        # 트리거 ID 생성
        trigger_id = self._generate_trigger_id("trailing_stop")
        
        # 트리거 생성
        trigger = TrailingStopTrigger(
            trigger_id=trigger_id,
            activation_profit_rate=activation_profit_rate,
            trail_distance_rate=trail_distance_rate,
            max_loss_rate=max_loss_rate
        )
        
        return trigger
    
    def create_hybrid_strategy(
        self,
        entry_triggers: List[BaseTrigger],
        trailing_stop_config: Dict[str, Any],
        additional_exit_triggers: List[BaseTrigger] = None
    ) -> TradingStrategy:
        """하이브리드 전략 생성 (진입 트리거 + 트레일링 스탑 + 기타 청산 트리거)"""
        
        # 진입 조건 결합
        entry_condition = self._combine_triggers_with_and(entry_triggers)
        
        # 트레일링 스탑 생성
        trailing_stop = self.create_trailing_stop_trigger(
            activation_profit_rate=Decimal(str(trailing_stop_config['activation_rate'])),
            trail_distance_rate=Decimal(str(trailing_stop_config['trail_distance'])),
            max_loss_rate=Decimal(str(trailing_stop_config.get('max_loss_rate'))) if trailing_stop_config.get('max_loss_rate') else None
        )
        
        # 청산 조건들 결합
        exit_conditions = [trailing_stop]
        if additional_exit_triggers:
            exit_conditions.extend(additional_exit_triggers)
        
        # 전략 생성
        strategy = TradingStrategy(
            strategy_id=self._generate_strategy_id(),
            entry_condition=entry_condition,
            exit_conditions=exit_conditions,
            risk_management_rules=self._create_default_risk_rules()
        )
        
        return strategy
    
    def _validate_trailing_stop_params(
        self,
        activation_profit_rate: Decimal,
        trail_distance_rate: Decimal,
        max_loss_rate: Optional[Decimal]
    ):
        """트레일링 스탑 파라미터 검증"""
        
        if activation_profit_rate <= 0 or activation_profit_rate >= 1:
            raise ValueError("활성화 수익률은 0과 1 사이여야 합니다")
        
        if trail_distance_rate <= 0 or trail_distance_rate >= 1:
            raise ValueError("추적 거리는 0과 1 사이여야 합니다")
        
        if max_loss_rate and (max_loss_rate <= 0 or max_loss_rate >= 1):
            raise ValueError("최대 손실률은 0과 1 사이여야 합니다")
        
        # 논리적 일관성 검사
        if activation_profit_rate <= trail_distance_rate:
            raise ValueError("활성화 수익률은 추적 거리보다 커야 합니다")
    
    def _combine_triggers_with_and(self, triggers: List[BaseTrigger]) -> CompoundTrigger:
        """트리거들을 AND 조건으로 결합"""
        if len(triggers) == 1:
            return triggers[0]
        
        return CompoundTrigger(
            trigger_id=self._generate_trigger_id("compound"),
            sub_triggers=triggers,
            combination_logic="AND"
        )
```

### 2. 전략 실행 엔진 통합
```python
# application/services/strategy_execution_engine.py
class StrategyExecutionEngine:
    """전략 실행 엔진 - 모든 트리거 타입 지원"""
    
    def __init__(self, market_data_service, order_service, event_publisher):
        self.market_data_service = market_data_service
        self.order_service = order_service
        self.event_publisher = event_publisher
        self.active_strategies: Dict[str, TradingStrategy] = {}
    
    async def evaluate_strategy(self, strategy: TradingStrategy, symbol: str):
        """전략 평가 실행"""
        
        # 시장 데이터 조회
        market_data = await self.market_data_service.get_market_data(symbol)
        
        # 포지션 상태에 따른 트리거 평가
        if strategy.position_status == PositionStatus.WAITING:
            await self._evaluate_entry_triggers(strategy, market_data)
        elif strategy.position_status == PositionStatus.OPEN:
            await self._evaluate_exit_triggers(strategy, market_data)
    
    async def _evaluate_exit_triggers(self, strategy: TradingStrategy, market_data: MarketData):
        """청산 트리거 평가"""
        
        for exit_trigger in strategy.exit_conditions:
            if not exit_trigger.is_enabled:
                continue
            
            try:
                result = exit_trigger.evaluate(market_data)
                
                # 트리거 발동 처리
                if result.is_triggered:
                    await self._handle_trigger_activation(strategy, exit_trigger, result)
                
                # 트레일링 스탑 활성화 알림 (청산은 아니지만 상태 변경)
                elif (isinstance(exit_trigger, TrailingStopTrigger) and 
                      result.action == "TRAILING_STOP_ACTIVATED"):
                    await self._handle_trailing_stop_activation(strategy, exit_trigger, result)
                
                # 도메인 이벤트 처리
                await self._process_domain_events(exit_trigger)
                
            except Exception as e:
                logger.error(f"트리거 평가 오류: {str(e)}")
                continue
    
    async def _handle_trailing_stop_activation(
        self,
        strategy: TradingStrategy,
        trigger: TrailingStopTrigger,
        result: TriggerResult
    ):
        """트레일링 스탑 활성화 처리"""
        
        # 활성화 이벤트 발행
        activation_event = TrailingStopActivatedEvent(
            strategy_id=strategy.strategy_id,
            trigger_id=trigger.id,
            activation_data=result.data
        )
        
        await self.event_publisher.publish_async(activation_event)
        
        # 로그 기록
        logger.info(f"트레일링 스탑 활성화: {strategy.strategy_id} - {result.reason}")
    
    async def _handle_trigger_activation(
        self,
        strategy: TradingStrategy,
        trigger: BaseTrigger,
        result: TriggerResult
    ):
        """트리거 발동 처리"""
        
        if result.action == "CLOSE_POSITION":
            await self._execute_position_close(strategy, trigger, result)
        elif result.action == "OPEN_POSITION":
            await self._execute_position_open(strategy, trigger, result)
        
        # 트리거 발동 이벤트
        trigger_event = TriggerActivatedEvent(
            strategy_id=strategy.strategy_id,
            trigger_id=trigger.id,
            trigger_type=trigger.trigger_type.value,
            action=result.action,
            data=result.data
        )
        
        await self.event_publisher.publish_async(trigger_event)
    
    async def _execute_position_close(
        self,
        strategy: TradingStrategy,
        trigger: BaseTrigger,
        result: TriggerResult
    ):
        """포지션 청산 실행"""
        
        try:
            # 청산 주문 실행
            close_order = await self.order_service.create_market_sell_order(
                symbol=strategy.symbol,
                quantity=strategy.current_position.quantity,
                reason=result.reason
            )
            
            # 전략 상태 업데이트
            strategy.close_position(
                close_price=close_order.executed_price,
                close_reason=result.reason
            )
            
            logger.info(f"포지션 청산 완료: {strategy.strategy_id} - {result.reason}")
            
        except Exception as e:
            logger.error(f"포지션 청산 실패: {str(e)}")
            raise
```

## 🎨 Presentation Layer 구현

### 1. 트리거 빌더 UI 확장
```python
# presentation/views/enhanced_trigger_builder_view.py
class EnhancedTriggerBuilderView(QWidget):
    """확장된 트리거 빌더 뷰"""
    
    def setup_trigger_type_selection(self):
        """트리거 타입 선택 UI"""
        self.trigger_type_combo = QComboBox()
        self.trigger_type_combo.addItems([
            "📊 단순 조건",
            "🔗 복합 조건",
            "📈 트레일링 스탑",
            "🎯 돌파 조건",
            "⚙️ 사용자 정의"
        ])
        
        self.trigger_type_combo.currentTextChanged.connect(self.on_trigger_type_changed)
    
    def on_trigger_type_changed(self, trigger_type: str):
        """트리거 타입 변경 시 UI 전환"""
        self.clear_current_settings()
        
        if "트레일링 스탑" in trigger_type:
            self.show_trailing_stop_builder()
        elif "단순 조건" in trigger_type:
            self.show_simple_trigger_builder()
        elif "복합 조건" in trigger_type:
            self.show_compound_trigger_builder()
    
    def show_trailing_stop_builder(self):
        """트레일링 스탑 빌더 UI 표시"""
        self.trailing_stop_widget = TrailingStopBuilderWidget()
        self.settings_layout.addWidget(self.trailing_stop_widget)
        
        # 미리보기 연결
        self.trailing_stop_widget.settings_changed.connect(self.update_trailing_stop_preview)

class TrailingStopBuilderWidget(QWidget):
    """트레일링 스탑 설정 위젯"""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout()
        
        # 기본 설정 그룹
        basic_group = self.create_basic_settings_group()
        layout.addWidget(basic_group)
        
        # 고급 설정 그룹
        advanced_group = self.create_advanced_settings_group()
        layout.addWidget(advanced_group)
        
        # 미리보기 차트
        self.preview_chart = TrailingStopPreviewChart()
        layout.addWidget(self.preview_chart)
        
        self.setLayout(layout)
    
    def create_basic_settings_group(self) -> QGroupBox:
        """기본 설정 그룹"""
        group = QGroupBox("🎯 기본 설정")
        layout = QFormLayout()
        
        # 활성화 수익률
        self.activation_rate_input = QDoubleSpinBox()
        self.activation_rate_input.setRange(0.1, 50.0)
        self.activation_rate_input.setValue(5.0)
        self.activation_rate_input.setSuffix(" %")
        self.activation_rate_input.setToolTip("이 수익률에 도달하면 트레일링 스탑이 활성화됩니다")
        layout.addRow("활성화 수익률:", self.activation_rate_input)
        
        # 추적 거리
        self.trail_distance_input = QDoubleSpinBox()
        self.trail_distance_input.setRange(0.1, 20.0)
        self.trail_distance_input.setValue(3.0)
        self.trail_distance_input.setSuffix(" %")
        self.trail_distance_input.setToolTip("최고가에서 이 거리만큼 떨어지면 매도합니다")
        layout.addRow("추적 거리:", self.trail_distance_input)
        
        group.setLayout(layout)
        return group
    
    def create_advanced_settings_group(self) -> QGroupBox:
        """고급 설정 그룹"""
        group = QGroupBox("⚙️ 고급 설정")
        layout = QFormLayout()
        
        # 최대 손실률 (선택사항)
        self.max_loss_checkbox = QCheckBox("최대 손실률 제한 사용")
        layout.addRow(self.max_loss_checkbox)
        
        self.max_loss_input = QDoubleSpinBox()
        self.max_loss_input.setRange(1.0, 50.0)
        self.max_loss_input.setValue(10.0)
        self.max_loss_input.setSuffix(" %")
        self.max_loss_input.setEnabled(False)
        self.max_loss_input.setToolTip("최고가에서 이 비율 이상 하락하면 강제 매도")
        layout.addRow("최대 손실률:", self.max_loss_input)
        
        # 체크박스와 입력 필드 연동
        self.max_loss_checkbox.toggled.connect(self.max_loss_input.setEnabled)
        
        group.setLayout(layout)
        return group
    
    def connect_signals(self):
        """시그널 연결"""
        self.activation_rate_input.valueChanged.connect(self.emit_settings_changed)
        self.trail_distance_input.valueChanged.connect(self.emit_settings_changed)
        self.max_loss_input.valueChanged.connect(self.emit_settings_changed)
        self.max_loss_checkbox.toggled.connect(self.emit_settings_changed)
    
    def emit_settings_changed(self):
        """설정 변경 시그널 발행"""
        settings = self.get_current_settings()
        self.settings_changed.emit(settings)
    
    def get_current_settings(self) -> dict:
        """현재 설정값 조회"""
        return {
            'activation_rate': self.activation_rate_input.value() / 100,
            'trail_distance': self.trail_distance_input.value() / 100,
            'max_loss_rate': self.max_loss_input.value() / 100 if self.max_loss_checkbox.isChecked() else None
        }
```

### 2. 미리보기 차트
```python
# presentation/widgets/trailing_stop_preview_chart.py
class TrailingStopPreviewChart(QWidget):
    """트레일링 스탑 미리보기 차트"""
    
    def __init__(self):
        super().__init__()
        self.setup_chart()
    
    def setup_chart(self):
        """차트 설정"""
        # matplotlib 기반 차트 구성
        self.figure = plt.figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
    
    def update_preview(self, settings: dict):
        """미리보기 업데이트"""
        # 가상의 가격 데이터 생성
        price_data = self.generate_sample_price_data()
        
        # 트레일링 스탑 시뮬레이션
        simulation_result = self.simulate_trailing_stop(price_data, settings)
        
        # 차트 그리기
        self.plot_simulation(price_data, simulation_result)
    
    def simulate_trailing_stop(self, price_data: List[float], settings: dict) -> dict:
        """트레일링 스탑 시뮬레이션"""
        entry_price = price_data[0]
        activation_price = entry_price * (1 + settings['activation_rate'])
        
        is_active = False
        highest_price = entry_price
        stop_prices = []
        activation_point = None
        exit_point = None
        
        for i, price in enumerate(price_data):
            if not is_active and price >= activation_price:
                is_active = True
                highest_price = price
                activation_point = i
            
            if is_active:
                if price > highest_price:
                    highest_price = price
                
                stop_price = highest_price * (1 - settings['trail_distance'])
                stop_prices.append(stop_price)
                
                # 청산 조건 체크
                if price <= stop_price and not exit_point:
                    exit_point = i
                    break
            else:
                stop_prices.append(None)
        
        return {
            'stop_prices': stop_prices,
            'activation_point': activation_point,
            'exit_point': exit_point,
            'highest_price': highest_price
        }
```

## 🚀 충돌 방지 및 논리적 일관성

### 1. 전략 메이커와의 호환성 분석
```python
# domain/services/strategy_conflict_analyzer.py
class StrategyConflictAnalyzer:
    """전략 충돌 분석기"""
    
    def analyze_strategy_conflicts(self, strategy: TradingStrategy) -> ConflictAnalysisResult:
        """전략 내 충돌 분석"""
        conflicts = []
        warnings = []
        
        # 1. 진입/청산 트리거 충돌 분석
        entry_exit_conflicts = self._analyze_entry_exit_conflicts(strategy)
        conflicts.extend(entry_exit_conflicts)
        
        # 2. 청산 트리거 간 충돌 분석
        exit_conflicts = self._analyze_exit_trigger_conflicts(strategy.exit_conditions)
        conflicts.extend(exit_conflicts)
        
        # 3. 리스크 관리 규칙 충돌
        risk_conflicts = self._analyze_risk_management_conflicts(strategy)
        warnings.extend(risk_conflicts)
        
        return ConflictAnalysisResult(conflicts, warnings)
    
    def _analyze_exit_trigger_conflicts(self, exit_triggers: List[BaseTrigger]) -> List[Conflict]:
        """청산 트리거 간 충돌 분석"""
        conflicts = []
        
        trailing_stops = [t for t in exit_triggers if isinstance(t, TrailingStopTrigger)]
        fixed_stops = [t for t in exit_triggers if isinstance(t, FixedStopLossTrigger)]
        
        # 1. 다중 트레일링 스탑 충돌
        if len(trailing_stops) > 1:
            conflicts.append(Conflict(
                type="MULTIPLE_TRAILING_STOPS",
                severity="HIGH",
                message="하나의 전략에 여러 트레일링 스탑이 설정되어 있습니다",
                suggestion="트레일링 스탑은 하나만 사용하거나 조건을 분리하세요"
            ))
        
        # 2. 트레일링 스탑과 고정 손절 충돌
        if trailing_stops and fixed_stops:
            for ts in trailing_stops:
                for fs in fixed_stops:
                    if self._check_stop_loss_overlap(ts, fs):
                        conflicts.append(Conflict(
                            type="STOP_LOSS_OVERLAP",
                            severity="MEDIUM",
                            message="트레일링 스탑과 고정 손절의 범위가 겹칩니다",
                            suggestion="손절 가격 범위를 조정하거나 우선순위를 설정하세요"
                        ))
        
        return conflicts
    
    def _check_stop_loss_overlap(
        self, 
        trailing_stop: TrailingStopTrigger, 
        fixed_stop: FixedStopLossTrigger
    ) -> bool:
        """손절 범위 겹침 검사"""
        # 트레일링 스탑의 최초 손절가와 고정 손절가 비교
        if trailing_stop.activation_profit_rate <= 0:
            return True  # 즉시 활성화되는 경우 겹칠 가능성 높음
        
        # 더 정교한 분석 로직 구현
        return False
```

### 2. 우선순위 관리 시스템
```python
# domain/services/trigger_priority_manager.py
class TriggerPriorityManager:
    """트리거 우선순위 관리자"""
    
    # 트리거 타입별 기본 우선순위
    DEFAULT_PRIORITIES = {
        TriggerType.TRAILING_STOP: 100,     # 높은 우선순위
        TriggerType.SIMPLE: 50,             # 중간 우선순위
        TriggerType.COMPOUND: 75,           # 높은 우선순위
        TriggerType.BREAKOUT: 60,           # 중간 우선순위
        TriggerType.CUSTOM: 25              # 낮은 우선순위
    }
    
    def resolve_trigger_conflicts(
        self, 
        triggered_results: List[Tuple[BaseTrigger, TriggerResult]]
    ) -> TriggerResult:
        """트리거 충돌 해결"""
        
        if not triggered_results:
            return TriggerResult.not_triggered()
        
        if len(triggered_results) == 1:
            return triggered_results[0][1]
        
        # 우선순위별 정렬
        sorted_results = sorted(
            triggered_results,
            key=lambda x: self._get_trigger_priority(x[0]),
            reverse=True
        )
        
        # 최고 우선순위 트리거 선택
        highest_priority_trigger, highest_priority_result = sorted_results[0]
        
        # 충돌 로그 기록
        self._log_trigger_conflict(sorted_results, highest_priority_trigger)
        
        return highest_priority_result
    
    def _get_trigger_priority(self, trigger: BaseTrigger) -> int:
        """트리거 우선순위 조회"""
        base_priority = self.DEFAULT_PRIORITIES.get(trigger.trigger_type, 50)
        
        # 트레일링 스탑의 경우 활성화 상태에 따라 우선순위 조정
        if isinstance(trigger, TrailingStopTrigger) and trigger.is_active:
            base_priority += 50  # 활성화된 트레일링 스탑은 최고 우선순위
        
        return base_priority
```

### 3. 안전장치 및 검증
```python
# application/services/strategy_safety_validator.py
class StrategySafetyValidator:
    """전략 안전성 검증기"""
    
    def validate_strategy_safety(self, strategy: TradingStrategy) -> ValidationResult:
        """전략 안전성 종합 검증"""
        
        issues = []
        
        # 1. 무한 루프 방지
        loop_check = self._check_infinite_loops(strategy)
        issues.extend(loop_check)
        
        # 2. 메모리 누수 방지
        memory_check = self._check_memory_usage(strategy)
        issues.extend(memory_check)
        
        # 3. 논리적 모순 검사
        logic_check = self._check_logical_consistency(strategy)
        issues.extend(logic_check)
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues
        )
    
    def _check_logical_consistency(self, strategy: TradingStrategy) -> List[ValidationIssue]:
        """논리적 일관성 검사"""
        issues = []
        
        # 트레일링 스탑 관련 검사
        for exit_trigger in strategy.exit_conditions:
            if isinstance(exit_trigger, TrailingStopTrigger):
                # 활성화 수익률이 너무 낮은 경우
                if exit_trigger.activation_profit_rate < Decimal('0.001'):  # 0.1%
                    issues.append(ValidationIssue(
                        type="LOW_ACTIVATION_RATE",
                        message="활성화 수익률이 너무 낮아 즉시 활성화될 수 있습니다",
                        severity="WARNING"
                    ))
                
                # 추적 거리가 활성화 수익률보다 큰 경우
                if exit_trigger.trail_distance_rate >= exit_trigger.activation_profit_rate:
                    issues.append(ValidationIssue(
                        type="INCONSISTENT_RATES",
                        message="추적 거리가 활성화 수익률보다 크거나 같습니다",
                        severity="ERROR"
                    ))
        
        return issues
```

이 통합 방식을 통해 **트레일링 스탑을 기존 트리거 시스템에 자연스럽게 통합**하면서도 **전략 메이커와의 충돌을 방지**하고 **논리적 일관성을 유지**할 수 있습니다.

---
**💡 핵심**: "트레일링 스탑을 특별한 트리거로 취급하여 기존 시스템과 완벽하게 통합하면서도 안전성과 일관성을 보장합니다!"
