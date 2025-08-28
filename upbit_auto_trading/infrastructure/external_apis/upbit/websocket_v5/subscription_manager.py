"""
업비트 WebSocket v5.0 - 통합 구독 시스템 v3.0

🎯 핵심 설계 원칙:
1. WebSocket 1개 → Streams 5개 (Public 3개 + Private 2개)
2. Subscription = 요청들의 집합 (어떤 티켓 사용할지 결정)
3. 기본 티켓 자동 관리 (사용자가 별도 요청시에만 새 티켓)
4. 모든 구독이 혼합 타입 지원 (ticker+trade+orderbook+candle)
5. 스냅샷/리얼타임 개별 요청별 설정 가능

🔧 구조:
- TicketManager: 5개 티켓 풀 관리 (Public 3 + Private 2)
- Subscription: 단일/혼합 구분 없이 통합 처리
- MessageRouter: 수신 메시지 타입별 분배
- CallbackSystem: 유연한 콜백 등록/실행
"""

from typing import Dict, List, Optional, Any, Callable, Union, Set
from datetime import datetime
import uuid
import json
import asyncio
from enum import Enum
from dataclasses import dataclass, field

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .models import infer_message_type
from .config import load_config

logger = create_component_logger("SubscriptionManagerV3")


# =====================================================================
# 1. 기본 타입 및 열거형
# =====================================================================

class TicketPoolType(str, Enum):
    """티켓 풀 타입 - Public/Private 구분"""
    PUBLIC = "public"
    PRIVATE = "private"


class RequestMode(str, Enum):
    """요청 모드"""
    SNAPSHOT_ONLY = "snapshot_only"      # 스냅샷만
    REALTIME_ONLY = "realtime_only"      # 리얼타임만
    SNAPSHOT_THEN_REALTIME = "snapshot_then_realtime"  # 스냅샷 후 리얼타임 (기본)


@dataclass
class DataRequest:
    """개별 데이터 요청"""
    data_type: str
    symbols: List[str]
    mode: RequestMode = RequestMode.SNAPSHOT_THEN_REALTIME
    options: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """검증"""
        if not self.data_type or not self.symbols:
            raise ValueError("data_type과 symbols는 필수입니다")

    def to_websocket_format(self) -> Dict[str, Any]:
        """WebSocket 메시지 형식으로 변환"""
        config = {
            "type": self.data_type,
            "codes": self.symbols
        }

        # 모드별 설정
        if self.mode == RequestMode.SNAPSHOT_ONLY:
            config["is_only_snapshot"] = True
        elif self.mode == RequestMode.REALTIME_ONLY:
            config["is_only_realtime"] = True
        # SNAPSHOT_THEN_REALTIME는 기본값이므로 별도 설정 불필요

        # 캔들 타입 특별 처리 제거 - 업비트 API는 type에 이미 간격이 포함됨
        # candle.1s, candle.1m 등의 형태로 type만 설정하면 충분

        # 추가 옵션 병합 (unit 제외 - 업비트 WebSocket API는 type 필드에 이미 간격 포함)
        filtered_options = {k: v for k, v in self.options.items() if k != "unit"}
        config.update(filtered_options)
        return config


# =====================================================================
# 2. 티켓 관리자
# =====================================================================

