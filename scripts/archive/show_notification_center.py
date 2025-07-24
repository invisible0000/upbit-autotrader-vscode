"""
알림 센터 샘플 GUI 화면 출력 스크립트

이 스크립트는 알림 센터 UI를 테스트하기 위한 독립 실행형 애플리케이션입니다.
샘플 알림 데이터를 생성하고 알림 센터 화면에 표시합니다.

사용 방법:
    python show_notification_center.py [--sample-count 개수] [--read-status all|read|unread]
"""
import sys
import argparse
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QApplication

from upbit_auto_trading.ui.desktop.screens.notification_center.notification_center import NotificationCenter
from upbit_auto_trading.ui.desktop.models.notification import Notification, NotificationType

# 상수 정의
BTC_PRICE_THRESHOLD = 50_000_000  # 5천만원
ETH_PRICE_THRESHOLD = 3_000_000   # 3백만원
BTC_SYMBOL = "KRW-BTC"
ETH_SYMBOL = "KRW-ETH"


class NotificationFactory:
    """알림 생성 팩토리 클래스"""
    
    _next_id = 1
    
    @classmethod
    def create_price_alert(cls, symbol, price, is_above=True, timestamp=None):
        """가격 알림 생성"""
        message = f"{symbol} 가격이 {price:,}원을 초과했습니다." if is_above else f"{symbol} 가격이 {price:,}원을 미만으로 떨어졌습니다."
        return Notification(
            id=cls._get_next_id(),
            type=NotificationType.PRICE_ALERT,
            title="가격 알림",
            message=message,
            timestamp=timestamp or datetime.now(),
            is_read=False,
            related_symbol=symbol
        )
    
    @classmethod
    def create_trade_alert(cls, symbol, price, quantity, is_buy=True, timestamp=None):
        """거래 알림 생성"""
        trade_type = "매수" if is_buy else "매도"
        return Notification(
            id=cls._get_next_id(),
            type=NotificationType.TRADE_ALERT,
            title="거래 알림",
            message=f"{symbol} {trade_type} 주문이 체결되었습니다. 체결 가격: {price:,}원, 수량: {quantity} {symbol.split('-')[1]}",
            timestamp=timestamp or datetime.now(),
            is_read=False,
            related_symbol=symbol
        )
    
    @classmethod
    def create_system_alert(cls, message, timestamp=None):
        """시스템 알림 생성"""
        return Notification(
            id=cls._get_next_id(),
            type=NotificationType.SYSTEM_ALERT,
            title="시스템 알림",
            message=message,
            timestamp=timestamp or datetime.now(),
            is_read=False,
            related_symbol=None
        )
    
    @classmethod
    def _get_next_id(cls):
        """다음 ID 반환 및 증가"""
        current_id = cls._next_id
        cls._next_id += 1
        return current_id


def create_sample_notifications(count=5):
    """샘플 알림 데이터 생성"""
    now = datetime.now()
    
    # 기본 샘플 알림 정의
    samples = [
        (NotificationFactory.create_price_alert, [BTC_SYMBOL, BTC_PRICE_THRESHOLD], {"timestamp": now - timedelta(minutes=5)}),
        (NotificationFactory.create_trade_alert, [BTC_SYMBOL, 49500000, 0.01], {"timestamp": now - timedelta(minutes=10)}),
        (NotificationFactory.create_system_alert, ["데이터베이스 연결이 복구되었습니다."], {"timestamp": now - timedelta(hours=1)}),
        (NotificationFactory.create_price_alert, [ETH_SYMBOL, ETH_PRICE_THRESHOLD], {"is_above": False, "timestamp": now - timedelta(hours=2)}),
        (NotificationFactory.create_trade_alert, [ETH_SYMBOL, 3050000, 0.5], {"is_buy": False, "timestamp": now - timedelta(hours=3)})
    ]
    
    # 요청된 개수만큼 반환 (기본 샘플을 반복해서 사용)
    result = []
    for i in range(count):
        factory_func, args, kwargs = samples[i % len(samples)]
        notification = factory_func(*args, **kwargs)
        result.append(notification)
    
    return result


def parse_arguments():
    """명령줄 인자 파싱"""
    parser = argparse.ArgumentParser(description="알림 센터 샘플 GUI 화면 출력")
    parser.add_argument("--sample-count", type=int, default=5, help="생성할 샘플 알림 개수")
    parser.add_argument("--read-status", choices=["all", "read", "unread"], default="all", help="알림 읽음 상태 필터")
    return parser.parse_args()


def set_notifications(notification_center, notifications):
    """알림 센터에 알림 목록 설정"""
    notification_center.notification_list.notifications = notifications
    notification_center.notification_list._update_notification_widgets()
    notification_center._update_status()


def main():
    """메인 함수"""
    try:
        # 명령줄 인자 파싱
        args = parse_arguments()
        
        # QApplication 인스턴스 생성
        app = QApplication(sys.argv)
        
        # 알림 센터 인스턴스 생성
        notification_center = NotificationCenter()
        
        try:
            # 샘플 알림 데이터 생성
            sample_notifications = create_sample_notifications(count=args.sample_count)
            
            # 읽음 상태 필터 적용
            if args.read_status == "read":
                for notification in sample_notifications:
                    notification.is_read = True
            elif args.read_status == "unread":
                for notification in sample_notifications:
                    notification.is_read = False
            
            # 알림 목록에 샘플 알림 추가
            set_notifications(notification_center, sample_notifications)
            
            # 알림 센터 표시
            notification_center.show()
            
            # 애플리케이션 실행
            sys.exit(app.exec())
        except Exception as e:
            print(f"알림 센터 실행 중 오류 발생: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"애플리케이션 초기화 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()