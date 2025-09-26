"""
QAsync 통합 테스트 환경 설정
목적: 모든 pytest 실행 시 qasync 이벤트 루프 환경 강제하여 회귀 방지
"""

import asyncio
import sys
from typing import Generator
import pytest
import logging

# qasync가 설치되어 있는지 확인
try:
    import qasync
    from PyQt6.QtWidgets import QApplication
    QASYNC_AVAILABLE = True
except ImportError:
    QASYNC_AVAILABLE = False
    print("⚠️ qasync 또는 PyQt6가 설치되지 않았습니다.")

# 로깅 설정
logging.basicConfig(level=logging.WARNING)


@pytest.fixture(scope="session")
def qasync_app() -> Generator[QApplication, None, None]:
    """
    세션 범위의 QApplication 인스턴스 제공
    모든 테스트가 동일한 QApplication을 공유하도록 함
    """
    if not QASYNC_AVAILABLE:
        pytest.skip("qasync 또는 PyQt6가 설치되지 않음")

    # 기존 QApplication 인스턴스가 있는지 확인
    app = QApplication.instance()

    if app is None:
        print("🔧 QAsync 테스트 환경 초기화 중...")
        # QApplication 생성 (테스트용 argv)
        app = qasync.QApplication(sys.argv if hasattr(sys, 'argv') else ['pytest'])
        app.setQuitOnLastWindowClosed(False)  # 테스트 중 자동 종료 방지
        created_app = True
    else:
        print("🔄 기존 QApplication 인스턴스 재사용...")
        created_app = False

    try:
        yield app
    finally:
        if created_app:
            print("🧹 QApplication 정리 중...")
            # 이벤트 루프가 실행 중이면 종료 대기
            if hasattr(app, '_event_loop') and app._event_loop.is_running():
                app._event_loop.stop()
            app.quit()


