#!/usr/bin/env python3
"""
조건 미리보기 위젯 - 조건 빌더 컴포넌트

생성 중인 조건의 미리보기 및 최종 검증을 담당하는 독립적인 위젯입니다.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox
)
from PyQt6.QtCore import pyqtSignal
from typing import Dict, Any

from upbit_auto_trading.infrastructure.logging import create_component_logger


class ConditionPreviewWidget(QWidget):
    """조건 미리보기 위젯

    조건 생성 과정에서 실시간 미리보기와 최종 검증을 담당합니다.
    단일 책임 원칙을 따라 미리보기 관련 기능만 처리합니다.

    Signals:
        preview_updated: 미리보기가 업데이트되었을 때 발생 (preview_text)
        validation_changed: 검증 상태가 변경되었을 때 발생 (is_valid, issues)
    """

    # 시그널 정의
    preview_updated = pyqtSignal(str)        # preview_text
    validation_changed = pyqtSignal(bool, list)  # is_valid, issues

    def __init__(self, parent=None):
        """조건 미리보기 위젯 초기화"""
        super().__init__(parent)
        self.logger = create_component_logger("ConditionPreviewWidget")

        # 현재 조건 상태
        self.current_condition = {}
        self.validation_issues = []

        # UI 초기화
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 미리보기 그룹
        preview_group = QGroupBox("👁️ 조건 미리보기")
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(8, 8, 8, 8)
        preview_layout.setSpacing(6)

        # 미리보기 텍스트
        self.preview_label = QLabel("조건을 설정하면 미리보기가 표시됩니다.")
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 10px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                color: #495057;
                font-size: 12px;
            }
        """)
        preview_layout.addWidget(self.preview_label)

        # 검증 상태 라벨
        self.validation_label = QLabel()
        self.validation_label.setWordWrap(True)
        self.validation_label.setStyleSheet("""
            QLabel {
                background-color: #e7f3ff;
                border: 1px solid #b3d9ff;
                padding: 6px;
                border-radius: 3px;
                margin: 2px 0;
                font-size: 10px;
                color: #0066cc;
            }
        """)
        self.validation_label.hide()  # 초기에는 숨김
        preview_layout.addWidget(self.validation_label)

        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        self.setLayout(layout)

    def update_preview(self, condition_data: Dict[str, Any]):
        """조건 데이터 기반 미리보기 업데이트"""
        try:
            self.current_condition = condition_data.copy()

            # 미리보기 텍스트 생성
            preview_text = self._generate_preview_text(condition_data)

            # 검증 실행
            is_valid, issues = self._validate_condition(condition_data)

            # UI 업데이트
            self._update_preview_display(preview_text, is_valid)
            self._update_validation_display(is_valid, issues)

            # 시그널 발생
            self.preview_updated.emit(preview_text)
            self.validation_changed.emit(is_valid, issues)

            self.logger.debug(f"미리보기 업데이트: valid={is_valid}")

        except Exception as e:
            self.logger.error(f"미리보기 업데이트 실패: {e}")
            self._show_error_preview(str(e))

    def _generate_preview_text(self, condition_data: Dict[str, Any]) -> str:
        """조건 데이터에서 미리보기 텍스트 생성"""
        try:
            variable = condition_data.get('variable', '').replace('📈 ', '').replace('⚡ ', '').replace('🔥 ', '')
            operator = condition_data.get('operator', '')
            value = condition_data.get('value', '')
            comparison_type = condition_data.get('comparison_type', '고정값')

            if not all([variable, operator, value]):
                return "조건을 설정하면 미리보기가 표시됩니다."

            # 기본 조건 텍스트
            if comparison_type == "고정값":
                preview_text = f"조건: {variable} {operator} {value}"
            else:
                preview_text = f"조건: {variable} {operator} {value} (변수)"

            # 추가 정보
            if condition_data.get('name'):
                preview_text += f"\n이름: {condition_data['name']}"

            if condition_data.get('description'):
                preview_text += f"\n설명: {condition_data['description']}"

            return preview_text

        except Exception as e:
            self.logger.error(f"미리보기 텍스트 생성 실패: {e}")
            return "미리보기 생성 오류"

    def _validate_condition(self, condition_data: Dict[str, Any]) -> tuple[bool, list]:
        """조건 유효성 검증"""
        issues = []

        # 필수 필드 검증
        required_fields = ['variable', 'operator', 'value']
        for field in required_fields:
            if not condition_data.get(field):
                issues.append(f"'{field}' 필드가 비어있습니다.")

        # 이름 검증
        if not condition_data.get('name', '').strip():
            issues.append("조건 이름을 입력해주세요.")

        # 값 형식 검증
        value = condition_data.get('value', '').strip()
        if value:
            try:
                # 숫자 형식 검사
                float(value)
            except ValueError:
                # 문자열일 수도 있으므로 경고만
                issues.append(f"값 '{value}'이 숫자가 아닙니다. 확인해주세요.")

        self.validation_issues = issues
        return len(issues) == 0, issues

    def _update_preview_display(self, preview_text: str, is_valid: bool):
        """미리보기 표시 업데이트"""
        self.preview_label.setText(preview_text)

        if is_valid:
            # 유효한 조건 - 기본 스타일
            self.preview_label.setStyleSheet("""
                QLabel {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    padding: 10px;
                    border-radius: 4px;
                    font-family: 'Courier New', monospace;
                    color: #495057;
                    font-size: 12px;
                }
            """)
        else:
            # 유효하지 않은 조건 - 경고 스타일
            self.preview_label.setStyleSheet("""
                QLabel {
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    padding: 10px;
                    border-radius: 4px;
                    font-family: 'Courier New', monospace;
                    color: #856404;
                    font-size: 12px;
                }
            """)

    def _update_validation_display(self, is_valid: bool, issues: list):
        """검증 상태 표시 업데이트"""
        if not issues:
            self.validation_label.hide()
            return

        # 검증 이슈가 있을 때만 표시
        issue_text = "⚠️ 검증 이슈:\n" + "\n".join(f"• {issue}" for issue in issues)
        self.validation_label.setText(issue_text)

        if is_valid:
            # 경고 수준 (데이터는 있지만 개선 필요)
            self.validation_label.setStyleSheet("""
                QLabel {
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    padding: 6px;
                    border-radius: 3px;
                    margin: 2px 0;
                    font-size: 10px;
                    color: #856404;
                }
            """)
        else:
            # 오류 수준 (필수 데이터 누락)
            self.validation_label.setStyleSheet("""
                QLabel {
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    padding: 6px;
                    border-radius: 3px;
                    margin: 2px 0;
                    font-size: 10px;
                    color: #721c24;
                }
            """)

        self.validation_label.show()

    def _show_error_preview(self, error_message: str):
        """오류 상태 미리보기 표시"""
        self.preview_label.setText(f"❌ 오류: {error_message}")
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                padding: 10px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                color: #721c24;
                font-size: 12px;
            }
        """)

    # === 공개 API ===

    def get_current_condition(self) -> Dict[str, Any]:
        """현재 조건 데이터 반환"""
        return self.current_condition.copy()

    def is_valid(self) -> bool:
        """현재 조건의 유효성 상태 반환"""
        return len(self.validation_issues) == 0

    def get_validation_issues(self) -> list:
        """현재 검증 이슈 목록 반환"""
        return self.validation_issues.copy()

    def clear_preview(self):
        """미리보기 초기화"""
        self.preview_label.setText("조건을 설정하면 미리보기가 표시됩니다.")
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 10px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                color: #495057;
                font-size: 12px;
            }
        """)
        self.validation_label.hide()
        self.current_condition = {}
        self.validation_issues = []
