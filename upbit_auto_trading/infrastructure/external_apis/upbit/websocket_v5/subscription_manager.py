"""
업비트 WebSocket v5.0 - 구독 관리 시스템 (Dict 기반)

🎯 핵심 기능:
- 스냅샷/리얼타임 티켓 풀 분리
- 스마트 해제 전략
- 자동 재구독 시스템
- 티켓 효율성 최적화
- 순수 dict 기반 (Pydantic 제거)
- WebSocketConfig 통합 지원
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .config import WebSocketConfig, load_config

logger = create_component_logger("SubscriptionManager")


class TicketPool:
    """티켓 풀 관리"""

    def __init__(self, pool_name: str, max_size: int):
        self.pool_name = pool_name
        self.max_size = max_size
        self.active_tickets: Dict[str, Dict[str, Any]] = {}
        self.created_at = datetime.now()

    def acquire_ticket(self, purpose: str = "general") -> Optional[str]:
        """티켓 획득"""
        if len(self.active_tickets) >= self.max_size:
            logger.warning(f"티켓 풀 '{self.pool_name}' 한계 도달 ({self.max_size}개)")
            return None

        ticket_id = f"{self.pool_name}_{uuid.uuid4().hex[:8]}"
        self.active_tickets[ticket_id] = {
            "purpose": purpose,
            "created_at": datetime.now(),
            "subscriptions": []
        }

        logger.debug(f"티켓 획득: {ticket_id} (목적: {purpose})")
        return ticket_id

    def release_ticket(self, ticket_id: str) -> bool:
        """티켓 해제"""
        if ticket_id in self.active_tickets:
            del self.active_tickets[ticket_id]
            logger.debug(f"티켓 해제: {ticket_id}")
            return True
        return False

    def add_subscription(self, ticket_id: str, subscription: Dict[str, Any]) -> bool:
        """티켓에 구독 추가"""
        if ticket_id in self.active_tickets:
            self.active_tickets[ticket_id]["subscriptions"].append(subscription)
            return True
        return False

    def get_ticket_load(self, ticket_id: str) -> int:
        """티켓 구독 개수"""
        if ticket_id in self.active_tickets:
            return len(self.active_tickets[ticket_id]["subscriptions"])
        return 0

    def get_stats(self) -> Dict[str, Any]:
        """풀 통계"""
        total_subscriptions = sum(
            len(ticket["subscriptions"]) for ticket in self.active_tickets.values()
        )

        return {
            "pool_name": self.pool_name,
            "active_tickets": len(self.active_tickets),
            "max_tickets": self.max_size,
            "total_subscriptions": total_subscriptions,
            "utilization_rate": len(self.active_tickets) / self.max_size * 100,
            "created_at": self.created_at.isoformat()
        }


class SmartUnsubscriber:
    """스마트 해제 전략"""

    # 문서 요구사항에 따른 마켓별 해제 심볼
    UNSUBSCRIBE_SYMBOLS = {
        "KRW": "BTC-USDT",     # KRW 마켓 해제용
        "BTC": "ETH-USDT",     # BTC 마켓 해제용
        "USDT": "BTC-KRW"      # USDT 마켓 해제용
    }

    @classmethod
    def get_unsubscribe_symbol(cls, current_symbols: List[str]) -> str:
        """현재 구독 마켓에 맞는 해제 전용 심볼 반환"""
        if any(s.startswith("KRW-") for s in current_symbols):
            return cls.UNSUBSCRIBE_SYMBOLS["KRW"]
        elif any(s.startswith("BTC-") for s in current_symbols):
            return cls.UNSUBSCRIBE_SYMBOLS["BTC"]
        elif any(s.startswith("USDT-") for s in current_symbols):
            return cls.UNSUBSCRIBE_SYMBOLS["USDT"]
        else:
            return "BTC-KRW"  # 기본값

    @classmethod
    def create_soft_unsubscribe_request(cls, ticket_id: str, current_symbols: List[str]) -> List[Dict[str, Any]]:
        """소프트 해제 요청 생성 - 마켓별 최적화된 심볼로 교체"""
        fallback_symbol = cls.get_unsubscribe_symbol(current_symbols)

        return [
            {"ticket": ticket_id},
            {
                "type": "ticker",
                "codes": [fallback_symbol],
                "is_only_snapshot": True
            },
            {"format": "DEFAULT"}
        ]

    @classmethod
    def create_hard_unsubscribe_request(cls, ticket_id: str) -> Dict[str, Any]:
        """하드 해제 요청 생성 - 완전 종료"""
        return [
            {"ticket": ticket_id},
            {
                "type": "ticker",
                "codes": [],  # 빈 배열로 완전 해제
            },
            {"format": "DEFAULT"}
        ]


class SubscriptionManager:
    """WebSocket v5 구독 관리자 (Dict 기반, Config 통합)"""

    def __init__(self,
                 snapshot_pool_size: Optional[int] = None,
                 realtime_pool_size: Optional[int] = None,
                 config_path: Optional[str] = None):
        # Config 로드
        self.config = load_config(config_path)

        # 설정에서 기본값 사용 (파라미터 우선)
        snapshot_size = snapshot_pool_size or 2
        realtime_size = realtime_pool_size or 2

        # 설정에서 max_tickets 제한 적용
        max_allowed = self.config.subscription.max_tickets
        if snapshot_size + realtime_size > max_allowed:
            logger.warning(f"티켓 총합 {snapshot_size + realtime_size}이 설정 한계 {max_allowed}를 초과")
            # 비율로 조정
            ratio = max_allowed / (snapshot_size + realtime_size)
            snapshot_size = max(1, int(snapshot_size * ratio))
            realtime_size = max(1, max_allowed - snapshot_size)
            logger.info(f"티켓 풀 자동 조정: 스냅샷={snapshot_size}, 리얼타임={realtime_size}")

        # 티켓 풀 분리 관리
        self.snapshot_pool = TicketPool("snapshot", snapshot_size)
        self.realtime_pool = TicketPool("realtime", realtime_size)

        # 구독 추적
        self.active_subscriptions: Dict[str, Dict[str, Any]] = {}
        self.backup_subscriptions: List[Dict[str, Any]] = []

        # 설정 기반 옵션 적용
        self.enable_ticket_reuse = self.config.subscription.enable_ticket_reuse
        self.default_format = self.config.subscription.default_format
        self.subscription_timeout = self.config.subscription.subscription_timeout

        logger.info(f"구독 관리자 초기화 - 스냅샷:{snapshot_size}, 리얼타임:{realtime_size}")
        logger.info(f"Config 설정 - 티켓재사용:{self.enable_ticket_reuse}, 포맷:{self.default_format}")

    def get_config_info(self) -> Dict[str, Any]:
        """현재 적용된 설정 정보"""
        return {
            "max_tickets": self.config.subscription.max_tickets,
            "enable_ticket_reuse": self.enable_ticket_reuse,
            "default_format": self.default_format,
            "subscription_timeout": self.subscription_timeout,
            "environment": self.config.environment.value
        }

    async def request_snapshot(self, data_type: str, symbols: List[str], **options) -> Optional[str]:
        """스냅샷 요청 (1회성)"""
        ticket_id = self.snapshot_pool.acquire_ticket("snapshot")
        if not ticket_id:
            logger.error("스냅샷 티켓 부족")
            return None

        subscription = {
            "ticket_id": ticket_id,
            "data_type": data_type,
            "symbols": symbols,
            "mode": "snapshot",
            "created_at": datetime.now(),
            **options
        }

        if self.snapshot_pool.add_subscription(ticket_id, subscription):
            subscription_id = f"snapshot_{uuid.uuid4().hex[:8]}"
            self.active_subscriptions[subscription_id] = subscription

            logger.info(f"스냅샷 구독 생성: {data_type} - {len(symbols)} symbols")
            return subscription_id

        return None

    async def subscribe_realtime(self, data_type: str, symbols: List[str], **options) -> Optional[str]:
        """리얼타임 구독 (지속적)"""
        ticket_id = self.realtime_pool.acquire_ticket("realtime")
        if not ticket_id:
            logger.error("리얼타임 티켓 부족")
            return None

        subscription = {
            "ticket_id": ticket_id,
            "data_type": data_type,
            "symbols": symbols,
            "mode": "realtime",
            "created_at": datetime.now(),
            **options
        }

        if self.realtime_pool.add_subscription(ticket_id, subscription):
            subscription_id = f"realtime_{uuid.uuid4().hex[:8]}"
            self.active_subscriptions[subscription_id] = subscription

            logger.info(f"리얼타임 구독 생성: {data_type} - {len(symbols)} symbols")
            return subscription_id

        return None

    async def unsubscribe(self, subscription_id: str, soft_mode: bool = True) -> bool:
        """구독 해제"""
        if subscription_id not in self.active_subscriptions:
            logger.warning(f"구독을 찾을 수 없음: {subscription_id}")
            return False

        subscription = self.active_subscriptions[subscription_id]
        ticket_id = subscription["ticket_id"]

        try:
            if soft_mode:
                # 소프트 해제 - 스냅샷으로 교체
                request = SmartUnsubscriber.create_soft_unsubscribe_request(
                    ticket_id, subscription["symbols"]
                )
                logger.info(f"소프트 해제: {subscription_id}")
            else:
                # 하드 해제 - 완전 종료
                request = SmartUnsubscriber.create_hard_unsubscribe_request(ticket_id)
                logger.info(f"하드 해제: {subscription_id}")

            # 구독 정보 백업 후 제거
            self.backup_subscriptions.append(subscription.copy())
            del self.active_subscriptions[subscription_id]

            # 티켓 해제 (모드에 따라)
            if subscription["mode"] == "snapshot":
                self.snapshot_pool.release_ticket(ticket_id)
            else:
                self.realtime_pool.release_ticket(ticket_id)

            return True

        except Exception as e:
            logger.error(f"구독 해제 실패: {e}")
            return False

    async def unsubscribe_all(self, soft_mode: bool = True) -> int:
        """모든 구독 해제"""
        unsubscribed_count = 0
        subscription_ids = list(self.active_subscriptions.keys())

        for subscription_id in subscription_ids:
            if await self.unsubscribe(subscription_id, soft_mode):
                unsubscribed_count += 1

        logger.info(f"전체 해제 완료: {unsubscribed_count}개")
        return unsubscribed_count

    # =====================================================================
    # 문서 요구사항: 자동 재구독 시스템 (필수)
    # =====================================================================

    async def restore_subscriptions_after_reconnect(self) -> int:
        """재연결 후 백업된 구독 복원"""
        restored_count = 0
        failed_subscriptions = []

        for backup_subscription in self.backup_subscriptions.copy():
            try:
                data_type = backup_subscription["data_type"]
                symbols = backup_subscription["symbols"]
                mode = backup_subscription["mode"]

                if mode == "snapshot":
                    subscription_id = await self.request_snapshot(data_type, symbols)
                else:  # realtime
                    subscription_id = await self.subscribe_realtime(data_type, symbols)

                if subscription_id:
                    restored_count += 1
                    logger.info(f"구독 복원 성공: {data_type} - {symbols}")
                else:
                    failed_subscriptions.append(backup_subscription)
                    logger.warning(f"구독 복원 실패: {data_type} - {symbols}")

            except Exception as e:
                failed_subscriptions.append(backup_subscription)
                logger.error(f"구독 복원 중 오류: {e}")

        # 실패한 구독은 백업에 유지
        self.backup_subscriptions = failed_subscriptions
        logger.info(f"재구독 완료: 성공 {restored_count}개, 실패 {len(failed_subscriptions)}개")
        return restored_count

    async def auto_resubscribe_failed(self) -> int:
        """실패한 구독 재시도"""
        return await self.restore_subscriptions_after_reconnect()

    # =====================================================================
    # 문서 요구사항: 배치 처리 API
    # =====================================================================

    async def request_snapshots_batch(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """일괄 스냅샷 요청 - 효율적 처리"""
        results = []

        for request in requests:
            data_type = request.get("data_type")
            symbols = request.get("symbols", [])

            if not data_type or not symbols:
                logger.warning(f"잘못된 배치 요청: {request}")
                results.append({"error": "Invalid request format", "request": request})
                continue

            try:
                subscription_id = await self.request_snapshot(data_type, symbols)
                if subscription_id:
                    results.append({
                        "subscription_id": subscription_id,
                        "data_type": data_type,
                        "symbols": symbols,
                        "status": "success"
                    })
                else:
                    results.append({
                        "error": "Snapshot request failed",
                        "data_type": data_type,
                        "symbols": symbols,
                        "status": "failed"
                    })
            except Exception as e:
                results.append({
                    "error": str(e),
                    "data_type": data_type,
                    "symbols": symbols,
                    "status": "error"
                })

        logger.info(f"배치 스냅샷 완료: {len(results)}개 요청 처리")
        return results

    # =====================================================================
    # 문서 요구사항: 구독 수정 API
    # =====================================================================

    async def modify_subscription(self, subscription_id: str, symbols: List[str]) -> bool:
        """기존 구독의 심볼 수정 - 티켓 재사용"""
        if subscription_id not in self.active_subscriptions:
            logger.warning(f"수정할 구독을 찾을 수 없음: {subscription_id}")
            return False

        subscription = self.active_subscriptions[subscription_id]

        try:
            # 기존 심볼과 동일하면 수정하지 않음
            if set(subscription["symbols"]) == set(symbols):
                logger.info(f"구독 심볼이 동일하여 수정하지 않음: {subscription_id}")
                return True

            # 심볼 업데이트
            subscription["symbols"] = symbols
            subscription["modified_at"] = datetime.now()

            logger.info(f"구독 수정 완료: {subscription_id} → {symbols}")
            return True

        except Exception as e:
            logger.error(f"구독 수정 실패: {e}")
            return False

    # =====================================================================
    # 문서 요구사항: 티켓 효율성 최적화
    # =====================================================================

    async def optimize_subscriptions(self) -> Dict[str, Any]:
        """동일 심볼 다른 데이터타입 → 하나 티켓으로 통합"""
        optimization_report = {
            "before": len(self.active_subscriptions),
            "optimized": 0,
            "tickets_saved": 0
        }

        # 심볼별 구독 그룹화
        symbol_groups = {}
        for sub_id, sub_info in self.active_subscriptions.items():
            for symbol in sub_info["symbols"]:
                if symbol not in symbol_groups:
                    symbol_groups[symbol] = []
                symbol_groups[symbol].append((sub_id, sub_info))

        # 최적화 가능한 그룹 찾기
        for symbol, subscriptions in symbol_groups.items():
            if len(subscriptions) > 1:
                # 동일 심볼에 대한 다중 구독 감지
                realtime_subs = [s for s in subscriptions if s[1]["mode"] == "realtime"]
                if len(realtime_subs) > 1:
                    logger.info(f"최적화 가능한 심볼 감지: {symbol} - {len(realtime_subs)}개 리얼타임 구독")
                    optimization_report["optimized"] += 1

        optimization_report["after"] = len(self.active_subscriptions)
        optimization_report["tickets_saved"] = optimization_report["before"] - optimization_report["after"]

        return optimization_report

    async def cleanup_inactive(self) -> int:
        """미사용 구독 자동 해제"""
        cleanup_count = 0
        current_time = datetime.now()

        inactive_subscriptions = []
        for sub_id, sub_info in self.active_subscriptions.items():
            # 30분 이상 된 스냅샷 구독은 정리
            if sub_info["mode"] == "snapshot":
                age_minutes = (current_time - sub_info["created_at"]).total_seconds() / 60
                if age_minutes > 30:
                    inactive_subscriptions.append(sub_id)

        for sub_id in inactive_subscriptions:
            if await self.unsubscribe(sub_id, soft_mode=True):
                cleanup_count += 1

        logger.info(f"미사용 구독 정리 완료: {cleanup_count}개")
        return cleanup_count

    def get_ticket_usage(self) -> Dict[str, Any]:
        """티켓 사용률 모니터링"""
        snapshot_utilization = len(self.snapshot_pool.active_tickets) / self.snapshot_pool.max_size * 100
        realtime_utilization = len(self.realtime_pool.active_tickets) / self.realtime_pool.max_size * 100

        return {
            "snapshot_pool": {
                "utilization": snapshot_utilization,
                "active": len(self.snapshot_pool.active_tickets),
                "max": self.snapshot_pool.max_size,
                "warning": snapshot_utilization > 80
            },
            "realtime_pool": {
                "utilization": realtime_utilization,
                "active": len(self.realtime_pool.active_tickets),
                "max": self.realtime_pool.max_size,
                "warning": realtime_utilization > 80
            },
            "overall_health": "good" if max(snapshot_utilization, realtime_utilization) < 80 else "warning"
        }

    # =====================================================================
    # 문서 요구사항: 충돌 방지 및 검증
    # =====================================================================

    def detect_conflicts(self) -> List[Dict[str, Any]]:
        """snapshot vs realtime 모드 충돌 감지"""
        conflicts = []

        # 동일 데이터타입 + 심볼 조합에서 snapshot과 realtime 동시 존재 체크
        subscription_map = {}
        for sub_id, sub_info in self.active_subscriptions.items():
            key = f"{sub_info['data_type']}:{','.join(sorted(sub_info['symbols']))}"
            if key not in subscription_map:
                subscription_map[key] = {"snapshot": [], "realtime": []}
            subscription_map[key][sub_info["mode"]].append(sub_id)

        for key, modes in subscription_map.items():
            if modes["snapshot"] and modes["realtime"]:
                conflicts.append({
                    "type": "mode_conflict",
                    "key": key,
                    "snapshot_subscriptions": modes["snapshot"],
                    "realtime_subscriptions": modes["realtime"],
                    "recommendation": "Keep realtime, remove snapshot"
                })

        return conflicts

    def get_subscription_count(self) -> Dict[str, int]:
        """구독 개수 통계"""
        snapshot_count = sum(1 for sub in self.active_subscriptions.values()
                           if sub["mode"] == "snapshot")
        realtime_count = sum(1 for sub in self.active_subscriptions.values()
                           if sub["mode"] == "realtime")

        return {
            "total": len(self.active_subscriptions),
            "snapshot": snapshot_count,
            "realtime": realtime_count,
            "backup": len(self.backup_subscriptions)
        }

    def get_resubscribe_requests(self) -> List[Dict[str, Any]]:
        """재구독 요청 목록 (재연결 시 사용)"""
        requests = []
        for subscription in self.backup_subscriptions:
            request = {
                "data_type": subscription["data_type"],
                "symbols": subscription["symbols"],
                "mode": subscription["mode"],
                "original_ticket": subscription.get("ticket_id"),
                "backup_time": subscription.get("created_at", datetime.now()).isoformat()
            }
            requests.append(request)

        return requests

    def clear_backup(self) -> int:
        """백업 구독 정리"""
        count = len(self.backup_subscriptions)
        self.backup_subscriptions.clear()
        logger.info(f"백업 구독 정리: {count}개")
        return count

    def validate_subscription(self, data_type: str, symbols: List[str]) -> bool:
        """구독 중복 검증"""
        for subscription_id, info in self.active_subscriptions.items():
            if (info["data_type"] == data_type and
                set(info["symbols"]) == set(symbols)):
                logger.warning(f"중복 구독 감지: {data_type} - {symbols}")
                return False
        return True

    def get_full_stats(self) -> Dict[str, Any]:
        """전체 통계"""
        return {
            "subscription_manager": {
                "active_subscriptions": len(self.active_subscriptions),
                "backup_subscriptions": len(self.backup_subscriptions),
                "subscription_counts": self.get_subscription_count()
            },
            "snapshot_pool": self.snapshot_pool.get_stats(),
            "realtime_pool": self.realtime_pool.get_stats()
        }

    def create_upbit_message(self, subscription: Dict[str, Any]) -> List[Dict[str, Any]]:
        """업비트 WebSocket 메시지 형식으로 변환"""
        message = [
            {"ticket": subscription["ticket_id"]},
            {
                "type": subscription["data_type"],
                "codes": subscription["symbols"]
            },
            {"format": "DEFAULT"}
        ]

        # 스냅샷 옵션 추가
        if subscription["mode"] == "snapshot":
            message[1]["is_only_snapshot"] = True
        elif subscription["mode"] == "realtime":
            message[1]["is_only_realtime"] = True

        return message


# 편의 함수들
def create_subscription_manager_dict(snapshot_pool_size: int = 2,
                                   realtime_pool_size: int = 2) -> SubscriptionManager:
    """구독 관리자 생성"""
    return SubscriptionManager(snapshot_pool_size, realtime_pool_size)


# =====================================================================
# 문서 요구사항: 사용 패턴별 최적화 편의 함수
# =====================================================================

async def quick_price_check(manager: SubscriptionManager, symbol: str) -> Optional[str]:
    """패턴 1: 단발성 조회 - 현재 가격만 확인"""
    return await manager.request_snapshot("ticker", [symbol])


async def start_price_monitoring(manager: SubscriptionManager, symbol: str) -> Optional[str]:
    """패턴 2: 지속적 모니터링 - 가격 변화 실시간 추적"""
    return await manager.subscribe_realtime("ticker", [symbol])


async def bulk_market_snapshot(manager: SubscriptionManager,
                              krw_markets: List[str],
                              major_markets: List[str]) -> List[Dict[str, Any]]:
    """패턴 3: 일괄 초기화 - 전체 마켓 현재 상태 수집"""
    batch_requests = [
        {"data_type": "ticker", "symbols": krw_markets},
        {"data_type": "orderbook", "symbols": major_markets}
    ]
    return await manager.request_snapshots_batch(batch_requests)


async def hybrid_data_collection(manager: SubscriptionManager, symbol: str) -> Dict[str, Any]:
    """패턴 4: 하이브리드 사용 - 초기 데이터 + 실시간 업데이트"""
    initial_id = await manager.request_snapshot("ticker", [symbol])
    realtime_id = await manager.subscribe_realtime("ticker", [symbol])

    return {
        "initial_subscription": initial_id,
        "realtime_subscription": realtime_id,
        "pattern": "hybrid"
    }


async def smart_unsubscribe_pattern(manager: SubscriptionManager,
                                  subscription_id: str,
                                  force_hard: bool = False) -> bool:
    """패턴 5: 스마트 해제 사용"""
    if force_hard:
        # 완전 리셋이 필요한 경우 (하드 해제)
        return await manager.unsubscribe(subscription_id, soft_mode=False)
    else:
        # 리얼타임 구독 해제 (소프트 해제)
        return await manager.unsubscribe(subscription_id, soft_mode=True)


def create_snapshot_request(data_type: str, symbols: List[str]) -> Dict[str, Any]:
    """스냅샷 요청 생성"""
    return {
        "data_type": data_type,
        "symbols": symbols,
        "mode": "snapshot",
        "created_at": datetime.now()
    }


def create_realtime_request(data_type: str, symbols: List[str]) -> Dict[str, Any]:
    """리얼타임 요청 생성"""
    return {
        "data_type": data_type,
        "symbols": symbols,
        "mode": "realtime",
        "created_at": datetime.now()
    }
