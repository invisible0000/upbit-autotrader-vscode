#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
기본 스크리너 테스트
개발 순서: 4.1 기본 스크리닝 기능 구현

BaseScreener 클래스의 기능을 테스트합니다.
"""

import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from upbit_auto_trading.business_logic.screener.base_screener import BaseScreener

class TestBaseScreener(unittest.TestCase):
    """BaseScreener 클래스 테스트"""
    
    @patch('upbit_auto_trading.business_logic.screener.base_screener.DataProcessor')
    @patch('upbit_auto_trading.business_logic.screener.base_screener.DataCollector')
    @patch('upbit_auto_trading.business_logic.screener.base_screener.UpbitAPI')
    def setUp(self, mock_api, mock_collector, mock_processor):
        """테스트 설정"""
        # 모의 객체 설정
        self.mock_api_instance = mock_api.return_value
        self.mock_collector_instance = mock_collector.return_value
        self.mock_processor_instance = mock_processor.return_value
        
        # BaseScreener 인스턴스 생성
        self.screener = BaseScreener()
        
        # 모의 객체 주입
        self.screener.api = self.mock_api_instance
        self.screener.data_collector = self.mock_collector_instance
        self.screener.data_processor = self.mock_processor_instance
    
    def test_04_1_1_screen_by_volume(self):
        """거래량 기준 스크리닝 테스트"""
        print("\n=== 테스트 id 4_1_1: test_screen_by_volume ===")
        # 모의 데이터 설정
        mock_markets = pd.DataFrame({
            'market': ['KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'BTC-ETH'],
            'korean_name': ['비트코인', '이더리움', '리플', '이더리움']
        })
        
        mock_tickers = pd.DataFrame({
            'market': ['KRW-BTC', 'KRW-ETH', 'KRW-XRP'],
            'acc_trade_price_24h': [5000000000, 2000000000, 500000000]
        })
        
        # 모의 객체 설정
        self.mock_api_instance.get_markets.return_value = mock_markets
        self.mock_api_instance.get_tickers.return_value = mock_tickers
        
        # 테스트 실행
        result = self.screener.screen_by_volume(1000000000)
        
        # 검증
        self.assertEqual(len(result), 2)
        self.assertIn('KRW-BTC', result)
        self.assertIn('KRW-ETH', result)
        self.assertNotIn('KRW-XRP', result)
    
    def test_04_1_2_screen_by_volatility(self):
        """변동성 기준 스크리닝 테스트"""
        print("\n=== 테스트 id 4_1_2: test_screen_by_volatility ===")
        # 모의 데이터 설정
        mock_markets = pd.DataFrame({
            'market': ['KRW-BTC', 'KRW-ETH', 'KRW-XRP'],
            'korean_name': ['비트코인', '이더리움', '리플']
        })
        
        # BTC: 높은 변동성 (10%)
        btc_data = pd.DataFrame({
            'timestamp': [datetime.now() - timedelta(days=i) for i in range(7)],
            'open': [10000000] * 7,
            'high': [11000000] * 7,
            'low': [10000000] * 7,
            'close': [10500000] * 7,
            'volume': [100] * 7,
            'symbol': ['KRW-BTC'] * 7,
            'timeframe': ['1d'] * 7
        })
        
        # ETH: 중간 변동성 (5%)
        eth_data = pd.DataFrame({
            'timestamp': [datetime.now() - timedelta(days=i) for i in range(7)],
            'open': [1000000] * 7,
            'high': [1050000] * 7,
            'low': [1000000] * 7,
            'close': [1025000] * 7,
            'volume': [100] * 7,
            'symbol': ['KRW-ETH'] * 7,
            'timeframe': ['1d'] * 7
        })
        
        # XRP: 낮은 변동성 (2%)
        xrp_data = pd.DataFrame({
            'timestamp': [datetime.now() - timedelta(days=i) for i in range(7)],
            'open': [500] * 7,
            'high': [510] * 7,
            'low': [500] * 7,
            'close': [505] * 7,
            'volume': [100] * 7,
            'symbol': ['KRW-XRP'] * 7,
            'timeframe': ['1d'] * 7
        })
        
        # 모의 객체 설정
        self.mock_api_instance.get_markets.return_value = mock_markets
        
        def mock_get_ohlcv_data(symbol, timeframe, start_date, end_date):
            if symbol == 'KRW-BTC':
                return btc_data
            elif symbol == 'KRW-ETH':
                return eth_data
            elif symbol == 'KRW-XRP':
                return xrp_data
            return pd.DataFrame()
        
        self.mock_collector_instance.get_ohlcv_data.side_effect = mock_get_ohlcv_data
        self.mock_collector_instance.collect_historical_ohlcv.side_effect = mock_get_ohlcv_data
        
        # 테스트 실행: 변동성 3% ~ 8% 필터링
        result = self.screener.screen_by_volatility(min_volatility=0.03, max_volatility=0.08)
        
        # 검증
        self.assertEqual(len(result), 1)
        self.assertIn('KRW-ETH', result)
        self.assertNotIn('KRW-BTC', result)  # 변동성이 너무 높음
        self.assertNotIn('KRW-XRP', result)  # 변동성이 너무 낮음
    
    def test_04_1_3_screen_by_trend(self):
        """추세 기준 스크리닝 테스트"""
        print("\n=== 테스트 id 4_1_3: test_screen_by_trend ===")
        # 모의 데이터 설정
        mock_markets = pd.DataFrame({
            'market': ['KRW-BTC', 'KRW-ETH', 'KRW-XRP'],
            'korean_name': ['비트코인', '이더리움', '리플']
        })
        
        # BTC: 상승 추세
        btc_data = pd.DataFrame({
            'timestamp': [datetime.now() - timedelta(days=i) for i in range(14, -1, -1)],
            'open': [10000000 + i * 100000 for i in range(15)],
            'high': [10100000 + i * 100000 for i in range(15)],
            'low': [9900000 + i * 100000 for i in range(15)],
            'close': [10050000 + i * 100000 for i in range(15)],
            'volume': [100] * 15,
            'symbol': ['KRW-BTC'] * 15,
            'timeframe': ['1d'] * 15
        })
        
        # ETH: 하락 추세
        eth_data = pd.DataFrame({
            'timestamp': [datetime.now() - timedelta(days=i) for i in range(14, -1, -1)],
            'open': [1000000 - i * 10000 for i in range(15)],
            'high': [1050000 - i * 10000 for i in range(15)],
            'low': [950000 - i * 10000 for i in range(15)],
            'close': [1000000 - i * 10000 for i in range(15)],
            'volume': [100] * 15,
            'symbol': ['KRW-ETH'] * 15,
            'timeframe': ['1d'] * 15
        })
        
        # XRP: 횡보 추세
        xrp_data = pd.DataFrame({
            'timestamp': [datetime.now() - timedelta(days=i) for i in range(14, -1, -1)],
            'open': [500 + (i % 3) * 10 for i in range(15)],
            'high': [510 + (i % 3) * 10 for i in range(15)],
            'low': [490 + (i % 3) * 10 for i in range(15)],
            'close': [500 + (i % 3) * 10 for i in range(15)],
            'volume': [100] * 15,
            'symbol': ['KRW-XRP'] * 15,
            'timeframe': ['1d'] * 15
        })
        
        # 모의 객체 설정
        self.mock_api_instance.get_markets.return_value = mock_markets
        
        def mock_get_ohlcv_data(symbol, timeframe, start_date, end_date):
            if symbol == 'KRW-BTC':
                return btc_data
            elif symbol == 'KRW-ETH':
                return eth_data
            elif symbol == 'KRW-XRP':
                return xrp_data
            return pd.DataFrame()
        
        self.mock_collector_instance.get_ohlcv_data.side_effect = mock_get_ohlcv_data
        self.mock_collector_instance.collect_historical_ohlcv.side_effect = mock_get_ohlcv_data
        
        # DataProcessor의 calculate_sma 메서드 모의 구현
        def mock_calculate_sma(data, window, column='close'):
            result = data.copy()
            
            if window == 5:
                # 5일 이동평균 계산
                sma = result[column].rolling(window=window).mean()
                result[f'SMA_{window}'] = sma
            elif window == 20:
                # 20일 이동평균은 테스트를 위해 직접 설정
                # BTC: 상승 추세를 위해 SMA_5보다 작은 값 설정
                if 'KRW-BTC' in result['symbol'].values:
                    result['SMA_20'] = result['close'] * 0.9  # SMA_5보다 작게 설정
                # ETH: 하락 추세를 위해 SMA_5보다 큰 값 설정
                elif 'KRW-ETH' in result['symbol'].values:
                    result['SMA_20'] = result['close'] * 1.1  # SMA_5보다 크게 설정
                # XRP: 횡보 추세를 위해 SMA_5와 비슷한 값 설정
                else:
                    result['SMA_20'] = result['close']
            else:
                # 다른 기간의 이동평균 계산
                sma = result[column].rolling(window=window).mean()
                result[f'SMA_{window}'] = sma
            
            # 디버깅 출력은 제거
            
            return result
            
        self.mock_processor_instance.calculate_sma.side_effect = mock_calculate_sma
        
        # 테스트 실행: 상승 추세 필터링
        result_bullish = self.screener.screen_by_trend(trend_type='bullish')
        

        
        # 검증
        self.assertIn('KRW-BTC', result_bullish)
        self.assertNotIn('KRW-ETH', result_bullish)
        
        # 테스트 실행: 하락 추세 필터링
        result_bearish = self.screener.screen_by_trend(trend_type='bearish')
        
        # 검증
        self.assertIn('KRW-ETH', result_bearish)
        self.assertNotIn('KRW-BTC', result_bearish)
    
    def test_04_1_4_combine_screening_results(self):
        """스크리닝 결과 조합 테스트"""
        print("\n=== 테스트 id 4_1_4: test_combine_screening_results ===")
        # 테스트 데이터
        result1 = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']
        result2 = ['KRW-BTC', 'KRW-ETH', 'KRW-ADA']
        result3 = ['KRW-BTC', 'KRW-DOGE']
        
        # 교집합 테스트
        intersection = self.screener.combine_screening_results([result1, result2, result3], method='intersection')
        self.assertEqual(len(intersection), 1)
        self.assertIn('KRW-BTC', intersection)
        
        # 합집합 테스트
        union = self.screener.combine_screening_results([result1, result2, result3], method='union')
        self.assertEqual(len(union), 5)
        self.assertIn('KRW-BTC', union)
        self.assertIn('KRW-ETH', union)
        self.assertIn('KRW-XRP', union)
        self.assertIn('KRW-ADA', union)
        self.assertIn('KRW-DOGE', union)
    
    def test_04_1_5_screen_coins(self):
        """코인 스크리닝 테스트"""
        
        # screen_by_volume 모의 구현
        self.screener.screen_by_volume = MagicMock(return_value=['KRW-BTC', 'KRW-ETH'])
        
        # screen_by_volatility 모의 구현
        self.screener.screen_by_volatility = MagicMock(return_value=['KRW-BTC', 'KRW-XRP'])
        
        # screen_by_trend 모의 구현
        self.screener.screen_by_trend = MagicMock(return_value=['KRW-BTC', 'KRW-DOGE'])
        
        # 티커 정보 모의 데이터
        mock_tickers = pd.DataFrame({
            'market': ['KRW-BTC'],
            'trade_price': [50000000],
            'acc_trade_price_24h': [5000000000]
        })
        self.mock_api_instance.get_tickers.return_value = mock_tickers
        
        # 마켓 정보 모의 데이터
        mock_markets = pd.DataFrame({
            'market': ['KRW-BTC'],
            'korean_name': ['비트코인']
        })
        self.mock_api_instance.get_markets.return_value = mock_markets
        
        # 테스트 실행
        criteria = [
            {
                'type': 'volume',
                'params': {
                    'min_volume': 1000000000
                }
            },
            {
                'type': 'volatility',
                'params': {
                    'min_volatility': 0.05,
                    'max_volatility': 0.2
                }
            },
            {
                'type': 'trend',
                'params': {
                    'trend_type': 'bullish'
                }
            }
        ]
        
        result = self.screener.screen_coins(criteria)
        
        # 검증
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['symbol'], 'KRW-BTC')
        self.assertEqual(result[0]['name'], '비트코인')
        self.assertEqual(result[0]['current_price'], 50000000)
        self.assertEqual(result[0]['volume_24h'], 5000000000)
        self.assertEqual(len(result[0]['matched_criteria']), 3)
        self.assertIn('volume', result[0]['matched_criteria'])
        self.assertIn('volatility', result[0]['matched_criteria'])
        self.assertIn('trend', result[0]['matched_criteria'])

if __name__ == '__main__':
    unittest.main()