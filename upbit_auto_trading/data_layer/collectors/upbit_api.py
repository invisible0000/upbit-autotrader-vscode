#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
업비트 API 클라이언트

업비트 API를 통해 시장 데이터를 수집하는 기능을 제공합니다.
"""

import os
import jwt
import uuid
import hashlib
import logging
import requests
import pandas as pd
from urllib.parse import urlencode
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class UpbitAPI:
    """업비트 API 클라이언트 클래스"""
    
    BASE_URL = "https://api.upbit.com/v1"
    WEBSOCKET_URL = "wss://api.upbit.com/websocket/v1"
    
    def __init__(self, access_key: str = None, secret_key: str = None):
        """UpbitAPI 초기화
        
        Args:
            access_key: 업비트 API 액세스 키 (없으면 환경 변수에서 로드)
            secret_key: 업비트 API 시크릿 키 (없으면 환경 변수에서 로드)
        """
        self.access_key = access_key or os.environ.get("UPBIT_ACCESS_KEY")
        self.secret_key = secret_key or os.environ.get("UPBIT_SECRET_KEY")
        
        if not self.access_key or not self.secret_key:
            logger.warning("API 키가 설정되지 않았습니다. 일부 기능이 제한될 수 있습니다.")
    
    def _get_auth_header(self, query: Dict = None) -> Dict:
        """인증 헤더를 생성합니다.
        
        Args:
            query: 쿼리 파라미터 (선택적)
            
        Returns:
            Dict: 인증 헤더
        """
        if not self.access_key or not self.secret_key:
            return {}
        
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4())
        }
        
        if query:
            query_string = urlencode(query)
            m = hashlib.sha512()
            m.update(query_string.encode())
            query_hash = m.hexdigest()
            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = 'SHA512'
        
        jwt_token = jwt.encode(payload, self.secret_key)
        return {'Authorization': f'Bearer {jwt_token}'}
    
    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """API 요청을 보냅니다.
        
        Args:
            method: HTTP 메서드 ('GET', 'POST', 'DELETE' 등)
            endpoint: API 엔드포인트 (예: '/candles/minutes/1')
            params: 쿼리 파라미터 (선택적)
            data: 요청 데이터 (선택적)
            
        Returns:
            Dict: API 응답
            
        Raises:
            requests.exceptions.RequestException: API 요청 실패 시
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_auth_header(params)
        
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API 요청 실패: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"응답 내용: {e.response.text}")
            raise
    
    def get_markets(self) -> pd.DataFrame:
        """마켓 코드 조회
        
        Returns:
            pd.DataFrame: 마켓 코드 정보
        """
        try:
            response = self._request('GET', '/market/all')
            df = pd.DataFrame(response)
            # KRW 마켓만 필터링
            df = df[df['market'].str.startswith('KRW-')]
            return df
        except Exception as e:
            logger.exception(f"마켓 코드 조회 중 오류가 발생했습니다: {e}")
            return pd.DataFrame()
    
    def get_candles(self, symbol: str, timeframe: str, count: int = 200) -> pd.DataFrame:
        """캔들 데이터 조회
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            timeframe: 시간대 (예: "1m", "5m", "15m", "1h", "4h", "1d")
            count: 조회할 캔들 개수 (최대 200)
            
        Returns:
            pd.DataFrame: OHLCV 데이터
        """
        try:
            # 시간대에 따라 다른 엔드포인트 사용
            if timeframe.endswith('m'):
                minutes = int(timeframe[:-1])
                endpoint = f'/candles/minutes/{minutes}'
            elif timeframe.endswith('h'):
                hours = int(timeframe[:-1])
                if hours == 1:
                    endpoint = '/candles/minutes/60'
                elif hours == 4:
                    endpoint = '/candles/minutes/240'
                else:
                    raise ValueError(f"지원하지 않는 시간대입니다: {timeframe}")
            elif timeframe == '1d':
                endpoint = '/candles/days'
            elif timeframe == '1w':
                endpoint = '/candles/weeks'
            elif timeframe == '1M':
                endpoint = '/candles/months'
            else:
                raise ValueError(f"지원하지 않는 시간대입니다: {timeframe}")
            
            params = {
                'market': symbol,
                'count': min(count, 200)  # 최대 200개
            }
            
            response = self._request('GET', endpoint, params=params)
            
            # 데이터프레임으로 변환
            df = pd.DataFrame(response)
            
            # 컬럼 이름 변경
            if 'candle_date_time_utc' in df.columns:
                df['timestamp'] = pd.to_datetime(df['candle_date_time_utc'])
            elif 'candle_date_time_kst' in df.columns:
                df['timestamp'] = pd.to_datetime(df['candle_date_time_kst'])
            
            # 필요한 컬럼만 선택
            columns = ['timestamp', 'opening_price', 'high_price', 'low_price', 'trade_price', 'candle_acc_trade_volume']
            if all(col in df.columns for col in columns):
                df = df[columns]
                df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                
                # 시간 순서대로 정렬
                df = df.sort_values('timestamp')
                
                # 인덱스 재설정
                df = df.reset_index(drop=True)
                
                # 시간대 정보 추가
                df['timeframe'] = timeframe
                df['symbol'] = symbol
                
                return df
            else:
                logger.error(f"예상치 못한 응답 형식: {df.columns}")
                return pd.DataFrame()
            
        except Exception as e:
            logger.exception(f"캔들 데이터 조회 중 오류가 발생했습니다: {e}")
            return pd.DataFrame()
    
    def get_orderbook(self, symbol: str) -> Dict:
        """호가 데이터 조회
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            
        Returns:
            Dict: 호가 정보
        """
        try:
            params = {'markets': symbol}
            response = self._request('GET', '/orderbook', params=params)
            
            if response and isinstance(response, list) and len(response) > 0:
                orderbook = response[0]
                
                # 타임스탬프 변환
                if 'timestamp' in orderbook:
                    orderbook['timestamp'] = datetime.fromtimestamp(orderbook['timestamp'] / 1000)
                
                return orderbook
            else:
                logger.error(f"호가 데이터 없음: {response}")
                return {}
            
        except Exception as e:
            logger.exception(f"호가 데이터 조회 중 오류가 발생했습니다: {e}")
            return {}
    
    def get_tickers(self, symbols: List[str] = None) -> pd.DataFrame:
        """티커 데이터 조회
        
        Args:
            symbols: 코인 심볼 목록 (None인 경우 모든 KRW 마켓 코인)
            
        Returns:
            pd.DataFrame: 티커 정보
        """
        try:
            if not symbols:
                # 모든 KRW 마켓 코인 조회
                markets_df = self.get_markets()
                if markets_df.empty:
                    return pd.DataFrame()
                symbols = markets_df['market'].tolist()
            
            # 한 번에 최대 100개까지 조회 가능
            chunks = [symbols[i:i+100] for i in range(0, len(symbols), 100)]
            all_tickers = []
            
            for chunk in chunks:
                params = {'markets': ','.join(chunk)}
                response = self._request('GET', '/ticker', params=params)
                all_tickers.extend(response)
            
            df = pd.DataFrame(all_tickers)
            
            # 타임스탬프 변환
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
            
        except Exception as e:
            logger.exception(f"티커 데이터 조회 중 오류가 발생했습니다: {e}")
            return pd.DataFrame()
    
    def get_account(self) -> List[Dict]:
        """계좌 정보 조회
        
        Returns:
            List[Dict]: 계좌 정보 목록
        """
        try:
            response = self._request('GET', '/accounts')
            return response
        except Exception as e:
            logger.exception(f"계좌 정보 조회 중 오류가 발생했습니다: {e}")
            return []
    
    def place_order(self, symbol: str, side: str, volume: float = None, price: float = None, ord_type: str = 'limit') -> Dict:
        """주문 실행
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            side: 주문 방향 ('bid': 매수, 'ask': 매도)
            volume: 주문량 (지정가 주문 시 필수)
            price: 주문 가격 (지정가 주문 시 필수)
            ord_type: 주문 유형 ('limit': 지정가, 'price': 시장가 매수, 'market': 시장가 매도)
            
        Returns:
            Dict: 주문 정보
        """
        try:
            if not self.access_key or not self.secret_key:
                raise ValueError("API 키가 설정되지 않았습니다.")
            
            params = {
                'market': symbol,
                'side': side,
                'ord_type': ord_type
            }
            
            if ord_type == 'limit':
                if volume is None or price is None:
                    raise ValueError("지정가 주문에는 volume과 price가 필요합니다.")
                params['volume'] = str(volume)
                params['price'] = str(price)
            elif ord_type == 'price':
                if price is None:
                    raise ValueError("시장가 매수 주문에는 price가 필요합니다.")
                params['price'] = str(price)
            elif ord_type == 'market':
                if volume is None:
                    raise ValueError("시장가 매도 주문에는 volume이 필요합니다.")
                params['volume'] = str(volume)
            
            response = self._request('POST', '/orders', params=params)
            return response
            
        except Exception as e:
            logger.exception(f"주문 실행 중 오류가 발생했습니다: {e}")
            raise