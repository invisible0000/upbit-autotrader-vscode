"""
시뮬레이션 실행 UseCase
전략 시뮬레이션 수행 및 결과 처리
"""

from typing import Optional

from upbit_auto_trading.application.dto.strategy_simulation.strategy_simulation_dto import (
    SimulationRequestDTO,
    SimulationDataDTO,
    SimulationScenarioListDTO
)
from upbit_auto_trading.domain.strategy_simulation.value_objects.data_source_type import DataSourceType
from upbit_auto_trading.domain.strategy_simulation.value_objects.simulation_scenario import SimulationScenario
from upbit_auto_trading.domain.strategy_simulation.services.strategy_simulation_service import StrategySimulationService
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("SimulationUseCase")


class LoadAvailableScenariosUseCase:
    """
    시뮬레이션 시나리오 목록 조회 UseCase
    """

    def __init__(self, simulation_service: StrategySimulationService):
        self._simulation_service = simulation_service
        logger.debug("시나리오 목록 조회 UseCase 초기화")

    def execute(self, source_type_value: str) -> SimulationScenarioListDTO:
        """특정 데이터 소스의 사용 가능한 시나리오 목록 반환"""
        try:
            source_type = DataSourceType(source_type_value)

            # 도메인 서비스에서 지원 시나리오 조회
            supported_scenarios = self._simulation_service.get_supported_scenarios(source_type)

            # DTO 변환
            scenario_dtos = []
            for scenario in supported_scenarios:
                scenario_dto = {
                    'type_value': scenario.value,
                    'display_name': scenario.get_display_name(),
                    'description': scenario.get_description(),
                    'is_available': True
                }
                scenario_dtos.append(scenario_dto)

            # 목록 DTO 생성
            result = SimulationScenarioListDTO.create(scenario_dtos)

            logger.debug(f"시나리오 목록 조회 완료: {source_type_value} - {len(scenario_dtos)}개")
            return result

        except ValueError:
            logger.error(f"잘못된 데이터 소스 타입: {source_type_value}")
            return SimulationScenarioListDTO.create([])
        except Exception as e:
            logger.error(f"시나리오 목록 조회 실패: {e}")
            return SimulationScenarioListDTO.create([])


class RunSimulationUseCase:
    """
    시뮬레이션 실행 UseCase
    """

    def __init__(self, simulation_service: StrategySimulationService):
        self._simulation_service = simulation_service
        logger.debug("시뮬레이션 실행 UseCase 초기화")

    def execute(self, request: SimulationRequestDTO) -> Optional[SimulationDataDTO]:
        """시뮬레이션 실행 및 결과 반환"""
        try:
            # DTO 검증
            if not request.is_valid():
                logger.error(f"잘못된 시뮬레이션 요청: {request.get_validation_errors()}")
                return None

            # 도메인 타입 변환
            source_type = DataSourceType(request.data_source_type)
            scenario = SimulationScenario(request.scenario_type)

            logger.info(f"시뮬레이션 시작: {source_type.value} - {scenario.value}")

            # 호환성 검증
            if not self._simulation_service.validate_compatibility(source_type, scenario):
                logger.error(f"호환되지 않는 조합: {source_type.value} + {scenario.value}")
                return None

            # 시뮬레이션 실행
            simulation_result = self._simulation_service.run_simulation(
                data_source_type=source_type,
                scenario=scenario,
                symbol=request.symbol,
                period_days=request.period_days
            )

            if simulation_result is None:
                logger.error("시뮬레이션 실행 실패")
                return None

            # DTO 변환
            result_dto = SimulationDataDTO.from_domain(simulation_result)

            logger.info(f"시뮬레이션 완료: 데이터 포인트 {result_dto.data_points}개")
            return result_dto

        except ValueError as e:
            logger.error(f"잘못된 파라미터: {e}")
            return None
        except Exception as e:
            logger.error(f"시뮬레이션 실행 실패: {e}")
            return None


