"""
확장된 KRW-BTC 데이터 분석 및 시나리오 매핑
- 2017-2025년 데이터로 더 정확한 시나리오 검출
- 일봉 데이터 기반 장기 트렌드 분석
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ExtendedDataScenarioMapper:
    def __init__(self, db_path: str = "data/upbit_auto_trading.sqlite3"):
        """
        확장된 데이터 기반 시나리오 매핑 시스템 초기화
        
        Args:
            db_path: KRW-BTC 데이터가 있는 DB 경로
        """
        self.db_path = db_path
        self.scenario_configs = {
            "📈 상승": {
                "name": "상승 트렌드",
                "description": "장기적 상승 추세 구간",
                "criteria": {
                    "min_return": 20.0,  # 최소 20% 상승 (일봉 기준)
                    "min_duration_days": 30,  # 최소 30일간
                    "trend_consistency": 0.6  # 60% 이상 상승 추세
                },
                "market_conditions": "bull_trend"
            },
            "📉 하락": {
                "name": "하락 트렌드", 
                "description": "장기적 하락 추세 구간",
                "criteria": {
                    "max_return": -20.0,  # 최소 20% 하락
                    "min_duration_days": 30,  # 최소 30일간
                    "trend_consistency": 0.6  # 60% 이상 하락 추세
                },
                "market_conditions": "bear_trend"
            },
            "🚀 급등": {
                "name": "급등",
                "description": "단기간 급격한 상승",
                "criteria": {
                    "min_return": 30.0,  # 최소 30% 상승
                    "max_duration_days": 14,  # 최대 2주간
                    "volatility_threshold": 5.0  # 변동성 5% 이상
                },
                "market_conditions": "pump"
            },
            "💥 급락": {
                "name": "급락",
                "description": "단기간 급격한 하락",
                "criteria": {
                    "max_return": -30.0,  # 최소 30% 하락
                    "max_duration_days": 14,  # 최대 2주간
                    "volatility_threshold": 5.0  # 변동성 5% 이상
                },
                "market_conditions": "dump"
            },
            "➡️ 횡보": {
                "name": "횡보",
                "description": "변동성이 낮은 박스권",
                "criteria": {
                    "max_return_abs": 10.0,  # 절대값 10% 이하 변동
                    "min_duration_days": 30,  # 최소 30일간
                    "max_volatility": 3.0  # 변동성 3% 이하
                },
                "market_conditions": "sideways"
            },
            "🔄 지수크로스": {
                "name": "이동평균 크로스",
                "description": "이동평균선 교차 구간",
                "criteria": {
                    "cross_type": "golden_cross",  # 골든크로스 또는 데드크로스
                    "ma_short": 20,
                    "ma_long": 60,
                    "min_duration_days": 7  # 최소 7일
                },
                "market_conditions": "cross_signal"
            },
            "🌪️ 고변동성": {
                "name": "고변동성",
                "description": "높은 변동성 구간",
                "criteria": {
                    "min_volatility": 4.0,  # 변동성 4% 이상 (조정)
                    "min_duration_days": 7,  # 최소 7일간
                    "price_swing": 25.0  # 최고/최저 25% 차이 (조정)
                },
                "market_conditions": "high_volatility"
            },
            "😴 저변동성": {
                "name": "저변동성",
                "description": "낮은 변동성 구간",
                "criteria": {
                    "max_volatility": 1.5,  # 변동성 1.5% 이하 (조정)
                    "min_duration_days": 10,  # 최소 10일간 (조정)
                    "max_price_swing": 8.0  # 최고/최저 8% 이하 (조정)
                },
                "market_conditions": "low_volatility"
            }
        }
    
    def load_daily_market_data(self) -> pd.DataFrame:
        """
        일봉 KRW-BTC 시장 데이터 로드
        
        Returns:
            DataFrame: timestamp, open, high, low, close, volume 컬럼을 가진 데이터프레임
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 일봉 데이터 조회 (timeframe이 1d인 데이터 우선, 없으면 ohlcv_data 테이블)
            queries = [
                """
                SELECT timestamp, open, high, low, close, volume
                FROM market_data
                WHERE symbol = 'KRW-BTC' AND timeframe = '1d'
                ORDER BY timestamp ASC
                """,
                """
                SELECT timestamp, open, high, low, close, volume
                FROM ohlcv_data
                WHERE symbol = 'KRW-BTC'
                ORDER BY timestamp ASC
                """,
                """
                SELECT timestamp, open, high, low, close, volume
                FROM market_data
                WHERE symbol = 'KRW-BTC'
                ORDER BY timestamp ASC
                LIMIT 3000
                """
            ]
            
            df = pd.DataFrame()
            for query in queries:
                try:
                    df = pd.read_sql_query(query, conn)
                    if not df.empty:
                        logging.info(f"✅ 쿼리 성공: {len(df)}개 캔들")
                        break
                except Exception as e:
                    logging.warning(f"⚠️ 쿼리 실패: {e}")
                    continue
            
            conn.close()
            
            if df.empty:
                logging.error("❌ 모든 쿼리 실패")
                return df
            
            # 타임스탬프 변환
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # 중복 제거 및 정렬
            df = df.drop_duplicates().sort_index()
            
            logging.info(f"✅ 일봉 데이터 로드 완료: {len(df)}개 캔들")
            logging.info(f"📅 데이터 기간: {df.index.min()} ~ {df.index.max()}")
            
            return df
            
        except Exception as e:
            logging.error(f"❌ 데이터 로드 실패: {e}")
            return pd.DataFrame()
    
    def calculate_daily_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        일봉 기반 기술적 지표 계산
        
        Args:
            df: OHLCV 데이터프레임
            
        Returns:
            DataFrame: 기술적 지표가 추가된 데이터프레임
        """
        # RSI 계산
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 이동평균선 계산
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_60'] = df['close'].rolling(window=60).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # 변동성 계산 (최근 30일)
        df['volatility_30d'] = df['close'].rolling(window=30).std() / df['close'].rolling(window=30).mean() * 100
        
        # 수익률 계산 (7일, 30일, 90일)
        df['return_7d'] = (df['close'] / df['close'].shift(7) - 1) * 100
        df['return_30d'] = (df['close'] / df['close'].shift(30) - 1) * 100
        df['return_90d'] = (df['close'] / df['close'].shift(90) - 1) * 100
        
        # 볼린저 밴드
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        return df
    
    def find_extended_scenario_segments(self, df: pd.DataFrame, scenario: str) -> List[Dict]:
        """
        확장된 데이터에서 시나리오 세그먼트 찾기
        
        Args:
            df: 기술적 지표가 포함된 데이터프레임
            scenario: 시나리오 키
            
        Returns:
            List[Dict]: 시나리오에 맞는 세그먼트 정보 리스트
        """
        if scenario not in self.scenario_configs:
            return []
        
        config = self.scenario_configs[scenario]
        criteria = config["criteria"]
        segments = []
        
        if scenario == "📈 상승":
            # 상승 트렌드 세그먼트 찾기 (30일 윈도우)
            for i in range(len(df) - 30):
                segment = df.iloc[i:i+30]
                if len(segment) < 30:
                    continue
                    
                start_price = segment['close'].iloc[0]
                end_price = segment['close'].iloc[-1]
                return_pct = (end_price / start_price - 1) * 100
                
                # 상승 일수 비율 계산
                daily_returns = segment['close'].pct_change().dropna()
                positive_days = (daily_returns > 0).sum()
                trend_consistency = positive_days / len(daily_returns)
                
                if (return_pct >= criteria["min_return"] and 
                    trend_consistency >= criteria["trend_consistency"]):
                    segments.append({
                        "start_time": segment.index[0],
                        "end_time": segment.index[-1],
                        "return_pct": return_pct,
                        "trend_consistency": trend_consistency,
                        "duration_days": len(segment),
                        "start_price": start_price,
                        "end_price": end_price,
                        "scenario": scenario
                    })
        
        elif scenario == "📉 하락":
            # 하락 트렌드 세그먼트 찾기 (30일 윈도우)
            for i in range(len(df) - 30):
                segment = df.iloc[i:i+30]
                if len(segment) < 30:
                    continue
                    
                start_price = segment['close'].iloc[0]
                end_price = segment['close'].iloc[-1]
                return_pct = (end_price / start_price - 1) * 100
                
                # 하락 일수 비율 계산
                daily_returns = segment['close'].pct_change().dropna()
                negative_days = (daily_returns < 0).sum()
                trend_consistency = negative_days / len(daily_returns)
                
                if (return_pct <= criteria["max_return"] and 
                    trend_consistency >= criteria["trend_consistency"]):
                    segments.append({
                        "start_time": segment.index[0],
                        "end_time": segment.index[-1],
                        "return_pct": return_pct,
                        "trend_consistency": trend_consistency,
                        "duration_days": len(segment),
                        "start_price": start_price,
                        "end_price": end_price,
                        "scenario": scenario
                    })
        
        elif scenario == "🚀 급등":
            # 급등 세그먼트 찾기 (14일 윈도우)
            for i in range(len(df) - 14):
                segment = df.iloc[i:i+14]
                if len(segment) < 14:
                    continue
                    
                start_price = segment['close'].iloc[0]
                max_price = segment['high'].max()
                return_pct = (max_price / start_price - 1) * 100
                volatility = segment['volatility_30d'].mean() if not segment['volatility_30d'].isna().all() else 0
                
                if (return_pct >= criteria["min_return"] and 
                    volatility >= criteria["volatility_threshold"]):
                    segments.append({
                        "start_time": segment.index[0],
                        "end_time": segment.index[-1],
                        "return_pct": return_pct,
                        "volatility": volatility,
                        "max_price": max_price,
                        "start_price": start_price,
                        "scenario": scenario
                    })
        
        elif scenario == "💥 급락":
            # 급락 세그먼트 찾기 (14일 윈도우)
            for i in range(len(df) - 14):
                segment = df.iloc[i:i+14]
                if len(segment) < 14:
                    continue
                    
                start_price = segment['close'].iloc[0]
                min_price = segment['low'].min()
                return_pct = (min_price / start_price - 1) * 100
                volatility = segment['volatility_30d'].mean() if not segment['volatility_30d'].isna().all() else 0
                
                if (return_pct <= criteria["max_return"] and 
                    volatility >= criteria["volatility_threshold"]):
                    segments.append({
                        "start_time": segment.index[0],
                        "end_time": segment.index[-1],
                        "return_pct": return_pct,
                        "volatility": volatility,
                        "min_price": min_price,
                        "start_price": start_price,
                        "scenario": scenario
                    })
        
        elif scenario == "➡️ 횡보":
            # 횡보 세그먼트 찾기 (30일 윈도우)
            for i in range(len(df) - 30):
                segment = df.iloc[i:i+30]
                if len(segment) < 30:
                    continue
                    
                start_price = segment['close'].iloc[0]
                end_price = segment['close'].iloc[-1]
                max_price = segment['high'].max()
                min_price = segment['low'].min()
                
                return_pct = abs(end_price / start_price - 1) * 100
                price_range = abs(max_price / min_price - 1) * 100
                volatility = segment['volatility_30d'].mean() if not segment['volatility_30d'].isna().all() else 0
                
                if (return_pct <= criteria["max_return_abs"] and 
                    price_range <= criteria["max_return_abs"] and
                    volatility <= criteria["max_volatility"]):
                    segments.append({
                        "start_time": segment.index[0],
                        "end_time": segment.index[-1],
                        "return_pct": return_pct,
                        "price_range": price_range,
                        "volatility": volatility,
                        "scenario": scenario
                    })
        
        elif scenario == "🔄 지수크로스":
            # 이동평균 크로스 세그먼트 찾기
            df_cross = df.dropna(subset=['sma_20', 'sma_60'])
            
            # 골든크로스/데드크로스 찾기
            cross_points = []
            for i in range(1, len(df_cross)):
                prev_diff = df_cross['sma_20'].iloc[i-1] - df_cross['sma_60'].iloc[i-1]
                curr_diff = df_cross['sma_20'].iloc[i] - df_cross['sma_60'].iloc[i]
                
                # 골든크로스 (음수에서 양수로)
                if prev_diff <= 0 and curr_diff > 0:
                    cross_points.append({
                        "cross_time": df_cross.index[i],
                        "cross_type": "golden_cross",
                        "sma_20": df_cross['sma_20'].iloc[i],
                        "sma_60": df_cross['sma_60'].iloc[i],
                        "price": df_cross['close'].iloc[i]
                    })
                # 데드크로스 (양수에서 음수로)
                elif prev_diff >= 0 and curr_diff < 0:
                    cross_points.append({
                        "cross_time": df_cross.index[i],
                        "cross_type": "dead_cross",
                        "sma_20": df_cross['sma_20'].iloc[i],
                        "sma_60": df_cross['sma_60'].iloc[i],
                        "price": df_cross['close'].iloc[i]
                    })
            
            # 크로스 포인트 주변 7일 세그먼트 생성
            for cross in cross_points:
                try:
                    cross_idx = df_cross.index.get_loc(cross["cross_time"])
                    start_idx = max(0, cross_idx - 3)
                    end_idx = min(len(df_cross) - 1, cross_idx + 4)
                    
                    segment = df_cross.iloc[start_idx:end_idx+1]
                    if len(segment) >= 7:
                        segments.append({
                            "start_time": segment.index[0],
                            "end_time": segment.index[-1],
                            "cross_time": cross["cross_time"],
                            "cross_type": cross["cross_type"],
                            "sma_20": cross["sma_20"],
                            "sma_60": cross["sma_60"],
                            "cross_price": cross["price"],
                            "scenario": scenario
                        })
                except Exception as e:
                    logging.warning(f"⚠️ 크로스 세그먼트 생성 실패: {e}")
                    continue
        
        elif scenario == "🌪️ 고변동성":
            # 고변동성 세그먼트 찾기 (7일 윈도우)
            for i in range(len(df) - 7):
                segment = df.iloc[i:i+7]
                if len(segment) < 7:
                    continue
                    
                # 변동성 계산
                volatility = segment['volatility_30d'].mean() if not segment['volatility_30d'].isna().all() else 0
                
                # 가격 스윙 계산
                max_price = segment['high'].max()
                min_price = segment['low'].min()
                price_swing = (max_price / min_price - 1) * 100 if min_price > 0 else 0
                
                if (volatility >= criteria["min_volatility"] and 
                    price_swing >= criteria["price_swing"]):
                    segments.append({
                        "start_time": segment.index[0],
                        "end_time": segment.index[-1],
                        "volatility": volatility,
                        "price_swing": price_swing,
                        "max_price": max_price,
                        "min_price": min_price,
                        "scenario": scenario
                    })
        
        elif scenario == "😴 저변동성":
            # 저변동성 세그먼트 찾기 (10일 윈도우)
            for i in range(len(df) - 10):
                segment = df.iloc[i:i+10]
                if len(segment) < 10:
                    continue
                    
                # 변동성 계산
                volatility = segment['volatility_30d'].mean() if not segment['volatility_30d'].isna().all() else 0
                
                # 가격 스윙 계산
                max_price = segment['high'].max()
                min_price = segment['low'].min()
                price_swing = (max_price / min_price - 1) * 100 if min_price > 0 else 0
                
                if (volatility <= criteria["max_volatility"] and 
                    price_swing <= criteria["max_price_swing"]):
                    segments.append({
                        "start_time": segment.index[0],
                        "end_time": segment.index[-1],
                        "volatility": volatility,
                        "price_swing": price_swing,
                        "max_price": max_price,
                        "min_price": min_price,
                        "scenario": scenario
                    })
        
        # 중복 제거 및 정렬
        segments = sorted(segments, key=lambda x: x['start_time'])
        unique_segments = []
        for segment in segments:
            # 겹치는 세그먼트 제거
            is_duplicate = False
            for existing in unique_segments:
                if (abs((segment['start_time'] - existing['start_time']).days) < 7):
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_segments.append(segment)
        
        logging.info(f"🔍 {scenario} 시나리오 세그먼트 {len(unique_segments)}개 발견")
        return unique_segments[:10]  # 최대 10개 세그먼트만 반환
    
    def generate_all_extended_scenarios(self) -> Dict[str, List[Dict]]:
        """
        모든 시나리오에 대한 세그먼트 생성 (확장 데이터 기반)
        
        Returns:
            Dict: 시나리오별 세그먼트 정보
        """
        logging.info("🚀 확장 데이터 시나리오 매핑 시작...")
        
        # 일봉 시장 데이터 로드
        df = self.load_daily_market_data()
        if df.empty:
            return {}
        
        # 기술적 지표 계산
        df = self.calculate_daily_technical_indicators(df)
        
        # 각 시나리오별 세그먼트 찾기
        all_scenarios = {}
        for scenario in self.scenario_configs.keys():
            segments = self.find_extended_scenario_segments(df, scenario)
            all_scenarios[scenario] = segments
        
        return all_scenarios
    
    def print_extended_scenario_summary(self, scenarios: Dict[str, List[Dict]]):
        """
        확장 시나리오 요약 출력
        
        Args:
            scenarios: 시나리오별 세그먼트 정보
        """
        print("🎯 === 확장 데이터 시나리오 매핑 결과 ===")
        print("=" * 70)
        
        for scenario, segments in scenarios.items():
            config = self.scenario_configs[scenario]
            print(f"\n{scenario} {config['name']}")
            print(f"📋 설명: {config['description']}")
            print(f"🔍 발견된 세그먼트: {len(segments)}개")
            
            if segments:
                print("📅 주요 세그먼트:")
                for i, segment in enumerate(segments[:3], 1):
                    start_time = segment['start_time'].strftime('%Y-%m-%d')
                    end_time = segment['end_time'].strftime('%Y-%m-%d')
                    print(f"  {i}. {start_time} ~ {end_time}")
                    
                    if 'return_pct' in segment:
                        print(f"     💰 수익률: {segment['return_pct']:.2f}%")
                    if 'volatility' in segment:
                        print(f"     📊 변동성: {segment['volatility']:.2f}%")
                    if 'cross_type' in segment:
                        print(f"     🔄 크로스: {segment['cross_type']}")
                        print(f"     💵 크로스 가격: {segment.get('cross_price', 0):,.0f}원")
                    if 'trend_consistency' in segment:
                        print(f"     📈 트렌드 일관성: {segment['trend_consistency']:.1%}")
                    if 'start_price' in segment and 'end_price' in segment:
                        start_price = segment.get('start_price', 0)
                        end_price = segment.get('end_price', 0)
                        print(f"     💸 가격 변화: {start_price:,.0f}원 → {end_price:,.0f}원")
            else:
                print("❌ 조건에 맞는 세그먼트를 찾을 수 없음")
            
            print("-" * 50)

def main():
    """메인 실행 함수"""
    print("🕐 확장 데이터 시나리오 매핑 시작:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    try:
        # 확장 시나리오 매퍼 초기화
        mapper = ExtendedDataScenarioMapper()
        
        # 모든 시나리오 생성
        scenarios = mapper.generate_all_extended_scenarios()
        
        # 결과 출력
        mapper.print_extended_scenario_summary(scenarios)
        
        print(f"\n✅ 확장 데이터 시나리오 매핑 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return scenarios
        
    except Exception as e:
        logging.error(f"❌ 확장 시나리오 매핑 실패: {e}")
        return {}

if __name__ == "__main__":
    scenarios = main()
