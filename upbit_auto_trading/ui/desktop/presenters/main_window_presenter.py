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

    # 시그널 정의 - MVP 패턴 강화
    theme_update_requested = pyqtSignal(str)  # UI에 테마 업데이트 요청
    status_update_requested = pyqtSignal(str, str)  # 상태 바 업데이트 요청
    screen_change_requested = pyqtSignal(str)  # 화면 전환 요청
    window_title_update_requested = pyqtSignal(str)  # 창 제목 업데이트 요청
    navigation_update_requested = pyqtSignal()  # 네비게이션 바 업데이트 요청
    error_message_requested = pyqtSignal(str, str)  # 에러 메시지 표시 요청 (제목, 내용)

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

        # Application Service들 추가 (MVP 패턴으로 이동)
        self.screen_manager_service = services.get('screen_manager_service')
        self.window_state_service = services.get('window_state_service')
        self.menu_service = services.get('menu_service')

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

    def handle_screen_initialization(self, stack_widget, screen_widgets):
        """화면 초기화 처리 - MVP 패턴으로 이동"""
        try:
            if self.screen_manager_service:
                self.screen_manager_service.initialize_screens(stack_widget, screen_widgets)
                self.logger.info("✅ ScreenManagerService를 통한 화면 초기화 완료")
                return True
            else:
                self.logger.warning("⚠️ ScreenManagerService를 사용할 수 없음")
                return False
        except Exception as e:
            self.logger.error(f"❌ 화면 초기화 실패: {e}")
            return False

    def handle_screen_change(self, screen_name, stack_widget, screen_widgets, dependencies):
        """화면 전환 처리 - MVP 패턴으로 이동"""
        try:
            if self.screen_manager_service:
                success = self.screen_manager_service.change_screen(
                    screen_name, stack_widget, screen_widgets, dependencies
                )
                if success:
                    self.logger.info(f"✅ 화면 전환 성공: {screen_name}")
                    # UI 업데이트 시그널 발송
                    self.navigation_update_requested.emit()
                    self.window_title_update_requested.emit(f"업비트 자동매매 - {screen_name}")
                else:
                    self.logger.warning(f"⚠️ 화면 전환 실패: {screen_name}")
                    self.error_message_requested.emit("화면 전환 실패", f"{screen_name} 화면으로 전환할 수 없습니다.")
                return success
            else:
                self.logger.warning("⚠️ ScreenManagerService를 사용할 수 없음")
                self.error_message_requested.emit("서비스 오류", "화면 관리 서비스를 사용할 수 없습니다.")
                return False
        except Exception as e:
            self.logger.error(f"❌ 화면 전환 처리 실패: {e}")
            self.error_message_requested.emit("시스템 오류", f"화면 전환 중 오류가 발생했습니다: {e}")
            return False

    def handle_window_state_load(self, window, settings_service):
        """창 상태 로드 처리 - MVP 패턴으로 이동"""
        try:
            if self.window_state_service:
                self.window_state_service.load_window_state(window, settings_service)
                self.logger.info("✅ 창 상태 로드 완료")
                return True
            else:
                self.logger.warning("⚠️ WindowStateService를 사용할 수 없음")
                return False
        except Exception as e:
            self.logger.error(f"❌ 창 상태 로드 실패: {e}")
            return False

    def handle_window_state_save(self, window, settings_service):
        """창 상태 저장 처리 - MVP 패턴으로 이동"""
        try:
            if self.window_state_service:
                self.window_state_service.save_window_state(window, settings_service)
                self.logger.info("✅ 창 상태 저장 완료")
                return True
            else:
                self.logger.warning("⚠️ WindowStateService를 사용할 수 없음")
                return False
        except Exception as e:
            self.logger.error(f"❌ 창 상태 저장 실패: {e}")
            return False

    def handle_menu_setup(self, window, dependencies):
        """메뉴 설정 처리 - MVP 패턴으로 이동"""
        try:
            if self.menu_service:
                self.menu_service.setup_menu_bar(window, dependencies)
                self.logger.info("✅ 메뉴 설정 완료")
                return True
            else:
                self.logger.warning("⚠️ MenuService를 사용할 수 없음")
                return False
        except Exception as e:
            self.logger.error(f"❌ 메뉴 설정 실패: {e}")
            return False
