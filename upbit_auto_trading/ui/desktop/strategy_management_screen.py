from PyQt6.QtWidgets import QVBoxLayout, QWidget, QTableWidgetItem
from PyQt6.QtWidgets import QTableWidgetItem
from .common.components import StyledTableWidget, PrimaryButton, SecondaryButton, DangerButton

class StrategyManagementScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.strategy_table = StyledTableWidget(rows=10, columns=4)
        self.create_button = PrimaryButton("전략 생성")
        self.edit_button = SecondaryButton("전략 수정")
        self.delete_button = DangerButton("전략 삭제")
        layout.addWidget(self.strategy_table)
        layout.addWidget(self.create_button)
        layout.addWidget(self.edit_button)
        layout.addWidget(self.delete_button)

        # 샘플 전략 데이터
        self.strategies = []
        self.is_loading = False
        self.load_strategies()

        # 이벤트 연결
        self.create_button.clicked.connect(self.create_strategy)
        self.edit_button.clicked.connect(self.edit_strategy)
        self.delete_button.clicked.connect(self.delete_strategy)
        self.strategy_table.cellClicked.connect(self.on_row_clicked)

        # 최초 데이터 fetch
        self.fetch_strategies()

        # 이벤트 연결
        self.create_button.clicked.connect(self.create_strategy)
        self.edit_button.clicked.connect(self.edit_strategy)
        self.delete_button.clicked.connect(self.delete_strategy)

    def load_strategies(self):
        self.strategy_table.clear()
        self.strategy_table.setRowCount(len(self.strategies))
        self.strategy_table.setColumnCount(3)
        self.strategy_table.setHorizontalHeaderLabels(["이름", "설명", "파라미터"])
        if self.is_loading:
        self.strategy_table.setRowCount(1)
        self.strategy_table.setItem(0, 0, QTableWidgetItem("데이터 로딩 중..."))
            return
        for i, s in enumerate(self.strategies):
            self.strategy_table.setItem(i, 0, QTableWidgetItem(str(s["이름"])))
            self.strategy_table.setItem(i, 1, QTableWidgetItem(str(s["설명"])))
            self.strategy_table.setItem(i, 2, QTableWidgetItem(str(s["파라미터"])))
    def on_row_clicked(self, row, col):
        if row < len(self.strategies):
            print(f"[테스트] 전략 행 클릭: {self.strategies[row]}")

    def fetch_strategies(self):
        # TODO: 실서비스 연동 시 REST API, WebSocket, DB 등에서 데이터 받아오기
        # 실제 구현 시 QThread, asyncio, requests, aiohttp 등 사용
        self.is_loading = True
        self.load_strategies()
        import time
        time.sleep(0.2)
        self.strategies = [
            {"이름": "모멘텀", "설명": "상승 추세 매수", "파라미터": "window=20"},
            {"이름": "역추세", "설명": "과매도 반등 매수", "파라미터": "threshold=30"}
        ]
        self.is_loading = False
        self.load_strategies()

    def save_strategies(self):
        try:
            with open("strategies.csv", "w", encoding="utf-8") as f:
                f.write(",".join(["이름", "설명", "파라미터"])+"\n")
                for s in self.strategies:
                    f.write(f"{s['이름']},{s['설명']},{s['파라미터']}\n")
            print("[테스트] strategies.csv 파일로 내보내기 완료")
        except Exception as e:
            print(f"[에러] 전략 저장 실패: {e}")

    def create_strategy(self):
        # 테스트용: 새 전략 추가
        new_strategy = {"이름": "신규전략", "설명": "테스트", "파라미터": "param=1"}
        self.strategies.append(new_strategy)
        self.load_strategies()
        print("[테스트] 전략 생성: 신규전략")

    def edit_strategy(self):
        # 테스트용: 첫 전략 수정
        if self.strategies:
            self.strategies[0]["설명"] = "수정됨"
            self.load_strategies()
            print(f"[테스트] 전략 수정: {self.strategies[0]['이름']}")

    def delete_strategy(self):
        # 테스트용: 마지막 전략 삭제
        if self.strategies:
            removed = self.strategies.pop()
            self.load_strategies()
            print(f"[테스트] 전략 삭제: {removed['이름']}")
