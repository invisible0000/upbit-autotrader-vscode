"""
WebSocket 장애 복구 전략

Smart Router가 WebSocket 장애 시 투명하게 REST API로 전환하여
사용자 경험을 최대한 보장하는 다층 Fallback 시스템입니다.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
import asyncio
import logging
from datetime import datetime, timedelta

from ..models import TradingSymbol, Timeframe, CandleDataRequest
from ..utils.exceptions import WebSocketException, DataRouterException


class FallbackLevel(Enum):
    """장애 복구 단계"""
    NORMAL = "normal"                    # 정상 WebSocket 동작
    IMMEDIATE_FALLBACK = "immediate"     # 즉시 REST API 전환
    BATCH_SIMULATION = "batch"           # 배치 모사 (폴링)
    SYSTEM_REST_MODE = "system_rest"     # 시스템 전체 REST 모드


class WebSocketHealthStatus(Enum):
    """WebSocket 상태"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"      # 일부 기능 장애
    FAILED = "failed"          # 완전 장애
    RECONNECTING = "reconnecting"


@dataclass
class FallbackStrategy:
    """Fallback 전략 설정"""

    level: FallbackLevel
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    polling_interval_seconds: float = 5.0
    health_check_interval: float = 30.0


class WebSocketFallbackManager:
    """WebSocket 장애 복구 관리자

    Smart Router의 WebSocket 장애를 투명하게 처리하여
    사용자는 느려진 것만 느끼고 기능은 계속 동작하도록 보장
    """

    def __init__(self, rest_provider, logger: Optional[logging.Logger] = None):
        self.rest_provider = rest_provider
        self.logger = logger or logging.getLogger(self.__class__.__name__)

        # 현재 상태
        self.current_level = FallbackLevel.NORMAL
        self.websocket_status = WebSocketHealthStatus.HEALTHY
        self.last_websocket_error: Optional[Exception] = None
        self.fallback_start_time: Optional[datetime] = None

        # 전략 설정
        self.strategies = {
            FallbackLevel.IMMEDIATE_FALLBACK: FallbackStrategy(
                level=FallbackLevel.IMMEDIATE_FALLBACK,
                retry_attempts=3,
                retry_delay_seconds=1.0
            ),
            FallbackLevel.BATCH_SIMULATION: FallbackStrategy(
                level=FallbackLevel.BATCH_SIMULATION,
                retry_attempts=5,
                polling_interval_seconds=3.0
            ),
            FallbackLevel.SYSTEM_REST_MODE: FallbackStrategy(
                level=FallbackLevel.SYSTEM_REST_MODE,
                retry_attempts=10,
                health_check_interval=60.0
            )
        }

        # 실행 중인 폴링 태스크
        self.polling_tasks: Dict[str, asyncio.Task] = {}

        # 복구 시도 통계
        self.recovery_stats = {
            "total_failures": 0,
            "immediate_recoveries": 0,
            "batch_fallbacks": 0,
            "system_mode_activations": 0,
            "current_uptime": datetime.now()
        }

    async def handle_websocket_error(
        self,
        error: Exception,
        operation: str,
        **operation_kwargs
    ) -> Any:
        """WebSocket 오류 처리 및 자동 복구

        Args:
            error: 발생한 WebSocket 오류
            operation: 실패한 작업 ("get_candle_data", "subscribe_realtime" 등)
            **operation_kwargs: 원본 작업의 매개변수들

        Returns:
            Fallback으로 처리된 결과
        """
        self.last_websocket_error = error
        self.recovery_stats["total_failures"] += 1

        self.logger.warning(
            f"WebSocket 오류 감지: {operation} - {str(error)}"
        )

        # 현재 레벨에 따른 처리
        if self.current_level == FallbackLevel.NORMAL:
            return await self._immediate_fallback(operation, **operation_kwargs)
        elif self.current_level == FallbackLevel.IMMEDIATE_FALLBACK:
            return await self._batch_simulation_fallback(operation, **operation_kwargs)
        elif self.current_level == FallbackLevel.BATCH_SIMULATION:
            return await self._system_rest_mode_fallback(operation, **operation_kwargs)
        else:
            # 이미 시스템 REST 모드
            return await self._execute_rest_operation(operation, **operation_kwargs)

    async def _immediate_fallback(self, operation: str, **kwargs) -> Any:
        """Level 1: 즉시 REST API 전환"""
        self.current_level = FallbackLevel.IMMEDIATE_FALLBACK
        self.fallback_start_time = datetime.now()

        self.logger.info("Level 1 Fallback: 즉시 REST API 전환")

        try:
            # 즉시 REST API로 실행
            result = await self._execute_rest_operation(operation, **kwargs)

            self.recovery_stats["immediate_recoveries"] += 1

            # 백그라운드에서 WebSocket 복구 시도
            asyncio.create_task(self._attempt_websocket_recovery())

            return result

        except Exception as e:
            self.logger.error(f"즉시 Fallback 실패: {e}")
            # 다음 단계로 진행
            return await self._batch_simulation_fallback(operation, **kwargs)

    async def _batch_simulation_fallback(self, operation: str, **kwargs) -> Any:
        """Level 2: 배치 모사 (폴링으로 WebSocket 흉내)"""
        self.current_level = FallbackLevel.BATCH_SIMULATION

        self.logger.info("Level 2 Fallback: 배치 모사 모드 (폴링)")

        self.recovery_stats["batch_fallbacks"] += 1

        # realtime_only 또는 snapshot_only 요청에 대한 특별 처리
        if self._is_realtime_request(operation, kwargs):
            return await self._simulate_realtime_with_polling(operation, **kwargs)
        else:
            # 일반 요청은 바로 REST API 처리
            return await self._execute_rest_operation(operation, **kwargs)

    async def _system_rest_mode_fallback(self, operation: str, **kwargs) -> Any:
        """Level 3: 시스템 전체 REST 모드"""
        self.current_level = FallbackLevel.SYSTEM_REST_MODE

        self.logger.warning("Level 3 Fallback: 시스템 전체 REST 모드 활성화")

        self.recovery_stats["system_mode_activations"] += 1

        # 모든 WebSocket 기능을 완전히 비활성화
        await self._disable_all_websocket_features()

        # REST API로만 동작
        return await self._execute_rest_operation(operation, **kwargs)

    async def _execute_rest_operation(self, operation: str, **kwargs) -> Any:
        """REST API를 사용하여 작업 실행"""
        try:
            if operation == "get_candle_data":
                return await self._rest_get_candle_data(**kwargs)
            elif operation == "get_ticker_data":
                return await self._rest_get_ticker_data(**kwargs)
            elif operation == "subscribe_realtime":
                return await self._rest_simulate_subscription(**kwargs)
            else:
                raise DataRouterException(f"지원하지 않는 REST 작업: {operation}")

        except Exception as e:
            self.logger.error(f"REST API 작업 실패 {operation}: {e}")
            raise DataRouterException(f"REST Fallback 실패: {str(e)}")

    async def _rest_get_candle_data(
        self,
        symbol: TradingSymbol,
        timeframe: Timeframe,
        realtime_only: bool = False,
        snapshot_only: bool = False,
        **kwargs
    ):
        """REST API로 캔들 데이터 조회 (realtime/snapshot 옵션 처리)"""

        if realtime_only:
            # 실시간 전용 요청: 최신 1개 캔들만 조회
            self.logger.info(f"REST로 realtime_only 모사: {symbol} {timeframe}")
            request = CandleDataRequest(
                symbol=symbol,
                timeframe=timeframe,
                count=1  # 최신 캔들 1개만
            )
            return await self.rest_provider.get_candle_data(request)

        elif snapshot_only:
            # 스냅샷 전용 요청: 완성된 캔들들만 조회
            self.logger.info(f"REST로 snapshot_only 모사: {symbol} {timeframe}")
            request = CandleDataRequest(
                symbol=symbol,
                timeframe=timeframe,
                **kwargs  # count, start_time, end_time 등
            )
            return await self.rest_provider.get_candle_data(request)

        else:
            # 일반 요청: 그대로 처리
            request = CandleDataRequest(
                symbol=symbol,
                timeframe=timeframe,
                **kwargs
            )
            return await self.rest_provider.get_candle_data(request)

    async def _rest_get_ticker_data(self, symbol: TradingSymbol, **kwargs):
        """REST API로 티커 데이터 조회"""
        from ..models.requests import RequestFactory

        request = RequestFactory.current_ticker(symbol)
        return await self.rest_provider.get_ticker_data(request)

    async def _rest_simulate_subscription(
        self,
        symbol: TradingSymbol,
        data_types: List[str],
        callback: Callable,
        **kwargs
    ) -> str:
        """REST API로 실시간 구독 모사 (폴링)"""

        subscription_id = f"rest_polling_{symbol}_{datetime.now().timestamp()}"

        # 폴링 태스크 시작
        polling_task = asyncio.create_task(
            self._polling_subscription(symbol, data_types, callback, subscription_id)
        )

        self.polling_tasks[subscription_id] = polling_task

        self.logger.info(
            f"REST 폴링 구독 시작: {subscription_id} "
            f"(데이터 타입: {data_types})"
        )

        return subscription_id

    async def _polling_subscription(
        self,
        symbol: TradingSymbol,
        data_types: List[str],
        callback: Callable,
        subscription_id: str
    ):
        """폴링 기반 구독 구현"""

        strategy = self.strategies[self.current_level]
        interval = strategy.polling_interval_seconds

        self.logger.info(f"폴링 구독 시작: {subscription_id} (간격: {interval}초)")

        try:
            while subscription_id in self.polling_tasks:
                for data_type in data_types:
                    try:
                        if data_type == "ticker":
                            data = await self._rest_get_ticker_data(symbol)
                            await callback({"type": "ticker", "data": data})
                        # 다른 데이터 타입들도 추가 가능

                    except Exception as e:
                        self.logger.error(f"폴링 중 오류: {data_type} - {e}")

                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            self.logger.info(f"폴링 구독 취소: {subscription_id}")
        except Exception as e:
            self.logger.error(f"폴링 구독 오류: {subscription_id} - {e}")

    async def _simulate_realtime_with_polling(self, operation: str, **kwargs):
        """실시간 요청을 폴링으로 모사"""

        self.logger.info(f"실시간 요청을 폴링으로 모사: {operation}")

        # 초기 데이터 반환
        initial_result = await self._execute_rest_operation(operation, **kwargs)

        # 백그라운드에서 주기적 업데이트 (필요시)
        if "callback" in kwargs:
            callback = kwargs["callback"]
            symbol = kwargs.get("symbol")

            # 주기적 업데이트 태스크 시작
            update_task = asyncio.create_task(
                self._periodic_update(symbol, callback, operation, kwargs)
            )

            # 태스크 추적
            task_id = f"update_{symbol}_{datetime.now().timestamp()}"
            self.polling_tasks[task_id] = update_task

        return initial_result

    async def _periodic_update(
        self,
        symbol: TradingSymbol,
        callback: Callable,
        operation: str,
        original_kwargs: Dict[str, Any]
    ):
        """주기적 데이터 업데이트"""

        strategy = self.strategies[self.current_level]
        interval = strategy.polling_interval_seconds

        try:
            while True:
                await asyncio.sleep(interval)

                try:
                    # 최신 데이터 조회
                    updated_data = await self._execute_rest_operation(
                        operation, **original_kwargs
                    )

                    # 콜백 호출
                    await callback(updated_data)

                except Exception as e:
                    self.logger.error(f"주기적 업데이트 실패: {e}")

        except asyncio.CancelledError:
            self.logger.info(f"주기적 업데이트 취소: {symbol}")

    def _is_realtime_request(self, operation: str, kwargs: Dict[str, Any]) -> bool:
        """실시간 요청 여부 판단"""
        if operation == "subscribe_realtime":
            return True

        if operation == "get_candle_data":
            return kwargs.get("realtime_only", False)

        return False

    async def _attempt_websocket_recovery(self):
        """WebSocket 복구 시도"""

        strategy = self.strategies[self.current_level]

        for attempt in range(strategy.retry_attempts):
            try:
                await asyncio.sleep(strategy.retry_delay_seconds * (attempt + 1))

                # WebSocket 상태 확인
                if await self._check_websocket_health():
                    await self._recover_to_normal_mode()
                    return

            except Exception as e:
                self.logger.warning(f"WebSocket 복구 시도 {attempt + 1} 실패: {e}")

        # 복구 실패 시 다음 레벨로 진행
        await self._escalate_fallback_level()

    async def _check_websocket_health(self) -> bool:
        """WebSocket 상태 확인"""
        try:
            # 실제 WebSocket 연결 테스트
            # (구현 필요: 간단한 ping/pong 또는 test subscription)

            # 임시 구현: 항상 False (실제로는 WebSocket Provider에 확인)
            return False

        except Exception as e:
            self.logger.error(f"WebSocket 상태 확인 실패: {e}")
            return False

    async def _recover_to_normal_mode(self):
        """정상 모드로 복구"""

        self.logger.info("WebSocket 복구 성공! 정상 모드로 전환")

        # 폴링 태스크들 정리
        await self._cleanup_polling_tasks()

        # 상태 리셋
        self.current_level = FallbackLevel.NORMAL
        self.websocket_status = WebSocketHealthStatus.HEALTHY
        self.last_websocket_error = None
        self.fallback_start_time = None

    async def _escalate_fallback_level(self):
        """Fallback 레벨 상승"""

        current_index = list(FallbackLevel).index(self.current_level)

        if current_index < len(FallbackLevel) - 1:
            new_level = list(FallbackLevel)[current_index + 1]
            self.current_level = new_level

            self.logger.warning(f"Fallback 레벨 상승: {new_level.value}")
        else:
            self.logger.error("최대 Fallback 레벨에 도달했습니다")

    async def _disable_all_websocket_features(self):
        """모든 WebSocket 기능 비활성화"""

        self.logger.warning("모든 WebSocket 기능을 비활성화합니다")

        # 기존 WebSocket 연결들 정리
        # (구현 필요: WebSocket Provider의 모든 연결 해제)

        # 폴링 태스크들 정리
        await self._cleanup_polling_tasks()

    async def _cleanup_polling_tasks(self):
        """폴링 태스크들 정리"""

        for task_id, task in self.polling_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self.polling_tasks.clear()
        self.logger.info("모든 폴링 태스크를 정리했습니다")

    def get_fallback_status(self) -> Dict[str, Any]:
        """현재 Fallback 상태 조회"""

        uptime = datetime.now() - self.recovery_stats["current_uptime"]
        fallback_duration = None

        if self.fallback_start_time:
            fallback_duration = datetime.now() - self.fallback_start_time

        return {
            "current_level": self.current_level.value,
            "websocket_status": self.websocket_status.value,
            "last_error": str(self.last_websocket_error) if self.last_websocket_error else None,
            "fallback_duration_seconds": fallback_duration.total_seconds() if fallback_duration else 0,
            "active_polling_tasks": len(self.polling_tasks),
            "recovery_stats": self.recovery_stats.copy(),
            "system_uptime_seconds": uptime.total_seconds()
        }


# 사용 예시
async def demonstrate_fallback_system():
    """Fallback 시스템 사용 예시"""

    # REST Provider 필요 (실제 구현에서는 의존성 주입)
    rest_provider = None  # UpbitRestProvider()

    fallback_manager = WebSocketFallbackManager(rest_provider)

    # WebSocket 오류 시뮬레이션
    try:
        # WebSocket으로 캔들 데이터 요청 시도
        raise WebSocketException("연결 끊어짐")

    except WebSocketException as e:
        # 자동 Fallback 처리
        result = await fallback_manager.handle_websocket_error(
            error=e,
            operation="get_candle_data",
            symbol=TradingSymbol("KRW-BTC"),
            timeframe=Timeframe.MINUTE_1,
            realtime_only=True
        )

        print(f"Fallback 결과: {result}")
        print(f"현재 상태: {fallback_manager.get_fallback_status()}")


if __name__ == "__main__":
    asyncio.run(demonstrate_fallback_system())
