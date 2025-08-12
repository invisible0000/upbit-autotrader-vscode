"""
Real-time Dashboard Data Generator for LLM Agent System Monitoring
실시간 대시보드 JSON 데이터 생성 및 관리
"""
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from ..briefing.status_tracker import SystemStatusTracker, ComponentStatus
from .issue_detector import IssueDetector, SystemIssue

@dataclass
class DashboardData:
    """대시보드 데이터 구조"""
    timestamp: str
    system_health: str
    components_summary: Dict[str, int]
    active_issues: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    recommendations: List[str]
    quick_actions: List[Dict[str, str]]

class RealtimeDashboard:
    """실시간 대시보드 데이터 생성기"""

    def __init__(self, status_tracker: SystemStatusTracker, issue_detector: IssueDetector):
        self.status_tracker = status_tracker
        self.issue_detector = issue_detector

    def generate_dashboard_data(self, recent_logs: List[str]) -> DashboardData:
        """대시보드 데이터 생성"""
        # 문제 감지
        detected_issues = self.issue_detector.detect_issues_from_logs(recent_logs)

        # 시스템 상태 분석
        system_health = self._calculate_system_health(detected_issues)
        components_summary = self._get_components_summary()

        # 성능 메트릭 계산
        performance_metrics = self._calculate_performance_metrics(detected_issues)

        # 추천 사항 생성
        recommendations = self._generate_recommendations(detected_issues)

        # 빠른 액션 생성
        quick_actions = self._generate_quick_actions(detected_issues)

        return DashboardData(
            timestamp=datetime.now().isoformat(),
            system_health=system_health,
            components_summary=components_summary,
            active_issues=[self._issue_to_dict(issue) for issue in detected_issues],
            performance_metrics=performance_metrics,
            recommendations=recommendations,
            quick_actions=quick_actions
        )

    def _calculate_system_health(self, issues: List[SystemIssue]) -> str:
        """전체 시스템 건강도 계산"""
        high_issues = [i for i in issues if i.severity == 'HIGH']
        medium_issues = [i for i in issues if i.severity == 'MEDIUM']

        if len(high_issues) >= 2:
            return "CRITICAL"
        elif len(high_issues) == 1:
            return "WARNING"
        elif len(medium_issues) >= 3:
            return "WARNING"
        elif len(medium_issues) > 0:
            return "ATTENTION"
        else:
            return "HEALTHY"

    def _get_components_summary(self) -> Dict[str, int]:
        """컴포넌트 상태 요약"""
        summary = {"OK": 0, "WARNING": 0, "ERROR": 0, "LIMITED": 0, "UNKNOWN": 0}

        for component_status in self.status_tracker.components.values():
            status = component_status.status
            if status in summary:
                summary[status] += 1
            else:
                summary["UNKNOWN"] += 1

        return summary

    def _calculate_performance_metrics(self, issues: List[SystemIssue]) -> Dict[str, Any]:
        """성능 메트릭 계산"""
        total_issues = len(issues)
        urgent_issues = len([i for i in issues if i.severity == 'HIGH'])
        estimated_fix_time = sum(issue.estimated_fix_time for issue in issues)

        # 컴포넌트별 문제 분포
        component_issues = {}
        for issue in issues:
            component = issue.component
            if component not in component_issues:
                component_issues[component] = 0
            component_issues[component] += 1

        return {
            "total_issues": total_issues,
            "urgent_issues": urgent_issues,
            "estimated_fix_time_minutes": estimated_fix_time,
            "issue_rate": round((urgent_issues / max(total_issues, 1)) * 100, 2),
            "component_issues": component_issues,
            "system_uptime_status": self._get_uptime_status()
        }

    def _get_uptime_status(self) -> str:
        """시스템 가동 상태"""
        # 간단한 가동 시간 상태 (실제로는 더 복잡한 로직 필요)
        components = self.status_tracker.components
        if not components:
            return "UNKNOWN"

        error_count = sum(1 for status in components.values() if status.status == "ERROR")
        total_count = len(components)

        if error_count == 0:
            return "STABLE"
        elif error_count <= total_count * 0.3:
            return "DEGRADED"
        else:
            return "UNSTABLE"

    def _generate_recommendations(self, issues: List[SystemIssue]) -> List[str]:
        """문제 기반 추천 사항 생성"""
        recommendations = []

        # 긴급 문제가 있는 경우
        urgent_issues = [i for i in issues if i.severity == 'HIGH']
        if urgent_issues:
            recommendations.append(f"🚨 긴급: {len(urgent_issues)}개의 HIGH 우선순위 문제를 먼저 해결하세요")

        # 많은 문제가 있는 경우
        if len(issues) > 5:
            recommendations.append("⚠️ 여러 문제가 동시에 발생했습니다. 시스템 재시작을 고려하세요")

        # 컴포넌트별 문제 패턴
        component_issues = {}
        for issue in issues:
            comp = issue.component
            if comp not in component_issues:
                component_issues[comp] = []
            component_issues[comp].append(issue)

        for component, comp_issues in component_issues.items():
            if len(comp_issues) > 1:
                recommendations.append(f"🔧 {component} 컴포넌트에 {len(comp_issues)}개 문제가 집중되어 있습니다")

        # 기본 추천
        if not recommendations:
            recommendations.append("✅ 시스템이 양호한 상태입니다. 정기 점검을 계속하세요")

        return recommendations

    def _generate_quick_actions(self, issues: List[SystemIssue]) -> List[Dict[str, str]]:
        """빠른 액션 버튼 생성"""
        actions = []

        # 문제별 빠른 액션
        for issue in issues[:3]:  # 최대 3개만
            if issue.suggested_actions:
                actions.append({
                    "label": f"Fix: {issue.component}",
                    "action": issue.suggested_actions[0],
                    "severity": issue.severity
                })

        # 기본 액션들
        actions.extend([
            {"label": "시스템 상태 새로고침", "action": "refresh_system_status", "severity": "INFO"},
            {"label": "로그 파일 보기", "action": "open_log_file", "severity": "INFO"},
            {"label": "문제 해결 가이드", "action": "open_troubleshooting_guide", "severity": "INFO"}
        ])

        return actions

    def _issue_to_dict(self, issue: SystemIssue) -> Dict[str, Any]:
        """SystemIssue를 dict로 변환"""
        return {
            "id": issue.id,
            "type": issue.type,
            "severity": issue.severity,
            "message": issue.message,
            "detected_at": issue.detected_at.isoformat(),
            "component": issue.component,
            "suggested_actions": issue.suggested_actions,
            "estimated_fix_time": issue.estimated_fix_time,
            "log_excerpt": issue.log_excerpt
        }

    def to_json(self, dashboard_data: DashboardData) -> str:
        """대시보드 데이터를 JSON 문자열로 변환"""
        return json.dumps(asdict(dashboard_data), ensure_ascii=False, indent=2)

    def get_summary_stats(self, dashboard_data: DashboardData) -> Dict[str, Any]:
        """대시보드 요약 통계"""
        return {
            "timestamp": dashboard_data.timestamp,
            "system_health": dashboard_data.system_health,
            "total_components": sum(dashboard_data.components_summary.values()),
            "active_issues_count": len(dashboard_data.active_issues),
            "urgent_issues_count": dashboard_data.performance_metrics.get("urgent_issues", 0),
            "recommendations_count": len(dashboard_data.recommendations),
            "estimated_fix_time": dashboard_data.performance_metrics.get("estimated_fix_time_minutes", 0)
        }
