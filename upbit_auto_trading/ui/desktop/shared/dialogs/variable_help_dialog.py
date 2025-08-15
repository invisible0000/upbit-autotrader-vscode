"""
변수 도움말 다이얼로그 - 상세 가이드 표시
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QTextBrowser,
    QPushButton, QLabel, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.repositories.variable_help_repository import VariableHelpRepository


class VariableHelpDialog(QDialog):
    """변수 도움말 다이얼로그"""

    def __init__(self, variable_id: str, variable_name: str, parent=None):
        super().__init__(parent)
        self._logger = create_component_logger("VariableHelpDialog")
        self._help_repository = VariableHelpRepository()
        self._variable_id = variable_id
        self._variable_name = variable_name

        self._init_ui()
        self._load_help_content()

    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle(f"📖 {self._variable_name} 도움말")
        self.setModal(True)
        self.resize(800, 600)

        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # 헤더
        header_layout = QHBoxLayout()

        title_label = QLabel(f"📊 {self._variable_name} ({self._variable_id})")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        main_layout.addWidget(self.tab_widget)

        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("❌ 닫기")
        close_btn.setMinimumSize(100, 35)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        main_layout.addLayout(button_layout)

    def _load_help_content(self):
        """도움말 내용 로드"""
        try:
            # DB에서 도움말 문서들 가져오기
            help_documents = self._help_repository.get_variable_help_documents(self._variable_id)

            if not help_documents:
                self._add_no_help_tab()
                return

            # 카테고리별로 그룹화
            categories = {}
            for doc in help_documents:
                category = doc.get('help_category', 'general')
                if category not in categories:
                    categories[category] = []
                categories[category].append(doc)

            # 카테고리 순서 정의
            category_order = ['concept', 'usage', 'advanced', 'examples', 'tips', 'warnings', 'general']
            category_names = {
                'concept': '📖 기본 개념',
                'usage': '🎯 활용 방법',
                'advanced': '🔧 고급 기법',
                'examples': '💡 사용 예시',
                'tips': '💫 팁 & 노하우',
                'warnings': '⚠️ 주의사항',
                'general': '📋 일반 정보'
            }

            # 카테고리별 탭 생성
            for category in category_order:
                if category in categories:
                    tab_name = category_names.get(category, category.title())
                    self._add_help_tab(tab_name, categories[category])

            # 기타 카테고리들
            for category, documents in categories.items():
                if category not in category_order:
                    tab_name = category_names.get(category, category.title())
                    self._add_help_tab(tab_name, documents)

            self._logger.info(f"도움말 로드 완료: {self._variable_id}, {len(categories)}개 카테고리")

        except Exception as e:
            self._logger.error(f"도움말 로드 실패: {e}")
            self._add_error_tab(str(e))

    def _add_help_tab(self, tab_name: str, documents: list):
        """도움말 탭 추가"""
        # 스크롤 가능한 위젯
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 내용 위젯
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(20)

        # 문서들을 순서대로 추가
        sorted_docs = sorted(documents, key=lambda x: x.get('display_order', 999))

        for doc in sorted_docs:
            section_widget = self._create_section_widget(doc)
            content_layout.addWidget(section_widget)

        content_layout.addStretch()
        scroll_area.setWidget(content_widget)

        self.tab_widget.addTab(scroll_area, tab_name)

    def _create_section_widget(self, document: dict) -> QWidget:
        """섹션 위젯 생성"""
        section_widget = QWidget()
        section_layout = QVBoxLayout(section_widget)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(10)

        # 제목
        title = document.get('title_ko', document.get('title_en', '제목 없음'))
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            QLabel {
                color: #34495e;
                padding: 8px 0px;
                border-bottom: 2px solid #ecf0f1;
                margin-bottom: 10px;
            }
        """)
        section_layout.addWidget(title_label)

        # 내용
        content = document.get('content_ko', document.get('content_en', '내용 없음'))
        content_browser = QTextBrowser()
        content_browser.setMaximumHeight(300)
        content_browser.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 12px;
                background-color: #fafafa;
                font-size: 11pt;
                line-height: 1.4;
            }
        """)

        # Markdown 기본 지원
        content_browser.setMarkdown(content)

        section_layout.addWidget(content_browser)

        return section_widget

    def _add_no_help_tab(self):
        """도움말 없음 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        no_help_label = QLabel("📝 아직 도움말이 작성되지 않았습니다.")
        no_help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_help_label.setStyleSheet("""
            QLabel {
                font-size: 14pt;
                color: #7f8c8d;
                padding: 40px;
            }
        """)

        layout.addWidget(no_help_label)

        self.tab_widget.addTab(widget, "📋 정보 없음")

    def _add_error_tab(self, error_message: str):
        """오류 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        error_label = QLabel(f"❌ 도움말 로드 중 오류가 발생했습니다:\n{error_message}")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setWordWrap(True)
        error_label.setStyleSheet("""
            QLabel {
                font-size: 12pt;
                color: #e74c3c;
                padding: 40px;
                background-color: #fdf2f2;
                border: 1px solid #f5c6cb;
                border-radius: 6px;
            }
        """)

        layout.addWidget(error_label)

        self.tab_widget.addTab(widget, "❌ 오류")
