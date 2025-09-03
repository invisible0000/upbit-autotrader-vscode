# 🔄 Pending State 배치 처리 시스템 상세 가이드

> **WebSocket v6의 핵심 혁신: 중복 Task 제거 + 자연스러운 배치**

## 🎯 문제 정의

### **기존 시스템의 문제점**

```python
# 🚨 문제: 매번 새로운 Task 생성
def _on_subscription_change(self, changes: Dict) -> None:
    asyncio.create_task(self._handle_subscription_changes(changes))  # ← 매번!

# 🚨 결과: 중복 Task들이 동시에 Rate Limiter 대기
T=0   Task A → Rate Limiter 대기...
T=2   Task B → Rate Limiter 대기...  # 🚨 중복!
T=5   Task C → Rate Limiter 대기...  # 🚨 중복!
T=15  Task A, B, C 거의 동시 실행 → 중복 전송 🚨
```

### **핵심 문제들**

1. **Task 중복 생성**: 요청마다 새 Task → 리소스 낭비
2. **중복 전송**: 동일한 구독 상태를 여러 번 전송
3. **Rate Limiter 비효율**: N번 대기 → N×15초 소요
4. **Race Condition**: 동시 Task들이 같은 상태 읽어서 전송

## 💡 Pending State 해결 방안

### **핵심 아이디어: "하나의 Task로 모든 요청 통합"**

```python
# ✅ 해결책: Pending State 기반 단일 Task
def _on_subscription_change(self, changes: Dict) -> None:
    if not self._pending_subscription_task or self._pending_subscription_task.done():
        self._pending_subscription_task = asyncio.create_task(
            self._debounced_subscription_handler()
        )
    # 🎯 이미 실행 중이면 새 Task 생성 안 함!
```

### **동작 원리**

```python
# 🔄 Pending State 동작 흐름
T=0   요청 1 → pending_task == None → 새 Task 생성 ✅
T=2   요청 2 → pending_task.running → 생성 안 함 ✅
T=5   요청 3 → pending_task.running → 생성 안 함 ✅
T=15  Task 깨어남 → 최신 통합 상태 한 번에 전송 🚀
```

## 🛠️ 구현 상세

### **1️⃣ Pending Task 관리**

```python
class WebSocketManager:
    def __init__(self):
        # 🎯 Pending State 핵심 변수
        self._pending_subscription_task: Optional[asyncio.Task] = None
        self._debounce_delay: float = 0.1  # 100ms 디바운스

    def _on_subscription_change(self, changes: Dict) -> None:
        """구독 변경 콜백 (v6.1 Pending State)"""
        try:
            # 🎯 핵심 로직: Task 중복 방지
            if not self._pending_subscription_task or self._pending_subscription_task.done():
                self.logger.debug("📝 새로운 구독 변경 처리 Task 생성")
                self._pending_subscription_task = asyncio.create_task(
                    self._debounced_subscription_handler()
                )
            else:
                self.logger.debug("⏳ 이미 처리 중인 구독 Task 있음 - 자동 통합됨")

        except Exception as e:
            self.logger.error(f"구독 변경 콜백 실패: {e}")
```

### **2️⃣ 디바운스 핸들러**

```python
async def _debounced_subscription_handler(self) -> None:
    """디바운스된 구독 처리 (Pending State 핵심 로직)"""
    try:
        # 🔄 짧은 디바운스 대기 (추가 요청들을 모으기 위해)
        await asyncio.sleep(self._debounce_delay)

        self.logger.debug("🚀 통합된 구독 상태 전송 시작")

        # 📡 최신 통합 상태 기반으로 전송 (Rate Limiter 적용)
        await self._send_latest_subscriptions()

        self.logger.debug("✅ 구독 상태 전송 완료")

    except Exception as e:
        self.logger.error(f"디바운스된 구독 처리 실패: {e}")
    finally:
        # 🔄 Pending 상태 해제
        self._pending_subscription_task = None
```

### **3️⃣ 최신 상태 전송**

