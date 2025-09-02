# WebSocket v6 Rate Limit 인식 배치 처리 시스템
> 전역 Rate Limiter 대안으로 개발된 고급 구독 관리 시스템

---

## 📋 개요

WebSocket v6에서 개발된 **Rate Limit 인식 배치 처리 시스템**은 업비트의 WebSocket 구독 제한(초당 5개)을 효율적으로 관리하기 위한 고급 기능입니다. 현재는 전역 Rate Limiter를 사용하므로 비활성화되었지만, 향후 필요시 재활용할 수 있도록 상세한 구현 내용을 문서화합니다.

---

## 🎯 핵심 개념

### 배치 처리 아키텍처
```
구독 요청들 → 배치 큐 → 200ms 대기 → Rate Limit 검사 → 일괄 처리
     ↓           ↓          ↓            ↓             ↓
   실시간      우선순위    지연 처리    안전성 확보   효율성 극대화
```

### Rate Limit 관리 전략
- **배치 윈도우**: 200ms마다 처리
- **최대 배치 크기**: 5개 (업비트 제한 준수)
- **우선순위 기반**: 해제 > 등록 순서
- **스마트 분할**: 큰 배치를 자동 분할

---

## 🏗️ 핵심 컴포넌트

### 1. SubscriptionBatch 클래스
```python
@dataclass
class SubscriptionBatch:
    """Rate Limit을 고려한 구독 배치"""
    changes: Dict[DataType, SubscriptionChange] = field(default_factory=dict)
    queued_at: float = field(default_factory=time.time)
    priority: int = 0  # 높을수록 우선순위 높음

    def get_total_changes(self) -> int:
        """총 변경 항목 수 (Rate Limit 계산용)"""
        return sum(
            len(change.added_symbols) + len(change.removed_symbols)
            for change in self.changes.values()
        )
```

**특징:**
- 여러 DataType의 변경사항을 하나의 배치로 통합
- 우선순위 기반 처리 (해제 작업이 높은 우선순위)
- Rate Limit 계산을 위한 변경 항목 수 자동 집계

### 2. 배치 처리 엔진
```python
# 핵심 변수들
self._pending_batches: List[SubscriptionBatch] = []
self._batch_processing_task: Optional[asyncio.Task] = None
self._max_batch_size: int = 5  # 업비트 WebSocket 초당 5개 구독 제한
self._batch_window_ms: int = 200  # 200ms 대기 후 배치 처리
```

**주요 메서드:**
- `start_batch_processor()`: 백그라운드 배치 처리 시작
- `_batch_processing_loop()`: 200ms 주기로 배치 처리
- `_process_pending_batches()`: Rate Limit 내에서 배치 선택 및 처리
- `_execute_batches()`: 선택된 배치들의 실제 실행

---

## ⚙️ 상세 동작 흐름

### 1. 구독 요청 수집 단계
```
컴포넌트A: ticker/KRW-BTC 구독 요청
           ↓
배치 생성: SubscriptionBatch(priority=0)
           ↓
큐에 추가: _pending_batches.append(batch)
```

### 2. 배치 처리 루프 (200ms 주기)
```python
async def _batch_processing_loop(self) -> None:
    while True:
        await asyncio.sleep(0.2)  # 200ms 대기

        if self._pending_batches:
            await self._process_pending_batches()
```

### 3. Rate Limit 인식 배치 선택
```python
async def _process_pending_batches(self) -> None:
    # 1. 우선순위 정렬
    self._pending_batches.sort(key=lambda b: b.priority, reverse=True)

    # 2. Rate Limit 내에서 처리 가능한 배치 선택
    processable_batches = []
    total_changes = 0

    for batch in self._pending_batches[:]:
        batch_changes = batch.get_total_changes()
        if total_changes + batch_changes <= 5:  # 업비트 제한
            processable_batches.append(batch)
            total_changes += batch_changes
        else:
            break  # Rate Limit 도달

    # 3. 선택된 배치들 실행
    await self._execute_batches(processable_batches)
```

