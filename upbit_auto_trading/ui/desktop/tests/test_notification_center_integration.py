"""
알림 센터 통합 테스트

이 모듈은 개선된 알림 센터 스크립트와의 통합 테스트를 포함합니다.
- 명령줄 인자 처리 테스트
- 알림 설정 함수 테스트
- 예외 처리 테스트
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import argparse

# 테스트 환경 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# 테스트 대상 모듈 임포트
from show_notification_center import parse_arguments, set_notifications, create_sample_notifications
from upbit_auto_trading.ui.desktop.screens.notification_center.notification_center import NotificationCenter


class TestNotificationCenterIntegration(unittest.TestCase):
    """알림 센터 통합 테스트 클래스"""

    def setUp(self):
        """각 테스트 전 설정"""
        print("\n=== 테스트 id 08_5_9: test_notification_center_integration ===")

    def test_argument_parsing(self):
        """명령줄 인자 파싱 테스트"""
        print("명령줄 인자 파싱 테스트 시작")
        
        # 기본 인자 테스트
        with patch('argparse.ArgumentParser.parse_args', 
                  return_value=argparse.Namespace(sample_count=5, read_status="all")):
            args = parse_arguments()
            self.assertEqual(args.sample_count, 5)
            self.assertEqual(args.read_status, "all")
        
        # 사용자 지정 인자 테스트
        with patch('argparse.ArgumentParser.parse_args', 
                  return_value=argparse.Namespace(sample_count=10, read_status="read")):
            args = parse_arguments()
            self.assertEqual(args.sample_count, 10)
            self.assertEqual(args.read_status, "read")
        
        print("명령줄 인자 파싱 테스트 완료")

    def test_set_notifications(self):
        """알림 설정 함수 테스트"""
        print("알림 설정 함수 테스트 시작")
        
        # 모의 알림 센터 객체 생성
        mock_notification_center = MagicMock(spec=NotificationCenter)
        mock_notification_list = MagicMock()
        mock_notification_center.notification_list = mock_notification_list
        
        # 샘플 알림 생성
        sample_notifications = create_sample_notifications(count=3)
        
        # 알림 설정 함수 호출
        set_notifications(mock_notification_center, sample_notifications)
        
        # 알림 목록에 알림이 설정되었는지 확인
        self.assertEqual(mock_notification_list.notifications, sample_notifications)
        
        # 내부 메서드가 호출되었는지 확인
        mock_notification_list._update_notification_widgets.assert_called_once()
        mock_notification_center._update_status.assert_called_once()
        
        print("알림 설정 함수 테스트 완료")

    def test_read_status_filter(self):
        """읽음 상태 필터 테스트"""
        print("읽음 상태 필터 테스트 시작")
        
        # 샘플 알림 생성
        notifications = create_sample_notifications(count=5)
        
        # 모든 알림이 기본적으로 읽지 않음 상태인지 확인
        for notification in notifications:
            self.assertFalse(notification.is_read)
        
        # 읽음 상태로 변경
        for notification in notifications:
            notification.is_read = True
        
        # 모든 알림이 읽음 상태인지 확인
        for notification in notifications:
            self.assertTrue(notification.is_read)
        
        print("읽음 상태 필터 테스트 완료")

    def test_exception_handling(self):
        """예외 처리 테스트"""
        print("예외 처리 테스트 시작")
        
        # 예외 발생 시뮬레이션
        with patch('show_notification_center.QApplication', side_effect=Exception("테스트 예외")):
            with patch('sys.exit') as mock_exit:
                with patch('builtins.print') as mock_print:
                    # main 함수 임포트 및 호출
                    from show_notification_center import main
                    main()
                    
                    # 예외 메시지가 출력되었는지 확인
                    mock_print.assert_called_with("애플리케이션 초기화 중 오류 발생: 테스트 예외")
                    
                    # sys.exit(1)이 호출되었는지 확인
                    mock_exit.assert_called_with(1)
        
        print("예외 처리 테스트 완료")


if __name__ == '__main__':
    unittest.main()