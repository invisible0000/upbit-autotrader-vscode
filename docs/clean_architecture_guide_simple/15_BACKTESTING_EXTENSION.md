# 📊 백테스팅 확장 가이드

> **목적**: Clean Architecture에서 백테스팅 시스템 구현 및 확장  
> **대상**: LLM 에이전트, 개발자  
> **갱신**: 2025-08-03

## 🎯 백테스팅 시스템 개요

### 핵심 기능
```python
BACKTESTING_CAPABILITIES = {
    "전략검증": "역사적 데이터로 매매 전략 성능 분석",
    "성능지표": "수익률, MDD, 샤프비율, 승률 등 계산",
    "리스크분석": "최대손실, 변동성, 드로우다운 기간 분석",
    "최적화": "파라미터 조합별 성능 비교",
    "시뮬레이션": "실제 거래 환경과 99.9% 일치"
}
```

### 처리 성능 목표
- **1년 분봉 데이터**: 5분 내 처리 완료
- **동시 백테스팅**: 최대 10개 전략 병렬 처리
- **메모리 효율성**: 1GB 이하 메모리 사용
- **정확성**: 실제 거래 대비 99.9% 일치

## 💎 Domain Layer 구현

### 백테스팅 엔티티
```python
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum

class BacktestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class BacktestConfiguration:
    """백테스팅 설정"""
    strategy_id: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_balance: Decimal
    commission_rate: Decimal = Decimal('0.0005')  # 0.05%
    slippage_rate: Decimal = Decimal('0.0001')    # 0.01%
    
@dataclass 
class BacktestResult:
    """백테스팅 결과"""
    id: str
    config: BacktestConfiguration
    status: BacktestStatus
    
    # 성능 지표
    total_return: Optional[Decimal] = None
    annual_return: Optional[Decimal] = None
    max_drawdown: Optional[Decimal] = None
    sharpe_ratio: Optional[Decimal] = None
    win_rate: Optional[Decimal] = None
    profit_factor: Optional[Decimal] = None
    
    # 거래 통계
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_holding_period: Optional[timedelta] = None
    
    # 추가 정보
    created_at: datetime = datetime.now()
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def calculate_performance_metrics(self, trades: List['BacktestTrade']):
        """성능 지표 계산"""
        if not trades:
            return
            
        # 기본 통계
        self.total_trades = len(trades)
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]
        
        self.winning_trades = len(winning_trades)
        self.losing_trades = len(losing_trades)
        self.win_rate = Decimal(self.winning_trades) / Decimal(self.total_trades) if self.total_trades > 0 else Decimal('0')
        
        # 수익률 계산
        total_pnl = sum(trade.pnl for trade in trades)
        self.total_return = total_pnl / self.config.initial_balance
        
        # 연간 수익률
        days = (self.config.end_date - self.config.start_date).days
        if days > 0:
            self.annual_return = self.total_return * Decimal('365') / Decimal(days)
            
        # 수익 팩터
        total_profit = sum(t.pnl for t in winning_trades)
        total_loss = abs(sum(t.pnl for t in losing_trades))
        self.profit_factor = total_profit / total_loss if total_loss > 0 else None
        
        # 평균 보유 기간
        if trades:
            total_holding_time = sum((t.exit_time - t.entry_time).total_seconds() for t in trades)
            avg_seconds = total_holding_time / len(trades)
            self.avg_holding_period = timedelta(seconds=avg_seconds)

@dataclass
class BacktestTrade:
    """백테스팅 거래 기록"""
    id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    entry_time: datetime
    entry_price: Decimal
    quantity: Decimal
    exit_time: Optional[datetime] = None
    exit_price: Optional[Decimal] = None
    commission: Decimal = Decimal('0')
    slippage: Decimal = Decimal('0')
    
    @property
    def pnl(self) -> Decimal:
        """손익 계산"""
        if not self.exit_price:
            return Decimal('0')
            
        if self.side == 'buy':
            gross_pnl = (self.exit_price - self.entry_price) * self.quantity
        else:  # sell
            gross_pnl = (self.entry_price - self.exit_price) * self.quantity
            
        return gross_pnl - self.commission - self.slippage
        
    @property
    def return_rate(self) -> Decimal:
        """수익률 계산"""
        if not self.exit_price:
            return Decimal('0')
        investment = self.entry_price * self.quantity
        return self.pnl / investment if investment > 0 else Decimal('0')

class BacktestDomainService:
    """백테스팅 도메인 서비스"""
    
    def calculate_max_drawdown(self, equity_curve: List[Decimal]) -> Decimal:
        """최대 드로우다운 계산"""
        if len(equity_curve) < 2:
            return Decimal('0')
            
        peak = equity_curve[0]
        max_dd = Decimal('0')
        
        for value in equity_curve[1:]:
            if value > peak:
                peak = value
            else:
                drawdown = (peak - value) / peak
                max_dd = max(max_dd, drawdown)
                
        return max_dd
        
    def calculate_sharpe_ratio(self, returns: List[Decimal], 
                             risk_free_rate: Decimal = Decimal('0.02')) -> Decimal:
        """샤프 비율 계산"""
        if len(returns) < 2:
            return Decimal('0')
            
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = variance.sqrt() if variance > 0 else Decimal('0')
        
        if std_dev == 0:
            return Decimal('0')
            
        excess_return = avg_return - risk_free_rate / Decimal('252')  # 일간 무위험 수익률
        return excess_return / std_dev * (Decimal('252').sqrt())  # 연간화
        
    def apply_commission_and_slippage(self, price: Decimal, quantity: Decimal,
                                    commission_rate: Decimal, 
                                    slippage_rate: Decimal) -> tuple[Decimal, Decimal]:
        """수수료와 슬리피지 적용"""
        notional = price * quantity
        commission = notional * commission_rate
        
        # 슬리피지는 가격에 직접 적용
        slippage_amount = price * slippage_rate
        adjusted_price = price + slippage_amount  # 매수 시 불리하게
        
        return commission, adjusted_price
```