class TicketManager:
    """통합 티켓 관리자 - Public 3개 + Private 2개"""

    def __init__(self, public_pool_size: int = 3, private_pool_size: int = 2):
        self.public_pool_size = public_pool_size
        self.private_pool_size = private_pool_size

        # 티켓 풀
        self.public_tickets: Dict[str, Dict[str, Any]] = {}
        self.private_tickets: Dict[str, Dict[str, Any]] = {}

        # 기본 티켓
        self.default_public_ticket: Optional[str] = None
        self.default_private_ticket: Optional[str] = None

        # 티켓 생성 카운터
        self._public_counter = 1
        self._private_counter = 1

        logger.info(f"티켓 관리자 초기화 - Public: {public_pool_size}, Private: {private_pool_size}")

    def get_default_ticket(self, pool_type: TicketPoolType) -> str:
        """기본 티켓 획득 (자동 생성)"""
        if pool_type == TicketPoolType.PUBLIC:
            if not self.default_public_ticket:
                self.default_public_ticket = self._create_ticket(TicketPoolType.PUBLIC, purpose="default")
            return self.default_public_ticket or ""
        else:
            if not self.default_private_ticket:
                self.default_private_ticket = self._create_ticket(TicketPoolType.PRIVATE, purpose="default")
            return self.default_private_ticket or ""

    def create_dedicated_ticket(self, pool_type: TicketPoolType, purpose: str = "dedicated") -> Optional[str]:
        """전용 티켓 생성 (사용자 요청시)"""
        return self._create_ticket(pool_type, purpose)

    def _create_ticket(self, pool_type: TicketPoolType, purpose: str) -> Optional[str]:
        """티켓 생성"""
        if pool_type == TicketPoolType.PUBLIC:
            if len(self.public_tickets) >= self.public_pool_size:
                logger.warning(f"Public 티켓 풀 한계 도달: {len(self.public_tickets)}/{self.public_pool_size}")
                return None

            ticket_id = f"pub_{self._public_counter:03d}_{uuid.uuid4().hex[:6]}"
            self._public_counter += 1
            self.public_tickets[ticket_id] = {
                "purpose": purpose,
                "created_at": datetime.now(),
                "request_count": 0,
                "data_types": set(),
                "symbols": set(),
                "is_default": purpose == "default"
            }
        else:
            if len(self.private_tickets) >= self.private_pool_size:
                logger.warning(f"Private 티켓 풀 한계 도달: {len(self.private_tickets)}/{self.private_pool_size}")
                return None

            ticket_id = f"prv_{self._private_counter:03d}_{uuid.uuid4().hex[:6]}"
            self._private_counter += 1
            self.private_tickets[ticket_id] = {
                "purpose": purpose,
                "created_at": datetime.now(),
                "request_count": 0,
                "data_types": set(),
                "symbols": set(),
                "is_default": purpose == "default"
            }

        logger.debug(f"티켓 생성: {ticket_id} ({pool_type.value}, {purpose})")
        return ticket_id

    def update_ticket_usage(self, ticket_id: str, data_types: List[str], symbols: List[str]) -> None:
        """티켓 사용량 업데이트"""
        ticket_pool = self.public_tickets if ticket_id.startswith("pub_") else self.private_tickets

        if ticket_id in ticket_pool:
            ticket_pool[ticket_id]["request_count"] += 1
            ticket_pool[ticket_id]["data_types"].update(data_types)
            ticket_pool[ticket_id]["symbols"].update(symbols)

    def release_ticket(self, ticket_id: str) -> bool:
        """티켓 해제 (기본 티켓은 해제 불가)"""
        if ticket_id == self.default_public_ticket or ticket_id == self.default_private_ticket:
            logger.warning(f"기본 티켓은 해제할 수 없습니다: {ticket_id}")
            return False

        if ticket_id in self.public_tickets:
            del self.public_tickets[ticket_id]
            logger.debug(f"Public 티켓 해제: {ticket_id}")
            return True
        elif ticket_id in self.private_tickets:
            del self.private_tickets[ticket_id]
            logger.debug(f"Private 티켓 해제: {ticket_id}")
            return True

        return False

    def get_available_tickets(self, exclude_default: bool = False) -> Dict[str, Any]:
        """사용 가능한 티켓 목록 (기본 티켓 제외 옵션)"""
        result = {
            "public": {},
            "private": {}
        }

        for ticket_id, info in self.public_tickets.items():
            if exclude_default and info.get("is_default", False):
                continue
            result["public"][ticket_id] = {
                "purpose": info["purpose"],
                "request_count": info["request_count"],
                "data_types": list(info["data_types"]),
                "symbol_count": len(info["symbols"])
            }

        for ticket_id, info in self.private_tickets.items():
            if exclude_default and info.get("is_default", False):
                continue
            result["private"][ticket_id] = {
                "purpose": info["purpose"],
                "request_count": info["request_count"],
                "data_types": list(info["data_types"]),
                "symbol_count": len(info["symbols"])
            }

        return result

    def get_stats(self) -> Dict[str, Any]:
        """티켓 사용 통계"""
        return {
            "public_pool": {
                "total_capacity": self.public_pool_size,
                "used": len(self.public_tickets),
                "available": self.public_pool_size - len(self.public_tickets),
                "utilization_percent": len(self.public_tickets) / self.public_pool_size * 100
            },
            "private_pool": {
                "total_capacity": self.private_pool_size,
                "used": len(self.private_tickets),
                "available": self.private_pool_size - len(self.private_tickets),
                "utilization_percent": len(self.private_tickets) / self.private_pool_size * 100
            },
            "total_tickets": len(self.public_tickets) + len(self.private_tickets),
            "max_total_tickets": self.public_pool_size + self.private_pool_size
        }


