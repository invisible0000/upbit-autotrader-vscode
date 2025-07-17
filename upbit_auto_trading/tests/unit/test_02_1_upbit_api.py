#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
업비트 API 클라이언트 단위 테스트
개발 순서: 2.1 업비트 REST API 기본 클라이언트 구현
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
    
    def test_get_markets(self):
        """마켓 코드 조회 테스트"""
        print("\n=== 테스트 id 2_1_1: test_get_markets ===")
        print("===== 마켓 코드 조회 테스트 시작 =====")
        
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"market": "KRW-BTC", "korean_name": "비트코인", "english_name": "Bitcoin"},
            {"market": "KRW-ETH", "korean_name": "이더리움", "english_name": "Ethereum"},
            {"market": "BTC-XRP", "korean_name": "리플", "english_name": "Ripple"}
        ]
        mock_response.raise_for_status.return_value = None
        self.mock_session_instance.request.return_value = mock_response
        
        print("모의 응답 설정 완료: KRW-BTC, KRW-ETH, BTC-XRP")
        
        # 함수 호출
        print("get_markets() 함수 호출 중...")
        result = self.api.get_markets()
        
        # 결과 출력
        print(f"반환된 데이터프레임 크기: {len(result)}")
        if not result.empty:
            print(f"포함된 마켓: {', '.join(result['market'].tolist())}")
        
        # 검증
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)  # KRW 마켓만 필터링되어야 함
        self.assertTrue("KRW-BTC" in result["market"].values)
        self.assertTrue("KRW-ETH" in result["market"].values)
        self.assertFalse("BTC-XRP" in result["market"].values)
        
        # API 호출 검증
        self.mock_session_instance.request.assert_called_once_with(
            method='GET',
            url='https://api.upbit.com/v1/market/all',
            params=None,
            json=None,
            headers={'Authorization': unittest.mock.ANY},
            timeout=(5, 30)
        )
        
        print("API 호출 검증 완료")
        print("===== 마켓 코드 조회 테스트 완료 =====\n")
    
    def test_get_candles_1m(self):
        """1분봉 조회 테스트"""
        print("\n=== 테스트 id 2_1_2: test_get_candles_1m ===")
        print("===== 1분봉 조회 테스트 시작 =====")
        
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
        self.mock_session_instance.request.return_value = mock_response
        
        print("모의 응답 설정 완료: 2개의 1분봉 데이터")
        
        # 함수 호출
        print("get_candles() 함수 호출 중...")
        result = self.api.get_candles(symbol="KRW-BTC", timeframe="1m", count=2)
        
        # 결과 출력
        print(f"반환된 데이터프레임 크기: {len(result)}")
        if not result.empty:
            print(f"첫 번째 캔들: 시가={result['open'].iloc[0]}, 고가={result['high'].iloc[0]}, 저가={result['low'].iloc[0]}, 종가={result['close'].iloc[0]}")
            print(f"두 번째 캔들: 시가={result['open'].iloc[1]}, 고가={result['high'].iloc[1]}, 저가={result['low'].iloc[1]}, 종가={result['close'].iloc[1]}")
        
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
        self.mock_session_instance.request.assert_called_once_with(
            method='GET',
            url='https://api.upbit.com/v1/candles/minutes/1',
            params={'market': 'KRW-BTC', 'count': 2},
            json=None,
            headers={'Authorization': unittest.mock.ANY},
            timeout=(5, 30)
        )
        
        print("API 호출 검증 완료")
        print("===== 1분봉 조회 테스트 완료 =====\n")
    
    def test_get_orderbook(self):
        """호가 데이터 조회 테스트"""
        print("\n=== 테스트 id 2_1_3: test_get_orderbook ===")
        print("===== 호가 데이터 조회 테스트 시작 =====")
        
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
        self.mock_session_instance.request.return_value = mock_response
        
        print("모의 응답 설정 완료: KRW-BTC 호가 데이터")
        
        # 함수 호출
        print("get_orderbook() 함수 호출 중...")
        result = self.api.get_orderbook(symbol="KRW-BTC")
        
        # 결과 출력
        print(f"반환된 호가 데이터: 마켓={result['market']}, 총 매도 수량={result['total_ask_size']}, 총 매수 수량={result['total_bid_size']}")
        print(f"호가 유닛 수: {len(result['orderbook_units'])}")
        print(f"첫 번째 호가: 매도가={result['orderbook_units'][0]['ask_price']}, 매수가={result['orderbook_units'][0]['bid_price']}")
        
        # 검증
        self.assertIsInstance(result, dict)
        self.assertEqual(result["market"], "KRW-BTC")
        self.assertIsInstance(result["timestamp"], datetime)
        self.assertEqual(result["total_ask_size"], 10.0)
        self.assertEqual(result["total_bid_size"], 12.0)
        self.assertEqual(len(result["orderbook_units"]), 2)
        
        # API 호출 검증
        self.mock_session_instance.request.assert_called_once_with(
            method='GET',
            url='https://api.upbit.com/v1/orderbook',
            params={'markets': 'KRW-BTC'},
            json=None,
            headers={'Authorization': unittest.mock.ANY},
            timeout=(5, 30)
        )
        
        print("API 호출 검증 완료")
        print("===== 호가 데이터 조회 테스트 완료 =====\n")
    
    def test_get_tickers(self):
        """티커 데이터 조회 테스트"""
        print("\n=== 테스트 id 2_1_4: test_get_tickers ===")
        print("===== 티커 데이터 조회 테스트 시작 =====")
        
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
        self.mock_session_instance.request.return_value = mock_response
        
        print("모의 응답 설정 완료: KRW-BTC, KRW-ETH 티커 데이터")
        
        # 함수 호출
        print("get_tickers() 함수 호출 중...")
        result = self.api.get_tickers(symbols=["KRW-BTC", "KRW-ETH"])
        
        # 결과 출력
        print(f"반환된 데이터프레임 크기: {len(result)}")
        if not result.empty:
            print(f"BTC 현재가: {result[result['market'] == 'KRW-BTC']['trade_price'].iloc[0]}, "
                  f"ETH 현재가: {result[result['market'] == 'KRW-ETH']['trade_price'].iloc[0]}")
            print(f"BTC 변동률: {result[result['market'] == 'KRW-BTC']['change_rate'].iloc[0]:.2%}, "
                  f"ETH 변동률: {result[result['market'] == 'KRW-ETH']['change_rate'].iloc[0]:.2%}")
        
        # 검증
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertTrue("KRW-BTC" in result["market"].values)
        self.assertTrue("KRW-ETH" in result["market"].values)
        
        # API 호출 검증
        self.mock_session_instance.request.assert_called_once_with(
            method='GET',
            url='https://api.upbit.com/v1/ticker',
            params={'markets': 'KRW-BTC,KRW-ETH'},
            json=None,
            headers={'Authorization': unittest.mock.ANY},
            timeout=(5, 30)
        )
        
        print("API 호출 검증 완료")
        print("===== 티커 데이터 조회 테스트 완료 =====\n")

    def test_check_rate_limit(self):
        """API 요청 제한 확인 테스트"""
        print("\n=== 테스트 id 2_1_5: test_check_rate_limit ===")
        print("===== API 요청 제한 확인 테스트 시작 =====")
        
        # 시간 패치
        with patch('upbit_auto_trading.data_layer.collectors.upbit_api.time.time') as mock_time, \
             patch('upbit_auto_trading.data_layer.collectors.upbit_api.time.sleep') as mock_sleep:
            
            # 현재 시간 설정
            mock_time.return_value = 1000.0
            print("현재 시간 설정: 1000.0")
            
            # 초기 상태 확인
            self.assertEqual(len(self.api.request_timestamps), 0)
            print("초기 타임스탬프 개수: 0")
            
            # 요청 제한 확인 호출
            print("첫 번째 _check_rate_limit() 호출...")
            self.api._check_rate_limit()
            
            # 타임스탬프 추가 확인
            self.assertEqual(len(self.api.request_timestamps), 1)
            self.assertEqual(self.api.request_timestamps[0], 1000.0)
            print(f"타임스탬프 추가 확인: {len(self.api.request_timestamps)}개, 값: {self.api.request_timestamps[0]}")
            
            # 초당 요청 제한 테스트 - 별도 테스트
            print("\n초당 요청 제한 테스트 시작...")
            # 새로운 API 인스턴스 생성
            api_sec_limit = UpbitAPI(access_key="test_access_key", secret_key="test_secret_key")
            api_sec_limit.session = self.mock_session_instance
            
            # 초당 요청 제한 수만큼 타임스탬프 추가
            api_sec_limit.request_timestamps = [1000.0] * api_sec_limit.RATE_LIMIT_PER_SEC
            print(f"초당 요청 제한 타임스탬프 설정: {len(api_sec_limit.request_timestamps)}개")
            
            # 요청 제한 확인 호출
            mock_sleep.reset_mock()
            api_sec_limit._check_rate_limit()
            
            # sleep 호출 확인
            self.assertEqual(mock_sleep.call_count, 1)
            mock_sleep.assert_called_once_with(1.0)
            print(f"초당 제한 sleep 호출 확인: {mock_sleep.call_count}회, 대기 시간: {mock_sleep.call_args[0][0]}초")
            
            # 분당 요청 제한 테스트 - 별도 테스트
            print("\n분당 요청 제한 테스트 시작...")
            # 새로운 API 인스턴스 생성
            api_min_limit = UpbitAPI(access_key="test_access_key", secret_key="test_secret_key")
            api_min_limit.session = self.mock_session_instance
            
            # 분당 요청 제한 수만큼 타임스탬프 추가 (60초 이내)
            api_min_limit.request_timestamps = [950.0 + i/100 for i in range(api_min_limit.RATE_LIMIT_PER_MIN)]
            print(f"분당 요청 제한 타임스탬프 설정: {len(api_min_limit.request_timestamps)}개")
            
            # 요청 제한 확인 호출
            mock_sleep.reset_mock()
            mock_time.return_value = 1000.0
            api_min_limit._check_rate_limit()
            
            # sleep 호출 확인 (가장 오래된 요청이 1분 지날 때까지 대기)
            self.assertEqual(mock_sleep.call_count, 1)
            self.assertGreater(mock_sleep.call_args[0][0], 0)
            print(f"분당 제한 sleep 호출 확인: {mock_sleep.call_count}회, 대기 시간: {mock_sleep.call_args[0][0]:.2f}초")
            
        print("===== API 요청 제한 확인 테스트 완료 =====\n")
    
    def test_create_session(self):
        """HTTP 세션 생성 테스트"""
        print("\n=== 테스트 id 2_1_6: test_create_session ===")
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
        print("\n=== 테스트 id 2_1_7: test_request_with_retry ===")
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
        print("\n=== 테스트 id 2_1_8: test_get_order ===")
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
        print("\n=== 테스트 id 2_1_9: test_get_market_day_candles ===")
        print("===== 일 캔들 조회 테스트 시작 =====")
        
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
        
        print("모의 응답 설정 완료: 2개의 일봉 데이터")
        
        # 함수 호출
        print("get_market_day_candles() 함수 호출 중...")
        result = self.api.get_market_day_candles(symbol="KRW-BTC", count=2)
        
        # 결과 출력
        print(f"반환된 데이터프레임 크기: {len(result)}")
        if not result.empty:
            print(f"첫 번째 캔들: 시가={result['open'].iloc[0]}, 고가={result['high'].iloc[0]}, 저가={result['low'].iloc[0]}, 종가={result['close'].iloc[0]}")
            print(f"두 번째 캔들: 시가={result['open'].iloc[1]}, 고가={result['high'].iloc[1]}, 저가={result['low'].iloc[1]}, 종가={result['close'].iloc[1]}")
        
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
        
        print("API 호출 검증 완료")
        print("===== 일 캔들 조회 테스트 완료 =====\n")
    
    def test_get_trades_ticks(self):
        """최근 체결 내역 조회 테스트"""
        print("\n=== 테스트 id 2_1_10: test_get_trades_ticks ===")
        print("===== 최근 체결 내역 조회 테스트 시작 =====")
        
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
        
        print("모의 응답 설정 완료: 2개의 체결 내역 데이터")
        
        # 함수 호출
        print("get_trades_ticks() 함수 호출 중...")
        result = self.api.get_trades_ticks(symbol="KRW-BTC", count=2)
        
        # 결과 출력
        print(f"반환된 데이터프레임 크기: {len(result)}")
        if not result.empty:
            print(f"첫 번째 체결: 가격={result['trade_price'].iloc[0]}, 수량={result['trade_volume'].iloc[0]}, 유형={result['ask_bid'].iloc[0]}")
            print(f"두 번째 체결: 가격={result['trade_price'].iloc[1]}, 수량={result['trade_volume'].iloc[1]}, 유형={result['ask_bid'].iloc[1]}")
        
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
        
        print("API 호출 검증 완료")
        print("===== 최근 체결 내역 조회 테스트 완료 =====\n")

if __name__ == '__main__':
    unittest.main()