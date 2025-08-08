"""
Strategy Maker Passive View - MVP 패턴

기존 StrategyMaker를 MVP 패턴의 Passive View로 리팩토링한 버전입니다.
모든 비즈니스 로직은 Presenter에 위임하고, 순수한 UI 기능만 담당합니다.
"""

from typing import Dict, Any, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QMessageBox, QTextEdit, QListWidget, QListWidgetItem,
    QLineEdit, QSpinBox, QDoubleSpinBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal

from upbit_auto_trading.presentation.presenters.strategy_maker_presenter import StrategyMakerPresenter
from upbit_auto_trading.ui.desktop.common.components import (
    PrimaryButton, SecondaryButton, DangerButton,
    StyledLineEdit
)


# PyQt6와 Protocol 기반 인터페이스 사용 (메타클래스 충돌 방지)
class StrategyMakerView(QWidget):
    """전략 메이커 Passive View

    MVP 패턴의 Passive View로 구현된 전략 메이커 UI입니다.
    모든 비즈니스 로직은 Presenter에 위임하고, 순수한 표시/입력 기능만 담당합니다.

    Note: IStrategyMakerView Protocol을 구조적으로 구현합니다.
    """

    def __init__(self, presenter: StrategyMakerPresenter, parent=None):
        """View 초기화

        Args:
            presenter: Strategy Maker Presenter
            parent: 부모 위젯
        """
        super().__init__(parent)
        self._presenter = presenter
        self.setWindowTitle("⚙️ 전략 메이커 (MVP)")

        # UI 구성 요소 초기화
        self._init_ui_components()
        self._setup_ui()
        self._connect_signals()

        # 초기 데이터 로드
        self._presenter.load_strategies()

    def _init_ui_components(self):
        """UI 구성 요소 초기화"""
        # 전략 기본 정보
        self.strategy_name_input = StyledLineEdit()
        self.strategy_desc_input = QTextEdit()

        # 전략 목록
        self.strategy_list_widget = QListWidget()

        # 진입/청산 조건
        self.entry_conditions_list = QListWidget()
        self.exit_conditions_list = QListWidget()

        # 리스크 관리
        self.stop_loss_input = QDoubleSpinBox()
        self.take_profit_input = QDoubleSpinBox()
        self.position_size_input = QDoubleSpinBox()
        self.max_positions_input = QSpinBox()

        # 버튼들
        self.save_button = PrimaryButton("💾 전략 저장")
        self.load_button = SecondaryButton("📂 전략 불러오기")
        self.validate_button = SecondaryButton("✅ 검증")
        self.clear_button = DangerButton("🗑️ 초기화")

        # 상태 표시
        self.status_label = QLabel("새 전략 생성 중...")
        self.progress_bar = QProgressBar()
        self.loading_label = QLabel()
        self.loading_label.hide()

    def _setup_ui(self):
        """UI 레이아웃 설정"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 헤더
        header_layout = QHBoxLayout()
        title_label = QLabel("⚙️ 전략 메이커")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        main_layout.addLayout(header_layout)

        # 메인 콘텐츠 (좌우 분할)
        content_layout = QHBoxLayout()

        # 왼쪽: 전략 목록
        left_panel = self._create_strategy_list_panel()
        content_layout.addWidget(left_panel, 1)

        # 오른쪽: 전략 편집
        right_panel = self._create_strategy_edit_panel()
        content_layout.addWidget(right_panel, 2)

        main_layout.addLayout(content_layout)

        # 하단: 컨트롤 버튼
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.validate_button)
        button_layout.addStretch()
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.save_button)
        main_layout.addLayout(button_layout)

        # 상태 표시
        main_layout.addWidget(self.loading_label)
        main_layout.addWidget(self.progress_bar)

    def _create_strategy_list_panel(self) -> QGroupBox:
        """전략 목록 패널 생성"""
        group = QGroupBox("📋 저장된 전략")
        layout = QVBoxLayout(group)

        layout.addWidget(self.strategy_list_widget)

        return group

    def _create_strategy_edit_panel(self) -> QGroupBox:
        """전략 편집 패널 생성"""
        group = QGroupBox("✏️ 전략 편집")
        layout = QVBoxLayout(group)

        # 기본 정보
        basic_info_group = QGroupBox("기본 정보")
        basic_layout = QVBoxLayout(basic_info_group)

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("전략명:"))
        name_layout.addWidget(self.strategy_name_input)
        basic_layout.addLayout(name_layout)

        basic_layout.addWidget(QLabel("설명:"))
        self.strategy_desc_input.setMaximumHeight(60)
        basic_layout.addWidget(self.strategy_desc_input)

        layout.addWidget(basic_info_group)

        # 조건 설정
        conditions_group = QGroupBox("진입/청산 조건")
        conditions_layout = QHBoxLayout(conditions_group)

        # 진입 조건
        entry_layout = QVBoxLayout()
        entry_layout.addWidget(QLabel("진입 조건:"))
        self.entry_conditions_list.setMaximumHeight(100)
        entry_layout.addWidget(self.entry_conditions_list)
        conditions_layout.addLayout(entry_layout)

        # 청산 조건
        exit_layout = QVBoxLayout()
        exit_layout.addWidget(QLabel("청산 조건:"))
        self.exit_conditions_list.setMaximumHeight(100)
        exit_layout.addWidget(self.exit_conditions_list)
        conditions_layout.addLayout(exit_layout)

        layout.addWidget(conditions_group)

        # 리스크 관리
        risk_group = QGroupBox("리스크 관리")
        risk_layout = QVBoxLayout(risk_group)

        risk_row1 = QHBoxLayout()
        risk_row1.addWidget(QLabel("손절 비율(%):"))
        self.stop_loss_input.setRange(0.1, 50.0)
        self.stop_loss_input.setValue(5.0)
        self.stop_loss_input.setSuffix("%")
        risk_row1.addWidget(self.stop_loss_input)

        risk_row1.addWidget(QLabel("익절 비율(%):"))
        self.take_profit_input.setRange(0.1, 100.0)
        self.take_profit_input.setValue(10.0)
        self.take_profit_input.setSuffix("%")
        risk_row1.addWidget(self.take_profit_input)
        risk_layout.addLayout(risk_row1)

        risk_row2 = QHBoxLayout()
        risk_row2.addWidget(QLabel("포지션 크기(%):"))
        self.position_size_input.setRange(1.0, 100.0)
        self.position_size_input.setValue(10.0)
        self.position_size_input.setSuffix("%")
        risk_row2.addWidget(self.position_size_input)

        risk_row2.addWidget(QLabel("최대 포지션:"))
        self.max_positions_input.setRange(1, 10)
        self.max_positions_input.setValue(3)
        risk_row2.addWidget(self.max_positions_input)
        risk_layout.addLayout(risk_row2)

        layout.addWidget(risk_group)

        return group

    def _connect_signals(self):
        """시그널 연결 - Presenter에 위임"""
        self.save_button.clicked.connect(self._on_save_clicked)
        self.load_button.clicked.connect(self._on_load_clicked)
        self.validate_button.clicked.connect(self._on_validate_clicked)
        self.clear_button.clicked.connect(self._on_clear_clicked)
        self.strategy_list_widget.itemDoubleClicked.connect(self._on_strategy_item_double_clicked)

    def _on_save_clicked(self):
        """저장 버튼 클릭 - Presenter에 위임"""
        self._presenter.save_strategy()

    def _on_load_clicked(self):
        """불러오기 버튼 클릭 - Presenter에 위임"""
        # 선택된 전략이 있으면 로드
        current_item = self.strategy_list_widget.currentItem()
        if current_item:
            strategy_id = current_item.data(Qt.ItemDataRole.UserRole)
            self._presenter.load_strategy(strategy_id)
        else:
            QMessageBox.information(self, "알림", "로드할 전략을 선택해주세요.")

    def _on_validate_clicked(self):
        """검증 버튼 클릭 - Presenter에 위임"""
        self._presenter.validate_strategy()

    def _on_clear_clicked(self):
        """초기화 버튼 클릭 - Presenter에 위임"""
        self._presenter.clear_strategy()

    def _on_strategy_item_double_clicked(self, item: QListWidgetItem):
        """전략 아이템 더블클릭 - 자동 로드"""
        strategy_id = item.data(Qt.ItemDataRole.UserRole)
        self._presenter.load_strategy(strategy_id)

    # IStrategyMakerView 인터페이스 구현

    def display_strategy_list(self, strategies: List[Dict[str, Any]]) -> None:
        """전략 목록 표시"""
        self.strategy_list_widget.clear()
        for strategy in strategies:
            item = QListWidgetItem(f"{strategy['name']} ({strategy['status']})")
            item.setData(Qt.ItemDataRole.UserRole, strategy['id'])
            item.setToolTip(f"생성일: {strategy['created_at']}\n설명: {strategy['description']}")
            self.strategy_list_widget.addItem(item)

    def display_validation_errors(self, errors: List[str]) -> None:
        """검증 오류 표시"""
        error_message = "다음 문제를 해결해주세요:\n\n" + "\n".join(f"• {error}" for error in errors)
        QMessageBox.warning(self, "검증 오류", error_message)

    def display_success_message(self, message: str) -> None:
        """성공 메시지 표시"""
        QMessageBox.information(self, "성공", message)

    def display_error_message(self, message: str) -> None:
        """오류 메시지 표시"""
        QMessageBox.critical(self, "오류", message)

    def clear_form(self) -> None:
        """폼 초기화"""
        self.strategy_name_input.clear()
        self.strategy_desc_input.clear()
        self.entry_conditions_list.clear()
        self.exit_conditions_list.clear()
        self.stop_loss_input.setValue(5.0)
        self.take_profit_input.setValue(10.0)
        self.position_size_input.setValue(10.0)
        self.max_positions_input.setValue(3)
        self.status_label.setText("새 전략 생성 중...")

    def get_strategy_form_data(self) -> Dict[str, Any]:
        """폼에서 전략 데이터 수집"""
        # 진입 조건 수집
        entry_triggers = []
        for i in range(self.entry_conditions_list.count()):
            item = self.entry_conditions_list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole):
                entry_triggers.append(item.data(Qt.ItemDataRole.UserRole))

        # 청산 조건 수집
        exit_triggers = []
        for i in range(self.exit_conditions_list.count()):
            item = self.exit_conditions_list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole):
                exit_triggers.append(item.data(Qt.ItemDataRole.UserRole))

        return {
            'name': self.strategy_name_input.text(),
            'description': self.strategy_desc_input.toPlainText(),
            'entry_triggers': entry_triggers,
            'exit_triggers': exit_triggers,
            'risk_management': {
                'stop_loss': self.stop_loss_input.value(),
                'take_profit': self.take_profit_input.value(),
                'position_size': self.position_size_input.value(),
                'max_positions': self.max_positions_input.value()
            }
        }

    def set_strategy_form_data(self, strategy_data: Dict[str, Any]) -> None:
        """폼에 전략 데이터 설정"""
        self.strategy_name_input.setText(strategy_data.get('name', ''))
        self.strategy_desc_input.setPlainText(strategy_data.get('description', ''))

        # 리스크 관리 설정
        risk_management = strategy_data.get('risk_management', {})
        self.stop_loss_input.setValue(risk_management.get('stop_loss', 5.0))
        self.take_profit_input.setValue(risk_management.get('take_profit', 10.0))
        self.position_size_input.setValue(risk_management.get('position_size', 10.0))
        self.max_positions_input.setValue(risk_management.get('max_positions', 3))

        # 조건들 설정 (추후 구현)
        # TODO: entry_triggers, exit_triggers 설정

        self.status_label.setText(f"편집 중: {strategy_data.get('name', '')}")

    def show_loading(self, message: str = "처리 중...") -> None:
        """로딩 상태 표시"""
        self.loading_label.setText(message)
        self.loading_label.show()
        self.progress_bar.setRange(0, 0)  # 무한 진행바

        # 버튼 비활성화
        self.save_button.setEnabled(False)
        self.load_button.setEnabled(False)
        self.validate_button.setEnabled(False)
        self.clear_button.setEnabled(False)

    def hide_loading(self) -> None:
        """로딩 상태 숨김"""
        self.loading_label.hide()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        # 버튼 활성화
        self.save_button.setEnabled(True)
        self.load_button.setEnabled(True)
        self.validate_button.setEnabled(True)
        self.clear_button.setEnabled(True)
