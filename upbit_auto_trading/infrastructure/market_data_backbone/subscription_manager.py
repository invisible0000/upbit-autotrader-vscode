"""
차트뷰어 구독 관리 시스템

기존 시스템과 격리된 차트뷰어 전용 구독 관리 시스템입니다.
심볼별 타임프레임별 구독을 관리하며, 중복 구독을 방지합니다.

주요 기능:
- 심볼별 타임프레임별 구독 관리
- 자동 구독/구독 해제 (사용량 기반)
- 중복 구독 방지
- 동적 구독 우선순위 조정
- WebSocket 연결 최적화
"""

import time
import threading
from typing import Dict, Set, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict, deque
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger


class SubscriptionStatus(Enum):
    """구독 상태"""
    INACTIVE = "inactive"
    PENDING = "pending"
    ACTIVE = "active"
    ERROR = "error"


class SubscriptionPriority(Enum):
    """구독 우선순위"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class SubscriptionRequest:
    """구독 요청"""
    symbol: str
    timeframe: str
    subscriber_id: str
    priority: SubscriptionPriority = SubscriptionPriority.NORMAL
    auto_unsubscribe: bool = True
    max_idle_time: int = 300  # 5분
    callback: Optional[Callable[[str, str, Any], None]] = None


@dataclass
class SubscriptionEntry:
    """구독 엔트리"""
    request: SubscriptionRequest
    status: SubscriptionStatus = SubscriptionStatus.INACTIVE
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    data_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None

    def update_activity(self) -> None:
        """활동 시간 업데이트"""
        self.last_activity = time.time()
        self.data_count += 1

    def is_idle(self) -> bool:
        """유휴 상태 확인"""
        if not self.request.auto_unsubscribe:
            return False

        idle_time = time.time() - self.last_activity
        return idle_time > self.request.max_idle_time


@dataclass
class SubscriptionStats:
    """구독 통계"""
    total_subscriptions: int = 0
    active_subscriptions: int = 0
    pending_subscriptions: int = 0
    error_subscriptions: int = 0
    total_data_received: int = 0
    auto_unsubscribed: int = 0
    last_cleanup: Optional[datetime] = None


class SubscriptionManager:
    """
    차트뷰어 구독 관리자

    기존 시스템과 격리된 차트뷰어 전용 구독 관리 시스템입니다.
    심볼별 타임프레임별 구독을 효율적으로 관리합니다.
    """

    def __init__(self, cleanup_interval: int = 60, max_subscriptions: int = 100):
        """
        Args:
            cleanup_interval: 정리 작업 간격 (초)
            max_subscriptions: 최대 구독 수
        """
        self.logger = create_component_logger("SubscriptionManager")

        # 설정
        self._cleanup_interval = cleanup_interval
        self._max_subscriptions = max_subscriptions

        # 구독 저장소 (심볼 -> 타임프레임 -> 구독자 ID -> 구독 엔트리)
        self._subscriptions: Dict[str, Dict[str, Dict[str, SubscriptionEntry]]] = defaultdict(
            lambda: defaultdict(dict)
        )

        # 활성 구독 추적 (빠른 조회용)
        self._active_subscriptions: Set[Tuple[str, str]] = set()  # (symbol, timeframe)

        # 구독자별 구독 추적
        self._subscriber_subscriptions: Dict[str, Set[Tuple[str, str]]] = defaultdict(set)

        # 통계
        self._stats = SubscriptionStats()

        # 스레드 안전성
        self._lock = threading.RLock()

        # 백그라운드 정리 작업
        self._cleanup_timer: Optional[threading.Timer] = None
        self._is_running = True

        # 콜백 관리
        self._connection_callback: Optional[Callable[[str, str, bool], None]] = None
        self._data_callback: Optional[Callable[[str, str, Any], None]] = None

        # 활동 히스토리 (최적화용)
        self._activity_history: deque = deque(maxlen=1000)

        self.logger.info(
            f"차트뷰어 구독 관리자 초기화: "
            f"정리 간격 {cleanup_interval}초, 최대 구독 {max_subscriptions}개 "
            f"(기존 시스템과 격리)"
        )

        # 정리 작업 시작
        self._start_cleanup_timer()

    def subscribe(self, request: SubscriptionRequest) -> bool:
        """
        구독 요청 처리

        Args:
            request: 구독 요청

        Returns:
            구독 성공 여부
        """
        try:
            with self._lock:
                symbol = request.symbol
                timeframe = request.timeframe
                subscriber_id = request.subscriber_id

                # 최대 구독 수 확인
                if self._stats.total_subscriptions >= self._max_subscriptions:
                    self.logger.warning(
                        f"최대 구독 수 초과: {self._stats.total_subscriptions} >= {self._max_subscriptions}"
                    )
                    return False

                # 기존 구독 확인
                if subscriber_id in self._subscriptions[symbol][timeframe]:
                    existing = self._subscriptions[symbol][timeframe][subscriber_id]
                    if existing.status == SubscriptionStatus.ACTIVE:
                        self.logger.debug(f"이미 구독 중: {symbol}:{timeframe} by {subscriber_id}")
                        existing.update_activity()
                        return True

                # 새 구독 엔트리 생성
                entry = SubscriptionEntry(
                    request=request,
                    status=SubscriptionStatus.PENDING
                )

                # 구독 저장
                self._subscriptions[symbol][timeframe][subscriber_id] = entry
                self._subscriber_subscriptions[subscriber_id].add((symbol, timeframe))

                # 통계 업데이트
                self._stats.total_subscriptions += 1
                self._stats.pending_subscriptions += 1

                # 신규 심볼-타임프레임 쌍인지 확인
                subscription_key = (symbol, timeframe)
                is_new_subscription = subscription_key not in self._active_subscriptions

                if is_new_subscription:
                    # WebSocket 연결 요청
                    success = self._request_connection(symbol, timeframe)
                    if success:
                        self._active_subscriptions.add(subscription_key)
                        entry.status = SubscriptionStatus.ACTIVE
                        self._stats.pending_subscriptions -= 1
                        self._stats.active_subscriptions += 1

                        self.logger.info(f"새 구독 활성화: {symbol}:{timeframe}")
                    else:
                        entry.status = SubscriptionStatus.ERROR
                        entry.last_error = "WebSocket 연결 실패"
                        self._stats.pending_subscriptions -= 1
                        self._stats.error_subscriptions += 1

                        self.logger.error(f"구독 실패: {symbol}:{timeframe}")
                        return False
                else:
                    # 기존 연결에 합류
                    entry.status = SubscriptionStatus.ACTIVE
                    self._stats.pending_subscriptions -= 1
                    self._stats.active_subscriptions += 1

                    self.logger.debug(f"기존 구독에 합류: {symbol}:{timeframe} by {subscriber_id}")

                # 활동 히스토리 기록
                self._activity_history.append({
                    'action': 'subscribe',
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'subscriber_id': subscriber_id,
                    'timestamp': time.time()
                })

                return True

        except Exception as e:
            self.logger.error(f"구독 처리 실패: {request.symbol}:{request.timeframe} - {e}")
            return False

    def unsubscribe(self, symbol: str, timeframe: str, subscriber_id: str) -> bool:
        """
        구독 해제

        Args:
            symbol: 심볼
            timeframe: 타임프레임
            subscriber_id: 구독자 ID

        Returns:
            해제 성공 여부
        """
        try:
            with self._lock:
                # 구독 확인
                if (symbol not in self._subscriptions or
                    timeframe not in self._subscriptions[symbol] or
                    subscriber_id not in self._subscriptions[symbol][timeframe]):
                    self.logger.warning(f"구독 없음: {symbol}:{timeframe} by {subscriber_id}")
                    return False

                entry = self._subscriptions[symbol][timeframe][subscriber_id]

                # 구독 제거
                del self._subscriptions[symbol][timeframe][subscriber_id]
                self._subscriber_subscriptions[subscriber_id].discard((symbol, timeframe))

                # 통계 업데이트
                if entry.status == SubscriptionStatus.ACTIVE:
                    self._stats.active_subscriptions -= 1
                elif entry.status == SubscriptionStatus.PENDING:
                    self._stats.pending_subscriptions -= 1
                elif entry.status == SubscriptionStatus.ERROR:
                    self._stats.error_subscriptions -= 1

                self._stats.total_subscriptions -= 1

                # 해당 심볼-타임프레임에 다른 구독자가 있는지 확인
                remaining_subscribers = len(self._subscriptions[symbol][timeframe])
                subscription_key = (symbol, timeframe)

                if remaining_subscribers == 0:
                    # 마지막 구독자 제거 - WebSocket 연결 해제
                    self._request_disconnection(symbol, timeframe)
                    self._active_subscriptions.discard(subscription_key)

                    # 빈 딕셔너리 정리
                    if not self._subscriptions[symbol][timeframe]:
                        del self._subscriptions[symbol][timeframe]
                    if not self._subscriptions[symbol]:
                        del self._subscriptions[symbol]

                    self.logger.info(f"구독 완전 해제: {symbol}:{timeframe}")
                else:
                    self.logger.debug(
                        f"구독 일부 해제: {symbol}:{timeframe} by {subscriber_id} "
                        f"(남은 구독자: {remaining_subscribers})"
                    )

                # 활동 히스토리 기록
                self._activity_history.append({
                    'action': 'unsubscribe',
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'subscriber_id': subscriber_id,
                    'timestamp': time.time()
                })

                return True

        except Exception as e:
            self.logger.error(f"구독 해제 실패: {symbol}:{timeframe} by {subscriber_id} - {e}")
            return False

    def unsubscribe_all(self, subscriber_id: str) -> int:
        """
        구독자의 모든 구독 해제

        Args:
            subscriber_id: 구독자 ID

        Returns:
            해제된 구독 수
        """
        try:
            with self._lock:
                if subscriber_id not in self._subscriber_subscriptions:
                    return 0

                # 구독 목록 복사 (반복 중 수정 방지)
                subscriptions_to_remove = list(self._subscriber_subscriptions[subscriber_id])
                unsubscribed_count = 0

                for symbol, timeframe in subscriptions_to_remove:
                    if self.unsubscribe(symbol, timeframe, subscriber_id):
                        unsubscribed_count += 1

                # 구독자 정리
                if subscriber_id in self._subscriber_subscriptions:
                    del self._subscriber_subscriptions[subscriber_id]

                self.logger.info(f"구독자 전체 해제: {subscriber_id} ({unsubscribed_count}개 구독)")
                return unsubscribed_count

        except Exception as e:
            self.logger.error(f"전체 구독 해제 실패: {subscriber_id} - {e}")
            return 0

    def on_data_received(self, symbol: str, timeframe: str, data: Any) -> None:
        """
        데이터 수신 처리

        Args:
            symbol: 심볼
            timeframe: 타임프레임
            data: 수신 데이터
        """
        try:
            with self._lock:
                if symbol not in self._subscriptions or timeframe not in self._subscriptions[symbol]:
                    return

                # 모든 구독자에게 데이터 전달
                subscribers = self._subscriptions[symbol][timeframe]
                delivered_count = 0

                for subscriber_id, entry in subscribers.items():
                    try:
                        # 활동 업데이트
                        entry.update_activity()

                        # 콜백 호출
                        if entry.request.callback:
                            entry.request.callback(symbol, timeframe, data)

                        # 전역 데이터 콜백
                        if self._data_callback:
                            self._data_callback(symbol, timeframe, data)

                        delivered_count += 1

                    except Exception as e:
                        entry.error_count += 1
                        entry.last_error = str(e)
                        self.logger.error(f"데이터 전달 실패: {subscriber_id} - {e}")

                # 통계 업데이트
                self._stats.total_data_received += 1

                self.logger.debug(
                    f"데이터 전달 완료: {symbol}:{timeframe} -> {delivered_count}명"
                )

        except Exception as e:
            self.logger.error(f"데이터 수신 처리 실패: {symbol}:{timeframe} - {e}")

    def _request_connection(self, symbol: str, timeframe: str) -> bool:
        """WebSocket 연결 요청"""
        try:
            if self._connection_callback:
                self._connection_callback(symbol, timeframe, True)
                self.logger.debug(f"WebSocket 연결 요청: {symbol}:{timeframe}")
                return True
            else:
                self.logger.warning("연결 콜백이 설정되지 않음")
                return False

        except Exception as e:
            self.logger.error(f"WebSocket 연결 요청 실패: {symbol}:{timeframe} - {e}")
            return False

    def _request_disconnection(self, symbol: str, timeframe: str) -> bool:
        """WebSocket 연결 해제 요청"""
        try:
            if self._connection_callback:
                self._connection_callback(symbol, timeframe, False)
                self.logger.debug(f"WebSocket 연결 해제 요청: {symbol}:{timeframe}")
                return True
            else:
                self.logger.warning("연결 콜백이 설정되지 않음")
                return False

        except Exception as e:
            self.logger.error(f"WebSocket 연결 해제 요청 실패: {symbol}:{timeframe} - {e}")
            return False

    def _start_cleanup_timer(self) -> None:
        """정리 작업 타이머 시작"""
        if not self._is_running:
            return

        self._cleanup_timer = threading.Timer(self._cleanup_interval, self._cleanup_task)
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()

    def _cleanup_task(self) -> None:
        """백그라운드 정리 작업"""
        try:
            with self._lock:
                if not self._is_running:
                    return

                # 유휴 구독 해제
                idle_subscriptions = []

                for symbol in list(self._subscriptions.keys()):
                    for timeframe in list(self._subscriptions[symbol].keys()):
                        for subscriber_id, entry in list(self._subscriptions[symbol][timeframe].items()):
                            if entry.is_idle():
                                idle_subscriptions.append((symbol, timeframe, subscriber_id))

                # 유휴 구독 해제 실행
                for symbol, timeframe, subscriber_id in idle_subscriptions:
                    if self.unsubscribe(symbol, timeframe, subscriber_id):
                        self._stats.auto_unsubscribed += 1
                        self.logger.info(f"유휴 구독 자동 해제: {symbol}:{timeframe} by {subscriber_id}")

                # 통계 업데이트
                self._stats.last_cleanup = datetime.now()

                if idle_subscriptions:
                    self.logger.info(f"정리 작업 완료: {len(idle_subscriptions)}개 유휴 구독 해제")

        except Exception as e:
            self.logger.error(f"정리 작업 실패: {e}")

        finally:
            # 다음 정리 작업 예약
            self._start_cleanup_timer()

    def set_connection_callback(self, callback: Callable[[str, str, bool], None]) -> None:
        """연결 콜백 설정"""
        self._connection_callback = callback
        self.logger.debug("연결 콜백 설정됨")

    def set_data_callback(self, callback: Callable[[str, str, Any], None]) -> None:
        """데이터 콜백 설정"""
        self._data_callback = callback
        self.logger.debug("데이터 콜백 설정됨")

    def get_subscriptions(self, subscriber_id: Optional[str] = None) -> Dict[str, Any]:
        """구독 목록 조회"""
        try:
            with self._lock:
                if subscriber_id:
                    # 특정 구독자의 구독 목록
                    if subscriber_id not in self._subscriber_subscriptions:
                        return {'subscriber_id': subscriber_id, 'subscriptions': []}

                    subscriptions = []
                    for symbol, timeframe in self._subscriber_subscriptions[subscriber_id]:
                        if (symbol in self._subscriptions and
                            timeframe in self._subscriptions[symbol] and
                            subscriber_id in self._subscriptions[symbol][timeframe]):

                            entry = self._subscriptions[symbol][timeframe][subscriber_id]
                            subscriptions.append({
                                'symbol': symbol,
                                'timeframe': timeframe,
                                'status': entry.status.value,
                                'priority': entry.request.priority.value,
                                'created_at': entry.created_at,
                                'last_activity': entry.last_activity,
                                'data_count': entry.data_count,
                                'error_count': entry.error_count
                            })

                    return {
                        'subscriber_id': subscriber_id,
                        'subscriptions': subscriptions
                    }
                else:
                    # 전체 구독 목록
                    all_subscriptions = []

                    for symbol in self._subscriptions:
                        for timeframe in self._subscriptions[symbol]:
                            for subscriber_id, entry in self._subscriptions[symbol][timeframe].items():
                                all_subscriptions.append({
                                    'symbol': symbol,
                                    'timeframe': timeframe,
                                    'subscriber_id': subscriber_id,
                                    'status': entry.status.value,
                                    'priority': entry.request.priority.value,
                                    'created_at': entry.created_at,
                                    'last_activity': entry.last_activity,
                                    'data_count': entry.data_count,
                                    'error_count': entry.error_count
                                })

                    return {
                        'total_subscriptions': len(all_subscriptions),
                        'subscriptions': all_subscriptions
                    }

        except Exception as e:
            self.logger.error(f"구독 목록 조회 실패: {e}")
            return {'error': str(e)}

    def get_stats(self) -> Dict[str, Any]:
        """구독 통계 조회"""
        try:
            with self._lock:
                return {
                    'total_subscriptions': self._stats.total_subscriptions,
                    'active_subscriptions': self._stats.active_subscriptions,
                    'pending_subscriptions': self._stats.pending_subscriptions,
                    'error_subscriptions': self._stats.error_subscriptions,
                    'total_data_received': self._stats.total_data_received,
                    'auto_unsubscribed': self._stats.auto_unsubscribed,
                    'last_cleanup': self._stats.last_cleanup.isoformat() if self._stats.last_cleanup else None,
                    'active_symbol_timeframes': len(self._active_subscriptions),
                    'total_subscribers': len(self._subscriber_subscriptions),
                    'cleanup_interval': self._cleanup_interval,
                    'max_subscriptions': self._max_subscriptions
                }

        except Exception as e:
            self.logger.error(f"통계 조회 실패: {e}")
            return {'error': str(e)}

    def get_activity_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """활동 히스토리 조회"""
        try:
            with self._lock:
                history = list(self._activity_history)
                return history[-limit:] if len(history) > limit else history

        except Exception as e:
            self.logger.error(f"활동 히스토리 조회 실패: {e}")
            return []

    def shutdown(self) -> None:
        """구독 관리자 종료"""
        try:
            self.logger.info("차트뷰어 구독 관리자 종료 시작")

            # 실행 중지
            self._is_running = False

            # 정리 타이머 중지
            if self._cleanup_timer:
                self._cleanup_timer.cancel()

            with self._lock:
                # 모든 구독 해제
                all_subscribers = list(self._subscriber_subscriptions.keys())
                for subscriber_id in all_subscribers:
                    self.unsubscribe_all(subscriber_id)

                # 데이터 정리
                self._subscriptions.clear()
                self._active_subscriptions.clear()
                self._subscriber_subscriptions.clear()
                self._activity_history.clear()

            self.logger.info("차트뷰어 구독 관리자 종료 완료")

        except Exception as e:
            self.logger.error(f"구독 관리자 종료 실패: {e}")

    def __del__(self):
        """소멸자"""
        if hasattr(self, '_is_running') and self._is_running:
            self.shutdown()
