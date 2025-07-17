#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
유틸리티 함수 단위 테스트
"""

import os
import unittest
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open

from upbit_auto_trading.utils import (
    generate_id,
    encrypt_api_key,
    decrypt_api_key,
    load_config,
    save_config,
    format_number,
    format_timestamp,
    parse_timeframe,
    ensure_directory
)

class TestUtils(unittest.TestCase):
    """유틸리티 함수 테스트"""
    
    def test_generate_id(self):
        """ID 생성 테스트"""
        # 접두사 없이 생성
        id1 = generate_id()
        self.assertIsInstance(id1, str)
        self.assertTrue(len(id1) > 0)
        
        # 접두사 있이 생성
        prefix = "test"
        id2 = generate_id(prefix)
        self.assertIsInstance(id2, str)
        self.assertTrue(id2.startswith(f"{prefix}-"))
        
        # 고유성 테스트
        id3 = generate_id(prefix)
        self.assertNotEqual(id2, id3)
    
    def test_encrypt_decrypt_api_key(self):
        """API 키 암호화/복호화 테스트"""
        api_key = "test_api_key"
        password = "test_password"
        
        # 암호화
        encrypted = encrypt_api_key(api_key, password)
        self.assertIsInstance(encrypted, str)
        self.assertNotEqual(encrypted, api_key)
        
        # 복호화
        decrypted = decrypt_api_key(encrypted, password)
        self.assertEqual(decrypted, api_key)
        
        # 잘못된 비밀번호로 복호화 시도
        with self.assertRaises(Exception):
            decrypt_api_key(encrypted, "wrong_password")
    
    def test_format_number(self):
        """숫자 포맷팅 테스트"""
        # 정수
        self.assertEqual(format_number(1000), "1,000.00")
        
        # 소수
        self.assertEqual(format_number(1234.5678), "1,234.57")
        
        # 소수점 자릿수 지정
        self.assertEqual(format_number(1234.5678, decimal_places=3), "1,234.568")
        
        # 0
        self.assertEqual(format_number(0), "0.00")
        
        # 음수
        self.assertEqual(format_number(-1000), "-1,000.00")
    
    def test_format_timestamp(self):
        """타임스탬프 포맷팅 테스트"""
        # 기본 포맷
        timestamp = datetime(2023, 1, 1, 9, 0, 0)
        self.assertEqual(format_timestamp(timestamp), "2023-01-01 09:00:00")
        
        # 사용자 지정 포맷
        self.assertEqual(format_timestamp(timestamp, "%Y-%m-%d"), "2023-01-01")
        self.assertEqual(format_timestamp(timestamp, "%H:%M:%S"), "09:00:00")
        self.assertEqual(format_timestamp(timestamp, "%Y%m%d%H%M%S"), "20230101090000")
    
    def test_parse_timeframe(self):
        """시간대 변환 테스트"""
        # 분
        self.assertEqual(parse_timeframe("1m"), timedelta(minutes=1))
        self.assertEqual(parse_timeframe("5m"), timedelta(minutes=5))
        self.assertEqual(parse_timeframe("15m"), timedelta(minutes=15))
        self.assertEqual(parse_timeframe("30m"), timedelta(minutes=30))
        
        # 시간
        self.assertEqual(parse_timeframe("1h"), timedelta(hours=1))
        self.assertEqual(parse_timeframe("4h"), timedelta(hours=4))
        
        # 일
        self.assertEqual(parse_timeframe("1d"), timedelta(days=1))
        
        # 주
        self.assertEqual(parse_timeframe("1w"), timedelta(weeks=1))
        
        # 월 (근사값)
        self.assertEqual(parse_timeframe("1M"), timedelta(days=30))
        
        # 잘못된 형식
        with self.assertRaises(ValueError):
            parse_timeframe("invalid")
        
        with self.assertRaises(ValueError):
            parse_timeframe("1x")
    
    def test_ensure_directory(self):
        """디렉토리 생성 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 존재하지 않는 디렉토리 생성
            test_dir = os.path.join(temp_dir, "test_dir")
            self.assertTrue(ensure_directory(test_dir))
            self.assertTrue(os.path.exists(test_dir))
            
            # 이미 존재하는 디렉토리
            self.assertTrue(ensure_directory(test_dir))
            
            # 중첩 디렉토리 생성
            nested_dir = os.path.join(test_dir, "nested", "dir")
            self.assertTrue(ensure_directory(nested_dir))
            self.assertTrue(os.path.exists(nested_dir))
    
    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    @patch("os.path.exists", return_value=True)
    def test_load_config_json(self, mock_exists, mock_file):
        """JSON 설정 파일 로드 테스트"""
        config = load_config("config.json")
        self.assertEqual(config, {"key": "value"})
        mock_exists.assert_called_once_with("config.json")
        mock_file.assert_called_once_with("config.json", "r", encoding="utf-8")
    
    @patch("yaml.safe_load", return_value={"key": "value"})
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    def test_load_config_yaml(self, mock_exists, mock_file, mock_yaml_load):
        """YAML 설정 파일 로드 테스트"""
        config = load_config("config.yaml")
        self.assertEqual(config, {"key": "value"})
        mock_exists.assert_called_once_with("config.yaml")
        mock_file.assert_called_once_with("config.yaml", "r", encoding="utf-8")
        mock_yaml_load.assert_called_once()
    
    @patch("os.path.exists", return_value=False)
    def test_load_config_not_exists(self, mock_exists):
        """존재하지 않는 설정 파일 로드 테스트"""
        config = load_config("not_exists.yaml")
        self.assertEqual(config, {})
        mock_exists.assert_called_once_with("not_exists.yaml")
    
    @patch("json.dump")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_save_config_json(self, mock_makedirs, mock_file, mock_json_dump):
        """JSON 설정 파일 저장 테스트"""
        config = {"key": "value"}
        result = save_config(config, "config.json")
        self.assertTrue(result)
        mock_makedirs.assert_called_once_with(os.path.dirname("config.json"), exist_ok=True)
        mock_file.assert_called_once_with("config.json", "w", encoding="utf-8")
        mock_json_dump.assert_called_once()
    
    @patch("yaml.dump")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_save_config_yaml(self, mock_makedirs, mock_file, mock_yaml_dump):
        """YAML 설정 파일 저장 테스트"""
        config = {"key": "value"}
        result = save_config(config, "config.yaml")
        self.assertTrue(result)
        mock_makedirs.assert_called_once_with(os.path.dirname("config.yaml"), exist_ok=True)
        mock_file.assert_called_once_with("config.yaml", "w", encoding="utf-8")
        mock_yaml_dump.assert_called_once()
    
    @patch("os.makedirs")
    def test_save_config_unsupported_format(self, mock_makedirs):
        """지원하지 않는 형식의 설정 파일 저장 테스트"""
        config = {"key": "value"}
        result = save_config(config, "config.txt")
        self.assertFalse(result)
        mock_makedirs.assert_called_once_with(os.path.dirname("config.txt"), exist_ok=True)

if __name__ == '__main__':
    unittest.main()