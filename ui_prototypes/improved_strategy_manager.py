"""
개선된 전략 관리 시스템
Enhanced Strategy Management System

명확한 개념 정리와 사용자 친화적 인터페이스
"""

import sys
import sqlite3
import json
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class StrategyInfo:
    """전략 정보"""
    strategy_id: str
    name: str
    description: str
    created_at: str
    modified_at: str
    is_active: bool
    rules_count: int
    tags: List[str]

class StrategyDatabase:
    """전략 데이터베이스 관리"""
    
    def __init__(self, db_path: str = "strategies.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 전략 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                strategy_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                modified_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                rules_count INTEGER DEFAULT 0,
                tags TEXT,
                strategy_data TEXT NOT NULL
            )
        """)
        
        # 실행 히스토리 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id TEXT,
                rule_id TEXT,
                executed_at TEXT,
                trigger_type TEXT,
                action_type TEXT,
                result TEXT,
                FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_strategy(self, strategy_data: Dict[str, Any]) -> str:
        """전략 저장 (자동 ID 생성)"""
        strategy_id = f"STR_{int(datetime.now().timestamp() * 1000)}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        tags = strategy_data.get('tags', [])
        
        cursor.execute("""
            INSERT OR REPLACE INTO strategies 
            (strategy_id, name, description, created_at, modified_at, is_active, rules_count, tags, strategy_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            strategy_id,
            strategy_data.get('name', '무제 전략'),
            strategy_data.get('description', ''),
            now, now, 1,
            len(strategy_data.get('rules', [])),
            json.dumps(tags),
            json.dumps(strategy_data, ensure_ascii=False)
        ))
        
        conn.commit()
        conn.close()
        
        return strategy_id
    
    def load_strategies(self) -> List[StrategyInfo]:
        """모든 전략 목록 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM strategies ORDER BY modified_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        strategies = []
        for row in rows:
            strategies.append(StrategyInfo(
                strategy_id=row[0],
                name=row[1],
                description=row[2] or '',
                created_at=row[3],
                modified_at=row[4],
                is_active=bool(row[5]),
                rules_count=row[6],
                tags=json.loads(row[7]) if row[7] else []
            ))
        
        return strategies
    
    def load_strategy_data(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """특정 전략 데이터 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT strategy_data FROM strategies WHERE strategy_id = ?", (strategy_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
    
    def delete_strategy(self, strategy_id: str):
        """전략 삭제"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM strategies WHERE strategy_id = ?", (strategy_id,))
        cursor.execute("DELETE FROM execution_history WHERE strategy_id = ?", (strategy_id,))
        
        conn.commit()
        conn.close()

class ActionTypeExplainer(QDialog):
    """액션 타입 설명 다이얼로그"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("액션 타입 설명")
        self.setModal(True)
        self.resize(600, 500)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("📚 액션 타입별 용도 설명")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # 설명 텍스트
        explanation = QTextEdit()
        explanation.setReadOnly(True)
        explanation.setHtml("""
        <h3>🔥 매수 (Buy Action)</h3>
        <p><b>언제 사용:</b> 포지션을 새로 열거나 기존 포지션에 추가 매수할 때</p>
        <p><b>예시:</b></p>
        <ul>
            <li>RSI < 30일 때 첫 매수</li>
            <li>가격이 5% 하락할 때마다 추가 매수 (불타기)</li>
            <li>골든크로스 시 초기 포지션 진입</li>
        </ul>
        <p><b>설정:</b> 전량/비율/고정금액, 매수 횟수 제한</p>
        
        <hr>
        <h3>🔴 매도 (Sell Action)</h3>
        <p><b>언제 사용:</b> 수익실현, 손절, 포지션 정리할 때</p>
        <p><b>예시:</b></p>
        <ul>
            <li>구매가 대비 10% 상승 시 전량 매도</li>
            <li>3% 손실 시 스탑로스 매도</li>
            <li>데드크로스 시 급매도</li>
        </ul>
        <p><b>설정:</b> 전량/일부 매도, 단계적 매도</p>
        
        <hr>
        <h3>👁️ 감시 (Watch Action) - 제거 권장</h3>
        <p><b>원래 목적:</b> 트리거 조건은 만족하지만 즉시 거래하지 않고 일정 시간 관찰</p>
        <p><b>문제점:</b> 실제 거래 시스템에서는 불필요한 복잡성만 추가</p>
        <p><b>대안:</b> 조건 설정으로 대체 (예: 연속 3번 신호 후 매수)</p>
        
        <hr>
        <h3>🔢 실행 횟수 관리</h3>
        <p><b>규칙 레벨 카운트:</b> 해당 규칙 전체의 실행 횟수 제한</p>
        <p><b>액션 레벨 카운트:</b> 특정 액션(매수)의 연속 실행 횟수 제한</p>
        <p><b>예시:</b> "불타기는 최대 3번까지만" → 액션 레벨</p>
        <p><b>예시:</b> "하루에 진입 규칙은 1번만" → 규칙 레벨</p>
        
        <hr>
        <h3>📈 상승시만 트리거 구현</h3>
        <p><b>기술적 구현:</b></p>
        <ul>
            <li>이전 가격과 현재 가격 비교</li>
            <li>트렌드 방향 판단 (이동평균 기울기)</li>
            <li>연속 상승 캔들 개수 확인</li>
        </ul>
        <p><b>설정 예시:</b> "구매가 대비 5% 상승" + "상승 추세에서만"</p>
        """)
        layout.addWidget(explanation)
        
        # 닫기 버튼
        close_btn = QPushButton("확인")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

