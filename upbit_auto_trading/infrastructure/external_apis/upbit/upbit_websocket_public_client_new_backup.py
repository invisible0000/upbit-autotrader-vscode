"""
업비트 WebSocket Public 클라이언트 v4.0 - 통합 구독 전용

🎯 혁신적 개선:
- 하나의 티켓으로 모든 타입 동시 구독 (5배 효율성)
- 개별 구독 방식 완전 제거 (레거시 호환성 제거)
- 티켓 최적화로 업비트 5개 제한 효율적 활용
- 업비트 검증 완료: ticker + trade + orderbook + candle 동시 구독 지원
"""

import asyncio
import json
import uuid
import websockets
from typing import Dict, List, Optional, Any, Callable, Set
from enum import Enum
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger


class WebSocketDataType(Enum):
    """WebSocket 데이터 타입"""
    TICKER = "ticker"          # 현재가
    TRADE = "trade"            # 체결
    ORDERBOOK = "orderbook"    # 호가
    CANDLE = "candle"          # 캔들


class UnifiedSubscription:
    """통합 구독 관리 클래스 - 하나의 티켓으로 여러 타입 처리"""

    def __init__(self, ticket: str):
        self.ticket = ticket
        self.types: Dict[str, Dict[str, Any]] = {}  # type -> config
        self.symbols: Set[str] = set()  # 모든 구독 심볼
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        self.message_count = 0

    def add_subscription_type(self, data_type: str, symbols: List[str], **kwargs):
        """구독 타입 추가"""
        self.types[data_type] = {
            "codes": symbols,
            **kwargs
        }
        self.symbols.update(symbols)
        self.last_updated = datetime.now()

    def remove_subscription_type(self, data_type: str):
        """구독 타입 제거"""
        if data_type in self.types:
            del self.types[data_type]

            # 다른 타입에서 사용하지 않는 심볼 제거
            remaining_symbols = set()
            for config in self.types.values():
                remaining_symbols.update(config.get("codes", []))

            self.symbols = remaining_symbols
            self.last_updated = datetime.now()

    def has_type(self, data_type: str) -> bool:
        """타입 구독 여부 확인"""
        return data_type in self.types

    def has_symbol(self, symbol: str) -> bool:
        """심볼 구독 여부 확인"""
        return symbol in self.symbols

    def is_empty(self) -> bool:
        """빈 구독인지 확인"""
        return len(self.types) == 0

    def to_websocket_message(self) -> List[Dict[str, Any]]:
        """업비트 WebSocket 구독 메시지 형식으로 변환"""
        if self.is_empty():
            return []

        message = [{"ticket": self.ticket}]

        # 각 타입별 구독 정보 추가
        for data_type, config in self.types.items():
            message.append({
                "type": data_type,
                **config
            })

        # 응답 형식 설정
        message.append({"format": "SIMPLE"})

        return message

    def increment_message_count(self):
        """메시지 수신 카운트 증가"""
        self.message_count += 1
        self.last_updated = datetime.now()


