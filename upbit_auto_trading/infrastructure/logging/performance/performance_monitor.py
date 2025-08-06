"""
Performance Monitoring System for LLM Agent Logging
성능 메트릭 수집 및 모니터링 시스템
"""
import time
import threading
import psutil
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import statistics


@dataclass
class PerformanceMetric:
    """성능 메트릭 정의"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    category: str
    threshold: Optional[float] = None
    status: str = "OK"  # OK, WARNING, CRITICAL


@dataclass
class SystemMetrics:
    """시스템 메트릭 스냅샷"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    thread_count: int
    file_descriptor_count: int


@dataclass
class PerformanceReport:
    """성능 리포트"""
    report_time: datetime
    duration_minutes: float
    system_metrics_summary: Dict[str, Any]
    logging_performance: Dict[str, Any]
    bottleneck_analysis: List[str]
    recommendations: List[str]


class PerformanceMonitor:
    """성능 모니터링 시스템"""

    def __init__(self,
                 monitoring_interval: float = 10.0,  # 10초마다 수집
                 history_size: int = 1000):

        self.monitoring_interval = monitoring_interval
        self.history_size = history_size

        # 모니터링 상태
        self.is_monitoring = False
        self.monitoring_thread = None

        # 메트릭 히스토리
        self.system_metrics_history: deque = deque(maxlen=history_size)
        self.custom_metrics: Dict[str, deque] = {}

        # 성능 임계값
        self.thresholds = {
            'cpu_percent': {'warning': 70.0, 'critical': 90.0},
            'memory_percent': {'warning': 80.0, 'critical': 95.0},
            'response_time_ms': {'warning': 1000.0, 'critical': 5000.0},
            'throughput_per_second': {'warning': 50.0, 'critical': 10.0}  # 최소 처리량
        }

        # 로깅 시스템 성능 메트릭
        self.logging_metrics = {
            'total_logs_processed': 0,
            'logs_per_second': deque(maxlen=60),  # 1분치 데이터
            'average_processing_time_ms': deque(maxlen=100),
            'error_count': 0,
            'queue_sizes': {},
            'cache_hit_rates': {}
        }

        # 프로세스 정보
        self.process = psutil.Process()
        self.initial_io_counters = None
        self.initial_net_counters = None

        # 커스텀 메트릭 콜백들
        self.metric_collectors: List[Callable[[], Dict[str, float]]] = []

    def start_monitoring(self):
        """성능 모니터링 시작"""
        if self.is_monitoring:
            return

        self.is_monitoring = True

        # 초기 카운터 설정
        try:
            self.initial_io_counters = self.process.io_counters()
            self.initial_net_counters = psutil.net_io_counters()
        except (psutil.AccessDenied, AttributeError):
            self.initial_io_counters = None
            self.initial_net_counters = None

        # 모니터링 스레드 시작
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="PerformanceMonitor"
        )
        self.monitoring_thread.start()
        print("📊 성능 모니터링 시작")

    def stop_monitoring(self):
        """성능 모니터링 중지"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)
        print("🛑 성능 모니터링 중지")

    def _monitoring_loop(self):
        """모니터링 루프"""
        while self.is_monitoring:
            try:
                # 시스템 메트릭 수집
                system_metrics = self._collect_system_metrics()
                self.system_metrics_history.append(system_metrics)

                # 커스텀 메트릭 수집
                self._collect_custom_metrics()

                # 임계값 체크
                self._check_thresholds(system_metrics)

                time.sleep(self.monitoring_interval)

            except Exception as e:
                print(f"❌ 성능 모니터링 오류: {e}")
                time.sleep(5.0)

    def _collect_system_metrics(self) -> SystemMetrics:
        """시스템 메트릭 수집"""
        try:
            # CPU 및 메모리
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            memory_mb = memory_info.rss / 1024 / 1024

            # I/O 통계
            disk_io_read_mb = 0
            disk_io_write_mb = 0
            if self.initial_io_counters:
                try:
                    current_io = self.process.io_counters()
                    disk_io_read_mb = (current_io.read_bytes - self.initial_io_counters.read_bytes) / 1024 / 1024
                    disk_io_write_mb = (current_io.write_bytes - self.initial_io_counters.write_bytes) / 1024 / 1024
                except (psutil.AccessDenied, AttributeError):
                    pass

            # 네트워크 통계
            network_sent_mb = 0
            network_recv_mb = 0
            if self.initial_net_counters:
                try:
                    current_net = psutil.net_io_counters()
                    network_sent_mb = (current_net.bytes_sent - self.initial_net_counters.bytes_sent) / 1024 / 1024
                    network_recv_mb = (current_net.bytes_recv - self.initial_net_counters.bytes_recv) / 1024 / 1024
                except AttributeError:
                    pass

            # 스레드 및 파일 디스크립터
            thread_count = self.process.num_threads()
            file_descriptor_count = 0
            try:
                file_descriptor_count = self.process.num_fds()
            except (psutil.AccessDenied, AttributeError):
                pass

            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_mb=memory_mb,
                disk_io_read_mb=disk_io_read_mb,
                disk_io_write_mb=disk_io_write_mb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                thread_count=thread_count,
                file_descriptor_count=file_descriptor_count
            )

        except Exception as e:
            print(f"❌ 시스템 메트릭 수집 실패: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0, memory_percent=0, memory_mb=0,
                disk_io_read_mb=0, disk_io_write_mb=0,
                network_sent_mb=0, network_recv_mb=0,
                thread_count=0, file_descriptor_count=0
            )

    def _collect_custom_metrics(self):
        """커스텀 메트릭 수집"""
        for collector in self.metric_collectors:
            try:
                metrics = collector()
                for name, value in metrics.items():
                    self.record_metric(name, value)
            except Exception as e:
                print(f"❌ 커스텀 메트릭 수집 실패: {e}")

    def _check_thresholds(self, metrics: SystemMetrics):
        """임계값 체크 및 알림"""
        alerts = []

        # CPU 체크
        cpu_thresholds = self.thresholds.get('cpu_percent', {})
        if metrics.cpu_percent > cpu_thresholds.get('critical', 100):
            alerts.append(f"🚨 CPU 사용률 임계: {metrics.cpu_percent:.1f}%")
        elif metrics.cpu_percent > cpu_thresholds.get('warning', 100):
            alerts.append(f"⚠️ CPU 사용률 높음: {metrics.cpu_percent:.1f}%")

        # 메모리 체크
        memory_thresholds = self.thresholds.get('memory_percent', {})
        if metrics.memory_percent > memory_thresholds.get('critical', 100):
            alerts.append(f"🚨 메모리 사용률 임계: {metrics.memory_percent:.1f}%")
        elif metrics.memory_percent > memory_thresholds.get('warning', 100):
            alerts.append(f"⚠️ 메모리 사용률 높음: {metrics.memory_percent:.1f}%")

        # 알림 출력
        for alert in alerts:
            print(alert)

    def record_metric(self, name: str, value: float, category: str = "custom"):
        """커스텀 메트릭 기록"""
        if name not in self.custom_metrics:
            self.custom_metrics[name] = deque(maxlen=self.history_size)

        metric = PerformanceMetric(
            name=name,
            value=value,
            unit="",
            timestamp=datetime.now(),
            category=category
        )

        self.custom_metrics[name].append(metric)

    def record_logging_performance(self, operation: str, duration_ms: float):
        """로깅 시스템 성능 기록"""
        if operation == "log_processing":
            self.logging_metrics['average_processing_time_ms'].append(duration_ms)

        # 처리량 계산
        current_time = time.time()
        self.logging_metrics['logs_per_second'].append((current_time, 1))

        # 1초 이전 데이터 제거
        cutoff_time = current_time - 1.0
        while (self.logging_metrics['logs_per_second'] and
               self.logging_metrics['logs_per_second'][0][0] < cutoff_time):
            self.logging_metrics['logs_per_second'].popleft()

    def add_metric_collector(self, collector: Callable[[], Dict[str, float]]):
        """메트릭 수집기 추가"""
        self.metric_collectors.append(collector)
        print(f"✅ 메트릭 수집기 추가됨: {collector.__name__}")

    def get_current_performance_summary(self) -> Dict[str, Any]:
        """현재 성능 요약"""
        if not self.system_metrics_history:
            return {"error": "No performance data available"}

        latest_metrics = self.system_metrics_history[-1]

        # 로깅 처리량 계산
        current_logs_per_second = len(self.logging_metrics['logs_per_second'])

        # 평균 처리 시간 계산
        avg_processing_time = 0
        if self.logging_metrics['average_processing_time_ms']:
            avg_processing_time = statistics.mean(self.logging_metrics['average_processing_time_ms'])

        return {
            "timestamp": latest_metrics.timestamp.isoformat(),
            "system": {
                "cpu_percent": latest_metrics.cpu_percent,
                "memory_percent": latest_metrics.memory_percent,
                "memory_mb": latest_metrics.memory_mb,
                "thread_count": latest_metrics.thread_count
            },
            "logging_performance": {
                "logs_per_second": current_logs_per_second,
                "average_processing_time_ms": round(avg_processing_time, 2),
                "total_logs_processed": self.logging_metrics['total_logs_processed'],
                "error_count": self.logging_metrics['error_count']
            },
            "status": self._get_overall_status(latest_metrics)
        }

    def _get_overall_status(self, metrics: SystemMetrics) -> str:
        """전체 상태 평가"""
        cpu_threshold = self.thresholds.get('cpu_percent', {})
        memory_threshold = self.thresholds.get('memory_percent', {})

        if (metrics.cpu_percent > cpu_threshold.get('critical', 100) or
            metrics.memory_percent > memory_threshold.get('critical', 100)):
            return "CRITICAL"

        if (metrics.cpu_percent > cpu_threshold.get('warning', 100) or
            metrics.memory_percent > memory_threshold.get('warning', 100)):
            return "WARNING"

        return "OK"

    def generate_performance_report(self, duration_hours: float = 1.0) -> PerformanceReport:
        """성능 리포트 생성"""
        cutoff_time = datetime.now() - timedelta(hours=duration_hours)

        # 기간 내 메트릭 필터링
        recent_metrics = [m for m in self.system_metrics_history if m.timestamp > cutoff_time]

        if not recent_metrics:
            return PerformanceReport(
                report_time=datetime.now(),
                duration_minutes=duration_hours * 60,
                system_metrics_summary={},
                logging_performance={},
                bottleneck_analysis=["데이터 부족"],
                recommendations=["모니터링 시간이 부족합니다"]
            )

        # 시스템 메트릭 요약
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]

        system_summary = {
            "cpu": {
                "average": round(statistics.mean(cpu_values), 2),
                "max": round(max(cpu_values), 2),
                "min": round(min(cpu_values), 2)
            },
            "memory": {
                "average": round(statistics.mean(memory_values), 2),
                "max": round(max(memory_values), 2),
                "min": round(min(memory_values), 2)
            }
        }

        # 로깅 성능 요약
        logging_performance = {
            "average_logs_per_second": len(self.logging_metrics['logs_per_second']),
            "total_processed": self.logging_metrics['total_logs_processed'],
            "error_rate": self.logging_metrics['error_count'] / max(self.logging_metrics['total_logs_processed'], 1)
        }

        # 병목 분석
        bottlenecks = self._analyze_bottlenecks(recent_metrics)

        # 추천 사항
        recommendations = self._generate_recommendations(recent_metrics)

        return PerformanceReport(
            report_time=datetime.now(),
            duration_minutes=duration_hours * 60,
            system_metrics_summary=system_summary,
            logging_performance=logging_performance,
            bottleneck_analysis=bottlenecks,
            recommendations=recommendations
        )

    def _analyze_bottlenecks(self, metrics: List[SystemMetrics]) -> List[str]:
        """병목 지점 분석"""
        bottlenecks = []

        if not metrics:
            return bottlenecks

        # CPU 병목
        high_cpu_count = sum(1 for m in metrics if m.cpu_percent > 80)
        if high_cpu_count > len(metrics) * 0.5:
            bottlenecks.append("CPU 사용률이 지속적으로 높습니다")

        # 메모리 병목
        high_memory_count = sum(1 for m in metrics if m.memory_percent > 80)
        if high_memory_count > len(metrics) * 0.3:
            bottlenecks.append("메모리 사용률이 높습니다")

        # 스레드 수 증가
        thread_counts = [m.thread_count for m in metrics]
        if thread_counts and max(thread_counts) > min(thread_counts) * 2:
            bottlenecks.append("스레드 수가 급격히 증가했습니다")

        return bottlenecks

    def _generate_recommendations(self, metrics: List[SystemMetrics]) -> List[str]:
        """성능 개선 추천 사항"""
        recommendations = []

        if not metrics:
            return recommendations

        avg_cpu = statistics.mean(m.cpu_percent for m in metrics)
        avg_memory = statistics.mean(m.memory_percent for m in metrics)

        if avg_cpu > 70:
            recommendations.append("비동기 처리를 증가시켜 CPU 부하를 분산하세요")

        if avg_memory > 70:
            recommendations.append("메모리 캐시 크기를 줄이고 가비지 컬렉션을 최적화하세요")

        # 로깅 성능 기반 추천
        if len(self.logging_metrics['logs_per_second']) < 10:
            recommendations.append("로그 처리 배치 크기를 늘려 처리량을 개선하세요")

        return recommendations

    def cleanup(self):
        """리소스 정리"""
        self.stop_monitoring()
        self.system_metrics_history.clear()
        self.custom_metrics.clear()
        print("✅ PerformanceMonitor 정리 완료")
