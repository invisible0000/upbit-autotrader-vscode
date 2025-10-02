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
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path

# Application Layer - Infrastructure 의존성 격리 (Phase 2 수정)
from .widgets.profile_selector_section import ProfileSelectorSection
from .widgets.yaml_editor_section import YamlEditorSection
# Presenter는 Factory에서 주입됨

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

    def __init__(self, parent=None, logging_service=None):
        super().__init__(parent)

        # 로깅 설정 - DI 패턴 적용
        if logging_service:
            self.logger = logging_service.get_component_logger("EnvironmentProfileView")
        else:
            raise ValueError("EnvironmentProfileView에 logging_service가 주입되지 않았습니다")

        self.self.self.logger.warning("🚫 환경 프로파일 기능이 정지되었습니다 (통합 설정 관리 가이드)")
        self.self.self.logger.info("🎯 EnvironmentProfileView 초기화 시작 - UI만 보존, 기능 비활성화")
        self.self.self.logger.info("ℹ️ 이 기능은 config/ 기반으로 재구현될 예정입니다")

        # 내부 위젯들 (타입 힌팅 명시)
        self.profile_selector: Optional[ProfileSelectorSection] = None
        self.yaml_editor: Optional[YamlEditorSection] = None
        self.main_splitter: Optional[QSplitter] = None

        # MVP Presenter는 Factory에서 설정됨
        self.presenter = None

        # 기본 UI 설정
        self._setup_ui()
        self._connect_signals()

        self.logger.info("✅ EnvironmentProfileView 초기화 완료 - Factory 패턴")

    def set_presenter(self, presenter):
        """Presenter 설정 및 연결

        Args:
            presenter: Environment Profile Presenter 인스턴스
        """
        self.presenter = presenter
        self.logger.info("🔗 Presenter 연결됨")

        # Presenter 시그널 연결
        self._connect_presenter_signals()

    def _setup_ui(self):
        """UI 레이아웃 설정 - QSplitter 기반 1:2 비율 강제"""
        self.self.self.logger.debug("🔧 UI 레이아웃 설정 시작 - QSplitter 모드")

        # 메인 레이아웃 생성
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # ⚠️ 기능 정지 안내 메시지 추가
        from PyQt6.QtWidgets import QLabel
        from PyQt6.QtCore import Qt

        warning_label = QLabel("⚠️ 프로파일 기능이 정지되었습니다")
        warning_label.setStyleSheet("""
            QLabel {
                background-color: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
            }
        """)
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(warning_label)

        info_label = QLabel("이 기능은 config/ 폴더 기반으로 재구현될 예정입니다. 자세한 내용은 docs/PROFILE_FEATURE_DISABLED_NOTICE.md를 참조하세요.")
        info_label.setStyleSheet("""
            QLabel {
                background-color: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

        try:
            # QSplitter로 1:2 비율 강제 적용
            self.main_splitter = QSplitter(Qt.Orientation.Horizontal, self)

            # 좌측: 프로파일 선택기 생성
            self.self.self.logger.debug("🔧 ProfileSelectorSection 생성 중...")
            self.profile_selector = ProfileSelectorSection(self)
            left_frame = QFrame()
            left_frame.setMinimumSize(300, 200)
            left_layout = QVBoxLayout(left_frame)
            left_layout.addWidget(self.profile_selector)

            # 우측: YAML 편집기 생성
            self.self.self.logger.debug("🔧 YamlEditorSection 생성 중...")
            self.yaml_editor = YamlEditorSection(self)
            right_frame = QFrame()
            right_frame.setMinimumSize(600, 200)
            right_layout = QVBoxLayout(right_frame)
            right_layout.addWidget(self.yaml_editor)

            # 스플리터에 프레임 추가
            self.main_splitter.addWidget(left_frame)
            self.main_splitter.addWidget(right_frame)

            # 1:2 비율 강제 설정
            self.main_splitter.setSizes([1, 2])  # 좌측:우측 = 1:2
            self.main_splitter.setStretchFactor(0, 1)  # 좌측 stretch factor
            self.main_splitter.setStretchFactor(1, 2)  # 우측 stretch factor

            # 메인 레이아웃에 스플리터 추가
            main_layout.addWidget(self.main_splitter)

            self.self.self.logger.debug("✅ ProfileSelectorSection 생성 완료")
            self.self.self.logger.debug("✅ YamlEditorSection 생성 완료")
            self.self.self.logger.debug("✅ UI 레이아웃 설정 완료 - QSplitter 1:2 비율")

        except Exception as e:
            self.self.self.logger.error(f"❌ 실제 위젯 생성 실패: {e}")
            self.self.self.logger.debug("⚠️ 폴백: 테스트 프레임으로 복구")

            # 폴백: 테스트 프레임만 표시 (배경색 제거 - 전역 테마 적용)
            test_frame1 = QFrame()
            test_frame1.setObjectName("test_frame_left")
            test_frame1.setMinimumSize(300, 200)
            main_layout.addWidget(test_frame1)

            test_frame2 = QFrame()
            test_frame2.setObjectName("test_frame_right")
            test_frame2.setMinimumSize(600, 200)
            main_layout.addWidget(test_frame2)

            self.self.logger.debug("✅ UI 레이아웃 설정 완료 - 폴백 테스트 버전")

    def _setup_splitter_layout(self):
        """QSplitter 기반 1:2 분할 레이아웃 설정"""
        self.self.logger.debug("🔧 스플리터 레이아웃 설정")

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # 기본 QSplitter 스타일 사용 (전역 스타일 적용)
        # 특별한 objectName 설정 없이 기본 스타일 활용

        # 스플리터 스타일 설정
        self.main_splitter.setHandleWidth(1)
        self.main_splitter.setChildrenCollapsible(False)  # 완전 축소 방지

        self.self.logger.debug("✅ 스플리터 레이아웃 설정 완료")

    def _setup_profile_selector(self):
        """좌측 프로파일 선택기 설정"""
        self.self.logger.debug("🔧 프로파일 선택기 설정")

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
            if self.main_splitter is not None:
                self.main_splitter.addWidget(profile_frame)

            self.self.logger.debug("✅ 프로파일 선택기 설정 완료")

        except Exception as e:
            self.self.logger.error(f"❌ 프로파일 선택기 설정 실패: {e}")
            # 에러 시 빈 위젯으로 대체
            error_widget = QWidget()
            error_widget.setObjectName("profile_selector_error")
            if self.main_splitter is not None:
                self.main_splitter.addWidget(error_widget)

    def _setup_yaml_editor(self):
        """우측 YAML 편집기 설정"""
        self.self.logger.debug("🔧 YAML 편집기 설정")

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
            if self.main_splitter is not None:
                self.main_splitter.addWidget(editor_frame)

            self.self.logger.debug("✅ YAML 편집기 설정 완료")

        except Exception as e:
            self.self.logger.error(f"❌ YAML 편집기 설정 실패: {e}")
            # 에러 시 빈 위젯으로 대체
            error_widget = QWidget()
            error_widget.setObjectName("yaml_editor_error")
            if self.main_splitter is not None:
                self.main_splitter.addWidget(error_widget)

    def _setup_splitter_ratios(self):
        """스플리터 비율 1:2로 설정"""
        self.self.logger.debug("🔧 스플리터 비율 설정 (1:2)")

        # 전체 크기에서 1:2 비율로 설정
        total_width = 900  # 기본 가정 크기
        left_width = total_width // 3  # 1/3
        right_width = total_width * 2 // 3  # 2/3

        # 🔥 테스트: QSplitter 강제 크기 할당 주석 처리 (자연스러운 확장 테스트)
        if self.main_splitter is not None:
            self.main_splitter.setSizes([left_width, right_width])

        self.self.logger.debug(f"✅ 스플리터 비율 설정 완료 (자연 확장 모드): {left_width}:{right_width}")

    def _connect_signals(self):
        """시그널 연결"""
        self.self.logger.debug("🔧 시그널 연결 시작")

        try:
            # 프로파일 선택기 시그널 연결
            if self.profile_selector:
                # 실제 시그널명에 맞춰 연결
                if hasattr(self.profile_selector, 'profile_selected'):
                    self.profile_selector.profile_selected.connect(self._on_profile_changed)
                if hasattr(self.profile_selector, 'profile_apply_requested'):
                    self.profile_selector.profile_apply_requested.connect(self._on_profile_changed)

                # 🔥 핵심 누락 수정: 퀵 환경 전환 시그널 연결
                if hasattr(self.profile_selector, 'environment_quick_switch'):
                    self.profile_selector.environment_quick_switch.connect(self._on_environment_quick_switch)

                self.self.logger.debug("✅ 프로파일 선택기 시그널 연결 완료")

            # YAML 편집기 시그널 연결
            if self.yaml_editor:
                if hasattr(self.yaml_editor, 'save_requested'):
                    self.yaml_editor.save_requested.connect(self._on_save_requested)
                if hasattr(self.yaml_editor, 'content_changed'):
                    self.yaml_editor.content_changed.connect(self._on_content_changed)
                # 이슈 2 해결: 편집 모드 요청 시그널 연결 추가
                if hasattr(self.yaml_editor, 'edit_mode_requested'):
                    self.yaml_editor.edit_mode_requested.connect(self._on_edit_mode_requested)
                if hasattr(self.yaml_editor, 'cancel_requested'):
                    self.yaml_editor.cancel_requested.connect(self._on_cancel_requested)
                self.self.logger.debug("✅ YAML 편집기 시그널 연결 완료")

            self.self.logger.debug("✅ 모든 시그널 연결 완료")

        except Exception as e:
            self.self.logger.error(f"❌ 시그널 연결 실패: {e}")

    # === 시그널 핸들러 ===

    def _on_profile_changed(self, profile_name: str):
        """프로파일 변경 시 처리 - 콤보박스 선택 또는 퀵 버튼 클릭"""
        self.self.logger.info(f"📂 프로파일 변경 요청: {profile_name}")

        try:
            # 🔥 중요: 상태 먼저 업데이트
            self._current_profile = profile_name

            # 🔥 핵심 수정: Presenter를 통해 프로파일 로드 처리
            if self.presenter and profile_name:
                self.self.logger.info(f"🎭 Presenter를 통한 프로파일 로드 시작: {profile_name}")
                success = self.presenter.load_profile(profile_name)
                if success:
                    self.self.logger.info(f"✅ Presenter를 통한 프로파일 로드 성공: {profile_name}")
                else:
                    self.self.logger.warning(f"⚠️ Presenter를 통한 프로파일 로드 실패: {profile_name}")
            else:
                self.self.logger.warning(f"⚠️ Presenter 없음 또는 프로파일명 없음: presenter={self.presenter}, profile={profile_name}")

            # 🔥 추가: 프로파일 정보 업데이트 (ProfileSelectorSection 미리보기)
            self._update_profile_info(profile_name, f"config.{profile_name}.yaml")

            # 외부에 변경 알림
            self.profile_changed.emit(f"config.{profile_name}.yaml")

        except Exception as e:
            self.self.logger.error(f"❌ 프로파일 변경 처리 실패: {e}")
            self._on_error_occurred(f"프로파일 로드 실패: {e}")

    def _on_save_requested(self, content: str, filename: str):
        """저장 요청 시 처리"""
        self.self.logger.info(f"💾 저장 요청: {filename}")

        try:
            # 실제 파일 저장
            config_path = f"config/{filename}"
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.self.logger.info(f"📁 파일 저장 완료: {config_path}")

            # YAML 편집기를 읽기 전용 모드로 전환
            if self.yaml_editor and hasattr(self.yaml_editor, 'set_edit_mode'):
                self.yaml_editor.set_edit_mode(False)
                self.self.logger.info("✏️ 편집 모드 종료")

            # 프로파일 선택기와 빠른 환경 버튼 다시 활성화
            self._set_editing_state(False)

            # 프로파일 선택기에 저장 완료 알림
            if self.profile_selector and hasattr(self.profile_selector, 'refresh_profiles'):
                self.profile_selector.refresh_profiles()
                self.self.logger.debug("✅ 프로파일 목록 새로고침 완료")

            # 외부에 저장 완료 알림
            self.content_saved.emit(content, filename)

            self.self.logger.info(f"✅ 파일 저장 및 편집 모드 종료 완료: {filename}")

        except Exception as e:
            self.self.logger.error(f"❌ 저장 처리 실패: {e}")
            self._on_error_occurred(f"저장 실패: {e}")

    def _set_editing_state(self, editing: bool):
        """편집 상태에 따른 UI 제어"""
        try:
            # 프로파일 선택기 비활성화/활성화
            if self.profile_selector:
                if hasattr(self.profile_selector, 'setEnabled'):
                    self.profile_selector.setEnabled(not editing)
                    self.self.logger.debug(f"🔒 프로파일 선택기 {'비활성화' if editing else '활성화'}")

            # 빠른 환경 버튼 비활성화/활성화
            if self.profile_selector and hasattr(self.profile_selector, 'quick_env_buttons'):
                if hasattr(self.profile_selector.quick_env_buttons, 'setEnabled'):
                    self.profile_selector.quick_env_buttons.setEnabled(not editing)
                    self.self.logger.debug(f"🔒 빠른 환경 버튼 {'비활성화' if editing else '활성화'}")

        except Exception as e:
            self.self.logger.warning(f"UI 상태 변경 중 오류: {e}")

    def _on_edit_mode_requested(self):
        """편집 모드 요청 처리"""
        try:
            # YAML 편집기를 편집 모드로 전환
            if self.yaml_editor and hasattr(self.yaml_editor, 'set_edit_mode'):
                self.yaml_editor.set_edit_mode(True)
                self.self.logger.info("✏️ 편집 모드 활성화")

            # 다른 UI 요소들 비활성화
            self._set_editing_state(True)

        except Exception as e:
            self.self.logger.error(f"❌ 편집 모드 전환 실패: {e}")

    def _on_cancel_requested(self):
        """편집 취소 요청 처리"""
        try:
            # YAML 편집기를 읽기 전용 모드로 전환
            if self.yaml_editor and hasattr(self.yaml_editor, 'set_edit_mode'):
                self.yaml_editor.set_edit_mode(False)
                self.self.logger.info("❌ 편집 취소")

            # 다른 UI 요소들 다시 활성화
            self._set_editing_state(False)

        except Exception as e:
            self.self.logger.error(f"❌ 편집 취소 실패: {e}")

    def _on_content_changed(self, content: str):
        """내용 변경 시 처리 (로깅 최적화)"""
        # 🔥 로깅 최적화: 과도한 디버그 메시지 제거
        # 사용자 요청: "어마어마한 디버그 메세지를 내보내는데 프로파일 편집중 일부 텍스트 커서의 움직임만 있어도 반응하는 기능이 많은거 같습니다"

        # 내용 변경 시마다 로그를 출력하지 않고, 필요한 경우에만 기록
        # self.self.logger.debug(f"📝 내용 변경됨 ({len(content)} 문자)")  # 제거

        # 현재는 별도 처리 없음, 필요시 확장
        pass

    def _on_environment_quick_switch(self, environment_name: str):
        """🔥 퀵 환경 버튼 클릭 시 처리 (핵심 누락 메서드)"""
        self.self.logger.info(f"🔘 퀵 환경 전환 요청: {environment_name}")

        try:
            # 환경 프로파일 파일 경로 생성
            config_file = f"config.{environment_name}.yaml"
            config_path = Path("config") / config_file

            self.self.logger.debug(f"📁 설정 파일 경로: {config_path}")

            # 설정 파일 존재 확인
            if config_path.exists():
                # 파일 내용 읽기
                with open(config_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # YAML 편집기에 내용 로드 (실제 메서드명 사용)
                if self.yaml_editor:
                    self.yaml_editor.load_file_content(config_file, content)
                    # 🔥 중요: 기본 프로파일 편집 보호를 위해 프로파일 이름 설정
                    if hasattr(self.yaml_editor, 'set_current_profile'):
                        self.yaml_editor.set_current_profile(environment_name)
                    self.self.logger.info(f"✅ {environment_name} 환경 파일 로드 완료")

                # 프로파일 선택기에 활성 환경 설정
                if self.profile_selector:
                    self.profile_selector.set_active_environment(environment_name)
                    self.self.logger.debug(f"✅ 활성 환경 설정: {environment_name}")

                # 외부에 환경 변경 알림
                self.profile_changed.emit(str(config_path))

                self.self.logger.info(f"🎯 퀵 환경 전환 완료: {environment_name}")

            else:
                error_msg = f"설정 파일을 찾을 수 없습니다: {config_file}"
                self.self.logger.error(f"❌ {error_msg}")
                self._on_error_occurred(error_msg)

        except Exception as e:
            error_msg = f"환경 전환 실패 ({environment_name}): {e}"
            self.self.logger.error(f"❌ {error_msg}")
            self._on_error_occurred(error_msg)

    def _update_profile_info(self, profile_name: str, file_path: str):
        """프로파일 정보 표시 업데이트"""
        self.self.logger.debug(f"📋 프로파일 정보 업데이트: {profile_name}")

        try:
            # 프로파일 선택기에 현재 선택 상태 반영 (실제 메서드명 사용)
            if self.profile_selector:
                self.profile_selector.set_active_profile(profile_name)
                self.self.logger.debug("✅ 프로파일 정보 업데이트 완료")

        except Exception as e:
            self.self.logger.error(f"❌ 프로파일 정보 업데이트 실패: {e}")

    def _on_error_occurred(self, error_message: str):
        """에러 발생 시 처리"""
        self.self.logger.error(f"❌ 에러 발생: {error_message}")

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
        self.self.logger.info("🔄 데이터 새로고침 시작")

        try:
            # 프로파일 선택기 새로고침 (실제 메서드 사용)
            if self.profile_selector and hasattr(self.profile_selector, 'refresh_profiles'):
                self.profile_selector.refresh_profiles()
                self.self.logger.debug("✅ 프로파일 목록 새로고침 완료")

            # Presenter를 통한 새로고침
            if self.presenter and hasattr(self.presenter, 'refresh_profile_list'):
                self.presenter.refresh_profile_list()
                self.self.logger.debug("✅ Presenter 새로고침 완료")

            self.self.logger.info("✅ 데이터 새로고침 완료")

        except Exception as e:
            self.self.logger.error(f"❌ 데이터 새로고침 실패: {e}")

    def get_current_profile_path(self) -> str:
        """현재 선택된 프로파일 경로 반환"""
        # ProfileSelectorSection의 실제 메서드 사용
        if self.profile_selector and hasattr(self.profile_selector, 'get_current_selection'):
            selection = self.profile_selector.get_current_selection()
            return selection.get('profile', '')
        return self._current_profile

    def set_current_profile(self, profile_path: str):
        """프로파일 설정"""
        self.self.logger.info(f"🎯 프로파일 설정: {profile_path}")

        # 내부 상태 업데이트
        if '.' in profile_path:  # config.development.yaml 형태
            profile_name = profile_path.split('.')[1]  # development 추출
        else:
            profile_name = profile_path

        self._current_profile = profile_name

        # ProfileSelectorSection의 실제 메서드 사용
        if self.profile_selector and hasattr(self.profile_selector, 'set_active_profile'):
            self.profile_selector.set_active_profile(profile_name)

    # === MVP Presenter 관련 메서드 ===

    def _connect_presenter_signals(self):
        """Presenter 시그널 연결"""
        if not self.presenter:
            return

        self.self.logger.debug("🔧 Presenter 시그널 연결")

        try:
            # Presenter → View 시그널 연결
            self.presenter.profile_data_loaded.connect(self._on_presenter_profile_loaded)
            self.presenter.yaml_content_loaded.connect(self._on_presenter_yaml_loaded)
            self.presenter.profile_list_updated.connect(self._on_presenter_profile_list_updated)  # 🔥 핵심 추가!
            self.presenter.validation_result.connect(self._on_presenter_validation)
            self.presenter.save_completed.connect(self._on_presenter_save_completed)
            self.presenter.error_occurred.connect(self._on_presenter_error)

            self.self.logger.debug("✅ Presenter 시그널 연결 완료")

            # 🔥 시그널 연결 완료 후 프로파일 목록 수동 요청 (초기화 시점 문제 해결)
            self.self.logger.info("🔄 시그널 연결 완료 후 프로파일 목록 수동 새로고침 요청")
            if hasattr(self.presenter, 'refresh_profile_list'):
                self.presenter.refresh_profile_list()
                self.self.logger.debug("✅ 수동 프로파일 목록 새로고침 요청 완료")

        except Exception as e:
            self.self.logger.error(f"❌ Presenter 시그널 연결 실패: {e}")

    # === Presenter 시그널 핸들러 ===

    def _on_presenter_profile_loaded(self, profile_data: dict):
        """Presenter에서 프로파일 데이터 로드 완료"""
        self.self.logger.debug(f"📂 Presenter 프로파일 로드: {profile_data.get('name', 'Unknown')}")

        # 🔥 수정: 내부 상태 업데이트만 수행 (ProfileSelectorSection은 자체 로직으로 처리)
        profile_name = profile_data.get('name', '')
        if profile_name:
            self._current_profile = profile_name
            self.self.logger.debug(f"✅ 내부 프로파일 상태 업데이트: {profile_name}")

    def _on_presenter_yaml_loaded(self, yaml_content: str):
        """Presenter에서 YAML 내용 로드 완료"""
        self.self.logger.info(f"📄 Presenter YAML 로드 완료: {len(yaml_content)} 문자")

        # YAML 편집기에 내용 로드
        if self.yaml_editor and hasattr(self.yaml_editor, 'load_file_content'):
            if self._current_profile:
                config_file = f"config.{self._current_profile}.yaml"
                self.self.logger.info(f"🔧 YAML 편집기에 파일 로드: {config_file}")
                self.yaml_editor.load_file_content(config_file, yaml_content)

                # 🔥 추가: 편집기에 현재 프로파일 설정 (기본 프로파일 보호)
                if hasattr(self.yaml_editor, 'set_current_profile'):
                    self.yaml_editor.set_current_profile(self._current_profile)
                    self.self.logger.debug(f"📋 편집기에 현재 프로파일 설정: {self._current_profile}")

                self.self.logger.info(f"✅ YAML 편집기에 내용 로드 완료: {config_file}")
            else:
                self.self.logger.warning("⚠️ 현재 프로파일이 설정되지 않아 YAML 로드 스킵")
        else:
            self.self.logger.error("❌ YAML 편집기가 없거나 load_file_content 메서드가 없음")

    def _on_presenter_profile_list_updated(self, profiles_data: dict):
        """Presenter에서 프로파일 목록 업데이트 수신 🔥 핵심 기능!"""
        self.self.logger.info(f"🚀 _on_presenter_profile_list_updated 핸들러 호출됨! {len(profiles_data)}개")

        # 테스트 버전에서는 실제 위젯이 없으므로 무시
        if not self.profile_selector:
            self.self.logger.info("📋 테스트 버전 - 프로파일 목록 수신했지만 실제 위젯이 없음 (정상)")
            return

        # 프로파일 선택기의 콤보박스 업데이트
        if hasattr(self.profile_selector, 'load_profiles'):
            self.self.logger.debug("✅ ProfileSelectorSection과 load_profiles 메서드 존재 확인됨")

            # Presenter에서 이미 올바른 딕셔너리 형태로 준비된 데이터를 직접 사용
            self.self.logger.info(f"🚀 load_profiles 호출하기 전: {list(profiles_data.keys())}")
            self.profile_selector.load_profiles(profiles_data)
            self.self.logger.info(f"✅ 콤보박스 프로파일 목록 업데이트 완료: {len(profiles_data)}개")
        else:
            has_method = hasattr(self.profile_selector, 'load_profiles') if self.profile_selector else 'N/A'
            self.self.logger.warning(f"⚠️ 문제 발생: profile_selector={self.profile_selector}, has_load_profiles={has_method}")

    def _on_presenter_validation(self, is_valid: bool, message: str):
        """Presenter에서 검증 결과 수신"""
        if is_valid:
            self.self.logger.info(f"✅ 검증 성공: {message}")
        else:
            self.self.logger.warning(f"⚠️ 검증 실패: {message}")
            # 사용자에게 검증 실패 알림 (필요시 구현)

    def _on_presenter_save_completed(self, filename: str):
        """Presenter에서 저장 완료 알림"""
        self.self.logger.info(f"💾 Presenter 저장 완료: {filename}")

        # 프로파일 목록 새로고침
        if self.profile_selector and hasattr(self.profile_selector, 'refresh_profiles'):
            self.profile_selector.refresh_profiles()

    def _on_presenter_error(self, error_message: str):
        """Presenter에서 에러 발생"""
        self.self.logger.error(f"❌ Presenter 에러: {error_message}")
