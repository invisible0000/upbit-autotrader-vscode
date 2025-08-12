"""
공통 시뮬레이션 엔진 - 통합 및 단순화
Git Clone 호환, Junction 링크 없이 모든 기능 포함
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import os
import sqlite3
import sys
from pathlib import Path

# 로깅 설정
logger = logging.getLogger(__name__)

class BaseSimulationEngine:
    """시뮬레이션 엔진 베이스 클래스"""
    
    def __init__(self):
        self.name = "Base"
        
    def load_market_data(self, limit: int = 100) -> Optional[pd.DataFrame]:
        """시장 데이터 로드"""
        raise NotImplementedError
        
    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 계산"""
        if data is None or data.empty:
            return data
        
        try:
            # SMA (단순이동평균)
            data['SMA_20'] = data['close'].rolling(window=20).mean()
            data['SMA_60'] = data['close'].rolling(window=60).mean()
            
            # EMA (지수이동평균)  
            data['EMA_12'] = data['close'].ewm(span=12).mean()
            data['EMA_26'] = data['close'].ewm(span=26).mean()
            
            # RSI (상대강도지수)
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD
            data['MACD'] = data['EMA_12'] - data['EMA_26']
            data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()
            
            # 볼린저 밴드
            bb_period = 20
            bb_std = 2
            bb_middle = data['close'].rolling(window=bb_period).mean()
            bb_std_dev = data['close'].rolling(window=bb_period).std()
            data['BB_Upper'] = bb_middle + (bb_std_dev * bb_std)
            data['BB_Lower'] = bb_middle - (bb_std_dev * bb_std)
            data['BB_Middle'] = bb_middle
            
            logger.info("✅ 기술적 지표 계산 완료")
            return data
            
        except Exception as e:
            logger.error(f"❌ 기술적 지표 계산 실패: {e}")
            return data
    
    def generate_sample_scenarios(self, base_data: pd.DataFrame, scenario: str = "횡보") -> pd.DataFrame:
        """시나리오별 샘플 데이터 생성"""
        if base_data is None or base_data.empty:
            # 기본 데이터 생성
            dates = pd.date_range(start='2024-01-01', periods=100, freq='H')
            base_price = 50000  # KRW
            
            if scenario == "상승":
                prices = [base_price + i * 100 + np.random.normal(0, 500) for i in range(100)]
            elif scenario == "하락":
                prices = [base_price - i * 100 + np.random.normal(0, 500) for i in range(100)]
            elif scenario == "급등":
                prices = [base_price + i * 200 + np.random.normal(0, 800) for i in range(100)]
            elif scenario == "급락":
                prices = [base_price - i * 200 + np.random.normal(0, 800) for i in range(100)]
            else:  # 횡보
                prices = [base_price + np.random.normal(0, 300) for _ in range(100)]
            
            # 가격이 음수가 되지 않도록 조정
            prices = [max(1000, price) for price in prices]
            
            volumes = [np.random.randint(10000, 100000) for _ in range(100)]
            
            base_data = pd.DataFrame({
                'timestamp': dates,
                'open': prices,
                'high': [p * 1.02 for p in prices],
                'low': [p * 0.98 for p in prices], 
                'close': prices,
                'volume': volumes
            })
        
        return self.calculate_technical_indicators(base_data)

class EmbeddedSimulationEngine(BaseSimulationEngine):
    """내장 데이터 시뮬레이션 엔진"""
    
    def __init__(self):
        super().__init__()
        self.name = "Embedded"
        
    def load_market_data(self, limit: int = 100) -> pd.DataFrame:
        """내장 최적화된 샘플 데이터 로드"""
        try:
            # 현실적인 비트코인 가격 패턴 생성
            dates = pd.date_range(start='2024-01-01', periods=limit, freq='H')
            base_price = 50000000  # 5천만원 (현실적인 BTC 가격)
            
            # 현실적인 가격 변동 패턴
            price_changes = np.random.normal(0, 0.02, limit)  # 2% 표준편차
            cumulative_changes = np.cumprod(1 + price_changes)
            
            prices = base_price * cumulative_changes
            volumes = np.random.lognormal(10, 1, limit)  # 로그정규분포 거래량
            
            data = pd.DataFrame({
                'timestamp': dates,
                'open': prices,
                'high': prices * (1 + np.abs(np.random.normal(0, 0.01, limit))),
                'low': prices * (1 - np.abs(np.random.normal(0, 0.01, limit))),
                'close': prices,
                'volume': volumes
            })
            
            logger.info(f"✅ 내장 시뮬레이션 데이터 로드 완료: {len(data)}개 레코드")
            return self.calculate_technical_indicators(data)
            
        except Exception as e:
            logger.error(f"❌ 내장 데이터 로드 실패: {e}")
            return self.generate_sample_scenarios(pd.DataFrame(), "횡보")

