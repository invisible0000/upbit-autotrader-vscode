"""
데이터 소스 선택 UI 위젯
트리거 빌더 미리보기용 임시 선택기 (향후 단일 소스로 통일 예정)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QRadioButton, QButtonGroup, QGroupBox, QFrame)
from PyQt6.QtCore import pyqtSignal
from typing import Dict, Optional
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("DataSourceSelector")


class DataSourceSelectorWidget(QWidget):
    """
    데이터 소스 선택 위젯
    현재: 4개 선택지 (내장/실제DB/합성/폴백)
    미래: 단일 최적화 소스로 통일하여 이 컴포넌트 제거 예정
    """    # 데이터 소스 변경 시그널
    source_changed = pyqtSignal(str)  # 선택된 소스 타입

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_source: Optional[str] = None
        self.manager = None
        logger.debug("DataSourceSelectorWidget 초기화 시작")
        self.init_ui()
        self.load_available_sources()

    def init_ui(self):
        """UI 초기화 - 매우 컴팩트한 버전 (기존 스타일 유지)"""
        layout = QVBoxLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(2, 2, 2, 2)

        # 데이터 소스 선택 그룹
        self.source_group = QGroupBox("데이터 소스")
        self.source_group.setStyleSheet("font-size: 12px;")
        source_layout = QVBoxLayout(self.source_group)
        source_layout.setSpacing(2)
        source_layout.setContentsMargins(4, 8, 4, 4)

        # 라디오 버튼 그룹
        self.button_group = QButtonGroup()
        self.source_buttons: Dict[str, QRadioButton] = {}

        # 버튼들이 추가될 컨테이너
        self.buttons_container = QWidget()
        self.buttons_layout = QVBoxLayout(self.buttons_container)
        self.buttons_layout.setSpacing(1)
        source_layout.addWidget(self.buttons_container)

        layout.addWidget(self.source_group)
        logger.debug("UI 초기화 완료")

    def load_available_sources(self):
        """사용 가능한 데이터 소스 로드 - 간단한 4개 선택지"""
        logger.debug("데이터 소스 로드 시작")

        try:
            # 기존 버튼들 제거
            for button in self.source_buttons.values():
                button.deleteLater()
            self.source_buttons.clear()

            # 4개 기본 데이터 소스 정의 (트리거 빌더 미리보기용)
            # 향후 단일 최적화 소스로 통일되어 이 선택기는 제거될 예정
            data_sources = {
                'embedded': {
                    'name': '내장 최적화',
                    'description': '시나리오별 최적화된 내장 데이터셋',
                    'available': True,
                    'recommended': True
                },
                'real_db': {
                    'name': '실제 DB',
                    'description': '실제 시장 데이터 (시나리오별 세그먼테이션)',
                    'available': self._check_real_db_availability(),
                    'recommended': False
                },
                'synthetic': {
                    'name': '합성 현실적',
                    'description': '합성된 현실적 시장 데이터',
                    'available': True,
                    'recommended': False
                },
                'fallback': {
                    'name': '단순 폴백',
                    'description': '단순 생성된 폴백 데이터',
                    'available': True,
                    'recommended': False
                }
            }

            # 사용 가능한 소스만 필터링
            available_sources = {k: v for k, v in data_sources.items() if v['available']}

            if not available_sources:
                self._show_no_sources_message()
                return

            # 각 소스별 라디오 버튼 생성
            for source_key, source_info in available_sources.items():
                self.create_source_button(source_key, source_info)

            # 기본값 설정 (내장 최적화 우선)
            if 'embedded' in available_sources:
                self.source_buttons['embedded'].setChecked(True)
                self.current_source = 'embedded'
            elif available_sources:
                first_source = next(iter(available_sources))
                self.source_buttons[first_source].setChecked(True)
                self.current_source = first_source

            logger.info(f"데이터 소스 로드 완료: {len(available_sources)}개")

        except Exception as e:
            logger.error(f"데이터 소스 로드 실패: {e}")
            self._show_error_message(f"데이터 소스 로드 실패: {e}")

    def _check_real_db_availability(self) -> bool:
        """실제 DB 가용성 확인"""
        try:
            import os
            # 간단한 파일 존재 여부만 확인
            db_path = os.path.join(
                os.path.dirname(__file__),
                "..", "..", "..", "..", "..",
                "data", "market_data.sqlite3"
            )
            return os.path.exists(db_path)
        except Exception:
            return False

    def create_source_button(self, source_key: str, source_info: dict):
        """개별 소스용 라디오 버튼 생성 - 기존 스타일 유지"""
        # 간단한 라디오 버튼 컨테이너
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                border: 1px solid #e0e0e0;
                border-radius: 3px;
                margin: 0px;
                padding: 2px;
            }
            QFrame:hover {
                border-color: #4a90e2;
            }
        """)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        # 라디오 버튼
        radio_button = QRadioButton(source_info["name"])
        radio_button.setStyleSheet("font-size: 12px;")
        layout.addWidget(radio_button)

        # 추천 표시
        if source_info.get("recommended", False):
            recommended_label = QLabel("🏆")
            recommended_label.setStyleSheet("font-size: 8px;")
            layout.addWidget(recommended_label)

        layout.addStretch()

        # 이벤트 연결
        radio_button.toggled.connect(
            lambda checked, key=source_key: self.on_source_selected(checked, key)
        )

        # 버튼 그룹에 추가
        self.button_group.addButton(radio_button)
        self.source_buttons[source_key] = radio_button

        # 레이아웃에 추가
        self.buttons_layout.addWidget(container)

    def on_source_selected(self, checked: bool, source_key: str):
        """데이터 소스 선택시 호출 - 자동 적용"""
        if checked:
            self.current_source = source_key
            logger.info(f"데이터 소스 선택됨: {source_key}")

            # 시그널 발생
            self.source_changed.emit(source_key)

    def get_current_source(self) -> str:
        """현재 선택된 데이터 소스 반환"""
        return self.current_source or ""

    def set_source(self, source_key: str) -> bool:
        """프로그래밍 방식으로 데이터 소스 설정"""
        if source_key in self.source_buttons:
            self.source_buttons[source_key].setChecked(True)
            self.current_source = source_key
            logger.debug(f"데이터 소스 설정됨: {source_key}")
            return True
        else:
            logger.warning(f"존재하지 않는 데이터 소스: {source_key}")
            return False

    def _show_no_sources_message(self):
        """사용 가능한 소스가 없을 때 메시지 표시"""
        no_source_label = QLabel("❌ 사용 가능한 데이터 소스가 없습니다.")
        no_source_label.setStyleSheet("color: red; font-weight: bold;")
        self.buttons_layout.addWidget(no_source_label)

    def _show_error_message(self, message: str):
        """에러 메시지 표시"""
        error_label = QLabel(f"❌ {message}")
        error_label.setStyleSheet("color: red;")
        self.buttons_layout.addWidget(error_label)


def create_data_source_selector(parent=None) -> DataSourceSelectorWidget:
    """
    데이터 소스 선택기 팩토리 함수
    트리거 빌더 미리보기용 임시 컴포넌트
    """
    logger.debug("DataSourceSelectorWidget 생성")
    return DataSourceSelectorWidget(parent)
