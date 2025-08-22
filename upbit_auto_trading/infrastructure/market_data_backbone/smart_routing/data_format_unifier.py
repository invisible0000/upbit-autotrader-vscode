"""
데이터 형식 통일기 (Data Format Unifier)

WebSocket과 REST API의 서로 다른 응답 형식을 REST API 기준으로 통일합니다.
이를 통해 사용자는 일관된 형식의 데이터를 받을 수 있습니다.
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from decimal import Decimal

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .models import DataType, ChannelType

logger = create_component_logger("DataFormatUnifier")


class DataFormatUnifier:
    """WebSocket과 REST API 응답을 통일된 형식으로 변환"""

    def __init__(self):
        """형식 통일기 초기화"""
        logger.info("DataFormatUnifier 초기화")

    def unify_ticker_data(self, data: Dict[str, Any], source: ChannelType) -> Dict[str, Any]:
        """티커 데이터를 REST API 형식으로 통일

        Args:
            data: 원본 데이터 (WebSocket 또는 REST 형식)
            source: 데이터 소스 (websocket 또는 rest_api)

        Returns:
            REST API 형식으로 통일된 데이터
        """
        try:
            if source == ChannelType.WEBSOCKET:
                return self._convert_websocket_ticker_to_rest(data)
            else:
                return self._add_source_metadata(data, source)

        except Exception as e:
            logger.error(f"티커 데이터 형식 통일 실패: {e}")
            return self._create_error_response(data, source, str(e))

    def unify_orderbook_data(self, data: Dict[str, Any], source: ChannelType) -> Dict[str, Any]:
        """호가 데이터를 REST API 형식으로 통일"""
        try:
            if source == ChannelType.WEBSOCKET:
                return self._convert_websocket_orderbook_to_rest(data)
            else:
                return self._add_source_metadata(data, source)

        except Exception as e:
            logger.error(f"호가 데이터 형식 통일 실패: {e}")
            return self._create_error_response(data, source, str(e))

    def unify_trades_data(self, data: Any, source: ChannelType) -> Dict[str, Any]:
        """체결 데이터를 REST API 형식으로 통일"""
        try:
            if source == ChannelType.WEBSOCKET:
                if isinstance(data, dict):
                    return self._convert_websocket_trades_to_rest(data)
                else:
                    logger.warning(f"WebSocket 체결 데이터가 예상 형식이 아님: {type(data)}")
                    return self._create_error_response({"error": "invalid_websocket_data"}, source, "Invalid WebSocket data format")
            else:
                # REST API 체결 데이터 처리
                if isinstance(data, list):
                    # 첫 번째 체결 데이터로 통일된 응답 생성 (리스트 형태는 metadata에 보관)
                    if len(data) > 0 and isinstance(data[0], dict):
                        unified_data = self._add_source_metadata(data[0], source)
                        unified_data["_trades_list"] = data  # 전체 리스트 보관
                        return unified_data
                    else:
                        return self._create_error_response({"error": "empty_trades_list"}, source, "Empty trades list")
                elif isinstance(data, dict):
                    return self._add_source_metadata(data, source)
                else:
                    logger.warning(f"예상치 못한 체결 데이터 형태: {type(data)}")
                    return self._create_error_response({"error": "invalid_data_format"}, source, "Invalid data format")

        except Exception as e:
            logger.error(f"체결 데이터 형식 통일 실패: {e}")
            return self._create_error_response(data if isinstance(data, dict) else {"error": "conversion_failed"}, source, str(e))

    def unify_candles_data(self, data: Any, source: ChannelType) -> Dict[str, Any]:
        """캔들 데이터 형식 통일 (주로 REST API 사용)"""
        try:
            if source == ChannelType.WEBSOCKET:
                if isinstance(data, dict):
                    return self._convert_websocket_candles_to_rest(data)
                else:
                    logger.warning(f"WebSocket 캔들 데이터가 예상 형식이 아님: {type(data)}")
                    error_data = {"error": "invalid_websocket_data"}
                    return self._create_error_response(error_data, source, "Invalid WebSocket data format")
            else:
                # REST API 캔들 데이터가 리스트인 경우 처리
                if isinstance(data, list):
                    if len(data) > 0 and isinstance(data[0], dict):
                        # 첫 번째 캔들 데이터로 통일된 응답 생성 (리스트는 metadata에 보관)
                        unified_data = self._add_source_metadata(data[0], source)
                        unified_data["_candles_list"] = data  # 전체 리스트 보관
                        return unified_data
                    else:
                        error_data = {"error": "empty_candles_list"}
                        return self._create_error_response(error_data, source, "Empty candles list")
                elif isinstance(data, dict):
                    return self._add_source_metadata(data, source)
                else:
                    # 예상치 못한 형태의 데이터
                    logger.warning(f"예상치 못한 캔들 데이터 형태: {type(data)}")
                    error_data = {"error": "invalid_data_format"}
                    return self._create_error_response(error_data, source, "Invalid data format")

        except Exception as e:
            logger.error(f"캔들 데이터 형식 통일 실패: {e}")
            error_data = data if isinstance(data, dict) else {"error": "conversion_failed"}
            return self._create_error_response(error_data, source, str(e))

    def _convert_websocket_ticker_to_rest(self, ws_data: Dict[str, Any]) -> Dict[str, Any]:
        """WebSocket 티커를 REST API 형식으로 변환"""
        timestamp = ws_data.get("timestamp", int(time.time() * 1000))
        dt = datetime.fromtimestamp(timestamp / 1000)

        # WebSocket 형식: {"type": "ticker", "code": "KRW-BTC", ...}
        # REST 형식: {"market": "KRW-BTC", "trade_date": "20241031", ...}

        rest_format = {
            # 기본 필드 매핑
            "market": ws_data.get("code", ""),
            "trade_date": dt.strftime("%Y%m%d"),
            "trade_time": dt.strftime("%H%M%S"),
            "trade_date_kst": dt.strftime("%Y%m%d"),
            "trade_time_kst": dt.strftime("%H%M%S"),
            "trade_timestamp": timestamp,

            # 가격 정보
            "opening_price": float(ws_data.get("opening_price", 0)),
            "high_price": float(ws_data.get("high_price", 0)),
            "low_price": float(ws_data.get("low_price", 0)),
            "trade_price": float(ws_data.get("trade_price", 0)),
            "prev_closing_price": float(ws_data.get("prev_closing_price", 0)),

            # 변화 정보
            "change": ws_data.get("change", "EVEN"),
            "change_price": float(ws_data.get("change_price", 0)),
            "change_rate": float(ws_data.get("change_rate", 0)),
            "signed_change_price": float(ws_data.get("signed_change_price", 0)),
            "signed_change_rate": float(ws_data.get("signed_change_rate", 0)),

            # 거래량 정보
            "trade_volume": float(ws_data.get("trade_volume", 0)),
            "acc_trade_price": float(ws_data.get("acc_trade_price", 0)),
            "acc_trade_price_24h": float(ws_data.get("acc_trade_price_24h", 0)),
            "acc_trade_volume": float(ws_data.get("acc_trade_volume", 0)),
            "acc_trade_volume_24h": float(ws_data.get("acc_trade_volume_24h", 0)),

            # 52주 고저가
            "highest_52_week_price": float(ws_data.get("highest_52_week_price", 0)),
            "highest_52_week_date": ws_data.get("highest_52_week_date", ""),
            "lowest_52_week_price": float(ws_data.get("lowest_52_week_price", 0)),
            "lowest_52_week_date": ws_data.get("lowest_52_week_date", ""),

            # 타임스탬프
            "timestamp": timestamp
        }

        return self._add_source_metadata(rest_format, ChannelType.WEBSOCKET)

    def _convert_websocket_orderbook_to_rest(self, ws_data: Dict[str, Any]) -> Dict[str, Any]:
        """WebSocket 호가를 REST API 형식으로 변환"""
        rest_format = {
            "market": ws_data.get("code", ""),
            "timestamp": ws_data.get("timestamp", int(time.time() * 1000)),
            "total_ask_size": float(ws_data.get("total_ask_size", 0)),
            "total_bid_size": float(ws_data.get("total_bid_size", 0)),
            "orderbook_units": []
        }

        # orderbook_units 변환
        units = ws_data.get("orderbook_units", [])
        for unit in units:
            rest_unit = {
                "ask_price": float(unit.get("ask_price", 0)),
                "bid_price": float(unit.get("bid_price", 0)),
                "ask_size": float(unit.get("ask_size", 0)),
                "bid_size": float(unit.get("bid_size", 0))
            }
            rest_format["orderbook_units"].append(rest_unit)

        return self._add_source_metadata(rest_format, ChannelType.WEBSOCKET)

    def _convert_websocket_trades_to_rest(self, ws_data: Dict[str, Any]) -> Dict[str, Any]:
        """WebSocket 체결을 REST API 형식으로 변환"""
        timestamp = ws_data.get("trade_timestamp", int(time.time() * 1000))
        dt = datetime.fromtimestamp(timestamp / 1000)

        rest_format = {
            "market": ws_data.get("code", ""),
            "trade_date_utc": dt.strftime("%Y-%m-%d"),
            "trade_time_utc": dt.strftime("%H:%M:%S"),
            "timestamp": timestamp,
            "trade_price": float(ws_data.get("trade_price", 0)),
            "trade_volume": float(ws_data.get("trade_volume", 0)),
            "prev_closing_price": float(ws_data.get("prev_closing_price", 0)),
            "change_price": float(ws_data.get("change_price", 0)),
            "ask_bid": ws_data.get("ask_bid", ""),
            "sequential_id": ws_data.get("sequential_id", 0)
        }

        return self._add_source_metadata(rest_format, ChannelType.WEBSOCKET)

    def _convert_websocket_candles_to_rest(self, ws_data: Dict[str, Any]) -> Dict[str, Any]:
        """WebSocket 캔들을 REST API 형식으로 변환 (1초 캔들 전용)"""
        timestamp = ws_data.get("timestamp", int(time.time() * 1000))
        dt = datetime.fromtimestamp(timestamp / 1000)

        rest_format = {
            "market": ws_data.get("code", ""),
            "candle_date_time_utc": dt.isoformat() + "Z",
            "candle_date_time_kst": dt.isoformat(),
            "opening_price": float(ws_data.get("opening_price", 0)),
            "high_price": float(ws_data.get("high_price", 0)),
            "low_price": float(ws_data.get("low_price", 0)),
            "trade_price": float(ws_data.get("trade_price", 0)),
            "timestamp": timestamp,
            "candle_acc_trade_price": float(ws_data.get("candle_acc_trade_price", 0)),
            "candle_acc_trade_volume": float(ws_data.get("candle_acc_trade_volume", 0)),
            "unit": 1  # 1초 단위
        }

        return self._add_source_metadata(rest_format, ChannelType.WEBSOCKET)

    def _add_source_metadata(self, data: Dict[str, Any], source: ChannelType) -> Dict[str, Any]:
        """소스 메타데이터 추가"""
        data["_unified"] = {
            "source": source.value,
            "unified_at": time.time(),
            "format_version": "2.0"
        }
        return data

    def _create_error_response(self, original_data: Dict[str, Any],
                               source: ChannelType, error_msg: str) -> Dict[str, Any]:
        """오류 응답 생성"""
        return {
            "_unified": {
                "source": source.value,
                "unified_at": time.time(),
                "format_version": "2.0",
                "error": error_msg
            },
            "_original_data": original_data,
            "success": False
        }

    def unify_data(self, data: Dict[str, Any], data_type: DataType,
                   source: ChannelType) -> Dict[str, Any]:
        """데이터 타입에 따른 자동 형식 통일"""
        try:
            if data_type == DataType.TICKER:
                return self.unify_ticker_data(data, source)
            elif data_type == DataType.ORDERBOOK:
                return self.unify_orderbook_data(data, source)
            elif data_type == DataType.TRADES:
                return self.unify_trades_data(data, source)
            elif data_type in [DataType.CANDLES, DataType.CANDLES_1S]:
                return self.unify_candles_data(data, source)
            else:
                # 기타 데이터 타입은 메타데이터만 추가
                return self._add_source_metadata(data, source)

        except Exception as e:
            logger.error(f"데이터 형식 통일 실패 - type: {data_type}, source: {source}, error: {e}")
            return self._create_error_response(data, source, str(e))
