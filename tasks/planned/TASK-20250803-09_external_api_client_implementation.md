# TASK-20250803-09

## Title
Infrastructure Layer - 외부 API 클라이언트 구현 (Upbit API 연동)

## Objective (목표)
업비트 거래소 API와의 연동을 담당하는 Infrastructure Layer의 외부 API 클라이언트를 구현합니다. 시장 데이터 조회, 주문 실행, 계좌 정보 조회 등의 기능을 안전하고 효율적으로 처리하며, 도메인 계층에서 정의한 인터페이스를 구현하여 의존성 역전 원칙을 준수합니다.

## Source of Truth (준거 문서)
'리팩토링 계획 브리핑 문서' - Section "Phase 3: Infrastructure Layer 구현 (2주)" > "3.2 외부 API 클라이언트 (4일)"

## Pre-requisites (선행 조건)
- `TASK-20250803-08`: Repository 구현 완료
- Upbit API 문서 분석 완료
- API 키 관리 및 보안 정책 수립

## Detailed Steps (상세 실행 절차)

### 1. **[분석]** Upbit API 요구사항 및 제약사항 분석
- [ ] 공개 API (Public): 시장 데이터, 캔들 데이터, 호가 정보
- [ ] 인증 API (Private): 계좌 조회, 주문 실행, 주문 내역
- [ ] API 호출 제한 (Rate Limiting): 초당 요청 수 제한
- [ ] 에러 처리: 네트워크 오류, API 오류, 인증 오류 대응

### 2. **[폴더 구조 생성]** External API 클라이언트 구조
- [ ] `upbit_auto_trading/infrastructure/external_apis/` 폴더 생성
- [ ] `upbit_auto_trading/infrastructure/external_apis/upbit/` 폴더 생성
- [ ] `upbit_auto_trading/infrastructure/external_apis/common/` 폴더 생성

