"""
상태 기반 백테스팅 엔진

역할 기반 전략 시스템을 위한 백테스팅 엔진:
- 포지션 상태에 따른 전략 역할 전환 로직
- StrategyCombination과 완전 연동
- 진입 대기 → 포지션 관리 → 포지션 종료 상태 순환
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
import sys
import os

# 모듈 임포트를 위한 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, project_root)

try:
    # 상대 임포트 시도 (패키지로 실행될 때)
    from .strategy_combination import StrategyCombination, StrategyConfig, ConflictResolutionType
    from .role_based_strategy import (
        BaseStrategy, EntryStrategy, ManagementStrategy, 
        TradingSignal, SignalType, StrategyRole,
        MovingAverageCrossEntry, RSIEntry, BollingerBandsEntry,
        VolatilityBreakoutEntry, MACDEntry, StochasticEntry,
        AveragingDownManagement, PyramidingManagement, TrailingStopManagement,
        FixedTargetManagement, PartialExitManagement, TimeBasedExitManagement
    )
except ImportError:
    # 절대 임포트 (직접 실행될 때)
    from upbit_auto_trading.business_logic.strategy.strategy_combination import (
        StrategyCombination, StrategyConfig, ConflictResolutionType
    )
    from upbit_auto_trading.business_logic.strategy.role_based_strategy import (
        BaseStrategy, EntryStrategy, ManagementStrategy, 
        TradingSignal, SignalType, StrategyRole,
        MovingAverageCrossEntry, RSIEntry, BollingerBandsEntry,
        VolatilityBreakoutEntry, MACDEntry, StochasticEntry,
        AveragingDownManagement, PyramidingManagement, TrailingStopManagement,
        FixedTargetManagement, PartialExitManagement, TimeBasedExitManagement
    )


class BacktestState(Enum):
    """백테스트 엔진 상태"""
    WAITING_ENTRY = "waiting_entry"        # 진입 대기
    POSITION_MANAGEMENT = "position_management"  # 포지션 관리
    POSITION_EXIT = "position_exit"        # 포지션 종료


@dataclass
class PositionInfo:
    """포지션 정보"""
    direction: str  # 'BUY' | 'SELL'
    entry_price: float
    entry_time: datetime
    quantity: float
    stop_price: Optional[float] = None
    management_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def get_current_pnl(self, current_price: float) -> float:
        """현재 손익 계산"""
        if self.direction == 'BUY':
            return (current_price - self.entry_price) / self.entry_price
        else:  # SELL
            return (self.entry_price - current_price) / self.entry_price
    
    def get_average_price(self) -> float:
        """평균 단가 계산 (추가 매수/매도 반영)"""
        total_cost = self.entry_price * self.quantity
        total_quantity = self.quantity
        
        for history in self.management_history:
            if history['action'] in ['ADD_BUY', 'ADD_SELL']:
                action_quantity = history.get('quantity', 0)
                action_price = history.get('price', 0)
                
                if history['action'] == 'ADD_BUY' and self.direction == 'BUY':
                    total_cost += action_price * action_quantity
                    total_quantity += action_quantity
                elif history['action'] == 'ADD_SELL' and self.direction == 'SELL':
                    total_cost += action_price * action_quantity
                    total_quantity += action_quantity
        
        return total_cost / total_quantity if total_quantity > 0 else self.entry_price


@dataclass
class BacktestResult:
    """백테스트 결과"""
    combination_id: str
    combination_name: str
    
    # 전체 성과
    total_return: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # 리스크 지표
    sharpe_ratio: float
    max_drawdown: float
    
    # 전략별 기여도
    entry_contribution: Dict[str, float]
    management_contribution: Dict[str, float]
    
    # 거래 상세
    trade_log: List[Dict[str, Any]]
    position_log: List[Dict[str, Any]]
    
    # 실행 정보
    backtest_start: datetime
    backtest_end: datetime
    data_points: int


class StrategyCombinationBacktestEngine:
    """전략 조합 백테스트 엔진"""
    
    def __init__(self):
        self.state = BacktestState.WAITING_ENTRY
        self.position: Optional[PositionInfo] = None
        self.current_combination: Optional[StrategyCombination] = None
        
        # 전략 인스턴스 저장
        self.entry_strategy: Optional[EntryStrategy] = None
        self.management_strategies: List[ManagementStrategy] = []
        
        # 백테스트 결과 저장
        self.trade_log: List[Dict[str, Any]] = []
        self.position_log: List[Dict[str, Any]] = []
        
        # 성과 추적
        self.initial_capital = 1000000  # 초기 자본
        self.current_capital = self.initial_capital
        self.peak_capital = self.initial_capital
        self.max_drawdown = 0.0
        
        # 리스크 관리 설정 (매개변수 최적화 대상)
        self.risk_settings = {
            'max_position_risk': 0.02,      # 포지션당 최대 리스크 (2%)
            'stop_loss_percent': 0.05,      # 기본 스탑로스 (5%)
            'trailing_stop_percent': 0.03,  # 트레일링 스탑 (3%)
            'max_drawdown_limit': 0.20,     # 최대 낙폭 제한 (20%)
            'position_size_method': 'fixed_risk'  # 포지션 크기 계산 방법
        }
        
        # 경고 플래그 (중복 경고 방지)
        self.max_drawdown_warning_shown = False
        
    def load_combination(self, combination: StrategyCombination) -> None:
        """전략 조합 로딩 및 초기화"""
        self.current_combination = combination
        
        # 진입 전략 인스턴스 생성
        self.entry_strategy = self._create_strategy_instance(
            combination.entry_strategy, is_entry=True
        )
        
        # 관리 전략 인스턴스들 생성
        self.management_strategies = []
        for mgmt_config in combination.management_strategies:
            mgmt_strategy = self._create_strategy_instance(mgmt_config, is_entry=False)
            # 전략 인스턴스에 우선순위 정보 저장
            mgmt_strategy.config_priority = mgmt_config.priority
            self.management_strategies.append(mgmt_strategy)
        
        # 우선순위별 정렬 (priority 속성이 있는 경우만)
        self.management_strategies.sort(key=lambda s: getattr(s, 'priority', getattr(s, 'config_priority', 0)))
        
        print(f"✅ 전략 조합 로딩 완료: {combination.name}")
        print(f"   📈 진입: {combination.entry_strategy.strategy_name}")
        print(f"   🛡️ 관리: {[ms.strategy_name for ms in combination.management_strategies]}")
    
    def _create_strategy_instance(self, config: StrategyConfig, is_entry: bool) -> BaseStrategy:
        """설정을 기반으로 전략 인스턴스 생성"""
        strategy_map = {
            # 진입 전략
            "ma_cross_entry": MovingAverageCrossEntry,
            "rsi_entry": RSIEntry,
            "bollinger_entry": BollingerBandsEntry,
            "volatility_entry": VolatilityBreakoutEntry,
            "macd_entry": MACDEntry,
            "stochastic_entry": StochasticEntry,
            
            # 관리 전략
            "averaging_down": AveragingDownManagement,
            "pyramiding": PyramidingManagement,
            "trailing_stop": TrailingStopManagement,
            "fixed_target": FixedTargetManagement,
            "partial_exit": PartialExitManagement,
            "time_based": TimeBasedExitManagement
        }
        
        strategy_class = strategy_map.get(config.strategy_id)
        if not strategy_class:
            raise ValueError(f"알 수 없는 전략: {config.strategy_id}")
        
        # 전략 인스턴스 생성 (파라미터 전달)
        strategy = strategy_class(parameters=config.parameters)
        
        # 우선순위 설정 (관리 전략만)
        if not is_entry and hasattr(strategy, 'priority'):
            strategy.priority = config.priority
        
        return strategy
    
    def set_risk_parameters(self, risk_params: Dict[str, Any]) -> None:
        """리스크 매개변수 설정 (최적화용)"""
        self.risk_settings.update(risk_params)
        print(f"   🛡️ 리스크 매개변수 업데이트: {risk_params}")
    
    def _check_stop_loss(self, current_price: float, timestamp: datetime) -> bool:
        """스탑로스 체크"""
        if not self.position:
            return False
        
        # 기본 스탑로스 체크
        pnl = self.position.get_current_pnl(current_price)
        stop_loss_threshold = -self.risk_settings['stop_loss_percent']
        
        if pnl <= stop_loss_threshold:
            self._close_position(current_price, timestamp, f"STOP_LOSS({pnl*100:.1f}%)")
            return True
        
        # 트레일링 스탑 체크
        if self.position.stop_price:
            if self.position.direction == 'BUY' and current_price <= self.position.stop_price:
                self._close_position(current_price, timestamp, f"TRAILING_STOP")
                return True
            elif self.position.direction == 'SELL' and current_price >= self.position.stop_price:
                self._close_position(current_price, timestamp, f"TRAILING_STOP")
                return True
        
        return False
    
    def _update_trailing_stop(self, current_price: float) -> None:
        """트레일링 스탑 업데이트"""
        if not self.position:
            return
        
        trailing_percent = self.risk_settings['trailing_stop_percent']
        
        if self.position.direction == 'BUY':
            # 매수 포지션: 가격이 오를 때 스탑 상향 조정
            new_stop = current_price * (1 - trailing_percent)
            if self.position.stop_price is None or new_stop > self.position.stop_price:
                self.position.stop_price = new_stop
        else:  # SELL
            # 매도 포지션: 가격이 내릴 때 스탑 하향 조정
            new_stop = current_price * (1 + trailing_percent)
            if self.position.stop_price is None or new_stop < self.position.stop_price:
                self.position.stop_price = new_stop
    
    def _check_max_drawdown_limit(self) -> bool:
        """최대 낙폭 제한 체크"""
        current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        max_limit = self.risk_settings['max_drawdown_limit']
        
        if current_drawdown >= max_limit:
            # 한 번만 경고 출력
            if not self.max_drawdown_warning_shown:
                print(f"   🚨 최대 낙폭 제한 도달: {current_drawdown*100:.1f}% >= {max_limit*100:.1f}%")
                print(f"      🛡️ 리스크 관리 모드 활성화 - 새로운 포지션 진입 중단")
                self.max_drawdown_warning_shown = True
            return True
        return False
    
    def _calculate_position_size(self, entry_price: float, signal: 'TradingSignal') -> float:
        """최적화 가능한 포지션 크기 계산"""
        method = self.risk_settings['position_size_method']
        risk_percent = self.risk_settings['max_position_risk']
        
        if method == 'fixed_risk':
            # 고정 리스크 방식
            return self.current_capital * risk_percent / entry_price
        
        elif method == 'volatility_adjusted':
            # 변동성 조정 방식 (향후 구현)
            # ATR 기반 포지션 크기 조정
            base_size = self.current_capital * risk_percent / entry_price
            # volatility_multiplier = self._calculate_volatility_multiplier()
            return base_size  # * volatility_multiplier
        
        elif method == 'kelly_criterion':
            # 켈리 공식 방식 (향후 구현)
            # 과거 승률과 평균 수익/손실 기반
            return self.current_capital * risk_percent / entry_price
        
        else:
            # 기본값
            return self.current_capital * risk_percent / entry_price
    
    def run_backtest(self, market_data: pd.DataFrame, 
                    initial_capital: float = 1000000) -> BacktestResult:
        """백테스트 실행"""
        if not self.current_combination:
            raise ValueError("전략 조합이 로딩되지 않았습니다")
        
        print(f"🚀 백테스트 시작: {self.current_combination.name}")
        
        # 초기화
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.peak_capital = initial_capital
        self.max_drawdown = 0.0
        self.trade_log = []
        self.position_log = []
        self.state = BacktestState.WAITING_ENTRY
        self.position = None
        
        # 경고 플래그 초기화
        self.max_drawdown_warning_shown = False
        
        # 기술적 지표 계산
        market_data = self._calculate_indicators(market_data)
        
        # 지표 계산 결과 확인
        print(f"   📊 지표 계산 완료:")
        for col in market_data.columns:
            if 'RSI' in col:
                valid_count = market_data[col].notna().sum()
                print(f"      {col}: {valid_count}/{len(market_data)} 유효 데이터")
                if valid_count > 0:
                    rsi_values = market_data[col].dropna()
                    print(f"         범위: {rsi_values.min():.1f} ~ {rsi_values.max():.1f}")
                    print(f"         평균: {rsi_values.mean():.1f}")
                    # 과매수/과매도 구간 분포 확인
                    oversold = (rsi_values < 30).sum()
                    overbought = (rsi_values > 70).sum()
                    print(f"         과매도(<30): {oversold}개, 과매수(>70): {overbought}개")
        
        # 가격 데이터 요약도 출력
        print(f"   💰 가격 데이터 요약:")
        print(f"      범위: {market_data['close'].min():.0f} ~ {market_data['close'].max():.0f}")
        print(f"      시작: {market_data['close'].iloc[0]:.0f}, 종료: {market_data['close'].iloc[-1]:.0f}")
        print(f"      변화율: {((market_data['close'].iloc[-1] / market_data['close'].iloc[0]) - 1) * 100:+.2f}%")
        
        # 전체 데이터를 저장 (전략이 과거 데이터를 참조할 수 있도록)
        self.full_market_data = market_data
        
        backtest_start = datetime.now()
        last_timestamp = None
        
        # 시장 데이터 순회
        for i, (timestamp, row) in enumerate(market_data.iterrows()):
            last_timestamp = timestamp
            self._process_market_data(timestamp, row)
            
            # 진행률 표시 (10% 단위)
            if i % max(1, len(market_data) // 10) == 0:
                progress = (i / len(market_data)) * 100
                print(f"   📊 진행률: {progress:.1f}%")
        
        backtest_end = datetime.now()
        
        # 최종 포지션 정리
        if self.position and last_timestamp:
            final_price = market_data.iloc[-1]['close']
            self._close_position(final_price, last_timestamp, "BACKTEST_END")
        
        # 결과 계산
        result = self._calculate_backtest_result(backtest_start, backtest_end, len(market_data))
        
        print(f"✅ 백테스트 완료")
        print(f"   💰 총 수익률: {result.total_return:.2f}%")
        print(f"   📊 총 거래: {result.total_trades}회")
        print(f"   🎯 승률: {result.win_rate:.1f}%")
        print(f"   📉 최대 낙폭: {result.max_drawdown:.2f}%")
        
        return result
    
    def _calculate_indicators(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """전략에 필요한 기술적 지표 계산"""
        data = market_data.copy()
        
        # 진입 전략 지표 계산
        entry_indicators = self.entry_strategy.get_required_indicators()
        for indicator in entry_indicators:
            if indicator["name"] == "RSI":
                period = indicator["params"]["window"]
                data[f"RSI_{period}"] = self._calculate_rsi(data['close'], period)
            elif indicator["name"] == "SMA":
                window = indicator["params"]["window"]
                data[f"SMA_{window}"] = data['close'].rolling(window=window).mean()
            elif indicator["name"] == "MACD":
                fast = indicator["params"].get("fast_period", 12)
                slow = indicator["params"].get("slow_period", 26)
                signal = indicator["params"].get("signal_period", 9)
                macd_line, macd_signal, macd_hist = self._calculate_macd(data['close'], fast, slow, signal)
                data['MACD'] = macd_line
                data['MACD_signal'] = macd_signal
                data['MACD_histogram'] = macd_hist
        
        # 관리 전략 지표 계산
        for mgmt_strategy in self.management_strategies:
            mgmt_indicators = mgmt_strategy.get_required_indicators()
            for indicator in mgmt_indicators:
                if indicator["name"] == "RSI":
                    period = indicator["params"]["window"]
                    if f"RSI_{period}" not in data.columns:
                        data[f"RSI_{period}"] = self._calculate_rsi(data['close'], period)
                elif indicator["name"] == "SMA":
                    window = indicator["params"]["window"]
                    if f"SMA_{window}" not in data.columns:
                        data[f"SMA_{window}"] = data['close'].rolling(window=window).mean()
        
        return data
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI 지표 계산 (개선된 버전)"""
        delta = prices.diff()
        
        # 상승분과 하락분 분리
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 평균 계산 (첫 번째 값은 단순 평균, 이후는 지수 이동 평균)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        
        # RSI 계산
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # NaN과 무한대 값 처리
        rsi = rsi.fillna(50)  # NaN을 중립값 50으로 대체
        rsi = np.where(np.isinf(rsi), 100, rsi)  # 무한대를 100으로 대체
        rsi = np.where(avg_loss == 0, 100, rsi)  # 손실이 없으면 100
        
        return pd.Series(rsi, index=prices.index)
    
    def _calculate_macd(self, prices: pd.Series, fast_period: int = 12, 
                       slow_period: int = 26, signal_period: int = 9) -> tuple:
        """MACD 지표 계산"""
        exp_fast = prices.ewm(span=fast_period).mean()
        exp_slow = prices.ewm(span=slow_period).mean()
        macd_line = exp_fast - exp_slow
        macd_signal = macd_line.ewm(span=signal_period).mean()
        macd_histogram = macd_line - macd_signal
        return macd_line, macd_signal, macd_histogram
    
    def _process_market_data(self, timestamp: datetime, market_data: pd.Series) -> None:
        """시장 데이터 처리 및 상태별 로직 실행"""
        current_price = market_data['close']
        
        # 최대 낙폭 제한 체크 (모든 상태에서)
        if self._check_max_drawdown_limit():
            if self.position:
                self._close_position(current_price, timestamp, "MAX_DRAWDOWN_LIMIT")
            return
        
        if self.state == BacktestState.WAITING_ENTRY:
            # 진입 대기: 진입 전략만 활성화
            # 현재 위치까지의 데이터를 찾기
            current_idx = self.full_market_data.index.get_loc(timestamp)
            
            if current_idx < 1:
                return  # 충분한 데이터가 없음
            
            # 현재까지의 모든 데이터를 전략에 전달
            strategy_data = self.full_market_data.iloc[:current_idx + 1]
            
            entry_signal = self.entry_strategy.generate_entry_signal(strategy_data, None)
            
            # 디버깅 정보 (첫 몇 개 신호만 출력)
            if hasattr(self, 'signal_count'):
                self.signal_count += 1
            else:
                self.signal_count = 1
            
            if self.signal_count <= 3 and entry_signal.signal_type != SignalType.HOLD:
                current_row = strategy_data.iloc[-1]
                print(f"   🔍 진입 신호 디버깅 #{self.signal_count}:")
                print(f"      신호: {entry_signal.signal_type.value}")
                print(f"      가격: {current_row['close']:.0f}")
                if 'RSI_14' in current_row:
                    print(f"      RSI: {current_row['RSI_14']:.1f}")
            
            if entry_signal.signal_type in [SignalType.BUY, SignalType.SELL]:
                self._enter_position(entry_signal, timestamp, market_data)
                self.state = BacktestState.POSITION_MANAGEMENT
                print(f"   📈 진입 신호 감지: {entry_signal.signal_type.value}")
                
        elif self.state == BacktestState.POSITION_MANAGEMENT:
            # 리스크 관리 우선 체크
            if self._check_stop_loss(current_price, timestamp):
                return  # 스탑로스로 청산됨
            
            # 트레일링 스탑 업데이트
            self._update_trailing_stop(current_price)
            
            # 포지션 관리: 관리 전략들 활성화
            management_signals = []
            
            if self.position:
                # PositionInfo를 역할 기반 전략의 PositionInfo로 변환
                position_info = self._convert_position_info(self.position)
                
                # 현재까지의 모든 데이터를 전략에 전달
                current_idx = self.full_market_data.index.get_loc(timestamp)
                strategy_data = self.full_market_data.iloc[:current_idx + 1]
                
                for mgmt_strategy in self.management_strategies:
                    mgmt_signal = mgmt_strategy.generate_management_signal(strategy_data, position_info)
                    if mgmt_signal.signal_type != SignalType.HOLD:
                        management_signals.append(mgmt_signal)
                
                # 충돌 해결
                if management_signals:
                    final_signal = self._resolve_conflicts(management_signals)
                    self._execute_management_action(final_signal, timestamp, market_data)
    
    def _convert_position_info(self, position: PositionInfo) -> 'PositionInfo':
        """백테스트 엔진의 PositionInfo를 역할 기반 전략의 PositionInfo로 변환"""
        # role_based_strategy의 PositionInfo import 필요
        try:
            from .role_based_strategy import PositionInfo as RoleBasedPositionInfo
        except ImportError:
            from upbit_auto_trading.business_logic.strategy.role_based_strategy import PositionInfo as RoleBasedPositionInfo
        
        return RoleBasedPositionInfo(
            direction="LONG" if position.direction == "BUY" else "SHORT",
            entry_price=position.entry_price,
            entry_time=position.entry_time,
            quantity=position.quantity,
            stop_price=position.stop_price,
            management_history=position.management_history
        )
    
    def _enter_position(self, signal: TradingSignal, timestamp: datetime, 
                       market_data: pd.Series) -> None:
        """포지션 진입 (리스크 관리 강화)"""
        entry_price = market_data['close']
        
        # 개선된 포지션 크기 계산
        position_size = self._calculate_position_size(entry_price, signal)
        
        # 초기 스탑로스 설정
        stop_loss_percent = self.risk_settings['stop_loss_percent']
        if signal.signal_type == SignalType.BUY:
            initial_stop = entry_price * (1 - stop_loss_percent)
        else:  # SELL
            initial_stop = entry_price * (1 + stop_loss_percent)
        
        self.position = PositionInfo(
            direction=signal.signal_type.value,
            entry_price=entry_price,
            entry_time=timestamp,
            quantity=position_size,
            stop_price=initial_stop
        )
        
        # 거래 로그 기록
        self.trade_log.append({
            'timestamp': timestamp,
            'action': 'ENTER',
            'direction': signal.signal_type.value,
            'price': entry_price,
            'quantity': position_size,
            'initial_stop': initial_stop,
            'strategy': self.entry_strategy.__class__.__name__,
            'reason': getattr(signal, 'metadata', {}).get('reason', 'Entry signal'),
            'risk_percent': self.risk_settings['max_position_risk']
        })
        
        print(f"   📈 포지션 진입: {signal.signal_type.value} @ {entry_price:.0f}")
        print(f"      수량: {position_size:.4f}, 초기 스탑: {initial_stop:.0f}")
        print(f"      리스크: {self.risk_settings['max_position_risk']*100:.1f}%")
    
    def _execute_management_action(self, signal: TradingSignal, timestamp: datetime,
                                  market_data: pd.Series) -> None:
        """관리 전략 액션 실행"""
        current_price = market_data['close']
        
        if not self.position:
            return
        
        if signal.signal_type == SignalType.ADD_BUY and self.position.direction == 'BUY':
            # 추가 매수 (물타기/불타기)
            add_quantity = signal.quantity or (self.position.quantity * 0.5)
            self.position.quantity += add_quantity
            
            self.position.management_history.append({
                'action': 'ADD_BUY',
                'timestamp': timestamp,
                'price': current_price,
                'quantity': add_quantity,
                'strategy': signal.metadata.get('strategy_name', 'Unknown') if signal.metadata else 'Unknown'
            })
            
            print(f"   💰 추가 매수: +{add_quantity:.3f} @ {current_price:.0f}")
            
        elif signal.signal_type == SignalType.ADD_SELL:
            # 부분 매도
            sell_quantity = signal.quantity or (self.position.quantity * 0.3)
            self.position.quantity -= sell_quantity
            
            # 수익 실현
            pnl = self.position.get_current_pnl(current_price)
            profit = self.current_capital * pnl * (sell_quantity / self.position.quantity)
            self.current_capital += profit
            
            self.position.management_history.append({
                'action': 'ADD_SELL',
                'timestamp': timestamp,
                'price': current_price,
                'quantity': sell_quantity,
                'strategy': signal.metadata.get('strategy_name', 'Unknown') if signal.metadata else 'Unknown'
            })
            
            print(f"   💵 부분 매도: -{sell_quantity:.3f} @ {current_price:.0f}")
            
        elif signal.signal_type == SignalType.UPDATE_STOP:
            # 트레일링 스탑 업데이트
            self.position.stop_price = signal.stop_price
            
            print(f"   🛡️ 스탑 업데이트: {signal.stop_price:.0f}")
            
        elif signal.signal_type == SignalType.CLOSE_POSITION:
            # 전체 포지션 청산
            strategy_name = signal.metadata.get('strategy_name', 'Unknown') if signal.metadata else 'Unknown'
            self._close_position(current_price, timestamp, strategy_name)
    
    def _close_position(self, exit_price: float, timestamp: datetime, reason: str) -> None:
        """포지션 청산"""
        if not self.position:
            return
        
        # 수익률 계산
        pnl = self.position.get_current_pnl(exit_price)
        profit_amount = self.current_capital * pnl
        self.current_capital += profit_amount
        
        # 최대 낙폭 업데이트
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        
        current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        self.max_drawdown = max(self.max_drawdown, current_drawdown)
        
        # 거래 로그 기록
        self.trade_log.append({
            'timestamp': timestamp,
            'action': 'EXIT',
            'direction': self.position.direction,
            'price': exit_price,
            'quantity': self.position.quantity,
            'pnl_percent': pnl * 100,
            'pnl_amount': profit_amount,
            'reason': reason,
            'holding_time': (timestamp - self.position.entry_time).total_seconds() / 3600  # 시간
        })
        
        print(f"   📉 포지션 청산: {pnl*100:+.2f}% @ {exit_price:.0f} ({reason})")
        
        # 상태 전환
        self.position = None
        self.state = BacktestState.WAITING_ENTRY
    
    def _resolve_conflicts(self, signals: List[TradingSignal]) -> TradingSignal:
        """관리 전략 신호 충돌 해결"""
        if not signals:
            # HOLD 신호 생성 (기본 생성자 형식에 맞춰)
            return TradingSignal(
                signal_type=SignalType.HOLD,
                timestamp=datetime.now(),
                price=0.0,
                metadata={"reason": "No signals"}
            )
        
        if len(signals) == 1:
            return signals[0]
        
        # 현재 조합의 충돌 해결 방식 적용
        resolution = self.current_combination.conflict_resolution
        
        if resolution == ConflictResolutionType.CONSERVATIVE:
            # 보수적 접근: CLOSE_POSITION 우선
            for signal in signals:
                if signal.signal_type == SignalType.CLOSE_POSITION:
                    return signal
            
            # 그 다음 HOLD
            for signal in signals:
                if signal.signal_type == SignalType.HOLD:
                    return signal
            
            # 그 외는 첫 번째 신호
            return signals[0]
        
        elif resolution == ConflictResolutionType.PRIORITY:
            # 우선순위 기반: priority 값이 높은 순
            # TradingSignal에 우선순위 정보가 없으므로 첫 번째 신호 반환
            return signals[0]
        
        else:  # MERGE
            # 신호 병합 (단순 구현)
            return signals[0]  # TODO: 더 정교한 병합 로직
    
    def _calculate_backtest_result(self, start_time: datetime, end_time: datetime,
                                  data_points: int) -> BacktestResult:
        """백테스트 결과 계산"""
        # 기본 성과 지표
        total_return = ((self.current_capital - self.initial_capital) / self.initial_capital) * 100
        total_trades = len([log for log in self.trade_log if log['action'] == 'EXIT'])
        
        winning_trades = len([log for log in self.trade_log 
                            if log['action'] == 'EXIT' and log['pnl_percent'] > 0])
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # 샤프 비율 (단순 계산)
        if total_trades > 0:
            returns = [log['pnl_percent'] for log in self.trade_log if log['action'] == 'EXIT']
            sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        # 전략 기여도 분석 (단순 구현)
        entry_contribution = {self.entry_strategy.__class__.__name__: total_return * 0.7}
        management_contribution = {}
        for mgmt_strategy in self.management_strategies:
            management_contribution[mgmt_strategy.__class__.__name__] = total_return * 0.3 / len(self.management_strategies)
        
        return BacktestResult(
            combination_id=self.current_combination.combination_id,
            combination_name=self.current_combination.name,
            total_return=total_return,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=self.max_drawdown * 100,
            entry_contribution=entry_contribution,
            management_contribution=management_contribution,
            trade_log=self.trade_log,
            position_log=self.position_log,
            backtest_start=start_time,
            backtest_end=end_time,
            data_points=data_points
        )
    
    def get_optimization_parameters(self) -> Dict[str, Dict[str, Any]]:
        """매개변수 최적화를 위한 파라미터 정의 반환"""
        return {
            # 리스크 관리 매개변수
            'risk_management': {
                'max_position_risk': {'min': 0.01, 'max': 0.05, 'type': 'float'},
                'stop_loss_percent': {'min': 0.02, 'max': 0.10, 'type': 'float'},
                'trailing_stop_percent': {'min': 0.01, 'max': 0.08, 'type': 'float'},
                'max_drawdown_limit': {'min': 0.10, 'max': 0.30, 'type': 'float'},
                'position_size_method': {
                    'options': ['fixed_risk', 'volatility_adjusted', 'kelly_criterion'], 
                    'type': 'categorical'
                }
            },
            # 진입 전략 매개변수 (RSI 예시)
            'entry_strategy': {
                'rsi_period': {'min': 10, 'max': 20, 'type': 'int'},
                'oversold': {'min': 20, 'max': 35, 'type': 'int'},
                'overbought': {'min': 65, 'max': 80, 'type': 'int'}
            },
            # 관리 전략 매개변수 (향후 확장)
            'management_strategy': {
                # 물타기 전략
                'averaging_down_threshold': {'min': -0.05, 'max': -0.15, 'type': 'float'},
                # 트레일링 스탑 전략
                'trailing_activation_profit': {'min': 0.03, 'max': 0.10, 'type': 'float'}
            }
        }
    
    def apply_optimization_parameters(self, params: Dict[str, Any]) -> None:
        """최적화된 매개변수 적용"""
        # 리스크 관리 매개변수 적용
        if 'risk_management' in params:
            self.set_risk_parameters(params['risk_management'])
        
        # 전략 매개변수 적용
        if 'entry_strategy' in params and self.entry_strategy:
            for param_name, param_value in params['entry_strategy'].items():
                if hasattr(self.entry_strategy, 'parameters'):
                    self.entry_strategy.parameters[param_name] = param_value
        
        if 'management_strategy' in params:
            for mgmt_strategy in self.management_strategies:
                for param_name, param_value in params['management_strategy'].items():
                    if hasattr(mgmt_strategy, 'parameters'):
                        if param_name in mgmt_strategy.parameters:
                            mgmt_strategy.parameters[param_name] = param_value
    
    def get_fitness_score(self, result: BacktestResult) -> float:
        """최적화를 위한 적합도 점수 계산"""
        # 다목적 최적화 점수 (수익률, 샤프비율, 최대낙폭, 승률 종합)
        
        # 기본 가중치 (조정 가능)
        weights = {
            'return': 0.3,      # 수익률
            'sharpe': 0.3,      # 샤프 비율
            'drawdown': 0.2,    # 최대 낙폭 (낮을수록 좋음)
            'win_rate': 0.2     # 승률
        }
        
        # 정규화된 점수 계산 (0-100 범위)
        return_score = max(0, min(100, result.total_return + 50))  # -50% ~ +50% → 0~100
        sharpe_score = max(0, min(100, (result.sharpe_ratio + 2) * 25))  # -2 ~ +2 → 0~100
        drawdown_score = max(0, 100 - result.max_drawdown)  # 낮을수록 좋음
        winrate_score = result.win_rate  # 이미 0-100 범위
        
        # 가중 평균 계산
        fitness = (
            weights['return'] * return_score +
            weights['sharpe'] * sharpe_score +
            weights['drawdown'] * drawdown_score +
            weights['win_rate'] * winrate_score
        )
        
        # 거래 수가 너무 적으면 패널티
        if result.total_trades < 5:
            fitness *= 0.5
        
        return fitness