# =====================================================================
# 3. 구독 클래스 (통합형)
# =====================================================================

class Subscription:
    """통합 구독 클래스 - 단일/혼합 구분 없음"""

    def __init__(self, subscription_id: str, ticket_id: str, pool_type: TicketPoolType):
        self.subscription_id = subscription_id
        self.ticket_id = ticket_id
        self.pool_type = pool_type
        self.requests: List[DataRequest] = []
        self.created_at = datetime.now()
        self.message_count = 0
        self.last_message_at: Optional[datetime] = None
        self.is_active = True

    def add_request(self, request: DataRequest) -> None:
        """요청 추가"""
        self.requests.append(request)

    def remove_request(self, data_type: str, symbols: Optional[List[str]] = None) -> bool:
        """요청 제거"""
        original_count = len(self.requests)

        if symbols:
            # 특정 심볼만 제거
            self.requests = [
                req for req in self.requests
                if not (req.data_type == data_type and any(symbol in req.symbols for symbol in symbols))
            ]
        else:
            # 데이터 타입 전체 제거
            self.requests = [req for req in self.requests if req.data_type != data_type]

        return len(self.requests) < original_count

    def get_websocket_message(self) -> List[Dict[str, Any]]:
        """WebSocket 메시지 생성"""
        if not self.requests:
            raise ValueError("구독에 요청이 없습니다")

        message = [{"ticket": self.ticket_id}]

        # 각 요청을 메시지에 추가
        for request in self.requests:
            message.append(request.to_websocket_format())

        # 포맷 설정
        message.append({"format": "DEFAULT"})
        return message

    def get_all_symbols(self) -> Set[str]:
        """모든 심볼 집합"""
        symbols = set()
        for request in self.requests:
            symbols.update(request.symbols)
        return symbols

    def get_all_data_types(self) -> Set[str]:
        """모든 데이터 타입 집합"""
        return {request.data_type for request in self.requests}

    def handles_message(self, message_type: str, symbol: str) -> bool:
        """메시지 처리 여부 확인"""
        for request in self.requests:
            if request.data_type == message_type and symbol in request.symbols:
                return True
        return False

    def update_message_stats(self) -> None:
        """메시지 통계 업데이트"""
        self.message_count += 1
        self.last_message_at = datetime.now()

    def get_info(self) -> Dict[str, Any]:
        """구독 정보"""
        return {
            "subscription_id": self.subscription_id,
            "ticket_id": self.ticket_id,
            "pool_type": self.pool_type.value,
            "request_count": len(self.requests),
            "data_types": list(self.get_all_data_types()),
            "symbol_count": len(self.get_all_symbols()),
            "symbols": list(self.get_all_symbols()),
            "message_count": self.message_count,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None
        }


# =====================================================================
# 4. 메시지 라우터
# =====================================================================