```python
async def _send_latest_subscriptions(self) -> None:
    """최신 구독 상태 전송 (Rate Limiter 적용)"""
    try:
        if not self._subscription_manager:
            return

        # 🎯 최신 통합 상태 조회 (항상 현재 시점의 상태)
        public_subs = self._subscription_manager.get_public_subscriptions()
        private_subs = self._subscription_manager.get_private_subscriptions()

        # 📤 Public 구독 처리
        if public_subs and self._connection_states[WebSocketType.PUBLIC] == ConnectionState.CONNECTED:
            await self._send_current_subscriptions(WebSocketType.PUBLIC)

        # 📤 Private 구독 처리
        if private_subs:
            await self._ensure_connection(WebSocketType.PRIVATE)
            await self._send_current_subscriptions(WebSocketType.PRIVATE)

    except Exception as e:
        self.logger.error(f"최신 구독 상태 전송 실패: {e}")
        raise
```

## 🔍 오묘한 시점 분석

### **시나리오: "Pending 중 + Rate Limiter 풀림 + 새 요청"**

```python
# 📊 타임라인 분석
T=0    컴포넌트A: ticker/KRW-BTC 구독
       └─ SubscriptionManager: 즉시 상태 통합 ✅
       └─ WebSocketManager: pending_task 생성
       └─ 디바운스 100ms 대기...

T=0.1  디바운스 완료, Rate Limiter 적용 시작...
       └─ await gate_websocket() 시작 (최대 15초 대기)

T=2    🎯 오묘한 시점 1: Rate Limiter 대기 중 새 요청
       └─ 컴포넌트B: ticker/KRW-ETH 구독
       └─ SubscriptionManager: 즉시 상태 통합 ✅ (BTC + ETH)
       └─ WebSocketManager: pending_task.done() == False
       └─ 새 Task 생성 안 함! ✅

T=5    🎯 오묘한 시점 2: 또 다른 요청
       └─ 컴포넌트C: orderbook/KRW-BTC 구독
       └─ SubscriptionManager: 즉시 상태 통합 ✅ (ticker:[BTC,ETH], orderbook:[BTC])
       └─ WebSocketManager: 여전히 pending_task 실행 중
       └─ 아무것도 안 함 ✅

T=15   🎯 오묘한 시점 3: Rate Limiter 풀림!
       └─ get_public_subscriptions() 호출
       └─ 최신 통합 상태 반환: ticker:[BTC,ETH], orderbook:[BTC] ✅
       └─ 모든 변경사항을 한 번에 전송! 🚀
       └─ pending_task = None (완료)
```

### **핵심 해결 포인트**

1. **실시간 통합**: SubscriptionManager가 즉시 상태 통합
2. **Task 단일화**: Pending 중에는 새 Task 생성 안 함
3. **최신 상태 보장**: Rate Limiter 해제 시 최신 상태만 전송
4. **자동 배치**: Rate Limiter가 자연스러운 배치 윈도우 역할

## 📊 성능 비교 분석

### **동시 요청 처리 성능**

| 요청 수 | 기존 시스템 | Pending State | 개선율 |
|---------|-------------|---------------|--------|
| 1개 | 15초 | 15초 | 1x |
| 5개 | 75초 | 15초 | 5x |
| 10개 | 150초 | 15초 | 10x |
| 100개 | 1500초 | 15초 | 100x |

### **메모리 사용량**

```python
# 📊 Task 메모리 사용량

# 기존 시스템 (N개 동시 요청):
Task 객체: N × 8KB = N × 8KB
콜백 참조: N × 1KB = N × 1KB
총 메모리: O(N × 9KB)

# Pending State 시스템:
Task 객체: 1 × 8KB = 8KB
통합 상태: 1 × 2KB = 2KB
총 메모리: O(10KB) ← 상수!
```

### **CPU 사용량**

```python
# 📊 CPU 사용 패턴

# 기존: N개 Task가 동시에 Rate Limiter 체크
CPU 스파이크: N번의 동시 처리

# Pending State: 1개 Task만 처리
CPU 사용량: 일정한 저부하
```

## 🛡️ 동시성 안전성

