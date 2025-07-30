#!/usr/bin/env python3
"""
변수 정의 모듈 (VariableDefinitions) - DB 동기화 자동 생성
==================================================

⚠️  **이 파일은 자동 생성됩니다. 직접 편집하지 마세요!**
📝 **편집하려면**: data/app_settings.sqlite3의 tv_trading_variables 테이블을 수정 후 sync_db_to_code.py 실행

🔄 **마지막 동기화**: 2025-07-30 16:17:29
📊 **총 지표 수**: 41개

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
        "AVG_BUY_PRICE": "subplot",
        "BOLLINGER_BAND": "overlay",
        "BOLLINGER_BANDS": "overlay",
        "BOLLINGER_WIDTH": "subplot",
        "CASH_BALANCE": "subplot",
        "CCI": "subplot",
        "COIN_BALANCE": "subplot",
        "CURRENT_PRICE": "overlay",
        "EMA": "overlay",
        "HIGH_PRICE": "overlay",
        "HULL_MA": "subplot",
        "ICHIMOKU": "overlay",
        "LOW_PRICE": "overlay",
        "MACD": "subplot",
        "MFI": "subplot",
        "OBV": "subplot",
        "OPEN_PRICE": "overlay",
        "PARABOLIC_SAR": "overlay",
        "PIVOT_POINTS": "overlay",
        "POSITION_SIZE": "subplot",
        "PROFIT_AMOUNT": "subplot",
        "PROFIT_PERCENT": "subplot",
        "ROC": "subplot",
        "RSI": "subplot",
        "SMA": "overlay",
        "SQUEEZE_MOMENTUM": "subplot",
        "STANDARD_DEVIATION": "subplot",
        "STOCH": "subplot",
        "STOCHASTIC": "subplot",
        "STOCH_RSI": "subplot",
        "SUPERTREND": "overlay",
        "TOTAL_BALANCE": "subplot",
        "VOLUME": "subplot",
        "VOLUME_PROFILE": "overlay",
        "VOLUME_SMA": "subplot",
        "VWAP": "overlay",
        "WILLIAMS_R": "subplot",
        "WMA": "overlay",
    }
    @staticmethod
    def get_variable_parameters(var_id: str) -> Dict[str, Any]:
        """변수별 파라미터 정의 반환 (DB 동기화)"""
        params = {
            "ATR": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "default": 14,
                    "help": "ATR 계산 기간",
                    "min": 1,
                    "max": 100,
                },
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "default": "포지션 설정 따름",
                    "help": "봉 단위 시간",
                    "options": ['포지션 설정 따름', '1분', '3분', '5분', '15분', '30분', '1시간', '4시간', '1일'],
                },
            },
            "AVG_BUY_PRICE": {
                "display_currency": {
                    "label": "표시 통화",
                    "type": "enum",
                    "default": "원화",
                    "help": "평균 매수가 표시 통화 (수수료 포함된 평단가)",
                    "options": ['원화', 'USD', '코인단위'],
                },
            },
            "BOLLINGER_BAND": {
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
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "default": "포지션 설정 따름",
                    "help": "봉 단위 시간",
                    "options": ['포지션 설정 따름', '1분', '3분', '5분', '15분', '30분', '1시간', '4시간', '1일'],
                },
            },
            "CASH_BALANCE": {
                "currency": {
                    "label": "표시 통화",
                    "type": "enum",
                    "default": "KRW",
                    "help": "현금 잔고 표시 기준 통화",
                    "options": ['KRW', 'USD', 'BTC'],
                },
                "scope": {
                    "label": "범위",
                    "type": "enum",
                    "default": "포지션제한",
                    "help": "포지션 할당 vs 전체 사용가능 현금",
                    "options": ['포지션제한', '계좌전체'],
                },
            },
            "COIN_BALANCE": {
                "coin_unit": {
                    "label": "표시 단위",
                    "type": "enum",
                    "default": "코인수량",
                    "help": "코인 보유량 표시 방식",
                    "options": ['코인수량', '원화가치', 'USD가치'],
                },
                "scope": {
                    "label": "범위",
                    "type": "enum",
                    "default": "현재코인",
                    "help": "현재 거래중인 코인 vs 보유한 모든 코인",
                    "options": ['현재코인', '전체코인'],
                },
            },
            "EMA": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "default": 12,
                    "help": "지수이동평균 계산 기간",
                    "min": 1,
                    "max": 240,
                },
                "exponential_factor": {
                    "label": "지수 계수",
                    "type": "float",
                    "default": 2.0,
                    "help": "지수 가중치 (2/(기간+1)이 표준)",
                    "min": 0.1,
                    "max": 10.0,
                },
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "default": "포지션 설정 따름",
                    "help": "봉 단위 시간",
                    "options": ['포지션 설정 따름', '1분', '3분', '5분', '15분', '30분', '1시간', '4시간', '1일'],
                },
            },
            "HIGH_PRICE": {
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "default": "포지션 설정 따름",
                    "help": "고가 기준 봉 단위",
                    "options": ['포지션 설정 따름', '1분', '5분', '15분', '30분', '1시간', '4시간', '1일'],
                },
            },
            "LOW_PRICE": {
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "default": "포지션 설정 따름",
                    "help": "저가 기준 봉 단위",
                    "options": ['포지션 설정 따름', '1분', '5분', '15분', '30분', '1시간', '4시간', '1일'],
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
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "default": "포지션 설정 따름",
                    "help": "봉 단위 시간",
                    "options": ['포지션 설정 따름', '1분', '3분', '5분', '15분', '30분', '1시간', '4시간', '1일'],
                },
            },
            "OPEN_PRICE": {
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "default": "포지션 설정 따름",
                    "help": "시가 기준 봉 단위 (당일 시작가 등)",
                    "options": ['포지션 설정 따름', '1분', '5분', '15분', '30분', '1시간', '4시간', '1일'],
                },
            },
            "POSITION_SIZE": {
                "unit_type": {
                    "label": "단위 형태",
                    "type": "enum",
                    "default": "수량",
                    "help": "수량: 코인개수, 금액: 원화가치, 비율: 포트폴리오대비%",
                    "options": ['수량', '금액', '비율'],
                },
            },
            "PROFIT_AMOUNT": {
                "currency": {
                    "label": "표시 통화",
                    "type": "enum",
                    "default": "KRW",
                    "help": "수익 금액 표시 통화",
                    "options": ['KRW', 'USD', 'BTC'],
                },
                "calculation_method": {
                    "label": "계산 방식",
                    "type": "enum",
                    "default": "미실현",
                    "help": "미실현: 현재가기준, 실현: 매도완료, 전체: 누적",
                    "options": ['미실현', '실현', '전체'],
                },
                "include_fees": {
                    "label": "수수료 포함",
                    "type": "enum",
                    "default": "포함",
                    "help": "거래 수수료 및 슬리피지 포함 여부",
                    "options": ['포함', '제외'],
                },
            },
            "RSI": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "default": 14,
                    "help": "RSI 계산 기간",
                    "min": 2,
                    "max": 240,
                },
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "default": "포지션 설정 따름",
                    "help": "봉 단위 시간 (전략 기본값 사용 시 무시)",
                    "options": ['포지션 설정 따름', '1분', '3분', '5분', '15분', '30분', '1시간', '4시간', '1일'],
                },
            },
            "SMA": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "default": 20,
                    "help": "단기: 5,10,20 / 중기: 60,120 / 장기: 200,240",
                    "min": 1,
                    "max": 240,
                },
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "default": "포지션 설정 따름",
                    "help": "봉 단위 시간",
                    "options": ['포지션 설정 따름', '1분', '3분', '5분', '15분', '30분', '1시간', '4시간', '1일'],
                },
            },
            "STOCHASTIC": {
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
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "default": "포지션 설정 따름",
                    "help": "봉 단위 시간",
                    "options": ['포지션 설정 따름', '1분', '3분', '5분', '15분', '30분', '1시간', '4시간', '1일'],
                },
            },
            "TOTAL_BALANCE": {
                "currency": {
                    "label": "표시 통화",
                    "type": "enum",
                    "default": "KRW",
                    "help": "총 자산 표시 기준 통화",
                    "options": ['KRW', 'USD', 'BTC'],
                },
                "scope": {
                    "label": "범위",
                    "type": "enum",
                    "default": "포지션제한",
                    "help": "포지션 할당 자본 vs 전체 계좌",
                    "options": ['포지션제한', '계좌전체'],
                },
            },
            "VOLUME": {
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "default": "포지션 설정 따름",
                    "help": "거래량 기준 봉 단위",
                    "options": ['포지션 설정 따름', '1분', '5분', '15분', '30분', '1시간', '4시간', '1일'],
                },
                "volume_type": {
                    "label": "거래량 종류",
                    "type": "enum",
                    "default": "거래량",
                    "help": "거래량: 코인수량, 거래대금: 원화금액, 상대거래량: 평균대비 비율",
                    "options": ['거래량', '거래대금', '상대거래량'],
                },
            },
            "VOLUME_SMA": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "default": 20,
                    "help": "거래량 이동평균 계산 기간",
                    "min": 1,
                    "max": 240,
                },
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "default": "포지션 설정 따름",
                    "help": "봉 단위 시간",
                    "options": ['포지션 설정 따름', '1분', '5분', '15분', '30분', '1시간', '4시간', '1일'],
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
            "AVG_BUY_PRICE": "수수료 포함 평균 매수가",
            "BOLLINGER_BAND": "이동평균선과 표준편차를 이용한 변동성 채널",
            "BOLLINGER_BANDS": "이동평균선과 표준편차를 이용한 변동성 채널",
            "BOLLINGER_WIDTH": "볼린저 밴드의 상하단 폭으로 변동성의 축소/확대를 파악",
            "CASH_BALANCE": "사용 가능한 현금 잔고",
            "CCI": "현재 가격이 평균 가격과 얼마나 떨어져 있는지를 측정",
            "COIN_BALANCE": "현재 보유중인 코인 수량",
            "CURRENT_PRICE": "현재 시점의 가격",
            "EMA": "최근 가격에 더 큰 가중치를 부여한 이동평균",
            "HIGH_PRICE": "특정 기간의 최고가",
            "HULL_MA": "매우 부드러운 이동평균 지표",
            "ICHIMOKU": "전환선, 기준선, 구름대 등을 통한 종합 분석 지표",
            "LOW_PRICE": "특정 기간의 최저가",
            "MACD": "두 이동평균선 사이의 관계를 보여주는 모멘텀 및 추세 지표",
            "MFI": "거래량을 고려한 RSI로, 자금의 유입 및 유출 강도를 나타냄",
            "OBV": "상승일 거래량은 더하고 하락일 거래량은 빼서 거래량 흐름을 표시",
            "OPEN_PRICE": "특정 기간의 시작 가격",
            "PARABOLIC_SAR": "추세의 전환 가능 지점을 점으로 나타내는 추세 추종 지표",
            "PIVOT_POINTS": "전일/전주/전월의 고가, 저가, 종가를 이용해 지지선과 저항선을 계산",
            "POSITION_SIZE": "현재 포지션의 크기",
            "PROFIT_AMOUNT": "매수가 대비 현재 수익 금액",
            "PROFIT_PERCENT": "매수가 대비 현재 수익률",
            "ROC": "현재 가격과 n일 전 가격의 변화율을 측정",
            "RSI": "상승압력과 하락압력 간의 상대적 강도를 나타내는 모멘텀 지표",
            "SMA": "특정 기간의 가격을 산술 평균한 값",
            "SQUEEZE_MOMENTUM": "볼린저 밴드와 켈트너 채널을 이용해 변동성 압축 후 폭발 방향을 예측",
            "STANDARD_DEVIATION": "가격이 평균에서 얼마나 떨어져 있는지를 측정하는 통계적 변동성 지표",
            "STOCH": "특정 기간 주가 변동 범위에서 현재 주가의 위치를 백분율로 표시",
            "STOCHASTIC": "특정 기간 주가 변동 범위에서 현재 주가의 위치를 백분율로 표시",
            "STOCH_RSI": "RSI 값에 스토캐스틱 공식을 적용하여 더 민감한 신호 생성",
            "SUPERTREND": "ATR을 기반으로 추세의 방향과 변동성을 시각적으로 표시",
            "TOTAL_BALANCE": "현금과 코인을 합친 총 자산",
            "VOLUME": "특정 기간 동안 거래된 주식의 총 수량",
            "VOLUME_PROFILE": "가격대별 거래량을 히스토그램으로 표시",
            "VOLUME_SMA": "거래량의 단순이동평균으로 평균 거래량 대비 현재 거래량 비교",
            "VWAP": "당일 거래량을 가중치로 부여한 평균 가격",
            "WILLIAMS_R": "스토캐스틱과 유사하게 과매수/과매도 수준을 측정",
            "WMA": "기간 내 가격에 선형적으로 가중치를 부여한 이동평균",
        }
    @staticmethod
    def get_category_variables() -> Dict[str, list]:
        """카테고리별 변수 목록 반환 (DB 동기화)"""
        return {
            "capital": [
                ("CASH_BALANCE", "현금 잔고"),
                ("COIN_BALANCE", "코인 보유량"),
                ("TOTAL_BALANCE", "총 자산"),
            ],
            "momentum": [
                ("CCI", "상품채널지수"),
                ("HULL_MA", "헐 이동평균"),
                ("MACD", "MACD 지표"),
                ("MFI", "자금흐름지수"),
                ("ROC", "가격변동률"),
                ("RSI", "RSI 지표"),
                ("SQUEEZE_MOMENTUM", "스퀴즈 모멘텀"),
                ("STOCH", "스토캐스틱"),
                ("STOCHASTIC", "스토캐스틱"),
                ("STOCH_RSI", "스토캐스틱 RSI"),
                ("WILLIAMS_R", "윌리엄스 %R"),
            ],
            "price": [
                ("CURRENT_PRICE", "현재가"),
                ("HIGH_PRICE", "고가"),
                ("LOW_PRICE", "저가"),
                ("OPEN_PRICE", "시가"),
            ],
            "state": [
                ("AVG_BUY_PRICE", "평균 매수가"),
                ("POSITION_SIZE", "포지션 크기"),
                ("PROFIT_AMOUNT", "현재 수익 금액"),
                ("PROFIT_PERCENT", "현재 수익률(%)"),
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
                ("BOLLINGER_BAND", "볼린저 밴드"),
                ("BOLLINGER_WIDTH", "볼린저 밴드 폭"),
                ("STANDARD_DEVIATION", "표준편차"),
            ],
            "volume": [
                ("OBV", "온밸런스 볼륨"),
                ("VOLUME", "거래량"),
                ("VOLUME_PROFILE", "거래량 프로파일"),
                ("VOLUME_SMA", "거래량 이동평균"),
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
