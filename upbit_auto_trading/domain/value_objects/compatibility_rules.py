#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
호환성 검증 규칙 Value Objects
===============================

매매 변수 간 호환성 검증을 위한 순수한 Value Object들입니다.
기존 UI 계층의 compatibility_validator.py 로직을 도메인 모델로 추상화합니다.

Value Objects:
- CompatibilityLevel: 호환성 수준 (COMPATIBLE, WARNING, INCOMPATIBLE)
- CompatibilityResult: 호환성 검증 결과
- ComparisonGroupRules: comparison_group별 호환성 규칙

Design Principles:
- Immutability: 모든 Value Object는 불변
- Rich Domain Model: 비즈니스 규칙을 객체 안에 캡슐화
- Self-Validation: 생성 시점에 유효성 검증
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set
from enum import Enum


class CompatibilityLevel(Enum):
    """
    변수 간 호환성 수준
    
    기존 compatibility_validator.py의 호환성 분류를 도메인 모델로 추상화
    """
    COMPATIBLE = "compatible"     # 직접 비교 가능 (같은 comparison_group)
    WARNING = "warning"          # 정규화 후 비교 가능 (price vs percentage 등)
    INCOMPATIBLE = "incompatible" # 비교 불가능 (완전히 다른 의미의 지표)
    
    def is_usable(self) -> bool:
        """사용 가능한 호환성 수준인지 확인"""
        return self in [self.COMPATIBLE, self.WARNING]
    
    def get_display_name(self) -> str:
        """사용자 표시용 한글 이름"""
        display_names = {
            self.COMPATIBLE: "호환 가능",
            self.WARNING: "주의 필요",
            self.INCOMPATIBLE: "호환 불가"
        }
        return display_names[self]
    
    def get_color_code(self) -> str:
        """UI 표시용 색상 코드"""
        color_codes = {
            self.COMPATIBLE: "#4CAF50",    # 녹색
            self.WARNING: "#FF9800",       # 주황색
            self.INCOMPATIBLE: "#F44336"   # 빨간색
        }
        return color_codes[self]


@dataclass(frozen=True)
class CompatibilityResult:
    """
    호환성 검증 결과
    
    기존 compatibility_validator.py의 검증 결과를 구조화한 Value Object
    """
    level: CompatibilityLevel
    message: str
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """결과 유효성 검증"""
        if not self.message:
            raise ValueError("호환성 결과 메시지는 필수입니다")
        
        # WARNING 수준인데 경고 메시지가 없으면 기본 경고 추가
        if self.level == CompatibilityLevel.WARNING and not self.warnings:
            object.__setattr__(self, 'warnings', ["정규화를 통한 비교입니다. 결과 해석에 주의하세요."])
    
    @property
    def is_compatible(self) -> bool:
        """호환 가능한지 확인 (COMPATIBLE 또는 WARNING)"""
        return self.level.is_usable()
    
    @property
    def should_block(self) -> bool:
        """UI에서 차단해야 하는지 확인"""
        return self.level == CompatibilityLevel.INCOMPATIBLE
    
    @property
    def requires_user_confirmation(self) -> bool:
        """사용자 확인이 필요한지 확인"""
        return self.level == CompatibilityLevel.WARNING
    
    def get_full_message(self) -> str:
        """전체 메시지 (본문 + 경고 + 제안) 반환"""
        parts = [self.message]
        
        if self.warnings:
            parts.append("⚠️ 주의사항:")
            parts.extend([f"  - {warning}" for warning in self.warnings])
        
        if self.suggestions:
            parts.append("💡 제안사항:")
            parts.extend([f"  - {suggestion}" for suggestion in self.suggestions])
        
        return "\n".join(parts)

    @classmethod
    def create_compatible(cls, message: str = "변수들이 직접 비교 가능합니다") -> 'CompatibilityResult':
        """호환 가능 결과 생성"""
        return cls(CompatibilityLevel.COMPATIBLE, message)
    
    @classmethod
    def create_warning(cls, message: str, warnings: List[str] = None, suggestions: List[str] = None) -> 'CompatibilityResult':
        """경고 포함 결과 생성"""
        return cls(
            CompatibilityLevel.WARNING, 
            message,
            warnings or [],
            suggestions or []
        )
    
    @classmethod
    def create_incompatible(cls, message: str, suggestions: List[str] = None) -> 'CompatibilityResult':
        """비호환 결과 생성"""
        return cls(
            CompatibilityLevel.INCOMPATIBLE,
            message,
            [],
            suggestions or []
        )


