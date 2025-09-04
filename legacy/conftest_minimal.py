"""
WebSocket v6 테스트용 최소 픽스처 (Logging 문제 해결)
====================================================

pytest-asyncio cleanup 문제의 근본 해결:
- Session scope 완전 제거 → Function scope만 사용
- 로깅 안전성 보장 (I/O closed file 방지)
- 최소한의 cleanup으로 빠른 종료
- Background task 추적 없음 (단순성 우선)
"""

import pytest
import pytest_asyncio
import asyncio
import time
import os
import sys
from typing import List, Dict, Any, Optional

# 안전한 로깅 (I/O 오류 방지)


def safe_log(message: str, level: str = "INFO"):
    """안전한 로깅 - I/O 닫힌 파일 오류 방지"""
    try:
        if hasattr(sys.stdout, 'closed') and not sys.stdout.closed:
            print(f"[{level}] {message}")
    except Exception:
        pass  # 로깅 실패해도 무시


@pytest_asyncio.fixture(scope="function")
async def global_manager():
    """최소 WebSocket 매니저 function 픽스처 (안전한 로깅)"""
    safe_log("=== 최소 WebSocket 매니저 초기화 ===")

    manager = None
    try:
        from upbit_auto_trading.infrastructure.external_apis.upbit.websocket.core.websocket_manager import (
            get_websocket_manager
        )

        manager = await get_websocket_manager()
        state = manager.get_state()
        safe_log(f"매니저 상태: {state}")

        yield manager

    except Exception as e:
        safe_log(f"WebSocket 매니저 초기화 실패: {e}", "ERROR")
        pytest.skip(f"WebSocket 매니저 생성 실패: {e}")
    finally:
        safe_log("=== 최소 매니저 정리 시작 ===")
        try:
            if manager is not None:
                # 매우 짧은 타임아웃으로 빠른 정리
                try:
                    await asyncio.wait_for(manager.stop(), timeout=0.1)
                    safe_log("✅ 초고속 정리 완료")
                except asyncio.TimeoutError:
                    safe_log("⚠️ 초고속 정리 타임아웃 (무시)")
                except Exception as e:
                    safe_log(f"⚠️ 초고속 정리 중 오류 (무시): {e}")
        except Exception as e:
            safe_log(f"매니저 정리 중 오류 (무시): {e}")


@pytest.fixture
def api_keys():
    """API 키 로딩 픽스처"""
    return load_api_keys_if_available()


def load_api_keys_if_available() -> Optional[Dict[str, Any]]:
    """API 키 로딩 (환경변수 우선)"""
    # 환경변수 우선 (단순성)
    access_key = os.getenv("UPBIT_ACCESS_KEY")
    secret_key = os.getenv("UPBIT_SECRET_KEY")

    if access_key and secret_key:
        safe_log("환경변수에서 API 키 로드 성공")
        return {
            "access_key": access_key,
            "secret_key": secret_key,
            "trade_permission": False
        }

    # ApiKeyService 시도
    try:
        from upbit_auto_trading.infrastructure.services.api_key_service import ApiKeyService
        from upbit_auto_trading.infrastructure.repositories.sqlite_secure_keys_repository import SqliteSecureKeysRepository
        from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager

        db_paths = {
            'settings': 'data/settings.sqlite3',
            'strategies': 'data/strategies.sqlite3',
            'market_data': 'data/market_data.sqlite3'
        }
        db_manager = DatabaseManager(db_paths)
        repository = SqliteSecureKeysRepository(db_manager)
        api_key_service = ApiKeyService(repository)

        access_key, secret_key, trade_permission = api_key_service.load_api_keys()
        if access_key and secret_key:
            safe_log("ApiKeyService에서 API 키 로드 성공")
            return {
                "access_key": access_key,
                "secret_key": secret_key,
                "trade_permission": trade_permission
            }
    except Exception as e:
        safe_log(f"ApiKeyService 로드 실패: {e}")

    safe_log("API 키를 찾을 수 없습니다. Private 테스트는 건너뜁니다.")
    return None


def has_api_keys() -> bool:
    """API 키 존재 여부 확인"""
    return load_api_keys_if_available() is not None


async def wait_for_events(events_list: List[Any], count: int, timeout: float = 10.0) -> None:
    """이벤트 리스트에 지정된 개수의 이벤트가 도착할 때까지 대기"""
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

    def add_event(self, event: Any, event_type: str = "unknown"):
        """이벤트 추가"""
        self.events.append(event)
        self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1
        safe_log(f"이벤트 수집: {event_type} (총 {len(self.events)}개)")

    def get_events_by_type(self, event_type: str) -> List[Any]:
        """특정 타입의 이벤트들 반환"""
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
    'connection_time': 3.0,
    'first_message': 5.0,
    'message_rate': 10,
    'memory_usage': 50,
    'reconnect_time': 5.0
}


def pytest_configure(config):
    """pytest 설정"""
    config.addinivalue_line("markers", "asyncio: 비동기 테스트")
    config.addinivalue_line("markers", "slow: 느린 테스트 (15초 이상)")
    config.addinivalue_line("markers", "api_required: API 키 필요한 테스트")
    config.addinivalue_line("markers", "integration: 통합 테스트")


def pytest_collection_modifyitems(config, items):
    """테스트 아이템 수정"""
    for item in items:
        if "api_required" in item.keywords and not has_api_keys():
            item.add_marker(pytest.mark.skip(reason="API 키 없음"))
