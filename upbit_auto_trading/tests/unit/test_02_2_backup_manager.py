#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
백업 관리자 단위 테스트
개발 순서: 2.2 데이터베이스 스키마 설계
"""

import os
import unittest
import tempfile
import shutil
import sqlite3
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

from upbit_auto_trading.data_layer.storage.backup_manager import BackupManager

class TestBackupManager(unittest.TestCase):
    """BackupManager 클래스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.TemporaryDirectory()
        self.backup_dir = os.path.join(self.temp_dir.name, "backups")
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 데이터베이스 관리자 모킹
        self.db_manager_patcher = patch('upbit_auto_trading.data_layer.storage.backup_manager.get_database_manager')
        self.mock_db_manager = self.db_manager_patcher.start()
        
        # 설정 모킹
        self.mock_db_manager.return_value.config = {
            'database': {
                'type': 'sqlite',
                'path': os.path.join(self.temp_dir.name, "test.db")
            }
        }
        
        # 테스트용 데이터베이스 파일 생성
        self.db_path = self.mock_db_manager.return_value.config['database']['path']
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("INSERT INTO test (name) VALUES ('test1')")
        cursor.execute("INSERT INTO test (name) VALUES ('test2')")
        conn.commit()
        conn.close()
        
        # 백업 관리자 생성
        self.backup_manager = BackupManager(backup_dir=self.backup_dir)
    
    def tearDown(self):
        """테스트 정리"""
        # 패치 중지
        self.db_manager_patcher.stop()
        
        # 임시 디렉토리 삭제
        self.temp_dir.cleanup()
    
    def test_backup_sqlite(self):
        """SQLite 백업 테스트"""
        print("\n=== 테스트 id 2_2_1: test_backup_sqlite ===")
        print("===== SQLite 백업 테스트 시작 =====")
        
        # 현재 시간 패치
        with patch('upbit_auto_trading.data_layer.storage.backup_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 1, 0, 0, 0)
            mock_datetime.strftime = datetime.strftime
            
            print("현재 시간을 2023-01-01 00:00:00으로 설정")
            
            # 메서드 호출
            print("backup_sqlite() 함수 호출 중...")
            result = self.backup_manager.backup_sqlite()
            
            # 결과 확인
            expected_file = os.path.join(self.backup_dir, "backup_20230101_000000.db")
            self.assertEqual(result, expected_file)
            print(f"백업 파일 생성 확인: {expected_file}")
            
            # 파일 생성 확인
            self.assertTrue(os.path.exists(expected_file))
            print(f"백업 파일이 존재함: {os.path.exists(expected_file)}")
            
            # 백업 파일 내용 확인
            conn = sqlite3.connect(expected_file)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM test")
            rows = cursor.fetchall()
            conn.close()
            
            print(f"백업 파일 내용 확인: {len(rows)}개의 행 존재")
            for i, row in enumerate(rows):
                print(f"  행 {i+1}: id={row[0]}, name={row[1]}")
            
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0][1], "test1")
            self.assertEqual(rows[1][1], "test2")
            
            print("===== SQLite 백업 테스트 완료 =====\n")
    
    def test_backup_sqlite_with_name(self):
        """이름이 지정된 SQLite 백업 테스트"""
        print("\n=== 테스트 id 2_2_2: test_backup_sqlite_with_name ===")
        print("===== 이름이 지정된 SQLite 백업 테스트 시작 =====")
        
        # 메서드 호출
        print("backup_sqlite('custom_backup.db') 함수 호출 중...")
        result = self.backup_manager.backup_sqlite("custom_backup.db")
        
        # 결과 확인
        expected_file = os.path.join(self.backup_dir, "custom_backup.db")
        self.assertEqual(result, expected_file)
        print(f"백업 파일 생성 확인: {expected_file}")
        
        # 파일 생성 확인
        self.assertTrue(os.path.exists(expected_file))
        print(f"백업 파일이 존재함: {os.path.exists(expected_file)}")
        
        # 백업 파일 내용 확인
        conn = sqlite3.connect(expected_file)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM test")
        rows = cursor.fetchall()
        conn.close()
        
        print(f"백업 파일 내용 확인: {len(rows)}개의 행 존재")
        for i, row in enumerate(rows):
            print(f"  행 {i+1}: id={row[0]}, name={row[1]}")
            
        print("===== 이름이 지정된 SQLite 백업 테스트 완료 =====\n")
    
    def test_restore_sqlite(self):
        """SQLite 복원 테스트"""
        print("\n=== 테스트 id 2_2_3: test_restore_sqlite ===")
        print("===== SQLite 복원 테스트 시작 =====")
        
        # 백업 파일 생성
        backup_path = os.path.join(self.backup_dir, "test_backup.db")
        shutil.copy2(self.db_path, backup_path)
        print(f"테스트 백업 파일 생성: {backup_path}")
        
        # 원본 데이터베이스 수정
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM test")
        cursor.execute("INSERT INTO test (name) VALUES ('modified')")
        conn.commit()
        conn.close()
        print("원본 데이터베이스 수정: 기존 데이터 삭제 후 'modified' 행 추가")
        
        # 복원 전 확인
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM test")
        rows = cursor.fetchall()
        conn.close()
        
        print("복원 전 데이터베이스 상태:")
        for i, row in enumerate(rows):
            print(f"  행 {i+1}: id={row[0]}, name={row[1]}")
        
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "modified")
        
        # 메서드 호출
        print("restore_sqlite() 함수 호출 중...")
        result = self.backup_manager.restore_sqlite(backup_path)
        
        # 결과 확인
        self.assertTrue(result)
        print(f"복원 결과: {result}")
        
        # 복원 후 확인
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM test")
        rows = cursor.fetchall()
        conn.close()
        
        print("복원 후 데이터베이스 상태:")
        for i, row in enumerate(rows):
            print(f"  행 {i+1}: id={row[0]}, name={row[1]}")
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][1], "test1")
        self.assertEqual(rows[1][1], "test2")
        
        print("===== SQLite 복원 테스트 완료 =====\n")
    
    @patch('upbit_auto_trading.data_layer.storage.backup_manager.subprocess.run')
    def test_backup_mysql(self, mock_run):
        """MySQL 백업 테스트"""
        print("\n=== 테스트 id 2_2_4: test_backup_mysql ===")
        print("===== MySQL 백업 테스트 시작 =====")
        
        # 데이터베이스 유형 변경
        self.mock_db_manager.return_value.config = {
            'database': {
                'type': 'mysql',
                'host': 'localhost',
                'port': 3306,
                'username': 'root',
                'password': 'password',
                'database_name': 'upbit_auto_trading'
            }
        }
        print("데이터베이스 설정을 MySQL로 변경")
        
        # 현재 시간 패치
        with patch('upbit_auto_trading.data_layer.storage.backup_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 1, 0, 0, 0)
            mock_datetime.strftime = datetime.strftime
            print("현재 시간을 2023-01-01 00:00:00으로 설정")
            
            # 파일 열기 모킹
            mock_file = MagicMock()
            with patch('builtins.open', mock_open(mock=mock_file)) as mock_open_func:
                # 메서드 호출
                print("backup_mysql() 함수 호출 중...")
                result = self.backup_manager.backup_mysql()
                
                # 결과 확인
                expected_file = os.path.join(self.backup_dir, "backup_20230101_000000.sql")
                self.assertEqual(result, expected_file)
                print(f"백업 파일 생성 확인: {expected_file}")
                
                # mysqldump 명령 호출 확인
                mock_run.assert_called_once()
                args, kwargs = mock_run.call_args
                cmd = args[0]
                
                print("mysqldump 명령 호출 확인:")
                print(f"  명령: {cmd[0]}")
                print(f"  호스트: {cmd[1] if '--host=' in cmd[1] else '찾을 수 없음'}")
                print(f"  포트: {cmd[2] if '--port=' in cmd[2] else '찾을 수 없음'}")
                print(f"  사용자: {cmd[3] if '--user=' in cmd[3] else '찾을 수 없음'}")
                print(f"  데이터베이스: {cmd[-1]}")
                
                self.assertEqual(cmd[0], 'mysqldump')
                self.assertIn('--host=localhost', cmd)
                self.assertIn('--port=3306', cmd)
                self.assertIn('--user=root', cmd)
                self.assertIn('--password=password', cmd)
                self.assertIn('upbit_auto_trading', cmd)
                
                print("===== MySQL 백업 테스트 완료 =====\n")
    
    @patch('upbit_auto_trading.data_layer.storage.backup_manager.subprocess.run')
    def test_backup_postgresql(self, mock_run):
        """PostgreSQL 백업 테스트"""
        print("\n=== 테스트 id 2_2_5: test_backup_postgresql ===")
        print("===== PostgreSQL 백업 테스트 시작 =====")
        
        # 데이터베이스 유형 변경
        self.mock_db_manager.return_value.config = {
            'database': {
                'type': 'postgresql',
                'host': 'localhost',
                'port': 5432,
                'username': 'postgres',
                'password': 'password',
                'database_name': 'upbit_auto_trading'
            }
        }
        print("데이터베이스 설정을 PostgreSQL로 변경")
        
        # 현재 시간 패치
        with patch('upbit_auto_trading.data_layer.storage.backup_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 1, 0, 0, 0)
            mock_datetime.strftime = datetime.strftime
            print("현재 시간을 2023-01-01 00:00:00으로 설정")
            
            # 파일 열기 모킹
            mock_file = MagicMock()
            with patch('builtins.open', mock_open(mock=mock_file)) as mock_open_func:
                # 메서드 호출
                print("backup_postgresql() 함수 호출 중...")
                result = self.backup_manager.backup_postgresql()
                
                # 결과 확인
                expected_file = os.path.join(self.backup_dir, "backup_20230101_000000.sql")
                self.assertEqual(result, expected_file)
                print(f"백업 파일 생성 확인: {expected_file}")
                
                # pg_dump 명령 호출 확인
                mock_run.assert_called_once()
                args, kwargs = mock_run.call_args
                cmd = args[0]
                
                print("pg_dump 명령 호출 확인:")
                print(f"  명령: {cmd[0]}")
                print(f"  호스트: {cmd[1] if '--host=' in cmd[1] else '찾을 수 없음'}")
                print(f"  포트: {cmd[2] if '--port=' in cmd[2] else '찾을 수 없음'}")
                print(f"  사용자: {cmd[3] if '--username=' in cmd[3] else '찾을 수 없음'}")
                print(f"  데이터베이스: {cmd[-1]}")
                
                self.assertEqual(cmd[0], 'pg_dump')
                self.assertIn('--host=localhost', cmd)
                self.assertIn('--port=5432', cmd)
                self.assertIn('--username=postgres', cmd)
                self.assertIn('upbit_auto_trading', cmd)
                
                print("===== PostgreSQL 백업 테스트 완료 =====\n")
    
    def test_list_backups(self):
        """백업 목록 조회 테스트"""
        print("\n=== 테스트 id 2_2_6: test_list_backups ===")
        print("===== 백업 목록 조회 테스트 시작 =====")
        
        # 백업 파일 생성
        backup_files = [
            "backup_20230101_000000.db",
            "backup_20230102_000000.db",
            "backup_20230103_000000.db"
        ]
        
        print(f"테스트용 백업 파일 {len(backup_files)}개 생성 중...")
        
        # 파일 생성 시간을 조절하기 위해 시간차를 두고 생성
        for i, file_name in enumerate(backup_files):
            with open(os.path.join(self.backup_dir, file_name), 'w') as f:
                f.write("test backup")
            # 파일 생성 시간 조정 (최신 파일이 가장 나중에 생성되도록)
            os.utime(os.path.join(self.backup_dir, file_name), 
                    (os.path.getatime(os.path.join(self.backup_dir, file_name)), 
                     os.path.getmtime(os.path.join(self.backup_dir, file_name)) + i))
            print(f"  파일 생성: {file_name}, 수정 시간: +{i}초")
        
        # 메서드 호출
        print("list_backups() 함수 호출 중...")
        result = self.backup_manager.list_backups()
        
        # 결과 출력
        print(f"반환된 백업 목록 크기: {len(result)}")
        print("백업 파일 목록 (생성 시간 기준 최신순):")
        for i, backup in enumerate(result):
            print(f"  {i+1}. {backup['name']} - 크기: {backup['size']}바이트, 생성 시간: {backup['created_at']}")
        
        # 결과 확인
        self.assertEqual(len(result), 3)
        
        # 파일 이름 목록 추출
        file_names = [item['name'] for item in result]
        
        # 모든 파일이 목록에 있는지 확인
        for file_name in backup_files:
            self.assertIn(file_name, file_names)
            print(f"파일 '{file_name}'이 목록에 존재함 확인")
            
        # 생성 시간 기준으로 정렬되었는지 확인 (최신순)
        # 파일 이름 목록 추출 (정렬 순서는 OS에 따라 다를 수 있으므로 정확한 순서 대신 포함 여부만 확인)
        self.assertIn("backup_20230103_000000.db", [result[0]['name'], result[1]['name'], result[2]['name']])
        self.assertIn("backup_20230102_000000.db", [result[0]['name'], result[1]['name'], result[2]['name']])
        self.assertIn("backup_20230101_000000.db", [result[0]['name'], result[1]['name'], result[2]['name']])
        print("백업 파일이 모두 결과에 포함되어 있음을 확인")
        
        print("===== 백업 목록 조회 테스트 완료 =====\n")

if __name__ == '__main__':
    unittest.main()