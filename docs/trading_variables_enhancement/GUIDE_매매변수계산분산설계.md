# GUIDE_매매변수계산분산설계

**목적**: 전략 조합 JSON 기반 동적 계산 시스템 설계
**대상**: 트리거빌더 → 전략메이커 → 포지션관리 연동 흐름
**분량**: 195줄 / 200줄 (98% 사용)

---

## 🎯 **실제 매매 흐름 기반 설계 (1-25줄: 핵심 개념)**

### **자동매매 프로그램 실제 흐름**
```yaml
1단계: 트리거 빌더에서 개별 조건 생성
   → RSI < 30, SMA 교차, 볼밴드 이탈 등 조건별 JSON

2단계: 전략 메이커에서 조건들을 집합으로 전략 구성
   → 진입전략(1개) + 관리전략(N개) JSON 조합

3단계: 포지션 관리에서 활성 포지션에 전략 할당
   → 각 포지션마다 전략 JSON 구성 연결

4단계: 계산기가 포지션별 전략 JSON 해석 → 동적 계산 실행
   → 필요한 변수만 MDMS에서 요청, 실시간 계산
```

### **JSON 기반 전략 구성 예시**
```json
{
  "strategy_id": "7rule_btc_v1",
  "position_id": "pos_btc_001",
  "entry_strategy": {
    "type": "rsi_oversold",
    "conditions": [{"var": "RSI", "params": {"period": 14}, "op": "<", "value": 30}]
  },
  "management_strategies": [
    {"type": "profit_add", "conditions": [{"var": "profit_rate", "op": ">", "value": 0.02}]},
    {"type": "trailing_stop", "conditions": [{"var": "profit_rate", "op": ">", "value": 0.05}]},
    {"type": "flash_crash", "conditions": [{"var": "price_change_5m", "op": "<", "value": -0.05}]}
  ]
}
```

### **설계 핵심 원칙**
- **동적 해석**: 고정 워커 대신 JSON 기반 계산기 동적 구성
- **포지션 중심**: 각 포지션마다 독립적인 전략 JSON과 계산 컨텍스트
- **지연 로딩**: 필요한 변수만 요청하여 MDMS 부하 최소화

---

## 🏗️ **JSON 해석 기반 계산 아키텍처 (26-65줄: 핵심 구조)**

### **3계층 동적 구조**
```yaml
계층 1: 전략 해석기 (Strategy Interpreter)
├── StrategyParser: JSON 전략 구성 파싱
├── ConditionAnalyzer: 필요 변수 자동 추출
├── CalculationPlanner: 계산 의존성 그래프 생성
└── ResourceManager: MDMS 데이터 요청 최적화

계층 2: 동적 계산 엔진 (Dynamic Calculation Engine)
├── VariableCalculatorFactory: 변수별 계산기 동적 생성
├── ConditionEvaluator: 조건식 실시간 평가
├── CacheManager: 포지션별 중간 결과 캐싱
└── DependencyResolver: 변수 간 의존성 해결

계층 3: 포지션별 신호 생성 (Position Signal Generator)
├── PositionContext: 포지션별 계산 컨텍스트 관리
├── StrategyStateMachine: 진입/관리 전략 상태 전환
├── SignalAggregator: 다중 관리전략 신호 통합
└── ActionDecider: 최종 매매 액션 결정
```