# 사용 예시 및 테스트
if __name__ == "__main__":
    try:
        from .strategy_combination import CombinationManager
    except ImportError:
        from upbit_auto_trading.business_logic.strategy.strategy_combination import CombinationManager
    
    print("🧪 전략 조합 백테스트 엔진 테스트")
    
    # 조합 매니저에서 샘플 조합 가져오기
    manager = CombinationManager()
    samples = manager.get_sample_combinations()
    
    if samples:
        # 첫 번째 샘플 조합으로 테스트
        combination = samples[0]
        
        # 백테스트 엔진 생성 및 조합 로딩
        engine = StrategyCombinationBacktestEngine()
        engine.load_combination(combination)
        
        # 리스크 관리 매개변수 테스트 (최적화 시뮬레이션)
        print("\n🧬 매개변수 최적화 테스트:")
        test_risk_params = {
            'max_position_risk': 0.03,      # 3% 리스크로 증가
            'stop_loss_percent': 0.04,      # 4% 스탑로스
            'trailing_stop_percent': 0.025, # 2.5% 트레일링
            'max_drawdown_limit': 0.15      # 15% 최대 낙폭 제한
        }
        engine.set_risk_parameters(test_risk_params)
        
        # 전략 매개변수 최적화 예시
        optimization_params = engine.get_optimization_parameters()
        print(f"   📊 최적화 가능한 매개변수 그룹: {list(optimization_params.keys())}")
        
        # RSI 매개변수 조정 예시
        if hasattr(engine.entry_strategy, 'parameters'):
            original_params = engine.entry_strategy.parameters.copy()
            print(f"   📈 원본 RSI 매개변수: {original_params}")
            
            # 최적화된 매개변수 적용
            optimized_params = {
                'entry_strategy': {
                    'rsi_period': 12,    # 14 → 12로 변경
                    'oversold': 25,      # 30 → 25로 변경
                    'overbought': 75     # 70 → 75로 변경
                }
            }
            engine.apply_optimization_parameters(optimized_params)
            print(f"   🔧 최적화된 RSI 매개변수: {engine.entry_strategy.parameters}")
        
        # 샘플 시장 데이터 생성 (실제로는 DB에서 가져옴)
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='h')
        np.random.seed(42)
        
        # 더 현실적인 가격 데이터 생성 (실제 시장과 유사하게)
        n_points = len(dates)
        
        # 실제 시장과 유사한 가격 움직임 생성
        initial_price = 50000
        prices = [initial_price]
        
        for i in range(1, n_points):
            # 기본 트렌드 (매우 약한 상승)
            trend_component = 0.0001 * np.sin(i / 1000)
            
            # 랜덤 워크 (주가의 기본 움직임)
            random_component = np.random.normal(0, 0.02)  # 2% 표준편차
            
            # 사이클 패턴 (RSI 과매수/과매도 구간을 만들기 위해)
            cycle_component = 0.01 * np.sin(i / 50)  # 50시간 주기
            
            # 가격 변화율 계산
            price_change = trend_component + random_component + cycle_component
            
            # 새로운 가격 계산 (이전 가격 기준)
            new_price = prices[-1] * (1 + price_change)
            
            # 가격이 너무 극단적이 되지 않도록 제한
            new_price = max(10000, min(100000, new_price))
            prices.append(new_price)
        
        prices = np.array(prices)
        
        market_data = pd.DataFrame({
            'close': prices,
            'high': prices * (1 + np.abs(np.random.normal(0, 0.005, n_points))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.005, n_points))),
            'volume': np.random.uniform(1000, 10000, n_points)
        }, index=dates)
        
        # 백테스트 실행
        result = engine.run_backtest(market_data, initial_capital=1000000)
        
        # 적합도 점수 계산
        fitness_score = engine.get_fitness_score(result)
        
        print(f"\n📊 백테스트 결과 요약:")
        print(f"   조합: {result.combination_name}")
        print(f"   수익률: {result.total_return:.2f}%")
        print(f"   거래 수: {result.total_trades}")
        print(f"   승률: {result.win_rate:.1f}%")
        print(f"   샤프 비율: {result.sharpe_ratio:.2f}")
        print(f"   최대 낙폭: {result.max_drawdown:.2f}%")
        print(f"   🏆 적합도 점수: {fitness_score:.1f}/100")
        
        # 리스크 관리 통계
        stop_loss_trades = len([log for log in result.trade_log 
                               if log['action'] == 'EXIT' and 'STOP_LOSS' in log['reason']])
        trailing_stop_trades = len([log for log in result.trade_log 
                                   if log['action'] == 'EXIT' and 'TRAILING_STOP' in log['reason']])
        
        print(f"\n🛡️ 리스크 관리 통계:")
        print(f"   스탑로스 청산: {stop_loss_trades}회")
        print(f"   트레일링 스탑 청산: {trailing_stop_trades}회")
        print(f"   평균 보유시간: {np.mean([log['holding_time'] for log in result.trade_log if log['action'] == 'EXIT']):.1f}시간")
        
        print(f"\n✅ 백테스트 엔진 테스트 완료")
    else:
        print("❌ 테스트할 조합이 없습니다")
