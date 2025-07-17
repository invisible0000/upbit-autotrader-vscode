#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
데이터 수집기

업비트 API를 통해 시장 데이터를 수집하고 저장하는 기능을 제공합니다.
"""

import os
import logging
import pandas as pd
import threading
import time
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from upbit_auto_trading.data_layer.collectors.upbit_api import UpbitAPI
from upbit_auto_trading.data_layer.storage.database_manager import get_database_manager

logger = logging.getLogger(__name__)

class DataCollector:
    """시장 데이터 수집 및 저장을 담당하는 클래스"""
    
    def __init__(self, api_key: str = None, secret_key: str = None):
        """DataCollector 초기화
        
        Args:
            api_key: 업비트 API 키 (없으면 환경 변수에서 로드)
            secret_key: 업비트 API 시크릿 키 (없으면 환경 변수에서 로드)
        """
        self.api = UpbitAPI(access_key=api_key, secret_key=secret_key)
        self.db_manager = get_database_manager()
        self._ensure_tables()
        
        # 수집 작업 관리를 위한 변수
        self._collection_tasks = {}
        self._stop_event = threading.Event()
    
    def _ensure_tables(self):
        """필요한 테이블이 존재하는지 확인하고, 없으면 생성합니다."""
        engine = self.db_manager.get_engine()
        
        # OHLCV 데이터 테이블 생성
        ohlcv_table_query = """
        CREATE TABLE IF NOT EXISTS ohlcv_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol VARCHAR(20) NOT NULL,
            timestamp DATETIME NOT NULL,
            open FLOAT NOT NULL,
            high FLOAT NOT NULL,
            low FLOAT NOT NULL,
            close FLOAT NOT NULL,
            volume FLOAT NOT NULL,
            timeframe VARCHAR(10) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, timestamp, timeframe)
        )
        """
        
        # 호가 데이터 테이블 생성
        orderbook_table_query = """
        CREATE TABLE IF NOT EXISTS orderbook_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol VARCHAR(20) NOT NULL,
            timestamp DATETIME NOT NULL,
            data JSON NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, timestamp)
        )
        """
        
        # 인덱스 생성
        ohlcv_index_query = """
        CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_timestamp ON ohlcv_data(symbol, timestamp)
        """
        
        orderbook_index_query = """
        CREATE INDEX IF NOT EXISTS idx_orderbook_symbol_timestamp ON orderbook_data(symbol, timestamp)
        """
        
        try:
            with engine.connect() as conn:
                conn.execute(text(ohlcv_table_query))
                conn.execute(text(orderbook_table_query))
                conn.execute(text(ohlcv_index_query))
                conn.execute(text(orderbook_index_query))
                conn.commit()
            logger.info("데이터 수집기 테이블이 생성되었습니다.")
        except Exception as e:
            logger.exception(f"테이블 생성 중 오류가 발생했습니다: {e}")
            raise
    
    def collect_ohlcv(self, symbol: str, timeframe: str, count: int = 200) -> pd.DataFrame:
        """OHLCV 데이터를 수집하고 저장합니다.
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            timeframe: 시간대 (예: "1m", "5m", "15m", "1h", "4h", "1d")
            count: 조회할 캔들 개수 (최대 200)
            
        Returns:
            pd.DataFrame: 수집된 OHLCV 데이터
        """
        try:
            # API를 통해 데이터 수집
            df = self.api.get_candles(symbol, timeframe, count)
            
            if df.empty:
                logger.warning(f"수집된 OHLCV 데이터가 없습니다: {symbol}, {timeframe}")
                return df
            
            # 데이터베이스에 저장
            self._save_ohlcv_data(df)
            
            logger.info(f"OHLCV 데이터 수집 완료: {symbol}, {timeframe}, {len(df)}개")
            return df
        except Exception as e:
            logger.exception(f"OHLCV 데이터 수집 중 오류가 발생했습니다: {e}")
            return pd.DataFrame()
    
    def collect_historical_ohlcv(self, symbol: str, timeframe: str, start_date: datetime, end_date: datetime = None) -> pd.DataFrame:
        """과거 OHLCV 데이터를 수집하고 저장합니다.
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            timeframe: 시간대 (예: "1m", "5m", "15m", "1h", "4h", "1d")
            start_date: 시작 날짜
            end_date: 종료 날짜 (기본값: 현재 시간)
            
        Returns:
            pd.DataFrame: 수집된 OHLCV 데이터
        """
        try:
            # 이미 저장된 데이터 확인
            existing_data = self.get_ohlcv_data(symbol, timeframe, start_date, end_date)
            
            if not existing_data.empty:
                logger.info(f"이미 저장된 데이터가 있습니다: {symbol}, {timeframe}, {len(existing_data)}개")
                
                # 시작 날짜와 종료 날짜 사이에 누락된 데이터가 있는지 확인
                if end_date is None:
                    end_date = datetime.now()
                
                # 데이터가 있는 날짜 범위 확인
                min_date = existing_data['timestamp'].min()
                max_date = existing_data['timestamp'].max()
                
                # 시작 날짜부터 min_date 사이에 누락된 데이터가 있으면 수집
                if start_date < min_date:
                    logger.info(f"시작 날짜({start_date})부터 기존 데이터 시작({min_date})까지의 데이터를 수집합니다.")
                    before_data = self.api.get_historical_candles(symbol, timeframe, start_date, min_date - timedelta(seconds=1))
                    if not before_data.empty:
                        self._save_ohlcv_data(before_data)
                        existing_data = pd.concat([before_data, existing_data])
                
                # max_date부터 종료 날짜 사이에 누락된 데이터가 있으면 수집
                if max_date < end_date:
                    logger.info(f"기존 데이터 종료({max_date})부터 종료 날짜({end_date})까지의 데이터를 수집합니다.")
                    after_data = self.api.get_historical_candles(symbol, timeframe, max_date + timedelta(seconds=1), end_date)
                    if not after_data.empty:
                        self._save_ohlcv_data(after_data)
                        existing_data = pd.concat([existing_data, after_data])
                
                # 중복 제거 및 정렬
                existing_data = existing_data.drop_duplicates(subset=['timestamp'])
                existing_data = existing_data.sort_values('timestamp')
                existing_data = existing_data.reset_index(drop=True)
                
                return existing_data
            
            # 저장된 데이터가 없으면 API를 통해 데이터 수집
            df = self.api.get_historical_candles(symbol, timeframe, start_date, end_date)
            
            if df.empty:
                logger.warning(f"수집된 과거 OHLCV 데이터가 없습니다: {symbol}, {timeframe}")
                return df
            
            # 데이터베이스에 저장
            self._save_ohlcv_data(df)
            
            logger.info(f"과거 OHLCV 데이터 수집 완료: {symbol}, {timeframe}, {len(df)}개")
            return df
        except Exception as e:
            logger.exception(f"과거 OHLCV 데이터 수집 중 오류가 발생했습니다: {e}")
            return pd.DataFrame()
    
    def collect_orderbook(self, symbol: str) -> Dict:
        """호가 데이터를 수집하고 저장합니다.
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            
        Returns:
            Dict: 수집된 호가 데이터
        """
        try:
            # API를 통해 데이터 수집
            orderbook = self.api.get_orderbook(symbol)
            
            if not orderbook:
                logger.warning(f"수집된 호가 데이터가 없습니다: {symbol}")
                return {}
            
            # 데이터베이스에 저장
            self._save_orderbook_data(symbol, orderbook)
            
            logger.info(f"호가 데이터 수집 완료: {symbol}")
            return orderbook
        except Exception as e:
            logger.exception(f"호가 데이터 수집 중 오류가 발생했습니다: {e}")
            return {}
    
    def _save_ohlcv_data(self, df: pd.DataFrame) -> bool:
        """OHLCV 데이터를 데이터베이스에 저장합니다.
        
        Args:
            df: OHLCV 데이터가 포함된 DataFrame
            
        Returns:
            bool: 저장 성공 여부
        """
        if df.empty:
            return False
        
        try:
            engine = self.db_manager.get_engine()
            
            # 데이터 삽입 쿼리
            insert_query = """
            INSERT OR IGNORE INTO ohlcv_data 
            (symbol, timestamp, open, high, low, close, volume, timeframe)
            VALUES (:symbol, :timestamp, :open, :high, :low, :close, :volume, :timeframe)
            """
            
            # 데이터 변환
            records = []
            for _, row in df.iterrows():
                records.append({
                    'symbol': row['symbol'],
                    'timestamp': row['timestamp'],
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume'],
                    'timeframe': row['timeframe']
                })
            
            # 데이터 삽입
            with engine.connect() as conn:
                conn.execute(text(insert_query), records)
                conn.commit()
            
            return True
        except SQLAlchemyError as e:
            logger.exception(f"OHLCV 데이터 저장 중 오류가 발생했습니다: {e}")
            return False
    
    def _save_orderbook_data(self, symbol: str, orderbook: Dict) -> bool:
        """호가 데이터를 데이터베이스에 저장합니다.
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            orderbook: 호가 데이터
            
        Returns:
            bool: 저장 성공 여부
        """
        if not orderbook:
            return False
        
        try:
            engine = self.db_manager.get_engine()
            
            # 데이터 삽입 쿼리
            insert_query = """
            INSERT OR IGNORE INTO orderbook_data 
            (symbol, timestamp, data)
            VALUES (:symbol, :timestamp, :data)
            """
            
            # 데이터 변환
            import json
            timestamp = orderbook.get('timestamp', datetime.now())
            data = json.dumps(orderbook)
            
            # 데이터 삽입
            with engine.connect() as conn:
                conn.execute(text(insert_query), {
                    'symbol': symbol,
                    'timestamp': timestamp,
                    'data': data
                })
                conn.commit()
            
            return True
        except SQLAlchemyError as e:
            logger.exception(f"호가 데이터 저장 중 오류가 발생했습니다: {e}")
            return False
    
    def get_ohlcv_data(self, symbol: str, timeframe: str, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        """저장된 OHLCV 데이터를 조회합니다.
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            timeframe: 시간대 (예: "1m", "5m", "15m", "1h", "4h", "1d")
            start_date: 시작 날짜 (기본값: None, 모든 데이터)
            end_date: 종료 날짜 (기본값: None, 현재 시간까지)
            
        Returns:
            pd.DataFrame: OHLCV 데이터
        """
        try:
            engine = self.db_manager.get_engine()
            
            # 쿼리 생성
            query = """
            SELECT symbol, timestamp, open, high, low, close, volume, timeframe
            FROM ohlcv_data
            WHERE symbol = :symbol AND timeframe = :timeframe
            """
            
            params = {
                'symbol': symbol,
                'timeframe': timeframe
            }
            
            if start_date:
                query += " AND timestamp >= :start_date"
                params['start_date'] = start_date
            
            if end_date:
                query += " AND timestamp <= :end_date"
                params['end_date'] = end_date
            
            query += " ORDER BY timestamp"
            
            # 데이터 조회
            with engine.connect() as conn:
                result = conn.execute(text(query), params)
                rows = result.fetchall()
            
            if not rows:
                return pd.DataFrame()
            
            # DataFrame 생성
            df = pd.DataFrame(rows, columns=['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume', 'timeframe'])
            
            # 타임스탬프 변환
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            return df
        except SQLAlchemyError as e:
            logger.exception(f"OHLCV 데이터 조회 중 오류가 발생했습니다: {e}")
            return pd.DataFrame()
    
    def get_orderbook_data(self, symbol: str, start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """저장된 호가 데이터를 조회합니다.
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            start_date: 시작 날짜 (기본값: None, 모든 데이터)
            end_date: 종료 날짜 (기본값: None, 현재 시간까지)
            
        Returns:
            List[Dict]: 호가 데이터 목록
        """
        try:
            engine = self.db_manager.get_engine()
            
            # 쿼리 생성
            query = """
            SELECT symbol, timestamp, data
            FROM orderbook_data
            WHERE symbol = :symbol
            """
            
            params = {
                'symbol': symbol
            }
            
            if start_date:
                query += " AND timestamp >= :start_date"
                params['start_date'] = start_date
            
            if end_date:
                query += " AND timestamp <= :end_date"
                params['end_date'] = end_date
            
            query += " ORDER BY timestamp"
            
            # 데이터 조회
            with engine.connect() as conn:
                result = conn.execute(text(query), params)
                rows = result.fetchall()
            
            if not rows:
                return []
            
            # 데이터 변환
            import json
            orderbooks = []
            for row in rows:
                orderbook = json.loads(row[2])
                orderbook['timestamp'] = row[1]
                orderbooks.append(orderbook)
            
            return orderbooks
        except SQLAlchemyError as e:
            logger.exception(f"호가 데이터 조회 중 오류가 발생했습니다: {e}")
            return []
    
    def start_ohlcv_collection(self, symbol: str, timeframe: str, interval_seconds: int = 60) -> bool:
        """주기적인 OHLCV 데이터 수집을 시작합니다.
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            timeframe: 시간대 (예: "1m", "5m", "15m", "1h", "4h", "1d")
            interval_seconds: 수집 간격 (초)
            
        Returns:
            bool: 수집 시작 성공 여부
        """
        task_key = f"ohlcv_{symbol}_{timeframe}"
        
        # 이미 실행 중인 작업이 있으면 중지
        if task_key in self._collection_tasks:
            self.stop_collection(task_key)
        
        # 수집 작업 스레드 생성
        thread = threading.Thread(
            target=self._ohlcv_collection_task,
            args=(symbol, timeframe, interval_seconds),
            daemon=True
        )
        
        # 작업 정보 저장
        self._collection_tasks[task_key] = {
            'thread': thread,
            'type': 'ohlcv',
            'symbol': symbol,
            'timeframe': timeframe,
            'interval': interval_seconds,
            'start_time': datetime.now()
        }
        
        # 스레드 시작
        thread.start()
        
        logger.info(f"OHLCV 데이터 수집 작업 시작: {symbol}, {timeframe}, 간격: {interval_seconds}초")
        return True
    
    def start_orderbook_collection(self, symbol: str, interval_seconds: int = 1) -> bool:
        """주기적인 호가 데이터 수집을 시작합니다.
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            interval_seconds: 수집 간격 (초)
            
        Returns:
            bool: 수집 시작 성공 여부
        """
        task_key = f"orderbook_{symbol}"
        
        # 이미 실행 중인 작업이 있으면 중지
        if task_key in self._collection_tasks:
            self.stop_collection(task_key)
        
        # 수집 작업 스레드 생성
        thread = threading.Thread(
            target=self._orderbook_collection_task,
            args=(symbol, interval_seconds),
            daemon=True
        )
        
        # 작업 정보 저장
        self._collection_tasks[task_key] = {
            'thread': thread,
            'type': 'orderbook',
            'symbol': symbol,
            'interval': interval_seconds,
            'start_time': datetime.now()
        }
        
        # 스레드 시작
        thread.start()
        
        logger.info(f"호가 데이터 수집 작업 시작: {symbol}, 간격: {interval_seconds}초")
        return True
    
    def stop_collection(self, task_key: str) -> bool:
        """데이터 수집 작업을 중지합니다.
        
        Args:
            task_key: 작업 키
            
        Returns:
            bool: 중지 성공 여부
        """
        if task_key not in self._collection_tasks:
            logger.warning(f"중지할 수집 작업이 없습니다: {task_key}")
            return False
        
        # 중지 이벤트 설정
        self._stop_event.set()
        
        # 스레드 종료 대기
        thread = self._collection_tasks[task_key]['thread']
        if thread.is_alive():
            thread.join(timeout=5)
        
        # 작업 정보 삭제
        del self._collection_tasks[task_key]
        
        # 중지 이벤트 초기화
        self._stop_event.clear()
        
        logger.info(f"데이터 수집 작업 중지: {task_key}")
        return True
    
    def stop_all_collections(self) -> bool:
        """모든 데이터 수집 작업을 중지합니다.
        
        Returns:
            bool: 중지 성공 여부
        """
        if not self._collection_tasks:
            logger.info("중지할 수집 작업이 없습니다.")
            return True
        
        # 중지 이벤트 설정
        self._stop_event.set()
        
        # 모든 스레드 종료 대기
        for task_key, task_info in list(self._collection_tasks.items()):
            thread = task_info['thread']
            if thread.is_alive():
                thread.join(timeout=5)
            
            # 작업 정보 삭제
            del self._collection_tasks[task_key]
        
        # 중지 이벤트 초기화
        self._stop_event.clear()
        
        logger.info("모든 데이터 수집 작업이 중지되었습니다.")
        return True
    
    def get_collection_status(self) -> Dict:
        """현재 실행 중인 데이터 수집 작업 상태를 반환합니다.
        
        Returns:
            Dict: 작업 상태 정보
        """
        status = {}
        
        for task_key, task_info in self._collection_tasks.items():
            # 스레드 상태 확인
            thread = task_info['thread']
            is_alive = thread.is_alive()
            
            # 작업 정보 복사
            task_status = task_info.copy()
            task_status['is_alive'] = is_alive
            task_status['running_time'] = (datetime.now() - task_info['start_time']).total_seconds()
            
            # 스레드 객체 제거 (JSON 직렬화 불가)
            del task_status['thread']
            
            status[task_key] = task_status
        
        return status
    
    def _ohlcv_collection_task(self, symbol: str, timeframe: str, interval_seconds: int):
        """OHLCV 데이터 수집 작업을 실행합니다.
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            timeframe: 시간대 (예: "1m", "5m", "15m", "1h", "4h", "1d")
            interval_seconds: 수집 간격 (초)
        """
        logger.info(f"OHLCV 수집 작업 시작: {symbol}, {timeframe}")
        
        while not self._stop_event.is_set():
            try:
                # OHLCV 데이터 수집
                self.collect_ohlcv(symbol, timeframe)
                
                # 다음 수집까지 대기
                self._stop_event.wait(interval_seconds)
            except Exception as e:
                logger.exception(f"OHLCV 수집 작업 중 오류 발생: {e}")
                
                # 오류 발생 시 잠시 대기 후 재시도
                self._stop_event.wait(10)
        
        logger.info(f"OHLCV 수집 작업 종료: {symbol}, {timeframe}")
    
    def _orderbook_collection_task(self, symbol: str, interval_seconds: int):
        """호가 데이터 수집 작업을 실행합니다.
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            interval_seconds: 수집 간격 (초)
        """
        logger.info(f"호가 수집 작업 시작: {symbol}")
        
        while not self._stop_event.is_set():
            try:
                # 호가 데이터 수집
                self.collect_orderbook(symbol)
                
                # 다음 수집까지 대기
                self._stop_event.wait(interval_seconds)
            except Exception as e:
                logger.exception(f"호가 수집 작업 중 오류 발생: {e}")
                
                # 오류 발생 시 잠시 대기 후 재시도
                self._stop_event.wait(10)
        
        logger.info(f"호가 수집 작업 종료: {symbol}")
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict:
        """오래된 데이터를 정리합니다.
        
        Args:
            days_to_keep: 보관할 일수
            
        Returns:
            Dict: 정리 결과
        """
        try:
            engine = self.db_manager.get_engine()
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # OHLCV 데이터 정리
            ohlcv_query = """
            DELETE FROM ohlcv_data
            WHERE timestamp < :cutoff_date
            """
            
            # 호가 데이터 정리
            orderbook_query = """
            DELETE FROM orderbook_data
            WHERE timestamp < :cutoff_date
            """
            
            # 쿼리 실행
            with engine.connect() as conn:
                ohlcv_result = conn.execute(text(ohlcv_query), {'cutoff_date': cutoff_date})
                orderbook_result = conn.execute(text(orderbook_query), {'cutoff_date': cutoff_date})
                conn.commit()
            
            # 결과 반환
            result = {
                'ohlcv_deleted': ohlcv_result.rowcount,
                'orderbook_deleted': orderbook_result.rowcount,
                'cutoff_date': cutoff_date
            }
            
            logger.info(f"오래된 데이터 정리 완료: {result}")
            return result
        except SQLAlchemyError as e:
            logger.exception(f"데이터 정리 중 오류가 발생했습니다: {e}")
            return {
                'error': str(e),
                'ohlcv_deleted': 0,
                'orderbook_deleted': 0,
                'cutoff_date': cutoff_date
            }