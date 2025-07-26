"""
지표 계산 엔진 - 하이브리드 접근법
코드 기반 핵심 지표 + DB 기반 사용자 정의 지표
"""

import pandas as pd
import numpy as np
import sqlite3
import json
import logging
from typing import Dict, Any, List, Optional, Union, Callable
from pathlib import Path
import ast
import operator
import math


class IndicatorCalculator:
    """
    통합 지표 계산 엔진
    
    하이브리드 접근법:
    1. 핵심 지표: 코드로 구현 (성능 중시)
    2. 사용자 정의: DB 기반 (유연성 중시)
    """
    
    def __init__(self, db_path: str = "../../data/app_settings.sqlite3"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # 핵심 지표들 (코드 기반 - 성능 중시)
        self._core_indicators = {
            'SMA': self._calculate_sma,
            'EMA': self._calculate_ema,
            'RSI': self._calculate_rsi,
            'MACD': self._calculate_macd,
            'BOLLINGER_BANDS': self._calculate_bollinger_bands,
            'STOCHASTIC': self._calculate_stochastic,
            'ATR': self._calculate_atr,
            'VOLUME_SMA': self._calculate_volume_sma,
        }
        
        # 수식 평가용 안전한 연산자들
        self._safe_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        
        # 안전한 함수들
        self._safe_functions = {
            'abs': abs,
            'max': max,
            'min': min,
            'round': round,
            'sqrt': math.sqrt,
            'log': math.log,
            'exp': math.exp,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
        }
        
        self._init_custom_indicators_table()
    
    def _init_custom_indicators_table(self):
        """사용자 정의 지표 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 기존 테이블 존재 여부 확인
                cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='custom_indicators'
                """)
                table_exists = cursor.fetchone() is not None
                
                if table_exists:
                    # 기존 테이블의 스키마 확인
                    cursor = conn.execute("PRAGMA table_info(custom_indicators)")
                    existing_columns = [row[1] for row in cursor.fetchall()]
                    self.logger.info(f"기존 custom_indicators 테이블 발견, 컬럼: {existing_columns}")
                else:
                    # 새 테이블 생성
                    conn.execute("""
                    CREATE TABLE custom_indicators (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        name_ko TEXT NOT NULL,
                        description TEXT,
                        formula TEXT NOT NULL,
                        parameters TEXT,  -- JSON
                        category TEXT DEFAULT 'custom',
                        created_by TEXT DEFAULT 'user',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                    """)
                    self.logger.info("새 custom_indicators 테이블 생성됨")
                
                # 샘플 데이터가 없으면 추가
                cursor = conn.execute("SELECT COUNT(*) FROM custom_indicators")
                count = cursor.fetchone()[0]
                
                if count == 0:
                    # 샘플 사용자 정의 지표 추가
                    sample_indicators = [
                        ('PRICE_MOMENTUM', '가격 모멘텀', '현재가와 N일 전 가격의 비율',
                         '현재가와 N일 전 가격의 비율을 계산', 'close / SMA(close, {period})', '{"period": 20}', 'custom'),
                        ('VOLUME_PRICE_TREND', '거래량-가격 추세', '거래량과 가격 변화의 상관관계',
                         '거래량과 가격 변화의 상관관계를 나타내는 지표', '(close - SMA(close, {period})) * volume', '{"period": 14}', 'custom'),
                        ('CUSTOM_RSI_SMA', 'RSI 기반 이동평균', 'RSI에 이동평균을 적용',
                         'RSI 값에 이동평균을 적용한 부드러운 지표', 'SMA(RSI(close, {rsi_period}), {sma_period})', '{"rsi_period": 14, "sma_period": 5}', 'custom')
                    ]
                    
                    for indicator in sample_indicators:
                        conn.execute("""
                        INSERT OR IGNORE INTO custom_indicators 
                        (id, name, name_ko, description, formula, parameters, category)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, indicator)
                    
                    self.logger.info(f"샘플 지표 {len(sample_indicators)}개 추가됨")
                else:
                    self.logger.info(f"기존 지표 데이터 {count}개 발견됨, 샘플 데이터 추가 생략")
                
        except Exception as e:
            self.logger.error(f"사용자 정의 지표 테이블 초기화 실패: {e}")
            # 상세한 오류 정보 로깅
            import traceback
            self.logger.error(f"상세 오류:\n{traceback.format_exc()}")
    
    def calculate(self, indicator_id: str, data: pd.DataFrame, **params) -> Union[pd.Series, pd.DataFrame]:
        """
        지표 계산 메인 함수
        
        Args:
            indicator_id: 지표 ID ('SMA', 'RSI', 'CUSTOM_XXX' 등)
            data: OHLCV 데이터
            **params: 지표 매개변수
            
        Returns:
            계산된 지표 데이터
        """
        try:
            # 1. 핵심 지표 (코드 기반)
            if indicator_id in self._core_indicators:
                return self._core_indicators[indicator_id](data, **params)
            
            # 2. 사용자 정의 지표 (DB 기반)
            return self._calculate_custom_indicator(indicator_id, data, **params)
            
        except Exception as e:
            self.logger.error(f"지표 계산 실패: {indicator_id}, {e}")
            return pd.Series(dtype=float)
    
    def get_available_indicators(self) -> Dict[str, List[Dict]]:
        """사용 가능한 모든 지표 목록 반환"""
        indicators = {
            'core': [],
            'custom': []
        }
        
        # 핵심 지표
        for indicator_id in self._core_indicators.keys():
            indicators['core'].append({
                'id': indicator_id,
                'name': indicator_id,
                'type': 'core',
                'performance': 'high'
            })
        
        # 사용자 정의 지표
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                SELECT id, name, name_ko, description, formula 
                FROM custom_indicators 
                WHERE is_active = 1
                """)
                
                for row in cursor.fetchall():
                    indicators['custom'].append({
                        'id': row[0],
                        'name': row[1],
                        'name_ko': row[2],
                        'description': row[3],
                        'formula': row[4],
                        'type': 'custom',
                        'performance': 'medium'
                    })
        except Exception as e:
            self.logger.error(f"사용자 정의 지표 조회 실패: {e}")
        
        return indicators
    
    def add_custom_indicator(self, indicator_id: str, name: str, name_ko: str, 
                           formula: str, description: str = "", **params) -> bool:
        """사용자 정의 지표 추가"""
        try:
            # 수식 유효성 검증
            if not self._validate_formula(formula):
                self.logger.error(f"유효하지 않은 수식: {formula}")
                return False
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                INSERT OR REPLACE INTO custom_indicators 
                (id, name, name_ko, description, formula, parameters) 
                VALUES (?, ?, ?, ?, ?, ?)
                """, (indicator_id, name, name_ko, description, formula, json.dumps(params)))
                
            self.logger.info(f"사용자 정의 지표 추가됨: {indicator_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"사용자 정의 지표 추가 실패: {e}")
            return False
    
    # ========== 핵심 지표 구현 (코드 기반) ==========
    
    def _calculate_sma(self, data: pd.DataFrame, period: int = 20, column: str = 'close') -> pd.Series:
        """단순 이동 평균"""
        return data[column].rolling(window=period).mean()
    
    def _calculate_ema(self, data: pd.DataFrame, period: int = 20, column: str = 'close') -> pd.Series:
        """지수 이동 평균"""
        return data[column].ewm(span=period, adjust=False).mean()
    
    def _calculate_rsi(self, data: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
        """RSI 계산"""
        delta = data[column].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, data: pd.DataFrame, fast: int = 12, slow: int = 26, 
                       signal: int = 9, column: str = 'close') -> pd.DataFrame:
        """MACD 계산"""
        fast_ema = data[column].ewm(span=fast).mean()
        slow_ema = data[column].ewm(span=slow).mean()
        
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        })
    
    def _calculate_bollinger_bands(self, data: pd.DataFrame, period: int = 20, 
                                  std_dev: float = 2.0, column: str = 'close') -> pd.DataFrame:
        """볼린저 밴드"""
        sma = data[column].rolling(window=period).mean()
        std = data[column].rolling(window=period).std()
        
        return pd.DataFrame({
            'upper': sma + (std * std_dev),
            'middle': sma,
            'lower': sma - (std * std_dev)
        })
    
    def _calculate_stochastic(self, data: pd.DataFrame, k_period: int = 14, 
                             d_period: int = 3) -> pd.DataFrame:
        """스토캐스틱"""
        low_min = data['low'].rolling(window=k_period).min()
        high_max = data['high'].rolling(window=k_period).max()
        
        k_percent = 100 * ((data['close'] - low_min) / (high_max - low_min))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return pd.DataFrame({
            'k': k_percent,
            'd': d_percent
        })
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average True Range"""
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(window=period).mean()
    
    def _calculate_volume_sma(self, data: pd.DataFrame, period: int = 20) -> pd.Series:
        """거래량 이동 평균"""
        return data['volume'].rolling(window=period).mean()
    
    # ========== 사용자 정의 지표 (DB 기반) ==========
    
    def _calculate_custom_indicator(self, indicator_id: str, data: pd.DataFrame, **params) -> pd.Series:
        """사용자 정의 지표 계산"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                SELECT formula, parameters FROM custom_indicators 
                WHERE id = ? AND is_active = 1
                """, (indicator_id,))
                
                result = cursor.fetchone()
                if not result:
                    raise ValueError(f"지표를 찾을 수 없습니다: {indicator_id}")
                
                formula, stored_params = result
                
                # 저장된 파라미터와 전달된 파라미터 병합
                if stored_params:
                    default_params = json.loads(stored_params)
                    default_params.update(params)
                    params = default_params
                
                # 수식 평가
                return self._evaluate_formula(formula, data, params)
                
        except Exception as e:
            self.logger.error(f"사용자 정의 지표 계산 실패: {indicator_id}, {e}")
            return pd.Series(dtype=float)
    
    def _evaluate_formula(self, formula: str, data: pd.DataFrame, params: Dict) -> pd.Series:
        """수식 평가 (안전한 방식)"""
        try:
            # 파라미터 치환
            formatted_formula = formula.format(**params)
            
            # 기본 변수 설정
            variables = {
                'close': data['close'],
                'open': data['open'],
                'high': data['high'],
                'low': data['low'],
                'volume': data['volume'],
                'data': data  # 전체 데이터프레임도 추가
            }
            
            # 핵심 지표 함수들을 변수로 추가
            def make_indicator_func(func):
                def wrapper(*args, **kwargs):
                    return func(data, *args, **kwargs)
                return wrapper
            
            for indicator_name, func in self._core_indicators.items():
                variables[indicator_name] = make_indicator_func(func)
            
            # 수식 파싱 및 평가 (보안 고려)
            return self._safe_eval(formatted_formula, variables)
            
        except Exception as e:
            self.logger.error(f"수식 평가 실패: {formula}, {e}")
            return pd.Series(dtype=float)
    
    def _safe_eval(self, expression: str, variables: Dict) -> pd.Series:
        """안전한 수식 평가 - 개선된 버전"""
        try:
            # 먼저 핵심 지표 함수 호출을 처리
            processed_expression = self._preprocess_indicators(expression, variables)
            
            # 위험한 함수들 제거
            safe_globals = {
                '__builtins__': {},
                **self._safe_functions,
                **{k: v for k, v in variables.items() if not callable(v)}
            }
            
            result = eval(processed_expression, safe_globals)
            
            if isinstance(result, pd.Series):
                return result
            else:
                return pd.Series([result] * len(variables['close']))
                
        except Exception as e:
            self.logger.error(f"안전한 평가 실패: {expression}, {e}")
            return pd.Series(dtype=float)
    
    def _preprocess_indicators(self, expression: str, variables: Dict) -> str:
        """지표 함수 호출을 미리 계산해서 변수로 치환"""
        import re
        
        # 지표 함수 패턴 찾기 (예: SMA(close, 20), RSI(close, 14) 등)
        indicator_pattern = r'(\w+)\(([^)]+)\)'
        
        def replace_indicator(match):
            func_name = match.group(1)
            args_str = match.group(2)
            
            if func_name in self._core_indicators:
                try:
                    # 인수 파싱
                    args = [arg.strip() for arg in args_str.split(',')]
                    
                    # 첫 번째 인수가 데이터 컬럼인지 확인
                    if args[0] in ['close', 'open', 'high', 'low', 'volume']:
                        column = args[0]
                        
                        # 나머지 인수들을 파라미터로 변환
                        params = {}
                        if len(args) > 1:
                            if func_name in ['SMA', 'EMA', 'RSI']:
                                params['period'] = int(args[1])
                            elif func_name == 'MACD':
                                if len(args) >= 4:
                                    params = {'fast': int(args[1]), 'slow': int(args[2]), 'signal': int(args[3])}
                                else:
                                    params = {'fast': 12, 'slow': 26, 'signal': 9}
                            # 다른 지표들에 대한 파라미터 처리 추가 가능
                        
                        # 지표 계산
                        if 'data' in variables:
                            data = variables['data']
                        else:
                            # 기본 데이터 재구성
                            data = pd.DataFrame({
                                'close': variables['close'],
                                'open': variables['open'],
                                'high': variables['high'],
                                'low': variables['low'],
                                'volume': variables['volume']
                            })
                        
                        result = self._core_indicators[func_name](data, column=column, **params)
                        
                        # 결과를 변수에 저장
                        var_name = f"_{func_name}_{column}_{hash(args_str) % 10000}"
                        variables[var_name] = result
                        
                        return var_name
                    
                except Exception as e:
                    self.logger.error(f"지표 전처리 실패: {func_name}({args_str}), {e}")
            
            return match.group(0)  # 원본 반환
        
        # 모든 지표 함수 호출을 변수로 치환
        processed = re.sub(indicator_pattern, replace_indicator, expression)
        return processed
    
    def _validate_formula(self, formula: str) -> bool:
        """수식 유효성 검증"""
        try:
            # 기본적인 구문 검증
            ast.parse(formula)
            
            # 위험한 키워드 검사
            dangerous_keywords = ['import', 'exec', 'eval', 'open', 'file', '__']
            for keyword in dangerous_keywords:
                if keyword in formula.lower():
                    return False
            
            return True
            
        except:
            return False


