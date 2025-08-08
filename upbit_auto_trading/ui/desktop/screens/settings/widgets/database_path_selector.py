"""
Database Path Selector Widget

데이터베이스 파일 경로 선택을 위한 전용 UI 위젯입니다.
MVP 패턴에 따라 Presenter와 연동되어 파일 선택 및 경로 검증을 수행합니다.

Features:
- 파일 경로 입력 및 브라우저 버튼
- 실시간 경로 검증 및 피드백
- 테마 시스템 완전 통합
"""

from typing import Dict
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QFrame
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

from upbit_auto_trading.infrastructure.logging import create_component_logger


class DatabasePathSelector(QWidget):
    """
    데이터베이스 파일 경로 선택 위젯

    사용자가 데이터베이스 파일 경로를 선택하고 검증할 수 있습니다.
    """

    # 경로 변경 시그널
    path_changed = pyqtSignal(str, str)  # database_type, new_path

    # 경로 검증 요청 시그널
    path_validation_requested = pyqtSignal(str, str)  # database_type, path

    def __init__(self, database_type: str, display_name: str, parent=None):
        super().__init__(parent)
        self.setObjectName(f"widget-path-selector-{database_type}")
        self._logger = create_component_logger("DatabasePathSelector")

        self.database_type = database_type
        self.display_name = display_name
        self._current_path = ""
        self._is_valid = False

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # 라벨
        label = QLabel(self.display_name)
        label_font = QFont()
        label_font.setBold(True)
        label.setFont(label_font)
        layout.addWidget(label)

        # 경로 입력 섹션
        path_layout = QHBoxLayout()
        path_layout.setSpacing(8)

        # 경로 입력 필드
        self.path_edit = QLineEdit()
        self.path_edit.setObjectName(f"edit-path-{self.database_type}")
        self.path_edit.setPlaceholderText("📁 데이터베이스 파일 경로를 입력하거나 찾아보기 버튼을 클릭하세요")
        path_layout.addWidget(self.path_edit, 1)

        # 브라우저 버튼
        self.browse_button = QPushButton("📁 찾아보기")
        self.browse_button.setObjectName(f"btn-browse-{self.database_type}")
        path_layout.addWidget(self.browse_button)

        layout.addLayout(path_layout)

        # 상태 표시 라벨
        self.status_label = QLabel("")
        self.status_label.setObjectName(f"label-status-{self.database_type}")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

    def _connect_signals(self):
        """시그널 연결"""
        self.path_edit.textChanged.connect(self._on_path_changed)
        self.browse_button.clicked.connect(self._on_browse_clicked)

    def _on_path_changed(self, text: str):
        """경로 변경 시 처리"""
        self._current_path = text.strip()

        if self._current_path:
            # 기본 검증
            self._validate_path_basic()

            # 상세 검증 요청
            self.path_validation_requested.emit(self.database_type, self._current_path)
        else:
            self._clear_status()

        # 경로 변경 시그널 발생
        self.path_changed.emit(self.database_type, self._current_path)

    def _on_browse_clicked(self):
        """파일 브라우저 버튼 클릭 시 처리"""
        dialog = QFileDialog()

        # 현재 경로가 있으면 해당 디렉토리에서 시작
        start_dir = ""
        if self._current_path:
            start_dir = str(Path(self._current_path).parent)

        file_path, _ = dialog.getOpenFileName(
            self,
            f"{self.display_name} 파일 선택",
            start_dir,
            "SQLite 파일 (*.sqlite3 *.sqlite *.db);;모든 파일 (*)"
        )

        if file_path:
            self.path_edit.setText(file_path)

    def _validate_path_basic(self):
        """기본적인 경로 검증"""
        if not self._current_path:
            return

        path_obj = Path(self._current_path)

        if not path_obj.exists():
            self._set_status("⚠️ 파일이 존재하지 않습니다", False)
            return

        if not path_obj.is_file():
            self._set_status("❌ 올바른 파일이 아닙니다", False)
            return

        # 파일 크기 체크
        try:
            size_mb = path_obj.stat().st_size / (1024 * 1024)
            self._set_status(f"📁 파일 크기: {size_mb:.1f}MB", True)
        except Exception as e:
            self._set_status(f"❌ 파일 정보 읽기 실패: {str(e)}", False)

    def _set_status(self, message: str, is_valid: bool):
        """상태 메시지 설정"""
        self._is_valid = is_valid
        self.status_label.setText(message)

        # 스타일 적용
        if is_valid:
            self.status_label.setStyleSheet("color: #2d5a2d;")
            self.path_edit.setStyleSheet("border: 2px solid #4CAF50;")
        else:
            self.status_label.setStyleSheet("color: #8b2635;")
            self.path_edit.setStyleSheet("border: 2px solid #f44336;")

    def _clear_status(self):
        """상태 초기화"""
        self._is_valid = False
        self.status_label.setText("")
        self.path_edit.setStyleSheet("")

    def set_validation_result(self, is_valid: bool, message: str):
        """외부 검증 결과 설정"""
        self._set_status(message, is_valid)

    def get_path(self) -> str:
        """현재 경로 반환"""
        return self._current_path

    def set_path(self, path: str):
        """경로 설정 (프로그래밍적 설정 - 시그널 발생 방지)"""
        # 시그널 일시 차단
        self.path_edit.blockSignals(True)
        self.path_edit.setText(path)
        self._current_path = path.strip()
        # 시그널 차단 해제
        self.path_edit.blockSignals(False)

        # 기본 검증만 수행 (시그널 없이)
        if self._current_path:
            self._validate_path_basic()

    def is_valid(self) -> bool:
        """경로 유효성 여부 반환"""
        return self._is_valid

    def clear(self):
        """입력 내용 초기화"""
        self.path_edit.clear()
        self._clear_status()


