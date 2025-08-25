"""
데이터 형식 통일기 (Data Format Unifier)

WebSocket과 REST API의 서로 다른 응답 형식을 REST API 기준으로 통일합니다.
이를 통해 사용자는 일관된 형식의 데이터를 받을 수 있습니다.
"""

import time
from datetime import datetime
from typing import Dict, Any, List, Union

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .models import DataType, ChannelType

logger = create_component_logger("DataFormatUnifier")


class DataFormatUnifier:
    """WebSocket과 REST API 응답을 통일된 형식으로 변환 - Dict 통일 정책 준수"""

    def __init__(self):
        """형식 통일기 초기화"""
        # 성능 최적화: 자주 사용되는 템플릿 캐싱
        self._metadata_template = {
            "_unified": True,
            "_source": "",
            "_timestamp": 0,
            "_format_version": "3.0",
            "_processing_time_ms": 0.0
        }
        logger.info("DataFormatUnifier 초기화 완료 (Dict 통일 정책 적용)")

    def unify_ticker_data(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], source: ChannelType) -> Dict[str, Any]:
        """티커 데이터를 REST API 형식으로 통일 - Dict 통일 정책 준수

        Args:
            data: 원본 데이터 (Dict 또는 List[Dict])
            source: 데이터 소스 (websocket 또는 rest_api)

        Returns:
            Dict: 통일된 형식의 티커 데이터
        """
        start_time = time.time()

        try:
            # Dict 통일 정책: 모든 반환값은 Dict
            if isinstance(data, list):
                if not data:  # 빈 리스트 처리
                    return self._create_fast_empty_response(source, start_time)

                # 다중 데이터 처리 - 성능 최적화
                if len(data) > 1:
                    unified_data = self._process_ticker_list(data, source, start_time)
                    return unified_data
                else:
                    # 단일 아이템 처리
                    data = data[0]

            # Dict 형태 데이터 처리
            if not isinstance(data, dict):
                return self._create_fast_error_response(data, source, "Invalid data type", start_time)

            # 소스별 변환 처리
            if source == ChannelType.WEBSOCKET:
                result = self._fast_convert_websocket_ticker_to_rest(data)
            else:
                result = self._fast_add_source_metadata(data, source)

            # 성능 메트릭 추가
            result["_processing_time_ms"] = (time.time() - start_time) * 1000
            return result

        except Exception as e:
            logger.error(f"티커 데이터 형식 통일 실패: {e}")
            return self._create_fast_error_response(data, source, str(e), start_time)

    def unify_orderbook_data(self, data: Union[Dict[str, Any], List[Dict[str, Any]]],
                             source: ChannelType) -> Dict[str, Any]:
        """호가 데이터를 REST API 형식으로 통일"""
        try:
            # list 형태의 데이터 처리
            if isinstance(data, list):
                if len(data) == 0:
                    logger.warning("빈 리스트 호가 데이터 수신")
                    return self._create_empty_response(source)

                # 다중 호가 데이터 처리
                if len(data) > 1:
                    unified_list = []
                    for item in data:
                        if source == ChannelType.WEBSOCKET:
                            unified_list.append(self._convert_websocket_orderbook_to_rest(item))
                        else:
                            unified_list.append(self._add_source_metadata(item, source))

                    return {
                        "_unified": True,
                        "_source": source.value,
                        "_timestamp": int(time.time() * 1000),
                        "_count": len(unified_list),
                        "_original_data": unified_list,
                        "data": unified_list
                    }
                else:
                    # 단일 아이템인 경우 첫 번째 요소 처리
                    data = data[0]

            # dict 형태의 데이터 처리 (기존 로직)
            if source == ChannelType.WEBSOCKET:
                return self._convert_websocket_orderbook_to_rest(data)
            else:
                return self._add_source_metadata(data, source)

        except Exception as e:
            logger.error(f"호가 데이터 형식 통일 실패: {e}")
            error_data = data if isinstance(data, dict) else {"error": "conversion_failed"}
            return self._create_error_response(error_data, source, str(e))

    def unify_trades_data(self, data: Union[Dict[str, Any], List[Dict[str, Any]]],
                          source: ChannelType) -> Dict[str, Any]:
        """체결 데이터를 REST API 형식으로 통일"""
        try:
            if source == ChannelType.WEBSOCKET:
                if isinstance(data, dict):
                    return self._convert_websocket_trades_to_rest(data)
                elif isinstance(data, list):
                    if len(data) == 0:
                        logger.warning("빈 리스트 체결 데이터 수신")
                        return self._create_empty_response(source)

                    # 다중 체결 데이터 처리
                    unified_list = []
                    for item in data:
                        if isinstance(item, dict):
                            unified_list.append(self._convert_websocket_trades_to_rest(item))
                        else:
                            logger.warning(f"체결 데이터 아이템이 dict가 아님: {type(item)}")

                    return {
                        "_unified": True,
                        "_source": source.value,
                        "_timestamp": int(time.time() * 1000),
                        "_count": len(unified_list),
                        "_original_data": unified_list,
                        "data": unified_list
                    }
                else:
                    logger.warning(f"WebSocket 체결 데이터가 예상 형식이 아님: {type(data)}")
                    error_data = {"error": "invalid_websocket_data"}
                    return self._create_error_response(error_data, source,
                                                       "Invalid WebSocket data format")
            else:
                # REST API 체결 데이터 처리
                if isinstance(data, list):
                    if len(data) == 0:
                        logger.warning("빈 리스트 체결 데이터 수신")
                        return self._create_empty_response(source)

                    # 체결 데이터 리스트 형태로 통일된 응답 생성
                    unified_list = []
                    for item in data:
                        if isinstance(item, dict):
                            unified_list.append(self._add_source_metadata(item, source))
                        else:
                            logger.warning(f"체결 데이터 아이템이 dict가 아님: {type(item)}")

                    return {
                        "_unified": True,
                        "_source": source.value,
                        "_timestamp": int(time.time() * 1000),
                        "_count": len(unified_list),
                        "_original_data": data,  # 원본 데이터 보관
                        "data": unified_list
                    }
                elif isinstance(data, dict):
                    return self._add_source_metadata(data, source)
                else:
                    logger.warning(f"예상치 못한 체결 데이터 형태: {type(data)}")
                    error_data = {"error": "invalid_data_format"}
                    return self._create_error_response(error_data, source, "Invalid data format")

        except Exception as e:
            logger.error(f"체결 데이터 형식 통일 실패: {e}")
            error_data = data if isinstance(data, dict) else {"error": "conversion_failed"}
            return self._create_error_response(error_data, source, str(e))

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
        """호환성을 위한 별칭 - 고속 메서드로 리다이렉트"""
        return self._fast_convert_websocket_ticker_to_rest(ws_data)

    def _convert_websocket_orderbook_to_rest(self, ws_data: Dict[str, Any]) -> Dict[str, Any]:
        """고속 WebSocket 호가 변환"""
        return self._fast_add_source_metadata({
            "market": ws_data.get("code", ""),
            "timestamp": ws_data.get("timestamp", int(time.time() * 1000)),
            "total_ask_size": float(ws_data.get("total_ask_size", 0)),
            "total_bid_size": float(ws_data.get("total_bid_size", 0)),
            "orderbook_units": ws_data.get("orderbook_units", []),
            "_original": ws_data
        }, ChannelType.WEBSOCKET)

    def _convert_websocket_trades_to_rest(self, ws_data: Dict[str, Any]) -> Dict[str, Any]:
        """고속 WebSocket 체결 변환"""
        timestamp = ws_data.get("trade_timestamp", int(time.time() * 1000))
        return self._fast_add_source_metadata({
            "market": ws_data.get("code", ""),
            "timestamp": timestamp,
            "trade_price": float(ws_data.get("trade_price", 0)),
            "trade_volume": float(ws_data.get("trade_volume", 0)),
            "ask_bid": ws_data.get("ask_bid", ""),
            "sequential_id": ws_data.get("sequential_id", 0),
            "_original": ws_data
        }, ChannelType.WEBSOCKET)

    def _convert_websocket_candles_to_rest(self, ws_data: Dict[str, Any]) -> Dict[str, Any]:
        """고속 WebSocket 캔들 변환"""
        timestamp = ws_data.get("timestamp", int(time.time() * 1000))
        return self._fast_add_source_metadata({
            "market": ws_data.get("code", ""),
            "timestamp": timestamp,
            "opening_price": float(ws_data.get("opening_price", 0)),
            "high_price": float(ws_data.get("high_price", 0)),
            "low_price": float(ws_data.get("low_price", 0)),
            "trade_price": float(ws_data.get("trade_price", 0)),
            "unit": 1,  # 1초 단위
            "_original": ws_data
        }, ChannelType.WEBSOCKET)

    def _fast_add_source_metadata(self, data: Dict[str, Any], source: ChannelType) -> Dict[str, Any]:
        """고속 소스 메타데이터 추가 - Dict 통일 정책"""
        # 성능 최적화: 템플릿 복사 후 필요한 부분만 수정
        result = data.copy()  # 얕은 복사로 성능 향상
        result.update({
            "_unified": True,
            "_source": source.value,
            "_timestamp": int(time.time() * 1000),
            "_format_version": "3.0"
        })
        return result

    def _fast_convert_websocket_ticker_to_rest(self, ws_data: Dict[str, Any]) -> Dict[str, Any]:
        """고속 WebSocket 티커 변환 - 필수 필드만 처리"""
        timestamp = ws_data.get("timestamp", int(time.time() * 1000))

        # 성능 최적화: 필수 필드만 처리하고 나머지는 원본 유지
        result = {
            # 핵심 필드만 변환
            "market": ws_data.get("code", ""),
            "trade_price": float(ws_data.get("trade_price", 0)),
            "change_rate": float(ws_data.get("change_rate", 0)),
            "timestamp": timestamp,

            # 메타데이터
            "_unified": True,
            "_source": "websocket",
            "_timestamp": int(time.time() * 1000),
            "_format_version": "3.0",

            # 원본 데이터 참조 (필요시 접근)
            "_original": ws_data
        }

        # 성능 중요 필드만 추가 변환
        if "opening_price" in ws_data:
            result["opening_price"] = float(ws_data["opening_price"])
        if "high_price" in ws_data:
            result["high_price"] = float(ws_data["high_price"])
        if "low_price" in ws_data:
            result["low_price"] = float(ws_data["low_price"])
        if "trade_volume" in ws_data:
            result["trade_volume"] = float(ws_data["trade_volume"])

        return result

    def _process_ticker_list(self, data_list: List[Dict[str, Any]], source: ChannelType, start_time: float) -> Dict[str, Any]:
        """고속 티커 리스트 처리 - Dict 통일 정책"""
        processed_items = []

        # 성능 최적화: 반복문 최적화
        if source == ChannelType.WEBSOCKET:
            for item in data_list:
                processed_items.append(self._fast_convert_websocket_ticker_to_rest(item))
        else:
            for item in data_list:
                processed_items.append(self._fast_add_source_metadata(item, source))

        return {
            "_unified": True,
            "_source": source.value,
            "_timestamp": int(time.time() * 1000),
            "_format_version": "3.0",
            "_count": len(processed_items),
            "_processing_time_ms": (time.time() - start_time) * 1000,
            "data": processed_items
        }

    def _create_fast_empty_response(self, source: ChannelType, start_time: float) -> Dict[str, Any]:
        """고속 빈 응답 생성"""
        return {
            "_unified": True,
            "_source": source.value,
            "_timestamp": int(time.time() * 1000),
            "_format_version": "3.0",
            "_count": 0,
            "_processing_time_ms": (time.time() - start_time) * 1000,
            "data": [],
            "success": True
        }

    def _create_fast_error_response(self, original_data: Any, source: ChannelType,
                                    error_msg: str, start_time: float) -> Dict[str, Any]:
        """고속 오류 응답 생성"""
        return {
            "_unified": True,
            "_source": source.value,
            "_timestamp": int(time.time() * 1000),
            "_format_version": "3.0",
            "_processing_time_ms": (time.time() - start_time) * 1000,
            "_error": error_msg,
            "_original_type": type(original_data).__name__,
            "success": False
        }

    # 호환성을 위한 별칭 메서드들
    def _add_source_metadata(self, data: Dict[str, Any], source: ChannelType) -> Dict[str, Any]:
        """호환성을 위한 별칭 - 고속 메서드로 리다이렉트"""
        return self._fast_add_source_metadata(data, source)

    def _create_error_response(self, original_data: Dict[str, Any],
                               source: ChannelType, error_msg: str) -> Dict[str, Any]:
        """호환성을 위한 오류 응답 - 고속 메서드로 리다이렉트"""
        return self._create_fast_error_response(original_data, source, error_msg, time.time())

    def _create_empty_response(self, source: ChannelType) -> Dict[str, Any]:
        """호환성을 위한 빈 응답 - 고속 메서드로 리다이렉트"""
        return self._create_fast_empty_response(source, time.time())

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
