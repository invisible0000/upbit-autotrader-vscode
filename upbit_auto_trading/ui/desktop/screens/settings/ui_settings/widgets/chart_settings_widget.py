"""
차트 설정 위젯

이 모듈은 차트 관련 설정 UI 컴포넌트를 구현합니다.
- 차트 스타일 설정
- 차트 업데이트 간격 설정
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QComboBox, QSpinBox,
    QGroupBox, QFormLayout
)

# Application Layer - Infrastructure 의존성 격리 (Phase 2 수정)

class ChartSettingsWidget(QWidget):
    """차트 설정 위젯"""

    # 시그널
    settings_changed = pyqtSignal()  # 설정 변경 시그널

    def __init__(self, parent=None, logging_service=None):
        """초기화

        Args:
            parent: 부모 위젯
            logging_service: 로깅 서비스 (DI)
        """
        super().__init__(parent)
        self.setObjectName("widget-chart-settings")

        # 로깅 설정 - DI 패턴 적용
        if logging_service:
            self.logger = logging_service.get_component_logger("ChartSettingsWidget")
        else:
            # DI 실패 시 명확한 오류 처리
            raise ValueError("ChartSettingsWidget에 logging_service가 주입되지 않았습니다")

        self.logger.info("� 차트 설정 위젯 초기화 시작")

        # 내부 상태
        self._is_loading = False

        # UI 설정
        self._setup_ui()

        self.logger.info("✅ 차트 설정 위젯 초기화 완료")

    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 차트 설정 그룹
        chart_group = QGroupBox("차트 설정")
        chart_layout = QFormLayout(chart_group)

        # 차트 스타일
        self.chart_style_combo = QComboBox()
        self.chart_style_combo.addItem("캔들스틱", "candlestick")
        self.chart_style_combo.addItem("라인", "line")
        self.chart_style_combo.addItem("바", "bar")
        self.chart_style_combo.currentTextChanged.connect(self._on_setting_changed)
        chart_layout.addRow("차트 스타일:", self.chart_style_combo)

        # 차트 업데이트 간격
        self.chart_update_spin = QSpinBox()
        self.chart_update_spin.setRange(1, 60)
        self.chart_update_spin.setSuffix(" 초")
        self.chart_update_spin.valueChanged.connect(self._on_setting_changed)
        chart_layout.addRow("업데이트 간격:", self.chart_update_spin)

        layout.addWidget(chart_group)

    def _on_setting_changed(self):
        """설정 변경 처리"""
        if not self._is_loading:
            self.logger.debug("📊 차트 설정 변경됨")
            self.settings_changed.emit()

    def get_chart_style(self) -> str:
        """차트 스타일 반환"""
        return self.chart_style_combo.currentData() or "candlestick"

    def get_chart_update_interval(self) -> int:
        """차트 업데이트 간격 반환 (초)"""
        return self.chart_update_spin.value()

    def set_chart_style(self, style: str):
        """차트 스타일 설정

        Args:
            style: 차트 스타일 ("candlestick", "line", "bar")
        """
        self._is_loading = True
        try:
            index = self.chart_style_combo.findData(style)
            if index >= 0:
                self.chart_style_combo.setCurrentIndex(index)
                self.logger.debug(f"📊 차트 스타일 설정됨: {style}")
            else:
                self.logger.warning(f"⚠️ 알 수 없는 차트 스타일: {style}")
        finally:
            self._is_loading = False

    def set_chart_update_interval(self, interval: int):
        """차트 업데이트 간격 설정

        Args:
            interval: 업데이트 간격 (초)
        """
        self._is_loading = True
        try:
            self.chart_update_spin.setValue(interval)
            self.logger.debug(f"📊 차트 업데이트 간격 설정됨: {interval}초")
        finally:
            self._is_loading = False

    def reset_to_default(self):
        """기본값으로 재설정"""
        self.set_chart_style("candlestick")
        self.set_chart_update_interval(1)
