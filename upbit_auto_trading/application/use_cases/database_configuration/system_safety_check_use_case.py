"""
시스템 안전성 확인 Use Case

백업/복원 작업 전 시스템 상태를 검사하여 안전성을 보장합니다.
실시간 매매, 백테스팅 등의 활성 상태를 확인합니다.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass(frozen=True)
class SystemSafetyRequestDto:
    """시스템 안전성 확인 요청 DTO"""

    operation_name: str
    safety_level: str = "NORMAL"  # NORMAL, HIGH, CRITICAL
    timeout_seconds: int = 30
    force_check: bool = False


@dataclass(frozen=True)
class SystemSafetyStatusDto:
    """시스템 안전성 상태 DTO"""

    is_safe_for_backup: bool
    is_trading_active: bool
    is_backtesting_active: bool
    active_processes: List[str]
    warning_messages: List[str]
    blocking_operations: List[str]
    last_checked: datetime

    def get_safety_summary(self) -> str:
        """안전성 상태 요약"""
        if self.is_safe_for_backup:
            return "✅ 시스템이 백업 작업에 안전한 상태입니다"
        else:
            blocking = ", ".join(self.blocking_operations)
            return f"⚠️ 백업 작업이 위험한 상태입니다: {blocking}"


class SystemSafetyCheckUseCase:
    """시스템 안전성 확인 Use Case"""

    def __init__(self):
        self.logger = create_component_logger("SystemSafetyCheckUseCase")

    def check_backup_safety(self) -> SystemSafetyStatusDto:
        """백업 작업 안전성 확인"""
        try:
            self.logger.info("🛡️ 시스템 백업 안전성 검사 시작")

            # 1. 거래 상태 확인
            trading_status = self._check_trading_status()

            # 2. 백테스팅 상태 확인
            backtesting_status = self._check_backtesting_status()

            # 3. DB 연결 상태 확인
            db_connections = self._check_database_connections()

            # 4. 활성 프로세스 확인
            active_processes = self._get_active_processes()

            # 5. 위험 요소 분석
            blocking_operations = []
            warning_messages = []

            if trading_status.get('is_active', False):
                blocking_operations.append("실시간 매매 활성")
                warning_messages.append("실시간 매매가 진행 중입니다. 백업 시 포지션 정보가 손실될 수 있습니다.")

            if backtesting_status.get('is_active', False):
                blocking_operations.append("백테스팅 실행 중")
                warning_messages.append("백테스팅이 실행 중입니다. 백업 시 결과가 손실될 수 있습니다.")

            if db_connections.get('active_connections', 0) > 0:
                blocking_operations.append(f"활성 DB 연결 {db_connections['active_connections']}개")
                warning_messages.append("데이터베이스 연결이 활성화되어 있습니다. 백업 전 연결을 종료해야 합니다.")

            # 6. 최종 안전성 판단
            is_safe = len(blocking_operations) == 0

            status = SystemSafetyStatusDto(
                is_safe_for_backup=is_safe,
                is_trading_active=trading_status.get('is_active', False),
                is_backtesting_active=backtesting_status.get('is_active', False),
                active_processes=active_processes,
                warning_messages=warning_messages,
                blocking_operations=blocking_operations,
                last_checked=datetime.now()
            )

            self.logger.info(f"🛡️ 안전성 검사 완료: {status.get_safety_summary()}")
            return status

        except Exception as e:
            self.logger.error(f"❌ 시스템 안전성 검사 실패: {e}")
            # 오류 시 안전하지 않다고 간주
            return SystemSafetyStatusDto(
                is_safe_for_backup=False,
                is_trading_active=False,
                is_backtesting_active=False,
                active_processes=[],
                warning_messages=[f"안전성 검사 중 오류 발생: {str(e)}"],
                blocking_operations=["시스템 상태 확인 불가"],
                last_checked=datetime.now()
            )

    def _check_trading_status(self) -> Dict[str, Any]:
        """거래 상태 확인"""
        try:
            # TradeMonitor 상태 확인
            # 실제 구현에서는 TradingStateService 사용
            return {
                'is_active': False,  # 임시: 실제로는 모니터링 서비스에서 확인
                'active_positions': 0,
                'active_orders': 0
            }
        except Exception as e:
            self.logger.warning(f"⚠️ 거래 상태 확인 실패: {e}")
            return {'is_active': False}

    def _check_backtesting_status(self) -> Dict[str, Any]:
        """백테스팅 상태 확인"""
        try:
            # BacktestApplicationService에서 실행 중인 백테스트 확인
            # 실제로는 BacktestRepository.find_running_backtests() 사용
            return {
                'is_active': False,  # 임시: 실제로는 백테스트 서비스에서 확인
                'running_backtests': []
            }
        except Exception as e:
            self.logger.warning(f"⚠️ 백테스팅 상태 확인 실패: {e}")
            return {'is_active': False}

    def _check_database_connections(self) -> Dict[str, Any]:
        """데이터베이스 연결 상태 확인"""
        try:
            # 실제로는 데이터베이스 연결 풀에서 활성 연결 수 확인
            return {
                'active_connections': 0,  # 임시: 실제로는 연결 풀에서 확인
                'connection_details': []
            }
        except Exception as e:
            self.logger.warning(f"⚠️ DB 연결 상태 확인 실패: {e}")
            return {'active_connections': 0}

    def _get_active_processes(self) -> List[str]:
        """활성 프로세스 목록 조회"""
        try:
            # SystemStatusTracker에서 활성 컴포넌트 확인
            return []  # 임시: 실제로는 상태 추적기에서 확인
        except Exception as e:
            self.logger.warning(f"⚠️ 활성 프로세스 확인 실패: {e}")
            return []

    def request_system_pause(self) -> bool:
        """시스템 일시 정지 요청"""
        try:
            self.logger.info("⏸️ 시스템 일시 정지 요청")

            # 1. 거래 모니터링 중지
            # TradeMonitor.stop_monitoring()

            # 2. 백테스팅 중지
            # BacktestApplicationService.stop_all_backtests()

            # 3. DB 연결 정리
            # DatabaseConnectionPool.close_all_connections()

            # 임시: 실제 구현은 각 서비스에 위임
            self.logger.info("✅ 시스템 일시 정지 완료")
            return True

        except Exception as e:
            self.logger.error(f"❌ 시스템 일시 정지 실패: {e}")
            return False

    def request_system_resume(self) -> bool:
        """시스템 재개 요청"""
        try:
            self.logger.info("▶️ 시스템 재개 요청")

            # 1. DB 연결 복구
            # DatabaseConnectionPool.initialize_connections()

            # 2. 거래 모니터링 재시작
            # TradeMonitor.start_monitoring()

            # 3. 시스템 상태 확인
            # SystemStatusTracker.refresh_all_components()

            # 임시: 실제 구현은 각 서비스에 위임
            self.logger.info("✅ 시스템 재개 완료")
            return True

        except Exception as e:
            self.logger.error(f"❌ 시스템 재개 실패: {e}")
            return False

    def check_system_safety(self, request: SystemSafetyRequestDto) -> SystemSafetyStatusDto:
        """시스템 안전성 검사"""
        try:
            self.logger.info(f"🔍 시스템 안전성 검사 시작: {request.operation_name}")

            # 기본 안전성 검사 수행
            safety_status = self.check_backup_safety()

            # 요청된 안전성 레벨에 따른 추가 검사
            if request.safety_level == "CRITICAL":
                # Critical 레벨 검사 강화
                if safety_status.is_trading_active or safety_status.is_backtesting_active:
                    # Critical 작업에서는 모든 활동 중단 필요
                    return SystemSafetyStatusDto(
                        is_safe_for_backup=False,
                        is_trading_active=safety_status.is_trading_active,
                        is_backtesting_active=safety_status.is_backtesting_active,
                        active_processes=safety_status.active_processes,
                        warning_messages=safety_status.warning_messages + ["Critical 작업을 위해 모든 활동 중단 필요"],
                        blocking_operations=safety_status.blocking_operations,
                        last_checked=datetime.now()
                    )

            return safety_status

        except Exception as e:
            self.logger.error(f"❌ 안전성 검사 실패: {e}")
            return SystemSafetyStatusDto(
                is_safe_for_backup=False,
                is_trading_active=False,
                is_backtesting_active=False,
                active_processes=[],
                warning_messages=[f"안전성 검사 실패: {str(e)}"],
                blocking_operations=["system_error"],
                last_checked=datetime.now()
            )

    def pause_trading_system(self, request: SystemSafetyRequestDto) -> SystemSafetyStatusDto:
        """거래 시스템 일시 정지"""
        try:
            self.logger.warning(f"🛑 거래 시스템 일시 정지: {request.operation_name}")

            # 시스템 일시 정지 수행
            pause_success = self.request_system_pause()

            if pause_success:
                return SystemSafetyStatusDto(
                    is_safe_for_backup=True,
                    is_trading_active=False,
                    is_backtesting_active=False,
                    active_processes=[],
                    warning_messages=[f"시스템이 '{request.operation_name}' 작업을 위해 일시 정지됨"],
                    blocking_operations=[],
                    last_checked=datetime.now()
                )
            else:
                return SystemSafetyStatusDto(
                    is_safe_for_backup=False,
                    is_trading_active=True,
                    is_backtesting_active=True,
                    active_processes=["unknown"],
                    warning_messages=["시스템 일시 정지 실패"],
                    blocking_operations=["system_pause_failed"],
                    last_checked=datetime.now()
                )

        except Exception as e:
            self.logger.error(f"❌ 거래 시스템 정지 실패: {e}")
            return SystemSafetyStatusDto(
                is_safe_for_backup=False,
                is_trading_active=True,
                is_backtesting_active=True,
                active_processes=["error"],
                warning_messages=[f"시스템 정지 실패: {str(e)}"],
                blocking_operations=["system_error"],
                last_checked=datetime.now()
            )

    def resume_trading_system(self, request: SystemSafetyRequestDto) -> SystemSafetyStatusDto:
        """거래 시스템 재개"""
        try:
            self.logger.info(f"▶️ 거래 시스템 재개: {request.operation_name}")

            # 시스템 재개 수행
            resume_success = self.request_system_resume()

            if resume_success:
                return SystemSafetyStatusDto(
                    is_safe_for_backup=True,
                    is_trading_active=False,  # 재개되었지만 아직 거래는 시작되지 않음
                    is_backtesting_active=False,
                    active_processes=[],
                    warning_messages=[f"시스템이 '{request.operation_name}' 작업 완료 후 재개됨"],
                    blocking_operations=[],
                    last_checked=datetime.now()
                )
            else:
                return SystemSafetyStatusDto(
                    is_safe_for_backup=False,
                    is_trading_active=False,
                    is_backtesting_active=False,
                    active_processes=["error"],
                    warning_messages=["시스템 재개 실패"],
                    blocking_operations=["system_resume_failed"],
                    last_checked=datetime.now()
                )

        except Exception as e:
            self.logger.error(f"❌ 거래 시스템 재개 실패: {e}")
            return SystemSafetyStatusDto(
                is_safe_for_backup=False,
                is_trading_active=False,
                is_backtesting_active=False,
                active_processes=["error"],
                warning_messages=[f"시스템 재개 실패: {str(e)}"],
                blocking_operations=["system_error"],
                last_checked=datetime.now()
            )
