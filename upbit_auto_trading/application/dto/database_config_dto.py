"""
Database Configuration DTOs for Application Layer

이 모듈은 데이터베이스 설정 도메인과 외부 계층 간의 데이터 전송을 위한 DTO를 정의합니다.
DDD 아키텍처에서 Application Layer의 경계를 명확히 하고
Domain Layer의 순수성을 보장하기 위해 사용됩니다.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class DatabaseStatusEnum(Enum):
    """데이터베이스 상태 열거형"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MIGRATING = "migrating"
    BACKUP_IN_PROGRESS = "backup_in_progress"


class DatabaseTypeEnum(Enum):
    """데이터베이스 타입 열거형"""
    SETTINGS = "settings"
    STRATEGIES = "strategies"
    MARKET_DATA = "market_data"


@dataclass(frozen=True)
class DatabaseProfileDto:
    """데이터베이스 프로필 정보 전송 객체"""

    profile_id: str
    profile_name: str
    database_type: DatabaseTypeEnum
    file_path: str
    is_active: bool
    created_at: datetime
    last_accessed_at: Optional[datetime] = None
    file_size_bytes: Optional[int] = None
    description: Optional[str] = None

    @classmethod
    def from_domain(cls, domain_profile) -> 'DatabaseProfileDto':
        """도메인 엔터티에서 DTO 생성"""
        # DatabaseType 도메인 문자열을 DTO enum으로 변환
        type_mapping = {
            "settings": DatabaseTypeEnum.SETTINGS,
            "strategies": DatabaseTypeEnum.STRATEGIES,
            "market_data": DatabaseTypeEnum.MARKET_DATA
        }

        return cls(
            profile_id=domain_profile.profile_id,  # 이미 문자열
            profile_name=domain_profile.name,
            database_type=type_mapping[domain_profile.database_type],
            file_path=str(domain_profile.file_path),
            is_active=domain_profile.is_active,
            created_at=domain_profile.created_at,
            last_accessed_at=domain_profile.last_accessed,
            description=domain_profile.metadata.get('description') if domain_profile.metadata else None
        )


@dataclass(frozen=True)
class BackupRecordDto:
    """백업 기록 정보 전송 객체"""

    backup_id: str
    profile_id: str
    backup_path: str
    created_at: datetime
    file_size_bytes: int
    compression_type: str
    backup_type: str  # MANUAL, AUTO, SCHEDULED
    description: Optional[str] = None

    @classmethod
    def from_domain(cls, domain_backup) -> 'BackupRecordDto':
        """도메인 엔터티에서 DTO 생성"""
        return cls(
            backup_id=domain_backup.backup_id.value,
            profile_id=domain_backup.profile_id.value,
            backup_path=str(domain_backup.backup_path.path),
            created_at=domain_backup.created_at,
            file_size_bytes=domain_backup.file_size_bytes,
            compression_type=domain_backup.compression_type.value,
            backup_type=domain_backup.backup_type.value,
            description=domain_backup.description
        )


@dataclass(frozen=True)
class DatabaseConfigDto:
    """데이터베이스 설정 정보 전송 객체 (간소화 버전)"""

    profiles: List[DatabaseProfileDto]
    active_profiles: Dict[DatabaseTypeEnum, str]  # type -> profile_id
    last_updated: datetime
    is_valid: bool = True
    validation_errors: Optional[List[str]] = None

    @classmethod
    def from_configuration_dto(cls, config_dto: 'DatabaseConfigurationDto') -> 'DatabaseConfigDto':
        """DatabaseConfigurationDto에서 변환"""
        return cls(
            profiles=config_dto.profiles,
            active_profiles=config_dto.active_profiles,
            last_updated=config_dto.last_updated,
            is_valid=config_dto.is_valid,
            validation_errors=config_dto.validation_errors
        )


