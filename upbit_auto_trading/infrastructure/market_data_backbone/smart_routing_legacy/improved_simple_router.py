"""
개선된 스마트 라우팅 시스템

사용자 피드백을 반영한 안정적이고 직관적인 라우팅 전략:
1. 캔들 요청 패턴 최적화 (단일 최신값 vs 히스토리컬 데이터)
2. 데이터 검증 로직 개선
3. 비동기 처리 안정성 향상
4. 실패 복구 메커니즘 강화
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
import asyncio
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .core.adaptive_routing_engine import AdaptiveRoutingEngine
from .models import (
    RoutingRequest, RoutingContext,
    UsageContext, NetworkPolicy, DataType, TimeFrame
)

logger = create_component_logger("ImprovedSimpleRouter")


class RequestPattern(Enum):
    """요청 패턴 분류"""
    REALTIME_SINGLE = "realtime_single"  # 실시간 단일 데이터
    HISTORICAL_BATCH = "historical_batch"  # 히스토리컬 배치 데이터
    MIXED_USAGE = "mixed_usage"  # 혼합 사용


@dataclass
class SymbolUsageProfile:
    """심볼별 사용 프로필"""
    symbol: str
    request_history: List[Tuple[datetime, str, int]] = field(default_factory=list)  # (시간, 타입, 개수)
    last_pattern: Optional[RequestPattern] = None

    def add_request(self, request_type: str, count: int = 1):
        """요청 기록 추가"""
        self.request_history.append((datetime.now(), request_type, count))
        # 최근 50개만 유지
        if len(self.request_history) > 50:
            self.request_history = self.request_history[-50:]

        # 패턴 업데이트
        self._update_pattern()

    def _update_pattern(self):
        """사용 패턴 분석 및 업데이트"""
        if len(self.request_history) < 3:
            self.last_pattern = RequestPattern.MIXED_USAGE
            return

        recent_requests = self.request_history[-10:]

        # 실시간 패턴 검사 (5분 내 5회 이상, 주로 단일 요청)
        now = datetime.now()
        recent_5min = [r for r in recent_requests if (now - r[0]).total_seconds() < 300]

        if len(recent_5min) >= 5:
            single_requests = [r for r in recent_5min if r[2] <= 1]
            if len(single_requests) / len(recent_5min) > 0.7:  # 70% 이상 단일 요청
                self.last_pattern = RequestPattern.REALTIME_SINGLE
                return

        # 배치 패턴 검사 (대량 데이터 요청이 많음)
        batch_requests = [r for r in recent_requests if r[2] > 10]
        if len(batch_requests) / len(recent_requests) > 0.5:  # 50% 이상 배치 요청
            self.last_pattern = RequestPattern.HISTORICAL_BATCH
            return

        self.last_pattern = RequestPattern.MIXED_USAGE

    def get_optimal_strategy(self, request_type: str, count: int) -> Tuple[str, List[str]]:
        """최적 라우팅 전략 반환 (우선순위, Tier 목록)"""
        # 현재 요청의 특성
        is_single_latest = (request_type == "ticker" or (request_type == "candles" and count <= 1))
        is_batch_historical = (request_type == "candles" and count > 10)

        # 패턴 기반 전략 결정
        if is_single_latest:
            if self.last_pattern == RequestPattern.REALTIME_SINGLE:
                return "realtime_optimized", ["LIVE_SUBSCRIPTION", "BATCH_SNAPSHOT", "HOT_CACHE", "WARM_CACHE_REST"]
            else:
                return "mixed_realtime", ["HOT_CACHE", "LIVE_SUBSCRIPTION", "BATCH_SNAPSHOT", "WARM_CACHE_REST"]

        elif is_batch_historical:
            return "batch_optimized", ["COLD_REST", "WARM_CACHE_REST", "HOT_CACHE"]

        else:  # 중간 크기 요청
            return "balanced", ["HOT_CACHE", "WARM_CACHE_REST", "BATCH_SNAPSHOT", "COLD_REST"]


class ImprovedSimpleRouter:
    """개선된 사용자 친화적 스마트 라우팅 인터페이스

    주요 개선사항:
    - 요청 패턴 기반 자동 최적화
    - 안정적인 데이터 반환 보장
    - 비동기 처리 개선
    - 실패 복구 메커니즘
    """

    def __init__(self):
        """라우터 초기화"""
        logger.info("ImprovedSimpleRouter 초기화 시작")

        self._engine = AdaptiveRoutingEngine()
        self._profiles: Dict[str, SymbolUsageProfile] = {}
        self._is_started = False
        self._fallback_cache: Dict[str, Tuple[Any, datetime]] = {}  # 간단한 폴백 캐시

        logger.info("ImprovedSimpleRouter 초기화 완료")

    async def start(self) -> None:
        """라우터 시작"""
        if self._is_started:
            return

        try:
            await self._engine.start()
            self._is_started = True
            logger.info("✅ ImprovedSimpleRouter 시작 완료")
        except Exception as e:
            logger.error(f"❌ ImprovedSimpleRouter 시작 실패: {e}")
            raise

    async def stop(self) -> None:
        """라우터 정지"""
        if not self._is_started:
            return

        try:
            await self._engine.stop()
            self._is_started = False
            logger.info("✅ ImprovedSimpleRouter 정지 완료")
        except Exception as e:
            logger.error(f"❌ ImprovedSimpleRouter 정지 실패: {e}")

    def _get_profile(self, symbol: str) -> SymbolUsageProfile:
        """심볼 프로필 조회/생성"""
        if symbol not in self._profiles:
            self._profiles[symbol] = SymbolUsageProfile(symbol)
        return self._profiles[symbol]

    def _create_optimized_context(self, symbol: str, request_type: str, count: int) -> RoutingContext:
        """최적화된 컨텍스트 생성"""
        profile = self._get_profile(symbol)
        strategy_name, _ = profile.get_optimal_strategy(request_type, count)

        # 전략별 컨텍스트 설정
        if strategy_name == "realtime_optimized":
            usage_context = UsageContext.REALTIME_TRADING
            network_policy = NetworkPolicy.AGGRESSIVE
        elif strategy_name == "batch_optimized":
            usage_context = UsageContext.RESEARCH_ANALYSIS
            network_policy = NetworkPolicy.CONSERVATIVE
        else:  # balanced, mixed_realtime
            usage_context = UsageContext.RESEARCH_ANALYSIS
            network_policy = NetworkPolicy.BALANCED

        return RoutingContext(
            usage_context=usage_context,
            network_policy=network_policy,
            session_id=f"improved_router_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

    async def _execute_with_fallback(self, symbol: str, request_func, request_type: str,
                                   count: int = 1) -> Any:
        """폴백 메커니즘이 있는 요청 실행"""
        try:
            # 메인 요청 실행
            result = await request_func()

            # 결과 검증 및 캐싱
            if result and self._is_valid_result(result):
                # 성공 시 폴백 캐시에 저장
                cache_key = f"{symbol}:{request_type}"
                self._fallback_cache[cache_key] = (result, datetime.now())
                return result
            else:
                logger.warning(f"⚠️ 빈 결과 수신: {symbol} {request_type}")

        except Exception as e:
            logger.warning(f"⚠️ 메인 요청 실패: {symbol} {request_type} - {e}")

        # 폴백 캐시 시도
        cache_key = f"{symbol}:{request_type}"
        if cache_key in self._fallback_cache:
            cached_data, cached_time = self._fallback_cache[cache_key]
            age_minutes = (datetime.now() - cached_time).total_seconds() / 60

            if age_minutes < 5:  # 5분 이내 캐시만 사용
                logger.info(f"🔄 폴백 캐시 사용: {symbol} (캐시 나이: {age_minutes:.1f}분)")
                return cached_data

        # 최후 수단: 직접 REST API 호출
        try:
            logger.info(f"🆘 최후 수단: 직접 API 호출 {symbol}")
            return await self._direct_api_call(symbol, request_type, count)
        except Exception as e:
            logger.error(f"❌ 모든 방법 실패: {symbol} {request_type} - {e}")
            return {} if request_type == "ticker" else []

    def _is_valid_result(self, result: Any) -> bool:
        """결과 유효성 검사"""
        if result is None:
            return False

        if isinstance(result, dict):
            return bool(result)  # 빈 딕셔너리가 아님

        if isinstance(result, list):
            return len(result) > 0  # 빈 리스트가 아님

        return True

    async def _direct_api_call(self, symbol: str, request_type: str, count: int) -> Any:
        """직접 API 호출 (최후 수단)"""
        # 이 부분은 실제 환경에서는 UpbitDataProvider의 직접 메서드를 호출하거나
        # REST API를 직접 호출하는 로직으로 구현
        logger.warning(f"직접 API 호출 미구현: {symbol} {request_type}")
        return {} if request_type == "ticker" else []

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """티커 데이터 조회 - 개선된 안정성"""
        if not self._is_started:
            await self.start()

        # 프로필 업데이트
        profile = self._get_profile(symbol)
        profile.add_request("ticker", 1)

        # 요청 함수 정의
        async def request_func():
            context = self._create_optimized_context(symbol, "ticker", 1)

            request = RoutingRequest(
                symbols=[symbol],
                data_type=DataType.TICKER,
                requested_at=datetime.now(),
                request_id=f"ticker_{symbol}_{datetime.now().strftime('%H%M%S%f')}"
            )

            response = await self._engine.route_data_request(request, context)

            if response.status.value == "success":
                return response.data.get(symbol, {})
            else:
                logger.warning(f"라우팅 엔진 응답 실패: {response.status} - {response.errors}")
                return {}

        # 폴백 메커니즘과 함께 실행
        result = await self._execute_with_fallback(symbol, request_func, "ticker", 1)

        if result:
            logger.debug(f"✅ 티커 조회 성공: {symbol}")
        else:
            logger.warning(f"⚠️ 티커 조회 최종 실패: {symbol}")

        return result

    async def get_candles(self, symbol: str, interval: str = "1m",
                          count: int = 100, from_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """캔들 데이터 조회 - 요청 패턴 최적화"""
        if not self._is_started:
            await self.start()

        # 프로필 업데이트
        profile = self._get_profile(symbol)
        profile.add_request("candles", count)

        # 요청 패턴에 따른 전략 결정
        if count == 1 and from_date is None:
            # 최신 1개 캔들 → 웹소켓 우선
            logger.debug(f"📊 최신 캔들 요청 최적화: {symbol}")
            return await self._get_latest_candle(symbol, interval)

        elif count > 100 or from_date is not None:
            # 대량 히스토리컬 데이터 → REST API 우선
            logger.debug(f"📈 히스토리컬 데이터 요청 최적화: {symbol} (count={count})")
            return await self._get_historical_candles(symbol, interval, count, from_date)

        else:
            # 중간 크기 → 균형 전략
            logger.debug(f"📊 균형 캔들 요청: {symbol} (count={count})")
            return await self._get_balanced_candles(symbol, interval, count)

    async def _get_latest_candle(self, symbol: str, interval: str) -> List[Dict[str, Any]]:
        """최신 캔들 조회 (웹소켓 우선)"""
        async def request_func():
            # 웹소켓/실시간 우선 컨텍스트
            context = RoutingContext(
                usage_context=UsageContext.REALTIME_TRADING,
                network_policy=NetworkPolicy.AGGRESSIVE,
                session_id=f"latest_candle_{datetime.now().strftime('%H%M%S')}"
            )

            request = RoutingRequest(
                symbols=[symbol],
                data_type=DataType.CANDLE,
                timeframe=TimeFrame.MINUTES_1,
                count=1,
                requested_at=datetime.now(),
                request_id=f"latest_candle_{symbol}_{datetime.now().strftime('%H%M%S%f')}"
            )

            response = await self._engine.route_data_request(request, context)

            if response.status.value == "success":
                return response.data.get(symbol, [])
            else:
                return []

        return await self._execute_with_fallback(symbol, request_func, f"candles_{interval}", 1)

    async def _get_historical_candles(self, symbol: str, interval: str, count: int,
                                    from_date: Optional[datetime]) -> List[Dict[str, Any]]:
        """히스토리컬 캔들 조회 (REST API 우선)"""
        async def request_func():
            # REST API 우선 컨텍스트
            context = RoutingContext(
                usage_context=UsageContext.RESEARCH_ANALYSIS,
                network_policy=NetworkPolicy.CONSERVATIVE,
                session_id=f"historical_candle_{datetime.now().strftime('%H%M%S')}"
            )

            request = RoutingRequest(
                symbols=[symbol],
                data_type=DataType.CANDLE,
                timeframe=TimeFrame.MINUTES_1,
                count=count,
                requested_at=datetime.now(),
                request_id=f"historical_candle_{symbol}_{datetime.now().strftime('%H%M%S%f')}"
            )

            response = await self._engine.route_data_request(request, context)

            if response.status.value == "success":
                return response.data.get(symbol, [])
            else:
                return []

        return await self._execute_with_fallback(symbol, request_func, f"candles_{interval}", count)

    async def _get_balanced_candles(self, symbol: str, interval: str, count: int) -> List[Dict[str, Any]]:
        """균형 캔들 조회 (캐시 우선)"""
        async def request_func():
            # 균형 컨텍스트
            context = RoutingContext(
                usage_context=UsageContext.RESEARCH_ANALYSIS,
                network_policy=NetworkPolicy.BALANCED,
                session_id=f"balanced_candle_{datetime.now().strftime('%H%M%S')}"
            )

            request = RoutingRequest(
                symbols=[symbol],
                data_type=DataType.CANDLE,
                timeframe=TimeFrame.MINUTES_1,
                count=count,
                requested_at=datetime.now(),
                request_id=f"balanced_candle_{symbol}_{datetime.now().strftime('%H%M%S%f')}"
            )

            response = await self._engine.route_data_request(request, context)

            if response.status.value == "success":
                return response.data.get(symbol, [])
            else:
                return []

        return await self._execute_with_fallback(symbol, request_func, f"candles_{interval}", count)

    def get_symbol_profile(self, symbol: str) -> SymbolUsageProfile:
        """심볼 사용 프로필 조회"""
        return self._get_profile(symbol)

    def get_cache_status(self) -> Dict[str, Any]:
        """캐시 상태 조회"""
        cache_items = []
        for key, (data, timestamp) in self._fallback_cache.items():
            age_minutes = (datetime.now() - timestamp).total_seconds() / 60
            cache_items.append({
                "key": key,
                "age_minutes": round(age_minutes, 2),
                "data_type": type(data).__name__,
                "data_size": len(str(data))
            })

        return {
            "total_items": len(cache_items),
            "items": cache_items
        }

    async def clear_cache(self):
        """캐시 정리"""
        self._fallback_cache.clear()
        logger.info("🧹 폴백 캐시 정리 완료")


# 전역 인스턴스
_global_improved_router: Optional[ImprovedSimpleRouter] = None


def get_improved_router() -> ImprovedSimpleRouter:
    """전역 개선된 라우터 인스턴스 조회"""
    global _global_improved_router

    if _global_improved_router is None:
        _global_improved_router = ImprovedSimpleRouter()

    return _global_improved_router


async def initialize_improved_router() -> ImprovedSimpleRouter:
    """개선된 라우터 초기화 및 시작"""
    router = get_improved_router()
    await router.start()
    return router
