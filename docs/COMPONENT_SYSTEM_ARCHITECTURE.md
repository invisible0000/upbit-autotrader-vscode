# 원자적 컴포넌트 시스템 아키텍처 (Atomic Component System Architecture)

## 🎯 **설계 철학**

> **"전략을 만드는 것이 아니라 전략을 만들 수 있는 도구를 제공한다"**

기존의 고정된 전략 클래스 방식을 폐기하고, 원자적 컴포넌트들을 조합하여 무한한 전략 조합을 가능하게 하는 시스템입니다.

---

## 🔬 **컴포넌트 분류 체계 (Component Classification)**

### **🧬 원자적 컴포넌트 레벨 (Atomic Level)**
최소 단위의 기능 컴포넌트들

### **🔗 조합 컴포넌트 레벨 (Composite Level)**  
원자적 컴포넌트들의 조합

### **🎪 전략 레벨 (Strategy Level)**
사용자가 최종적으로 만드는 완전한 트레이딩 시스템

---

## 🧩 **원자적 컴포넌트 카탈로그 (Atomic Component Catalog)**

### **📍 1. 트리거 컴포넌트 (Trigger Components)**
*특정 조건이 만족되었을 때 신호를 발생시키는 컴포넌트들*

```python
# 가격 트리거 컴포넌트들
class PriceTriggerComponent:
    - PriceAboveTrigger: 가격이 특정값 이상일 때
    - PriceBelowTrigger: 가격이 특정값 이하일 때  
    - PriceChangeTrigger: 가격 변화율이 특정 범위일 때
    - PriceCrossTrigger: 가격이 특정값을 돌파했을 때

# 지표 트리거 컴포넌트들  
class IndicatorTriggerComponent:
    - RSITrigger: RSI가 특정 구간에 진입했을 때
    - MACDCrossTrigger: MACD 라인 교차가 발생했을 때
    - MovingAverageCrossTrigger: 이동평균 교차가 발생했을 때
    - BollingerBandTrigger: 볼린저 밴드 터치가 발생했을 때

# 시간 트리거 컴포넌트들
class TimeTriggerComponent:
    - TimeElapsedTrigger: 특정 시간이 경과했을 때
    - ScheduleTrigger: 특정 시간대가 되었을 때
    - PeriodTrigger: 주기적으로 실행될 때

# 포지션 트리거 컴포넌트들
class PositionTriggerComponent:
    - PositionSizeTrigger: 포지션 크기가 특정값에 도달했을 때
    - ProfitLossTrigger: 수익/손실이 특정 비율에 도달했을 때
    - HoldingPeriodTrigger: 보유 기간이 특정 시간을 초과했을 때
```

### **⚡ 2. 액션 컴포넌트 (Action Components)**  
*트리거가 발생했을 때 실행할 구체적인 행동들*

```python
# 매수 액션 컴포넌트들
class BuyActionComponent:
    - FixedAmountBuy: 고정 금액 매수
    - PercentageBuy: 비율 기반 매수  
    - CalculatedBuy: 계산된 금액 매수 (리스크 기반 등)
    - AdditionalBuy: 기존 포지션에 추가 매수

# 매도 액션 컴포넌트들
class SellActionComponent:
    - FullPositionSell: 전량 매도
    - PartialSell: 부분 매도
    - PercentageSell: 비율 기반 매도
    - CalculatedSell: 계산된 수량 매도

# 관리 액션 컴포넌트들
class ManagementActionComponent:
    - UpdateStopLoss: 손절가 업데이트
    - UpdateTakeProfit: 익절가 업데이트  
    - PositionResize: 포지션 크기 조정
    - NotificationSend: 알림 발송
```

### **🔧 3. 조건 컴포넌트 (Condition Components)**
*트리거와 액션 사이의 검증 로직*

```python
# 검증 조건 컴포넌트들
class ValidationConditionComponent:
    - PositionExistsCondition: 포지션이 존재하는가?
    - NoPositionCondition: 포지션이 없는가?
    - ProfitableCondition: 수익 중인가?
    - WithinRiskLimitCondition: 리스크 한도 내인가?

# 조합 조건 컴포넌트들  
class CompositeConditionComponent:
    - AndCondition: 모든 조건이 참인가?
    - OrCondition: 하나라도 조건이 참인가?
    - NotCondition: 조건이 거짓인가?
    - CountCondition: 특정 개수 이상의 조건이 참인가?
```

### **📊 4. 계산 컴포넌트 (Calculator Components)**
*동적으로 값을 계산하는 컴포넌트들*

