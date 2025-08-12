"""
Database Profile Management Use Case

실거래/백테스팅 환경에서 데이터베이스 프로필의 안전한 관리를 담당하는 Use Case입니다.
비즈니스 규칙과 거래 상태를 고려하여 프로필 전환, 생성, 삭제를 수행합니다.
"""

from typing import Optional, List
import uuid
from pathlib import Path
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.dto.database_config_dto import (
    DatabaseProfileDto, CreateProfileRequestDto, UpdateProfileRequestDto,
    SwitchProfileRequestDto, DatabaseTypeEnum, TradingStateDto
)
from upbit_auto_trading.domain.database_configuration.repositories.idatabase_config_repository import (
    IDatabaseConfigRepository
)
from upbit_auto_trading.domain.database_configuration.entities.database_profile import DatabaseProfile
from upbit_auto_trading.domain.exceptions.domain_exceptions import DomainException

class DatabaseProfileManagementUseCase:
    """데이터베이스 프로필 관리 Use Case"""

    def __init__(self, repository: Optional[IDatabaseConfigRepository] = None):
        if repository is None:
            # 기본 Repository 생성 (향후 DI Container로 교체)
            from upbit_auto_trading.infrastructure.persistence.database_configuration_repository_impl import (
                FileSystemDatabaseConfigurationRepository
            )
            # 타입 체크 무시 (실제로는 interface 호환됨)
            repository = FileSystemDatabaseConfigurationRepository()  # type: ignore

        self._repository = repository  # type: ignore
        self._logger = create_component_logger("DatabaseProfileManagement")

    async def create_profile(self, request: CreateProfileRequestDto) -> DatabaseProfileDto:
        """새로운 데이터베이스 프로필을 생성합니다."""
        self._logger.info(f"🔧 프로필 생성 시작: {request.profile_name}")

        try:
            # 도메인 타입 변환
            domain_type = self._map_to_domain_type(request.database_type)

            # 프로필 생성
            profile_id = str(uuid.uuid4())
            profile = DatabaseProfile(
                profile_id=profile_id,
                name=request.profile_name,
                database_type=domain_type,
                file_path=Path(request.file_path),
                created_at=datetime.now(),
                metadata={'description': request.description} if request.description else None
            )

            # 저장
            await self._repository.save_profile(profile)

            # 활성화 요청 시 - 별도 처리 필요 (설정에서 관리)
            if request.should_activate:
                self._logger.info(f"활성화 요청됨 - 향후 구현 예정: {profile_id}")

            self._logger.info(f"✅ 프로필 생성 완료: {profile_id}")
            return DatabaseProfileDto.from_domain(profile)

        except DomainException as e:
            self._logger.error(f"❌ 프로필 생성 실패 (도메인 규칙 위반): {e}")
            raise
        except Exception as e:
            self._logger.error(f"❌ 프로필 생성 실패 (시스템 오류): {e}")
            raise

    async def update_profile(self, request: UpdateProfileRequestDto) -> DatabaseProfileDto:
        """기존 데이터베이스 프로필을 업데이트합니다."""
        self._logger.info(f"🔧 프로필 업데이트 시작: {request.profile_id}")

        try:
            # 기존 프로필 로드
            profile = await self._repository.load_profile(request.profile_id)
            if profile is None:
                raise ValueError(f"프로필을 찾을 수 없습니다: {request.profile_id}")

            # 업데이트 수행 (불변 객체이므로 새로운 인스턴스 생성)
            from dataclasses import replace

            updated_profile = replace(
                profile,
                name=request.profile_name if request.profile_name else profile.name,
                file_path=Path(request.file_path) if request.file_path else profile.file_path,
                metadata={'description': request.description} if request.description is not None else profile.metadata
            )

            # 저장
            await self._repository.save_profile(updated_profile)

            self._logger.info(f"✅ 프로필 업데이트 완료: {request.profile_id}")
            return DatabaseProfileDto.from_domain(updated_profile)

        except DomainException as e:
            self._logger.error(f"❌ 프로필 업데이트 실패 (도메인 규칙 위반): {e}")
            raise
        except Exception as e:
            self._logger.error(f"❌ 프로필 업데이트 실패 (시스템 오류): {e}")
            raise

    async def switch_database_profile(
        self,
        request: SwitchProfileRequestDto,
        trading_state: Optional[TradingStateDto] = None
    ) -> DatabaseProfileDto:
        """데이터베이스 프로필을 전환합니다. 거래 상태를 고려하여 안전하게 수행합니다."""
        self._logger.info(f"🔄 프로필 전환 시작: {request.database_type.value} -> {request.target_profile_id}")

        try:
            # 거래 상태 검증
            if trading_state and not request.force_switch:
                self._validate_switching_conditions(request.database_type, trading_state)

            # 대상 프로필 로드
            target_profile = await self._repository.load_profile(request.target_profile_id)
            if target_profile is None:
                raise ValueError(f"대상 프로필을 찾을 수 없습니다: {request.target_profile_id}")

            # 타입 일치 확인
            domain_type = self._map_to_domain_type(request.database_type)
            if target_profile.database_type != domain_type:
                raise ValueError(f"프로필 타입이 일치하지 않습니다: 요청={domain_type}, 프로필={target_profile.database_type}")

            # 프로필 활성화 (현재는 저장소에서 직접 처리, 향후 집합체에서 관리)
            activated_profile = target_profile.activate()
            await self._repository.save_profile(activated_profile)

            self._logger.info(f"✅ 프로필 전환 완료: {request.target_profile_id}")
            return DatabaseProfileDto.from_domain(activated_profile)

        except DomainException as e:
            self._logger.error(f"❌ 프로필 전환 실패 (도메인 규칙 위반): {e}")
            raise
        except Exception as e:
            self._logger.error(f"❌ 프로필 전환 실패 (시스템 오류): {e}")
            raise

    async def remove_profile(self, profile_id: str) -> bool:
        """데이터베이스 프로필을 제거합니다."""
        self._logger.info(f"🗑️ 프로필 제거 시작: {profile_id}")

        try:
            # 프로필 로드
            profile = await self._repository.load_profile(profile_id)
            if profile is None:
                raise ValueError(f"프로필을 찾을 수 없습니다: {profile_id}")

            # 활성 프로필인지 확인
            if profile.is_active:
                raise ValueError("활성 프로필은 제거할 수 없습니다")

            # 프로필 제거
            success = await self._repository.delete_profile(profile_id)

            if success:
                self._logger.info(f"✅ 프로필 제거 완료: {profile_id}")
            else:
                self._logger.warning(f"⚠️ 프로필 제거 실패: {profile_id}")

            return success

        except DomainException as e:
            self._logger.error(f"❌ 프로필 제거 실패 (도메인 규칙 위반): {e}")
            raise
        except Exception as e:
            self._logger.error(f"❌ 프로필 제거 실패 (시스템 오류): {e}")
            raise

    async def get_profile_by_id(self, profile_id: str) -> Optional[DatabaseProfileDto]:
        """ID로 프로필을 조회합니다."""
        try:
            profile = await self._repository.load_profile(profile_id)
            if profile is None:
                return None

            return DatabaseProfileDto.from_domain(profile)

        except Exception as e:
            self._logger.error(f"❌ 프로필 조회 실패: {e}")
            return None

    async def get_profiles_by_type(self, database_type: DatabaseTypeEnum) -> List[DatabaseProfileDto]:
        """타입별로 프로필 목록을 조회합니다."""
        try:
            domain_type = self._map_to_domain_type(database_type)
            profiles = await self._repository.load_profiles_by_type(domain_type)

            return [DatabaseProfileDto.from_domain(profile) for profile in profiles]

        except Exception as e:
            self._logger.error(f"❌ 프로필 목록 조회 실패: {e}")
            return []

    async def get_active_profile(self, database_type: DatabaseTypeEnum) -> Optional[DatabaseProfileDto]:
        """타입별 활성 프로필을 조회합니다."""
        try:
            active_profiles = await self._repository.get_active_profiles()
            domain_type = self._map_to_domain_type(database_type)

            active_profile = active_profiles.get(domain_type)
            if active_profile is None:
                return None

            return DatabaseProfileDto.from_domain(active_profile)

        except Exception as e:
            self._logger.error(f"❌ 활성 프로필 조회 실패: {e}")
            return None

    def _validate_switching_conditions(
        self,
        database_type: DatabaseTypeEnum,
        trading_state: TradingStateDto
    ) -> None:
        """프로필 전환 가능 조건을 검증합니다."""
        if not trading_state.can_switch_database:
            blocking_ops = ", ".join(trading_state.blocking_operations or [])
            raise ValueError(f"현재 프로필을 전환할 수 없습니다. 진행 중인 작업: {blocking_ops}")

        # 전략 DB 전환 시 추가 검증
        if database_type == DatabaseTypeEnum.STRATEGIES:
            if trading_state.is_trading_active:
                raise ValueError("실거래 진행 중에는 전략 데이터베이스를 전환할 수 없습니다")

            if trading_state.is_backtest_running:
                raise ValueError("백테스팅 진행 중에는 전략 데이터베이스를 전환할 수 없습니다")

        # 시장 데이터 DB 전환 시 추가 검증
        if database_type == DatabaseTypeEnum.MARKET_DATA:
            if trading_state.is_trading_active:
                self._logger.warning("⚠️ 실거래 중 시장 데이터 DB 전환은 신중해야 합니다")

    @staticmethod
    def _map_to_domain_type(dto_type: DatabaseTypeEnum) -> str:
        """DTO 타입을 도메인 타입으로 변환"""
        mapping = {
            DatabaseTypeEnum.SETTINGS: "settings",
            DatabaseTypeEnum.STRATEGIES: "strategies",
            DatabaseTypeEnum.MARKET_DATA: "market_data"
        }
        return mapping[dto_type]