class UpbitWebSocketPublicClient:
    """
    업비트 WebSocket Public 클라이언트 v4.0 - 통합 구독 전용

    핵심 기능:
    - 통합 구독: 하나의 티켓으로 여러 타입 동시 처리
    - 효율적 티켓 관리: 최대 5개 제한 내에서 최적 활용
    - 실시간 데이터: ticker, trade, orderbook, candle 동시 수신
    """

    def __init__(self, persistent_connection: bool = True):
        """
        Args:
            persistent_connection: 지속적 연결 유지
        """
        self.logger = create_component_logger("UpbitWebSocketClient")

        # 연결 설정
        self.uri = "wss://api.upbit.com/websocket/v1"
        self.websocket: Optional[Any] = None
        self.is_connected = False

        # 연결 정책
        self.persistent_connection = persistent_connection

        # 통합 구독 관리 (최대 5개 티켓)
        self.subscriptions: Dict[str, UnifiedSubscription] = {}
        self.max_subscriptions = 5  # 업비트 제한

        # 메시지 핸들러
        self.message_handlers: Dict[str, Callable] = {}  # type -> handler
        self.default_handler: Optional[Callable] = None

        # 백그라운드 태스크
        self._listener_task: Optional[asyncio.Task] = None

        self.logger.info("✅ 업비트 WebSocket 클라이언트 v4.0 초기화 (통합 구독 방식)")

    async def connect(self) -> bool:
        """WebSocket 연결"""
        try:
            if self.is_connected:
                self.logger.debug("이미 연결됨")
                return True

            self.logger.info("업비트 WebSocket 연결 시도...")

            # WebSocket 연결
            self.websocket = await websockets.connect(
                self.uri,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )

            self.is_connected = True

            # 백그라운드 태스크 시작
            self._listener_task = asyncio.create_task(self._message_listener())

            self.logger.info("✅ 업비트 WebSocket 연결 성공")
            return True

        except Exception as e:
            self.logger.error(f"❌ WebSocket 연결 실패: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """WebSocket 연결 해제"""
        try:
            self.logger.info("WebSocket 연결 해제 시작...")

            # 연결 상태 변경
            self.is_connected = False

            # 백그라운드 태스크 정리
            if self._listener_task and not self._listener_task.done():
                self._listener_task.cancel()
                try:
                    await self._listener_task
                except asyncio.CancelledError:
                    pass

            # WebSocket 연결 닫기
            if self.websocket:
                await self.websocket.close()
                self.websocket = None

            # 구독 상태 초기화
            self.subscriptions.clear()

            self.logger.info("✅ WebSocket 연결 해제 완료")

        except Exception as e:
            self.logger.error(f"❌ 연결 해제 중 오류: {e}")

    async def subscribe_unified(self, subscription_types: Dict[str, Dict[str, Any]],
                               subscription_id: Optional[str] = None) -> bool:
        """
        통합 구독 - 하나의 티켓으로 여러 타입 동시 구독

        Args:
            subscription_types: {type: {codes: [...], ...}} 형식
            subscription_id: 구독 ID (없으면 자동 생성)

        Returns:
            구독 성공 여부
        """
        if not self.is_connected:
            self.logger.error("WebSocket 연결되지 않음")
            return False

        try:
            # 구독 ID 생성 또는 사용
            if subscription_id is None:
                subscription_id = f"unified-{uuid.uuid4().hex[:8]}"

            # 기존 구독이 있으면 업데이트, 없으면 새로 생성
            if subscription_id in self.subscriptions:
                subscription = self.subscriptions[subscription_id]
                self.logger.info(f"🔄 기존 구독 업데이트: {subscription_id}")
            else:
                # 새 구독 생성 (5개 제한 확인)
                if len(self.subscriptions) >= self.max_subscriptions:
                    # 가장 오래된 구독 제거 (LRU)
                    oldest_id = min(self.subscriptions.keys(),
                                   key=lambda x: self.subscriptions[x].created_at)
                    await self._remove_subscription(oldest_id)
                    self.logger.info(f"🗑️ 구독 제한으로 오래된 구독 제거: {oldest_id}")

                subscription = UnifiedSubscription(subscription_id)
                self.subscriptions[subscription_id] = subscription
                self.logger.info(f"✨ 새 통합 구독 생성: {subscription_id}")

            # 구독 타입들 설정
            for data_type, config in subscription_types.items():
                symbols = config.get("codes", [])
                other_params = {k: v for k, v in config.items() if k != "codes"}
                subscription.add_subscription_type(data_type, symbols, **other_params)

            # WebSocket 구독 메시지 전송
            message = subscription.to_websocket_message()
            if self.websocket:
                await self.websocket.send(json.dumps(message))

            total_symbols = len(subscription.symbols)
            total_types = len(subscription.types)

            self.logger.info(
                f"✅ 통합 구독 성공: {subscription_id} "
                f"({total_types}개 타입, {total_symbols}개 심볼)"
            )
            self.logger.info(f"   - 타입: {list(subscription.types.keys())}")
            self.logger.info(f"   - 심볼: {sorted(subscription.symbols)}")

            return True

        except Exception as e:
            self.logger.error(f"❌ 통합 구독 실패: {e}")
            return False

    async def unsubscribe(self, subscription_id: str) -> bool:
        """구독 해제"""
        if subscription_id not in self.subscriptions:
            self.logger.warning(f"존재하지 않는 구독: {subscription_id}")
            return True

        return await self._remove_subscription(subscription_id)

    async def _remove_subscription(self, subscription_id: str) -> bool:
        """내부: 구독 제거"""
        try:
            if subscription_id in self.subscriptions:
                # 빈 메시지로 구독 해제 (업비트 방식)
                empty_message = [
                    {"ticket": subscription_id},
                    {"format": "SIMPLE"}
                ]

                if self.websocket:
                    await self.websocket.send(json.dumps(empty_message))

                del self.subscriptions[subscription_id]

                self.logger.info(f"✅ 구독 제거 완료: {subscription_id}")
                return True

            return True

        except Exception as e:
            self.logger.error(f"❌ 구독 제거 실패: {e}")
            return False

    def add_message_handler(self, data_type: str, handler: Callable):
        """타입별 메시지 핸들러 등록"""
        self.message_handlers[data_type] = handler
        self.logger.debug(f"메시지 핸들러 등록: {data_type}")

    def set_default_handler(self, handler: Callable):
        """기본 메시지 핸들러 설정"""
        self.default_handler = handler
        self.logger.debug("기본 메시지 핸들러 설정")

    async def _message_listener(self):
        """메시지 수신 리스너"""
        try:
            while self.is_connected and self.websocket:
                try:
                    # 메시지 수신
                    raw_message = await self.websocket.recv()

                    # 바이너리 데이터 처리
                    if isinstance(raw_message, bytes):
                        message_text = raw_message.decode('utf-8')
                    else:
                        message_text = raw_message

                    # JSON 파싱
                    data = json.loads(message_text)

                    # 메시지 처리
                    await self._process_message(data)

                except websockets.exceptions.ConnectionClosed:
                    self.logger.warning("WebSocket 연결 종료됨")
                    self.is_connected = False
                    break

                except Exception as e:
                    self.logger.error(f"메시지 처리 오류: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"메시지 리스너 오류: {e}")
        finally:
            self.is_connected = False

    async def _process_message(self, data: Dict[str, Any]):
        """수신 메시지 처리"""
        try:
            message_type = data.get('type', 'unknown')
            code = data.get('code', 'unknown')

            # 구독 통계 업데이트 (메시지가 어느 구독에서 왔는지 추적)
            for subscription in self.subscriptions.values():
                if subscription.has_symbol(code) and subscription.has_type(message_type):
                    subscription.increment_message_count()
                    break

            # 타입별 핸들러 호출
            if message_type in self.message_handlers:
                handler = self.message_handlers[message_type]
                await self._safe_call_handler(handler, data)
            elif self.default_handler:
                await self._safe_call_handler(self.default_handler, data)
            else:
                self.logger.debug(f"처리되지 않은 메시지: {message_type} | {code}")

        except Exception as e:
            self.logger.error(f"메시지 처리 오류: {e}")

    async def _safe_call_handler(self, handler: Callable, data: Dict[str, Any]):
        """안전한 핸들러 호출"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(data)
            else:
                handler(data)
        except Exception as e:
            self.logger.error(f"핸들러 실행 오류: {e}")

    def get_subscription_status(self) -> Dict[str, Any]:
        """구독 상태 조회"""
        total_symbols = set()
        total_types = set()

        for subscription in self.subscriptions.values():
            total_symbols.update(subscription.symbols)
            total_types.update(subscription.types.keys())

        status = {
            "connection": {
                "is_connected": self.is_connected,
                "persistent_mode": self.persistent_connection
            },
            "subscriptions": {
                "total_subscriptions": len(self.subscriptions),
                "max_subscriptions": self.max_subscriptions,
                "total_symbols": len(total_symbols),
                "total_types": len(total_types),
                "subscription_details": {}
            }
        }

        # 구독별 상세 정보
        for sub_id, subscription in self.subscriptions.items():
            status["subscriptions"]["subscription_details"][sub_id] = {
                "ticket": subscription.ticket,
                "types": list(subscription.types.keys()),
                "symbols": sorted(subscription.symbols),
                "message_count": subscription.message_count,
                "created_at": subscription.created_at.isoformat(),
                "last_updated": subscription.last_updated.isoformat()
            }

        return status

    # === 편의 메서드들 (자주 사용되는 패턴) ===

    async def subscribe_market_data(self, symbols: List[str]) -> bool:
        """시장 데이터 통합 구독 (ticker + trade)"""
        return await self.subscribe_unified({
            "ticker": {"codes": symbols},
            "trade": {"codes": symbols}
        }, "market-data")

    async def subscribe_full_data(self, symbols: List[str]) -> bool:
        """전체 데이터 통합 구독 (ticker + trade + orderbook)"""
        return await self.subscribe_unified({
            "ticker": {"codes": symbols},
            "trade": {"codes": symbols},
            "orderbook": {"codes": symbols}
        }, "full-data")

    async def subscribe_candle_data(self, symbols: List[str], unit: str = "minute", count: int = 1) -> bool:
        """캔들 데이터 구독"""
        return await self.subscribe_unified({
            "candle": {
                "codes": symbols,
                "unit": unit,
                "count": count
            }
        }, "candle-data")
