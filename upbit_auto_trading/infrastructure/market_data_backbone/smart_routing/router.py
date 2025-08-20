"""
스마트 라우터 - 자동 채널 선택 및 필드 매핑

기능:
1. URL 패턴 매칭으로 자동 채널 선택 (REST/WebSocket)
2. 요청 빈도 기반 채널 최적화
3. 필드명 자동 매핑 (snake_case ↔ camelCase)
4. 레이트 제한 준수 및 백오프 처리
"""

import re
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs

from .pattern_analyzer import RequestPatternTracker
from .rate_limiter import RateLimitGuard
from upbit_auto_trading.infrastructure.logging import create_component_logger


class FieldMapper:
    """필드명 자동 매핑 (snake_case ↔ camelCase)"""

    # 업비트 API 필드 매핑 테이블
    # REST → WebSocket 필드 매핑
    REST_TO_WS = {
        "candle_date_time_utc": "timestamp",
        "candle_date_time_kst": "timestamp",
        "opening_price": "opening_price",
        "high_price": "high_price",
        "low_price": "low_price",
        "trade_price": "trade_price",
        "prev_closing_price": "prev_closing_price",
        "change_price": "signed_change_price",
        "change_rate": "signed_change_rate",
        "candle_acc_trade_price": "acc_trade_price_24h",
        "candle_acc_trade_volume": "acc_trade_volume_24h",
    }

    # WebSocket → REST 필드 매핑
    WS_TO_REST = {
        "timestamp": "candle_date_time_utc",
        "signed_change_price": "change_price",
        "signed_change_rate": "change_rate",
        "acc_trade_price_24h": "candle_acc_trade_price",
        "acc_trade_volume_24h": "candle_acc_trade_volume"
    }

    @classmethod
    def map_fields(cls, data: Dict[str, Any], from_rest: bool = True) -> Dict[str, Any]:
        """필드명 매핑 (REST ↔ WebSocket)"""
        if not isinstance(data, dict):
            return data

        mapped = {}
        mappings = cls.REST_TO_WS if from_rest else cls.WS_TO_REST

        for key, value in data.items():
            # 매핑 테이블에 있으면 변환, 없으면 원본 유지
            mapped_key = mappings.get(key, key)
            mapped[mapped_key] = value

        return mapped

    @classmethod
    def snake_to_camel(cls, snake_str: str) -> str:
        """snake_case → camelCase"""
        components = snake_str.split('_')
        return components[0] + ''.join(x.capitalize() for x in components[1:])

    @classmethod
    def camel_to_snake(cls, camel_str: str) -> str:
        """camelCase → snake_case"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class SmartChannelRouter:
    """스마트 채널 라우터"""

    # URL 패턴별 채널 분류
    CHANNEL_PATTERNS = {
        "websocket": [
            r"/ticker",
            r"/trade",
            r"/orderbook",
            r"/candles/minutes/1(\?|$)",  # 1분봉만 WebSocket (쿼리 있거나 끝)
        ],
        "rest": [
            r"/candles/minutes/[35]$",  # 3분, 5분봉
            r"/candles/minutes/1[05]$",  # 10분, 15분봉
            r"/candles/minutes/[346]0$",  # 30분, 60분봉
            r"/candles/days",
            r"/candles/weeks",
            r"/candles/months",
            r"/market/all",
            r"/accounts",
            r"/orders",
        ]
    }

    def __init__(self):
        self.pattern_tracker = RequestPatternTracker()
        self.rate_limiter = RateLimitGuard()
        self._logger = create_component_logger("SmartChannelRouter")

        # 패턴 컴파일
        self.compiled_patterns = {
            channel: [re.compile(pattern) for pattern in patterns]
            for channel, patterns in self.CHANNEL_PATTERNS.items()
        }

    def extract_symbol_from_url(self, url: str) -> Optional[str]:
        """URL에서 심볼 추출"""
        # 쿼리 파라미터에서 market 찾기
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)

        if 'market' in query_params:
            return query_params['market'][0]

        # URL 경로에서 심볼 찾기 (예: /ticker/KRW-BTC)
        path_match = re.search(r'([A-Z]{3}-[A-Z]{3,4})', parsed.path)
        if path_match:
            return path_match.group(1)

        return None

    def classify_url(self, url: str) -> str:
        """URL 분류 (websocket/rest)"""
        for channel, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(url):
                    return channel

        # 기본값: REST
        return "rest"

    def should_prefer_websocket(self, symbol: str, url: str) -> bool:
        """WebSocket 선호 여부 판단"""
        # 기본 분류가 WebSocket이 아니면 무조건 REST
        if self.classify_url(url) != "websocket":
            return False

        # 빈도 예측 기반 결정
        frequency = self.pattern_tracker.get_frequency_prediction(symbol)

        # 고빈도 → WebSocket, 저빈도 → REST
        return frequency == "high"

    def route_request(self, url: str) -> Tuple[str, Dict[str, Any]]:
        """
        요청 라우팅 결정

        Returns:
            (channel, routing_info)
        """
        symbol = self.extract_symbol_from_url(url)
        base_channel = self.classify_url(url)

        # 심볼이 있으면 패턴 기록
        if symbol:
            self.pattern_tracker.record_request(symbol, url)

        # 채널 결정 로직
        if base_channel == "websocket" and symbol:
            # WebSocket 가능하지만 빈도 체크
            if self.should_prefer_websocket(symbol, url):
                # 레이트 제한 확인
                if self.rate_limiter.can_make_request(is_websocket=True):
                    chosen_channel = "websocket"
                else:
                    chosen_channel = "rest"
                    self._logger.debug(f"WebSocket 레이트 제한으로 REST로 우회: {symbol}")
            else:
                chosen_channel = "rest"
        else:
            chosen_channel = "rest"

        # 최종 레이트 제한 확인
        is_websocket = chosen_channel == "websocket"
        if not self.rate_limiter.can_make_request(is_websocket):
            # 백오프 중이거나 제한 초과
            return "blocked", {
                "reason": "rate_limit",
                "retry_after": self.rate_limiter.backoff_until or 1.0,
                "rate_status": self.rate_limiter.get_status()
            }

        # 요청 기록
        self.rate_limiter.record_request(is_websocket)

        routing_info = {
            "channel": chosen_channel,
            "symbol": symbol,
            "base_classification": base_channel,
            "frequency_prediction": self.pattern_tracker.get_frequency_prediction(symbol) if symbol else "unknown",
            "rate_status": self.rate_limiter.get_status()
        }

        return chosen_channel, routing_info

    def handle_response_error(self, error_code: int) -> None:
        """응답 에러 처리"""
        if error_code == 429:  # Too Many Requests
            self.rate_limiter.handle_rate_limit_error()
        elif 200 <= error_code < 300:  # 성공
            self.rate_limiter.reset_backoff()

    def get_routing_stats(self) -> Dict[str, Any]:
        """라우팅 통계"""
        return {
            "pattern_stats": self.pattern_tracker.get_all_patterns(),
            "rate_limit_status": self.rate_limiter.get_status(),
            "active_symbols": len(self.pattern_tracker.symbol_patterns)
        }

    def cleanup_inactive_patterns(self, hours: int = 1) -> int:
        """비활성 패턴 정리"""
        return self.pattern_tracker.cleanup_inactive(hours)


def create_smart_router() -> SmartChannelRouter:
    """스마트 라우터 팩토리"""
    return SmartChannelRouter()
