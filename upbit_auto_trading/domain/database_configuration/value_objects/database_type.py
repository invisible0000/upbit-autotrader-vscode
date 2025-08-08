"""
데이터베이스 설정 도메인 - 데이터베이스 타입 값 객체

데이터베이스 타입의 분류와 특성을 관리하는 값 객체입니다.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("DatabaseType")


class DatabaseCategory(Enum):
    """데이터베이스 카테고리"""
    CONFIGURATION = "configuration"  # 설정 데이터
    BUSINESS_DATA = "business_data"   # 비즈니스 데이터
    CACHE_DATA = "cache_data"         # 캐시 데이터


@dataclass(frozen=True)
class DatabaseType:
    """
    데이터베이스 타입 값 객체

    데이터베이스의 타입별 특성과 비즈니스 규칙을 캡슐화합니다.
    """

    type_name: str
    category: DatabaseCategory
    description: str
    default_filename: str

    # 타입별 상수 정의
    SETTINGS = None      # 클래스 변수로 나중에 설정
    STRATEGIES = None
    MARKET_DATA = None

    def __post_init__(self):
        """값 객체 생성 후 유효성 검증"""
        self._validate_type()
        logger.debug(f"DatabaseType 생성됨: {self.type_name} ({self.category.value})")

    def _validate_type(self) -> None:
        """타입 유효성 검증"""
        if not self.type_name or len(self.type_name.strip()) == 0:
            raise ValueError("데이터베이스 타입 이름은 필수입니다")

        # 허용된 타입 검증
        allowed_types = ['settings', 'strategies', 'market_data']
        if self.type_name not in allowed_types:
            raise ValueError(f"지원하지 않는 데이터베이스 타입: {self.type_name}")

        if not self.description or len(self.description.strip()) == 0:
            raise ValueError("데이터베이스 타입 설명은 필수입니다")

        if not self.default_filename or not self.default_filename.endswith('.sqlite3'):
            raise ValueError("기본 파일명은 .sqlite3 확장자를 가져야 합니다")

    def is_configuration_database(self) -> bool:
        """설정 데이터베이스 여부 확인"""
        is_config = self.category == DatabaseCategory.CONFIGURATION
        logger.debug(f"설정 데이터베이스 확인 - {self.type_name}: {is_config}")
        return is_config

    def is_business_database(self) -> bool:
        """비즈니스 데이터베이스 여부 확인"""
        is_business = self.category == DatabaseCategory.BUSINESS_DATA
        logger.debug(f"비즈니스 데이터베이스 확인 - {self.type_name}: {is_business}")
        return is_business

    def is_cache_database(self) -> bool:
        """캐시 데이터베이스 여부 확인"""
        is_cache = self.category == DatabaseCategory.CACHE_DATA
        logger.debug(f"캐시 데이터베이스 확인 - {self.type_name}: {is_cache}")
        return is_cache

    def requires_backup(self) -> bool:
        """백업 필요 여부 확인"""
        # 설정과 비즈니스 데이터는 백업 필요, 캐시는 불필요
        needs_backup = self.category in [DatabaseCategory.CONFIGURATION, DatabaseCategory.BUSINESS_DATA]
        logger.debug(f"백업 필요 여부 - {self.type_name}: {needs_backup}")
        return needs_backup

    def get_backup_priority(self) -> int:
        """백업 우선순위 반환 (1: 높음, 3: 낮음)"""
        priority_map = {
            'settings': 1,      # 설정은 최우선
            'strategies': 2,    # 전략은 두 번째
            'market_data': 3    # 시장 데이터는 마지막
        }

        priority = priority_map.get(self.type_name, 3)
        logger.debug(f"백업 우선순위 - {self.type_name}: {priority}")
        return priority

    def get_retention_days(self) -> int:
        """데이터 보존 기간 (일) 반환"""
        retention_map = {
            'settings': 365,      # 설정은 1년
            'strategies': 180,    # 전략은 6개월
            'market_data': 30     # 시장 데이터는 1개월
        }

        days = retention_map.get(self.type_name, 30)
        logger.debug(f"데이터 보존 기간 - {self.type_name}: {days}일")
        return days

    def get_expected_tables(self) -> List[str]:
        """데이터베이스에 포함되어야 할 테이블 목록"""
        table_map = {
            'settings': [
                'tv_trading_variables',
                'tv_variable_parameters',
                'tv_indicator_categories',
                'tv_comparison_groups',
                'tv_help_texts',
                'tv_placeholder_texts',
                'tv_indicator_library',
                'tv_parameter_types'
            ],
            'strategies': [
                'strategies',
                'strategy_rules',
                'strategy_conditions',
                'backtest_results',
                'backtest_trades'
            ],
            'market_data': [
                'market_prices',
                'technical_indicators',
                'volume_data',
                'order_book_data',
                'cache_metadata'
            ]
        }

        tables = table_map.get(self.type_name, [])
        logger.debug(f"예상 테이블 목록 - {self.type_name}: {tables}")
        return tables

    def get_display_properties(self) -> Dict[str, Any]:
        """UI 표시용 속성 반환"""
        return {
            'name': self.type_name,
            'display_name': self._get_display_name(),
            'category': self.category.value,
            'description': self.description,
            'default_filename': self.default_filename,
            'requires_backup': self.requires_backup(),
            'backup_priority': self.get_backup_priority(),
            'retention_days': self.get_retention_days(),
            'icon': self._get_icon(),
            'color': self._get_color()
        }

    def _get_display_name(self) -> str:
        """UI 표시용 이름 반환"""
        display_names = {
            'settings': '설정 데이터베이스',
            'strategies': '전략 데이터베이스',
            'market_data': '시장 데이터베이스'
        }
        return display_names.get(self.type_name, self.type_name)

    def _get_icon(self) -> str:
        """타입별 아이콘 이름 반환"""
        icons = {
            'settings': 'settings',
            'strategies': 'strategy',
            'market_data': 'chart'
        }
        return icons.get(self.type_name, 'database')

    def _get_color(self) -> str:
        """타입별 색상 반환"""
        colors = {
            'settings': '#4CAF50',      # 녹색
            'strategies': '#2196F3',    # 파란색
            'market_data': '#FF9800'    # 주황색
        }
        return colors.get(self.type_name, '#9E9E9E')

    def can_be_replaced_by(self, other: 'DatabaseType') -> bool:
        """다른 타입으로 교체 가능한지 확인"""
        # 같은 타입만 교체 가능
        can_replace = self.type_name == other.type_name
        logger.debug(f"타입 교체 가능성 - {self.type_name} -> {other.type_name}: {can_replace}")
        return can_replace

    def __str__(self) -> str:
        return self.type_name

    def __repr__(self) -> str:
        return f"DatabaseType(type_name='{self.type_name}', category='{self.category.value}')"

    def __eq__(self, other) -> bool:
        if not isinstance(other, DatabaseType):
            return False
        return self.type_name == other.type_name

    def __hash__(self) -> int:
        return hash(self.type_name)


# 상수 정의
DatabaseType.SETTINGS = DatabaseType(
    type_name="settings",
    category=DatabaseCategory.CONFIGURATION,
    description="애플리케이션 설정 및 변수 정의",
    default_filename="settings.sqlite3"
)

DatabaseType.STRATEGIES = DatabaseType(
    type_name="strategies",
    category=DatabaseCategory.BUSINESS_DATA,
    description="매매 전략 및 백테스팅 결과",
    default_filename="strategies.sqlite3"
)

DatabaseType.MARKET_DATA = DatabaseType(
    type_name="market_data",
    category=DatabaseCategory.CACHE_DATA,
    description="시장 데이터 및 기술적 지표 캐시",
    default_filename="market_data.sqlite3"
)


def get_all_database_types() -> List[DatabaseType]:
    """모든 데이터베이스 타입 반환"""
    return [
        DatabaseType.SETTINGS,
        DatabaseType.STRATEGIES,
        DatabaseType.MARKET_DATA
    ]


def get_database_type_by_name(type_name: str) -> DatabaseType:
    """이름으로 데이터베이스 타입 조회"""
    type_map = {
        'settings': DatabaseType.SETTINGS,
        'strategies': DatabaseType.STRATEGIES,
        'market_data': DatabaseType.MARKET_DATA
    }

    db_type = type_map.get(type_name.lower())
    if not db_type:
        raise ValueError(f"지원하지 않는 데이터베이스 타입: {type_name}")

    logger.debug(f"데이터베이스 타입 조회: {type_name} -> {db_type}")
    return db_type
