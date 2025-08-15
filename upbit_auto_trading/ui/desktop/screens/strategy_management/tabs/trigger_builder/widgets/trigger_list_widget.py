"""
트리거 리스트 위젯 - Legacy UI 기반 MVP 구현
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QLabel, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("TriggerListWidget")


class TriggerListWidget(QWidget):
    """트리거 리스트 위젯 - MVP 패턴"""

    # 시그널 정의
    trigger_selected = pyqtSignal(object, int)  # item, column
    trigger_edited = pyqtSignal()
    trigger_deleted = pyqtSignal()
    trigger_copied = pyqtSignal()
    trigger_save_requested = pyqtSignal()
    new_trigger_requested = pyqtSignal()
    edit_mode_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_edit_mode = False
        self.temp_triggers = []
        self.setup_ui()
        self.load_initial_data()

    def setup_ui(self):
        """UI 구성"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 검색 영역
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍")
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("트리거 검색...")
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # 트리거 트리 위젯
        self.trigger_tree = QTreeWidget()
        self.trigger_tree.setHeaderLabels(["트리거명", "변수", "조건"])
        self.trigger_tree.setRootIsDecorated(False)
        self.trigger_tree.setIndentation(0)

        # 헤더 설정
        header = self.trigger_tree.header()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
            header.setStretchLastSection(False)

        # 초기 열 너비
        self.trigger_tree.setColumnWidth(0, 150)
        self.trigger_tree.setColumnWidth(1, 100)
        self.trigger_tree.setColumnWidth(2, 120)

        # 시그널 연결
        self.trigger_tree.itemClicked.connect(self.on_trigger_selected)
        self.search_input.textChanged.connect(self.filter_triggers)

        main_layout.addWidget(self.trigger_tree)

        # 버튼 영역
        self.create_button_area(main_layout)

    def create_button_area(self, parent_layout):
        """버튼 영역 생성"""
        button_layout = QHBoxLayout()

        # 저장 버튼
        self.save_btn = QPushButton("💾 트리거 저장")
        self.save_btn.clicked.connect(self.save_current_condition)
        button_layout.addWidget(self.save_btn)

        # 신규 버튼
        self.new_btn = QPushButton("📝 신규")
        self.new_btn.clicked.connect(self.create_new_trigger)
        button_layout.addWidget(self.new_btn)

        # 복사 버튼
        self.copy_btn = QPushButton("📄 복사")
        self.copy_btn.clicked.connect(self.copy_trigger)
        button_layout.addWidget(self.copy_btn)

        # 편집 버튼
        self.edit_btn = QPushButton("✏️ 편집")
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        button_layout.addWidget(self.edit_btn)

        # 삭제 버튼
        self.delete_btn = QPushButton("🗑️ 삭제")
        self.delete_btn.clicked.connect(self.delete_trigger)
        button_layout.addWidget(self.delete_btn)

        parent_layout.addLayout(button_layout)

    def load_initial_data(self):
        """초기 데이터 로드"""
        # 임시 샘플 데이터
        sample_triggers = [
            {"name": "RSI 과매도 진입", "variable": "RSI", "condition": "< 30"},
            {"name": "이동평균 돌파", "variable": "MA20", "condition": "> 현재가"},
            {"name": "거래량 급증", "variable": "Volume", "condition": "> 평균 2배"},
        ]

        for trigger in sample_triggers:
            self.add_trigger_to_tree(trigger)

        logger.info(f"초기 트리거 {len(sample_triggers)}개 로드 완료")

    def add_trigger_to_tree(self, trigger_data):
        """트리거를 트리에 추가"""
        item = QTreeWidgetItem(self.trigger_tree)
        item.setText(0, trigger_data.get("name", ""))
        item.setText(1, trigger_data.get("variable", ""))
        item.setText(2, trigger_data.get("condition", ""))
        item.setData(0, Qt.ItemDataRole.UserRole, trigger_data)

    def on_trigger_selected(self, item, column):
        """트리거 선택 처리"""
        if item:
            self.trigger_selected.emit(item, column)
            logger.debug(f"트리거 선택: {item.text(0)}")

    def filter_triggers(self, text):
        """트리거 필터링"""
        if not text:
            # 빈 텍스트면 모든 아이템 표시
            for i in range(self.trigger_tree.topLevelItemCount()):
                item = self.trigger_tree.topLevelItem(i)
                if item:
                    item.setHidden(False)
            return

        for i in range(self.trigger_tree.topLevelItemCount()):
            item = self.trigger_tree.topLevelItem(i)
            if item:
                visible = (text.lower() in item.text(0).lower()
                          or text.lower() in item.text(1).lower()
                          or text.lower() in item.text(2).lower())
                item.setHidden(not visible)

    def save_current_condition(self):
        """현재 조건 저장"""
        self.trigger_save_requested.emit()
        logger.debug("트리거 저장 요청")

    def create_new_trigger(self):
        """새 트리거 생성"""
        self.new_trigger_requested.emit()
        logger.debug("새 트리거 생성 요청")

    def copy_trigger(self):
        """트리거 복사"""
        current_item = self.trigger_tree.currentItem()
        if current_item:
            self.trigger_copied.emit()
            logger.debug(f"트리거 복사: {current_item.text(0)}")

    def toggle_edit_mode(self):
        """편집 모드 토글"""
        self.is_edit_mode = not self.is_edit_mode
        self.edit_mode_changed.emit(self.is_edit_mode)

        if self.is_edit_mode:
            self.edit_btn.setText("✅ 완료")
        else:
            self.edit_btn.setText("✏️ 편집")

        logger.debug(f"편집 모드: {self.is_edit_mode}")

    def delete_trigger(self):
        """트리거 삭제"""
        current_item = self.trigger_tree.currentItem()
        if current_item:
            index = self.trigger_tree.indexOfTopLevelItem(current_item)
            self.trigger_tree.takeTopLevelItem(index)
            self.trigger_deleted.emit()
            logger.debug(f"트리거 삭제: {current_item.text(0)}")
