"""
지표 처리기 모듈

이 모듈은 기술적 지표 계산 기능을 제공합니다.
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional, Tuple


class IndicatorProcessor:
    """
    지표 처리기 클래스
    
    이 클래스는 기술적 지표 계산 기능을 제공합니다.
    """
    
    def __init__(self):
        """
        지표 처리기 초기화
        """
        self.logger = logging.getLogger(__name__)
    
    def calculate_indicators(self, data: pd.DataFrame, indicators: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        기술적 지표 계산
        
        Args:
            data: OHLCV 데이터가 포함된 DataFrame
            indicators: 계산할 지표 목록
                - name: 지표 이름 (예: 'SMA', 'RSI', 'BOLLINGER_BANDS')
                - params: 지표 매개변수 (예: {'window': 20, 'column': 'close'})
                
        Returns:
            지표가 추가된 DataFrame
        """
        self.logger.info(f"기술적 지표 계산 중: {len(indicators)}개 지표")
        
        # 데이터 복사
        result = data.copy()
        
        # 각 지표 계산
        for indicator in indicators:
            name = indicator['name']
            params = indicator['params']
            
            try:
                # 지표 유형에 따라 계산 함수 호출
                if name == 'SMA':
                    result = self._calculate_sma(result, params)
                elif name == 'EMA':
                    result = self._calculate_ema(result, params)
                elif name == 'RSI':
                    result = self._calculate_rsi(result, params)
                elif name == 'BOLLINGER_BANDS':
                    result = self._calculate_bollinger_bands(result, params)
                elif name == 'MACD':
                    result = self._calculate_macd(result, params)
                else:
                    self.logger.warning(f"지원하지 않는 지표: {name}")
            except Exception as e:
                self.logger.error(f"지표 계산 중 오류 발생: {name}, {str(e)}")
        
        self.logger.info(f"기술적 지표 계산 완료: {len(result.columns)}개 컬럼")
        return result
    
    def _calculate_sma(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        단순 이동 평균 계산
        
        Args:
            data: OHLCV 데이터가 포함된 DataFrame
            params: 지표 매개변수
                - window: 윈도우 크기
                - column: 대상 컬럼 (기본값: 'close')
                
        Returns:
            SMA가 추가된 DataFrame
        """
        window = params['window']
        column = params.get('column', 'close')
        
        # 컬럼 존재 확인
        if column not in data.columns:
            self.logger.warning(f"컬럼이 존재하지 않습니다: {column}")
            return data
        
        # SMA 계산
        data[f'SMA_{window}'] = data[column].rolling(window=window).mean()
        
        return data
    
    def _calculate_ema(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        지수 이동 평균 계산
        
        Args:
            data: OHLCV 데이터가 포함된 DataFrame
            params: 지표 매개변수
                - window: 윈도우 크기
                - column: 대상 컬럼 (기본값: 'close')
                
        Returns:
            EMA가 추가된 DataFrame
        """
        window = params['window']
        column = params.get('column', 'close')
        
        # 컬럼 존재 확인
        if column not in data.columns:
            self.logger.warning(f"컬럼이 존재하지 않습니다: {column}")
            return data
        
        # EMA 계산
        data[f'EMA_{window}'] = data[column].ewm(span=window, adjust=False).mean()
        
        return data
    
    def _calculate_rsi(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        상대 강도 지수 계산
        
        Args:
            data: OHLCV 데이터가 포함된 DataFrame
            params: 지표 매개변수
                - window: 윈도우 크기
                - column: 대상 컬럼 (기본값: 'close')
                
        Returns:
            RSI가 추가된 DataFrame
        """
        window = params['window']
        column = params.get('column', 'close')
        
        # 컬럼 존재 확인
        if column not in data.columns:
            self.logger.warning(f"컬럼이 존재하지 않습니다: {column}")
            return data
        
        # 가격 변화 계산
        delta = data[column].diff()
        
        # 상승/하락 구분
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 평균 상승/하락 계산
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        
        # RSI 계산
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # 결과 저장
        data[f'RSI_{window}'] = rsi
        
        return data
    
    def _calculate_bollinger_bands(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        볼린저 밴드 계산
        
        Args:
            data: OHLCV 데이터가 포함된 DataFrame
            params: 지표 매개변수
                - window: 윈도우 크기
                - num_std: 표준편차 배수
                - column: 대상 컬럼 (기본값: 'close')
                
        Returns:
            볼린저 밴드가 추가된 DataFrame
        """
        window = params['window']
        num_std = params.get('num_std', 2.0)
        column = params.get('column', 'close')
        
        # 컬럼 존재 확인
        if column not in data.columns:
            self.logger.warning(f"컬럼이 존재하지 않습니다: {column}")
            return data
        
        # 이동 평균 계산
        data['BB_MIDDLE'] = data[column].rolling(window=window).mean()
        
        # 표준편차 계산
        rolling_std = data[column].rolling(window=window).std()
        
        # 상단/하단 밴드 계산
        data['BB_UPPER'] = data['BB_MIDDLE'] + (rolling_std * num_std)
        data['BB_LOWER'] = data['BB_MIDDLE'] - (rolling_std * num_std)
        
        return data
    
    def _calculate_macd(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        MACD 계산
        
        Args:
            data: OHLCV 데이터가 포함된 DataFrame
            params: 지표 매개변수
                - fast_period: 빠른 EMA 기간
                - slow_period: 느린 EMA 기간
                - signal_period: 시그널 EMA 기간
                - column: 대상 컬럼 (기본값: 'close')
                
        Returns:
            MACD가 추가된 DataFrame
        """
        fast_period = params.get('fast_period', 12)
        slow_period = params.get('slow_period', 26)
        signal_period = params.get('signal_period', 9)
        column = params.get('column', 'close')
        
        # 컬럼 존재 확인
        if column not in data.columns:
            self.logger.warning(f"컬럼이 존재하지 않습니다: {column}")
            return data
        
        # 빠른 EMA 계산
        fast_ema = data[column].ewm(span=fast_period, adjust=False).mean()
        
        # 느린 EMA 계산
        slow_ema = data[column].ewm(span=slow_period, adjust=False).mean()
        
        # MACD 라인 계산
        data['MACD'] = fast_ema - slow_ema
        
        # 시그널 라인 계산
        data['MACD_SIGNAL'] = data['MACD'].ewm(span=signal_period, adjust=False).mean()
        
        # 히스토그램 계산
        data['MACD_HIST'] = data['MACD'] - data['MACD_SIGNAL']
        
        return data
    
    def normalize_data(self, data: pd.DataFrame, method: str = 'minmax') -> pd.DataFrame:
        """
        데이터 정규화
        
        Args:
            data: 정규화할 DataFrame
            method: 정규화 방법 ('minmax', 'zscore', 'robust')
                
        Returns:
            정규화된 DataFrame
        """
        self.logger.info(f"데이터 정규화 중: {method} 방법")
        
        # 데이터 복사
        result = data.copy()
        
        # 정규화 방법에 따라 처리
        if method == 'minmax':
            # Min-Max 정규화 (0-1 범위)
            for column in result.columns:
                if result[column].dtype in [np.float64, np.int64]:
                    min_val = result[column].min()
                    max_val = result[column].max()
                    if max_val > min_val:
                        result[column] = (result[column] - min_val) / (max_val - min_val)
        
        elif method == 'zscore':
            # Z-score 정규화 (평균 0, 표준편차 1)
            for column in result.columns:
                if result[column].dtype in [np.float64, np.int64]:
                    mean = result[column].mean()
                    std = result[column].std()
                    if std > 0:
                        result[column] = (result[column] - mean) / std
        
        elif method == 'robust':
            # Robust 정규화 (중앙값 0, IQR 1)
            for column in result.columns:
                if result[column].dtype in [np.float64, np.int64]:
                    median = result[column].median()
                    q1 = result[column].quantile(0.25)
                    q3 = result[column].quantile(0.75)
                    iqr = q3 - q1
                    if iqr > 0:
                        result[column] = (result[column] - median) / iqr
        
        else:
            self.logger.warning(f"지원하지 않는 정규화 방법: {method}")
        
        self.logger.info("데이터 정규화 완료")
        return result
    
    def resample_data(self, data: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        데이터 리샘플링
        
        Args:
            data: OHLCV 데이터가 포함된 DataFrame
            timeframe: 목표 시간대 ('1m', '5m', '15m', '30m', '1h', '4h', '1d')
                
        Returns:
            리샘플링된 DataFrame
        """
        self.logger.info(f"데이터 리샘플링 중: {timeframe} 시간대")
        
        # 인덱스가 datetime인지 확인
        if not isinstance(data.index, pd.DatetimeIndex):
            self.logger.error("인덱스가 datetime 형식이 아닙니다.")
            return data
        
        # 시간대 매핑
        timeframe_map = {
            '1m': '1min',
            '5m': '5min',
            '15m': '15min',
            '30m': '30min',
            '1h': '1H',
            '4h': '4H',
            '1d': '1D'
        }
        
        # 지원하는 시간대인지 확인
        if timeframe not in timeframe_map:
            self.logger.warning(f"지원하지 않는 시간대: {timeframe}")
            return data
        
        # 리샘플링 규칙
        rule = timeframe_map[timeframe]
        
        # OHLCV 데이터 리샘플링
        resampled = data.resample(rule).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        
        # NaN 값 제거
        resampled = resampled.dropna()
        
        self.logger.info(f"데이터 리샘플링 완료: {len(resampled)}개 데이터 포인트")
        return resampled