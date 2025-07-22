"""
드래그앤드롭 vs (+)버튼 방식 비교 실험
UX 유용성 검증을 위한 직접 비교 도구
"""

import sys
import json
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from typing import List, Dict, Any

class TriggerItem:
    """트리거 항목"""
    def __init__(self, name: str, icon: str, category: str, description: str):
        self.name = name
        self.icon = icon
        self.category = category
        self.description = description

class DragDropTriggerWidget(QLabel):
    """드래그 가능한 트리거 위젯"""
    
    def __init__(self, trigger_item: TriggerItem):
        super().__init__()
        self.trigger_item = trigger_item
        self.setup_ui()
    
    def setup_ui(self):
        self.setText(f"{self.trigger_item.icon} {self.trigger_item.name}")
        self.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                border: 2px solid #2196f3;
                border-radius: 8px;
                padding: 8px 12px;
                margin: 2px;
                font-weight: bold;
                color: #1976d2;
                cursor: move;
            }
            QLabel:hover {
                background-color: #bbdefb;
                border-color: #1976d2;
                transform: scale(1.05);
            }
        """)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFixedHeight(40)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 드래그 시작
            drag = QDrag(self)
            mime_data = QMimeData()
            
            # 트리거 데이터를 JSON으로 직렬화
            trigger_data = {
                'name': self.trigger_item.name,
                'icon': self.trigger_item.icon,
                'category': self.trigger_item.category,
                'description': self.trigger_item.description
            }
            mime_data.setText(json.dumps(trigger_data))
            drag.setMimeData(mime_data)
            
            # 드래그 이미지 설정
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())
            
            # 드래그 실행
            drop_action = drag.exec(Qt.DropAction.CopyAction)

class DropZoneWidget(QWidget):
    """드롭 영역 위젯"""
    
    trigger_added = pyqtSignal(dict)  # 트리거 추가 신호
    
    def __init__(self, title: str):
        super().__init__()
        self.title = title
        self.triggers = []
        self.setup_ui()
        
    def setup_ui(self):
        self.setAcceptDrops(True)
        self.setMinimumSize(300, 200)
        
        layout = QVBoxLayout()
        
        # 제목
        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 트리거 목록 영역
        self.triggers_area = QWidget()
        self.triggers_layout = QVBoxLayout()
        self.triggers_area.setLayout(self.triggers_layout)
        
        scroll = QScrollArea()
        scroll.setWidget(self.triggers_area)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # 안내 텍스트
        self.hint_label = QLabel("📦 트리거를 여기로 드래그하세요")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setStyleSheet("""
            QLabel {
                color: #999;
                font-style: italic;
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 20px;
                background-color: #f9f9f9;
            }
        """)
        layout.addWidget(self.hint_label)
        
        self.setLayout(layout)
        self.update_hint_visibility()
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet("background-color: #e8f5e8; border: 2px dashed #4caf50;")
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("")
    
    def dropEvent(self, event):
        if event.mimeData().hasText():
            try:
                trigger_data = json.loads(event.mimeData().text())
                self.add_trigger(trigger_data)
                event.acceptProposedAction()
                
                # 드롭 효과 애니메이션
                self.show_drop_effect()
                
            except json.JSONDecodeError:
                pass
        
        self.setStyleSheet("")
    
    def add_trigger(self, trigger_data: Dict[str, Any]):
        """트리거 추가"""
        self.triggers.append(trigger_data)
        
        # 트리거 위젯 생성
        trigger_widget = QWidget()
        trigger_layout = QHBoxLayout()
        
        # 트리거 정보
        info_label = QLabel(f"{trigger_data['icon']} {trigger_data['name']}")
        info_label.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
        """)
        
        # 삭제 버튼
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(30, 30)
        delete_btn.clicked.connect(lambda: self.remove_trigger(trigger_widget, trigger_data))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffebee;
                border: 1px solid #f44336;
                border-radius: 15px;
                color: #f44336;
            }
            QPushButton:hover {
                background-color: #f44336;
                color: white;
            }
        """)
        
        trigger_layout.addWidget(info_label)
        trigger_layout.addWidget(delete_btn)
        trigger_widget.setLayout(trigger_layout)
        
        self.triggers_layout.addWidget(trigger_widget)
        self.trigger_added.emit(trigger_data)
        self.update_hint_visibility()
    
    def remove_trigger(self, widget: QWidget, trigger_data: Dict[str, Any]):
        """트리거 제거"""
        if trigger_data in self.triggers:
            self.triggers.remove(trigger_data)
        
        widget.deleteLater()
        self.update_hint_visibility()
    
    def update_hint_visibility(self):
        """힌트 표시/숨김 업데이트"""
        self.hint_label.setVisible(len(self.triggers) == 0)
    
    def show_drop_effect(self):
        """드롭 효과 애니메이션"""
        effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(effect)
        
        self.fade_animation = QPropertyAnimation(effect, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.5)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.finished.connect(lambda: self.setGraphicsEffect(None))
        self.fade_animation.start()

class ButtonBasedTriggerWidget(QWidget):
    """버튼 기반 트리거 추가 위젯"""
    
    trigger_added = pyqtSignal(dict)
    
    def __init__(self, title: str, available_triggers: List[TriggerItem]):
        super().__init__()
        self.title = title
        self.available_triggers = available_triggers
        self.triggers = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 제목과 추가 버튼
        header_layout = QHBoxLayout()
        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        
        add_btn = QPushButton("➕ 트리거 추가")
        add_btn.clicked.connect(self.show_trigger_selection)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(add_btn)
        layout.addLayout(header_layout)
        
        # 트리거 목록
        self.triggers_area = QWidget()
        self.triggers_layout = QVBoxLayout()
        self.triggers_area.setLayout(self.triggers_layout)
        
        scroll = QScrollArea()
        scroll.setWidget(self.triggers_area)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # 안내 텍스트
        self.hint_label = QLabel("🔘 '트리거 추가' 버튼을 클릭하세요")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setStyleSheet("""
            QLabel {
                color: #999;
                font-style: italic;
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 20px;
                background-color: #f9f9f9;
            }
        """)
        layout.addWidget(self.hint_label)
        
        self.setLayout(layout)
        self.setMinimumSize(300, 200)
        self.update_hint_visibility()
    
    def show_trigger_selection(self):
        """트리거 선택 다이얼로그 표시"""
        dialog = QDialog(self)
        dialog.setWindowTitle("🎯 트리거 선택")
        dialog.resize(400, 500)
        
        layout = QVBoxLayout()
        
        # 카테고리별 트리거 목록
        categories = {}
        for trigger in self.available_triggers:
            if trigger.category not in categories:
                categories[trigger.category] = []
            categories[trigger.category].append(trigger)
        
        # 탭 위젯으로 카테고리 분리
        tab_widget = QTabWidget()
        
        for category, triggers in categories.items():
            tab = QWidget()
            tab_layout = QVBoxLayout()
            
            for trigger in triggers:
                btn = QPushButton(f"{trigger.icon} {trigger.name}")
                btn.setToolTip(trigger.description)
                btn.clicked.connect(lambda checked, t=trigger: self.add_trigger_from_button(t, dialog))
                btn.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        padding: 12px;
                        margin: 2px;
                        border: 1px solid #ddd;
                        border-radius: 6px;
                        background-color: white;
                    }
                    QPushButton:hover {
                        background-color: #e3f2fd;
                        border-color: #2196f3;
                    }
                """)
                tab_layout.addWidget(btn)
            
            tab_layout.addStretch()
            tab.setLayout(tab_layout)
            tab_widget.addTab(tab, category)
        
        layout.addWidget(tab_widget)
        
        # 취소 버튼
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(dialog.close)
        layout.addWidget(cancel_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def add_trigger_from_button(self, trigger: TriggerItem, dialog: QDialog):
        """버튼에서 트리거 추가"""
        trigger_data = {
            'name': trigger.name,
            'icon': trigger.icon,
            'category': trigger.category,
            'description': trigger.description
        }
        
        self.add_trigger(trigger_data)
        dialog.close()
    
    def add_trigger(self, trigger_data: Dict[str, Any]):
        """트리거 추가 (드롭 영역과 동일한 로직)"""
        self.triggers.append(trigger_data)
        
        # 트리거 위젯 생성
        trigger_widget = QWidget()
        trigger_layout = QHBoxLayout()
        
        # 트리거 정보
        info_label = QLabel(f"{trigger_data['icon']} {trigger_data['name']}")
        info_label.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
        """)
        
        # 삭제 버튼
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(30, 30)
        delete_btn.clicked.connect(lambda: self.remove_trigger(trigger_widget, trigger_data))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffebee;
                border: 1px solid #f44336;
                border-radius: 15px;
                color: #f44336;
            }
            QPushButton:hover {
                background-color: #f44336;
                color: white;
            }
        """)
        
        trigger_layout.addWidget(info_label)
        trigger_layout.addWidget(delete_btn)
        trigger_widget.setLayout(trigger_layout)
        
        self.triggers_layout.addWidget(trigger_widget)
        self.trigger_added.emit(trigger_data)
        self.update_hint_visibility()
    
    def remove_trigger(self, widget: QWidget, trigger_data: Dict[str, Any]):
        """트리거 제거"""
        if trigger_data in self.triggers:
            self.triggers.remove(trigger_data)
        
        widget.deleteLater()
        self.update_hint_visibility()
    
    def update_hint_visibility(self):
        """힌트 표시/숨김 업데이트"""
        self.hint_label.setVisible(len(self.triggers) == 0)