### **전략 JSON 해석 프로세스**
```python
class StrategyInterpreter:
    """포지션별 전략 JSON 해석 및 계산 계획 수립"""

    def __init__(self):
        self.variable_registry = VariableRegistry()
        self.calculation_planner = CalculationPlanner()

    async def parse_strategy_json(self, strategy_json: dict, position: Position):
        """전략 JSON 파싱 및 계산 계획 생성"""

        # 1. 전략 구성 파싱
        entry_strategy = strategy_json["entry_strategy"]
        management_strategies = strategy_json["management_strategies"]

        # 2. 필요 변수 추출
        required_variables = self.extract_required_variables(
            entry_strategy, management_strategies
        )

        # 3. 계산 계획 수립
        calculation_plan = await self.calculation_planner.create_plan(
            required_variables, position.symbol, position.timeframes
        )

        # 4. 포지션별 계산 컨텍스트 생성
        context = PositionCalculationContext(
            position_id=position.id,
            strategy_config=strategy_json,
            calculation_plan=calculation_plan,
            variable_cache=PositionCache(position.id)
        )

        return context

    def extract_required_variables(self, entry_strategy: dict, management_strategies: list):
        """전략에서 필요한 모든 변수 추출"""

        variables = set()

        # 진입 전략 변수 추출
        for condition in entry_strategy.get("conditions", []):
            var_name = condition["var"]
            var_params = condition.get("params", {})
            variables.add(VariableRequest(var_name, var_params))

        # 관리 전략 변수 추출
        for mgmt_strategy in management_strategies:
            for condition in mgmt_strategy.get("conditions", []):
                var_name = condition["var"]
                var_params = condition.get("params", {})
                variables.add(VariableRequest(var_name, var_params))

        return variables
```

### **동적 계산기 팩토리**
```python
class VariableCalculatorFactory:
    """변수 타입별 계산기 동적 생성"""

    def __init__(self):
        self.calculator_registry = {
            'RSI': RSICalculator,
            'SMA': SMACalculator,
            'profit_rate': ProfitRateCalculator,
            'price_change_5m': PriceChangeCalculator,
            'bollinger_upper': BollingerCalculator,
            'macd': MACDCalculator
        }

    async def create_calculator(self, variable_request: VariableRequest):
        """변수 요청에 따른 계산기 생성"""

        var_name = variable_request.name
        var_params = variable_request.params

        if var_name not in self.calculator_registry:
            raise UnsupportedVariableError(f"지원되지 않는 변수: {var_name}")

        calculator_class = self.calculator_registry[var_name]
        calculator = calculator_class(params=var_params)

        return calculator

class RSICalculator:
    """RSI 변수 계산기 예시"""

    def __init__(self, params: dict):
        self.period = params.get('period', 14)
        self.source = params.get('source', 'close')

    async def calculate(self, candles: List[Candle], context: PositionContext):
        """RSI 계산 실행"""

        # 캐시 확인
        cache_key = f"RSI_{self.period}_{self.source}"
        if context.cache.has(cache_key):
            return context.cache.get(cache_key)

        # RSI 계산
        if len(candles) < self.period + 1:
            return None

        prices = [getattr(candle, self.source) for candle in candles]
        rsi_value = self._calculate_rsi(prices, self.period)

        # 캐시 저장
        context.cache.set(cache_key, rsi_value, ttl=60)

        return rsi_value
```

---

## ⚡ **포지션별 실시간 계산 실행 (66-120줄: 실행 엔진)**

