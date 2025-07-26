#!/usr/bin/env python3
"""
변수 정의 모듈 - 모든 트레이딩 변수의 파라미터 정의
통합된 하이브리드 지표 시스템 지원
"""

from typing import Dict, Any
import sys
import os

# 호환성 검증기 import (같은 폴더)
try:
    from .compatibility_validator import CompatibilityValidator
    COMPATIBILITY_VALIDATOR_AVAILABLE = True
    print("✅ 통합 호환성 검증기 로드 성공 (trigger_builder/components)")
except ImportError as e:
    print(f"⚠️ 통합 호환성 검증기 로드 실패: {e}")
    COMPATIBILITY_VALIDATOR_AVAILABLE = False

# IntegratedVariableManager 임포트
try:
    # 상대 경로로 trading_variables 모듈 찾기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    trading_variables_path = os.path.join(current_dir, '..', '..', '..', '..', '..', 'utils', 'trading_variables')
    if trading_variables_path not in sys.path:
        sys.path.insert(0, trading_variables_path)
    
    from integrated_variable_manager import IntegratedVariableManager, HybridCompatibilityValidator
    HYBRID_SYSTEM_AVAILABLE = True
    print("✅ 하이브리드 지표 시스템 연동 성공")
except ImportError as e:
    print(f"⚠️ 하이브리드 지표 시스템을 찾을 수 없습니다: {e}")
    HYBRID_SYSTEM_AVAILABLE = False

