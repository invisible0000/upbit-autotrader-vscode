"""
DB 없이도 작동하는 강화된 시뮬레이션 엔진
실제 데이터가 없어도 현실적인 시뮬레이션 데이터를 생성
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import os
import sqlite3

class RobustSimulationEngine:
    """DB 없이도 작동하는 강화된 시뮬레이션 엔진"""
    
    def __init__(self, data_db_path: str = "data/market_data.sqlite3"):
        """
        강화된 시뮬레이션 엔진 초기화
        
        Args:
            data_db_path: 시장 데이터 DB 경로 (없어도 작동)
        """
        self.data_db_path = data_db_path
        self.cache_data = None
        self.cache_indicators = None
        
        # 내장 시드 데이터 (DB 없을 때 사용)
        self.seed_patterns = self._generate_seed_patterns()
        
    def _generate_seed_patterns(self) -> Dict[str, np.ndarray]:
        """시나리오별 시드 패턴 생성 (DB 없을 때 기본 템플릿)"""
        np.random.seed(42)  # 일관된 결과를 위한 시드 고정
        
        patterns = {}
        base_length = 365  # 1년 데이터
        
        # 비트코인 실제 특성을 반영한 기본 패턴들
        btc_base_price = 45000000  # 4천5백만원 기준
        
        # 1. 상승 추세 패턴 (2020년 하반기 스타일)
        uptrend = []
        for i in range(base_length):
            # 전체적인 상승 트렌드 + 일일 변동성
            trend_factor = 1 + (i / base_length) * 2.5  # 250% 상승
            daily_volatility = np.random.normal(1, 0.05)  # 5% 일일 변동성
            price = btc_base_price * trend_factor * daily_volatility
            uptrend.append(max(price, btc_base_price * 0.5))  # 최소 50% 하락 제한
        patterns['uptrend'] = np.array(uptrend)
        
        # 2. 하락 추세 패턴 (2022년 베어마켓 스타일)
        downtrend = []
        for i in range(base_length):
            trend_factor = 1 - (i / base_length) * 0.7  # 70% 하락
            daily_volatility = np.random.normal(1, 0.06)  # 6% 일일 변동성 (하락장에서 더 높음)
            price = btc_base_price * trend_factor * daily_volatility
            downtrend.append(max(price, btc_base_price * 0.2))  # 최소 80% 하락 제한
        patterns['downtrend'] = np.array(downtrend)
        
        # 3. 횡보 패턴
        sideways = []
        for i in range(base_length):
            # 작은 사이클과 노이즈
            cycle = np.sin(i * 2 * np.pi / 30) * 0.1  # 30일 주기
            noise = np.random.normal(0, 0.03)  # 3% 노이즈
            price = btc_base_price * (1 + cycle + noise)
            sideways.append(price)
        patterns['sideways'] = np.array(sideways)
        
        # 4. 급등 패턴 (갑작스러운 상승)
        surge = []
        surge_start = base_length // 3
        surge_duration = 30
        for i in range(base_length):
            if surge_start <= i < surge_start + surge_duration:
                # 급등 구간
                surge_progress = (i - surge_start) / surge_duration
                surge_factor = 1 + surge_progress * 0.8  # 80% 급등
            else:
                surge_factor = 1 + np.random.normal(0, 0.02)  # 평상시 2% 변동
            price = btc_base_price * surge_factor
            surge.append(price)
        patterns['surge'] = np.array(surge)
        
        # 5. 급락 패턴
        crash = []
        crash_start = base_length // 2
        crash_duration = 14
        for i in range(base_length):
            if crash_start <= i < crash_start + crash_duration:
                # 급락 구간
                crash_progress = (i - crash_start) / crash_duration
                crash_factor = 1 - crash_progress * 0.4  # 40% 급락
            else:
                crash_factor = 1 + np.random.normal(0, 0.025)  # 평상시 2.5% 변동
            price = btc_base_price * crash_factor
            crash.append(price)
        patterns['crash'] = np.array(crash)
        
        return patterns
    
    def load_market_data(self, limit: int = 500) -> Optional[pd.DataFrame]:
        """시장 데이터 로드 (DB 없으면 시드 데이터 사용)"""
        try:
            # 1. 실제 DB 시도
            if os.path.exists(self.data_db_path):
                logging.info("Real DB found, loading actual market data...")
                return self._load_real_data(limit)
            else:
                logging.warning(f"DB not found: {self.data_db_path}")
                logging.info("Generating realistic fallback data...")
                return self._generate_realistic_fallback_data(limit)
                
        except Exception as e:
            logging.error(f"Failed to load market data: {e}")
            logging.info("Falling back to synthetic data...")
            return self._generate_realistic_fallback_data(limit)
    
    def _load_real_data(self, limit: int) -> Optional[pd.DataFrame]:
        """실제 DB에서 데이터 로드"""
        try:
            conn = sqlite3.connect(self.data_db_path)
            
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
            LIMIT ?
            """
            
            df = pd.read_sql(query, conn, params=(limit,))
            conn.close()
            
            if df.empty:
                return None
            
            # 데이터 정렬 및 처리
            df = df.sort_values('timestamp').reset_index(drop=True)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
            
            # 숫자형 변환
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            logging.info(f"Real market data loaded: {len(df)} records")
            self.cache_data = df
            return df
            
        except Exception as e:
            logging.error(f"Failed to load real data: {e}")
            return None
    
    def _generate_realistic_fallback_data(self, limit: int) -> pd.DataFrame:
        """현실적인 폴백 데이터 생성 (DB 없을 때)"""
        try:
            # 여러 패턴을 조합한 현실적인 데이터 생성
            logging.info(f"Generating {limit} days of realistic BTC data...")
            
            # 시드 패턴 중 하나를 선택하고 조합
            pattern_keys = list(self.seed_patterns.keys())
            selected_patterns = np.random.choice(pattern_keys, size=3, replace=False)
            
            # 패턴들을 조합
            combined_data = []
            segment_size = limit // 3
            
            for i, pattern_key in enumerate(selected_patterns):
                pattern = self.seed_patterns[pattern_key]
                start_idx = np.random.randint(0, len(pattern) - segment_size)
                segment = pattern[start_idx:start_idx + segment_size]
                combined_data.extend(segment)
            
            # 부족한 부분은 마지막 패턴으로 채움
            while len(combined_data) < limit:
                pattern = self.seed_patterns[selected_patterns[-1]]
                idx = len(combined_data) % len(pattern)
                combined_data.append(pattern[idx])
            
            combined_data = combined_data[:limit]
            
            # DataFrame 생성
            end_date = datetime.now()
            start_date = end_date - timedelta(days=limit-1)
            
            dates = [start_date + timedelta(days=i) for i in range(limit)]
            
            df_data = {
                'timestamp': dates,
                'close': combined_data,
                'open': [],
                'high': [],
                'low': [],
                'volume': []
            }
            
            # OHLV 계산
            for i, close_price in enumerate(combined_data):
                # 일일 변동성을 고려한 OHLV 생성
                daily_volatility = 0.03  # 3% 일일 변동성
                
                # Open (전일 종가 기준)
                if i == 0:
                    open_price = close_price * np.random.uniform(0.98, 1.02)
                else:
                    open_price = combined_data[i-1] * np.random.uniform(0.995, 1.005)
                
                # High/Low (Open과 Close 기준으로 계산)
                price_range = [open_price, close_price]
                base_price = np.mean(price_range)
                
                high = base_price * (1 + np.random.uniform(0.01, daily_volatility))
                low = base_price * (1 - np.random.uniform(0.01, daily_volatility))
                
                # High는 Open/Close보다 높아야 하고, Low는 낮아야 함
                high = max(high, max(open_price, close_price))
                low = min(low, min(open_price, close_price))
                
                # Volume (현실적인 거래량)
                base_volume = 1000000000  # 10억원 기준
                volume_factor = np.random.uniform(0.5, 2.0)
                volume = base_volume * volume_factor
                
                df_data['open'].append(open_price)
                df_data['high'].append(high)
                df_data['low'].append(low)
                df_data['volume'].append(volume)
            
            df = pd.DataFrame(df_data)
            df = df.set_index('timestamp')
            
            logging.info(f"Realistic fallback data generated: {len(df)} records")
            logging.info(f"Price range: {df['close'].min():,.0f} ~ {df['close'].max():,.0f}")
            
            self.cache_data = df
            return df
            
        except Exception as e:
            logging.error(f"Failed to generate fallback data: {e}")
            return self._generate_simple_fallback_data(limit)
    
    def _generate_simple_fallback_data(self, limit: int) -> pd.DataFrame:
        """단순한 폴백 데이터 (최후의 수단)"""
        logging.warning("Using simple fallback data as last resort")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=limit-1)
        dates = [start_date + timedelta(days=i) for i in range(limit)]
        
        # 단순한 랜덤 워크
        base_price = 50000000
        prices = [base_price]
        
        for i in range(1, limit):
            change = np.random.normal(0, 0.02)  # 2% 일일 변동성
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, base_price * 0.1))  # 최소 10% 수준 유지
        
        df_data = {
            'close': prices,
            'open': [p * np.random.uniform(0.98, 1.02) for p in prices],
            'high': [p * np.random.uniform(1.01, 1.05) for p in prices],
            'low': [p * np.random.uniform(0.95, 0.99) for p in prices],
            'volume': [1000000000 * np.random.uniform(0.5, 2.0) for _ in prices]
        }
        
        df = pd.DataFrame(df_data, index=dates)
        df.index.name = 'timestamp'
        
        return df
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 계산 (실제 코드와 동일)"""
        try:
            if df is None or df.empty:
                return df
            
            # RSI 계산
            def calculate_rsi(prices, period=14):
                delta = prices.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                return rsi
            
            # 이동평균 계산
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_60'] = df['close'].rolling(window=60).mean()
            
            # RSI 계산
            df['rsi'] = calculate_rsi(df['close'])
            
            # 변동성 계산 (30일)
            df['volatility_30d'] = df['close'].pct_change().rolling(window=30).std() * 100
            
            # 수익률 계산
            df['return_7d'] = df['close'].pct_change(7) * 100
            df['return_30d'] = df['close'].pct_change(30) * 100
            
            self.cache_indicators = df
            logging.info("Technical indicators calculated")
            return df
            
        except Exception as e:
            logging.error(f"Failed to calculate indicators: {e}")
            return df
    
    def get_scenario_data(self, scenario: str, length: int = 50) -> Dict[str, Any]:
        """시나리오에 맞는 데이터 추출 (DB 없어도 작동)"""
        try:
            # 데이터 로드 (실제 DB 또는 폴백)
            df = self.load_market_data(500)
            
            if df is None or df.empty:
                logging.error("All data loading methods failed")
                return self._generate_emergency_fallback(scenario, length)
            
            # 기술적 지표 계산
            df = self.calculate_technical_indicators(df)
            
            # 시나리오별 조건
            scenario_conditions = {
                "상승 추세": lambda x: x['return_30d'] > 5,
                "하락 추세": lambda x: x['return_30d'] < -5,
                "급등": lambda x: x['return_7d'] > 15,
                "급락": lambda x: x['return_7d'] < -15,
                "횡보": lambda x: abs(x['return_30d']) < 3,
                "이동평균 교차": lambda x: True
            }
            
            condition = scenario_conditions.get(scenario)
            if condition:
                # 조건에 맞는 기간 찾기
                valid_periods = []
                for i in range(len(df) - length):
                    segment = df.iloc[i:i+length]
                    if not segment.empty and condition(segment.iloc[-1]):
                        valid_periods.append(i)
                
                if valid_periods:
                    start_idx = np.random.choice(valid_periods)
                    segment = df.iloc[start_idx:start_idx+length]
                else:
                    segment = df.tail(length)
            else:
                segment = df.tail(length)
            
            # 결과 반환
            if not segment.empty:
                last_row = segment.iloc[-1]
                
                if '교차' in scenario:
                    current_value = last_row['sma_20'] - last_row['sma_60']
                elif 'rsi' in scenario.lower():
                    current_value = last_row['rsi']
                else:
                    current_value = last_row['close']
                
                data_source = 'real_market_data' if os.path.exists(self.data_db_path) else 'synthetic_realistic_data'
                
                return {
                    'current_value': float(current_value) if not pd.isna(current_value) else 50.0,
                    'price_data': segment['close'].tolist(),
                    'scenario': scenario,
                    'data_source': data_source,
                    'period': f"{segment.index[0].strftime('%Y-%m-%d')} ~ {segment.index[-1].strftime('%Y-%m-%d')}",
                    'base_value': float(segment['close'].iloc[0]),
                    'change_percent': float((segment['close'].iloc[-1] / segment['close'].iloc[0] - 1) * 100)
                }
            
        except Exception as e:
            logging.error(f"Failed to get scenario data: {e}")
            
        return self._generate_emergency_fallback(scenario, length)
    
    def _generate_emergency_fallback(self, scenario: str, length: int) -> Dict[str, Any]:
        """비상용 최종 폴백 (모든 것이 실패했을 때)"""
        logging.warning("Using emergency fallback data")
        
        base_value = 50000000  # 5천만원
        
        # 시나리오별 간단한 패턴
        if scenario in ["상승 추세", "급등"]:
            trend = np.linspace(0, base_value * 0.15, length)
            noise = np.random.randn(length) * base_value * 0.02
            price_data = base_value + trend + noise
        elif scenario in ["하락 추세", "급락"]:
            trend = np.linspace(0, -base_value * 0.15, length)
            noise = np.random.randn(length) * base_value * 0.02
            price_data = base_value + trend + noise
        else:  # 횡보 등
            noise = np.random.randn(length) * base_value * 0.01
            price_data = base_value + noise
        
        # 음수 방지
        price_data = np.maximum(price_data, base_value * 0.1)
        
        return {
            'current_value': float(price_data[-1]),
            'price_data': price_data.tolist(),
            'scenario': scenario,
            'data_source': 'emergency_fallback',
            'period': 'simulated_emergency_data',
            'base_value': base_value,
            'change_percent': (price_data[-1] / price_data[0] - 1) * 100
        }

# 기존 RealDataSimulationEngine을 강화된 버전으로 확장
class EnhancedRealDataSimulationEngine(RobustSimulationEngine):
    """기존 기능과 호환되는 강화된 시뮬레이션 엔진"""
    pass

# 전역 인스턴스 (UI에서 사용)
_simulation_engine = None

def get_simulation_engine():
    """강화된 시뮬레이션 엔진 싱글톤 인스턴스 반환"""
    global _simulation_engine
    if _simulation_engine is None:
        _simulation_engine = EnhancedRealDataSimulationEngine()
    return _simulation_engine
