"""
지능형 캐시 관리자 - 실사용 시나리오 최적화

캐시 계층 재설계:
- L1 메모리 캐시: 실거래/실시간 조회 (100ms 미만)
- L2 디스크 캐시: 백테스팅 중간 결과 (1초 미만)
- L3 DB 저장: OptimizedDBManager로 분리

성능 목표:
- 실거래: 메모리 캐시 히트 99% (1ms 응답)
- 백테스팅: 디스크 캐시 활용으로 30% 속도 향상
- 스크리너: DB 직접 조회 (캐시 우회)
"""

import time
import pickle
import hashlib
import threading
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from collections import OrderedDict

from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass
class CacheEntry:
    """캐시 엔트리"""
    data: List[Dict[str, Any]]
    timestamp: datetime
    access_count: int = 0
    last_access: datetime = field(default_factory=datetime.now)
    size_bytes: int = 0

    def __post_init__(self):
        if not self.size_bytes:
            self.size_bytes = len(str(self.data).encode('utf-8'))


@dataclass
class CacheStats:
    """캐시 통계"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0

    @property
    def hit_rate(self) -> float:
        """히트율 계산"""
        return self.hits / self.total_requests if self.total_requests > 0 else 0.0


class OptimizedMemoryCache:
    """실시간 조회 최적화 메모리 캐시"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = CacheStats()
        self._lock = threading.RLock()
        self._logger = create_component_logger("OptimizedMemoryCache")

    def _make_key(self, symbol: str, timeframe: str, start_time: str, end_time: str) -> str:
        """캐시 키 생성"""
        key_data = f"{symbol}_{timeframe}_{start_time}_{end_time}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]

    def get(self, symbol: str, timeframe: str, start_time: str, end_time: str) -> Optional[List[Dict[str, Any]]]:
        """메모리 캐시에서 조회"""
        key = self._make_key(symbol, timeframe, start_time, end_time)

        with self._lock:
            self.stats.total_requests += 1

            if key not in self.cache:
                self.stats.misses += 1
                return None

            entry = self.cache[key]

            # TTL 확인
            if (datetime.now() - entry.timestamp).total_seconds() > self.ttl_seconds:
                del self.cache[key]
                self.stats.misses += 1
                self.stats.evictions += 1
                return None

            # LRU 업데이트 (맨 뒤로 이동)
            self.cache.move_to_end(key)
            entry.access_count += 1
            entry.last_access = datetime.now()

            self.stats.hits += 1
            self._logger.debug(f"메모리 캐시 히트: {symbol} {timeframe} ({len(entry.data)}개)")

            return entry.data.copy()  # 복사본 반환 (데이터 보호)

    def put(self, symbol: str, timeframe: str, start_time: str, end_time: str, data: List[Dict[str, Any]]) -> None:
        """메모리 캐시에 저장"""
        if not data:
            return

        key = self._make_key(symbol, timeframe, start_time, end_time)
        entry = CacheEntry(
            data=data.copy(),
            timestamp=datetime.now()
        )

        with self._lock:
            # 용량 초과시 LRU 삭제
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                self.stats.evictions += 1

            self.cache[key] = entry
            self._logger.debug(f"메모리 캐시 저장: {symbol} {timeframe} ({len(data)}개)")

    def invalidate(self, symbol: str, timeframe: str = None) -> int:
        """특정 심볼/타임프레임 캐시 무효화"""
        removed_count = 0

        with self._lock:
            keys_to_remove = []
            pattern = f"{symbol}_" if timeframe is None else f"{symbol}_{timeframe}_"

            for key in self.cache.keys():
                # 해시된 키에서는 패턴 매칭이 어려우므로 메타데이터 추가 필요
                # 간단히 전체 무효화
                keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.cache[key]
                removed_count += 1

        self._logger.info(f"메모리 캐시 무효화: {removed_count}개 항목")
        return removed_count

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        with self._lock:
            total_size = sum(entry.size_bytes for entry in self.cache.values())

            return {
                'hit_rate': self.stats.hit_rate,
                'total_entries': len(self.cache),
                'total_size_mb': total_size / 1024 / 1024,
                'hits': self.stats.hits,
                'misses': self.stats.misses,
                'evictions': self.stats.evictions
            }


