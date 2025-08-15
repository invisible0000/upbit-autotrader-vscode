"""
전략 시뮬레이션 DTO 모듈
전략 관리 화면 전용 미니 시뮬레이션 데이터 전송 객체
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

from upbit_auto_trading.domain.strategy_simulation.value_objects.data_source_type import DataSourceType
from upbit_auto_trading.domain.strategy_simulation.value_objects.simulation_scenario import SimulationScenario


@dataclass(frozen=True)
class DataSourceDTO:
    """데이터 소스 정보 DTO"""
    source_type: str
    name: str
    description: str
    is_available: bool
    is_recommended: bool
    metadata: Dict[str, Any]

    @classmethod
    def from_domain(cls, data_source) -> 'DataSourceDTO':
        """Domain Entity에서 DTO 생성"""
        return cls(
            source_type=data_source.source_type.value,
            name=data_source.name,
            description=data_source.description,
            is_available=data_source.is_available,
            is_recommended=data_source.source_type.is_recommended(),
            metadata=data_source.metadata or {}
        )


@dataclass(frozen=True)
class DataSourceListDTO:
    """데이터 소스 목록 DTO"""
    sources: List[DataSourceDTO]
    recommended_source: Optional[DataSourceDTO]
    user_preference: Optional[str]
    total_count: int
    available_count: int

    @classmethod
    def create(
        cls,
        sources: List[DataSourceDTO],
        user_preference: Optional[str] = None
    ) -> 'DataSourceListDTO':
        """데이터 소스 목록 생성"""
        available_sources = [s for s in sources if s.is_available]
        recommended = next((s for s in sources if s.is_recommended and s.is_available), None)

        return cls(
            sources=sources,
            recommended_source=recommended,
            user_preference=user_preference,
            total_count=len(sources),
            available_count=len(available_sources)
        )


@dataclass(frozen=True)
class SimulationScenarioDTO:
    """시뮬레이션 시나리오 DTO"""
    scenario_key: str
    display_name: str
    description: str
    color: str
    risk_level: str
    is_trending: bool
    is_high_risk: bool

    @classmethod
    def from_domain(cls, scenario: SimulationScenario) -> 'SimulationScenarioDTO':
        """Domain Value Object에서 DTO 생성"""
        return cls(
            scenario_key=scenario.value,
            display_name=scenario.value,
            description=SimulationScenario.get_scenario_description(scenario),
            color=SimulationScenario.get_scenario_color(scenario),
            risk_level=scenario.get_risk_level(),
            is_trending=scenario.is_trending_scenario(),
            is_high_risk=scenario.is_high_risk_scenario()
        )


@dataclass(frozen=True)
class SimulationScenarioListDTO:
    """시뮬레이션 시나리오 목록 DTO"""
    scenarios: List[SimulationScenarioDTO]
    grid_layout: List[List[SimulationScenarioDTO]]
    total_count: int

    @classmethod
    def create_from_scenarios(cls, scenarios: List[SimulationScenario]) -> 'SimulationScenarioListDTO':
        """시나리오 목록에서 DTO 생성"""
        scenario_dtos = [SimulationScenarioDTO.from_domain(s) for s in scenarios]

        # 3x2 그리드 레이아웃 생성
        grid_layout = []
        grid_scenarios = SimulationScenario.get_grid_layout()

        for row in grid_scenarios:
            row_dtos = [SimulationScenarioDTO.from_domain(s) for s in row]
            grid_layout.append(row_dtos)

        return cls(
            scenarios=scenario_dtos,
            grid_layout=grid_layout,
            total_count=len(scenario_dtos)
        )


@dataclass(frozen=True)
class SimulationDataDTO:
    """시뮬레이션 데이터 DTO"""
    scenario: str
    source_type: str
    current_value: float
    base_value: float
    change_percent: float
    price_data: List[float]
    volume_data: Optional[List[float]]
    period: str
    data_source: str
    quality_score: Optional[float]
    statistics: Dict[str, Any]
    metadata: Dict[str, Any]

    @classmethod
    def create(
        cls,
        scenario: str,
        source_type: str,
        simulation_result: Dict[str, Any],
        statistics: Optional[Dict[str, Any]] = None
    ) -> 'SimulationDataDTO':
        """시뮬레이션 결과에서 DTO 생성"""
        return cls(
            scenario=scenario,
            source_type=source_type,
            current_value=simulation_result.get('current_value', 0.0),
            base_value=simulation_result.get('base_value', 0.0),
            change_percent=simulation_result.get('change_percent', 0.0),
            price_data=simulation_result.get('price_data', []),
            volume_data=simulation_result.get('volume_data'),
            period=simulation_result.get('period', ''),
            data_source=simulation_result.get('data_source', ''),
            quality_score=simulation_result.get('quality_score'),
            statistics=statistics or {},
            metadata={
                'ohlc_data': simulation_result.get('ohlc_data', {}),
                'optimization_level': simulation_result.get('optimization_level'),
                'generated_at': datetime.now().isoformat()
            }
        )


@dataclass(frozen=True)
class SimulationRequestDTO:
    """시뮬레이션 요청 DTO"""
    scenario: str
    source_type: str
    data_length: int
    include_statistics: bool
    include_volume: bool

    def __post_init__(self):
        """요청 데이터 유효성 검증"""
        if not self.scenario or not self.scenario.strip():
            raise ValueError("시나리오는 필수입니다")

        if not self.source_type or not self.source_type.strip():
            raise ValueError("데이터 소스 타입은 필수입니다")

        if self.data_length <= 0 or self.data_length > 1000:
            raise ValueError("데이터 길이는 1-1000 범위여야 합니다")


@dataclass(frozen=True)
class SimulationCompatibilityDTO:
    """시뮬레이션 호환성 검증 DTO"""
    scenario: str
    source_type: str
    is_compatible: bool
    compatibility_score: float
    warnings: List[str]
    recommendations: List[str]
    optimal_data_length: int

    @classmethod
    def create_compatible(
        cls,
        scenario: str,
        source_type: str,
        optimal_length: int
    ) -> 'SimulationCompatibilityDTO':
        """호환 가능한 조합 생성"""
        return cls(
            scenario=scenario,
            source_type=source_type,
            is_compatible=True,
            compatibility_score=1.0,
            warnings=[],
            recommendations=[],
            optimal_data_length=optimal_length
        )

    @classmethod
    def create_incompatible(
        cls,
        scenario: str,
        source_type: str,
        warnings: List[str]
    ) -> 'SimulationCompatibilityDTO':
        """비호환 조합 생성"""
        return cls(
            scenario=scenario,
            source_type=source_type,
            is_compatible=False,
            compatibility_score=0.0,
            warnings=warnings,
            recommendations=["다른 데이터 소스를 선택해주세요"],
            optimal_data_length=100
        )


@dataclass(frozen=True)
class DataSourceStatusDTO:
    """데이터 소스 상태 DTO"""
    source_type: str
    is_available: bool
    last_check: str
    error_message: Optional[str]
    performance_metrics: Dict[str, Any]
    capabilities: Dict[str, bool]

    @classmethod
    def create_available(
        cls,
        source_type: str,
        capabilities: Dict[str, bool]
    ) -> 'DataSourceStatusDTO':
        """사용 가능한 상태 생성"""
        return cls(
            source_type=source_type,
            is_available=True,
            last_check=datetime.now().isoformat(),
            error_message=None,
            performance_metrics={
                "avg_load_time": 0.1,
                "success_rate": 1.0,
                "quality_score": 0.9
            },
            capabilities=capabilities
        )

    @classmethod
    def create_unavailable(
        cls,
        source_type: str,
        error_message: str
    ) -> 'DataSourceStatusDTO':
        """사용 불가능한 상태 생성"""
        return cls(
            source_type=source_type,
            is_available=False,
            last_check=datetime.now().isoformat(),
            error_message=error_message,
            performance_metrics={},
            capabilities={}
        )