class MessageRouter:
    """수신 메시지 타입별 분배"""

    def __init__(self):
        self.type_callbacks: Dict[str, List[Callable]] = {}
        self.global_callbacks: List[Callable] = []
        self.subscription_callbacks: Dict[str, List[Callable]] = {}  # 구독별 콜백

    def register_type_callback(self, data_type: str, callback: Callable) -> None:
        """타입별 콜백 등록"""
        if data_type not in self.type_callbacks:
            self.type_callbacks[data_type] = []
        self.type_callbacks[data_type].append(callback)

    def register_global_callback(self, callback: Callable) -> None:
        """전역 콜백 등록"""
        self.global_callbacks.append(callback)

    def register_subscription_callback(self, subscription_id: str, callback: Callable) -> None:
        """구독별 콜백 등록"""
        if subscription_id not in self.subscription_callbacks:
            self.subscription_callbacks[subscription_id] = []
        self.subscription_callbacks[subscription_id].append(callback)

    def unregister_subscription_callbacks(self, subscription_id: str) -> None:
        """구독 콜백 해제"""
        if subscription_id in self.subscription_callbacks:
            del self.subscription_callbacks[subscription_id]

    async def route_message(self, message_data: Dict[str, Any],
                            handling_subscriptions: Optional[List[str]] = None) -> None:
        """메시지 라우팅"""
        message_type = message_data.get("type", "")

        # 타입별 콜백 실행
        await self._execute_callbacks(self.type_callbacks.get(message_type, []), message_data)

        # 구독별 콜백 실행
        if handling_subscriptions:
            for sub_id in handling_subscriptions:
                callbacks = self.subscription_callbacks.get(sub_id, [])
                await self._execute_callbacks(callbacks, message_data)

        # 전역 콜백 실행
        await self._execute_callbacks(self.global_callbacks, message_data)

    async def _execute_callbacks(self, callbacks: List[Callable], message_data: Dict[str, Any]) -> None:
        """콜백 실행"""
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message_data)
                else:
                    callback(message_data)
            except Exception as e:
                logger.error(f"콜백 실행 오류: {e}")


# =====================================================================
# 5. 메인 구독 관리자
# =====================================================================

