"""
환경 관리 위젯 - 환경 프로파일 및 환경변수 통합 관리 (LEGACY)

TASK-20250809-01에 따라 environment_logging/ 폴더의
EnvironmentLoggingWidget으로 교체됨.

이 위젯은 EnvironmentProfileWidget과 EnvironmentVariablesWidget을
하나의 탭에서 통합 관리할 수 있도록 컨테이너 역할을 합니다.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal

# Infrastructure Layer Enhanced Logging v4.0
from upbit_auto_trading.infrastructure.logging import create_component_logger


class EnvironmentManagementWidget(QWidget):
    """환경 관리 통합 위젯

    환경 프로파일 관리와 환경변수 관리를 하나의 화면에서 제공합니다.
    - 좌측: 환경 프로파일 선택 (Development/Testing/Production)
    - 우측: 환경변수 상세 설정 (로깅, 거래, API, 시스템)
    """

    # 시그널 정의
    environment_changed = pyqtSignal(str)  # 환경 변경 시
    environment_variable_changed = pyqtSignal(str, str)  # 환경변수 변경 시

    def __init__(self, parent=None):
        """환경 관리 위젯 초기화"""
        super().__init__(parent)

        # Infrastructure Layer Enhanced Logging v4.0 초기화
        self.logger = create_component_logger("EnvironmentManagementWidget")
        self.logger.info("🌍 환경 관리 통합 위젯 초기화 시작")

        # 하위 위젯들 초기화
        self._init_sub_widgets()

        # UI 설정
        self._setup_ui()

        # 시그널 연결
        self._connect_signals()

        self.logger.info("✅ 환경 관리 통합 위젯 초기화 완료")

    def _init_sub_widgets(self):
        """하위 위젯들 초기화"""
        self.logger.debug("🔧 하위 위젯들 초기화 시작")

        try:
            from upbit_auto_trading.ui.desktop.screens.settings.widgets.environment_profile_widget import (
                EnvironmentProfileWidget
            )
            from upbit_auto_trading.ui.desktop.screens.settings.widgets.environment_variables_widget import (
                EnvironmentVariablesWidget
            )

            # 환경 프로파일 위젯 생성
            self.environment_profile_widget = EnvironmentProfileWidget(self)
            self.logger.debug("🏗️ 환경 프로파일 위젯 생성 완료")

            # 환경변수 위젯 생성
            self.environment_variables_widget = EnvironmentVariablesWidget(self)
            self.logger.debug("🔧 환경변수 위젯 생성 완료")

            self.logger.info("✅ 하위 위젯들 초기화 성공")

        except Exception as e:
            self.logger.error(f"❌ 하위 위젯 초기화 실패: {e}")

            # 폴백: 에러 메시지 위젯 생성
            self.environment_profile_widget = QWidget()
            self.environment_variables_widget = QWidget()

            widgets_info = [
                (self.environment_profile_widget, "환경 프로파일"),
                (self.environment_variables_widget, "환경변수")
            ]

            for widget, name in widgets_info:
                layout = QVBoxLayout(widget)
                error_label = QLabel(f"❌ {name} 위젯 로드 실패")
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(error_label)

    def _setup_ui(self):
        """UI 레이아웃 설정"""
        self.logger.debug("🎨 UI 레이아웃 설정 시작")

        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 제목
        title_label = QLabel("환경 관리")
        title_label.setObjectName("environment-management-title")
        font = title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        main_layout.addWidget(title_label)

        # 설명
        description_label = QLabel("개발 환경 프로파일과 환경변수를 통합 관리합니다.")
        description_label.setObjectName("environment-management-description")
        main_layout.addWidget(description_label)

        # 스플리터로 좌우 분할 (1:2 비율)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("environment-management-splitter")

        # 좌측: 환경 프로파일 위젯
        profile_container = QWidget()
        profile_container.setObjectName("environment-profile-container")
        profile_layout = QVBoxLayout(profile_container)
        profile_layout.setContentsMargins(10, 10, 10, 10)

        profile_title = QLabel("🏗️ 환경 프로파일")
        profile_title.setObjectName("environment-profile-section-title")
        font = profile_title.font()
        font.setPointSize(12)
        font.setBold(True)
        profile_title.setFont(font)
        profile_layout.addWidget(profile_title)

        profile_layout.addWidget(self.environment_profile_widget)
        splitter.addWidget(profile_container)

        # 우측: 환경변수 위젯
        variables_container = QWidget()
        variables_container.setObjectName("environment-variables-container")
        variables_layout = QVBoxLayout(variables_container)
        variables_layout.setContentsMargins(10, 10, 10, 10)

        variables_title = QLabel("🔧 환경변수 설정")
        variables_title.setObjectName("environment-variables-section-title")
        font = variables_title.font()
        font.setPointSize(12)
        font.setBold(True)
        variables_title.setFont(font)
        variables_layout.addWidget(variables_title)

        variables_layout.addWidget(self.environment_variables_widget)
        splitter.addWidget(variables_container)

        # 스플리터 비율 설정 (프로파일:변수 = 1:2)
        splitter.setSizes([300, 600])
        splitter.setCollapsible(0, False)  # 프로파일 섹션 접기 방지
        splitter.setCollapsible(1, False)  # 변수 섹션 접기 방지

        main_layout.addWidget(splitter)

        self.logger.info("✅ UI 레이아웃 설정 완료")

    def _connect_signals(self):
        """시그널 연결"""
        self.logger.debug("🔗 시그널 연결 시작")

        try:
            # 환경 프로파일 위젯 시그널 연결
            if hasattr(self.environment_profile_widget, 'environment_changed'):
                self.environment_profile_widget.environment_changed.connect(
                    self._on_environment_profile_changed
                )
                self.logger.debug("✅ 환경 프로파일 변경 시그널 연결")

            # 환경변수 위젯 시그널 연결
            if hasattr(self.environment_variables_widget, 'environment_variable_changed'):
                self.environment_variables_widget.environment_variable_changed.connect(
                    self._on_environment_variable_changed
                )
                self.logger.debug("✅ 환경변수 변경 시그널 연결")

            self.logger.info("✅ 시그널 연결 완료")

        except Exception as e:
            self.logger.error(f"❌ 시그널 연결 실패: {e}")

    def _on_environment_profile_changed(self, environment: str):
        """환경 프로파일 변경 이벤트 처리"""
        self.logger.info(f"🔄 환경 프로파일 변경: {environment}")

        # 환경변수 위젯에 현재 환경 알림 (필요 시)
        if hasattr(self.environment_variables_widget, 'set_current_environment'):
            try:
                self.environment_variables_widget.set_current_environment(environment)
                self.logger.debug(f"📨 환경변수 위젯에 환경 변경 알림: {environment}")
            except Exception as e:
                self.logger.warning(f"⚠️ 환경변수 위젯 환경 설정 실패: {e}")

        # 상위로 시그널 전파
        self.environment_changed.emit(environment)

    def _on_environment_variable_changed(self, key: str, value: str):
        """환경변수 변경 이벤트 처리"""
        self.logger.debug(f"🔄 환경변수 변경: {key} = {value}")

        # 상위로 시그널 전파
        self.environment_variable_changed.emit(key, value)

    def refresh_display(self):
        """화면 새로고침"""
        self.logger.debug("🔄 환경 관리 위젯 새로고침 시작")

        try:
            # 환경 프로파일 위젯 새로고침
            if hasattr(self.environment_profile_widget, 'refresh_display'):
                self.environment_profile_widget.refresh_display()
                self.logger.debug("✅ 환경 프로파일 위젯 새로고침")

            # 환경변수 위젯 새로고침
            if hasattr(self.environment_variables_widget, 'refresh_display'):
                self.environment_variables_widget.refresh_display()
                self.logger.debug("✅ 환경변수 위젯 새로고침")

            self.logger.info("✅ 환경 관리 위젯 새로고침 완료")

        except Exception as e:
            self.logger.error(f"❌ 환경 관리 위젯 새로고침 실패: {e}")

    def get_current_environment(self) -> str:
        """현재 선택된 환경 반환"""
        if hasattr(self.environment_profile_widget, 'get_current_environment'):
            try:
                return self.environment_profile_widget.get_current_environment()
            except Exception as e:
                self.logger.warning(f"⚠️ 현재 환경 조회 실패: {e}")

        return "Development"  # 기본값

    def set_current_environment(self, environment: str):
        """환경 설정"""
        if hasattr(self.environment_profile_widget, 'set_current_environment'):
            try:
                self.environment_profile_widget.set_current_environment(environment)
                self.logger.info(f"✅ 환경 설정 완료: {environment}")
            except Exception as e:
                self.logger.error(f"❌ 환경 설정 실패: {e}")
