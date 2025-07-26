"""
통합 변수 관리자 - IndicatorCalculator와 기존 VariableDefinitions 통합
"""

import logging
from typing import Dict, Any, List, Tuple
try:
    from .indicator_calculator import IndicatorCalculator
except ImportError:
    from indicator_calculator import IndicatorCalculator


class IndicatorVariableAdapter:
    """
                 ("BOLLINGER_BAND", "볼린저밴드"),  # 기존 시스템과 호환
                ("MACD", "MACD 지표"),
                ("STOCHASTIC", "스토캐스틱")IndicatorCalculator의 지표들을 기존 VariableDefinitions 형식으로 변환하는 어댑터
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.indicator_calculator = IndicatorCalculator()
        
        # 지표 타입별 카테고리 매핑
        self.indicator_categories = {
            # 핵심 지표들 (기존 시스템과 호환되는 이름 사용)
            'SMA': 'price_overlay',
            'EMA': 'price_overlay',
            'BOLLINGER_BAND': 'price_overlay',  # 기존 시스템과 호환 (단수형)
            'RSI': 'oscillator',
            'STOCHASTIC': 'oscillator',
            'MACD': 'momentum',
            'ATR': 'volatility',
            'VOLUME_SMA': 'volume',
            
            # 사용자 정의 지표들 (동적 분류)
            'PRICE_MOMENTUM': 'custom_price',
            'VOLUME_PRICE_TREND': 'custom_volume',
            'CUSTOM_RSI_SMA': 'custom_oscillator'
        }
    
    def get_all_indicators_as_variables(self) -> Dict[str, List[Tuple[str, str]]]:
        """모든 지표를 변수 형식으로 반환"""
        try:
            # IndicatorCalculator에서 사용 가능한 지표 가져오기
            available_indicators = self.indicator_calculator.get_available_indicators()
            
            # 카테고리별로 변수 목록 구성
            categorized_variables = {}
            
            # 핵심 지표들
            for indicator in available_indicators['core']:
                indicator_id = indicator['id']
                indicator_name = self._get_korean_name(indicator_id)
                category = self._get_indicator_category(indicator_id)
                
                if category not in categorized_variables:
                    categorized_variables[category] = []
                categorized_variables[category].append((indicator_id, indicator_name))
            
            # 사용자 정의 지표들
            for indicator in available_indicators['custom']:
                indicator_id = indicator['id']
                indicator_name = indicator['name_ko']
                category = self._get_indicator_category(indicator_id)
                
                if category not in categorized_variables:
                    categorized_variables[category] = []
                categorized_variables[category].append((indicator_id, indicator_name))
            
            return categorized_variables
            
        except Exception as e:
            self.logger.error(f"지표를 변수로 변환 실패: {e}")
            return {}
    
    def get_indicator_parameters(self, indicator_id: str) -> Dict[str, Any]:
        """지표의 파라미터를 UI 형식으로 변환"""
        try:
            # 핵심 지표들의 기본 파라미터 매핑
            core_params = {
                'SMA': {
                    "period": {
                        "label": "기간",
                        "type": "int",
                        "min": 1,
                        "max": 240,
                        "default": 20,
                        "suffix": " 봉",
                        "help": "단순이동평균 계산 기간"
                    }
                },
                'EMA': {
                    "period": {
                        "label": "기간",
                        "type": "int",
                        "min": 1,
                        "max": 240,
                        "default": 12,
                        "suffix": " 봉",
                        "help": "지수이동평균 계산 기간"
                    }
                },
                'RSI': {
                    "period": {
                        "label": "기간",
                        "type": "int",
                        "min": 2,
                        "max": 240,
                        "default": 14,
                        "suffix": " 봉",
                        "help": "RSI 계산 기간"
                    }
                },
                'BOLLINGER_BAND': {  # 기존 시스템과 호환 (단수형)
                    "period": {
                        "label": "기간",
                        "type": "int",
                        "min": 10,
                        "max": 240,
                        "default": 20,
                        "suffix": " 봉",
                        "help": "볼린저밴드 계산 기간"
                    },
                    "std_dev": {
                        "label": "표준편차 배수",
                        "type": "float",
                        "default": 2.0,
                        "help": "밴드 폭 결정"
                    }
                },
                'MACD': {
                    "fast": {
                        "label": "빠른선",
                        "type": "int",
                        "default": 12,
                        "help": "MACD 빠른 이동평균"
                    },
                    "slow": {
                        "label": "느린선",
                        "type": "int",
                        "default": 26,
                        "help": "MACD 느린 이동평균"
                    },
                    "signal": {
                        "label": "시그널",
                        "type": "int",
                        "default": 9,
                        "help": "MACD 시그널선"
                    }
                },
                'ATR': {
                    "period": {
                        "label": "기간",
                        "type": "int",
                        "default": 14,
                        "help": "ATR 계산 기간"
                    },
                    "multiplier": {
                        "label": "배수",
                        "type": "float",
                        "default": 2.0,
                        "help": "ATR 배수 (손절가 계산용)"
                    }
                },
                'VOLUME_SMA': {
                    "period": {
                        "label": "기간",
                        "type": "int",
                        "default": 20,
                        "help": "거래량 이동평균 기간"
                    }
                }
            }
            
            if indicator_id in core_params:
                return core_params[indicator_id]
            
            # 사용자 정의 지표는 동적 파라미터 추출
            return self._extract_custom_indicator_params(indicator_id)
            
        except Exception as e:
            self.logger.error(f"지표 파라미터 변환 실패: {indicator_id}, {e}")
            return {}
    
    def _get_korean_name(self, indicator_id: str) -> str:
        """지표 ID를 한국어 이름으로 변환"""
        name_mapping = {
            'SMA': '단순이동평균',
            'EMA': '지수이동평균',
            'RSI': 'RSI',
            'MACD': 'MACD',
            'BOLLINGER_BAND': '볼린저밴드',  # 기존 시스템과 호환 (단수형)
            'STOCHASTIC': '스토캐스틱',
            'ATR': 'ATR',
            'VOLUME_SMA': '거래량 이동평균'
        }
        return name_mapping.get(indicator_id, indicator_id)
    
    def _get_indicator_category(self, indicator_id: str) -> str:
        """지표의 호환성 카테고리 결정"""
        return self.indicator_categories.get(indicator_id, 'custom')
    
    def _extract_custom_indicator_params(self, indicator_id: str) -> Dict[str, Any]:
        """사용자 정의 지표의 파라미터 추출"""
        try:
            # DB에서 사용자 정의 지표 정보 조회
            import sqlite3
            
            with sqlite3.connect(self.indicator_calculator.db_path) as conn:
                cursor = conn.execute("""
                SELECT parameters FROM custom_indicators 
                WHERE id = ? AND is_active = 1
                """, (indicator_id,))
                
                result = cursor.fetchone()
                if result and result[0]:
                    import json
                    stored_params = json.loads(result[0])
                    
                    # 저장된 파라미터를 UI 형식으로 변환
                    ui_params = {}
                    for param_name, param_value in stored_params.items():
                        ui_params[param_name] = {
                            "label": param_name.title(),
                            "type": self._infer_param_type(param_value),
                            "default": param_value,
                            "help": f"{param_name} 파라미터"
                        }
                    
                    return ui_params
            
        except Exception as e:
            self.logger.error(f"사용자 정의 지표 파라미터 추출 실패: {indicator_id}, {e}")
        
        return {}
    
    def _infer_param_type(self, value: Any) -> str:
        """값에서 파라미터 타입 추론"""
        if isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            return "string"
        else:
            return "string"


class IntegratedVariableManager:
    """
    기존 VariableDefinitions와 새 IndicatorCalculator를 통합하는 관리자
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.adapter = IndicatorVariableAdapter()
        self.legacy_variables = self._get_legacy_variables()
        
    def get_category_variables(self) -> Dict[str, List[Tuple[str, str]]]:
        """통합된 카테고리별 변수 목록 반환"""
        try:
            # 기존 변수들
            integrated_variables = self.legacy_variables.copy()
            
            # 새 지표들
            indicator_variables = self.adapter.get_all_indicators_as_variables()
            
            # 통합: 새 지표가 기존 카테고리와 겹치면 합치고, 없으면 새로 추가
            for category, variables in indicator_variables.items():
                if category in integrated_variables:
                    # 중복 제거하면서 합치기
                    existing_ids = {var[0] for var in integrated_variables[category]}
                    for var_id, var_name in variables:
                        if var_id not in existing_ids:
                            integrated_variables[category].append((var_id, var_name))
                else:
                    integrated_variables[category] = variables
            
            return integrated_variables
            
        except Exception as e:
            self.logger.error(f"통합 변수 목록 생성 실패: {e}")
            return self.legacy_variables
    
    def get_variable_parameters(self, var_id: str) -> Dict[str, Any]:
        """변수 파라미터 반환 (기존 + 새 지표)"""
        try:
            # 먼저 새 지표에서 찾아보기
            indicator_params = self.adapter.get_indicator_parameters(var_id)
            if indicator_params:
                return indicator_params
            
            # 기존 변수에서 찾기
            return self._get_legacy_variable_parameters(var_id)
            
        except Exception as e:
            self.logger.error(f"변수 파라미터 조회 실패: {var_id}, {e}")
            return {}
    
    def get_variable_descriptions(self) -> Dict[str, str]:
        """변수 설명 반환 (통합)"""
        descriptions = self._get_legacy_descriptions()
        
        # 새 지표 설명 추가
        try:
            available_indicators = self.adapter.indicator_calculator.get_available_indicators()
            
            for indicator in available_indicators['core']:
                descriptions[indicator['id']] = f"핵심 지표: {indicator['name']}"
            
            for indicator in available_indicators['custom']:
                descriptions[indicator['id']] = indicator.get('description', 'Custom indicator')
                
        except Exception as e:
            self.logger.error(f"지표 설명 추가 실패: {e}")
        
        return descriptions
    
    def is_hybrid_indicator(self, var_id: str) -> bool:
        """새 하이브리드 지표인지 확인"""
        try:
            available_indicators = self.adapter.indicator_calculator.get_available_indicators()
            
            # 핵심 지표 확인
            core_ids = [ind['id'] for ind in available_indicators['core']]
            if var_id in core_ids:
                return True
            
            # 사용자 정의 지표 확인
            custom_ids = [ind['id'] for ind in available_indicators['custom']]
            if var_id in custom_ids:
                return True
            
            return False
            
        except Exception:
            return False
    
    def _get_legacy_variables(self) -> Dict[str, List[Tuple[str, str]]]:
        """기존 하드코딩된 변수들 반환"""
        return {
            "indicator": [
                ("RSI", "RSI"),
                ("SMA", "단순이동평균"),
                ("EMA", "지수이동평균"),
                ("BOLLINGER_BAND", "볼린저밴드"),
                ("MACD", "MACD"),
                ("STOCHASTIC", "스토캐스틱")
            ],
            "price": [
                ("CURRENT_PRICE", "현재가"),
                ("OPEN_PRICE", "시가"),
                ("HIGH_PRICE", "고가"),
                ("LOW_PRICE", "저가")
            ],
            "capital": [
                ("CASH_BALANCE", "현금 잔고"),
                ("COIN_BALANCE", "코인 보유량"),
                ("TOTAL_BALANCE", "총 자산")
            ],
            "state": [
                ("PROFIT_PERCENT", "수익률(%)"),
                ("PROFIT_AMOUNT", "수익 금액"),
                ("POSITION_SIZE", "포지션 크기")
            ]
        }
    
    def _get_legacy_variable_parameters(self, var_id: str) -> Dict[str, Any]:
        """기존 변수 파라미터 반환 (하드코딩)"""
        legacy_params = {
            "RSI": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "min": 2,
                    "max": 240,
                    "default": 14,
                    "suffix": " 봉"
                }
            },
            "SMA": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "min": 1,
                    "max": 240,
                    "default": 20,
                    "suffix": " 봉"
                }
            }
            # 다른 기존 변수들...
        }
        return legacy_params.get(var_id, {})
    
    def _get_legacy_descriptions(self) -> Dict[str, str]:
        """기존 변수 설명 반환"""
        return {
            "RSI": "상대강도지수 - 과매수/과매도 판단",
            "SMA": "단순이동평균 - 추세 확인",
            "EMA": "지수이동평균 - 빠른 추세 반응",
            "CURRENT_PRICE": "현재 시장가격",
            "PROFIT_PERCENT": "현재 수익률 (%)"
        }


