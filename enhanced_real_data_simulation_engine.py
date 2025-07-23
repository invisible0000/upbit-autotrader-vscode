"""
확장된 실제 데이터 기반 시뮬레이션 엔진
- 2017-2025년 KRW-BTC 데이터 활용
- 다양한 시나리오(상승, 하락, 급등, 급락, 횡보, 크로스) 지원
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
from extended_data_scenario_mapper import ExtendedDataScenarioMapper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EnhancedRealDataSimulationEngine:
    def __init__(self, unified_db_path: str = "upbit_trading_unified.db", 
                 data_db_path: str = "data/upbit_auto_trading.sqlite3"):
        """
        향상된 실제 데이터 기반 시뮬레이션 엔진 초기화
        
        Args:
            unified_db_path: 통합 DB 경로 (트리거 정보)
            data_db_path: 실제 시장 데이터 DB 경로
        """
        self.unified_db_path = unified_db_path
        self.data_db_path = data_db_path
        self.mapper = ExtendedDataScenarioMapper(data_db_path)
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
            
            # 기존 테이블 삭제 후 재생성
            cursor.execute("DROP TABLE IF EXISTS simulation_market_data")
            cursor.execute("DROP TABLE IF EXISTS simulation_trades")
            cursor.execute("DROP TABLE IF EXISTS simulation_sessions")
            
            # 시뮬레이션 세션 테이블 재생성
            cursor.execute("""
            CREATE TABLE simulation_sessions (
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
            CREATE TABLE simulation_market_data (
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
                volatility_30d REAL,
                return_7d REAL,
                return_30d REAL,
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
            
            logging.info("✅ 향상된 시뮬레이션 테이블 초기화 완료")
            
        except Exception as e:
            logging.error(f"❌ 시뮬레이션 테이블 초기화 실패: {e}")
    
    def load_simple_test_triggers(self) -> List[Dict]:
        """
        간단한 테스트용 트리거 생성 (DB 의존성 제거)
        
        Returns:
            List[Dict]: 테스트용 트리거 정보
        """
        test_triggers = [
            {
                'trigger_id': 'test_rsi_oversold',
                'name': 'RSI 과매도 매수',
                'description': 'RSI 40 이하일 때 매수',  # 35 -> 40으로 더 완화
                'condition_logic': {'rsi_threshold': 40, 'condition_type': 'rsi_oversold'},
                'action_config': {'action_type': 'market_buy', 'amount': 100000},
                'is_active': True
            },
            {
                'trigger_id': 'test_rsi_overbought',
                'name': 'RSI 과매수 매도',
                'description': 'RSI 60 이상일 때 매도',  # 65 -> 60으로 더 완화
                'condition_logic': {'rsi_threshold': 60, 'condition_type': 'rsi_overbought'},
                'action_config': {'action_type': 'market_sell', 'ratio': 0.5},
                'is_active': True
            },
            {
                'trigger_id': 'test_golden_cross',
                'name': '골든크로스 매수',
                'description': '20일선이 60일선을 상향 돌파시 매수',
                'condition_logic': {'ma_cross': 'golden', 'condition_type': 'ma_cross'},
                'action_config': {'action_type': 'market_buy', 'amount': 150000},
                'is_active': True
            },
            {
                'trigger_id': 'test_dead_cross',
                'name': '데드크로스 매도',
                'description': '20일선이 60일선을 하향 돌파시 매도',
                'condition_logic': {'ma_cross': 'dead', 'condition_type': 'ma_cross'},
                'action_config': {'action_type': 'market_sell', 'ratio': 0.3},
                'is_active': True
            },
            {
                'trigger_id': 'test_profit_taking',
                'name': '수익 실현',
                'description': '5% 수익 달성시 30% 매도',  # 10% -> 5%로 더 완화
                'condition_logic': {'profit_threshold': 5, 'condition_type': 'profit_target'},
                'action_config': {'action_type': 'market_sell', 'ratio': 0.3},
                'is_active': True
            },
            {
                'trigger_id': 'test_stop_loss',
                'name': '손절매',
                'description': '5% 손실 발생시 전량 매도',  # 7% -> 5%로 더 완화
                'condition_logic': {'loss_threshold': -5, 'condition_type': 'stop_loss'},
                'action_config': {'action_type': 'market_sell', 'ratio': 1.0},
                'is_active': True
            }
        ]
        
        logging.info(f"✅ 테스트 트리거 로드: {len(test_triggers)}개")
        return test_triggers
    
    def prepare_enhanced_simulation_data(self, scenario: str, segment_index: int = 0) -> Optional[str]:
        """
        향상된 시나리오 기반 시뮬레이션 데이터 준비
        
        Args:
            scenario: 시나리오 이름 (예: "📉 하락")
            segment_index: 세그먼트 인덱스 (0부터 시작)
            
        Returns:
            str: 생성된 시뮬레이션 세션 ID
        """
        try:
            # 시나리오 세그먼트 가져오기
            all_scenarios = self.mapper.generate_all_extended_scenarios()
            
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
            df = self.mapper.load_daily_market_data()
            df = self.mapper.calculate_daily_technical_indicators(df)
            
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
                 rsi_14, sma_20, sma_60, volatility_30d, return_7d, return_30d, profit_rate, is_processed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    float(row['volatility_30d']) if not pd.isna(row['volatility_30d']) else None,
                    float(row['return_7d']) if not pd.isna(row['return_7d']) else None,
                    float(row['return_30d']) if not pd.isna(row['return_30d']) else None,
                    float(profit_rate),
                    0
                ))
            
            conn.commit()
            conn.close()
            
            logging.info(f"✅ 향상된 시뮬레이션 데이터 준비 완료: {session_id}")
            logging.info(f"📊 데이터 기간: {segment['start_time'].strftime('%Y-%m-%d')} ~ {segment['end_time'].strftime('%Y-%m-%d')}")
            logging.info(f"📈 데이터 포인트: {len(segment_data)}개")
            
            # 세그먼트 상세 정보 출력
            if 'return_pct' in segment:
                logging.info(f"💰 예상 수익률: {segment['return_pct']:.2f}%")
            if 'start_price' in segment and 'end_price' in segment:
                logging.info(f"💸 가격 변화: {segment['start_price']:,.0f}원 → {segment.get('end_price', 0):,.0f}원")
            
            return session_id
            
        except Exception as e:
            logging.error(f"❌ 향상된 시뮬레이션 데이터 준비 실패: {e}")
            return None
    
    def run_enhanced_simulation(self, session_id: str) -> Dict[str, Any]:
        """
        향상된 시뮬레이션 실행
        
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
            
            # 테스트 트리거 로드
            triggers = self.load_simple_test_triggers()
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
                'total_value': float(current_capital),
                'max_value': float(current_capital),
                'max_drawdown': 0.0
            }
            
            triggered_conditions = []
            trades = []
            previous_ma_cross_state = None
            
            # 차트 데이터 수집용
            price_data = []
            trigger_results = []
            
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
                
                # 포트폴리오 수익률 계산
                if portfolio['btc_quantity'] > 0:
                    position_profit_rate = (float(close) / portfolio['btc_avg_price'] - 1) * 100
                else:
                    position_profit_rate = 0.0
                
                market_state['position_profit_rate'] = position_profit_rate
                
                # 현재 가격 데이터 수집
                price_data.append(float(close))
                
                # 트리거 발동 여부 초기화
                any_trigger_fired = False
                
                # 각 트리거 조건 확인
                for trigger in triggers:
                    trigger_fired = False
                    
                    if trigger['condition_logic']['condition_type'] == 'rsi_oversold':
                        # RSI 과매도 조건 (더 관대하게 설정)
                        if market_state['rsi_14'] <= trigger['condition_logic']['rsi_threshold'] and portfolio['btc_quantity'] == 0:
                            trigger_fired = True
                            logging.info(f"🔥 RSI 과매도 트리거 발동: RSI {market_state['rsi_14']:.1f}")
                    
                    elif trigger['condition_logic']['condition_type'] == 'rsi_overbought':
                        # RSI 과매수 조건
                        if market_state['rsi_14'] >= trigger['condition_logic']['rsi_threshold'] and portfolio['btc_quantity'] > 0:
                            trigger_fired = True
                            logging.info(f"🔥 RSI 과매수 트리거 발동: RSI {market_state['rsi_14']:.1f}")
                    
                    elif trigger['condition_logic']['condition_type'] == 'ma_cross':
                        # 골든크로스 감지 (20일선이 60일선을 상향 돌파)
                        current_cross_state = 'golden' if market_state['sma_20'] > market_state['sma_60'] else 'dead'
                        
                        if (trigger['condition_logic']['ma_cross'] == 'golden' and 
                            market_state['sma_20'] > market_state['sma_60'] and 
                            previous_ma_cross_state == 'dead' and
                            portfolio['btc_quantity'] == 0):
                            trigger_fired = True
                            logging.info(f"🔥 골든크로스 트리거 발동: SMA20({market_state['sma_20']:,.0f}) > SMA60({market_state['sma_60']:,.0f})")
                        
                        elif (trigger['condition_logic']['ma_cross'] == 'dead' and 
                              market_state['sma_20'] < market_state['sma_60'] and 
                              previous_ma_cross_state == 'golden' and
                              portfolio['btc_quantity'] > 0):
                            trigger_fired = True
                            logging.info(f"🔥 데드크로스 트리거 발동: SMA20({market_state['sma_20']:,.0f}) < SMA60({market_state['sma_60']:,.0f})")
                        
                        # 현재 상태 업데이트
                        previous_ma_cross_state = current_cross_state
                    
                    elif trigger['condition_logic']['condition_type'] == 'profit_target':
                        # 수익 실현 조건
                        if (portfolio['btc_quantity'] > 0 and 
                            position_profit_rate >= trigger['condition_logic']['profit_threshold']):
                            trigger_fired = True
                            logging.info(f"🔥 수익 실현 트리거 발동: 수익률 {position_profit_rate:.1f}%")
                    
                    elif trigger['condition_logic']['condition_type'] == 'stop_loss':
                        # 손절매 조건
                        if (portfolio['btc_quantity'] > 0 and 
                            position_profit_rate <= trigger['condition_logic']['loss_threshold']):
                            trigger_fired = True
                            logging.info(f"🔥 손절매 트리거 발동: 손실률 {position_profit_rate:.1f}%")
                    
                    if trigger_fired:
                        # 트리거 실행
                        trade_result = self.execute_enhanced_trigger_action(
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
                
                # 최대 가치 및 최대 손실 업데이트
                if portfolio['total_value'] > portfolio['max_value']:
                    portfolio['max_value'] = portfolio['total_value']
                
                current_drawdown = (portfolio['total_value'] / portfolio['max_value'] - 1) * 100
                if current_drawdown < portfolio['max_drawdown']:
                    portfolio['max_drawdown'] = current_drawdown
                
                # 진행률 표시 (10단계로)
                if i > 0 and i % max(1, len(market_data) // 10) == 0:
                    progress = (i / len(market_data)) * 100
                    logging.info(f"📊 시뮬레이션 진행률: {progress:.0f}% (가치: {portfolio['total_value']:,.0f}원)")
            
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
                'max_drawdown_percent': portfolio['max_drawdown'],
                'total_trades': len(trades),
                'triggered_conditions': len(triggered_conditions),
                'portfolio': portfolio,
                'trades': trades[-5:] if trades else [],  # 최근 5개 거래만
                'status': 'completed'
            }
            
            logging.info(f"✅ 향상된 시뮬레이션 완료: {session_id}")
            logging.info(f"💰 최종 수익률: {final_return:.2f}%")
            logging.info(f"📉 최대 손실률: {portfolio['max_drawdown']:.2f}%")
            logging.info(f"📊 총 거래 수: {len(trades)}개")
            
            return result
            
        except Exception as e:
            logging.error(f"❌ 향상된 시뮬레이션 실행 실패: {e}")
            return {"error": str(e)}
    
    def execute_enhanced_trigger_action(self, trigger: Dict, market_state: Dict, 
                                      portfolio: Dict, timestamp: str) -> Optional[Dict]:
        """
        향상된 트리거 액션 실행
        
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
            
            # 시장가 매도 액션
            elif action_config.get('action_type') == 'market_sell':
                sell_ratio = action_config.get('ratio', 1.0)  # 기본 전량 매도
                
                if portfolio['btc_quantity'] > 0:
                    sell_quantity = portfolio['btc_quantity'] * sell_ratio
                    sell_amount = sell_quantity * current_price
                    
                    # 포트폴리오 업데이트
                    portfolio['btc_quantity'] -= sell_quantity
                    portfolio['cash'] += sell_amount
                    
                    if portfolio['btc_quantity'] <= 0.000001:  # 잔량 정리
                        portfolio['btc_quantity'] = 0
                        portfolio['btc_avg_price'] = 0
                    
                    return {
                        'timestamp': timestamp,
                        'action': 'SELL',
                        'price': current_price,
                        'quantity': sell_quantity,
                        'amount': sell_amount,
                        'trigger_name': trigger['name'],
                        'trigger_condition': json.dumps(trigger.get('condition_logic', {})),
                        'portfolio_value': portfolio['cash'] + (portfolio['btc_quantity'] * current_price),
                        'reason': f"{trigger['name']} 조건 만족"
                    }
            
            return None
            
        except Exception as e:
            logging.error(f"❌ 향상된 액션 실행 실패: {e}")
            return None

