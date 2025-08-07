"""
Infrastructure Configuration 모듈
기존 config.simple_paths와 호환성 유지
"""

from .paths import infrastructure_paths

# 기존 코드와의 호환성을 위한 alias
paths = infrastructure_paths

# 직접 사용을 위한 export
__all__ = ['infrastructure_paths', 'paths']
