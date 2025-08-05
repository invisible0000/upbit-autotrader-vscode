"""
Domain Entity ↔ Database Record 매핑

Domain Layer의 엔티티들과 데이터베이스 레코드 간의 변환을 담당합니다.
타입 안전한 변환과 JSON 데이터의 올바른 직렬화/역직렬화를 보장합니다.

주요 Mapper들:
- StrategyMapper: Strategy 엔티티 ↔ strategies 테이블
- TriggerMapper: Trigger 엔티티 ↔ strategy_triggers 테이블
- TradingVariableMapper: TradingVariable ↔ tv_trading_variables 테이블 (향후)
- BacktestResultMapper: BacktestResult ↔ backtest_results 테이블 (향후)
"""

__all__ = []
