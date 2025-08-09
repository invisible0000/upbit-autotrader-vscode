"""
Database Status Query Use Case

데이터베이스 상태 조회 및 모니터링을 담당하는 Use Case입니다.
실시간 데이터베이스 상태 정보와 통계를 제공합니다.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.dto.database_config_dto import (
    DatabaseProfileDto, DatabaseStatusDto, DatabaseTypeEnum,
    DatabaseHealthCheckDto, DatabaseStatsDto
)
from upbit_auto_trading.domain.database_configuration.repositories.idatabase_config_repository import (
    IDatabaseConfigRepository
)


class DatabaseStatusQueryUseCase:
    """데이터베이스 상태 조회 Use Case"""

    def __init__(self, repository: IDatabaseConfigRepository):
        self._repository = repository
        self._logger = create_component_logger("DatabaseStatusQuery")

    async def get_current_database_status(
        self,
        database_type: Optional[DatabaseTypeEnum] = None
    ) -> List[DatabaseStatusDto]:
        """현재 데이터베이스 상태를 조회합니다."""
        self._logger.info(f"📊 데이터베이스 상태 조회 시작: {database_type}")

        try:
            status_list = []

            # 활성 프로필들 조회
            active_profiles = await self._repository.get_active_profiles()

            for domain_type, profile in active_profiles.items():
                # 타입 필터 적용
                if database_type:
                    profile_type = self._map_domain_to_dto_type(domain_type)
                    if profile_type != database_type:
                        continue

                status = await self._get_profile_status(profile)
                status_list.append(status)

            # 활성 프로필이 없는 타입들도 확인
            if database_type is None:
                all_types = [DatabaseTypeEnum.SETTINGS, DatabaseTypeEnum.STRATEGIES, DatabaseTypeEnum.MARKET_DATA]
                active_domain_types = set(active_profiles.keys())

                for dto_type in all_types:
                    domain_type = self._map_dto_to_domain_type(dto_type)
                    if domain_type not in active_domain_types:
                        # 비활성 상태로 추가
                        status_list.append(DatabaseStatusDto(
                            profile_id="",
                            database_type=dto_type,
                            status="INACTIVE",
                            file_path="",
                            is_active=False,
                            last_checked=datetime.now(),
                            file_size_bytes=0,
                            connection_healthy=False,
                            issues=["활성 프로필이 없습니다"]
                        ))

            self._logger.info(f"✅ 데이터베이스 상태 조회 완료: {len(status_list)}개")
            return status_list

        except Exception as e:
            self._logger.error(f"❌ 데이터베이스 상태 조회 실패: {e}")
            return []

    async def get_database_statistics(
        self,
        profile_id: str,
        include_table_stats: bool = True
    ) -> Optional[DatabaseStatsDto]:
        """데이터베이스 통계 정보를 조회합니다."""
        self._logger.info(f"📈 데이터베이스 통계 조회 시작: {profile_id}")

        try:
            profile = await self._repository.load_profile(profile_id)
            if profile is None:
                return None

            stats = await self._calculate_database_stats(profile, include_table_stats)
            self._logger.info(f"✅ 데이터베이스 통계 조회 완료: {profile_id}")
            return stats

        except Exception as e:
            self._logger.error(f"❌ 데이터베이스 통계 조회 실패: {e}")
            return None

    async def monitor_database_connections(self) -> Dict[str, Any]:
        """데이터베이스 연결 상태를 모니터링합니다."""
        self._logger.info("🔍 데이터베이스 연결 모니터링 시작")

        try:
            connection_info = {
                "timestamp": datetime.now(),
                "active_connections": {},
                "connection_pool_status": {},
                "performance_metrics": {}
            }

            active_profiles = await self._repository.get_active_profiles()

            for domain_type, profile in active_profiles.items():
                connection_status = await self._check_connection_status(profile)
                connection_info["active_connections"][domain_type] = connection_status

            self._logger.info("✅ 데이터베이스 연결 모니터링 완료")
            return connection_info

        except Exception as e:
            self._logger.error(f"❌ 데이터베이스 연결 모니터링 실패: {e}")
            return {"error": str(e), "timestamp": datetime.now()}

    async def get_database_activity_log(
        self,
        profile_id: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """데이터베이스 활동 로그를 조회합니다."""
        self._logger.info(f"📋 데이터베이스 활동 로그 조회: {profile_id} (최근 {hours}시간)")

        try:
            # 향후 구현: 실제 활동 로그 시스템과 연동
            # 현재는 기본 정보만 반환
            since = datetime.now() - timedelta(hours=hours)

            activity_log = [
                {
                    "timestamp": datetime.now(),
                    "action": "status_check",
                    "profile_id": profile_id,
                    "details": "시스템 상태 확인"
                }
            ]

            return activity_log

        except Exception as e:
            self._logger.error(f"❌ 활동 로그 조회 실패: {e}")
            return []

    async def check_database_disk_usage(self) -> Dict[str, Any]:
        """데이터베이스 디스크 사용량을 확인합니다."""
        self._logger.info("💾 데이터베이스 디스크 사용량 확인")

        try:
            disk_usage = {
                "timestamp": datetime.now(),
                "total_database_size": 0,
                "database_sizes": {},
                "backup_sizes": {},
                "available_space": None
            }

            active_profiles = await self._repository.get_active_profiles()

            for domain_type, profile in active_profiles.items():
                if profile.file_path.exists():
                    size = profile.file_path.stat().st_size
                    disk_usage["database_sizes"][domain_type] = size
                    disk_usage["total_database_size"] += size

            # 백업 크기 계산
            backup_records = await self._repository.get_all_backup_records()
            for backup in backup_records:
                if backup.backup_file_path.exists():
                    size = backup.backup_file_path.stat().st_size
                    db_type = backup.source_database_type
                    if db_type not in disk_usage["backup_sizes"]:
                        disk_usage["backup_sizes"][db_type] = 0
                    disk_usage["backup_sizes"][db_type] += size

            self._logger.info("✅ 디스크 사용량 확인 완료")
            return disk_usage

        except Exception as e:
            self._logger.error(f"❌ 디스크 사용량 확인 실패: {e}")
            return {"error": str(e), "timestamp": datetime.now()}

    async def _get_profile_status(self, profile) -> DatabaseStatusDto:
        """프로필 상태 정보 생성"""
        status = "ACTIVE" if profile.is_active else "INACTIVE"
        issues = []
        connection_healthy = True

        try:
            # 파일 존재 확인
            if not profile.file_path.exists():
                status = "ERROR"
                issues.append("데이터베이스 파일이 존재하지 않습니다")
                connection_healthy = False
            else:
                # 연결 테스트
                with sqlite3.connect(str(profile.file_path), timeout=5.0) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")

        except sqlite3.Error as e:
            status = "ERROR"
            issues.append(f"데이터베이스 연결 실패: {e}")
            connection_healthy = False
        except Exception as e:
            status = "WARNING"
            issues.append(f"상태 확인 중 오류: {e}")

        return DatabaseStatusDto(
            profile_id=profile.profile_id,
            database_type=self._map_domain_to_dto_type(profile.database_type),
            status=status,
            file_path=str(profile.file_path),
            is_active=profile.is_active,
            last_checked=datetime.now(),
            file_size_bytes=profile.file_path.stat().st_size if profile.file_path.exists() else 0,
            connection_healthy=connection_healthy,
            issues=issues
        )

    async def _calculate_database_stats(self, profile, include_table_stats: bool) -> DatabaseStatsDto:
        """데이터베이스 통계 계산"""
        try:
            with sqlite3.connect(str(profile.file_path)) as conn:
                cursor = conn.cursor()

                # 기본 통계
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
                index_count = cursor.fetchone()[0]

                # 파일 크기
                file_size = profile.file_path.stat().st_size if profile.file_path.exists() else 0

                # 테이블별 통계 (요청 시)
                table_stats = {}
                if include_table_stats:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()

                    for (table_name,) in tables:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
                            row_count = cursor.fetchone()[0]
                            table_stats[table_name] = {"row_count": row_count}
                        except sqlite3.Error:
                            table_stats[table_name] = {"row_count": 0, "error": "접근 불가"}

                return DatabaseStatsDto(
                    profile_id=profile.profile_id,
                    database_type=self._map_domain_to_dto_type(profile.database_type),
                    file_size_bytes=file_size,
                    table_count=table_count,
                    index_count=index_count,
                    table_statistics=table_stats,
                    calculated_at=datetime.now()
                )

        except Exception as e:
            # 오류 발생 시 기본 통계 반환
            return DatabaseStatsDto(
                profile_id=profile.profile_id,
                database_type=self._map_domain_to_dto_type(profile.database_type),
                file_size_bytes=0,
                table_count=0,
                index_count=0,
                table_statistics={},
                calculated_at=datetime.now(),
                error=str(e)
            )

    async def _check_connection_status(self, profile) -> Dict[str, Any]:
        """연결 상태 확인"""
        connection_status = {
            "profile_id": profile.profile_id,
            "is_connected": False,
            "response_time_ms": None,
            "last_activity": None,
            "error": None
        }

        try:
            start_time = datetime.now()

            with sqlite3.connect(str(profile.file_path), timeout=5.0) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")

                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds() * 1000

                connection_status.update({
                    "is_connected": True,
                    "response_time_ms": response_time,
                    "last_activity": datetime.now()
                })

        except Exception as e:
            connection_status["error"] = str(e)

        return connection_status

    @staticmethod
    def _map_domain_to_dto_type(domain_type: str) -> DatabaseTypeEnum:
        """도메인 타입을 DTO 타입으로 변환"""
        mapping = {
            "settings": DatabaseTypeEnum.SETTINGS,
            "strategies": DatabaseTypeEnum.STRATEGIES,
            "market_data": DatabaseTypeEnum.MARKET_DATA
        }
        return mapping.get(domain_type, DatabaseTypeEnum.SETTINGS)

    @staticmethod
    def _map_dto_to_domain_type(dto_type: DatabaseTypeEnum) -> str:
        """DTO 타입을 도메인 타입으로 변환"""
        mapping = {
            DatabaseTypeEnum.SETTINGS: "settings",
            DatabaseTypeEnum.STRATEGIES: "strategies",
            DatabaseTypeEnum.MARKET_DATA: "market_data"
        }
        return mapping[dto_type]
