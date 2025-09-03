"""
WebSocket v6.0 포맷 유틸리티
==========================

업비트 WebSocket 메시지 포맷팅 및 변환 유틸리티
- 업비트 API 메시지 변환
- 구독 메시지 생성
- 데이터 정규화
- SIMPLE ↔ DEFAULT 포맷 변환 (압축 지원)
"""

import json
import time
from typing import Dict, List, Any, Optional
from decimal import Decimal

from upbit_auto_trading.infrastructure.logging import create_component_logger
from ..core.websocket_types import DataType

# ================================================================
# SIMPLE 포맷 매핑 (업비트 공식 압축 포맷)
# ================================================================

# TICKER SIMPLE 매핑 (업비트 공식 문서 정확 반영)
TICKER_SIMPLE_MAPPING = {
    # 기본 필드
    'type': 'ty', 'code': 'cd', 'timestamp': 'tms', 'stream_type': 'st',

    # 가격 정보
    'opening_price': 'op', 'high_price': 'hp', 'low_price': 'lp', 'trade_price': 'tp', 'prev_closing_price': 'pcp',

    # 변화 정보
    'change': 'c', 'change_price': 'cp', 'signed_change_price': 'scp', 'change_rate': 'cr', 'signed_change_rate': 'scr',

    # 거래량/거래대금
    'trade_volume': 'tv', 'acc_trade_volume': 'atv', 'acc_trade_volume_24h': 'atv24h',
    'acc_trade_price': 'atp', 'acc_trade_price_24h': 'atp24h',

    # 거래 시간 정보
    'trade_date': 'tdt', 'trade_time': 'ttm', 'trade_timestamp': 'ttms',

    # 매수/매도 정보
    'ask_bid': 'ab', 'acc_ask_volume': 'aav', 'acc_bid_volume': 'abv',

    # 52주 고/저가
    'highest_52_week_price': 'h52wp', 'highest_52_week_date': 'h52wdt',
    'lowest_52_week_price': 'l52wp', 'lowest_52_week_date': 'l52wdt',

    # 시장 상태 (일부 Deprecated 포함)
    'trade_status': 'ts',  # Deprecated
    'market_state': 'ms', 'market_state_for_ios': 'msfi',  # msfi는 Deprecated
    'is_trading_suspended': 'its',  # Deprecated
    'delisting_date': 'dd', 'market_warning': 'mw',
}

# TRADE SIMPLE 매핑
TRADE_SIMPLE_MAPPING = {
    'type': 'ty', 'code': 'cd', 'timestamp': 'tms', 'stream_type': 'st',
    'trade_price': 'tp', 'trade_volume': 'tv', 'ask_bid': 'ab', 'prev_closing_price': 'pcp',
    'change': 'c', 'change_price': 'cp',
    'trade_date': 'td', 'trade_time': 'ttm', 'trade_timestamp': 'ttms',
    'sequential_id': 'sid',
    'best_ask_price': 'bap', 'best_ask_size': 'bas', 'best_bid_price': 'bbp', 'best_bid_size': 'bbs',
}

# ORDERBOOK SIMPLE 매핑
ORDERBOOK_SIMPLE_MAPPING = {
    'type': 'ty', 'code': 'cd', 'timestamp': 'tms', 'stream_type': 'st',
    'total_ask_size': 'tas', 'total_bid_size': 'tbs',
    'orderbook_units': 'obu', 'level': 'lv',
}

ORDERBOOK_UNITS_SIMPLE_MAPPING = {
    'ask_price': 'ap', 'bid_price': 'bp', 'ask_size': 'as', 'bid_size': 'bs',
}

# CANDLE SIMPLE 매핑
CANDLE_SIMPLE_MAPPING = {
    'type': 'ty', 'code': 'cd', 'timestamp': 'tms', 'stream_type': 'st',
    'candle_date_time_utc': 'cdttmu', 'candle_date_time_kst': 'cdttmk',
    'opening_price': 'op', 'high_price': 'hp', 'low_price': 'lp', 'trade_price': 'tp', 'prev_closing_price': 'pcp',
    'candle_acc_trade_volume': 'catv', 'candle_acc_trade_price': 'catp',
    'change': 'c', 'change_price': 'cp', 'change_rate': 'cr', 'signed_change_price': 'scp', 'signed_change_rate': 'scr',
    'unit': 'u',
}

