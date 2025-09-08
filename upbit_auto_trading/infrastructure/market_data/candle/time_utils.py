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
            calculated_start = aligned_end - timedelta(seconds=timeframe_seconds * (count - 1))
            logger.debug(f"count만 제공 → 현재시간 역순: {calculated_start} ~ {aligned_end} ({count}개)")
            return calculated_start, aligned_end, count

        # 3. start_time + count → end_time 계산 (과거 방향)
        elif start_time is not None and count is not None and end_time is None:
            aligned_start = TimeUtils._align_to_candle_boundary(start_time, timeframe)
            # 업비트 API는 start_time부터 과거로 수집하므로 end_time은 더 과거여야 함
            calculated_end = aligned_start - timedelta(seconds=timeframe_seconds * (count - 1))
            # 업비트 방향 (latest → past): start_time이 latest, calculated_end가 past
            logger.debug(f"start_time + count → end_time 계산 (과거 방향): {aligned_start} → {calculated_end} ({count}개)")
            return calculated_end, aligned_start, count

        # 4. start_time + end_time → count 계산
        elif start_time is not None and end_time is not None and count is None:
            aligned_start = TimeUtils._align_to_candle_boundary(start_time, timeframe)
            aligned_end = TimeUtils._align_to_candle_boundary(end_time, timeframe)

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

        Args:
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)

        Returns:
            int: 초 단위 간격

        Examples:
            '1m' → 60
            '5m' → 300
            '1h' → 3600
        """
        timeframe_minutes = TimeUtils._parse_timeframe_to_minutes(timeframe)
        if timeframe_minutes is None:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

        return timeframe_minutes * 60

    # === 검증된 기존 로직 (smart_data_provider_V4/time_utils.py 기반) ===

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
        업비트 UTC 경계에 맞춰 시간 정렬 (검증된 로직)

        업비트 실제 패턴:
        - 1분: 02:41:00, 02:40:00, 02:39:00 (분 단위 경계)
        - 3분: 02:39:00, 02:36:00, 02:33:00 (3분 간격, 정시 기준)
        - 5분: 02:40:00, 02:35:00, 02:30:00 (5분 간격, 정시 기준)
        - 15분: 02:30:00, 02:15:00, 02:00:00 (15분 간격)
        """
        timeframe_minutes = TimeUtils._parse_timeframe_to_minutes(timeframe)
        if timeframe_minutes is None:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")

        if timeframe_minutes < 60:
            # 1시간 미만: 분 단위로 정렬
            aligned_minute = (dt.minute // timeframe_minutes) * timeframe_minutes
            return dt.replace(minute=aligned_minute, second=0, microsecond=0)

        elif timeframe_minutes < 1440:  # 24시간 미만
            # 시간 단위로 정렬
            hours = timeframe_minutes // 60
            aligned_hour = (dt.hour // hours) * hours
            return dt.replace(hour=aligned_hour, minute=0, second=0, microsecond=0)

        else:
            # 일 단위 이상: 자정으로 정렬
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
