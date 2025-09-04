"""
WebSocket v6 테스트용 하이브리드 픽스처 (Session + Function Scope 전략)
==================================================================

pytest-asyncio 권장사항에 따른 개선된 접근:
- Session scope: WebSocket Manager (공유 리소스)
- Function scope: 개별 테스트 격리
- 구조화된 background task 관리
- 명시적 timeout 기반 cleanup
"""

import pytest
import pytest_asyncio
import asyncio
import time
import os
from typing import List, Dict, Any, Optional, Set

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket.core.websocket_manager import (
    get_websocket_manager
)


logger = create_component_logger("TestFixtures")


# Session-scoped WebSocket Manager
_session_manager = None
_session_tasks: Set[asyncio.Task] = set()


@pytest_asyncio.fixture(scope="session")
async def session_websocket_manager():
    """Session-scoped WebSocket 매니저 (공유 리소스)"""
    global _session_manager, _session_tasks

    logger.info("=== Session WebSocket 매니저 초기화 ===")

    try:
        _session_manager = await get_websocket_manager()
        logger.info(f"Session 매니저 상태: {_session_manager.get_state()}")

        yield _session_manager

    except Exception as e:
        logger.error(f"Session WebSocket 매니저 초기화 실패: {e}")
        pytest.skip(f"Session WebSocket 매니저 생성 실패: {e}")
    finally:
        logger.info("=== Session 매니저 정리 시작 ===")
        await _cleanup_session_manager()


async def _cleanup_session_manager():
    """Session manager와 관련 task들 정리"""
    global _session_manager, _session_tasks

    cleanup_timeout = 10.0  # 2분 → 10초로 단축

    try:
        # 1. 모든 추적된 task 정리
        if _session_tasks:
            logger.info(f"Session task {len(_session_tasks)}개 정리 시작")
            for task in list(_session_tasks):
                if not task.done():
                    task.cancel()

            # Task 완료 대기 (타임아웃 적용)
            if _session_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*_session_tasks, return_exceptions=True),
                        timeout=2.0
                    )
                    logger.info("✅ Session task 정리 완료")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Session task 정리 타임아웃 (강제 진행)")

        # 2. WebSocket Manager 정리
        if _session_manager is not None:
            try:
                await asyncio.wait_for(_session_manager.stop(), timeout=cleanup_timeout)
                logger.info("✅ Session WebSocket 매니저 정리 완료")
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ Session 매니저 정리 타임아웃 ({cleanup_timeout}초)")
            except Exception as e:
                logger.warning(f"⚠️ Session 매니저 정리 중 오류: {e}")

        # 3. 남은 event loop task들 강제 정리
        try:
            loop = asyncio.get_running_loop()
            pending_tasks = [task for task in asyncio.all_tasks(loop)
                             if not task.done() and task != asyncio.current_task()]

            if pending_tasks:
                logger.info(f"남은 pending task {len(pending_tasks)}개 강제 정리")
                for task in pending_tasks:
                    task.cancel()

                # 짧은 타임아웃으로 완료 대기
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*pending_tasks, return_exceptions=True),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Pending task 정리 타임아웃 (무시)")

        except Exception as e:
            logger.warning(f"Event loop task 정리 중 오류: {e}")

    except Exception as e:
        logger.error(f"Session cleanup 중 예외: {e}")
    finally:
        _session_manager = None
        _session_tasks.clear()
        logger.info("=== Session 정리 완료 ===")


@pytest_asyncio.fixture(scope="function")
async def global_manager(session_websocket_manager):
    """Function-scoped WebSocket 매니저 (빠른 격리)"""
    logger.info("=== Function 매니저 시작 ===")

    # Session manager 재사용
    manager = session_websocket_manager

    # 현재 테스트의 task 추적
    test_tasks: Set[asyncio.Task] = set()

    try:
        # 매니저 상태 확인
        state = manager.get_state()
        logger.info(f"Function 매니저 상태: {state}")

        yield manager

    finally:
        logger.info("=== Function 매니저 정리 시작 ===")

        # Function scope cleanup (빠른 정리)
        try:
            # 테스트별 task만 빠르게 정리
            if test_tasks:
                for task in list(test_tasks):
                    if not task.done():
                        task.cancel()

                # 짧은 타임아웃으로 완료 대기
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*test_tasks, return_exceptions=True),
                        timeout=0.5
                    )
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Function task 정리 타임아웃 (무시)")

            logger.info("✅ Function 정리 완료")

        except Exception as e:
            logger.warning(f"Function 정리 중 오류 (무시): {e}")


def track_session_task(task: asyncio.Task):
    """Session 레벨 task 추적 등록"""
    global _session_tasks
    _session_tasks.add(task)

    # Task 완료 시 자동 제거
    def remove_task(t):
        _session_tasks.discard(t)

    task.add_done_callback(remove_task)


@pytest.fixture
def api_keys():
    """API 키 로딩 픽스처"""
    return load_api_keys_if_available()


