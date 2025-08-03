# 📊 백테스팅 시스템 확장 가이드

> **목적**: Clean Architecture에서 백테스팅 시스템 구현 및 확장  
> **대상**: 개발자, 퀀트 분석가  
> **예상 읽기 시간**: 17분

## 🎯 백테스팅 시스템 요구사항

### 📋 기능 요구사항
- **전략 검증**: 다양한 매매 전략의 역사적 성능 분석
- **포트폴리오 시뮬레이션**: 다중 자산 포트폴리오 백테스팅
- **성능 지표**: 수익률, MDD, 샤프비율, 승률 등 종합 분석
- **리스크 관리**: 다양한 리스크 관리 전략 시뮬레이션

### 🔧 기술적 요구사항
- **대용량 처리**: 1년치 분봉 데이터 5분 내 처리
- **정확성**: 실제 거래와 99.9% 일치하는 시뮬레이션
- **확장성**: 새로운 전략과 지표 쉽게 추가 가능
- **재현성**: 동일 조건에서 동일 결과 보장

## 💎 Domain Layer 구현

### 1. 백테스팅 도메인 모델
```python
# domain/entities/backtest.py
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum

class BacktestStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

@dataclass(frozen=True)
class BacktestId:
    """백테스트 ID"""
    value: str

class Backtest:
    """백테스트 도메인 엔티티"""
    
    def __init__(
        self,
        id: BacktestId,
        strategy_config: 'StrategyConfiguration',
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: Decimal
    ):
        self.id = id
        self.strategy_config = strategy_config
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        
        # 상태 관리
        self._status = BacktestStatus.PENDING
        self._started_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None
        self._error_message: Optional[str] = None
        
        # 결과 데이터
        self._trades: List['BacktestTrade'] = []
        self._portfolio_snapshots: List['PortfolioSnapshot'] = []
        self._performance_metrics: Optional['PerformanceMetrics'] = None
    
    @property
    def status(self) -> BacktestStatus:
        return self._status
    
    @property
    def trades(self) -> List['BacktestTrade']:
        return self._trades.copy()
    
    @property
    def performance_metrics(self) -> Optional['PerformanceMetrics']:
        return self._performance_metrics
    
    def start_execution(self):
        """백테스트 실행 시작"""
        if self._status != BacktestStatus.PENDING:
            raise ValueError(f"백테스트 상태가 {self._status}이므로 시작할 수 없습니다")
        
        self._status = BacktestStatus.RUNNING
        self._started_at = datetime.utcnow()
    
    def complete_execution(self, performance_metrics: 'PerformanceMetrics'):
        """백테스트 실행 완료"""
        if self._status != BacktestStatus.RUNNING:
            raise ValueError(f"실행 중이 아닌 백테스트는 완료할 수 없습니다")
        
        self._status = BacktestStatus.COMPLETED
        self._completed_at = datetime.utcnow()
        self._performance_metrics = performance_metrics
    
    def fail_execution(self, error_message: str):
        """백테스트 실행 실패"""
        self._status = BacktestStatus.FAILED
        self._error_message = error_message
        self._completed_at = datetime.utcnow()
    
    def add_trade(self, trade: 'BacktestTrade'):
        """거래 추가"""
        if self._status != BacktestStatus.RUNNING:
            raise ValueError("실행 중인 백테스트에만 거래를 추가할 수 있습니다")
        
        self._trades.append(trade)
    
    def add_portfolio_snapshot(self, snapshot: 'PortfolioSnapshot'):
        """포트폴리오 스냅샷 추가"""
        if self._status != BacktestStatus.RUNNING:
            raise ValueError("실행 중인 백테스트에만 스냅샷을 추가할 수 있습니다")
        
        self._portfolio_snapshots.append(snapshot)
    
    def get_duration(self) -> Optional[timedelta]:
        """실행 시간 계산"""
        if not self._started_at:
            return None
        
        end_time = self._completed_at or datetime.utcnow()
        return end_time - self._started_at

@dataclass
class BacktestTrade:
    """백테스트 거래 기록"""
    timestamp: datetime
    action: str  # 'BUY', 'SELL'
    price: Decimal
    quantity: Decimal
    commission: Decimal
    position_id: str
    strategy_signal: str
    
    @property
    def total_amount(self) -> Decimal:
        """총 거래 금액"""
        return self.price * self.quantity + self.commission

@dataclass  
class PortfolioSnapshot:
    """포트폴리오 스냅샷"""
    timestamp: datetime
    cash_balance: Decimal
    position_value: Decimal
    total_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal

class PerformanceMetrics:
    """성능 지표"""
    
    def __init__(
        self,
        total_return: Decimal,
        annual_return: Decimal,
        max_drawdown: Decimal,
        sharpe_ratio: Decimal,
        win_rate: Decimal,
        profit_factor: Decimal,
        total_trades: int,
        winning_trades: int,
        losing_trades: int,
        avg_trade_return: Decimal,
        avg_holding_time: timedelta
    ):
        self.total_return = total_return
        self.annual_return = annual_return
        self.max_drawdown = max_drawdown
        self.sharpe_ratio = sharpe_ratio
        self.win_rate = win_rate
        self.profit_factor = profit_factor
        self.total_trades = total_trades
        self.winning_trades = winning_trades
        self.losing_trades = losing_trades
        self.avg_trade_return = avg_trade_return
        self.avg_holding_time = avg_holding_time
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'total_return': float(self.total_return),
            'annual_return': float(self.annual_return),
            'max_drawdown': float(self.max_drawdown),
            'sharpe_ratio': float(self.sharpe_ratio),
            'win_rate': float(self.win_rate),
            'profit_factor': float(self.profit_factor),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'avg_trade_return': float(self.avg_trade_return),
            'avg_holding_time_hours': self.avg_holding_time.total_seconds() / 3600
        }

# domain/entities/strategy_configuration.py
class StrategyConfiguration:
    """전략 설정"""
    
    def __init__(
        self,
        entry_strategy: 'EntryStrategyConfig',
        management_strategies: List['ManagementStrategyConfig'],
        risk_management: 'RiskManagementConfig'
    ):
        self.entry_strategy = entry_strategy
        self.management_strategies = management_strategies
        self.risk_management = risk_management
    
    def validate(self) -> bool:
        """전략 설정 유효성 검증"""
        if not self.entry_strategy:
            return False
        
        # 진입 전략 검증
        if not self.entry_strategy.validate():
            return False
        
        # 관리 전략 검증
        for mgmt_strategy in self.management_strategies:
            if not mgmt_strategy.validate():
                return False
        
        return True

@dataclass
class EntryStrategyConfig:
    """진입 전략 설정"""
    strategy_type: str  # 'RSI', 'MA_CROSSOVER', 'BOLLINGER_BANDS'
    parameters: Dict
    
    def validate(self) -> bool:
        """유효성 검증"""
        if not self.strategy_type or not self.parameters:
            return False
        
        # 전략별 파라미터 검증
        if self.strategy_type == 'RSI':
            required_params = ['period', 'oversold', 'overbought']
        elif self.strategy_type == 'MA_CROSSOVER':
            required_params = ['short_period', 'long_period']
        elif self.strategy_type == 'BOLLINGER_BANDS':
            required_params = ['period', 'std_dev']
        else:
            return False
        
        return all(param in self.parameters for param in required_params)

@dataclass
class ManagementStrategyConfig:
    """관리 전략 설정"""
    strategy_type: str  # 'TRAILING_STOP', 'FIXED_STOP', 'SCALE_IN'
    parameters: Dict
    priority: int = 1
    
    def validate(self) -> bool:
        """유효성 검증"""
        return bool(self.strategy_type and self.parameters)

@dataclass
class RiskManagementConfig:
    """리스크 관리 설정"""
    max_position_size: Decimal
    max_drawdown: Decimal
    stop_loss_rate: Decimal
    take_profit_rate: Decimal
```

