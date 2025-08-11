"""
환경 프로파일 설정 뷰 - 메인 화면
DDD + MVP 패턴 기반 좌우 1:2 분할 레이아웃

기존 environment_logging_redesigned_widget.py를 environment_profile_view.py로 리팩토링
- 환경 프로파일 관리 전용 탭으로 역할 명확화
- 좌측: ProfileSelectorSection (프로파일 선택 및 관리)
- 우측: YamlEditorSection (YAML 편집기)
- 비율: 1:2

Author: AI Assistant
Created: 2025-08-11
Refactored: 2025-08-11 (폴더 구조 리팩토링)
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QSplitter, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .widgets.profile_selector_section import ProfileSelectorSection
from .widgets.yaml_editor_section import YamlEditorSection
from .presenters.environment_profile_presenter import EnvironmentProfilePresenter

logger = create_component_logger("EnvironmentProfileView")


class EnvironmentProfileView(QWidget):
    """
    환경 프로파일 설정 메인 뷰
    - 좌측: ProfileSelectorSection (프로파일 선택 및 관리)
    - 우측: YamlEditorSection (YAML 편집기)
    - 비율: 1:2

    역할: 환경 프로파일 관리 전용 (로깅은 별도 탭으로 분리)
    """

    # 시그널 정의
    profile_changed = pyqtSignal(str)  # profile_path
    content_saved = pyqtSignal(str, str)  # content, filename
    error_occurred = pyqtSignal(str)  # error_message

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("🎯 EnvironmentProfileView 초기화 시작")

        # 내부 위젯들
        self.profile_selector = None
        self.yaml_editor = None
        self.main_splitter = None

        # MVP Presenter 초기화
        self.presenter = None

        # UI 초기화
        self._setup_ui()
        self._connect_signals()

        # Presenter 초기화 (View 준비 완료 후)
        self._setup_presenter()

        logger.info("✅ EnvironmentProfileView 초기화 완료")

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

        # 기본 QSplitter 스타일 사용 (전역 스타일 적용)
        # 특별한 objectName 설정 없이 기본 스타일 활용

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

            # 프레임으로 감싸기 (기본 QFrame 스타일 사용)
            profile_frame = QFrame()
            profile_frame.setFrameStyle(QFrame.Shape.StyledPanel)
            # objectName 제거 - 기본 QFrame 스타일 활용

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

            # 프레임으로 감싸기 (기본 QFrame 스타일 사용)
            editor_frame = QFrame()
            editor_frame.setFrameStyle(QFrame.Shape.StyledPanel)
            # objectName 제거 - 기본 QFrame 스타일 활용

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
                # 실제 시그널명에 맞춰 연결
                if hasattr(self.profile_selector, 'profile_selected'):
                    self.profile_selector.profile_selected.connect(self._on_profile_changed)
                if hasattr(self.profile_selector, 'profile_apply_requested'):
                    self.profile_selector.profile_apply_requested.connect(self._on_profile_changed)
                logger.debug("✅ 프로파일 선택기 시그널 연결 완료")

            # YAML 편집기 시그널 연결
            if self.yaml_editor:
                if hasattr(self.yaml_editor, 'save_requested'):
                    self.yaml_editor.save_requested.connect(self._on_save_requested)
                if hasattr(self.yaml_editor, 'content_changed'):
                    self.yaml_editor.content_changed.connect(self._on_content_changed)
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
                if hasattr(self.yaml_editor, 'load_file'):
                    self.yaml_editor.load_file(profile_path)
                elif hasattr(self.yaml_editor, 'load_profile'):
                    self.yaml_editor.load_profile(profile_path)
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
            if self.profile_selector and hasattr(self.profile_selector, 'refresh_profiles'):
                self.profile_selector.refresh_profiles()
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
            if self.profile_selector and hasattr(self.profile_selector, 'refresh_profiles'):
                self.profile_selector.refresh_profiles()
                logger.debug("✅ 프로파일 목록 새로고침 완료")

            if self.yaml_editor and hasattr(self.yaml_editor, 'refresh_content'):
                self.yaml_editor.refresh_content()
                logger.debug("✅ YAML 편집기 새로고침 완료")

            logger.info("✅ 데이터 새로고침 완료")

        except Exception as e:
            logger.error(f"❌ 데이터 새로고침 실패: {e}")

    def get_current_profile_path(self) -> str:
        """현재 선택된 프로파일 경로 반환"""
        if self.profile_selector and hasattr(self.profile_selector, 'get_selected_profile'):
            return self.profile_selector.get_selected_profile()
        return ""

    def set_current_profile(self, profile_path: str):
        """프로파일 설정"""
        logger.info(f"🎯 프로파일 설정: {profile_path}")

        if self.profile_selector and hasattr(self.profile_selector, 'set_profile'):
            self.profile_selector.set_profile(profile_path)

    # === MVP Presenter 관련 메서드 ===

    def _setup_presenter(self):
        """MVP Presenter 설정"""
        logger.debug("🔧 MVP Presenter 설정 시작")

        try:
            # Presenter 생성 및 View 연결
            self.presenter = EnvironmentProfilePresenter(self)

            # Presenter 시그널 연결
            self._connect_presenter_signals()

            logger.debug("✅ MVP Presenter 설정 완료")

        except Exception as e:
            logger.error(f"❌ MVP Presenter 설정 실패: {e}")

    def _connect_presenter_signals(self):
        """Presenter 시그널 연결"""
        if not self.presenter:
            return

        logger.debug("🔧 Presenter 시그널 연결")

        try:
            # Presenter → View 시그널 연결
            self.presenter.profile_data_loaded.connect(self._on_presenter_profile_loaded)
            self.presenter.yaml_content_loaded.connect(self._on_presenter_yaml_loaded)
            self.presenter.validation_result.connect(self._on_presenter_validation)
            self.presenter.save_completed.connect(self._on_presenter_save_completed)
            self.presenter.error_occurred.connect(self._on_presenter_error)

            logger.debug("✅ Presenter 시그널 연결 완료")

        except Exception as e:
            logger.error(f"❌ Presenter 시그널 연결 실패: {e}")

    # === Presenter 시그널 핸들러 ===

    def _on_presenter_profile_loaded(self, profile_data: dict):
        """Presenter에서 프로파일 데이터 로드 완료"""
        logger.debug(f"📂 Presenter 프로파일 로드: {profile_data.get('name', 'Unknown')}")

        # 프로파일 선택기에 데이터 업데이트
        if self.profile_selector and hasattr(self.profile_selector, 'update_profile_data'):
            self.profile_selector.update_profile_data(profile_data)

    def _on_presenter_yaml_loaded(self, yaml_content: str):
        """Presenter에서 YAML 내용 로드 완료"""
        logger.debug(f"📄 Presenter YAML 로드: {len(yaml_content)} 문자")

        # YAML 편집기에 내용 로드
        if self.yaml_editor and hasattr(self.yaml_editor, 'set_content'):
            self.yaml_editor.set_content(yaml_content)

    def _on_presenter_validation(self, is_valid: bool, message: str):
        """Presenter에서 검증 결과 수신"""
        if is_valid:
            logger.info(f"✅ 검증 성공: {message}")
        else:
            logger.warning(f"⚠️ 검증 실패: {message}")
            # 사용자에게 검증 실패 알림 (필요시 구현)

    def _on_presenter_save_completed(self, filename: str):
        """Presenter에서 저장 완료 알림"""
        logger.info(f"💾 Presenter 저장 완료: {filename}")

        # 프로파일 목록 새로고침
        if self.profile_selector and hasattr(self.profile_selector, 'refresh_profiles'):
            self.profile_selector.refresh_profiles()

    def _on_presenter_error(self, error_message: str):
        """Presenter에서 에러 발생"""
        logger.error(f"❌ Presenter 에러: {error_message}")

        # View 레벨에서 에러 처리
        self._on_error_occurred(error_message)
