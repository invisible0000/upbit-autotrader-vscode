import asyncio
import logging
from typing import Optional, Dict, Any

from upbit_auto_trading.infrastructure.events.event_bus_factory import EventBusFactory
from upbit_auto_trading.infrastructure.events.domain_event_publisher_impl import InfrastructureDomainEventPublisher
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager

class EventSystemInitializer:
    """이벤트 시스템 초기화 관리"""

    @staticmethod
    async def initialize_event_system(
        db_manager: DatabaseManager,
        config: Optional[Dict[str, Any]] = None
    ) -> tuple:
        """완전한 이벤트 시스템 초기화"""

        if config is None:
            config = {
                'max_queue_size': 10000,
                'worker_count': 4,
                'batch_size': 10,
                'batch_timeout_seconds': 1.0
            }

        logger = logging.getLogger(__name__)

        try:
            # 1. 이벤트 버스 생성
            event_bus = EventBusFactory.create_default_event_bus(db_manager)

            # 2. 도메인 이벤트 Publisher 생성
            domain_publisher = InfrastructureDomainEventPublisher(event_bus)

            # 3. 이벤트 버스 시작
            await event_bus.start()

            logger.info("이벤트 시스템 초기화 완료")

            return event_bus, domain_publisher

        except Exception as e:
            logger.error(f"이벤트 시스템 초기화 실패: {e}")
            raise

    @staticmethod
    async def shutdown_event_system(event_bus, timeout: float = 10.0) -> None:
        """이벤트 시스템 종료"""
        logger = logging.getLogger(__name__)

        try:
            # 이벤트 버스 정상 종료
            await asyncio.wait_for(event_bus.stop(), timeout=timeout)
            logger.info("이벤트 시스템 종료 완료")

        except asyncio.TimeoutError:
            logger.warning(f"이벤트 시스템 종료 타임아웃 ({timeout}초)")
        except Exception as e:
            logger.error(f"이벤트 시스템 종료 실패: {e}")
            raise

    @staticmethod
    def create_simple_event_system(db_manager: DatabaseManager) -> tuple:
        """간단한 이벤트 시스템 생성 (비동기 초기화 없음)"""
        logger = logging.getLogger(__name__)

        try:
            # 1. 이벤트 버스 생성
            event_bus = EventBusFactory.create_default_event_bus(db_manager)

            # 2. 도메인 이벤트 Publisher 생성
            domain_publisher = InfrastructureDomainEventPublisher(event_bus)

            logger.info("간단한 이벤트 시스템 생성 완료 (시작되지 않음)")

            return event_bus, domain_publisher

        except Exception as e:
            logger.error(f"간단한 이벤트 시스템 생성 실패: {e}")
            raise

    @staticmethod
    async def get_system_status(event_bus) -> Dict[str, Any]:
        """이벤트 시스템 상태 조회"""
        try:
            stats = event_bus.get_statistics()

            # 추가 상태 정보
            status = {
                'system_status': 'running' if stats['is_running'] else 'stopped',
                'health_check': 'healthy' if stats['is_running'] else 'unhealthy',
                'performance': {
                    'events_per_second': 0,
                    'avg_processing_time': stats.get('avg_processing_time_ms', 0),
                    'queue_utilization': 0
                },
                'statistics': stats
            }

            # 이벤트 처리 속도 계산
            if stats.get('uptime_seconds', 0) > 0:
                status['performance']['events_per_second'] = round(
                    stats['events_processed'] / stats['uptime_seconds'], 2
                )

            # 큐 사용률 계산 (추정)
            if hasattr(event_bus, '_event_queue'):
                queue_size = stats.get('queue_size', 0)
                max_size = getattr(event_bus._event_queue, 'maxsize', 0)
                if max_size > 0:
                    status['performance']['queue_utilization'] = round(
                        (queue_size / max_size) * 100, 2
                    )

            return status

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"시스템 상태 조회 실패: {e}")
            return {
                'system_status': 'error',
                'health_check': 'unhealthy',
                'error': str(e)
            }