```python
# 가격 계산 컴포넌트들
class PriceCalculatorComponent:
    - AveragePriceCalculator: 평균 단가 계산
    - ProfitLossCalculator: 손익 계산
    - PercentageChangeCalculator: 변화율 계산
    - SupportResistanceCalculator: 지지/저항선 계산

# 포지션 계산 컴포넌트들
class PositionCalculatorComponent:
    - PositionSizeCalculator: 적정 포지션 크기 계산
    - RiskBasedSizeCalculator: 리스크 기반 크기 계산
    - KellyCalculator: 켈리 공식 기반 계산
    - FixedRatioCalculator: 고정 비율 계산

# 지표 계산 컴포넌트들  
class IndicatorCalculatorComponent:
    - RSICalculator: RSI 계산
    - MACDCalculator: MACD 계산
    - MovingAverageCalculator: 이동평균 계산
    - BollingerBandCalculator: 볼린저 밴드 계산
```

---

## 🏗️ **컴포넌트 기반 전략 구성 예제**

### **🎯 물타기 전략 컴포넌트 분해**

```python
downward_averaging_strategy = {
    "strategy_name": "사용자 정의 물타기 전략",
    "strategy_id": "user_downward_averaging_001",
    
    # 규칙 1: 초기 진입
    "rules": [
        {
            "rule_id": "initial_entry",
            "description": "사용자 수동 진입",
            "trigger": {
                "component": "ManualTrigger",
                "parameters": {}
            },
            "conditions": [
                {
                    "component": "NoPositionCondition",
                    "parameters": {}
                }
            ],
            "action": {
                "component": "FixedAmountBuy", 
                "parameters": {
                    "amount": 100000  # 10만원 초기 진입
                }
            }
        },
        
        # 규칙 2: 하락시 추가 매수
        {
            "rule_id": "add_buy_on_dip",
            "description": "5% 하락마다 10만원 추가 매수",
            "trigger": {
                "component": "PriceChangeTrigger",
                "parameters": {
                    "reference": "average_price",
                    "change_percent": -0.05,  # -5% 하락
                    "direction": "below"
                }
            },
            "conditions": [
                {
                    "component": "PositionExistsCondition",
                    "parameters": {}
                },
                {
                    "component": "MaxCountCondition",
                    "parameters": {
                        "current_count": "add_buy_count",
                        "max_count": 3
                    }
                }
            ],
            "action": {
                "component": "AdditionalBuy",
                "parameters": {
                    "amount": 100000  # 10만원 추가
                }
            }
        },
        
        # 규칙 3: 손익분기점 청산
        {
            "rule_id": "break_even_exit",
            "description": "평단가 대비 3% 상승시 청산",
            "trigger": {
                "component": "PriceChangeTrigger", 
                "parameters": {
                    "reference": "average_price",
                    "change_percent": 0.03,   # +3% 상승
                    "direction": "above"
                }
            },
            "conditions": [
                {
                    "component": "PositionExistsCondition",
                    "parameters": {}
                }
            ],
            "action": {
                "component": "FullPositionSell",
                "parameters": {}
            }
        },
        
        # 규칙 4: 선택적 트레일링 스탑
        {
            "rule_id": "optional_trailing_stop",
            "description": "선택적 트레일링 스탑",
            "enabled": False,  # 사용자가 켜고 끌 수 있음
            "trigger": {
                "component": "ProfitLossTrigger",
                "parameters": {
                    "profit_percent": 0.05,  # 5% 수익 달성시 활성화
                    "trail_percent": 0.03    # 3% 트레일링
                }
            },
            "conditions": [
                {
                    "component": "PositionExistsCondition",
                    "parameters": {}
                }
            ],
            "action": {
                "component": "FullPositionSell",
                "parameters": {
                    "reason": "trailing_stop"
                }
            }
        }
    ]
}
```

### **📈 피라미딩 전략 컴포넌트 분해**

```python
pyramiding_strategy = {
    "strategy_name": "상승 피라미딩 전략",
    "strategy_id": "user_pyramiding_001", 
    
    "rules": [
        {
            "rule_id": "indicator_entry",
            "description": "RSI 과매도 + MACD 골든크로스 진입",
            "trigger": {
                "component": "CompositeANDTrigger",
                "parameters": {
                    "triggers": [
                        {
                            "component": "RSITrigger",
                            "parameters": {"rsi_threshold": 30, "direction": "below"}
                        },
                        {
                            "component": "MACDCrossTrigger", 
                            "parameters": {"cross_type": "golden"}
                        }
                    ]
                }
            },
            "action": {
                "component": "CalculatedBuy",
                "parameters": {
                    "calculator": "RiskBasedSizeCalculator",
                    "risk_percent": 0.02  # 2% 리스크
                }
            }
        },
        
        {
            "rule_id": "pyramid_on_profit",
            "description": "5% 수익마다 추가 매수",
            "trigger": {
                "component": "ProfitLossTrigger",
                "parameters": {
                    "profit_percent": 0.05,  # 5% 수익
                    "direction": "above"
                }
            },
            "action": {
                "component": "AdditionalBuy",
                "parameters": {
                    "amount": 100000
                }
            }
        }
    ]
}
```