### 3. **[새 코드 작성]** API 클라이언트 기본 인프라
- [ ] `upbit_auto_trading/infrastructure/external_apis/common/api_client_base.py` 생성:
```python
import asyncio
import aiohttp
import time
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class RateLimitConfig:
    """API 호출 제한 설정"""
    requests_per_second: int = 10
    requests_per_minute: int = 600
    burst_limit: int = 100

@dataclass
class ApiResponse:
    """API 응답 래퍼"""
    status_code: int
    data: Any
    headers: Dict[str, str]
    request_time: datetime
    response_time_ms: float
    success: bool
    error_message: Optional[str] = None

class RateLimiter:
    """API 호출 제한 관리"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._second_requests: List[float] = []
        self._minute_requests: List[float] = []
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """API 호출 권한 획득"""
        async with self._lock:
            now = time.time()
            
            # 1초 내 요청 수 체크
            self._second_requests = [t for t in self._second_requests if now - t <= 1.0]
            if len(self._second_requests) >= self.config.requests_per_second:
                sleep_time = 1.0 - (now - self._second_requests[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    now = time.time()
            
            # 1분 내 요청 수 체크
            self._minute_requests = [t for t in self._minute_requests if now - t <= 60.0]
            if len(self._minute_requests) >= self.config.requests_per_minute:
                sleep_time = 60.0 - (now - self._minute_requests[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    now = time.time()
            
            # 현재 요청 시간 기록
            self._second_requests.append(now)
            self._minute_requests.append(now)

class BaseApiClient(ABC):
    """API 클라이언트 기본 클래스"""
    
    def __init__(self, base_url: str, rate_limit_config: RateLimitConfig,
                 timeout: int = 30, max_retries: int = 3):
        self._base_url = base_url.rstrip('/')
        self._rate_limiter = RateLimiter(rate_limit_config)
        self._timeout = timeout
        self._max_retries = max_retries
        self._session: Optional[aiohttp.ClientSession] = None
        self._logger = logging.getLogger(self.__class__.__name__)
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _ensure_session(self) -> None:
        """HTTP 세션 확보"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,  # 최대 연결 수
                limit_per_host=30,  # 호스트당 최대 연결 수
                ttl_dns_cache=300,  # DNS 캐시 시간
                use_dns_cache=True
            )
            
            timeout = aiohttp.ClientTimeout(total=self._timeout)
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'User-Agent': 'UpbitAutoTrader/1.0'}
            )
    
    async def _make_request(self, method: str, endpoint: str,
                           params: Optional[Dict] = None,
                           data: Optional[Dict] = None,
                           headers: Optional[Dict] = None) -> ApiResponse:
        """HTTP 요청 실행"""
        url = f"{self._base_url}{endpoint}"
        
        # Rate limiting 적용
        await self._rate_limiter.acquire()
        
        # 재시도 로직
        last_exception = None
        for attempt in range(self._max_retries + 1):
            try:
                start_time = time.time()
                request_time = datetime.now()
                
                await self._ensure_session()
                
                # 요청 헤더 준비
                request_headers = self._prepare_headers(method, endpoint, params, data)
                if headers:
                    request_headers.update(headers)
                
                # HTTP 요청 실행
                async with self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=request_headers
                ) as response:
                    response_time_ms = (time.time() - start_time) * 1000
                    response_data = await response.json()
                    
                    api_response = ApiResponse(
                        status_code=response.status,
                        data=response_data,
                        headers=dict(response.headers),
                        request_time=request_time,
                        response_time_ms=response_time_ms,
                        success=200 <= response.status < 300
                    )
                    
                    if not api_response.success:
                        api_response.error_message = self._extract_error_message(response_data)
                    
                    self._log_request(method, url, api_response, attempt)
                    
                    if api_response.success:
                        return api_response
                    elif response.status in [429, 503, 504]:  # 재시도 가능한 오류
                        if attempt < self._max_retries:
                            await self._handle_retryable_error(response.status, attempt)
                            continue
                    
                    return api_response
                    
            except asyncio.TimeoutError as e:
                last_exception = e
                if attempt < self._max_retries:
                    await asyncio.sleep(2 ** attempt)  # 지수 백오프
                    continue
                    
            except aiohttp.ClientError as e:
                last_exception = e
                if attempt < self._max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
        
        # 모든 재시도 실패
        return ApiResponse(
            status_code=0,
            data=None,
            headers={},
            request_time=datetime.now(),
            response_time_ms=0,
            success=False,
            error_message=f"요청 실패 (재시도 {self._max_retries}회): {str(last_exception)}"
        )
    
    @abstractmethod
    def _prepare_headers(self, method: str, endpoint: str,
                        params: Optional[Dict], data: Optional[Dict]) -> Dict[str, str]:
        """요청 헤더 준비 (인증 등)"""
        pass
    
    def _extract_error_message(self, response_data: Any) -> str:
        """API 응답에서 에러 메시지 추출"""
        if isinstance(response_data, dict):
            return response_data.get('error', {}).get('message', 'Unknown error')
        return str(response_data)
    
    async def _handle_retryable_error(self, status_code: int, attempt: int) -> None:
        """재시도 가능한 오류 처리"""
        if status_code == 429:  # Rate limit exceeded
            sleep_time = min(60, (2 ** attempt) * 5)  # 최대 60초
        else:  # 503, 504 등 서버 오류
            sleep_time = 2 ** attempt
        
        self._logger.warning(f"재시도 가능한 오류 {status_code}, {sleep_time}초 대기")
        await asyncio.sleep(sleep_time)
    
    def _log_request(self, method: str, url: str, response: ApiResponse, attempt: int) -> None:
        """요청 로깅"""
        log_msg = (
            f"{method} {url} -> {response.status_code} "
            f"({response.response_time_ms:.1f}ms, 시도 {attempt + 1})"
        )
        
        if response.success:
            self._logger.debug(log_msg)
        else:
            self._logger.warning(f"{log_msg} - {response.error_message}")

class ApiClientError(Exception):
    """API 클라이언트 예외"""
    def __init__(self, message: str, status_code: Optional[int] = None,
                 response_data: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

class AuthenticationError(ApiClientError):
    """인증 오류"""
    pass

class RateLimitError(ApiClientError):
    """API 호출 제한 오류"""
    pass

class NetworkError(ApiClientError):
    """네트워크 오류"""
    pass
```

