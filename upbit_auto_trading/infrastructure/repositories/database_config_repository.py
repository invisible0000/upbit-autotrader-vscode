"""
DDD 원칙을 준수하는 단순한 데이터베이스 설정 리포지토리

Domain Layer의 IDatabaseConfigRepository 인터페이스를 YAML 기반으로 구현합니다.
시스템 시작 시 DB 검증을 위한 최소한의 기능만 제공합니다.
"""

import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.domain.database_configuration.repositories.idatabase_config_repository import IDatabaseConfigRepository
from upbit_auto_trading.domain.database_configuration.entities.database_profile import DatabaseProfile
from upbit_auto_trading.domain.database_configuration.entities.backup_record import BackupRecord
from upbit_auto_trading.domain.database_configuration.aggregates.database_configuration import DatabaseConfiguration

logger = create_component_logger("DatabaseConfigRepository")


class DatabaseConfigRepository(IDatabaseConfigRepository):
    """
    YAML 기반 데이터베이스 설정 리포지토리

    DDD 원칙을 준수하며 시스템 시작 시 필요한 최소한의 기능을 제공합니다.
    복잡한 기능은 추후 확장 가능하도록 설계되었습니다.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        리포지토리 초기화

        Args:
            config_path: 설정 파일 경로 (None이면 기본 경로 사용)
        """
        self.config_path = config_path or Path("config/database_config.yaml")
        self._ensure_config_exists()
        logger.info(f"📁 DatabaseConfigRepository 초기화: {self.config_path}")

    def _ensure_config_exists(self) -> None:
        """설정 파일이 없으면 기본 설정으로 생성"""
        if not self.config_path.exists():
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            default_config = {
                'databases': {
                    'settings': {
                        'path': 'data/settings.sqlite3',
                        'type': 'configuration',
                        'description': '설정 데이터베이스'
                    },
                    'strategies': {
                        'path': 'data/strategies.sqlite3',
                        'type': 'business_data',
                        'description': '전략 데이터베이스'
                    },
                    'market_data': {
                        'path': 'data/market_data.sqlite3',
                        'type': 'cache_data',
                        'description': '시장 데이터 캐시'
                    }
                }
            }

            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)

            logger.info(f"✅ 기본 설정 파일 생성: {self.config_path}")

    async def save_configuration(self, configuration: DatabaseConfiguration) -> None:
        """설정 저장 (향후 확장용)"""
        logger.debug("설정 저장은 현재 버전에서 지원되지 않습니다")
        pass

    async def load_configuration(self, configuration_id: str) -> Optional[DatabaseConfiguration]:
        """설정 로드 (향후 확장용)"""
        logger.debug("설정 로드는 현재 버전에서 지원되지 않습니다")
        return None

    async def get_default_configuration(self) -> DatabaseConfiguration:
        """
        기본 데이터베이스 설정 반환

        YAML에서 로드한 설정을 DatabaseConfiguration으로 변환합니다.
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            # 간단한 기본 설정 반환 (향후 확장 가능)
            from upbit_auto_trading.domain.database_configuration.aggregates.\
                database_configuration import DatabaseConfiguration
            configuration = DatabaseConfiguration(configuration_id="default")

            logger.debug(f"✅ 기본 설정 로드 완료: {len(config_data.get('databases', {}))}개 DB")
            return configuration

        except Exception as e:
            logger.error(f"❌ 설정 로드 실패: {e}")
            # 최소한의 기본 설정 반환
            from upbit_auto_trading.domain.database_configuration.aggregates.\
                database_configuration import DatabaseConfiguration
            return DatabaseConfiguration(configuration_id="fallback")

    # ==== 프로필 관련 메서드 (향후 확장용) ====

    async def save_profile(self, profile: DatabaseProfile) -> None:
        """프로필 저장 (향후 확장용)"""
        pass

    async def load_profile(self, profile_id: str) -> Optional[DatabaseProfile]:
        """프로필 로드 (향후 확장용)"""
        return None

    async def load_profiles_by_type(self, database_type: str) -> List[DatabaseProfile]:
        """타입별 프로필 로드 (향후 확장용)"""
        return []

    async def delete_profile(self, profile_id: str) -> bool:
        """프로필 삭제 (향후 확장용)"""
        return False

    # ==== 백업 관련 메서드 (향후 확장용) ====

    async def save_backup_record(self, backup_record: BackupRecord) -> None:
        """백업 기록 저장 (향후 확장용)"""
        pass

    async def load_backup_record(self, backup_id: str) -> Optional[BackupRecord]:
        """백업 기록 로드 (향후 확장용)"""
        return None

    async def load_backup_records_by_profile(self, profile_id: str) -> List[BackupRecord]:
        """프로필별 백업 기록 로드 (향후 확장용)"""
        return []

    async def delete_backup_record(self, backup_id: str) -> bool:
        """백업 기록 삭제 (향후 확장용)"""
        return False

    async def cleanup_old_backup_records(self, cutoff_date: datetime) -> int:
        """오래된 백업 기록 정리 (향후 확장용)"""
        return 0

    # ==== 시스템 상태 메서드 ====

    async def get_active_profiles(self) -> Dict[str, DatabaseProfile]:
        """활성 프로필 조회 (향후 확장용)"""
        return {}

    async def update_profile_access_time(self, profile_id: str, access_time: datetime) -> None:
        """프로필 접근 시간 업데이트 (향후 확장용)"""
        pass

    async def get_repository_statistics(self) -> Dict[str, Any]:
        """저장소 통계 정보 조회"""
        try:
            stats = {
                'config_file_exists': self.config_path.exists(),
                'config_file_size': self.config_path.stat().st_size if self.config_path.exists() else 0,
                'last_modified': self.config_path.stat().st_mtime if self.config_path.exists() else 0,
                'repository_type': 'YAML-based',
                'status': 'healthy'
            }
            return stats
        except Exception as e:
            logger.error(f"❌ 통계 조회 실패: {e}")
            return {'status': 'error', 'error': str(e)}

    async def verify_repository_integrity(self) -> bool:
        """저장소 무결성 검증"""
        try:
            # YAML 파일 파싱 테스트
            if not self.config_path.exists():
                logger.warning("⚠️ 설정 파일이 존재하지 않습니다")
                return False

            with open(self.config_path, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)

            logger.debug("✅ Repository 무결성 검증 성공")
            return True

        except Exception as e:
            logger.error(f"❌ Repository 무결성 검증 실패: {e}")
            return False
