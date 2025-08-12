"""
Option A Fixed: 가짜 콤보박스 + 트리뷰 방식
실제 콤보박스처럼 보이지만 내부적으로는 버튼 + 팝업 트리뷰로 구현
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QGroupBox, QFrame, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from component_data import COMPONENT_TREE_DATA
from auto_generated_component_data import REAL_COMPONENT_TREE_DATA


class FakeComboTreeWidget(QWidget):
    """콤보박스처럼 보이는 가짜 콤보박스 + 트리뷰"""

    component_selected = pyqtSignal(str, str)  # (display_name, path)

    def __init__(self):
        super().__init__()
        self.use_real_data = True
        self.selected_text = "컴포넌트 선택..."
        self.popup_widget = None
        self.tree_widget = None

        self._setup_ui()

    def _setup_ui(self):
        """UI 설정"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 가짜 콤보박스 버튼 (진짜 콤보박스처럼 보이게)
        self.combo_button = QPushButton(self.selected_text)
        self.combo_button.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 5px 25px 5px 5px;
                border: 1px solid #ccc;
                background: white;
                min-height: 20px;
            }
            QPushButton:hover {
                border: 1px solid #0078d4;
            }
            QPushButton:pressed {
                background: #f0f0f0;
            }
        """)

        # 드롭다운 화살표 추가
        arrow_label = QLabel("▼")
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow_label.setFixedWidth(20)
        arrow_label.setStyleSheet("""
            QLabel {
                border: none;
                background: transparent;
                color: #666;
            }
        """)

        # 버튼과 화살표를 겹치게 배치
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(self.combo_button, 1)

        # 화살표를 버튼 위에 겹치게
        arrow_frame = QFrame()
        arrow_frame.setLayout(QHBoxLayout())
        arrow_frame.layout().setContentsMargins(0, 0, 5, 0)
        arrow_frame.layout().addStretch()
        arrow_frame.layout().addWidget(arrow_label)
        arrow_frame.setFixedHeight(self.combo_button.sizeHint().height())

        layout.addWidget(self.combo_button)

        # 시그널 연결
        self.combo_button.clicked.connect(self._toggle_popup)

    def _toggle_popup(self):
        """팝업 토글"""
        if self.popup_widget and self.popup_widget.isVisible():
            self.popup_widget.hide()
        else:
            self._show_popup()

    def _show_popup(self):
        """트리뷰 팝업 표시"""
        if not self.popup_widget:
            self._create_popup()

        # 버튼 아래에 팝업 위치 설정
        button_rect = self.combo_button.geometry()
        global_pos = self.combo_button.mapToGlobal(button_rect.bottomLeft())

        self.popup_widget.move(global_pos)
        self.popup_widget.resize(400, 300)
        self.popup_widget.show()
        self.popup_widget.raise_()
        self.popup_widget.activateWindow()

    def _create_popup(self):
        """팝업 위젯 생성"""
        self.popup_widget = QWidget(None, Qt.WindowType.Popup)
        self.popup_widget.setWindowTitle("컴포넌트 선택")

        layout = QVBoxLayout(self.popup_widget)

        # 검색창
        search_box = QLineEdit()
        search_box.setPlaceholderText("컴포넌트 검색... (예: main, trading, logging)")
        search_box.textChanged.connect(self._on_search_changed)
        layout.addWidget(search_box)

        # 트리뷰
        self.tree_widget = ComponentTreeWidget(use_real_data=self.use_real_data)
        self.tree_widget.component_selected.connect(self._on_component_selected)
        layout.addWidget(self.tree_widget)

        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.popup_widget.hide)
        layout.addWidget(close_btn)

    def _on_search_changed(self, text):
        """검색 텍스트 변경"""
        if self.tree_widget:
            self.tree_widget.filter_tree(text)

    def _on_component_selected(self, display_name, path):
        """컴포넌트 선택시 처리"""
        self.selected_text = display_name
        self.combo_button.setText(display_name)
        self.popup_widget.hide()

        # 외부로 시그널 전달
        self.component_selected.emit(display_name, path)


class ComponentTreeWidget(QTreeWidget):
    """트리 위젯 (Option B에서 사용하는 것과 동일)"""

    component_selected = pyqtSignal(str, str)  # (display_name, path)

    def __init__(self, use_real_data=True):
        super().__init__()
        self.use_real_data = use_real_data

        self.setHeaderHidden(True)
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(True)
        self.setIndentation(20)
        self.setUniformRowHeights(True)
        self.setAnimated(True)

        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)

        self._populate_tree()
        self.itemClicked.connect(self._on_item_clicked)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    def _populate_tree(self):
        """트리 데이터 채우기"""
        self.clear()

        if self.use_real_data:
            data_source = REAL_COMPONENT_TREE_DATA
            print(f"🔍 실제 컴포넌트 로드 중... (총 {self._count_components(data_source)}개)")
        else:
            data_source = COMPONENT_TREE_DATA
            print("📝 테스트 컴포넌트 로드 중...")

        def _add_items(parent, data):
            for key, value in data.items():
                item = QTreeWidgetItem(parent, [key])

                if isinstance(value, dict):
                    # 중간 노드 (카테고리)
                    item.setData(0, Qt.ItemDataRole.UserRole, "")
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                    item.setForeground(0, item.foreground(0).color().darker(150))
                    _add_items(item, value)
                    item.setExpanded(not self.use_real_data)
                else:
                    # 말단 노드 (실제 컴포넌트)
                    item.setData(0, Qt.ItemDataRole.UserRole, value)
                    item.setToolTip(0, f"✅ 선택 가능! 경로: {value}")
                    item.setForeground(0, QColor(0, 100, 200))

        _add_items(self, data_source)

    def _count_components(self, data):
        """컴포넌트 개수 세기"""
        count = 0
        for key, value in data.items():
            if isinstance(value, dict):
                count += self._count_components(value)
            else:
                count += 1
        return count

    def _on_item_clicked(self, item, column):
        """아이템 클릭시 처리"""
        self._handle_item_selection(item)

    def _on_item_double_clicked(self, item, column):
        """아이템 더블클릭시 처리"""
        self._handle_item_selection(item)

    def _handle_item_selection(self, item):
        """아이템 선택 공통 처리"""
        component_path = item.data(0, Qt.ItemDataRole.UserRole)
        if component_path:
            display_name = item.text(0)
            print(f"🔍 DEBUG: 선택된 컴포넌트 - {display_name} : {component_path}")
            self.component_selected.emit(display_name, component_path)

    def filter_tree(self, search_text: str):
        """트리 필터링 (간단한 버전)"""
        search_text = search_text.lower().strip()

        # 간단한 반복으로 모든 아이템 처리
        def filter_item(item):
            if search_text:
                item_text = item.text(0).lower()
                component_path = item.data(0, Qt.ItemDataRole.UserRole)

                # 검색어와 일치하는지 확인
                matches = (search_text in item_text or
                           (component_path and search_text in component_path.lower()))

                # 실제 컴포넌트인 경우만 숨김 처리
                if component_path:  # 실제 컴포넌트
                    item.setHidden(not matches)
                else:  # 카테고리는 항상 표시
                    item.setHidden(False)
            else:
                item.setHidden(False)

            # 자식 아이템들도 처리
            for i in range(item.childCount()):
                filter_item(item.child(i))

        # 루트 아이템들부터 시작
        for i in range(self.topLevelItemCount()):
            filter_item(self.topLevelItem(i))


class OptionAFixedTestWidget(QWidget):
    """Option A Fixed 테스트 위젯"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Option A Fixed: 가짜 콤보박스 + 트리뷰 테스트")
        self.setGeometry(100, 100, 600, 400)

        self._setup_ui()

    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)

        # 설명
        desc_group = QGroupBox("🔥 Option A Fixed: 가짜 콤보박스 + 트리뷰 (실제 데이터!)")
        desc_layout = QVBoxLayout(desc_group)
        desc_label = QLabel(
            "진짜 콤보박스처럼 보이지만 클릭하면 트리뷰 팝업이 나타납니다!\n"
            "실제 403개 컴포넌트를 검색과 함께 선택 가능합니다.\n\n"
            "📖 사용법:\n"
            "• 콤보박스 클릭 → 트리뷰 팝업 → 검색 & 선택\n"
            "• 회색=카테고리, 파란색=선택가능한 컴포넌트\n"
            "• 검색창에 'main', 'trading' 등을 입력해보세요!"
        )
        desc_layout.addWidget(desc_label)
        layout.addWidget(desc_group)

        # 콤보박스 영역
        combo_group = QGroupBox("컴포넌트 선택")
        combo_layout = QVBoxLayout(combo_group)

        combo_layout.addWidget(QLabel("컴포넌트 집중:"))

        # 가짜 콤보박스
        self.fake_combo = FakeComboTreeWidget()
        self.fake_combo.component_selected.connect(self._on_component_selected)
        combo_layout.addWidget(self.fake_combo)

        layout.addWidget(combo_group)

        # 결과 표시 영역
        result_group = QGroupBox("선택 결과")
        result_layout = QVBoxLayout(result_group)

        self.result_display = QTextEdit()
        self.result_display.setMaximumHeight(150)
        self.result_display.setPlainText("아직 선택된 컴포넌트가 없습니다.")
        result_layout.addWidget(self.result_display)

        layout.addWidget(result_group)

        # 초기화 버튼
        reset_btn = QPushButton("초기화")
        reset_btn.clicked.connect(self._reset_selection)
        layout.addWidget(reset_btn)

    def _on_component_selected(self, display_name, path):
        """컴포넌트 선택시 결과 표시"""
        result_text = f"""✅ 컴포넌트 선택됨!

📝 표시명: {display_name}
📍 전체 경로: {path}

🎯 logging_config.yaml에 설정될 값:
component_focus: "{path}"

이 설정으로 해당 컴포넌트의 로그만 집중적으로 표시됩니다.
"""
        self.result_display.setPlainText(result_text)

    def _reset_selection(self):
        """선택 초기화"""
        self.fake_combo.selected_text = "컴포넌트 선택..."
        self.fake_combo.combo_button.setText("컴포넌트 선택...")
        self.result_display.setPlainText("아직 선택된 컴포넌트가 없습니다.")


def test_option_a_fixed():
    """Option A Fixed 테스트 실행"""
    app = QApplication(sys.argv)

    widget = OptionAFixedTestWidget()
    widget.show()

    return app.exec()


if __name__ == "__main__":
    test_option_a_fixed()