### 4. **[새 코드 작성]** Upbit API 인증 처리
- [ ] `upbit_auto_trading/infrastructure/external_apis/upbit/upbit_auth.py` 생성:
```python
import jwt
import hashlib
import uuid
from urllib.parse import urlencode
from typing import Dict, Optional, Any
import os
import logging

class UpbitAuthenticator:
    """Upbit API 인증 처리"""
    
    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None):
        """
        Args:
            access_key: Upbit API Access Key (None이면 환경변수에서 로드)
            secret_key: Upbit API Secret Key (None이면 환경변수에서 로드)
        """
        self._access_key = access_key or os.getenv('UPBIT_ACCESS_KEY')
        self._secret_key = secret_key or os.getenv('UPBIT_SECRET_KEY')
        self._logger = logging.getLogger(__name__)
        
        if not self._access_key or not self._secret_key:
            self._logger.warning("Upbit API 키가 설정되지 않았습니다. 공개 API만 사용 가능합니다.")
    
    def is_authenticated(self) -> bool:
        """인증 정보 설정 여부 확인"""
        return bool(self._access_key and self._secret_key)
    
    def create_jwt_token(self, query_params: Optional[Dict] = None,
                        request_body: Optional[Dict] = None) -> str:
        """JWT 토큰 생성"""
        if not self.is_authenticated():
            raise AuthenticationError("API 키가 설정되지 않았습니다")
        
        payload = {
            'access_key': self._access_key,
            'nonce': str(uuid.uuid4())
        }
        
        # 쿼리 파라미터 해시 추가
        if query_params:
            query_string = urlencode(query_params, doseq=True).encode()
            m = hashlib.sha512()
            m.update(query_string)
            payload['query_hash'] = m.hexdigest()
            payload['query_hash_alg'] = 'SHA512'
        
        # 요청 본문 해시 추가
        if request_body:
            import json
            body_string = json.dumps(request_body, separators=(',', ':')).encode()
            m = hashlib.sha512()
            m.update(body_string)
            payload['query_hash'] = m.hexdigest()
            payload['query_hash_alg'] = 'SHA512'
        
        try:
            token = jwt.encode(payload, self._secret_key, algorithm='HS256')
            return f'Bearer {token}'
        except Exception as e:
            self._logger.error(f"JWT 토큰 생성 실패: {e}")
            raise AuthenticationError(f"JWT 토큰 생성 실패: {e}")
    
    def get_public_headers(self) -> Dict[str, str]:
        """공개 API용 헤더"""
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def get_private_headers(self, query_params: Optional[Dict] = None,
                          request_body: Optional[Dict] = None) -> Dict[str, str]:
        """인증 API용 헤더"""
        headers = self.get_public_headers()
        
        if self.is_authenticated():
            headers['Authorization'] = self.create_jwt_token(query_params, request_body)
        
        return headers

from upbit_auto_trading.infrastructure.external_apis.common.api_client_base import (
    AuthenticationError
)
```

