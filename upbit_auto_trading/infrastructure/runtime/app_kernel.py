"""
AppKernel - QAsync 통합 런타임 커널
목적: 단일 조립점으로 모든 런타임 리소스의 생명주기를 중앙 관리

주요 책임:
- QAsync 이벤트 루프와 LoopGuard 초기화
- TaskManager를 통한 태스크 생명주기 관리
- EventBus 및 HTTP 클라이언트 통합 관리
- 안전한 shutdown 시퀀스 제공
- Infrastructure 컴포넌트들의 의존성 주입
"""

import asyncio
import logging
import sys
from typing import Optional, Dict, Any, Set
from datetime import datetime
from dataclasses import dataclass, field

try:
    import qasync
    from PyQt6.QtWidgets import QApplication
    QASYNC_AVAILABLE = True
except ImportError:
    QASYNC_AVAILABLE = False

from .loop_guard import LoopGuard, get_loop_guard


@dataclass
class KernelConfig:
    """AppKernel 설정"""
    strict_loop_guard: bool = True
    enable_task_manager: bool = True
    enable_event_bus: bool = True
    enable_http_clients: bool = True
    shutdown_timeout: float = 30.0
    log_level: str = "INFO"
    component_registry: Dict[str, Any] = field(default_factory=dict)


class TaskManager:
    """태스크 생명주기 관리자"""

    def __init__(self, logger: logging.Logger):
        self._tasks: Set[asyncio.Task] = set()
        self._named_tasks: Dict[str, asyncio.Task] = {}
        self._logger = logger
        self._shutdown_requested = False

    def create_task(self, coro, *, name: str = None, component: str = None) -> asyncio.Task:
        """
        태스크 생성 및 등록

        Args:
            coro: 코루틴
            name: 태스크 이름
            component: 소속 컴포넌트

        Returns:
            생성된 Task 객체
        """
        if self._shutdown_requested:
            raise RuntimeError("TaskManager가 종료 중입니다. 새 태스크를 생성할 수 없습니다.")

        task = asyncio.create_task(coro)
        self._tasks.add(task)

        # 태스크 이름 설정
        task_name = name or f"task-{id(task)}"
        if component:
            task_name = f"{component}:{task_name}"

        if hasattr(task, 'set_name'):
            task.set_name(task_name)

        # 이름이 있는 태스크는 별도 관리
        if name:
            if name in self._named_tasks and not self._named_tasks[name].done():
                self._logger.warning(f"태스크 이름 중복: {name} (기존 태스크 취소)")
                self._named_tasks[name].cancel()
            self._named_tasks[name] = task

        # 완료 콜백 설정
        def cleanup_callback(finished_task):
            self._tasks.discard(finished_task)
            if name and name in self._named_tasks:
                self._named_tasks.pop(name, None)

            if finished_task.cancelled():
                self._logger.debug(f"태스크 취소됨: {task_name}")
            elif finished_task.exception():
                exc = finished_task.exception()
                self._logger.error(f"태스크 실패: {task_name}, 오류: {exc}")
            else:
                self._logger.debug(f"태스크 완료: {task_name}")

        task.add_done_callback(cleanup_callback)

        self._logger.debug(f"태스크 생성: {task_name} (총 {len(self._tasks)}개)")
        return task

    def get_task(self, name: str) -> Optional[asyncio.Task]:
        """이름으로 태스크 조회"""
        return self._named_tasks.get(name)

    def cancel_task(self, name: str) -> bool:
        """이름으로 태스크 취소"""
        task = self._named_tasks.get(name)
        if task and not task.done():
            task.cancel()
            self._logger.info(f"태스크 취소: {name}")
            return True
        return False

    async def shutdown(self, timeout: float = 30.0) -> None:
        """모든 태스크 정리"""
        self._shutdown_requested = True

        if not self._tasks:
            self._logger.info("정리할 태스크가 없습니다.")
            return

        task_count = len(self._tasks)
        self._logger.info(f"TaskManager 종료: {task_count}개 태스크 정리 시작")

        # 모든 태스크 취소
        for task in self._tasks.copy():
            if not task.done():
                task.cancel()

        # 취소 완료 대기
        try:
            await asyncio.wait_for(
                asyncio.gather(*self._tasks, return_exceptions=True),
                timeout=timeout
            )
            self._logger.info(f"TaskManager 정리 완료: {task_count}개 태스크")
        except asyncio.TimeoutError:
            self._logger.warning(f"TaskManager 정리 타임아웃: {timeout}초")

        # 강제 정리
        self._tasks.clear()
        self._named_tasks.clear()

    def get_status(self) -> Dict[str, Any]:
        """현재 상태 반환"""
        return {
            "total_tasks": len(self._tasks),
            "named_tasks": list(self._named_tasks.keys()),
            "shutdown_requested": self._shutdown_requested
        }