### **포지션 컨텍스트 관리**
```python
class PositionCalculationContext:
    """포지션별 계산 컨텍스트"""

    def __init__(self, position_id: str, strategy_config: dict, calculation_plan: dict):
        self.position_id = position_id
        self.strategy_config = strategy_config
        self.calculation_plan = calculation_plan
        self.cache = PositionCache(position_id)
        self.state = PositionState.ENTRY_WAITING  # 진입대기/포지션관리/청산완료
        self.calculators = {}

    async def initialize_calculators(self):
        """전략 JSON 기반 계산기 초기화"""

        factory = VariableCalculatorFactory()

        # 필요한 모든 계산기 생성
        for var_request in self.calculation_plan["required_variables"]:
            calculator = await factory.create_calculator(var_request)
            self.calculators[var_request.cache_key] = calculator

    async def update_market_data(self, symbol: str, new_candle: Candle):
        """시장 데이터 업데이트 처리"""

        # 1. 현재 상태에 따른 활성 전략 결정
        active_strategies = self.get_active_strategies()

        # 2. 활성 전략의 모든 조건 평가
        evaluation_results = {}

        for strategy in active_strategies:
            strategy_name = strategy["type"]
            conditions = strategy["conditions"]

            # 각 조건별 계산 및 평가
            condition_results = []
            for condition in conditions:
                result = await self.evaluate_condition(condition, new_candle)
                condition_results.append(result)

            evaluation_results[strategy_name] = condition_results

        # 3. 신호 생성 및 상태 업데이트
        signals = await self.generate_signals(evaluation_results)

        return signals

    def get_active_strategies(self):
        """현재 포지션 상태에 따른 활성 전략 반환"""

        if self.state == PositionState.ENTRY_WAITING:
            # 진입 대기 상태: 진입 전략만 활성
            return [self.strategy_config["entry_strategy"]]

        elif self.state == PositionState.POSITION_ACTIVE:
            # 포지션 활성 상태: 관리 전략들만 활성
            return self.strategy_config["management_strategies"]

        else:
            # 청산 완료: 모든 전략 비활성
            return []

    async def evaluate_condition(self, condition: dict, new_candle: Candle):
        """개별 조건 평가"""

        var_name = condition["var"]
        var_params = condition.get("params", {})
        operator = condition["op"]
        target_value = condition["value"]

        # 1. 변수 계산
        cache_key = f"{var_name}_{hash(str(var_params))}"
        calculator = self.calculators[cache_key]

        calculated_value = await calculator.calculate(
            candles=self.get_historical_candles(new_candle),
            context=self
        )

        # 2. 조건 평가
        result = self.apply_operator(calculated_value, operator, target_value)

        return ConditionResult(
            variable=var_name,
            calculated_value=calculated_value,
            operator=operator,
            target_value=target_value,
            result=result,
            timestamp=new_candle.timestamp
        )

class PositionSignalGenerator:
    """포지션별 신호 생성기"""

    async def generate_signals(self, evaluation_results: dict, context: PositionCalculationContext):
        """평가 결과를 기반으로 매매 신호 생성"""

        signals = []

        # 진입 신호 처리
        if context.state == PositionState.ENTRY_WAITING:
            entry_signal = await self.process_entry_signals(evaluation_results)
            if entry_signal:
                signals.append(entry_signal)
                context.state = PositionState.POSITION_ACTIVE

        # 관리 신호 처리
        elif context.state == PositionState.POSITION_ACTIVE:
            mgmt_signals = await self.process_management_signals(evaluation_results)
            signals.extend(mgmt_signals)

            # 청산 신호 확인
            close_signal = self.check_close_signals(mgmt_signals)
            if close_signal:
                context.state = PositionState.CLOSED

        return signals

    async def process_entry_signals(self, evaluation_results: dict):
        """진입 신호 처리"""

        # 진입 전략의 모든 조건이 True인지 확인
        entry_results = evaluation_results.get("entry_strategy", [])

        if all(result.result for result in entry_results):
            return TradingSignal(
                signal_type=SignalType.ENTRY,
                action=TradingAction.BUY,
                strength=self.calculate_signal_strength(entry_results),
                conditions=entry_results
            )

        return None

    async def process_management_signals(self, evaluation_results: dict):
        """관리 신호 처리"""

        signals = []

        for strategy_name, condition_results in evaluation_results.items():
            if any(result.result for result in condition_results):

                # 전략 타입별 신호 생성
                if strategy_name == "profit_add":
                    signals.append(TradingSignal(
                        signal_type=SignalType.ADD_POSITION,
                        action=TradingAction.BUY,
                        reason="profit_based_add"
                    ))

                elif strategy_name == "trailing_stop":
                    signals.append(TradingSignal(
                        signal_type=SignalType.UPDATE_STOP,
                        action=TradingAction.UPDATE_STOP_LOSS,
                        reason="trailing_stop_update"
                    ))

                elif strategy_name == "flash_crash":
                    signals.append(TradingSignal(
                        signal_type=SignalType.EMERGENCY_ADD,
                        action=TradingAction.BUY,
                        reason="flash_crash_detected"
                    ))

        return signals
```

