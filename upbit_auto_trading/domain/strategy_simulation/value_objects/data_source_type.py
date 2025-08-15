"""
전략 시뮬레이션 데이터 소스 타입 Value Object
"""

from enum import Enum
from typing import Dict, List


class DataSourceType(Enum):
    """
    전략 시뮬레이션 데이터 소스 타입

    전략 관리 화면 전용 미니 시뮬레이션에서 사용
    실제 백테스팅과는 별개의 도메인
    """

    # 내장 최적화 데이터셋 (시나리오별 특화)
    EMBEDDED_OPTIMIZED = "embedded"

    # 실제 DB 데이터 (시나리오별 세그멘테이션)
    REAL_DATABASE = "real_db"

    # 합성 현실적 데이터
    SYNTHETIC_REALISTIC = "synthetic"

    # 단순 폴백 데이터
    SIMPLE_FALLBACK = "fallback"

    @classmethod
    def get_display_name(cls, source_type: 'DataSourceType') -> str:
        """UI 표시용 이름 반환"""
        display_names = {
            cls.EMBEDDED_OPTIMIZED: "내장 최적화",
            cls.REAL_DATABASE: "실제 DB",
            cls.SYNTHETIC_REALISTIC: "합성 현실적",
            cls.SIMPLE_FALLBACK: "단순 폴백"
        }
        return display_names.get(source_type, source_type.value)

    @classmethod
    def get_description(cls, source_type: 'DataSourceType') -> str:
        """상세 설명 반환"""
        descriptions = {
            cls.EMBEDDED_OPTIMIZED: "시나리오별 최적화된 내장 데이터셋",
            cls.REAL_DATABASE: "실제 시장 데이터 (시나리오별 세그멘테이션)",
            cls.SYNTHETIC_REALISTIC: "합성된 현실적 시장 데이터",
            cls.SIMPLE_FALLBACK: "단순 생성된 폴백 데이터"
        }
        return descriptions.get(source_type, f"{source_type.value} 데이터 소스")

    @classmethod
    def get_all_types(cls) -> List['DataSourceType']:
        """모든 데이터 소스 타입 반환"""
        return list(cls)

    @classmethod
    def get_priority_order(cls) -> List['DataSourceType']:
        """우선순위 순서로 정렬된 타입 목록"""
        return [
            cls.EMBEDDED_OPTIMIZED,    # 최우선 (시나리오별 최적화)
            cls.REAL_DATABASE,         # 실제 데이터
            cls.SYNTHETIC_REALISTIC,   # 합성 데이터
            cls.SIMPLE_FALLBACK        # 최후 폴백
        ]

    def is_recommended(self) -> bool:
        """추천 데이터 소스 여부"""
        return self == DataSourceType.EMBEDDED_OPTIMIZED

    def requires_external_data(self) -> bool:
        """외부 데이터 파일 필요 여부"""
        return self in [DataSourceType.REAL_DATABASE]

    def is_fallback(self) -> bool:
        """폴백 데이터 소스 여부"""
        return self == DataSourceType.SIMPLE_FALLBACK
