"""
Option A: QComboBox + QTreeWidget 방식
콤보박스 드롭다운을 트리 위젯으로 변경하여 계층적 선택 제공
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QTreeWidget, QTreeWidgetItem,
    QPushButton, QTextEdit, QGroupBox, QLineEdit,
    QTreeWidgetItemIterator
)
from PyQt6.QtCore import Qt, pyqtSignal

from component_data import COMPONENT_TREE_DATA
from auto_generated_component_data import REAL_COMPONENT_TREE_DATA


class ComponentTreeWidget(QTreeWidget):
    """트리 위젯을 콤보박스용으로 커스터마이징 (개선된 버전)"""

    component_selected = pyqtSignal(str, str)  # (display_name, path)

    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)  # 헤더 숨김
        self.setRootIsDecorated(True)  # 트리 구조 표시
        self.setAlternatingRowColors(True)  # 교대로 색상 표시

        # 🔧 추가 설정으로 사용성 개선
        self.setIndentation(20)  # 들여쓰기 깊이
        self.setUniformRowHeights(True)  # 행 높이 통일
        self.setAnimated(True)  # 확장/축소 애니메이션

        # 🔧 선택 동작 개선
        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)

        # 데이터 소스 선택 (실제 데이터 vs 테스트 데이터)
        self.use_real_data = True  # 실제 컴포넌트 데이터 사용

        # 데이터 로드
        self._populate_tree()

        # 시그널 연결 (더블클릭과 단일클릭 모두 지원)
        self.itemClicked.connect(self._on_item_clicked)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    def _populate_tree(self):
        """트리 데이터 채우기"""
        self.clear()

        # 데이터 소스 선택
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
                    # 중간 노드 (폴더) - 카테고리
                    item.setData(0, Qt.ItemDataRole.UserRole, "")  # 경로 없음
                    # 🔧 폴더 아이템은 비활성화 (선택 불가)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                    # 🎨 폴더는 회색으로 표시
                    item.setForeground(0, item.foreground(0).color().darker(150))
                    _add_items(item, value)
                    # 🔧 실제 데이터는 기본적으로 접혀있게 (너무 많아서)
                    item.setExpanded(not self.use_real_data)
                else:
                    # 말단 노드 (실제 컴포넌트) - 선택 가능!
                    item.setData(0, Qt.ItemDataRole.UserRole, value)
                    # 🔧 툴팁 추가로 전체 경로 표시
                    item.setToolTip(0, f"✅ 선택 가능! 경로: {value}")
                    # 🎨 실제 컴포넌트는 파란색으로 강조
                    from PyQt6.QtGui import QColor
                    item.setForeground(0, QColor(0, 100, 200))  # 파란색

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
        """아이템 클릭시 처리 (단일 클릭)"""
        self._handle_item_selection(item)

    def _on_item_double_clicked(self, item, column):
        """아이템 더블클릭시 처리"""
        self._handle_item_selection(item)

    def _handle_item_selection(self, item):
        """아이템 선택 공통 처리"""
        component_path = item.data(0, Qt.ItemDataRole.UserRole)
        if component_path:  # 실제 컴포넌트인 경우만
            display_name = item.text(0)
            print(f"🔍 DEBUG: 선택된 컴포넌트 - {display_name} : {component_path}")  # 디버그
            self.component_selected.emit(display_name, component_path)

    def filter_tree(self, search_text: str):
        """트리 필터링 (검색 기능)"""
        search_text = search_text.lower().strip()

        if not search_text:
            # 검색어가 없으면 모든 아이템 표시
            self._show_all_items()
            return

        # 모든 아이템 숨기기
        self._hide_all_items()

        # 검색어와 일치하는 아이템과 그 부모들 표시
        self._show_matching_items(search_text)

    def _show_all_items(self):
        """모든 아이템 표시"""
        iterator = QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            item.setHidden(False)
            iterator += 1

    def _hide_all_items(self):
        """모든 아이템 숨기기"""
        iterator = QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            item.setHidden(True)
            iterator += 1

    def _show_matching_items(self, search_text: str):
        """검색어와 일치하는 아이템들과 그 부모들 표시"""
        iterator = QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            item_text = item.text(0).lower()
            component_path = item.data(0, Qt.ItemDataRole.UserRole)

            # 텍스트나 경로에 검색어가 포함되면 표시
            if (search_text in item_text or
                    (component_path and search_text in component_path.lower())):

                # 해당 아이템과 모든 부모 아이템들 표시
                current_item = item
                while current_item:
                    current_item.setHidden(False)
                    current_item = current_item.parent()

            iterator += 1
class TreeComboBox(QComboBox):
    """트리 뷰를 사용하는 콤보박스 (개선된 버전)"""

    component_selected = pyqtSignal(str, str)  # (display_name, path)

    def __init__(self):
        super().__init__()

        # 🔧 중요: 에디터블 설정을 먼저 해야 함
        self.setEditable(True)
        self.setCurrentText("컴포넌트 선택...")

        # 트리 위젯 생성 및 설정
        self.tree_widget = ComponentTreeWidget()

        # 🔧 트리 위젯 크기 설정
        self.tree_widget.setMinimumWidth(400)
        self.tree_widget.setMinimumHeight(300)

        # 🎯 핵심: 콤보박스 뷰를 트리로 변경
        self.setView(self.tree_widget)

        # 시그널 연결 (뷰 설정 후에 연결!)
        self.tree_widget.component_selected.connect(self._on_component_selected)

        # 🔧 추가: 폰트 설정으로 가독성 향상
        font = self.font()
        font.setPointSize(10)
        self.setFont(font)
        self.tree_widget.setFont(font)

    def _on_component_selected(self, display_name, path):
        """컴포넌트 선택시 처리"""
        print(f"🔍 DEBUG: TreeComboBox에서 받은 시그널 - {display_name} : {path}")  # 디버그
        # 콤보박스 텍스트 업데이트
        self.setCurrentText(display_name)
        self.hidePopup()  # 드롭다운 닫기

        # 외부로 시그널 전달
        self.component_selected.emit(display_name, path)

    def showPopup(self):
        """팝업 표시시 트리 확장 상태 보장"""
        super().showPopup()
        # 🔧 팝업 표시 후 모든 아이템 확장
        self.tree_widget.expandAll()


class OptionATestWidget(QWidget):
    """Option A 테스트 위젯"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Option A: QComboBox + QTreeWidget 테스트")
        self.setGeometry(100, 100, 600, 400)

        self._setup_ui()

    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)

        # 설명
        desc_group = QGroupBox("🔥 혁신적 방법: 콤보박스 + 트리뷰 (실제 데이터!)")
        desc_layout = QVBoxLayout(desc_group)
        desc_label = QLabel(
            "일반 콤보박스처럼 보이지만 드롭다운이 트리 구조!\n"
            "실제 403개 컴포넌트를 계층적으로 선택 가능합니다.\n\n"
            "📖 사용법:\n"
            "• 회색 텍스트 = 카테고리 (선택 불가)\n"
            "• 파란색 텍스트 = 실제 컴포넌트 (클릭하여 선택!)\n"
            "• Presentation Layer, Infrastructure Layer 등을 펼쳐보세요!\n"
            "• 🏠 Main Window, 💰 Live Trading Screen 등을 클릭해보세요!"
        )
        desc_layout.addWidget(desc_label)
        layout.addWidget(desc_group)

        # 콤보박스 영역
        combo_group = QGroupBox("컴포넌트 선택")
        combo_layout = QVBoxLayout(combo_group)

        # 라벨
        combo_layout.addWidget(QLabel("컴포넌트 집중:"))

        # 트리 콤보박스
        self.tree_combo = TreeComboBox()
        self.tree_combo.component_selected.connect(self._on_component_selected)
        combo_layout.addWidget(self.tree_combo)

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
        print(f"🔍 DEBUG: 메인 위젯에서 받은 시그널 - {display_name} : {path}")  # 디버그
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
        self.tree_combo.setCurrentText("컴포넌트 선택...")
        self.result_display.setPlainText("아직 선택된 컴포넌트가 없습니다.")


def test_option_a():
    """Option A 테스트 실행"""
    app = QApplication(sys.argv)

    widget = OptionATestWidget()
    widget.show()

    return app.exec()


if __name__ == "__main__":
    test_option_a()
