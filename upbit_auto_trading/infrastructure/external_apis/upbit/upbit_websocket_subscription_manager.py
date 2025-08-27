"""
업비트 WebSocket 구독 관리자 v1.0 - 전담 구독 관리 시스템

🎯 분리 목적:
- upbit_websocket_public_client.py의 1400+ 라인 복잡도 해결
- 구독 관리 로직의 완전 독립성 확보
- 티켓 기반 구독 시스템의 전문화
- 재구독/복원 시스템의 안정성 향상

🚀 핵심 기능:
- 통합 구독 관리 (UnifiedSubscription)
- 레거시 호환성 관리 (SubscriptionResult)
- 티켓별 실제 API 요청 메시지 복원
- 스트림 타입(SNAPSHOT/REALTIME) 분리 관리
- 재구독 시스템 (원본 메시지 기반)
- 서브시스템별 구독 정보 구분
"""
import json
import uuid
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("UpbitSubscriptionManager")


@dataclass
class SubscriptionMetrics:
    """구독 통계 정보"""
    total_tickets: int = 0
    total_symbols: int = 0
    messages_sent: int = 0
    resubscribe_count: int = 0
    creation_time: Optional[datetime] = None
    last_update_time: Optional[datetime] = None

    def __post_init__(self):
        if self.creation_time is None:
            self.creation_time = datetime.now()
        if self.last_update_time is None:
            self.last_update_time = datetime.now()

    def update(self):
        """통계 업데이트"""
        self.last_update_time = datetime.now()


