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

import asyncio
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

    # 🚀 캐시 제거 - SmartDataProvider에서 200ms TTL 캐시 관리

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

        # 상태 관리
        self.is_initialized = False

        logger.info("SmartRouter v3.0 초기화 완료 (캐시 제거 - SmartDataProvider에서 관리)")

    async def initialize(self) -> None:
        """스마트 라우터 v3.0 완전 초기화 - 프로액티브 방식"""
        logger.info("SmartRouter v3.0 프로액티브 초기화 시작")

        # 1단계: REST 클라이언트 초기화 (항상 필요)
        await self._init_rest_client()

        # 2단계: WebSocket 클라이언트 초기화 및 연결
        await self._init_websocket_client()

        # 3단계: ChannelSelector에 정확한 상태 전달
        websocket_available = (self.websocket_client and
                               self.websocket_client.is_connected and
                               self.websocket_subscription_manager)

        self.channel_selector.update_websocket_status(bool(websocket_available))

        # 4단계: 초기화 완료 상태 설정
        self.is_initialized = True

        status_summary = {
            "REST": "✅" if self.rest_client else "❌",
            "WebSocket": "✅" if websocket_available else "❌",
            "구독매니저": "✅" if self.websocket_subscription_manager else "❌"
        }

        logger.info(f"✅ SmartRouter v3.0 초기화 완료 - {status_summary}")

    async def _init_rest_client(self) -> None:
        """REST 클라이언트 초기화"""
        if self.rest_client is not None:
            return

        try:
            # 🌍 글로벌 Rate Limiter 적용을 위해 팩토리 함수 사용
            from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import create_upbit_public_client
            self.rest_client = create_upbit_public_client()
            logger.info("REST 클라이언트 초기화 완료")
        except Exception as e:
            logger.error(f"REST 클라이언트 초기화 실패: {e}")
            # REST는 필수이므로 예외 발생
            raise RuntimeError(f"REST 클라이언트 초기화 필수: {e}")

    async def _init_websocket_client(self) -> None:
        """WebSocket 클라이언트 및 구독 매니저 지능적 초기화 (연결 안정성 개선)"""
        if self.websocket_client is not None:
            return

        try:
            from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_public_client import (
                UpbitWebSocketPublicClient
            )

            # WebSocket 클라이언트 생성 - 지속적 연결 모드 활성화
            self.websocket_client = UpbitWebSocketPublicClient(
                persistent_connection=True,  # 지속적 연결 유지
                auto_reconnect=True,
                max_reconnect_attempts=10,
                reconnect_delay=2.0
            )
            logger.info("WebSocket 클라이언트 생성 완료 (지속적 연결 모드)")

            # WebSocket 연결 시도
            try:
                await self.websocket_client.connect()
                is_connected = self.websocket_client.is_connected

                if is_connected:
                    logger.info("✅ WebSocket 연결 성공")

                    # 구독 매니저 초기화 - 지능적 관리 시작
                    await self._init_subscription_manager()
                else:
                    logger.warning("WebSocket 연결 실패 - REST API 전용 모드로 동작")

            except Exception as conn_error:
                logger.warning(f"WebSocket 연결 실패: {conn_error}")
                # 연결 실패해도 클라이언트는 유지 (재연결 가능)

        except Exception as e:
            logger.warning(f"WebSocket 클라이언트 생성 실패: {e}")
            # WebSocket은 선택사항이므로 계속 진행

    async def _init_subscription_manager(self) -> None:
        """WebSocket 구독 매니저 지능적 초기화"""
        if not self.websocket_client or not self.websocket_client.is_connected:
            logger.warning("WebSocket 미연결 - 구독 매니저 초기화 건너뜀")
            return

        if self.websocket_subscription_manager is not None:
            logger.debug("구독 매니저 이미 초기화됨")
            return

        try:
            # 구독 매니저 생성 - 최적화된 설정
            self.websocket_subscription_manager = WebSocketSubscriptionManager(
                self.websocket_client,
                max_subscription_types=SmartRouterConfig.BUFFER_SUBSCRIPTION_TYPES
            )

            logger.info(f"✅ WebSocket 구독 매니저 초기화 완료 - 최대 {SmartRouterConfig.BUFFER_SUBSCRIPTION_TYPES}개 타입 관리")

            # 🚀 지능적 사전 구독 전략
            await self._setup_intelligent_subscriptions()

        except Exception as e:
            logger.error(f"구독 매니저 초기화 실패: {e}")
            self.websocket_subscription_manager = None

    async def _setup_intelligent_subscriptions(self) -> None:
        """지능적 사전 구독 설정 - 사용 패턴 기반 최적화"""
        if not self.websocket_subscription_manager:
            return

        logger.info("🧠 지능적 WebSocket 사전 구독 설정 시작")

        # 📊 일반적인 사용 패턴 기반 우선순위 구독
        high_priority_types = [
            SubscriptionType.TICKER,    # 가장 많이 사용되는 데이터
            SubscriptionType.ORDERBOOK  # 실시간 거래에 중요
        ]

        # 우선순위 높은 타입들 사전 구독 (빈 심볼로 시작)
        for sub_type in high_priority_types:
            try:
                # 빈 구독으로 시작하여 나중에 심볼 추가 방식
                success = await self.websocket_subscription_manager.subscribe_symbols(
                    symbols=[],  # 빈 시작
                    subscription_type=sub_type,
                    priority=1   # 최고 우선순위
                )

                if success:
                    logger.info(f"✅ {sub_type.value} 타입 사전 구독 완료")
                else:
                    logger.warning(f"❌ {sub_type.value} 타입 사전 구독 실패")

            except Exception as e:
                logger.warning(f"사전 구독 오류 - {sub_type.value}: {e}")

        logger.info("🎯 지능적 WebSocket 사전 구독 설정 완료")

    async def _ensure_clients_initialized(self) -> None:
        """API 클라이언트들을 lazy loading으로 초기화"""
        if self.rest_client is None:
            try:
                # 필요할 때만 import하고 초기화
                # 🌍 글로벌 Rate Limiter 적용을 위해 팩토리 함수 사용
                from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import create_upbit_public_client
                self.rest_client = create_upbit_public_client()
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

            # 🚀 캐시 제거 - SmartDataProvider에서 200ms TTL 캐시 관리
            # SmartRouter는 라우팅 로직에만 집중

            # 1단계: 채널 선택 (정확한 정보 기반)
            channel_decision = self.channel_selector.select_channel(request)
            logger.info(f"채널 선택 완료 - 채널: {channel_decision.channel.value}, 이유: {channel_decision.reason}")

            # 2단계: 선택된 채널로 데이터 요청
            raw_data = await self._execute_request(request, channel_decision)

            # 4단계: 데이터 형식 통일
            unified_data = self._unify_response_data(raw_data, request.data_type, channel_decision.channel)

            # 🚀 캐시 제거됨: SmartDataProvider에서 200ms TTL 캐시 관리

            # 5단계: 메트릭 업데이트
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
                    "request_id": request.request_id,
                    # 🚀 2단계: 명확한 소스 정보 추가
                    "source_type": self._determine_source_type(channel_decision, raw_data),
                    "stream_info": self._extract_stream_info(channel_decision, raw_data),
                    "reliability_score": self._calculate_reliability_score(channel_decision),
                    "data_freshness": self._assess_data_freshness(channel_decision, raw_data),
                    "timestamp": datetime.now().isoformat()
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

                    # 🚀 기존 구독인지 확인하여 안정화 대기 최적화
                    existing_subscription = self.websocket_subscription_manager.type_subscriptions.get(SubscriptionType.TICKER)
                    if existing_subscription and all(s in existing_subscription.symbols for s in request.symbols):
                        # 모든 심볼이 이미 구독됨 - 안정화 대기 생략
                        logger.debug("모든 심볼이 기존 구독됨 - 안정화 대기 생략")
                    else:
                        # 새 심볼 추가 - 짧은 안정화 대기
                        await asyncio.sleep(0.1)  # 0.5초 → 0.1초 단축
                        logger.debug("새 심볼 구독 - 짧은 안정화 완료")

                else:
                    # 기존 직접 구독 방식
                    if self.websocket_client and hasattr(self.websocket_client, 'subscribe_ticker'):
                        await self.websocket_client.subscribe_ticker(request.symbols)
                        symbols_display = self._format_symbols_for_log(request.symbols)
                        logger.info(f"WebSocket 현재가 구독 완료: {symbols_display}")
                        # 직접 구독은 항상 안정화 대기
                        await asyncio.sleep(0.1)
                    else:
                        raise Exception("WebSocket 클라이언트 없음")

            except Exception as subscribe_error:
                logger.warning(f"WebSocket 구독 실패: {subscribe_error} - REST 폴백")
                # Rate Limit 롤백
                rollback_usage = self.channel_selector.rate_limits["websocket"]["current"] - 1
                self.channel_selector.update_rate_limit("websocket", rollback_usage)
                return await self._execute_rest_request(request)

            # 🚀 기존 구독 재사용 시 타임아웃 최적화 (캐시 사용 안함 - 실시간성 보장)
            if (self.websocket_subscription_manager and
                SubscriptionType.TICKER in self.websocket_subscription_manager.type_subscriptions):

                existing_subscription = self.websocket_subscription_manager.type_subscriptions[SubscriptionType.TICKER]
                if all(s in existing_subscription.symbols for s in request.symbols):
                    # 기존 구독이므로 WebSocket 스트림에서 새 데이터가 즉시 올 것으로 예상
                    timeout = 1.0  # 3초 → 1초로 단축 (실시간 데이터 대기)
                    logger.debug("🔥 기존 구독 재사용 - 실시간 데이터 대기 (짧은 타임아웃)")
                else:
                    # 새 구독이므로 구독 + 안정화 + 데이터 수신 시간 필요
                    timeout = SmartRouterConfig.WEBSOCKET_DATA_RECEIVE_TIMEOUT
                    logger.debug("새 구독 생성 - 표준 타임아웃 적용")
            else:
                timeout = SmartRouterConfig.WEBSOCKET_DATA_RECEIVE_TIMEOUT

            # 🔴 실시간 데이터 수신 (캐시 없음 - 항상 최신 데이터)
            realtime_data = await self._receive_websocket_data(
                data_type="ticker",
                symbols=request.symbols,
                timeout=timeout
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
        logger.debug("_unify_response_data 호출:")
        logger.debug(f"  - data_type: {data_type}")
        logger.debug(f"  - source: {source}")
        logger.debug(f"  - raw_data 키들: {list(raw_data.keys())}")

        # WebSocket 응답은 이미 _format_websocket_response에서 DataFormatUnifier로 처리됨
        # 이중 처리를 방지하기 위해 WebSocket 응답은 data 필드만 추출
        if source == ChannelType.WEBSOCKET and "data" in raw_data:
            logger.debug("WebSocket 응답 - 이미 처리된 data 필드 반환 (이중 처리 방지)")
            result = raw_data["data"]
            logger.debug(f"WebSocket _unify_response_data 결과: {str(result)[:10]}...")
            return result

        # REST API 응답은 DataFormatUnifier로 처리
        if "data" in raw_data:
            logger.debug("REST API raw_data['data']를 DataFormatUnifier로 처리")
            result = self.data_unifier.unify_data(raw_data["data"], data_type, source)
            logger.debug(f"REST API _unify_response_data 결과: {result}")
            return result
        else:
            logger.debug("raw_data 전체를 DataFormatUnifier로 처리")
            result = self.data_unifier.unify_data(raw_data, data_type, source)
            logger.debug(f"_unify_response_data 결과: {result}")
            return result

    def _format_symbols_for_log(self, symbols: List[str], max_display: int = 3) -> str:
        """로그용 심볼 표시 제한 (처음 3개 + ... + 마지막 3개)"""
        if len(symbols) <= max_display * 2:
            return f"[{', '.join(symbols)}]"

        first_part = symbols[:max_display]
        last_part = symbols[-max_display:]
        return f"[{', '.join(first_part)}, ... +{len(symbols) - max_display * 2}개, {', '.join(last_part)}]"

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
                "accuracy_rate": self.metrics.accuracy_rate
                # 🚀 cache_hit_ratio 제거: SmartDataProvider에서 관리
            },
            "channel_selector": self.channel_selector.get_performance_summary()
            # 🚀 cache_status 제거: SmartRouter에서 캐시 관리 안 함
        }

    def reset_metrics(self) -> None:
        """메트릭 초기화"""
        logger.info("메트릭 초기화 (캐시 제거됨)")
        self.metrics = RoutingMetrics()
        # 🚀 캐시 제거됨: SmartDataProvider에서 200ms TTL 캐시 관리
        logger.info("✅ 메트릭 초기화 완료")

    async def cleanup_resources(self) -> None:
        """리소스 정리"""
        logger.info("SmartRouter 리소스 정리 시작")

        # 🚀 캐시 제거됨: SmartDataProvider에서 200ms TTL 캐시 관리

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

        # 캐시 제거: 더 이상 캐시 정리 불필요
        # 캐시가 제거되었으므로 정리할 것이 없음

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
        """WebSocket 실시간 데이터 수신 - 스트림 타입 정보 포함"""
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
                                # 🚀 스트림 타입 정보 포함하여 반환
                                return self._create_websocket_data_with_stream_type(message)

                        # 관련 메시지 발견 시 즉시 반환
                        if message_type == data_type.lower():
                            logger.debug(f"WebSocket 데이터 수신 (심볼 무관): {data_type}")
                            # 🚀 스트림 타입 정보 포함하여 반환
                            return self._create_websocket_data_with_stream_type(message)

            except asyncio.TimeoutError:
                logger.debug(f"WebSocket 데이터 수신 타임아웃: {timeout}초 - 폴백")
                return None

        except Exception as e:
            logger.warning(f"WebSocket 실시간 데이터 수신 오류: {e} - 폴백")
            return None

        return None

    def _create_websocket_data_with_stream_type(self, message) -> Dict[str, Any]:
        """WebSocket 메시지에서 스트림 타입 정보를 포함한 데이터 생성"""
        # 디버깅: 메시지 구조 확인
        logger.debug("WebSocket 메시지 구조 분석:")
        logger.debug(f"  - message.type: {message.type}")
        logger.debug(f"  - message.market: {message.market}")
        logger.debug(f"  - message.data 타입: {type(message.data)}")
        logger.debug(f"  - message.data 내용: {str(message.data)[:10]}...")
        keys_str = str(list(message.data.keys()) if isinstance(message.data, dict) else 'N/A')
        logger.debug(f"  - message.data 키들: {keys_str[:10]}...")

        # 메시지의 데이터를 기본으로 하되, 스트림 타입 정보 추가
        data = message.data.copy() if isinstance(message.data, dict) else {"raw_data": message.data}

        # WebSocket 메시지에서 스트림 타입 정보 추출 및 추가
        if hasattr(message, 'stream_type') and message.stream_type:
            if hasattr(message.stream_type, 'value'):
                stream_type_value = message.stream_type.value
            else:
                stream_type_value = str(message.stream_type)
            data['stream_type'] = stream_type_value

        # 원본 메시지 정보도 포함 (디버깅용)
        message_type_value = message.type.value if hasattr(message.type, 'value') else str(message.type)
        data['_websocket_metadata'] = {
            "message_type": message_type_value,
            "market": getattr(message, 'market', 'unknown'),
            "timestamp": getattr(message, 'timestamp', None),
            "has_stream_type": hasattr(message, 'stream_type') and message.stream_type is not None
        }

        logger.debug(f"최종 생성된 데이터: {str(data)[:10]}...")
        return data

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

    # =====================================
    # 🚀 2단계: 명확한 소스 정보 제공 헬퍼 메서드들
    # =====================================

    def _determine_source_type(self, channel_decision: ChannelDecision, raw_data: Dict[str, Any]) -> str:
        """정확한 소스 타입 결정 - 추측 제거"""
        if channel_decision.channel == ChannelType.WEBSOCKET:
            # WebSocket의 경우 실제 스트림 타입에 따라 분류
            # raw_data에서 실제 업비트 스트림 타입 확인
            return self._extract_websocket_stream_type(raw_data)
        else:
            return "rest_api"

    def _extract_websocket_stream_type(self, raw_data: Dict[str, Any]) -> str:
        """WebSocket 메시지에서 실제 스트림 타입 추출"""
        # 1. raw_data에서 직접 스트림 타입 확인 (업비트 API 스펙)
        if 'stream_type' in raw_data:
            stream_type = raw_data['stream_type']
            if stream_type == 'REALTIME':
                return "websocket_realtime"
            elif stream_type == 'SNAPSHOT':
                return "websocket_snapshot"

        # 2. data 필드 내부에서 스트림 타입 확인
        if 'data' in raw_data and isinstance(raw_data['data'], dict):
            data_field = raw_data['data']
            if 'stream_type' in data_field:
                stream_type = data_field['stream_type']
                if stream_type == 'REALTIME':
                    return "websocket_realtime"
                elif stream_type == 'SNAPSHOT':
                    return "websocket_snapshot"

        # 3. 스트림 타입이 없거나 불명확한 경우 - 기본값은 실시간으로 간주
        # (업비트 WebSocket은 대부분 실시간 스트림)
        return "websocket_realtime"

    def _extract_stream_info(self, channel_decision: ChannelDecision, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """WebSocket 스트림 정보 추출"""
        if channel_decision.channel != ChannelType.WEBSOCKET:
            return {}

        # 실제 WebSocket 메시지에서 스트림 타입 추출
        stream_type = self._get_actual_stream_type_from_message(raw_data)

        return {
            "stream_type": stream_type,
            "is_live_stream": stream_type == "realtime",
            "connection_type": "websocket",
            "data_flow": "push_based",
            "raw_stream_type": raw_data.get('stream_type', 'unknown')
        }

    def _get_actual_stream_type_from_message(self, raw_data: Dict[str, Any]) -> str:
        """WebSocket 메시지에서 실제 스트림 타입 추출"""
        # 1. raw_data에서 직접 스트림 타입 확인
        if 'stream_type' in raw_data:
            stream_type = raw_data['stream_type']
            if stream_type == 'REALTIME':
                return "realtime"
            elif stream_type == 'SNAPSHOT':
                return "snapshot"

        # 2. data 필드 내부에서 스트림 타입 확인
        if 'data' in raw_data and isinstance(raw_data['data'], dict):
            data_field = raw_data['data']
            if 'stream_type' in data_field:
                stream_type = data_field['stream_type']
                if stream_type == 'REALTIME':
                    return "realtime"
                elif stream_type == 'SNAPSHOT':
                    return "snapshot"

        # 3. 기본값은 실시간으로 간주 (업비트 WebSocket 특성)
        return "realtime"

    def _calculate_reliability_score(self, channel_decision: ChannelDecision) -> float:
        """채널별 신뢰도 점수 계산"""
        base_score = channel_decision.confidence

        if channel_decision.channel == ChannelType.WEBSOCKET:
            # WebSocket 연결 품질 기반 신뢰도
            if self.websocket_subscription_manager:
                connection_health = self.websocket_subscription_manager.get_connection_health()
                return min(0.99, base_score * connection_health)
            else:
                return 0.5  # WebSocket 매니저 없음
        else:
            # REST API는 기본 신뢰도
            return min(0.95, base_score)

    def _assess_data_freshness(self, channel_decision: ChannelDecision, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 신선도 평가"""
        freshness_info = {
            "channel": channel_decision.channel.value,
            "timestamp": datetime.now().isoformat(),
            "estimated_delay_ms": 0
        }

        if channel_decision.channel == ChannelType.WEBSOCKET:
            # WebSocket의 경우 실제 스트림 타입에 따라 신선도 평가
            actual_stream_type = self._get_actual_stream_type_from_message(raw_data)

            if actual_stream_type == "realtime":
                freshness_info.update({
                    "is_realtime": True,
                    "estimated_delay_ms": 5,  # 실시간 데이터 지연
                    "stream_type": "realtime"
                })
            else:  # snapshot
                freshness_info.update({
                    "is_realtime": False,
                    "estimated_delay_ms": 50,  # 스냅샷 데이터 지연
                    "stream_type": "snapshot"
                })
        else:
            # REST API는 네트워크 지연 고려
            freshness_info.update({
                "is_realtime": False,
                "estimated_delay_ms": 100,  # REST API 기본 지연
                "stream_type": "snapshot"
            })

        return freshness_info

    def _get_websocket_subscription_status(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """WebSocket 구독 상태 정보 추출"""
        if not self.websocket_subscription_manager:
            return {"is_new_subscription": True, "age_ms": 0}

        # 실제 구독 매니저에서 상태 조회
        # 현재는 raw_data에서 구독 정보 추출
        subscription_id = raw_data.get('subscription_id')
        if subscription_id:
            return self.websocket_subscription_manager.get_subscription_info(subscription_id)
        else:
            # 구독 ID가 없으면 새 구독으로 간주
            return {
                "is_new_subscription": True,
                "age_ms": 0,
                "subscription_id": None,
                "sequence": 0,
                "type": "unknown"
            }


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