@pytest.fixture(scope="session")
def qasync_loop(qasync_app: QApplication) -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    세션 범위의 QAsync 이벤트 루프 제공
    모든 테스트가 동일한 이벤트 루프를 공유하도록 함
    """
    if not QASYNC_AVAILABLE:
        pytest.skip("qasync가 설치되지 않음")

    print("🔄 QAsync 이벤트 루프 설정 중...")

    # QEventLoop 생성 및 설정
    loop = qasync.QEventLoop(qasync_app)

    # 현재 실행 중인 루프가 있는지 확인
    try:
        asyncio.get_running_loop()
        print("⚠️ 이미 실행 중인 이벤트 루프 감지됨")
    except RuntimeError:
        # 실행 중인 루프가 없음 - 정상 상황
        pass

    # QAsync 루프를 기본 루프로 설정
    asyncio.set_event_loop(loop)

    # 루프 상태 검증
    assert asyncio.get_event_loop() is loop, "QAsync 루프가 올바르게 설정되지 않았습니다"

    try:
        print("✅ QAsync 이벤트 루프 준비 완료")
        yield loop
    finally:
        print("🧹 QAsync 이벤트 루프 정리 중...")

        # 실행 중인 태스크들 정리
        pending_tasks = asyncio.all_tasks(loop)
        if pending_tasks:
            print(f"⚠️ {len(pending_tasks)}개의 미완료 태스크 정리 중...")
            for task in pending_tasks:
                if not task.done():
                    task.cancel()

        # 루프 종료 (강제 종료하지 않고 자연스럽게 정리)
        if loop.is_running():
            loop.call_soon(loop.stop)


@pytest.fixture(autouse=True)
def ensure_qasync_environment(qasync_loop: asyncio.AbstractEventLoop):
    """
    모든 테스트에서 자동으로 실행되는 QAsync 환경 검증
    잘못된 이벤트 루프 사용 시 즉시 실패
    """
    if not QASYNC_AVAILABLE:
        return  # qasync가 없으면 스킵

    # 현재 이벤트 루프가 qasync 루프인지 확인
    try:
        current_loop = asyncio.get_event_loop()
        if current_loop is not qasync_loop:
            pytest.fail(
                f"❌ 잘못된 이벤트 루프 감지! "
                f"현재: {type(current_loop).__name__}, "
                f"예상: {type(qasync_loop).__name__} "
                f"(QAsync 환경이 아닙니다)"
            )
    except RuntimeError as e:
        pytest.fail(f"❌ 이벤트 루프 접근 실패: {e}")


@pytest.fixture
def async_test_client():
    """
    비동기 테스트를 위한 HTTP 클라이언트 팩토리
    QAsync 환경에서 안전하게 사용할 수 있는 aiohttp 클라이언트 제공
    """
    if not QASYNC_AVAILABLE:
        pytest.skip("qasync가 설치되지 않음")

    clients = []

    async def create_client(*args, **kwargs):
        """aiohttp.ClientSession을 QAsync 환경에서 안전하게 생성"""
        import aiohttp

        # 현재 루프 확인
        loop = asyncio.get_running_loop()

        # 클라이언트 세션 생성
        client = aiohttp.ClientSession(*args, loop=loop, **kwargs)
        clients.append(client)
        return client

    yield create_client

    # 정리: 모든 클라이언트 세션 종료
    async def cleanup():
        for client in clients:
            if not client.closed:
                await client.close()

    # QAsync 환경에서 정리 실행
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # 루프가 실행 중이면 태스크로 정리
        loop.create_task(cleanup())
    else:
        # 루프가 실행 중이 아니면 직접 실행
        loop.run_until_complete(cleanup())


# 마커 정의
def pytest_configure(config):
    """테스트 설정: 사용자 정의 마커 등록"""
    config.addinivalue_line("markers", "qasync: QAsync 환경이 필요한 테스트")
    config.addinivalue_line("markers", "no_qasync: QAsync 환경을 사용하지 않는 테스트")


def pytest_runtest_setup(item):
    """각 테스트 실행 전 검증"""
    # no_qasync 마커가 있는 테스트는 QAsync 환경 검증 스킵
    if item.get_closest_marker("no_qasync"):
        return

    # QAsync 환경이 필요한 테스트인지 확인
    if item.get_closest_marker("qasync") or item.get_closest_marker("asyncio"):
        if not QASYNC_AVAILABLE:
            pytest.skip("QAsync 환경이 필요하지만 qasync가 설치되지 않음")


@pytest.fixture
def loop_guard():
    """
    테스트 중 이벤트 루프 위반을 감지하는 가드
    향후 LoopGuard 클래스가 구현되면 이 픽스쳐를 통해 통합
    """
    if not QASYNC_AVAILABLE:
        pytest.skip("qasync가 설치되지 않음")

    class TestLoopGuard:
        def __init__(self):
            self.main_loop = asyncio.get_event_loop()

        def ensure_main(self, where: str = "test"):
            """현재 루프가 메인 루프인지 확인"""
            try:
                current_loop = asyncio.get_running_loop()
                if current_loop is not self.main_loop:
                    pytest.fail(f"❌ 이벤트 루프 위반 감지! 위치: {where}")
            except RuntimeError:
                pytest.fail(f"❌ 실행 중인 이벤트 루프 없음! 위치: {where}")

    return TestLoopGuard()


# pytest-asyncio 플러그인과의 호환성 설정
pytest_plugins = ["pytest_asyncio"]


# asyncio 모드 설정 (pytest-asyncio 0.21.0+)
@pytest.fixture(scope="session")
def event_loop_policy():
    """
    pytest-asyncio와의 호환성을 위한 이벤트 루프 정책
    QAsync 환경에서는 기본 정책을 그대로 사용
    """
    return asyncio.get_event_loop_policy()


# 테스트 실행 시 출력할 정보
def pytest_sessionstart(session):
    """테스트 세션 시작 시 환경 정보 출력"""
    print("\n" + "=" * 60)
    print("🧪 QAsync 통합 테스트 환경")
    print("=" * 60)
    print(f"✅ QAsync 사용 가능: {QASYNC_AVAILABLE}")
    if QASYNC_AVAILABLE:
        print(f"✅ PyQt6 버전: {qasync.__version__ if hasattr(qasync, '__version__') else 'Unknown'}")
        print("📋 모든 테스트는 QAsync 이벤트 루프 환경에서 실행됩니다")
        print("📋 이벤트 루프 충돌 시 테스트가 자동으로 실패합니다")
    else:
        print("⚠️ qasync 없이 테스트 실행 - 일부 테스트가 스킵됩니다")
    print("=" * 60 + "\n")


def pytest_sessionfinish(session, exitstatus):
    """테스트 세션 종료 시 정리"""
    print("\n" + "=" * 60)
    print("🧪 QAsync 테스트 세션 완료")
    print(f"📊 종료 상태: {exitstatus}")
    print("=" * 60 + "\n")
