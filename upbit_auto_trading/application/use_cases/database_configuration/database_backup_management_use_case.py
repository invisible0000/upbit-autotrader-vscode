"""
Database Backup Management Use Case

데이터베이스 백업과 복원을 관리하는 Use Case입니다.
실거래 중에도 안전하게 백업을 생성하고 복원할 수 있는 기능을 제공합니다.
"""

from typing import Optional, List
import uuid
from pathlib import Path
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.dto.database_config_dto import (
    BackupRecordDto, CreateBackupRequestDto, RestoreBackupRequestDto,
    DatabaseValidationResultDto, TradingStateDto
)
from upbit_auto_trading.domain.database_configuration.repositories.idatabase_config_repository import (
    IDatabaseConfigRepository
)
from upbit_auto_trading.domain.database_configuration.entities.backup_record import (
    BackupRecord, BackupType, BackupStatus
)
from upbit_auto_trading.domain.exceptions.domain_exceptions import DomainException


class DatabaseBackupManagementUseCase:
    """데이터베이스 백업 관리 Use Case"""

    def __init__(self, repository: IDatabaseConfigRepository):
        self._repository = repository
        self._logger = create_component_logger("DatabaseBackupManagement")

    async def create_backup(
        self,
        request: CreateBackupRequestDto,
        trading_state: Optional[TradingStateDto] = None
    ) -> BackupRecordDto:
        """새로운 백업을 생성합니다."""
        self._logger.info(f"💾 백업 생성 시작: {request.profile_id}")

        try:
            # 거래 상태 검증
            if trading_state:
                self._validate_backup_conditions(trading_state)

            # 원본 프로필 확인
            source_profile = await self._repository.load_profile(request.profile_id)
            if source_profile is None:
                raise ValueError(f"원본 프로필을 찾을 수 없습니다: {request.profile_id}")

            # 백업 경로 결정
            backup_path = self._determine_backup_path(
                source_profile,
                request.backup_path
            )

            # 백업 수행
            backup_record = await self._perform_backup(
                source_profile=source_profile,
                backup_path=backup_path,
                description=request.description,
                compression_enabled=request.compression_enabled
            )

            # 백업 기록 저장
            await self._repository.save_backup_record(backup_record)

            self._logger.info(f"✅ 백업 생성 완료: {backup_record.backup_id}")
            return BackupRecordDto.from_domain(backup_record)

        except DomainException as e:
            self._logger.error(f"❌ 백업 생성 실패 (도메인 규칙 위반): {e}")
            raise
        except Exception as e:
            self._logger.error(f"❌ 백업 생성 실패 (시스템 오류): {e}")
            raise

    async def restore_backup(
        self,
        request: RestoreBackupRequestDto,
        trading_state: Optional[TradingStateDto] = None
    ) -> bool:
        """백업에서 데이터베이스를 복원합니다."""
        self._logger.info(f"🔄 백업 복원 시작: {request.backup_id}")

        try:
            # 거래 상태 검증
            if trading_state:
                self._validate_restore_conditions(trading_state)

            # 백업 기록 확인
            backup_record = await self._repository.load_backup_record(request.backup_id)
            if backup_record is None:
                raise ValueError(f"백업 기록을 찾을 수 없습니다: {request.backup_id}")

            # 대상 프로필 결정
            target_profile_id = request.target_profile_id or backup_record.source_profile_id
            target_profile = await self._repository.load_profile(target_profile_id)
            if target_profile is None:
                raise ValueError(f"대상 프로필을 찾을 수 없습니다: {target_profile_id}")

            # 복원 전 백업 생성 (옵션)
            if request.create_backup_before_restore:
                await self._create_pre_restore_backup(target_profile)

            # 복원 수행
            success = await self._perform_restore(backup_record, target_profile)

            if success:
                self._logger.info(f"✅ 백업 복원 완료: {request.backup_id}")
            else:
                self._logger.error(f"❌ 백업 복원 실패: {request.backup_id}")

            return success

        except DomainException as e:
            self._logger.error(f"❌ 백업 복원 실패 (도메인 규칙 위반): {e}")
            raise
        except Exception as e:
            self._logger.error(f"❌ 백업 복원 실패 (시스템 오류): {e}")
            raise

    async def get_backup_records_by_profile(self, profile_id: str) -> List[BackupRecordDto]:
        """프로필별 백업 기록 목록을 조회합니다."""
        try:
            backup_records = await self._repository.load_backup_records_by_profile(profile_id)
            return [BackupRecordDto.from_domain(record) for record in backup_records]

        except Exception as e:
            self._logger.error(f"❌ 백업 기록 조회 실패: {e}")
            return []

    async def get_backup_record(self, backup_id: str) -> Optional[BackupRecordDto]:
        """백업 기록을 조회합니다."""
        try:
            backup_record = await self._repository.load_backup_record(backup_id)
            if backup_record is None:
                return None

            return BackupRecordDto.from_domain(backup_record)

        except Exception as e:
            self._logger.error(f"❌ 백업 기록 조회 실패: {e}")
            return None

    async def delete_backup(self, backup_id: str) -> bool:
        """백업을 삭제합니다."""
        self._logger.info(f"🗑️ 백업 삭제 시작: {backup_id}")

        try:
            # 백업 기록 확인
            backup_record = await self._repository.load_backup_record(backup_id)
            if backup_record is None:
                raise ValueError(f"백업 기록을 찾을 수 없습니다: {backup_id}")

            # 물리적 파일 삭제
            backup_path = backup_record.backup_file_path
            if backup_path.exists():
                backup_path.unlink()
                self._logger.debug(f"백업 파일 삭제됨: {backup_path}")

            # 기록 삭제
            success = await self._repository.delete_backup_record(backup_id)

            if success:
                self._logger.info(f"✅ 백업 삭제 완료: {backup_id}")
            else:
                self._logger.warning(f"⚠️ 백업 기록 삭제 실패: {backup_id}")

            return success

        except Exception as e:
            self._logger.error(f"❌ 백업 삭제 실패: {e}")
            raise

    async def cleanup_old_backups(self, cutoff_date: datetime) -> int:
        """오래된 백업들을 정리합니다."""
        self._logger.info(f"🧹 백업 정리 시작: {cutoff_date} 이전")

        try:
            deleted_count = await self._repository.cleanup_old_backup_records(cutoff_date)
            self._logger.info(f"✅ 백업 정리 완료: {deleted_count}개 삭제")
            return deleted_count

        except Exception as e:
            self._logger.error(f"❌ 백업 정리 실패: {e}")
            return 0

    async def validate_backup(self, backup_id: str) -> DatabaseValidationResultDto:
        """백업 파일의 무결성을 검증합니다."""
        self._logger.info(f"🔍 백업 검증 시작: {backup_id}")

        try:
            backup_record = await self._repository.load_backup_record(backup_id)
            if backup_record is None:
                return DatabaseValidationResultDto(
                    profile_id=backup_id,
                    is_valid=False,
                    validation_errors=["백업 기록을 찾을 수 없습니다"],
                    warnings=[]
                )

            # 백업 파일 존재 확인
            backup_path = backup_record.backup_file_path
            if not backup_path.exists():
                return DatabaseValidationResultDto(
                    profile_id=backup_id,
                    is_valid=False,
                    validation_errors=["백업 파일이 존재하지 않습니다"],
                    warnings=[]
                )

            # 파일 크기 검증
            actual_size = backup_path.stat().st_size
            if backup_record.file_size_bytes and actual_size != backup_record.file_size_bytes:
                return DatabaseValidationResultDto(
                    profile_id=backup_id,
                    is_valid=False,
                    validation_errors=[f"파일 크기 불일치: 예상={backup_record.file_size_bytes}, 실제={actual_size}"],
                    warnings=[]
                )

            # TODO: 압축 파일 내용 검증, 데이터베이스 스키마 검증 등

            return DatabaseValidationResultDto(
                profile_id=backup_id,
                is_valid=True,
                validation_errors=[],
                warnings=[]
            )

        except Exception as e:
            self._logger.error(f"❌ 백업 검증 실패: {e}")
            return DatabaseValidationResultDto(
                profile_id=backup_id,
                is_valid=False,
                validation_errors=[f"검증 중 오류 발생: {e}"],
                warnings=[]
            )

    def _determine_backup_path(self, source_profile, custom_path: Optional[str]) -> Path:
        """백업 파일 경로를 결정합니다."""
        if custom_path:
            return Path(custom_path)

        # 자동 경로 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{source_profile.name}_backup_{timestamp}.sqlite3"

        # 백업 디렉토리 (프로젝트 루트/backups)
        backup_dir = Path("backups") / source_profile.database_type
        backup_dir.mkdir(parents=True, exist_ok=True)

        return backup_dir / backup_filename

    async def _perform_backup(
        self,
        source_profile,
        backup_path: Path,
        description: Optional[str],
        compression_enabled: bool
    ) -> BackupRecord:
        """실제 백업 수행"""
        import shutil

        self._logger.debug(f"백업 수행: {source_profile.file_path} -> {backup_path}")

        # 원본 파일 복사
        shutil.copy2(source_profile.file_path, backup_path)

        # 압축 처리
        compression_type = "none"
        if compression_enabled:
            # TODO: 압축 구현
            self._logger.debug("압축 옵션이 활성화되었지만 아직 구현되지 않음")

        # 백업 기록 생성
        backup_record = BackupRecord(
            backup_id=str(uuid.uuid4()),
            source_profile_id=source_profile.profile_id,
            source_database_type=source_profile.database_type,
            backup_file_path=backup_path,
            backup_type=BackupType.MANUAL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            completed_at=datetime.now(),
            file_size_bytes=backup_path.stat().st_size,
            metadata={
                'description': description,
                'compression': compression_type
            } if description else {'compression': compression_type}
        )

        return backup_record

    async def _perform_restore(self, backup_record: BackupRecord, target_profile) -> bool:
        """실제 복원 수행"""
        import shutil

        try:
            self._logger.debug(f"복원 수행: {backup_record.backup_file_path} -> {target_profile.file_path}")

            # 백업에서 대상으로 복사
            shutil.copy2(backup_record.backup_file_path, target_profile.file_path)

            return True

        except Exception as e:
            self._logger.error(f"복원 실행 중 오류: {e}")
            return False

    async def _create_pre_restore_backup(self, target_profile) -> None:
        """복원 전 백업 생성"""
        self._logger.info(f"복원 전 백업 생성: {target_profile.name}")

        pre_restore_request = CreateBackupRequestDto(
            profile_id=target_profile.profile_id,
            description=f"복원 전 자동 백업 - {datetime.now().isoformat()}"
        )

        await self.create_backup(pre_restore_request)

    def _validate_backup_conditions(self, trading_state: TradingStateDto) -> None:
        """백업 생성 가능 조건 검증"""
        # 일반적으로 백업은 WAL 모드에서 안전하므로 제한이 적음
        if trading_state.blocking_operations:
            blocking_ops = ", ".join(trading_state.blocking_operations)
            self._logger.warning(f"⚠️ 진행 중인 작업이 있지만 백업 계속 진행: {blocking_ops}")

    def _validate_restore_conditions(self, trading_state: TradingStateDto) -> None:
        """백업 복원 가능 조건 검증"""
        if trading_state.is_trading_active:
            raise ValueError("실거래 진행 중에는 데이터베이스를 복원할 수 없습니다")

        if trading_state.is_backtest_running:
            raise ValueError("백테스팅 진행 중에는 데이터베이스를 복원할 수 없습니다")

        if not trading_state.can_switch_database:
            blocking_ops = ", ".join(trading_state.blocking_operations or [])
            raise ValueError(f"현재 데이터베이스를 복원할 수 없습니다. 진행 중인 작업: {blocking_ops}")
