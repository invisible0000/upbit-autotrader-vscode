"""
간단하고 안전한 즐겨찾기 테스트
"""

import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel
from PyQt6.QtCore import QTimer

# 수정된 위젯 임포트
from upbit_auto_trading.ui.desktop.screens.chart_view.widgets.coin_list_widget import CoinListWidget


class SafeFavoritesTestWindow(QMainWindow):
    """안전한 즐겨찾기 테스트 윈도우"""

    def __init__(self):
        super().__init__()
        self.coin_widget = None
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("즐겨찾기 기능 테스트 - 안전 버전")
        self.setGeometry(100, 100, 500, 700)

        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 상태 라벨
        self.status_label = QLabel("초기화 중...")
        layout.addWidget(self.status_label)

        # 테스트 버튼들
        button_layout = QHBoxLayout()

        self.toggle_btc_btn = QPushButton("BTC 즐겨찾기 토글")
        self.toggle_btc_btn.clicked.connect(self.toggle_btc_favorite)
        self.toggle_btc_btn.setEnabled(False)

        self.toggle_eth_btn = QPushButton("ETH 즐겨찾기 토글")
        self.toggle_eth_btn.clicked.connect(self.toggle_eth_favorite)
        self.toggle_eth_btn.setEnabled(False)

        button_layout.addWidget(self.toggle_btc_btn)
        button_layout.addWidget(self.toggle_eth_btn)
        layout.addLayout(button_layout)

        # 코인 위젯 초기화를 지연
        QTimer.singleShot(100, self.init_coin_widget)

    def init_coin_widget(self):
        """코인 위젯 지연 초기화"""
        try:
            self.status_label.setText("코인 위젯 생성 중...")

            # 코인 위젯 생성
            self.coin_widget = CoinListWidget()

            # 시그널 연결
            self.coin_widget.favorite_toggled.connect(self.on_favorite_toggled)

            # 레이아웃에 추가 - 직접 참조 방식
            if hasattr(self, 'centralWidget'):
                central = self.centralWidget()
                if central is not None:
                    main_layout = central.layout()
                    if main_layout is not None:
                        main_layout.addWidget(self.coin_widget)

            # 버튼 활성화
            self.toggle_btc_btn.setEnabled(True)
            self.toggle_eth_btn.setEnabled(True)

            self.status_label.setText("✅ 초기화 완료! 테스트를 시작하세요.")

            print("✅ 코인 위젯 초기화 성공!")
            print("💡 테스트 방법:")
            print("   - 코인 우클릭: 즐겨찾기 메뉴")
            print("   - ⭐ 체크박스: 즐겨찾기만 보기")
            print("   - 테스트 버튼: 프로그래밍 방식 토글")

        except Exception as e:
            error_msg = f"❌ 코인 위젯 초기화 실패: {e}"
            self.status_label.setText(error_msg)
            print(error_msg)
            traceback.print_exc()

    def toggle_btc_favorite(self):
        """BTC 즐겨찾기 토글"""
        if self.coin_widget:
            self.coin_widget.toggle_favorite("KRW-BTC")

    def toggle_eth_favorite(self):
        """ETH 즐겨찾기 토글"""
        if self.coin_widget:
            self.coin_widget.toggle_favorite("KRW-ETH")

    def on_favorite_toggled(self, symbol, is_favorite):
        """즐겨찾기 토글 시그널 처리"""
        status = "추가" if is_favorite else "해제"
        msg = f"🔔 {symbol} 즐겨찾기 {status}"
        print(msg)
        self.status_label.setText(msg)


def main():
    """메인 함수"""
    print("=== 안전한 즐겨찾기 테스트 시작 ===")

    # QApplication 생성
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    try:
        # 메인 윈도우 생성
        window = SafeFavoritesTestWindow()
        window.show()

        print("🚀 테스트 윈도우 표시 완료")
        print("🚪 창을 닫으면 테스트가 종료됩니다")

        # 이벤트 루프 실행
        return app.exec()

    except Exception as e:
        print(f"❌ 애플리케이션 실행 실패: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    print(f"👋 테스트 종료 (코드: {exit_code})")
    sys.exit(exit_code)
