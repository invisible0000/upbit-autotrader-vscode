#!/usr/bin/env python
"""
도메인 서비스 단위 테스트 검증 스크립트

pytest 없이 기본 Python으로 테스트 동작 확인
"""

import sys
import os
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def test_normalization_service():
    """NormalizationService 기본 동작 테스트"""
    print("🧪 NormalizationService 테스트 시작...")
    
    try:
        from upbit_auto_trading.domain.services.normalization_service import (
            NormalizationService, NormalizationMethod, NormalizationParameters
        )
        
        service = NormalizationService()
        print("✅ NormalizationService 임포트 성공")
        
        # 같은 그룹 간 정규화 테스트
        result = service.normalize_for_comparison(
            75.0, "percentage_comparable",
            80.0, "percentage_comparable"
        )
        
        assert result.normalized_value1 == 75.0
        assert result.normalized_value2 == 80.0
        assert result.confidence_score == 1.0
        print("✅ 같은 그룹 간 정규화 불필요 테스트 통과")
        
        # 다른 그룹 간 정규화 테스트
        result = service.normalize_for_comparison(
            50000.0, "price_comparable",
            75.0, "percentage_comparable"
        )
        
        assert result.original_value1 == 50000.0
        assert result.original_value2 == 75.0
        assert 0.0 <= result.normalized_value1 <= 1.0
        assert 0.0 <= result.normalized_value2 <= 1.0
        print("✅ 다른 그룹 간 정규화 테스트 통과")
        
        print("🎉 NormalizationService 모든 테스트 통과!")
        return True
        
    except Exception as e:
        print(f"❌ NormalizationService 테스트 실패: {e}")
        return False


def test_strategy_compatibility_service():
    """StrategyCompatibilityService 기본 동작 테스트"""
    print("\n🧪 StrategyCompatibilityService 테스트 시작...")
    
    try:
        from upbit_auto_trading.domain.services.strategy_compatibility_service import (
            StrategyCompatibilityService
        )
        from upbit_auto_trading.domain.entities.trigger import TradingVariable
        
        service = StrategyCompatibilityService()
        print("✅ StrategyCompatibilityService 임포트 성공")
        
        # 테스트용 변수들
        price_var = TradingVariable(
            variable_id="Close",
            display_name="종가",
            purpose_category="price",
            chart_category="overlay",
            comparison_group="price_comparable"
        )
        
        rsi_var = TradingVariable(
            variable_id="RSI_14",
            display_name="RSI",
            purpose_category="momentum",
            chart_category="subplot",
            comparison_group="percentage_comparable"
        )
        
        # 같은 그룹 간 호환성 테스트
        sma_var = TradingVariable(
            variable_id="SMA_20",
            display_name="20일 이동평균",
            purpose_category="trend",
            chart_category="overlay",
            comparison_group="price_comparable"
        )
        
        result = service.check_variable_compatibility(price_var, sma_var)
        assert result.is_compatible is True
        assert result.level.value == "PERFECT"
        print("✅ 같은 그룹 간 완벽 호환성 테스트 통과")
        
        # 다른 그룹 간 WARNING 수준 호환성 테스트
        result = service.check_variable_compatibility(price_var, rsi_var)
        assert result.is_compatible is True
        assert result.level.value == "WARNING"
        assert result.normalization_required is True
        print("✅ 다른 그룹 간 WARNING 수준 호환성 테스트 통과")
        
        print("🎉 StrategyCompatibilityService 모든 테스트 통과!")
        return True
        
    except Exception as e:
        print(f"❌ StrategyCompatibilityService 테스트 실패: {e}")
        return False


def test_trigger_evaluation_service():
    """TriggerEvaluationService 기본 동작 테스트"""
    print("\n🧪 TriggerEvaluationService 테스트 시작...")
    
    try:
        from upbit_auto_trading.domain.services.trigger_evaluation_service import (
            TriggerEvaluationService, MarketData
        )
        from upbit_auto_trading.domain.entities.trigger import (
            TriggerCondition, TradingVariable, ComparisonOperator
        )
        
        service = TriggerEvaluationService()
        print("✅ TriggerEvaluationService 임포트 성공")
        
        # 테스트용 시장 데이터
        market_data = MarketData(
            symbol="KRW-BTC",
            timestamp=datetime.now(),
            close_price=45500000.0,
            indicators={"RSI_14": 75.0}
        )
        
        # 테스트용 조건
        rsi_variable = TradingVariable(
            variable_id="RSI_14",
            display_name="RSI",
            purpose_category="momentum",
            chart_category="subplot",
            comparison_group="percentage_comparable"
        )
        
        condition = TriggerCondition(
            condition_id="RSI_OVERBOUGHT",
            variable=rsi_variable,
            operator=ComparisonOperator.GREATER_THAN,
            target_value=70.0
        )
        
        # 단일 조건 평가 테스트
        result = service.evaluate_single_condition(condition, market_data)
        assert result is True  # RSI 75 > 70
        print("✅ 단일 조건 평가 테스트 통과")
        
        print("🎉 TriggerEvaluationService 모든 테스트 통과!")
        return True
        
    except Exception as e:
        print(f"❌ TriggerEvaluationService 테스트 실패: {e}")
        return False


def test_integration():
    """도메인 서비스 통합 테스트"""
    print("\n🧪 도메인 서비스 통합 테스트 시작...")
    
    try:
        from upbit_auto_trading.domain.services.strategy_compatibility_service import (
            StrategyCompatibilityService
        )
        from upbit_auto_trading.domain.services.normalization_service import (
            NormalizationService, NormalizationMethod
        )
        from upbit_auto_trading.domain.entities.trigger import TradingVariable
        
        compatibility_service = StrategyCompatibilityService()
        normalization_service = NormalizationService()
        
        # 변수들
        price_var = TradingVariable(
            variable_id="Close",
            display_name="종가",
            purpose_category="price",
            chart_category="overlay",
            comparison_group="price_comparable"
        )
        
        rsi_var = TradingVariable(
            variable_id="RSI_14",
            display_name="RSI",
            purpose_category="momentum",
            chart_category="subplot",
            comparison_group="percentage_comparable"
        )
        
        # 1. 호환성 검증
        compatibility_result = compatibility_service.check_variable_compatibility(
            price_var, rsi_var
        )
        
        assert compatibility_result.level.value == "WARNING"
        assert compatibility_result.normalization_required is True
        print("✅ WARNING 수준 호환성 검증 통과")
        
        # 2. 정규화 수행
        normalization_result = normalization_service.normalize_for_comparison(
            45500000.0, "price_comparable",
            75.0, "percentage_comparable"
        )
        
        assert normalization_result.original_value1 == 45500000.0
        assert normalization_result.original_value2 == 75.0
        assert 0.0 <= normalization_result.normalized_value1 <= 1.0
        assert 0.0 <= normalization_result.normalized_value2 <= 1.0
        print("✅ 정규화 수행 통과")
        
        print("🎉 도메인 서비스 통합 테스트 모든 테스트 통과!")
        return True
        
    except Exception as e:
        print(f"❌ 통합 테스트 실패: {e}")
        return False


def main():
    """메인 테스트 실행"""
    print("🚀 도메인 서비스 단위 테스트 검증 시작")
    print("=" * 60)
    
    tests = [
        test_normalization_service,
        test_strategy_compatibility_service,
        test_trigger_evaluation_service,
        test_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 테스트 실행 중 오류: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("🎉 모든 도메인 서비스 테스트가 성공적으로 통과했습니다!")
        return True
    else:
        print("❌ 일부 테스트가 실패했습니다.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
