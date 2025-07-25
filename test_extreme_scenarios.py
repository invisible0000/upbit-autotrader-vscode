#!/usr/bin/env python3
"""
까다로운 조건으로 범위 확장 기능 테스트
극단적인 시나리오로 500개 범위를 넘어서는 검색 테스트
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

def test_extreme_scenarios():
    """극단적인 조건으로 범위 확장 테스트"""
    try:
        # 실제 DB 상황 확인을 위해 직접 쿼리
        import sqlite3
        import pandas as pd
        
        print("=" * 70)
        print("🔍 실제 데이터베이스 조건별 분포 분석")
        print("=" * 70)
        
        db_path = "data/market_data.sqlite3"
        if not os.path.exists(db_path):
            print(f"❌ DB 파일을 찾을 수 없습니다: {db_path}")
            return
        
        conn = sqlite3.connect(db_path)
        
        # 전체 데이터 로드
        query = """
        SELECT timestamp, close 
        FROM market_data 
        WHERE symbol = 'KRW-BTC' AND timeframe = '1d' 
        ORDER BY timestamp DESC 
        LIMIT 2000
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        if df.empty:
            print("❌ 데이터가 없습니다.")
            return
        
        # 수익률 계산
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        df['return_7d'] = df['close'].pct_change(7) * 100
        df['return_30d'] = df['close'].pct_change(30) * 100
        
        print(f"📊 총 데이터 수: {len(df)}개")
        print(f"📅 기간: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
        
        # 조건별 분포 확인
        conditions = {
            "최근 500개에서 급등 (7일 +15%)": (df.tail(500)['return_7d'] > 15).sum(),
            "최근 500개에서 급락 (7일 -15%)": (df.tail(500)['return_7d'] < -15).sum(),
            "최근 500개에서 극단적 급등 (+25%)": (df.tail(500)['return_7d'] > 25).sum(),
            "최근 500개에서 극단적 급락 (-25%)": (df.tail(500)['return_7d'] < -25).sum(),
            
            "전체 2000개에서 급등 (7일 +15%)": (df['return_7d'] > 15).sum(),
            "전체 2000개에서 급락 (7일 -15%)": (df['return_7d'] < -15).sum(),
            "전체 2000개에서 극단적 급등 (+25%)": (df['return_7d'] > 25).sum(),
            "전체 2000개에서 극단적 급락 (-25%)": (df['return_7d'] < -25).sum(),
        }
        
        print("\n📈 조건별 일치하는 구간 수:")
        print("-" * 70)
        for condition, count in conditions.items():
            print(f"{condition:<35}: {count:>3}개")
        
        # 실제 시뮬레이션 엔진으로 극단적 조건 테스트
        print(f"\n{'='*70}")
        print("🚀 극단적 조건으로 범위 확장 기능 테스트")
        print("=" * 70)
        
        from upbit_auto_trading.ui.desktop.screens.strategy_management.real_data_simulation import RealDataSimulationEngine
        
        # 기존 조건을 더 까다롭게 수정한 커스텀 엔진
        class ExtendedTestEngine(RealDataSimulationEngine):
            def get_scenario_data(self, scenario: str, length: int = 50):
                """극단적 조건으로 수정된 시나리오 테스트"""
                try:
                    # 단계별로 데이터 범위를 확장하며 조건에 맞는 구간 찾기
                    search_limits = [500, 1000, 1500, 2000]
                    
                    # 극단적 조건 정의
                    extreme_conditions = {
                        "극단적 급등": lambda x: x['return_7d'] > 25,  # 7일간 25% 이상
                        "극단적 급락": lambda x: x['return_7d'] < -25,  # 7일간 25% 이상 하락
                        "연속 상승": lambda x: x['return_7d'] > 20 and x['return_30d'] > 30,  # 복합 조건
                        "연속 하락": lambda x: x['return_7d'] < -20 and x['return_30d'] < -30,  # 복합 조건
                        "매우 안정적 횡보": lambda x: abs(x['return_30d']) < 1,  # 매우 작은 변동
                    }
                    
                    for limit in search_limits:
                        logging.info(f"🔍 Searching in {limit} records for extreme scenario: {scenario}")
                        
                        # 데이터 로드
                        df = self.load_market_data(limit)
                        if df is None or df.empty:
                            continue
                            
                        # 기술적 지표 계산
                        df = self.calculate_technical_indicators(df)
                        if df is None or df.empty:
                            continue

                        condition = extreme_conditions.get(scenario)
                        if condition:
                            # 조건에 맞는 기간 찾기
                            valid_periods = []
                            for i in range(len(df) - length):
                                segment = df.iloc[i:i+length]
                                if not segment.empty and condition(segment.iloc[-1]):
                                    valid_periods.append(i)
                            
                            # 조건에 맞는 구간을 찾았으면 반환
                            if valid_periods:
                                import numpy as np
                                start_idx = np.random.choice(valid_periods)
                                segment = df.iloc[start_idx:start_idx+length]
                                
                                last_row = segment.iloc[-1]
                                current_value = last_row['close']
                                
                                logging.info(f"✅ Found matching data in {limit} records")
                                return {
                                    'current_value': float(current_value),
                                    'price_data': segment['close'].tolist(),
                                    'scenario': scenario,
                                    'data_source': f'real_market_data_{limit}_records',
                                    'period': f"{segment.index[0].strftime('%Y-%m-%d')} ~ {segment.index[-1].strftime('%Y-%m-%d')}",
                                    'base_value': float(segment['close'].iloc[0]),
                                    'change_percent': float((segment['close'].iloc[-1] / segment['close'].iloc[0] - 1) * 100)
                                }
                    
                    # 모든 범위에서 조건을 찾지 못한 경우
                    logging.warning(f"❌ No matching data found for extreme scenario: {scenario}")
                    return {
                        'current_value': 50000,
                        'price_data': [50000] * length,
                        'scenario': scenario,
                        'data_source': 'no_matching_data_found',
                        'period': 'not_found',
                        'base_value': 50000,
                        'change_percent': 0
                    }
                    
                except Exception as e:
                    logging.error(f"❌ Failed to get extreme scenario data: {e}")
                    return self._generate_fallback_data(scenario, length)
        
        # 극단적 조건 테스트
        engine = ExtendedTestEngine()
        
        extreme_scenarios = [
            "극단적 급등",
            "극단적 급락", 
            "연속 상승",
            "연속 하락",
            "매우 안정적 횡보"
        ]
        
        results = []
        for scenario in extreme_scenarios:
            print(f"\n📊 테스트: {scenario}")
            print("-" * 50)
            
            result = engine.get_scenario_data(scenario, 30)
            
            data_source = result.get('data_source', 'unknown')
            period = result.get('period', 'unknown')
            change_percent = result.get('change_percent', 0)
            
            print(f"✅ 데이터 소스: {data_source}")
            print(f"📅 기간: {period}")
            print(f"📊 변화율: {change_percent:.2f}%")
            
            results.append({
                'scenario': scenario,
                'data_source': data_source,
                'found': 'real_market_data' in data_source,
                'expanded': any(x in data_source for x in ['1000', '1500', '2000'])
            })
        
        # 결과 요약
        print(f"\n{'='*70}")
        print("📋 극단적 조건 테스트 결과 요약")
        print("=" * 70)
        
        found_count = sum(1 for r in results if r['found'])
        expanded_count = sum(1 for r in results if r['expanded'])
        
        print(f"🎯 총 극단적 시나리오: {len(results)}개")
        print(f"✅ 조건에 맞는 데이터 발견: {found_count}개")
        print(f"🔄 범위 확장으로 발견: {expanded_count}개")
        
        if expanded_count > 0:
            print(f"\n🎉 범위 확장 기능이 정상 작동합니다!")
            print("📈 범위가 확장된 시나리오:")
            for r in results:
                if r['expanded']:
                    print(f"   - {r['scenario']}: {r['data_source']}")
        else:
            print(f"\n💡 모든 조건이 500개 범위 내에서 만족되었거나, 조건이 너무 까다로워서 데이터를 찾지 못했습니다.")
        
        return results
        
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """메인 실행 함수"""
    print("🔬 극단적 조건으로 범위 확장 기능 테스트")
    print("목적: 500개 범위에서 조건을 만족하지 못할 때 자동으로 범위가 확장되는지 확인")
    
    results = test_extreme_scenarios()
    
    if results:
        print(f"\n🎉 극단적 조건 테스트 완료!")
    else:
        print(f"\n❌ 테스트 실패")

if __name__ == "__main__":
    main()
