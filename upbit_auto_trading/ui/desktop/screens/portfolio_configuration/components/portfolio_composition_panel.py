"""
포트폴리오 구성 패널 컴포넌트
- 자산 배분 시각화 (도넛 차트)
- 자산 목록 테이블
- 자산 추가/수정/삭제
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QLabel, QMessageBox, QDialog, QDialogButtonBox,
    QFormLayout, QComboBox, QDoubleSpinBox, QLineEdit, QFrame,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QColor
import math

class PortfolioCompositionPanel(QWidget):
    """포트폴리오 구성 패널"""
    
    # 시그널 정의
    portfolio_changed = pyqtSignal(dict)  # 포트폴리오 변경 시
    portfolio_saved = pyqtSignal()  # 포트폴리오 저장 시
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_portfolio = None
        self.assets = []
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 제목 및 저장 버튼
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📊 포트폴리오 구성")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.save_btn = QPushButton("💾 저장")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.save_btn.clicked.connect(self.save_portfolio)
        self.save_btn.setEnabled(False)
        header_layout.addWidget(self.save_btn)
        
        layout.addLayout(header_layout)
        
        # 자산 배분 차트
        self.chart_widget = AssetAllocationChart(self)
        self.chart_widget.setFixedHeight(250)
        layout.addWidget(self.chart_widget)
        
        # 자산 추가 버튼
        self.add_asset_btn = QPushButton("+ 자산 추가")
        self.add_asset_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.add_asset_btn.clicked.connect(self.add_asset)
        self.add_asset_btn.setEnabled(False)
        layout.addWidget(self.add_asset_btn)
        
        # 자산 목록 테이블
        self.assets_table = QTableWidget()
        self.assets_table.setColumnCount(5)
        self.assets_table.setHorizontalHeaderLabels(["코인", "전략", "비중(%)", "예상수익률", "액션"])
        
        # 테이블 스타일
        self.assets_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                gridline-color: #e9ecef;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e9ecef;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
            }
        """)
        
        # 테이블 설정
        header = self.assets_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 코인
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 전략
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # 비중
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # 예상수익률
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)    # 액션
        
        self.assets_table.setColumnWidth(2, 80)   # 비중
        self.assets_table.setColumnWidth(3, 100)  # 예상수익률
        self.assets_table.setColumnWidth(4, 80)   # 액션
        
        self.assets_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.assets_table.itemChanged.connect(self.on_asset_changed)
        
        layout.addWidget(self.assets_table)
        
        # 총 비중 표시
        self.total_weight_label = QLabel("총 비중: 0%")
        self.total_weight_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #dc3545;
            padding: 10px;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
        """)
        layout.addWidget(self.total_weight_label)
    
    def load_portfolio(self, portfolio_data):
        """포트폴리오 로드"""
        self.current_portfolio = portfolio_data
        self.save_btn.setEnabled(True)
        self.add_asset_btn.setEnabled(True)
        
        # TODO: 실제 DB에서 포트폴리오 자산 정보 로드
        # assets = PortfolioManager.get_portfolio_assets(portfolio_data['id'])
        
        # 임시 데이터
        if portfolio_data['name'] == "안정형 포트폴리오":
            self.assets = [
                {"coin": "BTC-KRW", "strategy": "DCA 전략", "weight": 50.0, "expected_return": 12.5},
                {"coin": "ETH-KRW", "strategy": "RSI 전략", "weight": 30.0, "expected_return": 15.2},
                {"coin": "ADA-KRW", "strategy": "MA 크로스", "weight": 20.0, "expected_return": 8.7}
            ]
        elif portfolio_data['name'] == "성장형 포트폴리오":
            self.assets = [
                {"coin": "BTC-KRW", "strategy": "볼린저 밴드", "weight": 30.0, "expected_return": 18.2},
                {"coin": "ETH-KRW", "strategy": "RSI 전략", "weight": 25.0, "expected_return": 22.1},
                {"coin": "SOL-KRW", "strategy": "MA 크로스", "weight": 20.0, "expected_return": 25.8},
                {"coin": "DOT-KRW", "strategy": "DCA 전략", "weight": 15.0, "expected_return": 14.3},
                {"coin": "ADA-KRW", "strategy": "스윙 전략", "weight": 10.0, "expected_return": 16.9}
            ]
        else:
            self.assets = [
                {"coin": "BTC-KRW", "strategy": "테스트 전략", "weight": 50.0, "expected_return": 10.0},
                {"coin": "ETH-KRW", "strategy": "테스트 전략", "weight": 30.0, "expected_return": 12.0}
            ]
        
        self.update_table()
        self.update_chart()
        self.update_total_weight()
        
        # 포트폴리오 변경 시그널 발송
        self.portfolio_changed.emit(self.get_portfolio_data())
    
    def update_table(self):
        """자산 테이블 업데이트"""
        self.assets_table.setRowCount(len(self.assets))
        
        for row, asset in enumerate(self.assets):
            # 코인
            self.assets_table.setItem(row, 0, QTableWidgetItem(asset['coin']))
            
            # 전략
            self.assets_table.setItem(row, 1, QTableWidgetItem(asset['strategy']))
            
            # 비중
            weight_item = QTableWidgetItem(f"{asset['weight']:.1f}")
            weight_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.assets_table.setItem(row, 2, weight_item)
            
            # 예상수익률
            return_item = QTableWidgetItem(f"{asset['expected_return']:.1f}%")
            return_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            return_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # 읽기 전용
            self.assets_table.setItem(row, 3, return_item)
            
            # 삭제 버튼
            delete_btn = QPushButton("삭제")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            delete_btn.clicked.connect(lambda checked, r=row: self.remove_asset(r))
            self.assets_table.setCellWidget(row, 4, delete_btn)
    
    def update_chart(self):
        """차트 업데이트"""
        self.chart_widget.set_data(self.assets)
        self.chart_widget.update()
    
    def update_total_weight(self):
        """총 비중 업데이트"""
        total = sum(asset['weight'] for asset in self.assets)
        
        if total == 100.0:
            color = "#28a745"  # 녹색
            text = f"총 비중: {total:.1f}% ✓"
        elif total > 100.0:
            color = "#dc3545"  # 빨간색
            text = f"총 비중: {total:.1f}% (100% 초과!)"
        else:
            color = "#ffc107"  # 노란색
            text = f"총 비중: {total:.1f}% (100% 미만)"
        
        self.total_weight_label.setText(text)
        self.total_weight_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: bold; 
            color: {color};
            padding: 10px;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
        """)
    
    def add_asset(self):
        """자산 추가"""
        dialog = AddAssetDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            asset_data = dialog.get_asset_data()
            self.assets.append(asset_data)
            
            self.update_table()
            self.update_chart()
            self.update_total_weight()
            
            # 포트폴리오 변경 시그널 발송
            self.portfolio_changed.emit(self.get_portfolio_data())
    
    def remove_asset(self, row):
        """자산 제거"""
        if 0 <= row < len(self.assets):
            asset = self.assets[row]
            
            reply = QMessageBox.question(
                self,
                "자산 제거",
                f"{asset['coin']} 자산을 포트폴리오에서 제거하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.assets.pop(row)
                
                self.update_table()
                self.update_chart()
                self.update_total_weight()
                
                # 포트폴리오 변경 시그널 발송
                self.portfolio_changed.emit(self.get_portfolio_data())
    
    def on_asset_changed(self, item):
        """자산 정보 변경 시 처리"""
        row = item.row()
        col = item.column()
        
        if col == 2:  # 비중 변경
            try:
                new_weight = float(item.text())
                if 0 <= new_weight <= 100:
                    self.assets[row]['weight'] = new_weight
                    self.update_chart()
                    self.update_total_weight()
                    
                    # 포트폴리오 변경 시그널 발송
                    self.portfolio_changed.emit(self.get_portfolio_data())
                else:
                    QMessageBox.warning(self, "입력 오류", "비중은 0-100 사이의 값이어야 합니다.")
                    item.setText(f"{self.assets[row]['weight']:.1f}")
            except ValueError:
                QMessageBox.warning(self, "입력 오류", "숫자를 입력해주세요.")
                item.setText(f"{self.assets[row]['weight']:.1f}")
    
    def save_portfolio(self):
        """포트폴리오 저장"""
        if not self.current_portfolio:
            return
        
        # TODO: 실제 DB에 저장
        # PortfolioManager.save_portfolio(self.current_portfolio['id'], self.assets)
        
        QMessageBox.information(
            self,
            "저장 완료",
            f"'{self.current_portfolio['name']}' 포트폴리오가 저장되었습니다."
        )
        
        # 저장 완료 시그널 발송
        self.portfolio_saved.emit()
    
    def get_portfolio_data(self):
        """현재 포트폴리오 데이터 반환"""
        if not self.current_portfolio:
            return {}
        
        return {
            "portfolio": self.current_portfolio,
            "assets": self.assets,
            "total_weight": sum(asset['weight'] for asset in self.assets),
            "expected_return": sum(asset['weight'] * asset['expected_return'] / 100 for asset in self.assets),
            "asset_count": len(self.assets)
        }

class AssetAllocationChart(QWidget):
    """자산 배분 도넛 차트"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []
        self.colors = [
            QColor("#FF6384"), QColor("#36A2EB"), QColor("#FFCE56"),
            QColor("#4BC0C0"), QColor("#9966FF"), QColor("#FF9F40"),
            QColor("#FF6384"), QColor("#C9CBCF"), QColor("#4BC0C0")
        ]
    
    def set_data(self, assets):
        """데이터 설정"""
        self.data = assets
        self.update()
    
    def paintEvent(self, event):
        """차트 그리기"""
        if not self.data:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 빈 원 그리기
            rect = self.rect().adjusted(20, 20, -20, -20)
            painter.setPen(QPen(QColor("#dee2e6"), 2))
            painter.setBrush(QBrush(QColor("#f8f9fa")))
            painter.drawEllipse(rect)
            
            # 텍스트 표시
            painter.setPen(QColor("#6c757d"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "자산을 추가하세요")
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 차트 영역
        rect = self.rect().adjusted(50, 50, -50, -50)
        center = rect.center()
        radius = min(rect.width(), rect.height()) // 2
        inner_radius = radius * 0.6
        
        # 총 비중 계산
        total_weight = sum(asset['weight'] for asset in self.data)
        if total_weight == 0:
            return
        
        start_angle = 0
        
        for i, asset in enumerate(self.data):
            # 각도 계산 (16분할 단위)
            span_angle = int((asset['weight'] / total_weight) * 360 * 16)
            
            # 색상 설정
            color = self.colors[i % len(self.colors)]
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(120), 1))
            
            # 도넛 세그먼트 그리기
            painter.drawPie(rect, start_angle, span_angle)
            
            # 레이블 위치 계산
            mid_angle = (start_angle + span_angle / 2) / 16
            label_angle = math.radians(mid_angle)
            label_radius = radius * 0.8
            
            label_x = center.x() + label_radius * math.cos(label_angle)
            label_y = center.y() + label_radius * math.sin(label_angle)
            
            # 레이블 그리기
            painter.setPen(QColor("#495057"))
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            
            label_text = f"{asset['coin'].split('-')[0]}\n{asset['weight']:.1f}%"
            painter.drawText(int(label_x - 20), int(label_y - 10), 40, 20, 
                           Qt.AlignmentFlag.AlignCenter, label_text)
            
            start_angle += span_angle
        
        # 중앙 구멍 그리기
        painter.setBrush(QBrush(self.palette().color(self.backgroundRole())))
        painter.setPen(QPen(self.palette().color(self.backgroundRole())))
        inner_rect = rect.adjusted(radius - inner_radius, radius - inner_radius,
                                  -(radius - inner_radius), -(radius - inner_radius))
        painter.drawEllipse(inner_rect)

class AddAssetDialog(QDialog):
    """자산 추가 대화상자"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("자산 추가")
        self.setModal(True)
        self.resize(400, 300)
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 폼 레이아웃
        form = QFormLayout()
        
        # 코인 선택
        self.coin_combo = QComboBox()
        self.coin_combo.addItems([
            "BTC-KRW", "ETH-KRW", "ADA-KRW", "DOT-KRW", "SOL-KRW",
            "MATIC-KRW", "AVAX-KRW", "ATOM-KRW", "LINK-KRW", "XRP-KRW"
        ])
        form.addRow("코인:", self.coin_combo)
        
        # 전략 선택
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "DCA 전략", "RSI 전략", "MA 크로스", "볼린저 밴드", 
            "스윙 전략", "테스트 전략"
        ])
        form.addRow("전략:", self.strategy_combo)
        
        # 비중 입력
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(0.1, 100.0)
        self.weight_spin.setValue(10.0)
        self.weight_spin.setSuffix("%")
        form.addRow("비중:", self.weight_spin)
        
        layout.addLayout(form)
        
        # 버튼
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_asset_data(self):
        """입력된 자산 데이터 반환"""
        return {
            "coin": self.coin_combo.currentText(),
            "strategy": self.strategy_combo.currentText(),
            "weight": self.weight_spin.value(),
            "expected_return": 10.0 + (hash(self.coin_combo.currentText()) % 20)  # 임시 수익률
        }
