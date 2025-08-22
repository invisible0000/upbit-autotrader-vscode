# d:\projects\upbit-autotrader-vscode\upbit_auto_trading\infrastructure\market_data_backbone\smart_router\transformers\data_converter.py

from typing import Dict, Any, List, Union
from smart_router.models.canonical_ticker import CanonicalTicker
from smart_router.models.canonical_candle import CanonicalCandle
# 다른 표준 모델이 정의되면 임포트합니다.

class DataConverter:
    """
    업비트 REST 및 WebSocket API의 원시 데이터를 표준화된
    표준 데이터 모델로 변환합니다.
    """

    def convert_rest_ticker_to_canonical(self, raw_data: Dict[str, Any]) -> CanonicalTicker:
        """
        원시 REST API 티커 데이터를 CanonicalTicker로 변환합니다.
        raw_data는 단일 티커를 나타내는 딕셔너리라고 가정합니다.
        """
        # 예시 매핑 (실제 업비트 REST 티커 응답 구조에 따라 조정)
        return CanonicalTicker(
            symbol=raw_data.get('market', ''),
            trade_price=raw_data.get('trade_price', 0.0),
            trade_volume=raw_data.get('trade_volume', 0.0),
            change=raw_data.get('change', 'EVEN'), # 'RISE', 'FALL', 'EVEN'
            change_price=raw_data.get('change_price', 0.0),
            signed_change_price=raw_data.get('signed_change_price', 0.0),
            change_rate=raw_data.get('change_rate', 0.0),
            signed_change_rate=raw_data.get('signed_change_rate', 0.0),
            ask_bid=raw_data.get('ask_bid', ''), # 'ASK', 'BID'
            high_price=raw_data.get('high_price', 0.0),
            low_price=raw_data.get('low_price', 0.0),
            trade_timestamp=raw_data.get('trade_timestamp', 0),
            acc_trade_price_24h=raw_data.get('acc_trade_price_24h', 0.0),
            acc_trade_volume_24h=raw_data.get('acc_trade_volume_24h', 0.0)
        )

    def convert_websocket_ticker_to_canonical(self, raw_data: Dict[str, Any]) -> CanonicalTicker:
        """
        원시 WebSocket API 티커 데이터를 CanonicalTicker로 변환합니다.
        raw_data는 단일 티커를 나타내는 딕셔너리라고 가정합니다.
        """
        # 예시 매핑 (실제 업비트 WebSocket 티커 응답 구조에 따라 조정)
        return CanonicalTicker(
            symbol=raw_data.get('code', ''),
            trade_price=raw_data.get('trade_price', 0.0),
            trade_volume=raw_data.get('trade_volume', 0.0),
            change=raw_data.get('change', 'EVEN'),
            change_price=raw_data.get('change_price', 0.0),
            signed_change_price=raw_data.get('signed_change_price', 0.0),
            change_rate=raw_data.get('change_rate', 0.0),
            signed_change_rate=raw_data.get('signed_change_rate', 0.0),
            ask_bid=raw_data.get('ask_bid', ''),
            high_price=raw_data.get('high_price', 0.0),
            low_price=raw_data.get('low_price', 0.0),
            trade_timestamp=raw_data.get('trade_timestamp', 0),
            acc_trade_price_24h=raw_data.get('acc_trade_price_24h', 0.0),
            acc_trade_volume_24h=raw_data.get('acc_trade_volume_24h', 0.0)
        )

    def convert_rest_candle_to_canonical(self, raw_data: Dict[str, Any]) -> CanonicalCandle:
        """
        원시 REST API 캔들 데이터를 CanonicalCandle로 변환합니다.
        raw_data는 단일 캔들을 나타내는 딕셔너리라고 가정합니다.
        """
        # 예시 매핑 (실제 업비트 REST 캔들 응답 구조에 따라 조정)
        return CanonicalCandle(
            symbol=raw_data.get('market', ''),
            candle_date_time_utc=raw_data.get('candle_date_time_utc', ''),
            candle_date_time_kst=raw_data.get('candle_date_time_kst', ''),
            opening_price=raw_data.get('opening_price', 0.0),
            high_price=raw_data.get('high_price', 0.0),
            low_price=raw_data.get('low_price', 0.0),
            closing_price=raw_data.get('trade_price', 0.0), # 업비트 캔들에서 종가는 trade_price입니다.
            trade_price=raw_data.get('trade_price', 0.0),
            trade_volume=raw_data.get('candle_acc_trade_volume', 0.0),
            timestamp=raw_data.get('timestamp', 0),
            unit=raw_data.get('unit', None)
        )

    def convert_rest_account_info_to_canonical(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        원시 REST API 계정 정보 데이터를 표준 형식으로 변환합니다.
        현재는 CanonicalAccountInfo 모델이 없으므로 원시 데이터를 직접 반환합니다.
        """
        return raw_data # TODO: CanonicalAccountInfo 모델이 정의되면 변환 로직 추가

    # Add methods for other data types (e.g., orderbook, trade) and their REST/WebSocket variants
    # def convert_rest_orderbook_to_canonical(...)
    # def convert_websocket_orderbook_to_canonical(...)
    # def convert_rest_trade_to_canonical(...)
    # def convert_websocket_trade_to_canonical(...)

    def convert_to_canonical(self, data_type: str, source: str, raw_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[Any, List[Any]]:
        """
        데이터 유형 및 소스에 기반한 일반 변환 메서드입니다。
        :param data_type: 데이터 유형 (예: 'ticker', 'candle').
        :param source: 데이터 소스 ('REST', 'WEBSOCKET').
        :param raw_data: API의 원시 데이터.
        :return: 표준 데이터 모델 인스턴스.
        """
        if isinstance(raw_data, list):
            return [self.convert_to_canonical(data_type, source, item) for item in raw_data]

        if data_type == 'ticker':
            if source == 'REST':
                return self.convert_rest_ticker_to_canonical(raw_data)
            elif source == 'WEBSOCKET':
                return self.convert_websocket_ticker_to_canonical(raw_data)
        elif data_type == 'candle':
            if source == 'REST':
                return self.convert_rest_candle_to_canonical(raw_data)
            # WebSocket 캔들은 일반적으로 직접 스트리밍되지 않고, 체결로부터 파생됩니다.
            # 업비트 WS가 캔들 데이터를 제공한다면 여기에 변환기를 추가합니다.
        elif data_type == 'account_info':
            if source == 'REST':
                return self.convert_rest_account_info_to_canonical(raw_data)
        # Add more data type and source mappings
        raise ValueError(f"지원되지 않는 변환: data_type={data_type}, source={source}")
