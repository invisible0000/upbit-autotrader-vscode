# 🚀 새로운 전략 추가 가이드

> **목적**: Clean Architecture에서 새로운 매매 전략을 체계적으로 추가하는 방법  
> **대상**: 개발자, 전략 개발자  
> **예상 읽기 시간**: 16분

## 🎯 전략 추가 개요

### 📋 추가 프로세스
1. **도메인 모델 정의**: 전략의 핵심 비즈니스 로직
2. **애플리케이션 서비스**: 전략 실행 및 관리 로직
3. **인프라 구현**: 데이터 저장 및 외부 연동
4. **프레젠테이션**: UI 통합 및 사용자 인터페이스
5. **테스팅**: 단위 테스트 및 백테스팅 검증

### 🎯 예시 전략: "스토캐스틱 RSI 전략"
- **진입**: Stochastic RSI가 20 이하에서 상승 전환
- **익절**: 15% 수익 시 전량 매도
- **손절**: 5% 손실 시 전량 매도
- **관리**: 활성 트레일링 스탑 (8% 수익 후 3% 추적)

## 💎 Domain Layer 구현

### 1. 전략 도메인 모델
```python
# domain/entities/strategies/stochastic_rsi_strategy.py
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List
from datetime import datetime

@dataclass(frozen=True)
class StochasticRSIStrategyId:
    """스토캐스틱 RSI 전략 ID"""
    value: str

class StochasticRSIStrategy:
    """스토캐스틱 RSI 전략 도메인 엔티티"""
    
    def __init__(
        self,
        id: StochasticRSIStrategyId,
        name: str,
        rsi_period: int = 14,
        stochastic_period: int = 14,
        oversold_threshold: Decimal = Decimal('20'),
        overbought_threshold: Decimal = Decimal('80'),
        take_profit_rate: Decimal = Decimal('0.15'),
        stop_loss_rate: Decimal = Decimal('0.05'),
        trailing_stop_activation: Decimal = Decimal('0.08'),
        trailing_stop_distance: Decimal = Decimal('0.03')
    ):
        self.id = id
        self.name = name
        
        # 핵심 파라미터
        self.rsi_period = rsi_period
        self.stochastic_period = stochastic_period
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold
        
        # 리스크 관리 파라미터
        self.take_profit_rate = take_profit_rate
        self.stop_loss_rate = stop_loss_rate
        self.trailing_stop_activation = trailing_stop_activation
        self.trailing_stop_distance = trailing_stop_distance
        
        # 상태 관리
        self._is_active = True
        self._last_signal: Optional['StrategySignal'] = None
        self._created_at = datetime.utcnow()
        
        # 유효성 검증
        self._validate_parameters()
    
    def _validate_parameters(self):
        """파라미터 유효성 검증"""
        if self.rsi_period < 2 or self.rsi_period > 100:
            raise ValueError("RSI 기간은 2-100 사이여야 합니다")
        
        if self.stochastic_period < 2 or self.stochastic_period > 100:
            raise ValueError("스토캐스틱 기간은 2-100 사이여야 합니다")
        
        if not (0 < self.oversold_threshold < self.overbought_threshold < 100):
            raise ValueError("임계값은 0 < 과매도 < 과매수 < 100 이어야 합니다")
        
        if self.take_profit_rate <= 0 or self.stop_loss_rate <= 0:
            raise ValueError("익절/손절 비율은 0보다 커야 합니다")
        
        if self.trailing_stop_activation <= self.take_profit_rate:
            raise ValueError("트레일링 스탑 활성화는 익절 비율보다 작아야 합니다")
    
    def generate_signal(
        self, 
        market_data: 'MarketDataPoint', 
        historical_data: List['MarketDataPoint'],
        current_position: Optional['Position'] = None
    ) -> Optional['StrategySignal']:
        """전략 신호 생성"""
        
        # 충분한 데이터 확인
        if len(historical_data) < max(self.rsi_period, self.stochastic_period) + 1:
            return None
        
        # 지표 계산
        stoch_rsi_values = self._calculate_stochastic_rsi(historical_data)
        if not stoch_rsi_values:
            return None
        
        current_stoch_rsi = stoch_rsi_values[-1]
        previous_stoch_rsi = stoch_rsi_values[-2] if len(stoch_rsi_values) > 1 else None
        
        # 포지션 상태에 따른 신호 생성
        if current_position is None or current_position.is_closed():
            # 진입 신호 확인
            signal = self._check_entry_signal(current_stoch_rsi, previous_stoch_rsi, market_data)
        else:
            # 청산 신호 확인
            signal = self._check_exit_signal(current_position, market_data, current_stoch_rsi)
        
        self._last_signal = signal
        return signal
    
    def _calculate_stochastic_rsi(self, historical_data: List['MarketDataPoint']) -> List[Decimal]:
        """스토캐스틱 RSI 계산"""
        
        # 1. RSI 계산
        rsi_values = self._calculate_rsi(historical_data)
        
        if len(rsi_values) < self.stochastic_period:
            return []
        
        # 2. RSI에 스토캐스틱 적용
        stoch_rsi_values = []
        
        for i in range(self.stochastic_period - 1, len(rsi_values)):
            period_rsi = rsi_values[i - self.stochastic_period + 1:i + 1]
            
            min_rsi = min(period_rsi)
            max_rsi = max(period_rsi)
            current_rsi = period_rsi[-1]
            
            if max_rsi == min_rsi:
                stoch_rsi = Decimal('50')  # 중간값
            else:
                stoch_rsi = ((current_rsi - min_rsi) / (max_rsi - min_rsi)) * 100
            
            stoch_rsi_values.append(stoch_rsi)
        
        return stoch_rsi_values
    
    def _calculate_rsi(self, historical_data: List['MarketDataPoint']) -> List[Decimal]:
        """RSI 계산"""
        if len(historical_data) < self.rsi_period + 1:
            return []
        
        prices = [data.close_price for data in historical_data]
        gains = []
        losses = []
        
        # 가격 변화 계산
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(Decimal('0'))
            else:
                gains.append(Decimal('0'))
                losses.append(abs(change))
        
        if len(gains) < self.rsi_period:
            return []
        
        rsi_values = []
        
        # 첫 번째 RSI 계산 (단순 평균)
        avg_gain = sum(gains[:self.rsi_period]) / self.rsi_period
        avg_loss = sum(losses[:self.rsi_period]) / self.rsi_period
        
        if avg_loss == 0:
            rsi_values.append(Decimal('100'))
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)
        
        # 이후 RSI 계산 (지수 이동 평균)
        for i in range(self.rsi_period, len(gains)):
            avg_gain = (avg_gain * (self.rsi_period - 1) + gains[i]) / self.rsi_period
            avg_loss = (avg_loss * (self.rsi_period - 1) + losses[i]) / self.rsi_period
            
            if avg_loss == 0:
                rsi_values.append(Decimal('100'))
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                rsi_values.append(rsi)
        
        return rsi_values
    
    def _check_entry_signal(
        self,
        current_stoch_rsi: Decimal,
        previous_stoch_rsi: Optional[Decimal],
        market_data: 'MarketDataPoint'
    ) -> Optional['StrategySignal']:
        """진입 신호 확인"""
        
        if previous_stoch_rsi is None:
            return None
        
        # 과매도 구간에서 상승 전환 확인
        if (previous_stoch_rsi <= self.oversold_threshold and 
            current_stoch_rsi > self.oversold_threshold and
            current_stoch_rsi > previous_stoch_rsi):
            
            return StrategySignal(
                action='BUY',
                price=market_data.close_price,
                quantity=None,  # 포지션 크기는 포트폴리오 매니저가 결정
                reason=f"스토캐스틱 RSI 상승 전환: {previous_stoch_rsi:.2f} -> {current_stoch_rsi:.2f}",
                confidence=self._calculate_confidence(current_stoch_rsi, previous_stoch_rsi),
                timestamp=market_data.timestamp,
                strategy_id=self.id.value
            )
        
        return None
    
    def _check_exit_signal(
        self,
        position: 'Position',
        market_data: 'MarketDataPoint',
        current_stoch_rsi: Decimal
    ) -> Optional['StrategySignal']:
        """청산 신호 확인"""
        
        current_price = market_data.close_price
        profit_rate = (current_price - position.entry_price) / position.entry_price
        
        # 손절 확인
        if profit_rate <= -self.stop_loss_rate:
            return StrategySignal(
                action='SELL',
                price=current_price,
                quantity=position.quantity,
                reason=f"손절: {profit_rate:.2%}",
                confidence=Decimal('0.9'),
                timestamp=market_data.timestamp,
                strategy_id=self.id.value
            )
        
        # 익절 확인
        if profit_rate >= self.take_profit_rate:
            return StrategySignal(
                action='SELL',
                price=current_price,
                quantity=position.quantity,
                reason=f"익절: {profit_rate:.2%}",
                confidence=Decimal('0.8'),
                timestamp=market_data.timestamp,
                strategy_id=self.id.value
            )
        
        # 과매수 구간 청산 확인
        if current_stoch_rsi >= self.overbought_threshold:
            return StrategySignal(
                action='SELL',
                price=current_price,
                quantity=position.quantity,
                reason=f"과매수 청산: 스토캐스틱 RSI {current_stoch_rsi:.2f}",
                confidence=Decimal('0.7'),
                timestamp=market_data.timestamp,
                strategy_id=self.id.value
            )
        
        # 트레일링 스탑 확인
        if profit_rate >= self.trailing_stop_activation:
            trailing_stop_price = position.highest_price * (1 - self.trailing_stop_distance)
            if current_price <= trailing_stop_price:
                return StrategySignal(
                    action='SELL',
                    price=current_price,
                    quantity=position.quantity,
                    reason=f"트레일링 스탑: {current_price} <= {trailing_stop_price}",
                    confidence=Decimal('0.85'),
                    timestamp=market_data.timestamp,
                    strategy_id=self.id.value
                )
        
        return None
    
    def _calculate_confidence(
        self, 
        current_stoch_rsi: Decimal, 
        previous_stoch_rsi: Decimal
    ) -> Decimal:
        """신호 신뢰도 계산"""
        
        # 과매도 구간에서 멀수록 신뢰도 감소
        distance_from_oversold = current_stoch_rsi - self.oversold_threshold
        
        # 상승폭이 클수록 신뢰도 증가
        momentum = current_stoch_rsi - previous_stoch_rsi
        
        # 기본 신뢰도에서 조정
        base_confidence = Decimal('0.7')
        distance_factor = max(Decimal('0'), Decimal('10') - distance_from_oversold) / Decimal('10')
        momentum_factor = min(momentum / Decimal('10'), Decimal('0.2'))
        
        confidence = base_confidence + (distance_factor * Decimal('0.2')) + momentum_factor
        return max(Decimal('0.1'), min(confidence, Decimal('1.0')))
    
    def update_parameters(self, **kwargs):
        """파라미터 업데이트"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self._validate_parameters()
    
    def get_strategy_info(self) -> Dict:
        """전략 정보 반환"""
        return {
            'id': self.id.value,
            'name': self.name,
            'type': 'StochasticRSI',
            'parameters': {
                'rsi_period': self.rsi_period,
                'stochastic_period': self.stochastic_period,
                'oversold_threshold': float(self.oversold_threshold),
                'overbought_threshold': float(self.overbought_threshold),
                'take_profit_rate': float(self.take_profit_rate),
                'stop_loss_rate': float(self.stop_loss_rate),
                'trailing_stop_activation': float(self.trailing_stop_activation),
                'trailing_stop_distance': float(self.trailing_stop_distance)
            },
            'is_active': self._is_active,
            'created_at': self._created_at.isoformat()
        }

# domain/value_objects/strategy_signal.py
@dataclass
class StrategySignal:
    """전략 신호 값 객체"""
    action: str  # 'BUY', 'SELL', 'HOLD'
    price: Decimal
    quantity: Optional[Decimal]
    reason: str
    confidence: Decimal  # 0.0 ~ 1.0
    timestamp: datetime
    strategy_id: str
    
    def __post_init__(self):
        """유효성 검증"""
        if self.action not in ['BUY', 'SELL', 'HOLD']:
            raise ValueError(f"지원하지 않는 액션: {self.action}")
        
        if not (0 <= self.confidence <= 1):
            raise ValueError("신뢰도는 0과 1 사이여야 합니다")
        
        if self.price <= 0:
            raise ValueError("가격은 0보다 커야 합니다")
```

