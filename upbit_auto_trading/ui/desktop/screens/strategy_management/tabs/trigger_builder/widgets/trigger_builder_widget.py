"""
트리거 빌더 메인 Widget - MVP View 구현체
Legacy UI 레이아웃을 100% 그대로 복사하여 구현
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QGroupBox,
    QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.dto.trigger_builder.trading_variable_dto import (
    TradingVariableListDTO,
    TradingVariableDetailDTO
)


class TriggerBuilderWidget(QWidget):
    """트리거 빌더 메인 Widget - MVP View 구현체

    ITriggerBuilderView 인터페이스를 컴포지션으로 구현하여 메타클래스 충돌 방지
    """

    # 시그널 정의
    variable_selected = pyqtSignal(str)  # 변수 선택
    external_variable_selected = pyqtSignal(str)  # 외부 변수 선택
    trigger_selected = pyqtSignal(object, int)  # 트리거 선택
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
        """1+4: 조건 빌더 영역 - 실제 ConditionBuilderWidget 사용"""
        from ....shared.components.condition_builder.condition_builder_widget import ConditionBuilderWidget

        group = QGroupBox("🎯 조건 빌더")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 8, 5, 5)
        layout.setSpacing(3)

        # 실제 ConditionBuilderWidget 사용
        self.condition_builder = ConditionBuilderWidget()

        # 시그널 연결
        self.condition_builder.variable_selected.connect(
            lambda var: self.variable_selected.emit(var)
        )
        # 외부 변수 선택 시그널 - 별도 시그널로 처리
        self.condition_builder.external_variable_selected.connect(
            lambda var: self.external_variable_selected.emit(var)
        )

        layout.addWidget(self.condition_builder)
        group.setLayout(layout)
        return group

    def _create_trigger_list_area(self) -> QGroupBox:
        """2: 등록된 트리거 리스트 영역 - Legacy UI 복사"""
        group = QGroupBox("📝 등록된 트리거")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 8, 5, 5)
        layout.setSpacing(3)

        # 트리거 리스트 위젯 사용
        try:
            from .trigger_list_widget import TriggerListWidget
            self.trigger_list = TriggerListWidget()

            # 시그널 연결
            self.trigger_list.trigger_selected.connect(
                lambda item, column: self._on_trigger_selected(item, column)
            )

            layout.addWidget(self.trigger_list)
            self._logger.debug("트리거 리스트 위젯 생성 완료")

        except ImportError as e:
            self._logger.error(f"트리거 리스트 위젯 임포트 실패: {e}")
            # 임시 플레이스홀더
            placeholder = QLabel("트리거 리스트 (로딩 실패)")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("background-color: #fff2cc; border: 1px dashed #d6b656; padding: 20px;")
            layout.addWidget(placeholder)

        group.setLayout(layout)
        return group

        group.setLayout(layout)
        return group

    def _create_simulation_area(self) -> QGroupBox:
        """3: 케이스 시뮬레이션 영역 - Legacy UI 복사"""
        group = QGroupBox("🧪 시뮬레이션 제어")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 8, 5, 5)
        layout.setSpacing(3)

        # 시뮬레이션 컨트롤 위젯 사용
        try:
            from .simulation_control_widget import SimulationControlWidget
            self.simulation_control = SimulationControlWidget()

            # 시그널 연결
            self.simulation_control.simulation_requested.connect(
                lambda scenario: self._on_simulation_requested(scenario)
            )

            layout.addWidget(self.simulation_control)
            self._logger.debug("시뮬레이션 컨트롤 위젯 생성 완료")

        except ImportError as e:
            self._logger.error(f"시뮬레이션 컨트롤 위젯 임포트 실패: {e}")
            # 임시 플레이스홀더
            placeholder = QLabel("시뮬레이션 컨트롤 (로딩 실패)")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("background-color: #fff2cc; border: 1px dashed #d6b656; padding: 20px;")
            layout.addWidget(placeholder)

        group.setLayout(layout)
        return group

    def _create_trigger_detail_area(self) -> QGroupBox:
        """5: 선택한 트리거 상세 정보 영역 - Legacy UI 복사"""
        group = QGroupBox("🔍 트리거 상세")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 8, 5, 5)
        layout.setSpacing(3)

        # 트리거 상세 위젯 사용
        try:
            from .trigger_detail_widget import TriggerDetailWidget
            self.trigger_detail = TriggerDetailWidget()
            layout.addWidget(self.trigger_detail)
            self._logger.debug("트리거 상세 위젯 생성 완료")

        except ImportError as e:
            self._logger.error(f"트리거 상세 위젯 임포트 실패: {e}")
            # 임시 플레이스홀더
            placeholder = QLabel("트리거 상세 정보 (로딩 실패)")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("background-color: #f0f0f0; border: 1px dashed #ccc; padding: 20px;")
            layout.addWidget(placeholder)

        group.setLayout(layout)
        return group

    def _create_test_result_area(self) -> QGroupBox:
        """6: 작동 마커 차트 + 작동 기록 영역 - Legacy UI 복사"""
        group = QGroupBox("📊 시뮬레이션 결과")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 8, 5, 5)
        layout.setSpacing(3)

        # 시뮬레이션 결과 위젯 사용
        try:
            from .simulation_result_widget import SimulationResultWidget
            self.simulation_result = SimulationResultWidget()
            layout.addWidget(self.simulation_result)
            self._logger.debug("시뮬레이션 결과 위젯 생성 완료")

        except ImportError as e:
            self._logger.error(f"시뮬레이션 결과 위젯 임포트 실패: {e}")
            # 임시 플레이스홀더
            placeholder = QLabel("시뮬레이션 결과 (로딩 실패)")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("background-color: #f0f0f0; border: 1px dashed #ccc; padding: 20px;")
            layout.addWidget(placeholder)

        group.setLayout(layout)
        return group

    # ITriggerBuilderView 인터페이스 구현
    def display_variables(self, variables_dto: TradingVariableListDTO) -> None:
        """변수 목록을 UI에 표시 - ConditionBuilder에 전달"""
        self._logger.info(f"변수 목록 표시: {variables_dto.total_count}개")
        # ConditionBuilder에 변수 목록 전달
        if hasattr(self, 'condition_builder'):
            self.condition_builder.display_variables(variables_dto)

    def show_variable_details(self, details_dto: TradingVariableDetailDTO) -> None:
        """변수 상세 정보를 UI에 표시 - ConditionBuilder에 전달"""
        self._logger.info(f"변수 상세 정보 표시: {details_dto.variable_id}")
        # ConditionBuilder에 변수 상세 정보 전달
        if hasattr(self, 'condition_builder'):
            self.condition_builder.show_variable_details(details_dto)

    def show_external_variable_details(self, details_dto: TradingVariableDetailDTO) -> None:
        """외부 변수 상세 정보를 UI에 표시 - ConditionBuilder에 전달"""
        self._logger.info(f"외부 변수 상세 정보 표시: {details_dto.variable_id}")
        # ConditionBuilder에 외부 변수 상세 정보 전달
        if hasattr(self, 'condition_builder'):
            self.condition_builder.show_external_variable_details(details_dto)

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

    def run_simulation(self, scenario_type: str) -> None:
        """시뮬레이션 실행"""
        self._logger.info(f"시뮬레이션 실행: {scenario_type}")
        # TODO: 시뮬레이션 결과 위젯에 실행 요청
        # if hasattr(self, 'simulation_result'):
        #     self.simulation_result.start_simulation(scenario_type)

    def update_data_source(self, source_type: str) -> None:
        """데이터 소스 변경"""
        self._logger.info(f"데이터 소스 변경: {source_type}")
        # TODO: 데이터 소스 변경 처리

    def _on_trigger_selected(self, item, column):
        """트리거 선택 시 처리"""
        if item and hasattr(self, 'trigger_detail'):
            # 아이템에서 트리거 데이터 추출
            trigger_data = item.data(0, Qt.ItemDataRole.UserRole)
            if not trigger_data:
                # UserRole 데이터가 없으면 텍스트로 구성
                trigger_data = {
                    "name": item.text(0),
                    "variable": item.text(1),
                    "condition": item.text(2)
                }

            # 트리거 상세 정보 업데이트
            self.trigger_detail.update_trigger_detail(trigger_data)
            self._logger.debug(f"트리거 선택됨: {trigger_data.get('name', 'Unknown')}")

        # 외부로 시그널 전파
        self.trigger_selected.emit(item, column)

    def _on_simulation_requested(self, scenario_type):
        """시뮬레이션 요청 처리"""
        if hasattr(self, 'simulation_result'):
            # 시뮬레이션 결과 위젯에 결과 표시
            self.simulation_result.update_simulation_result(scenario_type)
            self._logger.info(f"시뮬레이션 실행: {scenario_type}")
        else:
            self._logger.warning("시뮬레이션 결과 위젯이 없습니다")

        # 외부로 시그널 전파 (기존 방식 유지)
        if scenario_type in ["full_test", "start"]:
            self.simulation_start_requested.emit()
        else:
            # 새로운 시나리오별 시그널 (추후 확장 가능)
            self._logger.debug(f"시나리오별 시뮬레이션: {scenario_type}")