class ImprovedActionConfigWidget(QWidget):
    """개선된 액션 설정 위젯"""
    
    def __init__(self, action_type: str):
        super().__init__()
        self.action_type = action_type
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        if self.action_type == "매수":
            # 매수 방식
            self.amount_type = QComboBox()
            self.amount_type.addItems([
                "전량 (가용 자금 전체)", 
                "비율 (자금의 N%)", 
                "고정 금액 (N원)",
                "불타기 방식 (회차별 증가)"
            ])
            layout.addRow("매수 방식:", self.amount_type)
            
            # 금액/비율 설정
            self.amount_value = QDoubleSpinBox()
            self.amount_value.setRange(1.0, 100.0)
            self.amount_value.setValue(20.0)
            self.amount_value.setSuffix("%")
            layout.addRow("비율/금액:", self.amount_value)
            
            # 매수 횟수 제한 (불타기)
            self.max_buy_count = QSpinBox()
            self.max_buy_count.setRange(1, 10)
            self.max_buy_count.setValue(3)
            layout.addRow("최대 매수 횟수:", self.max_buy_count)
            
            # 매수 간격 (불타기)
            self.buy_interval = QDoubleSpinBox()
            self.buy_interval.setRange(1.0, 50.0)
            self.buy_interval.setValue(5.0)
            self.buy_interval.setSuffix("%")
            layout.addRow("매수 간격 (가격 하락):", self.buy_interval)
            
        elif self.action_type == "매도":
            # 매도 방식
            self.sell_type = QComboBox()
            self.sell_type.addItems([
                "전량 매도",
                "일부 매도 (고정%)",
                "단계적 매도 (익절용)",
                "손절 매도"
            ])
            layout.addRow("매도 방식:", self.sell_type)
            
            # 매도 비율
            self.sell_ratio = QDoubleSpinBox()
            self.sell_ratio.setRange(1.0, 100.0)
            self.sell_ratio.setValue(100.0)
            self.sell_ratio.setSuffix("%")
            layout.addRow("매도 비율:", self.sell_ratio)
            
            # 수익/손실 기준
            self.profit_loss_base = QComboBox()
            self.profit_loss_base.addItems(["구매가 기준", "최고가 기준", "직전 가격 기준"])
            layout.addRow("기준 가격:", self.profit_loss_base)
            
        # 감시 액션은 제거 (너무 복잡하고 불필요)
        
        self.setLayout(layout)
    
    def get_config(self) -> Dict[str, Any]:
        if self.action_type == "매수":
            return {
                "amount_type": ["full", "percent", "fixed", "scaling"][self.amount_type.currentIndex()],
                "amount_value": self.amount_value.value(),
                "max_buy_count": self.max_buy_count.value(),
                "buy_interval_percent": self.buy_interval.value()
            }
        elif self.action_type == "매도":
            return {
                "sell_type": ["full", "partial", "staged", "stop_loss"][self.sell_type.currentIndex()],
                "sell_ratio": self.sell_ratio.value(),
                "base_price": ["buy_price", "high_price", "prev_price"][self.profit_loss_base.currentIndex()]
            }
        return {}

