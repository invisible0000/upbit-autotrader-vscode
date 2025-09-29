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

# Application Layer - Infrastructure 의존성 격리

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
    description_updated = pyqtSignal(str, str)  # backup_id, new_description

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("widget-database-backup")
        # Application Layer 로깅 서비스 사용 (폴백: None)
        self._logger = None

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
        self.backup_table.itemChanged.connect(self._on_item_changed)

        # 데이터베이스 콤보박스 변경 시그널 연결
        self.db_combo.currentTextChanged.connect(self._on_database_changed)

    def _on_create_backup(self):
        """백업 생성 버튼 클릭"""
        selected_text = self.db_combo.currentText()
        database_type = selected_text.split(" - ")[0]

        self.create_backup_requested.emit(database_type)

    def _on_refresh_backups(self):
        """새로고침 버튼 클릭"""
        self.refresh_backups_requested.emit()

    def _on_database_changed(self):
        """데이터베이스 콤보박스 변경 시 호출"""
        self._logger.info(f"🔄 데이터베이스 선택 변경: {self.db_combo.currentText()}")

        # 백업 목록 새로고침 요청 (MVP 패턴 준수)
        self.refresh_backups_requested.emit()

        # 선택된 데이터베이스에 따라 백업 목록 필터링은 새로고침 완료 후 자동으로 적용됨

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

    def _on_item_changed(self, item: QTableWidgetItem):
        """테이블 아이템 변경 시 호출 - 설명 열 편집 처리"""
        try:
            # 설명 열(5번)만 편집 허용
            if item.column() == 5:
                row = item.row()
                backup_id_item = self.backup_table.item(row, 0)
                if backup_id_item:
                    backup_id = backup_id_item.text()
                    new_description = item.text()

                    self._logger.info(f"📝 백업 설명 변경: {backup_id} -> {new_description}")

                    # Presenter에 설명 변경 요청
                    self.description_updated.emit(backup_id, new_description)

        except Exception as e:
            self._logger.error(f"❌ 아이템 변경 처리 실패: {e}")

    def _filter_backup_list(self):
        """선택된 데이터베이스에 따라 백업 목록 필터링"""
        if not self._backup_data:
            return

        # 선택된 데이터베이스 타입 추출
        selected_text = self.db_combo.currentText()
        selected_db_type = selected_text.split(" - ")[0]

        # 필터링된 백업 데이터
        filtered_data = []
        for backup in self._backup_data:
            if backup.get('database_type') == selected_db_type:
                filtered_data.append(backup)

        self._logger.info(f"📋 백업 목록 필터링: {selected_db_type} -> {len(filtered_data)}개 항목")

        # 테이블 업데이트 (필터링된 데이터로)
        self._update_table_with_data(filtered_data)

    def _update_table_with_data(self, backup_data: List[Dict[str, Any]]):
        """테이블을 특정 백업 데이터로 업데이트"""
        try:
            # 테이블 업데이트 중 시그널 차단 (메타데이터 덮어쓰기 방지)
            self.backup_table.blockSignals(True)

            self.backup_table.setRowCount(len(backup_data))

            for row, backup in enumerate(backup_data):
                # 백업 ID (0번 컬럼) - 전체 텍스트 표시 (잘림 없음)
                backup_id = backup.get('backup_id', 'N/A')
                item = QTableWidgetItem(str(backup_id))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                # 툴팁으로 전체 텍스트 표시
                item.setToolTip(str(backup_id))
                self.backup_table.setItem(row, 0, item)

                # 데이터베이스 (1번 컬럼) - database_type 사용
                database = backup.get('database_type', 'N/A')
                item = QTableWidgetItem(str(database))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.backup_table.setItem(row, 1, item)

                # 생성일시 (2번 컬럼) - creation_time 사용
                creation_time = backup.get('creation_time')
                if creation_time:
                    # datetime 객체를 문자열로 변환
                    created_at = creation_time.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    created_at = 'N/A'
                item = QTableWidgetItem(str(created_at))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.backup_table.setItem(row, 2, item)

                # 크기 (3번 컬럼) - file_size (bytes)를 MB로 변환
                file_size_bytes = backup.get('file_size', 0)
                if file_size_bytes > 0:
                    size_mb = file_size_bytes / (1024 * 1024)
                    size_text = f"{size_mb:.1f} MB"
                else:
                    size_text = "0 MB"
                item = QTableWidgetItem(size_text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.backup_table.setItem(row, 3, item)

                # 상태 (4번 컬럼)
                status = backup.get('status', 'COMPLETED')
                item = QTableWidgetItem(str(status))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.backup_table.setItem(row, 4, item)

                # 설명 (5번 컬럼) - 편집 가능하게 설정
                # 백업 데이터에서 가져온 설명을 그대로 사용 (기본값으로 대체하지 않음)
                description = backup.get('description', '')
                if not description:
                    # 설명이 없을 때만 기본값 표시 (메타데이터에는 저장하지 않음)
                    description = f"{backup.get('database_type', 'Unknown')} 데이터베이스 백업"
                item = QTableWidgetItem(str(description))
                # 설명 열은 편집 가능하게 유지 (편집 불가 플래그 제거)
                self.backup_table.setItem(row, 5, item)

            # 선택 상태 초기화
            self._selected_backup_id = None
            self.restore_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)

            self._logger.debug(f"📊 백업 테이블 업데이트 완료: {len(backup_data)}개 항목")

        except Exception as e:
            self._logger.error(f"❌ 백업 테이블 업데이트 실패: {e}")
        finally:
            # 시그널 다시 활성화 (try/except와 상관없이 실행)
            self.backup_table.blockSignals(False)

    def update_backup_list(self, backup_data: List[Dict[str, Any]]):
        """백업 목록 업데이트 - 전체 데이터 저장 후 필터링 적용"""
        try:
            # 전체 백업 데이터 저장
            self._backup_data = backup_data
            self._logger.info(f"📋 백업 데이터 업데이트: {len(backup_data)}개 항목")

            # 현재 선택된 데이터베이스에 따라 필터링 적용
            self._filter_backup_list()

        except Exception as e:
            self._logger.error(f"❌ 백업 목록 업데이트 실패: {e}")
            # 에러 발생 시 빈 테이블로 초기화
            self.backup_table.setRowCount(0)

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
