"""
데이터베이스 상태 표시 Presenter (MVP 패턴)

StatusBar의 "DB: 연결됨" 표시를 관리하는 Presenter입니다.
API 상태와 유사한 복잡한 구조로 구현되었습니다.
"""

from typing import Dict
from dataclasses import dataclass
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.use_cases.database_configuration.system_startup_health_check_use_case import (
    SystemStartupHealthCheckUseCase, StartupHealthCheckRequest
)
from upbit_auto_trading.domain.database_configuration.value_objects.database_health_report import (
    DatabaseHealthLevel, SystemDatabaseHealth
)


@dataclass
class DatabaseStatusDisplayState:
    """DB 상태 표시 상태"""
    is_connected: bool
    status_text: str
    tooltip_text: str
    last_updated: datetime
    health_level: DatabaseHealthLevel
    critical_issues: list
    can_be_refreshed: bool


class DatabaseStatusPresenter(QObject):
    """
    데이터베이스 상태 표시 Presenter

    StatusBar의 DB 상태를 관리하고 사용자에게 적절한 피드백을 제공합니다.
    API 상태와 유사한 복잡한 상태 관리를 수행합니다.
    """

    # 상태 변경 시그널
    status_changed = pyqtSignal(bool, str)  # connected, status_text
    critical_warning_detected = pyqtSignal(str)  # warning_message
    user_attention_required = pyqtSignal(list)  # recommendations

    def __init__(self, database_paths: Dict[str, str]):
        super().__init__()

        self._logger = create_component_logger("DatabaseStatusPresenter")
        self._database_paths = database_paths
        self._health_check_use_case = SystemStartupHealthCheckUseCase()

        # 현재 상태
        self._current_state = DatabaseStatusDisplayState(
            is_connected=False,
            status_text="DB: 확인 중...",
            tooltip_text="데이터베이스 상태를 확인하는 중입니다",
            last_updated=datetime.now(),
            health_level=DatabaseHealthLevel.WARNING,
            critical_issues=[],
            can_be_refreshed=True
        )

        # 자동 갱신 타이머 (API와 유사)
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._perform_background_check)

        # 쿨다운 타이머 (너무 빈번한 확인 방지)
        self._cooldown_timer = QTimer()
        self._cooldown_timer.setSingleShot(True)
        self._cooldown_timer.timeout.connect(self._enable_refresh)

        self._is_checking = False
        self._cooldown_active = False

        self._logger.info("DB 상태 Presenter 초기화 완료")

    async def check_database_status_on_startup(self) -> None:
        """프로그램 시작 시 DB 상태 확인"""
        self._logger.info("🚀 시작 시 DB 상태 확인")

        try:
            request = StartupHealthCheckRequest(
                database_paths=self._database_paths,
                force_start_on_failure=True,
                create_missing_databases=True
            )

            result = await self._health_check_use_case.execute(request)
            self._update_status_from_health_check(result.system_health)

            # 치명적 문제가 있으면 사용자에게 알림
            if result.requires_user_attention:
                self.user_attention_required.emit(result.recommended_user_actions)

            if result.critical_warnings:
                warning_text = "\n".join(result.critical_warnings)
                self.critical_warning_detected.emit(warning_text)

        except Exception as e:
            self._logger.error(f"시작 시 DB 상태 확인 실패: {e}")
            self._set_error_state(f"DB 상태 확인 실패: {str(e)}")

    async def check_database_status_on_settings_change(self, new_paths: Dict[str, str]) -> None:
        """설정 변경 시 DB 상태 확인"""
        self._logger.info("⚙️ 설정 변경으로 인한 DB 상태 확인")

        # 경로 업데이트
        self._database_paths = new_paths

        # 즉시 상태 확인
        await self.check_database_status_on_startup()

    async def check_database_status_on_failure_detection(self) -> None:
        """DB 고장 감지 시 상태 확인"""
        self._logger.warning("🚨 DB 고장 감지로 인한 상태 확인")

        if self._cooldown_active:
            self._logger.info("쿨다운 중이므로 확인 생략")
            return

        await self.check_database_status_on_startup()

        # 5분 쿨다운 적용 (너무 빈번한 확인 방지)
        self._start_cooldown(300)  # 5분

    def request_manual_refresh(self) -> None:
        """수동 새로고침 요청 (StatusBar 클릭 등)"""
        if self._is_checking or self._cooldown_active:
            self._logger.info("이미 확인 중이거나 쿨다운 중")
            return

        self._logger.info("🔄 수동 DB 상태 새로고침 요청")
        self._perform_manual_check()

    def _perform_manual_check(self) -> None:
        """수동 확인 수행"""
        # 비동기 확인을 동기적으로 트리거
        import asyncio
        try:
            # 이벤트 루프가 있으면 task로 실행
            loop = asyncio.get_event_loop()
            loop.create_task(self.check_database_status_on_startup())
        except RuntimeError:
            # 이벤트 루프가 없으면 새로 생성하여 실행
            asyncio.run(self.check_database_status_on_startup())

        # 수동 확인 후 30초 쿨다운
        self._start_cooldown(30)

    def _perform_background_check(self) -> None:
        """백그라운드 주기적 확인 (사용하지 않음 - 위험)"""
        # 동작 중 주기적 DB 확인은 위험하므로 비활성화
        self._logger.debug("백그라운드 DB 확인 스킵 (안전상 이유)")

    def _update_status_from_health_check(self, system_health: SystemDatabaseHealth) -> None:
        """건강 검사 결과로부터 상태 업데이트"""

        # 연결 상태 결정
        is_connected = system_health.system_can_start

        # 상태 텍스트 생성
        if system_health.overall_status == DatabaseHealthLevel.HEALTHY:
            status_text = "DB: 연결됨"
            tooltip = f"모든 데이터베이스가 정상입니다 ({len(system_health.healthy_databases)}개)"

        elif system_health.overall_status == DatabaseHealthLevel.WARNING:
            status_text = "DB: 경고"
            problematic = len(system_health.problematic_databases)
            tooltip = f"일부 데이터베이스에 문제가 있습니다 (문제: {problematic}개)"

        elif system_health.overall_status == DatabaseHealthLevel.ERROR:
            status_text = "DB: 오류"
            tooltip = "데이터베이스 연결에 문제가 있습니다"

        elif system_health.overall_status == DatabaseHealthLevel.CRITICAL:
            status_text = "DB: 치명적"
            tooltip = "데이터베이스가 심각하게 손상되었습니다"

        else:  # MISSING
            status_text = "DB: 파일 없음"
            tooltip = "데이터베이스 파일을 찾을 수 없습니다"

        # 상세 툴팁 생성
        detailed_tooltip = self._create_detailed_tooltip(system_health, tooltip)

        # 상태 업데이트
        self._current_state = DatabaseStatusDisplayState(
            is_connected=is_connected,
            status_text=status_text,
            tooltip_text=detailed_tooltip,
            last_updated=datetime.now(),
            health_level=system_health.overall_status,
            critical_issues=system_health.critical_issues,
            can_be_refreshed=True
        )

        # UI에 시그널 전송
        self.status_changed.emit(is_connected, status_text)

        self._logger.info(f"DB 상태 업데이트: {status_text}")

    def _create_detailed_tooltip(self, system_health: SystemDatabaseHealth, base_tooltip: str) -> str:
        """상세 툴팁 생성"""
        lines = [base_tooltip, ""]

        # 각 DB별 상태
        lines.append("📊 데이터베이스별 상태:")
        for db_type, report in system_health.reports.items():
            status_icon = "✅" if report.is_operational else "❌"
            lines.append(f"  {status_icon} {db_type}: {report.health_level.value}")

        # 마지막 확인 시간
        lines.append("")
        lines.append(f"🕒 마지막 확인: {self._current_state.last_updated.strftime('%H:%M:%S')}")

        # 클릭 안내
        if self._current_state.can_be_refreshed:
            lines.append("💡 클릭하여 수동 새로고침")

        return "\n".join(lines)

    def _set_error_state(self, error_message: str) -> None:
        """에러 상태 설정"""
        self._current_state = DatabaseStatusDisplayState(
            is_connected=False,
            status_text="DB: 확인 실패",
            tooltip_text=f"데이터베이스 상태 확인 실패\n{error_message}",
            last_updated=datetime.now(),
            health_level=DatabaseHealthLevel.ERROR,
            critical_issues=[error_message],
            can_be_refreshed=True
        )

        self.status_changed.emit(False, "DB: 확인 실패")

    def _start_cooldown(self, seconds: int) -> None:
        """쿨다운 시작"""
        self._cooldown_active = True
        self._current_state.can_be_refreshed = False
        self._cooldown_timer.start(seconds * 1000)

        self._logger.debug(f"DB 상태 확인 쿨다운 시작: {seconds}초")

    def _enable_refresh(self) -> None:
        """새로고침 활성화 (쿨다운 종료)"""
        self._cooldown_active = False
        self._current_state.can_be_refreshed = True

        self._logger.debug("DB 상태 확인 쿨다운 종료")

    def get_current_status(self) -> DatabaseStatusDisplayState:
        """현재 상태 반환"""
        return self._current_state

    def is_refresh_available(self) -> bool:
        """새로고침 가능 여부"""
        return self._current_state.can_be_refreshed and not self._is_checking
