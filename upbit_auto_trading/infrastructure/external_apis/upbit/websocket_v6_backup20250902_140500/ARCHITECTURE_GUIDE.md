# WebSocket v6.0 아키텍처 가이드

## 📋 개요

업비트 WebSocket v6.0은 v5 호환성을 완전히 제거하고 순수 v6 아키텍처로 재설계된 시스템입니다. 중앙 집중식 관리, 타입 안전성, 성능 최적화에 중점을 두었습니다.

## 🏗️ 아키텍처 설계 원칙

### 1. **중앙 집중식 관리 (Singleton Pattern)**
- `GlobalWebSocketManager`: 모든 WebSocket 연결과 구독을 중앙에서 관리
- 리소스 충돌 방지 및 효율적인 연결 재사용

### 2. **타입 안전성 (@dataclass 기반)**
- 모든 데이터 구조가 `@dataclass`로 정의됨
- 컴파일 타임 타입 검증 및 IDE 지원 강화

### 3. **WeakReference 기반 자동 정리**
- 컴포넌트 생명주기 자동 관리
- 메모리 누수 방지 및 자동 구독 해제

### 4. **백프레셔 및 성능 최적화**
- 큐 기반 데이터 라우팅으로 성능 병목 해결
- SIMPLE 포맷 지원으로 대역폭 최적화

## 📦 핵심 컴포넌트

### 🎯 **중앙 관리자 계층**

#### `GlobalWebSocketManager` (global_websocket_manager.py)
**역할**: 전체 시스템의 중앙 제어탑
- **기능**:
  - WebSocket 연결 생명주기 관리
  - 구독 상태 통합 관리
  - 컴포넌트 등록/해제 및 WeakRef 기반 자동 정리
  - Epoch 기반 재연결 처리
  - **백그라운드 모니터링 시스템** (v6.1 추가)
    - `_health_monitor_task()`: 30초마다 연결 상태 및 WeakRef 정리
    - `_metrics_collector_task()`: 10초마다 성능 메트릭스 자동 업데이트
    - `_cleanup_monitor_task()`: 1분마다 죽은 참조 자동 정리
  - **Rate Limiter 통합**: 업비트 API 429 오류 방지
- **의존성**:
  - ← `SubscriptionStateManager` (구독 상태 관리)
  - ← `DataRoutingEngine` (데이터 분배)
  - ← `NativeWebSocketClient` (실제 연결)
  - ← `EpochManager` (재연결 순서 보장)
  - ← `UpbitRateLimiter` (선택적, 요청 제한 관리)

#### `WebSocketClientProxy` (websocket_client_proxy.py)
**역할**: 사용자 친화적 인터페이스 제공
- **기능**:
  - 컨텍스트 매니저 지원 (`async with`)
  - 타입 안전한 구독 API (`subscribe_ticker`, `subscribe_orderbook`)
  - 자동 구독 해제 및 리소스 정리
- **의존성**:
  - → `GlobalWebSocketManager` (중앙 관리자 호출)
  - ← `types.py` (타입 정의)

### 🔌 **연결 계층**

#### `NativeWebSocketClient` (native_websocket_client.py)
**역할**: 순수 WebSocket 연결 관리
- **기능**:
  - Public/Private WebSocket 연결 관리
  - 메시지 송수신 및 압축 처리
  - 재연결 로직 및 상태 추적
- **의존성**:
  - ← `websockets` 라이브러리
  - ← `jwt_manager.py` (Private 인증)

#### `JWTManager` (jwt_manager.py)
**역할**: Private WebSocket 인증 관리
- **기능**:
  - JWT 토큰 자동 갱신 (임계값 기반)
  - 토큰 유효성 검증
  - 인증 실패 시 자동 재시도
- **의존성**:
  - ← `upbit_authenticator.py` (API 키 기반 토큰 생성)

### 📡 **데이터 처리 계층**

