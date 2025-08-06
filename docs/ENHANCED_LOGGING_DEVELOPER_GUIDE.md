# LLM 에이전트 로깅 시스템 v4.0 개발자 가이드

## 🏗️ 아키텍처 개요

LLM 에이전트 로깅 시스템 v4.0은 3단계 Phase로 구성된 계층형 아키텍처를 사용합니다:

```
Phase 1: 기본 로깅 시스템 (Enhanced Core)
├── EnhancedLoggingConfig: 통합 설정 관리
├── SmartLoggingService: 확장된 로깅 서비스
└── ConfigurationManager: 동적 설정 관리

Phase 2: LLM 브리핑 & 대시보드 시스템
├── briefing/
│   ├── SystemStatusTracker: 실시간 컴포넌트 상태 추적
│   ├── IssueAnalyzer: 패턴 기반 문제 감지
│   └── LLMBriefingService: 마크다운 브리핑 생성
└── dashboard/
    ├── IssueDetector: 로그 기반 자동 문제 감지
    ├── RealtimeDashboard: JSON 대시보드 데이터 생성
    └── DashboardService: 대시보드 파일 관리

Phase 3: 성능 최적화 레이어
└── performance/
    ├── AsyncLogProcessor: 비동기 로그 처리
    ├── MemoryOptimizer: 메모리 사용량 최적화
    ├── CacheManager: 지능형 캐싱 시스템
    └── PerformanceMonitor: 성능 메트릭 수집
```

## 🔧 핵심 컴포넌트 API

### 1. SystemStatusTracker

시스템 컴포넌트의 상태를 실시간으로 추적합니다.

```python
from upbit_auto_trading.infrastructure.logging.briefing import SystemStatusTracker

# 초기화
tracker = SystemStatusTracker()

# 컴포넌트 상태 업데이트
tracker.update_component_status(
    component_name="DatabaseManager",
    status="OK",  # OK, WARNING, ERROR, LIMITED
    details="DB 연결 성공",
    metrics={"connection_time": 125, "pool_size": 10}
)

# 시스템 전체 건강도 확인
health = tracker.get_system_health()  # OK, WARNING, ERROR, CRITICAL

# 컴포넌트별 상태 조회
status = tracker.get_component_status("DatabaseManager")
```

#### ComponentStatus 데이터 구조

```python
@dataclass
class ComponentStatus:
    status: str          # OK, WARNING, ERROR, LIMITED
    details: str         # 상세 설명
    last_updated: datetime
    metrics: Dict[str, Any]  # 성능 메트릭
    issue_count: int     # 발생한 문제 수
    resolution_suggestions: List[str]  # 해결 제안
```

### 2. IssueAnalyzer

패턴 기반으로 시스템 문제를 자동 감지하고 분류합니다.

```python
from upbit_auto_trading.infrastructure.logging.briefing import IssueAnalyzer

analyzer = IssueAnalyzer()

# 시스템 상태에서 문제 분석
issues = analyzer.analyze_for_issues(status_tracker)

# 새로운 감지 패턴 추가
analyzer.add_detection_pattern(
    name="custom_error",
    pattern=r"CustomService.*failed",
    priority="MEDIUM",
    category="SERVICE",
    actions=["서비스 재시작", "로그 분석"],
    estimated_time=20
)
```

#### SystemIssue 데이터 구조

```python
@dataclass
class SystemIssue:
    id: str
    title: str
    description: str
    priority: str        # HIGH, MEDIUM, LOW
    category: str        # DI, UI, DB, Memory, Config
    affected_components: List[str]
    suggested_actions: List[str]
    estimated_time: int  # 예상 해결 시간 (분)
    detection_time: datetime
```

### 3. AsyncLogProcessor

비동기로 로그를 처리하여 메인 스레드 블로킹을 방지합니다.

