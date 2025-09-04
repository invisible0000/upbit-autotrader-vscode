"""
WebSocket v6 테스트용 공통 픽스처
==============================

실제 API 기반 테스트를 위한 공통 설정
- 전역 WebSocket 매니저 픽스처
- API 키 로딩 및 검증
- 이벤트 대기 헬퍼
- 테스트 격리 보장
"""

import pytest
import pytest_asyncio
import asyncio
import time
import os
from typing import List, Dict, Any, Optional

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket.core.websocket_manager import (
    get_websocket_manager
)


logger = create_component_logger("TestFixtures")


async def _enhanced_cleanup_for_pytest(manager):
    """pytest 전용 강화된 정리 로직"""
    logger.info("🧪 pytest 전용 강화된 정리 시작")

    try:
        # 1단계: 일반 정리 시도 (짧은 타임아웃)
        await asyncio.wait_for(manager.stop(), timeout=2.0)
        logger.info("✅ 일반 정리 완료")

        # 2단계: 모든 백그라운드 태스크 강제 종료
        await _force_cleanup_all_tasks()

        logger.info("✅ pytest 전용 강화된 정리 완료")

    except asyncio.TimeoutError:
        logger.warning("⚠️ 정리 타임아웃 - 강제 태스크 정리 진행")
        await _force_cleanup_all_tasks()
    except Exception as e:
        logger.warning(f"⚠️ 정리 중 오류: {e}")
        await _force_cleanup_all_tasks()


async def _force_cleanup_all_tasks():
    """모든 백그라운드 태스크 강제 정리"""
    try:
        # 현재 실행 중인 모든 태스크 조회
        current_task = asyncio.current_task()
        all_tasks = [task for task in asyncio.all_tasks() if task != current_task and not task.done()]

        if not all_tasks:
            logger.info("✅ 정리할 태스크 없음")
            return

        logger.info(f"🔄 백그라운드 태스크 강제 정리: {len(all_tasks)}개")

        # 모든 태스크 취소
        for task in all_tasks:
            try:
                if not task.done():
                    task.cancel()
                    logger.debug(f"태스크 취소: {getattr(task, 'get_name', lambda: 'unnamed')()}")
            except Exception as e:
                logger.debug(f"태스크 취소 오류 (무시): {e}")

        # 취소된 태스크들이 완료될 때까지 대기 (최대 1초)
        if all_tasks:
            try:
                await asyncio.wait_for(asyncio.gather(*all_tasks, return_exceptions=True), timeout=1.0)
                logger.info("✅ 모든 태스크 정리 완료")
            except asyncio.TimeoutError:
                logger.warning("⚠️ 일부 태스크 정리 타임아웃 (무시)")
            except Exception as e:
                logger.debug(f"태스크 정리 중 예외 (무시): {e}")

    except Exception as e:
        logger.warning(f"⚠️ 강제 정리 중 오류 (무시): {e}")


@pytest_asyncio.fixture(scope="session")
async def global_manager():
    """전역 WebSocket 매니저 세션 픽스처 (연결 없이 매니저만 생성)"""
    logger.info("=== 전역 WebSocket 매니저 초기화 (연결 없음) ===")

    manager = None
    try:
        manager = await get_websocket_manager()

        # 매니저 상태 확인 (연결 시도 없음)
        state = manager.get_state()
        logger.info(f"매니저 상태: {state}")

        yield manager

    except Exception as e:
        logger.error(f"WebSocket 매니저 초기화 실패: {e}")
        pytest.skip(f"WebSocket 매니저 생성 실패: {e}")
    finally:
        logger.info("=== 전역 WebSocket 매니저 정리 ===")
        try:
            # manager 안전하게 정리
            if manager is not None:
                # event loop 상태 확인 후 정리
                try:
                    loop = asyncio.get_running_loop()
                    if loop and not loop.is_closed():
                        # 🧪 pytest 전용: 즉시 종료 모드
                        await _immediate_cleanup_for_pytest(manager)
                        logger.info("매니저 정상 정리 완료")
                    else:
                        logger.warning("Event loop이 이미 닫혀있어 매니저 정리 생략")
                except RuntimeError as e:
                    logger.warning(f"Event loop 관련 오류, 매니저 정리 생략: {e}")
                except asyncio.TimeoutError:
                    logger.warning("매니저 정리 타임아웃")
        except Exception as e:
            logger.warning(f"매니저 정리 중 오류 (무시): {e}")


async def _immediate_cleanup_for_pytest(manager):
    """pytest 전용 즉시 정리 로직 - 최소한의 대기로 강제 종료"""
    logger.info("🧪 pytest 전용 즉시 정리 시작")

    try:
        # 1단계: 매니저 즉시 정지 (매우 짧은 타임아웃)
        await asyncio.wait_for(manager.stop(), timeout=1.0)
        logger.info("✅ 매니저 정지 완료")

    except asyncio.TimeoutError:
        logger.warning("⚠️ 매니저 정지 타임아웃 - 강제 진행")
    except Exception as e:
        logger.warning(f"⚠️ 매니저 정지 중 오류: {e}")

    # 2단계: 모든 태스크 즉시 취소 (대기 없음)
    try:
        current_task = asyncio.current_task()
        all_tasks = [task for task in asyncio.all_tasks() if task != current_task and not task.done()]

        if all_tasks:
            logger.info(f"🔄 모든 태스크 즉시 취소: {len(all_tasks)}개")
            for task in all_tasks:
                try:
                    if not task.done():
                        task.cancel()
                except Exception:
                    pass  # 무시

            # 매우 짧은 대기만 허용
            try:
                await asyncio.wait_for(asyncio.sleep(0.1), timeout=0.2)
            except asyncio.TimeoutError:
                pass

        logger.info("✅ pytest 전용 즉시 정리 완료")

    except Exception as e:
        logger.warning(f"⚠️ 즉시 정리 중 오류 (무시): {e}")


async def _wait_for_stable_connection(manager, timeout: float = 10.0):
    """WebSocket 연결 안정성 대기"""
    import time
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # 매니저 상태 확인
            health = manager.get_health_status()
            if health and health.status == "healthy":
                logger.info("WebSocket 연결 안정성 확보 완료")
                return True
        except Exception as e:
            logger.debug(f"연결 상태 확인 중: {e}")

        await asyncio.sleep(0.5)

    logger.warning("WebSocket 연결 안정성 확보 타임아웃")
    return False


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