# MYORDER SIMPLE 매핑
MYORDER_SIMPLE_MAPPING = {
    'type': 'ty', 'code': 'cd', 'uuid': 'uid', 'timestamp': 'tms', 'stream_type': 'st',
    'ask_bid': 'ab', 'order_type': 'ot', 'state': 's', 'trade_uuid': 'tuid',
    'price': 'p', 'avg_price': 'ap', 'volume': 'v', 'remaining_volume': 'rv', 'executed_volume': 'ev',
    'trades_count': 'tc', 'reserved_fee': 'rsf', 'remaining_fee': 'rmf', 'paid_fee': 'pf',
    'locked': 'l', 'executed_funds': 'ef', 'trade_fee': 'tf',
    'time_in_force': 'tif', 'is_maker': 'im', 'identifier': 'id',
    'smp_type': 'smpt', 'prevented_volume': 'pv', 'prevented_locked': 'pl',
    'trade_timestamp': 'ttms', 'order_timestamp': 'otms',
}

# MYASSET SIMPLE 매핑
MYASSET_SIMPLE_MAPPING = {
    'type': 'ty', 'asset_uuid': 'astuid', 'timestamp': 'tms', 'stream_type': 'st',
    'assets': 'ast', 'asset_timestamp': 'asttms',
}

MYASSET_ASSETS_SIMPLE_MAPPING = {
    'currency': 'cu', 'balance': 'b', 'locked': 'l',
}

# 역방향 매핑 생성
TICKER_SIMPLE_REVERSE = {v: k for k, v in TICKER_SIMPLE_MAPPING.items()}
TRADE_SIMPLE_REVERSE = {v: k for k, v in TRADE_SIMPLE_MAPPING.items()}
ORDERBOOK_SIMPLE_REVERSE = {v: k for k, v in ORDERBOOK_SIMPLE_MAPPING.items()}
ORDERBOOK_UNITS_SIMPLE_REVERSE = {v: k for k, v in ORDERBOOK_UNITS_SIMPLE_MAPPING.items()}
CANDLE_SIMPLE_REVERSE = {v: k for k, v in CANDLE_SIMPLE_MAPPING.items()}
MYORDER_SIMPLE_REVERSE = {v: k for k, v in MYORDER_SIMPLE_MAPPING.items()}
MYASSET_SIMPLE_REVERSE = {v: k for k, v in MYASSET_SIMPLE_MAPPING.items()}
MYASSET_ASSETS_SIMPLE_REVERSE = {v: k for k, v in MYASSET_ASSETS_SIMPLE_MAPPING.items()}


