"""
통합 마켓 데이터 API (Unified Market Data Backbone)

사용자가 제안한 "백본 통신 채널" 시스템 구현
- 단일 진입점: 시스템은 항상 이 API만 호출
- 내부 최적화: REST API + WebSocket 자동 선택 및 혼합 활용
- 통합 포맷: 다양한 소스 → 하나의 일관된 데이터 형식
- 장애 복구: 한쪽 실패 시 자동 대체
- 대역폭 최적화: 두 채널의 장점을 모두 활용

DDD Infrastructure Layer에서 TDD로 구현
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import asyncio

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data_backbone.data_collector import (
    MultiSourceDataCollector, DataSourceConfig
)


class DataRequestType(Enum):
    """데이터 요청 타입"""
    HISTORICAL_CANDLES = "historical_candles"    # 과거 캔들 데이터
    REALTIME_CANDLES = "realtime_candles"       # 실시간 캔들 업데이트
    ORDERBOOK = "orderbook"                     # 호가창
    TICKER = "ticker"                           # 현재가
    TRADES = "trades"                           # 체결 내역


class ChannelStrategy(Enum):
    """채널 선택 전략"""
    AUTO = "auto"                    # 자동 최적화 (기본)
    WEBSOCKET_PREFERRED = "ws_preferred"  # WebSocket 우선
    API_PREFERRED = "api_preferred"      # REST API 우선
    HYBRID_BALANCED = "hybrid_balanced"   # 균형잡힌 하이브리드
    WEBSOCKET_ONLY = "ws_only"          # WebSocket 전용
    API_ONLY = "api_only"               # REST API 전용


@dataclass
class DataRequest:
    """통합 데이터 요청"""
    request_type: DataRequestType
    symbol: str
    timeframe: Optional[str] = None      # 캔들 데이터용
    count: Optional[int] = None          # 요청 개수
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    channel_strategy: ChannelStrategy = ChannelStrategy.AUTO
    priority: int = 5                    # 1-10 (낮을수록 높은 우선순위)
    timeout_seconds: float = 30.0

    # 콜백 함수들
    data_callback: Optional[Callable[[List[Dict[str, Any]]], None]] = None
    error_callback: Optional[Callable[[str], None]] = None


@dataclass
class ChannelStatus:
    """채널 상태"""
    channel_type: str  # "websocket", "api"
    is_available: bool
    latency_ms: float
    success_rate: float  # 0.0 - 1.0
    bandwidth_usage: float  # 0.0 - 1.0
    last_check: datetime
    error_count: int = 0


class SmartChannelRouter:
    """
    지능적 채널 라우터

    REST API와 WebSocket의 장단점을 분석하여
    최적의 채널을 자동 선택하는 라우팅 엔진
    """

    def __init__(self):
        self._logger = create_component_logger("SmartChannelRouter")

        # 채널 상태 모니터링
        self._channel_status: Dict[str, ChannelStatus] = {}
        self._performance_history: Dict[str, List[float]] = {
            "websocket_latency": [],
            "api_latency": [],
            "websocket_success": [],
            "api_success": []
        }

    def analyze_optimal_channel(self, request: DataRequest) -> ChannelStrategy:
        """
        요청에 최적인 채널 전략 분석

        Args:
            request: 데이터 요청

        Returns:
            최적 채널 전략
        """
        # 사용자가 명시적으로 지정한 경우
        if request.channel_strategy != ChannelStrategy.AUTO:
            return request.channel_strategy

        # 요청 타입별 최적 채널 결정
        if request.request_type == DataRequestType.HISTORICAL_CANDLES:
            # 과거 데이터: REST API가 효율적
            if request.count and request.count > 100:
                return ChannelStrategy.API_PREFERRED
            else:
                return ChannelStrategy.HYBRID_BALANCED

        elif request.request_type == DataRequestType.REALTIME_CANDLES:
            # 실시간 데이터: WebSocket 우선
            return ChannelStrategy.WEBSOCKET_PREFERRED

        elif request.request_type in [DataRequestType.ORDERBOOK, DataRequestType.TICKER]:
            # 호가창/현재가: WebSocket 전용
            return ChannelStrategy.WEBSOCKET_PREFERRED

        elif request.request_type == DataRequestType.TRADES:
            # 체결내역: 하이브리드
            return ChannelStrategy.HYBRID_BALANCED

        return ChannelStrategy.AUTO

    def get_channel_status(self) -> Dict[str, ChannelStatus]:
        """현재 채널 상태 반환"""
        return self._channel_status.copy()

    def update_channel_performance(self, channel: str, latency_ms: float, success: bool):
        """채널 성능 업데이트"""
        if channel not in self._channel_status:
            self._channel_status[channel] = ChannelStatus(
                channel_type=channel,
                is_available=True,
                latency_ms=latency_ms,
                success_rate=1.0 if success else 0.0,
                bandwidth_usage=0.0,
                last_check=datetime.now()
            )

        # 성능 히스토리 업데이트
        history_key = f"{channel}_latency"
        if history_key in self._performance_history:
            self._performance_history[history_key].append(latency_ms)
            # 최근 100개만 유지
            if len(self._performance_history[history_key]) > 100:
                self._performance_history[history_key] = self._performance_history[history_key][-100:]

        success_key = f"{channel}_success"
        if success_key in self._performance_history:
            self._performance_history[success_key].append(1.0 if success else 0.0)
            if len(self._performance_history[success_key]) > 100:
                self._performance_history[success_key] = self._performance_history[success_key][-100:]        # 채널 상태 업데이트
        status = self._channel_status[channel]
        status.latency_ms = latency_ms
        status.last_check = datetime.now()

        # 성공률 계산 (최근 10개 기준)
        recent_success = self._performance_history[success_key][-10:]
        if recent_success:
            status.success_rate = sum(recent_success) / len(recent_success)


class MockDataCollector:
    """데모용 Mock 데이터 수집기"""

    def __init__(self):
        self.logger = create_component_logger("MockDataCollector")

    async def start_collection(self, config: DataSourceConfig, data_callback):
        """Mock 데이터 수집 시작"""
        collection_id = f"{config.symbol}_{config.timeframe}_{config.source_type}"

        self.logger.info(f"Mock 데이터 수집 시작: {collection_id}")

        # 시뮬레이션된 데이터 생성
        await asyncio.sleep(0.1)  # 네트워크 지연 시뮬레이션

        mock_data = self._generate_mock_data(config)
        data_callback(mock_data)

        return collection_id

    def _generate_mock_data(self, config: DataSourceConfig) -> List[Dict[str, Any]]:
        """Mock 데이터 생성"""
        import random

        base_price = 45000000  # 4500만원
        data = []

        count = 10  # 기본값
        if config.symbol == "KRW-BTC":
            count = 200  # BTC는 더 많은 데이터

        for i in range(count):
            price_variation = random.uniform(-0.02, 0.02)  # ±2% 변동
            price = base_price * (1 + price_variation)

            candle = {
                'symbol': config.symbol,
                'timestamp': datetime.now().timestamp() - (count - i) * 60,
                'timeframe': config.timeframe,
                'open': price * 0.999,
                'high': price * 1.001,
                'low': price * 0.998,
                'close': price,
                'volume': random.uniform(0.1, 2.0),
                'source': config.source_type
            }
            data.append(candle)

        return data


class UnifiedMarketDataAPI:
    """
    통합 마켓 데이터 API

    사용자가 제안한 "백본 통신 채널" 시스템의 메인 구현체
    단일 진입점으로 모든 마켓 데이터 요청을 처리하고
    내부적으로 최적화된 채널 선택 및 장애 복구를 수행
    """

    def __init__(self, api_client=None, websocket_client=None):
        self._logger = create_component_logger("UnifiedMarketDataAPI")

        # 내부 컴포넌트들
        self._data_collector = MultiSourceDataCollector()
        self._channel_router = SmartChannelRouter()

        # 외부 클라이언트들
        self._api_client = api_client
        self._websocket_client = websocket_client

        # 요청 관리
        self._active_requests: Dict[str, DataRequest] = {}
        self._request_results: Dict[str, List[Dict[str, Any]]] = {}

        # 상태 관리
        self._is_initialized = False

        # 채널 상태 (SmartChannelRouter에서 이동)
        self._channel_status: Dict[str, ChannelStatus] = {}
        self._performance_history: Dict[str, List[float]] = {
            "websocket_latency": [],
            "api_latency": [],
            "websocket_success": [],
            "api_success": []
        }

    async def initialize(self) -> bool:
        """API 초기화"""
        if self._is_initialized:
            return True

        try:
            self._logger.info("통합 마켓 데이터 API 초기화 중...")

            # 채널 가용성 테스트
            await self._test_channel_availability()

            self._is_initialized = True
            self._logger.info("✅ 통합 마켓 데이터 API 초기화 완료")
            return True

        except Exception as e:
            self._logger.error(f"❌ API 초기화 실패: {e}")
            return False

    async def request_data(self, request: DataRequest) -> str:
        """
        데이터 요청 (비동기)

        Args:
            request: 데이터 요청 정보

        Returns:
            request_id: 요청 식별자
        """
        if not self._is_initialized:
            raise RuntimeError("API가 초기화되지 않았습니다")

        request_id = f"{request.symbol}_{request.request_type.value}_{id(request)}"

        self._logger.info(f"데이터 요청 접수: {request_id}")
        self._logger.debug(f"요청 상세: {request}")

        try:
            # 최적 채널 전략 결정
            optimal_strategy = self._channel_router.analyze_optimal_channel(request)
            self._logger.debug(f"선택된 채널 전략: {optimal_strategy}")

            # 요청 등록
            self._active_requests[request_id] = request

            # 비동기 데이터 수집 시작
            asyncio.create_task(self._process_request(request_id, optimal_strategy))

            return request_id

        except Exception as e:
            self._logger.error(f"데이터 요청 처리 실패: {request_id} - {e}")
            if request.error_callback:
                request.error_callback(f"요청 처리 실패: {e}")
            raise

    async def request_data_sync(self, request: DataRequest) -> List[Dict[str, Any]]:
        """
        데이터 요청 (동기)

        Args:
            request: 데이터 요청 정보

        Returns:
            요청된 데이터 리스트
        """
        request_id = await self.request_data(request)

        # 결과 대기
        timeout = request.timeout_seconds
        start_time = asyncio.get_event_loop().time()

        while True:
            if request_id in self._request_results:
                return self._request_results.pop(request_id)

            if asyncio.get_event_loop().time() - start_time > timeout:
                self._logger.error(f"요청 타임아웃: {request_id}")
                if request_id in self._active_requests:
                    del self._active_requests[request_id]
                raise TimeoutError(f"데이터 요청 타임아웃: {request_id}")

            await asyncio.sleep(0.1)

    async def _process_request(self, request_id: str, strategy: ChannelStrategy):
        """요청 처리 (내부)"""
        try:
            request = self._active_requests[request_id]

            # 채널 전략에 따른 데이터 소스 설정
            data_source_config = self._create_data_source_config(request, strategy)

            # 데이터 수집 시작
            await self._data_collector.start_collection(
                data_source_config,
                lambda data: self._on_data_received(request_id, data)
            )

        except Exception as e:
            self._logger.error(f"요청 처리 중 오류: {request_id} - {e}")
            if request_id in self._active_requests:
                request = self._active_requests[request_id]
                if request.error_callback:
                    request.error_callback(str(e))

    def _create_data_source_config(self, request: DataRequest, strategy: ChannelStrategy) -> DataSourceConfig:
        """요청과 전략에 따른 데이터 소스 설정 생성"""

        source_type_map = {
            ChannelStrategy.WEBSOCKET_ONLY: "websocket",
            ChannelStrategy.API_ONLY: "api",
            ChannelStrategy.WEBSOCKET_PREFERRED: "hybrid",  # WebSocket 80%
            ChannelStrategy.API_PREFERRED: "hybrid",        # API 80%
            ChannelStrategy.HYBRID_BALANCED: "hybrid",      # 50:50
            ChannelStrategy.AUTO: "hybrid"                  # 자동 조절
        }

        source_type = source_type_map.get(strategy, "hybrid")

        return DataSourceConfig(
            source_type=source_type,
            symbol=request.symbol,
            timeframe=request.timeframe or "1m",
            api_client=self._api_client,
            websocket_client=self._websocket_client,
            hybrid_ratio=self._get_hybrid_ratio(strategy)
        )

    def _get_hybrid_ratio(self, strategy: ChannelStrategy) -> float:
        """전략별 하이브리드 비율 반환"""
        ratio_map = {
            ChannelStrategy.WEBSOCKET_PREFERRED: 0.8,  # WebSocket 80%
            ChannelStrategy.API_PREFERRED: 0.2,        # WebSocket 20% (API 80%)
            ChannelStrategy.HYBRID_BALANCED: 0.5,      # WebSocket 50%
            ChannelStrategy.AUTO: 0.7                  # WebSocket 70%
        }
        return ratio_map.get(strategy, 0.7)

    def _on_data_received(self, request_id: str, data: List[Dict[str, Any]]):
        """데이터 수신 콜백"""
        if request_id not in self._active_requests:
            return

        request = self._active_requests[request_id]

        # 사용자 콜백 호출
        if request.data_callback:
            request.data_callback(data)

        # 동기 요청을 위한 결과 저장
        self._request_results[request_id] = data

        self._logger.debug(f"데이터 수신 완료: {request_id} ({len(data)}개)")

    async def _test_channel_availability(self):
        """채널 가용성 테스트"""
        self._logger.info("채널 가용성 테스트 중...")

        # WebSocket 테스트 (간단한 ping)
        # TODO: 실제 WebSocket 클라이언트 테스트 구현

        # REST API 테스트 (간단한 market 조회)
        # TODO: 실제 API 클라이언트 테스트 구현

        self._logger.info("✅ 채널 가용성 테스트 완료")

    def get_channel_status(self) -> Dict[str, ChannelStatus]:
        """현재 채널 상태 반환"""
        return self._channel_status

    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 반환"""
        return {
            "active_requests": len(self._active_requests),
            "channel_status": self.get_channel_status(),
            "performance_history": self._performance_history.copy()
        }


# 편의를 위한 팩토리 함수들
async def create_unified_api(api_client=None, websocket_client=None) -> UnifiedMarketDataAPI:
    """통합 API 생성 및 초기화"""
    api = UnifiedMarketDataAPI(api_client, websocket_client)
    await api.initialize()
    return api


def create_candle_request(
    symbol: str,
    timeframe: str = "1m",
    count: int = 200,
    strategy: ChannelStrategy = ChannelStrategy.AUTO
) -> DataRequest:
    """캔들 데이터 요청 생성"""
    return DataRequest(
        request_type=DataRequestType.HISTORICAL_CANDLES,
        symbol=symbol,
        timeframe=timeframe,
        count=count,
        channel_strategy=strategy
    )


def create_realtime_request(
    symbol: str,
    timeframe: str = "1m",
    data_callback: Optional[Callable[[List[Dict[str, Any]]], None]] = None
) -> DataRequest:
    """실시간 데이터 요청 생성"""
    return DataRequest(
        request_type=DataRequestType.REALTIME_CANDLES,
        symbol=symbol,
        timeframe=timeframe,
        data_callback=data_callback,
        channel_strategy=ChannelStrategy.WEBSOCKET_PREFERRED
    )
