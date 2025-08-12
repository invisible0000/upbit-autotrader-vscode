"""
리팩토링된 차트 뷰 화면
- 컴포넌트 기반 아키텍처
- UI 사양서 준수
- 향상된 사용자 경험
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QTabWidget, QGroupBox, QMessageBox, QFileDialog,
    QLabel, QPushButton, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, QMetaObject, Q_ARG
from PyQt6.QtGui import QIcon

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import logging

# 컴포넌트 임포트
from .components.chart_control_panel import ChartControlPanel
from .components.indicator_management_panel import IndicatorManagementPanel
from .components.chart_info_panel import ChartInfoPanel
from .components.enhanced_candlestick_chart import CandlestickChart

# 업비트 API 및 웹소켓 임포트
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
from upbit_auto_trading.data_layer.collectors.upbit_websocket import RealtimeChartUpdater

# 로거 설정
logger = logging.getLogger(__name__)

# 기존 컴포넌트 임포트 (점진적 마이그레이션)
try:
    from .indicator_overlay import IndicatorOverlay
    from .trade_marker import TradeMarker
except ImportError:
    # 임시 더미 클래스
    class IndicatorOverlay:
        def __init__(self, *args, **kwargs): pass
    
    class TradeMarker:
        def __init__(self, *args, **kwargs): pass

class ChartViewScreen(QWidget):
    """리팩토링된 차트 뷰 화면"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 업비트 API 인스턴스 생성
        self.upbit_api = UpbitAPI()
        
        # 웹소켓 실시간 업데이터
        self.realtime_updater = None
        self.use_websocket = True  # 웹소켓 사용 여부
        
        # 상태 변수
        self.current_symbol = "KRW-BTC"  # 업비트 형식으로 변경
        self.current_timeframe = "1d"
        self.chart_data = None  # 메인 차트 데이터 (pandas DataFrame, 메모리에 저장)
        self.active_indicators = {}
        self.trade_markers = []
        self.trade_markers = []
        self.settings_visible = False  # 설정 패널 표시 상태 추가
        
        # 화면 활성 상태 관리
        self.is_screen_active = True  # 차트뷰 화면이 활성 상태인지
        self.update_paused = False    # 업데이트 일시정지 상태
        
        # 코인별 뷰포트 및 지표 설정 저장
        self.coin_settings = {}  # 코인별 설정 딕셔너리
        
        # 코인별 데이터 캐싱 시스템
        self.coin_data_cache = {}  # 코인별 전체 데이터 캐시 {symbol_timeframe: DataFrame}
        self.cache_max_size = 10  # 최대 캐시 항목 수
        self.cache_access_time = {}  # 캐시 접근 시간 추적 (LRU용)
        
        # 무한 스크롤 관련 변수
        self.is_loading_past_data = False  # 과거 데이터 로딩 중인지 여부
        self.past_data_exhausted = False  # 더 이상 가져올 과거 데이터가 없는지 여부
        self.scroll_threshold = 5  # 스크롤 임계점 (왼쪽 끝에서 5개 캔들) - 사용자 요청에 따라 조정
        self.max_data_points = 5000  # 최대 데이터 포인트 (메모리 관리)
        self.max_candles = 5000  # 최대 캔들 개수 (실시간 업데이트용)
        
        # 렌더링 제한 관련 변수
        self.pending_chart_update = False
        self.pending_viewport_preservation = True
        self.render_delay_ms = 300  # 300ms 렌더링 지연
        
        # 무한 루프 방지 변수들
        self._updating_chart = False  # 차트 업데이트 중 플래그
        self._last_update_time = 0  # 마지막 업데이트 시간
        self._update_throttle_ms = 100  # 최소 업데이트 간격 (100ms)
        self._reapply_in_progress = False  # 지표 재적용 중 플래그
        
        # 렌더링 타이머 초기화
        self.render_timer = QTimer()
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self._perform_deferred_render)
        
        # UI 초기화
        self.init_ui()
        
        # 이벤트 연결
        self.connect_signals()
        
        # 초기 데이터 로드
        self.load_initial_data()
    
    def init_ui(self):
        """UI 초기화"""
        # 크기 정책 설정
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 메인 스플리터 (가로 분할)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 좌측 패널 (차트 영역)
        left_panel = self.create_chart_area()
        main_splitter.addWidget(left_panel)
        
        # 우측 패널 (컨트롤 및 정보)
        right_panel = self.create_control_area()
        main_splitter.addWidget(right_panel)
        
        # 스플리터 비율 설정 (차트:컨트롤 = 7:3)
        main_splitter.setSizes([700, 300])
        main_splitter.setChildrenCollapsible(False)
        
        layout.addWidget(main_splitter)
    
    def create_chart_area(self):
        """차트 영역 생성 - 트레이딩뷰 스타일"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #1e1e1e;")  # 다크 테마
        
        # 레이아웃 생성 (차트가 위젯 크기에 맞춰 조절되도록)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 메인 차트 (전체 영역)
        self.candlestick_chart = CandlestickChart()
        layout.addWidget(self.candlestick_chart)
        
        # 무한 스크롤 이벤트 연결
        self.setup_infinite_scroll()
        
        # 상단 컨트롤 패널 (오버레이)
        self.create_top_control_overlay(widget)
        
        # 하단 액션 버튼 (오버레이)
        self.create_bottom_action_overlay(widget)
        
        return widget
    
    def create_top_control_overlay(self, parent):
        """상단 컨트롤 오버레이 생성"""
        self.top_control_widget = QWidget(parent)
        
        # 크기 정책 설정
        from PyQt6.QtWidgets import QSizePolicy
        self.top_control_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.top_control_widget.setFixedHeight(40)
        
        self.top_control_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(33, 37, 41, 0.9);
                border-radius: 8px;
                margin: 0px;
            }
        """)
        
        layout = QHBoxLayout(self.top_control_widget)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(15)
        
        # 심볼 선택
        symbol_group = QWidget()
        symbol_layout = QHBoxLayout(symbol_group)
        symbol_layout.setContentsMargins(0, 0, 0, 0)
        symbol_layout.setSpacing(5)
        
        symbol_label = QLabel("종목:")
        symbol_label.setStyleSheet("color: white; font-size: 12px;")
        self.symbol_selector = QComboBox()
        self.symbol_selector.addItems([
            "KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", 
            "KRW-DOT", "KRW-DOGE", "KRW-SOL", "KRW-MATIC"
        ])
        self.symbol_selector.setCurrentText("KRW-BTC")
        self.symbol_selector.setStyleSheet("""
            QComboBox {
                background-color: #495057;
                color: white;
                border: 1px solid #6c757d;
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 80px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid white;
            }
        """)
        self.symbol_selector.currentTextChanged.connect(self.on_symbol_changed)
        
        symbol_layout.addWidget(symbol_label)
        symbol_layout.addWidget(self.symbol_selector)
        layout.addWidget(symbol_group)
        
        # 시간대 선택
        timeframe_group = QWidget()
        timeframe_layout = QHBoxLayout(timeframe_group)
        timeframe_layout.setContentsMargins(0, 0, 0, 0)
        timeframe_layout.setSpacing(2)
        
        timeframes = ["1분", "5분", "15분", "1시간", "4시간", "1일"]
        self.timeframe_buttons = {}
        
        for tf in timeframes:
            btn = QPushButton(tf)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #adb5bd;
                    border: 1px solid #495057;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                    min-width: 35px;
                }
                QPushButton:checked {
                    background-color: #007bff;
                    color: white;
                    border-color: #007bff;
                }
                QPushButton:hover {
                    background-color: #495057;
                    color: white;
                }
            """)
            btn.clicked.connect(lambda checked, t=tf: self.on_timeframe_button_clicked(t))
            self.timeframe_buttons[tf] = btn
            timeframe_layout.addWidget(btn)
        
        # 기본 1일 선택
        self.timeframe_buttons["1일"].setChecked(True)
        
        layout.addWidget(timeframe_group)
        
        # 지표 추가 버튼
        self.add_indicator_btn = QPushButton("+ 지표")
        self.add_indicator_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.add_indicator_btn.clicked.connect(self.show_quick_indicator_menu)
        layout.addWidget(self.add_indicator_btn)
        
        layout.addStretch()
        
        # 설정 버튼
        settings_btn = QPushButton("⚙️")
        settings_btn.setFixedSize(30, 25)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        settings_btn.clicked.connect(self.toggle_settings_panel)
        layout.addWidget(settings_btn)
    
    def create_bottom_action_overlay(self, parent):
        """하단 액션 버튼 오버레이 생성"""
        self.bottom_action_widget = QWidget(parent)
        self.bottom_action_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(33, 37, 41, 0.9);
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self.bottom_action_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)  # 버튼 간격을 8px로 증가
        
        # 차트 저장 버튼
        save_btn = QPushButton("💾")
        save_btn.setFixedSize(35, 35)
        save_btn.setToolTip("차트 저장")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        save_btn.clicked.connect(self.on_save_chart)
        layout.addWidget(save_btn)
        
        # 뷰포트 초기화 버튼 (약한 초기화)
        viewport_reset_btn = QPushButton("📍")
        viewport_reset_btn.setFixedSize(35, 35)
        viewport_reset_btn.setToolTip("뷰포트 초기화 (최신 200개 캔들)")
        viewport_reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        viewport_reset_btn.clicked.connect(self.reset_viewport_only)
        layout.addWidget(viewport_reset_btn)
        
        # 차트 완전 초기화 버튼 (강한 초기화)
        reset_btn = QPushButton("🔄")
        reset_btn.setFixedSize(35, 35)
        reset_btn.setToolTip("차트 완전 초기화 (지표 포함)")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        reset_btn.clicked.connect(self.reset_chart)
        layout.addWidget(reset_btn)
        
        # Y축 오토레인지 버튼 추가
        y_auto_range_btn = QPushButton("📏")
        y_auto_range_btn.setFixedSize(35, 35)
        y_auto_range_btn.setToolTip("Y축 오토레인지 (가격 범위 자동 조정)")
        y_auto_range_btn.setStyleSheet("""
            QPushButton {
                background-color: #fd7e14;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e8590c;
            }
        """)
        y_auto_range_btn.clicked.connect(self.auto_range_y_axis)
        layout.addWidget(y_auto_range_btn)
        
        # X축 오토레인지 버튼 추가
        x_auto_range_btn = QPushButton("🔍")
        x_auto_range_btn.setFixedSize(35, 35)
        x_auto_range_btn.setToolTip("X축 오토레인지 (전체 데이터 범위 표시)")
        x_auto_range_btn.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a2a9b;
            }
        """)
        x_auto_range_btn.clicked.connect(self.auto_range_x_axis)
        layout.addWidget(x_auto_range_btn)
        
        # 🚨 응급 중단 버튼 추가
        emergency_stop_btn = QPushButton("🛑")
        emergency_stop_btn.setFixedSize(35, 35)
        emergency_stop_btn.setToolTip("응급 중단 (무한 업데이트 루프 차단)")
        emergency_stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        emergency_stop_btn.clicked.connect(self.emergency_stop_updates)
        layout.addWidget(emergency_stop_btn)
        
        # 특정 시간 이동 버튼 추가
        time_jump_btn = QPushButton("📅")
        time_jump_btn.setFixedSize(35, 35)
        time_jump_btn.setToolTip("특정 시간으로 이동")
        time_jump_btn.setStyleSheet("""
            QPushButton {
                background-color: #e83e8c;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c2185b;
            }
        """)
        time_jump_btn.clicked.connect(self.show_time_jump_dialog)
        layout.addWidget(time_jump_btn)
    
    def show_quick_indicator_menu(self):
        """빠른 지표 추가 메뉴 - 우측 지표 패널과 연동 (표준 파라미터 포함)"""
        # 표준 파라미터가 포함된 지표 목록
        from PyQt6.QtWidgets import QInputDialog
        
        # 암호화폐 차트 분석을 위한 표준 지표 파라미터
        indicators = [
            # 이동평균선 (Moving Averages) - 5가지 기본 기간
            "MA5 (초단기 추세선)",
            "MA10 (단기 추세선)", 
            "MA20 (단기 기준선/생명선)",
            "MA60 (중기 추세선/수급선)",
            "MA120 (장기 추세선/경기선)",
            "EMA12 (MACD 단기선 기준)",
            "EMA20 (표준 지수이동평균)",
            "EMA26 (MACD 장기선 기준)",
            # 기술적 지표 (Technical Indicators) - 표준 파라미터
            "RSI14 (상대강도지수)",
            "MACD(12,26,9) (표준설정)",
            "볼린저밴드(20,2) (표준설정)",
            "스토캐스틱(14,3,3) (표준설정)"
        ]
        
        indicator, ok = QInputDialog.getItem(
            self, "📈 빠른 지표 추가", 
            "📊 암호화폐 차트 분석용 표준 지표를 선택하세요:\n\n" +
            "• MA5~120: 단기~장기 추세 분석\n" +
            "• RSI14: 과매수/과매도 판단 (70/30 기준)\n" +
            "• MACD: 추세 변화 포착\n" +
            "• 볼린저밴드: 변동성 분석\n" +
            "• 스토캐스틱: 모멘텀 분석",
            indicators, 0, False
        )
        
        if ok and indicator:
            # 표준 파라미터로 지표 추가
            params = self.get_standard_indicator_params(indicator)
            
            # 지표 표시명으로 변환
            indicator_display_name = self.convert_quick_to_display_name(indicator)
            
            # 우측 지표 패널을 통해 지표 추가 (통일된 처리)
            self.indicator_panel.add_indicator(indicator_display_name, params)
            
            # 사용자에게 추가된 지표 정보 표시
            param_info = self.get_param_description(params)
            print(f"✅ 지표 추가 완료: {indicator}")
            print(f"📋 설정: {param_info}")
    
    def get_standard_indicator_params(self, quick_name):
        """표준 파라미터가 적용된 지표 파라미터 반환"""
        # 이동평균선 (SMA)
        if "MA5" in quick_name:
            return {"type": "SMA", "period": 5, "color": "#FF6B6B"}  # 빨간색 (단기)
        elif "MA10" in quick_name:
            return {"type": "SMA", "period": 10, "color": "#4ECDC4"}  # 청록색
        elif "MA20" in quick_name:
            return {"type": "SMA", "period": 20, "color": "#45B7D1"}  # 파란색 (생명선)
        elif "MA60" in quick_name:
            return {"type": "SMA", "period": 60, "color": "#F7DC6F"}  # 노란색 (수급선)
        elif "MA120" in quick_name:
            return {"type": "SMA", "period": 120, "color": "#BB8FCE"}  # 보라색 (경기선)
        
        # 지수이동평균선 (EMA)
        elif "EMA12" in quick_name:
            return {"type": "EMA", "period": 12, "color": "#58D68D"}  # 연두색
        elif "EMA20" in quick_name:
            return {"type": "EMA", "period": 20, "color": "#5DADE2"}  # 하늘색
        elif "EMA26" in quick_name:
            return {"type": "EMA", "period": 26, "color": "#F8C471"}  # 주황색
        
        # 기술적 지표들 (표준 파라미터)
        elif "RSI14" in quick_name:
            return {
                "type": "RSI", 
                "period": 14, 
                "overbought": 70, 
                "oversold": 30,
                "color": "#E74C3C"
            }
        elif "MACD(12,26,9)" in quick_name:
            return {
                "type": "MACD", 
                "fast": 12, 
                "slow": 26, 
                "signal": 9,
                "color": "#2ECC71"
            }
        elif "볼린저밴드(20,2)" in quick_name:
            return {
                "type": "BBANDS", 
                "period": 20, 
                "std": 2.0,
                "color": "#9B59B6"
            }
        elif "스토캐스틱(14,3,3)" in quick_name:
            return {
                "type": "Stochastic", 
                "k": 14, 
                "d": 3, 
                "smooth": 3,
                "color": "#E67E22"
            }
        
        # 기본값 (호환성 유지)
        return {"type": "SMA", "period": 20, "color": "#2196F3"}
    
    def convert_quick_to_display_name(self, quick_name):
        """퀵 메뉴 이름을 지표 패널 표시명으로 변환"""
        # 이동평균선
        if "MA5" in quick_name:
            return "이동평균 (SMA)"
        elif "MA10" in quick_name:
            return "이동평균 (SMA)"
        elif "MA20" in quick_name:
            return "이동평균 (SMA)"
        elif "MA60" in quick_name:
            return "이동평균 (SMA)"
        elif "MA120" in quick_name:
            return "이동평균 (SMA)"
        elif "EMA" in quick_name:
            return "지수이동평균 (EMA)"
        
        # 기술적 지표
        elif "RSI14" in quick_name:
            return "RSI"
        elif "MACD" in quick_name:
            return "MACD"
        elif "볼린저밴드" in quick_name:
            return "볼린저밴드 (BBANDS)"
        elif "스토캐스틱" in quick_name:
            return "스토캐스틱"
        
        # 기본값
        return "이동평균 (SMA)"
    
    def get_param_description(self, params):
        """파라미터 설명 문자열 생성"""
        param_type = params.get("type", "")
        
        if param_type == "SMA":
            return f"기간 {params['period']}일"
        elif param_type == "EMA":
            return f"기간 {params['period']}일"
        elif param_type == "RSI":
            return f"기간 {params['period']}일, 과매수 {params.get('overbought', 70)}, 과매도 {params.get('oversold', 30)}"
        elif param_type == "MACD":
            return f"단기 {params['fast']}, 장기 {params['slow']}, 시그널 {params['signal']}"
        elif param_type == "BBANDS":
            return f"기간 {params['period']}일, 표준편차 {params['std']}배"
        elif param_type == "Stochastic":
            return f"%K {params['k']}일, %D {params['d']}일, 스무딩 {params.get('smooth', 3)}"
        
        return "표준 설정"
    
    def convert_to_display_name(self, quick_name):
        """기존 호환성을 위한 메서드 (deprecated)"""
        name_mapping = {
            "SMA(20)": "이동평균 (SMA)",
            "EMA(20)": "지수이동평균 (EMA)", 
            "볼린저밴드": "볼린저밴드 (BBANDS)",
            "RSI": "RSI",
            "MACD": "MACD"
        }
        return name_mapping.get(quick_name, quick_name)
    
    def get_default_indicator_params(self, indicator_name):
        """기본 지표 파라미터 반환"""
        if "SMA" in indicator_name:
            return {"type": "SMA", "period": 20, "color": "#2196F3"}
        elif "EMA" in indicator_name:
            return {"type": "EMA", "period": 20, "color": "#FF9800"}
        elif "볼린저밴드" in indicator_name:
            return {"type": "BBANDS", "period": 20, "std": 2.0, "color": "#9C27B0"}
        elif "RSI" in indicator_name:
            return {"type": "RSI", "period": 14, "color": "#F44336"}
        elif "MACD" in indicator_name:
            return {"type": "MACD", "fast": 12, "slow": 26, "signal": 9, "color": "#4CAF50"}
        return {}
    
    def toggle_settings_panel(self):
        """설정 패널 토글"""
        if not hasattr(self, 'settings_panel') or self.settings_panel is None:
            self.create_settings_panel()
        
        self.settings_visible = not self.settings_visible
        if hasattr(self, 'settings_panel'):
            self.settings_panel.setVisible(self.settings_visible)
    
    def create_settings_panel(self):
        """설정 패널 생성"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
        
        self.settings_panel = QDialog(self)
        self.settings_panel.setWindowTitle("차트 설정")
        self.settings_panel.setModal(False)
        self.settings_panel.resize(300, 400)
        
        layout = QVBoxLayout(self.settings_panel)
        layout.addWidget(QLabel("차트 설정 기능은 개발 중입니다."))
    
    def reset_chart(self):
        """차트 완전 초기화 - 사용자 확인 후 실행"""
        from PyQt6.QtWidgets import QMessageBox
        
        # 사용자 확인 대화상자
        reply = QMessageBox.question(
            self, 
            "차트 완전 초기화", 
            "모든 지표와 설정을 초기화하고 차트를 처음 상태로 되돌립니다.\n계속하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        try:
            logger.info("차트 완전 초기화 시작")
            
            # 1. 뷰포트를 기본 상태로 강제 초기화
            view_box = self.candlestick_chart.getViewBox()
            view_box.enableAutoRange()  # 자동 범위 조정 활성화
            view_box.autoRange()  # 즉시 자동 범위 적용
            
            # 2. 모든 지표 제거
            self.active_indicators.clear()
            
            # 3. 현재 코인의 설정도 초기화
            coin_key = f"{self.current_symbol}_{self.current_timeframe}"
            if coin_key in self.coin_settings:
                del self.coin_settings[coin_key]
            
            # 4. 무한 스크롤 상태 초기화
            self.reset_infinite_scroll_state()
            
            # 5. 차트 데이터 다시 로드 (깨끗한 상태)
            self.load_initial_data()
            
            # 6. 강제로 뷰포트를 전체 데이터에 맞춤
            QTimer.singleShot(100, self._force_auto_range)
            
            logger.info("차트 완전 초기화 완료")
            print("차트가 완전히 초기화되었습니다.")
            
        except Exception as e:
            logger.error(f"차트 초기화 중 오류: {e}")
            print(f"차트 초기화 중 오류가 발생했습니다: {e}")
    
    def _force_auto_range(self):
        """강제로 뷰포트를 전체 데이터에 맞춤"""
        try:
            view_box = self.candlestick_chart.getViewBox()
            view_box.enableAutoRange()
            view_box.autoRange()
            logger.debug("뷰포트 강제 자동 조정 완료")
        except Exception as e:
            logger.error(f"뷰포트 강제 조정 중 오류: {e}")
    
    def reset_viewport_only(self):
        """약한 초기화: 뷰포트만 초기화 (지표 유지)"""
        try:
            logger.info("뷰포트 초기화 시작")
            
            # 1. 뷰포트를 우측 끝 200개 캔들로 설정
            if self.chart_data is not None and len(self.chart_data) > 0:
                data_length = len(self.chart_data)
                view_width = min(200, data_length)  # 최대 200개 또는 전체 데이터
                
                # 최신 데이터 기준으로 범위 계산
                x_max = data_length - 1
                x_min = max(0, x_max - view_width + 1)
                
                # 가격 범위 계산 (보이는 데이터 기준으로 정확히 계산)
                visible_data = self.chart_data.iloc[int(x_min):int(x_max)+1]
                if not visible_data.empty:
                    price_min = visible_data['low'].min()
                    price_max = visible_data['high'].max()
                    
                    # 적절한 여백 추가 (5% 상하 여백)
                    price_range = price_max - price_min
                    if price_range > 0:
                        margin = price_range * 0.05
                        y_min = price_min - margin
                        y_max = price_max + margin
                    else:
                        # 가격이 동일한 경우 작은 여백 추가
                        margin = price_min * 0.01 if price_min > 0 else 1000
                        y_min = price_min - margin
                        y_max = price_max + margin
                else:
                    # 폴백: 전체 데이터 기준
                    price_min = self.chart_data['low'].min()
                    price_max = self.chart_data['high'].max()
                    price_range = price_max - price_min
                    margin = price_range * 0.05 if price_range > 0 else price_min * 0.01
                    y_min = price_min - margin
                    y_max = price_max + margin
                
                # 뷰포트 설정 (자동 범위 비활성화 후 수동 설정)
                view_box = self.candlestick_chart.getViewBox()
                view_box.disableAutoRange()
                view_box.setRange(
                    xRange=[x_min, x_max],
                    yRange=[y_min, y_max],
                    padding=0,
                    update=True
                )
                
                logger.info(f"뷰포트 초기화 완료: x=[{x_min:.1f}, {x_max:.1f}], y=[{y_min:.0f}, {y_max:.0f}], 캔들={view_width}개")
                print(f"뷰포트가 초기화되었습니다 (최신 {view_width}개 캔들 표시)")
            
        except Exception as e:
            logger.error(f"뷰포트 초기화 중 오류: {e}")
            print(f"뷰포트 초기화 중 오류가 발생했습니다: {e}")
    
    def auto_range_y_axis(self):
        """Y축 오토레인지 - 현재 보이는 X 범위에서 가격 범위 자동 조정"""
        try:
            logger.info("Y축 오토레인지 시작")
            
            if self.chart_data is not None and len(self.chart_data) > 0:
                # 현재 뷰포트의 X 범위 가져오기
                view_box = self.candlestick_chart.getViewBox()
                current_range = view_box.viewRange()
                x_range = current_range[0]
                x_min, x_max = x_range
                
                # X 범위를 데이터 인덱스 범위로 제한
                data_length = len(self.chart_data)
                x_min = max(0, int(x_min))
                x_max = min(data_length - 1, int(x_max))
                
                # 현재 보이는 데이터의 가격 범위 계산
                visible_data = self.chart_data.iloc[x_min:x_max+1]
                if not visible_data.empty:
                    price_min = visible_data['low'].min()
                    price_max = visible_data['high'].max()
                    
                    # 적절한 여백 추가 (3% 상하 여백)
                    price_range = price_max - price_min
                    if price_range > 0:
                        margin = price_range * 0.03
                        y_min = price_min - margin
                        y_max = price_max + margin
                    else:
                        # 가격이 동일한 경우 작은 여백 추가
                        margin = price_min * 0.01 if price_min > 0 else 1000
                        y_min = price_min - margin
                        y_max = price_max + margin
                    
                    # Y축만 조정 (X축은 현재 범위 유지)
                    view_box.setRange(
                        xRange=[x_range[0], x_range[1]],  # X축은 변경하지 않음
                        yRange=[y_min, y_max],
                        padding=0,
                        update=True
                    )
                    
                    logger.info(f"Y축 오토레인지 완료: y=[{y_min:.0f}, {y_max:.0f}], 가격범위={price_range:.0f}")
                    print(f"Y축이 자동 조정되었습니다 (범위: {y_min:,.0f} - {y_max:,.0f})")
                else:
                    print("표시할 데이터가 없습니다.")
            
        except Exception as e:
            logger.error(f"Y축 오토레인지 중 오류: {e}")
            print(f"Y축 오토레인지 중 오류가 발생했습니다: {e}")
    
    def auto_range_x_axis(self):
        """X축 오토레인지 - 전체 데이터 범위에 맞춤"""
        try:
            logger.info("X축 오토레인지 시작")
            
            if self.chart_data is not None and len(self.chart_data) > 0:
                # 현재 뷰포트의 Y 범위 가져오기 (Y축은 유지)
                view_box = self.candlestick_chart.getViewBox()
                current_range = view_box.viewRange()
                y_range = current_range[1]
                
                # 전체 데이터 범위로 X축 설정
                data_length = len(self.chart_data)
                x_min = 0
                x_max = data_length - 1
                
                # X축만 조정 (Y축은 현재 범위 유지)
                view_box.setRange(
                    xRange=[x_min, x_max],
                    yRange=y_range,  # Y축은 변경하지 않음
                    padding=0,
                    update=True
                )
                
                logger.info(f"X축 오토레인지 완료: x=[{x_min}, {x_max}], 전체 데이터={data_length}개")
                print(f"X축이 전체 데이터 범위로 조정되었습니다 ({data_length}개 캔들)")
            else:
                print("표시할 데이터가 없습니다.")
            
        except Exception as e:
            logger.error(f"X축 오토레인지 중 오류: {e}")
            print(f"X축 오토레인지 중 오류가 발생했습니다: {e}")
    
    def on_timeframe_button_clicked(self, timeframe_display):
        """타임프레임 버튼 클릭 처리 - 토글 기능 포함"""
        try:
            # 모든 버튼의 체크 상태 해제
            for tf_display, btn in self.timeframe_buttons.items():
                btn.setChecked(False)
            
            # 클릭된 버튼만 체크
            if timeframe_display in self.timeframe_buttons:
                self.timeframe_buttons[timeframe_display].setChecked(True)
                
                # 실제 타임프레임 변경 로직 호출
                self.on_timeframe_changed(timeframe_display)
                
                logger.debug(f"타임프레임 버튼 토글: {timeframe_display}")
            
        except Exception as e:
            logger.error(f"타임프레임 버튼 클릭 처리 중 오류: {e}")
    
    def update_timeframe_button_states(self, active_timeframe_display):
        """타임프레임 버튼 상태를 현재 타임프레임에 맞춰 업데이트"""
        try:
            # 모든 버튼 체크 해제
            for tf_display, btn in self.timeframe_buttons.items():
                btn.setChecked(False)
            
            # 현재 활성 타임프레임 버튼만 체크
            if active_timeframe_display in self.timeframe_buttons:
                self.timeframe_buttons[active_timeframe_display].setChecked(True)
                logger.debug(f"타임프레임 버튼 상태 업데이트: {active_timeframe_display} 활성화")
            
        except Exception as e:
            logger.error(f"타임프레임 버튼 상태 업데이트 중 오류: {e}")
    
    def show_time_jump_dialog(self):
        """특정 시간으로 이동하는 대화상자 표시"""
        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDateTimeEdit, QDialogButtonBox, QMessageBox
            from PyQt6.QtCore import QDateTime
            
            dialog = QDialog(self)
            dialog.setWindowTitle("특정 시간으로 이동")
            dialog.setModal(True)
            dialog.resize(400, 200)
            
            layout = QVBoxLayout(dialog)
            
            # 설명 라벨
            info_label = QLabel("이동할 날짜와 시간을 선택하세요:")
            info_label.setStyleSheet("font-size: 12px; margin-bottom: 10px;")
            layout.addWidget(info_label)
            
            # 날짜/시간 선택기
            datetime_edit = QDateTimeEdit()
            datetime_edit.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
            datetime_edit.setCalendarPopup(True)
            
            # 현재 시간으로 초기화
            if self.chart_data is not None and len(self.chart_data) > 0:
                # 중간 시점으로 초기화 (데이터가 있는 범위)
                middle_index = len(self.chart_data) // 2
                middle_time = self.chart_data.index[middle_index]
                datetime_edit.setDateTime(QDateTime.fromString(
                    middle_time.strftime("%Y-%m-%d %H:%M:%S"), 
                    "yyyy-MM-dd hh:mm:ss"
                ))
            else:
                datetime_edit.setDateTime(QDateTime.currentDateTime())
            
            layout.addWidget(datetime_edit)
            
            # 빠른 선택 버튼들
            quick_layout = QHBoxLayout()
            
            # 1년 전 버튼
            year_ago_btn = QPushButton("1년 전")
            year_ago_btn.clicked.connect(lambda: datetime_edit.setDateTime(
                QDateTime.currentDateTime().addDays(-365)
            ))
            quick_layout.addWidget(year_ago_btn)
            
            # 6개월 전 버튼
            six_months_ago_btn = QPushButton("6개월 전")
            six_months_ago_btn.clicked.connect(lambda: datetime_edit.setDateTime(
                QDateTime.currentDateTime().addDays(-180)
            ))
            quick_layout.addWidget(six_months_ago_btn)
            
            # 3개월 전 버튼
            three_months_ago_btn = QPushButton("3개월 전")
            three_months_ago_btn.clicked.connect(lambda: datetime_edit.setDateTime(
                QDateTime.currentDateTime().addDays(-90)
            ))
            quick_layout.addWidget(three_months_ago_btn)
            
            # 1개월 전 버튼
            month_ago_btn = QPushButton("1개월 전")
            month_ago_btn.clicked.connect(lambda: datetime_edit.setDateTime(
                QDateTime.currentDateTime().addDays(-30)
            ))
            quick_layout.addWidget(month_ago_btn)
            
            layout.addLayout(quick_layout)
            
            # 확인/취소 버튼
            button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            # 대화상자 실행
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_datetime = datetime_edit.dateTime().toPyDateTime()
                self.jump_to_time(selected_datetime)
                
        except Exception as e:
            logger.error(f"시간 이동 대화상자 표시 중 오류: {e}")
            try:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "오류", f"시간 이동 기능에 오류가 발생했습니다: {e}")
            except:
                print(f"시간 이동 기능에 오류가 발생했습니다: {e}")
    
    def jump_to_time(self, target_datetime):
        """특정 시간으로 차트 이동 - 개선된 버전"""
        try:
            logger.info(f"시간 이동 시작: {target_datetime}")
            
            if self.chart_data is None or len(self.chart_data) == 0:
                print("차트 데이터가 없습니다.")
                return
            
            # 1. 먼저 캐시된 데이터에서 목표 시간 찾기 (기존 기준)
            target_index = self.find_closest_time_index(target_datetime)
            
            if target_index is not None:
                # 캐시된 데이터에서 찾은 경우 바로 이동
                self.set_viewport_around_index(target_index)
                logger.info(f"캐시에서 시간 이동 완료: 인덱스 {target_index}")
                print(f"시간 이동 완료: {target_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                return
            
            # 2. 캐시에 없고 시간이 많이 다른 경우, 목표 시간이 현재 데이터 범위와 얼마나 떨어져 있는지 확인
            current_data_start = self.chart_data.index[0]
            current_data_end = self.chart_data.index[-1]
            target_timestamp = pd.Timestamp(target_datetime)
            
            # 목표 시간이 현재 데이터 범위에서 벗어난 정도 계산
            if target_timestamp < current_data_start:
                time_gap = current_data_start - target_timestamp
                direction = "과거"
            elif target_timestamp > current_data_end:
                time_gap = target_timestamp - current_data_end
                direction = "미래"
            else:
                # 데이터 범위 내에 있는데 찾을 수 없는 경우 (데이터가 드문드문한 경우)
                time_gap = timedelta(0)
                direction = "범위내"
            
            # 3. 시간 차이가 크면 새 데이터 로드, 작으면 현재 데이터에서 처리
            timeframe_delta = self.get_timeframe_delta()
            significant_gap_threshold = timeframe_delta * 50  # 50배 이상 차이나면 새 데이터 로드
            
            if time_gap > significant_gap_threshold:
                logger.info(f"목표 시간이 현재 데이터에서 {direction} 방향으로 {time_gap} 떨어져 있음 (임계값: {significant_gap_threshold})")
                print(f"목표 시간이 현재 데이터에서 멀리 떨어져 있어 새 데이터를 로드합니다...")
                self.load_data_around_time(target_datetime)
            else:
                # 시간 차이가 크지 않으면 관대한 기준으로 다시 찾기
                relaxed_index = self.find_closest_time_index_relaxed(target_datetime)
                if relaxed_index is not None:
                    self.set_viewport_around_index(relaxed_index)
                    logger.info(f"관대한 기준으로 시간 이동 완료: 인덱스 {relaxed_index}")
                    print(f"시간 이동 완료: {target_datetime.strftime('%Y-%m-%d %H:%M:%S')} (근사값)")
                else:
                    logger.warning(f"목표 시간을 찾을 수 없음: {target_datetime}")
                    print("목표 시간을 찾을 수 없습니다. 다른 시간을 시도해보세요.")
                
        except Exception as e:
            logger.error(f"시간 이동 중 오류: {e}")
            print(f"시간 이동 중 오류가 발생했습니다: {e}")
    
    def find_closest_time_index(self, target_datetime):
        """캐시된 데이터에서 목표 시간에 가장 가까운 인덱스 찾기"""
        try:
            if self.chart_data is None or len(self.chart_data) == 0:
                return None
            
            # 목표 시간을 pandas Timestamp로 변환
            target_timestamp = pd.Timestamp(target_datetime)
            
            # 시간 차이 계산하여 가장 가까운 인덱스 찾기
            time_diff = pd.Series((self.chart_data.index - target_timestamp)).abs()
            closest_index = time_diff.argmin()
            
            # 시간 차이가 너무 크면 (타임프레임의 10배 이상) None 반환
            min_diff = time_diff.iloc[closest_index]
            timeframe_delta = self.get_timeframe_delta()
            
            if min_diff > timeframe_delta * 10:
                logger.warning(f"목표 시간이 데이터 범위에서 너무 멀음: 차이={min_diff}, 임계값={timeframe_delta * 10}")
                return None
                
            return closest_index
            
        except Exception as e:
            logger.error(f"가장 가까운 시간 인덱스 찾기 중 오류: {e}")
            return None
    
    def find_closest_time_index_relaxed(self, target_datetime):
        """더 관대한 기준으로 목표 시간에 가장 가까운 인덱스 찾기 (원격 데이터 로드용)"""
        try:
            if self.chart_data is None or len(self.chart_data) == 0:
                return None
            
            # 목표 시간을 pandas Timestamp로 변환
            target_timestamp = pd.Timestamp(target_datetime)
            
            # 시간 차이 계산하여 가장 가까운 인덱스 찾기
            time_diff = pd.Series((self.chart_data.index - target_timestamp)).abs()
            closest_index = time_diff.argmin()
            
            # 관대한 기준: 타임프레임의 100배까지 허용 (먼 시간에 대해서는 더 관대하게)
            min_diff = time_diff.iloc[closest_index]
            timeframe_delta = self.get_timeframe_delta()
            relaxed_threshold = timeframe_delta * 100  # 10배에서 100배로 확장
            
            if min_diff > relaxed_threshold:
                logger.warning(f"목표 시간이 매우 멀음 (관대한 기준): 차이={min_diff}, 임계값={relaxed_threshold}")
                return None
                
            logger.info(f"관대한 기준으로 목표 시간 찾음: 차이={min_diff}, 인덱스={closest_index}")
            return closest_index
            
        except Exception as e:
            logger.error(f"관대한 기준 시간 인덱스 찾기 중 오류: {e}")
            return None
    
    def get_timeframe_delta(self):
        """현재 타임프레임에 해당하는 시간 간격 반환"""
        timeframe_deltas = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "1h": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "1d": timedelta(days=1)
        }
        return timeframe_deltas.get(self.current_timeframe, timedelta(hours=1))
    
    def set_viewport_around_index(self, center_index, width=200):
        """지정된 인덱스 주변으로 뷰포트 설정"""
        try:
            if self.chart_data is None or len(self.chart_data) == 0:
                return
            
            data_length = len(self.chart_data)
            half_width = width // 2
            
            # 뷰포트 범위 계산
            x_min = max(0, center_index - half_width)
            x_max = min(data_length - 1, center_index + half_width)
            
            # 실제 데이터가 있는 범위로 제한
            if x_max <= x_min:
                x_max = x_min + 1
            
            # 해당 범위의 가격 범위 계산
            visible_data = self.chart_data.iloc[int(x_min):int(x_max)+1]
            if not visible_data.empty:
                price_min = visible_data['low'].min()
                price_max = visible_data['high'].max()
                
                # 적절한 여백 추가 (5% 상하 여백)
                price_range = price_max - price_min
                if price_range > 0:
                    margin = price_range * 0.05
                    y_min = price_min - margin
                    y_max = price_max + margin
                else:
                    margin = price_min * 0.01 if price_min > 0 else 1000
                    y_min = price_min - margin
                    y_max = price_max + margin
            else:
                # 폴백: 전체 데이터 기준
                y_min = self.chart_data['low'].min()
                y_max = self.chart_data['high'].max()
            
            # 뷰포트 설정
            view_box = self.candlestick_chart.getViewBox()
            view_box.disableAutoRange()
            view_box.setRange(
                xRange=[x_min, x_max],
                yRange=[y_min, y_max],
                padding=0,
                update=True
            )
            
            logger.info(f"뷰포트 설정 완료: center={center_index}, x=[{x_min:.1f}, {x_max:.1f}], y=[{y_min:.0f}, {y_max:.0f}]")
            
        except Exception as e:
            logger.error(f"뷰포트 설정 중 오류: {e}")
    
    def load_data_around_time(self, target_datetime):
        """특정 시간 주변의 데이터를 API에서 로드 - 목표 시간 중심으로 데이터 교체"""
        try:
            logger.info(f"특정 시간 주변 데이터 로드: {target_datetime}")
            
            # 1. 먼저 해당 시간에 데이터가 존재하는지 확인 (소량 테스트)
            test_data = self.upbit_api.get_candles(
                symbol=self.current_symbol,
                timeframe=self.current_timeframe,
                count=1  # 1개만 가져와서 존재 여부 확인
            )
            
            if test_data is None or test_data.empty:
                logger.warning(f"현재 심볼({self.current_symbol})과 타임프레임({self.current_timeframe})에 대한 데이터가 존재하지 않습니다.")
                print("해당 코인/타임프레임에 대한 데이터가 존재하지 않습니다.")
                return
            
            # 2. 목표 시간 중심으로 더 많은 데이터 가져오기
            logger.info(f"목표 시간 {target_datetime} 중심으로 새 데이터 로드")
            new_data = self.upbit_api.get_candles(
                symbol=self.current_symbol,
                timeframe=self.current_timeframe,
                count=200  # 업비트 API 최대 제한 (200개)
            )
            
            if new_data is None or new_data.empty:
                logger.warning("새 데이터를 가져올 수 없습니다.")
                print("해당 시간대의 데이터를 가져올 수 없습니다.")
                return
            
            # 3. 데이터 인덱스 확인 및 수정
            new_data = self._ensure_datetime_index(new_data)
            
            # 4. 기존 데이터 완전 교체 (목표 시간이 멀 때는 이전 데이터 지우기)
            logger.info(f"기존 데이터 교체: 기존 {len(self.chart_data) if self.chart_data is not None else 0}개 → 새로운 {len(new_data)}개")
            
            # 캐시도 업데이트 (기존 데이터 교체)
            self.cache_data(self.current_symbol, self.current_timeframe, new_data)
            
            # 차트 데이터 완전 교체
            self.chart_data = new_data
            
            logger.info(f"목표 시간 중심 데이터 로드 완료: {len(self.chart_data)}개 캔들 (업비트 API 제한: 200개)")
            print(f"목표 시간 중심 데이터 로드 완료: {len(self.chart_data)}개 캔들")
            
            # 5. 차트 업데이트 (뷰포트 보존하지 않음 - 새로운 데이터 범위에 맞춤)
            self.update_chart(preserve_viewport=False)
            
            # 6. 목표 시간으로 뷰포트 이동 시도 (더 관대한 기준으로)
            target_index = self.find_closest_time_index_relaxed(target_datetime)
            if target_index is not None:
                self.set_viewport_around_index(target_index)
                logger.info(f"시간 이동 완료: 인덱스 {target_index}")
                print(f"시간 이동 완료: {target_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                # 목표 시간을 찾을 수 없어도 데이터의 중간 지점으로 이동
                middle_index = len(self.chart_data) // 2
                self.set_viewport_around_index(middle_index)
                logger.info(f"목표 시간을 찾을 수 없어 중간 지점으로 이동: 인덱스 {middle_index}")
                print(f"목표 시간을 정확히 찾을 수 없어 데이터 중간 지점으로 이동했습니다.")
                
        except Exception as e:
            logger.error(f"특정 시간 주변 데이터 로드 중 오류: {e}")
            print(f"데이터 로드 중 오류가 발생했습니다: {e}")
    
    def find_closest_time_index_in_data(self, target_datetime, data):
        """특정 데이터에서 목표 시간에 가장 가까운 인덱스 찾기"""
        try:
            if data is None or len(data) == 0:
                return None
            
            target_timestamp = pd.Timestamp(target_datetime)
            time_diff = abs(data.index - target_timestamp)
            return time_diff.argmin()
            
        except Exception as e:
            logger.error(f"데이터에서 가장 가까운 시간 인덱스 찾기 중 오류: {e}")
            return None
    
    def get_cached_data(self, symbol, timeframe):
        """캐시에서 데이터 가져오기"""
        try:
            cache_key = f"{symbol}_{timeframe}"
            
            if cache_key in self.coin_data_cache:
                # 접근 시간 업데이트 (LRU)
                self.cache_access_time[cache_key] = datetime.now()
                logger.debug(f"캐시에서 데이터 로드: {cache_key}, 크기={len(self.coin_data_cache[cache_key])}개")
                return self.coin_data_cache[cache_key].copy()
            
            return None
            
        except Exception as e:
            logger.error(f"캐시 데이터 로드 중 오류: {e}")
            return None
    
    def cache_data(self, symbol, timeframe, data):
        """데이터를 캐시에 저장"""
        try:
            if data is None or data.empty:
                return
                
            cache_key = f"{symbol}_{timeframe}"
            
            # 캐시 크기 제한 확인
            if len(self.coin_data_cache) >= self.cache_max_size and cache_key not in self.coin_data_cache:
                # LRU 방식으로 가장 오래된 항목 제거
                oldest_key = min(self.cache_access_time.keys(), key=lambda k: self.cache_access_time[k])
                del self.coin_data_cache[oldest_key]
                del self.cache_access_time[oldest_key]
                logger.debug(f"캐시 크기 제한으로 제거: {oldest_key}")
            
            # 데이터 캐시에 저장
            self.coin_data_cache[cache_key] = data.copy()
            self.cache_access_time[cache_key] = datetime.now()
            
            logger.debug(f"데이터 캐시 저장: {cache_key}, 크기={len(data)}개, 총 캐시={len(self.coin_data_cache)}개")
            
        except Exception as e:
            logger.error(f"데이터 캐시 저장 중 오류: {e}")
    
    def merge_cached_data(self, symbol, timeframe, new_data):
        """새 데이터를 캐시된 데이터와 병합"""
        try:
            if new_data is None or new_data.empty:
                return new_data
                
            cache_key = f"{symbol}_{timeframe}"
            cached_data = self.get_cached_data(symbol, timeframe)
            
            if cached_data is not None and not cached_data.empty:
                # 기존 캐시 데이터와 새 데이터 병합
                merged_data = pd.concat([cached_data, new_data]).drop_duplicates().sort_index()
                
                # 메모리 관리: 최대 크기 제한
                if len(merged_data) > self.max_data_points:
                    # 최신 데이터 우선 보존
                    merged_data = merged_data.tail(self.max_data_points)
                
                # 병합된 데이터 다시 캐시에 저장
                self.cache_data(symbol, timeframe, merged_data)
                
                logger.debug(f"데이터 병합 완료: {cache_key}, 기존={len(cached_data)}개, 새로운={len(new_data)}개, 병합={len(merged_data)}개")
                return merged_data
            else:
                # 캐시된 데이터가 없으면 새 데이터만 캐시에 저장
                self.cache_data(symbol, timeframe, new_data)
                return new_data
                
        except Exception as e:
            logger.error(f"데이터 병합 중 오류: {e}")
            return new_data
    
    def clear_cache(self):
        """캐시 전체 지우기"""
        try:
            cache_count = len(self.coin_data_cache)
            self.coin_data_cache.clear()
            self.cache_access_time.clear()
            logger.info(f"캐시 전체 지우기 완료: {cache_count}개 항목")
            
        except Exception as e:
            logger.error(f"캐시 지우기 중 오류: {e}")
    
    def save_current_coin_settings(self):
        """현재 코인의 뷰포트 및 지표 설정 저장"""
        try:
            coin_key = f"{self.current_symbol}_{self.current_timeframe}"
            
            # 현재 뷰포트 저장
            view_box = self.candlestick_chart.getViewBox()
            current_range = view_box.viewRange()
            
            # 현재 선택된 타임프레임 버튼 확인
            selected_timeframe_display = None
            for tf_display, btn in self.timeframe_buttons.items():
                if btn.isChecked():
                    selected_timeframe_display = tf_display
                    break
            
            # 설정 저장
            self.coin_settings[coin_key] = {
                'viewport': current_range,
                'indicators': self.active_indicators.copy(),
                'timeframe_display': selected_timeframe_display,  # 표시용 타임프레임 추가
                'timestamp': datetime.now()
            }
            
            logger.debug(f"코인 설정 저장: {coin_key}, 타임프레임: {selected_timeframe_display}")
            
        except Exception as e:
            logger.error(f"코인 설정 저장 중 오류: {e}")
    
    def load_coin_settings(self, symbol, timeframe):
        """지정된 코인의 설정 로드"""
        try:
            coin_key = f"{symbol}_{timeframe}"
            
            if coin_key in self.coin_settings:
                settings = self.coin_settings[coin_key]
                
                # 지표 설정 복원
                self.active_indicators = settings.get('indicators', {}).copy()
                
                # 타임프레임 버튼 복원
                timeframe_display = settings.get('timeframe_display')
                if timeframe_display and timeframe_display in self.timeframe_buttons:
                    # 모든 버튼 체크 해제
                    for btn in self.timeframe_buttons.values():
                        btn.setChecked(False)
                    # 저장된 타임프레임 버튼 체크
                    self.timeframe_buttons[timeframe_display].setChecked(True)
                    logger.debug(f"타임프레임 버튼 복원: {timeframe_display}")
                
                # 뷰포트는 데이터 로드 후에 복원 (별도 메서드에서)
                logger.debug(f"코인 설정 로드: {coin_key}, 타임프레임: {timeframe_display}")
                return settings.get('viewport')
            
            return None
            
        except Exception as e:
            logger.error(f"코인 설정 로드 중 오류: {e}")
            return None
    
    def position_overlays(self):
        """오버레이 위치 조정"""
        if not hasattr(self, 'top_control_widget') or not hasattr(self, 'bottom_action_widget'):
            return
            
        # 차트 영역의 실제 크기 가져오기
        chart_widget = self.top_control_widget.parent()
        if chart_widget:
            chart_rect = chart_widget.rect()
            
            # 상단 컨트롤 위치 및 크기 조정 (차트 폭에 맞춤)
            control_width = max(chart_rect.width() - 20, 300)  # 최소 300px 보장
            self.top_control_widget.resize(control_width, 40)
            self.top_control_widget.move(10, 10)
            
            # 하단 액션 버튼 위치 (우측 하단 모서리)
            action_width = 45
            action_height = 280  # 7개 버튼을 위해 높이 증가 (35px * 7 + 8px * 6간격 + 16px 패딩)
            right_margin = 15
            bottom_margin = 15
            
            self.bottom_action_widget.resize(action_width, action_height)
            self.bottom_action_widget.move(
                chart_rect.width() - action_width - right_margin,
                chart_rect.height() - action_height - bottom_margin
            )
            
            # 위젯이 보이도록 설정
            self.top_control_widget.show()
            self.bottom_action_widget.show()
            
            # Z-order 설정 (다른 위젯 위에 표시)
            self.top_control_widget.raise_()
            self.bottom_action_widget.raise_()
    
    def create_control_area(self):
        """컨트롤 영역 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 탭 위젯
        tab_widget = QTabWidget()
        tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # 정보 탭
        self.chart_info_panel = ChartInfoPanel()
        tab_widget.addTab(self.chart_info_panel, "📊 정보")
        
        # 지표 관리 탭
        self.indicator_panel = IndicatorManagementPanel()
        tab_widget.addTab(self.indicator_panel, "📈 지표")
        
        layout.addWidget(tab_widget)
        
        return widget
    
    def connect_signals(self):
        """시그널 연결"""        
        # 지표 관리 패널 시그널
        self.indicator_panel.indicator_added.connect(self.on_indicator_added)
        self.indicator_panel.indicator_removed.connect(self.on_indicator_removed)
        self.indicator_panel.indicator_visibility_changed.connect(self.on_indicator_visibility_changed)
        self.indicator_panel.indicator_settings_changed.connect(self.on_indicator_settings_changed)
    
    def setup_infinite_scroll(self):
        """무한 스크롤 설정"""
        try:
            # ViewBox의 범위 변경 신호 연결
            view_box = self.candlestick_chart.getViewBox()
            view_box.sigRangeChanged.connect(self.on_view_range_changed)
            
            logger.info("무한 스크롤 설정 완료")
            
        except Exception as e:
            logger.error(f"무한 스크롤 설정 중 오류: {e}")
    
    def on_view_range_changed(self, view_box, range_data):
        """뷰 범위 변경 시 호출 - 좌측 확장 검출만 수행"""
        try:
            # 데이터가 없거나 로딩 중이면 무시
            if (self.chart_data is None or 
                len(self.chart_data) == 0 or 
                self.is_loading_past_data):
                logger.debug(f"뷰 범위 변경 무시: 데이터={self.chart_data is not None}, 로딩중={self.is_loading_past_data}")
                return
            
            # past_data_exhausted 상태라도 로그 출력
            if self.past_data_exhausted:
                logger.debug(f"과거 데이터 소진 상태이지만 뷰 범위 변경 감지: x_min을 확인합니다")
            
            # x축 범위 가져오기
            x_range = range_data[0]  # [x_min, x_max]
            x_min, x_max = x_range
            
            # 좌측 확장 검출: 뷰포트 시작점이 데이터 시작점을 넘어섰을 때만 트리거
            # x_min이 0보다 작아지면 (데이터 범위를 벗어나면) 과거 데이터 로드
            if x_min < 0:
                if self.past_data_exhausted:
                    logger.info(f"좌측 확장 검출되었으나 과거 데이터가 소진됨: x_min={x_min:.1f}, 현재 데이터={len(self.chart_data)}개")
                else:
                    logger.info(f"좌측 확장 검출: x_min={x_min:.1f} < 0, 과거 데이터 로드 트리거")
                    self.load_past_data()
            else:
                logger.debug(f"뷰포트 범위 정상: x_min={x_min:.1f} >= 0")
                
        except Exception as e:
            logger.error(f"뷰 범위 변경 처리 중 오류: {e}")
    
    def load_past_data(self):
        """과거 데이터 로드 (무한 스크롤)"""
        try:
            # 로딩 상태 설정
            self.is_loading_past_data = True
            
            # 현재 데이터의 가장 오래된 시간 가져오기
            if self.chart_data is None or len(self.chart_data) == 0:
                logger.warning("차트 데이터가 없어 과거 데이터를 로드할 수 없습니다.")
                return
            
            oldest_timestamp = self.chart_data.index[0]
            current_data_count = len(self.chart_data)
            logger.info(f"과거 데이터 로드 시작: 기준 시간={oldest_timestamp}, 현재 데이터={current_data_count}개, 소진상태={self.past_data_exhausted}")
            
            # 업비트 API에서 과거 데이터 200개 가져오기
            logger.info(f"과거 데이터 API 호출: symbol={self.current_symbol}, timeframe={self.current_timeframe}, before={oldest_timestamp}")
            past_data = self.upbit_api.get_candles_before(
                symbol=self.current_symbol,
                timeframe=self.current_timeframe,
                before_timestamp=oldest_timestamp,
                count=200
            )
            
            if past_data is None or past_data.empty:
                logger.warning(f"더 이상 가져올 과거 데이터가 없습니다. (symbol={self.current_symbol}, timeframe={self.current_timeframe}, 현재={len(self.chart_data)}개)")
                self.past_data_exhausted = True
                return
            
            # 가져온 데이터가 매우 적으면 (예: 10개 미만) 소진 가능성 높음
            if len(past_data) < 10:
                logger.warning(f"가져온 과거 데이터가 너무 적음: {len(past_data)}개, 소진 가능성 높음")
                self.past_data_exhausted = True
            
            logger.info(f"API에서 받은 과거 데이터: {len(past_data)}개 캔들")
            
            # 데이터 인덱스 확인 및 수정
            past_data = self._ensure_datetime_index(past_data)
            
            # 기존 데이터와 합치기 (과거 데이터를 앞에 추가)
            combined_data = pd.concat([past_data, self.chart_data]).drop_duplicates()
            combined_data = combined_data.sort_index()
            
            # 메모리 관리: 최대 데이터 포인트 제한
            if len(combined_data) > self.max_data_points:
                # 가장 오래된 데이터부터 제거 (뒤쪽 최신 데이터 유지)
                excess_count = len(combined_data) - self.max_data_points
                combined_data = combined_data.iloc[excess_count:]
                logger.info(f"메모리 관리: {excess_count}개 오래된 캔들 제거, 현재 {len(combined_data)}개 유지")
            
            # 데이터 업데이트
            old_data_count = len(self.chart_data)
            self.chart_data = combined_data
            new_data_count = len(self.chart_data)
            added_count = new_data_count - old_data_count
            
            logger.info(f"과거 데이터 로드 완료: {added_count}개 캔들 추가 (전체: {new_data_count}개)")
            
            # 메모리 사용량 체크 및 로깅
            memory_mb = len(self.chart_data) * 8 * 5 / (1024 * 1024)  # 대략적인 메모리 사용량 (MB)
            logger.debug(f"예상 메모리 사용량: {memory_mb:.1f}MB ({len(self.chart_data)}개 캔들)")
            
            # 실제 추가된 데이터 개수를 전달하여 차트 업데이트
            self.update_chart_with_scroll_preservation(added_count)
            
            # 정보 패널 업데이트
            if hasattr(self, 'chart_info_panel'):
                self.chart_info_panel.set_data_count(len(self.chart_data))
            
        except Exception as e:
            logger.error(f"과거 데이터 로드 중 오류: {e}")
            
        finally:
            # 로딩 상태 해제
            self.is_loading_past_data = False
    
    def update_chart_with_scroll_preservation(self, added_data_count=0):
        """사용자 뷰포트를 절대 보존하면서 차트 업데이트 (무한 스크롤용)"""
        try:
            # 현재 뷰 범위 저장 (사용자의 관심 범위)
            view_box = self.candlestick_chart.getViewBox()
            user_viewport = view_box.viewRange()
            
            # 실제 추가된 데이터 개수 기반으로 x축 오프셋 계산
            data_offset = added_data_count if added_data_count > 0 else 0
            
            # 사용자 뷰포트를 오프셋만큼 조정 (데이터 추가로 인한 인덱스 변화 보정)
            x_range = user_viewport[0]
            y_range = user_viewport[1]
            adjusted_x_min = x_range[0] + data_offset
            adjusted_x_max = x_range[1] + data_offset
            
            preserved_range = [[adjusted_x_min, adjusted_x_max], y_range]
            logger.debug(f"사용자 뷰포트 절대 보존: 오프셋 +{data_offset} (추가된 데이터: {added_data_count}개)")
            
            # 뷰포트 절대 보존하면서 차트 업데이트
            self.update_chart_with_viewport_preservation(preserved_range)
            
        except Exception as e:
            logger.error(f"뷰포트 보존 차트 업데이트 중 오류: {e}")
            # 폴백: 기본 뷰포트 보존 업데이트  
            self.update_chart_with_viewport_preservation()
    
    def reset_infinite_scroll_state(self):
        """무한 스크롤 상태 초기화"""
        self.is_loading_past_data = False
        self.past_data_exhausted = False
        
        # 메모리 정리: 기존 대용량 데이터가 있다면 최신 데이터만 유지
        if self.chart_data is not None and len(self.chart_data) > 500:
            old_count = len(self.chart_data)
            self.chart_data = self.chart_data.tail(200)  # 최신 200개만 유지
            logger.info(f"메모리 정리: {old_count}개 → {len(self.chart_data)}개 캔들로 축소")
        
        logger.debug("무한 스크롤 상태 초기화됨")
    
    def load_initial_data(self):
        """초기 데이터 로드 - 실제 업비트 API 데이터 사용"""
        try:
            logger.info(f"업비트 API에서 데이터 로드 중: {self.current_symbol}, {self.current_timeframe}")
            
            # 업비트 API에서 캔들 데이터 가져오기
            self.chart_data = self.upbit_api.get_candles(
                symbol=self.current_symbol,
                timeframe=self.current_timeframe,
                count=200
            )
            
            if self.chart_data is None or self.chart_data.empty:
                logger.warning("API에서 데이터를 가져올 수 없습니다. 샘플 데이터를 사용합니다.")
                self.chart_data = self.generate_sample_data()
            else:
                logger.info(f"API 데이터 로드 성공: {len(self.chart_data)}개 캔들")
                
                # 데이터 인덱스가 제대로 datetime 형식인지 확인하고 수정
                self.chart_data = self._ensure_datetime_index(self.chart_data)
                
        except Exception as e:
            logger.error(f"데이터 로드 중 오류 발생: {e}")
            logger.info("샘플 데이터로 폴백합니다.")
            self.chart_data = self.generate_sample_data()
        
        # 차트 업데이트 (초기 로드는 뷰포트 보존하지 않음)
        self.update_chart(preserve_viewport=False)
        
        # 정보 패널 업데이트 (초기 로드 시 올바른 타임프레임 표시)
        if hasattr(self, 'chart_info_panel'):
            # 기본 타임프레임이 1일인데 정보패널에서 잘못 표시되는 문제 수정
            display_timeframe = "1일"  # 기본값은 1일
            for tf_display, btn in self.timeframe_buttons.items():
                if btn.isChecked():
                    display_timeframe = tf_display
                    break
            
            self.chart_info_panel.set_symbol_and_timeframe(
                self.current_symbol, 
                display_timeframe  # 내부 형식이 아닌 표시용 형식 전달
            )
            self.chart_info_panel.set_data_count(len(self.chart_data))
        
        # 실시간 시뮬레이션 시작
        self.start_realtime_simulation()
        
        # 오버레이 위치 조정
        QTimer.singleShot(100, self.position_overlays)
    
    def _ensure_datetime_index(self, data):
        """데이터 인덱스가 datetime 형식인지 확인하고 변환"""
        try:
            if data is None or data.empty:
                return data
                
            # 인덱스가 이미 datetime 형식인지 확인
            if pd.api.types.is_datetime64_any_dtype(data.index):
                logger.info("데이터 인덱스가 이미 datetime 형식입니다.")
                return data
                
            # timestamp 컬럼이 있다면 인덱스로 설정
            if 'timestamp' in data.columns:
                logger.info("timestamp 컬럼을 인덱스로 설정합니다.")
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                data.set_index('timestamp', inplace=True)
                return data
                
            # 인덱스를 datetime으로 변환 시도
            try:
                logger.info("인덱스를 datetime으로 변환 중...")
                data.index = pd.to_datetime(data.index)
                return data
            except:
                # 변환 실패시 새로운 datetime 인덱스 생성
                logger.warning("인덱스 변환 실패. 새로운 datetime 인덱스를 생성합니다.")
                date_range = pd.date_range(
                    start=datetime.now() - timedelta(days=len(data)), 
                    periods=len(data), 
                    freq='D'
                )
                data.index = date_range
                return data
                
        except Exception as e:
            logger.error(f"datetime 인덱스 설정 중 오류: {e}")
            return data
    
    def add_indicator(self, indicator_id, params):
        """지표 추가"""
        self.active_indicators[indicator_id] = params
        
        # 지표 계산 및 차트에 추가
        data = self.calculate_indicator_data(params)
        if data is not None:
            # 지표 데이터를 딕셔너리 형태로 전달
            self.candlestick_chart.add_indicator_overlay(indicator_id, data)
            print(f"지표 추가됨: {indicator_id}")
        else:
            print(f"지표 데이터 계산 실패: {indicator_id}")
    
    def calculate_indicator_data(self, params):
        """지표 데이터 계산"""
        if self.chart_data is None:
            return None
            
        indicator_type = params.get("type", "")
        
        if indicator_type == "SMA":
            period = params.get("period", 20)
            return self.chart_data['close'].rolling(window=period).mean()
        elif indicator_type == "EMA":
            period = params.get("period", 20)
            return self.chart_data['close'].ewm(span=period).mean()
        elif indicator_type == "RSI":
            period = params.get("period", 14)
            return self.calculate_rsi(period)
        # 다른 지표들 추가 가능
        
        return None
    
    def calculate_rsi(self, period=14):
        """RSI 계산"""
        if self.chart_data is None:
            return None
            
        delta = self.chart_data['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_sample_data(self, rows=200):
        """현실적인 샘플 데이터 생성 - 이상값 제거"""
        # 시작 날짜 설정
        start_date = datetime.now() - timedelta(days=rows)
        
        # 날짜 인덱스 생성
        dates = [start_date + timedelta(days=i) for i in range(rows)]
        
        # 시드 설정 (항상 동일한 결과)
        np.random.seed(42)
        
        # 현실적인 초기 가격 (비트코인 가격 수준)
        base_price = 50000.0  # 5만원 (합리적인 시작점)
        
        # OHLCV 데이터 생성
        data = []
        current_price = base_price
        
        for i in range(rows):
            # 일간 변동률 (±3% 범위)
            daily_change_percent = np.random.normal(0, 0.02)  # 평균 0%, 표준편차 2%
            daily_change_percent = np.clip(daily_change_percent, -0.05, 0.05)  # ±5% 제한
            
            # 새로운 종가 계산
            new_close = current_price * (1 + daily_change_percent)
            
            # 시가는 이전 종가
            open_price = current_price
            
            # 고가/저가 계산 (당일 변동폭 내에서)
            daily_range = abs(new_close - open_price) * np.random.uniform(1.2, 2.0)
            high_price = max(open_price, new_close) + daily_range * 0.3
            low_price = min(open_price, new_close) - daily_range * 0.3
            
            # 가격이 음수가 되지 않도록 보장
            low_price = max(low_price, current_price * 0.8)  # 최대 20% 하락 제한
            high_price = min(high_price, current_price * 1.2)  # 최대 20% 상승 제한
            
            # 거래량 생성 (현실적인 범위)
            volume = np.random.uniform(1000, 50000)  # 천~5만
            
            data.append({
                'timestamp': dates[i],
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(new_close, 2),
                'volume': round(volume, 2)
            })
            
            # 다음 날을 위해 현재 가격 업데이트
            current_price = new_close
        
        # DataFrame 생성
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        # 데이터 검증 및 이상값 제거
        for col in ['open', 'high', 'low', 'close']:
            # 0 또는 음수 값 제거
            df[col] = df[col].clip(lower=1.0)
            
            # 극단적인 이상값 제거 (IQR 방법)
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # 이상값을 중앙값으로 대체
            median_val = df[col].median()
            df[col] = df[col].clip(lower=max(lower_bound, 1.0), upper=upper_bound)
        
        # 최종 검증
        print(f"📊 샘플 데이터 생성 완료:")
        print(f"  가격 범위: {df['low'].min():.2f} ~ {df['high'].max():.2f}")
        print(f"  평균 가격: {df['close'].mean():.2f}")
        print(f"  데이터 행 수: {len(df)}")
        
        return df
        
        return df
    
    def update_chart(self, preserve_viewport=True):
        """차트 업데이트 - 무한 루프 응급 차단
        
        Args:
            preserve_viewport: 뷰포트 보존 여부 (기본값: True)
        """
        # � 화면 활성 상태 확인
        if hasattr(self, 'update_paused') and self.update_paused:
            print("⏸️ 화면 비활성화 상태 - 차트 업데이트 스킵")
            return
            
        if hasattr(self, 'is_screen_active') and not self.is_screen_active:
            print("💤 화면 비활성화 상태 - 차트 업데이트 스킵")
            return
        
        # �🚨 응급처치: 무한 루프 완전 차단
        if hasattr(self, '_emergency_stop_updates') and self._emergency_stop_updates:
            print("🚨 응급처치: 차트 업데이트 완전 차단 중")
            return
        
        # 업데이트 빈도 제한 (500ms 이내 재요청 차단)
        import time
        current_time = time.time() * 1000
        if hasattr(self, '_last_update_time') and (current_time - self._last_update_time) < 500:
            print(f"🚫 업데이트 빈도 제한: {current_time - self._last_update_time:.0f}ms < 500ms")
            return
        
        if hasattr(self, '_updating_chart') and self._updating_chart:
            print("🚫 이미 업데이트 중 - 건너뛰기")
            return
            
        if self.chart_data is not None:
            print(f"🔄 차트 업데이트 시작 (뷰포트 보존: {preserve_viewport})")
            print(f"  현재 활성 지표: {list(self.active_indicators.keys())}")
            
            self._updating_chart = True
            self._last_update_time = current_time
            
            try:
                # 캔들스틱 데이터만 업데이트 (지표는 내부에서 자동 처리)
                self.candlestick_chart.update_data(self.chart_data, preserve_viewport=preserve_viewport)
                print(f"  ✅ 캔들스틱 차트 업데이트 완료")
                
            except Exception as e:
                print(f"  ❌ 차트 업데이트 실패: {e}")
                logger.warning(f"차트 업데이트 실패: {e}")
                # 오류 발생 시 응급 중단 모드 활성화
                self._emergency_stop_updates = True
                print("🚨 오류로 인한 응급 중단 모드 활성화")
            
            finally:
                # 플래그 해제
                self._updating_chart = False
            
            print(f"🔄 차트 업데이트 완료: 지표 {len(self.active_indicators)}개 활성")
        
        else:
            print("❌ 차트 데이터 없음 - 업데이트 건너뜀")
    
    def reapply_indicators(self):
        """차트 데이터 업데이트 후 활성 지표들을 다시 적용 - 무한 루프 방지 강화"""
        try:
            # 🚫 차트 업데이트 중이면 재적용 건너뛰기 (무한 루프 방지)
            if hasattr(self, '_updating_chart') and self._updating_chart:
                print("🚫 차트 업데이트 중 - 지표 재적용 건너뛰기 (무한 루프 방지)")
                return
                
            # 🚫 지표 재적용 중이면 건너뛰기 (무한 루프 방지)
            if hasattr(self, '_reapply_in_progress') and self._reapply_in_progress:
                print("🚫 지표 재적용 중 - 중복 요청 건너뛰기 (무한 루프 방지)")
                return
            
            if hasattr(self, 'active_indicators') and self.active_indicators:
                self._reapply_in_progress = True
                try:
                    print(f"🔄 지표 재적용 시작: {len(self.active_indicators)}개")
                    for indicator_id, params in self.active_indicators.items():
                        self.calculate_and_add_indicator(indicator_id, params)
                        print(f"  ✅ {indicator_id} 재적용 완료")
                    print(f"🔄 지표 재적용 완료: {len(self.active_indicators)}개")
                    logger.debug(f"지표 재적용 완료: {len(self.active_indicators)}개")
                finally:
                    self._reapply_in_progress = False
            else:
                print("📋 재적용할 활성 지표 없음")
        except Exception as e:
            print(f"❌ 지표 재적용 중 오류: {e}")
            logger.error(f"지표 재적용 중 오류: {e}")
            if hasattr(self, '_reapply_in_progress'):
                self._reapply_in_progress = False
    
    def start_realtime_simulation(self):
        """실시간 시뮬레이션 시작 - 웹소켓 또는 폴링 방식"""
        try:
            # 웹소켓 방식 시도
            if self.use_websocket:
                success = self.start_websocket_realtime()
                if success:
                    logger.info("웹소켓 실시간 업데이트 시작됨")
                    return
                else:
                    logger.warning("웹소켓 연결 실패, 폴링 방식으로 폴백")
                    self.use_websocket = False
            
            # 폴링 방식 (기존 방식)
            self.start_polling_realtime()
            
        except Exception as e:
            logger.error(f"실시간 업데이트 시작 중 오류: {e}")
            # 에러 시 폴링 방식으로 폴백
            self.start_polling_realtime()
    
    def start_websocket_realtime(self) -> bool:
        """웹소켓 기반 실시간 업데이트 시작"""
        try:
            # 기존 웹소켓 연결이 있다면 중지
            if self.realtime_updater:
                self.realtime_updater.stop()
            
            # 새로운 웹소켓 업데이터 생성
            self.realtime_updater = RealtimeChartUpdater(self, self.current_symbol)
            
            # 실시간 업데이트 시작
            success = self.realtime_updater.start()
            
            if success:
                # 웹소켓용 차트 업데이트 메서드 추가
                self.add_websocket_chart_methods()
                
                # 초기 가격 설정
                if self.chart_data is not None and len(self.chart_data) > 0:
                    last_price = self.chart_data['close'].iloc[-1]
                    self.chart_info_panel.simulate_price_update(last_price)
                
                return True
            else:
                return False
                
        except ImportError as e:
            logger.warning(f"웹소켓 패키지 없음: {e}")
            return False
        except Exception as e:
            logger.error(f"웹소켓 실시간 업데이트 시작 실패: {e}")
            return False
    
    def start_polling_realtime(self):
        """폴링 기반 실시간 업데이트 시작 (기존 방식)"""
        # 실시간 업데이트 타이머 (30초마다 실제 가격 확인)
        self.realtime_timer = QTimer()
        self.realtime_timer.timeout.connect(self.simulate_realtime_update)
        self.realtime_timer.start(30000)  # 30초마다 업데이트
        
        # 렌더링 제한 타이머 (버벅임 방지)
        self.render_timer = QTimer()
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self._perform_deferred_render)
        self.pending_chart_update = False
        self.render_delay_ms = 300  # 300ms 렌더링 지연 (부드러운 성능)
        
        # 가격 정보 초기 설정
        if self.chart_data is not None and len(self.chart_data) > 0:
            last_price = self.chart_data['close'].iloc[-1]
            self.chart_info_panel.simulate_price_update(last_price)
            
        logger.info("폴링 기반 실시간 업데이트 시작됨")
    
    def add_websocket_chart_methods(self):
        """웹소켓용 차트 업데이트 메서드 추가"""
        def update_current_price(price):
            """현재가 실시간 업데이트 (메인 스레드에서 안전하게 호출)"""
            try:
                # 메인 스레드에서 실행되도록 QMetaObject.invokeMethod 사용
                QMetaObject.invokeMethod(
                    self, "_update_current_price_safe",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(float, price)
                )
                    
            except Exception as e:
                logger.error(f"현재가 업데이트 중 오류: {e}")
        
        def add_realtime_candle(candle_data):
            """실시간 캔들 추가/업데이트 (메인 스레드에서 안전하게 호출)"""
            try:
                # 메인 스레드에서 실행되도록 QMetaObject.invokeMethod 사용
                QMetaObject.invokeMethod(
                    self, "_add_realtime_candle_safe",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(object, candle_data)
                )
                    
            except Exception as e:
                logger.error(f"실시간 캔들 추가 중 오류: {e}")
        
        def update_current_candle(price, volume=0):
            """현재 진행 중인 캔들 업데이트 (메인 스레드에서 안전하게 호출)"""
            try:
                # 메인 스레드에서 실행되도록 QMetaObject.invokeMethod 사용
                QMetaObject.invokeMethod(
                    self, "_update_current_candle_safe",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(float, price),
                    Q_ARG(float, volume)
                )
                    
            except Exception as e:
                logger.error(f"현재 캔들 업데이트 중 오류: {e}")
        
        # 메서드를 현재 객체에 바인딩
        self.update_current_price = update_current_price
        self.add_realtime_candle = add_realtime_candle
        self.update_current_candle = update_current_candle
    
    @pyqtSlot(float)
    def _update_current_price_safe(self, price):
        """메인 스레드에서 안전하게 현재가 업데이트"""
        try:
            if hasattr(self, 'chart_info_panel'):
                self.chart_info_panel.simulate_price_update(price)
                
            # 차트에 현재가 라인 표시 (가능한 경우)
            if hasattr(self.candlestick_chart, 'update_current_price_line'):
                self.candlestick_chart.update_current_price_line(price)
                
            logger.debug(f"현재가 업데이트: {price:,.0f}원")
                
        except Exception as e:
            logger.error(f"메인 스레드 현재가 업데이트 중 오류: {e}")
    
    @pyqtSlot(object)
    def _add_realtime_candle_safe(self, candle_data):
        """메인 스레드에서 안전하게 실시간 캔들 추가/업데이트"""
        try:
            if self.chart_data is not None and not candle_data.empty:
                new_timestamp = candle_data.index[0]
                
                # 현재 뷰 범위 저장 (실시간 캔들 추가 시 뷰포트 보존)
                view_box = self.candlestick_chart.getViewBox()
                current_range = view_box.viewRange()
                
                # 마지막 캔들의 시간과 비교
                if len(self.chart_data) > 0:
                    last_timestamp = self.chart_data.index[-1]
                    
                    if new_timestamp > last_timestamp:
                        # 새로운 캔들 추가 - 차트 패키지의 기본 동작에 의존
                        self.chart_data = pd.concat([self.chart_data, candle_data])
                        
                        # 데이터 크기 제한 (최대 5000개 캔들) - 메모리 관리를 위해 유지
                        if len(self.chart_data) > self.max_candles:
                            removed_count = len(self.chart_data) - self.max_candles
                            self.chart_data = self.chart_data.tail(self.max_candles)
                            logger.debug(f"메모리 관리: {removed_count}개 캔들 제거")
                        
                        logger.info(f"새 캔들 추가: {new_timestamp}")
                        
                        # 차트 업데이트 (오토레인지 비활성화로 뷰포트 자연 유지, 렌더링 제한)
                        view_box.disableAutoRange()
                        self.schedule_chart_update(preserve_viewport=True)
                        
                    else:
                        # 기존 마지막 캔들 업데이트
                        self.chart_data.iloc[-1] = candle_data.iloc[0]
                        logger.debug(f"마지막 캔들 업데이트: {new_timestamp}")
                        
                        # 차트 업데이트 (오토레인지 비활성화로 뷰포트 자연 유지, 렌더링 제한)
                        view_box.disableAutoRange()
                        self.schedule_chart_update(preserve_viewport=True)
                else:
                    # 첫 캔들 추가
                    self.chart_data = candle_data
                    self.candlestick_chart.update_data(self.chart_data)
                
                # 정보 패널 업데이트
                if hasattr(self, 'chart_info_panel'):
                    self.chart_info_panel.set_data_count(len(self.chart_data))
                
                logger.debug("실시간 캔들 업데이트 완료")
                
        except Exception as e:
            logger.error(f"메인 스레드 실시간 캔들 추가 중 오류: {e}")
            import traceback
            traceback.print_exc()
    
    def update_chart_with_viewport_preservation(self, saved_range=None):
        """뷰포트를 보존하면서 차트 업데이트"""
        try:
            view_box = self.candlestick_chart.getViewBox()
            
            # 저장된 범위가 없으면 현재 범위 사용
            if saved_range is None:
                saved_range = view_box.viewRange()
            
            # 차트 데이터 업데이트 (자동 범위 조정 비활성화, 뷰포트 보존)
            view_box.disableAutoRange()  # 자동 범위 조정 비활성화
            self.candlestick_chart.update_data(self.chart_data, preserve_viewport=True)
            
            # 뷰 범위가 유효한지 확인하고 복원
            x_range, y_range = saved_range
            data_length = len(self.chart_data) if self.chart_data is not None else 0
            
            if data_length > 0:
                # x 범위가 데이터 범위 내에 있는지 확인
                valid_x_min = max(0, min(x_range[0], data_length - 1))
                valid_x_max = min(data_length - 1, max(x_range[1], valid_x_min + 1))
                
                # y 범위 유효성 검사 (가격 데이터 범위 내)
                # 사용자 Y축 범위 절대 보존 - 자동 조정하지 않음
                valid_y_min = y_range[0]
                valid_y_max = y_range[1]
                
                # 뷰포트 복원 (패딩 없이)
                view_box.setRange(
                    xRange=[valid_x_min, valid_x_max], 
                    yRange=[valid_y_min, valid_y_max], 
                    padding=0,
                    update=True
                )
                
                logger.debug(f"뷰포트 보존 완료: x=[{valid_x_min:.1f}, {valid_x_max:.1f}], y=[{valid_y_min:.0f}, {valid_y_max:.0f}]")
            
        except Exception as e:
            logger.error(f"뷰포트 보존 차트 업데이트 중 오류: {e}")
            import traceback
            traceback.print_exc()
            # 폴백: 기본 차트 업데이트
            try:
                self.candlestick_chart.update_data(self.chart_data, preserve_viewport=False)
            except:
                pass
    
    @pyqtSlot(float, float)
    def _update_current_candle_safe(self, price, volume):
        """메인 스레드에서 안전하게 현재 진행 중인 캔들 업데이트"""
        try:
            if self.chart_data is not None and len(self.chart_data) > 0:
                # 현재 뷰 범위 저장
                view_box = self.candlestick_chart.getViewBox()
                current_range = view_box.viewRange()
                
                # 마지막 캔들 업데이트
                last_idx = len(self.chart_data) - 1
                
                # 고가/저가 업데이트
                current_high = max(self.chart_data.iloc[last_idx]['high'], price)
                current_low = min(self.chart_data.iloc[last_idx]['low'], price)
                
                # 마지막 캔들 업데이트 (안전한 방식으로)
                self.chart_data.at[self.chart_data.index[last_idx], 'high'] = current_high
                self.chart_data.at[self.chart_data.index[last_idx], 'low'] = current_low
                self.chart_data.at[self.chart_data.index[last_idx], 'close'] = price
                if volume > 0:
                    self.chart_data.at[self.chart_data.index[last_idx], 'volume'] += volume
                
                # 뷰포트 보존하면서 차트 업데이트 (현재 캔들 업데이트는 뷰 변경 없음)
                self.update_chart_with_viewport_preservation(current_range)
                
                logger.debug(f"현재 캔들 업데이트: H={current_high:,.0f}, L={current_low:,.0f}, C={price:,.0f}")
                
        except Exception as e:
            logger.error(f"메인 스레드 현재 캔들 업데이트 중 오류: {e}")
            import traceback
            traceback.print_exc()
    
    def stop_realtime_updates(self):
        """실시간 업데이트 중지"""
        try:
            # 웹소켓 업데이터 중지
            if self.realtime_updater:
                self.realtime_updater.stop()
                self.realtime_updater = None
            
            # 폴링 타이머 중지
            if hasattr(self, 'realtime_timer') and self.realtime_timer:
                self.realtime_timer.stop()
                
            logger.info("실시간 업데이트 중지됨")
            
        except Exception as e:
            logger.error(f"실시간 업데이트 중지 중 오류: {e}")
    
    def simulate_realtime_update(self):
        """실시간 업데이트 - 최신 캔들 데이터 가져오기"""
        try:
            # 주기적으로 최신 캔들 1개를 가져와서 업데이트
            latest_data = self.upbit_api.get_candles(
                symbol=self.current_symbol,
                timeframe=self.current_timeframe,
                count=1  # 최신 1개만
            )
            
            if latest_data is not None and not latest_data.empty and len(self.chart_data) > 0:
                # 데이터 인덱스 확인 및 수정
                latest_data = self._ensure_datetime_index(latest_data)
                latest_timestamp = latest_data.index[0]
                latest_price = latest_data['close'].iloc[0]
                
                # 마지막 데이터와 시간이 다르면 새로운 데이터로 업데이트
                last_timestamp = self.chart_data.index[-1]
                if latest_timestamp > last_timestamp:
                    logger.info(f"실시간 데이터 업데이트: {latest_price:,.0f}원 ({latest_timestamp})")
                    
                    # 새로운 데이터 추가
                    self.chart_data = pd.concat([self.chart_data, latest_data])
                    if len(self.chart_data) > 500:
                        self.chart_data = self.chart_data.tail(500)
                    
                    # 차트 업데이트 (뷰포트 보존, 렌더링 제한)
                    self.schedule_chart_update()
                    self.chart_info_panel.set_data_count(len(self.chart_data))
                
                # 정보 패널에 현재 가격 업데이트
                self.chart_info_panel.simulate_price_update(latest_price)
            else:
                # API 호출 실패시 기존 방식으로 폴백
                self.simulate_price_movement()
                
        except Exception as e:
            logger.warning(f"실시간 가격 업데이트 실패: {e}, 시뮬레이션 모드로 전환")
            self.simulate_price_movement()
    
    def schedule_chart_update(self, preserve_viewport=True):
        """차트 업데이트 스케줄링 (렌더링 제한)"""
        self.pending_viewport_preservation = preserve_viewport
        
        if not self.pending_chart_update:
            self.pending_chart_update = True
            self.render_timer.start(self.render_delay_ms)
    
    def _perform_deferred_render(self):
        """지연된 렌더링 실행"""
        try:
            if self.pending_chart_update:
                self.update_chart(preserve_viewport=self.pending_viewport_preservation)
                self.pending_chart_update = False
                logger.debug("지연 렌더링 완료")
        except Exception as e:
            logger.error(f"지연 렌더링 중 오류: {e}")
            self.pending_chart_update = False
    
    def add_simulated_candle(self, current_price):
        """현재가 기반으로 시뮬레이션 캔들 추가"""
        if self.chart_data is None or len(self.chart_data) == 0:
            return
            
        # 새로운 시간 계산
        last_timestamp = self.chart_data.index[-1]
        if self.current_timeframe == "1d":
            new_timestamp = last_timestamp + timedelta(days=1)
        elif self.current_timeframe == "1h":
            new_timestamp = last_timestamp + timedelta(hours=1)
        elif self.current_timeframe == "1m":
            new_timestamp = last_timestamp + timedelta(minutes=1)
        else:
            new_timestamp = last_timestamp + timedelta(hours=1)  # 기본값
        
        # 새로운 캔들 데이터 생성 (현재가 기반)
        last_close = self.chart_data['close'].iloc[-1]
        open_price = last_close
        close_price = current_price
        
        # 고가/저가는 현재가 주변으로 설정
        price_volatility = abs(current_price - last_close) * 0.1
        high_price = max(open_price, close_price) + price_volatility
        low_price = min(open_price, close_price) - price_volatility
        
        # 거래량은 평균 거래량 기반으로 생성
        avg_volume = self.chart_data['volume'].tail(10).mean()
        volume = avg_volume * (0.8 + np.random.random() * 0.4)  # ±20% 변동
        
        # 새로운 데이터 추가
        new_row = pd.DataFrame({
            'open': [open_price],
            'high': [high_price],
            'low': [low_price],
            'close': [close_price],
            'volume': [volume]
        }, index=[new_timestamp])
        
        # 데이터 합치기 (최대 500개 캔들 유지)
        self.chart_data = pd.concat([self.chart_data, new_row])
        if len(self.chart_data) > 500:
            self.chart_data = self.chart_data.tail(500)
        
        # 차트 업데이트
        self.update_chart()
        self.chart_info_panel.set_data_count(len(self.chart_data))
    
    def simulate_price_movement(self):
        """기존 가격 시뮬레이션 방식 (API 실패시 폴백)"""
        if self.chart_data is not None and len(self.chart_data) > 0:
            last_close = self.chart_data['close'].iloc[-1]
            
            # 작은 가격 변동 시뮬레이션 (±0.5%)
            change_percent = np.random.normal(0, 0.005)  # 0.5% 변동성
            new_price = last_close * (1 + change_percent)
            
            # 정보 패널 업데이트
            self.chart_info_panel.simulate_price_update(new_price)
    
    @pyqtSlot(str)
    def on_symbol_changed(self, symbol):
        """심볼 변경 처리 - 코인별 설정 관리"""
        old_symbol = self.current_symbol
        
        # 1. 현재 코인의 설정 저장
        self.save_current_coin_settings()
        
        # 2. 심볼 변경
        self.current_symbol = symbol
        
        # 3. 무한 스크롤 상태 초기화
        self.reset_infinite_scroll_state()
        
        # 4. 웹소켓 업데이터가 있다면 심볼 변경
        if self.realtime_updater:
            self.realtime_updater.change_symbol(symbol)
        
        # 5. 새로운 코인의 설정 로드
        saved_viewport = self.load_coin_settings(symbol, self.current_timeframe)
        
        # 6. 새로운 데이터 로드 - 캐시 우선 활용
        try:
            logger.info(f"심볼 변경: {old_symbol} -> {symbol}")
            
            # 먼저 캐시에서 데이터 확인
            cached_data = self.get_cached_data(symbol, self.current_timeframe)
            
            if cached_data is not None and not cached_data.empty:
                # 캐시된 데이터 사용
                self.chart_data = cached_data
                logger.info(f"캐시에서 심볼 {symbol} 데이터 로드: {len(self.chart_data)}개 캔들")
                print(f"캐시된 데이터 사용: {symbol} ({len(self.chart_data)}개 캔들)")
            else:
                # 캐시에 없으면 API에서 가져오기
                logger.info(f"API에서 심볼 {symbol} 데이터 로드 중...")
                api_data = self.upbit_api.get_candles(
                    symbol=symbol,
                    timeframe=self.current_timeframe,
                    count=200
                )
                
                if api_data is not None and not api_data.empty:
                    # 데이터 인덱스 확인 및 수정
                    api_data = self._ensure_datetime_index(api_data)
                    
                    # 캐시에 저장
                    self.cache_data(symbol, self.current_timeframe, api_data)
                    self.chart_data = api_data
                    
                    logger.info(f"API에서 심볼 {symbol} 데이터 로드 성공: {len(self.chart_data)}개 캔들")
                    print(f"새 데이터 로드 완료: {symbol} ({len(self.chart_data)}개 캔들)")
                else:
                    logger.warning(f"심볼 {symbol}의 데이터를 가져올 수 없습니다. 샘플 데이터를 사용합니다.")
                    self.chart_data = self.generate_sample_data()
                    print(f"샘플 데이터 사용: {symbol}")
                
        except Exception as e:
            logger.error(f"심볼 {symbol} 데이터 로드 중 오류: {e}")
            self.chart_data = self.generate_sample_data()
            print(f"데이터 로드 실패, 샘플 데이터 사용: {symbol}")
        
        # 7. 차트 업데이트 (지표 포함) - 심볼 변경 시 뷰포트 보존하지 않음
        self.update_chart(preserve_viewport=False)
        
        # 8. 저장된 뷰포트가 있다면 복원, 없다면 자동 범위 설정
        if saved_viewport:
            QTimer.singleShot(200, lambda: self._restore_viewport(saved_viewport))
            logger.debug(f"코인 {symbol}의 저장된 뷰포트 복원 예정")
        else:
            QTimer.singleShot(200, self._force_auto_range)
            logger.debug(f"코인 {symbol}의 뷰포트를 기본값으로 설정")
        
        # 9. 정보 패널 업데이트
        if hasattr(self, 'chart_info_panel'):
            self.chart_info_panel.set_symbol_and_timeframe(symbol, self.current_timeframe)
            self.chart_info_panel.set_data_count(len(self.chart_data))
    
    def _restore_viewport(self, viewport):
        """저장된 뷰포트 복원"""
        try:
            if self.chart_data is not None and len(self.chart_data) > 0:
                self.update_chart_with_viewport_preservation(viewport)
                logger.debug("저장된 뷰포트 복원 완료")
        except Exception as e:
            logger.error(f"뷰포트 복원 중 오류: {e}")
            # 복원 실패 시 자동 범위로 폴백
            self._force_auto_range()
    
    @pyqtSlot(str)
    @pyqtSlot(str)
    def on_timeframe_changed(self, timeframe_display):
        """시간대 변경 처리 - 코인별 설정 관리"""
        # 표시용 시간대를 내부 형식으로 변환
        timeframe_map = {
            "1분": "1m", "3분": "3m", "5분": "5m", "15분": "15m", "30분": "30m",
            "1시간": "1h", "4시간": "4h", "1일": "1d", "1주": "1w", "1월": "1M"
        }
        
        old_timeframe = self.current_timeframe
        new_timeframe = timeframe_map.get(timeframe_display, "1d")
        
        # 버튼 상태 즉시 업데이트 (모든 버튼 체크 해제 후 선택된 버튼만 체크)
        for tf_display, btn in self.timeframe_buttons.items():
            btn.setChecked(tf_display == timeframe_display)
        
        # 시간대가 실제로 변경된 경우에만 새 데이터 로드
        if old_timeframe != new_timeframe:
            # 1. 현재 설정 저장
            self.save_current_coin_settings()
            
            # 2. 시간대 변경
            self.current_timeframe = new_timeframe
            
            # 3. 타임프레임 변경 완료 후 버튼 상태 재확인 및 업데이트
            QTimer.singleShot(50, lambda: self.update_timeframe_button_states(timeframe_display))
            
            # 3. 무한 스크롤 상태 초기화
            self.reset_infinite_scroll_state()
            
            # 4. 새로운 시간대의 설정 로드
            saved_viewport = self.load_coin_settings(self.current_symbol, self.current_timeframe)
            
            try:
                logger.info(f"시간대 변경: {old_timeframe} -> {self.current_timeframe}")
                
                # 먼저 캐시에서 데이터 확인
                cached_data = self.get_cached_data(self.current_symbol, self.current_timeframe)
                
                if cached_data is not None and not cached_data.empty:
                    # 캐시된 데이터 사용
                    self.chart_data = cached_data
                    logger.info(f"캐시에서 시간대 {self.current_timeframe} 데이터 로드: {len(self.chart_data)}개 캔들")
                    print(f"캐시된 데이터 사용: {timeframe_display} ({len(self.chart_data)}개 캔들)")
                else:
                    # 캐시에 없으면 API에서 가져오기
                    logger.info(f"API에서 시간대 {self.current_timeframe} 데이터 로드 중...")
                    api_data = self.upbit_api.get_candles(
                        symbol=self.current_symbol,
                        timeframe=self.current_timeframe,
                        count=200
                    )
                    
                    if api_data is not None and not api_data.empty:
                        # 데이터 인덱스 확인 및 수정
                        api_data = self._ensure_datetime_index(api_data)
                        
                        # 캐시에 저장
                        self.cache_data(self.current_symbol, self.current_timeframe, api_data)
                        self.chart_data = api_data
                        
                        logger.info(f"API에서 시간대 {self.current_timeframe} 데이터 로드 성공: {len(self.chart_data)}개 캔들")
                        print(f"새 데이터 로드 완료: {timeframe_display} ({len(self.chart_data)}개 캔들)")
                    else:
                        logger.warning(f"시간대 {self.current_timeframe} 데이터를 가져올 수 없습니다. 리샘플링을 시도합니다.")
                        self.resample_data()
                        print(f"리샘플링 데이터 사용: {timeframe_display}")
                    
            except Exception as e:
                logger.error(f"시간대 {self.current_timeframe} 데이터 로드 중 오류: {e}")
                self.resample_data()  # 폴백으로 리샘플링 시도
            
            # 5. 차트 업데이트 (지표 포함)
            self.update_chart()
            
            # 6. 저장된 뷰포트가 있다면 복원, 없다면 자동 범위 설정
            if saved_viewport:
                QTimer.singleShot(200, lambda: self._restore_viewport(saved_viewport))
                logger.debug(f"시간대 {self.current_timeframe}의 저장된 뷰포트 복원 예정")
            else:
                QTimer.singleShot(200, self._force_auto_range)
                logger.debug(f"시간대 {self.current_timeframe}의 뷰포트를 기본값으로 설정")
        
        # 7. 정보 패널 업데이트
        if hasattr(self, 'chart_info_panel'):
            self.chart_info_panel.set_symbol_and_timeframe(
                self.current_symbol, 
                self.current_timeframe
            )
    
    @pyqtSlot(str, dict)
    def on_indicator_added_from_control(self, indicator_name, params):
        """컨트롤 패널에서 지표 추가"""
        self.indicator_panel.add_indicator(indicator_name, params)
    
    @pyqtSlot(str, dict)
    def on_indicator_added(self, indicator_id, params):
        """지표 추가 처리"""
        self.active_indicators[indicator_id] = params
        self.calculate_and_add_indicator(indicator_id, params)
    
    def calculate_and_add_indicator(self, indicator_id, params):
        """지표 계산 및 차트에 추가"""
        try:
            # 지표 데이터 계산
            data = self.calculate_indicator_data(params)
            
            if data is not None:
                # 차트에 지표 추가 (CandlestickChart는 2개 파라미터만 받음)
                self.candlestick_chart.add_indicator_overlay(indicator_id, data)
                print(f"지표 추가됨: {indicator_id}")
            else:
                print(f"지표 데이터 계산 실패: {indicator_id}")
                
        except Exception as e:
            print(f"지표 추가 중 오류 ({indicator_id}): {e}")
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"지표 추가 중 오류 ({indicator_id}): {e}")
    
    @pyqtSlot(str)
    def on_indicator_removed(self, indicator_id):
        """지표 제거 처리"""
        print(f"🗑️ 지표 제거 요청: {indicator_id}")
        
        # active_indicators에서 제거
        if indicator_id in self.active_indicators:
            del self.active_indicators[indicator_id]
            print(f"  ✅ active_indicators에서 제거 완료")
        
        # 차트에서 지표 제거
        try:
            self.candlestick_chart.remove_indicator_overlay(indicator_id)
            print(f"  ✅ 차트에서 지표 제거 완료")
        except Exception as e:
            print(f"  ❌ 차트에서 지표 제거 실패: {e}")
        
        print(f"🗑️ 지표 제거 완료: {indicator_id}, 남은 활성 지표 수: {len(self.active_indicators)}")
    
    @pyqtSlot(str, bool)
    def on_indicator_visibility_changed(self, indicator_id, visible):
        """지표 가시성 변경"""
        # 차트에서 지표 가시성 토글
        self.candlestick_chart.set_indicator_visibility(indicator_id, visible)
    
    @pyqtSlot(str, dict)
    def on_indicator_settings_changed(self, indicator_id, new_params):
        """지표 설정 변경"""
        self.active_indicators[indicator_id] = new_params
        self.calculate_and_add_indicator(indicator_id, new_params)
    
    @pyqtSlot()
    def on_save_chart(self):
        """차트 저장"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "차트 저장",
            f"{self.current_symbol}_{self.current_timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            "PNG 파일 (*.png);;JPG 파일 (*.jpg)"
        )
        
        if file_path:
            self.save_chart_image(file_path)
    
    @pyqtSlot(dict)
    def on_chart_settings_changed(self, settings):
        """차트 설정 변경"""
        # 차트 표시 옵션 적용
        self.candlestick_chart.set_volume_visible(settings.get('show_volume', True))
        self.candlestick_chart.set_grid_visible(settings.get('show_grid', True))
        self.candlestick_chart.set_crosshair_visible(settings.get('show_crosshair', True))
    
    def calculate_and_add_indicator(self, indicator_id, params):
        """지표 계산 및 추가"""
        if self.chart_data is None or len(self.chart_data) == 0:
            return
        
        indicator_type = params.get('type', '')
        
        try:
            if indicator_type == 'SMA':
                data = self.calculate_sma(params['period'])
                self.candlestick_chart.add_indicator_overlay(indicator_id, data)
                
            elif indicator_type == 'EMA':
                data = self.calculate_ema(params['period'])
                self.candlestick_chart.add_indicator_overlay(indicator_id, data)
                
            elif indicator_type == 'BBANDS':
                data = self.calculate_bollinger_bands(params['period'], params['std'])
                self.candlestick_chart.add_indicator_overlay(indicator_id, data)
                
            elif indicator_type == 'RSI':
                data = self.calculate_rsi(params['period'])
                self.candlestick_chart.add_indicator_overlay(indicator_id, data)
                
            elif indicator_type == 'MACD':
                data = self.calculate_macd(params['fast'], params['slow'], params['signal'])
                self.candlestick_chart.add_indicator_overlay(indicator_id, data)
                
            elif indicator_type == 'Stochastic':
                data = self.calculate_stochastic(params['k'], params['d'])
                self.candlestick_chart.add_indicator_overlay(indicator_id, data)
                
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "지표 계산 오류", 
                f"지표 '{indicator_id}' 계산 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def calculate_sma(self, period):
        """단순 이동 평균 계산"""
        return self.chart_data['close'].rolling(window=period).mean()
    
    def calculate_ema(self, period):
        """지수 이동 평균 계산"""
        return self.chart_data['close'].ewm(span=period, adjust=False).mean()
    
    def calculate_bollinger_bands(self, period, std_multiplier):
        """볼린저 밴드 계산"""
        sma = self.chart_data['close'].rolling(window=period).mean()
        std = self.chart_data['close'].rolling(window=period).std()
        
        upper = sma + (std * std_multiplier)
        lower = sma - (std * std_multiplier)
        
        # 차트에서 기대하는 형식으로 반환
        return {
            f"BBANDS_{period}_{std_multiplier}_upper": upper,
            f"BBANDS_{period}_{std_multiplier}_middle": sma,
            f"BBANDS_{period}_{std_multiplier}_lower": lower
        }
    
    def calculate_rsi(self, period):
        """RSI 계산"""
        delta = self.chart_data['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # 차트에서 기대하는 형식으로 반환
        indicator_id = f"RSI_{period}"
        return {indicator_id: rsi}
    
    def calculate_macd(self, fast_period, slow_period, signal_period):
        """MACD 계산"""
        fast_ema = self.chart_data['close'].ewm(span=fast_period).mean()
        slow_ema = self.chart_data['close'].ewm(span=slow_period).mean()
        
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period).mean()
        histogram = macd_line - signal_line
        
        # 차트에서 기대하는 형식으로 반환
        indicator_id = f"MACD_{fast_period}_{slow_period}_{signal_period}"
        return {
            f"{indicator_id}_line": macd_line,
            f"{indicator_id}_signal": signal_line,
            f"{indicator_id}_histogram": histogram
        }
    
    def calculate_stochastic(self, k_period, d_period):
        """스토캐스틱 계산"""
        low_min = self.chart_data['low'].rolling(window=k_period).min()
        high_max = self.chart_data['high'].rolling(window=k_period).max()
        
        k_percent = 100 * ((self.chart_data['close'] - low_min) / (high_max - low_min))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        # 차트에서 기대하는 형식으로 반환
        indicator_id = f"Stochastic_{k_period}_{d_period}"
        return {
            f"{indicator_id}_k": k_percent,
            f"{indicator_id}_d": d_percent
        }
    
    def resample_data(self):
        """데이터 리샘플링"""
        if self.chart_data is None:
            return
        
        # 시간대별 리샘플링 규칙
        resample_rules = {
            '1m': '1T', '3m': '3T', '5m': '5T', '15m': '15T', '30m': '30T',
            '1h': '1H', '4h': '4H', '1d': '1D', '1w': '1W', '1M': '1M'
        }
        
        rule = resample_rules.get(self.current_timeframe, '1D')
        
        # 리샘플링 수행
        resampled = self.chart_data.resample(rule).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        self.chart_data = resampled
    
    def save_chart_image(self, file_path):
        """차트 이미지 저장"""
        try:
            self.candlestick_chart.save_image(file_path)
            QMessageBox.information(
                self, "저장 완료", 
                f"차트가 성공적으로 저장되었습니다:\n{os.path.basename(file_path)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "저장 실패", 
                f"차트 저장 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def add_trade_markers(self, trades_df):
        """거래 마커 추가"""
        # 기존 마커 제거
        for marker in self.trade_markers:
            self.candlestick_chart.remove_trade_marker(marker)
        
        self.trade_markers = []
        
        # 새 마커 추가
        for trade in trades_df.itertuples():
            marker = TradeMarker(
                timestamp=trade.timestamp,
                price=trade.price,
                trade_type=trade.type
            )
            self.trade_markers.append(marker)
            self.candlestick_chart.add_trade_marker(marker)
    
    def get_current_data(self):
        """현재 차트 데이터 반환"""
        return self.chart_data.copy() if self.chart_data is not None else None
    
    def closeEvent(self, event):
        """창 닫기 이벤트 - 리소스 정리"""
        try:
            # 실시간 업데이트 중지
            self.stop_realtime_updates()
            
            logger.info("차트 뷰 화면 정리 완료")
            
        except Exception as e:
            logger.error(f"차트 뷰 화면 정리 중 오류: {e}")
        
        super().closeEvent(event)
    
    def showEvent(self, event):
        """화면 표시 이벤트 - 차트 초기화 문제 해결"""
        super().showEvent(event)
        
        # 차트가 제대로 표시되도록 지연 후 업데이트
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self._refresh_chart)
        QTimer.singleShot(300, self._refresh_chart)
        
        # 오버레이 위치 조정
        QTimer.singleShot(200, self.position_overlays)
        QTimer.singleShot(400, self.position_overlays)
    
    def resizeEvent(self, event):
        """리사이즈 이벤트 - 차트 크기 조정"""
        super().resizeEvent(event)
        
        # 리사이즈 후 차트 업데이트
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, self._refresh_chart)
        
        # 오버레이 위치 조정
        QTimer.singleShot(100, self.position_overlays)
    
    def _refresh_chart(self):
        """차트 새로고침"""
        try:
            if hasattr(self, 'candlestick_chart') and self.candlestick_chart:
                # 차트 위젯 강제 업데이트
                self.candlestick_chart.update()
                self.candlestick_chart.repaint()
                
                # 차트 데이터가 있다면 다시 로드
                if self.chart_data is not None:
                    self.candlestick_chart.update_data(self.chart_data)
        except Exception as e:
            print(f"차트 새로고침 중 오류: {e}")
    
    def emergency_stop_updates(self):
        """긴급 업데이트 중지"""
        try:
            # 긴급 중지 플래그 설정
            self._emergency_stop_updates = True
            
            # 웹소켓 연결 중지
            if hasattr(self, 'realtime_updater') and self.realtime_updater:
                self.realtime_updater.stop()
                self.realtime_updater = None
            
            # 차트 업데이트 타이머 중지
            if hasattr(self, 'update_timer') and self.update_timer:
                self.update_timer.stop()
            
            # 사용자에게 알림
            QMessageBox.information(self, "긴급 중지", "모든 실시간 업데이트가 중지되었습니다.")
            logger.info("긴급 업데이트 중지 실행됨")
            
        except Exception as e:
            logger.error(f"긴급 중지 실행 중 오류: {e}")
            QMessageBox.warning(self, "오류", f"긴급 중지 실행 중 오류가 발생했습니다: {e}")
    
    def pause_chart_updates(self):
        """차트 업데이트 일시정지 (다른 탭으로 이동시 호출)"""
        print("⏸️ 차트뷰 화면 비활성화 - 업데이트 일시정지")
        self.is_screen_active = False
        self.update_paused = True
        
        try:
            # 실시간 업데이트 중지
            self.stop_realtime_updates()
            print("  📡 실시간 업데이트 중지")
            
            # 렌더링 타이머 중지
            if hasattr(self, 'render_timer') and self.render_timer:
                self.render_timer.stop()
                print("  ⏱️ 렌더링 타이머 정지")
                
        except Exception as e:
            logger.error(f"차트 업데이트 일시정지 중 오류: {e}")
    
    def resume_chart_updates(self):
        """차트 업데이트 재개 (차트뷰 탭 활성화시 호출)"""
        print("▶️ 차트뷰 화면 활성화 - 업데이트 재개")
        self.is_screen_active = True
        self.update_paused = False
        
        try:
            # 차트 데이터 새로고침 (놓친 업데이트 반영)
            if self.current_symbol:
                print("  🔄 차트 데이터 새로고침 중...")
                self.refresh_chart_data()
                
        except Exception as e:
            logger.error(f"차트 업데이트 재개 중 오류: {e}")
    
    def refresh_chart_data(self):
        """차트 데이터 새로고침 (재활성화시 호출)"""
        try:
            # 기존 업데이트 메서드 활용
            self.schedule_chart_update(preserve_viewport=True)
            print("  ✅ 차트 데이터 새로고침 완료")
            
        except Exception as e:
            logger.error(f"차트 데이터 새로고침 중 오류: {e}")
            print(f"  ❌ 차트 데이터 새로고침 실패: {e}")
    
    def is_update_allowed(self):
        """업데이트가 허용되는지 확인"""
        return self.is_screen_active and not self.update_paused

# 직접 실행을 위한 메인 블록
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Qt 애플리케이션 생성
    app = QApplication(sys.argv)
    
    # 차트 뷰 화면 생성
    chart_view = ChartViewScreen()
    chart_view.setWindowTitle("업비트 자동매매 - 차트 뷰 (실시간 API 연동)")
    chart_view.resize(1200, 800)
    chart_view.show()
    
    # 애플리케이션 실행
    sys.exit(app.exec())
