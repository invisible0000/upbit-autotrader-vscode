"""
업비트 WebSocket v5.0 - Mixed 타입 통합 구독 시스템

🎯 설계 원칙:
1. 티켓 = 재사용 가능한 연결 단위 (스냅샷/리얼타임 구분 없음)
2. 구독 = 논리적 데이터 요청 (여러 타입을 하나의 티켓으로 통합 가능)
3. Mixed 구독 = 하나의 메시지로 여러 데이터 타입 동시 요청
4. 콜백 = 타입별 독립적 처리 또는 통합 처리

🔧 핵심 개념:
- Ticket: 업비트 WebSocket의 물리적 연결 단위 (최대 5개)
- UnifiedSubscription: 여러 데이터 타입을 하나의 메시지로 통합
- BatchBuilder: Mixed 구독 요청 생성 도구
- TypeRouter: 수신 메시지를 타입별로 분배
"""

from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime
import uuid
import json
import asyncio
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .config import load_config

logger = create_component_logger("SubscriptionManager")


# =====================================================================
# 1. 데이터 타입 및 상수 정의
# =====================================================================

class DataType(Enum):
    """지원하는 데이터 타입"""
    TICKER = "ticker"
    TRADE = "trade"
    ORDERBOOK = "orderbook"
    CANDLE_1M = "candle"
    CANDLE_5M = "candle"
    CANDLE_15M = "candle"
    CANDLE_1H = "candle"
    CANDLE_4H = "candle"
    CANDLE_1D = "candle"


class SubscriptionMode(Enum):
    """구독 모드"""
    SNAPSHOT = "snapshot"  # 1회 응답
    REALTIME = "realtime"  # 지속 응답
    MIXED = "mixed"        # 여러 타입 통합


# =====================================================================
# 2. 통합 구독 메시지 생성기
# =====================================================================

class UnifiedSubscription:
    """하나의 티켓으로 여러 타입 통합 구독"""

    def __init__(self, ticket_id: str, is_snapshot: bool = False):
        self.ticket_id = ticket_id
        self.is_snapshot = is_snapshot
        self.data_types: Dict[str, Dict[str, Any]] = {}
        self.all_symbols: set = set()

    def add_ticker(self, symbols: List[str], **options) -> 'UnifiedSubscription':
        """TICKER 타입 추가"""
        config = {"codes": symbols}
        if self.is_snapshot or options.get("is_snapshot", False):
            config["is_only_snapshot"] = True

        self.data_types["ticker"] = config
        self.all_symbols.update(symbols)
        return self

    def add_trade(self, symbols: List[str], **options) -> 'UnifiedSubscription':
        """TRADE 타입 추가"""
        config = {"codes": symbols}
        if self.is_snapshot or options.get("is_snapshot", False):
            config["is_only_snapshot"] = True

        self.data_types["trade"] = config
        self.all_symbols.update(symbols)
        return self

    def add_orderbook(self, symbols: List[str], **options) -> 'UnifiedSubscription':
        """ORDERBOOK 타입 추가"""
        config = {"codes": symbols}
        if self.is_snapshot or options.get("is_snapshot", False):
            config["is_only_snapshot"] = True

        self.data_types["orderbook"] = config
        self.all_symbols.update(symbols)
        return self

    def add_candle(self, symbols: List[str], unit: str = "1m", **options) -> 'UnifiedSubscription':
        """CANDLE 타입 추가"""
        # 캔들은 타입명에 단위 포함
        candle_type = f"candle_{unit.upper()}" if "_" not in unit else f"candle_{unit}"

        config = {
            "type": "candle",  # 실제 업비트 API 타입
            "codes": symbols
        }

        # 단위별 파라미터 설정
        if "1m" in unit or "1M" in unit:
            config["unit"] = "1"
        elif "5m" in unit or "5M" in unit:
            config["unit"] = "5"
        elif "15m" in unit or "15M" in unit:
            config["unit"] = "15"
        elif "1h" in unit or "1H" in unit:
            config["unit"] = "60"
        elif "4h" in unit or "4H" in unit:
            config["unit"] = "240"
        elif "1d" in unit or "1D" in unit:
            config["unit"] = "1440"
        else:
            config["unit"] = unit  # 사용자 지정

        if self.is_snapshot or options.get("is_snapshot", False):
            config["is_only_snapshot"] = True

        self.data_types[candle_type] = config
        self.all_symbols.update(symbols)
        return self

    def get_message(self) -> List[Dict[str, Any]]:
        """최종 WebSocket 메시지 생성"""
        if not self.data_types:
            raise ValueError("구독할 데이터 타입이 없습니다")

        message = [{"ticket": self.ticket_id}]

        # 각 데이터 타입별 설정 추가
        for type_key, config in self.data_types.items():
            # candle 타입은 실제 type 사용
            if type_key.startswith("candle"):
                data_config = {
                    "type": config.get("type", "candle"),
                    "codes": config["codes"]
                }
                # unit 파라미터 추가
                if "unit" in config:
                    data_config["unit"] = config["unit"]
            else:
                data_config = {
                    "type": type_key,
                    "codes": config["codes"]
                }

            # 스냅샷 옵션 추가
            if config.get("is_only_snapshot"):
                data_config["is_only_snapshot"] = True

            message.append(data_config)

        # 포맷 설정
        message.append({"format": "DEFAULT"})

        return message

    def get_stats(self) -> Dict[str, Any]:
        """구독 통계"""
        return {
            "ticket_id": self.ticket_id,
            "is_snapshot": self.is_snapshot,
            "data_types": list(self.data_types.keys()),
            "total_symbols": len(self.all_symbols),
            "symbols": list(self.all_symbols),
            "message_size": len(json.dumps(self.get_message()))
        }