class AppKernel:
    """
    QAsync 통합 런타임 커널

    모든 런타임 리소스의 생명주기를 중앙에서 관리하며,
    QAsync 환경에서 안전한 초기화와 종료를 보장합니다.
    """

    _instance: Optional['AppKernel'] = None

    def __init__(self, config: Optional[KernelConfig] = None):
        if AppKernel._instance is not None:
            raise RuntimeError("AppKernel은 싱글톤입니다. bootstrap()을 사용하세요.")

        self.config = config or KernelConfig()
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(getattr(logging, self.config.log_level.upper()))

        # 핵심 컴포넌트들
        self.loop_guard: Optional[LoopGuard] = None
        self.task_manager: Optional[TaskManager] = None
        self.event_bus: Optional[Any] = None
        self.http_clients: Dict[str, Any] = {}

        # 상태 관리
        self._initialized = False
        self._shutting_down = False
        self._start_time = datetime.now()

        # QApplication 참조 (QAsync 환경)
        self._qapp: Optional[QApplication] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    @classmethod
    def bootstrap(cls, qapp: QApplication, config: Optional[KernelConfig] = None) -> 'AppKernel':
        """
        AppKernel 초기화 및 싱글톤 인스턴스 생성

        Args:
            qapp: QAsync QApplication 인스턴스
            config: 커널 설정

        Returns:
            초기화된 AppKernel 인스턴스
        """
        if cls._instance is not None:
            raise RuntimeError("AppKernel이 이미 초기화되었습니다.")

        if not QASYNC_AVAILABLE:
            raise RuntimeError("QAsync가 설치되지 않았습니다. pip install qasync")

        cls._instance = cls(config)
        cls._instance._initialize(qapp)
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'AppKernel':
        """현재 AppKernel 인스턴스 반환"""
        if cls._instance is None:
            raise RuntimeError("AppKernel이 초기화되지 않았습니다. bootstrap()을 먼저 호출하세요.")
        return cls._instance

    def _initialize(self, qapp: QApplication) -> None:
        """내부 초기화 메서드"""
        if self._initialized:
            return

        self._logger.info("🚀 AppKernel 초기화 시작...")

        # QApplication 및 이벤트 루프 설정
        self._qapp = qapp

        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            # QAsync 루프가 아직 시작되지 않은 경우
            self._loop = asyncio.get_event_loop()

        # LoopGuard 초기화
        if self.config.enable_task_manager:
            self.loop_guard = get_loop_guard()
            self.loop_guard.set_main_loop(self._loop, "AppKernel")
            self.loop_guard.set_strict_mode(self.config.strict_loop_guard)
            self.loop_guard.register_component("AppKernel", "QAsync 런타임 커널")

        # TaskManager 초기화
        if self.config.enable_task_manager:
            self.task_manager = TaskManager(self._logger)
            self._logger.info("✅ TaskManager 초기화 완료")

        # EventBus 초기화 (나중에 구현)
        if self.config.enable_event_bus:
            self._logger.info("⚠️ EventBus 초기화 예정 (Step 2에서 구현)")

        # HTTP 클라이언트 레지스트리 초기화
        if self.config.enable_http_clients:
            self._logger.info("✅ HTTP 클라이언트 레지스트리 초기화 완료")

        self._initialized = True
        self._logger.info("🎉 AppKernel 초기화 완료")

    def create_task(self, coro, *, name: str = None, component: str = None) -> asyncio.Task:
        """TaskManager를 통한 태스크 생성"""
        if not self.task_manager:
            raise RuntimeError("TaskManager가 초기화되지 않았습니다.")

        # LoopGuard 검증
        if self.loop_guard:
            self.loop_guard.ensure_main_loop(where="AppKernel.create_task")

        return self.task_manager.create_task(coro, name=name, component=component)

    def register_http_client(self, name: str, client: Any) -> None:
        """HTTP 클라이언트 등록"""
        if name in self.http_clients:
            self._logger.warning(f"HTTP 클라이언트 중복 등록: {name}")

        self.http_clients[name] = client
        self._logger.debug(f"HTTP 클라이언트 등록: {name}")

    def get_http_client(self, name: str) -> Optional[Any]:
        """등록된 HTTP 클라이언트 조회"""
        return self.http_clients.get(name)

    async def run(self) -> None:
        """
        메인 애플리케이션 실행

        QAsync 환경에서 애플리케이션을 시작하고
        종료까지 대기합니다.
        """
        if not self._initialized:
            raise RuntimeError("AppKernel이 초기화되지 않았습니다.")

        self._logger.info("🎬 AppKernel 메인 실행 시작")

        try:
            # 메인 UI 창 생성 및 표시 (추후 구현)
            self._logger.info("📱 메인 UI 초기화 예정...")

            # QApplication 실행 (QAsync 방식)
            # 실제로는 QApplication.exec()가 아니라 이벤트 루프에서 대기
            self._logger.info("⏳ 애플리케이션 실행 중... (Ctrl+C로 종료)")

            # 종료 신호 대기 - 실제 구현에서는 UI 이벤트나 시그널 처리
            import signal

            def signal_handler(signum, frame):
                self._logger.info(f"종료 신호 수신: {signum}")
                if self._loop and not self._shutting_down:
                    self._loop.create_task(self.shutdown())

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # 무한 대기 (실제로는 UI 이벤트 처리)
            while not self._shutting_down:
                await asyncio.sleep(1)

        except Exception as e:
            self._logger.error(f"AppKernel 실행 중 오류: {e}")
            raise
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """
        안전한 종료 시퀀스

        모든 리소스를 정리하고 애플리케이션을 종료합니다.
        """
        if self._shutting_down:
            return

        self._shutting_down = True
        self._logger.info("🛑 AppKernel 종료 시퀀스 시작...")

        try:
            # 1. 새 작업 수락 중지 (TaskManager에서 처리됨)

            # 2. 태스크 취소 및 정리
            if self.task_manager:
                await self.task_manager.shutdown(self.config.shutdown_timeout)

            # 3. HTTP 클라이언트 정리
            for name, client in self.http_clients.items():
                try:
                    if hasattr(client, 'close'):
                        if asyncio.iscoroutinefunction(client.close):
                            await client.close()
                        else:
                            client.close()
                    self._logger.debug(f"HTTP 클라이언트 정리: {name}")
                except Exception as e:
                    self._logger.error(f"HTTP 클라이언트 {name} 정리 실패: {e}")

            # 4. EventBus 정리 (나중에 구현)
            if self.event_bus:
                self._logger.info("EventBus 정리 예정...")

            # 5. LoopGuard 정리
            if self.loop_guard:
                violations = self.loop_guard.get_violations()
                if violations:
                    self._logger.warning(f"종료 시 {len(violations)}개 루프 위반 기록 발견")
                self.loop_guard.clear_violations()

            # 6. QApplication 종료 준비
            if self._qapp:
                self._qapp.quit()

            uptime = datetime.now() - self._start_time
            self._logger.info(f"✅ AppKernel 종료 완료 (실행 시간: {uptime})")

        except Exception as e:
            self._logger.error(f"종료 시퀀스 오류: {e}")
        finally:
            # 싱글톤 인스턴스 정리
            AppKernel._instance = None

    def get_status(self) -> Dict[str, Any]:
        """커널 상태 정보 반환"""
        uptime = datetime.now() - self._start_time

        status = {
            "initialized": self._initialized,
            "shutting_down": self._shutting_down,
            "uptime": str(uptime),
            "start_time": self._start_time.isoformat(),
            "config": {
                "strict_loop_guard": self.config.strict_loop_guard,
                "enable_task_manager": self.config.enable_task_manager,
                "enable_event_bus": self.config.enable_event_bus,
                "enable_http_clients": self.config.enable_http_clients,
            }
        }

        # 컴포넌트 상태
        if self.task_manager:
            status["task_manager"] = self.task_manager.get_status()

        if self.loop_guard:
            status["loop_guard"] = self.loop_guard.get_status_report()

        status["http_clients"] = list(self.http_clients.keys())

        return status