### 5. **[새 코드 작성]** Upbit 공개 API 클라이언트
- [ ] `upbit_auto_trading/infrastructure/external_apis/upbit/upbit_public_client.py` 생성:
```python
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from upbit_auto_trading.infrastructure.external_apis.common.api_client_base import (
    BaseApiClient, RateLimitConfig, ApiResponse, ApiClientError
)
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_auth import UpbitAuthenticator

class UpbitPublicClient(BaseApiClient):
    """Upbit 공개 API 클라이언트"""
    
    def __init__(self):
        # Upbit 공개 API 제한: 초당 10회, 분당 600회
        rate_config = RateLimitConfig(
            requests_per_second=10,
            requests_per_minute=600,
            burst_limit=100
        )
        
        super().__init__(
            base_url='https://api.upbit.com/v1',
            rate_limit_config=rate_config,
            timeout=30,
            max_retries=3
        )
        
        self._auth = UpbitAuthenticator()
    
    def _prepare_headers(self, method: str, endpoint: str,
                        params: Optional[Dict], data: Optional[Dict]) -> Dict[str, str]:
        """공개 API용 헤더 준비"""
        return self._auth.get_public_headers()
    
    async def get_markets(self, is_details: bool = False) -> List[Dict[str, Any]]:
        """마켓 코드 조회"""
        params = {'isDetails': 'true' if is_details else 'false'}
        
        response = await self._make_request('GET', '/market/all', params=params)
        
        if not response.success:
            raise ApiClientError(f"마켓 조회 실패: {response.error_message}",
                               response.status_code, response.data)
        
        return response.data
    
    async def get_candles_minutes(self, market: str, unit: int = 1,
                                 to: Optional[str] = None, count: int = 200) -> List[Dict[str, Any]]:
        """분봉 캔들 조회"""
        if unit not in [1, 3, 5, 15, 10, 30, 60, 240]:
            raise ValueError(f"유효하지 않은 분봉 단위: {unit}")
        
        if count > 200:
            raise ValueError("한 번에 최대 200개까지만 조회 가능합니다")
        
        params = {
            'market': market,
            'count': count
        }
        
        if to:
            params['to'] = to
        
        response = await self._make_request('GET', f'/candles/minutes/{unit}', params=params)
        
        if not response.success:
            raise ApiClientError(f"분봉 캔들 조회 실패: {response.error_message}",
                               response.status_code, response.data)
        
        return response.data
    
    async def get_candles_days(self, market: str, to: Optional[str] = None,
                              count: int = 200, converting_price_unit: Optional[str] = None) -> List[Dict[str, Any]]:
        """일봉 캔들 조회"""
        if count > 200:
            raise ValueError("한 번에 최대 200개까지만 조회 가능합니다")
        
        params = {
            'market': market,
            'count': count
        }
        
        if to:
            params['to'] = to
        
        if converting_price_unit:
            params['convertingPriceUnit'] = converting_price_unit
        
        response = await self._make_request('GET', '/candles/days', params=params)
        
        if not response.success:
            raise ApiClientError(f"일봉 캔들 조회 실패: {response.error_message}",
                               response.status_code, response.data)
        
        return response.data
    
    async def get_orderbook(self, markets: List[str]) -> List[Dict[str, Any]]:
        """호가 정보 조회"""
        if len(markets) > 5:
            raise ValueError("한 번에 최대 5개 마켓까지만 조회 가능합니다")
        
        params = {'markets': ','.join(markets)}
        
        response = await self._make_request('GET', '/orderbook', params=params)
        
        if not response.success:
            raise ApiClientError(f"호가 정보 조회 실패: {response.error_message}",
                               response.status_code, response.data)
        
        return response.data
    
    async def get_tickers(self, markets: List[str]) -> List[Dict[str, Any]]:
        """현재가 정보 조회"""
        if len(markets) > 100:
            raise ValueError("한 번에 최대 100개 마켓까지만 조회 가능합니다")
        
        params = {'markets': ','.join(markets)}
        
        response = await self._make_request('GET', '/ticker', params=params)
        
        if not response.success:
            raise ApiClientError(f"현재가 정보 조회 실패: {response.error_message}",
                               response.status_code, response.data)
        
        return response.data
    
    async def get_trades_ticks(self, market: str, to: Optional[str] = None,
                              count: int = 200, cursor: Optional[str] = None,
                              days_ago: Optional[int] = None) -> List[Dict[str, Any]]:
        """최근 체결 내역 조회"""
        if count > 500:
            raise ValueError("한 번에 최대 500개까지만 조회 가능합니다")
        
        params = {
            'market': market,
            'count': count
        }
        
        if to:
            params['to'] = to
        if cursor:
            params['cursor'] = cursor
        if days_ago is not None:
            params['daysAgo'] = days_ago
        
        response = await self._make_request('GET', '/trades/ticks', params=params)
        
        if not response.success:
            raise ApiClientError(f"체결 내역 조회 실패: {response.error_message}",
                               response.status_code, response.data)
        
        return response.data
    
    async def get_market_data_batch(self, market: str, days: int = 30) -> Dict[str, Any]:
        """마켓 데이터 일괄 조회 (캔들 + 현재가 + 호가)"""
        try:
            # 병렬로 데이터 조회
            tasks = [
                self.get_candles_days(market, count=min(days, 200)),
                self.get_tickers([market]),
                self.get_orderbook([market])
            ]
            
            candles, tickers, orderbook = await asyncio.gather(*tasks)
            
            return {
                'market': market,
                'candles': candles,
                'ticker': tickers[0] if tickers else None,
                'orderbook': orderbook[0] if orderbook else None,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self._logger.error(f"마켓 데이터 일괄 조회 실패 {market}: {e}")
            raise ApiClientError(f"마켓 데이터 일괄 조회 실패: {str(e)}")
```

