"""
Smart Data Router - 도메인 모델 기반 데이터 라우팅 구현체

기존 URL 기반 스마트 라우터를 완전히 교체하는 구현체입니다.
내부 시스템들은 더 이상 Upbit API의 URL 구조를 알 필요가 없습니다.
"""

from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from upbit_auto_trading.infrastructure.logging import create_component_logger
from ..interfaces.data_router import IDataRouter
from ..interfaces.data_provider import IDataProvider
from ..models.symbols import TradingSymbol
from ..models.timeframes import Timeframe
from ..models.requests import (
    CandleDataRequest,
    DataRequestPriority
)
# Response 모델들은 현재 사용하지 않으므로 주석 처리
# from ..models.responses import (...)
from ..utils.exceptions import DataRouterException

logger = create_component_logger("SmartDataRouter")


@dataclass(frozen=True)
class ProviderConfig:
    """데이터 제공자 설정"""
    name: str
    is_primary: bool
    max_concurrent_requests: int
    request_timeout_seconds: int
    retry_attempts: int
    priority_boost: int = 0  # 우선순위 보정값


class SmartDataRouter(IDataRouter):
    """
    Smart Data Router v2.0 - 도메인 모델 기반 구현

    특징:
    - URL 구조 완전 은닉: 내부 시스템은 TradingSymbol, Timeframe만 사용
    - 지능형 채널 선택: 요청 특성에 따른 최적 제공자 선택
    - 실시간/배치 데이터 통합: 단일 인터페이스로 모든 데이터 접근
    - 장애 복구: 자동 폴백 및 재시도 로직
    - 성능 최적화: 동시 요청 제한 및 캐싱 전략
    """

    def __init__(self):
        self._providers: Dict[str, IDataProvider] = {}
        self._provider_configs: Dict[str, ProviderConfig] = {}
        self._active_subscriptions: Dict[str, Any] = {}  # 구독 객체들
        self._request_counts: Dict[str, int] = {}
        self._last_request_times: Dict[str, datetime] = {}

        logger.info("SmartDataRouter v2.0 초기화 완료")

    def register_provider(
        self,
        name: str,
        provider: IDataProvider,
        config: ProviderConfig
    ) -> None:
        """데이터 제공자 등록"""
        self._providers[name] = provider
        self._provider_configs[name] = config
        self._request_counts[name] = 0

        logger.info(f"데이터 제공자 등록: {name} (primary={config.is_primary})")

    def unregister_provider(self, name: str) -> None:
        """데이터 제공자 해제"""
        if name in self._providers:
            del self._providers[name]
            del self._provider_configs[name]
            del self._request_counts[name]
            if name in self._last_request_times:
                del self._last_request_times[name]

            logger.info(f"데이터 제공자 해제: {name}")

    async def get_candle_data(
        self,
        symbol: TradingSymbol,
        timeframe: Timeframe,
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        캔들 데이터 조회 - 기존 인터페이스 호환 (내부에서 Request 객체로 변환)

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임
            count: 조회할 캔들 개수
            start_time: 시작 시간
            end_time: 종료 시간

        Returns:
            표준화된 Dict 형태 응답 (기존 인터페이스 호환)
        """
        logger.debug(f"캔들 데이터 요청: {symbol} {timeframe}")

        # 내부에서 Request 객체로 변환 (추상화 유지)
        request = CandleDataRequest(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            start_time=start_time,
            end_time=end_time
        )

        # 최적 제공자 선택
        provider_name = await self._select_optimal_provider(request)
        if not provider_name:
            raise DataRouterException("사용 가능한 데이터 제공자가 없습니다")

        provider = self._providers[provider_name]

        try:
            # 요청 실행
            self._track_request_start(provider_name)
            response = await self._fetch_candle_data_from_provider(provider, request)
            self._track_request_success(provider_name)

            logger.debug(f"캔들 데이터 응답: {len(response.get('data', []))}개 항목")
            return response

        except Exception as e:
            self._track_request_failure(provider_name)
            logger.error(f"캔들 데이터 조회 실패 ({provider_name}): {e}")

            # 폴백 시도
            fallback_response = await self._try_fallback_providers(
                request, exclude_provider=provider_name
            )
            if fallback_response:
                return fallback_response

            raise DataRouterException(f"모든 제공자에서 캔들 데이터 조회 실패: {e}")

    async def get_ticker_data(self, symbol: TradingSymbol) -> Dict[str, Any]:
        """현재 시세 정보 조회 (기존 인터페이스 호환)"""
        logger.debug(f"티커 데이터 조회: {symbol}")

        provider_name = await self._select_fast_provider()
        provider = self._providers[provider_name]

        try:
            return await self._fetch_ticker_data_from_provider(provider, symbol)
        except Exception as e:
            logger.error(f"티커 데이터 조회 실패 ({provider_name}): {e}")
            raise DataRouterException(f"티커 데이터 조회 실패: {e}")

    async def get_orderbook_data(
        self,
        symbol: TradingSymbol,
        depth: int = 10
    ) -> Dict[str, Any]:
        """호가 정보 조회 (기존 인터페이스 호환)"""
        logger.debug(f"호가 데이터 조회: {symbol}")

        provider_name = await self._select_fast_provider()
        provider = self._providers[provider_name]

        try:
            return await self._fetch_orderbook_data_from_provider(provider, symbol, depth)
        except Exception as e:
            logger.error(f"호가 데이터 조회 실패 ({provider_name}): {e}")
            raise DataRouterException(f"호가 데이터 조회 실패: {e}")

    async def get_trade_history(
        self,
        symbol: TradingSymbol,
        count: Optional[int] = None,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """최근 거래 내역 조회 (기존 인터페이스 호환)"""
        logger.debug(f"거래 내역 조회: {symbol}")

        provider_name = await self._select_fast_provider()
        provider = self._providers[provider_name]

        try:
            return await self._fetch_trade_history_from_provider(provider, symbol, count, cursor)
        except Exception as e:
            logger.error(f"거래 내역 조회 실패 ({provider_name}): {e}")
            raise DataRouterException(f"거래 내역 조회 실패: {e}")

    async def subscribe_realtime(
        self,
        symbol: TradingSymbol,
        data_types: list[str],
        callback: Callable[[Dict[str, Any]], None]
    ) -> str:
        """실시간 데이터 구독 (기존 인터페이스 호환)"""
        logger.info(f"실시간 구독 시작: {symbol} ({data_types})")

        # Primary 제공자 선택 (실시간은 안정성이 최우선)
        provider_name = self._get_primary_provider()
        if not provider_name:
            raise DataRouterException("Primary 데이터 제공자가 없습니다")

        provider = self._providers[provider_name]
        subscription_id = f"{provider_name}:{hash(str(symbol))}:{hash(str(data_types))}"

        try:
            # 실시간 구독 시작
            await self._start_realtime_subscription(provider, symbol, data_types, callback, subscription_id)
            return subscription_id

        except Exception as e:
            logger.error(f"실시간 구독 오류 ({provider_name}): {e}")
            raise DataRouterException(f"실시간 구독 실패: {e}")

    async def unsubscribe_realtime(self, subscription_id: str) -> bool:
        """실시간 데이터 구독 해제 (기존 인터페이스 호환)"""
        logger.info(f"실시간 구독 해제: {subscription_id}")

        try:
            if subscription_id in self._active_subscriptions:
                del self._active_subscriptions[subscription_id]
                return True
            return False
        except Exception as e:
            logger.error(f"구독 해제 실패: {e}")
            return False

    async def get_market_list(self) -> list[TradingSymbol]:
        """지원하는 마켓 목록 조회 (기존 인터페이스 호환)"""
        provider_name = self._get_primary_provider()
        if not provider_name:
            return []

        provider = self._providers[provider_name]
        try:
            return await self._fetch_market_list_from_provider(provider)
        except Exception as e:
            logger.error(f"마켓 목록 조회 실패: {e}")
            return []

    async def get_routing_stats(self) -> Dict[str, Any]:
        """라우팅 통계 정보 (기존 인터페이스 호환)"""
        return {
            "total_providers": len(self._providers),
            "active_subscriptions": len(self._active_subscriptions),
            "request_counts": self._request_counts.copy(),
            "last_request_times": {
                name: time.isoformat() for name, time in self._last_request_times.items()
            }
        }

    async def health_check(self) -> Dict[str, Any]:
        """헬스 체크"""
        logger.debug("헬스 체크 실행")

        health_status = {
            "router_status": "healthy",
            "providers": {},
            "active_subscriptions": len(self._active_subscriptions),
            "total_providers": len(self._providers)
        }

        for name, provider in self._providers.items():
            try:
                provider_health = await provider.health_check()
                health_status["providers"][name] = {
                    "status": "healthy",
                    "details": provider_health,
                    "request_count": self._request_counts.get(name, 0)
                }
            except Exception as e:
                health_status["providers"][name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "request_count": self._request_counts.get(name, 0)
                }

        return health_status

    async def close_subscriptions(self) -> None:
        """모든 구독 종료"""
        logger.info("모든 실시간 구독을 종료합니다")

        for subscription_key in list(self._active_subscriptions.keys()):
            try:
                # AsyncGenerator 종료 (close 메서드가 있다면)
                subscription = self._active_subscriptions[subscription_key]
                if hasattr(subscription, 'aclose'):
                    await subscription.aclose()
                del self._active_subscriptions[subscription_key]
            except Exception as e:
                logger.error(f"구독 종료 실패 ({subscription_key}): {e}")

        logger.info("모든 구독이 종료되었습니다")

    # === Private Helper Methods ===

    async def _select_optimal_provider(self, request: CandleDataRequest) -> Optional[str]:
        """요청에 최적화된 제공자 선택"""
        available_providers = []

        for name, config in self._provider_configs.items():
            if name not in self._providers:
                continue

            # 동시 요청 제한 확인
            current_requests = self._request_counts.get(name, 0)
            if current_requests >= config.max_concurrent_requests:
                continue

            # 우선순위 계산
            priority_score = 0

            # 1. Primary 제공자 우선
            if config.is_primary:
                priority_score += 100

            # 2. 요청 우선순위 반영
            if request.priority == DataRequestPriority.URGENT:
                priority_score += config.priority_boost + 50
            elif request.priority == DataRequestPriority.HIGH:
                priority_score += config.priority_boost + 20

            # 3. 최근 응답 시간 반영 (빠른 제공자 우선)
            last_request_time = self._last_request_times.get(name)
            if last_request_time:
                time_since_last = datetime.now() - last_request_time
                if time_since_last < timedelta(seconds=5):
                    priority_score += 10  # 최근 사용된 제공자 우선

            available_providers.append((name, priority_score))

        if not available_providers:
            return None

        # 우선순위 순으로 정렬하여 최적 제공자 선택
        available_providers.sort(key=lambda x: x[1], reverse=True)
        return available_providers[0][0]

    async def _select_fast_provider(self) -> str:
        """빠른 응답이 필요한 요청용 제공자 선택"""
        # Primary 제공자 중에서 현재 요청이 적은 것 선택
        primary_providers = [
            (name, config) for name, config in self._provider_configs.items()
            if config.is_primary and name in self._providers
        ]

        if not primary_providers:
            # Primary가 없으면 아무나
            if not self._providers:
                raise DataRouterException("사용 가능한 제공자가 없습니다")
            return next(iter(self._providers.keys()))

        # 요청 수가 가장 적은 Primary 제공자 선택
        best_provider = min(
            primary_providers,
            key=lambda x: self._request_counts.get(x[0], 0)
        )

        return best_provider[0]

    def _get_primary_provider(self) -> Optional[str]:
        """Primary 제공자 조회"""
        for name, config in self._provider_configs.items():
            if config.is_primary and name in self._providers:
                return name
        return None

    # === Provider Helper Methods ===

    async def _fetch_candle_data_from_provider(
        self,
        provider: IDataProvider,
        request: CandleDataRequest
    ) -> Dict[str, Any]:
        """Provider로부터 캔들 데이터 조회"""
        # UpbitDataProvider의 메서드 호출
        if hasattr(provider, 'fetch_candle_data_dict'):
            return await provider.fetch_candle_data_dict(
                request.symbol,
                request.timeframe,
                request.count,
                request.start_time,
                request.end_time
            )
        else:
            raise DataRouterException("Provider가 캔들 데이터 조회를 지원하지 않습니다")

    async def _fetch_ticker_data_from_provider(
        self,
        provider: IDataProvider,
        symbol: TradingSymbol
    ) -> Dict[str, Any]:
        """Provider로부터 티커 데이터 조회"""
        if hasattr(provider, 'fetch_ticker_data_dict'):
            return await provider.fetch_ticker_data_dict(symbol)
        else:
            raise DataRouterException("Provider가 티커 데이터 조회를 지원하지 않습니다")

    async def _fetch_orderbook_data_from_provider(
        self,
        provider: IDataProvider,
        symbol: TradingSymbol,
        depth: int
    ) -> Dict[str, Any]:
        """Provider로부터 호가 데이터 조회"""
        if hasattr(provider, 'fetch_orderbook_data_dict'):
            return await provider.fetch_orderbook_data_dict(symbol, depth)
        else:
            raise DataRouterException("Provider가 호가 데이터 조회를 지원하지 않습니다")

    async def _fetch_trade_history_from_provider(
        self,
        provider: IDataProvider,
        symbol: TradingSymbol,
        count: Optional[int],
        cursor: Optional[str]
    ) -> Dict[str, Any]:
        """Provider로부터 거래 내역 조회"""
        if hasattr(provider, 'fetch_trade_history_dict'):
            return await provider.fetch_trade_history_dict(symbol, count, cursor)
        else:
            raise DataRouterException("Provider가 거래 내역 조회를 지원하지 않습니다")

    async def _fetch_market_list_from_provider(
        self,
        provider: IDataProvider
    ) -> list[TradingSymbol]:
        """Provider로부터 마켓 목록 조회"""
        if hasattr(provider, 'fetch_market_list'):
            return await provider.fetch_market_list()
        else:
            raise DataRouterException("Provider가 마켓 목록 조회를 지원하지 않습니다")

    async def _start_realtime_subscription(
        self,
        provider: IDataProvider,
        symbol: TradingSymbol,
        data_types: list[str],
        callback: Callable[[Dict[str, Any]], None],
        subscription_id: str
    ) -> None:
        """실시간 구독 시작"""
        # 현재는 REST API만 지원하므로 에러
        raise DataRouterException("실시간 구독은 아직 지원되지 않습니다 (REST API만 지원)")

    async def _try_fallback_providers(
        self,
        request: CandleDataRequest,
        exclude_provider: str
    ) -> Optional[Dict[str, Any]]:
        """폴백 제공자들로 재시도"""
        for name, provider in self._providers.items():
            if name == exclude_provider:
                continue

            try:
                logger.info(f"폴백 제공자로 재시도: {name}")
                response = await self._fetch_candle_data_from_provider(provider, request)
                return response
            except Exception as e:
                logger.warning(f"폴백 제공자 실패 ({name}): {e}")
                continue

        return None

    def _track_request_start(self, provider_name: str) -> None:
        """요청 시작 추적"""
        self._request_counts[provider_name] = self._request_counts.get(provider_name, 0) + 1
        self._last_request_times[provider_name] = datetime.now()

    def _track_request_success(self, provider_name: str) -> None:
        """요청 성공 추적"""
        if provider_name in self._request_counts:
            self._request_counts[provider_name] = max(0, self._request_counts[provider_name] - 1)

    def _track_request_failure(self, provider_name: str) -> None:
        """요청 실패 추적"""
        if provider_name in self._request_counts:
            self._request_counts[provider_name] = max(0, self._request_counts[provider_name] - 1)
