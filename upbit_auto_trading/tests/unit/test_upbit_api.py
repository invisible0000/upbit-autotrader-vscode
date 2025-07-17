#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
업비트 API 클라이언트 단위 테스트
"""

import unittest
import pandas as pd
import time
import requests
from unittest.mock import patch, MagicMock, call
from datetime import datetime

from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI

class TestUpbitAPI(unittest.TestCase):
    """UpbitAPI 클래스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.api = UpbitAPI(access_key="test_access_key", secret_key="test_secret_key")
        # 세션 모킹을 위한 패치
        self.session_patcher = patch('upbit_auto_trading.data_layer.collectors.upbit_api.requests.Session')
        self.mock_session = self.session_patcher.start()
        self.mock_session_instance = self.mock_session.return_value
        self.api.session = self.mock_session_instance
    
    def tearDown(self):
        """테스트 정리"""
        self.session_patcher.stop()
    
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

    def test_check_rate_limit(self):
        """API 요청 제한 확인 테스트"""
        # 시간 패치
        with patch('upbit_auto_trading.data_layer.collectors.upbit_api.time.time') as mock_time, \
             patch('upbit_auto_trading.data_layer.collectors.upbit_api.time.sleep') as mock_sleep:
            
            # 현재 시간 설정
            mock_time.return_value = 1000.0
            
            # 초기 상태 확인
            self.assertEqual(len(self.api.request_timestamps), 0)
            
            # 요청 제한 확인 호출
            self.api._check_rate_limit()
            
            # 타임스탬프 추가 확인
            self.assertEqual(len(self.api.request_timestamps), 1)
            self.assertEqual(self.api.request_timestamps[0], 1000.0)
            
            # 초당 요청 제한 테스트
            # 초당 요청 제한 수만큼 타임스탬프 추가
            self.api.request_timestamps = [1000.0] * self.api.RATE_LIMIT_PER_SEC
            
            # 요청 제한 확인 호출
            self.api._check_rate_limit()
            
            # sleep 호출 확인
            mock_sleep.assert_called_once_with(1.0)
            
            # 분당 요청 제한 테스트
            mock_sleep.reset_mock()
            
            # 분당 요청 제한 수만큼 타임스탬프 추가 (60초 이내)
            self.api.request_timestamps = [950.0 + i for i in range(self.api.RATE_LIMIT_PER_MIN)]
            mock_time.return_value = 1000.0
            
            # 요청 제한 확인 호출
            self.api._check_rate_limit()
            
            # sleep 호출 확인 (가장 오래된 요청이 1분 지날 때까지 대기)
            mock_sleep.assert_called_once()
            self.assertGreater(mock_sleep.call_args[0][0], 0)
    
    def test_create_session(self):
        """HTTP 세션 생성 테스트"""
        # 세션 패치 해제
        self.session_patcher.stop()
        
        # 실제 세션 생성
        session = self.api._create_session()
        
        # 세션 타입 확인
        self.assertIsInstance(session, requests.Session)
        
        # 어댑터 확인
        self.assertTrue(any(isinstance(adapter, requests.adapters.HTTPAdapter) 
                          for adapter in session.adapters.values()))
        
        # 세션 패치 복구
        self.session_patcher = patch('upbit_auto_trading.data_layer.collectors.upbit_api.requests.Session')
        self.mock_session = self.session_patcher.start()
        self.mock_session_instance = self.mock_session.return_value
        self.api.session = self.mock_session_instance
    
    def test_request_with_retry(self):
        """API 요청 재시도 테스트"""
        # 세션 요청 모킹
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "success"}
        mock_response.raise_for_status.return_value = None
        
        # 첫 번째 요청은 429 오류, 두 번째 요청은 성공
        self.mock_session_instance.request.side_effect = [
            requests.exceptions.HTTPError("429 Too Many Requests"),
            mock_response
        ]
        
        # 429 오류 응답 모킹
        error_response = MagicMock()
        error_response.status_code = 429
        error_response.headers = {"Retry-After": "1"}
        error_response.text = "Too many requests"
        
        # 예외에 응답 추가
        http_error = requests.exceptions.HTTPError("429 Too Many Requests")
        http_error.response = error_response
        self.mock_session_instance.request.side_effect = [http_error, mock_response]
        
        # 시간 패치
        with patch('upbit_auto_trading.data_layer.collectors.upbit_api.time.sleep') as mock_sleep:
            # 함수 호출
            result = self.api._request('GET', '/test')
            
            # 검증
            self.assertEqual(result, {"result": "success"})
            
            # 재시도 확인
            self.assertEqual(self.mock_session_instance.request.call_count, 2)
            
            # sleep 호출 확인
            mock_sleep.assert_called_once_with(1)
    
    def test_get_order(self):
        """개별 주문 조회 테스트"""
        # 세션 요청 모킹
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "uuid": "test-uuid",
            "side": "bid",
            "ord_type": "limit",
            "price": "50000000.0",
            "state": "wait",
            "market": "KRW-BTC",
            "created_at": "2023-01-01T00:00:00+09:00",
            "volume": "0.01",
            "remaining_volume": "0.01",
            "reserved_fee": "250.0",
            "remaining_fee": "250.0",
            "paid_fee": "0.0",
            "locked": "500250.0",
            "executed_volume": "0.0",
            "trades_count": 0
        }
        mock_response.raise_for_status.return_value = None
        self.mock_session_instance.request.return_value = mock_response
        
        # 함수 호출
        result = self.api.get_order(uuid="test-uuid")
        
        # 검증
        self.assertIsInstance(result, dict)
        self.assertEqual(result["uuid"], "test-uuid")
        self.assertEqual(result["market"], "KRW-BTC")
        
        # API 호출 검증
        self.mock_session_instance.request.assert_called_once_with(
            method='GET',
            url='https://api.upbit.com/v1/order',
            params={'uuid': 'test-uuid'},
            json=None,
            headers={'Authorization': unittest.mock.ANY},
            timeout=(5, 30)
        )
    
    def test_get_market_day_candles(self):
        """일 캔들 조회 테스트"""
        # 세션 요청 모킹
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
                "candle_date_time_utc": "2023-01-02T00:00:00",
                "candle_date_time_kst": "2023-01-02T09:00:00",
                "opening_price": 50500000.0,
                "high_price": 52000000.0,
                "low_price": 50000000.0,
                "trade_price": 51500000.0,
                "timestamp": 1672617600000,
                "candle_acc_trade_price": 1200000000.0,
                "candle_acc_trade_volume": 24.0
            }
        ]
        mock_response.raise_for_status.return_value = None
        self.mock_session_instance.request.return_value = mock_response
        
        # 함수 호출
        result = self.api.get_market_day_candles(symbol="KRW-BTC", count=2)
        
        # 검증
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertEqual(result["symbol"].iloc[0], "KRW-BTC")
        self.assertEqual(result["timeframe"].iloc[0], "1d")
        self.assertEqual(result["open"].iloc[0], 50000000.0)
        self.assertEqual(result["high"].iloc[0], 51000000.0)
        self.assertEqual(result["low"].iloc[0], 49000000.0)
        self.assertEqual(result["close"].iloc[0], 50500000.0)
        self.assertEqual(result["volume"].iloc[0], 20.0)
        
        # API 호출 검증
        self.mock_session_instance.request.assert_called_once_with(
            method='GET',
            url='https://api.upbit.com/v1/candles/days',
            params={'market': 'KRW-BTC', 'count': 2},
            json=None,
            headers={'Authorization': unittest.mock.ANY},
            timeout=(5, 30)
        )
    
    def test_get_trades_ticks(self):
        """최근 체결 내역 조회 테스트"""
        # 세션 요청 모킹
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "market": "KRW-BTC",
                "trade_date_utc": "2023-01-01",
                "trade_time_utc": "00:00:00",
                "timestamp": 1672531200000,
                "trade_price": 50000000.0,
                "trade_volume": 0.01,
                "prev_closing_price": 49500000.0,
                "change_price": 500000.0,
                "ask_bid": "ASK",
                "sequential_id": 1672531200000000
            },
            {
                "market": "KRW-BTC",
                "trade_date_utc": "2023-01-01",
                "trade_time_utc": "00:01:00",
                "timestamp": 1672531260000,
                "trade_price": 50100000.0,
                "trade_volume": 0.02,
                "prev_closing_price": 49500000.0,
                "change_price": 600000.0,
                "ask_bid": "BID",
                "sequential_id": 1672531260000000
            }
        ]
        mock_response.raise_for_status.return_value = None
        self.mock_session_instance.request.return_value = mock_response
        
        # 함수 호출
        result = self.api.get_trades_ticks(symbol="KRW-BTC", count=2)
        
        # 검증
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertEqual(result["market"].iloc[0], "KRW-BTC")
        self.assertEqual(result["trade_price"].iloc[0], 50000000.0)
        self.assertEqual(result["trade_volume"].iloc[0], 0.01)
        
        # API 호출 검증
        self.mock_session_instance.request.assert_called_once_with(
            method='GET',
            url='https://api.upbit.com/v1/trades/ticks',
            params={'market': 'KRW-BTC', 'count': 2},
            json=None,
            headers={'Authorization': unittest.mock.ANY},
            timeout=(5, 30)
        )

