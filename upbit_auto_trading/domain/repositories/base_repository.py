"""
기본 Repository 인터페이스

모든 Repository 구현의 기반이 되는 Generic 기반 추상 인터페이스를 정의합니다.
기존 SQLite 직접 접근 방식과 SQLAlchemy ORM 모두와 호환 가능하도록 설계되었습니다.
Domain Event 발행을 통한 영속화 이벤트 알림 지원

Author: Repository 인터페이스 정의 Task
Created: 2025-08-04
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List

# Domain Event 관련 import 추가
from upbit_auto_trading.domain.events.domain_event_publisher import get_domain_event_publisher

# Generic 타입 변수 정의
T = TypeVar('T')  # Entity 타입
ID = TypeVar('ID')  # ID 타입 (str, int, UUID 등)


class BaseRepository(ABC, Generic[T, ID]):
    """
    모든 Repository의 기본 인터페이스

    DDD(Domain-Driven Design) 패턴에 따라 도메인 엔티티의 영속화를
    추상화하는 Repository 패턴의 기본 인터페이스입니다.

    Generic 타입을 사용하여 타입 안전성을 확보하며,
    기존 데이터 접근 패턴과의 호환성을 고려하여 설계되었습니다.

    Args:
        T: 관리할 도메인 엔티티 타입
        ID: 엔티티 식별자 타입

    Example:
        class StrategyRepository(BaseRepository[Strategy, StrategyId]):
            def save(self, strategy: Strategy) -> None:
                # 구체적인 저장 로직 구현
                pass
    """

    @abstractmethod
    def save(self, entity: T) -> None:
        """
        엔티티를 저장합니다.

        새로운 엔티티의 경우 INSERT, 기존 엔티티의 경우 UPDATE를 수행합니다.
        기존 StrategyStorage.save_strategy() 메서드와 호환되도록 설계되었습니다.

        도메인 이벤트 발행:
        엔티티가 도메인 이벤트를 가지고 있다면 저장 후 자동으로 발행합니다.

        Args:
            entity: 저장할 도메인 엔티티

        Raises:
            RepositoryError: 저장 과정에서 오류가 발생한 경우
        """
        pass

    def _publish_domain_events(self, entity: T) -> None:
        """
        엔티티의 도메인 이벤트를 발행합니다.

        구현체에서 save 메서드 완료 후 호출하여 도메인 이벤트를 발행합니다.
        hasattr()을 사용하여 엔티티가 도메인 이벤트를 지원하는지 확인합니다.

        Args:
            entity: 도메인 이벤트를 가질 수 있는 엔티티
        """
        try:
            # 엔티티가 도메인 이벤트를 지원하는지 확인
            if hasattr(entity, 'get_domain_events') and callable(getattr(entity, 'get_domain_events')):
                events = entity.get_domain_events()
                if events:
                    # 도메인 이벤트 발행
                    publisher = get_domain_event_publisher()
                    publisher.publish_all(events)

                    # 이벤트 발행 후 엔티티에서 이벤트 클리어
                    if hasattr(entity, 'clear_domain_events') and callable(getattr(entity, 'clear_domain_events')):
                        entity.clear_domain_events()
        except Exception as e:
            # 이벤트 발행 실패는 비즈니스 로직에 영향을 주지 않도록 로깅만 수행
            print(f"⚠️ 도메인 이벤트 발행 실패: {e}")

    @abstractmethod
    def find_by_id(self, entity_id: ID) -> Optional[T]:
        """
        ID로 엔티티를 조회합니다.

        기존 DatabaseManager 패턴의 ID 기반 조회 방식과 호환됩니다.

        Args:
            entity_id: 조회할 엔티티의 고유 식별자

        Returns:
            Optional[T]: 조회된 엔티티, 없으면 None

        Raises:
            RepositoryError: 조회 과정에서 오류가 발생한 경우
        """
        pass

    @abstractmethod
    def find_all(self) -> List[T]:
        """
        모든 엔티티를 조회합니다.

        기존 SQLite 직접 접근의 전체 조회 패턴과 호환됩니다.
        대용량 데이터의 경우 페이징 처리를 고려해야 합니다.

        Returns:
            List[T]: 조회된 모든 엔티티 목록

        Raises:
            RepositoryError: 조회 과정에서 오류가 발생한 경우
        """
        pass

    @abstractmethod
    def delete(self, entity_id: ID) -> bool:
        """
        엔티티를 삭제합니다.

        Args:
            entity_id: 삭제할 엔티티의 고유 식별자

        Returns:
            bool: 삭제 성공 여부 (True: 성공, False: 실패 또는 존재하지 않음)

        Raises:
            RepositoryError: 삭제 과정에서 오류가 발생한 경우
        """
        pass

    @abstractmethod
    def exists(self, entity_id: ID) -> bool:
        """
        엔티티 존재 여부를 확인합니다.

        전체 엔티티를 로드하지 않고 존재 여부만 확인하는 효율적인 방법입니다.

        Args:
            entity_id: 확인할 엔티티의 고유 식별자

        Returns:
            bool: 존재 여부 (True: 존재, False: 존재하지 않음)

        Raises:
            RepositoryError: 확인 과정에서 오류가 발생한 경우
        """
        pass
