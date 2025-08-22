"""
업비트 스마트 라우팅 시스템 V2.0

WebSocket과 REST API의 형식 차이와 지원 범위 차이를 해결하여,
사용자가 데이터 요청 시 최적의 통신 채널을 자동으로 선택하는 시스템입니다.

주요 특징:
- 형식 통일: REST API 기준으로 모든 응답 형식 통일
- 고정 라우팅: 특정 요청은 최적 채널로 고정
- 스마트 선택: 상황별 점수 기반 자동 채널 선택
- 패턴 학습: 사용자 요청 패턴 분석 및 예측
"""

from .smart_router import SmartRouter, get_smart_router, initialize_smart_router
from .data_format_unifier import DataFormatUnifier
from .channel_selector import ChannelSelector
from .models import (
    DataRequest,
    ChannelDecision,
    FrequencyAnalysis,
    RoutingMetrics,
    DataType,
    ChannelType,
    RealtimePriority
)

__all__ = [
    "SmartRouter",
    "get_smart_router",
    "initialize_smart_router",
    "DataFormatUnifier",
    "ChannelSelector",
    "DataRequest",
    "ChannelDecision",
    "FrequencyAnalysis",
    "RoutingMetrics",
    "DataType",
    "ChannelType",
    "RealtimePriority"
]

__version__ = "2.0.0"
