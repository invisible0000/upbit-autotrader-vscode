"""
차트뷰어 리소스 모니터

기존 시스템과 격리된 차트뷰어 전용 리소스 모니터링 시스템입니다.
메모리, CPU, 네트워크 사용량을 모니터링하며, 기존 시스템에 영향을 주지 않습니다.

주요 기능:
- 차트뷰어 전용 리소스 모니터링
- 메모리 사용량 추적 (기존 시스템과 격리)
- 캐시 성능 모니터링
- 리소스 임계값 알림
- 자동 최적화 제안
"""

import time
import threading
import psutil
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import deque

from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass
class ResourceSnapshot:
    """리소스 스냅샷"""
    timestamp: float
    memory_mb: float
    cpu_percent: float
    cache_hits: int
    cache_misses: int
    active_connections: int
    data_throughput_mbps: float


@dataclass
class ResourceLimits:
    """리소스 한계값 (차트뷰어 전용)"""
    max_memory_mb: float = 256.0  # 차트뷰어 최대 메모리
    max_cpu_percent: float = 15.0  # 차트뷰어 최대 CPU
    max_cache_miss_ratio: float = 0.3  # 최대 캐시 미스율
    max_data_throughput_mbps: float = 10.0  # 최대 데이터 처리량


@dataclass
class PerformanceMetrics:
    """성능 지표"""
    avg_response_time_ms: float = 0.0
    cache_hit_ratio: float = 0.0
    memory_efficiency: float = 0.0
    cpu_efficiency: float = 0.0
    overall_score: float = 0.0


