#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
스크리너 결과 테스트
개발 순서: 4.2 스크리닝 결과 처리 및 저장 기능 구현

ScreenerResult 클래스의 기능을 테스트합니다.
"""

import unittest
import os
import pandas as pd
import json
import tempfile
import warnings
import sqlite3
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text, event
from sqlalchemy.pool import Pool

from upbit_auto_trading.business_logic.screener.screener_result import ScreenerResult

# SQLite datetime 어댑터 경고 무시
warnings.filterwarnings("ignore", category=DeprecationWarning, 
                       message="The default datetime adapter is deprecated")

# ResourceWarning 무시
warnings.filterwarnings("ignore", category=ResourceWarning, 
                       message="unclosed database")

class TestScreenerResult(unittest.TestCase):
    """ScreenerResult 클래스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        print("\n===== 테스트 시작: {} =====".format(self._testMethodName))
        
        # 인메모리 SQLite 데이터베이스 생성
        self.engine = create_engine('sqlite:///:memory:')
        
        # 데이터베이스 연결이 닫히도록 이벤트 리스너 추가
        @event.listens_for(self.engine, "connect")
        def do_connect(dbapi_connection, connection_record):
            # SQLite 연결에 대한 외래 키 제약 활성화
            if isinstance(dbapi_connection, sqlite3.Connection):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        
        # 데이터베이스 매니저 모의 객체 생성
        self.db_manager_patcher = patch('upbit_auto_trading.business_logic.screener.screener_result.get_database_manager')
        self.mock_db_manager = self.db_manager_patcher.start()
        
        mock_db_manager_instance = MagicMock()
        mock_db_manager_instance.get_engine.return_value = self.engine
        self.mock_db_manager.return_value = mock_db_manager_instance
        
        # ScreenerResult 인스턴스 생성
        self.screener_result = ScreenerResult()
        print("ScreenerResult 인스턴스 생성 완료")
        
        # 테스트 데이터
        self.test_name = "테스트 스크리닝"
        self.test_description = "테스트 설명"
        self.test_criteria = [
            {
                "type": "volume",
                "params": {
                    "min_volume": 1000000000
                }
            },
            {
                "type": "volatility",
                "params": {
                    "min_volatility": 0.05,
                    "max_volatility": 0.2
                }
            }
        ]
        self.test_results = [
            {
                "symbol": "KRW-BTC",
                "name": "비트코인",
                "current_price": 50000000,
                "volume_24h": 5000000000,
                "matched_criteria": ["volume", "volatility"]
            },
            {
                "symbol": "KRW-ETH",
                "name": "이더리움",
                "current_price": 3000000,
                "volume_24h": 2000000000,
                "matched_criteria": ["volume"]
            }
        ]
        print("테스트 데이터 준비 완료")
    
    def tearDown(self):
        """테스트 정리"""
        self.db_manager_patcher.stop()
    
    def test_save_screening_result(self):
        """스크리닝 결과 저장 테스트"""
        print("\n=== 테스트 id 4_2_1: test_save_screening_result ===")
        print("스크리닝 결과 저장 테스트 시작")
        
        # 테스트 실행
        result_id = self.screener_result.save_screening_result(
            self.test_name, self.test_description, self.test_criteria, self.test_results
        )
        
        print(f"저장된 결과 ID: {result_id}")
        
        # 검증
        self.assertGreater(result_id, 0)
        
        # 저장된 결과 확인
        with self.engine.connect() as conn:
            # 결과 확인
            result = conn.execute(text("SELECT * FROM screening_results WHERE id = :id"), {"id": result_id})
            row = result.fetchone()
            
            self.assertIsNotNone(row)
            self.assertEqual(row[1], self.test_name)
            self.assertEqual(row[2], self.test_description)
            self.assertEqual(json.loads(row[3]), self.test_criteria)
            
            print(f"저장된 결과 확인: 이름={row[1]}, 설명={row[2]}")
            
            # 상세 정보 확인
            details = conn.execute(text("SELECT * FROM screening_details WHERE result_id = :id"), {"id": result_id})
            rows = details.fetchall()
            
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0][2], "KRW-BTC")
            self.assertEqual(rows[1][2], "KRW-ETH")
            
            print(f"저장된 상세 정보 확인: {len(rows)}개 항목, 심볼=[{rows[0][2]}, {rows[1][2]}]")
        
        print("스크리닝 결과 저장 테스트 완료")
    
    def test_get_screening_results(self):
        """스크리닝 결과 목록 조회 테스트"""
        print("\n=== 테스트 id 4_2_3: test_get_screening_results ===")
        print("스크리닝 결과 목록 조회 테스트 시작")
        
        # 테스트 데이터 저장
        result_id1 = self.screener_result.save_screening_result(
            self.test_name, self.test_description, self.test_criteria, self.test_results
        )
        
        result_id2 = self.screener_result.save_screening_result(
            self.test_name + " 2", self.test_description, self.test_criteria, self.test_results
        )
        
        print(f"테스트 데이터 저장 완료: ID={result_id1}, ID={result_id2}")
        
        # 테스트 실행
        results = self.screener_result.get_screening_results()
        
        # 검증
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], result_id2)  # 최신 결과가 먼저 나옴
        self.assertEqual(results[1]['id'], result_id1)
        
        print(f"결과 목록 조회 확인: {len(results)}개 항목, 최신 결과 ID={results[0]['id']}")
        
        # 페이지네이션 테스트
        results_limited = self.screener_result.get_screening_results(limit=1)
        self.assertEqual(len(results_limited), 1)
        self.assertEqual(results_limited[0]['id'], result_id2)
        
        print(f"페이지네이션 테스트 완료: limit=1 적용 시 {len(results_limited)}개 항목")
        print("스크리닝 결과 목록 조회 테스트 완료")
    
    def test_get_screening_result(self):
        """특정 스크리닝 결과 조회 테스트"""
        print("\n=== 테스트 id 4_2_2: test_get_screening_result ===")
        print("특정 스크리닝 결과 조회 테스트 시작")
        
        # 테스트 데이터 저장
        result_id = self.screener_result.save_screening_result(
            self.test_name, self.test_description, self.test_criteria, self.test_results
        )
        
        print(f"테스트 데이터 저장 완료: ID={result_id}")
        
        # 테스트 실행
        result = self.screener_result.get_screening_result(result_id)
        
        # 검증
        self.assertEqual(result['id'], result_id)
        self.assertEqual(result['name'], self.test_name)
        self.assertEqual(result['description'], self.test_description)
        self.assertEqual(result['criteria'], self.test_criteria)
        self.assertEqual(len(result['details']), 2)
        self.assertEqual(result['details'][0]['symbol'], "KRW-BTC")
        self.assertEqual(result['details'][1]['symbol'], "KRW-ETH")
        
        print(f"결과 조회 확인: ID={result['id']}, 이름={result['name']}")
        print(f"상세 정보: {len(result['details'])}개 항목, 심볼=[{result['details'][0]['symbol']}, {result['details'][1]['symbol']}]")
        print("특정 스크리닝 결과 조회 테스트 완료")
    
    def test_delete_screening_result(self):
        """스크리닝 결과 삭제 테스트"""
        print("\n=== 테스트 id 4_2_4: test_delete_screening_result ===")
        # 테스트 데이터 저장
        result_id = self.screener_result.save_screening_result(
            self.test_name, self.test_description, self.test_criteria, self.test_results
        )
        
        # 삭제 전 확인
        result = self.screener_result.get_screening_result(result_id)
        self.assertNotEqual(result, {})
        
        # 테스트 실행
        success = self.screener_result.delete_screening_result(result_id)
        
        # 검증
        self.assertTrue(success)
        
        # 삭제 후 확인
        result = self.screener_result.get_screening_result(result_id)
        self.assertEqual(result, {})
    
    def test_filter_screening_results(self):
        """스크리닝 결과 필터링 테스트"""
        print("\n=== 테스트 id 4_2_5: test_filter_screening_results ===")
        # 테스트 데이터 저장
        self.screener_result.save_screening_result(
            "볼륨 스크리닝", "거래량 기준 스크리닝", self.test_criteria, self.test_results
        )
        
        self.screener_result.save_screening_result(
            "변동성 스크리닝", "변동성 기준 스크리닝", self.test_criteria, self.test_results
        )
        
        # 이름으로 필터링 테스트
        results = self.screener_result.filter_screening_results({"name": "볼륨"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "볼륨 스크리닝")
        
        # 코인 심볼로 필터링 테스트
        results = self.screener_result.filter_screening_results({"symbol": "KRW-BTC"})
        self.assertEqual(len(results), 2)  # 두 결과 모두 KRW-BTC 포함
    
    def test_sort_screening_details(self):
        """스크리닝 결과 상세 정보 정렬 테스트"""
        print("\n=== 테스트 id 4_2_7: test_sort_screening_details ===")
        print("스크리닝 결과 상세 정보 정렬 테스트 시작")
        
        # 테스트 데이터 저장
        result_id = self.screener_result.save_screening_result(
            self.test_name, self.test_description, self.test_criteria, self.test_results
        )
        
        print(f"테스트 데이터 저장 완료: ID={result_id}")
        
        # 가격 기준 내림차순 정렬 테스트
        details = self.screener_result.sort_screening_details(result_id, sort_by='current_price', order='desc')
        self.assertEqual(details[0]['symbol'], "KRW-BTC")  # 비트코인이 더 비쌈
        self.assertEqual(details[1]['symbol'], "KRW-ETH")
        
        print(f"가격 내림차순 정렬 확인: 첫번째={details[0]['symbol']}, 두번째={details[1]['symbol']}")
        
        # 가격 기준 오름차순 정렬 테스트
        details = self.screener_result.sort_screening_details(result_id, sort_by='current_price', order='asc')
        self.assertEqual(details[0]['symbol'], "KRW-ETH")  # 이더리움이 더 쌈
        self.assertEqual(details[1]['symbol'], "KRW-BTC")
        
        print(f"가격 오름차순 정렬 확인: 첫번째={details[0]['symbol']}, 두번째={details[1]['symbol']}")
        
        # 심볼 기준 정렬 테스트
        details = self.screener_result.sort_screening_details(result_id, sort_by='symbol', order='asc')
        self.assertEqual(details[0]['symbol'], "KRW-BTC")  # 알파벳 순
        self.assertEqual(details[1]['symbol'], "KRW-ETH")
        
        print(f"심볼 정렬 확인: 첫번째={details[0]['symbol']}, 두번째={details[1]['symbol']}")
        print("스크리닝 결과 상세 정보 정렬 테스트 완료")
    
    @patch('os.path.join')
    @patch('os.makedirs')
    def test_export_to_csv(self, mock_makedirs, mock_join):
        """CSV 내보내기 테스트"""
        print("\n=== 테스트 id 4_2_6: test_export_to_csv ===")
        # 임시 파일 경로 직접 지정
        temp_file_path = "test_export.csv"
        
        # 경로 모의 설정
        mock_join.return_value = temp_file_path
        
        # 테스트 데이터 저장
        result_id = self.screener_result.save_screening_result(
            self.test_name, self.test_description, self.test_criteria, self.test_results
        )
        
        try:
            # 테스트 실행
            file_path = self.screener_result.export_to_csv(result_id, temp_file_path)
            
            # 검증
            self.assertEqual(file_path, temp_file_path)
            self.assertTrue(os.path.exists(file_path))
            
            # CSV 파일 내용 확인
            df = pd.read_csv(file_path)
            self.assertEqual(len(df), 2)
            self.assertEqual(df['symbol'].tolist(), ['KRW-BTC', 'KRW-ETH'])
            
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

if __name__ == '__main__':
    unittest.main()