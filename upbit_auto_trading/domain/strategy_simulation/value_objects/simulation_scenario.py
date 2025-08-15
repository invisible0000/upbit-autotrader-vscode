"""
전략 시뮬레이션 시나리오 Value Object
"""

from enum import Enum
from typing import List, Tuple


class SimulationScenario(Enum):
    """
    전략 시뮬레이션 시나리오 타입

    전략 관리 화면에서 사용하는 미니 시뮬레이션 시나리오
    각 시나리오는 특정 시장 상황을 모델링
    """

    # 추세 기반 시나리오
    UPTREND = "상승 추세"
    DOWNTREND = "하락 추세"
    SIDEWAYS = "횡보 장세"

    # 변동성 기반 시나리오
    HIGH_VOLATILITY = "변동성 확대"

    # 급변 시나리오
    SURGE = "급등"
    CRASH = "급락"

    @classmethod
    def get_all_scenarios(cls) -> List['SimulationScenario']:
        """모든 시나리오 반환"""
        return list(cls)

    @classmethod
    def get_scenario_color(cls, scenario: 'SimulationScenario') -> str:
        """시나리오별 UI 색상 반환"""
        colors = {
            cls.UPTREND: "#28a745",        # 녹색
            cls.DOWNTREND: "#dc3545",      # 빨간색
            cls.SIDEWAYS: "#6c757d",       # 회색
            cls.HIGH_VOLATILITY: "#fd7e14", # 주황색
            cls.SURGE: "#20c997",          # 청록색
            cls.CRASH: "#e83e8c"           # 자주색
        }
        return colors.get(scenario, "#6c757d")

    @classmethod
    def get_scenario_description(cls, scenario: 'SimulationScenario') -> str:
        """시나리오별 상세 설명"""
        descriptions = {
            cls.UPTREND: "지속적인 상승 추세 시장 상황",
            cls.DOWNTREND: "지속적인 하락 추세 시장 상황",
            cls.SIDEWAYS: "특정 범위 내 횡보하는 시장 상황",
            cls.HIGH_VOLATILITY: "높은 변동성을 보이는 시장 상황",
            cls.SURGE: "단기간 급격한 상승을 보이는 시장 상황",
            cls.CRASH: "단기간 급격한 하락을 보이는 시장 상황"
        }
        return descriptions.get(scenario, f"{scenario.value} 시나리오")

    @classmethod
    def get_grid_layout(cls) -> List[List['SimulationScenario']]:
        """UI 그리드 레이아웃용 시나리오 배열 (3x2)"""
        return [
            [cls.UPTREND, cls.DOWNTREND, cls.SIDEWAYS],
            [cls.HIGH_VOLATILITY, cls.SURGE, cls.CRASH]
        ]

    def get_risk_level(self) -> str:
        """시나리오별 위험도 레벨"""
        risk_levels = {
            SimulationScenario.UPTREND: "낮음",
            SimulationScenario.DOWNTREND: "중간",
            SimulationScenario.SIDEWAYS: "낮음",
            SimulationScenario.HIGH_VOLATILITY: "높음",
            SimulationScenario.SURGE: "중간",
            SimulationScenario.CRASH: "높음"
        }
        return risk_levels.get(self, "알 수 없음")

    def is_trending_scenario(self) -> bool:
        """추세 기반 시나리오 여부"""
        return self in [
            SimulationScenario.UPTREND,
            SimulationScenario.DOWNTREND
        ]

    def is_high_risk_scenario(self) -> bool:
        """고위험 시나리오 여부"""
        return self in [
            SimulationScenario.HIGH_VOLATILITY,
            SimulationScenario.CRASH
        ]
