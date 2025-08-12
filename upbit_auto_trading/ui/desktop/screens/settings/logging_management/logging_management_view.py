"""
실시간 로깅 관리 탭 - MVP Passive View
====================================

DDD Presentation Layer - PyQt6 UI (표시만, Passive View)
Infrastructure Layer 로깅 시스템과 통합된 실시간 로그 관리 UI

주요 특징:
- MVP 패턴 Passive View (순수 UI 관심사만)
- 좌우 1:2 분할 레이아웃 (환경변수 제어 | 로그 뷰어)
- Infrastructure 로깅 시스템 환경변수 제어
- 전역 스타일 관리 시스템 준수
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QComboBox, QCheckBox, QLineEdit,
    QPushButton, QPlainTextEdit, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class LoggingManagementView(QWidget):
    """실시간 로깅 관리 탭 - MVP Passive View"""

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """UI 레이아웃 구성 - DDD Presentation Layer 표준"""
        layout = QVBoxLayout()

        # 메인 스플리터 (좌우 1:2 비율)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setSizes([300, 600])  # 1:2 비율

        # 좌측: 환경변수 제어 패널
        self.control_panel = self._create_control_panel()

        # 우측: 로그 뷰어 패널
        self.log_viewer = self._create_log_viewer()

        self.main_splitter.addWidget(self.control_panel)
        self.main_splitter.addWidget(self.log_viewer)

        layout.addWidget(self.main_splitter)
        self.setLayout(layout)

    def _create_control_panel(self) -> QWidget:
        """환경변수 제어 패널 - Infrastructure 로깅 시스템 연동"""
        panel = QWidget()
        layout = QVBoxLayout()

        # 1. 로그 레벨 제어 그룹
        log_level_group = QGroupBox("로그 레벨 제어")
        log_level_layout = QVBoxLayout()

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText("INFO")  # 기본값

        log_level_layout.addWidget(QLabel("UPBIT_LOG_LEVEL:"))
        log_level_layout.addWidget(self.log_level_combo)
        log_level_group.setLayout(log_level_layout)

        # 2. 출력 제어 그룹
        output_group = QGroupBox("출력 제어")
        output_layout = QVBoxLayout()

        self.console_output_checkbox = QCheckBox("콘솔 출력 활성화")
        self.console_output_checkbox.setChecked(True)  # 기본값

        output_layout.addWidget(self.console_output_checkbox)
        output_group.setLayout(output_layout)

        # 3. 로깅 스코프 그룹 (Infrastructure 로깅 시스템 v4.0)
        scope_group = QGroupBox("로깅 스코프")
        scope_layout = QVBoxLayout()

        self.log_scope_combo = QComboBox()
        self.log_scope_combo.addItems(["silent", "minimal", "normal", "verbose", "debug_all"])
        self.log_scope_combo.setCurrentText("normal")  # 기본값

        scope_layout.addWidget(QLabel("UPBIT_LOG_SCOPE:"))
        scope_layout.addWidget(self.log_scope_combo)
        scope_group.setLayout(scope_layout)

        # 4. 컴포넌트 집중 모드
        focus_group = QGroupBox("컴포넌트 집중")
        focus_layout = QVBoxLayout()

        self.component_focus_edit = QLineEdit()
        self.component_focus_edit.setPlaceholderText("컴포넌트명 입력 (비어두면 모든 컴포넌트)")

        focus_layout.addWidget(QLabel("UPBIT_COMPONENT_FOCUS:"))
        focus_layout.addWidget(self.component_focus_edit)
        focus_group.setLayout(focus_layout)

        # 5. 제어 버튼
        button_layout = QHBoxLayout()
        self.apply_btn = QPushButton("설정 적용")
        self.reset_btn = QPushButton("기본값 복원")

        # 전역 스타일 적용을 위한 objectName 설정
        self.apply_btn.setObjectName("primary_button")
        self.reset_btn.setObjectName("secondary_button")

        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.reset_btn)

        # 레이아웃 조립
        layout.addWidget(log_level_group)
        layout.addWidget(output_group)
        layout.addWidget(scope_group)
        layout.addWidget(focus_group)
        layout.addLayout(button_layout)
        layout.addStretch()  # 하단 여백

        panel.setLayout(layout)
        return panel

    def _create_log_viewer(self) -> QWidget:
        """로그 뷰어 패널 - 실시간 로그 표시"""
        viewer_widget = QWidget()
        layout = QVBoxLayout()

        # 툴바
        toolbar = QHBoxLayout()

        # 자동 스크롤 토글
        self.auto_scroll_checkbox = QCheckBox("자동 스크롤")
        self.auto_scroll_checkbox.setChecked(True)

        # 로그 필터 (Phase 2에서 구현)
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("로그 필터링 (정규식 지원)")
        self.filter_edit.setEnabled(False)  # Phase 1에서는 비활성화

        # 제어 버튼
        self.clear_btn = QPushButton("로그 지우기")
        self.save_btn = QPushButton("로그 저장")

        # 전역 스타일 적용
        self.clear_btn.setObjectName("warning_button")
        self.save_btn.setObjectName("secondary_button")

        toolbar.addWidget(self.auto_scroll_checkbox)
        toolbar.addWidget(QLabel("필터:"))
        toolbar.addWidget(self.filter_edit)
        toolbar.addWidget(self.clear_btn)
        toolbar.addWidget(self.save_btn)
        toolbar.addStretch()

        # 로그 텍스트 뷰어
        self.log_text_edit = QPlainTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)

        # 모노스페이스 폰트 설정
        font = QFont("Consolas", 9)
        if not font.exactMatch():
            font = QFont("Courier New", 9)  # 폴백 폰트
        font.setFixedPitch(True)
        self.log_text_edit.setFont(font)

        # Phase 1 초기 메시지
        self.log_text_edit.setPlainText(
            "=== 실시간 로깅 관리 탭 ===\n"
            "Infrastructure Layer 로깅 시스템 v4.0 연동\n"
            "Phase 1: MVP 기본 구현 완료\n"
            "\n"
            "실시간 로그가 여기에 표시됩니다...\n"
        )

        # 상태바
        status_layout = QHBoxLayout()
        self.log_count_label = QLabel("로그 개수: 0")
        self.filter_count_label = QLabel("필터링됨: 0")

        status_layout.addWidget(self.log_count_label)
        status_layout.addWidget(self.filter_count_label)
        status_layout.addStretch()

        # 레이아웃 조립
        layout.addLayout(toolbar)
        layout.addWidget(self.log_text_edit)
        layout.addLayout(status_layout)

        viewer_widget.setLayout(layout)
        return viewer_widget

    # ===== MVP Passive View 인터페이스 =====

    def append_log(self, log_text: str):
        """로그 추가 (Presenter에서 호출)"""
        self.log_text_edit.appendPlainText(log_text)
        self._update_status()

    def append_log_batch(self, log_texts: list):
        """배치 로그 추가 (성능 최적화용)

        Args:
            log_texts: 추가할 로그 메시지 리스트
        """
        if not log_texts:
            return

        # 배치로 한번에 추가하여 UI 업데이트 최소화
        combined_text = '\n'.join(log_texts)
        self.log_text_edit.appendPlainText(combined_text)
        self._update_status()

    def clear_logs(self):
        """로그 클리어 (Presenter에서 호출)"""
        self.log_text_edit.clear()
        self._update_status()

    def get_log_level(self) -> str:
        """선택된 로그 레벨 반환"""
        return self.log_level_combo.currentText()

    def get_console_output_enabled(self) -> bool:
        """콘솔 출력 활성화 여부"""
        return self.console_output_checkbox.isChecked()

    def get_log_scope(self) -> str:
        """선택된 로그 스코프 반환"""
        return self.log_scope_combo.currentText()

    def get_component_focus(self) -> str:
        """컴포넌트 집중 모드 값 반환"""
        return self.component_focus_edit.text().strip()

    def set_log_level(self, level: str):
        """로그 레벨 설정 (환경변수 동기화용)"""
        index = self.log_level_combo.findText(level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)

    def set_console_output_enabled(self, enabled: bool):
        """콘솔 출력 설정 (환경변수 동기화용)"""
        self.console_output_checkbox.setChecked(enabled)

    def set_log_scope(self, scope: str):
        """로그 스코프 설정 (환경변수 동기화용)"""
        index = self.log_scope_combo.findText(scope)
        if index >= 0:
            self.log_scope_combo.setCurrentIndex(index)

    def set_component_focus(self, component: str):
        """컴포넌트 집중 설정 (환경변수 동기화용)"""
        self.component_focus_edit.setText(component)

    def _update_status(self):
        """상태바 업데이트"""
        # 현재 로그 라인 수 계산
        log_content = self.log_text_edit.toPlainText()
        line_count = len(log_content.split('\n')) if log_content.strip() else 0
        self.log_count_label.setText(f"로그 개수: {line_count}")

        # 필터링은 Phase 2에서 구현
        filter_text = self.filter_edit.text().strip()
        if filter_text:
            self.filter_count_label.setText(f"필터링됨: 활성")
        else:
            self.filter_count_label.setText("필터링됨: 비활성")
