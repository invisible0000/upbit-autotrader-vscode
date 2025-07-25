#!/usr/bin/env python3
"""
시나리오별 데이터 검색 범위 확장 테스트 스크립트
조건에 맞는 구간이 500개 안에 없을 때 범위를 확장하는지 확인
"""

import sys
import os
import logging

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

def test_scenario_search():
    """시나리오별 데이터 검색 테스트 (내장 데이터셋 포함)"""
    try:
        from upbit_auto_trading.ui.desktop.screens.strategy_management.real_data_simulation import get_simulation_engine
        
        print("=" * 60)
        print("🚀 시뮬레이션 엔진 통합 테스트 (내장 데이터셋 우선)")
        print("=" * 60)
        
        # 시뮬레이션 엔진 초기화 (자동으로 최적 엔진 선택)
        print("\n📌 최적 시뮬레이션 엔진 초기화 중...")
        engine = get_simulation_engine()
        
        # 엔진 타입 확인
        engine_type = type(engine).__name__
        print(f"✅ 선택된 엔진: {engine_type}")
        
        # 테스트할 시나리오들
        test_scenarios = [
            ("급등", "7일간 15% 이상 상승 (까다로운 조건)"),
            ("급락", "7일간 15% 이상 하락 (까다로운 조건)"),
            ("상승 추세", "30일간 5% 이상 상승"),
            ("하락 추세", "30일간 5% 이상 하락"),
            ("횡보", "30일간 변화율 3% 이내 (느슨한 조건)"),
            ("이동평균 교차", "이동평균선 교차 시뮬레이션")
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
                
                print(f"✅ 데이터 소스: {data_source}")
                print(f"📅 기간: {period}")
                print(f"📊 변화율: {change_percent:.2f}%")
                print(f"💰 현재값: {current_value:,.0f}")
                
                # 데이터 소스별 분류
                if 'embedded' in data_source:
                    source_type = "내장 데이터셋"
                    priority = 1
                elif 'real_market_data' in data_source:
                    source_type = "실제 DB"
                    priority = 2
                elif 'synthetic' in data_source:
                    source_type = "합성 데이터"
                    priority = 3
                else:
                    source_type = "폴백 데이터"
                    priority = 4
                
                print(f"🔧 데이터 타입: {source_type} (우선순위: {priority})")
                
                # 결과 저장
                results.append({
                    'scenario': scenario,
                    'data_source': data_source,
                    'source_type': source_type,
                    'priority': priority,
                    'period': period,
                    'change_percent': change_percent,
                    'success': True
                })
                
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                results.append({
                    'scenario': scenario,
                    'data_source': 'error',
                    'source_type': 'error',
                    'priority': 99,
                    'period': 'error',
                    'change_percent': 0,
                    'success': False
                })
        
        # 결과 요약
        print(f"\n{'='*60}")
        print("📊 통합 시뮬레이션 엔진 테스트 결과")
        print("=" * 60)
        
        success_count = sum(1 for r in results if r['success'])
        embedded_count = sum(1 for r in results if r['priority'] == 1)
        real_db_count = sum(1 for r in results if r['priority'] == 2)
        synthetic_count = sum(1 for r in results if r['priority'] == 3)
        fallback_count = sum(1 for r in results if r['priority'] == 4)
        
        print(f"🎯 총 테스트 시나리오: {len(results)}개")
        print(f"✅ 성공적으로 실행: {success_count}개")
        print(f"🔧 내장 데이터셋 사용: {embedded_count}개")
        print(f"📁 실제 DB 사용: {real_db_count}개")
        print(f"🧪 합성 데이터 사용: {synthetic_count}개")
        print(f"🔄 폴백 데이터 사용: {fallback_count}개")
        
        print(f"\n{'시나리오':<12} {'데이터 타입':<12} {'변화율':<8} {'상태'}")
        print("-" * 60)
        for r in results:
            status_icon = "✅" if r['success'] else "❌"
            priority_icon = ["", "🥇", "🥈", "🥉", "🔄"][min(r['priority'], 4)]
            print(f"{r['scenario']:<12} {priority_icon} {r['source_type']:<10} {r['change_percent']:>6.1f}% {status_icon}")
        
        # 엔진 성능 평가
        print(f"\n🏆 엔진 성능 평가:")
        if embedded_count == len(results):
            print("🎉 완벽: 모든 시나리오에서 최고 성능 내장 데이터셋 사용!")
        elif embedded_count >= len(results) * 0.8:
            print("🥇 우수: 대부분 내장 데이터셋 사용")
        elif real_db_count >= len(results) * 0.8:
            print("🥈 양호: 실제 DB 기반 시뮬레이션")
        else:
            print("🥉 보통: 혼합 데이터 소스 사용")
        
        return results
        
    except ImportError as e:
        print(f"❌ 모듈 Import 오류: {e}")
        print("💡 upbit_auto_trading 패키지 경로를 확인해주세요.")
        return None
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return None

def main():
    """메인 실행 함수"""
    print("🔬 통합 시뮬레이션 엔진 테스트")
    print("목적: 내장 데이터셋 우선의 다계층 시뮬레이션 시스템 검증")
    print("데이터 소스 우선순위: 내장 데이터셋 > 실제 DB > 합성 데이터 > 폴백")
    
    results = test_scenario_search()
    
    if results:
        embedded_count = sum(1 for r in results if r.get('priority') == 1)
        total_count = len(results)
        
        print(f"\n🎉 통합 엔진 테스트 완료!")
        print(f"📊 내장 데이터셋 활용률: {embedded_count}/{total_count} ({embedded_count/total_count*100:.1f}%)")
        
        if embedded_count == total_count:
            print("🏆 완벽: 모든 시나리오에서 최고 성능 내장 데이터셋 사용!")
            print("💡 이제 DB 없이도 완벽하게 시뮬레이션이 작동합니다.")
        elif embedded_count >= total_count * 0.8:
            print("🥇 우수: 대부분 시나리오에서 내장 데이터셋 사용")
        else:
            print("🥈 양호: 혼합 데이터 소스 활용")
    else:
        print("\n❌ 테스트 실패")
        sys.exit(1)

if __name__ == "__main__":
    main()
