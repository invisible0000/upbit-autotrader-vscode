"""
지능형 겹침 분석기 (Overlap Analyzer)

캐시와 요청 범위 간의 겹침을 지능적으로 분석하여 최적 전략을 결정합니다.

핵심 기능:
- 연속성 패턴 감지 (FORWARD_EXTEND, BACKWARD_EXTEND)
- 포함 관계 분석 (CONTAINED, COMPLETE_CONTAINMENT)
- 부분 겹침 비용 분석 (PARTIAL_OVERLAP)
- API vs DB 비용 추정
"""
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import time

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("OverlapAnalyzer")


class ContinuityType(Enum):
    """연속성 타입"""
    PERFECT_MATCH = "PERFECT_MATCH"           # 완전 일치
    COMPLETE_CONTAINMENT = "COMPLETE_CONTAINMENT"  # 완전 포함 (요청이 캐시 내부)
    FORWARD_EXTEND = "FORWARD_EXTEND"         # 순방향 확장 (시간 증가)
    BACKWARD_EXTEND = "BACKWARD_EXTEND"       # 역방향 확장 (시간 감소)
    BOTH_EXTEND = "BOTH_EXTEND"               # 양방향 확장
    PARTIAL_OVERLAP = "PARTIAL_OVERLAP"       # 부분 겹침 (비연속)
    NO_OVERLAP = "NO_OVERLAP"                 # 겹침 없음


class CacheStrategy(Enum):
    """캐시 전략"""
    USE_CACHE_DIRECT = "USE_CACHE_DIRECT"     # 캐시 직접 사용
    EXTEND_CACHE = "EXTEND_CACHE"             # 캐시 확장
    PARTIAL_FILL = "PARTIAL_FILL"             # 부분 채움
    FULL_REFRESH = "FULL_REFRESH"             # 전체 갱신


@dataclass
class TimeRange:
    """시간 범위"""
    start: datetime
    end: datetime
    count: int = 0

    def __post_init__(self):
        if self.start > self.end:
            raise ValueError(f"시작시간이 종료시간보다 늦습니다: {self.start} > {self.end}")

    @property
    def duration_seconds(self) -> float:
        """범위 길이 (초)"""
        return (self.end - self.start).total_seconds()

    def overlaps_with(self, other: 'TimeRange') -> bool:
        """다른 범위와 겹치는지 확인"""
        return not (self.end <= other.start or self.start >= other.end)

    def intersection(self, other: 'TimeRange') -> Optional['TimeRange']:
        """교집합 계산"""
        if not self.overlaps_with(other):
            return None

        start = max(self.start, other.start)
        end = min(self.end, other.end)
        return TimeRange(start, end)

    def union(self, other: 'TimeRange') -> 'TimeRange':
        """합집합 계산"""
        start = min(self.start, other.start)
        end = max(self.end, other.end)
        return TimeRange(start, end)

    def is_continuous_with(self, other: 'TimeRange', gap_tolerance_seconds: float = 0.0) -> bool:
        """연속성 확인 (허용 간격 내)"""
        gap1 = abs((self.end - other.start).total_seconds())
        gap2 = abs((other.end - self.start).total_seconds())
        return gap1 <= gap_tolerance_seconds or gap2 <= gap_tolerance_seconds

    def __str__(self) -> str:
        return f"TimeRange({self.start.strftime('%H:%M:%S')} ~ {self.end.strftime('%H:%M:%S')}, {self.count}개)"


@dataclass
class OverlapAnalysisResult:
    """겹침 분석 결과"""
    continuity_type: ContinuityType
    overlap_ratio: float                      # 겹침 비율 (0.0 ~ 1.0)
    missing_ratio: float                      # 누락 비율 (0.0 ~ 1.0)
    cache_range: TimeRange
    request_range: TimeRange
    intersection_range: Optional[TimeRange]
    missing_ranges: List[TimeRange]

    # 비용 추정
    api_call_count_estimate: int
    db_query_count_estimate: int
    cache_efficiency_score: float            # 캐시 효율성 점수 (0.0 ~ 1.0)

    # 전략 추천
    recommended_strategy: CacheStrategy
    strategy_confidence: float               # 전략 확신도 (0.0 ~ 1.0)

    # 메타데이터
    analysis_timestamp: datetime
    analysis_duration_ms: float


