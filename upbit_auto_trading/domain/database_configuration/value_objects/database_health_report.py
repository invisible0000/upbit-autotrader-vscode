"""
데이터베이스 건강 상태 모니터링 서비스

프로그램 시작 시, 설정 변경 시, 그리고 DB 고장 감지 시에만 안전하게 DB 상태를 모니터링합니다.
실시간 중 점검은 위험하므로 특정 시점에만 수행됩니다.
"""

from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class DatabaseHealthLevel(Enum):
    """데이터베이스 건강 상태 레벨"""
    HEALTHY = "healthy"           # 정상
    WARNING = "warning"           # 경고 (성능 저하 등)
    ERROR = "error"               # 오류 (연결 불가)
    CRITICAL = "critical"         # 치명적 (파일 손상)
    MISSING = "missing"           # 파일 없음

@dataclass
class DatabaseHealthReport:
    """데이터베이스 건강 상태 보고서"""
    database_type: str
    file_path: str
    health_level: DatabaseHealthLevel
    connection_time_ms: float
    file_size_mb: float
    table_count: int
    last_checked: datetime
    issues: List[str]
    recommendations: List[str]
    can_auto_recover: bool

    @property
    def is_operational(self) -> bool:
        """운영 가능한 상태인지 확인"""
        return self.health_level in [DatabaseHealthLevel.HEALTHY, DatabaseHealthLevel.WARNING]

    @property
    def needs_immediate_attention(self) -> bool:
        """즉시 사용자 개입이 필요한지 확인"""
        return self.health_level in [DatabaseHealthLevel.ERROR, DatabaseHealthLevel.CRITICAL, DatabaseHealthLevel.MISSING]

@dataclass
class SystemDatabaseHealth:
    """전체 시스템 DB 건강 상태"""
    overall_status: DatabaseHealthLevel
    reports: Dict[str, DatabaseHealthReport]
    system_can_start: bool
    critical_issues: List[str]
    recovery_recommendations: List[str]
    checked_at: datetime

    @property
    def healthy_databases(self) -> List[str]:
        """정상 상태의 데이터베이스 목록"""
        return [
            db_type for db_type, report in self.reports.items()
            if report.health_level == DatabaseHealthLevel.HEALTHY
        ]

    @property
    def problematic_databases(self) -> List[str]:
        """문제가 있는 데이터베이스 목록"""
        return [
            db_type for db_type, report in self.reports.items()
            if report.needs_immediate_attention
        ]
