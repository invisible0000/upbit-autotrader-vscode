"""
업비트 프라이빗 API 클라이언트 - 어댑터 패턴 적용

인증이 필요한 REST API 기능을 담당합니다.
"""
from typing import List, Dict, Any, Optional, Union, Literal
from decimal import Decimal

from ..core.base_client import BaseExchangeClient
from ..core.rate_limiter import UniversalRateLimiter, ExchangeRateLimitConfig
from ..adapters.upbit_adapter import UpbitAdapter
from .upbit_auth import UpbitAuthenticator


class UpbitPrivateClient(BaseExchangeClient):
    """
    업비트 프라이빗 API 클라이언트

    특징:
    - 인증이 필요한 모든 REST API 기능 제공
    - JWT 토큰 기반 인증
    - Rate Limiting 적용
    - 견고한 에러 처리
    """

    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None,
                 adapter: Optional[UpbitAdapter] = None,
                 rate_limiter: Optional[UniversalRateLimiter] = None):
        """
        업비트 프라이빗 API 클라이언트 초기화

        Args:
            access_key: Upbit API Access Key (기본값: 환경변수 또는 설정에서 로드)
            secret_key: Upbit API Secret Key (기본값: 환경변수 또는 설정에서 로드)
            adapter: 업비트 어댑터 (기본값: 자동 생성)
            rate_limiter: Rate Limiter (기본값: Private API용 설정)
        """
        if adapter is None:
            adapter = UpbitAdapter()
        if rate_limiter is None:
            config = ExchangeRateLimitConfig.for_upbit_private()
            rate_limiter = UniversalRateLimiter(config)

        super().__init__(adapter, rate_limiter)

        # 인증 관리자 초기화
        self._auth = UpbitAuthenticator(access_key, secret_key)
        if not self._auth.is_authenticated():
            raise ValueError("API 키가 설정되지 않았습니다. 인증이 필요한 API는 사용할 수 없습니다.")

    def _prepare_headers(self, method: str, endpoint: str,
                         params: Optional[Dict], data: Optional[Dict]) -> Dict[str, str]:
        """프라이빗 API용 JWT 인증 헤더 준비"""
        return self._auth.get_private_headers(query_params=params, request_body=data)

    # ================================================================
    # 자산(Asset) API
    # ================================================================

    async def get_accounts(self) -> List[Dict[str, Any]]:
        """
        계좌 정보 조회

        Returns:
            List[Dict]: 보유 자산 목록
        """
        response = await self._make_request('GET', '/accounts')
        return response.data

    # ================================================================
    # 주문(Order) API
    # ================================================================

    async def get_orders_chance(self, market: str) -> Dict[str, Any]:
        """
        페어별 주문 가능 정보 조회

        Args:
            market: 마켓 아이디 (예: KRW-BTC)

        Returns:
            Dict: 주문 가능 정보
        """
        params = {'market': market}
        response = await self._make_request('GET', '/orders/chance', params=params)
        return response.data

    async def place_order(self, market: str, side: Literal['bid', 'ask'],
                         ord_type: Literal['limit', 'price', 'market'],
                         volume: Optional[Decimal] = None, price: Optional[Decimal] = None,
                         identifier: Optional[str] = None) -> Dict[str, Any]:
        """
        주문 생성

        Args:
            market: 마켓 아이디 (예: KRW-BTC)
            side: 주문 종류 ('bid': 매수, 'ask': 매도)
            ord_type: 주문 타입 ('limit': 지정가, 'price': 시장가 매수, 'market': 시장가 매도)
            volume: 주문 수량 (지정가, 시장가 매도 시 필수)
            price: 주문 가격 (지정가, 시장가 매수 시 필수)
            identifier: 조회용 사용자 지정값 (선택)

        Returns:
            Dict: 생성된 주문 정보
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

        response = await self._make_request('POST', '/orders', data=data)
        return response.data

    async def get_order(self, uuid: Optional[str] = None,
                       identifier: Optional[str] = None) -> Dict[str, Any]:
        """
        개별 주문 조회

        Args:
            uuid: 주문 UUID (uuid 또는 identifier 중 하나 필수)
            identifier: 조회용 사용자 지정값

        Returns:
            Dict: 주문 정보
        """
        params = {}
        if uuid:
            params['uuid'] = uuid
        elif identifier:
            params['identifier'] = identifier
        else:
            raise ValueError("uuid 또는 identifier 중 하나는 필수입니다")

        response = await self._make_request('GET', '/order', params=params)
        return response.data

    async def get_orders(self, market: Optional[str] = None,
                        uuids: Optional[List[str]] = None,
                        identifiers: Optional[List[str]] = None,
                        state: Optional[Literal['wait', 'watch', 'done', 'cancel']] = None,
                        states: Optional[List[str]] = None,
                        page: int = 1, limit: int = 100,
                        order_by: Literal['asc', 'desc'] = 'desc') -> List[Dict[str, Any]]:
        """
        주문 목록 조회

        Args:
            market: 마켓 아이디
            uuids: 주문 UUID 목록 (최대 100개)
            identifiers: 사용자 지정값 목록 (최대 100개)
            state: 주문 상태
            states: 주문 상태 목록
            page: 페이지 수 (기본: 1)
            limit: 요청 개수 (기본: 100, 최대: 100)
            order_by: 정렬 방식

        Returns:
            List[Dict]: 주문 목록
        """
        params = {
            'page': page,
            'limit': limit,
            'order_by': order_by
        }

        if market:
            params['market'] = market
        if uuids:
            params['uuids'] = uuids
        if identifiers:
            params['identifiers'] = identifiers
        if state:
            params['state'] = state
        if states:
            params['states'] = states

        response = await self._make_request('GET', '/orders', params=params)
        return response.data

    async def cancel_order(self, uuid: Optional[str] = None,
                          identifier: Optional[str] = None) -> Dict[str, Any]:
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

        response = await self._make_request('DELETE', '/order', data=data)
        return response.data

    async def cancel_orders(self, uuids: Optional[List[str]] = None,
                           identifiers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        주문 일괄 취소

        Args:
            uuids: 취소할 주문 UUID 목록
            identifiers: 취소할 사용자 지정값 목록

        Returns:
            List[Dict]: 취소된 주문 목록
        """
        data = {}
        if uuids:
            data['uuids'] = uuids
        elif identifiers:
            data['identifiers'] = identifiers
        else:
            raise ValueError("uuids 또는 identifiers 중 하나는 필수입니다")

        response = await self._make_request('DELETE', '/orders', data=data)
        return response.data

    async def get_trades_history(self, market: Optional[str] = None,
                                 limit: int = 100,
                                 order_by: Literal['asc', 'desc'] = 'desc') -> List[Dict[str, Any]]:
        """
        내 체결 내역 조회 (기본 메서드)

        Args:
            market: 마켓 코드 (예: KRW-BTC)
            limit: 조회 개수 (최대 500)
            order_by: 정렬 순서
        """
        params = {
            'limit': min(limit, 500),
            'order_by': order_by
        }
        if market:
            params['market'] = market

        response = await self._make_request('GET', '/orders', params=params)
        return response.data

    # ================================================================
    # 출금(Withdraw) API
    # ================================================================

    async def get_withdraws(self, currency: Optional[str] = None,
                           state: Optional[Literal['submitting', 'submitted', 'almost_accepted',
                                                  'rejected', 'accepted', 'processing',
                                                  'done', 'canceled']] = None,
                           uuids: Optional[List[str]] = None,
                           txids: Optional[List[str]] = None,
                           limit: int = 100, page: int = 1,
                           order_by: Literal['asc', 'desc'] = 'desc') -> List[Dict[str, Any]]:
        """
        출금 목록 조회

        Args:
            currency: 화폐를 의미하는 영문 대문자 코드
            state: 출금 상태
            uuids: 출금 UUID 목록
            txids: 출금 transaction ID 목록
            limit: 요청 개수 (기본: 100, 최대: 100)
            page: 페이지 수 (기본: 1)
            order_by: 정렬 방식

        Returns:
            List[Dict]: 출금 목록
        """
        params = {
            'limit': limit,
            'page': page,
            'order_by': order_by
        }

        if currency:
            params['currency'] = currency
        if state:
            params['state'] = state
        if uuids:
            params['uuids'] = uuids
        if txids:
            params['txids'] = txids

        response = await self._make_request('GET', '/withdraws', params=params)
        return response.data

    async def get_withdraw(self, uuid: Optional[str] = None,
                          txid: Optional[str] = None,
                          currency: Optional[str] = None) -> Dict[str, Any]:
        """
        개별 출금 조회

        Args:
            uuid: 출금 UUID
            txid: 출금 transaction ID
            currency: 화폐를 의미하는 영문 대문자 코드

        Returns:
            Dict: 출금 정보
        """
        params = {}
        if uuid:
            params['uuid'] = uuid
        if txid:
            params['txid'] = txid
        if currency:
            params['currency'] = currency

        if not any([uuid, txid]):
            raise ValueError("uuid 또는 txid 중 하나는 필수입니다")

        response = await self._make_request('GET', '/withdraw', params=params)
        return response.data

    # ================================================================
    # 입금(Deposit) API
    # ================================================================

    async def get_deposits(self, currency: Optional[str] = None,
                          state: Optional[Literal['submitting', 'submitted', 'almost_accepted',
                                                 'rejected', 'accepted', 'processing']] = None,
                          uuids: Optional[List[str]] = None,
                          txids: Optional[List[str]] = None,
                          limit: int = 100, page: int = 1,
                          order_by: Literal['asc', 'desc'] = 'desc') -> List[Dict[str, Any]]:
        """
        입금 목록 조회

        Args:
            currency: 화폐를 의미하는 영문 대문자 코드
            state: 입금 상태
            uuids: 입금 UUID 목록
            txids: 입금 transaction ID 목록
            limit: 요청 개수 (기본: 100, 최대: 100)
            page: 페이지 수 (기본: 1)
            order_by: 정렬 방식

        Returns:
            List[Dict]: 입금 목록
        """
        params = {
            'limit': limit,
            'page': page,
            'order_by': order_by
        }

        if currency:
            params['currency'] = currency
        if state:
            params['state'] = state
        if uuids:
            params['uuids'] = uuids
        if txids:
            params['txids'] = txids

        response = await self._make_request('GET', '/deposits', params=params)
        return response.data

    async def generate_coin_address(self, currency: str) -> Dict[str, Any]:
        """
        입금 주소 생성 요청

        Args:
            currency: 화폐를 의미하는 영문 대문자 코드

        Returns:
            Dict: 생성된 입금 주소 정보
        """
        data = {'currency': currency}
        response = await self._make_request('POST', '/deposits/generate_coin_address', data=data)
        return response.data

    async def get_coin_addresses(self) -> List[Dict[str, Any]]:
        """
        전체 입금 주소 조회

        Returns:
            List[Dict]: 입금 주소 목록
        """
        response = await self._make_request('GET', '/deposits/coin_addresses')
        return response.data

    async def get_coin_address(self, currency: str) -> Dict[str, Any]:
        """
        개별 입금 주소 조회

        Args:
            currency: 화폐를 의미하는 영문 대문자 코드

        Returns:
            Dict: 입금 주소 정보
        """
        params = {'currency': currency}
        response = await self._make_request('GET', '/deposits/coin_address', params=params)
        return response.data


# ================================================================
# 편의 팩토리 함수
# ================================================================

def create_upbit_private_client(access_key: Optional[str] = None,
                               secret_key: Optional[str] = None) -> UpbitPrivateClient:
    """
    업비트 프라이빗 API 클라이언트 생성 (편의 함수)

    Args:
        access_key: Upbit API Access Key (기본값: 환경변수에서 로드)
        secret_key: Upbit API Secret Key (기본값: 환경변수에서 로드)

    Returns:
        UpbitPrivateClient: 설정된 클라이언트 인스턴스
    """
    adapter = UpbitAdapter()
    config = ExchangeRateLimitConfig.for_upbit_private()
    rate_limiter = UniversalRateLimiter(config)

    return UpbitPrivateClient(access_key, secret_key, adapter, rate_limiter)
