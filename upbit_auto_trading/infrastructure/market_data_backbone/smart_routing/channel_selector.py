"""
채널 선택기 (Channel Selector)

요청 상황에 따라 최적의 통신 채널(WebSocket 또는 REST API)을 선택합니다.
고정 규칙과 스마트 선택 알고리즘을 결합하여 최적화된 라우팅을 제공합니다.
"""

import time
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .models import (
    DataRequest, ChannelDecision, FrequencyAnalysis, ChannelType, DataType,
    RealtimePriority, FrequencyCategory, ALL_ENDPOINT_CONFIGS
)

logger = create_component_logger("ChannelSelector")


class RequestPatternAnalyzer:
    """요청 패턴 분석 및 예측"""

    def __init__(self, window_size: int = 20):
        """패턴 분석기 초기화

        Args:
            window_size: 분석에 사용할 요청 히스토리 윈도우 크기
        """
        self.window_size = window_size
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        logger.info(f"RequestPatternAnalyzer 초기화 - window_size: {window_size}")

    def record_request(self, symbol: str, data_type: DataType) -> None:
        """요청 기록"""
        key = f"{symbol}:{data_type.value}"
        self.request_history[key].append(time.time())

    def analyze_frequency(self, symbol: str, data_type: DataType) -> FrequencyAnalysis:
        """요청 빈도 분석"""
        key = f"{symbol}:{data_type.value}"
        history = self.request_history[key]

        if len(history) < 3:
            return FrequencyAnalysis(
                category=FrequencyCategory.UNKNOWN,
                avg_interval=0.0,
                trend="stable",
                confidence=0.0,
                sample_size=len(history)
            )

        # 요청 간격 계산
        intervals = [
            history[i] - history[i-1]
            for i in range(1, len(history))
        ]

        avg_interval = sum(intervals) / len(intervals)

        # 추세 분석 (최근 3개 vs 이전 3개)
        if len(intervals) >= 6:
            recent_avg = sum(intervals[-3:]) / 3
            older_avg = sum(intervals[-6:-3]) / 3

            if recent_avg < older_avg * 0.7:
                trend = "accelerating"
            elif recent_avg > older_avg * 1.3:
                trend = "decelerating"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # 빈도 카테고리 결정
        if avg_interval < 2.0:
            category = FrequencyCategory.HIGH_FREQUENCY
        elif avg_interval < 10.0:
            category = FrequencyCategory.MEDIUM_FREQUENCY
        else:
            category = FrequencyCategory.LOW_FREQUENCY

        # 신뢰도 계산 (샘플 수에 따라)
        confidence = min(len(history) / self.window_size, 1.0)

        return FrequencyAnalysis(
            category=category,
            avg_interval=avg_interval,
            trend=trend,
            confidence=confidence,
            sample_size=len(history)
        )


