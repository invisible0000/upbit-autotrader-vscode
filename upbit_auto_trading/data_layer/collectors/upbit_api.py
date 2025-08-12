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
import time
import json
import threading
from urllib.parse import urlencode
from typing import Dict, List, Optional, Union, Any, Tuple, Callable
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from functools import wraps

logger = logging.getLogger(__name__)

def retry_on_exception(max_retries=3, retry_delay=1, backoff_factor=2, exceptions=(Exception,)):
    """예외 발생 시 재시도하는 데코레이터
    
    Args:
        max_retries: 최대 재시도 횟수
        retry_delay: 초기 재시도 대기 시간(초)
        backoff_factor: 재시도 간격 증가 계수
        exceptions: 재시도할 예외 유형 튜플
        
    Returns:
        Callable: 데코레이터 함수
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            delay = retry_delay
            
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"최대 재시도 횟수({max_retries})에 도달했습니다: {e}")
                        raise
                    
                    logger.warning(f"예외 발생, {delay}초 후 재시도 ({retries}/{max_retries}): {e}")
                    time.sleep(delay)
                    delay *= backoff_factor
        
        return wrapper
    
    return decorator

class UpbitAPI:
    """업비트 API 클라이언트 클래스"""
    
    BASE_URL = "https://api.upbit.com/v1"
    WEBSOCKET_URL = "wss://api.upbit.com/websocket/v1"
    
    # API 요청 제한 설정
    RATE_LIMIT_PER_SEC = 10  # 초당 최대 요청 수
    RATE_LIMIT_PER_MIN = 600  # 분당 최대 요청 수
    
    # 요청 제한 관리를 위한 락
    _rate_limit_lock = threading.RLock()
    
    def __init__(self, access_key: str = None, secret_key: str = None):
        """UpbitAPI 초기화
        
        Args:
            access_key: 업비트 API 액세스 키 (없으면 환경 변수에서 로드)
            secret_key: 업비트 API 시크릿 키 (없으면 환경 변수에서 로드)
        """
        self.access_key = access_key or os.environ.get("UPBIT_ACCESS_KEY")
        self.secret_key = secret_key or os.environ.get("UPBIT_SECRET_KEY")
        
        if not self.access_key or not self.secret_key:
            # API 키가 없어도 공개 API는 사용 가능하므로 debug 레벨로 변경
            logger.debug("API 키가 설정되지 않았습니다. 공개 API만 사용 가능합니다.")
            
        # 요청 제한 관리를 위한 변수
        self.request_timestamps = []
        
        # 재시도 설정으로 HTTP 세션 생성
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """재시도 로직이 포함된 HTTP 세션을 생성합니다.
        
        Returns:
            requests.Session: HTTP 세션
        """
        session = requests.Session()
        
        # 재시도 전략 설정
        retry_strategy = Retry(
            total=5,                      # 최대 재시도 횟수
            backoff_factor=0.5,           # 재시도 간격 계수
            status_forcelist=[429, 500, 502, 503, 504],  # 재시도할 HTTP 상태 코드
            allowed_methods=["GET", "POST", "DELETE"]    # 재시도할 HTTP 메서드 (최신 버전에서는 method_whitelist 대신 allowed_methods 사용)
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def _check_rate_limit(self) -> None:
        """API 요청 제한을 확인하고 필요시 대기합니다.
        
        스레드 안전하게 요청 제한을 관리합니다.
        """
        with self._rate_limit_lock:
            now = time.time()
            
            # 1분 이상 지난 타임스탬프 제거
            self.request_timestamps = [ts for ts in self.request_timestamps if now - ts < 60]
            
            # 분당 요청 제한 확인
            if len(self.request_timestamps) >= self.RATE_LIMIT_PER_MIN:
                # 가장 오래된 요청이 1분 이상 지날 때까지 대기
                oldest = self.request_timestamps[0]
                sleep_time = 60 - (now - oldest)
                if sleep_time > 0:
                    logger.warning(f"분당 요청 제한에 도달했습니다. {sleep_time:.2f}초 대기합니다.")
                    time.sleep(sleep_time)
                    # 대기 후 타임스탬프 갱신
                    self.request_timestamps = [ts for ts in self.request_timestamps if time.time() - ts < 60]
                    # 분당 제한 처리 후 초당 제한은 확인하지 않음
                    self.request_timestamps.append(time.time())
                    return
            
            # 초당 요청 제한 확인
            recent_requests = [ts for ts in self.request_timestamps if now - ts < 1]
            if len(recent_requests) >= self.RATE_LIMIT_PER_SEC:
                sleep_time = 1.0
                logger.debug(f"초당 요청 제한에 도달했습니다. {sleep_time:.2f}초 대기합니다.")
                time.sleep(sleep_time)
            
            # 현재 요청 타임스탬프 추가
            self.request_timestamps.append(time.time())
    
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
    
    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None, retry_count: int = 3) -> Dict:
        """API 요청을 보냅니다.
        
        Args:
            method: HTTP 메서드 ('GET', 'POST', 'DELETE' 등)
            endpoint: API 엔드포인트 (예: '/candles/minutes/1')
            params: 쿼리 파라미터 (선택적)
            data: 요청 데이터 (선택적)
            retry_count: 재시도 횟수 (기본값: 3)
            
        Returns:
            Dict: API 응답
            
        Raises:
            requests.exceptions.RequestException: API 요청 실패 시
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_auth_header(params)
        
        # API 요청 제한 확인
        self._check_rate_limit()
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers,
                timeout=(5, 30)  # 연결 타임아웃 5초, 읽기 타임아웃 30초
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # 429 Too Many Requests 오류 처리
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 429:
                retry_after = int(e.response.headers.get('Retry-After', 10))
                logger.warning(f"API 요청 제한 초과. {retry_after}초 후 재시도합니다.")
                time.sleep(retry_after)
                if retry_count > 0:
                    return self._request(method, endpoint, params, data, retry_count - 1)
            
            # 기타 오류 처리
            logger.error(f"API 요청 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"응답 상태 코드: {e.response.status_code}")
                logger.error(f"응답 내용: {e.response.text}")
            
            # 일시적인 오류인 경우 재시도
            if retry_count > 0 and (not hasattr(e, 'response') or e.response is None or e.response.status_code >= 500):
                retry_delay = (4 - retry_count) * 2  # 점진적으로 대기 시간 증가
                logger.info(f"{retry_delay}초 후 재시도합니다. (남은 재시도: {retry_count})")
                time.sleep(retry_delay)
                return self._request(method, endpoint, params, data, retry_count - 1)
            
            raise
    
    def get_markets(self) -> pd.DataFrame:
        """마켓 코드 조회
        
        Returns:
            pd.DataFrame: 마켓 코드 정보
        """
        try:
            response = self._request('GET', '/market/all')
            if not response:
                logger.error("마켓 코드 응답이 비어있습니다.")
                return pd.DataFrame()
                
            df = pd.DataFrame(response)
            
            # 응답에 'market' 컬럼이 있는지 확인
            if 'market' not in df.columns:
                logger.error(f"마켓 코드 응답에 'market' 컬럼이 없습니다. 컬럼: {df.columns}")
                return pd.DataFrame()
                
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
    
    def get_candles_before(self, symbol: str, timeframe: str, before_timestamp: datetime, count: int = 200) -> pd.DataFrame:
        """특정 시점 이전의 캔들 데이터 조회 (무한 스크롤용)
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            timeframe: 시간대 (예: "1m", "5m", "15m", "1h", "4h", "1d")
            before_timestamp: 이 시점 이전의 데이터를 조회
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
            
            # 'to' 파라미터로 특정 시점 이전 데이터 요청
            # 업비트 API는 ISO 8601 형식을 사용
            to_param = before_timestamp.strftime('%Y-%m-%dT%H:%M:%S')
            
            params = {
                'market': symbol,
                'count': min(count, 200),  # 최대 200개
                'to': to_param
            }
            
            response = self._request('GET', endpoint, params=params)
            
            # 데이터프레임으로 변환
            df = pd.DataFrame(response)
            
            if df.empty:
                logger.warning(f"특정 시점({before_timestamp}) 이전의 데이터가 없습니다.")
                return pd.DataFrame()
            
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
                
                logger.info(f"과거 데이터 조회 성공: {len(df)}개 캔들 ({before_timestamp} 이전)")
                
                return df
            else:
                logger.error(f"예상치 못한 응답 형식: {df.columns}")
                return pd.DataFrame()
            
        except Exception as e:
            logger.exception(f"과거 캔들 데이터 조회 중 오류가 발생했습니다: {e}")
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
    
    def get_order(self, uuid: str = None, identifier: str = None) -> Dict:
        """개별 주문 조회
        
        Args:
            uuid: 주문 UUID (uuid와 identifier 중 하나는 필수)
            identifier: 조회용 사용자 지정 값
            
        Returns:
            Dict: 주문 정보
        """
        try:
            if not uuid and not identifier:
                raise ValueError("uuid와 identifier 중 하나는 필수입니다.")
            
            params = {}
            if uuid:
                params['uuid'] = uuid
            if identifier:
                params['identifier'] = identifier
            
            response = self._request('GET', '/order', params=params)
            return response
        except Exception as e:
            logger.exception(f"주문 조회 중 오류가 발생했습니다: {e}")
            return {}
    
    def get_orders(self, symbol: str = None, state: str = None, page: int = 1, limit: int = 100) -> List[Dict]:
        """주문 목록 조회
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC") (선택적)
            state: 주문 상태 ('wait', 'watch', 'done', 'cancel') (선택적)
            page: 페이지 번호 (선택적)
            limit: 페이지당 개수 (최대 100) (선택적)
            
        Returns:
            List[Dict]: 주문 목록
        """
        try:
            params = {
                'page': page,
                'limit': min(limit, 100)
            }
            
            if symbol:
                params['market'] = symbol
            if state:
                params['state'] = state
            
            response = self._request('GET', '/orders', params=params)
            return response
        except Exception as e:
            logger.exception(f"주문 목록 조회 중 오류가 발생했습니다: {e}")
            return []
    
    def cancel_order(self, uuid: str = None, identifier: str = None) -> Dict:
        """주문 취소
        
        Args:
            uuid: 주문 UUID (uuid와 identifier 중 하나는 필수)
            identifier: 조회용 사용자 지정 값
            
        Returns:
            Dict: 취소된 주문 정보
        """
        try:
            if not uuid and not identifier:
                raise ValueError("uuid와 identifier 중 하나는 필수입니다.")
            
            params = {}
            if uuid:
                params['uuid'] = uuid
            if identifier:
                params['identifier'] = identifier
            
            response = self._request('DELETE', '/order', params=params)
            return response
        except Exception as e:
            logger.exception(f"주문 취소 중 오류가 발생했습니다: {e}")
            raise
    
    def get_trades_ticks(self, symbol: str, count: int = 100) -> pd.DataFrame:
        """최근 체결 내역 조회
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            count: 조회할 체결 개수 (최대 500)
            
        Returns:
            pd.DataFrame: 체결 내역
        """
        try:
            params = {
                'market': symbol,
                'count': min(count, 500)
            }
            
            response = self._request('GET', '/trades/ticks', params=params)
            
            # 데이터프레임으로 변환
            df = pd.DataFrame(response)
            
            # 타임스탬프 변환
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
        except Exception as e:
            logger.exception(f"체결 내역 조회 중 오류가 발생했습니다: {e}")
            return pd.DataFrame()
    
    def get_market_minute_candles(self, symbol: str, unit: int, count: int = 200, to: str = None) -> pd.DataFrame:
        """분 캔들 조회 (확장 기능)
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            unit: 분 단위 (1, 3, 5, 15, 10, 30, 60, 240)
            count: 조회할 캔들 개수 (최대 200)
            to: 마지막 캔들 시각 (ISO 8601 형식, 예: "2023-01-01T00:00:00Z")
            
        Returns:
            pd.DataFrame: OHLCV 데이터
        """
        try:
            # 지원하는 분 단위 확인
            if unit not in [1, 3, 5, 15, 10, 30, 60, 240]:
                raise ValueError(f"지원하지 않는 분 단위입니다: {unit}")
            
            params = {
                'market': symbol,
                'count': min(count, 200)
            }
            
            if to:
                params['to'] = to
            
            response = self._request('GET', f'/candles/minutes/{unit}', params=params)
            
            # 데이터프레임으로 변환
            df = pd.DataFrame(response)
            
            # 컬럼 이름 변경
            if 'candle_date_time_utc' in df.columns:
                df['timestamp'] = pd.to_datetime(df['candle_date_time_utc'])
            
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
                df['timeframe'] = f"{unit}m"
                df['symbol'] = symbol
                
                return df
            else:
                logger.error(f"예상치 못한 응답 형식: {df.columns}")
                return pd.DataFrame()
            
        except Exception as e:
            logger.exception(f"분 캔들 조회 중 오류가 발생했습니다: {e}")
            return pd.DataFrame()
    
    def get_market_day_candles(self, symbol: str, count: int = 200, to: str = None, converting_price_unit: str = None) -> pd.DataFrame:
        """일 캔들 조회
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            count: 조회할 캔들 개수 (최대 200)
            to: 마지막 캔들 시각 (ISO 8601 형식, 예: "2023-01-01T00:00:00Z")
            converting_price_unit: 종가 환산 화폐 단위 (원화일 경우 생략)
            
        Returns:
            pd.DataFrame: OHLCV 데이터
        """
        try:
            params = {
                'market': symbol,
                'count': min(count, 200)
            }
            
            if to:
                params['to'] = to
            
            if converting_price_unit:
                params['converting_price_unit'] = converting_price_unit
            
            response = self._request('GET', '/candles/days', params=params)
            
            # 데이터프레임으로 변환
            df = pd.DataFrame(response)
            
            # 컬럼 이름 변경
            if 'candle_date_time_utc' in df.columns:
                df['timestamp'] = pd.to_datetime(df['candle_date_time_utc'])
            
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
                df['timeframe'] = "1d"
                df['symbol'] = symbol
                
                return df
            else:
                logger.error(f"예상치 못한 응답 형식: {df.columns}")
                return pd.DataFrame()
            
        except Exception as e:
            logger.exception(f"일 캔들 조회 중 오류가 발생했습니다: {e}")
            return pd.DataFrame()
    
    def get_market_week_candles(self, symbol: str, count: int = 200, to: str = None) -> pd.DataFrame:
        """주 캔들 조회
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            count: 조회할 캔들 개수 (최대 200)
            to: 마지막 캔들 시각 (ISO 8601 형식, 예: "2023-01-01T00:00:00Z")
            
        Returns:
            pd.DataFrame: OHLCV 데이터
        """
        try:
            params = {
                'market': symbol,
                'count': min(count, 200)
            }
            
            if to:
                params['to'] = to
            
            response = self._request('GET', '/candles/weeks', params=params)
            
            # 데이터프레임으로 변환
            df = pd.DataFrame(response)
            
            # 컬럼 이름 변경
            if 'candle_date_time_utc' in df.columns:
                df['timestamp'] = pd.to_datetime(df['candle_date_time_utc'])
            
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
                df['timeframe'] = "1w"
                df['symbol'] = symbol
                
                return df
            else:
                logger.error(f"예상치 못한 응답 형식: {df.columns}")
                return pd.DataFrame()
            
        except Exception as e:
            logger.exception(f"주 캔들 조회 중 오류가 발생했습니다: {e}")
            return pd.DataFrame()
    
    def get_market_month_candles(self, symbol: str, count: int = 200, to: str = None) -> pd.DataFrame:
        """월 캔들 조회
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            count: 조회할 캔들 개수 (최대 200)
            to: 마지막 캔들 시각 (ISO 8601 형식, 예: "2023-01-01T00:00:00Z")
            
        Returns:
            pd.DataFrame: OHLCV 데이터
        """
        try:
            params = {
                'market': symbol,
                'count': min(count, 200)
            }
            
            if to:
                params['to'] = to
            
            response = self._request('GET', '/candles/months', params=params)
            
            # 데이터프레임으로 변환
            df = pd.DataFrame(response)
            
            # 컬럼 이름 변경
            if 'candle_date_time_utc' in df.columns:
                df['timestamp'] = pd.to_datetime(df['candle_date_time_utc'])
            
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
                df['timeframe'] = "1M"
                df['symbol'] = symbol
                
                return df
            else:
                logger.error(f"예상치 못한 응답 형식: {df.columns}")
                return pd.DataFrame()
            
        except Exception as e:
            logger.exception(f"월 캔들 조회 중 오류가 발생했습니다: {e}")
            return pd.DataFrame()
            
    def get_historical_candles(self, symbol: str, timeframe: str, start_date: datetime, end_date: datetime = None) -> pd.DataFrame:
        """특정 기간의 캔들 데이터를 수집합니다.
        
        업비트 API는 한 번에 최대 200개의 캔들만 조회할 수 있으므로,
        여러 번 요청하여 전체 기간의 데이터를 수집합니다.
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            timeframe: 시간대 (예: "1m", "5m", "15m", "1h", "4h", "1d", "1w", "1M")
            start_date: 시작 날짜
            end_date: 종료 날짜 (기본값: 현재 시간)
            
        Returns:
            pd.DataFrame: OHLCV 데이터
        """
        if end_date is None:
            end_date = datetime.now()
        
        # 시작 날짜가 종료 날짜보다 늦으면 오류
        if start_date > end_date:
            raise ValueError("시작 날짜는 종료 날짜보다 이전이어야 합니다.")
        
        # 결과를 저장할 데이터프레임 리스트
        all_candles = []
        
        # 현재 조회할 날짜 (종료 날짜부터 시작)
        current_date = end_date
        
        # 시간대에 따른 간격 설정
        if timeframe.endswith('m'):
            minutes = int(timeframe[:-1])
            interval = timedelta(minutes=minutes * 200)
        elif timeframe.endswith('h'):
            hours = int(timeframe[:-1])
            interval = timedelta(hours=hours * 200)
        elif timeframe == '1d':
            interval = timedelta(days=200)
        elif timeframe == '1w':
            interval = timedelta(weeks=200)
        elif timeframe == '1M':
            # 월 단위는 대략 30일로 계산
            interval = timedelta(days=30 * 200)
        else:
            raise ValueError(f"지원하지 않는 시간대입니다: {timeframe}")
        
        try:
            while current_date >= start_date:
                # 현재 조회할 날짜를 ISO 8601 형식으로 변환
                to_date = current_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                
                # 시간대에 따라 적절한 메서드 호출
                if timeframe.endswith('m'):
                    minutes = int(timeframe[:-1])
                    df = self.get_market_minute_candles(symbol, minutes, count=200, to=to_date)
                elif timeframe == '1d':
                    df = self.get_market_day_candles(symbol, count=200, to=to_date)
                elif timeframe == '1w':
                    df = self.get_market_week_candles(symbol, count=200, to=to_date)
                elif timeframe == '1M':
                    df = self.get_market_month_candles(symbol, count=200, to=to_date)
                else:
                    # 시간 단위는 분 단위로 변환
                    if timeframe.endswith('h'):
                        hours = int(timeframe[:-1])
                        minutes = hours * 60
                        df = self.get_market_minute_candles(symbol, minutes, count=200, to=to_date)
                    else:
                        raise ValueError(f"지원하지 않는 시간대입니다: {timeframe}")
                
                # 데이터가 있으면 리스트에 추가
                if not df.empty:
                    all_candles.append(df)
                    
                    # 가장 오래된 캔들의 시간으로 다음 조회 날짜 설정
                    oldest_candle = df.iloc[-1]
                    current_date = oldest_candle["timestamp"] - timedelta(minutes=1)
                else:
                    # 더 이상 데이터가 없으면 종료
                    break
                
                # API 요청 제한을 고려하여 잠시 대기
                time.sleep(0.1)
                
                # 시작 날짜에 도달하면 종료
                if current_date < start_date:
                    break
            
            # 모든 데이터 병합
            if all_candles:
                result = pd.concat(all_candles)
                
                # 시작 날짜 이후의 데이터만 필터링
                result = result[result["timestamp"] >= start_date]
                
                # 중복 제거 및 시간순 정렬
                result = result.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
                
                return result
            else:
                return pd.DataFrame()
        
        except Exception as e:
            logger.exception(f"과거 캔들 데이터 수집 중 오류가 발생했습니다: {e}")
            return pd.DataFrame()
    
    def get_candles_range(self, symbol: str, timeframe: str, start_date: str, end_date: str) -> pd.DataFrame:
        """날짜 범위로 캔들 데이터 조회
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            timeframe: 시간대 (예: "1m", "5m", "15m", "1h", "4h", "1d")
            start_date: 시작 날짜 (YYYY-MM-DD 형식)
            end_date: 종료 날짜 (YYYY-MM-DD 형식)
            
        Returns:
            pd.DataFrame: OHLCV 데이터
        """
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # 종료일 포함
            
            all_data = []
            current_date = end_dt
            
            logger.info(f"데이터 수집 시작: {symbol} {timeframe} ({start_date} ~ {end_date})")
            
            while current_date > start_dt:
                try:
                    # 200개씩 데이터 요청
                    data = self.get_candles_before(symbol, timeframe, current_date, count=200)
                    
                    if data.empty:
                        break
                    
                    # 시작 날짜 이후 데이터만 필터링
                    filtered_data = data[data['timestamp'] >= start_dt]
                    
                    if not filtered_data.empty:
                        all_data.append(filtered_data)
                    
                    # 다음 요청을 위해 가장 오래된 데이터의 시간으로 설정
                    oldest_time = data['timestamp'].min()
                    current_date = oldest_time - timedelta(seconds=1)
                    
                    # API 요청 제한 고려
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"데이터 수집 중 오류: {e}")
                    break
            
            if all_data:
                # 모든 데이터 병합
                result = pd.concat(all_data, ignore_index=True)
                
                # 중복 제거 및 정렬
                result = result.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
                
                # 심볼과 타임프레임 정보 추가
                result['symbol'] = symbol
                result['timeframe'] = timeframe
                
                logger.info(f"데이터 수집 완료: {len(result)}개 캔들")
                return result
            else:
                logger.warning("수집된 데이터가 없습니다.")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"날짜 범위 데이터 수집 실패: {e}")
            return pd.DataFrame()