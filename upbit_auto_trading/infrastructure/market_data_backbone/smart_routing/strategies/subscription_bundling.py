"""
구독 묶음 관리 전략

기능별/성질별로 WebSocket 구독을 최적화하여 관리합니다.
업비트 API의 유연한 구독 시스템을 활용하여 효율적인 그룹핑을 제공합니다.
"""

from dataclasses import dataclass
from typing import Dict, List, Set, Optional, Any
from enum import Enum
import asyncio
from datetime import datetime

from ..models import TradingSymbol


class SubscriptionPurpose(Enum):
    """구독 목적 분류"""
    REAL_TRADING = "real_trading"        # 실시간 트레이딩
    MONITORING = "monitoring"            # 포트폴리오 모니터링
    BACKTESTING = "backtesting"          # 백테스팅
    ANALYSIS = "analysis"                # 차트 분석
    ALERT = "alert"                      # 급변 감지/알람


class DataTypeGroup(Enum):
    """데이터 타입 그룹"""
    PRICE_BASED = "price_based"          # ticker, candle
    DEPTH_BASED = "depth_based"          # orderbook
    EXECUTION_BASED = "execution_based"  # trade
    ALL_TYPES = "all_types"              # 모든 타입


@dataclass(frozen=True)
class SubscriptionBundle:
    """구독 묶음 정의"""

    bundle_id: str
    purpose: SubscriptionPurpose
    symbols: Set[TradingSymbol]
    data_types: Set[str]
    timeframes: Set[str]  # candle.1m, candle.5m 등
    priority: int = 5  # 1(높음) ~ 10(낮음)

    def get_websocket_request(self, ticket: str) -> List[Dict[str, Any]]:
        """업비트 WebSocket 요청 메시지 생성"""
        request = [
            {"ticket": ticket}
        ]

        # 데이터 타입별로 구독 요청 생성
        for data_type in self.data_types:
            if data_type.startswith("candle."):
                # 캔들 데이터 구독
                request.append({
                    "type": data_type,
                    "codes": [str(symbol) for symbol in self.symbols]
                })
            else:
                # ticker, orderbook, trade 구독
                request.append({
                    "type": data_type,
                    "codes": [str(symbol) for symbol in self.symbols]
                })

        # 포맷 설정
        request.append({"format": "DEFAULT"})

        return request


class SubscriptionBundlingStrategy:
    """구독 묶음 생성 전략"""

    def __init__(self):
        self.bundles: Dict[str, SubscriptionBundle] = {}
        self.active_subscriptions: Dict[str, Dict[str, Any]] = {}

    def create_trading_bundle(
        self,
        symbols: List[TradingSymbol],
        timeframes: List[str] = None
    ) -> SubscriptionBundle:
        """실시간 트레이딩용 구독 묶음"""
        if timeframes is None:
            timeframes = ["candle.1m"]

        bundle_id = f"trading_{datetime.now().timestamp()}"

        return SubscriptionBundle(
            bundle_id=bundle_id,
            purpose=SubscriptionPurpose.REAL_TRADING,
            symbols=set(symbols),
            data_types={"ticker", "orderbook"} | {f for f in timeframes},
            timeframes=set(timeframes),
            priority=1  # 최고 우선순위
        )

    def create_monitoring_bundle(
        self,
        symbols: List[TradingSymbol]
    ) -> SubscriptionBundle:
        """포트폴리오 모니터링용 구독 묶음"""
        bundle_id = f"monitoring_{datetime.now().timestamp()}"

        return SubscriptionBundle(
            bundle_id=bundle_id,
            purpose=SubscriptionPurpose.MONITORING,
            symbols=set(symbols),
            data_types={"ticker"},  # 티커만으로 충분
            timeframes=set(),
            priority=3
        )

    def create_analysis_bundle(
        self,
        symbol: TradingSymbol,
        timeframes: List[str]
    ) -> SubscriptionBundle:
        """차트 분석용 구독 묶음"""
        bundle_id = f"analysis_{symbol}_{datetime.now().timestamp()}"

        return SubscriptionBundle(
            bundle_id=bundle_id,
            purpose=SubscriptionPurpose.ANALYSIS,
            symbols={symbol},
            data_types={"ticker"} | set(timeframes),
            timeframes=set(timeframes),
            priority=4
        )

    def create_alert_bundle(
        self,
        symbols: List[TradingSymbol]
    ) -> SubscriptionBundle:
        """급변 감지용 구독 묶음"""
        bundle_id = f"alert_{datetime.now().timestamp()}"

        return SubscriptionBundle(
            bundle_id=bundle_id,
            purpose=SubscriptionPurpose.ALERT,
            symbols=set(symbols),
            data_types={"ticker", "trade"},  # 빠른 감지용
            timeframes=set(),
            priority=2  # 높은 우선순위
        )

    def optimize_bundles(
        self,
        bundles: List[SubscriptionBundle]
    ) -> List[SubscriptionBundle]:
        """구독 묶음 최적화

        - 동일한 목적과 심볼 집합을 통합
        - 우선순위별로 정렬
        - 업비트 연결 수 제한 고려
        """
        # 목적별로 그룹핑
        purpose_groups: Dict[SubscriptionPurpose, List[SubscriptionBundle]] = {}

        for bundle in bundles:
            if bundle.purpose not in purpose_groups:
                purpose_groups[bundle.purpose] = []
            purpose_groups[bundle.purpose].append(bundle)

        optimized = []

        for purpose, group_bundles in purpose_groups.items():
            # 동일 목적 내에서 심볼과 데이터 타입이 겹치는 묶음들을 통합
            merged = self._merge_compatible_bundles(group_bundles)
            optimized.extend(merged)

        # 우선순위별로 정렬
        optimized.sort(key=lambda b: b.priority)

        return optimized

    def _merge_compatible_bundles(
        self,
        bundles: List[SubscriptionBundle]
    ) -> List[SubscriptionBundle]:
        """호환 가능한 묶음들을 통합"""
        if not bundles:
            return []

        if len(bundles) == 1:
            return bundles

        # 단순 구현: 첫 번째 묶음에 나머지를 통합
        # 실제로는 더 정교한 알고리즘 필요
        base = bundles[0]

        merged_symbols = set(base.symbols)
        merged_data_types = set(base.data_types)
        merged_timeframes = set(base.timeframes)

        for bundle in bundles[1:]:
            merged_symbols.update(bundle.symbols)
            merged_data_types.update(bundle.data_types)
            merged_timeframes.update(bundle.timeframes)

        return [SubscriptionBundle(
            bundle_id=f"merged_{base.purpose.value}_{datetime.now().timestamp()}",
            purpose=base.purpose,
            symbols=merged_symbols,
            data_types=merged_data_types,
            timeframes=merged_timeframes,
            priority=min(b.priority for b in bundles)  # 최고 우선순위 사용
        )]

    def get_functional_grouping_example(self) -> Dict[str, SubscriptionBundle]:
        """기능별 구독 묶음 예시"""
        btc = TradingSymbol("KRW-BTC")
        eth = TradingSymbol("KRW-ETH")
        ada = TradingSymbol("KRW-ADA")

        examples = {}

        # 1. 실시간 트레이딩 (BTC, ETH)
        examples["trading"] = self.create_trading_bundle(
            symbols=[btc, eth],
            timeframes=["candle.1m", "candle.5m"]
        )

        # 2. 포트폴리오 모니터링 (여러 코인)
        examples["monitoring"] = self.create_monitoring_bundle(
            symbols=[btc, eth, ada]
        )

        # 3. BTC 차트 분석
        examples["btc_analysis"] = self.create_analysis_bundle(
            symbol=btc,
            timeframes=["candle.1m", "candle.15m", "candle.1h"]
        )

        # 4. 급변 감지 시스템
        examples["alert"] = self.create_alert_bundle(
            symbols=[btc, eth]
        )

        return examples


