"""
MarketDataBackbone V2.3 - Data Persistence System (최적화 버전)

실사용 시나리오 최적화된 데이터 지속성 시스템:
- 스크리너 → 백테스팅 → 실거래 워크플로우 최적화
- API 200개 제한 대응 및 4계층 시스템
- 심볼별 개별 테이블 + 지능형 캐싱 전략

구조:
1. collection_engine.py - API 수집 최적화
2. optimized_db_manager.py - DB 최적화 (L3)
3. smart_cache_manager.py - 지능형 캐싱 (L1/L2)
4. cache_manager.py - 통합 관리자 (하위 호환)
"""

# 핵심 엔진들
from .collection_engine import (
    CollectionEngine,
    APICollector,
    RequestOptimizer,
    ErrorHandler
)

# 최적화된 저장/캐시 시스템
from .optimized_db_manager import (
    OptimizedDBManager,
    SmartDataManager,
    TimeRange,
    DataGap
)

from .smart_cache_manager import (
    SmartCacheManager,
    OptimizedMemoryCache,
    IntelligentDiskCache,
    create_smart_cache_manager
)

# 통합 관리자 (메인 인터페이스)
from .cache_manager import (
    CacheManager,
    create_optimized_cache_manager
)

__all__ = [
    # Collection Engine
    'CollectionEngine',
    'APICollector',
    'RequestOptimizer',
    'ErrorHandler',

    # Optimized DB Manager
    'OptimizedDBManager',
    'SmartDataManager',
    'TimeRange',
    'DataGap',

    # Smart Cache Manager
    'SmartCacheManager',
    'OptimizedMemoryCache',
    'IntelligentDiskCache',
    'create_smart_cache_manager',

    # Unified Cache Manager (Main Interface)
    'CacheManager',
    'create_optimized_cache_manager'
]

__version__ = "2.3.0"
__architecture__ = "4-layer-optimized"
