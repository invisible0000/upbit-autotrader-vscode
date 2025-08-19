"""
코인 리스트 위젯 - 완전 재설계 버전

문제점:
1. _coin_list가 None이 되는 이슈
2. UI 중복 생성 문제
3. 재생성 로직의 복잡성

해결책:
1. 지연 초기화 (Lazy Initialization) 패턴
2. 프로퍼티 기반 안전한 접근
3. 단순하고 명확한 구조
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.chart_viewer.coin_list_service import CoinListService, CoinInfo


class CoinListWidget(QWidget):
    """코인 리스트 위젯 - 완전 재설계 버전"""

    # 시그널
    coin_selected = pyqtSignal(str)
    favorite_toggled = pyqtSignal(str, bool)
    market_changed = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._logger = create_component_logger("CoinListWidget")

        # 상태 변수
        self._current_market = "KRW"
        self._search_filter = ""
        self._coin_data: List[CoinInfo] = []
        self._is_initialized = False

        # UI 컴포넌트 - None으로 시작
        self._market_combo: Optional[QComboBox] = None
        self._search_input: Optional[QLineEdit] = None
        self._clear_button: Optional[QPushButton] = None
        self._list_widget: Optional[QListWidget] = None  # 이름 변경으로 충돌 방지

        # 서비스
        self._coin_service = CoinListService()

        # 즉시 초기화
        self._ensure_initialization()

        # 데이터 로드
        self._schedule_data_loading()

        self._logger.info("✅ 코인 리스트 위젯 초기화 완료")

    def _ensure_initialization(self) -> None:
        """확실한 초기화 보장"""
        if self._is_initialized:
            return

        try:
            self._create_ui_components()
            self._setup_layout()
            self._connect_signals()
            self._is_initialized = True
            self._logger.info("✅ UI 초기화 완료")
        except Exception as e:
            self._logger.error(f"❌ UI 초기화 실패: {e}")
            raise

    def _create_ui_components(self) -> None:
        """UI 컴포넌트 생성"""
        # 마켓 콤보박스
        self._market_combo = QComboBox()
        self._market_combo.addItems(["KRW", "BTC", "USDT"])
        self._market_combo.setCurrentText("KRW")

        # 검색 입력
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("코인 검색...")

        # 초기화 버튼
        self._clear_button = QPushButton("초기화")
        self._clear_button.setFixedWidth(60)

        # 리스트 위젯 - 가장 중요!
        self._list_widget = QListWidget()

        # 생성 즉시 검증
        if not self._list_widget:
            raise RuntimeError("리스트 위젯 생성 실패")

        self._logger.debug(f"✅ 리스트 위젯 생성 완료: {id(self._list_widget)}")

    def _setup_layout(self) -> None:
        """레이아웃 설정"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # 마켓 선택 영역
        market_layout = QHBoxLayout()
        market_label = QLabel("마켓:")
        market_label.setFixedWidth(40)
        market_layout.addWidget(market_label)
        market_layout.addWidget(self._market_combo)
        market_layout.addStretch()

        # 검색 영역
        search_layout = QHBoxLayout()
        search_layout.addWidget(self._search_input)
        search_layout.addWidget(self._clear_button)

        # 메인 레이아웃 조립
        main_layout.addLayout(market_layout)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self._list_widget)

        self._logger.debug("✅ 레이아웃 설정 완료")

    def _connect_signals(self) -> None:
        """시그널 연결"""
        if self._market_combo:
            self._market_combo.currentTextChanged.connect(self._on_market_changed)

        if self._search_input:
            self._search_input.textChanged.connect(self._on_search_changed)

        if self._clear_button:
            self._clear_button.clicked.connect(self._clear_search)

        if self._list_widget:
            self._list_widget.itemClicked.connect(self._on_item_clicked)

        self._logger.debug("✅ 시그널 연결 완료")

    @property
    def coin_list(self) -> QListWidget:
        """안전한 리스트 위젯 접근"""
        if not self._list_widget:
            self._logger.warning("⚠️ 리스트 위젯이 None임. 재초기화 시도...")
            self._ensure_initialization()

        if not self._list_widget:
            raise RuntimeError("리스트 위젯 초기화 실패")

        return self._list_widget

    def _schedule_data_loading(self) -> None:
        """데이터 로드 스케줄링"""
        # 즉시 샘플 데이터 표시
        self._load_sample_data()

        # 1초 후 실제 데이터 로드
        QTimer.singleShot(1000, self._load_real_data)

    def _load_sample_data(self) -> None:
        """샘플 데이터 로드"""
        sample_data = [
            CoinInfo("KRW-BTC", "비트코인", "KRW", "45000000", "45,000,000", "+2.5%", "+1,000,000", "1.2B", 120000000.0, False),
            CoinInfo("KRW-ETH", "이더리움", "KRW", "3200000", "3,200,000", "+1.8%", "+56,000", "800M", 80000000.0, False),
            CoinInfo("KRW-ADA", "에이다", "KRW", "650", "650", "-0.5%", "-3", "500M", 50000000.0, False),
        ]

        self._coin_data = sample_data
        self._update_ui()
        self._logger.info("✅ 샘플 데이터 로드 완료")

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
                    QTimer.singleShot(0, self._update_ui)
                    self._logger.info(f"✅ {self._current_market} 실제 데이터 로드 완료: {len(coins)}개")

            except Exception as e:
                self._logger.error(f"❌ 실제 데이터 로드 실패: {e}")

        thread = threading.Thread(target=load_data, daemon=True)
        thread.start()

    def _update_ui(self) -> None:
        """UI 업데이트"""
        try:
            # 안전한 리스트 위젯 접근
            list_widget = self.coin_list
            list_widget.clear()

            # 필터링된 데이터 가져오기
            filtered_data = self._filter_coins()

            # 아이템 추가
            for coin in filtered_data:
                item_text = f"{coin.symbol} - {coin.name}"
                if coin.price_formatted:
                    item_text += f" | {coin.price_formatted}"
                if coin.change_rate and coin.change_rate != "0.00%":
                    item_text += f" ({coin.change_rate})"

                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, coin.symbol)
                list_widget.addItem(item)

            self._logger.info(f"✅ UI 업데이트 완료: {len(filtered_data)}개 아이템")

        except Exception as e:
            self._logger.error(f"❌ UI 업데이트 실패: {e}")

    def _filter_coins(self) -> List[CoinInfo]:
        """코인 필터링"""
        if not self._search_filter:
            return self._coin_data

        search_lower = self._search_filter.lower()
        return [
            coin for coin in self._coin_data
            if (search_lower in coin.symbol.lower() or
                search_lower in coin.name.lower())
        ]

    def _on_market_changed(self, market: str) -> None:
        """마켓 변경 처리"""
        if market != self._current_market:
            self._current_market = market
            self.market_changed.emit(market)
            self._load_real_data()
            self._logger.info(f"📊 마켓 변경: {market}")

    def _on_search_changed(self, text: str) -> None:
        """검색 텍스트 변경 처리"""
        self._search_filter = text
        self._update_ui()

    def _clear_search(self) -> None:
        """검색 초기화"""
        if self._search_input:
            self._search_input.clear()
        self._search_filter = ""
        self._update_ui()

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """아이템 클릭 처리"""
        symbol = item.data(Qt.ItemDataRole.UserRole)
        if symbol:
            self.coin_selected.emit(symbol)
            self._logger.info(f"💰 코인 선택: {symbol}")

    def get_current_market(self) -> str:
        """현재 마켓 반환"""
        return self._current_market

    def refresh_data(self) -> None:
        """데이터 새로고침"""
        self._load_real_data()

    def get_selected_symbol(self) -> Optional[str]:
        """선택된 심볼 반환"""
        try:
            current_item = self.coin_list.currentItem()
            if current_item:
                return current_item.data(Qt.ItemDataRole.UserRole)
        except Exception:
            pass
        return None