# ========== 호환성 검증 로직 업데이트 ==========

class HybridCompatibilityValidator:
    """
    기존 + 새 지표에 대한 통합 호환성 검증기
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.integrated_manager = IntegratedVariableManager()
        
        # 확장된 카테고리 매핑
        self.category_mapping = {
            # 기존 카테고리
            'price_overlay': ['CURRENT_PRICE', 'SMA', 'EMA', 'BOLLINGER_BAND'],  # 기존 시스템과 호환
            'oscillator': ['RSI', 'STOCHASTIC'],
            'momentum': ['MACD'],
            'volume': ['VOLUME', 'VOLUME_SMA'],
            
            # 새로운 카테고리
            'custom_price': ['PRICE_MOMENTUM'],
            'custom_volume': ['VOLUME_PRICE_TREND'],
            'custom_oscillator': ['CUSTOM_RSI_SMA'],
            'volatility': ['ATR']
        }
    
    def is_compatible(self, var1_id: str, var2_id: str) -> Tuple[bool, str]:
        """두 변수/지표의 호환성 검증"""
        try:
            # 1. 같은 변수면 호환
            if var1_id == var2_id:
                return True, "동일한 변수"
            
            # 2. 하이브리드 지표인지 확인
            is_var1_hybrid = self.integrated_manager.is_hybrid_indicator(var1_id)
            is_var2_hybrid = self.integrated_manager.is_hybrid_indicator(var2_id)
            
            # 3. 둘 다 하이브리드 지표인 경우
            if is_var1_hybrid and is_var2_hybrid:
                return self._check_hybrid_compatibility(var1_id, var2_id)
            
            # 4. 하나는 하이브리드, 하나는 기존인 경우
            elif is_var1_hybrid or is_var2_hybrid:
                return self._check_mixed_compatibility(var1_id, var2_id)
            
            # 5. 둘 다 기존 변수인 경우 (레거시 로직)
            else:
                return self._check_legacy_compatibility(var1_id, var2_id)
                
        except Exception as e:
            self.logger.error(f"호환성 검증 실패: {var1_id} vs {var2_id}, {e}")
            return False, f"검증 오류: {e}"
    
    def _check_hybrid_compatibility(self, var1_id: str, var2_id: str) -> Tuple[bool, str]:
        """하이브리드 지표 간 호환성 검증"""
        # 카테고리 기반 호환성 검증
        var1_category = self._get_variable_category(var1_id)
        var2_category = self._get_variable_category(var2_id)
        
        # 같은 카테고리이거나 호환 가능한 카테고리인지 확인
        compatible_groups = [
            ['price_overlay', 'custom_price'],  # 가격 관련
            ['oscillator', 'custom_oscillator'],  # 오실레이터
            ['volume', 'custom_volume']  # 거래량 관련
        ]
        
        for group in compatible_groups:
            if var1_category in group and var2_category in group:
                return True, f"호환 그룹: {group[0]} 계열"
        
        if var1_category == var2_category:
            return True, f"같은 카테고리: {var1_category}"
        
        return False, f"다른 카테고리: {var1_category} vs {var2_category}"
    
    def _check_mixed_compatibility(self, var1_id: str, var2_id: str) -> Tuple[bool, str]:
        """하이브리드와 기존 변수 간 호환성 검증"""
        # 기존 변수를 하이브리드 카테고리로 매핑
        legacy_to_hybrid = {
            'RSI': 'oscillator',
            'SMA': 'price_overlay',
            'EMA': 'price_overlay',
            'CURRENT_PRICE': 'price_overlay',
            'MACD': 'momentum'
        }
        
        var1_category = self._get_variable_category(var1_id)
        var2_category = self._get_variable_category(var2_id)
        
        # 레거시 변수 카테고리 변환
        if var1_id in legacy_to_hybrid:
            var1_category = legacy_to_hybrid[var1_id]
        if var2_id in legacy_to_hybrid:
            var2_category = legacy_to_hybrid[var2_id]
        
        return self._check_hybrid_compatibility(var1_id, var2_id)
    
    def _check_legacy_compatibility(self, var1_id: str, var2_id: str) -> Tuple[bool, str]:
        """기존 변수 간 호환성 검증 (레거시 로직)"""
        # 기존 하드코딩된 호환성 규칙 유지
        legacy_compatible = {
            'RSI': ['STOCHASTIC'],
            'SMA': ['EMA', 'CURRENT_PRICE'],
            'EMA': ['SMA', 'CURRENT_PRICE'],
            'CURRENT_PRICE': ['SMA', 'EMA']
        }
        
        if var1_id in legacy_compatible:
            if var2_id in legacy_compatible[var1_id]:
                return True, "기존 호환성 규칙"
        
        return False, "기존 규칙에서 비호환"
    
    def _get_variable_category(self, var_id: str) -> str:
        """변수의 카테고리 반환"""
        for category, variables in self.category_mapping.items():
            if var_id in variables:
                return category
        return 'unknown'


if __name__ == "__main__":
    print("🔧 통합 변수 관리자 테스트")
    print("=" * 50)
    
    # 통합 관리자 생성
    manager = IntegratedVariableManager()
    
    # 통합된 변수 목록 확인
    category_vars = manager.get_category_variables()
    print("📊 통합된 카테고리별 변수:")
    for category, variables in category_vars.items():
        print(f"\n[{category}]")
        for var_id, var_name in variables:
            print(f"  {var_id}: {var_name}")
    
    # 호환성 검증 테스트
    validator = HybridCompatibilityValidator()
    
    test_cases = [
        ('SMA', 'EMA'),           # 기존 + 기존
        ('SMA', 'RSI'),           # 기존 비호환
        ('SMA', 'PRICE_MOMENTUM'), # 기존 + 새지표
        ('RSI', 'CUSTOM_RSI_SMA'), # 기존 + 새지표 (같은계열)
    ]
    
    print(f"\n🧪 호환성 검증 테스트:")
    for var1, var2 in test_cases:
        is_compatible, reason = validator.is_compatible(var1, var2)
        status = "✅" if is_compatible else "❌"
        print(f"  {status} {var1} ↔ {var2}: {reason}")
    
    print(f"\n🎉 통합 시스템 준비 완료!")
