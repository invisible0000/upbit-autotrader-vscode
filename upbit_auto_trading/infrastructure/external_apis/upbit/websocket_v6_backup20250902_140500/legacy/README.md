# 🚀 WebSocket v6.0 개발 가이드

## 📁 아키텍처 개요
```
Global Management (Singleton) → Component Proxy → Application Layer
     ↓                              ↓                    ↓
전역 구독 상태 관리              프록시 인터페이스      GUI 컴포넌트들
```

## 🎯 개발 목표
- **전역 중앙집중식 WebSocket 관리** (업비트 구독 덮어쓰기 문제 해결)
- **컴포넌트별 프록시 인터페이스** (Zero Configuration)
- **자동 리소스 정리** (WeakRef + 명시적 cleanup)
- **장애 복구 및 백프레셔 처리** (24/7 안정성)

---

## 📋 구현 파일 목록

### 🔧 1. 핵심 인프라 (Phase 1)
```python
# 전역 관리자 (싱글톤)
global_websocket_manager.py        # 150-200줄
├── GlobalWebSocketManager 클래스
├── 단일 Public/Private 연결 관리
├── 전역 구독 상태 통합
└── 데이터 라우팅 허브

# 구독 상태 관리
subscription_state_manager.py      # 120-150줄
├── SubscriptionStateManager 클래스
├── 클라이언트별 구독 추적
├── 구독 통합 알고리즘
└── 원자적 상태 업데이트

# 데이터 분배 엔진
data_routing_engine.py             # 100-130줄
├── DataRoutingEngine 클래스
├── FanoutHub (멀티캐스팅)
├── BackpressureHandler (큐 오버플로우 처리)
└── 콜백 에러 격리
```

### 🎭 2. 프록시 인터페이스 (Phase 2)
```python
# 컴포넌트용 프록시
websocket_client_proxy.py          # 180-220줄
├── WebSocketClientProxy 클래스
├── subscribe_ticker/orderbook/candle
├── get_snapshot 메서드들
├── WeakRef 기반 자동 정리
└── Context Manager 지원

# 생명주기 관리
component_lifecycle_manager.py     # 80-100줄
├── ComponentLifecycleManager 클래스
├── WeakRef 콜백 등록
├── 자동 구독 정리
└── 메모리 누수 방지
```

### 🔥 3. 고급 기능 (Phase 3)
```python
# 장애 복구 엔진
recovery_engine.py                 # 120-150줄
├── RecoveryEngine 클래스
├── 지수 백오프 재연결
├── 구독 상태 복원
└── EpochManager (데이터 순서 보장)

# JWT 토큰 관리 (Private 채널용)
jwt_manager.py                     # 90-120줄
├── JWTManager 클래스
├── 자동 토큰 갱신 (만료 80% 시점)
├── Graceful Degradation
└── REST API 폴백

# 백프레셔 처리
backpressure_handler.py            # 80-100줄
├── BackpressureHandler 클래스
├── drop_oldest 전략
├── coalesce_by_symbol 전략
└── throttle 전략

# GUI 스레드 브릿지
qt_bridge_manager.py               # 60-80줄
├── QtBridgeManager 클래스
├── SignalEmitter (PyQt 연동)
├── 스레드 안전 데이터 전달
└── GUI 업데이트 큐
```

### 📊 4. 모니터링 & 유틸리티 (Phase 4)
```python
# 성능 모니터링
performance_monitor.py             # 100-130줄
├── PerformanceMonitor 클래스
├── 실시간 메트릭 수집
├── 알림 임계값 관리
└── 상태 대시보드 데이터

# 타입 정의 (이벤트 시스템)
types.py                          # 80-100줄
├── @dataclass 이벤트들
├── TickerEvent, OrderbookEvent, CandleEvent
├── SubscriptionSpec, ComponentSubscription
└── PerformanceMetrics

# 설정 관리
config.py                         # 50-70줄
├── WebSocketV6Config 클래스
├── 연결 설정, 재연결 설정
├── 백프레셔 설정
└── 모니터링 설정

# 예외 정의
exceptions.py                     # 40-60줄
├── WebSocketV6Exception 계층
├── ConnectionError, SubscriptionError
├── BackpressureError, AuthError
└── RecoveryError
```

### 🧪 5. 테스트 지원 (Phase 4)
```python
# Mock WebSocket 서버
mock_websocket_server.py          # 150-200줄
├── MockUpbitWebSocketServer 클래스
├── 업비트 동작 모방 (구독 덮어쓰기)
├── 시장 데이터 시뮬레이션
└── 연결 실패 시뮬레이션

# 테스트 유틸리티
test_utils.py                     # 80-100줄
├── 테스트용 헬퍼 함수들
├── Mock 데이터 생성기
├── 성능 측정 도구
└── 시나리오 시뮬레이터
```

