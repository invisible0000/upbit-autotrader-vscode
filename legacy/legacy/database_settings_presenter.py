"""
데이터베이스 설정 Presenter

MVP 패턴의 Presenter로서 View와 Application Layer 사이의 중개자 역할을 합니다.
UI 로직과 비즈니스 로직을 완전히 분리합니다.
"""

from typing import Dict
from pathlib import Path

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.use_cases.database_configuration.database_validation_use_case import (
    DatabaseValidationUseCase
)
from upbit_auto_trading.application.use_cases.database_configuration.database_status_query_use_case import (
    DatabaseStatusQueryUseCase
)
from upbit_auto_trading.application.use_cases.database_configuration.database_profile_management_use_case import (
    DatabaseProfileManagementUseCase
)
from upbit_auto_trading.application.dto.database_config_dto import (
    ValidationRequestDto, DatabaseTypeEnum, DatabaseConfigurationDto
)
from upbit_auto_trading.application.services.database_health_service import (
    DatabaseHealthService
)


class DatabaseSettingsPresenter:
    """
    데이터베이스 설정 Presenter

    MVP 패턴의 핵심으로서 View의 이벤트를 Use Case로 전달하고,
    Use Case의 결과를 View에 적합한 형태로 변환하여 전달합니다.
    """

    def __init__(
        self,
        view,  # Duck typing으로 변경 (메타클래스 충돌 회피)
        validation_use_case: DatabaseValidationUseCase,
        status_query_use_case: DatabaseStatusQueryUseCase,
        profile_management_use_case: DatabaseProfileManagementUseCase
    ):
        """Presenter 초기화"""
        self._view = view
        self._validation_use_case = validation_use_case
        self._status_query_use_case = status_query_use_case
        self._profile_management_use_case = profile_management_use_case
        self._logger = create_component_logger("DatabaseSettingsPresenter")

        # DatabaseHealthService 추가
        self._health_service = DatabaseHealthService()

        # View 이벤트 연결
        self._connect_view_events()

        self._logger.info("데이터베이스 설정 Presenter 초기화 완료")

    async def refresh_database_status(self) -> None:
        """데이터베이스 상태 새로고침"""
        self._logger.info("데이터베이스 상태 새로고침 요청")

        try:
            # DatabaseHealthService를 통해 상세 상태 조회
            detailed_status = self._health_service.get_detailed_status()

            # View에 상태 업데이트 전달
            if hasattr(self._view, 'update_database_status'):
                self._view.update_database_status(detailed_status)

            self._logger.info("데이터베이스 상태 새로고침 완료")

        except Exception as e:
            self._logger.error(f"데이터베이스 상태 새로고침 실패: {e}")

    def _connect_view_events(self) -> None:
        """View 이벤트와 Presenter 메서드 연결"""
        try:
            # 데이터 로드 이벤트 - 새로고침도 포함 (동기 버전)
            self._view.get_load_current_settings_signal().connect(self._handle_refresh_status_sync)

            # 검증 이벤트
            self._view.get_validate_database_signal().connect(self._handle_validate_database)

            # 설정 적용 이벤트
            self._view.get_apply_settings_signal().connect(self._handle_apply_settings)

            # 파일 찾아보기 이벤트
            self._view.get_browse_file_signal().connect(self._handle_browse_file)

            # 기본값 초기화 이벤트
            self._view.get_reset_to_defaults_signal().connect(self._handle_reset_to_defaults)

            self._logger.debug("View 이벤트 연결 완료")

        except Exception as e:
            self._logger.error(f"View 이벤트 연결 실패: {e}")

    def _handle_refresh_status_sync(self) -> None:
        """새로고침 요청 처리 - 동기 버전 (PyQt6 시그널용)"""
        self._logger.info("🔄 데이터베이스 상태 새로고침 요청 처리")

        try:
            # DatabaseHealthService를 통해 상세 상태 조회
            detailed_status = self._health_service.get_detailed_status()

            self._logger.debug(f"📊 상세 상태 조회 결과: {detailed_status}")

            # View에 상태 업데이트 전달
            if hasattr(self._view, 'update_database_status'):
                self._view.update_database_status(detailed_status)
                self._logger.info("✅ View 상태 업데이트 완료")
            else:
                self._logger.warning("⚠️ View에 update_database_status 메서드 없음")

            self._logger.info("✅ 데이터베이스 상태 새로고침 완료")

        except Exception as e:
            self._logger.error(f"❌ 데이터베이스 상태 새로고침 실패: {e}")

    async def _handle_refresh_status(self) -> None:
        """새로고침 요청 처리 - DatabaseHealthService 사용"""
        self._logger.info("데이터베이스 상태 새로고침 요청 처리")

        try:
            # DatabaseHealthService를 통해 상세 상태 조회
            detailed_status = self._health_service.get_detailed_status()

            # View에 상태 업데이트 전달
            if hasattr(self._view, 'update_database_status'):
                self._view.update_database_status(detailed_status)

            self._logger.info("데이터베이스 상태 새로고침 완료")

        except Exception as e:
            self._logger.error(f"데이터베이스 상태 새로고침 실패: {e}")

    async def _handle_load_current_settings(self) -> None:
        """현재 설정 로드 처리"""
        self._logger.info("현재 설정 로드 요청 처리")

        try:
            self._view.set_loading_state(True)

            # Use Case를 통해 현재 데이터베이스 프로필들 조회
            profiles = await self._status_query_use_case.get_all_database_profiles()

            # View에 프로필 표시
            self._view.display_database_profiles(profiles)

            # 각 데이터베이스 상태 조회 및 표시
            for profile in profiles:
                status = await self._status_query_use_case.get_database_status(profile.profile_id)
                if status:
                    self._view.display_database_status(status)

            self._logger.info("현재 설정 로드 완료")

        except Exception as e:
            self._logger.error(f"현재 설정 로드 실패: {e}")
            self._view.show_error_message(f"설정을 불러오는 중 오류가 발생했습니다: {str(e)}")

        finally:
            self._view.set_loading_state(False)

    async def _handle_validate_database(self, database_type: str) -> None:
        """데이터베이스 검증 처리"""
        self._logger.info(f"데이터베이스 검증 요청: {database_type}")

        try:
            self._view.show_validation_progress(True, f"{database_type} 데이터베이스 검증 중...")

            # 현재 View에서 파일 경로 가져오기
            current_paths = self._view.get_current_file_paths()
            file_path = current_paths.get(f"{database_type}_db")

            if not file_path:
                self._view.show_error_message(f"{database_type} 데이터베이스 경로가 설정되지 않았습니다.")
                return

            # 검증 요청 DTO 생성
            validation_request = ValidationRequestDto(
                database_type=self._string_to_database_type(database_type),
                file_path=file_path,
                check_integrity=True,
                check_schema=True,
                check_performance=False  # UI에서는 기본 검증만
            )

            # Use Case를 통해 검증 수행
            validation_result = await self._validation_use_case.validate_database_profile(validation_request)

            # 결과를 View에 표시
            if validation_result.is_valid:
                self._view.show_success_message(
                    f"{database_type} 데이터베이스 검증이 성공적으로 완료되었습니다."
                )
            else:
                error_msg = "\n".join(validation_result.validation_errors)
                self._view.show_error_message(
                    f"{database_type} 데이터베이스 검증 실패:\n{error_msg}"
                )

            # 경고가 있으면 표시
            if validation_result.warnings:
                warning_msg = "\n".join(validation_result.warnings)
                self._view.show_warning_message(
                    f"{database_type} 데이터베이스 검증 경고:\n{warning_msg}"
                )

            self._logger.info(f"데이터베이스 검증 완료: {database_type}")

        except Exception as e:
            self._logger.error(f"데이터베이스 검증 실패: {database_type} - {e}")
            self._view.show_error_message(f"데이터베이스 검증 중 오류가 발생했습니다: {str(e)}")

        finally:
            self._view.show_validation_progress(False)

    async def _handle_apply_settings(self, file_paths: Dict[str, str]) -> None:
        """설정 적용 처리"""
        self._logger.info("설정 적용 요청 처리")

        try:
            self._view.set_loading_state(True)

            # 각 데이터베이스 타입별로 프로필 업데이트
            for db_key, file_path in file_paths.items():
                if not file_path:
                    continue

                # db_key에서 데이터베이스 타입 추출 (예: "settings_db" -> "settings")
                db_type = db_key.replace("_db", "")

                # 경로 유효성 검사
                path_obj = Path(file_path)
                if not path_obj.exists():
                    self._view.show_error_message(f"{db_type} 데이터베이스 파일이 존재하지 않습니다: {file_path}")
                    continue

                # 프로필 업데이트
                config_dto = DatabaseConfigurationDto(
                    database_type=self._string_to_database_type(db_type),
                    file_path=file_path,
                    is_active=True
                )

                await self._profile_management_use_case.update_database_configuration(config_dto)

                self._logger.debug(f"데이터베이스 설정 업데이트: {db_type} -> {file_path}")

            self._view.show_success_message("데이터베이스 설정이 성공적으로 적용되었습니다.")

            # 설정 적용 후 현재 상태 다시 로드
            await self._handle_load_current_settings()

        except Exception as e:
            self._logger.error(f"설정 적용 실패: {e}")
            self._view.show_error_message(f"설정 적용 중 오류가 발생했습니다: {str(e)}")

        finally:
            self._view.set_loading_state(False)

    async def _handle_browse_file(self, database_type: str) -> None:
        """파일 찾아보기 처리"""
        self._logger.info(f"파일 찾아보기 요청: {database_type}")

        try:
            # PyQt6 파일 다이얼로그는 View에서 처리하고
            # 선택된 파일 경로만 Presenter로 전달받는 것이 좋습니다.
            # 여기서는 View에게 파일 다이얼로그 표시를 요청하는 로직이 들어갈 수 있습니다.
            pass

        except Exception as e:
            self._logger.error(f"파일 찾아보기 실패: {e}")
            self._view.show_error_message(f"파일 찾아보기 중 오류가 발생했습니다: {str(e)}")

    async def _handle_reset_to_defaults(self) -> None:
        """기본값으로 초기화 처리"""
        self._logger.info("기본값으로 초기화 요청 처리")

        try:
            # 기본 파일 경로들
            default_paths = {
                "settings": "data/settings.sqlite3",
                "strategies": "data/strategies.sqlite3",
                "market_data": "data/market_data.sqlite3"
            }

            # View에 기본 경로들 설정
            for db_type, default_path in default_paths.items():
                self._view.update_file_path(db_type, default_path)

            # 적용 버튼 활성화
            self._view.enable_apply_button(True)

            self._view.show_success_message("기본값으로 초기화되었습니다.")

        except Exception as e:
            self._logger.error(f"기본값 초기화 실패: {e}")
            self._view.show_error_message(f"기본값 초기화 중 오류가 발생했습니다: {str(e)}")

    def _string_to_database_type(self, db_type_str: str) -> DatabaseTypeEnum:
        """문자열을 DatabaseTypeEnum으로 변환"""
        type_mapping = {
            "settings": DatabaseTypeEnum.SETTINGS,
            "strategies": DatabaseTypeEnum.STRATEGIES,
            "market_data": DatabaseTypeEnum.MARKET_DATA
        }

        return type_mapping.get(db_type_str.lower(), DatabaseTypeEnum.SETTINGS)

    async def initialize_view(self) -> None:
        """View 초기화 (Presenter 생성 후 호출)"""
        self._logger.info("View 초기화 시작")

        try:
            await self._handle_load_current_settings()
            self._logger.info("View 초기화 완료")

        except Exception as e:
            self._logger.error(f"View 초기화 실패: {e}")
            self._view.show_error_message(f"화면 초기화 중 오류가 발생했습니다: {str(e)}")

    def cleanup(self) -> None:
        """Presenter 정리"""
        self._logger.info("Presenter 정리")
        # 필요시 리소스 정리 코드 추가
