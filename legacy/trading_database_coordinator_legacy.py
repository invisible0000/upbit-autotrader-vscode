"""
Trading Database Coordinator Use Case

실거래와 백테스팅 상황에서 데이터베이스 조정을 담당하는 Use Case입니다.
거래 상태를 모니터링하고 데이터베이스 작업의 안전성을 보장합니다.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.dto.database_config_dto import (
    TradingStateDto, DatabaseStatusDto, DatabaseStatusEnum
)
from upbit_auto_trading.domain.database_configuration.repositories.idatabase_config_repository import (
    IDatabaseConfigRepository
)


class DatabaseOperationType(Enum):
    """데이터베이스 작업 타입"""
    PROFILE_SWITCH = "profile_switch"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
    SCHEMA_MIGRATION = "schema_migration"
    PROFILE_UPDATE = "profile_update"


class TradingDatabaseCoordinator:
    """거래-데이터베이스 조정자"""

    def __init__(self, repository: IDatabaseConfigRepository):
        self._repository = repository
        self._logger = create_component_logger("TradingDatabaseCoordinator")
        self._active_operations: Dict[str, DatabaseOperationType] = {}

    async def check_operation_feasibility(
        self,
        operation_type: DatabaseOperationType,
        profile_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        데이터베이스 작업의 실행 가능성을 검사합니다.

        Args:
            operation_type: 수행하려는 작업 타입
            profile_id: 대상 프로필 ID (옵션)

        Returns:
            실행 가능성 분석 결과
        """
        self._logger.info(f"🔍 작업 실행 가능성 검사: {operation_type.value}")

        try:
            # 거래 상태 조회
            trading_state = await self._get_current_trading_state()

            # 데이터베이스 상태 조회
            db_status = await self._get_database_status(profile_id)

            # 실행 가능성 분석
            feasibility = self._analyze_operation_feasibility(
                operation_type,
                trading_state,
                db_status
            )

            self._logger.info(f"✅ 실행 가능성 검사 완료: {feasibility['can_execute']}")
            return feasibility

        except Exception as e:
            self._logger.error(f"❌ 실행 가능성 검사 실패: {e}")
            return {
                'can_execute': False,
                'reason': f"검사 중 오류 발생: {e}",
                'recommendations': ["시스템 상태를 확인하고 다시 시도하세요"]
            }

    async def coordinate_safe_operation(
        self,
        operation_type: DatabaseOperationType,
        operation_params: Dict[str, Any],
        force_execution: bool = False
    ) -> Dict[str, Any]:
        """
        안전한 데이터베이스 작업을 조정합니다.

        Args:
            operation_type: 수행할 작업 타입
            operation_params: 작업 매개변수
            force_execution: 강제 실행 여부

        Returns:
            작업 결과
        """
        operation_id = f"{operation_type.value}_{datetime.now().timestamp()}"
        self._logger.info(f"🎯 안전한 작업 조정 시작: {operation_id}")

        try:
            # 실행 가능성 검사
            if not force_execution:
                feasibility = await self.check_operation_feasibility(
                    operation_type,
                    operation_params.get('profile_id')
                )

                if not feasibility['can_execute']:
                    return {
                        'success': False,
                        'operation_id': operation_id,
                        'reason': feasibility['reason'],
                        'recommendations': feasibility['recommendations']
                    }

            # 작업 등록
            self._register_operation(operation_id, operation_type)

            # 작업 실행
            result = await self._execute_coordinated_operation(
                operation_type,
                operation_params
            )

            # 작업 완료 처리
            self._unregister_operation(operation_id)

            result.update({
                'success': True,
                'operation_id': operation_id
            })

            self._logger.info(f"✅ 안전한 작업 조정 완료: {operation_id}")
            return result

        except Exception as e:
            self._unregister_operation(operation_id)
            self._logger.error(f"❌ 안전한 작업 조정 실패: {operation_id} - {e}")
            return {
                'success': False,
                'operation_id': operation_id,
                'reason': str(e),
                'recommendations': ["로그를 확인하고 시스템 관리자에게 문의하세요"]
            }

    async def get_safe_switching_window(self, target_profile_id: str) -> Dict[str, Any]:
        """
        안전한 프로필 전환 시점을 조회합니다.

        Args:
            target_profile_id: 전환할 프로필 ID

        Returns:
            안전한 전환 시점 정보
        """
        self._logger.info(f"🕐 안전한 전환 시점 조회: {target_profile_id}")

        try:
            trading_state = await self._get_current_trading_state()

            # 즉시 전환 가능한지 확인
            if self._can_switch_immediately(trading_state):
                return {
                    'can_switch_now': True,
                    'next_safe_window': datetime.now(),
                    'reason': "현재 즉시 전환 가능",
                    'estimated_duration_seconds': 5
                }

            # 다음 안전한 시점 예측
            next_window = self._predict_next_safe_window(trading_state)

            return {
                'can_switch_now': False,
                'next_safe_window': next_window['timestamp'],
                'reason': next_window['reason'],
                'estimated_duration_seconds': next_window['duration'],
                'blocking_operations': trading_state.blocking_operations or []
            }

        except Exception as e:
            self._logger.error(f"❌ 안전한 전환 시점 조회 실패: {e}")
            return {
                'can_switch_now': False,
                'next_safe_window': None,
                'reason': f"조회 중 오류 발생: {e}",
                'estimated_duration_seconds': 0
            }

    async def monitor_database_health(self) -> List[Dict[str, Any]]:
        """
        모든 데이터베이스 프로필의 건강 상태를 모니터링합니다.

        Returns:
            프로필별 건강 상태 목록
        """
        self._logger.info("💓 데이터베이스 건강 상태 모니터링")

        try:
            active_profiles = await self._repository.get_active_profiles()
            health_reports = []

            for db_type, profile in active_profiles.items():
                health_status = await self._check_profile_health(profile)
                health_reports.append({
                    'database_type': db_type,
                    'profile_id': profile.profile_id,
                    'profile_name': profile.name,
                    'health_status': health_status,
                    'checked_at': datetime.now()
                })

            self._logger.info(f"✅ 건강 상태 모니터링 완료: {len(health_reports)}개 프로필")
            return health_reports

        except Exception as e:
            self._logger.error(f"❌ 건강 상태 모니터링 실패: {e}")
            return []

    async def _get_current_trading_state(self) -> TradingStateDto:
        """현재 거래 상태를 조회합니다."""
        # TODO: 실제 거래 시스템과 연동
        # 현재는 mock 데이터 반환
        return TradingStateDto(
            is_trading_active=False,
            active_strategies=[],
            is_backtest_running=False,
            active_backtests=[],
            can_switch_database=True,
            blocking_operations=list(self._active_operations.keys())
        )

    async def _get_database_status(self, profile_id: Optional[str]) -> Optional[DatabaseStatusDto]:
        """데이터베이스 상태를 조회합니다."""
        if not profile_id:
            return None

        try:
            profile = await self._repository.load_profile(profile_id)
            if not profile:
                return None

            # TODO: 실제 데이터베이스 연결 상태 확인
            return DatabaseStatusDto(
                profile_id=profile_id,
                status=DatabaseStatusEnum.ACTIVE if profile.is_active else DatabaseStatusEnum.INACTIVE,
                connection_count=0,
                last_activity=profile.last_accessed
            )

        except Exception as e:
            self._logger.warning(f"데이터베이스 상태 조회 실패: {e}")
            return None

    def _analyze_operation_feasibility(
        self,
        operation_type: DatabaseOperationType,
        trading_state: TradingStateDto,
        db_status: Optional[DatabaseStatusDto]
    ) -> Dict[str, Any]:
        """작업 실행 가능성을 분석합니다."""

        # 기본 조건 확인
        if not trading_state.can_switch_database:
            return {
                'can_execute': False,
                'reason': "현재 데이터베이스 작업이 제한되어 있습니다",
                'recommendations': ["진행 중인 작업이 완료될 때까지 대기하세요"],
                'blocking_factors': trading_state.blocking_operations or []
            }

        # 작업 타입별 세부 검증
        if operation_type == DatabaseOperationType.PROFILE_SWITCH:
            return self._analyze_profile_switch_feasibility(trading_state, db_status)

        elif operation_type == DatabaseOperationType.BACKUP_RESTORE:
            return self._analyze_backup_restore_feasibility(trading_state)

        elif operation_type == DatabaseOperationType.BACKUP_CREATE:
            return self._analyze_backup_create_feasibility(trading_state)

        else:
            return {
                'can_execute': True,
                'reason': "일반적인 데이터베이스 작업은 실행 가능합니다",
                'recommendations': [],
                'estimated_duration_seconds': 10
            }

    def _analyze_profile_switch_feasibility(
        self,
        trading_state: TradingStateDto,
        db_status: Optional[DatabaseStatusDto]
    ) -> Dict[str, Any]:
        """프로필 전환 실행 가능성 분석"""

        if trading_state.is_trading_active:
            return {
                'can_execute': False,
                'reason': "실거래 진행 중에는 프로필을 전환할 수 없습니다",
                'recommendations': ["거래를 중단하거나 완료 후 전환하세요"],
                'active_strategies': trading_state.active_strategies
            }

        if trading_state.is_backtest_running:
            return {
                'can_execute': False,
                'reason': "백테스팅 진행 중에는 프로필을 전환할 수 없습니다",
                'recommendations': ["백테스팅 완료 후 전환하세요"],
                'active_backtests': trading_state.active_backtests
            }

        return {
            'can_execute': True,
            'reason': "프로필 전환이 가능합니다",
            'recommendations': [],
            'estimated_duration_seconds': 5
        }

    def _analyze_backup_restore_feasibility(self, trading_state: TradingStateDto) -> Dict[str, Any]:
        """백업 복원 실행 가능성 분석"""

        if trading_state.is_trading_active or trading_state.is_backtest_running:
            return {
                'can_execute': False,
                'reason': "거래나 백테스팅 진행 중에는 백업을 복원할 수 없습니다",
                'recommendations': ["모든 활동을 중단하고 복원하세요"]
            }

        return {
            'can_execute': True,
            'reason': "백업 복원이 가능합니다",
            'recommendations': ["복원 전 현재 상태의 백업 생성을 권장합니다"],
            'estimated_duration_seconds': 30
        }

    def _analyze_backup_create_feasibility(self, trading_state: TradingStateDto) -> Dict[str, Any]:
        """백업 생성 실행 가능성 분석"""
        # WAL 모드에서는 거의 항상 백업 가능
        return {
            'can_execute': True,
            'reason': "WAL 모드에서 백업 생성이 가능합니다",
            'recommendations': [],
            'estimated_duration_seconds': 15,
            'notes': ["거래 중에도 안전하게 백업이 생성됩니다"]
        }

    async def _execute_coordinated_operation(
        self,
        operation_type: DatabaseOperationType,
        operation_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """조정된 작업을 실행합니다."""

        if operation_type == DatabaseOperationType.PROFILE_SWITCH:
            # 실제 프로필 전환 로직은 ProfileManagementUseCase에 위임
            return {
                'result': "프로필 전환 요청이 처리되었습니다",
                'details': operation_params
            }

        elif operation_type == DatabaseOperationType.BACKUP_CREATE:
            return {
                'result': "백업 생성 요청이 처리되었습니다",
                'details': operation_params
            }

        elif operation_type == DatabaseOperationType.BACKUP_RESTORE:
            return {
                'result': "백업 복원 요청이 처리되었습니다",
                'details': operation_params
            }

        else:
            return {
                'result': f"{operation_type.value} 작업이 처리되었습니다",
                'details': operation_params
            }

    def _can_switch_immediately(self, trading_state: TradingStateDto) -> bool:
        """즉시 전환 가능한지 확인"""
        return (
            not trading_state.is_trading_active
            and not trading_state.is_backtest_running
            and trading_state.can_switch_database
            and len(self._active_operations) == 0
        )

    def _predict_next_safe_window(self, trading_state: TradingStateDto) -> Dict[str, Any]:
        """다음 안전한 전환 시점을 예측"""
        # 간단한 예측 로직 (실제로는 더 복잡한 분석 필요)
        if trading_state.is_trading_active:
            # 거래는 보통 몇 분 내에 완료
            return {
                'timestamp': datetime.now().replace(minute=datetime.now().minute + 5),
                'reason': "거래 완료 예상 시점",
                'duration': 300
            }

        if trading_state.is_backtest_running:
            # 백테스팅은 더 오래 걸릴 수 있음
            return {
                'timestamp': datetime.now().replace(hour=datetime.now().hour + 1),
                'reason': "백테스팅 완료 예상 시점",
                'duration': 3600
            }

        # 기타 작업들
        return {
            'timestamp': datetime.now().replace(minute=datetime.now().minute + 1),
            'reason': "현재 작업 완료 예상 시점",
            'duration': 60
        }

    async def _check_profile_health(self, profile) -> Dict[str, Any]:
        """프로필 건강 상태를 확인"""
        try:
            health_status = {
                'overall_status': 'healthy',
                'file_exists': profile.is_file_exists(),
                'file_size_bytes': profile.get_file_size(),
                'last_modified': profile.get_last_modified(),
                'issues': [],
                'warnings': []
            }

            # 파일 존재 여부 확인
            if not health_status['file_exists']:
                health_status['overall_status'] = 'critical'
                health_status['issues'].append("데이터베이스 파일이 존재하지 않습니다")

            # 파일 크기 확인
            if health_status['file_size_bytes'] == 0:
                health_status['overall_status'] = 'warning'
                health_status['warnings'].append("데이터베이스 파일이 비어있습니다")

            # TODO: 데이터베이스 연결 테스트, 스키마 검증 등 추가

            return health_status

        except Exception as e:
            return {
                'overall_status': 'error',
                'file_exists': False,
                'file_size_bytes': 0,
                'last_modified': None,
                'issues': [f"건강 상태 확인 중 오류: {e}"],
                'warnings': []
            }

    def _register_operation(self, operation_id: str, operation_type: DatabaseOperationType) -> None:
        """작업을 등록합니다"""
        self._active_operations[operation_id] = operation_type
        self._logger.debug(f"작업 등록됨: {operation_id} ({operation_type.value})")

    def _unregister_operation(self, operation_id: str) -> None:
        """작업 등록을 해제합니다"""
        if operation_id in self._active_operations:
            operation_type = self._active_operations.pop(operation_id)
            self._logger.debug(f"작업 등록 해제됨: {operation_id} ({operation_type.value})")