class VariableDefinitions:
    """트레이딩 변수들의 파라미터 정의를 관리하는 클래스 (하이브리드 지표 시스템 통합)"""
    
    # 클래스 변수로 통합 관리자 초기화
    _integrated_manager = None
    _compatibility_validator = None
    
    # 📊 표준화 문서 기반 차트 카테고리 매핑 (이중 카테고리 시스템)
    CHART_CATEGORIES = {
        # 오버레이 (메인 차트에 표시)
        "SMA": "overlay",
        "EMA": "overlay", 
        "BOLLINGER_BAND": "overlay",
        "CURRENT_PRICE": "overlay",
        "OPEN_PRICE": "overlay",
        "HIGH_PRICE": "overlay",
        "LOW_PRICE": "overlay",
        
        # 서브플롯 (별도 차트에 표시)
        "RSI": "subplot",
        "STOCHASTIC": "subplot",
        "MACD": "subplot",
        "ATR": "subplot",
        "VOLUME": "subplot",
        "VOLUME_SMA": "subplot",
        
        # 재무 정보 (별도 영역)
        "CASH_BALANCE": "subplot",
        "COIN_BALANCE": "subplot", 
        "TOTAL_BALANCE": "subplot",
        "PROFIT_PERCENT": "subplot",
        "PROFIT_AMOUNT": "subplot",
        "POSITION_SIZE": "subplot",
        "AVG_BUY_PRICE": "subplot"
    }
    
    @classmethod
    def get_chart_category(cls, variable_id: str) -> str:
        """변수 ID의 차트 카테고리 반환 (overlay or subplot)"""
        return cls.CHART_CATEGORIES.get(variable_id, "subplot")
    
    @classmethod
    def is_overlay_indicator(cls, variable_id: str) -> bool:
        """오버레이 지표인지 확인"""
        return cls.get_chart_category(variable_id) == "overlay"
    
    @classmethod
    def _get_integrated_manager(cls):
        """통합 변수 관리자 싱글톤 반환"""
        if cls._integrated_manager is None and HYBRID_SYSTEM_AVAILABLE:
            try:
                cls._integrated_manager = IntegratedVariableManager()
                print("✅ IntegratedVariableManager 초기화 성공")
            except Exception as e:
                print(f"⚠️ IntegratedVariableManager 초기화 실패: {e}")
                cls._integrated_manager = None
        return cls._integrated_manager
    
    @classmethod
    def _get_compatibility_validator(cls):
        """호환성 검증기 싱글톤 반환"""
        if cls._compatibility_validator is None and HYBRID_SYSTEM_AVAILABLE:
            try:
                cls._compatibility_validator = HybridCompatibilityValidator()
                print("✅ HybridCompatibilityValidator 초기화 성공")
            except Exception as e:
                print(f"⚠️ HybridCompatibilityValidator 초기화 실패: {e}")
                cls._compatibility_validator = None
        return cls._compatibility_validator
    
    @staticmethod
    def get_variable_parameters(var_id: str) -> Dict[str, Any]:
        """변수별 파라미터 정의 반환 (하이브리드 시스템 통합)"""
        # 하이브리드 시스템에서 먼저 찾기
        integrated_manager = VariableDefinitions._get_integrated_manager()
        if integrated_manager:
            try:
                hybrid_params = integrated_manager.get_variable_parameters(var_id)
                if hybrid_params:
                    print(f"✅ 하이브리드 지표 파라미터 로딩: {var_id}")
                    return hybrid_params
            except Exception as e:
                print(f"⚠️ 하이브리드 파라미터 로딩 실패: {var_id}, {e}")
        
        # 기존 하드코딩된 파라미터 (폴백)
        params = {
            "RSI": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "min": 2,
                    "max": 240,
                    "default": 14,
                    "suffix": " 봉",
                    "help": "RSI 계산 기간 (일반적으로 14)"
                },
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "options": ["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"],
                    "default": "포지션 설정 따름",
                    "help": "봉 단위 시간 (전략 기본값 사용 시 무시)"
                }
            },
            "SMA": {
                "period": {
                    "label": "기간", 
                    "type": "int",
                    "min": 1,
                    "max": 240,
                    "default": 20,
                    "suffix": " 봉",
                    "help": "단기: 5,10,20 / 중기: 60,120 / 장기: 200,240"
                },
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "options": ["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"],
                    "default": "포지션 설정 따름",
                    "help": "봉 단위 시간"
                }
            },
            "EMA": {
                "period": {
                    "label": "기간",
                    "type": "int", 
                    "min": 1,
                    "max": 240,
                    "default": 12,
                    "suffix": " 봉",
                    "help": "지수이동평균 계산 기간"
                },
                "exponential_factor": {
                    "label": "지수 계수",
                    "type": "float",
                    "default": 2.0,
                    "placeholder": "2.0",
                    "help": "지수 가중치 (2/(기간+1)이 표준)"
                },
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "options": ["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"],
                    "default": "포지션 설정 따름",
                    "help": "봉 단위 시간"
                }
            },
            "BOLLINGER_BAND": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "min": 10,
                    "max": 240,
                    "default": 20,
                    "suffix": " 봉",
                    "help": "볼린저밴드 계산 기간 (통상 20)"
                },
                "std_dev": {
                    "label": "표준편차 배수",
                    "type": "float", 
                    "default": 2.0,
                    "placeholder": "2.0",
                    "help": "밴드 폭 (1.0=68%, 2.0=95%, 2.5=99%)"
                },
                "band_position": {
                    "label": "밴드 위치",
                    "type": "enum",
                    "options": ["상단", "중앙선", "하단"],
                    "default": "상단",
                    "help": "비교할 볼린저밴드 위치"
                },
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "options": ["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"],
                    "default": "포지션 설정 따름",
                    "help": "봉 단위 시간"
                }
            },
            "MACD": {
                "fast_period": {
                    "label": "빠른선 기간",
                    "type": "int",
                    "min": 5,
                    "max": 30,
                    "default": 12,
                    "suffix": " 봉",
                    "help": "MACD 빠른 이동평균 (12EMA)"
                },
                "slow_period": {
                    "label": "느린선 기간", 
                    "type": "int",
                    "min": 15,
                    "max": 240,
                    "default": 26,
                    "suffix": " 봉",
                    "help": "MACD 느린 이동평균 (26EMA)"
                },
                "signal_period": {
                    "label": "시그널선 기간",
                    "type": "int",
                    "min": 5,
                    "max": 20,
                    "default": 9,
                    "suffix": " 봉",
                    "help": "MACD의 9일 이동평균 (매매신호)"
                },
                "macd_type": {
                    "label": "MACD 종류",
                    "type": "enum",
                    "options": ["MACD선", "시그널선", "히스토그램"],
                    "default": "MACD선",
                    "help": "MACD선: 빠른선-느린선, 시그널선: MACD의 이평, 히스토그램: MACD-시그널"
                }
            },
            "STOCHASTIC": {
                "k_period": {
                    "label": "%K 기간",
                    "type": "int",
                    "min": 5,
                    "max": 50,
                    "default": 14,
                    "suffix": " 봉",
                    "help": "스토캐스틱 %K 계산 기간"
                },
                "d_period": {
                    "label": "%D 기간",
                    "type": "int",
                    "min": 1,
                    "max": 20,
                    "default": 3,
                    "suffix": " 봉",
                    "help": "스토캐스틱 %D 평활화 기간"
                },
                "stoch_type": {
                    "label": "스토캐스틱 종류",
                    "type": "enum",
                    "options": ["%K", "%D"],
                    "default": "%K",
                    "help": "%K: 원시 스토캐스틱, %D: 평활화된 스토캐스틱"
                }
            },
            "ATR": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "min": 5,
                    "max": 100,
                    "default": 14,
                    "suffix": " 봉",
                    "help": "ATR 계산 기간 (일반적으로 14일)"
                },
                "multiplier": {
                    "label": "배수",
                    "type": "float",
                    "min": 0.5,
                    "max": 5.0,
                    "default": 2.0,
                    "step": 0.1,
                    "help": "ATR 값에 곱할 배수 (손절가 계산용)"
                }
            },
            "VOLUME_SMA": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "min": 5,
                    "max": 200,
                    "default": 20,
                    "suffix": " 봉",
                    "help": "거래량 이동평균 계산 기간"
                },
                "volume_type": {
                    "label": "거래량 타입",
                    "type": "enum",
                    "options": ["거래량", "거래대금"],
                    "default": "거래량",
                    "help": "거래량: 코인 개수, 거래대금: KRW 금액"
                }
            },
            "CURRENT_PRICE": {
                "price_type": {
                    "label": "가격 종류",
                    "type": "enum",
                    "options": ["현재가", "매수호가", "매도호가", "중간가"],
                    "default": "현재가",
                    "help": "실시간 거래에서 사용할 가격 기준"
                },
                "backtest_mode": {
                    "label": "백테스팅 모드",
                    "type": "enum",
                    "options": ["실시간(라이브전용)", "종가기준"],
                    "default": "실시간(라이브전용)",
                    "help": "백테스팅 시 해당 타임프레임 종가를 현재가로 사용"
                }
            },
            "PROFIT_PERCENT": {
                "calculation_method": {
                    "label": "계산 방식",
                    "type": "enum",
                    "options": ["미실현", "실현", "전체"],
                    "default": "미실현",
                    "help": "미실현: 현재가 기준, 실현: 매도 완료분, 전체: 포트폴리오 전체"
                },
                "scope": {
                    "label": "범위",
                    "type": "enum",
                    "options": ["현재포지션", "전체포지션", "포트폴리오"],
                    "default": "현재포지션",
                    "help": "수익률 계산 범위"
                },
                "include_fees": {
                    "label": "수수료 포함",
                    "type": "enum",
                    "options": ["포함", "제외"],
                    "default": "포함",
                    "help": "거래 수수료 및 슬리피지 포함 여부"
                }
            },
            "OPEN_PRICE": {
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "options": ["포지션 설정 따름", "1분", "5분", "15분", "30분", "1시간", "4시간", "1일"],
                    "default": "포지션 설정 따름",
                    "help": "시가 기준 봉 단위 (당일 시작가 등)"
                }
            },
            "HIGH_PRICE": {
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "options": ["포지션 설정 따름", "1분", "5분", "15분", "30분", "1시간", "4시간", "1일"],
                    "default": "포지션 설정 따름",
                    "help": "고가 기준 봉 단위"
                }
            },
            "LOW_PRICE": {
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "options": ["포지션 설정 따름", "1분", "5분", "15분", "30분", "1시간", "4시간", "1일"],
                    "default": "포지션 설정 따름",
                    "help": "저가 기준 봉 단위"
                }
            },
            "VOLUME": {
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "options": ["포지션 설정 따름", "1분", "5분", "15분", "30분", "1시간", "4시간", "1일"],
                    "default": "포지션 설정 따름",
                    "help": "거래량 기준 봉 단위"
                },
                "volume_type": {
                    "label": "거래량 종류",
                    "type": "enum",
                    "options": ["거래량", "거래대금", "상대거래량"],
                    "default": "거래량",
                    "help": "거래량: 코인수량, 거래대금: 원화금액, 상대거래량: 평균대비 비율"
                }
            },
            "TOTAL_BALANCE": {
                "currency": {
                    "label": "표시 통화",
                    "type": "enum",
                    "options": ["KRW", "USD", "BTC"],
                    "default": "KRW",
                    "help": "총 자산 표시 기준 통화"
                },
                "scope": {
                    "label": "범위",
                    "type": "enum",
                    "options": ["포지션제한", "계좌전체"],
                    "default": "포지션제한",
                    "help": "포지션 할당 자본 vs 전체 계좌"
                }
            },
            "CASH_BALANCE": {
                "currency": {
                    "label": "표시 통화",
                    "type": "enum",
                    "options": ["KRW", "USD", "BTC"],
                    "default": "KRW",
                    "help": "현금 잔고 표시 기준 통화"
                },
                "scope": {
                    "label": "범위",
                    "type": "enum",
                    "options": ["포지션제한", "계좌전체"],
                    "default": "포지션제한",
                    "help": "포지션 할당 vs 전체 사용가능 현금"
                }
            },
            "COIN_BALANCE": {
                "coin_unit": {
                    "label": "표시 단위",
                    "type": "enum",
                    "options": ["코인수량", "원화가치", "USD가치"],
                    "default": "코인수량",
                    "help": "코인 보유량 표시 방식"
                },
                "scope": {
                    "label": "범위",
                    "type": "enum",
                    "options": ["현재코인", "전체코인"],
                    "default": "현재코인",
                    "help": "현재 거래중인 코인 vs 보유한 모든 코인"
                }
            },
            "PROFIT_AMOUNT": {
                "currency": {
                    "label": "표시 통화",
                    "type": "enum",
                    "options": ["KRW", "USD", "BTC"],
                    "default": "KRW",
                    "help": "수익 금액 표시 통화"
                },
                "calculation_method": {
                    "label": "계산 방식",
                    "type": "enum",
                    "options": ["미실현", "실현", "전체"],
                    "default": "미실현",
                    "help": "미실현: 현재가기준, 실현: 매도완료, 전체: 누적"
                },
                "include_fees": {
                    "label": "수수료 포함",
                    "type": "enum",
                    "options": ["포함", "제외"],
                    "default": "포함",
                    "help": "거래 수수료 및 슬리피지 포함 여부"
                }
            },
            "POSITION_SIZE": {
                "unit_type": {
                    "label": "단위 형태",
                    "type": "enum",
                    "options": ["수량", "금액", "비율"],
                    "default": "수량",
                    "help": "수량: 코인개수, 금액: 원화가치, 비율: 포트폴리오대비%"
                }
            },
            "AVG_BUY_PRICE": {
                "display_currency": {
                    "label": "표시 통화",
                    "type": "enum",
                    "options": ["원화", "USD", "코인단위"],
                    "default": "원화",
                    "help": "평균 매수가 표시 통화 (수수료 포함된 평단가)"
                }
            }
        }
        
        return params.get(var_id, {})
    
    @staticmethod
    def get_variable_descriptions() -> Dict[str, str]:
        """변수별 설명 반환"""
        return {
            "RSI": "RSI(상대강도지수): 0~100 범위의 모멘텀 지표. 70 이상은 과매수, 30 이하는 과매도",
            "SMA": "단순이동평균: 일정 기간의 가격 평균. 추세 방향성 판단에 사용",
            "EMA": "지수이동평균: 최근 가격에 더 큰 가중치. 빠른 신호",
            "BOLLINGER_BAND": "볼린저밴드: 표준편차 기반 변동성 지표. 상단/중앙/하단 활용",
            "STOCHASTIC": "스토캐스틱: 0~100 범위의 모멘텀 오실레이터. %K는 원시값, %D는 평활화 값. 80 이상 과매수, 20 이하 과매도",
            "ATR": "ATR(평균진실범위): 변동성 측정 지표. 손절가/익절가 설정, 포지션 사이징에 활용",
            "VOLUME_SMA": "거래량 이동평균: 평균 거래량 대비 현재 거래량 비교. 거래량 급증/감소 확인",
            "MACD": ("MACD(이동평균 수렴확산): 단기(12일)와 장기(26일) 지수이동평균의 차이로 추세 강도와 방향을 측정. "
                     "MACD선(빠른선-느린선), 시그널선(MACD의 9일 지수이동평균), 히스토그램(MACD-시그널)으로 구성. "
                     "히스토그램이 0선 상향돌파시 골든크로스(상승신호), 하향돌파시 데드크로스(하락신호). "
                     "모든 계산은 종가 기준으로 캔들 마감 후 확정됨."),
            "CURRENT_PRICE": "현재가: 실시간 시장 가격",
            "PROFIT_PERCENT": "현재 수익률: 매수가 대비 수익률(%)"
        }
    
    @staticmethod
    def get_variable_placeholders() -> Dict[str, Dict[str, str]]:
        """변수별 플레이스홀더 반환"""
        return {
            "RSI": {
                "target": "예: 70 (과매수), 30 (과매도), 50 (중립)",
                "name": "예: RSI 과매수 신호",
                "description": "RSI가 70을 넘어 과매수 구간 진입 시 매도 신호"
            },
            "SMA": {
                "target": "예: 현재가 기준 또는 다른 SMA(골든크로스용)",
                "name": "예: 20일선 돌파",
                "description": "가격이 20일 이동평균선 상향 돌파 시 상승 추세 확인"
            },
            "CURRENT_PRICE": {
                "target": "예: 50000 (목표가), 비율: 1.05 (5%상승)",
                "name": "예: 목표가 도달",
                "description": "목표 가격 도달 시 수익 실현"
            },
            "MACD": {
                "target": "예: 0 (히스토그램 0선), 0.5 (MACD선 값), -0.3 (시그널선 값)",
                "name": "예: MACD 골든크로스",
                "description": "MACD 히스토그램이 0선 상향돌파로 상승 추세 시작 신호"
            },
            "PROFIT_PERCENT": {
                "target": "예: 5 (익절), -3 (손절), 10 (목표수익)",
                "name": "예: 수익률 5% 달성",
                "description": "목표 수익률 달성 시 포지션 정리"
            }
        }
    
    @staticmethod
    def get_category_variables() -> Dict[str, list]:
        """카테고리별 변수 목록 반환 (하이브리드 시스템 통합)"""
        # 하이브리드 시스템이 사용 가능한 경우 통합된 목록 반환
        integrated_manager = VariableDefinitions._get_integrated_manager()
        if integrated_manager:
            try:
                integrated_vars = integrated_manager.get_category_variables()
                print(f"✅ 통합 변수 목록 로딩: {len(integrated_vars)} 카테고리")
                return integrated_vars
            except Exception as e:
                print(f"⚠️ 통합 변수 목록 로딩 실패, 기존 방식 사용: {e}")
        
        # 표준화 문서 기반 용도별 카테고리 (이중 카테고리 시스템)
        return {
            "trend": [
                ("SMA", "단순이동평균"),
                ("EMA", "지수이동평균"),
            ],
            "momentum": [
                ("RSI", "RSI 지표"),
                ("STOCHASTIC", "스토캐스틱"),
                ("MACD", "MACD 지표")
            ],
            "volatility": [
                ("BOLLINGER_BAND", "볼린저밴드"),
                ("ATR", "ATR(평균진실범위)")
            ],
            "volume": [
                ("VOLUME", "거래량"),
                ("VOLUME_SMA", "거래량 이동평균")
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
                ("PROFIT_PERCENT", "현재 수익률(%)"),
                ("PROFIT_AMOUNT", "현재 수익 금액"),
                ("POSITION_SIZE", "포지션 크기"),
                ("AVG_BUY_PRICE", "평균 매수가")
            ]
        }
    
    @staticmethod
    def get_variable_category(variable_id: str) -> str:
        """변수 ID로부터 카테고리 찾기 (하이브리드 시스템 통합)"""
        # 하이브리드 시스템에서 먼저 찾기
        integrated_manager = VariableDefinitions._get_integrated_manager()
        if integrated_manager and integrated_manager.is_hybrid_indicator(variable_id):
            try:
                # 새 지표의 카테고리를 어댑터에서 가져오기
                category = integrated_manager.adapter._get_indicator_category(variable_id)
                print(f"✅ 하이브리드 지표 카테고리: {variable_id} → {category}")
                return category
            except Exception as e:
                print(f"⚠️ 하이브리드 카테고리 조회 실패: {variable_id}, {e}")
        
        # 기존 방식으로 찾기
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
            # 로컬 통합 호환성 검증기 사용
            if COMPATIBILITY_VALIDATOR_AVAILABLE:
                from .compatibility_validator import CompatibilityValidator
                validator = CompatibilityValidator()
                is_compatible, score, reason = validator.validate_compatibility(var1_id, var2_id)
                # reason이 dict인 경우 문자열로 변환
                reason_str = str(reason) if isinstance(reason, dict) else reason
                print(f"✅ 통합 호환성 검증: {var1_id} ↔ {var2_id} = {is_compatible} ({score}%) - {reason_str}")
                return is_compatible, reason_str
            else:
                # 폴백: 기존 방식 시도
                current_dir = os.path.dirname(os.path.abspath(__file__))
                compatibility_validator_path = os.path.join(
                    current_dir, '..', '..', '..', '..', '..', 'utils', 'trading_variables'
                )
                if compatibility_validator_path not in sys.path:
                    sys.path.insert(0, compatibility_validator_path)
                
                from compatibility_validator import check_compatibility
                is_compatible, reason = check_compatibility(var1_id, var2_id)
                print(f"✅ 백업 호환성 검증: {var1_id} ↔ {var2_id} = {is_compatible} ({reason})")
                return is_compatible, reason
            
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
        """사용 가능한 모든 지표 목록 반환 (하이브리드 시스템 전용)"""
        integrated_manager = VariableDefinitions._get_integrated_manager()
        if integrated_manager:
            try:
                indicators = integrated_manager.adapter.indicator_calculator.get_available_indicators()
                print(f"✅ 하이브리드 지표 목록: {len(indicators.get('core', []))} 핵심 + {len(indicators.get('custom', []))} 사용자정의")
                return indicators
            except Exception as e:
                print(f"⚠️ 하이브리드 지표 목록 조회 실패: {e}")
        
        return {"core": [], "custom": []}
