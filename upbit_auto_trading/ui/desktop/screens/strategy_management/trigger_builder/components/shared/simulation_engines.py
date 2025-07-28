"""
시뮬레이션 엔진 모듈 - 기존 검증된 코드 통합
upbit_auto_trading/ui/desktop/screens/strategy_management/ 폴더의 검증된 엔진들을 통합
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import os
import sqlite3
import sys
from pathlib import Path

# 새로운 통합 DB 경로 시스템 import
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent.parent.parent.parent))
try:
    from database_paths import MARKET_DATA_DB_PATH
    USE_NEW_DB_PATHS = True
except ImportError:
    # 백업: 새 경로 시스템을 찾을 수 없으면 기존 방식 사용
    USE_NEW_DB_PATHS = False
    MARKET_DATA_DB_PATH = "data/market_data.sqlite3"

# TriggerCalculator import 추가
try:
    from .trigger_calculator import TriggerCalculator
except ImportError:
    print("⚠️ TriggerCalculator import 실패 - 폴백 사용")
    TriggerCalculator = None


class BaseSimulationEngine:
    """시뮬레이션 엔진 베이스 클래스"""
    
    def __init__(self):
        self.name = "Base"
        # TriggerCalculator 인스턴스 생성
        if TriggerCalculator:
            self.trigger_calculator = TriggerCalculator()
        else:
            self.trigger_calculator = None
        
    def load_market_data(self, limit: int = 100) -> Optional[pd.DataFrame]:
        """시장 데이터 로드"""
        raise NotImplementedError
        
    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 계산"""
        if data is None or data.empty:
            return data
            
        # RSI 계산
        if 'close' in data.columns:
            data['rsi'] = self._calculate_rsi(data['close'])
            
        # SMA 계산
        if 'close' in data.columns:
            data['sma_20'] = data['close'].rolling(window=20).mean()
            data['sma_60'] = data['close'].rolling(window=60).mean()
            
        # MACD 계산
        if 'close' in data.columns:
            data['macd'] = self._calculate_macd(data['close'])
            
        return data
        
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI 계산 - TriggerCalculator로 위임"""
        if self.trigger_calculator and len(prices) > 0:
            try:
                # pandas Series를 리스트로 변환
                price_list = prices.dropna().tolist()
                if len(price_list) < period:
                    return pd.Series([50] * len(prices), index=prices.index)
                
                # TriggerCalculator로 계산
                rsi_values = self.trigger_calculator.calculate_rsi(price_list, period)
                
                # 결과를 pandas Series로 변환
                return pd.Series(rsi_values, index=prices.index[:len(rsi_values)])
            except Exception as e:
                print(f"⚠️ TriggerCalculator RSI 계산 실패, 폴백 사용: {e}")
        
        # 폴백: 기존 pandas 구현
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)  # NaN 값을 50으로 채움
        
    def _calculate_macd(self, prices: pd.Series) -> pd.Series:
        """MACD 계산 - TriggerCalculator로 위임"""
        if self.trigger_calculator and len(prices) > 0:
            try:
                # pandas Series를 리스트로 변환
                price_list = prices.dropna().tolist()
                if len(price_list) < 26:  # MACD는 최소 26개 데이터 필요
                    return pd.Series([0] * len(prices), index=prices.index)
                
                # TriggerCalculator로 계산
                macd_values = self.trigger_calculator.calculate_macd(price_list)
                
                # 결과를 pandas Series로 변환
                return pd.Series(macd_values, index=prices.index[:len(macd_values)])
            except Exception as e:
                print(f"⚠️ TriggerCalculator MACD 계산 실패, 폴백 사용: {e}")
        
        # 폴백: 기존 pandas 구현
        ema12 = prices.ewm(span=12).mean()
        ema26 = prices.ewm(span=26).mean()
        macd = ema12 - ema26
        return macd.fillna(0)  # NaN 값을 0으로 채움


class RealDataSimulationEngine(BaseSimulationEngine):
    """실제 데이터 기반 시뮬레이션 엔진 - 검증된 버전"""
    
    def __init__(self, data_db_path: str = None):
        super().__init__()
        self.name = "RealData"
        
        # 새로운 통합 DB 경로 시스템 사용 (하위 호환성 유지)
        if data_db_path is None:
            if USE_NEW_DB_PATHS:
                self.data_db_path = MARKET_DATA_DB_PATH  # market_data.sqlite3로 매핑됨
                print(f"🔗 RealDataSimulationEngine: 새로운 통합 DB 사용 - {self.data_db_path}")
            else:
                self.data_db_path = "data/market_data.sqlite3"  # 레거시 경로
                print(f"⚠️ RealDataSimulationEngine: 레거시 DB 경로 사용 - {self.data_db_path}")
        else:
            self.data_db_path = data_db_path
            print(f"📂 RealDataSimulationEngine: 사용자 지정 DB 경로 - {self.data_db_path}")
        
        self.cache_data = None
        self.cache_indicators = None
        
    def load_market_data(self, limit: int = 500) -> Optional[pd.DataFrame]:
        """실제 KRW-BTC 시장 데이터 로드"""
        try:
            if not os.path.exists(self.data_db_path):
                logging.warning(f"Market data DB not found: {self.data_db_path}")
                return self._generate_fallback_data(limit)
                
            conn = sqlite3.connect(self.data_db_path)
            
            # 일봉 데이터 로드
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
            
            df = pd.read_sql_query(query, conn, params=[limit])
            conn.close()
            
            if df.empty:
                logging.warning("No data found in database")
                return self._generate_fallback_data(limit)
            
            # 데이터 전처리
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            df = df.set_index('timestamp')
            
            # 기술적 지표 계산
            df = self.calculate_technical_indicators(df)
            
            self.cache_data = df
            logging.info(f"실제 DB에서 {len(df)}개 데이터 로드")
            return df
            
        except Exception as e:
            logging.error(f"실제 데이터 로드 실패: {e}")
            return self._generate_fallback_data(limit)
    
    def _generate_fallback_data(self, limit: int) -> pd.DataFrame:
        """DB가 없을 때 사용할 폴백 데이터"""
        dates = pd.date_range(end=datetime.now(), periods=limit, freq='D')
        
        # 현실적인 BTC 가격 패턴 생성
        base_price = 50000000  # 5천만원
        prices = [base_price]
        
        for i in range(1, limit):
            # 일일 변동률: -8% ~ +8% (BTC 특성)
            daily_change = np.random.normal(0, 0.04)  # 평균 0%, 표준편차 4%
            # 극단적 변동 제한
            daily_change = max(min(daily_change, 0.08), -0.08)
            
            new_price = prices[-1] * (1 + daily_change)
            new_price = max(new_price, base_price * 0.2)  # 최대 80% 하락 제한
            prices.append(new_price)
        
        # OHLCV 데이터 생성
        data = []
        for i, close_price in enumerate(prices):
            if i == 0:
                open_price = close_price
            else:
                open_price = prices[i-1] * np.random.uniform(0.995, 1.005)
            
            # High/Low 생성 (close 기준 ±3%)
            high = max(open_price, close_price) * np.random.uniform(1.0, 1.03)
            low = min(open_price, close_price) * np.random.uniform(0.97, 1.0)
            
            # 거래량 생성
            volume = np.random.randint(100000000, 2000000000)  # 1억~20억
            
            data.append({
                'timestamp': dates[i],
                'open': open_price,
                'high': high,
                'low': low,
                'close': close_price,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        df = df.set_index('timestamp')
        df = self.calculate_technical_indicators(df)
        
        logging.info(f"폴백 데이터 {len(df)}개 생성")
        return df


class RobustSimulationEngine(BaseSimulationEngine):
    """견고한 합성 데이터 시뮬레이션 엔진 - 검증된 버전"""
    
    def __init__(self, data_db_path: str = None):
        super().__init__()
        self.name = "Robust"
        
        # 새로운 통합 DB 경로 시스템 사용 (하위 호환성 유지)
        if data_db_path is None:
            if USE_NEW_DB_PATHS:
                self.data_db_path = MARKET_DATA_DB_PATH  # market_data.sqlite3로 매핑됨
                print(f"🔗 RobustSimulationEngine: 새로운 통합 DB 사용 - {self.data_db_path}")
            else:
                self.data_db_path = "data/market_data.sqlite3"  # 레거시 경로
                print(f"⚠️ RobustSimulationEngine: 레거시 DB 경로 사용 - {self.data_db_path}")
        else:
            self.data_db_path = data_db_path
            print(f"📂 RobustSimulationEngine: 사용자 지정 DB 경로 - {self.data_db_path}")
        
        self.cache_data = None
        self.cache_indicators = None
        
        # 내장 시드 데이터
        self.seed_patterns = self._generate_seed_patterns()
        
    def _generate_seed_patterns(self) -> Dict[str, np.ndarray]:
        """시나리오별 시드 패턴 생성"""
        np.random.seed(42)  # 일관된 결과
        
        patterns = {}
        base_length = 365
        btc_base_price = 45000000
        
        # 1. 상승 추세 패턴
        uptrend = []
        for i in range(base_length):
            trend_factor = 1 + (i / base_length) * 2.5  # 250% 상승
            daily_volatility = np.random.normal(1, 0.05)
            price = btc_base_price * trend_factor * daily_volatility
            uptrend.append(max(price, btc_base_price * 0.5))
        patterns['uptrend'] = np.array(uptrend)
        
        # 2. 하락 추세 패턴
        downtrend = []
        for i in range(base_length):
            trend_factor = 1 - (i / base_length) * 0.6  # 60% 하락
            daily_volatility = np.random.normal(1, 0.06)
            price = btc_base_price * trend_factor * daily_volatility
            downtrend.append(max(price, btc_base_price * 0.2))
        patterns['downtrend'] = np.array(downtrend)
        
        # 3. 횡보 패턴
        sideways = []
        for i in range(base_length):
            cycle = np.sin(i * 2 * np.pi / 30) * 0.1  # 월간 사이클
            noise = np.random.normal(0, 0.03)
            price = btc_base_price * (1 + cycle + noise)
            sideways.append(max(price, btc_base_price * 0.7))
        patterns['sideways'] = np.array(sideways)
        
        # 4. 급등 패턴
        surge = []
        surge_point = base_length // 2
        for i in range(base_length):
            if i < surge_point:
                trend_factor = 1 + (i / surge_point) * 0.2
            else:
                surge_intensity = min((i - surge_point) / 30, 1) * 3
                trend_factor = 1.2 * (1 + surge_intensity)
            
            daily_volatility = np.random.normal(1, 0.08)
            price = btc_base_price * trend_factor * daily_volatility
            surge.append(max(price, btc_base_price * 0.3))
        patterns['surge'] = np.array(surge)
        
        return patterns
        
    def load_market_data(self, limit: int = 100) -> pd.DataFrame:
        """견고한 합성 시장 데이터 생성"""
        # 시나리오 선택
        scenarios = ['uptrend', 'downtrend', 'sideways', 'surge']
        weights = [0.3, 0.2, 0.3, 0.2]  # 상승 편향
        scenario = np.random.choice(scenarios, p=weights)
        
        if scenario in self.seed_patterns:
            pattern = self.seed_patterns[scenario]
            # 랜덤 구간 선택
            if len(pattern) >= limit:
                start_idx = np.random.randint(0, len(pattern) - limit + 1)
                selected_prices = pattern[start_idx:start_idx + limit]
            else:
                selected_prices = pattern[:limit]
        else:
            # 기본 패턴
            base_price = 45000000
            selected_prices = [base_price * (1 + np.random.normal(0, 0.03)) for _ in range(limit)]
        
        # DataFrame 생성
        dates = pd.date_range(end=datetime.now(), periods=len(selected_prices), freq='D')
        data = []
        
        for i, close_price in enumerate(selected_prices):
            if i == 0:
                open_price = close_price
            else:
                open_price = selected_prices[i-1] * np.random.uniform(0.998, 1.002)
            
            high = max(open_price, close_price) * np.random.uniform(1.0, 1.02)
            low = min(open_price, close_price) * np.random.uniform(0.98, 1.0)
            volume = np.random.randint(200000000, 1500000000)
            
            data.append({
                'timestamp': dates[i],
                'open': open_price,
                'high': high,
                'low': low,
                'close': close_price,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        df = df.set_index('timestamp')
        df = self.calculate_technical_indicators(df)
        
        logging.info(f"견고한 합성 데이터 {len(df)}개 생성 (시나리오: {scenario})")
        return df


class EmbeddedSimulationEngine(BaseSimulationEngine):
    """내장 최적화 시뮬레이션 엔진 - 검증된 버전"""
    
    def __init__(self, data_db_path: str = None):
        super().__init__()
        self.name = "Embedded"
        
        # 새로운 통합 DB 경로 시스템 사용 (하위 호환성 유지)
        if data_db_path is None:
            if USE_NEW_DB_PATHS:
                self.data_db_path = MARKET_DATA_DB_PATH  # market_data.sqlite3로 매핑됨
                print(f"🔗 EmbeddedSimulationEngine: 새로운 통합 DB 사용 - {self.data_db_path}")
            else:
                self.data_db_path = "data/market_data.sqlite3"  # 레거시 경로
                print(f"⚠️ EmbeddedSimulationEngine: 레거시 DB 경로 사용 - {self.data_db_path}")
        else:
            self.data_db_path = data_db_path
            print(f"📂 EmbeddedSimulationEngine: 사용자 지정 DB 경로 - {self.data_db_path}")
        self.data_db_path = data_db_path
        self.cache_data = None
        self.cache_indicators = None
        
        # 시나리오별 최적화된 내장 데이터셋
        self.embedded_datasets = self._create_embedded_datasets()
        
        logging.info(f"내장 시뮬레이션 데이터셋 로드 완료: {len(self.embedded_datasets)}개 시나리오")
        
    def _create_embedded_datasets(self) -> Dict[str, Dict[str, Any]]:
        """시나리오별 최적화된 내장 데이터셋 생성"""
        np.random.seed(42)  # 일관된 결과
        
        datasets = {}
        base_price = 50000000  # 5천만원 기준
        data_length = 180  # 6개월 데이터
        
        # 1. 상승 추세 데이터셋
        datasets['bull_market'] = self._create_uptrend_dataset(base_price, data_length)
        
        # 2. 하락 추세 데이터셋  
        datasets['bear_market'] = self._create_downtrend_dataset(base_price, data_length)
        
        # 3. 급등 데이터셋
        datasets['surge'] = self._create_surge_dataset(base_price, data_length)
        
        # 4. 급락 데이터셋
        datasets['crash'] = self._create_crash_dataset(base_price, data_length)
        
        # 5. 횡보 데이터셋
        datasets['sideways'] = self._create_sideways_dataset(base_price, data_length)
        
        return datasets
    
    def _create_uptrend_dataset(self, base_price: float, length: int) -> Dict[str, Any]:
        """상승 추세 최적화 데이터셋"""
        monthly_return = 0.15
        daily_return = (1 + monthly_return) ** (1/30) - 1
        
        prices = [base_price]
        for i in range(1, length):
            trend = daily_return
            volatility = np.random.normal(0, 0.04)
            correction = -0.02 if np.random.random() < 0.1 else 0
            
            daily_change = trend + volatility + correction
            new_price = prices[-1] * (1 + daily_change)
            prices.append(max(new_price, base_price * 0.8))
        
        return self._create_full_dataset(prices, 'bull_market', length)
    
    def _create_downtrend_dataset(self, base_price: float, length: int) -> Dict[str, Any]:
        """하락 추세 최적화 데이터셋"""
        monthly_return = -0.08
        daily_return = (1 + monthly_return) ** (1/30) - 1
        
        prices = [base_price]
        for i in range(1, length):
            trend = daily_return
            volatility = np.random.normal(0, 0.05)
            bounce = 0.03 if np.random.random() < 0.08 else 0
            
            daily_change = trend + volatility + bounce
            new_price = prices[-1] * (1 + daily_change)
            prices.append(max(new_price, base_price * 0.3))
        
        return self._create_full_dataset(prices, 'bear_market', length)
    
    def _create_surge_dataset(self, base_price: float, length: int) -> Dict[str, Any]:
        """급등 최적화 데이터셋"""
        surge_start = length // 3
        surge_duration = 14
        
        prices = [base_price]
        for i in range(1, length):
            if surge_start <= i < surge_start + surge_duration:
                surge_progress = (i - surge_start) / surge_duration
                base_surge = 0.08 * (1 - surge_progress * 0.3)
                volatility = np.random.normal(0, 0.03)
                daily_change = base_surge + volatility
            else:
                daily_change = np.random.normal(0.005, 0.025)
            
            new_price = prices[-1] * (1 + daily_change)
            prices.append(max(new_price, base_price * 0.5))
        
        return self._create_full_dataset(prices, 'surge', length)
    
    def _create_crash_dataset(self, base_price: float, length: int) -> Dict[str, Any]:
        """급락 최적화 데이터셋"""
        crash_start = length // 2
        crash_duration = 10
        
        prices = [base_price]
        for i in range(1, length):
            if crash_start <= i < crash_start + crash_duration:
                crash_progress = (i - crash_start) / crash_duration
                base_crash = -0.06 * (1 - crash_progress * 0.4)
                volatility = np.random.normal(0, 0.04)
                daily_change = base_crash + volatility
            else:
                daily_change = np.random.normal(-0.002, 0.02)
            
            new_price = prices[-1] * (1 + daily_change)
            prices.append(max(new_price, base_price * 0.2))
        
        return self._create_full_dataset(prices, 'crash', length)
    
    def _create_sideways_dataset(self, base_price: float, length: int) -> Dict[str, Any]:
        """횡보 최적화 데이터셋"""
        prices = [base_price]
        center_price = base_price
        
        for i in range(1, length):
            distance_from_center = (prices[-1] - center_price) / center_price
            mean_reversion = -distance_from_center * 0.1
            
            cycle = np.sin(i * 2 * np.pi / 7) * 0.005
            noise = np.random.normal(0, 0.015)
            
            daily_change = mean_reversion + cycle + noise
            new_price = prices[-1] * (1 + daily_change)
            
            new_price = min(max(new_price, base_price * 0.92), base_price * 1.08)
            prices.append(new_price)
        
        return self._create_full_dataset(prices, 'sideways', length)
    
    def _create_full_dataset(self, prices: List[float], scenario: str, length: int) -> Dict[str, Any]:
        """완전한 OHLCV 데이터셋 생성"""
        ohlcv_data = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=length-1)
        
        for i, close_price in enumerate(prices):
            date = start_date + timedelta(days=i)
            
            if i == 0:
                open_price = close_price
            else:
                open_price = prices[i-1] * np.random.uniform(0.998, 1.002)
            
            daily_range = abs(close_price - open_price) * np.random.uniform(1.2, 2.0)
            base_price_for_hl = (open_price + close_price) / 2
            
            high = base_price_for_hl + daily_range * np.random.uniform(0.3, 0.7)
            low = base_price_for_hl - daily_range * np.random.uniform(0.3, 0.7)
            
            high = max(high, max(open_price, close_price))
            low = min(low, min(open_price, close_price))
            
            base_volume = 800000000
            volatility_factor = abs(close_price - open_price) / open_price * 10
            volume = base_volume * (1 + volatility_factor) * np.random.uniform(0.7, 1.5)
            
            ohlcv_data.append({
                'timestamp': date,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close_price,
                'volume': volume
            })
        
        df = pd.DataFrame(ohlcv_data)
        df = df.set_index('timestamp')
        df = self.calculate_technical_indicators(df)
        
        return {
            'dataframe': df,
            'scenario': scenario,
            'data_source': 'embedded_optimized_dataset',
            'description': f'{scenario} 시나리오에 최적화된 내장 데이터셋',
            'total_change': (prices[-1] / prices[0] - 1) * 100,
            'avg_daily_volatility': np.std([prices[i]/prices[i-1]-1 for i in range(1, len(prices))]) * 100,
            'data_points': len(prices)
        }
        
    def load_market_data(self, limit: int = 100) -> pd.DataFrame:
        """시나리오별 최적화된 내장 데이터"""
        # 랜덤 시나리오 선택
        scenarios = list(self.embedded_datasets.keys())
        scenario = np.random.choice(scenarios)
        
        dataset = self.embedded_datasets[scenario]
        df = dataset['dataframe']
        
        if len(df) >= limit:
            max_start = len(df) - limit
            start_idx = np.random.randint(0, max_start + 1) if max_start > 0 else 0
            return df.iloc[start_idx:start_idx + limit].copy()
        else:
            return df.copy()
    
    def get_scenario_data(self, scenario: str, length: int = 50) -> Dict[str, Any]:
        """시나리오별 최적화된 데이터 반환"""
        scenario_mapping = {
            'bull_market': 'bull_market',
            'bear_market': 'bear_market', 
            'sideways': 'sideways',
            'surge': 'surge',
            'crash': 'crash'
        }
        
        mapped_scenario = scenario_mapping.get(scenario, 'bull_market')
        
        if mapped_scenario in self.embedded_datasets:
            dataset = self.embedded_datasets[mapped_scenario]
            df = dataset['dataframe']
            
            if len(df) >= length:
                max_start = len(df) - length
                start_idx = np.random.randint(0, max_start + 1) if max_start > 0 else 0
                segment = df.iloc[start_idx:start_idx + length]
            else:
                segment = df
            
            if not segment.empty:
                last_row = segment.iloc[-1]
                current_value = last_row['close']
                
                return {
                    'current_value': float(current_value),
                    'price_data': segment['close'].tolist(),
                    'scenario': scenario,
                    'data_source': 'embedded_optimized_dataset',
                    'period': f"{segment.index[0].strftime('%Y-%m-%d')} ~ {segment.index[-1].strftime('%Y-%m-%d')}",
                    'base_value': float(segment['close'].iloc[0]),
                    'change_percent': float((segment['close'].iloc[-1] / segment['close'].iloc[0] - 1) * 100),
                    'description': dataset['description']
                }
        
        # 폴백
        return self._generate_simple_fallback(scenario, length)
    
    def _generate_simple_fallback(self, scenario: str, length: int) -> Dict[str, Any]:
        """단순 폴백 데이터"""
        base_value = 50000000
        
        if scenario in ["bull_market", "surge"]:
            trend = np.linspace(0, base_value * 0.1, length)
        elif scenario in ["bear_market", "crash"]:
            trend = np.linspace(0, -base_value * 0.1, length)
        else:
            trend = np.zeros(length)
        
        noise = np.random.randn(length) * base_value * 0.02
        price_data = base_value + trend + noise
        price_data = np.maximum(price_data, base_value * 0.1)
        
        return {
            'current_value': float(price_data[-1]),
            'price_data': price_data.tolist(),
            'scenario': scenario,
            'data_source': 'simple_fallback',
            'period': 'generated_data',
            'base_value': base_value,
            'change_percent': (price_data[-1] / price_data[0] - 1) * 100
        }


# 전역 엔진 인스턴스들
_embedded_engine = None
_real_engine = None  
_robust_engine = None

def get_embedded_simulation_engine():
    """내장 시뮬레이션 엔진 반환"""
    global _embedded_engine
    if _embedded_engine is None:
        _embedded_engine = EmbeddedSimulationEngine()
    return _embedded_engine

def get_real_data_simulation_engine():
    """실제 데이터 시뮬레이션 엔진 반환"""
    global _real_engine
    if _real_engine is None:
        _real_engine = RealDataSimulationEngine()
    return _real_engine

def get_robust_simulation_engine():
    """견고한 시뮬레이션 엔진 반환"""
    global _robust_engine
    if _robust_engine is None:
        _robust_engine = RobustSimulationEngine()
    return _robust_engine


# 호환성을 위한 별칭 (함수 형태로)
def create_real_data_simulation_engine():
    """호환성을 위한 별칭"""
    return get_real_data_simulation_engine()


def create_robust_simulation_engine():
    """호환성을 위한 별칭"""  
    return get_robust_simulation_engine()


def create_embedded_simulation_engine():
    """호환성을 위한 별칭"""
    return get_embedded_simulation_engine()
