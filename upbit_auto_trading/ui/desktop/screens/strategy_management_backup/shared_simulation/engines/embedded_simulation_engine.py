"""
내장 시뮬레이션 데이터셋 엔진
각 시나리오에 최적화된 고품질 시뮬레이션 데이터를 내장하여 제공
폴백이 아닌 주요 시뮬레이션 데이터 소스로 활용
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import os
import sqlite3

class EmbeddedSimulationDataEngine:
    """내장 시뮬레이션 데이터셋 엔진"""
    
    def __init__(self, data_db_path: str = "data/market_data.sqlite3"):
        """
        내장 시뮬레이션 데이터 엔진 초기화
        
        Args:
            data_db_path: 실제 DB 경로 (보조 데이터 소스)
        """
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
        datasets['상승 추세'] = self._create_uptrend_dataset(base_price, data_length)
        
        # 2. 하락 추세 데이터셋  
        datasets['하락 추세'] = self._create_downtrend_dataset(base_price, data_length)
        
        # 3. 급등 데이터셋
        datasets['급등'] = self._create_surge_dataset(base_price, data_length)
        
        # 4. 급락 데이터셋
        datasets['급락'] = self._create_crash_dataset(base_price, data_length)
        
        # 5. 횡보 데이터셋
        datasets['횡보'] = self._create_sideways_dataset(base_price, data_length)
        
        # 6. 이동평균 교차 데이터셋
        datasets['이동평균 교차'] = self._create_ma_cross_dataset(base_price, data_length)
        
        return datasets
    
    def _create_uptrend_dataset(self, base_price: float, length: int) -> Dict[str, Any]:
        """상승 추세 최적화 데이터셋 생성"""
        # 꾸준한 상승 트렌드 (월 15% 상승)
        monthly_return = 0.15
        daily_return = (1 + monthly_return) ** (1/30) - 1
        
        prices = [base_price]
        for i in range(1, length):
            # 기본 상승 트렌드
            trend = daily_return
            # 일일 변동성 (4%)
            volatility = np.random.normal(0, 0.04)
            # 가끔 조정 구간 (10% 확률로 -2% 하락)
            correction = -0.02 if np.random.random() < 0.1 else 0
            
            daily_change = trend + volatility + correction
            new_price = prices[-1] * (1 + daily_change)
            prices.append(max(new_price, base_price * 0.8))  # 최대 20% 하락 제한
        
        return self._create_full_dataset(prices, '상승 추세', length)
    
    def _create_downtrend_dataset(self, base_price: float, length: int) -> Dict[str, Any]:
        """하락 추세 최적화 데이터셋 생성"""
        # 점진적 하락 트렌드 (월 -8% 하락)
        monthly_return = -0.08
        daily_return = (1 + monthly_return) ** (1/30) - 1
        
        prices = [base_price]
        for i in range(1, length):
            # 기본 하락 트렌드
            trend = daily_return
            # 일일 변동성 (5% - 하락장에서 더 높음)
            volatility = np.random.normal(0, 0.05)
            # 가끔 반등 구간 (8% 확률로 +3% 상승)
            bounce = 0.03 if np.random.random() < 0.08 else 0
            
            daily_change = trend + volatility + bounce
            new_price = prices[-1] * (1 + daily_change)
            prices.append(max(new_price, base_price * 0.3))  # 최대 70% 하락 제한
        
        return self._create_full_dataset(prices, '하락 추세', length)
    
    def _create_surge_dataset(self, base_price: float, length: int) -> Dict[str, Any]:
        """급등 최적화 데이터셋 생성"""
        surge_start = length // 3  # 1/3 지점에서 급등 시작
        surge_duration = 14  # 2주간 급등
        
        prices = [base_price]
        for i in range(1, length):
            if surge_start <= i < surge_start + surge_duration:
                # 급등 구간: 일 평균 8% 상승
                surge_progress = (i - surge_start) / surge_duration
                base_surge = 0.08 * (1 - surge_progress * 0.3)  # 점진적 둔화
                volatility = np.random.normal(0, 0.03)
                daily_change = base_surge + volatility
            else:
                # 평상시: 약간의 상승 편향
                daily_change = np.random.normal(0.005, 0.025)  # 평균 0.5% 상승
            
            new_price = prices[-1] * (1 + daily_change)
            prices.append(max(new_price, base_price * 0.5))
        
        return self._create_full_dataset(prices, '급등', length)
    
    def _create_crash_dataset(self, base_price: float, length: int) -> Dict[str, Any]:
        """급락 최적화 데이터셋 생성"""
        crash_start = length // 2  # 중간 지점에서 급락 시작
        crash_duration = 10  # 10일간 급락
        
        prices = [base_price]
        for i in range(1, length):
            if crash_start <= i < crash_start + crash_duration:
                # 급락 구간: 일 평균 -6% 하락
                crash_progress = (i - crash_start) / crash_duration
                base_crash = -0.06 * (1 - crash_progress * 0.4)  # 점진적 완화
                volatility = np.random.normal(0, 0.04)
                daily_change = base_crash + volatility
            else:
                # 평상시: 약간 하락 편향
                daily_change = np.random.normal(-0.002, 0.02)  # 평균 -0.2% 하락
            
            new_price = prices[-1] * (1 + daily_change)
            prices.append(max(new_price, base_price * 0.2))
        
        return self._create_full_dataset(prices, '급락', length)
    
    def _create_sideways_dataset(self, base_price: float, length: int) -> Dict[str, Any]:
        """횡보 최적화 데이터셋 생성"""
        prices = [base_price]
        center_price = base_price
        
        for i in range(1, length):
            # 중심가격으로의 회귀 경향
            distance_from_center = (prices[-1] - center_price) / center_price
            mean_reversion = -distance_from_center * 0.1  # 10% 회귀력
            
            # 작은 사이클 (주간 패턴)
            cycle = np.sin(i * 2 * np.pi / 7) * 0.005  # 0.5% 진폭
            
            # 일일 노이즈
            noise = np.random.normal(0, 0.015)  # 1.5% 변동성
            
            daily_change = mean_reversion + cycle + noise
            new_price = prices[-1] * (1 + daily_change)
            
            # 횡보 범위 제한 (±8%)
            new_price = min(max(new_price, base_price * 0.92), base_price * 1.08)
            prices.append(new_price)
        
        return self._create_full_dataset(prices, '횡보', length)
    
    def _create_ma_cross_dataset(self, base_price: float, length: int) -> Dict[str, Any]:
        """이동평균 교차 최적화 데이터셋 생성"""
        cross_point = length // 2  # 중간에서 교차
        
        prices = [base_price]
        for i in range(1, length):
            # 교차 시점 전후로 트렌드 변화
            if i < cross_point - 10:
                # 하락 후 횡보
                daily_change = np.random.normal(-0.001, 0.02)
            elif i < cross_point + 10:
                # 교차 구간: 상승 전환
                progress = (i - (cross_point - 10)) / 20
                base_trend = progress * 0.02  # 점진적 상승
                daily_change = base_trend + np.random.normal(0, 0.025)
            else:
                # 교차 후 상승 추세
                daily_change = np.random.normal(0.008, 0.03)
            
            new_price = prices[-1] * (1 + daily_change)
            prices.append(max(new_price, base_price * 0.6))
        
        return self._create_full_dataset(prices, '이동평균 교차', length)
    
    def _create_full_dataset(self, prices: List[float], scenario: str, length: int) -> Dict[str, Any]:
        """완전한 OHLCV 데이터셋 생성"""
        ohlcv_data = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=length-1)
        
        for i, close_price in enumerate(prices):
            date = start_date + timedelta(days=i)
            
            # 일일 변동성을 고려한 OHLV 생성
            if i == 0:
                open_price = close_price
            else:
                open_price = prices[i-1] * np.random.uniform(0.998, 1.002)
            
            # High/Low 계산
            daily_range = abs(close_price - open_price) * np.random.uniform(1.2, 2.0)
            base_price_for_hl = (open_price + close_price) / 2
            
            high = base_price_for_hl + daily_range * np.random.uniform(0.3, 0.7)
            low = base_price_for_hl - daily_range * np.random.uniform(0.3, 0.7)
            
            # 논리적 제약 적용
            high = max(high, max(open_price, close_price))
            low = min(low, min(open_price, close_price))
            
            # Volume (현실적인 거래량)
            base_volume = 800000000  # 8억원 기준
            volatility_factor = abs(close_price - open_price) / open_price * 10  # 변동성에 비례
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
        
        # 기술적 지표 계산
        df = self._calculate_technical_indicators(df)
        
        # 데이터셋 메타정보
        return {
            'dataframe': df,
            'scenario': scenario,
            'data_source': 'embedded_optimized_dataset',
            'description': f'{scenario} 시나리오에 최적화된 내장 데이터셋',
            'total_change': (prices[-1] / prices[0] - 1) * 100,
            'avg_daily_volatility': np.std([prices[i]/prices[i-1]-1 for i in range(1, len(prices))]) * 100,
            'data_points': len(prices)
        }
    
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 계산"""
        try:
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
            
            # 변동성 계산
            df['volatility_30d'] = df['close'].pct_change().rolling(window=30).std() * 100
            
            # 수익률 계산
            df['return_7d'] = df['close'].pct_change(7) * 100
            df['return_30d'] = df['close'].pct_change(30) * 100
            
            return df
            
        except Exception as e:
            logging.error(f"기술적 지표 계산 실패: {e}")
            return df
    
    def get_scenario_data(self, scenario: str, length: int = 50) -> Dict[str, Any]:
        """시나리오별 최적화된 데이터 반환"""
        try:
            # 1차: 내장 데이터셋 사용 (우선순위)
            if scenario in self.embedded_datasets:
                dataset = self.embedded_datasets[scenario]
                df = dataset['dataframe']
                
                # 요청한 길이만큼 데이터 추출
                if len(df) >= length:
                    # 랜덤한 시작점에서 연속된 데이터 추출
                    max_start = len(df) - length
                    start_idx = np.random.randint(0, max_start + 1) if max_start > 0 else 0
                    segment = df.iloc[start_idx:start_idx + length]
                else:
                    segment = df  # 전체 데이터 사용
                
                if not segment.empty:
                    last_row = segment.iloc[-1]
                    
                    # 시나리오별 현재값 계산
                    if '교차' in scenario:
                        current_value = last_row['sma_20'] - last_row['sma_60']
                    elif 'rsi' in scenario.lower():
                        current_value = last_row['rsi']
                    else:
                        current_value = last_row['close']
                    
                    logging.info(f"내장 데이터셋 사용: {scenario}")
                    return {
                        'current_value': float(current_value) if not pd.isna(current_value) else 50.0,
                        'price_data': segment['close'].tolist(),
                        'scenario': scenario,
                        'data_source': 'embedded_optimized_dataset',
                        'period': f"{segment.index[0].strftime('%Y-%m-%d')} ~ {segment.index[-1].strftime('%Y-%m-%d')}",
                        'base_value': float(segment['close'].iloc[0]),
                        'change_percent': float((segment['close'].iloc[-1] / segment['close'].iloc[0] - 1) * 100),
                        'description': dataset['description']
                    }
            
            # 2차: 실제 DB 사용 (보조)
            if os.path.exists(self.data_db_path):
                logging.info(f"실제 DB 사용: {scenario}")
                return self._load_from_real_db(scenario, length)
            
            # 3차: 간단한 폴백
            logging.warning(f"폴백 데이터 사용: {scenario}")
            return self._generate_simple_fallback(scenario, length)
            
        except Exception as e:
            logging.error(f"시나리오 데이터 로딩 실패: {e}")
            return self._generate_simple_fallback(scenario, length)
    
    def _load_from_real_db(self, scenario: str, length: int) -> Dict[str, Any]:
        """실제 DB에서 데이터 로드 (보조 기능)"""
        # 실제 DB 로딩 로직 (기존 코드 활용)
        # 여기서는 간단한 구현만
        return self._generate_simple_fallback(scenario, length)
    
    def _generate_simple_fallback(self, scenario: str, length: int) -> Dict[str, Any]:
        """단순 폴백 데이터"""
        base_value = 50000000
        
        if scenario in ["상승 추세", "급등"]:
            trend = np.linspace(0, base_value * 0.1, length)
        elif scenario in ["하락 추세", "급락"]:
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
    
    def get_available_scenarios(self) -> List[str]:
        """사용 가능한 시나리오 목록 반환"""
        return list(self.embedded_datasets.keys())
    
    def get_dataset_info(self, scenario: str) -> Dict[str, Any]:
        """특정 시나리오의 데이터셋 정보 반환"""
        if scenario in self.embedded_datasets:
            dataset = self.embedded_datasets[scenario]
            return {
                'scenario': scenario,
                'data_source': dataset['data_source'],
                'description': dataset['description'],
                'total_change': dataset['total_change'],
                'avg_daily_volatility': dataset['avg_daily_volatility'],
                'data_points': dataset['data_points']
            }
        return None

# 전역 인스턴스
_embedded_engine = None

def get_embedded_simulation_engine():
    """내장 시뮬레이션 데이터 엔진 싱글톤 반환"""
    global _embedded_engine
    if _embedded_engine is None:
        _embedded_engine = EmbeddedSimulationDataEngine()
    return _embedded_engine