```python
import asyncio
from upbit_auto_trading.infrastructure.logging.performance import AsyncLogProcessor
from upbit_auto_trading.infrastructure.logging.performance.async_processor import LogEntry

async def setup_async_logging():
    # 프로세서 초기화
    processor = AsyncLogProcessor(
        queue_size=10000,
        worker_count=3,
        batch_size=100
    )
    await processor.initialize()

    # 로그 처리 핸들러 추가
    def custom_handler(entry: LogEntry):
        print(f"[{entry.level}] {entry.component}: {entry.message}")

    processor.add_handler(custom_handler)

    # 로그 엔트리 추가
    entry = LogEntry(
        timestamp=datetime.now(),
        level="INFO",
        component="MyService",
        message="서비스 시작됨",
        metadata={"user_id": 123},
        priority=1
    )
    await processor.add_log_entry(entry)

    # 긴급 로그 (우선 처리)
    urgent_entry = LogEntry(
        timestamp=datetime.now(),
        level="ERROR",
        component="CriticalService",
        message="심각한 오류 발생",
        metadata={"error_code": "E001"},
        priority=5
    )
    await processor.add_log_entry(urgent_entry, force_priority=True)

    # 처리 완료 대기
    completed = await processor.wait_for_completion(timeout=5.0)

    return processor
```

### 4. CacheManager

지능형 캐싱 시스템으로 반복적인 연산을 최적화합니다.

```python
from upbit_auto_trading.infrastructure.logging.performance import CacheManager

# 캐시 매니저 초기화
cache_manager = CacheManager(cleanup_interval=300.0)
cache_manager.start_cleanup_thread()

# 캐시 등록
user_cache = cache_manager.register_cache(
    "user_data",
    max_size=1000,
    default_ttl=3600  # 1시간
)

# 캐시 사용
user_cache.put("user_123", {"name": "홍길동", "role": "admin"})
user_data = user_cache.get("user_123")

# 함수 결과 캐싱 데코레이터
@cache_manager.cached_function("expensive_calc", max_size=100, ttl=600)
def expensive_calculation(n: int) -> int:
    # 복잡한 계산
    time.sleep(1)  # 시뮬레이션
    return n * n

# 첫 번째 호출 (계산 실행)
result1 = expensive_calculation(10)  # 1초 소요

# 두 번째 호출 (캐시에서 반환)
result2 = expensive_calculation(10)  # 즉시 반환
```

### 5. MemoryOptimizer

메모리 사용량을 모니터링하고 최적화합니다.

```python
from upbit_auto_trading.infrastructure.logging.performance import MemoryOptimizer

# 메모리 최적화기 초기화
optimizer = MemoryOptimizer(
    memory_threshold_mb=500.0,
    gc_threshold_factor=2.0,
    monitoring_interval=30.0
)

# 모니터링 시작
optimizer.start_monitoring()

# 객체 추적 등록
my_object = {"large_data": "x" * 10000}
weak_ref = optimizer.track_object(my_object)

# 캐시 객체 등록
my_cache = {}
optimizer.register_cache(my_cache)

# 메모리 통계 확인
stats = optimizer.get_memory_stats()
print(f"현재 메모리: {stats['current_memory_mb']:.1f}MB")
print(f"추적 객체: {stats['tracked_objects']}개")

# 강제 가비지 컬렉션
collected = optimizer.force_garbage_collection()
print(f"정리된 객체: {sum(collected.values())}개")

# 정리
optimizer.cleanup()
```

### 6. PerformanceMonitor

시스템 성능 메트릭을 수집하고 분석합니다.

```python
from upbit_auto_trading.infrastructure.logging.performance import PerformanceMonitor

# 성능 모니터 초기화
monitor = PerformanceMonitor(
    monitoring_interval=10.0,
    history_size=1000
)

# 모니터링 시작
monitor.start_monitoring()

# 커스텀 메트릭 수집기 추가
def custom_metrics():
    return {
        "active_users": get_active_user_count(),
        "api_response_time": measure_api_response_time()
    }

monitor.add_metric_collector(custom_metrics)

# 로깅 성능 기록
monitor.record_logging_performance("log_processing", 25.5)  # ms

# 커스텀 메트릭 기록
monitor.record_metric("database_queries", 150, "database")

# 성능 요약
summary = monitor.get_current_performance_summary()

# 성능 리포트 생성
report = monitor.generate_performance_report(duration_hours=1.0)
```

## 🔌 통합 및 확장

### 새로운 문제 감지 패턴 추가

```python
# IssueAnalyzer에 새 패턴 등록
analyzer = IssueAnalyzer()

analyzer.ISSUE_PATTERNS["custom_service_failure"] = {
    'pattern': r'CustomService.*connection.*timeout',
    'priority': 'HIGH',
    'category': 'NETWORK',
    'actions': [
        '네트워크 연결 상태 확인',
        'CustomService 재시작',
        '타임아웃 설정 조정'
    ],
    'estimated_time': 25
}
```

