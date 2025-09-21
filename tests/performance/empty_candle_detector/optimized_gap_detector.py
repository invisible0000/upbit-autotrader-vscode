"""
Optimized Gap Detection Method - TimeUtils 호출 최적화 방식

목적: 성능 비교를 위한 TimeUtils 호출 최적화 Gap 감지 로직 구현
- TimeUtils.get_time_by_ticks 호출을 직접 timedelta 계산으로 대체
- numpy 벡터화와 직접 시간 계산의 조합
- 예상 성능 향상: 60-80%

Created: 2025-09-21
"""

import sys
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from pathlib import Path
from dataclasses import dataclass
import numpy as np

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils


@dataclass
class OptimizedGapInfo:
    """최적화 방식용 Gap 정보 저장 모델"""
    gap_start: datetime                    # 실제 빈 캔들 시작 시간
    gap_end: datetime                      # 실제 빈 캔들 종료 시간
    market: str                            # 마켓 정보
    reference_state: Optional[str]         # 참조 상태
    timeframe: str                         # 타임프레임

    def __post_init__(self):
        """Gap 정보 검증 (업비트 정렬: gap_start > gap_end)"""
        if self.gap_start < self.gap_end:
            raise ValueError(f"Gap 시작시간이 종료시간보다 작습니다: {self.gap_start} < {self.gap_end}")
        if not self.market:
            raise ValueError("마켓 정보가 없습니다")
        if not self.timeframe:
            raise ValueError("타임프레임이 지정되지 않았습니다")


