"""
QAsync LoopGuard - 이벤트 루프 위반 실시간 감지 시스템
목적: 런타임에서 다중 이벤트 루프 사용을 즉시 감지하여 회귀 방지

주요 기능:
- 메인 QAsync 루프 등록 및 추적
- Infrastructure 컴포넌트에서 루프 위반 감지
- 위반 시 즉시 예외 발생으로 개발자에게 알림
- 상세한 위반 정보 로깅 및 디버깅 지원
"""

import asyncio
import logging
import threading
import traceback
from typing import Optional, Dict, List
from datetime import datetime
from dataclasses import dataclass


@dataclass
class LoopViolation:
    """이벤트 루프 위반 정보"""
    timestamp: datetime
    location: str
    expected_loop_id: str
    actual_loop_id: str
    thread_name: str
    stack_trace: List[str]
    component: Optional[str] = None


class LoopGuard:
    """
    QAsync 이벤트 루프 위반 감지 및 보호

    사용법:
        # 메인 루프 등록
        loop_guard = LoopGuard()
        loop_guard.set_main_loop(qasync_loop)

        # Infrastructure 컴포넌트에서 사용
        loop_guard.ensure_main_loop(where="UpbitPublicClient.make_request")
    """

    _instance: Optional['LoopGuard'] = None
    _lock = threading.Lock()

    def __init__(self):
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
        self._main_loop_id: Optional[str] = None
        self._main_thread_name: Optional[str] = None
        self._violations: List[LoopViolation] = []
        self._component_registry: Dict[str, str] = {}
        self._logger = logging.getLogger(__name__)
        self._strict_mode = True  # 기본적으로 엄격 모드

    @classmethod
    def get_instance(cls) -> 'LoopGuard':
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def set_main_loop(self, loop: asyncio.AbstractEventLoop, component: str = "QAsync") -> None:
        """
        메인 QAsync 루프 등록

        Args:
            loop: QAsync 이벤트 루프
            component: 등록하는 컴포넌트 이름
        """
        if self._main_loop is not None:
            self._logger.warning(f"메인 루프가 이미 설정되어 있습니다: {self._main_loop_id}")
            return

        self._main_loop = loop
        self._main_loop_id = f"{type(loop).__name__}@{id(loop)}"
        self._main_thread_name = threading.current_thread().name

        self._logger.info(
            f"LoopGuard 활성화: 메인 루프 {self._main_loop_id} "
            f"(스레드: {self._main_thread_name}, 컴포넌트: {component})"
        )

    def register_component(self, component_name: str, description: str = "") -> None:
        """
        Infrastructure 컴포넌트 등록

        Args:
            component_name: 컴포넌트 이름
            description: 컴포넌트 설명
        """
        self._component_registry[component_name] = description
        self._logger.debug(f"컴포넌트 등록: {component_name}")

    def ensure_main_loop(self, *, where: str, component: str = None) -> None:
        """
        현재 루프가 메인 루프인지 확인

        Args:
            where: 호출 위치 (예: "UpbitPublicClient.make_request")
            component: 컴포넌트 이름 (선택적)

        Raises:
            RuntimeError: 루프 위반 감지 시
        """
        if self._main_loop is None:
            # 메인 루프가 설정되지 않은 경우 - 개발 초기나 테스트 환경
            self._logger.warning(f"LoopGuard: 메인 루프 미설정 상태에서 호출됨 (위치: {where})")
            return

        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            # 실행 중인 루프가 없는 경우
            if self._strict_mode:
                self._record_violation(
                    location=where,
                    expected_loop_id=self._main_loop_id,
                    actual_loop_id="None (no running loop)",
                    component=component
                )
                raise RuntimeError(
                    f"❌ LoopGuard: 실행 중인 이벤트 루프가 없습니다! "
                    f"위치: {where}, 예상 루프: {self._main_loop_id}"
                )
            else:
                self._logger.warning(f"LoopGuard: 실행 중인 루프 없음 (위치: {where})")
                return

        current_loop_id = f"{type(current_loop).__name__}@{id(current_loop)}"

        if current_loop is not self._main_loop:
            # 루프 위반 감지!
            self._record_violation(
                location=where,
                expected_loop_id=self._main_loop_id,
                actual_loop_id=current_loop_id,
                component=component
            )

            if self._strict_mode:
                raise RuntimeError(
                    f"❌ LoopGuard: 이벤트 루프 위반 감지! "
                    f"위치: {where}, "
                    f"예상: {self._main_loop_id}, "
                    f"실제: {current_loop_id} "
                    f"(다중 이벤트 루프 충돌)"
                )
            else:
                self._logger.error(
                    f"LoopGuard: 루프 위반 감지되었지만 엄격 모드가 비활성화됨 "
                    f"(위치: {where})"
                )

    def _record_violation(
        self,
        location: str,
        expected_loop_id: str,
        actual_loop_id: str,
        component: Optional[str] = None
    ) -> None:
        """위반 사항 기록"""
        violation = LoopViolation(
            timestamp=datetime.now(),
            location=location,
            expected_loop_id=expected_loop_id,
            actual_loop_id=actual_loop_id,
            thread_name=threading.current_thread().name,
            stack_trace=traceback.format_stack(),
            component=component
        )

        self._violations.append(violation)

        # 상세 로깅
        self._logger.error(f"🚨 이벤트 루프 위반 기록: {location}")
        self._logger.error(f"   예상 루프: {expected_loop_id}")
        self._logger.error(f"   실제 루프: {actual_loop_id}")
        self._logger.error(f"   스레드: {violation.thread_name}")
        if component:
            self._logger.error(f"   컴포넌트: {component}")

    def get_violations(self) -> List[LoopViolation]:
        """기록된 위반 사항 반환"""
        return self._violations.copy()

    def clear_violations(self) -> None:
        """위반 기록 초기화"""
        violation_count = len(self._violations)
        self._violations.clear()
        self._logger.info(f"LoopGuard: {violation_count}개 위반 기록 초기화됨")

    def set_strict_mode(self, strict: bool) -> None:
        """
        엄격 모드 설정

        Args:
            strict: True시 위반 감지 시 즉시 예외 발생, False시 경고만
        """
        self._strict_mode = strict
        mode_str = "엄격 모드" if strict else "관대 모드"
        self._logger.info(f"LoopGuard: {mode_str}로 설정됨")

    def is_main_loop_set(self) -> bool:
        """메인 루프 설정 여부 확인"""
        return self._main_loop is not None

    def get_main_loop_info(self) -> Optional[Dict[str, str]]:
        """메인 루프 정보 반환"""
        if self._main_loop is None:
            return None

        return {
            "loop_id": self._main_loop_id,
            "loop_type": type(self._main_loop).__name__,
            "thread_name": self._main_thread_name,
            "is_running": str(self._main_loop.is_running()),
            "is_closed": str(self._main_loop.is_closed())
        }

    def get_status_report(self) -> Dict:
        """전체 상태 보고서 생성"""
        return {
            "main_loop_info": self.get_main_loop_info(),
            "strict_mode": self._strict_mode,
            "registered_components": list(self._component_registry.keys()),
            "violation_count": len(self._violations),
            "recent_violations": [
                {
                    "timestamp": v.timestamp.isoformat(),
                    "location": v.location,
                    "component": v.component
                }
                for v in self._violations[-5:]  # 최근 5개만
            ]
        }