class UpbitMessageFormatter:
    """업비트 메시지 포맷터 (SIMPLE ↔ DEFAULT 변환 지원)"""

    def __init__(self):
        self.logger = create_component_logger("UpbitMessageFormatter")

    # ================================================================
    # SIMPLE → DEFAULT 변환 (핵심 기능)
    # ================================================================

    def convert_simple_to_default(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        SIMPLE 포맷 → DEFAULT 포맷 변환 (자동 타입 감지)

        Args:
            data: SIMPLE 포맷 데이터

        Returns:
            DEFAULT 포맷 데이터
        """
        try:
            # 타입 감지
            data_type = self._detect_simple_type(data)
            if not data_type:
                self.logger.warning("SIMPLE 타입 감지 실패, 원본 반환")
                return data

            # 타입별 변환
            if data_type == 'ticker':
                return self._convert_mapping(data, TICKER_SIMPLE_REVERSE)
            elif data_type == 'trade':
                return self._convert_mapping(data, TRADE_SIMPLE_REVERSE)
            elif data_type == 'orderbook':
                return self._convert_orderbook_simple_to_default(data)
            elif data_type.startswith('candle'):
                return self._convert_mapping(data, CANDLE_SIMPLE_REVERSE)
            elif data_type == 'myorder':
                return self._convert_mapping(data, MYORDER_SIMPLE_REVERSE)
            elif data_type == 'myasset':
                return self._convert_myasset_simple_to_default(data)
            else:
                self.logger.warning(f"지원하지 않는 SIMPLE 타입: {data_type}")
                return data

        except Exception as e:
            self.logger.error(f"SIMPLE → DEFAULT 변환 실패: {e}")
            return data

    def convert_default_to_simple(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        DEFAULT 포맷 → SIMPLE 포맷 변환 (자동 타입 감지)

        Args:
            data: DEFAULT 포맷 데이터

        Returns:
            SIMPLE 포맷 데이터
        """
        try:
            # 타입 감지
            data_type = self._detect_default_type(data)
            if not data_type:
                self.logger.warning("DEFAULT 타입 감지 실패, 원본 반환")
                return data

            # 타입별 변환
            if data_type == 'ticker':
                return self._convert_mapping(data, TICKER_SIMPLE_MAPPING)
            elif data_type == 'trade':
                return self._convert_mapping(data, TRADE_SIMPLE_MAPPING)
            elif data_type == 'orderbook':
                return self._convert_orderbook_default_to_simple(data)
            elif data_type.startswith('candle'):
                return self._convert_mapping(data, CANDLE_SIMPLE_MAPPING)
            elif data_type == 'myorder':
                return self._convert_mapping(data, MYORDER_SIMPLE_MAPPING)
            elif data_type == 'myasset':
                return self._convert_myasset_default_to_simple(data)
            else:
                self.logger.warning(f"지원하지 않는 DEFAULT 타입: {data_type}")
                return data

        except Exception as e:
            self.logger.error(f"DEFAULT → SIMPLE 변환 실패: {e}")
            return data

    def _detect_simple_type(self, data: Dict[str, Any]) -> Optional[str]:
        """SIMPLE 포맷 타입 감지"""
        type_val = data.get('ty', data.get('type'))
        return type_val.lower() if type_val else None

    def _detect_default_type(self, data: Dict[str, Any]) -> Optional[str]:
        """DEFAULT 포맷 타입 감지"""
        type_val = data.get('type', data.get('ty'))
        return type_val.lower() if type_val else None

    def _convert_mapping(self, data: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
        """매핑 테이블을 사용한 필드 변환"""
        result = {}
        for key, value in data.items():
            new_key = mapping.get(key, key)
            result[new_key] = value
        return result

    def _convert_orderbook_simple_to_default(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Orderbook SIMPLE → DEFAULT 변환 (배열 처리 포함)"""
        result = self._convert_mapping(data, ORDERBOOK_SIMPLE_REVERSE)

        # orderbook_units 배열 변환
        if 'orderbook_units' in result:
            units = result['orderbook_units']
            if isinstance(units, list):
                converted_units = []
                for unit in units:
                    if isinstance(unit, dict):
                        converted_units.append(
                            self._convert_mapping(unit, ORDERBOOK_UNITS_SIMPLE_REVERSE)
                        )
                    else:
                        converted_units.append(unit)
                result['orderbook_units'] = converted_units

        return result

    def _convert_orderbook_default_to_simple(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Orderbook DEFAULT → SIMPLE 변환 (배열 처리 포함)"""
        result = self._convert_mapping(data, ORDERBOOK_SIMPLE_MAPPING)

        # orderbook_units 배열 변환
        if 'obu' in result:  # SIMPLE 키
            units = result['obu']
            if isinstance(units, list):
                converted_units = []
                for unit in units:
                    if isinstance(unit, dict):
                        converted_units.append(
                            self._convert_mapping(unit, ORDERBOOK_UNITS_SIMPLE_MAPPING)
                        )
                    else:
                        converted_units.append(unit)
                result['obu'] = converted_units

        return result

    def _convert_myasset_simple_to_default(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """MyAsset SIMPLE → DEFAULT 변환 (자산 배열 처리 포함)"""
        result = self._convert_mapping(data, MYASSET_SIMPLE_REVERSE)

        # assets 배열 변환
        if 'assets' in result:
            assets = result['assets']
            if isinstance(assets, list):
                converted_assets = []
                for asset in assets:
                    if isinstance(asset, dict):
                        converted_assets.append(
                            self._convert_mapping(asset, MYASSET_ASSETS_SIMPLE_REVERSE)
                        )
                    else:
                        converted_assets.append(asset)
                result['assets'] = converted_assets

        return result

    def _convert_myasset_default_to_simple(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """MyAsset DEFAULT → SIMPLE 변환 (자산 배열 처리 포함)"""
        result = self._convert_mapping(data, MYASSET_SIMPLE_MAPPING)

        # assets 배열 변환
        if 'ast' in result:  # SIMPLE 키
            assets = result['ast']
            if isinstance(assets, list):
                converted_assets = []
                for asset in assets:
                    if isinstance(asset, dict):
                        converted_assets.append(
                            self._convert_mapping(asset, MYASSET_ASSETS_SIMPLE_MAPPING)
                        )
                    else:
                        converted_assets.append(asset)
                result['ast'] = converted_assets

        return result

    # ================================================================
    # 기존 구독 메시지 생성 및 정규화 기능
    # ================================================================

    def create_subscription_message(
        self,
        data_type: DataType,
        symbols: List[str],
        is_only_snapshot: bool = False,
        is_only_realtime: bool = False
    ) -> List[Dict[str, Any]]:
        """
        업비트 구독 메시지 생성

        Args:
            data_type: 데이터 타입
            symbols: 심볼 리스트
            is_only_snapshot: 스냅샷만 수신 여부
            is_only_realtime: 실시간만 수신 여부

        Returns:
            업비트 형식의 구독 메시지 배열
        """
        ticket = {
            "ticket": f"upbit_ws_v6_{int(time.time() * 1000)}"
        }

        type_message = {
            "type": data_type.value,
            "codes": symbols,
            "isOnlySnapshot": is_only_snapshot,
            "isOnlyRealtime": is_only_realtime
        }

        format_message = {
            "format": "DEFAULT"
        }

        return [ticket, type_message, format_message]

    def create_unsubscription_message(
        self,
        data_type: DataType,
        symbols: List[str]
    ) -> List[Dict[str, Any]]:
        """
        업비트 구독 해제 메시지 생성

        Args:
            data_type: 데이터 타입
            symbols: 해제할 심볼 리스트

        Returns:
            업비트 형식의 구독 해제 메시지
        """
        ticket = {
            "ticket": f"upbit_ws_v6_unsub_{int(time.time() * 1000)}"
        }

        type_message = {
            "type": data_type.value,
            "codes": symbols,
            "isOnlySnapshot": False,
            "isOnlyRealtime": False
        }

        format_message = {
            "format": "DEFAULT"
        }

        return [ticket, type_message, format_message]

    def parse_upbit_message(self, raw_data: str) -> Optional[Dict[str, Any]]:
        """
        업비트 원시 메시지 파싱

        Args:
            raw_data: 원시 JSON 문자열

        Returns:
            파싱된 딕셔너리 또는 None
        """
        try:
            return json.loads(raw_data)
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON 파싱 실패: {e}")
            return None
        except Exception as e:
            self.logger.error(f"메시지 파싱 오류: {e}")
            return None

    def normalize_ticker_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        업비트 Ticker 데이터 정규화 (공식 문서 모든 필드 지원)

        Args:
            raw_data: 업비트 원시 Ticker 데이터

        Returns:
            정규화된 Ticker 데이터
        """
        try:
            return {
                # 기본 정보
                "symbol": raw_data.get("code", ""),
                "type": raw_data.get("type", "ticker"),

                # 가격 정보
                "opening_price": self._to_decimal(raw_data.get("opening_price")),
                "high_price": self._to_decimal(raw_data.get("high_price")),
                "low_price": self._to_decimal(raw_data.get("low_price")),
                "trade_price": self._to_decimal(raw_data.get("trade_price")),
                "prev_closing_price": self._to_decimal(raw_data.get("prev_closing_price")),

                # 변화 정보
                "change": raw_data.get("change", ""),  # RISE/EVEN/FALL
                "change_price": self._to_decimal(raw_data.get("change_price")),
                "signed_change_price": self._to_decimal(raw_data.get("signed_change_price")),
                "change_rate": self._to_decimal(raw_data.get("change_rate")),
                "signed_change_rate": self._to_decimal(raw_data.get("signed_change_rate")),

                # 거래량/거래대금
                "trade_volume": self._to_decimal(raw_data.get("trade_volume")),
                "acc_trade_volume": self._to_decimal(raw_data.get("acc_trade_volume")),
                "acc_trade_volume_24h": self._to_decimal(raw_data.get("acc_trade_volume_24h")),
                "acc_trade_price": self._to_decimal(raw_data.get("acc_trade_price")),
                "acc_trade_price_24h": self._to_decimal(raw_data.get("acc_trade_price_24h")),

                # 거래 시간 정보
                "trade_date": raw_data.get("trade_date", ""),  # yyyyMMdd
                "trade_time": raw_data.get("trade_time", ""),  # HHmmss
                "trade_timestamp": raw_data.get("trade_timestamp"),  # ms

                # 매수/매도 정보
                "ask_bid": raw_data.get("ask_bid", ""),  # ASK/BID
                "acc_ask_volume": self._to_decimal(raw_data.get("acc_ask_volume")),
                "acc_bid_volume": self._to_decimal(raw_data.get("acc_bid_volume")),

                # 52주 고/저가
                "highest_52_week_price": self._to_decimal(raw_data.get("highest_52_week_price")),
                "highest_52_week_date": raw_data.get("highest_52_week_date", ""),  # yyyy-MM-dd
                "lowest_52_week_price": self._to_decimal(raw_data.get("lowest_52_week_price")),
                "lowest_52_week_date": raw_data.get("lowest_52_week_date", ""),  # yyyy-MM-dd

                # 거래 상태 (일부 Deprecated)
                "trade_status": raw_data.get("trade_status", ""),  # Deprecated
                "market_state": raw_data.get("market_state", ""),  # PREVIEW/ACTIVE/DELISTED
                "market_state_for_ios": raw_data.get("market_state_for_ios", ""),  # Deprecated
                "is_trading_suspended": raw_data.get("is_trading_suspended", False),  # Deprecated
                "delisting_date": raw_data.get("delisting_date"),
                "market_warning": raw_data.get("market_warning", ""),  # NONE/CAUTION

                # 시스템 정보
                "timestamp": raw_data.get("timestamp"),
                "stream_type": raw_data.get("stream_type", ""),  # SNAPSHOT/REALTIME
            }
        except Exception as e:
            self.logger.error(f"Ticker 데이터 정규화 실패: {e}")
            return raw_data

    def normalize_orderbook_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        업비트 Orderbook 데이터 정규화

        Args:
            raw_data: 업비트 원시 Orderbook 데이터

        Returns:
            정규화된 Orderbook 데이터
        """
        try:
            orderbook_units = raw_data.get("orderbook_units", [])

            normalized_units = []
            for unit in orderbook_units:
                normalized_units.append({
                    "ask_price": self._to_decimal(unit.get("ask_price")),
                    "bid_price": self._to_decimal(unit.get("bid_price")),
                    "ask_size": self._to_decimal(unit.get("ask_size")),
                    "bid_size": self._to_decimal(unit.get("bid_size"))
                })

            return {
                "symbol": raw_data.get("code", ""),
                "total_ask_size": self._to_decimal(raw_data.get("total_ask_size")),
                "total_bid_size": self._to_decimal(raw_data.get("total_bid_size")),
                "orderbook_units": normalized_units,
                "timestamp": raw_data.get("timestamp"),
                "stream_type": raw_data.get("stream_type", ""),
                "level": raw_data.get("level", 0)  # 호가 모아보기 단위 추가
            }
        except Exception as e:
            self.logger.error(f"Orderbook 데이터 정규화 실패: {e}")
            return raw_data

    def normalize_trade_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        업비트 Trade 데이터 정규화

        Args:
            raw_data: 업비트 원시 Trade 데이터

        Returns:
            정규화된 Trade 데이터
        """
        try:
            return {
                "symbol": raw_data.get("code", ""),
                "trade_price": self._to_decimal(raw_data.get("trade_price")),
                "trade_volume": self._to_decimal(raw_data.get("trade_volume")),
                "ask_bid": raw_data.get("ask_bid", ""),
                "prev_closing_price": self._to_decimal(raw_data.get("prev_closing_price")),
                "change": raw_data.get("change", ""),
                "change_price": self._to_decimal(raw_data.get("change_price")),
                "trade_date": raw_data.get("trade_date", ""),
                "trade_time": raw_data.get("trade_time", ""),
                "trade_timestamp": raw_data.get("trade_timestamp"),
                "timestamp": raw_data.get("timestamp"),
                "sequential_id": raw_data.get("sequential_id")
            }
        except Exception as e:
            self.logger.error(f"Trade 데이터 정규화 실패: {e}")
            return raw_data

    def normalize_candle_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        업비트 Candle 데이터 정규화

        Args:
            raw_data: 업비트 원시 Candle 데이터

        Returns:
            정규화된 Candle 데이터
        """
        try:
            return {
                "symbol": raw_data.get("code", ""),
                "opening_price": self._to_decimal(raw_data.get("opening_price")),
                "high_price": self._to_decimal(raw_data.get("high_price")),
                "low_price": self._to_decimal(raw_data.get("low_price")),
                "trade_price": self._to_decimal(raw_data.get("trade_price")),
                "candle_acc_trade_price": self._to_decimal(raw_data.get("candle_acc_trade_price")),
                "candle_acc_trade_volume": self._to_decimal(raw_data.get("candle_acc_trade_volume")),
                "unit": raw_data.get("unit"),
                "timestamp": raw_data.get("timestamp"),
                "candle_date_time_utc": raw_data.get("candle_date_time_utc", ""),
                "candle_date_time_kst": raw_data.get("candle_date_time_kst", ""),
                "prev_closing_price": self._to_decimal(raw_data.get("prev_closing_price")),
                "change_price": self._to_decimal(raw_data.get("change_price")),
                "change_rate": self._to_decimal(raw_data.get("change_rate"))
            }
        except Exception as e:
            self.logger.error(f"Candle 데이터 정규화 실패: {e}")
            return raw_data

    def _to_decimal(self, value: Any) -> Optional[Decimal]:
        """
        값을 Decimal로 변환

        Args:
            value: 변환할 값

        Returns:
            Decimal 값 또는 None
        """
        if value is None:
            return None

        try:
            if isinstance(value, (int, float, str)):
                return Decimal(str(value))
            return None
        except (ValueError, TypeError):
            return None

    def detect_message_type(self, data: Dict[str, Any]) -> Optional[DataType]:
        """
        메시지 타입 감지 (통합 버전)

        Args:
            data: 메시지 데이터

        Returns:
            감지된 데이터 타입 또는 None
        """
        # 직접적인 타입 필드 확인 (SIMPLE/DEFAULT 포맷 모두 지원)
        type_field = data.get("ty", data.get("type", "")).lower()

        # 업비트 타입 매핑
        type_mapping = {
            "ticker": DataType.TICKER,
            "orderbook": DataType.ORDERBOOK,
            "trade": DataType.TRADE,
            "myorder": DataType.MYORDER,
            "myasset": DataType.MYASSET,
        }

        # 정확한 매칭
        if type_field in type_mapping:
            return type_mapping[type_field]

        # Candle 타입은 여러 형태가 있음
        if type_field.startswith("candle."):
            # 업비트의 candle 타입에 맞는 DataType 찾기
            for data_type in DataType:
                if data_type.value == type_field:
                    return data_type
            # 기본값으로 1분 캔들 반환
            return DataType.CANDLE_1M

        # 필드 기반 추론 (타입 필드가 없는 경우)
        if not type_field:
            if 'trade_price' in data and 'change' in data:
                return DataType.TICKER
            elif 'orderbook_units' in data:
                return DataType.ORDERBOOK
            elif 'trade_price' in data and 'ask_bid' in data:
                return DataType.TRADE
            elif 'opening_price' in data and 'high_price' in data:
                return DataType.CANDLE_1M  # 기본값
            elif 'order_uuid' in data:
                return DataType.MYORDER
            elif 'currency' in data and 'balance' in data:
                return DataType.MYASSET

        return None

    def create_ping_message(self) -> Dict[str, str]:
        """
        Ping 메시지 생성

        Returns:
            Ping 메시지
        """
        return {
            "ticket": f"upbit_ping_{int(time.time() * 1000)}",
            "type": "ping"
        }

    def is_pong_message(self, data: Dict[str, Any]) -> bool:
        """
        Pong 메시지 여부 확인

        Args:
            data: 메시지 데이터

        Returns:
            Pong 메시지 여부
        """
        return data.get("type") == "pong"


# 전역 포맷터 인스턴스
_global_formatter: Optional[UpbitMessageFormatter] = None


def get_message_formatter() -> UpbitMessageFormatter:
    """
    글로벌 메시지 포맷터 반환

    Returns:
        UpbitMessageFormatter 인스턴스
    """
    global _global_formatter
    if _global_formatter is None:
        _global_formatter = UpbitMessageFormatter()
    return _global_formatter


def create_subscription_message(
    data_type: DataType,
    symbols: List[str],
    is_only_snapshot: bool = False,
    is_only_realtime: bool = False
) -> str:
    """
    구독 메시지 생성 (편의 함수)

    Args:
        data_type: 데이터 타입
        symbols: 심볼 리스트
        is_only_snapshot: 스냅샷만 수신 여부
        is_only_realtime: 실시간만 수신 여부

    Returns:
        JSON 문자열 형태의 구독 메시지
    """
    formatter = get_message_formatter()
    message = formatter.create_subscription_message(
        data_type, symbols, is_only_snapshot, is_only_realtime
    )
    return json.dumps(message)


def normalize_upbit_data(data_type: DataType, raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    업비트 데이터 정규화 (편의 함수)

    Args:
        data_type: 데이터 타입
        raw_data: 원시 데이터

    Returns:
        정규화된 데이터
    """
    formatter = get_message_formatter()

    if data_type == DataType.TICKER:
        return formatter.normalize_ticker_data(raw_data)
    elif data_type == DataType.ORDERBOOK:
        return formatter.normalize_orderbook_data(raw_data)
    elif data_type == DataType.TRADE:
        return formatter.normalize_trade_data(raw_data)
    elif data_type.value.startswith("candle."):
        return formatter.normalize_candle_data(raw_data)
    else:
        return raw_data


# ================================================================
# SIMPLE 포맷 변환 편의 함수들 (핵심 기능)
# ================================================================

def convert_simple_to_default(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    SIMPLE 포맷을 DEFAULT 포맷으로 변환 (편의 함수)

    사용자가 압축된 SIMPLE 포맷을 받아서 표준 DEFAULT 포맷으로 사용할 수 있도록 함

    Args:
        data: SIMPLE 포맷 데이터

    Returns:
        DEFAULT 포맷 데이터

    Example:
        >>> simple_data = {'ty': 'ticker', 'cd': 'KRW-BTC', 'tp': 50000000}
        >>> default_data = convert_simple_to_default(simple_data)
        >>> # {'type': 'ticker', 'code': 'KRW-BTC', 'trade_price': 50000000}
    """
    formatter = get_message_formatter()
    return formatter.convert_simple_to_default(data)


def convert_default_to_simple(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    DEFAULT 포맷을 SIMPLE 포맷으로 변환 (편의 함수)

    Args:
        data: DEFAULT 포맷 데이터

    Returns:
        SIMPLE 포맷 데이터 (압축됨)
    """
    formatter = get_message_formatter()
    return formatter.convert_default_to_simple(data)


def is_simple_format(data: Dict[str, Any]) -> bool:
    """
    데이터가 SIMPLE 포맷인지 확인

    Args:
        data: 확인할 데이터

    Returns:
        SIMPLE 포맷 여부
    """
    # SIMPLE 포맷은 일반적으로 짧은 키를 사용
    if not isinstance(data, dict):
        return False

    # 'ty' 키가 있으면 SIMPLE, 'type' 키가 있으면 DEFAULT로 판단
    return 'ty' in data and 'type' not in data


def auto_convert_to_default(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    자동으로 포맷을 감지하고 DEFAULT 포맷으로 변환

    사용자가 어떤 포맷인지 신경쓰지 않고 항상 DEFAULT 포맷을 받을 수 있도록 함

    Args:
        data: 임의 포맷의 데이터

    Returns:
        DEFAULT 포맷 데이터
    """
    if is_simple_format(data):
        return convert_simple_to_default(data)
    else:
        return data  # 이미 DEFAULT 포맷으로 간주
