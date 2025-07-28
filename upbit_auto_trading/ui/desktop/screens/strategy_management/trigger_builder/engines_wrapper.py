"""
engines 모듈 - Junction 링크 대체 래퍼
Git Clone 호환성을 위해 실제 파일을 통한 접근 제공
"""

# mini_simulation_engines의 모든 내용을 re-export
from ..mini_simulation_engines.real_data_simulation import *
from ..mini_simulation_engines.embedded_simulation_engine import *
from ..mini_simulation_engines.robust_simulation_engine import *

# 호환성을 위한 명시적 import
try:
    from ..mini_simulation_engines.real_data_simulation import RealDataSimulation
    from ..mini_simulation_engines.embedded_simulation_engine import EmbeddedSimulationEngine
    from ..mini_simulation_engines.robust_simulation_engine import RobustSimulationEngine
    
    # 레거시 접근을 위한 alias
    REAL_DATA_SIMULATION = RealDataSimulation
    EMBEDDED_SIMULATION_ENGINE = EmbeddedSimulationEngine
    ROBUST_SIMULATION_ENGINE = RobustSimulationEngine
    
except ImportError as e:
    print(f"⚠️ engines 래퍼: mini_simulation_engines 모듈 로드 실패 - {e}")
    
    # Fallback: 공통 시스템 사용
    try:
        from ...components.mini_simulation import (
            get_simulation_engine,
            get_embedded_simulation_engine,
            get_real_data_simulation_engine,
            get_robust_simulation_engine
        )
        print("✅ engines 래퍼: 공통 시스템으로 fallback 성공")
    except ImportError:
        print("❌ engines 래퍼: 모든 fallback 실패")

# 모듈 정보
__version__ = "1.0.0"
__description__ = "TriggerBuilder engines wrapper for Git compatibility"