class ChannelSelector:
    """최적 통신 채널 선택"""

    def __init__(self):
        """채널 선택기 초기화"""
        logger.info("ChannelSelector 초기화")

        self.pattern_analyzer = RequestPatternAnalyzer()
        self.performance_metrics: Dict[str, Any] = {}
        self.websocket_status = {"connected": False, "uptime": 0.0}
        self.rate_limits = {
            "websocket": {"current": 0, "limit": 5, "window": 1.0},
            "rest": {"current": 0, "limit": 10, "window": 1.0}
        }

        logger.info("ChannelSelector 초기화 완료")

    def select_channel(self, request: DataRequest) -> ChannelDecision:
        """요청에 대한 최적 채널 결정

        Args:
            request: 데이터 요청 정보

        Returns:
            채널 선택 결정
        """
        # 요청 기록
        for symbol in request.symbols:
            self.pattern_analyzer.record_request(symbol, request.data_type)

        # 1단계: WebSocket 제약 검증 (데이터 무결성 보장)
        if request.data_type == DataType.CANDLES:
            # 필수 매개변수 검증
            if not request.interval:
                raise ValueError("캔들 요청 시 타임프레임(interval)은 필수입니다")
            if not request.symbols:
                raise ValueError("캔들 요청 시 심볼(symbols)은 필수입니다")

            # WebSocket 제약 검증 - 과거 데이터나 다중 캔들은 REST 필수
            if request.to is not None:
                return ChannelDecision(
                    channel=ChannelType.REST_API,
                    reason="past_data_requires_rest",
                    confidence=1.0
                )
            if request.count and request.count > 1:
                return ChannelDecision(
                    channel=ChannelType.REST_API,
                    reason="multiple_candles_requires_rest",
                    confidence=1.0
                )

        elif request.data_type == DataType.TRADES:
            # 체결 요청 WebSocket 제약 검증
            if not request.symbols:
                raise ValueError("체결 요청 시 심볼(symbols)은 필수입니다")

            # WebSocket 제약 검증 - 과거 데이터나 다중 체결은 REST 필수
            if request.to is not None:
                return ChannelDecision(
                    channel=ChannelType.REST_API,
                    reason="past_trades_requires_rest",
                    confidence=1.0
                )
            if request.count and request.count > 1:
                return ChannelDecision(
                    channel=ChannelType.REST_API,
                    reason="multiple_trades_requires_rest",
                    confidence=1.0
                )

        # 2단계: 고정 채널 확인
        endpoint_config = ALL_ENDPOINT_CONFIGS.get(request.data_type)
        if endpoint_config and endpoint_config.fixed_channel:
            return ChannelDecision(
                channel=endpoint_config.fixed_channel,
                reason="fixed_rule",
                confidence=1.0,
                metadata={
                    "description": endpoint_config.description,
                    "supported_channels": [ch.value for ch in endpoint_config.supported_channels]
                }
            )

        # 2단계: 스마트 선택
        return self._smart_selection(request)

    def _smart_selection(self, request: DataRequest) -> ChannelDecision:
        """스마트 채널 선택 알고리즘"""
        scores = {
            ChannelType.WEBSOCKET: self._calculate_websocket_score(request),
            ChannelType.REST_API: self._calculate_rest_score(request)
        }

        # 최고 점수 채널 선택 (20% 마진 적용)
        ws_score = scores[ChannelType.WEBSOCKET]
        rest_score = scores[ChannelType.REST_API]

        if ws_score > rest_score * 1.2:  # WebSocket 20% 우대
            selected = ChannelType.WEBSOCKET
            reason = "smart_selection_websocket"
        else:
            selected = ChannelType.REST_API
            reason = "smart_selection_rest"

        confidence = scores[selected] / (ws_score + rest_score) if (ws_score + rest_score) > 0 else 0.5

        logger.debug(f"스마트 선택 결과 - 채널: {selected.value}, WS점수: {ws_score:.2f}, REST점수: {rest_score:.2f}")

        return ChannelDecision(
            channel=selected,
            reason=reason,
            confidence=confidence,
            scores={ch.value: score for ch, score in scores.items()},
            metadata={
                "analysis_details": self._get_analysis_details(request),
                "websocket_status": self.websocket_status.copy(),
                "rate_limit_status": self.rate_limits.copy()
            }
        )

    def _calculate_websocket_score(self, request: DataRequest) -> float:
        """WebSocket 채널 점수 계산"""
        score = 0.0

        # 1. 실시간성 요구 (가중치: 3x)
        realtime_scores = {
            RealtimePriority.HIGH: 10,
            RealtimePriority.MEDIUM: 6,
            RealtimePriority.LOW: 2
        }
        score += realtime_scores[request.realtime_priority] * 3

        # 2. 요청 빈도 분석 (가중치: 2x)
        if request.symbols:
            main_symbol = request.symbols[0]
            freq_analysis = self.pattern_analyzer.analyze_frequency(main_symbol, request.data_type)

            if freq_analysis.category == FrequencyCategory.HIGH_FREQUENCY:
                score += 8 * 2
            elif freq_analysis.category == FrequencyCategory.MEDIUM_FREQUENCY:
                score += 5 * 2
            else:
                score += 2 * 2

        # 3. 연결 상태 (가중치: 3x)
        if self.websocket_status["connected"]:
            score += 10 * 3
        else:
            score += 0  # 연결되지 않으면 점수 없음

        # 4. Rate Limit 상태 (가중치: 2x)
        ws_usage = self.rate_limits["websocket"]["current"] / self.rate_limits["websocket"]["limit"]
        if ws_usage < 0.8:
            score += 5 * 2
        elif ws_usage < 0.9:
            score += 3 * 2
        else:
            score += 1 * 2

        # 5. 데이터 양 (가중치: 1x)
        if request.count and request.count <= 10:
            score += 3  # 소량 데이터는 WebSocket 유리
        elif request.count and request.count <= 100:
            score += 2
        else:
            score += 1

        # 6. 다중 타임프레임 캔들 효율성 (가중치: 2x)
        if request.data_type == DataType.CANDLES:
            # 과거 데이터 조회 시 WebSocket 점수 대폭 감소
            if request.to is not None:
                score -= 20  # 과거 데이터는 WebSocket 부적합
            elif len(request.symbols) > 1:
                score += 8 * 2  # 다중 심볼 캔들은 WebSocket이 매우 효율적
            else:
                score += 4 * 2  # 단일 심볼 캔들도 실시간성이 있으면 WebSocket 유리

        return score

    def _calculate_rest_score(self, request: DataRequest) -> float:
        """REST API 채널 점수 계산"""
        score = 0.0

        # 1. 안정성 우선 (가중치: 2x)
        score += 10 * 2  # REST는 항상 안정적

        # 2. 대량 데이터 처리 (가중치: 1x)
        if request.count and request.count > 100:
            score += 8
        elif request.count and request.count > 10:
            score += 5
        else:
            score += 3

        # 3. 데이터 타입별 조정 (가중치: 2x)
        if request.data_type == DataType.CANDLES:
            # 과거 데이터 조회 감지 ('to' 매개변수 존재)
            if request.to is not None:
                score += 12 * 2  # 과거 데이터는 REST API가 필수적
            # 실시간 우선순위에 따라 점수 차등 적용
            elif request.realtime_priority == RealtimePriority.LOW:
                score += 8 * 2  # 과거 데이터 조회는 REST 유리
            elif request.realtime_priority == RealtimePriority.MEDIUM:
                score += 4 * 2  # 중간 우선순위는 WebSocket과 경쟁
            else:
                score += 2 * 2  # 실시간 우선순위는 WebSocket 우대

        # 4. Rate Limit 상태 (가중치: 2x)
        rest_usage = self.rate_limits["rest"]["current"] / self.rate_limits["rest"]["limit"]
        if rest_usage < 0.8:
            score += 8 * 2
        elif rest_usage < 0.9:
            score += 5 * 2
        else:
            score += 2 * 2

        # 5. 실시간성 낮음 (가중치: 1x)
        if request.realtime_priority == RealtimePriority.LOW:
            score += 5
        elif request.realtime_priority == RealtimePriority.MEDIUM:
            score += 3
        else:
            score += 1

        return score

    def _get_analysis_details(self, request: DataRequest) -> Dict[str, Any]:
        """분석 세부사항 생성"""
        details = {
            "request_info": {
                "data_type": request.data_type.value,
                "symbols_count": len(request.symbols),
                "realtime_priority": request.realtime_priority.value,
                "count": request.count
            }
        }

        # 주요 심볼의 빈도 분석 추가
        if request.symbols:
            main_symbol = request.symbols[0]
            freq_analysis = self.pattern_analyzer.analyze_frequency(main_symbol, request.data_type)
            details["frequency_analysis"] = {
                "category": freq_analysis.category.value,
                "avg_interval": freq_analysis.avg_interval,
                "trend": freq_analysis.trend,
                "confidence": freq_analysis.confidence,
                "sample_size": freq_analysis.sample_size
            }

        return details

    def update_websocket_status(self, connected: bool, uptime: float = 0.0) -> None:
        """WebSocket 연결 상태 업데이트"""
        self.websocket_status = {
            "connected": connected,
            "uptime": uptime,
            "last_updated": time.time()
        }
        logger.debug(f"WebSocket 상태 업데이트 - 연결: {connected}, 업타임: {uptime:.2f}")

    def update_rate_limit(self, channel: str, current_usage: int) -> None:
        """Rate Limit 사용량 업데이트"""
        if channel in self.rate_limits:
            self.rate_limits[channel]["current"] = current_usage
            self.rate_limits[channel]["last_updated"] = time.time()

    def get_performance_summary(self) -> Dict[str, Any]:
        """성능 요약 조회"""
        return {
            "websocket_status": self.websocket_status,
            "rate_limits": self.rate_limits,
            "pattern_analyzer": {
                "tracked_patterns": len(self.pattern_analyzer.request_history),
                "window_size": self.pattern_analyzer.window_size
            }
        }
