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

from upbit_auto_trading.business_logic.strategy.strategy_interface import StrategyInterface

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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def create_strategy(self) -> 'TradingStrategy':
        """설정에 따라 전략 객체 생성"""
        if self.strategy_type == 'moving_average_cross':
            return MovingAverageCrossStrategy(self)
        elif self.strategy_type == 'rsi_reversal':
            return RSIReversalStrategy(self)
        elif self.strategy_type == 'bollinger_band_mean_reversion':
            return BollingerBandMeanReversionStrategy(self)
        elif self.strategy_type == 'volatility_breakout':
            return VolatilityBreakoutStrategy(self)
        elif self.strategy_type == 'buy_and_hold':
            return BuyAndHoldStrategy(self)
        else:
            raise ValueError(f"지원하지 않는 전략 타입: {self.strategy_type}")


class TradingStrategy(StrategyInterface):
    """매매전략 기본 클래스"""
    
    def __init__(self, parameters: Dict[str, Any]):
        """전략 초기화 - StrategyInterface 구현"""
        if isinstance(parameters, StrategyConfig):
            # StrategyConfig 객체인 경우
            self.config = parameters
            self.parameters = parameters.parameters
            self.name = parameters.name
            self.strategy_type = parameters.strategy_type
        else:
            # 딕셔너리인 경우
            self.parameters = parameters
            self.name = parameters.get('name', 'Unknown Strategy')
            self.strategy_type = parameters.get('strategy_type', 'unknown')
            self.config = None
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """전략 매개변수 유효성 검사 - 기본 구현"""
        if not isinstance(parameters, dict):
            return False
        
        # 기본적으로 필요한 필드들이 있는지 확인
        return True
    
    def get_parameters(self) -> Dict[str, Any]:
        """현재 전략 매개변수 반환"""
        return self.parameters.copy()
    
    def set_parameters(self, parameters: Dict[str, Any]) -> bool:
        """전략 매개변수 설정"""
        if self.validate_parameters(parameters):
            self.parameters = parameters
            return True
        return False
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """전략 정보 반환"""
        return {
            'name': self.name,
            'type': self.strategy_type,
            'description': f'{self.name} 전략',
            'parameters': self.parameters
        }
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """기본 매개변수 반환"""
        return {
            'name': self.name,
            'strategy_type': self.strategy_type,
            'enabled': True
        }
        
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """매매 신호 생성 - StrategyInterface 구현"""
        pass
    
    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 계산"""
        pass
    
    @abstractmethod
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        """이 전략에 필요한 기술적 지표 목록 반환"""
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
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        """필요한 기술적 지표 목록 반환"""
        return [
            {
                'name': 'MA',
                'period': self.short_period,
                'source': 'close'
            },
            {
                'name': 'MA',
                'period': self.long_period,
                'source': 'close'
            }
        ]
        
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
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        """필요한 기술적 지표 목록 반환"""
        return [
            {
                'name': 'RSI',
                'period': self.period,
                'source': 'close'
            }
        ]
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
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        """필요한 기술적 지표 목록 반환"""
        return [
            {
                'name': 'BB',  # Bollinger Bands
                'period': self.period,
                'std_dev': self.std_multiplier,
                'source': 'close'
            }
        ]
        
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


class FixedStopLossStrategy(TradingStrategy):
    """고정 손절 전략"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.stop_loss_percent = self.parameters.get('stop_loss_percent', 5.0)  # 5% 손절
        
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        """필요한 기술적 지표 목록 반환"""
        return []  # 손절 전략은 별도 지표 불필요
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """지표 계산 (손절은 별도 지표 불필요)"""
        return data.copy()
    
    def generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        """손절 신호 생성 (실제로는 포지션 관리에서 처리)"""
        return []  # 손절은 포지션 관리에서 처리


class TrailingStopStrategy(TradingStrategy):
    """트레일링 스톱 전략"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.trailing_percent = self.parameters.get('trailing_percent', 3.0)  # 3% 트레일링
        
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        """필요한 기술적 지표 목록 반환"""
        return []
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """지표 계산"""
        return data.copy()
    
    def generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        """트레일링 스톱 신호 생성"""
        return []  # 포지션 관리에서 처리


class TakeProfitStrategy(TradingStrategy):
    """이익 실현 전략"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.take_profit_percent = self.parameters.get('take_profit_percent', 10.0)  # 10% 익절
        
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        """필요한 기술적 지표 목록 반환"""
        return []
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """지표 계산"""
        return data.copy()
    
    def generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        """익절 신호 생성"""
        return []  # 포지션 관리에서 처리


