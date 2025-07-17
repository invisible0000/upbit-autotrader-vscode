#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
업비트 API 클라이언트 단위 테스트
"""

import unittest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime

from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI

class TestUpbitAPI(unittest.TestCase):
    """UpbitAPI 클래스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.api = UpbitAPI(access_key="test_access_key", secret_key="test_secret_key")
    
    @patch('upbit_auto_trading.data_layer.collectors.upbit_api.requests.request')
    def test_get_markets(self, mock_request):
        """마켓 코드 조회 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"market": "KRW-BTC", "korean_name": "비트코인", "english_name": "Bitcoin"},
            {"market": "KRW-ETH", "korean_name": "이더리움", "english_name": "Ethereum"},
            {"market": "BTC-XRP", "korean_name": "리플", "english_name": "Ripple"}
        ]
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # 함수 호출
        result = self.api.get_markets()
        
        # 검증
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)  # KRW 마켓만 필터링되어야 함
        self.assertTrue("KRW-BTC" in result["market"].values)
        self.assertTrue("KRW-ETH" in result["market"].values)
        self.assertFalse("BTC-XRP" in result["market"].values)
        
        # API 호출 검증
        mock_request.assert_called_once_with(
            method='GET',
            url='https://api.upbit.com/v1/market/all',
            params=None,
            json=None,
            headers={'Authorization': unittest.mock.ANY}
        )
    
    @patch('upbit_auto_trading.data_layer.collectors.upbit_api.requests.request')
    def test_get_candles_1m(self, mock_request):
        """1분봉 조회 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "market": "KRW-BTC",
                "candle_date_time_utc": "2023-01-01T00:00:00",
                "candle_date_time_kst": "2023-01-01T09:00:00",
                "opening_price": 50000000.0,
                "high_price": 51000000.0,
                "low_price": 49000000.0,
                "trade_price": 50500000.0,
                "timestamp": 1672531200000,
                "candle_acc_trade_price": 1000000000.0,
                "candle_acc_trade_volume": 20.0
            },
            {
                "market": "KRW-BTC",
                "candle_date_time_utc": "2023-01-01T00:01:00",
                "candle_date_time_kst": "2023-01-01T09:01:00",
                "opening_price": 50500000.0,
                "high_price": 51500000.0,
                "low_price": 50000000.0,
                "trade_price": 51000000.0,
                "timestamp": 1672531260000,
                "candle_acc_trade_price": 1100000000.0,
                "candle_acc_trade_volume": 22.0
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # 함수 호출
        result = self.api.get_candles(symbol="KRW-BTC", timeframe="1m", count=2)
        
        # 검증
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertEqual(result["symbol"].iloc[0], "KRW-BTC")
        self.assertEqual(result["timeframe"].iloc[0], "1m")
        self.assertEqual(result["open"].iloc[0], 50000000.0)
        self.assertEqual(result["high"].iloc[0], 51000000.0)
        self.assertEqual(result["low"].iloc[0], 49000000.0)
        self.assertEqual(result["close"].iloc[0], 50500000.0)
        self.assertEqual(result["volume"].iloc[0], 20.0)
        
        # API 호출 검증
        mock_request.assert_called_once_with(
            method='GET',
            url='https://api.upbit.com/v1/candles/minutes/1',
            params={'market': 'KRW-BTC', 'count': 2},
            json=None,
            headers={'Authorization': unittest.mock.ANY}
        )
    
    @patch('upbit_auto_trading.data_layer.collectors.upbit_api.requests.request')
    def test_get_orderbook(self, mock_request):
        """호가 데이터 조회 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "market": "KRW-BTC",
                "timestamp": 1672531200000,
                "total_ask_size": 10.0,
                "total_bid_size": 12.0,
                "orderbook_units": [
                    {
                        "ask_price": 51000000.0,
                        "bid_price": 50000000.0,
                        "ask_size": 1.0,
                        "bid_size": 1.2
                    },
                    {
                        "ask_price": 52000000.0,
                        "bid_price": 49000000.0,
                        "ask_size": 0.5,
                        "bid_size": 0.7
                    }
                ]
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # 함수 호출
        result = self.api.get_orderbook(symbol="KRW-BTC")
        
        # 검증
        self.assertIsInstance(result, dict)
        self.assertEqual(result["market"], "KRW-BTC")
        self.assertIsInstance(result["timestamp"], datetime)
        self.assertEqual(result["total_ask_size"], 10.0)
        self.assertEqual(result["total_bid_size"], 12.0)
        self.assertEqual(len(result["orderbook_units"]), 2)
        
        # API 호출 검증
        mock_request.assert_called_once_with(
            method='GET',
            url='https://api.upbit.com/v1/orderbook',
            params={'markets': 'KRW-BTC'},
            json=None,
            headers={'Authorization': unittest.mock.ANY}
        )
    
    @patch('upbit_auto_trading.data_layer.collectors.upbit_api.requests.request')
    def test_get_tickers(self, mock_request):
        """티커 데이터 조회 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "market": "KRW-BTC",
                "trade_date": "20230101",
                "trade_time": "090000",
                "trade_timestamp": 1672531200000,
                "opening_price": 50000000.0,
                "high_price": 51000000.0,
                "low_price": 49000000.0,
                "trade_price": 50500000.0,
                "prev_closing_price": 49500000.0,
                "change": "RISE",
                "change_price": 1000000.0,
                "change_rate": 0.0202,
                "signed_change_price": 1000000.0,
                "signed_change_rate": 0.0202,
                "trade_volume": 0.01,
                "acc_trade_price": 1000000000.0,
                "acc_trade_price_24h": 5000000000.0,
                "acc_trade_volume": 20.0,
                "acc_trade_volume_24h": 100.0,
                "timestamp": 1672531200000
            },
            {
                "market": "KRW-ETH",
                "trade_date": "20230101",
                "trade_time": "090000",
                "trade_timestamp": 1672531200000,
                "opening_price": 2000000.0,
                "high_price": 2100000.0,
                "low_price": 1900000.0,
                "trade_price": 2050000.0,
                "prev_closing_price": 1950000.0,
                "change": "RISE",
                "change_price": 100000.0,
                "change_rate": 0.0513,
                "signed_change_price": 100000.0,
                "signed_change_rate": 0.0513,
                "trade_volume": 0.1,
                "acc_trade_price": 500000000.0,
                "acc_trade_price_24h": 2000000000.0,
                "acc_trade_volume": 250.0,
                "acc_trade_volume_24h": 1000.0,
                "timestamp": 1672531200000
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # 함수 호출
        result = self.api.get_tickers(symbols=["KRW-BTC", "KRW-ETH"])
        
        # 검증
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertTrue("KRW-BTC" in result["market"].values)
        self.assertTrue("KRW-ETH" in result["market"].values)
        
        # API 호출 검증
        mock_request.assert_called_once_with(
            method='GET',
            url='https://api.upbit.com/v1/ticker',
            params={'markets': 'KRW-BTC,KRW-ETH'},
            json=None,
            headers={'Authorization': unittest.mock.ANY}
        )

if __name__ == '__main__':
    unittest.main()