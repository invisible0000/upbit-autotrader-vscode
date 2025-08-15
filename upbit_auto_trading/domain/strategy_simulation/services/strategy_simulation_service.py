"""
전략 시뮬레이션 도메인 서비스
"""

from typing import List, Optional, Dict, Any
import pandas as pd

from upbit_auto_trading.domain.strategy_simulation.entities.data_source import DataSource
from upbit_auto_trading.domain.strategy_simulation.value_objects.data_source_type import DataSourceType
from upbit_auto_trading.domain.strategy_simulation.value_objects.simulation_scenario import SimulationScenario
from upbit_auto_trading.domain.strategy_simulation.repositories.i_strategy_simulation_repository import (
    IStrategySimulationDataRepository,
    IStrategySimulationEngineRepository
)
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("StrategySimulationService")


class StrategySimulationService:
    """
    전략 시뮬레이션 도메인 서비스

    전략 관리 화면 전용 미니 시뮬레이션 비즈니스 로직
    실제 백테스팅과는 별개의 도메인
    """

    def __init__(
        self,
        data_repository: IStrategySimulationDataRepository,
        engine_repository: IStrategySimulationEngineRepository
    ):
        self._data_repository = data_repository
        self._engine_repository = engine_repository
        self._user_preference: Optional[DataSourceType] = None

        logger.debug("전략 시뮬레이션 도메인 서비스 초기화")

    def get_recommended_data_source(self) -> Optional[DataSource]:
        """추천 데이터 소스 반환"""
        available_sources = self._data_repository.get_available_data_sources()

        # 1. 사용자 선호도 확인
        if self._user_preference:
            for source in available_sources:
                if source.source_type == self._user_preference and source.is_available:
                    logger.debug(f"사용자 선호 데이터 소스 반환: {source.name}")
                    return source

        # 2. 우선순위 순서로 검색
        priority_order = DataSourceType.get_priority_order()
        for source_type in priority_order:
            for source in available_sources:
                if source.source_type == source_type and source.is_available:
                    logger.debug(f"우선순위 기준 데이터 소스 반환: {source.name}")
                    return source

        logger.warning("사용 가능한 데이터 소스가 없습니다")
        return None

    def set_user_preference(self, source_type: DataSourceType) -> bool:
        """사용자 선호 데이터 소스 설정"""
        if not self._data_repository.check_data_source_availability(source_type):
            logger.warning(f"사용할 수 없는 데이터 소스: {source_type.value}")
            return False

        self._user_preference = source_type
        logger.info(f"사용자 선호 데이터 소스 설정: {source_type.value}")
        return True

    def get_user_preference(self) -> Optional[DataSourceType]:
        """사용자 선호 데이터 소스 반환"""
        return self._user_preference

    def validate_scenario_compatibility(
        self,
        scenario: SimulationScenario,
        source_type: DataSourceType
    ) -> bool:
        """시나리오와 데이터 소스 호환성 검증"""
        try:
            # 데이터 소스 사용 가능 확인
            if not self._data_repository.check_data_source_availability(source_type):
                return False

            # 엔진 호환성 확인
            capabilities = self._engine_repository.get_engine_capabilities(source_type)

            # 시나리오별 특별 요구사항 확인
            if scenario.is_high_risk_scenario():
                # 고위험 시나리오는 더 정확한 데이터 필요
                if source_type == DataSourceType.SIMPLE_FALLBACK:
                    logger.warning(f"고위험 시나리오 {scenario.value}에는 폴백 데이터 부적합")
                    return False

            return True

        except Exception as e:
            logger.error(f"시나리오 호환성 검증 실패: {e}")
            return False

    def get_optimal_data_length_for_scenario(self, scenario: SimulationScenario) -> int:
        """시나리오별 최적 데이터 길이 반환"""
        length_mapping = {
            SimulationScenario.UPTREND: 150,        # 장기 추세 확인
            SimulationScenario.DOWNTREND: 150,      # 장기 추세 확인
            SimulationScenario.SIDEWAYS: 100,       # 중기 패턴 확인
            SimulationScenario.HIGH_VOLATILITY: 80, # 단기 변동성
            SimulationScenario.SURGE: 60,           # 단기 급변
            SimulationScenario.CRASH: 60            # 단기 급변
        }

        optimal_length = length_mapping.get(scenario, 100)
        logger.debug(f"시나리오 {scenario.value} 최적 데이터 길이: {optimal_length}")
        return optimal_length

    def calculate_scenario_statistics(
        self,
        data: pd.DataFrame,
        scenario: SimulationScenario
    ) -> Dict[str, Any]:
        """시나리오별 통계 계산"""
        if data is None or data.empty:
            return {}

        try:
            close_prices = data['close']

            # 기본 통계
            stats = {
                'start_price': float(close_prices.iloc[0]),
                'end_price': float(close_prices.iloc[-1]),
                'min_price': float(close_prices.min()),
                'max_price': float(close_prices.max()),
                'price_change_percent': float((close_prices.iloc[-1] / close_prices.iloc[0] - 1) * 100),
                'volatility': float(close_prices.pct_change().std() * 100),
                'data_points': len(data)
            }

            # 시나리오별 특화 통계
            if scenario.is_trending_scenario():
                # 추세 강도 계산
                price_changes = close_prices.diff()
                positive_changes = (price_changes > 0).sum()
                stats['trend_strength'] = float(positive_changes / len(price_changes) * 100)

            if scenario.is_high_risk_scenario():
                # 위험도 지표 계산
                daily_returns = close_prices.pct_change()
                stats['max_drawdown'] = float(((close_prices / close_prices.cummax()) - 1).min() * 100)
                stats['sharp_movements'] = int((abs(daily_returns) > daily_returns.std() * 2).sum())

            return stats

        except Exception as e:
            logger.error(f"시나리오 통계 계산 실패: {e}")
            return {}

    def cleanup_resources(self) -> None:
        """리소스 정리"""
        try:
            # 모든 엔진 리소스 정리
            for source_type in DataSourceType.get_all_types():
                self._engine_repository.cleanup_engine_resources(source_type)

            logger.debug("전략 시뮬레이션 리소스 정리 완료")

        except Exception as e:
            logger.error(f"리소스 정리 실패: {e}")
