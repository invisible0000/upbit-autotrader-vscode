"""
Asset Screener Screen
업비트 KRW마켓 코인 종목 스크리닝 화면
- UI/UX 개선안이 최종 반영된 버전
"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QGroupBox, QTableWidget, QTableWidgetItem, QSpinBox, 
    QMenu, QProgressBar, QLineEdit
)
from PyQt6.QtCore import Qt, QSize

class AssetScreenerScreen(QWidget):
    def __init__(self, parent=None):
        """클래스가 생성될 때 가장 먼저 실행되는 생성자입니다."""
        super().__init__(parent)
        self.setWindowTitle("자산 스크리닝 시스템")
        self.setGeometry(100, 100, 1400, 800) # 창 크기 확장
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 1. 최상단: 제목, 마켓 선택, 도움말 버튼 (개선된 배치)
        top_bar = QHBoxLayout()
        self.title_label = QLabel("자산 스크리닝 (Upbit KRW마켓)")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        top_bar.addWidget(self.title_label)
        top_bar.addStretch(1) # Stretch로 컨트롤들을 오른쪽으로
        self.market_combo = QComboBox()
        self.market_combo.addItems(["KRW마켓", "BTC마켓", "USDT마켓"])
        top_bar.addWidget(self.market_combo)
        self.help_btn = QPushButton("도움말/튜토리얼")
        top_bar.addWidget(self.help_btn)
        main_layout.addLayout(top_bar)

        # 2. 중간: 좌우 2분할 (필터/조건)
        mid_split_layout = QHBoxLayout()

        # 왼쪽: 기본 필터 그룹박스
        self.create_basic_filters_group(mid_split_layout)

        # 오른쪽: 사용자 조건 그룹박스
        self.create_user_conditions_group(mid_split_layout)

        main_layout.addLayout(mid_split_layout)

        # 3. 하단: 결과 테이블 및 액션 버튼
        self.create_results_area(main_layout)

        # 4. 이벤트 연결
        self.connect_events()

    def create_basic_filters_group(self, parent_layout):
        """(수정됨) 왼쪽 기본 필터 영역 생성"""
        left_box = QGroupBox("기본 필터")
        left_layout = QVBoxLayout(left_box)
        
        # 가격/거래량 필터
        price_row = QHBoxLayout()
        price_row.addWidget(QLabel("최소 가격:"))
        self.price_min = QSpinBox(); self.price_min.setMaximum(100000000)
        price_row.addWidget(self.price_min)
        left_layout.addLayout(price_row)

        volume_row = QHBoxLayout()
        volume_row.addWidget(QLabel("최소 거래량:"))
        self.volume_min = QSpinBox(); self.volume_min.setMaximum(1000000000)
        volume_row.addWidget(self.volume_min)
        left_layout.addLayout(volume_row)
        
        left_layout.addSpacing(15)

        # --- 개선된 기술적 지표 필터 빌더 ---
        tech_filter_builder_layout = QVBoxLayout()
        tech_filter_builder_layout.addWidget(QLabel("기술적 지표 필터 추가:"))
        
        builder_row = QHBoxLayout()
        self.tech_indicator_combo = QComboBox(); self.tech_indicator_combo.addItems(["RSI", "MACD", "이동평균"])
        self.tech_operator_combo = QComboBox(); self.tech_operator_combo.addItems([">", "<", ">=", "<=", "="])
        self.tech_value_spinbox = QSpinBox(); self.tech_value_spinbox.setRange(0, 100)
        self.add_filter_btn = QPushButton("추가 +")
        
        builder_row.addWidget(self.tech_indicator_combo)
        builder_row.addWidget(self.tech_operator_combo)
        builder_row.addWidget(self.tech_value_spinbox)
        builder_row.addWidget(self.add_filter_btn)
        
        tech_filter_builder_layout.addLayout(builder_row)
        left_layout.addLayout(tech_filter_builder_layout)
        
        # 추가된 필터들이 표시될 영역
        self.added_filters_layout = QVBoxLayout()
        left_layout.addLayout(self.added_filters_layout)
        
        left_layout.addStretch(1) # 위젯들을 위로 정렬
        parent_layout.addWidget(left_box, stretch=1)

    def create_user_conditions_group(self, parent_layout):
        """(수정됨) 오른쪽 사용자 조건 영역 생성"""
        right_box = QGroupBox("사용자 조건")
        right_layout = QVBoxLayout(right_box)
        
        # --- 개선된 사용자 조건 빌더 ---
        right_layout.addWidget(QLabel("사용자 조건식 추가:"))
        
        condition_builder_layout = QHBoxLayout()
        self.user_metric_combo = QComboBox(); self.user_metric_combo.addItems(["가격", "거래량", "시가총액", "RSI"])
        self.user_operator_combo = QComboBox(); self.user_operator_combo.addItems([">", "<", ">=", "<=", "="])
        self.user_value_input = QLineEdit("0")
        self.add_user_cond_btn = QPushButton("추가 +")
        
        condition_builder_layout.addWidget(self.user_metric_combo)
        condition_builder_layout.addWidget(self.user_operator_combo)
        condition_builder_layout.addWidget(self.user_value_input)
        condition_builder_layout.addWidget(self.add_user_cond_btn)
        
        right_layout.addLayout(condition_builder_layout)
        
        # 추가된 조건들이 표시될 영역
        self.added_conditions_layout = QVBoxLayout()
        right_layout.addLayout(self.added_conditions_layout)

        right_layout.addStretch(1)
        parent_layout.addWidget(right_box, stretch=1)

    def create_results_area(self, parent_layout):
        """하단 결과 테이블 및 액션 버튼 영역 생성"""
        self.result_table = QTableWidget(10, 8) # 행 개수 조정
        self.result_table.setHorizontalHeaderLabels(["자산명", "심볼", "24h변동", "거래량", "시가총액", "추세", "RSI", "MACD"])
        parent_layout.addWidget(self.result_table)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.save_button = QPushButton("결과 저장")
        self.export_button = QPushButton("CSV 내보내기")
        self.portfolio_btn = QPushButton("포트폴리오 구성")
        # --- 버튼 비활성화 상태로 시작 ---
        self.save_button.setEnabled(False)
        self.export_button.setEnabled(False)
        self.portfolio_btn.setEnabled(False)
        btn_row.addWidget(self.save_button)
        btn_row.addWidget(self.export_button)
        btn_row.addWidget(self.portfolio_btn)
        parent_layout.addLayout(btn_row)

    def add_filter(self):
        """'기본 필터' 영역에 설정된 기술적 지표 필터를 리스트에 추가"""
        indicator = self.tech_indicator_combo.currentText()
        operator = self.tech_operator_combo.currentText()
        value = self.tech_value_spinbox.value()
        
        filter_text = f"{indicator} {operator} {value}"
        
        filter_widget = QWidget()
        layout = QHBoxLayout(filter_widget)
        layout.setContentsMargins(0, 5, 0, 5)
        
        label = QLabel(filter_text)
        del_btn = QPushButton("X")
        del_btn.setFixedSize(QSize(22, 22))
        del_btn.setStyleSheet("color: red; font-weight: bold;")
        
        layout.addWidget(label)
        layout.addStretch(1)
        layout.addWidget(del_btn)
        
        # 'X' 버튼을 누르면 해당 필터를 제거하고 테이블 갱신
        del_btn.clicked.connect(lambda: self.remove_filter(filter_widget))
        
        self.added_filters_layout.addWidget(filter_widget)
        # 필터 추가 후 테이블 갱신
        self.refresh_table_data()
        
    def remove_filter(self, filter_widget):
        """필터 위젯을 제거하고 테이블 데이터 갱신"""
        filter_widget.deleteLater()
        self.refresh_table_data()
        
    def add_user_condition(self):
        """'사용자 조건' 영역에 설정된 조건식을 리스트에 추가"""
        # 입력값 검증
        value = self.user_value_input.text().strip()
        if not value or not self.is_valid_number(value):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "입력 오류", "올바른 숫자값을 입력하세요.")
            return
            
        if self.added_conditions_layout.count() > 0:
            # 첫 조건이 아닐 경우 AND/OR 연산자 추가
            logic_combo = QComboBox()
            logic_combo.addItems(["AND", "OR"])
            logic_combo.setFixedWidth(60)
            logic_combo.currentIndexChanged.connect(self.refresh_table_data)  # 논리 연산자 변경 시 갱신
            self.added_conditions_layout.addWidget(logic_combo, alignment=Qt.AlignmentFlag.AlignCenter)

        metric = self.user_metric_combo.currentText()
        operator = self.user_operator_combo.currentText()
        
        condition_text = f"{metric} {operator} {value}"
        
        cond_widget = QWidget()
        layout = QHBoxLayout(cond_widget)
        layout.setContentsMargins(0, 5, 0, 5)
        
        label = QLabel(condition_text)
        del_btn = QPushButton("X")
        del_btn.setFixedSize(QSize(22, 22))
        del_btn.setStyleSheet("color: red; font-weight: bold;")
        
        layout.addWidget(label)
        layout.addStretch(1)
        layout.addWidget(del_btn)
        
        # 'X' 버튼을 누르면 해당 조건 위젯과 논리연산자를 제거하고 테이블 갱신
        del_btn.clicked.connect(lambda: self.remove_condition_with_logic(cond_widget))

        self.added_conditions_layout.addWidget(cond_widget)
        # 조건 추가 후 테이블 갱신
        self.refresh_table_data()
        
    def is_valid_number(self, value):
        """입력값이 유효한 숫자인지 검증"""
        try:
            float(value)
            return True
        except ValueError:
            return False

    def remove_condition_with_logic(self, cond_widget):
        """조건식과 그 위의 논리 연산자를 함께 제거하는 스마트한 함수"""
        layout = self.added_conditions_layout
        index = layout.indexOf(cond_widget)
        
        # 위젯 자신을 삭제
        cond_widget.deleteLater()
        
        if index > 0: # 첫 번째 조건이 아니라면, 그 위의 논리 연산자도 함께 제거
            logic_widget_item = layout.itemAt(index - 1)
            if logic_widget_item:
                logic_widget = logic_widget_item.widget()
                if isinstance(logic_widget, QComboBox): # 논리 연산자 콤보박스가 맞는지 확인
                    logic_widget.deleteLater()
        
        # 조건 제거 후 테이블 갱신
        self.refresh_table_data()

    def save_results(self):
        """결과 저장 버튼 클릭 시 호출되는 핸들러"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "결과 저장",
            "",
            "JSON 파일 (*.json);;텍스트 파일 (*.txt)"
        )
        if file_path:
            try:
                # TODO: 실제 저장 로직 구현
                print(f"[DEBUG] 결과를 {file_path}에 저장")
                self.show_status_message("결과가 성공적으로 저장되었습니다.")
            except Exception as e:
                self.show_status_message(f"저장 중 오류 발생: {str(e)}", error=True)

    def export_csv(self):
        """CSV 내보내기 버튼 클릭 시 호출되는 핸들러"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "CSV 내보내기",
            "",
            "CSV 파일 (*.csv)"
        )
        if file_path:
            try:
                # TODO: 실제 CSV 내보내기 로직 구현
                print(f"[DEBUG] 결과를 {file_path}에 CSV로 내보내기")
                self.show_status_message("CSV 파일이 성공적으로 생성되었습니다.")
            except Exception as e:
                self.show_status_message(f"내보내기 중 오류 발생: {str(e)}", error=True)

    def make_portfolio(self):
        """포트폴리오 구성 버튼 클릭 시 호출되는 핸들러"""
        # TODO: 포트폴리오 구성 화면으로 전환 또는 대화상자 표시
        print("[DEBUG] 포트폴리오 구성 요청")
        self.show_status_message("포트폴리오 구성 기능 준비 중...")

    def show_status_message(self, message, error=False):
        """상태/에러 메시지를 사용자에게 표시"""
        from PyQt6.QtWidgets import QMessageBox
        if error:
            QMessageBox.critical(self, "오류", message)
        else:
            QMessageBox.information(self, "알림", message)

    def connect_events(self):
        """이벤트 핸들러 연결"""
        # 최상단 컨트롤 이벤트
        self.market_combo.currentIndexChanged.connect(self.on_market_changed)
        self.help_btn.clicked.connect(self.show_help)
        
        # 필터/조건 이벤트
        self.add_filter_btn.clicked.connect(self.add_filter)
        self.add_user_cond_btn.clicked.connect(self.add_user_condition)
        
        # 가격/거래량 변경 이벤트
        self.price_min.valueChanged.connect(self.on_filter_value_changed)
        self.volume_min.valueChanged.connect(self.on_filter_value_changed)
        
        # 결과 액션 버튼 이벤트
        self.save_button.clicked.connect(self.save_results)
        self.export_button.clicked.connect(self.export_csv)
        self.portfolio_btn.clicked.connect(self.make_portfolio)
    
    def on_market_changed(self, index):
        """마켓 변경 시 호출되는 핸들러"""
        market = self.market_combo.currentText()
        self.title_label.setText(f"자산 스크리닝 (Upbit {market})")
        # TODO: 선택된 마켓에 따라 테이블 데이터 갱신
        self.refresh_table_data()
    
    def show_help(self):
        """도움말/튜토리얼 버튼 클릭 시 호출되는 핸들러"""
        help_text = """
        [자산 스크리닝 시스템 사용 가이드]
        
        1. 기본 필터 사용법
        - 최소 가격/거래량 설정
        - 기술적 지표 필터 추가/삭제
        
        2. 사용자 조건식 사용법
        - 원하는 조건 설정 후 추가
        - AND/OR 로 조건 조합
        - X 버튼으로 조건 삭제
        
        3. 결과 활용
        - 결과 저장/CSV 내보내기
        - 포트폴리오 구성에 활용
        """
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "도움말/튜토리얼", help_text)
    
    def on_filter_value_changed(self):
        """가격/거래량 필터값 변경 시 호출되는 핸들러"""
        # 필터값이 변경될 때마다 결과 테이블 갱신
        self.refresh_table_data()
    
    def refresh_table_data(self):
        """테이블 데이터를 현재 필터/조건에 맞게 갱신"""
        # TODO: 실제 데이터 조회/필터링 로직 구현
        print(f"[DEBUG] 테이블 데이터 갱신 요청")
        print(f"- 선택된 마켓: {self.market_combo.currentText()}")
        print(f"- 최소 가격: {self.price_min.value()}")
        print(f"- 최소 거래량: {self.volume_min.value()}")
        # 테이블 데이터가 있을 때만 버튼 활성화
        has_data = True  # TODO: 실제 데이터 존재 여부 확인
        self.save_button.setEnabled(has_data)
        self.export_button.setEnabled(has_data)
        self.portfolio_btn.setEnabled(has_data)

# 테스트를 위한 실행 코드
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AssetScreenerScreen()
    window.show()
    sys.exit(app.exec())