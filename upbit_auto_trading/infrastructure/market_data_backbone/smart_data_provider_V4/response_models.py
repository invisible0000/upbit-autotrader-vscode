"""
응답 모델 정의 - V4.0 통합 버전
SmartDataProvider V4.0의 완전한 응답 구조와 우선순위 시스템
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union, Literal
from datetime import datetime
from enum import Enum


@dataclass
class DataSourceInfo:
    """
    데이터 소스 상세 정보 - 실시간성 보장을 위한 소스 추적

    실시간 거래에서 데이터의 출처와 신뢰도를 명확히 식별하기 위한 메타데이터
    """
    channel: Literal["websocket", "rest_api", "cache"]
    stream_type: Optional[Literal["snapshot", "realtime"]] = None  # WebSocket 전용
    cache_info: Optional[Dict[str, Any]] = None  # TTL, freshness, hit_rate 등
    reliability: float = 1.0  # 신뢰도 (0.0-1.0)
    latency_ms: Optional[float] = None  # 응답 지연시간
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """데이터 검증"""
        if self.channel == "websocket" and self.stream_type is None:
            raise ValueError("WebSocket 채널은 stream_type이 필수입니다")

        if not 0.0 <= self.reliability <= 1.0:
            raise ValueError("reliability는 0.0-1.0 범위여야 합니다")

    @property
    def is_realtime(self) -> bool:
        """실시간 데이터 여부"""
        return self.channel == "websocket" and self.stream_type == "realtime"

    @property
    def is_cached(self) -> bool:
        """캐시된 데이터 여부"""
        return self.channel == "cache"

    @property
    def freshness_score(self) -> float:
        """데이터 신선도 점수 (0.0-1.0)"""
        if self.is_realtime:
            return 1.0
        elif self.is_cached and self.cache_info:
            # TTL 기반 신선도 계산
            ttl_ms = self.cache_info.get("ttl_ms", 200)
            age_ms = self.cache_info.get("age_ms", 0)
            return max(0.0, 1.0 - (age_ms / ttl_ms))
        else:
            return 0.8  # REST API 기본값

    def get_source_summary(self) -> str:
        """데이터 소스 요약 문자열"""
        parts = [self.channel]

        if self.stream_type:
            parts.append(f"({self.stream_type})")

        if self.latency_ms is not None:
            parts.append(f"{self.latency_ms:.1f}ms")

        if self.is_cached and self.cache_info:
            age_ms = self.cache_info.get("age_ms", 0)
            parts.append(f"age={age_ms:.0f}ms")

        return " ".join(parts)


@dataclass
class DataResponse:
    """
    데이터 응답 - V4.0 통합 구조 + 데이터 소스 추적

    모든 기능을 지원하는 완전한 응답 모델
    실시간성 보장을 위한 데이터 소스 정보 포함
    """
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    data_source: Optional[DataSourceInfo] = None  # 🚀 데이터 소스 정보 추가

    @classmethod
    def create_success(cls, data: Dict[str, Any], data_source: Optional[DataSourceInfo] = None, **metadata) -> 'DataResponse':
        """성공 응답 생성 - 데이터 소스 정보 포함"""
        return cls(
            success=True,
            data=data,
            metadata=metadata,
            data_source=data_source
        )

    @classmethod
    def create_error(cls, error: str, data_source: Optional[DataSourceInfo] = None, **metadata) -> 'DataResponse':
        """실패 응답 생성 - 데이터 소스 정보 포함"""
        return cls(
            success=False,
            error=error,
            metadata=metadata,
            data_source=data_source
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

    # 🚀 데이터 소스 관련 편의 메서드들
    @property
    def source_channel(self) -> Optional[str]:
        """데이터 소스 채널 (websocket/rest_api/cache)"""
        return self.data_source.channel if self.data_source else None

    @property
    def is_realtime(self) -> bool:
        """실시간 데이터 여부"""
        return self.data_source.is_realtime if self.data_source else False

    @property
    def is_cached(self) -> bool:
        """캐시된 데이터 여부"""
        return self.data_source.is_cached if self.data_source else False

    @property
    def freshness_score(self) -> float:
        """데이터 신선도 점수 (0.0-1.0)"""
        return self.data_source.freshness_score if self.data_source else 0.0

    @property
    def reliability(self) -> float:
        """데이터 신뢰도 (0.0-1.0)"""
        return self.data_source.reliability if self.data_source else 0.0

    def get_source_summary(self) -> Dict[str, Any]:
        """데이터 소스 요약 정보"""
        if not self.data_source:
            return {"source": "unknown", "realtime": False, "cached": False}

        return {
            "channel": self.data_source.channel,
            "stream_type": self.data_source.stream_type,
            "realtime": self.data_source.is_realtime,
            "cached": self.data_source.is_cached,
            "freshness": self.data_source.freshness_score,
            "reliability": self.data_source.reliability,
            "latency_ms": self.data_source.latency_ms
        }


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
