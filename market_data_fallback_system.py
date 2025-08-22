"""
마켓 데이터 폴백 시스템 구현
스마트 라우터 장애 시 직접 클라이언트로 자동 폴백
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
    UpbitWebSocketQuotationClient
)


@dataclass
class FallbackMetrics:
    """폴백 시스템 지표"""
    smart_router_success_count: int = 0
    smart_router_failure_count: int = 0
    fallback_activation_count: int = 0
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    current_mode: str = "smart_router"  # "smart_router" | "fallback"


class MarketDataFallbackSystem:
    """마켓 데이터 폴백 시스템"""

    def __init__(self):
        self.logger = create_component_logger("MarketDataFallback")
        self.metrics = FallbackMetrics()

        # 스마트 라우터 (선택적)
        self.smart_router = None
        self.smart_router_available = False

        # 기본 클라이언트 (필수)
        self.public_client = UpbitPublicClient()
        self.websocket_client = UpbitWebSocketQuotationClient()

        # 폴백 설정
        self.max_failures = 3
        self.failure_timeout = 300  # 5분
        self.health_check_interval = 60  # 1분

        self.logger.info("폴백 시스템 초기화 완료")

    async def initialize(self):
        """시스템 초기화 - 스마트 라우터 우선, 실패 시 폴백"""
        # 1순위: 스마트 라우터 시도
        await self._try_smart_router_init()

        # 2순위: 기본 클라이언트 준비 (항상 실행)
        await self._prepare_fallback_clients()

        # 3순위: 상태 모니터링 시작
        asyncio.create_task(self._health_monitor())

    async def _try_smart_router_init(self):
        """스마트 라우터 초기화 시도"""
        try:
            from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing import SmartRouter

            self.smart_router = SmartRouter()
            await self.smart_router.initialize()

            # 기본 기능 테스트
            test_result = await self.smart_router.get_ticker(["KRW-BTC"])
            if test_result.get('success'):
                self.smart_router_available = True
                self.metrics.current_mode = "smart_router"
                self.metrics.last_success_time = datetime.now()
                self.logger.info("✅ 스마트 라우터 초기화 성공")
            else:
                raise Exception("스마트 라우터 기능 테스트 실패")

        except Exception as e:
            self.smart_router_available = False
            self.metrics.current_mode = "fallback"
            self.metrics.fallback_activation_count += 1
            self.logger.warning(f"⚠️ 스마트 라우터 초기화 실패, 폴백 모드로 시작: {e}")

    async def _prepare_fallback_clients(self):
        """폴백 클라이언트 준비"""
        try:
            # WebSocket 클라이언트 연결 테스트
            await self.websocket_client.connect()
            await self.websocket_client.disconnect()

            self.logger.info("✅ 폴백 클라이언트 준비 완료")

        except Exception as e:
            self.logger.error(f"🚨 폴백 클라이언트 준비 실패: {e}")
            raise Exception("폴백 시스템 초기화 실패 - 시스템 중단")

    async def get_ticker(self, symbols: List[str]) -> Dict[str, Any]:
        """티커 조회 - 자동 폴백 지원"""
        if self.smart_router_available:
            try:
                result = await self.smart_router.get_ticker(symbols)
                if result.get('success'):
                    self._record_success()
                    return result
                else:
                    self._record_failure()
                    await self._check_fallback_trigger()

            except Exception as e:
                self.logger.warning(f"스마트 라우터 티커 조회 실패: {e}")
                self._record_failure()
                await self._check_fallback_trigger()

        # 폴백 실행
        return await self._get_ticker_fallback(symbols)

    async def get_candles(self, symbols: List[str], interval: str,
                         count: int = 1, to: Optional[str] = None) -> Dict[str, Any]:
        """캔들 조회 - 자동 폴백 지원"""
        if self.smart_router_available:
            try:
                result = await self.smart_router.get_candles(
                    symbols, interval=interval, count=count, to=to
                )
                if result.get('success'):
                    self._record_success()
                    return result
                else:
                    self._record_failure()
                    await self._check_fallback_trigger()

            except Exception as e:
                self.logger.warning(f"스마트 라우터 캔들 조회 실패: {e}")
                self._record_failure()
                await self._check_fallback_trigger()

        # 폴백 실행
        return await self._get_candles_fallback(symbols, interval, count, to)

    async def get_trades(self, symbols: List[str], count: int = 1) -> Dict[str, Any]:
        """체결 조회 - 자동 폴백 지원"""
        if self.smart_router_available:
            try:
                result = await self.smart_router.get_trades(symbols, count=count)
                if result.get('success'):
                    self._record_success()
                    return result
                else:
                    self._record_failure()
                    await self._check_fallback_trigger()

            except Exception as e:
                self.logger.warning(f"스마트 라우터 체결 조회 실패: {e}")
                self._record_failure()
                await self._check_fallback_trigger()

        # 폴백 실행
        return await self._get_trades_fallback(symbols, count)

    async def _get_ticker_fallback(self, symbols: List[str]) -> Dict[str, Any]:
        """티커 폴백 구현"""
        try:
            markets = ",".join(symbols)
            data = await self.public_client.get_ticker(markets)

            self.logger.info(f"폴백으로 티커 조회 성공: {len(symbols)}개 심볼")
            return {
                "success": True,
                "data": data,
                "source": "fallback_rest_api",
                "symbols": symbols
            }

        except Exception as e:
            self.logger.error(f"티커 폴백 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "source": "fallback_rest_api"
            }

    async def _get_candles_fallback(self, symbols: List[str], interval: str,
                                  count: int, to: Optional[str] = None) -> Dict[str, Any]:
        """캔들 폴백 구현"""
        try:
            results = []

            for symbol in symbols:
                if interval.endswith('m'):
                    unit = int(interval[:-1])
                    data = await self.public_client.get_candles_minutes(
                        symbol, unit=unit, count=count, to=to
                    )
                elif interval == '1d':
                    data = await self.public_client.get_candles_days(
                        symbol, count=count, to=to
                    )
                elif interval == '1w':
                    data = await self.public_client.get_candles_weeks(
                        symbol, count=count, to=to
                    )
                else:
                    raise ValueError(f"지원하지 않는 간격: {interval}")

                results.extend(data)

            self.logger.info(f"폴백으로 캔들 조회 성공: {len(symbols)}개 심볼, {interval}, {count}개")
            return {
                "success": True,
                "data": results,
                "source": "fallback_rest_api",
                "symbols": symbols,
                "interval": interval,
                "count": count
            }

        except Exception as e:
            self.logger.error(f"캔들 폴백 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "source": "fallback_rest_api"
            }

    async def _get_trades_fallback(self, symbols: List[str], count: int) -> Dict[str, Any]:
        """체결 폴백 구현"""
        try:
            results = []

            for symbol in symbols:
                data = await self.public_client.get_ticks(symbol, count=count)
                results.extend(data)

            self.logger.info(f"폴백으로 체결 조회 성공: {len(symbols)}개 심볼, {count}개")
            return {
                "success": True,
                "data": results,
                "source": "fallback_rest_api",
                "symbols": symbols,
                "count": count
            }

        except Exception as e:
            self.logger.error(f"체결 폴백 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "source": "fallback_rest_api"
            }

    def _record_success(self):
        """성공 기록"""
        self.metrics.smart_router_success_count += 1
        self.metrics.last_success_time = datetime.now()

    def _record_failure(self):
        """실패 기록"""
        self.metrics.smart_router_failure_count += 1
        self.metrics.last_failure_time = datetime.now()

    async def _check_fallback_trigger(self):
        """폴백 트리거 조건 확인"""
        should_fallback = False

        # 조건 1: 연속 실패 횟수 초과
        if self.metrics.smart_router_failure_count >= self.max_failures:
            should_fallback = True
            reason = f"연속 실패 {self.metrics.smart_router_failure_count}회 초과"

        # 조건 2: 장시간 성공 없음
        if self.metrics.last_success_time:
            time_since_success = (datetime.now() - self.metrics.last_success_time).seconds
            if time_since_success > self.failure_timeout:
                should_fallback = True
                reason = f"마지막 성공 후 {time_since_success}초 경과"

        if should_fallback and self.smart_router_available:
            await self._activate_fallback(reason)

    async def _activate_fallback(self, reason: str):
        """폴백 모드 활성화"""
        self.smart_router_available = False
        self.metrics.current_mode = "fallback"
        self.metrics.fallback_activation_count += 1

        self.logger.warning(f"🚨 폴백 모드 활성화: {reason}")

        # 실시간 데이터 폴백 설정
        try:
            await self.websocket_client.connect()
            self.logger.info("실시간 폴백 WebSocket 연결 완료")
        except Exception as e:
            self.logger.error(f"실시간 폴백 설정 실패: {e}")

    async def _health_monitor(self):
        """주기적 상태 모니터링"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)

                # 폴백 모드에서 복구 시도
                if not self.smart_router_available and self.smart_router:
                    await self._try_recovery()

                # 지표 로깅
                await self._log_metrics()

            except Exception as e:
                self.logger.error(f"상태 모니터링 오류: {e}")

    async def _try_recovery(self):
        """스마트 라우터 복구 시도"""
        try:
            test_result = await self.smart_router.get_ticker(["KRW-BTC"])
            if test_result.get('success'):
                self.smart_router_available = True
                self.metrics.current_mode = "smart_router"
                self.metrics.smart_router_failure_count = 0  # 실패 카운터 리셋
                self._record_success()

                self.logger.info("✅ 스마트 라우터 복구 완료")

                # WebSocket 정리
                try:
                    await self.websocket_client.disconnect()
                except:
                    pass

        except Exception as e:
            self.logger.debug(f"스마트 라우터 복구 시도 실패: {e}")

    async def _log_metrics(self):
        """지표 로깅"""
        self.logger.info(
            f"📊 폴백 시스템 지표 - "
            f"모드: {self.metrics.current_mode}, "
            f"성공: {self.metrics.smart_router_success_count}, "
            f"실패: {self.metrics.smart_router_failure_count}, "
            f"폴백 활성화: {self.metrics.fallback_activation_count}회"
        )

    async def cleanup(self):
        """리소스 정리"""
        try:
            if self.smart_router:
                await self.smart_router.cleanup_resources()
        except:
            pass

        try:
            await self.websocket_client.disconnect()
        except:
            pass

        self.logger.info("폴백 시스템 리소스 정리 완료")


# 사용 예시
async def main():
    """폴백 시스템 사용 예시"""
    fallback_system = MarketDataFallbackSystem()

    try:
        await fallback_system.initialize()

        # 정상 사용 (자동 폴백 지원)
        ticker_data = await fallback_system.get_ticker(["KRW-BTC", "KRW-ETH"])
        print(f"티커 조회: {ticker_data.get('source')}")

        candle_data = await fallback_system.get_candles(
            ["KRW-BTC"], interval="5m", count=5
        )
        print(f"캔들 조회: {candle_data.get('source')}")

    finally:
        await fallback_system.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
