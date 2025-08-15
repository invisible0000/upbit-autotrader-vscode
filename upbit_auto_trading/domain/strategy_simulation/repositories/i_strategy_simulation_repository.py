"""
전략 시뮬레이션 데이터 Repository 인터페이스
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import pandas as pd

from upbit_auto_trading.domain.strategy_simulation.entities.data_source import DataSource
from upbit_auto_trading.domain.strategy_simulation.value_objects.data_source_type import DataSourceType
from upbit_auto_trading.domain.strategy_simulation.value_objects.simulation_scenario import SimulationScenario


class IStrategySimulationDataRepository(ABC):
    """
    전략 시뮬레이션 데이터 Repository 인터페이스

    전략 관리 화면 전용 미니 시뮬레이션에서 사용
    실제 백테스팅과는 별개의 도메인
    """

    @abstractmethod
    def get_available_data_sources(self) -> List[DataSource]:
        """사용 가능한 데이터 소스 목록 반환"""
        pass

    @abstractmethod
    def get_data_source_by_type(self, source_type: DataSourceType) -> Optional[DataSource]:
        """타입별 데이터 소스 조회"""
        pass

    @abstractmethod
    def check_data_source_availability(self, source_type: DataSourceType) -> bool:
        """데이터 소스 사용 가능 여부 확인"""
        pass

    @abstractmethod
    def load_scenario_data(
        self,
        scenario: SimulationScenario,
        source_type: DataSourceType,
        data_length: int = 100
    ) -> Optional[pd.DataFrame]:
        """시나리오별 시뮬레이션 데이터 로드"""
        pass

    @abstractmethod
    def get_scenario_metadata(
        self,
        scenario: SimulationScenario,
        source_type: DataSourceType
    ) -> Dict[str, Any]:
        """시나리오 메타데이터 조회"""
        pass

    @abstractmethod
    def validate_data_integrity(self, source_type: DataSourceType) -> bool:
        """데이터 무결성 검증"""
        pass


class IStrategySimulationEngineRepository(ABC):
    """
    전략 시뮬레이션 엔진 Repository 인터페이스

    시뮬레이션 엔진의 생성 및 관리를 담당
    """

    @abstractmethod
    def create_simulation_engine(self, source_type: DataSourceType) -> Any:
        """데이터 소스 타입에 맞는 시뮬레이션 엔진 생성"""
        pass

    @abstractmethod
    def get_engine_capabilities(self, source_type: DataSourceType) -> Dict[str, bool]:
        """엔진별 지원 기능 조회"""
        pass

    @abstractmethod
    def cleanup_engine_resources(self, source_type: DataSourceType) -> None:
        """엔진 리소스 정리"""
        pass
