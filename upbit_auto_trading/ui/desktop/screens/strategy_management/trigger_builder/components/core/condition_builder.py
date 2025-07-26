#!/usr/bin/env python3
"""
조건 빌더 - 조건 생성 로직 및 실행 코드 생성
"""

from typing import Dict, Any, Optional, List
from .variable_definitions import VariableDefinitions
from .condition_validator import ConditionValidator

class ConditionBuilder:
    """조건 생성 및 실행 코드 빌더"""
    
    def __init__(self):
        self.variable_definitions = VariableDefinitions()
        self.validator = ConditionValidator()
    
    def build_condition_from_ui(self, ui_data: Dict[str, Any]) -> Dict[str, Any]:
        """UI 데이터로부터 완전한 조건 객체 생성"""
        condition = {
            "name": ui_data.get("name", "").strip(),
            "description": ui_data.get("description", "").strip(),
            "variable_id": ui_data.get("variable_id", ""),
            "variable_name": ui_data.get("variable_name", ""),
            "variable_params": ui_data.get("variable_params", {}),
            "operator": ui_data.get("operator", ">"),
            "comparison_type": ui_data.get("comparison_type", "fixed"),
            "target_value": ui_data.get("target_value", ""),
            "external_variable": ui_data.get("external_variable"),
            "trend_direction": ui_data.get("trend_direction", "static"),
            "category": ui_data.get("category", "custom")
        }
        
        # 자동 이름 생성 (필요시)
        if not condition["name"]:
            condition["name"] = self._generate_auto_name(condition)
        
        return condition
    
    def generate_execution_code(self, condition: Dict[str, Any], 
                              language: str = "python") -> str:
        """조건 실행 코드 생성"""
        if language == "python":
            return self._generate_python_code(condition)
        elif language == "pine_script":
            return self._generate_pine_script_code(condition)
        else:
            raise ValueError(f"지원하지 않는 언어: {language}")
    
    def _generate_python_code(self, condition: Dict[str, Any]) -> str:
        """Python 실행 코드 생성"""
        var_id = condition["variable_id"]
        params = condition["variable_params"]
        operator = condition["operator"]
        comparison_type = condition["comparison_type"]
        target_value = condition["target_value"]
        external_variable = condition["external_variable"]
        
        code_lines = []
        code_lines.append(f"# 조건: {condition['name']}")
        code_lines.append(f"# 설명: {condition['description']}")
        code_lines.append("")
        
        # 변수 계산 코드
        variable_code = self._generate_variable_calculation_code(var_id, params)
        code_lines.extend(variable_code)
        
        # 비교 코드
        if comparison_type == "fixed":
            comparison_code = f"condition_result = {var_id.lower()}_value {operator} {target_value}"
        else:
            # 외부 변수 계산
            ext_var_id = external_variable["variable_id"]
            ext_params = external_variable.get("parameters", {})
            
            ext_variable_code = self._generate_variable_calculation_code(
                ext_var_id, ext_params, suffix="_external"
            )
            code_lines.extend(ext_variable_code)
            
            comparison_code = f"condition_result = {var_id.lower()}_value {operator} {ext_var_id.lower()}_external_value"
        
        code_lines.append("")
        code_lines.append("# 조건 평가")
        code_lines.append(comparison_code)
        
        # 추세 방향성 코드
        if condition["trend_direction"] != "static":
            trend_code = self._generate_trend_analysis_code(
                var_id, condition["trend_direction"]
            )
            code_lines.extend(trend_code)
            code_lines.append("condition_result = condition_result and trend_condition")
        
        code_lines.append("")
        code_lines.append("# 결과 반환")
        code_lines.append("return condition_result")
        
        return "\n".join(code_lines)
    
    def _generate_variable_calculation_code(self, var_id: str, params: Dict[str, Any], 
                                          suffix: str = "") -> List[str]:
        """변수별 계산 코드 생성"""
        code_lines = []
        var_name = f"{var_id.lower()}{suffix}_value"
        
        if var_id == "RSI":
            period = params.get("period", 14)
            timeframe = params.get("timeframe", "포지션 설정 따름")
            
            code_lines.append(f"# RSI 계산")
            code_lines.append(f"rsi_period = {period}")
            code_lines.append(f"timeframe = '{timeframe}'")
            code_lines.append(f"{var_name} = calculate_rsi(market_data, rsi_period, timeframe)")
            
        elif var_id == "SMA":
            period = params.get("period", 20)
            timeframe = params.get("timeframe", "포지션 설정 따름")
            
            code_lines.append(f"# SMA 계산")
            code_lines.append(f"sma_period = {period}")
            code_lines.append(f"timeframe = '{timeframe}'")
            code_lines.append(f"{var_name} = calculate_sma(market_data, sma_period, timeframe)")
            
        elif var_id == "EMA":
            period = params.get("period", 12)
            exp_factor = params.get("exponential_factor", 2.0)
            timeframe = params.get("timeframe", "포지션 설정 따름")
            
            code_lines.append(f"# EMA 계산")
            code_lines.append(f"ema_period = {period}")
            code_lines.append(f"exp_factor = {exp_factor}")
            code_lines.append(f"timeframe = '{timeframe}'")
            code_lines.append(f"{var_name} = calculate_ema(market_data, ema_period, exp_factor, timeframe)")
            
        elif var_id == "BOLLINGER_BAND":
            period = params.get("period", 20)
            std_dev = params.get("std_dev", 2.0)
            band_position = params.get("band_position", "상단")
            timeframe = params.get("timeframe", "포지션 설정 따름")
            
            code_lines.append(f"# 볼린저밴드 계산")
            code_lines.append(f"bb_period = {period}")
            code_lines.append(f"std_dev = {std_dev}")
            code_lines.append(f"band_position = '{band_position}'")
            code_lines.append(f"timeframe = '{timeframe}'")
            code_lines.append(f"{var_name} = calculate_bollinger_band(market_data, bb_period, std_dev, band_position, timeframe)")
            
        elif var_id == "MACD":
            fast_period = params.get("fast_period", 12)
            slow_period = params.get("slow_period", 26)
            signal_period = params.get("signal_period", 9)
            macd_type = params.get("macd_type", "MACD선")
            
            code_lines.append(f"# MACD 계산")
            code_lines.append(f"fast_period = {fast_period}")
            code_lines.append(f"slow_period = {slow_period}")
            code_lines.append(f"signal_period = {signal_period}")
            code_lines.append(f"macd_type = '{macd_type}'")
            code_lines.append(f"{var_name} = calculate_macd(market_data, fast_period, slow_period, signal_period, macd_type)")
            
        elif var_id == "CURRENT_PRICE":
            price_type = params.get("price_type", "현재가")
            
            code_lines.append(f"# 현재가 조회")
            code_lines.append(f"price_type = '{price_type}'")
            code_lines.append(f"{var_name} = get_current_price(market_data, price_type)")
            
        elif var_id == "PROFIT_PERCENT":
            calculation_method = params.get("calculation_method", "미실현")
            scope = params.get("scope", "현재포지션")
            include_fees = params.get("include_fees", "포함")
            
            code_lines.append(f"# 수익률 계산")
            code_lines.append(f"calculation_method = '{calculation_method}'")
            code_lines.append(f"scope = '{scope}'")
            code_lines.append(f"include_fees = '{include_fees}'")
            code_lines.append(f"{var_name} = calculate_profit_percent(position_data, calculation_method, scope, include_fees)")
            
        else:
            # 기본 변수들
            code_lines.append(f"# {var_id} 조회")
            code_lines.append(f"{var_name} = get_variable_value('{var_id}', {params})")
        
        code_lines.append("")
        return code_lines
    
    def _generate_trend_analysis_code(self, var_id: str, trend_direction: str) -> List[str]:
        """추세 분석 코드 생성"""
        code_lines = []
        code_lines.append("")
        code_lines.append("# 추세 방향성 분석")
        
        if trend_direction == "rising":
            code_lines.append(f"trend_condition = is_rising({var_id.lower()}_value, lookback_period=3)")
        elif trend_direction == "falling":
            code_lines.append(f"trend_condition = is_falling({var_id.lower()}_value, lookback_period=3)")
        elif trend_direction == "both":
            code_lines.append(f"trend_condition = has_volatility({var_id.lower()}_value, min_change_rate=0.01)")
        else:
            code_lines.append("trend_condition = True  # 정적 비교")
        
        return code_lines
    
    def _generate_pine_script_code(self, condition: Dict[str, Any]) -> str:
        """Pine Script 코드 생성 (TradingView용)"""
        var_id = condition["variable_id"]
        params = condition["variable_params"]
        operator = condition["operator"]
        target_value = condition["target_value"]
        
        code_lines = []
        code_lines.append("//@version=5")
        code_lines.append(f"// 조건: {condition['name']}")
        code_lines.append(f"// 설명: {condition['description']}")
        code_lines.append("")
        
        # Pine Script 변수 계산
        if var_id == "RSI":
            period = params.get("period", 14)
            code_lines.append(f"rsi_value = ta.rsi(close, {period})")
            
        elif var_id == "SMA":
            period = params.get("period", 20)
            code_lines.append(f"sma_value = ta.sma(close, {period})")
            
        elif var_id == "EMA":
            period = params.get("period", 12)
            code_lines.append(f"ema_value = ta.ema(close, {period})")
            
        elif var_id == "BOLLINGER_BAND":
            period = params.get("period", 20)
            std_dev = params.get("std_dev", 2.0)
            band_position = params.get("band_position", "상단")
            
            code_lines.append(f"[bb_middle, bb_upper, bb_lower] = ta.bb(close, {period}, {std_dev})")
            
            if band_position == "상단":
                code_lines.append("bb_value = bb_upper")
            elif band_position == "하단":
                code_lines.append("bb_value = bb_lower")
            else:
                code_lines.append("bb_value = bb_middle")
        
        # 조건 평가
        pine_operator = self._convert_operator_to_pine(operator)
        code_lines.append("")
        code_lines.append(f"condition_result = {var_id.lower()}_value {pine_operator} {target_value}")
        
        return "\n".join(code_lines)
    
    def _convert_operator_to_pine(self, operator: str) -> str:
        """Python 연산자를 Pine Script 연산자로 변환"""
        conversions = {
            ">": ">",
            ">=": ">=",
            "<": "<",
            "<=": "<=",
            "~=": "==",  # 근사값은 동등 비교로
            "!=": "!="
        }
        return conversions.get(operator, operator)
    
    def _generate_auto_name(self, condition: Dict[str, Any]) -> str:
        """자동 조건명 생성"""
        var_name = condition.get("variable_name", "변수")
        operator = condition.get("operator", ">")
        target = condition.get("target_value", "값")
        
        operator_names = {
            ">": "초과",
            ">=": "이상",
            "<": "미만",
            "<=": "이하",
            "~=": "근사",
            "!=": "다름"
        }
        
        operator_name = operator_names.get(operator, operator)
        
        if condition.get("comparison_type") == "external":
            external_var = condition.get("external_variable", {})
            target = external_var.get("variable_name", "외부변수")
            return f"{var_name} {operator_name} {target}"
        else:
            return f"{var_name} {operator_name} {target}"
    
    def build_condition_template(self, variable_id: str) -> Dict[str, Any]:
        """변수별 조건 템플릿 생성"""
        variable_params = self.variable_definitions.get_variable_parameters(variable_id)
        category_variables = self.variable_definitions.get_category_variables()
        
        # 변수가 속한 카테고리 찾기
        category = "custom"
        for cat, variables in category_variables.items():
            if any(var[0] == variable_id for var in variables):
                category = cat
                break
        
        # 변수명 찾기
        variable_name = variable_id
        for cat, variables in category_variables.items():
            for var_id, var_name in variables:
                if var_id == variable_id:
                    variable_name = var_name
                    break
        
        # 기본 파라미터 값 설정
        default_params = {}
        for param_name, param_config in variable_params.items():
            default_params[param_name] = param_config.get("default")
        
        template = {
            "name": "",
            "description": "",
            "variable_id": variable_id,
            "variable_name": variable_name,
            "variable_params": default_params,
            "operator": ">",
            "comparison_type": "fixed",
            "target_value": "",
            "external_variable": None,
            "trend_direction": "static",
            "category": category
        }
        
        return template
    
    def validate_and_build(self, ui_data: Dict[str, Any]) -> tuple[bool, str, Optional[Dict[str, Any]]]:
        """UI 데이터 검증 후 조건 빌드"""
        condition = self.build_condition_from_ui(ui_data)
        
        # 유효성 검사
        is_valid, error_message = self.validator.validate_condition_data(condition)
        
        if not is_valid:
            return False, error_message or "알 수 없는 검증 오류", None
        
        return True, "조건이 성공적으로 생성되었습니다.", condition