# UI에서 사용하는 전략 클래스들에 대한 별칭 추가
class RSIReversalStrategy(RSIStrategy):
    """RSI 반전 전략 (RSIStrategy의 별칭)"""
    pass


class BollingerBandMeanReversionStrategy(BollingerBandStrategy):
    """볼린저 밴드 평균회귀 전략 (BollingerBandStrategy의 별칭)"""
    pass


class VolatilityBreakoutStrategy(TradingStrategy):
    """변동성 돌파 전략"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.period = self.parameters.get('period', 20)
        self.k_value = self.parameters.get('k_value', 0.5)
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        """필요한 기술적 지표 목록 반환"""
        return [
            {
                'name': 'TR',  # True Range
                'period': self.period,
                'source': 'close'
            }
        ]
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """변동성 지표 계산"""
        df = data.copy()
        
        # 변동성 계산 (20일 고가/저가 범위)
        df['high_max'] = df['high'].rolling(window=self.period).max()
        df['low_min'] = df['low'].rolling(window=self.period).min()
        df['range'] = df['high_max'] - df['low_min']
        
        # 돌파 신호
        df['break_up'] = df['close'] > (df['low_min'] + self.k_value * df['range'])
        df['break_down'] = df['close'] < (df['high_max'] - self.k_value * df['range'])
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        """변동성 돌파 신호 생성"""
        if not self.validate_data(data):
            return []
        
        df = self.calculate_indicators(data)
        signals = []
        
        for i, row in df.iterrows():
            if pd.isna(row['range']):
                continue
                
            # 상향 돌파
            if row['break_up']:
                signals.append(TradeSignal(
                    timestamp=i,
                    action='buy',
                    price=row['close'],
                    confidence=0.7,
                    reason=f"변동성 상향 돌파"
                ))
            
            # 하향 돌파
            elif row['break_down']:
                signals.append(TradeSignal(
                    timestamp=i,
                    action='sell',
                    price=row['close'],
                    confidence=0.7,
                    reason=f"변동성 하향 돌파"
                ))
        
        return signals


class StrategyManager:
    """전략 관리자 클래스"""
    
    def __init__(self, db_path: str = "data/upbit_auto_trading.sqlite3"):
        self.db_path = db_path
        self.conn = None
        self._init_db()
        
    def _init_db(self):
        """전략 저장용 DB 테이블 초기화"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
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
        
        self.conn.commit()
        # DB 연결은 유지 (self.conn)
    
    def save_strategy(self, config: StrategyConfig) -> bool:
        """전략 저장"""
        try:
            cursor = self.conn.cursor()
            
            # signal_type 결정 (config에 있으면 사용, 없으면 전략 타입에 따라 결정)
            signal_type = getattr(config, 'signal_type', None)
            if not signal_type:
                # 관리 전략인지 판별하여 signal_type 설정
                management_types = ['고정 손절', '트레일링 스탑', '목표 익절', '부분 익절', '시간 기반 청산', '변동성 기반 관리']
                signal_type = 'MANAGEMENT' if config.strategy_type in management_types else 'BUY/SELL'
            
            cursor.execute('''
                INSERT OR REPLACE INTO trading_strategies 
                (strategy_id, name, strategy_type, parameters, description, created_at, updated_at, signal_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                config.strategy_id,
                config.name,
                config.strategy_type,
                json.dumps(config.parameters),
                config.description,
                config.created_at.isoformat() if config.created_at else datetime.now().isoformat(),
                datetime.now().isoformat(),
                signal_type
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"전략 저장 실패: {e}")
            return False
    
    def load_strategy(self, strategy_id: str) -> Optional[StrategyConfig]:
        """전략 불러오기"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
                SELECT strategy_id, name, strategy_type, parameters, description, created_at, updated_at, signal_type
                FROM trading_strategies WHERE strategy_id = ?
            ''', (strategy_id,))
            
            row = cursor.fetchone()
            
            if row:
                strategy = StrategyConfig(
                    strategy_id=row[0],
                    name=row[1],
                    strategy_type=row[2],
                    parameters=json.loads(row[3]),
                    description=row[4],
                    created_at=datetime.fromisoformat(row[5]) if row[5] else None,
                    updated_at=datetime.fromisoformat(row[6]) if row[6] else None
                )
                # signal_type 동적 속성 추가
                strategy.signal_type = row[7] if len(row) > 7 and row[7] else 'BUY/SELL'
                return strategy
            return None
            
        except Exception as e:
            logger.error(f"전략 불러오기 실패: {e}")
            return None
    
    def get_all_strategies(self) -> List[StrategyConfig]:
        """모든 전략 목록 조회"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
                SELECT strategy_id, name, strategy_type, parameters, description, created_at, updated_at, signal_type
                FROM trading_strategies ORDER BY updated_at DESC
            ''')
            
            rows = cursor.fetchall()
            
            strategies = []
            for row in rows:
                strategy = StrategyConfig(
                    strategy_id=row[0],
                    name=row[1],
                    strategy_type=row[2],
                    parameters=json.loads(row[3]),
                    description=row[4],
                    created_at=datetime.fromisoformat(row[5]) if row[5] else None,
                    updated_at=datetime.fromisoformat(row[6]) if row[6] else None
                )
                # signal_type 동적 속성 추가
                strategy.signal_type = row[7] if len(row) > 7 else 'BUY/SELL'
                strategies.append(strategy)
            
            return strategies
            
        except Exception as e:
            logger.error(f"전략 목록 조회 실패: {e}")
            return []
    
    def delete_strategy(self, strategy_id: str) -> bool:
        """전략 삭제"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "DELETE FROM trading_strategies WHERE strategy_id = ?",
                (strategy_id,)
            )
            self.conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"전략 삭제 완료: {strategy_id}")
                return True
            else:
                logger.warning(f"삭제할 전략을 찾을 수 없음: {strategy_id}")
                return False
                
        except sqlite3.Error as e:
            logger.error(f"전략 삭제 DB 오류: {e}")
            return False
        except Exception as e:
            logger.error(f"전략 삭제 실패: {e}")
            return False
    
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