### 2. 전략 팩토리 및 레지스트리
```python
# domain/services/strategy_factory.py
class StrategyFactory:
    """전략 팩토리"""
    
    def __init__(self):
        self._strategy_builders = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """기본 전략들 등록"""
        self._strategy_builders['StochasticRSI'] = self._build_stochastic_rsi_strategy
        self._strategy_builders['RSI'] = self._build_rsi_strategy
        self._strategy_builders['MovingAverage'] = self._build_ma_strategy
        # 추가 전략들...
    
    def create_strategy(self, strategy_config: Dict) -> 'BaseStrategy':
        """전략 생성"""
        strategy_type = strategy_config.get('type')
        
        if strategy_type not in self._strategy_builders:
            raise ValueError(f"지원하지 않는 전략 타입: {strategy_type}")
        
        builder = self._strategy_builders[strategy_type]
        return builder(strategy_config)
    
    def _build_stochastic_rsi_strategy(self, config: Dict) -> StochasticRSIStrategy:
        """스토캐스틱 RSI 전략 생성"""
        
        strategy_id = StochasticRSIStrategyId(config.get('id', self._generate_id()))
        
        return StochasticRSIStrategy(
            id=strategy_id,
            name=config.get('name', 'Stochastic RSI Strategy'),
            rsi_period=config.get('rsi_period', 14),
            stochastic_period=config.get('stochastic_period', 14),
            oversold_threshold=Decimal(str(config.get('oversold_threshold', 20))),
            overbought_threshold=Decimal(str(config.get('overbought_threshold', 80))),
            take_profit_rate=Decimal(str(config.get('take_profit_rate', 0.15))),
            stop_loss_rate=Decimal(str(config.get('stop_loss_rate', 0.05))),
            trailing_stop_activation=Decimal(str(config.get('trailing_stop_activation', 0.08))),
            trailing_stop_distance=Decimal(str(config.get('trailing_stop_distance', 0.03)))
        )
    
    def get_available_strategies(self) -> List[str]:
        """사용 가능한 전략 목록"""
        return list(self._strategy_builders.keys())
    
    def get_strategy_parameters(self, strategy_type: str) -> Dict:
        """전략별 파라미터 정의"""
        parameter_definitions = {
            'StochasticRSI': {
                'rsi_period': {'type': 'int', 'min': 2, 'max': 100, 'default': 14},
                'stochastic_period': {'type': 'int', 'min': 2, 'max': 100, 'default': 14},
                'oversold_threshold': {'type': 'float', 'min': 0, 'max': 50, 'default': 20},
                'overbought_threshold': {'type': 'float', 'min': 50, 'max': 100, 'default': 80},
                'take_profit_rate': {'type': 'float', 'min': 0.01, 'max': 1.0, 'default': 0.15},
                'stop_loss_rate': {'type': 'float', 'min': 0.01, 'max': 0.5, 'default': 0.05},
                'trailing_stop_activation': {'type': 'float', 'min': 0.01, 'max': 0.5, 'default': 0.08},
                'trailing_stop_distance': {'type': 'float', 'min': 0.01, 'max': 0.2, 'default': 0.03}
            }
        }
        
        return parameter_definitions.get(strategy_type, {})
    
    def _generate_id(self) -> str:
        """전략 ID 생성"""
        import uuid
        return f"strategy_{uuid.uuid4().hex[:8]}"

# domain/services/strategy_registry.py
class StrategyRegistry:
    """전략 레지스트리"""
    
    def __init__(self):
        self._registered_strategies = {}
    
    def register_strategy(self, strategy: 'BaseStrategy'):
        """전략 등록"""
        self._registered_strategies[strategy.id.value] = strategy
    
    def unregister_strategy(self, strategy_id: str):
        """전략 등록 해제"""
        self._registered_strategies.pop(strategy_id, None)
    
    def get_strategy(self, strategy_id: str) -> Optional['BaseStrategy']:
        """전략 조회"""
        return self._registered_strategies.get(strategy_id)
    
    def get_all_strategies(self) -> List['BaseStrategy']:
        """모든 전략 조회"""
        return list(self._registered_strategies.values())
    
    def get_active_strategies(self) -> List['BaseStrategy']:
        """활성 전략 조회"""
        return [s for s in self._registered_strategies.values() if s._is_active]
```

