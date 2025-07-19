from PyQt6.QtWidgets import QVBoxLayout, QWidget, QTableWidgetItem
from .common.components import StyledTableWidget, PrimaryButton, SecondaryButton

class PortfolioScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.coin_table = StyledTableWidget(rows=10, columns=4)
        self.add_button = PrimaryButton("코인 추가")
        self.remove_button = SecondaryButton("코인 제거")
        layout.addWidget(self.coin_table)
        layout.addWidget(self.add_button)
        layout.addWidget(self.remove_button)

        # 샘플 데이터
        self.coins = []
        self.is_loading = False
        self.load_coins()

        # 이벤트 연결
        self.add_button.clicked.connect(self.add_coin)
        self.remove_button.clicked.connect(self.remove_coin)
        self.coin_table.cellClicked.connect(self.on_row_clicked)

        # 최초 데이터 fetch
        self.fetch_coins()

    def load_coins(self):
        self.coin_table.clear()
        self.coin_table.setRowCount(len(self.coins))
        self.coin_table.setColumnCount(4)
        self.coin_table.setHorizontalHeaderLabels(["코인", "수량", "수익률", "포트폴리오"])
        if self.is_loading:
            self.coin_table.setRowCount(1)
            from PyQt6.QtWidgets import QTableWidgetItem
            self.coin_table.setItem(0, 0, "데이터 로딩 중...")
            return
        for i, row in enumerate(self.coins):
            for j, val in enumerate(row):
                from PyQt6.QtWidgets import QTableWidgetItem
                self.coin_table.setItem(i, j, str(val))
        # QTableWidgetItem 사용 방식 통일
    def on_row_clicked(self, row, col):
        if row < len(self.coins):
            print(f"[테스트] 포트폴리오 행 클릭: {self.coins[row]}")

    def fetch_coins(self):
        # TODO: 실서비스 연동 시 REST API, WebSocket, DB 등에서 데이터 받아오기
        # 실제 구현 시 QThread, asyncio, requests, aiohttp 등 사용
        self.is_loading = True
        self.load_coins()
        import time
        time.sleep(0.2)
        self.coins = [["BTC", "2개", "+5%", "O"], ["ETH", "1개", "+3%", "X"]]
        self.is_loading = False
        self.load_coins()

    def save_portfolio(self):
        try:
            with open("portfolio.csv", "w", encoding="utf-8") as f:
                f.write(",".join(["코인", "수량", "수익률", "포트폴리오"])+"\n")
                for row in self.coins:
                    f.write(",".join(row)+"\n")
            print("[테스트] portfolio.csv 파일로 내보내기 완료")
        except Exception as e:
            print(f"[에러] 포트폴리오 저장 실패: {e}")

    def add_coin(self):
        self.coins.append(["XRP", "1개", "+2%", "O"])
        self.load_coins()
        print("[테스트] 코인 추가: XRP")

    def remove_coin(self):
        if self.coins:
            removed = self.coins.pop()
            self.load_coins()
            print(f"[테스트] 코인 제거: {removed[0]}")
