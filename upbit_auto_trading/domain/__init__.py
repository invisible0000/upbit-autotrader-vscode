"""
도메인 계층 (Domain Layer)

매매 전략의 핵심 비즈니스 로직을 순수한 도메인 모델로 구현한 계층입니다.
UI와 완전히 분리된 도메인 엔티티들로 구성되어 있습니다.

구조:
- entities/: 도메인 엔티티들 (Strategy, Trigger, ManagementRule 등)
- value_objects/: 값 객체들 (StrategyId, TriggerId, ComparisonOperator 등)  
- exceptions/: 도메인 계층 전용 예외들
"""

__version__ = "1.0.0"
__author__ = "Upbit Auto Trading System"