class RealDataSimulationEngine(BaseSimulationEngine):
    """실제 DB 데이터 시뮬레이션 엔진"""
    
    def __init__(self):
        super().__init__()
        self.name = "RealData"
        
    def load_market_data(self, limit: int = 100) -> pd.DataFrame:
        """실제 데이터베이스에서 시장 데이터 로드"""
        try:
            # 샘플 DB 직접 사용
            possible_paths = [
                # 샘플 마켓 데이터 (우선순위)
                "upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/engines/data/sampled_market_data.sqlite3",
                # 메인 데이터베이스들
                "data/sampled_market_data.sqlite3",
                "../data/sampled_market_data.sqlite3",
                "../../data/sampled_market_data.sqlite3", 
                "../../../data/sampled_market_data.sqlite3",
                "../../../../data/sampled_market_data.sqlite3",
                "../../../../../data/sampled_market_data.sqlite3"
            ]
            
            db_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    db_path = path
                    break
            
            if not db_path:
                logger.warning("⚠️ 실제 DB를 찾을 수 없음, 샘플 데이터 사용")
                return EmbeddedSimulationEngine().load_market_data(limit)
            
            with sqlite3.connect(db_path) as conn:
                query = """
                SELECT timestamp, open, high, low, close, volume 
                FROM market_data 
                ORDER BY timestamp DESC 
                LIMIT ?
                """
                data = pd.read_sql_query(query, conn, params=[limit])
                
                if data.empty:
                    logger.warning("⚠️ DB에 데이터가 없음, 샘플 데이터 사용")
                    return EmbeddedSimulationEngine().load_market_data(limit)
                
                # 타임스탬프 변환
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                data = data.sort_values('timestamp').reset_index(drop=True)
                
                logger.info(f"✅ 실제 DB 데이터 로드 완료: {len(data)}개 레코드")
                return self.calculate_technical_indicators(data)
                
        except Exception as e:
            logger.error(f"❌ 실제 DB 데이터 로드 실패: {e}")
            return EmbeddedSimulationEngine().load_market_data(limit)

class RobustSimulationEngine(BaseSimulationEngine):
    """견고한 시뮬레이션 엔진 (다중 소스 지원)"""
    
    def __init__(self):
        super().__init__()
        self.name = "Robust"
        self.embedded_engine = EmbeddedSimulationEngine()
        self.realdata_engine = RealDataSimulationEngine()
        
    def load_market_data(self, limit: int = 100) -> pd.DataFrame:
        """다중 소스에서 최적의 데이터 로드"""
        try:
            # 1순위: 실제 DB 데이터
            data = self.realdata_engine.load_market_data(limit)
            if data is not None and len(data) >= limit * 0.8:  # 80% 이상 데이터가 있으면 사용
                logger.info("✅ 견고한 엔진: 실제 DB 데이터 사용")
                return data
            
            # 2순위: 내장 시뮬레이션 데이터
            logger.info("✅ 견고한 엔진: 내장 시뮬레이션 데이터 사용")
            return self.embedded_engine.load_market_data(limit)
            
        except Exception as e:
            logger.error(f"❌ 견고한 엔진 데이터 로드 실패: {e}")
            return self.embedded_engine.load_market_data(limit)

# 엔진 팩토리 함수들
def get_embedded_engine() -> EmbeddedSimulationEngine:
    """내장 엔진 반환"""
    return EmbeddedSimulationEngine()

def get_realdata_engine() -> RealDataSimulationEngine:
    """실제 데이터 엔진 반환"""
    return RealDataSimulationEngine()

def get_robust_engine() -> RobustSimulationEngine:
    """견고한 엔진 반환"""
    return RobustSimulationEngine()

def get_simulation_engine(engine_type: str = "robust") -> BaseSimulationEngine:
    """엔진 타입에 따라 적절한 엔진 반환"""
    engine_type = engine_type.lower()
    
    if engine_type == "embedded":
        return get_embedded_engine()
    elif engine_type == "realdata":
        return get_realdata_engine()
    elif engine_type == "robust":
        return get_robust_engine()
    else:
        logger.warning(f"⚠️ 알 수 없는 엔진 타입: {engine_type}, robust 엔진 사용")
        return get_robust_engine()

# 하위 호환성을 위한 클래스 별칭
RealDataSimulation = RealDataSimulationEngine
EmbeddedSimulationEngine = EmbeddedSimulationEngine
RobustSimulationEngine = RobustSimulationEngine

__all__ = [
    'BaseSimulationEngine',
    'EmbeddedSimulationEngine', 
    'RealDataSimulationEngine',
    'RobustSimulationEngine',
    'get_embedded_engine',
    'get_realdata_engine', 
    'get_robust_engine',
    'get_simulation_engine'
]
