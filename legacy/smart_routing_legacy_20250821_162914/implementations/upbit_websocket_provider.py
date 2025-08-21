"""
업비트 WebSocket 데이터 제공자 (새 구현)

업비트 WebSocket API를 통해 실시간 데이터를 제공합니다.
Smart Router의 IDataProvider 인터페이스를 구현합니다.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

from ..interfaces.data_provider import IDataProvider
from ..strategies.websocket_manager import WebSocketSubscriptionManager
from ..strategies.rate_limit_mapper import IntegratedRateLimitFieldMapper, RateLimitType
from upbit_auto_trading.infrastructure.logging import create_component_logger
from ..models import (
    TradingSymbol,
    CandleDataRequest,
    TickerDataRequest,
    OrderbookDataRequest,
    TradeDataRequest,
    CandleDataResponse,
    TickerDataResponse,
    OrderbookDataResponse,
    TradeDataResponse,
    TickerData,
    OrderbookData,
    OrderbookLevel,
    TradeData,
    CandleData,
    ResponseFactory
)
from ..utils.exceptions import (
    WebSocketConnectionException,
    WebSocketDataException
)


class UpbitWebSocketProvider(IDataProvider):
    """업비트 WebSocket 데이터 제공자 V2

    WebSocketManager를 활용한 개선된 구현:
    - 연결 관리는 WebSocketManager에 위임
    - 데이터 변환과 도메인 모델 매핑에 집중
    - 더 안정적인 연결 관리와 자동 재연결
    - 연결 재사용을 통한 성능 최적화
    """

    def __init__(self):
        self.logger = create_component_logger("UpbitWebSocketProviderV2")

        # 연결 재사용을 위한 WebSocket 클라이언트 풀
        self._ws_client = None
        self._connection_lock = asyncio.Lock()
        self._last_activity = None
        self._connection_timeout = 30.0  # 30초 비활성 시 연결 해제

        # WebSocketManager 통합 (lazy initialization으로 변경)
        self.websocket_manager = None
        self.is_initialized = False

        # 통합 Rate Limiting + Field Mapping 시스템
        self.integrated_mapper = IntegratedRateLimitFieldMapper()

        # 데이터 캐시 (심볼별 최신 데이터)
        self.data_cache: Dict[str, Dict[str, Any]] = {}

        # 구독 ID 관리 (요청별 추적)
        self.subscription_ids: Dict[str, str] = {}  # symbol -> subscription_id

        # WebSocket 캔들 전용 클라이언트 (연결 재사용)
        self._candle_client = None
        self._candle_client_lock = asyncio.Lock()

        self.logger.debug("UpbitWebSocketProvider V2 초기화 완료")

    async def _initialize_if_needed(self):
        """필요 시에만 WebSocketManager 초기화 (lazy initialization)"""
        if not self.is_initialized:
            self.websocket_manager = WebSocketSubscriptionManager(
                websocket_url="wss://api.upbit.com/websocket/v1",
                max_connections=3,
                max_subscriptions_per_connection=10,
                idle_timeout_minutes=30
            )
            self.is_initialized = True
            self.logger.debug("WebSocketManager 지연 초기화 완료")

    async def _get_or_create_connection(self):
        """WebSocket 연결을 가져오거나 새로 생성 (연결 재사용 최적화)"""
        async with self._connection_lock:
            # 기존 연결이 유효한지 확인
            if (self._ws_client and self._ws_client.is_connected and
                    self._last_activity and
                    (datetime.now() - self._last_activity).total_seconds() < self._connection_timeout):
                self.logger.debug("기존 WebSocket 연결 재사용")
                return self._ws_client

            # 기존 연결 정리
            if self._ws_client and self._ws_client.is_connected:
                self.logger.debug("기존 WebSocket 연결 해제")
                await self._ws_client.disconnect()

            # 새 연결 생성
            from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
                UpbitWebSocketQuotationClient
            )

            self._ws_client = UpbitWebSocketQuotationClient()
            await self._ws_client.connect()
            self._last_activity = datetime.now()

            self.logger.debug("새 WebSocket 연결 생성 완료")
            return self._ws_client

    async def disconnect(self):
        """WebSocket 연결 해제 (완전 정리)"""
        try:
            # 1. WebSocketManager 정리
            if self.websocket_manager and self.is_initialized:
                self.logger.debug("WebSocketManager 정리 시작")
                await self.websocket_manager.stop()
                self.websocket_manager = None

            # 2. 개별 WebSocket 클라이언트 정리 (자동 재연결 비활성화)
            async with self._connection_lock:
                if self._ws_client:
                    # 자동 재연결 비활성화
                    self._ws_client.auto_reconnect = False
                    if self._ws_client.is_connected:
                        await self._ws_client.disconnect()
                    self._ws_client = None

            # 3. 캔들 전용 클라이언트 정리
            async with self._candle_client_lock:
                if self._candle_client:
                    self._candle_client.auto_reconnect = False
                    if self._candle_client.is_connected:
                        await self._candle_client.disconnect()
                    self._candle_client = None

            # 4. 캐시 및 상태 정리
            self.data_cache.clear()
            self.subscription_ids.clear()
            self.is_initialized = False

            self.logger.info("✅ WebSocket Provider V2 완전 정리 완료")

        except Exception as e:
            self.logger.error(f"❌ WebSocket Provider 정리 중 오류: {e}")
            # 강제 정리
            self.websocket_manager = None
            self._ws_client = None
            self._candle_client = None
            self.is_initialized = False

    async def _ensure_initialized(self):
        """WebSocketManager 초기화 확인"""
        if not self.is_initialized:
            await self._initialize_if_needed()
            await self.websocket_manager.start()
            self.is_initialized = True
            self.logger.info("✅ WebSocketManager 초기화 완료")

    def _create_data_callback(self, symbol: TradingSymbol, data_type: str):
        """데이터 수신 콜백 생성"""

        def callback(raw_data: Dict[str, Any]):
            try:
                # 심볼별 데이터 캐시 업데이트
                symbol_key = symbol.to_upbit_symbol()

                if symbol_key not in self.data_cache:
                    self.data_cache[symbol_key] = {}

                # 첫 번째 데이터인지 확인
                is_first_data = data_type not in self.data_cache[symbol_key]

                # 데이터 타입별 저장
                self.data_cache[symbol_key][data_type] = raw_data
                self.data_cache[symbol_key]['last_update'] = datetime.now()

                if is_first_data:
                    self.logger.debug(f"📊 데이터 수신: {symbol_key} ({data_type}) - 첫 번째")
                else:
                    # 실시간 업데이트는 더 낮은 레벨로 로깅
                    self.logger.debug(f"🔄 데이터 업데이트: {symbol_key} ({data_type})")

            except Exception as e:
                self.logger.error(f"❌ 데이터 콜백 처리 오류: {e}")

        return callback

    async def _subscribe_if_needed(self, symbol: TradingSymbol, data_types: List[str]) -> str:
        """필요시 구독 설정"""
        await self._ensure_initialized()

        symbol_key = symbol.to_upbit_symbol()

        # 이미 구독된 경우 기존 ID 반환
        if symbol_key in self.subscription_ids:
            existing_subscription = self.websocket_manager.subscriptions.get(
                self.subscription_ids[symbol_key]
            )
            if existing_subscription and existing_subscription.is_active:
                self.logger.debug(f"🔄 기존 구독 재사용: {symbol_key}")
                return self.subscription_ids[symbol_key]

        # 새 구독 생성
        callback = self._create_data_callback(symbol, data_types[0])

        try:
            subscription_id = await self.websocket_manager.subscribe(
                symbol=symbol,
                data_types=data_types,
                callback=callback
            )

            self.subscription_ids[symbol_key] = subscription_id
            self.logger.info(f"✅ 새 구독 생성: {symbol_key} -> {subscription_id}")

            return subscription_id

        except Exception as e:
            self.logger.error(f"❌ 구독 생성 실패: {symbol_key} - {e}")
            raise WebSocketConnectionException(f"구독 실패: {e}")

    async def _wait_for_data(self, symbol: TradingSymbol, data_type: str, timeout: float = 5.0) -> Dict[str, Any]:
        """데이터 수신 대기"""
        symbol_key = symbol.to_upbit_symbol()

        # 이미 캐시된 데이터가 있으면 반환
        if (symbol_key in self.data_cache and
                data_type in self.data_cache[symbol_key]):
            return self.data_cache[symbol_key][data_type]

        # 데이터 수신 대기
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < timeout:
            if (symbol_key in self.data_cache and
                    data_type in self.data_cache[symbol_key]):
                return self.data_cache[symbol_key][data_type]

            await asyncio.sleep(0.1)

        raise WebSocketDataException(
            f"데이터 수신 타임아웃: {symbol_key} ({data_type})"
        )

    async def _get_candle_client(self):
        """캔들 전용 WebSocket 클라이언트 재사용 (성능 최적화)"""
        async with self._candle_client_lock:
            if self._candle_client is None or not self._candle_client.is_connected:
                from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
                    UpbitWebSocketQuotationClient
                )

                if self._candle_client and self._candle_client.is_connected:
                    await self._candle_client.disconnect()

                self._candle_client = UpbitWebSocketQuotationClient()
                await self._candle_client.connect()
                self.logger.debug("🔄 캔들 전용 WebSocket 클라이언트 생성/재연결")

            return self._candle_client

    # IDataProvider 인터페이스 구현

    def get_provider_info(self) -> Dict[str, str]:
        """Provider 정보 반환"""
        return {
            "name": "upbit_websocket_v2",
            "description": "업비트 WebSocket V2 (WebSocketManager 통합)",
            "version": "2.0.0",
            "data_source": "websocket_managed"
        }

    def get_supported_capabilities(self) -> List[str]:
        """지원되는 기능 목록 반환"""
        return ["ticker", "orderbook", "trade", "candle"]

    async def get_candle_data(self, request: CandleDataRequest) -> CandleDataResponse:
        """캔들 데이터 조회 (최적화된 연결 재사용 방식)"""
        try:
            symbol_str = request.symbol.to_upbit_symbol()

            # Timeframe을 WebSocket 캔들 단위로 변환
            candle_unit = self._timeframe_to_candle_unit(request.timeframe)
            if not candle_unit:
                raise WebSocketDataException(f"지원하지 않는 Timeframe: {request.timeframe}")

            self.logger.debug(f"WebSocket 캔들 구독 시도: {symbol_str} {candle_unit}분")

            # 연결 재사용 최적화된 WebSocket 클라이언트 가져오기
            ws_client = await self._get_or_create_connection()
            candle_data = None

            def candle_handler(message):
                """캔들 데이터 핸들러"""
                nonlocal candle_data
                if message.market == symbol_str and "candle" in message.type.value:
                    candle_data = message.data
                    self.logger.debug(f"WebSocket 캔들 데이터 수신: {symbol_str}")

            try:
                # WebSocket 캔들 핸들러 등록
                from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
                    WebSocketDataType
                )

                # 캔들 타입 매핑
                candle_type_map = {
                    1: WebSocketDataType.CANDLE_1M,
                    5: WebSocketDataType.CANDLE_5M,
                    15: WebSocketDataType.CANDLE_15M
                }

                if candle_unit not in candle_type_map:
                    raise WebSocketDataException(f"지원하지 않는 캔들 단위: {candle_unit}분")

                ws_client.add_message_handler(candle_type_map[candle_unit], candle_handler)

                # 캔들 구독 실행
                success = await ws_client.subscribe_candle([symbol_str], unit=candle_unit)
                if not success:
                    raise WebSocketDataException(f"캔들 구독 실패: {symbol_str}")

                self.logger.info(f"✅ 캔들 구독 성공: {symbol_str} ({candle_unit}분)")

                # 캔들 데이터 수신 대기 (최대 5초)
                max_wait = 50  # 0.1초씩 50번 = 5초
                wait_count = 0

                while candle_data is None and wait_count < max_wait:
                    await asyncio.sleep(0.1)
                    wait_count += 1

                if candle_data is None:
                    raise WebSocketDataException(f"캔들 데이터 수신 타임아웃: {symbol_str}")

                # 연결 활동 시간 업데이트
                self._last_activity = datetime.now()

                # 업비트 WebSocket 캔들 데이터를 도메인 모델로 변환
                domain_candle = self._convert_websocket_candle_to_domain(candle_data)
                response_data = [domain_candle]

                # 응답 메타데이터 생성
                metadata = ResponseFactory.create_metadata(
                    request_time=datetime.now(),
                    data_source="websocket"
                )

                return CandleDataResponse(
                    symbol=request.symbol,
                    timeframe=request.timeframe,
                    data=response_data,
                    metadata=metadata
                )

            except Exception as e:
                # 에러 발생 시 연결을 정리하지 않고 재사용 가능하도록 유지
                self.logger.error(f"캔들 데이터 조회 중 오류: {e}")
                raise

        except Exception as e:
            self.logger.error(f"WebSocket 캔들 데이터 조회 실패: {e}")
            raise WebSocketDataException(f"WebSocket 캔들 데이터 조회 실패: {e}")

    def _convert_websocket_candle_to_domain(self, raw_data: Dict[str, Any]) -> CandleData:
        """업비트 WebSocket 캔들 데이터를 도메인 모델로 변환"""
        from datetime import datetime
        from decimal import Decimal

        # 업비트 WebSocket 캔들 필드 매핑 (공식 문서 기준)
        # trade_price: 종가, opening_price: 시가, high_price: 고가, low_price: 저가
        # candle_acc_trade_volume: 누적 거래량, timestamp: 타임스탬프
        return CandleData(
            timestamp=datetime.fromtimestamp(raw_data.get('timestamp', 0) / 1000),  # 밀리초 -> 초
            open_price=Decimal(str(raw_data.get('opening_price', 0))),
            high_price=Decimal(str(raw_data.get('high_price', 0))),
            low_price=Decimal(str(raw_data.get('low_price', 0))),
            close_price=Decimal(str(raw_data.get('trade_price', 0))),  # 종가는 trade_price
            volume=Decimal(str(raw_data.get('candle_acc_trade_volume', 0)))
        )

    def _timeframe_to_websocket_type(self, timeframe) -> Optional[str]:
        """Timeframe을 WebSocket 캔들 타입으로 변환"""
        from ..models.timeframes import Timeframe

        mapping = {
            Timeframe.MINUTE_1: "candle.1m",
            Timeframe.MINUTE_5: "candle.5m",
            Timeframe.MINUTE_15: "candle.15m"
        }
        return mapping.get(timeframe)

    def _timeframe_to_candle_unit(self, timeframe) -> Optional[int]:
        """Timeframe을 캔들 단위(분)로 변환"""
        from ..models.timeframes import Timeframe

        mapping = {
            Timeframe.MINUTE_1: 1,
            Timeframe.MINUTE_5: 5,
            Timeframe.MINUTE_15: 15
        }
        return mapping.get(timeframe)

    async def _wait_for_candle_data(self, symbol: str, timeout: float = 5.0) -> Optional[Any]:
        """WebSocket에서 캔들 데이터 수신 대기"""
        # 간단한 구현: 캔들 데이터 캐시에서 확인
        # 실제로는 WebSocketManager에서 캔들 이벤트를 받아야 함

        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            # TODO: 실제 캔들 데이터 수신 로직 구현 필요
            # 현재는 타임아웃으로 None 반환
            await asyncio.sleep(0.1)

        return None  # 타임아웃

    def _handle_candle_data(self, data: Dict[str, Any]) -> None:
        """캔들 데이터 수신 핸들러"""
        # TODO: 캔들 데이터를 캐시하고 _wait_for_candle_data에서 활용
        market = data.get('market') or data.get('code', 'UNKNOWN')
        self.logger.debug(f"📊 캔들 데이터 수신: {market}")

    async def get_ticker_data(self, request: TickerDataRequest) -> TickerDataResponse:
        """티커 데이터 조회"""
        try:
            # 티커 데이터 구독
            await self._subscribe_if_needed(request.symbol, ["ticker"])

            # 데이터 수신 대기
            raw_data = await self._wait_for_data(request.symbol, "ticker")

            # 도메인 모델로 변환
            ticker_data = TickerData(
                timestamp=datetime.now(),
                current_price=Decimal(str(raw_data.get('trade_price', 0))),
                change_rate=Decimal(str(raw_data.get('signed_change_rate', 0.0))),
                change_amount=Decimal(str(raw_data.get('signed_change_price', 0))),
                volume_24h=Decimal(str(raw_data.get('acc_trade_volume_24h', 0.0))),
                high_24h=Decimal(str(raw_data.get('high_price', 0))),
                low_24h=Decimal(str(raw_data.get('low_price', 0))),
                opening_price=Decimal(str(raw_data.get('opening_price', 0)))
            )

            return TickerDataResponse(
                symbol=request.symbol,
                data=ticker_data,
                metadata=ResponseFactory.create_metadata(
                    request_time=datetime.now(),
                    data_source="websocket_v2"
                )
            )

        except Exception as e:
            self.logger.error(f"❌ 티커 데이터 조회 실패: {e}")
            raise WebSocketDataException(f"티커 데이터 조회 실패: {e}")

    async def get_orderbook_data(self, request: OrderbookDataRequest) -> OrderbookDataResponse:
        """호가창 데이터 조회"""
        try:
            # 호가창 데이터 구독
            await self._subscribe_if_needed(request.symbol, ["orderbook"])

            # 데이터 수신 대기
            raw_data = await self._wait_for_data(request.symbol, "orderbook")

            # 호가창 데이터 변환
            bids = []
            asks = []

            # 업비트 WebSocket orderbook_units 파싱
            orderbook_units = raw_data.get('orderbook_units', [])
            for unit in orderbook_units:
                # 매수 호가
                if 'bid_price' in unit and 'bid_size' in unit:
                    bids.append(OrderbookLevel(
                        price=Decimal(str(unit['bid_price'])),
                        size=Decimal(str(unit['bid_size']))
                    ))

                # 매도 호가
                if 'ask_price' in unit and 'ask_size' in unit:
                    asks.append(OrderbookLevel(
                        price=Decimal(str(unit['ask_price'])),
                        size=Decimal(str(unit['ask_size']))
                    ))

            orderbook_data = OrderbookData(
                timestamp=datetime.now(),
                bids=bids,
                asks=asks
            )

            return OrderbookDataResponse(
                symbol=request.symbol,
                data=orderbook_data,
                metadata=ResponseFactory.create_metadata(
                    request_time=datetime.now(),
                    data_source="websocket_v2"
                )
            )

        except Exception as e:
            self.logger.error(f"❌ 호가창 데이터 조회 실패: {e}")
            raise WebSocketDataException(f"호가창 데이터 조회 실패: {e}")

    async def get_trade_data(self, request: TradeDataRequest) -> TradeDataResponse:
        """체결 데이터 조회"""
        try:
            # 체결 데이터 구독
            await self._subscribe_if_needed(request.symbol, ["trade"])

            # 데이터 수신 대기
            raw_data = await self._wait_for_data(request.symbol, "trade")

            # ask_bid 변환: ASK(매도) -> sell, BID(매수) -> buy
            ask_bid = raw_data.get('ask_bid', 'BID')
            side = 'sell' if ask_bid == 'ASK' else 'buy'

            # 체결 데이터 변환
            trade_data = TradeData(
                timestamp=datetime.now(),
                price=Decimal(str(raw_data.get('trade_price', 0))),
                size=Decimal(str(raw_data.get('trade_volume', 0.0))),
                side=side
            )

            return TradeDataResponse(
                symbol=request.symbol,
                data=[trade_data],
                metadata=ResponseFactory.create_metadata(
                    request_time=datetime.now(),
                    data_source="websocket_v2"
                )
            )

        except Exception as e:
            self.logger.error(f"❌ 체결 데이터 조회 실패: {e}")
            raise WebSocketDataException(f"체결 데이터 조회 실패: {e}")

    async def get_market_list(self) -> List[TradingSymbol]:
        """마켓 목록 조회 (WebSocket으로는 불가능)"""
        raise NotImplementedError(
            "WebSocket V2 프로바이더는 마켓 목록 조회를 지원하지 않습니다. REST API를 사용하세요."
        )

    async def health_check(self) -> Dict[str, Any]:
        """상태 확인"""
        # WebSocketManager 통계 가져오기
        manager_stats = self.websocket_manager.get_subscription_stats()

        return {
            "status": "healthy" if self.is_initialized else "not_initialized",
            "provider_type": "websocket_v2",
            "websocket_manager": {
                "initialized": self.is_initialized,
                "total_subscriptions": manager_stats.get("total_subscriptions", 0),
                "active_subscriptions": manager_stats.get("active_subscriptions", 0),
                "total_connections": manager_stats.get("total_connections", 0)
            },
            "data_cache": {
                "cached_symbols": len(self.data_cache),
                "symbols": list(self.data_cache.keys())
            },
            "subscription_mapping": len(self.subscription_ids),
            "last_check": datetime.now().isoformat()
        }
