"""
업비트 WebSocket Private 클라이언트 v2.0 - 메시지 루프 시스템 통합

🎯 주요 개선:
- Public Client와 동일한 메시지 루프 시스템 적용
- Private 전용 구독 관리자 통합
- 자동 백그라운드 메시지 처리
- API 키 기반 JWT 인증 완전 자동화
- Public Client와 일관된 인터페이스

🚀 핵심 특징:
- 메시지 루프 자동 관리 (백그라운드 실행)
- 핸들러 기반 메시지 처리 시스템
- 자동 재연결 및 구독 복원
- Rate Limiter 통합 (Private API 정책)
- 연결 건강도 모니터링 (PING/PONG)
- 백그라운드 태스크 안전 관리
"""

import asyncio
import websockets
import json
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_auth import UpbitAuthenticator
from upbit_auto_trading.infrastructure.external_apis.core.rate_limiter import (
    UniversalRateLimiter, ExchangeRateLimitConfig
)
from .upbit_websocket_private_subscription_manager import (
    UpbitPrivateWebSocketSubscriptionManager
)


class StreamType(Enum):
    """WebSocket 스트림 타입 (Private도 동일하게 지원)"""
    SNAPSHOT = "SNAPSHOT"   # 스냅샷 데이터
    REALTIME = "REALTIME"   # 실시간 데이터


class PrivateWebSocketDataType(Enum):
    """Private WebSocket 데이터 타입 (업비트 공식 스펙)"""
    MY_ORDER = "myOrder"     # 내 주문/체결 정보
    MY_ASSET = "myAsset"     # 내 자산(잔고) 정보


@dataclass(frozen=True)
class PrivateWebSocketMessage:
    """
    Private WebSocket 메시지 구조 (Public과 동일한 일관성)
    모든 데이터는 Dict 형태로 통일된 접근 제공
    """
    type: PrivateWebSocketDataType
    data: Dict[str, Any]
    timestamp: datetime
    raw_data: str
    stream_type: Optional[StreamType] = None

    def is_snapshot(self) -> bool:
        """스냅샷 메시지 여부"""
        return self.stream_type == StreamType.SNAPSHOT

    def is_realtime(self) -> bool:
        """실시간 메시지 여부"""
        return self.stream_type == StreamType.REALTIME


