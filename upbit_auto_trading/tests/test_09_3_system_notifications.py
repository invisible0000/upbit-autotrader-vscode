"""
시스템 알림 기능 테스트 모듈

이 모듈은 시스템 알림 기능을 테스트합니다.
- 오류 알림 기능 테스트
- 시스템 상태 알림 기능 테스트
- 알림 설정 관리 기능 테스트
"""

import unittest
import os
import sys
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# 테스트 대상 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 테스트 대상 모듈 임포트
from upbit_auto_trading.business_logic.monitoring.system_monitor import SystemMonitor
from upbit_auto_trading.business_logic.monitoring.alert_manager import AlertManager
from upbit_auto_trading.ui.desktop.models.notification import NotificationType


class TestSystemNotifications(unittest.TestCase):
    """시스템 알림 기능 테스트 클래스"""
    
    def setUp(self):
        """각 테스트 전 설정"""
        print("\n=== 테스트 id 09_3_1: test_system_notifications ===")
        
        # 테스트용 알림 관리자 생성
        self.alert_manager = AlertManager()
        
        # 테스트용 시스템 모니터 생성
        self.system_monitor = SystemMonitor(self.alert_manager)
    
    def test_error_notification(self):
        """오류 알림 테스트"""
        print("오류 알림 테스트 시작")
        
        # 초기 알림 개수 확인
        notifications_before = self.alert_manager.get_notifications()
        print(f"초기 알림 개수: {len(notifications_before)}")
        
        # 오류 알림 생성
        error_message = "데이터베이스 연결 실패: Connection refused"
        self.system_monitor.notify_error("database", error_message, is_critical=True)
        
        # 알림 생성 확인
        notifications_after = self.alert_manager.get_notifications()
        print(f"오류 알림 생성 후 알림 개수: {len(notifications_after)}")
        
        # 알림 개수 확인
        self.assertEqual(len(notifications_after), 1)
        
        # 알림 내용 확인
        notification = notifications_after[0]
        self.assertEqual(notification.type, NotificationType.SYSTEM_ALERT)
        self.assertTrue("오류" in notification.title)
        print(f"생성된 알림: {notification.title} - {notification.message}")
        
        # 중요도가 낮은 오류 알림 생성
        warning_message = "API 응답 지연: 5초 초과"
        self.system_monitor.notify_error("api", warning_message, is_critical=False)
        
        # 알림 생성 확인
        notifications_after = self.alert_manager.get_notifications()
        print(f"경고 알림 생성 후 알림 개수: {len(notifications_after)}")
        
        # 알림 개수 확인
        self.assertEqual(len(notifications_after), 2)
        
        # 알림 내용 확인
        notification = notifications_after[0]
        self.assertEqual(notification.type, NotificationType.SYSTEM_ALERT)
        self.assertTrue("경고" in notification.title)
        print(f"생성된 알림: {notification.title} - {notification.message}")
        
        print("오류 알림 테스트 완료")
    
    def test_system_status_notification(self):
        """시스템 상태 알림 테스트"""
        print("시스템 상태 알림 테스트 시작")
        
        # 초기 알림 개수 확인
        notifications_before = self.alert_manager.get_notifications()
        print(f"초기 알림 개수: {len(notifications_before)}")
        
        # 시스템 상태 알림 생성
        status_message = "시스템이 정상적으로 시작되었습니다."
        self.system_monitor.notify_system_status("startup", status_message)
        
        # 알림 생성 확인
        notifications_after = self.alert_manager.get_notifications()
        print(f"상태 알림 생성 후 알림 개수: {len(notifications_after)}")
        
        # 알림 개수 확인
        self.assertEqual(len(notifications_after), 1)
        
        # 알림 내용 확인
        notification = notifications_after[0]
        self.assertEqual(notification.type, NotificationType.SYSTEM_ALERT)
        self.assertTrue("시스템 상태" in notification.title)
        print(f"생성된 알림: {notification.title} - {notification.message}")
        
        # 데이터베이스 백업 완료 알림 생성
        backup_message = "데이터베이스 백업이 완료되었습니다. 파일: backup_20250718.db"
        self.system_monitor.notify_system_status("database", backup_message)
        
        # 알림 생성 확인
        notifications_after = self.alert_manager.get_notifications()
        print(f"백업 알림 생성 후 알림 개수: {len(notifications_after)}")
        
        # 알림 개수 확인
        self.assertEqual(len(notifications_after), 2)
        
        # 알림 내용 확인
        notification = notifications_after[0]
        self.assertEqual(notification.type, NotificationType.SYSTEM_ALERT)
        print(f"생성된 알림: {notification.title} - {notification.message}")
        
        print("시스템 상태 알림 테스트 완료")
    
    def test_resource_monitoring(self):
        """리소스 모니터링 테스트"""
        print("리소스 모니터링 테스트 시작")
        
        # 초기 알림 개수 확인
        notifications_before = self.alert_manager.get_notifications()
        print(f"초기 알림 개수: {len(notifications_before)}")
        
        # CPU 사용량 임계값 설정
        self.system_monitor.set_cpu_threshold(80)
        
        # 메모리 사용량 임계값 설정
        self.system_monitor.set_memory_threshold(90)
        
        # 디스크 사용량 임계값 설정
        self.system_monitor.set_disk_threshold(95)
        
        # 임계값 설정 확인
        self.assertEqual(self.system_monitor.get_cpu_threshold(), 80)
        self.assertEqual(self.system_monitor.get_memory_threshold(), 90)
        self.assertEqual(self.system_monitor.get_disk_threshold(), 95)
        print("리소스 임계값 설정 완료")
        
        # CPU 사용량 알림 테스트
        self.system_monitor.check_cpu_usage(85)
        
        # 알림 생성 확인
        notifications_after = self.alert_manager.get_notifications()
        print(f"CPU 사용량 알림 생성 후 알림 개수: {len(notifications_after)}")
        
        # 알림 개수 확인
        self.assertEqual(len(notifications_after), 1)
        
        # 알림 내용 확인
        notification = notifications_after[0]
        self.assertEqual(notification.type, NotificationType.SYSTEM_ALERT)
        self.assertTrue("CPU" in notification.message)
        print(f"생성된 알림: {notification.title} - {notification.message}")
        
        # 메모리 사용량 알림 테스트
        self.system_monitor.check_memory_usage(95)
        
        # 알림 생성 확인
        notifications_after = self.alert_manager.get_notifications()
        print(f"메모리 사용량 알림 생성 후 알림 개수: {len(notifications_after)}")
        
        # 알림 개수 확인
        self.assertEqual(len(notifications_after), 2)
        
        # 알림 내용 확인
        notification = notifications_after[0]
        self.assertEqual(notification.type, NotificationType.SYSTEM_ALERT)
        self.assertTrue("메모리" in notification.message)
        print(f"생성된 알림: {notification.title} - {notification.message}")
        
        print("리소스 모니터링 테스트 완료")
    
    def test_notification_settings_management(self):
        """알림 설정 관리 테스트"""
        print("알림 설정 관리 테스트 시작")
        
        # 기본 설정 확인
        self.assertTrue(self.system_monitor.is_error_notification_enabled())
        self.assertTrue(self.system_monitor.is_status_notification_enabled())
        self.assertTrue(self.system_monitor.is_resource_notification_enabled())
        
        # 오류 알림 비활성화
        self.system_monitor.set_error_notification_enabled(False)
        self.assertFalse(self.system_monitor.is_error_notification_enabled())
        
        # 오류 알림 생성 시도
        error_message = "테스트 오류 메시지"
        self.system_monitor.notify_error("test", error_message, is_critical=True)
        
        # 알림이 생성되지 않았는지 확인
        notifications = self.alert_manager.get_notifications()
        self.assertEqual(len(notifications), 0)
        print("오류 알림 비활성화 테스트 완료")
        
        # 오류 알림 다시 활성화
        self.system_monitor.set_error_notification_enabled(True)
        self.assertTrue(self.system_monitor.is_error_notification_enabled())
        
        # 오류 알림 생성 시도
        self.system_monitor.notify_error("test", error_message, is_critical=True)
        
        # 알림이 생성되었는지 확인
        notifications = self.alert_manager.get_notifications()
        self.assertEqual(len(notifications), 1)
        print("오류 알림 활성화 테스트 완료")
        
        # 설정 저장 및 로드 테스트
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        # 설정 저장
        self.system_monitor.save_settings(temp_path)
        print(f"설정 저장 완료: {temp_path}")
        
        # 설정 변경
        self.system_monitor.set_error_notification_enabled(False)
        self.system_monitor.set_status_notification_enabled(False)
        self.system_monitor.set_resource_notification_enabled(False)
        
        # 설정 로드
        self.system_monitor.load_settings(temp_path)
        print("설정 로드 완료")
        
        # 설정 확인
        self.assertTrue(self.system_monitor.is_error_notification_enabled())
        self.assertTrue(self.system_monitor.is_status_notification_enabled())
        self.assertTrue(self.system_monitor.is_resource_notification_enabled())
        print("설정 로드 후 상태 확인 완료")
        
        # 임시 파일 삭제
        os.unlink(temp_path)
        
        print("알림 설정 관리 테스트 완료")
    
    def test_log_monitoring(self):
        """로그 모니터링 테스트"""
        print("로그 모니터링 테스트 시작")
        
        # 테스트용 로그 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
            temp_file.write("2025-07-18 12:00:00 INFO: 시스템 시작\n")
            temp_file.write("2025-07-18 12:01:00 INFO: 데이터베이스 연결 성공\n")
            temp_path = temp_file.name
        
        # 로그 모니터링 설정
        self.system_monitor.add_log_file_to_monitor(temp_path, ["ERROR", "CRITICAL"])
        
        # 초기 알림 개수 확인
        notifications_before = self.alert_manager.get_notifications()
        print(f"초기 알림 개수: {len(notifications_before)}")
        
        # 로그 파일에 오류 추가
        with open(temp_path, 'a') as f:
            f.write("2025-07-18 12:02:00 ERROR: 데이터베이스 쿼리 실패\n")
        
        # 로그 모니터링 실행
        self.system_monitor.check_log_files()
        
        # 알림 생성 확인
        notifications_after = self.alert_manager.get_notifications()
        print(f"로그 오류 발생 후 알림 개수: {len(notifications_after)}")
        
        # 알림 개수 확인
        self.assertEqual(len(notifications_after), 1)
        
        # 알림 내용 확인
        notification = notifications_after[0]
        self.assertEqual(notification.type, NotificationType.SYSTEM_ALERT)
        self.assertTrue("로그" in notification.title)
        print(f"생성된 알림: {notification.title} - {notification.message}")
        
        # 임시 파일 삭제
        os.unlink(temp_path)
        
        print("로그 모니터링 테스트 완료")


if __name__ == "__main__":
    unittest.main()