"""
스토리지 성능 모니터링 및 통계 시스템
Smart Data Provider의 전체 스토리지 계층 성능을 종합적으로 모니터링하고 통계를 제공합니다.
"""
import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque, defaultdict
from enum import Enum
import statistics

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("StoragePerformanceMonitor")


class OperationType(Enum):
    """스토리지 작업 유형"""
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    CACHE_SET = "cache_set"
    CACHE_EVICTION = "cache_eviction"
    DB_QUERY = "db_query"
    DB_INSERT = "db_insert"
    API_REQUEST = "api_request"
    DATA_MERGE = "data_merge"
    CLEANUP = "cleanup"


class StorageLayer(Enum):
    """스토리지 계층"""
    MEMORY_CACHE = "memory_cache"
    SQLITE_CACHE = "sqlite_cache"
    SMART_ROUTER = "smart_router"
    UPBIT_API = "upbit_api"


@dataclass
class PerformanceMetric:
    """성능 지표"""
    operation_type: OperationType
    storage_layer: StorageLayer
    symbol: str
    duration_ms: float
    data_size_bytes: int
    record_count: int
    timestamp: datetime = field(default_factory=datetime.now)
    cache_hit: bool = False
    error: Optional[str] = None

    @property
    def throughput_records_per_ms(self) -> float:
        """레코드 처리량 (레코드/ms)"""
        return self.record_count / self.duration_ms if self.duration_ms > 0 else 0

    @property
    def throughput_mb_per_s(self) -> float:
        """데이터 처리량 (MB/s)"""
        mb_per_ms = (self.data_size_bytes / 1024 / 1024) / self.duration_ms if self.duration_ms > 0 else 0
        return mb_per_ms * 1000


class PerformanceWindow:
    """성능 지표 시간 윈도우"""

    def __init__(self, window_size_minutes: int = 5):
        self.window_size = timedelta(minutes=window_size_minutes)
        self.metrics: deque = deque()
        self._lock = threading.RLock()

    def add_metric(self, metric: PerformanceMetric) -> None:
        """지표 추가"""
        with self._lock:
            self.metrics.append(metric)
            self._cleanup_old_metrics()

    def _cleanup_old_metrics(self) -> None:
        """오래된 지표 정리"""
        cutoff_time = datetime.now() - self.window_size
        while self.metrics and self.metrics[0].timestamp < cutoff_time:
            self.metrics.popleft()

    def get_metrics_by_operation(self, operation_type: OperationType) -> List[PerformanceMetric]:
        """작업 유형별 지표 조회"""
        with self._lock:
            return [m for m in self.metrics if m.operation_type == operation_type]

    def get_metrics_by_layer(self, storage_layer: StorageLayer) -> List[PerformanceMetric]:
        """스토리지 계층별 지표 조회"""
        with self._lock:
            return [m for m in self.metrics if m.storage_layer == storage_layer]

    def get_metrics_by_symbol(self, symbol: str) -> List[PerformanceMetric]:
        """심볼별 지표 조회"""
        with self._lock:
            return [m for m in self.metrics if m.symbol == symbol]


@dataclass
class AggregatedStats:
    """집계된 통계"""
    operation_count: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    p95_duration_ms: float = 0.0
    success_rate: float = 100.0
    total_records: int = 0
    total_data_bytes: int = 0
    avg_throughput_records_per_ms: float = 0.0
    avg_throughput_mb_per_s: float = 0.0

    def update_from_metrics(self, metrics: List[PerformanceMetric]) -> None:
        """지표 리스트로부터 통계 업데이트"""
        if not metrics:
            return

        durations = [m.duration_ms for m in metrics]
        successful_operations = [m for m in metrics if not m.error]

        self.operation_count = len(metrics)
        self.total_duration_ms = sum(durations)
        self.avg_duration_ms = statistics.mean(durations)
        self.min_duration_ms = min(durations)
        self.max_duration_ms = max(durations)
        self.p95_duration_ms = statistics.quantiles(durations, n=20)[18] if len(durations) > 1 else durations[0]
        self.success_rate = (len(successful_operations) / len(metrics)) * 100
        self.total_records = sum(m.record_count for m in metrics)
        self.total_data_bytes = sum(m.data_size_bytes for m in metrics)

        # 처리량 계산
        throughputs_records = [m.throughput_records_per_ms for m in metrics if m.duration_ms > 0]
        throughputs_mb = [m.throughput_mb_per_s for m in metrics if m.duration_ms > 0]

        self.avg_throughput_records_per_ms = statistics.mean(throughputs_records) if throughputs_records else 0
        self.avg_throughput_mb_per_s = statistics.mean(throughputs_mb) if throughputs_mb else 0


