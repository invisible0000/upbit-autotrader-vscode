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
    # Note: SimulationControlWidget, SimulationResultWidget are now using shared_simulation
    CORE_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Core 컴포넌트 로드 실패: {e}")
    CORE_COMPONENTS_AVAILABLE = False

# Shared Components (공유)
try:
    from .shared.trigger_calculator import TriggerCalculator
    # Note: ChartVisualizer is now using shared_simulation.charts.chart_visualizer
    from .shared.variable_display_system import get_variable_registry
    from .shared.compatibility_validator import check_compatibility
    # Note: simulation_engines moved to shared_simulation
    SHARED_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Shared 컴포넌트 로드 실패: {e}")
    SHARED_COMPONENTS_AVAILABLE = False

# Legacy Components - 제거됨 (Infrastructure Layer로 통합)
LEGACY_COMPONENTS_AVAILABLE = False

# 안전한 exports
__all__ = []

if CORE_COMPONENTS_AVAILABLE:
    __all__.extend([
        'ConditionDialog',
        'TriggerListWidget',
        'TriggerDetailWidget'
        # Note: SimulationControlWidget, SimulationResultWidget moved to shared_simulation
    ])

if SHARED_COMPONENTS_AVAILABLE:
    __all__.extend([
        'TriggerCalculator',
        # Note: ChartVisualizer moved to shared_simulation
        'get_variable_registry',
        'check_compatibility'
        # Note: simulation_engines moved to shared_simulation
        # Legacy components removed - migrated to Infrastructure Layer
    ])

# 레거시 컴포넌트는 제거됨

print(f"✅ TriggerBuilder Components 로드 완료: {len(__all__)}개 컴포넌트")
