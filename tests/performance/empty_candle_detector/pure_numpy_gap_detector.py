"""
Pure Numpy Gap Detection Method - 완전 벡터화 방식

목적: 성능 비교를 위한 순수 numpy 벡터화 Gap 감지 로직 구현
- TimeUtils 호출을 완전히 우회하여 모든 계산을 numpy로 처리
- timestamp 기반 완전 벡터화 연산
- datetime 변환을 마지막에 한 번만 수행
- 예상 성능 향상: 200-300%

Created: 2025-09-21
"""

import sys
from datetime import datetime, timezone
from typing import List, Optional
from pathlib import Path
from dataclasses import dataclass
import numpy as np

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils


@dataclass
class PureNumpyGapInfo:
    """순수 Numpy 방식용 Gap 정보 저장 모델"""
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


class PureNumpyGapDetector:
    """
    순수 Numpy 벡터화 Gap 감지기

    완전 벡터화 최적화:
    - TimeUtils 호출을 완전히 우회
    - 모든 계산을 numpy timestamp 기반으로 처리
    - datetime 변환을 마지막에 한 번만 수행
    - 벡터화된 Gap 정보 일괄 생성
    - 예상 성능 향상: 200-300%
    """

    def __init__(self, symbol: str, timeframe: str):
        """
        Pure Numpy Gap Detector 초기화

        Args:
            symbol: 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '1h', etc.)
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self._timeframe_delta_ms = TimeUtils.get_timeframe_ms(timeframe)

    def detect_gaps_pure_numpy(
        self,
        datetime_list: List[datetime],
        market: str,
        api_start: Optional[datetime] = None,
        api_end: Optional[datetime] = None,
        fallback_reference: Optional[str] = None,
        is_first_chunk: bool = False
    ) -> List[PureNumpyGapInfo]:
        """
        순수 Numpy 벡터화 Gap 감지 메서드

        완전 벡터화 최적화:
        1. 모든 datetime을 timestamp로 변환 (한 번만)
        2. numpy 벡터화 연산으로 모든 Gap 계산
        3. 벡터화된 예상 시간 계산
        4. 결과를 일괄 datetime 변환 (마지막에 한 번만)

        Args:
            datetime_list: 순수 datetime 리스트 (업비트 내림차순 정렬)
            market: 마켓 정보 (예: "KRW-BTC")
            api_start: Gap 검출 시작점
            api_end: Gap 검출 종료점
            fallback_reference: 안전한 참조 상태 (문자열 또는 None)
            is_first_chunk: 첫 번째 청크 여부

        Returns:
            List[PureNumpyGapInfo]: 감지된 Gap 정보 (순수 numpy 방식)
        """
        if not datetime_list:
            return []

        # 업비트 내림차순 정렬 확보 (최신 → 과거)
        sorted_datetimes = sorted(datetime_list, reverse=True)

        # 청크2부터 api_start +1틱 추가 (청크 경계 Gap 검출 해결)
        if api_start and not is_first_chunk:
            # 🚀 numpy로 직접 계산: api_start + 1틱
            api_start_plus_one_ms = int(api_start.timestamp() * 1000) + self._timeframe_delta_ms
            api_start_plus_one = datetime.fromtimestamp(api_start_plus_one_ms / 1000, tz=timezone.utc)
            extended_datetimes = [api_start_plus_one] + sorted_datetimes
        else:
            extended_datetimes = sorted_datetimes

        # api_end 처리: 마지막 Gap 감지를 위해 api_end-1틱을 리스트에 추가
        if api_end:
            # 🚀 numpy로 직접 계산: api_end - 1틱
            api_end_minus_one_ms = int(api_end.timestamp() * 1000) - self._timeframe_delta_ms
            api_end_minus_one = datetime.fromtimestamp(api_end_minus_one_ms / 1000, tz=timezone.utc)
            extended_datetimes.append(api_end_minus_one)

        gaps = []

        # 1. 첫 번째 캔들과 api_start 비교 (첫 청크에서만 적용)
        if api_start and is_first_chunk and extended_datetimes:
            first_time = extended_datetimes[0]
            if first_time < api_start:
                # 🚀 numpy로 직접 계산: gap_end = first_time + 1틱
                gap_end_ms = int(first_time.timestamp() * 1000) + self._timeframe_delta_ms
                gap_end_time = datetime.fromtimestamp(gap_end_ms / 1000, tz=timezone.utc)

                gap_info = PureNumpyGapInfo(
                    gap_start=api_start,
                    gap_end=gap_end_time,
                    market=market,
                    reference_state=fallback_reference,
                    timeframe=self.timeframe
                )
                gaps.append(gap_info)

        # 🚀 2. 순수 numpy 벡터화된 Gap 검출
        if len(extended_datetimes) >= 2:
            # 🚀 모든 datetime을 한 번에 timestamp 배열로 변환
            timestamps = np.array([
                int(dt.timestamp() * 1000) for dt in extended_datetimes
            ])

            # 🚀 벡터화된 차분과 예상 시간 계산
            deltas = timestamps[:-1] - timestamps[1:]
            expected_timestamps = timestamps[:-1] - self._timeframe_delta_ms

            # Gap 마스크
            gap_mask = deltas > self._timeframe_delta_ms

            if np.any(gap_mask):
                # 🚀 벡터화된 Gap 정보 생성
                gap_starts_ms = expected_timestamps[gap_mask]
                gap_ends_ms = timestamps[1:][gap_mask]
                gap_reference_indices = np.where(gap_mask)[0] + 1  # reference는 idx+1

                # 🚀 일괄 datetime 변환 (마지막에 한 번만)
                for i, (start_ms, end_ms, ref_idx) in enumerate(zip(gap_starts_ms, gap_ends_ms, gap_reference_indices)):
                    gap_start_time = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc)
                    gap_end_time = datetime.fromtimestamp(end_ms / 1000, tz=timezone.utc)
                    reference_time = extended_datetimes[ref_idx]

                    gap_info = PureNumpyGapInfo(
                        gap_start=gap_start_time,          # 실제 첫 번째 빈 캔들 시간
                        gap_end=gap_end_time,              # 실제 마지막 빈 캔들 시간
                        market=market,
                        reference_state=reference_time.strftime('%Y-%m-%dT%H:%M:%S'),
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
    ) -> List[PureNumpyGapInfo]:
        """
        사전 필터링 없는 전체 프로세스 (순수 numpy 방식)

        Args:
            api_candles: 업비트 API 원시 응답 데이터 (Dict 리스트)
            api_start: API 검출 범위 시작 시간
            api_end: API 검출 범위 종료 시간
            fallback_reference: 안전한 참조 시간
            is_first_chunk: 첫 번째 청크 여부

        Returns:
            List[PureNumpyGapInfo]: 감지된 Gap 정보
        """
        # 🚀 api_candles 필터링 제거로 빈 배열 발생하지 않음
        # 빈 배열 전체 청크 처리 로직 제거됨
        processed_candles = api_candles or []

        # 🚀 순수 시간 정보 추출 (메모리 최적화)
        datetime_list = [self._parse_utc_time(candle["candle_date_time_utc"]) for candle in processed_candles]

        # Gap 감지 (순수 numpy 방식)
        gaps = self.detect_gaps_pure_numpy(
            datetime_list, self.symbol, api_start, api_end, fallback_reference, is_first_chunk
        )

        return gaps

    def detect_gaps_ultra_optimized(
        self,
        api_candles: List[dict],
        api_start: Optional[datetime] = None,
        api_end: Optional[datetime] = None,
        fallback_reference: Optional[str] = None,
        is_first_chunk: bool = False
    ) -> List[PureNumpyGapInfo]:
        """
        🚀 울트라 최적화: timestamp 직접 추출 + 전체 벡터화

        극한 성능 최적화:
        1. API 응답에서 timestamp를 직접 추출 (datetime 변환 최소화)
        2. 모든 계산을 numpy timestamp로 처리
        3. 결과만 datetime으로 변환

        Args:
            api_candles: 업비트 API 원시 응답 데이터
            api_start: API 검출 범위 시작 시간
            api_end: API 검출 범위 종료 시간
            fallback_reference: 안전한 참조 시간
            is_first_chunk: 첫 번째 청크 여부

        Returns:
            List[PureNumpyGapInfo]: 감지된 Gap 정보
        """
        processed_candles = api_candles or []

        if not processed_candles:
            if self.symbol and api_start and api_end:
                gap_info = PureNumpyGapInfo(
                    gap_start=api_start,
                    gap_end=api_end,
                    market=self.symbol,
                    reference_state=fallback_reference,
                    timeframe=self.timeframe
                )
                return [gap_info]
            return []

        # 🚀 울트라 최적화: timestamp 직접 추출 (datetime 변환 최소화)
        if "timestamp" in processed_candles[0]:
            # API에서 timestamp를 직접 사용 (밀리초 단위)
            timestamps = np.array([candle["timestamp"] for candle in processed_candles])
        else:
            # 백업: datetime 문자열에서 timestamp 계산
            timestamps = np.array([
                int(self._parse_utc_time(candle["candle_date_time_utc"]).timestamp() * 1000)
                for candle in processed_candles
            ])

        # 업비트 내림차순 정렬 (최신 → 과거)
        timestamps = np.sort(timestamps)[::-1]

        # 청크2부터 api_start +1틱 추가
        if api_start and not is_first_chunk:
            api_start_plus_one_ms = int(api_start.timestamp() * 1000) + self._timeframe_delta_ms
            timestamps = np.concatenate([[api_start_plus_one_ms], timestamps])

        # api_end 처리
        if api_end:
            api_end_minus_one_ms = int(api_end.timestamp() * 1000) - self._timeframe_delta_ms
            timestamps = np.concatenate([timestamps, [api_end_minus_one_ms]])

        gaps = []

        # 첫 번째 캔들과 api_start 비교
        if api_start and is_first_chunk and len(timestamps) > 0:
            api_start_ms = int(api_start.timestamp() * 1000)
            if timestamps[0] < api_start_ms:
                gap_start_time = api_start
                gap_end_time = datetime.fromtimestamp((timestamps[0] + self._timeframe_delta_ms) / 1000, tz=timezone.utc)

                gap_info = PureNumpyGapInfo(
                    gap_start=gap_start_time,
                    gap_end=gap_end_time,
                    market=self.symbol,
                    reference_state=fallback_reference,
                    timeframe=self.timeframe
                )
                gaps.append(gap_info)

        # 🚀 완전 벡터화된 Gap 검출
        if len(timestamps) >= 2:
            deltas = timestamps[:-1] - timestamps[1:]
            expected_timestamps = timestamps[:-1] - self._timeframe_delta_ms
            gap_mask = deltas > self._timeframe_delta_ms

            if np.any(gap_mask):
                gap_starts_ms = expected_timestamps[gap_mask]
                gap_ends_ms = timestamps[1:][gap_mask]
                gap_reference_indices = np.where(gap_mask)[0] + 1

                # 일괄 datetime 변환
                for start_ms, end_ms, ref_idx in zip(gap_starts_ms, gap_ends_ms, gap_reference_indices):
                    gap_start_time = datetime.fromtimestamp(float(start_ms) / 1000, tz=timezone.utc)
                    gap_end_time = datetime.fromtimestamp(float(end_ms) / 1000, tz=timezone.utc)
                    reference_time = datetime.fromtimestamp(float(timestamps[ref_idx]) / 1000, tz=timezone.utc)

                    gap_info = PureNumpyGapInfo(
                        gap_start=gap_start_time,
                        gap_end=gap_end_time,
                        market=self.symbol,
                        reference_state=reference_time.strftime('%Y-%m-%dT%H:%M:%S'),
                        timeframe=self.timeframe
                    )
                    gaps.append(gap_info)

        return gaps

    def _parse_utc_time(self, utc_string: str) -> datetime:
        """UTC 시간 문자열을 datetime 객체로 변환"""
        try:
            return datetime.fromisoformat(utc_string).replace(tzinfo=timezone.utc)
        except Exception:
            raise ValueError(f"잘못된 UTC 시간 형식: {utc_string}")

    def get_stats(self) -> dict:
        """Pure Numpy Gap Detector 통계 정보 반환"""
        return {
            "method": "pure_numpy_vectorized",
            "timeframe": self.timeframe,
            "timeframe_delta_ms": self._timeframe_delta_ms,
            "preprocessing": "api_end_filtering_removed",
            "chunk_boundary_fix": "api_start_plus_one_tick",
            "optimization": "complete_numpy_vectorization",
            "features": [
                "timestamp_direct_extraction",
                "vectorized_gap_calculation",
                "batch_datetime_conversion",
                "ultra_optimized_variant"
            ],
            "expected_improvement": "200-300%"
        }
