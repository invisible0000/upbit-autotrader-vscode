"""
데이터 소스 관리자
다양한 데이터 소스에서 시장 데이터를 로드하고 검증
"""

import pandas as pd
import numpy as np
import sqlite3
import os
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MarketDataLoader:
    """시장 데이터 로더"""
    
    @staticmethod
    def load_from_database(db_path: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """데이터베이스에서 시장 데이터 로드"""
        try:
            if not os.path.exists(db_path):
                logger.warning(f"⚠️ DB 파일이 없음: {db_path}")
                return None
                
            with sqlite3.connect(db_path) as conn:
                query = """
                SELECT timestamp, open, high, low, close, volume 
                FROM market_data 
                ORDER BY timestamp DESC 
                LIMIT ?
                """
                data = pd.read_sql_query(query, conn, params=[limit])
                
                if data.empty:
                    logger.warning("⚠️ DB에 데이터가 없음")
                    return None
                
                # 타임스탬프 변환
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                data = data.sort_values('timestamp').reset_index(drop=True)
                
                logger.info(f"✅ DB 데이터 로드 완료: {len(data)}개 레코드")
                return data
                
        except Exception as e:
            logger.error(f"❌ DB 데이터 로드 실패: {e}")
            return None
    
    @staticmethod
    def find_database_path() -> Optional[str]:
        """프로젝트에서 데이터베이스 파일 찾기"""
        possible_paths = [
            # 샘플 마켓 데이터 (우선순위)
            "upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/engines/data/sampled_market_data.sqlite3",
            # 메인 데이터베이스들
            "data/upbit_auto_trading.sqlite3",
            "../data/upbit_auto_trading.sqlite3",
            "../../data/upbit_auto_trading.sqlite3", 
            "../../../data/upbit_auto_trading.sqlite3",
            "../../../../data/upbit_auto_trading.sqlite3",
            "../../../../../data/upbit_auto_trading.sqlite3"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"✅ DB 파일 발견: {path}")
                return path
                
        logger.warning("⚠️ 어떤 경로에서도 DB 파일을 찾을 수 없음")
        return None


class SampleDataGenerator:
    """샘플 데이터 생성기"""
    
    @staticmethod
    def generate_realistic_btc_data(limit: int = 100, scenario: str = "normal") -> pd.DataFrame:
        """현실적인 비트코인 데이터 생성"""
        try:
            dates = pd.date_range(start='2024-01-01', periods=limit, freq='H')
            base_price = 50000000  # 5천만원
            
            # 시나리오별 가격 패턴
            if scenario == "bull":  # 상승장
                trend = np.linspace(0, 0.3, limit)  # 30% 상승
                volatility = 0.015  # 1.5% 변동성
            elif scenario == "bear":  # 하락장
                trend = np.linspace(0, -0.2, limit)  # 20% 하락
                volatility = 0.02  # 2% 변동성
            elif scenario == "volatile":  # 고변동성
                trend = np.zeros(limit)
                volatility = 0.04  # 4% 변동성
            else:  # normal - 횡보
                trend = np.zeros(limit)
                volatility = 0.02  # 2% 변동성
            
            # 가격 변동 생성
            random_changes = np.random.normal(0, volatility, limit)
            cumulative_changes = np.cumprod(1 + trend/limit + random_changes)
            
            prices = base_price * cumulative_changes
            
            # OHLC 데이터 생성
            high_factors = 1 + np.abs(np.random.normal(0, 0.005, limit))
            low_factors = 1 - np.abs(np.random.normal(0, 0.005, limit))
            
            # 거래량 (로그정규분포)
            volumes = np.random.lognormal(10, 1, limit)
            
            data = pd.DataFrame({
                'timestamp': dates,
                'open': prices,
                'high': prices * high_factors,
                'low': prices * low_factors,
                'close': prices,
                'volume': volumes
            })
            
            logger.info(f"✅ {scenario} 시나리오 샘플 데이터 생성: {len(data)}개")
            return data
            
        except Exception as e:
            logger.error(f"❌ 샘플 데이터 생성 실패: {e}")
            return pd.DataFrame()


class DataValidator:
    """데이터 검증기"""
    
    @staticmethod
    def validate_market_data(data: pd.DataFrame) -> Dict[str, Any]:
        """시장 데이터 유효성 검증"""
        if data is None or data.empty:
            return {
                'is_valid': False,
                'errors': ['데이터가 비어있음'],
                'warnings': []
            }
        
        errors = []
        warnings = []
        
        # 필수 컬럼 확인
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            errors.append(f"필수 컬럼 누락: {missing_columns}")
        
        # 데이터 타입 확인
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in data.columns and not pd.api.types.is_numeric_dtype(data[col]):
                errors.append(f"{col} 컬럼이 숫자형이 아님")
        
        # 가격 논리 확인 (high >= max(open, close), low <= min(open, close))
        if all(col in data.columns for col in ['open', 'high', 'low', 'close']):
            invalid_high = data['high'] < data[['open', 'close']].max(axis=1)
            invalid_low = data['low'] > data[['open', 'close']].min(axis=1)
            
            if invalid_high.any():
                warnings.append(f"High 가격 이상: {invalid_high.sum()}개 레코드")
            if invalid_low.any():
                warnings.append(f"Low 가격 이상: {invalid_low.sum()}개 레코드")
        
        # 음수 가격 확인
        for col in ['open', 'high', 'low', 'close']:
            if col in data.columns and (data[col] <= 0).any():
                errors.append(f"{col}에 0 이하 값 존재")
        
        # 음수 거래량 확인
        if 'volume' in data.columns and (data['volume'] < 0).any():
            warnings.append("음수 거래량 존재")
        
        is_valid = len(errors) == 0
        
        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'record_count': len(data),
            'date_range': {
                'start': data['timestamp'].min() if 'timestamp' in data.columns else None,
                'end': data['timestamp'].max() if 'timestamp' in data.columns else None
            }
        }
    
    @staticmethod
    def is_data_sufficient(data: pd.DataFrame, min_records: int = 50) -> bool:
        """데이터가 충분한지 확인"""
        if data is None or data.empty:
            return False
        
        validation_result = DataValidator.validate_market_data(data)
        return (validation_result['is_valid'] and 
                validation_result['record_count'] >= min_records)


__all__ = [
    'MarketDataLoader',
    'SampleDataGenerator', 
    'DataValidator'
]
