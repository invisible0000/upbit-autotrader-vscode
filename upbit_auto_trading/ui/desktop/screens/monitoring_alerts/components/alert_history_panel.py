"""
알림 기록 패널 컴포넌트
- 과거 알림 기록 조회
- 알림 기록 검색 및 필터링
- 상세 정보 표시
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QDateEdit, QGroupBox, QHeaderView, QMessageBox, QDialog,
    QDialogButtonBox, QTextEdit, QFormLayout
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import datetime

class AlertHistoryPanel(QWidget):
    """알림 기록 패널"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.alert_records = []
        self.filtered_records = []
        self.init_ui()
        self.load_sample_data()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 검색 및 필터 영역
        search_filter_group = self.create_search_filter_panel()
        layout.addWidget(search_filter_group)
        
        # 알림 기록 테이블
        history_table_group = self.create_history_table()
        layout.addWidget(history_table_group)
        
        # 통계 정보
        stats_group = self.create_stats_panel()
        layout.addWidget(stats_group)
    
    def create_search_filter_panel(self):
        """검색 및 필터 패널 생성"""
        group = QGroupBox("🔍 검색 및 필터")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        # 첫 번째 행: 키워드 검색
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("키워드:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("코인명, 메시지 내용으로 검색...")
        self.search_input.textChanged.connect(self.apply_filters)
        search_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("검색")
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        search_btn.clicked.connect(self.apply_filters)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        # 두 번째 행: 필터 옵션
        filter_layout = QHBoxLayout()
        
        # 알림 유형 필터
        filter_layout.addWidget(QLabel("유형:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems([
            "전체", "가격 알림", "기술적 지표 알림", "주문 체결 알림", 
            "거래량 알림", "시스템 상태 알림"
        ])
        self.type_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.type_filter)
        
        # 상태 필터
        filter_layout.addWidget(QLabel("상태:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["전체", "발생", "해결", "무시"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.status_filter)
        
        # 기간 필터
        filter_layout.addWidget(QLabel("기간:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.start_date.setCalendarPopup(True)
        self.start_date.dateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.start_date)
        
        filter_layout.addWidget(QLabel("~"))
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.dateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.end_date)
        
        # 초기화 버튼
        reset_btn = QPushButton("초기화")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        reset_btn.clicked.connect(self.reset_filters)
        filter_layout.addWidget(reset_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        return group
    
    def create_history_table(self):
        """알림 기록 테이블 생성"""
        group = QGroupBox("📋 알림 기록")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        # 테이블 생성
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "시간", "유형", "코인", "메시지", "상태", "상세"
        ])
        
        # 테이블 스타일
        self.history_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                gridline-color: #e9ecef;
                alternate-background-color: #f8f9fa;
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
        header = self.history_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)    # 시간
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # 유형
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # 코인
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # 메시지
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)    # 상태
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)    # 상세
            
            self.history_table.setColumnWidth(0, 140)  # 시간
            self.history_table.setColumnWidth(1, 100)  # 유형
            self.history_table.setColumnWidth(2, 80)   # 코인
            self.history_table.setColumnWidth(4, 60)   # 상태
            self.history_table.setColumnWidth(5, 60)   # 상세
        
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.history_table)
        
        # 테이블 관리 버튼
        table_buttons_layout = QHBoxLayout()
        
        export_btn = QPushButton("📤 내보내기")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        export_btn.clicked.connect(self.export_history)
        table_buttons_layout.addWidget(export_btn)
        
        delete_btn = QPushButton("🗑️ 선택 삭제")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        delete_btn.clicked.connect(self.delete_selected_records)
        table_buttons_layout.addWidget(delete_btn)
        
        clear_btn = QPushButton("🧹 전체 삭제")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        clear_btn.clicked.connect(self.clear_all_records)
        table_buttons_layout.addWidget(clear_btn)
        
        table_buttons_layout.addStretch()
        layout.addLayout(table_buttons_layout)
        
        return group
    
    def create_stats_panel(self):
        """통계 정보 패널 생성"""
        group = QGroupBox("📊 통계 정보")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        layout = QHBoxLayout(group)
        
        # 총 알림 수
        self.total_alerts_label = QLabel("총 알림: 0개")
        self.total_alerts_label.setStyleSheet("font-size: 14px; color: #495057; font-weight: bold;")
        layout.addWidget(self.total_alerts_label)
        
        layout.addWidget(QLabel("|"))
        
        # 오늘 알림 수
        self.today_alerts_label = QLabel("오늘: 0개")
        self.today_alerts_label.setStyleSheet("font-size: 14px; color: #007bff;")
        layout.addWidget(self.today_alerts_label)
        
        layout.addWidget(QLabel("|"))
        
        # 가장 많은 알림 유형
        self.top_type_label = QLabel("주요 유형: --")
        self.top_type_label.setStyleSheet("font-size: 14px; color: #28a745;")
        layout.addWidget(self.top_type_label)
        
        layout.addWidget(QLabel("|"))
        
        # 최근 알림 시간
        self.last_alert_label = QLabel("최근 알림: --")
        self.last_alert_label.setStyleSheet("font-size: 14px; color: #6c757d;")
        layout.addWidget(self.last_alert_label)
        
        layout.addStretch()
        
        return group
    
    def load_sample_data(self):
        """샘플 데이터 로드"""
        # 샘플 알림 기록 생성
        sample_records = [
            {
                "id": 1,
                "timestamp": datetime.datetime.now() - datetime.timedelta(minutes=30),
                "type": "가격 알림",
                "coin": "BTC",
                "message": "BTC-KRW 가격이 45,000,000원을 돌파했습니다.",
                "status": "발생",
                "details": {"current_price": 45050000, "target_price": 45000000}
            },
            {
                "id": 2,
                "timestamp": datetime.datetime.now() - datetime.timedelta(hours=1),
                "type": "주문 체결 알림",
                "coin": "ETH",
                "message": "ETH-KRW 매수 주문이 체결되었습니다. (2.5 ETH)",
                "status": "발생",
                "details": {"order_type": "buy", "amount": 2.5, "price": 2800000}
            },
            {
                "id": 3,
                "timestamp": datetime.datetime.now() - datetime.timedelta(hours=2),
                "type": "기술적 지표 알림",
                "coin": "ADA",
                "message": "ADA-KRW RSI가 70을 초과했습니다. (현재: 72.5)",
                "status": "발생",
                "details": {"indicator": "RSI", "value": 72.5, "threshold": 70}
            },
            {
                "id": 4,
                "timestamp": datetime.datetime.now() - datetime.timedelta(hours=3),
                "type": "거래량 알림",
                "coin": "SOL",
                "message": "SOL-KRW 거래량이 평균 대비 3배 증가했습니다.",
                "status": "발생",
                "details": {"volume_ratio": 3.2, "current_volume": 15000000}
            },
            {
                "id": 5,
                "timestamp": datetime.datetime.now() - datetime.timedelta(days=1),
                "type": "시스템 상태 알림",
                "coin": "전체",
                "message": "API 연결이 일시적으로 중단되었습니다.",
                "status": "해결",
                "details": {"error_code": "CONNECTION_TIMEOUT", "duration": "5분"}
            }
        ]
        
        self.alert_records = sample_records
        self.filtered_records = sample_records.copy()
        self.update_table()
        self.update_stats()
    
    def add_alert_record(self, alert_data):
        """새 알림 기록 추가"""
        record = {
            "id": len(self.alert_records) + 1,
            "timestamp": alert_data.get("timestamp", datetime.datetime.now()),
            "type": alert_data.get("type", "알림"),
            "coin": alert_data.get("coin", ""),
            "message": alert_data.get("message", alert_data.get("description", "")),
            "status": alert_data.get("status", "발생"),
            "details": alert_data
        }
        
        self.alert_records.insert(0, record)  # 최신 순으로 추가
        self.apply_filters()  # 필터 적용하여 테이블 업데이트
        self.update_stats()
    
    def apply_filters(self):
        """필터 적용"""
        keyword = self.search_input.text().lower()
        type_filter = self.type_filter.currentText()
        status_filter = self.status_filter.currentText()
        
        # QDate를 Python date로 변환
        start_qdate = self.start_date.date()
        end_qdate = self.end_date.date()
        start_date = datetime.date(start_qdate.year(), start_qdate.month(), start_qdate.day())
        end_date = datetime.date(end_qdate.year(), end_qdate.month(), end_qdate.day())
        
        self.filtered_records = []
        
        for record in self.alert_records:
            # 키워드 필터
            if keyword and keyword not in record["message"].lower() and keyword not in record["coin"].lower():
                continue
            
            # 유형 필터
            if type_filter != "전체" and record["type"] != type_filter:
                continue
            
            # 상태 필터
            if status_filter != "전체" and record["status"] != status_filter:
                continue
            
            # 기간 필터
            record_date = record["timestamp"].date()
            if record_date < start_date or record_date > end_date:
                continue
            
            self.filtered_records.append(record)
        
        self.update_table()
    
    def update_table(self):
        """테이블 업데이트"""
        self.history_table.setRowCount(len(self.filtered_records))
        
        for row, record in enumerate(self.filtered_records):
            # 시간
            time_str = record["timestamp"].strftime("%m-%d %H:%M:%S")
            time_item = QTableWidgetItem(time_str)
            self.history_table.setItem(row, 0, time_item)
            
            # 유형
            type_item = QTableWidgetItem(record["type"])
            
            # 유형별 색상 설정
            if record["type"] == "가격 알림":
                type_item.setForeground(QColor("#007bff"))
            elif record["type"] == "주문 체결 알림":
                type_item.setForeground(QColor("#28a745"))
            elif record["type"] == "기술적 지표 알림":
                type_item.setForeground(QColor("#ffc107"))
            elif record["type"] == "거래량 알림":
                type_item.setForeground(QColor("#17a2b8"))
            elif record["type"] == "시스템 상태 알림":
                type_item.setForeground(QColor("#dc3545"))
            
            self.history_table.setItem(row, 1, type_item)
            
            # 코인
            coin_item = QTableWidgetItem(record["coin"])
            coin_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_table.setItem(row, 2, coin_item)
            
            # 메시지
            message_item = QTableWidgetItem(record["message"])
            self.history_table.setItem(row, 3, message_item)
            
            # 상태
            status_item = QTableWidgetItem(record["status"])
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if record["status"] == "발생":
                status_item.setForeground(QColor("#dc3545"))
            elif record["status"] == "해결":
                status_item.setForeground(QColor("#28a745"))
            else:
                status_item.setForeground(QColor("#6c757d"))
            
            self.history_table.setItem(row, 4, status_item)
            
            # 상세 버튼
            detail_btn = QPushButton("상세")
            detail_btn.setStyleSheet("""
                QPushButton {
                    background-color: #17a2b8;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #138496;
                }
            """)
            detail_btn.clicked.connect(lambda checked, r=row: self.show_detail(r))
            self.history_table.setCellWidget(row, 5, detail_btn)
    
    def update_stats(self):
        """통계 정보 업데이트"""
        total_count = len(self.alert_records)
        self.total_alerts_label.setText(f"총 알림: {total_count}개")
        
        # 오늘 알림 수
        today = datetime.date.today()
        today_count = sum(1 for record in self.alert_records 
                         if record["timestamp"].date() == today)
        self.today_alerts_label.setText(f"오늘: {today_count}개")
        
        # 가장 많은 알림 유형
        if self.alert_records:
            type_counts = {}
            for record in self.alert_records:
                type_name = record["type"]
                type_counts[type_name] = type_counts.get(type_name, 0) + 1
            
            if type_counts:
                # 가장 빈도가 높은 유형 찾기
                max_count = 0
                top_type = ""
                for type_name, count in type_counts.items():
                    if count > max_count:
                        max_count = count
                        top_type = type_name
                self.top_type_label.setText(f"주요 유형: {top_type}")
            else:
                self.top_type_label.setText("주요 유형: --")
            
            # 최근 알림 시간
            latest_record = max(self.alert_records, key=lambda x: x["timestamp"])
            last_time = latest_record["timestamp"].strftime("%m-%d %H:%M")
            self.last_alert_label.setText(f"최근 알림: {last_time}")
        else:
            self.top_type_label.setText("주요 유형: --")
            self.last_alert_label.setText("최근 알림: --")
    
    def show_detail(self, row):
        """상세 정보 표시"""
        if 0 <= row < len(self.filtered_records):
            record = self.filtered_records[row]
            dialog = AlertDetailDialog(record, self)
            dialog.exec()
    
    def reset_filters(self):
        """필터 초기화"""
        self.search_input.clear()
        self.type_filter.setCurrentText("전체")
        self.status_filter.setCurrentText("전체")
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.end_date.setDate(QDate.currentDate())
        self.apply_filters()
    
    def export_history(self):
        """기록 내보내기"""
        QMessageBox.information(
            self,
            "내보내기",
            "알림 기록을 CSV 파일로 내보내는 기능은 준비 중입니다."
        )
    
    def delete_selected_records(self):
        """선택된 기록 삭제"""
        selected_rows = set()
        for item in self.history_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.warning(self, "선택 오류", "삭제할 기록을 선택해주세요.")
            return
        
        reply = QMessageBox.question(
            self,
            "기록 삭제",
            f"{len(selected_rows)}개의 기록을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 선택된 기록들을 원본에서 제거
            selected_records = [self.filtered_records[row] for row in sorted(selected_rows)]
            for record in selected_records:
                if record in self.alert_records:
                    self.alert_records.remove(record)
            
            self.apply_filters()
            self.update_stats()
    
    def clear_all_records(self):
        """모든 기록 삭제"""
        reply = QMessageBox.critical(
            self,
            "전체 삭제",
            "모든 알림 기록을 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.alert_records.clear()
            self.filtered_records.clear()
            self.update_table()
            self.update_stats()

class AlertDetailDialog(QDialog):
    """알림 상세 정보 대화상자"""
    
    def __init__(self, record, parent=None):
        super().__init__(parent)
        self.record = record
        self.setWindowTitle("알림 상세 정보")
        self.setModal(True)
        self.resize(500, 400)
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 기본 정보
        form = QFormLayout()
        
        form.addRow("ID:", QLabel(str(self.record["id"])))
        form.addRow("시간:", QLabel(self.record["timestamp"].strftime("%Y-%m-%d %H:%M:%S")))
        form.addRow("유형:", QLabel(self.record["type"]))
        form.addRow("코인:", QLabel(self.record["coin"]))
        form.addRow("상태:", QLabel(self.record["status"]))
        
        layout.addLayout(form)
        
        # 메시지
        layout.addWidget(QLabel("메시지:"))
        message_text = QTextEdit()
        message_text.setPlainText(self.record["message"])
        message_text.setReadOnly(True)
        message_text.setMaximumHeight(80)
        layout.addWidget(message_text)
        
        # 상세 정보
        if self.record.get("details"):
            layout.addWidget(QLabel("상세 정보:"))
            details_text = QTextEdit()
            details_str = "\n".join([f"{k}: {v}" for k, v in self.record["details"].items()])
            details_text.setPlainText(details_str)
            details_text.setReadOnly(True)
            layout.addWidget(details_text)
        
        # 버튼
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
