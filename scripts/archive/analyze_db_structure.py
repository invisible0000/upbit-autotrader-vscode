#!/usr/bin/env python3
"""
현재 통합 DB 구조 및 백테스트 준비 상태 분석
"""
import sqlite3
import os
import json
from datetime import datetime

def analyze_database_structure():
    """통합 데이터베이스 구조 분석"""
    print("📊 === 통합 데이터베이스 구조 분석 ===")
    
    if not os.path.exists('upbit_trading_unified.db'):
        print("❌ upbit_trading_unified.db 파일을 찾을 수 없습니다.")
        return
    
    conn = sqlite3.connect('upbit_trading_unified.db')
    cursor = conn.cursor()
    
    # 테이블 목록 조회
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"🔸 총 테이블 수: {len(tables)}개")
    print("=" * 60)
    
    # 각 테이블 상세 정보
    for table_name, in tables:
        print(f"\n📋 테이블: {table_name}")
        print("-" * 40)
        
        # 스키마 정보
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        print("컬럼 구조:")
        for col in columns:
            col_id, name, data_type, not_null, default_val, pk = col
            pk_mark = " (PK)" if pk else ""
            null_mark = " NOT NULL" if not_null else ""
            default_mark = f" DEFAULT {default_val}" if default_val else ""
            print(f"  • {name}: {data_type}{pk_mark}{null_mark}{default_mark}")
        
        # 데이터 수
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"데이터 수: {count}개")
        
        # 샘플 데이터 (최대 3개)
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            samples = cursor.fetchall()
            print("샘플 데이터:")
            for i, sample in enumerate(samples, 1):
                print(f"  {i}. {sample}")
    
    conn.close()

def analyze_backtest_readiness():
    """백테스트 시스템 준비 상태 분석"""
    print("\n🧪 === 백테스트 시스템 준비 상태 분석 ===")
    
    # 백테스트 관련 파일들 확인
    backtest_files = [
        'upbit_auto_trading/business_logic/backtester/backtest_runner.py',
        'upbit_auto_trading/business_logic/strategy/combination_backtest_engine.py',
        'upbit_auto_trading/ui/desktop/screens/backtesting/backtesting_screen.py',
        'database_backtest_engine.py'
    ]
    
    print("🔍 백테스트 관련 파일 확인:")
    for file_path in backtest_files:
        exists = os.path.exists(file_path)
        status = "✅ 존재" if exists else "❌ 없음"
        print(f"  • {file_path}: {status}")
    
    # 시장 데이터 테이블 확인 (백테스트에 필요)
    required_tables = [
        'market_data',     # OHLCV 데이터
        'indicators',      # 기술적 지표 데이터
        'positions',       # 포지션 정보
        'trades',          # 거래 기록
        'portfolios',      # 포트폴리오 상태
    ]
    
    print("\n📊 백테스트 필수 테이블 확인:")
    if os.path.exists('upbit_trading_unified.db'):
        conn = sqlite3.connect('upbit_trading_unified.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        for table in required_tables:
            exists = table in existing_tables
            status = "✅ 존재" if exists else "❌ 없음"
            print(f"  • {table}: {status}")
        
        conn.close()
    else:
        print("❌ 통합 DB 파일이 없어서 확인할 수 없습니다.")

def analyze_variable_definitions():
    """변수 정의 시스템 분석"""
    print("\n🎯 === 변수 정의 시스템 분석 ===")
    
    # 변수 정의 파일들 확인
    variable_files = [
        'components/variable_definitions.py',
        'upbit_auto_trading/ui/desktop/screens/strategy_management/components/variable_definitions.py'
    ]
    
    print("🔍 변수 정의 파일 확인:")
    for file_path in variable_files:
        exists = os.path.exists(file_path)
        status = "✅ 존재" if exists else "❌ 없음"
        print(f"  • {file_path}: {status}")
        
        if exists:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'position' in content.lower():
                        print(f"    📍 포지션 관련 변수 포함")
                    if 'asset' in content.lower() or '자산' in content:
                        print(f"    💰 자산 관련 변수 포함")
                    if 'rsi' in content.lower():
                        print(f"    📈 RSI 지표 변수 포함")
                    if 'sma' in content.lower() or 'moving_average' in content.lower():
                        print(f"    📊 이동평균 변수 포함")
            except Exception as e:
                print(f"    ❌ 파일 읽기 실패: {e}")

def check_simulation_data_needs():
    """시뮬레이션 데이터 요구사항 분석"""
    print("\n🎮 === 시뮬레이션 데이터 요구사항 분석 ===")
    
    # 현재 트리거들의 변수 확인
    if os.path.exists('upbit_trading_unified.db'):
        conn = sqlite3.connect('upbit_trading_unified.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, variable_id, operator, target_value FROM trading_conditions WHERE is_active = 1;")
        conditions = cursor.fetchall()
        
        print("🎯 현재 활성 트리거 변수 분석:")
        variable_types = set()
        
        for name, variable_id, operator, target_value in conditions:
            print(f"  • {name}: {variable_id} {operator} {target_value}")
            
            # 변수 타입 분류
            if variable_id:
                if 'rsi' in variable_id.lower():
                    variable_types.add('RSI 지표')
                elif 'sma' in variable_id.lower() or 'moving' in variable_id.lower():
                    variable_types.add('이동평균')
                elif 'price' in variable_id.lower() or '가격' in variable_id.lower():
                    variable_types.add('가격')
                elif 'volume' in variable_id.lower() or '거래량' in variable_id.lower():
                    variable_types.add('거래량')
                elif 'position' in variable_id.lower() or '포지션' in variable_id.lower():
                    variable_types.add('포지션 상태')
                elif 'asset' in variable_id.lower() or '자산' in variable_id.lower():
                    variable_types.add('자산 정보')
                else:
                    variable_types.add('기타')
        
        print(f"\n📋 필요한 변수 타입들:")
        for var_type in sorted(variable_types):
            print(f"  🔸 {var_type}")
        
        conn.close()
    else:
        print("❌ 통합 DB가 없어서 분석할 수 없습니다.")

def generate_recommendations():
    """시뮬레이션 시스템 구현 권장사항"""
    print("\n💡 === 시뮬레이션 시스템 구현 권장사항 ===")
    
    recommendations = [
        "1. 📊 시장 데이터 모델 표준화",
        "   - OHLCV 데이터 테이블 설계",
        "   - 기술적 지표 계산 결과 저장 구조",
        "   - 실시간 데이터와 백테스트 데이터 호환성",
        "",
        "2. 🎯 변수 시스템 확장",
        "   - 포지션 상태 변수 (수량, 평균단가, 수익률)",
        "   - 자산 정보 변수 (가용 자산, 총 자산, 투자 비율)",
        "   - 기술적 지표 변수 (RSI, SMA, MACD, 볼린저밴드)",
        "",
        "3. 🎮 시뮬레이션 엔진 설계",
        "   - 시나리오별 데이터 생성기",
        "   - 실제 시장과 유사한 캔들 패턴",
        "   - 포지션 상태 시뮬레이션",
        "",
        "4. 🔄 데이터 일관성 보장",
        "   - 백테스트 DB 스키마와 시뮬레이션 DB 통일",
        "   - 실시간 데이터 구조와 호환성",
        "   - 변수 정의 시스템 표준화"
    ]
    
    for rec in recommendations:
        print(rec)

if __name__ == "__main__":
    print(f"🕐 분석 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    analyze_database_structure()
    analyze_backtest_readiness()
    analyze_variable_definitions()
    check_simulation_data_needs()
    generate_recommendations()
    
    print(f"\n✅ 분석 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
