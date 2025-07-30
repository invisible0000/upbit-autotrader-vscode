#!/usr/bin/env python3
"""
변수 정의 모듈 (VariableDefinitions) - DB 중심 자동 생성
====================================================

⚠️  **이 파일은 자동 생성됩니다. 직접 편집하지 마세요!**

🎯 **DB 중심 워크플로우**:
1. tv_trading_variables, tv_variable_parameters 테이블 수정
2. GUI의 DB → Code 동기화 탭에서 동기화 실행
3. 생성된 파일 검토 및 배포

🔄 **마지막 동기화**: 2025-07-30 18:17:53
📊 **지표 통계**: 활성 41개 / 총 파라미터 37개
📋 **data_info 상태**:
  ✅ indicator_library: 11개 정의
  ✅ help_texts: 0개 도움말
  ✅ placeholders: 0개 예시

🚀 **향후 계획**: data_info → DB 마이그레이션으로 완전한 DB 중심화
"""

from typing import Dict, Any, List, Optional

# 호환성 검증기 import (shared 폴더)
try:
    from ..shared.compatibility_validator import CompatibilityValidator
    COMPATIBILITY_VALIDATOR_AVAILABLE = True
    print("✅ 통합 호환성 검증기 로드 성공")
except ImportError as e:
    print(f"⚠️ 통합 호환성 검증기 로드 실패: {e}")
    COMPATIBILITY_VALIDATOR_AVAILABLE = False