### 2. 백테스팅 도메인 서비스
```python
# domain/services/backtest_service.py
class BacktestService:
    """백테스팅 도메인 서비스"""
    
    def __init__(self, performance_calculator):
        self.performance_calculator = performance_calculator
    
    def create_backtest(
        self,
        strategy_config: StrategyConfiguration,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: Decimal = Decimal('1000000')
    ) -> Backtest:
        """백테스트 생성"""
        
        # 입력 검증
        if not strategy_config.validate():
            raise ValueError("전략 설정이 유효하지 않습니다")
        
        if start_date >= end_date:
            raise ValueError("시작 날짜는 종료 날짜보다 이전이어야 합니다")
        
        if initial_capital <= 0:
            raise ValueError("초기 자본은 0보다 커야 합니다")
        
        # ID 생성
        backtest_id = BacktestId(f"bt_{symbol}_{int(datetime.utcnow().timestamp())}")
        
        return Backtest(
            id=backtest_id,
            strategy_config=strategy_config,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital
        )
    
    def calculate_performance_metrics(
        self,
        trades: List[BacktestTrade],
        portfolio_snapshots: List[PortfolioSnapshot],
        initial_capital: Decimal,
        period_days: int
    ) -> PerformanceMetrics:
        """성능 지표 계산"""
        
        if not trades or not portfolio_snapshots:
            return self._create_empty_metrics()
        
        # 기본 통계
        total_trades = len(trades)
        winning_trades = len([t for t in trades if self._is_winning_trade(t)])
        losing_trades = total_trades - winning_trades
        
        # 수익률 계산
        final_value = portfolio_snapshots[-1].total_value
        total_return = (final_value - initial_capital) / initial_capital
        annual_return = self._annualize_return(total_return, period_days)
        
        # 최대 낙폭 계산
        max_drawdown = self._calculate_max_drawdown(portfolio_snapshots)
        
        # 샤프 비율 계산
        sharpe_ratio = self._calculate_sharpe_ratio(portfolio_snapshots, annual_return)
        
        # 승률 계산
        win_rate = Decimal(winning_trades) / Decimal(total_trades) if total_trades > 0 else Decimal('0')
        
        # 수익 팩터 계산
        profit_factor = self._calculate_profit_factor(trades)
        
        # 평균 거래 수익률
        avg_trade_return = total_return / Decimal(total_trades) if total_trades > 0 else Decimal('0')
        
        # 평균 보유 시간
        avg_holding_time = self._calculate_avg_holding_time(trades)
        
        return PerformanceMetrics(
            total_return=total_return,
            annual_return=annual_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            avg_trade_return=avg_trade_return,
            avg_holding_time=avg_holding_time
        )
    
    def _calculate_max_drawdown(self, snapshots: List[PortfolioSnapshot]) -> Decimal:
        """최대 낙폭 계산"""
        if not snapshots:
            return Decimal('0')
        
        peak = snapshots[0].total_value
        max_dd = Decimal('0')
        
        for snapshot in snapshots:
            if snapshot.total_value > peak:
                peak = snapshot.total_value
            
            drawdown = (peak - snapshot.total_value) / peak
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd
    
    def _calculate_sharpe_ratio(
        self, 
        snapshots: List[PortfolioSnapshot], 
        annual_return: Decimal
    ) -> Decimal:
        """샤프 비율 계산"""
        if len(snapshots) < 2:
            return Decimal('0')
        
        # 일별 수익률 계산
        daily_returns = []
        for i in range(1, len(snapshots)):
            prev_value = snapshots[i-1].total_value
            curr_value = snapshots[i].total_value
            daily_return = (curr_value - prev_value) / prev_value
            daily_returns.append(daily_return)
        
        if not daily_returns:
            return Decimal('0')
        
        # 표준편차 계산
        mean_return = sum(daily_returns) / len(daily_returns)
        variance = sum((r - mean_return) ** 2 for r in daily_returns) / len(daily_returns)
        std_dev = variance ** Decimal('0.5')
        
        if std_dev == 0:
            return Decimal('0')
        
        # 무위험 수익률을 0으로 가정
        return annual_return / (std_dev * Decimal('252') ** Decimal('0.5'))  # 연간화
    
    def _calculate_profit_factor(self, trades: List[BacktestTrade]) -> Decimal:
        """수익 팩터 계산 (총 이익 / 총 손실)"""
        total_profit = Decimal('0')
        total_loss = Decimal('0')
        
        # 거래별 손익 계산 (간단화된 버전)
        for i in range(0, len(trades), 2):  # 매수-매도 쌍으로 처리
            if i + 1 < len(trades):
                buy_trade = trades[i]
                sell_trade = trades[i + 1]
                
                if buy_trade.action == 'BUY' and sell_trade.action == 'SELL':
                    pnl = (sell_trade.price - buy_trade.price) * buy_trade.quantity
                    if pnl > 0:
                        total_profit += pnl
                    else:
                        total_loss += abs(pnl)
        
        return total_profit / total_loss if total_loss > 0 else Decimal('0')
    
    def _calculate_avg_holding_time(self, trades: List[BacktestTrade]) -> timedelta:
        """평균 보유 시간 계산"""
        holding_times = []
        
        # 매수-매도 쌍으로 보유 시간 계산
        for i in range(0, len(trades), 2):
            if i + 1 < len(trades):
                buy_trade = trades[i]
                sell_trade = trades[i + 1]
                
                if buy_trade.action == 'BUY' and sell_trade.action == 'SELL':
                    holding_time = sell_trade.timestamp - buy_trade.timestamp
                    holding_times.append(holding_time)
        
        if not holding_times:
            return timedelta(0)
        
        avg_seconds = sum(ht.total_seconds() for ht in holding_times) / len(holding_times)
        return timedelta(seconds=avg_seconds)
    
    def _annualize_return(self, total_return: Decimal, period_days: int) -> Decimal:
        """연환산 수익률 계산"""
        if period_days <= 0:
            return Decimal('0')
        
        return total_return * (Decimal('365') / Decimal(period_days))
    
    def _is_winning_trade(self, trade: BacktestTrade) -> bool:
        """승리 거래 판단 (간단화된 버전)"""
        # 실제로는 매수-매도 쌍을 비교해야 함
        return 'profit' in trade.strategy_signal.lower()
    
    def _create_empty_metrics(self) -> PerformanceMetrics:
        """빈 성능 지표 생성"""
        return PerformanceMetrics(
            total_return=Decimal('0'),
            annual_return=Decimal('0'),
            max_drawdown=Decimal('0'),
            sharpe_ratio=Decimal('0'),
            win_rate=Decimal('0'),
            profit_factor=Decimal('0'),
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            avg_trade_return=Decimal('0'),
            avg_holding_time=timedelta(0)
        )
```

