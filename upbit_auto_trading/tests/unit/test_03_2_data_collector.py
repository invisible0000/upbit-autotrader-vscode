#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
데이터 수집기 단위 테스트
개발 순서: 3.2 데이터 수집기 구현
"""

import unittest
import pandas as pd
import json
import os
import tempfile
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta

from upbit_auto_trading.data_layer.collectors.data_collector import DataCollector

class TestDataCollector(unittest.TestCase):
    """DataCollector 클래스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # 데이터베이스 관리자 모킹
        self.db_manager_patcher = patch('upbit_auto_trading.data_layer.collectors.data_collector.get_database_manager')
        self.mock_db_manager = self.db_manager_patcher.start()
        
        # 엔진 모킹
        self.mock_engine = MagicMock()
        self.mock_db_manager.return_value.get_engine.return_value = self.mock_engine
        
        # 연결 모킹
        self.mock_conn = MagicMock()
        self.mock_engine.connect.return_value.__enter__.return_value = self.mock_conn
        
        # 업비트 API 모킹
        self.api_patcher = patch('upbit_auto_trading.data_layer.collectors.data_collector.UpbitAPI')
        self.mock_api_class = self.api_patcher.start()
        self.mock_api = self.mock_api_class.return_value
        
        # 데이터 수집기 생성 (테이블 생성 메서드 패치)
        with patch.object(DataCollector, '_ensure_tables'):
            self.collector = DataCollector()
    
    def tearDown(self):
        """테스트 정리"""
        # 패치 중지
        self.db_manager_patcher.stop()
        self.api_patcher.stop()
        
        # 임시 디렉토리 삭제
        self.temp_dir.cleanup()
    
    def test_ensure_tables(self):
        """테이블 생성 테스트"""
        print("\n=== 테스트 id 3_2_1: test_ensure_tables ===")
        print("테이블 생성 메서드 호출 중...")
        # 메서드 호출
        self.collector._ensure_tables()
        print(f"쿼리 실행 횟수: {self.mock_conn.execute.call_count} (4회여야 함)")
        print(f"commit 호출 여부: {self.mock_conn.commit.called} (commit이 반드시 호출되어야 함)")
        # 쿼리 실행 확인
        self.assertEqual(self.mock_conn.execute.call_count, 4)
        self.mock_conn.commit.assert_called_once()
        print("테스트 id 3_2_1: test_ensure_tables [성공]")
    
    def test_collect_ohlcv(self):
        """OHLCV 데이터 수집 테스트"""
        print("\n=== 테스트 id 3_2_2: test_collect_ohlcv ===")
        print("OHLCV 데이터 수집 테스트 시작!")
        # Mock 데이터 설정
        mock_df = pd.DataFrame({
            'timestamp': [datetime(2023, 1, 1), datetime(2023, 1, 2)],
            'open': [50000000.0, 50500000.0],
            'high': [51000000.0, 52000000.0],
            'low': [49000000.0, 50000000.0],
            'close': [50500000.0, 51500000.0],
            'volume': [20.0, 24.0],
            'symbol': ['KRW-BTC', 'KRW-BTC'],
            'timeframe': ['1d', '1d']
        })

        print("API에서 받은 데이터:")
        print(mock_df)

        # API 응답 모킹
        self.mock_api.get_candles.return_value = mock_df

        # 메서드 호출
        result = self.collector.collect_ohlcv('KRW-BTC', '1d', 2)
        print("collect_ohlcv 함수 반환값:")
        print(result)

        # 검증
        print(f"반환값 타입: {type(result)} (pd.DataFrame이어야 함)")
        print(f"데이터 개수: {len(result)} (2개여야 함)")
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)

        # API 호출 확인
        print("API get_candles 호출 여부:", self.mock_api.get_candles.called)
        self.mock_api.get_candles.assert_called_once_with('KRW-BTC', '1d', 2)

        # 데이터 저장 확인
        print("DB execute 호출 여부:", self.mock_conn.execute.called)
        print("DB commit 호출 여부:", self.mock_conn.commit.called)
        self.mock_conn.execute.assert_called()
        self.mock_conn.commit.assert_called()
        print("테스트 id 3_2_2: test_collect_ohlcv [성공]")
    
    def test_collect_orderbook(self):
        """호가 데이터 수집 테스트"""
        print("\n=== 테스트 id 3_2_3: test_collect_orderbook ===")
        print("호가 데이터 수집 테스트 시작!")
        # Mock 데이터 설정
        mock_orderbook = {
            'market': 'KRW-BTC',
            'timestamp': datetime(2023, 1, 1),
            'total_ask_size': 10.0,
            'total_bid_size': 12.0,
            'orderbook_units': [
                {
                    'ask_price': 51000000.0,
                    'bid_price': 50000000.0,
                    'ask_size': 1.0,
                    'bid_size': 1.2
                }
            ]
        }

        print("API에서 받은 데이터:")
        print(mock_orderbook)

        # API 응답 모킹
        self.mock_api.get_orderbook.return_value = mock_orderbook

        # 메서드 호출
        result = self.collector.collect_orderbook('KRW-BTC')
        print("collect_orderbook 함수 반환값:")
        print(result)

        # 검증
        print(f"반환값 타입: {type(result)} (dict이어야 함)")
        print(f"market 값: {result['market']} (KRW-BTC여야 함)")
        self.assertIsInstance(result, dict)
        self.assertEqual(result['market'], 'KRW-BTC')

        # API 호출 확인
        print("API get_orderbook 호출 여부:", self.mock_api.get_orderbook.called)
        self.mock_api.get_orderbook.assert_called_once_with('KRW-BTC')

        # 데이터 저장 확인
        print("DB execute 호출 여부:", self.mock_conn.execute.called)
        print("DB commit 호출 여부:", self.mock_conn.commit.called)
        self.mock_conn.execute.assert_called()
        self.mock_conn.commit.assert_called()
        print("테스트 id 3_2_3: test_collect_orderbook [성공]")
    
    def test_get_ohlcv_data(self):
        """OHLCV 데이터 조회 테스트"""
        print("\n=== 테스트 id 3_2_4: test_get_ohlcv_data ===")
        print("OHLCV 데이터 조회 테스트 시작!")
        # Mock 데이터 설정
        mock_rows = [
            ('KRW-BTC', datetime(2023, 1, 1), 50000000.0, 51000000.0, 49000000.0, 50500000.0, 20.0, '1d'),
            ('KRW-BTC', datetime(2023, 1, 2), 50500000.0, 52000000.0, 50000000.0, 51500000.0, 24.0, '1d')
        ]

        print("쿼리 결과로 반환될 mock 데이터:")
        for row in mock_rows:
            print(row)

        # 쿼리 결과 모킹
        mock_result = MagicMock()
        mock_result.fetchall.return_value = mock_rows
        self.mock_conn.execute.return_value = mock_result

        # 메서드 호출
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 2)
        result = self.collector.get_ohlcv_data('KRW-BTC', '1d', start_date, end_date)
        print("get_ohlcv_data 함수 반환값:")
        print(result)

        # 검증
        print(f"반환값 타입: {type(result)} (pd.DataFrame이어야 함)")
        print(f"데이터 개수: {len(result)} (2개여야 함)")
        print(f"첫 번째 symbol 값: {result['symbol'].iloc[0]}")
        print(f"첫 번째 timeframe 값: {result['timeframe'].iloc[0]}")
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertEqual(result['symbol'].iloc[0], 'KRW-BTC')
        self.assertEqual(result['timeframe'].iloc[0], '1d')

        # 쿼리 실행 확인
        print("DB execute 호출 여부:", self.mock_conn.execute.called)
        self.mock_conn.execute.assert_called_once()
        print("테스트 id 3_2_4: test_get_ohlcv_data [성공]")
    
    def test_get_orderbook_data(self):
        """호가 데이터 조회 테스트"""
        print("\n=== 테스트 id 3_2_5: test_get_orderbook_data ===")
        print("호가 데이터 조회 테스트 시작!")
        # Mock 데이터 설정
        mock_orderbook_str = json.dumps({
            'market': 'KRW-BTC',
            'timestamp': '2023-01-01T00:00:00',  # ISO 형식의 문자열로 변경
            'total_ask_size': 10.0,
            'total_bid_size': 12.0,
            'orderbook_units': [
                {
                    'ask_price': 51000000.0,
                    'bid_price': 50000000.0,
                    'ask_size': 1.0,
                    'bid_size': 1.2
                }
            ]
        })

        print("쿼리 결과로 반환될 mock 데이터:")
        mock_rows = [
            ('KRW-BTC', datetime(2023, 1, 1), mock_orderbook_str)
        ]
        for row in mock_rows:
            print(row)

        mock_result = MagicMock()
        mock_result.fetchall.return_value = mock_rows
        self.mock_conn.execute.return_value = mock_result

        # 메서드 호출
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 2)
        result = self.collector.get_orderbook_data('KRW-BTC', start_date, end_date)
        print("get_orderbook_data 함수 반환값:")
        print(result)

        # 검증
        print(f"반환값 타입: {type(result)} (list이어야 함)")
        print(f"데이터 개수: {len(result)} (1개여야 함)")
        print(f"첫 번째 market 값: {result[0]['market']}")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['market'], 'KRW-BTC')

        # 쿼리 실행 확인
        print("DB execute 호출 여부:", self.mock_conn.execute.called)
        self.mock_conn.execute.assert_called_once()
        print("테스트 id 3_2_5: test_get_orderbook_data [성공]")
    
    def test_collect_historical_ohlcv_new_data(self):
        """과거 OHLCV 데이터 수집 테스트 (새 데이터)"""
        print("\n=== 테스트 id 3_2_6: test_collect_historical_ohlcv_new_data ===")
        print("과거 OHLCV 데이터 수집 테스트 (새 데이터) 시작!")
        # 기존 데이터 없음 모킹
        self.collector.get_ohlcv_data = MagicMock(return_value=pd.DataFrame())

        # Mock 데이터 설정
        mock_df = pd.DataFrame({
            'timestamp': [datetime(2023, 1, 1), datetime(2023, 1, 2)],
            'open': [50000000.0, 50500000.0],
            'high': [51000000.0, 52000000.0],
            'low': [49000000.0, 50000000.0],
            'close': [50500000.0, 51500000.0],
            'volume': [20.0, 24.0],
            'symbol': ['KRW-BTC', 'KRW-BTC'],
            'timeframe': ['1d', '1d']
        })

        print("API에서 받은 데이터:")
        print(mock_df)

        # API 응답 모킹
        self.mock_api.get_historical_candles.return_value = mock_df

        # 메서드 호출
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 2)
        result = self.collector.collect_historical_ohlcv('KRW-BTC', '1d', start_date, end_date)
        print("collect_historical_ohlcv 함수 반환값:")
        print(result)

        # 검증
        print(f"반환값 타입: {type(result)} (pd.DataFrame이어야 함)")
        print(f"데이터 개수: {len(result)} (2개여야 함)")
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)

        # API 호출 확인
        print("API get_historical_candles 호출 여부:", self.mock_api.get_historical_candles.called)
        self.mock_api.get_historical_candles.assert_called_once_with('KRW-BTC', '1d', start_date, end_date)
        print("테스트 id 3_2_6: test_collect_historical_ohlcv_new_data [성공]")
    
    def test_collect_historical_ohlcv_existing_data(self):
        """과거 OHLCV 데이터 수집 테스트 (기존 데이터 있음)"""
        print("\n=== 테스트 id 3_2_7: test_collect_historical_ohlcv_existing_data ===")
        print("과거 OHLCV 데이터 수집 테스트 (기존 데이터 있음) 시작!")
        # 기존 데이터 모킹
        existing_df = pd.DataFrame({
            'timestamp': [datetime(2023, 1, 1)],
            'open': [50000000.0],
            'high': [51000000.0],
            'low': [49000000.0],
            'close': [50500000.0],
            'volume': [20.0],
            'symbol': ['KRW-BTC'],
            'timeframe': ['1d']
        })
        self.collector.get_ohlcv_data = MagicMock(return_value=existing_df)

        print("기존 데이터:")
        print(existing_df)

        # 추가 데이터 모킹
        new_df = pd.DataFrame({
            'timestamp': [datetime(2023, 1, 2)],
            'open': [50500000.0],
            'high': [52000000.0],
            'low': [50000000.0],
            'close': [51500000.0],
            'volume': [24.0],
            'symbol': ['KRW-BTC'],
            'timeframe': ['1d']
        })
        self.mock_api.get_historical_candles.return_value = new_df

        print("추가 데이터:")
        print(new_df)

        # 메서드 호출
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 2)
        result = self.collector.collect_historical_ohlcv('KRW-BTC', '1d', start_date, end_date)
        print("collect_historical_ohlcv 함수 반환값:")
        print(result)

        # 검증
        print(f"반환값 타입: {type(result)} (pd.DataFrame이어야 함)")
        print(f"데이터 개수: {len(result)} (2개여야 함)")
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)  # 기존 데이터 1개 + 새 데이터 1개

        # API 호출 확인 (기존 데이터의 마지막 날짜 이후부터 end_date까지)
        print("API get_historical_candles 호출 여부:", self.mock_api.get_historical_candles.called)
        self.mock_api.get_historical_candles.assert_called_once()
        print("테스트 id 3_2_7: test_collect_historical_ohlcv_existing_data [성공]")
    
    def test_cleanup_old_data(self):
        """오래된 데이터 정리 테스트"""
        print("\n=== 테스트 id 3_2_8: test_cleanup_old_data ===")
        # 쿼리 결과 모킹
        mock_ohlcv_result = MagicMock()
        mock_ohlcv_result.rowcount = 10

        mock_orderbook_result = MagicMock()
        mock_orderbook_result.rowcount = 5

        self.mock_conn.execute.side_effect = [mock_ohlcv_result, mock_orderbook_result]

        # 메서드 호출
        result = self.collector.cleanup_old_data(days_to_keep=30)
        print(f"삭제된 OHLCV 데이터 개수: {result['ohlcv_deleted']} (10개여야 함)")
        print(f"삭제된 Orderbook 데이터 개수: {result['orderbook_deleted']} (5개여야 함)")

        # 검증
        self.assertIsInstance(result, dict)
        self.assertEqual(result['ohlcv_deleted'], 10)
        self.assertEqual(result['orderbook_deleted'], 5)

        # 쿼리 실행 확인
        print(f"쿼리 실행 횟수: {self.mock_conn.execute.call_count} (2회여야 함)")
        print(f"commit 호출 여부: {self.mock_conn.commit.called} (commit이 반드시 호출되어야 함)")
        self.assertEqual(self.mock_conn.execute.call_count, 2)
        self.mock_conn.commit.assert_called_once()
        print("테스트 id 3_2_8: test_cleanup_old_data [성공]")
    
    @patch('upbit_auto_trading.data_layer.collectors.data_collector.threading.Thread')
    def test_start_ohlcv_collection(self, mock_thread):
        """OHLCV 데이터 수집 작업 시작 테스트"""
        print("\n=== 테스트 id 3_2_9: test_start_ohlcv_collection ===")
        # 스레드 모킹
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        # 메서드 호출
        result = self.collector.start_ohlcv_collection('KRW-BTC', '1d', 60)
        print(f"start_ohlcv_collection 반환값: {result}")

        # 검증
        self.assertTrue(result)

        # 스레드 생성 확인
        print(f"스레드 생성 여부: {mock_thread.called}")
        print(f"스레드 start 호출 여부: {mock_thread_instance.start.called}")
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

        # 작업 정보 저장 확인
        task_key = 'ohlcv_KRW-BTC_1d'
        print(f"작업 정보 저장 여부: {task_key in self.collector._collection_tasks}")
        if task_key in self.collector._collection_tasks:
            print(f"작업 타입: {self.collector._collection_tasks[task_key]['type']}")
            print(f"심볼: {self.collector._collection_tasks[task_key]['symbol']}")
            print(f"timeframe: {self.collector._collection_tasks[task_key]['timeframe']}")
            print(f"interval: {self.collector._collection_tasks[task_key]['interval']}")
        self.assertIn(task_key, self.collector._collection_tasks)
        self.assertEqual(self.collector._collection_tasks[task_key]['type'], 'ohlcv')
        self.assertEqual(self.collector._collection_tasks[task_key]['symbol'], 'KRW-BTC')
        self.assertEqual(self.collector._collection_tasks[task_key]['timeframe'], '1d')
        self.assertEqual(self.collector._collection_tasks[task_key]['interval'], 60)
        print("테스트 id 3_2_9: test_start_ohlcv_collection [성공]")
    
    @patch('upbit_auto_trading.data_layer.collectors.data_collector.threading.Thread')
    def test_start_orderbook_collection(self, mock_thread):
        """호가 데이터 수집 작업 시작 테스트"""
        print("\n=== 테스트 id 3_2_10: test_start_orderbook_collection ===")
        print("스레드 모킹 및 데이터 수집 작업 시작 메서드 호출 중...")
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        result = self.collector.start_orderbook_collection('KRW-BTC', 1)
        print(f"start_orderbook_collection 반환값: {result}")
        print(f"스레드 생성 여부: {mock_thread.called}")
        print(f"스레드 start 호출 여부: {mock_thread_instance.start.called}")
        task_key = 'orderbook_KRW-BTC'
        print(f"작업 정보 저장 여부: {task_key in self.collector._collection_tasks}")
        if task_key in self.collector._collection_tasks:
            print(f"작업 타입: {self.collector._collection_tasks[task_key]['type']}")
            print(f"심볼: {self.collector._collection_tasks[task_key]['symbol']}")
            print(f"interval: {self.collector._collection_tasks[task_key]['interval']}")
        self.assertTrue(result)
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        self.assertIn(task_key, self.collector._collection_tasks)
        self.assertEqual(self.collector._collection_tasks[task_key]['type'], 'orderbook')
        self.assertEqual(self.collector._collection_tasks[task_key]['symbol'], 'KRW-BTC')
        self.assertEqual(self.collector._collection_tasks[task_key]['interval'], 1)
    
    def test_stop_collection(self):
        """데이터 수집 작업 중지 테스트"""
        print("\n=== 테스트 id 3_2_11: test_stop_collection ===")
        # 작업 정보 설정
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True

        task_key = 'ohlcv_KRW-BTC_1d'
        self.collector._collection_tasks[task_key] = {
            'thread': mock_thread,
            'type': 'ohlcv',
            'symbol': 'KRW-BTC',
            'timeframe': '1d',
            'interval': 60,
            'start_time': datetime.now()
        }

        # 메서드 호출
        result = self.collector.stop_collection(task_key)
        print(f"stop_collection 반환값: {result}")

        # 검증
        self.assertTrue(result)

        # 스레드 종료 확인
        print(f"스레드 join 호출 여부: {mock_thread.join.called}")
        mock_thread.join.assert_called_once()

        # 작업 정보 삭제 확인
        print(f"작업 정보 삭제 여부: {task_key not in self.collector._collection_tasks}")
        self.assertNotIn(task_key, self.collector._collection_tasks)
        print("테스트 id 3_2_11: test_stop_collection [성공]")
    
    def test_stop_all_collections(self):
        """모든 데이터 수집 작업 중지 테스트"""
        print("\n=== 테스트 id 3_2_12: test_stop_all_collections ===")
        # 작업 정보 설정
        mock_thread1 = MagicMock()
        mock_thread1.is_alive.return_value = True

        mock_thread2 = MagicMock()
        mock_thread2.is_alive.return_value = True

        self.collector._collection_tasks = {
            'ohlcv_KRW-BTC_1d': {
                'thread': mock_thread1,
                'type': 'ohlcv',
                'symbol': 'KRW-BTC',
                'timeframe': '1d',
                'interval': 60,
                'start_time': datetime.now()
            },
            'orderbook_KRW-BTC': {
                'thread': mock_thread2,
                'type': 'orderbook',
                'symbol': 'KRW-BTC',
                'interval': 1,
                'start_time': datetime.now()
            }
        }

        # 메서드 호출
        result = self.collector.stop_all_collections()
        print(f"stop_all_collections 반환값: {result}")

        # 검증
        self.assertTrue(result)

        # 스레드 종료 확인
        print(f"스레드1 join 호출 여부: {mock_thread1.join.called}")
        print(f"스레드2 join 호출 여부: {mock_thread2.join.called}")
        mock_thread1.join.assert_called_once()
        mock_thread2.join.assert_called_once()

        # 작업 정보 삭제 확인
        print(f"작업 정보 삭제 여부: {len(self.collector._collection_tasks) == 0}")
        self.assertEqual(len(self.collector._collection_tasks), 0)
        print("테스트 id 3_2_12: test_stop_all_collections [성공]")
    
    def test_get_collection_status(self):
        """데이터 수집 작업 상태 조회 테스트"""
        print("\n=== 테스트 id 3_2_13: test_get_collection_status ===")
        # 작업 정보 설정
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True

        start_time = datetime.now() - timedelta(hours=1)
        task_key = 'ohlcv_KRW-BTC_1d'
        self.collector._collection_tasks[task_key] = {
            'thread': mock_thread,
            'type': 'ohlcv',
            'symbol': 'KRW-BTC',
            'timeframe': '1d',
            'interval': 60,
            'start_time': start_time
        }

        # 메서드 호출
        result = self.collector.get_collection_status()
        print(f"get_collection_status 반환값: {result}")

        # 검증
        self.assertIsInstance(result, dict)
        self.assertIn(task_key, result)
        self.assertEqual(result[task_key]['type'], 'ohlcv')
        self.assertEqual(result[task_key]['symbol'], 'KRW-BTC')
        self.assertEqual(result[task_key]['timeframe'], '1d')
        self.assertEqual(result[task_key]['interval'], 60)
        self.assertTrue(result[task_key]['is_alive'])
        self.assertGreaterEqual(result[task_key]['running_time'], 3600)  # 1시간 이상 실행 중
        print("테스트 id 3_2_13: test_get_collection_status [성공]")

if __name__ == '__main__':
    unittest.main()