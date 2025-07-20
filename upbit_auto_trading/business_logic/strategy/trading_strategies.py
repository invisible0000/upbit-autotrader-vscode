"""
백테스팅 연동 매매전략 시스템

UI에서 설정된 전략을 백테스팅에서 실행할 수 있도록 연동합니다.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import sqlite3
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class TradeSignal:
    """매매 신호 데이터 클래스"""
    timestamp: datetime
    action: str  # 'buy', 'sell', 'hold'
    price: float
    quantity: float = 0.0
    confidence: float = 0.0
    reason: str = ""


@dataclass
class StrategyConfig:
    """전략 설정 데이터 클래스"""
    strategy_id: str
    name: str
    strategy_type: str
    parameters: Dict[str, Any]
    description: str = ""
    created_at: datetime = None
    updated_at: datetime = None


class TradingStrategy(ABC):
    """매매전략 기본 클래스"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.parameters = config.parameters
        self.name = config.name
        self.strategy_type = config.strategy_type
        
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        """매매 신호 생성"""
        pass
    
    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 계산"""
        pass
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """데이터 유효성 검증"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        return all(col in data.columns for col in required_columns)


class MovingAverageCrossStrategy(TradingStrategy):
    """이동평균선 교차 전략"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.short_period = self.parameters.get('short_period', 5)
        self.long_period = self.parameters.get('long_period', 20)
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """이동평균선 계산"""
        df = data.copy()
        df[f'MA_{self.short_period}'] = df['close'].rolling(window=self.short_period).mean()
        df[f'MA_{self.long_period}'] = df['close'].rolling(window=self.long_period).mean()
        
        # 교차 신호 계산
        df['ma_diff'] = df[f'MA_{self.short_period}'] - df[f'MA_{self.long_period}']
        df['ma_diff_prev'] = df['ma_diff'].shift(1)
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        """매매 신호 생성"""
        if not self.validate_data(data):
            return []
        
        df = self.calculate_indicators(data)
        signals = []
        
        for i, row in df.iterrows():
            if pd.isna(row['ma_diff']) or pd.isna(row['ma_diff_prev']):
                continue
                
            # 골든 크로스 (매수 신호)
            if row['ma_diff_prev'] <= 0 and row['ma_diff'] > 0:
                signals.append(TradeSignal(
                    timestamp=i,
                    action='buy',
                    price=row['close'],
                    confidence=0.8,
                    reason=f"골든크로스: MA{self.short_period} > MA{self.long_period}"
                ))
            
            # 데드 크로스 (매도 신호)
            elif row['ma_diff_prev'] >= 0 and row['ma_diff'] < 0:
                signals.append(TradeSignal(
                    timestamp=i,
                    action='sell',
                    price=row['close'],
                    confidence=0.8,
                    reason=f"데드크로스: MA{self.short_period} < MA{self.long_period}"
                ))
        
        return signals


class RSIStrategy(TradingStrategy):
    """RSI 과매수/과매도 전략"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.period = self.parameters.get('period', 14)
        self.oversold = self.parameters.get('oversold', 30)
        self.overbought = self.parameters.get('overbought', 70)
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """RSI 계산"""
        df = data.copy()
        
        # 가격 변화 계산
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        # RSI 계산
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        """매매 신호 생성"""
        if not self.validate_data(data):
            return []
        
        df = self.calculate_indicators(data)
        signals = []
        
        for i, row in df.iterrows():
            if pd.isna(row['RSI']):
                continue
                
            # 과매도에서 매수
            if row['RSI'] <= self.oversold:
                signals.append(TradeSignal(
                    timestamp=i,
                    action='buy',
                    price=row['close'],
                    confidence=0.7,
                    reason=f"RSI 과매도: {row['RSI']:.1f} <= {self.oversold}"
                ))
            
            # 과매수에서 매도
            elif row['RSI'] >= self.overbought:
                signals.append(TradeSignal(
                    timestamp=i,
                    action='sell',
                    price=row['close'],
                    confidence=0.7,
                    reason=f"RSI 과매수: {row['RSI']:.1f} >= {self.overbought}"
                ))
        
        return signals


