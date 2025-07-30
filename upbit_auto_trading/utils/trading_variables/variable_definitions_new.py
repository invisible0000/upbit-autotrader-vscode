#!/usr/bin/env python3
"""
변수 정의 모듈 (VariableDefinitions) - DB 동기화 자동 생성
==================================================

⚠️  **이 파일은 자동 생성됩니다. 직접 편집하지 마세요!**
📝 **편집하려면**: data/app_settings.sqlite3의 tv_trading_variables 테이블을 수정 후 sync_db_to_code.py 실행

🔄 **마지막 동기화**: 2025-07-29 19:33:29
📊 **총 지표 수**: 30개

🎯 **새로운 지표 추가 워크플로우**:
1. tv_trading_variables 테이블에 지표 추가
2. tv_variable_parameters 테이블에 파라미터 추가
3. python sync_db_to_code.py 실행하여 이 파일 자동 생성
"""

from typing import Dict, Any

# 호환성 검증기 import (shared 폴더)
try:
    from ..shared.compatibility_validator import CompatibilityValidator
    COMPATIBILITY_VALIDATOR_AVAILABLE = True
    print("✅ 통합 호환성 검증기 로드 성공 (trigger_builder/components)")
except ImportError as e:
    print(f"⚠️ 통합 호환성 검증기 로드 실패: {e}")
    COMPATIBILITY_VALIDATOR_AVAILABLE = False


