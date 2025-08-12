"""
Option B: 별도 다이얼로그 방식
버튼 클릭시 다이얼로그가 열리고 트리에서 컴포넌트 선택
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QDialog, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QGroupBox, QLineEdit, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from component_data import COMPONENT_TREE_DATA, search_components
from auto_generated_component_data import REAL_COMPONENT_TREE_DATA, search_real_components


class ComponentSelectorDialog(QDialog):
    """컴포넌트 선택 다이얼로그"""

    component_selected = pyqtSignal(str, str)  # (display_name, path)

    def __init__(self, parent=None, use_real_data=True):
        super().__init__(parent)
        self.setWindowTitle("🧩 컴포넌트 선택기 (실제 데이터!)" if use_real_data else "🧩 컴포넌트 선택기")
        self.setModal(True)
        self.resize(700, 700)  # 실제 데이터는 더 크게

        self.selected_name = ""
        self.selected_path = ""
        self.use_real_data = use_real_data

        self._setup_ui()
        self._populate_tree()

    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)

        # 설명
        desc_label = QLabel(
            "🎯 로깅 집중 대상 컴포넌트를 선택하세요.\n"
            "선택한 컴포넌트의 로그만 표시됩니다."
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # 검색 기능
        search_group = QGroupBox("🔍 검색")
        search_layout = QVBoxLayout(search_group)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("컴포넌트 이름 또는 경로로 검색...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)

        layout.addWidget(search_group)

        # 트리 위젯
        tree_group = QGroupBox("📁 컴포넌트 계층")
        tree_layout = QVBoxLayout(tree_group)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["컴포넌트", "경로"])
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree_widget.itemSelectionChanged.connect(self._on_selection_changed)
        tree_layout.addWidget(self.tree_widget)

        layout.addWidget(tree_group)

        # 선택 정보 표시
        info_group = QGroupBox("ℹ️ 선택 정보")
        info_layout = QVBoxLayout(info_group)

        self.info_display = QTextEdit()
        self.info_display.setMaximumHeight(100)
        self.info_display.setPlainText("컴포넌트를 선택해주세요.")
        info_layout.addWidget(self.info_display)

        layout.addWidget(info_group)

        # 버튼들
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)

        # OK 버튼 초기 비활성화
        self.ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setEnabled(False)

        layout.addWidget(button_box)

    def _populate_tree(self):
        """트리 데이터 채우기"""
        self.tree_widget.clear()

        # 데이터 소스 선택
        if self.use_real_data:
            data_source = REAL_COMPONENT_TREE_DATA
            print(f"🔍 실제 컴포넌트 로드 중... (총 {self._count_components(data_source)}개)")
        else:
            data_source = COMPONENT_TREE_DATA
            print("📝 테스트 컴포넌트 로드 중...")

        def _add_items(parent, data, level=0):
            for key, value in data.items():
                if isinstance(value, dict):
                    # 중간 노드 (카테고리)
                    item = QTreeWidgetItem(parent, [key, ""])
                    item.setData(0, Qt.ItemDataRole.UserRole, "")  # 경로 없음
                    # 🎨 카테고리는 회색으로 표시
                    item.setForeground(0, item.foreground(0).color().darker(150))
                    _add_items(item, value, level + 1)
                    # 🔧 실제 데이터는 기본적으로 접혀있게 (너무 많아서)
                    item.setExpanded(level < 1 if self.use_real_data else level < 2)
                else:
                    # 말단 노드 (실제 컴포넌트)
                    item = QTreeWidgetItem(parent, [key, value])
                    item.setData(0, Qt.ItemDataRole.UserRole, value)
                    # 🎨 실제 컴포넌트는 파란색으로 강조
                    from PyQt6.QtGui import QColor
                    item.setForeground(0, QColor(0, 100, 200))  # 파란색
                    item.setToolTip(0, f"✅ 선택 가능! 경로: {value}")

        _add_items(self.tree_widget, data_source)

        # 컬럼 크기 조정
        self.tree_widget.resizeColumnToContents(0)

    def _count_components(self, data):
        """컴포넌트 개수 세기"""
        count = 0
        for key, value in data.items():
            if isinstance(value, dict):
                count += self._count_components(value)
            else:
                count += 1
        return count

    def _on_search(self, query):
        """검색 기능"""
        if len(query) < 2:
            self._populate_tree()
            return

        # 검색 결과로 트리 업데이트
        self.tree_widget.clear()

        # 데이터 소스에 따른 검색 함수 선택
        if self.use_real_data:
            results = search_real_components(query)
        else:
            results = search_components(query)

        if results:
            search_root = QTreeWidgetItem(self.tree_widget, [f"🔍 검색 결과 ({len(results)}개)", ""])
            search_root.setData(0, Qt.ItemDataRole.UserRole, "")

            for display_name, path in results:
                item = QTreeWidgetItem(search_root, [display_name.replace(" > ", " → "), path])
                item.setData(0, Qt.ItemDataRole.UserRole, path)

            search_root.setExpanded(True)
        else:
            no_result = QTreeWidgetItem(self.tree_widget, ["❌ 검색 결과 없음", ""])
            no_result.setData(0, Qt.ItemDataRole.UserRole, "")

    def _on_selection_changed(self):
        """선택 변경시 정보 업데이트"""
        current_item = self.tree_widget.currentItem()
        if not current_item:
            return

        component_path = current_item.data(0, Qt.ItemDataRole.UserRole)

        if component_path:  # 실제 컴포넌트인 경우
            self.selected_name = current_item.text(0)
            self.selected_path = component_path

            info_text = f"""✅ 선택된 컴포넌트:

📝 이름: {self.selected_name}
📍 경로: {self.selected_path}

더블클릭하거나 OK 버튼을 클릭하여 선택을 확정하세요."""

            self.info_display.setPlainText(info_text)
            self.ok_button.setEnabled(True)
        else:
            # 카테고리 선택
            self.selected_name = ""
            self.selected_path = ""
            self.info_display.setPlainText("📁 카테고리가 선택되었습니다. 구체적인 컴포넌트를 선택해주세요.")
            self.ok_button.setEnabled(False)

    def _on_item_double_clicked(self, item, column):
        """아이템 더블클릭시 즉시 선택"""
        component_path = item.data(0, Qt.ItemDataRole.UserRole)
        if component_path:  # 실제 컴포넌트인 경우만
            self._on_accept()

    def _on_accept(self):
        """선택 확정"""
        if self.selected_path:
            self.component_selected.emit(self.selected_name, self.selected_path)
            self.accept()


class OptionBTestWidget(QWidget):
    """Option B 테스트 위젯"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Option B: 별도 다이얼로그 방식 테스트 (실제 데이터!)")
        self.setGeometry(200, 200, 700, 500)

        self.current_component = ""
        self.current_path = ""

        self._setup_ui()

    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)

        # 설명
        desc_group = QGroupBox("🛡️ 안전한 방법: 별도 다이얼로그 (실제 403개 컴포넌트!)")
        desc_layout = QVBoxLayout(desc_group)
        desc_label = QLabel(
            "버튼 클릭시 다이얼로그가 열립니다.\n"
            "실제 403개 컴포넌트를 검색 기능과 함께 선택 가능!\n"
            "회색=카테고리, 파란색=선택가능한 컴포넌트\n"
            "검색창에 'main', 'trading', 'logging' 등을 입력해보세요!"
        )
        desc_layout.addWidget(desc_label)
        layout.addWidget(desc_group)

        # 선택 영역
        select_group = QGroupBox("컴포넌트 선택")
        select_layout = QVBoxLayout(select_group)

        # 현재 선택 표시
        select_layout.addWidget(QLabel("현재 선택된 컴포넌트:"))

        self.current_display = QLabel("아직 선택되지 않음")
        self.current_display.setStyleSheet(
            "QLabel { background-color: #f0f0f0; padding: 8px; border: 1px solid #ccc; }"
        )
        select_layout.addWidget(self.current_display)

        # 선택 버튼
        select_btn = QPushButton("🧩 컴포넌트 선택...")
        select_btn.clicked.connect(self._open_selector_dialog)
        select_layout.addWidget(select_btn)

        layout.addWidget(select_group)

        # 결과 표시 영역
        result_group = QGroupBox("선택 결과")
        result_layout = QVBoxLayout(result_group)

        self.result_display = QTextEdit()
        self.result_display.setMaximumHeight(150)
        self.result_display.setPlainText("컴포넌트를 선택해주세요.")
        result_layout.addWidget(self.result_display)

        layout.addWidget(result_group)

        # 초기화 버튼
        reset_btn = QPushButton("초기화")
        reset_btn.clicked.connect(self._reset_selection)
        layout.addWidget(reset_btn)

    def _open_selector_dialog(self):
        """컴포넌트 선택 다이얼로그 열기"""
        dialog = ComponentSelectorDialog(self, use_real_data=True)  # 실제 데이터 사용
        dialog.component_selected.connect(self._on_component_selected)
        dialog.exec()

    def _on_component_selected(self, display_name, path):
        """컴포넌트 선택시 결과 표시"""
        self.current_component = display_name
        self.current_path = path

        # 현재 선택 업데이트
        self.current_display.setText(f"📍 {display_name}")

        # 결과 표시
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
        self.current_component = ""
        self.current_path = ""
        self.current_display.setText("아직 선택되지 않음")
        self.result_display.setPlainText("컴포넌트를 선택해주세요.")


def test_option_b():
    """Option B 테스트 실행"""
    app = QApplication(sys.argv)

    widget = OptionBTestWidget()
    widget.show()

    return app.exec()


if __name__ == "__main__":
    test_option_b()