### 🔗 6. 메인 인터페이스 (Phase 5)
```python
# 메인 인터페이스
__init__.py                      # 30-50줄
├── 주요 클래스 export
├── 편의 함수들
├── 버전 정보
└── 설정 기본값
```

---

## 🎯 개발 우선순위

### Phase 1: 핵심 인프라 (1주차)
1. `global_websocket_manager.py` - 전역 관리 중심
2. `subscription_state_manager.py` - 구독 상태 통합
3. `data_routing_engine.py` - 데이터 분배
4. `types.py` - 기본 타입 정의

### Phase 2: 프록시 인터페이스 (2주차)
1. `websocket_client_proxy.py` - 컴포넌트 인터페이스
2. `component_lifecycle_manager.py` - 자동 정리
3. `exceptions.py` - 예외 체계
4. `config.py` - 설정 관리

### Phase 3: 고급 기능 (3-4주차)
1. `recovery_engine.py` - 장애 복구
2. `jwt_manager.py` - Private 인증
3. `backpressure_handler.py` - 성능 최적화
4. `qt_bridge_manager.py` - GUI 연동

### Phase 4: 모니터링 & 테스트 (5주차)
1. `performance_monitor.py` - 성능 추적
2. `mock_websocket_server.py` - 테스트 지원
3. `test_utils.py` - 테스트 도구

### Phase 5: 최종 통합 (6주차)
1. `__init__.py` - 최종 인터페이스
2. 통합 테스트 및 최적화
3. 전체 시스템 교체

---

## 🔧 기존 시스템 연동

### 전역 Rate Limiter 통합 (핵심)
```python
# 전역 Rate Limiter - 모든 업비트 요청 통합 관리
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import (
    get_global_rate_limiter,      # GCRA 기반 전역 Rate Limiter
    gate_websocket,               # WebSocket 전용 게이트
    UpbitRateLimitGroup          # 5개 그룹 분류
)

from upbit_auto_trading.infrastructure.external_apis.upbit.dynamic_rate_limiter_wrapper import (
    get_dynamic_rate_limiter,     # 429 에러 자동 조정
    DynamicConfig,               # 동적 조정 설정
    AdaptiveStrategy             # 조정 전략
)
```

### v5 재사용 컴포넌트
```python
# 물리적 WebSocket 연결만 재사용
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5 import (
    UpbitWebSocketPublicClient,   # 물리적 Public 연결
    UpbitWebSocketPrivateClient   # 물리적 Private 연결
)
```

### 인증 시스템 연동
```python
# 기존 인증 인프라 활용
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_auth import (
    UpbitAuthenticator           # JWT 토큰 생성
)
```

---

## 🚀 빠른 시작 예제

### 개발자용 사용법
```python
# 1. 프록시 생성 (Zero Configuration)
from websocket_v6 import WebSocketClientProxy

async def main():
    proxy = WebSocketClientProxy("my_chart_component")

    # 2. 구독 시작 (자동으로 전역 관리됨)
    await proxy.subscribe_ticker(
        ["KRW-BTC", "KRW-ETH"],
        callback=lambda event: print(f"{event.symbol}: {event.trade_price}")
    )

    # 3. 스냅샷 요청
    tickers = await proxy.get_ticker_snapshot(["KRW-BTC"])

    # 4. 자동 정리 (컨텍스트 종료 시)
    await proxy.cleanup()  # 또는 WeakRef 자동 호출
```

### 전역 상태 확인
```python
from websocket_v6 import GlobalWebSocketManager

# 시스템 상태 조회
manager = GlobalWebSocketManager.get_instance()
status = await manager.get_health_status()
print(f"연결 상태: {status['connections']}")
print(f"활성 구독: {status['subscriptions']}")
```

---

## 📈 예상 총 라인수
- **핵심 코드**: ~1,300줄 (호환성 제거)
- **테스트 코드**: ~600줄
- **문서/예제**: ~200줄
- **총합**: ~2,100줄

## 🎯 성공 기준
- ✅ 업비트 구독 충돌 문제 100% 해결
- ✅ 메모리 누수 0건 달성
- ✅ 99.9% 연결 안정성 확보
- ✅ 전역 Rate Limiter 통합 관리
- ✅ v6 완전 교체 (v5 제거)---

*📌 이 가이드는 [WEBSOCKET_V6_FINAL_SPECIFICATION.md](../../../docs/upbit_API_reference/websocket_v6/WEBSOCKET_V6_FINAL_SPECIFICATION.md)의 실제 구현을 위한 개발 로드맵입니다.*