### 커스텀 브리핑 포맷터 작성

```python
class CustomBriefingFormatter:
    def format_system_status(self, status_tracker):
        components = status_tracker.components
        healthy = sum(1 for c in components.values() if c.status == "OK")
        total = len(components)

        return f"### 시스템 상태: {healthy}/{total} 정상"

    def format_issues(self, issues):
        if not issues:
            return "### ✅ 감지된 문제 없음"

        high_priority = [i for i in issues if i.priority == "HIGH"]
        return f"### 🚨 긴급 문제: {len(high_priority)}개"

# LLMBriefingService에 커스텀 포맷터 사용
briefing_service = LLMBriefingService(config)
briefing_service.formatter = CustomBriefingFormatter()
```

### 성능 모니터링 커스터마이징

```python
class DatabasePerformanceCollector:
    def __init__(self, db_connection):
        self.db = db_connection

    def collect_metrics(self):
        return {
            "active_connections": self.db.get_active_connection_count(),
            "query_queue_size": self.db.get_query_queue_size(),
            "avg_query_time": self.db.get_average_query_time(),
            "cache_hit_rate": self.db.get_cache_hit_rate()
        }

# 성능 모니터에 등록
db_collector = DatabasePerformanceCollector(database)
monitor.add_metric_collector(db_collector.collect_metrics)
```

## 🧪 테스트 및 디버깅

### 단위 테스트 작성

```python
import pytest
from unittest.mock import Mock, patch
from upbit_auto_trading.infrastructure.logging.briefing import SystemStatusTracker

class TestSystemStatusTracker:
    def test_component_status_update(self):
        tracker = SystemStatusTracker()

        tracker.update_component_status("TestComponent", "OK", "정상 작동")

        status = tracker.get_component_status("TestComponent")
        assert status.status == "OK"
        assert status.details == "정상 작동"

    def test_system_health_calculation(self):
        tracker = SystemStatusTracker()

        tracker.update_component_status("Component1", "OK", "정상")
        tracker.update_component_status("Component2", "ERROR", "오류")

        health = tracker.get_system_health()
        assert health == "ERROR"

    @patch('datetime.datetime')
    def test_timestamp_tracking(self, mock_datetime):
        mock_now = Mock()
        mock_datetime.now.return_value = mock_now

        tracker = SystemStatusTracker()
        tracker.update_component_status("TestComponent", "OK", "테스트")

        status = tracker.get_component_status("TestComponent")
        assert status.last_updated == mock_now
```

### 통합 테스트 예제

```python
async def test_full_system_integration():
    # 모든 컴포넌트 초기화
    status_tracker = SystemStatusTracker()
    issue_analyzer = IssueAnalyzer()
    async_processor = AsyncLogProcessor()
    cache_manager = CacheManager()

    await async_processor.initialize()
    cache_manager.start_cleanup_thread()

    # 테스트 시나리오 실행
    status_tracker.update_component_status("TestService", "ERROR", "테스트 오류")

    issues = issue_analyzer.analyze_for_issues(status_tracker)
    assert len(issues) > 0

    # 로그 처리 테스트
    entry = LogEntry(
        timestamp=datetime.now(),
        level="ERROR",
        component="TestService",
        message="테스트 오류 발생",
        metadata={},
        priority=4
    )

    await async_processor.add_log_entry(entry)
    completed = await async_processor.wait_for_completion(timeout=2.0)
    assert completed

    # 정리
    await async_processor.shutdown()
    cache_manager.cleanup()
```

### 디버깅 도구

```python
# 디버그 모드 로깅 설정
import logging
logging.basicConfig(level=logging.DEBUG)

# 성능 프로파일링
import cProfile
import pstats

def profile_async_processing():
    profiler = cProfile.Profile()
    profiler.enable()

    # 비동기 처리 실행
    asyncio.run(test_async_processing())

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # 상위 10개 함수

# 메모리 사용량 추적
import tracemalloc

def trace_memory_usage():
    tracemalloc.start()

    # 테스트 코드 실행
    run_memory_intensive_operation()

    current, peak = tracemalloc.get_traced_memory()
    print(f"현재 메모리: {current / 1024 / 1024:.1f}MB")
    print(f"최대 메모리: {peak / 1024 / 1024:.1f}MB")

    tracemalloc.stop()
```

