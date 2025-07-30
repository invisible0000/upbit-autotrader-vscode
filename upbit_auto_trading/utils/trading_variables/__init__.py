"""
트레이딩 지표 변수 관리 시스템

이 패키지는 트레이딩 지표들의 체계적 관리, 호환성 검증, 자동 분류를 제공합니다.

주요 기능:
- 지표 간 호환성 자동 검증
- 새로운 지표 자동 분류 및 추가
- DB 기반 동적 지표 관리
- UI 통합을 위한 카테고리별 그룹화

사용법:
    from upbit_auto_trading.utils.trading_variables.legacy import SimpleVariableManager
    
    vm = SimpleVariableManager('trading.db')
    compatible = vm.get_compatible_variables('SMA')
"""

# 안전한 import - legacy 폴더에서 모듈 불러오기
try:
    from .legacy.variable_manager import SimpleVariableManager
except ImportError:
    print("⚠️ SimpleVariableManager는 legacy 폴더에서 직접 import하세요")
    SimpleVariableManager = None

try:
    from .legacy.indicator_classifier import SmartIndicatorClassifier
except ImportError:
    print("⚠️ SmartIndicatorClassifier는 legacy 폴더에서 직접 import하세요")
    SmartIndicatorClassifier = None

try:
    from .legacy.indicator_calculator import IndicatorCalculator
except ImportError:
    print("⚠️ IndicatorCalculator는 legacy 폴더에서 직접 import하세요")
    IndicatorCalculator = None

__version__ = "1.1.0"
__author__ = "GitHub Copilot"

__all__ = [
    'SimpleVariableManager',
    'SmartIndicatorClassifier', 
    'IndicatorCalculator'
]