# =====================================================================
# 3. 배치 구독 빌더
# =====================================================================

class BatchSubscriptionBuilder:
    """Mixed 구독 요청 생성 도구"""

    def __init__(self, is_snapshot: bool = False):
        self.is_snapshot = is_snapshot
        self._ticker_symbols: List[str] = []
        self._trade_symbols: List[str] = []
        self._orderbook_symbols: List[str] = []
        self._candle_configs: List[Dict[str, Any]] = []
        self._ticker_options: Dict[str, Any] = {}
        self._trade_options: Dict[str, Any] = {}
        self._orderbook_options: Dict[str, Any] = {}

    def add_ticker(self, symbols: Union[str, List[str]], **options) -> 'BatchSubscriptionBuilder':
        """TICKER 구독 추가"""
        symbol_list = [symbols] if isinstance(symbols, str) else symbols
        self._ticker_symbols.extend(symbol_list)
        self._ticker_options.update(options)
        return self

    def add_trade(self, symbols: Union[str, List[str]], **options) -> 'BatchSubscriptionBuilder':
        """TRADE 구독 추가"""
        symbol_list = [symbols] if isinstance(symbols, str) else symbols
        self._trade_symbols.extend(symbol_list)
        self._trade_options.update(options)
        return self

    def add_orderbook(self, symbols: Union[str, List[str]], **options) -> 'BatchSubscriptionBuilder':
        """ORDERBOOK 구독 추가"""
        symbol_list = [symbols] if isinstance(symbols, str) else symbols
        self._orderbook_symbols.extend(symbol_list)
        self._orderbook_options.update(options)
        return self

    def add_candle(self, symbols: Union[str, List[str]], unit: str = "1m", **options) -> 'BatchSubscriptionBuilder':
        """CANDLE 구독 추가"""
        symbol_list = [symbols] if isinstance(symbols, str) else symbols
        self._candle_configs.append({
            "symbols": symbol_list,
            "unit": unit,
            "options": options
        })
        return self

    def build(self, ticket_id: str) -> UnifiedSubscription:
        """UnifiedSubscription 객체 생성"""
        unified = UnifiedSubscription(ticket_id, self.is_snapshot)

        # 각 타입별 추가
        if self._ticker_symbols:
            unified.add_ticker(list(set(self._ticker_symbols)), **self._ticker_options)

        if self._trade_symbols:
            unified.add_trade(list(set(self._trade_symbols)), **self._trade_options)

        if self._orderbook_symbols:
            unified.add_orderbook(list(set(self._orderbook_symbols)), **self._orderbook_options)

        for candle_config in self._candle_configs:
            unified.add_candle(
                list(set(candle_config["symbols"])),
                candle_config["unit"],
                **candle_config["options"]
            )

        return unified

    def clear(self) -> 'BatchSubscriptionBuilder':
        """빌더 초기화"""
        self._ticker_symbols.clear()
        self._trade_symbols.clear()
        self._orderbook_symbols.clear()
        self._candle_configs.clear()
        self._ticker_options.clear()
        self._trade_options.clear()
        self._orderbook_options.clear()
        return self

    def get_summary(self) -> Dict[str, Any]:
        """빌더 상태 요약"""
        return {
            "is_snapshot": self.is_snapshot,
            "ticker_symbols": len(set(self._ticker_symbols)),
            "trade_symbols": len(set(self._trade_symbols)),
            "orderbook_symbols": len(set(self._orderbook_symbols)),
            "candle_configs": len(self._candle_configs),
            "total_unique_symbols": len(set(
                self._ticker_symbols + self._trade_symbols +
                self._orderbook_symbols +
                [s for config in self._candle_configs for s in config["symbols"]]
            ))
        }