## ⚙️ Application Layer 구현

### 1. 전략 관리 유스케이스
```python
# application/use_cases/create_strategy_use_case.py
class CreateStrategyUseCase:
    """전략 생성 유스케이스"""
    
    def __init__(
        self,
        strategy_repository,
        strategy_factory,
        strategy_validator,
        event_publisher
    ):
        self.strategy_repository = strategy_repository
        self.strategy_factory = strategy_factory
        self.strategy_validator = strategy_validator
        self.event_publisher = event_publisher
    
    def execute(self, command: CreateStrategyCommand) -> CreateStrategyResult:
        """전략 생성 실행"""
        
        try:
            # 1. 전략 설정 유효성 검증
            validation_result = self.strategy_validator.validate(command.strategy_config)
            if not validation_result.is_valid:
                return CreateStrategyResult.failure(validation_result.error_message)
            
            # 2. 전략 생성
            strategy = self.strategy_factory.create_strategy(command.strategy_config)
            
            # 3. 중복 확인
            existing_strategy = self.strategy_repository.find_by_name(strategy.name)
            if existing_strategy:
                return CreateStrategyResult.failure(f"동일한 이름의 전략이 이미 존재합니다: {strategy.name}")
            
            # 4. 저장
            saved_strategy = self.strategy_repository.save(strategy)
            
            # 5. 이벤트 발행
            event = StrategyCreatedEvent(
                strategy_id=saved_strategy.id.value,
                strategy_type=command.strategy_config['type'],
                created_at=datetime.utcnow()
            )
            self.event_publisher.publish(event)
            
            return CreateStrategyResult.success(saved_strategy.id.value)
            
        except Exception as e:
            logger.error(f"전략 생성 실패: {str(e)}")
            return CreateStrategyResult.failure(f"전략 생성 중 오류 발생: {str(e)}")

# application/use_cases/backtest_strategy_use_case.py
class BacktestStrategyUseCase:
    """전략 백테스팅 유스케이스"""
    
    def __init__(
        self,
        strategy_repository,
        market_data_service,
        backtest_engine,
        performance_calculator
    ):
        self.strategy_repository = strategy_repository
        self.market_data_service = market_data_service
        self.backtest_engine = backtest_engine
        self.performance_calculator = performance_calculator
    
    async def execute(self, command: BacktestStrategyCommand) -> BacktestStrategyResult:
        """전략 백테스팅 실행"""
        
        try:
            # 1. 전략 조회
            strategy = self.strategy_repository.find_by_id(
                StochasticRSIStrategyId(command.strategy_id)
            )
            if not strategy:
                return BacktestStrategyResult.failure("전략을 찾을 수 없습니다")
            
            # 2. 시장 데이터 로드
            market_data = await self.market_data_service.get_historical_data(
                symbol=command.symbol,
                start_date=command.start_date,
                end_date=command.end_date,
                timeframe=command.timeframe
            )
            
            if not market_data:
                return BacktestStrategyResult.failure("시장 데이터를 로드할 수 없습니다")
            
            # 3. 백테스팅 실행
            backtest_result = await self.backtest_engine.run_backtest(
                strategy=strategy,
                market_data=market_data,
                initial_capital=command.initial_capital
            )
            
            # 4. 성능 지표 계산
            performance_metrics = self.performance_calculator.calculate(
                trades=backtest_result.trades,
                portfolio_history=backtest_result.portfolio_history
            )
            
            return BacktestStrategyResult.success(
                strategy_id=command.strategy_id,
                performance_metrics=performance_metrics,
                trades=backtest_result.trades
            )
            
        except Exception as e:
            logger.error(f"전략 백테스팅 실패: {str(e)}")
            return BacktestStrategyResult.failure(f"백테스팅 중 오류 발생: {str(e)}")

# application/services/strategy_validation_service.py
class StrategyValidationService:
    """전략 유효성 검증 서비스"""
    
    def validate(self, strategy_config: Dict) -> 'ValidationResult':
        """전략 설정 유효성 검증"""
        
        errors = []
        
        # 필수 필드 검증
        required_fields = ['type', 'name']
        for field in required_fields:
            if field not in strategy_config:
                errors.append(f"필수 필드 누락: {field}")
        
        if errors:
            return ValidationResult(False, "; ".join(errors))
        
        # 전략 타입별 검증
        strategy_type = strategy_config['type']
        
        if strategy_type == 'StochasticRSI':
            self._validate_stochastic_rsi_config(strategy_config, errors)
        elif strategy_type == 'RSI':
            self._validate_rsi_config(strategy_config, errors)
        # 추가 전략 검증...
        
        return ValidationResult(len(errors) == 0, "; ".join(errors))
    
    def _validate_stochastic_rsi_config(self, config: Dict, errors: List[str]):
        """스토캐스틱 RSI 전략 설정 검증"""
        
        # 파라미터 범위 검증
        validations = [
            ('rsi_period', 2, 100),
            ('stochastic_period', 2, 100),
            ('oversold_threshold', 0, 50),
            ('overbought_threshold', 50, 100),
            ('take_profit_rate', 0.01, 1.0),
            ('stop_loss_rate', 0.01, 0.5),
            ('trailing_stop_activation', 0.01, 0.5),
            ('trailing_stop_distance', 0.01, 0.2)
        ]
        
        for param_name, min_val, max_val in validations:
            if param_name in config:
                value = config[param_name]
                if not (min_val <= value <= max_val):
                    errors.append(f"{param_name}은 {min_val}과 {max_val} 사이여야 합니다")
        
        # 논리적 검증
        if ('oversold_threshold' in config and 'overbought_threshold' in config):
            if config['oversold_threshold'] >= config['overbought_threshold']:
                errors.append("과매도 임계값은 과매수 임계값보다 작아야 합니다")
        
        if ('take_profit_rate' in config and 'trailing_stop_activation' in config):
            if config['trailing_stop_activation'] >= config['take_profit_rate']:
                errors.append("트레일링 스탑 활성화는 익절 비율보다 작아야 합니다")

@dataclass
class ValidationResult:
    """검증 결과"""
    is_valid: bool
    error_message: str = ""
```

