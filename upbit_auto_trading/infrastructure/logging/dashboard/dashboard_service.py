"""
Dashboard Service for LLM Agent Real-time System Monitoring
실시간 대시보드 파일 관리 및 업데이트 서비스
"""
import json
import os
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from ..briefing.status_tracker import SystemStatusTracker
from .issue_detector import IssueDetector
from .realtime_dashboard import RealtimeDashboard, DashboardData

class DashboardService:
    """대시보드 서비스 - 실시간 JSON 대시보드 파일 관리"""

    def __init__(self, dashboard_file_path: str = "logs/llm_agent_dashboard.json"):
        self.dashboard_file_path = dashboard_file_path
        self.status_tracker = SystemStatusTracker()
        self.issue_detector = IssueDetector()
        self.dashboard = RealtimeDashboard(self.status_tracker, self.issue_detector)

        # 로그 디렉토리 생성
        os.makedirs(os.path.dirname(dashboard_file_path), exist_ok=True)

    def update_dashboard(self, recent_logs: List[str] = None) -> DashboardData:
        """대시보드 업데이트"""
        if recent_logs is None:
            recent_logs = self._get_recent_logs()

        # 대시보드 데이터 생성
        dashboard_data = self.dashboard.generate_dashboard_data(recent_logs)

        # JSON 파일로 저장
        self._save_dashboard_file(dashboard_data)

        return dashboard_data

    def _get_recent_logs(self) -> List[str]:
        """최근 로그 라인 가져오기 (기본 구현)"""
        # 실제로는 로깅 시스템에서 최근 로그를 가져와야 함
        # 현재는 테스트용 더미 데이터
        return [
            "2025-01-14 10:30:15 - upbit.MainWindow - ERROR - DI Container를 찾을 수 없음",
            "2025-01-14 10:30:16 - upbit.ThemeService - WARNING - ThemeService metaclass 충돌 감지",
            "2025-01-14 10:30:17 - upbit.DatabaseManager - INFO - DB 연결 성공: settings.sqlite3"
        ]

    def _save_dashboard_file(self, dashboard_data: DashboardData) -> None:
        """대시보드 데이터를 JSON 파일로 저장"""
        try:
            json_content = self.dashboard.to_json(dashboard_data)

            with open(self.dashboard_file_path, 'w', encoding='utf-8') as f:
                f.write(json_content)

            print(f"✅ Dashboard updated: {self.dashboard_file_path}")

        except Exception as e:
            print(f"❌ Dashboard update failed: {e}")

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """대시보드 요약 정보 반환"""
        try:
            with open(self.dashboard_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return {
                "last_update": data.get("timestamp", "Unknown"),
                "system_health": data.get("system_health", "Unknown"),
                "total_issues": len(data.get("active_issues", [])),
                "urgent_issues": data.get("performance_metrics", {}).get("urgent_issues", 0),
                "components_status": data.get("components_summary", {}),
                "file_size": os.path.getsize(self.dashboard_file_path)
            }

        except Exception as e:
            return {"error": f"Dashboard file read failed: {e}"}

    def simulate_issue_scenario(self, scenario_name: str) -> DashboardData:
        """테스트용 문제 시나리오 시뮬레이션"""
        scenarios = {
            "critical_system": [
                "2025-01-14 10:30:15 - upbit.DI_Container - ERROR - Application Container를 찾을 수 없음",
                "2025-01-14 10:30:16 - upbit.Database - ERROR - database connection failed: corrupted file",
                "2025-01-14 10:30:17 - upbit.Memory - ERROR - memory leak detected in QWidget hierarchy"
            ],
            "normal_operation": [
                "2025-01-14 10:30:15 - upbit.MainWindow - INFO - MainWindow 초기화 완료",
                "2025-01-14 10:30:16 - upbit.ThemeService - INFO - 테마 적용 성공: dark_theme",
                "2025-01-14 10:30:17 - upbit.DatabaseManager - INFO - DB 연결 성공: strategies.sqlite3"
            ],
            "moderate_issues": [
                "2025-01-14 10:30:15 - upbit.ThemeService - WARNING - ThemeService metaclass 충돌 감지",
                "2025-01-14 10:30:16 - upbit.ConfigManager - WARNING - config loading failed: using defaults",
                "2025-01-14 10:30:17 - upbit.UIRenderer - WARNING - UI rendering failed: fallback to basic style"
            ]
        }

        test_logs = scenarios.get(scenario_name, scenarios["normal_operation"])

        # 테스트 컴포넌트 상태 설정
        if scenario_name == "critical_system":
            self.status_tracker.update_component_status("DI_Container", "ERROR", "Application Container 찾을 수 없음")
            self.status_tracker.update_component_status("Database", "ERROR", "연결 실패")
            self.status_tracker.update_component_status("Memory", "ERROR", "메모리 누수 감지")
        elif scenario_name == "moderate_issues":
            self.status_tracker.update_component_status("ThemeService", "WARNING", "메타클래스 충돌")
            self.status_tracker.update_component_status("ConfigManager", "WARNING", "설정 로드 실패")
            self.status_tracker.update_component_status("UIRenderer", "LIMITED", "기본 스타일로 fallback")
        else:  # normal_operation
            self.status_tracker.update_component_status("MainWindow", "OK", "정상 작동")
            self.status_tracker.update_component_status("ThemeService", "OK", "테마 적용 성공")
            self.status_tracker.update_component_status("DatabaseManager", "OK", "DB 연결 성공")

        return self.update_dashboard(test_logs)

    def generate_test_dashboard(self, scenario: str = "normal_operation") -> str:
        """테스트용 대시보드 생성 및 경로 반환"""
        dashboard_data = self.simulate_issue_scenario(scenario)
        return self.dashboard_file_path

    def cleanup_dashboard_files(self) -> None:
        """대시보드 파일 정리"""
        try:
            if os.path.exists(self.dashboard_file_path):
                os.remove(self.dashboard_file_path)
                print(f"🗑️ Dashboard file cleaned: {self.dashboard_file_path}")
        except Exception as e:
            print(f"❌ Dashboard cleanup failed: {e}")

    def validate_dashboard_structure(self) -> Dict[str, bool]:
        """대시보드 JSON 구조 유효성 검사"""
        try:
            with open(self.dashboard_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            required_keys = [
                "timestamp", "system_health", "components_summary",
                "active_issues", "performance_metrics", "recommendations", "quick_actions"
            ]

            validation_result = {}
            for key in required_keys:
                validation_result[key] = key in data

            validation_result["overall_valid"] = all(validation_result.values())
            return validation_result

        except Exception as e:
            return {"error": str(e), "overall_valid": False}