class ImprovedTriggerConfigWidget(QWidget):
    """개선된 트리거 설정 위젯"""
    
    def __init__(self, trigger_type: str):
        super().__init__()
        self.trigger_type = trigger_type
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        if self.trigger_type == "RSI":
            # RSI 기본 설정
            self.threshold = QSpinBox()
            self.threshold.setRange(0, 100)
            self.threshold.setValue(30)
            layout.addRow("RSI 임계값:", self.threshold)
            
            self.direction = QComboBox()
            self.direction.addItems(["이하 (<=)", "이상 (>=)"])
            layout.addRow("조건:", self.direction)
            
            self.period = QSpinBox()
            self.period.setRange(5, 50)
            self.period.setValue(14)
            layout.addRow("RSI 기간:", self.period)
            
        elif self.trigger_type == "가격변동":
            # 기준 가격
            self.base_price = QComboBox()
            self.base_price.addItems([
                "구매가 기준",
                "전일 종가 기준", 
                "최고가 기준",
                "최저가 기준",
                "이동평균 기준"
            ])
            layout.addRow("기준 가격:", self.base_price)
            
            # 변동률
            self.change_percent = QDoubleSpinBox()
            self.change_percent.setRange(-50.0, 50.0)
            self.change_percent.setValue(5.0)
            self.change_percent.setSuffix("%")
            layout.addRow("변동률:", self.change_percent)
            
            # **핵심: 상승/하락 구분**
            self.trend_filter = QComboBox()
            self.trend_filter.addItems([
                "상승/하락 모두", 
                "상승 추세에서만",  # 이동평균 위에서만
                "하락 추세에서만",  # 이동평균 아래에서만
                "연속 상승 중에만", # N개 캔들 연속 상승
                "연속 하락 중에만"  # N개 캔들 연속 하락
            ])
            layout.addRow("추세 필터:", self.trend_filter)
            
            # 추세 판단 기간
            self.trend_period = QSpinBox()
            self.trend_period.setRange(5, 50)
            self.trend_period.setValue(20)
            layout.addRow("추세 판단 기간:", self.trend_period)
            
        elif self.trigger_type == "MACD":
            # MACD 신호
            self.signal_type = QComboBox()
            self.signal_type.addItems([
                "골든크로스 (상승)",
                "데드크로스 (하락)",
                "히스토그램 > 0",
                "히스토그램 < 0",
                "MACD > 시그널"
            ])
            layout.addRow("MACD 신호:", self.signal_type)
        
        self.setLayout(layout)
    
    def get_config(self) -> Dict[str, Any]:
        if self.trigger_type == "RSI":
            return {
                "threshold": self.threshold.value(),
                "direction": "<=" if self.direction.currentIndex() == 0 else ">=",
                "period": self.period.value()
            }
        elif self.trigger_type == "가격변동":
            bases = ["buy_price", "prev_close", "high_price", "low_price", "ma_price"]
            trends = ["both", "uptrend", "downtrend", "consecutive_up", "consecutive_down"]
            return {
                "base_price": bases[self.base_price.currentIndex()],
                "change_percent": self.change_percent.value(),
                "trend_filter": trends[self.trend_filter.currentIndex()],
                "trend_period": self.trend_period.value()
            }
        elif self.trigger_type == "MACD":
            signals = ["golden_cross", "dead_cross", "hist_positive", "hist_negative", "macd_above_signal"]
            return {
                "signal_type": signals[self.signal_type.currentIndex()]
            }
        return {}

