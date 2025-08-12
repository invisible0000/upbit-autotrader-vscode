"""
백테스트 설정 위젯
- 코인 선택 및 차트 데이터 수집
- 테스트 기간 설정
- 초기 자본금 설정
- 거래 수수료/슬리피지 설정
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox, QDateEdit,
    QProgressBar, QTextEdit, QCheckBox, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, QDate, QThread, QTimer
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataCollectionThread(QThread):
    """차트 데이터 수집 스레드"""
    
    progress_updated = pyqtSignal(int, str)  # 진행률, 메시지
    data_collected = pyqtSignal(bool, str)   # 성공 여부, 메시지
    
    def __init__(self, coins, start_date, end_date, timeframes):
        super().__init__()
        self.coins = coins
        self.start_date = start_date
        self.end_date = end_date
        self.timeframes = timeframes
    
    def run(self):
        """데이터 수집 실행"""
        try:
            from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
            from upbit_auto_trading.data_layer.storage.market_data_storage import MarketDataStorage
            
            api = UpbitAPI()
            storage = MarketDataStorage()
            
            total_tasks = len(self.coins) * len(self.timeframes)
            current_task = 0
            
            self.progress_updated.emit(0, "데이터 수집 시작...")
            
            for coin in self.coins:
                for timeframe in self.timeframes:
                    current_task += 1
                    progress = int((current_task / total_tasks) * 100)
                    
                    self.progress_updated.emit(progress, f"{coin} {timeframe} 데이터 수집 중...")
                    
                    # API에서 데이터 가져오기
                    try:
                        data = api.get_candles_range(
                            symbol=coin,
                            timeframe=timeframe,
                            start_date=self.start_date,
                            end_date=self.end_date
                        )
                        
                        if data is not None and not data.empty:
                            # 데이터 저장
                            success = storage.save_market_data(data)
                            if success:
                                logger.info(f"{coin} {timeframe} 데이터 저장 완료: {len(data)}개")
                            else:
                                logger.warning(f"{coin} {timeframe} 데이터 저장 실패")
                        else:
                            logger.warning(f"{coin} {timeframe} 데이터 없음")
                            
                    except Exception as e:
                        logger.error(f"{coin} {timeframe} 데이터 수집 실패: {e}")
                        continue
            
            self.progress_updated.emit(100, "데이터 수집 완료!")
            self.data_collected.emit(True, f"총 {total_tasks}개 작업 완료")
            
        except Exception as e:
            logger.error(f"데이터 수집 중 오류: {e}")
            self.data_collected.emit(False, f"오류 발생: {str(e)}")

class BacktestSetupWidget(QWidget):
    # 백테스트 시작 시그널 (설정 정보를 딕셔너리로 전달)
    backtest_started = pyqtSignal(dict)
    # 데이터 수집 완료 시그널
    data_collection_completed = pyqtSignal(bool, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_collection_thread = None
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        # 전체 위젯의 최소/최대 폭 설정으로 좌측 패널 적절한 크기 유지
        self.setMinimumWidth(450)  # 최소 폭 증가
        self.setMaximumWidth(600)  # 최대 폭 증가 (창이 커져도 적절히 따라감)
        
        # 크기 정책 설정: 수평으로는 선호 크기까지 확장, 수직으로는 최소 크기 유지
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        
        layout = QVBoxLayout(self)
        
        # 1. 데이터 수집 및 기간 설정 (4줄 구성)
        data_group = QGroupBox("📊 데이터 수집 및 기간")
        data_group.setMaximumWidth(580)  # 최대 폭 더 증가
        data_layout = QVBoxLayout(data_group)
        
        # 첫 번째 줄: 대상 코인과 타임프레임
        first_row_layout = QHBoxLayout()
        first_row_layout.addWidget(QLabel("대상 코인:"))
        self.coin_selector = QComboBox()
        self.coin_selector.setEditable(True)
        self.coin_selector.setMaximumWidth(140)  # 너비 증가
        popular_coins = [
            "KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", "KRW-DOT",
            "KRW-DOGE", "KRW-SOL", "KRW-MATIC", "KRW-AVAX", "KRW-ATOM"
        ]
        self.coin_selector.addItems(popular_coins)
        first_row_layout.addWidget(self.coin_selector)
        
        first_row_layout.addSpacing(20)  # 간격 추가
        
        # 타임프레임 선택
        first_row_layout.addWidget(QLabel("타임프레임:"))
        self.timeframe_combo = QComboBox()
        timeframes = [
            ("1분", "1m"), ("3분", "3m"), ("5분", "5m"), ("10분", "10m"),
            ("15분", "15m"), ("30분", "30m"), ("1시간", "1h"), ("4시간", "4h"),
            ("1일", "1d"), ("1주", "1w"), ("1개월", "1M")
        ]
        for display_name, value in timeframes:
            self.timeframe_combo.addItem(display_name, value)
        self.timeframe_combo.setCurrentText("1시간")  # 기본값
        self.timeframe_combo.setMaximumWidth(120)  # 폭 증가
        first_row_layout.addWidget(self.timeframe_combo)
        first_row_layout.addStretch()
        data_layout.addLayout(first_row_layout)
        
        # 두 번째 줄: 수집 시작일과 종료일
        second_row_layout = QHBoxLayout()
        second_row_layout.addWidget(QLabel("수집 시작일:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addYears(-2))  # 2년 전
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setMaximumWidth(150)  # 폭 증가
        second_row_layout.addWidget(self.start_date)
        
        second_row_layout.addSpacing(20)  # 간격 추가
        
        second_row_layout.addWidget(QLabel("수집 종료일:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())  # 오늘
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setMaximumWidth(150)  # 폭 증가
        second_row_layout.addWidget(self.end_date)
        second_row_layout.addStretch()
        data_layout.addLayout(second_row_layout)
        
        # 세 번째 줄: 빠른 선택 버튼들
        third_row_layout = QHBoxLayout()
        third_row_layout.addWidget(QLabel("빠른 선택:"))
        quick_3m_btn = QPushButton("3개월")
        quick_6m_btn = QPushButton("6개월")
        quick_1y_btn = QPushButton("1년")
        quick_2y_btn = QPushButton("2년")
        
        # 버튼 크기 설정 (공간이 생겨서 더 크게 가능)
        for btn in [quick_3m_btn, quick_6m_btn, quick_1y_btn, quick_2y_btn]:
            btn.setMaximumWidth(70)
        
        quick_3m_btn.clicked.connect(lambda: self.set_quick_period(3))
        quick_6m_btn.clicked.connect(lambda: self.set_quick_period(6))
        quick_1y_btn.clicked.connect(lambda: self.set_quick_period(12))
        quick_2y_btn.clicked.connect(lambda: self.set_quick_period(24))
        
        third_row_layout.addWidget(quick_3m_btn)
        third_row_layout.addWidget(quick_6m_btn)
        third_row_layout.addWidget(quick_1y_btn)
        third_row_layout.addWidget(quick_2y_btn)
        third_row_layout.addStretch()
        data_layout.addLayout(third_row_layout)
        
        # 네 번째 줄: 차트 데이터 수집 버튼
        fourth_row_layout = QHBoxLayout()
        self.collect_data_btn = QPushButton("📥 차트 데이터 수집")
        self.collect_data_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.collect_data_btn.clicked.connect(self.collect_chart_data)
        fourth_row_layout.addWidget(self.collect_data_btn)
        fourth_row_layout.addStretch()
        data_layout.addLayout(fourth_row_layout)
        
        # 진행률 표시
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        data_layout.addWidget(self.progress_bar)
        
        # 로그 표시
        self.log_display = QTextEdit()
        self.log_display.setMaximumHeight(100)
        self.log_display.setVisible(False)
        data_layout.addWidget(self.log_display)
        
        layout.addWidget(data_group)
        
        # 2. 데이터베이스 선택 (개선된 레이아웃)
        db_group = QGroupBox("💾 백테스트 데이터 선택")
        db_group.setMaximumWidth(580)  # 최대 폭 더 증가
        db_layout = QVBoxLayout(db_group)
        
        # DB 선택 드롭다운과 새로고침 버튼 (드롭다운 폭 확보)
        db_select_layout = QHBoxLayout()
        self.db_selector = QComboBox()
        self.refresh_db_btn = QPushButton("🔄 새로고침")
        self.refresh_db_btn.clicked.connect(self.refresh_db_list)
        db_select_layout.addWidget(self.db_selector, stretch=4)  # 드롭다운에 더 많은 공간
        db_select_layout.addWidget(self.refresh_db_btn, stretch=1)
        db_layout.addLayout(db_select_layout)
        
        # DB 정보 표시와 삭제 버튼 (한 줄에 배치, UX 개선)
        db_info_layout = QHBoxLayout()
        self.db_info_label = QLabel("DB를 선택하세요")
        self.db_info_label.setStyleSheet("color: #666; font-size: 12px; padding: 5px;")
        self.delete_db_btn = QPushButton("🗑️ 삭제")
        self.delete_db_btn.clicked.connect(self.delete_selected_db)
        self.delete_db_btn.setMaximumWidth(80)
        db_info_layout.addWidget(self.db_info_label, stretch=4)  # 정보에 더 많은 공간
        db_info_layout.addWidget(self.delete_db_btn, stretch=1)  # 삭제 버튼은 작게
        db_layout.addLayout(db_info_layout)
        
        # DB 목록 초기 로드
        self.refresh_db_list()
        
        layout.addWidget(db_group)
        
        # 4. 전략 선택
        strategy_group = QGroupBox("📈 전략 선택")
        strategy_group.setMaximumWidth(580)  # 최대 폭 더 증가
        strategy_layout = QVBoxLayout(strategy_group)
        
        # 전략 새로고침 버튼
        refresh_strategy_layout = QHBoxLayout()
        self.strategy_selector = QComboBox()
        self.refresh_strategy_btn = QPushButton("🔄 새로고침")
        self.refresh_strategy_btn.clicked.connect(self.refresh_strategy_list)
        refresh_strategy_layout.addWidget(self.strategy_selector, stretch=4)
        refresh_strategy_layout.addWidget(self.refresh_strategy_btn, stretch=1)
        strategy_layout.addLayout(refresh_strategy_layout)
        
        # 전략 목록 초기 로드
        self.refresh_strategy_list()
        
        layout.addWidget(strategy_group)
        
        # 4. 거래 설정 및 백테스트 기간 (3줄 구성으로 재구성)
        trading_group = QGroupBox("💰 거래 설정 및 백테스트 기간")
        trading_group.setMaximumWidth(580)  # 최대 폭 더 증가
        trading_layout = QVBoxLayout(trading_group)
        
        # 첫 번째 줄: 초기 자본 (금액이 클 수 있으니 한 줄 독립)
        first_trading_row = QHBoxLayout()
        first_trading_row.addWidget(QLabel("초기 자본:"))
        self.initial_capital = QSpinBox()
        self.initial_capital.setRange(100000, 1000000000)
        self.initial_capital.setValue(10000000)  # 1천만원
        self.initial_capital.setSingleStep(1000000)  # 100만원 단위
        self.initial_capital.setSuffix(" 원")
        self.initial_capital.setMaximumWidth(180)  # 폭 증가
        first_trading_row.addWidget(self.initial_capital)
        first_trading_row.addStretch()
        trading_layout.addLayout(first_trading_row)
        
        # 두 번째 줄: 거래 수수료와 슬리피지 (함께 배치)
        second_trading_row = QHBoxLayout()
        second_trading_row.addWidget(QLabel("거래 수수료:"))
        self.trading_fee = QDoubleSpinBox()
        self.trading_fee.setRange(0, 1)
        self.trading_fee.setValue(0.05)  # 0.05%
        self.trading_fee.setSingleStep(0.01)
        self.trading_fee.setSuffix(" %")
        self.trading_fee.setMaximumWidth(120)  # 폭 증가
        second_trading_row.addWidget(self.trading_fee)
        
        second_trading_row.addSpacing(20)  # 간격
        
        second_trading_row.addWidget(QLabel("슬리피지:"))
        self.slippage = QDoubleSpinBox()
        self.slippage.setRange(0, 1)
        self.slippage.setValue(0.02)  # 0.02%
        self.slippage.setSingleStep(0.01)
        self.slippage.setSuffix(" %")
        self.slippage.setMaximumWidth(120)  # 폭 증가
        second_trading_row.addWidget(self.slippage)
        second_trading_row.addStretch()
        trading_layout.addLayout(second_trading_row)
        
        # 세 번째 줄: 시작일과 종료일 ("백테스트" 텍스트 제거)
        third_trading_row = QHBoxLayout()
        third_trading_row.addWidget(QLabel("시작일:"))
        self.backtest_start_date = QDateEdit()
        self.backtest_start_date.setDate(QDate.currentDate().addMonths(-6))  # 6개월 전
        self.backtest_start_date.setCalendarPopup(True)
        self.backtest_start_date.setDisplayFormat("yyyy-MM-dd")
        self.backtest_start_date.setMaximumWidth(150)  # 폭 증가
        third_trading_row.addWidget(self.backtest_start_date)
        
        third_trading_row.addSpacing(20)  # 간격
        
        third_trading_row.addWidget(QLabel("종료일:"))
        self.backtest_end_date = QDateEdit()
        self.backtest_end_date.setDate(QDate.currentDate().addDays(-1))  # 어제
        self.backtest_end_date.setCalendarPopup(True)
        self.backtest_end_date.setDisplayFormat("yyyy-MM-dd")
        self.backtest_end_date.setMaximumWidth(150)  # 폭 증가
        third_trading_row.addWidget(self.backtest_end_date)
        third_trading_row.addStretch()
        trading_layout.addLayout(third_trading_row)
        
        # 네 번째 줄: 빠른 선택 버튼들 ("백테스트 기간" 텍스트 제거, 버튼 크기 증가)
        fourth_trading_row = QHBoxLayout()
        fourth_trading_row.addWidget(QLabel("빠른 선택:"))  # "백테스트 기간" 제거
        
        backtest_quick_1m_btn = QPushButton("1개월")
        backtest_quick_3m_btn = QPushButton("3개월")
        backtest_quick_6m_btn = QPushButton("6개월")
        backtest_quick_1y_btn = QPushButton("1년")
        backtest_quick_2y_btn = QPushButton("2년")
        backtest_quick_max_btn = QPushButton("최대")
        
        # 버튼 크기 증가 (공간이 생겨서 더 크게 가능)
        quick_buttons = [backtest_quick_1m_btn, backtest_quick_3m_btn, backtest_quick_6m_btn, 
                        backtest_quick_1y_btn, backtest_quick_2y_btn, backtest_quick_max_btn]
        for btn in quick_buttons:
            btn.setMaximumWidth(65)  # 크기 증가
            btn.setStyleSheet("font-size: 12px; padding: 4px;")  # 폰트와 패딩 증가
        
        backtest_quick_1m_btn.clicked.connect(lambda: self.set_backtest_period(1))
        backtest_quick_3m_btn.clicked.connect(lambda: self.set_backtest_period(3))
        backtest_quick_6m_btn.clicked.connect(lambda: self.set_backtest_period(6))
        backtest_quick_1y_btn.clicked.connect(lambda: self.set_backtest_period(12))
        backtest_quick_2y_btn.clicked.connect(lambda: self.set_backtest_period(24))
        backtest_quick_max_btn.clicked.connect(lambda: self.set_backtest_period_max())
        
        for btn in quick_buttons:
            fourth_trading_row.addWidget(btn)
        fourth_trading_row.addStretch()
        trading_layout.addLayout(fourth_trading_row)
        
        # 백테스트 기간 정보 표시
        self.backtest_period_info = QLabel("💡 백테스트 기간은 선택된 DB 데이터 범위 내에서 설정해주세요")
        self.backtest_period_info.setStyleSheet("color: #666; font-size: 11px; padding: 2px;")
        trading_layout.addWidget(self.backtest_period_info)
        
        layout.addWidget(trading_group)
        
        # 5. 실행 버튼
        self.run_btn = QPushButton("🚀 백테스트 실행")
        self.run_btn.setMaximumWidth(580)  # 최대 폭 더 증가
        self.run_btn.clicked.connect(self.run_backtest)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        layout.addWidget(self.run_btn)
        
        # 남은 공간을 위쪽으로 밀어냄
        layout.addStretch(1)
    
    def set_quick_period(self, months):
        """빠른 기간 설정 (데이터 수집용)"""
        end_date = QDate.currentDate()
        start_date = end_date.addMonths(-months)
        
        self.start_date.setDate(start_date)
        self.end_date.setDate(end_date)
        
        logger.info(f"데이터 수집 기간 설정: {months}개월 ({start_date.toString('yyyy-MM-dd')} ~ {end_date.toString('yyyy-MM-dd')})")
    
    def set_backtest_period(self, months):
        """빠른 백테스트 기간 설정"""
        end_date = QDate.currentDate().addDays(-1)  # 어제
        start_date = end_date.addMonths(-months)
        
        self.backtest_start_date.setDate(start_date)
        self.backtest_end_date.setDate(end_date)
        
        logger.info(f"백테스트 기간 설정: {months}개월 ({start_date.toString('yyyy-MM-dd')} ~ {end_date.toString('yyyy-MM-dd')})")
    
    def set_backtest_period_max(self):
        """DB 내 최대 기간으로 백테스트 기간 설정"""
        try:
            from upbit_auto_trading.data_layer.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            
            # 선택된 코인 확인
            selected_coin = self.coin_selector.currentText().strip()
            if not selected_coin:
                QMessageBox.warning(self, "경고", "먼저 코인을 선택해주세요.")
                return
            
            # 선택된 타임프레임 확인
            selected_timeframe = self.timeframe_combo.currentData()
            if not selected_timeframe:
                QMessageBox.warning(self, "경고", "먼저 타임프레임을 선택해주세요.")
                return
            
            # DB에서 해당 코인의 최대 데이터 범위 조회
            query = """
                SELECT MIN(timestamp) as min_date, MAX(timestamp) as max_date
                FROM market_data
                WHERE symbol = ? AND timeframe = ?
            """
            
            result = db_manager.fetch_one(query, (selected_coin, selected_timeframe))
            
            if result and result[0] and result[1]:
                # 타임스탬프를 날짜로 변환
                from datetime import datetime
                min_date = datetime.fromtimestamp(result[0] / 1000)  # ms to seconds
                max_date = datetime.fromtimestamp(result[1] / 1000)
                
                # 날짜 설정
                self.backtest_start_date.setDate(QDate(min_date.year, min_date.month, min_date.day))
                self.backtest_end_date.setDate(QDate(max_date.year, max_date.month, max_date.day))
                
                logger.info(f"백테스트 기간 설정: 최대 기간 ({min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')})")
                
                # 사용자에게 피드백
                QMessageBox.information(
                    self, 
                    "최대 기간 설정", 
                    f"백테스트 기간이 DB 내 최대 범위로 설정되었습니다.\n"
                    f"시작일: {min_date.strftime('%Y-%m-%d')}\n"
                    f"종료일: {max_date.strftime('%Y-%m-%d')}"
                )
            else:
                QMessageBox.warning(
                    self, 
                    "데이터 없음", 
                    f"선택된 코인({selected_coin})과 타임프레임({self.timeframe_combo.currentText()})에 대한 데이터가 없습니다.\n"
                    f"먼저 데이터를 수집해주세요."
                )
                
        except Exception as e:
            logger.error(f"최대 기간 설정 실패: {e}")
            QMessageBox.critical(self, "오류", f"최대 기간 설정 중 오류가 발생했습니다:\n{str(e)}")
    
    
    def collect_chart_data(self):
        """차트 데이터 수집"""
        try:
            # 선택된 타임프레임 확인 (드롭다운에서)
            selected_timeframe = self.timeframe_combo.currentData()
            if not selected_timeframe:
                QMessageBox.warning(self, "경고", "타임프레임을 선택해주세요.")
                return
            
            selected_timeframes = [selected_timeframe]
            
            # 선택된 코인
            selected_coin = self.coin_selector.currentText().strip()
            if not selected_coin:
                QMessageBox.warning(self, "경고", "코인을 선택해주세요.")
                return
            
            # 기간 확인
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().toString("yyyy-MM-dd")
            
            if self.start_date.date() >= self.end_date.date():
                QMessageBox.warning(self, "경고", "시작일이 종료일보다 빠르거나 같습니다.")
                return
            
            # UI 상태 변경
            self.collect_data_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.log_display.setVisible(True)
            self.log_display.clear()
            
            self.log_display.append(f"📊 데이터 수집 시작")
            self.log_display.append(f"코인: {selected_coin}")
            self.log_display.append(f"기간: {start_date} ~ {end_date}")
            self.log_display.append(f"타임프레임: {self.timeframe_combo.currentText()}")
            
            # 데이터 수집 스레드 시작
            self.data_collection_thread = DataCollectionThread(
                coins=[selected_coin],
                start_date=start_date,
                end_date=end_date,
                timeframes=selected_timeframes
            )
            
            self.data_collection_thread.progress_updated.connect(self.on_progress_updated)
            self.data_collection_thread.data_collected.connect(self.on_data_collected)
            self.data_collection_thread.start()
            
        except Exception as e:
            logger.error(f"데이터 수집 시작 실패: {e}")
            QMessageBox.critical(self, "오류", f"데이터 수집을 시작할 수 없습니다:\n{str(e)}")
            self.collect_data_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def on_progress_updated(self, progress, message):
        """진행률 업데이트"""
        self.progress_bar.setValue(progress)
        self.log_display.append(f"⏳ {message}")
        
        # 스크롤을 맨 아래로
        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_data_collected(self, success, message):
        """데이터 수집 완료"""
        if success:
            self.log_display.append(f"✅ {message}")
            QMessageBox.information(self, "완료", "차트 데이터 수집이 완료되었습니다!")
        else:
            self.log_display.append(f"❌ {message}")
            QMessageBox.critical(self, "오류", f"데이터 수집 실패:\n{message}")
        
        # UI 상태 복원
        self.collect_data_btn.setEnabled(True)
        
        # 진행률 바를 3초 후에 숨김
        QTimer.singleShot(3000, lambda: self.progress_bar.setVisible(False))
        
        self.data_collection_completed.emit(success, message)
    
    def run_backtest(self):
        """백테스트 실행"""
        # 선택된 DB 데이터 확인
        selected_data = self.db_selector.currentData()
        if not selected_data:
            QMessageBox.warning(self, "경고", "백테스트할 데이터를 선택해주세요.")
            return
        
        config = {
            'coin': selected_data.get('symbol', self.coin_selector.currentText()),
            'strategy': self.strategy_selector.currentText(),
            'strategy_id': self.strategy_selector.currentData(),  # strategy_id 추가
            'start_date': self.backtest_start_date.date().toString("yyyy-MM-dd"),  # 백테스트 기간 사용
            'end_date': self.backtest_end_date.date().toString("yyyy-MM-dd"),      # 백테스트 기간 사용
            'initial_capital': self.initial_capital.value(),
            'trading_fee': self.trading_fee.value(),
            'slippage': self.slippage.value(),  # 슬리피지 추가
            'timeframes': [selected_data.get('timeframe', '1h')],  # 선택된 DB의 타임프레임 사용
            'selected_db': selected_data  # 선택된 DB 정보 추가
        }
        
        # 백테스트 기간이 DB 데이터 범위 내에 있는지 확인
        db_start = selected_data.get('start_date')
        db_end = selected_data.get('end_date')
        bt_start = config['start_date']
        bt_end = config['end_date']
        
        if bt_start < db_start or bt_end > db_end:
            QMessageBox.warning(
                self, 
                "경고", 
                f"백테스트 기간이 데이터 범위를 벗어났습니다.\n\n"
                f"데이터 범위: {db_start} ~ {db_end}\n"
                f"백테스트 기간: {bt_start} ~ {bt_end}\n\n"
                f"백테스트 기간을 데이터 범위 내로 설정해주세요."
            )
            return
        
        logger.info(f"백테스트 실행: {config}")
        self.backtest_started.emit(config)
    
    def refresh_strategy_list(self):
        """저장된 전략 목록 새로고침"""
        try:
            # 기존 항목 제거
            self.strategy_selector.clear()
            
            # 기본 전략 추가
            self.strategy_selector.addItem("단순 매수 보유 (Buy & Hold)", "buy_and_hold")
            
            # 실제 구현된 이동평균 전략들 추가
            self.strategy_selector.addItem("이동평균 교차 (5, 20) - 빠른 전략", "ma_cross_5_20")
            self.strategy_selector.addItem("이동평균 교차 (10, 30) - 보통 전략", "ma_cross_10_30")
            self.strategy_selector.addItem("이동평균 교차 (20, 50) - 느린 전략", "ma_cross_20_50")
            
            # 기본 전략들 추가
            self.strategy_selector.addItem("볼린저 밴드 전략", "bollinger_bands")
            self.strategy_selector.addItem("RSI 전략", "rsi_strategy")
            self.strategy_selector.addItem("변동성 돌파 전략", "volatility_breakout")
            
            # 저장된 전략 불러오기
            try:
                import sys
                import os
                
                # 프로젝트 루트 경로 추가
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
                sys.path.insert(0, project_root)
                
                from upbit_auto_trading.business_logic.strategy.trading_strategies import StrategyManager
                
                strategy_manager = StrategyManager()
                strategies = strategy_manager.get_all_strategies()
                
                for strategy in strategies:
                    display_name = f"{strategy.name} ({strategy.strategy_type})"
                    self.strategy_selector.addItem(display_name, strategy.strategy_id)
                    
                logger.info(f"전략 목록 새로고침 완료: {len(strategies)}개 전략")
                
            except Exception as e:
                logger.warning(f"저장된 전략 로딩 실패: {e}")
                # 폴백으로 추가 기본 전략들 추가
                self.strategy_selector.addItem("RSI 역추세 전략", "rsi_reversal") 
                self.strategy_selector.addItem("볼린저밴드 평균회귀 전략", "bb_mean_reversion")
                self.strategy_selector.addItem("변동성 돌파 전략", "volatility_breakout")
                
        except Exception as e:
            logger.error(f"전략 목록 새로고침 오류: {e}")
            QMessageBox.warning(self, "오류", f"전략 목록을 불러오는데 실패했습니다: {e}")
    
    def get_selected_strategy_id(self):
        """선택된 전략 ID 반환"""
        return self.strategy_selector.currentData()
    
    def refresh_db_list(self):
        """사용 가능한 데이터베이스 목록 새로고침"""
        try:
            # 기존 항목 제거
            self.db_selector.clear()
            
            # 실제 DB에서 데이터 조회
            try:
                import sys
                import os
                
                # 프로젝트 루트 경로 추가
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
                sys.path.insert(0, project_root)
                
                from upbit_auto_trading.data_layer.storage.market_data_storage import MarketDataStorage
                
                storage = MarketDataStorage()
                
                # 실제 저장된 데이터 조회
                datasets = self.get_real_datasets(storage)
                
                if datasets:
                    for dataset in datasets:
                        symbol = dataset.get('symbol', 'Unknown')
                        timeframe = dataset.get('timeframe', 'Unknown')
                        start_date = dataset.get('start_date', 'Unknown')
                        end_date = dataset.get('end_date', 'Unknown')
                        count = dataset.get('record_count', 0)
                        
                        display_name = f"{symbol} ({timeframe}) - {start_date} ~ {end_date} ({count}개)"
                        self.db_selector.addItem(display_name, dataset)
                        
                else:
                    # 데이터가 없는 경우 샘플 데이터 표시
                    self.add_sample_db_entries()
                    
            except Exception as e:
                logger.warning(f"DB 목록 로딩 실패: {e}")
                # 폴백으로 샘플 데이터 표시
                self.add_sample_db_entries()
            
            # DB 선택 시 정보 업데이트 연결
            self.db_selector.currentTextChanged.connect(self.update_db_info)
            self.update_db_info()
            
        except Exception as e:
            logger.error(f"DB 목록 새로고침 오류: {e}")
            QMessageBox.warning(self, "오류", f"DB 목록을 불러오는데 실패했습니다: {e}")
    
    def get_real_datasets(self, storage):
        """실제 저장된 데이터셋 정보 조회"""
        try:
            import sqlite3
            
            # DB에서 실제 데이터 조회
            conn = sqlite3.connect(storage.db_path)
            cursor = conn.cursor()
            
            # 심볼별, 타임프레임별 데이터 요약 조회
            query = """
            SELECT 
                symbol,
                timeframe,
                MIN(timestamp) as start_date,
                MAX(timestamp) as end_date,
                COUNT(*) as record_count
            FROM market_data 
            GROUP BY symbol, timeframe
            ORDER BY symbol, timeframe
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            
            datasets = []
            for row in rows:
                datasets.append({
                    'symbol': row[0],
                    'timeframe': row[1],
                    'start_date': row[2][:10] if row[2] else 'Unknown',  # YYYY-MM-DD 형식
                    'end_date': row[3][:10] if row[3] else 'Unknown',
                    'record_count': row[4]
                })
            
            return datasets
            
        except Exception as e:
            logger.error(f"실제 데이터셋 조회 오류: {e}")
            return []
    
    def delete_selected_db(self):
        """선택된 DB 데이터 삭제"""
        current_data = self.db_selector.currentData()
        if not current_data or 'symbol' not in current_data:
            QMessageBox.warning(self, "경고", "삭제할 데이터를 선택해주세요.")
            return
        
        symbol = current_data['symbol']
        timeframe = current_data['timeframe']
        
        reply = QMessageBox.question(
            self, 
            "확인", 
            f"{symbol} ({timeframe}) 데이터를 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                import sys
                import os
                
                # 프로젝트 루트 경로 추가
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
                sys.path.insert(0, project_root)
                
                from upbit_auto_trading.data_layer.storage.market_data_storage import MarketDataStorage
                
                storage = MarketDataStorage()
                
                # DB에서 해당 데이터 삭제
                import sqlite3
                conn = sqlite3.connect(storage.db_path)
                cursor = conn.cursor()
                
                cursor.execute(
                    "DELETE FROM market_data WHERE symbol = ? AND timeframe = ?",
                    (symbol, timeframe)
                )
                
                deleted_count = cursor.rowcount
                conn.commit()
                conn.close()
                
                QMessageBox.information(
                    self, 
                    "완료", 
                    f"{symbol} ({timeframe}) 데이터 삭제 완료\n삭제된 레코드: {deleted_count}개"
                )
                
                # DB 목록 새로고침
                self.refresh_db_list()
                
            except Exception as e:
                logger.error(f"DB 삭제 오류: {e}")
                QMessageBox.critical(self, "오류", f"데이터 삭제 중 오류가 발생했습니다: {e}")
    
    def add_sample_db_entries(self):
        """샘플 DB 데이터 추가"""
        sample_data = [
            {
                'symbol': 'KRW-BTC',
                'timeframe': '1d',
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
                'record_count': 365,
                'description': '비트코인 일봉 데이터'
            },
            {
                'symbol': 'KRW-ETH',
                'timeframe': '4h',
                'start_date': '2024-06-01',
                'end_date': '2024-12-31',
                'record_count': 1100,
                'description': '이더리움 4시간봉 데이터'
            },
            {
                'symbol': 'KRW-XRP',
                'timeframe': '1h',
                'start_date': '2024-11-01',
                'end_date': '2024-12-31',
                'record_count': 1500,
                'description': '리플 1시간봉 데이터'
            }
        ]
        
        for data in sample_data:
            display_name = f"{data['symbol']} ({data['timeframe']}) - {data['start_date']} ~ {data['end_date']} ({data['record_count']}개)"
            self.db_selector.addItem(display_name, data)
    
    def update_db_info(self):
        """선택된 DB 정보 업데이트"""
        current_data = self.db_selector.currentData()
        if current_data:
            symbol = current_data.get('symbol', 'Unknown')
            timeframe = current_data.get('timeframe', 'Unknown')
            start_date = current_data.get('start_date', 'Unknown')
            end_date = current_data.get('end_date', 'Unknown')
            count = current_data.get('record_count', 0)
            description = current_data.get('description', '')
            
            period_days = 0
            try:
                from datetime import datetime
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                period_days = (end - start).days
            except:
                pass
            
            info_text = f"📊 {symbol} | ⏱️ {timeframe} | 📅 {period_days}일간 | 📈 {count}개 레코드"
            if description:
                info_text += f" | 💡 {description}"
                
            self.db_info_label.setText(info_text)
        else:
            self.db_info_label.setText("DB를 선택하세요")
    
    def get_selected_db_info(self):
        """선택된 DB 정보 반환"""
        return self.db_selector.currentData()
