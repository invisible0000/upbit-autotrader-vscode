from typing import List, Dict, Any, Optional, Union
from decimal import Decimal

from upbit_auto_trading.infrastructure.external_apis.common.api_client_base import (
    BaseApiClient, RateLimitConfig, ApiClientError
)
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_auth import UpbitAuthenticator


class UpbitPrivateClient(BaseApiClient):
    """Upbit 프라이빗 API 클라이언트 - 인증이 필요한 API 담당"""

    def __init__(self, access_key: str, secret_key: str):
        """
        Args:
            access_key: Upbit API Access Key
            secret_key: Upbit API Secret Key
        """
        if not access_key or not secret_key:
            raise ValueError("API 키가 설정되지 않았습니다.")

        # Upbit 프라이빗 API 제한: 초당 8회, 분당 200회 (기존 설정 보존)
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

    def _prepare_headers(self, method: str, endpoint: str,
                         params: Optional[Dict], data: Optional[Dict]) -> Dict[str, str]:
        """프라이빗 API용 JWT 인증 헤더 준비"""
        return self._auth.get_private_headers(query_params=params, request_body=data)

    async def get_accounts(self) -> List[Dict[str, Any]]:
        """계좌 정보 조회"""
        response = await self._make_request('GET', '/accounts')

        if not response.success:
            raise ApiClientError(f"계좌 정보 조회 실패: {response.error_message}",
                                 response.status_code, response.data)

        return response.data

    async def get_account_balance(self, currency: str) -> Optional[Dict[str, Any]]:
        """특정 화폐 잔고 조회"""
        accounts = await self.get_accounts()

        for account in accounts:
            if account.get('currency') == currency:
                return {
                    'currency': account['currency'],
                    'balance': float(account['balance']),
                    'locked': float(account['locked']),
                    'avg_buy_price': float(account.get('avg_buy_price', 0)),
                    'avg_buy_price_modified': account.get('avg_buy_price_modified', False),
                    'unit_currency': account.get('unit_currency')
                }

        return None

    async def place_order(self, market: str, side: str, volume: Optional[str] = None,
                          price: Optional[str] = None, ord_type: str = 'limit',
                          identifier: Optional[str] = None) -> Dict[str, Any]:
        """주문 실행

        Args:
            market: 마켓 코드 (예: "KRW-BTC")
            side: 주문 방향 ('bid': 매수, 'ask': 매도)
            volume: 주문량 (ord_type이 'limit' 또는 'market'일 때)
            price: 주문 가격 (ord_type이 'limit' 또는 'price'일 때)
            ord_type: 주문 유형 ('limit': 지정가, 'price': 시장가 매수, 'market': 시장가 매도)
            identifier: 조회용 사용자 지정 값 (선택적)
        """
        if side not in ['bid', 'ask']:
            raise ValueError("side는 'bid' 또는 'ask'여야 합니다.")

        if ord_type not in ['limit', 'price', 'market']:
            raise ValueError("ord_type은 'limit', 'price', 'market' 중 하나여야 합니다.")

        data = {
            'market': market,
            'side': side,
            'ord_type': ord_type
        }

        if ord_type == 'limit':
            if not volume or not price:
                raise ValueError("지정가 주문에는 volume과 price가 필요합니다.")
            data['volume'] = str(volume)
            data['price'] = str(price)
        elif ord_type == 'price':
            if not price:
                raise ValueError("시장가 매수 주문에는 price가 필요합니다.")
            data['price'] = str(price)
        elif ord_type == 'market':
            if not volume:
                raise ValueError("시장가 매도 주문에는 volume이 필요합니다.")
            data['volume'] = str(volume)

        if identifier:
            data['identifier'] = identifier

        response = await self._make_request('POST', '/orders', data=data)

        if not response.success:
            raise ApiClientError(f"주문 실행 실패: {response.error_message}",
                                 response.status_code, response.data)

        return response.data

    async def cancel_order(self, uuid: Optional[str] = None,
                           identifier: Optional[str] = None) -> Dict[str, Any]:
        """주문 취소

        Args:
            uuid: 주문 UUID (uuid와 identifier 중 하나는 필수)
            identifier: 조회용 사용자 지정 값
        """
        if not uuid and not identifier:
            raise ValueError("uuid와 identifier 중 하나는 필수입니다.")

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

    async def get_order(self, uuid: Optional[str] = None,
                        identifier: Optional[str] = None) -> Dict[str, Any]:
        """개별 주문 조회

        Args:
            uuid: 주문 UUID (uuid와 identifier 중 하나는 필수)
            identifier: 조회용 사용자 지정 값
        """
        if not uuid and not identifier:
            raise ValueError("uuid와 identifier 중 하나는 필수입니다.")

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

    async def get_orders(self, market: Optional[str] = None, uuids: Optional[List[str]] = None,
                         identifiers: Optional[List[str]] = None, state: Optional[str] = None,
                         states: Optional[List[str]] = None, page: int = 1,
                         limit: int = 100, order_by: str = 'desc') -> List[Dict[str, Any]]:
        """주문 목록 조회

        Args:
            market: 마켓 코드 (선택적)
            uuids: 주문 UUID 목록 (선택적)
            identifiers: 조회용 사용자 지정 값 목록 (선택적)
            state: 주문 상태 ('wait', 'watch', 'done', 'cancel') (선택적)
            states: 주문 상태 목록 (선택적)
            page: 페이지 번호
            limit: 페이지당 개수 (최대 100)
            order_by: 정렬 순서 ('asc', 'desc')
        """
        if limit > 100:
            raise ValueError("한 번에 최대 100개까지만 조회 가능합니다")

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

        if not response.success:
            raise ApiClientError(f"주문 목록 조회 실패: {response.error_message}",
                                 response.status_code, response.data)

        return response.data

    async def get_order_chance(self, market: str) -> Dict[str, Any]:
        """주문 가능 정보 조회

        Args:
            market: 마켓 코드 (예: "KRW-BTC")
        """
        params = {'market': market}

        response = await self._make_request('GET', '/orders/chance', params=params)

        if not response.success:
            raise ApiClientError(f"주문 가능 정보 조회 실패: {response.error_message}",
                                 response.status_code, response.data)

        return response.data

    async def get_orders_chance_batch(self, markets: List[str]) -> Dict[str, Dict[str, Any]]:
        """여러 마켓의 주문 가능 정보 일괄 조회"""
        import asyncio

        if len(markets) > 10:
            raise ValueError("한 번에 최대 10개 마켓까지만 조회 가능합니다")

        try:
            tasks = [self.get_order_chance(market) for market in markets]
            results = await asyncio.gather(*tasks)

            return {market: result for market, result in zip(markets, results)}

        except Exception as e:
            self._logger.error(f"주문 가능 정보 일괄 조회 실패: {e}")
            raise ApiClientError(f"주문 가능 정보 일괄 조회 실패: {str(e)}")

    async def place_limit_buy_order(self, market: str, price: Union[str, float, Decimal],
                                    volume: Union[str, float, Decimal],
                                    identifier: Optional[str] = None) -> Dict[str, Any]:
        """지정가 매수 주문"""
        return await self.place_order(
            market=market,
            side='bid',
            volume=str(volume),
            price=str(price),
            ord_type='limit',
            identifier=identifier
        )

    async def place_limit_sell_order(self, market: str, price: Union[str, float, Decimal],
                                     volume: Union[str, float, Decimal],
                                     identifier: Optional[str] = None) -> Dict[str, Any]:
        """지정가 매도 주문"""
        return await self.place_order(
            market=market,
            side='ask',
            volume=str(volume),
            price=str(price),
            ord_type='limit',
            identifier=identifier
        )

    async def place_market_buy_order(self, market: str, price: Union[str, float, Decimal],
                                     identifier: Optional[str] = None) -> Dict[str, Any]:
        """시장가 매수 주문 (KRW 금액 지정)"""
        return await self.place_order(
            market=market,
            side='bid',
            price=str(price),
            ord_type='price',
            identifier=identifier
        )

    async def place_market_sell_order(self, market: str, volume: Union[str, float, Decimal],
                                      identifier: Optional[str] = None) -> Dict[str, Any]:
        """시장가 매도 주문 (코인 수량 지정)"""
        return await self.place_order(
            market=market,
            side='ask',
            volume=str(volume),
            ord_type='market',
            identifier=identifier
        )

    async def get_deposits(self, currency: Optional[str] = None, state: Optional[str] = None,
                           uuids: Optional[List[str]] = None, txids: Optional[List[str]] = None,
                           limit: int = 100, page: int = 1, order_by: str = 'desc') -> List[Dict[str, Any]]:
        """입금 리스트 조회"""
        if limit > 100:
            raise ValueError("한 번에 최대 100개까지만 조회 가능합니다")

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

        if not response.success:
            raise ApiClientError(f"입금 리스트 조회 실패: {response.error_message}",
                                 response.status_code, response.data)

        return response.data

    async def get_withdraws(self, currency: Optional[str] = None, state: Optional[str] = None,
                            uuids: Optional[List[str]] = None, txids: Optional[List[str]] = None,
                            limit: int = 100, page: int = 1, order_by: str = 'desc') -> List[Dict[str, Any]]:
        """출금 리스트 조회"""
        if limit > 100:
            raise ValueError("한 번에 최대 100개까지만 조회 가능합니다")

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

        if not response.success:
            raise ApiClientError(f"출금 리스트 조회 실패: {response.error_message}",
                                 response.status_code, response.data)

        return response.data

    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """포트폴리오 요약 정보 조회"""
        try:
            accounts = await self.get_accounts()

            total_krw = 0.0
            holdings = []

            for account in accounts:
                currency = account['currency']
                balance = float(account['balance'])
                locked = float(account['locked'])
                total_balance = balance + locked

                if total_balance > 0:
                    holding = {
                        'currency': currency,
                        'balance': balance,
                        'locked': locked,
                        'total': total_balance,
                        'avg_buy_price': float(account.get('avg_buy_price', 0))
                    }

                    if currency == 'KRW':
                        total_krw += total_balance
                        holding['krw_value'] = total_balance
                    else:
                        # 현재가 정보가 필요한 경우 퍼블릭 클라이언트와 연동 필요
                        holding['krw_value'] = 0.0

                    holdings.append(holding)

            return {
                'total_krw': total_krw,
                'holdings': holdings,
                'currencies_count': len(holdings)
            }

        except Exception as e:
            self._logger.error(f"포트폴리오 요약 조회 실패: {e}")
            raise ApiClientError(f"포트폴리오 요약 조회 실패: {str(e)}")
