"""
데이터 변환 서비스

업비트 API 응답을 스마트 라우팅 시스템의 표준 형식으로 변환하는 서비스입니다.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from ..models import TimeFrame

logger = create_component_logger("DataConverter")


class DataConverter:
    """데이터 변환 서비스

    업비트 API의 다양한 응답 형식을 표준화된 도메인 모델로 변환합니다.
    """

    def __init__(self):
        """데이터 변환기 초기화"""
        logger.debug("DataConverter 초기화")

        # 시간 프레임 매핑
        self.timeframe_mapping = {
            TimeFrame.MINUTES_1: 1,
            TimeFrame.MINUTES_3: 3,
            TimeFrame.MINUTES_5: 5,
            TimeFrame.MINUTES_15: 15,
            TimeFrame.MINUTES_30: 30,
            TimeFrame.HOURS_1: 60,
            TimeFrame.HOURS_4: 240,
        }

    def convert_ticker_response(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """업비트 REST API 티커 응답을 표준 형식으로 변환

        Args:
            raw_data: 업비트 REST API 티커 응답 데이터

        Returns:
            표준화된 티커 데이터 딕셔너리
        """
        ticker_data = {}

        for item in raw_data:
            symbol = item.get('market', '')
            ticker_data[symbol] = {
                'symbol': symbol,
                'price': float(item.get('trade_price', 0)),
                'change': float(item.get('change_price', 0)),
                'change_rate': float(item.get('change_rate', 0)),
                'volume': float(item.get('acc_trade_volume_24h', 0)),
                'value': float(item.get('acc_trade_price_24h', 0)),
                'high': float(item.get('high_price', 0)),
                'low': float(item.get('low_price', 0)),
                'opening': float(item.get('opening_price', 0)),
                'timestamp': datetime.now().isoformat(),
                'source': 'rest_api',
                'raw_data': item
            }

        logger.debug(f"REST 티커 응답 변환 완료: {len(ticker_data)}개 심볼")
        return ticker_data

    def convert_websocket_ticker_data(self, ws_data: Dict[str, Any], source: str = 'websocket') -> Dict[str, Any]:
        """WebSocket 티커 데이터를 표준 형식으로 변환

        Args:
            ws_data: WebSocket에서 수신한 티커 데이터
            source: 데이터 소스 ('websocket_live' 또는 'websocket_batch')

        Returns:
            표준화된 티커 데이터
        """
        try:
            # 필수 필드 검증
            if not ws_data:
                raise ValueError("WebSocket 데이터가 비어있습니다")

            # 심볼 추출 및 검증
            symbol = ws_data.get('code', ws_data.get('market', ''))
            if not symbol or not self.validate_symbol_format(symbol):
                raise ValueError(f"유효하지 않은 심볼: {symbol}")

            # 가격 데이터 안전한 변환
            def safe_float(value, default=0.0):
                try:
                    return float(value) if value is not None else default
                except (ValueError, TypeError):
                    return default

            converted_data = {
                'symbol': self.normalize_symbol(symbol),
                'price': safe_float(ws_data.get('trade_price', ws_data.get('tp', 0))),
                'change': safe_float(ws_data.get('change_price', ws_data.get('cp', 0))),
                'change_rate': safe_float(ws_data.get('change_rate', ws_data.get('cr', 0))),
                'volume': safe_float(ws_data.get('acc_trade_volume_24h', ws_data.get('atv24h', 0))),
                'value': safe_float(ws_data.get('acc_trade_price_24h', ws_data.get('atp24h', 0))),
                'high': safe_float(ws_data.get('high_price', ws_data.get('hp', 0))),
                'low': safe_float(ws_data.get('low_price', ws_data.get('lp', 0))),
                'opening': safe_float(ws_data.get('opening_price', ws_data.get('op', 0))),
                'timestamp': datetime.now().isoformat(),
                'source': source,
                'raw_data': ws_data
            }

            # 데이터 무결성 검증
            if converted_data['price'] <= 0:
                logger.warning(f"비정상적인 가격 데이터: {symbol}, price: {converted_data['price']}")

            logger.debug(f"WebSocket 티커 변환 완료: {symbol}")
            return converted_data

        except Exception as e:
            logger.error(f"WebSocket 티커 데이터 변환 실패: {str(e)}")
            # 기본값으로 빈 데이터 반환
            return {
                'symbol': ws_data.get('code', ws_data.get('market', 'UNKNOWN')),
                'price': 0.0,
                'change': 0.0,
                'change_rate': 0.0,
                'volume': 0.0,
                'value': 0.0,
                'high': 0.0,
                'low': 0.0,
                'opening': 0.0,
                'timestamp': datetime.now().isoformat(),
                'source': source,
                'error': str(e),
                'raw_data': ws_data
            }

        logger.debug(f"WebSocket 티커 데이터 변환: {converted_data['symbol']}")
        return converted_data

    def convert_candle_response(
        self,
        raw_data: List[Dict[str, Any]],
        timeframe: Optional[TimeFrame] = None
    ) -> List[Dict[str, Any]]:
        """업비트 캔들 응답을 표준 형식으로 변환

        Args:
            raw_data: 업비트 REST API 캔들 응답 데이터
            timeframe: 시간 프레임

        Returns:
            표준화된 캔들 데이터 리스트
        """
        candles = []

        for item in raw_data:
            candle = {
                'timeframe': timeframe.value if timeframe else 'unknown',
                'timestamp': item.get('candle_date_time_kst', ''),
                'open': float(item.get('opening_price', 0)),
                'high': float(item.get('high_price', 0)),
                'low': float(item.get('low_price', 0)),
                'close': float(item.get('trade_price', 0)),
                'volume': float(item.get('candle_acc_trade_volume', 0)),
                'value': float(item.get('candle_acc_trade_price', 0)),
                'source': 'rest_api',
                'raw_data': item
            }
            candles.append(candle)

        timeframe_str = timeframe.value if timeframe else 'unknown'
        logger.debug(f"캔들 응답 변환 완료: {len(candles)}개 캔들, TF: {timeframe_str}")
        return candles

    def convert_orderbook_response(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """업비트 호가창 응답을 표준 형식으로 변환

        Args:
            raw_data: 업비트 REST API 호가창 응답 데이터

        Returns:
            표준화된 호가창 데이터 딕셔너리
        """
        orderbook_data = {}

        for item in raw_data:
            symbol = item.get('market', '')

            # 매수/매도 호가 변환
            orderbook_units = item.get('orderbook_units', [])
            bids = []
            asks = []

            for unit in orderbook_units:
                bids.append({
                    'price': float(unit.get('bid_price', 0)),
                    'size': float(unit.get('bid_size', 0))
                })
                asks.append({
                    'price': float(unit.get('ask_price', 0)),
                    'size': float(unit.get('ask_size', 0))
                })

            orderbook_data[symbol] = {
                'symbol': symbol,
                'bids': bids,
                'asks': asks,
                'timestamp': datetime.now().isoformat(),
                'source': 'rest_api',
                'raw_data': item
            }

        logger.debug(f"호가창 응답 변환 완료: {len(orderbook_data)}개 심볼")
        return orderbook_data

    def convert_trade_response(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """업비트 체결 응답을 표준 형식으로 변환

        Args:
            raw_data: 업비트 REST API 체결 응답 데이터

        Returns:
            표준화된 체결 데이터 리스트
        """
        trades = []

        for item in raw_data:
            trade = {
                'timestamp': item.get('trade_date_utc', '') + 'T' + item.get('trade_time_utc', ''),
                'price': float(item.get('trade_price', 0)),
                'volume': float(item.get('trade_volume', 0)),
                'side': 'buy' if item.get('ask_bid') == 'BID' else 'sell',
                'sequential_id': item.get('sequential_id', 0),
                'source': 'rest_api',
                'raw_data': item
            }
            trades.append(trade)

        logger.debug(f"체결 응답 변환 완료: {len(trades)}개 체결")
        return trades

    def timeframe_to_upbit_unit(self, timeframe: TimeFrame) -> int:
        """시간 프레임을 업비트 API 단위로 변환

        Args:
            timeframe: 변환할 시간 프레임

        Returns:
            업비트 API 단위 (분 단위)

        Raises:
            ValueError: 지원하지 않는 시간 프레임인 경우
        """
        unit = self.timeframe_mapping.get(timeframe)
        if unit is None:
            raise ValueError(f"지원하지 않는 시간 프레임: {timeframe}")

        return unit

    def validate_symbol_format(self, symbol: str) -> bool:
        """심볼 형식 검증

        Args:
            symbol: 검증할 심볼 (예: KRW-BTC)

        Returns:
            유효한 형식 여부
        """
        if not symbol or '-' not in symbol:
            return False

        parts = symbol.split('-')
        if len(parts) != 2:
            return False

        quote, base = parts
        return len(quote) >= 3 and len(base) >= 2

    def normalize_symbol(self, symbol: str) -> str:
        """심볼을 정규화된 형식으로 변환

        Args:
            symbol: 정규화할 심볼

        Returns:
            정규화된 심볼 (대문자, 하이픈 포함)
        """
        return symbol.upper().strip()
