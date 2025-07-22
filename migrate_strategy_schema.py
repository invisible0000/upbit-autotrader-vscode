#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Strategy 테이블 스키마 마이그레이션
원래 개발 문서에 정의된 전략 성질 추가:
- signal_type: BUY_SELL, STOP_LOSS, TRAILING, TAKE_PROFIT, PARTIAL_EXIT, TIME_EXIT, VOLATILITY
- position_required: 포지션 보유 필요 여부
- role: ENTRY, EXIT, SCALE_OUT, MANAGEMENT  
- market_phase: ALL, TREND, VOLATILE, SIDEWAYS
- risk_level: LOW, MEDIUM, HIGH
"""

import sqlite3
import json
from datetime import datetime

def migrate_strategy_schema():
    """Strategy 테이블에 전략 성질 컬럼들 추가"""
    db_path = "data/upbit_auto_trading.sqlite3"
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Strategy 테이블 스키마 마이그레이션 시작...")
        
        # 기존 컬럼 확인
        cursor.execute("PRAGMA table_info(strategy)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 기존 컬럼: {columns}")
        
        # 전략 타입별 성질 매핑
        strategy_properties = {
            # 진입 전략들
            "moving_average_cross": {
                "signal_type": "BUY_SELL",
                "role": "ENTRY", 
                "position_required": False,
                "market_phase": "TREND",
                "risk_level": "MEDIUM"
            },
            "rsi_reversal": {
                "signal_type": "BUY_SELL", 
                "role": "ENTRY",
                "position_required": False,
                "market_phase": "SIDEWAYS", 
                "risk_level": "MEDIUM"
            },
            "bollinger_band_mean_reversion": {
                "signal_type": "BUY_SELL",
                "role": "ENTRY",
                "position_required": False,
                "market_phase": "VOLATILE",
                "risk_level": "MEDIUM"
            },
            "volatility_breakout": {
                "signal_type": "BUY_SELL",
                "role": "ENTRY", 
                "position_required": False,
                "market_phase": "VOLATILE",
                "risk_level": "HIGH"
            },
            "macd_cross": {
                "signal_type": "BUY_SELL",
                "role": "ENTRY",
                "position_required": False, 
                "market_phase": "TREND",
                "risk_level": "MEDIUM"
            },
            "stochastic": {
                "signal_type": "BUY_SELL",
                "role": "ENTRY",
                "position_required": False,
                "market_phase": "SIDEWAYS",
                "risk_level": "MEDIUM"  
            },
            
            # 증액 전략들 (피라미딩)
            "upward_pyramiding": {
                "signal_type": "ADD_BUY",
                "role": "SCALE_IN",
                "position_required": True,
                "market_phase": "TREND",
                "risk_level": "HIGH"
            },
            "downward_averaging": {
                "signal_type": "ADD_BUY", 
                "role": "SCALE_IN",
                "position_required": True,
                "market_phase": "VOLATILE",
                "risk_level": "VERY_HIGH"
            },
            
            # 관리 전략들
            "fixed_stop_loss": {
                "signal_type": "STOP_LOSS",
                "role": "EXIT",
                "position_required": True,
                "market_phase": "ALL", 
                "risk_level": "LOW"
            },
            "trailing_stop": {
                "signal_type": "TRAILING",
                "role": "EXIT",
                "position_required": True,
                "market_phase": "ALL",
                "risk_level": "MEDIUM"
            },
            "target_take_profit": {
                "signal_type": "TAKE_PROFIT", 
                "role": "EXIT",
                "position_required": True,
                "market_phase": "ALL",
                "risk_level": "LOW"
            },
            "partial_take_profit": {
                "signal_type": "PARTIAL_EXIT",
                "role": "SCALE_OUT", 
                "position_required": True,
                "market_phase": "ALL",
                "risk_level": "MEDIUM"
            },
            "time_based_exit": {
                "signal_type": "TIME_EXIT",
                "role": "EXIT",
                "position_required": True,
                "market_phase": "ALL", 
                "risk_level": "MEDIUM"
            },
            "volatility_based_management": {
                "signal_type": "VOLATILITY",
                "role": "MANAGEMENT",
                "position_required": True,
                "market_phase": "VOLATILE",
                "risk_level": "HIGH"
            }
        }
        
        # 컬럼 추가
        columns_to_add = [
            ("signal_type", "TEXT", "BUY_SELL"),
            ("role", "TEXT", "ENTRY"), 
            ("position_required", "INTEGER", "0"),
            ("market_phase", "TEXT", "ALL"),
            ("risk_level", "TEXT", "MEDIUM")
        ]
        
        for col_name, col_type, default_value in columns_to_add:
            if col_name not in columns:
                print(f"📝 {col_name} 컬럼 추가 중...")
                cursor.execute(f"ALTER TABLE strategy ADD COLUMN {col_name} {col_type} DEFAULT '{default_value}'")
        
        # 기존 전략들에 성질 적용
        cursor.execute("SELECT id, name, parameters FROM strategy")
        strategies = cursor.fetchall()
        
        for strategy_id, name, parameters_json in strategies:
            try:
                # parameters에서 strategy_type 추출
                parameters = json.loads(parameters_json) if parameters_json else {}
                strategy_type = parameters.get('strategy_type', '')
                
                # 전략 이름에서 타입 추론
                if not strategy_type:
                    if '이동평균' in name or 'moving_average' in name.lower():
                        strategy_type = 'moving_average_cross'
                    elif 'rsi' in name.lower():
                        strategy_type = 'rsi_reversal'
                    elif '볼린저' in name or 'bollinger' in name.lower():
                        strategy_type = 'bollinger_band_mean_reversion'
                    elif '변동성' in name or 'volatility' in name.lower():
                        strategy_type = 'volatility_breakout'
                    elif 'macd' in name.lower():
                        strategy_type = 'macd_cross'
                    elif '스토캐스틱' in name or 'stochastic' in name.lower():
                        strategy_type = 'stochastic'
                    elif '손절' in name or 'stop' in name.lower():
                        strategy_type = 'fixed_stop_loss'
                    elif '트레일링' in name or 'trailing' in name.lower():
                        strategy_type = 'trailing_stop'
                    elif '익절' in name or 'profit' in name.lower():
                        strategy_type = 'target_take_profit'
                    else:
                        strategy_type = 'moving_average_cross'  # 기본값
                
                # 성질 가져오기
                props = strategy_properties.get(strategy_type, strategy_properties['moving_average_cross'])
                
                # DB 업데이트
                cursor.execute("""
                    UPDATE strategy 
                    SET signal_type = ?, role = ?, position_required = ?, 
                        market_phase = ?, risk_level = ?
                    WHERE id = ?
                """, (
                    props['signal_type'], props['role'], props['position_required'],
                    props['market_phase'], props['risk_level'], strategy_id
                ))
                
                print(f"   - {name}: {props['role']} / {props['signal_type']} / 포지션 {'필요' if props['position_required'] else '불필요'}")
                
            except Exception as e:
                print(f"   ❌ {name} 처리 중 오류: {e}")
        
        conn.commit()
        print("✅ Strategy 테이블 마이그레이션 완료")
        
        # 결과 확인
        cursor.execute("SELECT id, name, signal_type, role, position_required, market_phase, risk_level FROM strategy")
        strategies = cursor.fetchall()
        
        print("\n📊 마이그레이션 결과:")
        for strategy_id, name, signal_type, role, position_required, market_phase, risk_level in strategies:
            pos_req = "필요" if position_required else "불필요"
            print(f"   {name}: {role} | {signal_type} | 포지션: {pos_req} | {market_phase} | {risk_level}")
        
    except Exception as e:
        print(f"❌ 마이그레이션 오류: {e}")
        try:
            if conn:
                conn.rollback()
        except:
            pass
    
    finally:
        try:
            if conn:
                conn.close()
        except:
            pass

if __name__ == "__main__":
    migrate_strategy_schema()