class UXComparisonApp(QMainWindow):
    """UX 비교 실험 앱"""
    
    def __init__(self):
        super().__init__()
        
        # 사용 통계 추적
        self.drag_drop_stats = {"adds": 0, "removes": 0, "time_spent": 0}
        self.button_stats = {"adds": 0, "removes": 0, "dialogs_opened": 0, "time_spent": 0}
        self.start_time = None
        
        self.setup_triggers()
        self.init_ui()
    
    def setup_triggers(self):
        """사용 가능한 트리거들 설정"""
        self.triggers = [
            TriggerItem("RSI", "📊", "기술지표", "상대강도지수 - 과매수/과매도"),
            TriggerItem("MACD", "📈", "기술지표", "이동평균수렴확산"),
            TriggerItem("볼린저밴드", "📉", "기술지표", "가격 변동 범위"),
            TriggerItem("가격변동", "💰", "가격", "가격 변동률 조건"),
            TriggerItem("수익률", "💎", "수익", "손익 기준 조건"),
            TriggerItem("급등급락", "⚡", "가격", "단시간 급변동"),
            TriggerItem("거래량", "📊", "거래량", "거래량 기반 조건"),
            TriggerItem("시간조건", "⏰", "시간", "특정 시간대"),
            TriggerItem("잔고확인", "🏦", "자산", "현금 잔고 조건"),
        ]
    
    def init_ui(self):
        self.setWindowTitle("🧪 드래그앤드롭 vs 버튼 방식 UX 비교 실험")
        self.setGeometry(100, 100, 1600, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃 (3단 구성)
        main_layout = QVBoxLayout()
        
        # 상단: 제목과 설명
        header = self.create_header()
        main_layout.addWidget(header)
        
        # 중앙: 비교 영역
        comparison_layout = QHBoxLayout()
        
        # 왼쪽: 트리거 팔레트
        palette = self.create_trigger_palette()
        comparison_layout.addWidget(palette, 1)
        
        # 중앙: 드래그앤드롭 방식
        drag_drop_area = self.create_drag_drop_area()
        comparison_layout.addWidget(drag_drop_area, 2)
        
        # 오른쪽: 버튼 방식
        button_area = self.create_button_area()
        comparison_layout.addWidget(button_area, 2)
        
        main_layout.addLayout(comparison_layout)
        
        # 하단: 통계 및 결과
        stats = self.create_stats_area()
        main_layout.addWidget(stats)
        
        central_widget.setLayout(main_layout)
        
        # 타이머 시작
        self.start_time = QTimer()
        self.start_time.start()
    
    def create_header(self) -> QWidget:
        """헤더 생성"""
        header = QWidget()
        header.setFixedHeight(100)
        header.setStyleSheet("background-color: #f0f4f8; border-bottom: 2px solid #ddd;")
        
        layout = QVBoxLayout()
        
        title = QLabel("🧪 UX 방식 비교 실험")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 10px;")
        
        subtitle = QLabel("왼쪽 트리거를 중앙(드래그앤드롭) 또는 오른쪽(버튼클릭)에 추가해보세요!")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        header.setLayout(layout)
        
        return header
    
    def create_trigger_palette(self) -> QWidget:
        """트리거 팔레트 생성"""
        palette = QWidget()
        palette.setMaximumWidth(250)
        
        layout = QVBoxLayout()
        
        title = QLabel("🎨 트리거 팔레트")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px; color: #34495e;")
        layout.addWidget(title)
        
        # 스크롤 영역
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # 카테고리별 그룹화
        categories = {}
        for trigger in self.triggers:
            if trigger.category not in categories:
                categories[trigger.category] = []
            categories[trigger.category].append(trigger)
        
        for category, triggers in categories.items():
            # 카테고리 라벨
            cat_label = QLabel(f"📁 {category}")
            cat_label.setStyleSheet("font-weight: bold; margin-top: 10px; color: #2c3e50;")
            scroll_layout.addWidget(cat_label)
            
            # 트리거들
            for trigger in triggers:
                drag_widget = DragDropTriggerWidget(trigger)
                scroll_layout.addWidget(drag_widget)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        
        layout.addWidget(scroll)
        palette.setLayout(layout)
        
        return palette
    
    def create_drag_drop_area(self) -> QWidget:
        """드래그앤드롭 영역 생성"""
        area = QWidget()
        area.setStyleSheet("background-color: #e8f5e8; border: 2px solid #4caf50; border-radius: 12px;")
        
        layout = QVBoxLayout()
        
        header = QLabel("🎯 드래그앤드롭 방식")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2e7d32; margin: 10px;")
        layout.addWidget(header)
        
        # 장점 표시
        pros = QLabel("✅ 직관적이고 빠름\n✅ 시각적 피드백\n✅ 재미있는 인터랙션")
        pros.setStyleSheet("color: #2e7d32; padding: 10px; font-size: 12px;")
        layout.addWidget(pros)
        
        # 드롭 영역
        self.drop_zone = DropZoneWidget("매수 조건")
        self.drop_zone.trigger_added.connect(self.on_drag_drop_add)
        layout.addWidget(self.drop_zone)
        
        area.setLayout(layout)
        return area
    
    def create_button_area(self) -> QWidget:
        """버튼 방식 영역 생성"""
        area = QWidget()
        area.setStyleSheet("background-color: #fff3e0; border: 2px solid #ff9800; border-radius: 12px;")
        
        layout = QVBoxLayout()
        
        header = QLabel("🔘 버튼 클릭 방식")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #f57c00; margin: 10px;")
        layout.addWidget(header)
        
        # 장점 표시
        pros = QLabel("✅ 명확한 액션\n✅ 접근성 좋음\n✅ 전통적 UI 패턴")
        pros.setStyleSheet("color: #f57c00; padding: 10px; font-size: 12px;")
        layout.addWidget(pros)
        
        # 버튼 기반 위젯
        self.button_widget = ButtonBasedTriggerWidget("매수 조건", self.triggers)
        self.button_widget.trigger_added.connect(self.on_button_add)
        layout.addWidget(self.button_widget)
        
        area.setLayout(layout)
        return area
    
    def create_stats_area(self) -> QWidget:
        """통계 영역 생성"""
        stats = QWidget()
        stats.setFixedHeight(100)
        stats.setStyleSheet("background-color: #f8f9fa; border-top: 2px solid #ddd;")
        
        layout = QHBoxLayout()
        
        # 드래그앤드롭 통계
        self.drag_stats_label = QLabel("🎯 드래그앤드롭: 0회 추가")
        self.drag_stats_label.setStyleSheet("font-weight: bold; color: #2e7d32; padding: 10px;")
        
        # 버튼 통계  
        self.button_stats_label = QLabel("🔘 버튼클릭: 0회 추가")
        self.button_stats_label.setStyleSheet("font-weight: bold; color: #f57c00; padding: 10px;")
        
        # 결과 버튼
        result_btn = QPushButton("📊 실험 결과 보기")
        result_btn.clicked.connect(self.show_experiment_results)
        result_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c5ce7;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a4fcf;
            }
        """)
        
        layout.addWidget(self.drag_stats_label)
        layout.addStretch()
        layout.addWidget(result_btn)
        layout.addStretch()
        layout.addWidget(self.button_stats_label)
        
        stats.setLayout(layout)
        return stats
    
    def on_drag_drop_add(self, trigger_data):
        """드래그앤드롭으로 추가될 때"""
        self.drag_drop_stats["adds"] += 1
        self.update_stats_display()
    
    def on_button_add(self, trigger_data):
        """버튼으로 추가될 때"""
        self.button_stats["adds"] += 1
        self.update_stats_display()
    
    def update_stats_display(self):
        """통계 표시 업데이트"""
        self.drag_stats_label.setText(
            f"🎯 드래그앤드롭: {self.drag_drop_stats['adds']}회 추가"
        )
        self.button_stats_label.setText(
            f"🔘 버튼클릭: {self.button_stats['adds']}회 추가"
        )
    
    def show_experiment_results(self):
        """실험 결과 표시"""
        dialog = QDialog(self)
        dialog.setWindowTitle("📊 UX 실험 결과")
        dialog.resize(600, 500)
        
        layout = QVBoxLayout()
        
        # 결과 분석
        results_text = QTextEdit()
        results_text.setReadOnly(True)
        
        # 통계 기반 분석
        drag_total = self.drag_drop_stats["adds"]
        button_total = self.button_stats["adds"]
        
        results = f"""
