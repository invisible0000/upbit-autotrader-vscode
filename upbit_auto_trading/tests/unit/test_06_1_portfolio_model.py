#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
포트폴리오 모델 및 기본 기능 테스트

이 테스트 모듈은 포트폴리오 데이터 모델과 기본 기능을 검증합니다.
- 포트폴리오 생성 및 관리 기능
- 코인 추가/제거 기능
"""

import unittest
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from upbit_auto_trading.data_layer.models import Base, Portfolio, PortfolioCoin, Strategy
from upbit_auto_trading.business_logic.portfolio.portfolio_manager import PortfolioManager


class TestPortfolioModel(unittest.TestCase):
    """포트폴리오 모델 및 기본 기능 테스트 클래스"""

    def setUp(self):
        """테스트 환경 설정"""
        # 인메모리 SQLite 데이터베이스 생성
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        
        # 세션 생성
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # 테스트용 전략 생성
        self.strategy1 = Strategy(
            id=str(uuid.uuid4()),
            name="테스트 전략 1",
            description="테스트용 전략 1",
            parameters={"param1": "value1"}
        )
        
        self.strategy2 = Strategy(
            id=str(uuid.uuid4()),
            name="테스트 전략 2",
            description="테스트용 전략 2",
            parameters={"param2": "value2"}
        )
        
        self.session.add_all([self.strategy1, self.strategy2])
        self.session.commit()
        
        # 포트폴리오 매니저 생성
        self.portfolio_manager = PortfolioManager(self.session)
        
        print("=== 테스트 id 06_1_1: test_create_portfolio ===")
        print("=== 테스트 id 06_1_2: test_add_coin_to_portfolio ===")
        print("=== 테스트 id 06_1_3: test_remove_coin_from_portfolio ===")
        print("=== 테스트 id 06_1_4: test_update_portfolio ===")
        print("=== 테스트 id 06_1_5: test_get_portfolio ===")
        print("=== 테스트 id 06_1_6: test_get_all_portfolios ===")
        print("=== 테스트 id 06_1_7: test_delete_portfolio ===")
        print("=== 테스트 id 06_1_8: test_validate_portfolio_weights ===")

    def tearDown(self):
        """테스트 환경 정리"""
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_create_portfolio(self):
        """포트폴리오 생성 테스트"""
        print("\n[테스트 시작] 포트폴리오 생성 테스트")
        
        # 포트폴리오 생성
        portfolio_id = self.portfolio_manager.create_portfolio(
            name="테스트 포트폴리오",
            description="테스트용 포트폴리오입니다."
        )
        
        # 생성된 포트폴리오 조회
        portfolio = self.session.query(Portfolio).filter_by(id=portfolio_id).first()
        
        # 검증
        self.assertIsNotNone(portfolio)
        self.assertEqual(portfolio.name, "테스트 포트폴리오")
        self.assertEqual(portfolio.description, "테스트용 포트폴리오입니다.")
        self.assertIsInstance(portfolio.created_at, datetime)
        self.assertIsInstance(portfolio.updated_at, datetime)
        
        print(f"생성된 포트폴리오 ID: {portfolio_id}")
        print(f"포트폴리오 이름: {portfolio.name}")
        print(f"포트폴리오 설명: {portfolio.description}")
        print(f"생성 시간: {portfolio.created_at}")
        print("[테스트 완료] 포트폴리오 생성 테스트 성공")

    def test_add_coin_to_portfolio(self):
        """포트폴리오에 코인 추가 테스트"""
        print("\n[테스트 시작] 포트폴리오에 코인 추가 테스트")
        
        # 포트폴리오 생성
        portfolio_id = self.portfolio_manager.create_portfolio(
            name="코인 추가 테스트 포트폴리오",
            description="코인 추가 테스트용 포트폴리오입니다."
        )
        
        # 코인 추가
        self.portfolio_manager.add_coin_to_portfolio(
            portfolio_id=portfolio_id,
            symbol="KRW-BTC",
            strategy_id=self.strategy1.id,
            weight=0.6
        )
        
        self.portfolio_manager.add_coin_to_portfolio(
            portfolio_id=portfolio_id,
            symbol="KRW-ETH",
            strategy_id=self.strategy2.id,
            weight=0.4
        )
        
        # 포트폴리오 조회
        portfolio = self.session.query(Portfolio).filter_by(id=portfolio_id).first()
        
        # 검증
        self.assertEqual(len(portfolio.coins), 2)
        
        # 코인 정보 검증
        coins = {coin.symbol: coin for coin in portfolio.coins}
        
        self.assertIn("KRW-BTC", coins)
        self.assertEqual(coins["KRW-BTC"].weight, 0.6)
        self.assertEqual(coins["KRW-BTC"].strategy_id, self.strategy1.id)
        
        self.assertIn("KRW-ETH", coins)
        self.assertEqual(coins["KRW-ETH"].weight, 0.4)
        self.assertEqual(coins["KRW-ETH"].strategy_id, self.strategy2.id)
        
        print(f"포트폴리오 ID: {portfolio_id}")
        print(f"추가된 코인 수: {len(portfolio.coins)}")
        for coin in portfolio.coins:
            print(f"코인: {coin.symbol}, 가중치: {coin.weight}, 전략: {coin.strategy.name}")
        print("[테스트 완료] 포트폴리오에 코인 추가 테스트 성공")

    def test_remove_coin_from_portfolio(self):
        """포트폴리오에서 코인 제거 테스트"""
        print("\n[테스트 시작] 포트폴리오에서 코인 제거 테스트")
        
        # 포트폴리오 생성
        portfolio_id = self.portfolio_manager.create_portfolio(
            name="코인 제거 테스트 포트폴리오",
            description="코인 제거 테스트용 포트폴리오입니다."
        )
        
        # 코인 추가
        self.portfolio_manager.add_coin_to_portfolio(
            portfolio_id=portfolio_id,
            symbol="KRW-BTC",
            strategy_id=self.strategy1.id,
            weight=0.5
        )
        
        self.portfolio_manager.add_coin_to_portfolio(
            portfolio_id=portfolio_id,
            symbol="KRW-ETH",
            strategy_id=self.strategy2.id,
            weight=0.5
        )
        
        # 코인 제거 전 확인
        portfolio_before = self.session.query(Portfolio).filter_by(id=portfolio_id).first()
        self.assertEqual(len(portfolio_before.coins), 2)
        print(f"제거 전 코인 수: {len(portfolio_before.coins)}")
        
        # 코인 제거
        result = self.portfolio_manager.remove_coin_from_portfolio(
            portfolio_id=portfolio_id,
            symbol="KRW-BTC"
        )
        
        # 검증
        self.assertTrue(result)
        
        # 포트폴리오 재조회
        portfolio_after = self.session.query(Portfolio).filter_by(id=portfolio_id).first()
        self.assertEqual(len(portfolio_after.coins), 1)
        self.assertEqual(portfolio_after.coins[0].symbol, "KRW-ETH")
        
        print(f"제거 후 코인 수: {len(portfolio_after.coins)}")
        print(f"남은 코인: {portfolio_after.coins[0].symbol}")
        print("[테스트 완료] 포트폴리오에서 코인 제거 테스트 성공")

    def test_update_portfolio(self):
        """포트폴리오 정보 업데이트 테스트"""
        print("\n[테스트 시작] 포트폴리오 정보 업데이트 테스트")
        
        # 포트폴리오 생성
        portfolio_id = self.portfolio_manager.create_portfolio(
            name="업데이트 전 포트폴리오",
            description="업데이트 전 설명"
        )
        
        # 업데이트 전 정보 확인
        portfolio_before = self.session.query(Portfolio).filter_by(id=portfolio_id).first()
        print(f"업데이트 전 이름: {portfolio_before.name}")
        print(f"업데이트 전 설명: {portfolio_before.description}")
        
        # 포트폴리오 정보 업데이트
        result = self.portfolio_manager.update_portfolio(
            portfolio_id=portfolio_id,
            name="업데이트 후 포트폴리오",
            description="업데이트 후 설명"
        )
        
        # 검증
        self.assertTrue(result)
        
        # 업데이트 후 정보 확인
        portfolio_after = self.session.query(Portfolio).filter_by(id=portfolio_id).first()
        self.assertEqual(portfolio_after.name, "업데이트 후 포트폴리오")
        self.assertEqual(portfolio_after.description, "업데이트 후 설명")
        
        print(f"업데이트 후 이름: {portfolio_after.name}")
        print(f"업데이트 후 설명: {portfolio_after.description}")
        print("[테스트 완료] 포트폴리오 정보 업데이트 테스트 성공")

    def test_get_portfolio(self):
        """포트폴리오 조회 테스트"""
        print("\n[테스트 시작] 포트폴리오 조회 테스트")
        
        # 포트폴리오 생성
        portfolio_id = self.portfolio_manager.create_portfolio(
            name="조회 테스트 포트폴리오",
            description="조회 테스트용 포트폴리오입니다."
        )
        
        # 코인 추가
        self.portfolio_manager.add_coin_to_portfolio(
            portfolio_id=portfolio_id,
            symbol="KRW-BTC",
            strategy_id=self.strategy1.id,
            weight=0.7
        )
        
        self.portfolio_manager.add_coin_to_portfolio(
            portfolio_id=portfolio_id,
            symbol="KRW-ETH",
            strategy_id=self.strategy2.id,
            weight=0.3
        )
        
        # 포트폴리오 조회
        portfolio_data = self.portfolio_manager.get_portfolio(portfolio_id)
        
        # 검증
        self.assertIsNotNone(portfolio_data)
        self.assertEqual(portfolio_data["id"], portfolio_id)
        self.assertEqual(portfolio_data["name"], "조회 테스트 포트폴리오")
        self.assertEqual(portfolio_data["description"], "조회 테스트용 포트폴리오입니다.")
        self.assertEqual(len(portfolio_data["coins"]), 2)
        
        # 코인 정보 검증
        coins = {coin["symbol"]: coin for coin in portfolio_data["coins"]}
        
        self.assertIn("KRW-BTC", coins)
        self.assertEqual(coins["KRW-BTC"]["weight"], 0.7)
        self.assertEqual(coins["KRW-BTC"]["strategy_id"], self.strategy1.id)
        
        self.assertIn("KRW-ETH", coins)
        self.assertEqual(coins["KRW-ETH"]["weight"], 0.3)
        self.assertEqual(coins["KRW-ETH"]["strategy_id"], self.strategy2.id)
        
        print(f"조회된 포트폴리오 ID: {portfolio_data['id']}")
        print(f"포트폴리오 이름: {portfolio_data['name']}")
        print(f"포트폴리오 설명: {portfolio_data['description']}")
        print(f"포트폴리오 코인 수: {len(portfolio_data['coins'])}")
        for coin in portfolio_data["coins"]:
            print(f"코인: {coin['symbol']}, 가중치: {coin['weight']}, 전략 ID: {coin['strategy_id']}")
        print("[테스트 완료] 포트폴리오 조회 테스트 성공")

    def test_get_all_portfolios(self):
        """모든 포트폴리오 조회 테스트"""
        print("\n[테스트 시작] 모든 포트폴리오 조회 테스트")
        
        # 여러 포트폴리오 생성
        portfolio_id1 = self.portfolio_manager.create_portfolio(
            name="포트폴리오 1",
            description="첫 번째 포트폴리오"
        )
        
        portfolio_id2 = self.portfolio_manager.create_portfolio(
            name="포트폴리오 2",
            description="두 번째 포트폴리오"
        )
        
        portfolio_id3 = self.portfolio_manager.create_portfolio(
            name="포트폴리오 3",
            description="세 번째 포트폴리오"
        )
        
        # 모든 포트폴리오 조회
        portfolios = self.portfolio_manager.get_all_portfolios()
        
        # 검증
        self.assertEqual(len(portfolios), 3)
        
        # 포트폴리오 ID 검증
        portfolio_ids = [p["id"] for p in portfolios]
        self.assertIn(portfolio_id1, portfolio_ids)
        self.assertIn(portfolio_id2, portfolio_ids)
        self.assertIn(portfolio_id3, portfolio_ids)
        
        print(f"조회된 포트폴리오 수: {len(portfolios)}")
        for portfolio in portfolios:
            print(f"포트폴리오 ID: {portfolio['id']}, 이름: {portfolio['name']}")
        print("[테스트 완료] 모든 포트폴리오 조회 테스트 성공")

    def test_delete_portfolio(self):
        """포트폴리오 삭제 테스트"""
        print("\n[테스트 시작] 포트폴리오 삭제 테스트")
        
        # 포트폴리오 생성
        portfolio_id = self.portfolio_manager.create_portfolio(
            name="삭제 테스트 포트폴리오",
            description="삭제 테스트용 포트폴리오입니다."
        )
        
        # 코인 추가
        self.portfolio_manager.add_coin_to_portfolio(
            portfolio_id=portfolio_id,
            symbol="KRW-BTC",
            strategy_id=self.strategy1.id,
            weight=1.0
        )
        
        # 삭제 전 확인
        portfolio_before = self.session.query(Portfolio).filter_by(id=portfolio_id).first()
        self.assertIsNotNone(portfolio_before)
        print(f"삭제 전 포트폴리오 존재 여부: {portfolio_before is not None}")
        
        # 포트폴리오 삭제
        result = self.portfolio_manager.delete_portfolio(portfolio_id)
        
        # 검증
        self.assertTrue(result)
        
        # 삭제 후 확인
        portfolio_after = self.session.query(Portfolio).filter_by(id=portfolio_id).first()
        self.assertIsNone(portfolio_after)
        
        # 연결된 코인도 삭제되었는지 확인
        coins = self.session.query(PortfolioCoin).filter_by(portfolio_id=portfolio_id).all()
        self.assertEqual(len(coins), 0)
        
        print(f"삭제 후 포트폴리오 존재 여부: {portfolio_after is not None}")
        print(f"삭제 후 연결된 코인 수: {len(coins)}")
        print("[테스트 완료] 포트폴리오 삭제 테스트 성공")

    def test_validate_portfolio_weights(self):
        """포트폴리오 가중치 검증 테스트"""
        print("\n[테스트 시작] 포트폴리오 가중치 검증 테스트")
        
        # 포트폴리오 생성
        portfolio_id = self.portfolio_manager.create_portfolio(
            name="가중치 검증 테스트 포트폴리오",
            description="가중치 검증 테스트용 포트폴리오입니다."
        )
        
        # 유효한 가중치로 코인 추가
        self.portfolio_manager.add_coin_to_portfolio(
            portfolio_id=portfolio_id,
            symbol="KRW-BTC",
            strategy_id=self.strategy1.id,
            weight=0.6
        )
        
        self.portfolio_manager.add_coin_to_portfolio(
            portfolio_id=portfolio_id,
            symbol="KRW-ETH",
            strategy_id=self.strategy2.id,
            weight=0.4
        )
        
        # 가중치 검증
        is_valid = self.portfolio_manager.validate_portfolio_weights(portfolio_id)
        self.assertTrue(is_valid)
        print(f"유효한 가중치(합계=1.0) 검증 결과: {is_valid}")
        
        # 유효하지 않은 가중치로 업데이트
        self.portfolio_manager.update_coin_weight(
            portfolio_id=portfolio_id,
            symbol="KRW-BTC",
            weight=0.7
        )
        
        # 가중치 검증
        is_valid = self.portfolio_manager.validate_portfolio_weights(portfolio_id)
        self.assertFalse(is_valid)
        print(f"유효하지 않은 가중치(합계=1.1) 검증 결과: {is_valid}")
        
        # 가중치 조정
        self.portfolio_manager.update_coin_weight(
            portfolio_id=portfolio_id,
            symbol="KRW-ETH",
            weight=0.3
        )
        
        # 가중치 재검증
        is_valid = self.portfolio_manager.validate_portfolio_weights(portfolio_id)
        self.assertTrue(is_valid)
        print(f"조정 후 가중치(합계=1.0) 검증 결과: {is_valid}")
        print("[테스트 완료] 포트폴리오 가중치 검증 테스트 성공")


if __name__ == '__main__':
    unittest.main()