#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
백업 관리자 단위 테스트
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
        # 현재 시간 패치
        with patch('upbit_auto_trading.data_layer.storage.backup_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 1, 0, 0, 0)
            mock_datetime.strftime = datetime.strftime
            
            # 메서드 호출
            result = self.backup_manager.backup_sqlite()
            
            # 결과 확인
            expected_file = os.path.join(self.backup_dir, "backup_20230101_000000.db")
            self.assertEqual(result, expected_file)
            
            # 파일 생성 확인
            self.assertTrue(os.path.exists(expected_file))
            
            # 백업 파일 내용 확인
            conn = sqlite3.connect(expected_file)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM test")
            rows = cursor.fetchall()
            conn.close()
            
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0][1], "test1")
            self.assertEqual(rows[1][1], "test2")
    
    def test_backup_sqlite_with_name(self):
        """이름이 지정된 SQLite 백업 테스트"""
        # 메서드 호출
        result = self.backup_manager.backup_sqlite("custom_backup.db")
        
        # 결과 확인
        expected_file = os.path.join(self.backup_dir, "custom_backup.db")
        self.assertEqual(result, expected_file)
        
        # 파일 생성 확인
        self.assertTrue(os.path.exists(expected_file))
    
    def test_restore_sqlite(self):
        """SQLite 복원 테스트"""
        # 백업 파일 생성
        backup_path = os.path.join(self.backup_dir, "test_backup.db")
        shutil.copy2(self.db_path, backup_path)
        
        # 원본 데이터베이스 수정
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM test")
        cursor.execute("INSERT INTO test (name) VALUES ('modified')")
        conn.commit()
        conn.close()
        
        # 복원 전 확인
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM test")
        rows = cursor.fetchall()
        conn.close()
        
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "modified")
        
        # 메서드 호출
        result = self.backup_manager.restore_sqlite(backup_path)
        
        # 결과 확인
        self.assertTrue(result)
        
        # 복원 후 확인
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM test")
        rows = cursor.fetchall()
        conn.close()
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][1], "test1")
        self.assertEqual(rows[1][1], "test2")
    
    @patch('upbit_auto_trading.data_layer.storage.backup_manager.subprocess.run')
    def test_backup_mysql(self, mock_run):
        """MySQL 백업 테스트"""
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
        
        # 현재 시간 패치
        with patch('upbit_auto_trading.data_layer.storage.backup_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 1, 0, 0, 0)
            mock_datetime.strftime = datetime.strftime
            
            # 파일 열기 모킹
            mock_file = MagicMock()
            with patch('builtins.open', mock_open(mock=mock_file)) as mock_open_func:
                # 메서드 호출
                result = self.backup_manager.backup_mysql()
                
                # 결과 확인
                expected_file = os.path.join(self.backup_dir, "backup_20230101_000000.sql")
                self.assertEqual(result, expected_file)
                
                # mysqldump 명령 호출 확인
                mock_run.assert_called_once()
                args, kwargs = mock_run.call_args
                cmd = args[0]
                
                self.assertEqual(cmd[0], 'mysqldump')
                self.assertIn('--host=localhost', cmd)
                self.assertIn('--port=3306', cmd)
                self.assertIn('--user=root', cmd)
                self.assertIn('--password=password', cmd)
                self.assertIn('upbit_auto_trading', cmd)
    
    @patch('upbit_auto_trading.data_layer.storage.backup_manager.subprocess.run')
    def test_backup_postgresql(self, mock_run):
        """PostgreSQL 백업 테스트"""
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
        
        # 현재 시간 패치
        with patch('upbit_auto_trading.data_layer.storage.backup_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 1, 0, 0, 0)
            mock_datetime.strftime = datetime.strftime
            
            # 파일 열기 모킹
            mock_file = MagicMock()
            with patch('builtins.open', mock_open(mock=mock_file)) as mock_open_func:
                # 메서드 호출
                result = self.backup_manager.backup_postgresql()
                
                # 결과 확인
                expected_file = os.path.join(self.backup_dir, "backup_20230101_000000.sql")
                self.assertEqual(result, expected_file)
                
                # pg_dump 명령 호출 확인
                mock_run.assert_called_once()
                args, kwargs = mock_run.call_args
                cmd = args[0]
                
                self.assertEqual(cmd[0], 'pg_dump')
                self.assertIn('--host=localhost', cmd)
                self.assertIn('--port=5432', cmd)
                self.assertIn('--username=postgres', cmd)
                self.assertIn('upbit_auto_trading', cmd)
    
    def test_list_backups(self):
        """백업 목록 조회 테스트"""
        # 백업 파일 생성
        backup_files = [
            "backup_20230101_000000.db",
            "backup_20230102_000000.db",
            "backup_20230103_000000.db"
        ]
        
        for file_name in backup_files:
            with open(os.path.join(self.backup_dir, file_name), 'w') as f:
                f.write("test backup")
        
        # 메서드 호출
        result = self.backup_manager.list_backups()
        
        # 결과 확인
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['name'], "backup_20230103_000000.db")
        self.assertEqual(result[1]['name'], "backup_20230102_000000.db")
        self.assertEqual(result[2]['name'], "backup_20230101_000000.db")

if __name__ == '__main__':
    unittest.main()