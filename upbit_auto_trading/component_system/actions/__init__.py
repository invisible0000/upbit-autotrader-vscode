"""
액션 컴포넌트 패키지 초기화
Action Components Package Initialization

모든 액션 컴포넌트들을 쉽게 가져올 수 있도록 하는 초기화 모듈
"""

# 매매 액션들
from .trading_actions import (
    BuyAction, BuyActionConfig,
    SellAction, SellActionConfig,
    PositionManagementAction, PositionManagementConfig
)

# 전체 액션 클래스 목록
ACTION_CLASSES = {
    # 매매 액션
    'buy': BuyAction,
    'sell': SellAction,
    'position_management': PositionManagementAction,
}

# 설정 클래스 목록
ACTION_CONFIG_CLASSES = {
    # 매매 액션
    'buy': BuyActionConfig,
    'sell': SellActionConfig,
    'position_management': PositionManagementConfig,
}

# 카테고리별 액션 그룹
ACTION_CATEGORIES = {
    'trading': ['buy', 'sell', 'position_management'],
}

# 액션 메타데이터
ACTION_METADATA = {
    'buy': {
        'display_name': '매수 액션',
        'category': 'trading',
        'description': '지정된 조건에 따라 매수를 실행',
        'difficulty': 'beginner'
    },
    'sell': {
        'display_name': '매도 액션',
        'category': 'trading',
        'description': '지정된 조건에 따라 매도를 실행',
        'difficulty': 'beginner'
    },
    'position_management': {
        'display_name': '포지션 관리 액션',
        'category': 'trading',
        'description': '포지션 크기나 상태를 관리',
        'difficulty': 'intermediate'
    },
}


def get_action_class(action_type: str):
    """액션 타입으로 클래스 가져오기"""
    return ACTION_CLASSES.get(action_type)


def get_action_config_class(action_type: str):
    """액션 타입으로 설정 클래스 가져오기"""
    return ACTION_CONFIG_CLASSES.get(action_type)


def get_actions_by_category(category: str):
    """카테고리별 액션 목록 가져오기"""
    return ACTION_CATEGORIES.get(category, [])


def get_action_metadata(action_type: str):
    """액션 메타데이터 가져오기"""
    return ACTION_METADATA.get(action_type, {})


def list_all_actions():
    """모든 사용 가능한 액션 목록"""
    return list(ACTION_CLASSES.keys())


def list_all_action_categories():
    """모든 액션 카테고리 목록"""
    return list(ACTION_CATEGORIES.keys())


__all__ = [
    # 클래스들
    'BuyAction', 'BuyActionConfig',
    'SellAction', 'SellActionConfig',
    'PositionManagementAction', 'PositionManagementConfig',
    
    # 딕셔너리들과 함수들
    'ACTION_CLASSES', 'ACTION_CONFIG_CLASSES', 'ACTION_CATEGORIES', 'ACTION_METADATA',
    'get_action_class', 'get_action_config_class', 'get_actions_by_category', 
    'get_action_metadata', 'list_all_actions', 'list_all_action_categories'
]
