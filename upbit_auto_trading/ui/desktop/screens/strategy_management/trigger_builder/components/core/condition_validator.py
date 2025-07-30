#!/usr/bin/env python3
"""
조건 검증기 (ConditionValidator) - 데이터 유효성 및 비즈니스 룰 검증
=======================================================================

역할: 조건 생성 시 입력 데이터의 형식과 범위 유효성 검사
- 필수 필드 검사 (name, variable_id, operator)
- 조건 이름 유효성 (길이, 특수문자 제한)
- 비교값 범위 검사 (RSI: 0-100, 가격: > 0)
- 파라미터 유효성 (MACD 빠른선 < 느린선)
- 연산자 적합성 (거래량에 "!=" 권장 안함)

호환성 검증기(CompatibilityValidator)와의 차이점:
- CompatibilityValidator: 변수 간 의미론적 호환성 (RSI ↔ MACD 비교 무의미)
- ConditionValidator: 단일 조건의 데이터 품질 보장 (RSI 값 0-100 범위)

검증 시점: 조건 저장 직전 최종 데이터 검증 단계
"""

from typing import Dict, Any, Tuple, Optional
import re


class ConditionValidator:
    """조건 생성 시 유효성 검사를 담당하는 클래스"""
    
    @staticmethod
    def validate_condition_data(condition_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """조건 데이터 전체 유효성 검사"""
        try:
            # 필수 필드 검사
            required_fields = ['name', 'variable_id', 'operator']
            for field in required_fields:
                if not condition_data.get(field):
                    return False, f"필수 필드 '{field}'가 누락되었습니다."
            
            # 조건 이름 검사
            name_valid, name_msg = ConditionValidator.validate_condition_name(
                condition_data['name']
            )
            if not name_valid:
                return False, name_msg
            
            # 비교값 검사
            comparison_type = condition_data.get('comparison_type', 'fixed')
            if comparison_type == 'fixed':
                target_valid, target_msg = ConditionValidator.validate_target_value(
                    condition_data.get('target_value', ''),
                    condition_data.get('variable_id', '')
                )
                if not target_valid:
                    return False, target_msg
            elif comparison_type == 'external':
                if not condition_data.get('external_variable'):
                    return False, "외부 변수 정보가 누락되었습니다."
            
            # 파라미터 검사
            param_valid, param_msg = ConditionValidator.validate_parameters(
                condition_data.get('variable_params', {}),
                condition_data.get('variable_id', '')
            )
            if not param_valid:
                return False, param_msg
            
            return True, None
            
        except Exception as e:
            return False, f"검증 중 오류 발생: {str(e)}"
    
    @staticmethod
    def validate_condition_name(name: str) -> Tuple[bool, Optional[str]]:
        """조건 이름 유효성 검사"""
        if not name or not name.strip():
            return False, "조건 이름을 입력해주세요."
        
        if len(name.strip()) < 2:
            return False, "조건 이름은 2글자 이상이어야 합니다."
        
        if len(name.strip()) > 50:
            return False, "조건 이름은 50글자 이하여야 합니다."
        
        # 특수문자 검사 (일부 허용)
        if re.search(r'[<>"|\\]', name):
            return False, "조건 이름에는 <, >, \", |, \\ 문자를 사용할 수 없습니다."
        
        return True, None
    
    @staticmethod
    def validate_target_value(target_value: str, variable_id: str) -> Tuple[bool, Optional[str]]:
        """비교값 유효성 검사"""
        if not target_value or not target_value.strip():
            return False, "비교값을 입력해주세요."
        
        # 숫자 검사
        try:
            value = float(target_value.strip())
            
            # 변수별 범위 검사
            if variable_id == "RSI":
                if not (0 <= value <= 100):
                    return False, "RSI 값은 0~100 범위여야 합니다."
            elif variable_id == "PROFIT_PERCENT":
                if not (-100 <= value <= 1000):
                    return False, "수익률은 -100%~1000% 범위여야 합니다."
            elif variable_id in ["CURRENT_PRICE", "OPEN_PRICE", "HIGH_PRICE", "LOW_PRICE"]:
                if value <= 0:
                    return False, "가격은 0보다 큰 값이어야 합니다."
            elif variable_id == "VOLUME":
                if value < 0:
                    return False, "거래량은 0 이상이어야 합니다."
            
        except ValueError:
            return False, "비교값은 숫자여야 합니다."
        
        return True, None
    
    @staticmethod
    def validate_parameters(parameters: Dict[str, Any], variable_id: str) -> Tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # 변수별 필수 파라미터 정의
        required_params = {
            "RSI": ["period"],
            "SMA": ["period"],
            "EMA": ["period"],
            "BOLLINGER_BAND": ["period", "std_dev", "band_position"],
            "MACD": ["fast_period", "slow_period", "signal_period", "macd_type"]
        }
        
        # 해당 변수의 필수 파라미터 검사
        if variable_id in required_params:
            for param in required_params[variable_id]:
                if param not in parameters or parameters[param] is None:
                    return False, f"필수 파라미터 '{param}'이 누락되었습니다."
        
        # 파라미터별 상세 검사
        if variable_id == "RSI":
            period = parameters.get("period")
            if isinstance(period, int) and not (2 <= period <= 50):
                return False, "RSI 기간은 2~50 범위여야 합니다."
        
        elif variable_id in ["SMA", "EMA"]:
            period = parameters.get("period")
            if isinstance(period, int) and not (1 <= period <= 240):
                return False, "이동평균 기간은 1~240 범위여야 합니다."
        
        elif variable_id == "BOLLINGER_BAND":
            period = parameters.get("period")
            std_dev = parameters.get("std_dev")
            
            if isinstance(period, int) and not (10 <= period <= 50):
                return False, "볼린저밴드 기간은 10~50 범위여야 합니다."
            
            try:
                if std_dev and not (0.5 <= float(std_dev) <= 3.0):
                    return False, "표준편차는 0.5~3.0 범위여야 합니다."
            except (ValueError, TypeError):
                return False, "표준편차는 숫자여야 합니다."
        
        elif variable_id == "MACD":
            fast_period = parameters.get("fast_period")
            slow_period = parameters.get("slow_period")
            signal_period = parameters.get("signal_period")
            
            if isinstance(fast_period, int) and isinstance(slow_period, int):
                if fast_period >= slow_period:
                    return False, "빠른선 기간이 느린선 기간보다 작아야 합니다."
            
            if isinstance(signal_period, int) and not (5 <= signal_period <= 20):
                return False, "시그널선 기간은 5~20 범위여야 합니다."
        
        return True, None
    
    @staticmethod
    def validate_operator_compatibility(variable_id: str, operator: str) -> Tuple[bool, Optional[str]]:
        """변수와 연산자 호환성 검사"""
        # 연산자별 호환성 체크
        if operator == "~=" and variable_id in ["RSI", "PROFIT_PERCENT"]:
            # 근사값 비교는 연속값에만 적용
            return True, None
        elif operator == "!=" and variable_id in ["VOLUME", "POSITION_SIZE"]:
            # 거래량이나 포지션 크기의 "다름" 연산자는 의미가 제한적
            return False, f"{variable_id}에는 '!=' 연산자가 권장되지 않습니다."
        
        return True, None
    
    @staticmethod
    def get_validation_suggestions(variable_id: str) -> Dict[str, str]:
        """변수별 검증 가이드라인 반환"""
        suggestions = {
            "RSI": {
                "target_range": "0~100 (과매도: 30 이하, 과매수: 70 이상)",
                "common_values": "30, 50, 70",
                "operators": "> (돌파), < (이탈), >= (도달), <= (하락)"
            },
            "SMA": {
                "target_range": "현재가 기준 또는 다른 SMA와 비교",
                "common_values": "현재가 * 1.02 (2% 위), 현재가 * 0.98 (2% 아래)",
                "operators": "> (상향돌파), < (하향이탈)"
            },
            "PROFIT_PERCENT": {
                "target_range": "-100~1000% (손절: -5%, 익절: 5~20%)",
                "common_values": "-3, -5, 3, 5, 10, 20",
                "operators": ">= (목표 달성), <= (손실 제한)"
            },
            "CURRENT_PRICE": {
                "target_range": "양수 (목표가격)",
                "common_values": "50000, 100000 (원화 기준)",
                "operators": ">= (도달), <= (하락)"
            }
        }
        
        return suggestions.get(variable_id, {
            "target_range": "변수에 적합한 범위 확인 필요",
            "common_values": "일반적인 값 없음",
            "operators": "모든 연산자 사용 가능"
        })
