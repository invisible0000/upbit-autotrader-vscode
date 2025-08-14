"""
공통 시뮬레이션 시스템 - 통합 인터페이스
Git Clone 호환, 명확한 구조, Junction 링크 불필요

이 모듈을 import하면 모든 시뮬레이션 기능에 접근 가능합니다.
"""

from .engines.simulation_engines import (
    BaseSimulationEngine,
    EmbeddedSimulationEngine,
    RealDataSimulationEngine, 
    RobustSimulationEngine,
    get_embedded_engine,
    get_realdata_engine,
    get_robust_engine,
    get_simulation_engine
)

from .data_sources.market_data_manager import (
    MarketDataLoader,
    SampleDataGenerator,
    DataValidator
)

# 버전 정보
__version__ = "2.0.0"
__description__ = "공통 시뮬레이션 시스템 - 명확하고 단순한 구조"

# 주요 기능들을 쉽게 접근할 수 있도록 제공
def get_simulation_system_info():
    """시뮬레이션 시스템 정보 반환"""
    return {
        'version': __version__,
        'description': __description__,
        'available_engines': ['embedded', 'realdata', 'robust'],
        'supported_scenarios': ['normal', 'bull', 'bear', 'volatile'],
        'features': [
            '✅ Git Clone 호환성',
            '✅ Junction 링크 불필요', 
            '✅ 명확한 폴더 구조',
            '✅ 통합된 인터페이스',
            '✅ 현실적인 데이터 생성',
            '✅ 자동 데이터 검증'
        ]
    }

def create_quick_simulation(scenario: str = "normal", limit: int = 100):
    """빠른 시뮬레이션 생성 (에이전트용 헬퍼 함수)"""
    try:
        # 견고한 엔진 사용
        engine = get_robust_engine()
        data = engine.load_market_data(limit)
        
        if data is None or data.empty:
            # Fallback: 샘플 데이터 생성
            generator = SampleDataGenerator()
            data = generator.generate_realistic_btc_data(limit, scenario)
        
        # 데이터 검증
        validator = DataValidator()
        validation = validator.validate_market_data(data)
        
        return {
            'data': data,
            'validation': validation,
            'engine_used': engine.name,
            'scenario': scenario,
            'record_count': len(data) if data is not None else 0
        }
        
    except Exception as e:
        return {
            'data': None,
            'validation': {'is_valid': False, 'errors': [str(e)]},
            'engine_used': 'None',
            'scenario': scenario,
            'record_count': 0
        }

# 하위 호환성을 위한 별칭들
SimulationEngine = RobustSimulationEngine  # 기본 엔진
get_default_engine = get_robust_engine

# 공개 API
__all__ = [
    # 엔진 클래스들
    'BaseSimulationEngine',
    'EmbeddedSimulationEngine', 
    'RealDataSimulationEngine',
    'RobustSimulationEngine',
    
    # 엔진 팩토리 함수들  
    'get_embedded_engine',
    'get_realdata_engine',
    'get_robust_engine', 
    'get_simulation_engine',
    'get_default_engine',
    
    # 데이터 관리
    'MarketDataLoader',
    'SampleDataGenerator',
    'DataValidator',
    
    # 헬퍼 함수들
    'get_simulation_system_info',
    'create_quick_simulation',
    
    # 별칭
    'SimulationEngine'
]