@dataclass(frozen=True)
class DatabaseConfigurationDto:
    """데이터베이스 설정 전체 정보 전송 객체"""

    configuration_id: str
    profiles: List[DatabaseProfileDto]
    active_profiles: Dict[DatabaseTypeEnum, str]  # type -> profile_id
    last_updated: datetime
    is_valid: bool = True
    validation_errors: Optional[List[str]] = None

    @classmethod
    def from_domain(cls, domain_config) -> 'DatabaseConfigurationDto':
        """도메인 집합체에서 DTO 생성"""
        profiles = [
            DatabaseProfileDto.from_domain(profile)
            for profile in domain_config.get_all_profiles()
        ]

        # 활성 프로필 매핑
        active_profiles = {}
        for db_type in DatabaseTypeEnum:
            domain_type = cls._map_to_domain_type(db_type)
            active_profile = domain_config.get_active_profile(domain_type)
            if active_profile:
                active_profiles[db_type] = active_profile.profile_id.value

        return cls(
            configuration_id=domain_config.configuration_id.value,
            profiles=profiles,
            active_profiles=active_profiles,
            last_updated=domain_config.last_updated,
            is_valid=True,
            validation_errors=[]
        )

    @staticmethod
    def _map_to_domain_type(dto_type: DatabaseTypeEnum):
        """DTO 타입을 도메인 타입으로 변환"""
        from upbit_auto_trading.domain.database_configuration.value_objects.database_type import DatabaseType

        mapping = {
            DatabaseTypeEnum.SETTINGS: DatabaseType.SETTINGS,
            DatabaseTypeEnum.STRATEGIES: DatabaseType.STRATEGIES,
            DatabaseTypeEnum.MARKET_DATA: DatabaseType.MARKET_DATA
        }
        return mapping[dto_type]


@dataclass(frozen=True)
class DatabaseStatusDto:
    """데이터베이스 상태 정보 DTO"""

    profile_id: str
    status: str  # "ACTIVE", "INACTIVE", "ERROR", "WARNING"
    file_path: str
    is_active: bool
    last_checked: datetime
    file_size_bytes: int
    connection_healthy: bool
    issues: List[str]
    connection_count: int = 0
    last_activity: Optional[datetime] = None


@dataclass(frozen=True)
class CreateProfileRequestDto:
    """프로필 생성 요청 DTO"""

    profile_name: str
    database_type: DatabaseTypeEnum
    file_path: str
    description: Optional[str] = None
    should_activate: bool = False


@dataclass(frozen=True)
class UpdateProfileRequestDto:
    """프로필 업데이트 요청 DTO"""

    profile_id: str
    profile_name: Optional[str] = None
    file_path: Optional[str] = None
    description: Optional[str] = None


@dataclass(frozen=True)
class CreateBackupRequestDto:
    """백업 생성 요청 DTO"""

    profile_id: str
    backup_path: Optional[str] = None  # None이면 자동 경로 생성
    description: Optional[str] = None
    compression_enabled: bool = True


@dataclass(frozen=True)
class RestoreBackupRequestDto:
    """백업 복원 요청 DTO"""

    backup_id: str
    target_profile_id: Optional[str] = None  # None이면 원본 프로필로 복원
    create_backup_before_restore: bool = True


@dataclass(frozen=True)
class SwitchProfileRequestDto:
    """프로필 전환 요청 DTO"""

    database_type: DatabaseTypeEnum
    target_profile_id: str
    force_switch: bool = False  # 거래 중에도 강제 전환할지 여부


@dataclass(frozen=True)
class DatabaseValidationResultDto:
    """데이터베이스 검증 결과 DTO"""

    profile_id: str
    is_valid: bool
    validation_errors: List[str]
    warnings: List[str]
    validation_performed_at: datetime
    schema_version: Optional[str] = None
    integrity_check_passed: bool = True
    performance_issues: Optional[List[str]] = None
    file_size_bytes: Optional[int] = None


@dataclass(frozen=True)
class ValidationRequestDto:
    """데이터베이스 검증 요청 DTO"""

    profile_id: str
    validate_schema: bool = True
    check_performance: bool = False
    check_integrity: bool = True


@dataclass(frozen=True)
class DatabaseStatsDto:
    """데이터베이스 통계 정보 DTO"""

    profile_id: str
    database_type: DatabaseTypeEnum
    file_size_bytes: int
    table_count: int
    index_count: int
    table_statistics: Dict[str, Any]
    calculated_at: datetime
    error: Optional[str] = None


@dataclass(frozen=True)
class DatabaseHealthCheckDto:
    """데이터베이스 건강 상태 확인 DTO"""

    profile_id: str
    database_type: DatabaseTypeEnum
    health_status: str  # "healthy", "warning", "error"
    issues: List[str]
    last_checked: datetime
    file_size_bytes: Optional[int] = None
    connection_test_passed: bool = True


@dataclass(frozen=True)
class TradingStateDto:
    """거래 상태 정보 DTO"""

    is_trading_active: bool
    active_strategies: List[str]
    is_backtest_running: bool
    active_backtests: List[str]
    can_switch_database: bool
    blocking_operations: Optional[List[str]] = None  # 전환을 막는 작업들


# 호환성을 위한 별칭
BackupRequestDto = CreateBackupRequestDto
