#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
데이터베이스 통합 테스트
"""

import os
import unittest
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from upbit_auto_trading.data_layer.models import Base, OHLCV, Strategy, OrderBook, Trade
from upbit_auto_trading.data_layer.storage.database_manager import DatabaseManager, get_database_manager

class TestDatabase(unittest.TestCase):
    """데이터베이스 통합 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        # 임시 데이터베이스 파일 생성
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.db")
        
        # 테스트용 설정
        self.config = {
            'database': {
                'type': 'sqlite',
                'path': self.db_path
            }
        }
        
        # 데이터베이스 관리자 생성
        self.db_manager = DatabaseManager(config=self.config)
        
        # 데이터베이스 초기화
        self.db_manager.initialize_database()
        
        # 세션 생성
        self.session = self.db_manager.get_session()
    
    def tearDown(self):
        """테스트 정리"""
        # 세션 닫기
        self.session.close()
        
        # 데이터베이스 연결 정리
        self.db_manager.cleanup_database()
        
        # 임시 디렉토리 삭제
        self.temp_dir.cleanup()
    
    def test_create_and_query_ohlcv(self):
        """OHLCV 데이터 생성 및 조회 테스트"""
        # 테스트 데이터 생성
        now = datetime.utcnow()
        ohlcv_data = [
            OHLCV(
                timestamp=now - timedelta(minutes=i),
                symbol="KRW-BTC",
                open=50000000.0 + i * 1000,
                high=51000000.0 + i * 1000,
                low=49000000.0 + i * 1000,
                close=50500000.0 + i * 1000,
                volume=10.0 + i * 0.1,
                timeframe="1m"
            )
            for i in range(5)
        ]
        
        # 데이터 저장
        self.session.add_all(ohlcv_data)
        self.session.commit()
        
        # 데이터 조회
        result = self.session.query(OHLCV).filter(
            OHLCV.symbol == "KRW-BTC",
            OHLCV.timeframe == "1m"
        ).order_by(OHLCV.timestamp.desc()).all()
        
        # 검증
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0].symbol, "KRW-BTC")
        self.assertEqual(result[0].timeframe, "1m")
        self.assertEqual(result[0].open, 50000000.0)
        self.assertEqual(result[0].high, 51000000.0)
        self.assertEqual(result[0].low, 49000000.0)
        self.assertEqual(result[0].close, 50500000.0)
        self.assertEqual(result[0].volume, 10.0)
    
    def test_create_and_query_strategy(self):
        """전략 데이터 생성 및 조회 테스트"""
        # 테스트 데이터 생성
        strategy = Strategy(
            id="test-strategy-1",
            name="테스트 전략",
            description="테스트용 전략입니다.",
            parameters={
                "strategy_type": "moving_average_crossover",
                "params": {
                    "short_window": 20,
                    "long_window": 50,
                    "signal_line": 9
                }
            }
        )
        
        # 데이터 저장
        self.session.add(strategy)
        self.session.commit()
        
        # 데이터 조회
        result = self.session.query(Strategy).filter(
            Strategy.id == "test-strategy-1"
        ).first()
        
        # 검증
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "test-strategy-1")
        self.assertEqual(result.name, "테스트 전략")
        self.assertEqual(result.description, "테스트용 전략입니다.")
        self.assertEqual(result.parameters["strategy_type"], "moving_average_crossover")
        self.assertEqual(result.parameters["params"]["short_window"], 20)
        self.assertEqual(result.parameters["params"]["long_window"], 50)
        self.assertEqual(result.parameters["params"]["signal_line"], 9)
    
    def test_database_manager(self):
        """데이터베이스 관리자 테스트"""
        # 엔진 및 세션 팩토리 검증
        self.assertIsNotNone(self.db_manager.get_engine())
        self.assertIsNotNone(self.db_manager.get_session())
        
        # 새 세션 생성 검증
        new_session = self.db_manager.get_session()
        self.assertIsNotNone(new_session)
        new_session.close()

    def test_create_and_query_orderbook(self):
        """호가 데이터 생성 및 조회 테스트"""
        # 테스트 데이터 생성
        now = datetime.utcnow()
        orderbook = OrderBook(
            timestamp=now,
            symbol="KRW-BTC",
            asks=[
                {"price": 51000000.0, "size": 0.5},
                {"price": 51100000.0, "size": 0.3}
            ],
            bids=[
                {"price": 50900000.0, "size": 0.7},
                {"price": 50800000.0, "size": 0.4}
            ]
        )
        
        # 데이터 저장
        self.session.add(orderbook)
        self.session.commit()
        
        # 데이터 조회
        result = self.session.query(OrderBook).filter(
            OrderBook.symbol == "KRW-BTC"
        ).order_by(OrderBook.timestamp.desc()).first()
        
        # 검증
        self.assertIsNotNone(result)
        self.assertEqual(result.symbol, "KRW-BTC")
        self.assertEqual(len(result.asks), 2)
        self.assertEqual(len(result.bids), 2)
        self.assertEqual(result.asks[0]["price"], 51000000.0)
        self.assertEqual(result.asks[0]["size"], 0.5)
        self.assertEqual(result.bids[0]["price"], 50900000.0)
        self.assertEqual(result.bids[0]["size"], 0.7)
    
    def test_create_and_query_trade(self):
        """거래 데이터 생성 및 조회 테스트"""
        # 테스트 데이터 생성
        now = datetime.utcnow()
        trade = Trade(
            timestamp=now,
            symbol="KRW-BTC",
            price=50500000.0,
            quantity=0.01,
            side="buy",
            fee=0.05
        )
        
        # 데이터 저장
        self.session.add(trade)
        self.session.commit()
        
        # 데이터 조회
        result = self.session.query(Trade).filter(
            Trade.symbol == "KRW-BTC"
        ).order_by(Trade.timestamp.desc()).first()
        
        # 검증
        self.assertIsNotNone(result)
        self.assertEqual(result.symbol, "KRW-BTC")
        self.assertEqual(result.price, 50500000.0)
        self.assertEqual(result.quantity, 0.01)
        self.assertEqual(result.side, "buy")
        self.assertEqual(result.fee, 0.05)
    
    @patch('upbit_auto_trading.data_layer.storage.database_manager.get_database_manager')
    def test_singleton_pattern(self, mock_get_db_manager):
        """싱글톤 패턴 테스트"""
        # 모의 객체 설정
        mock_instance = MagicMock()
        mock_get_db_manager.return_value = mock_instance
        
        # 첫 번째 호출
        db_manager1 = get_database_manager()
        
        # 두 번째 호출
        db_manager2 = get_database_manager()
        
        # 동일한 인스턴스인지 확인
        self.assertEqual(db_manager1, db_manager2)
        self.assertEqual(mock_get_db_manager.call_count, 1)

if __name__ == '__main__':
    unittest.main()