#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
백테스트 보고서 생성기

역할:
- 데이터베이스 백테스트 결과를 종합적인 보고서로 변환
- 상세한 성과 지표 계산
- 시각적 보고서 양식 생성
- 거래 이력 분석
"""

import os
import sys
import sqlite3
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# 프로젝트 루트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)


@dataclass
class BacktestReportData:
    """백테스트 보고서 데이터"""
    # 기본 정보
    backtest_id: str
    symbol: str
    start_date: str
    end_date: str
    timeframe: str
    initial_capital: float
    trading_fee_rate: float
    slippage_rate: float
    
    # 전략 정보
    combination_name: str
    entry_strategy: str
    management_strategies: List[str]
    combination_rule: str
    
    # 성과 지표
    final_value: float
    total_pnl: float
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    
    # 거래 통계
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # 고급 지표
    cagr: float = 0.0
    profit_factor: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    sortino_ratio: float = 0.0
    max_dd_duration: int = 0
    max_losing_streak: int = 0
    avg_holding_period: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    
    # 거래 이력
    trade_history: List[Dict[str, Any]] = None


class BacktestReportGenerator:
    """백테스트 보고서 생성기"""
    
    def __init__(self, db_path: str = "data/upbit_auto_trading.sqlite3"):
        self.db_path = db_path
    
    def get_connection(self) -> sqlite3.Connection:
        """데이터베이스 연결 반환"""
        return sqlite3.connect(self.db_path)
    
    def generate_report(self, backtest_result_id: str) -> str:
        """백테스트 보고서 생성"""
        # 1. 데이터 수집
        report_data = self._collect_report_data(backtest_result_id)
        
        # 2. 고급 지표 계산
        self._calculate_advanced_metrics(report_data)
        
        # 3. 보고서 텍스트 생성
        report_text = self._generate_report_text(report_data)
        
        return report_text
    
    def _collect_report_data(self, backtest_result_id: str) -> BacktestReportData:
        """백테스트 데이터 수집"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 백테스트 기본 정보 조회
            cursor.execute("""
                SELECT br.symbol, br.start_date, br.end_date, br.timeframe,
                       br.initial_capital, br.trading_fee_rate, br.slippage_rate,
                       br.total_return, br.total_trades, br.winning_trades, br.losing_trades,
                       br.win_rate, br.sharpe_ratio, br.max_drawdown,
                       sc.name as combination_name, sc.combination_id
                FROM backtest_results br
                JOIN strategy_combinations sc ON br.combination_id = sc.combination_id
                WHERE br.result_id = ?
            """, (backtest_result_id,))
            
            backtest_row = cursor.fetchone()
            if not backtest_row:
                raise ValueError(f"백테스트 결과를 찾을 수 없습니다: {backtest_result_id}")
            
            # 포트폴리오 정보 조회
            cursor.execute("""
                SELECT current_value, total_return_amount
                FROM portfolios
                WHERE portfolio_id = (
                    SELECT portfolio_id FROM backtest_results WHERE result_id = ?
                )
            """, (backtest_result_id,))
            
            portfolio_row = cursor.fetchone()
            final_value = portfolio_row[0] if portfolio_row else backtest_row[4] * (1 + backtest_row[7])
            total_pnl = portfolio_row[1] if portfolio_row else final_value - backtest_row[4]
            
            # 전략 조합 정보 조회
            entry_strategy, management_strategies = self._get_strategy_info(cursor, backtest_row[15])
            
            # 거래 이력 조회
            trade_history = self._get_trade_history(cursor, backtest_result_id)
            
            # 보고서 데이터 생성
            report_data = BacktestReportData(
                backtest_id=backtest_result_id,
                symbol=backtest_row[0],
                start_date=backtest_row[1],
                end_date=backtest_row[2],
                timeframe=backtest_row[3],
                initial_capital=backtest_row[4],
                trading_fee_rate=backtest_row[5],
                slippage_rate=backtest_row[6],
                combination_name=backtest_row[14],
                entry_strategy=entry_strategy,
                management_strategies=management_strategies,
                combination_rule=f"{entry_strategy}(진입) -> {' AND '.join(management_strategies)}(관리)",
                final_value=final_value,
                total_pnl=total_pnl,
                total_return=backtest_row[7],
                max_drawdown=backtest_row[13],
                sharpe_ratio=backtest_row[12],
                total_trades=backtest_row[8],
                winning_trades=backtest_row[9],
                losing_trades=backtest_row[10],
                win_rate=backtest_row[11],
                trade_history=trade_history
            )
            
            return report_data
            
        finally:
            conn.close()
    
    def _get_strategy_info(self, cursor, combination_id: str) -> Tuple[str, List[str]]:
        """전략 조합 정보 조회"""
        # 진입 전략 조회
        cursor.execute("""
            SELECT sc.strategy_name
            FROM strategy_combinations comb
            JOIN strategy_configs sc ON comb.entry_strategy_id = sc.config_id
            WHERE comb.combination_id = ?
        """, (combination_id,))
        
        entry_result = cursor.fetchone()
        entry_strategy = entry_result[0] if entry_result else "Unknown Entry Strategy"
        
        # 관리 전략들 조회
        cursor.execute("""
            SELECT sc.strategy_name
            FROM combination_management_strategies cms
            JOIN strategy_configs sc ON cms.strategy_config_id = sc.config_id
            WHERE cms.combination_id = ?
            ORDER BY cms.priority
        """, (combination_id,))
        
        management_strategies = [row[0] for row in cursor.fetchall()]
        
        return entry_strategy, management_strategies
    
    def _get_trade_history(self, cursor, backtest_result_id: str) -> List[Dict[str, Any]]:
        """거래 이력 조회"""
        cursor.execute("""
            SELECT position_id, timestamp, action, direction, price, quantity,
                   pnl_percent, pnl_amount, holding_time
            FROM trade_logs
            WHERE backtest_result_id = ?
            ORDER BY timestamp DESC
            LIMIT 10
        """, (backtest_result_id,))
        
        trades = []
        for row in cursor.fetchall():
            trades.append({
                'position_id': row[0],
                'timestamp': row[1],
                'action': row[2],
                'direction': row[3],
                'price': row[4],
                'quantity': row[5],
                'pnl_percent': row[6],
                'pnl_amount': row[7],
                'holding_time': row[8]
            })
        
        return trades
    
    def _calculate_advanced_metrics(self, report_data: BacktestReportData) -> None:
        """고급 성과 지표 계산"""
        # 연평균 수익률 (CAGR) 계산
        start_date = datetime.fromisoformat(report_data.start_date)
        end_date = datetime.fromisoformat(report_data.end_date)
        years = (end_date - start_date).days / 365.25
        
        if years > 0:
            report_data.cagr = (report_data.final_value / report_data.initial_capital) ** (1/years) - 1
        
        # 거래 이력 기반 지표 계산
        if report_data.trade_history:
            profits = [trade['pnl_amount'] for trade in report_data.trade_history if trade['pnl_amount'] > 0]
            losses = [trade['pnl_amount'] for trade in report_data.trade_history if trade['pnl_amount'] < 0]
            
            # 손익비 (Profit Factor)
            total_profit = sum(profits) if profits else 0
            total_loss = abs(sum(losses)) if losses else 1  # 0으로 나누기 방지
            report_data.profit_factor = total_profit / total_loss if total_loss > 0 else 0
            
            # 평균 수익/손실
            report_data.avg_profit = np.mean(profits) if profits else 0
            report_data.avg_loss = np.mean(losses) if losses else 0
            
            # 평균 보유 기간
            holding_times = [trade['holding_time'] for trade in report_data.trade_history if trade['holding_time']]
            report_data.avg_holding_period = np.mean(holding_times) if holding_times else 0
            
            # 연속 승/패 계산
            report_data.max_consecutive_wins, report_data.max_consecutive_losses = \
                self._calculate_consecutive_streaks(report_data.trade_history)
    
    def _calculate_consecutive_streaks(self, trade_history: List[Dict[str, Any]]) -> Tuple[int, int]:
        """연속 승/패 계산"""
        if not trade_history:
            return 0, 0
        
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0
        
        for trade in reversed(trade_history):  # 시간순으로 정렬
            if trade['pnl_amount'] > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            elif trade['pnl_amount'] < 0:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
        
        return max_wins, max_losses
    
    def _generate_report_text(self, data: BacktestReportData) -> str:
        """보고서 텍스트 생성"""
        report = f"""
============================================================
           백테스팅 결과 보고서 (Backtesting Report)
============================================================

------------------------------------------------------------
[ 테스트 개요 (Summary) ]
------------------------------------------------------------
- 테스트 종목     : {data.symbol}
- 테스트 기간     : {data.start_date} ~ {data.end_date}
- 적용 차트       : {data.timeframe}
- 초기 자본       : {data.initial_capital:,.0f} KRW
- 수수료 (Fee)    : {data.trading_fee_rate:.2%}
- 슬리피지 (Slippage) : {data.slippage_rate:.2%}

------------------------------------------------------------
[ 전략 구성 (Strategy Configuration) ]
------------------------------------------------------------
- 진입 전략 ID    : {data.entry_strategy}
- 관리 전략 ID(들) : {', '.join(data.management_strategies)}
- 조합 규칙       : {data.combination_rule}

------------------------------------------------------------
[ 종합 성과 (Overall Performance) ]
------------------------------------------------------------
- 최종 자산        : {data.final_value:,.0f} KRW
- 총 손익         : {data.total_pnl:+,.0f} KRW
- 총 수익률       : {data.total_return:+.2%}
- 최대 낙폭 (MDD)  : {data.max_drawdown:.2%}
- 샤프 지수       : {data.sharpe_ratio:.2f}

------------------------------------------------------------
[ 핵심 성과 지표 (Key Performance Indicators) ]
------------------------------------------------------------
[수익성 지표]
- 연평균 수익률 (CAGR) : {data.cagr:.2%}
- 손익비 (Profit Factor) : {data.profit_factor:.2f}
- 평균 수익 (거래당)    : {data.avg_profit:+,.0f} KRW
- 평균 손실 (거래당)    : {data.avg_loss:+,.0f} KRW

[거래 통계]
- 총 거래 횟수          : {data.total_trades}회
- 승률 (Win Rate)       : {data.win_rate:.2%}
- 평균 보유 기간        : {data.avg_holding_period:.1f}시간
- 최대 연속 수익        : {data.max_consecutive_wins}회
- 최대 연속 손실        : {data.max_consecutive_losses}회

------------------------------------------------------------
[ 최근 거래 내역 (Recent Trade Log) ]
------------------------------------------------------------
 포지션 ID |   진입 시간           |   청산 시간           | 유형 |    진입가     |    청산가     | 손익률
------------------------------------------------------------------------------------------------------"""

        # 거래 내역 추가
        if data.trade_history:
            for i, trade in enumerate(data.trade_history[:5]):  # 최근 5개만 표시
                if i < len(data.trade_history) - 1:
                    # 진입과 청산 쌍 찾기 (단순화)
                    entry_time = trade['timestamp'][:16].replace('T', ' ')
                    exit_time = data.trade_history[i+1]['timestamp'][:16].replace('T', ' ') if i+1 < len(data.trade_history) else "진행중"
                    direction = "매수" if trade['direction'] == 'BUY' else "매도"
                    entry_price = trade['price']
                    exit_price = data.trade_history[i+1]['price'] if i+1 < len(data.trade_history) else trade['price']
                    pnl_percent = trade['pnl_percent']
                    
                    report += f"""
 {trade['position_id'][:8]}  |   {entry_time}    |   {exit_time}    | {direction} |   {entry_price:,.0f}  |   {exit_price:,.0f}  |  {pnl_percent:+.2%}"""

        report += """

============================================================
"""
        
        return report


def main():
    """테스트 실행"""
    print("📊 백테스트 보고서 생성기 테스트")
    
    # 샘플 데이터로 보고서 생성 테스트
    generator = BacktestReportGenerator()
    
    # 데이터베이스에서 최근 백테스트 결과 조회
    conn = generator.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT result_id FROM backtest_results ORDER BY created_at DESC LIMIT 1")
        result = cursor.fetchone()
        
        if result:
            backtest_id = result[0]
            print(f"📈 백테스트 결과 분석: {backtest_id}")
            
            report = generator.generate_report(backtest_id)
            print(report)
            
            # 보고서 파일로 저장
            report_file = f"reports/backtest_report_{backtest_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            os.makedirs("reports", exist_ok=True)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"💾 보고서 저장됨: {report_file}")
        else:
            print("❌ 백테스트 결과가 없습니다.")
            
    finally:
        conn.close()


if __name__ == "__main__":
    main()
