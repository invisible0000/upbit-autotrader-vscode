#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
데이터 처리기 단위 테스트
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler, StandardScaler

from upbit_auto_trading.data_layer.processors.data_processor import DataProcessor

class TestDataProcessor(unittest.TestCase):
    """DataProcessor 클래스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.processor = DataProcessor()
        
        # 테스트용 OHLCV 데이터 생성
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        
        self.test_df = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.normal(50000000, 5000000, 100),
            'high': np.random.normal(52000000, 5000000, 100),
            'low': np.random.normal(48000000, 5000000, 100),
            'close': np.random.normal(51000000, 5000000, 100),
            'volume': np.random.normal(100, 20, 100)
        })
        
        # 고가가 항상 저가보다 크도록 조정
        self.test_df['high'] = self.test_df[['open', 'close']].max(axis=1) + abs(np.random.normal(1000000, 500000, 100))
        self.test_df['low'] = self.test_df[['open', 'close']].min(axis=1) - abs(np.random.normal(1000000, 500000, 100))
        
        # 음수 값 제거
        self.test_df['open'] = self.test_df['open'].abs()
        self.test_df['high'] = self.test_df['high'].abs()
        self.test_df['low'] = self.test_df['low'].abs()
        self.test_df['close'] = self.test_df['close'].abs()
        self.test_df['volume'] = self.test_df['volume'].abs()
    
    def test_calculate_sma(self):
        """단순 이동 평균 계산 테스트"""
        # 메서드 호출
        result = self.processor.calculate_sma(self.test_df, periods=[5, 10])
        
        # 검증
        self.assertIn('sma_5', result.columns)
        self.assertIn('sma_10', result.columns)
        
        # NaN 값 확인 (첫 n-1개 값은 NaN이어야 함)
        self.assertTrue(result['sma_5'].iloc[:4].isna().all())
        self.assertTrue(result['sma_10'].iloc[:9].isna().all())
        
        # 값 계산 확인
        for i in range(5, len(result)):
            expected_sma5 = self.test_df['close'].iloc[i-5:i].mean()
            self.assertAlmostEqual(result['sma_5'].iloc[i], expected_sma5)
        
        for i in range(10, len(result)):
            expected_sma10 = self.test_df['close'].iloc[i-10:i].mean()
            self.assertAlmostEqual(result['sma_10'].iloc[i], expected_sma10)
    
    def test_calculate_ema(self):
        """지수 이동 평균 계산 테스트"""
        # 메서드 호출
        result = self.processor.calculate_ema(self.test_df, periods=[5, 10])
        
        # 검증
        self.assertIn('ema_5', result.columns)
        self.assertIn('ema_10', result.columns)
        
        # 값 확인 (첫 번째 값은 단순 평균과 같아야 함)
        expected_ema5_first = self.test_df['close'].iloc[:5].mean()
        self.assertAlmostEqual(result['ema_5'].iloc[4], expected_ema5_first, places=0)
    
    def test_calculate_bollinger_bands(self):
        """볼린저 밴드 계산 테스트"""
        # 메서드 호출
        result = self.processor.calculate_bollinger_bands(self.test_df)
        
        # 검증
        self.assertIn('bb_middle', result.columns)
        self.assertIn('bb_upper', result.columns)
        self.assertIn('bb_lower', result.columns)
        self.assertIn('bb_width', result.columns)
        self.assertIn('bb_pct_b', result.columns)
        
        # NaN 값 확인 (첫 n-1개 값은 NaN이어야 함)
        self.assertTrue(result['bb_middle'].iloc[:19].isna().all())
        
        # 값 계산 확인
        for i in range(20, len(result)):
            expected_middle = self.test_df['close'].iloc[i-20:i].mean()
            expected_std = self.test_df['close'].iloc[i-20:i].std()
            expected_upper = expected_middle + (expected_std * 2)
            expected_lower = expected_middle - (expected_std * 2)
            
            self.assertAlmostEqual(result['bb_middle'].iloc[i], expected_middle)
            self.assertAlmostEqual(result['bb_upper'].iloc[i], expected_upper)
            self.assertAlmostEqual(result['bb_lower'].iloc[i], expected_lower)
    
    def test_calculate_rsi(self):
        """RSI 계산 테스트"""
        # 메서드 호출
        result = self.processor.calculate_rsi(self.test_df)
        
        # 검증
        self.assertIn('rsi', result.columns)
        
        # NaN 값 확인 (첫 n개 값은 NaN이어야 함)
        self.assertTrue(result['rsi'].iloc[:14].isna().all())
        
        # 값 범위 확인 (0-100)
        self.assertTrue((result['rsi'].dropna() >= 0).all())
        self.assertTrue((result['rsi'].dropna() <= 100).all())
    
    def test_calculate_macd(self):
        """MACD 계산 테스트"""
        # 메서드 호출
        result = self.processor.calculate_macd(self.test_df)
        
        # 검증
        self.assertIn('macd', result.columns)
        self.assertIn('macd_signal', result.columns)
        self.assertIn('macd_hist', result.columns)
        
        # 히스토그램 값 확인
        for i in range(len(result)):
            if not pd.isna(result['macd'].iloc[i]) and not pd.isna(result['macd_signal'].iloc[i]):
                expected_hist = result['macd'].iloc[i] - result['macd_signal'].iloc[i]
                self.assertAlmostEqual(result['macd_hist'].iloc[i], expected_hist)
    
    def test_calculate_stochastic(self):
        """스토캐스틱 오실레이터 계산 테스트"""
        # 메서드 호출
        result = self.processor.calculate_stochastic(self.test_df)
        
        # 검증
        self.assertIn('stoch_k', result.columns)
        self.assertIn('stoch_d', result.columns)
        
        # 값 범위 확인 (0-100)
        self.assertTrue((result['stoch_k'].dropna() >= 0).all())
        self.assertTrue((result['stoch_k'].dropna() <= 100).all())
        self.assertTrue((result['stoch_d'].dropna() >= 0).all())
        self.assertTrue((result['stoch_d'].dropna() <= 100).all())
    
    def test_calculate_atr(self):
        """ATR 계산 테스트"""
        # 메서드 호출
        result = self.processor.calculate_atr(self.test_df)
        
        # 검증
        self.assertIn('atr', result.columns)
        
        # NaN 값 확인 (첫 n개 값은 NaN이어야 함)
        self.assertTrue(result['atr'].iloc[:14].isna().all())
        
        # 값 확인 (항상 양수여야 함)
        self.assertTrue((result['atr'].dropna() > 0).all())
    
    def test_calculate_adx(self):
        """ADX 계산 테스트"""
        # 메서드 호출
        result = self.processor.calculate_adx(self.test_df)
        
        # 검증
        self.assertIn('adx', result.columns)
        self.assertIn('plus_di', result.columns)
        self.assertIn('minus_di', result.columns)
        
        # 값 범위 확인 (0-100)
        self.assertTrue((result['adx'].dropna() >= 0).all())
        self.assertTrue((result['adx'].dropna() <= 100).all())
        self.assertTrue((result['plus_di'].dropna() >= 0).all())
        self.assertTrue((result['plus_di'].dropna() <= 100).all())
        self.assertTrue((result['minus_di'].dropna() >= 0).all())
        self.assertTrue((result['minus_di'].dropna() <= 100).all())
    
    def test_calculate_ichimoku(self):
        """일목균형표 계산 테스트"""
        # 메서드 호출
        result = self.processor.calculate_ichimoku(self.test_df)
        
        # 검증
        self.assertIn('ichimoku_tenkan', result.columns)
        self.assertIn('ichimoku_kijun', result.columns)
        self.assertIn('ichimoku_senkou_a', result.columns)
        self.assertIn('ichimoku_senkou_b', result.columns)
        self.assertIn('ichimoku_chikou', result.columns)
        
        # 전환선 계산 확인
        for i in range(9, len(result)):
            expected_tenkan = (self.test_df['high'].iloc[i-9:i].max() + self.test_df['low'].iloc[i-9:i].min()) / 2
            self.assertAlmostEqual(result['ichimoku_tenkan'].iloc[i], expected_tenkan)
    
    def test_calculate_all_indicators(self):
        """모든 지표 계산 테스트"""
        # 메서드 호출
        result = self.processor.calculate_all_indicators(self.test_df)
        
        # 검증
        indicator_columns = [
            'sma_5', 'sma_10', 'sma_20', 'sma_50', 'sma_200',
            'ema_5', 'ema_10', 'ema_20', 'ema_50', 'ema_200',
            'bb_middle', 'bb_upper', 'bb_lower',
            'rsi', 'macd', 'macd_signal', 'macd_hist',
            'stoch_k', 'stoch_d', 'atr', 'adx',
            'ichimoku_tenkan', 'ichimoku_kijun'
        ]
        
        for column in indicator_columns:
            self.assertIn(column, result.columns)
    
    def test_normalize_data_minmax(self):
        """MinMax 정규화 테스트"""
        # 메서드 호출
        result = self.processor.normalize_data(self.test_df, columns=['close', 'volume'], method='minmax', key='test_minmax')
        
        # 검증
        self.assertIn('close_norm', result.columns)
        self.assertIn('volume_norm', result.columns)
        
        # 값 범위 확인 (0-1)
        self.assertTrue((result['close_norm'] >= 0).all())
        self.assertTrue((result['close_norm'] <= 1).all())
        self.assertTrue((result['volume_norm'] >= 0).all())
        self.assertTrue((result['volume_norm'] <= 1).all())
        
        # 스케일러 저장 확인
        self.assertIn('test_minmax', self.processor.scalers)
        self.assertIsInstance(self.processor.scalers['test_minmax'], MinMaxScaler)
    
    def test_normalize_data_standard(self):
        """표준화 테스트"""
        # 메서드 호출
        result = self.processor.normalize_data(self.test_df, columns=['close', 'volume'], method='standard', key='test_standard')
        
        # 검증
        self.assertIn('close_norm', result.columns)
        self.assertIn('volume_norm', result.columns)
        
        # 평균과 표준편차 확인
        self.assertAlmostEqual(result['close_norm'].mean(), 0, places=1)
        self.assertAlmostEqual(result['close_norm'].std(), 1, places=1)
        self.assertAlmostEqual(result['volume_norm'].mean(), 0, places=1)
        self.assertAlmostEqual(result['volume_norm'].std(), 1, places=1)
        
        # 스케일러 저장 확인
        self.assertIn('test_standard', self.processor.scalers)
        self.assertIsInstance(self.processor.scalers['test_standard'], StandardScaler)
    
    def test_denormalize_data(self):
        """역정규화 테스트"""
        # 정규화
        normalized = self.processor.normalize_data(self.test_df, columns=['close', 'volume'], method='minmax', key='test_denorm')
        
        # 역정규화
        result = self.processor.denormalize_data(normalized, columns=['close_norm', 'volume_norm'], key='test_denorm')
        
        # 검증
        self.assertIn('close_norm_denorm', result.columns)
        self.assertIn('volume_norm_denorm', result.columns)
        
        # 원래 값과 비교
        for i in range(len(self.test_df)):
            self.assertAlmostEqual(result['close_norm_denorm'].iloc[i], self.test_df['close'].iloc[i], places=0)
            self.assertAlmostEqual(result['volume_norm_denorm'].iloc[i], self.test_df['volume'].iloc[i], places=0)
    
    def test_resample_data(self):
        """데이터 리샘플링 테스트"""
        # 1분 데이터 생성
        dates = pd.date_range(start='2023-01-01', periods=1440, freq='1min')  # 1일치 1분 데이터
        
        minute_df = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.normal(50000000, 5000000, 1440),
            'high': np.random.normal(52000000, 5000000, 1440),
            'low': np.random.normal(48000000, 5000000, 1440),
            'close': np.random.normal(51000000, 5000000, 1440),
            'volume': np.random.normal(100, 20, 1440)
        })
        
        # 고가가 항상 저가보다 크도록 조정
        minute_df['high'] = minute_df[['open', 'close']].max(axis=1) + abs(np.random.normal(1000000, 500000, 1440))
        minute_df['low'] = minute_df[['open', 'close']].min(axis=1) - abs(np.random.normal(1000000, 500000, 1440))
        
        # 음수 값 제거
        minute_df['open'] = minute_df['open'].abs()
        minute_df['high'] = minute_df['high'].abs()
        minute_df['low'] = minute_df['low'].abs()
        minute_df['close'] = minute_df['close'].abs()
        minute_df['volume'] = minute_df['volume'].abs()
        
        # 1시간으로 리샘플링
        result = self.processor.resample_data(minute_df, timeframe='1H')
        
        # 검증
        self.assertEqual(len(result), 24)  # 1일치 데이터를 1시간으로 리샘플링하면 24개
        
        # OHLCV 값 확인
        for i in range(24):
            start_idx = i * 60
            end_idx = (i + 1) * 60
            
            self.assertEqual(result['open'].iloc[i], minute_df['open'].iloc[start_idx])
            self.assertEqual(result['high'].iloc[i], minute_df['high'].iloc[start_idx:end_idx].max())
            self.assertEqual(result['low'].iloc[i], minute_df['low'].iloc[start_idx:end_idx].min())
            self.assertEqual(result['close'].iloc[i], minute_df['close'].iloc[end_idx - 1])
            self.assertAlmostEqual(result['volume'].iloc[i], minute_df['volume'].iloc[start_idx:end_idx].sum())
    
    def test_add_time_features(self):
        """시간 특성 추가 테스트"""
        # 메서드 호출
        result = self.processor.add_time_features(self.test_df)
        
        # 검증
        time_features = ['hour', 'day', 'weekday', 'month', 'year', 
                        'hour_sin', 'hour_cos', 'day_sin', 'day_cos', 
                        'weekday_sin', 'weekday_cos', 'month_sin', 'month_cos']
        
        for feature in time_features:
            self.assertIn(feature, result.columns)
        
        # 값 확인
        for i in range(len(result)):
            timestamp = self.test_df['timestamp'].iloc[i]
            
            self.assertEqual(result['hour'].iloc[i], timestamp.hour)
            self.assertEqual(result['day'].iloc[i], timestamp.day)
            self.assertEqual(result['weekday'].iloc[i], timestamp.weekday())
            self.assertEqual(result['month'].iloc[i], timestamp.month)
            self.assertEqual(result['year'].iloc[i], timestamp.year)
    
    def test_add_price_features(self):
        """가격 특성 추가 테스트"""
        # 메서드 호출
        result = self.processor.add_price_features(self.test_df)
        
        # 검증
        price_features = ['price_change', 'price_change_pct', 'close_change', 'close_change_pct',
                         'high_low_range', 'high_low_range_pct', 'volume_change', 'volume_change_pct',
                         'price_volume_ratio', 'sma_20', 'close_to_sma20']
        
        for feature in price_features:
            self.assertIn(feature, result.columns)
        
        # 값 확인
        for i in range(len(result)):
            self.assertEqual(result['price_change'].iloc[i], self.test_df['close'].iloc[i] - self.test_df['open'].iloc[i])
            self.assertEqual(result['high_low_range'].iloc[i], self.test_df['high'].iloc[i] - self.test_df['low'].iloc[i])
    
    def test_prepare_data_for_ml(self):
        """머신러닝 데이터 준비 테스트"""
        # 메서드 호출
        X, y = self.processor.prepare_data_for_ml(self.test_df, n_steps=5, n_features=3)
        
        # 검증
        self.assertEqual(X.shape[0], len(self.test_df) - 5)  # 샘플 수
        self.assertEqual(X.shape[1], 5)  # 시퀀스 길이
        self.assertEqual(X.shape[2], 3)  # 특성 수
        self.assertEqual(y.shape[0], len(self.test_df) - 5)  # 타겟 수

if __name__ == '__main__':
    unittest.main()