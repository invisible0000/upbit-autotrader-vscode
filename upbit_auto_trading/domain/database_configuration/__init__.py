"""
데이터베이스 설정 도메인 - 패키지 초기화

DDD Domain Layer의 데이터베이스 설정 도메인을 정의합니다.
"""

# Entities
from .entities.database_profile import DatabaseProfile
from .entities.backup_record import BackupRecord, BackupStatus, BackupType

# Value Objects
from .value_objects.database_path import DatabasePath
from .value_objects.database_type import (
    DatabaseType,
    DatabaseCategory,
    get_all_database_types,
    get_database_type_by_name
)

# Aggregates
from .aggregates.database_configuration import DatabaseConfiguration

# Services
from .services.database_backup_service import DatabaseBackupService

# Repository Interfaces
from .repositories.idatabase_config_repository import (
    IDatabaseConfigRepository,
    IDatabaseValidationRepository
)

__all__ = [
    # Entities
    'DatabaseProfile',
    'BackupRecord',
    'BackupStatus',
    'BackupType',

    # Value Objects
    'DatabasePath',
    'DatabaseType',
    'DatabaseCategory',
    'get_all_database_types',
    'get_database_type_by_name',

    # Aggregates
    'DatabaseConfiguration',

    # Services
    'DatabaseBackupService',

    # Repository Interfaces
    'IDatabaseConfigRepository',
    'IDatabaseValidationRepository'
]