class BuyAndHoldStrategy(TradingStrategy):
    """단순 매수 보유 전략"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        """이 전략은 기술적 지표가 필요 없음"""
        return []
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 계산 (없음)"""
        return data.copy()
    
    def generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        """매매 신호 생성 - 첫 번째 데이터에서만 매수 신호"""
        if not self.validate_data(data) or len(data) == 0:
            return []
        
        # 첫 번째 행에서만 매수 신호 생성
        first_row = data.iloc[0]
        signals = [TradeSignal(
            timestamp=data.index[0],
            action='buy',
            price=first_row['close'],
            confidence=1.0,
            reason="Buy & Hold 전략 - 초기 매수"
        )]
        
        return signals


class VolatilityBreakoutStrategy(TradingStrategy):
    """변동성 돌파 전략"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.period = self.parameters.get('period', 20)
        self.k_value = self.parameters.get('k_value', 0.5)
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        """필요한 기술적 지표 목록 반환"""
        return [
            {
                'name': 'TR',  # True Range
                'period': self.period
            }
        ]
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """변동성 지표 계산"""
        df = data.copy()
        
        # True Range 계산
        df['prev_close'] = df['close'].shift(1)
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['prev_close'])
        df['tr3'] = abs(df['low'] - df['prev_close'])
        df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        # N일 범위 계산
        df['range_high'] = df['high'].rolling(window=self.period).max()
        df['range_low'] = df['low'].rolling(window=self.period).min()
        df['range_avg'] = (df['range_high'] + df['range_low']) / 2
        
        # 돌파 기준선
        df['upper_breakout'] = df['range_high'].shift(1)
        df['lower_breakout'] = df['range_low'].shift(1)
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> List[TradeSignal]:
        """변동성 돌파 신호 생성"""
        if not self.validate_data(data):
            return []
        
        df = self.calculate_indicators(data)
        signals = []
        
        for i, row in df.iterrows():
            if pd.isna(row['upper_breakout']) or pd.isna(row['lower_breakout']):
                continue
                
            # 상향 돌파 (매수)
            if row['close'] > row['upper_breakout']:
                signals.append(TradeSignal(
                    timestamp=i,
                    action='buy',
                    price=row['close'],
                    confidence=0.7,
                    reason=f"변동성 상향 돌파: {row['close']:.0f} > {row['upper_breakout']:.0f}"
                ))
            
            # 하향 돌파 (매도)
            elif row['close'] < row['lower_breakout']:
                signals.append(TradeSignal(
                    timestamp=i,
                    action='sell',
                    price=row['close'],
                    confidence=0.7,
                    reason=f"변동성 하향 돌파: {row['close']:.0f} < {row['lower_breakout']:.0f}"
                ))
        
        return signals


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