---

## 🎨 **비주얼 전략 빌더 UI 설계**

### **🎪 드래그 앤 드롭 인터페이스**

```python
class VisualStrategyBuilder:
    """비주얼 전략 빌더 UI"""
    
    def __init__(self):
        self.component_palette = ComponentPalette()
        self.strategy_canvas = StrategyCanvas() 
        self.property_panel = PropertyPanel()
        self.preview_panel = PreviewPanel()
        
    def create_layout(self):
        """UI 레이아웃 생성"""
        main_layout = QHBoxLayout()
        
        # 좌측: 컴포넌트 팔레트
        palette_layout = self.create_component_palette()
        main_layout.addLayout(palette_layout, 1)
        
        # 중앙: 전략 캔버스  
        canvas_layout = self.create_strategy_canvas()
        main_layout.addLayout(canvas_layout, 3)
        
        # 우측: 속성 패널
        property_layout = self.create_property_panel()
        main_layout.addLayout(property_layout, 1)
        
        return main_layout
    
    def create_component_palette(self):
        """컴포넌트 팔레트 생성"""
        palette = ComponentPaletteWidget()
        
        # 트리거 컴포넌트 그룹
        trigger_group = palette.add_group("🔥 트리거")
        trigger_group.add_component("가격 트리거", PriceTriggerComponent, "💰")
        trigger_group.add_component("지표 트리거", IndicatorTriggerComponent, "📊") 
        trigger_group.add_component("시간 트리거", TimeTriggerComponent, "⏰")
        trigger_group.add_component("수동 트리거", ManualTriggerComponent, "👆")
        
        # 액션 컴포넌트 그룹
        action_group = palette.add_group("⚡ 액션")
        action_group.add_component("매수", BuyActionComponent, "🟢")
        action_group.add_component("매도", SellActionComponent, "🔴")
        action_group.add_component("관리", ManagementActionComponent, "🔧")
        
        # 조건 컴포넌트 그룹  
        condition_group = palette.add_group("🔍 조건")
        condition_group.add_component("포지션 조건", PositionConditionComponent, "📍")
        condition_group.add_component("수익 조건", ProfitConditionComponent, "💚")
        condition_group.add_component("논리 조건", LogicConditionComponent, "🧠")
        
        return palette
```

### **🖱️ 드래그 앤 드롭 동작**

```python
class StrategyCanvasWidget(QWidget):
    """전략 캔버스 위젯"""
    
    def __init__(self):
        super().__init__()
        self.components = []
        self.connections = []
        self.setAcceptDrops(True)
        
    def dragEnterEvent(self, event):
        """드래그 진입 이벤트"""
        if event.mimeData().hasFormat("application/x-component"):
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """드롭 이벤트"""
        component_data = event.mimeData().data("application/x-component")
        component_info = json.loads(bytes(component_data).decode())
        
        # 컴포넌트를 캔버스에 추가
        position = event.pos()
        new_component = self.create_component_widget(
            component_info["type"], 
            component_info["name"],
            position
        )
        
        self.components.append(new_component)
        self.update_canvas()
        
        event.acceptProposedAction()
    
    def create_component_widget(self, component_type, component_name, position):
        """컴포넌트 위젯 생성"""
        widget = ComponentWidget(component_type, component_name)
        widget.move(position)
        widget.setParent(self)
        widget.show()
        
        # 컴포넌트 연결 가능하도록 핸들러 추가
        widget.connectionRequested.connect(self.on_connection_requested)
        
        return widget
    
    def on_connection_requested(self, source_component, target_component):
        """컴포넌트 연결 요청 처리"""
        connection = ComponentConnection(source_component, target_component)
        self.connections.append(connection)
        self.update_canvas()
```

---

## 🔬 **컴포넌트 실행 엔진**

### **⚙️ 규칙 기반 실행 엔진**

