"""
호환성 검증 UseCase
데이터 소스와 시나리오 간 호환성 검증
"""

from typing import Dict, List

from upbit_auto_trading.application.dto.strategy_simulation.strategy_simulation_dto import (
    SimulationCompatibilityDTO
)
from upbit_auto_trading.domain.strategy_simulation.value_objects.data_source_type import DataSourceType
from upbit_auto_trading.domain.strategy_simulation.value_objects.simulation_scenario import SimulationScenario
from upbit_auto_trading.domain.strategy_simulation.services.strategy_simulation_service import StrategySimulationService
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("CompatibilityUseCase")


class ValidateCompatibilityUseCase:
    """
    데이터 소스-시나리오 호환성 검증 UseCase
    """

    def __init__(self, simulation_service: StrategySimulationService):
        self._simulation_service = simulation_service
        logger.debug("호환성 검증 UseCase 초기화")

    def execute(self, source_type_value: str, scenario_value: str) -> SimulationCompatibilityDTO:
        """특정 조합의 호환성 검증"""
        try:
            source_type = DataSourceType(source_type_value)
            scenario = SimulationScenario(scenario_value)

            # 도메인 서비스를 통한 호환성 검증
            is_compatible = self._simulation_service.validate_compatibility(source_type, scenario)

            # 호환성 이유 분석
            compatibility_reason = self._analyze_compatibility_reason(source_type, scenario, is_compatible)

            # 권장사항 생성
            recommendations = self._generate_recommendations(source_type, scenario, is_compatible)

            # DTO 생성
            result = SimulationCompatibilityDTO.create(
                source_type_value=source_type_value,
                scenario_value=scenario_value,
                is_compatible=is_compatible,
                reason=compatibility_reason,
                recommendations=recommendations
            )

            logger.debug(f"호환성 검증 완료: {source_type_value} + {scenario_value} = {is_compatible}")
            return result

        except ValueError as e:
            logger.error(f"잘못된 파라미터: {e}")
            return SimulationCompatibilityDTO.create(
                source_type_value=source_type_value,
                scenario_value=scenario_value,
                is_compatible=False,
                reason=f"잘못된 파라미터: {str(e)}",
                recommendations=["올바른 데이터 소스 타입과 시나리오를 선택해주세요"]
            )
        except Exception as e:
            logger.error(f"호환성 검증 실패: {e}")
            return SimulationCompatibilityDTO.create(
                source_type_value=source_type_value,
                scenario_value=scenario_value,
                is_compatible=False,
                reason=f"검증 중 오류 발생: {str(e)}",
                recommendations=["시스템 관리자에게 문의해주세요"]
            )

    def _analyze_compatibility_reason(self, source_type: DataSourceType, scenario: SimulationScenario, is_compatible: bool) -> str:
        """호환성 판단 이유 분석"""
        if is_compatible:
            return f"{source_type.get_display_name()}는 {scenario.get_display_name()} 시나리오를 지원합니다"

        # 비호환 이유 분석
        if source_type == DataSourceType.FALLBACK:
            return "Fallback 데이터 소스는 제한된 시나리오만 지원합니다"

        if scenario == SimulationScenario.MARKET_CRASH and source_type == DataSourceType.EMBEDDED:
            return "임베디드 데이터에는 급락 패턴이 포함되어 있지 않습니다"

        return f"{source_type.get_display_name()}와 {scenario.get_display_name()} 조합은 지원되지 않습니다"

    def _generate_recommendations(self, source_type: DataSourceType, scenario: SimulationScenario, is_compatible: bool) -> List[str]:
        """권장사항 생성"""
        if is_compatible:
            return [
                "이 조합으로 시뮬레이션을 실행할 수 있습니다",
                "최적의 결과를 위해 적절한 기간을 선택해주세요"
            ]

        recommendations = []

        # 데이터 소스별 권장사항
        if source_type == DataSourceType.FALLBACK:
            recommendations.append("더 안정적인 데이터 소스를 선택해보세요")
            recommendations.append("Real DB 또는 Synthetic 데이터 소스 사용 권장")
        elif source_type == DataSourceType.EMBEDDED:
            recommendations.append("임베디드 데이터는 기본 패턴만 지원합니다")
            if scenario in [SimulationScenario.MARKET_CRASH, SimulationScenario.MARKET_SURGE]:
                recommendations.append("극단적 시나리오는 Synthetic 데이터 사용 권장")

        # 시나리오별 권장사항
        if scenario == SimulationScenario.MARKET_CRASH:
            recommendations.append("급락 시나리오는 Real DB 또는 Synthetic 데이터 권장")
        elif scenario == SimulationScenario.MARKET_SURGE:
            recommendations.append("급등 시나리오는 Real DB 또는 Synthetic 데이터 권장")

        return recommendations if recommendations else ["다른 조합을 시도해보세요"]


class GetCompatibilityMatrixUseCase:
    """
    전체 호환성 매트릭스 조회 UseCase
    """

    def __init__(self, simulation_service: StrategySimulationService):
        self._simulation_service = simulation_service
        logger.debug("호환성 매트릭스 UseCase 초기화")

    def execute(self) -> Dict[str, Dict[str, bool]]:
        """전체 데이터 소스-시나리오 호환성 매트릭스 반환"""
        try:
            compatibility_matrix = {}

            # 모든 데이터 소스 타입 순회
            for source_type in DataSourceType:
                source_compatibility = {}

                # 모든 시나리오와의 호환성 확인
                for scenario in SimulationScenario:
                    is_compatible = self._simulation_service.validate_compatibility(source_type, scenario)
                    source_compatibility[scenario.value] = is_compatible

                compatibility_matrix[source_type.value] = source_compatibility

            logger.debug(f"호환성 매트릭스 생성 완료: {len(compatibility_matrix)}개 데이터 소스")
            return compatibility_matrix

        except Exception as e:
            logger.error(f"호환성 매트릭스 생성 실패: {e}")
            return {}


