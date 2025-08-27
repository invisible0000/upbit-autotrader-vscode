# 업비트 WebSocket 구독 관리 시스템 설계

## 🎯 핵심 검증 결과
✅ **is_only_snapshot 분리 확인**: 스냅샷 모드는 1개 메시지만, 리얼타임 모드는 지속적 스트림
✅ **독립적 티켓 관리 필요성 확인**: 용도별 티켓 풀 분리가 효율적

## 🏗️ 구독 관리자 필수 기능

### 1. **티켓 풀 관리**
```python
class SubscriptionManager:
    snapshot_pool: TicketPool(max_size=1)    # 임시 사용
    realtime_pool: TicketPool(max_size=2)    # 장기 점유
```

### 2. **구독 상태 추적**
```python
subscription_registry = {
    "ticket_id": {
        "mode": "snapshot|realtime",
        "data_types": ["ticker", "trade"],
        "symbols": ["KRW-BTC", "KRW-ETH"],
        "created_at": timestamp,
        "last_message": timestamp,
        "status": "active|inactive|error"
    }
}
```

### 3. **자동 재구독 (필수)**
- **연결 끊김 복구**: 기존 realtime 구독 자동 복원
- **서버 재시작 대응**: 구독 목록 순차 재등록
- **오류 상황 복구**: 실패한 구독 재시도

### 4. **스냅샷 전용 API**
```python
async def request_snapshot(data_type: str, symbols: list) -> dict:
    """일회성 데이터 요청 - 응답 후 티켓 즉시 해제"""

async def request_snapshots_batch(requests: list) -> list:
    """일괄 스냅샷 요청 - 효율적 처리"""
```

### 5. **리얼타임 구독 API**
```python
async def subscribe_realtime(data_type: str, symbols: list) -> str:
    """지속적 구독 - subscription_id 반환"""

async def unsubscribe_realtime(subscription_id: str):
    """구독 해제 - 스마트 소프트 해제 사용"""

async def modify_subscription(subscription_id: str, symbols: list):
    """구독 수정 - 티켓 재사용"""
```

### 8. **구독 해제 전략 (업비트 제약 대응)**
```python
# 업비트 WebSocket은 명시적 unsubscribe API 없음
# 해제 방법: 하드 해제 vs 소프트 해제

UNSUBSCRIBE_SYMBOLS = {
    "KRW": "BTC-USDT",     # KRW 마켓 해제용
    "BTC": "ETH-USDT",     # BTC 마켓 해제용
    "USDT": "BTC-KRW"      # USDT 마켓 해제용
}

async def hard_unsubscribe(ticket_id: str):
    """하드 해제: 연결 종료 → 재연결"""
    await websocket.close()
    await websocket.connect()

async def soft_unsubscribe(ticket_id: str, current_symbols: list):
    """소프트 해제: 전용 심볼로 스냅샷 요청하여 스트림 정지"""
    unsubscribe_symbol = get_unsubscribe_symbol(current_symbols)
    await send_request("ticker", [unsubscribe_symbol], is_only_snapshot=True)

def get_unsubscribe_symbol(current_symbols: list) -> str:
    """현재 구독 마켓에 맞는 해제 전용 심볼 반환"""
    if any(s.startswith("KRW-") for s in current_symbols):
        return "BTC-USDT"
    elif any(s.startswith("BTC-") for s in current_symbols):
        return "ETH-USDT"
    else:
        return "BTC-KRW"  # 기본값
```

### 6. **티켓 효율성 최적화**
```python
async def optimize_subscriptions():
    """동일 심볼 다른 데이터타입 → 하나 티켓으로 통합"""

async def cleanup_inactive():
    """미사용 구독 자동 해제"""

def get_ticket_usage() -> dict:
    """티켓 사용률 모니터링"""
```

### 7. **충돌 방지 및 검증**
```python
def validate_subscription(data_type: str, symbols: list) -> bool:
    """중복 구독 방지"""

def detect_conflicts() -> list:
    """snapshot vs realtime 모드 충돌 감지"""
```

## 📊 사용 패턴별 최적화

### **패턴 1: 단발성 조회**
```python
# 현재 BTC 가격만 확인
price = await manager.request_snapshot("ticker", ["KRW-BTC"])
```

### **패턴 2: 지속적 모니터링**
```python
# BTC 가격 변화 실시간 추적
sub_id = await manager.subscribe_realtime("ticker", ["KRW-BTC"])
```

### **패턴 3: 일괄 초기화**
```python
# 전체 마켓 현재 상태 수집
all_prices = await manager.request_snapshots_batch([
    ("ticker", krw_markets),
    ("orderbook", major_markets)
])
```

### **패턴 4: 하이브리드 사용**
```python
# 초기 데이터 + 실시간 업데이트
initial = await manager.request_snapshot("ticker", ["KRW-BTC"])
sub_id = await manager.subscribe_realtime("ticker", ["KRW-BTC"])
```

### **패턴 5: 스마트 해제 사용**
```python
# 리얼타임 구독 해제 (소프트 해제)
await manager.soft_unsubscribe(sub_id, current_symbols=["KRW-BTC"])

# 완전 리셋이 필요한 경우 (하드 해제)
await manager.hard_unsubscribe(sub_id)
```

## 🔧 구현 우선순위

### **Phase 1: 기본 구조**
1. TicketPool 클래스
2. SubscriptionRegistry 클래스
3. 기본 snapshot/realtime API

### **Phase 2: 안정성**
1. 자동 재구독 로직
2. 오류 처리 및 복구
3. 연결 상태 모니터링

### **Phase 3: 최적화**
1. 티켓 통합 및 효율성
2. 배치 처리 최적화
3. 성능 모니터링

## 📋 필수 메트릭스

### **모니터링 지표**
- 티켓 사용률 (snapshot/realtime)
- 구독 성공/실패율
- 재연결 빈도
- 메시지 수신율

### **성능 기준**
- Snapshot 응답시간: < 3초
- Realtime 연결시간: < 5초
- 재구독 시간: < 10초
- 티켓 효율성: > 60%

---

**이 구조로 업비트 WebSocket의 효율적이고 안정적인 구독 관리가 가능합니다.**