#### `SubscriptionStateManager` (subscription_state_manager.py)
**역할**: 구독 상태의 중앙 집중 관리
- **기능**:
  - 컴포넌트별 구독 상태 추적
  - 구독 충돌 감지 및 해결
  - 구독 변경사항 계산 및 알림
- **의존성**:
  - ← `types.py` (구독 관련 타입)
  - → `GlobalWebSocketManager` (변경사항 알림)

#### `DataRoutingEngine` (data_routing_engine.py)
**역할**: 수신 데이터의 효율적 분배
- **기능**:
  - `FanoutHub`: 1:N 데이터 분배
  - 백프레셔 처리 (큐 기반)
  - 성능 메트릭 수집
- **하위 컴포넌트**:
  - `FanoutHub`: 콜백 관리 및 데이터 분배
  - `DataDistributionStats`: 성능 통계 수집

### 🎛️ **타입 시스템**

#### `types.py`
**역할**: 전체 시스템의 타입 정의
- **핵심 타입**:
  - 이벤트: `TickerEvent`, `OrderbookEvent`, `TradeEvent`, `CandleEvent`
  - Private 이벤트: `MyOrderEvent`, `MyAssetEvent` (DataType.MYORDER, DataType.MYASSET)
  - 캔들 데이터: `DataType.CANDLE_1M`, `CANDLE_3M`, `CANDLE_5M`, `CANDLE_15M`, `CANDLE_30M`, `CANDLE_60M`, `CANDLE_240M`
  - 구독: `SubscriptionSpec`, `ComponentSubscription`
  - 상태: `ConnectionState`, `WebSocketType`, `DataType`
  - 성능: `PerformanceMetrics`, `HealthStatus`, `ConnectionMetrics`
  - 관리자: `GlobalManagerState` (IDLE, ACTIVE, SHUTTING_DOWN, ERROR)

#### `models.py`
**역할**: v5 모델 통합 및 메시지 처리
- **기능**:
  - v5 필드 문서화 및 호환성 유지
  - 메시지 형식 변환 (`dict` ↔ `v6 Event`)
  - 데이터 검증 및 정규화
- **v5 통합 요소**:
  - `TICKER_FIELDS`, `TRADE_FIELDS` 등 필드 문서
  - `convert_dict_to_event()` 변환 함수

### ⚙️ **설정 및 유틸리티**

#### `config.py`
**역할**: 환경별 설정 관리
- **설정 영역**:
  - `ConnectionConfig`: 연결 URL, 타임아웃
  - `ReconnectionConfig`: 재연결 정책
  - `BackpressureConfig`: 백프레셔 전략
  - `AuthConfig`: JWT 갱신 정책
- **환경별 프리셋**: Development, Testing, Production

#### `exceptions.py`
**역할**: 체계적인 예외 처리
- **예외 계층**:
  - `WebSocketException` (기본)
  - `ConnectionError`, `SubscriptionError`
  - `BackpressureError`, `AuthenticationError`

#### `simple_format_converter.py` (선택사항)
**역할**: SIMPLE 포맷 지원
- **기능**: 대역폭 최적화를 위한 압축 포맷 변환

## 🔄 데이터 흐름

```
[업비트 서버]
    ↓ WebSocket
[NativeWebSocketClient]
    ↓ 원시 메시지
[GlobalWebSocketManager._convert_to_event]
    ↓ v6 이벤트
[DataRoutingEngine.route_event]
    ↓ 타입별 분배
[FanoutHub]
    ↓ 1:N 분배
[컴포넌트 콜백들]
```

## 🔗 의존성 관계

### 계층별 의존성
```
📱 사용자 코드
    ↓
🎯 WebSocketClientProxy (인터페이스)
    ↓
🏛️ GlobalWebSocketManager (중앙 관리)
    ↓
🔌 NativeWebSocketClient (연결) + 📡 DataRoutingEngine (분배)
    ↓
🌐 WebSocket Protocol
```

