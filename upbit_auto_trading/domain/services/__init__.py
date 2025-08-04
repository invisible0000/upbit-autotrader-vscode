#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Domain Services Module
========================

DDD 아키텍처 기반 도메인 서비스 모듈입니다.
Domain Service는 단일 엔티티로 표현하기 어려운 복잡한 비즈니스 로직을 캡슐화합니다.

서비스 종류:
- StrategyCompatibilityService: 전략 호환성 검증
- TriggerEvaluationService: 트리거 조건 평가
- NormalizationService: 변수 간 정규화

Design Principles:
- Stateless: 도메인 서비스는 상태를 가지지 않음
- Domain Logic Focus: 순수한 비즈니스 규칙만 포함
- Infrastructure Independence: 외부 의존성 최소화
"""

from .strategy_compatibility_service import StrategyCompatibilityService
from .trigger_evaluation_service import TriggerEvaluationService
from .normalization_service import NormalizationService

__all__ = [
    'StrategyCompatibilityService',
    'TriggerEvaluationService', 
    'NormalizationService'
]
