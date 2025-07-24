#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
데이터베이스 연동 백테스트 엔진

기존 combination_backtest_engine.py와 새로운 DB 스키마 V2.0을 연결하는 어댑터
- 포지션 ID 관리
- 포트폴리오 연동
- 백테스트 결과 DB 저장
- 실시간 성과 추적
"""

import os
import sys
import sqlite3
import json
import uuid
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

# 프로젝트 루트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, project_root)

# 기존 백테스트 엔진 임포트
try:
    from upbit_auto_trading.business_logic.strategy.combination_backtest_engine import (
        StrategyCombinationBacktestEngine, BacktestResult, PositionInfo, BacktestState
    )
    from upbit_auto_trading.business_logic.strategy.strategy_combination import (
        StrategyCombination, StrategyConfig
    )
except ImportError:
    # 개발 환경에서의 임포트
    sys.path.append(os.path.join(project_root, 'upbit_auto_trading', 'business_logic', 'strategy'))
    from combination_backtest_engine import (
        StrategyCombinationBacktestEngine, BacktestResult, PositionInfo, BacktestState
    )
    from strategy_combination import StrategyCombination, StrategyConfig


@dataclass
class DatabaseBacktestConfig:
    """데이터베이스 연동 백테스트 설정"""
    portfolio_id: str
    combination_id: str
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    initial_capital: float
    trading_fee_rate: float = 0.0005
    slippage_rate: float = 0.001
    risk_settings: Dict[str, Any] = None
    db_path: str = "data/market_data.sqlite3"


class DatabaseBacktestEngine:
    """데이터베이스 연동 백테스트 엔진"""
    
    def __init__(self, config: DatabaseBacktestConfig):
        self.config = config
        self.db_path = config.db_path
        
        # 백테스트 결과 ID 생성
        self.result_id = f"bt_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
        
        # 기존 백테스트 엔진 초기화
        self.engine = None
        
        # 포지션 ID 매핑 (엔진 내부 포지션 → DB 포지션 ID)
        self.position_id_mapping: Dict[str, str] = {}
        
    def get_connection(self) -> sqlite3.Connection:
        """데이터베이스 연결 반환"""
        return sqlite3.connect(self.db_path)
    
    def initialize_backtest_record(self) -> None:
        """백테스트 결과 레코드 초기화"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 백테스트 결과 초기 레코드 생성
            cursor.execute("""
                INSERT INTO backtest_results (
                    result_id, portfolio_id, combination_id, symbol, timeframe,
                    start_date, end_date, initial_capital, trading_fee_rate, slippage_rate,
                    risk_settings, status, backtest_start, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.result_id,
                self.config.portfolio_id,
                self.config.combination_id,
                self.config.symbol,
                self.config.timeframe,
                self.config.start_date,
                self.config.end_date,
                self.config.initial_capital,
                self.config.trading_fee_rate,
                self.config.slippage_rate,
                json.dumps(self.config.risk_settings or {}),
                'running',
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            print(f"✅ 백테스트 레코드 초기화: {self.result_id}")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 백테스트 레코드 초기화 실패: {e}")
            raise
        finally:
            conn.close()
    
    def load_strategy_combination(self) -> StrategyCombination:
        """데이터베이스에서 전략 조합 로드"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 전략 조합 정보 조회
            cursor.execute("""
                SELECT sc.name, sc.description, sc.entry_strategy_id, sc.conflict_resolution,
                       config.strategy_name, config.parameters, def.class_name
                FROM strategy_combinations sc
                JOIN strategy_configs config ON sc.entry_strategy_id = config.config_id
                JOIN strategy_definitions def ON config.strategy_definition_id = def.id
                WHERE sc.combination_id = ?
            """, (self.config.combination_id,))
            
            combination_row = cursor.fetchone()
            if not combination_row:
                raise ValueError(f"전략 조합을 찾을 수 없습니다: {self.config.combination_id}")
            
            name, description, entry_strategy_id, conflict_resolution, \
            entry_name, entry_params, entry_class = combination_row
            
            # 진입 전략 설정 생성
            entry_config = StrategyConfig(
                strategy_id=entry_strategy_id,
                strategy_name=entry_name,
                parameters=json.loads(entry_params),
                class_name=entry_class
            )
            
            # 관리 전략들 조회
            cursor.execute("""
                SELECT cms.priority, config.config_id, config.strategy_name, 
                       config.parameters, def.class_name
                FROM combination_management_strategies cms
                JOIN strategy_configs config ON cms.strategy_config_id = config.config_id
                JOIN strategy_definitions def ON config.strategy_definition_id = def.id
                WHERE cms.combination_id = ?
                ORDER BY cms.priority
            """, (self.config.combination_id,))
            
            management_configs = []
            for row in cursor.fetchall():
                priority, config_id, strategy_name, parameters, class_name = row
                management_config = StrategyConfig(
                    strategy_id=config_id,
                    strategy_name=strategy_name,
                    parameters=json.loads(parameters),
                    class_name=class_name
                )
                management_configs.append(management_config)
            
            # 전략 조합 생성
            combination = StrategyCombination(
                combination_id=self.config.combination_id,
                name=name,
                description=description,
                entry_strategy=entry_config,
                management_strategies=management_configs,
                conflict_resolution=conflict_resolution
            )
            
            print(f"✅ 전략 조합 로드: {name}")
            print(f"   진입 전략: {entry_name}")
            print(f"   관리 전략: {len(management_configs)}개")
            
            return combination
            
        except Exception as e:
            print(f"❌ 전략 조합 로드 실패: {e}")
            raise
        finally:
            conn.close()
    
    def create_position_record(self, position_info: PositionInfo, entry_signal: Dict[str, Any]) -> str:
        """포지션 레코드 생성"""
        position_id = f"pos_{self.config.symbol}_{uuid.uuid4().hex[:8]}"
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO positions (
                    position_id, portfolio_id, symbol, direction,
                    entry_price, current_price, quantity, remaining_quantity,
                    unrealized_pnl_percent, unrealized_pnl_amount, realized_pnl_amount,
                    entry_strategy_id, entry_reason, management_actions,
                    status, opened_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                position_id,
                self.config.portfolio_id,
                self.config.symbol,
                position_info.direction,
                position_info.entry_price,
                position_info.entry_price,  # 초기에는 진입가와 동일
                position_info.quantity,
                position_info.quantity,  # 초기에는 전체 수량
                0.0,  # 초기 손익은 0
                0.0,
                0.0,
                entry_signal.get('strategy_id'),
                entry_signal.get('reason', 'Entry signal'),
                json.dumps([]),  # 빈 관리 액션 리스트
                'open',
                position_info.entry_time.isoformat(),
                datetime.now().isoformat()
            ))
            
            # 포지션 이력 기록
            cursor.execute("""
                INSERT INTO position_history (
                    position_id, timestamp, action, price, quantity_change, quantity_after,
                    strategy_name, reason, triggered_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                position_id,
                position_info.entry_time.isoformat(),
                'OPEN',
                position_info.entry_price,
                position_info.quantity,
                position_info.quantity,
                entry_signal.get('strategy_name', 'Unknown'),
                entry_signal.get('reason', 'Entry signal'),
                'strategy'
            ))
            
            conn.commit()
            print(f"✅ 포지션 생성: {position_id} ({position_info.direction} {position_info.quantity})")
            
            return position_id
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 포지션 생성 실패: {e}")
            raise
        finally:
            conn.close()
    
    def update_position_record(self, position_id: str, current_price: float, 
                             action: Optional[Dict[str, Any]] = None) -> None:
        """포지션 레코드 업데이트"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 현재 포지션 정보 조회
            cursor.execute("""
                SELECT entry_price, quantity, remaining_quantity, direction
                FROM positions WHERE position_id = ?
            """, (position_id,))
            
            result = cursor.fetchone()
            if not result:
                return
            
            entry_price, quantity, remaining_quantity, direction = result
            
            # 손익 계산
            if direction == 'BUY':
                pnl_percent = (current_price - entry_price) / entry_price
            else:
                pnl_percent = (entry_price - current_price) / entry_price
            
            pnl_amount = pnl_percent * entry_price * remaining_quantity
            
            # 포지션 정보 업데이트
            cursor.execute("""
                UPDATE positions 
                SET current_price = ?, 
                    unrealized_pnl_percent = ?,
                    unrealized_pnl_amount = ?,
                    updated_at = ?
                WHERE position_id = ?
            """, (
                current_price,
                pnl_percent,
                pnl_amount,
                datetime.now().isoformat(),
                position_id
            ))
            
            # 관리 액션이 있는 경우 이력 추가
            if action:
                self.add_position_history(position_id, action)
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 포지션 업데이트 실패: {e}")
        finally:
            conn.close()
    
    def add_position_history(self, position_id: str, action: Dict[str, Any]) -> None:
        """포지션 이력 추가"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO position_history (
                    position_id, timestamp, action, price, quantity_change, quantity_after,
                    strategy_name, reason, triggered_by,
                    stop_price_before, stop_price_after
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                position_id,
                datetime.now().isoformat(),
                action.get('action_type', 'UPDATE'),
                action.get('price', 0),
                action.get('quantity_change', 0),
                action.get('quantity_after', 0),
                action.get('strategy_name', 'Unknown'),
                action.get('reason', 'Management action'),
                action.get('triggered_by', 'strategy'),
                action.get('stop_price_before'),
                action.get('stop_price_after')
            ))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 포지션 이력 추가 실패: {e}")
        finally:
            conn.close()
    
    def log_trade(self, trade_info: Dict[str, Any]) -> None:
        """거래 로그 기록"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO trade_logs (
                    backtest_result_id, position_id, timestamp, action, direction,
                    price, quantity, pnl_percent, pnl_amount, fees,
                    strategy_name, reason, stop_price, risk_percent, holding_time,
                    portfolio_value_after, cash_balance_after
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.result_id,
                trade_info.get('position_id'),
                trade_info.get('timestamp', datetime.now().isoformat()),
                trade_info.get('action'),
                trade_info.get('direction'),
                trade_info.get('price'),
                trade_info.get('quantity'),
                trade_info.get('pnl_percent'),
                trade_info.get('pnl_amount'),
                trade_info.get('fees', 0),
                trade_info.get('strategy_name'),
                trade_info.get('reason'),
                trade_info.get('stop_price'),
                trade_info.get('risk_percent'),
                trade_info.get('holding_time'),
                trade_info.get('portfolio_value_after'),
                trade_info.get('cash_balance_after')
            ))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 거래 로그 기록 실패: {e}")
        finally:
            conn.close()
    
    def finalize_backtest_result(self, result: BacktestResult) -> None:
        """백테스트 결과 완료 처리"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE backtest_results SET
                    total_return = ?,
                    total_trades = ?,
                    winning_trades = ?,
                    losing_trades = ?,
                    win_rate = ?,
                    sharpe_ratio = ?,
                    max_drawdown = ?,
                    entry_contribution = ?,
                    management_contribution = ?,
                    status = ?,
                    backtest_end = ?,
                    data_points = ?
                WHERE result_id = ?
            """, (
                result.total_return_percent,
                result.total_trades,
                result.winning_trades,
                result.losing_trades,
                result.win_rate,
                result.sharpe_ratio,
                result.max_drawdown,
                json.dumps(result.entry_contribution or {}),
                json.dumps(result.management_contribution or {}),
                'completed',
                datetime.now().isoformat(),
                len(result.trades) if hasattr(result, 'trades') else 0,
                self.result_id
            ))
            
            conn.commit()
            print(f"✅ 백테스트 결과 저장 완료: {self.result_id}")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 백테스트 결과 저장 실패: {e}")
            raise
        finally:
            conn.close()
    
    def run_backtest(self, market_data: pd.DataFrame) -> BacktestResult:
        """백테스트 실행"""
        print(f"🚀 데이터베이스 연동 백테스트 시작")
        print(f"   결과 ID: {self.result_id}")
        print(f"   포트폴리오: {self.config.portfolio_id}")
        print(f"   전략 조합: {self.config.combination_id}")
        
        try:
            # 1. 백테스트 레코드 초기화
            self.initialize_backtest_record()
            
            # 2. 전략 조합 로드
            combination = self.load_strategy_combination()
            
            # 3. 기존 백테스트 엔진 초기화
            self.engine = StrategyCombinationBacktestEngine()
            self.engine.load_combination(combination)
            
            # 4. 백테스트 실행 (기존 엔진 활용)
            result = self.engine.run_backtest(
                market_data=market_data,
                initial_capital=self.config.initial_capital
            )
            
            # 5. 결과를 데이터베이스에 저장
            self.finalize_backtest_result(result)
            
            print(f"🎉 백테스트 완료!")
            print(f"   총 수익률: {result.total_return:.2%}")
            print(f"   승률: {result.win_rate:.2%}")
            print(f"   최대 낙폭: {result.max_drawdown:.2%}")
            
            return result
            
        except Exception as e:
            # 실패 시 상태 업데이트
            conn = self.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE backtest_results SET
                        status = ?,
                        error_message = ?,
                        backtest_end = ?
                    WHERE result_id = ?
                """, ('failed', str(e), datetime.now().isoformat(), self.result_id))
                conn.commit()
            except:
                pass
            finally:
                conn.close()
            
            print(f"❌ 백테스트 실행 실패: {e}")
            raise


def main():
    """테스트 실행"""
    print("🧪 데이터베이스 연동 백테스트 엔진 테스트")
    
    # 테스트 설정
    config = DatabaseBacktestConfig(
        portfolio_id="backtest_portfolio_1",
        combination_id="rsi_averaging_trailing",
        symbol="KRW-BTC",
        timeframe="1h",
        start_date="2024-01-01",
        end_date="2024-12-31",
        initial_capital=1000000.0,
        risk_settings={
            "max_position_size": 0.2,
            "stop_loss": 0.05,
            "max_daily_loss": 0.03
        }
    )
    
    # 간단한 테스트 데이터 생성
    dates = pd.date_range('2024-01-01', '2024-01-31', freq='H')
    test_data = pd.DataFrame({
        'timestamp': dates,
        'open': 50000000 + np.random.randn(len(dates)) * 1000000,
        'high': 51000000 + np.random.randn(len(dates)) * 1000000,
        'low': 49000000 + np.random.randn(len(dates)) * 1000000,
        'close': 50000000 + np.random.randn(len(dates)) * 1000000,
        'volume': 100 + np.random.randn(len(dates)) * 10
    })
    
    # 백테스트 실행
    engine = DatabaseBacktestEngine(config)
    try:
        result = engine.run_backtest(test_data)
        print(f"✅ 테스트 성공: {result.combination_name}")
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")


if __name__ == "__main__":
    main()
