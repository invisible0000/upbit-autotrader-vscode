# 🚀 WebSocket v6 간편 가이드

> **5분만에 이해하는 업비트 WebSocket 시스템 구조**

## 📁 폴더 구조

```
websocket/
├── core/                           # 핵심 시스템
│   ├── websocket_manager.py        # 🎯 중앙 관리자 (싱글톤)
│   ├── websocket_client.py         # 📱 사용자 인터페이스
│   ├── websocket_types.py          # 📋 데이터 타입 정의
│   └── data_processor.py           # 🔄 메시지 처리기
│
├── support/                        # 지원 시스템
│   ├── subscription_manager.py     # 📺 구독 관리
│   ├── format_utils.py             # 🔧 메시지 변환
│   ├── websocket_config.py         # ⚙️ 설정 로더
│   └── jwt_manager.py              # 🔐 인증 토큰
│
└── 📄 WEBSOCKET_V6_SIMPLE_GUIDE.md # 이 문서
```

## 🎯 핵심 컴포넌트 역할

| 파일 | 역할 | 주요 메서드 |
|------|------|-------------|
| **🎯 websocket_manager.py** | **시스템 총괄** | `.register_component()` `.get_health_status()` |
| **📱 websocket_client.py** | **사용자 API** | `.subscribe_ticker()` `.subscribe_orderbook()` |
| **📋 websocket_types.py** | **데이터 구조** | `TickerEvent` `OrderbookEvent` |
| **🔄 data_processor.py** | **메시지 라우팅** | `.route_event()` `.register_callback()` |
| **📺 subscription_manager.py** | **구독 상태** | `.register_component()` `.get_required_subscriptions()` |

## 🔄 데이터 흐름 (3단계)

```
📡 업비트 WebSocket
        ↓ JSON 메시지
🎯 WebSocketManager
        ↓ 파싱 & 라우팅
🔄 DataProcessor
        ↓ 이벤트 분배
📱 사용자 컴포넌트 (콜백 함수)
```

## 💡 실제 사용법

### **1. 간단한 현재가 구독**

```python
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket import WebSocketClient

# 클라이언트 생성
client = WebSocketClient("my_app")

# 콜백 정의
async def on_price_change(event):
    print(f"💰 {event.symbol}: {event.trade_price:,}원")

# 구독 시작
await client.subscribe_ticker(["KRW-BTC", "KRW-ETH"], on_price_change)
```

### **2. 스냅샷(일회성) 데이터 요청**

```python
# 🔄 실시간 + 스냅샷 (기본값)
await client.subscribe_ticker(["KRW-BTC"], callback, stream_preference="both")

# 📸 스냅샷만 (일회성, 현재 상태만)
await client.subscribe_ticker(["KRW-BTC"], callback, stream_preference="snapshot_only")

# ⚡ 실시간만 (변경사항만)
await client.subscribe_ticker(["KRW-BTC"], callback, stream_preference="realtime_only")
```

### **3. 여러 데이터 동시 구독**

```python
# 현재가 + 호가 동시 구독
await client.subscribe_ticker(["KRW-BTC"], on_ticker)
await client.subscribe_orderbook(["KRW-BTC"], on_orderbook)

# 자동으로 하나의 WebSocket 연결에서 처리됨 ✨
```

### **4. 스냅샷 활용 예제**

```python
# 현재 가격 한 번만 확인하고 싶을 때
async def get_current_price(symbol):
    received_data = None

    async def capture_snapshot(event):
        nonlocal received_data
        received_data = event

    # 스냅샷만 요청
    await client.subscribe_ticker([symbol], capture_snapshot, "snapshot_only")

    # 잠시 대기
    await asyncio.sleep(1)

    return received_data.trade_price if received_data else None

# 사용법
current_btc_price = await get_current_price("KRW-BTC")
print(f"현재 BTC 가격: {current_btc_price:,}원")
```

## 🎨 시스템 아키텍처 다이어그램

```
     📱 Application
          │
          ▼
    🎯 WebSocketManager (싱글톤)
          │
    ┌─────┼─────┐
    ▼     ▼     ▼
📺 구독   🔄 처리  🔐 인증
   관리   라우팅   토큰
    │     │     │
    └─────┼─────┘
          ▼
    🌐 WebSocket 연결
    (Public / Private)
          │
          ▼
    📡 업비트 API
```

## ⚡ 핵심 특징

### **🎯 Pending State 시스템**
- **문제**: 동시에 여러 구독 요청 시 중복 전송
- **해결**: 15초 내 요청들을 자동 통합해서 한 번에 전송
- **효과**: 10배 성능 향상 + API 제한 준수

### **🔄 자동 재연결**
- 연결 끊김 감지 → 지수백오프 재시도 → 구독 상태 복원
- 최대 5회 시도 (1초 → 2초 → 4초 → 8초 → 16초)

### **💾 메모리 안전**
- WeakRef로 컴포넌트 관리 → 메모리 누수 방지
- 자동 정리 시스템으로 가비지 컬렉션

## 🚦 시작하기

### **1단계: 기본 설정**
```python
# 환경변수 설정 (Private 데이터용)
export UPBIT_ACCESS_KEY="your_key"
export UPBIT_SECRET_KEY="your_secret"
```

### **2단계: 클라이언트 생성**
```python
client = WebSocketClient("trading_bot")
```

### **3단계: 이벤트 핸들러 작성**
```python
async def handle_ticker(event):
    if event.trade_price > 50000000:  # 5천만원 이상
        print(f"🚨 고가 알림: {event.symbol}")
```

### **4단계: 구독 시작**
```python
await client.subscribe_ticker(["KRW-BTC"], handle_ticker)
```

## 🔧 설정 튜닝

| 환경 | heartbeat | strategy | 용도 |
|------|-----------|----------|------|
| **개발** | 60초 | aggressive | 빠른 테스트 |
| **운영** | 30초 | balanced | 안정성 + 성능 |

## 📊 모니터링

```python
# 시스템 상태 확인
manager = await get_global_websocket_manager()
status = manager.get_health_status()
print(f"상태: {status.status}")  # healthy/unhealthy

# 성능 지표
metrics = manager.get_all_connection_metrics()
print(f"처리된 메시지: {metrics['total_processed']}")
```

## 🛠️ 문제 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| 연결 실패 | 네트워크 | 인터넷 연결 확인 |
| 401 오류 | 인증 | API 키 확인 |
| 429 오류 | Rate Limit | 자동 조정 대기 |
| 메모리 증가 | 누수 | 컴포넌트 정리 |

## 🎉 핵심 정리

1. **📱 WebSocketClient**: 사용자가 직접 사용하는 API
2. **🎯 WebSocketManager**: 모든 것을 관리하는 중앙 허브
3. **📺 SubscriptionManager**: 구독 상태를 추적 관리
4. **🔄 DataProcessor**: 메시지를 적절한 곳으로 전달
5. **⚡ Pending State**: 여러 요청을 자동으로 통합 처리

### **📊 스트림 타입별 용도**

| 타입 | 코드 | 용도 | 예시 |
|------|------|------|------|
| **📸 스냅샷** | `"snapshot_only"` | 현재 상태 확인 | 현재가 조회, 호가 현황 |
| **⚡ 실시간** | `"realtime_only"` | 변경 감지 | 가격 변동 알림, 거래 모니터링 |
| **🔄 통합** | `"both"` | 현재상태+변경감지 | 일반적인 구독 (기본값) |

**→ 간단히 말해서: 업비트 데이터를 받아서 내 함수로 전달해주는 시스템! 🚀**

---
*업데이트: 2025년 9월 3일 | 버전: v6.2*
