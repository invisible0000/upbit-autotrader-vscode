#!/usr/bin/env python3
"""
조건 빌더 프레젠터 - MVP 패턴 적용

조건 빌더 다이얼로그의 비즈니스 로직을 담당하는 프레젠터입니다.
위젝들 간의 조정과 최종 데이터 처리를 담당합니다.

Design Pattern: MVP (Model-View-Presenter)
- View: ConditionBuilderDialog (Passive View)
- Presenter: ConditionBuilderPresenter (이 클래스)
- Model: VariableDefinitions, ConditionValidator 등
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger

if TYPE_CHECKING:
    from .widgets import (
        VariableSelectionWidget, ConditionInputWidget,
        CompatibilityWidget, ConditionPreviewWidget
    )


class ConditionBuilderPresenter(QObject):
    """조건 빌더 프레젠터

    위젯들 간의 조정과 비즈니스 로직 처리를 담당합니다.
    단일 프레젠터로 모든 위젯을 조정하되, 각 위젯의 자율성을 존중합니다.

    Responsibilities:
        1. 위젯 간 데이터 흐름 관리
        2. 최종 조건 데이터 수집 및 검증
        3. 편집 모드 상태 관리
        4. 비즈니스 규칙 적용

    Signals:
        condition_created: 새 조건이 생성되었을 때 발생
        condition_updated: 기존 조건이 수정되었을 때 발생
        validation_error: 검증 오류 발생 시
        edit_mode_changed: 편집 모드 변경 시
    """

    # 시그널 정의
    condition_created = pyqtSignal(dict)  # 조건 생성 완료
    condition_updated = pyqtSignal(dict)  # 조건 수정 완료
    validation_error = pyqtSignal(str)    # 검증 오류
    edit_mode_changed = pyqtSignal(bool)  # 편집 모드 변경

    def __init__(self):
        """프레젠터 초기화"""
        super().__init__()
        self.logger = create_component_logger("ConditionBuilderPresenter")

        # 편집 모드 상태
        self.edit_mode = False
        self.edit_condition_id = None
        self.editing_condition_name = None

        # 위젯 참조 (나중에 설정됨)
        self.variable_widget: Optional['VariableSelectionWidget'] = None
        self.input_widget: Optional['ConditionInputWidget'] = None
        self.compatibility_widget: Optional['CompatibilityWidget'] = None
        self.preview_widget: Optional['ConditionPreviewWidget'] = None

    def set_widgets(self, variable_widget, input_widget, compatibility_widget, preview_widget):
        """위젯 참조 설정 및 시그널 연결"""
        self.variable_widget = variable_widget
        self.input_widget = input_widget
        self.compatibility_widget = compatibility_widget
        self.preview_widget = preview_widget

        # 위젯 간 시그널 연결
        self._connect_widget_signals()
        self.logger.info("위젯 참조 설정 및 시그널 연결 완료")

    def _connect_widget_signals(self):
        """위젯들 간의 시그널 연결"""
        if not all([self.variable_widget, self.input_widget, self.preview_widget]):
            self.logger.warning("일부 위젯이 없어 시그널 연결 생략")
            return

        # 변수 선택 → 호환성 검증
        if self.compatibility_widget:
            self.variable_widget.variable_selected.connect(
                self._handle_variable_selected
            )

        # 입력 변경 → 미리보기 업데이트
        self.variable_widget.variable_selected.connect(self._update_preview)
        self.input_widget.operator_changed.connect(self._update_preview)
        self.input_widget.value_changed.connect(self._update_preview)
        self.input_widget.comparison_type_changed.connect(self._update_preview)

    def _handle_variable_selected(self, var_id: str, var_info: Dict[str, Any]):
        """변수 선택 시 호환성 검증 및 제안 표시"""
        if self.compatibility_widget:
            try:
                # 단일 변수 호환성 제안
                self.compatibility_widget.check_single_variable_compatibility(var_info)
                self.logger.debug(f"변수 '{var_id}' 호환성 제안 업데이트")
            except Exception as e:
                self.logger.error(f"호환성 제안 처리 실패: {e}")

    def _update_preview(self):
        """미리보기 업데이트"""
        if not self.preview_widget:
            return

        try:
            # 현재 조건 데이터 수집
            condition_data = self._collect_current_condition_data()

            # 미리보기 업데이트
            self.preview_widget.update_preview(condition_data)

        except Exception as e:
            self.logger.error(f"미리보기 업데이트 실패: {e}")

    def handle_condition_creation(self, condition_name: str, condition_desc: str = ""):
        """조건 생성 처리"""
        try:
            # 조건 데이터 수집
            condition_data = self._collect_final_condition_data(condition_name, condition_desc)

            # 검증 수행
            if not self._validate_condition_data(condition_data):
                return

            # 편집 모드에 따라 시그널 발생
            if self.edit_mode:
                condition_data['id'] = self.edit_condition_id
                self.condition_updated.emit(condition_data)
                self.logger.info(f"조건 수정 완료: {condition_name}")
            else:
                condition_data['id'] = self._generate_condition_id()
                self.condition_created.emit(condition_data)
                self.logger.info(f"조건 생성 완료: {condition_name}")

        except Exception as e:
            error_msg = f"조건 처리 실패: {str(e)}"
            self.logger.error(error_msg)
            self.validation_error.emit(error_msg)

    def _collect_current_condition_data(self) -> Dict[str, Any]:
        """현재 UI 상태에서 조건 데이터 수집 (미리보기용)"""
        condition_data = {}

        if self.variable_widget:
            condition_data['variable'] = self.variable_widget.get_variable_display_text()
            condition_data['variable_id'] = self.variable_widget.get_selected_variable()
            condition_data['category'] = self.variable_widget.get_selected_category()

        if self.input_widget:
            condition_data['operator'] = self.input_widget.get_operator()
            condition_data['value'] = self.input_widget.get_value()
            condition_data['comparison_type'] = self.input_widget.get_comparison_type()

        return condition_data

    def _collect_final_condition_data(self, name: str, description: str) -> Dict[str, Any]:
        """최종 조건 데이터 수집 (저장용)"""
        condition_data = self._collect_current_condition_data()

        # 메타데이터 추가
        condition_data.update({
            'name': name.strip(),
            'description': description.strip(),
            'created_at': self._get_timestamp(),
            'edit_mode': self.edit_mode
        })

        return condition_data

    def _validate_condition_data(self, condition_data: Dict[str, Any]) -> bool:
        """조건 데이터 검증"""
        # 필수 필드 검증
        required_fields = ['name', 'variable', 'operator', 'value']
        for field in required_fields:
            if not condition_data.get(field, '').strip():
                error_msg = f"'{field}' 필드가 비어있습니다."
                self.validation_error.emit(error_msg)
                return False

        # 미리보기 위젯의 검증 결과 확인
        if self.preview_widget and not self.preview_widget.is_valid():
            issues = self.preview_widget.get_validation_issues()
            error_msg = f"검증 실패: {', '.join(issues)}"
            self.validation_error.emit(error_msg)
            return False

        return True

    def set_edit_mode(self, condition_data: Dict[str, Any]):
        """편집 모드로 전환"""
        try:
            self.edit_mode = True
            self.edit_condition_id = condition_data.get('id')
            self.editing_condition_name = condition_data.get('name', 'Unknown')

            # 위젯들에 기존 데이터 로드
            self._load_condition_to_widgets(condition_data)

            self.edit_mode_changed.emit(True)
            self.logger.info(f"편집 모드 활성화: {self.editing_condition_name}")

        except Exception as e:
            self.logger.error(f"편집 모드 설정 실패: {e}")

    def reset_to_create_mode(self):
        """생성 모드로 초기화"""
        self.edit_mode = False
        self.edit_condition_id = None
        self.editing_condition_name = None

        # 위젯들 초기화
        self._clear_all_widgets()

        self.edit_mode_changed.emit(False)
        self.logger.info("생성 모드로 초기화")

    def _load_condition_to_widgets(self, condition_data: Dict[str, Any]):
        """조건 데이터를 위젯들에 로드 (편집 모드용)"""
        try:
            # 변수 선택 위젯
            if self.variable_widget and condition_data.get('variable_id'):
                self.variable_widget.set_selected_variable(condition_data['variable_id'])

            # 입력 위젯
            if self.input_widget:
                if condition_data.get('operator'):
                    self.input_widget.set_operator(condition_data['operator'])
                if condition_data.get('comparison_type'):
                    self.input_widget.set_comparison_type(condition_data['comparison_type'])
                if condition_data.get('value'):
                    self.input_widget.set_value(condition_data['value'])

            # 미리보기 업데이트
            self._update_preview()

        except Exception as e:
            self.logger.error(f"위젯 데이터 로드 실패: {e}")

    def _clear_all_widgets(self):
        """모든 위젯 초기화"""
        try:
            if self.input_widget:
                self.input_widget.clear_value()

            if self.compatibility_widget:
                self.compatibility_widget.clear_status()

            if self.preview_widget:
                self.preview_widget.clear_preview()

        except Exception as e:
            self.logger.error(f"위젯 초기화 실패: {e}")

    def _generate_condition_id(self) -> str:
        """새 조건 ID 생성"""
        timestamp = int(self._get_timestamp())
        return f"condition_{timestamp}"

    def _get_timestamp(self) -> float:
        """현재 타임스탬프 반환"""
        return datetime.now().timestamp()

    # === 공개 API ===

    def get_edit_mode(self) -> bool:
        """현재 편집 모드 상태 반환"""
        return self.edit_mode

    def get_editing_condition_name(self) -> Optional[str]:
        """편집 중인 조건 이름 반환"""
        return self.editing_condition_name
