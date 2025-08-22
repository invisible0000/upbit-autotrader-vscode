"""
스마트 라우터 V2.0 메인 시스템 통합 어댑터

기존 시스템과 스마트 라우터를 연결하는 어댑터 패턴 구현으로
하위 호환성을 보장하면서 새로운 기능을 점진적으로 도입합니다.
"""

import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.smart_router import (
    SmartRouter, get_smart_router, initialize_smart_router
)
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.models import (
    DataRequest, DataType, RealtimePriority
)

logger = create_component_logger("SmartRouterAdapter")


class SmartRouterMainAdapter:
    """
    스마트 라우터 메인 시스템 통합 어댑터

    기존 시스템의 마켓 데이터 요청을 스마트 라우터로 라우팅하여
    성능과 안정성을 향상시키면서 하위 호환성을 보장합니다.
    """

    def __init__(self, enable_smart_routing: bool = True):
        """어댑터 초기화

        Args:
            enable_smart_routing: 스마트 라우팅 활성화 여부 (기본: True)
        """
        self.enable_smart_routing = enable_smart_routing
        self.smart_router: Optional[SmartRouter] = None
        self.is_initialized = False

        logger.info(f"SmartRouterMainAdapter 초기화 - 스마트 라우팅: {'활성화' if enable_smart_routing else '비활성화'}")

    async def initialize(self) -> bool:
        """어댑터 초기화"""
        if self.is_initialized:
            return True

        if not self.enable_smart_routing:
            logger.info("스마트 라우팅이 비활성화됨 - 기존 방식 사용")
            self.is_initialized = True
            return True

        try:
            logger.info("스마트 라우터 초기화 시작...")
            self.smart_router = await initialize_smart_router()
            self.is_initialized = True
            logger.info("✅ 스마트 라우터 어댑터 초기화 완료")
            return True

        except Exception as e:
            logger.error(f"❌ 스마트 라우터 초기화 실패: {e}")
            self.enable_smart_routing = False
            self.is_initialized = True
            return False

    async def get_ticker_data(
        self,
        symbols: Union[str, List[str]],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """현재가 데이터 조회 (메인 시스템 호환 인터페이스)

        Args:
            symbols: 심볼 또는 심볼 리스트
            use_cache: 캐시 사용 여부

        Returns:
            현재가 데이터 (기존 형식 호환)
        """
        if not self.is_initialized:
            await self.initialize()

        # 심볼 정규화
        symbol_list = [symbols] if isinstance(symbols, str) else symbols

        if self.enable_smart_routing and self.smart_router:
            try:
                result = await self.smart_router.get_ticker(
                    symbol_list,
                    RealtimePriority.MEDIUM
                )

                if result["success"]:
                    return self._convert_to_legacy_format(result, "ticker")
                else:
                    logger.warning(f"스마트 라우터 티커 요청 실패: {result.get('error', 'Unknown')}")

            except Exception as e:
                logger.error(f"스마트 라우터 티커 요청 오류: {e}")

        # 폴백: 기존 방식 또는 에러 반환
        return await self._fallback_ticker_request(symbol_list)

    async def get_candle_data(
        self,
        symbols: Union[str, List[str]],
        interval: str = "1m",
        count: int = 100,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """캔들 데이터 조회 (메인 시스템 호환 인터페이스)

        Args:
            symbols: 심볼 또는 심볼 리스트
            interval: 캔들 간격 (1m, 5m, 15m, 1h, 1d 등)
            count: 조회할 캔들 개수
            use_cache: 캐시 사용 여부

        Returns:
            캔들 데이터 (기존 형식 호환)
        """
        if not self.is_initialized:
            await self.initialize()

        # 심볼 정규화
        symbol_list = [symbols] if isinstance(symbols, str) else symbols

        if self.enable_smart_routing and self.smart_router:
            try:
                result = await self.smart_router.get_candles(
                    symbol_list,
                    interval,
                    count
                )

                if result["success"]:
                    return self._convert_to_legacy_format(result, "candles")
                else:
                    logger.warning(f"스마트 라우터 캔들 요청 실패: {result.get('error', 'Unknown')}")

            except Exception as e:
                logger.error(f"스마트 라우터 캔들 요청 오류: {e}")

        # 폴백: 기존 방식 또는 에러 반환
        return await self._fallback_candle_request(symbol_list, interval, count)

    async def get_trades(
        self,
        symbols: Union[str, List[str]],
        count: int = 100,
        realtime_priority: RealtimePriority = RealtimePriority.MEDIUM
    ) -> Dict[str, Any]:
        """체결 데이터 조회 (메인 시스템 호환 인터페이스)

        Args:
            symbols: 심볼 또는 심볼 리스트
            count: 조회할 체결 개수 (최대 500개)
            realtime_priority: 실시간 우선순위

        Returns:
            체결 데이터 (기존 형식 호환)
        """
        if not self.is_initialized:
            await self.initialize()

        # 심볼 정규화
        symbol_list = [symbols] if isinstance(symbols, str) else symbols

        if self.enable_smart_routing and self.smart_router:
            try:
                result = await self.smart_router.get_trades(
                    symbol_list,
                    count=min(count, 500),  # API 최대 제한
                    realtime_priority=realtime_priority
                )

                if result["success"]:
                    return self._convert_to_legacy_format(result, "trades")
                else:
                    logger.warning(f"스마트 라우터 체결 요청 실패: {result.get('error', 'Unknown')}")

            except Exception as e:
                logger.error(f"스마트 라우터 체결 요청 오류: {e}")

        # 폴백: 기존 방식 또는 에러 반환
        return await self._fallback_trades_request(symbol_list, count)

    async def get_orderbook_data(
        self,
        symbols: Union[str, List[str]],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """호가 데이터 조회 (메인 시스템 호환 인터페이스)

        Args:
            symbols: 심볼 또는 심볼 리스트
            use_cache: 캐시 사용 여부

        Returns:
            호가 데이터 (기존 형식 호환)
        """
        if not self.is_initialized:
            await self.initialize()

        # 심볼 정규화
        symbol_list = [symbols] if isinstance(symbols, str) else symbols

        if self.enable_smart_routing and self.smart_router:
            try:
                result = await self.smart_router.get_orderbook(
                    symbol_list,
                    RealtimePriority.HIGH
                )

                if result["success"]:
                    return self._convert_to_legacy_format(result, "orderbook")
                else:
                    logger.warning(f"스마트 라우터 호가 요청 실패: {result.get('error', 'Unknown')}")

            except Exception as e:
                logger.error(f"스마트 라우터 호가 요청 오류: {e}")

        # 폴백: 기존 방식 또는 에러 반환
        return await self._fallback_orderbook_request(symbol_list)

    def _convert_to_legacy_format(self, smart_router_result: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """스마트 라우터 결과를 기존 시스템 형식으로 변환"""
        try:
            data = smart_router_result.get("data", {})
            metadata = smart_router_result.get("metadata", {})

            # 기존 시스템 형식으로 변환
            legacy_result = {
                "success": True,
                "data": data,
                "timestamp": datetime.now().isoformat(),
                "source": metadata.get("channel", "unknown"),
                "response_time_ms": metadata.get("response_time_ms", 0)
            }

            # 데이터 타입별 추가 처리
            if data_type == "candles" and isinstance(data, list):
                # 캔들 데이터의 경우 pandas DataFrame 형식으로 변환할 수도 있음
                legacy_result["candle_count"] = len(data)
            elif data_type == "ticker" and isinstance(data, list) and len(data) > 0:
                # 단일 심볼 요청의 경우 첫 번째 항목만 반환
                if len(data) == 1:
                    legacy_result["data"] = data[0]

            return legacy_result

        except Exception as e:
            logger.error(f"레거시 형식 변환 실패 ({data_type}): {e}")
            return {
                "success": False,
                "error": f"Format conversion failed: {str(e)}",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }

    async def _fallback_ticker_request(self, symbols: List[str]) -> Dict[str, Any]:
        """폴백 티커 요청 (기존 방식)"""
        logger.warning("폴백 티커 요청 - 기존 API 클라이언트 직접 사용")
        # TODO: 기존 UpbitPublicClient 직접 사용
        return {
            "success": False,
            "error": "Fallback not implemented",
            "data": None,
            "timestamp": datetime.now().isoformat(),
            "source": "fallback"
        }

    async def _fallback_candle_request(self, symbols: List[str], interval: str, count: int) -> Dict[str, Any]:
        """폴백 캔들 요청 (기존 방식)"""
        logger.warning("폴백 캔들 요청 - 기존 API 클라이언트 직접 사용")
        # TODO: 기존 UpbitPublicClient 직접 사용
        return {
            "success": False,
            "error": "Fallback not implemented",
            "data": None,
            "timestamp": datetime.now().isoformat(),
            "source": "fallback"
        }

    async def _fallback_trades_request(self, symbols: List[str], count: int) -> Dict[str, Any]:
        """폴백 체결 요청 (기존 방식)"""
        logger.warning("폴백 체결 요청 - 기존 API 클라이언트 직접 사용")
        # TODO: 기존 UpbitPublicClient 직접 사용
        return {
            "success": False,
            "error": "Fallback not implemented",
            "data": None,
            "timestamp": datetime.now().isoformat(),
            "source": "fallback"
        }

    async def _fallback_orderbook_request(self, symbols: List[str]) -> Dict[str, Any]:
        """폴백 호가 요청 (기존 방식)"""
        logger.warning("폴백 호가 요청 - 기존 API 클라이언트 직접 사용")
        # TODO: 기존 UpbitPublicClient 직접 사용
        return {
            "success": False,
            "error": "Fallback not implemented",
            "data": None,
            "timestamp": datetime.now().isoformat(),
            "source": "fallback"
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """성능 요약 조회"""
        if self.enable_smart_routing and self.smart_router:
            return self.smart_router.get_performance_summary()
        else:
            return {
                "smart_routing_enabled": False,
                "adapter_initialized": self.is_initialized,
                "message": "스마트 라우팅이 비활성화됨"
            }

    async def cleanup(self) -> None:
        """리소스 정리"""
        if self.smart_router and hasattr(self.smart_router, 'websocket_client'):
            if self.smart_router.websocket_client and self.smart_router.websocket_client.is_connected:
                await self.smart_router.websocket_client.disconnect()

        logger.info("SmartRouterMainAdapter 리소스 정리 완료")


# 전역 어댑터 인스턴스 (싱글톤 패턴)
_global_adapter: Optional[SmartRouterMainAdapter] = None


def get_market_data_adapter(enable_smart_routing: bool = True) -> SmartRouterMainAdapter:
    """전역 마켓 데이터 어댑터 인스턴스 조회"""
    global _global_adapter

    if _global_adapter is None:
        _global_adapter = SmartRouterMainAdapter(enable_smart_routing)

    return _global_adapter


async def initialize_market_data_adapter(enable_smart_routing: bool = True) -> SmartRouterMainAdapter:
    """마켓 데이터 어댑터 초기화 및 설정"""
    adapter = get_market_data_adapter(enable_smart_routing)
    await adapter.initialize()
    return adapter


# 편의 함수들 (기존 시스템 호환용)
async def get_ticker(symbols: Union[str, List[str]]) -> Dict[str, Any]:
    """현재가 조회 편의 함수"""
    adapter = get_market_data_adapter()
    return await adapter.get_ticker_data(symbols)


async def get_candles(symbols: Union[str, List[str]], interval: str = "1m", count: int = 100) -> Dict[str, Any]:
    """캔들 조회 편의 함수"""
    adapter = get_market_data_adapter()
    return await adapter.get_candle_data(symbols, interval, count)


async def get_orderbook(symbols: Union[str, List[str]]) -> Dict[str, Any]:
    """호가 조회 편의 함수"""
    adapter = get_market_data_adapter()
    return await adapter.get_orderbook_data(symbols)