class OverlapAnalyzer:
    """
    지능형 겹침 분석기

    캐시 범위와 요청 범위 간의 겹침을 분석하여 최적 전략을 결정합니다.
    """

    def __init__(self):
        # 전략 결정 임계값
        self.STRATEGY_THRESHOLDS = {
            "PERFECT_MATCH": {"min_ratio": 1.0, "confidence": 1.0},
            "COMPLETE_CONTAINMENT": {"min_ratio": 1.0, "confidence": 0.95},
            "CONTINUITY_EXTEND": {"min_ratio": 0.95, "max_api_calls": 1, "confidence": 0.9},
            "PARTIAL_FILL": {"min_ratio": 0.7, "max_api_calls": 50, "max_db_queries": 2, "confidence": 0.7},
            "FULL_REFRESH": {"min_ratio": 0.0, "confidence": 0.5}
        }

        # 비용 가중치 (상대적 비용)
        self.COST_WEIGHTS = {
            "api_call": 100,        # API 호출 비용
            "db_query": 10,         # DB 쿼리 비용
            "memory_access": 1,     # 메모리 접근 비용
            "data_merge": 5         # 데이터 병합 비용
        }

        # 성능 통계
        self._analysis_count = 0
        self._total_analysis_time = 0.0

        logger.info("지능형 겹침 분석기 초기화 완료")

    def analyze_overlap(self,
                        cache_range: Union[TimeRange, Tuple[datetime, datetime, int]],
                        request_range: Union[TimeRange, Tuple[datetime, datetime, int]],
                        symbol: str = "",
                        timeframe: str = "") -> OverlapAnalysisResult:
        """
        겹침 분석 실행

        Args:
            cache_range: 캐시 범위 (TimeRange 또는 (start, end, count) 튜플)
            request_range: 요청 범위 (TimeRange 또는 (start, end, count) 튜플)
            symbol: 심볼 (로깅용)
            timeframe: 타임프레임 (로깅용)

        Returns:
            OverlapAnalysisResult: 상세 분석 결과
        """
        start_time = time.time()
        self._analysis_count += 1

        try:
            # TimeRange 객체로 변환
            if isinstance(cache_range, tuple):
                cache_range = TimeRange(cache_range[0], cache_range[1], cache_range[2])
            if isinstance(request_range, tuple):
                request_range = TimeRange(request_range[0], request_range[1], request_range[2])

            logger.debug(f"겹침 분석 시작: {symbol} {timeframe}")
            logger.debug(f"캐시 범위: {cache_range}")
            logger.debug(f"요청 범위: {request_range}")

            # 1. 기본 겹침 분석
            intersection = cache_range.intersection(request_range)
            overlap_ratio = 0.0
            missing_ratio = 1.0

            if intersection:
                # 요청 범위 대비 겹침 비율
                if request_range.duration_seconds > 0:
                    overlap_ratio = intersection.duration_seconds / request_range.duration_seconds
                else:
                    overlap_ratio = 1.0 if cache_range.start <= request_range.start <= cache_range.end else 0.0

                missing_ratio = 1.0 - overlap_ratio

            # 2. 연속성 패턴 분석
            continuity_type = self._analyze_continuity_pattern(cache_range, request_range, intersection)

            # 3. 누락 범위 계산
            missing_ranges = self._calculate_missing_ranges(cache_range, request_range)

            # 4. 비용 추정
            api_calls, db_queries = self._estimate_costs(continuity_type, missing_ranges, request_range)

            # 5. 캐시 효율성 점수 계산
            efficiency_score = self._calculate_cache_efficiency(overlap_ratio, continuity_type, api_calls)

            # 6. 전략 추천
            strategy, confidence = self._recommend_strategy(
                continuity_type, overlap_ratio, api_calls, db_queries, efficiency_score
            )

            analysis_duration = (time.time() - start_time) * 1000
            self._total_analysis_time += analysis_duration

            result = OverlapAnalysisResult(
                continuity_type=continuity_type,
                overlap_ratio=overlap_ratio,
                missing_ratio=missing_ratio,
                cache_range=cache_range,
                request_range=request_range,
                intersection_range=intersection,
                missing_ranges=missing_ranges,
                api_call_count_estimate=api_calls,
                db_query_count_estimate=db_queries,
                cache_efficiency_score=efficiency_score,
                recommended_strategy=strategy,
                strategy_confidence=confidence,
                analysis_timestamp=datetime.now(),
                analysis_duration_ms=analysis_duration
            )

            logger.debug(f"겹침 분석 완료: {symbol} {timeframe}")
            logger.debug(f"결과: {continuity_type.value}, 겹침={overlap_ratio:.1%}, 전략={strategy.value}")

            return result

        except Exception as e:
            logger.error(f"겹침 분석 실패: {symbol} {timeframe}, {e}")
            # 안전한 fallback 결과 반환
            return self._create_fallback_result(cache_range, request_range, start_time)

    def _analyze_continuity_pattern(self, cache_range, request_range, intersection):
        """연속성 패턴 분석"""
        if not intersection:
            return ContinuityType.NO_OVERLAP

        # 완전 일치 확인
        if (cache_range.start == request_range.start and
                cache_range.end == request_range.end):
            return ContinuityType.PERFECT_MATCH

        # 완전 포함 확인 (요청이 캐시 내부에 완전히 포함)
        if (cache_range.start <= request_range.start and
                request_range.end <= cache_range.end):
            return ContinuityType.COMPLETE_CONTAINMENT

        # 연속성 확장 패턴 확인
        gap_tolerance = 60.0  # 1분 허용

        # 순방향 확장 (캐시 끝 ≈ 요청 시작)
        if (cache_range.end <= request_range.end and
                cache_range.is_continuous_with(request_range, gap_tolerance)):

            # 캐시가 요청 시작 부분을 포함하는지 확인
            cache_covers_start = cache_range.start <= request_range.start <= cache_range.end
            if cache_covers_start:
                return ContinuityType.FORWARD_EXTEND

        # 역방향 확장 (요청 끝 ≈ 캐시 시작)
        if (request_range.start <= cache_range.start and
                request_range.is_continuous_with(cache_range, gap_tolerance)):

            # 캐시가 요청 끝 부분을 포함하는지 확인
            cache_covers_end = request_range.start <= cache_range.end <= request_range.end
            if cache_covers_end:
                return ContinuityType.BACKWARD_EXTEND

        # 양방향 확장 (캐시가 요청 중간에 위치)
        if (request_range.start < cache_range.start and
                cache_range.end < request_range.end):
            return ContinuityType.BOTH_EXTEND

        # 부분 겹침 (비연속적)
        return ContinuityType.PARTIAL_OVERLAP

    def _calculate_missing_ranges(self, cache_range, request_range):
        """누락 범위 계산"""
        missing_ranges = []

        try:
            intersection = cache_range.intersection(request_range)

            if not intersection:
                # 전체 요청 범위가 누락
                missing_ranges.append(request_range)
                return missing_ranges

            # 요청 시작 부분이 누락되었는지 확인
            if request_range.start < intersection.start:
                missing_start = TimeRange(
                    request_range.start,
                    intersection.start,
                    0  # 개수는 추후 계산
                )
                missing_ranges.append(missing_start)

            # 요청 끝 부분이 누락되었는지 확인
            if intersection.end < request_range.end:
                missing_end = TimeRange(
                    intersection.end,
                    request_range.end,
                    0  # 개수는 추후 계산
                )
                missing_ranges.append(missing_end)

        except Exception as e:
            logger.warning(f"누락 범위 계산 실패: {e}")
            # 안전한 fallback: 전체 범위를 누락으로 처리
            missing_ranges.append(request_range)

        return missing_ranges

    def _estimate_costs(self, continuity_type, missing_ranges, request_range):
        """비용 추정 (API 호출 수, DB 쿼리 수)"""
        api_calls = 0
        db_queries = 0

        if continuity_type in [ContinuityType.PERFECT_MATCH, ContinuityType.COMPLETE_CONTAINMENT]:
            # 캐시에서 직접 조회
            db_queries = 1
            api_calls = 0

        elif continuity_type in [ContinuityType.FORWARD_EXTEND, ContinuityType.BACKWARD_EXTEND]:
            # 연속 확장: 1회 API 호출 + 1회 DB 쿼리
            api_calls = 1
            db_queries = 1

        elif continuity_type == ContinuityType.BOTH_EXTEND:
            # 양방향 확장: 2회 API 호출 + 1회 DB 쿼리
            api_calls = 2
            db_queries = 1

        elif continuity_type == ContinuityType.PARTIAL_OVERLAP:
            # 부분 겹침: 누락 범위 수만큼 API 호출
            api_calls = len(missing_ranges)
            db_queries = 1  # 기존 캐시 조회

        else:  # NO_OVERLAP
            # 전체 새로 요청
            api_calls = 1
            db_queries = 0

        # 대용량 요청 시 분할 고려 (500개 초과시)
        if request_range.count > 500:
            additional_splits = (request_range.count - 1) // 500
            api_calls += additional_splits

        return api_calls, db_queries

    def _calculate_cache_efficiency(self, overlap_ratio, continuity_type, api_calls):
        """캐시 효율성 점수 계산 (0.0 ~ 1.0)"""
        base_score = overlap_ratio

        # 연속성 타입별 보너스
        continuity_bonus = {
            ContinuityType.PERFECT_MATCH: 0.0,
            ContinuityType.COMPLETE_CONTAINMENT: 0.0,
            ContinuityType.FORWARD_EXTEND: 0.05,
            ContinuityType.BACKWARD_EXTEND: 0.05,
            ContinuityType.BOTH_EXTEND: -0.1,
            ContinuityType.PARTIAL_OVERLAP: -0.2,
            ContinuityType.NO_OVERLAP: -0.5
        }.get(continuity_type, 0.0)

        # API 호출 수에 따른 페널티
        api_penalty = min(api_calls * 0.1, 0.3)  # 최대 30% 페널티

        efficiency = max(0.0, min(1.0, base_score + continuity_bonus - api_penalty))
        return efficiency

    def _recommend_strategy(self, continuity_type, overlap_ratio, api_calls, db_queries, efficiency_score):
        """전략 추천"""

        # 완전 일치 또는 완전 포함
        if continuity_type in [ContinuityType.PERFECT_MATCH, ContinuityType.COMPLETE_CONTAINMENT]:
            return CacheStrategy.USE_CACHE_DIRECT, 1.0

        # 연속 확장 패턴
        if continuity_type in [ContinuityType.FORWARD_EXTEND, ContinuityType.BACKWARD_EXTEND]:
            if api_calls <= 1 and overlap_ratio >= 0.95:
                return CacheStrategy.EXTEND_CACHE, 0.9
            else:
                return CacheStrategy.PARTIAL_FILL, 0.7

        # 부분 겹침
        if continuity_type == ContinuityType.PARTIAL_OVERLAP:
            if overlap_ratio >= 0.7 and api_calls <= 50:
                return CacheStrategy.PARTIAL_FILL, 0.7
            else:
                return CacheStrategy.FULL_REFRESH, 0.6

        # 겹침 없음 또는 비효율적
        if continuity_type == ContinuityType.NO_OVERLAP or efficiency_score < 0.3:
            return CacheStrategy.FULL_REFRESH, 0.5

        # 기본값 (양방향 확장 등)
        return CacheStrategy.PARTIAL_FILL, 0.6

    def _create_fallback_result(self, cache_range, request_range, start_time):
        """안전한 fallback 결과 생성"""
        try:
            if isinstance(cache_range, tuple):
                cache_range = TimeRange(cache_range[0], cache_range[1], cache_range[2])
            if isinstance(request_range, tuple):
                request_range = TimeRange(request_range[0], request_range[1], request_range[2])
        except Exception:
            # 최종 fallback
            now = datetime.now()
            cache_range = TimeRange(now, now, 0)
            request_range = TimeRange(now, now, 0)

        return OverlapAnalysisResult(
            continuity_type=ContinuityType.NO_OVERLAP,
            overlap_ratio=0.0,
            missing_ratio=1.0,
            cache_range=cache_range,
            request_range=request_range,
            intersection_range=None,
            missing_ranges=[request_range],
            api_call_count_estimate=1,
            db_query_count_estimate=0,
            cache_efficiency_score=0.0,
            recommended_strategy=CacheStrategy.FULL_REFRESH,
            strategy_confidence=0.5,
            analysis_timestamp=datetime.now(),
            analysis_duration_ms=(time.time() - start_time) * 1000
        )

    # =====================================
    # 성능 및 통계
    # =====================================

    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 조회"""
        avg_analysis_time = (self._total_analysis_time / self._analysis_count
                           if self._analysis_count > 0 else 0.0)

        return {
            "analysis_count": self._analysis_count,
            "total_analysis_time_ms": self._total_analysis_time,
            "average_analysis_time_ms": avg_analysis_time,
            "strategy_thresholds": self.STRATEGY_THRESHOLDS,
            "cost_weights": self.COST_WEIGHTS
        }

    def reset_stats(self) -> None:
        """통계 초기화"""
        self._analysis_count = 0
        self._total_analysis_time = 0.0
        logger.info("겹침 분석기 통계 초기화 완료")

    def __str__(self) -> str:
        return (f"OverlapAnalyzer("
                f"analyses={self._analysis_count}, "
                f"avg_time={self._total_analysis_time / max(1, self._analysis_count):.1f}ms)")


# =====================================
# 유틸리티 함수
# =====================================

def create_time_range_from_candles(candles: List[Dict[str, Any]]) -> Optional[TimeRange]:
    """캔들 데이터에서 TimeRange 생성"""
    if not candles:
        return None

    try:
        # 시간 추출 (타임스탬프 또는 datetime)
        times = []
        for candle in candles:
            timestamp = candle.get('timestamp') or candle.get('candle_date_time_kst')
            if isinstance(timestamp, str):
                # ISO 형식 문자열을 datetime으로 변환
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                times.append(dt)
            elif isinstance(timestamp, datetime):
                times.append(timestamp)

        if not times:
            return None

        times.sort()
        return TimeRange(
            start=times[0],
            end=times[-1],
            count=len(candles)
        )

    except Exception as e:
        logger.warning(f"캔들에서 TimeRange 생성 실패: {e}")
        return None


def format_analysis_summary(result: OverlapAnalysisResult) -> str:
    """분석 결과 요약 포맷팅"""
    return (f"겹침분석: {result.continuity_type.value} | "
            f"겹침={result.overlap_ratio:.1%} | "
            f"전략={result.recommended_strategy.value} | "
            f"API={result.api_call_count_estimate}회 | "
            f"효율성={result.cache_efficiency_score:.1%}")
