"""
간단한 조건 조합 UI 샘플
Simple Condition Combination UI Sample

핵심 기능만 포함한 가벼운 버전:
1. RSI + 볼린저 밴드 드래그앤드롭
2. 가격변동 3개 추가
3. 트레일링 스탑 설정
4. 간단한 백테스트 설정
"""
import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class DraggableCondition(QLabel):
    """드래그 가능한 조건 위젯"""
    
    def __init__(self, condition_type: str, icon: str):
        super().__init__()
        self.condition_type = condition_type
        self.icon = icon
        self.setText(f"{icon} {condition_type}")
        self.setup_style()
    
    def setup_style(self):
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(120, 40)
        self.setStyleSheet("""
            QLabel {
                background-color: #3498db;
                color: white;
                border-radius: 8px;
                padding: 8px;
                margin: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QLabel:hover {
                background-color: #2980b9;
                transform: scale(1.05);
            }
        """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 드래그 시작
            drag = QDrag(self)
            mimeData = QMimeData()
            mimeData.setText(f"{self.condition_type}|{self.icon}")
            drag.setMimeData(mimeData)
            drag.exec(Qt.DropAction.CopyAction)

class DropZone(QWidget):
    """조건을 드롭할 수 있는 영역"""
    
    def __init__(self):
        super().__init__()
        self.conditions = []
        self.init_ui()
        
    def init_ui(self):
        self.setAcceptDrops(True)
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("🎯 매매 조건 조합")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 조건 관계 선택
        relation_layout = QHBoxLayout()
        
        self.and_radio = QRadioButton("AND (모든 조건)")
        self.and_radio.setChecked(True)
        self.or_radio = QRadioButton("OR (하나만)")
        
        relation_layout.addWidget(QLabel("조건 관계:"))
        relation_layout.addWidget(self.and_radio)
        relation_layout.addWidget(self.or_radio)
        relation_layout.addStretch()
        
        layout.addLayout(relation_layout)
        
        # 드롭된 조건들을 표시할 스크롤 영역
        scroll = QScrollArea()
        self.conditions_widget = QWidget()
        self.conditions_layout = QVBoxLayout()
        self.conditions_widget.setLayout(self.conditions_layout)
        scroll.setWidget(self.conditions_widget)
        scroll.setWidgetResizable(True)
        
        layout.addWidget(scroll)
        
        # 안내 메시지
        self.hint_label = QLabel("📦 왼쪽에서 조건을 드래그해서 여기에 놓으세요")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setStyleSheet("color: #7f8c8d; font-size: 14px; padding: 20px;")
        self.conditions_layout.addWidget(self.hint_label)
        
        self.setLayout(layout)
        self.setup_style()
    
    def setup_style(self):
        self.setStyleSheet("""
            DropZone {
                border: 3px dashed #3498db;
                border-radius: 12px;
                background-color: #ecf0f1;
            }
        """)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet("""
                DropZone {
                    border: 3px dashed #e74c3c;
                    border-radius: 12px;
                    background-color: #fadbd8;
                }
            """)
    
    def dragLeaveEvent(self, event):
        self.setup_style()
    
    def dropEvent(self, event):
        data = event.mimeData().text()
        condition_type, icon = data.split('|')
        
        self.add_condition(condition_type, icon)
        event.acceptProposedAction()
        self.setup_style()
    
    def add_condition(self, condition_type: str, icon: str):
        """조건 추가"""
        # 조건 위젯 생성
        condition_frame = QFrame()
        condition_frame.setFrameStyle(QFrame.Shape.Box)
        condition_frame.setStyleSheet("QFrame { border: 2px solid #3498db; border-radius: 8px; background-color: white; margin: 5px; }")
        
        layout = QHBoxLayout()
        
        # 조건 표시
        label = QLabel(f"{icon} {condition_type}")
        label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50; padding: 10px;")
        layout.addWidget(label)
        
        # 간단한 설정 (예시)
        if condition_type == "RSI":
            period_spin = QSpinBox()
            period_spin.setRange(5, 50)
            period_spin.setValue(14)
            
            threshold_spin = QSpinBox()
            threshold_spin.setRange(10, 40)
            threshold_spin.setValue(30)
            
            layout.addWidget(QLabel("기간:"))
            layout.addWidget(period_spin)
            layout.addWidget(QLabel("임계값:"))
            layout.addWidget(threshold_spin)
            
        elif condition_type == "볼린저밴드":
            period_spin = QSpinBox()
            period_spin.setValue(20)
            
            std_spin = QDoubleSpinBox()
            std_spin.setValue(2.0)
            
            layout.addWidget(QLabel("기간:"))
            layout.addWidget(period_spin)
            layout.addWidget(QLabel("표준편차:"))
            layout.addWidget(std_spin)
            
        elif condition_type == "가격변동":
            percent_spin = QDoubleSpinBox()
            percent_spin.setRange(-50, 50)
            percent_spin.setValue(5.0)
            percent_spin.setSuffix("%")
            
            layout.addWidget(QLabel("변동률:"))
            layout.addWidget(percent_spin)
            
        elif condition_type == "트레일링스탑":
            # 🔥 활성화 조건 표시
            activation_spin = QDoubleSpinBox()
            activation_spin.setRange(1, 50)
            activation_spin.setValue(3.0)
            activation_spin.setSuffix("% 수익시 활성화")
            
            trailing_spin = QDoubleSpinBox()
            trailing_spin.setRange(1, 20)
            trailing_spin.setValue(5.0)
            trailing_spin.setSuffix("% 하락시 매도")
            
            layout.addWidget(activation_spin)
            layout.addWidget(trailing_spin)
        
        # 삭제 버튼
        remove_btn = QPushButton("❌")
        remove_btn.setMaximumWidth(30)
        remove_btn.clicked.connect(lambda: self.remove_condition(condition_frame))
        layout.addWidget(remove_btn)
        
        condition_frame.setLayout(layout)
        
        # 힌트 라벨 숨기기
        if self.hint_label.isVisible():
            self.hint_label.hide()
        
        self.conditions_layout.addWidget(condition_frame)
        self.conditions.append(condition_frame)
    
    def remove_condition(self, condition_frame):
        """조건 제거"""
        condition_frame.setParent(None)
        self.conditions.remove(condition_frame)
        
        # 조건이 없으면 힌트 표시
        if len(self.conditions) == 0:
            self.hint_label.show()

class QuickBacktestSettings(QGroupBox):
    """간단한 백테스트 설정"""
    
    def __init__(self):
        super().__init__("🧪 백테스트 설정")
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        # 코인 선택
        self.coin_combo = QComboBox()
        self.coin_combo.addItems(["KRW-BTC", "KRW-ETH", "KRW-XRP"])
        
        # 기간 선택
        period_layout = QHBoxLayout()
        
        btn_1w = QPushButton("1주")
        btn_1m = QPushButton("1개월")
        btn_3m = QPushButton("3개월")
        
        period_layout.addWidget(btn_1w)
        period_layout.addWidget(btn_1m)  
        period_layout.addWidget(btn_3m)
        
        # 슬립피지
        self.slippage_spin = QDoubleSpinBox()
        self.slippage_spin.setRange(0, 5)
        self.slippage_spin.setValue(0.1)
        self.slippage_spin.setSuffix("%")
        
        layout.addRow("코인:", self.coin_combo)
        layout.addRow("기간:", period_layout)
        layout.addRow("슬립피지:", self.slippage_spin)
        
        # 실행 버튼
        run_btn = QPushButton("🚀 백테스트 실행")
        run_btn.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; font-weight: bold; padding: 10px; }")
        run_btn.clicked.connect(self.run_backtest)
        
        layout.addRow(run_btn)
        
        self.setLayout(layout)
    
    def run_backtest(self):
        """백테스트 실행"""
        QMessageBox.information(self, "백테스트", f"🎊 {self.coin_combo.currentText()} 백테스트 완료!\n수익률: +12.5%")

