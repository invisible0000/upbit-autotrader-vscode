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
        layout = QVBoxLayout(self)
        
        # 1. 코인 선택 및 데이터 수집
        data_group = QGroupBox("📊 데이터 수집")
        data_layout = QVBoxLayout(data_group)
        
        # 코인 선택
        coin_layout = QHBoxLayout()
        coin_layout.addWidget(QLabel("대상 코인:"))
        self.coin_selector = QComboBox()
        self.coin_selector.setEditable(True)
        popular_coins = [
            "KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", "KRW-DOT",
            "KRW-DOGE", "KRW-SOL", "KRW-MATIC", "KRW-AVAX", "KRW-ATOM"
        ]
        self.coin_selector.addItems(popular_coins)
        coin_layout.addWidget(self.coin_selector)
        data_layout.addLayout(coin_layout)
        
        # 타임프레임 선택
        timeframe_layout = QHBoxLayout()
        timeframe_layout.addWidget(QLabel("타임프레임:"))
        self.timeframe_1d = QCheckBox("1일")
        self.timeframe_4h = QCheckBox("4시간")
        self.timeframe_1h = QCheckBox("1시간")
        self.timeframe_1d.setChecked(True)  # 기본값
        timeframe_layout.addWidget(self.timeframe_1d)
        timeframe_layout.addWidget(self.timeframe_4h)
        timeframe_layout.addWidget(self.timeframe_1h)
        timeframe_layout.addStretch()
        data_layout.addLayout(timeframe_layout)
        
        # 데이터 수집 버튼
        self.collect_data_btn = QPushButton("📥 차트 데이터 수집")
        self.collect_data_btn.clicked.connect(self.collect_chart_data)
        data_layout.addWidget(self.collect_data_btn)
        
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
        
        # 2. 테스트 기간 설정
        period_group = QGroupBox("📅 테스트 기간")
        period_layout = QVBoxLayout(period_group)
        
        start_date_layout = QHBoxLayout()
        start_date_layout.addWidget(QLabel("시작일:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-3))  # 3달 전
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")  # 연도-월-일 형식으로 표시
        self.start_date.setMinimumWidth(120)  # 최소 너비 설정
        start_date_layout.addWidget(self.start_date)
        start_date_layout.addStretch()  # 여백 추가
        period_layout.addLayout(start_date_layout)
        
        end_date_layout = QHBoxLayout()
        end_date_layout.addWidget(QLabel("종료일:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())  # 오늘
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")  # 연도-월-일 형식으로 표시
        self.end_date.setMinimumWidth(120)  # 최소 너비 설정
        end_date_layout.addWidget(self.end_date)
        end_date_layout.addStretch()  # 여백 추가
        period_layout.addLayout(end_date_layout)
        
        # 빠른 기간 선택 버튼들
        quick_period_layout = QHBoxLayout()
        quick_1m_btn = QPushButton("1개월")
        quick_3m_btn = QPushButton("3개월")
        quick_6m_btn = QPushButton("6개월")
        quick_1y_btn = QPushButton("1년")
        
        quick_1m_btn.clicked.connect(lambda: self.set_quick_period(1))
        quick_3m_btn.clicked.connect(lambda: self.set_quick_period(3))
        quick_6m_btn.clicked.connect(lambda: self.set_quick_period(6))
        quick_1y_btn.clicked.connect(lambda: self.set_quick_period(12))
        
        quick_period_layout.addWidget(quick_1m_btn)
        quick_period_layout.addWidget(quick_3m_btn)
        quick_period_layout.addWidget(quick_6m_btn)
        quick_period_layout.addWidget(quick_1y_btn)
        
        period_layout.addLayout(quick_period_layout)
        layout.addWidget(period_group)
        
        # 3. 전략 선택
        strategy_group = QGroupBox("📈 전략 선택")
        strategy_layout = QVBoxLayout(strategy_group)
        
        self.strategy_selector = QComboBox()
        self.strategy_selector.addItems([
            "단순 매수 보유 (Buy & Hold)",
            "이동평균 교차 전략",
            "RSI 역추세 전략",
            "볼린저밴드 평균회귀 전략",
            "변동성 돌파 전략"
        ])
        strategy_layout.addWidget(self.strategy_selector)
        
        layout.addWidget(strategy_group)
        
        # 4. 자본금 및 거래 설정
        trading_group = QGroupBox("💰 거래 설정")
        trading_layout = QVBoxLayout(trading_group)
        
        # 초기 자본
        capital_layout = QHBoxLayout()
        capital_layout.addWidget(QLabel("초기 자본:"))
        self.initial_capital = QSpinBox()
        self.initial_capital.setRange(100000, 1000000000)
        self.initial_capital.setValue(10000000)  # 1천만원
        self.initial_capital.setSingleStep(1000000)  # 100만원 단위
        self.initial_capital.setSuffix(" 원")
        capital_layout.addWidget(self.initial_capital)
        trading_layout.addLayout(capital_layout)
        
        # 거래 수수료
        fee_layout = QHBoxLayout()
        fee_layout.addWidget(QLabel("거래 수수료:"))
        self.trading_fee = QDoubleSpinBox()
        self.trading_fee.setRange(0, 1)
        self.trading_fee.setValue(0.05)  # 0.05%
        self.trading_fee.setSingleStep(0.01)
        self.trading_fee.setSuffix(" %")
        fee_layout.addWidget(self.trading_fee)
        trading_layout.addLayout(fee_layout)
        
        layout.addWidget(trading_group)
        
        # 5. 실행 버튼
        self.run_btn = QPushButton("🚀 백테스트 실행")
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
        """빠른 기간 설정"""
        end_date = QDate.currentDate()
        start_date = end_date.addMonths(-months)
        
        self.start_date.setDate(start_date)
        self.end_date.setDate(end_date)
        
        logger.info(f"기간 설정: {months}개월 ({start_date.toString('yyyy-MM-dd')} ~ {end_date.toString('yyyy-MM-dd')})")
    
    def collect_chart_data(self):
        """차트 데이터 수집"""
        try:
            # 선택된 타임프레임 확인
            selected_timeframes = []
            if self.timeframe_1d.isChecked():
                selected_timeframes.append("1d")
            if self.timeframe_4h.isChecked():
                selected_timeframes.append("4h")
            if self.timeframe_1h.isChecked():
                selected_timeframes.append("1h")
            
            if not selected_timeframes:
                QMessageBox.warning(self, "경고", "최소 하나의 타임프레임을 선택해주세요.")
                return
            
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
            self.log_display.append(f"타임프레임: {', '.join(selected_timeframes)}")
            
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
        config = {
            'coin': self.coin_selector.currentText(),
            'strategy': self.strategy_selector.currentText(),
            'start_date': self.start_date.date().toString("yyyy-MM-dd"),
            'end_date': self.end_date.date().toString("yyyy-MM-dd"),
            'initial_capital': self.initial_capital.value(),
            'trading_fee': self.trading_fee.value(),
            'timeframes': []
        }
        
        # 선택된 타임프레임 추가
        if self.timeframe_1d.isChecked():
            config['timeframes'].append("1d")
        if self.timeframe_4h.isChecked():
            config['timeframes'].append("4h")
        if self.timeframe_1h.isChecked():
            config['timeframes'].append("1h")
        
        if not config['timeframes']:
            QMessageBox.warning(self, "경고", "최소 하나의 타임프레임을 선택해주세요.")
            return
        
        logger.info(f"백테스트 실행: {config}")
        self.backtest_started.emit(config)