class SubscriptionManager:
    """통합 구독 관리자 v3.0"""

    def __init__(self,
                 public_pool_size: int = 3,
                 private_pool_size: int = 2,
                 config_path: Optional[str] = None):
        # 설정 로드
        self.config = load_config(config_path)

        # 핵심 컴포넌트
        self.ticket_manager = TicketManager(public_pool_size, private_pool_size)
        self.message_router = MessageRouter()

        # 구독 관리
        self.active_subscriptions: Dict[str, Subscription] = {}
        self._subscription_counter = 1

        # WebSocket 연결
        self.websocket_connection: Optional[Any] = None

        logger.info(f"구독 관리자 v3.0 초기화 - Public: {public_pool_size}, Private: {private_pool_size}")

    def set_websocket_connection(self, websocket) -> None:
        """WebSocket 연결 설정"""
        self.websocket_connection = websocket
        logger.debug("WebSocket 연결 설정 완료")

    # =================================================================
    # 구독 생성 API
    # =================================================================

    async def subscribe(self,
                        requests: Union[DataRequest, List[DataRequest]],
                        ticket_id: Optional[str] = None,
                        pool_type: TicketPoolType = TicketPoolType.PUBLIC,
                        callback: Optional[Callable] = None) -> Optional[str]:
        """통합 구독 생성

        Args:
            requests: 단일 또는 다중 데이터 요청
            ticket_id: 사용할 티켓 ID (None이면 기본 티켓 사용)
            pool_type: 티켓 풀 타입 (PUBLIC/PRIVATE)
            callback: 콜백 함수
        """
        if not self.websocket_connection:
            logger.error("WebSocket 연결이 설정되지 않았습니다")
            return None

        try:
            # 요청 정규화
            request_list = requests if isinstance(requests, list) else [requests]

            # 티켓 확보
            if ticket_id is None:
                ticket_id = self.ticket_manager.get_default_ticket(pool_type)
            elif not self._is_valid_ticket(ticket_id):
                logger.error(f"유효하지 않은 티켓 ID: {ticket_id}")
                return None

            # 구독 생성
            subscription_id = f"sub_{self._subscription_counter:04d}_{uuid.uuid4().hex[:6]}"
            self._subscription_counter += 1

            subscription = Subscription(subscription_id, ticket_id, pool_type)
            for request in request_list:
                subscription.add_request(request)

            # WebSocket 메시지 전송
            message = subscription.get_websocket_message()
            logger.info(f"🔍 전송할 WebSocket 메시지: {json.dumps(message, indent=2, ensure_ascii=False)}")
            await self.websocket_connection.send(json.dumps(message))

            # 구독 등록
            self.active_subscriptions[subscription_id] = subscription

            # 콜백 등록
            if callback:
                self.message_router.register_subscription_callback(subscription_id, callback)

            # 티켓 사용량 업데이트
            self.ticket_manager.update_ticket_usage(
                ticket_id,
                list(subscription.get_all_data_types()),
                list(subscription.get_all_symbols())
            )

            logger.info(f"구독 생성: {subscription_id}")
            logger.debug(f"요청: {len(request_list)}개, 심볼: {len(subscription.get_all_symbols())}개")
            return subscription_id

        except Exception as e:
            logger.error(f"구독 생성 실패: {e}")
            return None

    async def subscribe_simple(self,
                               data_type: str,
                               symbols: Union[str, List[str]],
                               mode: RequestMode = RequestMode.SNAPSHOT_THEN_REALTIME,
                               callback: Optional[Callable] = None,
                               **options) -> Optional[str]:
        """간단한 구독 (편의 메서드)"""
        symbol_list = [symbols] if isinstance(symbols, str) else symbols
        request = DataRequest(data_type, symbol_list, mode, options)

        # 티켓 풀 타입 결정
        pool_type = TicketPoolType.PRIVATE if data_type in ["myOrder", "myAsset"] else TicketPoolType.PUBLIC

        return await self.subscribe(request, pool_type=pool_type, callback=callback)

    async def subscribe_mixed(self,
                              data_specs: Dict[str, Dict[str, Any]],
                              callback: Optional[Callable] = None,
                              ticket_id: Optional[str] = None) -> Optional[str]:
        """혼합 타입 구독

        Args:
            data_specs: {"ticker": {"symbols": ["KRW-BTC"], "mode": "snapshot_only"}, ...}
            callback: 콜백 함수
            ticket_id: 전용 티켓 ID
        """
        requests = []
        pool_type = TicketPoolType.PUBLIC

        for data_type, spec in data_specs.items():
            symbols = spec.get("symbols", [])
            mode_str = spec.get("mode", "snapshot_then_realtime")
            mode = RequestMode(mode_str)
            options = spec.get("options", {})

            if data_type in ["myOrder", "myAsset"]:
                pool_type = TicketPoolType.PRIVATE

            requests.append(DataRequest(data_type, symbols, mode, options))

        return await self.subscribe(requests, ticket_id, pool_type, callback)

    # =================================================================
    # 구독 해제 API
    # =================================================================

    async def unsubscribe(self, subscription_id: str) -> bool:
        """구독 해제"""
        if subscription_id not in self.active_subscriptions:
            logger.warning(f"구독을 찾을 수 없음: {subscription_id}")
            return False

        try:
            subscription = self.active_subscriptions[subscription_id]
            subscription.is_active = False

            # 콜백 해제
            self.message_router.unregister_subscription_callbacks(subscription_id)

            # 구독 제거
            del self.active_subscriptions[subscription_id]

            # 해제 메시지 전송 (더미 스냅샷으로 교체)
            if self.websocket_connection:
                unsubscribe_message = [
                    {"ticket": subscription.ticket_id},
                    {"type": "ticker", "codes": ["KRW-BTC"], "is_only_snapshot": True},
                    {"format": "DEFAULT"}
                ]
                await self.websocket_connection.send(json.dumps(unsubscribe_message))

            logger.info(f"구독 해제: {subscription_id}")
            return True

        except Exception as e:
            logger.error(f"구독 해제 실패: {e}")
            return False

    async def unsubscribe_all(self, pool_type: Optional[TicketPoolType] = None) -> int:
        """전체 구독 해제"""
        subscription_ids = list(self.active_subscriptions.keys())
        unsubscribed_count = 0

        for sub_id in subscription_ids:
            subscription = self.active_subscriptions[sub_id]
            if pool_type is None or subscription.pool_type == pool_type:
                if await self.unsubscribe(sub_id):
                    unsubscribed_count += 1

        logger.info(f"전체 구독 해제: {unsubscribed_count}개")
        return unsubscribed_count

    # =================================================================
    # 메시지 처리
    # =================================================================

    async def process_message(self, raw_message: str) -> None:
        """수신 메시지 처리"""
        try:
            data = json.loads(raw_message)
            if not isinstance(data, dict):
                return

            # 메시지 타입과 심볼 추출
            message_type = infer_message_type(data)
            symbol = data.get("code", data.get("market", "UNKNOWN"))

            # 해당 메시지를 처리할 구독 찾기
            handling_subscriptions = []
            for sub_id, subscription in self.active_subscriptions.items():
                if subscription.handles_message(message_type, symbol):
                    subscription.update_message_stats()
                    handling_subscriptions.append(sub_id)

            # 메시지 라우팅
            await self.message_router.route_message(data, handling_subscriptions)

        except Exception as e:
            logger.error(f"메시지 처리 오류: {e}")

    # =================================================================
    # 콜백 관리
    # =================================================================

    def register_type_callback(self, data_type: str, callback: Callable) -> None:
        """타입별 콜백 등록"""
        self.message_router.register_type_callback(data_type, callback)

    def register_global_callback(self, callback: Callable) -> None:
        """전역 콜백 등록"""
        self.message_router.register_global_callback(callback)

    # =================================================================
    # 티켓 관리 API
    # =================================================================

    def create_dedicated_ticket(self, pool_type: TicketPoolType, purpose: str = "dedicated") -> Optional[str]:
        """전용 티켓 생성"""
        return self.ticket_manager.create_dedicated_ticket(pool_type, purpose)

    def get_user_tickets(self) -> Dict[str, Any]:
        """사용자 티켓 목록 (기본 티켓 제외)"""
        return self.ticket_manager.get_available_tickets(exclude_default=True)

    def release_ticket(self, ticket_id: str) -> bool:
        """티켓 해제"""
        return self.ticket_manager.release_ticket(ticket_id)

    # =================================================================
    # 상태 조회 API
    # =================================================================

    def get_active_subscriptions(self) -> Dict[str, Dict[str, Any]]:
        """활성 구독 목록"""
        return {sub_id: sub.get_info() for sub_id, sub in self.active_subscriptions.items()}

    def get_ticket_stats(self) -> Dict[str, Any]:
        """티켓 통계"""
        return self.ticket_manager.get_stats()

    def get_stats(self) -> Dict[str, Any]:
        """전체 통계"""
        ticket_stats = self.get_ticket_stats()

        subscription_count_by_type = {}
        symbol_count_by_type = {}
        total_messages = 0

        for subscription in self.active_subscriptions.values():
            total_messages += subscription.message_count
            for data_type in subscription.get_all_data_types():
                subscription_count_by_type[data_type] = subscription_count_by_type.get(data_type, 0) + 1
                symbol_count_by_type[data_type] = len(subscription.get_all_symbols())

        return {
            "subscription_stats": {
                "total_subscriptions": len(self.active_subscriptions),
                "by_type": subscription_count_by_type,
                "symbols_by_type": symbol_count_by_type,
                "total_messages_received": total_messages
            },
            "ticket_stats": ticket_stats,
            "efficiency": {
                "subscriptions_per_ticket": len(self.active_subscriptions) / max(ticket_stats["total_tickets"], 1),
                "pool_utilization": ticket_stats["total_tickets"] / ticket_stats["max_total_tickets"] * 100
            }
        }

    # =================================================================
    # 내부 유틸리티
    # =================================================================

    def _is_valid_ticket(self, ticket_id: str) -> bool:
        """티켓 유효성 확인"""
        return (ticket_id in self.ticket_manager.public_tickets
                or ticket_id in self.ticket_manager.private_tickets)

    def _get_pool_type_for_data_type(self, data_type: str) -> TicketPoolType:
        """데이터 타입에 따른 티켓 풀 타입 결정"""
        return TicketPoolType.PRIVATE if data_type in ["myOrder", "myAsset"] else TicketPoolType.PUBLIC