class GetRecommendedCombinationsUseCase:
    """
    권장 조합 제안 UseCase
    """

    def __init__(self, simulation_service: StrategySimulationService):
        self._simulation_service = simulation_service
        logger.debug("권장 조합 제안 UseCase 초기화")

    def execute(self, priority: str = "balanced") -> List[Dict[str, str]]:
        """사용자 우선순위에 따른 권장 조합 반환"""
        try:
            recommendations = []

            if priority == "speed":
                # 속도 우선: 임베디드 → 합성 → 실제 DB
                recommendations.extend(self._get_speed_optimized_combinations())
            elif priority == "accuracy":
                # 정확도 우선: 실제 DB → 합성 → 임베디드
                recommendations.extend(self._get_accuracy_optimized_combinations())
            else:  # balanced
                # 균형: 합성 → 실제 DB → 임베디드
                recommendations.extend(self._get_balanced_combinations())

            logger.debug(f"권장 조합 생성 완료: {len(recommendations)}개 ({priority} 우선)")
            return recommendations[:6]  # 상위 6개만 반환 (3x2 그리드)

        except Exception as e:
            logger.error(f"권장 조합 생성 실패: {e}")
            return []

    def _get_speed_optimized_combinations(self) -> List[Dict[str, str]]:
        """속도 최적화 조합"""
        return [
            {
                "data_source": DataSourceType.EMBEDDED.value,
                "scenario": SimulationScenario.NORMAL_TREND.value,
                "reason": "즉시 실행 가능한 기본 조합"
            },
            {
                "data_source": DataSourceType.EMBEDDED.value,
                "scenario": SimulationScenario.SIDEWAYS_MARKET.value,
                "reason": "빠른 횡보 시장 분석"
            },
            {
                "data_source": DataSourceType.SYNTHETIC.value,
                "scenario": SimulationScenario.MARKET_SURGE.value,
                "reason": "빠른 급등 시나리오 테스트"
            },
            {
                "data_source": DataSourceType.SYNTHETIC.value,
                "scenario": SimulationScenario.MARKET_CRASH.value,
                "reason": "빠른 급락 시나리오 테스트"
            },
            {
                "data_source": DataSourceType.SYNTHETIC.value,
                "scenario": SimulationScenario.HIGH_VOLATILITY.value,
                "reason": "빠른 변동성 분석"
            },
            {
                "data_source": DataSourceType.SYNTHETIC.value,
                "scenario": SimulationScenario.NORMAL_TREND.value,
                "reason": "향상된 합성 데이터 분석"
            }
        ]

    def _get_accuracy_optimized_combinations(self) -> List[Dict[str, str]]:
        """정확도 최적화 조합"""
        return [
            {
                "data_source": DataSourceType.REAL_DB.value,
                "scenario": SimulationScenario.NORMAL_TREND.value,
                "reason": "실제 시장 데이터 기반 분석"
            },
            {
                "data_source": DataSourceType.REAL_DB.value,
                "scenario": SimulationScenario.HIGH_VOLATILITY.value,
                "reason": "실제 변동성 패턴 분석"
            },
            {
                "data_source": DataSourceType.REAL_DB.value,
                "scenario": SimulationScenario.SIDEWAYS_MARKET.value,
                "reason": "실제 횡보 패턴 분석"
            },
            {
                "data_source": DataSourceType.SYNTHETIC.value,
                "scenario": SimulationScenario.MARKET_CRASH.value,
                "reason": "정교한 급락 시나리오"
            },
            {
                "data_source": DataSourceType.SYNTHETIC.value,
                "scenario": SimulationScenario.MARKET_SURGE.value,
                "reason": "정교한 급등 시나리오"
            },
            {
                "data_source": DataSourceType.EMBEDDED.value,
                "scenario": SimulationScenario.NORMAL_TREND.value,
                "reason": "기준 데이터 비교"
            }
        ]

    def _get_balanced_combinations(self) -> List[Dict[str, str]]:
        """균형 최적화 조합"""
        return [
            {
                "data_source": DataSourceType.SYNTHETIC.value,
                "scenario": SimulationScenario.NORMAL_TREND.value,
                "reason": "균형잡힌 기본 분석"
            },
            {
                "data_source": DataSourceType.SYNTHETIC.value,
                "scenario": SimulationScenario.HIGH_VOLATILITY.value,
                "reason": "적절한 변동성 테스트"
            },
            {
                "data_source": DataSourceType.REAL_DB.value,
                "scenario": SimulationScenario.NORMAL_TREND.value,
                "reason": "실제 데이터 검증"
            },
            {
                "data_source": DataSourceType.SYNTHETIC.value,
                "scenario": SimulationScenario.MARKET_CRASH.value,
                "reason": "균형잡힌 리스크 테스트"
            },
            {
                "data_source": DataSourceType.REAL_DB.value,
                "scenario": SimulationScenario.SIDEWAYS_MARKET.value,
                "reason": "실제 횡보 검증"
            },
            {
                "data_source": DataSourceType.EMBEDDED.value,
                "scenario": SimulationScenario.NORMAL_TREND.value,
                "reason": "빠른 기준 비교"
            }
        ]
