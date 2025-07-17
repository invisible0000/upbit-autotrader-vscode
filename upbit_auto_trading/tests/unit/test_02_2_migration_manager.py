#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
마이그레이션 관리자 단위 테스트
개발 순서: 2.2 데이터베이스 스키마 설계
"""

import os
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

from sqlalchemy import Column, Integer, String, MetaData, Table, create_engine
from sqlalchemy.orm import sessionmaker

from upbit_auto_trading.data_layer.storage.migration_manager import MigrationManager

class TestMigrationManager(unittest.TestCase):
    """MigrationManager 클래스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.TemporaryDirectory()
        self.migrations_path = os.path.join(self.temp_dir.name, "migrations")
        os.makedirs(self.migrations_path, exist_ok=True)
        
        # 데이터베이스 관리자 모킹
        self.db_manager_patcher = patch('upbit_auto_trading.data_layer.storage.migration_manager.get_database_manager')
        self.mock_db_manager = self.db_manager_patcher.start()
        
        # 엔진 모킹
        self.mock_engine = MagicMock()
        self.mock_db_manager.return_value.get_engine.return_value = self.mock_engine
        
        # 세션 모킹
        self.mock_session = MagicMock()
        self.mock_db_manager.return_value.get_session.return_value = self.mock_session
        
        # 테이블 존재 여부 모킹
        self.mock_engine.dialect.has_table.return_value = False
        
        # 마이그레이션 관리자 생성
        self.migration_manager = MigrationManager(migrations_path=self.migrations_path)
    
    def tearDown(self):
        """테스트 정리"""
        # 패치 중지
        self.db_manager_patcher.stop()
        
        # 임시 디렉토리 삭제
        self.temp_dir.cleanup()
    
    def test_ensure_migration_table(self):
        """마이그레이션 테이블 생성 테스트"""
        print("\n=== 테스트 id 2_2_7: test_ensure_migration_table ===")
        print("===== 마이그레이션 테이블 생성 테스트 시작 =====")
        
        # 초기화 시 이미 _ensure_migration_table이 호출되었으므로 mock을 리셋
        self.mock_engine.dialect.has_table.reset_mock()
        
        # 테이블이 존재하지 않는 경우
        self.mock_engine.dialect.has_table.return_value = False
        print("테이블이 존재하지 않는 상황 설정")
        
        # 메서드 호출
        print("_ensure_migration_table() 함수 호출 중...")
        self.migration_manager._ensure_migration_table()
        
        # 테이블 생성 확인
        print("테이블 존재 여부 확인 함수 호출 확인")
        self.assertEqual(self.mock_engine.dialect.has_table.call_count, 1)
        print(f"has_table 호출 횟수: {self.mock_engine.dialect.has_table.call_count}")
        
        # 테이블이 이미 존재하는 경우
        self.mock_engine.dialect.has_table.reset_mock()
        self.mock_engine.dialect.has_table.return_value = True
        print("\n테이블이 이미 존재하는 상황 설정")
        
        # 메서드 호출
        print("_ensure_migration_table() 함수 다시 호출 중...")
        self.migration_manager._ensure_migration_table()
        
        # 테이블 생성 확인 (테이블이 이미 존재하므로 create_all은 호출되지 않음)
        print("테이블 존재 여부 확인 함수 호출 확인")
        self.assertEqual(self.mock_engine.dialect.has_table.call_count, 1)
        print(f"has_table 호출 횟수: {self.mock_engine.dialect.has_table.call_count}")
        
        print("===== 마이그레이션 테이블 생성 테스트 완료 =====\n")
    
    @patch('upbit_auto_trading.data_layer.storage.migration_manager.os.path.exists')
    def test_get_available_migrations(self, mock_exists):
        """사용 가능한 마이그레이션 목록 조회 테스트"""
        print("\n=== 테스트 id 2_2_8: test_get_available_migrations ===")
        print("===== 사용 가능한 마이그레이션 목록 조회 테스트 시작 =====")
        
        # 디렉토리가 존재하지 않는 경우
        mock_exists.return_value = False
        print("마이그레이션 디렉토리가 존재하지 않는 상황 설정")
        
        # 메서드 호출
        print("get_available_migrations() 함수 호출 중...")
        result = self.migration_manager.get_available_migrations()
        
        # 결과 확인
        print(f"반환된 마이그레이션 목록: {result}")
        self.assertEqual(result, [])
        
        # 디렉토리가 존재하는 경우
        mock_exists.return_value = True
        print("\n마이그레이션 디렉토리가 존재하는 상황 설정")
        
        # 마이그레이션 파일 생성
        migration_files = [
            "v20230101000000_initial.py",
            "v20230102000000_add_users.py",
            "v20230103000000_add_posts.py"
        ]
        
        print(f"테스트용 마이그레이션 파일 {len(migration_files)}개 생성 중...")
        for file_name in migration_files:
            with open(os.path.join(self.migrations_path, file_name), 'w') as f:
                f.write("# Test migration")
            print(f"  파일 생성: {file_name}")
        
        # pkgutil.iter_modules 패치
        with patch('upbit_auto_trading.data_layer.storage.migration_manager.pkgutil.iter_modules') as mock_iter_modules:
            mock_iter_modules.return_value = [
                (None, "v20230101000000_initial", False),
                (None, "v20230102000000_add_users", False),
                (None, "v20230103000000_add_posts", False),
                (None, "other_file", False),
                (None, "migrations", True)
            ]
            print("pkgutil.iter_modules 모킹 설정 완료")
            
            # 메서드 호출
            print("get_available_migrations() 함수 다시 호출 중...")
            result = self.migration_manager.get_available_migrations()
            
            # 결과 확인
            print(f"반환된 마이그레이션 목록: {result}")
            self.assertEqual(len(result), 3)
            self.assertIn("v20230101000000_initial", result)
            self.assertIn("v20230102000000_add_users", result)
            self.assertIn("v20230103000000_add_posts", result)
            
            print("===== 사용 가능한 마이그레이션 목록 조회 테스트 완료 =====\n")
    
    def test_get_applied_migrations(self):
        """적용된 마이그레이션 목록 조회 테스트"""
        print("\n=== 테스트 id 2_2_9: test_get_applied_migrations ===")
        print("===== 적용된 마이그레이션 목록 조회 테스트 시작 =====")
        
        # 쿼리 결과 모킹
        mock_result = MagicMock()
        mock_result.__iter__.return_value = [("v20230101000000_initial",), ("v20230102000000_add_users",)]
        print("모의 쿼리 결과 설정: v20230101000000_initial, v20230102000000_add_users")
        
        # 연결 및 실행 모킹
        mock_conn = MagicMock()
        mock_conn.execute.return_value = mock_result
        self.mock_engine.connect.return_value.__enter__.return_value = mock_conn
        print("데이터베이스 연결 및 쿼리 실행 모킹 설정 완료")
        
        # 메서드 호출
        print("get_applied_migrations() 함수 호출 중...")
        result = self.migration_manager.get_applied_migrations()
        
        # 결과 출력
        print(f"반환된 적용된 마이그레이션 목록: {result}")
        
        # 결과 확인
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "v20230101000000_initial")
        self.assertEqual(result[1], "v20230102000000_add_users")
        
        print("===== 적용된 마이그레이션 목록 조회 테스트 완료 =====\n")
    
    def test_get_pending_migrations(self):
        """보류 중인 마이그레이션 목록 조회 테스트"""
        print("\n=== 테스트 id 2_2_10: test_get_pending_migrations ===")
        print("===== 보류 중인 마이그레이션 목록 조회 테스트 시작 =====")
        
        # 적용된 마이그레이션 모킹
        with patch.object(self.migration_manager, 'get_applied_migrations') as mock_applied:
            mock_applied.return_value = ["v20230101000000_initial", "v20230102000000_add_users"]
            print("적용된 마이그레이션 모킹: v20230101000000_initial, v20230102000000_add_users")
            
            # 사용 가능한 마이그레이션 모킹
            with patch.object(self.migration_manager, 'get_available_migrations') as mock_available:
                mock_available.return_value = [
                    "v20230101000000_initial",
                    "v20230102000000_add_users",
                    "v20230103000000_add_posts"
                ]
                print("사용 가능한 마이그레이션 모킹: v20230101000000_initial, v20230102000000_add_users, v20230103000000_add_posts")
                
                # 메서드 호출
                print("get_pending_migrations() 함수 호출 중...")
                result = self.migration_manager.get_pending_migrations()
                
                # 결과 출력
                print(f"반환된 보류 중인 마이그레이션 목록: {result}")
                
                # 결과 확인
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0], "v20230103000000_add_posts")
                
                print("===== 보류 중인 마이그레이션 목록 조회 테스트 완료 =====\n")
    
    def test_create_migration(self):
        """마이그레이션 생성 테스트"""
        print("\n=== 테스트 id 2_2_11: test_create_migration ===")
        print("===== 마이그레이션 생성 테스트 시작 =====")
        
        # 현재 시간 패치
        with patch('upbit_auto_trading.data_layer.storage.migration_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 1, 0, 0, 0)
            mock_datetime.strftime = datetime.strftime
            print("현재 시간을 2023-01-01 00:00:00으로 설정")
            
            # 메서드 호출
            print("create_migration('test_migration') 함수 호출 중...")
            result = self.migration_manager.create_migration("test_migration")
            
            # 결과 확인
            expected_file = os.path.join(self.migrations_path, "v20230101000000_test_migration.py")
            self.assertEqual(result, expected_file)
            print(f"마이그레이션 파일 생성 확인: {expected_file}")
            
            # 파일 생성 확인
            self.assertTrue(os.path.exists(expected_file))
            print(f"마이그레이션 파일이 존재함: {os.path.exists(expected_file)}")
            
            # 파일 내용 확인
            with open(expected_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print("마이그레이션 파일 내용 확인:")
                print(f"  파일에 '마이그레이션: test_migration' 포함: {'마이그레이션: test_migration' in content}")
                print(f"  파일에 'def upgrade(session: Session):' 포함: {'def upgrade(session: Session):' in content}")
                print(f"  파일에 'def downgrade(session: Session):' 포함: {'def downgrade(session: Session):' in content}")
                
                self.assertIn("마이그레이션: test_migration", content)
                self.assertIn("def upgrade(session: Session):", content)
                self.assertIn("def downgrade(session: Session):", content)
                
            print("===== 마이그레이션 생성 테스트 완료 =====\n")

if __name__ == '__main__':
    unittest.main()