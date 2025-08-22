"""
단순화된 스마트 라우팅 인터페이스

기존 AdaptiveRoutingEngine의 복잡성을 숨기고 사용자 친화적인 API를 제공합니다.
사용 패턴을 학습하여 자동으로 최적의 라우팅을 결정합니다.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .core.adaptive_routing_engine import AdaptiveRoutingEngine
from .models import (
    RoutingRequest, RoutingContext,
    UsageContext, NetworkPolicy, DataType, TimeFrame
)

logger = create_component_logger("SimpleSmartRouter")


@dataclass
class SymbolPattern:
    """심볼별 사용 패턴"""
    symbol: str
    request_history: List[Tuple[datetime, str]] = field(default_factory=list)

    def add_request(self, request_type: str):
        """요청 기록 추가"""
        self.request_history.append((datetime.now(), request_type))
        # 최근 100개만 유지
        if len(self.request_history) > 100:
            self.request_history = self.request_history[-100:]

    def is_high_frequency(self) -> bool:
        """고빈도 요청 패턴 여부 (10초 내 5회 이상)"""
        if len(self.request_history) < 5:
            return False

        recent_5 = self.request_history[-5:]
        time_span = (recent_5[-1][0] - recent_5[0][0]).total_seconds()
        return time_span < 10.0

    def get_frequency_category(self) -> str:
        """빈도 카테고리 반환"""
        if self.is_high_frequency():
            return "high_frequency"
        else:
            return "normal"


class SimpleSmartRouter:
    """사용자 친화적 스마트 라우팅 인터페이스

    복잡한 AdaptiveRoutingEngine을 래핑하여 단순한 API를 제공합니다.
    """

    def __init__(self):
        """Simple Router 초기화"""
        logger.info("SimpleSmartRouter 초기화 시작")

        self._engine = AdaptiveRoutingEngine()
        self._patterns: Dict[str, SymbolPattern] = {}
        self._is_started = False

        logger.info("SimpleSmartRouter 초기화 완료")

    async def start(self) -> None:
        """라우터 시작"""
        if self._is_started:
            return

        await self._engine.start()
        self._is_started = True
        logger.info("✅ SimpleSmartRouter 시작 완료")

    async def stop(self) -> None:
        """라우터 정지"""
        if not self._is_started:
            return

        await self._engine.stop()
        self._is_started = False
        logger.info("✅ SimpleSmartRouter 정지 완료")

    def _track_request(self, symbol: str, request_type: str):
        """요청 패턴 기록"""
        if symbol not in self._patterns:
            self._patterns[symbol] = SymbolPattern(symbol)
        self._patterns[symbol].add_request(request_type)

    def _create_context(self, symbol: str, data_type: str) -> RoutingContext:
        """자동 컨텍스트 생성"""
        pattern = self._patterns.get(symbol, SymbolPattern(symbol))

        if pattern.is_high_frequency():
            usage_context = UsageContext.REALTIME_TRADING
            network_policy = NetworkPolicy.AGGRESSIVE
        else:
            usage_context = UsageContext.RESEARCH_ANALYSIS
            network_policy = NetworkPolicy.BALANCED

        return RoutingContext(
            usage_context=usage_context,
            network_policy=network_policy,
            session_id=f"simple_router_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """티커 데이터 조회 - 자동 최적화"""
        if not self._is_started:
            await self.start()

        # 패턴 추적
        self._track_request(symbol, "ticker")

        # 자동 컨텍스트 생성
        context = self._create_context(symbol, "ticker")

        # 요청 생성
        request = RoutingRequest(
            symbols=[symbol],
            data_type=DataType.TICKER,
            requested_at=datetime.now(),
            request_id=f"ticker_{symbol}_{datetime.now().strftime('%H%M%S%f')}"
        )

        # 라우팅 실행
        response = await self._engine.route_data_request(request, context)

        if response.status.value == "success":
            logger.debug(f"✅ 티커 조회 성공: {symbol}")
            # response.data 구조: {'success': True, 'data': {'KRW-BTC': {...}}, ...}
            actual_data = response.data.get('data', {})
            return actual_data.get(symbol, {})
        else:
            logger.warning(f"⚠️ 티커 조회 실패: {symbol}")
            return {}

    async def get_candles(self, symbol: str, interval: str = "1m",
                          count: int = 100) -> List[Dict[str, Any]]:
        """캔들 데이터 조회 - 자동 최적화"""
        if not self._is_started:
            await self.start()

        # 패턴 추적
        self._track_request(symbol, f"candles_{interval}")

        # 요청 패턴에 따른 최적화
        if count == 1:
            # 최신 1개 캔들 → 웹소켓 우선
            context = RoutingContext(
                usage_context=UsageContext.REALTIME_TRADING,
                network_policy=NetworkPolicy.AGGRESSIVE,
                session_id=f"realtime_candle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
        elif count > 100:
            # 대량 히스토리컬 데이터 → REST API 우선
            context = RoutingContext(
                usage_context=UsageContext.RESEARCH_ANALYSIS,
                network_policy=NetworkPolicy.CONSERVATIVE,
                session_id=f"historical_candle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
        else:
            # 중간 크기 → 자동 컨텍스트
            context = self._create_context(symbol, "candles")

        # 기본 TimeFrame 사용
        timeframe = TimeFrame.MINUTES_1

        # 요청 생성
        request = RoutingRequest(
            symbols=[symbol],
            data_type=DataType.CANDLE,
            timeframe=timeframe,
            count=count,
            requested_at=datetime.now(),
            request_id=f"candles_{symbol}_{interval}_{datetime.now().strftime('%H%M%S%f')}"
        )

        # 라우팅 실행
        response = await self._engine.route_data_request(request, context)

        if response.status.value == "success":
            logger.debug(f"✅ 캔들 조회 성공: {symbol} {interval}")
            # response.data 구조: {'success': True, 'data': {'KRW-BTC': [...]}, ...}
            actual_data = response.data.get('data', {})
            return actual_data.get(symbol, [])
        else:
            logger.warning(f"⚠️ 캔들 조회 실패: {symbol} {interval}")
            return []

    def get_symbol_pattern(self, symbol: str) -> SymbolPattern:
        """심볼 패턴 조회"""
        if symbol not in self._patterns:
            self._patterns[symbol] = SymbolPattern(symbol)
        return self._patterns[symbol]

    def get_usage_stats(self) -> Dict[str, Any]:
        """사용 통계 조회"""
        stats = {
            "total_symbols": len(self._patterns),
            "symbols": {}
        }

        for symbol, pattern in self._patterns.items():
            stats["symbols"][symbol] = {
                "total_requests": len(pattern.request_history),
                "frequency_category": pattern.get_frequency_category(),
                "is_high_frequency": pattern.is_high_frequency()
            }

        return stats


# 전역 인스턴스 (싱글톤 패턴)
_global_simple_router: Optional[SimpleSmartRouter] = None


def get_simple_router() -> SimpleSmartRouter:
    """전역 Simple Router 인스턴스 조회"""
    global _global_simple_router

    if _global_simple_router is None:
        _global_simple_router = SimpleSmartRouter()

    return _global_simple_router


async def initialize_simple_router() -> SimpleSmartRouter:
    """Simple Router 초기화 및 시작"""
    router = get_simple_router()
    await router.start()
    return router
