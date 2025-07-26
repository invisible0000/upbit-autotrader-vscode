"""
트레이딩 지표 변수 호환성 테스트

이 테스트 파일은 다음을 검증합니다:
1. SMA-EMA 호환성 문제 해결 확인 
2. RSI-STOCH 등 모멘텀 지표 호환성
3. 비호환 케이스 (RSI-VOLUME) 정상 동작
4. 자동 분류 시스템 정확도

실행 방법:
    python -m pytest tests/test_variable_compatibility.py -v
    또는
    python tests/test_variable_compatibility.py
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from upbit_auto_trading.utils.trading_variables.variable_manager import SimpleVariableManager
from upbit_auto_trading.utils.trading_variables.indicator_classifier import SmartIndicatorClassifier


class TestTradingVariableCompatibility(unittest.TestCase):
    """트레이딩 지표 호환성 테스트"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        # 임시 DB 파일 생성
        cls.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        cls.test_db_path = cls.test_db.name
        cls.test_db.close()
        
        # 테스트용 변수 관리자 생성
        cls.vm = SimpleVariableManager(cls.test_db_path)
        cls.classifier = SmartIndicatorClassifier()
        
        print(f"📁 테스트 DB 생성: {cls.test_db_path}")
    
    @classmethod 
    def tearDownClass(cls):
        """테스트 클래스 정리"""
        cls.vm.close()
        os.unlink(cls.test_db_path)
        print(f"🗑️ 테스트 DB 삭제: {cls.test_db_path}")
    
    def test_01_db_initialization(self):
        """DB 초기화 및 기본 데이터 확인"""
        stats = self.vm.get_statistics()
        
        # 최소 30개 지표가 있어야 함
        self.assertGreaterEqual(stats['active_variables'], 30, 
                               "활성 지표가 30개 미만입니다")
        
        # 5개 주요 카테고리 존재 확인
        expected_categories = ['trend', 'momentum', 'volatility', 'volume', 'price']
        for category in expected_categories:
            self.assertIn(category, stats['by_category'], 
                         f"{category} 카테고리가 없습니다")
            self.assertGreater(stats['by_category'][category], 0,
                              f"{category} 카테고리에 지표가 없습니다")
        
        print(f"✅ DB 초기화 성공: {stats['active_variables']}개 활성 지표")
    
    def test_02_sma_ema_compatibility(self):
        """핵심 테스트: SMA-EMA 호환성 문제 해결 확인"""
        
        # SMA와 호환 가능한 변수들 조회
        compatible = self.vm.get_compatible_variables('SMA')
        variable_ids = [var[0] for var in compatible]
        
        # EMA가 포함되어 있는지 확인
        self.assertIn('EMA', variable_ids, 
                     "SMA와 EMA가 호환되지 않습니다! 핵심 문제가 해결되지 않았습니다.")
        
        # 직접 호환성 확인
        result = self.vm.check_compatibility('SMA', 'EMA')
        self.assertTrue(result['compatible'], 
                       f"SMA-EMA 호환성 실패: {result['reason']}")
        
        # 추세 지표 카테고리 확인
        self.assertEqual(result['var1_info']['purpose'], 'trend',
                        "SMA가 trend 카테고리가 아닙니다")
        self.assertEqual(result['var2_info']['purpose'], 'trend', 
                        "EMA가 trend 카테고리가 아닙니다")
        
        print(f"✅ SMA-EMA 호환성 해결: {result['reason']}")
        print(f"✅ SMA 호환 지표 {len(compatible)}개: {[v[1] for v in compatible]}")
    
    def test_03_momentum_indicators_compatibility(self):
        """모멘텀 지표들 간 호환성 테스트"""
        
        # RSI와 호환 가능한 지표들
        rsi_compatible = self.vm.get_compatible_variables('RSI')
        rsi_ids = [var[0] for var in rsi_compatible]
        
        # 스토캐스틱이 포함되어 있어야 함
        self.assertIn('STOCH', rsi_ids, "RSI와 STOCH가 호환되지 않습니다")
        
        # RSI-STOCH 직접 호환성 확인
        result = self.vm.check_compatibility('RSI', 'STOCH')
        self.assertTrue(result['compatible'], 
                       f"RSI-STOCH 호환성 실패: {result['reason']}")
        
        # 윌리엄스 %R과도 호환되어야 함
        if 'WILLIAMS_R' in [v['variable_id'] for v in self.vm.get_all_variables()]:
            self.assertIn('WILLIAMS_R', rsi_ids, "RSI와 윌리엄스 %R이 호환되지 않습니다")
        
        print(f"✅ RSI 호환 모멘텀 지표 {len(rsi_compatible)}개")
    
    def test_04_incompatible_cases(self):
        """비호환 케이스 정상 동작 확인"""
        
        # RSI(모멘텀) vs VOLUME(거래량) - 호환되지 않아야 함
        result = self.vm.check_compatibility('RSI', 'VOLUME')
        self.assertFalse(result['compatible'], 
                        "RSI와 VOLUME이 호환된다고 나옵니다 (잘못된 결과)")
        
        # SMA(추세) vs ATR(변동성) - 호환되지 않아야 함
        result = self.vm.check_compatibility('SMA', 'ATR')
        self.assertFalse(result['compatible'],
                        "SMA와 ATR이 호환된다고 나옵니다 (잘못된 결과)")
        
        # 존재하지 않는 지표
        result = self.vm.check_compatibility('NONEXISTENT', 'SMA')
        self.assertFalse(result['compatible'])
        self.assertIn('찾을 수 없음', result['reason'])
        
        print("✅ 비호환 케이스 정상 동작 확인")
    
    def test_05_category_grouping(self):
        """카테고리별 그룹화 테스트"""
        
        # 추세 지표들 조회
        trend_indicators = self.vm.get_variables_by_category('trend')
        self.assertGreater(len(trend_indicators), 0, "추세 지표가 없습니다")
        
        # SMA, EMA가 추세 카테고리에 있는지 확인
        trend_ids = [var['variable_id'] for var in trend_indicators]
        self.assertIn('SMA', trend_ids, "SMA가 추세 카테고리에 없습니다")
        self.assertIn('EMA', trend_ids, "EMA가 추세 카테고리에 없습니다")
        
        # 모멘텀 지표들 조회
        momentum_indicators = self.vm.get_variables_by_category('momentum')
        momentum_ids = [var['variable_id'] for var in momentum_indicators]
        self.assertIn('RSI', momentum_ids, "RSI가 모멘텀 카테고리에 없습니다")
        
        print(f"✅ 카테고리 분류: 추세 {len(trend_indicators)}개, 모멘텀 {len(momentum_indicators)}개")
    
    def test_06_indicator_classifier_basic(self):
        """자동 분류 시스템 기본 테스트"""
        
        # 이동평균 분류 테스트
        result = self.classifier.classify_indicator("Hull Moving Average", "부드러운 이동평균")
        self.assertEqual(result['purpose_category'], 'trend', 
                        "헐 이동평균이 추세 카테고리로 분류되지 않았습니다")
        self.assertEqual(result['chart_category'], 'overlay',
                        "이동평균이 overlay로 분류되지 않았습니다")
        
        # RSI 계열 분류 테스트
        result = self.classifier.classify_indicator("Stochastic RSI", "RSI에 스토캐스틱 적용")
        self.assertEqual(result['purpose_category'], 'momentum',
                        "스토캐스틱 RSI가 모멘텀 카테고리로 분류되지 않았습니다")
        self.assertEqual(result['comparison_group'], 'percentage_comparable',
                        "RSI 계열이 percentage_comparable로 분류되지 않았습니다")
        
        # 거래량 지표 분류 테스트
        result = self.classifier.classify_indicator("On Balance Volume", "거래량 흐름 지표")
        self.assertEqual(result['purpose_category'], 'volume',
                        "OBV가 거래량 카테고리로 분류되지 않았습니다")
        
        print("✅ 자동 분류 시스템 기본 동작 확인")
    
    def test_07_classifier_confidence(self):
        """분류 신뢰도 테스트"""
        
        # 명확한 지표들은 높은 신뢰도를 가져야 함
        high_confidence_cases = [
            ("Simple Moving Average", "단순 이동평균"),
            ("RSI Indicator", "상대강도지수"),
            ("Volume Profile", "거래량 프로파일")
        ]
        
        for name, desc in high_confidence_cases:
            result = self.classifier.classify_indicator(name, desc)
            self.assertGreaterEqual(result['confidence'], 0.7,
                                   f"{name}의 신뢰도가 낮습니다: {result['confidence']:.1%}")
        
        # 모호한 지표는 낮은 신뢰도 + 경고
        result = self.classifier.classify_indicator("Custom Indicator", "")
        # 기본값으로도 어느 정도 신뢰도는 있어야 함
        self.assertGreater(result['confidence'], 0.3,
                          "기본 분류 신뢰도가 너무 낮습니다")
        
        print("✅ 분류 신뢰도 시스템 정상 동작")
    
    def test_08_comparison_groups(self):
        """비교 그룹 분류 정확성 테스트"""
        
        # 가격 비교 가능 그룹
        price_comparable = ['SMA', 'EMA', 'CURRENT_PRICE', 'SUPERTREND']
        for var_id in price_comparable:
            if var_id in [v['variable_id'] for v in self.vm.get_all_variables()]:
                vars_info = self.vm.get_all_variables()
                var_info = next((v for v in vars_info if v['variable_id'] == var_id), None)
                if var_info:
                    self.assertEqual(var_info['comparison_group'], 'price_comparable',
                                   f"{var_id}가 price_comparable 그룹이 아닙니다")
        
        # 퍼센트 비교 가능 그룹
        percentage_comparable = ['RSI', 'STOCH', 'WILLIAMS_R', 'MFI']
        for var_id in percentage_comparable:
            if var_id in [v['variable_id'] for v in self.vm.get_all_variables()]:
                vars_info = self.vm.get_all_variables()
                var_info = next((v for v in vars_info if v['variable_id'] == var_id), None)
                if var_info:
                    self.assertEqual(var_info['comparison_group'], 'percentage_comparable',
                                   f"{var_id}가 percentage_comparable 그룹이 아닙니다")
        
        print("✅ 비교 그룹 분류 정확성 확인")
    
    def test_09_database_operations(self):
        """DB 운영 기능 테스트"""
        
        # 새 지표 추가 테스트
        test_var_id = 'TEST_INDICATOR'
        success = self.vm.add_variable(
            variable_id=test_var_id,
            display_name_ko='테스트 지표',
            purpose_category='momentum',
            chart_category='subplot', 
            comparison_group='percentage_comparable',
            description='테스트용 지표'
        )
        self.assertTrue(success, "새 지표 추가 실패")
        
        # 추가된 지표 활성화
        success = self.vm.activate_variable(test_var_id)
        self.assertTrue(success, "지표 활성화 실패")
        
        # 활성화 확인
        all_vars = self.vm.get_all_variables()
        test_var = next((v for v in all_vars if v['variable_id'] == test_var_id), None)
        self.assertIsNotNone(test_var, "추가된 지표를 찾을 수 없습니다")
        self.assertEqual(test_var['is_active'], 1, "지표가 활성화되지 않았습니다")
        
        # 비활성화 테스트
        success = self.vm.deactivate_variable(test_var_id)
        self.assertTrue(success, "지표 비활성화 실패")
        
        print("✅ DB 운영 기능 정상 동작")


def run_compatibility_tests():
    """호환성 테스트 실행"""
    print("🧪 트레이딩 지표 변수 호환성 테스트 시작")
    print("=" * 60)
    
    # 테스트 스위트 생성
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTradingVariableCompatibility)
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약:")
    print(f"   총 테스트: {result.testsRun}개")
    print(f"   성공: {result.testsRun - len(result.failures) - len(result.errors)}개")
    print(f"   실패: {len(result.failures)}개") 
    print(f"   오류: {len(result.errors)}개")
    
    if result.failures:
        print("\n❌ 실패한 테스트:")
        for test, traceback in result.failures:
            print(f"   - {test}")
    
    if result.errors:
        print("\n💥 오류 발생 테스트:")
        for test, traceback in result.errors:
            print(f"   - {test}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n🎉 모든 테스트 통과! SMA-EMA 호환성 문제 해결 확인!")
    else:
        print("\n⚠️ 일부 테스트 실패. 문제를 확인해주세요.")
    
    return success


if __name__ == "__main__":
    run_compatibility_tests()