🧪 **UX 방식 비교 실험 결과**

📊 **사용 통계:**
• 드래그앤드롭 방식: {drag_total}회 사용
• 버튼 클릭 방식: {button_total}회 사용

🎯 **드래그앤드롭의 장점:**
✅ **직관성**: 마우스로 끌어다 놓는 자연스러운 동작
✅ **시각적 피드백**: 실시간 드래그 효과와 드롭 존 하이라이트
✅ **효율성**: 한 번의 동작으로 완료 (클릭 → 드래그 → 드롭)
✅ **재미**: 인터랙티브한 경험으로 사용자 만족도 높음
✅ **공간 활용**: 팔레트와 작업 영역 분리로 깔끔한 UI

🔘 **버튼 방식의 장점:**
✅ **명확성**: 명시적인 액션 버튼으로 의도가 분명
✅ **접근성**: 드래그가 어려운 사용자도 쉽게 사용
✅ **안정성**: 실수로 드래그되는 일이 없음
✅ **친숙함**: 전통적 UI 패턴으로 학습 비용 낮음

📈 **권장 결론:**

{self.get_recommendation(drag_total, button_total)}

🚀 **최적 설계안:**
두 방식을 모두 지원하는 하이브리드 UI가 최선!
• 기본: 드래그앤드롭 (빠르고 직관적)
• 대안: 우클릭 → "추가" 메뉴 (정확하고 안전)
• 접근성: 키보드 단축키 지원
        """
        
        results_text.setPlainText(results)
        layout.addWidget(results_text)
        
        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def get_recommendation(self, drag_count: int, button_count: int) -> str:
        """사용 패턴에 따른 추천"""
        if drag_count > button_count * 1.5:
            return """
🏆 **드래그앤드롭 승리!**
사용자가 드래그앤드롭을 압도적으로 선호합니다.
직관적이고 빠른 인터랙션이 효과적임을 증명!
"""
        elif button_count > drag_count * 1.5:
            return """
🏆 **버튼 방식 승리!**
명확한 액션 버튼을 더 선호하는 사용자입니다.
안정성과 명시성을 중요하게 생각하는 패턴!
"""
        else:
            return """
🤝 **무승부!**
두 방식 모두 각각의 장점이 있습니다.
하이브리드 방식으로 사용자 선택권을 제공하세요!
"""

def main():
    """메인 실행"""
    app = QApplication(sys.argv)
    
    # 스타일 시트
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f8f9fa;
        }
        QScrollArea {
            border: 1px solid #dee2e6;
            border-radius: 8px;
            background-color: white;
        }
        QScrollBar:vertical {
            background-color: #e9ecef;
            width: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background-color: #6c757d;
            border-radius: 6px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #495057;
        }
    """)
    
    window = UXComparisonApp()
    window.show()
    
    print("🧪 UX 비교 실험 앱이 시작되었습니다!")
    print("🎯 드래그앤드롭 vs 🔘 버튼 방식을 직접 비교해보세요!")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