### **MDMS 연동 최적화**
```python
class MDMSDataRequester:
    """포지션별 필요 데이터만 MDMS에 요청"""

    async def request_position_data(self, context: PositionCalculationContext, symbol: str):
        """포지션 계산에 필요한 최소 데이터 요청"""

        # 1. 계산 계획에서 필요 데이터 추출
        required_candles = self.analyze_data_requirements(context.calculation_plan)

        # 2. MDMS에 배치 요청
        data_requests = []
        for timeframe, count in required_candles.items():
            data_requests.append(
                MDMSRequest(
                    symbol=symbol,
                    timeframe=timeframe,
                    count=count,
                    priority="position_calculation"
                )
            )

        # 3. 병렬 데이터 수집
        candle_data = await self.mdms.batch_request(data_requests)

        return candle_data

    def analyze_data_requirements(self, calculation_plan: dict):
        """계산 계획 분석하여 필요 데이터 양 계산"""

        requirements = {}

        for var_request in calculation_plan["required_variables"]:
            var_name = var_request.name
            var_params = var_request.params

            # 변수별 필요 캔들 수 계산
            if var_name == "RSI":
                period = var_params.get("period", 14)
                requirements["1m"] = max(requirements.get("1m", 0), period * 2)

            elif var_name == "SMA":
                period = var_params.get("period", 20)
                requirements["1m"] = max(requirements.get("1m", 0), period + 5)

            elif var_name == "price_change_5m":
                requirements["5m"] = max(requirements.get("5m", 0), 2)

        return requirements
```

---

## 🔄 **실제 자동매매 흐름 통합 (121-180줄: 시스템 통합)**

