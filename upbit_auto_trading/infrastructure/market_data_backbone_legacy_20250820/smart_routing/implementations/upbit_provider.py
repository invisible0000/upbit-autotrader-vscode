"""
업비트 데이터 제공자 구현

이 모듈은 업비트 REST API를 통해 데이터를 제공하는 Provider를 구현합니다.
최소한의 기능으로 시작하여 점진적으로 확장합니다.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import aiohttp

from upbit_auto_trading.infrastructure.logging import create_component_logger
from ..interfaces.data_provider import IDataProvider
from ..models.symbols import TradingSymbol
from ..models.timeframes import Timeframe
from ..utils.exceptions import DataProviderException, RateLimitExceededException

logger = create_component_logger("UpbitDataProvider")


class UpbitDataProvider(IDataProvider):
    """
    업비트 REST API 기반 데이터 제공자

    특징:
    - REST API만 사용 (WebSocket은 추후 확장)
    - 레이트 제한 준수
    - 표준화된 응답 형태로 변환
    - 오류 상황 적절한 처리
    """

    BASE_URL = "https://api.upbit.com"

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_request_time = datetime.now()
        self._request_count = 0

        logger.info("UpbitDataProvider 초기화 완료")

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """HTTP 세션 확보"""
        if self._session is None:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session

    async def _rate_limit_check(self) -> None:
        """레이트 제한 확인 (초당 10요청 제한)"""
        now = datetime.now()
        time_diff = (now - self._last_request_time).total_seconds()

        if time_diff < 0.1:  # 100ms 최소 간격
            await asyncio.sleep(0.1 - time_diff)

        self._last_request_time = datetime.now()
        self._request_count += 1

    async def fetch_candle_data_dict(
        self,
        symbol: TradingSymbol,
        timeframe: Timeframe,
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        캔들 데이터 조회 (Dict 형태 반환)

        시간 파라미터 우선순위:
        1. count가 있으면 count 사용 (최신 N개)
        2. start_time/end_time이 있으면 시간 범위 사용
        3. 둘 다 없으면 기본값 200개
        """
        await self._rate_limit_check()

        # URL 구성
        upbit_timeframe = timeframe.to_upbit_format()
        upbit_symbol = symbol.to_upbit_format()

        url = f"{self.BASE_URL}/v1/candles/{upbit_timeframe}"

        # 파라미터 구성 (우선순위 적용)
        params = {"market": upbit_symbol}

        if count is not None:
            params["count"] = min(count, 200)  # 업비트 최대 200개 제한
        elif start_time and end_time:
            # 시간 범위 사용 시 종료 시간 기준으로 요청
            params["to"] = end_time.strftime("%Y-%m-%dT%H:%M:%S")
            # 시간 범위에서 대략적인 count 계산
            duration_hours = (end_time - start_time).total_seconds() / 3600
            estimated_count = int(duration_hours / (timeframe.minutes / 60))
            params["count"] = min(estimated_count, 200)
        else:
            params["count"] = 200  # 기본값

        logger.debug(f"업비트 API 호출: {url} with {params}")

        try:
            session = await self._ensure_session()
            async with session.get(url, params=params) as response:
                if response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise RateLimitExceededException(
                        "업비트 API 레이트 제한 초과", retry_after
                    )

                if response.status != 200:
                    raise DataProviderException(
                        f"업비트 API 오류: {response.status} - {await response.text()}"
                    )

                raw_data = await response.json()

                # 표준화된 형태로 변환
                return self._convert_candle_response(symbol, timeframe, raw_data)

        except aiohttp.ClientError as e:
            logger.error(f"업비트 API 연결 오류: {e}")
            raise DataProviderException(f"네트워크 오류: {e}")
        except Exception as e:
            logger.error(f"업비트 API 예상치 못한 오류: {e}")
            raise DataProviderException(f"데이터 조회 실패: {e}")

    def _convert_candle_response(
        self,
        symbol: TradingSymbol,
        timeframe: Timeframe,
        raw_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """업비트 API 응답을 표준 형태로 변환"""

        converted_data = []
        for item in raw_data:
            converted_item = {
                "timestamp": item["candle_date_time_kst"],
                "open": str(item["opening_price"]),
                "high": str(item["high_price"]),
                "low": str(item["low_price"]),
                "close": str(item["trade_price"]),
                "volume": str(item["candle_acc_trade_volume"]),
                "quote_volume": str(item["candle_acc_trade_price"])
            }
            converted_data.append(converted_item)

        now = datetime.now()
        return {
            "symbol": str(symbol),
            "timeframe": str(timeframe),
            "data": converted_data,
            "count": len(converted_data),
            "request_timestamp": now.isoformat(),
            "response_timestamp": now.isoformat(),
            "source": "upbit_rest"
        }

    async def fetch_ticker_data_dict(self, symbol: TradingSymbol) -> Dict[str, Any]:
        """티커 데이터 조회 (Dict 형태)"""
        await self._rate_limit_check()

        url = f"{self.BASE_URL}/v1/ticker"
        params = {"markets": symbol.to_upbit_format()}

        try:
            session = await self._ensure_session()
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise DataProviderException(f"티커 조회 실패: {response.status}")

                raw_data = await response.json()
                if not raw_data:
                    raise DataProviderException("티커 데이터 없음")

                item = raw_data[0]  # 첫 번째 항목

                return {
                    "symbol": str(symbol),
                    "price": str(item["trade_price"]),
                    "change": str(item["signed_change_price"]),
                    "change_rate": str(item["signed_change_rate"]),
                    "volume_24h": str(item["acc_trade_volume_24h"]),
                    "quote_volume_24h": str(item["acc_trade_price_24h"]),
                    "high_24h": str(item["high_price"]),
                    "low_24h": str(item["low_price"]),
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"티커 조회 오류: {e}")
            raise DataProviderException(f"티커 조회 실패: {e}")

    async def fetch_orderbook_data_dict(
        self,
        symbol: TradingSymbol,
        depth: int = 10
    ) -> Dict[str, Any]:
        """호가 데이터 조회 (Dict 형태)"""
        await self._rate_limit_check()

        url = f"{self.BASE_URL}/v1/orderbook"
        params = {"markets": symbol.to_upbit_format()}

        try:
            session = await self._ensure_session()
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise DataProviderException(f"호가 조회 실패: {response.status}")

                raw_data = await response.json()
                if not raw_data:
                    raise DataProviderException("호가 데이터 없음")

                item = raw_data[0]
                orderbook_units = item["orderbook_units"]

                # depth만큼 제한
                bids = []
                asks = []

                for unit in orderbook_units[:depth]:
                    bids.append({
                        "price": str(unit["bid_price"]),
                        "size": str(unit["bid_size"])
                    })
                    asks.append({
                        "price": str(unit["ask_price"]),
                        "size": str(unit["ask_size"])
                    })

                return {
                    "symbol": str(symbol),
                    "bids": bids,
                    "asks": asks,
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"호가 조회 오류: {e}")
            raise DataProviderException(f"호가 조회 실패: {e}")

    async def fetch_trade_history_dict(
        self,
        symbol: TradingSymbol,
        count: Optional[int] = None,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """거래 내역 조회 (Dict 형태)"""
        await self._rate_limit_check()

        url = f"{self.BASE_URL}/v1/trades/ticks"
        params = {
            "market": symbol.to_upbit_format(),
            "count": count or 100
        }

        if cursor:
            params["cursor"] = cursor

        try:
            session = await self._ensure_session()
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise DataProviderException(f"거래내역 조회 실패: {response.status}")

                raw_data = await response.json()

                trades = []
                for item in raw_data:
                    trades.append({
                        "timestamp": item["trade_date_utc"] + "T" + item["trade_time_utc"],
                        "price": str(item["trade_price"]),
                        "size": str(item["trade_volume"]),
                        "side": "sell" if item["ask_bid"] == "ASK" else "buy",
                        "trade_id": str(item["sequential_id"])
                    })

                return {
                    "symbol": str(symbol),
                    "trades": trades,
                    "count": len(trades),
                    "next_cursor": None,  # 업비트는 cursor 반환 안함
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"거래내역 조회 오류: {e}")
            raise DataProviderException(f"거래내역 조회 실패: {e}")

    async def fetch_market_list(self) -> List[TradingSymbol]:
        """마켓 목록 조회"""
        await self._rate_limit_check()

        url = f"{self.BASE_URL}/v1/market/all"

        try:
            session = await self._ensure_session()
            async with session.get(url) as response:
                if response.status != 200:
                    raise DataProviderException(f"마켓 목록 조회 실패: {response.status}")

                raw_data = await response.json()
                markets = []

                for item in raw_data:
                    if item["market_warning"] == "NONE":  # 정상 거래만
                        symbol = TradingSymbol.from_upbit_format(item["market"])
                        markets.append(symbol)

                return markets

        except Exception as e:
            logger.error(f"마켓 목록 조회 오류: {e}")
            raise DataProviderException(f"마켓 목록 조회 실패: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """헬스 체크"""
        try:
            # 서버 시간 조회로 연결 상태 확인
            url = f"{self.BASE_URL}/v1/server-time"
            session = await self._ensure_session()

            async with session.get(url) as response:
                if response.status == 200:
                    return {
                        "status": "healthy",
                        "api_available": True,
                        "request_count": self._request_count,
                        "last_check": datetime.now().isoformat()
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "api_available": False,
                        "error": f"HTTP {response.status}",
                        "last_check": datetime.now().isoformat()
                    }
        except Exception as e:
            return {
                "status": "unhealthy",
                "api_available": False,
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }

    async def close(self) -> None:
        """리소스 정리"""
        if self._session:
            await self._session.close()
            self._session = None

        logger.info("UpbitDataProvider 리소스 정리 완료")
