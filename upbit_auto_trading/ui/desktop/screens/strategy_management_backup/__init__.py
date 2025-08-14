"""
전략 관리 스크린 패키지
컴포넌트 기반 시스템으로 완전 리팩토링됨
"""

from .strategy_management_screen import StrategyManagementScreen

# 레거시 IntegratedConditionManager는 더 이상 export하지 않음
# 모든 기능이 TriggerBuilderScreen 컴포넌트로 이관됨

__all__ = ['StrategyManagementScreen']