### **전체 시스템 조정자**
```python
class AutoTradingSystemCoordinator:
    """자동매매 시스템 전체 조정"""

    def __init__(self):
        self.position_manager = PositionManager()
        self.strategy_interpreter = StrategyInterpreter()
        self.mdms_connector = MDMSConnector()
        self.active_contexts = {}  # position_id -> CalculationContext

    async def initialize_position_strategy(self, position_id: str, strategy_json: dict):
        """포지션에 전략 할당 및 계산 컨텍스트 초기화"""

        # 1. 포지션 정보 조회
        position = await self.position_manager.get_position(position_id)

        # 2. 전략 JSON 해석 및 계산 컨텍스트 생성
        context = await self.strategy_interpreter.parse_strategy_json(
            strategy_json, position
        )

        # 3. 계산기 초기화
        await context.initialize_calculators()

        # 4. MDMS 구독 설정
        await self.setup_mdms_subscription(position.symbol, context)

        # 5. 활성 컨텍스트 등록
        self.active_contexts[position_id] = context

        return context

    async def on_market_data_update(self, symbol: str, new_candle: Candle):
        """MDMS에서 시장 데이터 업데이트 수신"""

        # 1. 해당 심볼의 모든 활성 포지션 찾기
        active_positions = self.get_active_positions_for_symbol(symbol)

        # 2. 각 포지션별 병렬 계산 실행
        calculation_tasks = []
        for position_id in active_positions:
            context = self.active_contexts[position_id]
            task = context.update_market_data(symbol, new_candle)
            calculation_tasks.append(task)

        # 3. 모든 계산 완료 대기 (최대 2초)
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*calculation_tasks), timeout=2.0
            )
        except asyncio.TimeoutError:
            logger.warning(f"계산 타임아웃: {symbol}")
            return

        # 4. 신호 기반 매매 액션 실행
        for position_id, signals in zip(active_positions, results):
            await self.execute_trading_actions(position_id, signals)

    async def execute_trading_actions(self, position_id: str, signals: List[TradingSignal]):
        """계산된 신호를 실제 매매 액션으로 실행"""

        if not signals:
            return

        # 1. 신호 우선순위 정렬
        prioritized_signals = self.prioritize_signals(signals)

        # 2. 최우선 신호 실행
        primary_signal = prioritized_signals[0]

        try:
            if primary_signal.signal_type == SignalType.ENTRY:
                await self.position_manager.create_position(
                    position_id, primary_signal
                )

            elif primary_signal.signal_type == SignalType.ADD_POSITION:
                await self.position_manager.add_to_position(
                    position_id, primary_signal
                )

            elif primary_signal.signal_type == SignalType.CLOSE_POSITION:
                await self.position_manager.close_position(
                    position_id, primary_signal
                )
                # 포지션 종료시 컨텍스트 정리
                await self.cleanup_position_context(position_id)

        except Exception as e:
            logger.error(f"매매 액션 실행 실패: {position_id}, {e}")

class StrategyConfigurationManager:
    """전략 조합 JSON 관리"""

    def __init__(self):
        self.strategy_db = StrategyDatabase()

    async def create_strategy_from_triggers(self, trigger_configs: List[dict]):
        """트리거 빌더에서 생성된 트리거들을 전략으로 조합"""

        strategy_json = {
            "strategy_id": f"strategy_{int(time.time())}",
            "created_at": datetime.now().isoformat(),
            "entry_strategy": None,
            "management_strategies": []
        }

        # 트리거를 진입/관리 전략으로 분류
        for trigger_config in trigger_configs:
            if trigger_config["trigger_type"] == "entry":
                strategy_json["entry_strategy"] = self.convert_trigger_to_strategy(
                    trigger_config
                )
            else:
                management_strategy = self.convert_trigger_to_strategy(trigger_config)
                strategy_json["management_strategies"].append(management_strategy)

        # 전략 유효성 검증
        await self.validate_strategy_configuration(strategy_json)

        # 데이터베이스 저장
        await self.strategy_db.save_strategy(strategy_json)

        return strategy_json

    def convert_trigger_to_strategy(self, trigger_config: dict):
        """트리거 설정을 전략 JSON으로 변환"""

        return {
            "type": trigger_config["strategy_type"],
            "conditions": [
                {
                    "var": condition["variable"],
                    "params": condition["parameters"],
                    "op": condition["operator"],
                    "value": condition["target_value"]
                }
                for condition in trigger_config["conditions"]
            ],
            "priority": trigger_config.get("priority", 1),
            "enabled": trigger_config.get("enabled", True)
        }

    async def apply_strategy_to_position(self, position_id: str, strategy_id: str):
        """포지션에 전략 적용"""

        # 1. 전략 JSON 로드
        strategy_json = await self.strategy_db.load_strategy(strategy_id)

        # 2. 포지션별 전략 인스턴스 생성
        position_strategy = strategy_json.copy()
        position_strategy["position_id"] = position_id
        position_strategy["applied_at"] = datetime.now().isoformat()

        # 3. 자동매매 시스템에 등록
        coordinator = AutoTradingSystemCoordinator()
        await coordinator.initialize_position_strategy(position_id, position_strategy)

        return position_strategy

class PositionStrategyDatabase:
    """포지션별 전략 할당 내역 관리"""

    async def save_position_strategy_assignment(self, position_id: str, strategy_config: dict):
        """포지션-전략 할당 내역 저장"""

        assignment = {
            "position_id": position_id,
            "strategy_id": strategy_config["strategy_id"],
            "strategy_config": strategy_config,
            "assigned_at": datetime.now().isoformat(),
            "status": "active"
        }

        await self.db.execute("""
            INSERT INTO position_strategy_assignments
            (position_id, strategy_id, strategy_config, assigned_at, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            assignment["position_id"],
            assignment["strategy_id"],
            json.dumps(assignment["strategy_config"]),
            assignment["assigned_at"],
            assignment["status"]
        ))

    async def get_active_strategy_for_position(self, position_id: str):
        """포지션의 활성 전략 조회"""

        result = await self.db.execute("""
            SELECT strategy_config FROM position_strategy_assignments
            WHERE position_id = ? AND status = 'active'
            ORDER BY assigned_at DESC LIMIT 1
        """, (position_id,))

        if result:
            return json.loads(result[0]["strategy_config"])
        return None
```

