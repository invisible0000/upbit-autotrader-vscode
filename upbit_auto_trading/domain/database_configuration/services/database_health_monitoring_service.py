"""
데이터베이스 건강 모니터링 서비스 (Domain Service)

안전한 시점에만 DB 상태를 점검하는 도메인 서비스입니다.
- 프로그램 시작 시
- DB 설정 변경 시
- 확실한 DB 고장 감지 시
동작 중 점검은 위험하므로 수행하지 않습니다.
"""

import sqlite3
import time
from pathlib import Path
from typing import Dict
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.domain.database_configuration.value_objects.database_health_report import (
    DatabaseHealthReport, SystemDatabaseHealth, DatabaseHealthLevel
)


class DatabaseHealthMonitoringService:
    """
    데이터베이스 건강 모니터링 서비스

    도메인 서비스로서 DB 건강 상태를 안전하게 점검합니다.
    """

    def __init__(self):
        self._logger = create_component_logger("DatabaseHealthMonitoring")
        self._logger.info("DB 건강 모니터링 서비스 초기화")

    def check_system_database_health(self, database_paths: Dict[str, str]) -> SystemDatabaseHealth:
        """
        전체 시스템 DB 건강 상태 점검

        Args:
            database_paths: DB 타입별 파일 경로

        Returns:
            시스템 전체 DB 건강 상태
        """
        self._logger.info("🏥 시스템 DB 건강 상태 점검 시작")

        reports = {}
        critical_issues = []
        recovery_recommendations = []

        # 각 DB별 개별 점검
        for db_type, file_path in database_paths.items():
            try:
                report = self._check_individual_database(db_type, file_path)
                reports[db_type] = report

                if report.needs_immediate_attention:
                    critical_issues.extend(report.issues)
                    recovery_recommendations.extend(report.recommendations)

            except Exception as e:
                self._logger.error(f"DB 점검 실패: {db_type} - {e}")
                # 점검 실패도 치명적 상황으로 처리
                reports[db_type] = self._create_error_report(db_type, file_path, str(e))
                critical_issues.append(f"{db_type} DB 점검 실패: {str(e)}")

        # 전체 상태 결정
        overall_status = self._determine_overall_status(reports)
        system_can_start = self._can_system_start_safely(reports)

        result = SystemDatabaseHealth(
            overall_status=overall_status,
            reports=reports,
            system_can_start=system_can_start,
            critical_issues=critical_issues,
            recovery_recommendations=recovery_recommendations,
            checked_at=datetime.now()
        )

        self._logger.info(f"🏥 시스템 DB 건강 점검 완료: {overall_status.value}")
        return result

    def _check_individual_database(self, db_type: str, file_path: str) -> DatabaseHealthReport:
        """개별 데이터베이스 건강 상태 점검"""
        start_time = time.time()
        path_obj = Path(file_path)

        issues = []
        recommendations = []

        # 1. 파일 존재 확인
        if not path_obj.exists():
            return DatabaseHealthReport(
                database_type=db_type,
                file_path=file_path,
                health_level=DatabaseHealthLevel.MISSING,
                connection_time_ms=0.0,
                file_size_mb=0.0,
                table_count=0,
                last_checked=datetime.now(),
                issues=[f"데이터베이스 파일이 존재하지 않습니다: {file_path}"],
                recommendations=[
                    "데이터베이스 설정에서 올바른 파일을 선택하세요",
                    "또는 새로운 데이터베이스를 생성하세요"
                ],
                can_auto_recover=True  # 새 DB 생성 가능
            )

        # 2. 파일 크기 확인
        try:
            file_size_bytes = path_obj.stat().st_size
            file_size_mb = file_size_bytes / (1024 * 1024)

            if file_size_bytes == 0:
                issues.append("데이터베이스 파일이 비어있습니다")
                recommendations.append("스키마를 다시 초기화하세요")

        except Exception as e:
            file_size_mb = 0.0
            issues.append(f"파일 정보 읽기 실패: {str(e)}")

        # 3. SQLite 연결 및 기본 점검
        connection_time_ms = 0.0
        table_count = 0
        health_level = DatabaseHealthLevel.ERROR

        try:
            with sqlite3.connect(str(path_obj), timeout=5.0) as conn:
                # 연결 시간 측정
                connection_time_ms = (time.time() - start_time) * 1000

                cursor = conn.cursor()

                # 기본 연결 테스트
                cursor.execute("SELECT 1")
                cursor.fetchone()

                # 무결성 검사
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()

                if integrity_result[0] != "ok":
                    issues.append(f"데이터베이스 무결성 검사 실패: {integrity_result[0]}")
                    health_level = DatabaseHealthLevel.CRITICAL
                    recommendations.append("데이터베이스를 복구하거나 백업에서 복원하세요")

                # 테이블 수 확인
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]

                if table_count == 0:
                    issues.append("데이터베이스에 테이블이 없습니다")
                    health_level = DatabaseHealthLevel.ERROR
                    recommendations.append("스키마를 초기화하세요")
                elif health_level != DatabaseHealthLevel.CRITICAL:
                    # 무결성이 OK이고 테이블이 있으면
                    if connection_time_ms > 1000:  # 1초 이상
                        health_level = DatabaseHealthLevel.WARNING
                        issues.append(f"연결 시간이 느립니다: {connection_time_ms:.1f}ms")
                        recommendations.append("데이터베이스 최적화를 고려하세요")
                    else:
                        health_level = DatabaseHealthLevel.HEALTHY

        except sqlite3.DatabaseError as e:
            issues.append(f"데이터베이스 오류: {str(e)}")
            health_level = DatabaseHealthLevel.CRITICAL
            recommendations.append("데이터베이스 파일이 손상되었을 수 있습니다")
            recommendations.append("백업에서 복원하거나 새로 생성하세요")

        except Exception as e:
            issues.append(f"연결 오류: {str(e)}")
            health_level = DatabaseHealthLevel.ERROR
            recommendations.append("파일 권한이나 경로를 확인하세요")

        # 자동 복구 가능성 판단
        can_auto_recover = health_level in [
            DatabaseHealthLevel.MISSING,
            DatabaseHealthLevel.ERROR
        ] and "권한" not in str(issues)

        return DatabaseHealthReport(
            database_type=db_type,
            file_path=file_path,
            health_level=health_level,
            connection_time_ms=connection_time_ms,
            file_size_mb=file_size_mb,
            table_count=table_count,
            last_checked=datetime.now(),
            issues=issues,
            recommendations=recommendations,
            can_auto_recover=can_auto_recover
        )

    def _create_error_report(self, db_type: str, file_path: str, error_message: str) -> DatabaseHealthReport:
        """점검 실패 시 에러 리포트 생성"""
        return DatabaseHealthReport(
            database_type=db_type,
            file_path=file_path,
            health_level=DatabaseHealthLevel.ERROR,
            connection_time_ms=0.0,
            file_size_mb=0.0,
            table_count=0,
            last_checked=datetime.now(),
            issues=[f"건강 상태 점검 실패: {error_message}"],
            recommendations=["시스템 관리자에게 문의하세요"],
            can_auto_recover=False
        )

    def _determine_overall_status(self, reports: Dict[str, DatabaseHealthReport]) -> DatabaseHealthLevel:
        """전체 시스템의 건강 상태 결정"""
        if not reports:
            return DatabaseHealthLevel.CRITICAL

        # 가장 심각한 상태를 전체 상태로 사용
        severity_order = [
            DatabaseHealthLevel.CRITICAL,
            DatabaseHealthLevel.MISSING,
            DatabaseHealthLevel.ERROR,
            DatabaseHealthLevel.WARNING,
            DatabaseHealthLevel.HEALTHY,
        ]

        for severity in severity_order:
            if any(report.health_level == severity for report in reports.values()):
                return severity

        return DatabaseHealthLevel.HEALTHY

    def _can_system_start_safely(self, reports: Dict[str, DatabaseHealthReport]) -> bool:
        """시스템이 안전하게 시작할 수 있는지 판단"""
        # settings DB는 반드시 필요 (다른 DB는 없어도 시작 가능)
        settings_report = reports.get('settings')
        if not settings_report:
            return False

        # settings DB가 작동 가능하면 시스템 시작 가능
        return settings_report.is_operational

    def check_database_compatibility_for_replacement(
        self,
        current_path: str,
        new_path: str,
        db_type: str
    ) -> bool:
        """데이터베이스 교체 시 호환성 확인"""
        self._logger.info(f"DB 교체 호환성 확인: {db_type}")

        try:
            new_report = self._check_individual_database(db_type, new_path)

            # 새 DB가 정상이고 최소 요구사항을 만족하는지 확인
            if not new_report.is_operational:
                self._logger.warning(f"새 DB가 작동 불가 상태: {new_path}")
                return False

            if new_report.table_count == 0:
                self._logger.warning(f"새 DB에 테이블이 없음: {new_path}")
                return False

            self._logger.info(f"DB 교체 호환성 확인 완료: {db_type}")
            return True

        except Exception as e:
            self._logger.error(f"DB 교체 호환성 확인 실패: {e}")
            return False
