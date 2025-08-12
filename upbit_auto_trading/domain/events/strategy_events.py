"""
전략 관련 도메인 이벤트
Strategy Aggregate와 관련된 모든 비즈니스 이벤트 정의

DomainEvent 베이스 클래스 변경으로 인한 구조 개선:
- 이제 dataclass 제약 없이 필수 필드를 자유롭게 정의 가능
- 필수 필드를 생성자에서 직접 받아 검증
- frozen 특성은 프로퍼티의 setter 없음으로 구현
"""

from typing import Any, Dict, Optional
from datetime import datetime
from . import DomainEvent

class StrategyCreated(DomainEvent):
    """전략 생성 이벤트"""

    def __init__(self, strategy_id: str, strategy_name: str, strategy_type: str = "entry",
                 created_by: Optional[str] = None, strategy_config: Optional[Dict[str, Any]] = None):
        """
        전략 생성 이벤트 초기화

        Args:
            strategy_id: 전략 고유 ID (필수)
            strategy_name: 전략 이름 (필수)
            strategy_type: 전략 유형 (기본값: "entry")
            created_by: 생성자 ID (선택)
            strategy_config: 전략 설정 (선택)
        """
        super().__init__()

        # 필수 필드 검증
        if not strategy_id:
            raise ValueError("strategy_id는 필수 필드입니다")
        if not strategy_name:
            raise ValueError("strategy_name은 필수 필드입니다")

        self._strategy_id = strategy_id
        self._strategy_name = strategy_name
        self._strategy_type = strategy_type
        self._created_by = created_by
        self._strategy_config = strategy_config or {}

    @property
    def strategy_id(self) -> str:
        return self._strategy_id

    @property
    def strategy_name(self) -> str:
        return self._strategy_name

    @property
    def strategy_type(self) -> str:
        return self._strategy_type

    @property
    def created_by(self) -> Optional[str]:
        return self._created_by

    @property
    def strategy_config(self) -> Dict[str, Any]:
        return self._strategy_config

    @property
    def event_type(self) -> str:
        return "strategy.created"

    @property
    def aggregate_id(self) -> str:
        return self._strategy_id

class StrategyUpdated(DomainEvent):
    """전략 수정 이벤트"""

    def __init__(self, strategy_id: str, strategy_name: str,
                 updated_fields: Optional[Dict[str, Any]] = None,
                 previous_version: Optional[str] = None,
                 new_version: Optional[str] = None):
        """
        전략 수정 이벤트 초기화

        Args:
            strategy_id: 전략 고유 ID (필수)
            strategy_name: 전략 이름 (필수)
            updated_fields: 수정된 필드들 (선택)
            previous_version: 이전 버전 (선택)
            new_version: 새 버전 (선택)
        """
        super().__init__()

        # 필수 필드 검증
        if not strategy_id:
            raise ValueError("strategy_id는 필수 필드입니다")
        if not strategy_name:
            raise ValueError("strategy_name은 필수 필드입니다")

        self._strategy_id = strategy_id
        self._strategy_name = strategy_name
        self._updated_fields = updated_fields or {}
        self._previous_version = previous_version
        self._new_version = new_version

    @property
    def strategy_id(self) -> str:
        return self._strategy_id

    @property
    def strategy_name(self) -> str:
        return self._strategy_name

    @property
    def updated_fields(self) -> Dict[str, Any]:
        return self._updated_fields

    @property
    def previous_version(self) -> Optional[str]:
        return self._previous_version

    @property
    def new_version(self) -> Optional[str]:
        return self._new_version

    @property
    def event_type(self) -> str:
        return "strategy.updated"

    @property
    def aggregate_id(self) -> str:
        return self._strategy_id

class StrategyDeleted(DomainEvent):
    """전략 삭제 이벤트"""

    def __init__(self, strategy_id: str, strategy_name: str,
                 deleted_by: Optional[str] = None,
                 deletion_reason: Optional[str] = None):
        """
        전략 삭제 이벤트 초기화

        Args:
            strategy_id: 전략 고유 ID (필수)
            strategy_name: 전략 이름 (필수)
            deleted_by: 삭제 실행자 (선택)
            deletion_reason: 삭제 사유 (선택)
        """
        super().__init__()

        # 필수 필드 검증
        if not strategy_id:
            raise ValueError("strategy_id는 필수 필드입니다")
        if not strategy_name:
            raise ValueError("strategy_name은 필수 필드입니다")

        self._strategy_id = strategy_id
        self._strategy_name = strategy_name
        self._deleted_by = deleted_by
        self._deletion_reason = deletion_reason

    @property
    def strategy_id(self) -> str:
        return self._strategy_id

    @property
    def strategy_name(self) -> str:
        return self._strategy_name

    @property
    def deleted_by(self) -> Optional[str]:
        return self._deleted_by

    @property
    def deletion_reason(self) -> Optional[str]:
        return self._deletion_reason

    @property
    def event_type(self) -> str:
        return "strategy.deleted"

    @property
    def aggregate_id(self) -> str:
        return self._strategy_id

