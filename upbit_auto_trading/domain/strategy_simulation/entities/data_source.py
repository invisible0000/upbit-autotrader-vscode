"""
전략 시뮬레이션 데이터 소스 엔티티
전략 관리 전용 미니 시뮬레이션에서 사용하는 데이터 소스
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

from upbit_auto_trading.domain.strategy_simulation.value_objects.data_source_type import DataSourceType
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("DataSourceEntity")


@dataclass(frozen=True)
class DataSource:
    """
    전략 시뮬레이션 데이터 소스 엔티티

    - 전략 관리 화면에서만 사용하는 미니 시뮬레이션 전용
    - 실제 백테스팅과는 별개의 도메인
    - 미리 샘플된 마켓 데이터 기반
    """
    source_type: DataSourceType
    name: str
    description: str
    is_available: bool
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """데이터 소스 유효성 검증"""
        if not self.name or not self.name.strip():
            raise ValueError("데이터 소스 이름은 필수입니다")

        if not self.description or not self.description.strip():
            raise ValueError("데이터 소스 설명은 필수입니다")

        logger.debug(f"데이터 소스 엔티티 생성: {self.name} ({self.source_type.value})")

    def is_usable(self) -> bool:
        """데이터 소스 사용 가능 여부"""
        return self.is_available and self.source_type is not None

    def get_display_name(self) -> str:
        """UI 표시용 이름"""
        status = "✅" if self.is_available else "❌"
        return f"{status} {self.name}"

    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """메타데이터 값 조회"""
        if not self.metadata:
            return default
        return self.metadata.get(key, default)

    def with_availability(self, available: bool) -> 'DataSource':
        """가용성이 변경된 새 데이터 소스 인스턴스 반환"""
        return DataSource(
            source_type=self.source_type,
            name=self.name,
            description=self.description,
            is_available=available,
            metadata=self.metadata
        )
