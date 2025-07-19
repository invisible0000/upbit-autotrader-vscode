from PyQt6.QtWidgets import QVBoxLayout, QWidget, QTableWidgetItem
from .common.components import StyledTableWidget, StyledLineEdit, PrimaryButton, CardWidget

class RealtimeTradeScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.active_strategy_table = StyledTableWidget(rows=5, columns=4)
        self.order_input = StyledLineEdit("수동 주문 입력")
        self.order_button = PrimaryButton("주문 실행")
        self.market_data_card = CardWidget("실시간 시장 데이터")
        self.refresh_button = PrimaryButton("실시간 데이터 갱신")
        layout.addWidget(self.active_strategy_table)
        layout.addWidget(self.order_input)
        layout.addWidget(self.order_button)
        layout.addWidget(self.market_data_card)
        layout.addWidget(self.refresh_button)

        # 샘플 데이터
        self.strategies = []
        self.is_loading = False
        self.load_strategies()

        # 이벤트 연결
        self.order_button.clicked.connect(self.execute_order)
        self.refresh_button.clicked.connect(self.refresh_data)
        self.active_strategy_table.cellClicked.connect(self.on_row_clicked)

        # 최초 데이터 fetch
        self.fetch_strategies()

    def load_strategies(self):
        self.active_strategy_table.clear()
        self.active_strategy_table.setRowCount(len(self.strategies))
        self.active_strategy_table.setColumnCount(4)
        self.active_strategy_table.setHorizontalHeaderLabels(["전략", "상태", "코인", "포지션"])
        if self.is_loading:
            self.active_strategy_table.setRowCount(1)
            from PyQt6.QtWidgets import QTableWidgetItem
            self.active_strategy_table.setItem(0, 0, "데이터 로딩 중...")
            return
        for i, row in enumerate(self.strategies):
            for j, val in enumerate(row):
                from PyQt6.QtWidgets import QTableWidgetItem
                self.active_strategy_table.setItem(i, j, str(val))

    def execute_order(self):
        order = self.order_input.text()
        print(f"[테스트] 주문 실행: {order}")
        try:
            with open("orders.csv", "a", encoding="utf-8") as f:
                f.write(order+"\n")
            print("[테스트] orders.csv 파일에 주문 내역 저장 완료")
        except Exception as e:
            print(f"[에러] 주문 저장 실패: {e}")

    def refresh_data(self):
        print("[테스트] 실시간 데이터 갱신")
        self.fetch_strategies()

    def on_row_clicked(self, row, col):
        if row < len(self.strategies):
            print(f"[테스트] 전략 행 클릭: {self.strategies[row]}")

    def fetch_strategies(self):
        self.is_loading = True
        self.load_strategies()
        import time
        time.sleep(0.2)
        self.strategies = [["모멘텀", "진입", "BTC", "O"], ["역추세", "대기", "ETH", "X"]]
        self.is_loading = False
        self.load_strategies()