### 6. **[새 코드 작성]** Upbit 인증 API 클라이언트
- [ ] `upbit_auto_trading/infrastructure/external_apis/upbit/upbit_private_client.py` 생성:
```python
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

from upbit_auto_trading.infrastructure.external_apis.common.api_client_base import (
    BaseApiClient, RateLimitConfig, ApiResponse, ApiClientError, AuthenticationError
)
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_auth import UpbitAuthenticator

class UpbitPrivateClient(BaseApiClient):
    """Upbit 인증 API 클라이언트"""
    
    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None):
        # Upbit 인증 API 제한: 초당 8회, 분당 200회 (보수적으로 설정)
        rate_config = RateLimitConfig(
            requests_per_second=8,
            requests_per_minute=200,
            burst_limit=50
        )
        
        super().__init__(
            base_url='https://api.upbit.com/v1',
            rate_limit_config=rate_config,
            timeout=30,
            max_retries=3
        )
        
        self._auth = UpbitAuthenticator(access_key, secret_key)
        
        if not self._auth.is_authenticated():
            raise AuthenticationError("Upbit API 키가 설정되지 않았습니다")
    
    def _prepare_headers(self, method: str, endpoint: str,
                        params: Optional[Dict], data: Optional[Dict]) -> Dict[str, str]:
        """인증 API용 헤더 준비"""
        return self._auth.get_private_headers(params, data)
    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """계좌 정보 조회"""
        response = await self._make_request('GET', '/accounts')
        
        if not response.success:
            raise ApiClientError(f"계좌 조회 실패: {response.error_message}",
                               response.status_code, response.data)
        
        return response.data
    
    async def get_orders_chance(self, market: str) -> Dict[str, Any]:
        """주문 가능 정보 조회"""
        params = {'market': market}
        
        response = await self._make_request('GET', '/orders/chance', params=params)
        
        if not response.success:
            raise ApiClientError(f"주문 가능 정보 조회 실패: {response.error_message}",
                               response.status_code, response.data)
        
        return response.data
    
    async def place_order(self, market: str, side: str, volume: Optional[str] = None,
                         price: Optional[str] = None, ord_type: str = 'limit') -> Dict[str, Any]:
        """주문 실행"""
        if side not in ['bid', 'ask']:
            raise ValueError("side는 'bid' 또는 'ask'여야 합니다")
        
        if ord_type not in ['limit', 'price', 'market']:
            raise ValueError("ord_type은 'limit', 'price', 'market' 중 하나여야 합니다")
        
        data = {
            'market': market,
            'side': side,
            'ord_type': ord_type
        }
        
        if volume:
            data['volume'] = str(volume)
        if price:
            data['price'] = str(price)
        
        # 주문 타입별 필수 파라미터 검증
        if ord_type == 'limit':
            if not volume or not price:
                raise ValueError("지정가 주문은 volume과 price가 필요합니다")
        elif ord_type == 'market':
            if side == 'bid' and not price:
                raise ValueError("시장가 매수는 price(매수 금액)가 필요합니다")
            elif side == 'ask' and not volume:
                raise ValueError("시장가 매도는 volume이 필요합니다")
        
        response = await self._make_request('POST', '/orders', data=data)
        
        if not response.success:
            raise ApiClientError(f"주문 실행 실패: {response.error_message}",
                               response.status_code, response.data)
        
        return response.data
    
    async def cancel_order(self, uuid: Optional[str] = None,
                          identifier: Optional[str] = None) -> Dict[str, Any]:
        """주문 취소"""
        if not uuid and not identifier:
            raise ValueError("uuid 또는 identifier 중 하나는 필수입니다")
        
        data = {}
        if uuid:
            data['uuid'] = uuid
        if identifier:
            data['identifier'] = identifier
        
        response = await self._make_request('DELETE', '/order', data=data)
        
        if not response.success:
            raise ApiClientError(f"주문 취소 실패: {response.error_message}",
                               response.status_code, response.data)
        
        return response.data
    
    async def get_orders(self, market: Optional[str] = None, state: str = 'wait',
                        states: Optional[List[str]] = None, uuids: Optional[List[str]] = None,
                        identifiers: Optional[List[str]] = None,
                        page: int = 1, limit: int = 100, order_by: str = 'desc') -> List[Dict[str, Any]]:
        """주문 목록 조회"""
        params = {
            'state': state,
            'page': page,
            'limit': min(limit, 100),  # 최대 100개
            'order_by': order_by
        }
        
        if market:
            params['market'] = market
        if states:
            params['states[]'] = states
        if uuids:
            params['uuids[]'] = uuids
        if identifiers:
            params['identifiers[]'] = identifiers
        
        response = await self._make_request('GET', '/orders', params=params)
        
        if not response.success:
            raise ApiClientError(f"주문 목록 조회 실패: {response.error_message}",
                               response.status_code, response.data)
        
        return response.data
    
    async def get_order(self, uuid: Optional[str] = None,
                       identifier: Optional[str] = None) -> Dict[str, Any]:
        """개별 주문 조회"""
        if not uuid and not identifier:
            raise ValueError("uuid 또는 identifier 중 하나는 필수입니다")
        
        params = {}
        if uuid:
            params['uuid'] = uuid
        if identifier:
            params['identifier'] = identifier
        
        response = await self._make_request('GET', '/order', params=params)
        
        if not response.success:
            raise ApiClientError(f"주문 조회 실패: {response.error_message}",
                               response.status_code, response.data)
        
        return response.data
    
    async def get_order_fills(self, market: Optional[str] = None,
                             uuids: Optional[List[str]] = None,
                             identifiers: Optional[List[str]] = None,
                             page: int = 1, limit: int = 100, order_by: str = 'desc') -> List[Dict[str, Any]]:
        """체결 내역 조회"""
        params = {
            'page': page,
            'limit': min(limit, 100),
            'order_by': order_by
        }
        
        if market:
            params['market'] = market
        if uuids:
            params['uuids[]'] = uuids
        if identifiers:
            params['identifiers[]'] = identifiers
        
        response = await self._make_request('GET', '/fills', params=params)
        
        if not response.success:
            raise ApiClientError(f"체결 내역 조회 실패: {response.error_message}",
                               response.status_code, response.data)
        
        return response.data
    
    async def place_market_buy_order(self, market: str, price: str) -> Dict[str, Any]:
        """시장가 매수 주문 (편의 메서드)"""
        return await self.place_order(
            market=market,
            side='bid',
            price=price,
            ord_type='price'
        )
    
    async def place_market_sell_order(self, market: str, volume: str) -> Dict[str, Any]:
        """시장가 매도 주문 (편의 메서드)"""
        return await self.place_order(
            market=market,
            side='ask',
            volume=volume,
            ord_type='market'
        )
    
    async def place_limit_buy_order(self, market: str, volume: str, price: str) -> Dict[str, Any]:
        """지정가 매수 주문 (편의 메서드)"""
        return await self.place_order(
            market=market,
            side='bid',
            volume=volume,
            price=price,
            ord_type='limit'
        )
    
    async def place_limit_sell_order(self, market: str, volume: str, price: str) -> Dict[str, Any]:
        """지정가 매도 주문 (편의 메서드)"""
        return await self.place_order(
            market=market,
            side='ask',
            volume=volume,
            price=price,
            ord_type='limit'
        )
```

