#!/usr/bin/env python3
"""
조건부 호환성 위젯 - 외부 변수 선택시에만 표시

외부 변수와 내부 변수 간의 호환성을 실시간으로 검증하고 표시합니다.
첨부 이미지 요구사항: "호환성 검증은 외부 변수를 쓰지 않으면 필요 없는 정보이므로 평소에는 안보니다가"
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal
from typing import Dict, Any, TYPE_CHECKING

from upbit_auto_trading.infrastructure.logging import create_component_logger

# TYPE_CHECKING for lint safety
if TYPE_CHECKING:
    try:
        from ...trigger_builder.components.core.compatibility_validator import CompatibilityValidator
    except ImportError:
        pass

# 호환성 검증 시스템 import
COMPATIBILITY_VALIDATOR_AVAILABLE = False
try:
    from ...trigger_builder.components.core.compatibility_validator import CompatibilityValidator as CompatValidator
    COMPATIBILITY_VALIDATOR_AVAILABLE = True
except ImportError:
    CompatValidator = None

# 공통 컴포넌트 import
try:
    from upbit_auto_trading.ui.desktop.common.components import StyledGroupBox
    STYLED_COMPONENTS_AVAILABLE = True
except ImportError:
    StyledGroupBox = QGroupBox
    STYLED_COMPONENTS_AVAILABLE = False


class ConditionalCompatibilityWidget(QWidget):
    """조건부 호환성 위젯

    Features:
        - 조건부 표시: 외부 변수 선택시에만 표시
        - 실시간 호환성 검증
        - 시각적 상태 표시 (성공/경고/오류)
        - 상세한 호환성 정보 제공

    Signals:
        compatibility_status_changed: 호환성 상태 변경 (is_compatible, message)
        visibility_changed: 표시 상태 변경 (is_visible)
    """

    # 시그널 정의
    compatibility_status_changed = pyqtSignal(bool, str)  # is_compatible, message
    visibility_changed = pyqtSignal(bool)                 # is_visible

    def __init__(self, parent=None):
        """위젯 초기화"""
        super().__init__(parent)
        self.logger = create_component_logger("ConditionalCompatibilityWidget")

        # 호환성 검증기 초기화
        self.compatibility_validator = None
        if COMPATIBILITY_VALIDATOR_AVAILABLE and CompatValidator:
            try:
                self.compatibility_validator = CompatValidator()
                self.logger.info("CompatibilityValidator 초기화 완료")
            except Exception as e:
                self.logger.error(f"CompatibilityValidator 초기화 실패: {e}")

        # 현재 상태
        self.current_internal_variable = None
        self.current_external_variable = None
        self.is_currently_visible = False

        # UI 초기화
        self.init_ui()

        # 초기에는 숨김
        self.hide_widget()

    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 메인 그룹박스
        self.main_group = StyledGroupBox("⚠️ 호환성 검증")
        self.main_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(4)

        # 호환성 상태 라벨
        self.status_label = QLabel("호환성 검증 중...")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("font-size: 11px; padding: 4px;")
        self.main_layout.addWidget(self.status_label)

        # 상세 정보 라벨
        self.detail_label = QLabel("")
        self.detail_label.setWordWrap(True)
        self.detail_label.setStyleSheet("font-size: 10px; color: #666; padding: 2px;")
        self.main_layout.addWidget(self.detail_label)

        self.main_group.setLayout(self.main_layout)
        layout.addWidget(self.main_group)
        self.setLayout(layout)

    def show_widget(self):
        """위젯 표시 (외부 변수 선택시)"""
        if not self.is_currently_visible:
            self.is_currently_visible = True
            self.show()
            self.visibility_changed.emit(True)
            self.logger.debug("호환성 위젯 표시됨")

    def hide_widget(self):
        """위젯 숨김 (외부 변수 미선택시)"""
        if self.is_currently_visible:
            self.is_currently_visible = False
            self.hide()
            self.visibility_changed.emit(False)
            self.logger.debug("호환성 위젯 숨겨짐")

    def check_compatibility(self, internal_var_id: str, external_var_id: str):
        """두 변수간 호환성 검사"""
        self.current_internal_variable = internal_var_id
        self.current_external_variable = external_var_id

        if not self.compatibility_validator:
            self._show_fallback_compatibility()
            return

        try:
            # 실제 호환성 검증
            is_compatible, details = self.compatibility_validator.check_compatibility_with_status(
                internal_var_id, external_var_id
            )

            # UI 업데이트
            self._update_compatibility_display(is_compatible, details)

            # 시그널 발생
            message = self._generate_compatibility_message(is_compatible, details)
            self.compatibility_status_changed.emit(is_compatible, message)

            self.logger.info(f"호환성 검사 완료: {internal_var_id} vs {external_var_id} = {is_compatible}")

        except Exception as e:
            self.logger.error(f"호환성 검사 실패: {e}")
            self._show_error_state(str(e))

    def _update_compatibility_display(self, is_compatible: bool, details: Dict[str, Any]):
        """호환성 표시 업데이트"""
        if is_compatible:
            # 호환 가능
            self.status_label.setText("✅ 호환 가능")
            self.status_label.setStyleSheet(
                "font-size: 11px; padding: 4px; background-color: #d4edda; "
                "color: #155724; border: 1px solid #c3e6cb; border-radius: 4px;"
            )

            # 상세 정보
            detail_text = self._format_compatibility_details(details, True)
            self.detail_label.setText(detail_text)
            self.detail_label.setStyleSheet("font-size: 10px; color: #155724; padding: 2px;")

        else:
            # 호환 불가능
            self.status_label.setText("❌ 호환 불가")
            self.status_label.setStyleSheet(
                "font-size: 11px; padding: 4px; background-color: #f8d7da; "
                "color: #721c24; border: 1px solid #f5c6cb; border-radius: 4px;"
            )

            # 상세 정보 (경고 표시)
            detail_text = self._format_compatibility_details(details, False)
            self.detail_label.setText(detail_text)
            self.detail_label.setStyleSheet("font-size: 10px; color: #721c24; padding: 2px;")

    def _format_compatibility_details(self, details: Dict[str, Any], is_compatible: bool) -> str:
        """호환성 상세 정보 포맷팅"""
        if not details:
            return "상세 정보 없음"

        detail_parts = []

        # 비교 그룹 정보
        internal_group = details.get('internal_comparison_group', '알 수 없음')
        external_group = details.get('external_comparison_group', '알 수 없음')
        detail_parts.append(f"내부변수: {internal_group}")
        detail_parts.append(f"외부변수: {external_group}")

        # 호환성 이유
        reason = details.get('reason', '')
        if reason:
            detail_parts.append(f"이유: {reason}")

        # 권장사항
        if not is_compatible:
            recommendation = details.get('recommendation', '')
            if recommendation:
                detail_parts.append(f"권장: {recommendation}")

        return " | ".join(detail_parts)

    def _generate_compatibility_message(self, is_compatible: bool, details: Dict[str, Any]) -> str:
        """호환성 메시지 생성"""
        if is_compatible:
            return "두 변수는 호환 가능합니다"
        else:
            reason = details.get('reason', '호환되지 않습니다')
            return f"호환 불가: {reason}"

    def _show_fallback_compatibility(self):
        """폴백: 기본 호환성 표시"""
        self.status_label.setText("⚠️ 호환성 검증 불가")
        self.status_label.setStyleSheet(
            "font-size: 11px; padding: 4px; background-color: #fff3cd; "
            "color: #856404; border: 1px solid #ffeeba; border-radius: 4px;"
        )
        self.detail_label.setText("호환성 검증기를 사용할 수 없습니다. 수동으로 확인해주세요.")
        self.detail_label.setStyleSheet("font-size: 10px; color: #856404; padding: 2px;")

        # 기본적으로 호환 가능한 것으로 간주
        self.compatibility_status_changed.emit(True, "호환성 검증 불가 - 수동 확인 필요")

    def _show_error_state(self, error_message: str):
        """오류 상태 표시"""
        self.status_label.setText("🔴 검증 오류")
        self.status_label.setStyleSheet(
            "font-size: 11px; padding: 4px; background-color: #f8d7da; "
            "color: #721c24; border: 1px solid #f5c6cb; border-radius: 4px;"
        )
        self.detail_label.setText(f"오류: {error_message}")
        self.detail_label.setStyleSheet("font-size: 10px; color: #721c24; padding: 2px;")

        # 오류시 호환 불가능으로 간주
        self.compatibility_status_changed.emit(False, f"검증 오류: {error_message}")

    # === 공개 API ===

    def set_variables(self, internal_var_id: str, external_var_id: str):
        """변수 설정 및 호환성 검사"""
        if internal_var_id and external_var_id:
            self.show_widget()
            self.check_compatibility(internal_var_id, external_var_id)
        else:
            self.hide_widget()

    def clear_variables(self):
        """변수 정보 초기화 및 위젯 숨김"""
        self.current_internal_variable = None
        self.current_external_variable = None
        self.hide_widget()

    def get_current_status(self) -> tuple[bool, str]:
        """현재 호환성 상태 반환"""
        # 텍스트에서 상태 추출
        status_text = self.status_label.text()
        if "✅ 호환 가능" in status_text:
            return True, "호환 가능"
        elif "❌ 호환 불가" in status_text:
            return False, "호환 불가"
        elif "⚠️ 호환성 검증 불가" in status_text:
            return True, "검증 불가 - 수동 확인 필요"
        elif "🔴 검증 오류" in status_text:
            return False, "검증 오류"
        else:
            return True, "상태 확인 중"

    def is_visible_widget(self) -> bool:
        """위젯 표시 상태 확인"""
        return self.is_currently_visible

    def force_show_for_testing(self):
        """테스트용 강제 표시"""
        self.show_widget()
        self._show_fallback_compatibility()

    def reset(self):
        """위젯 초기화"""
        self.clear_variables()
        self.status_label.setText("호환성 검증 중...")
        self.status_label.setStyleSheet("font-size: 11px; padding: 4px;")
        self.detail_label.setText("")