```python
class ComponentBasedExecutionEngine:
    """컴포넌트 기반 실행 엔진"""
    
    def __init__(self, strategy_config):
        self.strategy_config = strategy_config
        self.component_factory = ComponentFactory()
        self.execution_context = ExecutionContext()
        self.rules = self._load_rules(strategy_config["rules"])
        
    def _load_rules(self, rules_config):
        """규칙들을 컴포넌트로 로드"""
        rules = []
        
        for rule_config in rules_config:
            rule = StrategyRule(
                rule_id=rule_config["rule_id"],
                description=rule_config["description"],
                enabled=rule_config.get("enabled", True),
                trigger=self.component_factory.create_trigger(rule_config["trigger"]),
                conditions=self.component_factory.create_conditions(rule_config.get("conditions", [])),
                action=self.component_factory.create_action(rule_config["action"])
            )
            rules.append(rule)
            
        return rules
    
    def execute_cycle(self, market_data):
        """실행 사이클"""
        execution_result = {
            "timestamp": market_data["timestamp"],
            "triggered_rules": [],
            "executed_actions": [],
            "context_updates": []
        }
        
        # 모든 활성화된 규칙을 평가
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            # 1. 트리거 조건 평가
            if rule.trigger.evaluate(market_data, self.execution_context):
                
                # 2. 추가 조건들 평가
                if self._evaluate_conditions(rule.conditions, market_data):
                    
                    # 3. 액션 실행
                    action_result = rule.action.execute(market_data, self.execution_context)
                    
                    execution_result["triggered_rules"].append(rule.rule_id)
                    execution_result["executed_actions"].append(action_result)
                    
                    # 4. 컨텍스트 업데이트
                    self._update_context(action_result)
        
        return execution_result
    
    def _evaluate_conditions(self, conditions, market_data):
        """조건들 평가"""
        if not conditions:
            return True
            
        for condition in conditions:
            if not condition.evaluate(market_data, self.execution_context):
                return False
                
        return True
```

### **🏭 컴포넌트 팩토리**

```python
class ComponentFactory:
    """컴포넌트 생성 팩토리"""
    
    def __init__(self):
        self.trigger_registry = {
            "PriceChangeTrigger": PriceChangeTriggerComponent,
            "RSITrigger": RSITriggerComponent,
            "MACDCrossTrigger": MACDCrossTriggerComponent,
            "ManualTrigger": ManualTriggerComponent,
            "CompositeANDTrigger": CompositeANDTriggerComponent
        }
        
        self.condition_registry = {
            "PositionExistsCondition": PositionExistsConditionComponent,
            "NoPositionCondition": NoPositionConditionComponent,
            "MaxCountCondition": MaxCountConditionComponent,
            "ProfitableCondition": ProfitableConditionComponent
        }
        
        self.action_registry = {
            "FixedAmountBuy": FixedAmountBuyActionComponent,
            "AdditionalBuy": AdditionalBuyActionComponent,
            "FullPositionSell": FullPositionSellActionComponent,
            "CalculatedBuy": CalculatedBuyActionComponent
        }
    
    def create_trigger(self, trigger_config):
        """트리거 컴포넌트 생성"""
        component_class = self.trigger_registry.get(trigger_config["component"])
        if component_class:
            return component_class(trigger_config["parameters"])
        else:
            raise ValueError(f"Unknown trigger component: {trigger_config['component']}")
    
    def create_conditions(self, conditions_config):
        """조건 컴포넌트들 생성"""
        conditions = []
        for condition_config in conditions_config:
            component_class = self.condition_registry.get(condition_config["component"])
            if component_class:
                conditions.append(component_class(condition_config["parameters"]))
            else:
                raise ValueError(f"Unknown condition component: {condition_config['component']}")
        return conditions
    
    def create_action(self, action_config):
        """액션 컴포넌트 생성"""
        component_class = self.action_registry.get(action_config["component"])
        if component_class:
            return component_class(action_config["parameters"])
        else:
            raise ValueError(f"Unknown action component: {action_config['component']}")
```

---

## 🎯 **다음 단계 계획**

### **Phase 1: 핵심 컴포넌트 구현** ⏱️ 1-2일
1. ✅ 컴포넌트 아키텍처 설계 완료
2. 🔲 기본 트리거 컴포넌트 구현 (가격, 지표, 시간)
3. 🔲 기본 액션 컴포넌트 구현 (매수, 매도, 관리)
4. 🔲 기본 조건 컴포넌트 구현 (포지션, 수익, 논리)

### **Phase 2: 실행 엔진 구현** ⏱️ 2-3일  
1. 🔲 컴포넌트 팩토리 구현
2. 🔲 규칙 기반 실행 엔진 구현
3. 🔲 실행 컨텍스트 관리 시스템 구현
4. 🔲 백테스트 엔진 통합

### **Phase 3: UI 구현** ⏱️ 3-4일
1. 🔲 비주얼 전략 빌더 UI 구현
2. 🔲 드래그 앤 드롭 인터페이스 구현  
3. 🔲 컴포넌트 속성 편집 패널 구현
4. 🔲 실시간 전략 테스트 기능 구현

### **Phase 4: 통합 및 테스트** ⏱️ 2-3일
1. 🔲 기존 시스템과 통합
2. 🔲 물타기/피라미딩 전략 템플릿 구현
3. 🔲 종합 테스트 및 최적화
4. 🔲 사용자 매뉴얼 작성

---

**💡 지금 즉시 Phase 1부터 시작합니다!** 🚀
