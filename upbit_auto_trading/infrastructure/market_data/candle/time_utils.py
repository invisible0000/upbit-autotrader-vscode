"""
TimeUtils - 캔들 데이터 시간 처리 유틸리티
업비트 전용, timedelta 기반 단순 구현 - 필요시 기능 추가
"""

from datetime import datetime, timedelta
from typing import Dict


class TimeUtils:
    """캔들 데이터 시간 처리 - timedelta 기반 단순 구현"""

    # 업비트 지원 타임프레임 (필요시 추가)
    _TIMEFRAME_MAP: Dict[str, timedelta] = {
        # 초/분봉
        "1s": timedelta(seconds=1),
        "1m": timedelta(minutes=1),
        "3m": timedelta(minutes=3),
        "5m": timedelta(minutes=5),
        "15m": timedelta(minutes=15),
        "30m": timedelta(minutes=30),

        # 시간봉 (분 기준으로 통일)
        "60m": timedelta(minutes=60),    # = 1h
        "1h": timedelta(minutes=60),     # 60m과 동일
        "240m": timedelta(minutes=240),  # = 4h
        "4h": timedelta(minutes=240),    # 240m과 동일

        # 일/주/월/년봉
        "1d": timedelta(days=1),
        "1w": timedelta(weeks=1),
        "1M": timedelta(days=30),   # 근사값, 필요시 정확한 월 계산 추가
        "1y": timedelta(days=365),  # 근사값, 윤년 고려 안함
    }

    # 성능 최적화: 초 단위 직접 매핑 (자주 사용되는 메서드용)
    _TIMEFRAME_SECONDS: Dict[str, int] = {
        # 초/분봉
        "1s": 1,
        "1m": 60,
        "3m": 180,
        "5m": 300,
        "15m": 900,
        "30m": 1800,

        # 시간봉
        "60m": 3600,
        "1h": 3600,
        "240m": 14400,
        "4h": 14400,

        # 일/주/월/년봉
        "1d": 86400,
        "1w": 604800,
        "1M": 2592000,   # 30 * 24 * 60 * 60
        "1y": 31536000,  # 365 * 24 * 60 * 60
    }

    @staticmethod
    def get_timeframe_delta(timeframe: str) -> timedelta:
        """타임프레임을 timedelta로 변환"""
        if timeframe not in TimeUtils._TIMEFRAME_MAP:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")
        return TimeUtils._TIMEFRAME_MAP[timeframe]

    @staticmethod
    def get_aligned_time_by_ticks(base_time: datetime, timeframe: str, tick_count: int) -> datetime:
        """
        틱 기반으로 정렬된 업비트 시간을 빠르게 계산

        base_time을 기준으로 timeframe 간격의 tick_count만큼 이동한 정렬된 시간을 반환.
        음수 tick_count는 과거 방향, 양수는 미래 방향으로 이동.

        Args:
            base_time: 기준 시간 (정렬되지 않아도 됨)
            timeframe: 타임프레임 ('1m', '5m', '1h', '1d', '1w', etc.)
            tick_count: 틱 개수 (음수=과거, 0=현재 정렬, 양수=미래)

        Returns:
            datetime: 정렬된 업비트 시간

        Examples:
            # 현재 시간을 5분봉으로 정렬
            get_aligned_time_by_ticks(now, '5m', 0)

            # 현재 시간에서 3개 5분봉 과거
            get_aligned_time_by_ticks(now, '5m', -3)  # 15분 전 정렬 시간

            # 일봉 기준 5일 후
            get_aligned_time_by_ticks(now, '1d', 5)   # 5일 후 자정

            # 주봉 기준 2주 전
            get_aligned_time_by_ticks(now, '1w', -2)  # 2주 전 일요일
        """
        # 1. 기준 시간을 해당 타임프레임으로 정렬
        aligned_base = TimeUtils._align_to_candle_boundary(base_time, timeframe)

        # 2. tick_count가 0이면 정렬된 기준 시간 반환
        if tick_count == 0:
            return aligned_base

        # 3. timeframe에 따른 틱 간격 계산
        if timeframe in ['1w', '1M', '1y']:
            # 주/월/년봉은 특별 처리 (정확한 날짜 산술)
            if timeframe == '1w':
                # 주봉: 7일 단위 (timedelta 사용 가능)
                tick_delta = timedelta(weeks=abs(tick_count))
                if tick_count > 0:
                    result_time = aligned_base + tick_delta
                else:
                    result_time = aligned_base - tick_delta
                return TimeUtils._align_to_candle_boundary(result_time, timeframe)

            elif timeframe == '1M':
                # 월봉: 정확한 월 단위 계산
                year = aligned_base.year
                month = aligned_base.month + tick_count

                # 월 오버플로우/언더플로우 처리
                while month > 12:
                    year += 1
                    month -= 12
                while month < 1:
                    year -= 1
                    month += 12

                # 월 첫날로 설정
                return datetime(year, month, 1, 0, 0, 0)

            elif timeframe == '1y':
                # 년봉: 정확한 년 단위 계산
                year = aligned_base.year + tick_count
                return datetime(year, 1, 1, 0, 0, 0)
        else:
            # 초/분/시간/일봉: 고정 길이, 빠른 계산
            timeframe_seconds = TimeUtils.get_timeframe_seconds(timeframe)
            total_seconds_offset = timeframe_seconds * tick_count

            return aligned_base + timedelta(seconds=total_seconds_offset)

    @staticmethod
    def generate_time_sequence(start_time: datetime, timeframe: str, count: int) -> list[datetime]:
        """
        정렬된 시간 시퀀스를 빠르게 생성

        Args:
            start_time: 시작 시간 (자동으로 정렬됨)
            timeframe: 타임프레임
            count: 생성할 시간 개수

        Returns:
            list[datetime]: 정렬된 시간 시퀀스

        Examples:
            # 현재부터 10개 5분봉 시간 시퀀스
            generate_time_sequence(now, '5m', 10)
            # → [14:30:00, 14:35:00, 14:40:00, ...]
        """
        if count <= 0:
            return []

        # 시작 시간 정렬
        aligned_start = TimeUtils._align_to_candle_boundary(start_time, timeframe)

        # 시퀀스 생성
        sequence = []
        for i in range(count):
            sequence.append(TimeUtils.get_aligned_time_by_ticks(aligned_start, timeframe, i))

        return sequence

    @staticmethod
    def get_time_range(start_time: datetime, end_time: datetime, timeframe: str) -> list[datetime]:
        """
        시간 범위 내의 모든 정렬된 시간점들을 반환

        Args:
            start_time: 시작 시간
            end_time: 종료 시간
            timeframe: 타임프레임

        Returns:
            list[datetime]: 범위 내 모든 정렬된 시간점들
        """
        if start_time >= end_time:
            return []

        # 시작점 정렬
        aligned_start = TimeUtils._align_to_candle_boundary(start_time, timeframe)

        # 예상 개수 계산
        expected_count = TimeUtils.calculate_expected_count(aligned_start, end_time, timeframe)

        # 시퀀스 생성 후 범위 내 필터링
        sequence = TimeUtils.generate_time_sequence(aligned_start, timeframe, expected_count + 1)

        # end_time 이전까지만 반환
        return [t for t in sequence if t < end_time]

    @staticmethod
    def get_timeframe_seconds(timeframe: str) -> int:
        """
        타임프레임을 초 단위로 변환 (CandleDataProvider 연동용)

        매우 자주 호출되는 메서드이므로 직접 매핑으로 최적화

        Args:
            timeframe: 타임프레임 ('1s', '1m', '5m', '15m', '1h', etc.)

        Returns:
            int: 초 단위 간격

        Examples:
            '1s' → 1
            '1m' → 60
            '5m' → 300
            '1h' → 3600
            '1d' → 86400

        Raises:
            ValueError: 지원하지 않는 타임프레임인 경우
        """
        if timeframe not in TimeUtils._TIMEFRAME_SECONDS:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")
        return TimeUtils._TIMEFRAME_SECONDS[timeframe]

    @staticmethod
    def _align_to_candle_boundary(dt: datetime, timeframe: str) -> datetime:
        """
        업비트 캔들 경계에 맞춰 시간 내림 정렬 (FLOOR)

        타임프레임별 정확한 경계로 내림 정렬:
        - 1분: 14:32:30 → 14:32:00
        - 5분: 14:32:30 → 14:30:00 (5분 경계)
        - 15분: 14:32:30 → 14:30:00 (15분 경계)
        - 1시간: 14:32:30 → 14:00:00
        - 1일: 14:32:30 → 00:00:00 (자정)

        Args:
            dt: 정렬할 시간
            timeframe: 타임프레임

        Returns:
            datetime: 내림 정렬된 시간

        Note:
            올림 정렬이 필요한 경우: floor_result + get_timeframe_delta(timeframe)
        """
        timeframe_seconds = TimeUtils.get_timeframe_seconds(timeframe)

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
            # 일 단위 이상: 특별 처리
            if timeframe == "1d":
                # 일봉: 자정으로 정렬
                return dt.replace(hour=0, minute=0, second=0, microsecond=0)
            elif timeframe == "1w":
                # 주봉: 해당 주의 일요일로 정렬 (업비트 기준)
                # 인터넷 표준 방식: (weekday + 1) % 7로 일요일 기준 계산
                days_since_sunday = (dt.weekday() + 1) % 7
                sunday = dt - timedelta(days=days_since_sunday)
                return sunday.replace(hour=0, minute=0, second=0, microsecond=0)
            elif timeframe == "1M":
                # 월봉: 해당 월의 1일로 정렬
                return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            elif timeframe == "1y":
                # 년봉: 해당 년의 1월 1일로 정렬
                return dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                # 기타 (일 단위 이상): 자정으로 정렬
                return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def calculate_expected_count(start_time: datetime, end_time: datetime, timeframe: str) -> int:
        """
        시간 범위에서 예상 캔들 개수 계산

        최종 최적화 버전:
        - 월/년봉: datetime 직접 계산으로 정확성 보장
        - 분/시/일/주봉: timedelta 계산으로 고성능 유지

        Args:
            start_time: 시작 시간 (자동으로 정렬됨)
            end_time: 종료 시간
            timeframe: 타임프레임

        Returns:
            int: 예상 캔들 개수
        """
        if start_time >= end_time:
            return 0

        # 시작 시간을 타임프레임에 맞게 정렬 (핵심 개선)
        aligned_start = TimeUtils._align_to_candle_boundary(start_time, timeframe)

        # 월/년봉은 실제 캔들 범위 계산 (정확성 우선)
        if timeframe == '1M':
            if aligned_start >= end_time:
                return 0
            # 실제 포함되는 월 수를 계산
            count = 0
            current = datetime(aligned_start.year, aligned_start.month, 1)
            while current < end_time:
                count += 1
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
            return count
        elif timeframe == '1y':
            if aligned_start >= end_time:
                return 0
            # 실제 포함되는 년 수를 계산
            count = 0
            current = datetime(aligned_start.year, 1, 1)
            while current < end_time:
                count += 1
                current = current.replace(year=current.year + 1)
            return count

        # 분/시/일/주봉은 timedelta 계산 (성능 우선)
        dt = TimeUtils.get_timeframe_delta(timeframe)
        time_diff = end_time - aligned_start
        count = int(time_diff.total_seconds() / dt.total_seconds())
        return max(0, count)


# 편의 함수들 (자주 사용할 패턴들)
def get_dt(timeframe: str) -> timedelta:
    """TimeUtils.get_timeframe_delta의 간단한 별칭"""
    return TimeUtils.get_timeframe_delta(timeframe)


def align_time(timestamp: datetime, timeframe: str) -> datetime:
    """TimeUtils._align_to_candle_boundary의 간단한 별칭"""
    return TimeUtils._align_to_candle_boundary(timestamp, timeframe)


def count_candles(start_time: datetime, end_time: datetime, timeframe: str) -> int:
    """TimeUtils.calculate_expected_count의 간단한 별칭"""
    return TimeUtils.calculate_expected_count(start_time, end_time, timeframe)