class SubscriptionManager:
    """구독 관리자"""

    def __init__(self):
        self.strategy = SubscriptionBundlingStrategy()
        self.active_bundles: Dict[str, SubscriptionBundle] = {}
        self.websocket_connections: Dict[str, Any] = {}

    async def subscribe_bundle(
        self,
        bundle: SubscriptionBundle,
        callback: Optional[Any] = None
    ) -> str:
        """구독 묶음 활성화"""
        # WebSocket 연결 및 구독 요청
        ticket = f"bundle_{bundle.bundle_id}"
        request = bundle.get_websocket_request(ticket)

        # 실제 WebSocket 구독 (구현 필요)
        # await self._websocket_subscribe(request, callback)

        self.active_bundles[bundle.bundle_id] = bundle

        return bundle.bundle_id

    async def unsubscribe_bundle(self, bundle_id: str) -> bool:
        """구독 묶음 해제"""
        if bundle_id in self.active_bundles:
            # WebSocket 연결 해제 (구현 필요)
            # await self._websocket_unsubscribe(bundle_id)

            del self.active_bundles[bundle_id]
            return True

        return False

    def get_bundle_stats(self) -> Dict[str, Any]:
        """구독 묶음 통계"""
        stats = {
            "total_bundles": len(self.active_bundles),
            "by_purpose": {},
            "total_symbols": set(),
            "total_data_types": set()
        }

        for bundle in self.active_bundles.values():
            purpose = bundle.purpose.value
            if purpose not in stats["by_purpose"]:
                stats["by_purpose"][purpose] = 0
            stats["by_purpose"][purpose] += 1

            stats["total_symbols"].update(bundle.symbols)
            stats["total_data_types"].update(bundle.data_types)

        stats["total_symbols"] = len(stats["total_symbols"])
        stats["total_data_types"] = len(stats["total_data_types"])

        return stats


# 사용 예시
def demonstrate_subscription_bundling():
    """구독 묶음 시스템 사용 예시"""

    manager = SubscriptionManager()

    # 기능별 구독 묶음 생성
    examples = manager.strategy.get_functional_grouping_example()

    print("=== 기능별 구독 묶음 ===")
    for name, bundle in examples.items():
        print(f"\n{name}:")
        print(f"  목적: {bundle.purpose.value}")
        print(f"  심볼: {[str(s) for s in bundle.symbols]}")
        print(f"  데이터 타입: {list(bundle.data_types)}")
        print(f"  우선순위: {bundle.priority}")

        # WebSocket 요청 메시지 미리보기
        request = bundle.get_websocket_request(f"demo_{name}")
        print(f"  WebSocket 요청: {len(request)}개 메시지")

    print("\n=== 구독 최적화 예시 ===")
    optimized = manager.strategy.optimize_bundles(list(examples.values()))
    print(f"원본 묶음: {len(examples)} → 최적화 후: {len(optimized)}")


if __name__ == "__main__":
    demonstrate_subscription_bundling()
