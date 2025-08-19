"""
코인 리스트 위젯 - 간소화 버전

차트뷰어의 좌측 패널에 표시되는 코인 리스트입니다.
마켓 선택, 검색 필터 기능을 제공합니다.
"""

from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.chart_viewer.coin_list_service import CoinListService, CoinInfo


class CoinListWidget(QWidget):
    """
    코인 리스트 위젯 - 간소화 버전

    구성:
    - 마켓 콤보박스 (KRW/BTC/USDT)
    - 검색 필터 + 초기화 버튼
    - 코인 리스트
    """

    # 시그널 정의
    coin_selected = pyqtSignal(str)  # 코인 선택 시그널
    market_changed = pyqtSignal(str)  # 마켓 변경 시그널

    def __init__(self, parent: Optional[QWidget] = None):
        """코인 리스트 위젯 초기화"""
        super().__init__(parent)

        self._logger = create_component_logger("CoinListWidget")

        # 상태 관리
        self._current_market = "KRW"
        self._search_filter = ""
        self._coin_data: List[CoinInfo] = []

        # 서비스
        self._coin_service = CoinListService()

        # UI 컴포넌트
        self._market_combo: Optional[QComboBox] = None
        self._search_input: Optional[QLineEdit] = None
        self._clear_button: Optional[QPushButton] = None
        self._coin_list: Optional[QListWidget] = None

        # UI 초기화
        self._setup_ui()
        self._load_initial_data()

        self._logger.info("📋 코인 리스트 위젯 초기화 완료")

    def _setup_ui(self) -> None:
        """UI 구성 - 매우 단순한 구조"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 1. 마켓 선택 콤보박스
        market_layout = QHBoxLayout()
        market_label = QLabel("마켓:")
        market_label.setFixedWidth(40)

        self._market_combo = QComboBox()
        self._market_combo.addItems(["KRW", "BTC", "USDT"])
        self._market_combo.setCurrentText("KRW")
        self._market_combo.currentTextChanged.connect(self._on_market_changed)

        market_layout.addWidget(market_label)
        market_layout.addWidget(self._market_combo)
        market_layout.addStretch()
        layout.addLayout(market_layout)

        # 2. 검색 필터
        search_layout = QHBoxLayout()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("코인 검색...")
        self._search_input.textChanged.connect(self._on_search_changed)

        self._clear_button = QPushButton("초기화")
        self._clear_button.setFixedWidth(60)
        self._clear_button.clicked.connect(self._clear_search)

        search_layout.addWidget(self._search_input)
        search_layout.addWidget(self._clear_button)
        layout.addLayout(search_layout)

        # 3. 코인 리스트
        self._coin_list = QListWidget()
        self._coin_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._coin_list)

        self._logger.debug("UI 구성 완료")

    def _load_initial_data(self) -> None:
        """초기 데이터 로드 - 매우 단순"""
        # 즉시 샘플 데이터 표시
        self._load_sample_data()

        # 1초 후 실제 데이터 로드
        QTimer.singleShot(1000, self._load_real_data)

    def _load_sample_data(self) -> None:
        """샘플 데이터 즉시 표시"""
        from upbit_auto_trading.application.chart_viewer.coin_list_service import CoinInfo

        sample_data = [
            CoinInfo("KRW-BTC", "비트코인", "KRW", "45000000", "45,000,000", "+2.5%", "+1,000,000", "1.2B", 120000000.0, False),
            CoinInfo("KRW-ETH", "이더리움", "KRW", "3200000", "3,200,000", "+1.8%", "+56,000", "800M", 80000000.0, False),
            CoinInfo("KRW-ADA", "에이다", "KRW", "650", "650", "-0.5%", "-3", "500M", 50000000.0, False),
        ]

        self._coin_data = sample_data
        self._update_ui_simple()
        self._logger.info("✅ 샘플 데이터 표시 완료")

    def _load_real_data(self) -> None:
        """실제 데이터 로드"""
        import asyncio
        import threading

        def load_data():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                coins = loop.run_until_complete(
                    self._coin_service.get_coins_by_market(self._current_market, self._search_filter)
                )

                if coins:
                    self._coin_data = coins
                    # 메인 스레드에서 UI 업데이트
                    QTimer.singleShot(0, self._update_ui_simple)
                    self._logger.info(f"✅ {self._current_market} 마켓 데이터 로드 완료: {len(coins)}개")

            except Exception as e:
                self._logger.error(f"❌ 데이터 로드 실패: {e}")
            finally:
                # loop 변수가 존재하지 않을 수 있으므로 제거
                pass

        thread = threading.Thread(target=load_data, daemon=True)
        thread.start()

    def _update_ui_simple(self) -> None:
        """UI 업데이트 - 매우 단순"""
        if not self._coin_list:
            return

        # 기존 항목 클리어
        self._coin_list.clear()

        # 필터링된 데이터 추가
        filtered_data = self._filter_coins()

        # 한 번에 모든 항목 추가 (개별 로깅 없음)
        for coin in filtered_data:
            item_text = f"{coin.symbol} - {coin.name}"
            if coin.price_formatted:
                item_text += f" | {coin.price_formatted}"
            if coin.change_rate and coin.change_rate != "0.00%":
                item_text += f" ({coin.change_rate})"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, coin.symbol)
            self._coin_list.addItem(item)

        # 단일 로그로 완료 보고
        self._logger.info(f"✅ {self._current_market} 마켓 UI 업데이트 완료: {len(filtered_data)}개")

    def _filter_coins(self) -> List[CoinInfo]:
        """코인 필터링"""
        if not self._search_filter:
            return self._coin_data

        filtered = []
        search_lower = self._search_filter.lower()

        for coin in self._coin_data:
            if (search_lower in coin.symbol.lower() or
                    search_lower in coin.name.lower()):
                filtered.append(coin)

        return filtered

    def _on_market_changed(self, market: str) -> None:
        """마켓 변경 처리"""
        if market == self._current_market:
            return

        self._current_market = market
        self._logger.info(f"📊 마켓 변경: {market}")

        # 즉시 빈 리스트 표시
        if self._coin_list:
            self._coin_list.clear()

        # 새 데이터 로드
        self._load_real_data()

        # 시그널 발송
        self.market_changed.emit(market)

    def _on_search_changed(self, text: str) -> None:
        """검색 필터 변경 처리"""
        self._search_filter = text.lower()
        # 즉시 필터링 적용 (네트워크 요청 없음)
        self._update_ui_simple()

    def _clear_search(self) -> None:
        """검색 필터 초기화"""
        if self._search_input:
            self._search_input.clear()
        self._search_filter = ""
        self._update_ui_simple()

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """코인 항목 클릭 처리"""
        symbol = item.data(Qt.ItemDataRole.UserRole)
        if symbol:
            self.coin_selected.emit(symbol)
            self._logger.info(f"💰 코인 선택: {symbol}")

    def get_current_market(self) -> str:
        """현재 선택된 마켓 반환"""
        return self._current_market

    def refresh_data(self) -> None:
        """데이터 새로고침"""
        self._logger.info("🔄 데이터 새로고침")
        self._load_real_data()

    def get_widget_info(self) -> Dict[str, Any]:
        """위젯 정보 반환"""
        return {
            "current_market": self._current_market,
            "search_filter": self._search_filter,
            "total_coins": len(self._coin_data),
            "visible_coins": self._coin_list.count() if self._coin_list else 0
        }
