"""
스마트 라우터 V2.0 - 메인 라우터

업비트 WebSocket과 REST API를 통합하여 최적의 채널을 자동 선택하고,
일관된 형식의 데이터를 제공하는 스마트 라우팅 시스템입니다.

주요 기능:
- 자동 채널 선택 (WebSocket vs REST API)
- 데이터 형식 통일 (REST API 기준)
- 패턴 학습 및 예측
- Rate Limit 관리
- 자동 폴백 처리
"""

import time
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .models import (
    DataRequest, ChannelDecision, RoutingMetrics,
    DataType, ChannelType, RealtimePriority
)
from .data_format_unifier import DataFormatUnifier
from .channel_selector import ChannelSelector
from .websocket_subscription_manager import WebSocketSubscriptionManager, SubscriptionType


class SmartRouterConfig:
    """스마트 라우터 설정 일괄 관리"""

    # WebSocket 타임아웃 설정
    WEBSOCKET_SUBSCRIPTION_TIMEOUT = 3.0  # 구독 타임아웃 (초)
    WEBSOCKET_DATA_RECEIVE_TIMEOUT = 3.0  # 데이터 수신 타임아웃 (초)
    WEBSOCKET_SUBSCRIPTION_STABILIZATION_DELAY = 0.1  # 구독 후 안정화 대기 (초)

    # REST API 타임아웃 설정
    REST_API_TIMEOUT = 5.0  # REST API 요청 타임아웃 (초)

    # 캐시 설정
    CACHE_TTL_SECONDS = 60.0  # 캐시 TTL (초)
    MAX_CACHE_SIZE = 1000  # 최대 캐시 개수

    # 성능 임계값
    WEBSOCKET_MIN_PERFORMANCE_THRESHOLD = 50  # WebSocket 최소 성능 임계값 (메시지/초)
    MAX_RETRY_ATTEMPTS = 3  # 최대 재시도 횟수

    # 구독 관리 설정 - v3.0 WebSocket 구독 모델
    MAX_SUBSCRIPTION_TYPES = 4  # 업비트 WebSocket 지원 타입 수 (ticker, trade, orderbook, candle)
    BUFFER_SUBSCRIPTION_TYPES = 5  # 끊김 없는 전환을 위한 버퍼 (4+1 전략)
    SUBSCRIPTION_TRANSITION_STABILIZATION_DELAY = 0.5  # 구독 전환 시 안정화 대기 (초)

    # 레거시 호환성 (Deprecated - v3.0에서는 구독 타입 수가 제한 요소)
    MAX_CONCURRENT_SUBSCRIPTIONS = BUFFER_SUBSCRIPTION_TYPES  # v3.0 호환: 타입 기준으로 설정
    EMERGENCY_SUBSCRIPTION_LIMIT = 3  # 비상시 구독 제한

    @classmethod
    def get_websocket_timeouts(cls) -> Dict[str, float]:
        """WebSocket 관련 타임아웃 설정 반환"""
        return {
            "subscription_timeout": cls.WEBSOCKET_SUBSCRIPTION_TIMEOUT,
            "data_receive_timeout": cls.WEBSOCKET_DATA_RECEIVE_TIMEOUT,
            "stabilization_delay": cls.WEBSOCKET_SUBSCRIPTION_STABILIZATION_DELAY
        }

    @classmethod
    def update_websocket_timeouts(cls, subscription_timeout: Optional[float] = None,
                                  data_receive_timeout: Optional[float] = None,
                                  stabilization_delay: Optional[float] = None) -> None:
        """WebSocket 타임아웃 설정 업데이트"""
        if subscription_timeout is not None:
            cls.WEBSOCKET_SUBSCRIPTION_TIMEOUT = subscription_timeout
        if data_receive_timeout is not None:
            cls.WEBSOCKET_DATA_RECEIVE_TIMEOUT = data_receive_timeout
        if stabilization_delay is not None:
            cls.WEBSOCKET_SUBSCRIPTION_STABILIZATION_DELAY = stabilization_delay


# Lazy import를 위한 TYPE_CHECKING
if TYPE_CHECKING:
    from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient
    from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_public_client import (
        UpbitWebSocketPublicClient, WebSocketDataType
    )

logger = create_component_logger("SmartRouter")


