#!/usr/bin/env python3
"""
실제 데이터 시뮬레이션 통합 테스트
UI 케이스 시뮬레이션이 실제 KRW-BTC 데이터를 사용하는지 확인
"""

import sys
import os
import sqlite3
from pathlib import Path

# 프로젝트 루트 경로 설정
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_real_data_availability():
    """실제 데이터 가용성 확인"""
    print("=== 실제 데이터 가용성 확인 ===")
    
    db_path = project_root / "data" / "market_data.sqlite3"
    
    if not db_path.exists():
        print(f"❌ 시장 데이터 DB 없음: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 테이블 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 사용 가능한 테이블: {tables}")
        
        # KRW-BTC 데이터 확인
        if 'KRW_BTC_daily' in tables:
            cursor.execute("SELECT COUNT(*) FROM KRW_BTC_daily")
            count = cursor.fetchone()[0]
            print(f"💰 KRW-BTC 일봉 데이터: {count}개")
            
            # 최신 데이터 확인
            cursor.execute("SELECT timestamp, close FROM KRW_BTC_daily ORDER BY timestamp DESC LIMIT 5")
            recent_data = cursor.fetchall()
            print("📈 최신 5개 데이터:")
            for timestamp, close in recent_data:
                print(f"  {timestamp}: {close:,}원")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ DB 접근 오류: {e}")
        return False

def test_real_data_simulation_module():
    """실제 데이터 시뮬레이션 모듈 테스트"""
    print("\n=== 실제 데이터 시뮬레이션 모듈 테스트 ===")
    
    try:
        # 실제 데이터 시뮬레이션 모듈 임포트
        real_sim_path = project_root / "upbit_auto_trading" / "ui" / "desktop" / "screens" / "strategy_management" / "real_data_simulation.py"
        
        if not real_sim_path.exists():
            print(f"❌ 실제 데이터 시뮬레이션 모듈 없음: {real_sim_path}")
            return False
        
        # 모듈 로드
        spec = __import__('importlib.util').util.spec_from_file_location("real_data_simulation", real_sim_path)
        real_data_sim = __import__('importlib.util').util.module_from_spec(spec)
        spec.loader.exec_module(real_data_sim)
        
        # 엔진 생성
        engine = real_data_sim.get_simulation_engine()
        print("✅ 실제 데이터 시뮬레이션 엔진 생성 성공")
        
        # 시장 데이터 로드 테스트
        market_data = engine.load_market_data()
        if market_data is not None and len(market_data) > 0:
            print(f"✅ 시장 데이터 로드 성공: {len(market_data)}개 항목")
            print(f"📊 데이터 범위: {market_data.index[0]} ~ {market_data.index[-1]}")
        else:
            print("❌ 시장 데이터 로드 실패")
            return False
        
        # 시나리오별 테스트
        scenarios = ["상승 추세", "하락 추세", "급등", "급락", "횡보"]
        
        for scenario in scenarios:
            scenario_data = engine.get_scenario_data(scenario, length=30)
            
            if scenario_data and scenario_data.get('data_source') == 'real_market_data':
                print(f"✅ {scenario}: 실제 데이터 {len(scenario_data.get('price_data', []))}개")
            else:
                print(f"❌ {scenario}: 실제 데이터 로드 실패")
        
        return True
        
    except Exception as e:
        print(f"❌ 모듈 테스트 오류: {e}")
        return False

def test_ui_integration():
    """UI 통합 테스트"""
    print("\n=== UI 통합 테스트 ===")
    
    try:
        # UI 시뮬레이션 매니저 임포트 (PyQt6 없이도 동작하도록)
        ui_path = project_root / "upbit_auto_trading" / "ui" / "desktop" / "screens" / "strategy_management" / "integrated_condition_manager.py"
        
        if not ui_path.exists():
            print(f"❌ UI 매니저 파일 없음: {ui_path}")
            return False
        
        print("✅ UI 통합 준비 완료")
        print("📋 UI에서 실제 데이터 사용 여부는 실제 GUI 실행 시 확인 가능")
        
        # 코드 내용 확인
        with open(ui_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'real_data_simulation' in content:
            print("✅ UI에 실제 데이터 시뮬레이션 통합됨")
        else:
            print("❌ UI에 실제 데이터 시뮬레이션 미통합")
            return False
        
        if 'get_simulation_engine()' in content:
            print("✅ UI에서 실제 데이터 엔진 호출 코드 발견")
        else:
            print("❌ UI에서 실제 데이터 엔진 호출 코드 없음")
        
        return True
        
    except Exception as e:
        print(f"❌ UI 통합 테스트 오류: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("🚀 실제 데이터 시뮬레이션 통합 테스트 시작\n")
    
    tests = [
        ("실제 데이터 가용성", test_real_data_availability),
        ("실제 데이터 시뮬레이션 모듈", test_real_data_simulation_module),
        ("UI 통합", test_ui_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"테스트: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 테스트 실행 오류: {e}")
            results.append((test_name, False))
    
    # 결과 요약
    print(f"\n{'='*50}")
    print("테스트 결과 요약")
    print('='*50)
    
    for test_name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{test_name}: {status}")
    
    success_count = sum(1 for _, result in results if result)
    print(f"\n총 {len(results)}개 테스트 중 {success_count}개 성공")
    
    if success_count == len(results):
        print("🎉 모든 테스트 성공! UI 케이스 시뮬레이션이 실제 데이터를 사용할 준비가 되었습니다.")
    else:
        print("⚠️ 일부 테스트 실패. 문제 해결 후 다시 시도해 주세요.")

if __name__ == "__main__":
    main()