### 2. 명령 및 결과 객체
```python
# application/commands/strategy_commands.py
@dataclass
class CreateStrategyCommand:
    """전략 생성 명령"""
    strategy_config: Dict

@dataclass
class BacktestStrategyCommand:
    """전략 백테스팅 명령"""
    strategy_id: str
    symbol: str
    start_date: datetime
    end_date: datetime
    timeframe: str = "1h"
    initial_capital: Decimal = Decimal('1000000')

# application/results/strategy_results.py
class CreateStrategyResult:
    """전략 생성 결과"""
    
    def __init__(self, success: bool, strategy_id: str = None, error_message: str = None):
        self.success = success
        self.strategy_id = strategy_id
        self.error_message = error_message
    
    @classmethod
    def success(cls, strategy_id: str):
        return cls(success=True, strategy_id=strategy_id)
    
    @classmethod
    def failure(cls, error_message: str):
        return cls(success=False, error_message=error_message)

class BacktestStrategyResult:
    """전략 백테스팅 결과"""
    
    def __init__(
        self, 
        success: bool, 
        strategy_id: str = None, 
        performance_metrics: Dict = None,
        trades: List = None,
        error_message: str = None
    ):
        self.success = success
        self.strategy_id = strategy_id
        self.performance_metrics = performance_metrics
        self.trades = trades
        self.error_message = error_message
    
    @classmethod
    def success(cls, strategy_id: str, performance_metrics: Dict, trades: List):
        return cls(
            success=True,
            strategy_id=strategy_id,
            performance_metrics=performance_metrics,
            trades=trades
        )
    
    @classmethod
    def failure(cls, error_message: str):
        return cls(success=False, error_message=error_message)
```

