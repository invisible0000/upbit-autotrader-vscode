# 🔧 Event Handler 시스템 문제해결 가이드

> **목적**: Event Handler와 Notification 시스템 구현 시 발생할 수 있는 문제들과 해결 방법
> **대상**: 주니어 개발자, 디버깅 경험이 필요한 개발자
> **기반**: TASK-20250803-07 실제 문제해결 경험

## 🚨 자주 발생하는 문제들

### 1. 테스트 실패: 메서드명 불일치

#### 문제 상황
```bash
test_cache_invalidation_handler.py::test_invalidate_for_strategy_change - FAILED
AttributeError: 'CacheInvalidationService' object has no attribute 'invalidate_for_strategy_change'
```

#### 원인 분석
- **테스트 코드**에서는 `invalidate_for_strategy_change()` 메서드 호출
- **실제 구현체**에서는 `invalidate()` 메서드만 존재
- 메서드명 불일치로 인한 테스트 실패

#### 해결 방법
```python
# ❌ 문제 코드
class CacheInvalidationService:
    def invalidate(self, rule_name: str, context: Dict = None):
        # 통합 무효화 메서드만 존재
        pass

# ✅ 해결 코드 - 테스트 호환성 메서드 추가
class CacheInvalidationService:
    def invalidate(self, rule_name: str, context: Dict = None):
        # 기존 통합 메서드
        cache_keys = self.invalidation_rules.get(rule_name, [])
        self._invalidate_caches(cache_keys, context)

    def invalidate_for_strategy_change(self, strategy_id: str = None):
        """테스트 호환성을 위한 전략 변경 전용 메서드"""
        self.invalidate('strategy_changed', {'strategy_id': strategy_id})

    def invalidate_for_backtest_completion(self, strategy_id: str = None):
        """테스트 호환성을 위한 백테스팅 완료 전용 메서드"""
        self.invalidate('backtest_completed', {'strategy_id': strategy_id})
```

#### 교훈
- **테스트 코드와 구현체의 인터페이스 일치** 필수
- 리팩토링 시 **기존 테스트 호환성** 고려
- **Adapter 패턴**으로 인터페이스 불일치 해결

---

### 2. EventHandlerRegistry: Mock 등록 문제

#### 문제 상황
```bash
test_event_handler_registry.py::test_register_cache_invalidation_handler - FAILED
AssertionError: Expected CacheInvalidationHandler to be registered as global handler
```

#### 원인 분석
- **Mock 객체**의 `__class__.__name__`이 예상과 다름
- **클래스명 기반 감지 로직**이 Mock에서는 동작 안함

#### 문제 코드 분석
```python
# ❌ 문제가 있는 감지 로직
def register_handler(self, event_type, handler):
    if 'CacheInvalidation' in handler.__class__.__name__:
        self._global_handlers.append(handler)
    else:
        self._handlers[event_type].append(handler)

# 테스트에서 Mock 사용 시
mock_handler = Mock()
mock_handler.__class__.__name__  # "Mock" - CacheInvalidation 포함 안됨
```

#### 해결 방법 1: Mock 설정 개선
```python
# ✅ Mock 객체에 올바른 클래스명 설정
def test_register_cache_invalidation_handler():
    mock_handler = Mock()
    mock_handler.__class__.__name__ = "CacheInvalidationHandler"  # 명시적 설정

    registry = EventHandlerRegistry()
    registry.register_handler(None, mock_handler)

    assert len(registry._global_handlers) == 1
    assert mock_handler in registry._global_handlers
```

#### 해결 방법 2: 감지 로직 개선 (권장)
```python
# ✅ 더 견고한 감지 로직
def register_handler(self, event_type, handler):
    # 1. 클래스명 확인
    class_name = getattr(handler.__class__, '__name__', '')

    # 2. 특별한 속성 확인 (더 명확한 방법)
    is_global_handler = (
        'CacheInvalidation' in class_name or
        getattr(handler, '_is_global_handler', False)
    )

    if is_global_handler:
        self._global_handlers.append(handler)
        self.logger.info(f"글로벌 핸들러 등록: {class_name}")
    else:
        self._handlers[event_type].append(handler)
        self.logger.info(f"이벤트 핸들러 등록: {event_type.__name__} -> {class_name}")
```

#### 해결 방법 3: 명시적 인터페이스 (최고 방법)
```python
# ✅ 명시적 인터페이스로 완전 해결
class GlobalEventHandler(EventHandler):
    """모든 이벤트를 처리하는 전역 핸들러 마커 인터페이스"""
    pass

class CacheInvalidationHandler(GlobalEventHandler):
    """캐시 무효화 전역 핸들러"""
    pass

def register_handler(self, event_type, handler):
    if isinstance(handler, GlobalEventHandler):
        self._global_handlers.append(handler)
    else:
        self._handlers[event_type].append(handler)
```

---

### 3. 알림 채널별 메시지 포맷팅 오류

#### 문제 상황
```python
# UI Toast에 너무 긴 메시지 표시
"✅ 백테스팅이 성공적으로 완료되었습니다. 총 수익률: 15.3%, 최대 손실률: -8.2%, 샤프 비율: 1.84, 총 거래 수: 143회"
```