## ⚙️ Application Layer 구현

### 백테스팅 UseCase
```python
class RunBacktestCommand:
    """백테스팅 실행 명령"""
    def __init__(self, strategy_id: str, symbol: str, start_date: datetime, 
                 end_date: datetime, initial_balance: Decimal):
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_balance = initial_balance

class BacktestingUseCase:
    """백테스팅 UseCase"""
    
    def __init__(self, backtest_repo, strategy_repo, market_data_service, 
                 trading_engine):
        self.backtest_repo = backtest_repo
        self.strategy_repo = strategy_repo
        self.market_data_service = market_data_service
        self.trading_engine = trading_engine
        self.domain_service = BacktestDomainService()
        
    async def run_backtest(self, command: RunBacktestCommand) -> Result[str]:
        """백테스팅 실행"""
        try:
            # 1. 설정 생성
            config = BacktestConfiguration(
                strategy_id=command.strategy_id,
                symbol=command.symbol,
                start_date=command.start_date,
                end_date=command.end_date,
                initial_balance=command.initial_balance
            )
            
            # 2. 백테스팅 결과 객체 생성
            backtest_result = BacktestResult(
                id=self._generate_id(),
                config=config,
                status=BacktestStatus.PENDING
            )
            
            # 3. 초기 저장
            await self.backtest_repo.save(backtest_result)
            
            # 4. 비동기 실행 시작
            await self._execute_backtest(backtest_result)
            
            return Result.success(backtest_result.id)
            
        except Exception as e:
            return Result.failure(f"백테스팅 실행 실패: {e}")
            
    async def _execute_backtest(self, backtest_result: BacktestResult):
        """실제 백테스팅 실행"""
        try:
            backtest_result.status = BacktestStatus.RUNNING
            await self.backtest_repo.save(backtest_result)
            
            # 1. 전략 로드
            strategy = await self.strategy_repo.get_by_id(backtest_result.config.strategy_id)
            if not strategy:
                raise ValueError("전략을 찾을 수 없습니다")
                
            # 2. 시장 데이터 로드
            market_data = await self.market_data_service.get_historical_data(
                backtest_result.config.symbol,
                backtest_result.config.start_date,
                backtest_result.config.end_date
            )
            
            # 3. 시뮬레이션 실행
            simulation_result = await self._run_simulation(
                strategy, market_data, backtest_result.config
            )
            
            # 4. 성과 계산
            backtest_result.calculate_performance_metrics(simulation_result.trades)
            backtest_result.max_drawdown = self.domain_service.calculate_max_drawdown(
                simulation_result.equity_curve
            )
            backtest_result.sharpe_ratio = self.domain_service.calculate_sharpe_ratio(
                simulation_result.daily_returns
            )
            
            # 5. 완료 처리
            backtest_result.status = BacktestStatus.COMPLETED
            backtest_result.completed_at = datetime.now()
            
        except Exception as e:
            backtest_result.status = BacktestStatus.FAILED
            backtest_result.error_message = str(e)
            
        finally:
            await self.backtest_repo.save(backtest_result)
            
    async def _run_simulation(self, strategy, market_data, config):
        """시뮬레이션 실행"""
        simulator = TradingSimulator(config)
        
        for i, candle in enumerate(market_data.iterrows()):
            timestamp, data = candle
            
            # 전략 신호 생성
            signal = strategy.generate_signal(market_data.iloc[:i+1])
            
            # 거래 실행
            if signal in ['BUY', 'SELL']:
                simulator.execute_trade(signal, timestamp, data['close'])
                
            # 포지션 관리
            simulator.update_positions(timestamp, data['close'])
            
        return simulator.get_result()
        
    def _generate_id(self) -> str:
        """고유 ID 생성"""
        import uuid
        return f"bt_{uuid.uuid4().hex[:8]}"

class BacktestOptimizationUseCase:
    """백테스팅 최적화 UseCase"""
    
    def __init__(self, backtesting_usecase):
        self.backtesting_usecase = backtesting_usecase
        
    async def optimize_strategy_parameters(self, strategy_id: str, 
                                         parameter_ranges: Dict[str, List],
                                         optimization_metric: str = 'sharpe_ratio') -> Result[Dict]:
        """전략 파라미터 최적화"""
        best_result = None
        best_params = None
        best_score = float('-inf')
        
        # 파라미터 조합 생성
        param_combinations = self._generate_parameter_combinations(parameter_ranges)
        
        for params in param_combinations:
            # 임시 전략 생성
            temp_strategy = await self._create_strategy_with_params(strategy_id, params)
            
            # 백테스팅 실행
            command = RunBacktestCommand(
                strategy_id=temp_strategy.id,
                symbol="KRW-BTC",
                start_date=datetime.now() - timedelta(days=365),
                end_date=datetime.now(),
                initial_balance=Decimal('1000000')
            )
            
            result = await self.backtesting_usecase.run_backtest(command)
            
            if result.is_success():
                backtest = await self.backtesting_usecase.backtest_repo.get_by_id(result.value)
                score = getattr(backtest, optimization_metric, 0)
                
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_result = backtest
                    
        return Result.success({
            'best_parameters': best_params,
            'best_score': best_score,
            'best_result': best_result
        })
        
    def _generate_parameter_combinations(self, parameter_ranges: Dict[str, List]) -> List[Dict]:
        """파라미터 조합 생성"""
        import itertools
        
        keys = parameter_ranges.keys()
        values = parameter_ranges.values()
        combinations = list(itertools.product(*values))
        
        return [dict(zip(keys, combo)) for combo in combinations]
```

