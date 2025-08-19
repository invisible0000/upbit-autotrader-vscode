"""
호가창 위젯

차트뷰어의 우측 패널에 표시되는 실시간 호가창입니다.
매수/매도 호가 구분 표시 및 호가량 시각화를 제공합니다.
"""

from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from upbit_auto_trading.infrastructure.logging import create_component_logger


class OrderbookWidget(QWidget):
    """
    호가창 위젯

    기능:
    - 실시간 매수/매도 호가 표시
    - 호가량에 따른 바차트 시각화
    - 가격 클릭 이벤트
    - 누적 수량 표시
    - 색상 구분 (매수/매도)
    """

    # 시그널 정의
    price_clicked = pyqtSignal(str, float)  # 가격 클릭 시그널 (타입, 가격)
    orderbook_updated = pyqtSignal(dict)  # 호가 업데이트 시그널

    def __init__(self, parent: Optional[QWidget] = None):
        """호가창 위젯 초기화"""
        super().__init__(parent)

        self._logger = create_component_logger("OrderbookWidget")

        # 상태 관리
        self._current_symbol = "KRW-BTC"
        self._orderbook_data: Dict[str, Any] = {}
        self._max_quantity = 0.0  # 시각화용 최대 수량

        # UI 컴포넌트
        self._orderbook_table: Optional[QTableWidget] = None
        self._spread_label: Optional[QLabel] = None

        # 색상 설정
        self._ask_color = QColor(255, 102, 102)  # 매도 (빨간색)
        self._bid_color = QColor(102, 153, 255)  # 매수 (파란색)
        self._neutral_color = QColor(240, 240, 240)  # 중립

        # UI 초기화
        self._setup_ui()
        self._load_sample_data()

        self._logger.info("💰 호가창 위젯 초기화 완료")

    def _setup_ui(self) -> None:
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 제목
        title = QLabel("💰 호가창")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # 스프레드 정보
        self._spread_label = QLabel("스프레드: - ")
        self._spread_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._spread_label)

        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # 호가 테이블
        self._orderbook_table = QTableWidget()
        self._setup_table()
        layout.addWidget(self._orderbook_table)

        # 범례
        legend_layout = QHBoxLayout()

        ask_legend = QLabel("■ 매도")
        ask_legend.setStyleSheet(f"color: {self._ask_color.name()};")

        bid_legend = QLabel("■ 매수")
        bid_legend.setStyleSheet(f"color: {self._bid_color.name()};")

        legend_layout.addWidget(ask_legend)
        legend_layout.addStretch()
        legend_layout.addWidget(bid_legend)
        layout.addLayout(legend_layout)

        self._logger.debug("UI 구성 완료")

    def _setup_table(self) -> None:
        """호가 테이블 설정"""
        if not self._orderbook_table:
            return

        # 테이블 기본 설정
        self._orderbook_table.setColumnCount(3)
        self._orderbook_table.setHorizontalHeaderLabels(["수량", "가격", "누적"])
        self._orderbook_table.setRowCount(20)  # 매도 10개 + 매수 10개

        # 헤더 설정
        header = self._orderbook_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        # 선택 모드 설정
        self._orderbook_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._orderbook_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # 클릭 이벤트 연결
        self._orderbook_table.cellClicked.connect(self._on_cell_clicked)

        self._logger.debug("호가 테이블 설정 완료")

    def _load_sample_data(self) -> None:
        """샘플 데이터 로드 (Phase 2 임시 데이터)"""
        self._orderbook_data = {
            "symbol": "KRW-BTC",
            "asks": [  # 매도 호가 (높은 가격부터)
                {"price": 45100000, "quantity": 0.125, "total": 0.125},
                {"price": 45090000, "quantity": 0.087, "total": 0.212},
                {"price": 45080000, "quantity": 0.156, "total": 0.368},
                {"price": 45070000, "quantity": 0.234, "total": 0.602},
                {"price": 45060000, "quantity": 0.189, "total": 0.791},
                {"price": 45050000, "quantity": 0.278, "total": 1.069},
                {"price": 45040000, "quantity": 0.145, "total": 1.214},
                {"price": 45030000, "quantity": 0.367, "total": 1.581},
                {"price": 45020000, "quantity": 0.198, "total": 1.779},
                {"price": 45010000, "quantity": 0.256, "total": 2.035},
            ],
            "bids": [  # 매수 호가 (높은 가격부터)
                {"price": 45000000, "quantity": 0.167, "total": 0.167},
                {"price": 44990000, "quantity": 0.234, "total": 0.401},
                {"price": 44980000, "quantity": 0.189, "total": 0.590},
                {"price": 44970000, "quantity": 0.298, "total": 0.888},
                {"price": 44960000, "quantity": 0.145, "total": 1.033},
                {"price": 44950000, "quantity": 0.356, "total": 1.389},
                {"price": 44940000, "quantity": 0.278, "total": 1.667},
                {"price": 44930000, "quantity": 0.123, "total": 1.790},
                {"price": 44920000, "quantity": 0.267, "total": 2.057},
                {"price": 44910000, "quantity": 0.198, "total": 2.255},
            ]
        }

        # 최대 수량 계산 (시각화용)
        all_quantities = []
        all_quantities.extend([item["quantity"] for item in self._orderbook_data["asks"]])
        all_quantities.extend([item["quantity"] for item in self._orderbook_data["bids"]])
        self._max_quantity = max(all_quantities) if all_quantities else 1.0

        # 테이블 업데이트
        self._update_orderbook_table()

        self._logger.debug("샘플 호가 데이터 로드 완료")

    def _update_orderbook_table(self) -> None:
        """호가 테이블 업데이트"""
        if not self._orderbook_table or not self._orderbook_data:
            return

        asks = self._orderbook_data.get("asks", [])
        bids = self._orderbook_data.get("bids", [])

        # 매도 호가 (상위 10개, 역순으로 표시)
        for i, ask in enumerate(reversed(asks[:10])):
            row = i
            self._set_orderbook_row(row, ask, "ask")

        # 매수 호가 (하위 10개)
        for i, bid in enumerate(bids[:10]):
            row = 10 + i
            self._set_orderbook_row(row, bid, "bid")

        # 스프레드 계산 및 표시
        if asks and bids:
            spread = asks[0]["price"] - bids[0]["price"]
            spread_rate = (spread / bids[0]["price"]) * 100
            if self._spread_label:
                self._spread_label.setText(f"스프레드: {spread:,.0f}원 ({spread_rate:.3f}%)")

        self._logger.debug("호가 테이블 업데이트 완료")

    def _set_orderbook_row(self, row: int, data: Dict[str, Any], order_type: str) -> None:
        """호가 행 설정"""
        if not self._orderbook_table:
            return

        price = data["price"]
        quantity = data["quantity"]
        total = data["total"]

        # 수량 (바차트 효과)
        quantity_item = QTableWidgetItem(f"{quantity:.3f}")
        quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # 가격
        price_item = QTableWidgetItem(f"{price:,.0f}")
        price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        price_item.setData(Qt.ItemDataRole.UserRole, {"price": price, "type": order_type})

        # 누적 수량
        total_item = QTableWidgetItem(f"{total:.3f}")
        total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # 색상 설정
        if order_type == "ask":
            color = self._ask_color
        else:
            color = self._bid_color

        # 수량에 따른 배경색 강도 조절
        intensity = min(quantity / self._max_quantity, 1.0)
        bg_color = QColor(color)
        bg_color.setAlpha(int(50 + 100 * intensity))  # 50-150 알파값

        quantity_item.setBackground(bg_color)
        price_item.setBackground(QColor(color.red(), color.green(), color.blue(), 30))
        total_item.setBackground(QColor(color.red(), color.green(), color.blue(), 20))

        # 테이블에 설정
        self._orderbook_table.setItem(row, 0, quantity_item)
        self._orderbook_table.setItem(row, 1, price_item)
        self._orderbook_table.setItem(row, 2, total_item)

    def _on_cell_clicked(self, row: int, column: int) -> None:
        """셀 클릭 처리"""
        if not self._orderbook_table:
            return

        # 가격 열 클릭시 이벤트 발송
        if column == 1:  # 가격 열
            price_item = self._orderbook_table.item(row, column)
            if price_item:
                data = price_item.data(Qt.ItemDataRole.UserRole)
                if data:
                    price = data["price"]
                    order_type = data["type"]
                    self.price_clicked.emit(order_type, price)
                    self._logger.debug(f"가격 클릭: {order_type} {price:,.0f}원")

    def update_orderbook(self, orderbook_data: Dict[str, Any]) -> None:
        """호가 데이터 업데이트 (실시간 연동용)"""
        self._orderbook_data = orderbook_data

        # 최대 수량 재계산
        all_quantities = []
        asks = orderbook_data.get("asks", [])
        bids = orderbook_data.get("bids", [])

        all_quantities.extend([item["quantity"] for item in asks])
        all_quantities.extend([item["quantity"] for item in bids])
        self._max_quantity = max(all_quantities) if all_quantities else 1.0

        # 테이블 업데이트
        self._update_orderbook_table()

        # 시그널 발송
        self.orderbook_updated.emit(orderbook_data)

        self._logger.debug(f"호가 데이터 업데이트: {orderbook_data.get('symbol', 'Unknown')}")

    def set_symbol(self, symbol: str) -> None:
        """심벌 설정"""
        self._current_symbol = symbol
        self._logger.debug(f"호가창 심벌 변경: {symbol}")
        # TODO: Phase 4에서 실제 호가 데이터 구독 로직 추가

    def get_current_symbol(self) -> str:
        """현재 심벌 반환"""
        return self._current_symbol

    def get_spread_info(self) -> Dict[str, Any]:
        """스프레드 정보 반환"""
        if not self._orderbook_data:
            return {}

        asks = self._orderbook_data.get("asks", [])
        bids = self._orderbook_data.get("bids", [])

        if not asks or not bids:
            return {}

        best_ask = asks[0]["price"]
        best_bid = bids[0]["price"]
        spread = best_ask - best_bid
        spread_rate = (spread / best_bid) * 100

        return {
            "best_ask": best_ask,
            "best_bid": best_bid,
            "spread": spread,
            "spread_rate": spread_rate
        }

    def get_widget_info(self) -> Dict[str, Any]:
        """위젯 정보 반환"""
        spread_info = self.get_spread_info()

        return {
            "current_symbol": self._current_symbol,
            "has_data": bool(self._orderbook_data),
            "ask_levels": len(self._orderbook_data.get("asks", [])),
            "bid_levels": len(self._orderbook_data.get("bids", [])),
            "spread_info": spread_info
        }
