"""
컴포넌트 선택기 테스트 런처
두 가지 방식을 모두 테스트할 수 있습니다.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QLabel, QPushButton, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from option_a_tree_combo import OptionATestWidget
from option_b_dialog import OptionBTestWidget


class TestLauncherWidget(QWidget):
    """테스트 런처 메인 위젯"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧪 컴포넌트 선택기 테스트 런처 (실제 403개 컴포넌트!)")
        self.setGeometry(300, 300, 600, 400)

        # 서브 윈도우들 참조
        self.option_a_window = None
        self.option_b_window = None

        self._setup_ui()

    def _setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)

        # 제목
        title_label = QLabel("🧪 Component Focus 선택기 테스트 (실제 데이터!)")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 설명
        desc_label = QLabel(
            "실제 403개 컴포넌트로 두 가지 방식을 테스트할 수 있습니다.\n"
            "Option A: 혁신적 콤보박스+트리 vs Option B: 안전한 다이얼로그\n"
            "각 방식의 장단점을 비교해보세요!"
        )
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Option A 그룹
        option_a_group = QGroupBox("🔥 Option A: QComboBox + QTreeWidget")
        option_a_layout = QVBoxLayout(option_a_group)

        option_a_desc = QLabel(
            "• 일반 콤보박스처럼 보이지만 드롭다운이 트리 구조\n"
            "• 공간 효율적, UI 통합도 높음\n"
            "• 혁신적이고 사용자 친화적"
        )
        option_a_layout.addWidget(option_a_desc)

        option_a_btn = QPushButton("Option A 테스트 시작")
        option_a_btn.clicked.connect(self._launch_option_a)
        option_a_layout.addWidget(option_a_btn)

        layout.addWidget(option_a_group)

        # Option B 그룹
        option_b_group = QGroupBox("🛡️ Option B: 별도 다이얼로그")
        option_b_layout = QVBoxLayout(option_b_group)

        option_b_desc = QLabel(
            "• 버튼 클릭시 전용 다이얼로그 팝업\n"
            "• 검색 기능, 상세 정보 제공\n"
            "• 안전하고 기능이 풍부함"
        )
        option_b_layout.addWidget(option_b_desc)

        option_b_btn = QPushButton("Option B 테스트 시작")
        option_b_btn.clicked.connect(self._launch_option_b)
        option_b_layout.addWidget(option_b_btn)

        layout.addWidget(option_b_group)

        # 동시 실행 버튼
        both_btn = QPushButton("🚀 두 방식 모두 테스트")
        both_btn.setStyleSheet("QPushButton { font-weight: bold; padding: 10px; }")
        both_btn.clicked.connect(self._launch_both)
        layout.addWidget(both_btn)

        # 종료 버튼
        exit_btn = QPushButton("종료")
        exit_btn.clicked.connect(self.close)
        layout.addWidget(exit_btn)

    def _launch_option_a(self):
        """Option A 테스트 창 열기"""
        if self.option_a_window is None or not self.option_a_window.isVisible():
            self.option_a_window = OptionATestWidget()
            self.option_a_window.show()
        else:
            self.option_a_window.raise_()
            self.option_a_window.activateWindow()

    def _launch_option_b(self):
        """Option B 테스트 창 열기"""
        if self.option_b_window is None or not self.option_b_window.isVisible():
            self.option_b_window = OptionBTestWidget()
            self.option_b_window.show()
        else:
            self.option_b_window.raise_()
            self.option_b_window.activateWindow()

    def _launch_both(self):
        """두 방식 모두 실행"""
        self._launch_option_a()
        self._launch_option_b()


def main():
    """메인 실행 함수"""
    app = QApplication(sys.argv)

    # 런처 창 생성
    launcher = TestLauncherWidget()
    launcher.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
