from typing import List, Dict, Any, Optional, Union
from decimal import Decimal
import asyncio
from datetime import datetime

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_private_client import UpbitPrivateClient
from upbit_auto_trading.infrastructure.external_apis.common.api_client_base import ApiClientError
from upbit_auto_trading.infrastructure.monitoring.simple_failure_monitor import mark_api_success, mark_api_failure

class UpbitClient:
    """Upbit API 통합 클라이언트 - 퍼블릭과 프라이빗 API를 모두 제공"""

    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None):
        """
        Args:
            access_key: Upbit API Access Key (프라이빗 API 사용 시 필요)
            secret_key: Upbit API Secret Key (프라이빗 API 사용 시 필요)
        """
        self.public = UpbitPublicClient()

        if access_key and secret_key:
            self.private = UpbitPrivateClient(access_key, secret_key)
            self._has_private_access = True
        else:
            self.private = None
            self._has_private_access = False

    def requires_private_access(self) -> None:
        """프라이빗 API 접근 권한이 필요한 메서드에서 사용"""
        if not self._has_private_access:
            raise ApiClientError("이 기능은 API 키가 필요합니다. UpbitClient 생성 시 access_key와 secret_key를 제공해주세요.")

    # ===================
    # 퍼블릭 API 메서드들
    # ===================

    async def get_markets(self, is_details: bool = False) -> List[Dict[str, Any]]:
        """마켓 코드 조회"""
        return await self.public.get_markets(is_details)

    async def get_krw_markets(self) -> List[str]:
        """KRW 마켓 목록 조회"""
        return await self.public.get_krw_markets()

    async def get_candles_minutes(self, market: str, unit: int = 1,
                                  to: Optional[str] = None, count: int = 200) -> List[Dict[str, Any]]:
        """분봉 캔들 조회"""
        try:
            result = await self.public.get_candles_minutes(market, unit, to, count)
            mark_api_success()  # API 성공 기록
            return result
        except Exception:
            mark_api_failure()  # API 실패 기록
            raise

    async def get_candles_days(self, market: str, to: Optional[str] = None,
                               count: int = 200, converting_price_unit: Optional[str] = None) -> List[Dict[str, Any]]:
        """일봉 캔들 조회"""
        return await self.public.get_candles_days(market, to, count, converting_price_unit)

    async def get_candles_weeks(self, market: str, to: Optional[str] = None,
                                count: int = 200) -> List[Dict[str, Any]]:
        """주봉 캔들 조회"""
        return await self.public.get_candles_weeks(market, to, count)

    async def get_candles_months(self, market: str, to: Optional[str] = None,
                                 count: int = 200) -> List[Dict[str, Any]]:
        """월봉 캔들 조회"""
        return await self.public.get_candles_months(market, to, count)

    async def get_orderbook(self, markets: List[str]) -> List[Dict[str, Any]]:
        """호가 정보 조회"""
        try:
            result = await self.public.get_orderbook(markets)
            mark_api_success()  # API 성공 기록
            return result
        except Exception:
            mark_api_failure()  # API 실패 기록
            raise

    async def get_tickers(self, markets: List[str]) -> List[Dict[str, Any]]:
        """현재가 정보 조회"""
        try:
            result = await self.public.get_tickers(markets)
            mark_api_success()  # API 성공 기록
            return result
        except Exception:
            mark_api_failure()  # API 실패 기록
            raise

    async def get_trades_ticks(self, market: str, to: Optional[str] = None,
                               count: int = 200, cursor: Optional[str] = None,
                               days_ago: Optional[int] = None) -> List[Dict[str, Any]]:
        """최근 체결 내역 조회"""
        return await self.public.get_trades_ticks(market, to, count, cursor, days_ago)

    async def get_market_data_batch(self, market: str, days: int = 30) -> Dict[str, Any]:
        """마켓 데이터 일괄 조회 (캔들 + 현재가 + 호가)"""
        return await self.public.get_market_data_batch(market, days)

    # ===================
    # 프라이빗 API 메서드들
    # ===================

    async def get_accounts(self) -> List[Dict[str, Any]]:
        """계좌 정보 조회"""
        try:
            self.requires_private_access()
            result = await self.private.get_accounts()
            mark_api_success()  # API 성공 기록
            return result
        except Exception as e:
            mark_api_failure()  # API 실패 기록
            raise

    async def get_account_balance(self, currency: str) -> Optional[Dict[str, Any]]:
        """특정 화폐 잔고 조회"""
        self.requires_private_access()
        return await self.private.get_account_balance(currency)

    async def place_order(self, market: str, side: str, volume: Optional[str] = None,
                          price: Optional[str] = None, ord_type: str = 'limit',
                          identifier: Optional[str] = None) -> Dict[str, Any]:
        """주문 실행"""
        self.requires_private_access()
        return await self.private.place_order(market, side, volume, price, ord_type, identifier)

    async def cancel_order(self, uuid: Optional[str] = None,
                           identifier: Optional[str] = None) -> Dict[str, Any]:
        """주문 취소"""
        self.requires_private_access()
        return await self.private.cancel_order(uuid, identifier)

    async def get_order(self, uuid: Optional[str] = None,
                        identifier: Optional[str] = None) -> Dict[str, Any]:
        """개별 주문 조회"""
        self.requires_private_access()
        return await self.private.get_order(uuid, identifier)

    async def get_orders(self, market: Optional[str] = None, uuids: Optional[List[str]] = None,
                         identifiers: Optional[List[str]] = None, state: Optional[str] = None,
                         states: Optional[List[str]] = None, page: int = 1,
                         limit: int = 100, order_by: str = 'desc') -> List[Dict[str, Any]]:
        """주문 목록 조회"""
        self.requires_private_access()
        return await self.private.get_orders(market, uuids, identifiers, state, states, page, limit, order_by)

    async def get_order_chance(self, market: str) -> Dict[str, Any]:
        """주문 가능 정보 조회"""
        self.requires_private_access()
        return await self.private.get_order_chance(market)

    async def place_limit_buy_order(self, market: str, price: Union[str, float, Decimal],
                                    volume: Union[str, float, Decimal],
                                    identifier: Optional[str] = None) -> Dict[str, Any]:
        """지정가 매수 주문"""
        self.requires_private_access()
        return await self.private.place_limit_buy_order(market, price, volume, identifier)

    async def place_limit_sell_order(self, market: str, price: Union[str, float, Decimal],
                                     volume: Union[str, float, Decimal],
                                     identifier: Optional[str] = None) -> Dict[str, Any]:
        """지정가 매도 주문"""
        self.requires_private_access()
        return await self.private.place_limit_sell_order(market, price, volume, identifier)

    async def place_market_buy_order(self, market: str, price: Union[str, float, Decimal],
                                     identifier: Optional[str] = None) -> Dict[str, Any]:
        """시장가 매수 주문 (KRW 금액 지정)"""
        self.requires_private_access()
        return await self.private.place_market_buy_order(market, price, identifier)

    async def place_market_sell_order(self, market: str, volume: Union[str, float, Decimal],
                                      identifier: Optional[str] = None) -> Dict[str, Any]:
        """시장가 매도 주문 (코인 수량 지정)"""
        self.requires_private_access()
        return await self.private.place_market_sell_order(market, volume, identifier)

    async def get_deposits(self, currency: Optional[str] = None, state: Optional[str] = None,
                           uuids: Optional[List[str]] = None, txids: Optional[List[str]] = None,
                           limit: int = 100, page: int = 1, order_by: str = 'desc') -> List[Dict[str, Any]]:
        """입금 리스트 조회"""
        self.requires_private_access()
        return await self.private.get_deposits(currency, state, uuids, txids, limit, page, order_by)

    async def get_withdraws(self, currency: Optional[str] = None, state: Optional[str] = None,
                            uuids: Optional[List[str]] = None, txids: Optional[List[str]] = None,
                            limit: int = 100, page: int = 1, order_by: str = 'desc') -> List[Dict[str, Any]]:
        """출금 리스트 조회"""
        self.requires_private_access()
        return await self.private.get_withdraws(currency, state, uuids, txids, limit, page, order_by)

    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """포트폴리오 요약 정보 조회"""
        self.requires_private_access()
        return await self.private.get_portfolio_summary()

    # ===============================
    # 통합 기능 메서드들 (고급 기능)
    # ===============================

    # =================
    # 편의 메서드들
    # =================

    async def get_market_summary(self, market: str) -> Dict[str, Any]:
        """마켓 요약 정보 조회"""
        try:
            # 병렬로 현재가와 호가 정보 조회
            ticker_task = self.public.get_tickers([market])
            orderbook_task = self.public.get_orderbook([market])

            tickers, orderbooks = await asyncio.gather(ticker_task, orderbook_task)

            ticker = tickers[0] if tickers else {}
            orderbook = orderbooks[0] if orderbooks else {}

            orderbook_units = orderbook.get('orderbook_units', [{}])
            bid_price = orderbook_units[0].get('bid_price') if orderbook_units else None
            ask_price = orderbook_units[0].get('ask_price') if orderbook_units else None

            return {
                'market': market,
                'current_price': ticker.get('trade_price'),
                'change_rate': ticker.get('change_rate'),
                'volume': ticker.get('acc_trade_volume_24h'),
                'bid_price': bid_price,
                'ask_price': ask_price,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            raise ApiClientError(f"마켓 요약 정보 조회 실패 {market}: {str(e)}")

    async def get_portfolio_with_prices(self) -> Dict[str, Any]:
        """포트폴리오 정보와 현재가를 함께 조회"""
        self.requires_private_access()

        try:
            # 계좌 정보 조회
            accounts = await self.get_accounts()

            # KRW가 아닌 화폐들의 마켓 코드 생성
            markets_to_fetch = []
            for account in accounts:
                currency = account['currency']
                balance = float(account['balance']) + float(account['locked'])
                if currency != 'KRW' and balance > 0:
                    markets_to_fetch.append(f'KRW-{currency}')

            # 현재가 정보 조회 (필요한 경우에만)
            tickers_dict = {}
            if markets_to_fetch:
                tickers = await self.get_tickers(markets_to_fetch)
                tickers_dict = {ticker['market']: ticker for ticker in tickers}

            # 포트폴리오 계산
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
                        krw_value = total_balance
                        holding['current_price'] = 1.0
                    else:
                        market_code = f'KRW-{currency}'
                        ticker = tickers_dict.get(market_code)
                        if ticker:
                            current_price = float(ticker['trade_price'])
                            krw_value = total_balance * current_price
                            holding['current_price'] = current_price

                            # 수익률 계산
                            if holding['avg_buy_price'] > 0:
                                profit_rate = ((current_price - holding['avg_buy_price']) / holding['avg_buy_price']) * 100
                                holding['profit_rate'] = profit_rate
                                holding['profit_loss'] = krw_value - (total_balance * holding['avg_buy_price'])
                        else:
                            krw_value = 0.0
                            holding['current_price'] = 0.0

                    holding['krw_value'] = krw_value
                    total_krw += krw_value
                    holdings.append(holding)

            return {
                'total_krw': total_krw,
                'holdings': holdings,
                'currencies_count': len(holdings),
                'market_data': tickers_dict
            }

        except Exception as e:
            raise ApiClientError(f"포트폴리오 조회 실패: {str(e)}")

    async def get_trading_summary(self, market: str) -> Dict[str, Any]:
        """특정 마켓의 거래 요약 정보 조회 (계좌 + 마켓 데이터 + 주문 가능 정보)"""
        self.requires_private_access()

        try:
            # 병렬로 데이터 조회
            tasks = [
                self.get_market_data_batch(market),
                self.get_order_chance(market),
                self.get_orders(market=market, state='wait', limit=10)  # 대기 중인 주문
            ]

            market_data, order_chance, pending_orders = await asyncio.gather(*tasks)

            return {
                'market': market,
                'market_data': market_data,
                'order_chance': order_chance,
                'pending_orders': pending_orders,
                'summary': {
                    'current_price': market_data['ticker']['trade_price'] if market_data['ticker'] else 0,
                    'pending_orders_count': len(pending_orders),
                    'base_available': order_chance.get('market', {}).get('bid', {}).get('available_balance', 0),
                    'quote_available': order_chance.get('market', {}).get('ask', {}).get('available_balance', 0)
                }
            }

        except Exception as e:
            raise ApiClientError(f"거래 요약 조회 실패: {str(e)}")

    async def close(self):
        """리소스 정리"""
        await self.public.close()
        if self.private:
            await self.private.close()

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 엔트리"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.close()