class OptimizedGapDetector:
    """
    TimeUtils 호출 최적화 Gap 감지기

    핵심 최적화:
    - TimeUtils.get_time_by_ticks 호출을 직접 timedelta 계산으로 대체
    - numpy 벡터화와 직접 시간 계산의 조합
    - 타임프레임별 미리 계산된 delta 사용
    - 예상 성능 향상: 60-80%
    """

    def __init__(self, symbol: str, timeframe: str):
        """
        Optimized Gap Detector 초기화

        Args:
            symbol: 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '1h', etc.)
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self._timeframe_delta_ms = TimeUtils.get_timeframe_ms(timeframe)

        # 🚀 핵심 최적화: 타임프레임별 미리 계산된 timedelta
        self._timeframe_delta = self._get_timeframe_timedelta(timeframe)

    def _get_timeframe_timedelta(self, timeframe: str) -> timedelta:
        """타임프레임별 timedelta 미리 계산"""
        if timeframe == '1m':
            return timedelta(minutes=1)
        elif timeframe == '5m':
            return timedelta(minutes=5)
        elif timeframe == '15m':
            return timedelta(minutes=15)
        elif timeframe == '30m':
            return timedelta(minutes=30)
        elif timeframe == '1h':
            return timedelta(hours=1)
        elif timeframe == '4h':
            return timedelta(hours=4)
        elif timeframe == '1d':
            return timedelta(days=1)
        elif timeframe == '1w':
            return timedelta(weeks=1)
        elif timeframe == '1M':
            # 월봉은 복잡하므로 TimeUtils 사용 (예외적)
            return None
        elif timeframe == '1y':
            # 년봉은 복잡하므로 TimeUtils 사용 (예외적)
            return None
        else:
            return timedelta(minutes=1)  # 기본값

    def _calculate_expected_time(self, current_time: datetime) -> datetime:
        """
        🚀 핵심 최적화: TimeUtils 대신 직접 시간 계산

        Args:
            current_time: 현재 시간

        Returns:
            datetime: 예상 이전 시간 (1틱 전)
        """
        if self._timeframe_delta is None:
            # 월봉/년봉만 TimeUtils 사용 (복잡한 날짜 산술 필요)
            return TimeUtils.get_time_by_ticks(current_time, self.timeframe, -1)
        else:
            # 🚀 직접 계산: 80% 성능 향상 예상
            return current_time - self._timeframe_delta

    def detect_gaps_optimized(
        self,
        datetime_list: List[datetime],
        market: str,
        api_start: Optional[datetime] = None,
        api_end: Optional[datetime] = None,
        fallback_reference: Optional[str] = None,
        is_first_chunk: bool = False
    ) -> List[OptimizedGapInfo]:
        """
        TimeUtils 호출 최적화 Gap 감지 메서드

        핵심 최적화:
        1. numpy 벡터화로 Gap 위치 찾기 (기존과 동일)
        2. TimeUtils.get_time_by_ticks 호출을 직접 timedelta 계산으로 대체 (60-80% 성능 향상)
        3. 타임프레임별 미리 계산된 delta 사용

        Args:
            datetime_list: 순수 datetime 리스트 (업비트 내림차순 정렬)
            market: 마켓 정보 (예: "KRW-BTC")
            api_start: Gap 검출 시작점
            api_end: Gap 검출 종료점
            fallback_reference: 안전한 참조 상태 (문자열 또는 None)
            is_first_chunk: 첫 번째 청크 여부

        Returns:
            List[OptimizedGapInfo]: 감지된 Gap 정보 (최적화된 방식)
        """
        if not datetime_list:
            return []

        # 업비트 내림차순 정렬 확보 (최신 → 과거)
        sorted_datetimes = sorted(datetime_list, reverse=True)

        # 청크2부터 api_start +1틱 추가 (청크 경계 Gap 검출 해결)
        if api_start and not is_first_chunk:
            api_start_plus_one = self._calculate_expected_time(api_start)
            if api_start_plus_one > api_start:  # 잘못된 계산 방지
                api_start_plus_one = api_start + self._timeframe_delta
            extended_datetimes = [api_start_plus_one] + sorted_datetimes
        else:
            extended_datetimes = sorted_datetimes

        # api_end 처리: 마지막 Gap 감지를 위해 api_end-1틱을 리스트에 추가
        if api_end:
            api_end_minus_one = self._calculate_expected_time(api_end)
            if api_end_minus_one < api_end:  # 올바른 과거 방향 확인
                extended_datetimes.append(api_end_minus_one)

        gaps = []

        # 1. 첫 번째 캔들과 api_start 비교 (첫 청크에서만 적용)
        if api_start and is_first_chunk and extended_datetimes:
            first_time = extended_datetimes[0]
            if first_time < api_start:
                gap_start_time = api_start
                gap_end_time = self._calculate_expected_time(first_time)
                if gap_end_time > first_time:  # 올바른 과거 방향
                    gap_end_time = first_time + self._timeframe_delta

                gap_info = OptimizedGapInfo(
                    gap_start=gap_start_time,
                    gap_end=gap_end_time,
                    market=market,
                    reference_state=fallback_reference,
                    timeframe=self.timeframe
                )
                gaps.append(gap_info)

        # 🚀 2. numpy 벡터화된 Gap 검출 (기존과 동일)
        if len(extended_datetimes) >= 2:
            # timestamp 배열 생성 (밀리초 단위, numpy 연산용)
            timestamps = np.array([
                int(dt.timestamp() * 1000) for dt in extended_datetimes
            ])

            # 벡터화 차분 계산: 업비트 내림차순이므로 양수가 정상 간격
            deltas = timestamps[:-1] - timestamps[1:]

            # Gap 조건: 차분이 timeframe 델타보다 큰 경우
            gap_mask = deltas > self._timeframe_delta_ms

            # Gap 인덱스 추출
            gap_indices = np.where(gap_mask)[0]

            # 3. 🚀 핵심 최적화: TimeUtils 대신 직접 시간 계산
            for idx in gap_indices:
                previous_time = extended_datetimes[idx]      # Gap 직전 (미래)
                current_time = extended_datetimes[idx + 1]   # Gap 직후 (과거, 참조점)

                # 🚀 TimeUtils.get_time_by_ticks 대신 직접 계산
                expected_current = self._calculate_expected_time(previous_time)

                gap_info = OptimizedGapInfo(
                    gap_start=expected_current,            # 실제 첫 번째 빈 캔들 시간
                    gap_end=current_time,                  # 실제 마지막 빈 캔들 시간
                    market=market,
                    reference_state=current_time.strftime('%Y-%m-%dT%H:%M:%S'),
                    timeframe=self.timeframe
                )
                gaps.append(gap_info)

        return gaps

    def detect_gaps_no_preprocessing(
        self,
        api_candles: List[dict],
        api_start: Optional[datetime] = None,
        api_end: Optional[datetime] = None,
        fallback_reference: Optional[str] = None,
        is_first_chunk: bool = False
    ) -> List[OptimizedGapInfo]:
        """
        사전 필터링 없는 전체 프로세스 (TimeUtils 최적화 방식)

        Args:
            api_candles: 업비트 API 원시 응답 데이터 (Dict 리스트)
            api_start: API 검출 범위 시작 시간
            api_end: API 검출 범위 종료 시간
            fallback_reference: 안전한 참조 시간
            is_first_chunk: 첫 번째 청크 여부

        Returns:
            List[OptimizedGapInfo]: 감지된 Gap 정보
        """
        # 사전 필터링 제거: api_candles를 직접 사용 (청크 독립성 유지)
        processed_candles = api_candles or []

        # 순수 시간 정보 추출
        datetime_list = []
        if processed_candles:
            datetime_list = [self._parse_utc_time(candle["candle_date_time_utc"]) for candle in processed_candles]

        # 빈 배열 처리 (전체 범위가 빈 캔들)
        if not processed_candles:
            if self.symbol and api_start and api_end:
                gap_info = OptimizedGapInfo(
                    gap_start=api_start,
                    gap_end=api_end,
                    market=self.symbol,
                    reference_state=fallback_reference,
                    timeframe=self.timeframe
                )
                return [gap_info]
            return []

        # Gap 감지 (TimeUtils 최적화 방식)
        gaps = self.detect_gaps_optimized(
            datetime_list, self.symbol, api_start, api_end, fallback_reference, is_first_chunk
        )

        return gaps

    def _parse_utc_time(self, utc_string: str) -> datetime:
        """UTC 시간 문자열을 datetime 객체로 변환"""
        try:
            return datetime.fromisoformat(utc_string).replace(tzinfo=timezone.utc)
        except Exception:
            raise ValueError(f"잘못된 UTC 시간 형식: {utc_string}")

    def get_stats(self) -> dict:
        """Optimized Gap Detector 통계 정보 반환"""
        return {
            "method": "optimized_timeutils_bypass",
            "timeframe": self.timeframe,
            "timeframe_delta_ms": self._timeframe_delta_ms,
            "preprocessing": "api_end_filtering_removed",
            "chunk_boundary_fix": "api_start_plus_one_tick",
            "optimization": "direct_timedelta_calculation",
            "expected_improvement": "60-80%"
        }