# 전역 편의 함수들
def get_kernel() -> AppKernel:
    """현재 AppKernel 인스턴스 반환"""
    return AppKernel.get_instance()


def create_task(coro, *, name: str = None, component: str = None) -> asyncio.Task:
    """AppKernel을 통한 태스크 생성"""
    return get_kernel().create_task(coro, name=name, component=component)


if __name__ == "__main__":
    # AppKernel 테스트 시나리오
    print("🧪 AppKernel 테스트")

    async def test_kernel():
        # 가상 QApplication (테스트용)
        if QASYNC_AVAILABLE:
            app = qasync.QApplication(sys.argv)
            loop = qasync.QEventLoop(app)
            asyncio.set_event_loop(loop)

            # AppKernel 부트스트랩
            kernel = AppKernel.bootstrap(app)

            # 테스트 태스크 생성
            async def test_task():
                await asyncio.sleep(1)
                return "테스트 완료"

            task = kernel.create_task(test_task(), name="test_task", component="TestApp")
            result = await task

            print(f"✅ 테스트 태스크 결과: {result}")
            print(f"📊 커널 상태: {kernel.get_status()}")

            # 종료
            await kernel.shutdown()

        else:
            print("❌ QAsync를 사용할 수 없습니다.")

    try:
        if QASYNC_AVAILABLE:
            # QAsync 환경에서 테스트 실행
            app = qasync.QApplication(sys.argv)
            loop = qasync.QEventLoop(app)
            with loop:
                loop.run_until_complete(test_kernel())
        else:
            # 일반 asyncio로 기본 테스트
            asyncio.run(test_kernel())
    except Exception as e:
        print(f"테스트 실행 오류: {e}")