## 📊 모니터링 및 알림

### 실시간 모니터링 대시보드

```python
class RealTimeMonitoringDashboard:
    def __init__(self, status_tracker, performance_monitor):
        self.status_tracker = status_tracker
        self.performance_monitor = performance_monitor
        self.alert_handlers = []

    def add_alert_handler(self, handler):
        self.alert_handlers.append(handler)

    def check_system_health(self):
        health = self.status_tracker.get_system_health()
        performance = self.performance_monitor.get_current_performance_summary()

        if health in ["ERROR", "CRITICAL"]:
            alert = {
                "type": "SYSTEM_HEALTH",
                "severity": "HIGH",
                "message": f"시스템 상태가 {health}입니다",
                "timestamp": datetime.now(),
                "data": {
                    "system_health": health,
                    "performance": performance
                }
            }
            self._send_alert(alert)

    def _send_alert(self, alert):
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                print(f"알림 전송 실패: {e}")

# 사용 예제
dashboard = RealTimeMonitoringDashboard(status_tracker, performance_monitor)

def slack_alert_handler(alert):
    # Slack 웹훅으로 알림 전송
    send_slack_notification(alert)

def email_alert_handler(alert):
    # 이메일 알림 전송
    send_email_notification(alert)

dashboard.add_alert_handler(slack_alert_handler)
dashboard.add_alert_handler(email_alert_handler)
```

## 🚀 성능 최적화 팁

### 1. 비동기 처리 최적화

```python
# 배치 크기 조정
processor = AsyncLogProcessor(
    queue_size=20000,     # 큐 크기 증가
    worker_count=4,       # 워커 수 증가
    batch_size=200        # 배치 크기 증가
)

# 우선순위 기반 처리
high_priority_entry = LogEntry(
    # ... 기타 필드
    priority=5  # 최고 우선순위
)
await processor.add_log_entry(high_priority_entry, force_priority=True)
```

### 2. 메모리 사용량 최적화

```python
# 메모리 임계값 조정
optimizer = MemoryOptimizer(
    memory_threshold_mb=300.0,  # 더 낮은 임계값
    gc_threshold_factor=1.5,    # 더 자주 GC 실행
    monitoring_interval=15.0    # 더 자주 모니터링
)

# 대용량 객체 약한 참조 사용
import weakref
large_cache = {}
weak_cache_ref = weakref.ref(large_cache)
optimizer.register_cache(large_cache)
```

### 3. 캐시 최적화

```python
# 계층화된 캐시 구조
l1_cache = cache_manager.register_cache("l1_fast", max_size=100, default_ttl=60)
l2_cache = cache_manager.register_cache("l2_large", max_size=10000, default_ttl=3600)

def get_data_with_tiered_cache(key):
    # L1 캐시 확인
    data = l1_cache.get(key)
    if data is not None:
        return data

    # L2 캐시 확인
    data = l2_cache.get(key)
    if data is not None:
        l1_cache.put(key, data, ttl=60)  # L1에 복사
        return data

    # 실제 데이터 로드
    data = load_data_from_source(key)
    l1_cache.put(key, data, ttl=60)
    l2_cache.put(key, data, ttl=3600)
    return data
```

## 🔧 설정 관리

### 동적 설정 변경

```python
from upbit_auto_trading.infrastructure.logging.config import EnhancedLoggingConfig

# 설정 로드
config = EnhancedLoggingConfig.from_file("config/enhanced_logging.yaml")

# 런타임 설정 변경
config.briefing_update_interval = 15  # 15초로 변경
config.performance_monitoring_enabled = True
config.memory_threshold_mb = 400

# 설정 적용
logging_service = get_enhanced_logging_service(config)
```

### 환경별 설정

```yaml
# config/enhanced_logging.development.yaml
briefing:
  enabled: true
  update_interval: 10  # 개발환경에서는 더 자주 업데이트

performance:
  memory_threshold_mb: 200  # 개발환경에서는 낮은 임계값

# config/enhanced_logging.production.yaml
briefing:
  enabled: true
  update_interval: 60  # 운영환경에서는 덜 자주

performance:
  memory_threshold_mb: 1000  # 운영환경에서는 높은 임계값
```

---

이 개발자 가이드를 통해 LLM 에이전트 로깅 시스템 v4.0의 모든 기능을 효과적으로 활용하고 확장할 수 있습니다.
