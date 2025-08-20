"""
고급 채널 선택기

요청 패턴, 성능 메트릭, 시스템 상태를 종합하여
최적의 데이터 채널을 자율적으로 선택합니다.
"""

from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..interfaces.data_router import IChannelSelector
from ..models import TradingSymbol
from .frequency_analyzer import AdvancedFrequencyAnalyzer, RequestPattern


class ChannelType(Enum):
    """채널 타입"""
    REST = "rest"
    WEBSOCKET = "websocket"
    HYBRID = "hybrid"  # 상황에 따라 동적 선택


class PerformanceLevel(Enum):
    """성능 수준"""
    EXCELLENT = "excellent"
    GOOD = "good"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class ChannelPerformance:
    """채널별 성능 정보"""

    channel_type: ChannelType
    avg_response_time_ms: float
    success_rate: float
    availability: float
    last_error_time: Optional[datetime] = None
    error_count_24h: int = 0

    @property
    def performance_score(self) -> float:
        """성능 점수 (0-100)"""
        # 응답시간, 성공률, 가용성을 종합한 점수
        time_score = max(0, 100 - self.avg_response_time_ms / 10)  # 1000ms = 0점
        success_score = self.success_rate * 100
        availability_score = self.availability * 100

        # 가중 평균
        return (time_score * 0.3 + success_score * 0.4 + availability_score * 0.3)

    @property
    def performance_level(self) -> PerformanceLevel:
        """성능 수준 분류"""
        score = self.performance_score

        if score >= 85:
            return PerformanceLevel.EXCELLENT
        elif score >= 70:
            return PerformanceLevel.GOOD
        elif score >= 50:
            return PerformanceLevel.POOR
        else:
            return PerformanceLevel.CRITICAL


@dataclass
class ChannelDecision:
    """채널 선택 결정"""

    selected_channel: ChannelType
    confidence: float  # 0-1, 결정에 대한 확신도
    reason: str
    alternatives: List[ChannelType]
    decision_time: datetime

    def __str__(self) -> str:
        return f"{self.selected_channel.value} (confidence: {self.confidence:.2f}, reason: {self.reason})"


