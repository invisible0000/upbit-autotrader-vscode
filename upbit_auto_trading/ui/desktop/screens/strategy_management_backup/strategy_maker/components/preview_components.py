#!/usr/bin/env python3
"""
미리보기 생성기 - 조건 미리보기 텍스트 생성
"""

from typing import Dict, Any, Optional

class PreviewGenerator:
    """조건 미리보기 텍스트를 생성하는 클래스"""
    
    @staticmethod
    def generate_condition_preview(condition_data: Dict[str, Any]) -> str:
        """조건 데이터로부터 미리보기 텍스트 생성"""
        try:
            var_text = condition_data.get('variable_name', '[변수]')
            operator = condition_data.get('operator', '>')
            condition_name = condition_data.get('name', 'Unknown Condition')
            comparison_type = condition_data.get('comparison_type', 'fixed')
            
            # 비교 대상 설정
            if comparison_type == 'external':
                external_var = condition_data.get('external_variable', {})
                target = external_var.get('variable_name', '[외부변수]')
                target_type = "🔗 외부변수"
            else:
                target = condition_data.get('target_value', '[값]')
                target_type = "💰 고정값"
            
            # 파라미터 정보
            param_text = PreviewGenerator._generate_parameter_text(
                condition_data.get('variable_id', ''),
                condition_data.get('variable_params', {})
            )
            
            # 추세 정보
            trend_text = PreviewGenerator._generate_trend_text(
                condition_data.get('trend_direction', 'static')
            )
            
            # 연산자 설명
            operator_desc = PreviewGenerator._get_operator_description(operator)
            
            preview_text = f"""
🎯 조건명: {condition_name}

📊 조건식: {var_text}{param_text} {operator} {target}{trend_text}

🔍 비교 유형: {target_type}

⚖️ 연산자: {operator_desc}

📝 해석: "{var_text}"이(가) "{target}"보다 {operator_desc}일 때 신호 발생
            """.strip()
            
            return preview_text
            
        except Exception as e:
            return f"미리보기 생성 중 오류: {str(e)}"
    
    @staticmethod
    def _generate_parameter_text(var_id: str, params: Dict[str, Any]) -> str:
        """파라미터 텍스트 생성"""
        if not params:
            return ""
        
        param_list = []
        for param_name, value in params.items():
            if value is not None and str(value).strip():
                param_list.append(f"{param_name}={value}")
        
        if param_list:
            return f" ({', '.join(param_list)})"
        return ""
    
    @staticmethod
    def _generate_trend_text(trend_direction: str) -> str:
        """추세 방향성 텍스트 생성"""
        trend_mapping = {
            "static": "",
            "rising": " [상승중]",
            "falling": " [하락중]",
            "both": " [양방향]"
        }
        return trend_mapping.get(trend_direction, "")
    
    @staticmethod
    def _get_operator_description(operator: str) -> str:
        """연산자 설명 반환"""
        descriptions = {
            ">": "초과 (크다)",
            ">=": "이상 (크거나 같다)",
            "<": "미만 (작다)",
            "<=": "이하 (작거나 같다)",
            "~=": "근사값 (±1% 범위)",
            "!=": "다름"
        }
        return descriptions.get(operator, operator)
    
    @staticmethod
    def generate_detailed_preview(condition_data: Dict[str, Any]) -> str:
        """상세 미리보기 생성 (기술적 분석 포함)"""
        basic_preview = PreviewGenerator.generate_condition_preview(condition_data)
        
        var_id = condition_data.get('variable_id', '')
        target_value = condition_data.get('target_value', '')
        operator = condition_data.get('operator', '')
        
        # 기술적 분석 가이드
        technical_guide = PreviewGenerator._get_technical_analysis_guide(
            var_id, target_value, operator
        )
        
        if technical_guide:
            detailed_preview = f"""
{basic_preview}

📈 기술적 분석:
{technical_guide}
            """.strip()
            return detailed_preview
        
        return basic_preview
    
    @staticmethod
    def _get_technical_analysis_guide(var_id: str, target_value: str, operator: str) -> str:
        """변수별 기술적 분석 가이드 생성"""
        guides = {
            "RSI": PreviewGenerator._get_rsi_guide(target_value, operator),
            "SMA": PreviewGenerator._get_sma_guide(target_value, operator),
            "EMA": PreviewGenerator._get_ema_guide(target_value, operator),
            "BOLLINGER_BAND": PreviewGenerator._get_bollinger_guide(target_value, operator),
            "MACD": PreviewGenerator._get_macd_guide(target_value, operator),
            "PROFIT_PERCENT": PreviewGenerator._get_profit_guide(target_value, operator)
        }
        
        return guides.get(var_id, "")
    
    @staticmethod
    def _get_rsi_guide(target_value: str, operator: str) -> str:
        """RSI 기술적 분석 가이드"""
        try:
            value = float(target_value) if target_value else 0
            
            if operator in [">", ">="]:
                if value >= 70:
                    return f"• RSI {value} 돌파 → 과매수 구간 진입\n• 단기 조정 가능성 증가\n• 추세 강도 확인 후 매도 검토"
                elif value >= 50:
                    return f"• RSI {value} 돌파 → 상승 모멘텀 강화\n• 중립선 상향 돌파로 매수 신호\n• 지속적인 상승 추세 기대"
                else:
                    return f"• RSI {value} 돌파 → 과매도 탈출\n• 바닥권 반등 신호\n• 점진적 매수 타이밍"
            
            elif operator in ["<", "<="]:
                if value <= 30:
                    return f"• RSI {value} 이탈 → 과매도 구간 진입\n• 반등 가능성 증가\n• 분할 매수 전략 고려"
                elif value <= 50:
                    return f"• RSI {value} 이탈 → 하락 모멘텀 확인\n• 중립선 하향 이탈로 매도 신호\n• 추가 하락 가능성"
                else:
                    return f"• RSI {value} 이탈 → 상승 모멘텀 약화\n• 고점 대비 조정 시작\n• 이익 실현 검토"
            
        except ValueError:
            pass
        
        return "• RSI 기반 모멘텀 분석 조건"
    
    @staticmethod
    def _get_sma_guide(target_value: str, operator: str) -> str:
        """SMA 기술적 분석 가이드"""
        if operator in [">", ">="]:
            return "• 가격이 이동평균선 상향 돌파\n• 상승 추세 전환 신호\n• 추세 지속성 확인 후 매수"
        elif operator in ["<", "<="]:
            return "• 가격이 이동평균선 하향 이탈\n• 하락 추세 전환 신호\n• 지지선 붕괴로 매도 검토"
        
        return "• 이동평균 기반 추세 분석"
    
    @staticmethod
    def _get_ema_guide(target_value: str, operator: str) -> str:
        """EMA 기술적 분석 가이드"""
        if operator in [">", ">="]:
            return "• 지수이동평균 상향 돌파\n• 빠른 추세 전환 감지\n• 단기 상승 모멘텀 확인"
        elif operator in ["<", "<="]:
            return "• 지수이동평균 하향 이탈\n• 빠른 하락 신호\n• 조기 손절 검토"
        
        return "• 지수이동평균 기반 빠른 신호"
    
    @staticmethod
    def _get_bollinger_guide(target_value: str, operator: str) -> str:
        """볼린저밴드 기술적 분석 가이드"""
        if operator in [">", ">="]:
            return "• 볼린저밴드 상단 돌파\n• 강한 상승 모멘텀 확인\n• 변동성 확대 구간"
        elif operator in ["<", "<="]:
            return "• 볼린저밴드 하단 이탈\n• 강한 하락 압력\n• 변동성 확대로 추가 하락 가능"
        
        return "• 볼린저밴드 기반 변동성 분석"
    
    @staticmethod
    def _get_macd_guide(target_value: str, operator: str) -> str:
        """MACD 기술적 분석 가이드"""
        try:
            value = float(target_value) if target_value else 0
            
            if value == 0:
                if operator in [">", ">="]:
                    return "• MACD 제로선 상향 돌파\n• 상승 추세 전환 확인\n• 중장기 매수 신호"
                else:
                    return "• MACD 제로선 하향 이탈\n• 하락 추세 전환 확인\n• 중장기 매도 신호"
            else:
                return "• MACD 시그널선 교차 분석\n• 단기 모멘텀 변화 감지\n• 추세 강도 확인"
                
        except ValueError:
            pass
        
        return "• MACD 기반 추세 분석"
    
    @staticmethod
    def _get_profit_guide(target_value: str, operator: str) -> str:
        """수익률 분석 가이드"""
        try:
            value = float(target_value) if target_value else 0
            
            if operator in [">", ">="]:
                if value > 0:
                    return f"• 목표 수익률 {value}% 달성\n• 이익 실현 타이밍\n• 부분 매도 또는 전량 매도 검토"
                else:
                    return f"• 손실률 {abs(value)}% 회복\n• 손실 축소 확인\n• 추가 회복 여력 판단"
            elif operator in ["<", "<="]:
                if value < 0:
                    return f"• 손절선 {abs(value)}% 도달\n• 손실 확대 방지\n• 즉시 청산 검토"
                else:
                    return f"• 수익률 {value}% 하회\n• 수익 축소 확인\n• 부분 매도 검토"
                    
        except ValueError:
            pass
        
        return "• 수익률 기반 리스크 관리"
    
    @staticmethod
    def generate_json_preview(condition_data: Dict[str, Any]) -> str:
        """JSON 형태의 조건 데이터 미리보기"""
        import json
        
        # 민감한 정보 제외하고 정리된 데이터 생성
        clean_data = {
            "condition_name": condition_data.get('name', ''),
            "variable": {
                "id": condition_data.get('variable_id', ''),
                "name": condition_data.get('variable_name', ''),
                "parameters": condition_data.get('variable_params', {})
            },
            "comparison": {
                "operator": condition_data.get('operator', ''),
                "type": condition_data.get('comparison_type', 'fixed'),
                "target_value": condition_data.get('target_value'),
                "external_variable": condition_data.get('external_variable')
            },
            "trend_direction": condition_data.get('trend_direction', 'static'),
            "description": condition_data.get('description', '')
        }
        
        try:
            return json.dumps(clean_data, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"JSON 미리보기 생성 오류: {str(e)}"