# =====================================================================
# 4. 메시지 타입 라우터
# =====================================================================

class TypeRouter:
    """수신 메시지를 타입별로 분배"""

    def __init__(self):
        self.type_callbacks: Dict[str, List[Callable]] = {}
        self.unified_callbacks: List[Callable] = []  # 모든 타입 수신

    def register_type_callback(self, data_type: str, callback: Callable) -> None:
        """특정 타입 콜백 등록"""
        if data_type not in self.type_callbacks:
            self.type_callbacks[data_type] = []
        self.type_callbacks[data_type].append(callback)

    def register_unified_callback(self, callback: Callable) -> None:
        """통합 콜백 등록 (모든 타입 수신)"""
        self.unified_callbacks.append(callback)

    async def route_message(self, message_data: Dict[str, Any]) -> None:
        """메시지를 적절한 콜백으로 라우팅"""
        message_type = message_data.get("type", "")

        # 타입별 콜백 실행
        if message_type in self.type_callbacks:
            for callback in self.type_callbacks[message_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message_data)
                    else:
                        callback(message_data)
                except Exception as e:
                    logger.error(f"타입별 콜백 실행 오류 [{message_type}]: {e}")

        # 통합 콜백 실행
        for callback in self.unified_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message_data)
                else:
                    callback(message_data)
            except Exception as e:
                logger.error(f"통합 콜백 실행 오류: {e}")


# =====================================================================
# 5. 티켓 관리자 (단순화)
# =====================================================================

class TicketManager:
    """업비트 WebSocket 티켓 관리"""

    def __init__(self, max_tickets: int = 3):
        self.max_tickets = max_tickets
        self.active_tickets: Dict[str, Dict[str, Any]] = {}
        self.next_ticket_number = 1

    def create_ticket(self, purpose: str = "general") -> Optional[str]:
        """새로운 티켓 생성"""
        if len(self.active_tickets) >= self.max_tickets:
            logger.warning(f"티켓 한계 도달: {len(self.active_tickets)}/{self.max_tickets}")
            return None

        ticket_id = f"ticket_{self.next_ticket_number:03d}_{uuid.uuid4().hex[:6]}"
        self.next_ticket_number += 1

        self.active_tickets[ticket_id] = {
            "purpose": purpose,
            "created_at": datetime.now(),
            "subscription_count": 0,
            "data_types": set(),
            "symbols": set()
        }

        logger.debug(f"티켓 생성: {ticket_id} (목적: {purpose})")
        return ticket_id

    def get_reusable_ticket(self) -> Optional[str]:
        """재사용 가능한 티켓 찾기"""
        for ticket_id, info in self.active_tickets.items():
            if info["subscription_count"] < 3:  # 티켓당 최대 3개 구독
                return ticket_id
        return None

    def update_ticket_info(self, ticket_id: str, data_types: List[str], symbols: List[str]) -> None:
        """티켓 정보 업데이트"""
        if ticket_id in self.active_tickets:
            self.active_tickets[ticket_id]["data_types"].update(data_types)
            self.active_tickets[ticket_id]["symbols"].update(symbols)
            self.active_tickets[ticket_id]["subscription_count"] += 1

    def release_ticket(self, ticket_id: str) -> bool:
        """티켓 해제"""
        if ticket_id in self.active_tickets:
            del self.active_tickets[ticket_id]
            logger.debug(f"티켓 해제: {ticket_id}")
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """티켓 통계"""
        return {
            "total_tickets": len(self.active_tickets),
            "max_tickets": self.max_tickets,
            "utilization": len(self.active_tickets) / self.max_tickets * 100,
            "tickets": {
                tid: {
                    "purpose": info["purpose"],
                    "subscription_count": info["subscription_count"],
                    "data_types": list(info["data_types"]),
                    "symbol_count": len(info["symbols"])
                }
                for tid, info in self.active_tickets.items()
            }
        }


