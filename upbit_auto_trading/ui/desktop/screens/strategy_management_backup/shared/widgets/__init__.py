#!/usr/bin/env python3
"""
위젯 모듈 초기화 - 4+1 위젯 구조

첨부 이미지 요구사항에 맞는 4+1 위젯 구조를 제공합니다:
1. 변수 선택 위젯 (파라미터 동적 생성)
2. 비교 설정 위젯 (비교값 + 연산자 + 추세방향)
3. 조건부 호환성 위젯 (외부 변수시에만 표시)
4. 조건 미리보기 위젯 (자연어 출력)

Available Widgets:
    Enhanced 4+1 Structure:
    - VariableSelectionWidget: 변수 선택 + 파라미터 동적 생성
    - ComparisonSettingsWidget: 비교 설정 + 추세방향
    - ConditionalCompatibilityWidget: 조건부 호환성 검증
    - ConditionPreviewWidget: 자연어 미리보기
"""

# 현재 4+1 위젯 구조 (활성)
from .variable_selection_widget import VariableSelectionWidget
from .comparison_settings_widget import ComparisonSettingsWidget
from .conditional_compatibility_widget import ConditionalCompatibilityWidget
from .condition_preview_widget import ConditionPreviewWidget

__all__ = [
    # === 4+1 위젯 구조 ===
    "VariableSelectionWidget",           # 1단계: 변수 선택 + 파라미터
    "ComparisonSettingsWidget",          # 2단계: 비교 설정 + 추세방향
    "ConditionalCompatibilityWidget",    # 조건부: 호환성 검증
    "ConditionPreviewWidget",           # 미리보기: 자연어 출력
]
