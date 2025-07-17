#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
데이터 처리기

시장 데이터를 처리하고 기술적 지표를 계산하는 기능을 제공합니다.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler, StandardScaler

logger = logging.getLogger(__name__)

class DataProcessor:
    """시장 데이터 처리 및 기술적 지표 계산을 담당하는 클래스"""
    
    def __init__(self):
        """DataProcessor 초기화"""
        self.scalers = {}
    
    def calculate_sma(self, df: pd.DataFrame, column: str = 'close', periods: List[int] = [5, 10, 20, 50, 200]) -> pd.DataFrame:
        """단순 이동 평균(Simple Moving Average)을 계산합니다.
        
        Args:
            df: OHLCV 데이터가 포함된 DataFrame
            column: 계산에 사용할 컬럼 이름
            periods: 이동 평균 기간 목록
            
        Returns:
            pd.DataFrame: 이동 평균이 추가된 DataFrame
        """
        if df.empty:
            return df
        
        result_df = df.copy()
        
        for period in periods:
            result_df[f'sma_{period}'] = result_df[column].rolling(window=period).mean()
        
        return result_df
    
    def calculate_ema(self, df: pd.DataFrame, column: str = 'close', periods: List[int] = [5, 10, 20, 50, 200]) -> pd.DataFrame:
        """지수 이동 평균(Exponential Moving Average)을 계산합니다.
        
        Args:
            df: OHLCV 데이터가 포함된 DataFrame
            column: 계산에 사용할 컬럼 이름
            periods: 이동 평균 기간 목록
            
        Returns:
            pd.DataFrame: 지수 이동 평균이 추가된 DataFrame
        """
        if df.empty:
            return df
        
        result_df = df.copy()
        
        for period in periods:
            result_df[f'ema_{period}'] = result_df[column].ewm(span=period, adjust=False).mean()
        
        return result_df
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, column: str = 'close', period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        """볼린저 밴드(Bollinger Bands)를 계산합니다.
        
        Args:
            df: OHLCV 데이터가 포함된 DataFrame
            column: 계산에 사용할 컬럼 이름
            period: 이동 평균 기간
            std_dev: 표준 편차 배수
            
        Returns:
            pd.DataFrame: 볼린저 밴드가 추가된 DataFrame
        """
        if df.empty:
            return df
        
        result_df = df.copy()
        
        # 중간 밴드 (SMA)
        result_df['bb_middle'] = result_df[column].rolling(window=period).mean()
        
        # 표준 편차
        result_df['bb_std'] = result_df[column].rolling(window=period).std()
        
        # 상단 밴드
        result_df['bb_upper'] = result_df['bb_middle'] + (result_df['bb_std'] * std_dev)
        
        # 하단 밴드
        result_df['bb_lower'] = result_df['bb_middle'] - (result_df['bb_std'] * std_dev)
        
        # 밴드 폭
        result_df['bb_width'] = (result_df['bb_upper'] - result_df['bb_lower']) / result_df['bb_middle']
        
        # %B 지표
        result_df['bb_pct_b'] = (result_df[column] - result_df['bb_lower']) / (result_df['bb_upper'] - result_df['bb_lower'])
        
        return result_df
    
    def calculate_rsi(self, df: pd.DataFrame, column: str = 'close', period: int = 14) -> pd.DataFrame:
        """상대 강도 지수(Relative Strength Index)를 계산합니다.
        
        Args:
            df: OHLCV 데이터가 포함된 DataFrame
            column: 계산에 사용할 컬럼 이름
            period: RSI 계산 기간
            
        Returns:
            pd.DataFrame: RSI가 추가된 DataFrame
        """
        if df.empty:
            return df
        
        result_df = df.copy()
        
        # 가격 변화 계산
        delta = result_df[column].diff()
        
        # 상승/하락 구분
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 평균 상승/하락 계산
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # 첫 번째 값 계산 (SMA 방식)
        first_avg_gain = gain.iloc[:period].mean()
        first_avg_loss = loss.iloc[:period].mean()
        
        # 나머지 값 계산 (지수 이동 평균 방식)
        for i in range(period, len(result_df)):
            avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period-1) + gain.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period-1) + loss.iloc[i]) / period
        
        # 상대 강도(RS) 계산
        rs = avg_gain / avg_loss
        
        # RSI 계산
        result_df['rsi'] = 100 - (100 / (1 + rs))
        
        return result_df
    
    def calculate_macd(self, df: pd.DataFrame, column: str = 'close', fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
        """MACD(Moving Average Convergence Divergence)를 계산합니다.
        
        Args:
            df: OHLCV 데이터가 포함된 DataFrame
            column: 계산에 사용할 컬럼 이름
            fast_period: 빠른 EMA 기간
            slow_period: 느린 EMA 기간
            signal_period: 시그널 EMA 기간
            
        Returns:
            pd.DataFrame: MACD가 추가된 DataFrame
        """
        if df.empty:
            return df
        
        result_df = df.copy()
        
        # 빠른 EMA
        result_df['ema_fast'] = result_df[column].ewm(span=fast_period, adjust=False).mean()
        
        # 느린 EMA
        result_df['ema_slow'] = result_df[column].ewm(span=slow_period, adjust=False).mean()
        
        # MACD 라인
        result_df['macd'] = result_df['ema_fast'] - result_df['ema_slow']
        
        # 시그널 라인
        result_df['macd_signal'] = result_df['macd'].ewm(span=signal_period, adjust=False).mean()
        
        # MACD 히스토그램
        result_df['macd_hist'] = result_df['macd'] - result_df['macd_signal']
        
        # 임시 컬럼 삭제
        result_df = result_df.drop(['ema_fast', 'ema_slow'], axis=1)
        
        return result_df
    
    def calculate_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3, slowing: int = 3) -> pd.DataFrame:
        """스토캐스틱 오실레이터(Stochastic Oscillator)를 계산합니다.
        
        Args:
            df: OHLCV 데이터가 포함된 DataFrame
            k_period: %K 기간
            d_period: %D 기간
            slowing: 슬로잉 기간
            
        Returns:
            pd.DataFrame: 스토캐스틱 오실레이터가 추가된 DataFrame
        """
        if df.empty:
            return df
        
        result_df = df.copy()
        
        # 최고가/최저가 계산
        result_df['lowest_low'] = result_df['low'].rolling(window=k_period).min()
        result_df['highest_high'] = result_df['high'].rolling(window=k_period).max()
        
        # %K 계산
        result_df['stoch_k_raw'] = 100 * ((result_df['close'] - result_df['lowest_low']) / 
                                      (result_df['highest_high'] - result_df['lowest_low']))
        
        # 슬로잉 적용
        result_df['stoch_k'] = result_df['stoch_k_raw'].rolling(window=slowing).mean()
        
        # %D 계산
        result_df['stoch_d'] = result_df['stoch_k'].rolling(window=d_period).mean()
        
        # 임시 컬럼 삭제
        result_df = result_df.drop(['lowest_low', 'highest_high', 'stoch_k_raw'], axis=1)
        
        return result_df
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """평균 실제 범위(Average True Range)를 계산합니다.
        
        Args:
            df: OHLCV 데이터가 포함된 DataFrame
            period: ATR 계산 기간
            
        Returns:
            pd.DataFrame: ATR이 추가된 DataFrame
        """
        if df.empty:
            return df
        
        result_df = df.copy()
        
        # 고가 - 저가
        high_low = result_df['high'] - result_df['low']
        
        # 고가 - 이전 종가
        high_close = (result_df['high'] - result_df['close'].shift(1)).abs()
        
        # 저가 - 이전 종가
        low_close = (result_df['low'] - result_df['close'].shift(1)).abs()
        
        # TR(True Range) 계산
        result_df['tr'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # ATR 계산
        result_df['atr'] = result_df['tr'].rolling(window=period).mean()
        
        # 임시 컬럼 삭제
        result_df = result_df.drop(['tr'], axis=1)
        
        return result_df
    
    def calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """평균 방향 지수(Average Directional Index)를 계산합니다.
        
        Args:
            df: OHLCV 데이터가 포함된 DataFrame
            period: ADX 계산 기간
            
        Returns:
            pd.DataFrame: ADX가 추가된 DataFrame
        """
        if df.empty:
            return df
        
        result_df = df.copy()
        
        # ATR 계산
        result_df = self.calculate_atr(result_df, period)
        
        # +DM, -DM 계산
        result_df['up_move'] = result_df['high'].diff()
        result_df['down_move'] = result_df['low'].shift(1) - result_df['low']
        
        result_df['plus_dm'] = np.where(
            (result_df['up_move'] > result_df['down_move']) & (result_df['up_move'] > 0),
            result_df['up_move'],
            0
        )
        
        result_df['minus_dm'] = np.where(
            (result_df['down_move'] > result_df['up_move']) & (result_df['down_move'] > 0),
            result_df['down_move'],
            0
        )
        
        # +DI, -DI 계산
        result_df['plus_di'] = 100 * (result_df['plus_dm'].rolling(window=period).mean() / result_df['atr'])
        result_df['minus_di'] = 100 * (result_df['minus_dm'].rolling(window=period).mean() / result_df['atr'])
        
        # DX 계산
        result_df['dx'] = 100 * (abs(result_df['plus_di'] - result_df['minus_di']) / 
                              (result_df['plus_di'] + result_df['minus_di']))
        
        # ADX 계산
        result_df['adx'] = result_df['dx'].rolling(window=period).mean()
        
        # 임시 컬럼 삭제
        result_df = result_df.drop(['up_move', 'down_move', 'plus_dm', 'minus_dm', 'dx'], axis=1)
        
        return result_df
    
    def calculate_ichimoku(self, df: pd.DataFrame, tenkan_period: int = 9, kijun_period: int = 26, senkou_b_period: int = 52, displacement: int = 26) -> pd.DataFrame:
        """일목균형표(Ichimoku Cloud)를 계산합니다.
        
        Args:
            df: OHLCV 데이터가 포함된 DataFrame
            tenkan_period: 전환선 기간
            kijun_period: 기준선 기간
            senkou_b_period: 선행스팬 B 기간
            displacement: 이격 기간
            
        Returns:
            pd.DataFrame: 일목균형표가 추가된 DataFrame
        """
        if df.empty:
            return df
        
        result_df = df.copy()
        
        # 전환선 (Tenkan-sen)
        result_df['ichimoku_tenkan'] = (result_df['high'].rolling(window=tenkan_period).max() + 
                                     result_df['low'].rolling(window=tenkan_period).min()) / 2
        
        # 기준선 (Kijun-sen)
        result_df['ichimoku_kijun'] = (result_df['high'].rolling(window=kijun_period).max() + 
                                    result_df['low'].rolling(window=kijun_period).min()) / 2
        
        # 선행스팬 A (Senkou Span A)
        result_df['ichimoku_senkou_a'] = ((result_df['ichimoku_tenkan'] + result_df['ichimoku_kijun']) / 2).shift(displacement)
        
        # 선행스팬 B (Senkou Span B)
        result_df['ichimoku_senkou_b'] = ((result_df['high'].rolling(window=senkou_b_period).max() + 
                                       result_df['low'].rolling(window=senkou_b_period).min()) / 2).shift(displacement)
        
        # 후행스팬 (Chikou Span)
        result_df['ichimoku_chikou'] = result_df['close'].shift(-displacement)
        
        return result_df
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """모든 기술적 지표를 계산합니다.
        
        Args:
            df: OHLCV 데이터가 포함된 DataFrame
            
        Returns:
            pd.DataFrame: 모든 기술적 지표가 추가된 DataFrame
        """
        if df.empty:
            return df
        
        result_df = df.copy()
        
        # 이동 평균
        result_df = self.calculate_sma(result_df)
        result_df = self.calculate_ema(result_df)
        
        # 볼린저 밴드
        result_df = self.calculate_bollinger_bands(result_df)
        
        # RSI
        result_df = self.calculate_rsi(result_df)
        
        # MACD
        result_df = self.calculate_macd(result_df)
        
        # 스토캐스틱 오실레이터
        result_df = self.calculate_stochastic(result_df)
        
        # ATR
        result_df = self.calculate_atr(result_df)
        
        # ADX
        result_df = self.calculate_adx(result_df)
        
        # 일목균형표
        result_df = self.calculate_ichimoku(result_df)
        
        return result_df
    
    def normalize_data(self, df: pd.DataFrame, columns: List[str] = None, method: str = 'minmax', feature_range: Tuple[float, float] = (0, 1), key: str = None) -> pd.DataFrame:
        """데이터를 정규화합니다.
        
        Args:
            df: 정규화할 DataFrame
            columns: 정규화할 컬럼 목록 (None인 경우 모든 숫자형 컬럼)
            method: 정규화 방법 ('minmax' 또는 'standard')
            feature_range: MinMaxScaler의 범위 (method가 'minmax'인 경우에만 사용)
            key: 스케일러를 저장할 키 (None인 경우 새 스케일러 생성)
            
        Returns:
            pd.DataFrame: 정규화된 DataFrame
        """
        if df.empty:
            return df
        
        result_df = df.copy()
        
        # 정규화할 컬럼 선택
        if columns is None:
            # 숫자형 컬럼만 선택
            columns = result_df.select_dtypes(include=['number']).columns.tolist()
            
            # timestamp 컬럼 제외
            if 'timestamp' in columns:
                columns.remove('timestamp')
        
        # 정규화할 데이터 추출
        data = result_df[columns].values
        
        # 스케일러 생성 또는 가져오기
        if key is None or key not in self.scalers:
            if method == 'minmax':
                scaler = MinMaxScaler(feature_range=feature_range)
            elif method == 'standard':
                scaler = StandardScaler()
            else:
                raise ValueError(f"지원하지 않는 정규화 방법입니다: {method}")
            
            # 스케일러 학습
            scaler.fit(data)
            
            # 스케일러 저장
            if key is not None:
                self.scalers[key] = scaler
        else:
            scaler = self.scalers[key]
        
        # 데이터 정규화
        normalized_data = scaler.transform(data)
        
        # 정규화된 데이터를 DataFrame에 적용
        for i, column in enumerate(columns):
            result_df[f'{column}_norm'] = normalized_data[:, i]
        
        return result_df
    
    def denormalize_data(self, df: pd.DataFrame, columns: List[str], key: str) -> pd.DataFrame:
        """정규화된 데이터를 원래 스케일로 되돌립니다.
        
        Args:
            df: 역정규화할 DataFrame
            columns: 역정규화할 컬럼 목록
            key: 사용할 스케일러의 키
            
        Returns:
            pd.DataFrame: 역정규화된 DataFrame
        """
        if df.empty or key not in self.scalers:
            return df
        
        result_df = df.copy()
        scaler = self.scalers[key]
        
        # 역정규화할 데이터 추출
        data = result_df[columns].values
        
        # 데이터 역정규화
        denormalized_data = scaler.inverse_transform(data)
        
        # 역정규화된 데이터를 DataFrame에 적용
        for i, column in enumerate(columns):
            result_df[f'{column}_denorm'] = denormalized_data[:, i]
        
        return result_df
    
    def resample_data(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """데이터를 리샘플링합니다.
        
        Args:
            df: 리샘플링할 DataFrame (timestamp 컬럼 필요)
            timeframe: 리샘플링할 시간대 ('1min', '5min', '15min', '1H', '4H', '1D', '1W', '1M')
            
        Returns:
            pd.DataFrame: 리샘플링된 DataFrame
        """
        if df.empty or 'timestamp' not in df.columns:
            return df
        
        # timestamp를 인덱스로 설정
        result_df = df.copy()
        result_df = result_df.set_index('timestamp')
        
        # 리샘플링
        resampled = result_df.resample(timeframe)
        
        # OHLCV 데이터 리샘플링
        result = pd.DataFrame()
        
        if 'open' in result_df.columns:
            result['open'] = resampled['open'].first()
        
        if 'high' in result_df.columns:
            result['high'] = resampled['high'].max()
        
        if 'low' in result_df.columns:
            result['low'] = resampled['low'].min()
        
        if 'close' in result_df.columns:
            result['close'] = resampled['close'].last()
        
        if 'volume' in result_df.columns:
            result['volume'] = resampled['volume'].sum()
        
        # 나머지 컬럼은 평균값 사용
        for column in result_df.columns:
            if column not in ['open', 'high', 'low', 'close', 'volume']:
                result[column] = resampled[column].mean()
        
        # 인덱스를 컬럼으로 변환
        result = result.reset_index()
        
        # 결측값 제거
        result = result.dropna()
        
        return result
    
    def add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """시간 관련 특성을 추가합니다.
        
        Args:
            df: 시간 특성을 추가할 DataFrame (timestamp 컬럼 필요)
            
        Returns:
            pd.DataFrame: 시간 특성이 추가된 DataFrame
        """
        if df.empty or 'timestamp' not in df.columns:
            return df
        
        result_df = df.copy()
        
        # 시간 특성 추출
        result_df['hour'] = result_df['timestamp'].dt.hour
        result_df['day'] = result_df['timestamp'].dt.day
        result_df['weekday'] = result_df['timestamp'].dt.weekday
        result_df['month'] = result_df['timestamp'].dt.month
        result_df['year'] = result_df['timestamp'].dt.year
        
        # 주기적 특성 (사인, 코사인 변환)
        result_df['hour_sin'] = np.sin(2 * np.pi * result_df['hour'] / 24)
        result_df['hour_cos'] = np.cos(2 * np.pi * result_df['hour'] / 24)
        
        result_df['day_sin'] = np.sin(2 * np.pi * result_df['day'] / 31)
        result_df['day_cos'] = np.cos(2 * np.pi * result_df['day'] / 31)
        
        result_df['weekday_sin'] = np.sin(2 * np.pi * result_df['weekday'] / 7)
        result_df['weekday_cos'] = np.cos(2 * np.pi * result_df['weekday'] / 7)
        
        result_df['month_sin'] = np.sin(2 * np.pi * result_df['month'] / 12)
        result_df['month_cos'] = np.cos(2 * np.pi * result_df['month'] / 12)
        
        return result_df
    
    def add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """가격 관련 특성을 추가합니다.
        
        Args:
            df: 가격 특성을 추가할 DataFrame (OHLCV 데이터 필요)
            
        Returns:
            pd.DataFrame: 가격 특성이 추가된 DataFrame
        """
        if df.empty or not all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume']):
            return df
        
        result_df = df.copy()
        
        # 가격 변화
        result_df['price_change'] = result_df['close'] - result_df['open']
        result_df['price_change_pct'] = (result_df['close'] - result_df['open']) / result_df['open'] * 100
        
        # 전일 대비 변화
        result_df['close_change'] = result_df['close'].diff()
        result_df['close_change_pct'] = result_df['close'].pct_change() * 100
        
        # 고가-저가 범위
        result_df['high_low_range'] = result_df['high'] - result_df['low']
        result_df['high_low_range_pct'] = (result_df['high'] - result_df['low']) / result_df['low'] * 100
        
        # 거래량 변화
        result_df['volume_change'] = result_df['volume'].diff()
        result_df['volume_change_pct'] = result_df['volume'].pct_change() * 100
        
        # 가격-거래량 관계
        result_df['price_volume_ratio'] = result_df['close'] * result_df['volume']
        
        # 이동 평균 대비 가격
        result_df = self.calculate_sma(result_df, periods=[20])
        result_df['close_to_sma20'] = result_df['close'] / result_df['sma_20']
        
        return result_df
    
    def prepare_data_for_ml(self, df: pd.DataFrame, target_column: str = 'close', n_steps: int = 10, n_features: int = None, normalize: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """머신러닝 모델을 위한 데이터를 준비합니다.
        
        Args:
            df: 준비할 DataFrame
            target_column: 예측할 타겟 컬럼
            n_steps: 시퀀스 길이
            n_features: 특성 수 (None인 경우 모든 숫자형 컬럼)
            normalize: 정규화 여부
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: X, y 데이터
        """
        if df.empty:
            return np.array([]), np.array([])
        
        # 결측값 제거
        df = df.dropna()
        
        # 특성 선택
        if n_features is None:
            # 숫자형 컬럼만 선택
            feature_columns = df.select_dtypes(include=['number']).columns.tolist()
            
            # timestamp 컬럼 제외
            if 'timestamp' in feature_columns:
                feature_columns.remove('timestamp')
        else:
            # 상관관계가 높은 특성 선택
            corr = df.corr()[target_column].abs().sort_values(ascending=False)
            feature_columns = corr.index[:n_features].tolist()
        
        # 정규화
        if normalize:
            df = self.normalize_data(df, columns=feature_columns, key='ml_data')
            
            # 정규화된 컬럼 사용
            feature_columns = [f'{col}_norm' for col in feature_columns]
            
            # 타겟 컬럼도 정규화된 버전 사용
            target_column = f'{target_column}_norm'
        
        # 데이터 준비
        X, y = [], []
        
        for i in range(len(df) - n_steps):
            X.append(df[feature_columns].values[i:i+n_steps])
            y.append(df[target_column].values[i+n_steps])
        
        return np.array(X), np.array(y)