# =====================================================================
# 6. 통합 구독 매니저 (v2.0)
# =====================================================================

class SubscriptionManager:
    """Mixed 타입 통합 구독 관리자"""

    def __init__(self, max_tickets: int = 3, config_path: Optional[str] = None):
        # 설정 로드
        self.config = load_config(config_path)

        # 핵심 컴포넌트들
        self.ticket_manager = TicketManager(max_tickets)
        self.type_router = TypeRouter()

        # 구독 추적
        self.active_subscriptions: Dict[str, Dict[str, Any]] = {}

        # WebSocket 연결 참조
        self.websocket_connection: Optional[Any] = None

        logger.info(f"Mixed 구독 매니저 초기화 - 최대 티켓: {max_tickets}")

    def set_websocket_connection(self, websocket) -> None:
        """WebSocket 연결 설정"""
        self.websocket_connection = websocket
        logger.debug("WebSocket 연결 설정 완료")

    # =================================================================
    # Mixed 구독 API (메인 기능)
    # =================================================================

    async def subscribe_mixed(self, builder: BatchSubscriptionBuilder,
                            callback: Optional[Callable] = None) -> Optional[str]:
        """배치 빌더를 사용한 Mixed 구독"""
        if not self.websocket_connection:
            logger.error("WebSocket 연결이 설정되지 않았습니다")
            return None

        # 티켓 획득 또는 생성
        ticket_id = self.ticket_manager.get_reusable_ticket()
        if not ticket_id:
            ticket_id = self.ticket_manager.create_ticket("mixed")
            if not ticket_id:
                logger.error("Mixed 구독용 티켓 생성 실패")
                return None

        try:
            # UnifiedSubscription 생성
            unified = builder.build(ticket_id)

            # 구독 ID 생성
            subscription_id = f"mixed_{uuid.uuid4().hex[:8]}"

            # 메시지 전송
            message = unified.get_message()
            await self.websocket_connection.send(json.dumps(message))

            # 구독 정보 저장
            self.active_subscriptions[subscription_id] = {
                "ticket_id": ticket_id,
                "mode": SubscriptionMode.MIXED.value,
                "data_types": list(unified.data_types.keys()),
                "symbols": list(unified.all_symbols),
                "is_snapshot": unified.is_snapshot,
                "created_at": datetime.now(),
                "message_count": 0,
                "unified_subscription": unified
            }

            # 콜백 등록
            if callback:
                self.type_router.register_unified_callback(callback)

            # 티켓 정보 업데이트
            self.ticket_manager.update_ticket_info(
                ticket_id,
                list(unified.data_types.keys()),
                list(unified.all_symbols)
            )

            logger.info(f"Mixed 구독 완료: {subscription_id}")
            logger.info(f"  타입: {list(unified.data_types.keys())}")
            logger.info(f"  심볼: {len(unified.all_symbols)}개")
            logger.debug(f"전송 메시지: {message}")

            return subscription_id

        except Exception as e:
            logger.error(f"Mixed 구독 실패: {e}")
            return None

    async def subscribe_quick_mixed(self, types_and_symbols: Dict[str, List[str]],
                                  is_snapshot: bool = False,
                                  callback: Optional[Callable] = None) -> Optional[str]:
        """간단한 딕셔너리를 사용한 Mixed 구독"""
        builder = BatchSubscriptionBuilder(is_snapshot)

        for data_type, symbols in types_and_symbols.items():
            if data_type == "ticker":
                builder.add_ticker(symbols)
            elif data_type == "trade":
                builder.add_trade(symbols)
            elif data_type == "orderbook":
                builder.add_orderbook(symbols)
            elif data_type.startswith("candle"):
                # candle_1m, candle_5m 등의 형태
                unit = data_type.split("_")[1] if "_" in data_type else "1m"
                builder.add_candle(symbols, unit)
            else:
                logger.warning(f"지원하지 않는 데이터 타입: {data_type}")

        return await self.subscribe_mixed(builder, callback)

    # =================================================================
    # 타입별 개별 구독 (기존 호환성)
    # =================================================================

    async def subscribe_ticker(self, symbols: List[str], is_snapshot: bool = False,
                             callback: Optional[Callable] = None) -> Optional[str]:
        """TICKER 개별 구독"""
        builder = BatchSubscriptionBuilder(is_snapshot)
        builder.add_ticker(symbols)
        return await self.subscribe_mixed(builder, callback)

    async def subscribe_trade(self, symbols: List[str], is_snapshot: bool = False,
                            callback: Optional[Callable] = None) -> Optional[str]:
        """TRADE 개별 구독"""
        builder = BatchSubscriptionBuilder(is_snapshot)
        builder.add_trade(symbols)
        return await self.subscribe_mixed(builder, callback)

    async def subscribe_orderbook(self, symbols: List[str], is_snapshot: bool = False,
                                callback: Optional[Callable] = None) -> Optional[str]:
        """ORDERBOOK 개별 구독"""
        builder = BatchSubscriptionBuilder(is_snapshot)
        builder.add_orderbook(symbols)
        return await self.subscribe_mixed(builder, callback)

    async def subscribe_candle(self, symbols: List[str], unit: str = "1m", is_snapshot: bool = False,
                             callback: Optional[Callable] = None) -> Optional[str]:
        """CANDLE 개별 구독"""
        builder = BatchSubscriptionBuilder(is_snapshot)
        builder.add_candle(symbols, unit)
        return await self.subscribe_mixed(builder, callback)

    # =================================================================
    # 구독 해제
    # =================================================================

    async def unsubscribe(self, subscription_id: str) -> bool:
        """구독 해제"""
        if subscription_id not in self.active_subscriptions:
            logger.warning(f"구독을 찾을 수 없음: {subscription_id}")
            return False

        subscription = self.active_subscriptions[subscription_id]
        ticket_id = subscription["ticket_id"]

        try:
            # 구독 정보 제거
            del self.active_subscriptions[subscription_id]

            # 스냅샷이거나 마지막 구독인 경우 티켓 해제
            if subscription["is_snapshot"] or not self._has_other_subscriptions(ticket_id):
                # 해제 메시지 전송 (스냅샷으로 교체)
                if self.websocket_connection:
                    unsubscribe_message = [
                        {"ticket": ticket_id},
                        {"type": "ticker", "codes": ["KRW-BTC"], "is_only_snapshot": True},
                        {"format": "DEFAULT"}
                    ]
                    await self.websocket_connection.send(json.dumps(unsubscribe_message))

                self.ticket_manager.release_ticket(ticket_id)

            logger.info(f"구독 해제 완료: {subscription_id}")
            return True

        except Exception as e:
            logger.error(f"구독 해제 실패: {e}")
            return False

    def _has_other_subscriptions(self, ticket_id: str) -> bool:
        """해당 티켓의 다른 구독이 있는지 확인"""
        return any(
            sub["ticket_id"] == ticket_id
            for sub in self.active_subscriptions.values()
        )

    # =================================================================
    # 메시지 처리
    # =================================================================

    async def process_message(self, raw_message: str) -> None:
        """수신된 메시지 처리"""
        try:
            data = json.loads(raw_message)
            if not isinstance(data, dict):
                return

            # 메시지 카운트 업데이트
            self._update_message_count(data)

            # 타입 라우터로 메시지 분배
            await self.type_router.route_message(data)

            # 스냅샷 자동 해제 처리
            await self._handle_snapshot_auto_unsubscribe(data)

        except Exception as e:
            logger.error(f"메시지 처리 오류: {e}")

    def _update_message_count(self, data: Dict[str, Any]) -> None:
        """메시지 카운트 업데이트"""
        message_type = data.get("type", "")
        for subscription in self.active_subscriptions.values():
            if message_type in subscription.get("data_types", []):
                subscription["message_count"] += 1

    async def _handle_snapshot_auto_unsubscribe(self, data: Dict[str, Any]) -> None:
        """스냅샷 자동 해제 처리"""
        message_type = data.get("type", "")
        to_unsubscribe = []

        for sub_id, subscription in self.active_subscriptions.items():
            if (subscription["is_snapshot"] and
                message_type in subscription.get("data_types", [])):
                to_unsubscribe.append(sub_id)

        for sub_id in to_unsubscribe:
            await self.unsubscribe(sub_id)
            logger.debug(f"스냅샷 자동 해제: {sub_id}")

    # =================================================================
    # 콜백 관리
    # =================================================================

    def register_type_callback(self, data_type: str, callback: Callable) -> None:
        """특정 타입 콜백 등록"""
        self.type_router.register_type_callback(data_type, callback)

    def register_global_callback(self, callback: Callable) -> None:
        """전역 콜백 등록 (모든 메시지 수신)"""
        self.type_router.register_unified_callback(callback)

    # =================================================================
    # 통계 및 상태 조회
    # =================================================================

    def get_stats(self) -> Dict[str, Any]:
        """전체 통계"""
        ticket_stats = self.ticket_manager.get_stats()

        subscription_stats = {
            "total_subscriptions": len(self.active_subscriptions),
            "snapshot_subscriptions": sum(1 for s in self.active_subscriptions.values() if s["is_snapshot"]),
            "realtime_subscriptions": sum(1 for s in self.active_subscriptions.values() if not s["is_snapshot"]),
            "mixed_subscriptions": sum(1 for s in self.active_subscriptions.values() if s["mode"] == "mixed")
        }

        return {
            "ticket_stats": ticket_stats,
            "subscription_stats": subscription_stats,
            "efficiency": {
                "tickets_used": ticket_stats["total_tickets"],
                "subscriptions_served": subscription_stats["total_subscriptions"],
                "efficiency_ratio": subscription_stats["total_subscriptions"] / max(ticket_stats["total_tickets"], 1)
            }
        }

    def get_active_subscriptions(self) -> Dict[str, Dict[str, Any]]:
        """활성 구독 목록"""
        return {
            sub_id: {
                "ticket_id": sub["ticket_id"],
                "mode": sub["mode"],
                "data_types": sub["data_types"],
                "symbol_count": len(sub["symbols"]),
                "is_snapshot": sub["is_snapshot"],
                "message_count": sub["message_count"],
                "created_at": sub["created_at"].isoformat()
            }
            for sub_id, sub in self.active_subscriptions.items()
        }