### 4. 배치 통합 및 실행
```python
async def _execute_batches(self, batches: List[SubscriptionBatch]) -> None:
    # 모든 배치의 변경사항을 통합
    consolidated_changes = {}

    for batch in batches:
        for data_type, change in batch.changes.items():
            if data_type not in consolidated_changes:
                consolidated_changes[data_type] = SubscriptionChange()

            # 변경사항 병합
            consolidated_changes[data_type].added_symbols.update(change.added_symbols)
            consolidated_changes[data_type].removed_symbols.update(change.removed_symbols)

    # 중복 제거 (추가와 제거가 동시에 있는 경우)
    for change in consolidated_changes.values():
        overlapping = change.added_symbols & change.removed_symbols
        if overlapping:
            change.added_symbols -= overlapping
            change.removed_symbols -= overlapping

    # 최종 변경 알림 전송
    await self._notify_changes(consolidated_changes)
```

---

## 📊 성능 모니터링

### 배치 처리 메트릭스
```python
self._performance_metrics: Dict[str, Any] = {
    'total_batches_processed': 0,        # 처리된 총 배치 수
    'avg_batch_size': 0.0,               # 평균 배치 크기
    'last_batch_processed_at': None,     # 마지막 처리 시간
    'subscription_efficiency_score': 0.0  # 구독 효율성 점수
}
```

### 효율성 계산
```python
def calculate_subscription_efficiency(self) -> float:
    """구독 효율성 점수 계산 (0.0 ~ 1.0)"""
    # 배치 효율성
    batch_efficiency = min(1.0, avg_batch_size / max_batch_size)

    # 충돌 페널티
    conflict_penalty = len(detected_conflicts) * 0.1

    # 전체 효율성
    return max(0.0, batch_efficiency - conflict_penalty)
```

---

## 🎮 사용 예시

### 기본 사용법
```python
# 1. 배치 처리기 시작
await subscription_manager.start_batch_processor()

# 2. 컴포넌트 등록 (자동으로 배치 큐에 추가)
await subscription_manager.register_component(
    component_id="trader_bot",
    subscription_specs=[
        SubscriptionSpec(DataType.TICKER, ["KRW-BTC"]),
        SubscriptionSpec(DataType.ORDERBOOK, ["KRW-ETH"])
    ],
    priority=5  # 일반 우선순위
)

# 3. 해제 (높은 우선순위로 즉시 처리)
await subscription_manager.unregister_component(
    component_id="trader_bot",
    priority=10  # 높은 우선순위
)

# 4. 배치 처리기 중지
await subscription_manager.stop_batch_processor()
```

### 고급 사용법
```python
# 성능 모니터링
metrics = subscription_manager.get_performance_metrics()
print(f"배치 효율성: {metrics['current_efficiency']:.2%}")
print(f"대기 중인 배치: {metrics['pending_batch_count']}개")

# 충돌 감지 및 해결
conflicts = subscription_manager.detect_subscription_conflicts()
if conflicts:
    print(f"구독 충돌 감지: {len(conflicts)}개")

# 상태 스냅샷
snapshot = subscription_manager.create_state_snapshot()
print(f"총 구독: {snapshot['component_count']}개 컴포넌트")
```

---

## ⚡ 장점과 특징

### 🎯 **Rate Limit 완벽 준수**
- 업비트 "초당 5개 구독" 제한을 절대 위반하지 않음
- 스마트한 배치 분할로 큰 요청도 안전하게 처리

### 🚀 **최적화된 성능**
- 200ms 배치 윈도우로 지연 최소화
- 우선순위 기반 처리로 중요한 작업 우선 처리
- 중복 제거로 불필요한 네트워크 트래픽 방지

### 📊 **상세한 모니터링**
- 실시간 성능 메트릭스
- 배치 효율성 점수
- 구독 충돌 자동 감지

### 🔄 **확장 가능한 구조**
- 새로운 DataType 쉽게 추가
- 우선순위 시스템으로 정책 변경 용이
- 플러그인 방식의 콜백 시스템

---

## 🤔 사용 시나리오

### 시나리오 1: 대량 컴포넌트 등록
```
T=0ms:    5개 컴포넌트가 동시에 등록 요청 (총 12개 구독)
T=200ms:  첫 번째 배치 처리 (5개 구독)
T=400ms:  두 번째 배치 처리 (5개 구독)
T=600ms:  세 번째 배치 처리 (2개 구독)
```

### 시나리오 2: 긴급 해제 요청
```
T=0ms:    일반 등록 요청들이 대기 중
T=50ms:   긴급 해제 요청 (priority=10)
T=200ms:  → 해제 요청이 우선 처리됨
T=400ms:  → 일반 등록 요청들 처리
```

