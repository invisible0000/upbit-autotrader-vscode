"""
시뮬레이션 데이터 UseCase
Application Layer - 시뮬레이션 데이터 비즈니스 로직
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from upbit_auto_trading.infrastructure.repositories.simulation_data_repository import SimulationDataRepository
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("SimulationDataUseCase")


@dataclass(frozen=True)
class ScenarioDataDTO:
    """시나리오 데이터 DTO"""
    current_value: float
    price_data: List[float]
    scenario: str
    data_source: str
    period: str
    base_value: float
    change_percent: float
    data_points: int


@dataclass(frozen=True)
class ScenarioSummaryDTO:
    """시나리오 요약 DTO"""
    scenario: str
    data_points: int
    date_range: str
    price_range: Dict[str, float]
    total_return: float
    volatility: float
    indicators: Dict[str, Optional[float]]


class LoadSimulationDataUseCase:
    """시뮬레이션 데이터 로드 UseCase"""

    def __init__(self, repository: SimulationDataRepository):
        self.repository = repository
        logger.debug("LoadSimulationDataUseCase 초기화")

    def execute(self, scenario: str, length: int = 100) -> ScenarioDataDTO:
        """
        시나리오별 시뮬레이션 데이터 로드

        Args:
            scenario: 시나리오명
            length: 데이터 길이

        Returns:
            ScenarioDataDTO
        """
        try:
            logger.info(f"시뮬레이션 데이터 로드 시작: {scenario}")

            # Repository에서 데이터 로드
            df = self.repository.load_scenario_data(scenario, length)

            if df is None or df.empty:
                logger.warning(f"데이터 없음 - 폴백 데이터 생성: {scenario}")
                return self._create_fallback_dto(scenario, length)

            # 기술적 지표 계산
            df = self.repository.calculate_technical_indicators(df)

            # 실제 길이에 맞게 자르기
            if len(df) > length:
                df = df.tail(length)

            # DTO 생성
            result = ScenarioDataDTO(
                current_value=float(df['close'].iloc[-1]),
                price_data=df['close'].tolist(),
                scenario=scenario,
                data_source="real_market_data",
                period=f"{df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}",
                base_value=float(df['close'].iloc[0]),
                change_percent=float((df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100),
                data_points=len(df)
            )

            logger.info(f"시뮬레이션 데이터 로드 완료: {scenario} ({len(df)}개)")
            return result

        except Exception as e:
            logger.error(f"시뮬레이션 데이터 로드 실패: {e}")
            return self._create_fallback_dto(scenario, length)

    def _create_fallback_dto(self, scenario: str, length: int) -> ScenarioDataDTO:
        """폴백 DTO 생성"""
        import numpy as np

        base_value = 50000000  # 5천만원 (BTC 기준)

        # 시나리오별 패턴
        if scenario == "급등":
            trend = np.linspace(0, base_value * 0.3, length)
        elif scenario == "상승추세":
            trend = np.linspace(0, base_value * 0.1, length)
        elif scenario == "하락추세":
            trend = np.linspace(0, -base_value * 0.1, length)
        elif scenario == "급락":
            trend = np.linspace(0, -base_value * 0.2, length)
        else:  # 횡보
            trend = np.sin(np.linspace(0, 4 * np.pi, length)) * base_value * 0.02

        noise = np.random.randn(length) * base_value * 0.01
        price_data = base_value + trend + noise
        price_data = np.maximum(price_data, base_value * 0.1)  # 최소값 보장

        return ScenarioDataDTO(
            current_value=float(price_data[-1]),
            price_data=price_data.tolist(),
            scenario=scenario,
            data_source="fallback_generated",
            period="simulated_period",
            base_value=base_value,
            change_percent=float((price_data[-1] / base_value - 1) * 100),
            data_points=length
        )


class GetAvailableScenariosUseCase:
    """사용 가능한 시나리오 목록 UseCase"""

    def __init__(self, repository: SimulationDataRepository):
        self.repository = repository
        logger.debug("GetAvailableScenariosUseCase 초기화")

    def execute(self) -> List[str]:
        """사용 가능한 시나리오 목록 반환"""
        try:
            scenarios = self.repository.get_available_scenarios()
            logger.info(f"사용 가능한 시나리오: {len(scenarios)}개")
            return scenarios
        except Exception as e:
            logger.error(f"시나리오 목록 로드 실패: {e}")
            return ["급등", "상승추세", "횡보", "하락추세", "급락"]  # 기본값


class GetScenarioSummaryUseCase:
    """시나리오 요약 정보 UseCase"""

    def __init__(self, repository: SimulationDataRepository):
        self.repository = repository
        logger.debug("GetScenarioSummaryUseCase 초기화")

    def execute(self, scenario: str) -> ScenarioSummaryDTO:
        """시나리오 요약 정보 반환"""
        try:
            logger.debug(f"시나리오 요약 생성: {scenario}")

            summary_data = self.repository.get_scenario_summary(scenario)

            if not summary_data:
                return self._create_fallback_summary(scenario)

            return ScenarioSummaryDTO(
                scenario=summary_data['scenario'],
                data_points=summary_data['data_points'],
                date_range=summary_data['date_range'],
                price_range=summary_data['price_range'],
                total_return=summary_data['total_return'],
                volatility=summary_data['volatility'],
                indicators=summary_data['indicators']
            )

        except Exception as e:
            logger.error(f"시나리오 요약 생성 실패: {e}")
            return self._create_fallback_summary(scenario)

    def _create_fallback_summary(self, scenario: str) -> ScenarioSummaryDTO:
        """폴백 요약 DTO"""
        return ScenarioSummaryDTO(
            scenario=scenario,
            data_points=0,
            date_range="데이터 없음",
            price_range={
                'min': 0.0,
                'max': 0.0,
                'start': 0.0,
                'end': 0.0
            },
            total_return=0.0,
            volatility=0.0,
            indicators={'rsi_avg': None, 'volume_avg': 0.0}
        )
