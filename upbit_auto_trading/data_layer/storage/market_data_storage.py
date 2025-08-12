"""
시장 데이터 저장소 모듈 (SQLite3 직접 사용)

이 모듈은 시장 데이터의 저장 및 로드 기능을 제공합니다.
"""
import pandas as pd
import sqlite3
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

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
        self.db_path = "data/upbit_auto_trading.sqlite3"
        
        # data 디렉토리 생성
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # 테이블 초기화
        self._init_tables()
    
    def _init_tables(self):
        """데이터베이스 테이블 초기화"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
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
            
            conn.commit()
            conn.close()
            self.logger.info("데이터베이스 테이블 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"테이블 초기화 실패: {e}")
    
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
            if 'timestamp' in df.columns and hasattr(df['timestamp'].iloc[0], 'strftime'):
                df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # 필수 컬럼 확인
            required_columns = ['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'timeframe']
            for col in required_columns:
                if col not in df.columns:
                    self.logger.error(f"필수 컬럼이 없습니다: {col}")
                    return False
            
            # 데이터베이스 연결
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 중복 시 교체하도록 데이터 삽입
            for _, row in df[required_columns].iterrows():
                cursor.execute('''
                    INSERT OR REPLACE INTO market_data 
                    (timestamp, symbol, open, high, low, close, volume, timeframe)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['timestamp'], row['symbol'], row['open'], row['high'], 
                    row['low'], row['close'], row['volume'], row['timeframe']
                ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"시장 데이터 저장 완료: {len(df)}개 데이터 포인트")
            return True
            
        except Exception as e:
            self.logger.error(f"시장 데이터 저장 중 오류 발생: {str(e)}")
            return False
    
    def load_market_data(self, symbol: str, timeframe: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        시장 데이터 로드
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            timeframe: 시간대 (예: "1d", "4h", "1h")
            start_date: 시작 날짜
            end_date: 종료 날짜
            
        Returns:
            로드된 OHLCV 데이터
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT timestamp, symbol, open, high, low, close, volume, timeframe
                FROM market_data
                WHERE symbol = ? AND timeframe = ? 
                AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp ASC
            '''
            
            start_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
            end_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
            
            df = pd.read_sql_query(query, conn, params=(symbol, timeframe, start_str, end_str))
            conn.close()
            
            if not df.empty:
                # timestamp를 datetime으로 변환
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            
            self.logger.info(f"시장 데이터 로드 완료: {len(df)}개 데이터 포인트")
            return df
            
        except Exception as e:
            self.logger.error(f"시장 데이터 로드 중 오류 발생: {str(e)}")
            return pd.DataFrame()
    
    def get_available_symbols(self) -> List[str]:
        """
        저장된 심볼 목록 조회
        
        Returns:
            사용 가능한 심볼 목록
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = 'SELECT DISTINCT symbol FROM market_data ORDER BY symbol'
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df['symbol'].tolist() if not df.empty else []
            
        except Exception as e:
            self.logger.error(f"심볼 목록 조회 중 오류 발생: {str(e)}")
            return []
    
    def cleanup_old_data(self, days_to_keep: int) -> int:
        """
        오래된 시장 데이터 정리
        
        Args:
            days_to_keep: 보관할 일수
            
        Returns:
            삭제된 레코드 수
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 삭제 기준일 계산
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d %H:%M:%S')
            
            # 삭제 전 레코드 수 확인
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
            
            conn.close()
            self.logger.info(f"오래된 데이터 정리 완료: {deleted_count}개 레코드 삭제")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"데이터 정리 중 오류 발생: {str(e)}")
            return 0
