"""
실제 데이터 기반 시뮬레이션 엔진 - UI 연동 버전
upbit_auto_trading 패키지 내에서 사용하는 안전한 버전
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
import os

# 전역 DB 매니저 임포트 - 비활성화
try:
    # from upbit_auto_trading.utils.global_db_manager import get_db_connection
    # USE_GLOBAL_MANAGER = True
    USE_GLOBAL_MANAGER = False  # 강제로 비활성화
    print("⚠️ 전역 DB 매니저 비활성화 - 직접 SQLite 연결 사용")
except ImportError:
    print("⚠️ 전역 DB 매니저를 사용할 수 없습니다. 기존 방식을 사용합니다.")
    USE_GLOBAL_MANAGER = False

class RealDataSimulationEngine:
    """UI용 실제 데이터 기반 시뮬레이션 엔진"""
    
    def __init__(self, data_db_path: str = "data/sampled_market_data.sqlite3"):
        """
        실제 데이터 기반 시뮬레이션 엔진 초기화
        
        Args:
            data_db_path: 시장 데이터 DB 경로 (전역 매니저 사용시 무시됨)
        """
        # 트리거 빌더 전용 샘플 데이터 경로 (같은 engines/data 폴더)
        self.data_db_path = os.path.join(os.path.dirname(__file__), "data", "sampled_market_data.sqlite3")
        self.use_global_manager = USE_GLOBAL_MANAGER
        self.cache_data = None
        self.cache_indicators = None
        
        # 시나리오별 데이터 세그먼트 정의
        self.scenario_segments = self._define_scenario_segments()
        
    def _get_connection(self):
        """DB 연결 반환 - 직접 SQLite 연결만 사용"""
        return sqlite3.connect(self.data_db_path)
        
    def load_market_data(self, limit: int = 500) -> Optional[pd.DataFrame]:
        """실제 KRW-BTC 시장 데이터 로드"""
        conn = None
        try:
            if not self.use_global_manager and not os.path.exists(self.data_db_path):
                logging.warning(f"Market data DB not found: {self.data_db_path}")
                return None
                
            conn = self._get_connection()
            
            # 일봉 데이터 로드 (기본 500일, 필요시 확장 가능)
            query = """
            SELECT 
                timestamp,
                open,
                high,
                low,
                close,
                volume
            FROM market_data 
            WHERE symbol = 'KRW-BTC' AND timeframe = '1d' 
            ORDER BY timestamp DESC 
            LIMIT ?
            """
            
            df = pd.read_sql(query, conn, params=(limit,))
            
            if df.empty:
                logging.warning("No market data found")
                return None
            
            # 데이터 정렬 (오래된 것부터)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # 날짜 컬럼을 인덱스로 설정
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
            
            # 숫자형 변환
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            logging.info(f"Market data loaded: {len(df)} records")
            self.cache_data = df
            return df
            
        except Exception as e:
            logging.error(f"Failed to load market data: {e}")
            return None
        finally:
            # 데이터베이스 연결 안전하게 닫기
            if conn is not None:
                try:
                    conn.close()
                except:
                    pass  # 이미 닫혔거나 에러 무시
    
    def _define_scenario_segments(self) -> Dict[str, Dict[str, Any]]:
        """시나리오별 데이터 세그먼트 정의 - 실제 시장 패턴 기반"""
        return {
            '급등': {
                'date_range': ('2025-04-16', '2025-07-21'),
                'description': '급등 구간 (+31.39%, 121M→160M)',
                'data_offset': 2760
            },
            '상승 추세': {
                'date_range': ('2023-07-16', '2023-10-23'),
                'description': '상승 추세 구간 (+13.47%, 39M→44M)',
                'data_offset': 2120
            },
            '횡보': {
                'date_range': ('2023-04-27', '2023-08-04'),
                'description': '횡보 구간 (-1.95%, 39M→38M)',
                'data_offset': 2040
            },
            '하락 추세': {
                'date_range': ('2023-07-06', '2023-10-13'),
                'description': '하락 추세 구간 (-7.26%, 40M→37M)',
                'data_offset': 2110
            },
            '급락': {
                'date_range': ('2018-08-01', '2018-11-08'),
                'description': '급락 구간 (-16.55%, 8.7M→7.3M)',
                'data_offset': 310
            }
        }
    
    def load_scenario_data(self, scenario: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """시나리오별 데이터 로드"""
        conn = None
        try:
            if scenario not in self.scenario_segments:
                logging.warning(f"Unknown scenario: {scenario}, using default data")
                return self.load_market_data(limit)
            
            segment_info = self.scenario_segments[scenario]
            
            conn = self._get_connection()
            
            # 시나리오별 날짜 범위 기반 데이터 쿼리 (더 정확함)
            start_date, end_date = segment_info['date_range']
            
            query = """
            SELECT 
                timestamp,
                open,
                high, 
                low,
                close,
                volume
            FROM market_data 
            WHERE symbol = 'KRW-BTC' AND timeframe = '1d'
            AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp ASC 
            LIMIT ?
            """
            
            df = pd.read_sql_query(query, conn, params=[start_date, end_date, limit])
            
            if df.empty:
                logging.warning(f"No data found for scenario: {scenario}")
                return self.load_market_data(limit)
            
            # 데이터 전처리
            df = df.sort_values('timestamp').reset_index(drop=True)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
            
            # 숫자형 변환
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 기술적 지표 계산
            df = self.calculate_technical_indicators(df)
            
            logging.info(f"Scenario data loaded: {scenario} ({len(df)} records)")
            return df
            
        except Exception as e:
            logging.error(f"Failed to load scenario data for {scenario}: {e}")
            return self.load_market_data(limit)
        finally:
            # 데이터베이스 연결 안전하게 닫기
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass  # 이미 닫혔거나 에러 무시
    
    def get_available_scenarios(self) -> List[str]:
        """사용 가능한 시나리오 목록 반환"""
        return list(self.scenario_segments.keys())
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 계산"""
        try:
            if df is None or df.empty:
                return df
            
            # RSI 계산
            def calculate_rsi(prices, period=14):
                delta = prices.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                return rsi
            
            # 이동평균 계산
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_60'] = df['close'].rolling(window=60).mean()
            
            # RSI 계산
            df['rsi'] = calculate_rsi(df['close'])
            
            # 변동성 계산 (30일)
            df['volatility_30d'] = df['close'].pct_change().rolling(window=30).std() * 100
            
            # 수익률 계산
            df['return_7d'] = df['close'].pct_change(7) * 100
            df['return_30d'] = df['close'].pct_change(30) * 100
            
            self.cache_indicators = df
            logging.info("Technical indicators calculated")
            return df
            
        except Exception as e:
            logging.error(f"Failed to calculate indicators: {e}")
            return df
    
    def get_scenario_data(self, scenario: str, length: int = 50) -> Dict[str, Any]:
        """시나리오에 맞는 실제 데이터 추출 (조건 불일치시 데이터 범위 확장)"""
        try:
            # 단계별로 데이터 범위를 확장하며 조건에 맞는 구간 찾기
            search_limits = [500, 1000, 2000, 5000]  # 검색 범위 단계적 확장
            
            for limit in search_limits:
                logging.info(f"Searching in {limit} records for scenario: {scenario}")
                
                # 데이터 로드
                df = self.load_market_data(limit)
                if df is None or df.empty:
                    continue
                    
                # 기술적 지표 계산
                df = self.calculate_technical_indicators(df)
                if df is None or df.empty:
                    continue

                # 시나리오별 데이터 필터링 로직
                scenario_conditions = {
                    "상승 추세": lambda x: x['return_30d'] > 5,
                    "하락 추세": lambda x: x['return_30d'] < -5,
                    "급등": lambda x: x['return_7d'] > 15,
                    "급락": lambda x: x['return_7d'] < -15,
                    "횡보": lambda x: abs(x['return_30d']) < 3,
                    "이동평균 교차": lambda x: True  # 모든 데이터에서 교차 확인
                }

                condition = scenario_conditions.get(scenario)
                if condition:
                    # 조건에 맞는 기간 찾기
                    valid_periods = []
                    for i in range(len(df) - length):
                        segment = df.iloc[i:i+length]
                        if not segment.empty and condition(segment.iloc[-1]):
                            valid_periods.append(i)
                    
                    # 조건에 맞는 구간을 찾았으면 반환
                    if valid_periods:
                        start_idx = np.random.choice(valid_periods)
                        segment = df.iloc[start_idx:start_idx+length]
                        
                        last_row = segment.iloc[-1]
                        
                        if '교차' in scenario:
                            current_value = last_row['sma_20'] - last_row['sma_60']
                        elif 'rsi' in scenario.lower():
                            current_value = last_row['rsi']
                        else:
                            current_value = last_row['close']
                        
                        logging.info(f"Found matching data in {limit} records")
                        return {
                            'current_value': float(current_value) if not pd.isna(current_value) else 50.0,
                            'price_data': segment['close'].tolist(),
                            'scenario': scenario,
                            'data_source': f'real_market_data_{limit}_records',
                            'period': f"{segment.index[0].strftime('%Y-%m-%d')} ~ {segment.index[-1].strftime('%Y-%m-%d')}",
                            'base_value': float(segment['close'].iloc[0]),
                            'change_percent': float((segment['close'].iloc[-1] / segment['close'].iloc[0] - 1) * 100)
                        }
            
            # 모든 범위에서 조건에 맞는 데이터를 찾지 못한 경우 최근 데이터 사용
            logging.warning(f"No matching data found for scenario: {scenario}, using recent data")
            df = self.load_market_data(500)
            if df is not None:
                df = self.calculate_technical_indicators(df)
                segment = df.tail(length)
                
                if not segment.empty:
                    last_row = segment.iloc[-1]
                    
                    if '교차' in scenario:
                        current_value = last_row['sma_20'] - last_row['sma_60']
                    elif 'rsi' in scenario.lower():
                        current_value = last_row['rsi']
                    else:
                        current_value = last_row['close']
                    
                    return {
                        'current_value': float(current_value) if not pd.isna(current_value) else 50.0,
                        'price_data': segment['close'].tolist(),
                        'scenario': scenario,
                        'data_source': 'recent_market_data_fallback',
                        'period': f"{segment.index[0].strftime('%Y-%m-%d')} ~ {segment.index[-1].strftime('%Y-%m-%d')}",
                        'base_value': float(segment['close'].iloc[0]),
                        'change_percent': float((segment['close'].iloc[-1] / segment['close'].iloc[0] - 1) * 100)
                    }
            
        except Exception as e:
            logging.error(f"Failed to get scenario data: {e}")
            
        # 실패 시 폴백 데이터 반환
        return self._generate_fallback_data(scenario, length)
    
    def _generate_fallback_data(self, scenario: str, length: int = 50) -> Dict[str, Any]:
        """실제 데이터 로드 실패 시 사용할 폴백 데이터"""
        # 기본값 설정
        base_value = 50000  # BTC 기본 가격
        
        # 시나리오별 변화 적용
        if scenario in ["상승 추세", "Uptrend"]:
            trend = np.linspace(0, base_value * 0.1, length)
            noise = np.random.randn(length) * base_value * 0.01
            price_data = base_value + trend + noise
            current_value = price_data[-1]
        elif scenario in ["하락 추세", "Downtrend"]:
            trend = np.linspace(0, -base_value * 0.1, length)
            noise = np.random.randn(length) * base_value * 0.01
            price_data = base_value + trend + noise
            current_value = price_data[-1]
        elif scenario in ["급등", "Surge"]:
            # 중간에 급등
            trend = np.concatenate([
                np.linspace(0, base_value * 0.05, length//2),
                np.linspace(base_value * 0.05, base_value * 0.2, length - length//2)
            ])
            noise = np.random.randn(length) * base_value * 0.02
            price_data = base_value + trend + noise
            current_value = price_data[-1]
        elif scenario in ["급락", "Crash"]:
            # 중간에 급락
            trend = np.concatenate([
                np.linspace(0, base_value * 0.05, length//2),
                np.linspace(base_value * 0.05, -base_value * 0.15, length - length//2)
            ])
            noise = np.random.randn(length) * base_value * 0.02
            price_data = base_value + trend + noise
            current_value = price_data[-1]
        elif scenario in ["이동평균 교차", "MA Cross"]:
            price_data = base_value + np.cumsum(np.random.randn(length) * base_value * 0.005)
            current_value = np.random.uniform(45, 55)  # MA 교차 시뮬레이션
        else:
            # 횡보 또는 기본
            noise = np.random.randn(length) * base_value * 0.01
            price_data = base_value + noise
            current_value = price_data[-1]
        
        return {
            'current_value': float(current_value),
            'price_data': price_data.tolist(),
            'scenario': scenario,
            'data_source': 'fallback_simulation',
            'period': 'simulated_data',
            'base_value': base_value,
            'change_percent': (current_value / base_value - 1) * 100
        }

# 전역 인스턴스 (UI에서 사용)
_simulation_engine = None

def get_simulation_engine():
    """시뮬레이션 엔진 싱글톤 인스턴스 반환 (사용자 선택 지원)"""
    global _simulation_engine
    if _simulation_engine is None:
        try:
            # 사용자 선택형 데이터 소스 관리자 사용
            from .data_source_manager import get_simulation_engine_by_preference
            _simulation_engine = get_simulation_engine_by_preference()
            logging.info("User-preference simulation engine loaded")
        except ImportError:
            try:
                # 폴백: 내장 최적화 데이터셋 엔진
                from .embedded_simulation_engine import get_embedded_simulation_engine
                _simulation_engine = get_embedded_simulation_engine()
                logging.info("Embedded optimized dataset engine loaded (fallback)")
            except ImportError:
                try:
                    # 폴백2: 강화된 엔진 (DB 없어도 작동)
                    from .robust_simulation_engine import EnhancedRealDataSimulationEngine
                    _simulation_engine = EnhancedRealDataSimulationEngine()
                    logging.info("Enhanced simulation engine loaded (fallback)")
                except ImportError:
                    # 폴백3: 기존 엔진 (DB 의존적)
                    _simulation_engine = RealDataSimulationEngine()
                    logging.warning("Using basic simulation engine (final fallback)")
    return _simulation_engine


def get_simulation_engine_with_source(source_type: str):
    """특정 데이터 소스로 시뮬레이션 엔진 생성"""
    try:
        from .data_source_manager import get_simulation_engine_by_preference
        return get_simulation_engine_by_preference(source_type)
    except ImportError:
        logging.warning("Data source manager not available, using default engine")
        return get_simulation_engine()


def reset_simulation_engine():
    """시뮬레이션 엔진 리셋 (데이터 소스 변경시 사용)"""
    global _simulation_engine
    _simulation_engine = None
    logging.info("Simulation engine reset")