@dataclass
class ComparisonGroupRules:
    """
    comparison_group별 호환성 규칙
    
    기존 compatibility_validator.py의 하드코딩된 호환성 규칙을 
    도메인 모델로 추상화하여 중앙 관리
    """
    same_group_compatible: Set[str] = field(default_factory=set)
    cross_group_rules: Dict[str, Dict[str, CompatibilityLevel]] = field(default_factory=dict)
    
    def __post_init__(self):
        """기본 호환성 규칙 초기화"""
        if not self.same_group_compatible:
            # 기존 YAML 파일에서 확인된 comparison_group들
            self.same_group_compatible = {
                "price_comparable",       # 가격 관련 (SMA, EMA, Close, etc)
                "percentage_comparable",  # 백분율 관련 (RSI, Stochastic, etc)
                "zero_centered",         # 0 중심 (MACD, etc)
                "volume_comparable",     # 거래량 관련 (Volume, etc)
                "volatility_comparable", # 변동성 관련 (ATR, etc)
                "signal_conditional"     # 조건부 신호 (MACD 등)
            }
        
        if not self.cross_group_rules:
            # 기존 VARIABLE_COMPATIBILITY.md에서 정의된 교차 호환성 규칙
            self.cross_group_rules = {
                "price_comparable": {
                    "percentage_comparable": CompatibilityLevel.WARNING,  # 정규화 가능
                    "zero_centered": CompatibilityLevel.INCOMPATIBLE,
                    "volume_comparable": CompatibilityLevel.INCOMPATIBLE,
                    "volatility_comparable": CompatibilityLevel.INCOMPATIBLE,
                    "signal_conditional": CompatibilityLevel.INCOMPATIBLE
                },
                "percentage_comparable": {
                    "price_comparable": CompatibilityLevel.WARNING,      # 정규화 가능
                    "zero_centered": CompatibilityLevel.INCOMPATIBLE,
                    "volume_comparable": CompatibilityLevel.INCOMPATIBLE,
                    "volatility_comparable": CompatibilityLevel.INCOMPATIBLE,
                    "signal_conditional": CompatibilityLevel.INCOMPATIBLE
                },
                "zero_centered": {
                    "price_comparable": CompatibilityLevel.INCOMPATIBLE,
                    "percentage_comparable": CompatibilityLevel.INCOMPATIBLE,
                    "volume_comparable": CompatibilityLevel.INCOMPATIBLE,
                    "volatility_comparable": CompatibilityLevel.INCOMPATIBLE,
                    "signal_conditional": CompatibilityLevel.WARNING     # 일부 가능
                },
                "volume_comparable": {
                    "price_comparable": CompatibilityLevel.INCOMPATIBLE,
                    "percentage_comparable": CompatibilityLevel.INCOMPATIBLE,
                    "zero_centered": CompatibilityLevel.INCOMPATIBLE,
                    "volatility_comparable": CompatibilityLevel.INCOMPATIBLE,
                    "signal_conditional": CompatibilityLevel.INCOMPATIBLE
                },
                "volatility_comparable": {
                    "price_comparable": CompatibilityLevel.INCOMPATIBLE,
                    "percentage_comparable": CompatibilityLevel.INCOMPATIBLE,
                    "zero_centered": CompatibilityLevel.INCOMPATIBLE,
                    "volume_comparable": CompatibilityLevel.INCOMPATIBLE,
                    "signal_conditional": CompatibilityLevel.INCOMPATIBLE
                },
                "signal_conditional": {
                    "price_comparable": CompatibilityLevel.INCOMPATIBLE,
                    "percentage_comparable": CompatibilityLevel.INCOMPATIBLE,
                    "zero_centered": CompatibilityLevel.WARNING,
                    "volume_comparable": CompatibilityLevel.INCOMPATIBLE,
                    "volatility_comparable": CompatibilityLevel.INCOMPATIBLE
                }
            }
    
    def check_compatibility(self, group1: str, group2: str) -> CompatibilityLevel:
        """두 comparison_group 간 호환성 확인"""
        if not group1 or not group2:
            return CompatibilityLevel.INCOMPATIBLE
        
        # 같은 그룹 = 직접 호환
        if group1 == group2:
            return CompatibilityLevel.COMPATIBLE
        
        # 교차 그룹 규칙 확인
        if group1 in self.cross_group_rules:
            return self.cross_group_rules[group1].get(group2, CompatibilityLevel.INCOMPATIBLE)
        
        # 규칙에 없는 조합은 비호환
        return CompatibilityLevel.INCOMPATIBLE
    
    def get_compatible_groups(self, group: str) -> List[str]:
        """특정 그룹과 호환 가능한 모든 그룹 반환"""
        compatible_groups = []
        
        # 자기 자신은 항상 호환
        if group in self.same_group_compatible:
            compatible_groups.append(group)
        
        # 교차 호환 그룹들 확인
        if group in self.cross_group_rules:
            for other_group, level in self.cross_group_rules[group].items():
                if level.is_usable():
                    compatible_groups.append(other_group)
        
        return compatible_groups
    
    def get_warning_combinations(self) -> Dict[str, List[str]]:
        """경고가 필요한 그룹 조합들 반환"""
        warning_combinations = {}
        
        for group1, rules in self.cross_group_rules.items():
            warning_groups = []
            for group2, level in rules.items():
                if level == CompatibilityLevel.WARNING:
                    warning_groups.append(group2)
            
            if warning_groups:
                warning_combinations[group1] = warning_groups
        
        return warning_combinations
