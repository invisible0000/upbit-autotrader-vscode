"""
Database Backup Management Widget

데이터베이스 백업 생성, 복원, 관리를 위한 전용 UI 위젯입니다.
MVP 패턴에 따라 Presenter와 연동되어 백업 관련 작업을 수행합니다.

Features:
- 백업 생성/복원/삭제
- 백업 목록 표시 및 관리
- 백업 스케줄링 (향후 확장)
- 진행상황 표시
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from upbit_auto_trading.infrastructure.logging import create_component_logger


class DatabaseBackupWidget(QWidget):
    """
    데이터베이스 백업 관리 위젯

    백업 생성, 복원, 삭제 등의 백업 관련 기능을 제공합니다.
    """

    # 백업 작업 시그널
    create_backup_requested = pyqtSignal(str)  # database_type
    restore_backup_requested = pyqtSignal(str)  # backup_id
    delete_backup_requested = pyqtSignal(str)  # backup_id
    refresh_backups_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("widget-database-backup")
        self._logger = create_component_logger("DatabaseBackupWidget")

        self._backup_data: List[Dict[str, Any]] = []
        self._selected_backup_id: Optional[str] = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """UI 구성 - 중복 제목 제거로 공간 확보"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 제목 제거 - 그룹박스에 이미 있음

        # 백업 생성 섹션
        self._create_backup_section(layout)

        # 백업 목록 섹션
        self._create_backup_list_section(layout)

        # 백업 관리 버튼 섹션
        self._create_management_buttons_section(layout)

    def _create_backup_section(self, parent_layout):
        """백업 생성 섹션"""
        backup_layout = QHBoxLayout()
        backup_layout.setSpacing(8)

        # 데이터베이스 선택
        db_label = QLabel("데이터베이스:")
        backup_layout.addWidget(db_label)

        self.db_combo = QComboBox()
        self.db_combo.addItems([
            "settings - Settings Database",
            "strategies - Strategies Database",
            "market_data - Market Data Database"
        ])
        backup_layout.addWidget(self.db_combo)

        backup_layout.addStretch()

        # 백업 생성 버튼
        self.create_backup_btn = QPushButton("📦 백업 생성")
        self.create_backup_btn.setObjectName("btn-create-backup")
        backup_layout.addWidget(self.create_backup_btn)

        parent_layout.addLayout(backup_layout)

    def _create_backup_list_section(self, parent_layout):
        """백업 목록 섹션"""
        list_label = QLabel("📋 백업 목록")
        list_font = QFont()
        list_font.setBold(True)
        list_label.setFont(list_font)
        parent_layout.addWidget(list_label)

        # 백업 목록 테이블
        self.backup_table = QTableWidget()
        self.backup_table.setObjectName("table-backup-list")
        self.backup_table.setColumnCount(6)
        self.backup_table.setHorizontalHeaderLabels([
            "백업 ID", "데이터베이스", "생성일시", "크기", "상태", "설명"
        ])

        # 테이블 설정
        header = self.backup_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        self.backup_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.backup_table.setAlternatingRowColors(True)

        parent_layout.addWidget(self.backup_table)

    def _create_management_buttons_section(self, parent_layout):
        """백업 관리 버튼 섹션"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        # 새로고침 버튼
        self.refresh_btn = QPushButton("🔄 새로고침")
        self.refresh_btn.setObjectName("btn-refresh-backups")
        button_layout.addWidget(self.refresh_btn)

        button_layout.addStretch()

        # 복원 버튼
        self.restore_btn = QPushButton("🔄 복원")
        self.restore_btn.setObjectName("btn-restore-backup")
        self.restore_btn.setEnabled(False)
        button_layout.addWidget(self.restore_btn)

        # 삭제 버튼
        self.delete_btn = QPushButton("🗑️ 삭제")
        self.delete_btn.setObjectName("btn-delete-backup")
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)

        parent_layout.addLayout(button_layout)

    def _connect_signals(self):
        """시그널 연결"""
        self.create_backup_btn.clicked.connect(self._on_create_backup)
        self.refresh_btn.clicked.connect(self._on_refresh_backups)
        self.restore_btn.clicked.connect(self._on_restore_backup)
        self.delete_btn.clicked.connect(self._on_delete_backup)

        self.backup_table.itemSelectionChanged.connect(self._on_selection_changed)

    def _on_create_backup(self):
        """백업 생성 버튼 클릭"""
        selected_text = self.db_combo.currentText()
        database_type = selected_text.split(" - ")[0]

        self.create_backup_requested.emit(database_type)

    def _on_refresh_backups(self):
        """새로고침 버튼 클릭"""
        self.refresh_backups_requested.emit()

    def _on_restore_backup(self):
        """복원 버튼 클릭"""
        if self._selected_backup_id:
            # 확인 대화상자
            reply = QMessageBox.question(
                self,
                "백업 복원 확인",
                f"선택한 백업으로 데이터베이스를 복원하시겠습니까?\n\n"
                f"백업 ID: {self._selected_backup_id}\n\n"
                f"⚠️ 현재 데이터는 백업 시점으로 되돌아갑니다.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.restore_backup_requested.emit(self._selected_backup_id)

    def _on_delete_backup(self):
        """삭제 버튼 클릭"""
        if self._selected_backup_id:
            # 확인 대화상자
            reply = QMessageBox.question(
                self,
                "백업 삭제 확인",
                f"선택한 백업을 삭제하시겠습니까?\n\n"
                f"백업 ID: {self._selected_backup_id}\n\n"
                f"⚠️ 삭제된 백업은 복구할 수 없습니다.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.delete_backup_requested.emit(self._selected_backup_id)

    def _on_selection_changed(self):
        """테이블 선택 변경"""
        selected_items = self.backup_table.selectedItems()

        if selected_items:
            row = selected_items[0].row()
            backup_id_item = self.backup_table.item(row, 0)

            if backup_id_item:
                self._selected_backup_id = backup_id_item.text()
                self.restore_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)
            else:
                self._selected_backup_id = None
                self.restore_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
        else:
            self._selected_backup_id = None
            self.restore_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)

    def update_backup_list(self, backup_data: List[Dict[str, Any]]):
        """백업 목록 업데이트"""
        try:
            self._backup_data = backup_data
            self.backup_table.setRowCount(len(backup_data))

            for row, backup in enumerate(backup_data):
                # 백업 ID
                self.backup_table.setItem(row, 0, QTableWidgetItem(
                    backup.get('backup_id', '')[:8] + '...'  # 앞 8자리만 표시
                ))

                # 데이터베이스 타입
                self.backup_table.setItem(row, 1, QTableWidgetItem(
                    backup.get('source_database_type', '')
                ))

                # 생성일시
                created_at = backup.get('created_at', '')
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        formatted_date = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        formatted_date = created_at
                else:
                    formatted_date = '알 수 없음'

                self.backup_table.setItem(row, 2, QTableWidgetItem(formatted_date))

                # 파일 크기
                file_size = backup.get('file_size_bytes', 0)
                if file_size > 0:
                    size_mb = file_size / (1024 * 1024)
                    size_text = f"{size_mb:.1f} MB"
                else:
                    size_text = '알 수 없음'

                self.backup_table.setItem(row, 3, QTableWidgetItem(size_text))

                # 상태
                status = backup.get('status', '')
                status_icons = {
                    'PENDING': '⏳',
                    'IN_PROGRESS': '🔄',
                    'COMPLETED': '✅',
                    'FAILED': '❌'
                }
                status_text = f"{status_icons.get(status, '❓')} {status}"
                self.backup_table.setItem(row, 4, QTableWidgetItem(status_text))

                # 설명
                description = backup.get('description', '')
                self.backup_table.setItem(row, 5, QTableWidgetItem(description))

            self._logger.info(f"📋 백업 목록 업데이트 완료: {len(backup_data)}개")

        except Exception as e:
            self._logger.error(f"❌ 백업 목록 업데이트 실패: {e}")

    def clear_backup_list(self):
        """백업 목록 초기화"""
        self.backup_table.setRowCount(0)
        self._backup_data.clear()
        self._selected_backup_id = None
        self.restore_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def set_enabled(self, enabled: bool):
        """위젯 활성화/비활성화"""
        self.create_backup_btn.setEnabled(enabled)
        self.refresh_btn.setEnabled(enabled)

        # 선택된 항목이 있을 때만 복원/삭제 버튼 활성화
        if enabled and self._selected_backup_id:
            self.restore_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
        else:
            self.restore_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)

    def get_selected_backup(self) -> Optional[Dict[str, Any]]:
        """선택된 백업 정보 반환"""
        if self._selected_backup_id:
            for backup in self._backup_data:
                if backup.get('backup_id', '').startswith(self._selected_backup_id[:8]):
                    return backup
        return None
