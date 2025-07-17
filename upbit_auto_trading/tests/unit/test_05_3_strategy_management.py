#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
전략 저장 및 관리 기능 테스트

이 모듈은 전략 저장, 불러오기, 목록 관리 기능을 테스트합니다.
"""

import unittest
import os
import json
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch, MagicMock
import pandas as pd
import sqlite3

from upbit_auto_trading.business_logic.strategy.strategy_interface import StrategyInterface
from upbit_auto_trading.business_logic.strategy.base_strategy import BaseStrategy
from upbit_auto_trading.business_logic.strategy.basic_strategies import MovingAverageCrossStrategy, BollingerBandsStrategy, RSIStrategy
from upbit_auto_trading.business_logic.strategy.strategy_factory import StrategyFactory
from upbit_auto_trading.business_logic.strategy.strategy_manager import StrategyManager
from upbit_auto_trading.data_layer.storage.database_manager import DatabaseManager, get_database_manager
from upbit_auto_trading.data_layer.models import Strategy


class TestStrategyManagement(unittest.TestCase):
    """전략 저장 및 관리 기능 테스트 클래스"""
    
    def setUp(self):
        """테스트 환경 설정"""
        print("\n=== 테스트 ID 05_3_1: setUp ===")
        
        # 임시 데이터베이스 파일 생성
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_strategy.db")
        
        # 데이터베이스 설정
        self.db_config = {
            'database': {
                'type': 'sqlite',
                'path': self.db_path
            }
        }
        
        # 데이터베이스 관리자 초기화
        self.db_manager = DatabaseManager(config=self.db_config)
        self.db_manager.initialize_database()
        
        # 전략 팩토리 초기화
        self.strategy_factory = StrategyFactory()
        
        # 기본 전략 등록
        self.strategy_factory.register_strategy("moving_average_cross", MovingAverageCrossStrategy)
        self.strategy_factory.register_strategy("bollinger_bands", BollingerBandsStrategy)
        self.strategy_factory.register_strategy("rsi", RSIStrategy)
        
        # 전략 관리자 초기화
        self.strategy_manager = StrategyManager(self.db_manager, self.strategy_factory)
        
        # 테스트용 전략 생성
        self.ma_strategy = MovingAverageCrossStrategy({
            "short_window": 10,
            "long_window": 30
        })
        
        self.bb_strategy = BollingerBandsStrategy({
            "window": 20,
            "num_std": 2.0,
            "column": "close"
        })
        
        self.rsi_strategy = RSIStrategy({
            "window": 14,
            "oversold": 30,
            "overbought": 70,
            "column": "close"
        })
    
    def tearDown(self):
        """테스트 환경 정리"""
        print("=== 테스트 ID 05_3_2: tearDown ===")
        
        # 데이터베이스 연결 정리
        self.db_manager.cleanup_database()
        
        # 임시 디렉토리 삭제
        shutil.rmtree(self.temp_dir)
    
    def test_save_strategy(self):
        """전략 저장 기능 테스트"""
        print("=== 테스트 ID 05_3_3: test_save_strategy ===")
        
        # 전략 인스턴스 생성 및 매개변수 확인
        ma_strategy = MovingAverageCrossStrategy({
            "short_window": 10,
            "long_window": 30
        })
        valid_params = ma_strategy.get_parameters()
        
        # 전략 저장
        strategy_id = "test_ma_strategy"
        result = self.strategy_manager.save_strategy(
            strategy_id=strategy_id,
            strategy_type="moving_average_cross",
            name="테스트 이동평균 교차 전략",
            description="테스트용 이동평균 교차 전략입니다.",
            parameters=valid_params
        )
        
        # 저장 성공 확인
        self.assertTrue(result)
        
        # 데이터베이스에서 전략 조회
        session = self.db_manager.get_session()
        strategy = session.query(Strategy).filter_by(id=strategy_id).first()
        session.close()
        
        # 저장된 전략 정보 확인
        self.assertIsNotNone(strategy)
        self.assertEqual(strategy.id, strategy_id)
        self.assertEqual(strategy.name, "테스트 이동평균 교차 전략")
        self.assertEqual(strategy.description, "테스트용 이동평균 교차 전략입니다.")
        
        # 저장된 매개변수 확인
        parameters = json.loads(strategy.parameters)
        self.assertEqual(parameters["short_window"], 10)
        self.assertEqual(parameters["long_window"], 30)
    
    def test_load_strategy(self):
        """전략 불러오기 기능 테스트"""
        print("=== 테스트 ID 05_3_4: test_load_strategy ===")
        
        # 테스트용 전략 생성 및 유효한 매개변수 가져오기
        bb_strategy = BollingerBandsStrategy({
            "window": 20,
            "num_std": 2.5,
            "column": "close"
        })
        valid_params = bb_strategy.get_parameters()
        
        # 테스트용 전략 저장
        strategy_id = "test_bb_strategy"
        self.strategy_manager.save_strategy(
            strategy_id=strategy_id,
            strategy_type="bollinger_bands",
            name="테스트 볼린저 밴드 전략",
            description="테스트용 볼린저 밴드 전략입니다.",
            parameters=valid_params
        )
        
        # 전략 불러오기
        strategy = self.strategy_manager.load_strategy(strategy_id)
        
        # 불러온 전략 확인
        self.assertIsNotNone(strategy)
        self.assertIsInstance(strategy, BollingerBandsStrategy)
        self.assertEqual(strategy.name, "BollingerBandsStrategy")
        
        # 불러온 전략 매개변수 확인
        parameters = strategy.get_parameters()
        self.assertEqual(parameters["window"], 20)
        self.assertEqual(parameters["num_std"], 2.5)
        self.assertEqual(parameters["column"], "close")
    
    def test_get_strategy_list(self):
        """전략 목록 조회 기능 테스트"""
        print("=== 테스트 ID 05_3_5: test_get_strategy_list ===")
        
        # 여러 전략 생성 및 유효한 매개변수 가져오기
        ma_strategy = MovingAverageCrossStrategy({
            "short_window": 10,
            "long_window": 30
        })
        ma_params = ma_strategy.get_parameters()
        
        bb_strategy = BollingerBandsStrategy({
            "window": 20,
            "num_std": 2.5,
            "column": "close"
        })
        bb_params = bb_strategy.get_parameters()
        
        rsi_strategy = RSIStrategy({
            "window": 14,
            "oversold": 30,
            "overbought": 70,
            "column": "close"
        })
        rsi_params = rsi_strategy.get_parameters()
        
        # 여러 전략 저장
        self.strategy_manager.save_strategy(
            strategy_id="test_ma_strategy",
            strategy_type="moving_average_cross",
            name="테스트 이동평균 교차 전략",
            description="테스트용 이동평균 교차 전략입니다.",
            parameters=ma_params
        )
        
        self.strategy_manager.save_strategy(
            strategy_id="test_bb_strategy",
            strategy_type="bollinger_bands",
            name="테스트 볼린저 밴드 전략",
            description="테스트용 볼린저 밴드 전략입니다.",
            parameters=bb_params
        )
        
        self.strategy_manager.save_strategy(
            strategy_id="test_rsi_strategy",
            strategy_type="rsi",
            name="테스트 RSI 전략",
            description="테스트용 RSI 전략입니다.",
            parameters=rsi_params
        )
        
        # 전략 목록 조회
        strategies = self.strategy_manager.get_strategy_list()
        
        # 목록 확인
        self.assertEqual(len(strategies), 3)
        
        # 전략 ID 목록 확인
        strategy_ids = [s["id"] for s in strategies]
        self.assertIn("test_ma_strategy", strategy_ids)
        self.assertIn("test_bb_strategy", strategy_ids)
        self.assertIn("test_rsi_strategy", strategy_ids)
        
        # 전략 타입 확인
        for strategy in strategies:
            if strategy["id"] == "test_ma_strategy":
                self.assertEqual(strategy["strategy_type"], "moving_average_cross")
            elif strategy["id"] == "test_bb_strategy":
                self.assertEqual(strategy["strategy_type"], "bollinger_bands")
            elif strategy["id"] == "test_rsi_strategy":
                self.assertEqual(strategy["strategy_type"], "rsi")
    
    def test_update_strategy(self):
        """전략 업데이트 기능 테스트"""
        print("=== 테스트 ID 05_3_6: test_update_strategy ===")
        
        # 전략 생성 및 유효한 매개변수 가져오기
        rsi_strategy = RSIStrategy({
            "window": 14,
            "oversold": 30,
            "overbought": 70,
            "column": "close"
        })
        valid_params = rsi_strategy.get_parameters()
        
        # 전략 저장
        strategy_id = "test_rsi_strategy"
        self.strategy_manager.save_strategy(
            strategy_id=strategy_id,
            strategy_type="rsi",
            name="테스트 RSI 전략",
            description="테스트용 RSI 전략입니다.",
            parameters=valid_params
        )
        
        # 업데이트할 매개변수 생성 및 유효성 확인
        updated_rsi_strategy = RSIStrategy({
            "window": 21,
            "oversold": 25,
            "overbought": 75,
            "column": "close"
        })
        updated_params = updated_rsi_strategy.get_parameters()
        
        # 전략 업데이트
        result = self.strategy_manager.update_strategy(
            strategy_id=strategy_id,
            name="업데이트된 RSI 전략",
            description="업데이트된 RSI 전략 설명입니다.",
            parameters=updated_params
        )
        
        # 업데이트 성공 확인
        self.assertTrue(result)
        
        # 업데이트된 전략 불러오기
        strategy = self.strategy_manager.load_strategy(strategy_id)
        
        # 업데이트된 정보 확인
        self.assertEqual(strategy.get_parameters()["window"], 21)
        self.assertEqual(strategy.get_parameters()["oversold"], 25)
        self.assertEqual(strategy.get_parameters()["overbought"], 75)
        
        # 데이터베이스에서 직접 확인
        session = self.db_manager.get_session()
        db_strategy = session.query(Strategy).filter_by(id=strategy_id).first()
        session.close()
        
        self.assertEqual(db_strategy.name, "업데이트된 RSI 전략")
        self.assertEqual(db_strategy.description, "업데이트된 RSI 전략 설명입니다.")
        
        # 저장된 매개변수 확인
        parameters = json.loads(db_strategy.parameters)
        self.assertEqual(parameters["window"], 21)
        self.assertEqual(parameters["oversold"], 25)
        self.assertEqual(parameters["overbought"], 75)
    
    def test_delete_strategy(self):
        """전략 삭제 기능 테스트"""
        print("=== 테스트 ID 05_3_7: test_delete_strategy ===")
        
        # 전략 생성 및 유효한 매개변수 가져오기
        ma_strategy = MovingAverageCrossStrategy({
            "short_window": 5,
            "long_window": 20
        })
        valid_params = ma_strategy.get_parameters()
        
        # 전략 저장
        strategy_id = "test_delete_strategy"
        self.strategy_manager.save_strategy(
            strategy_id=strategy_id,
            strategy_type="moving_average_cross",
            name="삭제할 전략",
            description="삭제 테스트용 전략입니다.",
            parameters=valid_params
        )
        
        # 저장된 전략 확인
        session = self.db_manager.get_session()
        strategy_count_before = session.query(Strategy).filter_by(id=strategy_id).count()
        session.close()
        self.assertEqual(strategy_count_before, 1)
        
        # 전략 삭제
        result = self.strategy_manager.delete_strategy(strategy_id)
        
        # 삭제 성공 확인
        self.assertTrue(result)
        
        # 데이터베이스에서 전략이 삭제되었는지 확인
        session = self.db_manager.get_session()
        strategy_count_after = session.query(Strategy).filter_by(id=strategy_id).count()
        session.close()
        self.assertEqual(strategy_count_after, 0)
        
        # 삭제된 전략 불러오기 시도
        strategy = self.strategy_manager.load_strategy(strategy_id)
        self.assertIsNone(strategy)
    
    def test_invalid_strategy_operations(self):
        """잘못된 전략 작업 테스트"""
        print("=== 테스트 ID 05_3_8: test_invalid_strategy_operations ===")
        
        # 존재하지 않는 전략 타입으로 저장 시도
        result = self.strategy_manager.save_strategy(
            strategy_id="invalid_type_strategy",
            strategy_type="non_existent_type",
            name="잘못된 타입 전략",
            description="존재하지 않는 전략 타입 테스트",
            parameters={}
        )
        self.assertFalse(result)
        
        # 잘못된 매개변수로 전략 저장 시도
        result = self.strategy_manager.save_strategy(
            strategy_id="invalid_params_strategy",
            strategy_type="moving_average_cross",
            name="잘못된 매개변수 전략",
            description="잘못된 매개변수 테스트",
            parameters={"wrong_param": 10}  # short_window, long_window가 없음
        )
        self.assertFalse(result)
        
        # 존재하지 않는 전략 업데이트 시도
        result = self.strategy_manager.update_strategy(
            strategy_id="non_existent_strategy",
            name="업데이트 실패 전략",
            description="존재하지 않는 전략 업데이트 테스트",
            parameters={}
        )
        self.assertFalse(result)
        
        # 존재하지 않는 전략 삭제 시도
        result = self.strategy_manager.delete_strategy("non_existent_strategy")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()