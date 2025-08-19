"""
MarketDataBackbone V2 - 데이터 생성 로직

소스별 TickerData 생성과 기본 변환을 담당합니다.
"""

from typing import Dict, Any
from decimal import Decimal
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .market_data_backbone import TickerData
from .data_models import DataSource


class TickerDataCreator:
    """소스별 TickerData 생성 담당 클래스"""

    def __init__(self):
        self._logger = create_component_logger("TickerDataCreator")

    def create_ticker_data(self, raw_data: Dict[str, Any], source: DataSource) -> TickerData:
        """소스별 TickerData 생성"""
        if source == DataSource.REST:
            return self._create_from_rest(raw_data)
        elif source in [DataSource.WEBSOCKET, DataSource.WEBSOCKET_SIMPLE]:
            return self._create_from_websocket(raw_data, source)
        else:
            raise ValueError(f"지원하지 않는 데이터 소스: {source}")

    def _create_from_rest(self, data: Dict[str, Any]) -> TickerData:
        """REST API 데이터로부터 TickerData 생성"""
        return TickerData(
            symbol=data["market"],
            current_price=Decimal(str(data["trade_price"])),
            change_rate=Decimal(str(data.get("signed_change_rate", 0))) * 100,
            change_amount=Decimal(str(data.get("signed_change_price", 0))),
            volume_24h=Decimal(str(data.get("acc_trade_volume_24h", 0))),
            high_24h=Decimal(str(data.get("high_price", 0))),
            low_24h=Decimal(str(data.get("low_price", 0))),
            prev_closing_price=Decimal(str(data.get("prev_closing_price", 0))),
            timestamp=datetime.now(),
            source=DataSource.REST.value
        )

    def _create_from_websocket(self, data: Dict[str, Any], source: DataSource) -> TickerData:
        """WebSocket 데이터로부터 TickerData 생성"""
        if source == DataSource.WEBSOCKET_SIMPLE:
            # SIMPLE 포맷 (축약된 필드명)
            symbol_field = "cd"
            price_field = "tp"
            change_rate_field = "scr"
            change_amount_field = "scp"
            volume_field = "aav24"
            high_field = "hp"
            low_field = "lp"
        else:
            # DEFAULT 포맷 (전체 필드명)
            symbol_field = "code"
            price_field = "trade_price"
            change_rate_field = "signed_change_rate"
            change_amount_field = "signed_change_price"
            volume_field = "acc_trade_volume_24h"
            high_field = "high_price"
            low_field = "low_price"

        return TickerData(
            symbol=data[symbol_field],
            current_price=Decimal(str(data[price_field])),
            change_rate=Decimal(str(data.get(change_rate_field, 0))) * 100,
            change_amount=Decimal(str(data.get(change_amount_field, 0))),
            volume_24h=Decimal(str(data.get(volume_field, 0))),
            high_24h=Decimal(str(data.get(high_field, 0))),
            low_24h=Decimal(str(data.get(low_field, 0))),
            prev_closing_price=Decimal(str(data.get("prev_closing_price", 0))),
            timestamp=datetime.now(),
            source=source.value
        )

    def validate_required_fields(self, raw_data: Dict[str, Any], source: DataSource) -> None:
        """필수 필드 검증 - 누락 시 예외 발생"""
        required_fields = []

        if source == DataSource.REST:
            required_fields = ["market", "trade_price"]
        elif source == DataSource.WEBSOCKET:
            required_fields = ["code", "trade_price"]
        elif source == DataSource.WEBSOCKET_SIMPLE:
            required_fields = ["cd", "tp"]

        missing_fields = []
        for field in required_fields:
            if field not in raw_data:
                missing_fields.append(field)

        if missing_fields:
            error_msg = f"필수 필드 누락: {', '.join(missing_fields)}"
            self._logger.error(error_msg)
            raise ValueError(error_msg)

    def extract_symbol_safe(self, raw_data: Dict[str, Any], source: DataSource) -> str:
        """안전한 심볼 추출"""
        try:
            if source == DataSource.REST:
                return raw_data.get("market", "UNKNOWN")
            elif source == DataSource.WEBSOCKET:
                return raw_data.get("code", "UNKNOWN")
            elif source == DataSource.WEBSOCKET_SIMPLE:
                return raw_data.get("cd", "UNKNOWN")
        except Exception:
            pass
        return "UNKNOWN"
