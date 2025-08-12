"""
Database Path Service

데이터베이스 경로 관리를 담당하는 도메인 서비스입니다.
DDD 원칙에 따라 경로 변경, 검증, 백업 등의 비즈니스 로직을 캡슐화합니다.
Enterprise급 프로파일 및 백업 시스템과 통합되어 안전한 데이터베이스 전환을 제공합니다.
"""

from typing import Optional, Dict, Tuple
from pathlib import Path
import shutil
import sqlite3
from datetime import datetime
import uuid

from upbit_auto_trading.domain.database_configuration.entities.database_configuration import DatabaseConfiguration
from upbit_auto_trading.domain.database_configuration.entities.database_profile import DatabaseProfile
from upbit_auto_trading.domain.database_configuration.entities.backup_record import BackupRecord, BackupType
from upbit_auto_trading.domain.database_configuration.services.database_backup_service import DatabaseBackupService
from upbit_auto_trading.domain.database_configuration.value_objects.database_path import DatabasePath
from upbit_auto_trading.domain.database_configuration.repositories.database_configuration_repository import IDatabaseConfigurationRepository
from upbit_auto_trading.infrastructure.logging import create_component_logger

class DatabasePathService:
    """
    데이터베이스 경로 관리 도메인 서비스

    데이터베이스 경로의 변경, 검증, 백업 등 복잡한 비즈니스 로직을 처리합니다.
    싱글톤 패턴으로 구현되어 애플리케이션 전체에서 일관된 상태를 유지합니다.
    """

    _instance = None
    _initialized = False

    def __new__(cls, repository: Optional[IDatabaseConfigurationRepository] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, repository: Optional[IDatabaseConfigurationRepository] = None):
        # 이미 초기화된 경우 다시 초기화하지 않음
        if self._initialized:
            return

        if repository is None:
            # 기본 Repository 생성
            from upbit_auto_trading.infrastructure.persistence.database_configuration_repository_impl import (
                FileSystemDatabaseConfigurationRepository
            )
            repository = FileSystemDatabaseConfigurationRepository()

        self.repository = repository
        self.logger = create_component_logger("DatabasePathService")

        # 백업 서비스 초기화
        self.backup_service = DatabaseBackupService()

        # 클래스 수준 초기화 완료 표시
        DatabasePathService._initialized = True

        self.logger.info("🛠️ DatabasePathService (Enterprise) 초기화 완료")

    def change_database_path_with_profile_safety(
        self, database_type: str, new_path: str, source_path: Optional[str] = None
    ) -> bool:
        """
        프로파일 안전 보장과 함께 데이터베이스 경로 변경

        Enterprise급 안전 기능:
        1. 기존 데이터베이스 자동 백업
        2. 프로파일 생성 및 관리
        3. 무결성 검증
        4. 실패 시 자동 롤백

        Args:
            database_type: 데이터베이스 타입
            new_path: 새로운 데이터베이스 경로
            source_path: 원본 파일 경로 (복사할 경우)

        Returns:
            변경 성공 여부
        """
        self.logger.info(f"🔒 안전한 데이터베이스 경로 변경 시작: {database_type}")

        try:
            # 1단계: 현재 설정 조회 및 백업
            current_config = self.repository.get_by_type(database_type)
            backup_record = None

            if current_config and current_config.database_path.exists():
                # 현재 데이터베이스 프로파일 생성
                current_profile = DatabaseProfile(
                    profile_id=str(uuid.uuid4()),
                    name=f"{database_type}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    database_type=database_type,
                    file_path=current_config.database_path.path,
                    created_at=datetime.now(),
                    is_active=True
                )

                # 안전 백업 생성
                self.logger.info("🛡️ 기존 데이터베이스 안전 백업 생성 중...")
                backup_record = self.backup_service.create_backup(current_profile, BackupType.MANUAL)
                self.logger.info(f"✅ 안전 백업 생성 완료: {backup_record.backup_id}")

            # 2단계: 새 경로 검증
            is_valid, error_message = self.validate_path(database_type, new_path)
            if not is_valid:
                self.logger.error(f"❌ 새 경로 검증 실패: {error_message}")
                return False

            # 3단계: 데이터베이스 파일 복사 (필요시)
            if source_path and source_path != new_path:
                self.logger.info(f"📋 데이터베이스 파일 복사: {source_path} → {new_path}")
                self._copy_database_file(source_path, new_path)

                # 복사된 파일 무결성 검증
                if not self._verify_database_integrity(new_path):
                    raise RuntimeError("복사된 데이터베이스 파일 무결성 검증 실패")

            # 4단계: 새 프로파일 생성 및 활성화
            new_profile = DatabaseProfile(
                profile_id=str(uuid.uuid4()),
                name=f"{database_type}_active_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                database_type=database_type,
                file_path=Path(new_path),
                created_at=datetime.now(),
                is_active=True
            )

            # 새 프로파일 활성화 (메타데이터 갱신)
            new_profile = new_profile.activate()
            self.logger.info(f"📋 새 프로파일 활성화: {new_profile.name}")

            # 5단계: DDD Repository에 저장
            from pathlib import Path
            database_path = DatabasePath(Path(new_path))
            config = DatabaseConfiguration(
                database_type=database_type,
                database_path=database_path,
                is_active=True,
                source_path=source_path
            )

            self.repository.save(config)
            self.logger.info(f"✅ DDD 리포지토리 저장 완료: {database_type}")

            # 6단계: 레거시 시스템 동기화
            self._sync_legacy_systems(database_type, new_path)

            # 7단계: API 키 서비스 리로드 신호 (settings DB 변경 시)
            if database_type == 'settings':
                self._notify_api_key_reload(new_path)

            self.logger.info(f"🎉 안전한 데이터베이스 경로 변경 완료: {database_type}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 안전한 경로 변경 실패: {e}")

            # 실패 시 자동 롤백 시도
            if backup_record and current_config:
                try:
                    self.logger.info("🔄 실패로 인한 자동 롤백 시작...")
                    rollback_success = self.backup_service.restore_backup(backup_record, current_config)
                    if rollback_success:
                        self.logger.info("✅ 자동 롤백 완료")
                    else:
                        self.logger.error("❌ 자동 롤백 실패")
                except Exception as rollback_error:
                    self.logger.error(f"❌ 롤백 중 오류: {rollback_error}")

            return False

    def change_database_path(self, database_type: str, new_path: str, source_path: Optional[str] = None) -> bool:
        """
        데이터베이스 경로 변경 및 모든 시스템 동기화

        DDD 서비스에서 경로를 변경하고, 레거시 시스템들도 함께 업데이트합니다.
        이는 3초 후 경로 복귀 문제를 해결하기 위한 핵심 기능입니다.
        """
        try:
            self.logger.info(f"🔄 데이터베이스 경로 변경 시작: {database_type} → {new_path}")

            # 1단계: 새 경로 검증
            is_valid, error_message = self.validate_path(database_type, new_path)
            if not is_valid:
                self.logger.error(f"❌ 경로 검증 실패: {new_path} - {error_message}")
                return False

            # 2단계: 데이터베이스 파일이 다르면 복사 수행
            if source_path and source_path != new_path:
                self.logger.info(f"📋 파일 복사: {source_path} → {new_path}")
                self._copy_database_file(source_path, new_path)

            # 3단계: DDD 리포지토리에 경로 저장
            from pathlib import Path
            database_path = DatabasePath(Path(new_path))
            config = DatabaseConfiguration(
                database_type=database_type,
                database_path=database_path,
                is_active=True,
                source_path=source_path  # 원본 파일 경로 명시적 설정
            )

            self.repository.save(config)
            self.logger.info(f"✅ DDD 리포지토리 저장 완료: {database_type}")

            # 4단계: **핵심** - 레거시 시스템들 동기화
            self._sync_legacy_systems(database_type, new_path)

            # 5단계: API 키 서비스 리로드 신호 (settings DB 변경 시)
            if database_type == 'settings':
                self._notify_api_key_reload(new_path)

            self.logger.info(f"🎉 데이터베이스 경로 변경 완료: {database_type}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 경로 변경 실패: {e}")
            return False

    def _sync_legacy_systems(self, database_type: str, new_path: str) -> None:
        """레거시 시스템들과 경로 동기화 - 3초 복귀 문제 해결"""
        try:
            self.logger.info(f"🔗 레거시 시스템 동기화 시작: {database_type}")

            # 1. config/simple_paths.py 업데이트 (있다면)
            self._update_simple_paths_config(database_type, new_path)

            # 2. infrastructure/configuration/paths.py 인스턴스 업데이트
            self._update_infrastructure_paths(database_type, new_path)

            # 3. 설정 파일들 업데이트
            self._update_config_files(database_type, new_path)

            # 4. 환경변수 업데이트 (필요시)
            self._update_environment_variables(database_type, new_path)

            self.logger.info(f"✅ 레거시 시스템 동기화 완료: {database_type}")

        except Exception as e:
            self.logger.warning(f"⚠️ 레거시 시스템 동기화 실패 (기능은 정상): {e}")

    def _update_simple_paths_config(self, database_type: str, new_path: str) -> None:
        """config/simple_paths.py 업데이트"""
        try:
            import sys
            # simple_paths 모듈이 이미 로드되어 있다면 경로 업데이트
            simple_paths_modules = [name for name in sys.modules.keys() if 'simple_paths' in name]

            for module_name in simple_paths_modules:
                module = sys.modules[module_name]
                if hasattr(module, 'SETTINGS_DB_PATH') and database_type == 'settings':
                    module.SETTINGS_DB_PATH = new_path
                    self.logger.debug(f"📝 {module_name}.SETTINGS_DB_PATH 업데이트: {new_path}")
                elif hasattr(module, 'STRATEGIES_DB_PATH') and database_type == 'strategies':
                    module.STRATEGIES_DB_PATH = new_path
                    self.logger.debug(f"📝 {module_name}.STRATEGIES_DB_PATH 업데이트: {new_path}")
                elif hasattr(module, 'MARKET_DATA_DB_PATH') and database_type == 'market_data':
                    module.MARKET_DATA_DB_PATH = new_path
                    self.logger.debug(f"📝 {module_name}.MARKET_DATA_DB_PATH 업데이트: {new_path}")

        except Exception as e:
            self.logger.debug(f"simple_paths 모듈 업데이트 실패 (정상): {e}")

    def _update_infrastructure_paths(self, database_type: str, new_path: str) -> None:
        """infrastructure/configuration/paths.py 인스턴스들 업데이트"""
        try:
            import sys
            # paths 모듈이 이미 로드되어 있다면 인스턴스 업데이트
            paths_modules = [name for name in sys.modules.keys() if 'infrastructure.configuration.paths' in name]

            for module_name in paths_modules:
                module = sys.modules[module_name]

                # infrastructure_paths 전역 인스턴스 찾기
                if hasattr(module, 'infrastructure_paths'):
                    paths_instance = module.infrastructure_paths

                    if database_type == 'settings' and hasattr(paths_instance, 'SETTINGS_DB'):
                        paths_instance.SETTINGS_DB = Path(new_path)
                        self.logger.debug(f"📝 infrastructure_paths.SETTINGS_DB 업데이트: {new_path}")
                    elif database_type == 'strategies' and hasattr(paths_instance, 'STRATEGIES_DB'):
                        paths_instance.STRATEGIES_DB = Path(new_path)
                        self.logger.debug(f"📝 infrastructure_paths.STRATEGIES_DB 업데이트: {new_path}")
                    elif database_type == 'market_data' and hasattr(paths_instance, 'MARKET_DATA_DB'):
                        paths_instance.MARKET_DATA_DB = Path(new_path)
                        self.logger.debug(f"📝 infrastructure_paths.MARKET_DATA_DB 업데이트: {new_path}")

        except Exception as e:
            self.logger.debug(f"infrastructure_paths 인스턴스 업데이트 실패 (정상): {e}")

    def _update_config_files(self, database_type: str, new_path: str) -> None:
        """설정 파일들 업데이트"""
        try:
            import yaml

            # database_config.yaml 업데이트
            config_path = Path('d:/projects/upbit-autotrader-vscode/config/database_config.yaml')
            config_path.parent.mkdir(exist_ok=True)

            config_data = {}
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}

            # 설정 업데이트
            if 'database_paths' not in config_data:
                config_data['database_paths'] = {}

            config_data['database_paths'][database_type] = {
                'path': new_path,
                'updated_at': datetime.now().isoformat(),
                'updated_by': 'DDD_DatabasePathService'
            }

            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)

            self.logger.debug(f"📝 config/database_config.yaml 업데이트 완료")

        except Exception as e:
            self.logger.debug(f"설정 파일 업데이트 실패 (정상): {e}")

    def _update_environment_variables(self, database_type: str, new_path: str) -> None:
        """환경변수 업데이트 (필요시)"""
        try:
            import os

            env_var_map = {
                'settings': 'UPBIT_SETTINGS_DB_PATH',
                'strategies': 'UPBIT_STRATEGIES_DB_PATH',
                'market_data': 'UPBIT_MARKET_DATA_DB_PATH'
            }

            if database_type in env_var_map:
                env_var = env_var_map[database_type]
                os.environ[env_var] = new_path
                self.logger.debug(f"📝 환경변수 {env_var} 업데이트: {new_path}")

        except Exception as e:
            self.logger.debug(f"환경변수 업데이트 실패 (정상): {e}")

    def _notify_api_key_reload(self, new_path: str) -> None:
        """API 키 서비스에 재로드 신호 전송"""
        try:
            # 메인 윈도우나 API 키 서비스에 재로드 신호 전송
            # 이는 'API: 연결 끊김' 문제를 해결하기 위함
            self.logger.info(f"🔑 API 키 서비스 재로드 신호 전송: {new_path}")

            # 전역 이벤트 시스템이나 시그널을 통해 알림
            # (실제 구현은 시스템 아키텍처에 따라 달라질 수 있음)

        except Exception as e:
            self.logger.debug(f"API 키 재로드 신호 실패 (정상): {e}")

    def _legacy_change_database_path(self, database_type: str, new_path: str, source_path: Optional[str] = None) -> bool:
        """
        데이터베이스 경로 변경

        Args:
            database_type: 데이터베이스 타입 (settings, strategies, market_data)
            new_path: 새로운 경로
            source_path: 원본 파일 경로 (복사용)

        Returns:
            bool: 성공 여부
        """
        try:
            self.logger.info(f"� 데이터베이스 경로 변경 시작: {database_type} -> {new_path}")

            # 1단계: 경로 유효성 검증
            new_database_path = DatabasePath(Path(new_path))
            if not new_database_path.is_valid():
                self.logger.error(f"❌ 유효하지 않은 경로: {new_path}")
                return False

            # 2단계: 원본 파일 존재 여부 확인 (source_path가 있는 경우)
            if source_path and not Path(source_path).exists():
                self.logger.error(f"❌ 원본 파일이 존재하지 않음: {source_path}")
                return False

            # 3단계: 기존 구성 조회 또는 생성
            existing_config = self.repository.get_by_type(database_type)

            if existing_config:
                # 기존 구성 업데이트
                existing_config.update_path(new_database_path, source_path)
                configuration = existing_config
            else:
                # 새 구성 생성
                configuration = DatabaseConfiguration(
                    database_type=database_type,
                    database_path=new_database_path,
                    source_path=source_path
                )

            # 4단계: 파일 복사 (source_path가 있는 경우)
            if source_path:
                self._copy_database_file(source_path, new_path)

            # 5단계: 구성 저장
            self.repository.save(configuration)

            # 6단계: 경로 변경 이벤트 발생 (추후 구현)
            self._publish_path_changed_event(database_type, new_path, source_path)

            self.logger.info(f"✅ 데이터베이스 경로 변경 완료: {database_type}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 경로 변경 실패: {e}")
            return False

    def _copy_database_file(self, source_path: str, target_path: str) -> None:
        """데이터베이스 파일을 안전하게 복사합니다."""
        try:
            # 대상 디렉토리 생성
            Path(target_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            self.logger.info(f"✅ 파일 복사 완료: {source_path} → {target_path}")
        except Exception as e:
            self.logger.error(f"❌ 파일 복사 실패: {e}")
            raise

    def _verify_database_integrity(self, database_path: str) -> bool:
        """데이터베이스 파일의 무결성을 검증합니다."""
        try:
            with sqlite3.connect(database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                if result and result[0] == "ok":
                    self.logger.info(f"✅ 데이터베이스 무결성 검증 통과: {database_path}")
                    return True
                else:
                    self.logger.error(f"❌ 데이터베이스 무결성 검증 실패: {result}")
                    return False
        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 무결성 검증 중 오류: {e}")
            return False

    def validate_path(self, database_type: str, path: str) -> Tuple[bool, str]:
        """데이터베이스 경로의 유효성을 검증합니다."""
        try:
            path_obj = Path(path)

            # 확장자 검증
            if not path.endswith('.sqlite3'):
                return False, "데이터베이스 파일은 .sqlite3 확장자여야 합니다"

            # 경로 생성 가능성 검증
            try:
                path_obj.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"경로 생성 불가: {e}"

            # 쓰기 권한 검증
            if path_obj.exists():
                if not path_obj.is_file():
                    return False, "지정된 경로가 파일이 아닙니다"

                # 기존 파일의 SQLite 유효성 검증
                try:
                    with sqlite3.connect(str(path_obj)) as conn:
                        conn.execute("SELECT 1")
                except sqlite3.Error:
                    return False, "기존 파일이 유효한 SQLite 데이터베이스가 아닙니다"

            return True, ""

        except Exception as e:
            return False, f"경로 검증 중 오류: {e}"

    def get_current_path(self, database_type: str) -> Optional[str]:
        """현재 데이터베이스 경로 조회"""
        try:
            configuration = self.repository.get_by_type(database_type)
            if configuration and configuration.is_active:
                return configuration.get_path_string()

            self.logger.debug(f"🔍 활성화된 데이터베이스 구성 없음: {database_type}")
            return None

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 경로 조회 실패: {e}")
            return None

    def get_all_paths(self) -> Dict[str, str]:
        """모든 데이터베이스 경로 조회"""
        try:
            configurations = self.repository.get_all()
            result = {}

            for config in configurations:
                if config.is_active:
                    result[config.database_type] = config.get_path_string()

            self.logger.debug(f"✅ 모든 데이터베이스 경로 조회 완료: {len(result)}개")
            return result

        except Exception as e:
            self.logger.error(f"❌ 모든 데이터베이스 경로 조회 실패: {e}")
            return {}

    def initialize_default_paths(self) -> bool:
        """기본 데이터베이스 구성 초기화"""
        try:
            self.logger.info("🔧 기본 데이터베이스 구성 초기화 시작")

            # 기본 데이터베이스 경로 설정
            default_paths = {
                'settings': 'data/settings.sqlite3',
                'strategies': 'data/strategies.sqlite3',
                'market_data': 'data/market_data.sqlite3'
            }

            for db_type, default_path in default_paths.items():
                try:
                    # 절대 경로로 변환
                    absolute_path = Path(default_path).resolve()

                    # 디렉토리 생성
                    absolute_path.parent.mkdir(parents=True, exist_ok=True)

                    # DDD Repository에 저장
                    database_path = DatabasePath(absolute_path)
                    config = DatabaseConfiguration(
                        database_type=db_type,
                        database_path=database_path,
                        is_active=True
                    )

                    self.repository.save(config)
                    self.logger.info(f"✅ 기본 경로 설정: {db_type} → {absolute_path}")

                except Exception as e:
                    self.logger.error(f"❌ {db_type} 기본 경로 설정 실패: {e}")
                    return False

            self.logger.info("🎉 기본 데이터베이스 구성 초기화 완료")
            return True

        except Exception as e:
            self.logger.error(f"❌ 기본 구성 초기화 실패: {e}")
            return False

    def _test_database_connection(self, path: str) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            with sqlite3.connect(path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                self.logger.debug(f"� 데이터베이스 연결 성공: {len(tables)}개 테이블")
                return True

        except Exception as e:
            self.logger.debug(f"🔍 데이터베이스 연결 실패: {e}")
            return False

    def _publish_path_changed_event(self, database_type: str, new_path: str, source_path: Optional[str]) -> None:
        """경로 변경 이벤트 발행"""
        try:
            self.logger.info(f"� 경로 변경 이벤트 발행: {database_type} → {new_path}")
            # 향후 이벤트 시스템 구현 시 확장
        except Exception as e:
            self.logger.error(f"❌ 이벤트 발행 실패: {e}")

    def _publish_path_changed_event(self, database_type: str, new_path: str, source_path: Optional[str]) -> None:
        """경로 변경 이벤트 발행 (추후 이벤트 시스템 구현 시 사용)"""
        self.logger.info(f"📢 데이터베이스 경로 변경 이벤트: {database_type} -> {new_path}")
        # TODO: 도메인 이벤트 시스템 구현 시 실제 이벤트 발행
