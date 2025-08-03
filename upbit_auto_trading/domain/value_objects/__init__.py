"""
값 객체 (Value Objects)

도메인의 개념을 나타내는 불변 객체들입니다.
값 자체가 중요하며, 동일한 값을 가진 객체들은 서로 교환 가능합니다.

주요 값 객체:
- StrategyId: 전략 식별자
- TriggerId: 트리거 식별자
- ComparisonOperator: 비교 연산자
- ConflictResolution: 충돌 해결 방식
- StrategyRole: 전략 역할
- SignalType: 신호 타입
- StrategyConfig: 전략 설정
"""

from .strategy_id import StrategyId
from .trigger_id import TriggerId
from .comparison_operator import ComparisonOperator
from .conflict_resolution import ConflictResolution
from .strategy_role import StrategyRole
from .signal_type import SignalType
from .strategy_config import StrategyConfig

__all__ = [
    "StrategyId",
    "TriggerId",
    "ComparisonOperator",
    "ConflictResolution",
    "StrategyRole",
    "SignalType",
    "StrategyConfig"
]
