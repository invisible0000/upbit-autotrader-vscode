"""
최소 의존성 코인 리스트 위젯
백본 시스템 의존성을 최소화하여 위젯 생성 문제 해결
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer


class MinimalCoinInfo:
    """최소한의 코인 정보 클래스"""
    def __init__(self, symbol: str, name: str, price: str = "", change: str = ""):
        self.symbol = symbol
        self.name = name
        self.price = price
        self.change = change


class MinimalCoinListWidget(QWidget):
    """최소 의존성 코인 리스트 위젯"""

    # 시그널
    coin_selected = pyqtSignal(str)
    favorite_toggled = pyqtSignal(str, bool)
    market_changed = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # 백본 시스템 의존성 제거 - 로깅 시스템 사용 안함
        print("MinimalCoinListWidget 초기화 시작")

        # 상태 변수
        self._current_market = "KRW"
        self._search_filter = ""
        self._coin_data: List[MinimalCoinInfo] = []

        # UI 컴포넌트
        self._market_combo: Optional[QComboBox] = None
        self._search_input: Optional[QLineEdit] = None
        self._clear_button: Optional[QPushButton] = None
        self._list_widget: Optional[QListWidget] = None

        # UI 초기화
        self._setup_ui()

        # 샘플 데이터 로드
        self._load_sample_data()

        print("MinimalCoinListWidget 초기화 완료")

    def _setup_ui(self) -> None:
        """UI 설정"""
        print("UI 설정 시작")

        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # 마켓 선택
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

        # 검색 영역
        search_layout = QHBoxLayout()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("코인 검색...")
        self._search_input.textChanged.connect(self._on_search_changed)

        self._clear_button = QPushButton("초기화")
        self._clear_button.setFixedWidth(60)
        self._clear_button.clicked.connect(self._clear_search)

        search_layout.addWidget(self._search_input)
        search_layout.addWidget(self._clear_button)

        # 리스트 위젯 - 핵심!
        print("리스트 위젯 생성 시작")
        self._list_widget = QListWidget()
        print(f"리스트 위젯 생성 완료: {id(self._list_widget)}")

        if not self._list_widget:
            print("❌ 리스트 위젯이 None입니다!")
            raise RuntimeError("리스트 위젯 생성 실패")

        self._list_widget.itemClicked.connect(self._on_item_clicked)

        # 레이아웃 조립
        main_layout.addLayout(market_layout)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self._list_widget)

        print("UI 설정 완료")

    def _load_sample_data(self) -> None:
        """샘플 데이터 로드"""
        print("샘플 데이터 로드 시작")

        self._coin_data = [
            MinimalCoinInfo("KRW-BTC", "비트코인", "45,000,000", "+2.5%"),
            MinimalCoinInfo("KRW-ETH", "이더리움", "3,200,000", "+1.8%"),
            MinimalCoinInfo("KRW-ADA", "에이다", "650", "-0.5%"),
            MinimalCoinInfo("KRW-XRP", "리플", "1,200", "+0.8%"),
            MinimalCoinInfo("KRW-DOT", "폴카닷", "12,000", "+3.2%"),
        ]

        self._update_ui()
        print("샘플 데이터 로드 완료")

    def _update_ui(self) -> None:
        """UI 업데이트"""
        if not self._list_widget:
            print("⚠️ _list_widget이 None입니다")
            return

        print("UI 업데이트 시작")

        # 기존 항목 클리어
        self._list_widget.clear()

        # 필터링된 데이터 가져오기
        filtered_data = self._filter_coins()

        # 아이템 추가
        for coin in filtered_data:
            item_text = f"{coin.symbol} - {coin.name}"
            if coin.price:
                item_text += f" | {coin.price}"
            if coin.change:
                item_text += f" ({coin.change})"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, coin.symbol)
            self._list_widget.addItem(item)

        print(f"UI 업데이트 완료: {len(filtered_data)}개 아이템")

    def _filter_coins(self) -> List[MinimalCoinInfo]:
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
        print(f"마켓 변경: {market}")
        self._current_market = market
        self.market_changed.emit(market)

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
            print(f"코인 선택: {symbol}")

    def get_current_market(self) -> str:
        """현재 마켓 반환"""
        return self._current_market

    def get_selected_symbol(self) -> Optional[str]:
        """선택된 심볼 반환"""
        if self._list_widget:
            current_item = self._list_widget.currentItem()
            if current_item:
                return current_item.data(Qt.ItemDataRole.UserRole)
        return None

    def refresh_data(self) -> None:
        """데이터 새로고침"""
        self._load_sample_data()


# 테스트 함수
def test_minimal_widget():
    """최소 의존성 위젯 테스트"""
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    try:
        print("=== 최소 의존성 위젯 테스트 시작 ===")
        widget = MinimalCoinListWidget()

        print(f"위젯 생성 성공: {id(widget)}")
        print(f"리스트 위젯: {id(widget._list_widget) if widget._list_widget else 'None'}")
        print(f"아이템 수: {widget._list_widget.count() if widget._list_widget else 0}")

        if widget._list_widget and widget._list_widget.count() > 0:
            for i in range(min(3, widget._list_widget.count())):
                item = widget._list_widget.item(i)
                if item:
                    print(f"아이템 {i}: {item.text()}")

        print("=== 테스트 성공! ===")
        return True

    except Exception as e:
        print(f"=== 테스트 실패: {e} ===")
        import traceback
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    test_minimal_widget()
