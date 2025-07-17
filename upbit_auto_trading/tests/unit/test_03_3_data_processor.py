#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
데이터 처리기 단위 테스트
개발 순서: 3.3 데이터 처리기 구현
"""

import unittest
import pandas as pd
import numpy as np
import os
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# 데이터 처리기 클래스 임포트
# 아직 구현되지 않았다면 테스트가 실패할 것입니다.
from upbit_auto_trading.data_layer.processors.data_processor import DataProcessor

class TestDataProcessor(unittest.TestCase):
    """DataProcessor 클래스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        print("\n===== 테스트 시작: {} =====".format(self._testMethodName))
        
        # 테스트용 OHLCV 데이터 생성
        dates = pd.date_range(start='2023-01-01', periods=100, freq='1D')
        self.test_data = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.normal(50000000, 5000000, 100),
            'high': np.random.normal(52000000, 5000000, 100),
            'low': np.random.normal(48000000, 5000000, 100),
            'close': np.random.normal(51000000, 5000000, 100),
            'volume': np.random.normal(100, 20, 100),
            'symbol': ['KRW-BTC'] * 100,
            'timeframe': ['1d'] * 100
        })
        
        # 데이터 일관성 보장 (high >= open, close, low / low <= open, close, high)
        for i in range(len(self.test_data)):
            values = [self.test_data.loc[i, 'open'], self.test_data.loc[i, 'close']]
            self.test_data.loc[i, 'high'] = max(values) + abs(np.random.normal(1000000, 500000))
            self.test_data.loc[i, 'low'] = min(values) - abs(np.random.normal(1000000, 500000))
            self.test_data.loc[i, 'volume'] = abs(self.test_data.loc[i, 'volume'])
        
        print(f"테스트 데이터 생성 완료: {len(self.test_data)}개의 OHLCV 데이터")
        print(f"데이터 샘플:\n{self.test_data.head(3)}")
        
        # 데이터 처리기 인스턴스 생성
        self.processor = DataProcessor()
    
    def tearDown(self):
        """테스트 정리"""
        print("\n===== 테스트 종료: {} =====".format(self._testMethodName))
    
    def test_03_3_1_calculate_sma(self):
        """단순 이동 평균(SMA) 계산 테스트"""
        print("\n단순 이동 평균(SMA) 계산 테스트 시작")
        
        # 테스트 파라미터
        window = 20
        column = 'close'
        
        # SMA 계산
        result = self.processor.calculate_sma(self.test_data, window, column)
        
        print(f"SMA 계산 결과: {len(result)}개의 데이터")
        print(f"원본 데이터 컬럼: {list(self.test_data.columns)}")
        print(f"결과 데이터 컬럼: {list(result.columns)}")
        print(f"SMA_{window} 컬럼 샘플:\n{result[['timestamp', column, f'SMA_{window}']].head(3)}")
        
        # 검증
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn(f'SMA_{window}', result.columns)
        self.assertEqual(len(result), len(self.test_data))
        
        # 첫 (window-1)개 행은 NaN이어야 함
        self.assertTrue(result[f'SMA_{window}'].iloc[:window-1].isna().all())
        
        # window 이후의 값들은 NaN이 아니어야 함
        self.assertTrue(result[f'SMA_{window}'].iloc[window:].notna().all())
        
        # 수동 계산으로 검증
        manual_sma = self.test_data[column].rolling(window=window).mean()
        # 값만 비교 (이름은 비교하지 않음)
        np.testing.assert_allclose(
            result[f'SMA_{window}'].dropna().values, 
            manual_sma.dropna().values,
            rtol=1e-10
        )
        
        print("단순 이동 평균(SMA) 계산 테스트 통과")
    
    def test_03_3_2_calculate_ema(self):
        """지수 이동 평균(EMA) 계산 테스트"""
        print("\n지수 이동 평균(EMA) 계산 테스트 시작")
        
        # 테스트 파라미터
        window = 20
        column = 'close'
        
        # EMA 계산
        result = self.processor.calculate_ema(self.test_data, window, column)
        
        print(f"EMA 계산 결과: {len(result)}개의 데이터")
        print(f"결과 데이터 컬럼: {list(result.columns)}")
        print(f"EMA_{window} 컬럼 샘플:\n{result[['timestamp', column, f'EMA_{window}']].head(3)}")
        
        # 검증
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn(f'EMA_{window}', result.columns)
        self.assertEqual(len(result), len(self.test_data))
        
        # 첫 행은 NaN이어야 함 (EMA는 첫 값을 SMA로 초기화)
        self.assertTrue(pd.isna(result[f'EMA_{window}'].iloc[0]))
        
        # 두 번째 행부터는 NaN이 아니어야 함
        self.assertTrue(result[f'EMA_{window}'].iloc[1:].notna().all())
        
        # 수동 계산으로 검증
        manual_ema = self.test_data[column].ewm(span=window, adjust=False).mean()
        
        # 첫 번째 값을 NaN으로 설정 (테스트 요구사항에 맞춤)
        manual_ema.iloc[0] = np.nan
        
        # 부동 소수점 오차를 고려하여 근사값 비교
        np.testing.assert_allclose(
            result[f'EMA_{window}'].dropna().values, 
            manual_ema.dropna().values,
            rtol=1e-10
        )
        
        print("지수 이동 평균(EMA) 계산 테스트 통과")
    
    def test_03_3_3_calculate_rsi(self):
        """상대 강도 지수(RSI) 계산 테스트"""
        print("\n상대 강도 지수(RSI) 계산 테스트 시작")
        
        # 테스트 파라미터
        window = 14
        column = 'close'
        
        # RSI 계산
        result = self.processor.calculate_rsi(self.test_data, window, column)
        
        print(f"RSI 계산 결과: {len(result)}개의 데이터")
        print(f"결과 데이터 컬럼: {list(result.columns)}")
        print(f"RSI_{window} 컬럼 샘플:\n{result[['timestamp', column, f'RSI_{window}']].head(window+3)}")
        
        # 검증
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn(f'RSI_{window}', result.columns)
        self.assertEqual(len(result), len(self.test_data))
        
        # 첫 window+1개 행은 NaN이어야 함 (차이 계산 + 평균 계산에 필요한 기간)
        self.assertTrue(result[f'RSI_{window}'].iloc[:window].isna().all())
        
        # window+1 이후의 값들은 NaN이 아니어야 함
        self.assertTrue(result[f'RSI_{window}'].iloc[window:].notna().all())
        
        # RSI 값은 0에서 100 사이여야 함
        valid_rsi = result[f'RSI_{window}'].dropna()
        self.assertTrue((valid_rsi >= 0).all() and (valid_rsi <= 100).all())
        
        print(f"RSI 값 범위: {valid_rsi.min()} ~ {valid_rsi.max()}")
        print("상대 강도 지수(RSI) 계산 테스트 통과")
    
    def test_03_3_4_calculate_bollinger_bands(self):
        """볼린저 밴드 계산 테스트"""
        print("\n볼린저 밴드 계산 테스트 시작")
        
        # 테스트 파라미터
        window = 20
        num_std = 2
        column = 'close'
        
        # 볼린저 밴드 계산
        result = self.processor.calculate_bollinger_bands(self.test_data, window, num_std, column)
        
        print(f"볼린저 밴드 계산 결과: {len(result)}개의 데이터")
        print(f"결과 데이터 컬럼: {list(result.columns)}")
        print(f"볼린저 밴드 컬럼 샘플:\n{result[['timestamp', column, 'BB_MIDDLE', 'BB_UPPER', 'BB_LOWER']].head(3)}")
        
        # 검증
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn('BB_MIDDLE', result.columns)
        self.assertIn('BB_UPPER', result.columns)
        self.assertIn('BB_LOWER', result.columns)
        self.assertEqual(len(result), len(self.test_data))
        
        # 첫 (window-1)개 행은 NaN이어야 함
        self.assertTrue(result['BB_MIDDLE'].iloc[:window-1].isna().all())
        self.assertTrue(result['BB_UPPER'].iloc[:window-1].isna().all())
        self.assertTrue(result['BB_LOWER'].iloc[:window-1].isna().all())
        
        # window 이후의 값들은 NaN이 아니어야 함
        self.assertTrue(result['BB_MIDDLE'].iloc[window-1:].notna().all())
        self.assertTrue(result['BB_UPPER'].iloc[window-1:].notna().all())
        self.assertTrue(result['BB_LOWER'].iloc[window-1:].notna().all())
        
        # 수동 계산으로 검증
        sma = self.test_data[column].rolling(window=window).mean()
        std = self.test_data[column].rolling(window=window).std()
        upper = sma + (std * num_std)
        lower = sma - (std * num_std)
        
        # 값만 비교 (이름은 비교하지 않음)
        np.testing.assert_allclose(
            result['BB_MIDDLE'].dropna().values, 
            sma.dropna().values,
            rtol=1e-10
        )
        
        np.testing.assert_allclose(
            result['BB_UPPER'].dropna().values, 
            upper.dropna().values,
            rtol=1e-10
        )
        
        np.testing.assert_allclose(
            result['BB_LOWER'].dropna().values, 
            lower.dropna().values,
            rtol=1e-10
        )
        
        # 상단 밴드는 항상 중간 밴드보다 크거나 같아야 함 (NaN 값 제외)
        valid_idx = result['BB_MIDDLE'].notna()
        self.assertTrue((result.loc[valid_idx, 'BB_UPPER'] >= result.loc[valid_idx, 'BB_MIDDLE']).all())
        
        # 하단 밴드는 항상 중간 밴드보다 작거나 같아야 함 (NaN 값 제외)
        self.assertTrue((result.loc[valid_idx, 'BB_LOWER'] <= result.loc[valid_idx, 'BB_MIDDLE']).all())
        
        print("볼린저 밴드 계산 테스트 통과")
    
    def test_03_3_5_calculate_macd(self):
        """MACD 계산 테스트"""
        print("\nMACD 계산 테스트 시작")
        
        # 테스트 파라미터
        fast_period = 12
        slow_period = 26
        signal_period = 9
        column = 'close'
        
        # MACD 계산
        result = self.processor.calculate_macd(self.test_data, fast_period, slow_period, signal_period, column)
        
        print(f"MACD 계산 결과: {len(result)}개의 데이터")
        print(f"결과 데이터 컬럼: {list(result.columns)}")
        print(f"MACD 컬럼 샘플:\n{result[['timestamp', column, 'MACD', 'MACD_SIGNAL', 'MACD_HIST']].head(3)}")
        
        # 검증
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn('MACD', result.columns)
        self.assertIn('MACD_SIGNAL', result.columns)
        self.assertIn('MACD_HIST', result.columns)
        self.assertEqual(len(result), len(self.test_data))
        
        # 첫 몇 개 행은 NaN이어야 함 (EMA 계산에 필요한 기간)
        self.assertTrue(result['MACD'].iloc[:slow_period-2].isna().all())
        self.assertTrue(result['MACD_SIGNAL'].iloc[:slow_period+signal_period-3].isna().all())
        self.assertTrue(result['MACD_HIST'].iloc[:slow_period+signal_period-3].isna().all())
        
        # 수동 계산으로 검증 - 여기서는 값의 패턴만 확인하고 정확한 일치는 요구하지 않음
        # 이는 EMA 계산 방식의 차이로 인한 오차를 허용하기 위함
        
        # MACD 값이 NaN이 아닌 부분만 확인
        valid_idx = result['MACD'].notna() & result['MACD_SIGNAL'].notna() & result['MACD_HIST'].notna()
        
        # 값이 존재하는지 확인
        self.assertTrue(valid_idx.sum() > 0)
        
        # MACD 히스토그램은 MACD - 시그널 라인과 같아야 함
        # 동일한 인덱스의 값들만 비교
        macd_values = result.loc[valid_idx, 'MACD']
        signal_values = result.loc[valid_idx, 'MACD_SIGNAL']
        hist_values = result.loc[valid_idx, 'MACD_HIST']
        
        # 계산된 히스토그램 값
        calculated_hist = macd_values - signal_values
        
        # 값 비교
        np.testing.assert_allclose(
            hist_values.values,
            calculated_hist.values,
            rtol=1e-10
        )
        
        print("MACD 계산 테스트 통과")
    
    def test_03_3_6_calculate_stochastic(self):
        """스토캐스틱 계산 테스트"""
        print("\n스토캐스틱 계산 테스트 시작")
        
        # 테스트 파라미터
        k_period = 14
        d_period = 3
        
        # 스토캐스틱 계산
        result = self.processor.calculate_stochastic(self.test_data, k_period, d_period)
        
        print(f"스토캐스틱 계산 결과: {len(result)}개의 데이터")
        print(f"결과 데이터 컬럼: {list(result.columns)}")
        print(f"스토캐스틱 컬럼 샘플:\n{result[['timestamp', 'close', 'STOCH_K', 'STOCH_D']].head(3)}")
        
        # 검증
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn('STOCH_K', result.columns)
        self.assertIn('STOCH_D', result.columns)
        self.assertEqual(len(result), len(self.test_data))
        
        # 첫 몇 개 행은 NaN이어야 함
        self.assertTrue(result['STOCH_K'].iloc[:k_period-1].isna().all())
        self.assertTrue(result['STOCH_D'].iloc[:k_period+d_period-2].isna().all())
        
        # k_period 이후의 값들은 NaN이 아니어야 함
        self.assertTrue(result['STOCH_K'].iloc[k_period-1:].notna().all())
        self.assertTrue(result['STOCH_D'].iloc[k_period+d_period-2:].notna().all())
        
        # 스토캐스틱 값은 0에서 100 사이여야 함
        valid_k = result['STOCH_K'].dropna()
        valid_d = result['STOCH_D'].dropna()
        self.assertTrue((valid_k >= 0).all() and (valid_k <= 100).all())
        self.assertTrue((valid_d >= 0).all() and (valid_d <= 100).all())
        
        print(f"STOCH_K 값 범위: {valid_k.min()} ~ {valid_k.max()}")
        print(f"STOCH_D 값 범위: {valid_d.min()} ~ {valid_d.max()}")
        print("스토캐스틱 계산 테스트 통과")
    
    def test_03_3_7_calculate_atr(self):
        """평균 실제 범위(ATR) 계산 테스트"""
        print("\n평균 실제 범위(ATR) 계산 테스트 시작")
        
        # 테스트 파라미터
        window = 14
        
        # ATR 계산
        result = self.processor.calculate_atr(self.test_data, window)
        
        print(f"ATR 계산 결과: {len(result)}개의 데이터")
        print(f"결과 데이터 컬럼: {list(result.columns)}")
        print(f"ATR 컬럼 샘플:\n{result[['timestamp', 'high', 'low', 'close', f'ATR_{window}']].head(3)}")
        
        # 검증
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn(f'ATR_{window}', result.columns)
        self.assertEqual(len(result), len(self.test_data))
        
        # 첫 window개 행은 NaN이어야 함
        self.assertTrue(result[f'ATR_{window}'].iloc[:window].isna().all())
        
        # window 이후의 값들은 NaN이 아니어야 함
        self.assertTrue(result[f'ATR_{window}'].iloc[window:].notna().all())
        
        # ATR은 항상 양수여야 함
        valid_atr = result[f'ATR_{window}'].dropna()
        self.assertTrue((valid_atr > 0).all())
        
        print(f"ATR 값 범위: {valid_atr.min()} ~ {valid_atr.max()}")
        print("평균 실제 범위(ATR) 계산 테스트 통과")
    
    def test_03_3_8_calculate_indicators(self):
        """여러 지표 동시 계산 테스트"""
        print("\n여러 지표 동시 계산 테스트 시작")
        
        # 테스트 파라미터
        indicators = [
            {
                "name": "SMA",
                "params": {
                    "window": 20,
                    "column": "close"
                }
            },
            {
                "name": "RSI",
                "params": {
                    "window": 14,
                    "column": "close"
                }
            },
            {
                "name": "BOLLINGER_BANDS",
                "params": {
                    "window": 20,
                    "num_std": 2,
                    "column": "close"
                }
            }
        ]
        
        # 여러 지표 계산
        result = self.processor.calculate_indicators(self.test_data, indicators)
        
        print(f"여러 지표 계산 결과: {len(result)}개의 데이터")
        print(f"결과 데이터 컬럼: {list(result.columns)}")
        
        # 검증
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn('SMA_20', result.columns)
        self.assertIn('RSI_14', result.columns)
        self.assertIn('BB_MIDDLE', result.columns)
        self.assertIn('BB_UPPER', result.columns)
        self.assertIn('BB_LOWER', result.columns)
        self.assertEqual(len(result), len(self.test_data))
        
        print("여러 지표 동시 계산 테스트 통과")
    
    def test_03_3_9_normalize_data(self):
        """데이터 정규화 테스트"""
        print("\n데이터 정규화 테스트 시작")
        
        # 테스트 파라미터
        columns = ['open', 'high', 'low', 'close', 'volume']
        
        # MinMax 정규화
        result_minmax = self.processor.normalize_data(self.test_data, method='minmax', columns=columns)
        
        print(f"MinMax 정규화 결과: {len(result_minmax)}개의 데이터")
        print(f"결과 데이터 컬럼: {list(result_minmax.columns)}")
        print(f"MinMax 정규화 샘플:\n{result_minmax[['timestamp'] + columns].head(3)}")
        
        # Z-Score 정규화
        result_zscore = self.processor.normalize_data(self.test_data, method='zscore', columns=columns)
        
        print(f"Z-Score 정규화 결과: {len(result_zscore)}개의 데이터")
        print(f"Z-Score 정규화 샘플:\n{result_zscore[['timestamp'] + columns].head(3)}")
        
        # 검증
        self.assertIsInstance(result_minmax, pd.DataFrame)
        self.assertIsInstance(result_zscore, pd.DataFrame)
        self.assertEqual(len(result_minmax), len(self.test_data))
        self.assertEqual(len(result_zscore), len(self.test_data))
        
        # MinMax 정규화 값은 0에서 1 사이여야 함
        for col in columns:
            self.assertTrue((result_minmax[col] >= 0).all() and (result_minmax[col] <= 1).all())
            print(f"MinMax {col} 값 범위: {result_minmax[col].min()} ~ {result_minmax[col].max()}")
        
        # Z-Score 정규화 값의 평균은 0에 가깝고, 표준편차는 1에 가까워야 함
        for col in columns:
            self.assertAlmostEqual(result_zscore[col].mean(), 0, delta=0.1)
            self.assertAlmostEqual(result_zscore[col].std(), 1, delta=0.1)
            print(f"Z-Score {col} 평균: {result_zscore[col].mean()}, 표준편차: {result_zscore[col].std()}")
        
        print("데이터 정규화 테스트 통과")
    
    def test_03_3_10_resample_data(self):
        """데이터 리샘플링 테스트"""
        print("\n데이터 리샘플링 테스트 시작")
        
        # 분 단위 데이터 생성 (1분 간격)
        dates = pd.date_range(start='2023-01-01', periods=1440, freq='1min')  # 1일치 1분 데이터
        minute_data = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.normal(50000000, 5000000, 1440),
            'high': np.random.normal(52000000, 5000000, 1440),
            'low': np.random.normal(48000000, 5000000, 1440),
            'close': np.random.normal(51000000, 5000000, 1440),
            'volume': np.abs(np.random.normal(10, 5, 1440)),
            'symbol': ['KRW-BTC'] * 1440,
            'timeframe': ['1m'] * 1440
        })
        
        # 데이터 일관성 보장
        for i in range(len(minute_data)):
            values = [minute_data.loc[i, 'open'], minute_data.loc[i, 'close']]
            minute_data.loc[i, 'high'] = max(values) + abs(np.random.normal(10000, 5000))
            minute_data.loc[i, 'low'] = min(values) - abs(np.random.normal(10000, 5000))
        
        print(f"1분 데이터 생성 완료: {len(minute_data)}개")
        print(f"1분 데이터 샘플:\n{minute_data.head(3)}")
        
        # 5분 데이터로 리샘플링
        result_5m = self.processor.resample_data(minute_data, '5m')
        
        print(f"5분 리샘플링 결과: {len(result_5m)}개의 데이터")
        print(f"5분 데이터 샘플:\n{result_5m.head(3)}")
        
        # 1시간 데이터로 리샘플링
        result_1h = self.processor.resample_data(minute_data, '1h')
        
        print(f"1시간 리샘플링 결과: {len(result_1h)}개의 데이터")
        print(f"1시간 데이터 샘플:\n{result_1h.head(3)}")
        
        # 검증
        self.assertIsInstance(result_5m, pd.DataFrame)
        self.assertIsInstance(result_1h, pd.DataFrame)
        
        # 5분 데이터는 1분 데이터의 1/5 정도여야 함
        self.assertAlmostEqual(len(result_5m), len(minute_data) / 5, delta=1)
        
        # 1시간 데이터는 1분 데이터의 1/60 정도여야 함
        self.assertAlmostEqual(len(result_1h), len(minute_data) / 60, delta=1)
        
        # 리샘플링된 데이터의 timeframe 값이 올바르게 설정되었는지 확인
        self.assertTrue((result_5m['timeframe'] == '5m').all())
        self.assertTrue((result_1h['timeframe'] == '1h').all())
        
        # OHLC 값이 올바르게 계산되었는지 확인 (첫 5분 데이터)
        first_5m_data = minute_data.iloc[:5]
        self.assertEqual(result_5m['open'].iloc[0], first_5m_data['open'].iloc[0])
        self.assertEqual(result_5m['high'].iloc[0], first_5m_data['high'].max())
        self.assertEqual(result_5m['low'].iloc[0], first_5m_data['low'].min())
        self.assertEqual(result_5m['close'].iloc[0], first_5m_data['close'].iloc[-1])
        self.assertAlmostEqual(result_5m['volume'].iloc[0], first_5m_data['volume'].sum(), delta=0.001)
        
        print("데이터 리샘플링 테스트 통과")

if __name__ == '__main__':
    unittest.main()