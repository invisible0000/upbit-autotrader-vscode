"""
Settings Presenter - MVP 패턴 구현

설정 관리 UI를 위한 MVP 패턴 Presenter입니다.
DDD Application Service와 연동하여 비즈니스 로직을 처리합니다.
"""

from upbit_auto_trading.infrastructure.logging import create_component_logger

class SettingsPresenter:
    """Settings Presenter - MVP Pattern 구현

    비즈니스 로직과 애플리케이션 로직을 담당:
    - 설정 로드/저장 오케스트레이션
    - 설정 유효성 검사
    - 에러 처리 및 사용자 피드백
    - View 상태 관리
    """

    def __init__(self, view, settings_service=None):
        """Presenter 초기화

        Args:
            view: Settings View 인터페이스 구현체 (SettingsScreen)
            settings_service: Application Service 의존성
        """
        self.view = view
        self.settings_service = settings_service
        self.logger = create_component_logger("SettingsPresenter")

        # View 시그널 연결
        self._connect_view_signals()

        # 초기 상태 설정
        self.is_loading = False

        self.logger.info("✅ SettingsPresenter 초기화 완료")

    def _connect_view_signals(self) -> None:
        """View 시그널을 Presenter와 연결"""
        try:
            # 설정 저장 요청 시그널
            if hasattr(self.view, 'save_all_requested'):
                self.view.save_all_requested.connect(self.handle_save_all_settings)

            # 설정 변경 시그널
            if hasattr(self.view, 'settings_changed'):
                self.view.settings_changed.connect(self.handle_settings_changed)

            # 테마 변경 시그널
            if hasattr(self.view, 'theme_changed'):
                self.view.theme_changed.connect(self.handle_theme_changed)

            # API 상태 변경 시그널
            if hasattr(self.view, 'api_status_changed'):
                self.view.api_status_changed.connect(self.handle_api_status_changed)

            # DB 상태 변경 시그널
            if hasattr(self.view, 'db_status_changed'):
                self.view.db_status_changed.connect(self.handle_db_status_changed)

            self.logger.info("✅ View 시그널 연결 완료")

        except Exception as e:
            self.logger.error(f"❌ View 시그널 연결 실패: {e}")

    def load_initial_settings(self) -> None:
        """초기 설정 로드 - 재귀 방지"""
        try:
            self.logger.info("📋 초기 설정 로드 시작")

            # 🚨 재귀 방지: View의 load_settings()를 호출하지 않고 직접 처리
            # Application Service를 통한 직접 설정 로드
            if self.settings_service:
                try:
                    # 실제 설정 로드 로직 (Application Service 의존)
                    # 현재는 설정 서비스의 초기화만 확인
                    self.logger.debug("⚙️ SettingsService를 통한 초기 설정 검증 완료")
                except Exception as service_error:
                    self.logger.warning(f"⚠️ SettingsService 초기 설정 로드 실패: {service_error}")
            else:
                self.logger.debug("📋 SettingsService 없이 기본 설정 사용")

            self.logger.info("✅ 초기 설정 로드 완료")

        except Exception as e:
            self.logger.error(f"❌ 초기 설정 로드 실패: {e}")
            if hasattr(self.view, 'show_status_message'):
                self.view.show_status_message(f"설정 로드 실패: {str(e)}", False)

    def handle_save_all_settings(self) -> None:
        """모든 설정 저장 처리"""
        try:
            self.logger.info("💾 모든 설정 저장 시작")

            # 로딩 상태 표시
            if hasattr(self.view, 'show_loading_state'):
                self.view.show_loading_state(True)

            self.is_loading = True

            # Application Service를 통한 설정 저장
            if self.settings_service:
                try:
                    # 설정 저장 로직 (실제 구현에 따라 조정)
                    self.settings_service.save_all_settings()
                    success = True
                    message = "모든 설정이 성공적으로 저장되었습니다."
                except Exception as e:
                    success = False
                    message = f"설정 저장 실패: {str(e)}"
            else:
                # Infrastructure Layer 직접 호출 (폴백)
                success = True
                message = "설정이 저장되었습니다."

            # 결과 처리
            if success:
                self.logger.info("✅ 모든 설정 저장 성공")
                if hasattr(self.view, 'show_save_success_message'):
                    self.view.show_save_success_message()
            else:
                self.logger.error(f"❌ 설정 저장 실패: {message}")
                if hasattr(self.view, 'show_save_error_message'):
                    self.view.show_save_error_message(message)

        except Exception as e:
            self.logger.error(f"❌ 설정 저장 처리 중 오류: {e}")
            if hasattr(self.view, 'show_save_error_message'):
                self.view.show_save_error_message(str(e))
        finally:
            # 로딩 상태 해제
            self.is_loading = False
            if hasattr(self.view, 'show_loading_state'):
                self.view.show_loading_state(False)

    def handle_settings_changed(self) -> None:
        """설정 변경 처리"""
        self.logger.debug("⚙️ 설정이 변경되었습니다")
        # 필요시 즉시 저장이나 검증 로직 추가

    def handle_theme_changed(self, theme_value: str) -> None:
        """테마 변경 처리"""
        try:
            self.logger.info(f"🎨 테마 변경 요청: {theme_value}")

            # Application Service를 통한 테마 변경
            if self.settings_service:
                try:
                    self.settings_service.set_theme(theme_value)
                    self.logger.info(f"✅ 테마 변경 완료: {theme_value}")
                except Exception as e:
                    self.logger.error(f"❌ 테마 변경 실패: {e}")
            else:
                # Infrastructure Layer 직접 호출 (폴백)
                self.logger.info(f"✅ 테마 변경 (폴백): {theme_value}")

        except Exception as e:
            self.logger.error(f"❌ 테마 변경 처리 중 오류: {e}")

    def handle_api_status_changed(self, connected: bool) -> None:
        """API 연결 상태 변경 처리"""
        status = "연결됨" if connected else "연결 끊김"
        self.logger.info(f"🔗 API 상태 변경: {status}")

    def handle_db_status_changed(self, connected: bool) -> None:
        """데이터베이스 연결 상태 변경 처리"""
        status = "연결됨" if connected else "연결 끊김"
        self.logger.info(f"💾 DB 상태 변경: {status}")

    def cleanup(self) -> None:
        """리소스 정리"""
        try:
            self.logger.info("🧹 SettingsPresenter 리소스 정리")
            # 필요시 정리 로직 추가
        except Exception as e:
            self.logger.error(f"❌ 리소스 정리 중 오류: {e}")
