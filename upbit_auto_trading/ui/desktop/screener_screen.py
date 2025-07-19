from PyQt6.QtWidgets import QVBoxLayout, QWidget, QTableWidgetItem
from .common.components import StyledComboBox, StyledTableWidget, PrimaryButton

class ScreenerScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.filter_box = StyledComboBox(items=["거래량", "변동성", "추세"])
        self.result_table = StyledTableWidget(rows=20, columns=6)
        self.save_button = PrimaryButton("결과 저장")
        layout.addWidget(self.filter_box)
        layout.addWidget(self.result_table)
        layout.addWidget(self.save_button)

        # 샘플 결과 데이터
        self.results = []
        self.is_loading = False
        self.load_results()

        # 이벤트 연결
        self.filter_box.currentIndexChanged.connect(self.on_filter_changed)
        self.save_button.clicked.connect(self.save_results)
        self.result_table.cellClicked.connect(self.on_row_clicked)

        # 최초 데이터 fetch
        self.fetch_results(self.filter_box.currentText())

    def load_results(self):
        self.result_table.clear()
        self.result_table.setRowCount(len(self.results))
        self.result_table.setColumnCount(6)
        self.result_table.setHorizontalHeaderLabels(["코인", "거래량", "변동률", "추세", "포지션", "포트폴리오"])
        if self.is_loading:
            self.result_table.setRowCount(1)
            self.result_table.setItem(0, 0, QTableWidgetItem("데이터 로딩 중..."))
            return
        for i, row in enumerate(self.results):
            for j, val in enumerate(row):
                self.result_table.setItem(i, j, QTableWidgetItem(str(val)))

    def on_filter_changed(self, idx):
        print(f"[테스트] 필터 변경: {self.filter_box.currentText()}")
        self.fetch_results(self.filter_box.currentText())

    def save_results(self):
        print("[테스트] 결과 저장/내보내기")
        # 테스트: 결과를 파일로 저장
        try:
            with open("screener_results.csv", "w", encoding="utf-8") as f:
                f.write(",".join(["코인", "거래량", "변동률", "추세", "포지션", "포트폴리오"])+"\n")
                for row in self.results:
                    f.write(",".join(row)+"\n")
            print("[테스트] screener_results.csv 파일로 내보내기 완료")
        except Exception as e:
            print(f"[에러] 결과 저장 실패: {e}")

    def on_row_clicked(self, row, col):
        if row < len(self.results):
            print(f"[테스트] 행 클릭: {self.results[row]}")

    def fetch_results(self, filter_name):
        # TODO: 실서비스 연동 시 REST API, WebSocket, DB 등에서 데이터 받아오기
        # 실제 구현 시 QThread, asyncio, requests, aiohttp 등 사용
        self.is_loading = True
        self.load_results()
        import time
        time.sleep(0.2)  # 테스트용 딜레이
        if filter_name == "거래량":
            self.results = [["BTC", "1000", "5%", "상승", "고점", "O"], ["ETH", "800", "3%", "하락", "저점", "X"]]
        elif filter_name == "변동성":
            self.results = [["XRP", "500", "2%", "횡보", "중립", "O"]]
        else:
            self.results = [["ADA", "300", "1%", "상승", "저점", "O"]]
        self.is_loading = False
        self.load_results()