class ResourceMonitor:
    """
    차트뷰어 리소스 모니터

    기존 시스템과 격리된 차트뷰어 전용 리소스 모니터링 시스템입니다.
    메모리, CPU, 캐시 성능 등을 모니터링하여 최적화 제안을 제공합니다.
    """

    def __init__(self, monitoring_interval: int = 5, history_size: int = 1000):
        """
        Args:
            monitoring_interval: 모니터링 간격 (초)
            history_size: 유지할 히스토리 개수
        """
        self.logger = create_component_logger("ResourceMonitor")

        # 모니터링 설정
        self._monitoring_interval = monitoring_interval
        self._history_size = history_size

        # 리소스 한계값 (차트뷰어 전용)
        self._limits = ResourceLimits()

        # 히스토리 저장 (deque로 효율적 관리)
        self._resource_history: deque[ResourceSnapshot] = deque(maxlen=history_size)

        # 실시간 상태
        self._current_snapshot: Optional[ResourceSnapshot] = None
        self._performance_metrics = PerformanceMetrics()

        # 모니터링 스레드
        self._monitoring_thread: Optional[threading.Thread] = None
        self._is_monitoring = False
        self._lock = threading.RLock()

        # 알림 콜백
        self._alert_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []

        # 차트뷰어 전용 메트릭스
        self._chart_metrics = {
            'render_count': 0,
            'render_time_total': 0.0,
            'data_points_processed': 0,
            'cache_operations': 0,
            'last_optimization': None
        }

        self.logger.info(
            f"차트뷰어 리소스 모니터 초기화: "
            f"모니터링 간격 {monitoring_interval}초, 히스토리 {history_size}개 "
            f"(기존 시스템과 격리)"
        )

    def start_monitoring(self) -> None:
        """리소스 모니터링 시작"""
        if self._is_monitoring:
            self.logger.warning("리소스 모니터링이 이미 실행 중입니다")
            return

        try:
            self._is_monitoring = True

            # 모니터링 스레드 시작
            self._monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                name="ChartViewerResourceMonitor",
                daemon=True
            )
            self._monitoring_thread.start()

            self.logger.info("차트뷰어 리소스 모니터링 시작")

        except Exception as e:
            self.logger.error(f"리소스 모니터링 시작 실패: {e}")
            self._is_monitoring = False

    def stop_monitoring(self) -> None:
        """리소스 모니터링 중지"""
        if not self._is_monitoring:
            return

        try:
            self._is_monitoring = False

            # 모니터링 스레드 종료 대기
            if self._monitoring_thread and self._monitoring_thread.is_alive():
                self._monitoring_thread.join(timeout=5.0)

            self.logger.info("차트뷰어 리소스 모니터링 중지")

        except Exception as e:
            self.logger.error(f"리소스 모니터링 중지 실패: {e}")

    def _monitoring_loop(self) -> None:
        """모니터링 루프 (백그라운드 스레드)"""
        self.logger.debug("리소스 모니터링 루프 시작")

        while self._is_monitoring:
            try:
                # 리소스 스냅샷 생성
                snapshot = self._create_resource_snapshot()

                with self._lock:
                    # 히스토리에 추가
                    self._resource_history.append(snapshot)
                    self._current_snapshot = snapshot

                    # 성능 지표 업데이트
                    self._update_performance_metrics()

                    # 임계값 확인 및 알림
                    self._check_thresholds(snapshot)

                # 주기적 최적화 제안
                if len(self._resource_history) % 10 == 0:  # 10회마다
                    self._generate_optimization_suggestions()

                # 다음 모니터링까지 대기
                time.sleep(self._monitoring_interval)

            except Exception as e:
                self.logger.error(f"모니터링 루프 오류: {e}")
                time.sleep(self._monitoring_interval)

        self.logger.debug("리소스 모니터링 루프 종료")

    def _create_resource_snapshot(self) -> ResourceSnapshot:
        """현재 리소스 상태 스냅샷 생성"""
        try:
            # 현재 프로세스 정보
            process = psutil.Process()

            # 메모리 사용량 (차트뷰어 전용 추정)
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            # CPU 사용률 (차트뷰어 전용 추정)
            cpu_percent = process.cpu_percent(interval=0.1)

            # 캐시 메트릭스 (외부에서 업데이트됨)
            cache_hits = self._chart_metrics.get('cache_hits', 0)
            cache_misses = self._chart_metrics.get('cache_misses', 0)

            # 네트워크 연결 수 (추정)
            active_connections = len(process.connections())

            # 데이터 처리량 (추정)
            data_throughput = self._chart_metrics.get('data_throughput_mbps', 0.0)

            return ResourceSnapshot(
                timestamp=time.time(),
                memory_mb=memory_mb,
                cpu_percent=cpu_percent,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                active_connections=active_connections,
                data_throughput_mbps=data_throughput
            )

        except Exception as e:
            self.logger.error(f"리소스 스냅샷 생성 실패: {e}")
            return ResourceSnapshot(
                timestamp=time.time(),
                memory_mb=0.0,
                cpu_percent=0.0,
                cache_hits=0,
                cache_misses=0,
                active_connections=0,
                data_throughput_mbps=0.0
            )

    def _update_performance_metrics(self) -> None:
        """성능 지표 업데이트"""
        try:
            if len(self._resource_history) < 2:
                return

            # 최근 데이터로 지표 계산
            recent_snapshots = list(self._resource_history)[-10:]  # 최근 10개

            # 캐시 히트율
            total_hits = sum(s.cache_hits for s in recent_snapshots)
            total_misses = sum(s.cache_misses for s in recent_snapshots)
            total_requests = total_hits + total_misses

            if total_requests > 0:
                self._performance_metrics.cache_hit_ratio = total_hits / total_requests

            # 메모리 효율성 (사용량 대비 성능)
            avg_memory = sum(s.memory_mb for s in recent_snapshots) / len(recent_snapshots)
            memory_efficiency = min(1.0, self._limits.max_memory_mb / max(avg_memory, 1.0))
            self._performance_metrics.memory_efficiency = memory_efficiency

            # CPU 효율성
            avg_cpu = sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots)
            cpu_efficiency = max(0.0, 1.0 - (avg_cpu / self._limits.max_cpu_percent))
            self._performance_metrics.cpu_efficiency = cpu_efficiency

            # 응답 시간 (차트 렌더링 시간 기준)
            if self._chart_metrics['render_count'] > 0:
                avg_render_time = (
                    self._chart_metrics['render_time_total'] /
                    self._chart_metrics['render_count']
                )
                self._performance_metrics.avg_response_time_ms = avg_render_time

            # 종합 점수 계산
            scores = [
                self._performance_metrics.cache_hit_ratio,
                memory_efficiency,
                cpu_efficiency,
                min(1.0, 100.0 / max(self._performance_metrics.avg_response_time_ms, 1.0))
            ]
            self._performance_metrics.overall_score = sum(scores) / len(scores)

        except Exception as e:
            self.logger.error(f"성능 지표 업데이트 실패: {e}")

    def _check_thresholds(self, snapshot: ResourceSnapshot) -> None:
        """임계값 확인 및 알림"""
        try:
            alerts = []

            # 메모리 사용량 확인
            if snapshot.memory_mb > self._limits.max_memory_mb:
                alerts.append({
                    'type': 'memory_high',
                    'message': f'메모리 사용량 초과: {snapshot.memory_mb:.1f}MB > {self._limits.max_memory_mb}MB',
                    'current': snapshot.memory_mb,
                    'limit': self._limits.max_memory_mb,
                    'severity': 'warning'
                })

            # CPU 사용률 확인
            if snapshot.cpu_percent > self._limits.max_cpu_percent:
                alerts.append({
                    'type': 'cpu_high',
                    'message': f'CPU 사용률 초과: {snapshot.cpu_percent:.1f}% > {self._limits.max_cpu_percent}%',
                    'current': snapshot.cpu_percent,
                    'limit': self._limits.max_cpu_percent,
                    'severity': 'warning'
                })

            # 캐시 미스율 확인
            if snapshot.cache_hits + snapshot.cache_misses > 0:
                miss_ratio = snapshot.cache_misses / (snapshot.cache_hits + snapshot.cache_misses)
                if miss_ratio > self._limits.max_cache_miss_ratio:
                    alerts.append({
                        'type': 'cache_miss_high',
                        'message': f'캐시 미스율 높음: {miss_ratio:.2f} > {self._limits.max_cache_miss_ratio:.2f}',
                        'current': miss_ratio,
                        'limit': self._limits.max_cache_miss_ratio,
                        'severity': 'info'
                    })

            # 알림 발송
            for alert in alerts:
                self._send_alert(alert['type'], alert)

        except Exception as e:
            self.logger.error(f"임계값 확인 실패: {e}")

    def _send_alert(self, alert_type: str, alert_data: Dict[str, Any]) -> None:
        """알림 발송"""
        try:
            # 로그 기록
            severity = alert_data.get('severity', 'info')
            message = alert_data.get('message', '')

            if severity == 'warning':
                self.logger.warning(f"리소스 알림: {message}")
            else:
                self.logger.info(f"리소스 알림: {message}")

            # 등록된 콜백 호출
            for callback in self._alert_callbacks:
                try:
                    callback(alert_type, alert_data)
                except Exception as e:
                    self.logger.error(f"알림 콜백 실행 실패: {e}")

        except Exception as e:
            self.logger.error(f"알림 발송 실패: {e}")

    def _generate_optimization_suggestions(self) -> None:
        """최적화 제안 생성"""
        try:
            if len(self._resource_history) < 10:
                return

            suggestions = []
            recent_snapshots = list(self._resource_history)[-20:]  # 최근 20개

            # 메모리 사용량 분석
            avg_memory = sum(s.memory_mb for s in recent_snapshots) / len(recent_snapshots)
            if avg_memory > self._limits.max_memory_mb * 0.8:
                suggestions.append({
                    'type': 'memory_optimization',
                    'message': '메모리 사용량이 높습니다. 캐시 크기를 줄이거나 정리 주기를 단축하세요.',
                    'priority': 'high'
                })

            # 캐시 성능 분석
            if self._performance_metrics.cache_hit_ratio < 0.7:
                suggestions.append({
                    'type': 'cache_optimization',
                    'message': '캐시 히트율이 낮습니다. 캐시 크기를 늘리거나 전략을 조정하세요.',
                    'priority': 'medium'
                })

            # CPU 사용률 분석
            avg_cpu = sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots)
            if avg_cpu > self._limits.max_cpu_percent * 0.8:
                suggestions.append({
                    'type': 'cpu_optimization',
                    'message': 'CPU 사용률이 높습니다. 렌더링 빈도를 줄이거나 최적화하세요.',
                    'priority': 'medium'
                })

            # 제안사항 로그 기록
            if suggestions:
                self.logger.info(f"최적화 제안 {len(suggestions)}개 생성")
                for suggestion in suggestions:
                    self.logger.info(f"  - {suggestion['message']} (우선순위: {suggestion['priority']})")

                self._chart_metrics['last_optimization'] = datetime.now()

        except Exception as e:
            self.logger.error(f"최적화 제안 생성 실패: {e}")

    def update_chart_metrics(self, metrics: Dict[str, Any]) -> None:
        """차트 메트릭스 업데이트 (외부에서 호출)"""
        try:
            with self._lock:
                for key, value in metrics.items():
                    if key in self._chart_metrics:
                        if key.endswith('_total') or key.endswith('_count'):
                            self._chart_metrics[key] += value
                        else:
                            self._chart_metrics[key] = value
                    else:
                        self._chart_metrics[key] = value

        except Exception as e:
            self.logger.error(f"차트 메트릭스 업데이트 실패: {e}")

    def add_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """알림 콜백 등록"""
        self._alert_callbacks.append(callback)
        self.logger.debug("알림 콜백 등록됨")

    def remove_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """알림 콜백 제거"""
        if callback in self._alert_callbacks:
            self._alert_callbacks.remove(callback)
            self.logger.debug("알림 콜백 제거됨")

    def get_current_status(self) -> Dict[str, Any]:
        """현재 리소스 상태 조회"""
        with self._lock:
            if not self._current_snapshot:
                return {'status': 'no_data'}

            return {
                'status': 'active',
                'timestamp': self._current_snapshot.timestamp,
                'memory_mb': self._current_snapshot.memory_mb,
                'cpu_percent': self._current_snapshot.cpu_percent,
                'cache_hits': self._current_snapshot.cache_hits,
                'cache_misses': self._current_snapshot.cache_misses,
                'active_connections': self._current_snapshot.active_connections,
                'data_throughput_mbps': self._current_snapshot.data_throughput_mbps,
                'performance_metrics': asdict(self._performance_metrics),
                'limits': asdict(self._limits),
                'is_monitoring': self._is_monitoring
            }

    def get_history(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """히스토리 데이터 조회"""
        try:
            with self._lock:
                if not self._resource_history:
                    return []

                # 지정된 시간 범위의 데이터만 반환
                cutoff_time = time.time() - (minutes * 60)
                filtered_history = [
                    asdict(snapshot) for snapshot in self._resource_history
                    if snapshot.timestamp >= cutoff_time
                ]

                return filtered_history

        except Exception as e:
            self.logger.error(f"히스토리 조회 실패: {e}")
            return []

    def get_resource_summary(self) -> Dict[str, Any]:
        """리소스 사용량 요약"""
        try:
            with self._lock:
                if not self._resource_history:
                    return {'status': 'no_data'}

                recent_snapshots = list(self._resource_history)[-20:]  # 최근 20개

                # 평균값 계산
                avg_memory = sum(s.memory_mb for s in recent_snapshots) / len(recent_snapshots)
                avg_cpu = sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots)

                # 최대값 계산
                max_memory = max(s.memory_mb for s in recent_snapshots)
                max_cpu = max(s.cpu_percent for s in recent_snapshots)

                # 사용률 계산
                memory_usage_percent = (avg_memory / self._limits.max_memory_mb) * 100
                cpu_usage_percent = (avg_cpu / self._limits.max_cpu_percent) * 100

                return {
                    'status': 'active',
                    'summary': {
                        'avg_memory_mb': round(avg_memory, 2),
                        'max_memory_mb': round(max_memory, 2),
                        'memory_usage_percent': round(memory_usage_percent, 1),
                        'avg_cpu_percent': round(avg_cpu, 2),
                        'max_cpu_percent': round(max_cpu, 2),
                        'cpu_usage_percent': round(cpu_usage_percent, 1),
                        'cache_hit_ratio': round(self._performance_metrics.cache_hit_ratio, 3),
                        'overall_score': round(self._performance_metrics.overall_score, 3)
                    },
                    'health_status': self._get_health_status(memory_usage_percent, cpu_usage_percent),
                    'chart_metrics': self._chart_metrics.copy()
                }

        except Exception as e:
            self.logger.error(f"리소스 요약 조회 실패: {e}")
            return {'status': 'error', 'message': str(e)}

    def _get_health_status(self, memory_usage: float, cpu_usage: float) -> str:
        """전체 시스템 건강 상태 평가"""
        if memory_usage > 90 or cpu_usage > 90:
            return 'critical'
        elif memory_usage > 80 or cpu_usage > 80:
            return 'warning'
        elif memory_usage > 60 or cpu_usage > 60:
            return 'caution'
        else:
            return 'healthy'

    def set_limits(self, limits: Dict[str, float]) -> None:
        """리소스 한계값 설정"""
        try:
            for key, value in limits.items():
                if hasattr(self._limits, key):
                    setattr(self._limits, key, value)
                    self.logger.info(f"리소스 한계값 업데이트: {key} = {value}")
                else:
                    self.logger.warning(f"알 수 없는 한계값: {key}")

        except Exception as e:
            self.logger.error(f"리소스 한계값 설정 실패: {e}")

    def shutdown(self) -> None:
        """리소스 모니터 종료"""
        try:
            self.stop_monitoring()

            # 히스토리 정리
            self._resource_history.clear()
            self._alert_callbacks.clear()

            self.logger.info("차트뷰어 리소스 모니터 종료 완료")

        except Exception as e:
            self.logger.error(f"리소스 모니터 종료 실패: {e}")

    def __del__(self):
        """소멸자"""
        if hasattr(self, '_is_monitoring') and self._is_monitoring:
            self.shutdown()