class AdvancedChannelSelector(IChannelSelector):
    """고급 채널 선택기

    다음 요소들을 종합하여 최적 채널을 선택합니다:
    1. 요청 빈도 패턴
    2. 채널별 성능 히스토리
    3. 시스템 부하 상태
    4. 데이터 타입별 특성
    5. 비즈니스 우선순위
    """

    def __init__(
        self,
        frequency_analyzer: Optional[AdvancedFrequencyAnalyzer] = None,
        performance_window_hours: int = 24,
        decision_cache_minutes: int = 5
    ):
        self.frequency_analyzer = frequency_analyzer or AdvancedFrequencyAnalyzer()
        self.performance_window_hours = performance_window_hours
        self.decision_cache_minutes = decision_cache_minutes

        # 채널별 성능 추적
        self.channel_performance: Dict[str, ChannelPerformance] = {}

        # 결정 캐시 (동일한 조건에서 반복 계산 방지)
        self.decision_cache: Dict[str, ChannelDecision] = {}

        # 데이터 타입별 선호 채널
        self.data_type_preferences = {
            "ticker": {
                ChannelType.WEBSOCKET: 0.8,  # 실시간성 중요
                ChannelType.REST: 0.2
            },
            "orderbook": {
                ChannelType.WEBSOCKET: 0.9,  # 매우 빈번한 변경
                ChannelType.REST: 0.1
            },
            "trade": {
                ChannelType.WEBSOCKET: 0.7,  # 실시간 체결 중요
                ChannelType.REST: 0.3
            },
            "candle": {
                ChannelType.REST: 0.8,       # 배치성 데이터
                ChannelType.WEBSOCKET: 0.2
            }
        }

        # 시스템 부하 상태
        self.system_load_factor = 1.0  # 1.0 = 정상, >1.0 = 과부하

        # WebSocket 연결 상태 추적
        self.websocket_connections: Set[str] = set()
        self.max_websocket_connections = 10

    def should_use_websocket(
        self,
        symbol: TradingSymbol,
        data_type: str,
        recent_request_count: int
    ) -> bool:
        """WebSocket 사용 여부 결정 (기본 인터페이스)"""

        decision = self.select_optimal_channel(
            symbol=symbol,
            data_type=data_type,
            recent_request_count=recent_request_count
        )

        return decision.selected_channel == ChannelType.WEBSOCKET

    def select_optimal_channel(
        self,
        symbol: TradingSymbol,
        data_type: str,
        recent_request_count: int,
        priority: str = "normal"
    ) -> ChannelDecision:
        """최적 채널 선택 (종합 분석)"""

        # 캐시 확인
        cache_key = f"{symbol}_{data_type}_{priority}"
        cached_decision = self._get_cached_decision(cache_key)
        if cached_decision:
            return cached_decision

        # 요청 패턴 분석
        pattern = self.frequency_analyzer.analyze_request_pattern(symbol, data_type)

        # 채널별 성능 평가
        rest_performance = self._get_channel_performance(ChannelType.REST, data_type)
        ws_performance = self._get_channel_performance(ChannelType.WEBSOCKET, data_type)

        # 결정 요소별 점수 계산
        scores = self._calculate_channel_scores(
            pattern=pattern,
            rest_performance=rest_performance,
            ws_performance=ws_performance,
            data_type=data_type,
            priority=priority
        )

        # 최종 결정
        decision = self._make_final_decision(scores, pattern, data_type)

        # 캐시에 저장
        self._cache_decision(cache_key, decision)

        return decision

    def update_request_pattern(
        self,
        symbol: TradingSymbol,
        data_type: str,
        request_time: datetime
    ) -> None:
        """요청 패턴 업데이트 (분석기에 위임)"""
        self.frequency_analyzer.update_request_pattern(
            symbol, data_type, request_time
        )

    def update_channel_performance(
        self,
        channel_type: ChannelType,
        data_type: str,
        response_time_ms: float,
        success: bool,
        error_details: Optional[str] = None
    ) -> None:
        """채널 성능 업데이트"""

        key = f"{channel_type.value}_{data_type}"

        if key not in self.channel_performance:
            self.channel_performance[key] = ChannelPerformance(
                channel_type=channel_type,
                avg_response_time_ms=response_time_ms,
                success_rate=1.0 if success else 0.0,
                availability=1.0 if success else 0.0
            )
        else:
            perf = self.channel_performance[key]

            # 이동 평균으로 응답 시간 업데이트
            alpha = 0.1  # 가중치
            perf.avg_response_time_ms = (
                (1 - alpha) * perf.avg_response_time_ms +
                alpha * response_time_ms
            )

            # 성공률 업데이트 (최근 100회 기준)
            if success:
                perf.success_rate = min(1.0, perf.success_rate + 0.01)
            else:
                perf.success_rate = max(0.0, perf.success_rate - 0.02)
                perf.last_error_time = datetime.now()
                perf.error_count_24h += 1

    def update_system_load(self, load_factor: float) -> None:
        """시스템 부하 상태 업데이트"""
        self.system_load_factor = max(0.1, min(5.0, load_factor))

    def get_channel_statistics(self) -> Dict[str, any]:
        """채널 통계 정보"""

        stats = {
            "websocket_connections": len(self.websocket_connections),
            "max_websocket_connections": self.max_websocket_connections,
            "system_load_factor": self.system_load_factor,
            "channel_performance": {},
            "decision_cache_size": len(self.decision_cache)
        }

        # 채널별 성능 정보
        for key, perf in self.channel_performance.items():
            stats["channel_performance"][key] = {
                "channel_type": perf.channel_type.value,
                "avg_response_time_ms": perf.avg_response_time_ms,
                "success_rate": perf.success_rate,
                "availability": perf.availability,
                "performance_score": perf.performance_score,
                "performance_level": perf.performance_level.value,
                "error_count_24h": perf.error_count_24h
            }

        return stats

    def _get_cached_decision(self, cache_key: str) -> Optional[ChannelDecision]:
        """캐시된 결정 조회"""

        if cache_key not in self.decision_cache:
            return None

        decision = self.decision_cache[cache_key]

        # 캐시 만료 확인
        cache_age = datetime.now() - decision.decision_time
        if cache_age.total_seconds() > self.decision_cache_minutes * 60:
            del self.decision_cache[cache_key]
            return None

        return decision

    def _cache_decision(self, cache_key: str, decision: ChannelDecision) -> None:
        """결정 캐시에 저장"""
        self.decision_cache[cache_key] = decision

        # 캐시 크기 제한 (최대 100개)
        if len(self.decision_cache) > 100:
            # 가장 오래된 항목 제거
            oldest_key = min(
                self.decision_cache.keys(),
                key=lambda k: self.decision_cache[k].decision_time
            )
            del self.decision_cache[oldest_key]

    def _get_channel_performance(
        self,
        channel_type: ChannelType,
        data_type: str
    ) -> ChannelPerformance:
        """채널 성능 정보 조회"""

        key = f"{channel_type.value}_{data_type}"

        if key not in self.channel_performance:
            # 기본 성능 정보 생성
            return ChannelPerformance(
                channel_type=channel_type,
                avg_response_time_ms=500.0,  # 기본값
                success_rate=0.95,           # 기본값
                availability=1.0             # 기본값
            )

        return self.channel_performance[key]

    def _calculate_channel_scores(
        self,
        pattern: RequestPattern,
        rest_performance: ChannelPerformance,
        ws_performance: ChannelPerformance,
        data_type: str,
        priority: str
    ) -> Dict[ChannelType, float]:
        """채널별 점수 계산"""

        scores = {}

        # REST 채널 점수
        rest_score = self._calculate_rest_score(
            pattern, rest_performance, data_type, priority
        )
        scores[ChannelType.REST] = rest_score

        # WebSocket 채널 점수
        ws_score = self._calculate_websocket_score(
            pattern, ws_performance, data_type, priority
        )
        scores[ChannelType.WEBSOCKET] = ws_score

        return scores

    def _calculate_rest_score(
        self,
        pattern: RequestPattern,
        performance: ChannelPerformance,
        data_type: str,
        priority: str
    ) -> float:
        """REST 채널 점수 계산"""

        # 기본 성능 점수
        base_score = performance.performance_score

        # 빈도 패턴 보정 (저빈도일수록 REST 유리)
        frequency_factor = max(0.5, 1.0 - pattern.requests_per_minute / 10.0)

        # 데이터 타입 선호도
        type_preference = self.data_type_preferences.get(data_type, {}).get(
            ChannelType.REST, 0.5
        )

        # 시스템 부하 보정 (부하 높을때 REST 선호)
        load_factor = min(2.0, self.system_load_factor)

        # 우선순위 보정
        priority_factor = 1.2 if priority == "high" else 1.0

        final_score = (
            base_score * 0.4 +
            frequency_factor * 30 +
            type_preference * 20 +
            load_factor * 5
        ) * priority_factor

        return min(100.0, final_score)

    def _calculate_websocket_score(
        self,
        pattern: RequestPattern,
        performance: ChannelPerformance,
        data_type: str,
        priority: str
    ) -> float:
        """WebSocket 채널 점수 계산"""

        # 기본 성능 점수
        base_score = performance.performance_score

        # 빈도 패턴 보정 (고빈도일수록 WebSocket 유리)
        frequency_factor = min(2.0, pattern.requests_per_minute / 2.0)

        # 일관성 보정 (일관적일수록 WebSocket 유리)
        consistency_factor = pattern.consistency_score

        # 데이터 타입 선호도
        type_preference = self.data_type_preferences.get(data_type, {}).get(
            ChannelType.WEBSOCKET, 0.5
        )

        # 연결 수 제한 (너무 많으면 불리)
        connection_penalty = max(0.5, 1.0 - len(self.websocket_connections) / self.max_websocket_connections)

        # 시스템 부하 보정 (부하 높을때 WebSocket 불리)
        load_penalty = max(0.5, 2.0 - self.system_load_factor)

        # 우선순위 보정
        priority_factor = 1.1 if priority == "high" else 1.0

        final_score = (
            base_score * 0.3 +
            frequency_factor * 20 +
            consistency_factor * 15 +
            type_preference * 25 +
            connection_penalty * 5
        ) * load_penalty * priority_factor

        return min(100.0, final_score)

    def _make_final_decision(
        self,
        scores: Dict[ChannelType, float],
        pattern: RequestPattern,
        data_type: str
    ) -> ChannelDecision:
        """최종 채널 결정"""

        # 가장 높은 점수의 채널 선택
        best_channel = max(scores.keys(), key=lambda ch: scores[ch])
        best_score = scores[best_channel]

        # 확신도 계산 (점수 차이가 클수록 확신도 높음)
        other_scores = [score for ch, score in scores.items() if ch != best_channel]
        if other_scores:
            score_diff = best_score - max(other_scores)
            confidence = min(1.0, score_diff / 50.0)  # 50점 차이 = 100% 확신
        else:
            confidence = 1.0

        # 결정 이유 생성
        reason = self._generate_decision_reason(best_channel, best_score, pattern, data_type)

        # 대안 채널들
        alternatives = [ch for ch in scores.keys() if ch != best_channel]
        alternatives.sort(key=lambda ch: scores[ch], reverse=True)

        return ChannelDecision(
            selected_channel=best_channel,
            confidence=confidence,
            reason=reason,
            alternatives=alternatives,
            decision_time=datetime.now()
        )

    def _generate_decision_reason(
        self,
        channel: ChannelType,
        score: float,
        pattern: RequestPattern,
        data_type: str
    ) -> str:
        """결정 이유 생성"""

        reasons = []

        if channel == ChannelType.WEBSOCKET:
            if pattern.requests_per_minute > 2.0:
                reasons.append(f"고빈도 요청({pattern.requests_per_minute:.1f}/분)")
            if pattern.consistency_score > 0.7:
                reasons.append(f"일관된 패턴({pattern.consistency_score:.2f})")
            if data_type in ["ticker", "orderbook"]:
                reasons.append(f"{data_type} 실시간성 중요")
        else:  # REST
            if pattern.requests_per_minute < 1.0:
                reasons.append(f"저빈도 요청({pattern.requests_per_minute:.1f}/분)")
            if data_type == "candle":
                reasons.append("배치성 데이터")
            if self.system_load_factor > 1.2:
                reasons.append("시스템 부하 고려")

        if not reasons:
            reasons.append(f"점수 기반 선택({score:.1f})")

        return ", ".join(reasons)