# =====================================================================
# 6. 편의 함수들
# =====================================================================

def create_subscription_manager(public_pool_size: int = 3,
                                private_pool_size: int = 2,
                                config_path: Optional[str] = None) -> SubscriptionManager:
    """구독 관리자 생성"""
    return SubscriptionManager(public_pool_size, private_pool_size, config_path)


async def quick_ticker_subscribe(manager: SubscriptionManager,
                                 symbols: List[str],
                                 callback: Optional[Callable] = None) -> Optional[str]:
    """빠른 현재가 구독"""
    return await manager.subscribe_simple("ticker", symbols, callback=callback)


async def quick_mixed_subscribe(manager: SubscriptionManager,
                                symbol: str = "KRW-BTC",
                                callback: Optional[Callable] = None) -> Optional[str]:
    """빠른 혼합 구독 (현재가+체결+호가)"""
    data_specs = {
        "ticker": {"symbols": [symbol]},
        "trade": {"symbols": [symbol]},
        "orderbook": {"symbols": [symbol]}
    }
    return await manager.subscribe_mixed(data_specs, callback)


async def market_overview_subscribe(manager: SubscriptionManager,
                                    major_symbols: Optional[List[str]] = None,
                                    callback: Optional[Callable] = None) -> Optional[str]:
    """마켓 개요 구독 (스냅샷 전용)"""
    if major_symbols is None:
        major_symbols = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]

    data_specs = {
        "ticker": {"symbols": major_symbols, "mode": "snapshot_only"}
    }
    return await manager.subscribe_mixed(data_specs, callback)


