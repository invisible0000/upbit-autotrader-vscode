#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 호환성 검증기 (Unified Compatibility Validator)
====================================================

모든 호환성 검증 기능을 하나로 통합한 클래스
- 기본 호환성 검증
- 고급 타입 기반 검증
- 복합 조건 검증
- 대안 제안
- 신뢰도 점수 계산
"""

from typing import Dict, List, Tuple, Any, Optional
from enum import Enum
import logging


class VariableType(Enum):
    """변수 타입 분류"""
    PRICE = "price"                    # 가격 관련 (현재가, 시가, 고가, 저가)
    PRICE_INDICATOR = "price_indicator"  # 가격 지표 (SMA, EMA, 볼린저밴드)
    OSCILLATOR = "oscillator"          # 오실레이터 (RSI, 스토캐스틱)
    MOMENTUM = "momentum"              # 모멘텀 (MACD)
    VOLUME = "volume"                  # 거래량 관련
    VOLATILITY = "volatility"          # 변동성 (ATR)
    FINANCIAL = "financial"            # 재무 정보 (잔고, 수익률)
    CUSTOM = "custom"                  # 사용자 정의 지표


class ScaleType(Enum):
    """척도 타입 분류"""
    PRICE_SCALE = "price_scale"        # 가격 단위 (원, 달러)
    PERCENT_SCALE = "percent_scale"    # 퍼센트 단위 (0-100)
    VOLUME_SCALE = "volume_scale"      # 거래량 단위
    RATIO_SCALE = "ratio_scale"        # 비율 (0-1 또는 임의)
    NORMALIZED = "normalized"          # 정규화된 값


class CompatibilityValidator:
    """통합 호환성 검증기 - 모든 호환성 검증을 담당하는 단일 클래스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 변수 타입 매핑
        self.variable_types = {
            # 가격 관련
            'CURRENT_PRICE': VariableType.PRICE,
            'OPEN_PRICE': VariableType.PRICE,
            'HIGH_PRICE': VariableType.PRICE,
            'LOW_PRICE': VariableType.PRICE,
            
            # 가격 지표
            'SMA': VariableType.PRICE_INDICATOR,
            'EMA': VariableType.PRICE_INDICATOR,
            'BOLLINGER_BAND': VariableType.PRICE_INDICATOR,
            
            # 오실레이터
            'RSI': VariableType.OSCILLATOR,
            'STOCHASTIC': VariableType.OSCILLATOR,
            
            # 모멘텀
            'MACD': VariableType.MOMENTUM,
            
            # 거래량
            'VOLUME': VariableType.VOLUME,
            'VOLUME_SMA': VariableType.VOLUME,
            
            # 변동성
            'ATR': VariableType.VOLATILITY,
            
            # 재무
            'CASH_BALANCE': VariableType.FINANCIAL,
            'COIN_BALANCE': VariableType.FINANCIAL,
            'TOTAL_BALANCE': VariableType.FINANCIAL,
            'PROFIT_PERCENT': VariableType.FINANCIAL,
            'PROFIT_AMOUNT': VariableType.FINANCIAL,
            'POSITION_SIZE': VariableType.FINANCIAL,
            'AVG_BUY_PRICE': VariableType.FINANCIAL
        }
        
        # 척도 타입 매핑
        self.scale_types = {
            # 가격 척도
            'CURRENT_PRICE': ScaleType.PRICE_SCALE,
            'OPEN_PRICE': ScaleType.PRICE_SCALE,
            'HIGH_PRICE': ScaleType.PRICE_SCALE,
            'LOW_PRICE': ScaleType.PRICE_SCALE,
            'SMA': ScaleType.PRICE_SCALE,
            'EMA': ScaleType.PRICE_SCALE,
            'BOLLINGER_BAND': ScaleType.PRICE_SCALE,
            'CASH_BALANCE': ScaleType.PRICE_SCALE,
            'TOTAL_BALANCE': ScaleType.PRICE_SCALE,
            'PROFIT_AMOUNT': ScaleType.PRICE_SCALE,
            'AVG_BUY_PRICE': ScaleType.PRICE_SCALE,
            
            # 퍼센트 척도
            'RSI': ScaleType.PERCENT_SCALE,
            'STOCHASTIC': ScaleType.PERCENT_SCALE,
            'PROFIT_PERCENT': ScaleType.PERCENT_SCALE,
            
            # 거래량 척도
            'VOLUME': ScaleType.VOLUME_SCALE,
            'VOLUME_SMA': ScaleType.VOLUME_SCALE,
            
            # 비율 척도
            'MACD': ScaleType.RATIO_SCALE,
            'ATR': ScaleType.RATIO_SCALE,
            'COIN_BALANCE': ScaleType.RATIO_SCALE,
            'POSITION_SIZE': ScaleType.RATIO_SCALE
        }
        
        # 호환성 매트릭스 (타입 기반)
        self.compatibility_matrix = {
            VariableType.PRICE: [VariableType.PRICE, VariableType.PRICE_INDICATOR],
            VariableType.PRICE_INDICATOR: [VariableType.PRICE, VariableType.PRICE_INDICATOR],
            VariableType.OSCILLATOR: [VariableType.OSCILLATOR],
            VariableType.MOMENTUM: [VariableType.MOMENTUM],
            VariableType.VOLUME: [VariableType.VOLUME],
            VariableType.VOLATILITY: [VariableType.VOLATILITY],
            VariableType.FINANCIAL: [VariableType.FINANCIAL],
            VariableType.CUSTOM: [VariableType.CUSTOM]
        }
        
        # 표준화 문서 기반 용도 카테고리 매핑 (이중 카테고리 시스템)
        self.legacy_categories = {
            # 추세 지표
            'SMA': 'trend',
            'EMA': 'trend',
            
            # 모멘텀 지표
            'RSI': 'momentum',
            'STOCHASTIC': 'momentum',
            'MACD': 'momentum',
            
            # 변동성 지표
            'BOLLINGER_BAND': 'volatility',
            'ATR': 'volatility',
            
            # 거래량 지표
            'VOLUME': 'volume',
            'VOLUME_SMA': 'volume',
            
            # 가격 데이터
            'CURRENT_PRICE': 'price',
            'OPEN_PRICE': 'price',
            'HIGH_PRICE': 'price',
            'LOW_PRICE': 'price'
        }
    
    def validate_compatibility(self, var1_id: str, var2_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        두 변수 간의 호환성을 종합적으로 검증
        
        Returns:
            Tuple[bool, str, Dict]: (호환 여부, 이유, 상세 정보)
        """
        try:
            # 1단계: 기본 호환성 검증 (레거시 카테고리 기반)
            basic_compatible, basic_reason = self._validate_basic_compatibility(var1_id, var2_id)
            
            # 2단계: 고급 타입 기반 검증
            advanced_compatible, advanced_reason, confidence = self._validate_advanced_compatibility(var1_id, var2_id)
            
            # 3단계: 종합 판정
            final_compatible = basic_compatible and advanced_compatible
            
            # 상세 정보 구성
            details = {
                'confidence_score': confidence,
                'basic_result': basic_compatible,
                'basic_reason': basic_reason,
                'advanced_result': advanced_compatible,
                'advanced_reason': advanced_reason,
                'var1_type': self.variable_types.get(var1_id, VariableType.CUSTOM),
                'var2_type': self.variable_types.get(var2_id, VariableType.CUSTOM),
                'var1_scale': self.scale_types.get(var1_id, ScaleType.NORMALIZED),
                'var2_scale': self.scale_types.get(var2_id, ScaleType.NORMALIZED)
            }
            
            # 최종 이유 결정
            if final_compatible:
                final_reason = f"호환 (기본: {basic_reason}, 고급: {advanced_reason})"
            else:
                final_reason = f"비호환 (기본: {basic_reason}, 고급: {advanced_reason})"
            
            return final_compatible, final_reason, details
            
        except Exception as e:
            self.logger.error(f"호환성 검증 오류: {e}")
            return False, f"검증 오류: {e}", {}
    
    def _validate_basic_compatibility(self, var1_id: str, var2_id: str) -> Tuple[bool, str]:
        """기본 카테고리 기반 호환성 검증 (레거시 시스템과 호환)"""
        cat1 = self.legacy_categories.get(var1_id, 'unknown')
        cat2 = self.legacy_categories.get(var2_id, 'unknown')
        
        if cat1 == cat2:
            return True, f"같은 카테고리: {cat1}"
        elif cat1 == 'price' and cat2 == 'price_overlay':
            return True, "가격과 가격 지표"
        elif cat1 == 'price_overlay' and cat2 == 'price':
            return True, "가격 지표와 가격"
        else:
            return False, f"다른 카테고리: {cat1} vs {cat2}"
    
    def _validate_advanced_compatibility(self, var1_id: str, var2_id: str) -> Tuple[bool, str, float]:
        """고급 타입 기반 호환성 검증"""
        type1 = self.variable_types.get(var1_id, VariableType.CUSTOM)
        type2 = self.variable_types.get(var2_id, VariableType.CUSTOM)
        scale1 = self.scale_types.get(var1_id, ScaleType.NORMALIZED)
        scale2 = self.scale_types.get(var2_id, ScaleType.NORMALIZED)
        
        # 타입 호환성 검사
        compatible_types = self.compatibility_matrix.get(type1, [])
        type_compatible = type2 in compatible_types
        
        # 척도 호환성 검사
        scale_compatible = scale1 == scale2
        
        # 신뢰도 점수 계산
        confidence = 0.0
        if type_compatible and scale_compatible:
            confidence = 100.0
        elif type_compatible:
            confidence = 75.0
        elif scale_compatible:
            confidence = 50.0
        else:
            confidence = 0.0
        
        # 이유 결정
        if type_compatible and scale_compatible:
            reason = f"완전 호환 (타입: {type1.value}={type2.value}, 척도: {scale1.value}={scale2.value})"
        elif type_compatible:
            reason = f"타입 호환 (타입: {type1.value}={type2.value}, 척도 차이: {scale1.value}≠{scale2.value})"
        elif scale_compatible:
            reason = f"척도 호환 (척도: {scale1.value}={scale2.value}, 타입 차이: {type1.value}≠{type2.value})"
        else:
            reason = f"비호환 (타입: {type1.value}≠{type2.value}, 척도: {scale1.value}≠{scale2.value})"
        
        return type_compatible, reason, confidence
    
    def validate_multiple_compatibility(self, variable_ids: List[str]) -> Tuple[bool, Dict[str, Any]]:
        """복수 변수들 간의 호환성 검증"""
        if len(variable_ids) < 2:
            return True, {'compatible_pairs': [], 'incompatible_pairs': [], 'overall_score': 100.0}
        
        compatible_pairs = []
        incompatible_pairs = []
        total_confidence = 0.0
        total_pairs = 0
        
        for i in range(len(variable_ids)):
            for j in range(i + 1, len(variable_ids)):
                var1, var2 = variable_ids[i], variable_ids[j]
                is_compatible, reason, details = self.validate_compatibility(var1, var2)
                
                confidence = details.get('confidence_score', 0.0)
                total_confidence += confidence
                total_pairs += 1
                
                if is_compatible:
                    compatible_pairs.append((var1, var2, reason, confidence))
                else:
                    incompatible_pairs.append((var1, var2, reason, confidence))
        
        overall_compatible = len(incompatible_pairs) == 0
        overall_score = total_confidence / total_pairs if total_pairs > 0 else 0.0
        
        result = {
            'compatible_pairs': compatible_pairs,
            'incompatible_pairs': incompatible_pairs,
            'overall_score': overall_score,
            'total_pairs': total_pairs
        }
        
        return overall_compatible, result
    
    def suggest_compatible_alternatives(self, target_var: str, candidate_vars: List[str], limit: int = 5) -> List[Tuple[str, float, str]]:
        """호환 가능한 대안 변수들 제안"""
        alternatives = []
        
        for candidate in candidate_vars:
            if candidate == target_var:
                continue
                
            is_compatible, reason, details = self.validate_compatibility(target_var, candidate)
            if is_compatible:
                confidence = details.get('confidence_score', 0.0)
                alternatives.append((candidate, confidence, reason))
        
        # 신뢰도 순으로 정렬하고 상위 N개 반환
        alternatives.sort(key=lambda x: x[1], reverse=True)
        return alternatives[:limit]
    
    def get_compatibility_summary(self, variable_ids: List[str]) -> Dict[str, Any]:
        """변수들의 호환성 종합 분석 결과"""
        if not variable_ids:
            return {}
        
        overall_compatible, details = self.validate_multiple_compatibility(variable_ids)
        
        # 변수별 타입/척도 정보
        variable_info = {}
        for var_id in variable_ids:
            variable_info[var_id] = {
                'type': self.variable_types.get(var_id, VariableType.CUSTOM).value,
                'scale': self.scale_types.get(var_id, ScaleType.NORMALIZED).value,
                'legacy_category': self.legacy_categories.get(var_id, 'unknown')
            }
        
        return {
            'overall_compatible': overall_compatible,
            'overall_score': details.get('overall_score', 0.0),
            'total_pairs': details.get('total_pairs', 0),
            'compatible_pairs': len(details.get('compatible_pairs', [])),
            'incompatible_pairs': len(details.get('incompatible_pairs', [])),
            'variable_info': variable_info,
            'incompatible_details': details.get('incompatible_pairs', [])
        }


# 편의성을 위한 모듈 레벨 함수들
_validator_instance = None

def get_compatibility_validator() -> CompatibilityValidator:
    """싱글톤 호환성 검증기 인스턴스 반환"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = CompatibilityValidator()
    return _validator_instance


def check_compatibility(var1_id: str, var2_id: str) -> Tuple[bool, str]:
    """간단한 호환성 검사 (기존 API와 호환)"""
    validator = get_compatibility_validator()
    is_compatible, reason, _ = validator.validate_compatibility(var1_id, var2_id)
    return is_compatible, reason


def validate_condition_variables(variable_ids: List[str]) -> bool:
    """조건에 사용된 변수들의 호환성 검증"""
    validator = get_compatibility_validator()
    is_compatible, _ = validator.validate_multiple_compatibility(variable_ids)
    return is_compatible


if __name__ == "__main__":
    # 테스트 코드
    validator = CompatibilityValidator()
    
    print("🧪 통합 호환성 검증기 테스트")
    print("=" * 50)
    
    # 기본 테스트
    test_pairs = [
        ('SMA', 'EMA'),
        ('RSI', 'STOCHASTIC'),
        ('SMA', 'RSI'),
        ('VOLUME_SMA', 'ATR'),
        ('CURRENT_PRICE', 'BOLLINGER_BAND')
    ]
    
    for var1, var2 in test_pairs:
        is_compatible, reason, details = validator.validate_compatibility(var1, var2)
        score = details.get('confidence_score', 0.0)
        print(f"✓ {var1} ↔ {var2}: {is_compatible} ({score:.1f}%) - {reason}")
    
    print("\n복합 조건 테스트:")
    variables = ['SMA', 'EMA', 'CURRENT_PRICE']
    summary = validator.get_compatibility_summary(variables)
    print(f"✓ {'+'.join(variables)}: 전체 호환성 {summary['overall_compatible']} ({summary['overall_score']:.1f}%)")
