"""
호가창 포맷터 - Infrastructure Layer

호가창 데이터의 표시 포맷팅을 담당합니다.
- 가격 포맷팅 (KRW/BTC/USDT별)
- 수량 포맷팅
- 스프레드 계산
- 테이블 데이터 변환
"""

from typing import Dict, Any, List, Tuple
from decimal import Decimal

from upbit_auto_trading.infrastructure.logging import create_component_logger


class OrderbookFormatter:
    """호가창 데이터 포맷터"""

    def __init__(self):
        """포맷터 초기화"""
        self._logger = create_component_logger("OrderbookFormatter")

    def format_orderbook_for_table(self, data: Dict[str, Any]) -> List[List[str]]:
        """호가창 데이터를 테이블 형식으로 변환"""
        if not data or not data.get("asks") or not data.get("bids"):
            return []

        asks = data["asks"]
        bids = data["bids"]
        market = data.get("market", "KRW")

        # 테이블 데이터 생성 (60행: 매도 30행 + 매수 30행)
        table_data = []

        # 매도 호가 (역순으로 표시 - 가격이 높은 것부터)
        for i in range(min(30, len(asks))):
            ask = asks[-(i+1)]  # 뒤에서부터 (가격 높은 순)
            row = [
                str(30 - i),  # 번호
                self._format_quantity(ask["quantity"]),
                self._format_price(ask["price"], market),
                self._format_quantity(ask["total"])
            ]
            table_data.append(row)

        # 매수 호가
        for i in range(min(30, len(bids))):
            bid = bids[i]
            row = [
                str(31 + i),  # 번호
                self._format_quantity(bid["quantity"]),
                self._format_price(bid["price"], market),
                self._format_quantity(bid["total"])
            ]
            table_data.append(row)

        return table_data

    def calculate_spread_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """스프레드 정보 계산"""
        if not data or not data.get("asks") or not data.get("bids"):
            return {"spread": 0, "spread_percent": 0, "best_ask": 0, "best_bid": 0}

        asks = data["asks"]
        bids = data["bids"]

        # 최우선 호가
        best_ask = min(ask["price"] for ask in asks) if asks else 0
        best_bid = max(bid["price"] for bid in bids) if bids else 0

        # 스프레드 계산
        spread = best_ask - best_bid if best_ask and best_bid else 0
        spread_percent = (spread / best_bid * 100) if best_bid > 0 else 0

        return {
            "spread": spread,
            "spread_percent": spread_percent,
            "best_ask": best_ask,
            "best_bid": best_bid
        }

    def format_spread_text(self, spread_info: Dict[str, Any], market: str) -> str:
        """스프레드 텍스트 포맷팅"""
        spread = spread_info.get("spread", 0)
        spread_percent = spread_info.get("spread_percent", 0)

        spread_text = self._format_price(spread, market)
        return f"스프레드: {spread_text} ({spread_percent:.2f}%)"

    def format_price_info_text(self, spread_info: Dict[str, Any], market: str) -> str:
        """가격 정보 텍스트 포맷팅"""
        best_bid = spread_info.get("best_bid", 0)
        best_ask = spread_info.get("best_ask", 0)

        bid_text = self._format_price(best_bid, market)
        ask_text = self._format_price(best_ask, market)

        return f"매수: {bid_text} | 매도: {ask_text}"

    def format_market_info_text(self, data: Dict[str, Any]) -> str:
        """시장 정보 텍스트 포맷팅"""
        asks = data.get("asks", [])
        bids = data.get("bids", [])

        total_ask_volume = sum(ask.get("quantity", 0) for ask in asks)
        total_bid_volume = sum(bid.get("quantity", 0) for bid in bids)

        # 거래량과 유동성 표시
        ask_volume_text = self._format_quantity(total_ask_volume)
        bid_volume_text = self._format_quantity(total_bid_volume)

        return f"거래량: 매도 {ask_volume_text} | 매수 {bid_volume_text}"

    def _format_price(self, price: float, market: str) -> str:
        """가격 포맷팅"""
        if price == 0:
            return "-"

        try:
            if market == "KRW":
                # KRW: 원화 표시
                if price >= 1000:
                    return f"{price:,.0f}"
                elif price >= 100:
                    return f"{price:.1f}"
                else:
                    return f"{price:.2f}"
            elif market == "BTC":
                # BTC: 8자리 정밀도
                return f"{price:.8f}"
            elif market == "USDT":
                # USDT: 4자리 정밀도
                return f"{price:.4f}"
            else:
                # 기타: 기본 포맷
                return f"{price:.4f}"
        except (ValueError, TypeError):
            return "-"

    def _format_quantity(self, quantity: float) -> str:
        """수량 포맷팅"""
        if quantity == 0:
            return "-"

        try:
            if quantity >= 1000000:
                return f"{quantity/1000000:.1f}M"
            elif quantity >= 1000:
                return f"{quantity/1000:.1f}K"
            elif quantity >= 1:
                return f"{quantity:.2f}"
            else:
                return f"{quantity:.4f}"
        except (ValueError, TypeError):
            return "-"

    def get_table_row_type(self, row_index: int) -> str:
        """테이블 행 타입 반환 (매도/매수 구분)"""
        if row_index < 30:
            return "ask"  # 매도
        else:
            return "bid"  # 매수

    def validate_orderbook_data(self, data: Dict[str, Any]) -> bool:
        """호가창 데이터 유효성 검증"""
        if not isinstance(data, dict):
            return False

        required_fields = ["symbol", "asks", "bids"]
        for field in required_fields:
            if field not in data:
                return False

        asks = data["asks"]
        bids = data["bids"]

        if not isinstance(asks, list) or not isinstance(bids, list):
            return False

        # 기본적인 데이터 구조 확인
        for ask in asks[:3]:  # 샘플 확인
            if not all(key in ask for key in ["price", "quantity"]):
                return False

        for bid in bids[:3]:  # 샘플 확인
            if not all(key in bid for key in ["price", "quantity"]):
                return False

        return True
