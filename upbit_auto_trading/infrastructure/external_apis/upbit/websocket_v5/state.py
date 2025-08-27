"""
업비트 WebSocket v5.0 - State Machine 및 예외 시스템

🎯 특징:
- 명시적인 상태 관리
- 안전한 상태 전이
- 구체적인 예외 타입
- 자동 복구 메커니즘
"""

from enum import Enum, auto
from typing import Set, Optional, Dict, Any
from datetime import datetime


class WebSocketState(Enum):
    """WebSocket 연결 상태"""
    DISCONNECTED = auto()      # 연결 해제됨
    CONNECTING = auto()        # 연결 중
    CONNECTED = auto()         # 연결됨
    SUBSCRIBING = auto()       # 구독 중
    ACTIVE = auto()           # 활성 상태 (구독 완료)
    RECONNECTING = auto()      # 재연결 중
    DISCONNECTING = auto()     # 연결 해제 중
    ERROR = auto()            # 오류 상태


class StateTransitionError(Exception):
    """잘못된 상태 전이 예외"""
    def __init__(self, current_state: WebSocketState, target_state: WebSocketState):
        self.current_state = current_state
        self.target_state = target_state
        super().__init__(f"잘못된 상태 전이: {current_state} -> {target_state}")


class WebSocketStateMachine:
    """WebSocket 상태 머신"""

    # 허용된 상태 전이 규칙
    ALLOWED_TRANSITIONS: Dict[WebSocketState, Set[WebSocketState]] = {
        WebSocketState.DISCONNECTED: {
            WebSocketState.CONNECTING
        },
        WebSocketState.CONNECTING: {
            WebSocketState.CONNECTED,
            WebSocketState.ERROR,
            WebSocketState.DISCONNECTED
        },
        WebSocketState.CONNECTED: {
            WebSocketState.SUBSCRIBING,
            WebSocketState.DISCONNECTING,
            WebSocketState.ERROR,
            WebSocketState.ACTIVE  # 구독 없이 바로 활성화
        },
        WebSocketState.SUBSCRIBING: {
            WebSocketState.ACTIVE,
            WebSocketState.ERROR,
            WebSocketState.DISCONNECTING
        },
        WebSocketState.ACTIVE: {
            WebSocketState.SUBSCRIBING,  # 추가 구독
            WebSocketState.DISCONNECTING,
            WebSocketState.RECONNECTING,
            WebSocketState.ERROR
        },
        WebSocketState.RECONNECTING: {
            WebSocketState.CONNECTING,
            WebSocketState.DISCONNECTED,
            WebSocketState.ERROR
        },
        WebSocketState.DISCONNECTING: {
            WebSocketState.DISCONNECTED
        },
        WebSocketState.ERROR: {
            WebSocketState.RECONNECTING,
            WebSocketState.DISCONNECTING,
            WebSocketState.DISCONNECTED
        }
    }

    def __init__(self, initial_state: WebSocketState = WebSocketState.DISCONNECTED):
        """상태 머신 초기화"""
        self._current_state = initial_state
        self._previous_state: Optional[WebSocketState] = None
        self._state_history: list[tuple[WebSocketState, datetime]] = []
        self._transition_callbacks: Dict[WebSocketState, list] = {}

        # 초기 상태 기록
        self._record_state_change(initial_state)

    @property
    def current_state(self) -> WebSocketState:
        """현재 상태 반환"""
        return self._current_state

    @property
    def previous_state(self) -> Optional[WebSocketState]:
        """이전 상태 반환"""
        return self._previous_state

    def can_transition_to(self, target_state: WebSocketState) -> bool:
        """특정 상태로 전이 가능한지 확인"""
        allowed_states = self.ALLOWED_TRANSITIONS.get(self._current_state, set())
        return target_state in allowed_states

    def transition_to(self, target_state: WebSocketState, force: bool = False) -> bool:
        """상태 전이 실행"""
        if not force and not self.can_transition_to(target_state):
            raise StateTransitionError(self._current_state, target_state)

        # 상태 변경
        self._previous_state = self._current_state
        self._current_state = target_state

        # 변경 기록
        self._record_state_change(target_state)

        # 콜백 실행
        self._execute_callbacks(target_state)

        return True

    def _record_state_change(self, state: WebSocketState) -> None:
        """상태 변경 기록"""
        self._state_history.append((state, datetime.now()))

        # 히스토리 크기 제한 (메모리 관리)
        if len(self._state_history) > 100:
            self._state_history = self._state_history[-50:]

    def add_transition_callback(self, state: WebSocketState, callback) -> None:
        """상태 전이 콜백 등록"""
        if state not in self._transition_callbacks:
            self._transition_callbacks[state] = []
        self._transition_callbacks[state].append(callback)

    def _execute_callbacks(self, state: WebSocketState) -> None:
        """상태 전이 콜백 실행"""
        callbacks = self._transition_callbacks.get(state, [])
        for callback in callbacks:
            try:
                callback(self._previous_state, state)
            except Exception as e:
                # 콜백 에러는 상태 전이를 방해하지 않음
                print(f"State transition callback error: {e}")

    def get_state_history(self, limit: int = 10) -> list[tuple[WebSocketState, datetime]]:
        """상태 히스토리 반환"""
        return self._state_history[-limit:]

    def is_connected(self) -> bool:
        """연결 상태 여부"""
        return self._current_state in {
            WebSocketState.CONNECTED,
            WebSocketState.SUBSCRIBING,
            WebSocketState.ACTIVE
        }

    def is_active(self) -> bool:
        """활성 상태 여부"""
        return self._current_state == WebSocketState.ACTIVE

    def is_error(self) -> bool:
        """오류 상태 여부"""
        return self._current_state == WebSocketState.ERROR

    def is_reconnecting(self) -> bool:
        """재연결 중 여부"""
        return self._current_state == WebSocketState.RECONNECTING

    def reset(self) -> None:
        """상태 초기화"""
        self.transition_to(WebSocketState.DISCONNECTED, force=True)
