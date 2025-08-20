"""
고급 요청 빈도 분석기

스마트 라우터가 자율적으로 최적 채널을 선택할 수 있도록
정교한 요청 패턴 분석을 제공합니다.
"""

import math
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from ..interfaces.data_router import IFrequencyAnalyzer
from ..models import TradingSymbol


@dataclass
class RequestPattern:
    """요청 패턴 분석 결과"""

    symbol: TradingSymbol
    data_type: str
    requests_per_minute: float
    peak_requests_per_minute: float
    consistency_score: float  # 0-1, 높을수록 일정한 패턴
    trend_direction: str      # "increasing", "decreasing", "stable"
    websocket_recommended: bool
    analysis_time: datetime = field(default_factory=datetime.now)


@dataclass
class RequestEvent:
    """개별 요청 이벤트"""

    timestamp: datetime
    symbol: TradingSymbol
    data_type: str
    response_time_ms: float = 0.0
    success: bool = True


class AdvancedFrequencyAnalyzer(IFrequencyAnalyzer):
    """고급 빈도 분석기

    다음을 분석합니다:
    1. 시간대별 요청 패턴
    2. 요청 빈도의 일관성
    3. 트렌드 변화 감지
    4. 성능 기반 채널 추천
    """

    def __init__(
        self,
        history_retention_hours: int = 24,
        analysis_window_minutes: int = 5,
        peak_detection_sensitivity: float = 1.5
    ):
        self.history_retention_hours = history_retention_hours
        self.analysis_window_minutes = analysis_window_minutes
        self.peak_detection_sensitivity = peak_detection_sensitivity

        # 요청 이력 저장 (심볼_데이터타입별)
        self.request_events: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)  # 최대 1000개 이벤트 유지
        )

        # 성능 메트릭 저장
        self.performance_metrics: Dict[str, Dict] = defaultdict(dict)

        # WebSocket 임계값 (데이터 타입별)
        self.websocket_thresholds = {
            "ticker": 0.8,      # 분당 0.8회 이상
            "orderbook": 1.5,   # 분당 1.5회 이상
            "trade": 0.5,       # 분당 0.5회 이상
            "candle": 1.2       # 분당 1.2회 이상 (거의 사용 안함)
        }

        # 성능 기반 조정 팩터
        self.performance_factors = {
            "excellent": 0.8,    # 성능 우수시 임계값 낮춤
            "good": 1.0,         # 기본
            "poor": 1.3,         # 성능 저하시 임계값 높임
            "failed": 2.0        # 실패 많을시 WebSocket 지연
        }

    def analyze_request_frequency(
        self,
        symbol: TradingSymbol,
        data_type: str,
        time_window_minutes: int = 5
    ) -> float:
        """요청 빈도 분석 (기본 인터페이스)"""
        pattern = self.analyze_request_pattern(symbol, data_type, time_window_minutes)
        return pattern.requests_per_minute

    def analyze_request_pattern(
        self,
        symbol: TradingSymbol,
        data_type: str,
        time_window_minutes: Optional[int] = None
    ) -> RequestPattern:
        """종합적인 요청 패턴 분석"""

        if time_window_minutes is None:
            time_window_minutes = self.analysis_window_minutes

        key = f"{symbol}_{data_type}"
        events = list(self.request_events[key])

        if not events:
            return RequestPattern(
                symbol=symbol,
                data_type=data_type,
                requests_per_minute=0.0,
                peak_requests_per_minute=0.0,
                consistency_score=0.0,
                trend_direction="stable",
                websocket_recommended=False
            )

        # 시간 윈도우 내 이벤트 필터링
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        recent_events = [e for e in events if e.timestamp >= cutoff_time]

        # 기본 빈도 계산
        requests_per_minute = len(recent_events) / time_window_minutes

        # 피크 빈도 계산 (1분 단위 최대값)
        peak_requests_per_minute = self._calculate_peak_frequency(
            recent_events, time_window_minutes
        )

        # 일관성 점수 계산
        consistency_score = self._calculate_consistency_score(
            recent_events, time_window_minutes
        )

        # 트렌드 분석
        trend_direction = self._analyze_trend(events)

        # WebSocket 추천 여부 결정
        websocket_recommended = self._should_recommend_websocket(
            symbol, data_type, requests_per_minute,
            peak_requests_per_minute, consistency_score
        )

        return RequestPattern(
            symbol=symbol,
            data_type=data_type,
            requests_per_minute=requests_per_minute,
            peak_requests_per_minute=peak_requests_per_minute,
            consistency_score=consistency_score,
            trend_direction=trend_direction,
            websocket_recommended=websocket_recommended
        )

    def update_request_pattern(
        self,
        symbol: TradingSymbol,
        data_type: str,
        request_time: datetime,
        response_time_ms: float = 0.0,
        success: bool = True
    ) -> None:
        """요청 패턴 업데이트 (성능 메트릭 포함)"""

        key = f"{symbol}_{data_type}"

        # 요청 이벤트 추가
        event = RequestEvent(
            timestamp=request_time,
            symbol=symbol,
            data_type=data_type,
            response_time_ms=response_time_ms,
            success=success
        )

        self.request_events[key].append(event)

        # 성능 메트릭 업데이트
        self._update_performance_metrics(key, response_time_ms, success)

        # 오래된 데이터 정리
        self._cleanup_old_events()

    def get_websocket_threshold(self, data_type: str) -> float:
        """WebSocket 전환 임계값 (성능 기반 동적 조정)"""

        base_threshold = self.websocket_thresholds.get(data_type, 1.0)

        # 전체 성능 등급 계산
        performance_grade = self._calculate_overall_performance_grade(data_type)
        performance_factor = self.performance_factors.get(performance_grade, 1.0)

        return base_threshold * performance_factor

    def get_detailed_analysis(
        self,
        symbol: TradingSymbol,
        data_type: str
    ) -> Dict[str, any]:
        """상세 분석 정보 (디버깅 및 모니터링용)"""

        key = f"{symbol}_{data_type}"
        events = list(self.request_events[key])

        if not events:
            return {"status": "no_data"}

        # 시간대별 분포 계산
        hourly_distribution = self._calculate_hourly_distribution(events)

        # 성공률 계산
        success_rate = sum(1 for e in events if e.success) / len(events)

        # 평균 응답 시간
        avg_response_time = sum(e.response_time_ms for e in events) / len(events)

        # 최근 패턴
        pattern = self.analyze_request_pattern(symbol, data_type)

        return {
            "total_requests": len(events),
            "success_rate": success_rate,
            "avg_response_time_ms": avg_response_time,
            "hourly_distribution": hourly_distribution,
            "current_pattern": {
                "requests_per_minute": pattern.requests_per_minute,
                "peak_requests_per_minute": pattern.peak_requests_per_minute,
                "consistency_score": pattern.consistency_score,
                "trend_direction": pattern.trend_direction,
                "websocket_recommended": pattern.websocket_recommended
            },
            "websocket_threshold": self.get_websocket_threshold(data_type),
            "performance_grade": self._calculate_overall_performance_grade(data_type)
        }

    def _calculate_peak_frequency(
        self,
        events: List[RequestEvent],
        time_window_minutes: int
    ) -> float:
        """피크 빈도 계산"""

        if not events or time_window_minutes < 1:
            return 0.0

        # 1분 간격으로 나누어 계산
        minute_counts = []
        start_time = datetime.now() - timedelta(minutes=time_window_minutes)

        for i in range(time_window_minutes):
            minute_start = start_time + timedelta(minutes=i)
            minute_end = minute_start + timedelta(minutes=1)

            count = sum(
                1 for event in events
                if minute_start <= event.timestamp < minute_end
            )
            minute_counts.append(count)

        return max(minute_counts) if minute_counts else 0.0

    def _calculate_consistency_score(
        self,
        events: List[RequestEvent],
        time_window_minutes: int
    ) -> float:
        """일관성 점수 계산 (0-1)"""

        if not events or time_window_minutes < 2:
            return 0.0

        # 분당 요청 수 분포 계산
        minute_counts = []
        start_time = datetime.now() - timedelta(minutes=time_window_minutes)

        for i in range(time_window_minutes):
            minute_start = start_time + timedelta(minutes=i)
            minute_end = minute_start + timedelta(minutes=1)

            count = sum(
                1 for event in events
                if minute_start <= event.timestamp < minute_end
            )
            minute_counts.append(count)

        if not minute_counts:
            return 0.0

        # 표준편차 기반 일관성 계산
        mean_count = sum(minute_counts) / len(minute_counts)

        if mean_count == 0:
            return 1.0  # 모두 0이면 일관성 높음

        variance = sum((x - mean_count) ** 2 for x in minute_counts) / len(minute_counts)
        std_dev = math.sqrt(variance)

        # 변동계수의 역수로 일관성 점수 계산
        coefficient_of_variation = std_dev / mean_count if mean_count > 0 else 0
        consistency_score = 1.0 / (1.0 + coefficient_of_variation)

        return min(consistency_score, 1.0)

    def _analyze_trend(self, events: List[RequestEvent]) -> str:
        """트렌드 분석"""

        if len(events) < 4:
            return "stable"

        # 최근 시간을 반으로 나누어 비교
        mid_point = len(events) // 2
        recent_half = events[mid_point:]
        older_half = events[:mid_point]

        # 각 반에서의 분당 요청 수 계산
        if not recent_half or not older_half:
            return "stable"

        recent_duration = (recent_half[-1].timestamp - recent_half[0].timestamp).total_seconds() / 60
        older_duration = (older_half[-1].timestamp - older_half[0].timestamp).total_seconds() / 60

        if recent_duration <= 0 or older_duration <= 0:
            return "stable"

        recent_rate = len(recent_half) / recent_duration
        older_rate = len(older_half) / older_duration

        # 변화율 계산
        if older_rate == 0:
            return "increasing" if recent_rate > 0 else "stable"

        change_rate = (recent_rate - older_rate) / older_rate

        if change_rate > 0.2:  # 20% 이상 증가
            return "increasing"
        elif change_rate < -0.2:  # 20% 이상 감소
            return "decreasing"
        else:
            return "stable"

    def _should_recommend_websocket(
        self,
        symbol: TradingSymbol,
        data_type: str,
        requests_per_minute: float,
        peak_requests_per_minute: float,
        consistency_score: float
    ) -> bool:
        """WebSocket 추천 여부 결정"""

        # 동적 임계값 적용
        threshold = self.get_websocket_threshold(data_type)

        # 기본 빈도 조건
        basic_condition = requests_per_minute >= threshold

        # 피크 빈도 조건 (피크가 임계값의 1.5배 이상)
        peak_condition = peak_requests_per_minute >= threshold * self.peak_detection_sensitivity

        # 일관성 조건 (일관성이 높을수록 WebSocket 적합)
        consistency_condition = consistency_score >= 0.6

        # 종합 판단
        if basic_condition and consistency_condition:
            return True

        if peak_condition and consistency_score >= 0.4:
            return True

        return False

    def _update_performance_metrics(
        self,
        key: str,
        response_time_ms: float,
        success: bool
    ) -> None:
        """성능 메트릭 업데이트"""

        if key not in self.performance_metrics:
            self.performance_metrics[key] = {
                "total_requests": 0,
                "successful_requests": 0,
                "total_response_time": 0.0,
                "last_updated": datetime.now()
            }

        metrics = self.performance_metrics[key]
        metrics["total_requests"] += 1

        if success:
            metrics["successful_requests"] += 1
            metrics["total_response_time"] += response_time_ms

        metrics["last_updated"] = datetime.now()

    def _calculate_overall_performance_grade(self, data_type: str) -> str:
        """전체 성능 등급 계산"""

        # 해당 데이터 타입의 모든 성능 메트릭 수집
        relevant_metrics = [
            metrics for key, metrics in self.performance_metrics.items()
            if key.endswith(f"_{data_type}")
        ]

        if not relevant_metrics:
            return "good"  # 기본값

        # 전체 성공률과 응답 시간 계산
        total_requests = sum(m["total_requests"] for m in relevant_metrics)
        total_successful = sum(m["successful_requests"] for m in relevant_metrics)
        total_response_time = sum(m["total_response_time"] for m in relevant_metrics)

        if total_requests == 0:
            return "good"

        success_rate = total_successful / total_requests
        avg_response_time = total_response_time / total_successful if total_successful > 0 else float('inf')

        # 등급 결정
        if success_rate >= 0.95 and avg_response_time <= 200:
            return "excellent"
        elif success_rate >= 0.9 and avg_response_time <= 500:
            return "good"
        elif success_rate >= 0.8 and avg_response_time <= 1000:
            return "poor"
        else:
            return "failed"

    def _calculate_hourly_distribution(
        self,
        events: List[RequestEvent]
    ) -> Dict[int, int]:
        """시간대별 요청 분포 계산"""

        distribution = defaultdict(int)

        for event in events:
            hour = event.timestamp.hour
            distribution[hour] += 1

        return dict(distribution)

    def _cleanup_old_events(self) -> None:
        """오래된 이벤트 정리"""

        cutoff_time = datetime.now() - timedelta(hours=self.history_retention_hours)

        for key in self.request_events:
            # deque의 왼쪽부터 오래된 항목 제거
            while (self.request_events[key] and
                   self.request_events[key][0].timestamp < cutoff_time):
                self.request_events[key].popleft()
