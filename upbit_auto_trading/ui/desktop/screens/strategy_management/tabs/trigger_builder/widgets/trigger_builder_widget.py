"""
트리거 빌더 메인 Widget - MVP View 구현체
Legacy UI 레이아웃을 100% 그대로 복사하여 구현
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QGroupBox,
    QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.dto.trigger_builder.trading_variable_dto import (
    TradingVariableListDTO,
    TradingVariableDetailDTO
)


class TriggerBuilderWidget(QWidget):
    """트리거 빌더 메인 Widget - MVP View 구현체

    ITriggerBuilderView 인터페이스를 구현하지만 다중 상속을 피하기 위해
    메타클래스 충돌을 방지합니다.
    """

    # 시그널 정의
    variable_selected = pyqtSignal(str)  # 변수 선택
    search_requested = pyqtSignal(str, str)  # 검색 요청 (검색어, 카테고리)
    simulation_start_requested = pyqtSignal()  # 시뮬레이션 시작
    simulation_stop_requested = pyqtSignal()  # 시뮬레이션 중지

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = create_component_logger("TriggerBuilderWidget")
        self._setup_ui()

    def _setup_ui(self):
        """UI 초기화 - Legacy 레이아웃 100% 복사"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)  # 마진 늘리기
        main_layout.setSpacing(5)  # 간격 늘리기

        # 메인 그리드 레이아웃 (3x2) - Legacy와 동일
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setContentsMargins(5, 5, 5, 5)  # 그리드 마진 늘리기
        grid_layout.setSpacing(8)  # 그리드 간격 늘리기

        # 1+4: 조건 빌더 (좌측, 세로 합쳐짐) - Legacy와 동일
        self.condition_builder_area = self._create_condition_builder_area()
        grid_layout.addWidget(self.condition_builder_area, 0, 0, 2, 1)  # 2행에 걸쳐 배치

        # 2: 등록된 트리거 리스트 (중앙 상단) - Legacy와 동일
        self.trigger_list_area = self._create_trigger_list_area()
        grid_layout.addWidget(self.trigger_list_area, 0, 1, 1, 1)

        # 3: 케이스 시뮬레이션 버튼들 (우측 상단) - Legacy와 동일
        self.simulation_area = self._create_simulation_area()
        self.simulation_area.setMinimumWidth(300)
        grid_layout.addWidget(self.simulation_area, 0, 2, 1, 1)

        # 5: 선택한 트리거 상세 정보 (중앙 하단) - Legacy와 동일
        self.trigger_detail_area = self._create_trigger_detail_area()
        grid_layout.addWidget(self.trigger_detail_area, 1, 1, 1, 1)

        # 6: 작동 마커 차트 + 작동 기록 (우측 하단) - Legacy와 동일
        self.test_result_area = self._create_test_result_area()
        self.test_result_area.setMinimumWidth(300)
        grid_layout.addWidget(self.test_result_area, 1, 2, 1, 1)

        # 그리드 비율 설정 (35:40:25) - Legacy와 동일
        grid_layout.setColumnStretch(0, 35)  # 조건 빌더
        grid_layout.setColumnStretch(1, 35)  # 트리거 관리
        grid_layout.setColumnStretch(2, 30)  # 시뮬레이션

        # 행 비율 설정 - Legacy와 동일
        grid_layout.setRowStretch(0, 1)  # 상단
        grid_layout.setRowStretch(1, 1)  # 하단

        main_layout.addWidget(grid_widget)

        self._logger.info("트리거 빌더 UI 초기화 완료")

    def _create_condition_builder_area(self) -> QGroupBox:
        """1+4: 조건 빌더 영역 - Legacy UI 복사"""
        group = QGroupBox("🎯 조건 빌더")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 8, 5, 5)
        layout.setSpacing(3)

        # TODO: 조건 빌더 컴포넌트 임베드
        placeholder = QLabel("조건 빌더 영역\n(컨디션 빌더 컴포넌트 예정)")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder)

        group.setLayout(layout)
        return group

    def _create_trigger_list_area(self) -> QGroupBox:
        """2: 등록된 트리거 리스트 영역 - Legacy UI 복사"""
        group = QGroupBox("📝 등록된 트리거")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 8, 5, 5)
        layout.setSpacing(3)

        # TODO: 트리거 리스트 위젯 임베드
        placeholder = QLabel("트리거 목록 영역\n(TriggerListWidget 예정)")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder)

        group.setLayout(layout)
        return group

    def _create_simulation_area(self) -> QGroupBox:
        """3: 케이스 시뮬레이션 영역 - Legacy UI 복사"""
        group = QGroupBox("🧪 시뮬레이션 제어")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 8, 5, 5)
        layout.setSpacing(3)

        # TODO: 시뮬레이션 컨트롤 위젯 임베드
        placeholder = QLabel("시뮬레이션 컨트롤 영역\n(SimulationControlWidget 예정)")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder)

        # 임시 시뮬레이션 버튼들
        start_btn = QPushButton("▶️ 시뮬레이션 시작")
        start_btn.clicked.connect(self.simulation_start_requested.emit)
        layout.addWidget(start_btn)

        stop_btn = QPushButton("⏹️ 시뮬레이션 중지")
        stop_btn.clicked.connect(self.simulation_stop_requested.emit)
        layout.addWidget(stop_btn)

        group.setLayout(layout)
        return group

    def _create_trigger_detail_area(self) -> QGroupBox:
        """5: 선택한 트리거 상세 정보 영역 - Legacy UI 복사"""
        group = QGroupBox("🔍 트리거 상세")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 8, 5, 5)
        layout.setSpacing(3)

        # TODO: 트리거 상세 위젯 임베드
        placeholder = QLabel("트리거 상세 정보 영역\n(TriggerDetailWidget 예정)")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder)

        group.setLayout(layout)
        return group

    def _create_test_result_area(self) -> QGroupBox:
        """6: 작동 마커 차트 + 작동 기록 영역 - Legacy UI 복사"""
        group = QGroupBox("📊 시뮬레이션 결과")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 8, 5, 5)
        layout.setSpacing(3)

        # TODO: 시뮬레이션 결과 위젯 임베드
        placeholder = QLabel("시뮬레이션 결과 영역\n(SimulationResultWidget 예정)")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder)

        group.setLayout(layout)
        return group

    # ITriggerBuilderView 인터페이스 구현
    def display_variables(self, variables_dto: TradingVariableListDTO) -> None:
        """변수 목록을 UI에 표시"""
        self._logger.info(f"변수 목록 표시: {variables_dto.total_count}개")
        # TODO: 조건 빌더 영역에 변수 목록 표시

    def show_variable_details(self, details_dto: TradingVariableDetailDTO) -> None:
        """변수 상세 정보를 UI에 표시"""
        self._logger.info(f"변수 상세 정보 표시: {details_dto.variable_id}")
        # TODO: 트리거 상세 영역에 변수 정보 표시

    def update_compatibility_status(self, is_compatible: bool, message: str) -> None:
        """호환성 검증 결과를 UI에 표시"""
        self._logger.info(f"호환성 상태 업데이트: {is_compatible}, {message}")
        # TODO: 조건 빌더 영역에 호환성 상태 표시

    def show_error_message(self, message: str) -> None:
        """에러 메시지를 UI에 표시"""
        QMessageBox.critical(self, "오류", message)
        self._logger.error(f"에러 메시지 표시: {message}")

    def show_success_message(self, message: str) -> None:
        """성공 메시지를 UI에 표시"""
        QMessageBox.information(self, "성공", message)
        self._logger.info(f"성공 메시지 표시: {message}")

    def enable_simulation_controls(self, enabled: bool) -> None:
        """시뮬레이션 컨트롤 활성화/비활성화"""
        self._logger.info(f"시뮬레이션 컨트롤 상태: {enabled}")
        # TODO: 시뮬레이션 영역의 버튼들 활성화/비활성화

    def update_simulation_progress(self, progress: int) -> None:
        """시뮬레이션 진행률 업데이트"""
        self._logger.info(f"시뮬레이션 진행률: {progress}%")
        # TODO: 시뮬레이션 영역에 진행률 표시
