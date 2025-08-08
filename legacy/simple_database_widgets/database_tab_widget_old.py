"""
데이터베이스 탭 위젯 - MVP 패턴 적용

기본에 충실하면서도 MVP 패턴을 적용한 데이터베이스 설정 탭 위젯입니다.
View와 Presenter를 분리하여 비즈니스 로직과 UI를 깔끔하게 분리했습니다.
"""

from typing import Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QMessageBox, QGroupBox,
    QProgressBar, QFrame
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.ui.desktop.screens.settings.presenters.simple_database_presenter import SimpleDatabasePresenter


class DatabaseTabWidget(QWidget):
    """
    데이터베이스 설정 탭 위젯 - MVP 패턴 적용

    기본에 충실하면서도 MVP 패턴을 적용한 데이터베이스 설정 화면입니다.
    View 역할만 담당하고, 비즈니스 로직은 Presenter에서 처리합니다.
    """

    # 시그널 정의
    settings_changed = pyqtSignal()
    db_status_changed = pyqtSignal(bool)  # 연결 상태 변화

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("widget-database-tab")

        # 로깅 초기화
        self.logger = create_component_logger("DatabaseTabWidget")
        self.logger.info("📊 데이터베이스 탭 위젯 (MVP) 초기화 시작")

        # Presenter 초기화
        self.presenter = SimpleDatabasePresenter(self)

        # UI 설정
        self._setup_ui()
        self._connect_signals()

        # 초기 데이터 로드 (Presenter를 통해)
        self.presenter.load_database_info()

        self.logger.info("✅ 데이터베이스 탭 위젯 (MVP) 초기화 완료")

    def _setup_ui(self):
        """UI 구성"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 제목
        title_label = QLabel("📊 데이터베이스 설정")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # 현재 데이터베이스 정보 그룹
        self._create_current_info_group(main_layout)

        # 데이터베이스 상태 그룹
        self._create_status_group(main_layout)

        # 관리 기능 그룹
        self._create_management_group(main_layout)

        # 진행 상황 표시
        self._create_progress_section(main_layout)

        main_layout.addStretch()

    def _create_current_info_group(self, parent_layout):
        """현재 데이터베이스 정보 그룹"""
        group = QGroupBox("📋 현재 데이터베이스 정보")
        layout = QFormLayout(group)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 정보 라벨들
        self.settings_db_label = QLabel("로딩 중...")
        self.strategies_db_label = QLabel("로딩 중...")
        self.market_data_db_label = QLabel("로딩 중...")

        # 라벨 스타일
        info_style = "color: #333333; background-color: #f5f5f5; padding: 8px; border-radius: 4px; font-family: monospace;"
        self.settings_db_label.setStyleSheet(info_style)
        self.strategies_db_label.setStyleSheet(info_style)
        self.market_data_db_label.setStyleSheet(info_style)

        layout.addRow("⚙️ 설정 DB:", self.settings_db_label)
        layout.addRow("🎯 전략 DB:", self.strategies_db_label)
        layout.addRow("📈 시장데이터 DB:", self.market_data_db_label)

        parent_layout.addWidget(group)

    def _create_status_group(self, parent_layout):
        """데이터베이스 상태 그룹"""
        group = QGroupBox("🔍 데이터베이스 상태")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)

        # 상태 표시 라벨
        self.status_label = QLabel("상태 확인 중...")
        self.status_label.setStyleSheet("color: #666666; padding: 5px;")
        layout.addWidget(self.status_label)

        # 상태 새로고침 버튼
        refresh_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("🔃 상태 새로고침")
        self.refresh_btn.clicked.connect(self._refresh_status)
        refresh_layout.addWidget(self.refresh_btn)
        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)

        parent_layout.addWidget(group)

    def _create_management_group(self, parent_layout):
        """관리 기능 그룹"""
        group = QGroupBox("🔧 데이터베이스 관리")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 정보 텍스트
        info_text = QLabel(
            "💡 데이터베이스 파일 위치와 상태를 확인할 수 있습니다.\n"
            "고급 관리 기능은 추후 업데이트될 예정입니다."
        )
        info_text.setStyleSheet("color: #666666; font-size: 11px; padding: 10px;")
        info_text.setWordWrap(True)
        layout.addWidget(info_text)

        # 관리 버튼들
        button_layout = QHBoxLayout()

        self.validate_btn = QPushButton("✅ 데이터베이스 검증")
        self.validate_btn.clicked.connect(self._validate_databases)
        button_layout.addWidget(self.validate_btn)

        self.open_folder_btn = QPushButton("📂 폴더 열기")
        self.open_folder_btn.clicked.connect(self._open_data_folder)
        button_layout.addWidget(self.open_folder_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        parent_layout.addWidget(group)

    def _create_progress_section(self, parent_layout):
        """진행 상황 섹션"""
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        parent_layout.addWidget(line)

        # 진행 상황 표시
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #666666; font-size: 11px;")
        self.progress_label.setVisible(False)

        parent_layout.addWidget(self.progress_bar)
        parent_layout.addWidget(self.progress_label)

    def _connect_signals(self):
        """시그널 연결 - Presenter와 연결"""
        self.refresh_btn.clicked.connect(self.presenter.refresh_status)
        self.validate_btn.clicked.connect(self.presenter.validate_databases)
        self.open_folder_btn.clicked.connect(self.presenter.open_data_folder)

    # ISimpleDatabaseView 인터페이스 구현
    def display_database_info(self, info: Dict[str, str]) -> None:
        """데이터베이스 정보 표시"""
        self.settings_db_label.setText(info['settings_db'])
        self.strategies_db_label.setText(info['strategies_db'])
        self.market_data_db_label.setText(info['market_data_db'])

    def display_status(self, status: Dict) -> None:
        """상태 정보 표시"""
        self.status_label.setText(status['status_message'])

    def show_progress(self, message: str, value: int = 0) -> None:
        """진행상황 표시"""
        self.progress_label.setText(message)
        self.progress_bar.setValue(value)
        self.progress_label.setVisible(True)
        self.progress_bar.setVisible(True)

    def hide_progress(self) -> None:
        """진행상황 숨김"""
        self.progress_label.setVisible(False)
        self.progress_bar.setVisible(False)

    def show_validation_result(self, results: list) -> None:
        """검증 결과 표시"""
        result_text = "📋 데이터베이스 검증 결과:\n\n" + "\n".join(results)
        QMessageBox.information(self, "검증 완료", result_text)

    def show_error_message(self, title: str, message: str) -> None:
        """오류 메시지 표시"""
        QMessageBox.critical(self, title, message)

    def show_info_message(self, title: str, message: str) -> None:
        """정보 메시지 표시"""
        QMessageBox.information(self, title, message)

    # 공개 메서드들 (MVP 패턴으로 간소화)
    def refresh_display(self):
        """화면 새로고침"""
        self.presenter.load_database_info()

    def _load_current_settings(self):
        """현재 설정 로드"""
        try:
            self.logger.debug("📊 현재 데이터베이스 설정 로드 중...")

            # 데이터베이스 파일 경로 정보 표시
            settings_path = str(self.paths.SETTINGS_DB)
            strategies_path = str(self.paths.STRATEGIES_DB)
            market_data_path = str(self.paths.MARKET_DATA_DB)

            self.settings_db_label.setText(settings_path)
            self.strategies_db_label.setText(strategies_path)
            self.market_data_db_label.setText(market_data_path)

            # 파일 존재 여부 확인
            settings_exists = self.paths.SETTINGS_DB.exists()
            strategies_exists = self.paths.STRATEGIES_DB.exists()
            market_data_exists = self.paths.MARKET_DATA_DB.exists()

            # 상태 메시지 업데이트
            status_parts = []
            if settings_exists:
                status_parts.append("⚙️ 설정 DB: 연결됨")
            else:
                status_parts.append("⚙️ 설정 DB: 파일 없음")

            if strategies_exists:
                status_parts.append("🎯 전략 DB: 연결됨")
            else:
                status_parts.append("🎯 전략 DB: 파일 없음")

            if market_data_exists:
                status_parts.append("📈 시장데이터 DB: 연결됨")
            else:
                status_parts.append("📈 시장데이터 DB: 파일 없음")

            self.status_label.setText(" | ".join(status_parts))

            # 전체 상태 시그널 발생
            all_exists = settings_exists and strategies_exists and market_data_exists
            self.db_status_changed.emit(all_exists)

            self.logger.info("✅ 데이터베이스 설정 로드 완료")

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 설정 로드 실패: {e}")
            self.status_label.setText("❌ 설정 로드 실패")
            self.db_status_changed.emit(False)

    def _refresh_status(self):
        """상태 새로고침"""
        self.logger.info("🔃 데이터베이스 상태 새로고침")
        self._show_progress("상태 새로고침 중...")

        try:
            self._load_current_settings()
            self._show_progress("새로고침 완료", 100)

            QMessageBox.information(
                self,
                "새로고침 완료",
                "데이터베이스 상태가 새로고침되었습니다."
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "새로고침 실패",
                f"상태 새로고침 중 오류가 발생했습니다:\n{str(e)}"
            )
        finally:
            self._hide_progress()

    def _validate_databases(self):
        """데이터베이스 검증"""
        self.logger.info("✅ 데이터베이스 검증 시작")
        self._show_progress("데이터베이스 검증 중...")

        try:
            import sqlite3
            validation_results = []

            # 각 데이터베이스 파일 검증
            databases = [
                ("설정 DB", self.paths.SETTINGS_DB),
                ("전략 DB", self.paths.STRATEGIES_DB),
                ("시장데이터 DB", self.paths.MARKET_DATA_DB)
            ]

            for db_name, db_path in databases:
                if db_path.exists():
                    try:
                        # 간단한 연결 테스트
                        conn = sqlite3.connect(str(db_path))
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 5")
                        tables = cursor.fetchall()
                        conn.close()

                        table_count = len(tables)
                        validation_results.append(f"✅ {db_name}: 정상 ({table_count}개 테이블)")
                    except Exception as e:
                        validation_results.append(f"❌ {db_name}: 오류 - {str(e)}")
                else:
                    validation_results.append(f"⚠️ {db_name}: 파일 없음")

            # 결과 표시
            result_text = "📋 데이터베이스 검증 결과:\n\n" + "\n".join(validation_results)
            QMessageBox.information(self, "검증 완료", result_text)

            self.logger.info("✅ 데이터베이스 검증 완료")

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 검증 실패: {e}")
            QMessageBox.critical(
                self,
                "검증 실패",
                f"데이터베이스 검증 중 오류가 발생했습니다:\n{str(e)}"
            )
        finally:
            self._hide_progress()

    def _open_data_folder(self):
        """데이터 폴더 열기"""
        try:
            import os
            import subprocess
            import platform

            data_folder = self.paths.DATA_DIR

            if platform.system() == "Windows":
                os.startfile(str(data_folder))
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(data_folder)])
            else:  # Linux
                subprocess.run(["xdg-open", str(data_folder)])

            self.logger.info(f"📂 데이터 폴더 열기: {data_folder}")

        except Exception as e:
            self.logger.error(f"❌ 폴더 열기 실패: {e}")
            QMessageBox.warning(
                self,
                "폴더 열기 실패",
                f"데이터 폴더를 열 수 없습니다:\n{str(e)}"
            )

    def _show_progress(self, message: str, value: int = 0):
        """진행상황 표시"""
        self.progress_label.setText(message)
        self.progress_bar.setValue(value)
        self.progress_label.setVisible(True)
        self.progress_bar.setVisible(True)

    def _hide_progress(self):
        """진행상황 숨김"""
        self.progress_label.setVisible(False)
        self.progress_bar.setVisible(False)

    # 공개 메서드들
    def refresh_display(self):
        """화면 새로고침"""
        self._load_current_settings()

    def get_current_status(self):
        """현재 상태 반환"""
        return {
            'settings_db': str(self.paths.SETTINGS_DB),
            'strategies_db': str(self.paths.STRATEGIES_DB),
            'market_data_db': str(self.paths.MARKET_DATA_DB),
            'settings_exists': self.paths.SETTINGS_DB.exists(),
            'strategies_exists': self.paths.STRATEGIES_DB.exists(),
            'market_data_exists': self.paths.MARKET_DATA_DB.exists()
        }