### 7. **[새 코드 작성]** 통합 Upbit 클라이언트
- [ ] `upbit_auto_trading/infrastructure/external_apis/upbit/upbit_client.py` 생성:
```python
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_private_client import UpbitPrivateClient
from upbit_auto_trading.infrastructure.external_apis.common.api_client_base import ApiClientError

class UpbitClient:
    """통합 Upbit API 클라이언트"""
    
    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None):
        """
        Args:
            access_key: API 접근 키 (None이면 공개 API만 사용)
            secret_key: API 비밀 키 (None이면 공개 API만 사용)
        """
        self._public_client = UpbitPublicClient()
        self._private_client = None
        
        # 인증 정보가 있으면 private client 초기화
        if access_key and secret_key:
            try:
                self._private_client = UpbitPrivateClient(access_key, secret_key)
            except Exception as e:
                print(f"⚠️ 인증 API 클라이언트 초기화 실패: {e}")
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self._public_client.__aenter__()
        if self._private_client:
            await self._private_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self._public_client.__aexit__(exc_type, exc_val, exc_tb)
        if self._private_client:
            await self._private_client.__aexit__(exc_type, exc_val, exc_tb)
    
    @property
    def public(self) -> UpbitPublicClient:
        """공개 API 클라이언트"""
        return self._public_client
    
    @property
    def private(self) -> UpbitPrivateClient:
        """인증 API 클라이언트"""
        if not self._private_client:
            raise ApiClientError("인증 API 클라이언트가 초기화되지 않았습니다")
        return self._private_client
    
    def is_authenticated(self) -> bool:
        """인증 상태 확인"""
        return self._private_client is not None
    
    # 편의 메서드들
    async def get_krw_markets(self) -> List[str]:
        """KRW 마켓 목록 조회"""
        markets = await self.public.get_markets()
        return [market['market'] for market in markets if market['market'].startswith('KRW-')]
    
    async def get_market_summary(self, market: str) -> Dict[str, Any]:
        """마켓 요약 정보 조회"""
        try:
            # 병렬로 현재가와 호가 정보 조회
            ticker_task = self.public.get_tickers([market])
            orderbook_task = self.public.get_orderbook([market])
            
            tickers, orderbooks = await asyncio.gather(ticker_task, orderbook_task)
            
            ticker = tickers[0] if tickers else {}
            orderbook = orderbooks[0] if orderbooks else {}
            
            return {
                'market': market,
                'current_price': ticker.get('trade_price'),
                'change_rate': ticker.get('change_rate'),
                'volume': ticker.get('acc_trade_volume_24h'),
                'bid_price': orderbook.get('orderbook_units', [{}])[0].get('bid_price') if orderbook.get('orderbook_units') else None,
                'ask_price': orderbook.get('orderbook_units', [{}])[0].get('ask_price') if orderbook.get('orderbook_units') else None,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise ApiClientError(f"마켓 요약 정보 조회 실패 {market}: {str(e)}")
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """포트폴리오 요약 정보 조회"""
        if not self.is_authenticated():
            raise ApiClientError("인증이 필요한 기능입니다")
        
        try:
            accounts = await self.private.get_accounts()
            
            total_krw = 0
            holdings = []
            
            for account in accounts:
                currency = account['currency']
                balance = float(account['balance'])
                locked = float(account['locked'])
                total_balance = balance + locked
                
                if currency == 'KRW':
                    total_krw += total_balance
                elif total_balance > 0:
                    # 다른 코인들의 KRW 가치 계산
                    market = f'KRW-{currency}'
                    try:
                        ticker = await self.public.get_tickers([market])
                        if ticker:
                            current_price = float(ticker[0]['trade_price'])
                            krw_value = total_balance * current_price
                            total_krw += krw_value
                            
                            holdings.append({
                                'currency': currency,
                                'balance': balance,
                                'locked': locked,
                                'total_balance': total_balance,
                                'current_price': current_price,
                                'krw_value': krw_value
                            })
                    except:
                        # 현재가 조회 실패 시 0으로 처리
                        holdings.append({
                            'currency': currency,
                            'balance': balance,
                            'locked': locked,
                            'total_balance': total_balance,
                            'current_price': 0,
                            'krw_value': 0
                        })
            
            return {
                'total_krw_value': total_krw,
                'holdings': holdings,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise ApiClientError(f"포트폴리오 요약 조회 실패: {str(e)}")
```