### 시나리오 3: 중복 요청 최적화
```
요청: KRW-BTC 구독 + KRW-BTC 해제 (같은 배치)
처리: 중복 제거로 실제 전송 없음
결과: 네트워크 트래픽 절약
```

---

## 🔧 커스터마이징 옵션

### 배치 설정 조정
```python
# 더 빠른 처리 (지연 감소)
self._batch_window_ms = 100  # 100ms

# 더 안전한 처리 (Rate Limit 여유)
self._max_batch_size = 3  # 3개로 제한

# 더 큰 배치 (효율성 증대)
self._max_batch_size = 8  # 8개까지 (주의: Rate Limit 위험)
```

### 우선순위 정책
```python
# 사용자 정의 우선순위
PRIORITY_EMERGENCY = 20   # 긴급 (즉시 처리)
PRIORITY_HIGH = 10        # 높음 (해제 작업)
PRIORITY_NORMAL = 5       # 보통 (일반 등록)
PRIORITY_LOW = 1          # 낮음 (백그라운드 작업)
```

---

## 🚨 주의사항

### Rate Limit 오해 방지
```python
# ❌ 잘못된 이해: "200ms마다 5개씩만 보내야 함"
# ✅ 올바른 이해: "1초 동안 총 5개를 넘으면 안 됨"

# 따라서 실제로는:
# 200ms: 5개 → 400ms: 0개 → 600ms: 0개 → 800ms: 0개 → 1000ms: 5개
```

### Event Loop 관리
```python
# 배치 처리기는 별도 Task로 실행
# 메인 스레드 블로킹 방지
self._batch_processing_task = asyncio.create_task(self._batch_processing_loop())
```

### 메모리 관리
```python
# 오래된 배치 자동 정리 (현재 미구현)
# 필요시 추가 구현:
def cleanup_old_batches(self, max_age_seconds: int = 30):
    current_time = time.time()
    self._pending_batches = [
        batch for batch in self._pending_batches
        if current_time - batch.queued_at < max_age_seconds
    ]
```

---

## 🔄 대안 시스템과의 비교

### vs 전역 Rate Limiter
| 특징 | 배치 처리 시스템 | 전역 Rate Limiter |
|------|------------------|-------------------|
| **응답성** | 200ms 지연 | 즉시 처리 |
| **복잡성** | 높음 | 낮음 |
| **효율성** | 매우 높음 | 보통 |
| **안정성** | 매우 높음 | 높음 |
| **확장성** | 우수 | 보통 |

### 선택 기준
- **즉시성 중요**: 전역 Rate Limiter 선택
- **효율성 중요**: 배치 처리 시스템 선택
- **안정성 최우선**: 배치 처리 시스템 선택

---

## 📝 구현 코드 아카이브

### 전체 구현 내용
이 문서 작성 시점(2025-09-02)의 완전한 구현 코드는 다음 파일에서 확인할 수 있습니다:
- **파일**: `subscription_manager.py`
- **커밋**: `master` 브랜치 최신
- **라인**: 95-200 (배치 처리 관련 코드)

### 재활용시 필요 작업
1. **데이터 클래스 복원**: `SubscriptionBatch` 클래스
2. **초기화 코드 복원**: `__init__`의 배치 관련 변수들
3. **메서드 복원**: 배치 처리 관련 메서드들
4. **통합 수정**: `register_component`, `unregister_component` 메서드
5. **성능 메트릭스 조정**: 배치 관련 통계 항목들

---

## 🎯 결론

**WebSocket v6 Rate Limit 인식 배치 처리 시스템**은 업비트 WebSocket의 Rate Limit을 완벽하게 관리하면서도 높은 효율성을 제공하는 고급 시스템입니다. 현재는 전역 Rate Limiter의 단순함을 선택했지만, 향후 다음과 같은 상황에서는 이 시스템을 재활용할 수 있습니다:

### 재활용 고려 상황
1. **대량 트래픽 처리** 필요시
2. **전역 Rate Limiter 성능 문제** 발생시
3. **세밀한 우선순위 제어** 필요시
4. **배치 최적화를 통한 효율성 향상** 필요시

이 문서는 해당 시스템의 완전한 설계 의도와 구현 내용을 보존하여, 필요시 빠른 복구와 개선이 가능하도록 합니다.

---

*문서 작성: 2025-09-02*
*작성자: GitHub Copilot*
*버전: v6.1 Enhanced*
