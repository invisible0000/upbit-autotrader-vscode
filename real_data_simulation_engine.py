"""
실제 데이터 기반 시뮬레이션 엔진
- 추출된 시나리오 세그먼트를 사용하여 실제 조건 테스트
- integrated_condition_manager와 연동
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
import json
import uuid
from data_scenario_mapper import DataScenarioMapper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RealDataSimulationEngine:
    def __init__(self, unified_db_path: str = "upbit_trading_unified.db", 
                 data_db_path: str = "data/upbit_auto_trading.sqlite3"):
        """
        실제 데이터 기반 시뮬레이션 엔진 초기화
        
        Args:
            unified_db_path: 통합 DB 경로 (트리거 정보)
            data_db_path: 실제 시장 데이터 DB 경로
        """
        self.unified_db_path = unified_db_path
        self.data_db_path = data_db_path
        self.mapper = DataScenarioMapper(data_db_path)
        self.current_simulation = None
        
        # 시뮬레이션 테이블 생성
        self.init_simulation_tables()
    
    def init_simulation_tables(self):
        """시뮬레이션용 테이블 초기화"""
        try:
            conn = sqlite3.connect(self.unified_db_path)
            cursor = conn.cursor()
            
            # 시뮬레이션 세션 테이블
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_sessions (
                session_id TEXT PRIMARY KEY,
                scenario_name TEXT NOT NULL,
                scenario_description TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                data_start_time TEXT NOT NULL,
                data_end_time TEXT NOT NULL,
                initial_capital REAL DEFAULT 1000000,
                current_capital REAL DEFAULT 1000000,
                current_price REAL DEFAULT 0,
                position_quantity REAL DEFAULT 0,
                position_avg_price REAL DEFAULT 0,
                total_trades INTEGER DEFAULT 0,
                triggered_conditions TEXT,
                execution_log TEXT,
                status TEXT DEFAULT 'running',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 시뮬레이션 시장 데이터 테이블 (실시간 재생용)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL NOT NULL,
                rsi_14 REAL,
                sma_20 REAL,
                sma_60 REAL,
                profit_rate REAL DEFAULT 0,
                is_processed BOOLEAN DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES simulation_sessions(session_id)
            )
            """)
            
            # 시뮬레이션 트레이드 로그 테이블
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_trades (
                trade_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                price REAL NOT NULL,
                quantity REAL NOT NULL,
                amount REAL NOT NULL,
                trigger_name TEXT,
                trigger_condition TEXT,
                profit_rate REAL,
                portfolio_value REAL,
                reason TEXT,
                FOREIGN KEY (session_id) REFERENCES simulation_sessions(session_id)
            )
            """)
            
            conn.commit()
            conn.close()
            
            logging.info("✅ 시뮬레이션 테이블 초기화 완료")
            
        except Exception as e:
            logging.error(f"❌ 시뮬레이션 테이블 초기화 실패: {e}")
    
    def load_active_triggers(self) -> List[Dict]:
        """
        활성화된 트리거 로드
        
        Returns:
            List[Dict]: 활성화된 트리거 정보
        """
        try:
            conn = sqlite3.connect(self.unified_db_path)
            cursor = conn.cursor()
            
            # 활성화된 트리거 조회
            cursor.execute("""
            SELECT trigger_id, name, description, condition_logic, action_config, is_active
            FROM triggers
            WHERE is_active = 1
            """)
            
            triggers = []
            for row in cursor.fetchall():
                triggers.append({
                    'trigger_id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'condition_logic': json.loads(row[3]) if row[3] else {},
                    'action_config': json.loads(row[4]) if row[4] else {},
                    'is_active': bool(row[5])
                })
            
            conn.close()
            logging.info(f"✅ 활성 트리거 로드: {len(triggers)}개")
            return triggers
            
        except Exception as e:
            logging.error(f"❌ 트리거 로드 실패: {e}")
            return []
    
    def prepare_simulation_data(self, scenario: str, segment_index: int = 0) -> Optional[str]:
        """
        시나리오에 맞는 시뮬레이션 데이터 준비
        
        Args:
            scenario: 시나리오 이름 (예: "📈 상승")
            segment_index: 세그먼트 인덱스 (0부터 시작)
            
        Returns:
            str: 생성된 시뮬레이션 세션 ID
        """
        try:
            # 시나리오 세그먼트 가져오기
            all_scenarios = self.mapper.generate_all_scenarios()
            
            if scenario not in all_scenarios or not all_scenarios[scenario]:
                logging.error(f"❌ {scenario} 시나리오에 대한 데이터가 없습니다")
                return None
            
            segments = all_scenarios[scenario]
            if segment_index >= len(segments):
                segment_index = 0
                
            segment = segments[segment_index]
            
            # 세션 ID 생성
            session_id = f"sim_{uuid.uuid4().hex[:8]}"
            
            # 해당 기간의 시장 데이터 로드
            df = self.mapper.load_market_data()
            df = self.mapper.calculate_technical_indicators(df)
            
            # 세그먼트 데이터 필터링
            segment_data = df[
                (df.index >= segment['start_time']) & 
                (df.index <= segment['end_time'])
            ].copy()
            
            if segment_data.empty:
                logging.error(f"❌ 세그먼트 데이터가 비어있습니다")
                return None
            
            # 시뮬레이션 세션 생성
            conn = sqlite3.connect(self.unified_db_path)
            cursor = conn.cursor()
            
            scenario_config = self.mapper.scenario_configs.get(scenario, {})
            
            cursor.execute("""
            INSERT INTO simulation_sessions 
            (session_id, scenario_name, scenario_description, start_time, 
             data_start_time, data_end_time, current_price, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                scenario,
                scenario_config.get('description', ''),
                datetime.now().isoformat(),
                segment['start_time'].isoformat(),
                segment['end_time'].isoformat(),
                float(segment_data['close'].iloc[0]),
                'prepared'
            ))
            
            # 시뮬레이션 시장 데이터 삽입
            for timestamp, row in segment_data.iterrows():
                # 수익률 계산 (첫 번째 가격 기준)
                initial_price = segment_data['close'].iloc[0]
                profit_rate = (row['close'] / initial_price - 1) * 100
                
                cursor.execute("""
                INSERT INTO simulation_market_data 
                (session_id, timestamp, open, high, low, close, volume, 
                 rsi_14, sma_20, sma_60, profit_rate, is_processed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    timestamp.isoformat(),
                    float(row['open']),
                    float(row['high']),
                    float(row['low']),
                    float(row['close']),
                    float(row['volume']),
                    float(row['rsi']) if not pd.isna(row['rsi']) else None,
                    float(row['sma_20']) if not pd.isna(row['sma_20']) else None,
                    float(row['sma_60']) if not pd.isna(row['sma_60']) else None,
                    float(profit_rate),
                    0
                ))
            
            conn.commit()
            conn.close()
            
            logging.info(f"✅ 시뮬레이션 데이터 준비 완료: {session_id}")
            logging.info(f"📊 데이터 기간: {segment['start_time']} ~ {segment['end_time']}")
            logging.info(f"📈 데이터 포인트: {len(segment_data)}개")
            
            return session_id
            
        except Exception as e:
            logging.error(f"❌ 시뮬레이션 데이터 준비 실패: {e}")
            return None
    
    def run_simulation(self, session_id: str) -> Dict[str, Any]:
        """
        시뮬레이션 실행
        
        Args:
            session_id: 시뮬레이션 세션 ID
            
        Returns:
            Dict: 시뮬레이션 결과
        """
        try:
            conn = sqlite3.connect(self.unified_db_path)
            cursor = conn.cursor()
            
            # 세션 정보 로드
            cursor.execute("""
            SELECT scenario_name, initial_capital, current_capital, current_price
            FROM simulation_sessions WHERE session_id = ?
            """, (session_id,))
            
            session_info = cursor.fetchone()
            if not session_info:
                return {"error": "세션을 찾을 수 없습니다"}
            
            scenario_name, initial_capital, current_capital, current_price = session_info
            
            # 활성 트리거 로드
            triggers = self.load_active_triggers()
            if not triggers:
                return {"error": "활성화된 트리거가 없습니다"}
            
            # 시뮬레이션 상태 업데이트
            cursor.execute("""
            UPDATE simulation_sessions 
            SET status = 'running', start_time = ?
            WHERE session_id = ?
            """, (datetime.now().isoformat(), session_id))
            
            # 시장 데이터 로드
            cursor.execute("""
            SELECT timestamp, open, high, low, close, volume, rsi_14, sma_20, sma_60, profit_rate
            FROM simulation_market_data 
            WHERE session_id = ? AND is_processed = 0
            ORDER BY timestamp ASC
            """, (session_id,))
            
            market_data = cursor.fetchall()
            
            # 시뮬레이션 실행
            portfolio = {
                'cash': float(current_capital),
                'btc_quantity': 0.0,
                'btc_avg_price': 0.0,
                'total_value': float(current_capital)
            }
            
            triggered_conditions = []
            trades = []
            
            for i, data_row in enumerate(market_data):
                timestamp, open_price, high, low, close, volume, rsi, sma_20, sma_60, profit_rate = data_row
                
                # 현재 시장 상황
                market_state = {
                    'current_price': float(close),
                    'profit_rate': float(profit_rate) if profit_rate else 0.0,
                    'rsi_14': float(rsi) if rsi else 50.0,
                    'sma_20': float(sma_20) if sma_20 else float(close),
                    'sma_60': float(sma_60) if sma_60 else float(close)
                }
                
                # 각 트리거 조건 확인
                for trigger in triggers:
                    if self.check_trigger_condition(trigger, market_state, portfolio):
                        # 트리거 실행
                        trade_result = self.execute_trigger_action(
                            trigger, market_state, portfolio, timestamp
                        )
                        
                        if trade_result:
                            triggered_conditions.append({
                                'trigger_name': trigger['name'],
                                'timestamp': timestamp,
                                'market_state': market_state.copy(),
                                'action': trade_result['action']
                            })
                            trades.append(trade_result)
                
                # 포트폴리오 가치 업데이트
                if portfolio['btc_quantity'] > 0:
                    portfolio['total_value'] = portfolio['cash'] + (portfolio['btc_quantity'] * float(close))
                else:
                    portfolio['total_value'] = portfolio['cash']
                
                # 진행률 표시 (10단계로)
                if i % max(1, len(market_data) // 10) == 0:
                    progress = (i / len(market_data)) * 100
                    logging.info(f"📊 시뮬레이션 진행률: {progress:.0f}%")
            
            # 최종 결과 계산
            final_return = (portfolio['total_value'] / initial_capital - 1) * 100
            
            # 결과 저장
            cursor.execute("""
            UPDATE simulation_sessions 
            SET end_time = ?, current_capital = ?, total_trades = ?, 
                triggered_conditions = ?, status = 'completed'
            WHERE session_id = ?
            """, (
                datetime.now().isoformat(),
                portfolio['total_value'],
                len(trades),
                json.dumps(triggered_conditions),
                session_id
            ))
            
            # 거래 로그 저장
            for trade in trades:
                cursor.execute("""
                INSERT INTO simulation_trades 
                (trade_id, session_id, timestamp, action, price, quantity, amount, 
                 trigger_name, trigger_condition, profit_rate, portfolio_value, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"trade_{uuid.uuid4().hex[:8]}",
                    session_id,
                    trade['timestamp'],
                    trade['action'],
                    trade['price'],
                    trade['quantity'],
                    trade['amount'],
                    trade.get('trigger_name', ''),
                    trade.get('trigger_condition', ''),
                    trade.get('profit_rate', 0),
                    trade.get('portfolio_value', 0),
                    trade.get('reason', '')
                ))
            
            conn.commit()
            conn.close()
            
            # 결과 반환
            result = {
                'session_id': session_id,
                'scenario': scenario_name,
                'initial_capital': initial_capital,
                'final_capital': portfolio['total_value'],
                'total_return_percent': final_return,
                'total_trades': len(trades),
                'triggered_conditions': len(triggered_conditions),
                'portfolio': portfolio,
                'trades': trades[-5:] if trades else [],  # 최근 5개 거래만
                'status': 'completed'
            }
            
            logging.info(f"✅ 시뮬레이션 완료: {session_id}")
            logging.info(f"💰 최종 수익률: {final_return:.2f}%")
            logging.info(f"📊 총 거래 수: {len(trades)}개")
            
            return result
            
        except Exception as e:
            logging.error(f"❌ 시뮬레이션 실행 실패: {e}")
            return {"error": str(e)}
    
    def check_trigger_condition(self, trigger: Dict, market_state: Dict, portfolio: Dict) -> bool:
        """
        트리거 조건 확인
        
        Args:
            trigger: 트리거 정보
            market_state: 현재 시장 상황
            portfolio: 포트폴리오 상태
            
        Returns:
            bool: 조건 만족 여부
        """
        try:
            condition_logic = trigger.get('condition_logic', {})
            
            # RSI 30 이하 조건 확인
            if 'rsi_threshold' in condition_logic:
                threshold = condition_logic['rsi_threshold']
                if market_state['rsi_14'] <= threshold:
                    return True
            
            # 골든크로스 조건 확인 (20일선이 60일선 위로)
            if 'ma_cross' in condition_logic:
                if (market_state['sma_20'] > market_state['sma_60'] and 
                    condition_logic['ma_cross'] == 'golden'):
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"❌ 조건 확인 실패: {e}")
            return False
    
    def execute_trigger_action(self, trigger: Dict, market_state: Dict, 
                             portfolio: Dict, timestamp: str) -> Optional[Dict]:
        """
        트리거 액션 실행
        
        Args:
            trigger: 트리거 정보
            market_state: 현재 시장 상황
            portfolio: 포트폴리오 상태
            timestamp: 실행 시간
            
        Returns:
            Dict: 거래 결과
        """
        try:
            action_config = trigger.get('action_config', {})
            current_price = market_state['current_price']
            
            # 시장가 매수 액션
            if action_config.get('action_type') == 'market_buy':
                buy_amount = action_config.get('amount', 100000)  # 기본 10만원
                
                if portfolio['cash'] >= buy_amount:
                    quantity = buy_amount / current_price
                    
                    # 포트폴리오 업데이트
                    if portfolio['btc_quantity'] > 0:
                        # 평균 단가 재계산
                        total_quantity = portfolio['btc_quantity'] + quantity
                        total_cost = (portfolio['btc_quantity'] * portfolio['btc_avg_price']) + buy_amount
                        portfolio['btc_avg_price'] = total_cost / total_quantity
                    else:
                        portfolio['btc_avg_price'] = current_price
                    
                    portfolio['btc_quantity'] += quantity
                    portfolio['cash'] -= buy_amount
                    
                    return {
                        'timestamp': timestamp,
                        'action': 'BUY',
                        'price': current_price,
                        'quantity': quantity,
                        'amount': buy_amount,
                        'trigger_name': trigger['name'],
                        'trigger_condition': json.dumps(trigger.get('condition_logic', {})),
                        'portfolio_value': portfolio['cash'] + (portfolio['btc_quantity'] * current_price),
                        'reason': f"{trigger['name']} 조건 만족"
                    }
            
            return None
            
        except Exception as e:
            logging.error(f"❌ 액션 실행 실패: {e}")
            return None

