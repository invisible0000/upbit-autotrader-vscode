"""
실제 KRW-BTC 데이터 기반 시나리오 매핑 시스템
- 실제 시장 데이터에서 각 시나리오에 맞는 구간 추출
- 시뮬레이션용 세그먼트 생성 및 관리
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataScenarioMapper:
    def __init__(self, db_path: str = "data/upbit_auto_trading.sqlite3"):
        """
        실제 데이터 기반 시나리오 매핑 시스템 초기화
        
        Args:
            db_path: 실제 KRW-BTC 데이터가 있는 DB 경로
        """
        self.db_path = db_path
        self.scenario_configs = {
            "📈 상승": {
                "name": "상승 트렌드",
                "description": "장기적 상승 추세 구간",
                "criteria": {
                    "min_return": 10.0,  # 최소 10% 상승
                    "min_duration_hours": 72,  # 최소 3일간
                    "trend_consistency": 0.7  # 70% 이상 상승 추세
                },
                "market_conditions": "bull_trend"
            },
            "📉 하락": {
                "name": "하락 트렌드", 
                "description": "장기적 하락 추세 구간",
                "criteria": {
                    "max_return": -10.0,  # 최소 10% 하락
                    "min_duration_hours": 72,  # 최소 3일간
                    "trend_consistency": 0.7  # 70% 이상 하락 추세
                },
                "market_conditions": "bear_trend"
            },
            "🚀 급등": {
                "name": "급등",
                "description": "단기간 급격한 상승",
                "criteria": {
                    "min_return": 15.0,  # 최소 15% 상승
                    "max_duration_hours": 24,  # 최대 1일간
                    "volatility_threshold": 5.0  # 변동성 5% 이상
                },
                "market_conditions": "pump"
            },
            "💥 급락": {
                "name": "급락",
                "description": "단기간 급격한 하락",
                "criteria": {
                    "max_return": -15.0,  # 최소 15% 하락
                    "max_duration_hours": 24,  # 최대 1일간
                    "volatility_threshold": 5.0  # 변동성 5% 이상
                },
                "market_conditions": "dump"
            },
            "➡️ 횡보": {
                "name": "횡보",
                "description": "변동성이 낮은 박스권",
                "criteria": {
                    "max_return_abs": 5.0,  # 절대값 5% 이하 변동
                    "min_duration_hours": 48,  # 최소 2일간
                    "max_volatility": 2.0  # 변동성 2% 이하
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
                    "min_duration_hours": 12  # 최소 12시간
                },
                "market_conditions": "cross_signal"
            }
        }
    
    def load_market_data(self) -> pd.DataFrame:
        """
        실제 KRW-BTC 시장 데이터 로드
        
        Returns:
            DataFrame: timestamp, open, high, low, close, volume 컬럼을 가진 데이터프레임
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # market_data 테이블에서 KRW-BTC 데이터 조회
            query = """
            SELECT timestamp, open, high, low, close, volume
            FROM market_data
            WHERE symbol = 'KRW-BTC' AND timeframe = '1h'
            ORDER BY timestamp ASC
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            # 타임스탬프 변환
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            logging.info(f"✅ 시장 데이터 로드 완료: {len(df)}개 캔들")
            logging.info(f"📅 데이터 기간: {df.index.min()} ~ {df.index.max()}")
            
            return df
            
        except Exception as e:
            logging.error(f"❌ 데이터 로드 실패: {e}")
            return pd.DataFrame()
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        기술적 지표 계산
        
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
        
        # 변동성 계산 (최근 24시간)
        df['volatility_24h'] = df['close'].rolling(window=24).std() / df['close'].rolling(window=24).mean() * 100
        
        # 수익률 계산 (24시간, 72시간)
        df['return_24h'] = (df['close'] / df['close'].shift(24) - 1) * 100
        df['return_72h'] = (df['close'] / df['close'].shift(72) - 1) * 100
        
        return df
    
    def find_scenario_segments(self, df: pd.DataFrame, scenario: str) -> List[Dict]:
        """
        특정 시나리오에 맞는 데이터 세그먼트 찾기
        
        Args:
            df: 기술적 지표가 포함된 데이터프레임
            scenario: 시나리오 키 (예: "📈 상승")
            
        Returns:
            List[Dict]: 시나리오에 맞는 세그먼트 정보 리스트
        """
        if scenario not in self.scenario_configs:
            return []
        
        config = self.scenario_configs[scenario]
        criteria = config["criteria"]
        segments = []
        
        if scenario == "📈 상승":
            # 상승 트렌드 세그먼트 찾기
            for i in range(len(df) - 72):
                segment = df.iloc[i:i+72]
                if len(segment) < 72:
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
                        "duration_hours": len(segment),
                        "scenario": scenario
                    })
        
        elif scenario == "📉 하락":
            # 하락 트렌드 세그먼트 찾기
            for i in range(len(df) - 72):
                segment = df.iloc[i:i+72]
                if len(segment) < 72:
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
                        "duration_hours": len(segment),
                        "scenario": scenario
                    })
        
        elif scenario == "🚀 급등":
            # 급등 세그먼트 찾기
            for i in range(len(df) - 24):
                segment = df.iloc[i:i+24]
                if len(segment) < 24:
                    continue
                    
                start_price = segment['close'].iloc[0]
                max_price = segment['high'].max()
                return_pct = (max_price / start_price - 1) * 100
                volatility = segment['volatility_24h'].iloc[-1] if not pd.isna(segment['volatility_24h'].iloc[-1]) else 0
                
                if (return_pct >= criteria["min_return"] and 
                    volatility >= criteria["volatility_threshold"]):
                    segments.append({
                        "start_time": segment.index[0],
                        "end_time": segment.index[-1],
                        "return_pct": return_pct,
                        "volatility": volatility,
                        "max_price": max_price,
                        "scenario": scenario
                    })
        
        elif scenario == "💥 급락":
            # 급락 세그먼트 찾기
            for i in range(len(df) - 24):
                segment = df.iloc[i:i+24]
                if len(segment) < 24:
                    continue
                    
                start_price = segment['close'].iloc[0]
                min_price = segment['low'].min()
                return_pct = (min_price / start_price - 1) * 100
                volatility = segment['volatility_24h'].iloc[-1] if not pd.isna(segment['volatility_24h'].iloc[-1]) else 0
                
                if (return_pct <= criteria["max_return"] and 
                    volatility >= criteria["volatility_threshold"]):
                    segments.append({
                        "start_time": segment.index[0],
                        "end_time": segment.index[-1],
                        "return_pct": return_pct,
                        "volatility": volatility,
                        "min_price": min_price,
                        "scenario": scenario
                    })
        
        elif scenario == "➡️ 횡보":
            # 횡보 세그먼트 찾기
            for i in range(len(df) - 48):
                segment = df.iloc[i:i+48]
                if len(segment) < 48:
                    continue
                    
                start_price = segment['close'].iloc[0]
                end_price = segment['close'].iloc[-1]
                max_price = segment['high'].max()
                min_price = segment['low'].min()
                
                return_pct = abs(end_price / start_price - 1) * 100
                price_range = abs(max_price / min_price - 1) * 100
                volatility = segment['volatility_24h'].mean() if not segment['volatility_24h'].isna().all() else 0
                
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
            
            # 골든크로스 찾기 (20일선이 60일선을 상향 돌파)
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
                        "sma_60": df_cross['sma_60'].iloc[i]
                    })
                # 데드크로스 (양수에서 음수로)
                elif prev_diff >= 0 and curr_diff < 0:
                    cross_points.append({
                        "cross_time": df_cross.index[i],
                        "cross_type": "dead_cross",
                        "sma_20": df_cross['sma_20'].iloc[i],
                        "sma_60": df_cross['sma_60'].iloc[i]
                    })
            
            # 크로스 포인트 주변 12시간 세그먼트 생성
            for cross in cross_points:
                cross_idx = df_cross.index.get_loc(cross["cross_time"])
                start_idx = max(0, cross_idx - 6)
                end_idx = min(len(df_cross) - 1, cross_idx + 6)
                
                segment = df_cross.iloc[start_idx:end_idx+1]
                if len(segment) >= 12:
                    segments.append({
                        "start_time": segment.index[0],
                        "end_time": segment.index[-1],
                        "cross_time": cross["cross_time"],
                        "cross_type": cross["cross_type"],
                        "sma_20": cross["sma_20"],
                        "sma_60": cross["sma_60"],
                        "scenario": scenario
                    })
        
        logging.info(f"🔍 {scenario} 시나리오 세그먼트 {len(segments)}개 발견")
        return segments[:5]  # 최대 5개 세그먼트만 반환
    
    def generate_all_scenarios(self) -> Dict[str, List[Dict]]:
        """
        모든 시나리오에 대한 세그먼트 생성
        
        Returns:
            Dict: 시나리오별 세그먼트 정보
        """
        logging.info("🚀 시나리오 매핑 시작...")
        
        # 시장 데이터 로드
        df = self.load_market_data()
        if df.empty:
            return {}
        
        # 기술적 지표 계산
        df = self.calculate_technical_indicators(df)
        
        # 각 시나리오별 세그먼트 찾기
        all_scenarios = {}
        for scenario in self.scenario_configs.keys():
            segments = self.find_scenario_segments(df, scenario)
            all_scenarios[scenario] = segments
        
        return all_scenarios
    
    def print_scenario_summary(self, scenarios: Dict[str, List[Dict]]):
        """
        시나리오 요약 출력
        
        Args:
            scenarios: 시나리오별 세그먼트 정보
        """
        print("🎯 === 시나리오 매핑 결과 ===")
        print("=" * 60)
        
        for scenario, segments in scenarios.items():
            config = self.scenario_configs[scenario]
            print(f"\n{scenario} {config['name']}")
            print(f"📋 설명: {config['description']}")
            print(f"🔍 발견된 세그먼트: {len(segments)}개")
            
            if segments:
                print("📅 주요 세그먼트:")
                for i, segment in enumerate(segments[:3], 1):
                    start_time = segment['start_time'].strftime('%Y-%m-%d %H:%M')
                    end_time = segment['end_time'].strftime('%Y-%m-%d %H:%M')
                    print(f"  {i}. {start_time} ~ {end_time}")
                    
                    if 'return_pct' in segment:
                        print(f"     💰 수익률: {segment['return_pct']:.2f}%")
                    if 'volatility' in segment:
                        print(f"     📊 변동성: {segment['volatility']:.2f}%")
                    if 'cross_type' in segment:
                        print(f"     🔄 크로스: {segment['cross_type']}")
            else:
                print("❌ 조건에 맞는 세그먼트를 찾을 수 없음")
            
            print("-" * 40)

def main():
    """메인 실행 함수"""
    print("🕐 시나리오 매핑 시작:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    try:
        # 시나리오 매퍼 초기화
        mapper = DataScenarioMapper()
        
        # 모든 시나리오 생성
        scenarios = mapper.generate_all_scenarios()
        
        # 결과 출력
        mapper.print_scenario_summary(scenarios)
        
        print(f"\n✅ 시나리오 매핑 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return scenarios
        
    except Exception as e:
        logging.error(f"❌ 시나리오 매핑 실패: {e}")
        return {}

if __name__ == "__main__":
    scenarios = main()
