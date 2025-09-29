"""
Quick Environment Buttons Widget
===============================

환경 프로파일 빠른 전환을 위한 버튼 위젯
좌우 분할 레이아웃의 좌측 상단에 위치하여 3개 기본 환경을 빠르게 전환

Features:
- Development, Testing, Production 3개 환경 버튼
- 환경별 색상 테마 구분 (초록, 노랑, 빨강)
- 현재 활성 환경 시각적 표시
- 버튼 호버 효과 및 클릭 피드백
- Infrastructure 로깅 통합
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton
)
from PyQt6.QtCore import pyqtSignal

# Application Layer - Infrastructure 의존성 격리 (Phase 2 수정)

logger = create_component_logger("QuickEnvironmentButtons")

class QuickEnvironmentButtons(QWidget):
    """
    퀵 환경 전환 버튼 위젯

    3개의 기본 환경(개발, 테스트, 운영)을 빠르게 전환할 수 있는
    버튼 그룹을 제공합니다. 각 환경은 고유한 색상으로 구분됩니다.
    """

    # 시그널 정의
    environment_selected = pyqtSignal(str)  # 환경 키 (development, testing, production)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("QuickEnvironmentButtons")

        logger.info("🔘 퀵 환경 버튼 위젯 초기화 시작")

        # 상태 관리
        self._current_environment = ""
        self._environment_buttons: Dict[str, QPushButton] = {}

        # 환경 정보 정의
        self._environment_config = {
            "development": {
                "display_name": "개발",
                "description": "개발 환경",
                "color": "#4CAF50",  # 초록색
                "icon": "🛠️"
            },
            "testing": {
                "display_name": "테스트",
                "description": "테스트 환경",
                "color": "#FF9800",  # 주황색
                "icon": "🧪"
            },
            "production": {
                "display_name": "운영",
                "description": "운영 환경",
                "color": "#F44336",  # 빨간색
                "icon": "🚀"
            }
        }

        # UI 구성
        self._setup_ui()
        self._create_environment_buttons()

        logger.info("✅ 퀵 환경 버튼 위젯 초기화 완료")

    def _setup_ui(self) -> None:
        """UI 기본 구조 설정"""
        self._main_layout = QHBoxLayout(self)
        self._main_layout.setContentsMargins(5, 5, 5, 5)
        self._main_layout.setSpacing(8)

    def _create_environment_buttons(self) -> None:
        """환경 버튼들 생성 - 테스트에서 성공한 방법 적용"""
        for env_key, env_config in self._environment_config.items():
            button = self._create_environment_button(env_key, env_config)
            self._environment_buttons[env_key] = button
            # 테스트에서 성공한 방법: stretch 파라미터 사용
            self._main_layout.addWidget(button, 1)

    def _create_environment_button(self, env_key: str, env_config: Dict[str, Any]) -> QPushButton:
        """개별 환경 버튼 생성 - 명시적 폭 설정으로 늘어남 강제"""
        button = QPushButton()
        button.setObjectName(f"quick_env_button_{env_key}")

        # 테스트에서 효과적이었던 설정들 적용
        button.setAutoDefault(False)  # autoDefault 해제
        from PyQt6.QtWidgets import QSizePolicy
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # 명시적 폭 설정 - 🔥 디버깅 결과: setMaximumWidth() 제거!
        button.setMinimumWidth(60)   # 최소 폭 설정
        # button.setMaximumWidth(600) 주석처리 - 이것이 stretch를 방해하는 주범!

        # 버튼 텍스트 설정
        icon = env_config["icon"]
        display_name = env_config["display_name"]
        button.setText(f"{icon} {display_name}")

        # 툴팁 설정
        button.setToolTip(f"{env_config['description']} 환경으로 전환")

        # 클릭 이벤트 연결
        button.clicked.connect(lambda checked, key=env_key: self._on_environment_selected(key))

        # 초기 스타일 적용
        self._apply_button_style(button, env_config, is_active=False)

        return button

    def _apply_button_style(self, button: QPushButton, env_config: Dict[str, Any], is_active: bool) -> None:
        """버튼 스타일 적용 - 완전 기본 상태 (크기 설정 없음)"""
        base_color = env_config["color"]

        if is_active:
            # 활성 상태 스타일 - 🧪 실험2: 전역 CSS max-width 명시적 오버라이드
            button.setStyleSheet(f"""
                QPushButton#{button.objectName()} {{
                    background-color: {base_color};
                    color: white;
                    border: 2px solid {self._darken_color(base_color, 0.3)};
                    border-radius: 4px;
                    font-weight: bold;
                    padding: 6px 12px;
                    max-width: 300px;
                    min-width: 60px;
                }}
                QPushButton#{button.objectName()}:hover {{
                    background-color: {self._darken_color(base_color, 0.1)};
                }}
                QPushButton#{button.objectName()}:pressed {{
                    background-color: {self._darken_color(base_color, 0.2)};
                }}
            """)
        else:
            # 비활성 상태 스타일 - 🧪 실험2: 전역 CSS max-width 명시적 오버라이드
            light_color = self._lighten_color(base_color, 0.8)
            button.setStyleSheet(f"""
                QPushButton#{button.objectName()} {{
                    background-color: {light_color};
                    color: {base_color};
                    border: 1px solid {base_color};
                    border-radius: 4px;
                    font-weight: normal;
                    padding: 6px 12px;
                    max-width: 300;
                    min-width: 60px;
                }}
                QPushButton#{button.objectName()}:hover {{
                    background-color: {self._lighten_color(base_color, 0.7)};
                    border: 2px solid {base_color};
                }}
                QPushButton#{button.objectName()}:pressed {{
                    background-color: {self._lighten_color(base_color, 0.6)};
                }}
            """)

    def _darken_color(self, color: str, factor: float = 0.2) -> str:
        """색상을 어둡게 만들기"""
        # 간단한 색상 어둡게 처리
        if color.startswith("#"):
            hex_color = color[1:]
            if len(hex_color) == 6:
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)

                r = max(0, int(r * (1 - factor)))
                g = max(0, int(g * (1 - factor)))
                b = max(0, int(b * (1 - factor)))

                return f"#{r:02x}{g:02x}{b:02x}"

        return color  # 처리 실패 시 원본 반환

    def _lighten_color(self, color: str, factor: float = 0.2) -> str:
        """색상을 밝게 만들기"""
        # 간단한 색상 밝게 처리
        if color.startswith("#"):
            hex_color = color[1:]
            if len(hex_color) == 6:
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)

                r = min(255, int(r + (255 - r) * factor))
                g = min(255, int(g + (255 - g) * factor))
                b = min(255, int(b + (255 - b) * factor))

                return f"#{r:02x}{g:02x}{b:02x}"

        return color  # 처리 실패 시 원본 반환

    def _on_environment_selected(self, env_key: str) -> None:
        """환경 선택 이벤트 처리 - 일시적 액션으로 변경"""
        logger.info(f"🔘 퀵 환경 액션 실행: {env_key}")

        # 🔥 UX 개선: 버튼 일시적 강조 효과
        button = self._environment_buttons.get(env_key)
        if button:
            env_config = self._environment_config[env_key]
            # 잠시 활성화 스타일 적용
            self._apply_button_style(button, env_config, is_active=True)

            # QTimer를 사용하여 짧은 시간 후 원래 상태로 복원
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(200, lambda: self._apply_button_style(button, env_config, is_active=False))

        # 시그널 발송 (상위 컴포넌트에서 콤보박스 업데이트 처리)
        self.environment_selected.emit(env_key)

    def _update_active_environment(self, env_key: str) -> None:
        """활성 환경 표시 업데이트"""
        old_environment = self._current_environment
        self._current_environment = env_key

        # 이전 활성 버튼 비활성화
        if old_environment and old_environment in self._environment_buttons:
            old_button = self._environment_buttons[old_environment]
            old_config = self._environment_config[old_environment]
            self._apply_button_style(old_button, old_config, is_active=False)

        # 새 활성 버튼 활성화
        if env_key in self._environment_buttons:
            new_button = self._environment_buttons[env_key]
            new_config = self._environment_config[env_key]
            self._apply_button_style(new_button, new_config, is_active=True)

        logger.debug(f"활성 환경 변경: {old_environment} → {env_key}")

    def set_active_environment(self, env_key: str) -> None:
        """
        외부에서 활성 환경 설정

        Args:
            env_key: 환경 키 (development, testing, production)
        """
        if env_key in self._environment_config:
            self._update_active_environment(env_key)
            logger.info(f"외부에서 활성 환경 설정: {env_key}")
        else:
            logger.warning(f"알 수 없는 환경 키: {env_key}")

    def get_active_environment(self) -> str:
        """현재 활성 환경 반환"""
        return self._current_environment

    def get_available_environments(self) -> Dict[str, Dict[str, Any]]:
        """사용 가능한 환경 목록 반환"""
        return self._environment_config.copy()

    def set_environment_enabled(self, env_key: str, enabled: bool) -> None:
        """특정 환경 버튼 활성화/비활성화"""
        if env_key in self._environment_buttons:
            button = self._environment_buttons[env_key]
            button.setEnabled(enabled)

            if not enabled and env_key == self._current_environment:
                # 비활성화된 환경이 현재 활성 환경이면 초기화
                self._current_environment = ""

            logger.debug(f"환경 버튼 상태 변경: {env_key} → {'활성' if enabled else '비활성'}")

    def get_button_info(self) -> Dict[str, Any]:
        """버튼 위젯 정보 반환 (디버깅용)"""
        return {
            'current_environment': self._current_environment,
            'total_buttons': len(self._environment_buttons),
            'button_states': {
                env_key: button.isEnabled()
                for env_key, button in self._environment_buttons.items()
            },
            'environment_config': self._environment_config
        }
