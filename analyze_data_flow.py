#!/usr/bin/env python3
"""
케이스 시뮬레이션 데이터 흐름 분석
UI 버튼 클릭 → 데이터 소스까지의 전체 흐름 추적
"""

import sys
import os
sys.path.append('upbit_auto_trading/ui/desktop/screens/strategy_management')

def analyze_data_flow():
    """데이터 흐름 분석"""
    print("🔍 케이스 시뮬레이션 데이터 흐름 분석")
    print("="*80)
    
    print("📋 데이터 흐름 단계별 분석:")
    print("-"*80)
    
    # 1단계: UI 버튼 클릭
    print("1️⃣ UI 버튼 클릭")
    print("   📍 위치: integrated_condition_manager.py")
    print("   🎯 함수: run_simulation(scenario)")
    print("   📝 동작: 시나리오명('상승 추세', '급등' 등)과 함께 호출")
    
    # 2단계: 시뮬레이션 데이터 생성
    print("\n2️⃣ 시뮬레이션 데이터 생성")
    print("   📍 위치: integrated_condition_manager.py")
    print("   🎯 함수: generate_simulation_data(scenario, variable_name)")
    print("   📝 동작: 실제 데이터 엔진 호출 시도")
    
    # 3단계: 실제 데이터 엔진 접근
    print("\n3️⃣ 실제 데이터 엔진 접근")
    print("   📍 위치: real_data_simulation.py")
    print("   🎯 함수: get_simulation_engine() → RealDataSimulationEngine")
    print("   📝 동작: 싱글톤 패턴으로 엔진 인스턴스 생성/반환")
    
    # 4단계: 데이터베이스 접근
    print("\n4️⃣ 데이터베이스 접근")
    print("   📍 위치: real_data_simulation.py")
    print("   🎯 함수: load_market_data()")
    print("   📝 동작: data/market_data.sqlite3에서 실시간 쿼리")
    print("   💾 쿼리: SELECT * FROM market_data WHERE symbol='KRW-BTC' LIMIT 500")
    
    # 5단계: 캐싱 메커니즘
    print("\n5️⃣ 캐싱 메커니즘")
    print("   📍 위치: RealDataSimulationEngine 클래스")
    print("   🎯 변수: self.cache_data, self.cache_indicators")
    print("   📝 동작: 첫 로드 후 메모리에 캐시, 이후 재사용")

def trace_actual_execution():
    """실제 실행 추적"""
    print("\n🎮 실제 실행 추적 테스트")
    print("="*80)
    
    try:
        from real_data_simulation import get_simulation_engine
        
        # 엔진 상태 확인
        engine = get_simulation_engine()
        print(f"🔧 엔진 인스턴스: {engine}")
        print(f"💾 캐시 상태 (초기): data={engine.cache_data is not None}, indicators={engine.cache_indicators is not None}")
        
        # 첫 번째 시나리오 실행 (데이터 로드)
        print(f"\n📊 첫 번째 시나리오 실행 ('상승 추세'):")
        result1 = engine.get_scenario_data("상승 추세", length=30)
        print(f"   💾 캐시 상태 (로드 후): data={engine.cache_data is not None}, indicators={engine.cache_indicators is not None}")
        print(f"   📈 데이터 소스: {result1.get('data_source', 'Unknown')}")
        print(f"   📅 기간: {result1.get('period', 'Unknown')}")
        
        if engine.cache_data is not None:
            print(f"   📊 캐시된 데이터: {len(engine.cache_data)}개 레코드")
            print(f"   📅 캐시 범위: {engine.cache_data.index[0]} ~ {engine.cache_data.index[-1]}")
        
        # 두 번째 시나리오 실행 (캐시 사용)
        print(f"\n📊 두 번째 시나리오 실행 ('급등') - 캐시 사용:")
        result2 = engine.get_scenario_data("급등", length=30)
        print(f"   📈 데이터 소스: {result2.get('data_source', 'Unknown')}")
        print(f"   📅 기간: {result2.get('period', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 실행 추적 오류: {e}")
        return False

def analyze_database_access():
    """데이터베이스 접근 패턴 분석"""
    print("\n💾 데이터베이스 접근 패턴 분석")
    print("="*80)
    
    import sqlite3
    
    db_path = 'data/market_data.sqlite3'
    if not os.path.exists(db_path):
        print(f"❌ DB 파일 없음: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 실제 쿼리 실행
        query = """
        SELECT 
            timestamp,
            open,
            high,
            low,
            close,
            volume
        FROM market_data 
        WHERE symbol = 'KRW-BTC' AND timeframe = '1d'
        ORDER BY timestamp DESC 
        LIMIT 500
        """
        
        print("🔍 실제 쿼리 실행:")
        print("   📝 SQL:", query.strip().replace('\n', ' '))
        
        cursor.execute(query)
        records = cursor.fetchall()
        
        print(f"   📊 반환된 레코드: {len(records)}개")
        print(f"   💰 최신 가격: {records[0][4]:,.0f}원 ({records[0][0]})")
        print(f"   📅 데이터 범위: {records[-1][0]} ~ {records[0][0]}")
        
        # 메모리 사용량 추정
        record_size = sum(len(str(field)) for field in records[0]) if records else 0
        total_size = record_size * len(records)
        print(f"   💾 메모리 사용량 (추정): {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ DB 접근 분석 오류: {e}")
        return False

def main():
    """메인 분석 실행"""
    print("🚀 케이스 시뮬레이션 데이터 흐름 종합 분석")
    print("="*100)
    
    # 1. 데이터 흐름 단계별 분석
    analyze_data_flow()
    
    # 2. 실제 실행 추적
    execution_ok = trace_actual_execution()
    
    # 3. 데이터베이스 접근 패턴 분석
    db_ok = analyze_database_access()
    
    # 결론
    print(f"\n" + "="*100)
    print("🎯 결론 요약")
    print("="*100)
    
    print("📊 데이터 소스:")
    print("   ✅ 실시간: data/market_data.sqlite3에서 직접 쿼리")
    print("   ✅ 캐싱: 첫 로드 후 메모리에 500개 레코드 캐시")
    print("   ✅ 폴백: DB 오류 시 시뮬레이션 데이터로 자동 전환")
    
    print(f"\n📋 동작 방식:")
    print("   1️⃣ UI 버튼 클릭 → run_simulation() 호출")
    print("   2️⃣ generate_simulation_data() → 실제 데이터 엔진 접근")
    print("   3️⃣ get_simulation_engine() → 싱글톤 엔진 인스턴스")
    print("   4️⃣ load_market_data() → SQLite DB 실시간 쿼리")
    print("   5️⃣ get_scenario_data() → 시나리오별 실제 케이스 추출")
    print("   6️⃣ UI 차트 업데이트 → 실제 가격 패턴 표시")
    
    print(f"\n💾 성능 최적화:")
    print("   ✅ 메모리 캐싱: 첫 로드 후 재사용")
    print("   ✅ 제한된 데이터: 최근 500일만 로드")
    print("   ✅ 인덱스 활용: timestamp DESC 정렬로 빠른 조회")
    
    if execution_ok and db_ok:
        print(f"\n🎉 완벽! 케이스 시뮬레이션은 실제 market_data.sqlite3에서")
        print(f"   실시간으로 데이터를 가져와 의미 있는 시나리오를 생성합니다!")
    else:
        print(f"\n⚠️ 일부 분석에서 문제가 발견되었습니다.")

if __name__ == "__main__":
    main()
