"""
통합 레이트 제한 및 필드 매핑 시스템

전체 Smart Routing Layer의 API 호출을 통합 관리하고
업비트 API 응답을 표준 형식으로 변환합니다.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

from ..models import TradingSymbol, Timeframe, CandleData, TickerData, OrderbookData, TradeData


class RateLimitType(Enum):
    """레이트 제한 유형"""
    REST_API = "rest_api"              # REST API 호출
    WEBSOCKET = "websocket"            # WebSocket 연결
    CANDLE_DATA = "candle_data"        # 캔들 데이터 요청
    TICKER_DATA = "ticker_data"        # 티커 데이터 요청
    ORDERBOOK_DATA = "orderbook_data"  # 호가 데이터 요청


class FieldMappingError(Exception):
    """필드 매핑 오류"""
    pass


@dataclass
class RateLimitConfig:
    """레이트 제한 설정"""

    requests_per_second: float
    requests_per_minute: int
    burst_capacity: int = 10
    cooldown_seconds: float = 1.0

    @property
    def min_interval(self) -> float:
        """최소 요청 간격 (초)"""
        return 1.0 / self.requests_per_second


@dataclass
class RateLimitState:
    """레이트 제한 상태"""

    config: RateLimitConfig
    request_times: List[float]
    last_request_time: float = 0.0
    total_requests: int = 0
    rejected_requests: int = 0

    def is_rate_limited(self, current_time: float) -> bool:
        """현재 레이트 제한 상태인지 확인"""

        # 1초당 제한 체크 - 더 관대한 검사
        if current_time - self.last_request_time < self.config.min_interval * 0.8:  # 20% 여유
            return True

        # 1분당 제한 체크
        minute_ago = current_time - 60.0
        recent_requests = [t for t in self.request_times if t > minute_ago]

        if len(recent_requests) >= self.config.requests_per_minute:
            return True

        return False

    def record_request(self, current_time: float) -> None:
        """요청 기록"""

        self.request_times.append(current_time)
        self.last_request_time = current_time
        self.total_requests += 1

        # 1분 이전 기록 정리
        minute_ago = current_time - 60.0
        self.request_times = [t for t in self.request_times if t > minute_ago]

    def record_rejection(self) -> None:
        """거부 기록"""
        self.rejected_requests += 1


class IntegratedRateLimiter:
    """통합 레이트 제한기

    모든 API 호출 유형에 대해 개별적으로 레이트 제한을 적용하며,
    전역 레이트 제한도 함께 관리합니다.
    """

    def __init__(self):
        # 업비트 공식 API 제한사항 기준 (전문가 의견 반영)
        self.rate_limit_configs = {
            RateLimitType.REST_API: RateLimitConfig(
                requests_per_second=8.0,  # REST API: 일반적으로 8-30/s, 안전 마진
                requests_per_minute=400,
                burst_capacity=15
            ),
            RateLimitType.WEBSOCKET: RateLimitConfig(
                requests_per_second=4.0,  # WebSocket 연결/메시지: 5/s 제한, 안전 마진
                requests_per_minute=100,  # 분당 100회 제한
                burst_capacity=5
            ),
            RateLimitType.CANDLE_DATA: RateLimitConfig(
                requests_per_second=5.0,  # 캔들 데이터는 REST 기반
                requests_per_minute=200,
                burst_capacity=10
            ),
            RateLimitType.TICKER_DATA: RateLimitConfig(
                requests_per_second=4.0,  # WebSocket 기반, 연결 제한 준수
                requests_per_minute=100,
                burst_capacity=8
            ),
            RateLimitType.ORDERBOOK_DATA: RateLimitConfig(
                requests_per_second=4.0,  # WebSocket 기반, 연결 제한 준수
                requests_per_minute=100,
                burst_capacity=8
            )
        }

        # 각 유형별 상태 관리
        self.rate_limit_states: Dict[RateLimitType, RateLimitState] = {}

        for limit_type, config in self.rate_limit_configs.items():
            self.rate_limit_states[limit_type] = RateLimitState(
                config=config,
                request_times=[]
            )

        # 전역 제한
        self.global_state = RateLimitState(
            config=RateLimitConfig(
                requests_per_second=15.0,
                requests_per_minute=800,
                burst_capacity=30
            ),
            request_times=[]
        )

        self.logger = logging.getLogger(self.__class__.__name__)

    async def acquire(
        self,
        rate_limit_type: RateLimitType,
        priority: float = 1.0
    ) -> bool:
        """레이트 제한 권한 획득

        Args:
            rate_limit_type: 제한 유형
            priority: 우선순위 (높을수록 우선, 기본 1.0)

        Returns:
            권한 획득 성공 여부
        """

        current_time = time.time()

        # 해당 유형의 레이트 제한 확인
        type_state = self.rate_limit_states[rate_limit_type]

        if type_state.is_rate_limited(current_time):
            type_state.record_rejection()
            self.logger.debug(f"레이트 제한 거부: {rate_limit_type.value}")
            return False

        # 전역 레이트 제한 확인
        if self.global_state.is_rate_limited(current_time):
            self.global_state.record_rejection()
            self.logger.debug("전역 레이트 제한 거부")
            return False

        # 권한 획득 성공 - 기록
        type_state.record_request(current_time)
        self.global_state.record_request(current_time)

        self.logger.debug(f"레이트 제한 권한 획득: {rate_limit_type.value}")
        return True

    async def wait_for_availability(
        self,
        rate_limit_type: RateLimitType,
        timeout_seconds: float = 30.0
    ) -> bool:
        """레이트 제한 해제까지 대기

        Args:
            rate_limit_type: 제한 유형
            timeout_seconds: 최대 대기 시간

        Returns:
            권한 획득 성공 여부
        """

        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            if await self.acquire(rate_limit_type):
                return True

            # 다음 요청 가능 시간까지 대기
            type_state = self.rate_limit_states[rate_limit_type]
            wait_time = type_state.config.min_interval

            await asyncio.sleep(min(wait_time, 0.1))

        self.logger.warning(f"레이트 제한 대기 시간 초과: {rate_limit_type.value}")
        return False

    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """레이트 제한 통계"""

        stats = {}

        for limit_type, state in self.rate_limit_states.items():
            current_time = time.time()
            minute_ago = current_time - 60.0
            recent_requests = len([t for t in state.request_times if t > minute_ago])

            stats[limit_type.value] = {
                "total_requests": state.total_requests,
                "rejected_requests": state.rejected_requests,
                "recent_requests_per_minute": recent_requests,
                "limit_per_minute": state.config.requests_per_minute,
                "utilization_rate": recent_requests / state.config.requests_per_minute,
                "last_request_time": state.last_request_time
            }

        # 전역 통계
        global_recent = len([t for t in self.global_state.request_times if t > time.time() - 60.0])
        stats["global"] = {
            "total_requests": self.global_state.total_requests,
            "rejected_requests": self.global_state.rejected_requests,
            "recent_requests_per_minute": global_recent,
            "limit_per_minute": self.global_state.config.requests_per_minute,
            "utilization_rate": global_recent / self.global_state.config.requests_per_minute
        }

        return stats

    def update_rate_limit_config(
        self,
        rate_limit_type: RateLimitType,
        config: RateLimitConfig
    ) -> None:
        """레이트 제한 설정 업데이트"""

        self.rate_limit_configs[rate_limit_type] = config
        self.rate_limit_states[rate_limit_type].config = config

        self.logger.info(f"레이트 제한 설정 업데이트: {rate_limit_type.value}")


class UpbitFieldMapper:
    """업비트 API 응답 필드 매핑기

    업비트 API의 다양한 응답 형식을 표준 데이터 모델로 변환합니다.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def map_candle_data(
        self,
        upbit_response: Dict[str, Any],
        symbol: TradingSymbol,
        timeframe: Timeframe
    ) -> CandleData:
        """업비트 캔들 데이터를 표준 형식으로 매핑"""

        try:
            return CandleData(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=datetime.fromisoformat(
                    upbit_response["candle_date_time_kst"].replace("T", " ")
                ),
                open_price=float(upbit_response["opening_price"]),
                high_price=float(upbit_response["high_price"]),
                low_price=float(upbit_response["low_price"]),
                close_price=float(upbit_response["trade_price"]),
                volume=float(upbit_response["candle_acc_trade_volume"]),
                trade_amount=float(upbit_response["candle_acc_trade_price"])
            )

        except (KeyError, ValueError, TypeError) as e:
            raise FieldMappingError(f"캔들 데이터 매핑 실패: {e}") from e

    def map_ticker_data(
        self,
        upbit_response: Dict[str, Any],
        symbol: TradingSymbol
    ) -> TickerData:
        """업비트 티커 데이터를 표준 형식으로 매핑"""

        try:
            return TickerData(
                symbol=symbol,
                timestamp=datetime.fromtimestamp(upbit_response["timestamp"] / 1000),
                trade_price=float(upbit_response["trade_price"]),
                trade_volume=float(upbit_response["trade_volume"]),
                prev_closing_price=float(upbit_response["prev_closing_price"]),
                change_rate=float(upbit_response["signed_change_rate"]),
                change_amount=float(upbit_response["signed_change_price"]),
                bid_price=float(upbit_response.get("highest_52_week_price", 0)),  # 임시 매핑
                ask_price=float(upbit_response.get("lowest_52_week_price", 0)),   # 임시 매핑
                acc_trade_volume_24h=float(upbit_response["acc_trade_volume_24h"]),
                acc_trade_price_24h=float(upbit_response["acc_trade_price_24h"])
            )

        except (KeyError, ValueError, TypeError) as e:
            raise FieldMappingError(f"티커 데이터 매핑 실패: {e}") from e

    def map_orderbook_data(
        self,
        upbit_response: Dict[str, Any],
        symbol: TradingSymbol
    ) -> OrderbookData:
        """업비트 호가 데이터를 표준 형식으로 매핑"""

        try:
            from ..models.market_data_types import OrderbookLevel

            # 매수/매도 호가 변환
            bid_levels = []
            ask_levels = []

            for unit in upbit_response["orderbook_units"]:
                # 매수 호가
                bid_levels.append(OrderbookLevel(
                    price=float(unit["bid_price"]),
                    size=float(unit["bid_size"])
                ))

                # 매도 호가
                ask_levels.append(OrderbookLevel(
                    price=float(unit["ask_price"]),
                    size=float(unit["ask_size"])
                ))

            return OrderbookData(
                symbol=symbol,
                timestamp=datetime.fromtimestamp(upbit_response["timestamp"] / 1000),
                bid_levels=bid_levels,
                ask_levels=ask_levels,
                total_bid_size=float(upbit_response["total_bid_size"]),
                total_ask_size=float(upbit_response["total_ask_size"])
            )

        except (KeyError, ValueError, TypeError) as e:
            raise FieldMappingError(f"호가 데이터 매핑 실패: {e}") from e

    def map_trade_data(
        self,
        upbit_response: Dict[str, Any],
        symbol: TradingSymbol
    ) -> TradeData:
        """업비트 체결 데이터를 표준 형식으로 매핑"""

        try:
            return TradeData(
                symbol=symbol,
                timestamp=datetime.fromtimestamp(upbit_response["timestamp"] / 1000),
                trade_id=str(upbit_response["sequential_id"]),
                price=float(upbit_response["trade_price"]),
                volume=float(upbit_response["trade_volume"]),
                side=upbit_response["ask_bid"].upper(),  # ASK 또는 BID
                change_price=float(upbit_response.get("change_price", 0)),
                prev_closing_price=float(upbit_response.get("prev_closing_price", 0))
            )

        except (KeyError, ValueError, TypeError) as e:
            raise FieldMappingError(f"체결 데이터 매핑 실패: {e}") from e

    def map_batch_response(
        self,
        upbit_responses: List[Dict[str, Any]],
        data_type: str,
        symbol: TradingSymbol,
        timeframe: Optional[Timeframe] = None
    ) -> List[Union[CandleData, TickerData, OrderbookData, TradeData]]:
        """배치 응답 매핑"""

        mapped_data = []

        for response in upbit_responses:
            try:
                if data_type == "candles" and timeframe:
                    mapped_data.append(self.map_candle_data(response, symbol, timeframe))
                elif data_type == "ticker":
                    mapped_data.append(self.map_ticker_data(response, symbol))
                elif data_type == "orderbook":
                    mapped_data.append(self.map_orderbook_data(response, symbol))
                elif data_type == "trades":
                    mapped_data.append(self.map_trade_data(response, symbol))
                else:
                    self.logger.warning(f"지원하지 않는 데이터 타입: {data_type}")

            except FieldMappingError as e:
                self.logger.error(f"배치 매핑 중 오류: {e}")
                continue

        return mapped_data


