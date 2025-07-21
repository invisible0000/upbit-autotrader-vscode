from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QTableWidgetItem, 
    QTabWidget, QLabel, QGroupBox, QSplitter, QComboBox, 
    QDateEdit, QFormLayout
)
from PyQt6.QtCore import Qt, QDate
from .common.components import StyledTableWidget, PrimaryButton, SecondaryButton, DangerButton
from ...business_logic.strategy.strategy_combination import CombinationManager, StrategyConfig

class StrategyManagementScreen(QWidget):
    """역할 기반 전략 관리 화면 - 진입/관리/조합 3탭 구조"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 전략 조합 매니저 초기화
        self.combination_manager = CombinationManager("ui_strategy_combinations.json")
        
        self.init_ui()
        self.load_initial_data()
        
    def init_ui(self):
        """UI 초기화 - 3탭 구조 구성"""
        layout = QVBoxLayout(self)
        
        # 상단 툴바 (검색/필터)
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # 3탭 구조
        self.tab_widget = QTabWidget()
        
        # 1) 진입 전략 탭
        entry_tab = self.create_entry_strategy_tab()
        self.tab_widget.addTab(entry_tab, "📈 진입 전략")
        
        # 2) 관리 전략 탭  
        management_tab = self.create_management_strategy_tab()
        self.tab_widget.addTab(management_tab, "🛡️ 관리 전략")
        
        # 3) 전략 조합 탭
        combination_tab = self.create_strategy_combination_tab()
        self.tab_widget.addTab(combination_tab, "🔗 전략 조합")
        
        layout.addWidget(self.tab_widget)
        
    def create_toolbar(self):
        """상단 툴바 생성"""
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        
        # 검색/필터 기능 추후 구현
        info_label = QLabel("💡 진입 전략으로 포지션을 열고, 관리 전략으로 리스크를 관리하세요")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
        toolbar_layout.addWidget(info_label)
        toolbar_layout.addStretch()
        
        return toolbar_widget
        
    def create_entry_strategy_tab(self):
        """진입 전략 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 진입 전략 설명
        description = QLabel("📈 진입 전략: 포지션이 없는 상태에서 최초 진입 신호를 생성합니다")
        description.setStyleSheet("font-weight: bold; color: #2196F3; padding: 10px; background: #E3F2FD; border-radius: 5px;")
        layout.addWidget(description)
        
        # 진입 전략 테이블
        self.entry_strategy_table = StyledTableWidget(rows=6, columns=4)
        self.entry_strategy_table.setHorizontalHeaderLabels(["전략명", "설명", "신호 유형", "상태"])
        layout.addWidget(self.entry_strategy_table)
        
        # 버튼 그룹
        button_layout = QHBoxLayout()
        self.create_entry_button = PrimaryButton("📈 진입 전략 생성")
        self.edit_entry_button = SecondaryButton("✏️ 수정")
        self.delete_entry_button = DangerButton("🗑️ 삭제")
        self.test_entry_button = SecondaryButton("🧪 백테스트")
        
        button_layout.addWidget(self.create_entry_button)
        button_layout.addWidget(self.edit_entry_button)
        button_layout.addWidget(self.delete_entry_button)
        button_layout.addWidget(self.test_entry_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return tab
        
    def create_management_strategy_tab(self):
        """관리 전략 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 관리 전략 설명
        description = QLabel("🛡️ 관리 전략: 이미 진입한 포지션의 리스크 관리 및 수익 극대화를 담당합니다")
        description.setStyleSheet("font-weight: bold; color: #FF9800; padding: 10px; background: #FFF3E0; border-radius: 5px;")
        layout.addWidget(description)
        
        # 관리 전략 테이블
        self.management_strategy_table = StyledTableWidget(rows=6, columns=4)
        self.management_strategy_table.setHorizontalHeaderLabels(["전략명", "설명", "신호 유형", "상태"])
        layout.addWidget(self.management_strategy_table)
        
        # 버튼 그룹
        button_layout = QHBoxLayout()
        self.create_mgmt_button = PrimaryButton("🛡️ 관리 전략 생성")
        self.edit_mgmt_button = SecondaryButton("✏️ 수정")
        self.delete_mgmt_button = DangerButton("🗑️ 삭제")
        self.test_mgmt_button = SecondaryButton("🧪 백테스트")
        
        button_layout.addWidget(self.create_mgmt_button)
        button_layout.addWidget(self.edit_mgmt_button)
        button_layout.addWidget(self.delete_mgmt_button)
        button_layout.addWidget(self.test_mgmt_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return tab
        
    def create_strategy_combination_tab(self):
        """전략 조합 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 조합 전략 설명
        description = QLabel("🔗 전략 조합: 1개 진입 전략 + 0~N개 관리 전략을 조합하여 완성된 매매 시스템을 구성합니다")
        description.setStyleSheet("font-weight: bold; color: #4CAF50; padding: 10px; background: #E8F5E8; border-radius: 5px;")
        layout.addWidget(description)
        
        # 3분할 레이아웃 (좌측: 조합 목록 / 중앙: 조합 에디터 / 우측: 백테스트 결과)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 좌측 패널 - 조합 목록 (25%)
        left_panel = self.create_combination_list_panel()
        splitter.addWidget(left_panel)
        
        # 중앙 패널 - 조합 에디터 (50%)
        center_panel = self.create_combination_editor_panel()
        splitter.addWidget(center_panel)
        
        # 우측 패널 - 백테스트 결과 (25%)
        right_panel = self.create_backtest_result_panel()
        splitter.addWidget(right_panel)
        
        # 패널 크기 비율 설정
        splitter.setSizes([250, 500, 250])
        
        layout.addWidget(splitter)
        
        return tab
    
    def create_combination_list_panel(self):
        """좌측 조합 목록 패널"""
        panel = QGroupBox("저장된 조합")
        layout = QVBoxLayout(panel)
        
        # 조합 목록 테이블
        self.combination_list_table = StyledTableWidget(rows=5, columns=2)
        self.combination_list_table.setHorizontalHeaderLabels(["조합명", "구성"])
        layout.addWidget(self.combination_list_table)
        
        # 버튼들
        button_layout = QVBoxLayout()
        self.new_combination_button = PrimaryButton("🆕 새 조합")
        self.delete_combination_button = DangerButton("🗑️ 삭제")
        
        button_layout.addWidget(self.new_combination_button)
        button_layout.addWidget(self.delete_combination_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return panel
        
    def create_combination_editor_panel(self):
        """중앙 조합 에디터 패널"""
        panel = QGroupBox("전략 조합 에디터")
        layout = QVBoxLayout(panel)
        
        # 조합 기본 정보
        info_group = QGroupBox("기본 정보")
        info_layout = QVBoxLayout(info_group)
        
        self.combination_name_label = QLabel("조합명: (새 조합)")
        self.combination_desc_label = QLabel("설명: 진입 전략과 관리 전략을 조합하세요")
        
        info_layout.addWidget(self.combination_name_label)
        info_layout.addWidget(self.combination_desc_label)
        layout.addWidget(info_group)
        
        # 진입 전략 선택 (필수, 1개만)
        entry_group = QGroupBox("📈 진입 전략 선택 (필수, 1개)")
        entry_layout = QVBoxLayout(entry_group)
        
        self.entry_selection_table = StyledTableWidget(rows=3, columns=3)
        self.entry_selection_table.setHorizontalHeaderLabels(["선택", "전략명", "설명"])
        entry_layout.addWidget(self.entry_selection_table)
        layout.addWidget(entry_group)
        
        # 관리 전략 선택 (선택, 0~N개)
        mgmt_group = QGroupBox("🛡️ 관리 전략 선택 (선택, 0~5개)")
        mgmt_layout = QVBoxLayout(mgmt_group)
        
        self.mgmt_selection_table = StyledTableWidget(rows=3, columns=4)
        self.mgmt_selection_table.setHorizontalHeaderLabels(["선택", "전략명", "설명", "우선순위"])
        mgmt_layout.addWidget(self.mgmt_selection_table)
        layout.addWidget(mgmt_group)
        
        # 조합 설정
        config_group = QGroupBox("⚙️ 조합 설정")
        config_layout = QVBoxLayout(config_group)
        
        self.execution_order_label = QLabel("실행 순서: 병렬 (Parallel)")
        self.conflict_resolution_label = QLabel("충돌 해결: 보수적 (Conservative)")
        
        config_layout.addWidget(self.execution_order_label)
        config_layout.addWidget(self.conflict_resolution_label)
        layout.addWidget(config_group)
        
        # 저장 버튼
        save_layout = QHBoxLayout()
        self.save_combination_button = PrimaryButton("💾 조합 저장")
        self.preview_combination_button = SecondaryButton("👁️ 미리보기")
        
        save_layout.addWidget(self.save_combination_button)
        save_layout.addWidget(self.preview_combination_button)
        save_layout.addStretch()
        
        layout.addLayout(save_layout)
        
        return panel
        
    def create_backtest_result_panel(self):
        """우측 백테스트 결과 패널"""
        panel = QGroupBox("백테스트 결과")
        layout = QVBoxLayout(panel)
        
        # 조합 성과 요약
        performance_group = QGroupBox("성과 요약")
        performance_layout = QVBoxLayout(performance_group)
        
        self.total_return_label = QLabel("총 수익률: -")
        self.win_rate_label = QLabel("승률: -")
        self.sharpe_ratio_label = QLabel("샤프 비율: -")
        self.max_drawdown_label = QLabel("최대 낙폭: -")
        
        performance_layout.addWidget(self.total_return_label)
        performance_layout.addWidget(self.win_rate_label)
        performance_layout.addWidget(self.sharpe_ratio_label)
        performance_layout.addWidget(self.max_drawdown_label)
        layout.addWidget(performance_group)
        
        # 개별 전략 기여도
        contribution_group = QGroupBox("전략 기여도")
        contribution_layout = QVBoxLayout(contribution_group)
        
        self.entry_contribution_label = QLabel("진입 전략: -")
        self.mgmt_contribution_label = QLabel("관리 전략: -")
        
        contribution_layout.addWidget(self.entry_contribution_label)
        contribution_layout.addWidget(self.mgmt_contribution_label)
        layout.addWidget(contribution_group)
        
        # 백테스트 설정
        backtest_settings_group = QGroupBox("백테스트 설정")
        settings_layout = QFormLayout(backtest_settings_group)
        
        # 데이터베이스 선택
        self.db_selector = QComboBox()
        self.db_selector.addItems([
            "업비트 실시간 데이터",
            "업비트 과거 데이터 (1일)",
            "업비트 과거 데이터 (1시간)",
            "업비트 과거 데이터 (15분)",
            "샘플 데이터 (테스트용)"
        ])
        self.db_selector.setCurrentIndex(4)  # 기본값: 샘플 데이터
        settings_layout.addRow("📊 데이터 소스:", self.db_selector)
        
        # 시작일 선택
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))  # 30일 전
        self.start_date_edit.setCalendarPopup(True)
        settings_layout.addRow("📅 시작일:", self.start_date_edit)
        
        # 종료일 선택
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())  # 오늘
        self.end_date_edit.setCalendarPopup(True)
        settings_layout.addRow("📅 종료일:", self.end_date_edit)
        
        # 초기 자본금
        self.initial_capital_combo = QComboBox()
        self.initial_capital_combo.setEditable(True)
        self.initial_capital_combo.addItems([
            "1,000,000",
            "5,000,000", 
            "10,000,000",
            "50,000,000",
            "100,000,000"
        ])
        self.initial_capital_combo.setCurrentText("1,000,000")
        settings_layout.addRow("💰 초기 자본:", self.initial_capital_combo)
        
        layout.addWidget(backtest_settings_group)
        
        # 백테스트 실행 버튼
        backtest_layout = QVBoxLayout()
        self.run_backtest_button = PrimaryButton("🚀 백테스트 실행")
        self.export_result_button = SecondaryButton("📊 결과 내보내기")
        
        backtest_layout.addWidget(self.run_backtest_button)
        backtest_layout.addWidget(self.export_result_button)
        backtest_layout.addStretch()
        
        layout.addLayout(backtest_layout)
        
        return panel
    
    def load_initial_data(self):
        """초기 데이터 로딩"""
        self.load_entry_strategies()
        self.load_management_strategies()
        self.load_strategy_combinations()
        self.connect_events()
    
    def load_entry_strategies(self):
        """진입 전략 데이터 로딩"""
        # 샘플 진입 전략 데이터
        entry_strategies = [
            {"name": "이동평균 교차", "desc": "골든크로스/데드크로스 신호", "signal": "BUY/SELL", "status": "활성"},
            {"name": "RSI 과매수/과매도", "desc": "RSI 30/70 돌파 신호", "signal": "BUY/SELL", "status": "활성"},
            {"name": "볼린저 밴드", "desc": "밴드 터치 후 반전 신호", "signal": "BUY/SELL", "status": "비활성"},
            {"name": "변동성 돌파", "desc": "래리 윌리엄스 돌파", "signal": "BUY/SELL", "status": "활성"},
            {"name": "MACD 교차", "desc": "MACD 라인 교차 신호", "signal": "BUY/SELL", "status": "비활성"},
            {"name": "스토캐스틱", "desc": "%K와 %D 라인 교차", "signal": "BUY/SELL", "status": "활성"}
        ]
        
        self.entry_strategy_table.setRowCount(len(entry_strategies))
        for i, strategy in enumerate(entry_strategies):
            self.entry_strategy_table.setItem(i, 0, QTableWidgetItem(strategy["name"]))
            self.entry_strategy_table.setItem(i, 1, QTableWidgetItem(strategy["desc"]))
            self.entry_strategy_table.setItem(i, 2, QTableWidgetItem(strategy["signal"]))
            self.entry_strategy_table.setItem(i, 3, QTableWidgetItem(strategy["status"]))
            
        # 진입 전략 선택 테이블에도 데이터 추가
        self.entry_selection_table.setRowCount(len(entry_strategies))
        for i, strategy in enumerate(entry_strategies):
            self.entry_selection_table.setItem(i, 0, QTableWidgetItem("☐"))
            self.entry_selection_table.setItem(i, 1, QTableWidgetItem(strategy["name"]))
            self.entry_selection_table.setItem(i, 2, QTableWidgetItem(strategy["desc"]))
    
    def load_management_strategies(self):
        """관리 전략 데이터 로딩"""
        # 샘플 관리 전략 데이터
        mgmt_strategies = [
            {"name": "물타기", "desc": "하락 시 추가 매수", "signal": "ADD_BUY", "status": "활성"},
            {"name": "불타기", "desc": "상승 시 추가 매수", "signal": "ADD_BUY", "status": "활성"},
            {"name": "트레일링 스탑", "desc": "동적 손절가 조정", "signal": "UPDATE_STOP", "status": "활성"},
            {"name": "고정 익절/손절", "desc": "고정 % 도달 시 청산", "signal": "CLOSE_POSITION", "status": "활성"},
            {"name": "부분 청산", "desc": "단계별 익절", "signal": "ADD_SELL", "status": "비활성"},
            {"name": "시간 기반 청산", "desc": "최대 보유 기간 청산", "signal": "CLOSE_POSITION", "status": "활성"}
        ]
        
        self.management_strategy_table.setRowCount(len(mgmt_strategies))
        for i, strategy in enumerate(mgmt_strategies):
            self.management_strategy_table.setItem(i, 0, QTableWidgetItem(strategy["name"]))
            self.management_strategy_table.setItem(i, 1, QTableWidgetItem(strategy["desc"]))
            self.management_strategy_table.setItem(i, 2, QTableWidgetItem(strategy["signal"]))
            self.management_strategy_table.setItem(i, 3, QTableWidgetItem(strategy["status"]))
            
        # 관리 전략 선택 테이블에도 데이터 추가
        self.mgmt_selection_table.setRowCount(len(mgmt_strategies))
        for i, strategy in enumerate(mgmt_strategies):
            self.mgmt_selection_table.setItem(i, 0, QTableWidgetItem("☐"))
            self.mgmt_selection_table.setItem(i, 1, QTableWidgetItem(strategy["name"]))
            self.mgmt_selection_table.setItem(i, 2, QTableWidgetItem(strategy["desc"]))
            self.mgmt_selection_table.setItem(i, 3, QTableWidgetItem("1"))
    
    def load_strategy_combinations(self):
        """전략 조합 데이터 로딩 - 실제 CombinationManager 사용"""
        # 실제 저장된 조합이 없으면 샘플 생성
        combinations = self.combination_manager.get_all_combinations()
        
        if not combinations:
            print("💡 저장된 조합이 없어 샘플 조합을 생성합니다")
            samples = self.combination_manager.get_sample_combinations()
            for combo in samples:
                self.combination_manager.combinations[combo.combination_id] = combo
            self.combination_manager.save_combinations()
            combinations = samples
        
        # UI 테이블에 데이터 로딩
        self.combination_list_table.setRowCount(len(combinations))
        for i, combo in enumerate(combinations):
            self.combination_list_table.setItem(i, 0, QTableWidgetItem(combo.name))
            self.combination_list_table.setItem(i, 1, QTableWidgetItem(combo.get_summary()))
        
        print(f"✅ 전략 조합 {len(combinations)}개 UI 로딩 완료")
    
    def connect_events(self):
        """이벤트 연결"""
        # 진입 전략 탭 이벤트
        self.create_entry_button.clicked.connect(self.create_entry_strategy)
        self.edit_entry_button.clicked.connect(self.edit_entry_strategy)
        self.delete_entry_button.clicked.connect(self.delete_entry_strategy)
        self.test_entry_button.clicked.connect(self.test_entry_strategy)
        
        # 관리 전략 탭 이벤트
        self.create_mgmt_button.clicked.connect(self.create_management_strategy)
        self.edit_mgmt_button.clicked.connect(self.edit_management_strategy)
        self.delete_mgmt_button.clicked.connect(self.delete_management_strategy)
        self.test_mgmt_button.clicked.connect(self.test_management_strategy)
        
        # 전략 조합 탭 이벤트
        self.new_combination_button.clicked.connect(self.create_new_combination)
        self.delete_combination_button.clicked.connect(self.delete_combination)
        self.save_combination_button.clicked.connect(self.save_combination)
        self.preview_combination_button.clicked.connect(self.preview_combination)
        self.run_backtest_button.clicked.connect(self.run_combination_backtest)
        self.export_result_button.clicked.connect(self.export_backtest_result)
        
        # 조합 목록 선택 이벤트
        self.combination_list_table.cellClicked.connect(self.on_combination_selected)
        
        # 체크박스 클릭 이벤트
        self.entry_selection_table.cellClicked.connect(self.on_entry_selection_clicked)
        self.mgmt_selection_table.cellClicked.connect(self.on_mgmt_selection_clicked)
    
    # ===== 진입 전략 관련 메서드 =====
    def create_entry_strategy(self):
        """진입 전략 생성"""
        print("[UI] 📈 진입 전략 생성 다이얼로그 열기")
        # TODO: 진입 전략 생성 다이얼로그 구현
        
    def edit_entry_strategy(self):
        """진입 전략 수정"""
        current_row = self.entry_strategy_table.currentRow()
        if current_row >= 0:
            strategy_name = self.entry_strategy_table.item(current_row, 0).text()
            print(f"[UI] ✏️ 진입 전략 수정: {strategy_name}")
            # TODO: 진입 전략 수정 다이얼로그 구현
        
    def delete_entry_strategy(self):
        """진입 전략 삭제"""
        current_row = self.entry_strategy_table.currentRow()
        if current_row >= 0:
            strategy_name = self.entry_strategy_table.item(current_row, 0).text()
            print(f"[UI] 🗑️ 진입 전략 삭제: {strategy_name}")
            # TODO: 삭제 확인 다이얼로그 후 삭제 실행
            
    def test_entry_strategy(self):
        """진입 전략 백테스트"""
        current_row = self.entry_strategy_table.currentRow()
        if current_row >= 0:
            strategy_name = self.entry_strategy_table.item(current_row, 0).text()
            print(f"[UI] 🧪 진입 전략 백테스트: {strategy_name}")
            # TODO: 백테스트 화면으로 전환
    
    # ===== 관리 전략 관련 메서드 =====
    def create_management_strategy(self):
        """관리 전략 생성"""
        print("[UI] 🛡️ 관리 전략 생성 다이얼로그 열기")
        # TODO: 관리 전략 생성 다이얼로그 구현
        
    def edit_management_strategy(self):
        """관리 전략 수정"""
        current_row = self.management_strategy_table.currentRow()
        if current_row >= 0:
            strategy_name = self.management_strategy_table.item(current_row, 0).text()
            print(f"[UI] ✏️ 관리 전략 수정: {strategy_name}")
            # TODO: 관리 전략 수정 다이얼로그 구현
        
    def delete_management_strategy(self):
        """관리 전략 삭제"""
        current_row = self.management_strategy_table.currentRow()
        if current_row >= 0:
            strategy_name = self.management_strategy_table.item(current_row, 0).text()
            print(f"[UI] 🗑️ 관리 전략 삭제: {strategy_name}")
            # TODO: 삭제 확인 다이얼로그 후 삭제 실행
            
    def test_management_strategy(self):
        """관리 전략 백테스트"""
        current_row = self.management_strategy_table.currentRow()
        if current_row >= 0:
            strategy_name = self.management_strategy_table.item(current_row, 0).text()
            print(f"[UI] 🧪 관리 전략 백테스트: {strategy_name}")
            # TODO: 백테스트 화면으로 전환
    
    # ===== 전략 조합 관련 메서드 =====
    def create_new_combination(self):
        """새 전략 조합 생성"""
        print("[UI] 🆕 새 전략 조합 생성")
        self.combination_name_label.setText("조합명: 새 조합 (편집 중)")
        self.combination_desc_label.setText("설명: 진입 전략 1개와 관리 전략을 선택하세요")
        
        # 기존 조합 선택 해제
        self.current_editing_combination = None
        
        # 선택 테이블 체크박스 초기화
        for i in range(self.entry_selection_table.rowCount()):
            item = self.entry_selection_table.item(i, 0)
            if item:
                item.setText("☐")
        
        for i in range(self.mgmt_selection_table.rowCount()):
            item = self.mgmt_selection_table.item(i, 0)
            if item:
                item.setText("☐")
        
    def delete_combination(self):
        """전략 조합 삭제"""
        current_row = self.combination_list_table.currentRow()
        if current_row >= 0:
            combo_name = self.combination_list_table.item(current_row, 0).text()
            
            # 실제 조합 찾기
            combinations = self.combination_manager.get_all_combinations()
            target_combo = None
            for combo in combinations:
                if combo.name == combo_name:
                    target_combo = combo
                    break
            
            if target_combo:
                success = self.combination_manager.delete_combination(target_combo.combination_id)
                if success:
                    print(f"[UI] 🗑️ 전략 조합 삭제 완료: {combo_name}")
                    # UI 새로고침
                    self.load_strategy_combinations()
                else:
                    print(f"[UI] ❌ 전략 조합 삭제 실패: {combo_name}")
            
    def save_combination(self):
        """전략 조합 저장"""
        print("[UI] 💾 전략 조합 저장")
        
        # TODO: 선택된 진입/관리 전략 수집
        # TODO: StrategyCombination 생성 및 저장
        # TODO: UI 새로고침
        
        # 임시 구현: 단순 메시지
        print("   📋 선택된 진입 전략: (수집 중...)")
        print("   📋 선택된 관리 전략: (수집 중...)")
        print("   💾 조합 저장 로직 구현 필요")
        
    def preview_combination(self):
        """전략 조합 미리보기"""
        print("[UI] 👁️ 전략 조합 미리보기")
        
        # 현재 선택된 전략들 표시
        selected_entry = []
        selected_mgmt = []
        
        # 진입 전략 체크 확인
        for i in range(self.entry_selection_table.rowCount()):
            check_item = self.entry_selection_table.item(i, 0)
            name_item = self.entry_selection_table.item(i, 1)
            if check_item and name_item and check_item.text() == "☑":
                selected_entry.append(name_item.text())
        
        # 관리 전략 체크 확인
        for i in range(self.mgmt_selection_table.rowCount()):
            check_item = self.mgmt_selection_table.item(i, 0)
            name_item = self.mgmt_selection_table.item(i, 1)
            if check_item and name_item and check_item.text() == "☑":
                selected_mgmt.append(name_item.text())
        
        print(f"   📈 진입 전략: {selected_entry}")
        print(f"   🛡️ 관리 전략: {selected_mgmt}")
        
        if not selected_entry:
            print("   ⚠️ 진입 전략을 선택해주세요")
        elif len(selected_entry) > 1:
            print("   ⚠️ 진입 전략은 1개만 선택 가능합니다")
        else:
            summary = selected_entry[0]
            if selected_mgmt:
                summary += f" + {', '.join(selected_mgmt)}"
            print(f"   ✅ 조합 구성: {summary}")
        
    def run_combination_backtest(self):
        """전략 조합 백테스트 실행"""
        print("[UI] 🚀 전략 조합 백테스트 실행")
        
        # 선택된 조합 확인
        current_row = self.combination_list_table.currentRow()
        if current_row < 0:
            print("   ⚠️ 백테스트할 조합을 선택해주세요")
            return
            
        combo_name = self.combination_list_table.item(current_row, 0).text()
        print(f"   📊 백테스트 대상: {combo_name}")
        
        # 백테스트 설정 수집
        data_source = self.db_selector.currentText()
        start_date = self.start_date_edit.date().toPython() if hasattr(self.start_date_edit.date(), 'toPython') else self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toPython() if hasattr(self.end_date_edit.date(), 'toPython') else self.end_date_edit.date().toString("yyyy-MM-dd")
        initial_capital_text = self.initial_capital_combo.currentText().replace(",", "")
        
        try:
            initial_capital = float(initial_capital_text)
        except ValueError:
            initial_capital = 1000000.0  # 기본값
            
        print(f"   📊 데이터 소스: {data_source}")
        print(f"   📅 백테스트 기간: {start_date} ~ {end_date}")
        print(f"   💰 초기 자본: {initial_capital:,.0f}원")
        
        # 데이터 소스별 처리
        if data_source == "샘플 데이터 (테스트용)":
            print("   🧪 샘플 데이터로 백테스트 실행")
            self._run_sample_backtest(combo_name, initial_capital)
        else:
            print(f"   🔗 실제 DB 연동 백테스트 (향후 구현)")
            print(f"      기간: {start_date} ~ {end_date}")
            print(f"      소스: {data_source}")
            # TODO: 실제 DB에서 데이터 로드 후 백테스트 실행
            self._show_temp_results()
    
    def _run_sample_backtest(self, combo_name: str, initial_capital: float):
        """샘플 데이터로 백테스트 실행"""
        try:
            # 백테스트 엔진 임포트 및 실행
            from ...business_logic.strategy.combination_backtest_engine import StrategyCombinationBacktestEngine
            import pandas as pd
            import numpy as np
            from datetime import datetime
            
            # 조합 정보 가져오기
            combinations = self.combination_manager.get_all_combinations()
            selected_combination = None
            for combo in combinations:
                if combo.name == combo_name:
                    selected_combination = combo
                    break
            
            if not selected_combination:
                print(f"   ❌ 조합을 찾을 수 없음: {combo_name}")
                return
            
            print("   ⚙️ 백테스트 엔진 초기화 중...")
            engine = StrategyCombinationBacktestEngine()
            engine.load_combination(selected_combination)
            
            # 샘플 시장 데이터 생성
            print("   📊 샘플 시장 데이터 생성 중...")
            dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='h')
            np.random.seed(42)
            
            n_points = len(dates)
            initial_price = 50000
            prices = [initial_price]
            
            for i in range(1, n_points):
                trend_component = 0.0001 * np.sin(i / 1000)
                random_component = np.random.normal(0, 0.02)
                cycle_component = 0.01 * np.sin(i / 50)
                price_change = trend_component + random_component + cycle_component
                new_price = prices[-1] * (1 + price_change)
                new_price = max(10000, min(100000, new_price))
                prices.append(new_price)
            
            prices = np.array(prices)
            market_data = pd.DataFrame({
                'close': prices,
                'high': prices * (1 + np.abs(np.random.normal(0, 0.005, n_points))),
                'low': prices * (1 - np.abs(np.random.normal(0, 0.005, n_points))),
                'volume': np.random.uniform(1000, 10000, n_points)
            }, index=dates)
            
            print("   🚀 백테스트 실행 중...")
            result = engine.run_backtest(market_data, initial_capital=initial_capital)
            
            # 결과 표시
            self._display_backtest_result(result)
            print("   ✅ 백테스트 완료")
            
        except Exception as e:
            print(f"   ❌ 백테스트 실행 오류: {e}")
            self._show_temp_results()
    
    def _display_backtest_result(self, result):
        """백테스트 결과를 UI에 표시"""
        self.total_return_label.setText(f"총 수익률: {result.total_return:+.2f}%")
        self.win_rate_label.setText(f"승률: {result.win_rate:.1f}%")
        self.sharpe_ratio_label.setText(f"샤프 비율: {result.sharpe_ratio:.2f}")
        self.max_drawdown_label.setText(f"최대 낙폭: {result.max_drawdown:.2f}%")
        
        # 전략 기여도 표시
        entry_contrib = list(result.entry_contribution.values())[0] if result.entry_contribution else 0
        mgmt_contrib = sum(result.management_contribution.values()) if result.management_contribution else 0
        
        self.entry_contribution_label.setText(f"진입 전략: {entry_contrib:+.2f}%")
        self.mgmt_contribution_label.setText(f"관리 전략: {mgmt_contrib:+.2f}%")
    
    def _show_temp_results(self):
        """임시 결과 표시 (실제 DB 연동 전까지)"""
        self.total_return_label.setText("총 수익률: +15.3%")
        self.win_rate_label.setText("승률: 64.2%")
        self.sharpe_ratio_label.setText("샤프 비율: 1.42")
        self.max_drawdown_label.setText("최대 낙폭: -8.1%")
        
        self.entry_contribution_label.setText("진입 전략: +12.1%")
        self.mgmt_contribution_label.setText("관리 전략: +3.2%")
        
    def export_backtest_result(self):
        """백테스트 결과 내보내기"""
        print("[UI] 📊 백테스트 결과 내보내기")
        # TODO: 결과를 CSV/Excel로 내보내기
    
    # ===== 이벤트 핸들러 =====
    def on_combination_selected(self, row, col):
        """조합 목록에서 조합 선택 시"""
        if row >= 0:
            combo_name = self.combination_list_table.item(row, 0).text()
            print(f"[UI] 📋 조합 선택: {combo_name}")
            
            # 조합 정보 표시
            combinations = self.combination_manager.get_all_combinations()
            for combo in combinations:
                if combo.name == combo_name:
                    self.combination_name_label.setText(f"조합명: {combo.name}")
                    self.combination_desc_label.setText(f"설명: {combo.description}")
                    
                    # 선택 테이블 업데이트 (TODO: 실제 선택 상태 반영)
                    print(f"   📈 진입: {combo.entry_strategy.strategy_name}")
                    print(f"   🛡️ 관리: {[ms.strategy_name for ms in combo.management_strategies]}")
                    break
    
    def on_entry_selection_clicked(self, row, col):
        """진입 전략 선택 체크박스 클릭"""
        if col == 0:  # 체크박스 컬럼
            item = self.entry_selection_table.item(row, col)
            strategy_name = self.entry_selection_table.item(row, 1).text()
            
            if item.text() == "☐":
                # 다른 진입 전략 체크 해제 (1개만 선택 가능)
                for i in range(self.entry_selection_table.rowCount()):
                    check_item = self.entry_selection_table.item(i, 0)
                    if check_item:
                        check_item.setText("☐")
                
                # 현재 항목 체크
                item.setText("☑")
                print(f"[UI] ✅ 진입 전략 선택: {strategy_name}")
            else:
                item.setText("☐")
                print(f"[UI] ❌ 진입 전략 선택 해제: {strategy_name}")
    
    def on_mgmt_selection_clicked(self, row, col):
        """관리 전략 선택 체크박스 클릭"""
        if col == 0:  # 체크박스 컬럼
            item = self.mgmt_selection_table.item(row, col)
            strategy_name = self.mgmt_selection_table.item(row, 1).text()
            
            if item.text() == "☐":
                # 선택된 관리 전략 개수 확인 (최대 5개)
                selected_count = 0
                for i in range(self.mgmt_selection_table.rowCount()):
                    check_item = self.mgmt_selection_table.item(i, 0)
                    if check_item and check_item.text() == "☑":
                        selected_count += 1
                
                if selected_count >= 5:
                    print(f"[UI] ⚠️ 관리 전략은 최대 5개까지 선택 가능합니다")
                else:
                    item.setText("☑")
                    print(f"[UI] ✅ 관리 전략 선택: {strategy_name}")
            else:
                item.setText("☐")
                print(f"[UI] ❌ 관리 전략 선택 해제: {strategy_name}")