class SubscriptionResult:
    """구독 결과 관리 클래스 (레거시 호환성 + 개선)"""

    def __init__(self):
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
        self.created_at = datetime.now()

    def add_subscription(self, data_type: str, symbols: List[str], **metadata):
        """구독 추가 (교체 방식 - Legacy 복구)"""
        self.subscriptions[data_type] = {
            "symbols": list(symbols),  # 새 심볼들로 교체 (누적 X)
            "created_at": datetime.now(),
            "metadata": metadata or {}
        }

    def add_subscription_with_key(self, type_key: str, symbols: List[str], **kwargs) -> None:
        """키로 직접 구독 추가 (캔들 타입 전용)"""
        if type_key not in self.subscriptions:
            self.subscriptions[type_key] = {
                'symbols': set(),
                'created_at': datetime.now(),
                'metadata': {}
            }

        # 심볼 추가 (중복 제거)
        if isinstance(self.subscriptions[type_key]['symbols'], list):
            self.subscriptions[type_key]['symbols'] = set(self.subscriptions[type_key]['symbols'])
        self.subscriptions[type_key]['symbols'].update(symbols)

        # 메타데이터 업데이트
        if kwargs:
            self.subscriptions[type_key]['metadata'].update(kwargs)

    def get_subscriptions(self) -> Dict[str, Dict[str, Any]]:
        """구독 정보 반환"""
        result = {}
        for type_key, sub_data in self.subscriptions.items():
            # set을 list로 변환 처리
            symbols = sub_data['symbols']
            if isinstance(symbols, set):
                symbols = list(symbols)

            result[type_key] = {
                'symbols': symbols,
                'created_at': sub_data['created_at'],
                'metadata': sub_data.get('metadata', {})
            }
        return result

    def get_symbols_by_type(self, data_type_value: str) -> List[str]:
        """특정 타입의 구독 심볼 목록 반환"""
        if data_type_value in self.subscriptions:
            symbols = self.subscriptions[data_type_value]['symbols']
            return list(symbols) if isinstance(symbols, set) else symbols
        return []

    def get_candle_subscriptions(self) -> List[str]:
        """모든 캔들 구독 심볼 통합 반환"""
        candle_symbols = set()
        for key in self.subscriptions:
            if key.startswith('candle.'):
                symbols = self.subscriptions[key]['symbols']
                if isinstance(symbols, set):
                    candle_symbols.update(symbols)
                else:
                    candle_symbols.update(symbols)
        return list(candle_symbols)

    def has_candle_subscriptions(self) -> bool:
        """캔들 구독이 있는지 확인"""
        return any(key.startswith('candle.') for key in self.subscriptions)

    def remove_subscription(self, data_type: str):
        """구독 제거"""
        if data_type in self.subscriptions:
            del self.subscriptions[data_type]

    def clear(self) -> None:
        """모든 구독 정보 삭제"""
        self.subscriptions.clear()


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
        """구독 타입 추가 - 업비트 API 형식에 맞게 자동 변환 및 검증"""
        # 캔들 타입 자동 변환 처리
        if data_type == "candle":
            unit = kwargs.get("unit", "1m")  # 기본값 1분봉

            # 업비트 지원 타임프레임 (공식 문서 기준 - 숫자 값 직접 검증)
            VALID_MINUTE_UNITS = [1, 3, 5, 10, 15, 30, 60, 240]
            VALID_SECOND_UNITS = [1]  # 업비트는 1초봉만 지원

            SUPPORTED_CANDLE_STRINGS = {
                # 문자열 형태
                "1s", "candle.1s",
                "1m", "3m", "5m", "10m", "15m", "30m", "60m", "240m",
                "candle.1m", "candle.3m", "candle.5m", "candle.10m",
                "candle.15m", "candle.30m", "candle.60m", "candle.240m"
            }

            # 변환 로직
            converted_type = None

            if unit.startswith("candle.") and unit in SUPPORTED_CANDLE_STRINGS:
                # "candle.5m" 형태 - 이미 정확한 형식 (최우선 처리)
                converted_type = unit
            elif unit.endswith("m"):
                # "5m" 형태 또는 "candle.5m"에서 candle. 제거 후 처리
                if unit.startswith("candle."):
                    minute_str = unit[7:-1]  # "candle." 제거하고 마지막 "m" 제거
                else:
                    minute_str = unit[:-1]

                if minute_str.isdigit():
                    minute_val = int(minute_str)
                    if minute_val in VALID_MINUTE_UNITS:
                        converted_type = f"candle.{minute_val}m"

            elif unit.endswith("s"):
                # "1s" 형태 또는 "candle.1s"에서 candle. 제거 후 처리
                if unit.startswith("candle."):
                    second_str = unit[7:-1]  # "candle." 제거하고 마지막 "s" 제거
                else:
                    second_str = unit[:-1]

                if second_str.isdigit():
                    second_val = int(second_str)
                    if second_val in VALID_SECOND_UNITS:
                        converted_type = f"candle.{second_val}s"

            elif unit.isdigit():
                # "5" 형태 - 분봉으로 해석
                unit_val = int(unit)
                if unit_val == 0:
                    # 특별 케이스: 0은 가장 짧은 간격인 1초봉으로 매핑
                    converted_type = "candle.1s"
                elif unit_val in VALID_MINUTE_UNITS:
                    converted_type = f"candle.{unit_val}m"

            # 검증 결과 처리
            if converted_type:
                data_type = converted_type
            else:
                # 지원하지 않는 타임프레임에 대한 에러 처리
                supported_list = ["1s", "1m", "3m", "5m", "10m", "15m", "30m", "60m", "240m"]
                raise ValueError(
                    f"지원하지 않는 캔들 타임프레임: '{unit}'. "
                    f"지원되는 형식: {supported_list}"
                )

            # unit 파라미터는 제거 (이미 type에 포함됨)
            kwargs = {k: v for k, v in kwargs.items() if k != "unit"}

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
            self.last_updated = datetime.now()

    def get_subscription_message(self) -> List[Dict[str, Any]]:
        """통합 구독 메시지 생성"""
        if not self.types:
            return []

        message = [{"ticket": self.ticket}]

        # 모든 타입을 하나의 메시지에 포함
        for data_type, config in self.types.items():
            type_message = {"type": data_type, **config}
            message.append(type_message)

        message.append({"format": "DEFAULT"})
        return message

    def get_subscription_types(self) -> List[str]:
        """현재 구독된 모든 타입 반환"""
        return list(self.types.keys())

    def is_empty(self) -> bool:
        """빈 구독인지 확인"""
        return len(self.types) == 0


