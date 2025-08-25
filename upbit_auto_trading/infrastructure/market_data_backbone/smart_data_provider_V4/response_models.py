"""
응답 모델 정의 - V4.0 통합 버전
SmartDataProvider V4.0의 완전한 응답 구조와 우선순위 시스템
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum


@dataclass
class DataResponse:
    """
    데이터 응답 - V4.0 통합 구조

    모든 기능을 지원하는 완전한 응답 모델
    """
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @classmethod
    def create_success(cls, data: Dict[str, Any], **metadata) -> 'DataResponse':
        """성공 응답 생성"""
        return cls(
            success=True,
            data=data,
            metadata=metadata
        )

    @classmethod
    def create_error(cls, error: str, **metadata) -> 'DataResponse':
        """실패 응답 생성"""
        return cls(
            success=False,
            error=error,
            metadata=metadata
        )

    def get(self, key: Optional[str] = None) -> Any:
        """키별 데이터 반환 또는 전체 Dict 반환"""
        if key:
            return self.data.get(key, {})
        return self.data

    def get_single(self, symbol: str) -> Dict[str, Any]:
        """단일 심볼 데이터 반환"""
        return self.data.get(symbol, {})

    def get_all(self) -> Dict[str, Any]:
        """전체 Dict 데이터 반환"""
        return self.data


class Priority(Enum):
    """
    통합 우선순위 시스템

    SmartRouter와 완전 호환되는 우선순위 정책
    """
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

    @property
    def smart_router_priority(self) -> str:
        """SmartRouter 호환 우선순위 문자열"""
        mapping = {
            Priority.CRITICAL: "high",
            Priority.HIGH: "high",
            Priority.NORMAL: "normal",
            Priority.LOW: "low"
        }
        return mapping[self]

    def __str__(self) -> str:
        return self.description

    def __repr__(self) -> str:
        return f"Priority.{self.name}"
