"""
전략 메이커 메인 윈도우
Strategy Maker Main Window

드래그 앤 드롭 방식의 비주얼 전략 빌더 UI
"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QScrollArea, QLabel, QPushButton, QFrame, QButtonGroup,
    QTabWidget, QTextEdit, QTreeWidget, QTreeWidgetItem, QListWidget,
    QListWidgetItem, QGroupBox, QFormLayout, QLineEdit, QSpinBox, 
    QDoubleSpinBox, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal, QSize
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPainter, QFont, QColor, QIcon
from typing import Dict, Any, List, Optional
import json

from upbit_auto_trading.component_system.triggers import (
    TRIGGER_CLASSES, TRIGGER_CATEGORIES, get_trigger_metadata
)


class ComponentPalette(QWidget):
    """컴포넌트 팔레트 - 드래그 가능한 컴포넌트들"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_components()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("컴포넌트 팔레트")
        title.setFont(QFont("맑은 고딕", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 카테고리 탭
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        self.setLayout(layout)
    
    def load_components(self):
        """컴포넌트들을 카테고리별로 로드"""
        
        # 트리거 카테고리
        for category, triggers in TRIGGER_CATEGORIES.items():
            category_names = {
                'price': '가격 기반',
                'indicator': '지표 기반',
                'time': '시간 기반',
                'volume': '거래량 기반'
            }
            
            # 카테고리 탭 생성
            tab = QScrollArea()
            tab_widget = QWidget()
            tab_layout = QVBoxLayout()
            
            # 각 트리거를 버튼으로 생성
            for trigger_type in triggers:
                metadata = get_trigger_metadata(trigger_type)
                if metadata:
                    button = ComponentButton(
                        trigger_type,
                        metadata.get('display_name', trigger_type),
                        metadata.get('description', ''),
                        'trigger'
                    )
                    tab_layout.addWidget(button)
            
            tab_layout.addStretch()
            tab_widget.setLayout(tab_layout)
            tab.setWidget(tab_widget)
            tab.setWidgetResizable(True)
            
            self.tab_widget.addTab(tab, category_names.get(category, category))


class ComponentButton(QPushButton):
    """드래그 가능한 컴포넌트 버튼"""
    
    def __init__(self, component_type: str, display_name: str, description: str, category: str):
        super().__init__(display_name)
        self.component_type = component_type
        self.display_name = display_name
        self.description = description
        self.category = category
        
        # 스타일 설정
        self.setMinimumHeight(50)
        self.setToolTip(description)
        self.setup_style()
        
    def setup_style(self):
        """버튼 스타일 설정"""
        style = """
        ComponentButton {
            background-color: #f0f0f0;
            border: 2px solid #d0d0d0;
            border-radius: 8px;
            padding: 8px;
            text-align: left;
            font-weight: bold;
        }
        ComponentButton:hover {
            background-color: #e0e0ff;
            border-color: #b0b0ff;
        }
        ComponentButton:pressed {
            background-color: #d0d0ff;
        }
        """
        self.setStyleSheet(style)
    
    def mousePressEvent(self, event):
        """마우스 프레스 이벤트 - 드래그 시작"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """마우스 무브 이벤트 - 드래그 수행"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        
        if ((event.pos() - self.drag_start_position).manhattanLength() 
            < QApplication.startDragDistance()):
            return
        
        # 드래그 데이터 생성
        drag_data = {
            'type': self.category,
            'component_type': self.component_type,
            'display_name': self.display_name,
            'description': self.description
        }
        
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(json.dumps(drag_data))
        drag.setMimeData(mime_data)
        
        # 드래그 실행
        drag.exec(Qt.DropAction.CopyAction)


class StrategyCanvas(QWidget):
    """전략 캔버스 - 컴포넌트들을 배치하는 영역"""
    
    componentAdded = pyqtSignal(dict)  # 컴포넌트 추가 시그널
    
    def __init__(self):
        super().__init__()
        self.components = []  # 배치된 컴포넌트들
        self.connections = []  # 컴포넌트 간 연결
        self.setup_ui()
    
    def setup_ui(self):
        """UI 설정"""
        self.setAcceptDrops(True)
        self.setMinimumSize(800, 600)
        
        # 배경 스타일
        self.setStyleSheet("""
        StrategyCanvas {
            background-color: white;
            border: 2px dashed #cccccc;
            border-radius: 8px;
        }
        """)
        
        # 레이아웃
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("여기에 컴포넌트를 드래그하여 전략을 구성하세요"))
        self.setLayout(self.layout)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """드래그 진입 이벤트"""
        if event.mimeData().hasText():
            try:
                data = json.loads(event.mimeData().text())
                if data.get('type') in ['trigger', 'action', 'condition']:
                    event.acceptProposedAction()
            except json.JSONDecodeError:
                pass
    
    def dropEvent(self, event: QDropEvent):
        """드롭 이벤트"""
        try:
            data = json.loads(event.mimeData().text())
            self.add_component(data, event.pos())
            event.acceptProposedAction()
        except json.JSONDecodeError:
            pass
    
    def add_component(self, component_data: dict, position):
        """컴포넌트 추가"""
        component_widget = StrategyComponentWidget(component_data)
        component_widget.move(position)
        component_widget.setParent(self)
        component_widget.show()
        
        self.components.append({
            'widget': component_widget,
            'data': component_data,
            'position': position
        })
        
        self.componentAdded.emit(component_data)
    
    def clear_canvas(self):
        """캔버스 클리어"""
        for component in self.components:
            component['widget'].deleteLater()
        self.components.clear()
        self.connections.clear()


class StrategyComponentWidget(QFrame):
    """전략 캔버스에 배치된 컴포넌트 위젯"""
    
    def __init__(self, component_data: dict):
        super().__init__()
        self.component_data = component_data
        self.setup_ui()
    
    def setup_ui(self):
        """UI 설정"""
        self.setFixedSize(150, 100)
        self.setFrameStyle(QFrame.Shape.Box)
        
        layout = QVBoxLayout()
        
        # 컴포넌트 이름
        name_label = QLabel(self.component_data.get('display_name', ''))
        name_label.setFont(QFont("맑은 고딕", 9, QFont.Weight.Bold))
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # 컴포넌트 타입
        type_label = QLabel(self.component_data.get('type', ''))
        type_label.setFont(QFont("맑은 고딕", 8))
        type_label.setStyleSheet("color: #666666;")
        layout.addWidget(type_label)
        
        self.setLayout(layout)
        
        # 스타일 설정
        colors = {
            'trigger': '#ffebee',    # 연한 빨강
            'action': '#e8f5e8',     # 연한 녹색
            'condition': '#fff3e0'   # 연한 주황
        }
        
        component_type = self.component_data.get('type', 'trigger')
        bg_color = colors.get(component_type, '#f5f5f5')
        
        self.setStyleSheet(f"""
        StrategyComponentWidget {{
            background-color: {bg_color};
            border: 2px solid #cccccc;
            border-radius: 8px;
            padding: 5px;
        }}
        StrategyComponentWidget:hover {{
            border-color: #4CAF50;
        }}
        """)


class ConfigPanel(QWidget):
    """설정 패널 - 선택된 컴포넌트의 설정"""
    
    def __init__(self):
        super().__init__()
        self.current_component = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("컴포넌트 설정")
        title.setFont(QFont("맑은 고딕", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 설정 영역
        self.config_area = QScrollArea()
        self.config_widget = QWidget()
        self.config_layout = QFormLayout()
        self.config_widget.setLayout(self.config_layout)
        self.config_area.setWidget(self.config_widget)
        self.config_area.setWidgetResizable(True)
        
        layout.addWidget(self.config_area)
        
        # 기본 메시지
        self.show_default_message()
        
        self.setLayout(layout)
    
    def show_default_message(self):
        """기본 메시지 표시"""
        self.clear_config()
        label = QLabel("컴포넌트를 선택하세요")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.config_layout.addRow(label)
    
    def clear_config(self):
        """설정 영역 클리어"""
        while self.config_layout.count():
            child = self.config_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def load_component_config(self, component_data: dict):
        """컴포넌트 설정 로드"""
        self.current_component = component_data
        self.clear_config()
        
        # 컴포넌트 정보 표시
        self.config_layout.addRow("이름:", QLabel(component_data.get('display_name', '')))
        self.config_layout.addRow("타입:", QLabel(component_data.get('type', '')))
        self.config_layout.addRow("설명:", QLabel(component_data.get('description', '')))
        
        # TODO: 실제 설정 필드들 동적 생성
        # 지금은 임시로 기본 필드들만 표시
        if component_data.get('type') == 'trigger':
            self.add_trigger_config_fields(component_data)
    
    def add_trigger_config_fields(self, component_data: dict):
        """트리거 설정 필드 추가"""
        component_type = component_data.get('component_type', '')
        
        if component_type == 'price_change':
            self.config_layout.addRow("변화율(%):", QDoubleSpinBox())
            self.config_layout.addRow("기준가격:", QComboBox())


class StrategyMakerWindow(QMainWindow):
    """전략 메이커 메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """UI 초기화"""
        self.setWindowTitle("업비트 자동매매 전략 메이커")
        self.setGeometry(100, 100, 1400, 900)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 좌측 패널 (컴포넌트 팔레트)
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        left_panel.setMaximumWidth(300)
        left_layout = QVBoxLayout()
        
        self.component_palette = ComponentPalette()
        left_layout.addWidget(self.component_palette)
        
        left_panel.setLayout(left_layout)
        main_layout.addWidget(left_panel)
        
        # 중앙 영역 (전략 캔버스)
        self.strategy_canvas = StrategyCanvas()
        main_layout.addWidget(self.strategy_canvas)
        
        # 우측 패널 (설정 및 미리보기)
        right_panel = QFrame()
        right_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        right_panel.setMaximumWidth(350)
        right_layout = QVBoxLayout()
        
        # 설정 패널
        self.config_panel = ConfigPanel()
        right_layout.addWidget(self.config_panel)
        
        # 전략 미리보기
        preview_group = QGroupBox("전략 미리보기")
        preview_layout = QVBoxLayout()
        self.strategy_preview = QTextEdit()
        self.strategy_preview.setMaximumHeight(200)
        self.strategy_preview.setPlainText("전략이 구성되면 여기에 표시됩니다")
        preview_layout.addWidget(self.strategy_preview)
        preview_group.setLayout(preview_layout)
        right_layout.addWidget(preview_group)
        
        # 액션 버튼들
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("전략 저장")
        self.load_button = QPushButton("전략 불러오기")
        self.test_button = QPushButton("백테스트")
        self.clear_button = QPushButton("초기화")
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.test_button)
        button_layout.addWidget(self.clear_button)
        
        right_layout.addLayout(button_layout)
        right_panel.setLayout(right_layout)
        main_layout.addWidget(right_panel)
    
    def setup_connections(self):
        """시그널 연결"""
        self.strategy_canvas.componentAdded.connect(self.on_component_added)
        self.clear_button.clicked.connect(self.strategy_canvas.clear_canvas)
        self.save_button.clicked.connect(self.save_strategy)
        self.load_button.clicked.connect(self.load_strategy)
        self.test_button.clicked.connect(self.test_strategy)
    
    def on_component_added(self, component_data: dict):
        """컴포넌트 추가 시 호출"""
        self.config_panel.load_component_config(component_data)
        self.update_strategy_preview()
    
    def update_strategy_preview(self):
        """전략 미리보기 업데이트"""
        components = self.strategy_canvas.components
        if not components:
            self.strategy_preview.setPlainText("전략이 구성되면 여기에 표시됩니다")
            return
        
        preview_text = "구성된 전략:\n\n"
        for i, comp in enumerate(components, 1):
            data = comp['data']
            preview_text += f"{i}. {data.get('display_name', '')}\n"
            preview_text += f"   - 타입: {data.get('type', '')}\n"
            preview_text += f"   - 설명: {data.get('description', '')}\n\n"
        
        self.strategy_preview.setPlainText(preview_text)
    
    def save_strategy(self):
        """전략 저장"""
        print("전략 저장 (미구현)")
    
    def load_strategy(self):
        """전략 불러오기"""
        print("전략 불러오기 (미구현)")
    
    def test_strategy(self):
        """전략 백테스트"""
        print("백테스트 실행 (미구현)")


def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    
    # 앱 설정
    app.setApplicationName("업비트 자동매매 전략 메이커")
    app.setApplicationVersion("1.0.0")
    
    # 메인 윈도우 생성 및 표시
    window = StrategyMakerWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
