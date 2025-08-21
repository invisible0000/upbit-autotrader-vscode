"""
업비트 퍼블릭 채널 통합 관리자

REST API + WebSocket을 하나의 인터페이스로 통합:
- 실시간 데이터: WebSocket (ticker, trade, orderbook, candle)
- 기초 데이터: REST API (markets, candles history)
- 자동 채널 선택: 요청 타입에 따른 최적 채널 라우팅
- 통합 에러 처리: 모든 채널의 에러를 일관된 방식으로 처리
- 레이트 제한 통합: 스마트 라우터의 통합 레이트 리미터 사용
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import UpbitWebSocketQuotationClient
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.channels.websocket.message_parser import (
    UpbitMessageParser, ParsedMessage, UpbitMessageType
)
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.strategies.rate_limit_mapper import (
    IntegratedRateLimiter, RateLimitType
)
from upbit_auto_trading.infrastructure.logging import create_component_logger


class DataRequestType(Enum):
    """데이터 요청 타입"""
    # 실시간 데이터 (WebSocket 우선)
    REALTIME_TICKER = "realtime_ticker"
    REALTIME_TRADE = "realtime_trade"
    REALTIME_ORDERBOOK = "realtime_orderbook"
    REALTIME_CANDLE = "realtime_candle"

    # 기초/과거 데이터 (REST API)
    MARKETS_LIST = "markets_list"
    CANDLES_HISTORY = "candles_history"
    TICKER_SNAPSHOT = "ticker_snapshot"
    ORDERBOOK_SNAPSHOT = "orderbook_snapshot"
    TRADE_HISTORY = "trade_history"


@dataclass
class ChannelStatus:
    """채널 상태 정보"""
    is_connected: bool
    last_activity: datetime
    message_count: int
    error_count: int
    rps: float


@dataclass
class DataRequest:
    """데이터 요청 구조"""
    request_type: DataRequestType
    markets: List[str]
    params: Dict[str, Any]
    callback: Optional[Callable[[ParsedMessage], None]] = None


class UpbitPublicChannelManager:
    """업비트 퍼블릭 채널 통합 관리자"""

    def __init__(self):
        self.logger = create_component_logger("UpbitPublicChannelManager")

        # 채널 클라이언트들
        self.rest_client = UpbitPublicClient()
        self.websocket_client = UpbitWebSocketQuotationClient()
        self.message_parser = UpbitMessageParser()

        # 🔧 통합 레이트 리미터 초기화
        try:
            self.rate_limiter = IntegratedRateLimiter()
            self.logger.debug("✅ 통합 레이트 리미터 초기화 완료")
        except Exception as e:
            self.logger.warning(f"레이트 리미터 초기화 실패, 기본 제한 사용: {e}")
            self.rate_limiter = None

        # 채널 상태 추적
        self.websocket_status = ChannelStatus(
            is_connected=False,
            last_activity=datetime.now(),
            message_count=0,
            error_count=0,
            rps=0.0
        )

        # 활성 구독 관리
        self.active_subscriptions: Dict[str, List[str]] = {}  # type -> markets
        self.message_handlers: Dict[UpbitMessageType, List[Callable]] = {}

        # 성능 모니터링
        self.performance_stats = {
            'rest_requests': 0,
            'websocket_messages': 0,
            'errors': 0,
            'start_time': datetime.now()
        }

    async def initialize(self) -> bool:
        """채널 관리자 초기화"""
        try:
            self.logger.info("퍼블릭 채널 관리자 초기화 시작")

            # WebSocket 연결
            websocket_success = await self.websocket_client.connect()
            if websocket_success:
                self.websocket_status.is_connected = True
                self.logger.info("✅ WebSocket 채널 초기화 완료")

                # 통합 메시지 핸들러 등록
                await self._setup_unified_message_handler()
            else:
                self.logger.error("❌ WebSocket 채널 초기화 실패")

            # REST 클라이언트는 즉시 사용 가능
            self.logger.info("✅ REST 채널 초기화 완료")

            return websocket_success

        except Exception as e:
            self.logger.error(f"채널 관리자 초기화 오류: {e}")
            return False

    async def _setup_unified_message_handler(self):
        """통합 메시지 핸들러 설정"""

        def unified_handler(ws_message):
            """모든 WebSocket 메시지를 통합 처리"""
            try:
                # 성능 통계 업데이트
                self.performance_stats['websocket_messages'] += 1
                self.websocket_status.message_count += 1
                self.websocket_status.last_activity = datetime.now()

                # 통합 파서로 파싱
                raw_data = getattr(ws_message, 'raw_data', '')
                parsed = self.message_parser.parse_message(raw_data)

                if parsed:
                    # 타입별 핸들러 실행
                    handlers = self.message_handlers.get(parsed.type, [])
                    for handler in handlers:
                        try:
                            handler(parsed)
                        except Exception as e:
                            self.logger.error(f"메시지 핸들러 실행 오류: {e}")
                            self.performance_stats['errors'] += 1
                else:
                    self.logger.debug("메시지 파싱 실패")

            except Exception as e:
                self.logger.error(f"통합 메시지 핸들러 오류: {e}")
                self.websocket_status.error_count += 1
                self.performance_stats['errors'] += 1

        # 모든 WebSocket 타입에 통합 핸들러 등록
        from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import WebSocketDataType

        self.websocket_client.add_message_handler(WebSocketDataType.TICKER, unified_handler)
        self.websocket_client.add_message_handler(WebSocketDataType.TRADE, unified_handler)
        self.websocket_client.add_message_handler(WebSocketDataType.ORDERBOOK, unified_handler)

        self.logger.debug("통합 메시지 핸들러 설정 완료")

    def add_message_handler(self, message_type: UpbitMessageType,
                           handler: Callable[[ParsedMessage], None]):
        """메시지 타입별 핸들러 등록"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
        self.logger.debug(f"메시지 핸들러 등록: {message_type.value}")

    async def request_data(self, request: DataRequest) -> Optional[Any]:
        """데이터 요청 (자동 채널 선택)"""

        try:
            # 요청 타입에 따른 자동 라우팅
            if self._is_realtime_request(request.request_type):
                return await self._handle_realtime_request(request)
            else:
                return await self._handle_rest_request(request)

        except Exception as e:
            self.logger.error(f"데이터 요청 처리 오류: {e}")
            self.performance_stats['errors'] += 1
            return None

    def _is_realtime_request(self, request_type: DataRequestType) -> bool:
        """실시간 요청인지 판별"""
        realtime_types = [
            DataRequestType.REALTIME_TICKER,
            DataRequestType.REALTIME_TRADE,
            DataRequestType.REALTIME_ORDERBOOK,
            DataRequestType.REALTIME_CANDLE
        ]
        return request_type in realtime_types

    async def _handle_realtime_request(self, request: DataRequest) -> bool:
        """실시간 요청 처리 (WebSocket)"""

        if not self.websocket_status.is_connected:
            self.logger.error("WebSocket이 연결되지 않음")
            return False

        # 콜백 핸들러 등록 (요청에 포함된 경우)
        if request.callback:
            message_type = self._map_request_to_message_type(request.request_type)
            if message_type:
                self.add_message_handler(message_type, request.callback)

        # WebSocket 구독
        success = False
        if request.request_type == DataRequestType.REALTIME_TICKER:
            success = await self.websocket_client.subscribe_ticker(request.markets)
        elif request.request_type == DataRequestType.REALTIME_TRADE:
            success = await self.websocket_client.subscribe_trade(request.markets)
        elif request.request_type == DataRequestType.REALTIME_ORDERBOOK:
            success = await self.websocket_client.subscribe_orderbook(request.markets)

        if success:
            # 구독 정보 저장
            request_key = request.request_type.value
            if request_key not in self.active_subscriptions:
                self.active_subscriptions[request_key] = []
            self.active_subscriptions[request_key].extend(request.markets)

            self.logger.info(f"✅ 실시간 구독 성공: {request.request_type.value} - {request.markets}")

        return success

    def _map_request_to_message_type(self, request_type: DataRequestType) -> Optional[UpbitMessageType]:
        """요청 타입을 메시지 타입으로 매핑"""
        mapping = {
            DataRequestType.REALTIME_TICKER: UpbitMessageType.TICKER,
            DataRequestType.REALTIME_TRADE: UpbitMessageType.TRADE,
            DataRequestType.REALTIME_ORDERBOOK: UpbitMessageType.ORDERBOOK,
            DataRequestType.REALTIME_CANDLE: UpbitMessageType.CANDLE
        }
        return mapping.get(request_type)

    async def _handle_rest_request(self, request: DataRequest) -> Optional[Any]:
        """REST 요청 처리 (레이트 리미터 통합)"""

        try:
            # 🔧 레이트 리미터 적용
            if self.rate_limiter:
                rate_limit_type = self._get_rate_limit_type(request.request_type)
                await self.rate_limiter.wait_for_availability(rate_limit_type)

            self.performance_stats['rest_requests'] += 1

            # REST API 호출
            if request.request_type == DataRequestType.MARKETS_LIST:
                is_details = request.params.get('is_details', False)
                return await self.rest_client.get_markets(is_details)

            elif request.request_type == DataRequestType.CANDLES_HISTORY:
                market = request.markets[0] if request.markets else ''
                unit = request.params.get('unit', 5)
                count = request.params.get('count', 200)
                to = request.params.get('to')
                return await self.rest_client.get_candles_minutes(market, unit, to, count)

            elif request.request_type == DataRequestType.TICKER_SNAPSHOT:
                # get_ticker → get_tickers로 수정 (올바른 메서드명)
                return await self.rest_client.get_tickers(request.markets)

            elif request.request_type == DataRequestType.ORDERBOOK_SNAPSHOT:
                return await self.rest_client.get_orderbook(request.markets)

            else:
                self.logger.warning(f"지원하지 않는 REST 요청: {request.request_type}")
                return None

        except Exception as e:
            self.logger.error(f"REST 요청 처리 오류: {e}")
            self.performance_stats['errors'] += 1
            return None

    def _get_rate_limit_type(self, request_type: DataRequestType) -> RateLimitType:
        """요청 타입에 따른 레이트 제한 타입 결정"""
        mapping = {
            DataRequestType.MARKETS_LIST: RateLimitType.REST_API,
            DataRequestType.CANDLES_HISTORY: RateLimitType.CANDLE_DATA,
            DataRequestType.TICKER_SNAPSHOT: RateLimitType.TICKER_DATA,
            DataRequestType.ORDERBOOK_SNAPSHOT: RateLimitType.ORDERBOOK_DATA,
            # 실시간 요청은 WebSocket이므로 별도 처리
            DataRequestType.REALTIME_TICKER: RateLimitType.WEBSOCKET,
            DataRequestType.REALTIME_TRADE: RateLimitType.WEBSOCKET,
            DataRequestType.REALTIME_ORDERBOOK: RateLimitType.WEBSOCKET,
            DataRequestType.REALTIME_CANDLE: RateLimitType.WEBSOCKET,
        }
        return mapping.get(request_type, RateLimitType.REST_API)

    def get_channel_status(self) -> Dict[str, Any]:
        """채널 상태 조회"""
        uptime = (datetime.now() - self.performance_stats['start_time']).total_seconds()

        # WebSocket RPS 계산
        if uptime > 0:
            websocket_rps = self.websocket_status.message_count / uptime
            self.websocket_status.rps = websocket_rps

        return {
            'websocket': {
                'connected': self.websocket_status.is_connected,
                'message_count': self.websocket_status.message_count,
                'error_count': self.websocket_status.error_count,
                'rps': round(self.websocket_status.rps, 2),
                'last_activity': self.websocket_status.last_activity.isoformat()
            },
            'rest': {
                'requests': self.performance_stats['rest_requests'],
                'available': True  # REST는 항상 사용 가능
            },
            'performance': {
                'total_errors': self.performance_stats['errors'],
                'uptime_seconds': round(uptime, 1),
                'total_websocket_messages': self.performance_stats['websocket_messages'],
                'total_rest_requests': self.performance_stats['rest_requests']
            },
            'active_subscriptions': dict(self.active_subscriptions)
        }

    async def shutdown(self):
        """채널 관리자 종료"""
        try:
            self.logger.info("퍼블릭 채널 관리자 종료 시작")

            # WebSocket 연결 해제
            if self.websocket_status.is_connected:
                await self.websocket_client.disconnect()
                self.websocket_status.is_connected = False

            # 상태 초기화
            self.active_subscriptions.clear()
            self.message_handlers.clear()

            self.logger.info("✅ 퍼블릭 채널 관리자 종료 완료")

        except Exception as e:
            self.logger.error(f"채널 관리자 종료 오류: {e}")

    # 편의 메서드들
    async def subscribe_ticker(self, markets: List[str],
                               callback: Optional[Callable[[ParsedMessage], None]] = None) -> bool:
        """현재가 구독 (편의 메서드)"""
        request = DataRequest(
            request_type=DataRequestType.REALTIME_TICKER,
            markets=markets,
            params={},
            callback=callback
        )
        result = await self.request_data(request)
        return isinstance(result, bool) and result

    async def subscribe_trade(self, markets: List[str],
                              callback: Optional[Callable[[ParsedMessage], None]] = None) -> bool:
        """체결 구독 (편의 메서드)"""
        request = DataRequest(
            request_type=DataRequestType.REALTIME_TRADE,
            markets=markets,
            params={},
            callback=callback
        )
        result = await self.request_data(request)
        return isinstance(result, bool) and result

    async def get_markets(self, is_details: bool = False) -> Optional[List[Dict[str, Any]]]:
        """마켓 정보 조회 (편의 메서드)"""
        request = DataRequest(
            request_type=DataRequestType.MARKETS_LIST,
            markets=[],
            params={'is_details': is_details}
        )
        return await self.request_data(request)

    async def get_candles_history(self, market: str, unit: int = 5,
                                  count: int = 200, to: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """캔들 기록 조회 (편의 메서드)"""
        request = DataRequest(
            request_type=DataRequestType.CANDLES_HISTORY,
            markets=[market],
            params={'unit': unit, 'count': count, 'to': to}
        )
        return await self.request_data(request)
