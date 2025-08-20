"""
업비트 WebSocket 데이터 제공자 (새 구현)

업비트 WebSocket API를 통해 실시간 데이터를 제공합니다.
Smart Router의 IDataProvider 인터페이스를 구현합니다.
"""

import asyncio
from typing import List, Dict, Any
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
    """

    def __init__(self):
        self.logger = create_component_logger("UpbitWebSocketProviderV2")

        # WebSocketManager 통합
        self.websocket_manager = WebSocketSubscriptionManager(
            websocket_url="wss://api.upbit.com/websocket/v1",
            max_connections=3,
            max_subscriptions_per_connection=10,
            idle_timeout_minutes=30
        )

        # 통합 Rate Limiting + Field Mapping 시스템
        self.integrated_mapper = IntegratedRateLimitFieldMapper()

        # 데이터 캐시 (심볼별 최신 데이터)
        self.data_cache: Dict[str, Dict[str, Any]] = {}

        # 구독 ID 관리 (요청별 추적)
        self.subscription_ids: Dict[str, str] = {}  # symbol -> subscription_id

        # 연결 상태
        self.is_initialized = False

    async def _ensure_initialized(self):
        """WebSocketManager 초기화 확인"""
        if not self.is_initialized:
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

                # 데이터 타입별 저장
                self.data_cache[symbol_key][data_type] = raw_data
                self.data_cache[symbol_key]['last_update'] = datetime.now()

                self.logger.debug(f"📊 데이터 수신: {symbol_key} ({data_type})")

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
        return ["ticker", "orderbook", "trade"]

    async def get_candle_data(self, request: CandleDataRequest) -> CandleDataResponse:
        """캔들 데이터 조회 (WebSocket으로는 제한적)"""
        raise NotImplementedError(
            "WebSocket V2 프로바이더는 캔들 데이터를 지원하지 않습니다. REST API를 사용하세요."
        )

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

            # 체결 데이터 변환
            trade_data = TradeData(
                timestamp=datetime.now(),
                price=Decimal(str(raw_data.get('trade_price', 0))),
                size=Decimal(str(raw_data.get('trade_volume', 0.0))),
                side=raw_data.get('ask_bid', 'BID').lower()
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

    async def disconnect(self):
        """연결 해제 및 정리"""
        if self.is_initialized:
            await self.websocket_manager.stop()
            self.is_initialized = False
            self.data_cache.clear()
            self.subscription_ids.clear()
            self.logger.info("✅ WebSocket Provider V2 연결 해제 완료")

    def __del__(self):
        """소멸자 - 연결 정리"""
        if self.is_initialized:
            try:
                asyncio.create_task(self.disconnect())
            except Exception:
                pass  # 이미 이벤트 루프가 종료된 경우
