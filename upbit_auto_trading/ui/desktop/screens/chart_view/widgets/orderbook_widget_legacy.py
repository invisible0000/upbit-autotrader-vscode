"""
호가창 위젯 - 실시간 WebSocket 연동 + 모든 코인 지원

차트뷰어의 우측 패널에 표시되는 실시간 호가창입니다.
- 실시간 WebSocket 데이터 연동
- 모든 업비트 코인 지원 (동적 가격 생성)
- DDD 아키텍처 준수
- API 대역폭 절약을 위한 WebSocket 우선 정책
"""

import asyncio
import hashlib
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QColor

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.events.bus.in_memory_event_bus import InMemoryEventBus
from upbit_auto_trading.infrastructure.services.websocket_market_data_service import WebSocketMarketDataService
from upbit_auto_trading.application.use_cases.chart_viewer_websocket_use_case import ChartViewerWebSocketUseCase
from upbit_auto_trading.domain.events.chart_viewer_events import WebSocketOrderbookUpdateEvent


class OrderbookWidget(QWidget):
    """
    호가창 위젯 - 실시간 WebSocket 연동

    주요 기능:
    - 실시간 WebSocket 데이터 연동
    - 모든 업비트 코인 지원 (동적 가격 생성)
    - 코인 선택 시 즉시 반응
    - DDD 아키텍처 준수
    - API 대역폭 절약 정책
    """

    # 시그널 정의
    price_clicked = pyqtSignal(str, float)  # 가격 클릭 시그널
    orderbook_updated = pyqtSignal(dict)    # 호가 업데이트 시그널
    market_impact_analyzed = pyqtSignal(dict)  # 시장 임팩트 분석 시그널 (호환성)
    optimal_price_suggested = pyqtSignal(str, float, str)  # 최적 가격 제안 시그널 (호환성)

    def __init__(self, parent: Optional[QWidget] = None, event_bus: Optional[InMemoryEventBus] = None):
        """호가창 위젯 초기화"""
        super().__init__(parent)

        self._logger = create_component_logger("OrderbookWidget")

        # WebSocket 연동
        self._event_bus = event_bus
        self._websocket_service: Optional[WebSocketMarketDataService] = None
        self._websocket_use_case: Optional[ChartViewerWebSocketUseCase] = None
        self._websocket_initialized = False
        self._websocket_connected = False  # 실제 연결 상태

        # 하이브리드 테스트 설정
        self._test_mode = "websocket"  # "websocket" | "hybrid"
        self._hybrid_rest_enabled = False  # 2단계 테스트용

        # 상태 관리
        self._current_symbol = "KRW-BTC"
        self._current_market = "KRW"
        self._orderbook_data: Dict[str, Any] = {}
        self._max_quantity = 0.0
        self._should_center_on_next_update = True  # 첫 로드시에만 중앙 정렬

        # UI 컴포넌트
        self._orderbook_table: Optional[QTableWidget] = None
        self._spread_label: Optional[QLabel] = None
        self._price_info_label: Optional[QLabel] = None
        self._market_info_label: Optional[QLabel] = None
        self._websocket_status_label: Optional[QLabel] = None

        # 색상 설정
        self._ask_color = QColor(255, 102, 102)  # 매도 (빨간색)
        self._bid_color = QColor(102, 153, 255)  # 매수 (파란색)

        # UI 초기화
        self._setup_ui()

        # WebSocket 초기화 (지연)
        QTimer.singleShot(1000, self._initialize_websocket)

        # WebSocket 우선 시스템 (실거래 환경)
        self._websocket_status_timer = QTimer(self)
        self._websocket_status_timer.timeout.connect(self._check_websocket_status)
        self._websocket_status_timer.start(1000)  # 1초마다 웹소켓 상태 체크

        # 하이브리드 테스트용 REST 보조 타이머 (2단계 테스트)
        self._hybrid_rest_timer = QTimer(self)
        self._hybrid_rest_timer.timeout.connect(self._hybrid_rest_update)
        # 2단계 테스트시에만 활성화

        # WebSocket 백업 타이머 (WebSocket 연결 시 REST 백업)
        self._websocket_backup_timer = QTimer(self)
        self._websocket_backup_timer.timeout.connect(self._websocket_backup_update)

        # 기존 REST 백업 타이머 제거 - WebSocket 우선 정책        # 초기 데이터 로드
        self._load_symbol_data(self._current_symbol)

        self._logger.info("💰 호가창 위젯 초기화 완료 (WebSocket 실시간 연동)")

    def _setup_ui(self) -> None:
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 제목
        title = QLabel("💰 호가창 (실시간)")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # WebSocket 상태 (통일된 폰트 12pt)
        self._websocket_status_label = QLabel("🔴 WebSocket 연결 중...")
        self._websocket_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._websocket_status_label.setStyleSheet("color: #888; font-size: 12pt; font-weight: bold;")
        layout.addWidget(self._websocket_status_label)

        # 스프레드 정보 (2줄로 표시, 12pt)
        self._spread_label = QLabel("스프레드: - ")
        self._spread_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._spread_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        layout.addWidget(self._spread_label)

        # 매수/매도 호가 정보 (12pt)
        self._price_info_label = QLabel("매수: - | 매도: -")
        self._price_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._price_info_label.setStyleSheet("color: #666; font-size: 12pt; font-weight: normal;")
        layout.addWidget(self._price_info_label)

        # 추가 시장 정보 (12pt)
        self._market_info_label = QLabel("거래량: - | 유동성: -")
        self._market_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._market_info_label.setStyleSheet("color: #888; font-size: 12pt; font-weight: normal;")
        layout.addWidget(self._market_info_label)        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # 호가 테이블
        self._orderbook_table = QTableWidget()
        self._setup_table()
        layout.addWidget(self._orderbook_table)

        # 범례 (12pt)
        legend_layout = QHBoxLayout()
        ask_legend = QLabel("■ 매도")
        ask_legend.setStyleSheet(f"color: {self._ask_color.name()}; font-size: 12pt;")
        bid_legend = QLabel("■ 매수")
        bid_legend.setStyleSheet(f"color: {self._bid_color.name()}; font-size: 12pt;")
        click_info = QLabel("💡가격 클릭")
        click_info.setStyleSheet("color: #666; font-size: 12pt;")

        legend_layout.addWidget(ask_legend)
        legend_layout.addStretch()
        legend_layout.addWidget(click_info)
        legend_layout.addStretch()
        legend_layout.addWidget(bid_legend)
        layout.addLayout(legend_layout)

    def _setup_table(self) -> None:
        """호가 테이블 설정"""
        if not self._orderbook_table:
            return

        # 테이블 기본 설정
        self._orderbook_table.setColumnCount(4)  # 번호, 수량, 가격, 누적
        self._orderbook_table.setHorizontalHeaderLabels(["번호", "수량", "가격", "누적"])
        self._orderbook_table.setRowCount(60)  # 매도 30개 + 매수 30개 (업비트 최대 호가)

        # 헤더 설정
        header = self._orderbook_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 번호
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # 수량
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 가격
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # 누적

        # 테이블 설정
        self._orderbook_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._orderbook_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._orderbook_table.cellClicked.connect(self._on_cell_clicked)

        # 중앙 포지션 설정 (30-31행이 보이도록) - 초기화시에만
        QTimer.singleShot(200, self._setup_center_position)  # 데이터 로드 후 중앙 정렬

    def _initialize_websocket(self) -> None:
        """WebSocket 초기화 - 실거래 환경 우선"""
        if not self._event_bus:
            self._logger.warning("이벤트 버스가 없어 WebSocket 초기화 불가 - REST 백업 모드로 전환")
            if self._websocket_status_label:
                self._websocket_status_label.setText("🔴 REST 백업 모드 (웹소켓 미지원)")
            return

        try:
            # WebSocket 서비스 초기화
            self._websocket_service = WebSocketMarketDataService(self._event_bus)
            self._websocket_use_case = ChartViewerWebSocketUseCase(self._websocket_service)

            # 이벤트 구독
            self._event_bus.subscribe(WebSocketOrderbookUpdateEvent, self._on_websocket_orderbook_update)

            self._websocket_initialized = True
            if self._websocket_status_label:
                self._websocket_status_label.setText("🟡 웹소켓 우선 모드 (실거래 최적화)")

            # 현재 심볼 구독
            asyncio.create_task(self._subscribe_current_symbol())

            self._logger.info("✅ 호가창 WebSocket 우선 모드 초기화 완료 (실거래 환경)")

        except Exception as e:
            self._logger.error(f"WebSocket 초기화 실패: {e}")
            if self._websocket_status_label:
                self._websocket_status_label.setText("🔴 웹소켓 오류 - REST 백업 활성화")

    async def _subscribe_current_symbol(self) -> None:
        """현재 심볼 WebSocket 구독"""
        if not self._websocket_use_case:
            return

        try:
            success = await self._websocket_use_case.request_orderbook_subscription(self._current_symbol)
            if success:
                self._websocket_connected = True  # 연결 상태 플래그 설정
                if self._websocket_status_label:
                    self._websocket_status_label.setText("🟢 실시간 연결됨")
                self._logger.info(f"WebSocket 구독 성공: {self._current_symbol}")
                
                # WebSocket 백업 타이머 시작
                self._start_websocket_backup_timer()
            else:
                self._websocket_connected = False
                if self._websocket_status_label:
                    self._websocket_status_label.setText("🔴 구독 실패")

        except Exception as e:
            self._websocket_connected = False
            self._logger.error(f"WebSocket 구독 오류: {e}")
            if self._websocket_status_label:
                self._websocket_status_label.setText("🔴 구독 오류")

    def set_symbol(self, symbol: str) -> None:
        """심볼 설정 - WebSocket 구독 변경 + 즉시 반응"""
        old_symbol = self._current_symbol
        self._current_symbol = symbol

        # 마켓 타입 추출
        if symbol.startswith("KRW-"):
            self._current_market = "KRW"
        elif symbol.startswith("BTC-"):
            self._current_market = "BTC"
        elif symbol.startswith("USDT-"):
            self._current_market = "USDT"
        else:
            self._current_market = "Unknown"

        # 즉시 데이터 로드 (모든 코인 지원)
        self._load_symbol_data(symbol)

        # 심볼 변경시에만 중앙 포지션 설정
        if old_symbol != symbol:
            self._should_center_on_next_update = True  # 코인 변경시에만 중앙 정렬 활성화
            QTimer.singleShot(100, self._setup_center_position)  # 데이터 로드 후 중앙 정렬

        # WebSocket 구독 변경
        if self._websocket_initialized and self._websocket_use_case:
            # 기존 심볼 구독 해제
            if old_symbol and old_symbol != symbol:
                asyncio.create_task(self._unsubscribe_symbol(old_symbol))

            # 새 심볼 구독
            asyncio.create_task(self._subscribe_symbol(symbol))

        self._logger.info(f"호가창 심볼 변경: {symbol} (마켓: {self._current_market})")
        if old_symbol != symbol:
            self._logger.debug(f"🎯 중앙 포지션 스케줄링: {symbol}")

    def _fetch_real_orderbook(self, symbol: str) -> Optional[Dict[str, Any]]:
        """실제 업비트 호가 API 호출"""
        try:
            # 업비트 호가 API 호출
            url = "https://api.upbit.com/v1/orderbook"
            params = {"markets": symbol}

            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()

            data = response.json()
            if not data or len(data) == 0:
                self._logger.warning(f"호가 데이터 없음: {symbol}")
                return None

            orderbook = data[0]  # 첫 번째 마켓 데이터

            # API 응답을 내부 형식으로 변환
            asks = []
            bids = []

            # 호가 단위별로 매도/매수 분리 처리
            for unit in orderbook.get("orderbook_units", []):
                # 매도 호가 (asks) - 가격 높은순 정렬
                asks.append({
                    "price": float(unit["ask_price"]),
                    "quantity": float(unit["ask_size"]),
                    "total": float(unit["ask_size"])
                })

                # 매수 호가 (bids) - 가격 높은순 정렬
                bids.append({
                    "price": float(unit["bid_price"]),
                    "quantity": float(unit["bid_size"]),
                    "total": float(unit["bid_size"])
                })

            # 매도 호가 정렬 (가격 높은순 - 1호가가 가장 낮은 매도가)
            asks.sort(key=lambda x: x["price"])

            # 매수 호가 정렬 (가격 높은순 - 1호가가 가장 높은 매수가)
            bids.sort(key=lambda x: x["price"], reverse=True)

            # 총 수량 누적 계산
            asks_total = 0
            for ask in asks:
                asks_total += ask["quantity"]
                ask["total"] = asks_total

            bids_total = 0
            for bid in bids:
                bids_total += bid["quantity"]
                bid["total"] = bids_total

            real_data = {
                "symbol": symbol,
                "asks": asks,
                "bids": bids,
                "timestamp": orderbook.get("timestamp", datetime.now().isoformat()),
                "market": symbol.split("-")[0],
                "source": "real_api"
            }

            self._logger.info(f"✅ 실제 호가 데이터 로드: {symbol} (매도 {len(asks)}개, 매수 {len(bids)}개)")
            return real_data

        except requests.exceptions.RequestException as e:
            self._logger.error(f"❌ 호가 API 호출 실패: {symbol} - {str(e)}")
            return None
        except Exception as e:
            self._logger.error(f"❌ 호가 데이터 처리 실패: {symbol} - {str(e)}")
            return None

    def _load_symbol_data(self, symbol: str) -> None:
        """심볼별 호가 데이터 로드 - 실제 API 우선, 실패 시 시뮬레이션"""

        # 🎯 1단계: 실제 업비트 호가 API 시도
        real_data = self._fetch_real_orderbook(symbol)
        if real_data:
            # 실제 데이터가 있으면 사용
            self._orderbook_data = real_data

            # 최대 수량 계산
            all_quantities = []
            for ask in real_data["asks"]:
                all_quantities.append(ask["quantity"])
            for bid in real_data["bids"]:
                all_quantities.append(bid["quantity"])
            self._max_quantity = max(all_quantities) if all_quantities else 1.0

            # UI 업데이트
            self._update_orderbook_table()
            self._update_spread_analysis(real_data["asks"], real_data["bids"])
            self._analyze_market_impact(real_data["asks"], real_data["bids"])

            # 시그널 발송
            self.orderbook_updated.emit(self._orderbook_data)

            self._logger.info(f"🌐 실제 호가 데이터 적용: {symbol}")
            return

        # 🎯 2단계: 실제 API 실패 시 시뮬레이션 데이터 사용
        self._logger.warning(f"⚠️ 실제 API 실패, 시뮬레이션 모드: {symbol}")

        # 업비트 주요 코인 설정 (동적 가격 생성 포함)
        known_configs = {
            "KRW-BTC": {"base_price": 45000000, "spread": 100000, "tick": 1000},
            "KRW-ETH": {"base_price": 3800000, "spread": 50000, "tick": 1000},
            "KRW-XRP": {"base_price": 1200, "spread": 10, "tick": 1},
            "KRW-ADA": {"base_price": 850, "spread": 10, "tick": 1},
            "KRW-SOL": {"base_price": 180000, "spread": 5000, "tick": 100},
            "KRW-DOGE": {"base_price": 300, "spread": 5, "tick": 1},
            "KRW-AVAX": {"base_price": 45000, "spread": 1000, "tick": 100},
            "KRW-DOT": {"base_price": 8500, "spread": 100, "tick": 10},
            "KRW-MATIC": {"base_price": 850, "spread": 10, "tick": 1},
            "KRW-SHIB": {"base_price": 0.03, "spread": 0.001, "tick": 0.001},
            "KRW-1INCH": {"base_price": 650, "spread": 10, "tick": 1},
            "KRW-GAS": {"base_price": 4600, "spread": 50, "tick": 10},
            "KRW-GAMEZ": {"base_price": 5200, "spread": 100, "tick": 10},
            "KRW-GLM": {"base_price": 365, "spread": 5, "tick": 1},
            "KRW-GRS": {"base_price": 420, "spread": 10, "tick": 1},
            "KRW-CKB": {"base_price": 18, "spread": 1, "tick": 1},
            "KRW-NEO": {"base_price": 8300, "spread": 100, "tick": 10},
            "KRW-NPXS": {"base_price": 1, "spread": 0.1, "tick": 0.1},
            "KRW-NEWT": {"base_price": 420, "spread": 10, "tick": 1},
            "KRW-NEAR": {"base_price": 3500, "spread": 50, "tick": 10},
            "KRW-GRT": {"base_price": 125, "spread": 5, "tick": 1},
            "KRW-DHFI": {"base_price": 720, "spread": 10, "tick": 1},
            "KRW-MANA": {"base_price": 390, "spread": 10, "tick": 1},
            "KRW-DKA": {"base_price": 21, "spread": 1, "tick": 1},
            "KRW-DEEP": {"base_price": 220, "spread": 5, "tick": 1},
            "KRW-LPT": {"base_price": 8600, "spread": 100, "tick": 10},
            "KRW-RAY": {"base_price": 4500, "spread": 50, "tick": 10},
            "KRW-RVN": {"base_price": 18, "spread": 1, "tick": 1},
            "KRW-ZRO": {"base_price": 2800, "spread": 50, "tick": 10},
            "KRW-RENDER": {"base_price": 5000, "spread": 100, "tick": 10},
            "KRW-LSK": {"base_price": 540, "spread": 10, "tick": 1},
            "KRW-MASK": {"base_price": 1700, "spread": 20, "tick": 10},
            "KRW-OM": {"base_price": 330, "spread": 5, "tick": 1},
            "KRW-ME": {"base_price": 950, "spread": 20, "tick": 1},
        }

        # 설정 가져오기 (없으면 동적 생성)
        config = known_configs.get(symbol)

        if not config:
            # 새로운 코인에 대한 동적 가격 생성
            hash_obj = hashlib.md5(symbol.encode())
            hash_int = int(hash_obj.hexdigest()[:8], 16)

            if symbol.startswith("KRW-"):
                if any(x in symbol.upper() for x in ["SHIB", "DOGE", "PEPE"]):
                    # 밈코인류 - 낮은 가격
                    base_price = (hash_int % 500) + 50
                    tick = 1
                    spread = max(base_price * 0.02, 1)
                elif any(x in symbol.upper() for x in ["BTC", "ETH"]):
                    # 메인코인 - 높은 가격
                    base_price = (hash_int % 10000000) + 1000000
                    tick = 1000
                    spread = base_price * 0.001
                else:
                    # 일반 알트코인 - 중간 가격
                    base_price = (hash_int % 10000) + 500
                    tick = 10 if base_price > 1000 else 1
                    spread = max(base_price * 0.01, 10)
            else:
                # BTC, USDT 마켓
                base_price = (hash_int % 100) + 10
                tick = 0.00000001
                spread = base_price * 0.001

            config = {
                "base_price": base_price,
                "spread": spread,
                "tick": tick
            }

            self._logger.info(f"새 코인 동적 생성: {symbol} (가격: {base_price:,.0f})")

        base_price = config["base_price"]
        spread = config["spread"]
        tick_size = config["tick"]

        # 호가 데이터 생성
        asks = []
        bids = []

        # 매도 호가 생성
        for i in range(10):
            price = base_price + spread + (i * tick_size * 10)
            quantity = 0.05 + (i * 0.02)
            total = sum([ask["quantity"] for ask in asks]) + quantity
            asks.append({"price": price, "quantity": quantity, "total": total})

        # 매수 호가 생성
        for i in range(10):
            price = base_price - (i * tick_size * 10)
            quantity = 0.08 + (i * 0.03)
            total = sum([bid["quantity"] for bid in bids]) + quantity
            bids.append({"price": price, "quantity": quantity, "total": total})

        # 호가 데이터 업데이트
        self._orderbook_data = {
            "symbol": symbol,
            "asks": asks,
            "bids": bids,
            "timestamp": datetime.now().isoformat(),
            "market": self._current_market
        }

        # 최대 수량 계산
        all_quantities = [item["quantity"] for item in asks + bids]
        self._max_quantity = max(all_quantities) if all_quantities else 1.0

        # UI 업데이트
        self._update_orderbook_table()
        self._update_spread_analysis(asks, bids)
        self._analyze_market_impact(asks, bids)

        # 시그널 발송
        self.orderbook_updated.emit(self._orderbook_data)

        self._logger.info(f"심볼 데이터 로드 완료: {symbol} (기준가: {base_price:,})")

    def _update_orderbook_table(self) -> None:
        """호가 테이블 업데이트"""
        if not self._orderbook_table or not self._orderbook_data:
            return

        asks = self._orderbook_data.get("asks", [])
        bids = self._orderbook_data.get("bids", [])

        # 매도 호가 (상위 30개, 역순으로 표시 - 1호가가 맨 아래)
        for i, ask in enumerate(reversed(asks[:30])):
            row = i
            self._set_orderbook_row(row, ask, "ask")

        # 매수 호가 (상위 30개 - 1호가가 맨 위)
        for i, bid in enumerate(bids[:30]):
            row = 30 + i
            self._set_orderbook_row(row, bid, "bid")

        # 중앙 포지션 설정 (1호가 부근이 보이도록)
        self._setup_center_position()

    def _set_orderbook_row(self, row: int, data: Dict[str, Any], order_type: str) -> None:
        """호가 행 설정"""
        if not self._orderbook_table:
            return

        price = data["price"]
        quantity = data["quantity"]
        total = data["total"]

        # 행 번호 계산 (매도: 30→1, 매수: 1→30)
        if order_type == "ask":
            display_number = 30 - (row)  # 30, 29, 28, ..., 1
        else:
            display_number = (row - 29)  # 1, 2, 3, ..., 30

        # 번호
        number_item = QTableWidgetItem(f"{display_number}")
        number_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # 수량
        quantity_item = QTableWidgetItem(f"{quantity:.3f}")
        quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # 가격
        price_item = QTableWidgetItem(f"{price:,.0f}")
        price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        price_item.setData(Qt.ItemDataRole.UserRole, {"price": price, "type": order_type})

        # 누적
        total_item = QTableWidgetItem(f"{total:.3f}")
        total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # 색상 설정
        color = self._ask_color if order_type == "ask" else self._bid_color

        # 수량에 따른 배경색 강도 조절
        intensity = min(quantity / self._max_quantity, 1.0) if self._max_quantity > 0 else 0
        bg_color = QColor(color)
        bg_color.setAlpha(int(50 + 100 * intensity))

        quantity_item.setBackground(bg_color)
        price_item.setBackground(QColor(color.red(), color.green(), color.blue(), 30))
        total_item.setBackground(QColor(color.red(), color.green(), color.blue(), 20))

        # 테이블에 설정
        # 아이템 설정
        self._orderbook_table.setItem(row, 0, number_item)
        self._orderbook_table.setItem(row, 1, quantity_item)
        self._orderbook_table.setItem(row, 2, price_item)
        self._orderbook_table.setItem(row, 3, total_item)

    def _update_spread_analysis(self, asks: list, bids: list) -> None:
        """스프레드 분석 업데이트 - 실거래 환경용 상세 정보"""
        if not asks or not bids:
            return

        best_ask = asks[0]["price"]  # 1호가 매도가 (가장 낮은 매도가)
        best_bid = bids[0]["price"]  # 1호가 매수가 (가장 높은 매수가)
        spread = best_ask - best_bid  # 스프레드 금액
        spread_rate = (spread / best_bid) * 100 if best_bid > 0 else 0  # 스프레드 비율

        # 스프레드 정보 (첫 번째 줄)
        if self._spread_label:
            self._spread_label.setText(f"스프레드: {spread:,.0f}원 ({spread_rate:.3f}%)")
            self._spread_label.setToolTip(
                f"스프레드 분석:\n"
                f"• 스프레드: {spread:,.0f}원\n"
                f"• 스프레드 비율: {spread_rate:.3f}%\n"
                f"• 유동성: {'높음' if spread_rate < 0.01 else '보통' if spread_rate < 0.05 else '낮음'}"
            )

        # 매수/매도 호가 정보 (두 번째 줄)
        if self._price_info_label:
            self._price_info_label.setText(f"매수: {best_bid:,.0f}원 | 매도: {best_ask:,.0f}원")
            self._price_info_label.setToolTip(
                f"호가 정보:\n"
                f"• 매수 1호가: {best_bid:,.0f}원\n"
                f"• 매도 1호가: {best_ask:,.0f}원\n"
                f"• 중간가: {(best_bid + best_ask) / 2:,.0f}원"
            )

        # 추가 시장 정보 (세 번째 줄)
        if self._market_info_label:
            # 호가 수량 분석
            total_ask_qty = sum(ask["quantity"] for ask in asks[:10])
            total_bid_qty = sum(bid["quantity"] for bid in bids[:10])
            liquidity_ratio = total_bid_qty / (total_ask_qty + total_bid_qty) if (total_ask_qty + total_bid_qty) > 0 else 0.5

            # 시장 편향성 분석
            market_bias = "매수우세" if liquidity_ratio > 0.6 else "매도우세" if liquidity_ratio < 0.4 else "균형"

            self._market_info_label.setText(
                f"거래량: 매수 {total_bid_qty:.2f} | 매도 {total_ask_qty:.2f} | 편향: {market_bias}"
            )
            self._market_info_label.setToolTip(
                f"시장 분석:\n"
                f"• 매수 총량(상위10): {total_bid_qty:.2f}\n"
                f"• 매도 총량(상위10): {total_ask_qty:.2f}\n"
                f"• 유동성 비율: {liquidity_ratio:.1%}\n"
                f"• 시장 편향: {market_bias}\n"
                f"• 거래 추천: {'매수 적극' if market_bias == '매도우세' else '매도 적극' if market_bias == '매수우세' else '신중 관망'}"
            )

    def _analyze_market_impact(self, asks: list, bids: list) -> None:
        """시장 임팩트 분석 (간단한 버전)"""
        if not asks or not bids:
            return

        # 간단한 시장 임팩트 분석
        total_ask_liquidity = sum(item["quantity"] for item in asks[:10])
        total_bid_liquidity = sum(item["quantity"] for item in bids[:10])
        total_liquidity = total_ask_liquidity + total_bid_liquidity

        liquidity_imbalance = 0
        if total_liquidity > 0:
            liquidity_imbalance = (total_bid_liquidity - total_ask_liquidity) / total_liquidity

        impact_analysis = {
            "total_ask_liquidity": total_ask_liquidity,
            "total_bid_liquidity": total_bid_liquidity,
            "liquidity_imbalance": liquidity_imbalance,
            "market_depth": total_liquidity
        }

        # 시그널 발송
        self.market_impact_analyzed.emit(impact_analysis)

    def _on_cell_clicked(self, row: int, column: int) -> None:
        """셀 클릭 처리"""
        if not self._orderbook_table or column != 1:  # 가격 열만 처리
            return

        price_item = self._orderbook_table.item(row, column)
        if price_item:
            data = price_item.data(Qt.ItemDataRole.UserRole)
            if data:
                price = data["price"]
                order_type = data["type"]
                self.price_clicked.emit(order_type, price)
                self._logger.info(f"💰 가격 클릭: {order_type} {price:,.0f}원")

    async def _subscribe_symbol(self, symbol: str) -> None:
        """심볼 WebSocket 구독"""
        if not self._websocket_use_case:
            return

        try:
            success = await self._websocket_use_case.request_orderbook_subscription(symbol)
            if success:
                self._websocket_connected = True  # 연결 상태 플래그 설정
                if self._websocket_status_label:
                    self._websocket_status_label.setText("🟢 실시간 연결됨")
                self._logger.info(f"WebSocket 구독 성공: {symbol}")
                
                # WebSocket 백업 타이머 시작 (15초 간격으로 REST 백업)
                self._start_websocket_backup_timer()
            else:
                self._websocket_connected = False
                if self._websocket_status_label:
                    self._websocket_status_label.setText("🔴 구독 실패")

        except Exception as e:
            self._websocket_connected = False
            self._logger.error(f"WebSocket 구독 오류 - {symbol}: {e}")
            if self._websocket_status_label:
                self._websocket_status_label.setText("🔴 구독 오류")

    async def _unsubscribe_symbol(self, symbol: str) -> None:
        """심볼 WebSocket 구독 해제"""
        if not self._websocket_use_case:
            return

        try:
            await self._websocket_use_case.cancel_symbol_subscription(symbol)
            self._websocket_connected = False  # 연결 상태 플래그 해제
            self._stop_websocket_backup_timer()  # 백업 타이머 중지
            self._logger.info(f"WebSocket 구독 해제: {symbol}")
        except Exception as e:
            self._logger.error(f"WebSocket 구독 해제 오류 - {symbol}: {e}")

    def _on_websocket_orderbook_update(self, event: WebSocketOrderbookUpdateEvent) -> None:
        """WebSocket 호가창 업데이트 이벤트 처리"""
        try:
            # 현재 심볼과 일치하는지 확인
            if event.symbol != self._current_symbol:
                return

            # 실시간 데이터로 업데이트
            self._update_realtime_orderbook(event.orderbook_data)

            # 스프레드 정보 업데이트
            if event.spread_percent > 0 and self._spread_label:
                self._spread_label.setText(f"스프레드: {event.spread_percent:.3f}% (실시간)")

            # WebSocket 상태 업데이트
            if self._websocket_status_label:
                self._websocket_status_label.setText("🟢 실시간 업데이트")

            self._logger.debug(f"WebSocket 호가창 업데이트: {event.symbol}")

        except Exception as e:
            self._logger.error(f"WebSocket 이벤트 처리 오류: {e}")

    def _update_realtime_orderbook(self, orderbook_data: Dict[str, Any]) -> None:
        """실시간 호가 데이터로 내부 상태 업데이트"""
        try:
            if 'orderbook_units' in orderbook_data:
                units = orderbook_data['orderbook_units']

                asks = []
                bids = []

                for unit in units:
                    if 'ask_price' in unit and 'ask_size' in unit:
                        asks.append({
                            'price': float(unit['ask_price']),
                            'quantity': float(unit['ask_size'])
                        })

                    if 'bid_price' in unit and 'bid_size' in unit:
                        bids.append({
                            'price': float(unit['bid_price']),
                            'quantity': float(unit['bid_size'])
                        })

                # 정렬
                asks.sort(key=lambda x: x['price'])
                bids.sort(key=lambda x: x['price'], reverse=True)

                # 누적 수량 계산
                for i, ask in enumerate(asks):
                    ask['total'] = sum(a['quantity'] for a in asks[:i + 1])

                for i, bid in enumerate(bids):
                    bid['total'] = sum(b['quantity'] for b in bids[:i + 1])

                self._orderbook_data = {
                    'asks': asks,
                    'bids': bids,
                    'timestamp': datetime.now(),
                    'symbol': self._current_symbol
                }

                # 최대 수량 재계산
                all_quantities = [item['quantity'] for item in asks + bids]
                if all_quantities:
                    self._max_quantity = max(all_quantities)

                # UI 업데이트
                self._update_orderbook_table()

        except Exception as e:
            self._logger.error(f"실시간 호가 데이터 변환 오류: {e}")

    # 기타 메소드들
    def get_current_symbol(self) -> str:
        """현재 심볼 반환"""
        return self._current_symbol

    def get_websocket_status(self) -> Dict[str, Any]:
        """WebSocket 연결 상태 반환"""
        return {
            'initialized': self._websocket_initialized,
            'current_symbol': self._current_symbol,
            'has_service': self._websocket_service is not None,
            'has_use_case': self._websocket_use_case is not None
        }

    def get_widget_info(self) -> Dict[str, Any]:
        """위젯 정보 반환"""
        return {
            "current_symbol": self._current_symbol,
            "current_market": self._current_market,
            "has_data": bool(self._orderbook_data),
            "websocket_enabled": self._websocket_initialized
        }

    def _refresh_orderbook(self) -> None:
        """실시간 호가 갱신 (REST API 백업용)"""
        if self._current_symbol:
            self._logger.debug(f"🔄 REST 백업 호가 갱신: {self._current_symbol}")
            self._load_symbol_data(self._current_symbol)

    def _hybrid_rest_update(self) -> None:
        """하이브리드 테스트용 REST 보조 갱신"""
        if self._current_symbol and self._hybrid_rest_enabled:
            self._logger.debug(f"🔄 하이브리드 REST 보조 갱신: {self._current_symbol}")
            # 기존 로드 메서드 호출하되, 로그로 구분 표시
            self._logger.info("🧪 [하이브리드 테스트] REST API로 데이터 교체 시도")
            self._load_symbol_data(self._current_symbol)

    def _websocket_backup_update(self) -> None:
        """WebSocket 백업용 REST 갱신 (WebSocket 연결 시에도 주기적 백업)"""
        if self._current_symbol and self._websocket_connected:
            self._logger.debug(f"🔄 WebSocket 백업 REST 갱신: {self._current_symbol}")
            self._load_symbol_data(self._current_symbol)

    def _start_websocket_backup_timer(self) -> None:
        """WebSocket 백업 타이머 시작 (15초 간격)"""
        if not self._websocket_backup_timer.isActive():
            self._websocket_backup_timer.start(15000)  # 15초마다 백업 갱신
            self._logger.info("🔄 WebSocket 백업 타이머 시작 (15초 간격)")

    def _stop_websocket_backup_timer(self) -> None:
        """WebSocket 백업 타이머 중지"""
        if self._websocket_backup_timer.isActive():
            self._websocket_backup_timer.stop()
            self._logger.info("🔄 WebSocket 백업 타이머 중지")

    def _check_websocket_status(self) -> None:
        """웹소켓 상태 체크 및 하이브리드 테스트 제어"""
        if not self._websocket_initialized or not self._websocket_service:
            # 웹소켓 미초기화시 상태 표시
            if self._websocket_status_label:
                self._websocket_status_label.setText("🔴 WebSocket 미연결 (초기화 중)")

        elif self._websocket_connected:
            # 웹소켓 정상 연결 상태
            if self._websocket_status_label:
                if self._test_mode == "hybrid" and self._hybrid_rest_enabled:
                    self._websocket_status_label.setText("🟢 WebSocket 연결됨 + REST 하이브리드")
                else:
                    self._websocket_status_label.setText("� WebSocket 연결됨 (실시간)")

        else:
            # 웹소켓 연결 시도 중
            if self._websocket_status_label:
                self._websocket_status_label.setText("🟡 WebSocket 연결 시도 중...")

    def enable_hybrid_test(self, enable: bool = True):
        """하이브리드 테스트 모드 활성화/비활성화"""
        self._test_mode = "hybrid" if enable else "websocket"
        self._hybrid_rest_enabled = enable

        if enable:
            # 2단계 테스트: WebSocket + REST 하이브리드
            self._hybrid_rest_timer.start(3000)  # 3초마다 REST 보조 갱신
            self._logger.info("🧪 하이브리드 테스트 모드 활성화: WebSocket + REST")
        else:
            # 1단계 테스트: WebSocket만
            self._hybrid_rest_timer.stop()
            self._logger.info("🎯 WebSocket 전용 모드 활성화")

        # 하이브리드 테스트 컨트롤 메서드
        self.enable_hybrid_test(False)  # 기본: WebSocket 전용

    def test_hybrid_mode(self):
        """하이브리드 모드 테스트 시작 (개발용)"""
        self._logger.info("🧪 하이브리드 테스트 시작: 1단계(WebSocket) → 2단계(WebSocket+REST)")

        # 1단계: WebSocket 전용 (5초간)
        self.enable_hybrid_test(False)
        QTimer.singleShot(5000, lambda: self._start_phase2_test())

    def _start_phase2_test(self):
        """2단계 테스트: WebSocket + REST 하이브리드"""
        self._logger.info("🧪 2단계 시작: WebSocket + REST 하이브리드 충돌 테스트")
        self.enable_hybrid_test(True)

        # 10초 후 테스트 종료
        QTimer.singleShot(10000, lambda: self._end_hybrid_test())

    def _end_hybrid_test(self):
        """하이브리드 테스트 종료"""
        self.enable_hybrid_test(False)
        self._logger.info("🧪 하이브리드 테스트 완료: WebSocket 전용 모드로 복귀")

    def _setup_center_position(self) -> None:
        """호가창 중앙 포지션 설정 (30-31행이 보이도록) - 코인 변경시에만"""
        if not self._orderbook_table or not self._should_center_on_next_update:
            return

        try:
            # 30-31행 (매도/매수 경계) 중앙에 배치
            center_row = 29  # 30행 (0-based index)
            self._orderbook_table.scrollToItem(
                self._orderbook_table.item(center_row, 0),
                QTableWidget.ScrollHint.PositionAtCenter
            )
            self._should_center_on_next_update = False  # 중앙 정렬 완료 후 비활성화
            self._logger.debug("📍 호가창 중앙 포지션 설정 완료")
        except Exception as e:
            self._logger.debug(f"중앙 포지션 설정 건너뜀: {e}")