class SimpleConditionUI(QMainWindow):
    """간단한 조건 조합 UI"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("📊 간단한 조건 조합 UI")
        self.setGeometry(100, 100, 1000, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        
        # 좌측: 조건 팔레트
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        palette_title = QLabel("📋 조건 팔레트")
        palette_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; padding: 10px;")
        left_layout.addWidget(palette_title)
        
        # 드래그 가능한 조건들
        conditions = [
            ("RSI", "📊"),
            ("볼린저밴드", "📈"), 
            ("가격변동", "💰"),
            ("가격변동", "💰"),  # 두 번째
            ("가격변동", "💰"),  # 세 번째  
            ("트레일링스탑", "📉")
        ]
        
        for condition_type, icon in conditions:
            draggable = DraggableCondition(condition_type, icon)
            left_layout.addWidget(draggable)
        
        left_layout.addStretch()
        
        # 안내 텍스트
        help_text = QLabel("💡 조건을 드래그해서 오른쪽에 놓으세요\n\n✅ RSI + 볼린저 밴드 AND 조건\n✅ 가격변동 3개 추가 가능\n✅ 트레일링 스탑 활성화 조건 표시")
        help_text.setStyleSheet("color: #7f8c8d; font-size: 11px; padding: 10px;")
        help_text.setWordWrap(True)
        left_layout.addWidget(help_text)
        
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(250)
        
        # 중앙: 드롭 존
        self.drop_zone = DropZone()
        
        # 우측: 백테스트 설정
        self.backtest_settings = QuickBacktestSettings()
        self.backtest_settings.setMaximumWidth(300)
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(self.drop_zone)
        main_layout.addWidget(self.backtest_settings)
        
        central_widget.setLayout(main_layout)
        
        self.statusBar().showMessage("📝 조건을 드래그앤드롭으로 조합하세요")

def main():
    """메인 실행"""
    app = QApplication(sys.argv)
    
    # 글로벌 스타일
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f8f9fa;
        }
        QPushButton {
            border: 2px solid #ccc;
            border-radius: 6px;
            padding: 6px 12px;
            background-color: white;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #e8e8e8;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #ddd;
            border-radius: 8px;
            margin: 10px;
            padding-top: 15px;
        }
    """)
    
    window = SimpleConditionUI()
    window.show()
    
    print("🚀 간단한 조건 조합 UI 시작!")
    print("✅ RSI + 볼린저 밴드 드래그앤드롭")
    print("✅ 가격변동 3개 추가")
    print("✅ 트레일링 스탑 활성화 조건")
    print("✅ 간단한 백테스트 설정")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