# =====================================================================
# 7. 사용 예시
# =====================================================================

async def example_usage():
    """사용 예시"""
    # 구독 관리자 생성
    manager = create_subscription_manager()

    # WebSocket 연결 설정 (실제 사용시)
    # manager.set_websocket_connection(websocket)

    # 1. 간단한 구독
    await manager.subscribe_simple("ticker", ["KRW-BTC", "KRW-ETH"])

    # 2. 혼합 구독
    await manager.subscribe_mixed({
        "ticker": {"symbols": ["KRW-BTC"]},
        "trade": {"symbols": ["KRW-BTC"]},
        "orderbook": {"symbols": ["KRW-BTC"]}
    })

    # 3. 전용 티켓으로 구독
    dedicated_ticket = manager.create_dedicated_ticket(TicketPoolType.PUBLIC, "trading")
    if dedicated_ticket:
        await manager.subscribe_simple("trade", ["KRW-BTC"], ticket_id=dedicated_ticket)

    # 4. 스냅샷 전용 구독
    await manager.subscribe_simple("ticker", ["KRW-ETH"], mode=RequestMode.SNAPSHOT_ONLY)

    # 상태 조회
    print("활성 구독:", manager.get_active_subscriptions())
    print("티켓 통계:", manager.get_ticket_stats())
    print("사용자 티켓:", manager.get_user_tickets())
    print("전체 통계:", manager.get_stats())


if __name__ == "__main__":
    asyncio.run(example_usage())
