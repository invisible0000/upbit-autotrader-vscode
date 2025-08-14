"""
MainWindow Presenter - MVP 패턴의 Presenter 계층

MainWindow와 Application Services 사이의 중재자 역할을 수행합니다.
View(MainWindow)의 프레젠테이션 로직을 담당하며,
UI 이벤트 처리와 상태 관리를 분리하여 테스트 가능한 구조를 제공합니다.
"""

from typing import Any, Dict, Protocol
from PyQt6.QtCore import QObject, pyqtSignal

from upbit_auto_trading.infrastructure.logging import create_component_logger


class IMainWindowPresenter(Protocol):
    """MainWindow Presenter 인터페이스 (Protocol 사용)"""

    def handle_theme_changed_from_service(self, theme_name: str) -> None:
        """서비스에서 테마 변경 시 처리"""
        ...

    def handle_settings_changed_from_screen(self, setting_key: str, setting_value: Any) -> None:
        """화면에서 설정 변경 시 처리"""
        ...

    def handle_api_connection_test(self) -> None:
        """API 연결 테스트 처리"""
        ...

    def handle_database_health_check(self) -> None:
        """데이터베이스 건강 검사 처리"""
        ...

    def handle_post_initialization_setup(self) -> None:
        """초기화 후 설정 처리"""
        ...


class MainWindowPresenter(QObject):
    """MainWindow MVP Presenter 구현체

    MainWindow View와 Application Services 사이의 프레젠테이션 로직을 담당합니다.
    UI 이벤트를 비즈니스 로직으로 변환하고, 서비스 결과를 UI에 반영합니다.
    """

    # 시그널 정의
    theme_update_requested = pyqtSignal(str)  # UI에 테마 업데이트 요청
    status_update_requested = pyqtSignal(str, str)  # 상태 바 업데이트 요청

    def __init__(self, services: Dict[str, Any]) -> None:
        """
        MainWindowPresenter 초기화

        Args:
            services: 필요한 서비스들의 딕셔너리
                - theme_service: 테마 관리 서비스
                - api_key_service: API 키 서비스
                - database_health_service: DB 건강 검사 서비스
                - navigation_bar: 네비게이션 바 서비스
                - status_bar: 상태 바 서비스
        """
        super().__init__()
        self.logger = create_component_logger("MainWindowPresenter")

        # 서비스 의존성 주입
        self.theme_service = services.get('theme_service')
        self.api_key_service = services.get('api_key_service')
        self.database_health_service = services.get('database_health_service')
        self.navigation_bar = services.get('navigation_bar')
        self.status_bar = services.get('status_bar')

        self.logger.info("✅ MainWindowPresenter 초기화 완료")

    def handle_theme_changed_from_service(self, theme_name: str) -> None:
        """서비스에서 테마 변경 시 처리

        Args:
            theme_name: 변경된 테마 이름
        """
        try:
            self.logger.debug(f"테마 변경 처리 시작: {theme_name}")

            # UI 업데이트 시그널 발송
            self.theme_update_requested.emit(theme_name)

            # 네비게이션 바 업데이트
            if self.navigation_bar:
                self.navigation_bar.update_all_widgets()

            self.logger.info(f"✅ 테마 변경 처리 완료: {theme_name}")

        except Exception as e:
            self.logger.error(f"❌ 테마 변경 처리 실패: {e}")

    def handle_settings_changed_from_screen(self, setting_key: str, setting_value: Any) -> None:
        """화면에서 설정 변경 시 처리

        Args:
            setting_key: 변경된 설정 키
            setting_value: 변경된 설정 값
        """
        try:
            self.logger.debug(f"설정 변경 처리: {setting_key} = {setting_value}")

            # 설정에 따른 UI 업데이트 로직
            if setting_key == "theme":
                if self.theme_service:
                    self.theme_service.set_theme(setting_value)

            self.logger.info(f"✅ 설정 변경 처리 완료: {setting_key}")

        except Exception as e:
            self.logger.error(f"❌ 설정 변경 처리 실패: {e}")

    def handle_api_connection_test(self) -> None:
        """API 연결 테스트 처리"""
        try:
            self.logger.info("API 연결 테스트 시작")

            if not self.api_key_service:
                self.logger.warning("API Key Service를 사용할 수 없음")
                self.status_update_requested.emit("api_status", "연결 실패")
                return

            # API 키 로드 및 연결 테스트
            api_keys = self.api_key_service.load_api_keys()
            if api_keys:
                self.logger.info("API 키 파일 발견 - 연결 테스트 중...")

                # 실제 연결 테스트
                connection_result = self.api_key_service.test_connection()
                if connection_result.get('success', False):
                    accounts_count = connection_result.get('accounts_count', 0)
                    krw_balance = connection_result.get('krw_balance', 0)

                    self.logger.info(f"✅ API 연결 성공 - 총 {accounts_count}개 계좌")
                    self.logger.info(f"💰 총 KRW 잔고: {krw_balance:,}원")

                    self.status_update_requested.emit("api_status", "연결됨")
                else:
                    self.logger.warning("⚠️ API 연결 실패")
                    self.status_update_requested.emit("api_status", "연결 실패")
            else:
                self.logger.info("API 키 파일이 없음 - 연결 테스트 건너뜀")
                self.status_update_requested.emit("api_status", "키 없음")

        except Exception as e:
            self.logger.error(f"❌ API 연결 테스트 실패: {e}")
            self.status_update_requested.emit("api_status", "오류")

    def handle_database_health_check(self) -> None:
        """데이터베이스 건강 검사 처리"""
        try:
            self.logger.info("🔍 DatabaseHealthService를 통한 DB 건강 검사 시작")

            if not self.database_health_service:
                self.logger.warning("Database Health Service를 사용할 수 없음")
                self.status_update_requested.emit("db_status", "서비스 없음")
                return

            # DB 건강 검사 실행
            health_result = self.database_health_service.check_startup_health()
            if health_result:
                self.logger.info("✅ DB 건강 검사 통과")
                self.status_update_requested.emit("db_status", "연결됨")
            else:
                self.logger.warning("⚠️ DB 건강 검사 실패")
                self.status_update_requested.emit("db_status", "문제 있음")

        except Exception as e:
            self.logger.error(f"❌ DB 건강 검사 실패: {e}")
            self.status_update_requested.emit("db_status", "오류")

    def handle_post_initialization_setup(self) -> None:
        """초기화 후 설정 처리"""
        try:
            self.logger.info("초기화 후 설정 처리 시작")

            # API 연결 테스트
            self.handle_api_connection_test()

            # DB 건강 검사
            self.handle_database_health_check()

            self.logger.info("✅ 초기화 후 설정 처리 완료")

        except Exception as e:
            self.logger.error(f"❌ 초기화 후 설정 처리 실패: {e}")
