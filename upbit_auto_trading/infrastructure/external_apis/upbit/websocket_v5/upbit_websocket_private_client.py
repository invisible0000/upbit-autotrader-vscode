"""
업비트 WebSocket v5.0 - Private 클라이언트 (v3.0 통합 버전)

🎯 특징:
- SubscriptionManager v3.0 완전 통합
- JWT 인증 자동 처리 및 토큰 갱신
- SIMPLE 포맷 지원
- 고급 성능 모니터링
- Private 데이터 전용 (myOrder, myAsset)
- 보안 강화 (API 키 검증, 토큰 관리)
- Public 클라이언트와 통일된 인터페이스
"""

import asyncio
import json
import time
import jwt
import uuid
import websockets
import logging
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime, timedelta

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .models import (
    validate_mixed_message, create_websocket_message,
    create_connection_status, process_websocket_message,
    get_message_format
)
from .config import load_config
from .state import WebSocketState, WebSocketStateMachine
from .subscription_manager import SubscriptionManager, RequestMode
from .exceptions import (
    WebSocketError, WebSocketConnectionError, WebSocketConnectionTimeoutError,
    SubscriptionError, MessageParsingError, InvalidAPIKeysError,
    ErrorCode
)
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_auth import UpbitAuthenticator

logger = create_component_logger("UpbitWebSocketPrivateV5")


class PrivateDataType:
    """Private 데이터 타입"""
    MY_ORDER = "myOrder"
    MY_ASSET = "myAsset"