class IntelligentDiskCache:
    """백테스팅 최적화 디스크 캐시"""

    def __init__(self, cache_dir: str = "data/cache", max_size_mb: int = 500, ttl_seconds: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_mb = max_size_mb
        self.ttl_seconds = ttl_seconds
        self._logger = create_component_logger("IntelligentDiskCache")

        # 메타데이터 파일
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """메타데이터 로드"""
        try:
            if self.metadata_file.exists():
                import json
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self._logger.warning(f"메타데이터 로드 실패: {e}")

        return {'files': {}, 'total_size': 0, 'last_cleanup': None}

    def _save_metadata(self) -> None:
        """메타데이터 저장"""
        try:
            import json
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            self._logger.error(f"메타데이터 저장 실패: {e}")

    def _get_cache_filename(self, symbol: str, timeframe: str, start_time: str, end_time: str) -> str:
        """캐시 파일명 생성"""
        # 시간 범위를 파일명에 포함 (백테스팅에서 중요)
        time_hash = hashlib.md5(f"{start_time}_{end_time}".encode()).hexdigest()[:8]
        return f"{symbol}_{timeframe}_{time_hash}.pickle"

    def get(self, symbol: str, timeframe: str, start_time: str, end_time: str) -> Optional[List[Dict[str, Any]]]:
        """디스크 캐시에서 조회"""
        filename = self._get_cache_filename(symbol, timeframe, start_time, end_time)
        filepath = self.cache_dir / filename

        if not filepath.exists():
            return None

        # TTL 확인
        file_age = time.time() - filepath.stat().st_mtime
        if file_age > self.ttl_seconds:
            filepath.unlink()  # 만료된 파일 삭제
            if filename in self.metadata['files']:
                del self.metadata['files'][filename]
                self._save_metadata()
            return None

        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)

            # 접근 시간 업데이트
            filepath.touch()

            self._logger.debug(f"디스크 캐시 히트: {filename}")
            return data

        except Exception as e:
            self._logger.error(f"디스크 캐시 로드 실패 {filename}: {e}")
            return None

    def put(self, symbol: str, timeframe: str, start_time: str, end_time: str, data: List[Dict[str, Any]]) -> None:
        """디스크 캐시에 저장"""
        if not data:
            return

        filename = self._get_cache_filename(symbol, timeframe, start_time, end_time)
        filepath = self.cache_dir / filename

        try:
            # 용량 정리
            self._cleanup_if_needed()

            with open(filepath, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

            # 메타데이터 업데이트
            file_size = filepath.stat().st_size
            self.metadata['files'][filename] = {
                'size': file_size,
                'created': datetime.now().isoformat(),
                'symbol': symbol,
                'timeframe': timeframe
            }
            self.metadata['total_size'] = sum(f['size'] for f in self.metadata['files'].values())
            self._save_metadata()

            self._logger.debug(f"디스크 캐시 저장: {filename} ({len(data)}개, {file_size//1024}KB)")

        except Exception as e:
            self._logger.error(f"디스크 캐시 저장 실패 {filename}: {e}")

    def _cleanup_if_needed(self) -> int:
        """용량 초과시 오래된 파일 정리"""
        max_size_bytes = self.max_size_mb * 1024 * 1024

        if self.metadata['total_size'] < max_size_bytes:
            return 0

        # 파일들을 접근 시간순으로 정렬
        files_by_access = []
        for filename, info in self.metadata['files'].items():
            filepath = self.cache_dir / filename
            if filepath.exists():
                access_time = filepath.stat().st_atime
                files_by_access.append((access_time, filename, info['size']))

        files_by_access.sort()  # 오래된 것부터

        removed_count = 0
        removed_size = 0

        for access_time, filename, size in files_by_access:
            if self.metadata['total_size'] - removed_size < max_size_bytes:
                break

            filepath = self.cache_dir / filename
            if filepath.exists():
                filepath.unlink()

            if filename in self.metadata['files']:
                del self.metadata['files'][filename]

            removed_size += size
            removed_count += 1

        self.metadata['total_size'] -= removed_size
        self.metadata['last_cleanup'] = datetime.now().isoformat()
        self._save_metadata()

        if removed_count > 0:
            self._logger.info(f"디스크 캐시 정리: {removed_count}개 파일 ({removed_size//1024//1024}MB)")

        return removed_count


class SmartCacheManager:
    """지능형 캐시 매니저 (L1 메모리 + L2 디스크)"""

    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = {
                'memory_cache': {'max_size': 1000, 'ttl_seconds': 300},
                'disk_cache': {'cache_dir': 'data/cache', 'max_size_mb': 500, 'ttl_seconds': 3600}
            }

        self.l1_memory = OptimizedMemoryCache(**config['memory_cache'])
        self.l2_disk = IntelligentDiskCache(**config['disk_cache'])
        self._logger = create_component_logger("SmartCacheManager")

        # 전체 통계
        self.global_stats = {
            'l1_hits': 0,
            'l2_hits': 0,
            'cache_misses': 0,
            'total_requests': 0
        }

    def get(self, symbol: str, timeframe: str, start_time: str, end_time: str) -> Optional[List[Dict[str, Any]]]:
        """지능형 계층 캐시 조회"""
        self.global_stats['total_requests'] += 1

        # L1 메모리 캐시 시도
        data = self.l1_memory.get(symbol, timeframe, start_time, end_time)
        if data is not None:
            self.global_stats['l1_hits'] += 1
            return data

        # L2 디스크 캐시 시도
        data = self.l2_disk.get(symbol, timeframe, start_time, end_time)
        if data is not None:
            self.global_stats['l2_hits'] += 1

            # L1으로 승급 (자주 사용되는 데이터)
            self.l1_memory.put(symbol, timeframe, start_time, end_time, data)
            return data

        # 캐시 미스
        self.global_stats['cache_misses'] += 1
        return None

    def put(self, symbol: str, timeframe: str, start_time: str, end_time: str, data: List[Dict[str, Any]]) -> None:
        """지능형 캐시 저장"""
        if not data:
            return

        # 데이터 크기 기반 저장 전략
        data_size = len(data)

        if data_size <= 100:
            # 소량 데이터: 메모리 캐시에만 (실시간 조회용)
            self.l1_memory.put(symbol, timeframe, start_time, end_time, data)
        elif data_size <= 1000:
            # 중간 데이터: 양쪽 모두 저장
            self.l1_memory.put(symbol, timeframe, start_time, end_time, data)
            self.l2_disk.put(symbol, timeframe, start_time, end_time, data)
        else:
            # 대량 데이터: 디스크 캐시에만 (백테스팅용)
            self.l2_disk.put(symbol, timeframe, start_time, end_time, data)

        self._logger.debug(f"지능형 캐시 저장: {symbol} {timeframe} ({data_size}개)")

    def invalidate_symbol(self, symbol: str, timeframe: str = None) -> None:
        """심볼별 캐시 무효화"""
        self.l1_memory.invalidate(symbol, timeframe)
        # 디스크 캐시는 TTL에 의존 (파일 삭제 비용 고려)

    def get_performance_summary(self) -> Dict[str, Any]:
        """캐시 성능 요약"""
        l1_stats = self.l1_memory.get_stats()

        total_hits = self.global_stats['l1_hits'] + self.global_stats['l2_hits']
        overall_hit_rate = total_hits / self.global_stats['total_requests'] if self.global_stats['total_requests'] > 0 else 0

        return {
            'overall_hit_rate': overall_hit_rate,
            'l1_memory': l1_stats,
            'l2_disk': {
                'cache_dir': str(self.l2_disk.cache_dir),
                'total_files': len(self.l2_disk.metadata['files']),
                'total_size_mb': self.l2_disk.metadata['total_size'] / 1024 / 1024
            },
            'request_distribution': {
                'l1_hits': self.global_stats['l1_hits'],
                'l2_hits': self.global_stats['l2_hits'],
                'cache_misses': self.global_stats['cache_misses'],
                'total_requests': self.global_stats['total_requests']
            }
        }

    def optimize_for_workflow(self, workflow_type: str) -> None:
        """워크플로우별 캐시 최적화"""
        if workflow_type == "live_trading":
            # 실거래: 메모리 캐시 우선, 짧은 TTL
            self.l1_memory.ttl_seconds = 60  # 1분

        elif workflow_type == "backtesting":
            # 백테스팅: 디스크 캐시 활용, 긴 TTL
            self.l1_memory.ttl_seconds = 600  # 10분
            self.l2_disk.ttl_seconds = 7200   # 2시간

        elif workflow_type == "screening":
            # 스크리너: 캐시 비활성화 (대량 일회성 조회)
            self.l1_memory.ttl_seconds = 10   # 거의 비활성화

        self._logger.info(f"캐시 최적화 적용: {workflow_type}")


# 편의 함수들
def create_smart_cache_manager(workflow_type: str = "balanced") -> SmartCacheManager:
    """워크플로우별 최적화된 캐시 매니저 생성"""

    configs = {
        "live_trading": {
            'memory_cache': {'max_size': 500, 'ttl_seconds': 60},
            'disk_cache': {'cache_dir': 'data/cache/live', 'max_size_mb': 100, 'ttl_seconds': 300}
        },
        "backtesting": {
            'memory_cache': {'max_size': 2000, 'ttl_seconds': 600},
            'disk_cache': {'cache_dir': 'data/cache/backtest', 'max_size_mb': 1000, 'ttl_seconds': 7200}
        },
        "screening": {
            'memory_cache': {'max_size': 100, 'ttl_seconds': 10},
            'disk_cache': {'cache_dir': 'data/cache/screen', 'max_size_mb': 50, 'ttl_seconds': 300}
        },
        "balanced": {
            'memory_cache': {'max_size': 1000, 'ttl_seconds': 300},
            'disk_cache': {'cache_dir': 'data/cache', 'max_size_mb': 500, 'ttl_seconds': 3600}
        }
    }

    config = configs.get(workflow_type, configs["balanced"])
    cache_manager = SmartCacheManager(config)
    cache_manager.optimize_for_workflow(workflow_type)

    return cache_manager