## ⚙️ Application Layer 구현

### 1. 백테스팅 유스케이스
```python
# application/use_cases/run_backtest_use_case.py
class RunBacktestUseCase:
    """백테스트 실행 유스케이스"""
    
    def __init__(
        self,
        backtest_repository,
        market_data_service,
        strategy_factory,
        backtest_engine,
        event_publisher
    ):
        self.backtest_repository = backtest_repository
        self.market_data_service = market_data_service
        self.strategy_factory = strategy_factory
        self.backtest_engine = backtest_engine
        self.event_publisher = event_publisher
    
    async def execute(self, command: RunBacktestCommand) -> RunBacktestResult:
        """백테스트 실행"""
        
        try:
            # 1. 백테스트 조회
            backtest = self.backtest_repository.find_by_id(BacktestId(command.backtest_id))
            if not backtest:
                return RunBacktestResult.failure("백테스트를 찾을 수 없습니다")
            
            # 2. 실행 시작
            backtest.start_execution()
            self.backtest_repository.save(backtest)
            
            # 3. 시장 데이터 로드
            market_data = await self.market_data_service.get_historical_data(
                symbol=backtest.symbol,
                start_date=backtest.start_date,
                end_date=backtest.end_date,
                timeframe="1h"
            )
            
            if not market_data:
                backtest.fail_execution("시장 데이터를 로드할 수 없습니다")
                self.backtest_repository.save(backtest)
                return RunBacktestResult.failure("시장 데이터 로드 실패")
            
            # 4. 전략 인스턴스 생성
            strategy = self.strategy_factory.create_strategy(backtest.strategy_config)
            
            # 5. 백테스트 엔진 실행
            execution_result = await self.backtest_engine.execute(
                backtest=backtest,
                market_data=market_data,
                strategy=strategy
            )
            
            # 6. 성능 지표 계산
            performance_metrics = self._calculate_performance_metrics(
                backtest, execution_result
            )
            
            # 7. 백테스트 완료
            backtest.complete_execution(performance_metrics)
            saved_backtest = self.backtest_repository.save(backtest)
            
            # 8. 이벤트 발행
            await self._publish_completion_event(saved_backtest)
            
            return RunBacktestResult.success(saved_backtest.id.value, performance_metrics)
            
        except Exception as e:
            logger.error(f"백테스트 실행 실패: {str(e)}")
            
            if 'backtest' in locals():
                backtest.fail_execution(str(e))
                self.backtest_repository.save(backtest)
            
            return RunBacktestResult.failure(f"실행 실패: {str(e)}")
    
    def _calculate_performance_metrics(
        self, 
        backtest: Backtest, 
        execution_result: 'BacktestExecutionResult'
    ) -> PerformanceMetrics:
        """성능 지표 계산"""
        
        backtest_service = BacktestService(self.performance_calculator)
        
        period_days = (backtest.end_date - backtest.start_date).days
        
        return backtest_service.calculate_performance_metrics(
            trades=execution_result.trades,
            portfolio_snapshots=execution_result.portfolio_snapshots,
            initial_capital=backtest.initial_capital,
            period_days=period_days
        )
    
    async def _publish_completion_event(self, backtest: Backtest):
        """완료 이벤트 발행"""
        event = BacktestCompletedEvent(
            backtest_id=backtest.id.value,
            symbol=backtest.symbol,
            performance_metrics=backtest.performance_metrics,
            completed_at=datetime.utcnow()
        )
        await self.event_publisher.publish_async(event)

# application/services/backtest_engine.py
class BacktestEngine:
    """백테스팅 엔진"""
    
    def __init__(self, portfolio_simulator, commission_calculator):
        self.portfolio_simulator = portfolio_simulator
        self.commission_calculator = commission_calculator
    
    async def execute(
        self,
        backtest: Backtest,
        market_data: List[Dict],
        strategy: 'BacktestStrategy'
    ) -> 'BacktestExecutionResult':
        """백테스트 실행"""
        
        # 포트폴리오 초기화
        portfolio = self.portfolio_simulator.initialize_portfolio(
            initial_capital=backtest.initial_capital,
            symbol=backtest.symbol
        )
        
        trades = []
        portfolio_snapshots = []
        
        # 시간순으로 데이터 처리
        for i, data_point in enumerate(market_data):
            timestamp = data_point['timestamp']
            
            # 1. 전략 신호 생성
            signal = strategy.generate_signal(
                current_data=data_point,
                historical_data=market_data[:i+1],
                portfolio=portfolio
            )
            
            # 2. 신호 실행
            if signal and signal.action != 'HOLD':
                trade = await self._execute_signal(
                    signal=signal,
                    data_point=data_point,
                    portfolio=portfolio,
                    backtest=backtest
                )
                
                if trade:
                    trades.append(trade)
                    backtest.add_trade(trade)
            
            # 3. 포트폴리오 업데이트
            portfolio.update_market_value(data_point['close'])
            
            # 4. 주기적 스냅샷 저장 (1일 간격)
            if i % 24 == 0:  # 시간봉 기준 1일
                snapshot = PortfolioSnapshot(
                    timestamp=timestamp,
                    cash_balance=portfolio.cash_balance,
                    position_value=portfolio.position_value,
                    total_value=portfolio.total_value,
                    unrealized_pnl=portfolio.unrealized_pnl,
                    realized_pnl=portfolio.realized_pnl
                )
                portfolio_snapshots.append(snapshot)
                backtest.add_portfolio_snapshot(snapshot)
        
        return BacktestExecutionResult(
            trades=trades,
            portfolio_snapshots=portfolio_snapshots,
            final_portfolio=portfolio
        )
    
    async def _execute_signal(
        self,
        signal: 'TradingSignal',
        data_point: Dict,
        portfolio: 'Portfolio',
        backtest: Backtest
    ) -> Optional[BacktestTrade]:
        """거래 신호 실행"""
        
        price = Decimal(str(data_point['close']))
        timestamp = data_point['timestamp']
        
        # 수수료 계산
        commission = self.commission_calculator.calculate(
            price=price,
            quantity=signal.quantity
        )
        
        # 거래 실행
        if signal.action == 'BUY':
            if portfolio.can_buy(price, signal.quantity, commission):
                portfolio.buy(price, signal.quantity, commission)
                
                return BacktestTrade(
                    timestamp=timestamp,
                    action='BUY',
                    price=price,
                    quantity=signal.quantity,
                    commission=commission,
                    position_id=signal.position_id or "default",
                    strategy_signal=signal.reason
                )
        
        elif signal.action == 'SELL':
            if portfolio.can_sell(signal.quantity):
                portfolio.sell(price, signal.quantity, commission)
                
                return BacktestTrade(
                    timestamp=timestamp,
                    action='SELL',
                    price=price,
                    quantity=signal.quantity,
                    commission=commission,
                    position_id=signal.position_id or "default",
                    strategy_signal=signal.reason
                )
        
        return None

@dataclass
class BacktestExecutionResult:
    """백테스트 실행 결과"""
    trades: List[BacktestTrade]
    portfolio_snapshots: List[PortfolioSnapshot]
    final_portfolio: 'Portfolio'

# application/commands/backtest_commands.py
@dataclass
class RunBacktestCommand:
    """백테스트 실행 명령"""
    backtest_id: str

@dataclass
class CreateBacktestCommand:
    """백테스트 생성 명령"""
    strategy_config: Dict
    symbol: str
    start_date: str  # ISO format
    end_date: str    # ISO format
    initial_capital: str  # Decimal string
```