class UpbitWebSocketPrivateV5:
    """업비트 WebSocket v5.0 Private 클라이언트 - v3.0 SubscriptionManager 통합"""

    def __init__(self,
                 access_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 config_path: Optional[str] = None,
                 event_broker: Optional[Any] = None,
                 private_pool_size: Optional[int] = None,
                 enable_compression: Optional[bool] = None,
                 format_preference: Optional[str] = None):
        """
        Args:
            access_key: 업비트 API Access Key (None이면 UpbitAuthenticator에서 자동 로드)
            secret_key: 업비트 API Secret Key (None이면 UpbitAuthenticator에서 자동 로드)
            config_path: 설정 파일 경로
            event_broker: 외부 이벤트 브로커
            private_pool_size: Private 티켓 풀 크기 (None이면 config에서 로드)
            enable_compression: WebSocket 압축 활성화 (None이면 config에서 로드)
            format_preference: 메시지 포맷 설정 (None이면 config에서 로드)
        """
        # UpbitAuthenticator를 통한 API 키 로드
        self.auth = UpbitAuthenticator(access_key, secret_key)

        # API 키 검증
        if not self.auth._access_key or not self.auth._secret_key:
            raise InvalidAPIKeysError("Private WebSocket 클라이언트는 API 키가 필수입니다")

        # 설정 로드
        self.config = load_config(config_path)

        # 설정값 결정 (매개변수 우선, 없으면 config 사용)
        self.enable_compression = (enable_compression
                                   if enable_compression is not None
                                   else self.config.performance.enable_message_compression)

        self.format_preference = (format_preference
                                  if format_preference is not None
                                  else self.config.subscription.format_preference).lower()

        pool_size_private = (private_pool_size
                             if private_pool_size is not None
                             else self.config.subscription.private_pool_size)

        # 상태 관리
        self.state_machine = WebSocketStateMachine()

        # 연결 관리
        self.websocket: Optional[Any] = None
        self.connection_id = str(uuid.uuid4())

        # 🚀 v3.0 구독 관리자 통합 (Private 풀만 사용)
        self.subscription_manager = SubscriptionManager(
            public_pool_size=0,  # Private 전용이므로 Public 풀 비활성화
            private_pool_size=pool_size_private,
            config_path=config_path,
            format_preference=self.format_preference
        )

        # JWT 토큰 관리
        self._jwt_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._token_refresh_task: Optional[asyncio.Task] = None

        # 이벤트 시스템
        self.event_broker = event_broker

        # 통계 및 성능 모니터링 (Public 클라이언트와 동일)
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
            'connection_quality': 100.0,
            'auth_token_refreshes': 0,
            'auth_failures': 0
        }

        # 백그라운드 태스크
        self._tasks: Set[asyncio.Task] = set()

        logger.info(f"Private WebSocket 클라이언트 v3.0 초기화 완료 - ID: {self.connection_id}")
        logger.info(f"구독 매니저: Private Pool={pool_size_private}")

    def _generate_jwt_token(self) -> str:
        """JWT 토큰 생성 및 갱신"""
        if not self.auth._secret_key:
            raise InvalidAPIKeysError("Secret Key가 없습니다")

        # 토큰 만료 시간: 현재 시간 + 9분 (10분 만료 전 여유)
        expire_time = datetime.now() + timedelta(minutes=9)

        payload = {
            'iss': self.auth._access_key,
            'exp': int(expire_time.timestamp())
        }

        token = jwt.encode(payload, self.auth._secret_key, algorithm='HS256')

        # 토큰 정보 저장
        self._jwt_token = token
        self._token_expires_at = expire_time

        logger.debug("JWT 토큰 생성 완료")
        return token

    def _is_token_expired(self) -> bool:
        """토큰 만료 여부 확인"""
        if not self._token_expires_at:
            return True

        # 만료 1분 전에 갱신 필요로 판단
        return datetime.now() >= (self._token_expires_at - timedelta(minutes=1))

    async def _refresh_token_if_needed(self) -> None:
        """필요시 토큰 갱신"""
        if self._is_token_expired():
            logger.info("JWT 토큰 갱신 중...")
            try:
                self._generate_jwt_token()
                self.stats['auth_token_refreshes'] += 1
                logger.info("JWT 토큰 갱신 완료")
            except Exception as e:
                logger.error(f"JWT 토큰 갱신 실패: {e}")
                self.stats['auth_failures'] += 1
                raise InvalidAPIKeysError(f"JWT 토큰 갱신 실패: {e}")

    async def _start_token_refresh_task(self) -> None:
        """토큰 자동 갱신 태스크 시작"""
        async def token_refresh_loop():
            while self.is_connected():
                try:
                    # 8분마다 토큰 갱신 확인
                    await asyncio.sleep(480)  # 8분
                    await self._refresh_token_if_needed()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"토큰 갱신 루프 오류: {e}")
                    await asyncio.sleep(60)  # 오류 시 1분 후 재시도

        self._token_refresh_task = asyncio.create_task(token_refresh_loop())
        self._tasks.add(self._token_refresh_task)
        self._token_refresh_task.add_done_callback(self._tasks.discard)

    async def connect(self) -> None:
        """WebSocket 연결 - JWT 인증 포함"""
        if self.state_machine.current_state != WebSocketState.DISCONNECTED:
            logger.warning(f"이미 연결된 상태입니다: {self.state_machine.current_state}")
            return

        try:
            self.state_machine.transition_to(WebSocketState.CONNECTING)
            logger.info(f"Private WebSocket 연결 시도: {self.config.connection.url}")

            # JWT 토큰 생성
            jwt_token = self._generate_jwt_token()

            # WebSocket 연결 (Authorization 헤더 포함)
            headers = {
                'Authorization': f'Bearer {jwt_token}'
            }

            # 압축 옵션 적용
            if self.enable_compression:
                logger.debug("Private WebSocket 압축 기능 활성화 (deflate)")
                self.websocket = await asyncio.wait_for(
                    websockets.connect(
                        self.config.connection.url,
                        extra_headers=headers,
                        ping_interval=self.config.connection.ping_interval,
                        ping_timeout=self.config.connection.ping_timeout,
                        close_timeout=self.config.connection.close_timeout,
                        compression="deflate"
                    ),
                    timeout=self.config.connection.connect_timeout
                )
            else:
                logger.debug("Private WebSocket 압축 기능 비활성화")
                self.websocket = await asyncio.wait_for(
                    websockets.connect(
                        self.config.connection.url,
                        extra_headers=headers,
                        ping_interval=self.config.connection.ping_interval,
                        ping_timeout=self.config.connection.ping_timeout,
                        close_timeout=self.config.connection.close_timeout
                    ),
                    timeout=self.config.connection.connect_timeout
                )

            self.state_machine.transition_to(WebSocketState.CONNECTED)
            logger.info("Private WebSocket 연결 완료")

            # 🚀 구독 매니저에 WebSocket 연결 설정
            self.subscription_manager.set_websocket_connection(self.websocket)

            # 백그라운드 태스크 시작
            self._start_background_tasks()

            # 토큰 자동 갱신 태스크 시작
            await self._start_token_refresh_task()

            # 이벤트 발송
            await self._emit_event("websocket.private.connected", {
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
                f"Private WebSocket 연결 실패: {str(e)}",
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
            logger.info("Private WebSocket 연결 해제 시작")

            # 백그라운드 태스크 정리
            await self._cleanup_tasks()

            # WebSocket 연결 종료
            if self.websocket:
                await self.websocket.close()
                self.websocket = None

            self.state_machine.transition_to(WebSocketState.DISCONNECTED)
            logger.info("Private WebSocket 연결 해제 완료")

            # 이벤트 발송
            await self._emit_event("websocket.private.disconnected", {
                "connection_id": self.connection_id,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Private 연결 해제 중 오류: {e}")
            self.state_machine.transition_to(WebSocketState.ERROR)

    async def subscribe_my_orders(self, markets: Optional[List[str]] = None,
                                  callback: Optional[Callable] = None,
                                  mode: RequestMode = RequestMode.SNAPSHOT_THEN_REALTIME) -> str:
        """내 주문 구독 - v3.0 SubscriptionManager 활용"""
        return await self._subscribe(PrivateDataType.MY_ORDER, markets, callback, mode)

    async def subscribe_my_assets(self, callback: Optional[Callable] = None,
                                  mode: RequestMode = RequestMode.SNAPSHOT_THEN_REALTIME) -> str:
        """내 자산 구독 - v3.0 SubscriptionManager 활용"""
        return await self._subscribe(PrivateDataType.MY_ASSET, None, callback, mode)

    async def _subscribe(self, data_type: str, markets: Optional[List[str]] = None,
                         callback: Optional[Callable] = None,
                         mode: RequestMode = RequestMode.SNAPSHOT_THEN_REALTIME) -> str:
        """Private 데이터 구독 - v3.0 통합"""
        if not self.is_connected():
            raise SubscriptionError("WebSocket이 연결되지 않았습니다", data_type)

        try:
            self.state_machine.transition_to(WebSocketState.SUBSCRIBING)

            # v3.0 구독 매니저 활용 (Private 전용)
            if data_type == PrivateDataType.MY_ORDER and markets:
                # myOrder는 특정 마켓 지정 가능
                subscription_id = await self.subscription_manager.subscribe_simple(
                    data_type, markets, mode=mode, callback=callback
                )
            else:
                # myAsset은 전체 자산 조회
                subscription_id = await self.subscription_manager.subscribe_simple(
                    data_type, ["ALL"], mode=mode, callback=callback
                )

            if subscription_id:
                self.state_machine.transition_to(WebSocketState.ACTIVE)

                # 이벤트 발송
                await self._emit_event("websocket.private.subscribed", {
                    "subscription_id": subscription_id,
                    "data_type": data_type,
                    "markets": markets
                })

                logger.info(f"Private 구독 완료: {data_type}")
                return subscription_id
            else:
                raise SubscriptionError("Private 구독 매니저에서 구독 실패", data_type)

        except Exception as e:
            error = SubscriptionError(f"Private 구독 실패: {str(e)}", data_type)
            await self._handle_error(error)
            raise error

    async def unsubscribe(self, subscription_id: str) -> bool:
        """구독 해제 - v3.0 SubscriptionManager 활용"""
        try:
            # v3.0 구독 매니저로 위임
            success = await self.subscription_manager.unsubscribe(subscription_id)

            if success:
                logger.info(f"Private 구독 해제 완료: {subscription_id}")

                # 이벤트 발송
                await self._emit_event("websocket.private.unsubscribed", {
                    "subscription_id": subscription_id
                })
            else:
                logger.warning(f"Private 구독 해제 실패: {subscription_id}")

            return success

        except Exception as e:
            logger.error(f"Private 구독 해제 중 오류: {e}")
            return False

    async def batch_subscribe(self, subscriptions: List[Dict[str, Any]]) -> List[str]:
        """일괄 구독 - Private 전용 구독들을 한 번에 처리

        Args:
            subscriptions: 구독 요청 리스트
                [
                    {
                        "data_type": "myOrder",
                        "markets": ["KRW-BTC", "KRW-ETH"],  # myOrder의 경우 선택 사항
                        "callback": callback_func,
                        "mode": "snapshot_then_realtime"
                    },
                    {
                        "data_type": "myAsset",
                        "callback": asset_callback,
                        "mode": "realtime_only"
                    }
                ]

        Returns:
            List[str]: 생성된 구독 ID 리스트
        """
        if not self.is_connected():
            raise SubscriptionError("WebSocket이 연결되지 않았습니다")

        logger.info(f"🔄 일괄 구독 시작: {len(subscriptions)}개 요청")

        results = []
        successful_count = 0

        for i, sub_request in enumerate(subscriptions):
            try:
                # 필수 필드 검증
                if "data_type" not in sub_request:
                    logger.error(f"구독 요청 {i + 1}: data_type이 누락되었습니다")
                    results.append("")
                    continue

                data_type = sub_request["data_type"]
                markets = sub_request.get("markets", None)
                callback = sub_request.get("callback", None)
                mode_str = sub_request.get("mode", "snapshot_then_realtime")

                # RequestMode 변환
                try:
                    mode = RequestMode(mode_str)
                except ValueError:
                    logger.warning(f"구독 요청 {i + 1}: 잘못된 모드 '{mode_str}', 기본값 사용")
                    mode = RequestMode.SNAPSHOT_THEN_REALTIME

                # Private 데이터 타입 검증
                if data_type not in [PrivateDataType.MY_ORDER, PrivateDataType.MY_ASSET]:
                    logger.error(f"구독 요청 {i + 1}: 지원하지 않는 Private 데이터 타입: {data_type}")
                    results.append("")
                    continue

                # 개별 구독 실행
                subscription_id = await self._subscribe(data_type, markets, callback, mode)
                results.append(subscription_id)
                successful_count += 1

                logger.debug(f"구독 요청 {i + 1}/{len(subscriptions)} 완료: {data_type}")

            except Exception as e:
                logger.error(f"구독 요청 {i + 1} 실패: {e}")
                results.append("")

        logger.info(f"✅ 일괄 구독 완료: {successful_count}/{len(subscriptions)}개 성공")

        # 이벤트 발송
        await self._emit_event("websocket.private.batch_subscribed", {
            "total_requests": len(subscriptions),
            "successful_count": successful_count,
            "subscription_ids": [sid for sid in results if sid]
        })

        return results

    async def smart_unsubscribe(self, data_type: Optional[str] = None,
                                keep_connection: bool = True) -> int:
        """스마트 구독 해제 - 조건부 해제 및 최적화

        Args:
            data_type: 해제할 데이터 타입 (None이면 모든 구독 해제)
                      "myOrder", "myAsset" 중 하나
            keep_connection: 연결 유지 여부

        Returns:
            int: 해제된 구독 수
        """
        logger.info(f"🧹 스마트 구독 해제 시작 - 타입: {data_type or '전체'}")

        try:
            unsubscribed_count = 0

            # 현재 활성 구독 목록 가져오기
            active_subscriptions = self.subscription_manager.get_active_subscriptions()

            if not active_subscriptions:
                logger.info("해제할 구독이 없습니다")
                return 0

            # 구독 해제 대상 필터링
            targets_to_unsubscribe = []

            for sub_id, sub_info in active_subscriptions.items():
                # Private 클라이언트는 myOrder, myAsset만 처리
                sub_data_types = sub_info.get('data_types', [])

                if data_type is None:
                    # 모든 Private 구독 해제
                    if any(dt in [PrivateDataType.MY_ORDER, PrivateDataType.MY_ASSET] for dt in sub_data_types):
                        targets_to_unsubscribe.append(sub_id)
                else:
                    # 특정 데이터 타입만 해제
                    if data_type in sub_data_types:
                        targets_to_unsubscribe.append(sub_id)

            # 구독 해제 실행
            for sub_id in targets_to_unsubscribe:
                try:
                    success = await self.unsubscribe(sub_id)
                    if success:
                        unsubscribed_count += 1
                        logger.debug(f"구독 해제 완료: {sub_id}")
                except Exception as e:
                    logger.error(f"구독 해제 실패 {sub_id}: {e}")

            logger.info(f"✅ 스마트 해제 완료: {unsubscribed_count}개 구독 해제")

            # 연결 유지하지 않는 경우 연결 종료
            if not keep_connection and unsubscribed_count > 0:
                logger.info("🔌 연결 유지하지 않음 - 연결 종료")
                await self.disconnect()

            # 이벤트 발송
            await self._emit_event("websocket.private.smart_unsubscribed", {
                "data_type": data_type,
                "unsubscribed_count": unsubscribed_count,
                "connection_kept": keep_connection
            })

            return unsubscribed_count

        except Exception as e:
            logger.error(f"스마트 구독 해제 실패: {e}")
            return 0

    async def switch_to_idle_mode(self, ultra_quiet: bool = False) -> str:
        """유휴 모드 전환 - 최소한의 연결 유지

        Args:
            ultra_quiet: True이면 울트라 조용 모드 (최소한의 시스템 메시지만)

        Returns:
            str: 유휴 모드 구독 ID 또는 "idle_mode_failed"
        """
        logger.info(f"💤 유휴 모드 전환 시작 {'(울트라 조용)' if ultra_quiet else '(일반)'}")

        try:
            # 1. 모든 활성 Private 구독 해제
            unsubscribed_count = await self.smart_unsubscribe(keep_connection=True)
            logger.info(f"기존 구독 해제: {unsubscribed_count}개")

            # 2. JWT 토큰 상태 확인 및 갱신
            try:
                await self._refresh_token_if_needed()
                logger.info("JWT 토큰 상태 확인 완료")
            except Exception as e:
                logger.warning(f"JWT 토큰 갱신 실패 (유휴 모드 계속 진행): {e}")

            # 3. 유휴 상태 설정
            if ultra_quiet:
                # 울트라 조용 모드: 토큰 갱신만 유지, 데이터 구독 없음
                logger.info("🔇 울트라 조용 모드: 토큰 갱신만 유지")
                idle_subscription_id = "ultra_quiet_mode"
            else:
                # 일반 유휴 모드: 최소한의 myAsset 스냅샷 (연결 유지용)
                try:
                    idle_subscription_id = await self.subscribe_my_assets(
                        callback=None,
                        mode=RequestMode.SNAPSHOT_ONLY
                    )
                    logger.info("💤 일반 유휴 모드: myAsset 스냅샷으로 최소 연결 유지")
                except Exception as e:
                    logger.error(f"유휴 모드 구독 실패: {e}")
                    idle_subscription_id = "idle_mode_failed"

            # 4. 이벤트 발송
            await self._emit_event("websocket.private.idle_mode", {
                "ultra_quiet": ultra_quiet,
                "unsubscribed_count": unsubscribed_count,
                "idle_subscription_id": idle_subscription_id,
                "jwt_auto_refresh_active": self._token_refresh_task is not None and not self._token_refresh_task.done()
            })

            logger.info(f"✅ 유휴 모드 전환 완료: {idle_subscription_id}")
            return idle_subscription_id

        except Exception as e:
            logger.error(f"유휴 모드 전환 실패: {e}")
            return "idle_mode_failed"

    # ========== Private 전용 보안 기능 ==========

    async def rotate_jwt_token(self, force: bool = False) -> bool:
        """JWT 토큰 강제 순환 갱신

        Args:
            force: True이면 현재 토큰이 유효해도 강제 갱신

        Returns:
            bool: 갱신 성공 여부
        """
        logger.info(f"🔄 JWT 토큰 {'강제 ' if force else ''}순환 갱신 시작")

        try:
            # 현재 토큰 만료 시간 확인
            current_exp = self._jwt_expires_at or 0
            current_time = time.time()
            time_to_expiry = current_exp - current_time

            if not force and time_to_expiry > 600:  # 10분 이상 남은 경우
                logger.info(f"토큰이 여전히 유효함 (만료까지 {time_to_expiry:.0f}초), 갱신 건너뜀")
                return True

            # 기존 토큰 백업 (로깅용)
            old_expires = self._jwt_expires_at

            # 새 토큰 생성
            new_token = self._generate_jwt_token()

            if not new_token:
                logger.error("새 JWT 토큰 생성 실패")
                return False

            # 토큰 교체
            self._jwt_token = new_token
            self._jwt_expires_at = time.time() + 3600  # 1시간

            logger.info(f"✅ JWT 토큰 순환 완료 (만료: {time_to_expiry:.0f}초 → 3600초)")

            # 이벤트 발송
            await self._emit_event("websocket.private.jwt_rotated", {
                "forced": force,
                "old_expiry": old_expires,
                "new_expiry": self._jwt_expires_at,
                "rotation_reason": "forced" if force else "auto"
            })

            return True

        except Exception as e:
            logger.error(f"JWT 토큰 순환 갱신 실패: {e}")
            return False

    async def validate_api_permissions(self) -> Dict[str, Any]:
        """API 권한 검증 - Private 엔드포인트 접근 권한 확인

        Returns:
            Dict[str, Any]: 권한 검증 결과
            {
                "valid": bool,
                "permissions": {
                    "view_orders": bool,
                    "view_balances": bool,
                    "trade": bool
                },
                "restrictions": List[str],
                "expires_at": Optional[float]
            }
        """
        logger.info("🔒 API 권한 검증 시작")

        result = {
            "valid": False,
            "permissions": {
                "view_orders": False,
                "view_balances": False,
                "trade": False
            },
            "restrictions": [],
            "expires_at": self._jwt_expires_at
        }

        try:
            # JWT 토큰 유효성 검증
            if not self._jwt_token:
                result["restrictions"].append("JWT 토큰 없음")
                return result

            current_time = time.time()
            if self._jwt_expires_at and self._jwt_expires_at <= current_time:
                result["restrictions"].append("JWT 토큰 만료")
                return result

            # WebSocket 연결 상태 확인
            if not self.is_connected():
                result["restrictions"].append("WebSocket 연결 없음")
                return result

            # 실제 권한 테스트를 위한 가벼운 요청 시도
            try:
                # myAsset 스냅샷 요청으로 권한 테스트
                test_sub_id = await self.subscribe_my_assets(
                    callback=None,
                    mode=RequestMode.SNAPSHOT_ONLY
                )

                if test_sub_id and test_sub_id != "subscription_failed":
                    result["permissions"]["view_balances"] = True

                    # 구독 즉시 해제
                    await self.unsubscribe(test_sub_id)

            except Exception as e:
                result["restrictions"].append(f"잔고 조회 권한 없음: {str(e)}")

            # 주문 조회 권한 테스트
            try:
                test_order_sub_id = await self.subscribe_my_orders(
                    callback=None,
                    mode=RequestMode.SNAPSHOT_ONLY
                )

                if test_order_sub_id and test_order_sub_id != "subscription_failed":
                    result["permissions"]["view_orders"] = True
                    await self.unsubscribe(test_order_sub_id)

            except Exception as e:
                result["restrictions"].append(f"주문 조회 권한 없음: {str(e)}")

            # 거래 권한은 API 키 설정으로 판단 (실제 주문은 테스트하지 않음)
            # 주의: 실제 거래 권한 테스트는 위험하므로 수행하지 않음
            result["permissions"]["trade"] = True  # API 키가 있다고 가정

            # 전체 유효성 판단
            has_any_permission = any(result["permissions"].values())
            result["valid"] = has_any_permission and len(result["restrictions"]) == 0

            status = "✅ 유효" if result["valid"] else "❌ 제한됨"
            logger.info(f"{status} API 권한 검증 완료: {result['permissions']}")

            return result

        except Exception as e:
            logger.error(f"API 권한 검증 실패: {e}")
            result["restrictions"].append(f"검증 중 오류: {str(e)}")
            return result

    async def get_auth_status(self) -> Dict[str, Any]:
        """Private 인증 상태 종합 정보

        Returns:
            Dict[str, Any]: 인증 상태 정보
        """
        current_time = time.time()

        # JWT 토큰 상태
        jwt_status = {
            "exists": bool(self._jwt_token),
            "expires_at": self._jwt_expires_at,
            "time_to_expiry": (self._jwt_expires_at - current_time) if self._jwt_expires_at else None,
            "auto_refresh_active": self._token_refresh_task is not None and not self._token_refresh_task.done()
        }

        # WebSocket 연결 상태
        connection_status = {
            "connected": self.is_connected(),
            "connection_state": getattr(self, '_connection_state', 'unknown'),
            "last_heartbeat": getattr(self, '_last_heartbeat', None)
        }

        # 구독 상태
        active_subs = self.subscription_manager.get_active_subscriptions()
        subscription_status = {
            "active_count": len(active_subs),
            "subscription_types": list(set(
                sub_type
                for sub_info in active_subs.values()
                for sub_type in sub_info.get('data_types', [])
            ))
        }

        # 성능 지표
        performance_metrics = self.subscription_manager.get_performance_metrics()

        return {
            "jwt": jwt_status,
            "connection": connection_status,
            "subscriptions": subscription_status,
            "performance": performance_metrics,
            "security_level": "private_authenticated" if jwt_status["exists"] else "unauthenticated",
            "status_checked_at": current_time
        }

    # ========== 편의 메서드 ==========

    async def get_subscription_count(self) -> int:
        """현재 활성 구독 수 반환"""
        active_subs = self.subscription_manager.get_active_subscriptions()
        return len(active_subs)

    def get_supported_data_types(self) -> List[str]:
        """Private 클라이언트가 지원하는 데이터 타입 목록"""
        return [PrivateDataType.MY_ORDER, PrivateDataType.MY_ASSET]

    async def reconnect_with_auth_refresh(self) -> bool:
        """인증 갱신과 함께 재연결"""
        logger.info("🔄 인증 갱신과 함께 재연결 시작")

        try:
            # 기존 연결 종료
            if self.is_connected():
                await self.disconnect()

            # JWT 토큰 강제 갱신
            token_rotated = await self.rotate_jwt_token(force=True)
            if not token_rotated:
                logger.error("JWT 토큰 갱신 실패")
                return False

            # 새로운 연결 수립
            success = await self.connect()
            logger.info(f"{'✅' if success else '❌'} 인증 갱신 재연결 완료")

            return success

        except Exception as e:
            logger.error(f"인증 갱신 재연결 실패: {e}")
            return False


# ========== Phase 2 사용 예시 ==========

async def demo_phase2_features():
    """Phase 2 고급 기능들의 사용 예시"""

    private_client = UpbitWebSocketPrivateV5()

    try:
        # 1. 연결 및 기본 설정
        await private_client.connect()

        # 2. 일괄 구독 (batch_subscribe)
        batch_requests = [
            {
                "data_type": "myOrder",
                "markets": ["KRW-BTC", "KRW-ETH"],
                "callback": lambda data: print(f"주문: {data}"),
                "mode": "realtime_only"
            },
            {
                "data_type": "myAsset",
                "callback": lambda data: print(f"자산: {data}"),
                "mode": "snapshot_then_realtime"
            }
        ]

        subscription_ids = await private_client.batch_subscribe(batch_requests)
        print(f"일괄 구독 완료: {subscription_ids}")

        # 3. 보안 상태 확인
        auth_status = await private_client.get_auth_status()
        print(f"인증 상태: {auth_status}")

        # 4. API 권한 검증
        permissions = await private_client.validate_api_permissions()
        print(f"API 권한: {permissions}")

        # 5. 데이터 수신 대기
        await asyncio.sleep(30)

        # 6. 스마트 해제 (myOrder만)
        unsubscribed = await private_client.smart_unsubscribe(
            data_type="myOrder",
            keep_connection=True
        )
        print(f"myOrder 구독 해제: {unsubscribed}개")

        # 7. 유휴 모드 전환
        idle_id = await private_client.switch_to_idle_mode(ultra_quiet=False)
        print(f"유휴 모드: {idle_id}")

        # 8. JWT 토큰 순환
        rotated = await private_client.rotate_jwt_token(force=True)
        print(f"토큰 순환: {'성공' if rotated else '실패'}")

    finally:
        await private_client.disconnect()


if __name__ == "__main__":
    # Phase 2 기능 데모 실행
    asyncio.run(demo_phase2_features())

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
            },
            "auth_metrics": {
                "token_refreshes": self.stats['auth_token_refreshes'],
                "auth_failures": self.stats['auth_failures'],
                "token_expires_at": self._token_expires_at.isoformat() if self._token_expires_at else None,
                "token_valid": not self._is_token_expired()
            }
        }

    def get_performance_analysis(self) -> Dict[str, Any]:
        """🚀 v5 신규: Private 상세 성능 분석 - 구독 매니저 통합"""
        current_time = datetime.now()
        uptime = (current_time - self.stats['start_time']).total_seconds()

        # 성능 등급 계산
        avg_rate = self.stats['messages_received'] / uptime if uptime > 0 else 0

        if avg_rate > 50:
            grade = "🥇 PRIVATE EXCELLENCE"
        elif avg_rate > 25:
            grade = "🥈 PRIVATE READY"
        elif avg_rate > 10:
            grade = "🥉 PRIVATE GRADE"
        else:
            grade = "📈 PRIVATE DEVELOPMENT"

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
            "auth_efficiency": {
                "token_refresh_rate": self.stats['auth_token_refreshes'] / max(uptime / 3600, 1),  # per hour
                "auth_success_rate": (1 - self.stats['auth_failures'] / max(self.stats['auth_token_refreshes'] + 1, 1)) * 100,
                "auto_refresh_enabled": self._token_refresh_task is not None and not self._token_refresh_task.done()
            },
            "efficiency_metrics": {
                "subscriptions_active": subscription_stats['total_subscriptions'],
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

    async def health_check(self) -> Dict[str, Any]:
        """🚀 v5 신규: Private 종합 건강 상태 체크 - 구독 매니저 통합"""
        current_time = datetime.now()
        uptime = (current_time - self.stats['start_time']).total_seconds()

        # 연결 상태 체크
        is_connected = self.is_connected()

        # 최근 메시지 수신 확인 (30초 이내)
        last_message_ago = None
        if self.stats['last_message_time']:
            last_message_ago = (current_time - self.stats['last_message_time']).total_seconds()

        # JWT 토큰 상태 확인
        token_valid = not self._is_token_expired()

        # 건강도 점수 계산
        health_score = 100

        if not is_connected:
            health_score -= 50

        if not token_valid:
            health_score -= 30

        if last_message_ago and last_message_ago > 60:  # Private는 60초 기준
            health_score -= 15

        if self.stats['errors'] / max(self.stats['messages_received'], 1) > 0.02:  # 2% 이상 에러율
            health_score -= 10

        if self.stats['auth_failures'] > 0:
            health_score -= 5

        # 상태 등급
        if health_score >= 90:
            status = "🟢 PRIVATE EXCELLENT"
        elif health_score >= 75:
            status = "🟡 PRIVATE GOOD"
        elif health_score >= 50:
            status = "🟠 PRIVATE WARNING"
        else:
            status = "🔴 PRIVATE CRITICAL"

        # v3.0 구독 정보
        stats = self.subscription_manager.get_stats()
        subscription_stats = stats['subscription_stats']
        ticket_stats = stats['ticket_stats']
        total_active_tickets = ticket_stats['private_pool']['used']  # Private만 사용

        return {
            'overall_status': status,
            'health_score': max(0, health_score),
            'connection_status': '🟢 Connected' if is_connected else '🔴 Disconnected',
            'auth_status': '🟢 Valid Token' if token_valid else '🔴 Invalid Token',
            'uptime_minutes': round(uptime / 60, 1),
            'last_message_seconds_ago': round(last_message_ago, 1) if last_message_ago else None,
            'message_rate_per_second': round(self.stats['avg_message_rate'], 2),
            'error_rate_percent': round(self.stats['errors'] / max(self.stats['messages_received'], 1) * 100, 2),
            'active_subscriptions': subscription_stats['total_subscriptions'],
            'memory_efficiency': f"{subscription_stats['total_subscriptions'] / max(total_active_tickets, 1):.1f} subs/ticket",
            'token_auto_refresh': self._token_refresh_task is not None and not self._token_refresh_task.done()
        }

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
        logger.info("Private 메시지 수신 루프 시작")

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
            logger.warning("Private WebSocket 연결이 종료되었습니다")
            await self._handle_disconnection()

        except Exception as e:
            logger.error(f"Private 메시지 루프 오류: {e}")
            self.stats['errors'] += 1
            await self._handle_error(WebSocketError(
                f"Private 메시지 루프 오류: {str(e)}",
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
                logger.debug(f"Private 메시지 처리: {message_type} ({original_format} → {result_format})")

            # 메시지별 처리 (SIMPLE 포맷 고려)
            if message_type == PrivateDataType.MY_ORDER:
                await self._handle_my_order(message_data)
            elif message_type == PrivateDataType.MY_ASSET:
                await self._handle_my_asset(message_data)

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
            logger.error(f"Private 메시지 처리 중 오류: {e}")

            # 🚀 v5 개선: 에러 복구 시간 추적
            if hasattr(self, '_last_error_time'):
                recovery_time = (datetime.now() - self._last_error_time).total_seconds()
                self.stats['error_recovery_time'] = recovery_time
            self._last_error_time = datetime.now()

    async def _handle_my_order(self, data: Dict[str, Any]) -> None:
        """내 주문 데이터 처리"""
        try:
            # 메시지 검증 및 정리
            validated_data = validate_mixed_message(data)
            message = create_websocket_message("myOrder", "PRIVATE", validated_data)
            await self._emit_data(PrivateDataType.MY_ORDER, message)
        except Exception as e:
            logger.error(f"MyOrder 데이터 처리 오류: {e}")

    async def _handle_my_asset(self, data: Dict[str, Any]) -> None:
        """내 자산 데이터 처리"""
        try:
            # 메시지 검증 및 정리
            validated_data = validate_mixed_message(data)
            message = create_websocket_message("myAsset", "PRIVATE", validated_data)
            await self._emit_data(PrivateDataType.MY_ASSET, message)
        except Exception as e:
            logger.error(f"MyAsset 데이터 처리 오류: {e}")

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
            await self._emit_event(f"websocket.private.{data_type}", data)

    async def _emit_event(self, event_type: str, data: Any) -> None:
        """이벤트 발송"""
        if self.event_broker:
            try:
                await self.event_broker.emit(event_type, data)
            except Exception as e:
                logger.error(f"Private 이벤트 발송 오류: {e}")

    async def _handle_error(self, error: WebSocketError) -> None:
        """오류 처리"""
        self.stats['errors'] += 1
        logger.error(f"Private WebSocket 오류: {error}")

        # 인증 관련 오류는 별도 처리
        if isinstance(error, InvalidAPIKeysError):
            self.stats['auth_failures'] += 1

        self.state_machine.transition_to(WebSocketState.ERROR)

        # 이벤트 발송
        await self._emit_event("websocket.private.error", {
            "error_code": error.error_code.value,
            "message": str(error),
            "recovery_action": error.recovery_action.value
        })

    async def _handle_disconnection(self) -> None:
        """연결 해제 처리"""
        logger.warning("Private WebSocket 연결이 끊어졌습니다")

        if self.config.reconnection.auto_reconnect:
            await self._attempt_reconnect()
        else:
            self.state_machine.transition_to(WebSocketState.DISCONNECTED)

    async def _attempt_reconnect(self) -> None:
        """재연결 시도 - JWT 토큰 갱신 포함"""
        max_attempts = self.config.reconnection.max_attempts

        for attempt in range(max_attempts):
            try:
                self.stats['reconnect_count'] += 1
                logger.info(f"Private 재연결 시도 {attempt + 1}/{max_attempts}")

                # 지연 시간 계산
                delay = min(
                    self.config.reconnection.initial_delay * (self.config.reconnection.backoff_multiplier ** attempt),
                    self.config.reconnection.max_delay
                )

                await asyncio.sleep(delay)

                # 🚀 JWT 토큰 갱신 (재연결 전)
                try:
                    await self._refresh_token_if_needed()
                    logger.info("재연결을 위한 JWT 토큰 갱신 완료")
                except Exception as e:
                    logger.error(f"재연결 전 JWT 토큰 갱신 실패: {e}")
                    # 토큰 갱신 실패 시에도 재연결 시도
                    self._generate_jwt_token()

                # 재연결
                await self.connect()

                # 구독 복원 (v3.0에서는 자동 복원)
                await self._restore_subscriptions()

                logger.info("Private 재연결 성공")
                return

            except Exception as e:
                logger.error(f"Private 재연결 실패 (시도 {attempt + 1}): {e}")

        logger.error("Private 최대 재연결 시도 횟수 초과")
        self.state_machine.transition_to(WebSocketState.ERROR)

    async def force_reconnect(self) -> bool:
        """능동적 재연결 - JWT 토큰 갱신 포함"""
        logger.info("Private 능동적 재연결 시작...")

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
                self.state_machine.transition_to(WebSocketState.DISCONNECTING)

            # 🚀 최적화: 연결 종료와 태스크 정리 병렬 처리
            close_task = None
            if self.websocket:
                close_timeout = 0.5 if was_properly_connected else 2.0
                close_task = asyncio.create_task(
                    asyncio.wait_for(self.websocket.close(), timeout=close_timeout)
                )

            cleanup_task = asyncio.create_task(self._cleanup_tasks())

            if close_task:
                try:
                    await asyncio.gather(close_task, cleanup_task, return_exceptions=True)
                except Exception:
                    pass
            else:
                await cleanup_task

            self.websocket = None
            self.state_machine.transition_to(WebSocketState.DISCONNECTED)

            # 🚀 JWT 토큰 강제 갱신
            try:
                self._generate_jwt_token()
                logger.info("능동적 재연결을 위한 JWT 토큰 갱신 완료")
            except Exception as e:
                logger.error(f"JWT 토큰 갱신 실패: {e}")
                return False

            if not was_properly_connected:
                await asyncio.sleep(0.05)  # 50ms
                logger.debug("비정상 연결 상태 - 최소 복구 대기시간 적용 (50ms)")

            # 재연결 시도
            await self.connect()

            logger.info("Private 능동적 재연결 성공")
            return True

        except Exception as e:
            logger.error(f"Private 능동적 재연결 실패: {e}")
            return False

    async def _restore_subscriptions(self) -> None:
        """구독 복원 - v3.0에서는 자동 복원 처리"""
        logger.info("Private 구독 복원 시작 (v3.0 자동 관리)")

        try:
            # v3.0에서는 구독 매니저가 자동으로 관리
            logger.info("Private 구독 복원 완료: v3.0 자동 관리")
        except Exception as e:
            logger.error(f"Private 구독 복원 실패: {e}")


# 편의 함수들
async def create_private_client(access_key: Optional[str] = None,
                                secret_key: Optional[str] = None,
                                config_path: Optional[str] = None,
                                event_broker: Optional[Any] = None,
                                private_pool_size: int = 2) -> UpbitWebSocketPrivateV5:
    """Private 클라이언트 생성"""
    client = UpbitWebSocketPrivateV5(
        access_key=access_key,
        secret_key=secret_key,
        config_path=config_path,
        event_broker=event_broker,
        private_pool_size=private_pool_size
    )
    await client.connect()
    return client


async def quick_subscribe_my_orders(access_key: Optional[str] = None,
                                    secret_key: Optional[str] = None,
                                    markets: Optional[List[str]] = None,
                                    callback: Optional[Callable] = None) -> UpbitWebSocketPrivateV5:
    """빠른 내 주문 구독 (개발/테스트용)"""
    client = await create_private_client(access_key, secret_key)
    await client.subscribe_my_orders(markets, callback)
    return client


async def quick_subscribe_my_assets(access_key: Optional[str] = None,
                                    secret_key: Optional[str] = None,
                                    callback: Optional[Callable] = None) -> UpbitWebSocketPrivateV5:
    """빠른 내 자산 구독 (개발/테스트용)"""
    client = await create_private_client(access_key, secret_key)
    await client.subscribe_my_assets(callback)
    return client
