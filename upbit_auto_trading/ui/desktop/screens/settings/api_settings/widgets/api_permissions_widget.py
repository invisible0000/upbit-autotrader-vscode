"""
API 권한 설정 위젯

API 권한 관리를 담당하는 위젯

Phase 2 마이그레이션으로 생성됨:
- 기존: ApiKeyManagerSecure의 권한 설정 부분
- 새로운: 독립적인 위젯으로 분리
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QCheckBox, QGroupBox)
from PyQt6.QtCore import pyqtSignal

from upbit_auto_trading.infrastructure.logging import create_component_logger

class ApiPermissionsWidget(QWidget):
    """
    API 권한 설정 위젯

    거래 권한 등 API 권한 설정을 관리합니다.
    """

    # 시그널 정의
    permissions_changed = pyqtSignal(bool)  # trade_permission

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("widget-api-permissions")

        self.logger = create_component_logger("ApiPermissionsWidget")

        self._setup_ui()
        self._connect_signals()

        self.logger.info("✅ API 권한 설정 위젯 초기화 완료")

    def _setup_ui(self):
        """UI 설정"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)

        # API 권한 설정 그룹
        permissions_group = QGroupBox("API 권한 설정")
        permissions_layout = QVBoxLayout(permissions_group)

        # 거래 권한 체크박스
        self.trade_permission_checkbox = QCheckBox("거래 권한 (매수/매도)")
        self.trade_permission_checkbox.setObjectName("checkbox-trade-permission")
        permissions_layout.addWidget(self.trade_permission_checkbox)

        self.main_layout.addWidget(permissions_group)

    def _connect_signals(self):
        """시그널 연결"""
        self.trade_permission_checkbox.stateChanged.connect(self._on_permission_changed)

    def _on_permission_changed(self):
        """권한 변경 시 처리"""
        trade_permission = self.trade_permission_checkbox.isChecked()
        self.permissions_changed.emit(trade_permission)
        self.logger.debug(f"거래 권한 변경: {trade_permission}")

    def set_trade_permission(self, enabled: bool):
        """거래 권한 설정"""
        self.trade_permission_checkbox.setChecked(enabled)
        self.logger.debug(f"거래 권한 설정: {enabled}")

    def get_trade_permission(self) -> bool:
        """거래 권한 상태 반환"""
        return self.trade_permission_checkbox.isChecked()

    def clear_permissions(self):
        """권한 설정 초기화"""
        self.trade_permission_checkbox.setChecked(False)
        self.logger.debug("권한 설정 초기화 완료")