def test_enhanced_simulation():
    """향상된 시뮬레이션 테스트 함수"""
    print("🕐 향상된 시뮬레이션 테스트 시작:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    try:
        # 향상된 시뮬레이션 엔진 초기화
        engine = EnhancedRealDataSimulationEngine()
        
        # 다양한 시나리오 테스트
        test_scenarios = ["📈 상승", "📉 하락", "🚀 급등", "💥 급락", "➡️ 횡보"]
        
        for scenario in test_scenarios:
            print(f"\n🎭 === {scenario} 시나리오 테스트 ===")
            
            # 시뮬레이션 데이터 준비
            session_id = engine.prepare_enhanced_simulation_data(scenario, 0)
            
            if session_id:
                # 시뮬레이션 실행
                result = engine.run_enhanced_simulation(session_id)
                
                if 'error' not in result:
                    print(f"📊 세션 ID: {result.get('session_id', 'N/A')}")
                    print(f"💰 초기 자본: {result.get('initial_capital', 0):,.0f}원")
                    print(f"💎 최종 자본: {result.get('final_capital', 0):,.0f}원")
                    print(f"📈 총 수익률: {result.get('total_return_percent', 0):.2f}%")
                    print(f"📉 최대 손실률: {result.get('max_drawdown_percent', 0):.2f}%")
                    print(f"🔄 총 거래 수: {result.get('total_trades', 0)}개")
                    print(f"⚡ 트리거 발동: {result.get('triggered_conditions', 0)}회")
                else:
                    print(f"❌ 시뮬레이션 실패: {result['error']}")
            else:
                print(f"❌ {scenario} 시나리오 데이터 준비 실패")
            
            print("-" * 50)
        
        print(f"\n✅ 향상된 시뮬레이션 테스트 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

if __name__ == "__main__":
    test_enhanced_simulation()