class DatabasePathSelectorGroup(QWidget):
    """
    여러 데이터베이스 경로 선택기를 그룹으로 관리하는 위젯
    """

    # 전체 검증 상태 변경 시그널
    validation_changed = pyqtSignal(bool)  # all_valid

    # 경로 변경 시그널
    path_changed = pyqtSignal(str, str)  # database_type, new_path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("widget-path-selector-group")
        self._logger = create_component_logger("DatabasePathSelectorGroup")

        self._selectors: Dict[str, DatabasePathSelector] = {}
        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 제목
        title_label = QLabel("📁 데이터베이스 파일 경로")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 데이터베이스별 선택기
        db_configs = [
            ("settings", "⚙️ Settings Database"),
            ("strategies", "📈 Strategies Database"),
            ("market_data", "📊 Market Data Database")
        ]

        for db_type, display_name in db_configs:
            selector = DatabasePathSelector(db_type, display_name)
            selector.path_changed.connect(self._on_path_changed)
            selector.path_validation_requested.connect(self._on_validation_requested)

            self._selectors[db_type] = selector
            layout.addWidget(selector)

    def _on_path_changed(self, database_type: str, new_path: str):
        """경로 변경 시 처리"""
        self.path_changed.emit(database_type, new_path)
        self._check_validation_state()

    def _on_validation_requested(self, database_type: str, path: str):
        """검증 요청 처리"""
        # TODO: Presenter를 통한 실제 검증 로직 연결
        self._logger.debug(f"검증 요청: {database_type} -> {path}")

    def _check_validation_state(self):
        """전체 검증 상태 확인"""
        all_valid = all(selector.is_valid() for selector in self._selectors.values())
        self.validation_changed.emit(all_valid)

    def get_paths(self) -> Dict[str, str]:
        """모든 경로 반환"""
        return {db_type: selector.get_path() for db_type, selector in self._selectors.items()}

    def set_paths(self, paths: Dict[str, str]):
        """경로들 설정"""
        for db_type, path in paths.items():
            if db_type in self._selectors:
                self._selectors[db_type].set_path(path)

    def set_validation_result(self, database_type: str, is_valid: bool, message: str):
        """검증 결과 설정"""
        if database_type in self._selectors:
            self._selectors[database_type].set_validation_result(is_valid, message)
            self._check_validation_state()

    def clear_all(self):
        """모든 입력 초기화"""
        for selector in self._selectors.values():
            selector.clear()

    def is_all_valid(self) -> bool:
        """모든 경로가 유효한지 확인"""
        return all(selector.is_valid() for selector in self._selectors.values())