if __name__ == '__main__':
    unittest.main()    @p
atch('upbit_auto_trading.data_layer.collectors.upbit_api.requests.request')
    def test_get_market_info(self, mock_request):
        """마켓 정보 조회 테스트"""
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
        result = self.api.get_market_info("KRW-BTC")
        
        # 검증
        self.assertIsInstance(result, dict)
        self.assertEqual(result["market"], "KRW-BTC")
        self.assertEqual(result["korean_name"], "비트코인")
        self.assertEqual(result["english_name"], "Bitcoin")
    
    @patch('upbit_auto_trading.data_layer.collectors.upbit_api.requests.request')
    def test_get_current_price(self, mock_request):
        """현재 시세 정보 조회 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "market": "KRW-BTC",
                "trade_date": "20230101",
                "trade_time": "090000",
                "trade_timestamp": 1672531200000,
                "trade_price": 50000000.0,
                "change": "RISE",
                "signed_change_rate": 0.0202,
                "acc_trade_volume_24h": 100.0,
                "timestamp": 1672531200000
            },
            {
                "market": "KRW-ETH",
                "trade_date": "20230101",
                "trade_time": "090000",
                "trade_timestamp": 1672531200000,
                "trade_price": 2000000.0,
                "change": "FALL",
                "signed_change_rate": -0.0102,
                "acc_trade_volume_24h": 500.0,
                "timestamp": 1672531200000
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # 함수 호출
        result = self.api.get_current_price(["KRW-BTC", "KRW-ETH"])
        
        # 검증
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 2)
        self.assertEqual(result["KRW-BTC"]["price"], 50000000.0)
        self.assertEqual(result["KRW-BTC"]["change"], "RISE")
        self.assertEqual(result["KRW-BTC"]["change_rate"], 0.0202)
        self.assertEqual(result["KRW-ETH"]["price"], 2000000.0)
        self.assertEqual(result["KRW-ETH"]["change"], "FALL")
        self.assertEqual(result["KRW-ETH"]["change_rate"], -0.0102)
    
    @patch('upbit_auto_trading.data_layer.collectors.upbit_api.requests.request')
    def test_get_historical_candles(self, mock_request):
        """과거 캔들 데이터 수집 테스트"""
        # Mock 응답 설정 - 첫 번째 요청
        mock_response1 = MagicMock()
        mock_response1.json.return_value = [
            {
                "market": "KRW-BTC",
                "candle_date_time_utc": "2023-01-02T00:00:00",
                "candle_date_time_kst": "2023-01-02T09:00:00",
                "opening_price": 50500000.0,
                "high_price": 52000000.0,
                "low_price": 50000000.0,
                "trade_price": 51500000.0,
                "timestamp": 1672617600000,
                "candle_acc_trade_volume": 24.0
            },
            {
                "market": "KRW-BTC",
                "candle_date_time_utc": "2023-01-01T00:00:00",
                "candle_date_time_kst": "2023-01-01T09:00:00",
                "opening_price": 50000000.0,
                "high_price": 51000000.0,
                "low_price": 49000000.0,
                "trade_price": 50500000.0,
                "timestamp": 1672531200000,
                "candle_acc_trade_volume": 20.0
            }
        ]
        
        # Mock 응답 설정 - 두 번째 요청 (더 이상 데이터 없음)
        mock_response2 = MagicMock()
        mock_response2.json.return_value = []
        
        mock_request.side_effect = [mock_response1, mock_response2]
        
        # 함수 호출
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 2)
        result = self.api.get_historical_candles("KRW-BTC", "1d", start_date, end_date)
        
        # 검증
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertEqual(result["symbol"].iloc[0], "KRW-BTC")
        self.assertEqual(result["timeframe"].iloc[0], "1d")
        
        # 시간 순서대로 정렬되었는지 확인
        self.assertTrue(result["timestamp"].is_monotonic_increasing)
        
        # 첫 번째 행이 1월 1일 데이터인지 확인
        self.assertEqual(pd.Timestamp(result["timestamp"].iloc[0]).date(), start_date.date())
        
        # 두 번째 행이 1월 2일 데이터인지 확인
        self.assertEqual(pd.Timestamp(result["timestamp"].iloc[1]).date(), end_date.date())
    
    @patch('upbit_auto_trading.data_layer.collectors.upbit_api.requests.request')
    def test_get_order_chance(self, mock_request):
        """주문 가능 정보 조회 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "bid_fee": "0.0005",
            "ask_fee": "0.0005",
            "market": {
                "id": "KRW-BTC",
                "name": "BTC/KRW",
                "order_types": ["limit"],
                "order_sides": ["ask", "bid"],
                "bid": {"currency": "KRW", "price_unit": 1000.0},
                "ask": {"currency": "BTC", "price_unit": 0.0001},
                "max_total": "1000000000.0",
                "state": "active"
            },
            "bid_account": {
                "currency": "KRW",
                "balance": "1000000.0",
                "locked": "0.0",
                "avg_buy_price": "0",
                "avg_buy_price_modified": False,
                "unit_currency": "KRW"
            },
            "ask_account": {
                "currency": "BTC",
                "balance": "1.0",
                "locked": "0.0",
                "avg_buy_price": "50000000",
                "avg_buy_price_modified": False,
                "unit_currency": "KRW"
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # 함수 호출
        result = self.api.get_order_chance("KRW-BTC")
        
        # 검증
        self.assertIsInstance(result, dict)
        self.assertEqual(result["bid_fee"], "0.0005")
        self.assertEqual(result["ask_fee"], "0.0005")
        self.assertEqual(result["market"]["id"], "KRW-BTC")
        self.assertEqual(result["bid_account"]["currency"], "KRW")
        self.assertEqual(result["ask_account"]["currency"], "BTC")
        
        # API 호출 검증
        mock_request.assert_called_once_with(
            method='GET',
            url='https://api.upbit.com/v1/orders/chance',
            params={'market': 'KRW-BTC'},
            json=None,
            headers={'Authorization': unittest.mock.ANY},
            timeout=(5, 30)
        )
    
    @patch('upbit_auto_trading.data_layer.collectors.upbit_api.requests.request')
    def test_get_deposit_addresses(self, mock_request):
        """입금 주소 목록 조회 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "currency": "BTC",
                "deposit_address": "3EusRYEEGHR1mT88rnvB3pEJcQ7CQjAr8X",
                "secondary_address": None
            },
            {
                "currency": "ETH",
                "deposit_address": "0x123f681646d4a755815f9cb19e1acc8565a0c2ac",
                "secondary_address": None
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # 함수 호출
        result = self.api.get_deposit_addresses()
        
        # 검증
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["currency"], "BTC")
        self.assertEqual(result[0]["deposit_address"], "3EusRYEEGHR1mT88rnvB3pEJcQ7CQjAr8X")
        self.assertEqual(result[1]["currency"], "ETH")
        self.assertEqual(result[1]["deposit_address"], "0x123f681646d4a755815f9cb19e1acc8565a0c2ac")
        
        # API 호출 검증
        mock_request.assert_called_once_with(
            method='GET',
            url='https://api.upbit.com/v1/deposits/coin_addresses',
            params=None,
            json=None,
            headers={'Authorization': unittest.mock.ANY},
            timeout=(5, 30)
        )
    
    @patch('upbit_auto_trading.data_layer.collectors.upbit_api.requests.request')
    def test_get_deposit_history(self, mock_request):
        """입금 내역 조회 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "type": "deposit",
                "uuid": "test-uuid-1",
                "currency": "BTC",
                "txid": "test-txid-1",
                "state": "done",
                "created_at": "2023-01-01T00:00:00+00:00",
                "done_at": "2023-01-01T00:10:00+00:00",
                "amount": "1.0",
                "fee": "0.0",
                "transaction_type": "default"
            },
            {
                "type": "deposit",
                "uuid": "test-uuid-2",
                "currency": "ETH",
                "txid": "test-txid-2",
                "state": "done",
                "created_at": "2023-01-02T00:00:00+00:00",
                "done_at": "2023-01-02T00:10:00+00:00",
                "amount": "10.0",
                "fee": "0.0",
                "transaction_type": "default"
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # 함수 호출
        result = self.api.get_deposit_history(currency="BTC", state="done", limit=10)
        
        # 검증
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["currency"], "BTC")
        self.assertEqual(result[0]["state"], "done")
        self.assertEqual(result[0]["amount"], "1.0")
        self.assertEqual(result[1]["currency"], "ETH")
        self.assertEqual(result[1]["state"], "done")
        self.assertEqual(result[1]["amount"], "10.0")
        
        # API 호출 검증
        mock_request.assert_called_once_with(
            method='GET',
            url='https://api.upbit.com/v1/deposits',
            params={'currency': 'BTC', 'state': 'done', 'limit': 10},
            json=None,
            headers={'Authorization': unittest.mock.ANY},
            timeout=(5, 30)
        )
    
    def test_retry_on_exception_decorator(self):
        """예외 발생 시 재시도 데코레이터 테스트"""
        # 테스트용 함수 정의
        mock_func = MagicMock()
        mock_func.side_effect = [
            requests.exceptions.RequestException("테스트 예외"),
            requests.exceptions.RequestException("테스트 예외"),
            "성공"
        ]
        
        # 데코레이터 적용
        from upbit_auto_trading.data_layer.collectors.upbit_api import retry_on_exception
        decorated_func = retry_on_exception(
            max_retries=3,
            retry_delay=0.01,
            exceptions=(requests.exceptions.RequestException,)
        )(mock_func)
        
        # 함수 호출
        with patch('upbit_auto_trading.data_layer.collectors.upbit_api.time.sleep') as mock_sleep:
            result = decorated_func()
        
        # 검증
        self.assertEqual(result, "성공")
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)  # 두 번의 재시도에 대한 대기
        
        # 최대 재시도 횟수 초과 테스트
        mock_func.reset_mock()
        mock_sleep.reset_mock()
        
        mock_func.side_effect = [
            requests.exceptions.RequestException("테스트 예외"),
            requests.exceptions.RequestException("테스트 예외"),
            requests.exceptions.RequestException("테스트 예외"),
            requests.exceptions.RequestException("테스트 예외")
        ]
        
        # 함수 호출 (예외 발생 예상)
        with patch('upbit_auto_trading.data_layer.collectors.upbit_api.time.sleep') as mock_sleep:
            with self.assertRaises(requests.exceptions.RequestException):
                decorated_func()
        
        # 검증
        self.assertEqual(mock_func.call_count, 4)  # 초기 호출 + 3번의 재시도
        self.assertEqual(mock_sleep.call_count, 3)  # 3번의 재시도에 대한 대기