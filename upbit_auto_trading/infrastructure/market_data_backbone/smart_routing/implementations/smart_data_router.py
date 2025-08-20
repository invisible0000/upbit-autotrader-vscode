"""
Smart Data Router 구현

완전 추상화된 자율적 데이터 라우터입니다.
내부 빈도 분석으로 REST ↔ WebSocket 자동 전환하고,
업비트 API 제한을 준수합니다.
"""

import asyncio
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime, timedelta
import logging

from ..interfaces.data_router import IDataRouter, IChannelSelector, IFrequencyAnalyzer
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
    RoutingStatsResponse,
    HealthCheckResponse,
    RequestFactory,
    ResponseFactory
)
from ..utils.exceptions import (
    DataRangeExceedsLimitException,
    InvalidRequestException,
    SymbolNotSupportedException,
    DataRouterException
)


class SmartDataRouter(IDataRouter):
    """자율적 Smart Data Router

    주요 특징:
    1. 내부 빈도 분석으로 REST ↔ WebSocket 자동 전환
    2. 업비트 API 제한(200개) 준수
    3. 완전한 도메인 모델 기반
    4. 자율적 최적화 (외부 간섭 없음)
    """

    def __init__(
        self,
        rest_provider: IDataProvider,
        websocket_provider: Optional[IDataProvider] = None,
        channel_selector: Optional[IChannelSelector] = None,
        frequency_analyzer: Optional[IFrequencyAnalyzer] = None
    ):
        self.rest_provider = rest_provider
        self.websocket_provider = websocket_provider
        self.channel_selector = channel_selector or BasicChannelSelector()
        self.frequency_analyzer = frequency_analyzer or BasicFrequencyAnalyzer()

        # 통계 추적
        self.stats = {
            "total_requests": 0,
            "websocket_requests": 0,
            "rest_requests": 0,
            "error_count": 0,
            "response_times": []
        }

        self.logger = logging.getLogger(self.__class__.__name__)

        # 실시간 구독 관리 (기본 구현)
        self.subscriptions: Dict[str, Dict[str, Any]] = {}

    async def get_candle_data(
        self,
        symbol: TradingSymbol,
        timeframe: Timeframe,
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> CandleDataResponse:
        """캔들 데이터 조회 (API 제한 준수)"""
        start_time_req = datetime.now()

        try:
            # 요청 검증 및 변환
            request = self._create_candle_request(
                symbol, timeframe, count, start_time, end_time
            )

            # 자율적 채널 선택
            use_websocket = self._should_use_websocket_for_candles(
                symbol, timeframe, request
            )

            # 요청 패턴 업데이트
            self.frequency_analyzer.update_request_pattern(
                symbol, "candle", start_time_req
            )

            # 데이터 조회
            if use_websocket and self.websocket_provider:
                response = await self._get_candle_data_via_websocket(request)
                self.stats["websocket_requests"] += 1
            else:
                response = await self._get_candle_data_via_rest(request)
                self.stats["rest_requests"] += 1

            # 통계 업데이트
            self._update_stats(start_time_req)

            return response

        except Exception as e:
            self.stats["error_count"] += 1
            self.logger.error(f"캔들 데이터 조회 실패: {e}")

            if isinstance(e, (DataRangeExceedsLimitException, InvalidRequestException)):
                raise

            raise DataRouterException(f"캔들 데이터 조회 중 오류: {str(e)}")

    async def get_ticker_data(self, symbol: TradingSymbol) -> TickerDataResponse:
        """티커 데이터 조회 (자율적 채널 선택)"""
        start_time_req = datetime.now()

        try:
            request = RequestFactory.current_ticker(symbol)

            # 자율적 채널 선택
            recent_requests = self.frequency_analyzer.analyze_request_frequency(
                symbol, "ticker", time_window_minutes=5
            )

            use_websocket = self.channel_selector.should_use_websocket(
                symbol, "ticker", int(recent_requests)
            )

            # 요청 패턴 업데이트
            self.frequency_analyzer.update_request_pattern(
                symbol, "ticker", start_time_req
            )

            # 데이터 조회
            if use_websocket and self.websocket_provider:
                response = await self._get_ticker_data_via_websocket(request)
                self.stats["websocket_requests"] += 1
            else:
                response = await self.rest_provider.get_ticker_data(request)
                self.stats["rest_requests"] += 1

            # 통계 업데이트
            self._update_stats(start_time_req)

            return response

        except Exception as e:
            self.stats["error_count"] += 1
            self.logger.error(f"티커 데이터 조회 실패: {e}")
            raise DataRouterException(f"티커 데이터 조회 중 오류: {str(e)}")

    async def get_orderbook_data(
        self,
        symbol: TradingSymbol,
        depth: int = 10
    ) -> OrderbookDataResponse:
        """호가창 데이터 조회"""
        start_time_req = datetime.now()

        try:
            request = RequestFactory.full_orderbook(symbol, depth)

            # 호가창은 일반적으로 REST API 사용 (빈번한 변경으로 WebSocket 비효율적)
            response = await self.rest_provider.get_orderbook_data(request)
            self.stats["rest_requests"] += 1

            # 요청 패턴 업데이트
            self.frequency_analyzer.update_request_pattern(
                symbol, "orderbook", start_time_req
            )

            # 통계 업데이트
            self._update_stats(start_time_req)

            return response

        except Exception as e:
            self.stats["error_count"] += 1
            self.logger.error(f"호가창 데이터 조회 실패: {e}")
            raise DataRouterException(f"호가창 데이터 조회 중 오류: {str(e)}")

    async def get_trade_data(
        self,
        symbol: TradingSymbol,
        count: int = 100,
        cursor: Optional[str] = None
    ) -> TradeDataResponse:
        """체결 데이터 조회"""
        start_time_req = datetime.now()

        try:
            request = RequestFactory.recent_trades(symbol, count)
            if cursor:
                # cursor 지원을 위해 request 수정 필요
                pass

            # 체결 데이터는 일반적으로 REST API 사용
            response = await self.rest_provider.get_trade_data(request)
            self.stats["rest_requests"] += 1

            # 요청 패턴 업데이트
            self.frequency_analyzer.update_request_pattern(
                symbol, "trade", start_time_req
            )

            # 통계 업데이트
            self._update_stats(start_time_req)

            return response

        except Exception as e:
            self.stats["error_count"] += 1
            self.logger.error(f"체결 데이터 조회 실패: {e}")
            raise DataRouterException(f"체결 데이터 조회 중 오류: {str(e)}")

    async def subscribe_realtime(
        self,
        symbol: TradingSymbol,
        data_types: List[str],
        callback: Callable[[Dict[str, Any]], None]
    ) -> str:
        """실시간 데이터 구독 (기본 구현)

        Note: Layer 1에서는 기본 구현만 제공
        실제 실시간 처리는 상위 Layer에서 구현 권장
        """
        if not self.websocket_provider:
            raise DataRouterException("WebSocket 제공자가 설정되지 않았습니다")

        # 기본적인 구독 관리
        subscription_id = f"{symbol}_{datetime.now().timestamp()}"

        self.subscriptions[subscription_id] = {
            "symbol": symbol,
            "data_types": data_types,
            "callback": callback,
            "created_at": datetime.now()
        }

        self.logger.info(f"실시간 구독 등록: {subscription_id}")

        return subscription_id

    async def unsubscribe_realtime(self, subscription_id: str) -> bool:
        """실시간 데이터 구독 해제"""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            self.logger.info(f"실시간 구독 해제: {subscription_id}")
            return True
        return False

    async def get_market_list(self) -> List[TradingSymbol]:
        """지원하는 마켓 목록 조회"""
        try:
            return await self.rest_provider.get_market_list()
        except Exception as e:
            self.logger.error(f"마켓 목록 조회 실패: {e}")
            raise DataRouterException(f"마켓 목록 조회 중 오류: {str(e)}")

    async def get_routing_stats(self) -> RoutingStatsResponse:
        """라우팅 통계 정보"""
        total_requests = self.stats["total_requests"]
        avg_response_time = 0.0

        if self.stats["response_times"]:
            avg_response_time = sum(self.stats["response_times"]) / len(self.stats["response_times"])

        error_rate = 0.0
        if total_requests > 0:
            error_rate = self.stats["error_count"] / total_requests

        return RoutingStatsResponse(
            total_requests=total_requests,
            websocket_requests=self.stats["websocket_requests"],
            rest_requests=self.stats["rest_requests"],
            avg_response_time_ms=avg_response_time,
            error_rate=error_rate,
            cache_hit_rate=0.0,  # 캐시 미구현
            metadata=ResponseFactory.create_metadata(
                request_time=datetime.now(),
                data_source="stats"
            )
        )

    async def health_check(self) -> HealthCheckResponse:
        """라우터 상태 확인"""
        try:
            # REST 제공자 상태 확인
            rest_health = await self.rest_provider.health_check()
            rest_available = rest_health.get("status") == "healthy"

            # WebSocket 제공자 상태 확인
            websocket_connected = False
            if self.websocket_provider:
                try:
                    ws_health = await self.websocket_provider.health_check()
                    websocket_connected = ws_health.get("status") == "healthy"
                except:
                    websocket_connected = False

            # 전체 상태 결정
            if rest_available:
                status = "healthy" if websocket_connected else "degraded"
            else:
                status = "unhealthy"

            return HealthCheckResponse(
                status=status,
                websocket_connected=websocket_connected,
                rest_api_available=rest_available,
                last_check=datetime.now(),
                metadata=ResponseFactory.create_metadata(
                    request_time=datetime.now(),
                    data_source="health_check"
                ),
                details={
                    "rest_provider": rest_health,
                    "total_subscriptions": len(self.subscriptions)
                }
            )

        except Exception as e:
            self.logger.error(f"상태 확인 실패: {e}")
            return HealthCheckResponse(
                status="unhealthy",
                websocket_connected=False,
                rest_api_available=False,
                last_check=datetime.now(),
                metadata=ResponseFactory.create_metadata(
                    request_time=datetime.now(),
                    data_source="health_check"
                ),
                details={"error": str(e)}
            )

    def _create_candle_request(
        self,
        symbol: TradingSymbol,
        timeframe: Timeframe,
        count: Optional[int],
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> CandleDataRequest:
        """캔들 요청 생성 및 검증"""

        # API 제한 검증
        effective_count = count if count is not None else 200

        if start_time and end_time:
            # 시간 범위가 주어진 경우 예상 개수 계산
            time_diff = end_time - start_time
            timeframe_minutes = timeframe.to_minutes()
            estimated_count = int(time_diff.total_seconds() / (timeframe_minutes * 60))

            if estimated_count > 200:
                raise DataRangeExceedsLimitException(
                    f"요청 범위 초과: 예상 {estimated_count}개 > 최대 200개. "
                    f"Coordinator에서 분할 요청 필요",
                    requested_count=estimated_count
                )

        return CandleDataRequest(
            symbol=symbol,
            timeframe=timeframe,
            count=effective_count,
            start_time=start_time,
            end_time=end_time
        )

    def _should_use_websocket_for_candles(
        self,
        symbol: TradingSymbol,
        timeframe: Timeframe,
        request: CandleDataRequest
    ) -> bool:
        """캔들 데이터에 대한 WebSocket 사용 여부 결정"""

        # 캔들 데이터는 일반적으로 REST API가 더 효율적
        # 실시간 업데이트가 아닌 이상 WebSocket 불필요
        if request.has_time_range:
            return False  # 과거 데이터는 REST API

        # 최신 데이터이고 고빈도 요청인 경우만 WebSocket 고려
        recent_requests = self.frequency_analyzer.analyze_request_frequency(
            symbol, "candle", time_window_minutes=5
        )

        return self.channel_selector.should_use_websocket(
            symbol, "candle", int(recent_requests)
        )

    async def _get_candle_data_via_rest(
        self,
        request: CandleDataRequest
    ) -> CandleDataResponse:
        """REST API를 통한 캔들 데이터 조회"""
        return await self.rest_provider.get_candle_data(request)

    async def _get_candle_data_via_websocket(
        self,
        request: CandleDataRequest
    ) -> CandleDataResponse:
        """WebSocket을 통한 캔들 데이터 조회 (기본 구현)"""
        # WebSocket으로 캔들 데이터를 받는 것은 복잡하므로
        # 일단 REST API로 fallback
        self.logger.warning("WebSocket 캔들 데이터는 미구현, REST API로 fallback")
        return await self._get_candle_data_via_rest(request)

    async def _get_ticker_data_via_websocket(
        self,
        request: TickerDataRequest
    ) -> TickerDataResponse:
        """WebSocket을 통한 티커 데이터 조회"""
        if not self.websocket_provider:
            self.logger.warning("WebSocket Provider가 없음, REST API로 fallback")
            return await self.rest_provider.get_ticker_data(request)

        try:
            # 실제 WebSocket Provider 호출
            response = await self.websocket_provider.get_ticker_data(request)
            self.logger.debug(f"WebSocket 티커 데이터 수신 성공: {request.symbol}")
            return response
        except Exception as e:
            self.logger.warning(f"WebSocket 티커 데이터 실패, REST로 fallback: {e}")
            return await self.rest_provider.get_ticker_data(request)

    def _update_stats(self, start_time: datetime) -> None:
        """통계 업데이트"""
        self.stats["total_requests"] += 1

        response_time = (datetime.now() - start_time).total_seconds() * 1000
        self.stats["response_times"].append(response_time)

        # 최근 100개 응답 시간만 유지
        if len(self.stats["response_times"]) > 100:
            self.stats["response_times"] = self.stats["response_times"][-100:]


class BasicChannelSelector(IChannelSelector):
    """기본 채널 선택 전략

    WebSocket-First 전략: 구독 관리를 통한 지능형 라우팅
    """

    def should_use_websocket(
        self,
        symbol: TradingSymbol,
        data_type: str,
        recent_request_count: int
    ) -> bool:
        """WebSocket 사용 여부 결정 (WebSocket-First 전략)"""

        # WebSocket 우선 전략: 실시간 데이터는 기본적으로 WebSocket 사용
        if data_type in ["ticker", "orderbook", "trade"]:
            # 즉시 WebSocket 사용 (구독 관리 방식)
            return True

        # 캔들 데이터는 여전히 REST 우선 (과거 데이터가 많음)
        if data_type == "candle":
            # 높은 빈도에서만 WebSocket 사용
            return recent_request_count >= 8

        # 기본: WebSocket 사용
        return True

    def update_request_pattern(
        self,
        symbol: TradingSymbol,
        data_type: str,
        request_time: datetime
    ) -> None:
        """요청 패턴 업데이트 (BasicFrequencyAnalyzer에 위임)"""
        pass


class BasicFrequencyAnalyzer(IFrequencyAnalyzer):
    """기본 요청 빈도 분석기

    단순한 시간 윈도우 기반 요청 카운팅
    """

    def __init__(self):
        self.request_history: Dict[str, List[datetime]] = {}

    def analyze_request_frequency(
        self,
        symbol: TradingSymbol,
        data_type: str,
        time_window_minutes: int = 5
    ) -> float:
        """요청 빈도 분석"""
        key = f"{symbol}_{data_type}"

        if key not in self.request_history:
            return 0.0

        # 시간 윈도우 내의 요청만 필터링
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        recent_requests = [
            req_time for req_time in self.request_history[key]
            if req_time >= cutoff_time
        ]

        # 분당 요청 횟수 계산
        return len(recent_requests) / time_window_minutes

    def update_request_pattern(
        self,
        symbol: TradingSymbol,
        data_type: str,
        request_time: datetime
    ) -> None:
        """요청 패턴 업데이트"""
        key = f"{symbol}_{data_type}"

        if key not in self.request_history:
            self.request_history[key] = []

        self.request_history[key].append(request_time)

        # 1시간 이전 데이터는 정리
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.request_history[key] = [
            req_time for req_time in self.request_history[key]
            if req_time >= cutoff_time
        ]

    def get_websocket_threshold(self, data_type: str) -> float:
        """WebSocket 전환 임계값"""
        thresholds = {
            "ticker": 1.0,     # 분당 1회 이상
            "orderbook": 2.0,  # 분당 2회 이상
            "trade": 0.6,      # 분당 0.6회 이상
            "candle": 2.0      # 분당 2회 이상
        }

        return thresholds.get(data_type, 1.0)
