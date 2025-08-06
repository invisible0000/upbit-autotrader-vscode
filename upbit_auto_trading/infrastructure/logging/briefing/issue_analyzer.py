"""
문제 분석 및 우선순위 시스템 - LLM 에이전트 자동 진단
시스템 이슈 패턴 인식 및 해결 방안 제시
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
import re
import time
from .status_tracker import SystemStatusTracker, ComponentStatus


@dataclass
class SystemIssue:
    """시스템 이슈 정보"""
    id: str
    title: str
    description: str
    priority: str  # 'HIGH', 'MEDIUM', 'LOW'
    category: str  # 'DI', 'MVP', 'UI', 'DB', 'PERF', 'CONFIG'
    affected_components: List[str]
    suggested_actions: List[str]
    estimated_time: int  # 분
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'category': self.category,
            'affected_components': self.affected_components,
            'suggested_actions': self.suggested_actions,
            'estimated_time': self.estimated_time,
            'timestamp': self.timestamp.isoformat()
        }


class IssueAnalyzer:
    """시스템 이슈 분석 및 진단 엔진"""

    # 알려진 이슈 패턴 정의
    ISSUE_PATTERNS = {
        'di_container_missing': {
            'pattern': r'Application Container.*찾을 수 없음|cannot.*find.*ApplicationContainer',
            'title': 'DI Container 초기화 실패',
            'description': 'ApplicationContext가 초기화되지 않아 의존성 주입이 불가능한 상태',
            'priority': 'HIGH',
            'category': 'DI',
            'actions': [
                'ApplicationContext 초기화 순서 확인',
                'DI Container 등록 로직 검토',
                'MainWindow 초기화 시점 조정'
            ],
            'estimated_time': 15
        },
        'theme_service_conflict': {
            'pattern': r'ThemeService.*metaclass.*충돌|ThemeService.*multiple inheritance',
            'title': 'ThemeService 메타클래스 충돌',
            'description': 'PyQt6와 DI Container 사이의 메타클래스 충돌 발생',
            'priority': 'MEDIUM',
            'category': 'UI',
            'actions': [
                'DI Container 통합 방식 변경',
                'PyQt6 호환성 검토',
                'ThemeService 구조 리팩토링'
            ],
            'estimated_time': 30
        },
        'mvp_pattern_warning': {
            'pattern': r'MVP.*패턴.*경고|Presenter.*View.*연결.*실패',
            'title': 'MVP 패턴 구현 경고',
            'description': 'MVP 패턴의 Presenter-View 연결에서 문제 발생',
            'priority': 'MEDIUM',
            'category': 'MVP',
            'actions': [
                'Presenter 인터페이스 검토',
                'View 생명주기 관리 확인',
                'Signal-Slot 연결 상태 점검'
            ],
            'estimated_time': 20
        },
        'database_connection': {
            'pattern': r'데이터베이스.*연결.*실패|Database.*connection.*failed',
            'title': '데이터베이스 연결 실패',
            'description': 'SQLite 데이터베이스 파일 접근 또는 연결 문제',
            'priority': 'HIGH',
            'category': 'DB',
            'actions': [
                'DB 파일 존재 여부 확인',
                '파일 권한 검사',
                'WAL 모드 설정 확인',
                'DB 스키마 마이그레이션 실행'
            ],
            'estimated_time': 10
        },
        'memory_leak': {
            'pattern': r'메모리.*사용량.*증가|Memory.*usage.*high',
            'title': '메모리 사용량 증가',
            'description': '비정상적인 메모리 사용량 증가 감지',
            'priority': 'MEDIUM',
            'category': 'PERF',
            'actions': [
                '가비지 컬렉션 강제 실행',
                '로그 버퍼 정리',
                '순환 참조 검사',
                'WeakRef 사용 검토'
            ],
            'estimated_time': 25
        },
        'ui_rendering_slow': {
            'pattern': r'UI.*렌더링.*느림|UI.*response.*slow',
            'title': 'UI 렌더링 성능 저하',
            'description': 'UI 컴포넌트 렌더링 응답 시간 지연',
            'priority': 'LOW',
            'category': 'PERF',
            'actions': [
                '위젯 초기화 순서 최적화',
                '불필요한 시그널 연결 제거',
                'QSS 스타일 최적화'
            ],
            'estimated_time': 15
        },
        'config_file_missing': {
            'pattern': r'설정.*파일.*없음|Config.*file.*not.*found',
            'title': '설정 파일 누락',
            'description': '필수 설정 파일이 존재하지 않음',
            'priority': 'HIGH',
            'category': 'CONFIG',
            'actions': [
                '기본 설정 파일 생성',
                '설정 파일 경로 확인',
                '환경변수 설정 검토'
            ],
            'estimated_time': 5
        }
    }

    def __init__(self):
        self.detected_issues: List[SystemIssue] = []
        self.last_analysis_time = datetime.now()

    def analyze_for_issues(self, status_tracker: SystemStatusTracker) -> List[SystemIssue]:
        """시스템 상태에서 문제점 분석"""
        issues = []

        # 컴포넌트 상태 기반 이슈 분석
        for component_name, status in status_tracker.components.items():
            if status.needs_attention():
                issue = self._classify_component_issue(component_name, status)
                if issue:
                    issues.append(issue)

        # 성능 메트릭 기반 이슈 분석
        performance_issues = self._analyze_performance_metrics(status_tracker)
        issues.extend(performance_issues)

        # 우선순위별 정렬
        sorted_issues = sorted(issues, key=lambda x: self._priority_order(x.priority))

        self.detected_issues = sorted_issues
        self.last_analysis_time = datetime.now()

        return sorted_issues

    def analyze_log_messages(self, log_messages: List[str]) -> List[SystemIssue]:
        """로그 메시지에서 이슈 패턴 감지"""
        detected_issues = []

        for log_message in log_messages:
            for pattern_name, pattern_info in self.ISSUE_PATTERNS.items():
                if re.search(pattern_info['pattern'], log_message, re.IGNORECASE):
                    issue = SystemIssue(
                        id=f"{pattern_name}_{int(time.time())}",
                        title=pattern_info['title'],
                        description=pattern_info['description'],
                        priority=pattern_info['priority'],
                        category=pattern_info['category'],
                        affected_components=[self._extract_component_from_log(log_message)],
                        suggested_actions=pattern_info['actions'],
                        estimated_time=pattern_info['estimated_time'],
                        timestamp=datetime.now()
                    )
                    detected_issues.append(issue)

        return detected_issues

    def _classify_component_issue(self,
                                component_name: str,
                                status: ComponentStatus) -> Optional[SystemIssue]:
        """컴포넌트 상태를 기반으로 이슈 분류"""
        # 컴포넌트 이름과 상태 메시지를 기반으로 패턴 매칭
        combined_message = f"{component_name} {status.details}"

        for pattern_name, pattern_info in self.ISSUE_PATTERNS.items():
            if re.search(pattern_info['pattern'], combined_message, re.IGNORECASE):
                return SystemIssue(
                    id=f"{pattern_name}_{component_name}_{int(time.time())}",
                    title=f"{pattern_info['title']} ({component_name})",
                    description=f"{pattern_info['description']} - {status.details}",
                    priority=pattern_info['priority'],
                    category=pattern_info['category'],
                    affected_components=[component_name],
                    suggested_actions=pattern_info['actions'],
                    estimated_time=pattern_info['estimated_time'],
                    timestamp=status.timestamp
                )

        # 패턴에 매칭되지 않는 경우 일반 이슈로 분류
        if status.status == 'ERROR':
            return SystemIssue(
                id=f"generic_error_{component_name}_{int(time.time())}",
                title=f"{component_name} 에러",
                description=status.details,
                priority='MEDIUM',
                category='GENERAL',
                affected_components=[component_name],
                suggested_actions=['로그 상세 확인', '컴포넌트 재시작 시도'],
                estimated_time=10,
                timestamp=status.timestamp
            )

        return None

    def _analyze_performance_metrics(self,
                                   status_tracker: SystemStatusTracker) -> List[SystemIssue]:
        """성능 메트릭 기반 이슈 분석"""
        issues = []
        performance_metrics = status_tracker.get_performance_metrics()

        # 로딩 시간 체크
        for metric_name, value in performance_metrics.items():
            if 'load_time' in metric_name and value > 5.0:  # 5초 이상
                component = metric_name.replace('_load_time', '')
                issues.append(SystemIssue(
                    id=f"slow_loading_{component}_{int(time.time())}",
                    title=f"{component} 로딩 시간 지연",
                    description=f"로딩 시간이 {value:.1f}초로 과도하게 긴 상태",
                    priority='MEDIUM',
                    category='PERF',
                    affected_components=[component],
                    suggested_actions=[
                        '컴포넌트 초기화 로직 최적화',
                        '불필요한 종속성 제거',
                        '지연 로딩 적용 검토'
                    ],
                    estimated_time=20,
                    timestamp=datetime.now()
                ))

        return issues

    def _extract_component_from_log(self, log_message: str) -> str:
        """로그 메시지에서 컴포넌트 이름 추출"""
        # 일반적인 컴포넌트 이름 패턴 매칭
        patterns = [
            r'(\w+Window)',
            r'(\w+Service)',
            r'(\w+Manager)',
            r'(\w+Component)',
            r'upbit\.(\w+)',
            r'- (\w+) -'
        ]

        for pattern in patterns:
            match = re.search(pattern, log_message)
            if match:
                return match.group(1)

        return 'Unknown'

    def _priority_order(self, priority: str) -> int:
        """우선순위 정렬용 숫자 반환"""
        priority_map = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        return priority_map.get(priority, 3)

    def get_issues_by_category(self, category: str) -> List[SystemIssue]:
        """카테고리별 이슈 조회"""
        return [issue for issue in self.detected_issues if issue.category == category]

    def get_high_priority_issues(self) -> List[SystemIssue]:
        """높은 우선순위 이슈만 반환"""
        return [issue for issue in self.detected_issues if issue.priority == 'HIGH']

    def get_estimated_resolution_time(self) -> int:
        """전체 이슈 해결 예상 시간 (분)"""
        return sum(issue.estimated_time for issue in self.detected_issues)

    def clear_resolved_issues(self, resolved_issue_ids: List[str]) -> int:
        """해결된 이슈 제거"""
        initial_count = len(self.detected_issues)
        self.detected_issues = [
            issue for issue in self.detected_issues
            if issue.id not in resolved_issue_ids
        ]
        return initial_count - len(self.detected_issues)
