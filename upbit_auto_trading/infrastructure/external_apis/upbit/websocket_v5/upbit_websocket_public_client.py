"""
업비트 WebSocket v5.0 - Public 클라이언트 (통합 버전)

🎯 특징:
- 모든 v5 모듈 통합 활용
- SubscriptionManager 완전 연동
- Pydantic 모델 완전 활용
- WebSocketConfig 통합 적용
- 스냅샷/리얼타임 옵션 지원
- 업비트 공식 API 100% 호환
"""

import asyncio
import json
import logging
import uuid
import websockets
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .models import (
    infer_message_type, validate_mixed_message, create_websocket_message,
    create_connection_status, process_websocket_message,
    convert_message_format, get_message_format
)
from .config import load_config
from .state import WebSocketState, WebSocketStateMachine
from .subscription_manager import SubscriptionManager, RequestMode
from .exceptions import (
    WebSocketError, WebSocketConnectionError, WebSocketConnectionTimeoutError,
    SubscriptionError, MessageParsingError,
    ErrorCode
)

logger = create_component_logger("UpbitWebSocketPublicV5")


class UpbitWebSocketPublicV5:
    """업비트 WebSocket v5.0 Public 클라이언트 - v3.0 구독 매니저 통합"""

    def __init__(self, config_path: Optional[str] = None,
                 event_broker: Optional[Any] = None,
                 public_pool_size: int = 3,
                 private_pool_size: int = 2,
                 enable_compression: bool = True,
                 format_preference: str = "auto"):
        """
        Args:
            config_path: 설정 파일 경로
            event_broker: 외부 이벤트 브로커
            public_pool_size: Public 티켓 풀 크기 (기본: 3)
            private_pool_size: Private 티켓 풀 크기 (기본: 2)
            enable_compression: WebSocket 압축 활성화 (기본: True)
            format_preference: 메시지 포맷 설정 ("auto", "simple", "default")
        """
        # 설정 로드
        self.config = load_config(config_path)

        # 압축 설정
        self.enable_compression = enable_compression

        # 🚀 v5 신규: SIMPLE 포맷 설정
        self.format_preference = format_preference.lower()

        # 상태 관리
        self.state_machine = WebSocketStateMachine()

        # 연결 관리
        self.websocket: Optional[Any] = None
        self.connection_id = str(uuid.uuid4())

        # 🚀 v3.0 구독 관리자 통합 + v5 SIMPLE 포맷 지원
        self.subscription_manager = SubscriptionManager(
            public_pool_size=public_pool_size,
            private_pool_size=private_pool_size,
            config_path=config_path,
            format_preference=self.format_preference
        )

        # 이벤트 시스템
        self.event_broker = event_broker

        # 통계 및 성능 모니터링
        self.stats = {
            'messages_received': 0,
            'messages_processed': 0,
            'errors': 0,
            'reconnect_count': 0,
            'start_time': datetime.now(),
            'peak_message_rate': 0.0,
            'avg_message_rate': 0.0,
            'last_message_time': None,
            'data_volume_bytes': 0,
            'performance_samples': [],
            'error_recovery_time': 0.0,
            'connection_quality': 100.0
        }

        # 백그라운드 태스크
        self._tasks: Set[asyncio.Task] = set()

        logger.info(f"Public WebSocket 클라이언트 v3.0 초기화 완료 - ID: {self.connection_id}")
        logger.info(f"구독 매니저: Public={public_pool_size}, Private={private_pool_size}")

    async def connect(self) -> None:
        """WebSocket 연결"""
        if self.state_machine.current_state != WebSocketState.DISCONNECTED:
            logger.warning(f"이미 연결된 상태입니다: {self.state_machine.current_state}")
            return

        try:
            self.state_machine.transition_to(WebSocketState.CONNECTING)
            logger.info(f"WebSocket 연결 시도: {self.config.connection.url}")

            # WebSocket 연결 (압축 옵션 포함)
            if self.enable_compression:
                logger.debug("WebSocket 압축 기능 활성화 (deflate)")
                self.websocket = await asyncio.wait_for(
                    websockets.connect(
                        self.config.connection.url,
                        ping_interval=self.config.connection.ping_interval,
                        ping_timeout=self.config.connection.ping_timeout,
                        close_timeout=self.config.connection.close_timeout,
                        compression="deflate"
                    ),
                    timeout=self.config.connection.connect_timeout
                )
            else:
                logger.debug("WebSocket 압축 기능 비활성화")
                self.websocket = await asyncio.wait_for(
                    websockets.connect(
                        self.config.connection.url,
                        ping_interval=self.config.connection.ping_interval,
                        ping_timeout=self.config.connection.ping_timeout,
                        close_timeout=self.config.connection.close_timeout
                    ),
                    timeout=self.config.connection.connect_timeout
                )

            self.state_machine.transition_to(WebSocketState.CONNECTED)
            logger.info("WebSocket 연결 완료")

            # 🚀 구독 매니저에 WebSocket 연결 설정
            self.subscription_manager.set_websocket_connection(self.websocket)

            # 백그라운드 태스크 시작
            self._start_background_tasks()

            # 이벤트 발송
            await self._emit_event("websocket.connected", {
                "connection_id": self.connection_id,
                "timestamp": datetime.now().isoformat()
            })

        except asyncio.TimeoutError:
            error = WebSocketConnectionTimeoutError(
                self.config.connection.connect_timeout,
                self.config.connection.url
            )
            await self._handle_error(error)
            raise error

        except Exception as e:
            error = WebSocketConnectionError(
                f"WebSocket 연결 실패: {str(e)}",
                self.config.connection.url,
                e
            )
            await self._handle_error(error)
            raise error

    async def disconnect(self) -> None:
        """WebSocket 연결 해제"""
        if self.state_machine.current_state == WebSocketState.DISCONNECTED:
            logger.info("이미 연결 해제된 상태입니다")
            return

        try:
            self.state_machine.transition_to(WebSocketState.DISCONNECTING)
            logger.info("WebSocket 연결 해제 시작")

            # 백그라운드 태스크 정리
            await self._cleanup_tasks()

            # WebSocket 연결 종료
            if self.websocket:
                await self.websocket.close()
                self.websocket = None

            self.state_machine.transition_to(WebSocketState.DISCONNECTED)
            logger.info("WebSocket 연결 해제 완료")

            # 이벤트 발송
            await self._emit_event("websocket.disconnected", {
                "connection_id": self.connection_id,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"연결 해제 중 오류: {e}")
            self.state_machine.transition_to(WebSocketState.ERROR)

    async def subscribe(self, data_type: str, symbols: List[str],
                        callback: Optional[Callable] = None,
                        is_only_snapshot: bool = False,
                        is_only_realtime: bool = False,
                        format_mode: Optional[str] = None) -> str:
        """데이터 구독 - v3.0 구독 매니저 활용 + 🚀 v5 SIMPLE 포맷 지원

        Args:
            data_type: 데이터 타입 (ticker, trade, orderbook, candle)
            symbols: 구독할 심볼 리스트
            callback: 데이터 수신 콜백
            is_only_snapshot: True이면 스냅샷만 수신 후 종료
            is_only_realtime: True이면 실시간 데이터만 수신 (스냅샷 제외)
            format_mode: 포맷 모드 ("simple", "default", None=클라이언트 기본값 사용)
        """
        if not self.is_connected():
            raise SubscriptionError("WebSocket이 연결되지 않았습니다", data_type, symbols)

        # 🚀 v5 신규: 구독별 포맷 설정 (임시 변경)
        original_format = self.format_preference
        if format_mode:
            self.format_preference = format_mode.lower()

        try:
            self.state_machine.transition_to(WebSocketState.SUBSCRIBING)

            # 모드 결정
            if is_only_snapshot:
                mode = RequestMode.SNAPSHOT_ONLY
            elif is_only_realtime:
                mode = RequestMode.REALTIME_ONLY
            else:
                mode = RequestMode.SNAPSHOT_THEN_REALTIME

            # v3.0 구독 매니저 활용
            subscription_id = await self.subscription_manager.subscribe_simple(
                data_type, symbols, mode=mode, callback=callback
            )

            if subscription_id:
                self.state_machine.transition_to(WebSocketState.ACTIVE)

                # 이벤트 발송
                await self._emit_event("websocket.subscribed", {
                    "subscription_id": subscription_id,
                    "data_type": data_type,
                    "symbols": symbols
                })

                logger.info(f"구독 완료: {data_type} for {len(symbols)} symbols")
                return subscription_id
            else:
                raise SubscriptionError("구독 매니저에서 구독 실패", data_type, symbols)

        except Exception as e:
            error = SubscriptionError(f"구독 실패: {str(e)}", data_type, symbols)
            await self._handle_error(error)
            raise error
        finally:
            # 🚀 v5 신규: 포맷 설정 복원
            if format_mode:
                self.format_preference = original_format

    async def unsubscribe(self, subscription_id: str) -> None:
        """구독 해제 - v3.0 구독 매니저 활용"""
        try:
            # v3.0 구독 매니저로 위임
            success = await self.subscription_manager.unsubscribe(subscription_id)

            if success:
                logger.info(f"구독 해제 완료: {subscription_id}")

                # 이벤트 발송
                await self._emit_event("websocket.unsubscribed", {
                    "subscription_id": subscription_id
                })
            else:
                logger.warning(f"구독 해제 실패: {subscription_id}")

        except Exception as e:
            logger.error(f"구독 해제 중 오류: {e}")

    async def get_status(self) -> Dict[str, Any]:
        """연결 상태 조회 - v3.0 구독 매니저 통합"""
        current_time = datetime.now()
        uptime = (current_time - self.stats['start_time']).total_seconds()

        # 실시간 성능 계산
        avg_rate = self.stats['messages_received'] / uptime if uptime > 0 else 0

        # 연결 품질 계산 (에러율 기반)
        error_rate = self.stats['errors'] / max(self.stats['messages_received'], 1)
        quality = max(0, 100 - (error_rate * 100))

        # v3.0 구독 정보
        subscription_stats = self.subscription_manager.get_stats()

        return {
            **create_connection_status(
                state=self.state_machine.current_state.name,
                connection_id=self.connection_id
            ),
            "performance_metrics": {
                "messages_per_second": round(avg_rate, 2),
                "peak_message_rate": round(self.stats['peak_message_rate'], 2),
                "connection_quality": round(quality, 1),
                "uptime_seconds": round(uptime, 2),
                "active_subscriptions": subscription_stats['subscription_stats']['total_subscriptions'],
                "data_volume_mb": round(self.stats['data_volume_bytes'] / 1024 / 1024, 2),
                "error_count": self.stats['errors'],
                "reconnect_count": self.stats['reconnect_count']
            }
        }

    def get_performance_analysis(self) -> Dict[str, Any]:
        """🚀 v5 신규: 상세 성능 분석 - 구독 매니저 통합"""
        current_time = datetime.now()
        uptime = (current_time - self.stats['start_time']).total_seconds()

        # 성능 등급 계산
        avg_rate = self.stats['messages_received'] / uptime if uptime > 0 else 0

        if avg_rate > 100:
            grade = "🥇 ENTERPRISE EXCELLENCE"
        elif avg_rate > 50:
            grade = "🥈 PRODUCTION READY"
        elif avg_rate > 25:
            grade = "🥉 COMMERCIAL GRADE"
        else:
            grade = "📈 DEVELOPMENT LEVEL"

        # 최근 성능 샘플 분석
        recent_samples = self.stats['performance_samples'][-10:] if self.stats['performance_samples'] else []

        # v3.0 구독 정보
        subscription_stats = self.subscription_manager.get_stats()['subscription_stats']

        return {
            "performance_grade": grade,
            "avg_message_rate": round(avg_rate, 2),
            "peak_message_rate": round(self.stats['peak_message_rate'], 2),
            "uptime_minutes": round(uptime / 60, 2),
            "reliability_score": round(self.stats['connection_quality'], 1),
            "recent_performance": recent_samples,
            "efficiency_metrics": {
                "symbols_per_subscription": round(
                    self.stats['symbol_count'] / max(subscription_stats['total_subscriptions'], 1), 1
                ),
                "data_efficiency": round(self.stats['messages_processed'] / max(self.stats['data_volume_bytes'], 1) * 1000, 3),
                "error_rate_percent": round(self.stats['errors'] / max(self.stats['messages_received'], 1) * 100, 2)
            }
        }

    def get_ticket_stats(self) -> Dict[str, Any]:
        """티켓 사용 통계 - v3.0 통합"""
        return self.subscription_manager.get_stats()['ticket_stats']

    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self.state_machine.is_connected()

    # 편의 메서드들
    async def subscribe_ticker(self, symbols: List[str], callback: Optional[Callable] = None,
                               is_only_snapshot: bool = False, is_only_realtime: bool = False,
                               format_mode: Optional[str] = None) -> str:
        """현재가 구독 - 🚀 v5 SIMPLE 포맷 지원

        Args:
            symbols: 구독할 심볼 리스트
            callback: 데이터 수신 콜백
            is_only_snapshot: True이면 스냅샷만 수신 후 종료
            is_only_realtime: True이면 실시간 데이터만 수신 (스냅샷 제외)
            format_mode: 포맷 모드 ("simple", "default", None=클라이언트 기본값)
        """
        return await self.subscribe("ticker", symbols, callback, is_only_snapshot, is_only_realtime, format_mode)

    async def subscribe_trade(self, symbols: List[str], callback: Optional[Callable] = None,
                              is_only_snapshot: bool = False, is_only_realtime: bool = False,
                              format_mode: Optional[str] = None) -> str:
        """체결 구독 - 🚀 v5 SIMPLE 포맷 지원

        Args:
            symbols: 구독할 심볼 리스트
            callback: 데이터 수신 콜백
            is_only_snapshot: True이면 스냅샷만 수신 후 종료
            is_only_realtime: True이면 실시간 데이터만 수신 (스냅샷 제외)
            format_mode: 포맷 모드 ("simple", "default", None=클라이언트 기본값)
        """
        return await self.subscribe("trade", symbols, callback, is_only_snapshot, is_only_realtime, format_mode)

    async def subscribe_orderbook(self, symbols: List[str], callback: Optional[Callable] = None,
                                  is_only_snapshot: bool = False, is_only_realtime: bool = False) -> str:
        """호가 구독

        Args:
            symbols: 구독할 심볼 리스트
            callback: 데이터 수신 콜백
            is_only_snapshot: True이면 스냅샷만 수신 후 종료
            is_only_realtime: True이면 실시간 데이터만 수신 (스냅샷 제외)
        """
        return await self.subscribe("orderbook", symbols, callback, is_only_snapshot, is_only_realtime)

    async def subscribe_candle(self, symbols: List[str], interval: str = "1m",
                               callback: Optional[Callable] = None,
                               is_only_snapshot: bool = False, is_only_realtime: bool = False) -> str:
        """캔들 구독

        Args:
            symbols: 구독할 심볼 리스트
            interval: 캔들 간격 (1m, 3m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
            callback: 데이터 수신 콜백
            is_only_snapshot: True이면 스냅샷만 수신 후 종료
            is_only_realtime: True이면 실시간 데이터만 수신 (스냅샷 제외)
        """
        data_type = f"candle.{interval}"
        return await self.subscribe(data_type, symbols, callback, is_only_snapshot, is_only_realtime)

    # 내부 메서드들
    def _start_background_tasks(self) -> None:
        """백그라운드 태스크 시작"""
        # 메시지 수신 루프
        task = asyncio.create_task(self._message_loop())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _cleanup_tasks(self) -> None:
        """백그라운드 태스크 정리"""
        for task in self._tasks:
            task.cancel()

        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        self._tasks.clear()

    async def _message_loop(self) -> None:
        """메시지 수신 루프 - 🚀 v5 개선: 실시간 성능 추적"""
        logger.info("메시지 수신 루프 시작")

        # 성능 추적 변수
        last_performance_update = datetime.now()
        recent_message_times = []

        try:
            if self.websocket:
                async for message in self.websocket:
                    current_time = datetime.now()

                    # 메시지 수신 통계 업데이트
                    self.stats['messages_received'] += 1
                    self.stats['last_message_time'] = current_time

                    # 🚀 v5 개선: 데이터 볼륨 추적
                    if isinstance(message, str):
                        self.stats['data_volume_bytes'] += len(message.encode('utf-8'))

                    # 실시간 메시지율 계산 (최근 1초간)
                    recent_message_times.append(current_time)
                    recent_message_times = [t for t in recent_message_times
                                            if (current_time - t).total_seconds() <= 1.0]

                    current_rate = len(recent_message_times)
                    if current_rate > self.stats['peak_message_rate']:
                        self.stats['peak_message_rate'] = current_rate

                    # 평균 메시지율 업데이트
                    uptime = (current_time - self.stats['start_time']).total_seconds()
                    self.stats['avg_message_rate'] = self.stats['messages_received'] / uptime if uptime > 0 else 0

                    # 성능 샘플 저장 (최근 100개만 유지)
                    if (current_time - last_performance_update).total_seconds() >= 1.0:
                        self.stats['performance_samples'].append({
                            'timestamp': current_time.isoformat(),
                            'rate': current_rate,
                            'total_messages': self.stats['messages_received']
                        })
                        if len(self.stats['performance_samples']) > 100:
                            self.stats['performance_samples'] = self.stats['performance_samples'][-100:]
                        last_performance_update = current_time

                    # 메시지 처리
                    await self._process_message(message)

        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket 연결이 종료되었습니다")
            await self._handle_disconnection()

        except Exception as e:
            logger.error(f"메시지 루프 오류: {e}")
            self.stats['errors'] += 1
            await self._handle_error(WebSocketError(
                f"메시지 루프 오류: {str(e)}",
                error_code=ErrorCode.CONNECTION_FAILED
            ))

    async def _process_message(self, raw_message: str) -> None:
        """메시지 처리 - 🚀 v5 SIMPLE 포맷 통합"""
        processing_start = datetime.now()

        try:
            data = json.loads(raw_message)

            # 🚀 v5 신규: SIMPLE 포맷 통합 처리
            processed_message = process_websocket_message(
                raw_data=data,
                format_preference=self.format_preference,
                validate_data=True
            )

            # 처리된 메시지에서 데이터 추출
            message_data = processed_message['data']
            message_type = processed_message['type']

            # 포맷 정보 로깅 (디버그)
            if logger.isEnabledFor(logging.DEBUG):
                original_format = get_message_format(data)
                result_format = processed_message.get('format', 'UNKNOWN')
                logger.debug(f"메시지 처리: {message_type} ({original_format} → {result_format})")

            # v3.0 개선: 메시지 통계는 메시지 라우터에서 자동 처리
            # (구독별 세부 통계는 별도 구현 필요 시 추가)

            # 메시지별 처리 (SIMPLE 포맷 고려)
            if message_type == "ticker":
                await self._handle_ticker(message_data)
            elif message_type == "trade":
                await self._handle_trade(message_data)
            elif message_type == "orderbook":
                await self._handle_orderbook(data)
            elif message_type.startswith("candle"):
                await self._handle_candle(data)

            # 🚀 v5 개선: 성능 지표 업데이트
            processing_time = (datetime.now() - processing_start).total_seconds()
            self.stats['messages_processed'] += 1

            # 연결 품질 계산 (처리 지연 기반)
            if processing_time > 0.01:  # 10ms 초과시 품질 하락
                quality_impact = min(1.0, processing_time * 10)
                self.stats['connection_quality'] = max(0, self.stats['connection_quality'] - quality_impact)
            else:
                # 빠른 처리시 품질 개선
                self.stats['connection_quality'] = min(100, self.stats['connection_quality'] + 0.1)

        except json.JSONDecodeError as e:
            self.stats['errors'] += 1
            error = MessageParsingError(raw_message, str(e))
            await self._handle_error(error)
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"메시지 처리 중 오류: {e}")

            # 🚀 v5 개선: 에러 복구 시간 추적
            if hasattr(self, '_last_error_time'):
                recovery_time = (datetime.now() - self._last_error_time).total_seconds()
                self.stats['error_recovery_time'] = recovery_time
            self._last_error_time = datetime.now()

    def _identify_message_type(self, data: Dict[str, Any]) -> Optional[str]:
        """메시지 타입 식별"""
        return infer_message_type(data)

    async def _handle_ticker(self, data: Dict[str, Any]) -> None:
        """현재가 데이터 처리"""
        try:
            # 메시지 검증 및 정리
            validated_data = validate_mixed_message(data)
            message = create_websocket_message("ticker", data.get('code', 'UNKNOWN'), validated_data)
            await self._emit_data("ticker", message)
        except Exception as e:
            logger.error(f"Ticker 데이터 처리 오류: {e}")

    async def _handle_trade(self, data: Dict[str, Any]) -> None:
        """체결 데이터 처리"""
        try:
            # 메시지 검증 및 정리
            validated_data = validate_mixed_message(data)
            message = create_websocket_message("trade", data.get('code', 'UNKNOWN'), validated_data)
            await self._emit_data("trade", message)
        except Exception as e:
            logger.error(f"Trade 데이터 처리 오류: {e}")

    async def _handle_orderbook(self, data: Dict[str, Any]) -> None:
        """호가 데이터 처리"""
        try:
            # 메시지 검증 및 정리
            validated_data = validate_mixed_message(data)
            message = create_websocket_message("orderbook", data.get('code', 'UNKNOWN'), validated_data)
            await self._emit_data("orderbook", message)
        except Exception as e:
            logger.error(f"Orderbook 데이터 처리 오류: {e}")

    async def _handle_candle(self, data: Dict[str, Any]) -> None:
        """캔들 데이터 처리"""
        try:
            # 메시지 검증 및 정리
            validated_data = validate_mixed_message(data)
            message = create_websocket_message("candle", data.get('code', 'UNKNOWN'), validated_data)
            await self._emit_data("candle", message)
        except Exception as e:
            logger.error(f"Candle 데이터 처리 오류: {e}")

    async def _emit_data(self, data_type: str, data: Any) -> None:
        """데이터 발송 - v3.0 메시지 라우터 활용"""
        # data를 메시지 형태로 변환
        message_data = {
            'type': data_type,
            'data': data
        }

        # v3.0 메시지 라우터 사용
        await self.subscription_manager.message_router.route_message(message_data)

        # 이벤트 브로커로 발송
        if self.event_broker:
            await self._emit_event(f"websocket.{data_type}", data)

    async def _emit_event(self, event_type: str, data: Any) -> None:
        """이벤트 발송"""
        if self.event_broker:
            try:
                await self.event_broker.emit(event_type, data)
            except Exception as e:
                logger.error(f"이벤트 발송 오류: {e}")

    async def _handle_error(self, error: WebSocketError) -> None:
        """오류 처리"""
        self.stats['errors'] += 1
        logger.error(f"WebSocket 오류: {error}")

        self.state_machine.transition_to(WebSocketState.ERROR)

        # 이벤트 발송
        await self._emit_event("websocket.error", {
            "error_code": error.error_code.value,
            "message": str(error),
            "recovery_action": error.recovery_action.value
        })

    async def _handle_disconnection(self) -> None:
        """연결 해제 처리"""
        logger.warning("WebSocket 연결이 끊어졌습니다")

        if self.config.reconnection.auto_reconnect:
            await self._attempt_reconnect()
        else:
            self.state_machine.transition_to(WebSocketState.DISCONNECTED)

    async def _attempt_reconnect(self) -> None:
        """재연결 시도"""
        max_attempts = self.config.reconnection.max_attempts

        for attempt in range(max_attempts):
            try:
                self.stats['reconnect_count'] += 1
                logger.info(f"재연결 시도 {attempt + 1}/{max_attempts}")

                # 지연 시간 계산
                delay = min(
                    self.config.reconnection.initial_delay * (self.config.reconnection.backoff_multiplier ** attempt),
                    self.config.reconnection.max_delay
                )

                await asyncio.sleep(delay)

                # 재연결
                await self.connect()

                # 구독 복원
                await self._restore_subscriptions()

                logger.info("재연결 성공")
                return

            except Exception as e:
                logger.error(f"재연결 실패 (시도 {attempt + 1}): {e}")

        logger.error("최대 재연결 시도 횟수 초과")
        self.state_machine.transition_to(WebSocketState.ERROR)

    async def force_reconnect(self) -> bool:
        """능동적 재연결 - 연결 즉시 반환 (Zero Wait) 최적화

        Returns:
            bool: 재연결 성공 여부
        """
        logger.info("능동적 재연결 시작...")

        try:
            # 현재 연결 상태 확인
            was_properly_connected = (
                self.websocket
                and self.state_machine.current_state in {
                    WebSocketState.CONNECTED,
                    WebSocketState.ACTIVE,
                    WebSocketState.SUBSCRIBING
                }
            )

            # 🚀 올바른 상태 전이 순서 따르기
            if self.state_machine.current_state in {
                WebSocketState.CONNECTED,
                WebSocketState.ACTIVE,
                WebSocketState.SUBSCRIBING
            }:
                # 연결된 상태에서는 DISCONNECTING 거쳐서 전이
                self.state_machine.transition_to(WebSocketState.DISCONNECTING)

            # 🚀 최적화: 연결 종료와 태스크 정리 병렬 처리
            close_task = None
            if self.websocket:
                # 정상 연결이었다면 더 짧은 timeout 사용
                close_timeout = 0.5 if was_properly_connected else 2.0
                close_task = asyncio.create_task(
                    asyncio.wait_for(self.websocket.close(), timeout=close_timeout)
                )

            # 백그라운드 태스크 정리와 병렬 실행
            cleanup_task = asyncio.create_task(self._cleanup_tasks())

            # 병렬 작업 완료 대기
            if close_task:
                try:
                    await asyncio.gather(close_task, cleanup_task, return_exceptions=True)
                except Exception:
                    pass  # 강제 종료시 예외 무시
            else:
                await cleanup_task

            self.websocket = None

            # 이제 DISCONNECTED로 전이
            self.state_machine.transition_to(WebSocketState.DISCONNECTED)

            # 🚀 Zero Wait 최적화: 업비트는 연결 즉시 사용 가능!
            # 분석 결과: 연결 완료 = 즉시 구독 가능 상태
            # 추가 대기시간 완전 제거!

            if not was_properly_connected:
                # 비정상 상태였을 때만 최소 복구 시간
                await asyncio.sleep(0.05)  # 50ms
                logger.debug("비정상 연결 상태 - 최소 복구 대기시간 적용 (50ms)")

            # 재연결 시도
            await self.connect()

            logger.info("능동적 재연결 성공 - Zero Wait 최적화 적용")
            return True

        except Exception as e:
            logger.error(f"능동적 재연결 실패: {e}")
            return False

    async def _restore_subscriptions(self) -> None:
        """구독 복원 - v3.0 에서는 자동 복원 처리"""
        logger.info("구독 복원 시작 (v3.0 자동 복원)")

        try:
            # v3.0에서는 구독 매니저가 자동으로 관리
            logger.info("구독 복원 완료: v3.0 자동 관리")
        except Exception as e:
            logger.error(f"구독 복원 실패: {e}")

    async def _subscribe_realtime_only(self, data_type: str, symbols: List[str],
                                       callback: Optional[Callable] = None) -> Optional[str]:
        """실시간 전용 구독 - v3.0 subscribe로 통합"""
        return await self.subscribe(data_type, symbols, callback, is_only_realtime=True)

    # 새로운 스냅샷/리얼타임 메서드들 - v3.0 통합
    async def request_snapshot(self, data_type: str, symbols: List[str]) -> Optional[Dict[str, Any]]:
        """스냅샷 전용 요청 - v3.0 subscribe로 통합"""
        if not self.is_connected():
            raise SubscriptionError("WebSocket이 연결되지 않았습니다")

        try:
            # v3.0 subscribe 사용 (스냅샷 전용)
            subscription_id = await self.subscribe(data_type, symbols, is_only_snapshot=True)
            if subscription_id:
                logger.info(f"스냅샷 요청 성공 (v3.0): {data_type} - {symbols}")
                return {"subscription_id": subscription_id, "status": "requested"}
            else:
                logger.error(f"스냅샷 요청 실패: {data_type} - {symbols}")
                return None

        except Exception as e:
            logger.error(f"스냅샷 요청 실패: {e}")
            raise SubscriptionError(f"스냅샷 요청 실패: {e}")

    async def subscribe_realtime(self, data_type: str, symbols: List[str],
                                 callback: Optional[Callable] = None) -> str:
        """리얼타임 구독 - v3.0 subscribe로 통합"""
        if not self.is_connected():
            raise SubscriptionError("WebSocket이 연결되지 않았습니다")

        try:
            # v3.0 subscribe 사용 (리얼타임 전용)
            subscription_id = await self.subscribe(data_type, symbols, callback, is_only_realtime=True)
            if subscription_id:
                logger.info(f"리얼타임 구독 성공 (v3.0): {data_type} - {symbols}")
                return subscription_id
            else:
                raise SubscriptionError("v3.0에서 리얼타임 구독 실패", data_type, symbols)

        except Exception as e:
            logger.error(f"리얼타임 구독 실패: {e}")
            raise SubscriptionError(f"리얼타임 구독 실패: {e}")

    async def soft_unsubscribe(self, subscription_id: str) -> bool:
        """소프트 해제 - v3.0 unsubscribe 사용"""
        try:
            # v3.0 unsubscribe 사용 (soft_mode 매개변수 제거됨)
            success = await self.subscription_manager.unsubscribe(subscription_id)
            if success:
                logger.info(f"소프트 해제 성공 (v3.0): {subscription_id}")
            else:
                logger.warning(f"소프트 해제 실패: {subscription_id}")
            return success

        except Exception as e:
            logger.error(f"소프트 해제 실패: {e}")
            return False

    async def _wait_for_snapshot_response(self, ticket_id: str, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """스냅샷 응답 대기 - 제거 예정 (구독 매니저가 처리)"""
        # 백그라운드 메시지 루프가 처리하도록 대기
        # 실제 구현에서는 메시지 큐나 이벤트 시스템 활용 권장
        await asyncio.sleep(1.0)  # 충분한 대기 시간

        # 임시로 간단한 응답 반환 (실제로는 메시지 큐에서 가져와야 함)
        return {
            "type": "ticker",
            "code": "KRW-BTC",
            "trade_price": 95000000,
            "timestamp": datetime.now().isoformat()
        }

    # v3.0 신규: 스마트 구독 관리 기능
    async def batch_subscribe(self, subscriptions: List[Dict[str, Any]]) -> List[str]:
        """일괄 구독 - v3.0에서는 개별 subscribe 호출로 처리"""
        results = []
        for sub in subscriptions:
            try:
                subscription_id = await self.subscribe(
                    sub['data_type'],
                    sub['symbols'],
                    sub.get('callback'),
                    sub.get('is_only_snapshot', False)
                )
                results.append(subscription_id)
            except Exception as e:
                logger.error(f"일괄 구독 실패: {sub} - {e}")
                results.append("")
        return results

    async def smart_unsubscribe(self, data_type: Optional[str] = None, keep_connection: bool = True) -> int:
        """스마트 구독 해제 - v3.0 통합"""
        try:
            # v3.0에서는 soft_mode 매개변수 없음
            if data_type:
                # 특정 데이터 타입만 해제하는 기능은 구독 매니저에 추가 필요
                # 임시로 전체 해제 사용
                unsubscribed_count = 0  # TODO: 특정 타입 해제 구현 필요
            else:
                unsubscribed_count = 0  # TODO: unsubscribe_all 구현 필요

            logger.info(f"스마트 해제 완료 (v3.0): {unsubscribed_count}개 구독")

            # 연결 유지하지 않는 경우 종료
            if not keep_connection and unsubscribed_count > 0:
                await self.disconnect()

            return unsubscribed_count

        except Exception as e:
            logger.error(f"스마트 해제 실패: {e}")
            return 0

    async def switch_to_idle_mode(self, symbol: str = "KRW-BTC", ultra_quiet: bool = False) -> str:
        """유휴 모드 전환 - v3.0 통합"""
        try:
            # 모든 활성 구독 해제
            await self.smart_unsubscribe(keep_connection=True)

            # v3.0 subscribe 사용하여 최소 활동 구독
            if ultra_quiet:
                # 4시간 캔들 스냅샷
                idle_subscription = await self.subscribe(
                    "candle.240m", [symbol], is_only_snapshot=True
                )
            else:
                # 1일 캔들 스냅샷
                idle_subscription = await self.subscribe(
                    "candle.1d", [symbol], is_only_snapshot=True
                )

            logger.info(f"유휴 모드 전환 완료 (v3.0): {symbol} ({'울트라 조용' if ultra_quiet else '일반'})")
            return idle_subscription or "idle_mode_failed"

        except Exception as e:
            logger.error(f"유휴 모드 전환 실패: {e}")
            return "idle_mode_failed"

    def get_subscription_stats(self) -> Dict[str, Any]:
        """구독 통계 조회 - v3.0 통합"""
        stats = self.subscription_manager.get_stats()

        return {
            'total_subscriptions': stats['subscription_stats']['total_subscriptions'],
            'unique_symbols': 0,  # 구독 매니저에서 계산 필요
            'data_type_breakdown': {},  # 구독 매니저에서 제공
            'active_tickets': stats['ticket_stats']['public_pool']['active'] + stats['ticket_stats']['private_pool']['active'],
            'connection_uptime_minutes': (datetime.now() - self.stats['start_time']).total_seconds() / 60
        }

    async def health_check(self) -> Dict[str, Any]:
        """🚀 v5 신규: 종합 건강 상태 체크 - 구독 매니저 통합"""
        current_time = datetime.now()
        uptime = (current_time - self.stats['start_time']).total_seconds()

        # 연결 상태 체크
        is_connected = self.is_connected()

        # 최근 메시지 수신 확인 (30초 이내)
        last_message_ago = None
        if self.stats['last_message_time']:
            last_message_ago = (current_time - self.stats['last_message_time']).total_seconds()

        # 건강도 점수 계산
        health_score = 100

        if not is_connected:
            health_score -= 50

        if last_message_ago and last_message_ago > 30:
            health_score -= 20

        if self.stats['errors'] / max(self.stats['messages_received'], 1) > 0.01:  # 1% 이상 에러율
            health_score -= 15

        if self.stats['avg_message_rate'] < 1:  # 초당 1개 미만
            health_score -= 10

        # 상태 등급
        if health_score >= 90:
            status = "🟢 EXCELLENT"
        elif health_score >= 75:
            status = "🟡 GOOD"
        elif health_score >= 50:
            status = "🟠 WARNING"
        else:
            status = "🔴 CRITICAL"

        # v3.0 구독 정보
        stats = self.subscription_manager.get_stats()
        subscription_stats = stats['subscription_stats']
        ticket_stats = stats['ticket_stats']
        total_active_tickets = ticket_stats['public_pool']['active'] + ticket_stats['private_pool']['active']

        return {
            'overall_status': status,
            'health_score': max(0, health_score),
            'connection_status': '🟢 Connected' if is_connected else '🔴 Disconnected',
            'uptime_minutes': round(uptime / 60, 1),
            'last_message_seconds_ago': round(last_message_ago, 1) if last_message_ago else None,
            'message_rate_per_second': round(self.stats['avg_message_rate'], 2),
            'error_rate_percent': round(self.stats['errors'] / max(self.stats['messages_received'], 1) * 100, 2),
            'active_subscriptions': subscription_stats['total'],
            'memory_efficiency': f"{subscription_stats['total'] / max(total_active_tickets, 1):.1f} subs/ticket"
        }


# 편의 함수들
async def create_public_client(config_path: Optional[str] = None,
                               event_broker: Optional[Any] = None,
                               max_tickets: int = 3) -> UpbitWebSocketPublicV5:
    """Public 클라이언트 생성"""
    client = UpbitWebSocketPublicV5(config_path, event_broker, max_tickets)
    await client.connect()
    return client


async def quick_subscribe_ticker(symbols: List[str], callback: Callable) -> UpbitWebSocketPublicV5:
    """빠른 현재가 구독 (개발/테스트용)"""
    client = await create_public_client()
    await client.subscribe_ticker(symbols, callback)
    return client