class IntegratedRateLimitFieldMapper:
    """통합 레이트 제한 및 필드 매핑 시스템

    레이트 제한과 필드 매핑을 하나의 인터페이스로 통합하여
    Smart Routing Layer 전체에서 일관성 있게 사용할 수 있도록 합니다.
    """

    def __init__(self):
        self.rate_limiter = IntegratedRateLimiter()
        self.field_mapper = UpbitFieldMapper()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute_with_rate_limit(
        self,
        rate_limit_type: RateLimitType,
        api_call: Callable,
        *args,
        **kwargs
    ) -> Any:
        """레이트 제한과 함께 API 호출 실행"""

        # 레이트 제한 권한 획득
        if not await self.rate_limiter.wait_for_availability(rate_limit_type):
            raise Exception(f"레이트 제한으로 인한 API 호출 실패: {rate_limit_type.value}")

        try:
            # API 호출 실행
            result = await api_call(*args, **kwargs)
            self.logger.debug(f"API 호출 성공: {rate_limit_type.value}")
            return result

        except Exception as e:
            self.logger.error(f"API 호출 실패: {rate_limit_type.value} - {e}")
            raise

    async def get_candle_data_with_mapping(
        self,
        api_call: Callable,
        symbol: TradingSymbol,
        timeframe: Timeframe,
        *args,
        **kwargs
    ) -> List[CandleData]:
        """캔들 데이터 조회 및 매핑"""

        # 레이트 제한과 함께 API 호출
        upbit_response = await self.execute_with_rate_limit(
            RateLimitType.CANDLE_DATA,
            api_call,
            *args,
            **kwargs
        )

        # 응답 데이터 매핑
        if isinstance(upbit_response, list):
            return self.field_mapper.map_batch_response(
                upbit_response, "candles", symbol, timeframe
            )
        else:
            return [self.field_mapper.map_candle_data(upbit_response, symbol, timeframe)]

    async def get_ticker_data_with_mapping(
        self,
        api_call: Callable,
        symbol: TradingSymbol,
        *args,
        **kwargs
    ) -> TickerData:
        """티커 데이터 조회 및 매핑"""

        # 레이트 제한과 함께 API 호출
        upbit_response = await self.execute_with_rate_limit(
            RateLimitType.TICKER_DATA,
            api_call,
            *args,
            **kwargs
        )

        # 단일 응답인 경우 리스트에서 첫 번째 요소 추출
        if isinstance(upbit_response, list) and len(upbit_response) > 0:
            upbit_response = upbit_response[0]

        # 응답 데이터 매핑
        return self.field_mapper.map_ticker_data(upbit_response, symbol)

    async def get_orderbook_data_with_mapping(
        self,
        api_call: Callable,
        symbol: TradingSymbol,
        *args,
        **kwargs
    ) -> OrderbookData:
        """호가 데이터 조회 및 매핑"""

        # 레이트 제한과 함께 API 호출
        upbit_response = await self.execute_with_rate_limit(
            RateLimitType.ORDERBOOK_DATA,
            api_call,
            *args,
            **kwargs
        )

        # 단일 응답인 경우 리스트에서 첫 번째 요소 추출
        if isinstance(upbit_response, list) and len(upbit_response) > 0:
            upbit_response = upbit_response[0]

        # 응답 데이터 매핑
        return self.field_mapper.map_orderbook_data(upbit_response, symbol)

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """통합 시스템 전체 통계"""

        return {
            "rate_limiter_stats": self.rate_limiter.get_rate_limit_stats(),
            "system_info": {
                "rate_limit_types": len(RateLimitType),
                "supported_data_types": ["candles", "ticker", "orderbook", "trades"]
            }
        }
