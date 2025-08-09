"""
Database Configuration MVP Presenter

Model-View-Presenter 패턴을 사용하여 데이터베이스 설정 UI와 Application Layer를 연결합니다.

Design Principles:
- MVP Pattern: View는 UI만, Presenter가 비즈니스 로직 조정
- Dependency Injection: Use Cases를 주입받아 느슨한 결합
- Event-Driven: UI 이벤트를 Application Layer로 변환
- Error Handling: 모든 예외를 적절한 UI 메시지로 변환

Responsibilities:
- UI 이벤트를 Use Case 호출로 변환
- Application Layer 결과를 UI 형태로 변환
- 에러 처리 및 사용자 피드백 관리
- 데이터 검증 및 상태 관리
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from upbit_auto_trading.infrastructure.logging import create_component_logger

# Application Layer Service
from upbit_auto_trading.application.services.database_configuration_app_service import (
    DatabaseConfigurationAppService
)

# DTOs
from upbit_auto_trading.application.dto.database_config_dto import (
    DatabaseProfileDto, DatabaseConfigDto, BackupRequestDto, ValidationRequestDto,
    DatabaseStatusDto
)

logger = create_component_logger("DatabaseConfigPresenter")


class DatabaseConfigPresenter:
    """
    데이터베이스 설정 MVP 패턴 프레젠터

    UI 계층과 Application 계층 사이의 중재자 역할을 수행합니다.
    """

    def __init__(self,
                 app_service: DatabaseConfigurationAppService,
                 view: Optional[Any] = None):
        """
        프레젠터 초기화

        Args:
            app_service: 데이터베이스 설정 애플리케이션 서비스
            view: UI 뷰 (나중에 설정 가능)
        """
        self._logger = logger
        self._app_service = app_service
        self._view = view

        # 현재 상태 캐시
        self._current_config: Optional[DatabaseConfigDto] = None
        self._current_status: Dict[str, DatabaseStatusDto] = {}

        self._logger.info("🎭 DatabaseConfigPresenter 초기화됨")

    def set_view(self, view: Any) -> None:
        """
        뷰 설정 (늦은 바인딩)

        Args:
            view: UI 뷰 객체
        """
        self._view = view
        self._logger.debug("📱 View 연결됨")

    # === 설정 관리 ===

    async def load_configuration(self) -> bool:
        """
        현재 데이터베이스 설정 로드

        Returns:
            로드 성공 여부
        """
        try:
            self._logger.info("📂 데이터베이스 설정 로드 시작")

            self._current_config = await self._app_service.get_current_configuration()

            if self._current_config and self._view:
                self._view.update_configuration_display(self._current_config)

            self._logger.info("✅ 데이터베이스 설정 로드 완료")
            return True

        except Exception as e:
            self._logger.error(f"❌ 설정 로드 실패: {e}")
            self._notify_error("설정 로드 실패", f"데이터베이스 설정을 불러올 수 없습니다: {str(e)}")
            return False

    async def save_configuration(self, config_data: Dict[str, Any]) -> bool:
        """
        데이터베이스 설정 저장

        Args:
            config_data: 저장할 설정 데이터

        Returns:
            저장 성공 여부
        """
        try:
            self._logger.info("💾 데이터베이스 설정 저장 시작")

            # DTO 변환
            config_dto = self._convert_to_config_dto(config_data)

            # Application Layer 호출
            success = await self._app_service.update_configuration(config_dto)

            if success:
                self._current_config = config_dto
                self._notify_success("설정 저장 완료", "데이터베이스 설정이 성공적으로 저장되었습니다.")
                return True
            else:
                raise Exception("설정 저장 실패")

        except Exception as e:
            self._logger.error(f"❌ 설정 저장 실패: {e}")
            self._notify_error("설정 저장 실패", f"데이터베이스 설정을 저장할 수 없습니다: {str(e)}")
            return False

    # === 프로필 관리 ===

    async def switch_database_profile(self, database_type: str, new_path: str) -> bool:
        """
        데이터베이스 프로필 전환

        Args:
            database_type: 데이터베이스 타입 ('settings', 'strategies', 'market_data')
            new_path: 새로운 데이터베이스 파일 경로

        Returns:
            전환 성공 여부
        """
        try:
            self._logger.info(f"🔄 DB 프로필 전환 시작: {database_type} -> {new_path}")

            # 진행상황 표시
            if self._view:
                self._view.show_progress("데이터베이스 전환 중...")

            # Application Layer 호출
            success = await self._app_service.switch_database_profile(database_type, Path(new_path))

            if success:
                # 설정 재로드
                await self.load_configuration()
                self._notify_success("프로필 전환 완료", f"{database_type} 데이터베이스가 성공적으로 전환되었습니다.")
                return True
            else:
                raise Exception("프로필 전환 실패")

        except Exception as e:
            self._logger.error(f"❌ DB 프로필 전환 실패: {e}")
            self._notify_error("프로필 전환 실패", f"데이터베이스 프로필을 전환할 수 없습니다: {str(e)}")
            return False
        finally:
            if self._view:
                self._view.hide_progress()

    async def create_database_profile(self, profile_data: Dict[str, Any]) -> bool:
        """
        새 데이터베이스 프로필 생성

        Args:
            profile_data: 프로필 데이터

        Returns:
            생성 성공 여부
        """
        try:
            self._logger.info("➕ 새 DB 프로필 생성 시작")

            # DTO 변환
            profile_dto = self._convert_to_profile_dto(profile_data)

            # Application Layer 호출
            success = await self._app_service.create_database_profile(profile_dto)

            if success:
                await self.load_configuration()
                self._notify_success("프로필 생성 완료", "새 데이터베이스 프로필이 생성되었습니다.")
                return True
            else:
                raise Exception("프로필 생성 실패")

        except Exception as e:
            self._logger.error(f"❌ DB 프로필 생성 실패: {e}")
            self._notify_error("프로필 생성 실패", f"데이터베이스 프로필을 생성할 수 없습니다: {str(e)}")
            return False

    # === 백업 관리 ===

    async def create_backup(self, database_type: str, backup_type: str = "manual") -> bool:
        """
        데이터베이스 백업 생성

        Args:
            database_type: 백업할 데이터베이스 타입
            backup_type: 백업 타입 ('manual', 'scheduled', 'automatic')

        Returns:
            백업 성공 여부
        """
        try:
            self._logger.info(f"💾 DB 백업 생성 시작: {database_type}")

            if self._view:
                self._view.show_progress("백업 생성 중...")

            # DTO 생성
            backup_request = BackupRequestDto(
                database_type=database_type,
                backup_type=backup_type,
                description=f"{database_type} 수동 백업"
            )

            # Application Layer 호출
            backup_result = await self._app_service.create_backup(backup_request)

            if backup_result:
                self._notify_success("백업 완료", f"{database_type} 데이터베이스 백업이 생성되었습니다.")
                return True
            else:
                raise Exception("백업 생성 실패")

        except Exception as e:
            self._logger.error(f"❌ DB 백업 실패: {e}")
            self._notify_error("백업 실패", f"데이터베이스 백업을 생성할 수 없습니다: {str(e)}")
            return False
        finally:
            if self._view:
                self._view.hide_progress()

    async def restore_backup(self, backup_id: str) -> bool:
        """
        백업에서 데이터베이스 복원

        Args:
            backup_id: 복원할 백업 ID

        Returns:
            복원 성공 여부
        """
        try:
            self._logger.info(f"🔄 DB 백업 복원 시작: {backup_id}")

            if self._view:
                self._view.show_progress("백업 복원 중...")

            # Application Layer 호출
            success = await self._app_service.restore_backup(backup_id)

            if success:
                await self.load_configuration()
                self._notify_success("복원 완료", "데이터베이스가 백업에서 성공적으로 복원되었습니다.")
                return True
            else:
                raise Exception("백업 복원 실패")

        except Exception as e:
            self._logger.error(f"❌ DB 백업 복원 실패: {e}")
            self._notify_error("복원 실패", f"백업에서 데이터베이스를 복원할 수 없습니다: {str(e)}")
            return False
        finally:
            if self._view:
                self._view.hide_progress()

    async def list_backups(self, database_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        백업 목록 조회

        Args:
            database_type: 특정 데이터베이스 타입 (None이면 전체)

        Returns:
            백업 목록
        """
        try:
            backups = await self._app_service.list_backups(database_type)
            return [backup.to_dict() for backup in backups] if backups else []

        except Exception as e:
            self._logger.error(f"❌ 백업 목록 조회 실패: {e}")
            self._notify_error("백업 목록 조회 실패", f"백업 목록을 불러올 수 없습니다: {str(e)}")
            return []

    # === 검증 및 상태 ===

    async def validate_database(self, database_type: str) -> bool:
        """
        데이터베이스 무결성 검증

        Args:
            database_type: 검증할 데이터베이스 타입

        Returns:
            검증 성공 여부
        """
        try:
            self._logger.info(f"🔍 DB 검증 시작: {database_type}")

            if self._view:
                self._view.show_progress("데이터베이스 검증 중...")

            # DTO 생성
            validation_request = ValidationRequestDto(
                database_type=database_type,
                check_integrity=True,
                check_accessibility=True,
                check_schema=True
            )

            # Application Layer 호출
            validation_result = await self._app_service.validate_database(validation_request)

            if validation_result and validation_result.is_valid:
                self._notify_success("검증 완료", f"{database_type} 데이터베이스가 정상입니다.")
                return True
            else:
                error_msg = validation_result.error_message if validation_result else "검증 실패"
                self._notify_warning("검증 문제", f"{database_type} 데이터베이스에 문제가 있습니다: {error_msg}")
                return False

        except Exception as e:
            self._logger.error(f"❌ DB 검증 실패: {e}")
            self._notify_error("검증 실패", f"데이터베이스를 검증할 수 없습니다: {str(e)}")
            return False
        finally:
            if self._view:
                self._view.hide_progress()

    async def refresh_status(self) -> Dict[str, Any]:
        """
        데이터베이스 상태 새로고침

        Returns:
            상태 정보
        """
        try:
            self._logger.debug("🔄 DB 상태 새로고침")

            # Application Layer 호출
            status_data = await self._app_service.get_database_status()

            if status_data and self._view:
                self._view.update_status_display(status_data)

            return status_data.to_dict() if status_data else {}

        except Exception as e:
            self._logger.error(f"❌ DB 상태 새로고침 실패: {e}")
            return {}

    # === Private Helper Methods ===

    def _convert_to_config_dto(self, config_data: Dict[str, Any]) -> DatabaseConfigDto:
        """설정 데이터를 DTO로 변환"""
        # 구현 세부사항...
        return DatabaseConfigDto(
            profiles={},  # 실제 변환 로직 구현 필요
            active_profile_ids={},
            created_at=datetime.now(),
            last_updated=datetime.now()
        )

    def _convert_to_profile_dto(self, profile_data: Dict[str, Any]) -> DatabaseProfileDto:
        """프로필 데이터를 DTO로 변환"""
        # 구현 세부사항...
        return DatabaseProfileDto(
            profile_id=profile_data.get('id', ''),
            name=profile_data.get('name', ''),
            database_type=profile_data.get('type', ''),
            file_path=profile_data.get('path', ''),
            is_active=profile_data.get('active', False),
            metadata=profile_data.get('metadata', {})
        )

    def _notify_success(self, title: str, message: str) -> None:
        """성공 메시지 표시"""
        self._logger.info(f"✅ {title}: {message}")
        if self._view:
            self._view.show_success_message(title, message)

    def _notify_error(self, title: str, message: str) -> None:
        """에러 메시지 표시"""
        self._logger.error(f"❌ {title}: {message}")
        if self._view:
            self._view.show_error_message(title, message)

    def _notify_warning(self, title: str, message: str) -> None:
        """경고 메시지 표시"""
        self._logger.warning(f"⚠️ {title}: {message}")
        if self._view:
            self._view.show_warning_message(title, message)

    def _notify_info(self, title: str, message: str) -> None:
        """정보 메시지 표시"""
        self._logger.info(f"ℹ️ {title}: {message}")
        if self._view:
            self._view.show_info_message(title, message)
