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

        # Rate Limiting (업비트 WebSocket 제한)
        self.rate_limit_config = {
            'connect_per_second': 5,  # 초당 최대 5회 연결
            'message_per_second': 5,  # 초당 최대 5회 메시지
            'message_per_minute': 100  # 분당 최대 100회 메시지
        }

        # Rate Limit 추적
        self.request_timestamps = []
        self.last_request_time = 0.0

        # 성능 메트릭
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

                # Rate Limit 체크
                await self._wait_for_rate_limit('connect')

                # 실제 연결
                success = await self.ws_client.connect()

                if success:
                    self.is_connected = True
                    self.metrics['connection_count'] += 1
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
            # Rate Limit 체크
            await self._wait_for_rate_limit('message')

            # 구독 요청
            success = await self.ws_client.subscribe_ticker(symbols)
            if not success:
                raise Exception("티커 구독 실패")

            # 구독 정보 업데이트
            self.active_subscriptions.update(symbols)
            self.metrics['subscription_count'] += len(symbols)

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
            # Rate Limit 체크 (배치는 더 관대한 제한)
            await self._wait_for_rate_limit('message', margin_factor=0.5)

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

    async def _wait_for_rate_limit(self, limit_type: str, margin_factor: float = 1.0) -> None:
        """Rate Limit 대기

        Args:
            limit_type: 제한 타입 ('connect' 또는 'message')
            margin_factor: 안전 마진 계수 (1.0 = 100% 제한, 0.5 = 50% 제한)
        """
        current_time = time.time()

        if limit_type == 'connect':
            base_interval = 1.0 / self.rate_limit_config['connect_per_second']
        else:  # message
            base_interval = 1.0 / self.rate_limit_config['message_per_second']

        # 안전 마진 적용
        safe_interval = base_interval * margin_factor

        # 마지막 요청 이후 경과 시간
        time_elapsed = current_time - self.last_request_time

        if time_elapsed < safe_interval:
            wait_time = safe_interval - time_elapsed
            logger.debug(f"Rate Limit 대기: {wait_time:.3f}초")
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time()
        self.request_timestamps.append(self.last_request_time)

        # 1분 이상 된 타임스탬프 제거
        cutoff_time = current_time - 60.0
        self.request_timestamps = [t for t in self.request_timestamps if t > cutoff_time]

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
        current_time = time.time()
        recent_requests = len([t for t in self.request_timestamps if current_time - t < 60.0])

        return {
            'is_connected': self.is_connected,
            'active_subscriptions': len(self.active_subscriptions),
            'subscribed_symbols': list(self.active_subscriptions),
            'metrics': self.metrics.copy(),
            'rate_limit_status': {
                'requests_last_minute': recent_requests,
                'requests_per_minute_limit': self.rate_limit_config['message_per_minute'],
                'usage_percentage': (recent_requests / self.rate_limit_config['message_per_minute']) * 100
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
        self.request_timestamps.clear()
        logger.info("WebSocket 메트릭 초기화 완료")
