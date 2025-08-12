"""
로깅 관리 다이얼로그 모듈

기본 로깅 설정과 독립적으로 동작하는 다이얼로그들을 제공합니다.
"""

# 컴포넌트 선택 다이얼로그 (독립적으로 동작)
try:
    from .component_selector import ComponentSelectorDialog, ComponentDataScanner
    DIALOGS_AVAILABLE = True
except ImportError as e:
    # 다이얼로그 모듈 오류가 기본 로깅 설정에 영향주지 않도록
    ComponentSelectorDialog = None
    ComponentDataScanner = None
    DIALOGS_AVAILABLE = False

__all__ = [
    'ComponentSelectorDialog',
    'ComponentDataScanner',
    'DIALOGS_AVAILABLE'
]
