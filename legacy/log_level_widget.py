"""
로그 레벨 설정 위젯

이 모듈은 로깅 레벨 선택 관련 UI 컴포넌트를 구현합니다.
- DEBUG, INFO, WARNING, ERROR, CRITICAL 레벨 선택
- 실시간 로그 레벨 변경 시그널
"""

from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QGroupBox, QFormLayout
)

from upbit_auto_trading.infrastructure.logging import create_component_logger


class LogLevelWidget(QWidget):
    """로그 레벨 설정 위젯"""

    # 시그널
    level_changed = pyqtSignal(str)  # 로그 레벨 변경 시그널
    settings_changed = pyqtSignal()  # 일반 설정 변경 시그널

    def __init__(self, parent=None):
        """초기화

        Args:
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.setObjectName("widget-log-level")

        # 로깅 설정
        self.logger = create_component_logger("LogLevelWidget")
        self.logger.info("📊 로그 레벨 위젯 초기화 시작")

        # 내부 상태
        self._current_level = "INFO"
        self._is_loading = False

        # UI 설정
        self._setup_ui()

        self.logger.info("✅ 로그 레벨 위젯 초기화 완료")

    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 로그 레벨 설정 그룹
        level_group = QGroupBox("로그 레벨 설정")
        level_layout = QFormLayout(level_group)

        # 로그 레벨 콤보박스
        self.level_combo = QComboBox()
        self.level_combo.addItem("🔍 DEBUG - 상세 디버그 정보", "DEBUG")
        self.level_combo.addItem("ℹ️ INFO - 일반 정보", "INFO")
        self.level_combo.addItem("⚠️ WARNING - 경고", "WARNING")
        self.level_combo.addItem("❌ ERROR - 오류", "ERROR")
        self.level_combo.addItem("💥 CRITICAL - 치명적 오류", "CRITICAL")
        self.level_combo.currentIndexChanged.connect(self._on_level_changed)

        # 설명 레이블
        self.description_label = QLabel("로그 출력 레벨을 설정합니다. 설정된 레벨 이상의 로그만 출력됩니다.")
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: gray; font-size: 11px;")

        level_layout.addRow("로그 레벨:", self.level_combo)
        level_layout.addRow("", self.description_label)
        layout.addWidget(level_group)

    def _on_level_changed(self):
        """로그 레벨 변경 처리"""
        if self._is_loading:
            return

        level_value = self.level_combo.currentData()
        if level_value and level_value != self._current_level:
            self._current_level = level_value
            self.logger.debug(f"📊 로그 레벨 변경됨: {level_value}")
            self.level_changed.emit(level_value)
            self.settings_changed.emit()

    def get_level(self) -> str:
        """현재 선택된 로그 레벨 반환

        Returns:
            str: 현재 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        return self.level_combo.currentData() or "INFO"

    def set_level(self, level: str):
        """로그 레벨 설정

        Args:
            level: 설정할 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self._is_loading = True
        try:
            index = self.level_combo.findData(level)
            if index >= 0:
                self.level_combo.setCurrentIndex(index)
                self._current_level = level
                self.logger.debug(f"📊 로그 레벨 설정됨: {level}")
            else:
                self.logger.warning(f"⚠️ 알 수 없는 로그 레벨: {level}")
        finally:
            self._is_loading = False

    def reset_to_default(self):
        """기본값으로 재설정"""
        self.set_level("INFO")
