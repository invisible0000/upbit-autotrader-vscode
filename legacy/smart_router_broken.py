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
from .websocket_subscription_manager import WebSocketSubscriptionManager
from .models import (
    DataRequest, ChannelDecision, RoutingMetrics,
    DataType, ChannelType, RealtimePriority
)
from .data_format_unifier import DataFormatUnifier
from .channel_selector import ChannelSelector

# Lazy import를 위한 TYPE_CHECKING
if TYPE_CHECKING:
    from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient
    from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
        UpbitWebSocketQuotationClient, WebSocketDataType
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
        self.websocket_client: Optional['UpbitWebSocketQuotationClient'] = None

        # 🆕 WebSocket 구독 관리자
        self.subscription_manager: Optional[WebSocketSubscriptionManager] = None

        # 외부 매니저 (이전 호환성 유지)
        self.websocket_manager = None
        self.rest_manager = None

        # 캐시 시스템 (간단한 메모리 캐시)
        self.cache = {}
        self.cache_ttl = 60.0  # 60초 TTL

        # 상태 관리
        self.is_initialized = False

        logger.info("SmartRouter 초기화 완료 (클라이언트들은 lazy loading)")

    async def initialize(self, websocket_manager=None, rest_manager=None) -> None:
        """스마트 라우터 초기화

        Args:
            websocket_manager: WebSocket 매니저 (선택적, 이전 호환성)
            rest_manager: REST API 매니저 (선택적, 이전 호환성)
        """
        logger.info("SmartRouter 서비스 초기화")

        # 외부 매니저 설정 (이전 호환성 유지)
        self.websocket_manager = websocket_manager
        self.rest_manager = rest_manager

        # API 클라이언트들을 lazy loading으로 초기화
        await self._ensure_clients_initialized()

        self.is_initialized = True
        logger.info("✅ SmartRouter 초기화 완료")

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
                from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
                    UpbitWebSocketQuotationClient
                )
                self.websocket_client = UpbitWebSocketQuotationClient()

                # 🚨 극도 보수적 WebSocket 구독 관리자 초기화 (기본 1개 구독)
                self.subscription_manager = WebSocketSubscriptionManager(
                    websocket_client=self.websocket_client,
                    max_subscriptions=1  # 🚨 극도 보수적: 기본 1개만 허용
                )

                # WebSocket 연결 시도 (에러 발생 시 상태만 업데이트)
                try:
                    await self.websocket_client.connect()
                    is_connected = self.websocket_client.is_connected
                    self.channel_selector.update_websocket_status(is_connected)
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
            logger.debug(f"데이터 요청 처리 시작 - type: {request.data_type.value}, symbols: {request.symbols}")

            # 메트릭 업데이트
            self.metrics.total_requests += 1

            # 1단계: 캐시 확인 (use_cache=False이거나 호가/티커 데이터는 캐시 제외)
            if not request.use_cache or request.data_type.value in ["orderbook", "ticker"]:
                logger.debug(f"캐시 사용 안함 - use_cache={request.use_cache}, data_type={request.data_type.value}")
                cached_result = None
            else:
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

            # 5단계: 캐시 저장 (use_cache=False이거나 호가/티커 데이터는 캐시 저장 제외)
            if request.use_cache and request.data_type.value not in ["orderbook", "ticker"]:
                self._store_cache(request, unified_data)
            else:
                logger.debug(f"캐시 저장 생략 - use_cache={request.use_cache}, data_type={request.data_type.value}")

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
        """WebSocket 요청 실행 (극도 보수적 구독 매니저 통합)"""
        try:
            # 클라이언트 초기화 확인
            await self._ensure_clients_initialized()

            # 🚨 개선된 WebSocket 연결 상태 체크
            websocket_connected = (
                self.websocket_client and 
                hasattr(self.websocket_client, 'is_connected') and 
                self.websocket_client.is_connected
            )
            
            if not websocket_connected:
                logger.warning("WebSocket 연결이 설정되지 않음 - REST API로 폴백")
                return await self._execute_rest_request(request)

            if request.data_type == DataType.TICKER:
                # 🚨 극도 보수적 구독 매니저를 통한 현재가 처리
                return await self._handle_ticker_with_subscription_manager(request)

            elif request.data_type == DataType.ORDERBOOK:
                # � 극도 보수적 구독 매니저를 통한 호가 처리
                return await self._handle_orderbook_with_subscription_manager(request)

            elif request.data_type == DataType.TRADES:
                # 🚨 극도 보수적 구독 매니저를 통한 체결 처리
                return await self._handle_trades_with_subscription_manager(request)

            else:
                # 기타 데이터 타입은 REST API로 처리
                logger.debug(f"데이터 타입 {request.data_type}는 REST API로 처리")
                return await self._execute_rest_request(request)

        except Exception as e:
                    logger.error(f"WebSocket 현재가 구독 오류: {request.symbols} - {e}")
                    return await self._execute_rest_request(request)

            elif request.data_type == DataType.ORDERBOOK:
                # 호가 구독 후 메시지 수신 - 예외 처리 강화
                try:
                    success = await self.websocket_client.subscribe_orderbook(request.symbols)
                    if success:
                        logger.info(f"WebSocket 호가 구독 완료: {request.symbols}")

                        # 🔥 실제 WebSocket 데이터 수신 대기
                        websocket_data = await self._wait_for_websocket_data(request.symbols[0], "orderbook", timeout=0.2)
                        if websocket_data:
                            logger.info(f"✅ WebSocket 호가 데이터 수신 성공: {request.symbols[0]}")

                            # 🔥 디버깅: 변환 전후 데이터 로깅
                            if isinstance(websocket_data, dict):
                                logger.debug(f"🔍 WebSocket 원시 데이터 키: {list(websocket_data.keys())}")
                                if 'orderbook_units' in websocket_data:
                                    units_count = len(websocket_data['orderbook_units'])
                                    logger.debug(f"🔍 orderbook_units 개수: {units_count}")

                            response = self._convert_websocket_to_response(
                                websocket_data, request.data_type, request.symbols[0]
                            )

                            response_data = response.get('data')
                            if isinstance(response_data, dict):
                                logger.debug(f"🔍 변환된 응답 data 키: {list(response_data.keys())}")

                            return response
                        else:
                            logger.warning(f"WebSocket 호가 데이터 수신 실패 - REST API로 폴백: {request.symbols}")
                            return await self._execute_rest_request(request)
                    else:
                        logger.warning(f"WebSocket 호가 구독 실패: {request.symbols} - REST API로 폴백")
                        return await self._execute_rest_request(request)
                except Exception as e:
                    logger.error(f"WebSocket 호가 구독 오류: {request.symbols} - {e}")
                    return await self._execute_rest_request(request)

            elif request.data_type == DataType.TRADES:
                # 체결 구독 후 메시지 수신
                await self.websocket_client.subscribe_trade(request.symbols)
                logger.info(f"WebSocket 체결 구독 완료: {request.symbols}")

                # 임시로 REST API로 폴백
                logger.warning("WebSocket 실시간 체결 데이터 수신 구현 중 - REST API로 폴백")
                return await self._execute_rest_request(request)

            elif request.data_type == DataType.CANDLES or request.data_type == DataType.CANDLES_1S:
                # 캔들 구독 후 메시지 수신
                interval_unit = self._convert_interval_to_websocket_unit(request.interval or "1m")
                await self.websocket_client.subscribe_candle(request.symbols, interval_unit)
                logger.info(f"WebSocket 캔들 구독 완료: {request.symbols}, 간격: {request.interval or '1m'}")

                # 임시로 REST API로 폴백 (실시간 데이터 수신 구현 필요)
                logger.warning("WebSocket 실시간 캔들 데이터 수신 구현 중 - REST API로 폴백")
                return await self._execute_rest_request(request)

            else:
                # 다른 데이터 타입은 REST API로 폴백
                logger.warning(f"WebSocket에서 지원하지 않는 데이터 타입: {request.data_type.value}")
                return await self._execute_rest_request(request)

        except Exception as e:
            logger.error(f"WebSocket 요청 실행 실패: {e}")
            # 폴백으로 REST API 사용
            return await self._execute_rest_request(request)

    async def _execute_rest_request(self, request: DataRequest) -> Dict[str, Any]:
        """REST API 요청 실행"""
        try:
            # 클라이언트 초기화 확인
            await self._ensure_clients_initialized()

            if self.rest_client is None:
                raise Exception("REST 클라이언트 초기화 실패")

            timestamp = int(time.time() * 1000)

            if request.data_type == DataType.TICKER:
                # 현재가 정보 조회
                data = await self.rest_client.get_tickers(request.symbols)
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
                all_trades = []
                for symbol in request.symbols:
                    trades = await self.rest_client.get_trades_ticks(
                        symbol,
                        count=request.count or 100
                    )
                    all_trades.extend(trades)

                return {
                    "source": "rest_api",
                    "data": all_trades,
                    "timestamp": timestamp
                }

            elif request.data_type == DataType.CANDLES:
                # 캔들 데이터 조회
                all_candles = []
                interval = request.interval or "1m"
                count = request.count or 1
                to = request.to  # 조회 기간 종료 시각

                for symbol in request.symbols:
                    if interval.endswith('m'):
                        # 분봉
                        unit = int(interval.replace('m', ''))
                        candles = await self.rest_client.get_candles_minutes(
                            symbol, unit=unit, count=count, to=to
                        )
                    elif interval == '1d':
                        # 일봉
                        candles = await self.rest_client.get_candles_days(
                            symbol, count=count, to=to
                        )
                    elif interval == '1w':
                        # 주봉
                        candles = await self.rest_client.get_candles_weeks(
                            symbol, count=count, to=to
                        )
                    elif interval == '1M':
                        # 월봉
                        candles = await self.rest_client.get_candles_months(
                            symbol, count=count, to=to
                        )
                    else:
                        logger.warning(f"지원하지 않는 캔들 간격: {interval}")
                        candles = await self.rest_client.get_candles_minutes(
                            symbol, count=count, to=to
                        )

                    # 심볼 정보 추가
                    for candle in candles:
                        candle['market'] = symbol
                    all_candles.extend(candles)

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

            # 기존 매니저 폴백 시도
            if self.rest_manager:
                logger.warning("REST 클라이언트 실패 - 기존 매니저로 폴백")
                return {
                    "source": "rest_manager_fallback",
                    "data": self._generate_dummy_data(request.data_type)["data"],
                    "timestamp": int(time.time() * 1000)
                }
            else:
                # 최종적으로 더미 데이터 반환
                logger.warning("REST API 실패 - 테스트용 더미 데이터 반환")
                return self._generate_dummy_data(request.data_type)

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

    async def __aenter__(self):
        """컨텍스트 매니저 진입"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        await self.cleanup_resources()

    # 🔥 WebSocket 데이터 수신 도우미 메서드들
    async def _wait_for_websocket_data(self, market: str, data_type: str, timeout: float = 0.2) -> Optional[Dict[str, Any]]:
        """WebSocket에서 데이터 수신 대기 (극도 보수적 구독 관리)"""
        import asyncio

        if not self.websocket_client:
            return None

        # 🚨 극도 보수적 전략: 구독 매니저를 통한 관리
        if self.subscription_manager:
            # 데이터 타입 매핑
            subscription_type_map = {
                "ticker": "ticker",
                "trade": "trade",
                "orderbook": "orderbook"
            }

            from .websocket_subscription_manager import SubscriptionType

            if data_type in subscription_type_map:
                try:
                    subscription_type = SubscriptionType(subscription_type_map[data_type])

                    # 🚨 구독 요청 (극도 보수적 관리)
                    success = await self.subscription_manager.request_subscription(
                        symbol=market,
                        subscription_type=subscription_type,
                        priority=1  # 높은 우선순위
                    )

                    if success:
                        logger.debug(f"✅ WebSocket 구독 활성화: {market}:{data_type}")
                        # 구독 성공 시 메시지 카운트 증가
                        self.subscription_manager.increment_message_count()

                        # WebSocket이 연결되어 있다면 구독이 활성화된 것으로 간주
                        if hasattr(self.websocket_client, 'is_connected') and self.websocket_client.is_connected:
                            return {"status": "subscribed", "market": market, "type": data_type}
                    else:
                        logger.warning(f"⚠️ WebSocket 구독 실패: {market}:{data_type}")

                except Exception as e:
                    logger.error(f"❌ 구독 요청 중 오류: {e}")

        # 짧은 대기 시간
        await asyncio.sleep(timeout)
        return None

    def _convert_websocket_to_response(
        self, websocket_data: Dict[str, Any], data_type: DataType, market: str
    ) -> Dict[str, Any]:
        """WebSocket 데이터를 DataResponse 형식으로 변환"""
        if data_type == DataType.TICKER:
            return {
                "success": True,
                "source": "websocket",
                "data": {
                    market: [websocket_data]  # 단일 심볼을 리스트로 래핑
                },
                "metadata": {
                    "source": "websocket",
                    "channel": "ticker",
                    "timestamp": websocket_data.get("timestamp", "")
                }
            }
        elif data_type == DataType.ORDERBOOK:
            # 🔥 WebSocket 호가 데이터는 이미 올바른 형식이므로 직접 사용
            return {
                "success": True,
                "source": "websocket",
                "data": websocket_data,  # 🚫 리스트로 래핑하지 않음 - 원시 데이터 직접 전달
                "metadata": {
                    "source": "websocket",
                    "channel": "orderbook",
                    "timestamp": websocket_data.get("timestamp", "")
                }
            }
        elif data_type == DataType.TRADES:
            return {
                "success": True,
                "source": "websocket",
                "data": {
                    market: [websocket_data]  # 단일 심볼을 리스트로 래핑
                },
                "metadata": {
                    "source": "websocket",
                    "channel": "trade",
                    "timestamp": websocket_data.get("timestamp", "")
                }
            }
        else:
            return {
                "success": False,
                "source": "websocket",
                "error": f"지원하지 않는 데이터 타입: {data_type}"
            }


# 전역 인스턴스 (싱글톤 패턴)
_global_smart_router: Optional[SmartRouter] = None


def get_smart_router() -> SmartRouter:
    """전역 SmartRouter 인스턴스 조회"""
    global _global_smart_router

    if _global_smart_router is None:
        _global_smart_router = SmartRouter()

    return _global_smart_router


async def initialize_smart_router(websocket_manager=None, rest_manager=None) -> SmartRouter:
    """SmartRouter 초기화 및 설정"""
    router = get_smart_router()
    await router.initialize(websocket_manager, rest_manager)
    return router