class BollingerBandStrategy(TradingStrategy):
    """볼린저 밴드 평균회귀 전략"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.period = self.parameters.get('period', 20)
        self.std_multiplier = self.parameters.get('std_multiplier', 2.0)
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """볼린저 밴드 계산"""
        df = data.copy()
        
        # 중심선 (이동평균)
        df['BB_MIDDLE'] = df['close'].rolling(window=self.period).mean()
        
        # 표준편차
        std = df['close'].rolling(window=self.period).std()
        
        # 상단/하단 밴드
        df['BB_UPPER'] = df['BB_MIDDLE'] + (std * self.std_multiplier)
        df['BB_LOWER'] = df['BB_MIDDLE'] - (std * self.std_multiplier)
        
        # 밴드 위치 (%B)
        df['BB_PERCENT'] = (df['close'] - df['BB_LOWER']) / (df['BB_UPPER'] - df['BB_LOWER'])
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        """매매 신호 생성"""
        if not self.validate_data(data):
            return []
        
        df = self.calculate_indicators(data)
        signals = []
        
        for i, row in df.iterrows():
            if pd.isna(row['BB_PERCENT']):
                continue
                
            # 하단 밴드 근처에서 매수 (평균회귀)
            if row['BB_PERCENT'] <= 0.1:  # 하위 10%
                signals.append(TradeSignal(
                    timestamp=i,
                    action='buy',
                    price=row['close'],
                    confidence=0.6,
                    reason=f"볼린저밴드 하단 접촉: %B={row['BB_PERCENT']:.2f}"
                ))
            
            # 상단 밴드 근처에서 매도
            elif row['BB_PERCENT'] >= 0.9:  # 상위 90%
                signals.append(TradeSignal(
                    timestamp=i,
                    action='sell',
                    price=row['close'],
                    confidence=0.6,
                    reason=f"볼린저밴드 상단 접촉: %B={row['BB_PERCENT']:.2f}"
                ))
        
        return signals


class StrategyManager:
    """전략 관리자 클래스"""
    
    def __init__(self, db_path: str = "data/upbit_auto_trading.sqlite3"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """전략 저장용 DB 테이블 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_strategies (
                strategy_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                strategy_type TEXT NOT NULL,
                parameters TEXT NOT NULL,
                description TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_strategy(self, config: StrategyConfig) -> bool:
        """전략 저장"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO trading_strategies 
                (strategy_id, name, strategy_type, parameters, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                config.strategy_id,
                config.name,
                config.strategy_type,
                json.dumps(config.parameters),
                config.description,
                config.created_at.isoformat() if config.created_at else datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"전략 저장 실패: {e}")
            return False
    
    def load_strategy(self, strategy_id: str) -> Optional[StrategyConfig]:
        """전략 불러오기"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT strategy_id, name, strategy_type, parameters, description, created_at, updated_at
                FROM trading_strategies WHERE strategy_id = ?
            ''', (strategy_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return StrategyConfig(
                    strategy_id=row[0],
                    name=row[1],
                    strategy_type=row[2],
                    parameters=json.loads(row[3]),
                    description=row[4],
                    created_at=datetime.fromisoformat(row[5]) if row[5] else None,
                    updated_at=datetime.fromisoformat(row[6]) if row[6] else None
                )
            return None
            
        except Exception as e:
            logger.error(f"전략 불러오기 실패: {e}")
            return None
    
    def get_all_strategies(self) -> List[StrategyConfig]:
        """모든 전략 목록 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT strategy_id, name, strategy_type, parameters, description, created_at, updated_at
                FROM trading_strategies ORDER BY updated_at DESC
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            strategies = []
            for row in rows:
                strategies.append(StrategyConfig(
                    strategy_id=row[0],
                    name=row[1],
                    strategy_type=row[2],
                    parameters=json.loads(row[3]),
                    description=row[4],
                    created_at=datetime.fromisoformat(row[5]) if row[5] else None,
                    updated_at=datetime.fromisoformat(row[6]) if row[6] else None
                ))
            
            return strategies
            
        except Exception as e:
            logger.error(f"전략 목록 조회 실패: {e}")
            return []
    
    def create_strategy(self, config: StrategyConfig) -> Optional[TradingStrategy]:
        """전략 인스턴스 생성"""
        try:
            if config.strategy_type == "이동평균 교차":
                return MovingAverageCrossStrategy(config)
            elif config.strategy_type == "RSI":
                return RSIStrategy(config)
            elif config.strategy_type == "볼린저 밴드":
                return BollingerBandStrategy(config)
            else:
                logger.error(f"지원하지 않는 전략 타입: {config.strategy_type}")
                return None
                
        except Exception as e:
            logger.error(f"전략 생성 실패: {e}")
            return None


# 기본 전략 설정 템플릿
DEFAULT_STRATEGIES = [
    {
        'strategy_id': 'ma_cross_5_20',
        'name': '골든크로스 전략 (5-20)',
        'strategy_type': '이동평균 교차',
        'parameters': {'short_period': 5, 'long_period': 20},
        'description': '단기 5일선이 장기 20일선을 상향 돌파시 매수, 하향 돌파시 매도'
    },
    {
        'strategy_id': 'rsi_classic',
        'name': 'RSI 클래식 전략',
        'strategy_type': 'RSI',
        'parameters': {'period': 14, 'oversold': 30, 'overbought': 70},
        'description': 'RSI 30 이하 매수, 70 이상 매도'
    },
    {
        'strategy_id': 'bb_mean_reversion',
        'name': '볼린저밴드 평균회귀',
        'strategy_type': '볼린저 밴드',
        'parameters': {'period': 20, 'std_multiplier': 2.0},
        'description': '볼린저밴드 하단 접촉시 매수, 상단 접촉시 매도'
    }
]


def initialize_default_strategies():
    """기본 전략들을 DB에 초기화"""
    manager = StrategyManager()
    
    for strategy_data in DEFAULT_STRATEGIES:
        config = StrategyConfig(
            strategy_id=strategy_data['strategy_id'],
            name=strategy_data['name'],
            strategy_type=strategy_data['strategy_type'],
            parameters=strategy_data['parameters'],
            description=strategy_data['description'],
            created_at=datetime.now()
        )
        
        success = manager.save_strategy(config)
        if success:
            print(f"✅ 기본 전략 초기화: {config.name}")
        else:
            print(f"❌ 기본 전략 초기화 실패: {config.name}")


if __name__ == "__main__":
    # 기본 전략 초기화 테스트
    initialize_default_strategies()
    
    # 전략 테스트
    manager = StrategyManager()
    strategies = manager.get_all_strategies()
    print(f"\n📊 저장된 전략 수: {len(strategies)}")
    
    for strategy in strategies:
        print(f"   - {strategy.name} ({strategy.strategy_type})")
