"""
백테스트 실행기 모듈

이 모듈은 백테스팅을 실행하고 결과를 생성하는 기능을 제공합니다.
"""
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import uuid

from upbit_auto_trading.business_logic.strategy.strategy_interface import StrategyInterface
from upbit_auto_trading.data_layer.storage.market_data_storage import MarketDataStorage
from upbit_auto_trading.data_layer.processors.indicator_processor import IndicatorProcessor


class BacktestRunner:
    """
    백테스트 실행기 클래스
    
    이 클래스는 전략을 과거 데이터에 적용하여 백테스팅을 실행하고 결과를 생성합니다.
    """
    
    def __init__(self, strategy: StrategyInterface, config: Dict[str, Any]):
        """
        백테스트 실행기 초기화
        
        Args:
            strategy: 백테스팅에 사용할 전략
            config: 백테스트 설정 딕셔너리
                - symbol: 코인 심볼 (예: 'KRW-BTC')
                - timeframe: 시간대 (예: '1m', '5m', '1h', '1d')
                - start_date: 시작 날짜 (datetime 객체)
                - end_date: 종료 날짜 (datetime 객체)
                - initial_capital: 초기 자본 (KRW)
                - fee_rate: 수수료율 (예: 0.0005 = 0.05%)
                - slippage: 슬리피지 (예: 0.0002 = 0.02%)
        """
        self.logger = logging.getLogger(__name__)
        
        # 전략 및 설정 저장
        self.strategy = strategy
        self.config = config
        
        # 설정에서 필요한 값 추출
        self.symbol = config["symbol"]
        self.timeframe = config["timeframe"]
        self.start_date = config["start_date"]
        self.end_date = config["end_date"]
        self.initial_capital = config["initial_capital"]
        self.fee_rate = config.get("fee_rate", 0.0005)  # 기본값: 0.05%
        self.slippage = config.get("slippage", 0.0002)  # 기본값: 0.02%
        
        # 백테스트 상태 초기화
        self.current_capital = self.initial_capital
        self.position = None  # 현재 포지션 (None: 포지션 없음)
        self.trades = []  # 거래 내역
        
        self.logger.info(f"백테스트 실행기 초기화 완료: {self.symbol}, {self.timeframe}, {self.start_date} ~ {self.end_date}")
    
    def load_market_data(self) -> pd.DataFrame:
        """
        시장 데이터 로드
        
        Returns:
            OHLCV 데이터가 포함된 DataFrame
        """
        self.logger.info(f"시장 데이터 로드 중: {self.symbol}, {self.timeframe}, {self.start_date} ~ {self.end_date}")
        
        # 데이터 저장소에서 데이터 로드
        storage = MarketDataStorage()
        data = storage.load_market_data(
            self.symbol,
            self.timeframe,
            self.start_date,
            self.end_date
        )
        
        self.logger.info(f"시장 데이터 로드 완료: {len(data)}개 데이터 포인트")
        return data
    
    def prepare_data(self) -> pd.DataFrame:
        """
        백테스팅을 위한 데이터 준비
        
        Returns:
            기술적 지표가 추가된 DataFrame
        """
        self.logger.info("백테스팅을 위한 데이터 준비 중")
        
        # 시장 데이터 로드
        data = self.load_market_data()
        
        # 필요한 기술적 지표 계산
        indicators = self.strategy.get_required_indicators()
        processor = IndicatorProcessor()
        data_with_indicators = processor.calculate_indicators(data, indicators)
        
        self.logger.info(f"데이터 준비 완료: {len(data_with_indicators.columns)}개 컬럼")
        return data_with_indicators
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        매매 신호 생성
        
        Args:
            data: 기술적 지표가 포함된 DataFrame
            
        Returns:
            매매 신호가 추가된 DataFrame
        """
        self.logger.info("매매 신호 생성 중")
        
        # 전략을 사용하여 매매 신호 생성
        data_with_signals = self.strategy.generate_signals(data)
        
        # 신호 통계 계산
        buy_signals = (data_with_signals['signal'] == 1).sum()
        sell_signals = (data_with_signals['signal'] == -1).sum()
        hold_signals = (data_with_signals['signal'] == 0).sum()
        
        self.logger.info(f"매매 신호 생성 완료: 매수 {buy_signals}개, 매도 {sell_signals}개, 홀드 {hold_signals}개")
        return data_with_signals
    
    def execute_backtest(self) -> Dict[str, Any]:
        """
        백테스트 실행
        
        Returns:
            백테스트 결과 딕셔너리
                - trades: 거래 내역 목록
                - performance_metrics: 성과 지표
                - equity_curve: 자본 곡선 DataFrame
        """
        self.logger.info("백테스트 실행 시작")
        
        # 상태 초기화
        self.reset()
        
        # 데이터 준비
        data = self.prepare_data()
        
        # 매매 신호 생성
        data_with_signals = self.generate_signals(data)
        
        # 신호에 따라 거래 실행
        self.process_signals(data_with_signals)
        
        # 성과 지표 계산
        performance_metrics = self.calculate_performance_metrics()
        
        # 자본 곡선 생성
        equity_curve = self.generate_equity_curve(data_with_signals)
        
        # 결과 반환
        results = {
            "trades": self.trades,
            "performance_metrics": performance_metrics,
            "equity_curve": equity_curve
        }
        
        self.logger.info(f"백테스트 실행 완료: {len(self.trades)}개 거래, 최종 자본: {self.current_capital:,.0f} KRW")
        return results
    
    def process_signals(self, data: pd.DataFrame) -> None:
        """
        매매 신호에 따라 거래 실행
        
        Args:
            data: 매매 신호가 포함된 DataFrame
        """
        self.logger.info("매매 신호 처리 중")
        
        # 각 시점별로 신호 처리
        for timestamp, row in data.iterrows():
            signal = row['signal']
            price = row['close']
            
            # 매수 신호 (1)
            if signal == 1 and self.position is None:
                self.execute_buy_order(timestamp, price)
            
            # 매도 신호 (-1)
            elif signal == -1 and self.position is not None and self.position['side'] == 'long':
                self.execute_sell_order(timestamp, price)
        
        # 백테스트 종료 시 열린 포지션이 있으면 청산
        if self.position is not None:
            last_timestamp = data.index[-1]
            last_price = data.iloc[-1]['close']
            self.execute_sell_order(last_timestamp, last_price)
        
        self.logger.info(f"매매 신호 처리 완료: {len(self.trades)}개 거래 실행")
    
    def execute_buy_order(self, timestamp: datetime, price: float) -> None:
        """
        매수 주문 실행
        
        Args:
            timestamp: 주문 시간
            price: 주문 가격
        """
        # 슬리피지 적용
        execution_price = price * (1 + self.slippage)
        
        # 수수료 계산
        fee = self.current_capital * self.fee_rate
        
        # 매수 가능 금액 계산 (수수료 제외)
        buy_amount = self.current_capital - fee
        
        # 매수 수량 계산
        quantity = buy_amount / execution_price
        
        # 포지션 설정
        self.position = {
            'side': 'long',
            'entry_price': execution_price,
            'quantity': quantity,
            'entry_time': timestamp,
            'entry_fee': fee
        }
        
        # 자본 업데이트
        self.current_capital = 0  # 모든 자본을 사용하여 매수
        
        self.logger.debug(f"매수 주문 실행: {timestamp}, 가격: {execution_price:,.0f} KRW, 수량: {quantity:.8f}, 수수료: {fee:,.0f} KRW")
    
    def execute_sell_order(self, timestamp: datetime, price: float) -> None:
        """
        매도 주문 실행
        
        Args:
            timestamp: 주문 시간
            price: 주문 가격
        """
        if self.position is None:
            self.logger.warning("매도 주문 실패: 포지션 없음")
            return
        
        # 슬리피지 적용
        execution_price = price * (1 - self.slippage)
        
        # 매도 금액 계산
        sell_amount = self.position['quantity'] * execution_price
        
        # 수수료 계산
        fee = sell_amount * self.fee_rate
        
        # 순 매도 금액 계산 (수수료 제외)
        net_sell_amount = sell_amount - fee
        
        # 거래 정보 생성
        trade = {
            'id': str(uuid.uuid4()),
            'symbol': self.symbol,
            'entry_time': self.position['entry_time'],
            'entry_price': self.position['entry_price'],
            'exit_time': timestamp,
            'exit_price': execution_price,
            'quantity': self.position['quantity'],
            'side': self.position['side'],
            'entry_fee': self.position['entry_fee'],
            'exit_fee': fee
        }
        
        # 거래 지표 계산
        trade_metrics = self.calculate_trade_metrics(trade)
        trade.update(trade_metrics)
        
        # 거래 내역에 추가
        self.trades.append(trade)
        
        # 자본 업데이트
        self.current_capital = net_sell_amount
        
        # 포지션 초기화
        self.position = None
        
        self.logger.debug(f"매도 주문 실행: {timestamp}, 가격: {execution_price:,.0f} KRW, 수량: {trade['quantity']:.8f}, 수수료: {fee:,.0f} KRW, 손익: {trade['profit_loss']:,.0f} KRW ({trade['profit_loss_percent']:.2f}%)")
    
    def calculate_trade_metrics(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        거래 지표 계산
        
        Args:
            trade: 거래 정보 딕셔너리
            
        Returns:
            거래 지표 딕셔너리
        """
        # 매수 금액 계산
        entry_amount = trade['quantity'] * trade['entry_price']
        
        # 매도 금액 계산
        exit_amount = trade['quantity'] * trade['exit_price']
        
        # 총 수수료
        total_fee = trade['entry_fee'] + trade['exit_fee']
        
        # 손익 계산 (수수료 포함)
        profit_loss = exit_amount - entry_amount - total_fee
        
        # 손익률 계산
        profit_loss_percent = (profit_loss / entry_amount) * 100
        
        # 거래 기간 계산
        duration = trade['exit_time'] - trade['entry_time']
        
        return {
            'profit_loss': profit_loss,
            'profit_loss_percent': profit_loss_percent,
            'duration': duration,
            'total_fee': total_fee
        }
    
    def calculate_performance_metrics(self) -> Dict[str, Any]:
        """
        성과 지표 계산
        
        Returns:
            성과 지표 딕셔너리
        """
        self.logger.info("성과 지표 계산 중")
        
        # 거래가 없으면 기본 지표 반환
        if not self.trades:
            return {
                'total_return': 0.0,
                'total_return_percent': 0.0,
                'annualized_return': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'trades_count': 0,
                'avg_profit_per_trade': 0.0,
                'avg_profit_percent_per_trade': 0.0,
                'avg_holding_period': timedelta(0)
            }
        
        # 총 수익 계산
        total_profit_loss = sum(trade['profit_loss'] for trade in self.trades)
        total_return_percent = (self.current_capital / self.initial_capital - 1) * 100
        
        # 승률 계산
        winning_trades = [trade for trade in self.trades if trade['profit_loss'] > 0]
        win_rate = len(winning_trades) / len(self.trades) if self.trades else 0
        
        # 수익 요인 계산 (총 이익 / 총 손실)
        total_profit = sum(trade['profit_loss'] for trade in winning_trades)
        losing_trades = [trade for trade in self.trades if trade['profit_loss'] <= 0]
        total_loss = abs(sum(trade['profit_loss'] for trade in losing_trades)) if losing_trades else 1
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # 평균 수익 계산
        avg_profit_per_trade = total_profit_loss / len(self.trades)
        avg_profit_percent_per_trade = sum(trade['profit_loss_percent'] for trade in self.trades) / len(self.trades)
        
        # 평균 보유 기간 계산
        durations = [(trade['exit_time'] - trade['entry_time']) for trade in self.trades]
        total_duration = sum(durations, timedelta(0))
        avg_holding_period = total_duration / len(self.trades)
        
        # 최대 손실폭 계산 (MDD)
        # 자본 곡선이 필요하지만, 여기서는 간단히 거래 기반으로 계산
        cumulative_returns = [0]
        for trade in self.trades:
            cumulative_returns.append(cumulative_returns[-1] + trade['profit_loss_percent'])
        
        peak = 0
        max_drawdown = 0
        for i, ret in enumerate(cumulative_returns):
            if ret > peak:
                peak = ret
            drawdown = peak - ret
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # 연간 수익률 계산
        total_days = (self.end_date - self.start_date).days
        if total_days > 0:
            annualized_return = ((1 + total_return_percent / 100) ** (365 / total_days) - 1) * 100
        else:
            annualized_return = 0
        
        # 샤프 비율 계산 (간단한 버전)
        returns = [trade['profit_loss_percent'] for trade in self.trades]
        if len(returns) > 1:
            mean_return = np.mean(returns)
            std_return = np.std(returns, ddof=1)
            sharpe_ratio = mean_return / std_return * np.sqrt(252) if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        # 소티노 비율 계산 (간단한 버전)
        negative_returns = [r for r in returns if r < 0]
        if negative_returns:
            downside_std = np.std(negative_returns, ddof=1)
            sortino_ratio = np.mean(returns) / downside_std * np.sqrt(252) if downside_std > 0 else 0
        else:
            sortino_ratio = float('inf') if np.mean(returns) > 0 else 0
        
        metrics = {
            'total_return': total_profit_loss,
            'total_return_percent': total_return_percent,
            'annualized_return': annualized_return,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate * 100,  # 백분율로 변환
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'trades_count': len(self.trades),
            'avg_profit_per_trade': avg_profit_per_trade,
            'avg_profit_percent_per_trade': avg_profit_percent_per_trade,
            'avg_holding_period': avg_holding_period
        }
        
        self.logger.info(f"성과 지표 계산 완료: 총 수익률 {total_return_percent:.2f}%, 승률 {win_rate*100:.2f}%, 최대 손실폭 {max_drawdown:.2f}%")
        return metrics
    
    def generate_equity_curve(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        자본 곡선 생성
        
        Args:
            data: 매매 신호가 포함된 DataFrame
            
        Returns:
            자본 곡선이 포함된 DataFrame
        """
        self.logger.info("자본 곡선 생성 중")
        
        # 결과 DataFrame 초기화
        equity_curve = data[['close']].copy()
        equity_curve['equity'] = self.initial_capital
        
        # 거래가 없으면 초기 자본으로 채운 곡선 반환
        if not self.trades:
            return equity_curve
        
        # 각 거래의 영향을 자본 곡선에 반영
        current_equity = self.initial_capital
        position = None
        
        for timestamp, row in equity_curve.iterrows():
            # 해당 시점에 매수한 거래 찾기
            for trade in self.trades:
                if trade['entry_time'] == timestamp:
                    position = {
                        'entry_price': trade['entry_price'],
                        'quantity': trade['quantity'],
                        'entry_fee': trade['entry_fee']
                    }
                    current_equity = 0  # 모든 자본을 사용하여 매수
                    break
            
            # 해당 시점에 매도한 거래 찾기
            for trade in self.trades:
                if trade['exit_time'] == timestamp:
                    # 매도 금액 계산
                    sell_amount = position['quantity'] * trade['exit_price']
                    
                    # 수수료 계산
                    exit_fee = sell_amount * self.fee_rate
                    
                    # 순 매도 금액 계산 (수수료 제외)
                    current_equity = sell_amount - exit_fee
                    position = None
                    break
            
            # 포지션이 있는 경우 현재 가치 계산
            if position is not None:
                market_value = position['quantity'] * row['close']
                current_equity = market_value  # 단순화를 위해 수수료는 고려하지 않음
            
            # 자본 곡선 업데이트
            equity_curve.at[timestamp, 'equity'] = current_equity
        
        self.logger.info("자본 곡선 생성 완료")
        return equity_curve
    
    def reset(self) -> None:
        """
        백테스트 상태 초기화
        """
        self.logger.info("백테스트 상태 초기화")
        self.current_capital = self.initial_capital
        self.position = None
        self.trades = []