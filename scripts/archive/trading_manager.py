#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
통합 트레이딩 매니저

백테스트 엔진과 포지션 관리 시스템을 통합하여 관리:
- 실시간 포지션 추적
- 백테스트 결과와 실제 포지션 연동
- 포트폴리오 성과 실시간 계산
- 리스크 관리 통합
"""

import os
import sys
import sqlite3
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# 프로젝트 루트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from database_backtest_engine import DatabaseBacktestEngine, DatabaseBacktestConfig
from position_manager import PositionManager, Position, PositionUpdate, PositionAction, PositionStatus


class TradingManager:
    """통합 트레이딩 매니저"""
    
    def __init__(self, db_path: str = "data/upbit_auto_trading.sqlite3"):
        self.db_path = db_path
        self.position_manager = PositionManager(db_path)
        
    def get_connection(self) -> sqlite3.Connection:
        """데이터베이스 연결 반환"""
        return sqlite3.connect(self.db_path)
    
    def run_strategy_backtest(self, config: DatabaseBacktestConfig, 
                            market_data: pd.DataFrame) -> Dict[str, Any]:
        """전략 백테스트 실행 및 결과 분석"""
        print("🚀 전략 백테스트 실행")
        
        # 백테스트 엔진 생성 및 실행
        engine = DatabaseBacktestEngine(config)
        result = engine.run_backtest(market_data)
        
        # 결과 분석
        analysis = self.analyze_backtest_result(result.result_id)
        
        return {
            "backtest_result": result,
            "analysis": analysis,
            "result_id": result.result_id
        }
    
    def analyze_backtest_result(self, result_id: str) -> Dict[str, Any]:
        """백테스트 결과 분석"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 백테스트 기본 정보
            cursor.execute("""
                SELECT combination_id, symbol, total_return, sharpe_ratio, 
                       max_drawdown, win_rate, total_trades
                FROM backtest_results WHERE result_id = ?
            """, (result_id,))
            
            result_row = cursor.fetchone()
            if not result_row:
                return {"error": "백테스트 결과를 찾을 수 없습니다"}
            
            combination_id, symbol, total_return, sharpe_ratio, max_drawdown, win_rate, total_trades = result_row
            
            # 거래 로그 분석
            cursor.execute("""
                SELECT action, direction, pnl_percent, holding_time
                FROM trade_logs 
                WHERE backtest_result_id = ? AND action IN ('ENTER', 'EXIT')
                ORDER BY timestamp
            """, (result_id,))
            
            trade_logs = cursor.fetchall()
            
            # 성과 지표 계산
            entry_trades = [t for t in trade_logs if t[0] == 'ENTER']
            exit_trades = [t for t in trade_logs if t[0] == 'EXIT']
            
            profitable_trades = [t for t in exit_trades if t[2] > 0]
            losing_trades = [t for t in exit_trades if t[2] < 0]
            
            avg_holding_time = sum(t[3] for t in exit_trades if t[3]) / len(exit_trades) if exit_trades else 0
            avg_profit = sum(t[2] for t in profitable_trades) / len(profitable_trades) if profitable_trades else 0
            avg_loss = sum(t[2] for t in losing_trades) / len(losing_trades) if losing_trades else 0
            
            analysis = {
                "basic_metrics": {
                    "total_return": total_return,
                    "sharpe_ratio": sharpe_ratio,
                    "max_drawdown": max_drawdown,
                    "win_rate": win_rate,
                    "total_trades": total_trades
                },
                "trade_analysis": {
                    "profitable_trades": len(profitable_trades),
                    "losing_trades": len(losing_trades),
                    "avg_profit": avg_profit,
                    "avg_loss": avg_loss,
                    "profit_factor": abs(avg_profit / avg_loss) if avg_loss != 0 else float('inf'),
                    "avg_holding_time": avg_holding_time
                },
                "risk_metrics": {
                    "max_drawdown": max_drawdown,
                    "sharpe_ratio": sharpe_ratio,
                    "win_rate": win_rate
                }
            }
            
            return analysis
            
        finally:
            conn.close()
    
    def get_portfolio_performance(self, portfolio_id: str) -> Dict[str, Any]:
        """포트폴리오 성과 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 포트폴리오 기본 정보
            cursor.execute("""
                SELECT name, initial_capital, current_value, cash_balance,
                       total_return_percent, total_return_amount,
                       unrealized_pnl, realized_pnl, max_drawdown
                FROM portfolios WHERE portfolio_id = ?
            """, (portfolio_id,))
            
            portfolio_row = cursor.fetchone()
            if not portfolio_row:
                return {"error": "포트폴리오를 찾을 수 없습니다"}
            
            name, initial_capital, current_value, cash_balance, \
            total_return_percent, total_return_amount, \
            unrealized_pnl, realized_pnl, max_drawdown = portfolio_row
            
            # 활성 포지션 조회
            active_positions = self.position_manager.get_portfolio_positions(
                portfolio_id, [PositionStatus.OPEN, PositionStatus.PARTIAL_CLOSED]
            )
            
            # 전체 포지션 통계
            cursor.execute("""
                SELECT COUNT(*), 
                       SUM(CASE WHEN status = 'closed' AND realized_pnl_amount > 0 THEN 1 ELSE 0 END),
                       SUM(CASE WHEN status = 'closed' AND realized_pnl_amount < 0 THEN 1 ELSE 0 END),
                       AVG(realized_pnl_amount),
                       SUM(realized_pnl_amount)
                FROM positions WHERE portfolio_id = ?
            """, (portfolio_id,))
            
            position_stats = cursor.fetchone()
            total_positions, winning_positions, losing_positions, avg_pnl, total_realized_pnl = position_stats
            
            performance = {
                "portfolio_info": {
                    "name": name,
                    "initial_capital": initial_capital,
                    "current_value": current_value,
                    "cash_balance": cash_balance
                },
                "returns": {
                    "total_return_percent": total_return_percent,
                    "total_return_amount": total_return_amount,
                    "unrealized_pnl": unrealized_pnl,
                    "realized_pnl": realized_pnl
                },
                "risk_metrics": {
                    "max_drawdown": max_drawdown
                },
                "position_summary": {
                    "active_positions": len(active_positions),
                    "total_positions": total_positions,
                    "winning_positions": winning_positions,
                    "losing_positions": losing_positions,
                    "win_rate": winning_positions / total_positions if total_positions > 0 else 0,
                    "avg_pnl": avg_pnl,
                    "total_realized_pnl": total_realized_pnl
                },
                "active_positions": [
                    {
                        "position_id": pos.position_id,
                        "symbol": pos.symbol,
                        "direction": pos.direction,
                        "entry_price": pos.entry_price,
                        "current_price": pos.current_price,
                        "quantity": pos.remaining_quantity,
                        "unrealized_pnl_percent": pos.unrealized_pnl_percent,
                        "unrealized_pnl_amount": pos.unrealized_pnl_amount
                    }
                    for pos in active_positions
                ]
            }
            
            return performance
            
        finally:
            conn.close()
    
    def update_portfolio_performance(self, portfolio_id: str) -> None:
        """포트폴리오 성과 실시간 업데이트"""
        
        # 활성 포지션들의 미실현 손익 합계 계산
        active_positions = self.position_manager.get_portfolio_positions(
            portfolio_id, [PositionStatus.OPEN, PositionStatus.PARTIAL_CLOSED]
        )
        
        total_unrealized_pnl = sum(pos.unrealized_pnl_amount for pos in active_positions)
        total_position_value = sum(pos.get_position_value() for pos in active_positions)
        
        # 실현 손익 조회
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT SUM(realized_pnl_amount), initial_capital, cash_balance
                FROM positions p
                JOIN portfolios pf ON p.portfolio_id = pf.portfolio_id
                WHERE p.portfolio_id = ?
                GROUP BY initial_capital, cash_balance
            """, (portfolio_id,))
            
            result = cursor.fetchone()
            if result:
                total_realized_pnl, initial_capital, cash_balance = result
                total_realized_pnl = total_realized_pnl or 0
                
                # 총 포트폴리오 가치 계산
                current_value = cash_balance + total_position_value
                total_return_amount = total_realized_pnl + total_unrealized_pnl
                total_return_percent = total_return_amount / initial_capital if initial_capital > 0 else 0
                
                # 포트폴리오 정보 업데이트
                cursor.execute("""
                    UPDATE portfolios SET
                        current_value = ?,
                        total_return_percent = ?,
                        total_return_amount = ?,
                        unrealized_pnl = ?,
                        realized_pnl = ?,
                        updated_at = ?
                    WHERE portfolio_id = ?
                """, (
                    current_value,
                    total_return_percent,
                    total_return_amount,
                    total_unrealized_pnl,
                    total_realized_pnl,
                    datetime.now().isoformat(),
                    portfolio_id
                ))
                
                conn.commit()
                print(f"✅ 포트폴리오 성과 업데이트: {portfolio_id}")
                print(f"   현재 가치: {current_value:,.0f}")
                print(f"   총 수익률: {total_return_percent:.2%}")
        
        finally:
            conn.close()
    
    def create_portfolio_snapshot(self, portfolio_id: str, snapshot_type: str = "hourly") -> None:
        """포트폴리오 스냅샷 생성"""
        performance = self.get_portfolio_performance(portfolio_id)
        
        if "error" in performance:
            print(f"❌ 스냅샷 생성 실패: {performance['error']}")
            return
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO portfolio_snapshots (
                    portfolio_id, snapshot_time, snapshot_type,
                    total_value, cash_balance, invested_amount,
                    total_return_percent, total_return_amount,
                    unrealized_pnl, realized_pnl, drawdown_percent,
                    open_positions_count, total_positions_value
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                portfolio_id,
                datetime.now().isoformat(),
                snapshot_type,
                performance["portfolio_info"]["current_value"],
                performance["portfolio_info"]["cash_balance"],
                performance["portfolio_info"]["current_value"] - performance["portfolio_info"]["cash_balance"],
                performance["returns"]["total_return_percent"],
                performance["returns"]["total_return_amount"],
                performance["returns"]["unrealized_pnl"],
                performance["returns"]["realized_pnl"],
                performance["risk_metrics"]["max_drawdown"],
                performance["position_summary"]["active_positions"],
                sum(pos["unrealized_pnl_amount"] + pos["current_price"] * pos["quantity"] 
                    for pos in performance["active_positions"])
            ))
            
            conn.commit()
            print(f"✅ 포트폴리오 스냅샷 생성: {portfolio_id} ({snapshot_type})")
            
        finally:
            conn.close()
    
    def get_strategy_performance_comparison(self) -> Dict[str, Any]:
        """전략 성과 비교"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 전략 조합별 백테스트 성과
            cursor.execute("""
                SELECT sc.name, sc.combination_id,
                       AVG(br.total_return) as avg_return,
                       AVG(br.sharpe_ratio) as avg_sharpe,
                       AVG(br.win_rate) as avg_win_rate,
                       AVG(br.max_drawdown) as avg_drawdown,
                       COUNT(br.result_id) as backtest_count
                FROM strategy_combinations sc
                LEFT JOIN backtest_results br ON sc.combination_id = br.combination_id
                WHERE br.status = 'completed'
                GROUP BY sc.combination_id, sc.name
                ORDER BY avg_return DESC
            """, ())
            
            strategy_performance = []
            for row in cursor.fetchall():
                name, combination_id, avg_return, avg_sharpe, avg_win_rate, avg_drawdown, backtest_count = row
                strategy_performance.append({
                    "name": name,
                    "combination_id": combination_id,
                    "avg_return": avg_return,
                    "avg_sharpe": avg_sharpe,
                    "avg_win_rate": avg_win_rate,
                    "avg_drawdown": avg_drawdown,
                    "backtest_count": backtest_count
                })
            
            return {
                "strategy_rankings": strategy_performance,
                "best_strategy": strategy_performance[0] if strategy_performance else None,
                "total_strategies": len(strategy_performance)
            }
            
        finally:
            conn.close()


def main():
    """테스트 실행"""
    print("🧪 통합 트레이딩 매니저 테스트")
    
    manager = TradingManager()
    
    # 1. 포트폴리오 성과 조회
    performance = manager.get_portfolio_performance("backtest_portfolio_1")
    if "error" not in performance:
        print("📊 포트폴리오 성과:")
        print(f"   현재 가치: {performance['portfolio_info']['current_value']:,.0f}")
        print(f"   총 수익률: {performance['returns']['total_return_percent']:.2%}")
        print(f"   활성 포지션: {performance['position_summary']['active_positions']}개")
    
    # 2. 포트폴리오 성과 업데이트
    manager.update_portfolio_performance("backtest_portfolio_1")
    
    # 3. 스냅샷 생성
    manager.create_portfolio_snapshot("backtest_portfolio_1", "daily")
    
    # 4. 전략 성과 비교
    strategy_comparison = manager.get_strategy_performance_comparison()
    print(f"📈 전략 성과 비교: {strategy_comparison['total_strategies']}개 전략")
    
    if strategy_comparison["best_strategy"]:
        best = strategy_comparison["best_strategy"]
        print(f"   최고 성과 전략: {best['name']}")
        print(f"   평균 수익률: {best['avg_return']:.2%}")
    
    print("✅ 통합 트레이딩 매니저 테스트 완료")


if __name__ == "__main__":
    main()
