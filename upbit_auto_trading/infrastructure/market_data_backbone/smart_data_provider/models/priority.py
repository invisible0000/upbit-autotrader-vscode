"""
우선순위 열거형

Smart Data Provider에서 사용하는 요청 우선순위를 정의합니다.
"""

from enum import Enum


class Priority(Enum):
    """요청 우선순위"""
    CRITICAL = 1    # 실거래봇 (< 50ms)
    HIGH = 2        # 실시간 모니터링 (< 100ms)
    NORMAL = 3      # 차트뷰어 (< 500ms)
    LOW = 4         # 백테스터 (백그라운드)

    @property
    def max_response_time_ms(self) -> float:
        """우선순위별 최대 응답 시간 (밀리초)"""
        response_times = {
            Priority.CRITICAL: 50.0,
            Priority.HIGH: 100.0,
            Priority.NORMAL: 500.0,
            Priority.LOW: 5000.0  # 5초
        }
        return response_times[self]

    @property
    def description(self) -> str:
        """우선순위 설명"""
        descriptions = {
            Priority.CRITICAL: "실거래봇 (최우선)",
            Priority.HIGH: "실시간 모니터링",
            Priority.NORMAL: "차트뷰어",
            Priority.LOW: "백테스터 (백그라운드)"
        }
        return descriptions[self]

    def __str__(self) -> str:
        return self.description

    def __repr__(self) -> str:
        return f"Priority.{self.name}"