class ValidateSimulationRequestUseCase:
    """
    시뮬레이션 요청 검증 UseCase
    """

    def __init__(self, simulation_service: StrategySimulationService):
        self._simulation_service = simulation_service
        logger.debug("시뮬레이션 요청 검증 UseCase 초기화")

    def execute(self, request: SimulationRequestDTO) -> tuple[bool, list[str]]:
        """시뮬레이션 요청 유효성 검증"""
        try:
            # 기본 DTO 검증
            if not request.is_valid():
                errors = request.get_validation_errors()
                logger.debug(f"DTO 검증 실패: {errors}")
                return False, errors

            # 도메인 검증
            source_type = DataSourceType(request.data_source_type)
            scenario = SimulationScenario(request.scenario_type)

            # 데이터 소스 가용성 확인
            if not self._simulation_service._data_repository.check_data_source_availability(source_type):
                return False, [f"데이터 소스 '{source_type.value}'를 사용할 수 없습니다"]

            # 호환성 검증
            if not self._simulation_service.validate_compatibility(source_type, scenario):
                return False, [f"'{source_type.value}'와 '{scenario.value}' 조합이 지원되지 않습니다"]

            logger.debug(f"시뮬레이션 요청 검증 통과: {source_type.value} + {scenario.value}")
            return True, []

        except ValueError as e:
            return False, [f"잘못된 파라미터: {str(e)}"]
        except Exception as e:
            logger.error(f"시뮬레이션 요청 검증 실패: {e}")
            return False, [f"검증 중 오류 발생: {str(e)}"]


class GetSimulationPreviewUseCase:
    """
    시뮬레이션 미리보기 UseCase
    """

    def __init__(self, simulation_service: StrategySimulationService):
        self._simulation_service = simulation_service
        logger.debug("시뮬레이션 미리보기 UseCase 초기화")

    def execute(self, source_type_value: str, scenario_value: str) -> dict:
        """시뮬레이션 미리보기 정보 반환"""
        try:
            source_type = DataSourceType(source_type_value)
            scenario = SimulationScenario(scenario_value)

            # 미리보기 정보 생성
            preview_info = {
                'data_source': {
                    'type': source_type_value,
                    'display_name': source_type.get_display_name(),
                    'description': source_type.get_description()
                },
                'scenario': {
                    'type': scenario_value,
                    'display_name': scenario.get_display_name(),
                    'description': scenario.get_description()
                },
                'compatibility': self._simulation_service.validate_compatibility(source_type, scenario),
                'estimated_duration': self._estimate_duration(source_type, scenario),
                'expected_data_points': self._estimate_data_points(source_type, scenario)
            }

            logger.debug(f"미리보기 생성 완료: {source_type_value} + {scenario_value}")
            return preview_info

        except ValueError as e:
            logger.error(f"잘못된 파라미터: {e}")
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"미리보기 생성 실패: {e}")
            return {'error': str(e)}

    def _estimate_duration(self, source_type: DataSourceType, scenario: SimulationScenario) -> str:
        """예상 실행 시간 추정"""
        if source_type == DataSourceType.EMBEDDED:
            return "즉시"
        elif source_type == DataSourceType.SYNTHETIC:
            return "1-2초"
        elif source_type == DataSourceType.REAL_DB:
            return "3-5초"
        else:  # FALLBACK
            return "5-10초"

    def _estimate_data_points(self, source_type: DataSourceType, scenario: SimulationScenario) -> int:
        """예상 데이터 포인트 수 추정"""
        if source_type == DataSourceType.EMBEDDED:
            return 100  # 기본 임베디드 데이터
        elif source_type == DataSourceType.SYNTHETIC:
            return 200  # 합성 데이터
        elif source_type == DataSourceType.REAL_DB:
            return 500  # 실제 DB 데이터
        else:  # FALLBACK
            return 50   # 최소 데이터
