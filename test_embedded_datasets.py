#!/usr/bin/env python3
"""
내장 시뮬레이션 데이터셋 테스트 스크립트
시나리오별 최적화된 내장 데이터의 품질과 특성 검증
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


def test_embedded_datasets():
    """내장 데이터셋의 품질과 특성 테스트"""
    try:
        from upbit_auto_trading.ui.desktop.screens.strategy_management.embedded_simulation_engine import get_embedded_simulation_engine
        
        print("=" * 80)
        print("🎯 내장 시뮬레이션 데이터셋 품질 검증 테스트")
        print("=" * 80)
        
        # 내장 시뮬레이션 엔진 초기화
        engine = get_embedded_simulation_engine()
        
        # 사용 가능한 시나리오 확인
        scenarios = engine.get_available_scenarios()
        print(f"\n📋 사용 가능한 시나리오: {len(scenarios)}개")
        for scenario in scenarios:
            print(f"   - {scenario}")
        
        print(f"\n{'='*80}")
        print("📊 시나리오별 데이터셋 특성 분석")
        print("=" * 80)
        
        results = []
        
        for scenario in scenarios:
            print(f"\n🎯 시나리오: {scenario}")
            print("-" * 60)
            
            try:
                # 데이터셋 정보 가져오기
                dataset_info = engine.get_dataset_info(scenario)
                
                if dataset_info:
                    print(f"📈 총 변화율: {dataset_info['total_change']:.2f}%")
                    print(f"📊 평균 일일 변동성: {dataset_info['avg_daily_volatility']:.2f}%")
                    print(f"📋 데이터 포인트: {dataset_info['data_points']:,}개")
                    print(f"📝 설명: {dataset_info['description']}")
                
                # 실제 시뮬레이션 데이터 테스트
                result = engine.get_scenario_data(scenario, 30)
                
                data_source = result.get('data_source', 'unknown')
                period = result.get('period', 'unknown')
                change_percent = result.get('change_percent', 0)
                current_value = result.get('current_value', 0)
                price_data = result.get('price_data', [])
                description = result.get('description', '')
                
                print(f"✅ 데이터 소스: {data_source}")
                print(f"📅 기간: {period}")
                print(f"📊 30일 변화율: {change_percent:.2f}%")
                print(f"💰 현재값: {current_value:,.0f}")
                print(f"📈 데이터 포인트: {len(price_data)}개")
                
                # 데이터 품질 검증
                if price_data:
                    min_price = min(price_data)
                    max_price = max(price_data)
                    price_range = (max_price - min_price) / min_price * 100
                    
                    print(f"💹 가격 범위: {min_price:,.0f} ~ {max_price:,.0f}")
                    print(f"📈 가격 변동 폭: {price_range:.2f}%")
                    
                    # 시나리오 특성 검증
                    is_valid = validate_scenario_characteristics(scenario, price_data, change_percent)
                    validation_status = "✅ 적합" if is_valid else "❌ 부적합"
                    print(f"🎯 시나리오 특성: {validation_status}")
                
                # 결과 저장
                results.append({
                    'scenario': scenario,
                    'data_source': data_source,
                    'change_percent': change_percent,
                    'current_value': current_value,
                    'data_points': len(price_data),
                    'is_embedded': 'embedded' in data_source,
                    'is_valid': is_valid if 'price_data' in locals() and price_data else False
                })
                
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                import traceback
                traceback.print_exc()
                results.append({
                    'scenario': scenario,
                    'data_source': 'error',
                    'change_percent': 0,
                    'current_value': 0,
                    'data_points': 0,
                    'is_embedded': False,
                    'is_valid': False
                })
        
        # 결과 요약
        print(f"\n{'='*80}")
        print("📊 내장 데이터셋 종합 평가")
        print("=" * 80)
        
        embedded_count = sum(1 for r in results if r['is_embedded'])
        valid_count = sum(1 for r in results if r['is_valid'])
        total_count = len(results)
        
        print(f"🎯 총 시나리오: {total_count}개")
        print(f"✅ 내장 데이터셋 사용: {embedded_count}개 ({embedded_count/total_count*100:.1f}%)")
        print(f"🎯 시나리오 특성 적합: {valid_count}개 ({valid_count/total_count*100:.1f}%)")
        
        print(f"\n{'시나리오':<12} {'데이터 소스':<25} {'변화율':<8} {'특성 적합성'}")
        print("-" * 80)
        for r in results:
            embedded_mark = "🔧" if r['is_embedded'] else "📁"
            validity_mark = "✅" if r['is_valid'] else "❌"
            print(f"{r['scenario']:<12} {embedded_mark} {r['data_source']:<22} {r['change_percent']:>6.1f}% {validity_mark}")
        
        # 품질 평가
        print(f"\n🏆 품질 평가:")
        if embedded_count == total_count and valid_count >= total_count * 0.8:
            print("🎉 우수: 모든 시나리오에서 고품질 내장 데이터셋 제공!")
        elif embedded_count >= total_count * 0.8:
            print("✅ 양호: 대부분 시나리오에서 내장 데이터셋 사용")
        else:
            print("⚠️  개선 필요: 내장 데이터셋 커버리지 부족")
        
        return results
        
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


def validate_scenario_characteristics(scenario: str, price_data: list, change_percent: float) -> bool:
    """시나리오별 특성이 적절한지 검증"""
    try:
        if not price_data or len(price_data) < 2:
            return False
        
        # 시나리오별 기대 특성
        expectations = {
            '상승 추세': {'min_change': 5, 'max_change': 50, 'direction': 'up'},
            '하락 추세': {'min_change': -50, 'max_change': -5, 'direction': 'down'},
            '급등': {'min_change': 15, 'max_change': 100, 'direction': 'up'},
            '급락': {'min_change': -60, 'max_change': -15, 'direction': 'down'},
            '횡보': {'min_change': -5, 'max_change': 5, 'direction': 'flat'},
            '이동평균 교차': {'min_change': -10, 'max_change': 20, 'direction': 'any'}
        }
        
        if scenario not in expectations:
            return True  # 정의되지 않은 시나리오는 패스
        
        expected = expectations[scenario]
        
        # 변화율 검증
        if not (expected['min_change'] <= change_percent <= expected['max_change']):
            return False
        
        # 추가 특성 검증 (변동성, 트렌드 등)
        # 여기서는 기본 변화율만 검증
        return True
        
    except Exception:
        return False


def test_performance_comparison():
    """내장 데이터셋 vs 기존 방식 성능 비교"""
    print(f"\n{'='*80}")
    print("⚡ 성능 비교: 내장 데이터셋 vs 기존 방식")
    print("=" * 80)
    
    import time
    
    try:
        # 1. 내장 데이터셋 성능 테스트
        from upbit_auto_trading.ui.desktop.screens.strategy_management.embedded_simulation_engine import get_embedded_simulation_engine
        
        embedded_engine = get_embedded_simulation_engine()
        
        print("\n🔧 내장 데이터셋 성능 테스트...")
        start_time = time.time()
        
        for _ in range(10):
            result = embedded_engine.get_scenario_data("급등", 50)
        
        embedded_time = time.time() - start_time
        print(f"✅ 내장 데이터셋 10회 처리: {embedded_time:.3f}초")
        print(f"✅ 평균 1회당: {embedded_time/10:.3f}초")
        
        # 2. 기존 방식 성능 테스트 (DB 기반)
        try:
            from upbit_auto_trading.ui.desktop.screens.strategy_management.real_data_simulation import RealDataSimulationEngine
            
            real_engine = RealDataSimulationEngine()
            
            print("\n📁 기존 DB 방식 성능 테스트...")
            start_time = time.time()
            
            for _ in range(10):
                result = real_engine.get_scenario_data("급등", 50)
            
            real_time = time.time() - start_time
            print(f"✅ 기존 DB 방식 10회 처리: {real_time:.3f}초")
            print(f"✅ 평균 1회당: {real_time/10:.3f}초")
            
            # 성능 비교
            print(f"\n📊 성능 비교 결과:")
            if embedded_time < real_time:
                speedup = real_time / embedded_time
                print(f"🚀 내장 데이터셋이 {speedup:.1f}배 빠름!")
            else:
                slowdown = embedded_time / real_time
                print(f"📈 기존 방식이 {slowdown:.1f}배 빠름")
            
            print(f"\n💡 내장 데이터셋의 장점:")
            print(f"   ✅ DB 의존성 없음")
            print(f"   ✅ 일관된 성능")
            print(f"   ✅ 시나리오별 최적화")
            print(f"   ✅ 오프라인 작동")
            
        except Exception as e:
            print(f"⚠️  기존 방식 테스트 건너뜀: {e}")
        
    except Exception as e:
        print(f"❌ 성능 테스트 중 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🔬 내장 시뮬레이션 데이터셋 품질 검증")
    print("목적: 시나리오별 최적화된 내장 데이터의 품질과 특성 확인")
    
    # 내장 데이터셋 테스트
    results = test_embedded_datasets()
    
    if results:
        success_rate = sum(1 for r in results if r['is_embedded'] and r['is_valid']) / len(results) * 100
        print(f"\n🎉 내장 데이터셋 테스트 완료!")
        print(f"📊 품질 점수: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🏆 최고 등급: 시나리오별 최적화 완벽!")
        elif success_rate >= 70:
            print("✅ 우수: 대부분 시나리오에서 고품질 제공")
        else:
            print("⚠️  개선 필요: 추가 최적화 필요")
    else:
        print("❌ 테스트 실패")
    
    # 성능 비교
    test_performance_comparison()
    
    print(f"\n🏁 모든 검증 완료!")


if __name__ == "__main__":
    main()