class VariableDefinitions:
    """트레이딩 변수들의 파라미터 정의를 관리하는 클래스 (DB 중심 자동 생성)"""

    # 📊 차트 카테고리 매핑 (DB 중심)
    CHART_CATEGORIES = {
        "ADX": "subplot",  # 평균방향성지수
        "AROON": "subplot",  # 아룬 지표
        "ATR": "subplot",  # 평균실제범위
        "AVG_BUY_PRICE": "subplot",  # 평균 매수가
        "BOLLINGER_BAND": "overlay",  # 볼린저 밴드
        "BOLLINGER_BANDS": "overlay",  # 볼린저 밴드
        "BOLLINGER_WIDTH": "subplot",  # 볼린저 밴드 폭
        "CASH_BALANCE": "subplot",  # 현금 잔고
        "CCI": "subplot",  # 상품채널지수
        "COIN_BALANCE": "subplot",  # 코인 보유량
        "CURRENT_PRICE": "overlay",  # 현재가
        "EMA": "overlay",  # 지수이동평균
        "HIGH_PRICE": "overlay",  # 고가
        "HULL_MA": "subplot",  # 헐 이동평균
        "ICHIMOKU": "overlay",  # 일목균형표
        "LOW_PRICE": "overlay",  # 저가
        "MACD": "subplot",  # MACD 지표
        "MFI": "subplot",  # 자금흐름지수
        "OBV": "subplot",  # 온밸런스 볼륨
        "OPEN_PRICE": "overlay",  # 시가
        "PARABOLIC_SAR": "overlay",  # 파라볼릭 SAR
        "PIVOT_POINTS": "overlay",  # 피봇 포인트
        "POSITION_SIZE": "subplot",  # 포지션 크기
        "PROFIT_AMOUNT": "subplot",  # 현재 수익 금액
        "PROFIT_PERCENT": "subplot",  # 현재 수익률(%)
        "ROC": "subplot",  # 가격변동률
        "RSI": "subplot",  # RSI 지표
        "SMA": "overlay",  # 단순이동평균
        "SQUEEZE_MOMENTUM": "subplot",  # 스퀴즈 모멘텀
        "STANDARD_DEVIATION": "subplot",  # 표준편차
        "STOCH": "subplot",  # 스토캐스틱
        "STOCHASTIC": "subplot",  # 스토캐스틱
        "STOCH_RSI": "subplot",  # 스토캐스틱 RSI
        "SUPERTREND": "overlay",  # 슈퍼트렌드
        "TOTAL_BALANCE": "subplot",  # 총 자산
        "VOLUME": "subplot",  # 거래량
        "VOLUME_PROFILE": "overlay",  # 거래량 프로파일
        "VOLUME_SMA": "subplot",  # 거래량 이동평균
        "VWAP": "overlay",  # 거래량가중평균가격
        "WILLIAMS_R": "subplot",  # 윌리엄스 %R
        "WMA": "overlay",  # 가중이동평균
    }

    @staticmethod
    def get_variable_parameters(variable_id: str) -> Dict[str, Any]:
        """지표별 파라미터 정보 반환 (DB 기반)"""
        parameters = {
            "ATR": {
                "period": {"type": "int", "default": 14, "label": "기간", "min": 1, "max": 100, "help": "ATR 계산 기간"},
                "timeframe": {"type": "enum", "default": "포지션 설정 따름", "label": "타임프레임", "options": ["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"], "help": "봉 단위 시간"},
            },
            "AVG_BUY_PRICE": {
                "display_currency": {"type": "enum", "default": "원화", "label": "표시 통화", "options": ["원화", "USD", "코인단위"], "help": "평균 매수가 표시 통화 (수수료 포함된 평단가)"},
            },
            "BOLLINGER_BAND": {
                "period": {"type": "int", "default": 20, "label": "기간", "min": 2, "max": 100, "help": "이동평균 기간"},
                "multiplier": {"type": "float", "default": 2.0, "label": "표준편차 배수", "min": 0.1, "max": 5.0, "help": "표준편차 곱셈 계수"},
                "timeframe": {"type": "enum", "default": "포지션 설정 따름", "label": "타임프레임", "options": ["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"], "help": "봉 단위 시간"},
            },
            "CASH_BALANCE": {
                "currency": {"type": "enum", "default": "KRW", "label": "표시 통화", "options": ["KRW", "USD", "BTC"], "help": "현금 잔고 표시 기준 통화"},
                "scope": {"type": "enum", "default": "포지션제한", "label": "범위", "options": ["포지션제한", "계좌전체"], "help": "포지션 할당 vs 전체 사용가능 현금"},
            },
            "COIN_BALANCE": {
                "coin_unit": {"type": "enum", "default": "코인수량", "label": "표시 단위", "options": ["코인수량", "원화가치", "USD가치"], "help": "코인 보유량 표시 방식"},
                "scope": {"type": "enum", "default": "현재코인", "label": "범위", "options": ["현재코인", "전체코인"], "help": "현재 거래중인 코인 vs 보유한 모든 코인"},
            },
            "EMA": {
                "period": {"type": "int", "default": 12, "label": "기간", "min": 1, "max": 240, "help": "지수이동평균 계산 기간"},
                "exponential_factor": {"type": "float", "default": 2.0, "label": "지수 계수", "min": 0.1, "max": 10.0, "help": "지수 가중치 (2/(기간+1)이 표준)"},
                "timeframe": {"type": "enum", "default": "포지션 설정 따름", "label": "타임프레임", "options": ["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"], "help": "봉 단위 시간"},
            },
            "HIGH_PRICE": {
                "timeframe": {"type": "enum", "default": "포지션 설정 따름", "label": "타임프레임", "options": ["포지션 설정 따름", "1분", "5분", "15분", "30분", "1시간", "4시간", "1일"], "help": "고가 기준 봉 단위"},
            },
            "LOW_PRICE": {
                "timeframe": {"type": "enum", "default": "포지션 설정 따름", "label": "타임프레임", "options": ["포지션 설정 따름", "1분", "5분", "15분", "30분", "1시간", "4시간", "1일"], "help": "저가 기준 봉 단위"},
            },
            "MACD": {
                "fast_period": {"type": "int", "default": 12, "label": "빠른 기간", "min": 1, "max": 50, "help": "빠른 EMA 기간"},
                "slow_period": {"type": "int", "default": 26, "label": "느린 기간", "min": 1, "max": 100, "help": "느린 EMA 기간"},
                "signal_period": {"type": "int", "default": 9, "label": "시그널 기간", "min": 1, "max": 50, "help": "시그널 라인 기간"},
                "timeframe": {"type": "enum", "default": "포지션 설정 따름", "label": "타임프레임", "options": ["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"], "help": "봉 단위 시간"},
            },
            "OPEN_PRICE": {
                "timeframe": {"type": "enum", "default": "포지션 설정 따름", "label": "타임프레임", "options": ["포지션 설정 따름", "1분", "5분", "15분", "30분", "1시간", "4시간", "1일"], "help": "시가 기준 봉 단위 (당일 시작가 등)"},
            },
            "POSITION_SIZE": {
                "unit_type": {"type": "enum", "default": "수량", "label": "단위 형태", "options": ["수량", "금액", "비율"], "help": "수량: 코인개수, 금액: 원화가치, 비율: 포트폴리오대비%"},
            },
            "PROFIT_AMOUNT": {
                "currency": {"type": "enum", "default": "KRW", "label": "표시 통화", "options": ["KRW", "USD", "BTC"], "help": "수익 금액 표시 통화"},
                "calculation_method": {"type": "enum", "default": "미실현", "label": "계산 방식", "options": ["미실현", "실현", "전체"], "help": "미실현: 현재가기준, 실현: 매도완료, 전체: 누적"},
                "include_fees": {"type": "enum", "default": "포함", "label": "수수료 포함", "options": ["포함", "제외"], "help": "거래 수수료 및 슬리피지 포함 여부"},
            },
            "RSI": {
                "period": {"type": "int", "default": 14, "label": "기간", "min": 2, "max": 240, "help": "RSI 계산 기간"},
                "timeframe": {"type": "enum", "default": "포지션 설정 따름", "label": "타임프레임", "options": ["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"], "help": "봉 단위 시간 (전략 기본값 사용 시 무시)"},
            },
            "SMA": {
                "period": {"type": "int", "default": 20, "label": "기간", "min": 1, "max": 240, "help": "단기: 5,10,20 / 중기: 60,120 / 장기: 200,240"},
                "timeframe": {"type": "enum", "default": "포지션 설정 따름", "label": "타임프레임", "options": ["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"], "help": "봉 단위 시간"},
            },
            "STOCHASTIC": {
                "k_period": {"type": "int", "default": 14, "label": "%K 기간", "min": 1, "max": 100, "help": "%K 라인 계산 기간"},
                "d_period": {"type": "int", "default": 3, "label": "%D 기간", "min": 1, "max": 50, "help": "%D 라인 계산 기간"},
                "timeframe": {"type": "enum", "default": "포지션 설정 따름", "label": "타임프레임", "options": ["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"], "help": "봉 단위 시간"},
            },
            "TOTAL_BALANCE": {
                "currency": {"type": "enum", "default": "KRW", "label": "표시 통화", "options": ["KRW", "USD", "BTC"], "help": "총 자산 표시 기준 통화"},
                "scope": {"type": "enum", "default": "포지션제한", "label": "범위", "options": ["포지션제한", "계좌전체"], "help": "포지션 할당 자본 vs 전체 계좌"},
            },
            "VOLUME": {
                "timeframe": {"type": "enum", "default": "포지션 설정 따름", "label": "타임프레임", "options": ["포지션 설정 따름", "1분", "5분", "15분", "30분", "1시간", "4시간", "1일"], "help": "거래량 기준 봉 단위"},
                "volume_type": {"type": "enum", "default": "거래량", "label": "거래량 종류", "options": ["거래량", "거래대금", "상대거래량"], "help": "거래량: 코인수량, 거래대금: 원화금액, 상대거래량: 평균대비 비율"},
            },
            "VOLUME_SMA": {
                "period": {"type": "int", "default": 20, "label": "기간", "min": 1, "max": 240, "help": "거래량 이동평균 계산 기간"},
                "timeframe": {"type": "enum", "default": "포지션 설정 따름", "label": "타임프레임", "options": ["포지션 설정 따름", "1분", "5분", "15분", "30분", "1시간", "4시간", "1일"], "help": "봉 단위 시간"},
            },
        }
        return parameters.get(variable_id, {})

    @staticmethod
    def get_variable_descriptions() -> Dict[str, str]:
        """변수별 설명 반환 (DB 기반)"""
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
    def get_category_variables() -> Dict[str, List[tuple]]:
        """카테고리별 변수 목록 반환 (DB 기반)"""
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

    @staticmethod
    def get_variable_placeholders() -> Dict[str, Dict[str, str]]:
        """지표별 사용 예시 및 플레이스홀더"""
        placeholders = {
            "ADX": {
                "basic_usage": "평균방향성지수 기본 설정으로 매매 신호 생성",
                "advanced_usage": "평균방향성지수 고급 설정으로 정밀한 분석",
            },
            "AROON": {
                "basic_usage": "아룬 지표 기본 설정으로 매매 신호 생성",
                "advanced_usage": "아룬 지표 고급 설정으로 정밀한 분석",
            },
            "ATR": {
                "basic_usage": "평균실제범위 기본 설정으로 매매 신호 생성",
                "advanced_usage": "평균실제범위 고급 설정으로 정밀한 분석",
            },
            "AVG_BUY_PRICE": {
                "basic_usage": "평균 매수가 기본 설정으로 매매 신호 생성",
                "advanced_usage": "평균 매수가 고급 설정으로 정밀한 분석",
            },
            "BOLLINGER_BAND": {
                "basic_usage": "볼린저 밴드 기본 설정으로 매매 신호 생성",
                "advanced_usage": "볼린저 밴드 고급 설정으로 정밀한 분석",
            },
            "BOLLINGER_BANDS": {
                "basic_usage": "볼린저 밴드 기본 설정으로 매매 신호 생성",
                "advanced_usage": "볼린저 밴드 고급 설정으로 정밀한 분석",
            },
            "BOLLINGER_WIDTH": {
                "basic_usage": "볼린저 밴드 폭 기본 설정으로 매매 신호 생성",
                "advanced_usage": "볼린저 밴드 폭 고급 설정으로 정밀한 분석",
            },
            "CASH_BALANCE": {
                "basic_usage": "현금 잔고 기본 설정으로 매매 신호 생성",
                "advanced_usage": "현금 잔고 고급 설정으로 정밀한 분석",
            },
            "CCI": {
                "basic_usage": "상품채널지수 기본 설정으로 매매 신호 생성",
                "advanced_usage": "상품채널지수 고급 설정으로 정밀한 분석",
            },
            "COIN_BALANCE": {
                "basic_usage": "코인 보유량 기본 설정으로 매매 신호 생성",
                "advanced_usage": "코인 보유량 고급 설정으로 정밀한 분석",
            },
            "CURRENT_PRICE": {
                "basic_usage": "현재가 기본 설정으로 매매 신호 생성",
                "advanced_usage": "현재가 고급 설정으로 정밀한 분석",
            },
            "EMA": {
                "basic_usage": "지수이동평균 기본 설정으로 매매 신호 생성",
                "advanced_usage": "지수이동평균 고급 설정으로 정밀한 분석",
            },
            "HIGH_PRICE": {
                "basic_usage": "고가 기본 설정으로 매매 신호 생성",
                "advanced_usage": "고가 고급 설정으로 정밀한 분석",
            },
            "HULL_MA": {
                "basic_usage": "헐 이동평균 기본 설정으로 매매 신호 생성",
                "advanced_usage": "헐 이동평균 고급 설정으로 정밀한 분석",
            },
            "ICHIMOKU": {
                "basic_usage": "일목균형표 기본 설정으로 매매 신호 생성",
                "advanced_usage": "일목균형표 고급 설정으로 정밀한 분석",
            },
            "LOW_PRICE": {
                "basic_usage": "저가 기본 설정으로 매매 신호 생성",
                "advanced_usage": "저가 고급 설정으로 정밀한 분석",
            },
            "MACD": {
                "basic_usage": "MACD 지표 기본 설정으로 매매 신호 생성",
                "advanced_usage": "MACD 지표 고급 설정으로 정밀한 분석",
            },
            "MFI": {
                "basic_usage": "자금흐름지수 기본 설정으로 매매 신호 생성",
                "advanced_usage": "자금흐름지수 고급 설정으로 정밀한 분석",
            },
            "OBV": {
                "basic_usage": "온밸런스 볼륨 기본 설정으로 매매 신호 생성",
                "advanced_usage": "온밸런스 볼륨 고급 설정으로 정밀한 분석",
            },
            "OPEN_PRICE": {
                "basic_usage": "시가 기본 설정으로 매매 신호 생성",
                "advanced_usage": "시가 고급 설정으로 정밀한 분석",
            },
            "PARABOLIC_SAR": {
                "basic_usage": "파라볼릭 SAR 기본 설정으로 매매 신호 생성",
                "advanced_usage": "파라볼릭 SAR 고급 설정으로 정밀한 분석",
            },
            "PIVOT_POINTS": {
                "basic_usage": "피봇 포인트 기본 설정으로 매매 신호 생성",
                "advanced_usage": "피봇 포인트 고급 설정으로 정밀한 분석",
            },
            "POSITION_SIZE": {
                "basic_usage": "포지션 크기 기본 설정으로 매매 신호 생성",
                "advanced_usage": "포지션 크기 고급 설정으로 정밀한 분석",
            },
            "PROFIT_AMOUNT": {
                "basic_usage": "현재 수익 금액 기본 설정으로 매매 신호 생성",
                "advanced_usage": "현재 수익 금액 고급 설정으로 정밀한 분석",
            },
            "PROFIT_PERCENT": {
                "basic_usage": "현재 수익률(%) 기본 설정으로 매매 신호 생성",
                "advanced_usage": "현재 수익률(%) 고급 설정으로 정밀한 분석",
            },
            "ROC": {
                "basic_usage": "가격변동률 기본 설정으로 매매 신호 생성",
                "advanced_usage": "가격변동률 고급 설정으로 정밀한 분석",
            },
            "RSI": {
                "basic_usage": "RSI 지표 기본 설정으로 매매 신호 생성",
                "advanced_usage": "RSI 지표 고급 설정으로 정밀한 분석",
            },
            "SMA": {
                "basic_usage": "단순이동평균 기본 설정으로 매매 신호 생성",
                "advanced_usage": "단순이동평균 고급 설정으로 정밀한 분석",
            },
            "SQUEEZE_MOMENTUM": {
                "basic_usage": "스퀴즈 모멘텀 기본 설정으로 매매 신호 생성",
                "advanced_usage": "스퀴즈 모멘텀 고급 설정으로 정밀한 분석",
            },
            "STANDARD_DEVIATION": {
                "basic_usage": "표준편차 기본 설정으로 매매 신호 생성",
                "advanced_usage": "표준편차 고급 설정으로 정밀한 분석",
            },
            "STOCH": {
                "basic_usage": "스토캐스틱 기본 설정으로 매매 신호 생성",
                "advanced_usage": "스토캐스틱 고급 설정으로 정밀한 분석",
            },
            "STOCHASTIC": {
                "basic_usage": "스토캐스틱 기본 설정으로 매매 신호 생성",
                "advanced_usage": "스토캐스틱 고급 설정으로 정밀한 분석",
            },
            "STOCH_RSI": {
                "basic_usage": "스토캐스틱 RSI 기본 설정으로 매매 신호 생성",
                "advanced_usage": "스토캐스틱 RSI 고급 설정으로 정밀한 분석",
            },
            "SUPERTREND": {
                "basic_usage": "슈퍼트렌드 기본 설정으로 매매 신호 생성",
                "advanced_usage": "슈퍼트렌드 고급 설정으로 정밀한 분석",
            },
            "TOTAL_BALANCE": {
                "basic_usage": "총 자산 기본 설정으로 매매 신호 생성",
                "advanced_usage": "총 자산 고급 설정으로 정밀한 분석",
            },
            "VOLUME": {
                "basic_usage": "거래량 기본 설정으로 매매 신호 생성",
                "advanced_usage": "거래량 고급 설정으로 정밀한 분석",
            },
            "VOLUME_PROFILE": {
                "basic_usage": "거래량 프로파일 기본 설정으로 매매 신호 생성",
                "advanced_usage": "거래량 프로파일 고급 설정으로 정밀한 분석",
            },
            "VOLUME_SMA": {
                "basic_usage": "거래량 이동평균 기본 설정으로 매매 신호 생성",
                "advanced_usage": "거래량 이동평균 고급 설정으로 정밀한 분석",
            },
            "VWAP": {
                "basic_usage": "거래량가중평균가격 기본 설정으로 매매 신호 생성",
                "advanced_usage": "거래량가중평균가격 고급 설정으로 정밀한 분석",
            },
            "WILLIAMS_R": {
                "basic_usage": "윌리엄스 %R 기본 설정으로 매매 신호 생성",
                "advanced_usage": "윌리엄스 %R 고급 설정으로 정밀한 분석",
            },
            "WMA": {
                "basic_usage": "가중이동평균 기본 설정으로 매매 신호 생성",
                "advanced_usage": "가중이동평균 고급 설정으로 정밀한 분석",
            },
        }
        return placeholders

    @staticmethod
    def get_variable_help_text(variable_id: str, parameter_name: str = None) -> str:
        """지표별 상세 도움말 텍스트"""
        help_texts = {
            "ADX": {
                "overview": "추세의 강도를 측정하는 지표 (방향은 알려주지 않음)",
            },
            "AROON": {
                "overview": "최고가/최저가 도달 후 경과 시간으로 추세 시작을 파악",
            },
            "ATR": {
                "overview": "주가의 변동성을 측정하는 지표. 절대적인 가격 변동폭을 나타냄",
                "parameters": {
                    "period": "ATR 계산 기간",
                    "timeframe": "봉 단위 시간",
                },
            },
            "AVG_BUY_PRICE": {
                "overview": "수수료 포함 평균 매수가",
                "parameters": {
                    "display_currency": "평균 매수가 표시 통화 (수수료 포함된 평단가)",
                },
            },
            "BOLLINGER_BAND": {
                "overview": "이동평균선과 표준편차를 이용한 변동성 채널",
                "trading_signals": "가격이 상단밴드 터치: 과매수, 매도 고려 | 가격이 하단밴드 터치: 과매도, 매수 고려 | 밴드 폭 축소: 변동성 압축, 큰 움직임 예고",
                "parameters": {
                    "period": "이동평균 기간",
                    "multiplier": "표준편차 곱셈 계수",
                    "timeframe": "봉 단위 시간",
                },
            },
            "BOLLINGER_BANDS": {
                "overview": "이동평균선과 표준편차를 이용한 변동성 채널",
            },
            "BOLLINGER_WIDTH": {
                "overview": "볼린저 밴드의 상하단 폭으로 변동성의 축소/확대를 파악",
            },
            "CASH_BALANCE": {
                "overview": "사용 가능한 현금 잔고",
                "parameters": {
                    "currency": "현금 잔고 표시 기준 통화",
                    "scope": "포지션 할당 vs 전체 사용가능 현금",
                },
            },
            "CCI": {
                "overview": "현재 가격이 평균 가격과 얼마나 떨어져 있는지를 측정",
            },
            "COIN_BALANCE": {
                "overview": "현재 보유중인 코인 수량",
                "parameters": {
                    "coin_unit": "코인 보유량 표시 방식",
                    "scope": "현재 거래중인 코인 vs 보유한 모든 코인",
                },
            },
            "CURRENT_PRICE": {
                "overview": "현재 시점의 가격",
            },
            "EMA": {
                "overview": "최근 가격에 더 큰 가중치를 부여한 이동평균",
                "parameters": {
                    "period": "지수이동평균 계산 기간",
                    "exponential_factor": "지수 가중치 (2/(기간+1)이 표준)",
                    "timeframe": "봉 단위 시간",
                },
            },
            "HIGH_PRICE": {
                "overview": "특정 기간의 최고가",
                "parameters": {
                    "timeframe": "고가 기준 봉 단위",
                },
            },
            "HULL_MA": {
                "overview": "매우 부드러운 이동평균 지표",
            },
            "ICHIMOKU": {
                "overview": "전환선, 기준선, 구름대 등을 통한 종합 분석 지표",
            },
            "LOW_PRICE": {
                "overview": "특정 기간의 최저가",
                "parameters": {
                    "timeframe": "저가 기준 봉 단위",
                },
            },
            "MACD": {
                "overview": "두 이동평균선 사이의 관계를 보여주는 모멘텀 및 추세 지표",
                "trading_signals": "MACD > 시그널: 상승 추세 | 히스토그램 0선 돌파: 골든크로스/데드크로스",
                "parameters": {
                    "fast_period": "빠른 EMA 기간",
                    "slow_period": "느린 EMA 기간",
                    "signal_period": "시그널 라인 기간",
                    "timeframe": "봉 단위 시간",
                },
            },
            "MFI": {
                "overview": "거래량을 고려한 RSI로, 자금의 유입 및 유출 강도를 나타냄",
            },
            "OBV": {
                "overview": "상승일 거래량은 더하고 하락일 거래량은 빼서 거래량 흐름을 표시",
            },
            "OPEN_PRICE": {
                "overview": "특정 기간의 시작 가격",
                "parameters": {
                    "timeframe": "시가 기준 봉 단위 (당일 시작가 등)",
                },
            },
            "PARABOLIC_SAR": {
                "overview": "추세의 전환 가능 지점을 점으로 나타내는 추세 추종 지표",
            },
            "PIVOT_POINTS": {
                "overview": "전일/전주/전월의 고가, 저가, 종가를 이용해 지지선과 저항선을 계산",
            },
            "POSITION_SIZE": {
                "overview": "현재 포지션의 크기",
                "parameters": {
                    "unit_type": "수량: 코인개수, 금액: 원화가치, 비율: 포트폴리오대비%",
                },
            },
            "PROFIT_AMOUNT": {
                "overview": "매수가 대비 현재 수익 금액",
                "parameters": {
                    "currency": "수익 금액 표시 통화",
                    "calculation_method": "미실현: 현재가기준, 실현: 매도완료, 전체: 누적",
                    "include_fees": "거래 수수료 및 슬리피지 포함 여부",
                },
            },
            "PROFIT_PERCENT": {
                "overview": "매수가 대비 현재 수익률",
            },
            "ROC": {
                "overview": "현재 가격과 n일 전 가격의 변화율을 측정",
            },
            "RSI": {
                "overview": "상승압력과 하락압력 간의 상대적 강도를 나타내는 모멘텀 지표",
                "interpretation": {
                    "overbought": "70 이상 (과매수)",
                    "oversold": "30 이하 (과매도)",
                    "neutral": "30-70 (중립)",
                },
                "trading_signals": "RSI > 70: 매도 고려 | RSI < 30: 매수 고려 | 50선 돌파: 추세 변화 신호",
                "parameters": {
                    "period": "RSI 계산 기간",
                    "timeframe": "봉 단위 시간 (전략 기본값 사용 시 무시)",
                },
            },
            "SMA": {
                "overview": "특정 기간의 가격을 산술 평균한 값",
                "trading_signals": "가격 > SMA: 상승 추세 | 단기선 > 장기선: 골든크로스 | 단기선 < 장기선: 데드크로스",
                "parameters": {
                    "period": "단기: 5,10,20 / 중기: 60,120 / 장기: 200,240",
                    "timeframe": "봉 단위 시간",
                },
            },
            "SQUEEZE_MOMENTUM": {
                "overview": "볼린저 밴드와 켈트너 채널을 이용해 변동성 압축 후 폭발 방향을 예측",
            },
            "STANDARD_DEVIATION": {
                "overview": "가격이 평균에서 얼마나 떨어져 있는지를 측정하는 통계적 변동성 지표",
            },
            "STOCH": {
                "overview": "특정 기간 주가 변동 범위에서 현재 주가의 위치를 백분율로 표시",
            },
            "STOCHASTIC": {
                "overview": "특정 기간 주가 변동 범위에서 현재 주가의 위치를 백분율로 표시",
                "interpretation": {
                    "overbought": "80 이상",
                    "oversold": "20 이하",
                },
                "trading_signals": "%K가 %D 상향돌파: 매수 신호 | %K가 %D 하향돌파: 매도 신호",
                "parameters": {
                    "k_period": "%K 라인 계산 기간",
                    "d_period": "%D 라인 계산 기간",
                    "timeframe": "봉 단위 시간",
                },
            },
            "STOCH_RSI": {
                "overview": "RSI 값에 스토캐스틱 공식을 적용하여 더 민감한 신호 생성",
            },
            "SUPERTREND": {
                "overview": "ATR을 기반으로 추세의 방향과 변동성을 시각적으로 표시",
            },
            "TOTAL_BALANCE": {
                "overview": "현금과 코인을 합친 총 자산",
                "parameters": {
                    "currency": "총 자산 표시 기준 통화",
                    "scope": "포지션 할당 자본 vs 전체 계좌",
                },
            },
            "VOLUME": {
                "overview": "특정 기간 동안 거래된 주식의 총 수량",
                "parameters": {
                    "timeframe": "거래량 기준 봉 단위",
                    "volume_type": "거래량: 코인수량, 거래대금: 원화금액, 상대거래량: 평균대비 비율",
                },
            },
            "VOLUME_PROFILE": {
                "overview": "가격대별 거래량을 히스토그램으로 표시",
            },
            "VOLUME_SMA": {
                "overview": "거래량의 단순이동평균으로 평균 거래량 대비 현재 거래량 비교",
                "trading_signals": "거래량 > 거래량SMA: 거래량 증가 | 급격한 거래량 증가: 중요한 움직임 시사",
                "parameters": {
                    "period": "거래량 이동평균 계산 기간",
                    "timeframe": "봉 단위 시간",
                },
            },
            "VWAP": {
                "overview": "당일 거래량을 가중치로 부여한 평균 가격",
            },
            "WILLIAMS_R": {
                "overview": "스토캐스틱과 유사하게 과매수/과매도 수준을 측정",
            },
            "WMA": {
                "overview": "기간 내 가격에 선형적으로 가중치를 부여한 이동평균",
            },
        }

        if variable_id not in help_texts:
            return f"지표 {variable_id}에 대한 도움말이 준비되지 않았습니다."

        var_help = help_texts[variable_id]
        if parameter_name:
            return var_help.get("parameters", {}).get(parameter_name, f"파라미터 {parameter_name}에 대한 도움말이 없습니다.")
        else:
            return var_help.get("overview", "도움말이 없습니다.")

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
            "custom": [],
            "categories": list(category_vars.keys()),
            "total_count": len(all_indicators)
        }
    
    @staticmethod
    def get_indicator_metadata(variable_id: str) -> Dict[str, Any]:
        """지표의 메타데이터 정보 반환"""
        parameters = VariableDefinitions.get_variable_parameters(variable_id)
        descriptions = VariableDefinitions.get_variable_descriptions()
        category = VariableDefinitions.get_variable_category(variable_id)
        chart_category = VariableDefinitions.CHART_CATEGORIES.get(variable_id, "subplot")
        
        return {
            "variable_id": variable_id,
            "description": descriptions.get(variable_id, "설명 없음"),
            "category": category,
            "chart_category": chart_category,
            "parameters": parameters,
            "parameter_count": len(parameters),
            "has_help": bool(VariableDefinitions.get_variable_help_text(variable_id)),
        }
