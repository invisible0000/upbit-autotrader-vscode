"""
업비트 REST API 데이터 제공자

업비트 REST API에 특화된 저수준 데이터 제공자입니다.
Smart Router가 내부적으로 사용합니다.
"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from decimal import Decimal
import logging

from ..interfaces.data_provider import IDataProvider
from ..models import (
    TradingSymbol,
    Timeframe,
    CandleDataRequest,
    TickerDataRequest,
    OrderbookDataRequest,
    TradeDataRequest,
    CandleDataResponse,
    TickerDataResponse,
    OrderbookDataResponse,
    TradeDataResponse,
    CandleData,
    TickerData,
    OrderbookData,
    OrderbookLevel,
    TradeData,
    ResponseFactory
)
from ..utils.exceptions import (
    RestApiException,
    SymbolNotSupportedException,
    TimeframeNotSupportedException,
    ApiRateLimitException,
    DataValidationException,
    ErrorConverter
)


class UpbitRestProvider(IDataProvider):
    """업비트 REST API 제공자

    업비트 REST API를 통해 데이터를 조회합니다.
    도메인 모델을 업비트 API 형태로 변환하고,
    응답을 다시 도메인 모델로 변환합니다.
    """

    def __init__(
        self,
        base_url: str = "https://api.upbit.com",
        timeout_seconds: float = 10.0,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self.max_retries = max_retries
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(self.__class__.__name__)

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.close()

    async def _ensure_session(self) -> None:
        """HTTP 세션 확보"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)

    async def close(self) -> None:
        """리소스 정리"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_candle_data(self, request: CandleDataRequest) -> CandleDataResponse:
        """캔들 데이터 조회"""
        request_time = datetime.now()

        try:
            # 도메인 모델을 업비트 API 파라미터로 변환
            url = self._build_candle_url(request.symbol, request.timeframe)
            params = self._build_candle_params(request)

            # API 호출
            raw_data = await self._make_request("GET", url, params=params)

            # 응답을 도메인 모델로 변환
            candle_data_list = self._convert_candle_response(raw_data)

            return ResponseFactory.candle_response(
                symbol=request.symbol,
                timeframe=request.timeframe,
                data=candle_data_list,
                request_time=request_time,
                data_source="rest"
            )

        except Exception as e:
            self.logger.error(f"캔들 데이터 조회 실패: {e}")
            if isinstance(e, (RestApiException, SymbolNotSupportedException)):
                raise
            raise RestApiException(f"캔들 데이터 조회 중 오류: {str(e)}")

    async def get_ticker_data(self, request: TickerDataRequest) -> TickerDataResponse:
        """티커 데이터 조회"""
        request_time = datetime.now()

        try:
            url = f"{self.base_url}/v1/ticker"
            params = {"markets": request.symbol.to_upbit_symbol()}

            raw_data = await self._make_request("GET", url, params=params)

            if not raw_data or len(raw_data) == 0:
                raise DataValidationException(
                    f"티커 데이터가 없습니다: {request.symbol}"
                )

            ticker_data = self._convert_ticker_response(raw_data[0])

            return ResponseFactory.ticker_response(
                symbol=request.symbol,
                data=ticker_data,
                request_time=request_time,
                data_source="rest"
            )

        except Exception as e:
            self.logger.error(f"티커 데이터 조회 실패: {e}")
            if isinstance(e, (RestApiException, SymbolNotSupportedException)):
                raise
            raise RestApiException(f"티커 데이터 조회 중 오류: {str(e)}")

    async def get_orderbook_data(self, request: OrderbookDataRequest) -> OrderbookDataResponse:
        """호가창 데이터 조회"""
        request_time = datetime.now()

        try:
            url = f"{self.base_url}/v1/orderbook"
            params = {"markets": request.symbol.to_upbit_symbol()}

            raw_data = await self._make_request("GET", url, params=params)

            if not raw_data or len(raw_data) == 0:
                raise DataValidationException(
                    f"호가창 데이터가 없습니다: {request.symbol}"
                )

            orderbook_data = self._convert_orderbook_response(raw_data[0], request.depth)

            return OrderbookDataResponse(
                symbol=request.symbol,
                data=orderbook_data,
                metadata=ResponseFactory.create_metadata(
                    request_time=request_time,
                    data_source="rest"
                )
            )

        except Exception as e:
            self.logger.error(f"호가창 데이터 조회 실패: {e}")
            if isinstance(e, (RestApiException, SymbolNotSupportedException)):
                raise
            raise RestApiException(f"호가창 데이터 조회 중 오류: {str(e)}")

    async def get_trade_data(self, request: TradeDataRequest) -> TradeDataResponse:
        """체결 데이터 조회"""
        request_time = datetime.now()

        try:
            url = f"{self.base_url}/v1/trades/ticks"
            params = {
                "market": request.symbol.to_upbit_symbol(),
                "count": request.count
            }

            if request.cursor:
                params["cursor"] = request.cursor

            raw_data = await self._make_request("GET", url, params=params)

            trade_data_list = self._convert_trade_response(raw_data)

            return TradeDataResponse(
                symbol=request.symbol,
                data=trade_data_list,
                metadata=ResponseFactory.create_metadata(
                    request_time=request_time,
                    data_source="rest"
                ),
                next_cursor=None  # 업비트 API 응답에서 추출 필요
            )

        except Exception as e:
            self.logger.error(f"체결 데이터 조회 실패: {e}")
            if isinstance(e, (RestApiException, SymbolNotSupportedException)):
                raise
            raise RestApiException(f"체결 데이터 조회 중 오류: {str(e)}")

    async def get_market_list(self) -> List[TradingSymbol]:
        """지원하는 마켓 목록 조회"""
        try:
            url = f"{self.base_url}/v1/market/all"
            raw_data = await self._make_request("GET", url)

            symbols = []
            for market_info in raw_data:
                if market_info.get("warning") != "NONE":
                    continue  # 경고가 있는 마켓은 제외

                market_id = market_info.get("market", "")
                try:
                    symbol = TradingSymbol.from_upbit_symbol(market_id)
                    symbols.append(symbol)
                except ValueError:
                    self.logger.warning(f"올바르지 않은 마켓 ID: {market_id}")
                    continue

            return symbols

        except Exception as e:
            self.logger.error(f"마켓 목록 조회 실패: {e}")
            raise RestApiException(f"마켓 목록 조회 중 오류: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        """제공자 상태 확인"""
        try:
            # 간단한 API 호출로 상태 확인
            url = f"{self.base_url}/v1/market/all"
            await self._make_request("GET", url)

            return {
                "status": "healthy",
                "provider": "upbit_rest",
                "base_url": self.base_url,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "upbit_rest",
                "base_url": self.base_url,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _build_candle_url(self, symbol: TradingSymbol, timeframe: Timeframe) -> str:
        """캔들 API URL 생성"""
        return f"{self.base_url}{timeframe.to_upbit_url_path()}"

    def _build_candle_params(self, request: CandleDataRequest) -> Dict[str, Any]:
        """캔들 API 파라미터 생성"""
        params = {
            "market": request.symbol.to_upbit_symbol(),
            "count": request.effective_count
        }

        # 시간 범위 처리
        if request.end_time:
            # ISO 8601 형태로 변환 (업비트 API 형식)
            params["to"] = request.end_time.strftime("%Y-%m-%dT%H:%M:%S")

        return params

    def _convert_candle_response(self, raw_data: List[Dict[str, Any]]) -> List[CandleData]:
        """업비트 캔들 응답을 도메인 모델로 변환"""
        candle_data_list = []

        for item in raw_data:
            try:
                # 업비트 시간 포맷 파싱
                timestamp_str = item.get("candle_date_time_kst", "")
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

                candle_data = CandleData(
                    timestamp=timestamp,
                    open_price=Decimal(str(item.get("opening_price", 0))),
                    high_price=Decimal(str(item.get("high_price", 0))),
                    low_price=Decimal(str(item.get("low_price", 0))),
                    close_price=Decimal(str(item.get("trade_price", 0))),
                    volume=Decimal(str(item.get("candle_acc_trade_volume", 0)))
                )

                candle_data_list.append(candle_data)

            except (ValueError, TypeError, KeyError) as e:
                self.logger.warning(f"캔들 데이터 변환 실패: {e}, 데이터: {item}")
                continue

        # 시간순 정렬 (오래된 것부터)
        candle_data_list.sort(key=lambda x: x.timestamp)

        return candle_data_list

    def _convert_ticker_response(self, raw_data: Dict[str, Any]) -> TickerData:
        """업비트 티커 응답을 도메인 모델로 변환"""
        try:
            timestamp = datetime.now(timezone.utc)

            return TickerData(
                timestamp=timestamp,
                current_price=Decimal(str(raw_data.get("trade_price", 0))),
                change_amount=Decimal(str(raw_data.get("change_price", 0))),
                change_rate=Decimal(str(raw_data.get("change_rate", 0))),
                volume_24h=Decimal(str(raw_data.get("acc_trade_volume_24h", 0))),
                high_24h=Decimal(str(raw_data.get("high_price", 0))),
                low_24h=Decimal(str(raw_data.get("low_price", 0))),
                opening_price=Decimal(str(raw_data.get("opening_price", 0)))
            )

        except (ValueError, TypeError, KeyError) as e:
            raise DataValidationException(
                f"티커 데이터 변환 실패: {e}",
                field_name="ticker_data",
                field_value=raw_data
            )

    def _convert_orderbook_response(
        self,
        raw_data: Dict[str, Any],
        depth: int
    ) -> OrderbookData:
        """업비트 호가창 응답을 도메인 모델로 변환"""
        try:
            timestamp = datetime.now(timezone.utc)

            # 매수 호가 (bids)
            bids = []
            bid_units = raw_data.get("orderbook_units", [])[:depth]
            for unit in bid_units:
                if unit.get("bid_price", 0) > 0:
                    bids.append(OrderbookLevel(
                        price=Decimal(str(unit["bid_price"])),
                        size=Decimal(str(unit["bid_size"]))
                    ))

            # 매도 호가 (asks)
            asks = []
            for unit in bid_units:
                if unit.get("ask_price", 0) > 0:
                    asks.append(OrderbookLevel(
                        price=Decimal(str(unit["ask_price"])),
                        size=Decimal(str(unit["ask_size"]))
                    ))

            # 가격순 정렬
            bids.sort(key=lambda x: x.price, reverse=True)  # 높은 가격 순
            asks.sort(key=lambda x: x.price)  # 낮은 가격 순

            return OrderbookData(
                timestamp=timestamp,
                bids=bids,
                asks=asks
            )

        except (ValueError, TypeError, KeyError) as e:
            raise DataValidationException(
                f"호가창 데이터 변환 실패: {e}",
                field_name="orderbook_data",
                field_value=raw_data
            )

    def _convert_trade_response(self, raw_data: List[Dict[str, Any]]) -> List[TradeData]:
        """업비트 체결 응답을 도메인 모델로 변환"""
        trade_data_list = []

        for item in raw_data:
            try:
                # 업비트 시간 포맷 파싱
                timestamp_str = item.get("trade_date_utc", "") + "T" + item.get("trade_time_utc", "")
                timestamp = datetime.fromisoformat(timestamp_str + "+00:00")

                # 체결 방향 변환
                ask_bid = item.get("ask_bid", "")
                side = "sell" if ask_bid == "ASK" else "buy"

                trade_data = TradeData(
                    timestamp=timestamp,
                    price=Decimal(str(item.get("trade_price", 0))),
                    size=Decimal(str(item.get("trade_volume", 0))),
                    side=side,
                    trade_id=str(item.get("sequential_id", ""))
                )

                trade_data_list.append(trade_data)

            except (ValueError, TypeError, KeyError) as e:
                self.logger.warning(f"체결 데이터 변환 실패: {e}, 데이터: {item}")
                continue

        # 시간순 정렬 (최신 것부터)
        trade_data_list.sort(key=lambda x: x.timestamp, reverse=True)

        return trade_data_list

    async def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Any:
        """HTTP 요청 실행 (재시도 로직 포함)"""
        await self._ensure_session()

        for attempt in range(self.max_retries + 1):
            try:
                async with self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data
                ) as response:

                    # HTTP 상태 코드 확인
                    if response.status == 429:
                        raise ApiRateLimitException(
                            "API 요청 제한에 도달했습니다",
                            retry_after_seconds=60
                        )

                    if response.status >= 400:
                        response_text = await response.text()
                        raise ErrorConverter.from_http_error(response.status, response_text)

                    return await response.json()

            except asyncio.TimeoutError:
                if attempt == self.max_retries:
                    raise RestApiException("요청 시간 초과")
                await asyncio.sleep(2 ** attempt)  # 지수 백오프

            except aiohttp.ClientError as e:
                if attempt == self.max_retries:
                    raise RestApiException(f"네트워크 오류: {str(e)}")
                await asyncio.sleep(2 ** attempt)

        raise RestApiException("최대 재시도 횟수 초과")
