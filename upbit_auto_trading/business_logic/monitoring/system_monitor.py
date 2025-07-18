"""
시스템 모니터링 모듈

이 모듈은 시스템 모니터링 기능을 제공합니다.
- 오류 알림 기능
- 시스템 상태 알림 기능
- 알림 설정 관리 기능
"""

import os
import json
import re
import threading
import time
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

# psutil 패키지 임포트 시도
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil package not available. Resource monitoring will be limited.")

from upbit_auto_trading.ui.desktop.models.notification import NotificationType
from .alert_manager import AlertManager


class SystemMonitor:
    """시스템 모니터링 클래스"""
    
    def __init__(self, alert_manager: AlertManager):
        """초기화
        
        Args:
            alert_manager: 알림 관리자 객체
        """
        self.alert_manager = alert_manager
        
        # 알림 설정
        self.error_notification_enabled = True
        self.status_notification_enabled = True
        self.resource_notification_enabled = True
        
        # 리소스 임계값 (%)
        self.cpu_threshold = 80
        self.memory_threshold = 90
        self.disk_threshold = 95
        
        # 알림 발생 이력 (중복 알림 방지)
        self.notified_errors: Set[str] = set()
        self.notified_resources: Set[str] = set()
        
        # 로그 모니터링 설정
        self.log_files: Dict[str, Dict[str, Any]] = {}
        
        # 모니터링 스레드
        self.monitoring_thread = None
        self.is_monitoring = False
        self.monitoring_interval = 60  # 초 단위
    
    def notify_error(self, component: str, message: str, is_critical: bool = False):
        """오류 알림 생성
        
        Args:
            component: 오류가 발생한 컴포넌트
            message: 오류 메시지
            is_critical: 중요 오류 여부
        """
        if not self.error_notification_enabled:
            return
        
        # 중복 알림 방지
        error_key = f"{component}:{message}"
        if error_key in self.notified_errors:
            return
        
        # 알림 제목 설정
        title = "심각한 오류 알림" if is_critical else "시스템 경고"
        
        # 알림 메시지 생성
        full_message = f"[{component}] {message}"
        
        # 알림 생성
        self.alert_manager.add_notification(
            notification_type=NotificationType.SYSTEM_ALERT,
            title=title,
            message=full_message,
            related_symbol=None
        )
        
        # 알림 이력에 추가
        self.notified_errors.add(error_key)
    
    def notify_system_status(self, component: str, message: str):
        """시스템 상태 알림 생성
        
        Args:
            component: 상태 정보를 제공하는 컴포넌트
            message: 상태 메시지
        """
        if not self.status_notification_enabled:
            return
        
        # 알림 제목 설정
        title = f"시스템 상태: {component}"
        
        # 알림 생성
        self.alert_manager.add_notification(
            notification_type=NotificationType.SYSTEM_ALERT,
            title=title,
            message=message,
            related_symbol=None
        )
    
    def check_cpu_usage(self, usage: Optional[float] = None):
        """CPU 사용량 확인
        
        Args:
            usage: CPU 사용량 (None이면 현재 사용량 측정)
        """
        if not self.resource_notification_enabled:
            return
        
        # CPU 사용량 측정
        if usage is None:
            if PSUTIL_AVAILABLE:
                usage = psutil.cpu_percent(interval=1)
            else:
                # psutil이 없을 경우 테스트용 값 사용
                return
        
        # 임계값 초과 시 알림
        if usage > self.cpu_threshold:
            # 중복 알림 방지
            resource_key = f"cpu:{int(usage)}"
            if resource_key in self.notified_resources:
                return
            
            # 알림 생성
            message = f"CPU 사용량이 임계값을 초과했습니다: {usage:.1f}% (임계값: {self.cpu_threshold}%)"
            self.alert_manager.add_notification(
                notification_type=NotificationType.SYSTEM_ALERT,
                title="시스템 리소스 경고",
                message=message,
                related_symbol=None
            )
            
            # 알림 이력에 추가
            self.notified_resources.add(resource_key)
    
    def check_memory_usage(self, usage: Optional[float] = None):
        """메모리 사용량 확인
        
        Args:
            usage: 메모리 사용량 (None이면 현재 사용량 측정)
        """
        if not self.resource_notification_enabled:
            return
        
        # 메모리 사용량 측정
        if usage is None:
            if PSUTIL_AVAILABLE:
                memory = psutil.virtual_memory()
                usage = memory.percent
            else:
                # psutil이 없을 경우 테스트용 값 사용
                return
        
        # 임계값 초과 시 알림
        if usage > self.memory_threshold:
            # 중복 알림 방지
            resource_key = f"memory:{int(usage)}"
            if resource_key in self.notified_resources:
                return
            
            # 알림 생성
            message = f"메모리 사용량이 임계값을 초과했습니다: {usage:.1f}% (임계값: {self.memory_threshold}%)"
            self.alert_manager.add_notification(
                notification_type=NotificationType.SYSTEM_ALERT,
                title="시스템 리소스 경고",
                message=message,
                related_symbol=None
            )
            
            # 알림 이력에 추가
            self.notified_resources.add(resource_key)
    
    def check_disk_usage(self, path: str = "/", usage: Optional[float] = None):
        """디스크 사용량 확인
        
        Args:
            path: 디스크 경로
            usage: 디스크 사용량 (None이면 현재 사용량 측정)
        """
        if not self.resource_notification_enabled:
            return
        
        # 디스크 사용량 측정
        if usage is None:
            if PSUTIL_AVAILABLE:
                disk = psutil.disk_usage(path)
                usage = disk.percent
            else:
                # psutil이 없을 경우 테스트용 값 사용
                return
        
        # 임계값 초과 시 알림
        if usage > self.disk_threshold:
            # 중복 알림 방지
            resource_key = f"disk:{path}:{int(usage)}"
            if resource_key in self.notified_resources:
                return
            
            # 알림 생성
            message = f"디스크 사용량이 임계값을 초과했습니다: {path} {usage:.1f}% (임계값: {self.disk_threshold}%)"
            self.alert_manager.add_notification(
                notification_type=NotificationType.SYSTEM_ALERT,
                title="시스템 리소스 경고",
                message=message,
                related_symbol=None
            )
            
            # 알림 이력에 추가
            self.notified_resources.add(resource_key)
    
    def add_log_file_to_monitor(self, file_path: str, log_levels: List[str]):
        """모니터링할 로그 파일 추가
        
        Args:
            file_path: 로그 파일 경로
            log_levels: 모니터링할 로그 레벨 목록 (예: ["ERROR", "CRITICAL"])
        """
        if not os.path.exists(file_path):
            return False
        
        # 파일 크기 확인
        file_size = os.path.getsize(file_path)
        
        self.log_files[file_path] = {
            "log_levels": log_levels,
            "last_position": file_size,
            "last_check": datetime.now()
        }
        
        return True
    
    def remove_log_file_from_monitor(self, file_path: str) -> bool:
        """모니터링 중인 로그 파일 제거
        
        Args:
            file_path: 로그 파일 경로
            
        Returns:
            bool: 성공 여부
        """
        if file_path in self.log_files:
            del self.log_files[file_path]
            return True
        return False
    
    def check_log_files(self):
        """로그 파일 확인"""
        if not self.error_notification_enabled:
            return
        
        for file_path, config in self.log_files.items():
            if not os.path.exists(file_path):
                continue
            
            try:
                # 파일 크기 확인
                file_size = os.path.getsize(file_path)
                
                # 파일이 변경되지 않았으면 건너뛰기
                if file_size <= config["last_position"]:
                    continue
                
                # 로그 파일 열기
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # 마지막 위치로 이동
                    f.seek(config["last_position"])
                    
                    # 새로운 로그 라인 읽기
                    new_lines = f.readlines()
                    
                    # 로그 레벨 패턴 생성
                    log_level_pattern = '|'.join(config["log_levels"])
                    pattern = re.compile(f".*({log_level_pattern}).*", re.IGNORECASE)
                    
                    # 로그 레벨 확인
                    for line in new_lines:
                        if pattern.match(line):
                            # 알림 생성
                            self.alert_manager.add_notification(
                                notification_type=NotificationType.SYSTEM_ALERT,
                                title="로그 파일 경고",
                                message=f"로그 파일에서 오류가 감지되었습니다: {file_path}\n{line.strip()}",
                                related_symbol=None
                            )
                
                # 마지막 위치 업데이트
                config["last_position"] = file_size
                config["last_check"] = datetime.now()
                
            except Exception as e:
                print(f"로그 파일 확인 중 오류 발생: {e}")
    
    def start_monitoring(self):
        """모니터링 시작"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        
        def monitoring_task():
            while self.is_monitoring:
                try:
                    # 리소스 사용량 확인
                    if self.resource_notification_enabled:
                        self.check_cpu_usage()
                        self.check_memory_usage()
                        self.check_disk_usage()
                    
                    # 로그 파일 확인
                    self.check_log_files()
                    
                except Exception as e:
                    print(f"시스템 모니터링 중 오류 발생: {e}")
                
                # 대기
                time.sleep(self.monitoring_interval)
        
        # 모니터링 스레드 시작
        self.monitoring_thread = threading.Thread(target=monitoring_task, daemon=True)
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.is_monitoring = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=1.0)
    
    def set_monitoring_interval(self, interval: int):
        """모니터링 간격 설정
        
        Args:
            interval: 모니터링 간격 (초)
        """
        self.monitoring_interval = max(1, interval)  # 최소 1초
    
    def set_cpu_threshold(self, threshold: float):
        """CPU 사용량 임계값 설정
        
        Args:
            threshold: CPU 사용량 임계값 (%)
        """
        self.cpu_threshold = max(1, min(100, threshold))
        # 임계값 변경 시 알림 이력 초기화
        self.notified_resources = set(r for r in self.notified_resources if not r.startswith("cpu:"))
    
    def set_memory_threshold(self, threshold: float):
        """메모리 사용량 임계값 설정
        
        Args:
            threshold: 메모리 사용량 임계값 (%)
        """
        self.memory_threshold = max(1, min(100, threshold))
        # 임계값 변경 시 알림 이력 초기화
        self.notified_resources = set(r for r in self.notified_resources if not r.startswith("memory:"))
    
    def set_disk_threshold(self, threshold: float):
        """디스크 사용량 임계값 설정
        
        Args:
            threshold: 디스크 사용량 임계값 (%)
        """
        self.disk_threshold = max(1, min(100, threshold))
        # 임계값 변경 시 알림 이력 초기화
        self.notified_resources = set(r for r in self.notified_resources if not r.startswith("disk:"))
    
    def get_cpu_threshold(self) -> float:
        """CPU 사용량 임계값 반환
        
        Returns:
            float: CPU 사용량 임계값 (%)
        """
        return self.cpu_threshold
    
    def get_memory_threshold(self) -> float:
        """메모리 사용량 임계값 반환
        
        Returns:
            float: 메모리 사용량 임계값 (%)
        """
        return self.memory_threshold
    
    def get_disk_threshold(self) -> float:
        """디스크 사용량 임계값 반환
        
        Returns:
            float: 디스크 사용량 임계값 (%)
        """
        return self.disk_threshold
    
    def set_error_notification_enabled(self, enabled: bool):
        """오류 알림 활성화 여부 설정
        
        Args:
            enabled: 활성화 여부
        """
        self.error_notification_enabled = enabled
        if enabled:
            # 활성화 시 알림 이력 초기화
            self.notified_errors.clear()
    
    def set_status_notification_enabled(self, enabled: bool):
        """상태 알림 활성화 여부 설정
        
        Args:
            enabled: 활성화 여부
        """
        self.status_notification_enabled = enabled
    
    def set_resource_notification_enabled(self, enabled: bool):
        """리소스 알림 활성화 여부 설정
        
        Args:
            enabled: 활성화 여부
        """
        self.resource_notification_enabled = enabled
        if enabled:
            # 활성화 시 알림 이력 초기화
            self.notified_resources.clear()
    
    def is_error_notification_enabled(self) -> bool:
        """오류 알림 활성화 여부 반환
        
        Returns:
            bool: 활성화 여부
        """
        return self.error_notification_enabled
    
    def is_status_notification_enabled(self) -> bool:
        """상태 알림 활성화 여부 반환
        
        Returns:
            bool: 활성화 여부
        """
        return self.status_notification_enabled
    
    def is_resource_notification_enabled(self) -> bool:
        """리소스 알림 활성화 여부 반환
        
        Returns:
            bool: 활성화 여부
        """
        return self.resource_notification_enabled
    
    def save_settings(self, file_path: str) -> bool:
        """알림 설정 저장
        
        Args:
            file_path: 저장할 파일 경로
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 디렉토리 경로 확인
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # 설정 데이터
            settings = {
                "error_notification_enabled": self.error_notification_enabled,
                "status_notification_enabled": self.status_notification_enabled,
                "resource_notification_enabled": self.resource_notification_enabled,
                "cpu_threshold": self.cpu_threshold,
                "memory_threshold": self.memory_threshold,
                "disk_threshold": self.disk_threshold,
                "monitoring_interval": self.monitoring_interval
            }
            
            # JSON 파일로 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"알림 설정 저장 중 오류 발생: {e}")
            return False
    
    def load_settings(self, file_path: str) -> bool:
        """알림 설정 로드
        
        Args:
            file_path: 로드할 파일 경로
            
        Returns:
            bool: 성공 여부
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            # JSON 파일에서 로드
            with open(file_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # 설정 적용
            self.error_notification_enabled = settings.get("error_notification_enabled", True)
            self.status_notification_enabled = settings.get("status_notification_enabled", True)
            self.resource_notification_enabled = settings.get("resource_notification_enabled", True)
            self.cpu_threshold = settings.get("cpu_threshold", 80)
            self.memory_threshold = settings.get("memory_threshold", 90)
            self.disk_threshold = settings.get("disk_threshold", 95)
            self.monitoring_interval = settings.get("monitoring_interval", 60)
            
            return True
        except Exception as e:
            print(f"알림 설정 로드 중 오류 발생: {e}")
            return False