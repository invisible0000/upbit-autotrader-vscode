"""
업비트 프라이빗 API 클라이언트 - 어댑터 패턴 적용

인증이 필요한 REST API 기능을 담당합니다.
"""
from typing import List, Dict, Any, Optional, Literal
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
                 rate_limiter: Optional[Any] = None):
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

    async def get_accounts(self) -> Dict[str, Dict[str, Any]]:
        """
        계좌 정보 조회 - Dict 통일

        Returns:
            Dict[str, Dict]: {
                'KRW': {'currency': 'KRW', 'balance': '20000', ...},
                'BTC': {'currency': 'BTC', 'balance': '0.00005', ...}
            }
        """
        response = await self._make_request('GET', '/accounts')
        # List 응답을 Dict로 변환
        accounts_dict = {}
        if isinstance(response.data, list):
            for account in response.data:
                currency = account.get('currency')
                if currency:
                    accounts_dict[currency] = account
        return accounts_dict

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
                         order_by: Literal['asc', 'desc'] = 'desc') -> Dict[str, Dict[str, Any]]:
        """
        주문 목록 조회 - Dict 통일 (기본 메서드, Deprecated 예정)

        Note:
            이 메서드는 일반적인 주문 목록 조회용입니다.
            더 구체적인 용도로는 get_open_orders, get_closed_orders, get_orders_by_ids를 사용하세요.

        Returns:
            Dict[str, Dict]: {
                'order_uuid_1': {...},
                'order_uuid_2': {...}
            }
        """
        params = {
            'page': page,
            'limit': limit,
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
        if isinstance(response.data, list):
            for order in response.data:
                order_id = order.get('uuid') or order.get('identifier')
                if order_id:
                    orders_dict[order_id] = order
        return orders_dict

    async def get_orders_by_ids(self, market: Optional[str] = None,
                                uuids: Optional[List[str]] = None,
                                identifiers: Optional[List[str]] = None,
                                order_by: Literal['asc', 'desc'] = 'desc') -> Dict[str, Dict[str, Any]]:
        """
        id로 주문 목록 조회

        UUID 또는 Identifier 목록으로 주문을 조회합니다.
        조회하고자 하는 주문들의 UUID 또는 Identifier를 알고 있는 경우 사용합니다.

        Args:
            market: 조회하고자 하는 페어(거래쌍)
            uuids: 조회하고자 하는 주문의 UUID 목록 (최대 100개)
            identifiers: 조회하고자 하는 주문의 클라이언트 지정 식별자 목록 (최대 100개)
            order_by: 결과 정렬 방식 ('desc': 최신순, 'asc': 오래된순)

        Returns:
            Dict[str, Dict]: {
                'order_uuid_1': {...},
                'order_uuid_2': {...}
            }

        Note:
            - uuids 또는 identifiers 중 하나는 필수입니다
            - 두 파라미터를 동시에 사용할 수 없습니다
            - 조회 가능한 최대 주문 개수는 100개입니다
        """
        if not uuids and not identifiers:
            raise ValueError("uuids 또는 identifiers 중 하나는 필수입니다")

        if uuids and identifiers:
            raise ValueError("uuids와 identifiers는 동시에 사용할 수 없습니다")

        if uuids and len(uuids) > 100:
            raise ValueError("조회 가능한 최대 UUID 개수는 100개입니다")

        if identifiers and len(identifiers) > 100:
            raise ValueError("조회 가능한 최대 identifier 개수는 100개입니다")

        params = {
            'order_by': order_by
        }

        if market:
            params['market'] = market
        if uuids:
            params['uuids'] = ','.join(uuids)
        if identifiers:
            params['identifiers'] = ','.join(identifiers)

        response = await self._make_request('GET', '/orders/uuids', params=params)

        # List 응답을 Dict로 변환
        orders_dict = {}
        if isinstance(response.data, list):
            for order in response.data:
                order_id = order.get('uuid') or order.get('identifier')
                if order_id:
                    orders_dict[order_id] = order
        return orders_dict

    async def get_open_orders(self, market: Optional[str] = None,
                              state: Optional[Literal['wait', 'watch']] = None,
                              states: Optional[List[str]] = None,
                              page: int = 1, limit: int = 100,
                              order_by: Literal['asc', 'desc'] = 'desc') -> Dict[str, Dict[str, Any]]:
        """
        체결 대기 주문 목록 조회

        계정의 체결 대기 주문 목록을 조회할 수 있습니다.
        필터 파라미터인 페어와 주문 상태를 선택적으로 입력하여 해당 조건을 만족하는 체결 대기 주문들을 조회할 수 있습니다.

        Args:
            market: 조회하고자 하는 페어(거래쌍)
            state: 주문 상태 ('wait': 체결 대기, 'watch': 예약 주문 대기)
            states: 주문 상태 배열 형식 (['wait', 'watch'])
            page: 조회할 페이지 번호 (기본값: 1)
            limit: 페이지당 항목 수 (최대 100개, 기본값: 100)
            order_by: 결과 정렬 방식 ('desc': 최신순, 'asc': 오래된순)

        Returns:
            Dict[str, Dict]: {
                'order_uuid_1': {...},
                'order_uuid_2': {...}
            }

        Note:
            - state와 states는 동시에 사용할 수 없습니다
            - 미지정시 기본값은 'wait'입니다
        """
        if state and states:
            raise ValueError("state와 states는 동시에 사용할 수 없습니다")

        params = {
            'page': page,
            'limit': min(limit, 100),
            'order_by': order_by
        }

        if market:
            params['market'] = market
        if state:
            params['state'] = state
        elif states:
            params['states'] = states
        else:
            params['state'] = 'wait'  # 기본값

        response = await self._make_request('GET', '/orders/open', params=params)

        # List 응답을 Dict로 변환
        orders_dict = {}
        if isinstance(response.data, list):
            for order in response.data:
                order_id = order.get('uuid') or order.get('identifier')
                if order_id:
                    orders_dict[order_id] = order
        return orders_dict

    async def get_closed_orders(self, market: Optional[str] = None,
                                state: Optional[Literal['done', 'cancel']] = None,
                                states: Optional[List[str]] = None,
                                start_time: Optional[str] = None,
                                end_time: Optional[str] = None,
                                limit: int = 100,
                                order_by: Literal['asc', 'desc'] = 'desc') -> Dict[str, Dict[str, Any]]:
        """
        종료 주문 목록 조회

        종료 주문(Closed Order) 목록을 조회합니다.
        종료 주문은 전량 체결 주문과 취소 주문을 포함합니다.
        조회 기간을 정하는 경우 최대 7일 구간을 조회할 수 있습니다.

        Args:
            market: 조회하고자 하는 페어(거래쌍)
            state: 주문 상태 ('done': 체결 완료, 'cancel': 주문 취소)
            states: 주문 상태 배열 형식 (['done', 'cancel'])
            start_time: 조회 기간의 시작 시각 (ISO 8601 형식 또는 밀리초 타임스탬프)
            end_time: 조회 기간의 종료 시각 (ISO 8601 형식 또는 밀리초 타임스탬프)
            limit: 페이지당 항목 수 (최대 1000개, 기본값: 100)
            order_by: 결과 정렬 방식 ('desc': 최신순, 'asc': 오래된순)

        Returns:
            Dict[str, Dict]: {
                'order_uuid_1': {...},
                'order_uuid_2': {...}
            }

        Note:
            - state와 states는 동시에 사용할 수 없습니다
            - 미지정시 기본값은 'done,cancel' (모든 상태)
            - 조회 가능 범위는 최대 7일입니다
            - start_time만 입력시 해당 시각 기준 이후 7일
            - end_time만 입력시 해당 시각 기준 이전 7일
            - 둘 다 미입력시 요청 시각 기준 이전 7일
        """
        if state and states:
            raise ValueError("state와 states는 동시에 사용할 수 없습니다")

        params = {
            'limit': min(limit, 1000),
            'order_by': order_by
        }

        if market:
            params['market'] = market
        if state:
            params['state'] = state
        elif states:
            params['states'] = states
        else:
            params['state'] = 'done,cancel'  # 기본값

        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time

        response = await self._make_request('GET', '/orders/closed', params=params)

        # List 응답을 Dict로 변환
        orders_dict = {}
        if isinstance(response.data, list):
            for order in response.data:
                order_id = order.get('uuid') or order.get('identifier')
                if order_id:
                    orders_dict[order_id] = order
        return orders_dict

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

    async def cancel_orders_by_ids(self, uuids: Optional[List[str]] = None,
                                   identifiers: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        id로 주문 목록 취소 접수

        UUID 또는 Identifier 목록으로 취소 대상 주문을 지정 취소합니다.
        한 번의 요청으로 최대 20개의 주문을 취소할 수 있습니다.

        Args:
            uuids: 취소하고자 하는 주문의 UUID 목록 (최대 20개)
            identifiers: 취소하고자 하는 주문의 클라이언트 지정 식별자 목록 (최대 20개)

        Returns:
            Dict: 취소 결과 정보 {
                'success': {
                    'count': 성공한 주문 수,
                    'orders': [...] 성공한 주문 목록
                },
                'failed': {
                    'count': 실패한 주문 수,
                    'orders': [...] 실패한 주문 목록
                }
            }

        Note:
            - uuids 또는 identifiers 중 하나는 필수입니다
            - 두 파라미터를 동시에 사용할 수 없습니다
            - 취소 가능한 최대 주문 개수는 20개입니다
            - 쿼리 파라미터 형식만 지원합니다 (Request Body 형식 지원 안함)

        Raises:
            ValueError: 매개변수 검증 실패시
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
            # 리스트를 쿼리 파라미터 배열로 변환하여 전달
            params['uuids'] = ','.join(uuids)
        if identifiers:
            # 리스트를 쿼리 파라미터 배열로 변환하여 전달
            params['identifiers'] = ','.join(identifiers)

        response = await self._make_request('DELETE', '/orders/uuids', params=params)
        return response.data

    async def batch_cancel_orders(self, quote_currencies: Optional[List[str]] = None,
                                  cancel_side: Literal['all', 'ask', 'bid'] = 'all',
                                  count: int = 20, order_by: Literal['asc', 'desc'] = 'desc',
                                  pairs: Optional[List[str]] = None,
                                  exclude_pairs: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        주문 일괄 취소 접수

        조건을 지정하여 해당 조건을 만족하는 최대 300개의 주문을 일괄 취소합니다.
        오직 체결 대기(WAIT) 상태의 주문만 취소할 수 있습니다.

        Args:
            quote_currencies: 주문 취소 대상 마켓 목록 (KRW, BTC, USDT 등)
            cancel_side: 매수/매도 구분 ('all': 전체, 'ask': 매도, 'bid': 매수)
            count: 취소할 주문의 최대 개수 (기본값: 20, 최대: 300)
            order_by: 정렬 방식 ('desc': 최신순, 'asc': 오래된순)
            pairs: 페어 목록 (최대 20개)
            exclude_pairs: 제외할 페어 목록 (최대 20개)

        Returns:
            Dict: 취소 결과 정보 (성공/실패 주문 목록)

        Rate Limit:
            최대 2초당 1회 호출 가능

        Note:
            - pairs와 quote_currencies는 동시에 사용할 수 없음
            - 최대 300개의 주문 취소 가능
            - 체결 대기(WAIT) 상태의 주문만 취소 가능
        """
        params = {
            'cancel_side': cancel_side,
            'count': min(count, 300),
            'order_by': order_by
        }

        # pairs와 quote_currencies는 동시 사용 불가
        if pairs and quote_currencies:
            raise ValueError("pairs와 quote_currencies는 동시에 사용할 수 없습니다")

        if quote_currencies:
            params['quote_currencies'] = ','.join(quote_currencies)
        elif pairs:
            params['pairs'] = ','.join(pairs)

        if exclude_pairs:
            params['exclude_pairs'] = ','.join(exclude_pairs)

        response = await self._make_request('DELETE', '/orders/open', params=params)
        return response.data

    async def cancel_and_new_order(self,
                                   prev_order_uuid: Optional[str] = None,
                                   prev_order_identifier: Optional[str] = None,
                                   new_ord_type: Literal['limit', 'price', 'market', 'best'] = 'limit',
                                   new_volume: Optional[str] = None,
                                   new_price: Optional[str] = None,
                                   new_identifier: Optional[str] = None,
                                   new_time_in_force: Optional[Literal['ioc', 'fok', 'post_only']] = None,
                                   new_smp_type: Optional[Literal['cancel_maker', 'cancel_taker', 'reduce']] = None
                                   ) -> Dict[str, Any]:
        """
        취소 후 재주문

        한 번의 요청으로 기존 주문을 취소하고 신규 주문을 생성합니다.
        신규 주문은 기존 주문과 동일한 페어, 동일한 주문 방향에 대해서만 생성 가능합니다.

        Args:
            prev_order_uuid: 취소할 주문의 UUID
            prev_order_identifier: 취소할 주문의 클라이언트 지정 식별자
            new_ord_type: 신규 주문 유형 ('limit', 'price', 'market', 'best')
            new_volume: 신규 주문 수량 (숫자 문자열 또는 "remain_only")
            new_price: 신규 주문 단가 또는 총액 (숫자 문자열)
            new_identifier: 신규 주문의 클라이언트 지정 식별자
            new_time_in_force: 주문 체결 조건 ('ioc', 'fok', 'post_only')
            new_smp_type: 자전거래 방지 모드 ('cancel_maker', 'cancel_taker', 'reduce')

        Returns:
            Dict: 취소된 주문 정보와 신규 생성된 주문 UUID

        Note:
            - prev_order_uuid 또는 prev_order_identifier 중 하나는 필수
            - 주문 유형별 필수 파라미터:
              * limit: new_volume, new_price 필수
              * price: new_price 필수 (시장가 매수)
              * market: new_volume 필수 (시장가 매도)
              * best: new_time_in_force 필수 (ioc 또는 fok)
            - 기존 identifier는 재사용 불가
            - 신규 주문은 기존 주문 취소 완료 후 생성됨
        """
        # 취소 대상 주문 지정 검증
        if not prev_order_uuid and not prev_order_identifier:
            raise ValueError("prev_order_uuid 또는 prev_order_identifier 중 하나는 필수입니다")

        if prev_order_uuid and prev_order_identifier:
            raise ValueError("prev_order_uuid와 prev_order_identifier는 동시에 사용할 수 없습니다")

        data = {
            'new_ord_type': new_ord_type
        }

        # 취소 대상 주문 지정
        if prev_order_uuid:
            data['prev_order_uuid'] = prev_order_uuid
        elif prev_order_identifier:
            data['prev_order_identifier'] = prev_order_identifier

        # 신규 주문 파라미터 설정
        if new_volume:
            data['new_volume'] = new_volume
        if new_price:
            data['new_price'] = new_price
        if new_identifier:
            data['new_identifier'] = new_identifier
        if new_time_in_force:
            data['new_time_in_force'] = new_time_in_force
        if new_smp_type:
            data['new_smp_type'] = new_smp_type

        response = await self._make_request('POST', '/orders/cancel_and_new', data=data)
        return response.data

    async def get_trades_history(self, market: Optional[str] = None,
                                 limit: int = 100,
                                 order_by: Literal['asc', 'desc'] = 'desc') -> Dict[str, Dict[str, Any]]:
        """
        내 체결 내역 조회 - Dict 통일

        Args:
            market: 마켓 코드 (예: KRW-BTC)
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

        response = await self._make_request('GET', '/orders', params=params)

        # List 응답을 Dict로 변환
        trades_dict = {}
        if isinstance(response.data, list):
            for i, trade in enumerate(response.data):
                # trade_id가 있으면 사용, 없으면 인덱스 기반 키 생성
                trade_id = trade.get('uuid', f'trade_{i}')
                trades_dict[trade_id] = trade
        return trades_dict


# ================================================================
# Note: create_upbit_private_client 함수는 보안상 제거됨
# 직접 UpbitPrivateClient(access_key, secret_key) 생성자를 사용하세요
# ================================================================
