"""
실무용 시간 처리 유틸리티 함수들
비개발자도 쉽게 사용할 수 있는 명확한 인터페이스
"""

from datetime import datetime, timedelta
from typing import Tuple


class TimeCalculator:
    """시간 연산 전용 클래스 - 명확한 인터페이스"""

    @staticmethod
    def add_candles(start_time: str, count: int, timeframe_minutes: int) -> str:
        """
        시작 시간에 캔들 개수만큼 더한 시간 계산

        Args:
            start_time: "2025-09-08T00:00:00"
            count: 캔들 개수 (100)
            timeframe_minutes: 1분봉=1, 5분봉=5, 15분봉=15

        Returns:
            계산된 시간 문자열

        Example:
            >>> TimeCalculator.add_candles("2025-09-08T00:00:00", 100, 1)
            "2025-09-08T01:40:00"
        """
        dt = datetime.fromisoformat(start_time)
        result_dt = dt + timedelta(minutes=count * timeframe_minutes)
        return result_dt.strftime('%Y-%m-%dT%H:%M:%S')

    @staticmethod
    def subtract_candles(start_time: str, count: int, timeframe_minutes: int) -> str:
        """
        시작 시간에서 캔들 개수만큼 뺀 시간 계산

        Example:
            >>> TimeCalculator.subtract_candles("2025-09-08T02:00:00", 100, 1)
            "2025-09-08T00:20:00"
        """
        dt = datetime.fromisoformat(start_time)
        result_dt = dt - timedelta(minutes=count * timeframe_minutes)
        return result_dt.strftime('%Y-%m-%dT%H:%M:%S')

    @staticmethod
    def count_candles_between(start_time: str, end_time: str, timeframe_minutes: int) -> int:
        """
        두 시간 사이의 캔들 개수 계산

        Example:
            >>> TimeCalculator.count_candles_between(
            ...     "2025-09-08T00:00:00",
            ...     "2025-09-08T01:40:00",
            ...     1
            ... )
            100
        """
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)

        time_diff = end_dt - start_dt
        total_minutes = int(time_diff.total_seconds() / 60)

        return total_minutes // timeframe_minutes

    @staticmethod
    def get_time_range(center_time: str, count: int, timeframe_minutes: int) -> Tuple[str, str]:
        """
        중심 시간을 기준으로 앞뒤 시간 범위 계산

        Args:
            center_time: 중심 시간
            count: 전체 캔들 개수
            timeframe_minutes: 타임프레임

        Returns:
            (시작_시간, 종료_시간)

        Example:
            >>> TimeCalculator.get_time_range("2025-09-08T12:00:00", 100, 1)
            ("2025-09-08T11:10:00", "2025-09-08T12:50:00")
        """
        dt = datetime.fromisoformat(center_time)

        # 절반씩 앞뒤로
        half_duration = (count // 2) * timeframe_minutes

        start_dt = dt - timedelta(minutes=half_duration)
        end_dt = dt + timedelta(minutes=half_duration)

        start_time = start_dt.strftime('%Y-%m-%dT%H:%M:%S')
        end_time = end_dt.strftime('%Y-%m-%dT%H:%M:%S')

        return start_time, end_time


class UpbitTimeFormatter:
    """업비트 API 형식 변환 전용 클래스"""

    @staticmethod
    def to_upbit_format(db_time: str, format_type: str = "Z") -> str:
        """
        DB 형식을 업비트 API 형식으로 변환

        Args:
            db_time: "2025-09-08T00:00:00"
            format_type: "Z", "space", "utc" 중 선택

        Returns:
            업비트 API 호환 형식
        """
        if format_type == "Z":
            return db_time + "Z"
        elif format_type == "space":
            return db_time.replace("T", " ")
        elif format_type == "utc":
            return db_time + "+00:00"
        else:
            return db_time

    @staticmethod
    def from_upbit_format(upbit_time: str) -> str:
        """
        업비트 형식을 DB 형식으로 변환

        Args:
            upbit_time: "2025-09-08T00:00:00Z" 등

        Returns:
            DB 호환 형식 "2025-09-08T00:00:00"
        """
        if upbit_time.endswith('Z'):
            return upbit_time.replace('Z', '')
        elif '+' in upbit_time:
            return upbit_time.split('+')[0]
        elif ' ' in upbit_time:
            return upbit_time.replace(' ', 'T')
        else:
            return upbit_time


def demo_practical_usage():
    """실무 사용 예시 데모"""
    print("🎯 실무 사용 예시")
    print("=" * 50)

    # 1. 기본 시간 연산
    print("1️⃣ 기본 시간 연산:")
    current = "2025-09-08T00:00:00"
    future = TimeCalculator.add_candles(current, 100, 1)
    past = TimeCalculator.subtract_candles(current, 50, 5)

    print(f"   현재: {current}")
    print(f"   100분 후: {future}")
    print(f"   250분 전: {past}")

    # 2. 캔들 개수 계산
    print("\n2️⃣ 캔들 개수 계산:")
    count = TimeCalculator.count_candles_between(current, future, 1)
    print(f"   {current} ~ {future} = {count}개 1분봉")

    # 3. 시간 범위 계산
    print("\n3️⃣ 시간 범위 계산:")
    start, end = TimeCalculator.get_time_range(current, 100, 1)
    print(f"   중심: {current}")
    print(f"   범위: {start} ~ {end}")

    # 4. 업비트 형식 변환
    print("\n4️⃣ 업비트 형식 변환:")
    db_format = "2025-09-08T00:00:00"
    upbit_z = UpbitTimeFormatter.to_upbit_format(db_format, "Z")
    upbit_space = UpbitTimeFormatter.to_upbit_format(db_format, "space")

    print(f"   DB 형식: {db_format}")
    print(f"   업비트 Z: {upbit_z}")
    print(f"   업비트 공백: {upbit_space}")

    # 5. 데이터베이스 쿼리 준비
    print("\n5️⃣ 데이터베이스 쿼리 준비:")
    query_start = TimeCalculator.subtract_candles(current, 200, 1)
    query_end = current

    print(f"   쿼리 범위: {query_start} ~ {query_end}")
    print(f"   SQL: SELECT * FROM candles WHERE time BETWEEN '{query_start}' AND '{query_end}'")


if __name__ == "__main__":
    demo_practical_usage()
