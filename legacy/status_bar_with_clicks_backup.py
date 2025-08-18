"""
상태 바 위젯 모듈

통합된 StatusBar - API 상태, DB 상태, 시계를 모두 포함하는 단일 위젯
테마 전환을 지원하며 전역 스타일 시스템과 연동됩니다.
"""
from PyQt6.QtWidgets import QStatusBar, QLabel
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from datetime import datetime
from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.monitoring.simple_failure_monitor import (
    get_api_statistics, is_api_healthy, GlobalAPIMonitor
)
from upbit_auto_trading.infrastructure.services.websocket_status_service import (
    websocket_status_service
)


class ClickableStatusLabel(QLabel):
    """클릭 가능한 상태 레이블"""

    clicked = pyqtSignal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def mousePressEvent(self, ev):
        if ev and ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(ev)


class StatusBar(QStatusBar):
    """
    통합된 상태 바 위젯

    - 실시간 시계 표시
    - 클릭 가능한 API 상태 (새로고침 기능 포함)
    - DB 연결 상태
    - 깔끔한 통합 UI
    """

    # API 새로고침 요청 시그널
    api_refresh_requested = pyqtSignal()

    def __init__(self, parent=None, database_health_service=None):
        """
        초기화

        Args:
            parent (QWidget, optional): 부모 위젯
            database_health_service: 데이터베이스 상태 서비스
        """
        super().__init__(parent)

        self.logger = create_component_logger("StatusBar")
        self.database_health_service = database_health_service

        # 오른쪽 끝의 사이즈 그립(하얀 상자) 비활성화
        self.setSizeGripEnabled(False)

        # 테마 노티파이어 연결
        try:
            from upbit_auto_trading.ui.desktop.common.theme_notifier import ThemeNotifier
            self.theme_notifier = ThemeNotifier()
            self.theme_notifier.theme_changed.connect(self._on_theme_changed)
        except Exception as e:
            self.logger.warning(f"테마 노티파이어 연결 실패: {e}")
            self.theme_notifier = None

        # API 상태 관련 속성
        self.api_cooldown_seconds = 10
        self.api_is_enabled = True
        self.api_remaining_time = 0

        # 웹소켓 상태 관련 속성
        self.websocket_is_enabled = True
        self.websocket_cooldown_seconds = 5
        self.websocket_remaining_time = 0

        self._setup_ui()
        self._setup_timers()
        self._setup_auto_status_check()

    def _setup_ui(self):
        """UI 설정"""
        # API 상태 레이블 (읽기 전용 - 실거래 안전성)
        self.api_status_label = QLabel("API: 확인 중...")
        self.api_status_label.setObjectName("api-status")

        # DB 상태 레이블
        self.db_status_label = QLabel("DB: 연결됨")
        self.db_status_label.setObjectName("db-status")

        # 웹소켓 상태 레이블 (읽기 전용 - 실거래 안전성)
        self.websocket_status_label = QLabel("WS: 미연결")
        self.websocket_status_label.setObjectName("websocket-status")

        # 시계 레이블
        self.time_label = QLabel()
        self.time_label.setObjectName("time-display")

        # 상태바에 위젯 추가 (왼쪽부터: API, DB, WS, 시계)
        self.addPermanentWidget(self.api_status_label)
        self.addPermanentWidget(self.db_status_label)
        self.addPermanentWidget(self.websocket_status_label)
        self.addPermanentWidget(self.time_label)

        # 기본 메시지 설정
        self.showMessage("준비됨")

        # 초기 스타일 적용
        self._apply_styles()
        self._update_api_tooltip()
        self._update_websocket_tooltip()

    def _setup_timers(self):
        """타이머 설정"""
        # 시계 업데이트 타이머 (1초마다)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_time)
        self.clock_timer.start(1000)

        # API 쿨다운 타이머
        self.api_cooldown_timer = QTimer(self)
        self.api_cooldown_timer.timeout.connect(self._on_api_cooldown_tick)

        # 초기 시간 설정
        self._update_time()

    def _setup_auto_status_check(self):
        """자동 상태 체크 설정"""
        # DB 상태는 시작할 때 한 번만 체크 (주기적 체크 제거)
        # 다른 기능들에 방해되지 않도록 개선

        # 초기 상태 체크 (500ms 후 - 더 빠른 시작)
        QTimer.singleShot(500, self._perform_initial_status_check)

    def _apply_styles(self):
        """
        테마 대응 스타일 적용
        QSS 파일의 공통 스타일을 사용하여 중복 제거
        """
        # QSS 파일의 스타일을 사용하므로 별도 스타일 설정 불필요
        # objectName이 이미 설정되어 있어 자동으로 스타일 적용됨
        self.logger.debug("StatusBar QSS 스타일 적용 완료")

    def _on_theme_changed(self, is_dark_theme):
        """
        테마 변경 시 호출되는 메서드
        QSS가 자동으로 적용되므로 단순히 로깅만 수행

        Args:
            is_dark_theme (bool): 다크 테마 여부
        """
        theme_name = "다크" if is_dark_theme else "라이트"
        self.logger.info(f"StatusBar 테마 변경됨: {theme_name} 모드")

        # QSS 파일에서 자동으로 스타일이 적용되므로 추가 작업 불필요
        self.update()  # 위젯 업데이트만 수행

    def _update_time(self):
        """시간 업데이트"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)

    def _perform_initial_status_check(self):
        """초기 상태 체크 - 시작할 때 한 번만 실행"""
        self.logger.info("StatusBar 초기 상태 체크 시작")
        self._check_db_status()
        self._check_api_status()
        self._check_websocket_status()

    def _check_db_status(self):
        """DB 상태 체크"""
        try:
            if self.database_health_service:
                # TODO: 실제 DB 상태 체크 로직 구현
                connected = True  # 기본값
                self.set_db_status(connected)
                self.logger.debug(f"DB 상태 체크 완료: {'연결됨' if connected else '연결 끊김'}")
            else:
                self.set_db_status(True)
                self.logger.debug("DB 서비스 없음, 기본값으로 연결됨 표시")
        except Exception as e:
            self.logger.error(f"DB 상태 체크 실패: {e}")
            self.set_db_status(False)

    def _check_api_status(self):
        """API 상태 체크 - SimpleFailureMonitor와 연동"""
        try:
            # 모니터링 시스템에서 현재 상태 확인
            api_healthy = is_api_healthy()
            api_stats = get_api_statistics()

            # 상태가 변경된 경우에만 로깅
            if hasattr(self, '_last_api_healthy') and self._last_api_healthy != api_healthy:
                if api_healthy:
                    self.logger.info(f"API 상태 복구됨 (성공률: {api_stats['success_rate']:.1f}%)")
                else:
                    self.logger.warning(f"API 상태 불량 감지 (연속 실패: {api_stats['consecutive_failures']}회)")

            # 상태 업데이트
            self.set_api_status(api_healthy)
            self._last_api_healthy = api_healthy

            # 통계가 없는 경우 실제 API 테스트 수행
            if api_stats['total_calls'] == 0:
                self._perform_live_api_test()

        except Exception as e:
            self.logger.error(f"API 상태 체크 실패: {e}")
            self.set_api_status(False)

    def _perform_live_api_test(self):
        """실제 API 테스트 수행 (초기 상태 확인용)"""
        try:
            # 실제 업비트 API 서버 상태 확인
            import requests
            from urllib3.exceptions import InsecureRequestWarning
            import urllib3

            # SSL 경고 무시 (간단한 상태 체크용)
            urllib3.disable_warnings(InsecureRequestWarning)

            # 업비트 공개 API로 간단한 연결 테스트
            response = requests.get(
                "https://api.upbit.com/v1/market/all",
                timeout=5,
                verify=False  # SSL 검증 생략하여 빠른 체크
            )

            connected = response.status_code == 200

            # 모니터링 시스템에 결과 기록
            from upbit_auto_trading.infrastructure.monitoring.simple_failure_monitor import (
                mark_api_success, mark_api_failure
            )

            if connected:
                mark_api_success()
                self.logger.debug("API 라이브 테스트 완료: 연결됨")
            else:
                mark_api_failure()
                self.logger.warning(f"API 라이브 테스트 완료: 연결 실패 (HTTP {response.status_code})")

            self.set_api_status(connected)

        except Exception as e:
            from upbit_auto_trading.infrastructure.monitoring.simple_failure_monitor import mark_api_failure
            mark_api_failure()
            self.logger.error(f"API 라이브 테스트 실패: {e}")
            self.set_api_status(False)

    def _on_api_click(self):
        """API 상태 클릭 이벤트 처리"""
        if self.api_is_enabled:
            self.logger.info("사용자가 API 상태 새로고침을 요청했습니다")

            # 확인 중 상태 표시
            self.set_api_status(None)

            # 쿨다운 시작
            self._start_api_cooldown()

            # API 상태 재체크 (1초 후)
            QTimer.singleShot(1000, self._check_api_status)

            # 외부 시그널 발신
            self.api_refresh_requested.emit()

    def _start_api_cooldown(self):
        """API 쿨다운 시작"""
        if not self.api_is_enabled:
            return

        self.api_is_enabled = False
        self.api_remaining_time = self.api_cooldown_seconds

        # 커서 변경
        self.api_status_label.setCursor(QCursor(Qt.CursorShape.ForbiddenCursor))

        # 쿨다운 타이머 시작
        self.api_cooldown_timer.start(1000)

        self._update_api_cooldown_display()
        self.logger.debug(f"API 쿨다운 시작: {self.api_cooldown_seconds}초")

    def _on_api_cooldown_tick(self):
        """API 쿨다운 타이머 틱"""
        self.api_remaining_time -= 1

        if self.api_remaining_time <= 0:
            self._end_api_cooldown()
        else:
            self._update_api_cooldown_display()
            self._update_api_tooltip()

    def _update_api_cooldown_display(self):
        """API 쿨다운 표시 업데이트"""
        if self.api_remaining_time > 0:
            original_text = self.api_status_label.text().split(" (")[0]
            self.api_status_label.setText(f"{original_text} ({self.api_remaining_time}초)")
            # 쿨다운 중에는 기본 스타일 유지

    def _end_api_cooldown(self):
        """API 쿨다운 종료"""
        self.api_cooldown_timer.stop()
        self.api_is_enabled = True
        self.api_remaining_time = 0

        # 텍스트에서 쿨다운 표시 제거
        original_text = self.api_status_label.text().split(" (")[0]
        self.api_status_label.setText(original_text)

        # 커서 복원
        self.api_status_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # 툴팁 업데이트
        self._update_api_tooltip()

        # 스타일 복원
        if "연결됨" in self.api_status_label.text():
            self.set_api_status(True)
        elif "연결 끊김" in self.api_status_label.text():
            self.set_api_status(False)
        else:
            self.set_api_status(None)

        self.logger.debug("API 쿨다운 종료")

    def _on_websocket_click(self):
        """웹소켓 상태 클릭 이벤트 처리"""
        if self.websocket_is_enabled:
            self.logger.info("사용자가 웹소켓 상태 새로고침을 요청했습니다")

            # 확인 중 상태 표시
            self.set_websocket_status(None)

            # 쿨다운 시작
            self._start_websocket_cooldown()

            # 웹소켓 상태 재체크 (1초 후)
            QTimer.singleShot(1000, self._check_websocket_status)

    def _start_websocket_cooldown(self):
        """웹소켓 쿨다운 시작"""
        if not self.websocket_is_enabled:
            return

        self.websocket_is_enabled = False
        self.websocket_remaining_time = self.websocket_cooldown_seconds

        # 커서 변경
        self.websocket_status_label.setCursor(QCursor(Qt.CursorShape.ForbiddenCursor))

        # 쿨다운 타이머 시작 (기존 API 타이머 재활용)
        QTimer.singleShot(self.websocket_cooldown_seconds * 1000, self._end_websocket_cooldown)

        self.logger.debug(f"웹소켓 쿨다운 시작: {self.websocket_cooldown_seconds}초")

    def _end_websocket_cooldown(self):
        """웹소켓 쿨다운 종료"""
        self.websocket_is_enabled = True
        self.websocket_remaining_time = 0

        # 커서 복원
        self.websocket_status_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.logger.debug("웹소켓 쿨다운 종료")

    def _check_websocket_status(self):
        """웹소켓 상태 체크 - 가볍게 구현"""
        try:
            # 웹소켓 상태 서비스에서 전체 상태 조회
            connected = websocket_status_service.get_overall_status()

            self.set_websocket_status(connected)
            self.logger.debug(f"웹소켓 상태 체크 완료: {'연결됨' if connected else '미연결'}")

        except Exception as e:
            self.logger.error(f"웹소켓 상태 체크 실패: {e}")
            self.set_websocket_status(False)

    def _update_api_tooltip(self):
        """API 툴팁 업데이트 - 모니터링 통계 포함"""
        if self.api_is_enabled:
            # 모니터링 통계 가져오기
            try:
                stats = get_api_statistics()
                if stats['total_calls'] > 0:
                    tooltip_text = (
                        "클릭하여 API 연결 상태를 새로고침합니다.\n"
                        "• 실시간 연결 테스트 수행\n"
                        "• 업비트 API 서버 상태 확인\n\n"
                        f"📊 API 모니터링 통계:\n"
                        f"• 총 호출: {stats['total_calls']}회\n"
                        f"• 성공률: {stats['success_rate']:.1f}%\n"
                        f"• 연속 실패: {stats['consecutive_failures']}회\n"
                        f"• 건강 상태: {'양호' if is_api_healthy() else '문제 있음'}"
                    )
                else:
                    tooltip_text = (
                        "클릭하여 API 연결 상태를 새로고침합니다.\n"
                        "• 실시간 연결 테스트 수행\n"
                        "• 업비트 API 서버 상태 확인\n\n"
                        "📊 API 모니터링: 아직 호출 기록이 없습니다"
                    )
            except Exception as e:
                self.logger.debug(f"모니터링 통계 조회 실패: {e}")
                tooltip_text = (
                    "클릭하여 API 연결 상태를 새로고침합니다.\n"
                    "• 실시간 연결 테스트 수행\n"
                    "• 업비트 API 서버 상태 확인"
                )

            self.api_status_label.setToolTip(tooltip_text)
        else:
            self.api_status_label.setToolTip(
                f"쿨다운 중입니다. {self.api_remaining_time}초 후에 다시 시도하세요.\n"
                "너무 빈번한 API 호출을 방지하기 위한 대기 시간입니다."
            )

    def _update_websocket_tooltip(self):
        """웹소켓 툴팁 업데이트 - 상태 서비스 연동"""
        try:
            if self.websocket_is_enabled:
                # 웹소켓 상태 서비스에서 상세 정보 가져오기
                status_summary = websocket_status_service.get_status_summary()
                detailed_status = websocket_status_service.get_detailed_status()

                if detailed_status:
                    tooltip_lines = [
                        "클릭하여 웹소켓 연결 상태를 새로고침합니다.",
                        "• 실시간 시세 데이터 연결 확인",
                        "• 업비트 WebSocket 서버 상태 확인",
                        "",
                        f"📡 웹소켓 상태: {status_summary}",
                        ""
                    ]

                    # 각 클라이언트별 상세 상태
                    for client_name, status in detailed_status.items():
                        status_icon = "🟢" if status['is_connected'] else "🔴"
                        tooltip_lines.append(f"• {client_name}: {status_icon}")

                    tooltip_text = "\n".join(tooltip_lines)
                else:
                    tooltip_text = (
                        "클릭하여 웹소켓 연결 상태를 새로고침합니다.\n"
                        "• 실시간 시세 데이터 연결 확인\n"
                        "• 업비트 WebSocket 서버 상태 확인\n\n"
                        "📡 웹소켓: 등록된 클라이언트가 없습니다"
                    )

                self.websocket_status_label.setToolTip(tooltip_text)
            else:
                self.websocket_status_label.setToolTip(
                    f"쿨다운 중입니다. {self.websocket_remaining_time}초 후에 다시 시도하세요.\n"
                    "너무 빈번한 상태 확인을 방지하기 위한 대기 시간입니다."
                )
        except Exception as e:
            self.logger.warning(f"웹소켓 툴팁 업데이트 실패: {e}")
            self.websocket_status_label.setToolTip("웹소켓 상태 정보를 가져올 수 없습니다.")

    def set_api_status(self, connected):
        """
        API 연결 상태 설정

        Args:
            connected (bool | None): 연결 상태 (None은 확인 중)
        """
        if connected is True:
            self.api_status_label.setText("API: 연결됨")
            # 성공 상태는 기본 스타일 사용 (추가 색상 불필요)
        elif connected is False:
            self.api_status_label.setText("API: 연결 끊김")
            # 실패 상태는 기본 스타일 사용 (추가 색상 불필요)
        else:
            # 확인 중 상태
            self.api_status_label.setText("API: 확인 중...")

        self.logger.debug(f"API 상태 업데이트: {connected}")

    def set_websocket_status(self, connected):
        """
        웹소켓 연결 상태 설정

        Args:
            connected (bool | None): 연결 상태 (None은 확인 중)
        """
        if connected is True:
            self.websocket_status_label.setText("WS: 활성")
        elif connected is False:
            self.websocket_status_label.setText("WS: 대기")
        else:
            # 확인 중 상태
            self.websocket_status_label.setText("WS: 확인 중...")

        self.logger.debug(f"웹소켓 상태 업데이트: {connected}")

    def set_db_status(self, connected):
        """
        DB 연결 상태 설정

        Args:
            connected (bool): 연결 상태
        """
        if connected:
            self.db_status_label.setText("DB: 연결됨")
        else:
            self.db_status_label.setText("DB: 연결 끊김")

        self.logger.debug(f"DB 상태 업데이트: {connected}")

    def show_message(self, message, timeout=0):
        """
        메시지 표시

        Args:
            message (str): 표시할 메시지
            timeout (int, optional): 메시지 표시 시간(ms). 0이면 계속 표시.
        """
        self.showMessage(message, timeout)

    # 하위 호환성을 위한 메서드들
    def update_api_status(self, connected):
        """외부 호환성을 위한 메서드"""
        self.set_api_status(connected)

    def update_db_status(self, connected):
        """외부 호환성을 위한 메서드"""
        self.set_db_status(connected)

    def update_websocket_status(self, connected):
        """외부 호환성을 위한 메서드"""
        self.set_websocket_status(connected)