## 🔌 Infrastructure Layer 구현

### 1. Repository 구현
```python
# infrastructure/repositories/sqlite_stochastic_rsi_strategy_repository.py
class SQLiteStochasticRSIStrategyRepository:
    """SQLite 스토캐스틱 RSI 전략 Repository"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """테이블 존재 확인 및 생성"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS stochastic_rsi_strategies (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            rsi_period INTEGER NOT NULL,
            stochastic_period INTEGER NOT NULL,
            oversold_threshold DECIMAL(5,2) NOT NULL,
            overbought_threshold DECIMAL(5,2) NOT NULL,
            take_profit_rate DECIMAL(5,4) NOT NULL,
            stop_loss_rate DECIMAL(5,4) NOT NULL,
            trailing_stop_activation DECIMAL(5,4) NOT NULL,
            trailing_stop_distance DECIMAL(5,4) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            CHECK (oversold_threshold < overbought_threshold),
            CHECK (take_profit_rate > 0 AND stop_loss_rate > 0),
            CHECK (trailing_stop_activation < take_profit_rate)
        )
        """
        
        self.db.execute(create_table_sql)
    
    def save(self, strategy: StochasticRSIStrategy) -> StochasticRSIStrategy:
        """전략 저장"""
        
        query = """
        INSERT OR REPLACE INTO stochastic_rsi_strategies 
        (id, name, rsi_period, stochastic_period, oversold_threshold, 
         overbought_threshold, take_profit_rate, stop_loss_rate, 
         trailing_stop_activation, trailing_stop_distance, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        with self.db.transaction():
            self.db.execute(query, (
                strategy.id.value,
                strategy.name,
                strategy.rsi_period,
                strategy.stochastic_period,
                float(strategy.oversold_threshold),
                float(strategy.overbought_threshold),
                float(strategy.take_profit_rate),
                float(strategy.stop_loss_rate),
                float(strategy.trailing_stop_activation),
                float(strategy.trailing_stop_distance),
                strategy._is_active,
                strategy._created_at.isoformat()
            ))
        
        return strategy
    
    def find_by_id(self, strategy_id: StochasticRSIStrategyId) -> Optional[StochasticRSIStrategy]:
        """ID로 전략 조회"""
        
        query = """
        SELECT * FROM stochastic_rsi_strategies WHERE id = ?
        """
        
        row = self.db.fetchone(query, (strategy_id.value,))
        if row:
            return self._map_to_domain(row)
        return None
    
    def find_by_name(self, name: str) -> Optional[StochasticRSIStrategy]:
        """이름으로 전략 조회"""
        
        query = """
        SELECT * FROM stochastic_rsi_strategies WHERE name = ?
        """
        
        row = self.db.fetchone(query, (name,))
        if row:
            return self._map_to_domain(row)
        return None
    
    def find_all_active(self) -> List[StochasticRSIStrategy]:
        """모든 활성 전략 조회"""
        
        query = """
        SELECT * FROM stochastic_rsi_strategies 
        WHERE is_active = 1 
        ORDER BY created_at DESC
        """
        
        rows = self.db.fetchall(query)
        return [self._map_to_domain(row) for row in rows]
    
    def _map_to_domain(self, row) -> StochasticRSIStrategy:
        """DB 행을 도메인 객체로 변환"""
        
        strategy = StochasticRSIStrategy(
            id=StochasticRSIStrategyId(row['id']),
            name=row['name'],
            rsi_period=row['rsi_period'],
            stochastic_period=row['stochastic_period'],
            oversold_threshold=Decimal(str(row['oversold_threshold'])),
            overbought_threshold=Decimal(str(row['overbought_threshold'])),
            take_profit_rate=Decimal(str(row['take_profit_rate'])),
            stop_loss_rate=Decimal(str(row['stop_loss_rate'])),
            trailing_stop_activation=Decimal(str(row['trailing_stop_activation'])),
            trailing_stop_distance=Decimal(str(row['trailing_stop_distance']))
        )
        
        # 저장된 상태 복원
        strategy._is_active = bool(row['is_active'])
        strategy._created_at = datetime.fromisoformat(row['created_at'])
        
        return strategy
```

