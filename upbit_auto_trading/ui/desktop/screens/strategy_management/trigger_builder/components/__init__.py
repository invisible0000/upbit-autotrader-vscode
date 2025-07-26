"""
Trigger Builder Components - 완전 독립화된 구조

Core Components: TriggerBuilder 전용
Shared Components: 공유 컴포넌트  
Legacy Components: 기존 컴포넌트들
"""

# Core Components (TriggerBuilder 전용)
try:
    from .core.condition_dialog import ConditionDialog
    from .core.trigger_list_widget import TriggerListWidget
    from .core.trigger_detail_widget import TriggerDetailWidget
    from .core.simulation_control_widget import SimulationControlWidget
    from .core.simulation_result_widget import SimulationResultWidget
    CORE_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Core 컴포넌트 로드 실패: {e}")
    CORE_COMPONENTS_AVAILABLE = False

# Shared Components (공유)
try:
    from .shared.trigger_calculator import TriggerCalculator
    from .shared.chart_visualizer import ChartVisualizer
    from .shared.simulation_engines import get_embedded_simulation_engine
    from .shared.variable_display_system import get_variable_registry
    from .shared.compatibility_validator import check_compatibility
    SHARED_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Shared 컴포넌트 로드 실패: {e}")
    SHARED_COMPONENTS_AVAILABLE = False

# Legacy Components (기존 호환성 유지)
try:
    from .data_source_manager import get_data_source_manager
    from .data_source_selector import DataSourceSelectorWidget
    LEGACY_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Legacy 컴포넌트 로드 실패: {e}")
    LEGACY_COMPONENTS_AVAILABLE = False

# 안전한 exports
__all__ = []

if CORE_COMPONENTS_AVAILABLE:
    __all__.extend([
        'ConditionDialog',
        'TriggerListWidget', 
        'TriggerDetailWidget',
        'SimulationControlWidget',
        'SimulationResultWidget'
    ])

if SHARED_COMPONENTS_AVAILABLE:
    __all__.extend([
        'TriggerCalculator',
        'ChartVisualizer', 
        'get_embedded_simulation_engine',
        'get_variable_registry',
        'check_compatibility'
    ])

if LEGACY_COMPONENTS_AVAILABLE:
    __all__.extend([
        'get_data_source_manager',
        'DataSourceSelectorWidget'
    ])

print(f"✅ TriggerBuilder Components 로드 완료: {len(__all__)}개 컴포넌트")