### 2. 백테스팅 결과 처리
```python
# application/services/backtest_analysis_service.py
class BacktestAnalysisService:
    """백테스트 분석 서비스"""
    
    def __init__(self, backtest_repository):
        self.backtest_repository = backtest_repository
    
    def compare_backtests(self, backtest_ids: List[str]) -> 'BacktestComparison':
        """백테스트 비교 분석"""
        
        backtests = []
        for backtest_id in backtest_ids:
            backtest = self.backtest_repository.find_by_id(BacktestId(backtest_id))
            if backtest and backtest.status == BacktestStatus.COMPLETED:
                backtests.append(backtest)
        
        if len(backtests) < 2:
            raise ValueError("비교를 위해서는 최소 2개의 완료된 백테스트가 필요합니다")
        
        # 성능 지표 비교
        comparison_metrics = {}
        
        for backtest in backtests:
            metrics = backtest.performance_metrics
            comparison_metrics[backtest.id.value] = {
                'symbol': backtest.symbol,
                'total_return': metrics.total_return,
                'annual_return': metrics.annual_return,
                'max_drawdown': metrics.max_drawdown,
                'sharpe_ratio': metrics.sharpe_ratio,
                'win_rate': metrics.win_rate,
                'total_trades': metrics.total_trades
            }
        
        # 순위 계산
        rankings = self._calculate_rankings(comparison_metrics)
        
        return BacktestComparison(
            backtest_ids=backtest_ids,
            metrics=comparison_metrics,
            rankings=rankings,
            recommendation=self._generate_recommendation(comparison_metrics, rankings)
        )
    
    def _calculate_rankings(self, metrics: Dict) -> Dict:
        """성능 지표별 순위 계산"""
        rankings = {}
        
        # 수익률 순위 (높을수록 좋음)
        sorted_by_return = sorted(
            metrics.items(), 
            key=lambda x: x[1]['total_return'], 
            reverse=True
        )
        rankings['total_return'] = {bt_id: rank+1 for rank, (bt_id, _) in enumerate(sorted_by_return)}
        
        # 샤프 비율 순위 (높을수록 좋음)
        sorted_by_sharpe = sorted(
            metrics.items(),
            key=lambda x: x[1]['sharpe_ratio'],
            reverse=True
        )
        rankings['sharpe_ratio'] = {bt_id: rank+1 for rank, (bt_id, _) in enumerate(sorted_by_sharpe)}
        
        # 최대 낙폭 순위 (낮을수록 좋음)
        sorted_by_mdd = sorted(
            metrics.items(),
            key=lambda x: x[1]['max_drawdown']
        )
        rankings['max_drawdown'] = {bt_id: rank+1 for rank, (bt_id, _) in enumerate(sorted_by_mdd)}
        
        return rankings
    
    def _generate_recommendation(self, metrics: Dict, rankings: Dict) -> str:
        """추천 결과 생성"""
        # 종합 점수 계산 (간단한 가중 평균)
        composite_scores = {}
        
        for bt_id in metrics.keys():
            score = (
                rankings['total_return'][bt_id] * 0.4 +  # 수익률 40%
                rankings['sharpe_ratio'][bt_id] * 0.35 +  # 샤프 비율 35%
                rankings['max_drawdown'][bt_id] * 0.25    # 최대 낙폭 25%
            )
            composite_scores[bt_id] = score
        
        # 최고 점수 백테스트 찾기
        best_backtest = min(composite_scores.items(), key=lambda x: x[1])
        
        return f"전체적으로 가장 우수한 전략: {best_backtest[0]}"

@dataclass
class BacktestComparison:
    """백테스트 비교 결과"""
    backtest_ids: List[str]
    metrics: Dict
    rankings: Dict
    recommendation: str
```