# =====================================================================
# 7. 편의 함수들
# =====================================================================

def create_subscription_manager(max_tickets: int = 3, config_path: Optional[str] = None) -> SubscriptionManager:
    """구독 매니저 생성"""
    return SubscriptionManager(max_tickets, config_path)


def create_batch_builder(is_snapshot: bool = False) -> BatchSubscriptionBuilder:
    """배치 빌더 생성"""
    return BatchSubscriptionBuilder(is_snapshot)


async def quick_market_overview(manager: SubscriptionManager,
                               major_symbols: List[str] = None) -> Optional[str]:
    """주요 마켓 개요 (TICKER + TRADE 스냅샷)"""
    if major_symbols is None:
        major_symbols = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]

    builder = create_batch_builder(is_snapshot=True)
    builder.add_ticker(major_symbols)
    builder.add_trade(major_symbols)

    return await manager.subscribe_mixed(builder)


async def comprehensive_symbol_monitoring(manager: SubscriptionManager,
                                        symbol: str = "KRW-BTC") -> Optional[str]:
    """단일 심볼 종합 모니터링 (모든 타입 리얼타임)"""
    builder = create_batch_builder(is_snapshot=False)
    builder.add_ticker([symbol])
    builder.add_trade([symbol])
    builder.add_orderbook([symbol])
    builder.add_candle([symbol], "1m")

    return await manager.subscribe_mixed(builder)
