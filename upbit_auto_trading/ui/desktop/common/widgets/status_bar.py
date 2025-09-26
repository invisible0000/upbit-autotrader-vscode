"""
상태 바 위젯 모듈 (실거래 안전 버전)

통합된 StatusBar - API 상태, DB 상태, 웹소켓 상태, 시계를 모두 포함하는 단일 위젯
읽기 전용으로 설계되어 실거래 중 우발적 상호작용을 방지합니다.
"""
from PyQt6.QtWidgets import QStatusBar, QLabel
from PyQt6.QtCore import QTimer
from datetime import datetime
from typing import Optional
from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.monitoring.simple_failure_monitor import (
    get_api_statistics, is_api_healthy
)
# websocket_status_service는 지연 로딩으로 처리


class StatusBar(QStatusBar):
    """
    통합된 상태 바 위젯 (실거래 안전 버전)

    - 실시간 시계 표시
    - 읽기 전용 API 상태 (실거래 안전성)
    - 읽기 전용 DB 연결 상태
    - 읽기 전용 웹소켓 상태 (실거래 안전성)
    - 깔끔한 통합 UI
    """

    def __init__(self, parent=None, database_health_service=None):
        """
        초기화

        Args:
            parent: 부모 위젯
            database_health_service: DB 건강 상태 서비스 (옵션)
        """
        super().__init__(parent)
        self.logger = create_component_logger("StatusBar")

        # 서비스 주입
        self.database_health_service = database_health_service

        # UI 설정
        self._setup_ui()

        # 타이머 설정
        self._setup_timers()

        # 초기 상태 체크
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
        self.websocket_status_label = QLabel("웹소켓: 대기")
        self.websocket_status_label.setObjectName("websocket-status")

        # 시계 레이블
        self.time_label = QLabel()
        self.time_label.setObjectName("time-display")
        self.time_label.setMinimumWidth(140)  # 날짜와 시간을 위한 충분한 폭

        # 상태바에 위젯 추가 (왼쪽부터: API, DB, WS, 시계)
        self.addPermanentWidget(self.api_status_label)
        self.addPermanentWidget(self.db_status_label)
        self.addPermanentWidget(self.websocket_status_label)
        self.addPermanentWidget(self.time_label)

        # 기본 메시지 설정
        self.showMessage("준비됨")

        self.logger.debug("StatusBar QSS 스타일 적용 완료")

    def _setup_timers(self):
        """타이머 설정"""
        # 시계 업데이트 타이머 (1초마다)
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_time)
        self.clock_timer.start(1000)

        # 상태 체크 타이머 (15초마다)
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._periodic_status_check)
        self.status_timer.start(15000)  # 15초

    def _setup_auto_status_check(self):
        """자동 상태 체크 설정"""
        self.logger.info("StatusBar 초기 상태 체크 시작")

        # 초기 시간 설정
        self._update_time()

        # 초기 상태 체크 (1초 후)
        QTimer.singleShot(1000, self._initial_status_check)

    def _initial_status_check(self):
        """초기 상태 체크"""
        self._check_db_status()
        self._check_api_status()
        self._check_websocket_status()

    def _periodic_status_check(self):
        """주기적 상태 체크"""
        self._check_db_status()
        self._check_api_status()
        self._check_websocket_status()

    def _update_time(self):
        """시계 업데이트 - 날짜와 시간 표시"""
        current_datetime = datetime.now()
        date_str = current_datetime.strftime("%Y-%m-%d")
        time_str = current_datetime.strftime("%H:%M:%S")
        self.time_label.setText(f"{date_str} {time_str}")

    # === DB 상태 관리 ===

    def _check_db_status(self):
        """DB 상태 체크"""
        try:
            if self.database_health_service:
                db_healthy = self.database_health_service.check_overall_health()
                self.set_db_status(db_healthy)
                self.logger.debug(f"DB 상태 업데이트: {db_healthy}")
            else:
                # 서비스가 없으면 기본값으로 연결됨 표시
                self.set_db_status(True)
                self.logger.debug("DB 서비스 없음, 기본값으로 연결됨 표시")
        except Exception as e:
            self.logger.error(f"DB 상태 체크 실패: {e}")
            self.set_db_status(False)

    def set_db_status(self, connected: bool):
        """
        DB 상태 설정

        Args:
            connected: DB 연결 상태
        """
        if connected:
            self.db_status_label.setText("DB: 연결됨")
            self._update_db_tooltip("데이터베이스가 정상적으로 연결되어 있습니다.")
        else:
            self.db_status_label.setText("DB: 연결 끊김")
            self._update_db_tooltip("데이터베이스 연결에 문제가 있습니다.")

    def _update_db_tooltip(self, message: str):
        """DB 툴팁 업데이트"""
        self.db_status_label.setToolTip(message)

    # === API 상태 관리 === (읽기 전용)

    def _check_api_status(self):
        """API 상태 체크 - 모니터링 통계 기반 (네트워크 호출 없음)"""
        try:
            # 모니터링 통계만 확인 (실제 네트워크 호출 없음)
            api_stats = get_api_statistics()
            api_healthy = is_api_healthy()

            # 상태가 변경된 경우에만 로깅
            if hasattr(self, '_last_api_healthy') and self._last_api_healthy != api_healthy:
                if api_healthy:
                    self.logger.info(f"API 상태 복구됨 (성공률: {api_stats['success_rate']:.1f}%)")
                else:
                    self.logger.warning(f"API 상태 불량 감지 (연속 실패: {api_stats['consecutive_failures']}회)")

            # 상태 업데이트
            self.set_api_status(api_healthy)
            self._last_api_healthy = api_healthy

            # 초기 한 번만 API 테스트 수행
            if not hasattr(self, '_initial_api_test_done') and api_stats['total_calls'] == 0:
                self._initial_api_test_done = True
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
                self.logger.debug("API 라이브 테스트 완료: 정상 연결")
            else:
                mark_api_failure()
                self.logger.warning(f"API 라이브 테스트 완료: 연결 실패 (HTTP {response.status_code})")

            self.set_api_status(connected)

        except Exception as e:
            from upbit_auto_trading.infrastructure.monitoring.simple_failure_monitor import mark_api_failure
            mark_api_failure()
            self.logger.error(f"API 라이브 테스트 실패: {e}")
            self.set_api_status(False)

    def set_api_status(self, connected: bool | None):
        """
        API 상태 설정 (읽기 전용)

        Args:
            connected: API 연결 상태 (None=확인 중)
        """
        if connected is None:
            self.api_status_label.setText("API: 확인 중...")
            self._update_api_tooltip("API 연결 상태를 확인하고 있습니다...")
        elif connected:
            self.api_status_label.setText("API: 연결됨")
            self._update_api_tooltip()
        else:
            self.api_status_label.setText("API: 연결 끊김")
            self._update_api_tooltip("API 연결에 문제가 있습니다. 네트워크 상태를 확인해주세요.")

        self.logger.debug(f"API 상태 업데이트: {connected} ({'정상' if connected else '연결 실패' if connected is False else '확인 중'})")

    def _update_api_tooltip(self, custom_message: Optional[str] = None):
        """API 툴팁 업데이트 - 모니터링 통계 포함"""
        if custom_message:
            self.api_status_label.setToolTip(custom_message)
            return

        # 모니터링 통계 가져오기
        try:
            stats = get_api_statistics()
            if stats['total_calls'] > 0:
                tooltip_text = (
                    "📊 API 모니터링 통계 (읽기 전용):\n"
                    f"• 총 호출: {stats['total_calls']}회\n"
                    f"• 성공률: {stats['success_rate']:.1f}%\n"
                    f"• 연속 실패: {stats['consecutive_failures']}회\n"
                    f"• 건강 상태: {'양호' if is_api_healthy() else '문제 있음'}\n\n"
                    "⚠️ 실거래 안전을 위해 클릭 기능이 비활성화되어 있습니다."
                )
            else:
                tooltip_text = (
                    "📊 API 상태 모니터링:\n"
                    "• 아직 API 호출 통계가 없습니다\n"
                    "• 자동으로 연결 상태를 확인 중입니다\n\n"
                    "⚠️ 실거래 안전을 위해 클릭 기능이 비활성화되어 있습니다."
                )

            self.api_status_label.setToolTip(tooltip_text)

        except Exception as e:
            self.logger.error(f"API 툴팁 업데이트 실패: {e}")
            self.api_status_label.setToolTip("API 상태 모니터링 (읽기 전용)")

    # === 웹소켓 상태 관리 === (읽기 전용)

    def _check_websocket_status(self):
        """웹소켓 상태 체크 - 가볍게 구현"""
        try:
            # 웹소켓 상태 서비스 지연 로딩
            from upbit_auto_trading.infrastructure.services.websocket_status_service import get_websocket_status_service
            websocket_status_service = get_websocket_status_service()

            # 웹소켓 상태 서비스에서 전체 상태 조회
            connected = websocket_status_service.get_overall_status()

            self.set_websocket_status(connected)
            self.logger.debug(f"웹소켓 상태 체크 완료: {'활성' if connected else '대기'}")

        except Exception as e:
            self.logger.error(f"웹소켓 상태 체크 실패: {e}")
            self.set_websocket_status(False)

    def set_websocket_status(self, connected: bool | None):
        """
        웹소켓 상태 설정 (읽기 전용)

        Args:
            connected: 웹소켓 연결 상태 (None=확인 중)
        """
        if connected is None:
            self.websocket_status_label.setText("웹소켓: 확인 중...")
            self._update_websocket_tooltip("웹소켓 연결 상태를 확인하고 있습니다...")
        elif connected:
            self.websocket_status_label.setText("웹소켓: 활성")
            self._update_websocket_tooltip()
        else:
            self.websocket_status_label.setText("웹소켓: 대기")
            self._update_websocket_tooltip()

        self.logger.debug(f"웹소켓 상태 업데이트: {connected} ({'활성' if connected else '대기' if connected is False else '확인 중'})")

    def _update_websocket_tooltip(self, custom_message: Optional[str] = None):
        """웹소켓 툴팁 업데이트"""
        if custom_message:
            self.websocket_status_label.setToolTip(custom_message)
            return

        try:
            # 웹소켓 상태 서비스 지연 로딩
            from upbit_auto_trading.infrastructure.services.websocket_status_service import get_websocket_status_service
            websocket_status_service = get_websocket_status_service()

            summary = websocket_status_service.get_status_summary()
            tooltip_text = (
                f"📡 웹소켓 상태 (읽기 전용):\n"
                f"{summary}\n\n"
                "⚠️ 실거래 안전을 위해 클릭 기능이 비활성화되어 있습니다."
            )
            self.websocket_status_label.setToolTip(tooltip_text)

        except Exception as e:
            self.logger.error(f"웹소켓 툴팁 업데이트 실패: {e}")
            self.websocket_status_label.setToolTip("웹소켓 상태 모니터링 (읽기 전용)")
