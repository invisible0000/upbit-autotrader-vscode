"""
전략 시뮬레이션 UseCase 패키지
"""

from .data_source_use_cases import (
    ListDataSourcesUseCase,
    SetUserPreferenceUseCase,
    GetDataSourceStatusUseCase,
    ValidateDataSourceUseCase
)

from .simulation_use_cases import (
    LoadAvailableScenariosUseCase,
    RunSimulationUseCase,
    ValidateSimulationRequestUseCase,
    GetSimulationPreviewUseCase
)

from .compatibility_use_cases import (
    ValidateCompatibilityUseCase,
    GetCompatibilityMatrixUseCase,
    GetRecommendedCombinationsUseCase
)

__all__ = [
    # 데이터 소스 관리
    'ListDataSourcesUseCase',
    'SetUserPreferenceUseCase',
    'GetDataSourceStatusUseCase',
    'ValidateDataSourceUseCase',

    # 시뮬레이션 실행
    'LoadAvailableScenariosUseCase',
    'RunSimulationUseCase',
    'ValidateSimulationRequestUseCase',
    'GetSimulationPreviewUseCase',

    # 호환성 검증
    'ValidateCompatibilityUseCase',
    'GetCompatibilityMatrixUseCase',
    'GetRecommendedCombinationsUseCase'
]