## 🔌 Infrastructure Layer 구현

### 고성능 시뮬레이터
```python
class TradingSimulator:
    """고성능 거래 시뮬레이터"""
    
    def __init__(self, config: BacktestConfiguration):
        self.config = config
        self.balance = config.initial_balance
        self.positions = {}
        self.trades = []
        self.equity_curve = [config.initial_balance]
        self.daily_returns = []
        
    def execute_trade(self, signal: str, timestamp: datetime, price: Decimal):
        """거래 실행"""
        if signal == 'BUY':
            self._execute_buy(timestamp, price)
        elif signal == 'SELL':
            self._execute_sell(timestamp, price)
            
    def _execute_buy(self, timestamp: datetime, price: Decimal):
        """매수 실행"""
        # 수수료와 슬리피지 적용
        commission, adjusted_price = self.domain_service.apply_commission_and_slippage(
            price, self.balance / price, 
            self.config.commission_rate, 
            self.config.slippage_rate
        )
        
        quantity = (self.balance - commission) / adjusted_price
        
        if quantity > 0:
            trade = BacktestTrade(
                id=self._generate_trade_id(),
                symbol=self.config.symbol,
                side='buy',
                entry_time=timestamp,
                entry_price=adjusted_price,
                quantity=quantity,
                commission=commission
            )
            
            self.positions[trade.id] = trade
            self.balance = Decimal('0')  # 전량 매수
            
    def _execute_sell(self, timestamp: datetime, price: Decimal):
        """매도 실행"""
        for position_id, position in list(self.positions.items()):
            # 수수료와 슬리피지 적용
            commission, adjusted_price = self.domain_service.apply_commission_and_slippage(
                price, position.quantity,
                self.config.commission_rate,
                -self.config.slippage_rate  # 매도 시 반대
            )
            
            # 포지션 종료
            position.exit_time = timestamp
            position.exit_price = adjusted_price
            position.commission += commission
            
            # 잔고 업데이트
            proceeds = position.quantity * adjusted_price - commission
            self.balance += proceeds
            
            # 거래 기록
            self.trades.append(position)
            del self.positions[position_id]
            
    def update_positions(self, timestamp: datetime, price: Decimal):
        """포지션 평가 및 자산 업데이트"""
        total_value = self.balance
        
        # 보유 포지션 평가
        for position in self.positions.values():
            position_value = position.quantity * price
            total_value += position_value
            
        self.equity_curve.append(total_value)
        
        # 일간 수익률 계산 (매일 종가 기준)
        if len(self.equity_curve) > 1:
            daily_return = (total_value - self.equity_curve[-2]) / self.equity_curve[-2]
            self.daily_returns.append(daily_return)
            
    def get_result(self):
        """시뮬레이션 결과 반환"""
        return {
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'daily_returns': self.daily_returns,
            'final_balance': self.equity_curve[-1] if self.equity_curve else self.config.initial_balance
        }
        
    def _generate_trade_id(self) -> str:
        """거래 ID 생성"""
        import uuid
        return f"trade_{uuid.uuid4().hex[:8]}"
```

