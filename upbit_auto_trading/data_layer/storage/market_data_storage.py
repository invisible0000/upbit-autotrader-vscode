"""
시장 데이터 저장소 모듈

이 모듈은 시장 데이터의 저장 및 로드 기능을 제공합니다.
"""
import pandas as pd
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from upbit_auto_trading.data_layer.storage.database_manager import DatabaseManager


class MarketDataStorage:
    """
    시장 데이터 저장소 클래스
    
    이 클래스는 시장 데이터의 저장 및 로드 기능을 제공합니다.
    """
    
    def __init__(self):
        """
        시장 데이터 저장소 초기화
        """
        self.logger = logging.getLogger(__name__)
        self.db_manager = DatabaseManager()
    
    def save_market_data(self, data: pd.DataFrame) -> bool:
        """
        시장 데이터 저장
        
        Args:
            data: 저장할 OHLCV 데이터가 포함된 DataFrame
                - 인덱스: timestamp (datetime)
                - 컬럼: symbol, open, high, low, close, volume, timeframe
                
        Returns:
            저장 성공 여부
        """
        self.logger.info(f"시장 데이터 저장 중: {len(data)}개 데이터 포인트")
        
        if data.empty:
            self.logger.warning("저장할 데이터가 없습니다.")
            return False
        
        try:
            # 데이터 준비
            df = data.copy()
            
            # 인덱스가 timestamp인 경우 컬럼으로 변환
            if isinstance(df.index, pd.DatetimeIndex):
                df = df.reset_index()
            
            # timestamp가 datetime 객체인 경우 문자열로 변환
            if 'timestamp' in df.columns and isinstance(df['timestamp'].iloc[0], datetime):
                df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # 필수 컬럼 확인
            required_columns = ['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'timeframe']
            for col in required_columns:
                if col not in df.columns:
                    self.logger.error(f"필수 컬럼이 없습니다: {col}")
                    return False
            
            # 데이터베이스 연결
            engine = self.db_manager.get_engine()
            conn = engine.connect()
            
            # 테이블 생성 (없는 경우)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS market_data (
                    timestamp TEXT,
                    symbol TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    timeframe TEXT,
                    PRIMARY KEY (timestamp, symbol, timeframe)
                )
            ''')
            
            # 데이터 삽입
            df[required_columns].to_sql('market_data', conn, if_exists='append', index=False)
            
            conn.commit()
            self.logger.info(f"시장 데이터 저장 완료: {len(df)}개 데이터 포인트")
            return True
            
        except Exception as e:
            self.logger.error(f"시장 데이터 저장 중 오류 발생: {str(e)}")
            return False
    
    def load_market_data(self, symbol: str, timeframe: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        시장 데이터 로드
        
        Args:
            symbol: 코인 심볼 (예: 'KRW-BTC')
            timeframe: 시간대 (예: '1m', '5m', '1h', '1d')
            start_date: 시작 날짜
            end_date: 종료 날짜
            
        Returns:
            OHLCV 데이터가 포함된 DataFrame
        """
        self.logger.info(f"시장 데이터 로드 중: {symbol}, {timeframe}, {start_date} ~ {end_date}")
        
        try:
            # 데이터베이스 연결
            engine = self.db_manager.get_engine()
            conn = engine.connect()
            
            # 쿼리 실행
            query = '''
                SELECT timestamp, open, high, low, close, volume
                FROM market_data
                WHERE symbol = ? AND timeframe = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            '''
            
            # 날짜 형식 변환
            start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
            end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
            
            # 데이터 로드
            df = pd.read_sql_query(
                query,
                conn,
                params=(symbol, timeframe, start_date_str, end_date_str)
            )
            
            # timestamp를 datetime으로 변환
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # timestamp를 인덱스로 설정
            df.set_index('timestamp', inplace=True)
            
            self.logger.info(f"시장 데이터 로드 완료: {len(df)}개 데이터 포인트")
            return df
            
        except Exception as e:
            self.logger.error(f"시장 데이터 로드 중 오류 발생: {str(e)}")
            # 오류 발생 시 빈 DataFrame 반환
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
    
    def cleanup_old_data(self, days_to_keep: int) -> int:
        """
        오래된 데이터 정리
        
        Args:
            days_to_keep: 보관할 일수
            
        Returns:
            삭제된 레코드 수
        """
        self.logger.info(f"오래된 데이터 정리 중: {days_to_keep}일 이전 데이터 삭제")
        
        try:
            # 데이터베이스 연결
            engine = self.db_manager.get_engine()
            conn = engine.connect()
            
            # 삭제 기준일 계산
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d %H:%M:%S')
            
            # 삭제 전 레코드 수 확인
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM market_data')
            before_count = cursor.fetchone()[0]
            
            # 오래된 데이터 삭제
            cursor.execute('DELETE FROM market_data WHERE timestamp < ?', (cutoff_date,))
            conn.commit()
            
            # 삭제 후 레코드 수 확인
            cursor.execute('SELECT COUNT(*) FROM market_data')
            after_count = cursor.fetchone()[0]
            
            # 삭제된 레코드 수 계산
            deleted_count = before_count - after_count
            
            self.logger.info(f"오래된 데이터 정리 완료: {deleted_count}개 레코드 삭제")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"오래된 데이터 정리 중 오류 발생: {str(e)}")
            return 0