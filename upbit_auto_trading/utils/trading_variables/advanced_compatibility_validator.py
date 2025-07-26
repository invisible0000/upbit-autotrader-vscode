"""
Step 2.2: 고급 호환성 검증 로직 및 validation_utils 확장
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum

# 기존 시스템 import
try:
    from integrated_variable_manager import HybridCompatibilityValidator
    HYBRID_SYSTEM_AVAILABLE = True
except ImportError:
    HYBRID_SYSTEM_AVAILABLE = False
    print("⚠️ 하이브리드 시스템을 찾을 수 없습니다")


class VariableType(Enum):
    """변수 타입 분류"""
    PRICE = "price"           # 가격 관련 (현재가, 시가, 고가, 저가)
    PRICE_INDICATOR = "price_indicator"  # 가격 기반 지표 (SMA, EMA, 볼린저밴드)
    OSCILLATOR = "oscillator"  # 오실레이터 (RSI, 스토캐스틱)
    MOMENTUM = "momentum"      # 모멘텀 (MACD)
    VOLUME = "volume"          # 거래량 관련
    VOLATILITY = "volatility"  # 변동성 (ATR)
    FINANCIAL = "financial"    # 자산/수익률 관련
    CUSTOM = "custom"          # 사용자 정의


class ScaleType(Enum):
    """스케일 타입 분류"""
    PRICE_SCALE = "price"      # 가격 단위 (원, 달러)
    PERCENT_SCALE = "percent"  # 퍼센트 단위 (0-100)
    VOLUME_SCALE = "volume"    # 거래량 단위
    RATIO_SCALE = "ratio"      # 비율 단위 (배수)
    NORMALIZED = "normalized"  # 정규화된 값 (0-1)


class AdvancedCompatibilityValidator:
    """고급 호환성 검증 시스템"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 기본 호환성 검증기
        self.hybrid_validator = None
        if HYBRID_SYSTEM_AVAILABLE:
            try:
                self.hybrid_validator = HybridCompatibilityValidator()
                print("✅ HybridCompatibilityValidator 연동 성공")
            except Exception as e:
                print(f"⚠️ HybridCompatibilityValidator 연동 실패: {e}")
        
        # 고급 타입 매핑
        self.variable_type_mapping = self._init_type_mapping()
        self.scale_type_mapping = self._init_scale_mapping()
        self.compatibility_matrix = self._init_compatibility_matrix()
    
    def _init_type_mapping(self) -> Dict[str, VariableType]:
        """변수 ID를 타입으로 매핑"""
        return {
            # 가격 관련
            "CURRENT_PRICE": VariableType.PRICE,
            "OPEN_PRICE": VariableType.PRICE,
            "HIGH_PRICE": VariableType.PRICE,
            "LOW_PRICE": VariableType.PRICE,
            
            # 가격 기반 지표
            "SMA": VariableType.PRICE_INDICATOR,
            "EMA": VariableType.PRICE_INDICATOR,
            "BOLLINGER_BANDS": VariableType.PRICE_INDICATOR,
            "BOLLINGER_BAND": VariableType.PRICE_INDICATOR,  # 레거시
            
            # 오실레이터
            "RSI": VariableType.OSCILLATOR,
            "STOCHASTIC": VariableType.OSCILLATOR,
            "CUSTOM_RSI_SMA": VariableType.OSCILLATOR,
            
            # 모멘텀
            "MACD": VariableType.MOMENTUM,
            
            # 거래량
            "VOLUME": VariableType.VOLUME,
            "VOLUME_SMA": VariableType.VOLUME,
            "VOLUME_PRICE_TREND": VariableType.VOLUME,
            
            # 변동성
            "ATR": VariableType.VOLATILITY,
            
            # 금융/자산
            "CASH_BALANCE": VariableType.FINANCIAL,
            "COIN_BALANCE": VariableType.FINANCIAL,
            "TOTAL_BALANCE": VariableType.FINANCIAL,
            "PROFIT_PERCENT": VariableType.FINANCIAL,
            "PROFIT_AMOUNT": VariableType.FINANCIAL,
            "POSITION_SIZE": VariableType.FINANCIAL,
            "AVG_BUY_PRICE": VariableType.FINANCIAL,
            
            # 사용자 정의
            "PRICE_MOMENTUM": VariableType.CUSTOM,
            "TEST_INDICATOR": VariableType.CUSTOM,
        }
    
    def _init_scale_mapping(self) -> Dict[str, ScaleType]:
        """변수 ID를 스케일 타입으로 매핑"""
        return {
            # 가격 스케일
            "CURRENT_PRICE": ScaleType.PRICE_SCALE,
            "OPEN_PRICE": ScaleType.PRICE_SCALE,
            "HIGH_PRICE": ScaleType.PRICE_SCALE,
            "LOW_PRICE": ScaleType.PRICE_SCALE,
            "SMA": ScaleType.PRICE_SCALE,
            "EMA": ScaleType.PRICE_SCALE,
            "BOLLINGER_BANDS": ScaleType.PRICE_SCALE,
            "BOLLINGER_BAND": ScaleType.PRICE_SCALE,
            "AVG_BUY_PRICE": ScaleType.PRICE_SCALE,
            
            # 퍼센트 스케일
            "RSI": ScaleType.PERCENT_SCALE,
            "STOCHASTIC": ScaleType.PERCENT_SCALE,
            "PROFIT_PERCENT": ScaleType.PERCENT_SCALE,
            
            # 거래량 스케일
            "VOLUME": ScaleType.VOLUME_SCALE,
            "VOLUME_SMA": ScaleType.VOLUME_SCALE,
            
            # 비율 스케일
            "MACD": ScaleType.RATIO_SCALE,
            "ATR": ScaleType.RATIO_SCALE,
            "PRICE_MOMENTUM": ScaleType.RATIO_SCALE,
            
            # 가격 스케일 (자산)
            "CASH_BALANCE": ScaleType.PRICE_SCALE,
            "COIN_BALANCE": ScaleType.PRICE_SCALE,
            "TOTAL_BALANCE": ScaleType.PRICE_SCALE,
            "PROFIT_AMOUNT": ScaleType.PRICE_SCALE,
            "POSITION_SIZE": ScaleType.PRICE_SCALE,
        }
    
    def _init_compatibility_matrix(self) -> Dict[Tuple[VariableType, VariableType], bool]:
        """호환성 매트릭스 초기화"""
        matrix = {}
        
        # 같은 타입은 항상 호환
        for var_type in VariableType:
            matrix[(var_type, var_type)] = True
        
        # 가격과 가격 지표 호환
        matrix[(VariableType.PRICE, VariableType.PRICE_INDICATOR)] = True
        matrix[(VariableType.PRICE_INDICATOR, VariableType.PRICE)] = True
        
        # 오실레이터 간 호환
        matrix[(VariableType.OSCILLATOR, VariableType.OSCILLATOR)] = True
        
        # 거래량 관련 호환
        matrix[(VariableType.VOLUME, VariableType.VOLUME)] = True
        
        # 금융 관련 호환
        matrix[(VariableType.FINANCIAL, VariableType.FINANCIAL)] = True
        
        # 사용자 정의는 제한적 호환
        matrix[(VariableType.CUSTOM, VariableType.PRICE)] = True
        matrix[(VariableType.CUSTOM, VariableType.PRICE_INDICATOR)] = True
        matrix[(VariableType.PRICE, VariableType.CUSTOM)] = True
        matrix[(VariableType.PRICE_INDICATOR, VariableType.CUSTOM)] = True
        
        return matrix
    
    def get_variable_type(self, var_id: str) -> VariableType:
        """변수의 타입 반환"""
        return self.variable_type_mapping.get(var_id, VariableType.CUSTOM)
    
    def get_scale_type(self, var_id: str) -> ScaleType:
        """변수의 스케일 타입 반환"""
        return self.scale_type_mapping.get(var_id, ScaleType.NORMALIZED)
    
    def check_type_compatibility(self, var1_id: str, var2_id: str) -> Tuple[bool, str]:
        """타입 기반 호환성 검증"""
        type1 = self.get_variable_type(var1_id)
        type2 = self.get_variable_type(var2_id)
        
        # 호환성 매트릭스에서 확인
        is_compatible = self.compatibility_matrix.get((type1, type2), False)
        
        if is_compatible:
            if type1 == type2:
                return True, f"같은 타입: {type1.value}"
            else:
                return True, f"호환 타입: {type1.value} ↔ {type2.value}"
        else:
            return False, f"비호환 타입: {type1.value} vs {type2.value}"
    
    def check_scale_compatibility(self, var1_id: str, var2_id: str) -> Tuple[bool, str]:
        """스케일 기반 호환성 검증"""
        scale1 = self.get_scale_type(var1_id)
        scale2 = self.get_scale_type(var2_id)
        
        if scale1 == scale2:
            return True, f"같은 스케일: {scale1.value}"
        
        # 스케일 변환 가능한 경우들
        convertible_pairs = [
            (ScaleType.PRICE_SCALE, ScaleType.RATIO_SCALE),  # 가격 <-> 비율
            (ScaleType.PERCENT_SCALE, ScaleType.NORMALIZED), # 퍼센트 <-> 정규화
        ]
        
        for pair in convertible_pairs:
            if (scale1, scale2) in [pair, pair[::-1]]:
                return True, f"변환 가능: {scale1.value} ↔ {scale2.value}"
        
        return False, f"스케일 비호환: {scale1.value} vs {scale2.value}"
    
    def validate_advanced_compatibility(self, var1_id: str, var2_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """고급 호환성 검증 (종합)"""
        result = {
            "hybrid_check": None,
            "type_check": None,
            "scale_check": None,
            "final_decision": None,
            "confidence": 0.0
        }
        
        # 1. 하이브리드 검증기 우선 사용
        if self.hybrid_validator:
            try:
                is_hybrid_compatible, hybrid_reason = self.hybrid_validator.is_compatible(var1_id, var2_id)
                result["hybrid_check"] = (is_hybrid_compatible, hybrid_reason)
            except Exception as e:
                self.logger.warning(f"하이브리드 검증 실패: {e}")
        
        # 2. 타입 기반 검증
        is_type_compatible, type_reason = self.check_type_compatibility(var1_id, var2_id)
        result["type_check"] = (is_type_compatible, type_reason)
        
        # 3. 스케일 기반 검증
        is_scale_compatible, scale_reason = self.check_scale_compatibility(var1_id, var2_id)
        result["scale_check"] = (is_scale_compatible, scale_reason)
        
        # 4. 종합 판정
        checks = []
        if result["hybrid_check"]:
            checks.append(result["hybrid_check"][0])
        checks.extend([is_type_compatible, is_scale_compatible])
        
        # 모든 검증을 통과해야 호환
        final_compatible = all(checks)
        
        # 신뢰도 계산
        confidence = sum(checks) / len(checks) if checks else 0.0
        result["confidence"] = confidence
        
        # 최종 이유 구성
        reasons = []
        if result["hybrid_check"]:
            reasons.append(f"하이브리드: {result['hybrid_check'][1]}")
        reasons.append(f"타입: {type_reason}")
        reasons.append(f"스케일: {scale_reason}")
        
        final_reason = " | ".join(reasons)
        result["final_decision"] = (final_compatible, final_reason)
        
        return final_compatible, final_reason, result


# ValidationUtils 확장
class ExtendedValidationUtils:
    """확장된 검증 유틸리티"""
    
    def __init__(self):
        self.advanced_validator = AdvancedCompatibilityValidator()
    
    def validate_variable_combination(self, variables: List[str]) -> Dict[str, Any]:
        """여러 변수의 조합 호환성 검증"""
        if len(variables) < 2:
            return {"valid": True, "message": "단일 변수"}
        
        results = {
            "valid": True,
            "incompatible_pairs": [],
            "warnings": [],
            "detailed_results": {}
        }
        
        # 모든 쌍에 대해 검증
        for i in range(len(variables)):
            for j in range(i + 1, len(variables)):
                var1, var2 = variables[i], variables[j]
                
                is_compatible, reason, details = self.advanced_validator.validate_advanced_compatibility(var1, var2)
                
                pair_key = f"{var1}↔{var2}"
                results["detailed_results"][pair_key] = details
                
                if not is_compatible:
                    results["valid"] = False
                    results["incompatible_pairs"].append((var1, var2, reason))
                elif details["confidence"] < 0.8:
                    results["warnings"].append((var1, var2, f"낮은 신뢰도: {details['confidence']:.1%}"))
        
        return results
    
    def suggest_compatible_alternatives(self, var_id: str, candidate_vars: List[str]) -> List[Tuple[str, float, str]]:
        """호환 가능한 대안 변수 제안"""
        alternatives = []
        
        for candidate in candidate_vars:
            if candidate == var_id:
                continue
            
            is_compatible, reason, details = self.advanced_validator.validate_advanced_compatibility(var_id, candidate)
            
            if is_compatible:
                confidence = details["confidence"]
                alternatives.append((candidate, confidence, reason))
        
        # 신뢰도 순으로 정렬
        alternatives.sort(key=lambda x: x[1], reverse=True)
        
        return alternatives


def test_advanced_compatibility():
    """고급 호환성 검증 테스트"""
    print("🧪 Step 2.2 고급 호환성 검증 테스트")
    print("=" * 60)
    
    validator = AdvancedCompatibilityValidator()
    extended_utils = ExtendedValidationUtils()
    
    # 1. 기본 호환성 테스트
    print("\n1️⃣ 기본 호환성 테스트:")
    test_pairs = [
        ("SMA", "EMA"),
        ("RSI", "STOCHASTIC"), 
        ("SMA", "RSI"),
        ("CURRENT_PRICE", "SMA"),
        ("VOLUME", "VOLUME_SMA"),
        ("CASH_BALANCE", "PROFIT_AMOUNT")
    ]
    
    for var1, var2 in test_pairs:
        is_compatible, reason, details = validator.validate_advanced_compatibility(var1, var2)
        status = "✅" if is_compatible else "❌"
        confidence = details["confidence"]
        print(f"  {status} {var1} ↔ {var2}: {reason[:60]}... (신뢰도: {confidence:.1%})")
    
    # 2. 조합 검증 테스트
    print(f"\n2️⃣ 조합 검증 테스트:")
    test_combinations = [
        ["SMA", "EMA", "CURRENT_PRICE"],
        ["RSI", "STOCHASTIC", "MACD"],
        ["SMA", "RSI", "VOLUME"]  # 혼합 타입
    ]
    
    for combo in test_combinations:
        result = extended_utils.validate_variable_combination(combo)
        status = "✅" if result["valid"] else "❌"
        combo_str = " + ".join(combo)
        print(f"  {status} {combo_str}")
        
        if result["incompatible_pairs"]:
            for var1, var2, reason in result["incompatible_pairs"]:
                print(f"    ⚠️ {var1} ↔ {var2}: {reason[:50]}...")
    
    # 3. 대안 제안 테스트
    print(f"\n3️⃣ 대안 제안 테스트:")
    test_var = "SMA"
    candidates = ["EMA", "RSI", "CURRENT_PRICE", "BOLLINGER_BANDS", "VOLUME"]
    
    alternatives = extended_utils.suggest_compatible_alternatives(test_var, candidates)
    print(f"  {test_var}와 호환 가능한 대안들:")
    
    for alt_var, confidence, reason in alternatives[:3]:  # 상위 3개만
        print(f"    • {alt_var}: {confidence:.1%} - {reason[:40]}...")
    
    print(f"\n🎉 Step 2.2 고급 호환성 검증 완료!")
    return True


if __name__ == "__main__":
    success = test_advanced_compatibility()
    if success:
        print(f"\n🚀 다음 단계: Step 3.1 - 트리거 빌더 변수 로딩 테스트")
    else:
        print(f"\n🔧 문제 해결 후 다시 시도해주세요")