## 🎨 Presentation Layer 구현

### 1. 전략 설정 UI
```python
# presentation/views/strategy_creation_view.py
class StrategyCreationView(QWidget):
    """전략 생성 View"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_events()
    
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout()
        
        # 전략 타입 선택
        self.strategy_type_combo = QComboBox()
        self.strategy_type_combo.addItems(['스토캐스틱 RSI', 'RSI', '이동평균'])
        layout.addWidget(QLabel("전략 타입:"))
        layout.addWidget(self.strategy_type_combo)
        
        # 전략 이름
        self.strategy_name_edit = QLineEdit()
        layout.addWidget(QLabel("전략 이름:"))
        layout.addWidget(self.strategy_name_edit)
        
        # 파라미터 설정 영역
        self.parameter_scroll = QScrollArea()
        self.parameter_widget = QWidget()
        self.parameter_layout = QFormLayout()
        self.parameter_widget.setLayout(self.parameter_layout)
        self.parameter_scroll.setWidget(self.parameter_widget)
        layout.addWidget(self.parameter_scroll)
        
        # 버튼들
        button_layout = QHBoxLayout()
        self.create_button = QPushButton("전략 생성")
        self.backtest_button = QPushButton("백테스트")
        self.reset_button = QPushButton("초기화")
        
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.backtest_button)
        button_layout.addWidget(self.reset_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 초기 파라미터 로드
        self.load_strategy_parameters()
    
    def setup_events(self):
        """이벤트 연결"""
        self.strategy_type_combo.currentTextChanged.connect(self.load_strategy_parameters)
        self.create_button.clicked.connect(self.create_strategy)
        self.backtest_button.clicked.connect(self.run_backtest)
        self.reset_button.clicked.connect(self.reset_parameters)
    
    def load_strategy_parameters(self):
        """전략별 파라미터 UI 로드"""
        # 기존 파라미터 위젯 제거
        for i in reversed(range(self.parameter_layout.count())):
            self.parameter_layout.itemAt(i).widget().setParent(None)
        
        strategy_type = self.strategy_type_combo.currentText()
        
        if strategy_type == "스토캐스틱 RSI":
            self._create_stochastic_rsi_parameters()
        elif strategy_type == "RSI":
            self._create_rsi_parameters()
        # 추가 전략 파라미터...
    
    def _create_stochastic_rsi_parameters(self):
        """스토캐스틱 RSI 파라미터 UI 생성"""
        
        # RSI 기간
        self.rsi_period_spin = QSpinBox()
        self.rsi_period_spin.setRange(2, 100)
        self.rsi_period_spin.setValue(14)
        self.parameter_layout.addRow("RSI 기간:", self.rsi_period_spin)
        
        # 스토캐스틱 기간
        self.stoch_period_spin = QSpinBox()
        self.stoch_period_spin.setRange(2, 100)
        self.stoch_period_spin.setValue(14)
        self.parameter_layout.addRow("스토캐스틱 기간:", self.stoch_period_spin)
        
        # 과매도 임계값
        self.oversold_spin = QDoubleSpinBox()
        self.oversold_spin.setRange(0, 50)
        self.oversold_spin.setValue(20)
        self.parameter_layout.addRow("과매도 임계값:", self.oversold_spin)
        
        # 과매수 임계값
        self.overbought_spin = QDoubleSpinBox()
        self.overbought_spin.setRange(50, 100)
        self.overbought_spin.setValue(80)
        self.parameter_layout.addRow("과매수 임계값:", self.overbought_spin)
        
        # 익절 비율
        self.take_profit_spin = QDoubleSpinBox()
        self.take_profit_spin.setRange(0.01, 1.0)
        self.take_profit_spin.setValue(0.15)
        self.take_profit_spin.setSuffix(" %")
        self.parameter_layout.addRow("익절 비율:", self.take_profit_spin)
        
        # 손절 비율
        self.stop_loss_spin = QDoubleSpinBox()
        self.stop_loss_spin.setRange(0.01, 0.5)
        self.stop_loss_spin.setValue(0.05)
        self.stop_loss_spin.setSuffix(" %")
        self.parameter_layout.addRow("손절 비율:", self.stop_loss_spin)
        
        # 트레일링 스탑 활성화
        self.trailing_activation_spin = QDoubleSpinBox()
        self.trailing_activation_spin.setRange(0.01, 0.5)
        self.trailing_activation_spin.setValue(0.08)
        self.trailing_activation_spin.setSuffix(" %")
        self.parameter_layout.addRow("트레일링 스탑 활성화:", self.trailing_activation_spin)
        
        # 트레일링 스탑 거리
        self.trailing_distance_spin = QDoubleSpinBox()
        self.trailing_distance_spin.setRange(0.01, 0.2)
        self.trailing_distance_spin.setValue(0.03)
        self.trailing_distance_spin.setSuffix(" %")
        self.parameter_layout.addRow("트레일링 스탑 거리:", self.trailing_distance_spin)
    
    def create_strategy(self):
        """전략 생성"""
        strategy_config = self.get_strategy_config()
        
        if not strategy_config:
            QMessageBox.warning(self, "오류", "전략 설정을 확인해주세요")
            return
        
        # Presenter에게 전달
        self.presenter.create_strategy(strategy_config)
    
    def get_strategy_config(self) -> Optional[Dict]:
        """현재 UI에서 전략 설정 추출"""
        strategy_type = self.strategy_type_combo.currentText()
        strategy_name = self.strategy_name_edit.text().strip()
        
        if not strategy_name:
            QMessageBox.warning(self, "오류", "전략 이름을 입력해주세요")
            return None
        
        if strategy_type == "스토캐스틱 RSI":
            return {
                'type': 'StochasticRSI',
                'name': strategy_name,
                'rsi_period': self.rsi_period_spin.value(),
                'stochastic_period': self.stoch_period_spin.value(),
                'oversold_threshold': self.oversold_spin.value(),
                'overbought_threshold': self.overbought_spin.value(),
                'take_profit_rate': self.take_profit_spin.value() / 100,
                'stop_loss_rate': self.stop_loss_spin.value() / 100,
                'trailing_stop_activation': self.trailing_activation_spin.value() / 100,
                'trailing_stop_distance': self.trailing_distance_spin.value() / 100
            }
        
        return None
    
    def show_strategy_created(self, strategy_id: str):
        """전략 생성 완료 표시"""
        QMessageBox.information(self, "성공", f"전략이 생성되었습니다\nID: {strategy_id}")
        self.reset_parameters()
    
    def show_error(self, error_message: str):
        """오류 메시지 표시"""
        QMessageBox.critical(self, "오류", error_message)
```

