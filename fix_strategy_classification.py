#!/usr/bin/env python3
"""
전략 분류 및 DB 수정 스크립트
- trading_strategies 테이블에 signal_type 컬럼 추가
- 기존 전략들을 타입별로 분류
- 관리 전략 예제 추가
"""

import sqlite3
import json
from datetime import datetime

def add_signal_type_column(db_file):
    """signal_type 컬럼 추가"""
    print(f"\n=== {db_file}에 signal_type 컬럼 추가 ===")
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # signal_type 컬럼이 이미 있는지 확인
        cursor.execute("PRAGMA table_info(trading_strategies)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'signal_type' not in columns:
            # signal_type 컬럼 추가
            cursor.execute("ALTER TABLE trading_strategies ADD COLUMN signal_type TEXT DEFAULT 'BUY/SELL'")
            print("✅ signal_type 컬럼 추가 완료")
        else:
            print("✅ signal_type 컬럼이 이미 존재합니다")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 컬럼 추가 실패: {e}")
        return False

def classify_existing_strategies(db_file):
    """기존 전략들을 타입별로 분류"""
    print(f"\n=== 기존 전략 분류 ===")
    
    # 진입 전략 타입들
    entry_strategy_types = [
        '이동평균 교차', 'RSI 과매수/과매도', '볼린저 밴드',
        '변동성 돌파', 'MACD 교차', '스토캐스틱'
    ]
    
    # 관리 전략 타입들
    management_strategy_types = [
        '고정 손절', '트레일링 스탑', '목표 익절', '부분 익절',
        '시간 기반 청산', '변동성 기반 관리'
    ]
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 모든 전략 조회
        cursor.execute("SELECT strategy_id, name, strategy_type, signal_type FROM trading_strategies")
        strategies = cursor.fetchall()
        
        updated_count = 0
        for strategy_id, name, strategy_type, current_signal_type in strategies:
            new_signal_type = None
            
            # 전략 타입에 따라 signal_type 결정
            if strategy_type in entry_strategy_types:
                new_signal_type = 'BUY/SELL'
            elif strategy_type in management_strategy_types:
                new_signal_type = 'MANAGEMENT'
            else:
                # 이름에서 추론 시도
                if any(mgmt_type in name for mgmt_type in ['손절', '스탑', '익절', '청산', '관리']):
                    new_signal_type = 'MANAGEMENT'
                else:
                    new_signal_type = 'BUY/SELL'
            
            # signal_type 업데이트 (현재 값이 다른 경우만)
            if current_signal_type != new_signal_type:
                cursor.execute(
                    "UPDATE trading_strategies SET signal_type = ? WHERE strategy_id = ?",
                    (new_signal_type, strategy_id)
                )
                updated_count += 1
                print(f"📝 {name}: {current_signal_type or 'None'} → {new_signal_type}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ {updated_count}개 전략 분류 완료")
        return True
        
    except Exception as e:
        print(f"❌ 전략 분류 실패: {e}")
        return False

def add_management_strategy_examples(db_file):
    """관리 전략 예제 추가"""
    print(f"\n=== 관리 전략 예제 추가 ===")
    
    management_examples = [
        {
            'strategy_id': 'mgmt_fixed_stop_01',
            'name': '고정 손절 (예제)',
            'strategy_type': '고정 손절',
            'signal_type': 'MANAGEMENT',
            'parameters': '{"stop_loss_percent": 5.0, "enabled": true}',
            'description': '진입가 대비 일정 비율 하락 시 손절'
        },
        {
            'strategy_id': 'mgmt_trailing_stop_01',
            'name': '트레일링 스탑 (예제)',
            'strategy_type': '트레일링 스탑',
            'signal_type': 'MANAGEMENT',
            'parameters': '{"trailing_percent": 3.0, "min_profit_percent": 2.0, "enabled": true}',
            'description': '수익 발생 후 일정 비율 하락 시 매도'
        },
        {
            'strategy_id': 'mgmt_target_profit_01',
            'name': '목표 익절 (예제)',
            'strategy_type': '목표 익절',
            'signal_type': 'MANAGEMENT',
            'parameters': '{"target_profit_percent": 10.0, "enabled": true}',
            'description': '목표 수익률 달성 시 전량 매도'
        },
        {
            'strategy_id': 'mgmt_partial_profit_01',
            'name': '부분 익절 (예제)',
            'strategy_type': '부분 익절',
            'signal_type': 'MANAGEMENT',
            'parameters': '{"first_target": 5.0, "first_sell_ratio": 0.3, "second_target": 10.0, "second_sell_ratio": 0.5, "enabled": true}',
            'description': '구간별 수익률 달성 시 일부 매도'
        },
        {
            'strategy_id': 'mgmt_time_exit_01',
            'name': '시간 기반 청산 (예제)',
            'strategy_type': '시간 기반 청산',
            'signal_type': 'MANAGEMENT',
            'parameters': '{"max_hold_hours": 24, "force_close": true, "enabled": true}',
            'description': '일정 시간 보유 후 강제 청산'
        },
        {
            'strategy_id': 'mgmt_volatility_01',
            'name': '변동성 기반 관리 (예제)',
            'strategy_type': '변동성 기반 관리',
            'signal_type': 'MANAGEMENT',
            'parameters': '{"volatility_threshold": 0.05, "position_reduce_ratio": 0.5, "enabled": true}',
            'description': '변동성 급증 시 포지션 축소'
        }
    ]
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 기존 관리 전략 개수 확인
        cursor.execute("SELECT COUNT(*) FROM trading_strategies WHERE signal_type = 'MANAGEMENT'")
        existing_mgmt_count = cursor.fetchone()[0]
        
        print(f"📋 기존 관리 전략: {existing_mgmt_count}개")
        
        # 새로 추가할 예제들 확인
        added_count = 0
        current_time = datetime.now().isoformat()
        
        for example in management_examples:
            # 중복 확인 (strategy_id 기준)
            cursor.execute(
                "SELECT COUNT(*) FROM trading_strategies WHERE strategy_id = ?",
                (example['strategy_id'],)
            )
            
            if cursor.fetchone()[0] == 0:
                # 새 관리 전략 추가
                cursor.execute("""
                    INSERT INTO trading_strategies 
                    (strategy_id, name, strategy_type, signal_type, parameters, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    example['strategy_id'],
                    example['name'],
                    example['strategy_type'],
                    example['signal_type'],
                    example['parameters'],
                    example['description'],
                    current_time,
                    current_time
                ))
                added_count += 1
                print(f"➕ {example['name']} 추가")
            else:
                print(f"⏭️ {example['name']} 이미 존재")
        
        conn.commit()
        conn.close()
        
        print(f"✅ 관리 전략 {added_count}개 추가 완료")
        return True
        
    except Exception as e:
        print(f"❌ 관리 전략 추가 실패: {e}")
        return False

def show_strategy_summary(db_file):
    """전략 요약 정보 출력"""
    print(f"\n=== 전략 요약 ===")
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 전략 타입별 개수
        cursor.execute("""
            SELECT signal_type, COUNT(*) as count
            FROM trading_strategies 
            GROUP BY signal_type
            ORDER BY signal_type
        """)
        
        type_counts = cursor.fetchall()
        for signal_type, count in type_counts:
            print(f"📊 {signal_type}: {count}개")
        
        # 각 타입별 전략 목록
        for signal_type, count in type_counts:
            print(f"\n📋 {signal_type} 전략 목록:")
            cursor.execute("""
                SELECT name, strategy_type 
                FROM trading_strategies 
                WHERE signal_type = ?
                ORDER BY created_at
            """, (signal_type,))
            
            strategies = cursor.fetchall()
            for i, (name, strategy_type) in enumerate(strategies, 1):
                print(f"   {i}. {name} ({strategy_type})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 요약 정보 조회 실패: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🔧 전략 분류 및 DB 수정 도구")
    print("=" * 60)
    
    db_file = 'data/upbit_auto_trading.sqlite3'
    
    # 1. signal_type 컬럼 추가
    if not add_signal_type_column(db_file):
        print("❌ signal_type 컬럼 추가 실패. 종료합니다.")
        return
    
    # 2. 기존 전략들 분류
    if not classify_existing_strategies(db_file):
        print("❌ 기존 전략 분류 실패")
        return
    
    # 3. 관리 전략 예제 추가
    if not add_management_strategy_examples(db_file):
        print("❌ 관리 전략 예제 추가 실패")
        return
    
    # 4. 결과 요약
    show_strategy_summary(db_file)
    
    print("\n" + "=" * 60)
    print("🎉 전략 분류 및 DB 수정 완료!")
    print("=" * 60)
    print("💡 이제 UI에서 전략이 올바른 탭에 표시될 것입니다.")

if __name__ == "__main__":
    main()