class UpbitWebSocketSubscriptionManager:
    """
    업비트 WebSocket 구독 관리자 v1.0 - 전담 구독 관리 시스템

    🎯 책임 범위:
    - 티켓 기반 구독 관리 (생성/수정/삭제)
    - 실제 API 요청 메시지 복원 및 재구독
    - 스트림 타입(SNAPSHOT/REALTIME) 분리 관리
    - 레거시 호환성 유지 (기존 테스트 지원)
    - 구독 통계 및 상태 모니터링

    🚀 핵심 특징:
    - 완전한 독립성: WebSocket 연결과 분리
    - 재구독 안정성: 원본 메시지 기반 복원
    - 티켓 효율성: 업비트 5개 제한 최적화
    - 테스트 호환성: 기존 테스트 100% 지원
    """

    def __init__(self, max_tickets: int = 5, enable_ticket_reuse: bool = True):
        """
        구독 관리자 초기화

        Args:
            max_tickets: 최대 동시 티켓 수 (업비트 권장: 5개)
            enable_ticket_reuse: 티켓 재사용 활성화 여부
        """
        self.logger = create_component_logger("UpbitSubscriptionManager")

        # 구독 관리 (테스트 호환성)
        self._subscription_manager = SubscriptionResult()

        # 통합 구독 관리 (새로운 방식)
        self._unified_subscriptions: Dict[str, UnifiedSubscription] = {}
        self._current_ticket = None

        # 티켓 관리 설정
        self._max_tickets = max_tickets
        self.enable_ticket_reuse = enable_ticket_reuse
        self._shared_tickets: Dict[str, str] = {}  # data_type -> ticket_id
        self._ticket_usage_count: Dict[str, int] = {}

        # 통계 정보
        self._metrics = SubscriptionMetrics()

        self.logger.info("✅ UpbitWebSocketSubscriptionManager v1.0 초기화 완료")

    # ================================================================
    # 티켓 관리 시스템 (성능 최적화)
    # ================================================================

    def _generate_ticket_id(self, purpose: str = "unified") -> str:
        """티켓 ID 생성"""
        return f"{purpose}-{uuid.uuid4().hex[:8]}"

    def _get_or_create_ticket(self, data_type: str) -> str:
        """
        데이터 타입별 티켓 획득 또는 생성 (재사용 최적화)

        Args:
            data_type: 데이터 타입 문자열

        Returns:
            str: 티켓 ID
        """
        if not self.enable_ticket_reuse:
            # 티켓 재사용 비활성화 시 기존 방식
            return self._generate_ticket_id("auto-trader")

        # 이미 할당된 티켓이 있으면 재사용
        if data_type in self._shared_tickets:
            existing_ticket = self._shared_tickets[data_type]
            self._ticket_usage_count[existing_ticket] = self._ticket_usage_count.get(existing_ticket, 0) + 1
            self.logger.debug(f"티켓 재사용: {existing_ticket[:8]}... (사용횟수: {self._ticket_usage_count[existing_ticket]})")
            return existing_ticket

        # 새 티켓 생성 (최대 개수 체크)
        if len(self._shared_tickets) >= self._max_tickets:
            # 가장 적게 사용된 티켓을 재할당
            least_used_type = min(self._shared_tickets.keys(),
                                  key=lambda t: self._ticket_usage_count.get(self._shared_tickets[t], 0))
            reused_ticket = self._shared_tickets[least_used_type]

            # 기존 타입에서 제거하고 새 타입에 할당
            del self._shared_tickets[least_used_type]
            self._shared_tickets[data_type] = reused_ticket
            self._ticket_usage_count[reused_ticket] = self._ticket_usage_count.get(reused_ticket, 0) + 1

            self.logger.info(f"티켓 재할당: {reused_ticket[:8]}... ({least_used_type} → {data_type})")
            return reused_ticket

        # 새 티켓 생성
        new_ticket = self._generate_ticket_id("reuse")
        self._shared_tickets[data_type] = new_ticket
        self._ticket_usage_count[new_ticket] = 1

        self.logger.info(f"새 티켓 생성: {new_ticket[:8]}... (타입: {data_type}, 총 {len(self._shared_tickets)}개)")
        return new_ticket

    def get_ticket_statistics(self) -> Dict[str, Any]:
        """티켓 사용 통계 반환"""
        # 통합 구독 방식 통계
        unified_tickets = len(self._unified_subscriptions)
        total_subscriptions = len(self.get_consolidated_view())

        # 효율성 계산: 전통적 방식(각 타입마다 1티켓) vs 통합 방식
        traditional_tickets = max(total_subscriptions, 1)
        actual_tickets = max(unified_tickets, 1)
        efficiency = ((traditional_tickets - actual_tickets) / traditional_tickets) * 100 if traditional_tickets > 0 else 0

        return {
            "enable_ticket_reuse": self.enable_ticket_reuse,
            "max_tickets": self._max_tickets,
            "total_tickets": unified_tickets,
            "active_tickets": unified_tickets,
            "unified_subscriptions": unified_tickets,
            "traditional_method_tickets": traditional_tickets,
            "ticket_assignments": {
                f"unified-{i}": list(sub.types.keys())
                for i, sub in enumerate(self._unified_subscriptions.values())
            },
            "current_ticket": self._current_ticket[:8] + "..." if self._current_ticket else None,
            "reuse_efficiency": efficiency
        }

    def clear_ticket_cache(self) -> None:
        """티켓 캐시 초기화 (재연결 시 호출)"""
        self._shared_tickets.clear()
        self._ticket_usage_count.clear()
        self.logger.info("티켓 캐시 초기화 완료")

    # ================================================================
    # 구독 관리 핵심 메서드
    # ================================================================

    def add_unified_subscription(self, data_type: str, symbols: List[str], **kwargs) -> str:
        """
        통합 구독 추가

        Args:
            data_type: 데이터 타입 ('ticker', 'candle', etc)
            symbols: 구독할 심볼 목록
            **kwargs: 추가 구독 옵션

        Returns:
            str: 생성된 티켓 ID
        """
        try:
            # 현재 티켓이 없으면 새로 생성
            if not self._current_ticket:
                self._current_ticket = self._generate_ticket_id("unified")
                self._unified_subscriptions[self._current_ticket] = UnifiedSubscription(self._current_ticket)

            # 통합 구독에 타입 추가
            unified_sub = self._unified_subscriptions[self._current_ticket]
            unified_sub.add_subscription_type(data_type, symbols, **kwargs)

            # 테스트 호환성을 위한 구독 정보 업데이트
            self._subscription_manager.add_subscription(data_type, symbols, **kwargs)

            # 통계 업데이트
            self._metrics.total_symbols = len(unified_sub.symbols)
            self._metrics.update()

            self.logger.info(f"✅ {data_type} 통합 구독 추가: {len(symbols)}개 심볼, 티켓: {self._current_ticket}")
            return self._current_ticket

        except Exception as e:
            self.logger.error(f"❌ {data_type} 구독 추가 실패: {e}")
            raise

    def add_idle_subscription(self, idle_symbol: str = "KRW-BTC", ultra_quiet: bool = True) -> str:
        """
        Idle 모드 구독 추가 (기존 구독과 분리)

        Args:
            idle_symbol: Idle 상태에서 유지할 심볼
            ultra_quiet: True면 240m 캔들 snapshot으로 초저활동

        Returns:
            str: 생성된 idle 티켓 ID
        """
        try:
            # 새로운 idle 전용 티켓 생성 (기존 구독과 분리)
            idle_ticket = self._generate_ticket_id("idle")

            if ultra_quiet:
                # 초저활동 모드: 240분 캔들 + snapshot only
                idle_subscription = UnifiedSubscription(idle_ticket)
                idle_subscription.add_subscription_type("candle.240m", [idle_symbol], isOnlySnapshot=True)
                mode_desc = "240m 캔들 snapshot (4시간당 1개 메시지)"
                idle_type = "candle.240m"
            else:
                # 일반 idle: ticker
                idle_subscription = UnifiedSubscription(idle_ticket)
                idle_subscription.add_subscription_type("ticker", [idle_symbol])
                mode_desc = "ticker (실시간 메시지)"
                idle_type = "ticker"

            self._unified_subscriptions[idle_ticket] = idle_subscription

            # 테스트 호환성을 위한 구독 정보 추가 (기존 구독 유지)
            if ultra_quiet:
                self._subscription_manager.add_subscription(idle_type, [idle_symbol], isOnlySnapshot=True)
            else:
                self._subscription_manager.add_subscription(idle_type, [idle_symbol])

            # 통계 업데이트
            self._metrics.total_tickets = len(self._unified_subscriptions)
            self._metrics.update()

            self.logger.info(f"✅ Idle 구독 추가: {idle_symbol} {mode_desc}, 티켓: {idle_ticket}")
            return idle_ticket

        except Exception as e:
            self.logger.error(f"❌ Idle 구독 추가 실패: {e}")
            raise

    def remove_subscription_by_type(self, data_type: str) -> List[str]:
        """
        데이터 타입별 구독 제거

        Args:
            data_type: 제거할 데이터 타입

        Returns:
            List[str]: 영향받은 티켓 ID 목록
        """
        affected_tickets = []

        try:
            if self._current_ticket and self._current_ticket in self._unified_subscriptions:
                unified_sub = self._unified_subscriptions[self._current_ticket]

                # 해당 데이터 타입과 일치하는 모든 키 찾기
                keys_to_remove = []
                if data_type == "candle":
                    # 캔들의 경우 "candle.XXX" 형태의 모든 키 찾기
                    keys_to_remove = [key for key in unified_sub.types.keys() if key.startswith("candle.")]
                else:
                    # 다른 타입은 정확한 매칭
                    if data_type in unified_sub.types:
                        keys_to_remove = [data_type]

                # 찾은 키들 제거
                for key in keys_to_remove:
                    unified_sub.remove_subscription_type(key)
                    self.logger.debug(f"🗑️ 구독 타입 제거: {key}")

                if keys_to_remove:
                    affected_tickets.append(self._current_ticket)

                # 모든 타입이 제거되면 티켓 자체 제거
                if unified_sub.is_empty():
                    del self._unified_subscriptions[self._current_ticket]
                    self._current_ticket = None
                    self.logger.info(f"🗑️ 빈 티켓 제거: {self._current_ticket}")

            # 테스트 호환성
            self._subscription_manager.remove_subscription(data_type)

            # 통계 업데이트
            self._metrics.total_tickets = len(self._unified_subscriptions)
            self._metrics.update()

            self.logger.info(f"✅ {data_type} 구독 제거 완료")
            return affected_tickets

        except Exception as e:
            self.logger.error(f"❌ {data_type} 구독 제거 실패: {e}")
            raise

    def remove_ticket(self, ticket_id: str) -> bool:
        """
        특정 티켓 완전 제거

        Args:
            ticket_id: 제거할 티켓 ID

        Returns:
            bool: 제거 성공 여부
        """
        try:
            if ticket_id in self._unified_subscriptions:
                del self._unified_subscriptions[ticket_id]

                # 현재 티켓이 제거된 경우 초기화
                if self._current_ticket == ticket_id:
                    self._current_ticket = None

                # 통계 업데이트
                self._metrics.total_tickets = len(self._unified_subscriptions)
                self._metrics.update()

                self.logger.info(f"✅ 티켓 완전 제거: {ticket_id}")
                return True
            else:
                self.logger.warning(f"⚠️ 제거할 티켓을 찾을 수 없음: {ticket_id}")
                return False

        except Exception as e:
            self.logger.error(f"❌ 티켓 제거 실패: {ticket_id} - {e}")
            return False

    def clear_all_subscriptions(self) -> bool:
        """모든 구독 정보 초기화"""
        try:
            self._unified_subscriptions.clear()
            self._subscription_manager.clear()
            self._current_ticket = None

            # 통계 초기화
            self._metrics = SubscriptionMetrics()

            self.logger.info("✅ 모든 구독 정보 초기화 완료")
            return True

        except Exception as e:
            self.logger.error(f"❌ 구독 정보 초기화 실패: {e}")
            return False

    def create_subscription_replacement_message(
        self, new_subscriptions: List[Dict[str, Any]]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        구독 교체용 메시지 생성 (스마트 라우팅 지원)

        Args:
            new_subscriptions: 새로운 구독 목록

        Returns:
            Optional[List[Dict]]: WebSocket 전송용 메시지 (None이면 실패)
        """
        try:
            if not new_subscriptions:
                return None

            # 새로운 티켓으로 메시지 생성
            replacement_ticket = self._generate_ticket_id("replace")
            message = [{"ticket": replacement_ticket}]

            # 모든 새 구독을 하나의 메시지에 포함
            for sub_config in new_subscriptions:
                sub_type = sub_config.get('type')
                symbols = sub_config.get('symbols', [])

                if not sub_type or not symbols:
                    continue

                # 구독 메시지 섹션 생성
                config = {k: v for k, v in sub_config.items() if k not in ['type', 'symbols']}
                message.append({
                    "type": sub_type,
                    "codes": symbols,
                    **config
                })

            message.append({"format": "DEFAULT"})

            self.logger.info(f"🔄 교체 메시지 생성: 티켓 {replacement_ticket}, {len(new_subscriptions)}개 구독")
            return message

        except Exception as e:
            self.logger.error(f"❌ 교체 메시지 생성 실패: {e}")
            return None

    def create_snapshot_message(self, data_type: str, symbols: List[str], **kwargs) -> Optional[List[Dict[str, Any]]]:
        """
        스냅샷 요청용 메시지 생성 (일회성 데이터 조회)

        Args:
            data_type: 데이터 타입
            symbols: 심볼 목록
            **kwargs: 추가 옵션

        Returns:
            Optional[List[Dict]]: WebSocket 전송용 메시지
        """
        try:
            snapshot_ticket = self._generate_ticket_id("snapshot")

            message = [
                {"ticket": snapshot_ticket},
                {
                    "type": data_type,
                    "codes": symbols,
                    "isOnlySnapshot": True,  # 스냅샷만 요청
                    **kwargs
                },
                {"format": "DEFAULT"}
            ]

            self.logger.info(f"📸 스냅샷 메시지 생성: {data_type} - {len(symbols)}개 심볼")
            return message

        except Exception as e:
            self.logger.error(f"❌ 스냅샷 메시지 생성 실패: {e}")
            return None

    # ================================================================
    # 정보 조회 메서드 (티켓별 실제 API 요청 메시지 기반)
    # ================================================================

    def get_subscriptions(self) -> Dict[str, Any]:
        """
        티켓별 실제 업비트 API 요청 메시지 기반 구독 정보 조회

        Returns:
            Dict[str, Any]: {
                'tickets': Dict - 티켓별 상세 정보
                'consolidated_view': Dict - 기존 호환성을 위한 통합 뷰
                'total_tickets': int - 총 티켓 수
                'current_ticket': str - 현재 활성 티켓
                'resubscribe_ready': bool - 모든 티켓이 재구독 가능한지
            }
        """
        # 티켓별 상세 정보 (실제 API 요청 메시지 포함)
        tickets_info = {}

        for ticket_id, unified_sub in self._unified_subscriptions.items():
            # 실제 업비트 API 요청 메시지 생성 (재전송 가능)
            raw_message = unified_sub.get_subscription_message()

            # 스트림 설정 분석
            stream_configs = {}
            subscription_types = list(unified_sub.types.keys())

            for sub_type, type_config in unified_sub.types.items():
                # SNAPSHOT/REALTIME 분석
                is_snapshot_only = type_config.get('isOnlySnapshot', False)
                is_realtime = not is_snapshot_only

                stream_configs[sub_type] = {
                    'codes': type_config.get('codes', []),
                    'raw_config': type_config,
                    'is_snapshot_only': is_snapshot_only,
                    'is_realtime': is_realtime,
                    'stream_type': 'SNAPSHOT' if is_snapshot_only else 'REALTIME'
                }

            tickets_info[ticket_id] = {
                'ticket': unified_sub.ticket,
                'raw_message': raw_message,
                'resubscribe_message': raw_message,  # 재구독용 메시지 (raw_message와 동일)
                'subscription_types': subscription_types,
                'total_symbols': len(unified_sub.symbols),
                'stream_configs': stream_configs,
                'created_at': unified_sub.created_at,
                'last_updated': unified_sub.last_updated,
                'message_count': unified_sub.message_count,
                'is_resendable': len(raw_message) > 0 and 'ticket' in (raw_message[0] if raw_message else {}),
                'symbols_summary': self._format_symbols_for_log(list(unified_sub.symbols), max_display=3)
            }

        # 기존 호환성을 위한 통합 뷰 (레거시 테스트 지원)
        consolidated_view = self.get_consolidated_view()

        # 재구독 준비 상태 확인
        resubscribe_ready = all(
            ticket_info['is_resendable']
            for ticket_info in tickets_info.values()
        )

        return {
            'tickets': tickets_info,
            'consolidated_view': consolidated_view,
            'total_tickets': len(self._unified_subscriptions),
            'current_ticket': self._current_ticket,
            'resubscribe_ready': resubscribe_ready
        }

    def get_consolidated_view(self) -> Dict[str, Dict[str, Any]]:
        """기존 호환성을 위한 통합 뷰 반환"""
        consolidated_view = {}

        for ticket_id, unified_sub in self._unified_subscriptions.items():
            for subscription_type, type_config in unified_sub.types.items():
                if subscription_type not in consolidated_view:
                    consolidated_view[subscription_type] = {
                        'symbols': set(),
                        'created_at': unified_sub.created_at,
                        'metadata': type_config.copy()
                    }

                # 심볼 통합 (중복 제거)
                symbols = type_config.get('codes', [])
                consolidated_view[subscription_type]['symbols'].update(symbols)

                # 메타데이터 병합 (codes 제외)
                metadata = {k: v for k, v in type_config.items() if k != 'codes'}
                consolidated_view[subscription_type]['metadata'].update(metadata)

        # set을 list로 변환
        for sub_type, sub_data in consolidated_view.items():
            consolidated_view[sub_type]['symbols'] = list(sub_data['symbols'])

        return consolidated_view

    def get_active_subscriptions(self) -> Dict[str, Dict[str, Any]]:
        """활성 구독 정보 조회 - 레거시 호환성을 위해 consolidated_view 반환"""
        return self.get_consolidated_view()

    def get_all_tickets_info(self) -> Dict[str, Any]:
        """모든 티켓의 상세 정보 조회 (디버깅용)"""
        tickets_info = {}

        for ticket_id, unified_sub in self._unified_subscriptions.items():
            tickets_info[ticket_id] = {
                'ticket': unified_sub.ticket,
                'created_at': unified_sub.created_at,
                'last_updated': unified_sub.last_updated,
                'message_count': unified_sub.message_count,
                'subscription_types': list(unified_sub.types.keys()),
                'total_symbols': len(unified_sub.symbols),
                'symbols_by_type': {
                    sub_type: type_config.get('codes', [])
                    for sub_type, type_config in unified_sub.types.items()
                }
            }

        return {
            'total_tickets': len(self._unified_subscriptions),
            'current_ticket': self._current_ticket,
            'tickets': tickets_info
        }

    def get_legacy_subscription_manager_info(self) -> Dict[str, Dict[str, Any]]:
        """레거시 _subscription_manager 정보 조회 (테스트 호환성 확인용)"""
        return self._subscription_manager.get_subscriptions()

    # ================================================================
    # 재구독 시스템 (원본 메시지 기반)
    # ================================================================

    def get_resubscribe_messages(self) -> List[Dict[str, Any]]:
        """
        모든 티켓의 재구독 메시지 목록 반환

        Returns:
            List[Dict]: [{'ticket_id': str, 'message': List[Dict]}, ...]
        """
        resubscribe_messages = []

        for ticket_id, unified_sub in self._unified_subscriptions.items():
            raw_message = unified_sub.get_subscription_message()
            if raw_message:  # 빈 메시지 제외
                resubscribe_messages.append({
                    'ticket_id': ticket_id,
                    'message': raw_message,
                    'subscription_types': list(unified_sub.types.keys()),
                    'total_symbols': len(unified_sub.symbols)
                })

        return resubscribe_messages

    def get_resubscribe_message_by_ticket(self, ticket_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        특정 티켓의 재구독 메시지 반환

        Args:
            ticket_id: 티켓 ID

        Returns:
            Optional[List[Dict]]: 재구독 메시지 (없으면 None)
        """
        if ticket_id in self._unified_subscriptions:
            unified_sub = self._unified_subscriptions[ticket_id]
            raw_message = unified_sub.get_subscription_message()
            return raw_message if raw_message else None
        return None

    def validate_resubscribe_messages(self) -> Dict[str, bool]:
        """
        모든 티켓의 재구독 메시지 유효성 검증

        Returns:
            Dict[str, bool]: 티켓별 검증 결과
        """
        validation_results = {}

        for ticket_id, unified_sub in self._unified_subscriptions.items():
            try:
                raw_message = unified_sub.get_subscription_message()

                # 기본 구조 검증
                if not raw_message or len(raw_message) < 2:
                    validation_results[ticket_id] = False
                    continue

                # 티켓 필드 검증
                if 'ticket' not in raw_message[0]:
                    validation_results[ticket_id] = False
                    continue

                # 타입 필드 검증
                if 'type' not in raw_message[1]:
                    validation_results[ticket_id] = False
                    continue

                # JSON 직렬화 가능성 검증
                json_str = json.dumps(raw_message)
                restored_message = json.loads(json_str)
                if restored_message != raw_message:
                    validation_results[ticket_id] = False
                    continue

                validation_results[ticket_id] = True

            except Exception as e:
                self.logger.warning(f"⚠️ 티켓 {ticket_id} 검증 실패: {e}")
                validation_results[ticket_id] = False

        return validation_results

    # ================================================================
    # 스트림 타입 및 핸들러 추출 시스템
    # ================================================================

    def extract_handlers_by_stream_type(self, stream_type: str) -> Dict[str, List[str]]:
        """
        스트림 타입별 핸들러 추출 가능한 구독 정보 반환

        Args:
            stream_type: 'SNAPSHOT' 또는 'REALTIME'

        Returns:
            Dict[str, List[str]]: {ticket_id: [applicable_subscription_types]}
        """
        applicable_tickets = {}
        subscription_info = self.get_subscriptions()

        for ticket_id, ticket_info in subscription_info['tickets'].items():
            applicable_types = []

            for sub_type, config in ticket_info['stream_configs'].items():
                if config['stream_type'] == stream_type:
                    applicable_types.append(sub_type)

            if applicable_types:
                applicable_tickets[ticket_id] = applicable_types

        return applicable_tickets

    def get_symbols_by_ticket_and_type(self, ticket_id: str, subscription_type: str) -> List[str]:
        """
        특정 티켓의 특정 구독 타입에서 심볼 목록 추출

        Args:
            ticket_id: 티켓 ID
            subscription_type: 구독 타입 (예: 'ticker', 'candle.5m')

        Returns:
            List[str]: 해당 조건의 심볼 목록
        """
        subscription_info = self.get_subscriptions()

        if ticket_id not in subscription_info['tickets']:
            return []

        ticket_info = subscription_info['tickets'][ticket_id]
        stream_config = ticket_info['stream_configs'].get(subscription_type, {})

        return stream_config.get('codes', [])

    # ================================================================
    # 통계 및 유틸리티
    # ================================================================

    def get_subscription_metrics(self) -> Dict[str, Any]:
        """구독 통계 정보 반환"""
        creation_time = self._metrics.creation_time or datetime.now()
        uptime_seconds = (datetime.now() - creation_time).total_seconds()

        # 구독 타입들 수집
        subscription_types = set()
        for unified_sub in self._unified_subscriptions.values():
            subscription_types.update(unified_sub.get_subscription_types())

        return {
            "total_tickets": self._metrics.total_tickets,
            "total_symbols": self._metrics.total_symbols,
            "messages_sent": self._metrics.messages_sent,
            "resubscribe_count": self._metrics.resubscribe_count,
            "creation_time": self._metrics.creation_time,
            "last_update_time": self._metrics.last_update_time,
            "uptime_seconds": uptime_seconds,
            "efficiency_score": self._calculate_efficiency_score(),
            "subscription_types": list(subscription_types)
        }

    def _calculate_efficiency_score(self) -> float:
        """효율성 점수 계산 (0-100)"""
        if not self._unified_subscriptions:
            return 100.0

        total_types = sum(len(sub.types) for sub in self._unified_subscriptions.values())
        total_tickets = len(self._unified_subscriptions)

        # 전통적 방식 대비 효율성 (각 타입마다 1티켓 vs 통합 방식)
        traditional_tickets = total_types
        efficiency = ((traditional_tickets - total_tickets) / traditional_tickets) * 100 if traditional_tickets > 0 else 100.0

        return max(0.0, min(100.0, efficiency))

    def _format_symbols_for_log(self, symbols: List[str], max_display: int = 3) -> str:
        """심볼 목록을 로그에 적합하게 포맷팅"""
        if not symbols:
            return "[]"

        total_count = len(symbols)

        # 심볼이 적으면 모두 표시
        if total_count <= max_display * 2:
            return f"[{', '.join(symbols)}]"

        # 심볼이 많으면 처음 3개 + ... + 마지막 1개 + 총 개수
        first_part = symbols[:max_display]
        last_part = symbols[-1:]  # 마지막 1개만

        formatted = f"[{', '.join(first_part)}, ..., {', '.join(last_part)}] (총 {total_count}개)"
        return formatted

    def __repr__(self) -> str:
        """객체 문자열 표현"""
        ticket_count = len(self._unified_subscriptions)
        efficiency = self._calculate_efficiency_score()
        return f"UpbitWebSocketSubscriptionManager(티켓={ticket_count}개, 효율성={efficiency:.1f}%)"
