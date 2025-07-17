"""
백테스트 결과 분석기 모듈

이 모듈은 백테스트 결과를 분석하고 시각화하는 기능을 제공합니다.
"""
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# matplotlib 및 seaborn 임포트 시도
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import seaborn as sns
    from matplotlib.figure import Figure
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    # 시각화 라이브러리가 없을 때 사용할 Figure 대체 클래스
    class DummyFigure:
        """시각화 라이브러리가 없을 때 사용하는 더미 Figure 클래스"""
        pass
    Figure = DummyFigure


class BacktestAnalyzer:
    """
    백테스트 결과 분석기 클래스
    
    이 클래스는 백테스트 결과를 분석하고 시각화하는 기능을 제공합니다.
    """
    
    def __init__(self, results: Dict[str, Any]):
        """
        백테스트 결과 분석기 초기화
        
        Args:
            results: 백테스트 결과 딕셔너리
                - trades: 거래 내역 목록
                - performance_metrics: 성과 지표
                - equity_curve: 자본 곡선 DataFrame
                - config: 백테스트 설정
                - strategy: 백테스트에 사용된 전략
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("백테스트 결과 분석기 초기화")
        
        # 백테스트 결과 저장
        self.results = results
        self.trades = results.get('trades', [])
        self.performance_metrics = results.get('performance_metrics', {})
        self.equity_curve = results.get('equity_curve', pd.DataFrame())
        self.config = results.get('config', {})
        self.strategy = results.get('strategy', None)
        
        # 스타일 설정
        plt.style.use('seaborn-v0_8-darkgrid')
        
        self.logger.info(f"백테스트 결과 분석기 초기화 완료: {len(self.trades)}개 거래, {len(self.equity_curve)}개 데이터 포인트")
    
    def calculate_advanced_metrics(self) -> Dict[str, Any]:
        """
        고급 성과 지표 계산
        
        Returns:
            고급 성과 지표 딕셔너리
        """
        self.logger.info("고급 성과 지표 계산 중")
        
        # 거래가 없으면 기본 지표 반환
        if not self.trades:
            return {
                'calmar_ratio': 0.0,
                'ulcer_index': 0.0,
                'profit_to_max_drawdown': 0.0,
                'avg_profit_to_avg_loss': 0.0,
                'win_loss_ratio': 0.0,
                'expectancy': 0.0,
                'system_quality_number': 0.0,
                'recovery_factor': 0.0,
                'risk_of_ruin': 0.0
            }
        
        # 자본 곡선이 없으면 계산 불가
        if self.equity_curve.empty or 'equity' not in self.equity_curve.columns:
            self.logger.warning("자본 곡선이 없어 일부 지표 계산이 불가능합니다.")
            return {
                'calmar_ratio': 0.0,
                'ulcer_index': 0.0,
                'profit_to_max_drawdown': 0.0,
                'avg_profit_to_avg_loss': 0.0,
                'win_loss_ratio': 0.0,
                'expectancy': 0.0,
                'system_quality_number': 0.0,
                'recovery_factor': 0.0,
                'risk_of_ruin': 0.0
            }
        
        # 칼마 비율 계산 (연간 수익률 / 최대 손실폭)
        annualized_return = self.performance_metrics.get('annualized_return', 0.0)
        max_drawdown = self.performance_metrics.get('max_drawdown', 1.0)  # 0으로 나누기 방지
        calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0.0
        
        # 울서 지수 계산 (자본 곡선의 하락 정도를 측정)
        equity_series = self.equity_curve['equity']
        rolling_max = equity_series.expanding().max()
        drawdowns = (equity_series - rolling_max) / rolling_max * 100
        squared_drawdowns = drawdowns ** 2
        ulcer_index = np.sqrt(squared_drawdowns.mean())
        
        # 수익률 대 최대 손실폭 비율
        total_return_percent = self.performance_metrics.get('total_return_percent', 0.0)
        profit_to_max_drawdown = total_return_percent / max_drawdown if max_drawdown > 0 else 0.0
        
        # 평균 이익 대 평균 손실 비율
        winning_trades = [trade for trade in self.trades if trade.get('profit_loss', 0) > 0]
        losing_trades = [trade for trade in self.trades if trade.get('profit_loss', 0) <= 0]
        
        avg_profit = np.mean([trade.get('profit_loss', 0) for trade in winning_trades]) if winning_trades else 0
        avg_loss = abs(np.mean([trade.get('profit_loss', 0) for trade in losing_trades])) if losing_trades else 1  # 0으로 나누기 방지
        
        avg_profit_to_avg_loss = avg_profit / avg_loss if avg_loss > 0 else 0.0
        
        # 승률 대 패률 비율
        win_rate = self.performance_metrics.get('win_rate', 0.0) / 100  # 백분율에서 비율로 변환
        loss_rate = 1 - win_rate
        win_loss_ratio = win_rate / loss_rate if loss_rate > 0 else float('inf')
        
        # 기대값 계산 (승률 * 평균 이익 - 패률 * 평균 손실)
        expectancy = (win_rate * avg_profit) - (loss_rate * avg_loss)
        
        # 시스템 품질 지수 (SQN)
        trades_count = len(self.trades)
        if trades_count > 1:
            returns = [trade.get('profit_loss_percent', 0) for trade in self.trades]
            mean_return = np.mean(returns)
            std_return = np.std(returns, ddof=1) if len(returns) > 1 else 1  # 0으로 나누기 방지
            system_quality_number = mean_return * np.sqrt(trades_count) / std_return if std_return > 0 else 0.0
        else:
            system_quality_number = 0.0
        
        # 회복 요인 (총 수익률 / 최대 손실폭)
        recovery_factor = total_return_percent / max_drawdown if max_drawdown > 0 else 0.0
        
        # 파산 위험 (간단한 계산)
        # 승률과 손익비를 기반으로 한 파산 위험 추정
        if win_rate > 0 and avg_profit_to_avg_loss > 0:
            risk_of_ruin = (1 - (win_rate * avg_profit_to_avg_loss - loss_rate) / (win_rate * avg_profit_to_avg_loss + loss_rate)) ** trades_count
            risk_of_ruin = max(0, min(1, risk_of_ruin))  # 0-1 범위로 제한
        else:
            risk_of_ruin = 1.0
        
        metrics = {
            'calmar_ratio': calmar_ratio,
            'ulcer_index': ulcer_index,
            'profit_to_max_drawdown': profit_to_max_drawdown,
            'avg_profit_to_avg_loss': avg_profit_to_avg_loss,
            'win_loss_ratio': win_loss_ratio,
            'expectancy': expectancy,
            'system_quality_number': system_quality_number,
            'recovery_factor': recovery_factor,
            'risk_of_ruin': risk_of_ruin
        }
        
        self.logger.info(f"고급 성과 지표 계산 완료: 칼마 비율 {calmar_ratio:.2f}, 울서 지수 {ulcer_index:.2f}, SQN {system_quality_number:.2f}")
        return metrics
    
    def analyze_trades(self) -> Dict[str, Any]:
        """
        거래 내역 분석
        
        Returns:
            거래 분석 결과 딕셔너리
        """
        self.logger.info("거래 내역 분석 중")
        
        # 거래가 없으면 기본 분석 결과 반환
        if not self.trades:
            return {
                'profitable_trades': 0,
                'losing_trades': 0,
                'avg_profit_trade': 0.0,
                'avg_loss_trade': 0.0,
                'max_profit_trade': None,
                'max_loss_trade': None,
                'avg_holding_period_profit': timedelta(0),
                'avg_holding_period_loss': timedelta(0),
                'profit_by_day_of_week': {},
                'profit_by_hour': {},
                'consecutive_wins': 0,
                'consecutive_losses': 0,
                'max_consecutive_wins': 0,
                'max_consecutive_losses': 0
            }
        
        # 수익/손실 거래 분류
        profitable_trades = [trade for trade in self.trades if trade.get('profit_loss', 0) > 0]
        losing_trades = [trade for trade in self.trades if trade.get('profit_loss', 0) <= 0]
        
        # 평균 수익/손실 계산
        avg_profit_trade = np.mean([trade.get('profit_loss', 0) for trade in profitable_trades]) if profitable_trades else 0
        avg_loss_trade = np.mean([trade.get('profit_loss', 0) for trade in losing_trades]) if losing_trades else 0
        
        # 최대 수익/손실 거래 찾기
        max_profit_trade = max(self.trades, key=lambda x: x.get('profit_loss', 0)) if self.trades else None
        max_loss_trade = min(self.trades, key=lambda x: x.get('profit_loss', 0)) if self.trades else None
        
        # 평균 보유 기간 계산
        avg_holding_period_profit = np.mean([trade.get('duration', timedelta(0)) for trade in profitable_trades]) if profitable_trades else timedelta(0)
        avg_holding_period_loss = np.mean([trade.get('duration', timedelta(0)) for trade in losing_trades]) if losing_trades else timedelta(0)
        
        # 요일별 수익 분석
        profit_by_day_of_week = {}
        for day in range(7):
            day_trades = [trade for trade in self.trades if trade.get('exit_time').weekday() == day]
            if day_trades:
                profit_by_day_of_week[day] = sum(trade.get('profit_loss', 0) for trade in day_trades)
            else:
                profit_by_day_of_week[day] = 0
        
        # 시간별 수익 분석
        profit_by_hour = {}
        for hour in range(24):
            hour_trades = [trade for trade in self.trades if trade.get('exit_time').hour == hour]
            if hour_trades:
                profit_by_hour[hour] = sum(trade.get('profit_loss', 0) for trade in hour_trades)
            else:
                profit_by_hour[hour] = 0
        
        # 연속 승/패 분석
        current_streak = 0
        max_win_streak = 0
        max_loss_streak = 0
        
        # 거래를 시간순으로 정렬
        sorted_trades = sorted(self.trades, key=lambda x: x.get('exit_time'))
        
        for i, trade in enumerate(sorted_trades):
            if trade.get('profit_loss', 0) > 0:
                if current_streak > 0:
                    current_streak += 1
                else:
                    current_streak = 1
                max_win_streak = max(max_win_streak, current_streak)
            else:
                if current_streak < 0:
                    current_streak -= 1
                else:
                    current_streak = -1
                max_loss_streak = max(max_loss_streak, abs(current_streak))
        
        # 현재 연속 승/패
        consecutive_wins = current_streak if current_streak > 0 else 0
        consecutive_losses = abs(current_streak) if current_streak < 0 else 0
        
        analysis = {
            'profitable_trades': len(profitable_trades),
            'losing_trades': len(losing_trades),
            'avg_profit_trade': avg_profit_trade,
            'avg_loss_trade': avg_loss_trade,
            'max_profit_trade': max_profit_trade,
            'max_loss_trade': max_loss_trade,
            'avg_holding_period_profit': avg_holding_period_profit,
            'avg_holding_period_loss': avg_holding_period_loss,
            'profit_by_day_of_week': profit_by_day_of_week,
            'profit_by_hour': profit_by_hour,
            'consecutive_wins': consecutive_wins,
            'consecutive_losses': consecutive_losses,
            'max_consecutive_wins': max_win_streak,
            'max_consecutive_losses': max_loss_streak
        }
        
        self.logger.info(f"거래 내역 분석 완료: 수익 거래 {len(profitable_trades)}개, 손실 거래 {len(losing_trades)}개")
        return analysis
    
    def analyze_drawdowns(self) -> pd.DataFrame:
        """
        손실폭(Drawdown) 분석
        
        Returns:
            손실폭 분석 결과 DataFrame
        """
        self.logger.info("손실폭 분석 중")
        
        # 자본 곡선이 없으면 빈 DataFrame 반환
        if self.equity_curve.empty or 'equity' not in self.equity_curve.columns:
            self.logger.warning("자본 곡선이 없어 손실폭 분석이 불가능합니다.")
            return pd.DataFrame(columns=['drawdown_percent', 'duration', 'start_date', 'end_date', 'recovery_date'])
        
        # 자본 곡선에서 손실폭 계산
        equity = self.equity_curve['equity']
        
        # 누적 최대값 계산
        running_max = equity.expanding().max()
        
        # 손실폭 계산 (%)
        drawdown = (equity - running_max) / running_max * 100
        
        # 손실폭 시작점 식별
        is_drawdown_start = (drawdown < 0) & (drawdown.shift(1) >= 0)
        
        # 손실폭 종료점 식별 (다음 최고점 도달)
        is_recovery = (drawdown == 0) & (drawdown.shift(1) < 0)
        
        # 손실폭 시작 및 종료 시간
        drawdown_starts = self.equity_curve.index[is_drawdown_start]
        recoveries = self.equity_curve.index[is_recovery]
        
        # 손실폭 목록 생성
        drawdowns = []
        
        for i, start_date in enumerate(drawdown_starts):
            # 시작 이후의 회복 시점 찾기
            future_recoveries = recoveries[recoveries > start_date]
            
            if len(future_recoveries) > 0:
                recovery_date = future_recoveries[0]
            else:
                # 회복 시점이 없으면 마지막 시점으로 설정
                recovery_date = self.equity_curve.index[-1]
            
            # 시작 시점부터 회복 시점까지의 손실폭
            dd_period = drawdown[start_date:recovery_date]
            
            # 최대 손실폭 및 발생 시점
            max_dd = dd_period.min()
            max_dd_date = dd_period.idxmin()
            
            # 손실폭 기간
            duration = recovery_date - start_date
            
            # 손실폭 정보 저장
            if max_dd < 0:  # 실제 손실폭만 저장
                drawdowns.append({
                    'drawdown_percent': max_dd,
                    'duration': duration,
                    'start_date': start_date,
                    'end_date': max_dd_date,
                    'recovery_date': recovery_date
                })
        
        # DataFrame으로 변환
        if drawdowns:
            df_drawdowns = pd.DataFrame(drawdowns)
            # 손실폭 크기 순으로 정렬
            df_drawdowns = df_drawdowns.sort_values('drawdown_percent')
        else:
            df_drawdowns = pd.DataFrame(columns=['drawdown_percent', 'duration', 'start_date', 'end_date', 'recovery_date'])
        
        self.logger.info(f"손실폭 분석 완료: {len(df_drawdowns)}개 손실폭 식별")
        return df_drawdowns
    
    def analyze_monthly_returns(self) -> pd.DataFrame:
        """
        월별 수익률 분석
        
        Returns:
            월별 수익률 분석 결과 DataFrame
        """
        self.logger.info("월별 수익률 분석 중")
        
        # 자본 곡선이 없으면 빈 DataFrame 반환
        if self.equity_curve.empty or 'equity' not in self.equity_curve.columns:
            self.logger.warning("자본 곡선이 없어 월별 수익률 분석이 불가능합니다.")
            return pd.DataFrame(columns=['year', 'month', 'return_percent'])
        
        # 자본 곡선에서 월별 수익률 계산
        equity = self.equity_curve['equity']
        
        # 월별 첫 값과 마지막 값 추출
        monthly_equity = equity.resample('M').agg(['first', 'last'])
        
        # 월별 수익률 계산
        monthly_returns = (monthly_equity['last'] / monthly_equity['first'] - 1) * 100
        
        # 연도와 월 추출
        monthly_returns = monthly_returns.reset_index()
        monthly_returns['year'] = monthly_returns['timestamp'].dt.year
        monthly_returns['month'] = monthly_returns['timestamp'].dt.month
        monthly_returns = monthly_returns.rename(columns={0: 'return_percent'})
        
        # 필요한 컬럼만 선택
        result = monthly_returns[['year', 'month', 'return_percent']]
        
        self.logger.info(f"월별 수익률 분석 완료: {len(result)}개월 분석")
        return result
    
    def plot_equity_curve(self) -> Figure:
        """
        자본 곡선 시각화
        
        Returns:
            matplotlib Figure 객체
        """
        self.logger.info("자본 곡선 시각화 중")
        
        # 자본 곡선이 없으면 빈 Figure 반환
        if self.equity_curve.empty or 'equity' not in self.equity_curve.columns:
            self.logger.warning("자본 곡선이 없어 시각화가 불가능합니다.")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "자본 곡선 데이터가 없습니다.", ha='center', va='center')
            return fig
        
        # 그림 생성
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 자본 곡선 그리기
        ax.plot(self.equity_curve.index, self.equity_curve['equity'], label='자본금', color='#1f77b4', linewidth=2)
        
        # 매수/매도 시점 표시
        if self.trades:
            # 매수 시점
            entry_times = [trade['entry_time'] for trade in self.trades]
            entry_values = [self.equity_curve.loc[self.equity_curve.index.get_indexer([t], method='nearest')[0], 'equity'] for t in entry_times]
            ax.scatter(entry_times, entry_values, color='green', marker='^', s=100, label='매수', alpha=0.7)
            
            # 매도 시점
            exit_times = [trade['exit_time'] for trade in self.trades]
            exit_values = [self.equity_curve.loc[self.equity_curve.index.get_indexer([t], method='nearest')[0], 'equity'] for t in exit_times]
            ax.scatter(exit_times, exit_values, color='red', marker='v', s=100, label='매도', alpha=0.7)
        
        # 그래프 스타일 설정
        ax.set_title('백테스트 자본 곡선', fontsize=16)
        ax.set_xlabel('날짜', fontsize=12)
        ax.set_ylabel('자본금 (KRW)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left')
        
        # x축 날짜 포맷 설정
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate()
        
        # 수익률 표시
        initial_capital = self.equity_curve['equity'].iloc[0]
        final_capital = self.equity_curve['equity'].iloc[-1]
        total_return_percent = (final_capital / initial_capital - 1) * 100
        
        ax.text(0.02, 0.95, f'초기 자본: {initial_capital:,.0f} KRW\n'
                           f'최종 자본: {final_capital:,.0f} KRW\n'
                           f'총 수익률: {total_return_percent:.2f}%',
                transform=ax.transAxes, fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        self.logger.info("자본 곡선 시각화 완료")
        return fig
    
    def plot_drawdowns(self) -> Figure:
        """
        손실폭 시각화
        
        Returns:
            matplotlib Figure 객체
        """
        self.logger.info("손실폭 시각화 중")
        
        # 자본 곡선이 없으면 빈 Figure 반환
        if self.equity_curve.empty or 'equity' not in self.equity_curve.columns:
            self.logger.warning("자본 곡선이 없어 손실폭 시각화가 불가능합니다.")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "자본 곡선 데이터가 없습니다.", ha='center', va='center')
            return fig
        
        # 그림 생성
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})
        
        # 자본 곡선 그리기
        ax1.plot(self.equity_curve.index, self.equity_curve['equity'], label='자본금', color='#1f77b4', linewidth=2)
        
        # 누적 최대값 계산
        equity = self.equity_curve['equity']
        running_max = equity.expanding().max()
        ax1.plot(self.equity_curve.index, running_max, label='최고점', color='green', linestyle='--', alpha=0.7)
        
        # 손실폭 분석 결과 가져오기
        drawdowns_df = self.analyze_drawdowns()
        
        # 주요 손실폭 표시
        if not drawdowns_df.empty:
            # 상위 3개 손실폭만 표시
            top_drawdowns = drawdowns_df.head(3)
            
            for i, (_, dd) in enumerate(top_drawdowns.iterrows()):
                # 손실폭 영역 표시
                ax1.axvspan(dd['start_date'], dd['recovery_date'], alpha=0.2, color=f'C{i+1}')
                
                # 손실폭 레이블 추가
                ax1.text(dd['end_date'], self.equity_curve.loc[self.equity_curve.index.get_indexer([dd['end_date']], method='nearest')[0], 'equity'],
                        f"DD: {dd['drawdown_percent']:.2f}%", ha='center', va='bottom', fontsize=10,
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 손실폭 그래프 그리기
        drawdown = (equity - running_max) / running_max * 100
        ax2.fill_between(self.equity_curve.index, drawdown, 0, color='red', alpha=0.3)
        ax2.plot(self.equity_curve.index, drawdown, color='red', linewidth=1)
        
        # 그래프 스타일 설정
        ax1.set_title('백테스트 자본 곡선 및 손실폭', fontsize=16)
        ax1.set_ylabel('자본금 (KRW)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper left')
        
        ax2.set_title('손실폭 (%)', fontsize=14)
        ax2.set_xlabel('날짜', fontsize=12)
        ax2.set_ylabel('손실폭 (%)', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # x축 날짜 포맷 설정
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate()
        
        # 최대 손실폭 표시
        max_dd = self.performance_metrics.get('max_drawdown', 0.0)
        ax2.axhline(y=-max_dd, color='black', linestyle='--', alpha=0.7)
        ax2.text(self.equity_curve.index[0], -max_dd, f'최대 손실폭: {max_dd:.2f}%', fontsize=10, va='bottom')
        
        plt.tight_layout()
        
        self.logger.info("손실폭 시각화 완료")
        return fig
    
    def plot_monthly_returns(self) -> Figure:
        """
        월별 수익률 시각화
        
        Returns:
            matplotlib Figure 객체
        """
        self.logger.info("월별 수익률 시각화 중")
        
        # 월별 수익률 분석 결과 가져오기
        monthly_returns = self.analyze_monthly_returns()
        
        # 월별 수익률이 없으면 빈 Figure 반환
        if monthly_returns.empty:
            self.logger.warning("월별 수익률 데이터가 없어 시각화가 불가능합니다.")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "월별 수익률 데이터가 없습니다.", ha='center', va='center')
            return fig
        
        # 그림 생성
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 월 이름 매핑
        month_names = {
            1: '1월', 2: '2월', 3: '3월', 4: '4월', 5: '5월', 6: '6월',
            7: '7월', 8: '8월', 9: '9월', 10: '10월', 11: '11월', 12: '12월'
        }
        
        # 연도별로 그룹화
        years = monthly_returns['year'].unique()
        
        # 각 연도별 월별 수익률 그래프 그리기
        bar_width = 0.8 / len(years)
        
        for i, year in enumerate(sorted(years)):
            year_data = monthly_returns[monthly_returns['year'] == year]
            
            # 월별 수익률 데이터 준비
            months = year_data['month'].values
            returns = year_data['return_percent'].values
            
            # 막대 위치 계산
            x = np.arange(len(month_names))
            positions = x - 0.4 + (i + 0.5) * bar_width
            
            # 월별 수익률 막대 그래프 그리기
            bars = ax.bar(positions[months-1], returns, bar_width, label=str(year))
            
            # 막대 색상 설정 (수익/손실에 따라)
            for j, bar in enumerate(bars):
                if returns[j] >= 0:
                    bar.set_color('green')
                else:
                    bar.set_color('red')
        
        # 그래프 스타일 설정
        ax.set_title('월별 수익률', fontsize=16)
        ax.set_xlabel('월', fontsize=12)
        ax.set_ylabel('수익률 (%)', fontsize=12)
        ax.set_xticks(np.arange(len(month_names)))
        ax.set_xticklabels(list(month_names.values()))
        ax.grid(True, alpha=0.3, axis='y')
        
        # 0% 라인 추가
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # 범례 추가
        if len(years) > 1:
            ax.legend(title='연도')
        
        plt.tight_layout()
        
        self.logger.info("월별 수익률 시각화 완료")
        return fig
    
    def plot_trade_analysis(self) -> Figure:
        """
        거래 분석 시각화
        
        Returns:
            matplotlib Figure 객체
        """
        self.logger.info("거래 분석 시각화 중")
        
        # 거래가 없으면 빈 Figure 반환
        if not self.trades:
            self.logger.warning("거래 데이터가 없어 시각화가 불가능합니다.")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "거래 데이터가 없습니다.", ha='center', va='center')
            return fig
        
        # 거래 분석 결과 가져오기
        trade_analysis = self.analyze_trades()
        
        # 그림 생성 (2x2 서브플롯)
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. 수익/손실 거래 비율 파이 차트
        profitable_trades = trade_analysis['profitable_trades']
        losing_trades = trade_analysis['losing_trades']
        
        ax1.pie([profitable_trades, losing_trades], labels=['수익 거래', '손실 거래'],
                autopct='%1.1f%%', startangle=90, colors=['green', 'red'])
        ax1.set_title('수익/손실 거래 비율', fontsize=14)
        
        # 2. 요일별 수익 막대 그래프
        day_names = ['월', '화', '수', '목', '금', '토', '일']
        days = list(range(7))
        profits = [trade_analysis['profit_by_day_of_week'].get(day, 0) for day in days]
        
        bars = ax2.bar(days, profits)
        
        # 막대 색상 설정 (수익/손실에 따라)
        for i, bar in enumerate(bars):
            if profits[i] >= 0:
                bar.set_color('green')
            else:
                bar.set_color('red')
        
        ax2.set_title('요일별 수익', fontsize=14)
        ax2.set_xlabel('요일', fontsize=12)
        ax2.set_ylabel('수익 (KRW)', fontsize=12)
        ax2.set_xticks(days)
        ax2.set_xticklabels(day_names)
        ax2.grid(True, alpha=0.3, axis='y')
        
        # 3. 시간별 수익 막대 그래프
        hours = list(range(24))
        profits = [trade_analysis['profit_by_hour'].get(hour, 0) for hour in hours]
        
        bars = ax3.bar(hours, profits)
        
        # 막대 색상 설정 (수익/손실에 따라)
        for i, bar in enumerate(bars):
            if profits[i] >= 0:
                bar.set_color('green')
            else:
                bar.set_color('red')
        
        ax3.set_title('시간별 수익', fontsize=14)
        ax3.set_xlabel('시간', fontsize=12)
        ax3.set_ylabel('수익 (KRW)', fontsize=12)
        ax3.set_xticks(hours)
        ax3.set_xticklabels([f'{h}시' for h in hours])
        ax3.grid(True, alpha=0.3, axis='y')
        
        # 4. 거래별 수익/손실 분포 히스토그램
        profits = [trade.get('profit_loss', 0) for trade in self.trades]
        
        ax4.hist(profits, bins=20, color='skyblue', edgecolor='black')
        ax4.axvline(x=0, color='black', linestyle='--', alpha=0.7)
        ax4.set_title('거래별 수익/손실 분포', fontsize=14)
        ax4.set_xlabel('수익/손실 (KRW)', fontsize=12)
        ax4.set_ylabel('거래 수', fontsize=12)
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        self.logger.info("거래 분석 시각화 완료")
        return fig
    
    def generate_report(self) -> Dict[str, Any]:
        """
        백테스트 결과 보고서 생성
        
        Returns:
            보고서 딕셔너리
        """
        self.logger.info("백테스트 결과 보고서 생성 중")
        
        # 백테스트 설정 요약
        summary = {
            'symbol': self.config.get('symbol', ''),
            'timeframe': self.config.get('timeframe', ''),
            'start_date': self.config.get('start_date', ''),
            'end_date': self.config.get('end_date', ''),
            'initial_capital': self.config.get('initial_capital', 0.0),
            'strategy_name': self.strategy.__class__.__name__ if self.strategy else '',
            'strategy_params': self.strategy.params if self.strategy else {}
        }
        
        # 고급 성과 지표 계산
        advanced_metrics = self.calculate_advanced_metrics()
        
        # 거래 분석
        trade_analysis = self.analyze_trades()
        
        # 손실폭 분석
        drawdowns = self.analyze_drawdowns()
        
        # 월별 수익률 분석
        monthly_returns = self.analyze_monthly_returns()
        
        # 시각화
        figures = {
            'equity_curve': self.plot_equity_curve(),
            'drawdowns': self.plot_drawdowns(),
            'monthly_returns': self.plot_monthly_returns(),
            'trade_analysis': self.plot_trade_analysis()
        }
        
        # 보고서 생성
        report = {
            'summary': summary,
            'performance_metrics': self.performance_metrics,
            'advanced_metrics': advanced_metrics,
            'trade_analysis': trade_analysis,
            'drawdowns': drawdowns,
            'monthly_returns': monthly_returns,
            'figures': figures
        }
        
        self.logger.info("백테스트 결과 보고서 생성 완료")
        return report