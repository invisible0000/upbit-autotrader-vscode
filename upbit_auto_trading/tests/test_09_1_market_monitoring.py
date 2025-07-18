"""
시장 모니터링 기능 테스트 모듈

이 모듈은 시장 모니터링 기능을 테스트합니다.
- 가격 알림 설정 기능 테스트
- 기술적 지표 알림 설정 기능 테스트
- 패턴 인식 알림 설정 기능 테스트
"""

import unittest
import os
import sys
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# 테스트 대상 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 테스트 대상 모듈 임포트
from upbit_auto_trading.business_logic.monitoring.market_monitor import MarketMonitor
from upbit_auto_trading.business_logic.monitoring.alert_condition import (
    PriceAlertCondition, 
    IndicatorAlertCondition, 
    PatternAlertCondition
)
from upbit_auto_trading.business_logic.monitoring.alert_manager import AlertManager
from upbit_auto_trading.ui.desktop.models.notification import NotificationType


class TestMarketMonitoring(unittest.TestCase):
    """시장 모니터링 기능 테스트 클래스"""
    
    def setUp(self):
        """각 테스트 전 설정"""
        print("\n=== 테스트 id 09_1_1: test_market_monitoring ===")
        
        # 테스트용 알림 관리자 생성
        self.alert_manager = AlertManager()
        
        # 테스트용 시장 모니터 생성
        self.market_monitor = MarketMonitor(self.alert_manager)
        
        # 테스트용 코인 심볼
        self.test_symbol = "KRW-BTC"
        
        # 테스트용 가격 데이터
        self.price_data = {
            "opening_price": 50000000,
            "high_price": 51000000,
            "low_price": 49000000,
            "trade_price": 50500000,
            "prev_closing_price": 49800000,
            "acc_trade_volume_24h": 100.0,
            "acc_trade_price_24h": 5000000000
        }
        
        # 테스트용 기술적 지표 데이터
        self.indicator_data = {
            "rsi_14": 65.5,
            "macd": 500000,
            "macd_signal": 450000,
            "bollinger_upper": 52000000,
            "bollinger_middle": 50000000,
            "bollinger_lower": 48000000
        }
    
    def test_price_alert_condition(self):
        """가격 알림 조건 테스트"""
        print("가격 알림 조건 테스트 시작")
        
        # 상승 가격 알림 조건 생성
        price_condition_above = PriceAlertCondition(
            symbol=self.test_symbol,
            price=50000000,
            is_above=True,
            name="BTC 5천만원 돌파 알림"
        )
        
        # 하락 가격 알림 조건 생성 (가격이 49000000원 이하일 때 알림)
        price_condition_below = PriceAlertCondition(
            symbol=self.test_symbol,
            price=49000000,
            is_above=False,
            name="BTC 4천9백만원 하락 알림"
        )
        
        # 조건 검사 (상승 조건 충족)
        self.assertTrue(price_condition_above.check_condition(self.price_data))
        print(f"상승 가격 알림 조건 충족 여부: {price_condition_above.check_condition(self.price_data)}")
        
        # 조건 검사 (하락 조건 미충족 - 현재 가격이 49000000 이하가 아니므로 False)
        result = price_condition_below.check_condition(self.price_data)
        self.assertFalse(result)
        print(f"하락 가격 알림 조건 충족 여부: {result}")
        
        # 가격 변경 후 조건 검사 (48000000원으로 변경하여 49000000원 이하 조건 충족)
        self.price_data["trade_price"] = 48000000
        result = price_condition_below.check_condition(self.price_data)
        self.assertTrue(result)
        print(f"가격 변경 후 하락 가격 알림 조건 충족 여부: {result}")
        
        print("가격 알림 조건 테스트 완료")
    
    def test_indicator_alert_condition(self):
        """기술적 지표 알림 조건 테스트"""
        print("기술적 지표 알림 조건 테스트 시작")
        
        # RSI 과매수 알림 조건 생성
        rsi_condition = IndicatorAlertCondition(
            symbol=self.test_symbol,
            indicator_name="rsi_14",
            threshold=70,
            comparison="<",
            name="BTC RSI 과매수 알림"
        )
        
        # MACD 골든크로스 알림 조건 생성
        macd_condition = IndicatorAlertCondition(
            symbol=self.test_symbol,
            indicator_name="macd",
            threshold="macd_signal",  # 다른 지표와 비교
            comparison=">",
            name="BTC MACD 골든크로스 알림"
        )
        
        # 조건 검사 (RSI 조건 충족)
        self.assertTrue(rsi_condition.check_condition(self.indicator_data))
        print(f"RSI 알림 조건 충족 여부: {rsi_condition.check_condition(self.indicator_data)}")
        
        # 조건 검사 (MACD 조건 충족)
        self.assertTrue(macd_condition.check_condition(self.indicator_data))
        print(f"MACD 알림 조건 충족 여부: {macd_condition.check_condition(self.indicator_data)}")
        
        # 지표 변경 후 조건 검사
        self.indicator_data["rsi_14"] = 75.0
        self.assertFalse(rsi_condition.check_condition(self.indicator_data))
        print(f"지표 변경 후 RSI 알림 조건 충족 여부: {rsi_condition.check_condition(self.indicator_data)}")
        
        print("기술적 지표 알림 조건 테스트 완료")
    
    def test_pattern_alert_condition(self):
        """패턴 인식 알림 조건 테스트"""
        print("패턴 인식 알림 조건 테스트 시작")
        
        # 테스트용 캔들 데이터 (상승 추세)
        uptrend_candles = [
            {"opening_price": 48000000, "trade_price": 49000000},
            {"opening_price": 49000000, "trade_price": 50000000},
            {"opening_price": 50000000, "trade_price": 51000000},
            {"opening_price": 51000000, "trade_price": 52000000},
            {"opening_price": 52000000, "trade_price": 53000000}
        ]
        
        # 테스트용 캔들 데이터 (하락 추세)
        downtrend_candles = [
            {"opening_price": 53000000, "trade_price": 52000000},
            {"opening_price": 52000000, "trade_price": 51000000},
            {"opening_price": 51000000, "trade_price": 50000000},
            {"opening_price": 50000000, "trade_price": 49000000},
            {"opening_price": 49000000, "trade_price": 48000000}
        ]
        
        # 상승 추세 패턴 알림 조건 생성
        uptrend_condition = PatternAlertCondition(
            symbol=self.test_symbol,
            pattern_type="uptrend",
            timeframe="1h",
            min_candles=5,
            name="BTC 상승 추세 알림"
        )
        
        # 하락 추세 패턴 알림 조건 생성
        downtrend_condition = PatternAlertCondition(
            symbol=self.test_symbol,
            pattern_type="downtrend",
            timeframe="1h",
            min_candles=5,
            name="BTC 하락 추세 알림"
        )
        
        # 조건 검사 (상승 추세 조건 충족)
        self.assertTrue(uptrend_condition.check_pattern(uptrend_candles))
        print(f"상승 추세 알림 조건 충족 여부: {uptrend_condition.check_pattern(uptrend_candles)}")
        
        # 조건 검사 (하락 추세 조건 충족)
        self.assertTrue(downtrend_condition.check_pattern(downtrend_candles))
        print(f"하락 추세 알림 조건 충족 여부: {downtrend_condition.check_pattern(downtrend_candles)}")
        
        # 잘못된 패턴 검사
        self.assertFalse(uptrend_condition.check_pattern(downtrend_candles))
        print(f"잘못된 패턴 검사 (상승 추세 조건 + 하락 추세 데이터): {uptrend_condition.check_pattern(downtrend_candles)}")
        
        print("패턴 인식 알림 조건 테스트 완료")
    
    def test_market_monitor_add_alert_condition(self):
        """시장 모니터 알림 조건 추가 테스트"""
        print("시장 모니터 알림 조건 추가 테스트 시작")
        
        # 가격 알림 조건 생성 및 추가
        price_condition = PriceAlertCondition(
            symbol=self.test_symbol,
            price=50000000,
            is_above=True,
            name="BTC 5천만원 돌파 알림"
        )
        
        condition_id = self.market_monitor.add_alert_condition(price_condition)
        self.assertIsNotNone(condition_id)
        print(f"추가된 가격 알림 조건 ID: {condition_id}")
        
        # 기술적 지표 알림 조건 생성 및 추가
        indicator_condition = IndicatorAlertCondition(
            symbol=self.test_symbol,
            indicator_name="rsi_14",
            threshold=70,
            comparison="<",
            name="BTC RSI 과매수 알림"
        )
        
        condition_id = self.market_monitor.add_alert_condition(indicator_condition)
        self.assertIsNotNone(condition_id)
        print(f"추가된 기술적 지표 알림 조건 ID: {condition_id}")
        
        # 패턴 알림 조건 생성 및 추가
        pattern_condition = PatternAlertCondition(
            symbol=self.test_symbol,
            pattern_type="uptrend",
            timeframe="1h",
            min_candles=5,
            name="BTC 상승 추세 알림"
        )
        
        condition_id = self.market_monitor.add_alert_condition(pattern_condition)
        self.assertIsNotNone(condition_id)
        print(f"추가된 패턴 알림 조건 ID: {condition_id}")
        
        # 알림 조건 목록 확인
        conditions = self.market_monitor.get_alert_conditions()
        self.assertEqual(len(conditions), 3)
        print(f"등록된 알림 조건 수: {len(conditions)}")
        
        print("시장 모니터 알림 조건 추가 테스트 완료")
    
    def test_market_monitor_check_conditions(self):
        """시장 모니터 조건 검사 테스트"""
        print("시장 모니터 조건 검사 테스트 시작")
        
        # 알림 관리자 모의 객체 설정
        mock_alert_manager = MagicMock()
        market_monitor = MarketMonitor(mock_alert_manager)
        
        # 가격 알림 조건 추가
        price_condition = PriceAlertCondition(
            symbol=self.test_symbol,
            price=50000000,
            is_above=True,
            name="BTC 5천만원 돌파 알림"
        )
        price_condition_id = market_monitor.add_alert_condition(price_condition)
        
        # 시장 데이터 업데이트 및 조건 검사
        market_data = {
            self.test_symbol: {
                "price_data": self.price_data,
                "indicator_data": self.indicator_data,
                "candle_data": []
            }
        }
        
        # 조건 검사 실행
        triggered_alerts = market_monitor.check_conditions(market_data)
        
        # 알림 발생 확인
        self.assertEqual(len(triggered_alerts), 1)
        self.assertEqual(triggered_alerts[0]["condition_id"], price_condition_id)
        print(f"발생한 알림 수: {len(triggered_alerts)}")
        print(f"알림 내용: {triggered_alerts[0]}")
        
        # 알림 관리자 호출 확인
        mock_alert_manager.add_notification.assert_called_once()
        call_args = mock_alert_manager.add_notification.call_args
        self.assertEqual(call_args[1]['notification_type'], NotificationType.PRICE_ALERT)
        print(f"알림 관리자 호출 확인: {call_args}")
        
        print("시장 모니터 조건 검사 테스트 완료")
    
    def test_alert_manager(self):
        """알림 관리자 테스트"""
        print("알림 관리자 테스트 시작")
        
        # 알림 추가
        notification = self.alert_manager.add_notification(
            notification_type=NotificationType.PRICE_ALERT,
            title="가격 알림",
            message="BTC 가격이 5천만원을 초과했습니다.",
            related_symbol=self.test_symbol
        )
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.type, NotificationType.PRICE_ALERT)
        self.assertEqual(notification.related_symbol, self.test_symbol)
        print(f"추가된 알림: {notification.title} - {notification.message}")
        
        # 알림 목록 조회
        notifications = self.alert_manager.get_notifications()
        self.assertEqual(len(notifications), 1)
        print(f"알림 목록 개수: {len(notifications)}")
        
        # 읽지 않은 알림 개수 확인
        unread_count = self.alert_manager.get_unread_count()
        self.assertEqual(unread_count, 1)
        print(f"읽지 않은 알림 개수: {unread_count}")
        
        # 알림 읽음 표시
        self.alert_manager.mark_as_read(notification.id)
        unread_count = self.alert_manager.get_unread_count()
        self.assertEqual(unread_count, 0)
        print(f"알림 읽음 표시 후 읽지 않은 알림 개수: {unread_count}")
        
        print("알림 관리자 테스트 완료")
    
    def test_save_load_alert_conditions(self):
        """알림 조건 저장 및 로드 테스트"""
        print("알림 조건 저장 및 로드 테스트 시작")
        
        # 가격 알림 조건 추가
        price_condition = PriceAlertCondition(
            symbol=self.test_symbol,
            price=50000000,
            is_above=True,
            name="BTC 5천만원 돌파 알림"
        )
        self.market_monitor.add_alert_condition(price_condition)
        
        # 기술적 지표 알림 조건 추가
        indicator_condition = IndicatorAlertCondition(
            symbol=self.test_symbol,
            indicator_name="rsi_14",
            threshold=70,
            comparison="<",
            name="BTC RSI 과매수 알림"
        )
        self.market_monitor.add_alert_condition(indicator_condition)
        
        # 알림 조건 저장
        temp_file = "./temp_alert_conditions.json"
        result = self.market_monitor.save_alert_conditions(temp_file)
        self.assertTrue(result)
        print(f"알림 조건 저장 완료: {temp_file}")
        
        # 새 시장 모니터 생성
        new_market_monitor = MarketMonitor(self.alert_manager)
        
        # 알림 조건 로드
        result = new_market_monitor.load_alert_conditions(temp_file)
        self.assertTrue(result)
        loaded_conditions = new_market_monitor.get_alert_conditions()
        
        # 로드된 조건 확인
        self.assertEqual(len(loaded_conditions), 2)
        print(f"로드된 알림 조건 수: {len(loaded_conditions)}")
        
        # 임시 파일 삭제
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        print("알림 조건 저장 및 로드 테스트 완료")


if __name__ == "__main__":
    unittest.main()