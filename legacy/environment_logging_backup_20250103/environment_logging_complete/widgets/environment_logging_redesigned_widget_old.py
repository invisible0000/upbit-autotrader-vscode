"""
환경 및 로깅 설정 탭 - 재디자인된 메인 위젯
DDD + MVP 패턴 기반 좌우 1:2 분할 레이아웃

Author: AI Assistant
Created: 2025-08-11
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QSplitter, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .profile_selector_section import ProfileSelectorSection
from .yaml_editor_section import YamlEditorSection

logger = create_component_logger("EnvironmentLoggingRedesignedWidget")


class EnvironmentLoggingRedesignedWidget(QWidget):
    """
    환경 및 로깅 설정 메인 위젯 (재디자인)
    - 좌측: ProfileSelectorSection (프로파일 선택 및 관리)
    - 우측: YamlEditorSection (YAML 편집기)
    - 비율: 1:2
    """

    # 시그널 정의
    profile_changed = pyqtSignal(str)  # profile_path
    content_saved = pyqtSignal(str, str)  # content, filename
    error_occurred = pyqtSignal(str)  # error_message

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("🎯 EnvironmentLoggingRedesignedWidget 초기화 시작")

        # 내부 위젯들
        self.profile_selector = None
        self.yaml_editor = None
        self.main_splitter = None

        # UI 초기화
        self._setup_ui()
        self._connect_signals()

        logger.info("✅ EnvironmentLoggingRedesignedWidget 초기화 완료")

    def _setup_ui(self):
        """UI 레이아웃 설정"""
        logger.debug("🔧 UI 레이아웃 설정 시작")

        # 메인 레이아웃
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 좌우 분할 스플리터 설정
        self._setup_splitter_layout()

        # 스플리터를 메인 레이아웃에 추가
        main_layout.addWidget(self.main_splitter)

        # 분할 위젯들 설정
        self._setup_profile_selector()
        self._setup_yaml_editor()

        # 스플리터 비율 설정 (1:2)
        self._setup_splitter_ratios()

        logger.debug("✅ UI 레이아웃 설정 완료")

    def _setup_splitter_layout(self):
        """QSplitter 기반 1:2 분할 레이아웃 설정"""
        logger.debug("🔧 스플리터 레이아웃 설정")

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # 스플리터 스타일 설정
        self.main_splitter.setHandleWidth(1)
        self.main_splitter.setChildrenCollapsible(False)  # 완전 축소 방지

        logger.debug("✅ 스플리터 레이아웃 설정 완료")

    def _setup_profile_selector(self):
        """좌측 프로파일 선택기 설정"""
        logger.debug("🔧 프로파일 선택기 설정")

        try:
            # ProfileSelectorSection 위젯 생성
            self.profile_selector = ProfileSelectorSection(self)

            # 프레임으로 감싸기 (스타일링 용도)
            profile_frame = QFrame()
            profile_frame.setFrameStyle(QFrame.Shape.StyledPanel)
            profile_frame.setObjectName("profile_selector_frame")

            # 프로파일 선택기를 프레임에 배치
            profile_layout = QHBoxLayout(profile_frame)
            profile_layout.setContentsMargins(8, 8, 8, 8)
            profile_layout.addWidget(self.profile_selector)

            # 스플리터에 추가
            self.main_splitter.addWidget(profile_frame)

            logger.debug("✅ 프로파일 선택기 설정 완료")

        except Exception as e:
            logger.error(f"❌ 프로파일 선택기 설정 실패: {e}")
            # 에러 시 빈 위젯으로 대체
            error_widget = QWidget()
            error_widget.setObjectName("profile_selector_error")
            self.main_splitter.addWidget(error_widget)

    def _setup_yaml_editor(self):
        """우측 YAML 편집기 설정"""
        logger.debug("🔧 YAML 편집기 설정")

        try:
            # YamlEditorSection 위젯 생성
            self.yaml_editor = YamlEditorSection(self)

            # 프레임으로 감싸기 (스타일링 용도)
            editor_frame = QFrame()
            editor_frame.setFrameStyle(QFrame.Shape.StyledPanel)
            editor_frame.setObjectName("yaml_editor_frame")

            # YAML 편집기를 프레임에 배치
            editor_layout = QHBoxLayout(editor_frame)
            editor_layout.setContentsMargins(8, 8, 8, 8)
            editor_layout.addWidget(self.yaml_editor)

            # 스플리터에 추가
            self.main_splitter.addWidget(editor_frame)

            logger.debug("✅ YAML 편집기 설정 완료")

        except Exception as e:
            logger.error(f"❌ YAML 편집기 설정 실패: {e}")
            # 에러 시 빈 위젯으로 대체
            error_widget = QWidget()
            error_widget.setObjectName("yaml_editor_error")
            self.main_splitter.addWidget(error_widget)

    def _setup_splitter_ratios(self):
        """스플리터 비율 1:2로 설정"""
        logger.debug("🔧 스플리터 비율 설정 (1:2)")

        # 전체 크기에서 1:2 비율로 설정
        total_width = 900  # 기본 가정 크기
        left_width = total_width // 3  # 1/3
        right_width = total_width * 2 // 3  # 2/3

        self.main_splitter.setSizes([left_width, right_width])

        logger.debug(f"✅ 스플리터 비율 설정 완료: {left_width}:{right_width}")

    def _connect_signals(self):
        """시그널 연결"""
        logger.debug("🔧 시그널 연결 시작")

        try:
            # 프로파일 선택기 시그널 연결
            if self.profile_selector:
                self.profile_selector.profile_changed.connect(self._on_profile_changed)
                self.profile_selector.error_occurred.connect(self._on_error_occurred)
                logger.debug("✅ 프로파일 선택기 시그널 연결 완료")

            # YAML 편집기 시그널 연결
            if self.yaml_editor:
                self.yaml_editor.save_requested.connect(self._on_save_requested)
                self.yaml_editor.content_changed.connect(self._on_content_changed)
                self.yaml_editor.error_occurred.connect(self._on_error_occurred)
                logger.debug("✅ YAML 편집기 시그널 연결 완료")

            logger.debug("✅ 모든 시그널 연결 완료")

        except Exception as e:
            logger.error(f"❌ 시그널 연결 실패: {e}")

    # === 시그널 핸들러 ===

    def _on_profile_changed(self, profile_path: str):
        """프로파일 변경 시 처리"""
        logger.info(f"📂 프로파일 변경: {profile_path}")

        try:
            # YAML 편집기에 새 프로파일 로드
            if self.yaml_editor and profile_path:
                self.yaml_editor.load_file(profile_path)
                logger.debug("✅ YAML 편집기에 프로파일 로드 완료")

            # 외부에 변경 알림
            self.profile_changed.emit(profile_path)

        except Exception as e:
            logger.error(f"❌ 프로파일 변경 처리 실패: {e}")
            self._on_error_occurred(f"프로파일 로드 실패: {e}")

    def _on_save_requested(self, content: str, filename: str):
        """저장 요청 시 처리"""
        logger.info(f"💾 저장 요청: {filename}")

        try:
            # 프로파일 선택기에 저장 완료 알림
            if self.profile_selector:
                self.profile_selector.refresh_profile_list()
                logger.debug("✅ 프로파일 목록 새로고침 완료")

            # 외부에 저장 완료 알림
            self.content_saved.emit(content, filename)

            logger.info(f"✅ 파일 저장 완료: {filename}")

        except Exception as e:
            logger.error(f"❌ 저장 처리 실패: {e}")
            self._on_error_occurred(f"저장 실패: {e}")

    def _on_content_changed(self, content: str):
        """내용 변경 시 처리 (필요시 확장)"""
        logger.debug(f"📝 내용 변경됨 ({len(content)} 문자)")
        # 현재는 로깅만, 필요시 추가 로직 구현

    def _on_error_occurred(self, error_message: str):
        """에러 발생 시 처리"""
        logger.error(f"❌ 에러 발생: {error_message}")

        # 에러 메시지 박스 표시
        QMessageBox.warning(
            self,
            "오류",
            f"작업 중 오류가 발생했습니다:\n\n{error_message}"
        )

        # 외부에 에러 알림
        self.error_occurred.emit(error_message)

    # === 공개 메서드 ===

    def refresh_data(self):
        """데이터 새로고침"""
        logger.info("🔄 데이터 새로고침 시작")

        try:
            if self.profile_selector:
                self.profile_selector.refresh_profile_list()
                logger.debug("✅ 프로파일 목록 새로고침 완료")

            if self.yaml_editor:
                self.yaml_editor.refresh_current_file()
                logger.debug("✅ YAML 편집기 새로고침 완료")

            logger.info("✅ 데이터 새로고침 완료")

        except Exception as e:
            logger.error(f"❌ 데이터 새로고침 실패: {e}")

    def get_current_profile_path(self) -> str:
        """현재 선택된 프로파일 경로 반환"""
        if self.profile_selector:
            return self.profile_selector.get_current_profile_path()
        return ""

    def set_current_profile(self, profile_path: str):
        """프로파일 설정"""
        logger.info(f"🎯 프로파일 설정: {profile_path}")

        if self.profile_selector:
            self.profile_selector.set_current_profile(profile_path)
