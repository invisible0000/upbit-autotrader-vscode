"""
CandleDataProvider v4.0 - Time Utilities
시간 계산 및 청크 분할 Infrastructure Utility

핵심 기능:
- 5가지 파라미터 조합 처리 (count/start_time/end_time)
- 업비트 UTC 시간 정렬 (검증된 패턴 기반)
- 200개 청크 분할 계산
- overlap_analyzer 연동 지원

설계 원칙:
- 업비트 API와 100% 일치하는 시간 정렬
- smart_data_provider_V4/time_utils.py의 검증된 로직 활용
- CandleDataProvider의 복잡한 시간 계산 담당
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("TimeUtils")


class ValidationError(Exception):
    """시간 파라미터 유효성 검사 에러"""
    pass


@dataclass(frozen=True)
class TimeChunk:
    """시간 기반 청크 정보"""
    start_time: datetime
    end_time: datetime
    expected_count: int
    chunk_index: int


class TimeUtils:
    """
    CandleDataProvider v4.0 시간 계산 유틸리티

    핵심 역할:
    - 다양한 파라미터 조합을 표준화된 (start_time, end_time, count) 튜플로 변환
    - 업비트 UTC 경계에 맞는 시간 정렬 (검증된 패턴)
    - 대량 요청의 200개 청크 분할
    - overlap_analyzer와의 시간 계산 연동
    """

    @staticmethod
    def determine_target_end_time(
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        timeframe: str = "1m"
    ) -> Tuple[datetime, datetime, int]:
        """
        모든 파라미터 조합을 처리하여 표준화된 (start_time, end_time, count) 반환

        지원하는 5가지 패턴:
        1. count만: 현재시간부터 역순으로 count개
        2. start_time + count: 시작점부터 count개
        3. start_time + end_time: 시간 범위로 count 자동 계산
        4. end_time만: 현재시간부터 end_time까지 count 자동 계산
        5. count + end_time: ValidationError (상호 배타적)

        Args:
            count: 캔들 개수 (옵션)
            start_time: 시작 시간 (옵션)
            end_time: 종료 시간 (옵션)
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)

        Returns:
            Tuple[datetime, datetime, int]: (계산된_start_time, 계산된_end_time, 계산된_count)

        Raises:
            ValidationError: 잘못된 파라미터 조합 또는 값
        """
        logger.debug(f"파라미터 조합 처리 시작: count={count}, start_time={start_time}, end_time={end_time}, timeframe={timeframe}")

        # 유효성 검사
        TimeUtils._validate_time_params(count, start_time, end_time)

        current_time = datetime.now(timezone.utc)
        timeframe_seconds = TimeUtils.get_timeframe_seconds(timeframe)

        # 1. count + end_time 동시 제공 → 에러
        if count is not None and end_time is not None:
            raise ValidationError("count와 end_time을 동시에 제공할 수 없습니다 (상호 배타적)")

        # 2. count만 제공 → 현재시간부터 역순
        elif count is not None and start_time is None and end_time is None:
            aligned_end = TimeUtils._align_to_candle_boundary(current_time, timeframe)
            # 올림 정렬 후 미래 시간 검증
            if aligned_end > current_time:
                raise ValidationError(
                    f"올림 정렬된 end_time이 현재시간보다 미래입니다: {aligned_end} > {current_time}\n"
                    f"현재시간이 캔들 경계가 아니어서 올림되었습니다. 더 과거 시간을 사용하거나 잠시 후 다시 시도해주세요."
                )
            calculated_start = aligned_end - timedelta(seconds=timeframe_seconds * (count - 1))
            logger.debug(f"count만 제공 → 현재시간 역순: {calculated_start} ~ {aligned_end} ({count}개)")
            return calculated_start, aligned_end, count

        # 3. start_time + count → end_time 계산 (과거 방향)
        elif start_time is not None and count is not None and end_time is None:
            aligned_start = TimeUtils._align_to_candle_boundary(start_time, timeframe)
            # 올림 정렬 후 미래 시간 검증
            if aligned_start > current_time:
                raise ValidationError(
                    f"올림 정렬된 start_time이 현재시간보다 미래입니다: {aligned_start} > {current_time}\n"
                    f"요청 시간 {start_time}이 캔들 경계가 아니어서 {aligned_start}로 올림되었습니다.\n"
                    f"더 과거 시간을 사용하거나 잠시 후 다시 시도해주세요."
                )
            # 업비트 API는 start_time부터 과거로 수집하므로 end_time은 더 과거여야 함
            calculated_end = aligned_start - timedelta(seconds=timeframe_seconds * (count - 1))
            # 업비트 방향 (latest → past): start_time이 latest, calculated_end가 past
            logger.debug(f"start_time + count → end_time 계산 (과거 방향): {aligned_start} → {calculated_end} ({count}개)")
            return calculated_end, aligned_start, count

        # 4. start_time + end_time → count 계산
        elif start_time is not None and end_time is not None and count is None:
            aligned_start = TimeUtils._align_to_candle_boundary(start_time, timeframe)
            aligned_end = TimeUtils._align_to_candle_boundary(end_time, timeframe)

            # 올림 정렬 후 미래 시간 검증
            if aligned_start > current_time:
                raise ValidationError(
                    f"올림 정렬된 start_time이 현재시간보다 미래입니다: {aligned_start} > {current_time}\n"
                    f"요청 시간 {start_time}이 캔들 경계가 아니어서 {aligned_start}로 올림되었습니다.\n"
                    f"더 과거 시간을 사용하거나 잠시 후 다시 시도해주세요."
                )
            if aligned_end > current_time:
                raise ValidationError(
                    f"올림 정렬된 end_time이 현재시간보다 미래입니다: {aligned_end} > {current_time}\n"
                    f"요청 시간 {end_time}이 캔들 경계가 아니어서 {aligned_end}로 올림되었습니다.\n"
                    f"더 과거 시간을 사용하거나 잠시 후 다시 시도해주세요."
                )

            if aligned_end <= aligned_start:
                raise ValidationError(f"end_time ({aligned_end})이 start_time ({aligned_start})보다 작거나 같습니다")

            time_diff_seconds = int((aligned_end - aligned_start).total_seconds())
            calculated_count = (time_diff_seconds // timeframe_seconds) + 1
            logger.debug(f"start_time + end_time → count 계산: {aligned_start} ~ {aligned_end} ({calculated_count}개)")
            return aligned_start, aligned_end, calculated_count

        # 5. end_time만 제공 → 현재시간부터 end_time까지
        elif end_time is not None and start_time is None and count is None:
            aligned_end = TimeUtils._align_to_candle_boundary(end_time, timeframe)
            aligned_current = TimeUtils._align_to_candle_boundary(current_time, timeframe)

            # 올림 정렬 후 미래 시간 검증
            if aligned_current > current_time:
                raise ValidationError(
                    f"올림 정렬된 현재시간이 실제 현재시간보다 미래입니다: {aligned_current} > {current_time}\n"
                    f"현재시간이 캔들 경계가 아니어서 올림되었습니다. 잠시 후 다시 시도해주세요."
                )

            if aligned_end >= aligned_current:
                raise ValidationError(f"end_time ({aligned_end})이 현재시간 ({aligned_current})보다 미래입니다")

            time_diff_seconds = int((aligned_current - aligned_end).total_seconds())
            calculated_count = (time_diff_seconds // timeframe_seconds) + 1
            logger.debug(f"end_time만 제공 → 현재시간부터: {aligned_end} ~ {aligned_current} ({calculated_count}개)")
            return aligned_end, aligned_current, calculated_count

        # 6. 아무것도 제공하지 않음 → 기본값 (최근 200개)
        elif count is None and start_time is None and end_time is None:
            default_count = 200
            aligned_end = TimeUtils._align_to_candle_boundary(current_time, timeframe)
            # 올림 정렬 후 미래 시간 검증
            if aligned_end > current_time:
                raise ValidationError(
                    f"올림 정렬된 현재시간이 실제 현재시간보다 미래입니다: {aligned_end} > {current_time}\n"
                    f"현재시간이 캔들 경계가 아니어서 올림되었습니다. 잠시 후 다시 시도해주세요."
                )
            calculated_start = aligned_end - timedelta(seconds=timeframe_seconds * (default_count - 1))
            logger.debug(f"기본값 사용 → 최근 {default_count}개: {calculated_start} ~ {aligned_end}")
            return calculated_start, aligned_end, default_count

        else:
            raise ValidationError(f"지원하지 않는 파라미터 조합: count={count}, start_time={start_time}, end_time={end_time}")

    @staticmethod
    def calculate_chunk_boundaries(
        start_time: datetime,
        end_time: datetime,
        timeframe: str,
        chunk_size: int = 200
    ) -> List[TimeChunk]:
        """
        대량 요청을 청크 단위로 분할

        Args:
            start_time: 전체 시작 시간
            end_time: 전체 종료 시간
            timeframe: 타임프레임
            chunk_size: 청크당 캔들 개수 (기본 200개)

        Returns:
            List[TimeChunk]: 분할된 청크 목록
        """
        logger.debug(f"청크 분할 시작: {start_time} ~ {end_time}, chunk_size={chunk_size}")

        timeframe_seconds = TimeUtils.get_timeframe_seconds(timeframe)
        total_seconds = int((end_time - start_time).total_seconds())
        total_count = (total_seconds // timeframe_seconds) + 1

        if total_count <= chunk_size:
            # 청크 분할 불필요
            logger.debug(f"청크 분할 불필요: 총 {total_count}개 ≤ {chunk_size}")
            return [TimeChunk(
                start_time=start_time,
                end_time=end_time,
                expected_count=total_count,
                chunk_index=0
            )]

        chunks = []
        current_start = start_time
        chunk_index = 0

        while current_start < end_time:
            # 현재 청크의 종료 시간 계산
            chunk_end = current_start + timedelta(seconds=timeframe_seconds * (chunk_size - 1))

            # 마지막 청크 처리: 전체 종료 시간을 넘지 않도록
            if chunk_end > end_time:
                chunk_end = end_time

            # 청크 생성
            chunk_seconds = int((chunk_end - current_start).total_seconds())
            chunk_count = (chunk_seconds // timeframe_seconds) + 1

            chunks.append(TimeChunk(
                start_time=current_start,
                end_time=chunk_end,
                expected_count=chunk_count,
                chunk_index=chunk_index
            ))

            # 다음 청크 시작점 계산
            current_start = chunk_end + timedelta(seconds=timeframe_seconds)
            chunk_index += 1

        logger.debug(f"청크 분할 완료: 총 {len(chunks)}개 청크, 총 {total_count}개 캔들")
        return chunks

    @staticmethod
    def adjust_start_from_connection(
        connected_end: datetime,
        timeframe: str,
        count: int = 200
    ) -> datetime:
        """
        overlap_analyzer가 찾은 connected_end 기준으로 새로운 API 요청 시작점 계산

        Args:
            connected_end: 연속된 데이터의 마지막 시점 (overlap_analyzer 결과)
            timeframe: 타임프레임
            count: 요청할 캔들 개수 (기본 200개)

        Returns:
            datetime: 겹침 없는 새로운 시작점 (connected_end 다음 캔들부터)
        """
        timeframe_seconds = TimeUtils.get_timeframe_seconds(timeframe)

        # connected_end 다음 캔들부터 시작
        new_start = connected_end + timedelta(seconds=timeframe_seconds)

        # 캔들 경계에 정렬
        aligned_start = TimeUtils._align_to_candle_boundary(new_start, timeframe)

        logger.debug(f"겹침 최적화: connected_end={connected_end} → new_start={aligned_start}")
        return aligned_start

    @staticmethod
    def get_timeframe_seconds(timeframe: str) -> int:
        """
        타임프레임을 초 단위로 변환 (overlap_analyzer 연동용)

        1초봉 지원을 포함한 모든 업비트 공식 타임프레임 지원

        Args:
            timeframe: 타임프레임 ('1s', '1m', '5m', '15m', '1h', etc.)

        Returns:
            int: 초 단위 간격

        Examples:
            '1s' → 1
            '1m' → 60
            '5m' → 300
            '1h' → 3600

        Raises:
            ValueError: 지원하지 않는 타임프레임인 경우
        """
        timeframe_seconds = TimeUtils._parse_timeframe_to_seconds(timeframe)
        if timeframe_seconds is None:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

        return timeframe_seconds

    # === 검증된 기존 로직 (smart_data_provider_V4/time_utils.py 기반) ===

    @staticmethod
    def _parse_timeframe_to_seconds(timeframe: str) -> Optional[int]:
        """
        타임프레임 문자열을 초 단위로 변환 (1초봉 지원)

        업비트 공식 지원 타임프레임 매핑:
        - 초(Second): 1s
        - 분(Minute): 1m, 3m, 5m, 10m, 15m, 30m, 60m, 240m
        - 시간(Hour): 1h, 4h (60m/240m과 동일)
        - 일(Day): 1d
        - 주(Week): 1w
        - 월(Month): 1M
        - 연(Year): 1y        Args:
            timeframe: 타임프레임 문자열 ('1s', '1m', '5m', '1h', etc.)

        Returns:
            Optional[int]: 초 단위 간격, 지원하지 않는 경우 None
        """
        # 업비트 공식 지원 타임프레임 → 초 단위 매핑
        TIMEFRAME_SECONDS_MAP = {
            # 초(Second) 캔들 - 공식 지원: 1초만
            '1s': 1,

            # 분(Minute) 캔들 - 공식 지원: 1, 3, 5, 10, 15, 30, 60, 240분
            '1m': 60,
            '3m': 180,
            '5m': 300,
            '10m': 600,
            '15m': 900,
            '30m': 1800,
            '60m': 3600,
            '240m': 14400,

            # 시간(Hour) 캔들 - 60분/240분과 동일 (호환성)
            '1h': 3600,      # 60분과 동일
            '4h': 14400,     # 240분과 동일

            # 일(Day) 캔들
            '1d': 86400,     # 24시간

            # 주(Week) 캔들
            '1w': 604800,    # 7일

            # 월(Month) 캔들 - 30일로 근사
            '1M': 2592000,   # 30일

            # 연(Year) 캔들 - 365일로 근사
            '1y': 31536000   # 365일
        }

        # 대소문자 구분 필요: 1m(분봉) vs 1M(월봉)
        timeframe_normalized = timeframe.strip()
        return TIMEFRAME_SECONDS_MAP.get(timeframe_normalized)

    @staticmethod
    def _parse_timeframe_to_minutes(timeframe: str) -> Optional[int]:
        """타임프레임 문자열을 분 단위로 변환 (기존 검증된 로직)"""
        timeframe = timeframe.lower().strip()

        if timeframe.endswith('m'):
            return int(timeframe[:-1])
        elif timeframe.endswith('h'):
            return int(timeframe[:-1]) * 60
        elif timeframe.endswith('d'):
            return int(timeframe[:-1]) * 60 * 24
        elif timeframe.endswith('w'):
            return int(timeframe[:-1]) * 60 * 24 * 7
        elif timeframe.endswith('M'):  # 월 단위는 30일로 근사
            return int(timeframe[:-1]) * 60 * 24 * 30
        else:
            # 숫자만 있는 경우 분으로 간주
            try:
                return int(timeframe)
            except ValueError:
                return None

    @staticmethod
    def _align_to_candle_boundary(dt: datetime, timeframe: str) -> datetime:
        """
        업비트 UTC 경계에 맞춰 시간 정렬 - 올림(CEILING) 방식

        ⚠️ 중요: 올림 정렬을 사용하는 이유
        - 업비트 API `to` 파라미터는 시작 시간을 배제(exclusive)
        - 내림 정렬 시: dt가 포함된 캔들이 아닌 이전 캔들을 반환
        - 올림 정렬 시: dt가 포함된 캔들을 정확히 반환

        예시:
        - 입력: 14:32:30 (30초)
        - 올림: 14:33:00 → API to=14:33:00 → 14:32:00 캔들 반환 ✅
        - 내림: 14:32:00 → API to=14:32:00 → 14:31:00 캔들 반환 ❌

        업비트 캔들 시간 패턴 (올림 정렬 후):
        - 1초: 02:41:36, 02:41:35, 02:41:34 (다음 초 경계)
        - 1분: 02:42:00, 02:41:00, 02:40:00 (다음 분 경계)
        - 3분: 02:42:00, 02:39:00, 02:36:00 (다음 3분 경계)
        - 5분: 02:35:00, 02:30:00, 02:25:00 (다음 5분 경계)
        - 15분: 02:45:00, 02:30:00, 02:15:00 (다음 15분 경계)
        - 1시간: 03:00:00, 02:00:00, 01:00:00 (다음 시간 경계)
        - 1일: 다음날 00:00:00 (다음 자정 경계)
        """
        timeframe_seconds = TimeUtils._parse_timeframe_to_seconds(timeframe)
        if timeframe_seconds is None:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

        # 효율적인 올림 정렬: 내림 정렬 + 나머지 존재 시 +1
        # 공식: ceiling(x/y) = floor(x/y) + (x % y != 0)
        # 참조: https://stackoverflow.com/a/14878734 (Miguel Figueiredo)
        floor_aligned = TimeUtils._floor_to_candle_boundary(dt, timeframe_seconds)

        # 정확한 경계가 아니면 다음 경계로 올림
        if dt != floor_aligned:
            return floor_aligned + timedelta(seconds=timeframe_seconds)
        else:
            return floor_aligned

    @staticmethod
    def _floor_to_candle_boundary(dt: datetime, timeframe_seconds: int) -> datetime:
        """
        내림 정렬 헬퍼 함수 (기존 로직)

        타임프레임 초 단위 기준으로 내림 정렬 수행
        """
        if timeframe_seconds < 60:
            # 1분 미만 (초봉): 초 단위로 정렬
            aligned_second = (dt.second // timeframe_seconds) * timeframe_seconds
            return dt.replace(second=aligned_second, microsecond=0)

        elif timeframe_seconds < 3600:  # 1시간 미만 (분봉)
            # 분 단위로 정렬
            timeframe_minutes = timeframe_seconds // 60
            aligned_minute = (dt.minute // timeframe_minutes) * timeframe_minutes
            return dt.replace(minute=aligned_minute, second=0, microsecond=0)

        elif timeframe_seconds < 86400:  # 24시간 미만 (시간봉)
            # 시간 단위로 정렬
            timeframe_hours = timeframe_seconds // 3600
            aligned_hour = (dt.hour // timeframe_hours) * timeframe_hours
            return dt.replace(hour=aligned_hour, minute=0, second=0, microsecond=0)

        else:
            # 일 단위 이상 (일봉, 주봉, 월봉, 연봉): 자정으로 정렬
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def _validate_time_params(
        count: Optional[int],
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> None:
        """시간 파라미터 유효성 검사 - 미래 시간 요청 엄격 검증"""
        if count is not None and count <= 0:
            raise ValidationError(f"count는 양수여야 합니다: {count}")

        if count is not None and count > 10000:
            raise ValidationError(f"count가 너무 큽니다 (최대 10000): {count}")

        # 🎯 미래 시간 요청 엄격 방지 (사용자 책임)
        current_time = datetime.now(timezone.utc)

        if start_time and start_time > current_time:
            raise ValidationError(
                f"start_time이 미래입니다: {start_time} > {current_time}\n"
                f"사용자가 시간을 확인하고 올바른 과거 시간을 제공해주세요."
            )

        if end_time and end_time > current_time:
            raise ValidationError(
                f"end_time이 미래입니다: {end_time} > {current_time}\n"
                f"사용자가 시간을 확인하고 올바른 과거 시간을 제공해주세요."
            )

        # start_time과 end_time 순서 검증
        if start_time and end_time and start_time >= end_time:
            raise ValidationError(
                f"start_time ({start_time})이 end_time ({end_time})보다 크거나 같습니다.\n"
                f"start_time < end_time 조건을 만족하도록 수정해주세요."
            )

    # === 기존 호환성 유지 메서드들 ===

    @staticmethod
    def generate_candle_times(start_time: datetime, end_time: datetime, timeframe: str) -> List[datetime]:
        """
        시작 시간부터 종료 시간까지 예상되는 캔들 시간 목록 생성
        (기존 smart_data_provider_V4 호환성 유지)
        """
        timeframe_minutes = TimeUtils._parse_timeframe_to_minutes(timeframe)
        if timeframe_minutes is None:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

        # 시작 시간을 캔들 시간 경계로 정렬
        aligned_start = TimeUtils._align_to_candle_boundary(start_time, timeframe)

        times = []
        current_time = aligned_start

        while current_time <= end_time:
            times.append(current_time)
            current_time += timedelta(minutes=timeframe_minutes)

        return times

    @staticmethod
    def get_before_candle_time(dt: datetime, timeframe: str) -> datetime:
        """
        이전 캔들 시간 계산 (업비트 순서상 before = 시간상 과거)

        ✅ 검증 완료: 업비트 시간 정렬 패턴 일치
        ✅ 1m/5m/15m/1h 타임프레임 지원

        업비트 데이터 순서: 미래 ← 10:02, 10:01, 10:00, 09:59 → 과거

        사용 목적: inclusive_start=True일 때 start_time을 시간상 과거로 조정
        - 사용자 요청: 10:00부터 포함
        - 조정: 10:00 → 09:59 (before)
        - API 결과: 09:59 배제 → 10:00부터 포함됨
        """
        timeframe_minutes = TimeUtils._parse_timeframe_to_minutes(timeframe)
        if timeframe_minutes is None:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

        aligned = TimeUtils._align_to_candle_boundary(dt, timeframe)
        return aligned - timedelta(minutes=timeframe_minutes)

    @staticmethod
    def get_after_candle_time(dt: datetime, timeframe: str) -> datetime:
        """
        다음 캔들 시간 계산 (업비트 순서상 after = 시간상 미래)

        ✅ 검증 완료: 업비트 시간 정렬 패턴 일치
        ✅ 1m/5m/15m/1h 타임프레임 지원

        업비트 데이터 순서: 미래 ← 10:02, 10:01, 10:00, 09:59 → 과거

        사용 목적: 시간 범위 계산, 청크 분할 등에서 활용
        """
        timeframe_minutes = TimeUtils._parse_timeframe_to_minutes(timeframe)
        if timeframe_minutes is None:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

        aligned = TimeUtils._align_to_candle_boundary(dt, timeframe)
        return aligned + timedelta(minutes=timeframe_minutes)
