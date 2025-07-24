#!/usr/bin/env python3
"""
변수 정의 모듈 - 모든 트레이딩 변수의 파라미터 정의
"""

from typing import Dict, Any

class VariableDefinitions:
    """트레이딩 변수들의 파라미터 정의를 관리하는 클래스"""
    
    @staticmethod
    def get_variable_parameters(var_id: str) -> Dict[str, Any]:
        """변수별 파라미터 정의 반환"""
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
            "MACD": "MACD: 이동평균 수렴확산. 추세 변화 감지",
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
            "PROFIT_PERCENT": {
                "target": "예: 5 (익절), -3 (손절), 10 (목표수익)",
                "name": "예: 수익률 5% 달성",
                "description": "목표 수익률 달성 시 포지션 정리"
            }
        }
    
    @staticmethod
    def get_category_variables() -> Dict[str, list]:
        """카테고리별 변수 목록 반환"""
        return {
            "indicator": [
                ("RSI", "RSI 지표"),
                ("SMA", "단순이동평균"),
                ("EMA", "지수이동평균"),
                ("BOLLINGER_BAND", "볼린저밴드"),
                ("MACD", "MACD 지표")
            ],
            "price": [
                ("CURRENT_PRICE", "현재가"),
                ("OPEN_PRICE", "시가"),
                ("HIGH_PRICE", "고가"),
                ("LOW_PRICE", "저가"),
                ("VOLUME", "거래량")
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
