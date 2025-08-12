"""
Auto-Diagnosis Issue Detection System for LLM Agent Logging
실시간 로그 분석을 통한 자동 문제 감지 시스템
"""
import re
import time
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SystemIssue:
    """시스템 문제 정의"""
    id: str
    type: str
    severity: str
    message: str
    detected_at: datetime
    component: str
    suggested_actions: List[str]
    estimated_fix_time: int
    log_excerpt: str

class IssueDetector:
    """자동 문제 감지 시스템"""

    def __init__(self):
        self.detection_rules = self._load_detection_rules()

    def _load_detection_rules(self) -> Dict[str, Dict[str, Any]]:
        """문제 감지 규칙 로드"""
        return {
            'di_container_missing': {
                'pattern': r'Application Container.*찾을 수 없음',
                'severity': 'HIGH',
                'component': 'DI_Container',
                'actions': ['ApplicationContext 초기화 순서 확인', 'DI Container 등록 로직 검토'],
                'estimated_time': 15
            },
            'theme_service_conflict': {
                'pattern': r'ThemeService.*metaclass.*충돌',
                'severity': 'MEDIUM',
                'component': 'ThemeService',
                'actions': ['DI Container 통합 방식 변경', 'PyQt6 호환성 검토'],
                'estimated_time': 30
            },
            'mvp_pattern_violation': {
                'pattern': r'MVP.*패턴.*위반',
                'severity': 'MEDIUM',
                'component': 'MVP_Architecture',
                'actions': ['Presenter-View 분리 확인', 'Business Logic 분리 검토'],
                'estimated_time': 25
            },
            'database_connection_error': {
                'pattern': r'(database|DB).*connection.*failed',
                'severity': 'HIGH',
                'component': 'Database',
                'actions': ['DB 파일 경로 확인', 'SQLite 권한 검토', 'DB 스키마 유효성 검사'],
                'estimated_time': 20
            },
            'memory_leak_detected': {
                'pattern': r'memory.*leak|메모리.*누수',
                'severity': 'HIGH',
                'component': 'Memory_Management',
                'actions': ['객체 참조 순환 검사', 'WeakRef 사용 검토', 'QObject 삭제 로직 확인'],
                'estimated_time': 45
            },
            'ui_rendering_error': {
                'pattern': r'UI.*rendering.*failed|렌더링.*실패',
                'severity': 'MEDIUM',
                'component': 'UI_Rendering',
                'actions': ['QSS 스타일 검증', '테마 적용 순서 확인', 'Widget 계층 구조 검토'],
                'estimated_time': 20
            },
            'config_loading_error': {
                'pattern': r'config.*loading.*failed|설정.*로드.*실패',
                'severity': 'MEDIUM',
                'component': 'Configuration',
                'actions': ['YAML 파일 구문 검사', '환경변수 확인', '기본값 fallback 검토'],
                'estimated_time': 15
            }
        }

    def detect_issues_from_logs(self, recent_logs: List[str]) -> List[SystemIssue]:
        """최근 로그에서 문제 자동 감지"""
        detected_issues = []

        for log_line in recent_logs:
            for rule_name, rule in self.detection_rules.items():
                if re.search(rule['pattern'], log_line, re.IGNORECASE):
                    issue = SystemIssue(
                        id=f"{rule_name}_{int(time.time())}",
                        type=rule_name,
                        severity=rule['severity'],
                        message=self._extract_issue_message(log_line),
                        detected_at=datetime.now(),
                        component=rule['component'],
                        suggested_actions=rule['actions'],
                        estimated_fix_time=rule['estimated_time'],
                        log_excerpt=log_line.strip()
                    )
                    detected_issues.append(issue)

        return self._deduplicate_issues(detected_issues)

    def _extract_issue_message(self, log_line: str) -> str:
        """로그 라인에서 문제 메시지 추출"""
        # 로그 레벨과 타임스탬프 제거하고 핵심 메시지만 추출
        parts = log_line.split(' - ')
        if len(parts) >= 3:
            return parts[-1].strip()
        return log_line.strip()

    def _deduplicate_issues(self, issues: List[SystemIssue]) -> List[SystemIssue]:
        """중복 문제 제거 (같은 타입, 5분 이내)"""
        unique_issues = []
        seen_types = set()

        for issue in sorted(issues, key=lambda x: x.detected_at, reverse=True):
            if issue.type not in seen_types:
                unique_issues.append(issue)
                seen_types.add(issue.type)

        return unique_issues

    def classify_severity(self, issues: List[SystemIssue]) -> Dict[str, int]:
        """문제 심각도별 분류"""
        severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}

        for issue in issues:
            if issue.severity in severity_counts:
                severity_counts[issue.severity] += 1

        return severity_counts

    def get_urgent_issues(self, issues: List[SystemIssue]) -> List[SystemIssue]:
        """긴급 처리 필요한 문제 필터링"""
        return [issue for issue in issues if issue.severity == 'HIGH']

    def estimate_total_fix_time(self, issues: List[SystemIssue]) -> int:
        """전체 수정 예상 시간 계산 (분 단위)"""
        return sum(issue.estimated_fix_time for issue in issues)
