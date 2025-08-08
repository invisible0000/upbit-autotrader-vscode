"""
데이터베이스 설정 모듈 - simple_paths 시스템용

이 모듈은 새로운 단순화된 데이터베이스 설정 기능을 구현합니다.
- 3개 고정 데이터베이스 파일 상태 확인
- 데이터베이스 초기화 및 백업
- 데이터베이스 정보 표시
"""

import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QMessageBox, QGroupBox,
    QTextEdit, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from upbit_auto_trading.infrastructure.configuration.paths import infrastructure_paths
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("DatabaseSettings")


class DatabaseSettings(QWidget):
    """데이터베이스 설정 위젯 - simple_paths 기반"""

    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.paths = infrastructure_paths
        self._setup_ui()
        self._update_database_info()

    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 제목
        title_label = QLabel("데이터베이스 설정")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 설명
        desc_label = QLabel("3개의 고정 데이터베이스 파일을 관리합니다.")
        desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc_label)

        # 데이터베이스 상태 그룹
        self._create_database_status_group(layout)

        # 관리 기능 그룹
        self._create_management_group(layout)

        # 백업 기능 그룹
        self._create_backup_group(layout)

        layout.addStretch()

    def _create_database_status_group(self, parent_layout):
        """데이터베이스 상태 그룹 생성"""
        group = QGroupBox("데이터베이스 상태")
        group_layout = QVBoxLayout(group)

        # 상태 표시용 텍스트 영역
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(200)
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
        """)
        group_layout.addWidget(self.status_text)

        # 새로고침 버튼
        refresh_btn = QPushButton("상태 새로고침")
        refresh_btn.clicked.connect(self._update_database_info)
        refresh_btn.setMaximumWidth(120)
        group_layout.addWidget(refresh_btn)

        parent_layout.addWidget(group)

    def _create_management_group(self, parent_layout):
        """관리 기능 그룹 생성"""
        group = QGroupBox("데이터베이스 관리")
        group_layout = QVBoxLayout(group)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()

        # 초기화 버튼
        init_btn = QPushButton("데이터베이스 초기화")
        init_btn.clicked.connect(self._initialize_databases)
        init_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        button_layout.addWidget(init_btn)

        # 검증 버튼
        verify_btn = QPushButton("무결성 검증")
        verify_btn.clicked.connect(self._verify_databases)
        verify_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        button_layout.addWidget(verify_btn)

        button_layout.addStretch()
        group_layout.addLayout(button_layout)

        parent_layout.addWidget(group)

    def _create_backup_group(self, parent_layout):
        """백업 기능 그룹 생성"""
        group = QGroupBox("백업 관리")
        group_layout = QVBoxLayout(group)

        # 백업 버튼들
        button_layout = QHBoxLayout()

        backup_btn = QPushButton("전체 백업 생성")
        backup_btn.clicked.connect(self._create_backup)
        backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        button_layout.addWidget(backup_btn)

        restore_btn = QPushButton("백업에서 복원")
        restore_btn.clicked.connect(self._restore_backup)
        restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        button_layout.addWidget(restore_btn)

        button_layout.addStretch()
        group_layout.addLayout(button_layout)

        parent_layout.addWidget(group)

    def _update_database_info(self):
        """데이터베이스 정보 업데이트"""
        try:
            info_lines = []
            info_lines.append("=== 데이터베이스 상태 정보 ===\n")

            # 각 데이터베이스 파일 상태 확인
            databases = [
                ("Settings DB", self.paths.SETTINGS_DB, "애플리케이션 설정 및 구성"),
                ("Strategies DB", self.paths.STRATEGIES_DB, "매매 전략 및 룰"),
                ("Market Data DB", self.paths.MARKET_DATA_DB, "시장 데이터 및 차트")
            ]

            for name, db_path, description in databases:
                info_lines.append(f"📊 {name}")
                info_lines.append(f"   경로: {db_path}")
                info_lines.append(f"   설명: {description}")

                if db_path.exists():
                    # 파일 크기
                    size_mb = db_path.stat().st_size / (1024 * 1024)
                    info_lines.append(f"   상태: ✅ 존재 ({size_mb:.2f} MB)")

                    # 테이블 수 확인
                    try:
                        with sqlite3.connect(str(db_path)) as conn:
                            cursor = conn.cursor()
                            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                            table_count = cursor.fetchone()[0]
                            info_lines.append(f"   테이블: {table_count}개")
                    except sqlite3.Error as e:
                        info_lines.append(f"   오류: {e}")
                else:
                    info_lines.append("   상태: ❌ 파일 없음")

                info_lines.append("")

            # 백업 디렉토리 정보
            backup_dir = self.paths.BACKUPS_DIR
            if backup_dir.exists():
                backup_files = list(backup_dir.glob("*.sqlite3"))
                info_lines.append(f"💾 백업 파일: {len(backup_files)}개")
            else:
                info_lines.append("💾 백업 파일: 없음")

            self.status_text.setPlainText("\n".join(info_lines))

        except Exception as e:
            logger.error(f"데이터베이스 정보 업데이트 실패: {e}")
            self.status_text.setPlainText(f"정보 로드 실패: {e}")

    def _initialize_databases(self):
        """데이터베이스 초기화"""
        reply = QMessageBox.question(
            self,
            "데이터베이스 초기화",
            "모든 데이터베이스를 초기화하시겠습니까?\n\n⚠️ 기존 데이터가 모두 삭제됩니다!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 각 데이터베이스 파일 생성/초기화
                databases = [self.paths.SETTINGS_DB, self.paths.STRATEGIES_DB, self.paths.MARKET_DATA_DB]

                for db_path in databases:
                    if db_path.exists():
                        db_path.unlink()  # 기존 파일 삭제

                    # 새 데이터베이스 파일 생성
                    with sqlite3.connect(str(db_path)) as conn:
                        conn.execute("CREATE TABLE IF NOT EXISTS init_check (id INTEGER PRIMARY KEY, created_at TEXT)")
                        conn.execute("INSERT INTO init_check (created_at) VALUES (?)", (datetime.now().isoformat(),))
                        conn.commit()

                QMessageBox.information(self, "초기화 완료", "모든 데이터베이스가 성공적으로 초기화되었습니다.")
                self._update_database_info()
                self.settings_changed.emit()

            except Exception as e:
                logger.error(f"데이터베이스 초기화 실패: {e}")
                QMessageBox.critical(self, "초기화 실패", f"데이터베이스 초기화 중 오류가 발생했습니다:\n{e}")

    def _verify_databases(self):
        """데이터베이스 무결성 검증"""
        try:
            results = []
            databases = [
                ("Settings", self.paths.SETTINGS_DB),
                ("Strategies", self.paths.STRATEGIES_DB),
                ("Market Data", self.paths.MARKET_DATA_DB)
            ]

            for name, db_path in databases:
                if not db_path.exists():
                    results.append(f"❌ {name}: 파일 없음")
                    continue

                try:
                    with sqlite3.connect(str(db_path)) as conn:
                        conn.execute("PRAGMA integrity_check")
                        results.append(f"✅ {name}: 정상")
                except sqlite3.Error as e:
                    results.append(f"❌ {name}: {e}")

            QMessageBox.information(
                self,
                "검증 결과",
                "\n".join(results)
            )

        except Exception as e:
            logger.error(f"데이터베이스 검증 실패: {e}")
            QMessageBox.critical(self, "검증 실패", f"검증 중 오류가 발생했습니다:\n{e}")

    def _create_backup(self):
        """전체 백업 생성"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.paths.BACKUPS_DIR / f"db_backup_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)

            databases = [self.paths.SETTINGS_DB, self.paths.STRATEGIES_DB, self.paths.MARKET_DATA_DB]
            backed_up = 0

            for db_path in databases:
                if db_path.exists():
                    backup_path = backup_dir / db_path.name
                    shutil.copy2(str(db_path), str(backup_path))
                    backed_up += 1

            if backed_up > 0:
                QMessageBox.information(
                    self,
                    "백업 완료",
                    f"{backed_up}개 데이터베이스 파일이 백업되었습니다.\n\n백업 위치: {backup_dir}"
                )
            else:
                QMessageBox.warning(self, "백업 실패", "백업할 데이터베이스 파일이 없습니다.")

        except Exception as e:
            logger.error(f"백업 생성 실패: {e}")
            QMessageBox.critical(self, "백업 실패", f"백업 생성 중 오류가 발생했습니다:\n{e}")

    def _restore_backup(self):
        """백업에서 복원"""
        try:
            backup_dir = self.paths.BACKUPS_DIR
            if not backup_dir.exists():
                QMessageBox.warning(self, "복원 실패", "백업 폴더가 존재하지 않습니다.")
                return

            from PyQt6.QtWidgets import QFileDialog
            selected_dir = QFileDialog.getExistingDirectory(
                self,
                "백업 폴더 선택",
                str(backup_dir)
            )

            if selected_dir:
                selected_path = Path(selected_dir)
                db_files = list(selected_path.glob("*.sqlite3"))

                if not db_files:
                    QMessageBox.warning(self, "복원 실패", "선택한 폴더에 데이터베이스 파일이 없습니다.")
                    return

                reply = QMessageBox.question(
                    self,
                    "백업 복원",
                    f"{len(db_files)}개의 데이터베이스 파일을 복원하시겠습니까?\n\n⚠️ 기존 데이터가 덮어쓰여집니다!",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    restored = 0
                    for db_file in db_files:
                        target_path = self.paths.DATA_DIR / db_file.name
                        shutil.copy2(str(db_file), str(target_path))
                        restored += 1

                    QMessageBox.information(
                        self,
                        "복원 완료",
                        f"{restored}개 데이터베이스 파일이 복원되었습니다."
                    )
                    self._update_database_info()
                    self.settings_changed.emit()

        except Exception as e:
            logger.error(f"백업 복원 실패: {e}")
            QMessageBox.critical(self, "복원 실패", f"백업 복원 중 오류가 발생했습니다:\n{e}")

    def load_settings(self):
        """설정 로드 (호환성을 위한 메서드)"""
        self._update_database_info()

    def save_settings(self):
        """설정 저장 (호환성을 위한 메서드)"""
        # 현재는 별도 저장할 설정이 없음
        pass