#### 원인 분석
- **채널별 특성** 무시한 동일한 메시지 전송
- **UI 제약사항** (Toast 30자, Status Bar 50자) 고려 안함

#### 해결 방법
```python
# ✅ 채널별 최적화된 메시지 포맷팅
def _format_message_for_channel(self, notification: Notification, channel: NotificationChannel) -> str:
    if channel == NotificationChannel.UI_TOAST:
        # Toast: 핵심 정보만 짧게 (30자 이내)
        icon = {"SUCCESS": "✅", "INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌"}
        return f"{icon.get(notification.type.name, '📝')} {notification.title}"

    elif channel == NotificationChannel.UI_STATUS_BAR:
        # Status Bar: 상태 + 핵심 지표 (50자 이내)
        status = notification.metadata.get('status', '')
        return f"📊 {notification.title[:20]} - {status}"

    elif channel == NotificationChannel.LOG_FILE:
        # Log: 상세 정보 포함
        metadata_str = ", ".join([f"{k}: {v}" for k, v in notification.metadata.items()])
        return f"📝 {notification.title}: {notification.message} [{metadata_str}]"

    else:  # SYSTEM_NOTIFICATION
        # System: 전체 메시지 + 메타데이터
        return f"🔔 {notification.title}\n{notification.message}\n상세정보: {notification.metadata}"
```

#### 채널별 최적화 가이드
| 채널 | 최대 길이 | 포맷 | 용도 |
|------|-----------|------|------|
| UI_TOAST | 30자 | `✅ 제목` | 즉각적 피드백 |
| UI_STATUS_BAR | 50자 | `📊 제목 - 상태` | 현재 상태 표시 |
| LOG_FILE | 제한없음 | `📝 제목: 메시지 [메타데이터]` | 디버깅/추적 |
| SYSTEM_NOTIFICATION | 200자 | `🔔 제목\n메시지\n상세정보` | 중요한 알림 |

---

### 4. 캐시 무효화 성능 문제

#### 문제 상황
```python
# 전략 생성할 때마다 모든 캐시를 무효화
def handle_strategy_created(self, event):
    self.cache_service.invalidate_all()  # ❌ 성능 문제
```

#### 원인 분석
- **과도한 캐시 무효화**로 성능 저하
- **불필요한 캐시 클리어**로 사용자 경험 악화

#### 해결 방법
```python
# ✅ 최적화된 캐시 무효화 전략
class CacheInvalidationService:
    def __init__(self):
        # 이벤트별 세밀한 무효화 규칙
        self.invalidation_rules = {
            'strategy_created': [
                'strategy_list_cache',          # 새 전략이 목록에 나타나야 함
                'dashboard_summary_cache'       # 총 전략 수 등 업데이트
                # ❌ strategy_performance_cache 제외 (아직 성과 없음)
            ],
            'strategy_updated': [
                'strategy_list_cache',          # 전략 정보 변경
                'strategy_performance_cache',   # 설정 변경으로 성과 영향
                'dashboard_summary_cache'
            ],
            'strategy_deleted': [
                'strategy_list_cache',
                'strategy_performance_cache',
                'dashboard_summary_cache',
                'active_strategies_cache'       # 활성 전략 목록에서 제거
            ]
        }

    def invalidate_smart(self, event_type: str, strategy_id: str = None):
        """스마트 캐시 무효화 - 필요한 것만"""
        rules = self.invalidation_rules.get(event_type, [])

        # 전략별 캐시 키 생성
        strategy_specific_keys = []
        if strategy_id:
            strategy_specific_keys = [
                f"strategy_detail_{strategy_id}",
                f"strategy_backtest_{strategy_id}"
            ]

        all_keys = rules + strategy_specific_keys
        self._invalidate_caches(all_keys)
```

#### 성능 최적화 팁
1. **세밀한 규칙**: 이벤트별 최소한의 캐시만 무효화
2. **전략별 캐시**: 특정 전략의 캐시만 무효화
3. **지연 무효화**: 즉시 무효화 대신 배치 처리
4. **조건부 무효화**: 실제 변경사항이 있을 때만 무효화

---

### 5. 이벤트 핸들러 순환 참조

#### 문제 상황
```python
# 이벤트 핸들러가 다시 이벤트를 발생시켜 무한 루프
class StrategyUpdatedHandler:
    def handle(self, event: StrategyUpdated):
        # 캐시 무효화 후 다시 전략 업데이트 이벤트 발생
        self.cache_service.invalidate_for_strategy_change()
        self.event_bus.publish(StrategyUpdated(...))  # ❌ 순환 참조!
```

