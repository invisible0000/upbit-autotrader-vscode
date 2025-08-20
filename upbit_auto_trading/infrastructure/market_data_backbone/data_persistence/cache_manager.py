"""
통합 캐시 관리자 - V2.3 최적화 버전

새로운 구조:
- OptimizedDBManager: L3 DB 저장 (심볼별 테이블)
- SmartCacheManager: L1/L2 캐싱 (메모리/디스크)
- 워크플로우별 최적화 전략
"""

from typing import List, Dict, Any, Optional
from upbit_auto_trading.infrastructure.logging import create_component_logger
from .optimized_db_manager import OptimizedDBManager
from .smart_cache_manager import SmartCacheManager


class CacheManager:
    """
    통합 캐시 관리자 (하위 호환성 유지)

    내부적으로 최적화된 구조 사용:
    - L1/L2: SmartCacheManager
    - L3: OptimizedDBManager
    """

    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = {}

        # 기본 설정
        db_config = config.get('database_cache', {})
        db_path = db_config.get('db_path', 'data/market_data.sqlite3')

        cache_config = {
            'memory_cache': config.get('memory_cache', {'max_size': 1000, 'ttl_seconds': 300}),
            'disk_cache': config.get('disk_cache', {'cache_dir': 'data/cache', 'max_size_mb': 500, 'ttl_seconds': 3600})
        }

        # 최적화된 구성 요소 초기화
        self.db_manager = OptimizedDBManager(db_path)
        self.cache_manager = SmartCacheManager(cache_config)
        self._logger = create_component_logger("CacheManager")

        # 통계 추적
        self.stats = {
            'cache_hits': 0,
            'db_hits': 0,
            'total_requests': 0
        }

    def get(self, symbol: str, timeframe: str, start_time: str, end_time: str) -> Optional[List[Dict[str, Any]]]:
        """
        다층 캐시에서 데이터 조회

        순서: L1 메모리 → L2 디스크 → L3 DB
        """
        self.stats['total_requests'] += 1

        # L1/L2 캐시 시도
        data = self.cache_manager.get(symbol, timeframe, start_time, end_time)
        if data is not None:
            self.stats['cache_hits'] += 1
            return data

        # L3 DB 조회
        data = self.db_manager.get_candles(symbol, timeframe, start_time, end_time)
        if data is not None:
            self.stats['db_hits'] += 1

            # 캐시에 승급 저장
            self.cache_manager.put(symbol, timeframe, start_time, end_time, data)

            self._logger.debug(f"DB 히트 → 캐시 승급: {symbol} {timeframe} ({len(data)}개)")
            return data

        # 완전 미스
        self._logger.debug(f"데이터 미스: {symbol} {timeframe}")
        return None

    def put(self, symbol: str, timeframe: str, start_time: str, end_time: str, data: List[Dict[str, Any]]) -> None:
        """모든 계층에 데이터 저장"""
        if not data:
            return

        # L1/L2 캐시 저장 (지능형 전략)
        self.cache_manager.put(symbol, timeframe, start_time, end_time, data)

        # L3 DB 저장 (최적화된 테이블 구조)
        stored_count = self.db_manager.store_candles(symbol, timeframe, data)

        self._logger.debug(f"전체 저장 완료: {symbol} {timeframe} ({stored_count}개)")

    def invalidate(self, symbol: str, timeframe: str = None) -> None:
        """특정 심볼/타임프레임 캐시 무효화"""
        self.cache_manager.invalidate_symbol(symbol, timeframe)
        self._logger.info(f"캐시 무효화: {symbol} {timeframe or 'all'}")

    def optimize_for_workflow(self, workflow_type: str) -> None:
        """워크플로우별 캐시 최적화"""
        self.cache_manager.optimize_for_workflow(workflow_type)
        self._logger.info(f"워크플로우 최적화 적용: {workflow_type}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """전체 성능 요약"""
        cache_summary = self.cache_manager.get_performance_summary()
        db_summary = self.db_manager.get_storage_summary()

        total_hits = self.stats['cache_hits'] + self.stats['db_hits']
        overall_hit_rate = total_hits / self.stats['total_requests'] if self.stats['total_requests'] > 0 else 0

        return {
            'overall_performance': {
                'hit_rate': overall_hit_rate,
                'cache_hits': self.stats['cache_hits'],
                'db_hits': self.stats['db_hits'],
                'total_requests': self.stats['total_requests']
            },
            'cache_performance': cache_summary,
            'db_performance': {
                'total_ranges': db_summary.get('total_ranges', 0),
                'total_records': db_summary.get('total_records', 0)
            }
        }

    def find_gaps(self, symbol: str, timeframe: str, start_time: str, end_time: str):
        """데이터 누락 구간 분석 (DB 레벨)"""
        return self.db_manager.find_data_gaps(symbol, timeframe, start_time, end_time)

    def get_storage_info(self) -> Dict[str, Any]:
        """저장 현황 상세 정보"""
        return self.db_manager.get_storage_summary()


# 하위 호환성을 위한 별칭
MemoryCache = None  # 더 이상 직접 사용하지 않음
DiskCache = None    # 더 이상 직접 사용하지 않음
DatabaseCache = None # OptimizedDBManager로 대체됨


# 워크플로우별 최적화된 캐시 매니저 팩토리
def create_optimized_cache_manager(workflow_type: str = "balanced") -> CacheManager:
    """워크플로우별 최적화된 캐시 매니저 생성"""

    workflow_configs = {
        "live_trading": {
            'memory_cache': {'max_size': 500, 'ttl_seconds': 60},
            'disk_cache': {'cache_dir': 'data/cache/live', 'max_size_mb': 100, 'ttl_seconds': 300},
            'database_cache': {'db_path': 'data/market_data.sqlite3'}
        },
        "backtesting": {
            'memory_cache': {'max_size': 2000, 'ttl_seconds': 600},
            'disk_cache': {'cache_dir': 'data/cache/backtest', 'max_size_mb': 1000, 'ttl_seconds': 7200},
            'database_cache': {'db_path': 'data/market_data.sqlite3'}
        },
        "screening": {
            'memory_cache': {'max_size': 100, 'ttl_seconds': 10},
            'disk_cache': {'cache_dir': 'data/cache/screen', 'max_size_mb': 50, 'ttl_seconds': 300},
            'database_cache': {'db_path': 'data/market_data.sqlite3'}
        }
    }

    config = workflow_configs.get(workflow_type, {
        'memory_cache': {'max_size': 1000, 'ttl_seconds': 300},
        'disk_cache': {'cache_dir': 'data/cache', 'max_size_mb': 500, 'ttl_seconds': 3600},
        'database_cache': {'db_path': 'data/market_data.sqlite3'}
    })

    cache_manager = CacheManager(config)
    cache_manager.optimize_for_workflow(workflow_type)

    return cache_manager