### 모듈 간 의존성
```
types.py ← 모든 모듈 (타입 정의)
config.py ← 모든 모듈 (설정)
exceptions.py ← 모든 모듈 (예외)

GlobalWebSocketManager → SubscriptionStateManager
                      → DataRoutingEngine
                      → NativeWebSocketClient
                      → JWTManager

WebSocketClientProxy → GlobalWebSocketManager

models.py → types.py (v5 호환성)
```

## 🚀 사용 방법

### 기본 사용법
```python
from websocket_v6 import WebSocketClientProxy

async def my_callback(event):
    print(f"받은 데이터: {event.symbol} = {event.trade_price}")

async def candle_callback(event):
    print(f"캔들 데이터: {event.symbol} - 시가: {event.opening_price}, 종가: {event.trade_price}")

# 컨텍스트 매니저 사용 (권장)
async with WebSocketClientProxy("my_component") as ws:
    await ws.subscribe_ticker(["KRW-BTC"], my_callback)
    await ws.subscribe_candle(["KRW-BTC"], candle_callback, unit=5)  # 5분봉
    # 자동으로 정리됨
```

### 고급 사용법
```python
from websocket_v6 import get_global_websocket_manager

manager = await get_global_websocket_manager()
health = await manager.get_health_status()
metrics = await manager.get_performance_metrics()

# 백그라운드 모니터링 상태 확인
print(f"Background tasks: {len(manager._background_tasks)}")
print(f"Uptime: {manager.uptime_seconds:.2f}s")
```

## 📊 성능 특징

### 메모리 관리
- **WeakRef 기반**: 컴포넌트 자동 정리로 메모리 누수 방지
- **백그라운드 모니터링**: 3개의 백그라운드 태스크가 자동으로 시스템 상태 관리
  - 헬스 모니터링 (30초 주기)
  - 성능 메트릭스 수집 (10초 주기)
  - 죽은 참조 정리 (1분 주기)
- **백프레셔 제어**: 큐 크기 제한으로 메모리 사용량 제어

### 네트워크 효율성
- **연결 재사용**: 중앙 집중식 관리로 연결 수 최소화
- **Rate Limiter 통합**: 업비트 API 429 오류 자동 방지 및 백오프
- **SIMPLE 포맷**: 선택적 압축으로 대역폭 절약

### 확장성
- **비동기 처리**: 모든 I/O 작업이 비동기
- **타입 안전성**: 컴파일 타임 오류 검출

## 🔧 확장 포인트

### 새로운 데이터 타입 추가
1. `types.py`에 `DataType` enum 추가 (예: `CANDLE_1D = "candle.1d"`)
2. 해당 이벤트 클래스 정의 (또는 기존 `CandleEvent` 확장)
3. `GlobalWebSocketManager._convert_to_event()` 확장
4. `WebSocketClientProxy`에 전용 메서드 추가 (예: `subscribe_daily_candle()`)
5. `SubscriptionStateManager`에서 이벤트 타입 매핑 추가

### 새로운 백프레셔 전략
1. `types.py`에 `BackpressureStrategy` 추가
2. `DataRoutingEngine`에 전략 구현
3. `config.py`에 설정 추가

## ⚠️ 주의사항

### v5 호환성
- **완전 제거**: v5 코드와 호환되지 않음
- **마이그레이션**: v5 → v6 마이그레이션 가이드 별도 제공

### 리소스 관리
- **컨텍스트 매니저 사용 권장**: 자동 정리 보장
- **WeakRef 주의**: 참조가 사라지면 자동 해제됨

### 성능 튜닝
- **백프레셔 설정**: 환경에 맞는 큐 크기 조정 필요
- **Rate Limiter 통합**: 자동으로 최적화되어 수동 조정 불필요
- **모니터링 주기**: 백그라운드 태스크 주기는 운영 환경에 최적화됨
- **재연결 정책**: 네트워크 환경에 맞는 백오프 전략 설정

---

**WebSocket v6.0은 안정성과 성능, 개발자 경험, 자동 모니터링을 모두 고려하여 설계된 차세대 WebSocket 시스템입니다.**