# 사용 예시
if __name__ == "__main__":
    # 샘플 데이터 생성
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    sample_data = pd.DataFrame({
        'close': np.random.randn(100).cumsum() + 100,
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 105,
        'low': np.random.randn(100).cumsum() + 95,
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    # 계산기 생성
    calc = IndicatorCalculator()
    
    # 핵심 지표 계산 (코드 기반 - 빠름)
    sma_20 = calc.calculate('SMA', sample_data, period=20)
    rsi_14 = calc.calculate('RSI', sample_data, period=14)
    
    print("📊 핵심 지표 계산 완료")
    print(f"SMA(20): {sma_20.tail(3).values}")
    print(f"RSI(14): {rsi_14.tail(3).values}")
    
    # 사용자 정의 지표 추가
    calc.add_custom_indicator(
        'MOMENTUM_RATIO',
        '모멘텀 비율',
        '모멘텀 비율 지표',
        'close / SMA(close, {period})',
        period=20
    )
    
    # 사용자 정의 지표 계산 (DB 기반 - 유연함)
    momentum = calc.calculate('MOMENTUM_RATIO', sample_data)
    print(f"사용자 정의 모멘텀: {momentum.tail(3).values}")
    
    # 사용 가능한 모든 지표 조회
    all_indicators = calc.get_available_indicators()
    print(f"\n📋 사용 가능한 지표:")
    print(f"핵심 지표: {len(all_indicators['core'])}개")
    print(f"사용자 정의: {len(all_indicators['custom'])}개")
