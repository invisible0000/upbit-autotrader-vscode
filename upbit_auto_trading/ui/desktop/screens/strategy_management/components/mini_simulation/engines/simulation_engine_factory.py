"""
통합 시뮬레이션 엔진 팩토리

중복된 시뮬레이션 엔진들을 통합하고 일관된 인터페이스를 제공합니다.
"""

from enum import Enum
from typing import Dict, Any
import logging

from .base_simulation_engines import (
    BaseSimulationEngine,
    EmbeddedSimulationEngine,
    RealDataSimulationEngine,
    RobustSimulationEngine
)


class DataSourceType(Enum):
    """데이터 소스 타입"""
    EMBEDDED = "embedded"      # 내장 최적화 데이터셋
    REAL_DB = "real_db"       # 실제 DB 데이터
    SYNTHETIC = "synthetic"    # 합성 데이터
    SIMPLE_FALLBACK = "simple_fallback"  # 단순 폴백


# 엔진 인스턴스 캐시 (싱글톤 패턴)
_engine_cache: Dict[DataSourceType, BaseSimulationEngine] = {}


def get_simulation_engine(source_type: DataSourceType = DataSourceType.EMBEDDED) -> BaseSimulationEngine:
    """
    데이터 소스 타입에 따른 시뮬레이션 엔진 반환
    
    Args:
        source_type: 데이터 소스 타입
        
    Returns:
        BaseSimulationEngine: 시뮬레이션 엔진 인스턴스
    """
    if source_type not in _engine_cache:
        if source_type == DataSourceType.EMBEDDED:
            _engine_cache[source_type] = EmbeddedSimulationEngine()
        elif source_type == DataSourceType.REAL_DB:
            _engine_cache[source_type] = RealDataSimulationEngine()
        elif source_type == DataSourceType.SYNTHETIC:
            _engine_cache[source_type] = RobustSimulationEngine()
        else:  # SIMPLE_FALLBACK
            _engine_cache[source_type] = EmbeddedSimulationEngine()  # 폴백
            
        logging.info(f"✅ {source_type.value} 시뮬레이션 엔진 생성")
    
    return _engine_cache[source_type]


def get_embedded_simulation_engine() -> BaseSimulationEngine:
    """내장 시뮬레이션 엔진 반환 (호환성)"""
    return get_simulation_engine(DataSourceType.EMBEDDED)


def get_real_data_simulation_engine() -> BaseSimulationEngine:
    """실제 데이터 시뮬레이션 엔진 반환 (호환성)"""
    return get_simulation_engine(DataSourceType.REAL_DB)


def get_robust_simulation_engine() -> BaseSimulationEngine:
    """견고한 시뮬레이션 엔진 반환 (호환성)"""
    return get_simulation_engine(DataSourceType.SYNTHETIC)


def reset_engine_cache():
    """엔진 캐시 초기화 (테스트용)"""
    global _engine_cache
    _engine_cache.clear()
    logging.info("🔄 시뮬레이션 엔진 캐시 초기화")


def get_available_engines() -> Dict[str, Any]:
    """사용 가능한 엔진 정보 반환"""
    return {
        'engines': [e.value for e in DataSourceType],
        'cached_engines': list(_engine_cache.keys()),
        'default_engine': DataSourceType.EMBEDDED.value
    }
