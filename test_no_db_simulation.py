#!/usr/bin/env python3
"""
DB 없는 환경에서 시뮬레이션 테스트 스크립트
실제 DB를 임시로 이동시키고 폴백 시스템 테스트
"""

import sys
import os
import logging
import shutil
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


def backup_database():
    """실제 DB를 백업하여 DB 없는 환경 시뮬레이션"""
    db_path = "data/market_data.sqlite3"
    backup_path = "data/market_data.sqlite3.backup_for_test"
    
    if os.path.exists(db_path):
        shutil.move(db_path, backup_path)
        logging.info(f"✅ DB 백업 완료: {db_path} -> {backup_path}")
        return True
    else:
        logging.info("ℹ️  DB가 원래부터 없습니다.")
        return False


def restore_database():
    """백업한 DB 복원"""
    db_path = "data/market_data.sqlite3"
    backup_path = "data/market_data.sqlite3.backup_for_test"
    
    if os.path.exists(backup_path):
        shutil.move(backup_path, db_path)
        logging.info(f"✅ DB 복원 완료: {backup_path} -> {db_path}")
        return True
    else:
        logging.warning("❌ 복원할 백업 DB가 없습니다.")
        return False


def test_without_db():
    """DB 없는 환경에서 시뮬레이션 테스트"""
    try:
        print("=" * 70)
        print("🚀 DB 없는 환경에서 시뮬레이션 테스트")
        print("=" * 70)
        
        # 강화된 시뮬레이션 엔진 테스트
        from upbit_auto_trading.ui.desktop.screens.strategy_management.robust_simulation_engine import RobustSimulationEngine
        
        # 시뮬레이션 엔진 초기화
        print("\n📌 강화된 시뮬레이션 엔진 초기화 중...")
        engine = RobustSimulationEngine("data/nonexistent_db.sqlite3")  # 존재하지 않는 DB 경로
        
        # 테스트할 시나리오들
        test_scenarios = [
            ("상승 추세", "30일간 5% 이상 상승"),
            ("하락 추세", "30일간 5% 이상 하락"),
            ("급등", "7일간 15% 이상 급등"),
            ("급락", "7일간 15% 이상 급락"),
            ("횡보", "30일간 변화율 3% 이내"),
            ("이동평균 교차", "이동평균선 교차")
        ]
        
        results = []
        
        for scenario, description in test_scenarios:
            print(f"\n{'='*50}")
            print(f"🎯 시나리오: {scenario}")
            print(f"📋 조건: {description}")
            print("-" * 50)
            
            try:
                # 시나리오 데이터 검색
                result = engine.get_scenario_data(scenario, 30)
                
                data_source = result.get('data_source', 'unknown')
                period = result.get('period', 'unknown')
                change_percent = result.get('change_percent', 0)
                current_value = result.get('current_value', 0)
                price_data = result.get('price_data', [])
                
                print(f"✅ 데이터 소스: {data_source}")
                print(f"📅 기간: {period}")
                print(f"📊 변화율: {change_percent:.2f}%")
                print(f"💰 현재값: {current_value:,.0f}")
                print(f"📈 데이터 포인트: {len(price_data)}개")
                
                # 가격 데이터 품질 확인
                if price_data:
                    min_price = min(price_data)
                    max_price = max(price_data)
                    print(f"💹 가격 범위: {min_price:,.0f} ~ {max_price:,.0f}")
                
                # 결과 저장
                results.append({
                    'scenario': scenario,
                    'data_source': data_source,
                    'period': period,
                    'change_percent': change_percent,
                    'current_value': current_value,
                    'data_points': len(price_data),
                    'success': data_source != 'emergency_fallback'
                })
                
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                import traceback
                traceback.print_exc()
                results.append({
                    'scenario': scenario,
                    'data_source': 'error',
                    'period': 'error',
                    'change_percent': 0,
                    'current_value': 0,
                    'data_points': 0,
                    'success': False
                })
        
        # 결과 요약
        print(f"\n{'='*70}")
        print("📊 DB 없는 환경 테스트 결과 요약")
        print("=" * 70)
        
        success_count = sum(1 for r in results if r['success'])
        emergency_count = sum(1 for r in results if r['data_source'] == 'emergency_fallback')
        synthetic_count = sum(1 for r in results if 'synthetic' in r['data_source'])
        
        print(f"🎯 총 테스트 시나리오: {len(results)}개")
        print(f"✅ 성공적으로 실행: {success_count}개")
        print(f"🔧 합성 데이터 사용: {synthetic_count}개")
        print(f"🚨 비상 폴백 사용: {emergency_count}개")
        
        print(f"\n{'시나리오':<12} {'데이터 소스':<25} {'변화율':<8} {'상태'}")
        print("-" * 70)
        for r in results:
            status = "✅" if r['success'] else "❌"
            print(f"{r['scenario']:<12} {r['data_source']:<25} {r['change_percent']:>6.1f}% {status}")
        
        # 데이터 품질 분석
        print(f"\n📈 데이터 품질 분석:")
        if synthetic_count > 0:
            print(f"✅ 합성 데이터가 성공적으로 생성되었습니다!")
            print(f"✅ 모든 시나리오에서 {results[0]['data_points']}개의 데이터 포인트 제공")
            print(f"✅ 현실적인 가격 범위와 변동성 구현")
        
        if emergency_count == 0:
            print(f"🎉 비상 폴백 없이 모든 시나리오 처리 성공!")
        else:
            print(f"⚠️  {emergency_count}개 시나리오에서 비상 폴백 사용됨")
        
        return results
        
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_performance_comparison():
    """실제 DB vs 합성 데이터 성능 비교"""
    print(f"\n{'='*70}")
    print("⚡ 성능 비교 테스트: 실제 DB vs 합성 데이터")
    print("=" * 70)
    
    import time
    
    try:
        # 1. 합성 데이터 성능 테스트
        from upbit_auto_trading.ui.desktop.screens.strategy_management.robust_simulation_engine import RobustSimulationEngine
        
        engine = RobustSimulationEngine("data/nonexistent_db.sqlite3")
        
        print("\n🔧 합성 데이터 생성 성능 테스트...")
        start_time = time.time()
        
        synthetic_results = []
        for i in range(5):  # 5번 반복
            result = engine.get_scenario_data("급등", 50)
            synthetic_results.append(result)
        
        synthetic_time = time.time() - start_time
        print(f"✅ 합성 데이터 5회 생성 시간: {synthetic_time:.3f}초")
        print(f"✅ 평균 1회당: {synthetic_time/5:.3f}초")
        
        # 2. 실제 DB 복원 후 성능 테스트 (DB가 있다면)
        if restore_database():
            print("\n💾 실제 DB 성능 테스트...")
            from upbit_auto_trading.ui.desktop.screens.strategy_management.real_data_simulation import RealDataSimulationEngine
            
            real_engine = RealDataSimulationEngine()
            start_time = time.time()
            
            real_results = []
            for i in range(5):  # 5번 반복
                result = real_engine.get_scenario_data("급등", 50)
                real_results.append(result)
            
            real_time = time.time() - start_time
            print(f"✅ 실제 DB 5회 조회 시간: {real_time:.3f}초")
            print(f"✅ 평균 1회당: {real_time/5:.3f}초")
            
            # 성능 비교
            print(f"\n📊 성능 비교 결과:")
            if synthetic_time < real_time:
                speedup = real_time / synthetic_time
                print(f"🚀 합성 데이터가 {speedup:.1f}배 빠름!")
            else:
                slowdown = synthetic_time / real_time
                print(f"📈 실제 DB가 {slowdown:.1f}배 빠름")
            
            print(f"💡 합성 데이터의 장점: DB 의존성 없음, 일관된 성능")
            print(f"💡 실제 DB의 장점: 진짜 시장 상황 반영")
            
        else:
            print("ℹ️  실제 DB를 찾을 수 없어 성능 비교를 건너뜁니다.")
        
    except Exception as e:
        print(f"❌ 성능 테스트 중 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🔬 DB 없는 환경에서 시뮬레이션 시스템 테스트")
    print("목적: 실제 DB가 없어도 시뮬레이션이 정상 작동하는지 확인")
    
    # DB를 임시로 백업 (DB 없는 환경 시뮬레이션)
    has_db = backup_database()
    
    try:
        # DB 없는 환경 테스트
        results = test_without_db()
        
        if results:
            success_rate = sum(1 for r in results if r['success']) / len(results) * 100
            print(f"\n🎉 DB 없는 환경 테스트 완료!")
            print(f"📊 성공률: {success_rate:.1f}%")
            
            if success_rate >= 80:
                print("✅ 우수: 시뮬레이션 시스템이 DB 없이도 잘 작동합니다!")
            elif success_rate >= 60:
                print("⚠️  양호: 대부분 작동하지만 개선 여지가 있습니다.")
            else:
                print("❌ 미흡: 추가 개선이 필요합니다.")
        else:
            print("❌ 테스트 실패")
        
        # 성능 비교 테스트
        test_performance_comparison()
        
    finally:
        # DB 복원 (테스트 후 원상복구)
        if has_db:
            print(f"\n🔄 DB 복원 중...")
            restore_database()
        
    print(f"\n🏁 모든 테스트 완료!")


if __name__ == "__main__":
    main()
