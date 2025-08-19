"""
호가창 위젯 - 리팩터링된 버전 (DDD 아키텍처 적용)

Presentation Layer의 순수 UI 컴포넌트입니다.
- MVP 패턴 적용 (Presenter 분리)
- UI 로직만 담당
- 비즈니스 로직은 Presenter에 위임
- QAsync 기반 안정적인 처리 (asyncio 문제 해결)
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.events.bus.in_memory_event_bus import InMemoryEventBus
from upbit_auto_trading.ui.desktop.screens.chart_view.presenters.orderbook_presenter import OrderbookPresenter
from upbit_auto_trading.infrastructure.formatters.orderbook_formatter import OrderbookFormatter


class OrderbookWidget(QWidget):
    """
    호가창 위젯 - DDD 아키텍처 적용

    주요 기능:
    - 실시간 호가창 표시
    - WebSocket + REST 하이브리드
    - MVP 패턴 (Presenter 분리)
    - 폰트 크기 12pt 통일
    """

    # 시그널 정의 (호환성 유지)
    price_clicked = pyqtSignal(str, float)
    orderbook_updated = pyqtSignal(dict)
    market_impact_analyzed = pyqtSignal(dict)
    optimal_price_suggested = pyqtSignal(str, float, str)

    def __init__(self, parent: Optional[QWidget] = None, event_bus: Optional[InMemoryEventBus] = None):
        """위젯 초기화"""
        super().__init__(parent)

        self._logger = create_component_logger("OrderbookWidget")
        self._event_bus = event_bus

        # 컴포넌트 초기화
        self._presenter = OrderbookPresenter(event_bus)
        self._formatter = OrderbookFormatter()

        # UI 상태
        self._should_center_on_next_update = True
        self._colors = self._setup_colors()

        # 자동 갱신 타이머 (WebSocket 시뮬레이션을 위한 빠른 갱신)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._auto_refresh_data)
        self._refresh_timer.setInterval(500)  # 0.5초마다 갱신 (WebSocket 속도 시뮬레이션)
        self._refresh_timer.start()

        # UI 위젯
        self._orderbook_table: Optional[QTableWidget] = None
        self._websocket_status_label: Optional[QLabel] = None
        self._spread_label: Optional[QLabel] = None
        self._price_info_label: Optional[QLabel] = None
        self._market_info_label: Optional[QLabel] = None
        self._order_info_label: Optional[QLabel] = None

        # UI 구성
        self._setup_ui()
        self._connect_presenter_signals()

        # 초기 데이터 로드
        self._presenter.refresh_data()

        self._logger.info("💰 호가창 위젯 초기화 완료 (DDD 리팩터링 버전)")

    def _setup_colors(self) -> Dict[str, QColor]:
        """색상 설정"""
        return {
            "ask": QColor("#FF4444"),    # 매도 (빨강)
            "bid": QColor("#4444FF"),    # 매수 (파랑)
            "neutral": QColor("#666666")  # 중립
        }

    def _setup_ui(self) -> None:
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        # WebSocket 상태 표시 (12pt)
        self._websocket_status_label = QLabel("🟡 연결 중...")
        self._websocket_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._websocket_status_label.setStyleSheet("color: #888; font-size: 12pt; font-weight: bold;")
        layout.addWidget(self._websocket_status_label)

        # 스프레드 정보 (12pt)
        self._spread_label = QLabel("스프레드: - ")
        self._spread_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._spread_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        layout.addWidget(self._spread_label)

        # 매수/매도 호가 정보 (12pt)
        self._price_info_label = QLabel("매수: - | 매도: -")
        self._price_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._price_info_label.setStyleSheet("color: #666; font-size: 12pt; font-weight: normal;")
        layout.addWidget(self._price_info_label)

        # 시장 정보 (12pt)
        self._market_info_label = QLabel("거래량: - | 유동성: -")
        self._market_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._market_info_label.setStyleSheet("color: #888; font-size: 12pt; font-weight: normal;")
        layout.addWidget(self._market_info_label)

        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # 호가 테이블
        self._orderbook_table = QTableWidget()
        self._setup_table()
        layout.addWidget(self._orderbook_table)

        # 주문 정보 라벨 (호가창 아래 거래 정보)
        self._order_info_label = QLabel("주문가: - | 예상 수수료: -<br>최소 수량: - | 호가 번호: -")
        self._order_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._order_info_label.setStyleSheet("""
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 3px;
            padding: 8px;
            font-size: 11pt;
            font-weight: bold;
            color: #333;
        """)
        layout.addWidget(self._order_info_label)        # 범례 (12pt)
        legend_layout = QHBoxLayout()
        ask_legend = QLabel("■ 매도")
        ask_legend.setStyleSheet(f"color: {self._colors['ask'].name()}; font-size: 12pt;")
        bid_legend = QLabel("■ 매수")
        bid_legend.setStyleSheet(f"color: {self._colors['bid'].name()}; font-size: 12pt;")
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
        self._orderbook_table.setColumnCount(4)
        self._orderbook_table.setRowCount(60)  # 30행씩 매도/매수
        self._orderbook_table.setHorizontalHeaderLabels(["번호", "수량", "가격", "누적"])

        # 헤더 설정 - None 체크 추가
        header = self._orderbook_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # 번호
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 수량
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # 가격
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # 누적
            header.resizeSection(0, 40)

        # 테이블 속성 설정
        self._orderbook_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._orderbook_table.setAlternatingRowColors(True)

        # 수직 헤더 숨기기 - None 체크 추가
        vertical_header = self._orderbook_table.verticalHeader()
        if vertical_header:
            vertical_header.hide()

        # 클릭 이벤트 연결
        self._orderbook_table.cellClicked.connect(self._on_cell_clicked)

        # 폰트 설정 (12pt)
        font = QFont()
        font.setPointSize(12)
        self._orderbook_table.setFont(font)

    def _connect_presenter_signals(self) -> None:
        """Presenter 시그널 연결"""
        self._presenter.data_updated.connect(self._update_orderbook_display)
        self._presenter.status_changed.connect(self._update_status_display)
        self._presenter.error_occurred.connect(self._handle_error)

    def _update_orderbook_display(self, data: Dict[str, Any]) -> None:
        """호가창 표시 업데이트"""
        if not self._formatter.validate_orderbook_data(data):
            self._logger.warning("유효하지 않은 호가창 데이터")
            return

        try:
            # 테이블 데이터 생성
            table_data = self._formatter.format_orderbook_for_table(data)
            self._populate_table(table_data, data)

            # 정보 라벨 업데이트
            self._update_info_labels(data)

            # 중앙 정렬 (코인 변경시에만)
            if self._should_center_on_next_update:
                QTimer.singleShot(100, self._setup_center_position)

            # 시그널 발생 (호환성)
            self.orderbook_updated.emit(data)

        except Exception as e:
            self._logger.error(f"호가창 표시 업데이트 오류: {e}")

    def _populate_table(self, table_data: list, original_data: Dict[str, Any]) -> None:
        """테이블 데이터 채우기 - 시각적 개선 포함"""
        if not self._orderbook_table or not table_data:
            return

        # 전체 수량 계산 (배경 그라데이션용)
        asks = original_data.get("asks", [])
        bids = original_data.get("bids", [])

        max_ask_quantity = max((ask.get("quantity", 0) for ask in asks), default=1)
        max_bid_quantity = max((bid.get("quantity", 0) for bid in bids), default=1)
        max_quantity = max(max_ask_quantity, max_bid_quantity)

        for row_idx, row_data in enumerate(table_data):
            if row_idx >= 60:  # 안전 체크
                break

            row_type = self._formatter.get_table_row_type(row_idx)
            is_ask = row_type == "ask"

            # 기본 색상 설정
            base_color = self._colors["ask"] if is_ask else self._colors["bid"]

            # 수량 데이터에서 배경 강도 계산
            try:
                quantity_text = str(row_data[1]).replace(",", "")

                # K, M 접미사 처리
                if quantity_text.endswith("K"):
                    quantity = float(quantity_text[:-1]) * 1000
                elif quantity_text.endswith("M"):
                    quantity = float(quantity_text[:-1]) * 1000000
                elif quantity_text == "-":
                    quantity = 0
                else:
                    quantity = float(quantity_text)

                # 정규화된 강도 (0.05 ~ 0.6)
                intensity = 0.05 + (quantity / max_quantity) * 0.55 if max_quantity > 0 else 0.05

            except (ValueError, IndexError, TypeError):
                intensity = 0.05            # 배경색 계산 (알파값 조정)
            background_color = QColor(base_color)
            background_color.setAlphaF(intensity)

            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # 컬럼별 스타일링
                if col_idx == 0:  # 번호 컬럼
                    item.setForeground(QColor("#888"))
                elif col_idx == 1:  # 수량 컬럼
                    item.setBackground(background_color)  # 수량 기반 배경
                    item.setForeground(QColor("#333"))
                elif col_idx == 2:  # 가격 컬럼 (중요)
                    item.setForeground(base_color)
                    item.setBackground(QColor(background_color.red(), background_color.green(), background_color.blue(), 50))
                    # 굵은 폰트
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                elif col_idx == 3:  # 누적 컬럼
                    item.setBackground(QColor(background_color.red(), background_color.green(), background_color.blue(), 30))
                    item.setForeground(QColor("#666"))

                self._orderbook_table.setItem(row_idx, col_idx, item)

    def _update_info_labels(self, data: Dict[str, Any]) -> None:
        """정보 라벨 업데이트"""
        if not data:
            return

        market = data.get("market", "KRW")
        spread_info = self._formatter.calculate_spread_info(data)

        # 스프레드 정보
        if self._spread_label:
            spread_text = self._formatter.format_spread_text(spread_info, market)
            self._spread_label.setText(spread_text)

        # 가격 정보
        if self._price_info_label:
            price_text = self._formatter.format_price_info_text(spread_info, market)
            self._price_info_label.setText(price_text)

        # 시장 정보
        if self._market_info_label:
            market_text = self._formatter.format_market_info_text(data)
            self._market_info_label.setText(market_text)

    def _update_status_display(self, status: Dict[str, Any]) -> None:
        """상태 표시 업데이트"""
        if not self._websocket_status_label:
            return

        websocket_connected = status.get("websocket_connected", False)
        websocket_initialized = status.get("websocket_initialized", False)

        if websocket_connected:
            self._websocket_status_label.setText("🟢 WebSocket 연결됨 (0.5초 갱신)")
            self._websocket_status_label.setStyleSheet("color: #22AA22; font-size: 12pt; font-weight: bold;")
        elif websocket_initialized:
            self._websocket_status_label.setText("🟡 WebSocket 연결 시도 중...")
            self._websocket_status_label.setStyleSheet("color: #AAAA22; font-size: 12pt; font-weight: bold;")
        else:
            self._websocket_status_label.setText("🔴 REST 모드 (0.5초 갱신)")
            self._websocket_status_label.setStyleSheet("color: #AA2222; font-size: 12pt; font-weight: bold;")

    def _handle_error(self, error_message: str) -> None:
        """오류 처리"""
        self._logger.error(f"Presenter 오류: {error_message}")

        if self._websocket_status_label:
            self._websocket_status_label.setText("🔴 오류 발생")

    def _on_cell_clicked(self, row: int, column: int) -> None:
        """셀 클릭 이벤트 처리"""
        if column == 2 and self._orderbook_table:  # 가격 컬럼
            item = self._orderbook_table.item(row, column)
            if item:
                try:
                    price_text = item.text().replace(",", "")
                    price = float(price_text)
                    symbol = self._presenter.get_current_symbol()

                    # 매도/매수 구분 (30행 이하는 매도, 30행 이상은 매수)
                    order_type = "매도" if row < 30 else "매수"

                    # 주문 정보 계산 및 업데이트
                    self._update_order_info(symbol, price, order_type, row)

                    self.price_clicked.emit(symbol, price)
                    self._logger.debug(f"가격 클릭: {symbol} {price}")
                except (ValueError, TypeError):
                    pass

    def _update_order_info(self, symbol: str, price: float, order_type: str, row: int) -> None:
        """주문 정보 업데이트"""
        if not self._order_info_label:
            return

        try:
            # 기본 거래 정보 계산
            fee_rate = 0.0005  # 0.05% 수수료
            min_order_amount = 5000  # 최소 주문 금액 5,000원

            # 1개 단위 주문 시 예상 금액 계산
            quantity = 1.0
            total_amount = price * quantity
            fee_amount = total_amount * fee_rate

            # 최소 주문 수량 계산 (5,000원 이상)
            min_quantity = max(1.0, min_order_amount / price)

            # 호가 번호 계산 (1-30)
            if row < 30:  # 매도
                orderbook_number = 30 - row
            else:  # 매수
                orderbook_number = row - 29

            # 색상 설정
            color = "#FF4444" if order_type == "매도" else "#4444FF"

            # 정보 텍스트 구성 (2줄로 표시)
            info_text = (
                f"<span style='color: {color}; font-weight: bold;'>{order_type} {orderbook_number}번</span> | "
                f"주문가: {price:,.0f}원 | "
                f"예상 수수료: {fee_amount:.0f}원<br>"
                f"최소 수량: {min_quantity:.4f}개 | "
                f"1개 거래시: {total_amount:,.0f}원"
            )

            self._order_info_label.setText(info_text)

        except Exception as e:
            self._logger.debug(f"주문 정보 업데이트 실패: {e}")
            self._order_info_label.setText("주문가: - | 예상 수수료: -<br>최소 수량: - | 호가 번호: -")

    def _setup_center_position(self) -> None:
        """중앙 포지션 설정 (매도 1행과 매수 1행 경계)"""
        if not self._orderbook_table or not self._should_center_on_next_update:
            return

        try:
            # 매도 마지막(1번)과 매수 첫번째(1번) 사이로 중앙 정렬
            center_row = 29  # 30행 (0-based index 29) - 매도 마지막
            self._orderbook_table.scrollToItem(
                self._orderbook_table.item(center_row, 0),
                QTableWidget.ScrollHint.PositionAtCenter
            )
            self._should_center_on_next_update = False
            self._logger.debug("📍 호가창 중앙 포지션 설정 완료 (매도1번/매수1번 경계)")
        except Exception as e:
            self._logger.debug(f"중앙 포지션 설정 건너뜀: {e}")

    # 공개 인터페이스 (호환성 유지)
    def set_symbol(self, symbol: str) -> None:
        """심볼 설정 - QTimer 기반으로 안전하게"""
        self._should_center_on_next_update = True  # 심볼 변경시 중앙 정렬

        # QTimer를 사용하여 안전하게 심볼 변경 (asyncio 사용하지 않음)
        QTimer.singleShot(50, lambda: self._change_symbol_safe(symbol))

    def _change_symbol_safe(self, symbol: str) -> None:
        """안전한 심볼 변경 (QAsync 기반 동기 래퍼 사용)"""
        try:
            # QAsync 기반 동기 래퍼 사용
            success = self._presenter.change_symbol_sync(symbol)
            if success:
                self._logger.info(f"✅ 심볼 변경 완료: {symbol}")
            else:
                self._logger.warning(f"⚠️ 심볼 변경 실패: {symbol}")
        except Exception as e:
            self._logger.error(f"❌ 심볼 변경 오류: {symbol} - {e}")

    def get_current_symbol(self) -> str:
        """현재 심볼 반환"""
        return self._presenter.get_current_symbol()

    def refresh_data(self) -> None:
        """데이터 수동 갱신"""
        self._presenter.refresh_data()

    def _auto_refresh_data(self) -> None:
        """자동 갱신 (타이머 기반)"""
        if hasattr(self, '_presenter') and self._presenter:
            self._presenter.refresh_data()
            # 상태도 함께 업데이트
            status = self._presenter.get_connection_status()
            self._update_status_display(status)

    def get_debug_info(self) -> Dict[str, Any]:
        """디버그 정보 반환"""
        status = self._presenter.get_connection_status()
        status.update({
            "widget_initialized": True,
            "table_rows": self._orderbook_table.rowCount() if self._orderbook_table else 0
        })
        return status

    def cleanup(self) -> None:
        """리소스 정리"""
        # 타이머 중지
        if hasattr(self, '_refresh_timer') and self._refresh_timer:
            self._refresh_timer.stop()

        if self._presenter:
            self._presenter.cleanup()
        self._logger.info("OrderbookWidget 리소스 정리 완료")
