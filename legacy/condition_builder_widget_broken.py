"""
조건 빌더 임베딩 위젯 - ConditionBuilderDialog의 임베딩 버전
MVP 패턴 4+1 위젯 구조를 QWidget으로 임베딩하여 콤팩트한 UI 제공
"""

from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QSizePolicy, QFrame, QScrollArea, QMessageBox
)
from PyQt6.QtCore import QSize, pyqtSignal

from upbit_auto_trading.infrastructure.logging import create_component_logger

# 위젯 클래스들 import
from .widgets.variable_selection_widget import VariableSelectionWidget
from .widgets.comparison_settings_widget import ComparisonSettingsWidget
from .widgets.conditional_compatibility_widget import ConditionalCompatibilityWidget
from .widgets.condition_preview_widget import ConditionPreviewWidget


class ConditionBuilderWidget(QWidget):
    """
    임베딩 가능한 조건 빌더 위젯
    - 4+1 위젯 구조를 QWidget으로 구현
    - 콤팩트한 레이아웃 최적화
    - 부모 화면에 임베딩 가능
    """

    # 시그널 정의
    condition_created = pyqtSignal(dict)
    condition_cancelled = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = create_component_logger("ConditionBuilderWidget")

        # 4+1 위젯 참조 저장
        self.variable_selection_widget: Optional[VariableSelectionWidget] = None
        self.comparison_settings_widget: Optional[ComparisonSettingsWidget] = None
        self.conditional_compatibility_widget: Optional[ConditionalCompatibilityWidget] = None
        self.condition_preview_widget: Optional[ConditionPreviewWidget] = None

        # 상태 변수
        self.is_edit_mode = False
        self.current_condition_data: Optional[Dict[str, Any]] = None

        # UI 초기화
        self._init_ui()
        self._setup_widget_connections()

        self.logger.info("ConditionBuilderWidget 초기화 완료")

    def _init_ui(self):
        """임베딩 최적화된 UI 초기화"""
        # 메인 레이아웃 (콤팩트)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)  # 콤팩트한 여백
        main_layout.setSpacing(4)  # 콤팩트한 간격

        # 스크롤 영역 (콘텐츠가 긴 경우 대비)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(scroll_area.horizontalScrollBarPolicy())
        scroll_area.setVerticalScrollBarPolicy(scroll_area.verticalScrollBarPolicy())

        # 스크롤 콘텐츠 위젯
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(4, 4, 4, 4)
        content_layout.setSpacing(6)

        # 4+1 위젯 섹션들 생성
        self._create_widget_sections(content_layout)

        # 하단 액션 버튼들
        self._create_action_buttons(content_layout)

        # 스크롤 영역에 콘텐츠 설정
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # 최소 크기 설정 (콤팩트)
        self.setMinimumSize(QSize(350, 400))  # 다이얼로그보다 작게
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

    def _create_widget_sections(self, layout: QVBoxLayout):
        """4+1 위젯 섹션들 생성"""
        try:
            # 1. 변수 선택 위젯
            var_group = QGroupBox("📊 변수 선택")
            var_group.setMaximumHeight(200)  # 높이 제한
            var_layout = QVBoxLayout()
            var_layout.setContentsMargins(4, 4, 4, 4)

            self.variable_selection_widget = VariableSelectionWidget()
            var_layout.addWidget(self.variable_selection_widget)
            var_group.setLayout(var_layout)
            layout.addWidget(var_group)

            # 2. 비교 설정 위젯
            comp_group = QGroupBox("⚖️ 비교 설정")
            comp_group.setMaximumHeight(150)  # 높이 제한
            comp_layout = QVBoxLayout()
            comp_layout.setContentsMargins(4, 4, 4, 4)

            self.comparison_settings_widget = ComparisonSettingsWidget()
            comp_layout.addWidget(self.comparison_settings_widget)
            comp_group.setLayout(comp_layout)
            layout.addWidget(comp_group)

            # 3. 호환성 위젯 (조건부 표시)
            self.conditional_compatibility_widget = ConditionalCompatibilityWidget()
            layout.addWidget(self.conditional_compatibility_widget)

            # 4. 조건 미리보기 위젯
            preview_group = QGroupBox("👁️ 조건 미리보기")
            preview_group.setMaximumHeight(120)  # 높이 제한
            preview_layout = QVBoxLayout()
            preview_layout.setContentsMargins(4, 4, 4, 4)

            self.condition_preview_widget = ConditionPreviewWidget()
            preview_layout.addWidget(self.condition_preview_widget)
            preview_group.setLayout(preview_layout)
            layout.addWidget(preview_group)

            self.logger.info("4+1 위젯 섹션 생성 완료")

        except Exception as e:
            self.logger.error(f"위젯 섹션 생성 실패: {e}")
            raise

    def _create_action_buttons(self, layout: QVBoxLayout):
        """하단 액션 버튼들 생성"""
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(4, 4, 4, 4)

        # 취소 버튼
        self.cancel_btn = QPushButton("❌ 취소")
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        self.cancel_btn.setToolTip("조건 생성을 취소합니다")
        button_layout.addWidget(self.cancel_btn)

        button_layout.addStretch()

        # 조건 생성/수정 버튼
        self.create_btn = QPushButton("✅ 조건 생성")
        self.create_btn.clicked.connect(self._on_create_clicked)
        self.create_btn.setToolTip("조건을 생성합니다")
        self.create_btn.setDefault(True)
        button_layout.addWidget(self.create_btn)

        layout.addLayout(button_layout)

    def _setup_widget_connections(self):
        """4+1 위젯간 시그널 연결"""
        try:
            if not all([
                self.variable_selection_widget,
                self.comparison_settings_widget,
                self.conditional_compatibility_widget,
                self.condition_preview_widget
            ]):
                self.logger.error("일부 위젯이 초기화되지 않았습니다")
                return

            # 변수 선택 → 호환성 체크 & 미리보기 업데이트
            self.variable_selection_widget.variable_selected.connect(
                self._on_variable_changed
            )
            self.variable_selection_widget.parameters_changed.connect(
                self._on_parameters_changed
            )

            # 비교 설정 → 미리보기 업데이트
            self.comparison_settings_widget.operator_changed.connect(
                self._update_preview
            )
            self.comparison_settings_widget.comparison_value_changed.connect(
                self._update_preview
            )
            self.comparison_settings_widget.trend_direction_changed.connect(
                self._update_preview
            )

            self.logger.info("위젯 간 시그널 연결 완료")

        except Exception as e:
            self.logger.error(f"시그널 연결 실패: {e}")

    def _on_variable_changed(self, var_id: str, var_info: Dict[str, Any]):
        """변수 변경 시 처리"""
        try:
            # 호환성 체크 및 표시/숨김
            if var_info.get('category') == 'external':
                self.conditional_compatibility_widget.show_widget()
                # 호환성 체크 실행
                self._check_compatibility()
            else:
                self.conditional_compatibility_widget.hide_widget()

            # 미리보기 업데이트
            self._update_preview()

        except Exception as e:
        except Exception as e:
            self.logger.error(f"변수 변경 처리 실패: {e}")

    def _on_parameters_changed(self, parameters: Dict[str, Any]):
        """매개변수 변경 시 처리"""
        try:
            # 미리보기 업데이트
            self._update_preview()

        except Exception as e:
            self.logger.error(f"매개변수 변경 처리 실패: {e}")

    def _check_compatibility(self):
        """호환성 체크 실행"""
        try:
            if self.conditional_compatibility_widget:
                # 현재 조건 데이터 수집
                condition_data = self._collect_condition_data()

                # external 변수 ID 추출
                external_var_id = condition_data.get('variable')
                if external_var_id:
                    # 호환성 체크
                    self.conditional_compatibility_widget.check_compatibility(external_var_id)

        except Exception as e:
            self.logger.error(f"호환성 체크 실패: {e}")

    def _update_preview(self):
        """조건 미리보기 업데이트"""
        try:
            if self.condition_preview_widget:
                # 현재 조건 데이터 수집
                condition_data = self._collect_condition_data()

                # 미리보기 업데이트
                self.condition_preview_widget.update_preview(condition_data)

        except Exception as e:
            self.logger.error(f"미리보기 업데이트 실패: {e}")

    def _collect_condition_data(self) -> Dict[str, Any]:
        """현재 조건 데이터 수집"""
        try:
            condition_data = {}

            # 변수 선택 위젯에서 데이터 수집
            if self.variable_selection_widget:
                condition_data['variable'] = self.variable_selection_widget.get_selected_variable()
                condition_data['category'] = self.variable_selection_widget.get_selected_category()
                condition_data['parameters'] = self.variable_selection_widget.get_current_parameters()

            # 비교 설정 위젯에서 데이터 수집
            if self.comparison_settings_widget:
                comparison_settings = self.comparison_settings_widget.get_all_settings()
                condition_data.update(comparison_settings)

            return condition_data

        except Exception as e:
            self.logger.error(f"조건 데이터 수집 실패: {e}")
            return {}    def _on_cancel_clicked(self):
        """취소 버튼 클릭 처리"""
        try:
            self.logger.info("조건 생성 취소됨")
            self.condition_cancelled.emit()

        except Exception as e:
            self.logger.error(f"취소 처리 실패: {e}")

    def _on_create_clicked(self):
        """생성 버튼 클릭 처리"""
        try:
            # 조건 데이터 수집
            condition_data = self._collect_condition_data()

            # 유효성 검사
            if not self._validate_condition_data(condition_data):
                return

            # 호환성 체크 (external 변수인 경우)
            if condition_data.get('category') == 'external':
                if self.conditional_compatibility_widget:
                    is_compatible = self.conditional_compatibility_widget.check_compatibility(condition_data)
                    if not is_compatible:
                        QMessageBox.warning(
                            self,
                            "호환성 경고",
                            "선택한 변수들이 호환되지 않습니다. 호환성을 확인해주세요."
                        )
                        return

            # 조건 생성 완료
            action = "수정" if self.is_edit_mode else "생성"
            self.logger.info(f"조건 {action} 완료: {condition_data}")

            self.condition_created.emit(condition_data)

        except Exception as e:
            self.logger.error(f"조건 생성 실패: {e}")
            QMessageBox.critical(
                self,
                "오류",
                f"조건을 생성할 수 없습니다: {str(e)}"
            )

    def _validate_condition_data(self, condition_data: Dict[str, Any]) -> bool:
        """조건 데이터 유효성 검사"""
        try:
            # 필수 필드 체크
            required_fields = ['variable', 'operator', 'value']
            for field in required_fields:
                if not condition_data.get(field):
                    QMessageBox.warning(
                        self,
                        "입력 오류",
                        f"{field} 필드가 비어있습니다. 모든 필드를 입력해주세요."
                    )
                    return False

            return True

        except Exception as e:
            self.logger.error(f"유효성 검사 실패: {e}")
            return False

    # === 공개 메서드들 ===

    def load_condition(self, condition_data: Dict[str, Any]):
        """기존 조건 로드 (수정 모드)"""
        try:
            self.current_condition_data = condition_data
            self.is_edit_mode = True

            # 위젯들에 데이터 로드
            if self.variable_selection_widget:
                self.variable_selection_widget.load_condition(condition_data)

            if self.comparison_settings_widget:
                self.comparison_settings_widget.load_condition(condition_data)

            # 버튼 텍스트 변경
            self.create_btn.setText("✅ 조건 수정")
            self.create_btn.setToolTip("조건을 수정합니다")

            self.logger.info(f"조건 로드 완료 (수정 모드): {condition_data}")

        except Exception as e:
            self.logger.error(f"조건 로드 실패: {e}")

    def clear_all_inputs(self):
        """모든 입력 필드 초기화"""
        try:
            # 상태 초기화
            self.is_edit_mode = False
            self.current_condition_data = None

            # 위젯들 초기화
            if self.variable_selection_widget:
                self.variable_selection_widget.clear_selection()

            if self.comparison_settings_widget:
                self.comparison_settings_widget.clear_settings()

            if self.conditional_compatibility_widget:
                self.conditional_compatibility_widget.hide_widget()

            if self.condition_preview_widget:
                self.condition_preview_widget.clear_preview()

            # 버튼 텍스트 복원
            self.create_btn.setText("✅ 조건 생성")
            self.create_btn.setToolTip("조건을 생성합니다")

            self.logger.info("모든 입력 필드 초기화 완료")

        except Exception as e:
            self.logger.error(f"입력 필드 초기화 실패: {e}")

    def exit_edit_mode(self):
        """수정 모드 종료"""
        try:
            self.is_edit_mode = False
            self.current_condition_data = None

            # 버튼 텍스트 복원
            self.create_btn.setText("✅ 조건 생성")
            self.create_btn.setToolTip("조건을 생성합니다")

            self.logger.info("수정 모드 종료")

        except Exception as e:
            self.logger.error(f"수정 모드 종료 실패: {e}")
