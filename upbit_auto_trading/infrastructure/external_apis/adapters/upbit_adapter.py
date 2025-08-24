"""
업비트 전용 어댑터

업비트 특화 로직을 격리하여 표준화된 인터페이스 제공
"""
from typing import Dict, Any, List

from .base_adapter import ExchangeAdapter
from ..core.data_models import (
    StandardTicker, StandardOrderbook, StandardCandle, StandardTrade
)


class UpbitAdapter(ExchangeAdapter):
    """업비트 특화 어댑터"""

    def __init__(self):
        super().__init__('upbit')

    # ================================================================
    # 심볼 및 파라미터 변환
    # ================================================================

    def normalize_symbol_format(self, symbol: str) -> str:
        """업비트는 KRW-BTC 형식 그대로 사용"""
        return symbol

    def build_batch_params(self, symbols: List[str], endpoint: str) -> Dict[str, Any]:
        """업비트 배치 요청용 파라미터"""
        return {'markets': ','.join(symbols)}

    def build_single_params(self, symbol: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """업비트 단일 요청용 파라미터"""
        params = {'market': symbol}

        # 캔들 관련 추가 파라미터
        if 'candle' in endpoint:
            if 'count' in kwargs and kwargs['count'] is not None:
                params['count'] = str(min(kwargs['count'], 200))
            if 'to' in kwargs and kwargs['to'] is not None:
                params['to'] = kwargs['to']

        # 체결 관련 추가 파라미터
        elif 'trade' in endpoint:
            if 'count' in kwargs and kwargs['count'] is not None:
                params['count'] = str(min(kwargs['count'], 500))

        return params

    # ================================================================
    # 응답 데이터 파싱
    # ================================================================

    def parse_ticker_response(self, raw_data: List[Dict[str, Any]]) -> List[StandardTicker]:
        """업비트 티커 응답 파싱"""
        tickers = []
        for item in raw_data:
            try:
                ticker = StandardTicker(
                    symbol=item.get('market', ''),
                    price=self._safe_decimal(item.get('trade_price')),
                    price_change=self._safe_decimal(item.get('change_price')),
                    price_change_percent=self._safe_decimal(item.get('change_rate', 0)) * 100,
                    volume_24h=self._safe_decimal(item.get('acc_trade_volume_24h')),
                    volume_value_24h=self._safe_decimal(item.get('acc_trade_price_24h')),
                    high_24h=self._safe_decimal(item.get('high_price')),
                    low_24h=self._safe_decimal(item.get('low_price')),
                    timestamp=self._safe_datetime(item.get('timestamp')),
                    exchange='upbit',
                    raw_data=item
                )
                tickers.append(ticker)
            except Exception:
                # 로깅은 Infrastructure 계층에서 처리
                continue

        return tickers

    def parse_orderbook_response(self, raw_data: List[Dict[str, Any]]) -> List[StandardOrderbook]:
        """업비트 호가 응답 파싱"""
        orderbooks = []
        for item in raw_data:
            try:
                # 업비트 호가 데이터 구조
                orderbook_units = item.get('orderbook_units', [])

                bids = []
                asks = []

                for unit in orderbook_units:
                    # 매수 호가
                    if unit.get('bid_price') and unit.get('bid_size'):
                        bids.append({
                            'price': self._safe_decimal(unit['bid_price']),
                            'size': self._safe_decimal(unit['bid_size'])
                        })

                    # 매도 호가
                    if unit.get('ask_price') and unit.get('ask_size'):
                        asks.append({
                            'price': self._safe_decimal(unit['ask_price']),
                            'size': self._safe_decimal(unit['ask_size'])
                        })

                orderbook = StandardOrderbook(
                    symbol=item.get('market', ''),
                    bids=bids,
                    asks=asks,
                    timestamp=self._safe_datetime(item.get('timestamp')),
                    exchange='upbit',
                    raw_data=item
                )
                orderbooks.append(orderbook)
            except Exception:
                continue

        return orderbooks

    def parse_candle_response(self, raw_data: List[Dict[str, Any]],
                              symbol: str, timeframe: str) -> List[StandardCandle]:
        """업비트 캔들 응답 파싱"""
        candles = []
        for item in raw_data:
            try:
                candle = StandardCandle(
                    symbol=symbol,
                    timeframe=timeframe,
                    open_price=self._safe_decimal(item.get('opening_price')),
                    high_price=self._safe_decimal(item.get('high_price')),
                    low_price=self._safe_decimal(item.get('low_price')),
                    close_price=self._safe_decimal(item.get('trade_price')),
                    volume=self._safe_decimal(item.get('candle_acc_trade_volume')),
                    timestamp=self._safe_datetime(item.get('candle_date_time_kst')),
                    exchange='upbit',
                    raw_data=item
                )
                candles.append(candle)
            except Exception:
                continue

        return candles

    def parse_trade_response(self, raw_data: List[Dict[str, Any]],
                             symbol: str) -> List[StandardTrade]:
        """업비트 체결 응답 파싱"""
        trades = []
        for item in raw_data:
            try:
                # 업비트 ask_bid 필드: ASK(매도), BID(매수)
                side = 'sell' if item.get('ask_bid') == 'ASK' else 'buy'

                # 안전한 날짜 문자열 생성
                trade_date = item.get('trade_date_utc') or ''
                trade_time = item.get('trade_time_utc') or ''
                datetime_str = f"{trade_date}T{trade_time}" if trade_date and trade_time else None

                trade = StandardTrade(
                    symbol=symbol,
                    price=self._safe_decimal(item.get('trade_price')),
                    size=self._safe_decimal(item.get('trade_volume')),
                    side=side,
                    timestamp=self._safe_datetime(datetime_str),
                    trade_id=str(item.get('sequential_id', '')),
                    exchange='upbit',
                    raw_data=item
                )
                trades.append(trade)
            except Exception:
                continue

        return trades

    # ================================================================
    # 에러 처리
    # ================================================================

    def parse_error_response(self, response_data: Any, status_code: int) -> str:
        """업비트 에러 응답 파싱"""
        if isinstance(response_data, dict):
            error_info = response_data.get('error', {})
            if isinstance(error_info, dict):
                message = error_info.get('message', 'Unknown error')
                name = error_info.get('name', '')
                if name:
                    return f"[{name}] {message}"
                return message
            else:
                return str(error_info)

        return f"HTTP {status_code}: {str(response_data)}"

    # ================================================================
    # 업비트 특화 유틸리티 메서드
    # ================================================================

    def get_candle_endpoint(self, timeframe: str) -> str:
        """시간프레임에 맞는 캔들 엔드포인트 반환 (업비트 API 문서 기반)"""
        # 업비트 API 문서 기반 완전한 시간프레임 지원
        endpoint_map = {
            # 초 캔들 (1초 고정, 최대 3개월 데이터)
            '1s': '/candles/seconds',
            # 분 캔들 (공식 지원: 1, 3, 5, 10, 15, 30, 60, 240)
            '1m': '/candles/minutes/1',
            '3m': '/candles/minutes/3',
            '5m': '/candles/minutes/5',
            '10m': '/candles/minutes/10',
            '15m': '/candles/minutes/15',
            '30m': '/candles/minutes/30',
            '1h': '/candles/minutes/60',
            '4h': '/candles/minutes/240',
            # 일/주/월/년 캔들 (표준 표기법)
            '1d': '/candles/days',
            '1w': '/candles/weeks',
            '1M': '/candles/months',  # 월은 대문자 (분과 구분)
            '1y': '/candles/years'    # 년은 소문자 (표준)
        }

        endpoint = endpoint_map.get(timeframe)
        if not endpoint:
            raise ValueError(f"지원하지 않는 시간프레임: {timeframe}")

        return endpoint

    def categorize_markets(self, markets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """업비트 마켓을 카테고리별로 분류"""
        krw_markets = []
        btc_markets = []
        usdt_markets = []

        for market in markets:
            market_code = market.get('market', '')
            if market_code.startswith('KRW-'):
                krw_markets.append(market)
            elif market_code.startswith('BTC-'):
                btc_markets.append(market)
            elif market_code.startswith('USDT-'):
                usdt_markets.append(market)

        return {
            'krw_markets': krw_markets,
            'btc_markets': btc_markets,
            'usdt_markets': usdt_markets,
            'total_count': len(markets)
        }

    def is_krw_market(self, symbol: str) -> bool:
        """KRW 마켓 여부 확인"""
        return symbol.startswith('KRW-')

    def extract_base_currency(self, symbol: str) -> str:
        """심볼에서 기준 통화 추출 (예: KRW-BTC → BTC)"""
        parts = symbol.split('-')
        return parts[1] if len(parts) >= 2 else symbol
