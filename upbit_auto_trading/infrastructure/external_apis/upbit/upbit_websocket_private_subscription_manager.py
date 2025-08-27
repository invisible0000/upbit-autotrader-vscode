"""
업비트 Private WebSocket 전용 구독 관리자 v1.0 - 단순화된 설계

🎯 Private 특화 설계:
- myOrder, myAsset 2개 타입만 관리
- 1-2개 티켓으로 충분한 단순한 구독
- Public 대비 90% 복잡도 감소
- API 키 기반 인증 전용

🚀 핵심 특징:
- 단순한 티켓 관리 (1개 통합 티켓 권장)
- 마켓별 주문 구독 지원
- 자산 정보 실시간 업데이트
- 간단한 재구독 시스템
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import uuid

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("UpbitPrivateSubscriptionManager")


class PrivateDataType(Enum):
    """Private WebSocket 데이터 타입 (업비트 공식)"""
    MY_ORDER = "myOrder"    # 내 주문/체결 정보
    MY_ASSET = "myAsset"    # 내 자산(잔고) 정보


@dataclass
class PrivateSubscriptionInfo:
    """Private 구독 정보"""
    data_type: PrivateDataType
    markets: Optional[List[str]] = None  # myOrder용 마켓 필터
    ticket_id: Optional[str] = None
    created_at: Optional[datetime] = None
    is_active: bool = False

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class UpbitPrivateWebSocketSubscriptionManager:
    """
    업비트 Private WebSocket 전용 구독 관리자 v1.0

    🎯 단순화 원칙:
    - Private 특성에 맞는 최소한의 기능만 제공
    - Public 구독 관리자 대비 90% 복잡도 감소
    - 1개 통합 티켓으로 모든 구독 관리
    - API 키 기반 인증만 처리

    🚀 핵심 기능:
    - 간단한 구독 관리 (myOrder, myAsset)
    - 마켓별 주문 필터링
    - 단순한 재구독 메시지 생성
    - 구독 상태 추적
    """

    def __init__(self):
        """Private 구독 관리자 초기화"""
        self.logger = create_component_logger("UpbitPrivateSubscriptionManager")

        # 단순한 구독 상태 관리
        self.subscriptions: Dict[PrivateDataType, PrivateSubscriptionInfo] = {}
        self.current_ticket_id: Optional[str] = None

        # 통계 정보
        self.created_at = datetime.now()
        self.subscription_count = 0
        self.message_sent_count = 0

        self.logger.info("✅ Private WebSocket 구독 관리자 초기화 완료")

    def subscribe_my_orders(self, markets: Optional[List[str]] = None) -> str:
        """
        내 주문 정보 구독

        Args:
            markets: 구독할 마켓 목록 (None이면 모든 마켓)

        Returns:
            str: 티켓 ID
        """
        ticket_id = self._ensure_ticket()

        subscription = PrivateSubscriptionInfo(
            data_type=PrivateDataType.MY_ORDER,
            markets=markets,
            ticket_id=ticket_id,
            is_active=True
        )

        self.subscriptions[PrivateDataType.MY_ORDER] = subscription
        self.subscription_count += 1

        self.logger.info(f"✅ 내 주문 구독 등록: {markets or '전체 마켓'}")
        return ticket_id

    def subscribe_my_assets(self) -> str:
        """
        내 자산 정보 구독

        Returns:
            str: 티켓 ID
        """
        ticket_id = self._ensure_ticket()

        subscription = PrivateSubscriptionInfo(
            data_type=PrivateDataType.MY_ASSET,
            markets=None,  # 자산은 마켓 필터 없음
            ticket_id=ticket_id,
            is_active=True
        )

        self.subscriptions[PrivateDataType.MY_ASSET] = subscription
        self.subscription_count += 1

        self.logger.info("✅ 내 자산 구독 등록")
        return ticket_id

    def unsubscribe(self, data_type: PrivateDataType) -> bool:
        """
        특정 타입 구독 해제

        Args:
            data_type: 해제할 데이터 타입

        Returns:
            bool: 해제 성공 여부
        """
        if data_type in self.subscriptions:
            del self.subscriptions[data_type]
            self.logger.info(f"✅ {data_type.value} 구독 해제")
            return True

        self.logger.warning(f"⚠️ {data_type.value} 구독이 없어 해제 실패")
        return False

    def clear_all_subscriptions(self) -> None:
        """모든 구독 해제"""
        self.subscriptions.clear()
        self.current_ticket_id = None
        self.logger.info("✅ 모든 구독 해제 완료")

    def create_subscription_message(self) -> Optional[List[Dict[str, Any]]]:
        """
        현재 구독 상태를 기반으로 WebSocket 메시지 생성

        Returns:
            Optional[List[Dict]]: WebSocket 전송용 메시지
        """
        if not self.subscriptions:
            self.logger.warning("구독할 데이터가 없어 메시지 생성 실패")
            return None

        ticket_id = self._ensure_ticket()
        message = [{"ticket": ticket_id}]

        # 각 구독 타입별 메시지 추가
        for data_type, subscription in self.subscriptions.items():
            if data_type == PrivateDataType.MY_ORDER:
                if subscription.markets:
                    message.append({
                        "type": "myOrder",
                        "codes": subscription.markets
                    })
                else:
                    message.append({"type": "myOrder"})

            elif data_type == PrivateDataType.MY_ASSET:
                message.append({"type": "myAsset"})

        # 포맷 지정
        message.append({"format": "DEFAULT"})

        self.message_sent_count += 1
        self.logger.debug(f"📤 구독 메시지 생성: {len(self.subscriptions)}개 타입")

        return message

    def get_resubscribe_message(self) -> Optional[List[Dict[str, Any]]]:
        """
        재구독용 메시지 생성 (연결 복구 시 사용)

        Returns:
            Optional[List[Dict]]: 재구독 메시지
        """
        return self.create_subscription_message()

    def has_subscriptions(self) -> bool:
        """활성 구독이 있는지 확인"""
        return len(self.subscriptions) > 0

    def has_order_subscription(self) -> bool:
        """주문 구독이 있는지 확인"""
        return PrivateDataType.MY_ORDER in self.subscriptions

    def has_asset_subscription(self) -> bool:
        """자산 구독이 있는지 확인"""
        return PrivateDataType.MY_ASSET in self.subscriptions

    def get_subscription_info(self) -> Dict[str, Any]:
        """
        현재 구독 정보 조회

        Returns:
            Dict: 구독 상태 정보
        """
        subscription_details = {}

        for data_type, subscription in self.subscriptions.items():
            subscription_details[data_type.value] = {
                "markets": subscription.markets,
                "ticket_id": subscription.ticket_id,
                "created_at": subscription.created_at,
                "is_active": subscription.is_active
            }

        return {
            "active_subscriptions": subscription_details,
            "total_subscriptions": len(self.subscriptions),
            "current_ticket": self.current_ticket_id,
            "subscription_count": self.subscription_count,
            "message_sent_count": self.message_sent_count,
            "created_at": self.created_at
        }

    def get_subscribed_markets(self) -> List[str]:
        """
        구독 중인 모든 마켓 목록 반환

        Returns:
            List[str]: 마켓 목록
        """
        markets = set()

        if PrivateDataType.MY_ORDER in self.subscriptions:
            order_subscription = self.subscriptions[PrivateDataType.MY_ORDER]
            if order_subscription.markets:
                markets.update(order_subscription.markets)

        return list(markets)

    def _ensure_ticket(self) -> str:
        """티켓 ID 확보 (없으면 생성)"""
        if self.current_ticket_id is None:
            self.current_ticket_id = f"private-{uuid.uuid4().hex[:8]}"
            self.logger.debug(f"🎫 새 티켓 생성: {self.current_ticket_id}")

        return self.current_ticket_id

    def _reset_ticket(self) -> None:
        """티켓 재설정 (재연결 시 호출)"""
        old_ticket = self.current_ticket_id
        self.current_ticket_id = None

        if old_ticket:
            self.logger.debug(f"🎫 티켓 재설정: {old_ticket} → 신규 생성 대기")

    def __repr__(self) -> str:
        """객체 문자열 표현"""
        active_types = [dt.value for dt in self.subscriptions.keys()]
        return f"UpbitPrivateWebSocketSubscriptionManager(구독: {active_types})"
