from PyQt6.QtWidgets import QVBoxLayout, QWidget, QTableWidgetItem
from .common.components import PrimaryButton
from .common.components import CardWidget, StyledTableWidget

class DashboardScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.portfolio_card = CardWidget("포트폴리오 요약")
        self.market_card = CardWidget("시장 개요")
        self.active_positions_card = CardWidget("실시간 거래 현황")
        self.refresh_button = PrimaryButton("실시간 데이터 갱신")
        self.portfolio_card.add_widget(StyledTableWidget(rows=5, columns=3))
        self.market_card.add_widget(StyledTableWidget(rows=10, columns=4))
        self.active_positions_card.add_widget(StyledTableWidget(rows=5, columns=5))
        layout.addWidget(self.portfolio_card)
        layout.addWidget(self.market_card)
        layout.addWidget(self.active_positions_card)
        layout.addWidget(self.refresh_button)

        # 샘플 데이터
        self.portfolio_data = []
        self.is_loading = False
        self.load_portfolio()

        # 이벤트 연결
        self.refresh_button.clicked.connect(self.refresh_data)
        self.portfolio_card.findChild(StyledTableWidget).cellClicked.connect(self.on_row_clicked)

        # 최초 데이터 fetch
        self.fetch_portfolio()

    def load_portfolio(self):
        table = self.portfolio_card.findChild(StyledTableWidget)
        if table:
            table.clear()
            table.setRowCount(len(self.portfolio_data))
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels(["코인", "수량", "수익률"])
            if self.is_loading:
                table.setRowCount(1)
            from PyQt6.QtWidgets import QTableWidgetItem
            table.setItem(0, 0, QTableWidgetItem("데이터 로딩 중..."))
                return
            for i, row in enumerate(self.portfolio_data):
                for j, val in enumerate(row):
                from PyQt6.QtWidgets import QTableWidgetItem
                table.setItem(i, j, QTableWidgetItem(str(val)))

    def refresh_data(self):
        print("[테스트] 실시간 데이터 갱신")
        self.fetch_portfolio()

    def on_row_clicked(self, row, col):
        if row < len(self.portfolio_data):
            print(f"[테스트] 포트폴리오 행 클릭: {self.portfolio_data[row]}")

    def fetch_portfolio(self):
        self.is_loading = True
        self.load_portfolio()
        import time
        time.sleep(0.2)
        self.portfolio_data = [["BTC", "2개", "+5%"], ["ETH", "1개", "+3%"]]
        self.is_loading = False
        self.load_portfolio()

        try:
                table.setItem(0, 0, QTableWidgetItem("데이터 로딩 중..."))
            with open("portfolio.csv", "w", encoding="utf-8") as f:
                f.write(",".join(["코인", "수량", "수익률"])+"\n")
                for row in self.portfolio_data:
                    f.write(",".join(row)+"\n")
            print("[테스트] portfolio.csv 파일로 내보내기 완료")
        except Exception as e:
            print(f"[에러] 포트폴리오 저장 실패: {e}")