#### 해결 방법
```python
# ✅ 이벤트 체인 추적으로 순환 방지
class EventHandlerRegistry:
    def __init__(self):
        self._processing_events: Set[str] = set()  # 현재 처리 중인 이벤트

    def publish_event(self, event: Any):
        event_id = f"{event.__class__.__name__}_{getattr(event, 'id', uuid.uuid4())}"

        if event_id in self._processing_events:
            self.logger.warning(f"순환 참조 감지, 이벤트 무시: {event_id}")
            return

        self._processing_events.add(event_id)
        try:
            # 실제 이벤트 처리
            self._handle_event(event)
        finally:
            self._processing_events.remove(event_id)

# ✅ 이벤트 레벨 구분으로 순환 방지
class DomainEvent:
    def __init__(self, level: int = 0):
        self.level = level  # 0: 원본, 1: 파생, 2: 2차 파생...
        self.max_level = 2  # 최대 2단계까지만 허용

class EventHandlerRegistry:
    def publish_event(self, event: DomainEvent):
        if event.level > event.max_level:
            self.logger.warning(f"이벤트 레벨 초과, 처리 중단: {event.level}")
            return

        # 파생 이벤트 생성 시 레벨 증가
        for derived_event in self._create_derived_events(event):
            derived_event.level = event.level + 1
            self.publish_event(derived_event)
```

---

### 6. 메모리 누수: 알림 히스토리 무제한 증가

#### 문제 상황
```python
class NotificationService:
    def __init__(self):
        self._history = []  # ❌ 무제한 증가

    def send_notification(self, notification):
        self._history.append(notification)  # 계속 누적
```

#### 해결 방법
```python
# ✅ 메모리 관리가 포함된 알림 서비스
class NotificationService:
    def __init__(self, max_history=1000, cleanup_interval=3600):
        self._history: List[Notification] = []
        self.max_history = max_history
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = time.time()

    def send_notification(self, notification: Notification):
        self._history.append(notification)

        # 정기적 메모리 정리
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_history()
            self.last_cleanup = current_time

    def _cleanup_history(self):
        """히스토리 정리: 크기 제한 + 오래된 항목 제거"""
        # 1. 크기 제한
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]

        # 2. 오래된 항목 제거 (7일 이상)
        cutoff_time = datetime.now() - timedelta(days=7)
        self._history = [
            n for n in self._history
            if n.timestamp > cutoff_time
        ]

        self.logger.info(f"알림 히스토리 정리 완료: {len(self._history)}개 유지")
```

---

## 🔍 디버깅 도구와 기법

### 1. 이벤트 추적 로깅
```python
class EventTracker:
    def __init__(self):
        self.event_trace = []

    def track_event(self, event, handler, result):
        trace_info = {
            'timestamp': datetime.now(),
            'event_type': event.__class__.__name__,
            'handler': handler.__class__.__name__,
            'result': result,
            'metadata': getattr(event, 'metadata', {})
        }
        self.event_trace.append(trace_info)

        # 실시간 디버깅 출력
        self.logger.debug(
            f"이벤트 추적: {trace_info['event_type']} -> {trace_info['handler']} "
            f"({trace_info['result']})"
        )
```

### 2. 성능 모니터링
```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = str(e)
            success = False
            raise
        finally:
            duration = time.time() - start_time
            logger.info(
                f"성능 모니터링: {func.__name__} "
                f"({duration:.3f}s, {'성공' if success else '실패'})"
            )
        return result
    return wrapper

class EventHandlerRegistry:
    @monitor_performance
    def publish_event(self, event):
        # 이벤트 처리 성능 자동 측정
        pass
```

### 3. 테스트 유틸리티
```python
class EventSystemTestUtils:
    @staticmethod
    def create_test_event(event_type, **kwargs):
        """테스트용 이벤트 생성"""
        return event_type(**kwargs)

    @staticmethod
    def assert_notification_sent(notification_service, title_pattern):
        """알림 전송 검증"""
        matching_notifications = [
            n for n in notification_service._history
            if title_pattern in n.title
        ]
        assert len(matching_notifications) > 0, f"알림 미발송: {title_pattern}"

    @staticmethod
    def assert_cache_invalidated(cache_service, cache_key_pattern):
        """캐시 무효화 검증"""
        # Mock을 통한 호출 검증 또는 실제 캐시 상태 확인
        pass
```

---

## 📊 성능 벤치마크

### 이벤트 처리 성능 기준
- **단순 이벤트**: 1ms 이내
- **복합 이벤트**: 5ms 이내
- **백테스팅 이벤트**: 10ms 이내
- **메모리 사용량**: 100MB 이내 (1만개 알림 기준)

### 성능 측정 스크립트
```python
# performance_test.py
def benchmark_event_system():
    registry = EventHandlerRegistry()
    notification_service = NotificationService()

    # 1000개 이벤트 처리 시간 측정
    start_time = time.time()
    for i in range(1000):
        event = StrategyCreated(f"strategy-{i}", f"전략 {i}")
        registry.publish_event(event)

    duration = time.time() - start_time
    avg_time = duration / 1000

    print(f"평균 이벤트 처리 시간: {avg_time:.3f}ms")
    print(f"메모리 사용량: {len(notification_service._history)}개 알림")
```

---

**💡 핵심 원칙**: "문제 발생 시 로그를 먼저 확인하고, 단계별로 격리하여 원인을 찾아라!"

**🎯 예방법**: "철저한 테스트 코드와 모니터링으로 문제를 사전에 차단하라!"
