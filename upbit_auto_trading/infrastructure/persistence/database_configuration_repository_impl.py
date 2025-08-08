"""
Database Configuration Repository Implementation

데이터베이스 구성 정보를 파일 시스템에 저장하는 Repository 구현체입니다.
DDD의 Infrastructure Layer에서 실제 데이터 저장 로직을 담당합니다.
"""

import json
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from upbit_auto_trading.domain.database_configuration.repositories.database_configuration_repository import IDatabaseConfigurationRepository
from upbit_auto_trading.domain.database_configuration.entities.database_configuration import DatabaseConfiguration
from upbit_auto_trading.domain.database_configuration.value_objects.database_path import DatabasePath
from upbit_auto_trading.infrastructure.logging import create_component_logger


class FileSystemDatabaseConfigurationRepository(IDatabaseConfigurationRepository):
    """파일 시스템 기반 데이터베이스 구성 Repository"""

    def __init__(self, config_file_path: Optional[str] = None):
        self.logger = create_component_logger("DatabaseConfigRepository")

        # 기본 설정 파일 경로
        if config_file_path is None:
            from upbit_auto_trading.infrastructure.configuration.paths import infrastructure_paths
            self.config_file = infrastructure_paths.CONFIG_DIR / "database_config.yaml"  # ✅ 올바른 파일명
        else:
            self.config_file = Path(config_file_path)

        # 설정 파일 디렉토리 생성
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"📁 Database Configuration Repository 초기화: {self.config_file}")

    def save(self, configuration: DatabaseConfiguration) -> None:
        """데이터베이스 구성 저장"""
        try:
            # 기존 전체 설정 로드 (databases 섹션 포함)
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    full_data = yaml.safe_load(f) or {}
            else:
                full_data = {}

            # databases 섹션 초기화
            if 'databases' not in full_data:
                full_data['databases'] = {}

            # 새 구성 업데이트
            full_data['databases'][configuration.database_type] = {
                'path': str(configuration.database_path.path),
                'last_modified': datetime.now().isoformat(),
                'source': configuration.source_path
            }

            # 파일에 저장
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(full_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            self.logger.info(f"✅ 데이터베이스 구성 저장 완료: {configuration.database_type}")

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 구성 저장 실패: {e}")
            raise

    def get_by_type(self, database_type: str) -> Optional[DatabaseConfiguration]:
        """타입별 데이터베이스 구성 조회"""
        try:
            configurations = self._load_all_configurations()

            if database_type not in configurations:
                self.logger.debug(f"🔍 데이터베이스 구성 없음: {database_type}")
                return None

            config_data = configurations[database_type]

            # DatabaseConfiguration 객체 생성
            database_path = DatabasePath(Path(config_data['database_path']))

            configuration = DatabaseConfiguration(
                database_type=config_data['database_type'],
                database_path=database_path,
                is_active=config_data.get('is_active', True),
                created_at=datetime.fromisoformat(config_data['last_modified']) if config_data.get('last_modified') else None,
                updated_at=datetime.fromisoformat(config_data['last_modified']) if config_data.get('last_modified') else None,
                source_path=config_data.get('source')
            )

            self.logger.debug(f"✅ 데이터베이스 구성 조회 완료: {database_type}")
            return configuration

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 구성 조회 실패: {e}")
            return None

    def get_all(self) -> List[DatabaseConfiguration]:
        """모든 데이터베이스 구성 조회"""
        try:
            configurations = self._load_all_configurations()
            result = []

            for database_type in configurations:
                config = self.get_by_type(database_type)
                if config:
                    result.append(config)

            self.logger.debug(f"✅ 모든 데이터베이스 구성 조회 완료: {len(result)}개")
            return result

        except Exception as e:
            self.logger.error(f"❌ 모든 데이터베이스 구성 조회 실패: {e}")
            return []

    def delete(self, database_type: str) -> bool:
        """데이터베이스 구성 삭제"""
        try:
            configurations = self._load_all_configurations()

            if database_type not in configurations:
                self.logger.debug(f"🔍 삭제할 데이터베이스 구성 없음: {database_type}")
                return False

            del configurations[database_type]

            # 파일에 저장
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(configurations, f, default_flow_style=False, allow_unicode=True)

            self.logger.info(f"✅ 데이터베이스 구성 삭제 완료: {database_type}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 구성 삭제 실패: {e}")
            return False

    def exists(self, database_type: str) -> bool:
        """데이터베이스 구성 존재 여부 확인"""
        try:
            configurations = self._load_all_configurations()
            exists = database_type in configurations
            self.logger.debug(f"🔍 데이터베이스 구성 존재 여부: {database_type} = {exists}")
            return exists

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 구성 존재 여부 확인 실패: {e}")
            return False

    def _load_all_configurations(self) -> Dict[str, Any]:
        """모든 설정 로드"""
        try:
            if not self.config_file.exists():
                self.logger.debug(f"📄 설정 파일 없음, 빈 설정 반환: {self.config_file}")
                return {}

            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}

            # YAML 구조 정규화: databases 섹션을 직접 반환
            if 'databases' in data:
                configurations = data['databases']
                # 각 구성에 database_type 필드 추가
                for db_type, config in configurations.items():
                    config['database_type'] = db_type
                    # path 키를 database_path로 정규화
                    if 'path' in config:
                        config['database_path'] = config['path']

                self.logger.debug(f"📄 설정 파일 로드 완료: {len(configurations)}개 구성")
                return configurations
            else:
                self.logger.debug(f"📄 databases 섹션 없음, 빈 설정 반환")
                return {}

        except Exception as e:
            self.logger.error(f"❌ 설정 파일 로드 실패: {e}")
            return {}

    def initialize_default_configurations(self) -> None:
        """기본 데이터베이스 구성 초기화"""
        try:
            # 기본 데이터 디렉토리 경로
            from upbit_auto_trading.infrastructure.configuration.paths import infrastructure_paths
            data_dir = infrastructure_paths.DATA_DIR

            # 기본 구성들
            default_configs = [
                ('settings', data_dir / "settings.sqlite3"),
                ('strategies', data_dir / "strategies.sqlite3"),
                ('market_data', data_dir / "market_data.sqlite3")
            ]

            for db_type, db_path in default_configs:
                if not self.exists(db_type):
                    database_path = DatabasePath(db_path)
                    configuration = DatabaseConfiguration(
                        database_type=db_type,
                        database_path=database_path,
                        is_active=True
                    )
                    self.save(configuration)
                    self.logger.info(f"📋 기본 데이터베이스 구성 생성: {db_type}")

            self.logger.info("✅ 기본 데이터베이스 구성 초기화 완료")

        except Exception as e:
            self.logger.error(f"❌ 기본 데이터베이스 구성 초기화 실패: {e}")
            raise