class StrategyListWidget(QWidget):
    """전략 목록 위젯"""
    
    strategy_selected = pyqtSignal(str)  # 전략 선택 신호
    strategy_deleted = pyqtSignal(str)   # 전략 삭제 신호
    
    def __init__(self):
        super().__init__()
        self.db = StrategyDatabase()
        self.init_ui()
        self.refresh_strategies()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("💼 저장된 전략들")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # 전략 테이블
        self.strategy_table = QTableWidget()
        self.strategy_table.setColumnCount(6)
        self.strategy_table.setHorizontalHeaderLabels([
            "전략명", "설명", "규칙수", "생성일", "상태", "액션"
        ])
        
        # 테이블 설정
        header = self.strategy_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.strategy_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.strategy_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.strategy_table)
        
        # 하단 버튼들
        buttons_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self.refresh_strategies)
        buttons_layout.addWidget(refresh_btn)
        
        new_strategy_btn = QPushButton("➕ 새 전략")
        new_strategy_btn.clicked.connect(self.create_new_strategy)
        new_strategy_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        buttons_layout.addWidget(new_strategy_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def refresh_strategies(self):
        """전략 목록 새로고침"""
        strategies = self.db.load_strategies()
        self.strategy_table.setRowCount(len(strategies))
        
        for row, strategy in enumerate(strategies):
            # 전략명
            name_item = QTableWidgetItem(strategy.name)
            self.strategy_table.setItem(row, 0, name_item)
            
            # 설명
            desc_item = QTableWidgetItem(strategy.description[:50] + "..." if len(strategy.description) > 50 else strategy.description)
            self.strategy_table.setItem(row, 1, desc_item)
            
            # 규칙수
            rules_item = QTableWidgetItem(str(strategy.rules_count))
            self.strategy_table.setItem(row, 2, rules_item)
            
            # 생성일
            created_date = datetime.fromisoformat(strategy.created_at).strftime("%Y-%m-%d %H:%M")
            date_item = QTableWidgetItem(created_date)
            self.strategy_table.setItem(row, 3, date_item)
            
            # 상태
            status_item = QTableWidgetItem("🟢 활성" if strategy.is_active else "🔴 비활성")
            self.strategy_table.setItem(row, 4, status_item)
            
            # 액션 버튼들
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(30, 25)
            edit_btn.clicked.connect(lambda checked, sid=strategy.strategy_id: self.strategy_selected.emit(sid))
            actions_layout.addWidget(edit_btn)
            
            export_btn = QPushButton("📤")
            export_btn.setFixedSize(30, 25)
            export_btn.clicked.connect(lambda checked, sid=strategy.strategy_id: self.export_strategy(sid))
            actions_layout.addWidget(export_btn)
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(30, 25)
            delete_btn.setStyleSheet("background-color: #f44336; color: white;")
            delete_btn.clicked.connect(lambda checked, sid=strategy.strategy_id: self.delete_strategy(sid))
            actions_layout.addWidget(delete_btn)
            
            self.strategy_table.setCellWidget(row, 5, actions_widget)
    
    def create_new_strategy(self):
        """새 전략 생성 신호"""
        self.strategy_selected.emit("")  # 빈 ID = 새 전략
    
    def export_strategy(self, strategy_id: str):
        """전략 JSON 내보내기"""
        strategy_data = self.db.load_strategy_data(strategy_id)
        if strategy_data:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "전략 내보내기",
                f"{strategy_data['name']}.json",
                "JSON Files (*.json)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(strategy_data, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "내보내기 완료", f"전략이 저장되었습니다:\n{filename}")
    
    def delete_strategy(self, strategy_id: str):
        """전략 삭제"""
        reply = QMessageBox.question(
            self, 
            "전략 삭제", 
            "정말로 이 전략을 삭제하시겠습니까?\n삭제된 전략은 복구할 수 없습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_strategy(strategy_id)
            self.refresh_strategies()
            QMessageBox.information(self, "삭제 완료", "전략이 삭제되었습니다.")

def main():
    """메인 실행 함수"""
    app = QApplication(sys.argv)
    
    # 스타일 설정
    app.setStyleSheet("""
        QMainWindow { background-color: #f5f5f5; }
        QGroupBox { 
            font-weight: bold; border: 2px solid #cccccc; 
            border-radius: 5px; margin: 5px; padding-top: 10px; 
        }
        QPushButton { 
            border: 1px solid #cccccc; border-radius: 3px; 
            padding: 5px; background-color: white; 
        }
        QPushButton:hover { background-color: #e0e0e0; }
        QTableWidget { 
            gridline-color: #d0d0d0; 
            selection-background-color: #e3f2fd;
        }
    """)
    
    # 테스트용 간단 창
    window = QMainWindow()
    window.setWindowTitle("🚀 개선된 전략 관리 시스템")
    window.setGeometry(100, 100, 1200, 800)
    
    # 탭 위젯
    tab_widget = QTabWidget()
    
    # 전략 목록 탭
    strategy_list = StrategyListWidget()
    tab_widget.addTab(strategy_list, "📋 전략 목록")
    
    # 액션 설명 탭
    explanation_btn = QPushButton("📚 액션 타입 설명")
    explanation_btn.clicked.connect(lambda: ActionTypeExplainer(window).exec())
    
    help_widget = QWidget()
    help_layout = QVBoxLayout()
    help_layout.addWidget(explanation_btn)
    help_layout.addStretch()
    help_widget.setLayout(help_layout)
    
    tab_widget.addTab(help_widget, "❓ 도움말")
    
    window.setCentralWidget(tab_widget)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