class StrategyActivated(DomainEvent):
    """전략 활성화 이벤트"""

    def __init__(self, strategy_id: str, strategy_name: str,
                 activated_by: Optional[str] = None,
                 activation_reason: Optional[str] = None):
        """
        전략 활성화 이벤트 초기화

        Args:
            strategy_id: 전략 고유 ID (필수)
            strategy_name: 전략 이름 (필수)
            activated_by: 활성화 실행자 (선택)
            activation_reason: 활성화 사유 (선택)
        """
        super().__init__()

        # 필수 필드 검증
        if not strategy_id:
            raise ValueError("strategy_id는 필수 필드입니다")
        if not strategy_name:
            raise ValueError("strategy_name은 필수 필드입니다")

        self._strategy_id = strategy_id
        self._strategy_name = strategy_name
        self._activated_by = activated_by
        self._activation_reason = activation_reason

    @property
    def strategy_id(self) -> str:
        return self._strategy_id

    @property
    def strategy_name(self) -> str:
        return self._strategy_name

    @property
    def activated_by(self) -> Optional[str]:
        return self._activated_by

    @property
    def activation_reason(self) -> Optional[str]:
        return self._activation_reason

    @property
    def event_type(self) -> str:
        return "strategy.activated"

    @property
    def aggregate_id(self) -> str:
        return self._strategy_id

class StrategyDeactivated(DomainEvent):
    """전략 비활성화 이벤트"""

    def __init__(self, strategy_id: str, strategy_name: str,
                 deactivated_by: Optional[str] = None,
                 deactivation_reason: Optional[str] = None):
        """
        전략 비활성화 이벤트 초기화

        Args:
            strategy_id: 전략 고유 ID (필수)
            strategy_name: 전략 이름 (필수)
            deactivated_by: 비활성화 실행자 (선택)
            deactivation_reason: 비활성화 사유 (선택)
        """
        super().__init__()

        # 필수 필드 검증
        if not strategy_id:
            raise ValueError("strategy_id는 필수 필드입니다")
        if not strategy_name:
            raise ValueError("strategy_name은 필수 필드입니다")

        self._strategy_id = strategy_id
        self._strategy_name = strategy_name
        self._deactivated_by = deactivated_by
        self._deactivation_reason = deactivation_reason

    @property
    def strategy_id(self) -> str:
        return self._strategy_id

    @property
    def strategy_name(self) -> str:
        return self._strategy_name

    @property
    def deactivated_by(self) -> Optional[str]:
        return self._deactivated_by

    @property
    def deactivation_reason(self) -> Optional[str]:
        return self._deactivation_reason

    @property
    def event_type(self) -> str:
        return "strategy.deactivated"

    @property
    def aggregate_id(self) -> str:
        return self._strategy_id

