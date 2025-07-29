"""
미니 시뮬레이from .engines.factory import (
    get_simulation_engine,
    get_embedded_simulation_engine,
    get_real_data_simulation_engine,
    get_robust_simulation_engine,
    DataSourceType
)

from .services.data_source_manager import SimulationDataSourceManager
from .services.mini_simulation_service import MiniSimulationService 시스템

이 모듈은 재사용 가능한 미니 시뮬레이션 컴포넌트들을 제공합니다.
TriggerBuilder뿐만 아니라 StrategyMaker, Backtest 등 다른 탭에서도 활용 가능합니다.

구조:
- engines/: 시뮬레이션 데이터 엔진들 (통합된 버전)
- widgets/: 재사용 가능한 UI 컴포넌트들
- services/: 비즈니스 로직 서비스들
"""

# 엔진 팩토리
from .engines.simulation_engine_factory import (
    get_simulation_engine,
    get_embedded_simulation_engine,
    get_real_data_simulation_engine,
    get_robust_simulation_engine,
    DataSourceType
)

# 서비스
from .services.data_source_manager import SimulationDataSourceManager
from .services.mini_simulation_service import MiniSimulationService

__version__ = "1.0.0"
__author__ = "Upbit Auto Trading System"

# 공통 인터페이스 노출
__all__ = [
    # 엔진 팩토리
    'get_simulation_engine',
    'get_embedded_simulation_engine',
    'get_real_data_simulation_engine',
    'get_robust_simulation_engine',
    'DataSourceType',
    
    # 서비스
    'SimulationDataSourceManager',
    'MiniSimulationService',
]


def get_mini_simulation_info():
    """미니 시뮬레이션 시스템 정보 반환"""
    return {
        'version': __version__,
        'available_engines': ['embedded', 'real_data', 'robust'],
        'supported_scenarios': ['상승 추세', '하락 추세', '급등', '급락', '횡보', 'MA 크로스'],
        'data_sources': ['EMBEDDED', 'REAL_DB', 'SYNTHETIC', 'SIMPLE_FALLBACK']
    }