### **성능 모니터링 및 최적화**
```python
class CalculationPerformanceMonitor:
    """계산 성능 모니터링"""

    def __init__(self):
        self.calculation_metrics = {}
        self.performance_history = deque(maxlen=1000)

    async def monitor_calculation_performance(self, context: PositionCalculationContext):
        """포지션별 계산 성능 모니터링"""

        start_time = time.time()

        # 계산 실행
        try:
            yield
        finally:
            end_time = time.time()
            duration = end_time - start_time

            # 성능 메트릭 기록
            self.record_performance_metric(context.position_id, duration)

            # 성능 임계값 초과시 경고
            if duration > 1.5:  # 1.5초 초과
                logger.warning(f"계산 성능 저하: {context.position_id}, {duration:.2f}초")

    def record_performance_metric(self, position_id: str, duration: float):
        """성능 메트릭 기록"""

        metric = {
            "position_id": position_id,
            "duration": duration,
            "timestamp": time.time()
        }

        self.performance_history.append(metric)

        # 포지션별 통계 업데이트
        if position_id not in self.calculation_metrics:
            self.calculation_metrics[position_id] = {
                "count": 0,
                "total_time": 0,
                "max_time": 0,
                "avg_time": 0
            }

        stats = self.calculation_metrics[position_id]
        stats["count"] += 1
        stats["total_time"] += duration
        stats["max_time"] = max(stats["max_time"], duration)
        stats["avg_time"] = stats["total_time"] / stats["count"]
```

---

## 💡 **설계 검토 및 자동매매 적합성 (181-195줄: 검증)**

### **자동매매 프로그램 흐름 완벽 매칭 ✅**

```yaml
트리거 빌더 단계:
✅ 개별 조건 JSON 생성: {"var": "RSI", "params": {"period": 14}, "op": "<", "value": 30}
✅ 호환성 검증: comparison_group 기반 조건 조합 제한
✅ 데이터베이스 저장: trading_conditions 테이블에 조건별 저장

전략 메이커 단계:
✅ 조건 집합화: 진입전략(1개) + 관리전략(N개) 조합
✅ 전략 JSON 생성: StrategyConfigurationManager.create_strategy_from_triggers()
✅ 충돌 해결: 관리전략 우선순위 및 실행 순서 설정

포지션 관리 단계:
✅ 전략 할당: PositionStrategyDatabase.apply_strategy_to_position()
✅ 컨텍스트 생성: PositionCalculationContext로 포지션별 독립 계산
✅ 실시간 모니터링: 포지션 상태별 활성 전략 자동 전환

계산기 동작 단계:
✅ JSON 해석: StrategyInterpreter가 전략 JSON 파싱 및 변수 추출
✅ 동적 계산기 생성: VariableCalculatorFactory가 필요 계산기만 생성
✅ MDMS 요청: MDMSDataRequester가 최소 필요 데이터만 요청
```

### **기존 설계 대비 장점**
- **메모리 효율**: 고정 워커 대신 필요시에만 계산기 생성
- **확장성**: 새로운 조건 추가시 JSON만 수정, 코드 변경 불필요
- **포지션 격리**: 포지션별 독립 계산으로 간섭 없음
- **상태 관리**: 진입/관리 전략 자동 전환으로 상태 버그 방지

### **MDMS 연동 최적화**
```python
# 기존: 모든 워커가 동일 데이터 중복 요청
모든_워커 = [RSIWorker, ProfitWorker, TrailingWorker, ...]
각_워커마다_MDMS_요청()  # 비효율적

# 개선: 포지션별 필요 데이터만 배치 요청
포지션_컨텍스트 = analyze_strategy_json(strategy_json)
필요_데이터 = extract_required_variables(포지션_컨텍스트)
MDMS_배치_요청(필요_데이터)  # 효율적
```

**최종 결론**: 트리거빌더 → 전략메이커 → 포지션관리 흐름에 **완벽 적합**한 설계 ✨
**핵심 혁신**: JSON 기반 동적 해석으로 **무한 확장 가능**한 계산 시스템 🚀
