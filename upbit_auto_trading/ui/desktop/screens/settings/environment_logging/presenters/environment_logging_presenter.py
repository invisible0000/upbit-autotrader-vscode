"""
Environment Logging Presenter
============================

환경&로깅 통합 탭의 MVP 패턴 Presenter
View와 Application Layer 사이의 중재자 역할

Features:
- 프로파일 전환 요청 처리 (ConfigProfileService 연동)
- 로깅 설정 적용 처리
- 환경-로깅 동기화 관리
- 실시간 프로파일 스위칭 지원
"""

from typing import Optional
from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.services.config_profile_service import ConfigProfileService


class EnvironmentLoggingPresenter:
    """
    환경&로깅 통합 Presenter

    MVP 패턴에 따라 View의 이벤트를 받아서
    Application Layer Service를 호출하고
    결과를 다시 View에 반영
    """

    def __init__(self, view=None):
        """Presenter 초기화

        Args:
            view: EnvironmentLoggingWidget 인스턴스
        """
        self._view = view
        self._logger = create_component_logger("EnvironmentLoggingPresenter")
        self._logger.info("🎭 환경&로깅 Presenter 초기화 시작")

        # ConfigProfileService 초기화
        self._profile_service = ConfigProfileService()

        self._connect_view_signals()
        self._logger.info("✅ 환경&로깅 Presenter 초기화 완료")

    def _connect_view_signals(self):
        """View 시그널 연결"""
        if self._view:
            # 환경 전환 요청 (기존 호환성)
            self._view.environment_switch_requested.connect(
                self._handle_environment_switch_request
            )

            # 로깅 설정 변경
            self._view.logging_config_changed.connect(
                self._handle_logging_config_change
            )

            # 환경-로깅 동기화 요청
            self._view.environment_logging_sync_requested.connect(
                self._handle_environment_logging_sync
            )

            # 프로파일 스위칭 (신규)
            if hasattr(self._view, 'profile_switched'):
                self._view.profile_switched.connect(
                    self._handle_profile_switched
                )

            self._logger.info("🔗 View 시그널 연결 완료")

    def _handle_environment_switch_request(self, environment_name: str):
        """환경 전환 요청 처리 (기존 호환성 유지)"""
        self._logger.info(f"🔄 환경 전환 요청 처리 (호환성 모드): {environment_name}")

        try:
            # 환경 이름을 프로파일명으로 변환
            profile_name = environment_name.lower()

            # ConfigProfileService를 통한 프로파일 전환
            result = self._profile_service.switch_profile(profile_name)

            if result.success:
                # View에 성공 알림
                if self._view:
                    self._view.show_environment_switch_success(environment_name)
                    self._view.set_current_environment(environment_name)

                self._logger.info(f"✅ 환경 전환 완료: {environment_name}")
            else:
                error_msg = '\n'.join(result.errors) if result.errors else "알 수 없는 오류"
                if self._view:
                    self._view.show_environment_switch_error(error_msg)
                self._logger.error(f"❌ 환경 전환 실패: {error_msg}")

        except Exception as e:
            self._logger.error(f"❌ 환경 전환 실패: {e}")
            if self._view:
                self._view.show_environment_switch_error(str(e))

    def _handle_profile_switched(self, profile_name: str):
        """프로파일 스위칭 완료 처리"""
        self._logger.info(f"🎯 프로파일 스위칭 완료 처리: {profile_name}")

        try:
            # UI 상태 동기화 (로깅 설정 등)
            if self._view and hasattr(self._view, 'logging_section'):
                ui_state = self._profile_service.get_ui_state()
                self._view.logging_section.update_from_ui_state(ui_state)

            self._logger.info(f"✅ 프로파일 스위칭 후 UI 동기화 완료: {profile_name}")

        except Exception as e:
            self._logger.error(f"❌ 프로파일 스위칭 후 UI 동기화 실패: {e}")

    def _handle_logging_config_change(self, key: str, value: str):
        """로깅 설정 변경 처리"""
        self._logger.debug(f"� 로깅 설정 변경 처리: {key} = {value}")

        try:
            # 환경변수 직접 설정
            import os
            if value:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

            self._logger.debug(f"✅ 로깅 설정 적용: {key}")

        except Exception as e:
            self._logger.error(f"❌ 로깅 설정 적용 실패: {e}")

    def _handle_environment_logging_sync(self, environment_name: str):
        """환경-로깅 동기화 처리"""
        self._logger.info(f"🔄 환경-로깅 동기화: {environment_name}")

        try:
            # 환경별 기본 로깅 설정 적용
            profile_name = environment_name.lower()
            result = self._profile_service.switch_profile(profile_name)

            if result.success and self._view:
                # UI 업데이트
                ui_state = self._profile_service.get_ui_state()
                if hasattr(self._view, 'update_logging_config'):
                    self._view.update_logging_config(result.env_vars_applied)

            self._logger.info(f"✅ 환경-로깅 동기화 완료: {environment_name}")

        except Exception as e:
            self._logger.error(f"❌ 환경-로깅 동기화 실패: {e}")

    def set_view(self, view):
        """View 설정 (지연 주입)"""
        self._view = view
        self._connect_view_signals()
        self._logger.info("🔗 View 지연 주입 완료")

    def get_current_environment(self) -> str:
        """현재 환경 조회"""
        if self._view:
            return self._view.get_current_environment()
        return "development"

    def get_current_profile(self) -> Optional[str]:
        """현재 프로파일 조회"""
        return self._profile_service.get_current_profile()

    def refresh_view(self):
        """View 새로고침"""
        self._logger.debug("🔄 View 새로고침 요청")
        try:
            if self._view and hasattr(self._view, 'refresh_profiles'):
                self._view.refresh_profiles()
            self._logger.debug("✅ View 새로고침 완료")
        except Exception as e:
            self._logger.error(f"❌ View 새로고침 실패: {e}")

    def get_available_profiles(self) -> list:
        """사용 가능한 프로파일 목록 조회"""
        try:
            return self._profile_service.get_available_profiles()
        except Exception as e:
            self._logger.error(f"❌ 프로파일 목록 조회 실패: {e}")
            return []
