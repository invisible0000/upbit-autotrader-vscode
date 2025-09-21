"""
Original Gap Detection Method - 기존 루프 기반 방식

목적: 성능 비교를 위한 기존 Gap 감지 로직 독립 구현
- 루프 기반 순차 처리
- 기존 EmptyCandleDetector 로직 재현
- TimeUtils 의존성 포함

Created: 2025-09-21
"""

import sys
from datetime import datetime, timezone
from typing import List, Optional
from pathlib import Path
from dataclasses import dataclass

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils


@dataclass
class OriginalGapInfo:
    """기존 방식용 Gap 정보 저장 모델"""
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


class OriginalGapDetector:
    """
    기존 루프 기반 Gap 감지기

    EmptyCandleDetector의 원래 로직을 독립적으로 재현:
    - 순차적 루프 기반 처리
    - 사전 필터링 포함
    - 기존 성능 특성 유지
    """

    def __init__(self, symbol: str, timeframe: str):
        """
        Original Gap Detector 초기화

        Args:
            symbol: 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '1h', etc.)
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self._timeframe_delta_ms = TimeUtils.get_timeframe_ms(timeframe)

    def detect_gaps_original(
        self,
        datetime_list: List[datetime],
        market: str,
        api_start: Optional[datetime] = None,
        api_end: Optional[datetime] = None,
        fallback_reference: Optional[str] = None
    ) -> List[OriginalGapInfo]:
        """
        기존 루프 기반 Gap 감지 메서드

        원래 EmptyCandleDetector의 _detect_gaps_in_datetime_list 로직 재현:
        - 순차적 for 루프
        - TimeUtils 호출 기반
        - 기존 성능 특성 유지

        Args:
            datetime_list: 순수 datetime 리스트 (업비트 내림차순 정렬)
            market: 마켓 정보 (예: "KRW-BTC")
            api_start: Gap 검출 시작점
            api_end: Gap 검출 종료점
            fallback_reference: 안전한 참조 상태 (문자열 또는 None)

        Returns:
            List[OriginalGapInfo]: 감지된 Gap 정보 (기존 방식)
        """

        # # 🔍 디버깅: 입력 파라미터 로깅
        # print(f"\n🔍 detect_gaps_original 호출:")
        # print(f"  • datetime_list 개수: {len(datetime_list)}개")
        # print(f"  • market: {market}")
        # print(f"  • api_start: {api_start}")
        # print(f"  • api_end: {api_end}")
        # print(f"  • fallback_reference: {fallback_reference}")

        # if datetime_list:
        #     print(f"  • datetime_list 샘플 (처음 5개):")
        #     for i, dt in enumerate(datetime_list[:5]):
        #         print(f"    [{i+1}] {dt}")

        # 업비트 내림차순 정렬 확보 (최신 → 과거)
        sorted_datetimes = sorted(datetime_list, reverse=True)

        # api_end 처리: 마지막 Gap 감지를 위해 api_end-1틱을 리스트에 추가
        if api_end:
            sorted_datetimes.append(TimeUtils.get_time_by_ticks(api_end, self.timeframe, -1))

        gaps = []

        # 1. 첫 번째 캔들과 api_start 비교 (처음부터 빈 캔들 검출)
        if api_start and sorted_datetimes:
            first_time = sorted_datetimes[0]
            expected_first = api_start

            if first_time < expected_first:
                # 첫 번째 Gap: 실제 빈 캔들 범위 계산 (업비트 내림차순: start > end)
                # gap_start_time = TimeUtils.get_time_by_ticks(expected_first, self.timeframe, -1)  # 첫 번째 빈 캔들 (최신)
                gap_start_time = expected_first  # api_start와 first_time가 다르므로 expected_first 부터 빈 캔들 시작
                gap_end_time = TimeUtils.get_time_by_ticks(first_time, self.timeframe, 1)        # 마지막 빈 캔들 (과거)
                gap_info = OriginalGapInfo(
                    gap_start=gap_start_time,     # 실제 첫 번째 빈 캔들 시간
                    gap_end=gap_end_time,         # 실제 마지막 빈 캔들 시간
                    market=market,
                    reference_state=fallback_reference,
                    timeframe=self.timeframe
                )
                gaps.append(gap_info)

        # 2. 순차적 Gap 검출 루프 (기존 방식)
        for i in range(1, len(sorted_datetimes)):
            previous_time = sorted_datetimes[i - 1]  # 더 최신
            current_time = sorted_datetimes[i]       # 더 과거

            # Gap 검출 로직
            expected_current = TimeUtils.get_time_by_ticks(previous_time, self.timeframe, -1)

            if current_time < expected_current:
                # Gap 발견: 실제 빈 캔들 범위를 GapInfo에 저장 (업비트 내림차순: start > end)
                gap_start_time = expected_current                                           # 첫 번째 빈 캔들 (최신)
                gap_end_time = TimeUtils.get_time_by_ticks(current_time, self.timeframe, 1)  # 마지막 빈 캔들 (과거)
                gap_info = OriginalGapInfo(
                    gap_start=gap_start_time,          # 실제 첫 번째 빈 캔들 시간
                    gap_end=gap_end_time,              # 실제 마지막 빈 캔들 시간
                    # gap_end=current_time,              # 실제 마지막 빈 캔들 시간
                    market=market,
                    reference_state=previous_time.strftime('%Y-%m-%dT%H:%M:%S'),
                    timeframe=self.timeframe
                )
                gaps.append(gap_info)

        return gaps

    def detect_gaps_with_preprocessing(
        self,
        api_candles: List[dict],
        api_start: Optional[datetime] = None,
        api_end: Optional[datetime] = None,
        fallback_reference: Optional[str] = None
    ) -> List[OriginalGapInfo]:
        """
        사전 필터링을 포함한 전체 프로세스 재현

        기존 detect_and_fill_gaps의 Gap 검출 부분만 추출:
        - 사전 필터링 포함
        - datetime 리스트 변환
        - Gap 검출

        Args:
            api_candles: 업비트 API 원시 응답 데이터 (Dict 리스트)
            api_start: API 검출 범위 시작 시간
            api_end: API 검출 범위 종료 시간
            fallback_reference: 안전한 참조 시간

        Returns:
            List[OriginalGapInfo]: 감지된 Gap 정보
        """
        # 🚀 1. 사전 필터링: api_end보다 과거인 캔들 제거 (기존 방식)
        if api_end and api_candles:
            filtered_candles = [
                candle for candle in api_candles
                if self._parse_utc_time(candle["candle_date_time_utc"]) >= api_end
            ]
        else:
            filtered_candles = api_candles or []

        # 2. 순수 시간 정보 추출
        datetime_list = []
        if filtered_candles:
            datetime_list = [self._parse_utc_time(candle["candle_date_time_utc"]) for candle in filtered_candles]

        # 빈 배열 처리
        if not filtered_candles:
            if self.symbol and api_start and api_end:
                gap_info = OriginalGapInfo(
                    gap_start=api_start,
                    gap_end=api_end,
                    market=self.symbol,
                    reference_state=fallback_reference,
                    timeframe=self.timeframe
                )
                return [gap_info]
            return []

        # 3. Gap 감지 (기존 방식)
        gaps = self.detect_gaps_original(datetime_list, self.symbol, api_start, api_end, fallback_reference)

        return gaps

    def _parse_utc_time(self, utc_string: str) -> datetime:
        """UTC 시간 문자열을 datetime 객체로 변환"""
        try:
            return datetime.fromisoformat(utc_string).replace(tzinfo=timezone.utc)
        except Exception as e:
            raise ValueError(f"잘못된 UTC 시간 형식: {utc_string}")

    def get_stats(self) -> dict:
        """Original Gap Detector 통계 정보 반환"""
        return {
            "method": "original_loop_based",
            "timeframe": self.timeframe,
            "timeframe_delta_ms": self._timeframe_delta_ms,
            "preprocessing": "api_end_filtering_enabled"
        }