## 🧪 테스팅

### 1. 단위 테스트
```python
# tests/domain/entities/test_stochastic_rsi_strategy.py
class TestStochasticRSIStrategy:
    """스토캐스틱 RSI 전략 단위 테스트"""
    
    def test_strategy_creation_with_valid_parameters(self):
        """유효한 파라미터로 전략 생성 테스트"""
        strategy_id = StochasticRSIStrategyId("test_strategy_1")
        
        strategy = StochasticRSIStrategy(
            id=strategy_id,
            name="Test Stochastic RSI",
            rsi_period=14,
            stochastic_period=14,
            oversold_threshold=Decimal('20'),
            overbought_threshold=Decimal('80')
        )
        
        assert strategy.id == strategy_id
        assert strategy.name == "Test Stochastic RSI"
        assert strategy.rsi_period == 14
        assert strategy._is_active is True
    
    def test_strategy_creation_with_invalid_parameters(self):
        """잘못된 파라미터로 전략 생성 테스트"""
        strategy_id = StochasticRSIStrategyId("test_strategy_2")
        
        with pytest.raises(ValueError, match="RSI 기간은 2-100 사이여야 합니다"):
            StochasticRSIStrategy(
                id=strategy_id,
                name="Test Strategy",
                rsi_period=1  # 잘못된 값
            )
    
    def test_entry_signal_generation(self):
        """진입 신호 생성 테스트"""
        strategy = self._create_test_strategy()
        
        # 테스트 데이터 생성
        historical_data = self._create_test_market_data()
        current_data = historical_data[-1]
        
        # 과매도에서 상승 전환 시나리오
        signal = strategy.generate_signal(current_data, historical_data)
        
        if signal:
            assert signal.action == 'BUY'
            assert signal.confidence > 0
            assert "상승 전환" in signal.reason
    
    def test_exit_signal_generation(self):
        """청산 신호 생성 테스트"""
        strategy = self._create_test_strategy()
        
        # 테스트 포지션 생성
        position = self._create_test_position()
        historical_data = self._create_test_market_data()
        
        # 손절 시나리오 - 가격 하락
        current_data = MarketDataPoint(
            timestamp=datetime.utcnow(),
            close_price=position.entry_price * Decimal('0.94')  # 6% 하락
        )
        
        signal = strategy.generate_signal(current_data, historical_data, position)
        
        assert signal is not None
        assert signal.action == 'SELL'
        assert "손절" in signal.reason
    
    def _create_test_strategy(self) -> StochasticRSIStrategy:
        """테스트용 전략 생성"""
        return StochasticRSIStrategy(
            id=StochasticRSIStrategyId("test_strategy"),
            name="Test Strategy",
            rsi_period=14,
            stochastic_period=14,
            oversold_threshold=Decimal('20'),
            overbought_threshold=Decimal('80'),
            stop_loss_rate=Decimal('0.05')
        )
    
    def _create_test_market_data(self) -> List[MarketDataPoint]:
        """테스트용 시장 데이터 생성"""
        base_price = Decimal('50000')
        data = []
        
        for i in range(50):  # 충분한 데이터 포인트
            price = base_price + (i * Decimal('100'))
            data.append(MarketDataPoint(
                timestamp=datetime.utcnow() - timedelta(hours=50-i),
                close_price=price
            ))
        
        return data
    
    def _create_test_position(self):
        """테스트용 포지션 생성"""
        return Position(
            entry_price=Decimal('50000'),
            quantity=Decimal('0.1'),
            entry_time=datetime.utcnow() - timedelta(hours=1)
        )
```

## 🔍 다음 단계

- **[테스팅 전략](16_TESTING_STRATEGY.md)**: 전략별 테스트 방법론
- **[모니터링 전략](17_MONITORING_STRATEGY.md)**: 전략 성능 모니터링
- **[디버깅 가이드](15_DEBUGGING_GUIDE.md)**: 전략 디버깅 방법

---
**💡 핵심**: "Clean Architecture를 통해 새로운 전략을 체계적으로 추가하고, 각 계층에서 적절한 책임을 분리하여 확장 가능한 구조를 만듭니다!"
