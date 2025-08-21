"""
WebSocket 연결 관리 서비스

업비트 WebSocket 연결과 실시간 데이터 구독을 관리하는 서비스입니다.
"""

import asyncio
from typing import Dict, List, Any, Optional, Set
import time

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
    UpbitWebSocketQuotationClient, WebSocketDataType
)
from ..core.rate_limit_manager import get_global_rate_limiter, RateLimitType

logger = create_component_logger("WebSocketManager")


class WebSocketManager:
    """WebSocket 연결 관리 서비스

    LIVE_SUBSCRIPTION과 BATCH_SNAPSHOT Tier를 위한 WebSocket 연결을 관리합니다.
    """

    def __init__(self):
        """WebSocket 관리자 초기화"""
        logger.info("WebSocketManager 초기화 시작")

        self.ws_client = UpbitWebSocketQuotationClient()
        self.is_connected = False
        self.connection_lock = asyncio.Lock()

        # 구독 관리
        self.active_subscriptions: Set[str] = set()
        self.subscription_callbacks: Dict[str, List] = {}

        # 중앙 Rate Limit Manager 사용
        self.rate_limiter = get_global_rate_limiter()

        # 성능 메트릭 (Rate Limit 추적 제거)
        self.metrics = {
            'connection_count': 0,
            'reconnection_count': 0,
            'subscription_count': 0,
            'message_count': 0,
            'error_count': 0,
            'avg_latency_ms': 0.0
        }

        logger.info("WebSocketManager 초기화 완료")

    async def connect(self) -> bool:
        """WebSocket 연결 설정

        Returns:
            연결 성공 여부
        """
        async with self.connection_lock:
            if self.is_connected:
                logger.debug("이미 WebSocket 연결됨")
                return True

            try:
                logger.info("WebSocket 연결 시도...")

                # Rate Limit 체크 (중앙 RateLimitManager 사용)
                await self.rate_limiter.wait_for_slot(RateLimitType.WEBSOCKET_CONNECT)

                # 실제 연결
                success = await self.ws_client.connect()

                if success:
                    self.is_connected = True
                    self.metrics['connection_count'] += 1
                    # 중앙 Rate Limit Manager에 연결 요청 기록
                    await self.rate_limiter.record_request(RateLimitType.WEBSOCKET_CONNECT)
                    logger.info("✅ WebSocket 연결 성공")
                else:
                    logger.error("❌ WebSocket 연결 실패")

                return success

            except Exception as e:
                logger.error(f"❌ WebSocket 연결 오류: {e}")
                self.metrics['error_count'] += 1
                self.is_connected = False
                return False

    async def disconnect(self) -> None:
        """WebSocket 연결 해제"""
        async with self.connection_lock:
            if not self.is_connected:
                logger.debug("WebSocket이 이미 연결 해제됨")
                return

            try:
                logger.info("WebSocket 연결 해제 중...")

                # 모든 구독 해제
                await self._unsubscribe_all()

                # 연결 해제
                await self.ws_client.disconnect()
                self.is_connected = False

                logger.info("✅ WebSocket 연결 해제 완료")

            except Exception as e:
                logger.warning(f"WebSocket 연결 해제 중 오류: {e}")
                self.is_connected = False

    async def subscribe_ticker_live(self, symbols: List[str], timeout: float = 1.0) -> Dict[str, Any]:
        """실시간 티커 구독 (LIVE_SUBSCRIPTION Tier)

        Args:
            symbols: 구독할 심볼 리스트
            timeout: 데이터 수집 타임아웃 (초)

        Returns:
            수집된 티커 데이터
        """
        logger.info(f"실시간 티커 구독: {len(symbols)}개 심볼")

        if not await self._ensure_connection():
            raise Exception("WebSocket 연결 실패")

        try:
            # Rate Limit 체크 (중앙 RateLimitManager 사용)
            await self.rate_limiter.wait_for_slot(RateLimitType.WEBSOCKET_MESSAGE)

            # 구독 요청
            success = await self.ws_client.subscribe_ticker(symbols)
            if not success:
                raise Exception("티커 구독 실패")

            # 구독 정보 업데이트
            self.active_subscriptions.update(symbols)
            self.metrics['subscription_count'] += len(symbols)

            # 중앙 Rate Limit Manager에 메시지 요청 기록
            await self.rate_limiter.record_request(RateLimitType.WEBSOCKET_MESSAGE)

            # 실시간 데이터 수집
            return await self._collect_ticker_data(symbols, timeout, 'live')

        except Exception as e:
            logger.error(f"실시간 티커 구독 실패: {e}")
            self.metrics['error_count'] += 1
            raise

    async def subscribe_ticker_batch(self, symbols: List[str], timeout: float = 2.0) -> Dict[str, Any]:
        """배치 티커 구독 (BATCH_SNAPSHOT Tier)

        Args:
            symbols: 구독할 심볼 리스트
            timeout: 데이터 수집 타임아웃 (초)

        Returns:
            수집된 티커 데이터
        """
        logger.info(f"배치 티커 구독: {len(symbols)}개 심볼")

        if not await self._ensure_connection():
            raise Exception("WebSocket 연결 실패")

        try:
            # Rate Limit 체크 (중앙 RateLimitManager 사용)
            await self.rate_limiter.wait_for_slot(RateLimitType.WEBSOCKET_MESSAGE)

            # 구독 요청
            success = await self.ws_client.subscribe_ticker(symbols)
            if not success:
                raise Exception("배치 티커 구독 실패")

            # 구독 정보 업데이트
            self.active_subscriptions.update(symbols)
            self.metrics['subscription_count'] += len(symbols)

            # 배치 데이터 수집 (더 긴 타임아웃)
            return await self._collect_ticker_data(symbols, timeout, 'batch')

        except Exception as e:
            logger.error(f"배치 티커 구독 실패: {e}")
            self.metrics['error_count'] += 1
            raise

    async def _ensure_connection(self) -> bool:
        """WebSocket 연결 보장"""
        if not self.is_connected:
            return await self.connect()
        return True

    async def _collect_ticker_data(
        self,
        symbols: List[str],
        timeout: float,
        source_type: str
    ) -> Dict[str, Any]:
        """티커 데이터 수집

        Args:
            symbols: 수집할 심볼 리스트
            timeout: 타임아웃 (초)
            source_type: 소스 타입 ('live' 또는 'batch')

        Returns:
            수집된 티커 데이터
        """
        collected_data = {}
        collected_symbols = set()
        start_time = time.time()

        logger.debug(f"데이터 수집 시작: {len(symbols)}개 심볼, {timeout}초 타임아웃")

        try:
            # WebSocket 메시지 수신 대기
            async for message in self.ws_client.listen():
                if message.type == WebSocketDataType.TICKER:
                    symbol = message.market

                    if symbol in symbols and symbol not in collected_symbols:
                        # 데이터 수집
                        collected_data[symbol] = {
                            'symbol': symbol,
                            'data': message.data,
                            'collected_at': time.time(),
                            'source': f'websocket_{source_type}'
                        }
                        collected_symbols.add(symbol)
                        self.metrics['message_count'] += 1

                        logger.debug(f"데이터 수집: {symbol} ({len(collected_symbols)}/{len(symbols)})")

                        # 모든 심볼 수집 완료
                        if len(collected_symbols) >= len(symbols):
                            break

                # 타임아웃 체크
                if time.time() - start_time > timeout:
                    logger.debug(f"데이터 수집 타임아웃: {len(collected_symbols)}/{len(symbols)}")
                    break

        except Exception as e:
            logger.warning(f"데이터 수집 중 오류: {e}")

        # 수집 통계
        collection_time = time.time() - start_time
        success_rate = len(collected_symbols) / len(symbols) if symbols else 0.0

        logger.info(f"데이터 수집 완료: {len(collected_symbols)}/{len(symbols)} "
                   f"({success_rate:.1%}), {collection_time:.3f}초")

        return {
            'collected_data': collected_data,
            'success_rate': success_rate,
            'collection_time_ms': collection_time * 1000,
            'symbols_collected': len(collected_symbols),
            'symbols_missing': [s for s in symbols if s not in collected_symbols]
        }

    async def _unsubscribe_all(self) -> None:
        """모든 구독 해제"""
        if self.active_subscriptions:
            logger.info(f"모든 구독 해제: {len(self.active_subscriptions)}개")

            try:
                # 구독 해제 로직 (WebSocket 클라이언트에 따라 구현)
                # 현재는 단순히 추적 정보만 정리
                self.active_subscriptions.clear()
                self.subscription_callbacks.clear()

            except Exception as e:
                logger.warning(f"구독 해제 중 오류: {e}")

    def get_connection_status(self) -> Dict[str, Any]:
        """연결 상태 조회

        Returns:
            상세한 연결 상태 정보
        """
        # 중앙 RateLimitManager에서 정보 가져오기
        rate_limit_stats = self.rate_limiter.get_status()

        return {
            'is_connected': self.is_connected,
            'active_subscriptions': len(self.active_subscriptions),
            'subscribed_symbols': list(self.active_subscriptions),
            'metrics': self.metrics.copy(),
            'rate_limit_status': {
                'websocket_message_limit_per_second': 5,  # 업비트 공식 제한
                'websocket_connect_limit_per_second': 5,  # 업비트 공식 제한
                'websocket_message_limit_per_minute': 100,  # 업비트 공식 제한
                'central_rate_limiter_status': 'active'  # 중앙 관리 중
            },
            'performance': {
                'avg_latency_ms': self.metrics['avg_latency_ms'],
                'error_rate': self.metrics['error_count'] / max(self.metrics['message_count'], 1),
                'connection_stability': self.metrics['connection_count'] / max(self.metrics['reconnection_count'] + 1, 1)
            }
        }

    def reset_metrics(self) -> None:
        """메트릭 초기화"""
        self.metrics = {
            'connection_count': 0,
            'reconnection_count': 0,
            'subscription_count': 0,
            'message_count': 0,
            'error_count': 0,
            'avg_latency_ms': 0.0
        }
        logger.info("WebSocket 메트릭 초기화 완료")
