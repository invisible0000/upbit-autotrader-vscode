"""
업비트 데이터 제공자 서비스 (리팩터링 버전)

업비트 API를 통해 시장 데이터를 수집하는 서비스입니다.
Facade 패턴을 사용하여 여러 서비스 컴포넌트를 조율합니다.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_client import UpbitClient

from .data_converter import DataConverter
from .cache_manager import CacheManager
from .websocket_manager import WebSocketManager
from .rest_api_manager import RestApiManager
from .metrics_collector import MetricsCollector

logger = create_component_logger("UpbitDataProvider")


class UpbitDataProvider:
    """
    업비트 데이터 제공자 서비스 (리팩터링 버전)

    Facade 패턴을 사용하여 다음 컴포넌트들을 조율:
    - DataConverter: 데이터 변환 로직
    - CacheManager: 캐시 관리 로직
    - WebSocketManager: WebSocket 연결 관리
    - RestApiManager: REST API 호출 관리
    - MetricsCollector: 성능 메트릭 수집
    """

    def __init__(self):
        """데이터 제공자 초기화"""
        logger.info("UpbitDataProvider 초기화 시작")

        # 핵심 API 클라이언트
        self.upbit_client = UpbitClient()

        # 서비스 컴포넌트들 초기화
        self.data_converter = DataConverter()
        self.cache_manager = CacheManager(max_size=10000, cleanup_interval=60.0)
        self.websocket_manager = WebSocketManager()
        self.rest_api_manager = RestApiManager(self.upbit_client)
        self.metrics_collector = MetricsCollector()

        # 캐시 시스템 (CacheManager에서 관리)
        self.cache = self.cache_manager.cache

        # 연결 상태
        self.is_initialized = False

        logger.info("UpbitDataProvider 초기화 완료")

    async def start(self) -> None:
        """데이터 제공자 시작"""
        if self.is_initialized:
            logger.debug("이미 시작됨")
            return

        try:
            logger.info("데이터 제공자 시작 중...")

            # 캐시 시스템 시작
            await self.cache_manager.start()

            # WebSocket 연결 초기화 (선택적)
            # await self.websocket_manager.connect()

            self.is_initialized = True
            logger.info("✅ 데이터 제공자 시작 완료")

        except Exception as e:
            logger.error(f"❌ 데이터 제공자 시작 실패: {e}")
            raise

    async def stop(self) -> None:
        """데이터 제공자 정지"""
        if not self.is_initialized:
            logger.debug("이미 정지됨")
            return

        try:
            logger.info("데이터 제공자 정지 중...")

            # WebSocket 연결 해제
            await self.websocket_manager.disconnect()

            # 캐시 시스템 정지
            await self.cache_manager.stop()

            self.is_initialized = False
            logger.info("✅ 데이터 제공자 정지 완료")

        except Exception as e:
            logger.warning(f"정지 중 오류: {e}")

    async def initialize(self) -> bool:
        """데이터 제공자 초기화 (호환성 유지)

        Returns:
            초기화 성공 여부
        """
        await self.start()
        return self.is_initialized

    async def get_ticker_data(
        self,
        symbols: List[str],
        tier: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """티커 데이터 조회 (통합 인터페이스)

        Args:
            symbols: 조회할 심볼 리스트
            tier: 요청된 Tier (HOT_CACHE, LIVE_SUBSCRIPTION, etc.)
            context: 요청 컨텍스트

        Returns:
            조회된 티커 데이터
        """
        start_time = time.time()

        try:
            logger.info(f"티커 데이터 조회 시작: {tier} - {len(symbols)}개 심볼")

            # Tier별 데이터 조회 라우팅
            if tier == "HOT_CACHE":
                result = await self._get_ticker_hot_cache(symbols)
            elif tier == "LIVE_SUBSCRIPTION":
                result = await self._get_ticker_live_subscription(symbols)
            elif tier == "BATCH_SNAPSHOT":
                result = await self._get_ticker_batch_snapshot(symbols)
            elif tier == "WARM_CACHE_REST":
                result = await self._get_ticker_warm_cache_rest(symbols)
            elif tier == "COLD_REST":
                result = await self._get_ticker_cold_rest(symbols)
            else:
                raise ValueError(f"지원하지 않는 Tier: {tier}")

            # 메트릭 기록
            response_time_ms = (time.time() - start_time) * 1000
            success = result.get('success', False)
            self.metrics_collector.record_request(
                tier=tier,
                response_time_ms=response_time_ms,
                success=success,
                symbols_count=len(symbols)
            )

            logger.info(f"티커 데이터 조회 완료: {tier} - {response_time_ms:.1f}ms")
            return result

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"티커 데이터 조회 실패: {tier} - {e}")

            # 메트릭 기록 (실패)
            self.metrics_collector.record_request(
                tier=tier,
                response_time_ms=response_time_ms,
                success=False,
                symbols_count=len(symbols),
                error_type=type(e).__name__
            )

            # 에러 응답 반환
            return {
                'success': False,
                'error': str(e),
                'tier': tier,
                'symbols': symbols,
                'response_time_ms': response_time_ms
            }

    async def _get_ticker_hot_cache(self, symbols: List[str]) -> Dict[str, Any]:
        """HOT_CACHE Tier 데이터 조회"""
        logger.debug(f"HOT_CACHE 조회: {len(symbols)}개 심볼")

        # 캐시에서 데이터 조회
        result = self.cache_manager.get_ticker_data(symbols)

        if result['success'] and result['hit_rate'] > 0.8:  # 80% 이상 히트
            # 캐시 히트 기록
            for symbol in result['data']:
                self.metrics_collector.record_cache_hit("HOT_CACHE")

            return {
                'success': True,
                'data': result['data'],
                'source': 'hot_cache',
                'hit_rate': result['hit_rate'],
                'response_time_ms': result.get('response_time_ms', 0.0)
            }
        else:
            # 캐시 미스 기록
            for symbol in symbols:
                if symbol not in result.get('data', {}):
                    self.metrics_collector.record_cache_miss("HOT_CACHE")

            return {
                'success': False,
                'error': 'cache_miss',
                'hit_rate': result.get('hit_rate', 0.0)
            }

    async def _get_ticker_live_subscription(self, symbols: List[str]) -> Dict[str, Any]:
        """LIVE_SUBSCRIPTION Tier 데이터 조회"""
        logger.debug(f"LIVE_SUBSCRIPTION 조회: {len(symbols)}개 심볼")

        # WebSocket 실시간 구독
        result = await self.websocket_manager.subscribe_ticker_live(symbols, timeout=1.0)
        self.metrics_collector.record_websocket_connection()

        if result['success_rate'] >= 0.8:  # 80% 이상 성공
            # 데이터 변환
            converted_data = {}
            for symbol, raw_data in result['collected_data'].items():
                converted_data[symbol] = self.data_converter.convert_websocket_ticker_data(
                    raw_data['data']
                )

            # 캐시에 저장
            self.cache_manager.store_ticker_data(converted_data)

            return {
                'success': True,
                'data': converted_data,
                'source': 'websocket_live',
                'success_rate': result['success_rate'],
                'collection_time_ms': result['collection_time_ms']
            }
        else:
            return {
                'success': False,
                'error': 'websocket_subscription_failed',
                'success_rate': result['success_rate']
            }

    async def _get_ticker_batch_snapshot(self, symbols: List[str]) -> Dict[str, Any]:
        """BATCH_SNAPSHOT Tier 데이터 조회"""
        logger.debug(f"BATCH_SNAPSHOT 조회: {len(symbols)}개 심볼")

        # WebSocket 배치 구독
        result = await self.websocket_manager.subscribe_ticker_batch(symbols, timeout=2.0)
        self.metrics_collector.record_websocket_connection()

        if result['success_rate'] >= 0.7:  # 70% 이상 성공
            # 데이터 변환
            converted_data = {}
            for symbol, raw_data in result['collected_data'].items():
                converted_data[symbol] = self.data_converter.convert_websocket_ticker_data(
                    raw_data['data']
                )

            # 캐시에 저장
            self.cache_manager.store_ticker_data(converted_data)

            return {
                'success': True,
                'data': converted_data,
                'source': 'websocket_batch',
                'success_rate': result['success_rate'],
                'collection_time_ms': result['collection_time_ms']
            }
        else:
            return {
                'success': False,
                'error': 'batch_snapshot_failed',
                'success_rate': result['success_rate']
            }

    async def _get_ticker_warm_cache_rest(self, symbols: List[str]) -> Dict[str, Any]:
        """WARM_CACHE_REST Tier 데이터 조회"""
        logger.debug(f"WARM_CACHE_REST 조회: {len(symbols)}개 심볼")

        # REST API 호출 (Warm 모드)
        result = await self.rest_api_manager.get_ticker_data_warm(symbols, enable_retry=True)
        self.metrics_collector.record_rest_api_call()

        if result['success']:
            # 데이터 변환
            converted_data = {}
            for symbol, raw_data in result['collected_data'].items():
                converted_data[symbol] = self.data_converter.convert_ticker_response(
                    raw_data['data']
                )

            # 캐시에 저장 (Warm 전략)
            self.cache_manager.store_ticker_data(converted_data)

            return {
                'success': True,
                'data': converted_data,
                'source': 'rest_warm',
                'success_rate': result['success_rate'],
                'response_time_ms': result['response_time_ms']
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'rest_warm_failed'),
                'response_time_ms': result.get('response_time_ms', 0.0)
            }

    async def _get_ticker_cold_rest(self, symbols: List[str]) -> Dict[str, Any]:
        """COLD_REST Tier 데이터 조회"""
        logger.debug(f"COLD_REST 조회: {len(symbols)}개 심볼")

        # REST API 호출 (Cold 모드)
        result = await self.rest_api_manager.get_ticker_data_cold(symbols, enable_retry=True)
        self.metrics_collector.record_rest_api_call()

        if result['success']:
            # 데이터 변환
            converted_data = {}
            for symbol, raw_data in result['collected_data'].items():
                converted_data[symbol] = self.data_converter.convert_ticker_response(
                    raw_data['data']
                )

            # 캐시에 저장 (Cold 전략)
            self.cache_manager.store_ticker_data(converted_data)

            return {
                'success': True,
                'data': converted_data,
                'source': 'rest_cold',
                'success_rate': result['success_rate'],
                'response_time_ms': result['response_time_ms']
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'rest_cold_failed'),
                'response_time_ms': result.get('response_time_ms', 0.0)
            }

    async def get_candle_data(
        self,
        symbols: List[str],
        interval: str = "1m",
        count: int = 100,
        tier: str = "COLD_REST"
    ) -> Dict[str, Any]:
        """캔들 데이터 조회"""
        try:
            result = await self.rest_api_manager.get_candles(symbols, interval, count)

            # 데이터 변환 및 캐시 저장
            if result.get('success'):
                converted_data = {}
                for symbol, raw_data in result['collected_data'].items():
                    converted_data[symbol] = self.data_converter.convert_candle_response(
                        raw_data['data']
                    )

                # 캐시에 저장
                for symbol, data in converted_data.items():
                    cache_key = f"candle:{symbol}:{interval}"
                    self.cache_manager.set_cache(cache_key, data)

                return {
                    'success': True,
                    'data': converted_data,
                    'source': 'rest_api'
                }
            else:
                return result

        except Exception as e:
            logger.error(f"캔들 데이터 조회 실패: {e}")
            return {'success': False, 'error': str(e)}

    async def get_orderbook_data(self, symbols: List[str], tier: str = "COLD_REST") -> Dict[str, Any]:
        """호가 데이터 조회"""
        try:
            result = await self.rest_api_manager.get_orderbook(symbols)

            # 데이터 변환 및 캐시 저장
            if result.get('success'):
                converted_data = {}
                for symbol, raw_data in result['collected_data'].items():
                    converted_data[symbol] = self.data_converter.convert_orderbook_response(
                        raw_data['data']
                    )

                # 캐시에 저장
                for symbol, data in converted_data.items():
                    self.cache_manager.set_cache(f"orderbook:{symbol}", data)

                return {
                    'success': True,
                    'data': converted_data,
                    'source': 'rest_api'
                }
            else:
                return result

        except Exception as e:
            logger.error(f"호가 데이터 조회 실패: {e}")
            return {'success': False, 'error': str(e)}

    async def get_trade_data(
        self,
        symbols: List[str],
        count: int = 100,
        tier: str = "COLD_REST"
    ) -> Dict[str, Any]:
        """체결 데이터 조회"""
        try:
            result = await self.rest_api_manager.get_trades(symbols, count)

            # 데이터 변환 및 캐시 저장
            if result.get('success'):
                converted_data = {}
                for symbol, raw_data in result['collected_data'].items():
                    converted_data[symbol] = self.data_converter.convert_trade_response(
                        raw_data['data']
                    )

                # 캐시에 저장
                for symbol, data in converted_data.items():
                    self.cache_manager.set_cache(f"trade:{symbol}", data)

                return {
                    'success': True,
                    'data': converted_data,
                    'source': 'rest_api'
                }
            else:
                return result

        except Exception as e:
            logger.error(f"체결 데이터 조회 실패: {e}")
            return {'success': False, 'error': str(e)}

    def get_performance_summary(self) -> Dict[str, Any]:
        """성능 요약 조회

        Returns:
            전체 성능 요약 정보
        """
        return {
            'system_overview': self.metrics_collector.get_system_overview(),
            'tier_performance': self.metrics_collector.get_tier_performance_summary(),
            'cache_status': self.cache_manager.get_cache_stats(),
            'websocket_status': self.websocket_manager.get_connection_status(),
            'rest_api_metrics': self.rest_api_manager.get_performance_metrics()
        }

    def reset_performance_metrics(self) -> None:
        """성능 메트릭 초기화"""
        logger.info("성능 메트릭 초기화")

        self.metrics_collector.reset_metrics()
        self.websocket_manager.reset_metrics()
        self.rest_api_manager.reset_metrics()
        self.cache_manager.reset_cache_stats()

        logger.info("✅ 성능 메트릭 초기화 완료")

    # 편의용 동기 메서드들 (RestApiManager 호출)
    def get_candles(self, symbols: List[str], interval: str, count: int) -> Dict[str, Any]:
        """동기 캔들 데이터 조회 (RestApiManager 사용)"""
        return asyncio.run(self.rest_api_manager.get_candles(symbols, interval, count))

    def get_orderbook(self, symbols: List[str]) -> Dict[str, Any]:
        """동기 호가 데이터 조회 (RestApiManager 사용)"""
        return asyncio.run(self.rest_api_manager.get_orderbook(symbols))

    def get_trades(self, symbols: List[str], count: int = 10) -> Dict[str, Any]:
        """동기 거래 데이터 조회 (RestApiManager 사용)"""
        return asyncio.run(self.rest_api_manager.get_trades(symbols, count))