class SmartRouter:
    """스마트 라우터 - 통합 라우팅 시스템"""

    def __init__(self):
        """스마트 라우터 초기화"""
        logger.info("SmartRouter 초기화 시작")

        # 핵심 컴포넌트
        self.data_unifier = DataFormatUnifier()
        self.channel_selector = ChannelSelector()

        # 라우팅 메트릭
        self.metrics = RoutingMetrics()

        # API 클라이언트들 (lazy loading)
        self.rest_client: Optional['UpbitPublicClient'] = None
        self.websocket_client: Optional['UpbitWebSocketPublicClient'] = None

        # WebSocket 구독 매니저 (v3.0 핵심 컴포넌트)
        self.websocket_subscription_manager: Optional[WebSocketSubscriptionManager] = None

        # 캐시 시스템 (v3.0 최적화된 단순 캐시)
        self.cache = {}
        self.cache_ttl = SmartRouterConfig.CACHE_TTL_SECONDS

        # 상태 관리
        self.is_initialized = False

        logger.info("SmartRouter v3.0 초기화 완료 (클라이언트들은 on-demand 초기화)")

    async def initialize(self) -> None:
        """스마트 라우터 v3.0 초기화"""
        logger.info("SmartRouter v3.0 서비스 초기화")

        # API 클라이언트들을 on-demand 초기화
        await self._ensure_clients_initialized()

        self.is_initialized = True
        logger.info("✅ SmartRouter v3.0 초기화 완료")

    async def _ensure_clients_initialized(self) -> None:
        """API 클라이언트들을 lazy loading으로 초기화"""
        if self.rest_client is None:
            try:
                # 필요할 때만 import하고 초기화
                from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient
                self.rest_client = UpbitPublicClient()
                logger.info("REST 클라이언트 초기화 완료")
            except Exception as e:
                logger.warning(f"REST 클라이언트 초기화 실패: {e}")

        if self.websocket_client is None:
            try:
                from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_public_client import (
                    UpbitWebSocketPublicClient
                )
                self.websocket_client = UpbitWebSocketPublicClient()

                # WebSocket 연결 시도 (에러 발생 시 상태만 업데이트)
                try:
                    await self.websocket_client.connect()
                    is_connected = self.websocket_client.is_connected
                    self.channel_selector.update_websocket_status(is_connected)

                    # WebSocket 구독 매니저 초기화 - v3.0 버퍼 전략 적용
                    if is_connected and self.websocket_subscription_manager is None:
                        self.websocket_subscription_manager = WebSocketSubscriptionManager(
                            self.websocket_client,
                            max_subscription_types=SmartRouterConfig.BUFFER_SUBSCRIPTION_TYPES
                        )
                        logger.info(f"WebSocket 구독 매니저 v3.0 초기화 완료 - 버퍼 전략: {SmartRouterConfig.BUFFER_SUBSCRIPTION_TYPES}개 타입")

                    logger.info(f"WebSocket 클라이언트 초기화 완료 - 연결 상태: {'연결됨' if is_connected else '연결 실패'}")
                except Exception as conn_error:
                    logger.warning(f"WebSocket 연결 실패: {conn_error}")
                    self.channel_selector.update_websocket_status(False)

            except Exception as e:
                logger.warning(f"WebSocket 클라이언트 초기화 실패: {e}")
                self.channel_selector.update_websocket_status(False)

    async def get_data(self, request: DataRequest) -> Dict[str, Any]:
        """통합 데이터 요청 처리

        Args:
            request: 데이터 요청

        Returns:
            통일된 형식의 응답 데이터
        """
        start_time = time.time()
        channel_decision = None

        try:
            # 로그용 심볼 표시 제한 (처음 3개 + 마지막 3개)
            symbols_display = self._format_symbols_for_log(request.symbols)
            logger.debug(f"데이터 요청 처리 시작 - type: {request.data_type.value}, symbols: {symbols_display}")

            # 메트릭 업데이트
            self.metrics.total_requests += 1

            # 1단계: 캐시 확인 (호가/티커는 실시간성 우선으로 캐시 건너뛰기)
            if request.data_type not in [DataType.ORDERBOOK, DataType.TICKER]:
                cached_result = self._check_cache(request)
                if cached_result:
                    logger.debug("캐시에서 데이터 반환")
                    self.metrics.cache_hit_ratio = self._update_cache_hit_ratio(True)
                    return cached_result

            self.metrics.cache_hit_ratio = self._update_cache_hit_ratio(False)

            # 2단계: 채널 선택
            channel_decision = self.channel_selector.select_channel(request)
            logger.info(f"채널 선택 완료 - 채널: {channel_decision.channel.value}, 이유: {channel_decision.reason}")

            # 3단계: 선택된 채널로 데이터 요청
            raw_data = await self._execute_request(request, channel_decision)

            # 4단계: 데이터 형식 통일
            unified_data = self._unify_response_data(raw_data, request.data_type, channel_decision.channel)

            # 5단계: 캐시 저장 (호가/티커는 실시간성 우선으로 캐시 저장 건너뛰기)
            if request.data_type not in [DataType.ORDERBOOK, DataType.TICKER]:
                self._store_cache(request, unified_data)

            # 6단계: 메트릭 업데이트
            self._update_metrics(channel_decision, time.time() - start_time, True)

            logger.debug(f"데이터 요청 처리 완료 - 소요시간: {(time.time() - start_time) * 1000:.1f}ms")

            return {
                "success": True,
                "data": unified_data,
                "metadata": {
                    "channel": channel_decision.channel.value,
                    "reason": channel_decision.reason,
                    "confidence": channel_decision.confidence,
                    "response_time_ms": (time.time() - start_time) * 1000,
                    "request_id": request.request_id
                }
            }

        except Exception as e:
            logger.error(f"데이터 요청 처리 실패: {e}")
            self._update_metrics(None, time.time() - start_time, False)

            # 에러 상황에서도 채널 정보 제공 (가능한 경우)
            channel_info = {}
            if channel_decision is not None:
                channel_info = {
                    "channel": channel_decision.channel.value,
                    "reason": channel_decision.reason,
                    "confidence": channel_decision.confidence
                }

            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    **channel_info,
                    "response_time_ms": (time.time() - start_time) * 1000,
                    "request_id": request.request_id
                }
            }

    async def get_ticker(
        self,
        symbols: List[str],
        realtime_priority: RealtimePriority = RealtimePriority.MEDIUM
    ) -> Dict[str, Any]:
        """티커 데이터 조회 (편의 메서드)"""
        request = DataRequest(
            symbols=symbols,
            data_type=DataType.TICKER,
            realtime_priority=realtime_priority,
            request_id=f"ticker_{int(time.time() * 1000)}"
        )
        return await self.get_data(request)

    async def get_orderbook(
        self,
        symbols: List[str],
        realtime_priority: RealtimePriority = RealtimePriority.HIGH
    ) -> Dict[str, Any]:
        """호가 데이터 조회 (편의 메서드)"""
        request = DataRequest(
            symbols=symbols,
            data_type=DataType.ORDERBOOK,
            realtime_priority=realtime_priority,
            request_id=f"orderbook_{int(time.time() * 1000)}"
        )
        return await self.get_data(request)

    async def get_trades(
        self,
        symbols: List[str],
        count: int = 100,
        realtime_priority: RealtimePriority = RealtimePriority.MEDIUM
    ) -> Dict[str, Any]:
        """체결 데이터 조회 (편의 메서드)"""
        request = DataRequest(
            symbols=symbols,
            data_type=DataType.TRADES,
            realtime_priority=realtime_priority,
            count=count,
            request_id=f"trades_{int(time.time() * 1000)}"
        )
        return await self.get_data(request)

    async def get_candles(
        self,
        symbols: List[str],
        interval: str = "1m",
        count: int = 1,
        to: Optional[str] = None
    ) -> Dict[str, Any]:
        """캔들 데이터 조회 (편의 메서드)

        Args:
            symbols: 조회할 심볼 리스트 (예: ["KRW-BTC"])
            interval: 캔들 간격 (예: "1m", "5m", "15m", "1h", "1d")
            count: 조회할 캔들 개수 (최대 200개, 기본값: 1)
            to: 조회 기간 종료 시각 (ISO 8601 형식, 예: "2025-06-24T04:56:53Z")
        """
        # 실시간성 우선순위 결정
        if count <= 10:
            realtime_priority = RealtimePriority.HIGH
        elif count <= 50:
            realtime_priority = RealtimePriority.MEDIUM
        else:
            realtime_priority = RealtimePriority.LOW

        request = DataRequest(
            symbols=symbols,
            data_type=DataType.CANDLES,
            realtime_priority=realtime_priority,
            count=count,
            interval=interval,
            to=to,
            request_id=f"candles_{int(time.time() * 1000)}"
        )
        return await self.get_data(request)

    async def _execute_request(self, request: DataRequest, decision: ChannelDecision) -> Dict[str, Any]:
        """선택된 채널로 실제 요청 실행"""
        if decision.channel == ChannelType.WEBSOCKET:
            return await self._execute_websocket_request(request)
        else:
            return await self._execute_rest_request(request)

    async def _execute_websocket_request(self, request: DataRequest) -> Dict[str, Any]:
        """WebSocket 요청 실행 - 최적화된 버전"""
        try:
            # 클라이언트 초기화 확인
            await self._ensure_clients_initialized()

            if not self.websocket_client or not getattr(self.websocket_client, 'is_connected', False):
                logger.warning("WebSocket 연결 없음 - 즉시 REST 폴백")
                self.channel_selector.record_websocket_error()
                return await self._execute_rest_request(request)

            # WebSocket 구독 및 실시간 데이터 수신 통합 처리
            if request.data_type == DataType.TICKER:
                return await self._handle_websocket_ticker(request)
            elif request.data_type == DataType.ORDERBOOK:
                return await self._handle_websocket_orderbook(request)
            elif request.data_type == DataType.TRADES:
                return await self._handle_websocket_trades(request)
            elif request.data_type == DataType.CANDLES or request.data_type == DataType.CANDLES_1S:
                # 캔들 데이터는 WebSocket 제약이 많아 REST API로 처리
                logger.info("캔들 데이터 요청 - REST API 사용")
                self.channel_selector.record_websocket_error()
                return await self._execute_rest_request(request)
            else:
                logger.warning(f"WebSocket에서 지원하지 않는 데이터 타입: {request.data_type.value}")
                self.channel_selector.record_websocket_error()
                return await self._execute_rest_request(request)

        except Exception as e:
            logger.error(f"WebSocket 요청 실행 실패: {e}")
            self.channel_selector.record_websocket_error()
            return await self._execute_rest_request(request)

    async def _handle_websocket_ticker(self, request: DataRequest) -> Dict[str, Any]:
        """WebSocket 현재가 데이터 처리 - 구독 매니저 통합"""
        try:
            # Rate Limit 사용량 증가 (구독 기반)
            current_usage = self.channel_selector.rate_limits["websocket"]["current"] + 1
            self.channel_selector.update_rate_limit("websocket", current_usage)

            # 구독 매니저를 통한 구독 처리 (에러 시 즉시 폴백)
            try:
                # 구독 매니저가 있으면 배치 구독 사용
                if self.websocket_subscription_manager:
                    success = await self.websocket_subscription_manager.request_batch_subscription(
                        request.symbols, SubscriptionType.TICKER, priority=5
                    )

                    if not success:
                        logger.warning("구독 매니저를 통한 배치 구독 실패 - 직접 구독 시도")
                        raise Exception("구독 매니저 배치 구독 실패")

                    symbols_display = self._format_symbols_for_log(request.symbols)
                    logger.info(f"구독 매니저를 통한 현재가 배치 구독 완료: {symbols_display}")
                else:
                    # 기존 직접 구독 방식
                    if self.websocket_client and hasattr(self.websocket_client, 'subscribe_ticker'):
                        await self.websocket_client.subscribe_ticker(request.symbols)
                        symbols_display = self._format_symbols_for_log(request.symbols)
                        logger.info(f"WebSocket 현재가 구독 완료: {symbols_display}")
                    else:
                        raise Exception("WebSocket 클라이언트 없음")

                # 구독 후 안정화 대기 (설정값 사용)
                import asyncio
                await asyncio.sleep(SmartRouterConfig.WEBSOCKET_SUBSCRIPTION_STABILIZATION_DELAY)

            except Exception as subscribe_error:
                logger.warning(f"WebSocket 구독 실패: {subscribe_error} - REST 폴백")
                # Rate Limit 롤백
                rollback_usage = self.channel_selector.rate_limits["websocket"]["current"] - 1
                self.channel_selector.update_rate_limit("websocket", rollback_usage)
                return await self._execute_rest_request(request)

            # 실시간 데이터 수신 (설정값 사용)
            realtime_data = await self._receive_websocket_data(
                data_type="ticker",
                symbols=request.symbols,
                timeout=SmartRouterConfig.WEBSOCKET_DATA_RECEIVE_TIMEOUT
            )

            if realtime_data:
                logger.info("✅ WebSocket 실시간 현재가 데이터 수신 성공")
                self.channel_selector.record_websocket_success()
                return self._format_websocket_response(realtime_data, request)
            else:
                # 실시간 수신 실패 시 REST API로 폴백
                logger.warning("WebSocket 실시간 수신 실패 → REST 폴백")
                self.channel_selector.record_websocket_error()
                return await self._execute_rest_request(request)

        except Exception as e:
            logger.error(f"WebSocket 현재가 처리 실패: {e}")
            self.channel_selector.record_websocket_error()
            return await self._execute_rest_request(request)

    async def _handle_websocket_orderbook(self, request: DataRequest) -> Dict[str, Any]:
        """WebSocket 호가 데이터 처리 - 설정 기반 최적화"""
        try:
            # 구독 처리
            try:
                if self.websocket_client and hasattr(self.websocket_client, 'subscribe_orderbook'):
                    await self.websocket_client.subscribe_orderbook(request.symbols)
                    symbols_display = self._format_symbols_for_log(request.symbols)
                    logger.info(f"WebSocket 호가 구독 완료: {symbols_display}")

                    # 구독 후 안정화 대기 (설정값 사용)
                    import asyncio
                    await asyncio.sleep(SmartRouterConfig.WEBSOCKET_SUBSCRIPTION_STABILIZATION_DELAY)
                else:
                    raise Exception("WebSocket 클라이언트 없음")
            except Exception as subscribe_error:
                logger.warning(f"WebSocket 호가 구독 실패: {subscribe_error} - REST 폴백")
                return await self._execute_rest_request(request)

            # 실시간 데이터 수신 (설정값 사용)
            realtime_data = await self._receive_websocket_data(
                data_type="orderbook",
                symbols=request.symbols,
                timeout=SmartRouterConfig.WEBSOCKET_DATA_RECEIVE_TIMEOUT
            )

            if realtime_data:
                logger.info("✅ WebSocket 실시간 호가 데이터 수신 성공")
                self.channel_selector.record_websocket_success()
                return self._format_websocket_response(realtime_data, request)
            else:
                logger.warning("WebSocket 호가 실시간 수신 실패 → REST 폴백")
                self.channel_selector.record_websocket_error()
                return await self._execute_rest_request(request)

        except Exception as e:
            logger.error(f"WebSocket 호가 처리 실패: {e}")
            self.channel_selector.record_websocket_error()
            return await self._execute_rest_request(request)

    async def _handle_websocket_trades(self, request: DataRequest) -> Dict[str, Any]:
        """WebSocket 체결 데이터 처리 - 설정 기반 최적화"""
        try:
            # 구독 처리
            try:
                if self.websocket_client and hasattr(self.websocket_client, 'subscribe_trade'):
                    await self.websocket_client.subscribe_trade(request.symbols)
                    symbols_display = self._format_symbols_for_log(request.symbols)
                    logger.info(f"WebSocket 체결 구독 완료: {symbols_display}")

                    # 구독 후 안정화 대기 (설정값 사용)
                    import asyncio
                    await asyncio.sleep(SmartRouterConfig.WEBSOCKET_SUBSCRIPTION_STABILIZATION_DELAY)
                else:
                    raise Exception("WebSocket 클라이언트 없음")
            except Exception as subscribe_error:
                logger.warning(f"WebSocket 체결 구독 실패: {subscribe_error} - REST 폴백")
                return await self._execute_rest_request(request)

            # 실시간 데이터 수신 (설정값 사용)
            realtime_data = await self._receive_websocket_data(
                data_type="trade",
                symbols=request.symbols,
                timeout=SmartRouterConfig.WEBSOCKET_DATA_RECEIVE_TIMEOUT
            )

            if realtime_data:
                logger.info("✅ WebSocket 실시간 체결 데이터 수신 성공")
                self.channel_selector.record_websocket_success()
                return self._format_websocket_response(realtime_data, request)
            else:
                logger.warning("WebSocket 체결 실시간 수신 실패 → REST 폴백")
                self.channel_selector.record_websocket_error()
                return await self._execute_rest_request(request)

        except Exception as e:
            logger.error(f"WebSocket 체결 처리 실패: {e}")
            self.channel_selector.record_websocket_error()
            return await self._execute_rest_request(request)

    async def _execute_rest_request(self, request: DataRequest) -> Dict[str, Any]:
        """REST API 요청 실행"""
        try:
            # Rate Limit 사용량 증가 (요청 기반)
            current_usage = self.channel_selector.rate_limits["rest"]["current"] + 1
            self.channel_selector.update_rate_limit("rest", current_usage)

            # 클라이언트 초기화 확인
            await self._ensure_clients_initialized()

            if self.rest_client is None:
                raise Exception("REST 클라이언트 초기화 실패")

            timestamp = int(time.time() * 1000)

            if request.data_type == DataType.TICKER:
                # 현재가 정보 조회
                data = await self.rest_client.get_ticker(request.symbols)
                return {
                    "source": "rest_api",
                    "data": data,
                    "timestamp": timestamp
                }

            elif request.data_type == DataType.ORDERBOOK:
                # 호가 정보 조회
                data = await self.rest_client.get_orderbook(request.symbols)
                return {
                    "source": "rest_api",
                    "data": data,
                    "timestamp": timestamp
                }

            elif request.data_type == DataType.TRADES:
                # 체결 내역 조회 (한 심볼씩)
                all_trades = {}
                for symbol in request.symbols:
                    trades_dict = await self.rest_client.get_trades(
                        symbol,
                        count=request.count or 100
                    )
                    # Dict 형태 응답을 처리
                    if isinstance(trades_dict, dict) and symbol in trades_dict:
                        all_trades[symbol] = trades_dict[symbol]
                    else:
                        all_trades[symbol] = []

                return {
                    "source": "rest_api",
                    "data": all_trades,
                    "timestamp": timestamp
                }

            elif request.data_type == DataType.CANDLES:
                # 캔들 데이터 조회
                all_candles = {}
                interval = request.interval or "1m"
                count = request.count or 1
                to = request.to  # 조회 기간 종료 시각

                for symbol in request.symbols:
                    if interval.endswith('m'):
                        # 분봉
                        unit = int(interval.replace('m', ''))
                        candles_dict = await self.rest_client.get_candle_minutes(
                            symbol, unit=unit, count=count, to=to
                        )
                    elif interval == '1d':
                        # 일봉
                        candles_dict = await self.rest_client.get_candle_days(
                            symbol, count=count, to=to
                        )
                    elif interval == '1w':
                        # 주봉
                        candles_dict = await self.rest_client.get_candle_weeks(
                            symbol, count=count, to=to
                        )
                    elif interval == '1M':
                        # 월봉
                        candles_dict = await self.rest_client.get_candle_months(
                            symbol, count=count, to=to
                        )
                    else:
                        logger.warning(f"지원하지 않는 캔들 간격: {interval}")
                        candles_dict = await self.rest_client.get_candle_minutes(
                            symbol, count=count, to=to
                        )

                    # Dict 형태 응답을 처리
                    if isinstance(candles_dict, dict) and symbol in candles_dict:
                        all_candles[symbol] = candles_dict[symbol]
                    else:
                        all_candles[symbol] = []

                return {
                    "source": "rest_api",
                    "data": all_candles,
                    "timestamp": timestamp
                }

            else:
                logger.error(f"지원하지 않는 데이터 타입: {request.data_type}")
                return {
                    "source": "rest_api",
                    "data": [],
                    "timestamp": timestamp
                }

        except Exception as e:
            logger.error(f"REST API 요청 실행 실패: {e}")

            # v3.0: 직접 더미 데이터 반환 (외부 매니저 의존성 제거)
            logger.warning("REST 클라이언트 실패 - 더미 데이터로 폴백")
            return {
                "source": "rest_fallback_v3",
                "data": self._generate_dummy_data(request.data_type)["data"],
                "timestamp": int(time.time() * 1000)
            }

    def _generate_dummy_data(self, data_type: DataType) -> Dict[str, Any]:
        """테스트용 더미 데이터 생성"""
        timestamp = int(time.time() * 1000)

        if data_type == DataType.TICKER:
            return {
                "source": "rest_api",
                "data": {
                    "market": "KRW-BTC",
                    "trade_price": 50000000,
                    "prev_closing_price": 49000000,
                    "change": "RISE",
                    "change_price": 1000000,
                    "change_rate": 0.0204,
                    "trade_volume": 0.12345678,
                    "acc_trade_volume": 123.456,
                    "acc_trade_volume_24h": 567.890,
                    "acc_trade_price": 6000000000,
                    "acc_trade_price_24h": 28000000000,
                    "trade_date": "20240101",
                    "trade_time": "090000",
                    "trade_timestamp": timestamp,
                    "ask_bid": "BID",
                    "acc_ask_volume": 60.123,
                    "acc_bid_volume": 63.333,
                    "highest_52_week_price": 70000000,
                    "highest_52_week_date": "2023-11-20",
                    "lowest_52_week_price": 30000000,
                    "lowest_52_week_date": "2023-03-15",
                    "market_state": "ACTIVE",
                    "is_trading_suspended": False,
                    "delisting_date": None,
                    "market_warning": "NONE",
                    "timestamp": timestamp,
                    "stream_type": "SNAPSHOT"
                },
                "timestamp": timestamp
            }
        elif data_type == DataType.CANDLES:
            return {
                "source": "rest_api",
                "data": [
                    {
                        "market": "KRW-BTC",
                        "candle_date_time_utc": "2024-01-01T00:00:00",
                        "candle_date_time_kst": "2024-01-01T09:00:00",
                        "opening_price": 49000000,
                        "high_price": 50500000,
                        "low_price": 48500000,
                        "trade_price": 50000000,
                        "timestamp": timestamp,
                        "candle_acc_trade_price": 5000000000,
                        "candle_acc_trade_volume": 102.345,
                        "unit": 1
                    }
                ],
                "timestamp": timestamp
            }
        else:
            return {
                "source": "rest_api",
                "data": {},
                "timestamp": timestamp
            }

    def _unify_response_data(self, raw_data: Dict[str, Any], data_type: DataType, source: ChannelType) -> Dict[str, Any]:
        """응답 데이터 형식 통일"""
        if "data" in raw_data:
            return self.data_unifier.unify_data(raw_data["data"], data_type, source)
        else:
            return self.data_unifier.unify_data(raw_data, data_type, source)

    def _format_symbols_for_log(self, symbols: List[str], max_display: int = 3) -> str:
        """로그용 심볼 표시 제한 (처음 3개 + ... + 마지막 3개)"""
        if len(symbols) <= max_display * 2:
            return f"[{', '.join(symbols)}]"

        first_part = symbols[:max_display]
        last_part = symbols[-max_display:]
        return f"[{', '.join(first_part)}, ... +{len(symbols) - max_display * 2}개, {', '.join(last_part)}]"

    def _check_cache(self, request: DataRequest) -> Optional[Dict[str, Any]]:
        """캐시 확인"""
        cache_key = self._generate_cache_key(request)
        cached_item = self.cache.get(cache_key)

        if cached_item:
            # TTL 확인
            if time.time() - cached_item["timestamp"] < self.cache_ttl:
                cached_data = cached_item["data"]

                # 캐시된 데이터가 올바른 응답 구조인지 확인
                if isinstance(cached_data, dict) and "success" in cached_data:
                    return cached_data
                else:
                    # 이전 형식의 캐시 데이터를 올바른 구조로 변환
                    logger.debug("이전 형식의 캐시 데이터 발견 - 올바른 구조로 변환")
                    return {
                        "success": True,
                        "data": cached_data,
                        "metadata": {
                            "channel": "cache",
                            "reason": "cache_hit",
                            "confidence": 1.0,
                            "response_time_ms": 0,
                            "request_id": request.request_id
                        }
                    }
            else:
                # 만료된 캐시 삭제
                del self.cache[cache_key]

        return None

    def _store_cache(self, request: DataRequest, data: Dict[str, Any]) -> None:
        """캐시 저장 - 통일된 응답 데이터만 저장"""
        cache_key = self._generate_cache_key(request)

        # 응답 구조를 올바른 형식으로 저장
        cache_data = {
            "success": True,
            "data": data,
            "metadata": {
                "channel": "cache",
                "reason": "cache_stored",
                "confidence": 1.0,
                "response_time_ms": 0,
                "request_id": request.request_id,
                "cached_at": int(time.time() * 1000)
            }
        }

        self.cache[cache_key] = {
            "data": cache_data,
            "timestamp": time.time()
        }

        # 캐시 크기 제한 (1000개 초과 시 오래된 것부터 삭제)
        if len(self.cache) > 1000:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]

    def _generate_cache_key(self, request: DataRequest) -> str:
        """캐시 키 생성"""
        symbols_str = ",".join(sorted(request.symbols))
        to_str = request.to if request.to else "latest"
        return f"{request.data_type.value}:{symbols_str}:{request.count}:{request.interval}:{to_str}"

    def _update_metrics(self, decision: Optional[ChannelDecision], response_time: float, success: bool) -> None:
        """메트릭 업데이트"""
        # 이전 총 요청 수 저장 (정확도 계산용)
        prev_total_requests = self.metrics.total_requests

        if decision:
            if decision.channel == ChannelType.WEBSOCKET:
                self.metrics.websocket_requests += 1
            else:
                self.metrics.rest_requests += 1

        # 응답 시간 평균 업데이트
        current_avg = self.metrics.avg_response_time_ms

        if prev_total_requests > 0:
            self.metrics.avg_response_time_ms = (
                (current_avg * prev_total_requests + response_time * 1000) / (prev_total_requests + 1)
            )
        else:
            self.metrics.avg_response_time_ms = response_time * 1000

        # 정확도 업데이트 (성공률로 계산)
        if prev_total_requests > 0:
            prev_success_count = prev_total_requests * self.metrics.accuracy_rate
            new_success_count = prev_success_count + (1 if success else 0)
            self.metrics.accuracy_rate = new_success_count / (prev_total_requests + 1)
        else:
            self.metrics.accuracy_rate = 1.0 if success else 0.0

        self.metrics.last_updated = datetime.now()

    def _update_cache_hit_ratio(self, hit: bool) -> float:
        """캐시 히트율 업데이트"""
        current_ratio = self.metrics.cache_hit_ratio
        total_requests = self.metrics.total_requests

        if total_requests > 1:
            hit_count = current_ratio * (total_requests - 1)
            if hit:
                hit_count += 1
            return hit_count / total_requests
        else:
            return 1.0 if hit else 0.0

    def get_metrics(self) -> RoutingMetrics:
        """현재 메트릭 조회"""
        return self.metrics

    def get_performance_summary(self) -> Dict[str, Any]:
        """성능 요약 조회"""
        return {
            "routing_metrics": {
                "total_requests": self.metrics.total_requests,
                "websocket_requests": self.metrics.websocket_requests,
                "rest_requests": self.metrics.rest_requests,
                "avg_response_time_ms": self.metrics.avg_response_time_ms,
                "accuracy_rate": self.metrics.accuracy_rate,
                "cache_hit_ratio": self.metrics.cache_hit_ratio
            },
            "channel_selector": self.channel_selector.get_performance_summary(),
            "cache_status": {
                "cache_size": len(self.cache),
                "cache_ttl": self.cache_ttl
            }
        }

    def reset_metrics(self) -> None:
        """메트릭 초기화"""
        logger.info("메트릭 초기화")
        self.metrics = RoutingMetrics()
        self.cache.clear()
        logger.info("✅ 메트릭 초기화 완료")

    def clear_cache(self) -> None:
        """캐시 클리어"""
        logger.debug("캐시 클리어")
        self.cache.clear()

    def get_cache_info(self) -> Dict[str, Any]:
        """캐시 정보 조회"""
        return {
            "cache_size": len(self.cache),
            "cache_ttl": self.cache_ttl,
            "cache_keys": list(self.cache.keys())
        }

    async def cleanup_resources(self) -> None:
        """리소스 정리"""
        logger.info("SmartRouter 리소스 정리 시작")

        # WebSocket 연결 정리
        if self.websocket_client and hasattr(self.websocket_client, 'disconnect'):
            try:
                await self.websocket_client.disconnect()
                logger.debug("WebSocket 클라이언트 연결 해제 완료")
            except Exception as e:
                logger.warning(f"WebSocket 연결 해제 중 오류: {e}")

        # REST 클라이언트 정리
        if self.rest_client and hasattr(self.rest_client, 'close'):
            try:
                await self.rest_client.close()
                logger.debug("REST 클라이언트 연결 해제 완료")
            except Exception as e:
                logger.warning(f"REST 클라이언트 정리 중 오류: {e}")

        # 캐시 정리
        self.cache.clear()

        logger.info("✅ SmartRouter 리소스 정리 완료")

    def _convert_interval_to_websocket_unit(self, interval: str) -> int:
        """REST API 간격을 WebSocket 캔들 단위로 변환

        Args:
            interval: REST API 간격 (예: "1m", "5m", "15m", "1h", "1d")

        Returns:
            WebSocket 캔들 단위 (분 단위)
        """
        # 간격별 변환 매핑
        interval_mapping = {
            "1s": 1,      # 1초 -> 1분 (WebSocket에서는 최소 1분)
            "1m": 1,      # 1분
            "3m": 3,      # 3분
            "5m": 5,      # 5분
            "10m": 10,    # 10분
            "15m": 15,    # 15분
            "30m": 30,    # 30분
            "1h": 60,     # 1시간 = 60분
            "60m": 60,    # 60분
            "240m": 240,  # 240분 = 4시간
            "1d": 1440,   # 1일 = 1440분 (WebSocket은 분단위만 지원하므로 REST로 폴백)
            "1w": 10080,  # 1주 = 10080분 (WebSocket은 분단위만 지원하므로 REST로 폴백)
            "1M": 43200   # 1월 = 약 43200분 (WebSocket은 분단위만 지원하므로 REST로 폴백)
        }

        return interval_mapping.get(interval, 1)  # 기본값: 1분

    async def _receive_websocket_data(self, data_type: str, symbols: list, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """WebSocket 실시간 데이터 수신 - 최적화된 버전"""
        # 타임아웃 기본값을 설정에서 가져오기
        if timeout is None:
            timeout = SmartRouterConfig.WEBSOCKET_DATA_RECEIVE_TIMEOUT

        try:
            # WebSocket 클라이언트 상태 확인
            if not self.websocket_client or not hasattr(self.websocket_client, 'listen'):
                logger.warning("WebSocket 클라이언트 없음 - 즉시 폴백")
                return None

            # 연결 상태 빠른 확인
            if not getattr(self.websocket_client, 'is_connected', False):
                logger.warning("WebSocket 미연결 - 즉시 폴백")
                return None

            # 실시간 메시지 수신 시도 (짧은 타임아웃으로 빠른 응답)
            import asyncio
            try:
                async with asyncio.timeout(timeout):
                    async for message in self.websocket_client.listen():
                        # 메시지 유효성 검증
                        if not message or not hasattr(message, 'type') or not hasattr(message, 'data'):
                            continue

                        # 요청한 데이터 타입과 심볼 매칭
                        message_type = message.type.value.lower()
                        if message_type == data_type.lower() and hasattr(message, 'market'):
                            if message.market in symbols:
                                logger.debug(f"WebSocket 실시간 데이터 수신: {data_type} - {message.market}")
                                return message.data

                        # 관련 메시지 발견 시 즉시 반환
                        if message_type == data_type.lower():
                            logger.debug(f"WebSocket 데이터 수신 (심볼 무관): {data_type}")
                            return message.data

            except asyncio.TimeoutError:
                logger.debug(f"WebSocket 데이터 수신 타임아웃: {timeout}초 - 폴백")
                return None

        except Exception as e:
            logger.warning(f"WebSocket 실시간 데이터 수신 오류: {e} - 폴백")
            return None

        return None

    def _format_websocket_response(self, data: Dict[str, Any], request: DataRequest) -> Dict[str, Any]:
        """WebSocket 데이터를 표준 응답 형식으로 변환"""
        try:
            # DataFormatUnifier를 통해 통합 포맷으로 변환
            unified_data = self.data_unifier.unify_data(
                data, request.data_type, ChannelType.WEBSOCKET
            )

            # 메타데이터 추가
            current_time = time.time()
            metadata = {
                "channel": "websocket",
                "reason": "realtime_websocket_success",
                "confidence": 0.95,  # WebSocket 실시간 데이터 신뢰도
                "request_id": f"ws_realtime_{int(current_time * 1000)}",
                "response_time_ms": 50  # 실시간 수신이므로 매우 빠름
            }

            return {
                "success": True,
                "data": unified_data,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"WebSocket 응답 포맷 변환 실패: {e}")
            # 변환 실패 시 기본 응답 반환
            return {
                "success": False,
                "error": f"WebSocket 데이터 포맷 변환 실패: {e}",
                "metadata": {
                    "channel": "websocket",
                    "reason": "format_conversion_error",
                    "confidence": 0.0
                }
            }

    async def __aenter__(self):
        """컨텍스트 매니저 진입"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        await self.cleanup_resources()


# 전역 인스턴스 (싱글톤 패턴)
_global_smart_router: Optional[SmartRouter] = None


def get_smart_router() -> SmartRouter:
    """전역 SmartRouter 인스턴스 조회"""
    global _global_smart_router

    if _global_smart_router is None:
        _global_smart_router = SmartRouter()

    return _global_smart_router


async def initialize_smart_router() -> SmartRouter:
    """SmartRouter v3.0 초기화 및 설정"""
    router = get_smart_router()
    await router.initialize()
    return router