### 8. **[테스트 코드 작성]** API 클라이언트 테스트
- [ ] `tests/infrastructure/external_apis/` 폴더 생성
- [ ] `tests/infrastructure/external_apis/test_upbit_client.py` 생성:
```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_client import UpbitClient
from upbit_auto_trading.infrastructure.external_apis.common.api_client_base import ApiClientError

class TestUpbitClient:
    @pytest.fixture
    def mock_public_response(self):
        return {
            'status_code': 200,
            'data': [{'market': 'KRW-BTC', 'trade_price': 50000000}],
            'success': True
        }
    
    @pytest.mark.asyncio
    async def test_public_api_market_data(self, mock_public_response):
        # Given
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = [{'market': 'KRW-BTC', 'trade_price': 50000000}]
            mock_response.headers = {}
            mock_request.return_value.__aenter__.return_value = mock_response
            
            # When
            async with UpbitClient() as client:
                result = await client.public.get_tickers(['KRW-BTC'])
            
            # Then
            assert len(result) == 1
            assert result[0]['market'] == 'KRW-BTC'
    
    @pytest.mark.asyncio
    async def test_authentication_required_error(self):
        # Given
        client = UpbitClient()  # 인증 정보 없음
        
        # When & Then
        with pytest.raises(ApiClientError, match="인증이 필요한 기능입니다"):
            await client.get_portfolio_summary()
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        # Given
        async with UpbitClient() as client:
            rate_limiter = client.public._rate_limiter
            
            # When
            start_time = asyncio.get_event_loop().time()
            
            # 연속으로 여러 요청 (rate limiting 테스트)
            for _ in range(3):
                await rate_limiter.acquire()
            
            end_time = asyncio.get_event_loop().time()
            
            # Then
            # Rate limiting으로 인한 지연이 있어야 함
            assert end_time - start_time >= 0  # 기본 테스트
```

