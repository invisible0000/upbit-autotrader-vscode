"""
포트폴리오 목록 패널 컴포넌트
- 저장된 포트폴리오 목록 표시
- 새 포트폴리오 생성
- 포트폴리오 선택/삭제
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
    QListWidgetItem, QLabel, QMessageBox, QInputDialog, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class PortfolioListPanel(QWidget):
    """포트폴리오 목록 패널"""
    
    # 시그널 정의
    portfolio_selected = pyqtSignal(dict)  # 선택된 포트폴리오 정보
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_portfolios()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 제목
        title_label = QLabel("📁 포트폴리오 목록")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057;")
        layout.addWidget(title_label)
        
        # 새 포트폴리오 생성 버튼
        self.new_portfolio_btn = QPushButton("+ 새 포트폴리오")
        self.new_portfolio_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.new_portfolio_btn.clicked.connect(self.create_new_portfolio)
        layout.addWidget(self.new_portfolio_btn)
        
        # 포트폴리오 목록
        self.portfolio_list = QListWidget()
        self.portfolio_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #e9ecef;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
        self.portfolio_list.itemClicked.connect(self.on_portfolio_selected)
        layout.addWidget(self.portfolio_list)
        
        # 포트폴리오 관리 버튼들
        buttons_layout = QHBoxLayout()
        
        self.edit_btn = QPushButton("편집")
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
            }
        """)
        self.edit_btn.clicked.connect(self.edit_portfolio)
        self.edit_btn.setEnabled(False)
        buttons_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("삭제")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_portfolio)
        self.delete_btn.setEnabled(False)
        buttons_layout.addWidget(self.delete_btn)
        
        layout.addLayout(buttons_layout)
        
        # 포트폴리오 정보 표시
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Shape.Box)
        info_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: #f8f9fa;
                padding: 10px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        
        self.portfolio_info_label = QLabel("포트폴리오를 선택하세요")
        self.portfolio_info_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        self.portfolio_info_label.setWordWrap(True)
        info_layout.addWidget(self.portfolio_info_label)
        
        layout.addWidget(info_frame)
        
        # 스페이서
        layout.addStretch()
    
    def load_portfolios(self):
        """포트폴리오 목록 로드"""
        # TODO: 실제 DB에서 포트폴리오 목록 조회
        # portfolios = PortfolioManager.get_all_portfolios()
        
        # 임시 데이터
        sample_portfolios = [
            {
                "id": 1,
                "name": "안정형 포트폴리오",
                "description": "BTC/ETH 중심의 안정적인 포트폴리오",
                "created_date": "2025-01-15",
                "asset_count": 3,
                "total_weight": 100.0
            },
            {
                "id": 2,
                "name": "성장형 포트폴리오",
                "description": "알트코인 포함 고수익 추구",
                "created_date": "2025-01-10",
                "asset_count": 5,
                "total_weight": 100.0
            },
            {
                "id": 3,
                "name": "테스트 포트폴리오",
                "description": "전략 테스트용",
                "created_date": "2025-01-20",
                "asset_count": 2,
                "total_weight": 80.0
            }
        ]
        
        self.portfolio_list.clear()
        self.portfolios = {}
        
        for portfolio in sample_portfolios:
            item = QListWidgetItem()
            item.setText(f"{portfolio['name']}\n{portfolio['asset_count']}개 자산 • {portfolio['total_weight']}%")
            item.setData(Qt.ItemDataRole.UserRole, portfolio)
            self.portfolio_list.addItem(item)
            self.portfolios[portfolio['id']] = portfolio
    
    def create_new_portfolio(self):
        """새 포트폴리오 생성"""
        name, ok = QInputDialog.getText(
            self,
            "새 포트폴리오",
            "포트폴리오 이름을 입력하세요:"
        )
        
        if ok and name.strip():
            description, ok2 = QInputDialog.getText(
                self,
                "새 포트폴리오",
                "포트폴리오 설명을 입력하세요 (선택사항):"
            )
            
            if ok2:
                # TODO: 실제 포트폴리오 생성
                new_portfolio = {
                    "id": len(self.portfolios) + 1,
                    "name": name.strip(),
                    "description": description.strip() or "새로 생성된 포트폴리오",
                    "created_date": "2025-01-21",
                    "asset_count": 0,
                    "total_weight": 0.0
                }
                
                print(f"[DEBUG] 새 포트폴리오 생성: {new_portfolio}")
                self.refresh_list()
                
                # 새로 생성된 포트폴리오 선택
                self.portfolio_selected.emit(new_portfolio)
    
    def on_portfolio_selected(self, item):
        """포트폴리오 선택 시 처리"""
        portfolio_data = item.data(Qt.ItemDataRole.UserRole)
        
        # 버튼 활성화
        self.edit_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        
        # 포트폴리오 정보 표시
        info_text = f"""포트폴리오: {portfolio_data['name']}
설명: {portfolio_data['description']}
생성일: {portfolio_data['created_date']}
자산 개수: {portfolio_data['asset_count']}개
총 비중: {portfolio_data['total_weight']}%"""
        
        self.portfolio_info_label.setText(info_text)
        
        # 선택된 포트폴리오 정보 전달
        self.portfolio_selected.emit(portfolio_data)
    
    def edit_portfolio(self):
        """포트폴리오 편집"""
        current_item = self.portfolio_list.currentItem()
        if not current_item:
            return
        
        portfolio_data = current_item.data(Qt.ItemDataRole.UserRole)
        
        name, ok = QInputDialog.getText(
            self,
            "포트폴리오 편집",
            "포트폴리오 이름:",
            text=portfolio_data['name']
        )
        
        if ok and name.strip():
            portfolio_data['name'] = name.strip()
            current_item.setText(f"{portfolio_data['name']}\n{portfolio_data['asset_count']}개 자산 • {portfolio_data['total_weight']}%")
            current_item.setData(Qt.ItemDataRole.UserRole, portfolio_data)
            
            # TODO: DB 업데이트
            print(f"[DEBUG] 포트폴리오 편집: {portfolio_data}")
    
    def delete_portfolio(self):
        """포트폴리오 삭제"""
        current_item = self.portfolio_list.currentItem()
        if not current_item:
            return
        
        portfolio_data = current_item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self,
            "포트폴리오 삭제",
            f"'{portfolio_data['name']}' 포트폴리오를 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: DB에서 삭제
            print(f"[DEBUG] 포트폴리오 삭제: {portfolio_data}")
            
            self.portfolio_list.takeItem(self.portfolio_list.currentRow())
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.portfolio_info_label.setText("포트폴리오를 선택하세요")
    
    def refresh_list(self):
        """포트폴리오 목록 새로고침"""
        self.load_portfolios()
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.portfolio_info_label.setText("포트폴리오를 선택하세요")
