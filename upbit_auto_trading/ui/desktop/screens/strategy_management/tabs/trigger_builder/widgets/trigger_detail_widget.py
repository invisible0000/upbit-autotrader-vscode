"""
트리거 상세정보 위젯 - Legacy UI 기반 MVP 구현
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout,
    QSizePolicy, QMessageBox
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
import json

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("TriggerDetailWidget")


class TriggerDetailWidget(QWidget):
    """트리거 상세정보 위젯 - MVP 패턴"""

    # 시그널 정의
    trigger_copied = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_trigger = None
        self.setup_ui()
        self.initialize_default_state()

    def setup_ui(self):
        """UI 구성"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 크기 정책을 Expanding으로 설정
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # 상세 정보 표시
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # 폰트 설정
        font = QFont()
        font.setPointSize(9)
        self.detail_text.setFont(font)

        # 문서 여백 설정
        document = self.detail_text.document()
        if document:
            document.setDocumentMargin(3)

        main_layout.addWidget(self.detail_text, 1)

        # 액션 버튼들
        self.create_button_area(main_layout)

    def create_button_area(self, parent_layout):
        """버튼 영역 생성"""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)

        self.copy_detail_btn = QPushButton("📄 복사")
        self.copy_detail_btn.setMaximumHeight(25)
        self.copy_detail_btn.clicked.connect(self.copy_detail_to_clipboard)
        btn_layout.addWidget(self.copy_detail_btn)

        self.json_view_btn = QPushButton("📋 JSON")
        self.json_view_btn.setMaximumHeight(25)
        self.json_view_btn.clicked.connect(self.show_json_popup)
        btn_layout.addWidget(self.json_view_btn)

        btn_layout.addStretch()

        parent_layout.addLayout(btn_layout)

    def initialize_default_state(self):
        """기본 상태 초기화"""
        self.detail_text.setPlainText("트리거를 선택하면 상세정보가 표시됩니다.")

    def update_trigger_detail(self, trigger_data):
        """트리거 상세정보 업데이트"""
        try:
            if not trigger_data:
                self.detail_text.setPlainText("트리거를 선택하면 상세정보가 표시됩니다.")
                self.current_trigger = None
                return

            self.current_trigger = trigger_data

            # 상세 정보 텍스트 생성
            detail_text = self.format_trigger_detail(trigger_data)
            self.detail_text.setPlainText(detail_text)

            logger.debug(f"트리거 상세정보 업데이트: {trigger_data.get('name', 'Unknown')}")

        except Exception as e:
            logger.error(f"트리거 상세정보 업데이트 실패: {e}")
            self.detail_text.setPlainText(f"상세정보 로드 실패: {str(e)}")

    def format_trigger_detail(self, trigger_data):
        """트리거 상세정보 포맷팅"""
        if isinstance(trigger_data, dict):
            # 딕셔너리 형태의 데이터
            lines = []
            lines.append("=== 트리거 상세정보 ===\n")

            lines.append(f"📌 트리거명: {trigger_data.get('name', 'N/A')}")
            lines.append(f"📊 변수: {trigger_data.get('variable', 'N/A')}")
            lines.append(f"⚙️ 조건: {trigger_data.get('condition', 'N/A')}")

            if 'description' in trigger_data:
                lines.append(f"📝 설명: {trigger_data['description']}")

            if 'created_at' in trigger_data:
                lines.append(f"⏰ 생성일: {trigger_data['created_at']}")

            if 'last_triggered' in trigger_data:
                lines.append(f"🔔 마지막 트리거: {trigger_data['last_triggered']}")

            # 추가 속성이 있으면 표시
            excluded_keys = ['name', 'variable', 'condition', 'description',
                            'created_at', 'last_triggered']
            additional_keys = [k for k in trigger_data.keys()
                              if k not in excluded_keys]

            if additional_keys:
                lines.append("\n=== 추가 속성 ===")
                for key in additional_keys:
                    lines.append(f"{key}: {trigger_data[key]}")

            return '\n'.join(lines)

        else:
            # 문자열이나 기타 형태
            return f"트리거 정보:\n{str(trigger_data)}"

    def copy_detail_to_clipboard(self):
        """상세정보를 클립보드에 복사"""
        try:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(self.detail_text.toPlainText())
                logger.debug("트리거 상세정보를 클립보드에 복사")
                self.trigger_copied.emit()
        except Exception as e:
            logger.error(f"클립보드 복사 실패: {e}")

    def show_json_popup(self):
        """JSON 형태로 데이터 표시"""
        if not self.current_trigger:
            QMessageBox.information(self, "정보", "선택된 트리거가 없습니다.")
            return

        try:
            json_str = json.dumps(self.current_trigger, indent=2, ensure_ascii=False)

            msg = QMessageBox()
            msg.setWindowTitle("트리거 JSON 데이터")
            msg.setText("트리거 데이터를 JSON 형태로 표시합니다:")
            msg.setDetailedText(json_str)
            msg.exec()

        except Exception as e:
            logger.error(f"JSON 표시 실패: {e}")
            QMessageBox.warning(self, "오류", f"JSON 변환 실패: {str(e)}")

    def clear_detail(self):
        """상세정보 초기화"""
        self.initialize_default_state()
        self.current_trigger = None
