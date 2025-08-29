"""
업비트 프라이빗 API 클라이언트 - 업비트 전용 단순화 버전

업비트 전용으로 최적화된 구현
인증이 필요한 REST API 기능을 담당합니다.
"""
import aiohttp
import logging
from typing import List, Dict, Any, Optional, Literal
from decimal import Decimal

from .upbit_auth import UpbitAuthenticator
from .upbit_rate_limiter import UpbitRateLimiter, create_upbit_private_limiter


class UpbitPrivateClient:
    """
    업비트 전용 프라이빗 API 클라이언트

    특징:
    - 업비트 전용 최적화
    - 업비트 Rate Limiter 사용
    - 간단하고 직관적인 구조
    - 인증이 필요한 모든 기능 지원
    """

    BASE_URL = "https://api.upbit.com/v1"

    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None,
                 rate_limiter: Optional[UpbitRateLimiter] = None):
        """
        업비트 프라이빗 API 클라이언트 초기화

        Args:
            access_key: Upbit API Access Key
            secret_key: Upbit API Secret Key
            rate_limiter: 업비트 Rate Limiter (기본값: 자동 생성)
        """
        # 인증 관리자 초기화
        self._auth = UpbitAuthenticator(access_key, secret_key)
        if not self._auth.is_authenticated():
            raise ValueError("API 키가 설정되지 않았습니다. 인증이 필요한 API는 사용할 수 없습니다.")

        # Rate Limiter 설정
        self.rate_limiter = rate_limiter or create_upbit_private_limiter("upbit_private")
        self._session: Optional[aiohttp.ClientSession] = None
        self._logger = logging.getLogger("UpbitPrivateClient")

    def __repr__(self):
        return f"UpbitPrivateClient(authenticated={self._auth.is_authenticated()})"

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _ensure_session(self) -> None:
        """HTTP 세션 확보"""
        if not self._session:
            self._session = aiohttp.ClientSession()

    async def close(self) -> None:
        """리소스 정리"""
        if self._session:
            await self._session.close()
            self._session = None

    def is_authenticated(self) -> bool:
        """인증 상태 확인"""
        return self._auth.is_authenticated()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Any:
        """
        인증된 HTTP 요청 수행

        Args:
            method: HTTP 메서드
            endpoint: API 엔드포인트
            params: 쿼리 파라미터
            data: 요청 바디 데이터

        Returns:
            Any: API 응답 데이터 (보통 Dict 또는 List)
        """
        await self._ensure_session()

        # Rate Limiting 적용
        await self.rate_limiter.acquire(endpoint)

        # 인증 헤더 생성
        headers = self._auth.get_private_headers(query_params=params, request_body=data)
        headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'upbit-autotrader-vscode/1.0'
        })

        url = f"{self.BASE_URL}{endpoint}"

        if not self._session:
            raise RuntimeError("HTTP 세션이 초기화되지 않았습니다")

        try:
            async with self._session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers
            ) as response:
                response_text = await response.text()

                if response.status == 200:
                    return await response.json()
                else:
                    self._logger.error(f"API 요청 실패: {response.status} - {response_text}")
                    response.raise_for_status()

        except Exception as e:
            self._logger.error(f"HTTP 요청 중 오류 발생: {e}")
            raise

    # ================================================================
    # 자산(Asset) API - 계좌 및 자산 관리
    # ================================================================

    async def get_accounts(self) -> Dict[str, Dict[str, Any]]:
        """
        계좌 정보 조회

        내가 보유한 자산 리스트를 통화별로 인덱싱하여 반환합니다.

        Returns:
            Dict[str, Dict]: {
                'KRW': {'currency': 'KRW', 'balance': '20000.0', 'locked': '0.0', ...},
                'BTC': {'currency': 'BTC', 'balance': '0.00005', 'locked': '0.0', ...}
            }

        Note:
            기존 List 형식이 필요한 경우, 다음과 같이 변환할 수 있습니다:
            accounts_list = list(accounts.values())
        """
        response = await self._make_request('GET', '/accounts')

        # List 응답을 Dict로 변환
        accounts_dict = {}
        if isinstance(response, list):
            for account in response:
                if isinstance(account, dict):
                    currency = account.get('currency')
                    if currency:
                        accounts_dict[currency] = account
        return accounts_dict

    # ================================================================
    # 주문(Order) API - 주문 생성, 조회, 취소
    # ================================================================

    async def get_orders_chance(self, market: str) -> Dict[str, Any]:
        """
        주문 가능 정보 조회

        마켓별 주문 가능 정보를 확인합니다.

        Args:
            market: 마켓 코드 (예: KRW-BTC)

        Returns:
            Dict: 주문 가능 정보 (최대/최소 주문 금액, 수수료 등)
        """
        params = {'market': market}
        return await self._make_request('GET', '/orders/chance', params=params)

    async def place_order(
        self,
        market: str,
        side: Literal['bid', 'ask'],
        ord_type: Literal['limit', 'price', 'market'],
        volume: Optional[Decimal] = None,
        price: Optional[Decimal] = None,
        identifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        주문 생성

        Args:
            market: 마켓 코드 (예: KRW-BTC)
            side: 주문 종류 ('bid': 매수, 'ask': 매도)
            ord_type: 주문 타입
                - 'limit': 지정가 주문 (volume, price 필수)
                - 'price': 시장가 매수 (price 필수)
                - 'market': 시장가 매도 (volume 필수)
            volume: 주문 수량 (지정가, 시장가 매도 시 필수)
            price: 주문 가격 (지정가, 시장가 매수 시 필수)
            identifier: 조회용 사용자 지정값

        Returns:
            Dict: 생성된 주문 정보

        Examples:
            # 지정가 매수
            order = await client.place_order('KRW-BTC', 'bid', 'limit', volume=Decimal('0.001'), price=Decimal('50000000'))

            # 시장가 매수 (5만원어치)
            order = await client.place_order('KRW-BTC', 'bid', 'price', price=Decimal('50000'))

            # 시장가 매도 (0.001 BTC)
            order = await client.place_order('KRW-BTC', 'ask', 'market', volume=Decimal('0.001'))
        """
        data = {
            'market': market,
            'side': side,
            'ord_type': ord_type
        }

        if volume is not None:
            data['volume'] = str(volume)
        if price is not None:
            data['price'] = str(price)
        if identifier is not None:
            data['identifier'] = identifier

        return await self._make_request('POST', '/orders', data=data)

    async def get_order(self, uuid: Optional[str] = None, identifier: Optional[str] = None) -> Dict[str, Any]:
        """
        개별 주문 조회

        Args:
            uuid: 주문 UUID (uuid 또는 identifier 중 하나 필수)
            identifier: 조회용 사용자 지정값

        Returns:
            Dict: 주문 상세 정보
        """
        params = {}
        if uuid:
            params['uuid'] = uuid
        elif identifier:
            params['identifier'] = identifier
        else:
            raise ValueError("uuid 또는 identifier 중 하나는 필수입니다")

        return await self._make_request('GET', '/order', params=params)

    async def get_orders(
        self,
        market: Optional[str] = None,
        uuids: Optional[List[str]] = None,
        identifiers: Optional[List[str]] = None,
        state: Optional[Literal['wait', 'watch', 'done', 'cancel']] = None,
        states: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 100,
        order_by: Literal['asc', 'desc'] = 'desc'
    ) -> Dict[str, Dict[str, Any]]:
        """
        주문 목록 조회

        Args:
            market: 마켓 코드
            uuids: 주문 UUID 목록
            identifiers: 사용자 지정 식별자 목록
            state: 주문 상태 ('wait': 체결대기, 'watch': 예약주문, 'done': 체결완료, 'cancel': 취소)
            states: 주문 상태 목록
            page: 페이지 번호
            limit: 페이지당 항목 수 (최대 100)
            order_by: 정렬 순서

        Returns:
            Dict[str, Dict]: {
                'order_uuid_1': {...},
                'order_uuid_2': {...}
            }
        """
        params = {
            'page': page,
            'limit': min(limit, 100),
            'order_by': order_by
        }

        if market:
            params['market'] = market
        if uuids:
            params['uuids'] = ','.join(uuids)
        if identifiers:
            params['identifiers'] = ','.join(identifiers)
        if state:
            params['state'] = state
        if states:
            params['states'] = ','.join(states) if isinstance(states, list) else states

        response = await self._make_request('GET', '/orders', params=params)

        # List 응답을 Dict로 변환
        orders_dict = {}
        if isinstance(response, list):
            for order in response:
                if isinstance(order, dict):
                    order_id = order.get('uuid') or order.get('identifier')
                    if order_id:
                        orders_dict[order_id] = order
        return orders_dict

    async def get_open_orders(
        self,
        market: Optional[str] = None,
        state: Optional[Literal['wait', 'watch']] = None,
        page: int = 1,
        limit: int = 100,
        order_by: Literal['asc', 'desc'] = 'desc'
    ) -> Dict[str, Dict[str, Any]]:
        """
        체결 대기 주문 목록 조회

        현재 체결 대기 중인 주문들을 조회합니다.

        Args:
            market: 마켓 코드
            state: 주문 상태 ('wait': 체결대기, 'watch': 예약주문, 기본값: 'wait')
            page: 페이지 번호
            limit: 페이지당 항목 수 (최대 100)
            order_by: 정렬 순서

        Returns:
            Dict[str, Dict]: 체결 대기 주문들
        """
        params = {
            'page': page,
            'limit': min(limit, 100),
            'order_by': order_by,
            'state': state or 'wait'
        }

        if market:
            params['market'] = market

        response = await self._make_request('GET', '/orders/open', params=params)

        # List 응답을 Dict로 변환
        orders_dict = {}
        if isinstance(response, list):
            for order in response:
                if isinstance(order, dict):
                    order_id = order.get('uuid') or order.get('identifier')
                    if order_id:
                        orders_dict[order_id] = order
        return orders_dict

    async def get_closed_orders(
        self,
        market: Optional[str] = None,
        state: Optional[Literal['done', 'cancel']] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
        order_by: Literal['asc', 'desc'] = 'desc'
    ) -> Dict[str, Dict[str, Any]]:
        """
        종료 주문 목록 조회

        체결 완료되거나 취소된 주문들을 조회합니다.
        조회 기간은 최대 7일입니다.

        Args:
            market: 마켓 코드
            state: 주문 상태 ('done': 체결완료, 'cancel': 취소, 기본값: 모든 상태)
            start_time: 조회 시작 시간 (ISO 8601)
            end_time: 조회 종료 시간 (ISO 8601)
            limit: 페이지당 항목 수 (최대 1000)
            order_by: 정렬 순서

        Returns:
            Dict[str, Dict]: 종료된 주문들
        """
        params = {
            'limit': min(limit, 1000),
            'order_by': order_by,
            'state': state or 'done,cancel'
        }

        if market:
            params['market'] = market
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time

        response = await self._make_request('GET', '/orders/closed', params=params)

        # List 응답을 Dict로 변환
        orders_dict = {}
        if isinstance(response, list):
            for order in response:
                if isinstance(order, dict):
                    order_id = order.get('uuid') or order.get('identifier')
                    if order_id:
                        orders_dict[order_id] = order
        return orders_dict

    async def cancel_order(self, uuid: Optional[str] = None, identifier: Optional[str] = None) -> Dict[str, Any]:
        """
        주문 취소

        Args:
            uuid: 주문 UUID (uuid 또는 identifier 중 하나 필수)
            identifier: 조회용 사용자 지정값

        Returns:
            Dict: 취소된 주문 정보
        """
        data = {}
        if uuid:
            data['uuid'] = uuid
        elif identifier:
            data['identifier'] = identifier
        else:
            raise ValueError("uuid 또는 identifier 중 하나는 필수입니다")

        return await self._make_request('DELETE', '/order', data=data)

    # ================================================================
    # 고급 주문 기능 - 대량 처리 및 특수 주문
    # ================================================================

    async def cancel_orders_by_ids(
        self,
        uuids: Optional[List[str]] = None,
        identifiers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        ID로 주문 목록 취소

        최대 20개의 주문을 한 번에 취소할 수 있습니다.

        Args:
            uuids: 취소할 주문 UUID 목록 (최대 20개)
            identifiers: 취소할 주문 식별자 목록 (최대 20개)

        Returns:
            Dict: 취소 결과 (성공/실패 주문 목록)
        """
        if not uuids and not identifiers:
            raise ValueError("uuids 또는 identifiers 중 하나는 필수입니다")
        if uuids and identifiers:
            raise ValueError("uuids와 identifiers는 동시에 사용할 수 없습니다")
        if uuids and len(uuids) > 20:
            raise ValueError("취소 가능한 최대 UUID 개수는 20개입니다")
        if identifiers and len(identifiers) > 20:
            raise ValueError("취소 가능한 최대 identifier 개수는 20개입니다")

        params = {}
        if uuids:
            params['uuids'] = ','.join(uuids)
        if identifiers:
            params['identifiers'] = ','.join(identifiers)

        return await self._make_request('DELETE', '/orders/uuids', params=params)

    async def batch_cancel_orders(
        self,
        quote_currencies: Optional[List[str]] = None,
        cancel_side: Literal['all', 'ask', 'bid'] = 'all',
        count: int = 20,
        order_by: Literal['asc', 'desc'] = 'desc'
    ) -> Dict[str, Any]:
        """
        주문 일괄 취소

        조건을 만족하는 최대 300개의 주문을 일괄 취소합니다.

        Args:
            quote_currencies: 기준 통화 목록 (['KRW', 'BTC', 'USDT'])
            cancel_side: 취소할 주문 방향 ('all': 전체, 'ask': 매도, 'bid': 매수)
            count: 취소할 최대 주문 수 (최대 300)
            order_by: 정렬 순서

        Returns:
            Dict: 취소 결과

        Note:
            Rate Limit: 최대 2초당 1회 호출 가능
        """
        params = {
            'cancel_side': cancel_side,
            'count': min(count, 300),
            'order_by': order_by
        }

        if quote_currencies:
            params['quote_currencies'] = ','.join(quote_currencies)

        return await self._make_request('DELETE', '/orders/open', params=params)

    # ================================================================
    # 체결 내역 조회
    # ================================================================

    async def get_trades_history(
        self,
        market: Optional[str] = None,
        limit: int = 100,
        order_by: Literal['asc', 'desc'] = 'desc'
    ) -> Dict[str, Dict[str, Any]]:
        """
        내 체결 내역 조회

        Args:
            market: 마켓 코드
            limit: 조회 개수 (최대 500)
            order_by: 정렬 순서

        Returns:
            Dict[str, Dict]: {
                'trade_id_1': {...},
                'trade_id_2': {...}
            }
        """
        params = {
            'limit': min(limit, 500),
            'order_by': order_by
        }
        if market:
            params['market'] = market

        response = await self._make_request('GET', '/trades', params=params)

        # List 응답을 Dict로 변환
        trades_dict = {}
        if isinstance(response, list):
            for i, trade in enumerate(response):
                if isinstance(trade, dict):
                    trade_id = trade.get('uuid', f'trade_{i}')
                    trades_dict[trade_id] = trade
        return trades_dict


# ================================================================
# 편의 팩토리 함수
# ================================================================

def create_upbit_private_client(access_key: str, secret_key: str) -> UpbitPrivateClient:
    """업비트 프라이빗 API 클라이언트 생성 (편의 함수)"""
    return UpbitPrivateClient(access_key=access_key, secret_key=secret_key)