def test_simulation():
    """시뮬레이션 테스트 함수"""
    print("🕐 시뮬레이션 테스트 시작:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    try:
        # 시뮬레이션 엔진 초기화
        engine = RealDataSimulationEngine()
        
        # 상승 시나리오로 시뮬레이션 데이터 준비
        session_id = engine.prepare_simulation_data("📈 상승", 0)
        
        if session_id:
            # 시뮬레이션 실행
            result = engine.run_simulation(session_id)
            
            print("\n🎯 === 시뮬레이션 결과 ===")
            print(f"📊 세션 ID: {result.get('session_id', 'N/A')}")
            print(f"🎭 시나리오: {result.get('scenario', 'N/A')}")
            print(f"💰 초기 자본: {result.get('initial_capital', 0):,.0f}원")
            print(f"💎 최종 자본: {result.get('final_capital', 0):,.0f}원")
            print(f"📈 총 수익률: {result.get('total_return_percent', 0):.2f}%")
            print(f"🔄 총 거래 수: {result.get('total_trades', 0)}개")
            print(f"⚡ 트리거 발동: {result.get('triggered_conditions', 0)}회")
            
            if result.get('trades'):
                print("\n📋 최근 거래 내역:")
                for trade in result['trades'][-3:]:
                    print(f"  • {trade['timestamp'][:16]} - {trade['action']} {trade['quantity']:.6f} BTC @ {trade['price']:,.0f}원")
        else:
            print("❌ 시뮬레이션 데이터 준비 실패")
        
        print(f"\n✅ 테스트 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

if __name__ == "__main__":
    test_simulation()