## 🔌 Infrastructure Layer 구현

### 1. Repository 구현
```python
# infrastructure/repositories/sqlite_backtest_repository.py
class SQLiteBacktestRepository:
    """SQLite 백테스트 Repository"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def save(self, backtest: Backtest) -> Backtest:
        """백테스트 저장"""
        
        # 메인 백테스트 정보 저장
        query = """
        INSERT OR REPLACE INTO backtests 
        (id, symbol, start_date, end_date, initial_capital, status, 
         strategy_config, started_at, completed_at, error_message,
         performance_metrics, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        with self.db.transaction():
            self.db.execute(query, (
                backtest.id.value,
                backtest.symbol,
                backtest.start_date.isoformat(),
                backtest.end_date.isoformat(),
                float(backtest.initial_capital),
                backtest.status.value,
                json.dumps(self._strategy_config_to_dict(backtest.strategy_config)),
                backtest._started_at.isoformat() if backtest._started_at else None,
                backtest._completed_at.isoformat() if backtest._completed_at else None,
                backtest._error_message,
                json.dumps(backtest.performance_metrics.to_dict()) if backtest.performance_metrics else None,
                datetime.utcnow().isoformat()
            ))
            
            # 거래 기록 저장
            self._save_trades(backtest.id.value, backtest.trades)
            
            # 포트폴리오 스냅샷 저장
            self._save_portfolio_snapshots(backtest.id.value, backtest._portfolio_snapshots)
        
        return backtest
    
    def find_by_id(self, backtest_id: BacktestId) -> Optional[Backtest]:
        """ID로 백테스트 조회"""
        
        query = """
        SELECT * FROM backtests WHERE id = ?
        """
        
        row = self.db.fetchone(query, (backtest_id.value,))
        if row:
            return self._map_to_domain(row)
        return None
    
    def find_by_symbol_and_period(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Backtest]:
        """심볼과 기간으로 백테스트 조회"""
        
        query = """
        SELECT * FROM backtests 
        WHERE symbol = ? AND start_date >= ? AND end_date <= ?
        ORDER BY created_at DESC
        """
        
        rows = self.db.fetchall(query, (
            symbol, 
            start_date.isoformat(), 
            end_date.isoformat()
        ))
        
        return [self._map_to_domain(row) for row in rows]
    
    def _save_trades(self, backtest_id: str, trades: List[BacktestTrade]):
        """거래 기록 저장"""
        
        # 기존 거래 삭제
        self.db.execute("DELETE FROM backtest_trades WHERE backtest_id = ?", (backtest_id,))
        
        if not trades:
            return
        
        # 새 거래 저장
        query = """
        INSERT INTO backtest_trades 
        (backtest_id, timestamp, action, price, quantity, commission, 
         position_id, strategy_signal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        trade_data = [
            (
                backtest_id,
                trade.timestamp.isoformat(),
                trade.action,
                float(trade.price),
                float(trade.quantity),
                float(trade.commission),
                trade.position_id,
                trade.strategy_signal
            )
            for trade in trades
        ]
        
        self.db.executemany(query, trade_data)
    
    def _save_portfolio_snapshots(self, backtest_id: str, snapshots: List[PortfolioSnapshot]):
        """포트폴리오 스냅샷 저장"""
        
        # 기존 스냅샷 삭제
        self.db.execute("DELETE FROM backtest_portfolio_snapshots WHERE backtest_id = ?", (backtest_id,))
        
        if not snapshots:
            return
        
        # 새 스냅샷 저장
        query = """
        INSERT INTO backtest_portfolio_snapshots 
        (backtest_id, timestamp, cash_balance, position_value, 
         total_value, unrealized_pnl, realized_pnl)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        snapshot_data = [
            (
                backtest_id,
                snapshot.timestamp.isoformat(),
                float(snapshot.cash_balance),
                float(snapshot.position_value),
                float(snapshot.total_value),
                float(snapshot.unrealized_pnl),
                float(snapshot.realized_pnl)
            )
            for snapshot in snapshots
        ]
        
        self.db.executemany(query, snapshot_data)
```