class StoragePerformanceMonitor:
    """
    스토리지 성능 모니터

    전체 스토리지 계층의 성능을 실시간으로 모니터링하고 분석합니다.
    - 메모리 캐시 성능 추적
    - SQLite 캐시 성능 추적
    - Smart Router 성능 추적
    - 전체 응답 시간 분석
    - 캐시 효율성 분석
    """

    def __init__(self, window_size_minutes: int = 5):
        self.window_size_minutes = window_size_minutes
        self.performance_window = PerformanceWindow(window_size_minutes)

        # 계층별 통계
        self.layer_stats: Dict[StorageLayer, AggregatedStats] = {
            layer: AggregatedStats() for layer in StorageLayer
        }

        # 작업별 통계
        self.operation_stats: Dict[OperationType, AggregatedStats] = {
            op_type: AggregatedStats() for op_type in OperationType
        }

        # 심볼별 통계 (상위 N개만 추적)
        self.symbol_stats: Dict[str, AggregatedStats] = {}
        self.max_tracked_symbols = 50

        # 실시간 지표
        self.active_operations = 0
        self.total_operations = 0
        self.uptime_start = datetime.now()

        # 성능 임계값
        self.performance_thresholds = {
            OperationType.CACHE_HIT: 1.0,      # 1ms
            OperationType.CACHE_MISS: 50.0,    # 50ms
            OperationType.DB_QUERY: 100.0,     # 100ms
            OperationType.API_REQUEST: 1000.0, # 1초
        }

        # 경고 카운터
        self.slow_operation_count = 0
        self.error_count = 0

        self._lock = threading.RLock()

        logger.info(f"스토리지 성능 모니터 초기화 완료 - 윈도우: {window_size_minutes}분")

    # =====================================
    # 메트릭 기록
    # =====================================

    def record_operation(self,
                        operation_type: OperationType,
                        storage_layer: StorageLayer,
                        symbol: str,
                        duration_ms: float,
                        data_size_bytes: int = 0,
                        record_count: int = 0,
                        cache_hit: bool = False,
                        error: Optional[str] = None) -> None:
        """작업 성능 기록"""

        metric = PerformanceMetric(
            operation_type=operation_type,
            storage_layer=storage_layer,
            symbol=symbol,
            duration_ms=duration_ms,
            data_size_bytes=data_size_bytes,
            record_count=record_count,
            cache_hit=cache_hit,
            error=error
        )

        with self._lock:
            self.performance_window.add_metric(metric)
            self.total_operations += 1

            # 에러 및 느린 작업 카운팅
            if error:
                self.error_count += 1

            threshold = self.performance_thresholds.get(operation_type, 1000.0)
            if duration_ms > threshold:
                self.slow_operation_count += 1
                logger.warning(f"느린 작업 감지: {operation_type.value} on {storage_layer.value} "
                              f"for {symbol} took {duration_ms:.1f}ms (threshold: {threshold}ms)")

            # 통계 업데이트 (주기적으로)
            if self.total_operations % 100 == 0:
                self._update_aggregated_stats()

    def start_operation(self) -> int:
        """작업 시작 - 작업 ID 반환"""
        with self._lock:
            self.active_operations += 1
            return int(time.time() * 1000000)  # 마이크로초 기반 ID

    def end_operation(self, operation_id: int) -> float:
        """작업 종료 - 경과 시간(ms) 반환"""
        with self._lock:
            self.active_operations = max(0, self.active_operations - 1)
            current_time = int(time.time() * 1000000)
            return (current_time - operation_id) / 1000.0  # ms로 변환

    # =====================================
    # 편의 메서드
    # =====================================

    def record_cache_hit(self, symbol: str, duration_ms: float, data_size: int = 0) -> None:
        """캐시 히트 기록"""
        self.record_operation(
            OperationType.CACHE_HIT,
            StorageLayer.MEMORY_CACHE,
            symbol,
            duration_ms,
            data_size,
            cache_hit=True
        )

    def record_cache_miss(self, symbol: str, duration_ms: float) -> None:
        """캐시 미스 기록"""
        self.record_operation(
            OperationType.CACHE_MISS,
            StorageLayer.MEMORY_CACHE,
            symbol,
            duration_ms,
            cache_hit=False
        )

    def record_db_query(self, symbol: str, duration_ms: float, record_count: int = 0) -> None:
        """DB 쿼리 기록"""
        self.record_operation(
            OperationType.DB_QUERY,
            StorageLayer.SQLITE_CACHE,
            symbol,
            duration_ms,
            record_count=record_count
        )

    def record_api_request(self, symbol: str, duration_ms: float, record_count: int = 0, error: str = None) -> None:
        """API 요청 기록"""
        self.record_operation(
            OperationType.API_REQUEST,
            StorageLayer.UPBIT_API,
            symbol,
            duration_ms,
            record_count=record_count,
            error=error
        )

    # =====================================
    # 통계 업데이트
    # =====================================

    def _update_aggregated_stats(self) -> None:
        """집계 통계 업데이트"""
        try:
            # 계층별 통계 업데이트
            for layer in StorageLayer:
                metrics = self.performance_window.get_metrics_by_layer(layer)
                self.layer_stats[layer].update_from_metrics(metrics)

            # 작업별 통계 업데이트
            for op_type in OperationType:
                metrics = self.performance_window.get_metrics_by_operation(op_type)
                self.operation_stats[op_type].update_from_metrics(metrics)

            # 심볼별 통계 업데이트 (상위 심볼만)
            symbol_metrics = defaultdict(list)
            for metric in self.performance_window.metrics:
                symbol_metrics[metric.symbol].append(metric)

            # 활성도 기준 상위 심볼 선택
            top_symbols = sorted(
                symbol_metrics.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:self.max_tracked_symbols]

            self.symbol_stats.clear()
            for symbol, metrics in top_symbols:
                stats = AggregatedStats()
                stats.update_from_metrics(metrics)
                self.symbol_stats[symbol] = stats

        except Exception as e:
            logger.error(f"집계 통계 업데이트 실패: {e}")

    # =====================================
    # 성능 분석
    # =====================================

    def get_cache_efficiency(self) -> Dict[str, float]:
        """캐시 효율성 분석"""
        hit_metrics = self.performance_window.get_metrics_by_operation(OperationType.CACHE_HIT)
        miss_metrics = self.performance_window.get_metrics_by_operation(OperationType.CACHE_MISS)

        total_cache_operations = len(hit_metrics) + len(miss_metrics)
        hit_rate = (len(hit_metrics) / total_cache_operations * 100) if total_cache_operations > 0 else 0

        # 평균 응답 시간
        avg_hit_time = statistics.mean([m.duration_ms for m in hit_metrics]) if hit_metrics else 0
        avg_miss_time = statistics.mean([m.duration_ms for m in miss_metrics]) if miss_metrics else 0

        return {
            "hit_rate_percent": hit_rate,
            "miss_rate_percent": 100 - hit_rate,
            "avg_hit_time_ms": avg_hit_time,
            "avg_miss_time_ms": avg_miss_time,
            "cache_efficiency_score": hit_rate * (1 + max(0, 50 - avg_hit_time) / 50)  # 속도도 고려
        }

    def get_layer_performance_comparison(self) -> Dict[str, Dict[str, float]]:
        """계층별 성능 비교"""
        comparison = {}

        for layer in StorageLayer:
            stats = self.layer_stats[layer]
            comparison[layer.value] = {
                "avg_duration_ms": stats.avg_duration_ms,
                "p95_duration_ms": stats.p95_duration_ms,
                "success_rate": stats.success_rate,
                "operations_per_min": stats.operation_count / self.window_size_minutes,
                "avg_throughput_mb_per_s": stats.avg_throughput_mb_per_s
            }

        return comparison

    def get_bottleneck_analysis(self) -> Dict[str, Any]:
        """병목 지점 분석"""
        # 가장 느린 작업 유형
        slowest_operation = max(
            self.operation_stats.items(),
            key=lambda x: x[1].avg_duration_ms
        )[0] if self.operation_stats else None

        # 가장 오류가 많은 계층
        layer_error_rates = {}
        for layer in StorageLayer:
            metrics = self.performance_window.get_metrics_by_layer(layer)
            error_count = sum(1 for m in metrics if m.error)
            layer_error_rates[layer.value] = (error_count / len(metrics) * 100) if metrics else 0

        most_error_prone_layer = max(layer_error_rates.items(), key=lambda x: x[1])[0] if layer_error_rates else None

        # 가장 부하가 높은 심볼
        busiest_symbol = max(
            self.symbol_stats.items(),
            key=lambda x: x[1].operation_count
        )[0] if self.symbol_stats else None

        return {
            "slowest_operation": slowest_operation.value if slowest_operation else None,
            "most_error_prone_layer": most_error_prone_layer,
            "busiest_symbol": busiest_symbol,
            "total_slow_operations": self.slow_operation_count,
            "total_errors": self.error_count,
            "active_operations": self.active_operations
        }

    # =====================================
    # 종합 리포트
    # =====================================

    def get_comprehensive_report(self) -> Dict[str, Any]:
        """종합 성능 리포트"""
        uptime = datetime.now() - self.uptime_start

        return {
            "summary": {
                "uptime_minutes": uptime.total_seconds() / 60,
                "total_operations": self.total_operations,
                "active_operations": self.active_operations,
                "operations_per_minute": self.total_operations / (uptime.total_seconds() / 60) if uptime.total_seconds() > 0 else 0,
                "window_size_minutes": self.window_size_minutes
            },
            "cache_efficiency": self.get_cache_efficiency(),
            "layer_performance": self.get_layer_performance_comparison(),
            "bottleneck_analysis": self.get_bottleneck_analysis(),
            "top_symbols": {
                symbol: {
                    "operations": stats.operation_count,
                    "avg_duration_ms": stats.avg_duration_ms,
                    "success_rate": stats.success_rate
                }
                for symbol, stats in sorted(
                    self.symbol_stats.items(),
                    key=lambda x: x[1].operation_count,
                    reverse=True
                )[:10]
            }
        }

    def get_real_time_metrics(self) -> Dict[str, float]:
        """실시간 지표"""
        recent_metrics = [
            m for m in self.performance_window.metrics
            if (datetime.now() - m.timestamp).total_seconds() < 60
        ]

        if not recent_metrics:
            return {
                "recent_operations_per_min": 0.0,
                "recent_avg_duration_ms": 0.0,
                "recent_cache_hit_rate": 0.0,
                "recent_error_rate": 0.0
            }

        cache_hits = sum(1 for m in recent_metrics if m.cache_hit)
        errors = sum(1 for m in recent_metrics if m.error)

        return {
            "recent_operations_per_min": len(recent_metrics),
            "recent_avg_duration_ms": statistics.mean([m.duration_ms for m in recent_metrics]),
            "recent_cache_hit_rate": (cache_hits / len(recent_metrics) * 100),
            "recent_error_rate": (errors / len(recent_metrics) * 100)
        }

    # =====================================
    # 컨텍스트 매니저 (편의 기능)
    # =====================================

    def operation_timer(self, operation_type: OperationType, storage_layer: StorageLayer, symbol: str):
        """작업 타이머 컨텍스트 매니저"""
        class OperationTimer:
            def __init__(self, monitor, op_type, layer, sym):
                self.monitor = monitor
                self.operation_type = op_type
                self.storage_layer = layer
                self.symbol = sym
                self.start_time = None
                self.operation_id = None

            def __enter__(self):
                self.start_time = time.time()
                self.operation_id = self.monitor.start_operation()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                duration_ms = (time.time() - self.start_time) * 1000
                error = str(exc_val) if exc_val else None

                self.monitor.record_operation(
                    self.operation_type,
                    self.storage_layer,
                    self.symbol,
                    duration_ms,
                    error=error
                )
                self.monitor.end_operation(self.operation_id)

        return OperationTimer(self, operation_type, storage_layer, symbol)

    def __str__(self) -> str:
        report = self.get_comprehensive_report()
        summary = report["summary"]
        cache_eff = report["cache_efficiency"]

        return (f"StoragePerformanceMonitor("
                f"operations={summary['total_operations']}, "
                f"cache_hit_rate={cache_eff['hit_rate_percent']:.1f}%, "
                f"uptime={summary['uptime_minutes']:.1f}min)")


# 전역 성능 모니터 인스턴스 (싱글톤 패턴)
_global_monitor: Optional[StoragePerformanceMonitor] = None
_monitor_lock = threading.Lock()


def get_performance_monitor() -> StoragePerformanceMonitor:
    """전역 성능 모니터 인스턴스 반환"""
    global _global_monitor

    if _global_monitor is None:
        with _monitor_lock:
            if _global_monitor is None:
                _global_monitor = StoragePerformanceMonitor()

    return _global_monitor


def reset_performance_monitor() -> None:
    """성능 모니터 리셋 (테스트용)"""
    global _global_monitor
    with _monitor_lock:
        _global_monitor = None