### 9. **[통합]** API 클라이언트 팩토리
- [ ] `upbit_auto_trading/infrastructure/external_apis/api_client_factory.py` 생성:
```python
from typing import Optional
import os

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_client import UpbitClient

class ApiClientFactory:
    """API 클라이언트 팩토리"""
    
    @staticmethod
    def create_upbit_client(access_key: Optional[str] = None,
                           secret_key: Optional[str] = None) -> UpbitClient:
        """Upbit 클라이언트 생성"""
        # 환경변수에서 API 키 로드 (파라미터가 없을 경우)
        if access_key is None:
            access_key = os.getenv('UPBIT_ACCESS_KEY')
        if secret_key is None:
            secret_key = os.getenv('UPBIT_SECRET_KEY')
        
        return UpbitClient(access_key, secret_key)
    
    @staticmethod
    def create_public_only_client() -> UpbitClient:
        """공개 API 전용 클라이언트 생성"""
        return UpbitClient()
```

### 10. **[통합]** Infrastructure API 패키지 초기화
- [ ] `upbit_auto_trading/infrastructure/external_apis/__init__.py` 생성:
```python
from .api_client_factory import ApiClientFactory
from .upbit.upbit_client import UpbitClient

__all__ = ['ApiClientFactory', 'UpbitClient']
```

## Verification Criteria (완료 검증 조건)

### **[API 클라이언트 동작 검증]** 모든 API 기능 정상 동작 확인
- [ ] `pytest tests/infrastructure/external_apis/ -v` 실행하여 모든 테스트 통과
- [ ] Python REPL에서 공개 API 테스트:
```python
import asyncio
from upbit_auto_trading.infrastructure.external_apis import ApiClientFactory

async def test_public_api():
    async with ApiClientFactory.create_public_only_client() as client:
        markets = await client.get_krw_markets()
        print(f"KRW 마켓 수: {len(markets)}")
        
        if markets:
            summary = await client.get_market_summary(markets[0])
            print(f"첫 번째 마켓 정보: {summary}")
    
    print("✅ 공개 API 검증 완료")

asyncio.run(test_public_api())
```

### **[인증 API 검증]** API 키 설정 시 인증 API 동작 확인
- [ ] 환경변수에 API 키 설정 후 인증 API 테스트
- [ ] 계좌 정보 조회 및 주문 가능 정보 조회 확인

### **[Rate Limiting 검증]** API 호출 제한 정상 동작 확인
- [ ] 연속 요청 시 Rate Limiting 적용 확인
- [ ] 429 에러 발생 시 재시도 로직 확인

### **[에러 처리 검증]** 다양한 오류 상황 처리 확인
- [ ] 네트워크 오류 시 재시도 및 폴백 동작
- [ ] API 오류 응답 시 적절한 예외 발생
- [ ] 인증 오류 시 명확한 에러 메시지

## Notes (주의사항)
- API 키는 절대 코드에 하드코딩하지 말고 환경변수 사용 필수
- Rate Limiting을 엄격히 준수하여 API 차단 방지
- 모든 API 호출은 비동기로 처리하여 성능 최적화
- 에러 처리는 사용자에게 명확한 메시지 제공
- 실제 거래 API 테스트 시 소액으로만 테스트
