from PyQt6.QtWidgets import QVBoxLayout, QWidget
from PyQt6.QtWidgets import QTableWidgetItem
from .common.components import StyledComboBox, StyledLineEdit, PrimaryButton, CardWidget

class BacktestingScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.strategy_selector = StyledComboBox(items=["전략1", "전략2"])
        self.param_input = StyledLineEdit("기간/자본/수수료 입력")
        self.run_button = PrimaryButton("백테스트 실행")
        self.result_card = CardWidget("백테스트 결과")
        layout.addWidget(self.strategy_selector)
        layout.addWidget(self.param_input)
        layout.addWidget(self.run_button)
        layout.addWidget(self.result_card)

        # 샘플 결과 데이터
        self.result_data = []
        self.is_loading = False
        self.load_result()

        # 이벤트 연결
        self.run_button.clicked.connect(self.run_backtest)
        self.result_card.findChild(StyledTableWidget).cellClicked.connect(self.on_row_clicked)

        # 최초 데이터 fetch
        self.fetch_result()

    def load_result(self):
        table = self.result_card.findChild(StyledTableWidget)
        if table:
            table.clear()
            table.setRowCount(len(self.result_data))
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["날짜", "수익률", "거래횟수", "결과"])
            if self.is_loading:
                table.setRowCount(1)
                table.setItem(0, 0, QTableWidgetItem("데이터 로딩 중..."))
                return
            for i, row in enumerate(self.result_data):
                for j, val in enumerate(row):
                    table.setItem(i, j, QTableWidgetItem(str(val)))

    def on_row_clicked(self, row, col):
        if row < len(self.result_data):
            print(f"[테스트] 백테스트 행 클릭: {self.result_data[row]}")

    def fetch_result(self):
        # TODO: 실서비스 연동 시 REST API, WebSocket, DB 등에서 데이터 받아오기
        # 실제 구현 시 QThread, asyncio, requests, aiohttp 등 사용
        self.is_loading = True
        self.load_result()
        import time
        time.sleep(0.2)
        self.result_data = [["2025-07-19", "+10%", "5회", "성공"]]
        self.is_loading = False
        self.load_result()

    def save_result(self):
        try:
            with open("backtest_result.csv", "w", encoding="utf-8") as f:
                f.write(",".join(["날짜", "수익률", "거래횟수", "결과"])+"\n")
                for row in self.result_data:
                    f.write(",".join(row)+"\n")
            print("[테스트] backtest_result.csv 파일로 내보내기 완료")
        except Exception as e:
            print(f"[에러] 결과 저장 실패: {e}")