class StrategyBacktestCompleted(DomainEvent):
    """전략 백테스트 완료 이벤트"""

    def __init__(self, strategy_id: str, backtest_id: str, symbol: str,
                 total_return: float, max_drawdown: float, sharpe_ratio: float,
                 win_rate: float = 0.0, total_trades: int = 0,
                 completed_at: Optional[datetime] = None,
                 additional_metrics: Optional[Dict[str, Any]] = None):
        """
        전략 백테스트 완료 이벤트 초기화

        Args:
            strategy_id: 전략 고유 ID (필수)
            backtest_id: 백테스트 고유 ID (필수)
            symbol: 거래 심볼 (필수)
            total_return: 총 수익률 (필수)
            max_drawdown: 최대 손실률 (필수)
            sharpe_ratio: 샤프 비율 (필수)
            win_rate: 승률 (기본값: 0.0)
            total_trades: 총 거래 수 (기본값: 0)
            completed_at: 완료 시간 (선택, 기본값: 현재 시간)
            additional_metrics: 추가 지표 (선택)
        """
        super().__init__()

        # datetime import 확인
        from datetime import datetime as dt

        # 필수 필드 검증
        if not strategy_id:
            raise ValueError("strategy_id는 필수 필드입니다")
        if not backtest_id:
            raise ValueError("backtest_id는 필수 필드입니다")
        if not symbol:
            raise ValueError("symbol은 필수 필드입니다")
        if total_return is None:
            raise ValueError("total_return은 필수 필드입니다")
        if max_drawdown is None:
            raise ValueError("max_drawdown은 필수 필드입니다")
        if sharpe_ratio is None:
            raise ValueError("sharpe_ratio는 필수 필드입니다")

        self._strategy_id = strategy_id
        self._backtest_id = backtest_id
        self._symbol = symbol
        self._total_return = total_return
        self._max_drawdown = max_drawdown
        self._sharpe_ratio = sharpe_ratio
        self._win_rate = win_rate
        self._total_trades = total_trades
        self._completed_at = completed_at or dt.now()
        self._additional_metrics = additional_metrics or {}

    @property
    def strategy_id(self) -> str:
        return self._strategy_id

    @property
    def backtest_id(self) -> str:
        return self._backtest_id

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def total_return(self) -> float:
        return self._total_return

    @property
    def max_drawdown(self) -> float:
        return self._max_drawdown

    @property
    def sharpe_ratio(self) -> float:
        return self._sharpe_ratio

    @property
    def win_rate(self) -> float:
        return self._win_rate

    @property
    def total_trades(self) -> int:
        return self._total_trades

    @property
    def completed_at(self) -> datetime:
        return self._completed_at

    @property
    def additional_metrics(self) -> Dict[str, Any]:
        return self._additional_metrics

    @property
    def event_type(self) -> str:
        return "strategy.backtest.completed"

    @property
    def aggregate_id(self) -> str:
        return self._strategy_id

class StrategyValidated(DomainEvent):
    """전략 호환성 검증 성공 이벤트"""

    def __init__(self, strategy_id: str,
                 validation_type: str = "compatibility",
                 validation_result: str = "success",
                 validation_details: Optional[Dict[str, Any]] = None,
                 confidence_score: float = 1.0):
        """
        전략 검증 이벤트 초기화

        Args:
            strategy_id: 전략 고유 ID (필수)
            validation_type: 검증 유형 (기본값: "compatibility")
            validation_result: 검증 결과 (기본값: "success")
            validation_details: 검증 상세 정보 (선택)
            confidence_score: 신뢰도 점수 (기본값: 1.0)
        """
        super().__init__()

        # 필수 필드 검증
        if not strategy_id:
            raise ValueError("strategy_id는 필수 필드입니다")

        self._strategy_id = strategy_id
        self._validation_type = validation_type
        self._validation_result = validation_result
        self._validation_details = validation_details or {}
        self._confidence_score = confidence_score

    @property
    def strategy_id(self) -> str:
        return self._strategy_id

    @property
    def validation_type(self) -> str:
        return self._validation_type

    @property
    def validation_result(self) -> str:
        return self._validation_result

    @property
    def validation_details(self) -> Dict[str, Any]:
        return self._validation_details

    @property
    def confidence_score(self) -> float:
        return self._confidence_score

    @property
    def event_type(self) -> str:
        return "strategy.validated"

    @property
    def aggregate_id(self) -> str:
        return self._strategy_id

class StrategyValidationFailed(DomainEvent):
    """전략 호환성 검증 실패 이벤트"""

    def __init__(self, strategy_id: str,
                 validation_type: str = "compatibility",
                 validation_result: str = "failed",
                 error_message: str = "Validation failed",
                 error_details: Optional[Dict[str, Any]] = None):
        """
        전략 검증 실패 이벤트 초기화

        Args:
            strategy_id: 전략 고유 ID (필수)
            validation_type: 검증 유형 (기본값: "compatibility")
            validation_result: 검증 결과 (기본값: "failed")
            error_message: 오류 메시지 (기본값: "Validation failed")
            error_details: 오류 상세 정보 (선택)
        """
        super().__init__()

        # 필수 필드 검증
        if not strategy_id:
            raise ValueError("strategy_id는 필수 필드입니다")

        self._strategy_id = strategy_id
        self._validation_type = validation_type
        self._validation_result = validation_result
        self._error_message = error_message
        self._error_details = error_details or {}

    @property
    def strategy_id(self) -> str:
        return self._strategy_id

    @property
    def validation_type(self) -> str:
        return self._validation_type

    @property
    def validation_result(self) -> str:
        return self._validation_result

    @property
    def error_message(self) -> str:
        return self._error_message

    @property
    def error_details(self) -> Dict[str, Any]:
        return self._error_details

    @property
    def event_type(self) -> str:
        return "strategy.validation_failed"

    @property
    def aggregate_id(self) -> str:
        return self._strategy_id
