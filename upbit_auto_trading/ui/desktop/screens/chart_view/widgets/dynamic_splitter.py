"""
동적 스플리터 위젯

차트뷰어의 3열 레이아웃(1:4:2 비율)을 위한 동적 스플리터입니다.
창 크기 변경시 비율 유지 및 최소 크기 제한을 지원합니다.
"""

from typing import List, Optional
from PyQt6.QtWidgets import QSplitter, QWidget
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from upbit_auto_trading.infrastructure.logging import create_component_logger


class DynamicSplitter(QSplitter):
    """
    동적 3열 스플리터 (1:4:2 비율)

    차트뷰어의 기본 레이아웃을 제공합니다:
    - 좌측: 코인 리스트 (1 비율)
    - 중앙: 차트 영역 (4 비율)
    - 우측: 호가창 (2 비율)
    """

    # 시그널 정의
    layout_changed = pyqtSignal()  # 레이아웃 변경 시그널

    def __init__(self, parent: Optional[QWidget] = None):
        """동적 스플리터 초기화"""
        super().__init__(Qt.Orientation.Horizontal, parent)

        self._logger = create_component_logger("DynamicSplitter")

        # 기본 비율 설정 (1:4:2)
        self._default_ratios = [1, 4, 2]
        self._min_widths = [200, 400, 200]  # 각 패널의 최소 너비

        # 스플리터 설정
        self._setup_splitter()

        self._logger.info("🎯 동적 3열 스플리터 초기화 완료 (1:4:2 비율)")

    def _setup_splitter(self) -> None:
        """스플리터 기본 설정"""
        # 핸들 스타일 설정
        self.setHandleWidth(3)
        self.setChildrenCollapsible(False)  # 패널 접기 방지

        # 스플리터 이동 시그널 연결
        self.splitterMoved.connect(self._on_splitter_moved)

        self._logger.debug("스플리터 기본 설정 완료")

    def add_panel(self, widget: QWidget, ratio: int) -> None:
        """패널 추가"""
        if not widget:
            self._logger.warning("빈 위젯은 추가할 수 없습니다")
            return

        index = self.count()
        self.addWidget(widget)

        # 최소 크기 설정
        if index < len(self._min_widths):
            widget.setMinimumWidth(self._min_widths[index])

        self._logger.debug(f"패널 추가됨: 인덱스 {index}, 비율 {ratio}")

    def setup_layout(self, widgets: List[QWidget]) -> None:
        """3열 레이아웃 설정"""
        if len(widgets) != 3:
            self._logger.error(f"정확히 3개의 위젯이 필요합니다. 현재: {len(widgets)}개")
            return

        # 기존 위젯 제거
        self._clear_widgets()

        # 새 위젯 추가
        for i, widget in enumerate(widgets):
            self.add_panel(widget, self._default_ratios[i])

        # 초기 비율 적용
        self._apply_ratios()

        self._logger.info("✅ 3열 레이아웃 설정 완료")

    def _clear_widgets(self) -> None:
        """기존 위젯들 제거"""
        while self.count() > 0:
            widget = self.widget(0)
            widget.setParent(None)

    def _apply_ratios(self) -> None:
        """기본 비율 적용"""
        if self.count() != 3:
            return

        total_width = self.width()
        if total_width <= 0:
            # 초기화 시점에는 QTimer로 지연 적용
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self._apply_ratios)
            return

        # 최소 너비 고려한 비율 계산
        total_min_width = sum(self._min_widths)
        available_width = max(total_width - total_min_width, 0)
        total_ratio = sum(self._default_ratios)

        sizes = []
        for i in range(3):
            ratio_width = (available_width * self._default_ratios[i]) // total_ratio
            final_width = self._min_widths[i] + ratio_width
            sizes.append(final_width)

        self.setSizes(sizes)
        self._logger.debug(f"비율 적용: {sizes}")

    def _on_splitter_moved(self, pos: int, index: int) -> None:
        """스플리터 이동 시 처리"""
        self._logger.debug(f"스플리터 이동: 위치 {pos}, 인덱스 {index}")
        self.layout_changed.emit()

    def resizeEvent(self, event) -> None:
        """창 크기 변경 시 비율 유지"""
        super().resizeEvent(event)

        if self.count() == 3:
            # 비율 유지하며 리사이즈
            self._maintain_ratios_on_resize()

    def _maintain_ratios_on_resize(self) -> None:
        """리사이즈 시 비율 유지"""
        current_sizes = self.sizes()
        total_width = sum(current_sizes)

        if total_width <= 0:
            return

        # 현재 비율 계산
        current_ratios = [size / total_width for size in current_sizes]

        # 새 크기 계산
        new_total = self.width()
        new_sizes = []

        for i, ratio in enumerate(current_ratios):
            new_size = max(int(new_total * ratio), self._min_widths[i])
            new_sizes.append(new_size)

        self.setSizes(new_sizes)

    def reset_to_default_ratios(self) -> None:
        """기본 비율로 재설정"""
        self._apply_ratios()
        self._logger.info("기본 비율(1:4:2)로 재설정됨")

    def get_current_ratios(self) -> List[float]:
        """현재 비율 반환"""
        sizes = self.sizes()
        total = sum(sizes)

        if total == 0:
            return self._default_ratios.copy()

        return [size / total for size in sizes]

    def save_layout_state(self) -> dict:
        """레이아웃 상태 저장"""
        return {
            'sizes': self.sizes(),
            'ratios': self.get_current_ratios(),
            'width': self.width()
        }

    def restore_layout_state(self, state: dict) -> None:
        """레이아웃 상태 복원"""
        if 'sizes' in state and len(state['sizes']) == 3:
            self.setSizes(state['sizes'])
            self._logger.info("레이아웃 상태 복원됨")
        else:
            self._logger.warning("잘못된 레이아웃 상태 - 기본값 사용")
            self.reset_to_default_ratios()

    def sizeHint(self) -> QSize:
        """권장 크기 반환"""
        return QSize(1200, 600)  # 차트뷰어에 적합한 기본 크기

    def minimumSizeHint(self) -> QSize:
        """최소 크기 반환"""
        min_width = sum(self._min_widths)
        return QSize(min_width, 400)