## 🎨 Presentation Layer 구현

### 1. 백테스팅 View
```python
# presentation/views/backtest_view.py
class BacktestView(QWidget):
    """백테스트 View"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_charts()
    
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout()
        
        # 설정 패널
        self.config_panel = self.create_config_panel()
        layout.addWidget(self.config_panel)
        
        # 결과 패널
        self.results_panel = self.create_results_panel()
        layout.addWidget(self.results_panel)
        
        self.setLayout(layout)
    
    def create_config_panel(self) -> QWidget:
        """설정 패널 생성"""
        panel = QGroupBox("백테스트 설정")
        layout = QGridLayout()
        
        # 기간 설정
        layout.addWidget(QLabel("시작 날짜:"), 0, 0)
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addYears(-1))
        layout.addWidget(self.start_date_edit, 0, 1)
        
        layout.addWidget(QLabel("종료 날짜:"), 0, 2)
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        layout.addWidget(self.end_date_edit, 0, 3)
        
        # 초기 자본
        layout.addWidget(QLabel("초기 자본:"), 1, 0)
        self.initial_capital_edit = QSpinBox()
        self.initial_capital_edit.setRange(100000, 100000000)
        self.initial_capital_edit.setValue(1000000)
        self.initial_capital_edit.setSuffix(" 원")
        layout.addWidget(self.initial_capital_edit, 1, 1)
        
        # 실행 버튼
        self.run_button = QPushButton("백테스트 실행")
        layout.addWidget(self.run_button, 1, 2, 1, 2)
        
        panel.setLayout(layout)
        return panel
    
    def create_results_panel(self) -> QWidget:
        """결과 패널 생성"""
        panel = QGroupBox("백테스트 결과")
        layout = QHBoxLayout()
        
        # 성능 지표 테이블
        self.metrics_table = self.create_metrics_table()
        layout.addWidget(self.metrics_table, 1)
        
        # 차트 영역
        self.chart_widget = self.create_chart_widget()
        layout.addWidget(self.chart_widget, 2)
        
        panel.setLayout(layout)
        return panel
    
    def create_metrics_table(self) -> QTableWidget:
        """성능 지표 테이블 생성"""
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["지표", "값"])
        table.setRowCount(8)
        
        # 지표 이름 설정
        metrics = [
            "총 수익률", "연환산 수익률", "최대 낙폭", "샤프 비율",
            "승률", "수익 팩터", "총 거래 수", "평균 보유 시간"
        ]
        
        for i, metric in enumerate(metrics):
            table.setItem(i, 0, QTableWidgetItem(metric))
            table.setItem(i, 1, QTableWidgetItem("-"))
        
        table.resizeColumnsToContents()
        return table
    
    def update_results(self, performance_metrics: PerformanceMetrics):
        """결과 업데이트"""
        
        # 성능 지표 테이블 업데이트
        metrics_values = [
            f"{performance_metrics.total_return:.2%}",
            f"{performance_metrics.annual_return:.2%}",
            f"{performance_metrics.max_drawdown:.2%}",
            f"{performance_metrics.sharpe_ratio:.2f}",
            f"{performance_metrics.win_rate:.2%}",
            f"{performance_metrics.profit_factor:.2f}",
            f"{performance_metrics.total_trades}",
            f"{performance_metrics.avg_holding_time.total_seconds() / 3600:.1f}시간"
        ]
        
        for i, value in enumerate(metrics_values):
            self.metrics_table.setItem(i, 1, QTableWidgetItem(value))
        
        # 차트 업데이트
        self.update_chart(performance_metrics)
```

## 🔍 다음 단계

- **[새 전략 추가](14_NEW_STRATEGY_ADDITION.md)**: 백테스팅 가능한 전략 추가
- **[성능 최적화](10_PERFORMANCE_OPTIMIZATION.md)**: 대용량 데이터 처리 최적화
- **[모니터링 전략](17_MONITORING_STRATEGY.md)**: 백테스팅 성능 모니터링

---
**💡 핵심**: "Clean Architecture를 통해 확장 가능하고 테스트 가능한 백테스팅 시스템을 구축하여 다양한 전략의 성능을 정확하게 분석합니다!"