### 병렬 처리 시스템
```python
import asyncio
from concurrent.futures import ProcessPoolExecutor

class ParallelBacktestingService:
    """병렬 백테스팅 서비스"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ProcessPoolExecutor(max_workers=max_workers)
        
    async def run_multiple_backtests(self, commands: List[RunBacktestCommand]) -> List[Result]:
        """다중 백테스팅 병렬 실행"""
        loop = asyncio.get_event_loop()
        
        # 각 백테스팅을 별도 프로세스에서 실행
        tasks = []
        for command in commands:
            task = loop.run_in_executor(
                self.executor, 
                self._run_single_backtest, 
                command
            )
            tasks.append(task)
            
        # 모든 백테스팅 완료 대기
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
        
    def _run_single_backtest(self, command: RunBacktestCommand) -> Result:
        """단일 백테스팅 실행 (별도 프로세스)"""
        # 프로세스 내에서 실행되는 백테스팅 로직
        pass
```

## 🎨 Presentation Layer 구현

### 백테스팅 결과 시각화
```python
class BacktestResultPresenter:
    """백테스팅 결과 프레젠터"""
    
    def __init__(self, view):
        self.view = view
        
    def present_backtest_result(self, result: BacktestResult):
        """백테스팅 결과 표시"""
        # 성능 지표 표시
        self.view.show_performance_metrics({
            '총 수익률': f"{result.total_return:.2%}",
            '연간 수익률': f"{result.annual_return:.2%}",
            '최대 낙폭': f"{result.max_drawdown:.2%}",
            '샤프 비율': f"{result.sharpe_ratio:.2f}",
            '승률': f"{result.win_rate:.2%}",
            '총 거래수': str(result.total_trades)
        })
        
        # 차트 업데이트
        self.view.update_equity_curve_chart(result.equity_curve)
        self.view.update_drawdown_chart(result.drawdown_curve)
        
    def present_optimization_result(self, optimization_result: Dict):
        """최적화 결과 표시"""
        self.view.show_best_parameters(optimization_result['best_parameters'])
        self.view.show_parameter_heatmap(optimization_result['parameter_performance'])
```

## 📚 관련 문서

- [시스템 개요](01_SYSTEM_OVERVIEW.md): Clean Architecture 구조
- [성능 최적화](09_PERFORMANCE_OPTIMIZATION.md): 처리 성능 향상
- [기능 개발](04_FEATURE_DEVELOPMENT.md): 새 기능 추가 방법
- [테스팅 전략](11_TESTING_STRATEGY.md): 백테스팅 검증 방법

---
**💡 핵심**: "정확하고 빠른 백테스팅으로 전략의 실제 성능을 검증하세요!"
