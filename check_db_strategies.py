#!/usr/bin/env python3
"""
DB에 저장된 전략 데이터 확인 스크립트
"""
import sqlite3
import json
from datetime import datetime
import os

def check_db_strategies():
    """DB에 저장된 전략들 확인"""
    db_path = 'data/upbit_auto_trading.db'
    
    if not os.path.exists(db_path):
        print(f"❌ DB 파일이 존재하지 않습니다: {db_path}")
        return
    
    try:
        # DB 연결
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 구조 확인
        print('=== 테이블 구조 ===')
        cursor.execute("PRAGMA table_info(trading_strategies)")
        columns = cursor.fetchall()
        for col in columns:
            print(f'{col[1]}: {col[2]}')
        
        print('\n=== 저장된 전략 데이터 ===')
        cursor.execute('SELECT strategy_id, name, strategy_type, parameters, description, created_at FROM trading_strategies ORDER BY created_at DESC')
        strategies = cursor.fetchall()
        
        if not strategies:
            print("DB에 저장된 전략이 없습니다.")
            return
        
        print(f"총 {len(strategies)}개의 전략이 저장되어 있습니다.\n")
        
        entry_count = 0
        management_count = 0
        
        for i, strategy in enumerate(strategies):
            print(f'{i+1}. ID: {strategy[0][:8]}...')
            print(f'   이름: {strategy[1]}')
            print(f'   타입: {strategy[2]}')
            print(f'   설명: {strategy[4]}')
            print(f'   생성일: {strategy[5]}')
            
            # 파라미터 파싱
            try:
                params = json.loads(strategy[3]) if strategy[3] else {}
                print(f'   파라미터: {params}')
            except Exception as e:
                print(f'   파라미터(JSON 파싱 실패): {strategy[3]}')
                print(f'   파싱 오류: {e}')
            
            # 전략 타입별 카운트
            strategy_type = strategy[2]
            entry_types = ["이동평균 교차", "RSI 과매수/과매도", "볼린저 밴드", "변동성 돌파", "MACD 교차", "스토캐스틱"]
            management_types = ["고정 손절", "트레일링 스탑", "목표 익절", "부분 익절", "시간 기반 청산", "변동성 기반 관리"]
            
            if strategy_type in entry_types:
                entry_count += 1
                print(f'   📈 진입 전략')
            elif strategy_type in management_types:
                management_count += 1
                print(f'   🛡️ 관리 전략')
            else:
                print(f'   ❓ 미분류 전략')
            
            print()
        
        print(f'=== 전략 타입별 통계 ===')
        print(f'📈 진입 전략: {entry_count}개')
        print(f'🛡️ 관리 전략: {management_count}개')
        print(f'총합: {len(strategies)}개')
        
        conn.close()
        
    except Exception as e:
        print(f"❌ DB 확인 중 오류 발생: {e}")

def clean_db_strategies():
    """DB에서 잘못된 전략들 정리"""
    db_path = 'data/upbit_auto_trading.db'
    
    if not os.path.exists(db_path):
        print(f"❌ DB 파일이 존재하지 않습니다: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 진입 전략 타입들
        entry_types = ["이동평균 교차", "RSI 과매수/과매도", "볼린저 밴드", "변동성 돌파", "MACD 교차", "스토캐스틱"]
        # 관리 전략 타입들  
        management_types = ["고정 손절", "트레일링 스탑", "목표 익절", "부분 익절", "시간 기반 청산", "변동성 기반 관리"]
        
        # 잘못된 전략들 찾기 (관리 전략이 진입 전략으로 분류된 경우)
        cursor.execute('SELECT strategy_id, name, strategy_type FROM trading_strategies')
        strategies = cursor.fetchall()
        
        wrong_strategies = []
        for strategy in strategies:
            strategy_id, name, strategy_type = strategy
            
            # 관리 전략 타입인데 이름이 관리 전략 패턴이 아닌 경우 확인
            if strategy_type in management_types:
                print(f"관리 전략 발견: {name} ({strategy_type})")
            elif strategy_type in entry_types:
                # 이름에 관리 전략 키워드가 포함된 경우
                for mgmt_type in management_types:
                    if mgmt_type in name:
                        wrong_strategies.append((strategy_id, name, strategy_type, mgmt_type))
                        break
        
        if wrong_strategies:
            print(f"\n잘못 분류된 전략들 ({len(wrong_strategies)}개):")
            for strategy_id, name, wrong_type, correct_type in wrong_strategies:
                print(f"  - {name}: {wrong_type} → {correct_type}")
            
            response = input("\n이 전략들을 올바른 타입으로 수정하시겠습니까? (y/N): ")
            if response.lower() == 'y':
                for strategy_id, name, wrong_type, correct_type in wrong_strategies:
                    cursor.execute('UPDATE trading_strategies SET strategy_type = ? WHERE strategy_id = ?', 
                                 (correct_type, strategy_id))
                    print(f"✅ {name}: {wrong_type} → {correct_type}")
                
                conn.commit()
                print(f"\n✅ {len(wrong_strategies)}개 전략의 타입이 수정되었습니다.")
        else:
            print("잘못 분류된 전략이 없습니다.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ DB 정리 중 오류 발생: {e}")

if __name__ == "__main__":
    print("=== 전략 DB 상태 확인 ===")
    check_db_strategies()
    
    print("\n" + "="*50)
    clean_db_strategies()