class VariableDefinitions:
    """트레이딩 변수들의 파라미터 정의를 관리하는 클래스 (DB 동기화)"""
    
    # 📊 차트 카테고리 매핑 (DB 동기화)
    CHART_CATEGORIES = {
        "ADX": "subplot",
        "AROON": "subplot",
        "ATR": "subplot",
        "BOLLINGER_BANDS": "overlay",
        "BOLLINGER_WIDTH": "subplot",
        "CCI": "subplot",
        "CURRENT_PRICE": "overlay",
        "EMA": "overlay",
        "HIGH_PRICE": "overlay",
        "ICHIMOKU": "overlay",
        "LOW_PRICE": "overlay",
        "MACD": "subplot",
        "MFI": "subplot",
        "OBV": "subplot",
        "OPEN_PRICE": "overlay",
        "PARABOLIC_SAR": "overlay",
        "PIVOT_POINTS": "overlay",
        "ROC": "subplot",
        "RSI": "subplot",
        "SMA": "overlay",
        "SQUEEZE_MOMENTUM": "subplot",
        "STANDARD_DEVIATION": "subplot",
        "STOCH": "subplot",
        "STOCH_RSI": "subplot",
        "SUPERTREND": "overlay",
        "VOLUME": "subplot",
        "VOLUME_PROFILE": "overlay",
        "VWAP": "overlay",
        "WILLIAMS_R": "subplot",
        "WMA": "overlay",
    }
    @staticmethod
    def get_variable_parameters(var_id: str) -> Dict[str, Any]:
        """변수별 파라미터 정의 반환 (DB 동기화)"""
        params = {
            "ADX": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "default": 14,
                    "help": "ADX 계산 기간",
                    "min": 1,
                    "max": 100,
                },
            },
            "ATR": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "default": 14,
                    "help": "ATR 계산 기간",
                    "min": 1,
                    "max": 100,
                },
            },
            "BOLLINGER_BANDS": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "default": 20,
                    "help": "이동평균 기간",
                    "min": 2,
                    "max": 100,
                },
                "multiplier": {
                    "label": "표준편차 배수",
                    "type": "float",
                    "default": 2.0,
                    "help": "표준편차 곱셈 계수",
                    "min": 0.1,
                    "max": 5.0,
                },
                "source": {
                    "label": "데이터 소스",
                    "type": "enum",
                    "default": "close",
                    "help": "계산에 사용할 가격 데이터",
                    "options": ['open', 'high', 'low', 'close', 'hl2', 'hlc3', 'ohlc4'],
                },
            },
            "CCI": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "default": 20,
                    "help": "CCI 계산 기간",
                    "min": 1,
                    "max": 100,
                },
                "factor": {
                    "label": "상수",
                    "type": "float",
                    "default": 0.015,
                    "help": "CCI 계산 상수",
                    "min": 0.001,
                    "max": 1.0,
                },
            },
            "EMA": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "default": 20,
                    "help": "지수이동평균 계산 기간",
                    "min": 1,
                    "max": 200,
                },
                "source": {
                    "label": "데이터 소스",
                    "type": "enum",
                    "default": "close",
                    "help": "계산에 사용할 가격 데이터",
                    "options": ['open', 'high', 'low', 'close', 'hl2', 'hlc3', 'ohlc4'],
                },
            },
            "MACD": {
                "fast_period": {
                    "label": "빠른 기간",
                    "type": "int",
                    "default": 12,
                    "help": "빠른 EMA 기간",
                    "min": 1,
                    "max": 50,
                },
                "slow_period": {
                    "label": "느린 기간",
                    "type": "int",
                    "default": 26,
                    "help": "느린 EMA 기간",
                    "min": 1,
                    "max": 100,
                },
                "signal_period": {
                    "label": "시그널 기간",
                    "type": "int",
                    "default": 9,
                    "help": "시그널 라인 기간",
                    "min": 1,
                    "max": 50,
                },
            },
            "RSI": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "default": 14,
                    "help": "RSI 계산 기간",
                    "min": 2,
                    "max": 100,
                },
                "source": {
                    "label": "데이터 소스",
                    "type": "enum",
                    "default": "close",
                    "help": "계산에 사용할 가격 데이터",
                    "options": ['open', 'high', 'low', 'close', 'hl2', 'hlc3', 'ohlc4'],
                },
            },
            "SMA": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "default": 20,
                    "help": "이동평균 계산 기간",
                    "min": 1,
                    "max": 200,
                },
                "source": {
                    "label": "데이터 소스",
                    "type": "enum",
                    "default": "close",
                    "help": "계산에 사용할 가격 데이터",
                    "options": ['open', 'high', 'low', 'close', 'hl2', 'hlc3', 'ohlc4'],
                },
            },
            "STOCH": {
                "k_period": {
                    "label": "%K 기간",
                    "type": "int",
                    "default": 14,
                    "help": "%K 라인 계산 기간",
                    "min": 1,
                    "max": 100,
                },
                "d_period": {
                    "label": "%D 기간",
                    "type": "int",
                    "default": 3,
                    "help": "%D 라인 계산 기간",
                    "min": 1,
                    "max": 50,
                },
                "smooth": {
                    "label": "스무딩",
                    "type": "int",
                    "default": 3,
                    "help": "스토캐스틱 스무딩 기간",
                    "min": 1,
                    "max": 10,
                },
            },
        }

        return params.get(var_id, {})
    @staticmethod
    def get_variable_descriptions() -> Dict[str, str]:
        """변수별 설명 반환 (DB 동기화)"""
        return {
            "ADX": "추세의 강도를 측정하는 지표 (방향은 알려주지 않음)",
            "AROON": "최고가/최저가 도달 후 경과 시간으로 추세 시작을 파악",
            "ATR": "주가의 변동성을 측정하는 지표. 절대적인 가격 변동폭을 나타냄",
            "BOLLINGER_BANDS": "이동평균선과 표준편차를 이용한 변동성 채널",
            "BOLLINGER_WIDTH": "볼린저 밴드의 상하단 폭으로 변동성의 축소/확대를 파악",
            "CCI": "현재 가격이 평균 가격과 얼마나 떨어져 있는지를 측정",
            "CURRENT_PRICE": "현재 시점의 가격",
            "EMA": "최근 가격에 더 큰 가중치를 부여한 이동평균",
            "HIGH_PRICE": "특정 기간의 최고가",
            "ICHIMOKU": "전환선, 기준선, 구름대 등을 통한 종합 분석 지표",
            "LOW_PRICE": "특정 기간의 최저가",
            "MACD": "두 이동평균선 사이의 관계를 보여주는 모멘텀 및 추세 지표",
            "MFI": "거래량을 고려한 RSI로, 자금의 유입 및 유출 강도를 나타냄",
            "OBV": "상승일 거래량은 더하고 하락일 거래량은 빼서 거래량 흐름을 표시",
            "OPEN_PRICE": "특정 기간의 시작 가격",
            "PARABOLIC_SAR": "추세의 전환 가능 지점을 점으로 나타내는 추세 추종 지표",
            "PIVOT_POINTS": "전일/전주/전월의 고가, 저가, 종가를 이용해 지지선과 저항선을 계산",
            "ROC": "현재 가격과 n일 전 가격의 변화율을 측정",
            "RSI": "상승압력과 하락압력 간의 상대적 강도를 나타내는 모멘텀 지표",
            "SMA": "특정 기간의 가격을 산술 평균한 값",
            "SQUEEZE_MOMENTUM": "볼린저 밴드와 켈트너 채널을 이용해 변동성 압축 후 폭발 방향을 예측",
            "STANDARD_DEVIATION": "가격이 평균에서 얼마나 떨어져 있는지를 측정하는 통계적 변동성 지표",
            "STOCH": "특정 기간 주가 변동 범위에서 현재 주가의 위치를 백분율로 표시",
            "STOCH_RSI": "RSI 값에 스토캐스틱 공식을 적용하여 더 민감한 신호 생성",
            "SUPERTREND": "ATR을 기반으로 추세의 방향과 변동성을 시각적으로 표시",
            "VOLUME": "특정 기간 동안 거래된 주식의 총 수량",
            "VOLUME_PROFILE": "가격대별 거래량을 히스토그램으로 표시",
            "VWAP": "당일 거래량을 가중치로 부여한 평균 가격",
            "WILLIAMS_R": "스토캐스틱과 유사하게 과매수/과매도 수준을 측정",
            "WMA": "기간 내 가격에 선형적으로 가중치를 부여한 이동평균",
        }
    @staticmethod
    def get_category_variables() -> Dict[str, list]:
        """카테고리별 변수 목록 반환 (DB 동기화)"""
        return {
            "momentum": [
                ("CCI", "상품채널지수"),
                ("MACD", "MACD 지표"),
                ("MFI", "자금흐름지수"),
                ("ROC", "가격변동률"),
                ("RSI", "RSI 지표"),
                ("SQUEEZE_MOMENTUM", "스퀴즈 모멘텀"),
                ("STOCH", "스토캐스틱"),
                ("STOCH_RSI", "스토캐스틱 RSI"),
                ("WILLIAMS_R", "윌리엄스 %R"),
            ],
            "price": [
                ("CURRENT_PRICE", "현재가"),
                ("HIGH_PRICE", "고가"),
                ("LOW_PRICE", "저가"),
                ("OPEN_PRICE", "시가"),
            ],
            "support_resistance": [
                ("PIVOT_POINTS", "피봇 포인트"),
            ],
            "trend": [
                ("ADX", "평균방향성지수"),
                ("AROON", "아룬 지표"),
                ("BOLLINGER_BANDS", "볼린저 밴드"),
                ("EMA", "지수이동평균"),
                ("ICHIMOKU", "일목균형표"),
                ("PARABOLIC_SAR", "파라볼릭 SAR"),
                ("SMA", "단순이동평균"),
                ("SUPERTREND", "슈퍼트렌드"),
                ("WMA", "가중이동평균"),
            ],
            "volatility": [
                ("ATR", "평균실제범위"),
                ("BOLLINGER_WIDTH", "볼린저 밴드 폭"),
                ("STANDARD_DEVIATION", "표준편차"),
            ],
            "volume": [
                ("OBV", "온밸런스 볼륨"),
                ("VOLUME", "거래량"),
                ("VOLUME_PROFILE", "거래량 프로파일"),
                ("VWAP", "거래량가중평균가격"),
            ],
        }

    @classmethod
    def get_chart_category(cls, variable_id: str) -> str:
        """변수 ID의 차트 카테고리 반환 (overlay or subplot)"""
        return cls.CHART_CATEGORIES.get(variable_id, "subplot")
    
    @classmethod
    def is_overlay_indicator(cls, variable_id: str) -> bool:
        """오버레이 지표인지 확인"""
        return cls.get_chart_category(variable_id) == "overlay"
    
    @staticmethod
    def get_variable_category(variable_id: str) -> str:
        """변수 ID로부터 카테고리 찾기"""
        category_variables = VariableDefinitions.get_category_variables()
        
        for category, variables in category_variables.items():
            for var_id, var_name in variables:
                if var_id == variable_id:
                    return category
        
        return "custom"  # 기본값
    
    @staticmethod
    def check_variable_compatibility(var1_id: str, var2_id: str) -> tuple[bool, str]:
        """변수 간 호환성 검증 (통합 호환성 검증기 사용)"""
        try:
            if COMPATIBILITY_VALIDATOR_AVAILABLE:
                validator = CompatibilityValidator()
                is_compatible, score, reason = validator.validate_compatibility(var1_id, var2_id)
                reason_str = str(reason) if isinstance(reason, dict) else reason
                return is_compatible, reason_str
            else:
                # 폴백: 기본 카테고리 기반 검증
                cat1 = VariableDefinitions.get_variable_category(var1_id)
                cat2 = VariableDefinitions.get_variable_category(var2_id)
                
                if cat1 == cat2:
                    return True, f"같은 카테고리: {cat1}"
                else:
                    return False, f"다른 카테고리: {cat1} vs {cat2}"
            
        except Exception as e:
            print(f"⚠️ 호환성 검증 실패, 기본 방식 사용: {e}")
            
            # 폴백: 기본 카테고리 기반 검증
            cat1 = VariableDefinitions.get_variable_category(var1_id)
            cat2 = VariableDefinitions.get_variable_category(var2_id)
            
            if cat1 == cat2:
                return True, f"같은 카테고리: {cat1}"
            else:
                return False, f"다른 카테고리: {cat1} vs {cat2}"
    
    @staticmethod
    def get_available_indicators() -> Dict[str, Any]:
        """사용 가능한 모든 지표 목록 반환"""
        category_vars = VariableDefinitions.get_category_variables()
        all_indicators = []
        for variables in category_vars.values():
            all_indicators.extend([var_id for var_id, _ in variables])
        
        return {
            "core": all_indicators,
            "custom": []
        }