def load_api_keys_if_available() -> Optional[Dict[str, Any]]:
    """
    API 키 로딩 (ApiKeyService 우선, 환경변수 폴백)

    Returns:
        API 키 딕셔너리 또는 None
    """
    # 1. ApiKeyService를 통한 암호화된 키 로드 시도
    try:
        from upbit_auto_trading.infrastructure.services.api_key_service import ApiKeyService
        from upbit_auto_trading.infrastructure.repositories.sqlite_secure_keys_repository import SqliteSecureKeysRepository
        from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager

        # ApiKeyService 인스턴스 생성
        db_paths = {
            'settings': 'data/settings.sqlite3',
            'strategies': 'data/strategies.sqlite3',
            'market_data': 'data/market_data.sqlite3'
        }
        db_manager = DatabaseManager(db_paths)
        repository = SqliteSecureKeysRepository(db_manager)
        api_key_service = ApiKeyService(repository)

        # 암호화된 API 키 로드
        access_key, secret_key, trade_permission = api_key_service.load_api_keys()
        if access_key and secret_key:
            logger.info("ApiKeyService에서 API 키 로드 성공")
            return {
                "access_key": access_key,
                "secret_key": secret_key,
                "trade_permission": trade_permission
            }
        else:
            logger.debug("ApiKeyService에서 유효한 키를 찾을 수 없음")

    except Exception as e:
        logger.debug(f"ApiKeyService 로드 실패, 환경변수 폴백: {e}")

    # 2. 환경변수 폴백
    access_key = os.getenv("UPBIT_ACCESS_KEY")
    secret_key = os.getenv("UPBIT_SECRET_KEY")

    if access_key and secret_key:
        logger.info("환경변수에서 API 키 로드 성공")
        return {
            "access_key": access_key,
            "secret_key": secret_key,
            "trade_permission": False  # 환경변수는 기본 False
        }

    # 3. config/secure/ 폴더에서 로드 시도 (레거시)
    try:
        from pathlib import Path
        import json

        secure_path = Path("config/secure/api_keys.json")
        if secure_path.exists():
            with open(secure_path, 'r', encoding='utf-8') as f:
                keys = json.load(f)
                if keys.get("access_key") and keys.get("secret_key"):
                    logger.info("config/secure/ 파일에서 API 키 로드 성공")
                    return keys
    except Exception as e:
        logger.debug(f"API 키 파일 로드 실패: {e}")

    logger.warning("API 키를 찾을 수 없습니다. Private 테스트는 건너뜁니다.")
    return None


def has_api_keys() -> bool:
    """API 키 존재 여부 확인"""
    return load_api_keys_if_available() is not None


async def wait_for_events(events_list: List[Any], count: int, timeout: float = 10.0) -> None:
    """
    이벤트 리스트에 지정된 개수의 이벤트가 도착할 때까지 대기

    Args:
        events_list: 이벤트를 저장할 리스트
        count: 대기할 이벤트 개수
        timeout: 타임아웃 (초)

    Raises:
        TimeoutError: 타임아웃 시
    """
    start_time = time.time()
    while len(events_list) < count:
        if time.time() - start_time > timeout:
            raise TimeoutError(f"이벤트 {count}개 대기 시간 초과 (현재: {len(events_list)}개)")
        await asyncio.sleep(0.1)


@pytest.fixture
def event_collector():
    """이벤트 수집기 픽스처"""
    return EventCollector()


class EventCollector:
    """테스트용 이벤트 수집기"""

    def __init__(self):
        self.events: List[Any] = []
        self.event_counts: Dict[str, int] = {}
        self.logger = create_component_logger("EventCollector")

    def add_event(self, event: Any, event_type: str = "unknown"):
        """이벤트 추가"""
        self.events.append(event)
        self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1
        self.logger.debug(f"이벤트 수집: {event_type} (총 {len(self.events)}개)")

    def get_events_by_type(self, event_type: str) -> List[Any]:
        """특정 타입의 이벤트들 반환"""
        # 실제 구현에서는 이벤트 타입 필터링 로직 필요
        return self.events

    def clear(self):
        """이벤트 리스트 초기화"""
        self.events.clear()
        self.event_counts.clear()

    async def wait_for_count(self, count: int, timeout: float = 10.0):
        """지정된 개수의 이벤트 대기"""
        await wait_for_events(self.events, count, timeout)


# 테스트 환경 상수
TEST_SYMBOLS = ["KRW-BTC", "KRW-ETH"]
DEFAULT_TIMEOUT = 10.0
INTEGRATION_TIMEOUT = 30.0

# 성능 기준
PERFORMANCE_CRITERIA = {
    'connection_time': 3.0,      # 연결 시간 < 3초
    'first_message': 5.0,        # 첫 메시지 < 5초
    'message_rate': 10,          # 초당 메시지 >= 10개 (활발한 시간대 기준)
    'memory_usage': 50,          # 메모리 사용량 < 50MB
    'reconnect_time': 5.0        # 재연결 시간 < 5초
}


def pytest_configure(config):
    """pytest 설정"""
    # 비동기 테스트 마커 추가
    config.addinivalue_line("markers", "asyncio: 비동기 테스트")
    config.addinivalue_line("markers", "slow: 느린 테스트 (15초 이상)")
    config.addinivalue_line("markers", "api_required: API 키 필요한 테스트")
    config.addinivalue_line("markers", "integration: 통합 테스트")


def pytest_collection_modifyitems(config, items):
    """테스트 아이템 수정"""
    for item in items:
        # API 키가 필요한 테스트 자동 스킵
        if "api_required" in item.keywords and not has_api_keys():
            item.add_marker(pytest.mark.skip(reason="API 키 없음"))