class UpbitWebSocketPrivateClient:
    """
    업비트 WebSocket Private 클라이언트 v2.0 - 메시지 루프 시스템 통합

    🎯 Public Client와 동일한 수준의 기능 제공:
    - 자동 메시지 루프 관리
    - 핸들러 기반 메시지 처리
    - 구독 관리자 통합
    - 자동 재연결 및 복원
    - 백그라운드 태스크 안전 관리

    🚀 Private 특화 기능:
    - API 키 기반 JWT 인증
    - myOrder, myAsset 데이터 실시간 수신
    - 마켓별 주문 필터링
    - 자산 변동 실시간 추적
    """

    def __init__(self,
                 access_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 auto_reconnect: bool = True,
                 max_reconnect_attempts: int = 10,
                 reconnect_delay: float = 5.0,
                 ping_interval: float = 30.0,
                 message_timeout: float = 60.0,
                 auto_start_message_loop: bool = True):
        """
        업비트 Private WebSocket 클라이언트 초기화

        Args:
            access_key: Upbit API Access Key (기본값: 시스템에서 자동 로드)
            secret_key: Upbit API Secret Key (기본값: 시스템에서 자동 로드)
            auto_reconnect: 자동 재연결 여부
            max_reconnect_attempts: 최대 재연결 시도 횟수
            reconnect_delay: 재연결 지연 시간 (초)
            ping_interval: 핑 간격 (초)
            message_timeout: 메시지 타임아웃 (초)
            auto_start_message_loop: 자동 메시지 루프 시작 여부
        """
        # 로거 초기화
        self.logger = create_component_logger("UpbitWebSocketPrivate")

        # 연결 설정
        self.url = "wss://api.upbit.com/websocket/v1/private"
        self.auth = UpbitAuthenticator(access_key, secret_key)
        self.websocket: Optional[Any] = None
        self.is_connected = False

        # Rate Limiter 설정 (Private API 정책)
        config = ExchangeRateLimitConfig.for_upbit_private()
        self.rate_limiter = UniversalRateLimiter(config)

        # 재연결 설정
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self.reconnect_attempts = 0

        # 메시지 처리 설정
        self.ping_interval = ping_interval
        self.message_timeout = message_timeout
        self.auto_start_message_loop = auto_start_message_loop

        # 🎯 Private 전용 구독 관리자 통합
        self.subscription_manager = UpbitPrivateWebSocketSubscriptionManager()

        # 메시지 핸들러 시스템 (Public Client와 동일)
        self.message_handlers: Dict[PrivateWebSocketDataType, List[Callable]] = {}
        self.message_loop_task: Optional[asyncio.Task] = None
        self._message_loop_running = False

        # 백그라운드 태스크 관리
        self._background_tasks: Set[asyncio.Task] = set()
        self._task_cleanup_timeout = 3.0

        # 연결 건강도 모니터링
        self._connection_health = {
            'last_ping_time': None,
            'last_pong_time': None,
            'ping_failures': 0,
            'max_ping_failures': 3
        }

        # 통계 정보
        self._stats = {
            'messages_received': 0,
            'messages_processed': 0,
            'errors_count': 0,
            'last_message_time': None,
            'connection_start_time': None,
            'reconnection_count': 0
        }

        self.logger.info("✅ UpbitWebSocketPrivateClient v2.0 초기화 완료 (메시지 루프 시스템 통합)")

    # ================================================================
    # 연결 관리 (JWT 인증 + Rate Limiter)
    # ================================================================

    async def connect(self) -> bool:
        """WebSocket 연결 (API 키 인증 필요)"""
        try:
            # Rate Limiter 체크
            await self.rate_limiter.acquire()
            
            self.logger.info(f"Private WebSocket 연결 시도: {self.url}")            # JWT 토큰 생성
            jwt_token = self.auth.create_jwt_token()
            headers = {
                "Authorization": f"Bearer {jwt_token}"
            }

            # WebSocket 연결
            self.websocket = await websockets.connect(
                self.url,
                additional_headers=headers,
                ping_interval=self.ping_interval,
                ping_timeout=self.message_timeout,
                close_timeout=10.0
            )

            self.is_connected = True
            self.reconnect_attempts = 0
            self._stats['connection_start_time'] = datetime.now()

            # 자동 메시지 루프 시작 (Public Client와 동일)
            if self.auto_start_message_loop:
                await self._start_message_loop()

            # 백그라운드 태스크 시작
            self._background_tasks.add(asyncio.create_task(self._keep_alive()))

            self.logger.info("✅ Private WebSocket 연결 성공 (API 키 인증 완료)")
            return True

        except Exception as e:
            self.logger.error(f"❌ Private WebSocket 연결 실패: {e}")
            self.is_connected = False
            return False

    async def disconnect(self) -> None:
        """WebSocket 연결 해제 (개선된 안정성)"""
        try:
            self.logger.info("🔌 Private WebSocket 연결 해제 시작")

            # 메시지 루프 정지
            await self._stop_message_loop()

            # 연결 상태 비활성화
            self.is_connected = False
            self.auto_reconnect = False

            # WebSocket 연결 정리
            if self.websocket:
                try:
                    await asyncio.wait_for(self.websocket.close(), timeout=3.0)
                except asyncio.TimeoutError:
                    self.logger.warning("WebSocket 닫기 타임아웃 - 강제 종료")
                except Exception as close_error:
                    self.logger.debug(f"WebSocket 닫기 중 오류: {close_error}")

            # 백그라운드 태스크 정리
            await self._cleanup_background_tasks()

            self.logger.info("✅ Private WebSocket 연결 해제 완료")

        except Exception as e:
            self.logger.warning(f"연결 해제 중 오류: {e}")
        finally:
            self.websocket = None

    # ================================================================
    # 구독 관리 (Private 전용 구독 관리자 사용)
    # ================================================================

    async def subscribe_my_orders(self, markets: Optional[List[str]] = None) -> bool:
        """
        내 주문/체결 정보 구독

        Args:
            markets: 구독할 마켓 목록 (None이면 모든 마켓)

        Returns:
            bool: 구독 성공 여부
        """
        if not self.is_connected or not self.websocket:
            self.logger.error("WebSocket이 연결되지 않음")
            return False

        try:
            # 구독 관리자에 등록
            self.subscription_manager.subscribe_my_orders(markets)

            # WebSocket 메시지 전송
            message = self.subscription_manager.create_subscription_message()
            if not message:
                self.logger.error("구독 메시지 생성 실패")
                return False

            await self.websocket.send(json.dumps(message))

            self.logger.info(f"✅ 내 주문 구독 완료: {markets or '전체 마켓'}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 내 주문 구독 실패: {e}")
            return False

    async def subscribe_my_assets(self) -> bool:
        """
        내 자산(잔고) 정보 구독

        Returns:
            bool: 구독 성공 여부
        """
        if not self.is_connected or not self.websocket:
            self.logger.error("WebSocket이 연결되지 않음")
            return False

        try:
            # 구독 관리자에 등록
            self.subscription_manager.subscribe_my_assets()

            # WebSocket 메시지 전송
            message = self.subscription_manager.create_subscription_message()
            if not message:
                self.logger.error("구독 메시지 생성 실패")
                return False

            await self.websocket.send(json.dumps(message))

            self.logger.info("✅ 내 자산 구독 완료")
            return True

        except Exception as e:
            self.logger.error(f"❌ 내 자산 구독 실패: {e}")
            return False

    async def subscribe_all(self, markets: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        모든 Private 데이터 구독 (편의 메서드)

        Args:
            markets: 주문 구독용 마켓 목록

        Returns:
            Dict[str, bool]: 구독 결과 {'my_orders': bool, 'my_assets': bool}
        """
        results = {}

        # 주문 정보 구독
        results['my_orders'] = await self.subscribe_my_orders(markets)

        # 자산 정보 구독
        results['my_assets'] = await self.subscribe_my_assets()

        success_count = sum(results.values())
        self.logger.info(f"📊 Private 데이터 구독 완료: {success_count}/2개 성공")

        return results

    # ================================================================
    # 메시지 핸들러 시스템 (Public Client와 동일)
    # ================================================================

    def add_message_handler(self, data_type: PrivateWebSocketDataType, handler: Callable) -> None:
        """메시지 핸들러 추가"""
        if data_type not in self.message_handlers:
            self.message_handlers[data_type] = []
        self.message_handlers[data_type].append(handler)
        self.logger.debug(f"📝 {data_type.value} 핸들러 추가")

    def add_order_handler(self, handler: Callable) -> None:
        """주문 정보 핸들러 추가 (편의 메서드)"""
        self.add_message_handler(PrivateWebSocketDataType.MY_ORDER, handler)

    def add_asset_handler(self, handler: Callable) -> None:
        """자산 정보 핸들러 추가 (편의 메서드)"""
        self.add_message_handler(PrivateWebSocketDataType.MY_ASSET, handler)

    def add_order_completion_handler(self, handler: Callable) -> None:
        """주문 완료 전용 핸들러 (주문 상태가 done인 경우)"""
        def order_completion_filter(message: PrivateWebSocketMessage):
            if (message.type == PrivateWebSocketDataType.MY_ORDER and
                    message.data.get('state') == 'done'):
                handler(message)

        self.add_message_handler(PrivateWebSocketDataType.MY_ORDER, order_completion_filter)

    def add_snapshot_handler(self, data_type: PrivateWebSocketDataType, handler: Callable) -> None:
        """스냅샷 전용 핸들러 추가"""
        def snapshot_filter(message: PrivateWebSocketMessage):
            if message.is_snapshot():
                handler(message)

        self.add_message_handler(data_type, snapshot_filter)

    def add_realtime_handler(self, data_type: PrivateWebSocketDataType, handler: Callable) -> None:
        """실시간 전용 핸들러 추가"""
        def realtime_filter(message: PrivateWebSocketMessage):
            if message.is_realtime():
                handler(message)

        self.add_message_handler(data_type, realtime_filter)

    # ================================================================
    # 메시지 루프 시스템 (Public Client와 동일)
    # ================================================================

    async def _start_message_loop(self) -> None:
        """메시지 수신 루프 시작"""
        if self._message_loop_running:
            return

        self.message_loop_task = asyncio.create_task(self._message_receiver_loop())
        self._background_tasks.add(self.message_loop_task)
        self._message_loop_running = True
        self.logger.debug("🔄 Private 메시지 루프 시작")

    async def _stop_message_loop(self) -> None:
        """메시지 수신 루프 정지"""
        self._message_loop_running = False

        if self.message_loop_task and not self.message_loop_task.done():
            self.message_loop_task.cancel()
            try:
                await self.message_loop_task
            except asyncio.CancelledError:
                pass

        self.message_loop_task = None
        self.logger.debug("🛑 Private 메시지 루프 정지")

    async def _message_receiver_loop(self) -> None:
        """메시지 수신 루프 (백그라운드 실행)"""
        while self._message_loop_running and self.is_connected:
            try:
                if self.websocket:
                    message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=self.message_timeout
                    )
                    await self._handle_message(message)
                else:
                    break

            except asyncio.TimeoutError:
                # 타임아웃은 정상적인 상황 (아무 메시지 없음)
                continue
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning("⚠️ Private WebSocket 연결 종료됨")
                break
            except Exception as e:
                self.logger.error(f"❌ Private 메시지 수신 오류: {e}")
                self._stats['errors_count'] += 1

                # 심각한 오류 시 재연결 시도
                if self.auto_reconnect:
                    await self._attempt_reconnect()
                    break

    async def _handle_message(self, raw_message) -> None:
        """메시지 처리 (JSON 파싱 + 핸들러 호출)"""
        try:
            # 바이너리 메시지 처리
            if isinstance(raw_message, bytes):
                raw_message = raw_message.decode('utf-8')

            # JSON 파싱
            data = json.loads(raw_message)

            # 통계 업데이트
            self._stats['messages_received'] += 1
            self._stats['last_message_time'] = datetime.now()

            # 에러 메시지 체크
            if 'error' in data:
                self.logger.error(f"Private WebSocket 에러: {data['error']}")
                return

            # 메시지 타입 식별
            message_type = self._identify_message_type(data)
            if not message_type:
                return

            # 스트림 타입 추출
            stream_type = self._extract_stream_type(data)

            # 메시지 객체 생성
            message = PrivateWebSocketMessage(
                type=message_type,
                data=data,
                timestamp=datetime.now(),
                raw_data=raw_message,
                stream_type=stream_type
            )

            # 핸들러 호출
            await self._call_handlers(message)

            self._stats['messages_processed'] += 1

        except json.JSONDecodeError as e:
            self.logger.warning(f"Private 메시지 JSON 파싱 실패: {e}")
        except Exception as e:
            self.logger.error(f"Private 메시지 처리 오류: {e}")

    def _identify_message_type(self, data: Dict[str, Any]) -> Optional[PrivateWebSocketDataType]:
        """
        메시지 타입 식별 (업비트 공식 스펙 기반)
        """
        try:
            # 1. type 필드 기반 식별 (가장 정확한 방법)
            message_type = data.get('type', '')
            if message_type == 'myOrder':
                return PrivateWebSocketDataType.MY_ORDER
            elif message_type == 'myAsset':
                return PrivateWebSocketDataType.MY_ASSET

            # 2. 업비트 공식 필드 기반 식별 (fallback)
            # MyOrder 필드들: uuid, ask_bid, order_type, state, trade_uuid 등
            myorder_fields = {'uuid', 'ask_bid', 'order_type', 'state', 'trade_uuid',
                              'price', 'volume', 'executed_volume', 'trades_count'}

            # MyAsset 필드들: asset_uuid, assets, asset_timestamp
            myasset_fields = {'asset_uuid', 'assets', 'asset_timestamp'}

            data_keys = set(data.keys())

            # MyOrder 식별
            if any(field in data_keys for field in myorder_fields):
                return PrivateWebSocketDataType.MY_ORDER

            # MyAsset 식별
            if any(field in data_keys for field in myasset_fields):
                return PrivateWebSocketDataType.MY_ASSET

            # 알 수 없는 메시지 타입
            self.logger.debug(f"알 수 없는 Private 메시지 타입: {list(data.keys())[:5]}")
            return None

        except Exception as e:
            self.logger.error(f"Private 메시지 타입 식별 실패: {e}")
            return None

    def _extract_stream_type(self, data: Dict[str, Any]) -> Optional[StreamType]:
        """스트림 타입 추출"""
        try:
            stream_type_str = data.get('stream_type')
            if stream_type_str == 'SNAPSHOT':
                return StreamType.SNAPSHOT
            elif stream_type_str == 'REALTIME':
                return StreamType.REALTIME
            else:
                return None
        except Exception as e:
            self.logger.debug(f"스트림 타입 추출 실패: {e}")
            return None

    async def _call_handlers(self, message: PrivateWebSocketMessage) -> None:
        """메시지 핸들러 호출"""
        handlers = self.message_handlers.get(message.type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                self.logger.error(f"Private 메시지 핸들러 실행 오류: {e}")

    # ================================================================
    # 백그라운드 태스크 관리
    # ================================================================

    async def _cleanup_background_tasks(self) -> None:
        """백그라운드 태스크 안전 정리"""
        if not self._background_tasks:
            return

        self.logger.debug(f"백그라운드 태스크 {len(self._background_tasks)}개 정리 중...")

        # 태스크 취소 요청
        for task in list(self._background_tasks):
            if not task.done():
                task.cancel()

        # 타임아웃 적용하여 정리 대기
        try:
            await asyncio.wait_for(
                asyncio.gather(*self._background_tasks, return_exceptions=True),
                timeout=self._task_cleanup_timeout
            )
        except asyncio.TimeoutError:
            self.logger.warning("백그라운드 태스크 정리 타임아웃")

        self._background_tasks.clear()

    async def _keep_alive(self) -> None:
        """연결 유지 (PING 메시지)"""
        while self.is_connected and self.websocket:
            try:
                await asyncio.sleep(self.ping_interval)
                if self.is_connected and self.websocket:
                    pong_waiter = await self.websocket.ping()
                    try:
                        await asyncio.wait_for(pong_waiter, timeout=10.0)
                        self._connection_health['last_ping_time'] = datetime.now()
                        self._connection_health['ping_failures'] = 0
                    except asyncio.TimeoutError:
                        self._connection_health['ping_failures'] += 1
                        if self._connection_health['ping_failures'] >= self._connection_health['max_ping_failures']:
                            self.logger.warning("PING 응답 실패가 지속됨 - 재연결 시도")
                            if self.auto_reconnect:
                                await self._attempt_reconnect()
                            break
            except Exception as e:
                self.logger.warning(f"PING 전송 실패: {e}")
                break

    # ================================================================
    # 재연결 시스템
    # ================================================================

    async def _attempt_reconnect(self) -> bool:
        """자동 재연결 시도"""
        if not self.auto_reconnect or self.reconnect_attempts >= self.max_reconnect_attempts:
            return False

        self.reconnect_attempts += 1
        wait_time = min(2 ** self.reconnect_attempts, 30)  # 지수 백오프

        self.logger.info(f"Private WebSocket 재연결 시도 {self.reconnect_attempts}/{self.max_reconnect_attempts} (대기: {wait_time}초)")

        await asyncio.sleep(wait_time)

        # 기존 연결 정리
        await self.disconnect()

        # 재연결 시도
        if await self.connect():
            self._stats['reconnection_count'] += 1
            # 구독 복원
            await self._restore_subscriptions()
            return True

        return False

    async def _restore_subscriptions(self) -> None:
        """구독 복원 (재연결 후)"""
        if not self.subscription_manager.has_subscriptions():
            return

        try:
            message = self.subscription_manager.get_resubscribe_message()
            if message and self.websocket:
                await self.websocket.send(json.dumps(message))
                self.logger.info("✅ Private 구독 복원 완료")
        except Exception as e:
            self.logger.error(f"❌ Private 구독 복원 실패: {e}")

    # ================================================================
    # 정보 조회 메서드
    # ================================================================

    def get_subscription_info(self) -> Dict[str, Any]:
        """구독 정보 조회"""
        return self.subscription_manager.get_subscription_info()

    def get_connection_stats(self) -> Dict[str, Any]:
        """연결 통계 정보 조회"""
        uptime = None
        if self._stats['connection_start_time']:
            uptime = (datetime.now() - self._stats['connection_start_time']).total_seconds()

        return {
            **self._stats,
            'uptime_seconds': uptime,
            'is_connected': self.is_connected,
            'reconnect_attempts': self.reconnect_attempts,
            'connection_health': self._connection_health.copy()
        }

    # ================================================================
    # 컨텍스트 매니저
    # ================================================================

    async def __aenter__(self):
        """async context manager 진입"""
        if await self.connect():
            return self
        else:
            raise ConnectionError("Private WebSocket 연결 실패")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async context manager 종료"""
        await self.disconnect()

    def __repr__(self) -> str:
        """객체 문자열 표현"""
        status = "연결됨" if self.is_connected else "연결해제"
        subscriptions = len(self.subscription_manager.subscriptions)
        return f"UpbitWebSocketPrivateClient(상태={status}, 구독={subscriptions}개)"