### **Race Condition 방지 매커니즘**

```python
# 🔒 1단계: SubscriptionManager Lock
async with self._lock:  # 원자적 상태 업데이트
    self._recalculate_subscriptions()
    changes = self._calculate_changes()
    await self._notify_changes(changes)

# 🔒 2단계: WebSocketManager Pending State
if not self._pending_subscription_task or self._pending_subscription_task.done():
    # 단 하나의 Task만 생성 보장

# 🔒 3단계: Rate Limiter 전역 제어
await gate_websocket()  # 전역 세마포어로 동시성 제어
```

### **메모리 일관성 보장**

```python
# ✅ 안전한 상태 읽기
def get_public_subscriptions(self) -> Dict[DataType, Set[str]]:
    return {
        data_type: active_sub.symbols.copy()  # ← 복사본 반환
        for data_type, active_sub in self._public_subscriptions.items()
    }
    # 🎯 항상 현재 시점의 일관된 상태 보장
```

## 🔧 설정 및 튜닝

### **핵심 매개변수**

```python
# 📐 디바운스 딜레이 (추가 요청 수집 시간)
_debounce_delay = 0.1  # 100ms

# 조정 가이드:
# - 요청 빈도 높음 → 값 낮춤 (50ms)
# - 요청 빈도 낮음 → 값 높임 (200ms)
# - 실시간성 중요 → 값 낮춤
# - 배치 효율 중요 → 값 높임
```

### **모니터링 지표**

```python
# 📊 핵심 모니터링 메트릭스
{
    'pending_task_created': 0,      # Pending Task 생성 횟수
    'pending_task_skipped': 0,      # Task 생성 스킵 횟수 (배치됨)
    'batch_efficiency': 0.85,       # 배치 효율성 (스킵률)
    'avg_batch_size': 3.2,         # 평균 배치 크기
    'rate_limiter_waits': 45,       # Rate Limiter 대기 횟수
    'duplicate_requests_prevented': 156  # 중복 요청 방지 횟수
}
```

## 🧪 테스트 시나리오

### **단위 테스트**

```python
async def test_pending_state_prevents_duplicate_tasks():
    """Pending State가 중복 Task 생성을 방지하는지 테스트"""
    manager = WebSocketManager()

    # 첫 번째 요청 → Task 생성
    manager._on_subscription_change({})
    task1 = manager._pending_subscription_task
    assert task1 is not None

    # 두 번째 요청 → Task 생성 안 함
    manager._on_subscription_change({})
    task2 = manager._pending_subscription_task
    assert task1 is task2  # 동일한 Task 객체
```

### **통합 테스트**

```python
async def test_concurrent_subscription_requests():
    """동시 구독 요청이 올바르게 배치되는지 테스트"""
    manager = await WebSocketManager.get_instance()

    # 동시에 10개 구독 요청
    tasks = []
    for i in range(10):
        task = asyncio.create_task(
            manager.register_component(f"comp_{i}", [spec])
        )
        tasks.append(task)

    # 모든 요청 완료 대기
    await asyncio.gather(*tasks)

    # 검증: 단일 WebSocket 메시지로 모든 구독 처리됨
    assert manager._rate_limit_stats['total_messages'] == 1  # 한 번만 전송
```

## 🎯 결론

### **Pending State 시스템의 핵심 혜택**

1. **🚀 성능**: N배 빠른 처리 (15초 vs N×15초)
2. **💾 메모리**: 상수 메모리 사용 (O(1) vs O(N))
3. **🛡️ 안정성**: Race Condition 완전 제거
4. **🎯 단순성**: 복잡한 배치 로직 제거

### **도입 성공 요소**

- **즉시 통합**: SubscriptionManager의 실시간 상태 통합
- **단일 Task**: Pending State로 중복 Task 완전 방지
- **자연스러운 배치**: Rate Limiter가 배치 윈도우 역할
- **안전한 상태 관리**: 원자적 업데이트 + 일관성 보장

**→ WebSocket v6의 Pending State는 단순하면서도 강력한 배치 처리 혁신! 🚀**