# 전역 인스턴스 (편의성을 위해)
_global_loop_guard = None


def get_loop_guard() -> LoopGuard:
    """전역 LoopGuard 인스턴스 반환"""
    global _global_loop_guard
    if _global_loop_guard is None:
        _global_loop_guard = LoopGuard.get_instance()
    return _global_loop_guard


def ensure_main_loop(*, where: str, component: str = None) -> None:
    """
    편의 함수: 현재 루프가 메인 루프인지 확인

    사용 예시:
        from upbit_auto_trading.infrastructure.runtime.loop_guard import ensure_main_loop

        async def make_request(self):
            ensure_main_loop(where="UpbitPublicClient.make_request", component="UpbitAPI")
            # ... 나머지 로직
    """
    get_loop_guard().ensure_main_loop(where=where, component=component)


def register_component(component_name: str, description: str = "") -> None:
    """편의 함수: 컴포넌트 등록"""
    get_loop_guard().register_component(component_name, description)


def set_main_loop(loop: asyncio.AbstractEventLoop, component: str = "QAsync") -> None:
    """편의 함수: 메인 루프 설정"""
    get_loop_guard().set_main_loop(loop, component)


# Infrastructure 컴포넌트에서 사용할 데코레이터
def loop_protected(component: str = None):
    """
    LoopGuard 보호 데코레이터

    비동기 메서드에 적용하면 자동으로 루프 검증을 수행

    사용 예시:
        @loop_protected(component="UpbitAPI")
        async def make_request(self):
            # 자동으로 루프 검증 수행
            pass
    """
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                # 메서드 이름과 클래스명으로 위치 식별
                method_name = func.__name__
                if args and hasattr(args[0], '__class__'):
                    class_name = args[0].__class__.__name__
                    location = f"{class_name}.{method_name}"
                else:
                    location = method_name

                ensure_main_loop(where=location, component=component)
                return await func(*args, **kwargs)
            return async_wrapper
        else:
            # 동기 함수인 경우 경고만
            logging.getLogger(__name__).warning(
                f"@loop_protected가 비동기 함수가 아닌 {func.__name__}에 적용됨"
            )
            return func
    return decorator


if __name__ == "__main__":
    # 간단한 테스트/데모
    print("🔧 LoopGuard 테스트")

    guard = LoopGuard()

    # 상태 확인
    print(f"메인 루프 설정됨: {guard.is_main_loop_set()}")

    # 가상 루프로 테스트
    import asyncio

    async def test():
        loop = asyncio.get_running_loop()
        guard.set_main_loop(loop, "TestLoop")

        print("✅ 메인 루프 설정 완료")
        print(f"루프 정보: {guard.get_main_loop_info()}")

        # 정상 케이스
        try:
            guard.ensure_main_loop(where="test_function")
            print("✅ 루프 검증 통과")
        except RuntimeError as e:
            print(f"❌ 루프 검증 실패: {e}")

        # 상태 보고서
        print(f"상태 보고서: {guard.get_status_report()}")

    # 테스트 실행
    try:
        asyncio.run(test())
    except Exception as e:
        print(f"테스트 실행 오류: {e}")
