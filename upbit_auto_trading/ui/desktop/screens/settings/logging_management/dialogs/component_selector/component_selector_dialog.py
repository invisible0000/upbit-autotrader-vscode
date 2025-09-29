"""
컴포넌트 선택 다이얼로그

로깅 component_focus 설정을 위한 독립적인 다이얼로그입니다.
실제 프로젝트의 컴포넌트들을 스캔하여 선택할 수 있습니다.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QGroupBox, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QPushButton, QDialogButtonBox
)

# Application Layer - Infrastructure 의존성 격리 (Phase 2 수정)

try:
    from .component_data_scanner import ComponentDataScanner, get_real_component_data, get_real_component_data_hierarchical
except ImportError:
    # 스캐너 오류시에도 다이얼로그는 동작하도록 fallback
    ComponentDataScanner = None
    get_real_component_data = None
    get_real_component_data_hierarchical = None
    get_real_component_data = None


class ComponentSelectorDialog(QDialog):
    """컴포넌트 선택 다이얼로그"""

    component_selected = pyqtSignal(str, str)  # (display_name, module_path)

    def __init__(self, parent=None, logging_service=None):
        super().__init__(parent)

        # 로깅
        if logging_service:
            self.logger = logging_service.get_component_logger("ComponentSelectorDialog")
        else:
            raise ValueError("ComponentSelectorDialog에 logging_service가 주입되지 않았습니다")

        # 다이얼로그 설정
        self.setWindowTitle("🧩 컴포넌트 선택기")
        self.setModal(True)
        self.resize(900, 700)  # 더 큰 초기 크기
        self.setMinimumSize(700, 500)  # 최소 크기 설정

        # 크기 조정 가능하게 설정
        self.setSizeGripEnabled(True)

        # 선택된 컴포넌트 정보
        self.selected_name = ""
        self.selected_path = ""

        # UI 구성
        self._setup_ui()
        self._populate_tree()

        self.logger.info("🧩 컴포넌트 선택 다이얼로그 초기화 완료")

    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)

        # 설명
        desc_label = QLabel(
            "🎯 로깅 집중 대상 컴포넌트를 선택하세요.\n"
            "선택한 컴포넌트의 로그만 표시됩니다."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc_label)

        # 검색 기능
        search_group = QGroupBox("🔍 검색")
        search_layout = QVBoxLayout(search_group)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("컴포넌트 이름 또는 경로로 검색...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)

        layout.addWidget(search_group, 0)  # stretch factor 0: 고정 크기

        # 트리 위젯
        tree_group = QGroupBox("📁 컴포넌트 계층")
        tree_layout = QVBoxLayout(tree_group)

        # 트리 제어 버튼들
        tree_controls_layout = QHBoxLayout()

        expand_all_button = QPushButton("📖 모두 펼치기")
        expand_all_button.setToolTip("모든 트리 항목을 펼칩니다")
        expand_all_button.clicked.connect(self._expand_all)
        tree_controls_layout.addWidget(expand_all_button)

        collapse_all_button = QPushButton("📕 모두 접기")
        collapse_all_button.setToolTip("모든 트리 항목을 접습니다")
        collapse_all_button.clicked.connect(self._collapse_all)
        tree_controls_layout.addWidget(collapse_all_button)

        expand_to_depth_button = QPushButton("📗 2단계까지")
        expand_to_depth_button.setToolTip("최상위 2단계까지만 펼칩니다")
        expand_to_depth_button.clicked.connect(self._expand_to_depth)
        tree_controls_layout.addWidget(expand_to_depth_button)

        tree_controls_layout.addStretch()  # 오른쪽 공간 확보
        tree_layout.addLayout(tree_controls_layout)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["컴포넌트", "모듈 경로"])
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.setRootIsDecorated(True)
        self.tree_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree_widget.itemSelectionChanged.connect(self._on_selection_changed)

        # 열 너비 조정
        self.tree_widget.setColumnWidth(0, 300)

        tree_layout.addWidget(self.tree_widget)
        layout.addWidget(tree_group, 1)  # stretch factor 1: 확장 가능

        # 선택 정보 표시
        info_group = QGroupBox("ℹ️ 선택 정보")
        info_layout = QVBoxLayout(info_group)

        self.info_display = QTextEdit()
        # 6라인 정도 표시 가능하도록 최대 높이 설정
        font_metrics = self.info_display.fontMetrics()
        line_height = font_metrics.lineSpacing()
        max_lines = 6
        max_height = line_height * max_lines + 20  # 여백 추가
        self.info_display.setMaximumHeight(max_height)
        self.info_display.setMinimumHeight(60)  # 최소 높이도 설정
        self.info_display.setPlainText("컴포넌트를 선택해주세요.")
        self.info_display.setReadOnly(True)
        info_layout.addWidget(self.info_display)

        layout.addWidget(info_group, 0)  # stretch factor 0: 고정 크기

        # 추가 버튼
        clear_layout = QHBoxLayout()

        self.clear_button = QPushButton("🗑️ 선택 해제")
        self.clear_button.clicked.connect(self._clear_selection)
        clear_layout.addWidget(self.clear_button)

        clear_layout.addStretch()
        layout.addLayout(clear_layout, 0)  # stretch factor 0: 고정 크기

        # 다이얼로그 버튼
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box, 0)  # stretch factor 0: 고정 크기

    def _populate_tree(self):
        """트리 데이터 구성"""
        self.tree_widget.clear()

        try:
            if get_real_component_data_hierarchical is not None:
                # 계층적 실제 컴포넌트 데이터 사용
                component_data = get_real_component_data_hierarchical()
                self.logger.info(f"📊 계층적 컴포넌트 데이터 로드: {len(component_data)}개 계층")
                self._populate_hierarchical_tree(component_data)
            elif get_real_component_data is not None:
                # 기본 실제 컴포넌트 데이터 사용
                component_data = get_real_component_data()
                self.logger.info(f"📊 기본 컴포넌트 데이터 로드: {len(component_data)}개 계층")
                self._populate_flat_tree(component_data)
            else:
                # Fallback 데이터 사용
                component_data = self._get_fallback_component_data()
                self.logger.warning("⚠️ Fallback 컴포넌트 데이터 사용")
                self._populate_flat_tree(component_data)

        except Exception as e:
            self.logger.error(f"❌ 컴포넌트 데이터 로드 실패: {e}")
            # 에러시 기본 데이터로 fallback
            self._populate_fallback_data()

    def _populate_hierarchical_tree(self, data, parent_item=None):
        """계층적 데이터로 트리 구성"""
        for key, value in data.items():
            if isinstance(value, dict):
                # 폴더/계층인 경우
                if parent_item is None:
                    folder_item = QTreeWidgetItem(self.tree_widget, [key, ""])
                else:
                    folder_item = QTreeWidgetItem(parent_item, [key, ""])
                folder_item.setExpanded(True)

                # 재귀적으로 하위 항목 추가
                self._populate_hierarchical_tree(value, folder_item)
            else:
                # 실제 컴포넌트인 경우
                if parent_item is None:
                    comp_item = QTreeWidgetItem(self.tree_widget, [key, str(value)])
                else:
                    comp_item = QTreeWidgetItem(parent_item, [key, str(value)])
                comp_item.setData(0, Qt.ItemDataRole.UserRole, str(value))

    def _populate_flat_tree(self, component_data):
        """기본 플랫 데이터로 트리 구성"""
        for layer_name, components in component_data.items():
            if not components:  # 빈 계층은 건너뛰기
                continue

            layer_item = QTreeWidgetItem(self.tree_widget, [layer_name, ""])
            layer_item.setExpanded(True)

            for comp_name, comp_path in components.items():
                comp_item = QTreeWidgetItem(layer_item, [comp_name, comp_path])
                comp_item.setData(0, Qt.ItemDataRole.UserRole, comp_path)

    def _get_fallback_component_data(self):
        """스캐너 실패시 사용할 기본 컴포넌트 데이터"""
        return {
            "🎨 Presentation Layer": {
                "🏠 MainWindow": "upbit_auto_trading.ui.desktop.main_window",
                "🔧 LoggingSettingsWidget": "upbit_auto_trading.ui.desktop.screens.settings.logging_management.widgets.logging_settings_widget",
                "📊 EnvironmentProfileView": "upbit_auto_trading.ui.desktop.screens.settings.environment_profile.environment_profile_view",
                "🔧 DatabaseSettingsView": "upbit_auto_trading.ui.desktop.screens.settings.database_settings.database_settings_view",
            },
            "🚀 Application Layer": {
                "⚙️ LoggingConfigManager": "upbit_auto_trading.application.services.config.logging_config_manager",
                "⚙️ DatabaseConfigService": "upbit_auto_trading.application.services.database_config_service",
            },
            "🧠 Domain Layer": {
                "🔧 Strategy": "upbit_auto_trading.domain.entities.strategy",
                "🔧 TriggerCondition": "upbit_auto_trading.domain.entities.trigger_condition",
            },
            "🔧 Infrastructure Layer": {
                "🔧 DatabaseManager": "upbit_auto_trading.infrastructure.database.database_manager",
                "🔧 LoggingSystem": "upbit_auto_trading.infrastructure.logging",
            }
        }

    def _populate_fallback_data(self):
        """에러시 기본 데이터로 트리 구성"""
        self.tree_widget.clear()
        fallback_data = self._get_fallback_component_data()

        for layer_name, components in fallback_data.items():
            layer_item = QTreeWidgetItem(self.tree_widget, [layer_name, ""])
            layer_item.setExpanded(True)

            for comp_name, comp_path in components.items():
                comp_item = QTreeWidgetItem(layer_item, [comp_name, comp_path])
                comp_item.setData(0, Qt.ItemDataRole.UserRole, comp_path)

    def _on_search(self, text):
        """검색 필터링"""
        self._filter_tree(text.lower().strip())

    def _filter_tree(self, search_text):
        """트리 필터링"""
        if not search_text:
            # 검색어가 없으면 모든 항목 표시
            self._show_all_items()
            return

        # 모든 항목 숨기기
        self._hide_all_items()

        # 검색 조건에 맞는 항목만 표시
        for i in range(self.tree_widget.topLevelItemCount()):
            layer_item = self.tree_widget.topLevelItem(i)
            layer_has_matches = False

            for j in range(layer_item.childCount()):
                comp_item = layer_item.child(j)
                comp_name = comp_item.text(0).lower()
                comp_path = comp_item.text(1).lower()

                if search_text in comp_name or search_text in comp_path:
                    comp_item.setHidden(False)
                    layer_has_matches = True

            layer_item.setHidden(not layer_has_matches)
            if layer_has_matches:
                layer_item.setExpanded(True)

    def _show_all_items(self):
        """모든 항목 표시"""
        for i in range(self.tree_widget.topLevelItemCount()):
            layer_item = self.tree_widget.topLevelItem(i)
            layer_item.setHidden(False)
            for j in range(layer_item.childCount()):
                layer_item.child(j).setHidden(False)

    def _hide_all_items(self):
        """모든 항목 숨기기"""
        for i in range(self.tree_widget.topLevelItemCount()):
            layer_item = self.tree_widget.topLevelItem(i)
            for j in range(layer_item.childCount()):
                layer_item.child(j).setHidden(True)

    def _on_item_double_clicked(self, item, column):
        """항목 더블클릭시 선택하고 다이얼로그 닫기"""
        if item.parent() is not None:  # 컴포넌트 항목인 경우만
            self.accept()

    def _on_selection_changed(self):
        """선택 변경시 정보 업데이트"""
        current_item = self.tree_widget.currentItem()
        if current_item and current_item.parent() is not None:
            # 이모티콘 제거하여 순수한 컴포넌트명 추출
            raw_name = current_item.text(0)
            self.selected_name = self._clean_component_name(raw_name)
            self.selected_path = current_item.text(1)

            info_text = "📋 선택된 컴포넌트:\n"
            info_text += f"• 표시 이름: {raw_name}\n"
            info_text += f"• 컴포넌트명: {self.selected_name}\n"
            info_text += f"• 경로: {self.selected_path}\n\n"
            info_text += "이 컴포넌트의 로그만 표시됩니다."

            self.info_display.setPlainText(info_text)
        else:
            self.selected_name = ""
            self.selected_path = ""
            self.info_display.setPlainText("컴포넌트를 선택해주세요.")

    def _clear_selection(self):
        """선택 해제"""
        self.tree_widget.clearSelection()
        self.selected_name = ""
        self.selected_path = ""
        self.info_display.setPlainText("전체 컴포넌트의 로그를 표시합니다.")

    def _clean_component_name(self, raw_name):
        """컴포넌트명에서 이모티콘과 불필요한 공백 제거"""
        import re
        # 이모티콘 패턴 제거 (유니코드 이모티콘 범위)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"  # dingbats
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE
        )

        cleaned = emoji_pattern.sub('', raw_name)
        # 앞뒤 공백 제거
        cleaned = cleaned.strip()

        return cleaned

    def get_selected_component(self):
        """선택된 컴포넌트 반환"""
        return self.selected_name, self.selected_path

    def _expand_all(self):
        """모든 트리 항목 펼치기"""
        self.logger.debug("모든 트리 항목 펼치기")
        self.tree_widget.expandAll()

    def _collapse_all(self):
        """모든 트리 항목 접기"""
        self.logger.debug("모든 트리 항목 접기")
        self.tree_widget.collapseAll()

    def _expand_to_depth(self):
        """지정된 깊이까지만 펼치기 (최상위 2레벨)"""
        self.logger.debug("2단계 깊이까지 트리 펼치기")
        self.tree_widget.collapseAll()  # 먼저 모두 접기
        self.tree_widget.expandToDepth(1)  # 2레벨까지 펼치기 (0: 첫번째, 1: 두번째)
