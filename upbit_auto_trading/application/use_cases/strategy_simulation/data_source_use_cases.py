"""
데이터 소스 관리 UseCase
전략 시뮬레이션 데이터 소스 조회 및 관리
"""

from typing import Optional

from upbit_auto_trading.application.dto.strategy_simulation.strategy_simulation_dto import (
    DataSourceListDTO,
    DataSourceDTO,
    DataSourceStatusDTO
)
from upbit_auto_trading.domain.strategy_simulation.value_objects.data_source_type import DataSourceType
from upbit_auto_trading.domain.strategy_simulation.services.strategy_simulation_service import StrategySimulationService
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("ListDataSourcesUseCase")


class ListDataSourcesUseCase:
    """
    데이터 소스 목록 조회 UseCase

    전략 관리 화면에서 사용 가능한 데이터 소스 목록 제공
    """

    def __init__(self, simulation_service: StrategySimulationService):
        self._simulation_service = simulation_service
        logger.debug("데이터 소스 목록 조회 UseCase 초기화")

    def execute(self) -> DataSourceListDTO:
        """사용 가능한 데이터 소스 목록 반환"""
        try:
            # 도메인 서비스에서 데이터 소스 조회
            domain_sources = self._simulation_service._data_repository.get_available_data_sources()

            # DTO 변환
            source_dtos = [DataSourceDTO.from_domain(source) for source in domain_sources]

            # 사용자 선호도 조회
            user_preference = self._simulation_service.get_user_preference()
            user_preference_value = user_preference.value if user_preference else None

            # 목록 DTO 생성
            result = DataSourceListDTO.create(source_dtos, user_preference_value)

            logger.debug(f"데이터 소스 목록 조회 완료: {result.total_count}개 (사용가능: {result.available_count}개)")
            return result

        except Exception as e:
            logger.error(f"데이터 소스 목록 조회 실패: {e}")
            # 빈 목록 반환
            return DataSourceListDTO.create([])


class SetUserPreferenceUseCase:
    """
    사용자 선호 데이터 소스 설정 UseCase
    """

    def __init__(self, simulation_service: StrategySimulationService):
        self._simulation_service = simulation_service
        logger.debug("사용자 선호 설정 UseCase 초기화")

    def execute(self, source_type_value: str) -> bool:
        """사용자 선호 데이터 소스 설정"""
        try:
            # 문자열을 DataSourceType으로 변환
            source_type = DataSourceType(source_type_value)

            # 도메인 서비스를 통해 설정
            success = self._simulation_service.set_user_preference(source_type)

            if success:
                logger.info(f"사용자 선호 데이터 소스 설정 완료: {source_type_value}")
            else:
                logger.warning(f"사용자 선호 데이터 소스 설정 실패: {source_type_value}")

            return success

        except ValueError as e:
            logger.error(f"잘못된 데이터 소스 타입: {source_type_value}, {e}")
            return False
        except Exception as e:
            logger.error(f"사용자 선호 설정 실패: {e}")
            return False


class GetDataSourceStatusUseCase:
    """
    데이터 소스 상태 조회 UseCase
    """

    def __init__(self, simulation_service: StrategySimulationService):
        self._simulation_service = simulation_service
        logger.debug("데이터 소스 상태 조회 UseCase 초기화")

    def execute(self, source_type_value: str) -> Optional[DataSourceStatusDTO]:
        """특정 데이터 소스의 상태 조회"""
        try:
            source_type = DataSourceType(source_type_value)

            # 가용성 확인
            is_available = self._simulation_service._data_repository.check_data_source_availability(source_type)

            if is_available:
                # 엔진 기능 조회
                capabilities = self._simulation_service._engine_repository.get_engine_capabilities(source_type)
                return DataSourceStatusDTO.create_available(source_type_value, capabilities)
            else:
                return DataSourceStatusDTO.create_unavailable(
                    source_type_value,
                    "데이터 소스를 사용할 수 없습니다"
                )

        except ValueError:
            return DataSourceStatusDTO.create_unavailable(
                source_type_value,
                "잘못된 데이터 소스 타입입니다"
            )
        except Exception as e:
            logger.error(f"데이터 소스 상태 조회 실패: {e}")
            return DataSourceStatusDTO.create_unavailable(
                source_type_value,
                f"상태 조회 중 오류 발생: {str(e)}"
            )


class ValidateDataSourceUseCase:
    """
    데이터 소스 유효성 검증 UseCase
    """

    def __init__(self, simulation_service: StrategySimulationService):
        self._simulation_service = simulation_service
        logger.debug("데이터 소스 검증 UseCase 초기화")

    def execute(self, source_type_value: str) -> bool:
        """데이터 소스 유효성 검증"""
        try:
            source_type = DataSourceType(source_type_value)

            # 도메인 서비스를 통해 데이터 무결성 검증
            is_valid = self._simulation_service._data_repository.validate_data_integrity(source_type)

            logger.debug(f"데이터 소스 검증 결과: {source_type_value} = {is_valid}")
            return is_valid

        except ValueError:
            logger.error(f"잘못된 데이터 소스 타입: {source_type_value}")
            return False
        except Exception as e:
            logger.error(f"데이터 소스 검증 실패: {e}")
            return False
